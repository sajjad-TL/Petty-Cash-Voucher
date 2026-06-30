import tkinter as tk
from tkinter import messagebox
import os

# Import project modules
from modules.database import DatabaseManager
from modules.voucher_manager import VoucherManager
from modules.ui import PettyCashUI

class PettyCashApplication:

    def __init__(self):

        # -------------------------
        # Create folders if missing
        # -------------------------
        folders = [
            "assets",
            "data",
            "pdf",
            "backup"
        ]

        for folder in folders:
            os.makedirs(folder, exist_ok=True)

        # -------------------------
        # Database
        # -------------------------
        self.database = DatabaseManager()

        # -------------------------
        # Voucher Manager
        # -------------------------
        self.voucher = VoucherManager(self.database)

        # -------------------------
        # Tkinter Window
        # -------------------------
        self.root = tk.Tk()

        self.root.title("Petty Cash Voucher System")

        self.root.geometry("1280x850")

        self.root.minsize(1200, 800)

        self.root.configure(bg="#F4F6F8")

        # Application Icon
        try:
            self.root.iconbitmap("assets/icon.ico")
        except:
            pass

        # -------------------------
        # Start UI
        # -------------------------
        self.ui = PettyCashUI(

            root=self.root,

            database=self.database,

            voucher=self.voucher

        )

    def run(self):

        self.root.mainloop()


if __name__ == "__main__":

    try:

        app = PettyCashApplication()

        app.run()

    except Exception as e:

        messagebox.showerror(
            "Application Error",
            str(e)
        )