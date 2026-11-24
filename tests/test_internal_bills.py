import os
import tempfile
import unittest

import fitz

from modules.bill_manager import InternalBillManager
from modules.database import DatabaseManager
from modules.internal_bill_pdf import InternalBillPDFGenerator


class InternalBillTests(unittest.TestCase):
    def setUp(self):
        self.database = DatabaseManager(":memory:")
        self.manager = InternalBillManager(self.database)

    def tearDown(self):
        self.database.close()

    def create_bill(self, description):
        return self.manager.create_bill(
            bill_date="25-Nov-2026",
            bill_to="Office",
            note="No supplier receipt provided",
            items=[
                {
                    "description": description,
                    "unit_price": "12.50",
                    "quantity": "2",
                }
            ],
        )

    def test_bill_totals_persist_and_slots_cycle_in_groups_of_four(self):
        first_bill = self.create_bill("Stationery")
        self.assertEqual(first_bill["total"], 25.0)
        self.assertEqual(first_bill["record_no"], "IER-000001")
        self.assertEqual((first_bill["page_number"], first_bill["slot"]), (1, 0))

        for index in range(2, 5):
            bill = self.create_bill(f"Item {index}")
            self.assertEqual(bill["page_number"], 1)
            self.assertEqual(bill["slot"], index - 1)

        self.assertEqual(len(self.manager.get_page_bills(1)), 4)
        fifth_bill = self.create_bill("Next sheet")
        self.assertEqual((fifth_bill["page_number"], fifth_bill["slot"]), (2, 0))
        self.assertEqual(
            [bill["record_no"] for bill in self.manager.get_page_bills(2)],
            ["IER-000005"],
        )

    def test_incomplete_or_invalid_items_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "Complete the description"):
            self.manager.create_bill(
                bill_date="25-Nov-2026",
                bill_to="",
                note="",
                items=[{"description": "Pens", "unit_price": "", "quantity": "2"}],
            )

        with self.assertRaisesRegex(ValueError, "quantity must be greater"):
            self.manager.create_bill(
                bill_date="25-Nov-2026",
                bill_to="",
                note="",
                items=[{"description": "Pens", "unit_price": "1", "quantity": "0"}],
            )

    def test_description_suggestions_use_recent_saved_item_descriptions(self):
        self.manager.create_bill(
            "25-Nov-2026",
            "Office",
            "Stationery",
            [{"description": "Pens", "unit_price": "1.25", "quantity": "2"}],
        )
        self.manager.create_bill(
            "26-Nov-2026",
            "office",
            "Monthly supplies",
            [{"description": "Pens", "unit_price": "1.50", "quantity": "3"}],
        )

        suggestions = self.manager.get_description_suggestions()

        self.assertEqual(suggestions, ["Pens"])

    def test_pdf_contains_four_forms_and_marks_them_as_internal_records(self):
        bill = self.create_bill("Stationery")
        page_bills = self.manager.get_page_bills(bill["page_number"])

        with tempfile.TemporaryDirectory() as directory:
            filename = os.path.join(directory, "internal-bills.pdf")
            InternalBillPDFGenerator().generate_page(page_bills, filename)

            with fitz.open(filename) as document:
                self.assertEqual(len(document), 1)
                text = document[0].get_text()

        self.assertEqual(text.count("INTERNAL EXPENSE RECORD - NOT A SUPPLIER RECEIPT"), 4)
        self.assertEqual(text.count("BILL"), 4)
        self.assertEqual(text.count("IER-000001"), 1)
        self.assertIn("25-11-2026", text)


if __name__ == "__main__":
    unittest.main()
