import csv
import math
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
import os
import platform
import sqlite3
import webbrowser
from .voucher_manager import VoucherManager

class PettyCashUI:

    def __init__(self, root, database, voucher, bill_manager):

        self.root = root
        self.database = database
        self.voucher = voucher
        self.bill_manager = bill_manager

        self.rows = []

        self.create_variables()

        self.build_interface()

        self.voucher.close_elapsed_months()

        self.new_voucher()

        self.schedule_month_close()


    # ==========================================================
    # VARIABLES
    # ==========================================================

    def create_variables(self):

        today = datetime.today().strftime("%d-%b-%Y")

        self.voucher_id = tk.StringVar()

        self.current_date = tk.StringVar(value=today)

        self.total = tk.StringVar(value="0.00")

        self.prepared_by = tk.StringVar(value="Sajjad Ahmed")

        self.prepared_date = tk.StringVar(value=today)

        self.proposed_date = tk.StringVar(value=today)

        self.issuer_name = tk.StringVar(value="Muhammad Hassan")

        self.issuer_date = tk.StringVar(value=today)

        self.approver_name = tk.StringVar(value="Muhammad Hassan")

        self.approver_date = tk.StringVar(value=today)


    # ==========================================================
    # BUILD UI
    # ==========================================================

    def build_interface(self):

        self.build_toolbar()

        self.build_header()

        self.build_voucher_information()

        self.build_expense_table()

        self.build_total_section()

        self.build_signature_section()

        self.build_bottom_buttons()

        self.build_statusbar()


    # ==========================================================
    # TOOLBAR
    # ==========================================================

    def build_toolbar(self):

        toolbar = tk.Frame(
            self.root,
            bg="#1E3A5F",
            height=45
        )

        toolbar.pack(fill="x")

        buttons = [

            ("New Voucher", self.new_voucher),

            ("Save PDF", self.save_pdf),

            ("Print", self.print_voucher),

            ("Search", self.search_voucher),

            ("History", self.show_history),

            ("Bill Generator", self.open_bill_generator),

            ("Settings", self.open_settings),

            ("Exit", self.root.quit)

        ]

        for text, command in buttons:

            tk.Button(

                toolbar,

                text=text,

                command=command,

                bg="white",

                width=14,

                relief="flat"

            ).pack(side="left", padx=5, pady=6)


    # ==========================================================
    # HEADER
    # ==========================================================

    def build_header(self):

        frame = tk.Frame(self.root, bg="#F4F6F8")

        frame.pack(fill="x", padx=20, pady=15)

        tk.Label(

            frame,

            text="PETTY CASH VOUCHER SYSTEM",

            font=("Segoe UI", 20, "bold"),

            bg="#F4F6F8"

        ).pack()


    # ==========================================================
    # VOUCHER INFO
    # ==========================================================

    def build_voucher_information(self):

        frame = tk.LabelFrame(

            self.root,

            text="Voucher Information",

            padx=15,

            pady=10

        )

        frame.pack(fill="x", padx=20)

        tk.Label(frame, text="Voucher ID").grid(row=0, column=0, sticky="w")

        tk.Entry(

            frame,

            textvariable=self.voucher_id,

            state="readonly",

            width=22

        ).grid(row=0, column=1, padx=10)

        tk.Label(frame, text="Voucher Date").grid(row=0, column=2)

        tk.Entry(

            frame,

            textvariable=self.current_date,

            width=20

        ).grid(row=0, column=3)


    # ==========================================================
    # EXPENSE TABLE
    # ==========================================================

    def build_expense_table(self):

        frame = tk.LabelFrame(

            self.root,

            text="Expense Details",

            padx=10,

            pady=10

        )

        frame.pack(fill="both", padx=20, pady=15)

        headers = [

            "Purpose of Fund",

            "Expense Head",

            "Amount"

        ]

        widths = [40, 35, 18]

        for i, header in enumerate(headers):

            tk.Label(

                frame,

                text=header,

                relief="solid",

                width=widths[i],

                bg="#D9EAF7",

                font=("Segoe UI", 10, "bold")

            ).grid(row=0, column=i)

        self.table_frame = frame

        for i in range(5):

            self.add_row()


        control = tk.Frame(frame)

        control.grid(row=20, column=0, columnspan=3, pady=10)

        tk.Button(

            control,

            text="Add Row",

            command=self.add_row,

            width=15

        ).pack(side="left", padx=5)

        tk.Button(

            control,

            text="Remove Row",

            command=self.remove_row,

            width=15

        ).pack(side="left", padx=5)


    # ==========================================================
    # ADD ROW
    # ==========================================================

    def add_row(self):

        row = len(self.rows) + 1

        purpose = ttk.Combobox(

            self.table_frame,

            width=38,

            values=[

                "Payment for Grocery",

                "Payment for Vegetables",

                "Payment for Flour",

                "Payment for Yogurt",

                "Payment for Cream"

            ]

        )

        expense = ttk.Combobox(

            self.table_frame,

            width=34,

            values=[

                "Meal & Entertainment",

                "Repair & Maintenance"

            ]

        )

        amount = tk.Entry(

            self.table_frame,

            width=20

        )

        amount.bind("<KeyRelease>", lambda e: self.calculate_total())

        purpose.grid(row=row, column=0)

        expense.grid(row=row, column=1)

        amount.grid(row=row, column=2)

        self.rows.append((purpose, expense, amount))


    # ==========================================================
    # REMOVE ROW
    # ==========================================================

    def remove_row(self):

        if len(self.rows) <= 1:

            return

        widgets = self.rows.pop()

        for widget in widgets:

            widget.destroy()

        self.calculate_total()


    # ==========================================================
    # TOTAL
    # ==========================================================

    def build_total_section(self):

        frame = tk.Frame(self.root)

        frame.pack(fill="x", padx=20)

        tk.Label(

            frame,

            text="TOTAL",

            font=("Segoe UI", 12, "bold")

        ).pack(side="right")

        tk.Entry(

            frame,

            textvariable=self.total,

            justify="right",

            width=18,

            font=("Segoe UI", 12, "bold"),

            state="readonly"

        ).pack(side="right", padx=10)

            # ==========================================================
    # SIGNATURE SECTION
    # ==========================================================

    def build_signature_section(self):

        frame = tk.LabelFrame(
            self.root,
            text="Authorization",
            padx=15,
            pady=10
        )

        frame.pack(fill="x", padx=20, pady=10)

        # ---------------------------------------------------
        # Prepared By
        # ---------------------------------------------------

        tk.Label(frame, text="Prepared By").grid(row=0, column=0, sticky="w")
        tk.Entry(
            frame,
            textvariable=self.prepared_by,
            width=30
        ).grid(row=0, column=1, padx=5)

        tk.Label(frame, text="Prepared Date").grid(row=0, column=2)
        tk.Entry(
            frame,
            textvariable=self.prepared_date,
            width=18
        ).grid(row=0, column=3, padx=5)

        # ---------------------------------------------------
        # Proposed Bill Date
        # ---------------------------------------------------

        tk.Label(frame, text="Proposed Bills Date").grid(row=1, column=0, sticky="w")
        tk.Entry(
            frame,
            textvariable=self.proposed_date,
            width=30
        ).grid(row=1, column=1, padx=5)

        tk.Label(frame, text="Signature").grid(row=1, column=2)
        tk.Entry(
            frame,
            width=18
        ).grid(row=1, column=3)

        # ---------------------------------------------------
        # Petty Cash Issuer
        # ---------------------------------------------------

        tk.Label(frame, text="Petty Cash Issuer").grid(row=2, column=0, sticky="w")
        tk.Entry(
            frame,
            textvariable=self.issuer_name,
            width=30
        ).grid(row=2, column=1)

        tk.Label(frame, text="Issuer Date").grid(row=2, column=2)
        tk.Entry(
            frame,
            textvariable=self.issuer_date,
            width=18
        ).grid(row=2, column=3)

        # ---------------------------------------------------
        # Approver
        # ---------------------------------------------------

        tk.Label(frame, text="Approver Name").grid(row=3, column=0, sticky="w")
        tk.Entry(
            frame,
            textvariable=self.approver_name,
            width=30
        ).grid(row=3, column=1)

        tk.Label(frame, text="Approver Date").grid(row=3, column=2)
        tk.Entry(
            frame,
            textvariable=self.approver_date,
            width=18
        ).grid(row=3, column=3)

        tk.Label(frame, text="Approver Signature").grid(row=4, column=0)
        tk.Entry(
            frame,
            width=30
        ).grid(row=4, column=1)


    # ==========================================================
    # BOTTOM BUTTONS
    # ==========================================================

    def build_bottom_buttons(self):

        frame = tk.Frame(self.root)

        frame.pack(fill="x", padx=20, pady=15)

        tk.Button(
            frame,
            text="New Voucher",
            width=18,
            bg="#3498db",
            fg="white",
            command=self.new_voucher
        ).pack(side="left", padx=5)

        tk.Button(
            frame,
            text="Save Voucher",
            width=18,
            bg="#27ae60",
            fg="white",
            command=self.save_pdf
        ).pack(side="left", padx=5)

        tk.Button(
            frame,
            text="Print Voucher",
            width=18,
            bg="#e67e22",
            fg="white",
            command=self.print_voucher
        ).pack(side="left", padx=5)

        tk.Button(
            frame,
            text="Search",
            width=18,
            command=self.search_voucher
        ).pack(side="left", padx=5)

        tk.Button(
            frame,
            text="History",
            width=18,
            command=self.show_history
        ).pack(side="left", padx=5)

        tk.Button(
            frame,
            text="Exit",
            width=18,
            bg="#c0392b",
            fg="white",
            command=self.root.destroy
        ).pack(side="right")


    # ==========================================================
    # STATUS BAR
    # ==========================================================

    def build_statusbar(self):

        self.status = tk.StringVar()

        self.status.set("Ready")

        statusbar = tk.Label(

            self.root,

            textvariable=self.status,

            bd=1,

            relief="sunken",

            anchor="w"

        )

        statusbar.pack(side="bottom", fill="x")


    # ==========================================================
    # CALCULATE TOTAL
    # ==========================================================

    def calculate_total(self):

        total = 0.0

        for purpose, expense, amount in self.rows:

            value = amount.get().replace(",", "").strip()

            if value == "":
                continue

            try:
                total += float(value)

            except:

                pass

        self.total.set(f"{total:,.2f}")


    # ==========================================================
    # NEW VOUCHER
    # ==========================================================

    def new_voucher(self):

        self.voucher_id.set(

            self.voucher.generate_voucher_id()

        )

        today = datetime.today().strftime("%d-%b-%Y")

        self.current_date.set(today)

        self.prepared_date.set(today)

        self.proposed_date.set(today)

        self.issuer_date.set(today)

        self.approver_date.set(today)

        self.total.set("0.00")

        for purpose, expense, amount in self.rows:

            purpose.set("")

            expense.set("")

            amount.delete(0, tk.END)

        self.status.set("New voucher created.")


    # ==========================================================
    # PLACE HOLDERS
    # ==========================================================

    def build_voucher_data(self):
        voucher = {
            "voucher_no": self.voucher_id.get(),
            "date": self.current_date.get(),
            "prepared_by": self.prepared_by.get(),
            "prepared_date": self.prepared_date.get(),
            "proposed_date": self.proposed_date.get(),
            "issuer_name": self.issuer_name.get(),
            "issuer_date": self.issuer_date.get(),
            "approver_name": self.approver_name.get(),
            "approver_date": self.approver_date.get(),
            "approved_by": self.approver_name.get(),
            "paid_to": self.issuer_name.get(),
            "total": float(self.total.get().replace(",", "")) if self.total.get() else 0.0,
            "expenses": [],
        }

        for purpose_var, head_var, amount_entry in self.rows:
            purpose = purpose_var.get() if hasattr(purpose_var, "get") else ""
            head = head_var.get() if hasattr(head_var, "get") else ""
            try:
                amount = float(amount_entry.get().replace(",", ""))
            except Exception:
                amount = 0.0
            if purpose or head or amount:
                voucher["expenses"].append({
                    "purpose": purpose,
                    "head": head,
                    "amount": amount,
                })

        return voucher

    def generate_pdf_file(self, voucher=None):
        if voucher is None:
            voucher = self.build_voucher_data()

        filename = f"pdf/{voucher['voucher_no'] or 'voucher'}.pdf"
        os.makedirs("pdf", exist_ok=True)

        try:
            from .pdf_generator import PDFGenerator
        except Exception:
            messagebox.showerror(
                "Missing Dependency",
                "reportlab is not installed. Install it with:\n\npython -m pip install reportlab",
            )
            return None

        try:
            PDFGenerator().generate(voucher, filename)
            return filename
        except Exception as e:
            messagebox.showerror("PDF Error", str(e))
            return None

    def save_pdf(self):
        voucher = self.build_voucher_data()
        try:
            VoucherManager.parse_date(voucher["date"])
        except ValueError as error:
            messagebox.showerror("Invalid Voucher Date", str(error))
            return None

        if self.voucher.get_voucher(voucher["voucher_no"]) is not None:
            messagebox.showerror(
                "Voucher Already Saved",
                "This voucher is already in History. Create a new voucher before saving another.",
            )
            return None

        expenses = [
            {
                "purpose": expense["purpose"],
                "expense_head": expense["head"],
                "amount": expense["amount"],
            }
            for expense in voucher["expenses"]
        ]
        try:
            self.voucher.save_voucher(
                voucher_no=voucher["voucher_no"],
                voucher_date=voucher["date"],
                total=voucher["total"],
                prepared_by=voucher["prepared_by"],
                approved_by=voucher["approver_name"],
                issuer=voucher["issuer_name"],
                proposed_date=voucher["proposed_date"],
                prepared_date=voucher["prepared_date"],
                issuer_date=voucher["issuer_date"],
                approver_date=voucher["approver_date"],
                expenses=expenses,
            )
        except (sqlite3.Error, ValueError) as error:
            messagebox.showerror("Voucher Save Error", str(error))
            return None

        filename = self.generate_pdf_file(voucher)
        if not filename:
            self.status.set("Voucher saved to History; PDF generation failed.")
            return None

        messagebox.showinfo("PDF Saved", f"PDF saved to {filename}")
        self.status.set(f"Voucher saved to History; PDF saved: {filename}")

        try:
            # Open PDF in browser
            file_path = os.path.abspath(filename)
            webbrowser.open('file://' + file_path)
        except Exception:
            pass

        return filename

    def print_voucher(self):
        filename = self.generate_pdf_file()
        if not filename:
            return

        try:
            if platform.system() == "Windows":
                os.startfile(filename, "print")
            elif platform.system() == "Darwin":
                os.system(f"lp '{filename}'")
            else:
                os.system(f"lp '{filename}'")
            messagebox.showinfo("Success", "Voucher sent to printer")
            self.status.set("Voucher sent to printer")
        except Exception as e:
            messagebox.showerror("Error", f"Could not print: {e}")

    def open_bill_generator(self):
        from .bill_ui import InternalBillWindow

        InternalBillWindow(self.root, self.bill_manager)

    def search_voucher(self):

        messagebox.showinfo(
            "Search",
            "Search module coming in Version 2."
        )


    def show_history(self):
        window = tk.Toplevel(self.root)
        window.title("Daily Voucher History")
        window.geometry("900x550")
        window.transient(self.root)

        filters = ttk.Frame(window, padding=10)
        filters.pack(fill="x")
        today = datetime.today().date()
        history_start = tk.StringVar(
            value=today.replace(day=1).isoformat()
        )
        history_end = tk.StringVar(value=today.isoformat())
        ttk.Label(filters, text="From (YYYY-MM-DD):").pack(side="left")
        ttk.Entry(filters, textvariable=history_start, width=13).pack(
            side="left", padx=(5, 12)
        )
        ttk.Label(filters, text="To:").pack(side="left")
        ttk.Entry(filters, textvariable=history_end, width=13).pack(
            side="left", padx=5
        )
        ttk.Button(
            filters,
            text="Show Vouchers",
            command=lambda: self.load_history(
                tree, history_start, history_end
            ),
        ).pack(side="left", padx=8)

        columns = ("date", "voucher_no", "total", "month_status")
        tree = ttk.Treeview(window, columns=columns, show="headings")
        tree.heading("date", text="Voucher Date")
        tree.heading("voucher_no", text="Voucher ID")
        tree.heading("total", text="Total (PKR)")
        tree.heading("month_status", text="Month Status")
        tree.column("date", width=140)
        tree.column("voucher_no", width=220)
        tree.column("total", width=150, anchor="e")
        tree.column("month_status", width=170)
        tree.pack(fill="both", expand=True, padx=10, pady=5)

        actions = ttk.Frame(window, padding=10)
        actions.pack(fill="x")
        ttk.Button(
            actions,
            text="View Voucher PDF",
            command=lambda: self.open_history_voucher(tree),
        ).pack(side="left", padx=4)
        ttk.Button(
            actions,
            text="Delete Voucher",
            command=lambda: self.delete_history_voucher(
                tree, history_start, history_end
            ),
        ).pack(side="left", padx=4)
        ttk.Button(
            actions,
            text="Expense Report",
            command=lambda: self.open_expense_report(window),
        ).pack(side="left", padx=4)

        self.load_history(tree, history_start, history_end)

    def load_history(self, tree, start_var, end_var):
        try:
            vouchers = self.voucher.get_vouchers_for_period(
                start_var.get(),
                end_var.get(),
            )
        except ValueError as error:
            messagebox.showerror("Invalid Date Range", str(error))
            return
        except sqlite3.Error as error:
            messagebox.showerror("History Error", str(error))
            return

        for item in tree.get_children():
            tree.delete(item)
        try:
            for row in vouchers:
                voucher_month = row["voucher_month"]
                status = (
                    "Archived (editable)"
                    if self.database.is_month_closed(voucher_month)
                    else "Open"
                )
                tree.insert(
                    "",
                    "end",
                    iid=row["voucher_no"],
                    values=(
                        self.voucher.parse_date(row["voucher_date"]).strftime("%d-%b-%Y"),
                        row["voucher_no"],
                        f"{float(row['total'] or 0):,.2f}",
                        status,
                    ),
                )
        except sqlite3.Error as error:
            messagebox.showerror("History Error", str(error))

    def selected_history_voucher(self, tree):
        selected = tree.selection()
        if not selected:
            messagebox.showwarning(
                "Select a Voucher",
                "Select a voucher from the History list first.",
            )
            return None
        return selected[0]

    def open_history_voucher(self, tree):
        voucher_no = self.selected_history_voucher(tree)
        if voucher_no is None:
            return
        try:
            saved = self.voucher.get_voucher(voucher_no)
        except sqlite3.Error as error:
            messagebox.showerror("History Error", str(error))
            return
        if saved is None:
            messagebox.showerror("Voucher Not Found", "The selected voucher no longer exists.")
            return

        row = saved["voucher"]
        voucher_data = {
            "voucher_no": row["voucher_no"],
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
                for item in saved["items"]
            ],
        }
        filename = self.generate_pdf_file(voucher_data)
        if filename:
            webbrowser.open("file://" + os.path.abspath(filename))

    def delete_history_voucher(self, tree, start_var, end_var):
        voucher_no = self.selected_history_voucher(tree)
        if voucher_no is None:
            return
        if not messagebox.askyesno(
            "Delete Voucher",
            f"Delete voucher {voucher_no} and its expense lines?",
            parent=tree.winfo_toplevel(),
        ):
            return
        try:
            self.voucher.delete_voucher(voucher_no)
        except sqlite3.Error as error:
            messagebox.showerror("Voucher Delete Error", str(error))
            return
        self.load_history(tree, start_var, end_var)
        self.status.set(f"Voucher deleted: {voucher_no}")

    def open_expense_report(self, parent=None):
        parent = parent or self.root
        window = tk.Toplevel(parent)
        window.title("Expense Report")
        window.geometry("1000x650")
        window.transient(parent)

        today = datetime.today().date()
        start_var = tk.StringVar(value=today.replace(day=1).isoformat())
        end_var = tk.StringVar(value=today.isoformat())
        filters = ttk.Frame(window, padding=10)
        filters.pack(fill="x")
        ttk.Label(filters, text="From (YYYY-MM-DD):").pack(side="left")
        ttk.Entry(filters, textvariable=start_var, width=13).pack(
            side="left", padx=(5, 12)
        )
        ttk.Label(filters, text="To:").pack(side="left")
        ttk.Entry(filters, textvariable=end_var, width=13).pack(
            side="left", padx=5
        )
        ttk.Button(
            filters,
            text="Generate Report",
            command=lambda: self.refresh_expense_report(
                window, tree, summary, start_var, end_var
            ),
        ).pack(side="left", padx=8)
        ttk.Button(
            filters,
            text="Export CSV",
            command=lambda: self.export_expense_report(start_var, end_var),
        ).pack(side="left", padx=4)

        summary = ttk.Label(window, padding=10, justify="left")
        summary.pack(fill="x")

        columns = ("date", "voucher_no", "purpose", "expense_head", "amount")
        tree = ttk.Treeview(window, columns=columns, show="headings")
        for column, heading in (
            ("date", "Date"),
            ("voucher_no", "Voucher ID"),
            ("purpose", "Purpose"),
            ("expense_head", "Expense Head"),
            ("amount", "Amount (PKR)"),
        ):
            tree.heading(column, text=heading)
        tree.column("date", width=120)
        tree.column("voucher_no", width=170)
        tree.column("purpose", width=300)
        tree.column("expense_head", width=190)
        tree.column("amount", width=140, anchor="e")
        tree.pack(fill="both", expand=True, padx=10, pady=5)

        ttk.Label(
            window,
            text="Budget and cook salary are counted once for each calendar month touched by the selected dates.",
            padding=8,
        ).pack(fill="x")
        self.refresh_expense_report(
            window, tree, summary, start_var, end_var
        )

    def refresh_expense_report(self, window, tree, summary, start_var, end_var):
        try:
            report = self.voucher.get_expense_report(
                start_var.get(),
                end_var.get(),
            )
        except ValueError as error:
            messagebox.showerror(
                "Invalid Date Range",
                str(error),
                parent=window,
            )
            return
        except sqlite3.Error as error:
            messagebox.showerror("Report Error", str(error), parent=window)
            return

        for item in tree.get_children():
            tree.delete(item)
        for row in report["rows"]:
            tree.insert(
                "",
                "end",
                values=(
                    row["date"].strftime("%d-%b-%Y"),
                    row["voucher_no"],
                    row["purpose"],
                    row["expense_head"],
                    f"{row['amount']:,.2f}",
                ),
            )

        summary.configure(
            text=(
                f"Budget for {report['months']} month(s): "
                f"PKR {report['budget_total']:,.2f}    "
                f"Voucher expenses: PKR {report['voucher_expenses']:,.2f}\n"
                f"Cook salary: PKR {report['salary_total']:,.2f}    "
                f"Total expenses: PKR {report['total_expenses']:,.2f}    "
                f"Remaining budget: PKR {report['remaining_budget']:,.2f}"
            )
        )

    def export_expense_report(self, start_var, end_var):
        try:
            report = self.voucher.get_expense_report(
                start_var.get(),
                end_var.get(),
            )
        except ValueError as error:
            messagebox.showerror("Invalid Date Range", str(error))
            return
        except sqlite3.Error as error:
            messagebox.showerror("Report Error", str(error))
            return

        filename = filedialog.asksaveasfilename(
            parent=self.root,
            title="Export Expense Report",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile="petty_cash_expense_report.csv",
        )
        if not filename:
            return
        try:
            with open(filename, "w", newline="", encoding="utf-8-sig") as report_file:
                writer = csv.writer(report_file)
                writer.writerow(["Expense Report"])
                writer.writerow(["From", report["start_date"].isoformat()])
                writer.writerow(["To", report["end_date"].isoformat()])
                writer.writerow(["Monthly budget (PKR)", report["monthly_budget"]])
                writer.writerow(["Cook salary per month (PKR)", report["cook_salary"]])
                writer.writerow(["Total budget (PKR)", report["budget_total"]])
                writer.writerow(["Voucher expenses (PKR)", report["voucher_expenses"]])
                writer.writerow(["Total expenses (PKR)", report["total_expenses"]])
                writer.writerow(["Remaining budget (PKR)", report["remaining_budget"]])
                writer.writerow([])
                writer.writerow([
                    "Date", "Voucher ID", "Purpose", "Expense Head", "Amount (PKR)"
                ])
                for row in report["rows"]:
                    writer.writerow([
                        row["date"].isoformat(),
                        row["voucher_no"],
                        row["purpose"],
                        row["expense_head"],
                        row["amount"],
                    ])
        except OSError as error:
            messagebox.showerror("Report Export Error", str(error))
            return
        messagebox.showinfo("Report Exported", f"Report saved to {filename}")

    def open_settings(self):
        window = tk.Toplevel(self.root)
        window.title("Petty Cash Settings")
        window.geometry("430x210")
        window.transient(self.root)
        frame = ttk.Frame(window, padding=20)
        frame.pack(fill="both", expand=True)

        budget_var = tk.StringVar(
            value=f"{self.voucher.get_monthly_budget():g}"
        )
        salary_var = tk.StringVar(
            value=f"{self.voucher.get_cook_salary():g}"
        )
        ttk.Label(frame, text="Monthly petty cash budget (PKR)").grid(
            row=0, column=0, sticky="w", pady=6
        )
        ttk.Entry(frame, textvariable=budget_var, width=18).grid(
            row=0, column=1, padx=8, pady=6
        )
        ttk.Label(frame, text="Monthly cook salary (PKR)").grid(
            row=1, column=0, sticky="w", pady=6
        )
        ttk.Entry(frame, textvariable=salary_var, width=18).grid(
            row=1, column=1, padx=8, pady=6
        )

        def save_settings():
            try:
                budget = float(budget_var.get().replace(",", "").strip())
                salary = float(salary_var.get().replace(",", "").strip())
                if not math.isfinite(budget) or not math.isfinite(salary):
                    raise ValueError("Amounts must be finite numbers.")
                if budget < 0 or salary < 0:
                    raise ValueError("Amounts cannot be negative.")
            except ValueError as error:
                messagebox.showerror("Invalid Settings", str(error), parent=window)
                return

            try:
                self.voucher.set_monthly_budget(budget)
                self.voucher.set_cook_salary(salary)
            except sqlite3.Error as error:
                messagebox.showerror(
                    "Settings Save Error",
                    str(error),
                    parent=window,
                )
                return
            self.status.set("Monthly budget and cook salary settings saved.")
            window.destroy()

        ttk.Button(frame, text="Save Settings", command=save_settings).grid(
            row=2, column=0, columnspan=2, pady=14
        )

    def schedule_month_close(self):
        now = datetime.now()
        next_midnight = now.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        ) + timedelta(days=1)
        delay_ms = max(1000, int((next_midnight - now).total_seconds() * 1000))
        self.root.after(delay_ms, self.run_month_close_check)

    def run_month_close_check(self):
        try:
            closed_months = self.voucher.close_elapsed_months()
        except sqlite3.Error as error:
            messagebox.showerror("Month Close Error", str(error))
        else:
            if closed_months:
                self.status.set(
                    f"Month-end archive checked through {closed_months[-1]}."
                )
        self.schedule_month_close()