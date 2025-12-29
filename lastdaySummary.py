from datetime import datetime, timedelta
import sqlite3
from datetime import date
from customtkinter import CTkToplevel, CTkLabel
from utils.type_utils import to_int, to_float




class summary:
    def __init__(self, mainwindow, font="Roboto"):
        self.font = font
        self.mainwindow = mainwindow
        lastday = datetime.now() - timedelta(days=1)
        self.lastday_str = lastday.strftime('%d-%m-%Y')
        self.conn = sqlite3.connect("datas/taxinvoice.db")
        self.cursor = self.conn.cursor()
        self.ti_info = []
        self.ti_data = []
        self.invoicenumber = []
        self.totlalNumberofInvoices = 0
        self.totalwithoutgst = 0
        self.gstamount = 0
        self.totalSales = 0
        self.topitemsdict = {}
        self.topitem = ""
        self.today = date.today().strftime("%d-%m-%Y")

    def getDatafortheDay(self):
        QUERY1 = "SELECT invoiceno, customer_name, quantity, mobile FROM ti_info WHERE invoice_date = ?"
        self.cursor.execute(QUERY1, (self.lastday_str,))
        self.ti_info = self.cursor.fetchall()
        self.invoicenumber = [i[0] for i in self.ti_info]
        self.totlalNumberofInvoices = len(self.ti_info)
        
    def getOtherData(self):
        QUERY2 = "SELECT invoiceno, item_name, quantity, rate, amount FROM ti_data WHERE invoiceno = ?"

        self.getDatafortheDay()

        for i in self.invoicenumber:
            self.cursor.execute(QUERY2, (i,))
            self.ti_data.extend(self.cursor.fetchall())

    def segregate(self):
        # calculating total without gst
        for i in self.ti_data:
            self.totalwithoutgst += to_float(i[2]) * to_float(i[3])
            self.totalSales += to_float(i[4])

        # count top items
        for i in self.ti_data:
            qty = to_float(i[2])

            if i[1] in self.topitemsdict:
                self.topitemsdict[i[1]] += qty
            else:
                self.topitemsdict[i[1]] = qty

        high = 0
        for key, value in self.topitemsdict.items():
            if high == 0 or value > high:
                high = value
                self.topitem = key

        self.totalSales = round(to_float(self.totalSales), 2)
        self.totalwithoutgst = round(to_float(self.totalwithoutgst), 2)
        self.gstamount = round(to_float(self.totalSales - self.totalwithoutgst), 2)


    def presentingPreviousDayData(self):
        self.summaryWin = CTkToplevel(self.mainwindow)
        self.summaryWin.resizable(0, 0)
        self.summaryWin.wm_transient(self.mainwindow)
        self.summaryWin.title("Previous Day's Summary")
        self.summaryWin.geometry("400x250+500+200")

        title = f"Summary for {self.today} (Yesterday’s Stats)"
        CTkLabel(self.summaryWin, text=title, font=(
            "Arial", 16, "bold")).pack(pady=(15, 10))

        CTkLabel(self.summaryWin, text=f"🧾 Total Invoices: {self.totlalNumberofInvoices}", font=(
            self.font, 14)).pack(pady=5)
        CTkLabel(self.summaryWin, text=f"💸 Total GST Collected: ₹{self.gstamount}", font=(
            self.font, 14)).pack(pady=5)
        CTkLabel(self.summaryWin, text=f"🏆 Top Sale Amount: ₹{self.totalSales}", font=(
            self.font, 14)).pack(pady=5)
        CTkLabel(self.summaryWin,
                 text=f"📦 Top-Selling Item: {self.topitem}", font=(self.font, 14)).pack(pady=5)

        CTkLabel(self.summaryWin, text="✔️ Backup your data regularly!",
                 font=(self.font, 12, "italic")).pack(pady=(20, 10))
        
        self.close_db()

    def close_db(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
