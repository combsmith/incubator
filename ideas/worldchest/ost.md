---
artifact: ost
status: final
---

# Opportunity–Solution Tree — WorldChest (working name BlockVault): backup, sync, restore & versioning for Minecraft Bedrock worlds

- **Slug:** `worldchest`
- **Last updated:** 2026-10-20

```mermaid
flowchart TD
    O["🎯 Outcome: paying families whose kids lose zero worlds across a device change"]

    O --> OPP1["Opportunity: worlds are lost or corrupted when a kid moves to a new phone"]
    O --> OPP2["Opportunity: no undo — a bad update, grief or mistake ruins a world with no history"]
    O --> OPP3["Opportunity: parents want peace of mind without doing technical work"]

    OPP1 --> S1["Solution: guided whole-library migration (desktop companion / Shizuku power mode)"]
    OPP1 --> S2["Solution: zero-setup .mcworld share-sheet export to cloud"]
    OPP2 --> S3["Solution: automatic versioned backups with rewind (Shizuku power mode)"]
    OPP3 --> S4["Solution: Family subscription with parent account and restore button"]

    S1 --> A1["Test: 3 non-technical parents attempt Shizuku onboarding unaided — completion rate"]
    S2 --> A2["Test: 1-day spike — does Bedrock mobile export .mcworld via share-sheet on Android 15 and iOS?"]
    S3 --> A3["Test: 1-day spike — scheduled Shizuku backup survives reboot and restores a prior version"]
    S4 --> A4["Test: fake-door Family plan on worldchest.app + 5 parent problem interviews"]
```

## Notes
- **Outcome** is a metric, not a feature: *paying families with zero lost worlds across a
  device change*. The thread names no outcome metric, so this one is inferred from the
  JTBD and the freemium-to-Family model [ASSUMPTION].
- **Opportunities** come from the Discussion's problem statement and JTBD (device
  change, no undo, parent as buyer). Creator/streamer and classroom segments are
  left out of the tree until the primary family segment is validated.
- **Solutions** are the thread's proposed tiered-access model. The official Mojang API
  "holy grail" is left out because it is not something this team can test.
- **Assumption tests** match brief §6. A4 (willingness to pay) comes first because it
  kills the business if it fails. A1 comes next because it is the thread's own "biggest
  conversion risk".
- The tree is built from the Discussion only; `brainstorm.md` is reconstructed from the same thread.
