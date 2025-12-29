from customtkinter import CTkLabel, CTkEntry, CTkToplevel, CTk, CTkFrame, CTkButton, CTkComboBox, StringVar, CTkScrollbar
import sqlite3
from tkinter.ttk import Treeview, Style
from tkinter import messagebox, END


class addCustomer:
    def __init__(self, master, windowControl, font="Roboto"):
        self.windowControl = windowControl
        self.master = master
        self.font = font
        self.companyTL = CTkToplevel(self.master)
        self.companyTL.iconbitmap("images/add_icon.png")
        self.companyTL.wm_transient(self.master)
        self.companyTL.title("Add Entity")
        self.companyTL.geometry("400x600+500+50")
        self.companyTL.resizable(False, False)
        self.companyTL.protocol("WM_DELETE_WINDOW", self.destroy)

        self.setWidget()

    def setWidget(self):
        CTkLabel(self.companyTL, text="Entity Name", font=(
            self.font, 15)).place(relx=0.05, rely=0.03)
        self.companyName = StringVar()
        CTkEntry(self.companyTL, width=200, textvariable=self.companyName,
                 font=(self.font, 15)).place(relx=0.45, rely=0.03)

        CTkLabel(self.companyTL, text="Representative", font=(
            self.font, 15)).place(relx=0.05, rely=0.13)
        self.representative = StringVar()
        CTkEntry(self.companyTL, width=200, textvariable=self.representative, font=(
            self.font, 15)).place(relx=0.45, rely=0.13)

        CTkLabel(self.companyTL, text="GST Number", font=(
            self.font, 15)).place(relx=0.05, rely=0.23)
        self.gstNumber = StringVar()
        CTkEntry(self.companyTL,  width=200, textvariable=self.gstNumber,
                 font=(self.font, 15)).place(relx=0.45, rely=0.23)

        CTkLabel(self.companyTL, text="Mobile Number", font=(
            self.font, 15)).place(relx=0.05, rely=0.33)
        self.mobileNumber = StringVar()
        CTkEntry(self.companyTL, width=200, textvariable=self.mobileNumber, font=(
            self.font, 15)).place(relx=0.45, rely=0.33)

        CTkLabel(self.companyTL, text="----------------------------------Address------------------------------------",
                 font=(self.font, 15, "bold")).place(relx=0.0, rely=0.40)

        CTkLabel(self.companyTL, text="Building No", font=(
            self.font, 15)).place(relx=0.05, rely=0.47)
        self.buildingNo = StringVar()
        CTkEntry(self.companyTL, width=200, textvariable=self.buildingNo,
                 font=(self.font, 15)).place(relx=0.45, rely=0.47)

        CTkLabel(self.companyTL, text="Street", font=(
            self.font, 15)).place(relx=0.05, rely=0.57)
        self.street = StringVar()
        CTkEntry(self.companyTL, width=200, textvariable=self.street,
                 font=(self.font, 15)).place(relx=0.45, rely=0.57)

        CTkLabel(self.companyTL, text="City/Town/Village",
                 font=(self.font, 15)).place(relx=0.05, rely=0.67)
        self.city = StringVar()
        CTkEntry(self.companyTL, width=200, textvariable=self.city,
                 font=(self.font, 15)).place(relx=0.45, rely=0.67)

        indian_states = [
            "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
            "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
            "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
            "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
            "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
            "Uttar Pradesh", "Uttarakhand", "West Bengal"
        ]
        CTkLabel(self.companyTL, text="State", font=(
            self.font, 15)).place(relx=0.05, rely=0.77)
        self.state = StringVar(value="Karnataka")
        self.statecombo = CTkComboBox(self.companyTL, width=200, variable=self.state,
                                      values=indian_states, state="readonly", font=(self.font, 15))
        self.statecombo.place(relx=0.45, rely=0.77)

        CTkLabel(self.companyTL, text="Pincode", font=(
            self.font, 15)).place(relx=0.05, rely=0.87)
        self.pincode = StringVar()
        CTkEntry(self.companyTL, width=200, textvariable=self.pincode,
                 font=(self.font, 15)).place(relx=0.45, rely=0.87)

        CTkButton(self.companyTL, text="Add Customer",
                  command=self.storeData).place(relx=0.35, rely=0.95)

    def storeData(self):
        def getCompanies(con, cur):
            getQuerry = "SELECT company_name from customers"
            cur.execute(getQuerry)
            con.commit()
            return cur.fetchall()

        def insertData(con, cur, *args):
            INSERTQUERRY = "INSERT INTO customers(company_name, representative, gst_number, mobile_number, building_no,street, city, state, pincode) values(?,?,?,?,?,?,?,?,?)"
            cur.execute(INSERTQUERRY, (args[0], args[1], args[2],
                        args[3], args[4], args[5], args[6], args[7], args[8]))
            con.commit()
            con.close()
            messagebox.showinfo("SUCCESS", "DATAS INSERTED SUCCESSFULLY")
            return True

        try:
            self.conn = sqlite3.connect("datas/customerDB.db")
            self.cur = self.conn.cursor()

            TBCQUERY = """CREATE TABLE IF NOT EXISTS customers (
                          id INTEGER PRIMARY KEY AUTOINCREMENT, 
                          company_name TEXT NOT NULL,
                          representative TEXT NULL,
                          gst_number TEXT,
                          mobile_number TEXT,
                          building_no TEXT,
                          street TEXT,
                          city TEXT,
                          state TEXT,
                          pincode TEXT
            )"""

            self.cur.execute(TBCQUERY)
            self.conn.commit()

            complis = getCompanies(self.conn, self.cur)

            for i in complis:
                if (i[0] == self.companyName.get()):
                    if ((messagebox.askquestion("QUESTION", "THIS Company name already exists do you want to still store it ?".upper(), parent=self.companyTL) == "yes")):
                        break
                    else:
                        return

            if (len(self.companyName.get()) < 3):
                return messagebox.showwarning("WARNING", "ENTITY NAME IS TOO SHORT")
            if (len(self.representative.get()) < 3):
                self.representative.set("____")
            if (len(self.gstNumber.get()) < 3):
                self.gstNumber.set("______")
            if (self.mobileNumber.get().isalpha()):
                return messagebox.showwarning("WARNING", "MOBILE NUMBER CARRIES ALPHABET")
            if (len(self.mobileNumber.get()) < 9):
                return messagebox.showwarning("WARNING", "CHECK THE MOBILE NUMBER")

            # inserting data into database
            acknowledgment = insertData(self.conn, self.cur, self.companyName.get(), self.representative.get(), self.gstNumber.get(), self.mobileNumber.get(),
                                        self.buildingNo.get(), self.street.get(), self.city.get(), self.state.get(), self.pincode.get())
            if (acknowledgment):
                self.companyName.set("")
                self.representative.set("")
                self.gstNumber.set("")
                self.mobileNumber.set("")
                self.buildingNo.set("")
                self.street.set("")
                self.city.set("")
                self.pincode.set("")

        except Exception as e:
            print("Error:", e)

    def destroy(self):
        self.windowControl["add_company"] = False
        self.companyTL.destroy()


class modCustomer:
    def __init__(self, master, windowControl, font="Roboto"):
        self.windowControl = windowControl
        self.master = master
        self.font = font
        self.companyTL = CTkToplevel(self.master)
        """ self.companyTL.attributes("-topmost", True) """
        self.companyTL.wm_transient(self.master)
        self.companyTL.title("Modify or Delete Entity")
        self.companyTL.geometry("1000x600+150+50")
        self.companyTL.resizable(False, False)

        self.widgetFrame = CTkFrame(self.companyTL, height=200)
        self.widgetFrame.pack(fill="both", expand=True)
        self.treeviewFrame = CTkFrame(self.companyTL, height=600)
        self.treeviewFrame.pack(fill="both", expand=True)
        self.companyTL.protocol("WM_DELETE_WINDOW", self.destroy)

        self.setWidget()

    def setWidget(self):
        CTkLabel(self.widgetFrame, text="Entity Name", font=(
            self.font, 15)).place(relx=0.02, rely=0.03)
        self.companyName = StringVar()
        CTkEntry(self.widgetFrame, width=350, textvariable=self.companyName, font=(
            self.font, 15)).place(relx=0.14, rely=0.03)

        CTkLabel(self.widgetFrame, text="Representative",
                 font=(self.font, 15)).place(relx=0.50, rely=0.03)
        self.representative = StringVar()
        CTkEntry(self.widgetFrame, width=350, textvariable=self.representative, font=(
            self.font, 15)).place(relx=0.61, rely=0.03)

        CTkLabel(self.widgetFrame, text="GST Number", font=(
            self.font, 15)).place(relx=0.02, rely=0.20)
        self.gstNumber = StringVar()
        CTkEntry(self.widgetFrame,  width=200, textvariable=self.gstNumber, font=(
            self.font, 15)).place(relx=0.12, rely=0.20)

        CTkLabel(self.widgetFrame, text="Mobile Number", font=(
            self.font, 15)).place(relx=0.34, rely=0.20)
        self.mobileNumber = StringVar()
        CTkEntry(self.widgetFrame, width=200, textvariable=self.mobileNumber, font=(
            self.font, 15)).place(relx=0.46, rely=0.20)

        CTkLabel(self.widgetFrame, text="Building No", font=(
            self.font, 15)).place(relx=0.67, rely=0.20)
        self.buildingNo = StringVar()
        CTkEntry(self.widgetFrame, width=200, textvariable=self.buildingNo, font=(
            self.font, 15)).place(relx=0.76, rely=0.20)

        CTkLabel(self.widgetFrame, text="Street", font=(
            self.font, 15)).place(relx=0.02, rely=0.40)
        self.street = StringVar()
        CTkEntry(self.widgetFrame, width=200, textvariable=self.street,
                 font=(self.font, 15)).place(relx=0.08, rely=0.40)

        CTkLabel(self.widgetFrame, text="City/Town/Village",
                 font=(self.font, 15)).place(relx=0.30, rely=0.40)
        self.city = StringVar()
        CTkEntry(self.widgetFrame, width=200, textvariable=self.city,
                 font=(self.font, 15)).place(relx=0.43, rely=0.40)

        indian_states = [
            "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
            "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
            "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
            "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
            "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
            "Uttar Pradesh", "Uttarakhand", "West Bengal"
        ]
        CTkLabel(self.widgetFrame, text="State", font=(
            self.font, 15)).place(relx=0.65, rely=0.40)
        self.state = StringVar(value="Karnataka")
        self.statecombo = CTkComboBox(self.widgetFrame, width=260, variable=self.state,
                                      values=indian_states, state="readonly", font=(self.font, 15))
        self.statecombo.place(relx=0.70, rely=0.40)

        CTkLabel(self.widgetFrame, text="Pincode", font=(
            self.font, 15)).place(relx=0.68, rely=0.60)
        self.pincode = StringVar()
        CTkEntry(self.widgetFrame, width=200, textvariable=self.pincode,
                 font=(self.font, 15)).place(relx=0.75, rely=0.60)

        self.modify = CTkButton(self.widgetFrame, text="Modify", font=(
            self.font, 15), command=self.updateData)
        self.modify.place(relx=0.05, rely=0.75)
        self.delete = CTkButton(self.widgetFrame, text="Delete", font=(
            self.font, 15), fg_color="darkred", command=self.deleteData)
        self.delete.place(relx=0.20, rely=0.75)
        self.clear = CTkButton(self.widgetFrame, text="Clear", font=(
            self.font, 15), fg_color="blue", command=self.clearData)
        self.clear.place(relx=0.35, rely=0.75)
        self.search = CTkButton(self.widgetFrame, text="Search", font=(
            self.font, 15), fg_color="green", command=self.searchData)
        self.search.place(relx=0.80, rely=0.75)

        # adding treeview
        tvStyle = Style()
        tvStyle.theme_use('clam')
        tvStyle.configure('Treeview', background='silver',
                          foreground='black', rowheight=21, fieldbackground='silver')
        tvStyle.configure('mystyle.Treeview', font=(self.font, 10))
        tvStyle.configure('mystyle.Treeview.Heading', font=(
            self.font, 10, 'bold'), justify='center')

        yscrollbar = CTkScrollbar(self.treeviewFrame, orientation="vertical")
        yscrollbar.pack(side="right", fill="y")
        xscrollbar = CTkScrollbar(self.treeviewFrame, orientation="horizontal")
        xscrollbar.pack(side="bottom", fill="x")
        self.treeview = Treeview(self.treeviewFrame, column=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10], style="mystyle.Treeview",
                                 height=10, show="headings", yscrollcommand=yscrollbar.set, xscrollcommand=xscrollbar.set)

        self.treeview.heading(1, text="Entity Name")
        self.treeview.column(1, width=100, anchor="center")
        self.treeview.heading(2, text="Representative")
        self.treeview.column(2, width=100, anchor="center")
        self.treeview.heading(3, text="GST")
        self.treeview.column(3, width=100, anchor="center")
        self.treeview.heading(4, text="Mobile")
        self.treeview.column(4, width=100, anchor="center")
        self.treeview.heading(5, text="Building No")
        self.treeview.column(5, width=50, anchor="center")
        self.treeview.heading(6, text="Street")
        self.treeview.column(6, width=100, anchor="center")
        self.treeview.heading(7, text="City")
        self.treeview.column(7, width=100, anchor="center")
        self.treeview.heading(8, text="State")
        self.treeview.column(8, width=100, anchor="center")
        self.treeview.heading(9, text="Pincode")
        self.treeview.column(9, width=50, anchor="center")
        self.treeview.heading(10, text="ID")
        self.treeview.column(10, width=0, anchor="center")

        self.treeview.pack(fill="both", expand=True)
        self.treeview.bind("<<TreeviewSelect>>", self.on_treeview_select)

    def on_treeview_select(self, event):
        selected = self.treeview.focus()

        if (not selected):
            return

        item_values = self.treeview.item(selected, "values")
        if not item_values:
            return

        self.companyName.set(item_values[0])  # Company Name
        self.representative.set(item_values[1])  # Representative Name
        self.gstNumber.set(item_values[2])  # GST Number
        self.mobileNumber.set(item_values[3])  # Mobile Number
        self.buildingNo.set(item_values[4])  # Building Number
        self.street.set(item_values[5])  # Street
        self.city.set(item_values[6])  # City
        self.state.set(item_values[7])  # State
        self.pincode.set(item_values[8])

    def clearData(self):
        self.companyName.set("")
        self.representative.set("")
        self.gstNumber.set("")
        self.mobileNumber.set("")
        self.buildingNo.set("")
        self.street.set("")
        self.city.set("")
        self.state.set("Karnataka")
        self.pincode.set("")

        self.treeview.delete(*self.treeview.get_children())

    def updateData(self):
        def update(*args):
            con = sqlite3.connect("datas/customerDB.db")
            cur = con.cursor()

            UPDATEQUERY = "UPDATE customers SET company_name = ?, representative = ?, gst_number = ?, mobile_number = ?, building_no = ?, street = ?, city = ?, state = ?, pincode = ? WHERE id = ?"
            SEARCHQUERY = "SELECT company_name, representative, gst_number, mobile_number, building_no, street, city, state, pincode, id FROM customers WHERE id = ?"
            cur.execute(UPDATEQUERY, (self.companyName.get(), self.representative.get(), self.gstNumber.get(), self.mobileNumber.get(), self.buildingNo.get(), self.street.get(), self.city.get(),
                                      self.state.get(), self.pincode.get(), args[0][9]))
            cur.execute(SEARCHQUERY, (args[0][9],))

            rows = cur.fetchall()[0]
            con.commit()
            con.close()
            self.clearData()

            self.treeview.insert("", "end", values=rows)

            return messagebox.showinfo("SUCCESS", "DATAS UPDATED SUCCESSFULLY")

        selected = self.treeview.focus()
        if (not selected):
            return messagebox.showwarning("WARNING", "SELECT A COMPANY TO UPDATE")
        item_values = self.treeview.item(selected, "values")

        update(item_values)

    def deleteData(self):
        def delete(id):
            con = sqlite3.connect("datas/customerDB.db")
            cur = con.cursor()

            DELETE = "DELETE FROM customers WHERE id = ?"
            cur.execute(DELETE, (id,))
            con.commit()
            self.clearData()
            con.close()
            cur.close()
            return messagebox.showinfo("SUCCESS", "DATAS REMOVED SUCCESSFULLY")

        selected = self.treeview.focus()
        if (not selected):
            return messagebox.showwarning("WARNING", "SELECT A COMPANY TO DELETE")
        item_values = self.treeview.item(selected, "values")

        self.conn = sqlite3.connect("datas/customerDB.db")
        self.cur = self.conn.cursor()
        delete(self.conn, self.cur, item_values[9])
        self.conn.close()
        self.cur.close()

    def searchData(self):
        def search(column, data):
            con = sqlite3.connect("datas/customerDB.db")
            cur = con.cursor()

            SEARCHQUERY = f"SELECT company_name, representative, gst_number, mobile_number, building_no, street, city, state, pincode, id FROM customers WHERE {column} LIKE '%{data}%'"
            cur.execute(SEARCHQUERY)
            con.commit()

            row = cur.fetchall()
            cur.close()
            con.close()
            return row

        if (len(self.companyName.get()) > 1):
            output = search("company_name", self.companyName.get())
        elif (len(self.representative.get()) > 1):
            output = search("representative", self.representative.get())
        elif (len(self.gstNumber.get()) > 0):
            output = search("gst_number", self.gstNumber.get())
        elif (len(self.mobileNumber.get()) > 8):
            output = search("mobile_number", self.mobileNumber.get())
        elif (len(self.buildingNo.get()) > 0):
            output = search("building_no", self.buildingno.get())
        elif (len(self.street.get()) > 0):
            output = search("street", self.street.get())
        elif (len(self.city.get()) > 0):
            output = search("city", self.city.get())
        elif (len(self.pincode.get()) > 0):
            output = search("pincode", self.pincode.get())
        else:
            output = search("state", self.state.get())

        if (output == []):
            return messagebox.showinfo("NO DATA", "NO DATA FOUND")

        self.treeview.delete(*self.treeview.get_children())

        for datas in output:
            self.treeview.insert("", END, values=datas[0: len(datas)])

    def destroy(self):
        self.windowControl["modify_company"] = False
        self.companyTL.destroy()
