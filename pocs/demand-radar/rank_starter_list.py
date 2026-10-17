#!/usr/bin/env python3
"""
DemandRadar — starter-list ranker (spike, phase 3).

Reads the enriched records, drops the REJECTs, scores the survivors with a simple
transparent heuristic, merges any manual MobileAction magnitude labels, and writes
a ranked `output/starter-list.md` — the robust idea starter list.

It also flags app-store-channel candidates that still lack a magnitude read
(`needs_magnitude`) — that column is the worklist for the manual MobileAction pass.

Score = gap severity + supply-scarcity + community corroboration + autocomplete demand,
then a MobileAction volume boost/penalty for labeled app-store keywords. Deliberately
legible, not tuned — the labeled set (labels/) is what a real scorer trains on.
"""

import json
import os

from records import load_current

HERE = os.path.dirname(os.path.abspath(__file__))
GAP_W = {"absent-in-store": 3, "absent": 3, "nascent": 2, "stale": 2, "low-quality": 2, "thin": 1, "served": 0}
COMP_W = {"low": 2, "medium": 1, "high": 0}
# Community strength is normalized PER SOURCE: mention units differ wildly (YouTube summed
# views vs. HN/StackExchange/Reddit post counts), so the bonus uses each source's
# (corroborate, thin) cutoffs instead of one raw count. Mirrors enrich_community.THRESHOLDS.
COMMUNITY_THRESHOLDS = {
    "youtube": (50_000, 2_000),
    "hackernews": (300, 50),
    "stackexchange": (25, 3),
    "reddit": (10, 2),
}


def load_labels():
    """Load MobileAction labels from file as dict keyed by lowercase keyword."""
    path = os.path.join(HERE, "labels", "mobileaction-labels.json")
    out = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for lab in json.load(f).get("labels", []):
                out[lab["keyword"].lower()] = lab
    return out


def community_bonus(rec):
    """Extract community bonus (0/1/2) and mention count from record's community metric."""
    cm = (rec.get("demand") or {}).get("community_metric") or {}
    m = cm.get("mentions")
    if m is None:
        return 0, None
    corr, thin = COMMUNITY_THRESHOLDS.get(cm.get("source"), (300, 50))
    return (2 if m >= corr else 1 if m >= thin else 0), m


def load_broad():
    """keyword -> (broad_interest, app_intent) from the Google-Suggest broad pass."""
    path = os.path.join(HERE, "output", "keywords.broad.jsonl")
    out = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                if r.get("broad_interest") is not None:
                    out[r["keyword"].lower()] = (r.get("broad_interest") or 0, r.get("app_intent") or 0)
    return out


def _gap_weight(gap, channel, app_intent, bi):
    """(gap weight, trust note) — discounts an "absent-in-store" gap the evidence can't back."""
    gap_w = GAP_W.get(gap, 0)
    if gap != "absent-in-store":
        return gap_w, None
    if channel == "app-store":
        # UNRELIABLE on app-store: usually a relevance false-negative (a real app
        # exists under a different name — 'step calculator' vs 'Pedometer++'). Do NOT
        # let it top the list on 'absent' alone; only MobileAction volume (below) can
        # promote it. Trustworthy app-store signals are stale/low-quality/thin, where
        # we actually matched and assessed real incumbents.
        return 1.0, "unverified-absent"
    if not (app_intent or bi >= 6):
        return 0.5, None  # community nonsense combo (no demand)
    return gap_w, None


def _magnitude_adj(channel, lab, vol):
    """(score delta, note) from a MobileAction label's volume."""
    # Demand-aware: MobileAction magnitude only applies to app-store channel (#44).
    # A labeled app-store candidate with real volume gets a boost; one that is N/A
    # or at the ~5 floor is demand-validated-EMPTY -> heavy demote (real gap, no demand).
    if channel != "app-store" or lab is None:
        return 0, None
    if vol is not None and vol >= 40:
        return 2, "demand-validated"
    if vol is not None and vol >= 15:
        return 1, None
    return -3, "no store demand"  # vol <= ~5 floor, or null/N/A


def _rank_row(r, labels, broad):
    """Compute ranking row for a candidate record."""
    v = r.get("verdict_heuristic", "")
    gap = r["gap"]["gap_type"]
    comp = r["supply"]["competition_intensity"]
    cbonus, mentions = community_bonus(r)
    bi, app_intent = broad.get(r["canonical_query"].lower(), (0, 0))
    gap_w, trust_note = _gap_weight(gap, r["discovery_channel"], app_intent, bi)
    demand_bonus = app_intent + min(bi, 8) / 4.0  # reward real autocomplete demand
    score = gap_w + COMP_W.get(comp, 0) + cbonus + demand_bonus
    lab = labels.get(r["canonical_query"].lower())
    vol = lab["volume"] if lab else None
    delta, mag_note = _magnitude_adj(r["discovery_channel"], lab, vol)
    score += delta
    needs_mag = (r["discovery_channel"] == "app-store") and (lab is None)
    return {
        "score": round(score, 1),
        "kw": r["canonical_query"],
        "group": r["industry"],
        "channel": r["discovery_channel"],
        "gap": gap,
        "comp": comp,
        "sat": r["supply"]["best_existing_satisfaction"],
        "mentions": mentions,
        "demand": f"{app_intent}/{bi}",
        "vol": vol,
        "verdict": v,
        "needs_mag": needs_mag,
        "mag_note": mag_note,
        "trust_note": trust_note,
    }


def _dash(value):
    """Format value as-is or '—' if None."""
    return value if value is not None else "—"


def _table_line(x):
    """Format ranking row as markdown table line."""
    parts = [x["mag_note"], x.get("trust_note")]
    if x["needs_mag"]:
        parts.append("needs MA ▲")
    note = " · ".join(p for p in parts if p)
    return (
        f"| {x['score']} | {x['kw']} | {x['group']} | {x['channel']} | {x['gap']} | "
        f"{x['comp']} | {x['demand']} | {_dash(x['mentions'])} | "
        f"{_dash(x['vol'])} | {x['verdict']} | {note} |\n"
    )


def _write_starter_list(out, rows, n_records):
    """Write ranked starter list to markdown file."""
    with open(out, "w", encoding="utf-8") as f:
        f.write("# DemandRadar — idea starter list (ranked)\n\n")
        f.write(f"{len(rows)} non-REJECT candidates from {n_records} keywords. ")
        f.write(
            "Score = gap severity + supply scarcity + community corroboration + autocomplete demand, "
            "then a MobileAction volume boost/penalty on labeled app-store keywords (legible, untuned).\n\n"
        )
        f.write(
            "`vol` = MobileAction App Store volume (manual label). `—` = no volume: not yet pulled "
            "(app-store rows are then flagged `needs MA ▲`) or pulled and N/A. "
        )
        f.write("`*` in verdict = store gap needing non-store verification.\n\n")
        f.write(
            "`demand` = autocomplete app_intent/broad_interest from the broad pass (nonsense gate). "
            "`community` = mentions from the record's community source (Hacker News / StackExchange / "
            "Reddit post counts, or YouTube summed views) — units differ by source, so treat it as "
            "directional.\n\n"
        )
        f.write(
            "| score | keyword | group | channel | gap | comp | demand | community | store vol | verdict | note |\n"
        )
        f.write("|--:|---|---|---|---|---|:--:|--:|--:|---|---|\n")
        for x in rows:
            f.write(_table_line(x))
        worklist = [x["kw"] for x in rows if x["needs_mag"]]
        f.write(f"\n**MobileAction worklist ({len(worklist)} app-store candidates need magnitude):**\n\n")
        f.write(", ".join(f"`{k}`" for k in worklist) + "\n")


def main():
    """Rank non-REJECT candidates and write starter list with scoring breakdown."""
    records = load_current(HERE)
    labels = load_labels()
    broad = load_broad()

    rows = [_rank_row(r, labels, broad) for r in records if not r.get("verdict_heuristic", "").startswith("REJECT")]
    rows.sort(key=lambda x: (-x["score"], x["group"]))

    out = os.path.join(HERE, "output", "starter-list.md")
    _write_starter_list(out, rows, len(records))

    print(f"Wrote {out}  ({len(rows)} candidates)")
    print("Top 15:")
    for x in rows[:15]:
        print(f"  {x['score']}  {x['kw']:<24} {x['group']:<20} {x['channel']:<10} {x['gap']:<15} {x['verdict']}")


if __name__ == "__main__":
    main()
