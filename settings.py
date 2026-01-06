import os
import shutil
import sqlite3
import hashlib
import configparser
from PIL import Image
from tkinter import filedialog
from tkinter import messagebox
from tkinter.ttk import Treeview, Style
from utils.runtime_paths import resource_path
from customtkinter import CTkEntry, CTkButton, CTkComboBox, StringVar
from customtkinter import CTkToplevel, CTkFrame, CTkLabel, CTkScrollbar

USER_DB = resource_path("datas", "user.db")
CONFIG_FILE = resource_path("config", "configuration.ini")

class User:
    def __init__(self, db):
        self.db = db

        with sqlite3.connect(self.db) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users
                (
                    Username TEXT,
                    Password TEXT,
                    AccessLevel TEXT
                )
            """)

            conn.commit()

    def getallusername(self):
        with sqlite3.connect(self.db) as conn:
            return conn.execute("SELECT Username FROM users").fetchall()
    
    def getall(self):
        with sqlite3.connect(self.db) as conn:
            return conn.execute("SELECT * FROM users").fetchall()

    def modifyuser(self, username, password, access):
        with sqlite3.connect(self.db) as conn:
            conn.execute(
                "UPDATE users SET Password=?, AccessLevel=? WHERE Username=?",
                (password, access, username)
            )

    def deleteuser(self, username):
        with sqlite3.connect(self.db) as conn:
            conn.execute(
                "DELETE FROM users WHERE Username=?",
                (username,)
            )

    def insertuser(self, username, password, access):
        with sqlite3.connect(self.db) as conn:
            conn.execute(
                "INSERT INTO users VALUES (?, ?, ?)",
                (username, password, access)
            )

class Settings:
    def __init__(self, mainWindow, windowControl, font="Roboto"):
            self.windowControl = windowControl

            self.Set_win = CTkToplevel(mainWindow)
            self.Set_win.wm_transient(mainWindow)
            self.Set_win.resizable(0, 0)
            self.Set_win.title("Settings")
            self.Set_win.geometry("800x600+225+70")
            self.font= font

            # self.sepatator = ttk.Separator(self.Set_win, orient="vertical")
            # self.sepatator.place(relx=0.30, rely=0.05, relwidth=0.2, relheight=0.9)

            self.left_frame = CTkFrame(self.Set_win, height=600)
            # self.left_frame.place(relx=0, rely=0.00, relwidth=0.3)
            self.left_frame.pack(side="left", fill="y", padx=0.5)

            self.right_frame = CTkFrame(self.Set_win, height=600)
            self.right_frame.pack(fill="both")

            self.scrollbar = CTkScrollbar(
                self.left_frame, orientation="horizontal")
            self.scrollbar.pack(side="bottom", fill="x")

            tvStyle = Style()
            tvStyle.theme_use('clam')
            tvStyle.configure('Treeview', background='silver',
                            foreground='black', rowheight=21, fieldbackground='silver')
            tvStyle.configure('mystyle.Treeview', font=(self.font, 10))
            tvStyle.configure('mystyle.Treeview.Heading', font=(self.font, 10, 'bold'), justify='center')

            self.treeview = Treeview(self.left_frame, height=600,  style="mystyle.Treeview")
            self.treeview.bind("<ButtonRelease-1>", self.return_for_window)
            self.treeview.pack(fill="both")

            # parent widget of hierarchical tree view
            self.treeview.insert("", "0", "item1", text="Settings", open=True)

            # first child widget of hierarchical tree view
            self.treeview.insert(
                "", "1", "item2", text="Authentication Manager", open=True)

            # second child widget of hierarchical tree view
            self.treeview.insert("", "2", "item3", text="Add User")
            self.treeview.insert("", "3", "item4", text="Modify User")

            self.treeview.insert(
                            "", "4", "item5", text="Printer Settings", open=True)
                        
            self.treeview.insert("", "5", "item6", text="Color Management")

            self.treeview.insert("", "6", "item7", text="Others", open=True)
            self.treeview.insert("", "7", "item8", text="Company and Bank")

            # placing each child items in parent widget
            self.treeview.move("item2", "item1", "end")
            self.treeview.move("item3", "item2", "end")
            self.treeview.move("item4", "item2", "end")
            self.treeview.move("item5", "item1", "end")
            self.treeview.move("item6", "item5", "end")
            self.treeview.move("item7", "item1", "end")
            self.treeview.move("item8", "item7", "end")

            self.Set_win.protocol("WM_DELETE_WINDOW", self.close_window)

            self.add_user()

    def return_for_window(self, event=None):
        varCheck = self.treeview.focus()

        if varCheck == "item3":
            self.add_user()
        if varCheck == "item4":
            self.mod_user()
        if varCheck == "item6":
            self.printerColorManagementSettings()
        if varCheck == "item8":
            self.company_bank_settings()

    def add_user(self):
        def addUsertoDatabase():
            if self.varUserName.get() == "" or self.varPassWord.get() == "" or self.AuthenticationLevel.get() == "":
                return messagebox.showwarning("WARNING", "PLEASE FILL ALL THE FIELD")
            elif len(self.varUserName.get()) < 5 or len(self.varPassWord.get()) < 5:
                return messagebox.showwarning("WARNING", "SEEMS LIKE LENGHT OF THE USERNAME OR PASSWORD IS LESS THEN 5")
            else:
                objectInsert = User(USER_DB)

                usernamelist = objectInsert.getallusername()
                encodedUserName = hashlib.sha256(
                    self.varUserName.get().encode()).hexdigest()

                for username in usernamelist:
                    if username[0] == encodedUserName:
                        return messagebox.showwarning("WARNING", "USER ALREADY IN THE DATABASE")

                encodedUserName = hashlib.sha256(
                    self.varUserName.get().encode()).hexdigest()
                encodedPassWord = hashlib.sha256(
                    self.varPassWord.get().encode()).hexdigest()

                objectInsert.insertuser(
                    encodedUserName, encodedPassWord, self.AuthenticationLevel.get())

                # setting the field empty
                self.varUserName.set("")
                self.varPassWord.set("")
                self.AuthenticationLevel.set("")

                return messagebox.showinfo("SUCCESS", "USER INSERTED SUCCESSFULLY")

        self.destroy_widgets()

        CTkLabel(self.right_frame, text="Add User", font=(self.font, 16, "bold")).place(
            relx=0.4, rely=0.04, anchor="w")

        CTkLabel(self.right_frame, text="User Name",  font=(self.font, 15), justify="center").place(
            rely=0.15, relx=0.1, anchor="w")
        self.varUserName = StringVar()
        CTkEntry(self.right_frame, textvariable=self.varUserName, font=(self.font, 15)).place(
            rely=0.15, relx=0.3, anchor="w")

        CTkLabel(self.right_frame, text="Password",  justify="center", font=(self.font, 15)).place(
            rely=0.25, relx=0.1, anchor="w")
        self.varPassWord = StringVar()
        CTkEntry(self.right_frame, textvariable=self.varPassWord, show="*", font=(self.font, 15)).place(
            rely=0.25, relx=0.3, anchor="w")

        CTkLabel(self.right_frame, text="Access Level",  justify="center", font=(self.font, 15)).place(
            rely=0.35, relx=0.1, anchor="w")
        self.AuthenticationLevel = StringVar()
        VALUE = ["ADMIN", "WORKER"]
        CTkComboBox(self.right_frame, variable=self.AuthenticationLevel, width=140,
                    state="readonly", values=VALUE, font=(self.font, 15)).place(rely=0.35, relx=0.3, anchor="w")

        CTkButton(self.right_frame, text="Add User", command=addUsertoDatabase, font=(self.font, 15)).place(
            relx=0.50, rely=0.45, anchor="w")

    def mod_user(self):
        def modifyUsertoDatabase(option):
            if self.varUserName.get() == "" or self.varPassWord.get() == "" or self.AuthenticationLevel.get() == "":
                return messagebox.showwarning("WARNING", "PLEASE FILL ALL THE FIELD")
            elif len(self.varUserName.get()) < 5 or len(self.varPassWord.get()) < 5:
                return messagebox.showwarning("WARNING", "SEEMS LIKE LENGHT OF THE USERNAME OR PASSWORD IS LESS THEN 5")
            elif self.varUserName.get() == "admin":
                return messagebox.showwarning("WARNING", "USER ALREADY IN THE DATABASE")
            else:
                objectInsert = User(USER_DB)

                usernamelist = objectInsert.getall()
                encodedUserName = hashlib.sha256(
                    self.varUserName.get().encode()).hexdigest()
                encodedPassWord = hashlib.sha256(
                    self.varPassWord.get().encode()).hexdigest()

                is_available = False
                index = 0
                for idx, username in enumerate(usernamelist):
                    if username[0] == encodedUserName:
                        is_available = True
                        index = idx

                if is_available == False:
                    return messagebox.showwarning("WARNING", "USER NOT IN THE DATABASE")

                if option == "mod":
                    objectInsert.modifyuser(
                        encodedUserName, encodedPassWord, self.AuthenticationLevel.get())

                    # clear fields
                    self.varUserName.set("")
                    self.varPassWord.set("")
                    self.AuthenticationLevel.set("")

                    messagebox.showinfo("SUCCESS", "USER UPDATED SUCCESSFULLY")
                    return

                elif option == "del":
                    objectInsert.deleteuser(encodedUserName)

                    # clear fields
                    self.varUserName.set("")
                    self.varPassWord.set("")
                    self.AuthenticationLevel.set("")

                    messagebox.showinfo("SUCCESS", "USER DELETED SUCCESSFULLY")
                    return


        self.destroy_widgets()

        CTkLabel(self.right_frame, text="Modify User", font=(self.font, 16, "bold"), ).place(
            relx=0.4, rely=0.04, anchor="w")

        CTkLabel(self.right_frame, text="User Name",  justify="center", font=(self.font, 15)).place(
            rely=0.15, relx=0.1, anchor="w")
        self.varUserName = StringVar()
        CTkEntry(self.right_frame, textvariable=self.varUserName ,font=(self.font, 15)).place(
            rely=0.15, relx=0.3, anchor="w")

        CTkLabel(self.right_frame, text="Password",  justify="center" ,font=(self.font, 15)).place(
            rely=0.25, relx=0.1, anchor="w")
        self.varPassWord = StringVar()
        CTkEntry(self.right_frame, textvariable=self.varPassWord, show="*", font=(self.font, 15)).place(
            rely=0.25, relx=0.3, anchor="w")

        CTkLabel(self.right_frame, text="Access Level",  justify="center", font=(self.font, 15)).place(
            rely=0.35, relx=0.1, anchor="w")
        self.AuthenticationLevel = StringVar()
        VALUE = ["ADMIN", "WORKER"]
        CTkComboBox(self.right_frame, variable=self.AuthenticationLevel, width=140,
                    state="readonly", values=VALUE, font=(self.font, 15)).place(rely=0.35, relx=0.3, anchor="w")

        CTkButton(self.right_frame, text="Update User", font=(self.font, 15), command=lambda: modifyUsertoDatabase(
            "mod")).place(relx=0.50, rely=0.45, anchor="w")
        CTkButton(self.right_frame, text="Delete User", font=(self.font, 15), command=lambda: modifyUsertoDatabase(
            "del")).place(relx=0.25, rely=0.45, anchor="w")
        
    def printerColorManagementSettings(self):
        def save_settings(currentcolorsettings):
            colorConfig  = configparser.ConfigParser()
            colorConfig.read(CONFIG_FILE)
            colorConfig.set("SectionFive", "printercolor", currentcolorsettings)

            with open(CONFIG_FILE, "w") as configfile:
                colorConfig.write(configfile)
            
            return messagebox.showwarning("SUCCESS", "SETTINGS APPLIED SUCCESSFULLY")


        config = configparser.ConfigParser()

        if not os.path.exists(CONFIG_FILE):
            messagebox.showerror("Error", "Configuration file not found.")
            return

        config.read(CONFIG_FILE)

        
        # It is good practice to provide a fallback value in case the key is missing
        printerColor = config.get("SectionFive", "printercolor", fallback="Black & White")

        self.destroy_widgets()

        CTkLabel(self.right_frame, text="Color Management", font=(self.font, 16, "bold")).place(
            relx=0.4, rely=0.04, anchor="w")

        CTkLabel(self.right_frame, text="Color Settings", font=(self.font, 15), justify="center").place(
            rely=0.15, relx=0.1, anchor="w")
        
        VALUE = ["Black & White", "Color"]

        # --- CORRECTION START ---
        # 1. Create the widget and assign it to the variable
        printercolorCombobox = CTkComboBox(self.right_frame, values=VALUE)
        
        # 2. Place it on the screen separately
        printercolorCombobox.place(rely=0.15, relx=0.3, anchor="w")
        
        # 3. Now you can safely call .set()
        printercolorCombobox.set(printerColor)
        # --- CORRECTION END ---
        
        # Note: You likely want to add a command to this button to actually save the changes
        CTkButton(self.right_frame, text="Save", font=(self.font, 15), command=lambda: save_settings(printercolorCombobox.get())).place(
            rely=0.25, relx=0.5, anchor="w")
        
    # ---------------- COMPANY & BANK ----------------
    def company_bank_settings(self):
        self.destroy_widgets()

        config = configparser.ConfigParser()
        config.read(CONFIG_FILE)

        for section in ("CompanyDetails", "BankDetails"):
            if not config.has_section(section):
                config.add_section(section)

        fields = {
            "Company Name": ("CompanyDetails", "company_name"),
            "Address": ("CompanyDetails", "address"),
            "Phone": ("CompanyDetails", "phone"),
            "Email": ("CompanyDetails", "email"),
            "GSTIN": ("CompanyDetails", "gstin"),
            "Bank Name": ("BankDetails", "bank_name"),
            "Branch": ("BankDetails", "branch"),
            "Account No": ("BankDetails", "account_no"),
            "IFSC": ("BankDetails", "ifsc"),
            "UPI Name": ("BankDetails", "upi_name"),
            "UPI ID": ("BankDetails", "upi_id"),
            "Invoice Logo (PNG/JPG)": ("CompanyDetails", "logo_image"),
            "Application Icon (.ico)": ("CompanyDetails", "app_icon")
        }

        vars = {}
        y = 0.12

        CTkLabel(self.right_frame, text="Company & Bank Details", font=("Roboto", 16, "bold")).place(relx=0.3, rely=0.04)

        for label, (sec, key) in fields.items():
            vars[key] = StringVar(value=config.get(sec, key, fallback=""))

            CTkLabel(self.right_frame, text=label).place(relx=0.05, rely=y)

            if key == "logo_image":
                row = CTkFrame(self.right_frame, fg_color="transparent")
                row.place(relx=0.35, rely=y, relwidth=0.55)

                CTkEntry(row, textvariable=vars[key], width=260).pack(side="left", padx=(0, 10))

                def browse_logo():
                    ...
                CTkButton(row, text="Browse", width=90, command=browse_logo).pack(side="left")

            elif key == "app_icon":
                entry = CTkEntry(
                    self.right_frame,
                    textvariable=vars[key],
                    width=350,
                    state="disabled"
                )
                entry.place(relx=0.35, rely=y)
                entry.configure(placeholder_text="Auto-generated from Invoice Logo")

            else:
                CTkEntry(
                    self.right_frame,
                    textvariable=vars[key],
                    width=350
                ).place(relx=0.35, rely=y)

            y += 0.055

        def save():
            for label, (sec, key) in fields.items():
                config.set(sec, key, vars[key].get())
            with open(CONFIG_FILE, "w") as f:
                config.write(f)
            messagebox.showinfo("Saved", "Company & Bank details updated")

        CTkButton(self.right_frame, text="Save Details", command=save).place(relx=0.45, rely=0.90)

    
    def convert_image_to_ico(self, image_path):
        """
        Converts PNG/JPG to Windows .ico format
        """
        ico_path = resource_path("images", "app_icon.ico")

        img = Image.open(image_path)

        # Convert to square
        size = min(img.size)
        img = img.crop((0, 0, size, size))

        img.save(
            ico_path,
            format="ICO",
            sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        )

    def destroy_widgets(self):
        for widgets in self.right_frame.winfo_children():
            widgets.destroy()

    def close_window(self):
        self.windowControl["settings"] = False
        self.Set_win.destroy()
