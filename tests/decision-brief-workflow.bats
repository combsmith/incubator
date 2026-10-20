#!/usr/bin/env bats
# Drift regression guard for .github/workflows/decision-brief.yml (issue #3).
#
# decision-brief.yml is a THIN CALLER STUB: Mary (the BMAD Analyst), the vendored
# BMAD skills, the provenance guard and the PR opener all live centrally in
# combsmith/.github-private, behind the reusable decision-brief-reusable.yml
# pinned to the moving `decision-brief/v1-stable` channel tag. Its header forbids
# behavioural edits to the `uses:` ref, the `central_ref` input (which must equal
# the pin), the `secrets:` block and the trigger event shape; only the cron
# schedule and the `max_briefs` sweep cap may be tuned per repo. The one failure
# mode this consumer repo controls is LOCAL DRIFT of the caller: a trimmed
# trigger, a widened top-level permission, a `@main` / SHA / frozen `@vX` ref, a
# `central_ref` that no longer matches the pin, a dropped NOSONAR marker (which
# re-fails the Quality Gate), an `inputs.*` reference that fails workflow setup
# on the discussion/schedule events (the #571 class), or a `max_briefs` that is
# no longer a positive integer. These tests pin those stability invariants so
# such drift fails CI before it ships.
# Mirrors tests/dev-lead-workflow.bats (#39) and tests/feature-ideation-workflow.bats (#64).

DB_YML="${BATS_TEST_DIRNAME}/../.github/workflows/decision-brief.yml"

# Emit the `uses:` line of the `decision-brief` job only (not any other job).
_job_uses() {
  awk '/^  decision-brief:$/ {p=1; next} p && /^    uses:/ {print; exit} p && /^  [^ ]/ {p=0}' "$DB_YML"
}

# Reusable ref pinned on the `uses:` line, i.e. the text after
# `decision-brief-reusable.yml@` up to the first whitespace (a comment or EOL).
_uses_ref() {
  _job_uses | sed -E 's/.*decision-brief-reusable\.yml@([^[:space:]]+).*/\1/'
}

# Emit the body of the top-level `on:` block (event trigger definitions).
_on_block() {
  awk '/^on:$/ {p=1; next} p && /^[^ ]/ {exit} p {print}' "$DB_YML"
}

# Emit the `key: value` lines of the `with:` block under the `decision-brief` job
# (comment lines inside the block are dropped).
_job_with() {
  awk '/^  decision-brief:$/ {ij=1; next} ij && /^    with:$/ {p=1; next} p && /^      [a-z_]+:/ {print} p && /^    [a-z]/ {p=0} ij && /^  [^ ]/ {exit}' "$DB_YML"
}

# Value of one `with:` input (text after `key:` up to EOL, trailing comment stripped).
_with_value() {
  _job_with | awk -v key="$1" '$1 == key":" {sub(/^[^:]+:[[:space:]]*/, ""); sub(/[[:space:]]+#.*$/, ""); print; exit}'
}

@test "decision-brief.yml exists" {
  [ -f "$DB_YML" ]
}

@test "the required workflow name is preserved" {
  grep -qE '^name: Decision Brief — Draft the go/no-go brief for a ripe idea$' "$DB_YML"
}

@test "top-level least-privilege permissions: {} is preserved" {
  # The caller grants nothing itself; every scope the stage needs is held by the
  # central run via the org-level PAT. A widened top-level block is drift.
  grep -qE '^permissions: \{\}$' "$DB_YML"
  # Exactly one permissions: key — a job-level grant would be drift too, since the
  # reusable-call job must not carry one.
  [ "$(grep -cE '^[[:space:]]*permissions:' "$DB_YML")" -eq 1 ]
}

@test "all required event triggers are present" {
  # Dropping any trigger silently disables that path into the stage:
  # discussion (the `needs-brief` label), schedule (the weekly Ripe sweep),
  # workflow_dispatch (manual brief or sweep).
  local trigger
  for trigger in discussion schedule workflow_dispatch; do
    _on_block | grep -qE "^  ${trigger}:$"
  done

  # schedule: must carry at least one - cron: entry (a bare key disables the sweep).
  _on_block | awk '
    /^  schedule:$/ { in_schedule=1; next }
    in_schedule && /^  [^ ]/ { exit }
    in_schedule && /^    - cron:/ { found=1 }
    END { exit !found }
  '
}

@test "the discussion trigger fires on labeled" {
  # The `needs-brief` label path only works if `discussion: labeled` events
  # arrive. Scope the check to the `discussion:` block.
  awk '/^  discussion:$/ {p=1; next} p && /^    types:/ {print; exit} p && /^  [^ ]/ {p=0}' "$DB_YML" \
    | grep -qE '\[labeled\]'
}

@test "the sweep cron runs off minute 0 and after the idea-triage slot" {
  # Header rule: keep the schedule after the idea-triage run (13:30 UTC Monday)
  # and off minute 0 (the GitHub top-of-hour pile-up). Both are allowed edits —
  # this pins only the constraints, not the exact minute.
  local cron minute hour dow
  cron="$(_on_block | awk '/^    - cron:/ {sub(/.*cron:[[:space:]]*/, ""); gsub(/["'"'"']/, ""); sub(/[[:space:]]+#.*$/, ""); print; exit}')"
  [ -n "$cron" ]
  minute="$(echo "$cron" | awk '{print $1}')"
  hour="$(echo "$cron" | awk '{print $2}')"
  dow="$(echo "$cron" | awk '{print $5}')"
  [[ "$minute" =~ ^[0-9]+$ ]]
  [[ "$hour" =~ ^[0-9]+$ ]]
  [ "$minute" -ne 0 ]
  [ "$hour" -ge 14 ]
  # Monday only (the idea-triage run is Monday 13:30 UTC); 1 or MON.
  [[ "$dow" =~ ^(1|MON)$ ]]
}

@test "workflow_dispatch exposes the optional discussion input" {
  # Manual dispatch must accept a Discussion number (empty => sweep); the
  # reusable reads it through github.event.inputs.discussion.
  _on_block | awk '/^  workflow_dispatch:$/ {p=1; next} p && /^  [^ ]/ {exit} p {print}' \
    | grep -qE '^      discussion:$'
}

@test "the reusable ref is pinned to the decision-brief stable channel, never @main or a SHA" {
  # The header forbids repointing to @main, a SHA, or a frozen @vX: releases roll
  # out by moving the channel tag centrally, never by editing callers.
  local ref; ref="$(_uses_ref)"
  [ -n "$ref" ]
  [ "$ref" = "decision-brief/v1-stable" ]
}

@test "the reusable lives in combsmith/.github-private" {
  # The reusable is hosted in the org-private automation repo (not combsmith/.github,
  # where the other stubs' reusables live). Pin the owner/repo/path.
  _job_uses | grep -qE '^    uses: combsmith/\.github-private/\.github/workflows/decision-brief-reusable\.yml@'
}

@test "the reusable uses: line carries its S7637 NOSONAR marker" {
  # Without the marker SonarCloud's githubactions:S7637 fails the Quality Gate on
  # the first-party channel ref, turning every run red.
  _job_uses | grep -qE 'uses:.*decision-brief-reusable\.yml@[^[:space:]]+[[:space:]]+# NOSONAR\(githubactions:S7637\)'
}

@test "central_ref matches the channel pinned on the uses: ref" {
  # central_ref threads the SAME channel into the central workflow dispatch (the
  # dev-lead agent_ref convention); a mismatch runs the caller against one ring
  # and Mary against another.
  local uses_ref central_ref
  uses_ref="$(_uses_ref)"
  central_ref="$(_with_value central_ref)"
  [ -n "$uses_ref" ]
  [ -n "$central_ref" ]
  [ "$uses_ref" = "$central_ref" ]
}

@test "the discussion input is read via github.event.inputs, not the inputs context" {
  # `${{ inputs.discussion }}` fails at workflow setup on the discussion/schedule
  # events (the #571 class — zero jobs, 100% failure). Pin the safe form.
  [ "$(_with_value discussion)" = "\${{ github.event.inputs.discussion }}" ]
  [ "$(_job_with | grep -cE '\$\{\{[[:space:]]*inputs\.')" -eq 0 ]
}

@test "max_briefs is a quoted positive integer" {
  # The sweep cap is a caller-tunable input, but the reusable declares it as a
  # string and bounds the sweep by it; a blank, zero or non-numeric value either
  # disables the sweep or fails input validation.
  local cap; cap="$(_with_value max_briefs)"
  [[ "$cap" =~ ^\'[1-9][0-9]*\'$ ]]
}

@test "secrets: inherit carries its S7635 NOSONAR marker" {
  # The reusable reads the org-level PAT through inherited secrets; an explicit
  # secrets map would silently drop it, and the missing marker re-fails the gate.
  grep -qE '^    secrets: inherit[[:space:]]+# NOSONAR\(githubactions:S7635\)' "$DB_YML"
}

@test "the caller declares no concurrency block" {
  # Concurrency is centralised: the central run holds one lane per idea so each
  # brief gets its own PR. A caller-level group would collapse the sweep's
  # per-idea dispatches onto one ref-keyed lane.
  run grep -E '^[[:space:]]*concurrency:' "$DB_YML"
  [ "$status" -ne 0 ]
}

@test "the stub declares exactly one job and it is the reusable call" {
  # A second job (a local redispatch bridge, a lint step, …) is logic that belongs
  # in the reusable; the stub stays a single thin call.
  local jobs
  jobs="$(awk '/^jobs:$/ {p=1; next} p && /^  [A-Za-z_][A-Za-z0-9_-]*:$/ {print}' "$DB_YML")"
  [ "$jobs" = "  decision-brief:" ]
  run awk '/^  decision-brief:$/ {p=1; next} p && /^  [^ ]/ {p=0} p && /^    (runs-on|steps):/' "$DB_YML"
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}
