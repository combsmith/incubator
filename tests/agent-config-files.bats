#!/usr/bin/env bats
# Compliance regression guard for repository agent instruction files
# (combsmith/.github -> standards/agent-standards.md):
# Validates that AGENTS.md, CLAUDE.md, and GEMINI.md exist, end with a trailing
# newline (POSIX text file compliance), cross-reference AGENTS.md and
# combsmith/.github/AGENTS.md, and contain no stale petry-projects references.

REPO_ROOT="${BATS_TEST_DIRNAME}/.."

validate_agent_config_dir() {
  local root_dir="${1:-$REPO_ROOT}"
  python3 - "$root_dir" << 'PY'
from pathlib import Path
import sys

root = Path(sys.argv[1])
required = ("AGENTS.md", "CLAUDE.md", "GEMINI.md")

for name in required:
    path = root / name
    if not path.is_file():
        sys.exit(f"missing required agent config file: {name}")
    raw = path.read_bytes()
    if not raw:
        sys.exit(f"agent config file is empty: {name}")
    if not raw.endswith(b"\n"):
        sys.exit(f"{name} must end with a trailing newline")
    text = raw.decode("utf-8")
    if "petry-projects" in text.lower():
        sys.exit(f"{name} contains stale 'petry-projects' org reference")

claude_text = (root / "CLAUDE.md").read_text(encoding="utf-8")
if "agents.md" not in claude_text.lower():
    sys.exit("CLAUDE.md must reference AGENTS.md")

gemini_text = (root / "GEMINI.md").read_text(encoding="utf-8")
if "agents.md" not in gemini_text.lower():
    sys.exit("GEMINI.md must reference AGENTS.md")
if "https://github.com/combsmith/.github/blob/main/AGENTS.md" not in gemini_text:
    sys.exit("GEMINI.md must reference combsmith/.github/blob/main/AGENTS.md")

agents_text = (root / "AGENTS.md").read_text(encoding="utf-8")
if "https://github.com/combsmith/.github/blob/main/AGENTS.md" not in agents_text:
    sys.exit("AGENTS.md must reference combsmith/.github/blob/main/AGENTS.md")
PY
}

@test "AGENTS.md, CLAUDE.md, and GEMINI.md exist and are non-empty" {
  [ -s "${REPO_ROOT}/AGENTS.md" ]
  [ -s "${REPO_ROOT}/CLAUDE.md" ]
  [ -s "${REPO_ROOT}/GEMINI.md" ]
}

@test "AGENTS.md, CLAUDE.md, and GEMINI.md end with a trailing newline" {
  for f in AGENTS.md CLAUDE.md GEMINI.md; do
    last_byte="$(tail -c 1 "${REPO_ROOT}/${f}" | od -An -tx1 | tr -d ' \n')"
    [ "${last_byte}" = "0a" ]
  done
}

@test "CLAUDE.md and GEMINI.md reference AGENTS.md" {
  grep -qiF 'AGENTS.md' "${REPO_ROOT}/CLAUDE.md"
  grep -qiF 'AGENTS.md' "${REPO_ROOT}/GEMINI.md"
}

@test "AGENTS.md and GEMINI.md reference combsmith/.github/AGENTS.md" {
  grep -qF 'https://github.com/combsmith/.github/blob/main/AGENTS.md' "${REPO_ROOT}/AGENTS.md"
  grep -qF 'https://github.com/combsmith/.github/blob/main/AGENTS.md' "${REPO_ROOT}/GEMINI.md"
}

@test "agent instruction files pass full validation and contain no stale petry-projects references" {
  run validate_agent_config_dir "${REPO_ROOT}"
  [ "$status" -eq 0 ]
}

@test "validate_agent_config_dir rejects missing trailing newline and stale petry-projects reference" {
  local tmp_dir
  tmp_dir="$(mktemp -d)"
  cp "${REPO_ROOT}/AGENTS.md" "${REPO_ROOT}/CLAUDE.md" "${REPO_ROOT}/GEMINI.md" "${tmp_dir}/"

  # 1. Missing trailing newline on CLAUDE.md fails closed
  printf 'See [AGENTS.md](./AGENTS.md).' > "${tmp_dir}/CLAUDE.md"
  run validate_agent_config_dir "${tmp_dir}"
  [ "$status" -ne 0 ]
  [[ "$output" == *"CLAUDE.md must end with a trailing newline"* ]]

  # 2. Stale petry-projects org reference in GEMINI.md fails closed
  cp "${REPO_ROOT}/CLAUDE.md" "${tmp_dir}/CLAUDE.md"
  printf '# GEMINI.md\nSee [AGENTS.md](AGENTS.md) and https://github.com/petry-projects/.github/blob/main/AGENTS.md\n' > "${tmp_dir}/GEMINI.md"
  run validate_agent_config_dir "${tmp_dir}"
  [ "$status" -ne 0 ]
  [[ "$output" == *"stale 'petry-projects'"* ]]

  rm -rf "${tmp_dir}"
}
