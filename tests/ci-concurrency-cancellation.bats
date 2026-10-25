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
# so `cancel-in-progress` never matches or cancels an earlier in-flight run on the
# same branch/PR ref. Superseded runs continue executing to completion or failure
# instead of cancelling cleanly.
#
# This guard pins the fix: ci.yml's concurrency group must be `ci-${{ github.ref }}`
# (keyed by github.ref and free of per-commit/per-run tokens like .sha, run_id, or
# run_attempt), and cancel-in-progress must supersede non-main branch/PR runs while
# allowing main runs to complete.

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

# Assert that a workflow file's concurrency group references the exact `github.ref`
# property (and not a prefix match like `github.ref_type` or `github.ref_name`).
assert_group_keyed_by_github_ref() {
  local file="${1:-$CI_YML}"
  local group
  group="$(group_value "$file")"
  printf '%s\n' "$group" | grep -qE 'github\.ref([^A-Za-z0-9_]|$)' \
    || { echo "concurrency group must be keyed by github.ref so pushes to a ref share a group: $group"; return 1; }
}

# Assert that a workflow file's concurrency group does not embed any per-commit or
# per-run identifier (`github.sha`, `*.sha`, `run_id`, `run_attempt`, `run_number`)
# that would place each push in a distinct concurrency group.
assert_group_not_per_commit_or_run() {
  local file="${1:-$CI_YML}"
  local group
  group="$(group_value "$file")"
  if printf '%s\n' "$group" | grep -qE '(\.sha|run_id|run_attempt|run_number)([^A-Za-z0-9_]|$)'; then
    echo "concurrency group must NOT contain per-commit/per-run tokens (.sha, run_id, run_attempt, run_number): $group"
    return 1
  fi
}

@test "ci.yml exists at the expected path" {
  [ -f "$CI_YML" ]
}

@test "ci.yml declares a top-level concurrency block" {
  grep -qE '^concurrency:[[:space:]]*(#.*)?$' "$CI_YML"
}

@test "concurrency block defines the canonical ci-\${{ github.ref }} group" {
  local group
  group="$(group_value)"
  [ "$group" = "ci-\${{ github.ref }}" ] \
    || { echo "expected concurrency group 'ci-\${{ github.ref }}', got: $group"; return 1; }
}

@test "concurrency group is keyed by github.ref" {
  assert_group_keyed_by_github_ref "$CI_YML"
}

@test "concurrency group check rejects github.ref_type substring" {
  local fixture="${BATS_TEST_TMPDIR}/ci-ref-type.yml"
  cat > "$fixture" <<'EOF'
concurrency:
  group: ci-${{ github.ref_type }}
  cancel-in-progress: true
jobs:
  build:
    runs-on: ubuntu-latest
EOF
  run assert_group_keyed_by_github_ref "$fixture"
  [ "$status" -ne 0 ]
}

@test "concurrency group does not embed github.sha or other per-commit/per-run tokens" {
  assert_group_not_per_commit_or_run "$CI_YML"
}

@test "concurrency group denylist rejects head.sha and run_id tokens" {
  local fixture_sha="${BATS_TEST_TMPDIR}/ci-head-sha.yml"
  cat > "$fixture_sha" <<'EOF'
concurrency:
  group: ci-${{ github.ref }}-${{ github.event.pull_request.head.sha }}
  cancel-in-progress: true
jobs:
  build:
    runs-on: ubuntu-latest
EOF
  run assert_group_not_per_commit_or_run "$fixture_sha"
  [ "$status" -ne 0 ]

  local fixture_run="${BATS_TEST_TMPDIR}/ci-run-id.yml"
  cat > "$fixture_run" <<'EOF'
concurrency:
  group: ci-${{ github.ref }}-${{ github.run_id }}
  cancel-in-progress: true
jobs:
  build:
    runs-on: ubuntu-latest
EOF
  run assert_group_not_per_commit_or_run "$fixture_run"
  [ "$status" -ne 0 ]
}

@test "cancel-in-progress cancels PR/branch runs while protecting refs/heads/main" {
  concurrency_block | grep -qE "^[[:space:]]+cancel-in-progress:[[:space:]]*\\$\\{\\{[[:space:]]*github\\.ref[[:space:]]*!=[[:space:]]*'refs/heads/main'[[:space:]]*\\}\\}([[:space:]]*|[[:space:]]+#.*)$" \
    || { echo "concurrency must set cancel-in-progress: \${{ github.ref != 'refs/heads/main' }}"; return 1; }
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
  if printf '%s\n' "$group" | grep -qE 'github\.ref([^A-Za-z0-9_]|$)'; then
    echo "inline comment leaked into group_value: $group"
    return 1
  fi
}

@test "AGENTS.md and copilot-instructions.md document the exact CI commands from ci.yml" {
  local agents_md="${BATS_TEST_DIRNAME}/../AGENTS.md"
  local copilot_md="${BATS_TEST_DIRNAME}/../.github/copilot-instructions.md"
  local cmd

  # Every DemandRadar command documented in AGENTS.md / copilot-instructions.md must
  # also exist verbatim in .github/workflows/ci.yml so docs and CI never drift.
  for cmd in \
    'python3 -m pip install -q --only-binary :all: --require-hashes -r requirements-ci.txt' \
    'ruff check .' \
    'ruff format --check .' \
    'mypy --ignore-missing-imports .' \
    'python3 -m pytest tests/ -q --tb=short' \
    'python3 -m pytest tests/ --cov=. --cov-report=xml:coverage.xml --cov-report=term-missing --cov-fail-under=80'
  do
    grep -qF "$cmd" "$CI_YML" \
      || { echo "ci.yml no longer contains expected command: $cmd"; return 1; }
    for doc in "$agents_md" "$copilot_md"; do
      [ -f "$doc" ]
      grep -qF "$cmd" "$doc" \
        || { echo "$doc is missing CI command: $cmd"; return 1; }
    done
  done

  # Both docs must also document the PyYAML install step alongside bats tests/*.bats.
  for doc in "$agents_md" "$copilot_md"; do
    grep -qF 'python3 -m pip install -q pyyaml==6.0.2' "$doc"
    grep -qF 'bats tests/*.bats' "$doc"
  done
}
