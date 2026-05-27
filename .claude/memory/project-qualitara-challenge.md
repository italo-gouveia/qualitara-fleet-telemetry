---
name: project-qualitara-challenge
description: "Take-home challenge for Qualitara Staff/Principal Fullstack role — fleet telemetry service, 48h deadline, ADR+AI log required"
type: project
---

# Qualitara Fleet Telemetry Challenge

**Received**: 2026-05-27
**Deadline**: 48 hours from receipt (2026-05-29)
**Submit to**: jacki.torres@qualitara.com — public GitHub repo link

## What's Being Evaluated

70% system design / systematic thinking, 30% hands-on coding.
Explicit evaluation of AI tool usage and ability to catch flawed AI output.
ADR and AI log are weighted equally to code.

**Why**: Understanding evaluation criteria shapes how much time to spend on code vs documentation.

**How to apply**: Write the ADR and AI log with the same care as the implementation. Concurrency decisions must be documented and correct.

## Stack Decided

- Python 3.12 + FastAPI + SQLAlchemy async
- PostgreSQL (SQLite for dev)
- React 18 + TypeScript + TanStack Query (2s polling)
- In-process anomaly rule list (no queue)

## Critical Correctness Requirements

1. Zone counter: `UPDATE zone_counts SET entry_count = entry_count + 1` — never read-modify-write
2. Fault transition: `SELECT FOR UPDATE` + single transaction (mission cancel + maintenance record)
3. Fleet aggregate: DB `GROUP BY`, not in-process counters
