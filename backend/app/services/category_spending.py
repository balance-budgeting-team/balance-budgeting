"""Aggregate a current transaction snapshot using FR-04 spending rules.

Callers normalize transaction kinds and supply dates and period boundaries.
This service performs no synchronization, persistence, or alert submission.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, localcontext


def _identifier(value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("identifiers must be nonempty strings")


@dataclass(frozen=True)
class SpendingTransaction:
    """Normalized USD transaction; refunds are negative, other kinds nonnegative.

    A posted record may reference its replaced pending ID even when that pending
    record is absent from the snapshot. IDs are scoped to a user.
    """

    transaction_id: str
    user_id: str
    category_id: str
    effective_date: date
    amount: Decimal
    kind: str = "purchase"
    pending: bool = False
    pending_transaction_id: str | None = None

    def __post_init__(self) -> None:
        for value in (self.transaction_id, self.user_id, self.category_id):
            _identifier(value)
        if type(self.effective_date) is not date:
            raise ValueError("effective_date must be a date, without a time")
        if not isinstance(self.amount, Decimal):
            raise TypeError("amount must be a Decimal")
        if not self.amount.is_finite():
            raise ValueError("amount must be finite")
        with localcontext() as context:
            context.prec = max(28, len(self.amount.as_tuple().digits), self.amount.adjusted() + 3)
            if self.amount != self.amount.quantize(Decimal("0.01")):
                raise ValueError("amount must contain whole cents")
        if self.kind not in ("purchase", "refund", "transfer", "credit_card_payment"):
            raise ValueError("unsupported transaction kind")
        if (self.kind == "refund" and self.amount > 0) or (
            self.kind != "refund" and self.amount < 0
        ):
            raise ValueError("refunds must be nonpositive; other amounts nonnegative")
        if type(self.pending) is not bool:
            raise TypeError("pending must be a bool")
        if self.pending_transaction_id is not None:
            _identifier(self.pending_transaction_id)
            if self.pending or self.pending_transaction_id == self.transaction_id:
                raise ValueError("only a posted record may replace a different pending ID")


def calculate_category_spending(
    transactions: Iterable[SpendingTransaction],
    user_id: str,
    category_id: str,
    period_start: date,
    period_end: date,
) -> Decimal:
    """Return net spending in [period_start, period_end), including pending buys.

    Exact duplicates count once; conflicting records and ambiguous replacements
    fail rather than guessing. Replacements are resolved before category/date
    filtering, using the posted record's date, category, kind, and amount.
    """
    _identifier(user_id)
    _identifier(category_id)
    if type(period_start) is not date or type(period_end) is not date:
        raise ValueError("period boundaries must be dates, without times")
    if period_start >= period_end:
        raise ValueError("period_start must precede period_end")

    unique: dict[tuple[str, str], SpendingTransaction] = {}
    for transaction in transactions:
        if not isinstance(transaction, SpendingTransaction):
            raise TypeError("transactions must contain SpendingTransaction records")
        key = (transaction.user_id, transaction.transaction_id)
        if key in unique and unique[key] != transaction:
            raise ValueError("conflicting records for the same user and transaction ID")
        unique[key] = transaction

    replaced: set[tuple[str, str]] = set()
    for transaction in unique.values():
        if transaction.pending_transaction_id is None:
            continue
        key = (transaction.user_id, transaction.pending_transaction_id)
        if key in replaced:
            raise ValueError("multiple posted records replace the same pending ID")
        if key in unique and not unique[key].pending:
            raise ValueError("replacement target must be pending")
        replaced.add(key)

    amounts = [
        transaction.amount
        for key, transaction in unique.items()
        if key not in replaced
        and transaction.user_id == user_id
        and transaction.category_id == category_id
        and period_start <= transaction.effective_date < period_end
        and transaction.kind in ("purchase", "refund")
    ]
    # Allow enough precision for every cent, including large totals and cancellation.
    with localcontext() as context:
        context.prec = max(28, max((a.adjusted() + 3 for a in amounts), default=0)) + len(
            str(len(amounts))
        )
        return sum(amounts, Decimal("0.00"))
