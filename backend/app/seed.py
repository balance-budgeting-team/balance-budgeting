"""Create the tables and load synthetic demo data that matches the Figma frames.

Run from ``backend/`` after the database is up::

    python -m app.seed

Running it again resets the demo user's data. All data is made up; no real
financial data is used.

Resulting Home values (Flow 1, F1-1): a weekly budget of $350.00 and $152.00
spent so far this week.
"""

from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import Base, SessionLocal, engine
from app.models import Budget, Transaction
from app.services.budget_summary import period_bounds

DEMO_BUDGET_PERIOD = "weekly"
DEMO_BUDGET_AMOUNT = Decimal("350.00")

# (merchant, category, amount, days ago). Included amounts sum to $152.00.
THIS_WEEK = [
    ("Blue Bottle Coffee", "Dining", Decimal("5.75"), 0),
    ("Whole Foods", "Groceries", Decimal("32.14"), 1),
    ("Netflix", "Subscription", Decimal("15.99"), 2),
    ("Target", "Shopping", Decimal("48.62"), 2),
    ("Chipotle", "Dining", Decimal("13.40"), 3),
    ("Shell", "Gas", Decimal("36.10"), 3),
]
# Excluded from spending (FR-10): stays in history, never counted.
EXCLUDED_THIS_WEEK = ("Venmo transfer to roommate", "Transfer", Decimal("20.00"), 1)
# Old enough to fall outside any current daily, weekly, or monthly period.
OLDER = ("Spirit Airlines", "Travel", Decimal("189.00"), 40)


def _posted_at(now: datetime, days_ago: int, week_start: datetime) -> datetime:
    # Keep "this week" rows inside the current week even early on a Monday.
    return max(now - timedelta(days=days_ago, minutes=5), week_start)


def seed_demo_data(session: Session, now: datetime, user_id: int) -> Budget:
    """Reset ``user_id``'s budget and transactions to the demo values."""
    week_start, _ = period_bounds("weekly", now)

    budget = session.scalar(select(Budget).where(Budget.user_id == user_id))
    if budget is None:
        budget = Budget(user_id=user_id)
        session.add(budget)
    budget.period = DEMO_BUDGET_PERIOD
    budget.amount = DEMO_BUDGET_AMOUNT

    session.execute(delete(Transaction).where(Transaction.user_id == user_id))
    for merchant, category, amount, days_ago in THIS_WEEK:
        session.add(
            Transaction(
                user_id=user_id,
                merchant=merchant,
                category=category,
                amount=amount,
                posted_at=_posted_at(now, days_ago, week_start),
            )
        )
    merchant, category, amount, days_ago = EXCLUDED_THIS_WEEK
    session.add(
        Transaction(
            user_id=user_id,
            merchant=merchant,
            category=category,
            amount=amount,
            posted_at=_posted_at(now, days_ago, week_start),
            excluded=True,
        )
    )
    merchant, category, amount, days_ago = OLDER
    session.add(
        Transaction(
            user_id=user_id,
            merchant=merchant,
            category=category,
            amount=amount,
            posted_at=now - timedelta(days=days_ago),
        )
    )
    session.commit()
    return budget


def main() -> None:
    Base.metadata.create_all(engine)
    with SessionLocal() as session:
        budget = seed_demo_data(
            session, datetime.now(settings.timezone), settings.demo_user_id
        )
        print(
            f"Seeded demo data: budget_id={budget.id}, "
            f"{budget.period} budget ${budget.amount}."
        )


if __name__ == "__main__":
    main()
