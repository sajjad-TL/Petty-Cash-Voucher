import unittest
from datetime import date

from modules.database import DatabaseManager
from modules.voucher_manager import VoucherManager


class VoucherHistoryTests(unittest.TestCase):
    def setUp(self):
        self.database = DatabaseManager(":memory:")
        self.voucher = VoucherManager(self.database)

    def tearDown(self):
        self.database.close()

    def save_voucher(self, voucher_no, voucher_date, amount):
        self.voucher.save_voucher(
            voucher_no=voucher_no,
            voucher_date=voucher_date,
            total=amount,
            prepared_by="Test",
            approved_by="Approver",
            issuer="Issuer",
            proposed_date=voucher_date,
            prepared_date=voucher_date,
            issuer_date=voucher_date,
            approver_date=voucher_date,
            expenses=[
                {
                    "purpose": "Groceries",
                    "expense_head": "Food",
                    "amount": amount,
                }
            ],
        )

    def test_date_range_report_includes_vouchers_salary_and_budget(self):
        self.save_voucher("PCV-202611-0001", "05-Nov-2026", 2500)
        self.save_voucher("PCV-202610-0001", "31-Oct-2026", 4000)

        report = self.voucher.get_expense_report("2026-11-01", "2026-11-30")

        self.assertEqual(report["voucher_expenses"], 2500)
        self.assertEqual(report["salary_total"], 12000)
        self.assertEqual(report["total_expenses"], 14500)
        self.assertEqual(report["budget_total"], 60000)
        self.assertEqual(report["remaining_budget"], 45500)
        self.assertEqual(len(report["rows"]), 2)

    def test_settings_are_saved_and_used_by_report(self):
        self.voucher.set_monthly_budget(70000)
        self.voucher.set_cook_salary(15000)

        report = self.voucher.get_expense_report("01-Nov-2026", "2026-12-01")

        self.assertEqual(report["budget_total"], 140000)
        self.assertEqual(report["salary_total"], 30000)

    def test_month_end_closure_is_idempotent_archive_snapshot(self):
        self.save_voucher("PCV-202610-0001", "31-Oct-2026", 3500)

        closed = self.voucher.close_elapsed_months(date(2026, 11, 1))
        snapshot = self.database.fetchone(
            "SELECT * FROM month_closures WHERE month=?",
            ("2026-10",),
        )
        self.save_voucher("PCV-202610-0002", "31-Oct-2026", 1000)
        self.voucher.close_elapsed_months(date(2026, 11, 1))
        unchanged_snapshot = self.database.fetchone(
            "SELECT * FROM month_closures WHERE month=?",
            ("2026-10",),
        )

        self.assertIn("2026-10", closed)
        self.assertEqual(snapshot["voucher_count"], 1)
        self.assertEqual(snapshot["voucher_total"], 3500)
        self.assertEqual(unchanged_snapshot["voucher_count"], 1)
        self.assertEqual(unchanged_snapshot["voucher_total"], 3500)
        self.assertEqual(
            len(self.voucher.get_vouchers_for_period("2026-10-01", "2026-10-31")),
            2,
        )

    def test_invalid_date_range_is_rejected(self):
        with self.assertRaises(ValueError):
            self.voucher.get_vouchers_for_period("2026-11-30", "2026-11-01")


if __name__ == "__main__":
    unittest.main()
