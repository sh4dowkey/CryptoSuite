import customtkinter
from gui.encrypt_frame import EncryptFrame
from gui.decrypt_frame import DecryptFrame
from gui.toast import ToastNotification


class App(customtkinter.CTk):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title("CryptoSuite")
        self.geometry("1200x700")
        self.minsize(1100, 600)
        customtkinter.set_appearance_mode("Dark")
        customtkinter.set_default_color_theme("blue")

        self.active_toast = None

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.header_frame = customtkinter.CTkFrame(self, height=60, corner_radius=0)
        self.header_frame.grid(row=0, column=0, sticky="ew")
        self.header_frame.grid_columnconfigure(0, weight=1)
        self.app_name_label = customtkinter.CTkLabel(self.header_frame, text="CryptoSuite 🔐",
                                                     font=customtkinter.CTkFont(family="Helvetica", size=24,
                                                                                weight="bold"))
        self.app_name_label.grid(row=0, column=0, padx=20, pady=15, sticky="w")

        self.main_body_frame = customtkinter.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_body_frame.grid(row=1, column=0, sticky="nsew")
        self.main_body_frame.grid_columnconfigure(1, weight=1)
        self.main_body_frame.grid_rowconfigure(0, weight=1)

        self.navigation_rail = customtkinter.CTkFrame(self.main_body_frame, width=150, corner_radius=0)
        self.navigation_rail.grid(row=0, column=0, sticky="nsw")
        self.navigation_rail.grid_rowconfigure(3, weight=1)

        self.encrypt_button = customtkinter.CTkButton(self.navigation_rail, text="🔒  Encrypt",
                                                      command=lambda: self.select_frame("encrypt"), corner_radius=0,
                                                      height=50, font=("", 16), anchor="w", border_spacing=10)
        self.encrypt_button.grid(row=0, column=0, sticky="ew", pady=(5, 0))

        self.decrypt_button = customtkinter.CTkButton(self.navigation_rail, text="🔓  Decrypt",
                                                      command=lambda: self.select_frame("decrypt"), corner_radius=0,
                                                      height=50, font=("", 16), anchor="w", border_spacing=10)
        self.decrypt_button.grid(row=1, column=0, sticky="ew")

        self.frame_container = customtkinter.CTkFrame(self.main_body_frame, fg_color="transparent")
        self.frame_container.grid(row=0, column=1, sticky="nsew")

        self.status_bar = customtkinter.CTkLabel(self, text="Ready", anchor="w", font=("", 12))
        self.status_bar.grid(row=2, column=0, sticky="ew", padx=10, pady=(5, 5))

        self.frames = {
            "encrypt": EncryptFrame(master=self.frame_container, app=self, status_bar=self.status_bar),
            "decrypt": DecryptFrame(master=self.frame_container, app=self, status_bar=self.status_bar)
        }
        self.select_frame("encrypt")

    def show_toast(self, title, message, toast_type="info"):
        if self.active_toast is not None and self.active_toast.winfo_exists():
            self.active_toast.destroy()

        toast = ToastNotification(self, title, message, toast_type)
        toast.place(relx=0.99, rely=0.98, anchor="se")
        toast.lift()

        self.active_toast = toast

        self.after(4000, toast.destroy)

    def select_frame(self, name):
        self.encrypt_button.configure(
            fg_color="transparent" if name != "encrypt" else customtkinter.ThemeManager.theme["CTkButton"]["fg_color"])
        self.decrypt_button.configure(
            fg_color="transparent" if name != "decrypt" else customtkinter.ThemeManager.theme["CTkButton"]["fg_color"])

        for frame_name, frame in self.frames.items():
            if frame_name == name:
                frame.pack(fill="both", expand=True)
            else:
                frame.pack_forget()