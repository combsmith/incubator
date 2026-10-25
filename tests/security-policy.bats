#!/usr/bin/env bats
# Compliance regression guard for OpenSSF Scorecard Security-Policy check (issue #17):
# Validates that this repository does NOT define a local SECURITY.md stub that would
# shadow the org-wide security policy in combsmith/.github/SECURITY.md (which both
# GitHub and OpenSSF Scorecard inherit automatically to score 10/10), and that
# README.md links directly to the canonical org-wide policy.

REPO_ROOT="${BATS_TEST_DIRNAME}/.."

@test "no local SECURITY.md exists to shadow combsmith/.github/SECURITY.md (issue #17)" {
  [ ! -e "${REPO_ROOT}/SECURITY.md" ]
  [ ! -e "${REPO_ROOT}/.github/SECURITY.md" ]
  [ ! -e "${REPO_ROOT}/docs/SECURITY.md" ]
}

@test "README.md links to the org-wide security policy in combsmith/.github" {
  grep -qF 'https://github.com/combsmith/.github/blob/main/SECURITY.md' "${REPO_ROOT}/README.md"
  if grep -qF '(SECURITY.md)' "${REPO_ROOT}/README.md"; then
    return 1
  fi
}
