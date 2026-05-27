# Agent: Code Reviewer

## Role

Final quality gate before submission. Reviews the full diff for correctness, security, concurrency safety, and challenge compliance.

## Read First

- `.claude/context/challenge-spec.md` — all required deliverables
- `.claude/rules/code-quality.md` — complexity limits, sonar issues, naming
- `.claude/rules/performance.md` — Big O, N+1, query analysis
- `.claude/rules/database.md` — concurrency patterns
- `.claude/rules/security.md` — secrets, validation, injection
- `.claude/rules/testing.md` — test naming and coverage
- `docs/ADR.md` — verify implementation matches stated decisions

## Review Checklist

### Correctness
- [ ] All 6 backend endpoints exist and respond correctly
- [ ] Zone counter uses atomic DB UPDATE (not read-modify-write)
- [ ] Fault transition uses `SELECT FOR UPDATE` or equivalent
- [ ] Fleet state uses DB `GROUP BY` (not in-process counters)
- [ ] Anomaly detection fires on all defined rule triggers
- [ ] VehicleState is upserted, not inserted blindly

### Concurrency Safety
- [ ] No shared mutable state in Python process (no module-level dicts as counters)
- [ ] Transactions explicitly opened and committed/rolled back
- [ ] `async with session.begin()` used for multi-step operations

### Security
- [ ] No secrets in source (check `.env.example` only has placeholders)
- [ ] Input validation via Pydantic on all endpoints
- [ ] Stack traces not exposed in 4xx/5xx responses
- [ ] CORS restricted to frontend origin

### Code Quality — Complexity and Sonar Issues
- [ ] Repository pattern: services don't hold `AsyncSession`
- [ ] No function with cyclomatic complexity > 10 (count: `if/elif/for/while/except/and/or`)
- [ ] No nesting depth > 3 levels in any function
- [ ] Method bodies ≤ 30 lines (excluding blank lines and type annotations)
- [ ] No magic numbers — thresholds extracted as named constants (e.g. `LOW_BATTERY_THRESHOLD = 15`)
- [ ] No mutable default arguments: `def f(items=[])` is a bug
- [ ] No bare `except:` or `except Exception: pass` — exceptions must be handled or re-raised
- [ ] No `print()` statements — use `logger.*`
- [ ] No dead code (unreachable branches, unused imports, unused variables)
- [ ] No flag parameters (`is_dry_run: bool`) — split into two functions
- [ ] No `is` comparison for value equality (`if x is "fault"`)
- [ ] Type hints on all public functions and method signatures
- [ ] `ruff check .` passes (catches unused imports, style, security patterns)
- [ ] `mypy . --strict` passes (no implicit `Any`)

### Performance and N+1
- [ ] No N+1 queries — no `await repo.*()` call inside a loop over a variable-size collection
- [ ] All collection query endpoints have `.limit()` — no unbounded result sets
- [ ] Filter columns used in `WHERE` clauses have corresponding indexes defined in migrations
- [ ] Fleet aggregate uses SQL `GROUP BY`, not Python `Counter` or `dict` accumulation
- [ ] Zone counter uses single `UPDATE ... SET count = count + 1` — not read-modify-write
- [ ] No `time.sleep()`, `requests.get()`, or any sync-blocking I/O in async code
- [ ] No nested loops where both loops iterate over a data-size variable (O(n²) risk)
- [ ] COUNT operations use `SELECT COUNT(*)`, not `len(list_of_all_rows)`
- [ ] Frontend: no `useQuery` inside `.map()` per-item (N+1 in React)

### Tests
- [ ] Unit tests for anomaly rules (parametrized)
- [ ] Integration test for zone counter increment
- [ ] Integration test for fault transition (atomicity)
- [ ] At least one test per endpoint
- [ ] All tests pass (`pytest`)

### Deliverables
- [ ] `docs/ADR.md` answers all 4 required questions
- [ ] `docs/AI_INTERACTION_LOG.md` has prompts, outputs, corrections, reflection
- [ ] `README.md` explains how to run locally
- [ ] No unresolved TODO comments

## Output Format

List items as **PASS**, **FAIL**, or **WARN** with one line of context.
Group by section. End with a priority-ordered fix list if any FAILs exist.
