"""Budget API against PostgreSQL, using the Flow 1 Figma values (FR-03, FR-04)."""

from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api import errors
from app.models import Budget, Transaction
from app.seed import seed_demo_data

DEMO_USER_ID = 1  # matches the demo_budget fixture


def _saved_budget(db: Session) -> Budget:
    db.expire_all()
    budget = db.scalar(select(Budget).where(Budget.user_id == DEMO_USER_ID))
    assert budget is not None
    return budget


def test_home_loads_budget_and_spending(
    client: TestClient, demo_budget: Budget
) -> None:
    # F1-1: "Weekly spending $152 of $350". Safe to spend = ($350 - $152) / 5 days.
    response = client.get("/budgets/current")
    assert response.status_code == 200
    assert response.json() == {
        "budget_id": demo_budget.id,
        "period": "weekly",
        "amount": 350.0,
        "spent_so_far": 152.0,
        "progress_percent": 43,
        "safe_to_spend_today": 39.6,
    }


def test_saving_new_weekly_amount_returns_and_persists_totals(
    client: TestClient, demo_budget: Budget, db: Session
) -> None:
    # F1-3 -> F1-4: weekly limit $350.00 -> $400.00, spending stays $152.00.
    response = client.put(
        f"/budgets/{demo_budget.id}", json={"period": "weekly", "amount": 400.00}
    )
    assert response.status_code == 200
    expected = {
        "budget_id": demo_budget.id,
        "period": "weekly",
        "amount": 400.0,
        "spent_so_far": 152.0,
        "progress_percent": 38,
        "safe_to_spend_today": 49.6,
    }
    assert response.json() == expected
    assert client.get("/budgets/current").json() == expected
    saved = _saved_budget(db)
    assert (saved.period, saved.amount) == ("weekly", Decimal("400.00"))


def test_switching_to_monthly_uses_this_months_spending(
    client: TestClient, demo_budget: Budget
) -> None:
    # The 40-day-old transaction is outside November, so spending stays $152.
    response = client.put(
        f"/budgets/{demo_budget.id}", json={"period": "monthly", "amount": 1200}
    )
    assert response.json() == {
        "budget_id": demo_budget.id,
        "period": "monthly",
        "amount": 1200.0,
        "spent_so_far": 152.0,
        "progress_percent": 13,
        "safe_to_spend_today": 80.61,  # ($1200 - $152) / 13 days, rounded down
    }


def test_switching_to_daily_counts_only_today(
    client: TestClient, demo_budget: Budget
) -> None:
    # Only Blue Bottle Coffee ($5.75) is from today.
    response = client.put(
        f"/budgets/{demo_budget.id}", json={"period": "daily", "amount": 50}
    )
    body = response.json()
    assert (body["spent_so_far"], body["progress_percent"]) == (5.75, 12)
    assert body["safe_to_spend_today"] == 44.25


def test_amount_given_as_numeric_string_is_accepted(
    client: TestClient, demo_budget: Budget
) -> None:
    response = client.put(
        f"/budgets/{demo_budget.id}", json={"period": "weekly", "amount": "400.50"}
    )
    assert response.status_code == 200
    assert response.json()["amount"] == 400.5


@pytest.mark.parametrize(
    ("body", "message"),
    [
        ({"period": "weekly", "amount": 0}, errors.AMOUNT_TOO_LOW),
        ({"period": "weekly", "amount": -50}, errors.AMOUNT_TOO_LOW),
        ({"period": "weekly", "amount": ""}, errors.AMOUNT_TOO_LOW),
        ({"period": "weekly", "amount": "abc"}, errors.AMOUNT_TOO_LOW),
        ({"period": "yearly", "amount": 400}, errors.PERIOD_INVALID),
    ],
)
def test_rejected_update_leaves_saved_budget_unchanged(
    client: TestClient,
    demo_budget: Budget,
    db: Session,
    body: dict[str, object],
    message: str,
) -> None:
    response = client.put(f"/budgets/{demo_budget.id}", json=body)
    assert response.status_code == 422
    assert response.json() == {"detail": message}
    saved = _saved_budget(db)
    assert (saved.period, saved.amount) == ("weekly", Decimal("350.00"))
    assert client.get("/budgets/current").json()["amount"] == 350.0


def test_unknown_budget_id_returns_404(client: TestClient, demo_budget: Budget) -> None:
    response = client.put("/budgets/999", json={"period": "weekly", "amount": 400})
    assert response.status_code == 404
    assert response.json() == {"detail": "Budget not found."}


def test_cannot_update_another_users_budget(
    client: TestClient, demo_budget: Budget, db: Session, fixed_now: datetime
) -> None:
    other = seed_demo_data(db, fixed_now, user_id=2)
    response = client.put(
        f"/budgets/{other.id}", json={"period": "weekly", "amount": 1}
    )
    assert response.status_code == 404
    db.expire_all()
    assert db.get(Budget, other.id).amount == Decimal("350.00")


def test_home_without_a_budget_returns_404(client: TestClient) -> None:
    response = client.get("/budgets/current")
    assert response.status_code == 404
    assert response.json() == {"detail": "Budget not found."}


def test_excluded_transaction_does_not_count(
    client: TestClient, demo_budget: Budget, db: Session
) -> None:
    # Matches Flow 2 (F2-3): excluding Blue Bottle Coffee moves $152.00 to $146.25.
    db.execute(
        update(Transaction)
        .where(Transaction.merchant == "Blue Bottle Coffee")
        .values(excluded=True)
    )
    db.commit()
    assert client.get("/budgets/current").json()["spent_so_far"] == 146.25


def test_spending_from_last_week_does_not_count(
    client: TestClient, demo_budget: Budget, db: Session, fixed_now: datetime
) -> None:
    db.add(
        Transaction(
            user_id=DEMO_USER_ID,
            merchant="Last week groceries",
            category="Groceries",
            amount=Decimal("80.00"),
            posted_at=fixed_now - timedelta(days=7),
        )
    )
    db.commit()
    assert client.get("/budgets/current").json()["spent_so_far"] == 152.0


def test_database_rejects_non_positive_budget(db: Session) -> None:
    db.add(Budget(user_id=3, period="weekly", amount=Decimal("0")))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_reseeding_resets_data_and_keeps_the_same_budget_id(
    db: Session, fixed_now: datetime
) -> None:
    first = seed_demo_data(db, fixed_now, DEMO_USER_ID)
    second = seed_demo_data(db, fixed_now, DEMO_USER_ID)
    assert first.id == second.id
    count = db.scalar(
        select(func.count())
        .select_from(Transaction)
        .where(Transaction.user_id == DEMO_USER_ID)
    )
    assert count == 8  # 6 this week, 1 excluded, 1 older
