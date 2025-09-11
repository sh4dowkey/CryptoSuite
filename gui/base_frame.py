# File: gui/base_frame.py

import customtkinter
import pyperclip
import json
import threading
import queue
from tkinter import filedialog


class BaseFrame(customtkinter.CTkFrame):
    def __init__(self, master, app, status_bar, **kwargs):
        super().__init__(master, **kwargs)
        self.app = app
        self.status_bar = status_bar
        self.configure(fg_color="transparent")

        # --- Core Attributes ---
        self.current_step_index = 0
        self.recipe_placeholder = None
        self.result_queue = queue.Queue()

        # --- Layout Configuration ---
        self.grid_columnconfigure(0, weight=2, minsize=200)
        self.grid_columnconfigure(1, weight=3, minsize=300)
        self.grid_columnconfigure(2, weight=4, minsize=400)
        self.grid_rowconfigure(0, weight=1)

        # --- Build UI ---
        # These methods will be defined in the child classes (EncryptFrame, DecryptFrame)
        self.create_operations_sidebar()
        self.create_recipe_panel()
        self.create_io_panel()
        self.update_recipe_placeholder()

    # --- Threading and Processing Logic (Common to both frames) ---

    def set_processing_state(self, is_processing: bool):
        """Disables/Enables buttons during processing."""
        state = "disabled" if is_processing else "normal"
        self.bake_button.configure(state=state)
        self.step_button.configure(state=state)
        if is_processing:
            self.status_bar.configure(text="Processing... Please wait.", text_color="orange")

    def reset_step_state(self, event=None):
        self.current_step_index = 0
        for widget in self.recipe_scrollable_frame.winfo_children():
            if isinstance(widget, customtkinter.CTkFrame):
                widget.configure(border_width=0)
        self.status_bar.configure(text="Ready", text_color="gray70")

    def process_step(self):
        """Starts step-by-step processing in a background thread."""
        self.set_processing_state(True)
        thread = threading.Thread(target=self._worker_process_step)
        thread.daemon = True
        thread.start()
        self.after(100, self.check_queue)

    def bake_recipe(self):
        """Starts full recipe processing in a background thread."""
        self.set_processing_state(True)
        thread = threading.Thread(target=self._worker_bake_recipe)
        thread.daemon = True
        thread.start()
        self.after(100, self.check_queue)

    def _worker_process_step(self):
        """Worker function for step processing (runs in background)."""
        recipe_steps = [child for child in self.recipe_scrollable_frame.winfo_children() if
                        isinstance(child, customtkinter.CTkFrame)]
        if not recipe_steps:
            self.result_queue.put(("error", ("Recipe Error", "Please add an operation.")))
            return

        if self.current_step_index >= len(recipe_steps):
            self.result_queue.put(("reset", "End of recipe reached. Resetting."))
            return

        current_data = self.input_textbox.get("1.0", "end-1c")

        for i in range(self.current_step_index + 1):
            step_frame = recipe_steps[i]
            operation_name = step_frame.op_name
            success, current_data = self.execute_operation(operation_name, current_data, step_frame)
            if not success:
                self.result_queue.put(
                    ("error", ("Processing Failed", f"Step '{operation_name}' failed: {current_data}")))
                return

        self.result_queue.put(("step_success", (current_data, self.current_step_index)))

    def _worker_bake_recipe(self):
        """Worker function for baking (runs in background)."""
        self.reset_step_state()
        current_data = self.input_textbox.get("1.0", "end-1c")
        recipe_steps = [child for child in self.recipe_scrollable_frame.winfo_children() if
                        isinstance(child, customtkinter.CTkFrame)]

        if not current_data:
            self.result_queue.put(("error", ("Input Error", "The input field is empty.")))
            return
        if not recipe_steps:
            self.result_queue.put(("error", ("Recipe Error", "Please add at least one operation.")))
            return

        for step_frame in recipe_steps:
            operation_name = step_frame.op_name
            success, current_data = self.execute_operation(operation_name, current_data, step_frame)
            if not success:
                self.result_queue.put(
                    ("error", ("Processing Failed", f"Step '{operation_name}' failed: {current_data}")))
                return

        self.result_queue.put(("bake_success", current_data))

    def check_queue(self):
        """Checks queue for results from the background thread to update the UI."""
        try:
            message = self.result_queue.get_nowait()
            msg_type, data = message

            if msg_type == "bake_success":
                self.output_textbox.configure(state="normal")
                self.output_textbox.delete("1.0", "end")
                self.output_textbox.insert("1.0", data)
                self.output_textbox.configure(state="disabled")
                self.status_bar.configure(text="Recipe baked successfully!", text_color="gray70")
            elif msg_type == "step_success":
                result_data, step_index = data
                self.output_textbox.configure(state="normal")
                self.output_textbox.delete("1.0", "end")
                self.output_textbox.insert("1.0", result_data)
                self.output_textbox.configure(state="disabled")

                recipe_steps = [child for child in self.recipe_scrollable_frame.winfo_children() if
                                isinstance(child, customtkinter.CTkFrame)]
                for widget in recipe_steps: widget.configure(border_width=0)
                current_step_frame = recipe_steps[step_index]
                current_step_frame.configure(border_width=2, border_color="#3498DB")
                self.status_bar.configure(text=f"Executed step {step_index + 1}: {current_step_frame.op_name}",
                                          text_color="gray70")
                self.current_step_index += 1
            elif msg_type == "reset":
                self.status_bar.configure(text=data, text_color="gray70")
                self.reset_step_state()
            elif msg_type == "error":
                title, msg = data
                self.app.show_toast(title, msg, toast_type="error")
                self.reset_step_state()

            self.set_processing_state(False)
        except queue.Empty:
            self.after(100, self.check_queue)

    # --- Recipe and UI Management (Common to both frames) ---

    def clear_recipe(self):
        for widget in self.recipe_scrollable_frame.winfo_children():
            widget.destroy()
        self.recipe_placeholder = None
        self.update_recipe_placeholder()
        self.reset_step_state()

    def add_recipe_step(self, operation_name, args=None):
        if args is None: args = {}
        self.update_recipe_placeholder()

        step_frame = customtkinter.CTkFrame(self.recipe_scrollable_frame)
        step_frame.pack(fill="x", padx=10, pady=4)
        step_frame.op_name = operation_name
        step_frame.op_args = args

        customtkinter.CTkLabel(step_frame, text="⠿", font=("", 20), fg_color="transparent").pack(side="left",
                                                                                                 padx=(10, 5), pady=5)

        param_container = customtkinter.CTkFrame(step_frame, fg_color="transparent")
        param_container.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        customtkinter.CTkLabel(param_container, text=operation_name).pack(side="left", padx=(0, 10))

        if "Caesar" in operation_name:
            shift_val = args.get("shift", "")
            entry = customtkinter.CTkEntry(param_container, placeholder_text="Shift (1-25)", width=120)
            entry.insert(0, str(shift_val))
            entry.pack(side="left", fill="x", expand=True)
            step_frame.param_entry = entry
        elif "AES" in operation_name:
            key = args.get("key", "")
            entry = customtkinter.CTkEntry(param_container, placeholder_text="Enter Key...")
            entry.insert(0, key)
            entry.pack(side="left", fill="x", expand=True)
            step_frame.param_entry = entry

        remove_button = customtkinter.CTkButton(step_frame, text="✖", width=28, height=28, fg_color="transparent",
                                                hover_color="#333333")
        remove_button.pack(side="right", padx=(0, 5), pady=5)
        remove_button.configure(
            command=lambda sf=step_frame: (sf.destroy(), self.update_recipe_placeholder(), self.reset_step_state()))

        self.reset_step_state()
        self.update_recipe_placeholder()

    def save_recipe(self):
        recipe_steps = [child for child in self.recipe_scrollable_frame.winfo_children() if
                        isinstance(child, customtkinter.CTkFrame)]
        if not recipe_steps:
            self.app.show_toast("Warning", "Recipe is empty, nothing to save.", toast_type="warning")
            return
        recipe_data = []
        for step_frame in recipe_steps:
            operation_name = step_frame.op_name
            args = {}
            if hasattr(step_frame, 'param_entry'):
                param_value = step_frame.param_entry.get()
                if "Caesar" in operation_name:
                    args["shift"] = param_value
                elif "AES" in operation_name:
                    args["key"] = param_value
            recipe_data.append({"operation": operation_name, "args": args})
        filepath = filedialog.asksaveasfilename(title="Save Recipe As", defaultextension=".json",
                                                filetypes=[("JSON files", "*.json")])
        if not filepath: return
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(recipe_data, f, indent=4)
            self.status_bar.configure(text=f"Recipe saved!", text_color="gray70")
        except Exception as e:
            self.app.show_toast("File Error", f"Failed to save recipe: {e}", toast_type="error")

    def update_recipe_placeholder(self):
        step_frames_exist = any(
            isinstance(child, customtkinter.CTkFrame) for child in self.recipe_scrollable_frame.winfo_children())
        if not step_frames_exist:
            if self.recipe_placeholder is None or not self.recipe_placeholder.winfo_exists():
                self.recipe_placeholder = customtkinter.CTkLabel(self.recipe_scrollable_frame,
                                                                 text=self.placeholder_text, font=("", 14),
                                                                 text_color="gray60")
            self.recipe_placeholder.pack(expand=True)
        else:
            if self.recipe_placeholder is not None and self.recipe_placeholder.winfo_exists():
                self.recipe_placeholder.pack_forget()

    # --- UI Panels (Common to both frames) ---
    def create_recipe_panel(self):
        recipe_frame = customtkinter.CTkFrame(self)
        recipe_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=10)
        recipe_frame.grid_rowconfigure(1, weight=1);
        recipe_frame.grid_columnconfigure(0, weight=1)
        recipe_header = customtkinter.CTkFrame(recipe_frame, fg_color="transparent")
        recipe_header.grid(row=0, column=0, padx=20, pady=(10, 10), sticky="ew")
        customtkinter.CTkLabel(recipe_header, text=self.recipe_title,
                               font=customtkinter.CTkFont(size=18, weight="bold")).pack(side="left", padx=(0, 10))
        customtkinter.CTkButton(recipe_header, text=self.load_button_text, width=self.load_button_width,
                                command=self.load_recipe).pack(side="right", padx=(5, 0))
        customtkinter.CTkButton(recipe_header, text="💾 Save", width=70, command=self.save_recipe).pack(side="right",
                                                                                                       padx=(5, 0))
        customtkinter.CTkButton(recipe_header, text="Clear All", width=80, command=self.clear_recipe, fg_color="gray40",
                                hover_color="gray30").pack(side="right")
        self.recipe_scrollable_frame = customtkinter.CTkScrollableFrame(recipe_frame)
        self.recipe_scrollable_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        button_frame = customtkinter.CTkFrame(recipe_frame, fg_color="transparent")
        button_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        button_frame.grid_columnconfigure((0, 1), weight=1)
        self.step_button = customtkinter.CTkButton(button_frame, text="Step", height=40,
                                                   font=customtkinter.CTkFont(size=16), fg_color="#494949",
                                                   hover_color="#333333", command=self.process_step)
        self.step_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        self.bake_button = customtkinter.CTkButton(button_frame, text="🏭 Bake Recipe!", height=40,
                                                   font=customtkinter.CTkFont(size=16, weight="bold"),
                                                   command=self.bake_recipe)
        self.bake_button.grid(row=0, column=1, padx=(5, 0), sticky="ew")

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

    def copy_output(self):
        content = self.output_textbox.get("1.0", "end-1c")
        if content:
            pyperclip.copy(content)
            self.status_bar.configure(text="Output copied to clipboard.", text_color="gray70")
        else:
            self.app.show_toast("Warning", "Output is empty.", toast_type="warning")

    def open_from_file(self):
        filepath = filedialog.askopenfilename(title="Open Text File",
                                              filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if not filepath: return
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.input_textbox.delete("1.0", "end");
                self.input_textbox.insert("1.0", f.read())
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

    # --- Methods to be implemented by child classes ---
    def execute_operation(self, operation_name, input_data, step_frame):
        raise NotImplementedError("This method must be implemented by a subclass")

    def create_operations_sidebar(self):
        raise NotImplementedError("This method must be implemented by a subclass")

    def load_recipe(self):
        raise NotImplementedError("This method must be implemented by a subclass")