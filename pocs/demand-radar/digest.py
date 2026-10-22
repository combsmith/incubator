"""
DemandRadar — the weekly digest (output/weekly-digest.md), written by pipeline.py --preset
weekly after the board data is exported.

A short, link-rich read of what changed this week: the slice that was explored (and
whether the lexicon is exhausted), which community source ran, the board's NEW entries
(exactly the rows the "New this week" filter shows), leaders newly found resented, the
deep-dive briefs written, and the entries that dropped off the board. The Analyst pass
(prompts/weekly-signals-analyst.md) reads this file.
"""

import collections
import json
import os

from resented_giants import SWITCH
from weekly import DATA_PATH, OUT, RESENTED_PATH

OUT_PATH = os.path.join(OUT, "weekly-digest.md")
NONE = "_None this week._"


def _cell(text):
    """A markdown table cell: pipes escaped and newlines flattened so a cell stays one cell."""
    return " ".join(str(text if text is not None else "—").split()).replace("|", "\\|")


def _key(row):
    return row.get("vert"), row.get("kw")


def _brief_link(path):
    # rows link from the board root ("output/deepdive/x.md"); the digest lives in output/
    return f"[brief]({path.removeprefix('output/')})" if path else "—"


def _sources(rows, youtube_key):
    counts = collections.Counter(r.get("commSrc") for r in rows if r.get("commSrc") and r.get("commSrc") != "none")
    ran = ", ".join(f"{src} ×{n}" for src, n in sorted(counts.items(), key=lambda x: (-x[1], x[0]))) or "none"
    note = (
        ""
        if youtube_key
        else " — YouTube skipped (no `YOUTUBE_API_KEY`), so enrich fell back to StackExchange / Hacker News"
    )
    return f"- Community source on this week's entries: {ran}{note}"


def build(today, rows, prev_rows, info, resented_before, resented_after, dives, degraded):
    week = info.get("week") or ""
    L = [f"# DemandRadar — weekly digest · {today.isoformat()} ({week})", ""]
    if degraded:
        L += [
            f"> **DEGRADED** — stage(s) failed: {', '.join(degraded)}. The data below is a partial refresh.",
            "",
        ]

    L += ["## This week's slice", ""]
    if info.get("exhausted"):
        L.append(
            "- **Lexicon exhausted** — every keyword in the idea space has been scored. Add phrases to "
            "`keyword-seeds.json`, or domains / tool types to `generate_keywords.py`, to keep discovery going."
        )
    else:
        L.append(f"- Verticals in rotation: {', '.join(info.get('verticals') or []) or '—'}")
        L.append(f"- User-phrase seeds in the slice: {info.get('seeds', 0)}")
    L.append(f"- **{info.get('scored', 0):,}** keywords scored for the first time this run")
    L.append(f"- Never-scored keywords left in the idea space: {info.get('pending_total', 0):,}")
    new = [r for r in rows if r.get("new")]
    L += [_sources(new, info.get("youtube_key")), ""]

    L += [f"## New this week ({len(new)})", ""]
    if new:
        L += [
            "| # | Idea | Vertical | Verdict | Signal | Disrupt | First seen | Deep-dive |",
            "|--:|---|---|---|--:|--:|---|---|",
        ]
        for i, r in enumerate(new, 1):
            L.append(
                f"| {i} | {_cell(r.get('kw', ''))} | {_cell(r.get('vert'))} | {_cell(r.get('verdict'))} | "
                f"{r.get('score', 0)} | {r.get('dScore') or 0} | {_cell(r.get('seen'))} | {_brief_link(r.get('dd'))} |"
            )
    else:
        L.append(NONE)
    L.append("")

    fresh = [
        v for k, v in resented_after.items() if v.get("resented") and not (resented_before.get(k) or {}).get("resented")
    ]
    fresh.sort(key=lambda v: -(v.get("resent_frac") or 0))
    L += [f"## Newly resented leaders ({len(fresh)})", ""]
    for v in fresh:
        cats = ", ".join(c for c in SWITCH if (v.get("cat_hits") or {}).get(c)) or "—"
        L.append(
            f"- **{_cell(v.get('app'))}** — {round((v.get('resent_frac') or 0) * 100)}% of recent 1–3★ reviews resent it "
            f"({cats}); market {v.get('market') or 0:,} reviews; e.g. “{_cell(v.get('kw'))}” [{_cell(v.get('vert'))}]"
        )
    L += [NONE] if not fresh else []
    L.append("")

    L += [f"## Deep-dives written ({len(dives)})", ""]
    for d in dives:
        L.append(f"- [{_cell(d.get('kw', ''))}]({d.get('path', '')}) — {_cell(d.get('vert'))}")
    L += [NONE] if not dives else []
    L.append("")

    now = {_key(r) for r in rows}
    dropped = [r for r in prev_rows if _key(r) not in now]
    L += [f"## Dropped off the board ({len(dropped)})", ""]
    for r in dropped:
        L.append(f"- {_cell(r.get('kw'))} [{_cell(r.get('vert'))}] — was {_cell(r.get('verdict'))}")
    L += [NONE] if not dropped else []
    L.append("")
    return "\n".join(L)


def run(today, info, before, dives, degraded, data_path=DATA_PATH, resented_path=RESENTED_PATH, out_path=OUT_PATH):
    try:
        with open(data_path, encoding="utf-8") as f:
            rows = json.load(f)
            if not isinstance(rows, list):
                rows = []
    except (OSError, json.JSONDecodeError):  # file-access / JSON decode error
        rows = []
    resented = {}
    if os.path.exists(resented_path):
        try:
            with open(resented_path, encoding="utf-8") as f:
                resented = json.load(f)
                if not isinstance(resented, dict):
                    resented = {}
        except (OSError, json.JSONDecodeError):
            resented = {}
    md = build(
        today=today,
        rows=rows,
        prev_rows=before.get("rows") or [],
        info=info,
        resented_before=before.get("resented") or {},
        resented_after=resented,
        dives=dives,
        degraded=degraded,
    )
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"wrote {out_path}")
    return out_path
