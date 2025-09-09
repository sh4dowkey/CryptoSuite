# File: gui/toast.py

import customtkinter


class ToastNotification(customtkinter.CTkFrame):
    def __init__(self, master, title, message, toast_type="info"):
        super().__init__(master)

        # Configure the frame style based on the message type
        styles = {
            "info": {"fg_color": "#17A2B8", "text_color": "white"},
            "success": {"fg_color": "#28A745", "text_color": "white"},
            "warning": {"fg_color": "#FFC107", "text_color": "black"},
            "error": {"fg_color": "#DC3545", "text_color": "white"}
        }
        style = styles.get(toast_type, styles["info"])

        self.configure(corner_radius=7, fg_color=style["fg_color"])

        # --- Content ---
        title_label = customtkinter.CTkLabel(self, text=title, text_color=style["text_color"],
                                             font=customtkinter.CTkFont(size=16, weight="bold"))
        title_label.pack(padx=20, pady=(10, 5), anchor="w")

        message_label = customtkinter.CTkLabel(self, text=message, text_color=style["text_color"],
                                               font=customtkinter.CTkFont(size=14), wraplength=450, justify="left")
        message_label.pack(padx=20, pady=(0, 15), anchor="w")

        # This toast will be created, placed, and destroyed by the main App class
