# Backend

Balance's Python FastAPI backend. It currently contains one service, `app/services/budget_threshold_alerts.py`, which decides when to submit FR-07 budget threshold alerts and honors FR-16 alert preferences. It also contains the provider-agnostic SMS interface, `app/adapters/sms.py`. There is no FastAPI application entry point, API route, database model, migration, Docker Compose configuration, or provider implementation yet.

`app/services/` holds financial and application logic. `app/adapters/` isolates external providers behind interfaces so tests can replace them with fakes. `tests/unit/` and `tests/integration/` separate isolated behavior from API/database integration. Shared test fakes live in `tests/conftest.py`.

## Setup and checks

Use Python 3.12 (see `.python-version`). From this directory:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/pytest
```

`pyproject.toml` pins pytest and ruff exactly. Installation needs internet access; the tests make no network requests and need no provider credentials. CI runs the same lint, format, and test commands as **Backend unit tests**.

## Gates still to add

Acceptance uses PostgreSQL, simulated providers, unset live credentials, and test traffic limited to the database. Every implemented adapter needs success/error/timeout tests and at least 80% line coverage; the complete suite must finish in under 10 minutes. PostgreSQL acceptance, the outbound-network restriction, and adapter coverage are not enforced yet because no database or provider implementation exists. Add them with that code. See the [development process](../doc/DEVELOPMENT_PROCESS.md#application-gates-to-add-with-implementation).
