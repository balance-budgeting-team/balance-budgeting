"""Unit tests for FR-07 budget threshold alerts (SYS-04) and FR-16 preferences.

All amounts are synthetic. Expected values were calculated by hand against a
$200.00 budget: 75% = $150.00, 80% = $160.00, 82% = $164.00, 90% = $180.00,
100% = $200.00, 103% = $206.00.
"""

from datetime import date
from decimal import Decimal

import pytest

from app.adapters.sms import SmsSendError
from app.services.budget_threshold_alerts import (
    AlertOutcome,
    AlertRecipient,
    AlertThreshold,
    CategoryPeriodKey,
    CategorySpending,
    evaluate_budget_threshold_alert,
    thresholds_reached,
)

WARNING = AlertThreshold.WARNING
LIMIT = AlertThreshold.LIMIT
SENT = AlertOutcome.SENT
SUPPRESSED = AlertOutcome.SUPPRESSED
NO_ALERT = AlertOutcome.NO_ALERT

BUDGET = Decimal("200.00")
PHONE = "+15555550100"  # fictional number
NOVEMBER = CategoryPeriodKey("user-1", "dining", date(2026, 11, 1))
DECEMBER = CategoryPeriodKey("user-1", "dining", date(2026, 12, 1))
GROCERIES = CategoryPeriodKey("user-1", "groceries", date(2026, 11, 1))

ENABLED = AlertRecipient(PHONE, proactive_alerts_enabled=True)
DISABLED = AlertRecipient(PHONE, proactive_alerts_enabled=False)

# FR-07 test method: spending moves from 75% to 82%, 90%, and 103%.
PROGRESSION = [
    Decimal("150.00"),  # 75%
    Decimal("164.00"),  # 82%
    Decimal("180.00"),  # 90%
    Decimal("206.00"),  # 103%
]

MESSAGE_82 = (
    "Balance alert: you've used 82% of your $200.00 Dining budget this month "
    "($164.00 spent)."
)
MESSAGE_103 = (
    "Balance alert: you've used 103% of your $200.00 Dining budget this month "
    "($206.00 spent)."
)


def spending(spent, key=NOVEMBER, budget=BUDGET, name="Dining"):
    return CategorySpending(
        key=key, category_name=name, budget_amount=budget, spent_amount=spent
    )


def run(amounts, store, sms, recipient=ENABLED, key=NOVEMBER):
    return [
        evaluate_budget_threshold_alert(spending(a, key), recipient, store, sms)
        for a in amounts
    ]


def test_progression_75_82_90_103_sends_exactly_two_alerts(store, sms):
    results = run(PROGRESSION, store, sms)

    assert [r.outcome for r in results] == [NO_ALERT, SENT, NO_ALERT, SENT]
    assert [r.threshold for r in results] == [None, WARNING, None, LIMIT]
    assert sms.sent == [(PHONE, MESSAGE_82), (PHONE, MESSAGE_103)]
    assert store.get_handled(NOVEMBER) == {WARNING, LIMIT}


def test_replaying_updates_sends_no_duplicates(store, sms):
    run(PROGRESSION, store, sms)

    for _ in range(5):
        replay = run(PROGRESSION, store, sms)
        assert all(r.outcome is NO_ALERT for r in replay)

    assert sms.sent == [(PHONE, MESSAGE_82), (PHONE, MESSAGE_103)]


def test_new_period_makes_thresholds_eligible_again(store, sms):
    run(PROGRESSION, store, sms, key=NOVEMBER)

    december = run(PROGRESSION, store, sms, key=DECEMBER)

    assert [r.outcome for r in december] == [NO_ALERT, SENT, NO_ALERT, SENT]
    assert [body for _, body in sms.sent] == [
        MESSAGE_82,
        MESSAGE_103,
        MESSAGE_82,
        MESSAGE_103,
    ]
    assert store.get_handled(NOVEMBER) == {WARNING, LIMIT}
    assert store.get_handled(DECEMBER) == {WARNING, LIMIT}


def test_jump_75_to_103_sends_only_100_alert(store, sms):
    results = run([Decimal("150.00"), Decimal("206.00")], store, sms)

    assert [r.outcome for r in results] == [NO_ALERT, SENT]
    assert results[1].threshold is LIMIT
    assert results[1].newly_handled == {WARNING, LIMIT}
    assert sms.sent == [(PHONE, MESSAGE_103)]

    later = run([Decimal("180.00"), Decimal("206.00")], store, sms)

    assert all(r.outcome is NO_ALERT for r in later)
    assert len(sms.sent) == 1


def test_disabled_alerts_send_nothing_and_suppress_thresholds(store, sms):
    [suppressed] = run([Decimal("164.00")], store, sms, recipient=DISABLED)

    assert suppressed.outcome is SUPPRESSED
    assert suppressed.threshold is WARNING
    assert sms.sent == []
    assert store.get_handled(NOVEMBER) == {WARNING}

    # After re-enabling, the 80% threshold crossed while disabled stays handled;
    # a later eligible threshold can still be submitted.
    after_80, after_100 = run([Decimal("180.00"), Decimal("206.00")], store, sms)

    assert after_80.outcome is NO_ALERT
    assert after_100.outcome is SENT
    assert after_100.threshold is LIMIT
    assert sms.sent == [(PHONE, MESSAGE_103)]


def test_disabled_alerts_send_nothing_for_full_progression(store, sms):
    results = run(PROGRESSION, store, sms, recipient=DISABLED)

    assert [r.outcome for r in results] == [NO_ALERT, SUPPRESSED, NO_ALERT, SUPPRESSED]
    assert sms.sent == []
    assert store.get_handled(NOVEMBER) == {WARNING, LIMIT}


@pytest.mark.parametrize(
    ("spent", "expected"),
    [
        (Decimal("150.00"), set()),
        (Decimal("159.99"), set()),
        (Decimal("160.00"), {WARNING}),
        (Decimal("199.99"), {WARNING}),
        (Decimal("200.00"), {WARNING, LIMIT}),
        (Decimal("206.00"), {WARNING, LIMIT}),
    ],
)
def test_threshold_boundaries(spent, expected):
    assert thresholds_reached(spent, BUDGET) == expected


def test_categories_are_tracked_independently(store, sms):
    evaluate_budget_threshold_alert(
        spending(Decimal("164.00"), NOVEMBER), ENABLED, store, sms
    )
    groceries = evaluate_budget_threshold_alert(
        spending(Decimal("164.00"), GROCERIES, name="Groceries"), ENABLED, store, sms
    )

    assert groceries.outcome is SENT
    assert groceries.threshold is WARNING
    assert [body for _, body in sms.sent] == [
        MESSAGE_82,
        "Balance alert: you've used 82% of your $200.00 Groceries budget this month "
        "($164.00 spent).",
    ]
    assert store.get_handled(NOVEMBER) == {WARNING}
    assert store.get_handled(GROCERIES) == {WARNING}


def test_sms_failure_leaves_threshold_unhandled(store, sms):
    sms.fail_next = True

    with pytest.raises(SmsSendError):
        evaluate_budget_threshold_alert(
            spending(Decimal("164.00")), ENABLED, store, sms
        )

    assert sms.sent == []
    assert store.get_handled(NOVEMBER) == frozenset()

    retry = evaluate_budget_threshold_alert(
        spending(Decimal("164.00")), ENABLED, store, sms
    )

    assert retry.outcome is SENT
    assert sms.sent == [(PHONE, MESSAGE_82)]


@pytest.mark.parametrize(
    ("spent", "budget", "error"),
    [
        (Decimal("164.00"), 200.0, TypeError),
        (164.0, BUDGET, TypeError),
        (Decimal("164.00"), 200, TypeError),
        (Decimal("164.00"), Decimal("-200.00"), ValueError),
        (Decimal("NaN"), BUDGET, ValueError),
        (Decimal("164.00"), Decimal("Infinity"), ValueError),
    ],
)
def test_invalid_amounts_rejected(spent, budget, error):
    with pytest.raises(error):
        spending(spent, budget=budget)
    with pytest.raises(error):
        thresholds_reached(spent, budget)


def test_zero_budget_alerts_on_any_positive_spending(store, sms):
    [result] = run_one(Decimal("0.01"), Decimal("0.00"), store, sms)

    assert result.outcome is SENT
    assert result.threshold is LIMIT
    assert result.newly_handled == {WARNING, LIMIT}
    assert sms.sent == [
        (
            PHONE,
            "Balance alert: you've spent $0.01 against your $0.00 Dining budget "
            "this month.",
        )
    ]


@pytest.mark.parametrize(
    ("spent", "budget"),
    [
        (Decimal("0.00"), BUDGET),
        (Decimal("-5.00"), BUDGET),  # net refunds
        (Decimal("0.00"), Decimal("0.00")),
    ],
)
def test_non_positive_spending_sends_nothing(spent, budget, store, sms):
    [result] = run_one(spent, budget, store, sms)

    assert result.outcome is NO_ALERT
    assert sms.sent == []
    assert store.get_handled(NOVEMBER) == frozenset()


def test_message_rounds_percentage_down_and_amounts_to_cents(store, sms):
    # $1,000.005 / $1,234.50 = 81.0048...%, shown as 81%; $1,000.005 shows as $1,000.01.
    run_one(Decimal("1000.005"), Decimal("1234.50"), store, sms)
    # $199.98 / $200.00 = 99.99%, shown as 99% rather than 100%.
    run_one(Decimal("199.98"), BUDGET, store, sms, key=GROCERIES)

    assert [body for _, body in sms.sent] == [
        "Balance alert: you've used 81% of your $1,234.50 Dining budget this month "
        "($1,000.01 spent).",
        "Balance alert: you've used 99% of your $200.00 Dining budget this month "
        "($199.98 spent).",
    ]


def run_one(spent, budget, store, sms, key=NOVEMBER):
    return [
        evaluate_budget_threshold_alert(
            spending(spent, key, budget=budget), ENABLED, store, sms
        )
    ]
