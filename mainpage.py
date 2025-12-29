import os
import sqlite3
import datetime
import subprocess
import configparser
from PIL import Image
from tkinter import messagebox
from pdfviewer import PdfViewer
from tkcalendar import DateEntry
from createbill import createBill
from tkinter import messagebox, Menu
from tkinter.ttk import Treeview, Style
from CTkMessagebox import CTkMessagebox
from utils.runtime_paths import resource_path
from customtkinter import CTkButton, CTkLabel, CTkFrame, CTkScrollbar, CTkImage

class MainPage:
    def __init__(self, master, fontstyle):
        self.master = master
        self.font = fontstyle

        # setting up required frames
        self.titleFrame = CTkFrame(
            self.master, fg_color="transparent", border_color="grey", border_width=2, height=50)
        self.titleFrame.pack(fill="x", padx=3, pady=3)
        self.tvFrame = CTkFrame(self.master)
        self.tvFrame.pack(fill="both", expand=True)

        self.titleframe()
        self.treeviewframe()
        self.filldata()

    def getDate(self):
        date = self.date.get_date().strftime("%d-%m-%Y")
        self.filldata(date)

    def filldata(self, date=datetime.datetime.now().strftime("%d-%m-%Y")):
        connection = sqlite3.connect(resource_path("datas", "taxinvoice.db"))
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM ti_info WHERE invoice_date = ?", (date,))
        rows = cursor.fetchall()

        for row in self.treeview.get_children():
            self.treeview.delete(row)

        for row in rows:
            self.treeview.insert("", "end", values=(
                row[1], row[0], row[3], row[4], row[6]))

        cursor.close()
        connection.close()

    def callcreatebill(self):
        createBill(self.master, self.font)
        self.filldata()

    def titleframe(self):
        CTkLabel(self.titleFrame, text="TAX INVOICE", font=(
            self.font, 20, "bold")).place(relx=0.45, rely=0.10)

        self.date = DateEntry(self.titleFrame,
                              width=11,
                              height=15,
                              background="darkblue",
                              font=(self.font, 10, "bold"),
                              foreground="white",
                              borderwidth=2,
                              borderradius=100,
                              justify="center",
                              date_pattern='dd-mm-yyyy'
                              )

        self.date.place(relx=0.80, rely=0.18)
        CTkButton(self.titleFrame, text="Get data", font=(self.font, 15),
                  width=15, command=lambda: self.getDate()).place(relx=0.90, rely=0.15)

        """ addImage = PhotoImage(file="images/add_icon.png") """
        image = CTkImage(light_image=Image.open(
            "images/add_icon.png"), size=(20, 20))  # adjust size as needed
        CTkButton(self.titleFrame, text="CreateTI", image=image, compound="left", font=(
            self.font, 15), width=15, command=lambda: self.callcreatebill()).place(relx=0.02, rely=0.15)

    def callPdfViewer(self, pdfpath):
        PdfViewer(self.master, pdfpath)

    def on_treeview_double_click(self, event):
        def set_printer_color_mode(is_color=True):
            if is_color:
                cmd = (
                    'Set-PrintConfiguration '
                    '-PrinterName (Get-Printer | Where-Object {$_.Default -eq $true}).Name '
                    '-Color $true -Grayscale $false'
                )
            else:
                cmd = (
                    'Set-PrintConfiguration '
                    '-PrinterName (Get-Printer | Where-Object {$_.Default -eq $true}).Name '
                    '-Color $false -Grayscale $true'
                )

            subprocess.run(
                ["powershell", "-Command", cmd],
                shell=True,
                check=False
            )

        def print_pdf(file_path):
            colorConfig = configparser.ConfigParser()
            colorConfig.read("config/configuration.ini")
            currentColor = colorConfig.get(
                "SectionFive", "printercolor", fallback="Black & White"
            ).lower()

            # Apply printer settings
            if currentColor == "color":
                set_printer_color_mode(True)
            else:
                set_printer_color_mode(False)

            sumatra_path = os.path.join(os.getcwd(), "Sumatra.exe")

            if os.path.exists(sumatra_path):
                subprocess.Popen(
                    [sumatra_path, "-print-to-default", file_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )

        msg = CTkMessagebox(title="PRINT OR SHARE", message="Do you want to print or share?",
                            option_1="Preview pdf", option_2="Print", option_3="Open")
        
        if msg.get() == "Cancel":
            return

        self.selectedRow = self.treeview.item(self.treeview.focus(), "values")

        connection = sqlite3.connect("datas/taxinvoice.db")
        cursor = connection.cursor()
        cursor.execute(
            "SELECT invoiceno, invoice_date FROM ti_info WHERE invoiceno = ?", (self.selectedRow[1],))
        companyDetails = cursor.fetchall()[0]

        connection.close()

        invoiceno = companyDetails[0]
        date = companyDetails[1]

        date_obj = datetime.datetime.strptime(date, "%d-%m-%Y")
        invoiceMonth = date_obj.strftime("%B")

        if date_obj.day < 10:
            invoiceDate = "0" + str(date_obj.day)
        else:
            invoiceDate = str(date_obj.day)

        invoiceYear = date_obj.year

        pdf_path = f"bills\\invoice\\{invoiceYear}\\{invoiceMonth}-{invoiceYear}\\{invoiceDate}-{invoiceMonth}\\tiKEI_{invoiceMonth}_{invoiceno}.pdf"

        if msg.get() == "Print":
            messagebox.showinfo("INFO", "PRINTING PROGRESS BEGINS")
            print_pdf(os.path.abspath(pdf_path))
        if msg.get() == "Preview pdf":
            self.callPdfViewer(pdfpath=pdf_path)
        if msg.get() == "Open":
            if os.path.exists(pdf_path):
                subprocess.Popen(
                    f'explorer /select,"{os.path.abspath(pdf_path)}"'
                )
            else:
                messagebox.showerror(
                    "FILE NOT FOUND",
                    f"PDF not found:\n{pdf_path}"
                )


    def treeviewframe(self):
        tvStyle = Style()
        tvStyle.theme_use('clam')
        tvStyle.configure('Treeview', background='silver',
                          foreground='black', rowheight=21, fieldbackground='silver')
        tvStyle.configure('mystyle.Treeview', font=(self.font, 10))
        tvStyle.configure('mystyle.Treeview.Heading', font=(
            self.font, 10, 'bold'), justify='center')

        scrollbar = CTkScrollbar(self.tvFrame, orientation="vertical")
        scrollbar.pack(side="right", fill="y")

        self.treeview = Treeview(self.tvFrame, style="mystyle.Treeview", columns=[
                                 1, 2, 3, 4, 5], height=23, yscrollcommand=scrollbar.set)
        self.treeview["show"] = "headings"

        self.treeview.heading(1, text="CUSTOMER")
        self.treeview.column(1, anchor="center")
        self.treeview.heading(2, text="INVOICE NO")
        self.treeview.column(2, anchor="center")
        self.treeview.heading(3, text="TIME")
        self.treeview.column(3, anchor="center")
        self.treeview.heading(4, text="QUANTITY")
        self.treeview.column(4, anchor="center")
        self.treeview.heading(5, text="MOBILE")
        self.treeview.column(5, anchor="center")

        self.treeview.pack(fill="both", expand=True)
        self.treeview.bind("<Double-1>", self.on_treeview_double_click)

        self.tree_menu = Menu(self.treeview, tearoff=0)
        self.tree_menu.add_command(
            label="Payment status", command=self.get_payment_status)
        self.treeview.bind("<Button-3>", self.show_menu)

    def show_menu(self, event):
        selected_item = self.treeview.identify_row(event.y)
        if selected_item:
            self.treeview.selection_set(selected_item)
            self.tree_menu.post(event.x_root, event.y_root)

    def get_payment_status(self, event=None):
        item_id = self.treeview.selection()[0]
        values = self.treeview.item(item_id, "values")

        self.conn = sqlite3.connect("datas\\taxinvoice.db")
        self.cursor = self.conn.cursor()

        QUERY = """SELECT isPaid from ti_paid WHERE invoiceno = ?"""
        self.cursor.execute(QUERY, (str(values[1]),))

        is_paid = int(self.cursor.fetchone()[0])

        if is_paid == 1:
            msg = CTkMessagebox(title="PAID", title_color="green", icon="check",
                                message="This invoice is already paid.", option_1="Set Unpaid", fade_in_duration=0)
            if msg.get() == "Set Unpaid":
                QUERY = """UPDATE ti_paid SET isPaid = 0 WHERE invoiceno = ?"""
                self.cursor.execute(QUERY, (values[1],))
                self.conn.commit()
                messagebox.showinfo(
                    "SUCCESS", "Invoice set to unpaid successfully.")

        else:
            msg = CTkMessagebox(title="UNPAID", title_color="red", icon="cancel",
                                message="This invoice is not paid.", option_1="Set Paid", fade_in_duration=0)
            if msg.get() == "Set Paid":
                QUERY = """UPDATE ti_paid SET isPaid = 1 WHERE invoiceno = ?"""
                self.cursor.execute(QUERY, (values[1],))
                self.conn.commit()
                messagebox.showinfo("SUCCESS", "Invoice paid successfully.")

    def destroy(self):
        self.mailWindow.destroy()
