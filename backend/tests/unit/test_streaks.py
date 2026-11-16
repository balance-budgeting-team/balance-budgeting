"""Unit tests for the FR-13 streak and achievement engine."""

import json
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from app.services.streaks import (
    Achievement,
    DayInput,
    Outcome,
    StreakState,
    completed_local_dates,
    daily_allowance,
    days_remaining_in_period,
    evaluate_day,
    evaluate_days,
)

FIXTURE = Path(__file__).resolve().parents[3] / "tests/fixtures/streaks/fr13_40day.v1.json"
EASTERN = ZoneInfo("America/New_York")
PACIFIC = ZoneInfo("America/Los_Angeles")

D = Decimal


def run(days: list[tuple[str, str | None, str | None]], state: StreakState | None = None):
    """Evaluate (iso date, budget, spending) tuples from a fresh or given state."""
    inputs = [
        DayInput(
            date.fromisoformat(day),
            None if budget is None else D(budget),
            None if spent is None else D(spent),
        )
        for day, budget, spent in days
    ]
    return evaluate_days(state or StreakState(), inputs)


def qualifying_run(start: date, count: int) -> list[DayInput]:
    """``count`` consecutive days that each qualify with a generous budget and $0 spending."""
    return [DayInput(start + timedelta(days=n), D("1000.00"), D("0.00")) for n in range(count)]


# --- Allowance ---------------------------------------------------------------


def test_allowance_on_first_day_of_30_day_month_divides_by_30():
    assert days_remaining_in_period(date(2026, 9, 1)) == 30
    assert daily_allowance(D("300.00"), date(2026, 9, 1)) == D("10.00")


def test_allowance_on_last_day_of_month_is_whole_remaining_budget():
    assert days_remaining_in_period(date(2026, 10, 31)) == 1
    assert daily_allowance(D("42.17"), date(2026, 10, 31)) == D("42.17")


def test_allowance_in_leap_year_february_divides_by_29():
    assert days_remaining_in_period(date(2028, 2, 1)) == 29
    assert daily_allowance(D("290.00"), date(2028, 2, 1)) == D("10.00")
    assert days_remaining_in_period(date(2027, 2, 1)) == 28


def test_allowance_rounds_down_to_the_cent_and_that_value_is_judged():
    assert daily_allowance(D("100.00"), date(2026, 9, 1)) == D("3.33")

    _, [at_allowance] = run([("2026-09-01", "100.00", "3.33")])
    _, [one_cent_over] = run([("2026-09-01", "100.00", "3.34")])

    assert at_allowance.allowance == D("3.33")
    assert at_allowance.outcome is Outcome.WITHIN_ALLOWANCE
    assert one_cent_over.outcome is Outcome.OVER_ALLOWANCE


# --- Single-day evaluation ---------------------------------------------------


def test_spending_under_allowance_increments_streak():
    state, [result] = run([("2026-09-01", "300.00", "4.00")])
    assert result.outcome is Outcome.WITHIN_ALLOWANCE
    assert result.streak_after == state.current_streak == 1
    assert state.last_evaluated_date == date(2026, 9, 1)


def test_spending_equal_to_allowance_increments_streak():
    _, [result] = run([("2026-09-01", "300.00", "10.00")])
    assert result.outcome is Outcome.WITHIN_ALLOWANCE
    assert result.streak_after == 1


def test_spending_one_cent_over_resets_streak_to_zero():
    state, results = run([("2026-09-01", "300.00", "10.00"), ("2026-09-02", "290.00", "10.01")])
    assert results[-1].outcome is Outcome.OVER_ALLOWANCE
    assert state.current_streak == 0


@pytest.mark.parametrize(("budget", "spent"), [("290.00", None), (None, "0.00"), (None, None)])
def test_missing_financial_data_resets_streak(budget, spent):
    state, results = run([("2026-09-01", "300.00", "0.00"), ("2026-09-02", budget, spent)])
    assert results[-1].outcome is Outcome.MISSING_DATA
    assert state.current_streak == 0


def test_missing_spending_still_records_allowance_from_known_budget():
    _, [result] = run([("2026-09-01", "300.00", None)])
    assert result.allowance == D("10.00")
    assert result.outcome is Outcome.MISSING_DATA


def test_negative_remaining_budget_resets_even_with_no_spending():
    state, results = run([("2026-09-01", "300.00", "0.00"), ("2026-09-02", "-0.01", "0.00")])
    assert results[-1].outcome is Outcome.NEGATIVE_BUDGET
    assert results[-1].allowance is None
    assert state.current_streak == 0


def test_zero_remaining_budget_qualifies_only_with_zero_spending():
    # Team decision point: a $0 budget gives a $0 allowance, and $0 spent still earns credit.
    _, [no_spending] = run([("2026-09-01", "0.00", "0.00")])
    _, [one_cent] = run([("2026-09-01", "0.00", "0.01")])

    assert no_spending.allowance == D("0.00")
    assert no_spending.outcome is Outcome.WITHIN_ALLOWANCE
    assert no_spending.streak_after == 1
    assert one_cent.outcome is Outcome.OVER_ALLOWANCE


def test_recorded_allowance_comes_from_start_of_day_budget():
    _, [result] = run([("2026-09-07", "200.00", "5.00")])
    assert result.allowance == D("8.33")
    assert result.counted_spending == D("5.00")


# --- Achievements ------------------------------------------------------------


def test_three_day_achievement_awarded_on_third_day_only():
    state, results = evaluate_days(StreakState(), qualifying_run(date(2026, 9, 1), 5))
    assert [r.awarded for r in results] == [(), (), (Achievement.STREAK_3,), (), ()]
    assert state.achievements == {Achievement.STREAK_3: date(2026, 9, 3)}


def test_long_run_earns_each_achievement_once_at_its_threshold():
    start = date(2026, 9, 1)
    state, results = evaluate_days(StreakState(), qualifying_run(start, 31))
    awarded_on = {r.streak_after: r.awarded for r in results if r.awarded}
    assert awarded_on == {
        3: (Achievement.STREAK_3,),
        7: (Achievement.STREAK_7,),
        30: (Achievement.STREAK_30,),
    }
    assert state.achievements == {
        Achievement.STREAK_3: start + timedelta(days=2),
        Achievement.STREAK_7: start + timedelta(days=6),
        Achievement.STREAK_30: start + timedelta(days=29),
    }


def test_achievements_persist_after_reset_and_are_not_reawarded():
    state, _ = evaluate_days(StreakState(), qualifying_run(date(2026, 9, 1), 3))
    state, [reset] = evaluate_days(state, [DayInput(date(2026, 9, 4), D("270.00"), D("99.00"))])
    assert reset.streak_after == 0
    assert Achievement.STREAK_3 in state.achievements

    state, results = evaluate_days(state, qualifying_run(date(2026, 9, 5), 3))
    assert results[-1].streak_after == 3
    assert all(r.awarded == () for r in results)
    assert state.achievements == {Achievement.STREAK_3: date(2026, 9, 3)}


def test_twenty_nine_day_streak_does_not_earn_thirty_day_achievement():
    state, _ = evaluate_days(StreakState(), qualifying_run(date(2026, 9, 1), 29))
    assert state.current_streak == 29
    assert Achievement.STREAK_30 not in state.achievements


# --- SDP 40-day fixture ------------------------------------------------------


def load_fixture() -> dict:
    with FIXTURE.open(encoding="utf-8") as handle:
        return json.load(handle)


def test_fixture_is_versioned_and_covers_forty_days():
    fixture = load_fixture()
    assert fixture["version"] == 1
    assert fixture["requirement"] == "FR-13"
    assert [day["day"] for day in fixture["days"]] == list(range(1, 41))


@pytest.mark.parametrize("tz", [EASTERN, PACIFIC], ids=["eastern", "pacific"])
def test_forty_day_fixture_with_mocked_clock(tz):
    fixture = load_fixture()
    state = StreakState()

    for day in fixture["days"]:
        local_date = date.fromisoformat(day["local_date"])
        # The mocked clock reads one minute after the user's local midnight ending that day.
        next_midnight = datetime.combine(local_date + timedelta(days=1), datetime.min.time(), tz)
        now = (next_midnight + timedelta(minutes=1)).astimezone(UTC)

        assert completed_local_dates(now, tz, state.last_evaluated_date) == [local_date]

        state, result = evaluate_day(
            state,
            DayInput(local_date, D(day["remaining_budget_at_start"]), D(day["counted_spending"])),
        )
        expected = day["expected"]
        assert result is not None
        assert days_remaining_in_period(local_date) == expected["days_remaining"]
        assert result.allowance == D(expected["allowance"]), day["day"]
        assert result.outcome.value == expected["outcome"], day["day"]
        assert result.streak_after == expected["streak_after"], day["day"]
        assert [int(a) for a in result.awarded] == expected["awarded"], day["day"]

    assert state.current_streak == 34
    assert state.achievements == {
        Achievement.STREAK_3: date(2026, 9, 3),
        Achievement.STREAK_7: date(2026, 9, 13),
        Achievement.STREAK_30: date(2026, 10, 6),
    }


def fixture_inputs() -> list[DayInput]:
    return [
        DayInput(
            date.fromisoformat(d["local_date"]),
            D(d["remaining_budget_at_start"]),
            D(d["counted_spending"]),
        )
        for d in load_fixture()["days"]
    ]


# --- Replays and late data ---------------------------------------------------


def test_replaying_a_day_changes_nothing():
    state, _ = run([("2026-09-01", "300.00", "0.00"), ("2026-09-02", "290.00", "0.00")])
    replayed, result = evaluate_day(state, DayInput(date(2026, 9, 2), D("290.00"), D("0.00")))
    assert result is None
    assert replayed is state


def test_replaying_entire_forty_day_run_is_a_no_op():
    first, results = evaluate_days(StreakState(), fixture_inputs())
    second, replay_results = evaluate_days(first, fixture_inputs())
    assert len(results) == 40
    assert replay_results == []
    assert second == first


def test_late_transaction_does_not_change_completed_day():
    state, _ = evaluate_days(StreakState(), fixture_inputs())
    # Day 10 resubmitted after a late $500 transaction was imported.
    late, result = evaluate_day(state, DayInput(date(2026, 9, 10), D("185.00"), D("505.00")))
    assert result is None
    assert late == state


def test_next_day_allowance_uses_updated_budget_after_late_transaction():
    state, [day_one] = run([("2026-09-01", "300.00", "10.00")])
    # A late $40.00 day-1 transaction lowers the budget the caller supplies for day 2:
    # 300.00 - 10.00 - 40.00 = 250.00; 250.00 / 29 = 8.620... -> 8.62.
    _, [within] = run([("2026-09-02", "250.00", "8.62")], state)
    _, [over] = run([("2026-09-02", "250.00", "8.63")], state)

    assert day_one.streak_after == 1
    assert within.allowance == D("8.62")
    assert within.streak_after == 2
    assert over.outcome is Outcome.OVER_ALLOWANCE


# --- Time zones --------------------------------------------------------------


def test_same_instant_completes_day_in_eastern_but_not_pacific():
    now = datetime(2026, 9, 2, 5, 30, tzinfo=UTC)  # 01:30 EDT / 22:30 PDT on Sep 1
    last = date(2026, 8, 31)
    assert completed_local_dates(now, EASTERN, last) == [date(2026, 9, 1)]
    assert completed_local_dates(now, PACIFIC, last) == []


@pytest.mark.parametrize(
    ("tz", "oct_31_ends", "nov_1_ends"),
    [
        # Oct 31 ends at local midnight under daylight time; Nov 1 (25 hours) ends under standard.
        (EASTERN, datetime(2026, 11, 1, 4, tzinfo=UTC), datetime(2026, 11, 2, 5, tzinfo=UTC)),
        (PACIFIC, datetime(2026, 11, 1, 7, tzinfo=UTC), datetime(2026, 11, 2, 8, tzinfo=UTC)),
    ],
    ids=["eastern", "pacific"],
)
def test_completed_dates_across_dst_fall_back(tz, oct_31_ends, nov_1_ends):
    assert nov_1_ends - oct_31_ends == timedelta(hours=25)

    # Exact boundaries: one microsecond before each local midnight the day is still open.
    tick = timedelta(microseconds=1)
    assert completed_local_dates(oct_31_ends - tick, tz, date(2026, 10, 30)) == []
    assert completed_local_dates(oct_31_ends, tz, date(2026, 10, 30)) == [date(2026, 10, 31)]
    assert completed_local_dates(nov_1_ends - tick, tz, date(2026, 10, 31)) == []
    assert completed_local_dates(nov_1_ends, tz, date(2026, 10, 31)) == [date(2026, 11, 1)]

    # A job polling every minute from Oct 31 to Nov 3 UTC sees each date exactly once,
    # at the first minute on or after the local midnight ending it.
    first_seen: dict[date, list[datetime]] = {}
    last = date(2026, 10, 30)
    now = datetime(2026, 10, 31, tzinfo=UTC)
    while now < datetime(2026, 11, 3, tzinfo=UTC):
        for completed in completed_local_dates(now, tz, last):
            first_seen.setdefault(completed, []).append(now)
            last = completed
        now += timedelta(minutes=1)

    assert first_seen[date(2026, 10, 31)] == [oct_31_ends]
    assert first_seen[date(2026, 11, 1)] == [nov_1_ends]
    assert all(len(instants) == 1 for instants in first_seen.values())


def test_first_run_returns_only_yesterday():
    now = datetime(2026, 9, 10, 12, tzinfo=UTC)
    assert completed_local_dates(now, EASTERN, None) == [date(2026, 9, 9)]


def test_missed_job_runs_return_each_missed_day_in_order():
    now = datetime(2026, 9, 10, 12, tzinfo=UTC)
    assert completed_local_dates(now, EASTERN, date(2026, 9, 6)) == [
        date(2026, 9, 7),
        date(2026, 9, 8),
        date(2026, 9, 9),
    ]
    assert completed_local_dates(now, EASTERN, date(2026, 9, 9)) == []


def test_completed_dates_rejects_naive_datetime():
    with pytest.raises(ValueError, match="timezone-aware"):
        completed_local_dates(datetime(2026, 9, 10, 12), EASTERN, None)


# --- Ordering and input validation -------------------------------------------


def test_skipped_day_raises_and_leaves_state_unchanged():
    state, _ = run([("2026-11-01", "300.00", "0.00")])
    with pytest.raises(ValueError, match=r"expected 2026-11-02 next, got 2026-11-03"):
        evaluate_day(state, DayInput(date(2026, 11, 3), D("290.00"), D("0.00")))
    assert state.last_evaluated_date == date(2026, 11, 1)
    assert state.current_streak == 1


def test_negative_spending_is_rejected():
    with pytest.raises(ValueError, match="counted_spending must not be negative"):
        DayInput(date(2026, 9, 1), D("300.00"), D("-1.00"))


@pytest.mark.parametrize(
    "kwargs",
    [
        {"remaining_budget_at_start": 300.0, "counted_spending": D("1.00")},
        {"remaining_budget_at_start": D("300.00"), "counted_spending": 1.0},
        {"remaining_budget_at_start": D("300.00"), "counted_spending": 1},
    ],
    ids=["float-budget", "float-spending", "int-spending"],
)
def test_non_decimal_money_is_rejected(kwargs):
    with pytest.raises(TypeError, match="must be a Decimal"):
        DayInput(date(2026, 9, 1), **kwargs)


@pytest.mark.parametrize("value", ["NaN", "Infinity"])
def test_non_finite_money_is_rejected(value):
    with pytest.raises(ValueError, match="must be finite"):
        DayInput(date(2026, 9, 1), D("300.00"), D(value))


def test_datetime_is_not_accepted_as_local_date():
    with pytest.raises(TypeError, match=r"local_date must be a datetime\.date"):
        DayInput(datetime(2026, 9, 1, 12), D("300.00"), D("0.00"))


def test_state_achievements_cannot_be_mutated_through_the_mapping():
    source = {Achievement.STREAK_3: date(2026, 9, 3)}
    state = StreakState(3, date(2026, 9, 3), source)
    source[Achievement.STREAK_7] = date(2026, 9, 7)
    assert Achievement.STREAK_7 not in state.achievements
    with pytest.raises(TypeError):
        state.achievements[Achievement.STREAK_7] = date(2026, 9, 7)  # type: ignore[index]
