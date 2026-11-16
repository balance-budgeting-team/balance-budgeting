"""Request and response bodies for the budget API (Section 3.3).

Example request (``PUT /budgets/{budget_id}``)::

    {"period": "weekly", "amount": 400.00}

Example response (``GET /budgets/current`` and ``PUT /budgets/{budget_id}``)::

    {
      "budget_id": 1,
      "period": "weekly",
      "amount": 400.0,
      "spent_so_far": 152.0,
      "progress_percent": 38,
      "safe_to_spend_today": 49.6
    }

Money is sent as JSON numbers in US dollars with at most two decimal places.
``safe_to_spend_today`` depends on how many days are left in the period; the
example above is for a Wednesday. Invalid requests return status 422 with
``{"detail": "<message to show the user>"}``; an unknown budget returns 404.
"""

from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer

BudgetPeriod = Literal["daily", "weekly", "monthly"]

MAX_BUDGET_AMOUNT = Decimal("1000000")

# Decimal internally for exact cents; plain JSON number on the wire.
Money = Annotated[
    Decimal, PlainSerializer(lambda value: float(value), return_type=float)
]


class BudgetUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    period: BudgetPeriod
    amount: Annotated[
        Decimal,
        Field(gt=0, le=MAX_BUDGET_AMOUNT, decimal_places=2, allow_inf_nan=False),
    ]


class BudgetSummaryOut(BaseModel):
    budget_id: int
    period: BudgetPeriod
    amount: Money
    spent_so_far: Money
    progress_percent: int
    safe_to_spend_today: Money


class ErrorOut(BaseModel):
    detail: str
