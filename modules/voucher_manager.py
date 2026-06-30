from datetime import datetime
from modules.database import DatabaseManager


class VoucherManager:

    def __init__(self, database=None):
        self.db = database if database is not None else DatabaseManager()

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

        self.db.execute(

            """

            DELETE FROM voucher_items

            WHERE voucher_no=?

            """,

            (voucher_no,)
        )

        self.db.execute(

            """

            DELETE FROM vouchers

            WHERE voucher_no=?

            """,

            (voucher_no,)
        )

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