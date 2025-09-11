import customtkinter
import json
from tkinter import filedialog
from gui.base_frame import BaseFrame
from operations.encoders import to_base64
from operations.ciphers import caesar_cipher
from operations.hex import to_hex


class EncryptFrame(BaseFrame):
    def __init__(self, master, app, status_bar, **kwargs):
        # --- Set unique properties for this frame ---
        self.recipe_title = "Encryption Recipe"
        self.placeholder_text = "Click an operation to begin..."
        self.load_button_text = "📂 Load"
        self.load_button_width = 70

        super().__init__(master, app, status_bar, **kwargs)

    def execute_operation(self, operation_name, input_data, step_frame):
        if operation_name == "To Base64":
            return to_base64(input_data)
        elif operation_name == "To Hex":
            return to_hex(input_data)
        elif operation_name == "Caesar Encrypt":
            try:
                shift = int(step_frame.param_entry.get())
                if not 1 <= shift <= 25:
                    return False, "Shift must be between 1 and 25."
                return caesar_cipher(input_data, shift, decrypt=False)
            except (ValueError, TypeError):
                return False, "Invalid shift value. Must be an integer."
            except AttributeError:
                return False, "Could not find shift parameter."
        else:
            return False, f"Unknown operation: {operation_name}"

    def create_operations_sidebar(self):
        sidebar_frame = customtkinter.CTkFrame(self)
        sidebar_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        sidebar_frame.grid_rowconfigure(1, weight=1);
        sidebar_frame.grid_columnconfigure(0, weight=1)
        customtkinter.CTkLabel(sidebar_frame, text="Operations",
                               font=customtkinter.CTkFont(size=18, weight="bold")).grid(row=0, column=0, padx=20,
                                                                                        pady=(10, 10))
        scrollable_frame = customtkinter.CTkScrollableFrame(sidebar_frame, fg_color="transparent", corner_radius=0)
        scrollable_frame.grid(row=1, column=0, sticky="nsew", pady=(10, 0));
        scrollable_frame.grid_columnconfigure(0, weight=1)

        encoder_label = customtkinter.CTkLabel(scrollable_frame, text="Encoders / Decoders",
                                               font=customtkinter.CTkFont(weight="bold"))
        encoder_label.grid(row=0, column=0, pady=(5, 2), padx=10, sticky="w")

        to_base64_btn = customtkinter.CTkButton(scrollable_frame, text="To Base64", anchor="w",
                                                command=lambda: self.add_recipe_step("To Base64"))
        to_base64_btn.grid(row=1, column=0, sticky="ew", padx=10, pady=2)

        to_hex_btn = customtkinter.CTkButton(scrollable_frame, text="To Hex", anchor="w",
                                             command=lambda: self.add_recipe_step("To Hex"))
        to_hex_btn.grid(row=2, column=0, sticky="ew", padx=10, pady=2)

        cipher_label = customtkinter.CTkLabel(scrollable_frame, text="Ciphers",
                                              font=customtkinter.CTkFont(weight="bold"))
        cipher_label.grid(row=3, column=0, pady=(15, 2), padx=10, sticky="w")

        caesar_encrypt_btn = customtkinter.CTkButton(scrollable_frame, text="Caesar Encrypt", anchor="w",
                                                     command=lambda: self.add_recipe_step("Caesar Encrypt"))
        caesar_encrypt_btn.grid(row=4, column=0, sticky="ew", padx=10, pady=2)

        aes_encrypt_btn = customtkinter.CTkButton(scrollable_frame, text="AES Encrypt", anchor="w",
                                                  command=lambda: self.add_recipe_step("AES Encrypt"))
        aes_encrypt_btn.grid(row=5, column=0, sticky="ew", padx=10, pady=2)

    def load_recipe(self):
        filepath = filedialog.askopenfilename(title="Load Recipe", filetypes=[("JSON files", "*.json")])
        if not filepath: return
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                recipe_data = json.load(f)
            self.clear_recipe()
            for step in recipe_data:
                operation_name = step.get("operation")
                args = step.get("args", {})
                if operation_name: self.add_recipe_step(operation_name, args=args)
            self.status_bar.configure(text=f"Recipe loaded!", text_color="gray70")
        except Exception as e:
            self.app.show_toast("File Error", f"Failed to load recipe: {e}", toast_type="error")