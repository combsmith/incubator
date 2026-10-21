---
artifact: prd
status: final
---

# PRD — WorldChest (working name BlockVault): evidence programme for backup, sync, restore & versioning of Minecraft Bedrock worlds

- **Slug:** `worldchest`
- **Source Discussion:** https://github.com/combsmith/incubator/discussions/5
- **Seeded from:** `brief.md` (primary input); `brainstorm.md`, `market-research.md`, `ost.md`
  and the Discussion thread as supporting inputs
- **Owner:** John 📋 (PM), vendored `bmad-prd` run headless with `intent: create`
  (`prompts/incubation/producer-prd.md` overlay)
- **Stakes:** pre-product evidence sprint, about one week, run by the idea owner. Rigor is
  calibrated to a solo/internal effort; the substance bar still applies.
- **Last updated:** 2026-10-21

> **Scope note.** `brief.md` §7 recommends **park: buy evidence first**. Under that
> recommendation, `idea:approved` on Discussion #5 authorises the evidence programme in
> `brief.md` §6 (tests 1–4, plus the time-boxed watch in test 5) and the return of its results
> to the Discussion. It does **not** authorise product code, a backend, a store listing or a
> paid plan. This PRD therefore specifies the evidence programme as the deliverable. The backup
> product the tests are about appears only as the hypothesis under test (§4.0) and in the
> non-goals (§6). A product PRD is a later `update` of this document, written after the Decider
> has read the results.

## 0. Document Purpose

For the Decider (the idea owner, who applies `idea:approved`), for whoever runs the tests, and
for the later product PRD that will extract from it. Vocabulary is anchored in the Glossary
(§3); requirements are grouped by test with globally numbered FR-IDs; inferences carry inline
`[ASSUMPTION]` tags indexed in §10. It builds on `brief.md`, `market-research.md`, `ost.md` and
`brainstorm.md` and does not restate them.

## 1. Vision

A parent can keep every Minecraft Bedrock world their child has built, and rewind to an
earlier save, across a device change or a corrupted world, with no technical work. That is
the product vision, taken from the thread's job to be done.

This document's vision is narrower: within about a week and without writing product code, know
whether that product is worth building. Four questions decide it. Will parents pay for it, can
a Non-technical parent complete Power mode setup unaided, does the zero-setup Share-sheet baseline
tier actually work on current devices, and does Mojang permit a paid third-party backup
service. When the programme ends, the Decider has a dated answer to each, written into
`brief.md` §6, and can approve, close or re-park the idea with reasons that are on record.

**Why now (load-bearing).** Android 11, 13 and 14 each made the World folder harder to
reach, so the manual route is getting worse, and players are asking Mojang for native mobile
export (`market-research.md`). If Mojang ships it, the product becomes a feature. The window
for a third party is open now and may close; the programme is the cheapest way to find out
whether to step through it.

## 2. Target User

### 2.1 Jobs To Be Done

The programme serves two jobs. The product job is the thread's, repeated here only so the
tests can be read against it.

- **Decider (functional):** when I must decide whether to build WorldChest, I want evidence on
  demand, onboarding, platform and legal permission, so I can apply `idea:approved` or close
  the idea with a reason that will still make sense in a year.
- **Decider (emotional):** avoid building a free utility nobody pays for, and avoid losing a
  real product to a week of hesitation.
- **Product job (from the thread, under test):** "When I get a new device or a world corrupts,
  help me keep every world I've built, and let me rewind to an earlier save, without any
  technical work." The user is a young Bedrock player (~7–15) on a phone or tablet; the buyer
  is their parent. Personas are in `brief.md` §2 and are not re-derived here.

### 2.2 Non-Users (v1)

- Children are not interviewed, tested or asked for data in this programme. Every participant
  is an adult parent.
- Map creators, streamers and Minecraft Education classrooms are not researched (`brief.md`
  §8 lists them as unvalidated).
- iOS users get one spike (FR-4) and nothing else.

### 2.3 Key User Journeys

Journeys are captured, not authored. Only one real session exists in the inputs; the others
are the programme's own procedures, written at the light end of the scope dial.

- **UJ-1. The author migrates 232 worlds by hand.** Don, the idea owner, moves a child's
  Bedrock Library from a Galaxy S22 to an S24. Samsung Smart Switch produces a restore that
  crashes the game. The working path takes ADB, a Chromebook and most of a day, yields the
  Include/skip file set, uploads the Library to Google Drive with md5 checks, and restores
  every World loading on the new phone (thread, POC comment). This is the baseline the
  product must beat and the know-how the Hallway test (UJ-3) packages.
- **UJ-2. A recruited parent is interviewed.** A parent of a Bedrock player aged ~7–15 who
  has changed a device or lost Worlds recently talks about what happened, what they did,
  and what they already pay for `[ASSUMPTION: no input sets an interview length; the
  interviewer chooses one and records it]`. The interviewer records whether a
  loss or device-change incident is described. `[NOTE FOR PM]` Named journeys for the
  product PRD come out of these interviews; none exist yet.
- **UJ-3. A parent attempts Power mode setup unaided.** A Non-technical parent is handed the
  draft Onboarding script and their own Android phone, and left alone. The observer records
  completion, elapsed time and where they stopped.
- **UJ-4. The Decider reads the results.** The results land in the `brief.md` §6 Result
  column and as a comment on Discussion #5. The Decider checks them against the Graduation
  criteria in `brief.md` §7 and applies `idea:approved` or writes why not.

## 3. Glossary

- **World** — one Minecraft Bedrock save, stored as a folder inside the game's app-private
  storage on a phone or tablet.
- **Library** — every World on one device.
- **Share-sheet baseline** — exporting a World as a `.mcworld` file through the OS share sheet,
  with no special storage access. The zero-setup tier of the hypothesis.
- **Power mode** — automatic whole-Library backup using Shizuku (ADB-level access without
  root). The core tier of the hypothesis.
- **Desktop companion** — a computer-side tool for large migrations. A tier of the hypothesis;
  not tested in this programme.
- **Include/skip file set** — the list of files to copy and the account/settings files to
  omit so a restored Library loads without crashing (POC comment).
- **Fake door** — a page on `worldchest.app` that describes the Family plan and offers a
  waitlist, without taking payment or delivering anything.
- **Waitlist sign-up** — an adult visitor who leaves an email address on the Fake door.
- **Conversion threshold** — the waitlist-sign-ups-per-visitor rate the Decider writes down
  before the Fake door goes live (`brief.md` §7).
- **Parent interview** — a structured conversation with one adult parent of a Bedrock player
  about device changes, lost Worlds and what they pay for.
- **Hallway test** — one Non-technical parent following the Onboarding script on their own
  Android phone with no help.
- **Non-technical parent** — a parent who has never enabled Developer options or used ADB on
  a phone `[ASSUMPTION: the thread and brief do not define the term]`.
- **Onboarding script** — the parent-facing, step-by-step instructions for Power mode setup
  used in the Hallway test.
- **Decider** — the human who applies `idea:approved` on Discussion #5 (the idea owner).
- **Family plan** — the hypothesised recurring subscription (~$5/mo, `brief.md` §6 row 1),
  bought by a parent.
- **Disclaimer** — the "NOT AN OFFICIAL MINECRAFT PRODUCT" notice the brand decision says
  the Minecraft Usage Guidelines require on the listing and site. The Guidelines' full
  required wording was not read by any input `[ASSUMPTION: the thread's short form is used
  until FR-5 confirms the exact wording]`.
- **Naming rule** — "Minecraft" only as a secondary title ("backup for Minecraft worlds"),
  never in the brand, domain, handles or packages (brand decision, 2026-10-19).
- **Graduation criteria** — the pass conditions in `brief.md` §7.

## 4. Functional Requirements

### 4.0 Hypothesis under test (not authorised to build)

The product the tests are about is the thread's tiered access model: Share-sheet baseline for
everyone, Power mode for automatic versioned whole-Library backup and restore using the
Include/skip file set, a Desktop companion for big migrations, and the official Mojang API as
the long-term goal, sold to parents as a Family plan under the WorldChest brand
`[ASSUMPTION: parents will pay about $5/mo; brief §6 row 1]` `[ASSUMPTION: Mojang ships
no native mobile cloud saves within about 18 months; brief §6 row 5]`. The Include/skip file
set comes from one author-reported migration on two devices and is not independently
verified (`market-research.md`, "The gap / wedge") `[ASSUMPTION: it generalises beyond those
devices]`. Nothing in §4.1–§4.6 builds any of it. Each test maps to one row of `brief.md`
§6.

### 4.1 Demand evidence (brief §6 row 1)

**Description:** the riskiest assumption is that parents will pay a recurring fee when Realms
($3.99/mo, includes backups) and a $0.99 sync app exist. Two instruments test it together: a
Fake door that measures intent to sign up, and Parent interviews that establish whether the
loss incident is real and what parents already pay for. Realises UJ-2 and UJ-4.

#### FR-1: Fake door on worldchest.app

The Decider can publish a Fake door for the Family plan at `worldchest.app` and count visitors
and Waitlist sign-ups.

**Consequences (testable):**
- Before the page receives its first visitor, the Conversion threshold is written into
  `brief.md` §6 row 1 (or the Discussion) with a date.
- The page names the product WorldChest, follows the Naming rule, and shows the Disclaimer.
- The page takes no payment and stores nothing but an email address and a timestamp per
  Waitlist sign-up `[ASSUMPTION: an adult's email with no child data is the least the test
  can collect; counsel has not reviewed this]`.
- "Visitor" means a unique session as counted by the page's analytics; the test window
  (start and end date) is written down with the Conversion threshold before launch
  `[ASSUMPTION: the brief sets neither; both are the Decider's to fix before the first
  visitor]`.
- Visitor count, sign-up count and the resulting rate are recorded with the date range.

**Out of Scope:** pricing experiments beyond the single stated price; advertising spend
`[ASSUMPTION: traffic comes from the owner's own channels; the brief names no budget]`.

#### FR-2: Parent interviews

The Decider (or a delegate) can interview five parents of Bedrock players aged about 7–15 who
have changed a device or lost Worlds within the last twelve months `[ASSUMPTION: the brief
says "recent" without a bound]`, and record the outcome per interview.

**Consequences (testable):**
- Five interviews are completed and dated; each has notes.
- Each record states whether the parent described a lost-World or device-change incident
  (yes/no), what they did about it, and what backup-like services they already pay for.
- The count of parents describing an incident is written into `brief.md` §6 row 1.

**Out of Scope:** interviewing children; surveys; compensation beyond what the Decider chooses
`[ASSUMPTION: recruitment comes from the owner's own network; the brief names no channel]`.

### 4.2 Onboarding feasibility (brief §6 row 2)

**Description:** the thread's "biggest conversion risk" is that Power mode setup needs a
technician. The test packages the POC know-how as an Onboarding script and watches three
Non-technical parents follow it alone. Realises UJ-3.

#### FR-3: Shizuku Hallway test

The Decider can run three Hallway tests from one Onboarding script and record completion and
time for each.

**Consequences (testable):**
- An Onboarding script exists that takes a parent from installing the Shizuku app to the
  end state below on their own Android phone, with no command line or computer required of
  the parent `[ASSUMPTION: Shizuku's wireless-debugging route makes this possible on
  Android 11+; the POC used a computer and ADB]`.
- **End state ("completed Power mode setup"):** no WorldChest app exists, so completion is
  Shizuku's own status screen reporting that its service is running, reached by the parent
  without help `[ASSUMPTION: Shizuku's status screen is the only observable end point
  available before any product code; the thread describes no onboarding steps]`.
- If the script cannot avoid a computer step (§9 question 4), the test still runs; the
  computer step is recorded, and SM-3 is reported as "completed with a computer step".
- Three Non-technical parents each attempt it unaided ("unaided" = no words or touches
  from the observer after the phone and script are handed over); for each, completion
  (yes/no), elapsed time and the step where they stopped are recorded.
- The tester's phone is left in its original state afterwards (Developer options and
  wireless debugging turned back off) `[ASSUMPTION: the setup is reversible with no data at
  risk; not stated in the thread]`.
- The completion count is written into `brief.md` §6 row 2.

**Out of Scope:** a real backup run during the test; iOS.

### 4.3 Share-sheet baseline spike (brief §6 row 3)

**Description:** the zero-setup tier only exists if current Bedrock mobile builds can export a
World through the share sheet and re-import it. One day, two devices.

#### FR-4: Share-sheet round trip

The Decider can export one World as a `.mcworld` through the share sheet and re-import it, on
one Android 15 device and one iOS device, and record the result for each.

**Consequences (testable):**
- For each device: whether an export action exists in the game, whether the exported file
  arrives in a chosen destination, and whether re-import produces a World that loads.
- Game version and OS version are recorded for each device.
- Time-box of one working day; an unfinished spike is recorded as "not shown", not as a
  failure.
- The result is written into `brief.md` §6 row 3.

**Out of Scope:** automating the export; multi-World export.

### 4.4 Legal gate (brief §6 row 4)

**Description:** the brand decision already settled naming and the Disclaimer. Whether a *paid*
third-party backup service for user Worlds is permitted is not settled, and the EULA page did
not load during research (`brief.md` §8). This is a gate, not a feature.

#### FR-5: EULA and Usage Guidelines read

The Decider can produce a dated one-page note on whether a paid third-party backup service for
user Worlds is permitted, prohibited or unclear under the Minecraft EULA and Usage Guidelines.

**Consequences (testable):**
- The note quotes the clauses it relies on, with the URL and the date read.
- It states one of permitted / prohibited / unclear, and what would change the answer.
- A written question is sent to Mojang brand or legal, and the send date and any reply are
  recorded.
- The verdict is written into `brief.md` §6 row 4.

**Out of Scope:** engaging counsel `[ASSUMPTION: the brief budgets one hour of reading and a
written question, not legal fees]`; COPPA / GDPR-K design, which is deferred to the product
PRD (§9).

#### FR-6: Brand compliance carried forward

Everything the programme publishes (the Fake door, any Discussion or social post) follows the
Naming rule and carries the Disclaimer.

**Consequences (testable):**
- No published page, handle or package name contains "Minecraft" except as a secondary title.
- The Disclaimer appears on the Fake door.
- Every Discussion comment or social post the programme publishes about WorldChest follows
  the Naming rule and, where it describes the product, carries the Disclaimer.

### 4.5 Incumbent watch (brief §6 row 5)

#### FR-7: Mojang native-backup watch

The Decider can keep a dated note of any Mojang announcement or release of native mobile World
export or cloud saves, checked at least once during the programme and once more before the
decision.

**Consequences (testable):**
- The note lists the feedback-site threads and release-notes pages checked, with dates.
- Any native feature found is written into `brief.md` §6 row 5 and is grounds for a "no".

**Out of Scope:** building anything in response; a standing monitor beyond the decision date
(§9).

### 4.6 Evidence record and decision return

**Description:** the programme ends when the Decider has the evidence in one place and has
decided. Realises UJ-4.

#### FR-8: Results into the brief and the Discussion

The Decider can read every test's result in `brief.md` §6 and a summary comment on
Discussion #5, and record the decision.

**Consequences (testable):**
- Each of rows 1–5 in `brief.md` §6 has a dated Result entry (a value, "not shown", or "not
  run" with a reason).
- A comment on Discussion #5 lists the five results against Graduation criteria (a) and (b)
  in `brief.md` §7 and the "say no" conditions. Criterion (c), a non-technical user
  completing an end-to-end restore on a fresh device with zero crashes, needs product code
  and is reported as "not testable in this programme" `[NOTE FOR PM]` the Decider must
  either accept (a) and (b) alone or authorise a restore prototype as a separate step.
- The decision is recorded as `idea:approved` on the Discussion, or as a comment saying why
  not, with the date.

## 5. Constraints and Guardrails

- **Privacy.** No child is a participant and no child data is collected. The Fake door stores
  an adult email and a timestamp only. Interview notes name no child. World files are not
  uploaded anywhere by this programme.
- **Safety of participants' devices.** The Hallway test touches a parent's own phone;
  nothing is backed up, deleted or restored during it, and the phone is returned to its
  original settings (FR-3).
- **Cost.** About one week of the owner's time in total (`brief.md` §7); no paid traffic,
  no counsel `[ASSUMPTION: carried from the brief's "cost about a week together and need no
  product code"]`.
- **Brand.** See FR-6.

## 6. Non-Goals (Explicit)

- No product code, no Android or iOS app, no backend, no cloud storage of Worlds.
- No app-store listing and no Google Play policy test for a Shizuku-dependent app (open in
  `brief.md` §8; it belongs to the product PRD).
- No paid plan, no payment collection, no price testing beyond the one stated price.
- No iOS work beyond the FR-4 spike.
- No research into creators, streamers or classrooms.
- No COPPA / GDPR-K architecture design; the programme avoids the question by collecting no
  child data (§5).
- No Desktop companion test; the POC already proved the manual migration path.
- No versioning or rewind spike (`ost.md` test A3, "scheduled Shizuku backup survives
  reboot and restores a prior version"): it needs product code, so it is deferred to the
  product PRD. The Vision's "rewind" therefore stays untested by this programme.
- No end-to-end restore test by a non-technical user (`brief.md` §7 criterion c): same
  reason, same deferral.
- No Java Edition.

## 7. MVP Scope

### 7.1 In Scope

- FR-1 Fake door and FR-2 Parent interviews (demand).
- FR-3 Shizuku Hallway test (onboarding).
- FR-4 Share-sheet round trip on Android 15 and iOS (platform).
- FR-5 EULA / Usage Guidelines note and Mojang question; FR-6 brand compliance (legal).
- FR-7 incumbent watch, time-boxed.
- FR-8 results in the brief and the Discussion, and the decision.

### 7.2 Out of Scope for MVP

- Everything in §6. `[NOTE FOR PM]` The Power mode product itself is the emotionally
  load-bearing deferral: the POC proves it works, and the owner may be tempted to build
  ahead of the evidence. The brief's recommendation is to resist that for one week.

## 8. Success Metrics

Each metric validates the FR(s) it names. Targets are the Graduation criteria in `brief.md`
§7 where the brief sets one; where it leaves the target to the Decider, this document says so
rather than inventing one.

**Primary**
- **SM-1 Incident rate in interviews** — parents who describe a lost-World or device-change
  incident, out of five. Target: at least 3 of 5 (`brief.md` §7a). Validates FR-2.
- **SM-2 Fake-door conversion** — Waitlist sign-ups per visitor over the test window.
  Target: at or above the Conversion threshold the Decider sets before launch (`brief.md`
  §7a; the value is open, §9). Validates FR-1.
- **SM-3 Unaided setup completion** — Non-technical parents who reach the FR-3 end state
  (Shizuku reporting its service running) alone, out of three; reported "with a computer
  step" if one was needed. Target: at least 2 of 3 (`brief.md` §7b). Validates FR-3.
- **SM-4 Legal verdict recorded** — a dated permitted / prohibited / unclear note exists and
  the Mojang question has been sent. Target: both done; "prohibited" is a "no" condition
  (`brief.md` §7). Validates FR-5.

**Secondary**
- **SM-5 Share-sheet round trip** — devices (of two) on which export and re-import both
  succeed. Target: none set by the brief; a result on both devices is the deliverable.
  Validates FR-4.
- **SM-6 Programme elapsed time** — working days from the first test to the decision
  comment. Target: about five (`brief.md` §7). Validates FR-8.

**Counter-metrics (do not optimise)**
- **SM-C1 Waitlist size.** A big list bought with urgency copy or dark patterns says
  nothing about paying; the rate against the pre-set threshold is the measure.
  Counterbalances SM-2.
- **SM-C2 Lines of product code written.** Any is a programme failure; the point is to
  decide before building. Counterbalances SM-6.
- **SM-C3 Participant hand-holding.** Help given during a Hallway test invalidates that
  test; a lower honest completion count beats a higher coached one. Counterbalances SM-3.

## 9. Open Questions

1. What is the Conversion threshold? The brief leaves it to the Decider; it must be set and
   dated before the Fake door goes live (FR-1).
2. Where are five qualifying parents recruited from, and who interviews them (FR-2)?
3. Which iOS device and version is used for FR-4, and is an export action available there at
   all? (`market-research.md` reports iOS world files are not reliably visible in Files.)
4. Can the Onboarding script avoid a computer entirely (Shizuku via wireless debugging), or
   does Power mode setup need a one-time PC step? This changes what "unaided" means (FR-3).
5. Does collecting an adult email on the Fake door need a privacy notice beyond the
   Disclaimer? Not reviewed by counsel.
6. Does the incumbent watch (FR-7) stop at the decision, or continue if the idea is parked
   again?
7. COPPA / GDPR-K consent and data-minimisation architecture, and whether World files alone
   are personal information: deferred to the product PRD, unanswered.
8. Google Play policy on a Shizuku-dependent app: deferred to the product PRD, unanswered.
9. What does "a version" mean for rewind (per save, per day, per backup run)? Raised in
   `brainstorm.md`; the POC shows one backup-and-restore cycle only.

## 10. Assumptions Index

- §3 Glossary — a Non-technical parent is one who has never enabled Developer options or
  used ADB; the thread and brief do not define the term.
- §4.1 FR-1 — the Fake door collects only an adult email and a timestamp, with no counsel
  review.
- §4.1 FR-1 — Fake-door traffic comes from the owner's own channels; no ad budget.
- §4.1 FR-2 — interview recruitment comes from the owner's own network.
- §4.2 FR-3 — Shizuku's wireless-debugging route lets a parent complete setup without a
  computer on Android 11+; the POC used a computer and ADB.
- §4.2 FR-3 — Power mode setup on a tester's phone is reversible with no data at risk.
- §4.4 FR-5 — the legal gate is one hour of reading and a written question, with no legal
  fees.
- §5 Cost — the whole programme is about one week of the owner's time, carried from the
  brief.
- §3 Glossary — the Disclaimer's short form from the thread is used until FR-5 confirms the
  Usage Guidelines' exact wording.
- §2.3 UJ-2 — no input sets an interview length; the interviewer chooses and records one.
- §4.0 — parents will pay about $5/mo (`brief.md` §6 row 1).
- §4.0 — Mojang ships no native mobile cloud saves within about 18 months (`brief.md` §6
  row 5).
- §4.0 — the POC's Include/skip file set generalises beyond the author's two devices
  (author-reported, n=1, per `market-research.md`).
- §4.1 FR-1 — "visitor" is a unique session and the test window is fixed before launch;
  the brief sets neither.
- §4.1 FR-2 — "recent" device change or loss means within the last twelve months.
- §4.2 FR-3 — Shizuku's status screen is the only observable end point before any product
  code exists.
