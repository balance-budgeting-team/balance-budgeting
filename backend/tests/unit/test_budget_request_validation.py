"""Request validation for PUT /budgets/{budget_id}, without a database.

Invalid requests are rejected before the route runs, so the database session
dependency is replaced with one that fails the test if it is ever used.
"""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.api import errors
from app.core.db import get_db
from app.main import app


class _NoDatabase:
    def __getattr__(self, name: str) -> None:
        raise AssertionError("invalid requests must not reach the database")


@pytest.fixture
def client() -> Iterator[TestClient]:
    app.dependency_overrides[get_db] = lambda: _NoDatabase()
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize(
    ("body", "message"),
    [
        ({"period": "weekly", "amount": 0}, errors.AMOUNT_TOO_LOW),  # F1-2e
        ({"period": "weekly", "amount": -25}, errors.AMOUNT_TOO_LOW),
        ({"period": "weekly", "amount": None}, errors.AMOUNT_TOO_LOW),
        ({"period": "weekly", "amount": ""}, errors.AMOUNT_TOO_LOW),
        ({"period": "weekly", "amount": "abc"}, errors.AMOUNT_TOO_LOW),
        ({"period": "weekly", "amount": "NaN"}, errors.AMOUNT_TOO_LOW),
        ({"period": "weekly"}, errors.AMOUNT_TOO_LOW),
        ({"period": "weekly", "amount": 1000000.01}, errors.AMOUNT_TOO_HIGH),
        ({"period": "weekly", "amount": 400.125}, errors.AMOUNT_TOO_PRECISE),
        ({"period": "yearly", "amount": 400}, errors.PERIOD_INVALID),
        ({"period": "Weekly", "amount": 400}, errors.PERIOD_INVALID),
        ({"amount": 400}, errors.PERIOD_INVALID),
        (
            {"period": "weekly", "amount": 400, "ammount": 400},
            "Unexpected field: ammount.",
        ),
    ],
)
def test_invalid_budget_is_rejected_with_one_message(
    client: TestClient, body: dict[str, object], message: str
) -> None:
    response = client.put("/budgets/1", json=body)
    assert response.status_code == 422
    assert response.json() == {"detail": message}


def test_non_json_body_is_rejected(client: TestClient) -> None:
    response = client.put(
        "/budgets/1",
        content="period=weekly&amount=400",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": errors.BODY_INVALID}


def test_non_numeric_budget_id_is_rejected(client: TestClient) -> None:
    response = client.put("/budgets/abc", json={"period": "weekly", "amount": 400})
    assert response.status_code == 422
    assert response.json() == {"detail": errors.BUDGET_ID_INVALID}


def test_health(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok"}
