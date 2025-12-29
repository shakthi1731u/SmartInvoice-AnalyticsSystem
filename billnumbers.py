from customtkinter import CTkToplevel, CTkLabel, CTkEntry, CTkButton, StringVar
import configparser
from tkinter import messagebox


class billNumbers:
    def __init__(self, master, windowControl, font="Roboto"):
        self.windowControl = windowControl
        self.master = master
        self.font = font
        self.settings = CTkToplevel(self.master)
        self.settings.geometry("300x200+450+200")
        self.settings.wm_protocol("WM_DELETE_WINDOW", self.destroy)
        self.settings.wm_transient(self.master)
        self.settings.title("Bill Numbers")
        self.settings.resizable(False, False)

        self.dconfig = configparser.ConfigParser()
        self.tconfig = configparser.ConfigParser()
        self.dconfig.read("config/dcdetails.ini")
        self.tconfig.read("config/invoicedetails.ini")
        self.dcno = self.tempdcno = StringVar(
            value=self.dconfig.get("SectionOne", "dcno"))
        self.taxinvoiceno = self.tempinvoiceno = StringVar(
            value=self.tconfig.get("SectionOne", "invoiceno"))

        CTkLabel(self.settings,
                 text="Bill Numbers",
                 font=(self.font, 20)).place(relx=0.40, rely=0.05)

        CTkLabel(self.settings,
                 text="DeliverChallan NO",
                 font=(self.font, 13)).place(relx=0.10, rely=0.30)
        CTkEntry(self.settings,
                 textvariable=self.dcno,
                 font=(self.font, 13)).place(relx=0.5, rely=0.30)

        CTkLabel(self.settings,
                 text="Tax Invoice NO",
                 font=(self.font, 13)).place(relx=0.10, rely=0.55)
        CTkEntry(self.settings,
                 textvariable=self.taxinvoiceno,
                 font=(self.font, 13)).place(relx=0.5, rely=0.55)

        CTkButton(self.settings,
                  text="Save",
                  font=(self.font, 13),
                  command=self.save).place(relx=0.3, rely=0.75)

    def save(self):
        if self.tempdcno == self.dcno.get() and self.tempinvoiceno == self.taxinvoiceno.get():
            return

        self.dconfig.set("SectionOne", "dcno", self.dcno.get())
        self.tconfig.set("SectionOne", "invoiceno", self.taxinvoiceno.get())
        
        with open("config/dcdetails.ini", "w") as configfile:
            self.dconfig.write(configfile)
        with open("config/invoicedetails.ini", "w") as configfile:
            self.tconfig.write(configfile)

        self.tempdcno = self.dcno.get()
        self.tempinvoiceno = self.taxinvoiceno.get()

        messagebox.showinfo("SUCCESS", "Settings Saved Successfully")

    def destroy(self):
        self.windowControl["bill_number"] = False
        self.settings.destroy()
