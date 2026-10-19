---
artifact: brief
status: final
---

# Decision Brief — DemandRadar

<!--
The decision brief / PRD-lite. This is the artifact a human decides `idea:approved`
on. It exists to INFORM the go/no-go with discovery evidence — it does not replace
discovery, and it is not the full PRD (that gets written in the product repo after
graduation). Owner: Mary (Analyst). Keep it tight — a page or two.
-->

- **Slug:** `demand-radar`
- **Source Discussion:** https://github.com/combsmith/incubator/discussions/44
- **Spike (merged 2026-10-10, PR #121):** [`pocs/demand-radar/`](../../pocs/demand-radar/) — weekly refresh via [`demand-radar-signal.yml`](../../.github/workflows/demand-radar-signal.yml)
- **Author / owner:** don-petry
- **Status:** `ready-for-decision`
- **Last updated:** 2026-10-19

> **Provenance.** Unlike most briefs, this one is written *after* the spike. Every claim
> below is traceable to one of: the Discussion #44 body (concept, schema, two hand-run
> Wizard-of-Oz passes on 2026-07-18, the 2026-10-10 "Spike result" section), the
> committed spike output under `pocs/demand-radar/output/` (1,250 scored records, 834
> dashboard rows, 314 leaders scanned for resentment, 3 deep dives), the hand-labelled
> MobileAction set (`labels/mobileaction-labels.json`, 2026-07-18/19), or the
> github-actions "Weekly Update" comment of 2026-07-21 (competitor landscape — **agent
> researched, not independently verified by a human**; marked as such wherever used).
> Counts are read from the committed snapshot, not re-run.

## 1. Problem

The incubator's top-of-funnel is anecdotal. Ideas arrive as hunches carried by hand into
Ideas Discussions, and the demand evidence behind them is a vibe, not a dataset: nothing is
timestamped, comparable across sources, or deduplicated against solutions (or incubator
ideas) that already exist. The 2026-10 incubator review found 54 auto-generated ideas
sitting untriaged with no brief stage behind them — volume without evidence. There is no
structured, refreshable feed of "people want X and cannot find a good X" that the funnel
(`feature-ideation → idea-triage → idea:approved`) can consume. Two hand-run passes in
July 2026 showed the signal *can* be extracted (20 records; 19 have a recorded verdict:
5 CANDIDATE, 3 WATCH, 10 REJECT, 1 DEDUP against incubator #5 — Discussion #44 lists 9 verdicts
for the 10 gaming records and does not record the tenth), and the October spike showed it can be extracted on a
schedule, headless, from free sources. The problem is real and the mechanism is proven;
what is not yet proven is that the output changes what the incubator does.

## 2. Target user & JTBD

- **Who:** the incubator's idea owner / analyst role (today: one person plus the
  `feature-ideation` and `idea-triage` agents). DemandRadar is an **internal feeder tool**,
  not an end-user product. External users (indie developers, studios) are a *possible*
  later audience and are explicitly out of scope for this decision.
- **Job to be done:** When _I am deciding which app idea deserves a brief_, I want to
  _see refreshed, cross-source evidence of demand and a weak or resented incumbent_, so I
  can _spend discovery effort only where the gap is real and the market is winnable_.

## 3. Market & competitive context

Detail in [`market-research.md`](./market-research.md). Takeaway:

- **The category is validated by others.** Four AI idea-validation tools (IdeaProof, Preuve
  AI, WorthBuild, Startup Ignition ToolSuite) now sell "is this idea worth building" reports
  [agent-researched 2026-07-21, unverified]. All are **single-shot**: you bring the idea,
  they produce a prose report. None monitors demand continuously or emits machine-readable
  records.
- **DemandRadar's differentiation is structural, not feature-level:** a repeatable
  multi-source pipeline, structured output, and *finding* the idea rather than validating one
  you already had. "Continuous" is only partly true today: the weekly `refresh` preset
  re-runs community enrichment, but App Store supply and review-resentment data are the July
  snapshot until the `full` preset is run by hand (extract skips keywords already scored;
  `resented_giants` is not in `refresh`). PRD FR-5 adds a bounded recheck to close this.
- **But the differentiation only matters if someone consumes the feed.** As an internal
  tool its "market" is one funnel. The competitive picture says the idea is sound; it says
  nothing about whether it should be a product. This brief treats it as a tool.

## 4. Opportunity → solution

Mapped onto [`ost.md`](./ost.md):

- **Desired outcome (metric):** DemandRadar-sourced Ideas Discussions that reach a decision
  brief, per quarter. **Current value: 0** — in the ~9 days since the spike merged
  (2026-10-10), no record it produced has been promoted into an Ideas Discussion.
- **Opportunity addressed:** "I cannot tell a real gap from a vibe, and I cannot tell a
  beatable incumbent from a well-rated one."
- **Proposed solution (built):** a two-lens funnel. **Gap lens** — keyword space (25
  verticals, 1,250 priority keywords) → App Store supply check with graded relevance →
  community corroboration (StackExchange / YouTube / Hacker News, Reddit when forced) →
  ranked starter list. **Disrupt lens** — 314 proven-market leaders scanned for review-text
  resentment (paywall, ads, "got worse"); 170 flagged; per-market deep-dive briefs.
- **Proposed solution (not built):** the handoff — promoting a high-corroboration record
  into an Ideas Discussion with `market-research.md` pre-filled from the deep dive.

## 5. Value & feasibility (rough)

- **Impact: medium-high for the incubator; nil outside it until the handoff exists.** A
  refreshed evidence feed changes idea sourcing from anecdote to data. The spike already
  produced one demand-validated gap (`watermark remover`: MobileAction volume 48,
  difficulty 25, best incumbent 3.98★) and three resentment-backed disruption targets with
  written wedges.
- **Effort: small — it is built.** Remaining work is the handoff, metric normalisation,
  decay policy, and relevance tuning: roughly 2–3 person-weeks, mostly judgement.
- **Prioritization score — ICE (shown, with reasoning):**
  - **Impact = 4/5.** Same as the post-validation gut-check in #44. Held, not raised: the
    spike proved the mechanics, not the outcome metric (0 graduates so far).
  - **Confidence = 3/5.** Up from the pre-spike 3 in spirit but held at 3 in number:
    free-source feasibility, relevance, and review-text resentment are proven; the
    labelled set is 34 entries (24 app-store, 9 community, 1 baseline), community metrics are not normalised, and MobileAction
    validation is still a human in a browser.
  - **Ease = 4/5.** Up from 3: the pipeline exists, runs weekly on stdlib Python, and is
    tested at an 80% coverage floor. The remaining pieces are small.
  - **ICE = 4 × 3 × 4 = 48 / 125 (≈ 0.38 normalised).** For comparison, ContentTwin
    scored 6/125 — the gap is almost entirely confidence bought by the spike.
  - *RICE is a poor fit here and is not used:* Reach is one internal funnel, so the
    formula degenerates to Impact × Confidence / Effort and adds nothing over ICE.

## 6. Riskiest assumptions & cheapest test

Most-dangerous first. **Proven** rows are settled by the spike; **open** rows are what the
decision-maker should know is still unresolved.

| # | Assumption | If wrong… | Cheapest test | Result |
|---|-----------|-----------|---------------|--------|
| 1 | Records the funnel emits will become Ideas Discussions that survive `idea-triage` | Tool runs weekly, changes nothing; the outcome metric stays 0 | Hand-promote the top 3 into Ideas Discussions and see whether triage keeps them. Candidates named in the spike notes are `watermark remover`, `white noise`, `mood tracker`, but the committed output has no record for `watermark remover` or `white noise` (nearest: `watermark manager`, `white noise generator`) and no deep dive for `watermark remover`; only `mood tracker` has both. Fallback: promote from the three existing deep dives (mood tracker, white noise, guitar chords) and take `watermark remover` from its MobileAction label and the hand-run pass, with the missing record re-generated first | **OPEN** — not attempted in the ~9 days since the spike merged; this is the gate for graduation |
| 2 | The load-bearing signal can be extracted headless from free sources | Needs paid ASO ($) on the critical path; cannot run as a cron | The spike itself | **PROVEN** — 1,250 keywords scored, weekly refresh, stdlib only, no auth except an optional YouTube key |
| 3 | Supply presence can be judged without a relevance model | Everything reads "served" (`raid dps meter` → decibel meters) | Add graded name/description token match; re-run | **PROVEN essential** — without it the supply layer is meaningless; graded match fixes collisions but branded-incumbent recall is still crude |
| 4 | Star ratings identify beatable incumbents | Disrupt lens finds nothing | Count proven markets with a >4.6★ leader | **DISPROVEN** — ~89% of proven markets have a >4.6★ leader. Pivoted to review-text resentment: 170 of 314 leaders flagged (Quizlet 4.78★, 46% resentment; BetterSleep 98%) |
| 5 | Free endpoints tolerate bulk scoring | One-shot scoring of 11k keywords | Burst iTunes Search | **DISPROVEN** — iTunes bans after ~100 calls (~20–30/min cap), Google Suggest after ~6k; Reddit 403s datacenter IPs. Funnel order, pacing, resume and a 403 circuit-breaker follow from this |
| 6 | App Store "absent" means a gap | False gaps promoted | Check app-store-channel gaps in MobileAction | **PARTLY DISPROVEN** — of 12 app-store starter candidates, only `watermark remover` has real volume; 5 sit at the ~5 floor, 4 are N/A; the remaining 2 were not recorded in the spike notes, so "1 of 12" is the count of confirmed-volume candidates, not a full breakdown. "Absent" is often a relevance miss, so app-store gaps are down-weighted until volume confirms |
| 7 | Community metrics from different sources can be compared | Gaming (community-discovered) gaps are mis-ranked against app-store gaps | Normalise per-source cutoffs against the labelled set | **OPEN** — per-source thresholds exist (HN 300/50, SE 25/3, Reddit 10/2, YouTube 50k/2k views) but units are not normalised against each other or against app-store volume |
| 8 | Demand magnitude can be automated | Every candidate needs a human in a browser | Script MobileAction, or accept manual | **OPEN** — MobileAction is paid and driven by hand through a logged-in session; 34 entries labelled so far (24 app-store, 9 community, 1 baseline) |
| 9 | Gaps are stable enough to act on | A gap closes before the brief is written (the 2026 AI-flashcard wave closed one in weeks) | Define `recheck_by` per `gap_type` and expire records | **OPEN** — `recheck_by` is in the schema; no decay policy is implemented |
| 10 | The deep-dive brief discriminates between markets | Every brief says the same thing | Compare wedges across the three deep dives | **WEAK** — all three name "fix the money model" as wedge #1. Either paywall resentment is genuinely universal or the gripe lexicon is dominated by one category. Needs a wider sample before trusting a single brief |

## 7. Recommendation (go / no-go)

**Go — as the incubator's feeder tool. No-go — on graduating DemandRadar to its own
product repo now.**

Why go: the spike answered the question #44 posed. The signal is extractable, headless, on
a schedule, from free sources; the two hand-run passes and the automated run agree with each
other and with two paid magnitude instruments; and the disrupt lens found a signal (review-
text resentment) that the obvious approach (star ratings) could not. The marginal cost of
keeping it is one weekly Action.

Why not a product repo: the outcome metric is zero. A tool that has not yet fed a single
Ideas Discussion has not earned a repo, a PRD-for-a-product, or external users. Graduating
it now would be graduating the mechanism, not the result. The competitive picture says a
standalone product is *plausible*, not that it is *ours to build*; the org's bet is the app
factory the tool feeds, not the tool.

**What "approved" authorises** (the PRD in this package scopes exactly this, nothing more):
1. Wire the **handoff**: a reviewed queue, not auto-opened Discussions — a human promotes a
   record and the deep dive lands as `ideas/<new-slug>/market-research.md`.
2. **Normalise** community metrics against the labelled set; implement `recheck_by` decay.
3. **Promote the first three** records by hand to measure whether triage keeps them.

**Graduation trigger** (re-open this brief when met): ≥3 DemandRadar-sourced Ideas
Discussions have survived `idea-triage`, and ≥1 has reached a decision brief. At that
point the question becomes whether to move the tool out of `pocs/` (a "disposable" spike
should not carry a long-lived cron) into a tooling repo, and whether external users exist.

**Hard gate:** the go/no-go is a human's, applied via `idea:approved`. This brief informs
that decision; it does not make it.

## 8. Open questions

- **Handoff shape:** queue a human promotes (recommended here) vs. auto-opening Ideas
  Discussions. Auto-opening would add to the 54 untriaged ideas, not reduce them.
- **Decay policy:** default `recheck_by` window per `gap_type` — stale and complaint-driven
  gaps close faster than absent ones; no numbers yet.
- **MobileAction:** keep manual (free, slow) or pay for API access gated on
  `discovery_channel = app-store`? Volume floor appears to be ~5; 34 labels is too few to
  calibrate thresholds.
- **Reddit:** the correct source for gaming gaps, but 403s from datacenter IPs even with
  OAuth; needs a token *and* likely a proxy. Without it the pilot vertical (gaming) is
  under-corroborated.
- **Deep-dive discrimination:** is "paywall resentment everywhere" a finding or a lexicon
  artefact? Run deep dives across the top ~15 resented giants before trusting one.
- **Where the tool lives:** `pocs/` is documented as disposable, yet the weekly workflow
  lives in this repo's `.github/`. Acceptable while the handoff target is this repo's own
  Discussions; revisit at the graduation trigger.
- **Dashboard URL:** the weekly artifact has no stable public URL (Discussion #165 proposes
  GitHub Pages). Separate idea; not blocking.
