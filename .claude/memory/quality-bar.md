---
name: quality-bar
description: "Complexity limits, N+1 prevention, performance expectations, sonar-style code quality standards for this project"
type: project
---

# Quality Bar

## Complexity Limits (non-negotiable)

- Cyclomatic complexity ≤ 10 per function — counts `if/elif/for/while/except/and/or`
- Cognitive complexity ≤ 15 per function — nesting depth penalised
- Max nesting depth: 3 levels — extract helper if exceeded
- Method body ≤ 30 lines

**Why**: evaluators will read the code. Readable, simple code signals seniority.

**How to apply**: Flag any function that violates these before suggesting implementation.

## N+1 Rules (correctness, not just performance)

- No `await repo.*()` inside a loop over a variable-size collection
- Frontend: no `useQuery` inside `.map()` per item
- Fix: batch load then `dict`/`Map` lookup, or JOIN at DB level

**Why**: N+1 at 50 vehicles = 50 queries per page load; at 500 = 500 queries. The evaluator will look for this specifically given the concurrent-writes focus of the challenge.

## Performance Expectations

- All collection endpoints bounded by `.limit()` — no unbounded result sets
- Zone counter: single `UPDATE ... SET count = count + 1` — enforced
- Fleet aggregate: SQL `GROUP BY` — enforced
- No `time.sleep()`, `requests.get()`, sync I/O in async code

## Sonar-Style Issues to Auto-Flag

- Mutable default arguments (`def f(items=[])`)
- Bare `except:` or `except Exception: pass`
- Magic numbers (extract as named constants)
- Dead code (unreachable branches, unused imports)
- `is` comparison for value equality
- `len(list_of_all_rows)` for count — use `SELECT COUNT(*)`
