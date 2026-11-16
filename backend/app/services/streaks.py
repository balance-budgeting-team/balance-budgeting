"""FR-13 streak and achievement engine.

Pure functions with no I/O, database, provider, or clock access. Callers supply each
completed local day's remaining discretionary budget (at the start of that day) and its
counted discretionary spending, already deduplicated across pending and posted versions.

Rules:

* The daily allowance is the remaining discretionary budget at the start of the day divided
  by the days remaining in the calendar month, including that day, rounded down to the cent.
  The rounded value is recorded and is the value spending is compared against.
* Spending at or below the allowance extends the streak by one; anything else resets it to 0.
  Missing data or a negative remaining budget resets the streak. A $0 budget yields a $0
  allowance, so a day with $0 counted spending still qualifies.
* The 3-, 7-, and 30-day achievements are each awarded once, the first time the streak
  reaches that length, and are kept after the streak resets.
* Days are evaluated in order without gaps. Re-evaluating a completed day is a no-op, so
  replayed jobs and late transactions never change completed results.
"""

import calendar
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, tzinfo
from decimal import ROUND_DOWN, Decimal
from enum import Enum, IntEnum
from types import MappingProxyType

CENT = Decimal("0.01")


class Achievement(IntEnum):
    """Streak-length achievements; each value is the streak length that earns it."""

    STREAK_3 = 3
    STREAK_7 = 7
    STREAK_30 = 30


class Outcome(Enum):
    """Result of evaluating one completed day."""

    WITHIN_ALLOWANCE = "within_allowance"
    OVER_ALLOWANCE = "over_allowance"
    MISSING_DATA = "missing_data"
    NEGATIVE_BUDGET = "negative_budget"

    @property
    def qualifies(self) -> bool:
        return self is Outcome.WITHIN_ALLOWANCE


def _check_date(value: object, name: str) -> None:
    # datetime subclasses date; a timestamp is not a local calendar day.
    if not isinstance(value, date) or isinstance(value, datetime):
        raise TypeError(f"{name} must be a datetime.date, got {type(value).__name__}")


def _check_money(value: object, name: str, *, allow_negative: bool) -> None:
    if value is None:
        return
    if not isinstance(value, Decimal):
        raise TypeError(f"{name} must be a Decimal or None, got {type(value).__name__}")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite, got {value}")
    if not allow_negative and value < 0:
        raise ValueError(f"{name} must not be negative, got {value}")


@dataclass(frozen=True)
class DayInput:
    """Financial inputs for one completed local day. ``None`` means the data is missing."""

    local_date: date
    remaining_budget_at_start: Decimal | None
    counted_spending: Decimal | None

    def __post_init__(self) -> None:
        _check_date(self.local_date, "local_date")
        _check_money(
            self.remaining_budget_at_start, "remaining_budget_at_start", allow_negative=True
        )
        _check_money(self.counted_spending, "counted_spending", allow_negative=False)


@dataclass(frozen=True)
class DayResult:
    """Recorded result for one completed day."""

    local_date: date
    allowance: Decimal | None
    counted_spending: Decimal | None
    outcome: Outcome
    streak_after: int
    awarded: tuple[Achievement, ...]


@dataclass(frozen=True)
class StreakState:
    """A user's streak state between evaluations."""

    current_streak: int = 0
    last_evaluated_date: date | None = None
    achievements: Mapping[Achievement, date] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if isinstance(self.current_streak, bool) or not isinstance(self.current_streak, int):
            raise TypeError("current_streak must be an int")
        if self.current_streak < 0:
            raise ValueError("current_streak must not be negative")
        if self.last_evaluated_date is not None:
            _check_date(self.last_evaluated_date, "last_evaluated_date")
        # Copy into a read-only view so a frozen state cannot be changed through the mapping.
        object.__setattr__(self, "achievements", MappingProxyType(dict(self.achievements)))


def days_remaining_in_period(local_date: date) -> int:
    """Days left in the calendar month containing ``local_date``, including that day."""
    _check_date(local_date, "local_date")
    days_in_month = calendar.monthrange(local_date.year, local_date.month)[1]
    return days_in_month - local_date.day + 1


def daily_allowance(remaining_budget: Decimal, local_date: date) -> Decimal:
    """Allowance for ``local_date``, rounded down to the cent."""
    _check_money(remaining_budget, "remaining_budget", allow_negative=False)
    if remaining_budget is None:
        raise TypeError("remaining_budget must be a Decimal, got NoneType")
    days = days_remaining_in_period(local_date)
    return (remaining_budget / days).quantize(CENT, rounding=ROUND_DOWN)


def evaluate_day(state: StreakState, day: DayInput) -> tuple[StreakState, DayResult | None]:
    """Evaluate one completed day.

    Returns the new state and the day's result. A day on or before the last evaluated day
    returns ``(state, None)`` unchanged. Raises ``ValueError`` if a day would be skipped.
    """
    last = state.last_evaluated_date
    if last is not None:
        if day.local_date <= last:
            return state, None
        expected = last + timedelta(days=1)
        if day.local_date != expected:
            raise ValueError(
                f"expected {expected.isoformat()} next, got {day.local_date.isoformat()}; "
                "days must be evaluated in order without gaps"
            )

    budget = day.remaining_budget_at_start
    spending = day.counted_spending
    allowance = None
    if budget is not None and budget >= 0:
        allowance = daily_allowance(budget, day.local_date)

    if budget is None or spending is None:
        outcome = Outcome.MISSING_DATA
    elif allowance is None:
        outcome = Outcome.NEGATIVE_BUDGET
    elif spending <= allowance:
        outcome = Outcome.WITHIN_ALLOWANCE
    else:
        outcome = Outcome.OVER_ALLOWANCE

    streak_after = state.current_streak + 1 if outcome.qualifies else 0
    awarded = tuple(a for a in Achievement if a not in state.achievements and streak_after >= a)
    achievements = {**state.achievements, **dict.fromkeys(awarded, day.local_date)}

    result = DayResult(
        local_date=day.local_date,
        allowance=allowance,
        counted_spending=spending,
        outcome=outcome,
        streak_after=streak_after,
        awarded=awarded,
    )
    return StreakState(streak_after, day.local_date, achievements), result


def evaluate_days(
    state: StreakState, days: Iterable[DayInput]
) -> tuple[StreakState, list[DayResult]]:
    """Evaluate days in order, skipping already-evaluated ones. Returns only new results."""
    results: list[DayResult] = []
    for day in days:
        state, result = evaluate_day(state, day)
        if result is not None:
            results.append(result)
    return state, results


def completed_local_dates(now: datetime, tz: tzinfo, last_evaluated: date | None) -> list[date]:
    """Local dates in ``tz`` that have fully ended by ``now`` and still need evaluation.

    With no previous evaluation, only the most recently completed day (yesterday) is
    returned. Dates are returned oldest first.
    """
    if not isinstance(now, datetime):
        raise TypeError(f"now must be a datetime, got {type(now).__name__}")
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    if last_evaluated is not None:
        _check_date(last_evaluated, "last_evaluated")

    yesterday = now.astimezone(tz).date() - timedelta(days=1)
    if last_evaluated is None:
        return [yesterday]
    pending = (yesterday - last_evaluated).days
    return [last_evaluated + timedelta(days=n) for n in range(1, pending + 1)]
