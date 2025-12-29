import sqlite3
from tkinter import Menu
from tkinter import messagebox
from tkinter.ttk import Treeview, Style
from utils.type_utils import to_float
from customtkinter import CTkToplevel, CTkScrollbar

class Unpaid:
    def __init__(self, master, font,  access):
        #restricting access for normal user
        if access != "ADMIN": 
            messagebox.showerror("NO Access", "Access Denied")
            return None
        
        self.font = font
        self.master = master
        self.data = None
        
        self.get_unpaid()
        
        #if no unpaid user found returning to main window
        if not self.data: 
            messagebox.showinfo("NO DATA", "No unpaid invoices found.")
            return None
        
        self.window = CTkToplevel(self.master)
        self.window.wm_transient(self.master)
        self.window.title("Unpaid Invoices")
        self.window.resizable(width=False, height=False)
        self.window.geometry("500x500+350+150")
        self.window.protocol("WM_DELETE_WINDOW", self.window.destroy)

        tvStyle = Style()
        tvStyle.theme_use('clam')
        tvStyle.configure('Treeview', background='silver',foreground='black',rowheight=21,fieldbackground='silver')
        tvStyle.configure('mystyle.Treeview',font=(self.font,10))
        tvStyle.configure('mystyle.Treeview.Heading',font=(self.font ,10,'bold'),justify='center')

        scrollbar = CTkScrollbar(self.window, orientation="vertical")
        scrollbar.pack(side="right", fill="y")

        self.treeview = Treeview(self.window, style="mystyle.Treeview", columns=[1,2,3,4], height=23, yscrollcommand=scrollbar.set)
        self.treeview["show"] = "headings"

        self.treeview.heading(1, text="CUSTOMER")
        self.treeview.column(1, anchor="center")
        self.treeview.heading(2, text="INVOICE NO")
        self.treeview.column(2, anchor="center", width=60)
        self.treeview.heading(3, text="AMOUNT")
        self.treeview.column(3, anchor="center", width=70)
        self.treeview.heading(4, text="DATE")
        self.treeview.column(4, anchor="center", width=70)

        self.treeview.pack(fill="both", expand=True)

        self.tree_menu = Menu(self.treeview, tearoff=0)
        self.tree_menu.add_command(label="set paid", command=self.set_paid)
        self.treeview.bind("<Button-3>", self.show_menu)

        self.fill_data()

    def show_menu(self, event):
        selected_item = self.treeview.identify_row(event.y)
        if selected_item:
            self.treeview.selection_set(selected_item)
            self.tree_menu.post(event.x_root, event.y_root)

    def set_paid(self):
        selection = self.treeview.selection()
        if not selection:
            messagebox.showwarning("No selection", "Please select an invoice.")
            return

        item_id = selection[0]
        values = self.treeview.item(item_id, "values")

        with sqlite3.connect("datas/taxinvoice.db") as conn:
            cursor = conn.cursor()
            QUERY = """UPDATE ti_paid SET isPaid = 1 WHERE invoiceno = ?"""
            cursor.execute(QUERY, (values[1],))
            conn.commit()


        self.treeview.delete(item_id)

        messagebox.showinfo("SUCCESS", "Invoice set to paid successfully.")

    def get_unpaid(self):
        with sqlite3.connect("datas/taxinvoice.db") as conn:
            cursor = conn.cursor()
            QUERY = """SELECT * FROM ti_paid WHERE isPaid = 0;"""
            cursor.execute(QUERY)
            self.data = cursor.fetchall()


    def fill_data(self):
        if not self.data: return None
        for i in self.data:
            self.treeview.insert(
                "",
                "end",
                values=(
                    i[1],                 # customer
                    i[0],                 # invoice no
                    to_float(i[2]),       # amount (SAFE)
                    i[3]                  # date
                )
            )
