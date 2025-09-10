import customtkinter
import pyperclip
import json
from tkinter import filedialog
from operations.encoders import from_base64
from gui.toast import ToastNotification


class DecryptFrame(customtkinter.CTkFrame):
    def __init__(self, master, app, status_bar, **kwargs):
        super().__init__(master, **kwargs)
        self.app = app
        self.status_bar = status_bar
        self.configure(fg_color="transparent")

        self.current_step_index = 0
        self.operation_widgets = {}
        self.category_labels = {}

        self.grid_columnconfigure(0, weight=2, minsize=200)
        self.grid_columnconfigure(1, weight=3, minsize=300)
        self.grid_columnconfigure(2, weight=4, minsize=400)
        self.grid_rowconfigure(0, weight=1)

        self.create_operations_sidebar()
        self.create_recipe_panel()
        self.create_io_panel()
        self.update_recipe_placeholder()

    def reset_step_state(self, event=None):
        self.current_step_index = 0
        for widget in self.recipe_scrollable_frame.winfo_children():
            if isinstance(widget, customtkinter.CTkFrame):
                widget.configure(border_width=0)
        self.status_bar.configure(text="Ready", text_color="gray70")

    def process_step(self):
        recipe_steps = [child for child in self.recipe_scrollable_frame.winfo_children() if
                        isinstance(child, customtkinter.CTkFrame)]
        if not recipe_steps:
            self.app.show_toast("Recipe Error", "Please add an operation to the recipe.", toast_type="warning")
            return
        if self.current_step_index >= len(recipe_steps):
            self.status_bar.configure(text="End of recipe reached. Resetting.", text_color="gray70")
            self.reset_step_state()
            return
        current_data = self.input_textbox.get("1.0", "end-1c")
        for i in range(self.current_step_index + 1):
            step_frame = recipe_steps[i]
            operation_label = step_frame.winfo_children()[1]
            operation_name = operation_label.cget("text")
            success, result = True, current_data
            if operation_name == "From Base64":
                success, result = from_base64(current_data)
            else:
                success, result = False, "Unknown operation in recipe."
            if not success:
                self.app.show_toast("Processing Failed", f"Step '{operation_name}' failed: {result}",
                                      toast_type="error")
                self.reset_step_state()
                return
            current_data = result
        self.output_textbox.configure(state="normal")
        self.output_textbox.delete("1.0", "end")
        self.output_textbox.insert("1.0", current_data)
        self.output_textbox.configure(state="disabled")
        self.reset_step_state()
        current_step_frame = recipe_steps[self.current_step_index]
        current_step_frame.configure(border_width=2, border_color="#3498DB")
        self.status_bar.configure(
            text=f"Executed step {self.current_step_index + 1}: {current_step_frame.winfo_children()[1].cget('text')}",
            text_color="gray70")
        self.current_step_index += 1

    def bake_recipe(self):
        self.reset_step_state()
        current_data = self.input_textbox.get("1.0", "end-1c")
        recipe_steps = [child for child in self.recipe_scrollable_frame.winfo_children() if
                        isinstance(child, customtkinter.CTkFrame)]
        if not current_data:
            self.app.show_toast("Input Error", "The input field is empty.", toast_type="error")
            return
        if not recipe_steps:
            self.app.show_toast("Recipe Error", "Please add at least one operation to the recipe.",
                                  toast_type="warning")
            return
        for step_frame in recipe_steps:
            operation_label = step_frame.winfo_children()[1]
            operation_name = operation_label.cget("text")
            success, result = True, current_data
            if operation_name == "From Base64":
                success, result = from_base64(current_data)
            else:
                success, result = False, "Unknown operation in recipe."
            if not success:
                self.app.show_toast("Processing Failed", f"Step '{operation_name}' failed: {result}",
                                      toast_type="error")
                return
            current_data = result
        self.output_textbox.configure(state="normal")
        self.output_textbox.delete("1.0", "end")
        self.output_textbox.insert("1.0", current_data)
        self.output_textbox.configure(state="disabled")
        self.status_bar.configure(text="Recipe baked successfully!", text_color="gray70")

    def clear_recipe(self):
        for widget in self.recipe_scrollable_frame.winfo_children():
            widget.destroy()
        self.recipe_placeholder = customtkinter.CTkLabel(self.recipe_scrollable_frame,
                                                         text="Build recipe or use Auto-Detect...", font=("", 14),
                                                         text_color="gray60")
        self.update_recipe_placeholder()
        self.reset_step_state()

    def copy_output(self):
        content = self.output_textbox.get("1.0", "end-1c")
        if content:
            pyperclip.copy(content)
            self.status_bar.configure(text="Output copied to clipboard.", text_color="gray70")
        else:
            self.app.show_toast("Warning", "Output is empty, nothing to copy.", toast_type="warning")

    def save_recipe(self):
        recipe_steps = [child for child in self.recipe_scrollable_frame.winfo_children() if
                        isinstance(child, customtkinter.CTkFrame)]
        if not recipe_steps: self.app.show_toast("Warning", "Recipe is empty, nothing to save.",
                                                  toast_type="warning"); return
        recipe_data = []
        for step_frame in recipe_steps:
            operation_label = step_frame.winfo_children()[1]
            operation_name = operation_label.cget("text")
            step_dict = {"operation": operation_name, "args": {}}
            for widget in step_frame.winfo_children():
                if isinstance(widget, customtkinter.CTkEntry): step_dict["args"]["key"] = widget.get()
            recipe_data.append(step_dict)
        filepath = filedialog.asksaveasfilename(title="Save Recipe As", defaultextension=".json",
                                                filetypes=[("JSON files", "*.json")])
        if not filepath: return
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(recipe_data, f, indent=4)
            self.status_bar.configure(text=f"Recipe saved!", text_color="gray70")
        except Exception as e:
            self.app.show_toast("File Error", f"Failed to save recipe: {e}", toast_type="error")

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

    # --- The rest of the file is unchanged ---
    def update_recipe_placeholder(self):
        step_frames = [child for child in self.recipe_scrollable_frame.winfo_children() if
                       isinstance(child, customtkinter.CTkFrame)]
        if not step_frames:
            self.recipe_placeholder.pack(expand=True)
        else:
            self.recipe_placeholder.pack_forget()

    def add_recipe_step(self, operation_name, args=None):
        if args is None: args = {}
        self.update_recipe_placeholder()
        step_frame = customtkinter.CTkFrame(self.recipe_scrollable_frame)
        step_frame.pack(fill="x", padx=10, pady=4)
        customtkinter.CTkLabel(step_frame, text="⠿", font=("", 20), fg_color="transparent").pack(side="left",
                                                                                                 padx=(10, 5), pady=5)
        customtkinter.CTkLabel(step_frame, text=operation_name).pack(side="left", padx=5, pady=5)
        if "AES" in operation_name:
            key = args.get("key", "")
            entry = customtkinter.CTkEntry(step_frame, placeholder_text="Enter Key...", width=120)
            entry.insert(0, key)
            entry.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        remove_button = customtkinter.CTkButton(step_frame, text="✖", width=28, height=28, fg_color="transparent",
                                                hover_color="#333333")
        remove_button.pack(side="right", padx=5, pady=5)
        remove_button.configure(
            command=lambda: (step_frame.destroy(), self.update_recipe_placeholder(), self.reset_step_state()))
        self.reset_step_state()

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
        from_base64 = customtkinter.CTkButton(scrollable_frame, text="From Base64", anchor="w",
                                              command=lambda: self.add_recipe_step("From Base64"))
        from_base64.grid(row=1, column=0, sticky="ew", padx=10, pady=2)

        cipher_label = customtkinter.CTkLabel(scrollable_frame, text="Ciphers",
                                              font=customtkinter.CTkFont(weight="bold"))
        cipher_label.grid(row=2, column=0, pady=(15, 2), padx=10, sticky="w")
        aes_decrypt = customtkinter.CTkButton(scrollable_frame, text="AES Decrypt", anchor="w",
                                              command=lambda: self.add_recipe_step("AES Decrypt"))
        aes_decrypt.grid(row=3, column=0, sticky="ew", padx=10, pady=2)

        self.category_labels["decoders"] = decoder_label
        self.operation_widgets["decoders"] = [from_base64]
        self.category_labels["ciphers"] = cipher_label
        self.operation_widgets["ciphers"] = [aes_decrypt]

    def create_recipe_panel(self):
        recipe_frame = customtkinter.CTkFrame(self)
        recipe_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=10)
        recipe_frame.grid_rowconfigure(2, weight=1);
        recipe_frame.grid_columnconfigure(0, weight=1)

        recipe_header = customtkinter.CTkFrame(recipe_frame, fg_color="transparent")
        recipe_header.grid(row=0, column=0, padx=20, pady=(10, 5), sticky="ew")
        customtkinter.CTkLabel(recipe_header, text="Decryption Recipe",
                               font=customtkinter.CTkFont(size=18, weight="bold")).pack(side="left", padx=(0, 10))
        customtkinter.CTkButton(recipe_header, text="📂 Load", width=70, command=self.load_recipe).pack(side="right",
                                                                                                         padx=(5, 0))
        customtkinter.CTkButton(recipe_header, text="💾 Save", width=70, command=self.save_recipe).pack(side="right",
                                                                                                         padx=(5, 0))
        customtkinter.CTkButton(recipe_header, text="Clear All", width=80, command=self.clear_recipe, fg_color="gray40",
                                hover_color="gray30").pack(side="right")

        customtkinter.CTkButton(recipe_frame, text="Auto-Detect Magic ✨", height=40).grid(row=1, column=0, padx=10,
                                                                                         pady=(5, 10), sticky="ew")
        self.recipe_scrollable_frame = customtkinter.CTkScrollableFrame(recipe_frame)
        self.recipe_scrollable_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        self.recipe_placeholder = customtkinter.CTkLabel(self.recipe_scrollable_frame,
                                                         text="Build recipe or use Auto-Detect...", font=("", 14),
                                                         text_color="gray60")

        button_frame = customtkinter.CTkFrame(recipe_frame, fg_color="transparent")
        button_frame.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        button_frame.grid_columnconfigure((0, 1), weight=1)
        customtkinter.CTkButton(button_frame, text="Step", height=40, font=customtkinter.CTkFont(size=16),
                                fg_color="#494949", hover_color="#333333", command=self.process_step).grid(row=0,
                                                                                                            column=0,
                                                                                                            padx=(0, 5),
                                                                                                            sticky="ew")
        customtkinter.CTkButton(button_frame, text="🏭 Bake Recipe!", height=40,
                                font=customtkinter.CTkFont(size=16, weight="bold"), command=self.bake_recipe).grid(
            row=0, column=1, padx=(5, 0), sticky="ew")

    def create_io_panel(self):
        io_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        io_frame.grid(row=0, column=2, sticky="nsew", padx=(5, 10), pady=10)
        io_frame.grid_rowconfigure((1, 3), weight=1);
        io_frame.grid_columnconfigure(0, weight=1)

        input_controls = customtkinter.CTkFrame(io_frame, fg_color="transparent")
        input_controls.grid(row=0, column=0, padx=10, pady=(0, 5), sticky="ew")
        customtkinter.CTkLabel(input_controls, text="Input", font=customtkinter.CTkFont(size=16)).pack(side="left")
        customtkinter.CTkButton(input_controls, text="❌ Clear", width=80, command=self.clear_input, fg_color="#D2691E",
                                hover_color="#C2590E").pack(side="right", padx=(5, 0))
        customtkinter.CTkButton(input_controls, text="📂 Open", width=80, command=self.open_from_file).pack(side="right",
                                                                                                           padx=(5, 0))
        customtkinter.CTkButton(input_controls, text="📋 Paste", width=80, command=self.paste_to_input).pack(
            side="right", padx=(5, 0))
        self.input_textbox = customtkinter.CTkTextbox(io_frame)
        self.input_textbox.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self.input_textbox.bind("<KeyRelease>", self.reset_step_state)

        output_controls = customtkinter.CTkFrame(io_frame, fg_color="transparent")
        output_controls.grid(row=2, column=0, padx=10, pady=(10, 5), sticky="ew")
        customtkinter.CTkLabel(output_controls, text="Final Output", font=customtkinter.CTkFont(size=16)).pack(
            side="left")
        customtkinter.CTkButton(output_controls, text="❌ Clear", width=80, command=self.clear_output,
                                fg_color="#D2691E", hover_color="#C2590E").pack(side="right", padx=(5, 0))
        customtkinter.CTkButton(output_controls, text="💾 Save", width=80, command=self.save_to_file).pack(side="right",
                                                                                                           padx=(5, 0))
        customtkinter.CTkButton(output_controls, text="📝 Copy", width=80, command=self.copy_output).pack(side="right",
                                                                                                           padx=(5, 0))
        self.output_textbox = customtkinter.CTkTextbox(io_frame, state="disabled")
        self.output_textbox.grid(row=3, column=0, padx=10, pady=(0, 0), sticky="nsew")

    def open_from_file(self):
        filepath = filedialog.askopenfilename(title="Open Text File",
                                              filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if not filepath: return
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.input_textbox.delete("1.0", "end"); self.input_textbox.insert("1.0", f.read())
            self.reset_step_state()
        except Exception as e:
            self.app.show_toast("File Error", f"Failed to read file: {e}", toast_type="error")

    def save_to_file(self):
        content = self.output_textbox.get("1.0", "end-1c")
        if not content: self.app.show_toast("Warning", "Output is empty.", toast_type="warning"); return
        filepath = filedialog.asksaveasfilename(title="Save Output As", defaultextension=".txt",
                                                filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if not filepath: return
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            self.app.show_toast("Error", f"Failed to save file: {e}", toast_type="error")

    def paste_to_input(self):
        try:
            self.input_textbox.delete("1.0", "end");
            self.input_textbox.insert("1.0", pyperclip.paste())
            self.reset_step_state()
        except Exception as e:
            self.app.show_toast("Error", f"Could not paste from clipboard: {e}", toast_type="error")

    def clear_input(self):
        self.input_textbox.delete("1.0", "end")
        self.reset_step_state()

    def clear_output(self):
        self.output_textbox.configure(state="normal");
        self.output_textbox.delete("1.0", "end");
        self.output_textbox.configure(state="disabled")