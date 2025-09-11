import customtkinter
import json
from tkinter import filedialog
from gui.base_frame import BaseFrame
from operations.encoders import from_base64
from operations.ciphers import caesar_cipher
from operations.hex import from_hex


class DecryptFrame(BaseFrame):
    def __init__(self, master, app, status_bar, **kwargs):
        # --- Set unique properties for this frame ---
        self.recipe_title = "Decryption Recipe"
        self.placeholder_text = "Click an operation or load & invert a recipe..."
        self.load_button_text = "📂 Load & Invert"
        self.load_button_width = 110

        self.inverse_operations = {
            "To Base64": "From Base64", "From Base64": "To Base64",
            "To Hex": "From Hex", "From Hex": "To Hex",
            "Caesar Encrypt": "Caesar Decrypt", "Caesar Decrypt": "Caesar Encrypt",
            "AES Encrypt": "AES Decrypt", "AES Decrypt": "AES Encrypt"
        }

        super().__init__(master, app, status_bar, **kwargs)

    def execute_operation(self, operation_name, input_data, step_frame):
        if operation_name == "From Base64":
            return from_base64(input_data)
        elif operation_name == "From Hex":
            return from_hex(input_data)
        elif operation_name == "Caesar Decrypt":
            try:
                shift = int(step_frame.param_entry.get())
                if not 1 <= shift <= 25:
                    return False, "Shift must be between 1 and 25."
                return caesar_cipher(input_data, shift, decrypt=True)
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

        decoder_label = customtkinter.CTkLabel(scrollable_frame, text="Decoders",
                                               font=customtkinter.CTkFont(weight="bold"))
        decoder_label.grid(row=0, column=0, pady=(5, 2), padx=10, sticky="w")

        from_base64_btn = customtkinter.CTkButton(scrollable_frame, text="From Base64", anchor="w",
                                                  command=lambda: self.add_recipe_step("From Base64"))
        from_base64_btn.grid(row=1, column=0, sticky="ew", padx=10, pady=2)

        from_hex_btn = customtkinter.CTkButton(scrollable_frame, text="From Hex", anchor="w",
                                               command=lambda: self.add_recipe_step("From Hex"))
        from_hex_btn.grid(row=2, column=0, sticky="ew", padx=10, pady=2)

        cipher_label = customtkinter.CTkLabel(scrollable_frame, text="Ciphers",
                                              font=customtkinter.CTkFont(weight="bold"))
        cipher_label.grid(row=3, column=0, pady=(15, 2), padx=10, sticky="w")

        caesar_decrypt_btn = customtkinter.CTkButton(scrollable_frame, text="Caesar Decrypt", anchor="w",
                                                     command=lambda: self.add_recipe_step("Caesar Decrypt"))
        caesar_decrypt_btn.grid(row=4, column=0, sticky="ew", padx=10, pady=2)

        aes_decrypt_btn = customtkinter.CTkButton(scrollable_frame, text="AES Decrypt", anchor="w",
                                                  command=lambda: self.add_recipe_step("AES Decrypt"))
        aes_decrypt_btn.grid(row=5, column=0, sticky="ew", padx=10, pady=2)

    def load_recipe(self):
        filepath = filedialog.askopenfilename(title="Load and Invert Recipe", filetypes=[("JSON files", "*.json")])
        if not filepath: return
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                recipe_data = json.load(f)
            self.clear_recipe()

            for step in reversed(recipe_data):
                original_op_name = step.get("operation")
                inverted_op_name = self.inverse_operations.get(original_op_name, "Unknown")

                if inverted_op_name == "Unknown":
                    self.app.show_toast("Warning", f"Could not find an inverse for '{original_op_name}'. Skipping.",
                                        "warning")
                    continue

                args = step.get("args", {})
                self.add_recipe_step(inverted_op_name, args=args)

            self.status_bar.configure(text=f"Recipe loaded and inverted!", text_color="gray70")
        except Exception as e:
            self.app.show_toast("File Error", f"Failed to load and invert recipe: {e}", toast_type="error")

    # --- NEW: Placeholder function for the Auto-Detect button ---
    def auto_detect_placeholder(self):
        """Shows a toast notification for the coming soon feature."""
        self.app.show_toast("Coming Soon!", "The Auto-Detect feature is currently under development.",
                            toast_type="info")

    def create_recipe_panel(self):
        # --- MODIFIED: This panel now includes the Auto-Detect button again ---
        recipe_frame = customtkinter.CTkFrame(self)
        recipe_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=10)
        recipe_frame.grid_rowconfigure(2, weight=1);
        recipe_frame.grid_columnconfigure(0, weight=1)
        recipe_header = customtkinter.CTkFrame(recipe_frame, fg_color="transparent")
        recipe_header.grid(row=0, column=0, padx=20, pady=(10, 5), sticky="ew")

        customtkinter.CTkLabel(recipe_header, text=self.recipe_title,
                               font=customtkinter.CTkFont(size=18, weight="bold")).pack(side="left", padx=(0, 10))
        customtkinter.CTkButton(recipe_header, text=self.load_button_text, width=self.load_button_width,
                                command=self.load_recipe).pack(side="right", padx=(5, 0))
        customtkinter.CTkButton(recipe_header, text="💾 Save", width=70, command=self.save_recipe).pack(side="right",
                                                                                                       padx=(5, 0))
        customtkinter.CTkButton(recipe_header, text="Clear All", width=80, command=self.clear_recipe, fg_color="gray40",
                                hover_color="gray30").pack(side="right")

        # The Auto-Detect button is added back here
        auto_detect_button = customtkinter.CTkButton(recipe_frame, text="Auto-Detect Magic ✨", height=40,
                                                     command=self.auto_detect_placeholder)
        auto_detect_button.grid(row=1, column=0, padx=10, pady=(5, 10), sticky="ew")

        self.recipe_scrollable_frame = customtkinter.CTkScrollableFrame(recipe_frame)
        self.recipe_scrollable_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

        button_frame = customtkinter.CTkFrame(recipe_frame, fg_color="transparent")
        button_frame.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        button_frame.grid_columnconfigure((0, 1), weight=1)

        self.step_button = customtkinter.CTkButton(button_frame, text="Step", height=40,
                                                   font=customtkinter.CTkFont(size=16), fg_color="#494949",
                                                   hover_color="#333333", command=self.process_step)
        self.step_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        self.bake_button = customtkinter.CTkButton(button_frame, text="🏭 Bake Recipe!", height=40,
                                                   font=customtkinter.CTkFont(size=16, weight="bold"),
                                                   command=self.bake_recipe)
        self.bake_button.grid(row=0, column=1, padx=(5, 0), sticky="ew")