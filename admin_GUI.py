import tkinter as tk
from tkinter import ttk, messagebox
import requests

API_BASE_URL = "http://172.16.0.60:8002"  # Change if your FastAPI server runs elsewhere

class AdminDashboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Admin Dashboard")
        self.geometry("900x600")
        self.selected_user_id = None
        self.full_user_list = []  # Store all users once

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="User View", width=20, command=self.show_user_view).grid(row=0, column=0, padx=10)
        tk.Button(btn_frame, text="Generate QR", width=20, command=self.show_generate_qr).grid(row=0, column=1, padx=10)

        self.container = tk.Frame(self)
        self.container.pack(fill='both', expand=True)

        self.show_user_view()

    def clear_container(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    def get_all_users(self):
        try:
            res = requests.get(f"{API_BASE_URL}/admin/get-users")
            res.raise_for_status()
            self.full_user_list = res.json()
            return self.full_user_list
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch users: {e}")
            return []

    def search_users(self, query):
        return [
            user for user in self.full_user_list
            if query.lower() in user["username"].lower()
        ]

    def get_transactions(self, user_id):
        try:
            res = requests.get(f"{API_BASE_URL}/get-transaction", params={"id": user_id})
            res.raise_for_status()
            return res.json()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch transactions: {e}")
            return []

    def generate_qr(self, name, amount, filename):
        try:
            res = requests.post(f"{API_BASE_URL}/generate-qr", json={"name": name, "amount": amount}, stream=True)
            res.raise_for_status()
            with open(filename, "wb") as f:
                f.write(res.content)
            messagebox.showinfo("Success", f"QR Code saved as {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate QR: {e}")

    def show_user_view(self):
        self.clear_container()

        search_frame = tk.Frame(self.container)
        search_frame.pack(fill='x', pady=10)

        search_entry = tk.Entry(search_frame, width=40)
        search_entry.pack(side='left', padx=10)

        tk.Button(search_frame, text="Search", command=lambda: update_tree(self.search_users(search_entry.get()))).pack(side='left')

        cols = ("ID", "Username", "Phone", "Email", "DOB", "Height", "Weight", "Gender", "Blood", "Credits")
        self.tree = ttk.Treeview(self.container, columns=cols, show='headings')
        for col in cols:
            self.tree.heading(col, text=col)
        self.tree.pack(fill='both', expand=True)

        def update_tree(data):
            for row in self.tree.get_children():
                self.tree.delete(row)
            for user in data:
                self.tree.insert('', 'end', values=(
                    user["user_id"], user["username"], user["phone_number"],
                    user["email"], user["DOB"], user["height"], user["weight"],
                    user["gender"], user["blood_group"], user["credit_balance"]
                ))

        def on_user_select(event):
            selected = self.tree.selection()
            if selected:
                user_id = self.tree.item(selected[0])["values"][0]
                self.show_transactions(user_id)

        self.tree.bind("<<TreeviewSelect>>", on_user_select)

        update_tree(self.get_all_users())

    def show_transactions(self, user_id):
        self.clear_container()

        tk.Label(self.container, text=f"Transactions for User ID: {user_id}", font=("Helvetica", 14)).pack(pady=10)

        trans_tree = ttk.Treeview(self.container, columns=("Type", "Activity", "Amount", "Date"), show='headings')
        for col in ("Type", "Activity", "Amount", "Date"):
            trans_tree.heading(col, text=col)
        trans_tree.pack(fill='both', expand=True)

        transactions = self.get_transactions(user_id)
        for txn in transactions:
            trans_tree.insert('', 'end', values=(
                txn["transaction_type"], txn["activity_type"], txn["amount"], txn["created_at"]
            ))

        tk.Button(self.container, text="Back", command=self.show_user_view).pack(pady=10)

    def show_generate_qr(self):
        self.clear_container()

        tk.Label(self.container, text="Generate QR Code", font=("Helvetica", 14)).pack(pady=10)

        name_var = tk.StringVar()
        amount_var = tk.StringVar()
        filename_var = tk.StringVar()

        form_frame = tk.Frame(self.container)
        form_frame.pack(pady=10)

        tk.Label(form_frame, text="Name: ").grid(row=0, column=0, sticky='e')
        tk.Entry(form_frame, textvariable=name_var).grid(row=0, column=1, padx=10)

        tk.Label(form_frame, text="Amount: ").grid(row=1, column=0, sticky='e')
        tk.Entry(form_frame, textvariable=amount_var).grid(row=1, column=1, padx=10)

        tk.Label(form_frame, text="Filename: ").grid(row=2, column=0, sticky='e')
        tk.Entry(form_frame, textvariable=filename_var).grid(row=2, column=1, padx=10)

        def handle_generate():
            try:
                name = name_var.get()
                amount = float(amount_var.get())
                filename = filename_var.get().strip()
                if not filename.endswith(".png"):
                    filename += ".png"
                self.generate_qr(name, amount, filename)
            except Exception as e:
                messagebox.showerror("Error", str(e))

        tk.Button(self.container, text="Generate QR", command=handle_generate).pack(pady=20)

if __name__ == "__main__":
    app = AdminDashboard()
    app.mainloop()
