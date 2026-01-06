import os
import sqlite3
import threading
import configparser
from tkinter import *
from login import Login
from tkinter.ttk import *
from customtkinter import *
from menubar import MenuBar
from dchallan import dChallan
from mainpage import MainPage
from tkinter import messagebox
from lastdaySummary import summary
from splashscreen import SplashScreen
from utils.backup_utils import run_backup

APP_VERSION = 1.0

def table_creation():
    def create_table_for_dc():
        QUERY1 = """ CREATE TABLE IF NOT EXISTS dc_info(
                    dc_id VARCHAR(15),
                    customer_name VARCHAR(100),
                    dc_date DATE,
                    time TIME,
                    quantity INT,
                    gstNumber VARCHAR(15),
                    mobile VARCHAR(15),
                    customer_dc_no, 
                    Ddate DATE, 
                    EwayBillNo VARCHAR(20),
                    Vehicle VARCHAR(20),
                    shippingCompanyName VARCHAR(25),
                    shippingDoorNo VARCHAR(7),
                    shippingStreet VARCHAR(15),
                    shippingCity VARCHAR(20),
                    shippingState VARCHAR(25),
                    shippingPincode VARCHAR(10),
                    buyingCompanyName VARCHAR(25),
                    buyingDoorNo VARCHAR(7),
                    buyingStreet VARCHAR(15),
                    buyingCity VARCHAR(20),
                    buyingState VARCHAR(25),
                    buyingPincode VARCHAR(10)
        )
        """
        QUERY2 = """ CREATE TABLE IF NOT EXISTS dc_data(
                    dc_id VARCHAR(15),
                    item_name VARCHAR(100),
                    quantity VARCHAR(8),
                    Hsn VARCHAR(10), 
                    remark VARCHAR(50)
                )
                """
        connection = sqlite3.connect("datas/deliverychallan.db")
        cursor = connection.cursor()
        cursor.execute(QUERY1)
        cursor.execute(QUERY2)
        connection.commit()
        cursor.close()
        connection.close()

    def create_table_for_ti():
        QUERY1 = """ CREATE TABLE IF NOT EXISTS ti_info(
                    invoiceno VARCHAR(15),
                    customer_name VARCHAR(100),
                    invoice_date DATE,
                    time TIME,
                    quantity INT,
                    gstNumber VARCHAR(15),
                    mobile VARCHAR(15),
                    customer_dc_no, 
                    Ddate DATE, 
                    pono VARCHAR(20),
                    EwayBillNo VARCHAR(20),
                    Vehicle VARCHAR(20),
                    shippingCompanyName VARCHAR(25),
                    shippingDoorNo VARCHAR(7),
                    shippingStreet VARCHAR(15),
                    shippingCity VARCHAR(20),
                    shippingState VARCHAR(25),
                    shippingPincode VARCHAR(10),
                    buyingCompanyName VARCHAR(25),
                    buyingDoorNo VARCHAR(7),
                    buyingStreet VARCHAR(15),
                    buyingCity VARCHAR(20),
                    buyingState VARCHAR(25),
                    buyingPincode VARCHAR(10)
        )
        """
        QUERY2 = """ CREATE TABLE IF NOT EXISTS ti_data(
                    invoiceno VARCHAR(15),
                    item_name VARCHAR(100),
                    Hsn VARCHAR(10), 
                    quantity VARCHAR(8),
                    rate VARCHAR(8),
                    gst VARCHAR(8),
                    amount VARCHAR(10)
                )
                """

        QUERY3 = """ CREATE TABLE IF NOT EXISTS ti_paid(
                    invoiceno VARCHAR(15),
                    customer VARCHAR(100),
                    amount VARCHAR(10),
                    date DATE,
                    isPaid TINYINT
                )
                """

        connection = sqlite3.connect("datas/taxinvoice.db")
        cursor = connection.cursor()
        cursor.execute(QUERY1)
        cursor.execute(QUERY2)
        cursor.execute(QUERY3)
        connection.commit()
        cursor.close()
        connection.close()

    def init_product_db():
        conn = sqlite3.connect("datas/products.db")
        cursor = conn.cursor()
        # Updated schema: added 'quantity' column
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT NOT NULL,
                hsn_code TEXT,
                rate REAL,
                quantity INTEGER, 
                gst_rate TEXT
            )
        """)

        conn.commit()
        conn.close()

    create_table_for_dc()
    create_table_for_ti()
    init_product_db()

def runapp(theme, fontstyle, windowControl):
    root = CTk()
    root.withdraw()

    """ login = Login(root)
    root.wait_window(login.window)

    if not login.success:
        root.destroy()
        return """

    app = MyApp(root, theme, fontstyle, windowControl)
    root.mainloop()

def callMisc():
    try:
        table_creation()
        run_backup(force=False)
    except Exception as e:
        print("Background task error:", e)

class MyApp:
    def __init__(self, root, theme, fontstyle, windowControl):
        self.theme = theme
        self.font = fontstyle
        self.windowControl = windowControl

        config = configparser.ConfigParser()
        config.read("config/configuration.ini")
        self.accesslevel = config.get("SectionThree", "Accesslevel")

        set_appearance_mode(self.theme)

        """Creates folder structure for invoices and delivery challans"""
        self.foldercreation()

        self.root = root
        self.root.withdraw()

        SplashScreen(
            self.root,
            self.font,
            on_close=self.start_app
        )

        try:
            self.root.iconbitmap("images/icons/icon_30x24.ico")
        except FileNotFoundError:
            print("Icon not found")

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.root.geometry(
            "{}x{}+{}+{}".format(screen_width, screen_height, -10, -2))
        self.root.title("Sales & Report Management System")
        self.root.wm_protocol("WM_DELETE_WINDOW", self.destroy)
        self.root.resizable(False, True)

        threading.Thread(target=callMisc, daemon=True).start() 

    def start_app(self):
        self.root.deiconify()

        self.root.option_add("*Titlebar.font", (self.font, 10)) 
        self.root.option_add("*TCombobox*Listbox.font", (self.font, 10))
        self.root.option_add("*Entry.font", (self.font, 10))
        self.root.option_add("*Menu.font", (self.font, 10))

        self.setMenubar()

        self.tabview = CTkTabview(self.root, width=1500, height=1000)
        self.tabview.pack(pady=3, padx=10)

        self.tabview.add("Tax Invoice")
        self.tabview.add("Delivery Challan")
        self.tabview.set("Tax Invoice")

        self.mainPage()
        self.dcPage()

        self.callpreviousdaySummaary()

    def callpreviousdaySummaary(self):
        try:
            obj = summary(self.root, self.font)
            obj.getDatafortheDay()

            if obj.totlalNumberofInvoices == 0:
                return

            obj.getOtherData()
            obj.segregate()
            obj.presentingPreviousDayData()

        except Exception as e:
            messagebox.showwarning(
                "SUMMARY WARNING",
                f"Previous day summary could not be loaded.\n\n{e}"
            )

    def setMenubar(self):
        MenuBar(self.root, self.font, self.theme, self.destroy, self.windowControl, self.accesslevel)

    def mainPage(self):
        MainPage(self.tabview.tab("Tax Invoice"), self.windowControl, self.font)

    def dcPage(self):
        dChallan(self.tabview.tab("Delivery Challan"), self.font)

    def destroy(self):
        self.root.quit()
        self.root.destroy()

    def foldercreation(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))

        marker_dir = os.path.join(base_dir, ".datas")
        marker_file = os.path.join(marker_dir, ".folders_initialized")

        if os.path.exists(marker_file):
            return

        os.makedirs(marker_dir, exist_ok=True)

        folders = [
            os.path.join(base_dir, "bills"),
            os.path.join(base_dir, "bills", "invoice"),
            os.path.join(base_dir, "bills", "deliverychallan"),
            os.path.join(base_dir, "datas"),
            os.path.join(base_dir, "config"),
            os.path.join(base_dir, "backup"),
            os.path.join(base_dir, "logs"),
        ]

        for folder in folders:
            os.makedirs(folder, exist_ok=True)

        with open(marker_file, "w") as f:
            f.write("initialized")

if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read("config/configuration.ini")

    theme = config.get("SectionOne", "theme")
    fontstyle = config.get("SectionTwo", "font")

    windowControl = {
        "add_company": False,
        "modify_company": False,
        "add_product": False,
        "modify_product": False,
        "report": False,
        "detailed_report": False,
        "bill_number": False,
        "settings": False,
        "unpaid_customer": False,
        "tax_invoice": False,
        "delivery_challan": False
    }

    # UI must be in main thread
    runapp(theme, fontstyle, windowControl)


