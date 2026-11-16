"""Unit tests for budget period math and the Home spending summary."""

from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest

from app.services.budget_summary import (
    build_summary,
    days_left_including_today,
    period_bounds,
    progress_percent,
    safe_to_spend_today,
)

TZ = ZoneInfo("America/Indiana/Indianapolis")
# Wednesday, November 18, 2026 at noon.
WEDNESDAY = datetime(2026, 11, 18, 12, 0, tzinfo=TZ)


def at(*args: int) -> datetime:
    return datetime(*args, tzinfo=TZ)


class TestPeriodBounds:
    def test_daily_runs_midnight_to_midnight(self) -> None:
        assert period_bounds("daily", WEDNESDAY) == (
            at(2026, 11, 18),
            at(2026, 11, 19),
        )

    def test_weekly_starts_monday(self) -> None:
        assert period_bounds("weekly", WEDNESDAY) == (
            at(2026, 11, 16),
            at(2026, 11, 23),
        )

    def test_weekly_on_monday_midnight_is_start_of_that_week(self) -> None:
        start, _ = period_bounds("weekly", at(2026, 11, 16))
        assert start == at(2026, 11, 16)

    def test_weekly_on_sunday_belongs_to_the_week_before(self) -> None:
        start, end = period_bounds("weekly", at(2026, 11, 22, 23, 59))
        assert (start, end) == (at(2026, 11, 16), at(2026, 11, 23))

    def test_monthly_rolls_over_the_year(self) -> None:
        assert period_bounds("monthly", at(2026, 12, 15)) == (
            at(2026, 12, 1),
            at(2027, 1, 1),
        )

    def test_monthly_handles_february(self) -> None:
        assert period_bounds("monthly", at(2028, 2, 29)) == (
            at(2028, 2, 1),
            at(2028, 3, 1),
        )

    def test_week_across_daylight_saving_change_keeps_local_midnights(self) -> None:
        # US daylight saving time ends Sunday, November 1, 2026.
        start, end = period_bounds("weekly", at(2026, 10, 28, 9))
        assert (start.hour, end.hour) == (0, 0)
        assert start.utcoffset() != end.utcoffset()

    def test_rejects_naive_datetime(self) -> None:
        with pytest.raises(ValueError, match="timezone-aware"):
            period_bounds("weekly", datetime(2026, 11, 18))

    def test_rejects_unknown_period(self) -> None:
        with pytest.raises(ValueError, match="unknown budget period"):
            period_bounds("yearly", WEDNESDAY)


@pytest.mark.parametrize(
    ("period", "expected"),
    [("daily", 1), ("weekly", 5), ("monthly", 13)],
)
def test_days_left_includes_today(period: str, expected: int) -> None:
    assert days_left_including_today(period, WEDNESDAY) == expected


@pytest.mark.parametrize(
    ("spent", "amount", "expected"),
    [
        ("152.00", "350.00", 43),  # Figma F1-1
        ("152.00", "400.00", 38),  # Figma F1-4
        ("0.00", "350.00", 0),
        ("400.00", "350.00", 114),  # over budget can exceed 100
        ("1.00", "8.00", 13),  # 12.5 rounds half up
    ],
)
def test_progress_percent(spent: str, amount: str, expected: int) -> None:
    assert progress_percent(Decimal(spent), Decimal(amount)) == expected


def test_progress_percent_rejects_non_positive_budget() -> None:
    with pytest.raises(ValueError):
        progress_percent(Decimal("1"), Decimal("0"))


class TestSafeToSpendToday:
    def test_spreads_remaining_money_over_days_left(self) -> None:
        # ($350 - $152) / 5 days left (Wed through Sun)
        value = safe_to_spend_today(Decimal("350"), Decimal("152"), "weekly", WEDNESDAY)
        assert value == Decimal("39.60")

    def test_rounds_down_to_the_cent(self) -> None:
        # $100 over 3 days is 33.333...; never overstate what is safe.
        value = safe_to_spend_today(
            Decimal("100"), Decimal("0"), "weekly", at(2026, 11, 20, 9)
        )
        assert value == Decimal("33.33")

    def test_is_zero_when_over_budget(self) -> None:
        value = safe_to_spend_today(Decimal("350"), Decimal("400"), "weekly", WEDNESDAY)
        assert value == Decimal("0.00")

    def test_last_day_of_period_gets_all_remaining_money(self) -> None:
        value = safe_to_spend_today(
            Decimal("350"), Decimal("300"), "weekly", at(2026, 11, 22, 18)
        )
        assert value == Decimal("50.00")


def test_build_summary_matches_figma_review_values() -> None:
    summary = build_summary(
        budget_id=7,
        period="weekly",
        amount=Decimal("400"),
        spent=Decimal("152"),
        now=WEDNESDAY,
    )
    assert summary.budget_id == 7
    assert summary.amount == Decimal("400.00")
    assert summary.spent_so_far == Decimal("152.00")
    assert summary.progress_percent == 38
    assert summary.safe_to_spend_today == Decimal("49.60")
