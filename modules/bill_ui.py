import math
import os
import sqlite3
import webbrowser
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

from .bill_manager import InternalBillManager
from .internal_bill_pdf import InternalBillPDFGenerator


class InternalBillWindow:
    def __init__(self, root, bill_manager):
        self.root = root
        self.bill_manager = bill_manager
        self.rows = []

        self.window = tk.Toplevel(root)
        self.window.title("Internal Bill Generator")
        self.window.geometry("900x600")
        self.window.minsize(780, 520)
        self.window.transient(root)

        self.bill_date = tk.StringVar(value=datetime.today().strftime("%d-%b-%Y"))
        self.bill_to = tk.StringVar()
        self.note = tk.StringVar()
        self.total = tk.StringVar(value="0.00")
        self.description_suggestions = self.bill_manager.get_description_suggestions()

        self._build_interface()

    def _build_interface(self):
        heading = tk.Label(
            self.window,
            text="Internal Expense Record",
            font=("Segoe UI", 16, "bold"),
        )
        heading.pack(pady=(14, 2))
        tk.Label(
            self.window,
            text="For recording expenses when no supplier receipt is available; not a supplier-issued receipt.",
            fg="#7A2424",
        ).pack(pady=(0, 12))
        tk.Label(
            self.window,
            text="Item description suggestions are based on previously saved bills.",
            fg="#555555",
        ).pack(pady=(0, 8))

        details = tk.LabelFrame(self.window, text="Bill Information", padx=12, pady=10)
        details.pack(fill="x", padx=18)
        tk.Label(details, text="Date").grid(row=0, column=0, sticky="w")
        ttk.Entry(details, textvariable=self.bill_date, width=20).grid(
            row=0, column=1, padx=(6, 18), sticky="w"
        )
        tk.Label(details, text="Bill to").grid(row=0, column=2, sticky="w")
        ttk.Entry(details, textvariable=self.bill_to, width=48).grid(
            row=0, column=3, padx=6, sticky="ew"
        )
        tk.Label(details, text="Note").grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(details, textvariable=self.note).grid(
            row=1, column=1, columnspan=3, padx=6, pady=(8, 0), sticky="ew"
        )
        details.columnconfigure(3, weight=1)

        items_frame = tk.LabelFrame(self.window, text="Expense Items", padx=10, pady=8)
        items_frame.pack(fill="both", expand=True, padx=18, pady=12)
        self.items_frame = items_frame
        for column, (title, width) in enumerate(
            (("Item description", 46), ("Unit price", 14), ("Quantity", 10), ("Line total", 16))
        ):
            tk.Label(
                items_frame,
                text=title,
                font=("Segoe UI", 9, "bold"),
                width=width,
                anchor="w",
            ).grid(row=0, column=column, padx=3, pady=(0, 5), sticky="w")

        for _ in range(4):
            self.add_row()

        controls = tk.Frame(items_frame)
        controls.grid(row=20, column=0, columnspan=4, sticky="w", pady=(8, 0))
        ttk.Button(controls, text="Add item", command=self.add_row).pack(side="left", padx=(0, 6))
        ttk.Button(controls, text="Remove last item", command=self.remove_row).pack(side="left")

        footer = tk.Frame(self.window)
        footer.pack(fill="x", padx=18, pady=(0, 16))
        tk.Label(footer, text="Total", font=("Segoe UI", 11, "bold")).pack(side="right")
        tk.Label(
            footer,
            textvariable=self.total,
            font=("Segoe UI", 11, "bold"),
            width=16,
            anchor="e",
        ).pack(side="right", padx=(8, 18))
        ttk.Button(footer, text="Generate 4-up A4 sheet", command=self.generate_bill).pack(
            side="left"
        )

    def add_row(self):
        if len(self.rows) >= InternalBillManager.MAX_ITEMS:
            messagebox.showwarning(
                "Item limit",
                f"A bill can contain at most {InternalBillManager.MAX_ITEMS} items.",
                parent=self.window,
            )
            return

        row_index = len(self.rows) + 1
        description_values = self.description_suggestions
        description = ttk.Combobox(
            self.items_frame,
            width=46,
            values=description_values,
        )
        unit_price = ttk.Entry(self.items_frame, width=14)
        quantity = ttk.Entry(self.items_frame, width=10)
        line_total = tk.StringVar(value="")
        total_label = tk.Label(self.items_frame, textvariable=line_total, width=16, anchor="w")

        description.grid(row=row_index, column=0, padx=3, pady=2, sticky="ew")
        unit_price.grid(row=row_index, column=1, padx=3, pady=2, sticky="ew")
        quantity.grid(row=row_index, column=2, padx=3, pady=2, sticky="ew")
        total_label.grid(row=row_index, column=3, padx=3, pady=2, sticky="w")

        row = {
            "description": description,
            "unit_price": unit_price,
            "quantity": quantity,
            "line_total": line_total,
        }
        self.rows.append(row)
        self._bind_suggestions(description, description_values)
        for widget in (description, unit_price, quantity):
            widget.bind(
                "<KeyRelease>",
                lambda _event: self.calculate_total(),
                add="+",
            )

    def _bind_suggestions(self, widget, suggestions):
        self._set_suggestion_values(widget, suggestions)
        widget.bind("<KeyRelease>", self._update_suggestions)

    @staticmethod
    def _set_suggestion_values(widget, suggestions):
        widget.suggestion_values = tuple(suggestions)
        widget.configure(values=widget.suggestion_values)

    def _update_suggestions(self, event):
        if event.keysym in {
            "Alt_L", "Alt_R", "Control_L", "Control_R", "Down", "End",
            "Escape", "Home", "Left", "Return", "Right", "Shift_L",
            "Shift_R", "Tab", "Up",
        }:
            return

        widget = event.widget
        typed = widget.get().casefold()
        matches = [
            value for value in widget.suggestion_values
            if not typed or value.casefold().startswith(typed)
        ][:10]
        widget.configure(values=matches)
        if matches and typed != matches[0].casefold():
            widget.event_generate("<Down>")

    def _refresh_suggestions(self):
        self.description_suggestions = self.bill_manager.get_description_suggestions()
        for row in self.rows:
            self._set_suggestion_values(
                row["description"],
                self.description_suggestions,
            )

    def remove_row(self):
        if len(self.rows) <= 1:
            return
        row = self.rows.pop()
        for key in ("description", "unit_price", "quantity"):
            row[key].destroy()
        self.calculate_total()

    def calculate_total(self):
        total = 0.0
        for row in self.rows:
            price_text = row["unit_price"].get().replace(",", "").strip()
            quantity_text = row["quantity"].get().replace(",", "").strip()
            if not price_text and not quantity_text:
                row["line_total"].set("")
                continue
            try:
                line_total = round(float(price_text) * float(quantity_text), 2)
            except ValueError:
                row["line_total"].set("Check values")
                self.total.set("Check values")
                return
            if not math.isfinite(line_total):
                row["line_total"].set("Check values")
                self.total.set("Check values")
                return
            row["line_total"].set(f"{line_total:,.2f}")
            total += line_total
        self.total.set(f"{total:,.2f}")

    def _get_items(self):
        return [
            {
                "description": row["description"].get(),
                "unit_price": row["unit_price"].get(),
                "quantity": row["quantity"].get(),
            }
            for row in self.rows
        ]

    def generate_bill(self):
        try:
            bill = self.bill_manager.create_bill(
                bill_date=self.bill_date.get(),
                bill_to=self.bill_to.get(),
                note=self.note.get(),
                items=self._get_items(),
            )
        except (ValueError, sqlite3.Error) as error:
            messagebox.showerror("Bill not generated", str(error), parent=self.window)
            return

        try:
            self._refresh_suggestions()
        except sqlite3.Error as error:
            messagebox.showwarning(
                "Suggestions not refreshed",
                f"Record {bill['record_no']} was saved, but suggestions could not be refreshed:\n{error}",
                parent=self.window,
            )

        try:
            page_bills = self.bill_manager.get_page_bills(bill["page_number"])
            filename = os.path.abspath(
                os.path.join(
                    "pdf",
                    "internal_bills",
                    f"IER-SHEET-{bill['page_number']:04d}.pdf",
                )
            )
            InternalBillPDFGenerator().generate_page(page_bills, filename)
        except (OSError, ValueError, sqlite3.Error) as error:
            messagebox.showerror(
                "PDF generation failed",
                f"{bill['record_no']} was saved, but its A4 sheet could not be generated:\n{error}",
                parent=self.window,
            )
            return

        messagebox.showinfo(
            "Bill generated",
            f"Record {bill['record_no']} generated.\n"
            f"Sheet {bill['page_number']} now contains "
            f"{len(page_bills)} of 4 bills.\n\nSaved to:\n{filename}",
            parent=self.window,
        )
        webbrowser.open_new(Path(filename).as_uri())
        self._reset_form()

    def _reset_form(self):
        self.bill_date.set(datetime.today().strftime("%d-%b-%Y"))
        self.bill_to.set("")
        self.note.set("")
        for row in self.rows:
            for key in ("description", "unit_price", "quantity"):
                row[key].delete(0, tk.END)
            row["line_total"].set("")
        self.total.set("0.00")
