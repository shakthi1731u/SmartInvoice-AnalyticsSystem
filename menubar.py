import os
import products
import threading
import configparser
from unpaid import Unpaid
from settings import Settings
from tkinter import messagebox
from tkinter import Menu, RIDGE
from lastdaySummary import summary
from billnumbers import billNumbers
from utils.backup_utils import run_backup
from CTkMessagebox import CTkMessagebox
from report import Report, DetailedReport
from company import addCustomer, modCustomer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config", "configuration.ini")


class MenuBar:
    def __init__(self, root, currentFont, currentTheme, destroy, windowControl, accesslevel):
        self.theme = currentTheme
        self.font = currentFont
        self.destroy = destroy
        self.windowControl = windowControl
        self.accesslevel = accesslevel
        self.master = root
        self.menubar = Menu(root)
        self.backup_running = False
        self.master.config(menu=self.menubar)

        filemenu = Menu(self.menubar, tearoff=0,
                        activebackground="orange", font=(self.font, 10))
        self.menubar.add_cascade(label="File", menu=filemenu)

        fonts = ["Roboto", "Times New Roman", "Arial", "Calibri"]
        for i in range(len(fonts)):
            if (fonts[i] == self.font):
                fonts[i] = f"✓ {fonts[i]}"
            else:
                fonts[i] = f"     {fonts[i]}"

        # creating sub menu for font menu
        fontMenu = Menu(filemenu, tearoff=0, relief=RIDGE,
                        activebackground="orange", font=(self.font, 10))
        filemenu.add_cascade(label="Fonts", menu=fontMenu)
        fontMenu.add_command(label=fonts[0], font=(
            "Roboto", 10), command=lambda: self.change_font("Roboto"))
        fontMenu.add_command(label=fonts[1], font=(
            "Times New Roman", 10), command=lambda: self.change_font("Times New Roman"))
        fontMenu.add_command(label=fonts[2], font=(
            "Arial", 10), command=lambda: self.change_font("Arial"))
        fontMenu.add_command(label=fonts[3], font=(
            "Calibri", 10), command=lambda: self.change_font("Calibri"))

        themes = ["light", "dark"]
        for i in range(len(themes)):
            if (themes[i] == self.theme):
                themes[i] = f"✓ {themes[i]}"
            else:
                themes[i] = f"     {themes[i]}"

        # creating sub menu for theme menu
        themeMenu = Menu(filemenu, tearoff=0, relief=RIDGE,
                         activebackground="orange", font=(self.font, 10))
        filemenu.add_cascade(label="Theme", menu=themeMenu)

        themeMenu.add_command(label=themes[0], command=lambda: self.change_appearance(
            choosen_theme="light"), font=(self.font, 10))
        themeMenu.add_command(label=themes[1], command=lambda: self.change_appearance(
            choosen_theme="dark"), font=(self.font, 10))
        filemenu.add_separator()

        filemenu.add_command(label="Backup", command=self.BackupThread)
        filemenu.add_command(label="Settings", command=lambda: self.callSettings(
            self.master, self.font), font=(self.font, 10))
        filemenu.add_separator()
        filemenu.add_command(label="Bill Numbers", command=lambda: self.billnumbers(
            self.master, self.font), font=(self.font, 10))
        filemenu.add_separator()
        filemenu.add_command(label="Exit                                  Alt+F4",
                             command=self.destroy, font=(self.font, 10))

        # company menu
        company = Menu(self.menubar, tearoff=0,
                       activebackground="orange", font=(self.font, 10))
        self.menubar.add_cascade(label="Manage", menu=company)
        company.add_command(label="Add Entity",
                            command=lambda: self.calladdCompany(), font=(self.font, 10))
        company.add_command(label="Add Products",
                            command=lambda: self.calladdProducts(), font=(self.font, 10))
        company.add_separator()
        company.add_command(label="Modify Entity",
                            command=lambda: self.callmodCompany(), font=(self.font, 10))
        company.add_command(label="Modify Products",
                            command=lambda: self.callmodProducts(), font=(self.font, 10))
        company.add_separator()
        company.add_command(label="Show unpaid", command=self.callUnpaid)

        # report menu
        report = Menu(self.menubar, tearoff=0,
                      activebackground="orange", font=(self.font, 10))
        self.menubar.add_cascade(label="Report", menu=report)
        report.add_command(
            label="Report", command=self.callReport, font=(self.font, 10))
        report.add_command(label="Detailed Report",
                           command=self.callDetailedReport, font=(self.font, 10))
        report.add_separator()
        report.add_command(label="Last day Summary",
                           command=self.callLastDayReport, font=(self.font, 10))
        
        # help menu
        help = Menu(self.menubar, tearoff=0,
                    activebackground="orange", font=(self.font, 10))
        self.menubar.add_cascade(label="Help", menu=help)
        help.add_command(label="About", command=self.callAbout,
                         font=(self.font, 10))

    def calladdProducts(self):
        if self.accesslevel != "ADMIN":
            return messagebox.showerror("NO Access", "Access Denied")
        # Using index 5 for Add Product
        if not self.windowControl["add_product"]:
            self.windowControl["add_product"] = True
            products.AddProduct(self.master, self.windowControl, self.font)

    def callmodProducts(self):
        if self.accesslevel != "ADMIN":
            return messagebox.showerror("NO Access", "Access Denied")
        # Using index 5 for Add Product
        if not self.windowControl["modify_product"]:
            self.windowControl["modify_product"] = True
            products.ModifyProduct(self.master, self.windowControl, self.font)

    def callUnpaid(self):
        Unpaid(self.master, self.font, self.accesslevel)

    def callLastDayReport(self):
        try:
            obj = summary(self.master, self.font)
            obj.getDatafortheDay()
        except Exception as e:
            return messagebox.showerror("Error", str(e))


        if obj.totlalNumberofInvoices == 0:
            return messagebox.showinfo("INFO", "NO SALES PRESENT YESTERDAY")

        obj.getOtherData()
        obj.segregate()
        obj.presentingPreviousDayData()

    def callAbout(self):
        CTkMessagebox(title="Info", message="This is a final year project 2022-2025.\n\nFor more information refer this link 'https://github.com/shakthi1731u/Smart-Invoice-and-analytics-system'", options="OK", fade_in_duration=0.5)

    def callBackup(self):
        success = run_backup(force=True)

        if success:
            messagebox.showinfo("Backup", "Backup completed successfully.")
        else:
            messagebox.showerror("Backup", "Backup failed. Check internet.")

    def BackupThread(self):
        if self.accesslevel != "ADMIN":
            return messagebox.showerror("NO Access", "Access Denied")

        if self.backup_running:
            return messagebox.showinfo("Backup", "Backup already running.")

        self.backup_running = True

        def task():
            try:
                self.callBackup()
            finally:
                self.backup_running = False

        threading.Thread(target=task, daemon=True).start()

    def callSettings(self, master, font):
        if self.accesslevel != "ADMIN":
            return messagebox.showerror("NO Access", "Access Denied")
        if not self.windowControl["settings"]:
            self.windowControl["settings"] = True
            Settings(master, self.windowControl, font)

    def callDetailedReport(self):
        if self.accesslevel != "ADMIN":
            return messagebox.showerror("NO Access", "Access Denied")
        if not self.windowControl["detailed_report"]:
            self.windowControl["detailed_report"] = True
            DetailedReport(self.master, self.windowControl, self.font)

    def billnumbers(self, master, font):
        if self.accesslevel != "ADMIN":
            return messagebox.showerror("NO Access", "Access Denied")
        if not self.windowControl["bill_number"]:
            self.windowControl["bill_number"] = True
            billNumbers(master, self.windowControl, font)

    def callReport(self):
        if self.accesslevel != "ADMIN":
            return messagebox.showerror("NO Access", "Access Denied")
        if not self.windowControl["report"]:
            self.windowControl["report"] = True
            Report(self.master, self.windowControl, self.font)

    def calladdCompany(self):
        if self.accesslevel != "ADMIN":
            return messagebox.showerror("NO Access", "Access Denied")
        if not self.windowControl["add_company"]:
            self.windowControl["add_company"] = True
            addCustomer(self.master,  self.windowControl, self.font)

    def callmodCompany(self):
        if self.accesslevel != "ADMIN":
            return messagebox.showerror("NO Access", "Access Denied")
        if not self.windowControl["modify_company"]:
            self.windowControl["modify_company"] = True
            modCustomer(self.master, self.windowControl, self.font)

    def change_font(self, updated_font):
        if self.font == updated_font:
            return
        else:
            config = configparser.ConfigParser()
            config.read(CONFIG_FILE)
            config.set("SectionTwo", "font", updated_font)

            with open(CONFIG_FILE, "w") as configfile:
                config.write(configfile)

        return messagebox.showinfo("SUCCESS", "RESTART THE APPLICATION FOR CHANGES TO TAKE EFFECT")

    def change_appearance(self, choosen_theme):
        if self.theme == choosen_theme:
            return
        else:
            config = configparser.ConfigParser()
            config.read(CONFIG_FILE)
            config.set("SectionOne", "theme", choosen_theme)

            with open(CONFIG_FILE, "w") as configfile:
                config.write(configfile)

        return messagebox.showinfo("SUCCESS", "RESTART THE APPLICATION FOR CHANGES TO TAKE EFFECT")
