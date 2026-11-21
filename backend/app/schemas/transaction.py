"""Response bodies for transaction history."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.budget import Money


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    merchant: str
    category: str
    amount: Money
    posted_at: datetime
    excluded: bool


class RecentTransactionsOut(BaseModel):
    transactions: list[TransactionOut]
