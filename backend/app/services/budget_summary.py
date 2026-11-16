"""Budget period math and the spending summary shown on Home (Flow 1).

The calculations are plain functions so they can be unit-tested without a
database. ``load_spent_so_far`` is the only function that queries the database.

Prototype rules:
- Periods are calendar-based in the configured timezone: a day starts at
  midnight, a week starts Monday at midnight, a month starts on the 1st.
- Spending so far counts transactions in the current period that are not
  excluded (FR-10).
- Safe to spend today spreads the money left in the period evenly over the days
  left, including today, rounded down to the cent. This is a simplified
  stand-in for the full FR-04 available-to-spend rule, which also needs account
  balances, obligations, and savings that the prototype does not have yet.
"""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Transaction

CENT = Decimal("0.01")


@dataclass(frozen=True)
class BudgetSummary:
    budget_id: int
    period: str
    amount: Decimal
    spent_so_far: Decimal
    progress_percent: int
    safe_to_spend_today: Decimal


def _midnight(day: date, now: datetime) -> datetime:
    return datetime.combine(day, time.min, tzinfo=now.tzinfo)


def period_bounds(period: str, now: datetime) -> tuple[datetime, datetime]:
    """Return ``(start, end)`` of the period containing ``now``; end is exclusive.

    ``now`` must be timezone-aware and already in the user's timezone.
    """
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    today = now.date()
    if period == "daily":
        start_day, end_day = today, today + timedelta(days=1)
    elif period == "weekly":
        start_day = today - timedelta(days=today.weekday())
        end_day = start_day + timedelta(days=7)
    elif period == "monthly":
        start_day = today.replace(day=1)
        end_day = (start_day + timedelta(days=32)).replace(day=1)
    else:
        raise ValueError(f"unknown budget period: {period!r}")
    return _midnight(start_day, now), _midnight(end_day, now)


def days_left_including_today(period: str, now: datetime) -> int:
    _, end = period_bounds(period, now)
    return (end.date() - now.date()).days


def progress_percent(spent: Decimal, amount: Decimal) -> int:
    """Whole-number percent of the budget used. Can exceed 100 when over budget."""
    if amount <= 0:
        raise ValueError("budget amount must be positive")
    return int((spent / amount * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def safe_to_spend_today(
    amount: Decimal, spent: Decimal, period: str, now: datetime
) -> Decimal:
    remaining = max(amount - spent, Decimal("0"))
    days_left = days_left_including_today(period, now)
    return (remaining / days_left).quantize(CENT, rounding=ROUND_DOWN)


def build_summary(
    *, budget_id: int, period: str, amount: Decimal, spent: Decimal, now: datetime
) -> BudgetSummary:
    spent = spent.quantize(CENT)
    return BudgetSummary(
        budget_id=budget_id,
        period=period,
        amount=amount.quantize(CENT),
        spent_so_far=spent,
        progress_percent=progress_percent(spent, amount),
        safe_to_spend_today=safe_to_spend_today(amount, spent, period, now),
    )


def load_spent_so_far(
    session: Session, *, user_id: int, period: str, now: datetime
) -> Decimal:
    """Sum the user's included spending in the period containing ``now``."""
    start, end = period_bounds(period, now)
    total = session.scalar(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == user_id,
            Transaction.excluded.is_(False),
            Transaction.posted_at >= start,
            Transaction.posted_at < end,
        )
    )
    return Decimal(total)
