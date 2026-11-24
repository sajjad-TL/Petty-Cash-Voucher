import sqlite3
from datetime import datetime


class DatabaseManager:
    def __init__(self, db_name="petty_cash.db"):
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

        self.create_tables()

    # --------------------------------------------------
    # Create Tables
    # --------------------------------------------------
    def create_tables(self):

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS vouchers(
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            voucher_no TEXT UNIQUE,
            voucher_month TEXT,

            voucher_date TEXT,

            prepared_by TEXT,
            prepared_date TEXT,

            proposed_date TEXT,

            issuer_name TEXT,
            issuer_date TEXT,

            approver_name TEXT,
            approver_date TEXT,

            total REAL,

            created_at TEXT
        )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS voucher_items(
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            voucher_no TEXT,

            purpose TEXT,

            expense_head TEXT,

            amount REAL
        )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings(
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS month_closures(
            month TEXT PRIMARY KEY,
            closed_at TEXT NOT NULL,
            voucher_count INTEGER NOT NULL,
            voucher_total REAL NOT NULL
        )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS internal_bills(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bill_date TEXT NOT NULL,
            bill_to TEXT NOT NULL DEFAULT '',
            note TEXT NOT NULL DEFAULT '',
            total REAL NOT NULL,
            created_at TEXT NOT NULL
        )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS internal_bill_items(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bill_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            unit_price REAL NOT NULL,
            quantity REAL NOT NULL,
            line_total REAL NOT NULL
        )
        """)

        self.conn.commit()

    def execute(self, query, params=()):
        self.cursor.execute(query, params)
        self.conn.commit()
        return self.cursor

    def fetchone(self, query, params=()):
        self.cursor.execute(query, params)
        return self.cursor.fetchone()

    def fetchall(self, query, params=()):
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def insert(self, query, params=()):
        self.cursor.execute(query, params)
        self.conn.commit()
        return self.cursor.lastrowid

    def get_setting(self, key, default=None):
        row = self.fetchone("SELECT value FROM settings WHERE key=?", (key,))
        return default if row is None else row["value"]

    def set_setting(self, key, value):
        self.execute(
            """
            INSERT OR REPLACE INTO settings(key, value)
            VALUES(?, ?)
            """,
            (key, str(value)),
        )

    def get_month_closures(self):
        return self.fetchall("SELECT * FROM month_closures ORDER BY month DESC")

    def is_month_closed(self, month):
        return self.fetchone(
            "SELECT 1 FROM month_closures WHERE month=?",
            (month,),
        ) is not None

    def close_month(self, month):
        """Record a month-end snapshot once; existing vouchers remain editable."""
        self.cursor.execute(
            """
            SELECT COUNT(*) AS voucher_count, COALESCE(SUM(total), 0) AS voucher_total
            FROM vouchers
            WHERE voucher_month=?
            """,
            (month,),
        )
        totals = self.cursor.fetchone()
        self.cursor.execute(
            """
            INSERT OR IGNORE INTO month_closures(
                month, closed_at, voucher_count, voucher_total
            )
            VALUES(?, ?, ?, ?)
            """,
            (
                month,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                totals["voucher_count"],
                totals["voucher_total"],
            ),
        )
        self.conn.commit()
        return self.fetchone(
            "SELECT * FROM month_closures WHERE month=?",
            (month,),
        )

    def save_internal_bill(self, bill_date, bill_to, note, total, items):
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            self.cursor.execute("BEGIN")
            self.cursor.execute(
                """
                INSERT INTO internal_bills(
                    bill_date, bill_to, note, total, created_at
                )
                VALUES(?, ?, ?, ?, ?)
                """,
                (bill_date, bill_to, note, total, created_at),
            )
            bill_id = self.cursor.lastrowid

            for item in items:
                self.cursor.execute(
                    """
                    INSERT INTO internal_bill_items(
                        bill_id, description, unit_price, quantity, line_total
                    )
                    VALUES(?, ?, ?, ?, ?)
                    """,
                    (
                        bill_id,
                        item["description"],
                        item["unit_price"],
                        item["quantity"],
                        item["line_total"],
                    ),
                )

            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

        return bill_id

    def get_internal_bill_page(self, page_number, bills_per_page=4):
        first_id = (page_number - 1) * bills_per_page + 1
        last_id = first_id + bills_per_page - 1
        rows = self.fetchall(
            """
            SELECT *
            FROM internal_bills
            WHERE id BETWEEN ? AND ?
            ORDER BY id
            """,
            (first_id, last_id),
        )

        bills = []
        for row in rows:
            bill = dict(row)
            items = self.fetchall(
                """
                SELECT description, unit_price, quantity, line_total
                FROM internal_bill_items
                WHERE bill_id=?
                ORDER BY id
                """,
                (bill["id"],),
            )
            bill["items"] = [dict(item) for item in items]
            bills.append(bill)
        return bills

    def get_internal_bill_descriptions(self, limit=100):
        return self.fetchall(
            """
            SELECT description
            FROM internal_bill_items
            WHERE TRIM(description) != ''
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )

    # --------------------------------------------------
    # Generate Monthly Voucher Number
    # Example:
    # Sep-2026
    # PCV-0001
    # --------------------------------------------------
    def generate_voucher_no(self):

        month = datetime.today().strftime("%Y-%m")

        self.cursor.execute("""
            SELECT COUNT(*)
            FROM vouchers
            WHERE voucher_month=?
        """, (month,))

        count = self.cursor.fetchone()[0]

        new_no = count + 1

        return f"PCV-{new_no:04d}"

    # --------------------------------------------------
    # Save Voucher
    # --------------------------------------------------
    def save_voucher(
            self,
            voucher_no,
            voucher_date,
            prepared_by,
            prepared_date,
            proposed_date,
            issuer_name,
            issuer_date,
            approver_name,
            approver_date,
            total,
            items
    ):

        if not isinstance(voucher_date, str):
            raise ValueError("Voucher date must be text.")
        normalized_date = voucher_date.strip()
        parsed_date = None
        for date_format in (
            "%Y-%m-%d",
            "%d-%b-%Y",
            "%d-%B-%Y",
            "%d-%m-%Y",
        ):
            try:
                parsed_date = datetime.strptime(normalized_date, date_format).date()
                break
            except ValueError:
                continue
        if parsed_date is None:
            raise ValueError(
                "Voucher date must use YYYY-MM-DD or DD-Mon-YYYY format."
            )

        month = parsed_date.strftime("%Y-%m")

        created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            self.cursor.execute("""
            INSERT INTO vouchers(
                voucher_no, voucher_month, voucher_date,
                prepared_by, prepared_date, proposed_date,
                issuer_name, issuer_date, approver_name, approver_date,
                total, created_at
            )
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                voucher_no, month, voucher_date,
                prepared_by, prepared_date, proposed_date,
                issuer_name, issuer_date, approver_name, approver_date,
                total, created,
            ))

            for item in items:
                self.cursor.execute("""
                INSERT INTO voucher_items(
                    voucher_no, purpose, expense_head, amount
                )
                VALUES(?,?,?,?)
                """, (
                    voucher_no,
                    item["purpose"],
                    item["expense_head"],
                    item["amount"],
                ))

            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    # --------------------------------------------------
    # Get Voucher
    # --------------------------------------------------
    def get_voucher(self, voucher_no):

        self.cursor.execute("""
        SELECT *
        FROM vouchers
        WHERE voucher_no=?
        """, (voucher_no,))

        voucher = self.cursor.fetchone()

        self.cursor.execute("""
        SELECT *
        FROM voucher_items
        WHERE voucher_no=?
        """, (voucher_no,))

        items = self.cursor.fetchall()

        return voucher, items

    # --------------------------------------------------
    # Get All Vouchers
    # --------------------------------------------------
    def get_all_vouchers(self):

        self.cursor.execute("""
        SELECT *
        FROM vouchers
        ORDER BY id DESC
        """)

        return self.cursor.fetchall()

    # --------------------------------------------------
    # Search Voucher
    # --------------------------------------------------
    def search(self, keyword):

        keyword = "%" + keyword + "%"

        self.cursor.execute("""
        SELECT *
        FROM vouchers
        WHERE voucher_no LIKE ?
           OR prepared_by LIKE ?
           OR issuer_name LIKE ?
           OR approver_name LIKE ?
        ORDER BY id DESC
        """,
        (
            keyword,
            keyword,
            keyword,
            keyword
        ))

        return self.cursor.fetchall()

    # --------------------------------------------------
    # Delete Voucher
    # --------------------------------------------------
    def delete_voucher(self, voucher_no):
        try:
            self.cursor.execute(
                "DELETE FROM voucher_items WHERE voucher_no=?",
                (voucher_no,),
            )
            self.cursor.execute(
                "DELETE FROM vouchers WHERE voucher_no=?",
                (voucher_no,),
            )
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    # --------------------------------------------------
    # Update Voucher
    # --------------------------------------------------
    def update_total(self, voucher_no, total):

        self.cursor.execute("""
        UPDATE vouchers
        SET total=?
        WHERE voucher_no=?
        """,
        (
            total,
            voucher_no
        ))

        self.conn.commit()

    # --------------------------------------------------
    # Close Database
    # --------------------------------------------------
    def close(self):
        self.conn.close()


# ------------------------------------------------------
# Testing
# ------------------------------------------------------

if __name__ == "__main__":

    db = DatabaseManager()

    print("Database Created Successfully")

    print("Next Voucher Number :")

    print(db.generate_voucher_no())

    db.close()