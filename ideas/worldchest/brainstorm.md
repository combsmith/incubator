---
artifact: brainstorm
status: final
---

# Brainstorm — WorldChest (working name BlockVault)

- **Slug:** `worldchest`
- **Source Discussion:** https://github.com/combsmith/incubator/discussions/5
- **Last updated:** 2026-10-20

Provenance: this brainstorm is reconstructed from the Discussion thread only. No separate
facilitated session was held, and no option below was tested beyond what the thread's POC
covers.

## Problem space
Kids' Minecraft Bedrock worlds live in one on-device folder. A new phone, a broken device
or a bad update can wipe them, and there is no undo. The thread's author moved 232 worlds
between phones by hand (ADB, a Chromebook, most of a day). Android keeps making that
folder harder to reach, so the manual route keeps getting worse. The question is whether a
parent-runnable, versioned, whole-library backup is a product.

## Ideas explored

| Idea | Promise | Why kept / dropped |
|------|---------|--------------------|
| Zero-setup `.mcworld` share-sheet export | Works for everyone, no special access | Kept as the baseline tier. One world at a time, so it cannot carry the product alone |
| Shizuku "power mode" automatic versioned backup | Whole-library, hands-off, versioned | Kept as the wedge. Depends on Android access that may close |
| Desktop companion for big migrations | Handles hundreds of worlds in one pass | Kept as an add-on for large moves |
| Family subscription plus parent account | Buyer is the parent, and consent is needed for kids | Kept. Price (~$5/mo) is an untested assumption |
| Official Mojang API integration | Cleanest path | Dropped: not something this team can build or test |
| Creator/streamer and classroom segments | Possible extra buyers | Parked: not validated |

## Selected direction
Tiered access: a free share-sheet baseline, a Shizuku power mode for automatic versioned
whole-library backup, a desktop companion for migrations, and a Family subscription with a
parent account on top. The first work is evidence on willingness to pay, onboarding
completion and Mojang's terms, not product code (see `brief.md` §6–§7).

## Open questions
- Will parents pay a recurring fee when Realms and a $0.99 app exist?
- Can a non-technical parent finish Shizuku setup unaided?
- Does Mojang allow a paid third-party backup service?
- What consent architecture does a children's audience need?
