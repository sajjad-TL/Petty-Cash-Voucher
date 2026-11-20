from datetime import date, datetime, timedelta
from modules.database import DatabaseManager


class VoucherManager:
    DEFAULT_MONTHLY_BUDGET = 60000
    DEFAULT_COOK_SALARY = 12000

    def __init__(self, database=None):
        self.db = database if database is not None else DatabaseManager()

    @staticmethod
    def parse_date(value):
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value

        value = str(value).strip()
        for date_format in (
            "%Y-%m-%d",
            "%d-%b-%Y",
            "%d-%B-%Y",
            "%d-%m-%Y",
        ):
            try:
                return datetime.strptime(value, date_format).date()
            except ValueError:
                continue
        raise ValueError("Enter dates as YYYY-MM-DD or DD-Mon-YYYY.")

    def get_monthly_budget(self):
        value = self.db.get_setting(
            "monthly_budget",
            self.DEFAULT_MONTHLY_BUDGET,
        )
        return float(value)

    def get_cook_salary(self):
        value = self.db.get_setting(
            "cook_salary",
            self.DEFAULT_COOK_SALARY,
        )
        return float(value)

    def set_monthly_budget(self, amount):
        self.db.set_setting("monthly_budget", amount)

    def set_cook_salary(self, amount):
        self.db.set_setting("cook_salary", amount)

    def close_elapsed_months(self, today=None):
        """Close prior months, including missed month ends after an app was closed."""
        today = today or date.today()
        current_month = today.strftime("%Y-%m")
        previous_month = (today.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
        voucher_months = self.db.fetchall(
            """
            SELECT DISTINCT voucher_month
            FROM vouchers
            WHERE voucher_month < ?
            """,
            (current_month,),
        )
        months_to_close = {row["voucher_month"] for row in voucher_months}
        months_to_close.add(previous_month)
        for month in sorted(months_to_close):
            self.db.close_month(month)
        return sorted(months_to_close)

    def get_vouchers_for_period(self, start_date, end_date):
        start = self.parse_date(start_date)
        end = self.parse_date(end_date)
        if start > end:
            raise ValueError("Start date must be on or before end date.")

        matching = []
        for row in self.db.fetchall("SELECT * FROM vouchers ORDER BY id DESC"):
            try:
                voucher_date = self.parse_date(row["voucher_date"])
            except ValueError:
                continue
            if start <= voucher_date <= end:
                matching.append(row)
        return matching

    def get_expense_report(self, start_date, end_date):
        start = self.parse_date(start_date)
        end = self.parse_date(end_date)
        if start > end:
            raise ValueError("Start date must be on or before end date.")

        report_rows = []
        voucher_expenses = 0.0
        for row in self.db.fetchall("""
            SELECT
                v.voucher_no,
                v.voucher_date,
                i.purpose,
                i.expense_head,
                i.amount
            FROM vouchers AS v
            JOIN voucher_items AS i ON i.voucher_no = v.voucher_no
            ORDER BY v.id DESC, i.id ASC
        """):
            try:
                voucher_date = self.parse_date(row["voucher_date"])
            except ValueError:
                continue
            if start <= voucher_date <= end:
                amount = float(row["amount"] or 0)
                voucher_expenses += amount
                report_rows.append({
                    "date": voucher_date,
                    "voucher_no": row["voucher_no"],
                    "purpose": row["purpose"] or "",
                    "expense_head": row["expense_head"] or "",
                    "amount": amount,
                })

        month_count = (
            (end.year - start.year) * 12 + end.month - start.month + 1
        )
        monthly_budget = self.get_monthly_budget()
        cook_salary = self.get_cook_salary()
        budget_total = monthly_budget * month_count
        salary_total = cook_salary * month_count

        month = date(start.year, start.month, 1)
        last_month = date(end.year, end.month, 1)
        while month <= last_month:
            report_rows.append({
                "date": max(start, month),
                "voucher_no": "",
                "purpose": "Cook salary (monthly)",
                "expense_head": "Fixed salary",
                "amount": cook_salary,
            })
            if month.month == 12:
                month = date(month.year + 1, 1, 1)
            else:
                month = date(month.year, month.month + 1, 1)

        report_rows.sort(key=lambda row: (row["date"], row["voucher_no"]))
        return {
            "start_date": start,
            "end_date": end,
            "months": month_count,
            "monthly_budget": monthly_budget,
            "budget_total": budget_total,
            "cook_salary": cook_salary,
            "salary_total": salary_total,
            "voucher_expenses": voucher_expenses,
            "total_expenses": voucher_expenses + salary_total,
            "remaining_budget": budget_total - voucher_expenses - salary_total,
            "rows": report_rows,
        }

    # ---------------------------------------
    # Generate Monthly Voucher ID
    # Example:
    # September 2026
    # PCV-202609-0001
    # PCV-202609-0002
    #
    # October automatically becomes
    # PCV-202610-0001
    # ---------------------------------------
    def generate_voucher_id(self):

        month_code = datetime.now().strftime("%Y%m")

        query = """
        SELECT voucher_no
        FROM vouchers
        WHERE voucher_no LIKE ?
        ORDER BY id DESC
        LIMIT 1
        """

        row = self.db.fetchone(query, (f"PCV-{month_code}-%",))

        if row is None:

            number = 1

        else:

            last_id = row[0]

            try:

                number = int(last_id.split("-")[-1]) + 1

            except:

                number = 1

        return f"PCV-{month_code}-{number:04d}"

    def get_month_vouchers_for_pdf(self):
        """Return current-month vouchers (oldest first) with expense lines for batch PDF."""
        month_code = datetime.now().strftime("%Y%m")
        rows = self.db.fetchall(
            """
            SELECT *
            FROM vouchers
            WHERE voucher_no LIKE ?
            ORDER BY id ASC
            """,
            (f"PCV-{month_code}-%",),
        )

        vouchers = []
        for row in rows:
            voucher_no = row["voucher_no"]
            items = self.db.fetchall(
                """
                SELECT purpose, expense_head, amount
                FROM voucher_items
                WHERE voucher_no=?
                ORDER BY id ASC
                """,
                (voucher_no,),
            )
            vouchers.append({
                "voucher_no": voucher_no,
                "date": row["voucher_date"],
                "prepared_by": row["prepared_by"],
                "prepared_date": row["prepared_date"],
                "proposed_date": row["proposed_date"],
                "issuer_name": row["issuer_name"],
                "issuer_date": row["issuer_date"],
                "approver_name": row["approver_name"],
                "approver_date": row["approver_date"],
                "total": row["total"],
                "expenses": [
                    {
                        "purpose": item["purpose"],
                        "head": item["expense_head"],
                        "amount": item["amount"],
                    }
                    for item in items
                ],
            })

        return vouchers

    def get_next_voucher_number(self):
        return self.generate_voucher_id()

    # ---------------------------------------
    # Save Voucher
    # ---------------------------------------
    def save_voucher(
        self,
        voucher_no,
        voucher_date,
        total,
        prepared_by,
        approved_by,
        issuer,
        proposed_date,
        prepared_date,
        issuer_date,
        approver_date,
        expenses
    ):
        return self.db.save_voucher(
            voucher_no,
            voucher_date,
            prepared_by,
            prepared_date,
            proposed_date,
            issuer,
            issuer_date,
            approved_by,
            approver_date,
            total,
            expenses
        )

    # ---------------------------------------
    # Get Voucher List
    # ---------------------------------------
    def get_all_vouchers(self):

        return self.db.fetchall("""

        SELECT *

        FROM vouchers

        ORDER BY id DESC

        """)

    # ---------------------------------------
    # Get Single Voucher
    # ---------------------------------------
    def get_voucher(self, voucher_no):

        voucher = self.db.fetchone(

            """

            SELECT *

            FROM vouchers

            WHERE voucher_no=?

            """,

            (voucher_no,)
        )

        if voucher is None:

            return None

        items = self.db.fetchall(

            """

            SELECT *

            FROM voucher_items

            WHERE voucher_no=?

            """,

            (voucher_no,)
        )

        return {

            "voucher": voucher,

            "items": items

        }

    # ---------------------------------------
    # Delete Voucher
    # ---------------------------------------
    def delete_voucher(self, voucher_no):
        self.db.delete_voucher(voucher_no)

    # ---------------------------------------
    # Search Voucher
    # ---------------------------------------
    def search(self, keyword):

        keyword = f"%{keyword}%"

        return self.db.fetchall(

            """

            SELECT *

            FROM vouchers

            WHERE

            voucher_no LIKE ?

            OR prepared_by LIKE ?

            OR approver_name LIKE ?

            OR issuer_name LIKE ?

            ORDER BY id DESC

            """,

            (
                keyword,
                keyword,
                keyword,
                keyword
            )

        )

    # ---------------------------------------
    # Count Monthly Vouchers
    # ---------------------------------------
    def monthly_count(self):

        month_code = datetime.now().strftime("%Y%m")

        row = self.db.fetchone(

            """

            SELECT COUNT(*)

            FROM vouchers

            WHERE voucher_no LIKE ?

            """,

            (f"PCV-{month_code}-%",)

        )

        return row[0]

    # ---------------------------------------
    # Total Amount This Month
    # ---------------------------------------
    def monthly_total(self):

        month_code = datetime.now().strftime("%Y%m")

        row = self.db.fetchone(

            """

            SELECT SUM(total)

            FROM vouchers

            WHERE voucher_no LIKE ?

            """,

            (f"PCV-{month_code}-%",)

        )

        if row[0] is None:

            return 0

        return row[0]

    # ---------------------------------------
    # Today's Voucher Count
    # ---------------------------------------
    def today_count(self):

        today = datetime.now().strftime("%d-%b-%Y")

        row = self.db.fetchone(

            """

            SELECT COUNT(*)

            FROM vouchers

            WHERE voucher_date=?

            """,

            (today,)

        )

        return row[0]