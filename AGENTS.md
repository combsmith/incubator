# AGENTS.md

This repository follows the organization-wide development standards defined in
[`combsmith/.github/AGENTS.md`](https://github.com/combsmith/.github/blob/main/AGENTS.md).

Read that file before making changes that touch CI, agent configuration, repo
settings, or labels. Repo-specific deviations, if any, are documented below.

## Pre-Commit Quality Checks

Before committing or pushing any changes, run the repository's local CI checks:

- **CI & compliance regression guards (repo root; requires `bats` and `python3` with `PyYAML`):**
  ```bash
  bats tests/*.bats
  ```
- **DemandRadar Python package (`pocs/demand-radar/`):**
  Whenever touching files under `pocs/demand-radar/`, install the hash-pinned CI tools and run all four stages enforced by `.github/workflows/ci.yml`:
  ```bash
  cd pocs/demand-radar
  python3 -m pip install -q --only-binary :all: --require-hashes -r requirements-ci.txt
  ruff check .
  ruff format --check .
  mypy --ignore-missing-imports .
  python3 -m pytest tests/ -q --cov=. --cov-fail-under=80
  ```
