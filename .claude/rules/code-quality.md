# Code Quality — Complexity, Sonar Issues, and Cognitive Load

## Cyclomatic Complexity

McCabe cyclomatic complexity = number of linearly independent paths through a function.
Each `if`, `elif`, `for`, `while`, `except`, `and`, `or`, `match case` adds +1 to the base of 1.

| Score | Status |
|-------|--------|
| 1–5 | Ideal |
| 6–10 | Acceptable — review if it can be split |
| 11–15 | Warning — refactor before merge |
| 16+ | **Block** — must be refactored |

```python
# COMPLEXITY 7 — borderline, refactor
def process_event(event):
    if event.status == "fault":          # +1
        if event.battery_pct < 5:        # +1
            alert_critical()
        elif event.error_codes:          # +1
            log_errors()
    elif event.status == "moving":       # +1
        if event.speed_mps > 3:          # +1
            flag_overspeed()
    for code in event.error_codes:       # +1
        persist(code)

# REFACTORED — extract into small focused functions
def process_event(event):
    handle_status(event)
    persist_error_codes(event.error_codes)
```

## Cognitive Complexity (SonarQube-style)

Cognitive complexity penalises **nested** control flow more than cyclomatic complexity does.
Each nesting level adds extra weight — a loop inside an `if` inside another `if` is much harder to read than three sequential `if`s.

**Rule**: no function should require the reader to track more than 3 levels of nesting simultaneously.

```python
# HIGH COGNITIVE COMPLEXITY — 3 levels deep
def analyse(events):
    for event in events:               # nesting +1
        if event.status == "fault":    # nesting +2
            for code in event.codes:   # nesting +3  ← hard limit
                if is_critical(code):  # nesting +4  ← VIOLATION
                    ...

# REFACTORED
def analyse(events):
    for event in events:
        if event.status == "fault":
            handle_fault_codes(event.codes)  # extracted

def handle_fault_codes(codes):
    critical = [c for c in codes if is_critical(c)]
    ...
```

## Cognitive Complexity Penalties (reference)

| Construct | Flat | Per nesting level |
|-----------|------|-------------------|
| `if / elif / else` | +1 | +nesting depth |
| `for / while` | +1 | +nesting depth |
| `except` | +1 | +nesting depth |
| `and / or` (boolean chain) | +1 each | flat |
| Recursion | +1 | flat |
| Nested function / lambda | +1 | flat |

**Target**: cognitive complexity ≤ 15 per function. Above 25 is a blocker.

---

## SonarQube-Style Issues — Categories

### Bugs (must fix before merge)
- Mutable default argument: `def f(items=[])` — shared across all calls
- Comparing `datetime` objects without timezone awareness
- Missing `await` on coroutines (silent no-op in Python)
- `except Exception as e: pass` — swallowing exceptions
- Unbounded recursion without base case guard
- `is` comparison for value equality: `if x is "fault"` (use `==`)
- `float` equality: `if battery == 0.0` (use `abs(battery) < epsilon`)

### Code Smells (refactor within sprint)
- **Long method**: > 30 lines (excluding docstring/comments)
- **Long parameter list**: > 4 parameters — consider a dataclass/schema
- **Duplicated code**: same block in 3+ places — extract helper
- **Dead code**: unreachable branches, unused imports, unused variables
- **Magic numbers**: `if battery < 15` — use named constants
- **Flag parameters**: `def process(event, is_dry_run: bool)` — split into two functions
- **Shotgun surgery**: one change requires edits in 5+ files

### Vulnerability Hotspots (fix immediately)
- Any `eval()` or `exec()` on user input
- `text(f"SELECT ... {user_input}")` — raw SQL with user data
- Logging request bodies at INFO level (PII/secrets exposure)
- Hard-coded credentials in source

### Security Hotspots (review carefully)
- `random` module for anything security-related (use `secrets`)
- Unvalidated redirect URLs
- Unbounded query results (no `.limit()`)

---

## Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Module | `snake_case` | `telemetry_service.py` |
| Class | `PascalCase` | `TelemetryRepository` |
| Function / method | `snake_case`, verb | `get_fleet_state`, `ingest_event` |
| Constant | `UPPER_SNAKE` | `MAX_BATCH_SIZE = 500` |
| Private helper | `_snake_case` | `_apply_anomaly_rules` |
| Type alias | `PascalCase` | `VehicleId = str` |

**Anti-patterns**: `Manager`, `Handler`, `Helper`, `Utils` as sole class names — these are responsibility dumping grounds.

---

## DRY vs YAGNI Balance

| Situation | Action |
|-----------|--------|
| Same logic in 2 places | Leave it — watch for a third |
| Same logic in 3+ places | Extract a named function |
| Same pattern in tests | Extract a fixture or helper, not a base class |
| Speculative "we might need this" | Delete it — YAGNI |

---

## Function Length Guidelines

| Length | Action |
|--------|--------|
| ≤ 15 lines | Good |
| 16–30 lines | Acceptable if cohesive |
| 31–50 lines | Consider extracting private helpers |
| > 50 lines | Extract — almost always violates SRP |

This applies to **body lines** only (not blank lines, comments, or type annotations).

---

## Pre-merge Checklist

- [ ] No function with cyclomatic complexity > 10
- [ ] No function with nesting depth > 3
- [ ] No magic numbers — all thresholds are named constants
- [ ] No `except: pass` or bare `except Exception`
- [ ] No mutable default arguments
- [ ] No unused imports (`ruff check` catches these)
- [ ] No dead code paths
- [ ] Names describe intent — no `data`, `obj`, `temp`, `x` outside list comprehensions
