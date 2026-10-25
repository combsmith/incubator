#!/usr/bin/env bats
# Compliance regression guard for the pr-quality ruleset Standard and OpenSSF
# Scorecard Branch-Protection check (issue #13):
# (combsmith/.github -> standards/github-settings.md#pr-quality--standard-ruleset-all-repositories,
#  codified locally at standards/rulesets/pr-quality.json).
#
# OpenSSF Scorecard evaluates Branch-Protection using a strict tiered rubric where
# Tier 1 (3/10 points) requires both:
#   1. Preventing branch deletions (`deletion` rule in GitHub branch rulesets)
#   2. Preventing force pushes (`non_fast_forward` rule in GitHub branch rulesets)
#
# Because Scorecard requires each tier to be 100% satisfied before awarding credit
# for higher tiers, omitting `deletion` and `non_fast_forward` caused Tier 1 to fail
# and discarded all higher-tier points, resulting in a 0/10 score on issue #13.
#
# Relationship to `combsmith/.github:standards/rulesets/pr-quality.json`:
#   - `standards/github-settings.md` (§ `pr-quality — Standard Ruleset`) mandates
#     `Allow force pushes: No` (`non_fast_forward`) and `Allow deletions: No`
#     (`deletion`), while `combsmith/.github:standards/rulesets/pr-quality.json`
#     currently codifies only the `pull_request` rule.
#   - This repo's `standards/rulesets/pr-quality.json` codifies the full 3-rule
#     set (`pull_request`, `deletion`, `non_fast_forward`) plus
#     `require_extra_approval_for_unattributed_changes: true` enforced on live
#     ruleset `18834182` (leaving `required_reviewers: []` and
#     `dismissal_restriction` as API-managed defaults). Note that running
#     `scripts/apply-rulesets.sh` from `combsmith/.github` before upstream
#     `combsmith/.github:standards/rulesets/pr-quality.json` adds `deletion` and
#     `non_fast_forward` would full-replace the live ruleset and strip those two
#     rules; re-apply `standards/rulesets/pr-quality.json` if that occurs.
#
# Execution scope (CI vs. local):
#   - CI (`coverage` job in `.github/workflows/ci.yml`) runs with
#     `persist-credentials: false` and `permissions: {}` without a `GH_TOKEN` /
#     `GITHUB_TOKEN`, so CI exercises the codified `standards/rulesets/pr-quality.json`
#     and negative fixtures; the live GitHub API check is local/credentialed-only
#     (unless `REQUIRE_LIVE_RULESET=1` is set in a job with a ruleset-read token).

RULESET_JSON="${BATS_TEST_DIRNAME}/../standards/rulesets/pr-quality.json"
REPO_SLUG="${GITHUB_REPOSITORY:-combsmith/incubator}"

# Read one value from the pull_request rule's parameters as its JSON literal.
# Uses python3 (installed in CI for the compliance job) so no jq dependency is required.
pr_param() {
  local file="${2:-$RULESET_JSON}"
  python3 - "$file" "$1" << 'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)
rule = next(r for r in data["rules"] if isinstance(r, dict) and r.get("type") == "pull_request")
print(json.dumps(rule["parameters"][sys.argv[2]], separators=(",", ":")))
PY
}

# Validate a pr-quality ruleset JSON file against the org standard and OpenSSF
# Scorecard Tier 1 Branch-Protection requirements (issue #13).
# Fails closed (non-zero exit with diagnostic message) on any schema or policy drift.
validate_pr_quality_ruleset() {
  local file="${1:-$RULESET_JSON}"
  python3 - "$file" << 'PY'
import json
import sys

path = sys.argv[1]
try:
    with open(path, encoding="utf-8") as fh:
        ruleset = json.load(fh)
except Exception as exc:
    sys.exit(f"failed to parse JSON from {path}: {exc}")

if not isinstance(ruleset, dict):
    sys.exit("ruleset root must be a JSON object")

if ruleset.get("name") != "pr-quality":
    sys.exit(f"name must be 'pr-quality', got {ruleset.get('name')!r}")

if ruleset.get("target") != "branch":
    sys.exit(f"target must be 'branch', got {ruleset.get('target')!r}")

if ruleset.get("enforcement") != "active":
    sys.exit(f"enforcement must be 'active', got {ruleset.get('enforcement')!r}")

conditions = ruleset.get("conditions")
if not isinstance(conditions, dict):
    sys.exit("conditions must be an object")

ref_name = conditions.get("ref_name")
if not isinstance(ref_name, dict):
    sys.exit("conditions.ref_name must be an object")

include = ref_name.get("include")
exclude = ref_name.get("exclude")
if not isinstance(include, list) or include != ["~DEFAULT_BRANCH"]:
    sys.exit("conditions.ref_name.include must equal ['~DEFAULT_BRANCH']")
if not isinstance(exclude, list) or len(exclude) != 0:
    sys.exit("conditions.ref_name.exclude must be an empty list []")

rules = ruleset.get("rules")
if not isinstance(rules, list) or not rules:
    sys.exit("rules must be a non-empty list")

rule_types = []
for rule in rules:
    if not isinstance(rule, dict) or not isinstance(rule.get("type"), str):
        sys.exit("every entry in rules must be an object with a string 'type'")
    rule_types.append(rule["type"])

if len(rule_types) != len(set(rule_types)):
    sys.exit(f"duplicate rule types are not allowed: {rule_types}")

expected_rule_types = {"pull_request", "deletion", "non_fast_forward"}
for required_type in ("pull_request", "deletion", "non_fast_forward"):
    if required_type not in rule_types:
        sys.exit(f"missing required rule type {required_type!r} in {rule_types}")
if set(rule_types) != expected_rule_types:
    sys.exit(f"unexpected rule types in ruleset: got {sorted(rule_types)}, expected {sorted(expected_rule_types)}")

pr_rules = [r for r in rules if r.get("type") == "pull_request"]
if len(pr_rules) != 1:
    sys.exit("exactly one pull_request rule is required")

params = pr_rules[0].get("parameters")
if not isinstance(params, dict):
    sys.exit("pull_request rule parameters must be an object")

review_count = params.get("required_approving_review_count")
if isinstance(review_count, bool) or not isinstance(review_count, int) or review_count != 1:
    sys.exit("required_approving_review_count must be the integer 1")

for bool_key in (
    "require_code_owner_review",
    "required_review_thread_resolution",
    "dismiss_stale_reviews_on_push",
    "require_last_push_approval",
    "require_extra_approval_for_unattributed_changes",
):
    if params.get(bool_key) is not True:
        sys.exit(f"pull_request parameter {bool_key} must be true")

if params.get("allowed_merge_methods") != ["squash"]:
    sys.exit("allowed_merge_methods must equal ['squash']")

bypass_actors = ruleset.get("bypass_actors")
if not isinstance(bypass_actors, list):
    sys.exit("bypass_actors must be a list")

normalized_actors = []
for actor in bypass_actors:
    if not isinstance(actor, dict):
        sys.exit("every bypass_actors entry must be an object")
    normalized_actors.append(
        (actor.get("actor_type"), actor.get("actor_id"), actor.get("bypass_mode"))
    )

expected_actors = {
    ("OrganizationAdmin", None, "always"),
    ("Integration", 3167543, "always"),
}
if len(normalized_actors) != 2 or set(normalized_actors) != expected_actors:
    sys.exit(
        f"bypass_actors must equal exactly OrganizationAdmin/always and Integration 3167543/always, got {normalized_actors}"
    )
PY
}

@test "codified pr-quality ruleset exists" {
  [ -f "$RULESET_JSON" ]
}

@test "codified pr-quality ruleset is valid JSON" {
  python3 -c 'import json,sys
with open(sys.argv[1], encoding="utf-8") as f:
    d = json.load(f)
assert isinstance(d, dict)' "$RULESET_JSON"
}

@test "ruleset targets the default branch with active enforcement" {
  run python3 -c 'import json,sys
with open(sys.argv[1], encoding="utf-8") as f:
    d = json.load(f)
print(json.dumps({"target": d["target"], "enforcement": d["enforcement"], "include": d["conditions"]["ref_name"]["include"], "exclude": d["conditions"]["ref_name"]["exclude"]}, separators=(",", ":")))' "$RULESET_JSON"
  [ "$status" -eq 0 ]
  [ "$output" = '{"target":"branch","enforcement":"active","include":["~DEFAULT_BRANCH"],"exclude":[]}' ]
}

@test "require_last_push_approval is enabled" {
  [ "$(pr_param require_last_push_approval)" = "true" ]
}

@test "required_approving_review_count is 1" {
  [ "$(pr_param required_approving_review_count)" = "1" ]
}

@test "require_code_owner_review is enabled" {
  [ "$(pr_param require_code_owner_review)" = "true" ]
}

@test "required_review_thread_resolution is enabled" {
  [ "$(pr_param required_review_thread_resolution)" = "true" ]
}

@test "dismiss_stale_reviews_on_push is enabled" {
  [ "$(pr_param dismiss_stale_reviews_on_push)" = "true" ]
}

@test "require_extra_approval_for_unattributed_changes is enabled" {
  [ "$(pr_param require_extra_approval_for_unattributed_changes)" = "true" ]
}

@test "allowed_merge_methods is squash-only" {
  [ "$(pr_param allowed_merge_methods)" = '["squash"]' ]
}

@test "ruleset enforces deletion and non_fast_forward rules for OpenSSF Scorecard Tier 1 (issue #13)" {
  run python3 -c 'import json,sys
with open(sys.argv[1], encoding="utf-8") as f:
    d = json.load(f)
types = sorted(r["type"] for r in d["rules"])
print(json.dumps(types, separators=(",", ":")))' "$RULESET_JSON"
  [ "$status" -eq 0 ]
  [ "$output" = '["deletion","non_fast_forward","pull_request"]' ]
}

@test "ruleset defines the exact bypass_actors set (OrganizationAdmin and Integration 3167543)" {
  run python3 -c 'import json,sys
with open(sys.argv[1], encoding="utf-8") as f:
    d = json.load(f)
actors = sorted((a.get("actor_type"), a.get("actor_id"), a.get("bypass_mode")) for a in d["bypass_actors"])
print(json.dumps(actors, separators=(",", ":")))' "$RULESET_JSON"
  [ "$status" -eq 0 ]
  [ "$output" = '[["Integration",3167543,"always"],["OrganizationAdmin",null,"always"]]' ]
}

@test "validate_pr_quality_ruleset passes on the codified pr-quality.json" {
  run validate_pr_quality_ruleset "$RULESET_JSON"
  [ "$status" -eq 0 ]
}

@test "validate_pr_quality_ruleset rejects missing deletion, missing non_fast_forward, or extra rule types" {
  local missing_deletion="${BATS_TEST_TMPDIR}/missing-deletion.json"
  python3 - "$RULESET_JSON" "$missing_deletion" << 'PY'
import json, sys
with open(sys.argv[1], encoding="utf-8") as f:
    d = json.load(f)
d["rules"] = [r for r in d["rules"] if r.get("type") != "deletion"]
with open(sys.argv[2], "w", encoding="utf-8") as f:
    json.dump(d, f)
PY
  run validate_pr_quality_ruleset "$missing_deletion"
  [ "$status" -ne 0 ]
  [[ "$output" == *"missing required rule type 'deletion'"* ]]

  local missing_nff="${BATS_TEST_TMPDIR}/missing-nff.json"
  python3 - "$RULESET_JSON" "$missing_nff" << 'PY'
import json, sys
with open(sys.argv[1], encoding="utf-8") as f:
    d = json.load(f)
d["rules"] = [r for r in d["rules"] if r.get("type") != "non_fast_forward"]
with open(sys.argv[2], "w", encoding="utf-8") as f:
    json.dump(d, f)
PY
  run validate_pr_quality_ruleset "$missing_nff"
  [ "$status" -ne 0 ]
  [[ "$output" == *"missing required rule type 'non_fast_forward'"* ]]

  local extra_rule="${BATS_TEST_TMPDIR}/extra-rule.json"
  python3 - "$RULESET_JSON" "$extra_rule" << 'PY'
import json, sys
with open(sys.argv[1], encoding="utf-8") as f:
    d = json.load(f)
d["rules"].append({"type": "required_linear_history"})
with open(sys.argv[2], "w", encoding="utf-8") as f:
    json.dump(d, f)
PY
  run validate_pr_quality_ruleset "$extra_rule"
  [ "$status" -ne 0 ]
  [[ "$output" == *"unexpected rule types in ruleset"* ]]
}

@test "validate_pr_quality_ruleset rejects non-active enforcement, non-branch target, or excluded default branch" {
  local disabled_rs="${BATS_TEST_TMPDIR}/disabled.json"
  python3 - "$RULESET_JSON" "$disabled_rs" << 'PY'
import json, sys
with open(sys.argv[1], encoding="utf-8") as f:
    d = json.load(f)
d["enforcement"] = "evaluate"
with open(sys.argv[2], "w", encoding="utf-8") as f:
    json.dump(d, f)
PY
  run validate_pr_quality_ruleset "$disabled_rs"
  [ "$status" -ne 0 ]
  [[ "$output" == *"enforcement must be 'active'"* ]]

  local wrong_target="${BATS_TEST_TMPDIR}/wrong-target.json"
  python3 - "$RULESET_JSON" "$wrong_target" << 'PY'
import json, sys
with open(sys.argv[1], encoding="utf-8") as f:
    d = json.load(f)
d["target"] = "tag"
with open(sys.argv[2], "w", encoding="utf-8") as f:
    json.dump(d, f)
PY
  run validate_pr_quality_ruleset "$wrong_target"
  [ "$status" -ne 0 ]
  [[ "$output" == *"target must be 'branch'"* ]]

  local excluded_main="${BATS_TEST_TMPDIR}/excluded-main.json"
  python3 - "$RULESET_JSON" "$excluded_main" << 'PY'
import json, sys
with open(sys.argv[1], encoding="utf-8") as f:
    d = json.load(f)
d["conditions"]["ref_name"]["exclude"] = ["refs/heads/main"]
with open(sys.argv[2], "w", encoding="utf-8") as f:
    json.dump(d, f)
PY
  run validate_pr_quality_ruleset "$excluded_main"
  [ "$status" -ne 0 ]
  [[ "$output" == *"conditions.ref_name.exclude must be an empty list"* ]]
}

@test "validate_pr_quality_ruleset rejects boolean or non-1 review count, duplicate rules, missing or extra bypass actors" {
  local bool_count="${BATS_TEST_TMPDIR}/bool-count.json"
  python3 - "$RULESET_JSON" "$bool_count" << 'PY'
import json, sys
with open(sys.argv[1], encoding="utf-8") as f:
    d = json.load(f)
for r in d["rules"]:
    if r.get("type") == "pull_request":
        r["parameters"]["required_approving_review_count"] = True
with open(sys.argv[2], "w", encoding="utf-8") as f:
    json.dump(d, f)
PY
  run validate_pr_quality_ruleset "$bool_count"
  [ "$status" -ne 0 ]
  [[ "$output" == *"required_approving_review_count must be the integer 1"* ]]

  local two_count="${BATS_TEST_TMPDIR}/two-count.json"
  python3 - "$RULESET_JSON" "$two_count" << 'PY'
import json, sys
with open(sys.argv[1], encoding="utf-8") as f:
    d = json.load(f)
for r in d["rules"]:
    if r.get("type") == "pull_request":
        r["parameters"]["required_approving_review_count"] = 2
with open(sys.argv[2], "w", encoding="utf-8") as f:
    json.dump(d, f)
PY
  run validate_pr_quality_ruleset "$two_count"
  [ "$status" -ne 0 ]
  [[ "$output" == *"required_approving_review_count must be the integer 1"* ]]

  local dup_rules="${BATS_TEST_TMPDIR}/dup-rules.json"
  python3 - "$RULESET_JSON" "$dup_rules" << 'PY'
import json, sys
with open(sys.argv[1], encoding="utf-8") as f:
    d = json.load(f)
d["rules"].append({"type": "deletion"})
with open(sys.argv[2], "w", encoding="utf-8") as f:
    json.dump(d, f)
PY
  run validate_pr_quality_ruleset "$dup_rules"
  [ "$status" -ne 0 ]
  [[ "$output" == *"duplicate rule types are not allowed"* ]]

  local missing_bypass="${BATS_TEST_TMPDIR}/missing-bypass.json"
  python3 - "$RULESET_JSON" "$missing_bypass" << 'PY'
import json, sys
with open(sys.argv[1], encoding="utf-8") as f:
    d = json.load(f)
d["bypass_actors"] = []
with open(sys.argv[2], "w", encoding="utf-8") as f:
    json.dump(d, f)
PY
  run validate_pr_quality_ruleset "$missing_bypass"
  [ "$status" -ne 0 ]
  [[ "$output" == *"bypass_actors must equal exactly OrganizationAdmin/always and Integration 3167543/always"* ]]

  local extra_bypass="${BATS_TEST_TMPDIR}/extra-bypass.json"
  python3 - "$RULESET_JSON" "$extra_bypass" << 'PY'
import json, sys
with open(sys.argv[1], encoding="utf-8") as f:
    d = json.load(f)
d["bypass_actors"].append({"actor_id": 5, "actor_type": "RepositoryRole", "bypass_mode": "always"})
with open(sys.argv[2], "w", encoding="utf-8") as f:
    json.dump(d, f)
PY
  run validate_pr_quality_ruleset "$extra_bypass"
  [ "$status" -ne 0 ]
  [[ "$output" == *"bypass_actors must equal exactly OrganizationAdmin/always and Integration 3167543/always"* ]]
}

@test "live GitHub pr-quality ruleset on ${REPO_SLUG} enforces deletion and non_fast_forward (local/credentialed check, issue #13)" {
  if ! command -v gh >/dev/null 2>&1; then
    skip "gh CLI is not installed"
  fi
  if [ -z "${GH_TOKEN:-}${GITHUB_TOKEN:-}" ] && ! gh auth status >/dev/null 2>&1; then
    if [ "${REQUIRE_LIVE_RULESET:-0}" = "1" ]; then
      echo "REQUIRE_LIVE_RULESET=1 but no gh credentials are available"
      return 1
    fi
    skip "no gh credentials for ${REPO_SLUG} (live check is local/credentialed-only; CI exercises codified JSON)"
  fi
  local rulesets_list
  if ! rulesets_list="$(gh api "repos/${REPO_SLUG}/rulesets")"; then
    echo "gh api failed to list rulesets for ${REPO_SLUG}"
    return 1
  fi
  local rs_id
  rs_id="$(python3 -c 'import json,sys
data = json.loads(sys.argv[1])
print(next((str(r["id"]) for r in data if isinstance(r, dict) and r.get("name") == "pr-quality"), ""))' "$rulesets_list")"
  [ -n "$rs_id" ] || { echo "no pr-quality ruleset found on ${REPO_SLUG}"; return 1; }

  local live_rs="${BATS_TEST_TMPDIR}/live-pr-quality.json"
  if ! gh api "repos/${REPO_SLUG}/rulesets/${rs_id}" > "$live_rs"; then
    echo "gh api failed to fetch ruleset ${rs_id} for ${REPO_SLUG}"
    return 1
  fi
  run validate_pr_quality_ruleset "$live_rs"
  [ "$status" -eq 0 ] || { echo "live pr-quality ruleset failed validation: $output"; return 1; }
}
