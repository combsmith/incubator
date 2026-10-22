# Ideas triage — combsmith/incubator, 2026-10-19

> **Cron: pause `feature-ideation.yml`'s weekly schedule until something triages its output.** 52 bot ideas, 0 human comments on any of them, and the bot's "Weekly Update" comments stopped after 2026-08-31 (9 comments on 8 ideas, none since), so the "weekly" refresh is not happening either. Keep `workflow_dispatch` and the `discussion: created` enhancer. The stub allows editing the cron line. This report changes nothing.

Read-only report. Nothing was posted to, labelled on, or closed in GitHub.

## Scope and method

- **56 open Ideas discussions**, not 54: 52 bot-filed (#48–#159, all labelled `enhancement`, no other labels) and 4 human-filed (#5 BlockVault, #6 ContentTwin, #44 DemandRadar, #165 DemandRadar dashboard). Every comment and reply was read: 14 comments in total.
- Commenters: `github-actions` 9, `don-petry` 2 (#5 and #44), `redbotster` 2, `Tomosu-AI` 1. **No outside human has said anything substantive on any idea.**
- "Evidence" below means something that happened in the world or in this org. An idea's own "Market Signal" section is the pitch and does not count.
- **Org evidence** comes from this repo. It contains 57 commits, 13 of them "sync org-standard workflow stub(s)". It also contains 5 "Compliance: stub-surface-drift / verbatim-stub-drift" fixes, 12 "Fleet Monitor" workflow fixes and 8 SonarCloud fixes. The org runs `agent-shield`, `dev-lead`, `persona-mention`, `pr-review-mention`, `pr-auto-review`, `initiative-driver` and `feature-ideation` as caller stubs. The repo has no `.github/agents/`, no gh-aw files, no plugin manifests and no MCP server code.
- **Externally verified by me on 2026-10-19 (web search):**
  - OpenAI announced the Promptfoo acquisition on 2026-03-09 and committed to keeping the open-source tools.
  - HalluSquatting is real: TAU, Technion and Intuit, around July 2026. The 85% / 100% hallucination rates and the react-codeshift spread to 237 repos are quoted in the CSA note.
  - The "Scanning the Harness" paper is real (arXiv 2609.07360, submitted Sept 2026). **Its authors also released an open-source scanner, `harness-eval`**, as a CLI, GitHub Action, Claude Code plugin and pre-commit hook. No idea or bot comment mentions it.
  - Mitchell Hashimoto's "Ghostty Is Leaving GitHub" post is dated 2026-04-28.
- **Not verified** (bot assertion only): the MCP 2026-07-28 spec details and 400M downloads, MCPJam, CostHQ, GitHub usage-based billing from 2026-06-01, the "57 outages" count, the Agent Plugins 1.0 launch date (idea bodies say both Aug 6 and Aug 12), and DORA 2026.

## 1. Cluster table (20 clusters, 56 discussions)

| # | Cluster | Strongest representative | Subsumes |
|---|---|---|---|
| 1 | DemandRadar | #44 DemandRadar | #165 dashboard on Pages |
| 2 | BlockVault | #5 BlockVault | — |
| 3 | ContentTwin | #6 ContentTwin | — (already has `ideas/content-twin/` brief) |
| 4 | Reusable-workflow contract testing | #98 WorkflowLab | — |
| 5 | Hallucinated / phantom dependencies | #96 SlopGuard | #156 DepPhantom |
| 6 | AI-authored-PR quality gates | #137 DiffSentry | #155 MutaGuard |
| 7 | Static security scan of agent configs, workflows and permissions | #146 HarnessLint | #114 ConfigShield, #119 OWASPAgentScan, #116 AWLint, #71 AgentGuard, #88 PermissionLens, #109 WorkflowDiffGuard, #130 AgentScope, #118 SkillChain |
| 8 | Runtime defense and identity for CI agents | #115 AgentFirewall | #131 AgentPassport |
| 9 | Agent Plugins 1.0 / skill-package tooling | #136 PluginGuard | #139 PluginCompat, #113 PluginForge, #150 PluginMigrate, #147 SkillScorecard |
| 10 | Agent-config sync and policy-as-code | #112 SkillSync | #148 AgentConfigSync, #158 AgentPolicyHub, #85 SkillForge |
| 11 | Protocol conformance, security and migration (MCP, A2A) | #48 MCP Probe | #106 MCPScan, #149 MCPServerCard, #108 MCPMigrate, #157 A2AProbe |
| 12 | MCP governance and infra | #72 MCPRegistry | #105 MCPGateway |
| 13 | Prompt testing and evals | #73 PromptDrift | #51 PromptSpec, #107 AgentEval |
| 14 | Agent cost and budget | #49 AgentLedger | #132 AgentBudget, #74 FleetPulse |
| 15 | Agent-PR outcome and stability metrics | #117 AgentImpactScore | #159 InstabilityRadar |
| 16 | Compliance audit trail, BOM and provenance | #104 AgentAuditTrail | #95 AgentBOM, #111 AgentAttest |
| 17 | Agent-run debugging | #138 AgentForensics | #110 AgentReplay |
| 18 | gh-aw (Agentic Workflows) ecosystem tooling | #129 AgentWorkbench | #120 AgentWorkflowMigrate, #140 AgentRecipes |
| 19 | Agent-fleet runtime primitives | #97 AgentDeconflict | #87 AgentMemory, #86 AgentTriage |
| 20 | Ideation pipeline as a product | #50 IdeaPilot | — |

Named in the brief as overlapping, and confirmed as one cluster each: AgentGuard / OWASPAgentScan / AWLint / AgentScope / HarnessLint / ConfigShield are all in #7. MCP Probe / MCPScan / MCPServerCard are in #11. PluginGuard / PluginCompat / PluginForge / SkillScorecard are in #9. SlopGuard / DepPhantom are in #5. DiffSentry belongs in #6, not #5: only its dependency check overlaps SlopGuard, and the rest is generic lint.

## 2. Verdict per cluster

Counts: **5 advance, 1 already briefed, 13 park, 1 close.** Many discussions inside the parked clusters are duplicates of their representative and can be closed once someone is allowed to close things.

1. **DemandRadar — ADVANCE to brief.** The spike is merged to `main` (PR #121) and taught something concrete: star ratings are useless, review-text resentment is the signal. The README's next step, `ideas/demand-radar/`, "has not been started". Treat #165 as a chore after the brief, not an idea.
2. **BlockVault — ADVANCE to brief.** It is the only idea with a hands-on result from a real user: 232 worlds backed up and restored on a new phone, Samsung Smart Switch crash reproduced. The sample is n=1 (a household). Settle the EULA / COPPA gates in the brief before anything else. It is not agent tooling.
3. **ContentTwin — NO TRIAGE NEEDED.** It already has `brief.md`, `market-research.md` and `ost.md`. I did not assess their quality.
4. **WorkflowLab — ADVANCE to brief.** This org shows the pain directly: 13 stub-sync commits and 5 stub-drift fixes in 57 commits. The outage and Ghostty context is verified (Ghostty post 2026-04-28). Caveats: the central compliance checker already auto-files the drift issues, so the brief must show what contract testing adds beyond detection. #98's body describes static validation but its weekly update re-scopes it to runtime contract testing, so pick one. "No competitor exists" is unverified, and `actionlint` and `act` exist.
5. **SlopGuard + DepPhantom — ADVANCE to brief (merge #156 into #96).** The weekly update's HalluSquatting claim is verified (July 2026 paper; react-codeshift reached 237 repos). The org's agents add dependencies, and `dependency-audit.yml` exists as a baseline to compare against. Only one vendor comment (Tomosu) touches the neighbouring cluster.
6. **AI-PR quality gates — PARK.** The only support is the ideas' own citations (DORA 2026, unverified). The one outside comment is a vendor pitch (Tomosu). No incident or org signal.
7. **Static agent-config scanners — PARK #146; CLOSE the other 8 as duplicates of it.** The need is real. The "Scanning the Harness" paper is verified, and the Plugin4Shell and Trail of Bits items are bot or vendor-cited. But the paper's authors already ship an open-source scanner, `harness-eval`, as a GitHub Action, and the org already runs `agent-shield` on every repo. Run a gap analysis against both before anyone writes a brief. I have not checked the contents of agent-shield's reusable workflow.
8. **AgentFirewall — ADVANCE to brief, scoped as org-internal hardening first.** This org runs mention-triggered agents (`persona-mention`, `pr-review-mention`) and a Discussion-triggered ideation agent, all of which handle untrusted text. The Jan 2026 Claude Code Action and Clinejection incidents come from the idea body and are unverified by me. I did not verify that the agents ingest Discussion comments. #131 AgentPassport is parked as a separate, thinner idea.
9. **Agent Plugins 1.0 tooling — PARK.** There is no plugin in this org to dogfood, and the spec's launch date is inconsistent across ideas (Aug 6 vs Aug 12). The five ideas are one product, so if it ever advances, write one brief on #136.
10. **Config sync / policy-as-code — PARK (collapse to #112).** The org already syncs standards centrally (13 sync commits), so the internal need is met. External demand is pitch only.
11. **MCP / A2A conformance — PARK; close #106, #149, #108 and #157 as duplicates of #48.** The bot rated it "strongest timing window" twice (2026-07-24 and 07-31). But those updates cite unverified facts and name incumbents (MCPJam, the official Inspector). The org runs no MCP servers, so there is no dogfood need. #108's value decays as the 12-month deprecation window runs.
12. **MCP governance / gateway — PARK.** It is infra with no org user and no outside signal.
13. **Prompt testing — PARK; close #51 and #107 as duplicates of #73.** The Promptfoo acquisition is verified, but OpenAI committed to keeping it open source, which weakens the bot's "lock-in window" argument. The org has 6+ agent prompts, but they live in `combsmith/.github`, not here.
14. **Agent cost — PARK until we measure our own agent spend.** The bot cites GitHub usage-based billing from 2026-06-01 (unverified). No org spend number has been produced, and that number is the missing evidence. Fold #132 and #74 into #49.
15. **Outcome metrics — PARK; close #159 as a duplicate of #117.** It depends on DORA 2026 (unverified) and has no org signal.
16. **Audit trail / AIBOM / attestation — PARK; close #95 and #111 as duplicates of #104.** The EU AI Act and CISA dates are regulatory events but are unverified here, and the org is not a high-risk-AI operator that I can see.
17. **Agent-run debugging — PARK; merge #110 into #138.** No incident in this org's history motivates it.
18. **gh-aw tooling — PARK.** The org uses claude-code-action reusable workflows, and this repo has no gh-aw files.
19. **Fleet primitives — PARK.** No duplicate-PR or claim-conflict incident is visible in the org's history. Note that #86 AgentTriage routes *issues* and is not the missing idea-triage stage.
20. **IdeaPilot — CLOSE as already built.** Its own body says the org "already built and operates this entire system", and this repo calls it as `feature-ideation-reusable.yml`. The pipeline's 52 outputs have drawn zero human engagement, which is a negative demand signal.

## 3. Top 10 by evidence (things that happened, not pitches)

| Rank | Cluster | Evidence that happened |
|---|---|---|
| 1 | DemandRadar (#44, #165) | A working spike merged (PR #121). Its run found star ratings useless and review-text resentment predictive. The scheduled workflow is running. |
| 2 | BlockVault (#5) | A real backup and restore of 232 worlds for one real user, plus a reproduced failure of the default path. n=1, non-agent. |
| 3 | WorkflowLab (#98) | In-org: 13 stub-sync commits, 5 stub-drift fixes and 12 Fleet Monitor fixes in 57 commits. World: Ghostty left GitHub citing outages (2026-04-28, verified). |
| 4 | SlopGuard / DepPhantom (#96, #156) | HalluSquatting paper (July 2026) and react-codeshift in 237 repos (verified). The org's agents add dependencies. |
| 5 | Agent-config scanners (#146 + 8) | "Scanning the Harness" paper (Sept 2026, verified) and a released OSS scanner. Evidence supports adopting a scanner, not building one. |
| 6 | AgentFirewall (#115) | The org runs mention-triggered agents on untrusted text. Cited external incidents are unverified. |
| 7 | MCP / A2A conformance (#48 + 4) | Bot-reported spec release, MCPJam and CVEs. Unverified, no org need. |
| 8 | Prompt testing (#73 + 2) | OpenAI announced plans to acquire Promptfoo on 2026-03-09 (verified; the announcement said closing was subject to conditions). The org has 6+ agent prompts, but OpenAI kept the project open source. |
| 9 | Agent cost (#49 + 2) | Bot-reported GitHub usage billing (unverified). The org runs several Claude-backed agents, but nobody has measured the spend. |
| 10 | Agent Plugins 1.0 tooling (#136 + 4) | Bot- and idea-reported multi-vendor spec (Aug 2026, date inconsistent). No org use. |

Ranks 7–10 rest on bot assertions I did not verify. The ordering among them is a judgment call, not a measurement.

## 4. Vendor comments to ignore

| Where | Author | Why ignore |
|---|---|---|
| #119 OWASPAgentScan | `redbotster` | Self-disclosed 1Claw employee pitching a vault product, asking to name it as a remediation in scanner output. Marketing. |
| #146 HarnessLint | `redbotster` | Same author and product (1Claw), "i'm a bit biased". The one useful point, that static scanning cannot cover the secrets category, is generic and needs no vendor. |
| #137 DiffSentry | `Tomosu-AI` | Product plug for Tomosu's Production Risk Index. No substance about the idea. |

None of these is validation. Do not count the commenters as users or leads.

## 5. Structural findings (for whoever wires triage)

- The README lifecycle says `feature-ideation` → `idea-triage` → `idea:approved`. In this repo there is no triage workflow, no `idea:approved` label, and no label on any idea except `enhancement`. Issue #3 (decision-brief stage) is open.
- A triage pass would have collapsed 56 ideas to about 20 clusters at once. Ideation keeps filing near-duplicates because nothing marks an idea as taken (e.g. #156 knew about #96, yet both sit open).
- Nothing the bot says it validated stays attached to the idea: the weekly updates cover 8 of 52 ideas and stopped on 2026-08-31.
