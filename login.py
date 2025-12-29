import sys
import time
import hashlib
import sqlite3
import configparser
import customtkinter as ctk
from tkinter import messagebox
from PIL import Image
from customtkinter import CTkImage


class getAuth:
    def auth(self, user, pas):
        try:
            usrhash = hashlib.sha256(user.encode()).hexdigest()
            pashash = hashlib.sha256(pas.encode()).hexdigest()

            QUERY = "SELECT AccessLevel FROM users WHERE Username = ? AND Password = ?"

            with sqlite3.connect("datas/user.db") as con:
                cur = con.cursor()
                cur.execute(QUERY, (usrhash, pashash))
                row = cur.fetchone()

            if row is None:
                return None

            authlevel = row[0]

            config = configparser.ConfigParser()
            config.read("config/configuration.ini")
            config.set("SectionThree", "Accesslevel", str(authlevel))

            with open("config/configuration.ini", "w") as configfile:
                config.write(configfile)

            return authlevel

        except Exception as e:
            messagebox.showerror("LOGIN ERROR", str(e))
            return None

class Login(getAuth):
    def __init__(self, parent):
        self.success = False

        
        config = configparser.ConfigParser()
        config.read("config/configuration.ini")

        self.theme = config.get("SectionOne", "theme", fallback="Light")
        self.font = config.get("SectionTwo", "font", fallback="Poppins")

        ctk.set_appearance_mode(self.theme)

        self.window = ctk.CTkToplevel(parent)
        self.window.title("Login")
        self.window.geometry("420x480+500+150")
        self.window.resizable(False, False)
        self.window.attributes("-topmost", True)
        self.window.protocol("WM_DELETE_WINDOW", self.killAll)

        try:
            self.window.iconbitmap("images/icons/icon_30x24.ico")
        except Exception:
            pass

        container = ctk.CTkFrame(self.window, corner_radius=16)
        container.pack(expand=True, fill="both", padx=20, pady=20)

        try:
            logo_img = CTkImage(
                light_image=Image.open("images/login_icon.png"),
                dark_image=Image.open("images/login_icon.png"),
                size=(70, 70)
            )
            ctk.CTkLabel(container, image=logo_img, text="").pack(pady=(15, 10))
            self.logo_img = logo_img
        except Exception:
            pass

        ctk.CTkLabel(
            container,
            text="Welcome Back",
            font=(self.font, 22, "bold")
        ).pack(pady=(5, 5))

        ctk.CTkLabel(
            container,
            text="Please login to continue",
            font=(self.font, 13),
            text_color="gray"
        ).pack(pady=(0, 20))

    
        self.varUser = ctk.StringVar()
        self.varPass = ctk.StringVar()

        # ---------------- Username ----------------
        ctk.CTkEntry(
            container,
            placeholder_text="Username",
            textvariable=self.varUser,
            font=(self.font, 14),
            height=40,
            corner_radius=10
        ).pack(fill="x", padx=25, pady=(5, 10))

        # ---------------- Password ----------------
        ctk.CTkEntry(
            container,
            placeholder_text="Password",
            textvariable=self.varPass,
            font=(self.font, 14),
            height=40,
            show="●",
            corner_radius=10
        ).pack(fill="x", padx=25, pady=(0, 20))

        ctk.CTkButton(
            container,
            text="Login",
            height=42,
            corner_radius=10,
            font=(self.font, 14, "bold"),
            command=self.checkCredentials
        ).pack(fill="x", padx=25, pady=(0, 10))

        ctk.CTkButton(
            container,
            text="Clear",
            height=38,
            corner_radius=10,
            fg_color="transparent",
            border_width=1,
            text_color=("black", "white"),
            font=(self.font, 13),
            command=self.clear
        ).pack(fill="x", padx=25)

        self.window.bind("<Return>", self.checkCredentials)

    def destroyWindow(self, user):
        self.window.attributes("-topmost", False)

        messagebox.showinfo(
            "SUCCESS",
            "LOGIN SUCCESSFUL",
            parent=self.window
        )

        curDate = time.localtime()
        curTime = time.strftime("%H:%M:%S")

        with open("datas/login.txt", "a") as file:
            file.write(
                f"Logged in by {user} at {curDate[2]}/{curDate[1]}/{curDate[0]} , {curTime}\n"
            )

        self.success = True
        self.window.destroy()

    def clear(self):
        self.varUser.set("")
        self.varPass.set("")

    def checkCredentials(self, event=None):
        if not self.varUser.get():
            return messagebox.showwarning("WARNING", "PLEASE ENTER USER NAME", parent=self.window)

        if not self.varPass.get():
            return messagebox.showwarning("WARNING", "PLEASE ENTER PASSWORD", parent=self.window)

        sign = super().auth(self.varUser.get(), self.varPass.get())
        if sign is not None:
            self.destroyWindow(self.varUser.get())
        else:
            messagebox.showwarning("WARNING", "CREDENTIALS ARE WRONG", parent=self.window)

    def killAll(self):
        self.window.destroy()
        sys.exit(0)
