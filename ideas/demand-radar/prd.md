---
artifact: prd
status: final
---

# PRD — DemandRadar (feeder-tool hardening and handoff)

<!--
The Product Requirements Document. Owner: John (PM), via the BMAD `bmad-prd` skill
(headless-capable + has a validation checklist — the one artifact with a first-class
machine-checkable gate). Seeded from brief.md; do not restate the brief — decide.
This is the last artifact in the package; a complete PRD is what turns approval into
"begin work as defined."
-->

- **Slug:** `demand-radar`
- **Source Discussion:** https://github.com/combsmith/incubator/discussions/44
- **Seeded from:** `brief.md`
- **Last updated:** 2026-10-19

> **Scope note.** The brief recommends *go as a feeder tool, no-go as a product*. This PRD
> therefore defines the work that `idea:approved` authorises under that recommendation:
> hardening the existing spike into the incubator's feeder and wiring its handoff. It is
> **not** a PRD for a standalone product; that would be written in a product repo if the
> graduation trigger in `brief.md` §7 is ever met. Written by hand from the brief, not by
> the `bmad-prd` skill; the BMAD content-quality tier has not been run on it.

## Vision

Every idea that enters the incubator's brief stage arrives with refreshed, cross-source,
machine-readable evidence of demand and of a weak or resented incumbent. The analyst spends
discovery time only on gaps the data says are real; the funnel stops carrying hunches.

## Target User & JTBD

Per `brief.md` §2: the incubator's idea owner / analyst, and the `idea-triage` agent that
reads what they promote. When deciding which app idea deserves a brief, they want refreshed
evidence of demand and incumbent weakness so discovery effort goes only where the gap is
real and the market winnable. No external users in this scope.

## Functional Requirements

Grouped by journey. "Must" items are the definition of done for this approval.

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-1 | The weekly refresh runs bounded (`--max`, `--rate`), paced, resumable, and never retries a 403/429; a degraded run is labelled as such in the artifact name. **Gaps:** (a) *State is not persisted across runs.* The workflow checks out read-only and uploads only `dashboard-data.json`, `starter-list.md` and `dashboard.html`, so each run restarts from the same committed snapshot; durable state restoration/persistence must be built before any claim of accumulated coverage. (b) *No stop on first throttle.* `extract.fetch` returns the same `False` for a 403/429 as for any failure and `extract.run` aborts only after 15 consecutive failures, so up to ~15 further calls can hit an active ban; propagate the HTTP status and abort on the first 403/429. (d) *The same breaker is missing from the other `full`-preset network stages:* `broad_pass.run` records each 403/429 as an ordinary per-keyword failure and continues through the whole pending set, and `resented_giants.run` catches lookup/review failures and continues through the remaining leaders; both need a first-throttle (or consecutive-failure) abort. (c) `enrich_community.run` re-reads un-enriched `records.jsonl`, enriches only the first `--max` (240 in the workflow) survivors and overwrites `records.enriched.jsonl`, so a weekly run discards community evidence on records beyond the cap (the committed snapshot has more enriched records than one run covers). The refresh must merge prior enrichment or rotate and persist batches | must (bounded run exists; state persistence, first-throttle abort and evidence-preserving merge to build) |
| FR-2 | **Promotion queue.** `rank_starter_list.py` / `export_dashboard.py` emit a `promotion-queue.md` listing records that meet a promotion rule (≥2 mechanisms **with positive corroboration** — `community_note == community-corroborated`, not merely `corroboration_count ≥ 2`, which would also queue the 39 `community-too-thin` REJECTs and 14 `community-weak` WATCHes — or DISRUPT with resentment ≥ 0.4 and, where the channel is app-store, MobileAction volume > 5 *when a label exists*; the paid, manual MobileAction check is an explicitly permitted gate on this path only, and without a label the record may still enter the queue flagged `volume-unverified` so a valid disruption is not blocked) | must |
| FR-3 | **Handoff.** A command (`promote.py --keyword X`) writes `ideas/<new-slug>/market-research.md` from the deep dive and the record's provenance, with `status: draft`. Per the repo lifecycle (`README.md`, `ideas/README.md`) a human must first open the Ideas Discussion and have it reach Ripe in `idea-triage`; only then is `promote.py` run to write the package, so no package exists for an idea that has not passed the gate | must |
| FR-4 | **No auto-opened Discussions.** The tool never creates GitHub Discussions, issues or PRs itself | must |
| FR-5 | **Decay.** Each record carries a `recheck_by` derived from `gap_type` (`stale` and `low-quality` shorter than `absent-in-store`; a resentment-driven opportunity is keyed from the existing `disruption` flag / resentment score, not a `gap_type`, because `extract.analyze` never emits `complaint-driven`); records past `recheck_by` are flagged on the board and excluded from the promotion queue until re-scored. The scheduled path gets a bounded supply/resentment recheck (oldest `recheck_by` first), since `refresh` currently skips already-scored keywords and does not run `resented_giants` | must |
| FR-6 | **Community-metric normalisation.** Per-source cutoffs (Hacker News, StackExchange, Reddit, YouTube views) are expressed on one 0–1 corroboration scale, calibrated against a community ground-truth set; the raw per-source value is retained. The MobileAction labels cannot serve here (all 9 community-channel labels are N/A), so the PRD requires a human-labelled cross-source community set (≥ 20 keywords, built as part of this work) before cutoffs are fixed | must |
| FR-7 | **Labels merged.** `labels/mobileaction-labels.json` values populate `demand.app_store_volume` on matching records; the label file remains the manual ground truth | should |
| FR-8 | **Deep-dive breadth.** Deep dives exist for the top ~15 resented giants, and the gripe-category distribution across them is reported so a lexicon artefact can be detected | should |
| FR-9 | **Reddit wired** for the gaming pilot (token plus proxy if needed), else the pilot's community corroboration is documented as degraded | should |
| FR-10 | Relevance: branded-incumbent recall improved and measured against the labelled set | could |

## Non-Functional Requirements

- **Cost:** free sources only on the critical path, with one explicit exception: the manual, paid MobileAction volume check for app-store-channel DISRUPT records (FR-2), which stays manual or is gated
  on `discovery_channel = app-store` behind an explicit budget decision.
- **Rate-limit safety:** low concurrency and pacing from the first call; a 403-storm aborts
  the batch silently. No stage may extend a ban by retrying.
- **Security:** stage inputs/outputs are fixed paths, not argv (path-injection sink), with one
  exception: `promote.py --keyword X` (FR-3) derives `ideas/<new-slug>/market-research.md`.
  The slug must be validated against a strict allowlist (`^[a-z0-9]+(-[a-z0-9]+)*$`, bounded
  length), the resolved path must be contained under `ideas/`, and an existing package
  directory must never be overwritten;
  workflow inputs pass through env, never interpolated into shell. Secrets optional; no
  secret is required for a degraded-but-valid run.
- **Quality gates:** existing CI stays green — lint/format/typecheck, unit tests at the 80%
  coverage floor, SonarCloud new-code gate, no suppressions or coverage exemptions.
- **Privacy:** public venue metadata only; no personal data inferred or stored.

## Success Metrics

| Metric | Baseline (2026-10-19) | Target for this scope |
|---|---|---|
| DemandRadar-sourced Ideas Discussions that survive `idea-triage` | 0 | ≥ 3 |
| Of those, reaching a decision brief | 0 | ≥ 1 |
| Community-backed records in the promotion queue with normalised corroboration (DISRUPT entries promoted on resentment and MobileAction volume alone carry no community evidence and are out of this metric) | n/a (16 records are positively community-corroborated, un-normalised) | 100% of community-backed queue entries |
| Records past `recheck_by` still shown as live | unknown (no decay) | 0 |
| Weekly refresh runs degraded | not tracked | tracked; < 1 in 4 |

Meeting the first two rows is the **graduation trigger** that re-opens `brief.md` §7.

## Scope & Non-Goals

**In:** FR-1 to FR-6; FR-7 to FR-9 as capacity allows.

**Out, explicitly:** a product repo; external users or pricing; auto-opening Discussions;
TikTok or any scraping outside published API limits; paid ASO on the critical path;
publishing the dashboard to GitHub Pages (Discussion #165, separate idea); moving the code
out of `pocs/` (decided at the graduation trigger, not now).

## Open Questions

- Exact promotion rule thresholds in FR-2 — the proposed numbers are from the committed
  snapshot and should be re-checked once FR-6 normalisation lands.
- Default `recheck_by` windows per `gap_type` (FR-5) — no empirical basis beyond one
  observed closure in weeks.
- Whether Reddit (FR-9) is achievable from GitHub-hosted runners at all.

## Assumptions

1. A human will actually review the promotion queue weekly; without that, FR-2/FR-3 produce
   files nobody reads and the success metrics stay at 0.
2. The free endpoints keep their current limits and terms through this scope.
3. The 34-entry MobileAction set (24 app-store, 9 community, 1 baseline) is enough to
   calibrate app-store thresholds only; community-metric normalisation (FR-6) needs its own
   labelled set.
4. `idea-triage` can consume a pre-filled `market-research.md` without changes to the
   triage agent.
