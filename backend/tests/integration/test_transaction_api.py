"""Recent transaction history against PostgreSQL."""

from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.budgets import get_current_user_id
from app.main import app
from app.models import Budget, Transaction


def test_seed_history(client: TestClient, demo_budget: Budget) -> None:
    response = client.get("/transactions/recent")
    assert response.status_code == 200
    transactions = response.json()["transactions"]
    assert len(transactions) == 8
    assert transactions[0] == {
        "id": transactions[0]["id"],
        "merchant": "Blue Bottle Coffee",
        "category": "Dining",
        "amount": 5.75,
        "posted_at": "2026-11-18T16:55:00Z",
        "excluded": False,
    }
    assert any(
        t["merchant"] == "Venmo transfer to roommate" and t["excluded"]
        for t in transactions
    )


def test_order_limits_and_isolation(
    client: TestClient, db: Session, fixed_now: datetime
) -> None:
    rows = [
        Transaction(
            user_id=1,
            merchant=f"Merchant {i}",
            category="Dining",
            amount=Decimal("1.25"),
            posted_at=fixed_now - timedelta(minutes=i // 2),
            excluded=i == 0,
        )
        for i in range(12)
    ]
    db.add_all(
        rows
        + [
            Transaction(
                user_id=2,
                merchant="Other",
                category="Dining",
                amount=Decimal("2.00"),
                posted_at=fixed_now + timedelta(days=1),
                excluded=False,
            )
        ]
    )
    db.commit()
    expected = sorted(rows, key=lambda row: (row.posted_at, row.id), reverse=True)
    default = client.get("/transactions/recent").json()["transactions"]
    assert [t["id"] for t in default] == [row.id for row in expected[:10]]
    assert any(t["excluded"] for t in default)
    for limit in (1, 5, 50):
        response = client.get("/transactions/recent", params={"limit": limit})
        assert response.status_code == 200
        assert [t["id"] for t in response.json()["transactions"]] == [
            row.id for row in expected[:limit]
        ]
    app.dependency_overrides[get_current_user_id] = lambda: 2
    assert [
        t["merchant"] for t in client.get("/transactions/recent").json()["transactions"]
    ] == ["Other"]


@pytest.mark.parametrize("limit", ["0", "-1", "51", "1.5", "abc"])
def test_invalid_limit(client: TestClient, limit: str) -> None:
    response = client.get("/transactions/recent", params={"limit": limit})
    assert response.status_code == 422
    assert response.json() == {
        "detail": "Limit must be a whole number between 1 and 50."
    }


def test_empty_history(client: TestClient) -> None:
    response = client.get("/transactions/recent")
    assert response.status_code == 200
    assert response.json() == {"transactions": []}
