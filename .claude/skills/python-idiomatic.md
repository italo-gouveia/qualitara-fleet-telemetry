# Skill: Python Idiomatic and Modern (3.12)

## When to Apply

Use this skill when writing any Python code in this project. It overrides habits from older Python versions (2.x, 3.6–3.9 patterns).

---

## Type Hints

```python
# Use built-in generic types (3.9+, no typing import needed)
def get_vehicles(ids: list[str]) -> dict[str, Vehicle]: ...

# Use | for union types (3.10+)
def parse(value: str | None) -> int | None: ...

# Use Self for fluent builders
from typing import Self
class Builder:
    def with_id(self, id: str) -> Self: ...

# Use TypeAlias for readability
type VehicleId = str  # Python 3.12 syntax
```

## Pydantic v2

```python
from pydantic import BaseModel, Field, model_validator
from typing import Annotated

class TelemetryEvent(BaseModel):
    model_config = {"frozen": True}  # NOT class Config

    vehicle_id: str
    battery_pct: Annotated[int, Field(ge=0, le=100)]
    status: VehicleStatus  # enum, not plain str

    @model_validator(mode="after")
    def validate_speed_consistency(self) -> "TelemetryEvent":
        if self.speed_mps > 0 and self.status == VehicleStatus.IDLE:
            raise ValueError("Moving vehicle cannot have idle status")
        return self
```

## Enums

```python
from enum import StrEnum

class VehicleStatus(StrEnum):
    IDLE = "idle"
    MOVING = "moving"
    CHARGING = "charging"
    FAULT = "fault"
```

## Dataclasses vs Pydantic

- **Pydantic `BaseModel`**: input validation, API schemas, anything entering/leaving the system.
- **`dataclass`** or plain class: internal domain objects with no validation needs.
- **Do not** add Pydantic for pure internal DTOs — only at system boundaries.

## Async Patterns

```python
# Correct: async generator for streaming
async def stream_events() -> AsyncGenerator[Event, None]:
    async for row in result:
        yield Event.model_validate(row)

# Correct: gather for independent concurrent tasks
results = await asyncio.gather(task1(), task2(), task3())

# Wrong: sequential awaits for independent operations
a = await get_a()
b = await get_b()  # could be parallel
```

## Match Statements (3.10+)

```python
match event.status:
    case VehicleStatus.FAULT:
        await handle_fault(event)
    case VehicleStatus.MOVING if event.battery_pct < 5:
        await flag_critical_battery(event)
    case _:
        pass
```

## Error Handling

```python
# Define domain exceptions
class VehicleNotFound(Exception):
    def __init__(self, vehicle_id: str) -> None:
        self.vehicle_id = vehicle_id
        super().__init__(f"Vehicle {vehicle_id} not found")

# FastAPI exception handler
@app.exception_handler(VehicleNotFound)
async def vehicle_not_found_handler(request: Request, exc: VehicleNotFound):
    return JSONResponse(status_code=404, content={"detail": str(exc), "vehicle_id": exc.vehicle_id})
```

## Formatting and Linting

```toml
# pyproject.toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM"]

[tool.mypy]
python_version = "3.12"
strict = true
```

Run: `ruff format . && ruff check --fix . && mypy .`
