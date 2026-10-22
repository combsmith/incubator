#!/usr/bin/env python3
"""Export candidates + BOTH opportunity lenses to a compact JSON for the dashboard.
 - Gap lens (build an absent/weak niche): score from rank_starter_list.py logic.
 - Disruption lens (attack a proven market with a beatable leader): market_size x dissatisfaction.
Includes a record if it's a non-REJECT gap candidate OR a disruption target.
Each row also carries `seen` (first_seen date), `new` (first seen in the last 7 days — the
board's "New this week" filter and the weekly digest list the same rows) and `dd` (link to
the keyword's deep-dive brief, when one has been written)."""

import json
import math
import os
import re
from datetime import datetime, timedelta, timezone

from patterns import slug
from records import first_seen, load_current

HERE = os.path.dirname(os.path.abspath(__file__))
GAP_W = {"absent-in-store": 3, "absent": 3, "nascent": 2, "stale": 2, "low-quality": 2, "thin": 1, "served": 0}
COMP_W = {"low": 2, "medium": 1, "high": 0}
STOP = {"app", "apps", "the", "for", "best", "free", "pro", "plus", "with", "your"}
DISRUPT_USERS, DISRUPT_RATING = 8000, 4.2
NEW_WINDOW_DAYS = 7  # "New this week": first seen within the last 7 days, today included


def toks(q):
    return [w for w in re.findall(r"[a-z0-9]+", q.lower()) if w not in STOP and len(w) >= 4]


def name_rel(name, q):
    # Whole-word match: tokenize both sides and require every query token to be a WHOLE word
    # in the name, so "counter" no longer matches "encounter" and picks a wrong leaderApp.
    t = toks(q)
    words = set(re.findall(r"[a-z0-9]+", (name or "").lower()))
    return bool(t) and all(x in words for x in t)


def load_labels():
    p = os.path.join(HERE, "labels", "mobileaction-labels.json")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return {lab.get("keyword", "").lower(): lab for lab in json.load(f).get("labels", []) if lab.get("keyword")}
    return {}


def load_broad():
    p = os.path.join(HERE, "output", "keywords.broad.jsonl")
    out = {}
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                if r.get("broad_interest") is not None and r.get("keyword"):
                    out[r.get("keyword", "").lower()] = (r.get("broad_interest") or 0, r.get("app_intent") or 0)
    return out


# Community strength is normalized PER SOURCE: mention units differ wildly (YouTube summed
# views vs. HN/StackExchange/Reddit post counts), so a raw threshold would give a tiny YT view
# count the same bonus as a corroborated HN count. Mirrors enrich_community.THRESHOLDS.
COMMUNITY_THRESHOLDS = {
    "youtube": (50_000, 2_000),
    "hackernews": (300, 50),
    "stackexchange": (25, 3),
    "reddit": (10, 2),
}


def cbonus(m, src=None):
    if m is None:
        return 0
    corr, thin = COMMUNITY_THRESHOLDS.get(src, (300, 50))
    if m >= corr:
        return 2
    return 1 if m >= thin else 0


def load_resented():
    p = os.path.join(HERE, "output", "resented.json")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return {}


def disruption(rec):
    """(market_size, leader_rating, leader_app, is_target). Uses detector fields if present,
    else derives from stored top-5 via name-relevance (lossy for pre-detector records)."""
    sup = rec.get("supply")
    q = rec.get("canonical_query", "")
    if sup is None:
        return 0, None, None, False
    if sup.get("market_size") is not None:  # scored with the new detector
        ms, lr, sols = sup.get("market_size"), sup.get("leader_rating"), sup.get("solutions", [])
        # The detector's leader is the relevant incumbent whose review count IS market_size
        # (extract.analyze). Recover it by that count — the rule resented_giants.py keys
        # resented.json on — so a leader that was relevant through its description rather
        # than its name still resolves. Records with no such match fall back to name relevance.
        lead = next((a for a in sols if ms and (a.get("rating_count") or 0) == ms and a.get("app")), None)
        if lead is None:
            apps = [a for a in sols if name_rel(a.get("app"), q) and a.get("rating")]
            lead = max(apps, key=lambda a: a.get("rating_count") or 0, default=None)
        return ms, lr, (lead or {}).get("app"), bool(sup.get("disruption"))
    apps = [a for a in sup.get("solutions", []) if name_rel(a.get("app"), q) and a.get("rating")]
    if not apps:
        return 0, None, None, False
    lead = max(apps, key=lambda a: a.get("rating_count") or 0)
    ms = lead.get("rating_count") or 0
    lr = lead.get("rating")
    lr = round(lr, 2) if lr else None
    return ms, lr, lead.get("app"), (ms >= DISRUPT_USERS and lr is not None and 1.0 < lr <= DISRUPT_RATING)


def wedge_from(rg):
    """Synthesize a 'how to win' wedge from a resented leader's gripe categories."""
    if not rg:
        return None
    ch = rg.get("cat_hits", {})
    tmpl = {
        "pricing": "Fix the money model \u2014 pricing/paywall is the top complaint; win with a genuinely free tier or a one-time unlock, not another subscription.",
        "ads": "Ship ad-free \u2014 ads are a repeated gripe and 'no ads' is itself a selling point.",
        "enshittification": "Be the simple, un-bloated alternative \u2014 users say it got worse / raised prices / removed basics; restore the clean original.",
        "missing": "Restore the removed/basic features users keep citing.",
    }
    order = sorted([c for c in tmpl if ch.get(c)], key=lambda c: -ch.get(c, 0))
    return [tmpl[c] for c in order[:3]] or None


def deep_dive_link(kw):
    """Relative link (from dashboard.html, and from the Pages site root of the board) to the
    keyword's deep-dive brief, or None when none has been written."""
    rel = f"output/deepdive/{slug(kw)}.md"
    return rel if os.path.exists(os.path.join(HERE, rel)) else None


def main(today=None):
    today = today or datetime.now(timezone.utc).date()
    cutoff = (today - timedelta(days=NEW_WINDOW_DAYS - 1)).isoformat()
    labels, broad, resented = load_labels(), load_broad(), load_resented()
    out = []
    for r in load_current(HERE):
        v = r.get("verdict_heuristic", "")
        ms, lr, lapp, star_dis = disruption(r)
        rg = resented.get((lapp or "").lower()) if lapp else None
        res_flag = bool(rg and rg.get("resented"))
        dis = star_dis or res_flag  # disruption = low-rated giant OR well-rated-but-RESENTED giant
        if v.startswith("REJECT") and not dis:  # keep gap-candidates OR disruption targets
            continue
        gap = r.get("gap", {}).get("gap_type", "")
        comp = r.get("supply", {}).get("competition_intensity", "")
        ch = r.get("discovery_channel", "")
        cm = (r.get("demand") or {}).get("community_metric") or {}
        m = cm.get("mentions")
        m = m if isinstance(m, int) else None
        canonical_kw = r.get("canonical_query", "")
        bi, app_intent = broad.get(canonical_kw.lower(), (0, 0))
        gap_w = GAP_W.get(gap, 0)
        trust = None
        if gap == "absent-in-store":
            if ch == "app-store":
                gap_w = 1.0
                trust = "unverified-absent"
            elif not (app_intent or bi >= 6):
                gap_w = 0.5
        score = gap_w + COMP_W.get(comp, 0) + cbonus(m, cm.get("source")) + app_intent + min(bi, 8) / 4.0
        lab = labels.get(canonical_kw.lower())
        vol = lab.get("volume") if lab else None
        magnote = None
        if ch == "app-store" and lab is not None:
            if vol is not None and vol >= 40:
                score += 2
                magnote = "demand-validated"
            elif vol is not None and vol >= 15:
                score += 1
            else:
                score -= 3
                magnote = "no-store-demand"
        ds_star = math.log10(ms) * max(0.0, 4.6 - lr) if star_dis and ms > 0 and lr else 0.0
        ds_res = math.log10(ms) * rg.get("resent_frac", 0) if res_flag and ms > 0 else 0.0
        dscore = round(max(ds_star, ds_res), 2)
        verdict = "DISRUPT" if dis else v
        sup = r.get("supply") or {}
        seen = first_seen(r)
        out.append(
            {
                "kw": r.get("canonical_query", ""),
                "vert": r.get("industry", ""),
                "ch": ch,
                "gap": gap,
                "comp": comp,
                "sat": sup.get("best_existing_satisfaction"),
                "verdict": verdict,
                "score": round(score, 1),
                "comm": m,
                "commSrc": cm.get("source"),
                "app": app_intent,
                "bi": bi,
                "vol": vol,
                "magnote": magnote,
                "trust": trust,
                "needsMA": (ch == "app-store" and lab is None and not dis),
                "market": ms or None,
                "leaderR": lr,
                "leaderApp": lapp,
                "disrupt": dis,
                "dScore": dscore,
                "resented": res_flag,
                "resentFrac": rg.get("resent_frac") if res_flag else None,
                "resentCats": [
                    c for c in ("pricing", "ads", "enshittification") if res_flag and rg.get("cat_hits", {}).get(c)
                ]
                if res_flag
                else None,
                "gripes": rg.get("gripes") if res_flag else None,
                "wedge": wedge_from(rg) if res_flag else None,
                "bestRating": sup.get("best_existing_rating"),
                "fresh": sup.get("freshest_incumbent_days"),
                "relInc": sup.get("relevant_incumbents"),
                "seen": seen,
                "new": bool(seen and cutoff <= seen <= today.isoformat()),
                "dd": deep_dive_link(canonical_kw),
                "apps": [
                    {
                        "n": a.get("app"),
                        "r": a.get("rating"),
                        "c": a.get("rating_count"),
                        "u": a.get("last_updated_days"),
                    }
                    for a in sup.get("solutions", [])[:5]
                ],
            }
        )
    out.sort(key=lambda x: (-max(x.get("score", 0), (x.get("dScore") or 0) * 2), x.get("kw", "")))
    dest = os.path.join(HERE, "output", "dashboard-data.json")
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(out, f, separators=(",", ":"))
    nd = sum(1 for x in out if x.get("disrupt"))
    nn = sum(1 for x in out if x.get("new"))
    print(
        f"wrote {len(out)} candidates ({nd} disruption targets, {nn} new this week) -> {dest} "
        f"({os.path.getsize(dest) // 1024} KB)"
    )


if __name__ == "__main__":
    main()
