---
artifact: brief
status: final
---

# Decision Brief — WorldChest (working name BlockVault): backup, sync, restore & versioning for Minecraft Bedrock worlds

- **Slug:** `worldchest`
- **Source Discussion:** https://github.com/combsmith/incubator/discussions/5
- **Author / owner:** don-petry (idea); Mary 📊 (Analyst, brief)
- **Status:** `ready-for-decision`
- **Last updated:** 2026-10-20

## 1. Problem
Kids' Minecraft **Bedrock** worlds live in one on-device folder. A new phone, a broken
device or a bad update can wipe them, and there is no undo. **Evidence:**
- **n=1, firsthand (thread):** the author moved 232 worlds from a Galaxy S22 to an S24.
  It took ADB, a Chromebook and most of a day. Samsung Smart Switch produced a
  corrupt/crashing restore.
- **Public, qualitative:** Microsoft's own Q&A confirms worlds do not follow the Microsoft
  account between phones, and a commenter reports permanently lost worlds
  (https://learn.microsoft.com/en-in/answers/questions/5895884/how-to-transfer-minecraft-worlds-between-one-mobil).
  Mojang cannot restore locally deleted worlds
  (https://learn.microsoft.com/en-us/answers/questions/5619077/how-to-fix-the-new-minecraft-bedrock-update-that-d).
- **Asserted, not evidenced:** "most families just lose the worlds", and that parents
  will pay. How often this happens is unknown — needs discovery.

**Why now:** Android 11, 13 and 14 each made `Android/data` harder to reach
(https://www.lonelycatgames.com/docs/xplore/known-problems/no-android-data), so the
manual workaround keeps getting harder. The team already has a working, md5-verified
backup and restore path for Android 15 (thread POC).

## 2. Target user & JTBD
- **Who:** young Bedrock players (~7–15) on phones/tablets (user); **their parents** (buyer).
  Secondary segments: map creators/streamers and Minecraft Education classrooms (not validated).
- **Job to be done:** When _I get a new device or a world corrupts_, I want to _keep every
  world I've built and rewind to an earlier save_, so I can _keep playing without losing
  hundreds of hours, and without any technical work_.

## 3. Market & competitive context
Today players use **Realms** (official, but one world at a time and multiplayer-shaped:
$3.99/mo, includes backups, https://www.itechguides.com/minecraft-server-vs-realm-cost-breakdown-for-2026/).
Other options are **manual copying** (blocked by Android scoped storage), **Shizuku file
managers** (generic and technical), and a small **$0.99 Google Drive sync app** (https://beebom.com/how-sync-minecraft-worlds-android/amp/), or they do nothing. **Gap:**
nobody offers automatic, versioned, whole-library backup and restore that a parent can
run. **Wedge:** the POC's known include/skip file set that restores without crashing.
**Threats:** Mojang shipping native mobile export or cloud saves (players are asking for it), and Android
closing the Shizuku path. Willingness to pay is unevidenced: the market size is unknown — needs
discovery. Detail: [`market-research.md`](market-research.md); tree: [`ost.md`](ost.md).

## 4. Opportunity → solution
- **Desired outcome (metric):** paying families whose kids lose zero worlds across a device change [ASSUMPTION — thread names no metric].
- **Opportunity addressed:** worlds are lost or corrupted on device change, and there is no history or undo.
- **Proposed solution(s):** tiered access. Everyone gets a zero-setup `.mcworld`
  share-sheet baseline. A **Shizuku power mode** adds automatic versioned whole-library
  backup. A desktop companion handles big migrations. A Family subscription and parent
  account sit on top.

## 5. Value & feasibility (rough)
- **Impact:** 4/5. The pain is real and emotional, and the player base is large. It is not 5 because
  the buyer's willingness to pay is untested and Realms/free tools anchor the price low.
- **Effort:** medium/high (thread). Android power mode plus a cloud backend plus
  COPPA-grade parent consent. iOS beyond share-sheet export may be infeasible.
- **Prioritization score:** ICE, because no measured Reach exists, so RICE would invent it.
  - **ICE = 4 × 2 × 2 = 16 / 125**
  - **Impact 4:** see above.
  - **Confidence 2** (rung 2: the thread plus cited market context, but no user or buyer
    signal). The n=1 POC shows the job is *technically feasible*. The cited forum posts
    show the problem exists. Nothing shows anyone will *pay*, so it does not reach rung 3/4.
    The thread's own gut-check put Confidence at 3. This brief lowers it because the
    evidence is about feasibility, not demand.
  - **Ease 2:** platform storage limits, Shizuku onboarding, COPPA, and legal review of
    the Mojang EULA (matches the thread's Ease 2).

## 6. Riskiest assumptions & cheapest test
| # | Assumption | If wrong… | Cheapest test | Result |
|---|-----------|-----------|---------------|--------|
| 1 | Parents will pay a recurring ~$5/mo Family plan for world backup, even though Realms and a $0.99 app exist [ASSUMPTION] | No business, only a free utility | Fake-door "Family plan — join waitlist" page on worldchest.app, plus 5 parent problem interviews (recent device change, lost worlds, what they paid for) | — |
| 2 | A non-technical parent can complete Shizuku power-mode setup unaided | Automatic backup reaches only technical families, and conversion collapses | Hallway test: 3 non-technical parents follow a draft onboarding script on their own Android phone; measure completion and time | — |
| 3 | The `.mcworld` share-sheet baseline works on current Bedrock mobile (Android 15, iOS) | No zero-setup tier, so iOS and non-power users get nothing | 1-day spike: export and re-import a world through the share-sheet on one Android 15 and one iOS device | — |
| 4 | The Mojang EULA/Usage Guidelines allow a paid third-party backup service for user worlds | Takedown or store rejection | 1-hour read of the EULA and Usage Guidelines, plus a written question to Mojang brand/legal | — |
| 5 | Mojang will not ship native mobile cloud saves within ~18 months [ASSUMPTION] | The product becomes a built-in feature | Monitor the Mojang feedback threads and release notes; time-box, no build | — |

## 7. Recommendation (go / no-go)
**park**: buy evidence first. Feasibility is unusually well retired for a new idea: the
team has a real 232-world restore with a known safe file set. The bet that remains is commercial and
legal: will parents pay, can they complete onboarding, and does Mojang allow it. Tests #1–#4
cost about a week together and need no product code. Run them, then return for `idea:approved`.

- **What a POC must prove to graduate:** (a) at least 3 of 5 interviewed parents describe a
  lost-world or device-change incident *and* the fake door converts visitors to waitlist
  sign-ups at a rate the decider sets before launch. (b) 2 of 3 non-technical parents
  finish Shizuku setup unaided. (c) A non-technical user can complete an end-to-end restore
  on a fresh device with zero crashes.
- **What should make the decider say no:** parents treat it as a free-utility problem
  ("I'd just use Realms / not bother"); Shizuku setup fails for non-technical parents and
  the share-sheet tier cannot carry the product alone; the EULA/Usage Guidelines forbid a
  paid service; or Mojang announces native mobile world backup.
- **The decision is the human's**, made by applying `idea:approved` on the Discussion/PR.
  This brief only recommends.

## 8. Open questions
- **Slug:** the package was generated under `block-vault` and renamed to `worldchest`
  on this PR (2026-10-20) to match the brand decision in the thread; the product repo is
  `combsmith/worldchest`.
- **Brainstorm provenance:** `brainstorm.md` is reconstructed from the Discussion only; no separate facilitated session was held.
- **EULA/Usage Guidelines:** is a *paid* backup service for player worlds allowed? (The EULA page did not load during research.)
- **COPPA / GDPR-K:** what parent-consent and data-minimisation architecture is needed?
  Is storing world files alone "personal information" for children under 13?
- **Google Play policy** on shipping an app that depends on Shizuku: unknown.
- **iOS:** is anything beyond manual `.mcworld` export feasible?
- **Competitor viability:** does the "Bedrock" sync app (https://beebom.com/how-sync-minecraft-worlds-android/amp/) still work on Android 14/15, and how many installs does it have? (unknown — needs discovery)
- **Secondary segments** (creators/streamers, classrooms): not researched.
- The private concept brief and internal runbook the thread references were not available to this stage.
