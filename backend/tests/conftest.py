"""Shared backend test fakes. No live provider credentials or network access."""

from collections.abc import Iterable

import pytest

from app.adapters.sms import SmsSendError
from app.services.budget_threshold_alerts import AlertThreshold, CategoryPeriodKey


class FakeSmsSender:
    """Records submitted messages; can simulate one provider rejection."""

    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []
        self.fail_next = False

    def send(self, to: str, body: str) -> None:
        if self.fail_next:
            self.fail_next = False
            raise SmsSendError("simulated provider rejection")
        self.sent.append((to, body))


class InMemoryHandledThresholdStore:
    def __init__(self) -> None:
        self._handled: dict[CategoryPeriodKey, frozenset[AlertThreshold]] = {}

    def get_handled(self, key: CategoryPeriodKey) -> frozenset[AlertThreshold]:
        return self._handled.get(key, frozenset())

    def mark_handled(
        self, key: CategoryPeriodKey, thresholds: Iterable[AlertThreshold]
    ) -> None:
        self._handled[key] = self.get_handled(key) | frozenset(thresholds)


@pytest.fixture
def sms() -> FakeSmsSender:
    return FakeSmsSender()


@pytest.fixture
def store() -> InMemoryHandledThresholdStore:
    return InMemoryHandledThresholdStore()
