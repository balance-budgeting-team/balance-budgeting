# Backend

Reserved for Balance's Python FastAPI backend. There is no application entry point, dependency manifest, Docker Compose configuration, database migration, or runnable backend test suite yet.

`app/services/` will hold financial and application logic. `app/adapters/` will isolate external providers behind interfaces so tests can replace them with fakes. `tests/unit/` and `tests/integration/` separate isolated behavior from API/database integration.

The first implementation must add reproducible dependency/setup commands, formatting/linting, and real unit/integration checks. Acceptance uses PostgreSQL, simulated providers, unset live credentials, and test traffic limited to the database. Every implemented adapter needs success/error/timeout tests and at least 80% line coverage; the complete suite must finish in under 10 minutes. See the [development process](../doc/DEVELOPMENT_PROCESS.md#application-gates-to-add-with-implementation).
