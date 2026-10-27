#!/usr/bin/env bats
# Shape guard for .github/workflows/demand-radar-signal.yml (Discussion #165).
#
# The DemandRadar scheduled refresh publishes dashboard.html to GitHub Pages. That adds
# write-scoped permissions (pages: write, id-token: write) to a workflow that was
# read-only, so these tests pin the security shape the discussion sketched:
#   - the write permissions live on the deploy job ONLY (top level stays `{}`, the
#     refresh job stays `contents: read`);
#   - the deploy job runs in the `github-pages` environment;
#   - it deploys only a CLEAN run (a DEGRADED refresh keeps the last good site) and only
#     from the default branch (a manual dispatch from a feature branch never publishes);
#   - every action is SHA-pinned, per the org Action Pinning Policy;
#   - the existing 30-day build artifact upload is preserved.
# Issue #186 (weekly research session) adds, and these tests pin:
#   - the schedule runs the `weekly` preset; run state is carried between runs as the
#     `demand-radar-state` artifact (refresh job: + actions: read, nothing that writes);
#   - the Analyst (`analyst`) gets a read-only token (contents: read only; Bash limited to
#     cat/jq/the citation gate) and never a Discussions scope;
#   - only the isolated `post-signals` job holds discussions: write, and it runs the
#     citation gate from a clean checkout before posting.
#   - the fleet pause (AGENTS_PAUSED=true) skips the Analyst, and `fleet-paused` says so in
#     a run notice — run 40327424532 lost its weekly comment to a pause with no trace.
# Free-per-repo workflow (tier 3): the shape below is this repo's, not an org stub.

DR_YML="${BATS_TEST_DIRNAME}/../.github/workflows/demand-radar-signal.yml"

# _job_block NAME — the body of job NAME (lines under `  NAME:` until the next job key).
_job_block() {
  awk -v job="  $1:" '$0==job{p=1;next} /^  [a-zA-Z_-]+:/{p=0} p' "$DR_YML"
}

# _step_block JOB STEP_NAME — the body of the step named STEP_NAME inside job JOB.
_step_block() {
  _job_block "$1" | awk -v step="      - name: $2" '$0==step{p=1;next} /^      - name: /{p=0} p'
}

# setup — populate REFRESH and DEPLOY variables by extracting job blocks from the workflow.
setup() {
  REFRESH="$(_job_block refresh)"
  DEPLOY="$(_job_block deploy-pages)"
  ANALYST="$(_job_block analyst)"
  POST="$(_job_block post-signals)"
  PAUSED="$(_job_block fleet-paused)"
  export REFRESH DEPLOY ANALYST POST PAUSED
}

# _perms BLOCK — the job's permission grants as one sorted "key: value " line.
_perms() {
  printf '%s\n' "$1" | awk '/^    permissions:/{p=1;next} /^    [a-z_-]+:/{p=0} p' | grep -oE '^      [a-z-]+: [a-z]+' | sed 's/^ *//' | sort | tr '\n' ' '
}

@test "demand-radar-signal.yml exists" {
  [ -f "$DR_YML" ]
}

@test "the workflow keeps the default-deny top-level permissions" {
  grep -qE '^permissions: \{\}' "$DR_YML"
}

@test "the refresh and deploy-pages jobs both exist" {
  [ -n "$REFRESH" ]
  [ -n "$DEPLOY" ]
}

# ── permission scope ────────────────────────────────────────────────────────────

@test "the refresh job grants only reads: contents (checkout) and actions (last week's state)" {
  [ "$(_perms "$REFRESH")" = "actions: read contents: read " ]
}

@test "the deploy-pages job grants exactly pages: write and id-token: write" {
  perms="$(printf '%s\n' "$DEPLOY" | awk '/^    permissions:/{p=1;next} /^    [a-z_-]+:/{p=0} p' | grep -oE '^      [a-z-]+: [a-z]+' | sed 's/^ *//' | sort | tr '\n' ' ')"
  [ "$perms" = "id-token: write pages: write " ]
}

@test "pages: write appears only inside the deploy-pages job" {
  [ "$(grep -cE '^\s+pages: write' "$DR_YML")" -eq 1 ]
  [ "$(printf '%s\n' "$DEPLOY" | grep -cE '^      pages: write')" -eq 1 ]
}

@test "id-token: write appears only in deploy-pages (Pages OIDC)" {
  [ "$(grep -cE '^\s+id-token: write' "$DR_YML")" -eq 1 ]
  [ "$(printf '%s\n' "$DEPLOY" | grep -cE '^      id-token: write')" -eq 1 ]
}

@test "the deploy-pages job does not check out the repo (no contents permission needed)" {
  if printf '%s\n' "$DEPLOY" | grep -qE 'actions/checkout'; then false; fi
  if printf '%s\n' "$DEPLOY" | grep -qE '^      contents:'; then false; fi
}

# ── environment and gating ──────────────────────────────────────────────────────

@test "the deploy-pages job runs in the github-pages environment" {
  env_block="$(printf '%s\n' "$DEPLOY" | awk '/^    environment:/{p=1;next} /^    [a-z_-]+:/{p=0} p')"
  printf '%s\n' "$env_block" | grep -qE '^      name: github-pages$'
}

@test "the deploy-pages job depends on the refresh job" {
  printf '%s\n' "$DEPLOY" | grep -qE '^    needs: refresh$'
}

@test "the refresh job exposes a 'clean' output derived from the pipeline step outcome" {
  outputs="$(printf '%s\n' "$REFRESH" | awk '/^    outputs:/{p=1;next} /^    [a-z_-]+:/{p=0} p')"
  printf '%s\n' "$outputs" | grep -qE "^      clean: \\$\\{\\{ steps\\.pipeline\\.outcome == 'success' \\}\\}$"
}

@test "the deploy-pages job is gated on a clean (non-DEGRADED) refresh" {
  cond="$(printf '%s\n' "$DEPLOY" | grep -E '^    if: ')"
  [ -n "$cond" ]
  printf '%s\n' "$cond" | grep -qE "needs\\.refresh\\.result == 'success'"
  printf '%s\n' "$cond" | grep -qE "needs\\.refresh\\.outputs\\.clean == 'true'"
  # No always()/failure(): a failed refresh must skip the deploy, never run it.
  if printf '%s\n' "$cond" | grep -qE 'always\(\)|failure\(\)'; then false; fi
}

@test "the deploy-pages job is gated on the default branch (no deploy from a dispatched feature branch)" {
  cond="$(printf '%s\n' "$DEPLOY" | grep -E '^    if: ')"
  printf '%s\n' "$cond" | grep -qE "github\\.ref == format\\('refs/heads/\\{0\\}', github\\.event\\.repository\\.default_branch\\)"
}

@test "the Pages staging and upload steps share the deploy gate" {
  for step in "Stage the dashboard for GitHub Pages" "Upload Pages artifact"; do
    cond="$(_step_block refresh "$step" | grep -E '^        if: ')"
    [ -n "$cond" ]
    printf '%s\n' "$cond" | grep -qE "steps\\.pipeline\\.outcome == 'success'"
    printf '%s\n' "$cond" | grep -qE "github\\.event\\.repository\\.default_branch"
    if printf '%s\n' "$cond" | grep -qE 'always\(\)'; then false; fi
  done
}

@test "the staged site serves the board under /demand-radar/ with a forwarding root page" {
  stage="$(_step_block refresh "Stage the dashboard for GitHub Pages")"
  printf '%s\n' "$stage" | grep -qE 'cp pocs/demand-radar/dashboard\.html _site/demand-radar/index\.html'
  printf '%s\n' "$stage" | grep -qE 'url=demand-radar/'
  upload="$(_step_block refresh "Upload Pages artifact")"
  printf '%s\n' "$upload" | grep -qE '^          path: _site$'
}

# ── action pinning ──────────────────────────────────────────────────────────────

@test "upload-pages-artifact and deploy-pages are used, in the right jobs" {
  printf '%s\n' "$REFRESH" | grep -qE '^        uses: actions/upload-pages-artifact@'
  printf '%s\n' "$DEPLOY" | grep -qE '^        uses: actions/deploy-pages@'
  if printf '%s\n' "$REFRESH" | grep -qE 'actions/deploy-pages@'; then false; fi
}

@test "every action in the workflow is pinned to a full commit SHA with a version comment" {
  uses="$(grep -E '^\s+uses: ' "$DR_YML")"
  [ -n "$uses" ]
  unpinned="$(printf '%s\n' "$uses" | grep -vE '^\s+uses: [A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[0-9a-f]{40} # v[0-9]+\.[0-9]+\.[0-9]+$' || true)"
  [ -z "$unpinned" ]
}

# ── existing behaviour preserved ────────────────────────────────────────────────

@test "the 30-day build artifact upload is preserved and still ships DEGRADED runs" {
  upload="$(_step_block refresh "Upload data + built dashboard")"
  [ -n "$upload" ]
  printf '%s\n' "$upload" | grep -qE '^        if: .*always\(\)'
  printf '%s\n' "$upload" | grep -qE '^        uses: actions/upload-artifact@'
  printf '%s\n' "$upload" | grep -qE '^          retention-days: 30$'
}

# ── weekly research session (issue #186) ────────────────────────────────────────

@test "the schedule and the dispatch default run the weekly preset" {
  printf '%s\n' "$REFRESH" | grep -qE "DR_PRESET: \\$\\{\\{ github\\.event\\.inputs\\.preset \\|\\| 'weekly' \\}\\}"
  grep -qE "^        default: 'weekly'$" "$DR_YML"
  grep -qE '^        options: \[weekly, refresh, full, export\]$' "$DR_YML"
}

@test "last week's state is restored before the pipeline runs" {
  restore_line="$(printf '%s\n' "$REFRESH" | grep -nE "^      - name: Restore last week's run state$" | cut -d: -f1)"
  pipeline_line="$(printf '%s\n' "$REFRESH" | grep -nE '^      - name: Run DemandRadar pipeline' | cut -d: -f1)"
  [ -n "$restore_line" ] && [ -n "$pipeline_line" ]
  [ "$restore_line" -lt "$pipeline_line" ]
  restore="$(_step_block refresh "Restore last week's run state")"
  printf '%s\n' "$restore" | grep -qE 'demand-radar-state'
  # only default-branch state is trusted as a starting point
  printf '%s\n' "$restore" | grep -qE 'head_branch == \$b'
}

@test "the run state is saved only from the default branch, with a long retention" {
  save="$(_step_block refresh "Save the run state for next week")"
  [ -n "$save" ]
  printf '%s\n' "$save" | grep -qE "github\\.event\\.repository\\.default_branch"
  printf '%s\n' "$save" | grep -qE '^          name: demand-radar-state$'
  printf '%s\n' "$save" | grep -qE 'pocs/demand-radar/output/records\.jsonl'
  printf '%s\n' "$save" | grep -qE '^          retention-days: 90$'
}

@test "the digest and deep-dive briefs ship in the artifact and on the Pages site" {
  upload="$(_step_block refresh "Upload data + built dashboard")"
  printf '%s\n' "$upload" | grep -qE 'pocs/demand-radar/output/weekly-digest\.md'
  printf '%s\n' "$upload" | grep -qE 'pocs/demand-radar/output/deepdive/'
  stage="$(_step_block refresh "Stage the dashboard for GitHub Pages")"
  printf '%s\n' "$stage" | grep -qE 'weekly-digest\.md _site/demand-radar/output/'
  printf '%s\n' "$stage" | grep -qE '_site/demand-radar/output/deepdive/'
}

@test "the analyst job has a read-only token and no Discussions scope" {
  [ -n "$ANALYST" ]
  [ "$(_perms "$ANALYST")" = "contents: read " ]
  printf '%s\n' "$ANALYST" | grep -qE '^        uses: anthropics/claude-code-action@'
  # Bash is limited to cat, jq and the citation gate — never a bare `Bash`
  printf '%s\n' "$ANALYST" | grep -qF 'Bash(python3 pocs/demand-radar/analyst_check.py)'
  if printf '%s\n' "$ANALYST" | grep -qE 'allowedTools.*[ ,"]Bash[ ,"]'; then false; fi
  printf '%s\n' "$ANALYST" | grep -qE 'prompts/weekly-signals-analyst\.md'
  if printf '%s\n' "$ANALYST" | grep -qE 'post_signals\.py'; then false; fi
}

@test "the analyst job runs only after a default-branch run that wrote a digest" {
  cond="$(printf '%s\n' "$ANALYST" | grep -E '^    if: ')"
  printf '%s\n' "$cond" | grep -qE "needs\\.refresh\\.outputs\\.digest == 'true'"
  printf '%s\n' "$cond" | grep -qE "github\\.event\\.repository\\.default_branch"
}

@test "only post-signals holds discussions: write, and it gates before posting" {
  [ "$(grep -cE '^\s+discussions: write' "$DR_YML")" -eq 1 ]
  [ "$(_perms "$POST")" = "contents: read discussions: write " ]
  if printf '%s\n' "$POST" | grep -qE 'claude-code-action'; then false; fi
  gate_line="$(printf '%s\n' "$POST" | grep -nE 'run: python3 pocs/demand-radar/analyst_check\.py' | cut -d: -f1)"
  post_line="$(printf '%s\n' "$POST" | grep -nE 'run: python3 pocs/demand-radar/post_signals\.py' | cut -d: -f1)"
  [ -n "$gate_line" ] && [ -n "$post_line" ]
  [ "$gate_line" -lt "$post_line" ]
}

@test "post-signals waits for a drafted comment from the default branch" {
  cond="$(printf '%s\n' "$POST" | grep -E '^    if: ')"
  printf '%s\n' "$cond" | grep -qE "needs\\.analyst\\.outputs\\.drafted == 'true'"
  printf '%s\n' "$cond" | grep -qE "github\\.event\\.repository\\.default_branch"
}

# ── fleet pause (AGENTS_PAUSED) ─────────────────────────────────────────────────

@test "the analyst job keeps the fleet-pause guard" {
  cond="$(printf '%s\n' "$ANALYST" | grep -E '^    if: ')"
  printf '%s\n' "$cond" | grep -qF "vars.AGENTS_PAUSED != 'true'"
  # always() is what lets a DEGRADED (failed) refresh still be reviewed
  printf '%s\n' "$cond" | grep -qE 'always\(\)'
}

@test "a paused fleet leaves a run notice instead of a silent skip" {
  [ -n "$PAUSED" ]
  cond="$(printf '%s\n' "$PAUSED" | grep -E '^    if: ')"
  printf '%s\n' "$cond" | grep -qF "vars.AGENTS_PAUSED == 'true'"
  printf '%s\n' "$cond" | grep -qE "github\\.event\\.repository\\.default_branch"
  printf '%s\n' "$PAUSED" | grep -qE '::notice title=Agent fleet paused::DemandRadar'
}

@test "fleet-paused stands alone and holds nothing that could reach the model" {
  # no needs: (a slow or failed refresh must not silence it)
  if printf '%s\n' "$PAUSED" | grep -qE '^    needs:'; then false; fi
  printf '%s\n' "$PAUSED" | grep -qE '^    permissions: \{\}$'
  if printf '%s\n' "$PAUSED" | grep -qE 'secrets\.|github\.token|uses: '; then false; fi
  # pause metadata reaches the script through env:, never ${{ }} in the run body
  run_body="$(printf '%s\n' "$PAUSED" | awk '/^        run: \|/{p=1;next} p')"
  [ -n "$run_body" ]
  if printf '%s\n' "$run_body" | grep -qF '${{'; then false; fi
}
