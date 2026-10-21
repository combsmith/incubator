#!/usr/bin/env python3
"""
DemandRadar — deep dive on a top pick (disruption / market opportunity brief).

Answers "how do I win this market?" for one keyword: pulls the competitor set (what
users actually see when they search), mines each leader's reviews for what users
HATE (the openings) and what they LOVE (what to preserve), reads the pricing/staleness
landscape, and synthesizes a WEDGE + writes a readable opportunity brief.

  python deep_dive.py --keyword "mood tracker"
  python deep_dive.py --keyword "guitar chords" --top 8 --pages 3

Outputs: output/deepdive/<slug>.json  and  output/deepdive/<slug>.md
Free data only (iTunes Search API + customer-reviews RSS). Paced; no auth.
pipeline.py --preset weekly calls run() on the week's top new entries, with --rate pacing
every iTunes call so a batch of briefs stays inside the ~20/min limit.
"""

import argparse
import collections
import itertools
import json
import os
import re
import threading
import time
import urllib.parse
import urllib.request

from patterns import cat_pattern, slug

HERE = os.path.dirname(os.path.abspath(__file__))
UA = "DemandRadar-spike/0.6 (+combsmith/incubator; research)"

PRICING = "pricing / paywall"
GOT_WORSE = "got worse (enshittification)"

GRIPES = {
    PRICING: [
        "paywall",
        "behind a wall",
        "locked behind",
        "subscription",
        "subscribe",
        "premium",
        "pay for",
        "pay to",
        "have to pay",
        "costs money",
        "cost money",
        "now costs",
        "not free",
        "isn't free",
        "used to be free",
        "expensive",
        "overpriced",
        "money grab",
        "cash grab",
        "greedy",
        "rip off",
        "ripoff",
        "charge",
        "$",
    ],
    "ads": ["ads", "adverts", "advertisement", "pop up", "pop-up", "popup", "commercials", "full of ads"],
    GOT_WORSE: [
        "used to",
        "got worse",
        "gotten worse",
        "downhill",
        "ruined",
        "bring back",
        "worse now",
        "not the same",
        "since the update",
        "update ruined",
        "was better",
    ],
    "bugs / reliability": [
        "bug",
        "crash",
        "crashes",
        "glitch",
        "broken",
        "won't open",
        "wont open",
        "freezes",
        "freezing",
        "lag",
        "laggy",
        "sync issue",
        "lost my data",
        "lost data",
    ],
    "missing / limited": [
        "wish",
        "missing",
        "no way to",
        "can't",
        "cant",
        "needs a",
        "would be nice",
        "please add",
        "add a",
        "no option",
        "lacks",
        "limited",
    ],
}
# the gripe categories that actually drive users to abandon/switch (resentment signal)
RESENT_CATS = (PRICING, "ads", GOT_WORSE)


GRIPE_RE = {c: cat_pattern(kws) for c, kws in GRIPES.items()}
LOVES = [
    "simple",
    "easy",
    "clean",
    "love it",
    "love this",
    "best",
    "intuitive",
    "private",
    "offline",
    "no ads",
    "free",
    "cute",
    "aesthetic",
    "minimal",
    "beautiful",
    "fast",
    "reliable",
    "customizable",
]
# whole-word/phrase matching, so "free" is not found inside "freezes" and counted as praise
LOVE_RE = {w: cat_pattern([w]) for w in LOVES}
WISH_RE = re.compile(r"(?:wish|would love|needs?|please add|no way to|can'?t)\b[^.!?]{0,80}", re.I)


def _clip(text, n):
    """Cut text to n chars, marking the cut with an ellipsis so a clipped excerpt is never
    presented as the complete review."""
    return text if len(text) <= n else text[:n].rstrip() + "…"


# --- rate limiter: run(rate=N) spaces every iTunes call >= 60/N s apart (0 = unpaced CLI) ---
_pace_lock = threading.Lock()
_next_at = [0.0]
_min_interval = [0.0]


def pace():
    with _pace_lock:
        now = time.time()
        wait = max(0.0, _next_at[0] - now)
        _next_at[0] = max(now, _next_at[0]) + _min_interval[0]
    if wait > 0:
        time.sleep(wait)


def _fetch(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=20).read()


def get(url):
    pace()
    return _fetch(url)


def load_ma_label(kw):
    p = os.path.join(HERE, "labels", "mobileaction-labels.json")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as fh:
            labels = json.load(fh).get("labels", [])
        for label in labels:
            if label["keyword"].lower() == kw.lower():
                return label
    return None


def competitors(kw, top):
    d = json.loads(
        get(
            "https://itunes.apple.com/search?"
            + urllib.parse.urlencode({"term": kw, "country": "us", "entity": "software", "limit": max(top, 10)})
        )
    )
    return d.get("results", [])[:top]


def reviews(tid, pages):
    """Recent reviews as (rating, title, content), or None when not even the first page could
    be fetched — an unavailable sample must not be reported as 0% resentment."""
    out = []
    for pg in range(1, pages + 1):
        try:
            r = json.loads(
                get(f"https://itunes.apple.com/us/rss/customerreviews/page={pg}/id={tid}/sortBy=mostRecent/json")
            )
        except Exception:  # noqa: BLE001
            if pg == 1:
                return None
            break
        for e in r.get("feed", {}).get("entry", []):
            rt = e.get("im:rating", {}).get("label")
            if rt:
                out.append((int(rt), e.get("title", {}).get("label", ""), e.get("content", {}).get("label", "")))
        time.sleep(0.4)
    return out


def analyze_reviews(revs):
    low = [x for x in revs if x[0] <= 3]
    high = [x for x in revs if x[0] >= 4]
    gcat = collections.Counter()
    quotes = collections.defaultdict(list)
    resenting = 0  # count each low review AT MOST ONCE toward resent_frac (not per category)
    for rt, t, b in low:
        hay = (t + " . " + b).lower()
        hit_resent = False
        for c, rx in GRIPE_RE.items():
            if rx.search(hay):
                gcat[c] += 1
                if c in RESENT_CATS:
                    hit_resent = True
                if len(quotes[c]) < 3:
                    quotes[c].append({"r": rt, "t": _clip(t, 70), "b": _clip(b, 160)})
        if hit_resent:
            resenting += 1
    loves = collections.Counter()
    for rt, t, b in high:
        hay = (t + " . " + b).lower()
        for w, rx in LOVE_RE.items():
            if rx.search(hay):
                loves[w.replace(" it", "").replace(" this", "")] += 1
    wishes = []
    for rt, t, b in low + high:
        for m in WISH_RE.findall(b):
            s = m.strip()
            if 12 < len(s) < 90 and s.lower() not in [w.lower() for w in wishes]:
                wishes.append(s)
    return {
        "n": len(revs),
        "n_low": len(low),
        "n_high": len(high),
        "resent_frac": round(resenting / len(low), 2) if low else 0,
        "gripes": dict(gcat),
        "quotes": dict(quotes),
        "loves": dict(loves.most_common(8)),
        "wishes": wishes[:6],
    }


WEDGE_TEMPLATES = {
    PRICING: "**Fix the money model** ({n} gripes — the dominant complaint): win with a genuinely useful free tier or a one-time unlock, not another subscription/paywall-after-2-entries.",
    "ads": "**Ship ad-free** ({n} gripes): ads are a repeated complaint here, and 'no ads' is itself a selling point users praise.",
    GOT_WORSE: "**Be the simple, un-bloated alternative** ({n} gripes): users say the incumbents got worse / raised prices / removed basics — restore the clean original experience.",
    "bugs / reliability": "**Make reliability the pitch** ({n} gripes): recurring crashes / broken widgets / lost-data complaints — rock-solid sync + export/backup is a real differentiator.",
    "missing / limited": "**Close the feature gaps** ({n} gripes) users keep explicitly asking for (see the wishes list).",
}


def synth_wedge(market_gripes, loves):
    total = sum(market_gripes.values()) or 1
    w = []
    for cat, n in sorted(market_gripes.items(), key=lambda x: -x[1]):
        if n >= max(3, 0.12 * total) and cat in WEDGE_TEMPLATES:
            w.append(WEDGE_TEMPLATES[cat].format(n=n))
    if loves:
        w.append(
            "**Keep what they love:** " + ", ".join(list(loves)[:5]) + " — don't out-feature these into complexity."
        )
    return w


def run(keyword, top=8, pages=3, min_ratings=2000, rate=0):
    """Write the opportunity brief for one keyword; return the markdown path. rate > 0 caps
    iTunes calls per minute (the weekly pipeline passes its --rate)."""
    _min_interval[0] = 60.0 / rate if rate > 0 else 0.0
    kw = keyword
    brief = slug(kw)
    outdir = os.path.join(HERE, "output", "deepdive")
    os.makedirs(outdir, exist_ok=True)
    ma = load_ma_label(kw)

    apps = competitors(kw, top)
    time.sleep(2.0)
    comps = []
    market_gripes = collections.Counter()
    wish_lists = []  # one list per review-mined competitor
    for a in apps:
        c = {
            "app": a.get("trackName"),
            "id": a.get("trackId"),
            "seller": a.get("sellerName"),
            "rating": round(a.get("averageUserRating") or 0, 2),
            "count": a.get("userRatingCount") or 0,
            "price": a.get("formattedPrice"),
            "updated": (a.get("currentVersionReleaseDate") or "")[:7],
            "genre": a.get("primaryGenreName"),
        }
        if c["count"] >= min_ratings and c["id"]:
            revs = reviews(c["id"], pages)
            if revs is None or not revs:
                c["reviews_unavailable"] = True  # rendered as unknown ("n/a"), not 0%
            else:
                rv = analyze_reviews(revs)
                c["reviews"] = rv
                for k, v in rv["gripes"].items():
                    market_gripes[k] += v
                wish_lists.append(rv["wishes"])
            time.sleep(0.6)
        comps.append(c)

    loves = collections.Counter()
    for c in comps:
        for k, v in (c.get("reviews", {}).get("loves") or {}).items():
            loves[k] += v
    wedge = synth_wedge(market_gripes, dict(loves.most_common(6)))
    # Round-robin across competitors so the capped market list draws from every incumbent
    # instead of being filled by the first one or two.
    all_wishes = [w for tier in itertools.zip_longest(*wish_lists) for w in tier if w is not None]

    result = {
        "keyword": kw,
        "mobileaction": ma,
        "competitors": comps,
        "market_gripes": dict(market_gripes),
        "market_loves": dict(loves.most_common(8)),
        "wishes": all_wishes[:10],
        "wedge": wedge,
    }
    with open(os.path.join(outdir, brief + ".json"), "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)

    # ---- markdown brief ----
    L = [f"# Deep dive — **{kw}**\n"]
    if ma:
        L.append(
            f"**Market demand (MobileAction):** search volume `{ma.get('volume')}` · difficulty `{ma.get('difficulty')}` · {ma.get('ranked_apps')} ranked apps. {ma.get('note', '')}\n"
        )
    L.extend(
        [
            "## The market — who you're up against\n",
            "| App | ★ | Ratings | Price | Updated | Resent% |",
            "|---|--:|--:|---|---|--:|",
        ]
    )
    for c in comps:
        rv = c.get("reviews")
        if rv:
            res = f"{int(rv.get('resent_frac', 0) * 100)}%"
        elif c.get("reviews_unavailable"):
            res = "n/a"
        else:
            res = "—"
        name = (c["app"] or "—").replace("|", "\\|")
        L.append(f"| {name} | {c['rating']} | {c['count']:,} | {c['price'] or '—'} | {c['updated'] or '—'} | {res} |")
    cutoff = time.strftime("%Y-%m", time.gmtime(time.time() - 365 * 86400))
    stale = [c["app"] for c in comps if c["updated"] and c["updated"] < cutoff]
    if stale:
        L.append(f"\n*Aging (no update since {cutoff}):* {', '.join(stale)} — softer targets.")
    L.append("\n## What the market gets wrong — the openings\n")
    for cat, n in sorted(market_gripes.items(), key=lambda x: -x[1]):
        L.append(f"- **{cat}** — {n} complaint(s) across leaders")
        for c in comps:
            for q in (c.get("reviews", {}).get("quotes", {}).get(cat, []))[:1]:
                # collapse literal newlines so a multi-line review body stays one list item
                L.append('    - *"{}"* — {}'.format(" ".join(q["t"].split()), " ".join(q["b"].split())))
                break
    L.append("\n## What users love — preserve these\n")
    L.append(", ".join(f"**{k}** ({v})" for k, v in loves.most_common(8)) or "—")
    if result["wishes"]:
        L.append("\n## Specific feature wishes (from reviews)\n")
        for w in result["wishes"]:
            L.append(f'- "{w}"')
    L.append("\n## The wedge — how to win\n")
    for b in wedge:
        L.append(f"- {b}")
    md_path = os.path.join(outdir, brief + ".md")
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")
    print(f"wrote {md_path} (+ .json)")
    return md_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keyword", required=True)
    ap.add_argument("--top", type=int, default=8)
    ap.add_argument("--pages", type=int, default=3)
    ap.add_argument(
        "--min-ratings", type=int, default=2000, help="only review-mine competitors above this (real incumbents)"
    )
    ap.add_argument("--rate", type=float, default=0, help="max iTunes calls/min (0 = unpaced)")
    args = ap.parse_args()
    md_path = run(args.keyword, top=args.top, pages=args.pages, min_ratings=args.min_ratings, rate=args.rate)
    with open(md_path, encoding="utf-8") as fh:
        print(fh.read(), end="")


if __name__ == "__main__":
    main()
