# AGENTS.md

This repository follows the organization-wide development standards defined in
[`combsmith/.github/AGENTS.md`](https://github.com/combsmith/.github/blob/main/AGENTS.md).

Read that file before making changes that touch CI, agent configuration, repo
settings, or labels. Repo-specific deviations, if any, are documented below.

## Pre-Commit Quality Checks

Before committing or pushing any changes, run the repository's local CI checks:

- **CI & compliance regression guards (repo root):**
  ```bash
  bats tests/*.bats
  ```
- **DemandRadar Python package (`pocs/demand-radar/`):**
  Whenever touching files under `pocs/demand-radar/`, run all four stages enforced by `.github/workflows/ci.yml`:
  ```bash
  cd pocs/demand-radar
  ruff check .
  ruff format --check .
  mypy --ignore-missing-imports .
  python3 -m pytest tests/ -q --cov=. --cov-fail-under=80
  ```
