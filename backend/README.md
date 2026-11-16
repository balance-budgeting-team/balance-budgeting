# Backend

Balance's Python FastAPI backend. It currently serves the budget API for the Flow 1 prototype (set a daily, weekly, or monthly budget):

| Method and path | Purpose |
| --- | --- |
| `GET /budgets/current` | Load the budget and spending totals shown on Home. |
| `PUT /budgets/{budget_id}` | Save a new budget period and amount (FR-03) and return the recalculated totals. |
| `GET /health` | Report that the server is running. |

## Request and response format

Save a budget with `PUT /budgets/{budget_id}`:

```json
{ "period": "weekly", "amount": 400.00 }
```

Both budget routes return:

```json
{
  "budget_id": 1,
  "period": "weekly",
  "amount": 400.0,
  "spent_so_far": 152.0,
  "progress_percent": 38,
  "safe_to_spend_today": 49.6
}
```

- `period` is `daily`, `weekly`, or `monthly`.
- Money is a JSON number in US dollars with at most two decimal places.
- An invalid request returns status 422 with one message the app can show, for example `{"detail": "Enter an amount greater than $0."}`.
- An unknown budget returns status 404 with `{"detail": "Budget not found."}`.

With the server running, interactive documentation is at <http://localhost:8000/docs>.

## Prototype rules and limitations

- Periods use the `America/Indiana/Indianapolis` timezone (`BALANCE_TIMEZONE`). A day starts at midnight, a week starts Monday, and a month starts on the 1st.
- Spending so far counts transactions in the current period that are not excluded (FR-10).
- `safe_to_spend_today` is a simplified stand-in for FR-04: the money left in the period divided by the days left, including today, rounded down to the cent. The full FR-04 rule needs account balances, obligations, and savings that the prototype does not have yet.
- There is no sign-in yet. Every request acts as demo user 1.
- Tables are created by `python -m app.seed`. There are no migrations yet.
- All data is synthetic. No provider integrations or real financial data are used.

## Layout

`app/api/` holds routes and the validation-error format. `app/schemas/` holds request and response bodies. `app/models/` holds database tables. `app/services/` holds financial calculations (`budget_summary.py`). `app/core/` holds settings and the database session. `app/seed.py` loads demo data matching the Figma frames. `tests/unit/` runs without a database. `tests/integration/` runs the API against PostgreSQL.

## Run locally

Use Python 3.12 (see `.python-version`) and Docker. From this directory:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
docker compose up -d --wait
.venv/bin/python -m app.seed
.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

`docker compose up` starts PostgreSQL 16 with a `balance` database and an empty `balance_test` database. `app.seed` creates the tables and resets the demo data: a $350.00 weekly budget with $152.00 spent this week. Run it again at any time to reset.

From an app on the same Mac or the iOS Simulator, use `http://localhost:8000`. From a physical phone, use the Mac's local network address instead, for example `http://192.168.1.20:8000`. Browser-based clients (Expo web) must run on an origin listed in `CORS_ORIGINS`.

## Checks

```sh
.venv/bin/ruff check .
.venv/bin/ruff format --check .
TEST_DATABASE_URL=postgresql+psycopg://balance:balance@localhost:5432/balance_test .venv/bin/pytest
```

Integration tests drop and recreate every table in `TEST_DATABASE_URL`, so never point it at the `balance` development database. Without `TEST_DATABASE_URL`, integration tests are reported as skipped. CI always sets it and runs them against a PostgreSQL 16 service in **Backend tests (PostgreSQL)**. The tests make no network requests and need no provider credentials.

## Gates still to add

Acceptance uses PostgreSQL, simulated providers, unset live credentials, and test traffic limited to the database. Every implemented adapter needs success/error/timeout tests and at least 80% line coverage; the complete suite must finish in under 10 minutes. The outbound-network restriction and adapter coverage are not enforced yet because no provider implementation exists. Add them with that code. See the [development process](../doc/DEVELOPMENT_PROCESS.md#application-gates-to-add-with-implementation).
