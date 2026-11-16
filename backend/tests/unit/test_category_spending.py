"""Synthetic FR-04 examples with independently calculated expected USD totals."""

import unittest
from dataclasses import FrozenInstanceError, replace
from datetime import date, datetime
from decimal import Decimal, localcontext

from backend.app.services.category_spending import (
    SpendingTransaction,
    calculate_category_spending,
)

START = date(2026, 11, 1)
END = date(2026, 12, 1)


def transaction(transaction_id="purchase-1", amount="10.00", **changes):
    values = dict(
        transaction_id=transaction_id,
        user_id="user-1",
        category_id="dining",
        effective_date=date(2026, 11, 15),
        amount=Decimal(amount),
    )
    values.update(changes)
    return SpendingTransaction(**values)


def total(transactions, **changes):
    values = dict(
        user_id="user-1", category_id="dining", period_start=START, period_end=END
    )
    values.update(changes)
    return calculate_category_spending(transactions, **values)


class CategorySpendingTests(unittest.TestCase):
    def test_empty_snapshot_returns_decimal_zero(self):
        result = total([])
        self.assertIsInstance(result, Decimal)
        self.assertEqual(result, Decimal("0.00"))

    def test_purchases_sum_exactly(self):
        self.assertEqual(
            total([transaction("a", "0.10"), transaction("b", "0.20")]),
            Decimal("0.30"),
        )

    def test_refund_reduces_spending(self):
        self.assertEqual(
            total([transaction(), transaction("refund", "-2.75", kind="refund")]),
            Decimal("7.25"),
        )

    def test_refunds_can_make_total_negative(self):
        self.assertEqual(
            total([transaction("refund", "-15.00", kind="refund")]),
            Decimal("-15.00"),
        )

    def test_transfers_and_card_payments_are_excluded(self):
        self.assertEqual(
            total([
                transaction("card-purchase", "25.00"),
                transaction("transfer", "100.00", kind="transfer"),
                transaction("payment", "25.00", kind="credit_card_payment"),
            ]),
            Decimal("25.00"),
        )

    def test_users_and_categories_are_isolated(self):
        self.assertEqual(
            total([
                transaction(),
                transaction(user_id="user-2"),
                transaction("other-category", category_id="groceries"),
            ]),
            Decimal("10.00"),
        )

    def test_no_matching_transactions_returns_zero(self):
        self.assertEqual(total([transaction(user_id="user-2")]), Decimal("0.00"))

    def test_period_is_start_inclusive_end_exclusive(self):
        self.assertEqual(
            total([
                transaction("before", effective_date=date(2026, 10, 31)),
                transaction("start", effective_date=START),
                transaction("last", effective_date=date(2026, 11, 30)),
                transaction("end", effective_date=END),
            ]),
            Decimal("20.00"),
        )

    def test_refund_uses_its_own_effective_period(self):
        self.assertEqual(
            total([
                transaction(),
                transaction("refund", "-5.00", kind="refund", effective_date=END),
            ]),
            Decimal("10.00"),
        )

    def test_pending_purchase_counts(self):
        self.assertEqual(total([transaction(pending=True)]), Decimal("10.00"))

    def test_posted_replaces_pending_with_its_updated_amount(self):
        pending = transaction("pending", pending=True)
        posted = transaction("posted", "12.50", pending_transaction_id="pending")
        self.assertEqual(total([pending, posted]), Decimal("12.50"))

    def test_posted_record_can_arrive_without_pending(self):
        self.assertEqual(
            total([transaction(pending_transaction_id="absent")]), Decimal("10.00")
        )

    def test_posted_category_supersedes_pending_category(self):
        pending = transaction("pending", pending=True)
        posted = transaction(
            "posted", category_id="groceries", pending_transaction_id="pending"
        )
        self.assertEqual(total([pending, posted]), Decimal("0.00"))
        self.assertEqual(
            total([pending, posted], category_id="groceries"), Decimal("10.00")
        )

    def test_posted_date_outside_period_suppresses_pending_inside(self):
        pending = transaction("pending", pending=True)
        posted = transaction("posted", effective_date=END, pending_transaction_id="pending")
        self.assertEqual(total([pending, posted]), Decimal("0.00"))

    def test_posted_date_inside_period_replaces_pending_outside(self):
        pending = transaction("pending", pending=True, effective_date=date(2026, 10, 31))
        posted = transaction("posted", pending_transaction_id="pending")
        self.assertEqual(total([pending, posted]), Decimal("10.00"))

    def test_posted_transfer_suppresses_pending_purchase(self):
        pending = transaction("pending", pending=True)
        posted = transaction("posted", kind="transfer", pending_transaction_id="pending")
        self.assertEqual(total([pending, posted]), Decimal("0.00"))

    def test_replacement_reference_is_scoped_to_user(self):
        pending = transaction("pending", pending=True)
        posted = transaction(
            "posted", user_id="user-2", pending_transaction_id="pending"
        )
        self.assertEqual(total([pending, posted]), Decimal("10.00"))

    def test_exact_duplicates_count_once(self):
        record = transaction()
        self.assertEqual(total([record, replace(record), record]), Decimal("10.00"))

    def test_duplicate_posted_replacement_counts_once(self):
        pending = transaction("pending", pending=True)
        posted = transaction("posted", pending_transaction_id="pending")
        self.assertEqual(total([pending, posted, posted]), Decimal("10.00"))

    def test_conflicting_duplicates_fail_in_either_order(self):
        records = [transaction(), transaction(amount="12.00")]
        for ordered in (records, list(reversed(records))):
            with self.subTest(ordered=ordered), self.assertRaises(ValueError):
                total(ordered)

    def test_multiple_replacements_are_rejected(self):
        with self.assertRaises(ValueError):
            total([
                transaction("a", pending_transaction_id="pending"),
                transaction("b", pending_transaction_id="pending"),
            ])

    def test_replacement_target_must_be_pending(self):
        with self.assertRaises(ValueError):
            total([transaction("a"), transaction("b", pending_transaction_id="a")])

    def test_input_order_does_not_change_result(self):
        records = [
            transaction("pending", pending=True),
            transaction("posted", "12.50", pending_transaction_id="pending"),
            transaction("refund", "-2.00", kind="refund"),
        ]
        self.assertEqual(total(records), Decimal("10.50"))
        self.assertEqual(total(reversed(records)), Decimal("10.50"))

    def test_generator_input_is_supported(self):
        self.assertEqual(total(transaction(str(i)) for i in range(3)), Decimal("30.00"))

    def test_inputs_are_unchanged(self):
        records = [transaction(), transaction("refund", "-1.00", kind="refund")]
        before = records.copy()
        total(records)
        self.assertEqual(records, before)
        with self.assertRaises(FrozenInstanceError):
            records[0].amount = Decimal("0.00")

    def test_invalid_amount_types_are_rejected(self):
        for amount in (10, 10.0, "10.00", None):
            with self.subTest(amount=amount), self.assertRaises(TypeError):
                replace(transaction(), amount=amount)

    def test_nonfinite_and_fractional_cent_amounts_are_rejected(self):
        for amount in ("NaN", "sNaN", "Infinity", "-Infinity", "1.001", "0.00001"):
            with self.subTest(amount=amount), self.assertRaises(ValueError):
                transaction(amount=amount)

    def test_invalid_amount_signs_are_rejected(self):
        for kind, amount in (
            ("refund", "1.00"),
            ("purchase", "-1.00"),
            ("transfer", "-1.00"),
            ("credit_card_payment", "-1.00"),
        ):
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                transaction(amount=amount, kind=kind)

    def test_zero_and_trailing_decimal_zeros_are_valid(self):
        self.assertEqual(
            total([transaction("a", "1.2300"), transaction("b", "0.00", kind="refund")]),
            Decimal("1.23"),
        )

    def test_invalid_kind_and_pending_flag_are_rejected(self):
        with self.assertRaises(ValueError):
            transaction(kind="unknown")
        with self.assertRaises(TypeError):
            transaction(pending=1)

    def test_invalid_identifiers_are_rejected(self):
        for field in ("transaction_id", "user_id", "category_id", "pending_transaction_id"):
            for value in ("", " ", None, 1):
                if field == "pending_transaction_id" and value is None:
                    continue
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    transaction(**{field: value})

    def test_invalid_transaction_date_is_rejected(self):
        for value in ("2026-11-15", None, datetime(2026, 11, 15)):
            with self.subTest(value=value), self.assertRaises(ValueError):
                transaction(effective_date=value)

    def test_invalid_replacement_references_are_rejected(self):
        with self.assertRaises(ValueError):
            transaction(pending=True, pending_transaction_id="other")
        with self.assertRaises(ValueError):
            transaction(pending_transaction_id="purchase-1")

    def test_invalid_periods_are_rejected(self):
        for start, end in (
            (START, START), (END, START), (None, END),
            (START, "2026-12-01"), (datetime(2026, 11, 1), END),
        ):
            with self.subTest(start=start, end=end), self.assertRaises(ValueError):
                total([], period_start=start, period_end=end)

    def test_invalid_query_identifiers_are_rejected(self):
        for field in ("user_id", "category_id"):
            with self.subTest(field=field), self.assertRaises(ValueError):
                total([], **{field: ""})

    def test_invalid_snapshot_record_is_rejected(self):
        with self.assertRaises(TypeError):
            total([{"amount": "10.00"}])

    def test_large_amounts_and_cancellation_preserve_cents(self):
        records = [
            transaction("a", "1000000000000000000000000000000.01"),
            transaction("b", "-1000000000000000000000000000000.00", kind="refund"),
        ]
        with localcontext() as context:
            context.prec = 4
            self.assertEqual(total(records), Decimal("0.01"))
            self.assertEqual(total(reversed(records)), Decimal("0.01"))


if __name__ == "__main__":
    unittest.main()
