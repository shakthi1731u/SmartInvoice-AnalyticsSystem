import os
import time
import sqlite3
import datetime
import datetime
import subprocess
import configparser
from createdc import createDC
from tkinter import PhotoImage
from tkinter import messagebox
from pdfviewer import PdfViewer
from tkcalendar import DateEntry
from tkinter.ttk import Style, Treeview
from CTkMessagebox import CTkMessagebox
from customtkinter import CTkFrame, CTkLabel, CTkButton, CTkScrollbar

class dChallan:
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

            # IMPORTANT: wait for Windows to apply settings
            time.sleep(2)

            sumatra_path = os.path.join(os.getcwd(), "Sumatra.exe")

            if os.path.exists(sumatra_path):
                subprocess.Popen(
                    [sumatra_path, "-print-to-default", file_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )

        msg = CTkMessagebox(title="PRINT OR SHARE", message="Do you want to print or share?",
                            option_1="Preview pdf", option_2="Print", option_3="Open")

        self.selectedRow = self.treeview.item(self.treeview.focus(), "values")

        connection = sqlite3.connect("datas/deliverychallan.db")
        cursor = connection.cursor()
        cursor.execute(
            "SELECT dc_id, dc_date FROM dc_info WHERE dc_id = ?", (self.selectedRow[1],))
        companyDetails = cursor.fetchall()[0]
        connection.close()

        dcno = companyDetails[0]
        date = companyDetails[1]

        date_obj = datetime.datetime.strptime(date, "%d-%m-%Y")
        dcMonth = date_obj.strftime("%B")

        if date_obj.day < 10:
            dcDate = "0" + str(date_obj.day)
        else:
            dcDate = str(date_obj.day)

        dcYear = date_obj.year

        pdf_path = f"bills\\deliverychallan\\{dcYear}\\{dcMonth}-{dcYear}\\{dcDate}-{dcMonth}\\dcKEI_{dcMonth}_{dcno}.pdf"

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

    
    def callcreateDC(self):
        createDC(self.master, self.font)
        self.master.after(100, self.filldata)

    def filldata(self, date=datetime.datetime.now().strftime("%d-%m-%Y")):
        connection = sqlite3.connect("datas/deliverychallan.db")
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM dc_info WHERE dc_date = ?", (date,))
        rows = cursor.fetchall()

        for row in self.treeview.get_children():
            self.treeview.delete(row)

        for row in rows:
            self.treeview.insert("", "end", values=(
                row[1], row[0], row[4], row[3], row[5]))

        cursor.close()
        connection.close()

    def titleframe(self):
        CTkLabel(self.titleFrame, text="DELIVERY CHALLAN", font=(
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

        addImage = PhotoImage(file="images/add_icon.png")
        CTkButton(self.titleFrame, text="CreateDC", image=addImage, compound="left", font=(
            self.font, 15), width=15, command=lambda: self.callcreateDC()).place(relx=0.02, rely=0.15)

    def useDefaultMobileSwitchfun(self):
        if self.useDefaultMobile.get() == "1":
            self.mobileNumber.set(self.selectedRow[4])
            self.mobileEntry.configure(state="readonly")
        else:
            self.mobileNumber.set("")
            self.mobileEntry.configure(state="normal")

    def treeviewframe(self):
        tvStyle = Style()
        tvStyle.theme_use('clam')
        tvStyle.configure('Treeview', background='silver',
                          foreground='black', rowheight=25, fieldbackground='silver')
        tvStyle.configure('mystyle.Treeview', font=(self.font, 10))
        tvStyle.configure('mystyle.Treeview.Heading', font=(
            self.font, 10, 'bold'), justify='center')

        scrollbar = CTkScrollbar(self.tvFrame, orientation="vertical")
        scrollbar.pack(side="right", fill="y")

        self.treeview = Treeview(self.tvFrame, style="mystyle.Treeview", columns=[
                                 1, 2, 3, 4, 5], height=23, yscrollcommand=scrollbar.set)
        self.treeview["show"] = "headings"

        self.treeview.heading(1, text="CUSTOMER NAME")
        self.treeview.column(1, anchor="center")
        self.treeview.heading(2, text="DC NO")
        self.treeview.column(2, anchor="center")
        self.treeview.heading(3, text="QUANTITY")
        self.treeview.column(3, anchor="center")
        self.treeview.heading(4, text="TIME")
        self.treeview.column(4, anchor="center")
        self.treeview.heading(5, text="MOBILE")
        self.treeview.column(5, anchor="center")

        self.treeview.pack(fill="both", expand=True)
        self.treeview.bind("<Double-1>", self.on_treeview_double_click)

    def destroy(self):
        self.mailWindow.destroy()
