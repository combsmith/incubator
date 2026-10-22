"""Unit tests for the weekly research session (issue #186): the rotated discovery slice,
first_seen stamping, the export's new/deep-dive fields, the digest, the weekly pipeline
preset, and the Analyst comment gate + poster. Hermetic like the rest of the suite: no
network (FakeHTTP / faked stages), no real sleeping, tmp_path files only."""

import json
from datetime import date
from pathlib import Path

import pytest
from helpers import FakeResponse, make_record, read_jsonl

import analyst_check
import deep_dive
import digest
import enrich_community as enrich
import errors
import export_dashboard as dash
import generate_keywords
import patterns
import pipeline
import post_signals
import records
import select_priority
import weekly

MONDAY = date(2026, 10, 26)


def kw(keyword, vertical, seed=False):
    row = {"keyword": keyword, "vertical": vertical, "discovery_channel": "app-store", "vertical_dynamics": "mixed"}
    if seed:
        row["seed"] = True
    return row


def broad(keyword, vertical, bi=1, seed=False):
    return {**kw(keyword, vertical, seed), "broad_interest": bi, "app_intent": 0, "n_suggestions": bi}


def scored(keyword, vertical, **extra):
    return {**make_record(keyword, industry=vertical), **extra}


# ───────────────────────── rotation ─────────────────────────


class TestRotation:
    VERTS = [f"v{i}" for i in range(25)]

    def test_three_verticals_per_week_deterministic(self):
        assert weekly.rotation(self.VERTS, MONDAY) == weekly.rotation(self.VERTS, MONDAY)
        assert len(weekly.rotation(self.VERTS, MONDAY)) == 3

    def test_the_whole_iso_week_shares_one_rotation(self):
        sunday = date(2026, 11, 1)
        assert weekly.rotation(self.VERTS, MONDAY) == weekly.rotation(self.VERTS, sunday)
        assert weekly.rotation(self.VERTS, MONDAY) != weekly.rotation(self.VERTS, date(2026, 11, 2))

    def test_consecutive_weeks_cover_every_vertical(self):
        seen = set()
        for week in range(9):  # ceil(25 / 3)
            seen.update(weekly.rotation(self.VERTS, date.fromordinal(MONDAY.toordinal() + 7 * week)))
        assert seen == set(self.VERTS)

    def test_wraps_and_handles_small_or_empty_lists(self):
        assert sorted(weekly.rotation(["a", "b"], MONDAY)) == ["a", "b"]
        assert weekly.rotation([], MONDAY) == []

    def test_order_starts_at_the_rotation_and_wraps(self):
        order = weekly.vertical_order(self.VERTS, MONDAY)
        assert sorted(order) == sorted(self.VERTS)
        assert order[:3] == weekly.rotation(self.VERTS, MONDAY)


# ───────────────────────── weekly slice ─────────────────────────


class TestSelectSlice:
    @pytest.fixture
    def paths(self, tmp_path):
        return {
            "keywords_path": str(tmp_path / "keywords.jsonl"),
            "records_path": str(tmp_path / "records.jsonl"),
            "broad_path": str(tmp_path / "broad.jsonl"),
            "out_path": str(tmp_path / "slice.jsonl"),
        }

    def test_slice_is_never_scored_keywords_of_the_rotated_verticals_plus_seeds(self, paths, write_jsonl):
        verts = [f"v{i}" for i in range(6)]
        rows = [kw(f"{v} {t}", v) for v in verts for t in ("tracker", "planner")]
        rows.append(kw("minecraft world backup", "v5", seed=True))
        write_jsonl(Path(paths["keywords_path"]), rows)
        rot = weekly.rotation(verts, MONDAY)
        done = rot[0]
        write_jsonl(Path(paths["records_path"]), [scored(f"{done} tracker", done)])

        info = weekly.select_slice(MONDAY, per_week=3, **paths)

        picked = read_jsonl(paths["out_path"])
        keys = {(r["vertical"], r["keyword"]) for r in picked}
        assert (done, f"{done} tracker") not in keys  # never re-scores
        assert (done, f"{done} planner") in keys
        assert ("v5", "minecraft world backup") in keys  # seeds ride along whatever the rotation
        assert {r["vertical"] for r in picked if not r.get("seed")} == set(rot)
        assert info["verticals"] == rot
        assert info["seeds"] == 1
        assert info["slice"] == len(picked)
        assert info["pending_total"] == len(rows) - 1
        assert info["exhausted"] is False

    def test_exhausted_verticals_fall_through_to_the_next_with_pending(self, paths, write_jsonl):
        verts = ["a", "b", "c", "d", "e"]
        write_jsonl(Path(paths["keywords_path"]), [kw(f"{v} log", v) for v in verts])
        order = weekly.vertical_order(verts, MONDAY)
        write_jsonl(Path(paths["records_path"]), [scored(f"{v} log", v) for v in order[:3]])
        info = weekly.select_slice(MONDAY, per_week=3, **paths)
        assert info["verticals"] == order[3:]
        assert info["exhausted"] is False

    def test_reports_an_exhausted_lexicon(self, paths, write_jsonl):
        write_jsonl(Path(paths["keywords_path"]), [kw("a log", "a"), kw("b log", "b")])
        write_jsonl(Path(paths["records_path"]), [scored("a log", "a"), scored("b log", "b")])
        info = weekly.select_slice(MONDAY, **paths)
        assert info["exhausted"] is True
        assert info["slice"] == 0
        assert info["verticals"] == []
        assert read_jsonl(paths["out_path"]) == []

    def test_unscored_autocomplete_calls_are_capped(self, paths, write_jsonl):
        rows = [kw(f"a thing {i}", "a") for i in range(10)]
        write_jsonl(Path(paths["keywords_path"]), rows)
        # two already have a broad score (free); the other eight need an autocomplete call
        write_jsonl(Path(paths["broad_path"]), [broad("a thing 0", "a"), broad("a thing 1", "a")])
        info = weekly.select_slice(MONDAY, broad_cap=3, **paths)
        picked = [r["keyword"] for r in read_jsonl(paths["out_path"])]
        assert picked == ["a thing 0", "a thing 1", "a thing 2", "a thing 3", "a thing 4"]
        assert info["broad_calls"] == 3

    def test_missing_keyword_file_is_a_stage_error(self, paths):
        with pytest.raises(errors.StageError, match="keywords"):
            weekly.select_slice(MONDAY, **paths)


class TestPickPriority:
    def test_top_k_per_vertical_of_the_slice_and_every_seed(self, tmp_path, write_jsonl):
        slice_rows = [kw("a one", "a"), kw("a two", "a"), kw("a three", "a"), kw("a seed", "a", seed=True)]
        slice_path = write_jsonl(tmp_path / "slice.jsonl", slice_rows)
        broad_path = write_jsonl(
            tmp_path / "broad.jsonl",
            [
                {**broad("a one", "a", bi=1), "broad_interest": None, "error": True},  # failed, then retried
                broad("a one", "a", bi=5),
                broad("a two", "a", bi=3),
                broad("a three", "a", bi=1),
                broad("a seed", "a", bi=0, seed=True),
                broad("not in slice", "a", bi=99),
            ],
        )
        out = tmp_path / "weekly.jsonl"
        n = weekly.pick_priority(slice_path=slice_path, broad_path=broad_path, out_path=str(out), per_vertical=2)
        rows = read_jsonl(out)
        assert [r["keyword"] for r in rows] == ["a seed", "a one", "a two"]
        assert n == 3

    def test_priority_keys(self, tmp_path, write_jsonl):
        p = write_jsonl(tmp_path / "w.jsonl", [kw("a one", "a"), kw("b one", "b")])
        assert weekly.priority_keys(p) == {("a", "a one"), ("b", "b one")}
        assert weekly.priority_keys(str(tmp_path / "missing.jsonl")) == set()


class TestSelectPriorityRank:
    def test_rank_is_reusable(self):
        rows = [broad("x", "a", bi=1), broad("y", "a", bi=4), broad("z", "b", bi=2)]
        assert [r["keyword"] for r in select_priority.rank(rows, 1)] == ["y", "z"]


# ───────────────────────── seeds ─────────────────────────


class TestSeeds:
    def test_user_phrase_seeds_enter_the_idea_space_flagged(self, tmp_path, monkeypatch):
        monkeypatch.setattr(generate_keywords, "VERTICALS", {"a": ("community", "mixed", ["dog"])})
        seeds = tmp_path / "seeds.json"
        seeds.write_text(
            json.dumps({"seeds": {"a": ["minecraft world backup", "dog tracker"], "nope": ["lost seed"]}}),
            encoding="utf-8",
        )
        out = tmp_path / "k.jsonl"
        n = generate_keywords.run(out=str(out), n_tools=1, seeds_path=str(seeds))
        rows = read_jsonl(out)
        assert n == 2  # "dog tracker" is already in the grid; the unknown vertical is skipped
        assert rows[-1] == {
            "keyword": "minecraft world backup",
            "vertical": "a",
            "discovery_channel": "community",
            "vertical_dynamics": "mixed",
            "seed": True,
        }

    def test_missing_seed_file_means_no_seeds(self, tmp_path, monkeypatch):
        monkeypatch.setattr(generate_keywords, "VERTICALS", {"a": ("community", "mixed", ["dog"])})
        out = tmp_path / "k.jsonl"
        assert generate_keywords.run(out=str(out), n_tools=1, seeds_path=str(tmp_path / "none.json")) == 1

    def test_committed_seed_file_only_names_known_verticals(self):
        with open(generate_keywords.SEEDS_PATH, encoding="utf-8") as f:
            seeds = json.load(f)["seeds"]
        assert seeds
        assert set(seeds) <= set(generate_keywords.VERTICALS)


# ───────────────────────── first_seen ─────────────────────────


class TestFirstSeen:
    def test_new_records_are_stamped_with_their_capture_date(self):
        import extract

        sig = extract.analyze("mood tracker", [])
        rec = extract.to_record({"name": "v"}, "mood tracker", sig, "2026-10-26T06:20:00Z")
        assert rec["first_seen"] == "2026-10-26"

    def test_backfill_from_captured_at_else_today_and_keeps_existing(self, tmp_path, write_jsonl):
        path = write_jsonl(
            tmp_path / "records.jsonl",
            [
                {**make_record("old"), "captured_at": "2026-07-22T02:52:55Z"},
                {**make_record("kept"), "captured_at": "2026-08-01T00:00:00Z", "first_seen": "2026-07-30"},
                make_record("undated"),
            ],
        )
        assert records.stamp_first_seen(path, MONDAY) == 2
        assert [r["first_seen"] for r in read_jsonl(path)] == ["2026-07-22", "2026-07-30", "2026-10-26"]
        assert records.stamp_first_seen(path, MONDAY) == 0  # idempotent

    def test_stamping_a_missing_file_is_a_no_op(self, tmp_path):
        assert records.stamp_first_seen(str(tmp_path / "none.jsonl"), MONDAY) == 0

    def test_enriched_overlay_keeps_the_base_first_seen(self, tmp_path, write_jsonl):
        write_jsonl(tmp_path / "output" / "records.jsonl", [{**make_record("dog log"), "first_seen": "2026-10-26"}])
        write_jsonl(tmp_path / "output" / "records.enriched.jsonl", [make_record("dog log")])
        assert records.load_current(str(tmp_path))[0]["first_seen"] == "2026-10-26"


# ───────────────────────── enrich on the slice only ─────────────────────────


class TestEnrichOnly:
    def test_only_targets_the_slice_and_keeps_earlier_metrics(self, tmp_path, write_jsonl, monkeypatch):
        earlier = {"source": "stackexchange", "mentions": 30}
        base = write_jsonl(tmp_path / "records.jsonl", [make_record("old", industry="pets"), make_record("new")])
        out = write_jsonl(tmp_path / "enriched.jsonl", [make_record("old", industry="pets", community=earlier)])
        asked = []

        def fake(record, *a):
            asked.append(record["canonical_query"])
            return {"source": "hackernews", "mentions": 99}

        monkeypatch.setattr(enrich, "fetch_for", fake)
        monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)
        enrich.run(inp=base, out=out, only={("pets", "new")}, max_n=10)
        assert asked == ["new"]
        by_kw = {r["canonical_query"]: r for r in read_jsonl(out)}
        assert by_kw["old"]["demand"]["community_metric"] == earlier
        assert by_kw["new"]["demand"]["community_metric"]["mentions"] == 99


# ───────────────────────── deep dives from the pipeline ─────────────────────────


class TestDeepDiveRun:
    def test_run_is_callable_and_paced(self, tmp_path, monkeypatch, sleeps):
        monkeypatch.setattr(deep_dive, "HERE", str(tmp_path))
        calls = []

        def fake_get(url):
            calls.append(url)
            if "search" in url:
                return json.dumps({"results": [{"trackName": "Daylio", "trackId": 1, "userRatingCount": 5000}]})
            return json.dumps({"feed": {"entry": [{"im:rating": {"label": "1"}, "content": {"label": "paywall"}}]}})

        monkeypatch.setattr(deep_dive, "_fetch", fake_get)
        clock = [1000.0]
        monkeypatch.setattr(deep_dive.time, "time", lambda: clock[0])
        monkeypatch.setattr(deep_dive, "_next_at", [0.0])  # no slot left over from another test
        path = deep_dive.run("Mood Tracker", pages=1, min_ratings=100, rate=20)
        assert path == str(tmp_path / "output" / "deepdive" / "mood-tracker.md")
        assert (tmp_path / "output" / "deepdive" / "mood-tracker.json").exists()
        assert len(calls) == 2
        assert 3.0 in sleeps  # 60 / 20 between iTunes calls (the clock never advanced)

    def test_slug_is_shared(self):
        assert patterns.slug("Guitar Chords!") == "guitar-chords"
        assert patterns.slug("D&D  character sheet") == "d-d-character-sheet"


class TestWeeklyDeepDives:
    def test_top_new_entries_without_a_brief_get_one(self, tmp_path, monkeypatch):
        rows = [
            {"kw": "old idea", "vert": "a", "new": False},
            {"kw": "has brief", "vert": "a", "new": True, "dd": "output/deepdive/has-brief.md"},
            {"kw": "first", "vert": "a", "new": True, "dd": None},
            {"kw": "second", "vert": "b", "new": True, "dd": None},
            {"kw": "third", "vert": "b", "new": True, "dd": None},
        ]
        data = tmp_path / "dashboard-data.json"
        data.write_text(json.dumps(rows), encoding="utf-8")
        ran = []
        monkeypatch.setattr(weekly.deep_dive, "run", lambda keyword, **k: ran.append((keyword, k)) or "p")
        out = weekly.deep_dives(n=2, rate=18, data_path=str(data))
        assert [k for k, _ in ran] == ["first", "second"]
        assert ran[0][1] == {"rate": 18}
        assert out == [
            {"kw": "first", "vert": "a", "slug": "first", "path": "deepdive/first.md"},
            {"kw": "second", "vert": "b", "slug": "second", "path": "deepdive/second.md"},
        ]

    def test_a_failed_dive_is_reported_after_the_rest_ran(self, tmp_path, monkeypatch):
        rows = [{"kw": "boom", "vert": "a", "new": True}, {"kw": "fine", "vert": "a", "new": True}]
        data = tmp_path / "d.json"
        data.write_text(json.dumps(rows), encoding="utf-8")

        def fake(keyword, **k):
            if keyword == "boom":
                raise OSError("403")
            return "p"

        monkeypatch.setattr(weekly.deep_dive, "run", fake)
        written = []
        with pytest.raises(errors.StageError, match="boom"):
            weekly.deep_dives(n=3, rate=18, data_path=str(data), written=written)
        assert [d["kw"] for d in written] == ["fine"]

    def test_zero_means_none(self, tmp_path):
        assert weekly.deep_dives(n=0, rate=18, data_path=str(tmp_path / "missing.json")) == []


# ───────────────────────── export: seen / new / dd ─────────────────────────


class TestExportNewFields:
    def test_rows_carry_first_seen_new_flag_and_deep_dive_link(self, tmp_path, write_jsonl, monkeypatch):
        write_jsonl(
            tmp_path / "output" / "records.jsonl",
            [
                {**make_record("fresh idea"), "first_seen": "2026-10-26"},
                {**make_record("last week"), "first_seen": "2026-10-19"},
                {**make_record("legacy"), "captured_at": "2026-10-21T00:00:00Z"},
            ],
        )
        (tmp_path / "output" / "deepdive").mkdir()
        (tmp_path / "output" / "deepdive" / "fresh-idea.md").write_text("# brief", encoding="utf-8")
        monkeypatch.setattr(dash, "HERE", str(tmp_path))
        dash.main(today=MONDAY)
        rows = {r["kw"]: r for r in json.loads((tmp_path / "output" / "dashboard-data.json").read_text())}
        assert rows["fresh idea"]["seen"] == "2026-10-26"
        assert rows["fresh idea"]["new"] is True
        assert rows["fresh idea"]["dd"] == "output/deepdive/fresh-idea.md"
        assert rows["last week"]["new"] is False
        assert rows["last week"]["dd"] is None
        assert rows["legacy"]["seen"] == "2026-10-21"
        assert rows["legacy"]["new"] is True  # inside the 7-day window


# ───────────────────────── digest ─────────────────────────


def drow(kw_, vert="pets", new=True, **extra):
    base = {"kw": kw_, "vert": vert, "verdict": "CANDIDATE", "score": 7.5, "dScore": 0.0, "new": new}
    base.update({"dd": None, "commSrc": None, "seen": "2026-10-26"})
    base.update(extra)
    return base


class TestDigest:
    INFO = {
        "week": "2026-W44",
        "verticals": ["pets", "travel", "home-diy"],
        "seeds": 4,
        "slice": 160,
        "pending_total": 9000,
        "exhausted": False,
        "scored": 150,
        "youtube_key": False,
    }

    def build(self, **over):
        args = {
            "today": MONDAY,
            "rows": [
                drow("dog | walk log", commSrc="stackexchange", dd="output/deepdive/dog-walk-log.md"),
                drow("trip planner", vert="travel", commSrc="hackernews"),
                drow("old thing", new=False),
            ],
            "prev_rows": [drow("old thing", new=False), drow("gone idea", vert="travel")],
            "info": dict(self.INFO),
            "resented_before": {"quizlet": {"app": "Quizlet", "resented": True}},
            "resented_after": {
                "quizlet": {"app": "Quizlet", "resented": True},
                "camscanner": {
                    "app": "CamScanner",
                    "resented": True,
                    "resent_frac": 0.46,
                    "market": 120000,
                    "kw": "pdf scanner",
                    "vert": "everyday-utilities",
                    "cat_hits": {"pricing": 5, "ads": 2, "enshittification": 0},
                },
                "calm": {"app": "Calm", "resented": False},
            },
            "dives": [
                {"kw": "dog | walk log", "vert": "pets", "slug": "dog-walk-log", "path": "deepdive/dog-walk-log.md"}
            ],
            "degraded": [],
        }
        args.update(over)
        return digest.build(**args)

    def test_sections(self):
        md = self.build()
        assert md.startswith("# DemandRadar — weekly digest · 2026-10-26 (2026-W44)")
        assert "pets, travel, home-diy" in md
        assert "**150** keywords scored for the first time" in md
        assert "9,000" in md
        # new candidates = the board's New this week rows, pipes escaped, deep-dive linked
        assert "## New this week (2)" in md
        assert "dog \\| walk log" in md
        assert "[brief](deepdive/dog-walk-log.md)" in md
        assert "old thing" not in md.split("## New this week")[1].split("##")[0]
        # newly resented leaders only
        assert "## Newly resented leaders (1)" in md
        assert "**CamScanner** — 46%" in md
        assert "pricing, ads" in md
        assert "Quizlet" not in md
        assert "## Deep-dives written (1)" in md
        assert "## Dropped off the board (1)" in md
        assert "gone idea" in md
        assert "DEGRADED" not in md

    def test_names_the_community_source_that_ran(self):
        md = self.build()
        assert "hackernews ×1" in md and "stackexchange ×1" in md
        assert "YouTube skipped (no `YOUTUBE_API_KEY`)" in md
        md = self.build(info={**self.INFO, "youtube_key": True})
        assert "YouTube skipped" not in md

    def test_says_when_the_lexicon_is_exhausted(self):
        md = self.build(info={**self.INFO, "exhausted": True, "pending_total": 0, "scored": 0, "verticals": []})
        assert "**Lexicon exhausted**" in md
        assert "keyword-seeds.json" in md

    def test_degraded_and_empty_sections(self):
        md = self.build(
            rows=[], prev_rows=[], resented_after={}, resented_before={}, dives=[], degraded=["supply (iTunes)"]
        )
        assert "**DEGRADED**" in md and "supply (iTunes)" in md
        assert "## New this week (0)" in md
        assert md.count("_None this week._") == 4

    def test_run_writes_the_file(self, tmp_path):
        (tmp_path / "dashboard-data.json").write_text(json.dumps([drow("a")]), encoding="utf-8")
        out = tmp_path / "weekly-digest.md"
        before = {"rows": [], "resented": {}, "records": 0}
        path = digest.run(
            MONDAY,
            dict(self.INFO),
            before,
            [],
            [],
            data_path=str(tmp_path / "dashboard-data.json"),
            resented_path=str(tmp_path / "missing.json"),
            out_path=str(out),
        )
        assert path == str(out)
        assert "## New this week (1)" in out.read_text(encoding="utf-8")


class TestSnapshot:
    def test_snapshot_reads_what_exists(self, tmp_path, write_jsonl):
        (tmp_path / "d.json").write_text(json.dumps([drow("a")]), encoding="utf-8")
        write_jsonl(tmp_path / "r.jsonl", [make_record("a"), make_record("b")])
        snap = weekly.snapshot(
            data_path=str(tmp_path / "d.json"),
            resented_path=str(tmp_path / "none.json"),
            records_path=str(tmp_path / "r.jsonl"),
        )
        assert snap == {"rows": [drow("a")], "resented": {}, "records": 2}

    def test_count_records(self, tmp_path):
        assert weekly.count_records(str(tmp_path / "none.jsonl")) == 0


# ───────────────────────── pipeline --preset weekly ─────────────────────────


class TestWeeklyPreset:
    @pytest.fixture
    def stages(self, monkeypatch):
        calls = []
        fail = {}

        def recorder(name, ret=None):
            def stage(*a, **kw):
                calls.append((name, kw))
                if name in fail:
                    raise fail[name]
                return ret

            return stage

        monkeypatch.setattr(pipeline, "_today", lambda: MONDAY)
        monkeypatch.setattr(pipeline.weekly, "snapshot", lambda: {"rows": [], "resented": {}, "records": 10})
        monkeypatch.setattr(pipeline.weekly, "count_records", lambda *a: 25)
        monkeypatch.setattr(pipeline.weekly, "priority_keys", lambda *a: {("a", "x")})
        monkeypatch.setattr(pipeline.generate_keywords, "run", recorder("generate"))
        monkeypatch.setattr(
            pipeline.weekly,
            "select_slice",
            recorder("slice", {"verticals": ["a"], "slice": 1, "pending_total": 5, "exhausted": False}),
        )
        monkeypatch.setattr(pipeline.broad_pass, "run", recorder("broad"))
        monkeypatch.setattr(pipeline.weekly, "pick_priority", recorder("pick"))
        monkeypatch.setattr(pipeline.extract, "run", recorder("extract"))
        monkeypatch.setattr(pipeline.records, "stamp_first_seen", recorder("stamp"))
        monkeypatch.setattr(pipeline.enrich_community, "run", recorder("enrich"))
        monkeypatch.setattr(pipeline.resented_giants, "run", recorder("resented"))
        monkeypatch.setattr(pipeline.export_dashboard, "main", recorder("export"))

        def dives(**kw):
            calls.append(("deepdive", kw))
            kw["written"].append({"kw": "x", "vert": "a", "slug": "x", "path": "deepdive/x.md"})
            if "deepdive" in fail:
                raise fail["deepdive"]

        monkeypatch.setattr(pipeline.weekly, "deep_dives", dives)
        monkeypatch.setattr(pipeline.rank_starter_list, "main", recorder("rank"))
        monkeypatch.setattr(pipeline.digest, "run", recorder("digest"))
        monkeypatch.setattr(pipeline, "build_dashboard", recorder("build"))
        monkeypatch.delenv("DR_COMMUNITY_SOURCE", raising=False)
        monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)
        return calls, fail

    def test_runs_discovery_on_the_slice_only_within_the_limits(self, stages, argv, capsys):
        calls, _ = stages
        argv("--preset", "weekly")
        pipeline.main()
        assert [n for n, _ in calls] == [
            "generate",
            "slice",
            "broad",
            "pick",
            "extract",
            "stamp",
            "enrich",
            "resented",
            "export",
            "deepdive",
            "export",
            "rank",
            "digest",
            "build",
        ]
        kw_ = dict(calls)
        assert kw_["slice"]["broad_cap"] == pipeline.weekly.BROAD_CAP
        assert kw_["broad"] == {"inp": pipeline.weekly.SLICE_PATH, "workers": 2, "engine": "ddg"}
        assert kw_["pick"] == {"per_vertical": 50}
        assert kw_["extract"] == {"keywords_path": pipeline.weekly.WEEKLY_PATH, "workers": 2, "rate": 18, "max_n": 240}
        assert kw_["enrich"] == {"source": "", "max_n": 240, "only": {("a", "x")}}
        assert kw_["resented"] == {"max_n": 40, "sleep": pipeline.RESENTED_SLEEP}
        assert kw_["deepdive"]["n"] == 3 and kw_["deepdive"]["rate"] == 18
        assert "pipeline complete" in capsys.readouterr().out

    def test_digest_gets_the_run_summary(self, stages, argv):
        calls, _ = stages
        argv("--preset", "weekly", "--deep-dives", "1")
        pipeline.main()
        digest_kw = dict(calls)["digest"]
        assert digest_kw["today"] == MONDAY
        assert digest_kw["info"]["scored"] == 15
        assert digest_kw["info"]["week"] == "2026-W44"
        assert digest_kw["info"]["youtube_key"] is False
        assert digest_kw["dives"] == [{"kw": "x", "vert": "a", "slug": "x", "path": "deepdive/x.md"}]
        assert digest_kw["degraded"] == []
        assert dict(calls)["deepdive"]["n"] == 1

    def test_a_ban_degrades_the_run_but_still_writes_digest_and_board(self, stages, argv, capsys):
        calls, fail = stages
        fail["extract"] = errors.StageError("iTunes fetches kept failing")
        fail["deepdive"] = errors.StageError("deep dive failed for: x")
        argv("--preset", "weekly")
        with pytest.raises(SystemExit) as exc:
            pipeline.main()
        assert exc.value.code == 1
        names = [n for n, _ in calls]
        assert names[-2:] == ["digest", "build"]
        assert dict(calls)["digest"]["degraded"] == ["supply (iTunes)", "deep dives"]
        assert "DEGRADED" in capsys.readouterr().err

    def test_rejects_negative_weekly_caps(self, stages, argv):
        argv("--preset", "weekly", "--deep-dives", "-1")
        with pytest.raises(SystemExit) as exc:
            pipeline.main()
        assert exc.value.code == 2


# ───────────────────────── Analyst comment gate ─────────────────────────


GOOD_COMMENT = """## DemandRadar — weekly signals · 2026-10-26

### 1. Dog walk log
- Emerging gap: a tiny incumbent and low competition [record: pets / dog walk log]
- The leader's reviews complain about the paywall [deep-dive: dog-walk-log]

### 2. Trip planner
- Corroborated by community chatter [record: travel / trip planner]
"""


class TestAnalystCheck:
    @pytest.fixture
    def data(self, tmp_path):
        rows = [drow("dog walk log"), drow("trip planner", vert="travel")]
        (tmp_path / "dashboard-data.json").write_text(json.dumps(rows), encoding="utf-8")
        (tmp_path / "deepdive").mkdir()
        (tmp_path / "deepdive" / "dog-walk-log.md").write_text("# brief", encoding="utf-8")
        return tmp_path

    def check(self, data, text):
        return analyst_check.check(
            text, data_path=str(data / "dashboard-data.json"), deepdive_dir=str(data / "deepdive")
        )

    def test_a_cited_comment_passes(self, data):
        assert self.check(data, GOOD_COMMENT) == []

    def test_no_ideas_is_a_valid_week(self, data):
        text = "## DemandRadar — weekly signals · 2026-10-26\n\nNo idea cleared the bar this week.\n"
        assert self.check(data, text) == []

    def test_more_than_three_ideas_fails(self, data):
        idea = "### {n}. Dog\n- gap [record: pets / dog walk log]\n"
        text = "".join(idea.format(n=i) for i in range(4))
        assert any("at most 3" in e for e in self.check(data, text))

    def test_other_heading_levels_count_as_ideas(self, data):
        idea = "## {n}. Dog\n- gap [record: pets / dog walk log]\n"
        text = "".join(idea.format(n=i) for i in range(4))
        assert any("at most 3" in e for e in self.check(data, text))

    def test_prefix_extended_headings_are_counted_as_ideas(self, data):
        """Headings that extend TITLE_PREFIX but are not the exact date-based title are counted."""
        text = """## DemandRadar — weekly signals · 2026-10-26

## DemandRadar — weekly signals extended
- gap [record: pets / dog walk log]

## DemandRadar — weekly signals bonus round
- gap [record: travel / trip planner]

## DemandRadar — weekly signals part 2
- gap [record: pets / dog walk log]

## DemandRadar — weekly signals and more
- gap [record: travel / trip planner]
"""
        errs = self.check(data, text)
        assert any("at most 3" in e for e in errs), f"Expected 'at most 3' error but got: {errs}"

    def test_an_uncited_claim_fails(self, data):
        text = GOOD_COMMENT + "- Huge market, millions of users\n"
        assert any("no citation" in e for e in self.check(data, text))

    def test_a_citation_must_resolve(self, data):
        text = "### 1. Ghost\n- made up [record: pets / ghost idea]\n- also [deep-dive: ghost]\n"
        errs = self.check(data, text)
        assert any("ghost idea" in e for e in errs)
        assert any("deep-dive: ghost" in e for e in errs)

    def test_an_intro_claim_outside_an_idea_must_cite_too(self, data):
        text = "Lots of new demand this week.\n" + GOOD_COMMENT
        assert any("no citation" in e for e in self.check(data, text))

    def test_mentions_and_empty_comments_fail(self, data):
        assert any(
            "@-mention" in e for e in self.check(data, GOOD_COMMENT + "- cc @someone [record: pets / dog walk log]\n")
        )
        assert any("empty" in e for e in self.check(data, "  \n"))
        assert any("long" in e for e in self.check(data, "x" * (analyst_check.MAX_CHARS + 1)))

    def test_mentions_in_headings_fail(self, data):
        text = GOOD_COMMENT + "### 1. @someone\n- gap [record: pets / dog walk log]\n"
        assert any("@-mention" in e for e in self.check(data, text))

    def test_main_reads_the_fixed_paths(self, data, monkeypatch, capsys):
        (data / "signals-comment.md").write_text(GOOD_COMMENT, encoding="utf-8")
        monkeypatch.setattr(analyst_check, "COMMENT_PATH", str(data / "signals-comment.md"))
        monkeypatch.setattr(analyst_check, "DATA_PATH", str(data / "dashboard-data.json"))
        monkeypatch.setattr(analyst_check, "DEEPDIVE_DIR", str(data / "deepdive"))
        assert analyst_check.main() == 0
        (data / "signals-comment.md").write_text("### 1. x\n- uncited\n", encoding="utf-8")
        assert analyst_check.main() == 1
        assert "FAIL" in capsys.readouterr().err

    def test_main_fails_on_a_missing_comment(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr(analyst_check, "COMMENT_PATH", str(tmp_path / "none.md"))
        assert analyst_check.main() == 1


# ───────────────────────── posting the comment ─────────────────────────


class FakeGraphQL:
    """Routes GraphQL POSTs by operation name; records every request body."""

    def __init__(self, existing=None, comments=(), category_names=("General", "Ideas")):
        self.existing = existing
        self.comments = list(comments)
        self.categories = [{"id": f"cat-{n}", "name": n} for n in category_names]
        self.requests = []

    def __call__(self, req, timeout=None):
        body = json.loads(req.data.decode("utf-8"))
        self.requests.append(body)
        q = body["query"]
        assert req.headers["Authorization"] == "Bearer tok"
        if "search(" in q:
            nodes = [self.existing] if self.existing else []
            return FakeResponse({"data": {"search": {"nodes": nodes}}})
        if "discussionCategories" in q:
            return FakeResponse(
                {"data": {"repository": {"id": "repo-1", "discussionCategories": {"nodes": self.categories}}}}
            )
        if "createDiscussion" in q:
            return FakeResponse({"data": {"createDiscussion": {"discussion": {"id": "d-new", "url": "https://x/d/1"}}}})
        if "comments(last" in q:
            return FakeResponse({"data": {"node": {"comments": {"nodes": [{"body": b} for b in self.comments]}}}})
        if "addDiscussionComment" in q:
            return FakeResponse({"data": {"addDiscussionComment": {"comment": {"url": "https://x/c/1"}}}})
        raise AssertionError(q)


class TestPostSignals:
    THREAD = {"id": "d-1", "title": post_signals.THREAD_TITLE, "url": "https://x/d/9", "category": {"name": "General"}}

    def post(self, monkeypatch, fake, body="hello"):
        monkeypatch.setattr(post_signals.urllib.request, "urlopen", fake)
        return post_signals.post(body, MONDAY, repo="combsmith/incubator", token="tok")

    def test_comments_on_the_existing_thread_with_a_week_marker_and_footer(self, monkeypatch):
        fake = FakeGraphQL(existing=self.THREAD)
        assert self.post(monkeypatch, fake) == "https://x/c/1"
        add = fake.requests[-1]
        assert "addDiscussionComment" in add["query"]
        assert add["variables"]["id"] == "d-1"
        sent = add["variables"]["body"]
        assert sent.startswith("<!-- demand-radar-weekly-signals:2026-W44 -->")
        assert "hello" in sent
        assert "promotes nothing" in sent
        assert not any("createDiscussion" in r["query"] for r in fake.requests)

    def test_creates_the_thread_in_general_when_missing(self, monkeypatch):
        fake = FakeGraphQL()
        self.post(monkeypatch, fake)
        create = next(r for r in fake.requests if "createDiscussion" in r["query"])
        assert create["variables"]["categoryId"] == "cat-General"
        assert create["variables"]["title"] == post_signals.THREAD_TITLE
        assert fake.requests[-1]["variables"]["id"] == "d-new"

    def test_never_posts_into_the_ideas_category(self, monkeypatch):
        fake = FakeGraphQL()
        monkeypatch.setattr(post_signals, "CATEGORY", "Ideas")
        with pytest.raises(post_signals.PostError, match="Ideas"):
            self.post(monkeypatch, fake)
        assert not any("createDiscussion" in r["query"] for r in fake.requests)

    def test_ignores_a_same_titled_thread_in_ideas(self, monkeypatch):
        fake = FakeGraphQL(existing={**self.THREAD, "category": {"name": "Ideas"}})
        self.post(monkeypatch, fake)
        assert any("createDiscussion" in r["query"] for r in fake.requests)

    def test_ignores_a_same_titled_thread_in_another_category(self, monkeypatch):
        fake = FakeGraphQL(existing={**self.THREAD, "category": {"name": "Q&A"}})
        self.post(monkeypatch, fake)
        assert any("createDiscussion" in r["query"] for r in fake.requests)

    def test_a_week_is_posted_once(self, monkeypatch):
        fake = FakeGraphQL(existing=self.THREAD, comments=["<!-- demand-radar-weekly-signals:2026-W44 -->\nold"])
        assert self.post(monkeypatch, fake) is None
        assert not any("addDiscussionComment" in r["query"] for r in fake.requests)

    def test_missing_category_and_graphql_errors(self, monkeypatch):
        with pytest.raises(post_signals.PostError, match="category"):
            self.post(monkeypatch, FakeGraphQL(category_names=("Ideas",)))

        def err(req, timeout=None):
            return FakeResponse({"errors": [{"message": "nope"}]})

        with pytest.raises(post_signals.PostError, match="nope"):
            self.post(monkeypatch, err)

    def test_main_needs_token_and_repo(self, tmp_path, monkeypatch, capsys):
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.setattr(post_signals, "COMMENT_PATH", str(tmp_path / "c.md"))
        assert post_signals.main() == 1
        assert "GITHUB_TOKEN" in capsys.readouterr().err

    def test_main_posts_the_comment_file(self, tmp_path, monkeypatch, capsys):
        (tmp_path / "c.md").write_text("body", encoding="utf-8")
        monkeypatch.setattr(post_signals, "COMMENT_PATH", str(tmp_path / "c.md"))
        monkeypatch.setenv("GITHUB_TOKEN", "tok")
        monkeypatch.setenv("GITHUB_REPOSITORY", "combsmith/incubator")
        monkeypatch.setattr(post_signals, "_today", lambda: MONDAY)
        fake = FakeGraphQL(existing=TestPostSignals.THREAD)
        monkeypatch.setattr(post_signals.urllib.request, "urlopen", fake)
        assert post_signals.main() == 0
        assert "https://x/c/1" in capsys.readouterr().out

    def test_main_reports_a_post_error(self, tmp_path, monkeypatch, capsys):
        (tmp_path / "c.md").write_text("body", encoding="utf-8")
        monkeypatch.setattr(post_signals, "COMMENT_PATH", str(tmp_path / "c.md"))
        monkeypatch.setenv("GITHUB_TOKEN", "tok")
        monkeypatch.setenv("GITHUB_REPOSITORY", "combsmith/incubator")
        monkeypatch.setattr(post_signals.urllib.request, "urlopen", FakeGraphQL(category_names=()))
        assert post_signals.main() == 1
        assert "category" in capsys.readouterr().err
