"""Database tables used by the Flow 1 budget prototype."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base

BUDGET_PERIODS = ("daily", "weekly", "monthly")


class Budget(Base):
    """A user's recurring everyday-spending budget (one per user)."""

    __tablename__ = "budgets"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_budgets_amount_positive"),
        CheckConstraint(
            "period IN ('daily', 'weekly', 'monthly')", name="ck_budgets_period"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    period: Mapped[str] = mapped_column(String(16))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Transaction(Base):
    """A spending transaction. Positive ``amount`` means money spent."""

    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    merchant: Mapped[str] = mapped_column(String(120))
    category: Mapped[str] = mapped_column(String(60))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    posted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    # FR-10: excluded transactions stay in history but do not count as spending.
    excluded: Mapped[bool] = mapped_column(Boolean, default=False)
