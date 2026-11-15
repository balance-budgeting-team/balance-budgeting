"""Provider-agnostic SMS interface.

Services depend on this interface rather than on a particular SMS provider
client. Provider implementations will live alongside it; tests substitute fakes.
"""

from typing import Protocol


class SmsSendError(Exception):
    """The SMS provider did not accept the message for submission."""


class SmsSender(Protocol):
    def send(self, to: str, body: str) -> None:
        """Submit ``body`` to the phone number ``to``.

        Returns once the provider has accepted the message for submission.
        Raises ``SmsSendError`` if the provider rejects it or cannot be reached.
        """
        ...
