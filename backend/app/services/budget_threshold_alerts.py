"""Budget threshold alerts (FR-07, SYS-04), honoring FR-16 alert preferences.

Decides whether an 80% or 100% budget alert should be submitted for one
category in one budget period, and records which thresholds have been handled.

Each threshold is handled at most once per category per period. If a single
update reaches both thresholds, only the 100% alert is submitted and both are
marked handled. While proactive alerts are disabled, newly reached thresholds
are marked handled without sending, so re-enabling alerts never produces stale
alerts for thresholds crossed earlier in the period.

Counted category spending is calculated elsewhere (FR-04, FR-10) and passed in.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal
from enum import Enum, IntEnum
from typing import Protocol

from app.adapters.sms import SmsSender

_CENT = Decimal("0.01")


class AlertThreshold(IntEnum):
    """Budget thresholds, as a percentage of the category budget."""

    WARNING = 80
    LIMIT = 100


@dataclass(frozen=True)
class CategoryPeriodKey:
    """Identifies one category's budget in one monthly period."""

    user_id: str
    category_id: str
    period_start: date  # first day of the budget period


@dataclass(frozen=True)
class CategorySpending:
    key: CategoryPeriodKey
    category_name: str
    budget_amount: Decimal  # USD
    spent_amount: Decimal  # counted category spending, USD

    def __post_init__(self) -> None:
        _validate_amounts(self.spent_amount, self.budget_amount)


@dataclass(frozen=True)
class AlertRecipient:
    phone_number: str  # verified number (FR-14)
    proactive_alerts_enabled: bool  # FR-16


class AlertOutcome(Enum):
    SENT = "sent"
    SUPPRESSED = "suppressed"  # threshold newly reached, but alerts are disabled
    NO_ALERT = "no_alert"


@dataclass(frozen=True)
class ThresholdAlertResult:
    outcome: AlertOutcome
    threshold: AlertThreshold | None  # the threshold sent or suppressed
    newly_handled: frozenset[AlertThreshold]


class HandledThresholdStore(Protocol):
    def get_handled(self, key: CategoryPeriodKey) -> frozenset[AlertThreshold]:
        """Return the thresholds already handled for ``key``."""
        ...

    def mark_handled(
        self, key: CategoryPeriodKey, thresholds: Iterable[AlertThreshold]
    ) -> None:
        """Add ``thresholds`` to the handled set for ``key``."""
        ...


def _validate_amounts(spent: Decimal, budget: Decimal) -> None:
    for name, value in (("spent", spent), ("budget", budget)):
        if not isinstance(value, Decimal):
            raise TypeError(f"{name} must be a Decimal, not {type(value).__name__}")
        if not value.is_finite():
            raise ValueError(f"{name} must be a finite amount")
    if budget < 0:
        raise ValueError("budget must not be negative")


def thresholds_reached(spent: Decimal, budget: Decimal) -> frozenset[AlertThreshold]:
    """Return every threshold that ``spent`` has reached for ``budget``.

    Uses exact Decimal comparisons (no division or rounding). Zero or negative
    spending reaches no threshold; any positive spending reaches every threshold
    of a $0 budget.
    """
    _validate_amounts(spent, budget)
    if spent <= 0:
        return frozenset()
    return frozenset(t for t in AlertThreshold if spent * 100 >= budget * t)


def select_alert_threshold(
    reached: frozenset[AlertThreshold], handled: frozenset[AlertThreshold]
) -> AlertThreshold | None:
    """Return the highest reached threshold not yet handled, if any."""
    eligible = reached - handled
    return max(eligible) if eligible else None


def _usd(amount: Decimal) -> str:
    return f"${amount.quantize(_CENT, rounding=ROUND_HALF_UP):,}"


def format_alert_message(spending: CategorySpending, threshold: AlertThreshold) -> str:
    """Build the SMS body. Contains no account numbers or credentials (NFR-01)."""
    budget = spending.budget_amount
    spent = spending.spent_amount
    if budget == 0:
        return (
            f"Balance alert: you've spent {_usd(spent)} against your "
            f"{_usd(budget)} {spending.category_name} budget this month."
        )
    # Round the percentage down so that, e.g., 99.99% is never shown as 100%.
    percent = (spent * 100 / budget).to_integral_value(rounding=ROUND_DOWN)
    return (
        f"Balance alert: you've used {percent}% of your {_usd(budget)} "
        f"{spending.category_name} budget this month ({_usd(spent)} spent)."
    )


def evaluate_budget_threshold_alert(
    spending: CategorySpending,
    recipient: AlertRecipient,
    store: HandledThresholdStore,
    sms: SmsSender,
) -> ThresholdAlertResult:
    """Submit at most one threshold alert for the category's current spending.

    Thresholds are marked handled only after the SMS provider accepts the
    message. If ``sms.send`` raises ``SmsSendError``, the error propagates and
    nothing is marked, so a later evaluation can retry the alert.
    """
    handled = store.get_handled(spending.key)
    reached = thresholds_reached(spending.spent_amount, spending.budget_amount)
    threshold = select_alert_threshold(reached, handled)
    if threshold is None:
        return ThresholdAlertResult(AlertOutcome.NO_ALERT, None, frozenset())

    newly_handled = reached - handled
    if not recipient.proactive_alerts_enabled:
        store.mark_handled(spending.key, newly_handled)
        return ThresholdAlertResult(AlertOutcome.SUPPRESSED, threshold, newly_handled)

    sms.send(recipient.phone_number, format_alert_message(spending, threshold))
    store.mark_handled(spending.key, newly_handled)
    return ThresholdAlertResult(AlertOutcome.SENT, threshold, newly_handled)
