# calculator/programmer_window.py
# The Programmer mode window. The math is in programmer.py; this file only
# shows it and reacts to what you type and click.

from __future__ import annotations

import tkinter as tk
from typing import Callable

from .logic import CalcError
from .programmer import (
    BASE_NUMBERS,
    WORD_SIZES,
    Representation,
    describe,
    evaluate_int,
    format_binary,
    format_hex,
    format_octal,
    represent,
)
from .themes import FONT_NAME, THEMES

MONO_FONT = "Consolas"
HINT = "Click a result to copy it. Try: 0xFF & 0b1010, 1 << 4, ~0, 255 xor 15"

# (button text, text inserted in the expression)
OPERATOR_BUTTONS = [
    ("AND", " & "), ("OR", " | "), ("XOR", " ^ "), ("NOT", "~"),
    ("<<", " << "), (">>", " >> "), ("MOD", " % "), ("(", "("), (")", ")"),
]


class ProgrammerWindow:
    """A window that shows a whole number in binary, octal, decimal and hex."""

    def __init__(
        self,
        master,
        theme_name: str,
        state: dict | None = None,
        on_change: Callable[[dict], None] | None = None,
        on_use: Callable[[str], None] | None = None,
        get_value: Callable[[], int | None] | None = None,
    ):
        self.on_change = on_change
        self.on_use = on_use
        self.get_value = get_value
        self.theme = THEMES[theme_name]
        self.current: Representation | None = None    # the number being shown

        # Start with the settings used last time
        state = state if isinstance(state, dict) else {}
        base = state.get("base")
        self.base = base if isinstance(base, str) and base in BASE_NUMBERS else "DEC"
        bits = state.get("bits")
        self.bits = bits if bits in WORD_SIZES else 64
        signed = state.get("signed")
        self.signed = signed if isinstance(signed, bool) else True

        self.window = tk.Toplevel(master)
        self.window.title("Programmer")
        self.window.geometry("580x660+660+30")
        self.window.minsize(540, 620)

        self.expression_var = tk.StringVar(value="255")
        self.dec_var = tk.StringVar(value="")
        self.hex_var = tk.StringVar(value="")
        self.oct_var = tk.StringVar(value="")
        self.bin_var = tk.StringVar(value="")
        self.note_var = tk.StringVar(value="")
        self.status_var = tk.StringVar(value=HINT)

        self.frames = []
        self.labels = []
        self.sub_labels = []
        self.value_labels = []
        self.plain_buttons = []      # always the grey style
        self.base_buttons = {}       # highlighted when chosen
        self.bits_buttons = {}
        self.signed_button = None

        self.build()
        self.set_theme(theme_name)
        self.expression_var.trace_add("write", self.on_expression_changed)
        self.update_results()

    # ----- building the window -----

    def make_button(self, parent, text, command, padx=10):
        button = tk.Button(
            parent, text=text, font=(FONT_NAME, 10), relief="flat", bd=0,
            padx=padx, pady=3, cursor="hand2", command=command,
        )
        return button

    def build(self):
        body = tk.Frame(self.window)
        body.pack(fill="both", expand=True, padx=20, pady=16)
        body.columnconfigure(1, weight=1)
        self.frames.append(body)

        def add_label(text, row, sticky="w"):
            label = tk.Label(body, text=text, font=(FONT_NAME, 11), anchor="w")
            label.grid(row=row, column=0, sticky=sticky, pady=6, padx=(0, 12))
            self.labels.append(label)

        # The expression
        add_label("Expression", 0)
        self.entry = tk.Entry(
            body, textvariable=self.expression_var, font=(MONO_FONT, 16),
            relief="flat", highlightthickness=1,
        )
        self.entry.grid(row=0, column=1, sticky="ew", pady=6, ipady=6)

        # Input base
        add_label("Input", 1)
        row = tk.Frame(body)
        row.grid(row=1, column=1, sticky="w", pady=6)
        self.frames.append(row)
        for name in BASE_NUMBERS:
            button = self.make_button(row, name, lambda n=name: self.choose_base(n), padx=12)
            button.pack(side="left", padx=(0, 6))
            self.base_buttons[name] = button

        # Word size and signed / unsigned
        add_label("Word", 2)
        row = tk.Frame(body)
        row.grid(row=2, column=1, sticky="w", pady=6)
        self.frames.append(row)
        for size in WORD_SIZES:
            button = self.make_button(row, f"{size}-bit", lambda s=size: self.choose_bits(s), padx=10)
            button.pack(side="left", padx=(0, 6))
            self.bits_buttons[size] = button
        self.signed_button = self.make_button(row, "Signed", self.toggle_signed, padx=12)
        self.signed_button.pack(side="left", padx=(12, 0))

        # Operator buttons
        row = tk.Frame(body)
        row.grid(row=3, column=0, columnspan=2, sticky="w", pady=(8, 10))
        self.frames.append(row)
        for text, inserted in OPERATOR_BUTTONS:
            button = self.make_button(row, text, lambda t=inserted: self.insert_text(t), padx=9)
            button.pack(side="left", padx=(0, 5))
            self.plain_buttons.append(button)

        # The four results
        results = [("DEC", self.dec_var), ("HEX", self.hex_var),
                   ("OCT", self.oct_var), ("BIN", self.bin_var)]
        for index, (name, variable) in enumerate(results):
            add_label(name, 4 + index, sticky="nw")
            label = tk.Label(
                body, textvariable=variable, font=(MONO_FONT, 14), anchor="w",
                justify="left", padx=10, pady=6, cursor="hand2",
            )
            label.grid(row=4 + index, column=1, sticky="ew", pady=4)
            label.bind("<Button-1>", lambda event, n=name, v=variable: self.copy_value(n, v))
            self.value_labels.append(label)

        self.note_label = tk.Label(
            body, textvariable=self.note_var, font=(FONT_NAME, 10), anchor="w", justify="left",
        )
        self.note_label.grid(row=8, column=0, columnspan=2, sticky="w", pady=(8, 4))
        self.sub_labels.append(self.note_label)

        row = tk.Frame(body)
        row.grid(row=9, column=0, columnspan=2, sticky="w", pady=(8, 4))
        self.frames.append(row)
        self.from_button = self.make_button(row, "From calculator", self.load_from_calculator, padx=14)
        self.from_button.pack(side="left")
        self.plain_buttons.append(self.from_button)
        self.use_button = self.make_button(row, "Use in calculator", self.use_result, padx=14)
        self.use_button.pack(side="left", padx=8)

        self.status_label = tk.Label(
            body, textvariable=self.status_var, font=(FONT_NAME, 10), anchor="w", justify="left",
        )
        self.status_label.grid(row=10, column=0, columnspan=2, sticky="w", pady=(8, 0))
        self.sub_labels.append(self.status_label)

    # ----- window control -----

    def exists(self) -> bool:
        return bool(self.window.winfo_exists())

    def show(self):
        self.window.lift()
        self.window.focus_force()

    def style_button(self, button, selected: bool):
        """Blue when chosen, grey otherwise."""
        colors = self.theme["equals"] if selected else self.theme["function"]
        button.configure(
            bg=colors["bg"], fg=colors["fg"],
            activebackground=colors["active"], activeforeground=colors["fg"],
        )

    def refresh_choices(self):
        """Highlight the chosen base and word size."""
        for name, button in self.base_buttons.items():
            self.style_button(button, name == self.base)
        for size, button in self.bits_buttons.items():
            self.style_button(button, size == self.bits)
        self.signed_button.configure(text="Signed" if self.signed else "Unsigned")
        self.style_button(self.signed_button, self.signed)

    def set_theme(self, theme_name: str):
        """Paint the window with the light or dark colors."""
        theme = THEMES[theme_name]
        self.theme = theme

        self.window.configure(bg=theme["window_bg"])
        for frame in self.frames:
            frame.configure(bg=theme["window_bg"])
        for label in self.labels:
            label.configure(bg=theme["window_bg"], fg=theme["display_fg"])
        for label in self.sub_labels:
            label.configure(bg=theme["window_bg"], fg=theme["sub_fg"])
        for label in self.value_labels:
            label.configure(bg=theme["display_bg"], fg=theme["display_fg"])

        self.entry.configure(
            bg=theme["display_bg"],
            fg=theme["display_fg"],
            insertbackground=theme["display_fg"],
            highlightbackground=theme["number"]["active"],
            highlightcolor=theme["equals"]["bg"],
        )
        for button in self.plain_buttons:
            self.style_button(button, False)
        self.use_button.configure(
            bg=theme["operator"]["bg"],
            fg=theme["operator"]["fg"],
            activebackground=theme["operator"]["active"],
            activeforeground=theme["operator"]["fg"],
        )
        self.refresh_choices()

    # ----- choosing -----

    def current_state(self) -> dict:
        return {"base": self.base, "bits": self.bits, "signed": self.signed}

    def save_state(self):
        if self.on_change is not None:
            self.on_change(self.current_state())

    def text_in_base(self, rep: Representation, base: str) -> str:
        """The number as text you could type in a given base."""
        if base == "DEC":
            return str(rep.shown)
        if base == "HEX":
            return format_hex(rep)
        if base == "OCT":
            return format_octal(rep)
        return format(rep.wrapped, "b")           # no leading zeros

    def choose_base(self, name: str):
        """Change the input base. The number on screen is rewritten in the new base."""
        rep = self.current
        self.base = name
        self.refresh_choices()
        if rep is not None:
            self.expression_var.set(self.text_in_base(rep, name))   # this also updates the results
        else:
            self.update_results()
        self.save_state()

    def choose_bits(self, size: int):
        self.bits = size
        self.refresh_choices()
        self.update_results()
        self.save_state()

    def toggle_signed(self):
        self.signed = not self.signed
        self.refresh_choices()
        self.update_results()
        self.save_state()

    def insert_text(self, text: str):
        """Put an operator into the expression at the cursor."""
        current = self.expression_var.get()
        position = self.entry.index("insert")
        self.expression_var.set(current[:position] + text + current[position:])
        self.entry.icursor(position + len(text))
        self.entry.focus_set()

    # ----- calculating -----

    def on_expression_changed(self, *args):
        self.update_results()

    def clear_results(self, placeholder: str = ""):
        self.current = None
        for variable in (self.dec_var, self.hex_var, self.oct_var, self.bin_var):
            variable.set(placeholder)
        self.note_var.set("")

    def update_results(self):
        """Work out the expression and show it in all four bases."""
        text = self.expression_var.get()
        if text.strip() == "":
            self.clear_results()
            self.status_var.set(HINT)
            return

        try:
            value = evaluate_int(text, BASE_NUMBERS[self.base])
        except CalcError as error:
            self.clear_results("—")
            self.status_var.set(str(error))
            return

        rep = represent(value, self.bits, self.signed)
        self.current = rep
        self.dec_var.set(str(rep.shown))
        self.hex_var.set(format_hex(rep))
        self.oct_var.set(format_octal(rep))
        self.bin_var.set(format_binary(rep))
        self.note_var.set(describe(rep))
        self.status_var.set(HINT)

    # ----- the buttons -----

    def copy_value(self, name: str, variable):
        """Click a result to copy it."""
        text = variable.get()
        if self.current is None or text in ("", "—"):
            self.status_var.set("Nothing to copy yet.")
            return
        if name == "BIN":
            text = text.replace("\n", " ")
        self.window.clipboard_clear()
        self.window.clipboard_append(text)
        self.status_var.set(f"Copied {name}: {text}")

    def use_result(self):
        """Send the decimal value to the calculator's screen."""
        if self.current is None:
            self.status_var.set("Nothing to send yet.")
            return
        if self.on_use is not None:
            self.on_use(str(self.current.shown))
            self.status_var.set("Sent to the calculator.")

    def load_from_calculator(self):
        """Bring the whole number from the calculator's screen into this window."""
        value = self.get_value() if self.get_value is not None else None
        if value is None:
            self.status_var.set("The calculator does not hold a whole number right now.")
            return
        self.base = "DEC"
        self.refresh_choices()
        self.expression_var.set(str(value))
        self.save_state()