#!/usr/bin/env bats
# Compliance regression guard for ci.yml job-level timeout backstops (issue #190).
#
# Fleet Monitor issue #190 reported elevated p95 duration (412s, with individual runs
# exceeding 9 minutes) alongside step failures in .github/workflows/ci.yml.
#
# Prior remediations (#124 network-fetch retries, #126 checkout retries) only retry
# operations that *error* (`outcome == 'failure'`). Neither bounds an operation that
# *hangs* (stalled git/pip/apt/curl/gitleaks socket or wedged GitHub-hosted runner):
# without a job-level `timeout-minutes` backstop, a stalled job sits until GitHub's
# 6-hour default timeout expires.
#
# This guard pins the fix: every job in `.github/workflows/ci.yml` must declare an
# explicit job-level `timeout-minutes` integer in [1, 60].

CI_YML="${BATS_TEST_DIRNAME}/../.github/workflows/ci.yml"

# Extract the YAML slice for a single job under `jobs:` (2-space indent for job key,
# 4-space indent for job-level attributes). Supports unquoted, double-quoted, and
# single-quoted YAML job keys. Stops at the next 2-space job key or top-level key.
job_block() {
  local job="$1"
  local file="${2:-$CI_YML}"
  awk -v job="$job" '
    /^jobs:[[:space:]]*(#.*)?$/ { in_jobs = 1; next }
    in_jobs && /^[^[:space:]#]/ { in_jobs = 0 }
    in_jobs && $0 ~ "^  (\"|\x27)?" job "(\"|\x27)?:[[:space:]]*(#.*)?$" { in_job = 1; print; next }
    in_job && /^  ("|\x27)?[A-Za-z0-9_-]+("|\x27)?:[[:space:]]*(#.*)?$/ { in_job = 0 }
    in_job { print }
  ' "$file"
}

# List every job key declared directly under `jobs:` (2-space indent), stripping
# optional surrounding single or double quotes.
list_jobs() {
  local file="${1:-$CI_YML}"
  awk '
    /^jobs:[[:space:]]*(#.*)?$/ { in_jobs = 1; next }
    in_jobs && /^[^[:space:]#]/ { in_jobs = 0 }
    in_jobs && /^  ("|\x27)?[A-Za-z0-9_-]+("|\x27)?:[[:space:]]*(#.*)?$/ {
      line = $0
      sub(/^  ("|\x27)?/, "", line)
      sub(/("|\x27)?:.*$/, "", line)
      print line
    }
  ' "$file"
}

# Assert that a given job block in a workflow file declares a 4-space job-level
# `timeout-minutes: <int>` with 1 <= int <= 60.
assert_job_has_bounded_timeout() {
  local job="$1"
  local file="${2:-$CI_YML}"
  local block line val

  block="$(job_block "$job" "$file")"
  [ -n "$block" ] || { echo "job '$job' not found in $file"; return 1; }

  line="$(printf '%s\n' "$block" | grep -E '^    timeout-minutes:[[:space:]]*[0-9]+([[:space:]]*(#.*)?)?$' | head -n1)"
  [ -n "$line" ] || {
    echo "job '$job' in $file is missing a job-level 'timeout-minutes: <int>' attribute"
    return 1
  }

  val="$(printf '%s\n' "$line" | sed -E 's/^    timeout-minutes:[[:space:]]*([0-9]+).*$/\1/')"
  if [ "$val" -lt 1 ] || [ "$val" -gt 60 ]; then
    echo "job '$job' timeout-minutes=$val is outside bounded range [1, 60]"
    return 1
  fi
}

@test "ci.yml exists and declares the expected jobs" {
  [ -f "$CI_YML" ]
  local jobs
  jobs="$(list_jobs)"
  printf '%s\n' "$jobs" | grep -qx 'build-and-test'
  printf '%s\n' "$jobs" | grep -qx 'secret-scan'
  printf '%s\n' "$jobs" | grep -qx 'coverage'
}

@test "build-and-test job declares a bounded job-level timeout-minutes (1..60)" {
  assert_job_has_bounded_timeout "build-and-test"
}

@test "secret-scan job declares a bounded job-level timeout-minutes (1..60)" {
  assert_job_has_bounded_timeout "secret-scan"
}

@test "coverage job declares a bounded job-level timeout-minutes (1..60)" {
  assert_job_has_bounded_timeout "coverage"
}

@test "every job discovered in ci.yml declares a bounded job-level timeout-minutes" {
  local jobs job count=0
  jobs="$(list_jobs)"
  [ -n "$jobs" ]
  while IFS= read -r job; do
    [ -n "$job" ] || continue
    count=$((count + 1))
    assert_job_has_bounded_timeout "$job"
  done <<< "$jobs"
  [ "$count" -ge 3 ]
}

@test "job_block does not treat a step-level timeout-minutes as satisfying the job-level backstop" {
  local fixture="${BATS_TEST_TMPDIR}/step-only.yml"
  cat > "$fixture" <<'EOF'
name: fixture
on: push
jobs:
  step-only-job:
    runs-on: ubuntu-latest
    steps:
      - name: step with timeout
        timeout-minutes: 5
        run: echo hi
EOF
  run assert_job_has_bounded_timeout "step-only-job" "$fixture"
  [ "$status" -ne 0 ]
}

@test "list_jobs and job_block recognize quoted job keys and reject missing timeout-minutes" {
  local fixture="${BATS_TEST_TMPDIR}/quoted-jobs.yml"
  cat > "$fixture" <<'EOF'
name: fixture
on: push
jobs:
  "double-quoted-ok":
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - run: echo ok
  'single-quoted-missing':
    runs-on: ubuntu-latest
    steps:
      - run: echo missing
EOF
  local jobs
  jobs="$(list_jobs "$fixture")"
  printf '%s\n' "$jobs" | grep -qx 'double-quoted-ok'
  printf '%s\n' "$jobs" | grep -qx 'single-quoted-missing'

  assert_job_has_bounded_timeout "double-quoted-ok" "$fixture"
  run assert_job_has_bounded_timeout "single-quoted-missing" "$fixture"
  [ "$status" -ne 0 ]
}

@test "ci.yml remains valid YAML with no duplicate keys and integer timeout-minutes on all jobs" {
  if ! command -v python3 >/dev/null 2>&1 || ! python3 -c "import yaml" >/dev/null 2>&1; then
    skip "python3 with PyYAML not installed"
  fi
  python3 - "$CI_YML" <<'PY'
import sys
import yaml


class StrictSafeLoader(yaml.SafeLoader):
    pass


def _construct_mapping(loader, node, deep=False):
    loader.flatten_mapping(node)
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"found duplicate key {key!r}",
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


StrictSafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_mapping,
)

with open(sys.argv[1], encoding="utf-8") as fh:
    doc = yaml.load(fh, Loader=StrictSafeLoader)

jobs = doc.get("jobs") or {}
assert len(jobs) >= 3, f"expected >=3 jobs, got {list(jobs)}"
for name, spec in jobs.items():
    tm = spec.get("timeout-minutes")
    assert isinstance(tm, int) and not isinstance(tm, bool), (
        f"job {name!r} missing integer timeout-minutes: {tm!r}"
    )
    assert 1 <= tm <= 60, f"job {name!r} timeout-minutes={tm} out of [1, 60]"
PY
}
