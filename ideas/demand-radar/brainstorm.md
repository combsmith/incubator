---
artifact: brainstorm
status: final
---

# Brainstorm — DemandRadar

<!--
The divergent-then-convergent thinking behind the idea. Mary (Analyst) facilitates
this in the idea Discussion (it is human-facilitated today — not headless); capture
the outcome here. Ground it: record what was actually explored, not a tidy fiction.
-->

- **Slug:** `demand-radar`
- **Source Discussion:** https://github.com/combsmith/incubator/discussions/44
- **Last updated:** 2026-10-19

> **Provenance.** This idea did not go through a facilitated brainstorm session. The
> divergent thinking happened across three rounds in Discussion #44 (concept 2026-07-18,
> two hand-run validation passes the same day that reshaped the schema to "v3", and the
> scripted spike merged 2026-10-10). This file reconstructs what was actually explored and
> dropped from that record and from `pocs/demand-radar/README.md` and `CONTINUE.md`. It is
> written after the fact; it is not a tidy fiction, but it is a reconstruction.

## Problem space

The question circled was: **can "people want X and cannot find a good X" be turned from
anecdote into a refreshable dataset that feeds the incubator?** Framed broadly it has two
halves that are easy to conflate:

- **Demand** — how often and how urgently people ask. Measurable only through the channel
  they use to discover apps (store search, web research, or community), which is why a
  single instrument never works.
- **Supply gap** — how absent *or how bad* the current answers are. Presence is cheap to
  measure; *satisfaction* is the hard, novel part.

The working equation, `Opportunity ≈ Demand × Supply gap`, was set early and survived every
round. What changed was the understanding of which instruments can see which half.

## Ideas explored

| Idea | Promise | Why kept / dropped |
|------|---------|--------------------|
| Single scoring engine that picks winners | One tool, one answer | **Dropped (boundary).** DemandRadar fills every field *except* `downstream` (score, rank, dedup verdict); picking winners is the funnel's job. Kept the tool honest about what it measures |
| Paid ASO data as the demand backbone | Real search volume for every record | **Dropped to conditional.** Two instruments (Keyword Planner, MobileAction) confirmed the free ranking rather than reordering it, and returned N/A for every community-discovered gaming term. Valid only when `discovery_channel = app-store` |
| One `demand` number per record | Simple to rank | **Dropped for the `discovery_channel` axis.** The July passes showed a null keyword volume on a community record is expected, not disqualifying. Demand is read *through* the channel |
| Gaming as pilot vertical | Gap-generating: churn and fragmentation manufacture fresh openings | **Kept.** Student-tools pass (7/10 REJECT) showed a consolidated red ocean; gaming pass (3 CANDIDATE) showed live gaps. Student-tools kept as the difficulty control |
| Star-rating disruption detector | Find proven markets whose leader is weak | **Dropped — dead end.** ~89% of proven App Store markets have a leader rated above 4.6. Replaced by review-text resentment, which found 170 of 314 leaders |
| Hacker News as the universal community source | Free, no auth, high limits | **Dropped as universal, kept as fallback.** Tech-skewed: scored `valheim base builder` at 6 and `couch co op finder` at 0. Proves the mechanism, wrong source for gaming; routing per vertical to StackExchange / YouTube / Reddit instead |
| Score the whole 11,616-keyword space in one run | Complete coverage | **Dropped.** Every free endpoint IP-bans bursts. Replaced by a funnel ordered by rate limit (cheap autocomplete wide, scarce iTunes narrow) and a weekly bounded, resumable batch |
| Second "disrupt" lens alongside "gap" | Attack a proven market whose leader is hated, not just fill an absent niche | **Kept — added by the spike.** The best-evidenced opportunities (white noise, mood tracker, guitar chords) are resented incumbents, not empty niches |
| Auto-open an Ideas Discussion per high-corroboration record | Zero-touch handoff | **Open, leaning no.** Would add to the 54 untriaged ideas rather than reduce them; a reviewed queue a human promotes is the brief's recommendation |
| Publish the dashboard to GitHub Pages | Stable public URL for the weekly refresh | **Split out** as its own idea, Discussion #165 |
| Demographic inference from venue metadata | Audience hints for records | **Parked.** Ethics question (public venue skew only, no personal data) raised in #44 and not pursued |

## Selected direction

A **two-lens, free-source, continuously refreshed feeder tool** for the incubator:

- **Gap lens** — supply quality with graded relevance, corroborated by the community source
  that matches the vertical, demand-weighted by MobileAction only where the channel makes
  that valid.
- **Disrupt lens** — review-text resentment in proven markets, with a per-market deep-dive
  brief naming the wedge.
- **Output** — structured records (schema v3) and a ranked board, consumed by a human who
  promotes the best into Ideas Discussions.

Rationale: the thing the incubator lacks is *evidence at the top of the funnel*, not
another prose validator. The free-source constraint is a feature — it keeps the tool
runnable as a cron with no budget line — and the two lenses cover the two ways a market
can be open (nobody serves it well; somebody serves it resentfully).

## Open questions

- What is the canonical magnitude for a community gap (subreddit size, request frequency,
  video views) and how is it normalised against app-store volume?
- Default `recheck_by` window per `gap_type`.
- Handoff: queue vs. auto-open.
- Is "paywall is the #1 wedge everywhere" a finding or a lexicon artefact?
- Does the tool stay in `pocs/` (documented as disposable) while carrying a weekly cron?
