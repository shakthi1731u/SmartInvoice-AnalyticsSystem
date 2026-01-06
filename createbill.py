import io
import os
import json
import qrcode
import base64
import sqlite3
import datetime
import subprocess
import configparser
from jinja2 import Template
from weasyprint import HTML
from tkinter import messagebox
from num2words import num2words
from company import addCustomer
from tkcalendar import DateEntry
from tkinter.ttk import Treeview, Style
from utils.runtime_paths import resource_path
from utils.type_utils import to_int, to_float
from utils.path_utils import get_invoice_and_challan_paths
from customtkinter import CTkRadioButton, CTkComboBox, StringVar, CTkScrollbar, IntVar
from customtkinter import CTkToplevel, CTkFrame, CTkLabel, CTkEntry, CTkButton, DoubleVar


class createBill:
    def __init__(self, master, windowControl, font="Roboto"):
        self.windowControl = windowControl
        self.master = master
        self.font = font
        self.cbill = CTkToplevel(self.master)
        self.cbill.wm_transient(self.master)
        self.cbill.title("Bill")
        self.cbill.geometry("1100x650+100+20")
        self.cbill.resizable(False, False)
        self.cbill.protocol("WM_DELETE_WINDOW", self.destroy)

        self.PNAME_CACHE = resource_path("cache", "pname.json")
        self.HSN_CACHE = resource_path("cache", "hsn.json")
        INVOICE_CONFIG = resource_path("config", "invoicedetails.ini")


        self.pname_cache_data = self.load_cache(self.PNAME_CACHE)
        self.hsn_cache_data = self.load_cache(self.HSN_CACHE)

        self.bconfig = configparser.ConfigParser()
        self.bconfig.read(INVOICE_CONFIG)
        self.invoiceno = int(self.bconfig.get("SectionOne", "invoiceno"))

        self.customerDetails = []
        self.scompanyname = StringVar()
        self.smobile = StringVar()
        self.sgst = StringVar()
        self.srepresentative = StringVar()
        self.sbuildingno = StringVar()
        self.sstreet = StringVar()
        self.scity = StringVar()
        self.sstate = StringVar(value="Karnataka")
        self.spincode = StringVar()

        self.output = []

        self.totalwithgst = DoubleVar()
        self.totalwithoutgst = DoubleVar()

        self.setWidget()

    def load_cache(self, filename):
        try:
            with open(filename, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    # saving into the cache file if the item is not present in the cache
    def save_cache(self, filename, data):
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error saving cache: {e}")

    def on_input_pname(self):
        text = self.pName.get()
        pname_cache = self.load_cache(self.PNAME_CACHE)

        if text and text not in pname_cache:
            pname_cache.append(text)
            self.save_cache(self.PNAME_CACHE, pname_cache)

        self.pnamecbx.configure(values=[item for item in pname_cache])
        self.pnamecbx.update_idletasks()

    def on_input_hsn(self):
        text = self.hsn.get()
        hsn_cache = self.load_cache(self.HSN_CACHE)

        if text and text not in hsn_cache:
            hsn_cache.append(text)
            self.save_cache(self.HSN_CACHE, hsn_cache)

        self.hsncbx.configure(values=[item for item in hsn_cache])
        self.hsncbx.update_idletasks()

    def final_fill_product_details(self):
        
        focused_item = self.tree.focus()

        if not focused_item:
            return messagebox.showwarning("WARNING", "PLEASE SELECT DATA FROM THE VIEW AND CONTINUE")
        else:
            self.rowData = self.tree.item(focused_item, "values")
            self.available_qty = to_int(self.rowData[5])
        
        if self.available_qty<=0:
            ack = messagebox.askyesno("QUESTION", "THE QUANTITY IS TOO LOW STILL DO YOU WANT TO CONTINUE")
            if not ack: 
                return 
            
        self.final_window = CTkToplevel(self.window) 
        self.final_window.title("Enter Quantity")
        self.final_window.geometry("300x250")
        self.final_window.resizable(False, False)
        self.final_window.wm_transient(self.window)
        
        # Make sure this window stays on top
        self.final_window.after(100, lambda: self.final_window.lift())
        self.final_window.after(100, lambda: self.final_window.grab_set())

        # --- UI Elements ---
        
        # Label showing Available Quantity
        CTkLabel(self.final_window, 
                 text=f"Available Quantity: {self.available_qty}", 
                 font=(self.font, 16, "bold"),
                 text_color="green").pack(pady=(30, 10))

        # Input Field for Selling Quantity
        self.sell_qty_var = StringVar()
        self.qty_entry = CTkEntry(self.final_window, 
                                  textvariable=self.sell_qty_var, 
                                  font=(self.font, 14), 
                                  width=150,
                                  placeholder_text="Enter Qty")
        self.qty_entry.pack(pady=10)
        self.qty_entry.focus() # Auto-focus so user can type immediately

        # Submit Button
        CTkButton(self.final_window, 
                  text="Add to Bill", 
                  font=(self.font, 14), 
                  command=lambda: self.validate_and_add(self.available_qty, self.rowData)).pack(pady=20)
        
        # Bind 'Enter' key to submit as well
        self.final_window.bind("<Return>", lambda event: self.validate_and_add(self.available_qty, self.rowData))

    def update_product_stock(self, sold_items):
        """
        Reduce stock ONLY for products that exist in DB.
        Manual items are ignored safely.
        """
        try:
            with sqlite3.connect("datas/products.db") as conn:
                cursor = conn.cursor()

                for item in sold_items:
                    product_name = item["Description"]
                    hsn = item["HSN"]
                    sold_qty = to_int(item["Qty"])

                    # Check if product exists
                    cursor.execute(
                        "SELECT quantity FROM products WHERE product_name=? AND hsn_code=?",
                        (product_name, hsn)
                    )
                    result = cursor.fetchone()

                    # Manual product → skip
                    if result is None:
                        continue

                    current_qty = to_int(result[0])

                    if sold_qty > current_qty:
                        raise ValueError(
                            f"Insufficient stock for {product_name} (Available: {current_qty})"
                        )

                    cursor.execute(
                        """
                        UPDATE products
                        SET quantity = quantity - ?
                        WHERE product_name=? AND hsn_code=?
                        """,
                        (sold_qty, product_name, hsn)
                    )

                # commit happens automatically on exit

        except Exception as e:
            messagebox.showerror("STOCK UPDATE ERROR", str(e))

    def validate_and_add(self, available_qty, rowData):
        self.selected_row_values = rowData
        user_input = self.sell_qty_var.get()
        
        # 1. Check if input is empty
        if not user_input:
            return messagebox.showerror("Error", "Please enter a quantity")

        try:
            # 2. Check if input is a valid number
            entered_qty = to_float(user_input)
            
            # 3. Check if input is positive
            if entered_qty <= 0:
                return messagebox.showerror("Error", "Quantity must be greater than 0")
                
            # 4. Check if input exceeds available stock
            if entered_qty > float(available_qty):
                return messagebox.showerror("Error", f"Insufficient Stock!\nOnly {available_qty} available.")
            
            # --- SUCCESS: Fill Main Window & Close Popups ---
            self.pName.set(self.selected_row_values[1])        # Name
            self.hsn.set(self.selected_row_values[2])          # HSN
            self.price.set(self.selected_row_values[3])        # Price
            self.gst.set(self.selected_row_values[4])          # GST
            self.Qnty.set(entered_qty)                         # Set the USER ENTERED Qty
            
            self.final_window.destroy() # Close Quantity Window
            self.window.destroy()       # Close Select Product Window

        except ValueError:
            return messagebox.showerror("Error", "Invalid Quantity! Please enter a number.")

        CTkLabel(self.final_window, text="Available Quantity ")

    def fill_product_details(self, event=None):
        choice = self.pName.get()
        print("Choice", choice)
        if choice=="":
            return messagebox.showerror("ERROR", "NO DATA present continue manually")
        
        # --- 1. Database Fetch ---
        try:
            connection = sqlite3.connect("datas/products.db")
            cursor = connection.cursor()
            
            # FIX 1: Add wildcards for partial search
            query = "SELECT id, product_name, hsn_code, rate, gst_rate, quantity FROM products WHERE product_name LIKE ?"
            cursor.execute(query, ('%' + choice + '%',))
            
            # FIX 2: Use fetchall() to get a list of rows
            data = cursor.fetchall()
            
            connection.close()
        except Exception as e:
            print(f"Database Error: {e}")

        if len(data)==0:
            return messagebox.showerror("ERROR", "NO DATA present continue manually")
        
        # --- 2. Window Creation (Fixes Background Issue) ---
        # Use self.cbill as the master, NOT self.master
        self.window = CTkToplevel(self.cbill) 
        self.window.title("Select Product")
        self.window.geometry("550x400+250+100")
        self.window.resizable(False, False)
        
        # Make it transient to the Bill window, so it stays on top
        self.window.wm_transient(self.cbill)
        
        # Force focus and grab (makes it modal - user must close it to go back)
        self.window.after(100, lambda: self.window.lift()) 
        self.window.after(100, lambda: self.window.grab_set()) 

        # --- 3. UI Setup ---
        # Title
        CTkLabel(self.window, text="Select Product", font=(self.font, 18, "bold")).place(relx=0.5, rely=0.05, anchor="center")
        
        # Proceed Button
        self.btn_proceed = CTkButton(self.window, text="Proceed", width=80, height=25, 
                                     font=(self.font, 12), command= self.final_fill_product_details)
        self.btn_proceed.place(relx=0.95, rely=0.05, anchor="e")

        # Tree Frame
        self.treeFrame = CTkFrame(self.window)
        self.treeFrame.pack(fill="both", expand=True, padx=10, pady=(50, 10))

        # Scrollbar
        self.scrollbar = CTkScrollbar(self.treeFrame, orientation="vertical")
        self.scrollbar.pack(side="right", fill="y")

        # --- 4. Style Configuration (Fixes Expanded Tree Issue) ---
        style = Style()
        # Do NOT call theme_use('clam') again, it resets everything.
        
        # Create a UNIQUE style name for this popup (Popup.Treeview)
        # instead of overwriting the global 'Treeview' style.
        style.configure('Popup.Treeview', 
                        background='silver',
                        foreground='black',
                        rowheight=25,
                        fieldbackground='silver',
                        font=(self.font, 10))
        
        style.configure('Popup.Treeview.Heading', 
                        font=(self.font, 10, 'bold'),
                        justify='center')
        
        # --- 5. Treeview Setup ---
        columns = ("ID", "Description", "HSN", "Price", "GST", "Qnty")
        # Apply the unique style here
        self.tree = Treeview(self.treeFrame, columns=columns, show="headings", 
                             style="Popup.Treeview", 
                             yscrollcommand=self.scrollbar.set, selectmode="browse")
        
        self.scrollbar.configure(command=self.tree.yview)

        # Columns
        self.tree.heading("ID", text="ID")
        self.tree.column("ID", width=50, anchor="w")

        self.tree.heading("Description", text="Description")
        self.tree.column("Description", width=120, anchor="w")

        self.tree.heading("HSN", text="HSN")
        self.tree.column("HSN", width=60, anchor="center")

        self.tree.heading("Price", text="Price")
        self.tree.column("Price", width=60, anchor="center")

        self.tree.heading("GST", text="GST")
        self.tree.column("GST", width=50, anchor="center")

        self.tree.heading("Qnty", text="Qnty")
        self.tree.column("Qnty", width=40, anchor="center")

        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", self.proceed)

        self.populate_data(data)

    def populate_data(self, data):
        self.tree.delete(*self.tree.get_children())
        
        for i in data:
            self.tree.insert("", "end", values=(i[0], i[1], i[2], i[3], i[4], i[5]))

    def proceed(self, event=None):
        selected = self.tree.selection()
        if not selected:
            return
        
        item = self.tree.item(selected[0])
        values = item['values']
        print(f"User Selected: {values}")
        # Add your logic here (e.g., pass data back to main window)
        self.window.destroy()
        
    def on_pname_enter(self, event=None):
        self.fill_product_details()

    def get_sumatra_path(self):
        path = resource_path(
            "third_party", "sumatra", "SumatraPDF.exe"
        )

        if not os.path.exists(path):
            return None

        return path

    def setWidget(self):
        topFrame = CTkFrame(self.cbill, height=120)
        topFrame.pack(fill="both")
        secondFrame = CTkFrame(self.cbill, height=50,
                               border_width=1, border_color="grey")
        secondFrame.pack(fill="x")
        middleFrame = CTkFrame(self.cbill)
        middleFrame.pack(fill="x")
        bottomFrame = CTkFrame(self.cbill, height=80)
        bottomFrame.pack(fill="both", expand=True)

        # top frame widget
        CTkLabel(topFrame, text="TAX INVOICE", font=(self.font, 20,
                 "bold", "underline")).place(relx=0.45, rely=0.010)
        CTkLabel(topFrame, text="Recipient Name", font=(
            self.font, 15)).place(relx=0.02, rely=0.35)
        self.company = StringVar()
        self.cmpEnt = CTkEntry(topFrame, width=150,
                               textvariable=self.company, font=(self.font, 15))
        self.cmpEnt.place(relx=0.11, rely=0.35)

        CTkLabel(
            topFrame, 
            text="Mobile", 
            font=(self.font, 15)
        ).place(relx=0.26, rely=0.35)

        self.RecipientMobileNumber = StringVar()
        self.RecipientMobileEnt = CTkEntry(
            topFrame,
            textvariable= self.RecipientMobileNumber,
            font=(self.font, 15)
        )
        self.RecipientMobileEnt.place(relx=0.30, rely=0.35)
        
        CTkLabel(
            topFrame, 
            text="City", 
            font=(self.font, 15)
        ).place(relx=0.44, rely=0.35)

        self.RecipientCity = StringVar()
        self.RecipientCityEnt = CTkEntry(
            topFrame,
            textvariable= self.RecipientCity,
            font=(self.font, 15)
        )
        self.RecipientCityEnt.place(relx=0.47, rely=0.35)

        CTkLabel(
            topFrame, 
            text="State", 
            font=(self.font, 15)
        ).place(relx=0.61, rely=0.35)

        indian_states = [
            "Andhra Pradesh","Arunachal Pradesh","Assam","Bihar","Chhattisgarh","Goa",
            "Gujarat","Haryana","Himachal Pradesh","Jharkhand","Karnataka","Kerala","Madhya Pradesh",
            "Maharashtra","Manipur","Meghalaya","Mizoram","Nagaland","Odisha","Punjab","Rajasthan",
            "Sikkim","Tamil Nadu","Telangana","Tripura","Uttar Pradesh","Uttarakhand","West Bengal"
        ]

        self.RecipientState = StringVar(value="Tamil Nadu")
        self.RecipientStateEnt = CTkComboBox(
            topFrame,
            variable= self.RecipientState,
            values = indian_states,
            font=(self.font, 15)
        )
        self.RecipientStateEnt.place(relx=0.64, rely=0.35)

        self.addcmpBtn = CTkButton(
            topFrame,
            text= "Add",
            font= (self.font, 15),
            width= 100,
            command= self.addCustomerfromcreateBill
        )
        self.addcmpBtn.place(relx=0.78, rely=0.35)

        self.cmpBtn = CTkButton(
            topFrame, 
            text="Search", 
            font=(self.font, 15), 
            width= 100,
            command= self.findCompany
        )
        self.cmpBtn.place(relx=0.89, rely=0.35)

        CTkLabel(topFrame, text="is delivery address is same as shipping address?", font=(
            self.font, 15)).place(relx=0.02, rely=0.70)
        self.isSame = IntVar(value=1)
        self.sameradio = CTkRadioButton(topFrame, text="Same", font=(self.font, 15), state="disabled", variable=self.isSame,
                                        radiobutton_width=16, radiobutton_height=16, value=1, command=self.on_click_address_radio_button)
        self.sameradio.place(relx=0.32, rely=0.70)
        self.diffradio = CTkRadioButton(topFrame, text="Not Same", font=(self.font, 15), state="disabled", radiobutton_width=16,
                                        radiobutton_height=16, variable=self.isSame, value=0, command=self.on_click_address_radio_button)
        self.diffradio.place(relx=0.38, rely=0.70)
        self.shipaddress = StringVar(value="\t\t\tChoose a address")
        CTkEntry(topFrame, width=550, state="readonly", textvariable=self.shipaddress, font=(
            self.font, 15)).place(relx=0.47, rely=0.70)

        CTkLabel(secondFrame, text="PName", font=(
            self.font, 15)).place(relx=0.02, rely=0.30)
        self.pname_cache = self.load_cache(self.PNAME_CACHE)

        self.pName = StringVar()
        self.pnamecbx = CTkComboBox(
            secondFrame, 
            font=(self.font, 15), 
            variable=self.pName, 
            width=200, 
            values=self.pname_cache_data,
        )
        self.pnamecbx.place(relx=0.07, rely=0.30)

        CTkLabel(secondFrame, text="HSN", font=(
            self.font, 15)).place(relx=0.26, rely=0.30)

        self.hsn = StringVar()
        self.hsncbx = CTkComboBox(secondFrame, font=(
            self.font, 15), variable=self.hsn, width=100, values=self.hsn_cache_data)
        self.hsncbx.place(relx=0.29, rely=0.30)

        CTkLabel(secondFrame, text="Qnty", font=(
            self.font, 15)).place(relx=0.39, rely=0.30)
        self.Qnty = StringVar(value=0.0)
        CTkEntry(secondFrame, font=(self.font, 15),
                 textvariable=self.Qnty, width=100).place(relx=0.42, rely=0.30)
        CTkLabel(secondFrame, text="Price", font=(
            self.font, 15)).place(relx=0.52, rely=0.30)
        self.price = StringVar(value=0)
        CTkEntry(secondFrame, font=(self.font, 15),
                 textvariable=self.price, width=100).place(relx=0.56, rely=0.30)
        CTkLabel(secondFrame, text="Gst", font=(
            self.font, 15)).place(relx=0.67, rely=0.30)

        self.gst = StringVar(value=0)
        gstvalues = ["0", "5", "12", "18", "28"]
        CTkComboBox(secondFrame, font=(self.font, 15), values=gstvalues,
                    variable=self.gst, width=100).place(relx=0.70, rely=0.30)

        CTkButton(secondFrame, text="Add", font=(self.font, 15),
                  command=self.addtoTV).place(relx=0.85, rely=0.30)

        tvStyle = Style()
        tvStyle.theme_use('clam')
        tvStyle.configure('Treeview', background='silver',
                          foreground='black', rowheight=21, fieldbackground='silver')
        tvStyle.configure('mystyle.Treeview', font=(self.font, 10))
        tvStyle.configure('mystyle.Treeview.Heading', font=(
            self.font, 10, 'bold'), justify='center')

        vscrollbar = CTkScrollbar(
            middleFrame, orientation="vertical", bg_color="black")
        vscrollbar.pack(fill="y", side="right")

        self.treeview = Treeview(middleFrame, column=[1, 2, 3, 4, 5, 6, 7], height=17, show="headings",
                                 style="mystyle.Treeview", yscrollcommand=vscrollbar.set)

        self.treeview.heading(1, text="DESCRIPTION")
        self.treeview.column(1, anchor="n", width=200)
        self.treeview.heading(2, text="HSN")
        self.treeview.column(2, anchor="center", width=100)
        self.treeview.heading(3, text="QUANTITY")
        self.treeview.column(3, anchor="center", width=50)
        self.treeview.heading(4, text="PRICE")
        self.treeview.column(4, anchor="center", width=100)
        self.treeview.heading(5, text="PRICE x QUANTITY")
        self.treeview.column(5, anchor="center", width=100)
        self.treeview.heading(6, text="GST %")
        self.treeview.column(6, anchor="center", width=50)
        self.treeview.heading(7, text="TOTAL")
        self.treeview.column(7, anchor="center", width=100)
        self.treeview.bind("<Double-1>", self.on_treeview_double_click2)

        self.treeview.pack(fill="x")

        CTkLabel(bottomFrame, text="Total", font=(
            self.font, 20)).place(relx=0.75, rely=0.20)
        CTkEntry(bottomFrame, font=(self.font, 20),
                 textvariable=self.totalwithgst, width=200).place(relx=0.80, rely=0.20)
        CTkButton(bottomFrame, text="Proceed", font=(self.font, 15), fg_color="green",
                  width=150, command=self.proceed).place(relx=0.83, rely=0.65)

    def addCustomerfromcreateBill(self):
        #creating data dictionary
        data = {
            "Company_Name":self.company.get(), 
            "Mobile_Number": self.RecipientMobileNumber.get(),
            "State": self.RecipientState.get(),
            "City": self.RecipientCity.get()
        }

        if not self.windowControl["add_company"]:
            self.windowControl["add_company"] = True
            addCustomer(self.master,  self.windowControl, self.font)
        

    def generatebillno(self):
        month = datetime.datetime.now().strftime("%B")
        self.billno = f"tiKEI_{month}_{self.invoiceno}"

    def initiatebill(self, rowsoftreeview):
        def print_pdf(file_path):
            sumatra_path = self.get_sumatra_path()

            if not sumatra_path:
                messagebox.showerror(
                    "Printing Error",
                    "SumatraPDF not found.\nPlease reinstall the application."
                )
                return
            
            if not os.path.exists(file_path):
                messagebox.showerror(
                    "File Missing",
                    f"PDF not found:\n{file_path}"
                )
                return

            if os.path.getsize(file_path) == 0:
                messagebox.showerror(
                    "Invalid PDF",
                    "PDF file is empty or corrupted."
                )
                return
            
            subprocess.Popen(
                [
                    sumatra_path, 
                    "-print-to-default", 
                    "-silent",
                    file_path
                ],
                shell=False
            )

        self.generatebillno()

        base_dir = os.path.dirname(os.path.abspath(__file__))
        invoice_path, _ = get_invoice_and_challan_paths(base_dir)

        pdf_path = os.path.join(invoice_path, f"{self.billno}.pdf")


        if not messagebox.askyesno("PROCEED", "ARE YOU SURE YOU WANT TO PROCEED"):
            return

        # ---- Default placeholders ----
        self.customerdcno.set(self.customerdcno.get() or "_______________")
        self.pono.set(self.pono.get() or "_______________")
        self.ewaybillno.set(self.ewaybillno.get() or "_______________")
        self.vehicle.set(self.vehicle.get() or "_______________")

        shippingdate = self.date.get_date().strftime("%d-%m-%Y")

        ack = bill(
            self.invoiceno,
            self.customerDetails,
            self.scompanyname.get(),
            self.sbuildingno.get(),
            self.sstreet.get(),
            self.scity.get(),
            self.sstate.get(),
            self.spincode.get(),
            rowsoftreeview,
            self.customerdcno.get(),
            self.pono.get(),
            shippingdate,
            self.ewaybillno.get(),
            self.vehicle.get(),
            self.totalwithgst.get(),
            tibillno= pdf_path
        )

        if ack.SUCCESS != 1:
            return

        # ---- Update stock safely ----
        self.update_product_stock(rowsoftreeview)
        self.proceeWin.destroy()

        INSERT_TI_INFO = """
        INSERT INTO ti_info(
            invoiceno, customer_name, invoice_date, time, quantity, mobile,
            customer_dc_no, Ddate, pono, EwayBillNo, Vehicle, gstNumber,
            shippingCompanyName, shippingDoorNo, shippingStreet, shippingCity,
            shippingState, shippingPincode, buyingCompanyName, buyingDoorNo,
            buyingStreet, buyingCity, buyingState, buyingPincode
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """

        INSERT_TI_DATA = """
        INSERT INTO ti_data(
            invoiceno, item_name, Hsn, quantity, rate, gst, amount
        ) VALUES (?,?,?,?,?,?,?)
        """

        INSERT_PAID = "INSERT INTO ti_paid VALUES (?, ?, ?, ?, ?)"

        date = datetime.datetime.now().strftime("%d-%m-%Y")
        time_now = datetime.datetime.now().strftime("%H:%M:%S")

        total_amount = 0.0
        for item in rowsoftreeview:
            total_amount += to_float(item["Rowtotal"])

        try:
            with sqlite3.connect("datas/taxinvoice.db") as conn:
                cursor = conn.cursor()

                # ---- Main invoice info ----
                cursor.execute(
                    INSERT_TI_INFO,
                    (
                        self.invoiceno,
                        self.customerDetails[0],
                        date,
                        time_now,
                        self.totalQnty,
                        self.customerDetails[7],
                        self.customerdcno.get(),
                        shippingdate,
                        self.pono.get(),
                        self.ewaybillno.get(),
                        self.vehicle.get(),
                        self.customerDetails[8],
                        self.scompanyname.get(),
                        self.sbuildingno.get(),
                        self.sstreet.get(),
                        self.scity.get(),
                        self.sstate.get(),
                        self.spincode.get(),
                        self.customerDetails[0],
                        self.customerDetails[1],
                        self.customerDetails[2],
                        self.customerDetails[3],
                        self.customerDetails[4],
                        self.customerDetails[5]
                    )
                )

                # ---- Line items ----
                for item in rowsoftreeview:
                    cursor.execute(
                        INSERT_TI_DATA,
                        (
                            self.invoiceno,
                            item["Description"],
                            item["HSN"],
                            item["Qty"],
                            item["Price"],
                            item["GST"],
                            item["Rowtotal"]
                        )
                    )

                # ---- Payment status ----
                paid = messagebox.askyesno("PROCEED", "Is the customer paid?")
                cursor.execute(
                    INSERT_PAID,
                    (self.invoiceno, self.customerDetails[0], total_amount, date, int(paid))
                )

            # ---- Invoice number increment (ONLY after success) ----
            self.invoiceno += 1
            self.bconfig.set("SectionOne", "invoiceno", str(self.invoiceno))
            INVOICE_CONFIG = resource_path("config", "invoicedetails.ini")
            with open(INVOICE_CONFIG, "w") as configfile:
                self.bconfig.write(configfile)

        except Exception as e:
            messagebox.showerror("DATABASE ERROR", str(e))
            return

        self.cbill.destroy()

        if messagebox.askyesno("PROCEED", "Invoice created successfully!\nDo you want to print the PDF?"):
            print_pdf(pdf_path)
            
    def proceed(self, event=None):
        if self.cmpEnt.cget("state") == "normal":
            return messagebox.showerror("ERROR", "PLEASE SELECT COMPANY")
        if self.company.get() == "" or self.shipaddress.get() == "":
            return messagebox.showerror("ERROR", "PLEASE SELECT COMPANY")
        rows = []
        i = 0
        self.totalQnty = 0.0

        for item in self.treeview.get_children():
            row = self.treeview.item(item)['values']
            self.totalQnty += to_float(row[2])

            rows.append({
                "SiNo": i + 1,
                "Description": row[0],
                "HSN": row[1],
                "Qty": to_float(row[2]),
                "Price": to_float(row[3]),
                "PricexQuantity": to_float(row[4]),
                "GST": row[5],
                "Rowtotal": to_float(row[6])
            })
            i += 1

        if (rows == []):
            return messagebox.showerror("ERROR", "PLEASE ADD SOME PRODUCTS")

        self.proceeWin = CTkToplevel(self.cbill)
        self.proceeWin.wm_transient(self.cbill)

        self.proceeWin.title("PROCEED")
        self.proceeWin.geometry("400x300+400+200")
        self.proceeWin.resizable(False, False)

        CTkLabel(self.proceeWin, text="PROCEED", font=(
            self.font, 20)).place(relx=0.35, rely=0.05)
        CTkLabel(self.proceeWin, text="Customer DCNO", font=(
            self.font, 15)).place(relx=0.10, rely=0.20)
        self.customerdcno = StringVar()
        CTkEntry(self.proceeWin, textvariable=self.customerdcno,
                 font=(self.font, 15)).place(relx=0.5, rely=0.20)

        CTkLabel(self.proceeWin, text="P.O. No", font=(
            self.font, 15)).place(relx=0.10, rely=0.35)
        self.pono = StringVar()
        CTkEntry(self.proceeWin, textvariable=self.pono,
                 font=(self.font, 15)).place(relx=0.5, rely=0.35)

        CTkLabel(self.proceeWin, text="Date", font=(
            self.font, 15)).place(relx=0.10, rely=0.50)
        self.date = DateEntry(self.proceeWin, width=20, height=15, background="darkblue",
                              foreground="white", borderwidth=2, borderradius=100)
        self.date.place(relx=0.5, rely=0.50)

        CTkLabel(self.proceeWin, text="E-Way Bill No",
                 font=(self.font, 15)).place(relx=0.10, rely=0.65)
        self.ewaybillno = StringVar()
        CTkEntry(self.proceeWin, textvariable=self.ewaybillno,
                 font=(self.font, 15)).place(relx=0.5, rely=0.65)

        CTkLabel(self.proceeWin, text="Vehicle No ", font=(
            self.font, 15)).place(relx=0.10, rely=0.80)
        self.vehicle = StringVar()
        CTkEntry(self.proceeWin, textvariable=self.vehicle,
                 font=(self.font, 15)).place(relx=0.5, rely=0.80)

        output = CTkButton(self.proceeWin, text="Proceed", width=100, command=lambda: self.initiatebill(
            rows), font=(self.font, 15)).place(relx=0.70, rely=0.05)

    def set_shipping_address(self):
        comb = f"{self.scompanyname.get()} {self.sbuildingno.get()} {self.sstreet.get()} {self.scity.get()} {self.sstate.get()} {self.spincode.get()}"
        self.shipaddress.set(comb)
        self.addressWin.destroy()

    def on_click_address_radio_button(self):
        tempcompany = self.scompanyname.get()
        tempbuidling = self.sbuildingno.get()
        tempstreet = self.sstreet.get()
        tempstate = self.sstate.get()
        tempcity = self.scity.get()
        temprepresentative = self.srepresentative.get()
        tempmobile = self.smobile.get()
        tempgst = self.sgst.get()
        temppincode = self.spincode.get()

        self.scompanyname.set("")
        self.srepresentative.set("")
        self.smobile.set("")
        self.sgst.set("")
        self.sstate.set("Karnataka")
        self.scity.set("")
        self.sstreet.set("")
        self.sbuildingno.set("")
        self.spincode.set("")

        if self.isSame.get() == 1:
            self.shipaddress.set(self.company.get())
        else:
            self.addressWin = CTkToplevel(self.cbill)
            self.addressWin.wm_transient(self.cbill)
            self.addressWin.title("SHIPPING ADDRESS")
            self.addressWin.geometry("400x370+400+150")
            self.addressWin.resizable(False, False)
            self.addressWin.protocol("WM_DELETE_WINDOW", lambda: self.sdestroy(
                tempcompany, tempbuidling, tempstreet, tempstate, tempcity, temprepresentative, tempmobile, tempgst, temppincode))

            CTkLabel(self.addressWin, text="Companyname", font=(
                self.font, 15)).place(relx=0.05, rely=0.05)
            CTkLabel(self.addressWin, text="Building no", font=(
                self.font, 15)).place(relx=0.05, rely=0.20)
            CTkLabel(self.addressWin, text="Street", font=(
                self.font, 15)).place(relx=0.05, rely=0.35)
            CTkLabel(self.addressWin, text="City", font=(
                self.font, 15)).place(relx=0.05, rely=0.50)
            CTkLabel(self.addressWin, text="State", font=(
                self.font, 15)).place(relx=0.05, rely=0.65)
            CTkLabel(self.addressWin, text="Pincode", font=(
                self.font, 15)).place(relx=0.05, rely=0.80)

            indian_states = [
                "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
                "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
                "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
                "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
                "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
                "Uttar Pradesh", "Uttarakhand", "West Bengal"
            ]

            CTkEntry(self.addressWin, width=250, textvariable=self.scompanyname, font=(
                self.font, 15)).place(relx=0.30, rely=0.05)
            CTkEntry(self.addressWin, width=250, textvariable=self.sbuildingno, font=(
                self.font, 15)).place(relx=0.30, rely=0.20)
            CTkEntry(self.addressWin, width=250, textvariable=self.sstreet, font=(
                self.font, 15)).place(relx=0.30, rely=0.35)
            CTkEntry(self.addressWin, width=250, textvariable=self.scity,
                     font=(self.font, 15)).place(relx=0.30, rely=0.50)
            self.statecmbbx = CTkComboBox(self.addressWin, values=indian_states,
                                          variable=self.sstate, width=250, state="readonly", font=(self.font, 15))
            self.statecmbbx.place(relx=0.30, rely=0.65)
            CTkEntry(self.addressWin, width=250, textvariable=self.spincode, font=(
                self.font, 15)).place(relx=0.30, rely=0.80)
            CTkButton(self.addressWin, text="Submit", font=(self.font, 15), fg_color="green",
                      width=150, command=self.set_shipping_address).place(relx=0.35, rely=0.90)

    def addtoTV(self):
        if len(self.pName.get()) == 0:
            return messagebox.showerror("ERROR", "PLEASE ENTER PRODUCT DESCRIPTION")
        if self.Qnty.get() == "0.0":
            return messagebox.showerror("ERROR", "PLEASE ENTER THE QUANTITY")
        if self.Qnty.get() == "":
            return messagebox.showerror("ERROR", "PLEASE ENTER THE QUANTITY")
        if self.price.get() == 0:
            return messagebox.showerror("ERROR", "PLEASE ENTER PRICE")
        if len(self.gst.get()) == 0:
            self.gst.set(0)
        if self.Qnty.get().isalpha():
            return messagebox.showerror("ERROR", "QUANTITY CONTAINS ALPHABET")
        if self.price.get().isalpha():
            return messagebox.showerror("ERROR", "PRICE CONTAINS ALPHABET")
        if self.gst.get().isalpha():
            return messagebox.showerror("ERROR", "GST CONTAINS ALPHABET")

        self.on_input_pname()
        self.on_input_hsn()

        try:
            qty = to_float(self.Qnty.get())
            price = to_float(self.price.get())
            gst = to_float(self.gst.get())
        except ValueError:
            return messagebox.showerror("ERROR", "Invalid numeric input")

        priceXquantity = qty * price
        gstamount = 0
        
        if gst > 0:
            gstamount = (priceXquantity * gst) / 100

        rowtotal = round(priceXquantity + gstamount, 2)

        self.totalwithoutgst.set(round(self.totalwithoutgst.get() + priceXquantity, 2))
        self.totalwithgst.set(round(self.totalwithgst.get() + rowtotal, 2))


        self.treeview.insert("", "end", values=(str(self.pName.get()), str(self.hsn.get()), str(
            self.Qnty.get()), str(self.price.get()), str(priceXquantity), f"{self.gst.get()}%", str(rowtotal)))
        
        self.pName.set("")
        self.hsn.set("")
        self.Qnty.set(0)
        self.price.set(0)
        self.gst.set(0)

    def on_treeview_double_click(self, event=None):
        selected = self.companyTV.focus()
        if not selected:
            return

        values = self.companyTV.item(selected, "values")
        if not values or len(values) < 5:
            return messagebox.showerror("ERROR", "Invalid selection")

        customer_id = values[4]

        try:
            with sqlite3.connect("datas/customerDB.db") as con:
                cur = con.cursor()
                cur.execute("""
                    SELECT company_name, building_no, street, city, state,
                        pincode, representative, mobile_number, gst_number, id
                    FROM customers
                    WHERE id = ?
                """, (customer_id,))
                row = cur.fetchone()

            if row is None:
                return messagebox.showerror("ERROR", "Customer data not found")

            # IMPORTANT: overwrite safely
            self.customerDetails = list(row)

        except Exception as e:
            return messagebox.showerror("DATABASE ERROR", str(e))

        # ---- UI FILL (SAFE) ----
        company_str = f"{row[0]}, {row[1]}, {row[2]}, {row[3]}"
        self.company.set(row[0])
        self.RecipientCity.set(row[3])
        self.RecipientState.set(row[4])
        self.RecipientMobileNumber.set(row[7])

        self.scompanyname.set(row[0])
        self.sbuildingno.set(row[1])
        self.sstreet.set(row[2])
        self.scity.set(row[3])
        self.sstate.set(row[4])
        self.spincode.set(row[5])
        self.srepresentative.set(row[6])
        self.smobile.set(row[7])
        self.sgst.set(row[8])

        self.shipaddress.set(company_str)

        self.diffradio.configure(state="normal")
        self.sameradio.configure(state="normal")
        self.cmpEnt.configure(state="disabled")
        self.cmpBtn.configure(state="disabled")

        self.findC.destroy()

    def on_treeview_double_click2(self, event):
        item = self.treeview.focus()
        if not item:
            return

        values = self.treeview.item(item, "values")
        if not values:
            return

        if (messagebox.askyesno("DELETE", f"ARE YOU SURE YOU WANT TO DELETE {values[0]}")):
            self.treeview.delete(self.treeview.focus())

            self.totalwithgst.set(
                round(to_float(self.totalwithgst.get()) - to_float(values[6]), 2)
            )

            self.totalwithoutgst.set(
                round(to_float(self.totalwithoutgst.get()) - to_float(values[4]), 2)
            )

            if self.totalwithgst.get() <= 0 or self.totalwithoutgst.get() <= 0:
                self.totalwithgst.set(0)
                self.totalwithoutgst.set(0)
        return

    def findCompany(self):
        def searchCompany(column, value):
            print(f"Column = {column} Value = {value} Column Type = {type(column)} Value Type={type(value)}")
            with sqlite3.connect("datas/customerDB.db") as con:
                cur = con.cursor()

                QUERY = f"""
                SELECT company_name, building_no, street, city, state,
                    pincode, representative, mobile_number, gst_number, id
                FROM customers
                WHERE {column} LIKE ?
                """
                cur.execute(QUERY, (f"%{value}%",))
                return cur.fetchall()

        if not self.company.get() and not self.RecipientMobileNumber.get() and not self.RecipientCity.get():
            return messagebox.showwarning("WARNING", "PLEASE ENTER CUSTOMER DETAILS TO FIND RELATED DATA")

        self.findC = CTkToplevel(self.cbill)
        self.findC.geometry("750x250+300+100")
        self.findC.wm_transient(self.cbill)

        vscrollbar = CTkScrollbar(self.findC, orientation="vertical")
        vscrollbar.pack(fill="y", side="right")

        self.companyTV = Treeview(
            self.findC,
            column=[1, 2, 3, 4, 5],
            show="headings",
            yscrollcommand=vscrollbar.set
        )

        self.companyTV.heading(1, text="Recipient")
        self.companyTV.column(1, anchor="n", width=100)
        self.companyTV.heading(2, text="Mobile")
        self.companyTV.column(2, anchor="n", width=100)
        self.companyTV.heading(3, text="City")
        self.companyTV.column(3, anchor="n", width=80)
        self.companyTV.heading(4, text="State")
        self.companyTV.column(4, anchor="n", width=80)
        self.companyTV.heading(5, text="ID")
        self.companyTV.column(5, anchor="n", width=50)

        self.companyTV.pack(fill="both", expand=True)
        self.companyTV.bind("<Double-1>", self.on_treeview_double_click)

        flagSearched = False
        if self.company.get():
            rows = searchCompany("company_name", self.company.get())
            if rows==[]:
                self.findC.destroy()
                return messagebox.showinfo("ZERO DATA", "NO Record Found")
            self.findC.title("Company Details searched by Company Name")
            flagSearched = True
        if not flagSearched and self.RecipientMobileNumber.get():
            rows = searchCompany("mobile_number", self.RecipientMobileNumber.get())
            if rows==[]:
                self.findC.destroy()
                return messagebox.showinfo("ZERO DATA", "NO Record Found")
            self.findC.title("Company Details searched by Mobile Number")
            flagSearched = True
        if not flagSearched and self.RecipientCity.get():
            rows = searchCompany("city", self.RecipientCity.get())
            if rows==[]:
                self.findC.destroy()
                return messagebox.showinfo("ZERO DATA", "NO Record Found")
            self.findC.title("Company Details searched by City Name")

        for row in rows:
            self.companyTV.insert("", "end", values=(row[0], row[7], row[3], row[4], row[9]))

    def sdestroy(self, tempcompany, tempbuidling, tempstreet, tempstate, tempcity, temprepresentative, tempmobile, tempgst, temppincode):
        self.scompanyname.set(tempcompany)
        self.sbuildingno.set(tempbuidling)
        self.sstreet.set(tempstreet)
        self.sstate.set(tempstate)
        self.scity.set(tempcity)
        self.srepresentative.set(temprepresentative)
        self.smobile.set(tempmobile)
        self.sgst.set(tempgst)
        self.spincode.set(temppincode)
        self.isSame.set(1)
        self.addressWin.destroy()

    def destroy(self):
        self.windowControl["tax_invoice"] = False
        self.cbill.destroy()


class bill:
    def __init__(self, invoiceno, customerDetails, scompanyname, sbuilding_no, sstreet, scity, sstate, spincode, sales, customerdcno, pono, date, ewaybillno, vehicle, totalwithgst, gstoptional="", tibillno=""):
        def encode_image(image_path):
            with open(image_path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
            
        self.SUCCESS = 0
        self.invoiceno = invoiceno
        self.companydetails = customerDetails
        self.scompanyname = scompanyname
        self.sbuilding_no = sbuilding_no
        self.sstreet = sstreet
        self.scity = scity
        self.sstate = sstate
        self.spincode = spincode
        self.customerdcno = customerdcno
        self.pono = pono
        self.date = date
        self.ewaybillno = ewaybillno
        self.vehicle = vehicle
        self.sales = sales
        self.totalwithgst = round(to_float(totalwithgst), 2)

        config = configparser.ConfigParser()
        config.read(resource_path("config", "configuration.ini"))
        
        self.Default_Company_Name= config.get("CompanyDetails", "company_name")
        self.Default_Company_Address= config.get("CompanyDetails", "address")
        self.Default_Company_Mobile=  config.get("CompanyDetails", "phone")
        self.Default_Company_Email=  config.get("CompanyDetails", "email")
        self.Default_Company_GST=  config.get("CompanyDetails", "gstin")
        self.logo_path = config.get("CompanyDetails", "logo_image")

        self.Default_Company_BankName = config.get("BankDetails", "bank_name")
        self.Default_Company_BankBranch = config.get("BankDetails", "branch")
        self.Default_Company_AccountNo = config.get("BankDetails", "account_no")
        self.Default_Company_IFSC = config.get("BankDetails", "ifsc")
        self.Default_Company_UPINAME = config.get("BankDetails", "upi_name")
        self.Default_Company_UPIID = config.get("BankDetails", "upi_id")

        if self.logo_path and os.path.exists(self.logo_path):
            self.logo_base64 = "data:image/png;base64," + encode_image(self.logo_path)
        else:
            self.logo_base64 = ""

        
        if gstoptional == "":
            self.gstnumber = self.companydetails[8]
        else:
            self.gstnumber = gstoptional

        if tibillno == "":
            self.tibillno = "temp_taxinvoice"
        else:
            self.tibillno = tibillno

        if self.scompanyname == "":
            self.scompanyname = "-------------------------------"
        self.setHTMLcontent()

    def generate_upi_qr_base64(self, upi_id, name):
        """
        Generates a base64 PNG QR for UPI ID
        """
        upi_uri = f"upi://pay?pa={upi_id}&pn={name}&cu=INR"

        qr = qrcode.QRCode(
            version=1,                 # Controls complexity
            error_correction=qrcode.constants.ERROR_CORRECT_Q,
            box_size=6,                # SIZE CONTROL (important)
            border=2                   # WHITE BORDER
        )
        qr.add_data(upi_uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        return base64.b64encode(buffer.read()).decode("utf-8")

    def setHTMLcontent(self):
        def num_to_indian_words(num):
            words = num2words(num, lang="en_IN")
            words = words.replace("million", "lakhs").replace("billion", "crores")
            return words + " only"

        def encode_image(image_path):
            with open(image_path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")

        base64_logo = self.logo_base64 
        
        base64_upi = "data:image/png;base64," + self.generate_upi_qr_base64(
            self.Default_Company_UPIID,
            self.Default_Company_Name
        )

        total_words = num_to_indian_words(self.totalwithgst)
        today_date = datetime.datetime.now().strftime("%d-%m-%Y")

        invoice_data = {
            "image_path": base64_logo,
            "invoiceno": self.invoiceno,
            "gstno": self.gstnumber,
            "invoiceDate": today_date,
            "cdcno": self.customerdcno,
            "poNo": self.pono,
            "cdDate": self.date,
            "ewaybill": self.ewaybillno,
            "vehicleNo": self.vehicle,
            "CustomerCompanyName": self.companydetails[0],
            "buildingNo": self.companydetails[1],
            "street": self.companydetails[2],
            "city": self.companydetails[3],
            "state": self.companydetails[4],
            "pincode": self.companydetails[5],
            "scompanyname": self.scompanyname,
            "sbuildingNo": self.sbuilding_no,
            "sstreet": self.sstreet,
            "scity": self.scity,
            "sstate": self.sstate,
            "spincode": self.spincode,
            "items": self.sales,
            "totalwithgst": self.totalwithgst,
            "totalinwords": total_words,
            "upi_image": base64_upi,
            "Default_Company_Name": self.Default_Company_Name,
            "Default_Company_Address": self.Default_Company_Address,
            "Default_Company_Mobile": self.Default_Company_Mobile,
            "Default_Company_Email": self.Default_Company_Email,
            "Default_Company_GST": self.Default_Company_GST,
            "Default_Company_BankName": self.Default_Company_BankName,
            "Default_Company_BankBranch": self.Default_Company_BankBranch,
            "Default_Company_AccountNo": self.Default_Company_AccountNo,
            "Default_Company_IFSC": self.Default_Company_IFSC,
            "Default_Company_UPINAME": self.Default_Company_UPINAME,
            "Default_Company_UPIID": self.Default_Company_UPIID
        }

        self.HTML_TEMPLATE = Template("""
       <!DOCTYPE html>
        <html>
            <head>
                <title>TAX INVOICE</title>
                <style>
                    @page{
                        size: A4;
                        margin: 0mm;
                    }
                                    
                    @media print {
                        .page-break { 
                            page-break-after: always; 
                            margin-top: 10mm;
                        }
                    }

                    body {
                        margin-top: 30px;
                        padding: 0;
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        background-color: #f4f4f4; 
                    }

                    #dclabel {
                        font-weight: bold;
                        font-size: 15px;
                        text-align: center;
                        margin: 0px;
                    }

                    .cmpDetails {
                        text-align: center;  
                        padding: 0;
                        margin: 0;
                    }

                    hr {
                        padding-bottom: 0px;
                        margin-bottom: 0px;
                    }

                    .cmpDetails #companyName {
                        font-size: 20px;
                        font-stretch: narrower;
                        font-weight: bold;
                        margin: 0px;
                    }

                    .cmpDetails #companyAddress {
                        font-size: 12px;
                        margin-top: 0px;
                        margin-bottom: 5px;
                    }

                    #companyName img {
                        width: 60px;
                        vertical-align: middle;
                        margin-right: 10px;
                    }

                    .cmpDetails #mobandmail {
                        font-size: 15px;
                        font-weight: bold;
                        margin-top: 0px;
                        margin-bottom: 10px;
                    }

                    .invoicedata{
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        width: 90%;
                        margin-left: 40px;
                        margin-top: 5px;
                        padding-top: 5px;
                    }
                        
                    .invoice_details {
                        flex: 1;
                    }          

                    .invoicedata p {
                        color: rgb(0, 0, 0);
                        font-size: 15px;
                        font-weight: bold;
                        padding-left: 0%;
                        padding-bottom: 0px;
                        margin-bottom: 3px;
                    }

                    .container {
                        display: flex;
                        justify-content: space-between;
                        width: 90%;
                        margin: 10px auto;
                    }

                    .company_data {
                        width: 48%;
                        border: 1px solid black;
                        border-radius: 5px;
                        background-color: rgb(223, 208, 226);
                        padding-bottom: 3px;
                        box-sizing: border-box;
                        margin-right: 20px; 
                    }

                    .customer_data {
                        width: 48%;
                        border: 1px solid black;
                        border-radius: 5px;
                        background-color: rgb(223, 208, 226);
                        padding-bottom: 3px;
                        box-sizing: border-box;
                    }

                    .main_table {
                        width: 90%;
                        margin: 20px auto;
                        margin-top: 5px;
                        margin-bottom: 0px;
                        border-collapse: collapse;
                    }

                    .main_table th {
                        font-size: 15px;
                        height: 40px;
                        color: #f4f4f4;
                        background-color: rgb(182, 120, 245);
                        justify-content: center;
                        text-align: center;
                    }

                    .main_table td {
                        background-color: light-grey;
                        border: 0.5px solid grey;
                        text-align: center;
                    }

                    .main_table tr:nth-child(even) {
                        background-color: #f2f2f2;
                    }

                    .signature-box {
                        display: flex;
                        justify-content: space-between;
                        width: 90%;
                        margin: 10px auto;
                    }

                    .signature-box p {
                        margin: 5px 10px;
                        display: flex;
                        text-align: center;
                        justify-content: space-between;
                    }

                    .right-align {
                        text-align: right;
                        flex-grow: 1;
                    }

                    .payment_details {
                        display: flex;
                        align-items: center;
                        justify-content: space-around;
                        width: 90%;
                        margin: 10px auto;
                        border: 1px solid grey;
                        border-radius: 20px;
                        padding: 10px;
                        box-sizing: border-box;
                    }

                    .bank_details {
                        width: 40%;
                        font-size: 14px;
                    }
                                      
                    .upi{
                        width: 20%;
                        text-align: center;
                    }

                    .upi_details{
                        width: 25%;
                        text-align: center;
                        font-size: 13px;
                        word-wrap: break-word;
                        overflow-wrap: break-word;
                    }
                </style>
            </head>
            <body lang="en">
                <p style="margin-top:0px; margin-bottom: 5px;" id="dclabel"><u>TAX INVOICE</u></p>
                <div class="cmpDetails">  
                    <p id="companyName"><img src="{{image_path}}" alt="logo"><span>{{Default_Company_Name}}</span> </p>
                    <P id="companyAddress">{{Default_Company_Address}}</P>    
                    <p id="mobandmail">Phone No: {{Default_Company_Mobile}} | Email : {{Default_Company_Email}}</p>
                    <hr style="width: 90%;">
                </div>
                
                <div class="invoicedata">
                    <div class="invoice_details">
                        <p id="dc_no">Invoice No: {{invoiceno}}</p> 
                        <p id="invoice_date">Date: {{invoiceDate}}</p>
                        <p>GSTIN : {{Default_Company_GST}}</p>
                    </div>
                    <div style="text-align: right; padding-right: 10px;">
                        <p>Your D.C.NO: {{cdcno}} <bold style="color: black;">|</bold> Date: {{cdDate}}</p>
                        <p>P.O. No: {{poNo}} <bold style="color: black;">|</bold> E-Way Bill No: {{ewaybill}}</p>
                        <p>Vehicle No: {{vehicleNo}}</p>        
                    </div>
                </div>
                <div class="container">
                    <div class="company_data">
                        <p style="font-weight: bold; font-size: 20px; margin-top:0px; margin-bottom:5px; padding-left:  5px;">Billing Address</p>
                        <p style="padding-left: 10px; margin-top:0px; font-weight: bold; margin-top:0px; margin-bottom:5px;">{{CustomerCompanyName}}</p>
                        <p style="padding-left: 10px; margin-top:0px; margin-bottom:5px;">No.{{buildingNo}}, {{street}}, {{city}},{{state}}, {{pincode}}</p>
                        <p style="padding-left: 10px; font-weight: bold; font-size: 15px; margin-top:0px; margin-bottom:5px;">GSTIN : {{gstno}}</p>
                    </div>
                    <div class="customer_data">
                        <p style="font-weight: bold; font-size: 20px; margin-top:0px; margin-bottom:5px; padding-left:  5px;">Shipping Address</p>
                        <p style="padding-left: 10px; margin-top:0px; font-weight: bold; margin-top:0px; margin-bottom:5px;">{{scompanyname}}</p>
                        <p style="padding-left: 10px; margin-top:0px; margin-bottom:5px;">No.{{sbuildingNo}}, {{sstreet}}, {{scity}},{{sstate}}, {{spincode}}.</p>
                    </div>
                </div>
                <table class="main_table">
                    <tr>
                        <th style="width:5%; border-top-left-radius: 5px;">SI.NO</th>
                        <th style="width:30%">Description</th>
                        <th style="width:10%">HSN Code</th>
                        <th style="width:10%">Qty</th>
                        <th style="width:15%">Rate</th>
                        <th style="width:10%">GST</th>
                        <th style="width:35%; border-top-right-radius: 5px;">Amount<br><sub>(after gst)</sub></th>
                    </tr>
                    {% for item in items %}
                        <tr>
                            <td style="padding: 8px; font-size: 13px;">{{item.SiNo}}</td>
                            <td style="padding: 8px; font-size: 13px;">{{item.Description}}</td>
                            <td style="padding: 8px; font-size: 13px;">{{item.HSN}}</td>  
                            <td style="padding: 8px; font-size: 13px;">{{item.Qty}}</td>
                            <td style="padding: 8px; font-size: 13px;">{{item.Price}}</td>
                            <td style="padding: 8px; font-size: 13px;">{{item.GST}}</td>
                            <td style="padding: 8px; font-size: 13px;">{{item.Rowtotal}}</td>
                        </tr>          
                    {% endfor %}
                    <tr style="line-height: 8px;">
                        <td colspan="6"><p style="font-weight:bold; font-size: 13px; text-align:right; padding-right: 10px;">Grand Total</p></td>
                        <td colspan="1"><p style="font-weight:bold; font-size: 13px; text-align:center;">{{totalwithgst}}</p></td>
                    </tr>
                    <tr style="line-height: 8px;">
                        <td colspan="3" rowspan="1" style="padding : 0px; margin: 0px;"><p style="font-size: 12px; font-weight:bold; text-align:bottom;">JOB WORK ONLY / NOT FOR SALE</p></td>
                        <td colspan="4" rowspan="1"><p style="font-size: 12px; font-weight:bold; text-align:bottom; align-items:bottom;">Value of Goods........................</p></td>
                    </tr>
                    <tr style="line-height: 30px;">
                        <td colspan="7" style="text-align: left; font-weight: bold; font-size: 13px;">Total Amount in Words : {{totalinwords}}</td>
                    </tr>
                </table>
                <div class="payment_details">
                    <div class="bank_details">
                        <p>
                            <strong style="padding-left: 50px; padding-bottom: 10px;"><u>Bank Details</u></strong><br>
                            <strong>Bank Name:</strong> {{Default_Company_BankName}}<br>
                            <strong>Branch:</strong> {{Default_Company_BankBranch}}<br>
                            <strong>Account No:</strong>{{Default_Company_AccountNo}}<br>
                            <strong>IFSC Code:</strong>{{Default_Company_IFSC}}
                        </p>
                    </div>
                    <div style="width:1px; background:#999; height:120px;"></div>
                    <div class="upi">
                        <img 
                            src="{{upi_image}}" 
                            alt="UPI QR"
                            style="
                                width:120px;
                                height:120px;
                                padding: 6px;
                                background: white;
                                border: 1px solid #aaa;
                                object-fit: contain;
                                display: block;
                                margin: auto;
                            ">
                    </div>
                    <div class="upi_details">
                        <p style="font-weight: bold; text-align: center;">UPI DETAILS</p>
                        <P>{{Default_Company_UPINAME}}</P>
                        <p style="
                            text-align: center;
                            word-break: break-all;
                            font-size: 12px;
                        ">
                            {{Default_Company_UPIID}}
                        </p>
                    </div>
                </div>
                <div class="signature-box">
                    <div class="receiver_signature">
                        <p>Received the above goods in good condition.</p>
                        <br><br>
                        <p style="text-align: center;"><strong>Receiver’s Signature & Seal</strong> 
                    </div>  
                    <div class="sender_signature">    
                        <p><strong>For {{Default_Company_Name}}</strong></p>      
                        <br><br> 
                        <p style="text-align: center;">Authorised Signature</p>
                    </div>
                </div>              
            </body>
        </html>
        """)

        html_content = self.HTML_TEMPLATE.render(**invoice_data)

        if self.tibillno == "temp_taxinvoice":
            pdf_path = resource_path("bills", "invoice", "temp_invoice.pdf")
        else:
            pdf_path = self.tibillno

        HTML(string=html_content).write_pdf(pdf_path)
        self.SUCCESS = 1
