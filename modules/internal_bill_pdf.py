import os
import sys
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import stringWidth


PAGE_WIDTH, PAGE_HEIGHT = A4
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DISCLAIMER = "INTERNAL EXPENSE RECORD - NOT A SUPPLIER RECEIPT"


def _find_logo_path():
    executable_dir = os.path.dirname(os.path.abspath(sys.executable))
    extraction_dir = getattr(sys, "_MEIPASS", executable_dir)
    candidates = [
        os.path.join(PROJECT_ROOT, "assets", "tecklogics_logo_white.png"),
        os.path.join(executable_dir, "assets", "tecklogics_logo_white.png"),
        os.path.join(extraction_dir, "assets", "tecklogics_logo_white.png"),
        os.path.join(os.getcwd(), "assets", "tecklogics_logo_white.png"),
    ]
    return next((path for path in candidates if os.path.isfile(path)), None)


class InternalBillPDFGenerator:
    PAGE_MARGIN = 18
    COLUMN_GAP = 12
    ROW_GAP = 16
    INNER_MARGIN = 10
    ITEM_ROWS = 9
    TABLE_HEADER_HEIGHT = 14
    TABLE_ROW_HEIGHT = 11
    TABLE_TOTAL_HEIGHT = 14

    def __init__(self, logo_path=None):
        self.logo_path = logo_path or _find_logo_path()
        self._logo = None

    def _get_logo(self):
        if self._logo is None:
            if not self.logo_path or not os.path.isfile(self.logo_path):
                raise FileNotFoundError(
                    "The Tecklogics logo was not found in the assets folder."
                )
            self._logo = ImageReader(self.logo_path)
        return self._logo

    def generate_page(self, bills, filename):
        if len(bills) > 4:
            raise ValueError("An A4 bill sheet can contain at most four bills.")

        os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)
        c = canvas.Canvas(filename, pagesize=A4)
        c.setTitle("Internal Expense Records")
        c.setAuthor("Petty Cash Voucher System")

        slot_width = (
            PAGE_WIDTH - 2 * self.PAGE_MARGIN - self.COLUMN_GAP
        ) / 2
        slot_height = (
            PAGE_HEIGHT - 2 * self.PAGE_MARGIN - self.ROW_GAP
        ) / 2
        slots = {
            0: (self.PAGE_MARGIN, self.PAGE_MARGIN + slot_height + self.ROW_GAP),
            1: (
                self.PAGE_MARGIN + slot_width + self.COLUMN_GAP,
                self.PAGE_MARGIN + slot_height + self.ROW_GAP,
            ),
            2: (self.PAGE_MARGIN, self.PAGE_MARGIN),
            3: (self.PAGE_MARGIN + slot_width + self.COLUMN_GAP, self.PAGE_MARGIN),
        }
        bills_by_slot = {bill["slot"]: bill for bill in bills}

        for slot in range(4):
            x, y = slots[slot]
            self._draw_bill(
                c,
                x,
                y,
                slot_width,
                slot_height,
                bills_by_slot.get(slot),
            )

        c.save()

    def _draw_bill(self, c, x, y, width, height, bill):
        right = x + width
        top = y + height
        left_inside = x + self.INNER_MARGIN
        right_inside = right - self.INNER_MARGIN
        content_width = right_inside - left_inside

        c.setStrokeColor(colors.HexColor("#8B8B8B"))
        c.setLineWidth(0.65)
        c.rect(x, y, width, height)

        header_x = left_inside
        header_y = top - 52
        header_width = content_width
        header_height = 42
        self._draw_header_gradient(c, header_x, header_y, header_width, header_height)
        c.drawImage(
            self._get_logo(),
            header_x + 8,
            header_y + 7,
            width=28,
            height=28,
            preserveAspectRatio=True,
            mask="auto",
        )
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(
            header_x + header_width / 2,
            header_y + 25,
            "BILL",
        )
        c.setFont("Helvetica-Bold", 5.7)
        c.drawCentredString(
            header_x + header_width / 2,
            header_y + 11,
            DISCLAIMER,
        )

        bill = bill or {}
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 6.5)
        date_y = top - 65
        c.drawString(left_inside, date_y, "Date:")
        c.setFont("Helvetica", 6.5)
        date_text = self._format_date(bill.get("bill_date", ""))
        c.drawString(left_inside + 24, date_y, date_text)
        c.setStrokeColor(colors.black)
        c.setLineWidth(0.45)
        c.line(left_inside + 22, date_y - 3, left_inside + 91, date_y - 3)

        record_x = left_inside + content_width * 0.60
        c.setFont("Helvetica-Bold", 6.5)
        c.drawString(record_x, date_y, "Record No.:")
        c.setFont("Helvetica", 6.5)
        record_no = bill.get("record_no", "")
        c.drawString(record_x + 43, date_y, record_no)
        c.line(record_x + 42, date_y - 3, right_inside, date_y - 3)

        bill_to_y = top - 85
        c.setFont("Helvetica-Bold", 6.5)
        c.drawString(left_inside, bill_to_y, "Bill to:")
        c.setFont("Helvetica", 6.5)
        c.drawString(
            left_inside + 28,
            bill_to_y,
            self._fit_text(bill.get("bill_to", ""), "Helvetica", 6.5, content_width - 30),
        )
        c.line(left_inside + 27, bill_to_y - 3, right_inside, bill_to_y - 3)

        table_top = top - 99
        self._draw_items_table(c, left_inside, table_top, content_width, bill)

        table_height = (
            self.TABLE_HEADER_HEIGHT
            + self.ITEM_ROWS * self.TABLE_ROW_HEIGHT
            + self.TABLE_TOTAL_HEIGHT
        )
        total_box_y = table_top - table_height - 19
        c.setStrokeColor(colors.black)
        c.setLineWidth(0.55)
        c.rect(right_inside - 100, total_box_y, 100, 16)
        c.setFont("Helvetica-Bold", 6.5)
        c.drawString(right_inside - 95, total_box_y + 5, "Total:")
        c.setFont("Helvetica", 6.5)
        c.drawRightString(
            right_inside - 5,
            total_box_y + 5,
            self._format_money(bill.get("total", "")),
        )

        note_y = total_box_y - 15
        c.setFont("Helvetica-Bold", 6.5)
        c.drawString(left_inside, note_y, "Note:")
        c.setFont("Helvetica", 6.5)
        c.drawString(
            left_inside + 20,
            note_y,
            self._fit_text(bill.get("note", ""), "Helvetica", 6.5, content_width - 20),
        )
        c.line(left_inside, note_y - 3, right_inside, note_y - 3)

        approval_y = note_y - 31
        middle = left_inside + content_width / 2
        c.setLineWidth(0.45)
        c.line(left_inside + 2, approval_y, middle - 7, approval_y)
        c.line(middle + 7, approval_y, right_inside - 2, approval_y)
        c.setFont("Helvetica", 6)
        c.drawCentredString((left_inside + middle - 7) / 2, approval_y - 9, "Approved By")
        c.drawCentredString((middle + 7 + right_inside - 2) / 2, approval_y - 9, "Signature")

        c.setFont("Helvetica-Bold", 5.5)
        c.setFillColor(colors.HexColor("#263E86"))
        c.drawString(left_inside, y + 13, "TECKLOGICS")
        c.setFont("Helvetica", 5)
        c.setFillColor(colors.HexColor("#333333"))
        c.drawRightString(right_inside, y + 13, "INTERNAL EXPENSE RECORD")

    def _draw_header_gradient(self, c, x, y, width, height):
        steps = 48
        for step in range(steps):
            ratio = step / (steps - 1)
            color = colors.Color(
                0.015 + ratio * 0.10,
                0.015 + ratio * 0.17,
                0.16 + ratio * 0.38,
            )
            c.setFillColor(color)
            c.rect(
                x + width * step / steps,
                y,
                width / steps + 0.5,
                height,
                stroke=0,
                fill=1,
            )

    def _draw_items_table(self, c, left, top, width, bill):
        column_widths = [
            width * 0.14,
            width * 0.39,
            width * 0.16,
            width * 0.10,
            width * 0.21,
        ]
        column_x = [left]
        for column_width in column_widths:
            column_x.append(column_x[-1] + column_width)

        header_height = self.TABLE_HEADER_HEIGHT
        row_height = self.TABLE_ROW_HEIGHT
        total_height = self.TABLE_TOTAL_HEIGHT
        headers = ["Date", "Item Description", "Price", "Qty", "Total"]
        header_bottom = top - header_height

        c.setFillColor(colors.HexColor("#203A82"))
        c.rect(left, header_bottom, width, header_height, stroke=0, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 5.8)
        for index, label in enumerate(headers):
            c.drawCentredString(
                (column_x[index] + column_x[index + 1]) / 2,
                header_bottom + 4.5,
                label,
            )

        items = list(bill.get("items", []) or [])
        row_top = header_bottom
        c.setStrokeColor(colors.HexColor("#555555"))
        c.setLineWidth(0.4)
        for index in range(self.ITEM_ROWS):
            row_bottom = row_top - row_height
            c.rect(left, row_bottom, width, row_height)
            for boundary in column_x[1:-1]:
                c.line(boundary, row_bottom, boundary, row_top)

            if index < len(items):
                item = items[index]
                baseline = row_bottom + 3.3
                c.setFillColor(colors.black)
                c.setFont("Helvetica", 5.5)
                c.drawString(
                    column_x[0] + 2,
                    baseline,
                    self._format_date(bill.get("bill_date", "")),
                )
                c.drawString(
                    column_x[1] + 2,
                    baseline,
                    self._fit_text(
                        item.get("description", ""),
                        "Helvetica",
                        5.5,
                        column_widths[1] - 4,
                    ),
                )
                c.drawRightString(
                    column_x[3] - 2,
                    baseline,
                    self._format_money(item.get("unit_price", "")),
                )
                c.drawRightString(
                    column_x[4] - 2,
                    baseline,
                    self._format_quantity(item.get("quantity", "")),
                )
                c.drawRightString(
                    column_x[5] - 2,
                    baseline,
                    self._format_money(item.get("line_total", "")),
                )
            row_top = row_bottom

        total_bottom = row_top - total_height
        c.rect(left, total_bottom, width, total_height)
        for boundary in column_x[1:-1]:
            c.line(boundary, total_bottom, boundary, row_top)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 6)
        c.drawRightString(column_x[4] - 3, total_bottom + 4.2, "Total:")
        c.setFont("Helvetica-Bold", 6)
        c.drawRightString(
            column_x[5] - 2,
            total_bottom + 4.2,
            self._format_money(bill.get("total", "")),
        )

    @staticmethod
    def _format_date(value):
        if not value:
            return ""
        for date_format in ("%Y-%m-%d", "%d-%b-%Y", "%d-%B-%Y", "%d-%m-%Y"):
            try:
                return datetime.strptime(str(value).strip(), date_format).strftime("%d-%m-%Y")
            except ValueError:
                continue
        return str(value)

    @staticmethod
    def _format_money(value):
        if value in ("", None):
            return ""
        try:
            return f"{float(value):,.2f}"
        except (TypeError, ValueError):
            return str(value)

    @staticmethod
    def _format_quantity(value):
        if value in ("", None):
            return ""
        try:
            number = float(value)
        except (TypeError, ValueError):
            return str(value)
        if number.is_integer():
            return f"{int(number):,}"
        return f"{number:,.2f}".rstrip("0").rstrip(".")

    @staticmethod
    def _fit_text(value, font, font_size, max_width):
        text = str(value or "")
        if stringWidth(text, font, font_size) <= max_width:
            return text
        suffix = "..."
        while text and stringWidth(text + suffix, font, font_size) > max_width:
            text = text[:-1]
        return text + suffix if text else ""
