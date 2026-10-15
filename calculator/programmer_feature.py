# calculator/programmer_feature.py
# Adds the Prog button (and Ctrl+P) to the calculator. Like the other
# features, it is a "mixin": a small class that adds one feature.

from __future__ import annotations

import tkinter as tk

from .programmer_window import ProgrammerWindow
from .storage import save_settings
from .themes import FONT_NAME


class ProgrammerMixin:
    """Adds a Prog button to the scientific panel."""

    modern_widgets = False    # app.py sets this to True for the CustomTkinter look
    programmer_window = None  # the open Programmer window, if any

    def create_buttons(self):
        super().create_buttons()
        self.add_programmer_button()
        for sequence in ("<Control-p>", "<Control-P>"):
            self.root.bind(sequence, self.open_programmer)

    def add_programmer_button(self):
        """A wide grey button in the scientific panel, under the Units button."""
        if self.modern_widgets:
            import customtkinter as ctk
            from .modern_ui import pair

            button = ctk.CTkButton(
                self.sci_frame,
                text="Prog",
                font=(FONT_NAME, 21),
                width=40,
                height=40,
                corner_radius=12,
                border_width=0,
                fg_color=pair("function", "bg"),
                hover_color=pair("function", "active"),
                text_color=pair("function", "fg"),
                command=self.open_programmer,
            )
        else:
            button = tk.Button(
                self.sci_frame,
                text="Prog",
                font=(FONT_NAME, 14),
                width=5,
                relief="flat",
                bd=0,
                cursor="hand2",
                command=self.open_programmer,
            )
            self.buttons.append((button, "function"))   # the classic theme recolors these
            button.bind("<Enter>", lambda event, b=button: self.on_hover(b, "function", True))
            button.bind("<Leave>", lambda event, b=button: self.on_hover(b, "function", False))

        self.sci_frame.rowconfigure(7, weight=1, uniform="row")
        button.grid(row=7, column=0, columnspan=2, sticky="nsew", padx=4, pady=4)

    def open_programmer(self, event=None):
        """Open Programmer mode (or bring it to the front if it is open)."""
        if self.programmer_window is not None and self.programmer_window.exists():
            self.programmer_window.show()
            return "break"

        self.programmer_window = ProgrammerWindow(
            self.root,
            self.theme_name,
            state=self.settings.get("programmer"),
            on_change=self.remember_programmer,
            on_use=self.use_programmer_value,
            get_value=self.calculator_whole_number,
        )
        return "break"

    def remember_programmer(self, state: dict):
        """Keep the base, word size and signed setting for next time."""
        self.settings["programmer"] = state
        save_settings(self.settings)

    def use_programmer_value(self, text: str):
        """Put a number from Programmer mode on the calculator's screen."""
        if hasattr(self, "insert_number"):
            self.insert_number(text)             # provided by the math feature
        else:
            self.expression = text
            self.just_calculated = True
            self.update_display()

    def calculator_whole_number(self):
        """The calculator's current value if it is a whole number, otherwise None."""
        value = self.current_value()
        if value is None or value != int(value):
            return None
        return int(value)

    def apply_theme(self):
        super().apply_theme()
        if self.programmer_window is not None and self.programmer_window.exists():
            self.programmer_window.set_theme(self.theme_name)