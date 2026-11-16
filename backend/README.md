# Backend

Reserved for Balance's Python FastAPI backend. There is no application entry point, Docker Compose configuration, database migration, or provider integration yet.

`app/services/` holds financial and application logic. `app/adapters/` will isolate external providers behind interfaces so tests can replace them with fakes. `tests/unit/` and `tests/integration/` separate isolated behavior from API/database integration.

## Implemented

- `app/services/streaks.py`: the FR-13 streak and achievement engine, a pure module with no database, provider, scheduler, or API dependencies. Callers supply each completed local day's remaining discretionary budget and already-counted discretionary spending. Tests are in `tests/unit/test_streaks.py` and use the shared fixture `tests/fixtures/streaks/fr13_40day.v1.json`.

## Local checks

Use Python 3.12 or later. From `backend/`:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/python -m pytest
```

The **Backend checks** workflow runs the same lint, format, and test commands on Python 3.12. PostgreSQL acceptance and coverage gates are not configured yet.

## Gates to add with further implementation

Further backend work must add formatting/linting and real unit/integration checks for what it introduces. Acceptance uses PostgreSQL, simulated providers, unset live credentials, and test traffic limited to the database. Every implemented adapter needs success/error/timeout tests and at least 80% line coverage; the complete suite must finish in under 10 minutes. See the [development process](../doc/DEVELOPMENT_PROCESS.md#application-gates-to-add-with-implementation).
