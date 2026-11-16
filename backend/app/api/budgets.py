"""Budget routes for Flow 1: load the budget on Home and save an edited budget."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.models import Budget
from app.schemas.budget import BudgetSummaryOut, BudgetUpdate, ErrorOut
from app.services.budget_summary import build_summary, load_spent_so_far

router = APIRouter(prefix="/budgets", tags=["budgets"])

BUDGET_NOT_FOUND = "Budget not found."


def get_now() -> datetime:
    """Current time in the configured timezone. Tests override this dependency."""
    return datetime.now(settings.timezone)


def get_current_user_id() -> int:
    """Prototype stand-in for sign-in: every request acts as the demo user."""
    return settings.demo_user_id


DbSession = Annotated[Session, Depends(get_db)]
Now = Annotated[datetime, Depends(get_now)]
UserId = Annotated[int, Depends(get_current_user_id)]


def _summary(session: Session, budget: Budget, now: datetime) -> BudgetSummaryOut:
    spent = load_spent_so_far(
        session, user_id=budget.user_id, period=budget.period, now=now
    )
    summary = build_summary(
        budget_id=budget.id,
        period=budget.period,
        amount=budget.amount,
        spent=spent,
        now=now,
    )
    return BudgetSummaryOut.model_validate(summary, from_attributes=True)


@router.get(
    "/current",
    response_model=BudgetSummaryOut,
    responses={404: {"model": ErrorOut}},
    summary="Load the user's budget and spending totals for Home",
)
def get_current_budget(
    session: DbSession, now: Now, user_id: UserId
) -> BudgetSummaryOut:
    budget = session.scalar(select(Budget).where(Budget.user_id == user_id))
    if budget is None:
        raise HTTPException(status_code=404, detail=BUDGET_NOT_FOUND)
    return _summary(session, budget, now)


@router.put(
    "/{budget_id}",
    response_model=BudgetSummaryOut,
    responses={404: {"model": ErrorOut}, 422: {"model": ErrorOut}},
    summary="Save a new budget period and amount (FR-03)",
)
def update_budget(
    budget_id: int,
    body: BudgetUpdate,
    session: DbSession,
    now: Now,
    user_id: UserId,
) -> BudgetSummaryOut:
    budget = session.get(Budget, budget_id)
    # Another user's budget is reported as missing so its existence is not revealed.
    if budget is None or budget.user_id != user_id:
        raise HTTPException(status_code=404, detail=BUDGET_NOT_FOUND)
    budget.period = body.period
    budget.amount = body.amount
    session.commit()
    session.refresh(budget)
    return _summary(session, budget, now)
