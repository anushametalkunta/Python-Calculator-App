# calculator/ui.py
# The calculator window: buttons, display, memory, history window,
# keyboard shortcuts, copy and paste. The math lives in logic.py,
# saving lives in storage.py and the colors live in themes.py.

from __future__ import annotations

import re
import tkinter as tk

from .input_cleaner import clean_pasted_text
from .logic import (
    CalcError,
    apply_function,
    apply_percent,
    calculate,
    evaluate,
    find_last_number,
    format_number,
)
from .storage import (
    MAX_HISTORY,
    load_history,
    load_settings,
    save_history,
    save_settings,
)
from .themes import FONT_NAME, THEMES

OPERATORS = "+-×÷^"

WINDOW_HEIGHT = 630       # the height we would like
BASIC_WIDTH = 320         # width without the scientific panel
SCIENTIFIC_WIDTH = 480    # width with the scientific panel


# ---------------------------------------------------------------------------
# Buttons and colors
# ---------------------------------------------------------------------------

# Buttons that work on the last number: label -> function name in calculator_logic.py
SCIENTIFIC = {
    "√": "sqrt",
    "x²": "square",
    "1/x": "reciprocal",
    "±": "negate",
}

# Scientific panel buttons: label -> text added to the calculation
SCI_TOKENS = {
    "sin": "sin(",
    "cos": "cos(",
    "tan": "tan(",
    "log": "log(",
    "ln": "ln(",
    "xʸ": "^",
    "(": "(",
    ")": ")",
    "π": "π",
    "e": "e",
}

MEMORY_BUTTONS = ("MC", "MR", "M+", "M-")

# Pieces that backspace removes in one go
FUNCTION_TOKENS = ("sin(", "cos(", "tan(", "log(", "ln(")

MEMORY_LAYOUT = [
    ["MC", "MR", "M+", "M-"],
]

BUTTON_LAYOUT = [
    ["√", "x²", "1/x", "±"],
    ["C", "⌫", "%", "÷"],
    ["7", "8", "9", "×"],
    ["4", "5", "6", "-"],
    ["1", "2", "3", "+"],
    ["0", ".", "="],
]

SCI_LAYOUT = [
    ["sin", "cos"],
    ["tan", "log"],
    ["ln", "xʸ"],
    ["(", ")"],
    ["π", "e"],
]


class CalculatorApp:
    """The calculator window and everything inside it."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Calculator")
        self.root.geometry(f"{BASIC_WIDTH}x{self.fit_height()}+120+8")
        self.root.resizable(False, False)

        # Variables that remember what is happening
        self.expression = ""
        self.just_calculated = False
        self.sci_visible = False
        self.buttons = []
        self.history = load_history()   # loaded from the file (empty the first time)
        self.history_window = None
        self.history_listbox = None

        # Memory (the M+ M- MR MC buttons)
        self.memory = 0.0

        # For the short messages that appear on the small line
        self.flash_job = None
        self.flash_backup = ""
        self.flash_text = ""

        # Settings: load the theme you used last time
        self.settings = load_settings()
        saved_theme = self.settings.get("theme")
        if isinstance(saved_theme, str) and saved_theme in THEMES:
            self.theme_name = saved_theme
        else:
            self.theme_name = "light"

        # Tkinter variables: when they change, the labels on screen change
        self.display_var = tk.StringVar(value="0")  # the big line
        self.sub_var = tk.StringVar(value="")       # the small line above it

        self.create_toggle()
        self.create_display()
        self.create_buttons()
        self.apply_theme()

        self.root.bind("<Key>", self.on_key_press)
        for sequence in ("<Control-c>", "<Control-C>"):
            self.root.bind(sequence, self.copy_result)
        for sequence in ("<Control-v>", "<Control-V>"):
            self.root.bind(sequence, self.paste_text)

    # ----- building the window -----

    def fit_height(self) -> int:
        """A window height that fits this screen (so the bottom row is never hidden)."""
        available = self.root.winfo_screenheight() - 90   # leave room for the taskbar
        return max(480, min(WINDOW_HEIGHT, available))


    def create_toggle(self):
        """Top bar: History (left), Scientific (middle), theme button (right)."""
        self.top_bar = tk.Frame(self.root)
        self.top_bar.pack(fill="x", padx=10, pady=(8, 0))

        self.toggle_button = tk.Button(
            self.top_bar,
            font=(FONT_NAME, 10),
            relief="flat",
            bd=0,
            cursor="hand2",
            takefocus=0,
            command=self.toggle_theme,
        )
        self.toggle_button.pack(side="right")

        self.history_button = tk.Button(
            self.top_bar,
            text="History",
            font=(FONT_NAME, 10),
            relief="flat",
            bd=0,
            cursor="hand2",
            takefocus=0,
            command=self.show_history,
        )
        self.history_button.pack(side="left")

        self.sci_toggle_button = tk.Button(
            self.top_bar,
            text="Scientific",
            font=(FONT_NAME, 10),
            relief="flat",
            bd=0,
            cursor="hand2",
            takefocus=0,
            command=self.toggle_scientific,
        )
        self.sci_toggle_button.pack(side="left", padx=14)

    def create_display(self):
        """The screen: a small line on top and the big line below it."""
        self.display_frame = tk.Frame(self.root)
        self.display_frame.pack(fill="x", padx=10, pady=(6, 5))

        self.sub_display = tk.Label(
            self.display_frame,
            textvariable=self.sub_var,
            anchor="e",
            font=(FONT_NAME, 12),
            padx=15,
        )
        self.sub_display.pack(fill="x", pady=(12, 0))

        self.display = tk.Label(
            self.display_frame,
            textvariable=self.display_var,
            anchor="e",
            font=(FONT_NAME, 32),
            padx=15,
            pady=8,
        )
        self.display.pack(fill="x")

        # A small "M" in the corner that shows when something is in memory
        self.memory_label = tk.Label(
            self.display_frame, text="", font=(FONT_NAME, 10, "bold")
        )
        self.memory_label.place(x=14, y=10)

    def create_buttons(self):
        """Make the memory row, the main button grid and the (hidden) scientific panel."""
        self.memory_frame = tk.Frame(self.root)
        self.memory_frame.pack(fill="x", padx=6)

        self.body = tk.Frame(self.root)
        self.body.pack(fill="both", expand=True)

        self.sci_frame = tk.Frame(self.body)

        self.button_frame = tk.Frame(self.body)
        self.button_frame.pack(side="left", fill="both", expand=True, padx=6, pady=6)

        self.make_grid(self.memory_frame, MEMORY_LAYOUT, columns=4, font_size=11, width=0)
        self.make_grid(self.sci_frame, SCI_LAYOUT, columns=2, font_size=14, width=5)
        self.make_grid(self.button_frame, BUTTON_LAYOUT, columns=4, font_size=16, width=0)

    def make_grid(self, parent, layout, columns, font_size, width):
        """Create a grid of buttons inside 'parent' from a list of rows."""
        for column in range(columns):
            parent.columnconfigure(column, weight=1, uniform="col")
        for row in range(len(layout)):
            parent.rowconfigure(row, weight=1, uniform="row")

        for row_index, row in enumerate(layout):
            column = 0
            for text in row:
                span = 2 if text == "0" else 1

                button = tk.Button(
                    parent,
                    text=text,
                    font=(FONT_NAME, font_size),
                    width=width,
                    relief="flat",
                    bd=0,
                    cursor="hand2",
                    command=lambda value=text: self.on_button_click(value),
                )
                button.grid(
                    row=row_index, column=column, columnspan=span,
                    sticky="nsew", padx=4, pady=4,
                )
                kind = self.pick_kind(text)
                self.buttons.append((button, kind))
                button.bind("<Enter>", lambda event, b=button, k=kind: self.on_hover(b, k, True))
                button.bind("<Leave>", lambda event, b=button, k=kind: self.on_hover(b, k, False))
                column += span

    def pick_kind(self, text):
        """Decide which color group a button belongs to."""
        if text == "=":
            return "equals"
        if text in OPERATORS:
            return "operator"
        if text in ("C", "⌫", "%") or text in SCIENTIFIC or text in SCI_TOKENS \
                or text in MEMORY_BUTTONS:
            return "function"
        return "number"

    # ----- colors and themes -----

    def apply_theme(self):
        """Paint every part of the calculator with the current theme's colors."""
        theme = THEMES[self.theme_name]

        self.root.configure(bg=theme["window_bg"])
        self.top_bar.configure(bg=theme["window_bg"])
        self.memory_frame.configure(bg=theme["window_bg"])
        self.body.configure(bg=theme["window_bg"])
        self.sci_frame.configure(bg=theme["window_bg"])
        self.button_frame.configure(bg=theme["window_bg"])

        self.display_frame.configure(bg=theme["display_bg"])
        self.sub_display.configure(bg=theme["display_bg"], fg=theme["sub_fg"])
        self.display.configure(bg=theme["display_bg"], fg=theme["display_fg"])
        self.memory_label.configure(bg=theme["display_bg"], fg=theme["sub_fg"])

        self.toggle_button.configure(
            text=theme["toggle_text"],
            bg=theme["window_bg"],
            fg=theme["display_fg"],
            activebackground=theme["window_bg"],
            activeforeground=theme["display_fg"],
        )

        for small_button in (self.history_button, self.sci_toggle_button):
            small_button.configure(
                bg=theme["window_bg"],
                fg=theme["display_fg"],
                activebackground=theme["window_bg"],
                activeforeground=theme["display_fg"],
            )

        if self.history_window is not None and self.history_window.winfo_exists():
            self.history_window.configure(bg=theme["window_bg"])
            self.history_listbox.configure(
                bg=theme["display_bg"], fg=theme["display_fg"]
            )

        for button, kind in self.buttons:
            colors = theme[kind]
            button.configure(
                bg=colors["bg"],
                fg=colors["fg"],
                activebackground=colors["active"],
                activeforeground=colors["fg"],
            )

    def toggle_theme(self):
        """Switch between light and dark mode, and remember the choice."""
        self.theme_name = "dark" if self.theme_name == "light" else "light"
        self.apply_theme()
        self.settings["theme"] = self.theme_name
        save_settings(self.settings)

    def toggle_scientific(self):
        """Show or hide the scientific panel."""
        if self.sci_visible:
            self.sci_frame.pack_forget()
            self.root.geometry(f"{BASIC_WIDTH}x{self.fit_height()}")
            self.sci_toggle_button.configure(text="Scientific")
        else:
            self.sci_frame.pack(
                side="left", fill="y", padx=(6, 0), pady=6, before=self.button_frame
            )
            self.root.geometry(f"{SCIENTIFIC_WIDTH}x{self.fit_height()}")
            self.sci_toggle_button.configure(text="Basic")
        self.sci_visible = not self.sci_visible

    def on_hover(self, button, kind, entering):
        """Change a button's shade when the mouse enters or leaves it."""
        colors = THEMES[self.theme_name][kind]
        if entering:
            button.configure(bg=colors["active"])
        else:
            button.configure(bg=colors["bg"])

    # ----- the display -----

    def update_display(self):
        """Show the current text on the big line."""
        text = self.expression if self.expression != "" else "0"
        self.display_var.set(text)

        size = 32 if len(text) <= 10 else 20
        self.display.config(font=(FONT_NAME, size))

    def set_sub_display(self, text):
        """Show text on the small line above the big one."""
        self.sub_var.set(text)

        size = 12 if len(text) <= 28 else 9
        self.sub_display.config(font=(FONT_NAME, size))

    def flash_message(self, message):
        """Show a short message on the small line, then put the old text back."""
        if self.flash_job is not None:
            self.root.after_cancel(self.flash_job)
            # If the line changed while the message was showing, keep the new text
            if self.sub_var.get() != self.flash_text:
                self.flash_backup = self.sub_var.get()
        else:
            self.flash_backup = self.sub_var.get()

        self.flash_text = message
        self.set_sub_display(message)
        self.flash_job = self.root.after(1200, self.end_flash)

    def end_flash(self):
        """Put the small line back to what it was before the message."""
        if self.sub_var.get() == self.flash_text:
            self.set_sub_display(self.flash_backup)
        self.flash_job = None

    def show_error(self, message, sub_text=""):
        """Show an error message on the screen and reset the calculator."""
        self.display_var.set(message)
        self.display.config(font=(FONT_NAME, 20))
        self.set_sub_display(sub_text)
        self.expression = ""
        self.just_calculated = False

    # ----- button clicks -----

    def on_button_click(self, text):
        """Runs every time a button is clicked."""
        if text == "C":
            self.expression = ""
            self.just_calculated = False
            self.set_sub_display("")

        elif text == "⌫":
            self.press_backspace()

        elif text == "=":
            self.press_equals()
            return

        elif text == "%":
            self.expression = apply_percent(self.expression)
            self.just_calculated = False

        elif text in MEMORY_BUTTONS:
            self.press_memory(text)
            return

        elif text in SCIENTIFIC:
            self.press_function(text)
            return

        elif text in SCI_TOKENS:
            self.press_scientific(text)

        elif text in OPERATORS:
            self.add_operator(text)

        else:
            self.add_digit(text)

        self.update_display()

    def press_backspace(self):
        """Delete the last character (or a whole function name like 'sin(')."""
        self.just_calculated = False
        for name in FUNCTION_TOKENS:
            if self.expression.endswith(name):
                self.expression = self.expression[:-len(name)]
                return
        self.expression = self.expression[:-1]

    def add_digit(self, text):
        """Add a number or decimal point to the expression."""
        if self.just_calculated:
            self.expression = ""
            self.just_calculated = False

        if text == ".":
            current_number = re.split(r"[+\-×÷^()πe]", self.expression)[-1]
            if "." in current_number:
                return

        if self.expression[-1:] in (")", "π", "e"):
            self.expression += "×"

        self.expression += text

    def add_operator(self, text):
        """Add + - × ÷ ^ to the expression."""
        self.just_calculated = False

        if self.expression == "":
            if text == "-":
                self.expression = "-"
            return

        last = self.expression[-1]

        if last == "(":
            if text == "-":
                self.expression += "-"
            return

        if text == "-" and last in "×÷^":
            self.expression += text
            return

        base = self.expression.rstrip(OPERATORS)
        if base == "" or base.endswith("("):
            self.expression = base
        else:
            self.expression = base + text

    def press_scientific(self, label):
        """Handle the buttons from the scientific panel."""
        token = SCI_TOKENS[label]

        if token == "^":
            self.add_operator("^")
        elif token == ")":
            self.add_close_bracket()
        else:
            self.add_open_token(token)

    def add_open_token(self, token):
        """Add sin( cos( tan( log( ln( ( or π or e."""
        if self.just_calculated:
            self.expression = ""
            self.just_calculated = False

        last = self.expression[-1:]
        if last != "" and (last.isdigit() or last in ")πe."):
            self.expression += "×"

        self.expression += token

    def add_close_bracket(self):
        """Add ) only when it makes sense."""
        if self.just_calculated:
            return
        if self.expression.count("(") <= self.expression.count(")"):
            return
        if self.expression[-1] in OPERATORS or self.expression[-1] == "(":
            return
        self.expression += ")"

    def press_function(self, text):
        """Apply √, x², 1/x or ± to the last number."""
        if self.expression == "":
            return

        new_expression, error = apply_function(self.expression, SCIENTIFIC[text])

        if error is not None:
            self.show_error(error)
            return

        if new_expression == self.expression:
            return

        self.expression = new_expression
        self.just_calculated = re.search(r"[+\-×÷^()πe]", new_expression[1:]) is None
        self.update_display()

    def press_equals(self):
        """Calculate the answer, show it, and save it to the history file."""
        if self.expression == "":
            return

        result = calculate(self.expression)
        full_calculation = f"{self.expression} ="

        if result[0].isdigit() or result[0] == "-":
            self.history.append(f"{self.expression} = {result}")
            self.history = self.history[-MAX_HISTORY:]
            save_history(self.history)
            if self.history_window is not None and self.history_window.winfo_exists():
                self.refresh_history()
            self.set_sub_display(full_calculation)
            self.expression = result
            self.just_calculated = True
            self.update_display()
        else:
            self.show_error(result, full_calculation)

    # ----- memory -----

    def current_value(self):
        """The number on the screen, or None if it is empty or not a valid calculation."""
        if self.expression == "":
            return None
        try:
            return evaluate(self.expression)
        except CalcError:
            return None

    def update_memory_indicator(self):
        """Show a small 'M' in the corner when the memory holds something."""
        self.memory_label.configure(text="M" if self.memory != 0 else "")

    def press_memory(self, text):
        """Handle MC (clear), MR (recall), M+ (add) and M- (subtract)."""
        if text == "MC":
            self.memory = 0.0
            self.update_memory_indicator()
            self.flash_message("Memory cleared")
            return

        if text == "MR":
            self.recall_memory()
            return

        value = self.current_value()
        if value is None:
            self.flash_message("Nothing to store")
            return

        if text == "M+":
            self.memory += value
        else:
            self.memory -= value
        self.memory = round(self.memory, 10)

        self.update_memory_indicator()
        self.flash_message(f"Memory: {format_number(self.memory)}")

    def recall_memory(self):
        """Put the stored number on the screen, like typing it."""
        text = format_number(self.memory)

        if self.just_calculated:
            self.expression = ""
            self.just_calculated = False

        found = find_last_number(self.expression)
        if found is not None:
            # Replace the number you are in the middle of typing
            self.expression = self.expression[:found[0]] + text
        else:
            if self.expression[-1:] in (")", "π", "e"):
                self.expression += "×"
            self.expression += text

        self.just_calculated = re.search(r"[+\-×÷^()πe]", self.expression[1:]) is None
        self.update_display()

    # ----- copy and paste -----

    def copy_result(self, event=None):
        """Ctrl+C: copy the answer (or the text on screen if it cannot be calculated)."""
        if self.expression == "":
            return "break"

        value = self.current_value()
        text = format_number(value) if value is not None else self.expression

        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.flash_message("Copied")
        return "break"

    def paste_text(self, event=None):
        """Ctrl+V: paste a number or calculation from the clipboard."""
        try:
            raw_text = self.root.clipboard_get()
        except tk.TclError:
            self.flash_message("Clipboard is empty")
            return "break"

        text = clean_pasted_text(raw_text)
        if text == "":
            self.flash_message("Can't paste that")
            return "break"

        if self.just_calculated:
            self.expression = ""
            self.just_calculated = False

        # (2+3) followed by 4 means (2+3)×4
        if self.expression[-1:] in (")", "π", "e") and text[0] not in "+-×÷^)":
            self.expression += "×"

        self.expression += text
        self.update_display()
        return "break"

    # ----- keyboard -----

    def on_key_press(self, event):
        """Runs every time you press a key on the keyboard."""
        key_map = {
            "*": "×",
            "/": "÷",
            "x": "×",
            "=": "=",
            "c": "C",
            "C": "C",
            "^": "xʸ",
            "(": "(",
            ")": ")",
            "p": "π",
            "e": "e",
        }

        if event.keysym in ("Return", "KP_Enter"):
            self.on_button_click("=")
        elif event.keysym == "BackSpace":
            self.on_button_click("⌫")
        elif event.keysym == "Escape":
            self.on_button_click("C")
        elif event.char in key_map:
            self.on_button_click(key_map[event.char])
        elif event.char != "" and event.char in "0123456789.+-%":
            self.on_button_click(event.char)

    # ----- history window -----

    def show_history(self):
        """Open the history window, or bring it forward if already open."""
        if self.history_window is not None and self.history_window.winfo_exists():
            self.history_window.lift()
            return

        self.history_window = tk.Toplevel(self.root)
        self.history_window.title("History")
        self.history_window.geometry("260x320")

        self.history_listbox = tk.Listbox(
            self.history_window,
            font=(FONT_NAME, 12),
            relief="flat",
            bd=0,
            highlightthickness=0,
            activestyle="none",
        )
        self.history_listbox.pack(fill="both", expand=True, padx=8, pady=8)
        self.history_listbox.bind("<<ListboxSelect>>", self.use_history_item)

        clear_button = tk.Button(
            self.history_window,
            text="Clear history",
            relief="flat",
            command=self.clear_history,
        )
        clear_button.pack(pady=(0, 8))

        self.refresh_history()
        self.apply_theme()

    def refresh_history(self):
        """Fill the history list with saved calculations (newest first)."""
        self.history_listbox.delete(0, "end")
        for entry in reversed(self.history):
            self.history_listbox.insert("end", entry)

    def use_history_item(self, event):
        """When you click a history entry, show it on the calculator."""
        selection = self.history_listbox.curselection()
        if not selection:
            return
        entry = self.history_listbox.get(selection[0])
        calculation, answer = entry.rsplit(" = ", 1)
        self.set_sub_display(f"{calculation} =")
        self.expression = answer
        self.just_calculated = True
        self.update_display()

    def clear_history(self):
        """Delete all saved calculations, including the ones in the file."""
        self.history = []
        save_history(self.history)
        self.refresh_history()