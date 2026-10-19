---
artifact: ost
status: final
---

# Opportunity–Solution Tree — DemandRadar

<!--
Teresa Torres's opportunity-solution-tree, rendered as Mermaid (GitHub renders it
natively — no whiteboard tool needed). Structure: one desired OUTCOME → the
OPPORTUNITY space (customer needs/pains) → the SOLUTION space → ASSUMPTION tests.
A living document — revisit as you learn. Owner: Mary (Analyst).
-->

- **Slug:** `demand-radar`
- **Last updated:** 2026-10-19

Legend: ✅ built and tested by the spike · ⚠️ built, calibration open · ⬜ not built.

```mermaid
flowchart TD
    O["🎯 Outcome: DemandRadar-sourced Ideas Discussions that reach a decision brief, per quarter (now 0)"]

    O --> OPP1["Opportunity: I cannot tell a real gap from a vibe — demand evidence is anecdotal and untimestamped"]
    O --> OPP2["Opportunity: a well-rated incumbent hides a beatable one — stars say 'served', users say 'resented'"]
    O --> OPP3["Opportunity: the instrument I have is blind to the demand I care about — keyword tools return N/A for community-discovered apps"]
    O --> OPP4["Opportunity: even a good record goes nowhere — there is no path from the board into an Ideas Discussion"]

    OPP1 --> S1["✅ Gap lens: keyword space → App Store supply check with graded relevance → community corroboration → ranked list"]
    OPP1 --> S2["⚠️ Demand-aware ranking: down-weight app-store gaps until MobileAction volume confirms"]
    OPP2 --> S3["✅ Disrupt lens: mine 1–3★ reviews of proven-market leaders for paywall / ads / got-worse resentment"]
    OPP2 --> S4["⚠️ Deep-dive brief per market: incumbents, gripes, loves, feature wishes, wedge"]
    OPP3 --> S5["⚠️ discovery_channel axis: route magnitude to the valid instrument; size community gaps from community metrics"]
    OPP4 --> S6["⬜ Handoff: reviewed queue → human promotes → deep dive lands as the new idea's market-research.md"]
    OPP4 --> S7["⬜ Decay: recheck_by per gap_type; expire stale records off the board"]

    S1 --> A1["Test: does relevance change verdicts? — PROVEN: without it everything reads 'served'"]
    S2 --> A2["Test: do app-store gaps have volume? — 1 of 12 did; MobileAction still manual"]
    S3 --> A3["Test: do stars find targets? — DISPROVEN (~89% of leaders >4.6★); review text found 170/314"]
    S4 --> A4["Test: do deep dives discriminate? — WEAK: all 3 name paywall as wedge #1; widen to ~15 giants"]
    S5 --> A5["Test: normalise HN/SE/Reddit/YouTube cutoffs against a new human-labelled community ground-truth set — OPEN"]
    S6 --> A6["Test: hand-promote top 3 records; does idea-triage keep them? — OPEN, the graduation gate"]
    S7 --> A7["Test: how fast did the July gaps close? — one closed in weeks (AI flashcards); policy OPEN"]
```

## Notes

- **Outcome is a metric, not a feature.** The spike optimised the solution space (lenses,
  ranking, dashboard) and never moved the outcome: no record has been promoted in the ~9
  days since the spike merged (2026-10-10). `OPP4` is where the next effort belongs; see `brief.md` §7.
- **The opportunity space was widened by running it.** `OPP2` (resentment behind good
  ratings) and `OPP3` (instrument blindness) were not in the original concept; they came
  out of the July passes and the October spike respectively.
- Each solution bottoms out in the cheapest test that could invalidate it; the table in
  `brief.md` §6 carries the same tests with their results.
