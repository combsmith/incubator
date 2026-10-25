#!/usr/bin/env bats
# Compliance regression guard for ci.yml concurrency-cancellation reliability (issue #190).
#
# Fleet Monitor issue #190 reported a 40.6% failure rate (13/32 runs) with 0 cancelled
# runs across rapid pull_request push bursts on a single branch. The root cause of
# zero cancellations was the top-level concurrency group key:
#
#   concurrency:
#     group: ci-${{ github.ref }}-${{ github.sha }}   # <- github.sha
#     cancel-in-progress: true
#
# Embedding ${{ github.sha }} places every commit in a distinct concurrency group,
# so `cancel-in-progress: true` never matches or cancels an earlier in-flight run on
# the same branch/PR ref. Superseded runs continue executing to completion or failure
# instead of cancelling cleanly.
#
# This guard pins the fix: ci.yml's concurrency group must be keyed by github.ref,
# must NOT contain github.sha, and must keep cancel-in-progress: true.

CI_YML="${BATS_TEST_DIRNAME}/../.github/workflows/ci.yml"

# Print the top-level `concurrency:` block — from the `concurrency:` line up to the
# next top-level (column-0) key — so assertions are scoped to it. Comment lines are
# dropped so a commented-out key can never satisfy a guard.
concurrency_block() {
  local file="${1:-$CI_YML}"
  awk '
    /^concurrency:[[:space:]]*(#.*)?$/ { f = 1; print; next }
    f && /^[A-Za-z0-9_-]/ { f = 0 }
    f { print }
  ' "$file" | grep -v '^[[:space:]]*#'
}

# The value of the concurrency `group:` key (everything after `group:`), or empty.
# An inline YAML comment (` # …`) is stripped so comment text can never satisfy a
# guard — e.g. `group: ci-static # github.ref is required` must NOT pass the
# github.ref check on the strength of the comment alone.
group_value() {
  local file="${1:-$CI_YML}"
  concurrency_block "$file" | grep -E '^[[:space:]]+group:' | head -1 \
    | sed -E 's/^[[:space:]]+group:[[:space:]]*//; s/[[:space:]]+#.*$//; s/[[:space:]]+$//'
}

@test "ci.yml exists at the expected path" {
  [ -f "$CI_YML" ]
}

@test "ci.yml declares a top-level concurrency block" {
  grep -qE '^concurrency:[[:space:]]*(#.*)?$' "$CI_YML"
}

@test "concurrency block defines a group" {
  local group
  group="$(group_value)"
  [ -n "$group" ] || { echo "ci.yml concurrency has no 'group:' key"; return 1; }
}

@test "concurrency group is keyed by github.ref" {
  local group
  group="$(group_value)"
  printf '%s\n' "$group" | grep -qE 'github\.ref' \
    || { echo "concurrency group must be keyed by github.ref so pushes to a ref share a group: $group"; return 1; }
}

@test "concurrency group does not embed github.sha (would defeat cancel-in-progress)" {
  local group
  group="$(group_value)"
  ! printf '%s\n' "$group" | grep -qE 'github\.sha' \
    || { echo "concurrency group must NOT contain github.sha: $group"; return 1; }
}

@test "cancel-in-progress is enabled so a new push supersedes the stale run" {
  concurrency_block | grep -qE '^[[:space:]]+cancel-in-progress:[[:space:]]*(true|"true"|'\''true'\'')([[:space:]]*|[[:space:]]+#.*)$' \
    || { echo "concurrency must set cancel-in-progress: true"; return 1; }
}

@test "group_value strips inline YAML comments so comments cannot satisfy guards" {
  local fixture="${BATS_TEST_TMPDIR}/ci-inline-comment.yml"
  cat > "$fixture" <<'EOF'
concurrency:
  group: ci-static # github.ref would be ignored here
  cancel-in-progress: true
jobs:
  build:
    runs-on: ubuntu-latest
EOF
  local group
  group="$(group_value "$fixture")"
  [ "$group" = "ci-static" ]
  if printf '%s\n' "$group" | grep -qE 'github\.ref'; then
    echo "inline comment leaked into group_value: $group"
    return 1
  fi
}

@test "AGENTS.md and copilot-instructions.md document DemandRadar pre-commit lint/format/typecheck commands" {
  local agents_md="${BATS_TEST_DIRNAME}/../AGENTS.md"
  local copilot_md="${BATS_TEST_DIRNAME}/../.github/copilot-instructions.md"
  for doc in "$agents_md" "$copilot_md"; do
    [ -f "$doc" ]
    grep -qF 'pocs/demand-radar' "$doc"
    grep -qF 'ruff check .' "$doc"
    grep -qF 'ruff format --check .' "$doc"
    grep -qF 'mypy --ignore-missing-imports .' "$doc"
  done
}
