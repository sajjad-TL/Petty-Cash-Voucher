import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import os
import platform
import webbrowser
from .voucher_manager import VoucherManager

class PettyCashUI:

    def __init__(self, root, database, voucher):

        self.root = root
        self.database = database
        self.voucher = voucher

        self.rows = []

        self.create_variables()

        self.build_interface()

        self.new_voucher()


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
        filename = self.generate_pdf_file()
        if not filename:
            return None

        messagebox.showinfo("PDF Saved", f"PDF saved to {filename}")
        self.status.set(f"PDF saved: {filename}")

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


    def search_voucher(self):

        messagebox.showinfo(
            "Search",
            "Search module coming in Version 2."
        )


    def show_history(self):

        messagebox.showinfo(
            "History",
            "Voucher history coming in Version 2."
        )


    def open_settings(self):

        messagebox.showinfo(
            "Settings",
            "Settings module coming later."
        )