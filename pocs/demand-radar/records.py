"""Loading the current opportunity records for the reporting stages
(export_dashboard.py, rank_starter_list.py), and stamping their first_seen date."""

import json
import os


def _read(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def _key(rec):
    return rec.get("industry"), rec.get("canonical_query")


def merge(base, enriched):
    """Every record in `base`, each replaced by its copy in `enriched` when it has one.

    The enriched copy is a rewrite from an earlier run, so it may predate the base row's
    first_seen stamp: the base date is carried over rather than lost."""
    if not os.path.exists(enriched):
        return _read(base)
    enriched_rows = _read(enriched)
    if not os.path.exists(base):
        return enriched_rows
    by_key = {_key(r): r for r in enriched_rows}
    out = []
    for r in _read(base):
        e = by_key.get(_key(r))
        if e is None:
            out.append(r)
        elif "first_seen" not in e and "first_seen" in r:
            out.append({**e, "first_seen": r["first_seen"]})
        else:
            out.append(e)
    return out


def load_current(here):
    """Every record scored so far, each in its most enriched form.

    output/records.jsonl is appended to by every supply batch; output/records.enriched.jsonl
    is a full rewrite from the last *successful* enrichment. Reading only the enriched file
    would hide records appended after an enrichment that failed or was skipped, so start from
    the base file and overlay the enriched copy of each record that has one."""
    return merge(
        os.path.join(here, "output", "records.jsonl"),
        os.path.join(here, "output", "records.enriched.jsonl"),
    )


def first_seen(rec):
    """The date a record entered the board: its stamp, else the day it was scored (extract
    never re-scores, so captured_at is the first sighting for records older than the stamp)."""
    return rec.get("first_seen") or (rec.get("captured_at") or "")[:10] or None


def stamp_first_seen(path, today):
    """Give every record in `path` a first_seen date (YYYY-MM-DD); return how many were
    stamped. Records that already carry one keep it, so the stamp is set exactly once."""
    if not os.path.exists(path):
        return 0
    rows = _read(path)
    n = 0
    for r in rows:
        if not r.get("first_seen"):
            r["first_seen"] = first_seen(r) or today.isoformat()
            n += 1
    if n:
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        os.replace(tmp, path)
    return n
