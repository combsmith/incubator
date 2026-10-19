---
artifact: market-research
status: final
---

# Market Research — DemandRadar

<!--
Competitive / market context feeding the decision brief. Owner: Mary (Analyst).
Summarize the takeaway into brief.md §3 — keep the detail here.
-->

- **Slug:** `demand-radar`
- **Last updated:** 2026-10-19

> **Provenance.** The competitor rows come from the github-actions "Weekly Update" comment
> on Discussion #44 dated 2026-07-21. That comment was produced by an agent doing web
> research; **no human has independently verified the vendor claims** (accuracy figures,
> source counts, prices). Treat those cells as a starting frame, not as measured facts. The
> "manual workaround" row and everything under *Market signal* is measured — it comes from
> the spike's own output and the two hand-run passes.

## How it's solved today

Two different jobs are being compared here, and it matters which one a competitor does:
**validate an idea I already have** (single-shot) versus **find ideas I do not have yet**
(continuous). All four external tools do the first.

| Alternative | What it does well | Where it falls short | Pricing / model |
|-------------|-------------------|----------------------|-----------------|
| **Manual / anecdotal sourcing** (the incubator today) | Zero cost; human judgement on every idea | Lossy, untimestamped, not comparable, not deduplicated; produced 54 untriaged auto-ideas with no brief stage behind them (2026-10 review) | Free (analyst time) |
| **Hand-run Wizard-of-Oz pass** (what #44 did in July 2026) | Rich qualitative signal; produced 20 usable records in ~2 hours | Does not refresh; ~1 hour per 10 records; cannot cover 25 verticals | Free (analyst time) |
| **IdeaProof** [unverified] | Broadest feature set: validation, business plan, brand, marketing; claims 89% accuracy in ~120 s | Single-shot; prose report; validates *your* idea, does not find one | Unknown — not researched |
| **Preuve AI** [unverified] | Evidence you can check: live research across 50+ sources per scan, each claim linked to its source. Closest to DemandRadar's "structured, cited" stance | Single-shot; one scan per idea; no monitoring over time | Unknown — not researched |
| **WorthBuild** [unverified] | Price leader; customer-discovery included | Single-shot report | ~$4–5 per report [unverified] |
| **Startup Ignition ToolSuite** [unverified] | Methodology-driven (1,000+ mentored ventures); structured reports with validation tasks | Single-shot; consulting-shaped | Unknown — not researched |
| **Paid ASO tools** (MobileAction, AppTweak, Sensor Tower) | Real App Store search volume and difficulty — the only magnitude instrument for `app-store`-channel ideas | Structurally blind to `community`-discovered demand (all 9 `community`-channel labels N/A); paid; measures demand, not supply quality | Subscription; MobileAction used manually via Keyword Inspector for 34 labels |
| **Google Keyword Planner / Trends** | Free-ish web-search volume; valid for `web-research`-channel ideas (citation managers, army builders) | Same blindness for community-discovered apps; Google Suggest IP-bans bursts after ~6k calls | Free |

## The gap / wedge

Three structural differences, none of which an existing tool offers (per the 2026-07-21
scan, unverified):

1. **Continuous, not single-shot.** DemandRadar runs weekly and accumulates coverage of a
   1,250-keyword priority set; incumbents produce one report per idea on request.
2. **Finds, rather than validates.** Input is a vertical lexicon, not a user's idea. The
   output is a ranked list the user did not think of (`watermark remover`, `white noise`
   resentment, 170 resented leaders).
3. **Structured records, not prose.** Every record carries `discovery_channel`, `gap_type`,
   supply, community and provenance fields so downstream automation (triage, dedup against
   incubator Discussions) can consume it.

**The honest caveat:** these are differentiators for a *tool used inside a funnel*. Whether
they would sell to indie developers as a product is unknown and not tested; the brief does
not recommend finding out yet.

## Market signal

Measured, from the spike's committed snapshot (counts read from `pocs/demand-radar/output/`,
not re-run) and the hand-labelled MobileAction set:

| Signal | Value | What it says |
|---|---|---|
| Priority keywords supply-scored | 1,250 across 25 verticals | Coverage is achievable on free data with a weekly bounded batch |
| Supply verdict mix | 745 REJECT · 180 WATCH · 163 CANDIDATE · 158 CANDIDATE* (store shows a gap, verify elsewhere) · 4 DISRUPT (1,250 total) | ~60% of plausible ideas are already served — relevance scoring is what makes that number trustworthy |
| Records evaluated by ≥2 mechanisms (supply + community) | 69 of 1,250: 16 corroborated (CANDIDATE), 14 weak (WATCH), 39 community-too-thin (REJECT) | Only the 16 are positive corroboration; the anti-noise rule is strict and most gaps remain single-source |
| Vertical dynamics | 250 gap-generating · 350 saturated · 650 mixed | Gaming/tabletop manufacture gaps; student-tools and productivity are red oceans |
| Proven-market leaders with a >4.6★ rating | ~89% | Star ratings cannot find beatable incumbents |
| Leaders flagged by review-text resentment | 170 of 314 scanned | The usable disruption signal; e.g. Quizlet 4.78★ with 46% of low-star reviews about pricing/ads/decline; Unit Converter 4.81★ / 69%; Rocket Money 4.48★ / 62% |
| Dashboard rows | 834 (448 DISRUPT · 137 WATCH · 130 CANDIDATE · 119 CANDIDATE*) | Two lenses, one board |
| App-store candidates with real search volume | 1 of 12 (`watermark remover`, vol 48, difficulty 25, best incumbent 3.98★) | Demand magnitude collapses the app-store worklist; "real gap, no demand" is the common case |
| Community-channel labels visible to MobileAction | 0 of 9 | Keyword tools are blind to community-discovered demand, as #44 predicted |
| Deep dives written | 3 (mood tracker vol 48; white noise vol 64; guitar chords vol 43) | Each names paywall as the #1 wedge — see *Risks* |

Demand evidence for the *tool itself* (would anyone else want DemandRadar?) was **not
collected** and is not claimed. The category's existence (four vendors) is the only
external signal, and it is second-hand.

## Risks & unknowns

- **Platform dependency / rate limits.** Every free endpoint IP-bans bursts: iTunes Search
  (~20–30 calls/min, bans after ~100), Google Suggest (~6k), Reddit (403 from datacenter IPs
  even with OAuth), StackExchange (~300/day), YouTube (~90/day on a free key). A ToS change
  on any one of them degrades a layer. The pipeline paces, resumes and circuit-breaks, but
  it cannot make a banned source un-banned.
- **Terms of service.** Store listings and public APIs are used within published limits;
  Reddit's and TikTok's terms were flagged in #44 and not resolved. TikTok is not used.
- **Lexicon artefact risk.** All three deep dives converge on "fix the money model". If the
  gripe lexicon over-weights pricing, every market will look like a paywall play and the
  brief loses discriminating power.
- **Small labelled set.** 34 MobileAction label entries (24 app-store, 9 community, 1 baseline) are the entire
  ground truth for thresholds and for the `discovery_channel` finding.
- **Gap decay.** The AI-flashcard wave closed a validated gap within weeks of the July pass.
  Without a decay policy the board accumulates stale opportunities.
- **Incumbency, if ever productised.** Preuve AI's "every claim cited" positioning is close
  to DemandRadar's; a continuous mode would be a feature for them, not a new company.
