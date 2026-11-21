"""Recent transaction history for Home."""

from typing import Annotated

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.api.budgets import DbSession, UserId
from app.models import Transaction
from app.schemas.transaction import RecentTransactionsOut, TransactionOut

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("/recent", response_model=RecentTransactionsOut)
def get_recent_transactions(
    session: DbSession, user_id: UserId, limit: Annotated[int, Query(ge=1, le=50)] = 10
) -> RecentTransactionsOut:
    transactions = session.scalars(
        select(Transaction)
        .where(Transaction.user_id == user_id)
        .order_by(Transaction.posted_at.desc(), Transaction.id.desc())
        .limit(limit)
    ).all()
    return RecentTransactionsOut(
        transactions=[
            TransactionOut.model_validate(transaction) for transaction in transactions
        ]
    )
