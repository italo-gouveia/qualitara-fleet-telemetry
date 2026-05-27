# Local Context — Personal Dev Notes

## What `.local-context/` Is

A gitignored directory for personal, in-progress, or sensitive development notes that should never be committed.

## What Goes Here

- Spike results: "tried X, didn't work because Y"
- Personal API keys for testing (NEVER commit these)
- Rough notes from reading the FastAPI/SQLAlchemy docs
- Performance benchmarks you ran locally
- Draft ADR text before it's polished enough for `docs/ADR.md`
- Scratch SQL queries from exploration

## What Does NOT Go Here

- Architecture decisions → `docs/ADR.md`
- AI interaction log → `docs/AI_INTERACTION_LOG.md`
- Shared team context → `.global-context/`
- Anything another developer would need to run the project

## File Naming

```
.local-context/
├── spike-asyncpg-concurrent-writes.md
├── notes-sqlalchemy-upsert.md
├── scratch-zone-counter-queries.sql
└── draft-adr.md
```

## Git Configuration

`.local-context/` is in `.gitignore` at the repo root.
Verify before first commit:

```bash
git check-ignore -v .local-context/
# should output: .gitignore:2:.local-context/
```

## Sharing Local Context

If a spike note becomes a team decision, move the content to:
- `docs/ADR.md` for architectural decisions
- `.claude/context/` for shared engineering context
- `README.md` for operational knowledge

Then delete the local copy.
