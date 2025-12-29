import sqlite3
from customtkinter import *
from tkinter import messagebox, ttk
from utils.type_utils import to_int, to_float

class AddProduct:
    def __init__(self, master, windowControl, font="Roboto"):
        self.master = master
        self.windowControl = windowControl
        self.font = font
    
        self.window = CTkToplevel(master)
        self.window.title("Add Product")
        self.window.geometry("500x500+450+150") # Increased height slightly
        self.window.resizable(False, False)
        self.window.wm_transient(master)
        self.window.protocol("WM_DELETE_WINDOW", self.destroy)

        # Title - Centered
        CTkLabel(self.window, text="Add New Product", font=(self.font, 20, "bold")).place(relx=0.5, rely=0.06, anchor="center")

        # Form Frame
        self.frame = CTkFrame(self.window, fg_color="transparent")
        self.frame.pack(padx=40, pady=(50, 10), fill="both")

        # Fields
        self.create_entry("Product Name:", 0)
        self.create_entry("HSN Code:", 1)
        self.create_entry("Rate / Price:", 2)
        self.create_entry("Quantity:", 3) # Added Quantity Field
        
        # --- GST ComboBox with Manual Entry ---
        CTkLabel(self.frame, text="GST %:", font=(self.font, 14)).grid(row=4, column=0, sticky="w", pady=10, padx=10)
        
        self.gst_var = StringVar(value="0") # Default value
        gst_values = ["0", "5", "15", "18"] # User defined values
        
        self.gst_combo = CTkComboBox(self.frame, values=gst_values, 
                                     variable=self.gst_var,
                                     font=(self.font, 14), 
                                     width=250)
        # Note: We do NOT set state="readonly" so users can type manually
        self.gst_combo.grid(row=4, column=1, pady=10, padx=10)


        # Buttons
        self.btnFrame = CTkFrame(self.window, fg_color="transparent")
        self.btnFrame.pack(pady=20)

        CTkButton(self.btnFrame, text="Add Product", font=(self.font, 15), 
                  command=self.add_product, width=150).pack(side="left", padx=10)
        
        CTkButton(self.btnFrame, text="Clear", font=(self.font, 15), 
                  fg_color="#D32F2F", hover_color="#B71C1C",
                  command=self.clear_fields, width=100).pack(side="left", padx=10)

        # Store entry widgets reference
        self.entries = [self.entry_0, self.entry_1, self.entry_2, self.entry_3]

    def create_entry(self, label_text, row):
        CTkLabel(self.frame, text=label_text, font=(self.font, 14)).grid(row=row, column=0, sticky="w", pady=10, padx=10)
        entry = CTkEntry(self.frame, font=(self.font, 14), width=250)
        entry.grid(row=row, column=1, pady=10, padx=10)
        # Dynamic variable assignment
        setattr(self, f"entry_{row}", entry)

    def add_product(self):
        name = self.entry_0.get()
        hsn = self.entry_1.get()
        rate = self.entry_2.get()
        quantity = self.entry_3.get() # Get Quantity
        gst = self.gst_combo.get()

        if not name or not rate or not quantity:
            messagebox.showerror("Error", "Product Name, Rate, and Quantity are required!")
            return

        rate = to_float(rate)
        quantity = to_int(quantity)

        if rate <= 0 or quantity <= 0:
            messagebox.showerror("Error", "Rate and Quantity must be greater than zero!")
            return

        try:
            conn = sqlite3.connect("datas/products.db")
            cursor = conn.cursor()
            # Insert Quantity
            cursor.execute("INSERT INTO products (product_name, hsn_code, rate, quantity, gst_rate) VALUES (?, ?, ?, ?, ?)",
                           (name, hsn, rate, quantity, gst))
            conn.commit()
            conn.close()
            messagebox.showinfo("Success", "Product Added Successfully")
            self.clear_fields()
        except Exception as e:
            messagebox.showerror("Error", f"Database Error: {e}")

    def clear_fields(self):
        for entry in self.entries:
            entry.delete(0, END)
        self.gst_combo.set("0")

    def destroy(self):
        self.windowControl["add_product"] = False
        self.window.destroy()

class ModifyProduct:
    def __init__(self, master, windowControl, font="Roboto"):
        self.master = master
        self.font = font
        self.selected_id = None
        self.windowControl = windowControl

        self.window = CTkToplevel(master)
        self.window.title("Modify Product")
        self.window.geometry("900x600+250+100") # Widened window slightly for extra column
        self.window.resizable(False, False)
        self.window.wm_transient(master)
        self.window.protocol("WM_DELETE_WINDOW", self.destroy)

        # --- Title Centered ---
        CTkLabel(self.window, text="Modify / Delete Product", font=(self.font, 20, "bold")).place(relx=0.5, rely=0.05, anchor="center")

        # --- Top Section: Edit Fields ---
        self.topFrame = CTkFrame(self.window)
        self.topFrame.pack(fill="x", padx=10, pady=(50, 10))

        # Define variables for entries
        self.name_var = StringVar()
        self.hsn_var = StringVar()
        self.rate_var = StringVar()
        self.qty_var = StringVar() # Quantity Variable
        self.gst_var = StringVar()

        # Row 1
        CTkLabel(self.topFrame, text="Product Name", font=(self.font, 14)).grid(row=1, column=0, padx=10, pady=5, sticky="e")
        CTkEntry(self.topFrame, textvariable=self.name_var, font=(self.font, 14), width=200).grid(row=1, column=1, padx=10, pady=5)

        CTkLabel(self.topFrame, text="HSN Code", font=(self.font, 14)).grid(row=1, column=2, padx=10, pady=5, sticky="e")
        CTkEntry(self.topFrame, textvariable=self.hsn_var, font=(self.font, 14), width=200).grid(row=1, column=3, padx=10, pady=5)

        # Row 2
        CTkLabel(self.topFrame, text="Rate", font=(self.font, 14)).grid(row=2, column=0, padx=10, pady=5, sticky="e")
        CTkEntry(self.topFrame, textvariable=self.rate_var, font=(self.font, 14), width=200).grid(row=2, column=1, padx=10, pady=5)

        CTkLabel(self.topFrame, text="Quantity", font=(self.font, 14)).grid(row=2, column=2, padx=10, pady=5, sticky="e")
        CTkEntry(self.topFrame, textvariable=self.qty_var, font=(self.font, 14), width=200).grid(row=2, column=3, padx=10, pady=5)

        # Row 3 (GST)
        CTkLabel(self.topFrame, text="GST %", font=(self.font, 14)).grid(row=3, column=0, padx=10, pady=5, sticky="e")
        gst_values = ["0", "5", "15", "18"]
        self.gst_combo_mod = CTkComboBox(self.topFrame, values=gst_values, 
                                         variable=self.gst_var,
                                         font=(self.font, 14), width=200)
        self.gst_combo_mod.grid(row=3, column=1, padx=10, pady=5)

        # --- Middle Section: Buttons ---
        self.midFrame = CTkFrame(self.window, fg_color="transparent")
        self.midFrame.pack(pady=10)

        CTkButton(self.midFrame, text="Modify", font=(self.font, 14), width=120, command=self.modify_data).pack(side="left", padx=10)
        CTkButton(self.midFrame, text="Delete", font=(self.font, 14), width=120, fg_color="#D32F2F", hover_color="#B71C1C", command=self.delete_data).pack(side="left", padx=10)
        CTkButton(self.midFrame, text="Clear", font=(self.font, 14), width=120, fg_color="grey", hover_color="darkgrey", command=self.clear_form).pack(side="left", padx=10)
        
        # Search Section
        CTkLabel(self.midFrame, text=" |   Search by Name:", font=(self.font, 14)).pack(side="left", padx=(20, 5))
        self.search_var = StringVar()
        CTkEntry(self.midFrame, textvariable=self.search_var, width=150, placeholder_text="Enter name...").pack(side="left", padx=5)
        CTkButton(self.midFrame, text="Search", font=(self.font, 14), width=80, fg_color="green", hover_color="darkgreen", command=self.search_data).pack(side="left", padx=5)


        # --- Bottom Section: Treeview ---
        self.treeFrame = CTkFrame(self.window)
        self.treeFrame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", font=(self.font, 12), rowheight=25)
        style.configure("Treeview.Heading", font=(self.font, 12, "bold"))

        scrollbar = CTkScrollbar(self.treeFrame, orientation="vertical")
        scrollbar.pack(side="right", fill="y")

        # Added Quantity Column
        columns = ("ID", "Product Name", "HSN Code", "Rate", "GST", "Quantity")
        self.tree = ttk.Treeview(self.treeFrame, columns=columns, show="headings", yscrollcommand=scrollbar.set)
        
        self.tree.heading("ID", text="ID")
        self.tree.column("ID", width=30, anchor="center")
        
        self.tree.heading("Product Name", text="Product Name")
        self.tree.column("Product Name", width=200)

        self.tree.heading("HSN Code", text="HSN Code")
        self.tree.column("HSN Code", width=100, anchor="center")

        self.tree.heading("Rate", text="Rate")
        self.tree.column("Rate", width=80, anchor="center")

        self.tree.heading("GST", text="GST %")
        self.tree.column("GST", width=80, anchor="center")

        self.tree.heading("Quantity", text="Quantity")
        self.tree.column("Quantity", width=80, anchor="center")

        self.tree.pack(fill="both", expand=True)
        scrollbar.configure(command=self.tree.yview)

        self.tree.bind("<ButtonRelease-1>", self.get_cursor)

        # Initial Load
        self.search_data()

    def get_cursor(self):
        cursor_row = self.tree.focus()
        contents = self.tree.item(cursor_row)
        row = contents['values']
        if row:
            self.selected_id = row[0]
            self.name_var.set(row[1])
            self.hsn_var.set(row[2])
            self.rate_var.set(to_float(row[3]))
            self.qty_var.set(to_int(row[5]))
            self.gst_var.set(row[4])

    def search_data(self):
        conn = sqlite3.connect("datas/products.db")
        cursor = conn.cursor()
        
        search_term = self.search_var.get()
        if search_term:
            cursor.execute("SELECT * FROM products WHERE product_name LIKE ?", ('%' + search_term + '%',))
        else:
            cursor.execute("SELECT * FROM products")
            
        rows = cursor.fetchall()
        self.tree.delete(*self.tree.get_children())
        for row in rows:
            self.tree.insert(
            '',
            'end',
            values=(
                row[0],
                row[1],
                row[2],
                to_float(row[3]),
                to_int(row[4]),
                to_int(row[5])
            )
        )

        conn.close()

    def modify_data(self):
        if not self.selected_id:
            messagebox.showerror("Error", "No product selected")
            return

        rate = to_float(self.rate_var.get())
        quantity = to_int(self.qty_var.get())

        if rate <= 0 or quantity < 0:
            messagebox.showerror("Error", "Invalid rate or quantity")
            return

        try:
            with sqlite3.connect("datas/products.db") as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE products 
                    SET product_name=?, hsn_code=?, rate=?, gst_rate=?, quantity=?
                    WHERE id=?
                """, (
                    self.name_var.get(),
                    self.hsn_var.get(),
                    rate,
                    self.gst_var.get(),
                    quantity,
                    self.selected_id
                ))
            messagebox.showinfo("Success", "Product Updated Successfully")
            self.clear_form()
            self.search_data()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def delete_data(self):
        if not self.selected_id:
            messagebox.showerror("Error", "No product selected")
            return
        
        confirmation = messagebox.askyesno("Confirm", "Are you sure you want to delete this product?")
        if confirmation:
            conn = sqlite3.connect("datas/products.db")
            cursor = conn.cursor()
            try:
                cursor.execute("DELETE FROM products WHERE id=?", (self.selected_id,))
                conn.commit()
                messagebox.showinfo("Success", "Product Deleted Successfully")
                self.clear_form()
                self.search_data()
            except Exception as e:
                messagebox.showerror("Error", str(e))
            finally:
                conn.close()

    def clear_form(self):
        self.selected_id = None
        self.name_var.set("")
        self.hsn_var.set("")
        self.rate_var.set("")
        self.qty_var.set("")
        self.gst_var.set("")
        self.search_var.set("")
        self.search_data()

    def destroy(self):
        self.windowControl["modify_product"] = False
        self.window.destroy()