---
artifact: market-research
status: final
---

# Market Research — WorldChest (working name BlockVault): backup, sync, restore & versioning for Minecraft Bedrock worlds

- **Slug:** `worldchest`
- **Last updated:** 2026-10-20

Scope: Minecraft **Bedrock** worlds on phones/tablets (Android first, iOS second), for
young players and the parents who would pay. Research was desk-only (web search and
fetch on 2026-10-20). No user interviews, surveys or store analytics were available.
Brand per the thread (2026-10-19): **WorldChest**; "BlockVault" is the working name in the slug.

## How it's solved today

| Alternative | What it does well | Where it falls short | Pricing / model |
|-------------|-------------------|----------------------|-----------------|
| **Minecraft Realms** (official), the route Microsoft's own Q&A recommends for moving a world between mobile devices (https://learn.microsoft.com/en-in/answers/questions/5895884/how-to-transfer-minecraft-worlds-between-one-mobil) | Official, works on every Bedrock platform, no file access needed; includes backups and world slots per third-party summary (https://www.itechguides.com/minecraft-server-vs-realm-cost-breakdown-for-2026/); first-party page: https://www.minecraft.net/en-us/realms | Moves one world at a time through a hosted multiplayer server. It does not preserve a whole *local* library and has no per-device restore of 200+ worlds. Ongoing subscription | Realms $3.99/mo, Realms Plus $7.99/mo per third-party summary (https://www.itechguides.com/minecraft-server-vs-realm-cost-breakdown-for-2026/). Not yet verified against https://www.minecraft.net/en-us/realms (region and access date to be recorded when checked) |
| **Manual file copy** of `Android/data/com.mojang.minecraftpe/files/games/com.mojang/minecraftWorlds` to cloud/USB (https://learn.microsoft.com/en-in/answers/questions/5895884/how-to-transfer-minecraft-worlds-between-one-mobil) | Free, whole-library | Android 11+ blocks `Android/data` and Android 14+ hides it further from file managers (https://www.lonelycatgames.com/docs/xplore/known-problems/no-android-data). In the thread it took ADB, a Chromebook and most of a day | Free, but needs expert time |
| **Shizuku-enabled file managers** (X-plore, FV File Manager, MiXplorer) (https://www.lonelycatgames.com/docs/xplore/known-problems/no-android-data) | No root; regains `Android/data` access | General-purpose tools for technical users. No Minecraft knowledge, such as the include/skip file set the thread's author reports avoids the crash (author-reported, discussion #5: https://github.com/combsmith/incubator/discussions/5; the X-plore source supports only the Android storage restrictions). No versioning, no parent UX. Results vary by device/OEM (same source) | Free / freemium (exact pricing not researched — unknown — needs discovery) |
| **"Bedrock" world-sync app** (`com.draco.bedrock`) syncing worlds to Google Drive (https://beebom.com/how-sync-minecraft-worlds-android/amp/) | Purpose-built, Google Drive storage, cross-device | Depends on Minecraft's "External" storage setting and the same game version on both devices (same source). Whether it still works on Android 14/15 is unknown — needs discovery. Install base unknown — needs discovery | $0.99 one-off per Beebom, updated 2025-10-15 (https://beebom.com/how-sync-minecraft-worlds-android/amp/) |
| **Phone-to-phone transfer tools** (e.g. Samsung Smart Switch) | Zero effort, already part of the upgrade | The thread reproduced a corrupt/crashing restore from this path (n=1, discussion comment). No public source was consulted for how often this happens: unknown — needs discovery | Free with device |
| **In-game world export (.mcworld)** | Official, no special permissions | Per the Microsoft Q&A, an Export option exists on Windows (https://learn.microsoft.com/en-us/answers/questions/5619077/how-to-fix-the-new-minecraft-bedrock-update-that-d). Players on Mojang's feedback site ask for an export button on mobile (https://feedback.minecraft.net/hc/en-us/community/posts/46820338260877-Add-an-In-Game-Export-World-Button-for-Mobile-Devices), so mobile export is at least not obvious. Manual and one world at a time | Free |
| **Java-edition sync mods** (Game Sync, Google Drive Resync) (https://www.curseforge.com/minecraft/mc-mods/game-sync) | Show the demand for "cloud safety net for worlds" exists | Java only. They do not address Bedrock mobile, the target segment | Free mods |
| **Do nothing**, the thread's stated default ("most families just lose the worlds") | — | Worlds are lost. Microsoft confirms Mojang cannot restore locally deleted worlds (https://learn.microsoft.com/en-us/answers/questions/5619077/how-to-fix-the-new-minecraft-bedrock-update-that-d) | — |

## The gap / wedge

- **Gap:** no product found that does an *automatic, whole-library, versioned* backup
  of Bedrock mobile worlds with a restore flow a parent can run without help. Realms is
  per-world and multiplayer-shaped. File managers are generic and technical. The one
  purpose-built app found is a small manual sync tool whose current Android 14/15
  viability is unverified.
- **Wedge:** the thread's n=1 POC (author-reported in discussion #5, https://github.com/combsmith/incubator/discussions/5, not independently verified). It knows the *exact* include/skip file set that
  restores cleanly (skipping account/settings files avoids the Smart Switch-style
  crash), has md5-verified round-trips, and has a working write path around Android 15
  owner-only storage. That knowledge is domain-specific and not visible in any
  general-purpose tool reviewed.
- **Why the wedge is fragile:** it depends on (a) Shizuku/ADB-grade access, which
  Android keeps narrowing (https://www.lonelycatgames.com/docs/xplore/known-problems/no-android-data),
  and (b) Mojang not shipping native mobile export or cloud saves. Players are asking
  Mojang for exactly that
  (https://feedback.minecraft.net/hc/en-us/community/posts/48218526108429-Import-Export-or-Storage-Location-for-Minecraft-Bedrock-esp-Android).
  A first-party feature would close most of the gap overnight.

## Market signal

- **Player base (third-party estimate, not first-party data):** an aggregator puts
  Minecraft at about 204 million monthly active players for 2024 across *all* editions (https://www.searchlogistics.com/learn/statistics/minecraft-user-statistics/)
  and gives no primary source for that figure. The
  share that is Bedrock-on-mobile, under 15, and on a hand-me-down or upgrading device
  is unknown — needs discovery. This is the top of a funnel, not a reach figure, so
  it is **not** used as RICE Reach.
- **Demand evidence: the problem (qualitative, cited):**
  - Microsoft Q&A, 2026-05-19: a user finds worlds don't follow their Microsoft account
    between phones, and a commenter reports permanently losing worlds after deleting
    the app (https://learn.microsoft.com/en-in/answers/questions/5895884/how-to-transfer-minecraft-worlds-between-one-mobil).
  - Mojang feedback-site requests for a mobile World Save Manager
    (https://feedback.minecraft.net/hc/en-us/community/posts/41434704802061-World-Save-Manager-for-Minecraft-Bedrock-Mobile),
    an in-game export button
    (https://feedback.minecraft.net/hc/en-us/community/posts/46820338260877-Add-an-In-Game-Export-World-Button-for-Mobile-Devices),
    and import/export or storage-location control on Android
    (https://feedback.minecraft.net/hc/en-us/community/posts/48218526108429-Import-Export-or-Storage-Location-for-Minecraft-Bedrock-esp-Android).
    These pages returned HTTP 403 to the fetcher, so their vote counts and dates were
    **not** read: unknown — needs discovery.
  - Lost-world threads recur (e.g. worlds deleted by a Bedrock update on Windows,
    https://learn.microsoft.com/en-us/answers/questions/5619077/how-to-fix-the-new-minecraft-bedrock-update-that-d).
- **Demand evidence, willingness to pay: none found.** The idea's ~$5/mo Family price is the author's hypothesis [ASSUMPTION]. The anchors found sit at or below it:
  Realms $3.99/mo, which includes backups (https://www.itechguides.com/minecraft-server-vs-realm-cost-breakdown-for-2026/),
  and a $0.99 one-off sync app (https://beebom.com/how-sync-minecraft-worlds-android/amp/).
  Market size in dollars: unknown — needs discovery.
- **Adjacent traction:** Java-side cloud-sync mods exist (https://www.curseforge.com/minecraft/mc-mods/game-sync).
  Their download counts were not checked: unknown — needs discovery.

## Risks & unknowns

- **Platform: Android storage.** Android 11/13/14 each tightened `Android/data` access.
  Shizuku is the remaining non-root path, and results vary by OEM
  (https://www.lonelycatgames.com/docs/xplore/known-problems/no-android-data). The next
  Android release could close it. Google Play policy on apps that rely on Shizuku is
  unknown — needs discovery.
- **Platform: iOS.** One Microsoft Q&A report describes world files as not reliably
  visible in the Files app on iOS 17
  (https://learn.microsoft.com/en-in/answers/questions/5895884/how-to-transfer-minecraft-worlds-between-one-mobil).
  iOS feasibility beyond `.mcworld` share-sheet export remains unresolved.
- **Incumbent risk.** Mojang ships native mobile export or cloud saves (players are
  asking for it, see Market signal). This would turn the product into a feature.
- **Legal: Mojang.** The official Minecraft Usage Guidelines
  (https://www.minecraft.net/en-us/usage-guidelines) are the primary source: third-party
  tools must not look official, must carry a non-official disclaimer, and commercial use
  is restricted unless specifically covered. This page was not fetched in this research,
  so the points here rest on a secondary summary
  (https://conductatlas.com/platform/minecraft/minecraft-usage-guidelines/provision/CA-P-025271/mandatory-not-official-disclaimer-requirement/).
  The thread's naming rule addresses the naming point only; naming compliance is not
  sufficient. Paid backup-service legality is an explicit, unresolved legal gate. Whether the EULA/Usage Guidelines
  allow a *paid* backup service for user worlds was not confirmed: the EULA page
  (https://www.minecraft.net/en-us/eula) timed out on fetch, so this is unknown — needs discovery.
- **Legal: children's privacy.** The amended FTC COPPA Rule took effect in June 2025, with
  operator compliance due 2026-04-22 (https://www.ashurstperkinscoie.com/en/insights/ftc-finally-publishes-amended-coppa-rule-compliance-deadlines-set/).
  COPPA applicability depends on the target age, whether the service collects personal
  information from children, and which account or world-file fields qualify as personal
  information. Treat parent-account and verifiable-consent architecture as a legal
  assumption pending counsel review. GDPR-K was not researched: unknown — needs discovery.
- **Positioning.** "Doesn't Realms already do that?" Realms does include backups
  (https://www.itechguides.com/minecraft-server-vs-realm-cost-breakdown-for-2026/), so
  the difference (whole local library, versioning, device migration) has to be shown,
  not assumed.

## Sources

- https://learn.microsoft.com/en-in/answers/questions/5895884/how-to-transfer-minecraft-worlds-between-one-mobil
- https://learn.microsoft.com/en-us/answers/questions/5619077/how-to-fix-the-new-minecraft-bedrock-update-that-d
- https://www.itechguides.com/minecraft-server-vs-realm-cost-breakdown-for-2026/
- https://www.lonelycatgames.com/docs/xplore/known-problems/no-android-data
- https://beebom.com/how-sync-minecraft-worlds-android/amp/
- https://feedback.minecraft.net/hc/en-us/community/posts/41434704802061-World-Save-Manager-for-Minecraft-Bedrock-Mobile
- https://feedback.minecraft.net/hc/en-us/community/posts/46820338260877-Add-an-In-Game-Export-World-Button-for-Mobile-Devices
- https://feedback.minecraft.net/hc/en-us/community/posts/48218526108429-Import-Export-or-Storage-Location-for-Minecraft-Bedrock-esp-Android
- https://www.curseforge.com/minecraft/mc-mods/game-sync
- https://www.searchlogistics.com/learn/statistics/minecraft-user-statistics/
- https://conductatlas.com/platform/minecraft/minecraft-usage-guidelines/provision/CA-P-025271/mandatory-not-official-disclaimer-requirement/
- https://www.minecraft.net/en-us/eula
- https://www.minecraft.net/en-us/usage-guidelines
- https://www.minecraft.net/en-us/realms
- https://www.ashurstperkinscoie.com/en/insights/ftc-finally-publishes-amended-coppa-rule-compliance-deadlines-set/
