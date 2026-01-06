import os
import json
import base64
import datetime
import sqlite3
import subprocess
import configparser
from weasyprint import HTML
from jinja2 import Template
from tkinter import messagebox
from num2words import num2words
from tkcalendar import DateEntry
from tkinter.ttk import Treeview, Style
from utils.runtime_paths import resource_path
from utils.path_utils import get_invoice_and_challan_paths
from customtkinter import CTkComboBox, StringVar, CTkScrollbar, IntVar
from customtkinter import CTkToplevel, CTkFrame, CTkLabel, CTkEntry, CTkButton, CTkRadioButton

base_dir = os.path.dirname(os.path.abspath(__file__))
_, challan_path = get_invoice_and_challan_paths(base_dir)

class createDC:
    def __init__(self, master, font="Roboto"):
        self.master = master
        self.font = font
        self.cDC = CTkToplevel(self.master)
        self.cDC.wm_transient(self.master)
        self.cDC.title("Bill")
        self.cDC.geometry("1100x650+100+20")
        self.cDC.resizable(False, False)
        self.cDC.protocol("WM_DELETE_WINDOW", self.destroy)

        self.PNAME_CACHE = "cache/pname.json"
        self.HSN_CACHE = "cache/hsn.json"

        self.pname_cache_data = self.load_cache(self.PNAME_CACHE)
        self.hsn_cache_data = self.load_cache(self.HSN_CACHE)

        self.dconfig = configparser.ConfigParser()
        self.dconfig.read("config/dcdetails.ini")
        self.dcno = int(self.dconfig.get("SectionOne", "dcno"))

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

        self.setWidget()

    def load_cache(self, filename):
        try:
            if os.path.exists(filename):
                with open(filename, "r") as f:
                    return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
        return []

    # saving into the cache file if the item is not present in the cache
    def save_cache(self, filename, data):
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error saving cache: {e}")

    def get_sumatra_path(self):
        path = resource_path(
            "third_party", "sumatra", "SumatraPDF.exe"
        )

        if not os.path.exists(path):
            return None

        return path

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

    def setWidget(self):
        topFrame = CTkFrame(self.cDC, height=120)
        topFrame.pack(fill="both")
        secondFrame = CTkFrame(self.cDC, height=50,
                               border_width=1, border_color="grey")
        secondFrame.pack(fill="x")
        middleFrame = CTkFrame(self.cDC)
        middleFrame.pack(fill="x")
        bottomFrame = CTkFrame(self.cDC, height=80)
        bottomFrame.pack(fill="both", expand=True)

        # top frame widget
        CTkLabel(topFrame, text="DELIVERY CHALLAN", font=(
            self.font, 20, "bold", "underline")).place(relx=0.45, rely=0.010)
        CTkLabel(topFrame, text="Company Name", font=(
            self.font, 15)).place(relx=0.02, rely=0.35)
        self.company = StringVar()
        self.cmpEnt = CTkEntry(topFrame, width=800,
                               textvariable=self.company, font=(self.font, 15))
        self.cmpEnt.place(relx=0.12, rely=0.35)
        self.cmpBtn = CTkButton(topFrame, text="Search", font=(
            self.font, 15), command=self.findCompany)
        self.cmpBtn.place(relx=0.85, rely=0.35)

        CTkLabel(topFrame, text="is delivery address is same as shipping address?", font=(
            self.font, 15)).place(relx=0.02, rely=0.70)
        self.isSame = IntVar(value=1)
        self.sameradio = CTkRadioButton(topFrame, text="Same", font=(self.font, 15), state="disabled", variable=self.isSame,
                                        radiobutton_width=16, radiobutton_height=16, value=1, command=self.on_click_address_radio_button)
        self.sameradio.place(relx=0.32, rely=0.70)
        self.diffradio = CTkRadioButton(topFrame, text="Not Same", font=(self.font, 15), state="disabled", radiobutton_width=16,
                                        radiobutton_height=16, variable=self.isSame, value=0, command=self.on_click_address_radio_button)
        self.diffradio.place(relx=0.38, rely=0.70)
        self.shipaddress = StringVar(value="\t\t\tselect a company")
        CTkEntry(topFrame, width=550, state="readonly", textvariable=self.shipaddress, font=(
            self.font, 15)).place(relx=0.47, rely=0.70)

        CTkLabel(secondFrame, text="PName", font=(
            self.font, 15)).place(relx=0.02, rely=0.30)

        self.pName = StringVar()
        self.pnamecbx = CTkComboBox(secondFrame, font=(
            self.font, 15), variable=self.pName, width=250, values=self.pname_cache_data)
        self.pnamecbx.place(relx=0.07, rely=0.30)

        CTkLabel(secondFrame, text="Qnty", font=(
            self.font, 15)).place(relx=0.31, rely=0.30)
        self.Qnty = StringVar(value=0.0)
        CTkEntry(secondFrame, font=(self.font, 15),
                 textvariable=self.Qnty, width=150).place(relx=0.34, rely=0.30)
        CTkLabel(secondFrame, text="HSN", font=(
            self.font, 15)).place(relx=0.49, rely=0.30)

        self.hsn = StringVar()
        self.hsncbx = CTkComboBox(secondFrame, font=(
            self.font, 15), variable=self.hsn, width=150, values=self.hsn_cache_data)
        self.hsncbx.place(relx=0.52, rely=0.30)

        CTkLabel(secondFrame, text="Remark", font=(
            self.font, 15)).place(relx=0.67, rely=0.30)
        self.remark = StringVar()
        CTkEntry(secondFrame, font=(self.font, 15),
                 textvariable=self.remark, width=120).place(relx=0.72, rely=0.30)

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

        self.treeview = Treeview(middleFrame, column=[1, 2, 3, 4], height=18, show="headings",
                                 style="mystyle.Treeview", yscrollcommand=vscrollbar.set)

        self.treeview.heading(1, text="DESCRIPTION")
        self.treeview.column(1, anchor="n", width=300)
        self.treeview.heading(2, text="QUANTITY")
        self.treeview.column(2, anchor="center", width=50)
        self.treeview.heading(3, text="HSN")
        self.treeview.column(3, anchor="center", width=50)
        self.treeview.heading(4, text="REMARK")
        self.treeview.column(4, anchor="center", width=100)
        self.treeview.bind("<Double-1>", self.on_treeview_double_click2)
        self.treeview.pack(fill="x")

        CTkButton(bottomFrame, text="Proceed", font=(self.font, 15), fg_color="green",
                  width=150, command=self.proceed).place(relx=0.83, rely=0.45)

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
            self.addressWin = CTkToplevel(self.cDC)
            self.addressWin.wm_transient(self.cDC)
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

    def proceed(self):
        if self.company.get() == "" or self.shipaddress.get() == "":
            return messagebox.showerror("ERROR", "PLEASE SELECT COMPANY")
        if self.cmpEnt.cget("state") == "normal":
            return messagebox.showerror("ERROR", "PLEASE SELECT COMPANY")
        rows = []
        i = 0
        self.totalQnty = 0
        for item in self.treeview.get_children():
            row = self.treeview.item(item)['values']
            self.totalQnty += float(row[1])
            rows.append(
                {"SiNo": i+1, "Description": row[0], "Qty": row[1], "HSNCode": row[2], "Remark": row[3]})
            i += 1
        if (rows == []):
            return messagebox.showerror("ERROR", "PLEASE ADD SOME PRODUCTS")

        self.proceeWin = CTkToplevel(self.cDC)
        self.proceeWin.wm_transient(self.cDC)

        self.proceeWin.title("PROCEED")
        self.proceeWin.geometry("400x300+400+200")
        self.proceeWin.resizable(False, False)

        CTkLabel(self.proceeWin, text="PROCEED", font=(
            self.font, 20)).place(relx=0.35, rely=0.05)
        CTkLabel(self.proceeWin, text="Customer DCNO", font=(
            self.font, 15)).place(relx=0.10, rely=0.30)
        self.customerdcno = StringVar()
        CTkEntry(self.proceeWin, textvariable=self.customerdcno,
                 font=(self.font, 15)).place(relx=0.5, rely=0.30)

        CTkLabel(self.proceeWin, text="Date", font=(
            self.font, 15)).place(relx=0.10, rely=0.45)
        self.date = DateEntry(self.proceeWin, width=20, height=15, background="darkblue",
                              foreground="white", borderwidth=2, borderradius=100)
        self.date.place(relx=0.5, rely=0.45)

        CTkLabel(self.proceeWin, text="E-Way Bill No",
                 font=(self.font, 15)).place(relx=0.10, rely=0.60)
        self.ewaybillno = StringVar()
        CTkEntry(self.proceeWin, textvariable=self.ewaybillno,
                 font=(self.font, 15)).place(relx=0.5, rely=0.60)

        CTkLabel(self.proceeWin, text="Vehicle No ", font=(
            self.font, 15)).place(relx=0.10, rely=0.75)
        self.vehicle = StringVar()
        CTkEntry(self.proceeWin, textvariable=self.vehicle,
                 font=(self.font, 15)).place(relx=0.5, rely=0.75)

        output = CTkButton(self.proceeWin, text="Proceed", width=100, command=lambda: self.initiatebill(
            rows), font=(self.font, 15)).place(relx=0.70, rely=0.05)

    def generatebillno(self):
        month = datetime.datetime.now().strftime("%B")
        self.billno = f"dcKEI_{month}_{self.dcno}"

    def initiatebill(self, rows):
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
                shell=False)

        self.generatebillno()
        # if user doesn't want to move any further they can cancel the process by clicking no.
        msg = messagebox.askyesno(
            "PROCEED", "ARE YOU SURE YOU WANT TO PROCEED")
        if (not msg):
            return

        # setting up the customer dcno, pono, ewaybillno and vehicle no if they are empty so they
        # can enter the datas manualy in the invoice.
        if (self.customerdcno.get() == ""):
            self.customerdcno.set("_______________")
        if (self.ewaybillno.get() == ""):
            self.ewaybillno.set("_______________")
        if (self.vehicle.get() == ""):
            self.vehicle.set("_______________")

        # getting the shipping date from proceed window datepicker
        shippingdate = self.date.get_date().strftime("%d-%m-%Y")

        # creating bill
        ack = bill(self.dcno, self.customerDetails, self.scompanyname.get(), self.sbuildingno.get(), self.sstreet.get(), self.scity.get(), self.sstate.get(
        ), self.spincode.get(), rows, self.customerdcno.get(), shippingdate, self.ewaybillno.get(), self.vehicle.get(), dcbillno=self.billno)

        if (ack.SUCCESS == 1):
            self.proceeWin.destroy()

        INSERTQUERY1 = "INSERT INTO dc_info(dc_id, customer_name, dc_date, time, quantity, mobile, customer_dc_no, Ddate, EwayBillNo, Vehicle,  gstNumber, shippingCompanyName, shippingDoorNo, shippingStreet, shippingCity, shippingState, shippingPincode, buyingCompanyName, buyingDoorNo, buyingStreet, buyingCity, buyingState, buyingPincode) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        INSERTQUERY2 = "INSERT INTO dc_data(dc_id, item_name, quantity, Hsn, remark) VALUES(?, ?, ?, ?, ?)"

        connection = sqlite3.connect("datas/deliverychallan.db")
        cursor = connection.cursor()
        self.time = datetime.datetime.now().strftime("%H:%M:%S")
        date = datetime.datetime.now().strftime("%d-%m-%Y")
        shipping_address = "{}, {},{}, {}, {}, {}".format(self.scompanyname.get(), self.sbuildingno.get(
        ), self.sstreet.get(), self.scity.get(), self.sstate.get(), self.spincode.get())
        cursor.execute(INSERTQUERY1, (self.dcno, self.customerDetails[0], date, self.time, self.totalQnty, self.customerDetails[7], self.customerdcno.get(), shippingdate, self.ewaybillno.get(), self.vehicle.get(), self.customerDetails[8], self.scompanyname.get(
        ), self.sbuildingno.get(), self.sstreet.get(), self.scity.get(), self.sstate.get(), self.spincode.get(), self.customerDetails[0], self.customerDetails[1], self.customerDetails[2], self.customerDetails[3], self.customerDetails[4], self.customerDetails[5]))
        connection.commit()

        for row in rows:
            cursor.execute(
                INSERTQUERY2, (self.dcno, row["Description"], row["Qty"], row["HSNCode"], row["Remark"]))
            connection.commit()

        connection.close()

        self.dcno += 1
        self.dconfig.set("SectionOne", "dcno", str(self.dcno))

        with open("config/dcdetails.ini", "w") as configfile:
            self.dconfig.write(configfile)

        self.cDC.destroy()

        # if user decides to print the pdf they can by clicking yes
        msg = messagebox.askyesno(
            "PROCEED", "Invoice created successfully!\nDo you want to print the PDF?")
        if msg:
            month = datetime.datetime.now().strftime("%B")
            year = datetime.datetime.now().strftime("%Y")
            day = datetime.datetime.now().strftime("%d")

            print_pdf(os.path.abspath(
                f"bills/deliverychallan/{year}/{month}-{year}/{day}-{month}/{self.billno}.pdf"))

    def addtoTV(self):
        if len(self.pName.get()) == 0:
            return messagebox.showerror("ERROR", "PLEASE ENTER PRODUCT DESCRIPTION")
        if self.Qnty.get() == 0.0:
            return messagebox.showerror("ERROR", "QUANTITY IS TOO LOW")
        if self.Qnty.get().isalpha():
            return messagebox.showerror("ERROR", "QUANTITY CONTAINS ALPHABET")
        if self.remark.get() == "":
            self.remark.set("-")

        self.on_input_pname()
        self.on_input_hsn()

        self.treeview.insert("", "end", values=(
            self.pName.get(), self.Qnty.get(), self.hsn.get(), self.remark.get()))
        self.pName.set("")
        self.Qnty.set(0.0)
        self.remark.set("")
        self.hsn.set("")

    def on_treeview_double_click(self, event):
        values = self.companyTV.item(self.companyTV.focus(), "values")
        stringForm = f"{values[0]}, {values[1]}, {values[2]}, {values[3]}"

        for i in self.customerDetails:
            if (i[9] == int(values[4])):
                self.customerDetails = i
                break

        self.company.set(stringForm)

        self.scompanyname.set(self.customerDetails[0])
        self.srepresentative.set(self.customerDetails[6])
        self.smobile.set(self.customerDetails[7])
        self.sgst.set(self.customerDetails[8])
        self.sstate.set(self.customerDetails[4])
        self.scity.set(self.customerDetails[3])
        self.sstreet.set(self.customerDetails[2])
        self.sbuildingno.set(self.customerDetails[1])
        self.spincode.set(self.customerDetails[5])

        self.shipaddress.set(stringForm)

        self.diffradio.configure(state="normal")
        self.sameradio.configure(state="normal")
        self.cmpEnt.configure(state="disabled")
        self.cmpBtn.configure(state="disabled")
        self.findC.destroy()

    def on_treeview_double_click2(self, event):
        values = self.treeview.item(self.treeview.focus(), "values")
        if (messagebox.askyesno("DELETE", f"ARE YOU SURE YOU WANT TO DELETE {values[0]}")):
            self.treeview.delete(self.treeview.focus())
            self.total.set(self.total.get() - float(values[4]))
        return

    def findCompany(self):
        def searchCompany(companyName):
            con = sqlite3.connect("datas/customerDB.db")
            cur = con.cursor()

            SEARCHQUERY = f"SELECT company_name, building_no, street, city, state, pincode, representative, mobile_number, gst_number, id FROM customers WHERE company_name LIKE '%{companyName}%'"
            cur.execute(SEARCHQUERY)
            row = self.customerDetails = cur.fetchall()
            cur.close()
            con.close()
            return row

        if (len(self.company.get()) == 0):
            return messagebox.showwarning("WARNING", "PLEASE ENTER COMPANY NAME")

        self.findC = CTkToplevel(self.cDC)
        self.findC.title("Select company")
        self.findC.attributes('-topmost', True)
        self.findC.geometry("700x250+300+100")
        self.findC.wm_transient(self.cDC)

        tvStyle = Style()
        tvStyle.theme_use('clam')
        tvStyle.configure('Treeview', background='silver',
                          foreground='black', rowheight=21, fieldbackground='silver')
        tvStyle.configure('mystyle.Treeview', font=(self.font, 10))
        tvStyle.configure('mystyle.Treeview.Heading', font=(
            self.font, 10, 'bold'), justify='center')

        vscrollbar = CTkScrollbar(
            self.findC, orientation="vertical", bg_color="black")
        vscrollbar.pack(fill="y", side="right")

        self.companyTV = Treeview(
            self.findC, column=[1, 2, 3, 4, 5], style="mystyle.Treeview", show="headings")
        self.companyTV.heading(1, text="Company")
        self.companyTV.column(1, anchor="center", width=300)
        self.companyTV.heading(2, text="Representative")
        self.companyTV.column(2, anchor="center", width=100)
        self.companyTV.heading(3, text="Mobile")
        self.companyTV.column(3, anchor="center", width=100)
        self.companyTV.heading(4, text="City")
        self.companyTV.column(4, anchor="center", width=100)
        self.companyTV.heading(5, text="ID")
        self.companyTV.column(5, anchor="center", width=100)

        self.companyTV.bind("<Double-1>", self.on_treeview_double_click)
        self.companyTV.pack(fill="both", expand=True)

        for i in searchCompany(self.company.get()):
            self.companyTV.insert("", "end", values=(
                i[0], i[6], i[7], i[3], i[9]))

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
        self.cDC.destroy()


class bill:
    def __init__(self, dcno, customerDetails, scompanyname, sbuilding_no, sstreet, scity, sstate, spincode, sales, customerdcno, date, ewaybillno, vehicle, gstoptional="", dcbillno=""):
        self.SUCCESS = 0
        self.dcno = dcno
        self.companydetails = customerDetails
        self.scompanyname = scompanyname
        self.sbuilding_no = sbuilding_no
        self.sstreet = sstreet
        self.scity = scity
        self.sstate = sstate
        self.spincode = spincode
        self.customerdcno = customerdcno
        self.date = date
        self.ewaybillno = ewaybillno
        self.vehicle = vehicle
        self.sales = sales

        if gstoptional == "":
            self.gstnumber = self.companydetails[8]
        else:
            self.gstnumber = gstoptional

        if dcbillno == "":
            self.dcbillno = "temp_deliverychallan"
        else:
            self.dcbillno = dcbillno

        if self.scompanyname == "":
            self.scompanyname = "-------------------------------"

        self.setHTMLcontent()

    def setHTMLcontent(self):
        def num_to_indian_words(num):
            words = num2words(num)
            words = words.replace("million", "lakhs").replace(
                "billion", "crores")
            return words

        def encode_image(image_path):
            with open(image_path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")

        # for logo
        image_path = "images/icons/icon_50x39.png"
        base64_image = f"data:image/png;base64,{encode_image(image_path)}"
        """ words = num_to_indian_words(self.total) """

        # for date
        date = datetime.datetime.now().strftime("%d-%m-%Y")

        invoice_data = {
            "image_path": base64_image,
            "dcno": self.dcno,
            "gstno": self.gstnumber,
            "invoiceDate": date,
            "cdcno": self.customerdcno,
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
            "items": self.sales
        }

        html_template = Template("""
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
                        margin-top: 40px;
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
                        margin: 0px;
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

                    .invoicedata {
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        width: 90%;
                        margin: auto;
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
                        margin: 20px auto;
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
                        border-collapse: collapse;
                    }

                    .main_table th {
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
                        margin: 20px auto;
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
                </style>
            </head>
            <body lang="en">
                <p style="margin-top:0px; margin-bottom: 5px;" id="dclabel"><u>Delivery Challan</u></p>
                <div class="cmpDetails">  
                    <p id="companyName"><img src="{{image_path}}" alt="logo"><span>ABDCEFGH ENGINEERING INDUSTRIES</span> </p>
                    <P id="companyAddress">No.4, 11th Cross, Patel Channappa Industrial Estate, Andhrahalli Main Road, Near Peenya 2nd Stage, Banglore-91.</P>    
                    <p id="mobandmail">Phone No: 8147689901 | Email : kar411engineering@gmail.com</p>
                    <hr style="width: 90%;">
                </div>
                
                <div class="invoicedata">
                    <div class="invoice_details">
                        <p id="dc_no">DC_No: {{dcno}}</p> 
                        <p id="invoice_date">Date: {{invoiceDate}}</p>
                        <p>GSTIN : 29ARDPR1854M1Z7</p>
                    </div>
                    <div style="text-align: right; padding-right: 10px;">
                        <p>Your D.C.NO: {{cdcno}} <bold style="color: black;">|</bold> Date: {{cdDate}}</p>
                        <p>E-Way Bill No: {{ewaybill}}</p>
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
                        <th style="width:10%; border-top-left-radius: 5px;">SI.NO</th>
                        <th style="width:40%">Description</th>
                        <th style="width:10%">HSN Code</th>
                        <th style="width:10%">Qty</th>
                        <th style="width:25%; border-top-right-radius: 5px;">Remarks</th>
                    </tr>
                    {% for item in items %}
                        <tr>
                            <td style="padding: 8px;">{{item.SiNo}}</td>
                            <td style="padding: 8px;">{{item.Description}}</td>
                            <td style="padding: 8px;">{{item.HSNCode}}</td>  
                            <td style="padding: 8px;">{{item.Qty}}</td>
                            <td style="padding: 8px;">{{item.Remark}}</td>
                        </tr>          
                    {% endfor %}
                    <tr>
                        <td colspan="3" style="padding : 0px; margin: 0px;"><p style="font-weight:bold; text-align:bottom; align-items:bottom;">JOB WORK ONLY / NOT FOR SALE</p></td>
                        <td colspan="2"><p style="font-weight:bold; text-align:bottom; align-items:bottom;">Value of Goods........................</p></td>
                    </tr>
                </table>
                <div class="signature-box">
                    <div class="receiver_signature">
                        <p>Received the above goods in good condition.</p>
                        <br><br>
                        <p style="text-align: center;"><strong>Receiver’s Signature & Seal</strong> 
                    </div>  
                    <div class="sender_signature">    
                        <p><strong>For KARNATAKA ENGINEERING INDUSTRIES</strong></p>      
                        <br><br> 
                        <p style="text-align: center;">Authorised Signature</p>
                    </div>
                </div>              
            </body>
        </html>
        """)

        html_content = html_template.render(**invoice_data)

        month = datetime.datetime.now().strftime("%B")
        year = datetime.datetime.now().strftime("%Y")
        day = datetime.datetime.now().strftime("%d")

        if self.dcbillno == "temp_deliverychallan":
            pdf_file = "bills/deliverychallan/temp_deliverychallan.pdf"
        else:
            pdf_file = f"bills/deliverychallan/{year}/{month}-{year}/{day}-{month}/{self.dcbillno}.pdf"

        HTML(string=html_content).write_pdf(pdf_file)

        self.SUCCESS = 1
