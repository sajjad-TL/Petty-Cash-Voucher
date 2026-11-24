import math

from .voucher_manager import VoucherManager


class InternalBillManager:
    BILLS_PER_PAGE = 4
    MAX_ITEMS = 9

    def __init__(self, database):
        self.db = database

    def create_bill(self, bill_date, bill_to, note, items):
        parsed_date = VoucherManager.parse_date(bill_date)
        clean_items = []
        total = 0.0

        for row_number, item in enumerate(items, start=1):
            description = str(item.get("description", "")).strip()
            price_text = str(item.get("unit_price", "")).replace(",", "").strip()
            quantity_text = str(item.get("quantity", "")).replace(",", "").strip()

            if not description and not price_text and not quantity_text:
                continue
            if not description or not price_text or not quantity_text:
                raise ValueError(f"Complete the description, price, and quantity for item {row_number}.")

            try:
                unit_price = float(price_text)
                quantity = float(quantity_text)
            except ValueError as error:
                raise ValueError(f"Item {row_number} must have a valid price and quantity.") from error

            if not math.isfinite(unit_price) or unit_price < 0:
                raise ValueError(f"Item {row_number} price must be a non-negative number.")
            if not math.isfinite(quantity) or quantity <= 0:
                raise ValueError(f"Item {row_number} quantity must be greater than zero.")

            line_total = round(unit_price * quantity, 2)
            total += line_total
            clean_items.append({
                "description": description,
                "unit_price": unit_price,
                "quantity": quantity,
                "line_total": line_total,
            })

        if not clean_items:
            raise ValueError("Enter at least one expense item.")
        if len(clean_items) > self.MAX_ITEMS:
            raise ValueError(f"A bill can contain at most {self.MAX_ITEMS} items.")

        bill_id = self.db.save_internal_bill(
            parsed_date.isoformat(),
            str(bill_to or "").strip(),
            str(note or "").strip(),
            round(total, 2),
            clean_items,
        )
        page_number = (bill_id - 1) // self.BILLS_PER_PAGE + 1
        return {
            "id": bill_id,
            "record_no": f"IER-{bill_id:06d}",
            "page_number": page_number,
            "slot": (bill_id - 1) % self.BILLS_PER_PAGE,
            "bill_date": parsed_date.isoformat(),
            "bill_to": str(bill_to or "").strip(),
            "note": str(note or "").strip(),
            "total": round(total, 2),
            "items": clean_items,
        }

    def get_page_bills(self, page_number):
        if not isinstance(page_number, int) or page_number < 1:
            raise ValueError("Page number must be a positive integer.")

        bills = self.db.get_internal_bill_page(
            page_number,
            self.BILLS_PER_PAGE,
        )
        for bill in bills:
            bill["record_no"] = f"IER-{bill['id']:06d}"
            bill["page_number"] = page_number
            bill["slot"] = (bill["id"] - 1) % self.BILLS_PER_PAGE
        return bills

    def get_description_suggestions(self):
        suggestions = []
        seen_descriptions = set()
        for row in self.db.get_internal_bill_descriptions():
            description = row["description"].strip()
            description_key = description.casefold()
            if description and description_key not in seen_descriptions:
                seen_descriptions.add(description_key)
                suggestions.append(description)
        return suggestions
