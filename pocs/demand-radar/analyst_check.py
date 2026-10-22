#!/usr/bin/env python3
"""
DemandRadar — deterministic gate on the Analyst's weekly signals comment.

The headless Analyst (Mary, prompts/weekly-signals-analyst.md) drafts
output/signals-comment.md from the weekly digest and the deep-dives. This check runs twice:
the model runs it before it finishes, and the workflow runs it again from a clean checkout
before anything is posted, so an uncited or fabricated comment never reaches the Discussion.

Rules:
  * at most MAX_IDEAS ideas, one heading each (every heading but the title counts);
  * every line that is not a heading, a blank line or the fixed NO_IDEAS sentence carries a
    citation — `[record: <vertical> / <keyword>]` (a row on the board) or
    `[deep-dive: <slug>]` (a brief under output/deepdive/) — and every citation resolves;
  * no @-mentions; non-empty; at most MAX_CHARS characters.

  python analyst_check.py     # exit 0 = OK, 1 = FAIL (reasons on stderr)
"""

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# Fixed data locations (never argv — see extract.py); tests patch these module globals.
COMMENT_PATH = os.path.join(HERE, "output", "signals-comment.md")
DATA_PATH = os.path.join(HERE, "output", "dashboard-data.json")
DEEPDIVE_DIR = os.path.join(HERE, "output", "deepdive")

MAX_IDEAS = 3
MAX_CHARS = 6000
NO_IDEAS = "No idea cleared the bar this week."
TITLE_PREFIX = "## DemandRadar — weekly signals"
RECORD_RE = re.compile(r"\[record:\s*([a-z0-9-]+)\s*/\s*([^\]]+?)\s*\]", re.I)
DEEPDIVE_RE = re.compile(r"\[deep-dive:\s*([^\]]+?)\s*\]", re.I)
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MENTION_RE = re.compile(r"(?<![\w.])@[A-Za-z0-9]")


def _board(data_path):
    if not os.path.exists(data_path):
        return set()
    try:
        with open(data_path, encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, list):
                return set()
            return {(r.get("vert", "").lower(), r.get("kw", "").lower()) for r in data if isinstance(r, dict)}
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return set()


def check(text, data_path=DATA_PATH, deepdive_dir=DEEPDIVE_DIR):
    """Every reason the comment must not be posted (an empty list means it may)."""
    if not text.strip():
        return ["comment is empty"]
    errs = []
    if len(text) > MAX_CHARS:
        errs.append(f"comment too long ({len(text)} > {MAX_CHARS} characters)")
    board = _board(data_path)
    ideas = 0
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if line.startswith("#"):
            # any heading other than the title is an idea, whatever its level
            if not line.startswith(TITLE_PREFIX):
                ideas += 1
            continue
        if MENTION_RE.search(line):
            errs.append(f"line {n}: @-mention — the comment must not ping anyone")
        if not line or line == NO_IDEAS or line == "---":
            continue
        records = RECORD_RE.findall(line)
        dives = DEEPDIVE_RE.findall(line)
        if not records and not dives:
            errs.append(f"line {n}: no citation — every claim cites [record: …] or [deep-dive: …]: {line[:80]}")
        for vert, kw in records:
            if (vert.lower(), kw.lower()) not in board:
                errs.append(f"line {n}: [record: {vert} / {kw}] is not on the board")
        for s in dives:
            if not SLUG_RE.match(s) or not os.path.exists(os.path.join(deepdive_dir, s + ".md")):
                errs.append(f"line {n}: [deep-dive: {s}] has no brief")
    if ideas > MAX_IDEAS:
        errs.append(f"{ideas} ideas — name at most {MAX_IDEAS}")
    return errs


def main():
    if not os.path.exists(COMMENT_PATH):
        print(f"FAIL: no comment at {COMMENT_PATH}", file=sys.stderr)
        return 1
    try:
        with open(COMMENT_PATH, encoding="utf-8") as f:
            text = f.read()
    except (OSError, UnicodeDecodeError):
        print(f"FAIL: cannot read {COMMENT_PATH}", file=sys.stderr)
        return 1
    errs = check(text, data_path=DATA_PATH, deepdive_dir=DEEPDIVE_DIR)
    for e in errs:
        print(f"FAIL: {e}", file=sys.stderr)
    if errs:
        return 1
    print("OK: every claim cites a board record or a deep-dive")
    return 0


if __name__ == "__main__":
    sys.exit(main())
