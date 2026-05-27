# Security Rules

## Secrets

- **Never commit**: `.env`, API keys, DB passwords, `SECRET_KEY`.
- All secrets via environment variables; use `pydantic-settings` `BaseSettings` to load them.
- Provide `.env.example` with placeholder values (committed); `.env` is gitignored.
- In logs: never print `DATABASE_URL` (contains password), never print request bodies wholesale.

## Input Validation

- **All** incoming data validated by Pydantic schemas before reaching services or DB.
- Use strict types: `battery_pct: Annotated[int, Field(ge=0, le=100)]`.
- `vehicle_id`: validate format (e.g. regex `r"v-\d{1,3}"`) to prevent injection via path params.
- `status`: use Python `Enum` — FastAPI will reject unknown values automatically.
- `timestamp`: accept ISO 8601 string, parse to `datetime` in Pydantic — reject malformed dates.
- Reject payloads larger than a configured max size (FastAPI `max_upload_size` or middleware).

## SQL Injection

- Zero risk when using SQLAlchemy expressions (`select()`, `update()`) with bound parameters.
- If `text()` is ever used, **always** pass values via `:named` params, never f-strings:
  ```python
  # CORRECT
  text("SELECT * FROM zones WHERE zone_id = :zid").bindparams(zid=zone_id)
  # NEVER
  text(f"SELECT * FROM zones WHERE zone_id = '{zone_id}'")
  ```

## CORS

- Allow only the frontend origin in non-production: `CORS_ORIGINS=http://localhost:5173`.
- In production: restrict to known domains via env var; never `allow_origins=["*"]` in prod.

## Dependency Security

- Pin exact versions in `requirements.txt` or `pyproject.toml` after initial install.
- Run `pip audit` or `safety check` before submission.
- Keep FastAPI, SQLAlchemy, and Pydantic on current stable versions.

## Error Responses

- Never expose stack traces, SQL errors, or internal model names in HTTP responses.
- Use FastAPI exception handlers to return structured `{"detail": "...", "type": "..."}` JSON.
- Log full exception server-side; return only safe generic message to client.

## Rate / Size Limiting

- For the challenge: document that production would need rate limiting on `POST /telemetry`.
- Add a `Content-Length` guard in middleware (e.g. reject bodies > 64KB).
