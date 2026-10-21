---
artifact: brainstorm
status: final
---

# Brainstorm — WorldChest (working name BlockVault): backup, sync, restore & versioning for Minecraft Bedrock worlds

- **Slug:** `worldchest`
- **Source Discussion:** https://github.com/combsmith/incubator/discussions/5
- **Last updated:** 2026-10-21
- **Facilitator:** Mary 📊 (Analyst), headless run of the vendored `bmad-brainstorming` method
  (`prompts/incubation/producer-brainstorm.md` overlay)
- **Inputs:** Discussion #5 body (2026-07-12); the author's POC-evidence comment (2026-07-12);
  the brand-decision comment (decision dated 2026-10-19, posted 2026-10-20); the decision-brief
  comment (2026-10-20); prior artifacts `brief.md`, `market-research.md`, `ost.md`.

**Provenance.** No live facilitated session was held. This document is the headless capture of
what the Discussion thread actually explored, organised with the method's divergent-then-
convergent shape (frame broadly → diverge → converge → action). Every row and claim below
traces to the thread or to a prior artifact in this package. Sentences marked *(inferred)* are
Mary's connective reasoning, not thread content. The private concept brief and the internal
runbook the thread links were not available to this run.

## Problem space

**Session topic (thread):** kids sink hundreds of hours into Minecraft **Bedrock** worlds that
live in a single fragile on-device folder. A new phone, a cracked screen or a bad update wipes
them. There is no undo, no history and no simple device-to-device move.

**Session goal (thread, restated):** decide whether a parent-runnable, versioned, whole-library
backup and restore of Bedrock worlds is a product worth incubating, and what shape it takes.

Framing before narrowing, walking the thread's own "why" chain (Five Whys lens on the body):

- **Why do worlds get lost?** The library is one app-private folder (body). The "free"
  routes fail: Samsung Smart Switch copies the data
  in a state that corrupts and crashes the game; Realms is paid hosted multiplayer, not
  preservation of a *local* library; manual copying took the author ADB, a Chromebook and most
  of a day for 232 worlds (Galaxy S22 → S24).
- **Why now?** Bedrock is ubiquitous on cheap and hand-me-down kid devices, cloud storage is
  cheap, and the migration mechanics were just proven firsthand. The thread asserts "most
  families just lose the worlds instead"; `brief.md` §1 marks that as asserted, not evidenced.
- **Why is it hard?** Android 11+ and iOS forbid one app reading another app's private
  storage. The thread calls platform storage both "the moat *and* the risk".
- **Why would anyone pay?** Parents already pay for photo backup, device insurance and peace
  of mind (thread). Whether they will pay for *this* is the thread's claim, not its evidence.

**Stakeholders the thread names** (Role Playing lens, no perspectives added):

| Role | What the thread says they want |
|------|--------------------------------|
| Young Bedrock player, ~7–15, phone/tablet (primary user) | Keep every world built; rewind to an earlier save |
| Parent (buyer) | Peace of mind "without any technical work"; already pays for backup-like services |
| Map creators and streamers (secondary) | Versioned saves |
| Minecraft Education classrooms (secondary) | Named only; no need stated |
| Mojang (counterparty, raised as a question) | EULA permission, trademark-safe naming; later the Usage Guidelines naming rule |

## Ideas explored

Divergent inventory of every option the thread raised, with the discards kept. Rows are
grouped by the domain they came from so the pivot between domains is visible (access
mechanism → product shape and business → segments → brand). Nothing here was generated for
this document; the "Why kept / dropped" column records the thread's reasoning, with inferences
tagged.

| Idea | Promise | Why kept / dropped |
|------|---------|--------------------|
| **Zero-setup `.mcworld` share-sheet export** (body: "baseline (everyone)") | Works with no special storage access, on any device | **Kept as the baseline tier.** The body lists its durability under tightening OS storage rules as an open question. It exports one world at a time (`market-research.md`, "In-game world export") |
| **Shizuku (ADB, no root) "power mode"** for automatic full-library backup (body) | Whole library, automatic, no technician on hand | **Kept as the core tier.** The body names parent-proof onboarding as "the biggest conversion risk". The POC comment confirms the Android 15 owner-only storage behaviour and a working write path around it |
| **Desktop companion** for big migrations (body) | "For big migrations" (body); the 232-world case *(inferred)* | **Kept as a tier for large moves.** It productises the ADB path the author actually used *(inferred)* |
| **Official Mojang API** (body: "the long-term holy grail") | Sanctioned, cross-platform access with no storage workaround | **Kept as horizon only.** The thread places it long-term; nothing this team can build or test today *(inferred)* |
| **Phone-transfer tools** such as Samsung Smart Switch (body, POC comment; `market-research.md`) | Zero effort, already part of the upgrade (`market-research.md`) | **Dropped.** The POC reproduced the corrupt/crashing restore this path causes |
| **Manual copy via ADB + Chromebook** (body, POC comment) | Free, whole library | **Dropped as a product; kept as know-how.** 232 worlds took most of a day. The exercise yielded the include-vs-skip file set (skip the account/settings files) and md5-verified round trips that the tiers above build on |
| **Realms** (body; `market-research.md`) | Official, hosted; includes backups (`market-research.md`) | **Dropped as the answer.** Paid hosted multiplayer, not preservation of a local library. Kept as a positioning problem: "doesn't Realms already do that?" |
| **Google Drive as the backup target** (POC comment) | Cheap (body: "cloud storage is cheap"); the POC's proven target | **Recorded as the POC's choice, not a decision.** The thread does not choose the product's storage target |
| **Integrity-verified whole-library backup** (POC: md5, include/skip set) | A restore that loads with no corruption | **Kept.** This is the wedge `market-research.md` names |
| **Versioned saves with rewind** (title; JTBD "rewind to an earlier save") | Undo for a bad update, grief or mistake | **Kept as part of the job.** The POC comment describes one backup-and-restore cycle, so versioning is not yet demonstrated *(inferred)* |
| **Freemium → Family subscription, ~$5/mo, parent as buyer** (body) | Parent pays as they do for photo backup or device insurance | **Kept as the working model.** Price and willingness to pay are untested; `brief.md` §6 row 1 |
| **Map creators and streamers** as a segment (body) | Versioned saves for people who publish worlds | **Parked.** Named as secondary; not validated (`brief.md` §2) |
| **Minecraft Education classrooms** as a segment (body) | A second institutional buyer | **Parked.** Named only; no need or evidence in the thread |
| **"BlockVault"** as the product brand (body, working name) | The working name since capture (body) | **Dropped 2026-10-19.** Squatted on .com, .app, the GitHub org and four social handles (brand comment) |
| **"Minecraft" in the brand, domain, handles or packages** | The body's "trademark-safe naming?" question, answered | **Dropped.** The Minecraft Usage Guidelines allow "Minecraft" only as a secondary title ("backup for Minecraft worlds"), with the NOT AN OFFICIAL MINECRAFT PRODUCT disclaimer on listing and site (brand comment) |
| **"WorldChest"** (brand comment) | Available everywhere that mattered | **Selected.** `worldchest.app` registered with auto-renew, PyPI and npm `worldchest` placeholders, Instagram `worldchest.app`; slug `worldchest`; product repo `combsmith/worldchest` (`brief.md` §8) |

Raised as **questions rather than options**, so they appear under Open questions, not here:
Mojang EULA permission for third-party backup; COPPA / GDPR-K consent architecture; Realms
positioning confusion.

## Selected direction

**The thread converged on a tiered access model, and this brainstorm hands that forward as
the hypothesis under test, not as a build decision.**

1. **Tiers, in order of reach:** `.mcworld` share-sheet baseline for everyone → Shizuku
   power mode for automatic, integrity-verified, whole-library backup with versioning →
   desktop companion for big migrations → official Mojang API as the long-term goal.
2. **Buyer and model:** the parent, on a freemium-to-Family subscription (price untested).
3. **Brand:** WorldChest, under the Usage Guidelines naming rule and disclaimer.
4. **Know-how carried in:** the include/skip file set and md5-verified restore from the
   232-world POC.

**Why this direction (thread reasoning):** the POC answered "can it be done and what exactly
to move". What remains is productising access without a technician (Shizuku and share-sheet
UX) and the legal and privacy gates (EULA, COPPA). That is the thread's own risk split, and the
tiered model is its answer to the access half.

**Prioritisation of what to learn next** (the method's convergent step, applied to the thread's
open questions; ordering is *inferred* and matches `brief.md` §6 and `ost.md`):

- **Kills the business if wrong:** will parents pay a recurring fee when Realms and a $0.99
  sync app exist? → fake door on `worldchest.app` plus five parent interviews.
- **The thread's own biggest conversion risk:** can a non-technical parent finish Shizuku
  setup unaided? → hallway test with three parents.
- **Cheapest to settle:** does the share-sheet export round-trip on Android 15 and iOS? →
  one-day spike.
- **Gate, not a feature:** does the EULA / Usage Guidelines allow a *paid* third-party backup
  service? → one-hour read plus a written question to Mojang.

**Scores on record:** the thread's gut-check was ICE Impact 5 / Confidence 3 / Ease 2. The
brief, built on this direction, lowers Impact to 4 and Confidence to 2 (evidence is about
feasibility, not demand), giving ICE 16/125, and recommends **park: buy evidence first** (`brief.md` §5 and §7). This brainstorm does
not override that; it is what the brief and the PRD build on.

## Open questions

Surfaced in the thread and not resolved there (two sharpened by `brief.md` §6 and §8, as
marked):

- Does the Mojang EULA permit a third-party backup service for user-created worlds? Naming
  is settled by the 2026-10-19 brand decision; whether a *paid* service is allowed is the
  sharper form in `brief.md` §6 row 4.
- **COPPA / GDPR-K:** what parent-consent and data-minimisation architecture does storing
  minors' content need? `brief.md` §8 adds: are world files alone "personal information"?
- Can Shizuku power-mode onboarding be made genuinely parent-proof?
- Is the `.mcworld` share-sheet baseline durable as OS storage rules keep tightening?
- How much "doesn't Realms already do that?" confusion is there to overcome?

Surfaced by this organisation of the thread (tagged inferred):

- Versioning and rewind are in the job but not in the POC; what does "a version" mean (per
  save, per day, per backup run)? *(inferred)*
- The product's storage target (the POC used Google Drive) is undecided. *(inferred)*
- iOS beyond share-sheet export: the thread raises the iOS storage rule but explores no iOS
  tier (`brief.md` §8 lists it as open).
- Google Play policy on an app that depends on Shizuku: raised in `market-research.md`, not in
  the thread.
