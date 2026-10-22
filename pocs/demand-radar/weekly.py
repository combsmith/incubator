"""
DemandRadar — the weekly research session's discovery slice (issue #186).

`pipeline.py --preset weekly` keeps NEW ideas coming instead of only refreshing the numbers
of the fixed priority set. Each ISO week it picks a fresh slice of the idea space:

  * every pending "real user phrase" seed (keyword-seeds.json, flagged `seed`), and
  * the never-scored keywords of VERTICALS_PER_WEEK verticals in rotation. The rotation is
    a pure function of the week, so no cursor has to survive between runs; a rotated
    vertical with nothing left to score hands its place to the next one that has some.

and runs broad -> priority -> supply -> enrich on that slice only. "Pending" means no
record yet (extract never re-scores), so every run adds keywords never scored before until
the whole lexicon is covered — select_slice() reports `exhausted` and the digest says so.

Rate limits: the slice costs at most BROAD_CAP autocomplete calls (far under the ~6k burst
ceiling; already-scored broad rows are free), and the iTunes stages are paced by the caller.
"""

import json
import os

import deep_dive
import select_priority
from errors import StageError
from patterns import slug

HERE = os.path.dirname(os.path.abspath(__file__))
# Fixed data locations (never taken from argv — see extract.py); tests pass paths directly.
OUT = os.path.join(HERE, "output")
KEYWORDS_PATH = os.path.join(OUT, "keywords.jsonl")
BROAD_PATH = os.path.join(OUT, "keywords.broad.jsonl")
RECORDS_PATH = os.path.join(OUT, "records.jsonl")
DATA_PATH = os.path.join(OUT, "dashboard-data.json")
RESENTED_PATH = os.path.join(OUT, "resented.json")
SLICE_PATH = os.path.join(OUT, "keywords.weekly-slice.jsonl")  # broad-pass input
WEEKLY_PATH = os.path.join(OUT, "keywords.weekly.jsonl")  # the supply pass's keyword set

VERTICALS_PER_WEEK = 3
BROAD_CAP = 600  # autocomplete calls per weekly run (the engines IP-ban bursts ~6k)


def _read_jsonl(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _read_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def week_index(day):
    """Weeks since 0001-01-01 (a Monday): constant Monday..Sunday, +1 each Monday."""
    return (day.toordinal() - 1) // 7


def iso_week(day):
    y, w, _ = day.isocalendar()
    return f"{y}-W{w:02d}"


def vertical_order(verticals, day):
    """Every vertical, starting at this week's rotation offset and wrapping around."""
    n = len(verticals)
    if not n:
        return []
    start = (week_index(day) * VERTICALS_PER_WEEK) % n
    return [verticals[(start + i) % n] for i in range(n)]


def rotation(verticals, day, size=VERTICALS_PER_WEEK):
    """This week's verticals. With 25 verticals and 3 a week, gcd(3, 25) = 1, so the window
    visits every vertical within ceil(25 / 3) = 9 weeks."""
    return vertical_order(verticals, day)[: min(size, len(verticals))]


def count_records(path=RECORDS_PATH):
    return len(_read_jsonl(path))


def snapshot(data_path=DATA_PATH, resented_path=RESENTED_PATH, records_path=RECORDS_PATH):
    """What the board looked like before this run — the digest diffs against it (dropped
    entries, newly resented leaders, keywords newly scored)."""
    return {
        "rows": _read_json(data_path, []),
        "resented": _read_json(resented_path, {}),
        "records": count_records(records_path),
    }


def select_slice(
    today,
    keywords_path=KEYWORDS_PATH,
    records_path=RECORDS_PATH,
    broad_path=BROAD_PATH,
    out_path=SLICE_PATH,
    per_week=VERTICALS_PER_WEEK,
    broad_cap=BROAD_CAP,
):
    """Write this week's discovery slice (keyword rows) to out_path and return a summary."""
    if not os.path.exists(keywords_path):
        raise StageError(f"no keywords file at {keywords_path} — run generate_keywords first")
    keywords = _read_jsonl(keywords_path)
    done = {(r.get("industry"), r.get("canonical_query")) for r in _read_jsonl(records_path)}
    has_broad = {
        (r.get("vertical"), r.get("keyword")) for r in _read_jsonl(broad_path) if r.get("broad_interest") is not None
    }
    pending = [k for k in keywords if (k.get("vertical"), k.get("keyword")) not in done]

    verticals = list(dict.fromkeys(k.get("vertical") for k in keywords))
    with_pending = {k.get("vertical") for k in pending if not k.get("seed")}
    chosen = [v for v in vertical_order(verticals, today) if v in with_pending][:per_week]
    seeds = [k for k in pending if k.get("seed")]
    lexicon = [k for k in pending if not k.get("seed") and k.get("vertical") in chosen]

    picked, calls = [], 0
    for k in seeds + lexicon:
        if (k.get("vertical"), k.get("keyword")) not in has_broad:
            if calls >= broad_cap:
                continue  # stays pending: a later week's slice picks it up
            calls += 1
        picked.append(k)
    with open(out_path, "w", encoding="utf-8") as f:
        for k in picked:
            f.write(json.dumps(k) + "\n")

    info = {
        "verticals": chosen,
        "seeds": sum(1 for k in picked if k.get("seed")),
        "slice": len(picked),
        "broad_calls": calls,
        "pending_total": len(pending),
        "exhausted": not pending,
    }
    print(
        f"weekly slice: {len(picked)} keywords ({info['seeds']} seeds) from {', '.join(chosen) or 'no vertical'}; "
        f"{calls} need autocomplete; {len(pending)} never-scored keywords left in the idea space",
        flush=True,
    )
    return info


def pick_priority(slice_path=SLICE_PATH, broad_path=BROAD_PATH, out_path=WEEKLY_PATH, per_vertical=50):
    """The supply pass's keyword set for this week: every broad-scored seed in the slice plus
    the top `per_vertical` lexicon keywords of each rotated vertical by broad demand."""
    keys = {(k.get("vertical"), k.get("keyword")) for k in _read_jsonl(slice_path)}
    rows = {}
    for r in _read_jsonl(broad_path):  # later rows win: a retried failure replaces the failed row
        key = (r.get("vertical"), r.get("keyword"))
        if key in keys and r.get("broad_interest") is not None:
            rows[key] = r
    seeds = [r for r in rows.values() if r.get("seed")]
    picked = seeds + select_priority.rank([r for r in rows.values() if not r.get("seed")], per_vertical)
    select_priority.write(out_path, picked)
    print(f"weekly priority: {len(picked)} keywords ({len(seeds)} seeds) -> {out_path}", flush=True)
    return len(picked)


def priority_keys(path=WEEKLY_PATH):
    """(vertical, keyword) of this week's supply set — the enrich stage's `only` filter."""
    return {(r.get("vertical"), r.get("keyword")) for r in _read_jsonl(path)}


def deep_dives(n=3, rate=18, data_path=DATA_PATH, written=None):
    """Write a deep-dive brief for the top `n` NEW board entries that have none yet (the
    board is already sorted by signal / disruption score). Returns what was written; a dive
    that fails is reported after the others ran, so one throttled keyword fails the stage
    (DEGRADED) without costing the rest."""
    written = [] if written is None else written
    if n <= 0:
        return written
    rows = _read_json(data_path, [])
    todo, slugs = [], set()
    for r in rows:
        kw = r.get("kw")
        if not kw:
            continue
        s = slug(kw)
        if r.get("new") and not r.get("dd") and s not in slugs:
            todo.append(r)
            slugs.add(s)
        if len(todo) >= n:
            break
    failed = []
    for r in todo:
        kw = r.get("kw")
        if not kw:
            continue
        try:
            deep_dive.run(kw, rate=rate)
        except Exception as e:  # noqa: BLE001 — network/throttle: report it, keep going
            print(f"  ! deep dive failed for {kw!r}: {e}", flush=True)
            failed.append(kw)
            continue
        written.append({"kw": kw, "vert": r.get("vert"), "slug": slug(kw), "path": f"deepdive/{slug(kw)}.md"})
    if failed:
        raise StageError(f"deep dive failed for: {', '.join(failed)}")
    return written
