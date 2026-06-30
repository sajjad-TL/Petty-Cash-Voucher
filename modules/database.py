import sqlite3
import os
from datetime import datetime


class DatabaseManager:
    def __init__(self):
        self.db_name = "petty_cash.db"
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

        month = datetime.today().strftime("%Y-%m")

        created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.cursor.execute("""
        INSERT INTO vouchers(
            voucher_no,
            voucher_month,
            voucher_date,

            prepared_by,
            prepared_date,

            proposed_date,

            issuer_name,
            issuer_date,

            approver_name,
            approver_date,

            total,

            created_at
        )
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            voucher_no,
            month,
            voucher_date,

            prepared_by,
            prepared_date,

            proposed_date,

            issuer_name,
            issuer_date,

            approver_name,
            approver_date,

            total,

            created
        ))

        for item in items:

            self.cursor.execute("""
            INSERT INTO voucher_items(
                voucher_no,
                purpose,
                expense_head,
                amount
            )
            VALUES(?,?,?,?)
            """,
            (
                voucher_no,
                item["purpose"],
                item["expense_head"],
                item["amount"]
            ))

        self.conn.commit()

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

        self.cursor.execute("""
        DELETE FROM vouchers
        WHERE voucher_no=?
        """, (voucher_no,))

        self.cursor.execute("""
        DELETE FROM voucher_items
        WHERE voucher_no=?
        """, (voucher_no,))

        self.conn.commit()

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