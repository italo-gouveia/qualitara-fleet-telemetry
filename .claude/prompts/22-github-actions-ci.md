# Prompt 22 — GitHub Actions CI

## Context

The project has no CI pipeline. Every quality gate (pytest, ruff, mypy, tsc, npm build)
runs only locally via `make`. A hiring evaluator opening the repo will immediately
check whether CI is green — a missing workflow is a visible gap.

## Goal

Add `.github/workflows/ci.yml` that runs on every push and PR to `main`:

1. **Backend** — pytest, ruff, mypy
2. **Frontend** — tsc --noEmit, npm run build

Security and advanced steps (OWASP Dependency-Check, SBOM, Dependabot) are
deferred to a future workflow as documented in the roadmap.

---

## Deliverables

### `.github/workflows/ci.yml`

Two jobs: `backend` and `frontend`, both running on `ubuntu-latest`.

**backend job:**
```
- uses: actions/checkout@v4
- uses: actions/setup-python@v5 (python-version: "3.12")
- run: pip install -r requirements.txt -r requirements-dev.txt
- run: python -m pytest tests/ -v
- run: python -m ruff check app/ tests/
- run: python -m mypy app/ --ignore-missing-imports
```
Working directory: `backend/`

**frontend job:**
```
- uses: actions/checkout@v4
- uses: actions/setup-node@v4 (node-version: "20")
- run: npm ci
- run: npm run build
- run: npx tsc --noEmit
```
Working directory: `frontend/`

### Trigger

```yaml
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
```

### Concurrency (cancel stale runs on the same branch)

```yaml
concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true
```

---

## Acceptance criteria

- [ ] `.github/workflows/ci.yml` present with backend + frontend jobs
- [ ] `pytest -v` / `ruff` / `mypy` run in backend job
- [ ] `npm ci` / `npm run build` / `tsc --noEmit` run in frontend job
- [ ] Concurrency group cancels stale runs
- [ ] `pytest -v` still passes locally (no app code changed)
