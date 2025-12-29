import fitz  # PyMuPDF
import customtkinter as ctk
from PIL import Image, ImageTk
from customtkinter import CTkImage


class PdfViewer(ctk.CTkToplevel):
    def __init__(self, master, pdf_path):
        super().__init__(master)
        self.title("PDF Viewer")
        self.attributes("-topmost", True)
        self.geometry("900x700")
        self.pdf_path = pdf_path
        self.page_number = 0

        pdf_frame = ctk.CTkScrollableFrame(self)
        pdf_frame.pack(fill="both", expand=True)

        self.image_label = ctk.CTkLabel(
            pdf_frame,
            text="",              # IMPORTANT
            fg_color="transparent"
        )

        self.image_label.pack(expand=True, fill="both", pady=10)

        self.load_pdf()

        # Buttons
        self.next_btn = ctk.CTkButton(
            self, text="Next", command=self.next_page)
        self.next_btn.pack(side="right", padx=10, pady=10)

        self.prev_btn = ctk.CTkButton(
            self, text="Previous", command=self.prev_page)
        self.prev_btn.pack(side="left", padx=10, pady=10)

        self.label = ctk.CTkLabel(
            self, text=f"Page {self.page_number + 1}/{len(fitz.open(self.pdf_path))}")
        self.label.pack(anchor="center", side="top", padx=10, pady=10)

    def load_pdf(self):
        pdf = fitz.open(self.pdf_path)
        page = pdf.load_page(self.page_number)

        # Increase DPI for clarity (2.0 = ~144 DPI)
        zoom = 2.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)

        image = Image.frombytes(
            "RGB",
            (pix.width, pix.height),
            pix.samples
        )

        # Optional: Resize cleanly using LANCZOS
        max_width = 800
        scale = max_width / image.width
        new_size = (int(image.width * scale), int(image.height * scale))
        image = image.resize(new_size, Image.LANCZOS)

        ctk_img = CTkImage(
            light_image=image,
            dark_image=image,
            size=image.size
        )

        self.image_label.configure(image=ctk_img)
        self.image_label.image = ctk_img
        

    def next_page(self):
        pdf = fitz.open(self.pdf_path)
        if self.page_number + 1 < len(pdf):
            self.page_number += 1
            self.load_pdf()
            self.label.configure(
                text=f"Page {self.page_number+1}/{len(fitz.open(self.pdf_path))}")

    def prev_page(self):
        if self.page_number > 0:
            self.page_number -= 1
            self.load_pdf()
            self.label.configure(
                text=f"Page {self.page_number+1}/{len(fitz.open(self.pdf_path))}")
