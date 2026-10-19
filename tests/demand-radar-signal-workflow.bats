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

setup() {
  REFRESH="$(_job_block refresh)"
  DEPLOY="$(_job_block deploy-pages)"
  export REFRESH DEPLOY
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

@test "the refresh job grants contents: read and nothing else" {
  perms="$(printf '%s\n' "$REFRESH" | awk '/^    permissions:/{p=1;next} /^    [a-z_-]+:/{p=0} p' | grep -oE '^      [a-z-]+: [a-z]+' | sed 's/^ *//' | sort | tr '\n' ' ')"
  [ "$perms" = "contents: read " ]
}

@test "the deploy-pages job grants exactly pages: write and id-token: write" {
  perms="$(printf '%s\n' "$DEPLOY" | awk '/^    permissions:/{p=1;next} /^    [a-z_-]+:/{p=0} p' | grep -oE '^      [a-z-]+: [a-z]+' | sed 's/^ *//' | sort | tr '\n' ' ')"
  [ "$perms" = "id-token: write pages: write " ]
}

@test "pages: write and id-token: write appear only inside the deploy-pages job" {
  # Two grants in the whole file, both of them in the deploy job block.
  [ "$(grep -cE '^\s+(pages|id-token): write' "$DR_YML")" -eq 2 ]
  [ "$(printf '%s\n' "$DEPLOY" | grep -cE '^      (pages|id-token): write')" -eq 2 ]
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
