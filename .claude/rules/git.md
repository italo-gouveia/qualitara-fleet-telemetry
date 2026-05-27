# Git Rules — Branch, Commit, PR

## Branch Strategy

| Pattern | Use |
|---------|-----|
| `feat/<slug>` | New feature or endpoint |
| `fix/<slug>` | Bug fix |
| `chore/<slug>` | Config, tooling, CI |
| `docs/<slug>` | Documentation only |
| `test/<slug>` | Tests only |
| `refactor/<slug>` | Code change without behavior change |

- Branch off `main`; merge back to `main`.
- Keep `main` always deployable (CI must be green).
- Do **not** force-push `main`.

## Conventional Commits

Format: `<type>(<scope>): <imperative description>`

```text
feat(telemetry): add POST /telemetry ingest endpoint
feat(zones): implement atomic zone entry counter
feat(dashboard): add live vehicle status list
fix(fault): correct atomic mission cancellation transaction
test(telemetry): add concurrent ingest integration test
docs(adr): document database and polling decisions
chore(ci): add ruff and mypy to GitHub Actions workflow
```

**Types**: `feat`, `fix`, `perf`, `refactor`, `test`, `docs`, `build`, `chore`, `ci`
**Scopes** (suggested): `telemetry`, `zones`, `fleet`, `anomaly`, `dashboard`, `api`, `db`, `ci`, `docs`
**Breaking change**: append `!` — `feat(api)!: rename vehicle_id field to id`

## Commit Discipline

- Small, coherent commits: one logical change per commit.
- Never commit: `.env`, `*.db`, `__pycache__`, `node_modules`, secrets.
- Commit `docs/AI_INTERACTION_LOG.md` updates alongside the code they describe.
- Verify `.gitignore` covers `.local-context/` and `.env` before first commit.

## PR Process (for self-review before submission)

PR description must cover:
1. **What**: summary of what was built
2. **Decisions**: key trade-offs made (DB choice, polling vs WebSocket, anomaly rules)
3. **AI usage**: confirm AI tools used; reference `docs/AI_INTERACTION_LOG.md`
4. **How to run**: `docker compose up` or manual steps
5. **Known gaps**: what was deliberately left out and why

## Quick Reference

```bash
# Start a feature branch
git checkout -b feat/telemetry-ingest

# Stage specific files (prefer over git add -A)
git add backend/app/routers/telemetry.py backend/tests/integration/test_telemetry.py

# Commit with conventional message
git commit -m "feat(telemetry): add POST /telemetry with zone and anomaly detection"

# Merge to main (no delete for challenge submission)
git checkout main && git merge feat/telemetry-ingest --no-ff
```
