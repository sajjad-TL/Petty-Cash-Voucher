from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from datetime import datetime
import os

A4_WIDTH, A4_HEIGHT = A4
VOUCHER_SLOT_HEIGHT = A4_HEIGHT / 2

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
DEFAULT_LOGO = os.path.join(PROJECT_ROOT, "logo.png")

MONTH_ABBR = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]


class PDFGenerator:
    """Generate petty cash vouchers on A4 (two per page: top / bottom)."""

    # Space between A4 half-slot edge and voucher border
    SLOT_MARGIN_TOP = 10
    SLOT_MARGIN_BOTTOM = 10
    SLOT_MARGIN_SIDE = 12

    # Padding inside voucher border
    INNER_PAD = 12

    # Extra space above/below header block
    HEADER_PAD_TOP = 14
    HEADER_PAD_BOTTOM = 12
    HEADER_HEIGHT = 50

    SECTION_GAP = 8
    PREP_BOX_HEIGHT = 42
    APPROVAL_BOX_HEIGHT = 50

    def __init__(self, logo_path=None):
        self.logo_path = logo_path or DEFAULT_LOGO
        self._set_dimensions(A4_WIDTH, VOUCHER_SLOT_HEIGHT)

    def _set_dimensions(self, width, height):
        self.width = width
        self.height = height

        self.voucher_left = self.SLOT_MARGIN_SIDE
        self.voucher_right = self.width - self.SLOT_MARGIN_SIDE
        self.voucher_bottom = self.SLOT_MARGIN_BOTTOM
        self.voucher_top = self.height - self.SLOT_MARGIN_TOP
        self.voucher_height = self.voucher_top - self.voucher_bottom

        self.content_left = self.voucher_left + self.INNER_PAD
        self.content_right = self.voucher_right - self.INNER_PAD
        self.content_bottom = self.voucher_bottom + self.INNER_PAD
        self.content_top = self.voucher_top - self.INNER_PAD
        self.content_width = self.content_right - self.content_left

    def generate(self, voucher, filename, slot=0):
        os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)
        c = canvas.Canvas(filename, pagesize=A4)
        c.setAuthor(voucher.get("prepared_by", ""))
        c.setTitle(f"Petty Cash Voucher - {voucher.get('voucher_no', '')}")
        self._draw_voucher_slot(c, voucher, slot)
        c.save()

    def generate_a4_batch(self, vouchers, filename):
        os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)
        if not vouchers:
            return

        c = canvas.Canvas(filename, pagesize=A4)
        c.setTitle("Petty Cash Vouchers")

        for index, voucher in enumerate(vouchers):
            slot = index % 2
            if index > 0 and slot == 0:
                c.showPage()
            self._draw_voucher_slot(c, voucher, slot)

        c.save()

    def _draw_voucher_slot(self, c, voucher, slot):
        y_base = VOUCHER_SLOT_HEIGHT if slot == 0 else 0

        c.saveState()
        c.translate(0, y_base)
        self._set_dimensions(A4_WIDTH, VOUCHER_SLOT_HEIGHT)
        self._draw_voucher(c, voucher)
        c.restoreState()

        if slot == 0:
            cut_y = VOUCHER_SLOT_HEIGHT
            c.setStrokeColor(colors.grey)
            c.setLineWidth(0.5)
            c.setDash(4, 3)
            c.line(self.SLOT_MARGIN_SIDE, cut_y, A4_WIDTH - self.SLOT_MARGIN_SIDE, cut_y)
            c.setDash()

    def _draw_voucher(self, c, voucher):
        self._draw_outer_border(c)

        header_top = self.content_top - self.HEADER_PAD_TOP
        header_bottom = header_top - self.HEADER_HEIGHT
        table_top = header_bottom - self.HEADER_PAD_BOTTOM

        table_bottom = (
            self.content_bottom
            + self.APPROVAL_BOX_HEIGHT
            + self.SECTION_GAP
            + self.PREP_BOX_HEIGHT
            + self.SECTION_GAP
        )

        self._draw_header(c, header_top, header_bottom, voucher)
        table_end = self._draw_expense_table(c, table_top, table_bottom, voucher)
        prep_bottom = self._draw_preparation_box(c, table_end - self.SECTION_GAP, voucher)
        self._draw_approval_box(c, prep_bottom - self.SECTION_GAP, voucher)

    @staticmethod
    def format_voucher_id(voucher_no):
        try:
            parts = str(voucher_no).split("-")
            if len(parts) >= 3 and len(parts[1]) == 6 and parts[1].isdigit():
                year = parts[1][:4]
                month = int(parts[1][4:6])
                number = int(parts[2])
                return f"PCV-{number:04d}/{MONTH_ABBR[month - 1]}-{year}"
        except (TypeError, ValueError, IndexError):
            pass
        return str(voucher_no)

    @staticmethod
    def format_date(value):
        if not value:
            return ""
        for fmt in ("%d-%b-%Y", "%d-%B-%Y", "%d-%m-%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(str(value).strip(), fmt).strftime("%d-%m-%Y")
            except ValueError:
                continue
        return str(value)

    def _draw_outer_border(self, c):
        c.setStrokeColor(colors.black)
        c.setLineWidth(1)
        c.rect(
            self.voucher_left,
            self.voucher_bottom,
            self.voucher_right - self.voucher_left,
            self.voucher_height,
        )

    def _draw_header(self, c, header_top, header_bottom, voucher):
        left = self.content_left
        right = self.content_right
        header_mid = (header_top + header_bottom) / 2

        if os.path.isfile(self.logo_path):
            try:
                c.drawImage(
                    ImageReader(self.logo_path),
                    left,
                    header_bottom + 4,
                    width=115,
                    height=42,
                    preserveAspectRatio=True,
                    mask="auto",
                )
            except Exception:
                pass

        c.setFont("Helvetica-Bold", 13)
        c.drawCentredString(self.width / 2, header_mid + 4, "PETTY CASH VOUCHER")

        box_width = 160
        box_height = 17
        box_x = right - box_width
        date_y = header_top - box_height
        voucher_y = date_y - box_height - 4

        self._draw_label_box(
            c, box_x, date_y, box_width, box_height,
            f"Date: {self.format_date(voucher.get('date', ''))}",
        )
        self._draw_label_box(
            c, box_x, voucher_y, box_width, box_height,
            f"Voucher ID: {self.format_voucher_id(voucher.get('voucher_no', ''))}",
        )

        c.setStrokeColor(colors.black)
        c.setLineWidth(0.6)
        c.line(self.content_left, header_bottom, self.content_right, header_bottom)

    def _draw_label_box(self, c, x, y, width, height, text):
        c.setStrokeColor(colors.black)
        c.setLineWidth(0.8)
        c.rect(x, y, width, height)
        c.setFont("Helvetica", 8)
        c.drawString(x + 6, y + 5, text)

    def _column_positions(self):
        left = self.content_left
        right = self.content_right
        width = self.content_width
        col2 = left + width * 0.50
        col3 = left + width * 0.80
        return left, col2, col3, right

    def _draw_expense_table(self, c, top, min_bottom, voucher):
        left, col2, col3, right = self._column_positions()
        min_rows = 5

        expenses = list(voucher.get("expenses", []) or [])
        while len(expenses) < min_rows:
            expenses.append({"purpose": "", "head": "", "amount": ""})

        # Header + data rows + total row
        row_count = len(expenses) + 2
        available = top - min_bottom
        row_height = max(17, min(22, available / row_count))

        y = top
        header_bottom = y - row_height
        self._draw_table_cells(c, y, header_bottom, left, col2, col3, right)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(left + 6, header_bottom + 6, "Purpose of Fund")
        c.drawString(col2 + 6, header_bottom + 6, "Expense Head")
        c.drawString(col3 + 6, header_bottom + 6, "Amount")

        y = header_bottom
        total = 0.0

        for row in expenses:
            if y - row_height < min_bottom + row_height:
                break
            row_top = y
            row_bottom = y - row_height
            self._draw_table_cells(c, row_top, row_bottom, left, col2, col3, right)

            purpose = str(row.get("purpose", "") or row.get("description", ""))
            head = str(row.get("head", "") or row.get("expense_head", ""))
            amount_raw = row.get("amount", "")
            amount_text = ""
            if amount_raw not in ("", None):
                try:
                    amount_val = float(str(amount_raw).replace(",", ""))
                    total += amount_val
                    amount_text = f"{amount_val:,.2f}"
                except (TypeError, ValueError):
                    amount_text = str(amount_raw)

            c.setFont("Helvetica", 8)
            c.drawString(left + 6, row_bottom + 6, purpose[:50])
            c.drawString(col2 + 6, row_bottom + 6, head[:30])
            c.drawString(col3 + 6, row_bottom + 6, amount_text)
            y = row_bottom

        display_total = self._resolve_total(voucher, total)
        total_top = y
        total_bottom = y - row_height
        self._draw_table_cells(c, total_top, total_bottom, left, col2, col3, right, amount_only=True)
        c.setFont("Helvetica-Bold", 8)
        c.drawRightString(col3 - 6, total_bottom + 6, "Total:")
        c.drawString(col3 + 6, total_bottom + 6, f"{display_total:,.2f}")

        c.setStrokeColor(colors.black)
        c.setLineWidth(0.6)
        c.line(left, top, left, total_bottom)
        c.line(right, top, right, total_bottom)
        c.line(col2, top, col2, total_bottom)
        c.line(col3, top, col3, total_bottom)

        return total_bottom

    def _draw_table_cells(self, c, top, bottom, left, col2, col3, right, amount_only=False):
        c.setStrokeColor(colors.black)
        c.setLineWidth(0.8)
        c.rect(left, bottom, right - left, top - bottom)
        if not amount_only:
            c.line(col2, bottom, col2, top)
        c.line(col3, bottom, col3, top)

    def _draw_preparation_box(self, c, top, voucher):
        left = self.content_left
        right = self.content_right
        box_height = self.PREP_BOX_HEIGHT
        bottom = top - box_height
        mid = left + self.content_width / 2

        c.setStrokeColor(colors.black)
        c.setLineWidth(0.8)
        c.rect(left, bottom, right - left, box_height)
        c.line(mid, bottom, mid, top)

        c.setFont("Helvetica", 8)
        c.drawString(left + 8, top - 15, f"Prepared By: {voucher.get('prepared_by', '')}")
        c.drawString(left + 8, top - 30, f"Date: {self.format_date(voucher.get('prepared_date', ''))}")
        c.drawString(mid + 8, top - 15, f"Proposed Bills/Refund Date: {self.format_date(voucher.get('proposed_date', ''))}")
        c.drawString(mid + 8, top - 30, "Signature: __________________")

        return bottom

    def _draw_approval_box(self, c, top, voucher):
        left = self.content_left
        right = self.content_right
        box_height = self.APPROVAL_BOX_HEIGHT
        bottom = top - box_height

        c.setStrokeColor(colors.black)
        c.setLineWidth(0.8)
        c.rect(left, bottom, right - left, box_height)

        c.setFont("Helvetica", 8)
        c.drawString(left + 8, top - 15, f"Petty Cash Issuer: {voucher.get('issuer_name', '')}")
        c.drawRightString(right - 8, top - 15, f"Date: {self.format_date(voucher.get('issuer_date', ''))}")
        c.drawString(left + 8, top - 31, "Approver Signature: __________________________")
        c.drawString(left + 8, top - 46, f"Approver Name: {voucher.get('approver_name', '')}")
        c.drawRightString(right - 8, top - 46, f"Date: {self.format_date(voucher.get('approver_date', ''))}")

        return bottom

    @staticmethod
    def _resolve_total(voucher, calculated_total):
        display_total = voucher.get("total", calculated_total)
        if isinstance(display_total, str):
            display_total = display_total.replace(",", "").strip()
        try:
            return float(display_total)
        except (TypeError, ValueError):
            return calculated_total
