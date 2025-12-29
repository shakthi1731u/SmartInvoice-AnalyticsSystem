from customtkinter import *


class SplashScreen:
    def __init__(self, master, on_close, duration=3000):
        self.on_close = on_close
        self.root = CTkToplevel(master)
        self.root.geometry("600x400+400+150")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.0)

        self.title = CTkLabel(
            self.root,
            text="SBHL LIMITED",
            font=("Poppins Bold", 25),
            text_color="#00ADB5"
        )
        self.title.pack(pady=100)

        self.progress = CTkProgressBar(
            self.root, width=400, height=10
        )
        self.progress.pack(pady=30)
        self.progress.set(0)

        self.alpha = 0.0
        self.step = 0
        self.duration = duration

        self.fade_in()

    def fade_in(self):
        if self.alpha < 1.0:
            self.alpha += 0.05
            self.root.attributes("-alpha", self.alpha)
            self.root.after(20, self.fade_in)
        else:
            self.load()

    def load(self):
        if self.step <= 100:
            self.progress.set(self.step / 100)
            self.step += 1
            self.root.after(self.duration // 100, self.load)
        else:
            self.fade_out()

    def fade_out(self):
        if self.alpha > 0.0:
            self.alpha -= 0.05
            self.root.attributes("-alpha", self.alpha)
            self.root.after(20, self.fade_out)
        else:
            self.root.destroy()
            self.on_close()
