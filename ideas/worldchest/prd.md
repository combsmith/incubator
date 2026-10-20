---
artifact: prd
status: final
---

# PRD — WorldChest (working name BlockVault)

- **Slug:** `worldchest`
- **Source Discussion:** https://github.com/combsmith/incubator/discussions/5
- **Seeded from:** `brief.md`
- **Last updated:** 2026-10-20

Scope note: the brief recommends **park**. This PRD defines the first build only if the
decider approves after the evidence tests in `brief.md` §6. It is a lean PRD and has not
been through the BMAD `bmad-prd` validation checklist.

## Vision
A parent can keep every Minecraft Bedrock world their child has built, and rewind to an
earlier save, across a device change or a corrupted world, with no technical work.

## Target User & JTBD
Young Bedrock players (~7–15) on phones/tablets are the users; their parents are the
buyers. The job: when a device changes or a world corrupts, keep every world and rewind
to an earlier save without losing hours of play. Personas are in `brief.md` §2.

## Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-1 | Export a single world as `.mcworld` through the share sheet, with no special access | must |
| FR-2 | Guided Shizuku setup that a non-technical parent can finish unaided | must |
| FR-3 | Automatic backup of the whole local world library using the POC's known include/skip file set | must |
| FR-4 | Keep versions of each world and restore any earlier version | must |
| FR-5 | Restore the full library on a fresh device with zero game crashes, verified by checksum | must |
| FR-6 | Parent account with verifiable parental consent before any child's content is uploaded | must |
| FR-7 | Show a prominent "not an official Minecraft product" disclaimer and avoid official-looking branding | must |
| FR-8 | Desktop companion for large migrations | should |

## Non-Functional Requirements
- **Privacy:** minimise stored data. Which fields count as personal information is a legal
  question pending counsel review (see `market-research.md`).
- **Integrity:** every restore is checksum-verified against the backup.
- **Usability:** no command line or ADB for the parent.
- **Compliance:** subject to Mojang EULA/Usage Guidelines review before any paid launch.

## Success Metrics
Outcome: paying families whose kids lose zero worlds across a device change [ASSUMPTION,
no metric in the thread]. Graduation targets come from `brief.md` §7: at least 3 of 5
interviewed parents describe a loss incident, the fake door converts at a rate the decider
sets in advance, 2 of 3 non-technical parents finish setup unaided, and an end-to-end
restore on a fresh device has zero crashes.

## Scope & Non-Goals
In: Android share-sheet baseline, Shizuku power mode, versioned backup and restore, parent
account. Out for the first build: iOS beyond share-sheet export, creator/streamer and
classroom features, Java edition.

## Open Questions
- Is a paid backup service for player worlds allowed by the Mojang EULA/Usage Guidelines?
- What parent-consent and data-minimisation architecture is needed (COPPA, GDPR-K)?
- Does Google Play permit an app that depends on Shizuku?
- Is anything beyond manual `.mcworld` export feasible on iOS?

## Assumptions
1. Parents will pay about $5/mo despite Realms and a $0.99 app.
2. A non-technical parent can complete Shizuku setup unaided.
3. Mojang will not ship native mobile cloud saves within ~18 months.
4. The POC's include/skip file set generalises beyond the author's devices (n=1).
