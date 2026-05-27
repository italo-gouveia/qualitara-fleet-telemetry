# Simplicity First — KISS, YAGNI, and the 5-6h Budget

This project has a fixed time budget. Over-engineering is a submission failure.

## The Rules

### KISS — Keep It Simple

- If you can solve it in 20 lines, don't build a framework for it.
- One function, one job. No "utils.py" dumping grounds.
- No metaclasses, no decorators-of-decorators, no abstract base classes for concepts that only have one implementation.

### YAGNI — You Aren't Gonna Need It

| Temptation | Reality |
|------------|---------|
| Redis cache | Not in the spec; polling at 2s is fine |
| Kafka for events | 50 vehicles at 1 Hz is trivially synchronous |
| JWT auth | Not required in the challenge |
| Multi-tenant isolation | There is one fleet |
| Plugin registry for anomaly rules | A list of functions is enough |

### Three Strikes Rule

- Copy once: fine.
- Copy twice: maybe fine.
- Copy three times: extract a helper. Not before.

## When Abstraction IS Worth It

The challenge explicitly asks for extensibility in the fault-handling and anomaly logic:

- **Anomaly rules as a list of functions** `[rule1, rule2, ...]` — each `(event) -> Optional[Anomaly]`. New rules append to the list. This is the right level.
- **Repository pattern for DB access** — one class per entity, methods named after queries. Worth it because it makes tests trivial (inject a fake repo).
- **Pydantic schemas separate from ORM models** — worth it; mixing them causes pain.

## Complexity Limits

- Methods: ≤ 20 lines is a good smell; > 40 lines is a red flag.
- Nesting: ≤ 3 levels deep. Use early returns / guard clauses.
- Files: if a file exceeds ~150 lines, ask whether it has one responsibility.

## Anti-Patterns to Avoid Here

- `AbstractBaseFactory` for a thing that has one implementation.
- Generic `EventBus` when a direct function call works.
- `config.py` with 50 settings when 5 are used.
- Middleware for cross-cutting concerns that only one route needs.
- Celery/background tasks for work that takes <50ms inline.
