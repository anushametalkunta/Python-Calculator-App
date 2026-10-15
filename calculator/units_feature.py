# calculator/units_feature.py
# Adds the Units button (and Ctrl+U) to the calculator. Like the graph and
# math features, it is a "mixin": a small class that adds one feature.

from __future__ import annotations

import tkinter as tk

from .storage import save_settings
from .themes import FONT_NAME
from .unit_window import UnitWindow


class UnitsMixin:
    """Adds a Units button to the scientific panel."""

    modern_widgets = False    # app.py sets this to True for the CustomTkinter look
    units_window = None       # the open converter window, if any

    def create_buttons(self):
        super().create_buttons()
        self.add_units_button()
        for sequence in ("<Control-u>", "<Control-U>"):
            self.root.bind(sequence, self.open_units)

    def add_units_button(self):
        """A wide orange button in the scientific panel, under the Graph button."""
        if self.modern_widgets:
            import customtkinter as ctk
            from .modern_ui import pair

            button = ctk.CTkButton(
                self.sci_frame,
                text="Units",
                font=(FONT_NAME, 21),
                width=40,
                height=40,
                corner_radius=12,
                border_width=0,
                fg_color=pair("operator", "bg"),
                hover_color=pair("operator", "active"),
                text_color=pair("operator", "fg"),
                command=self.open_units,
            )
        else:
            button = tk.Button(
                self.sci_frame,
                text="Units",
                font=(FONT_NAME, 14),
                width=5,
                relief="flat",
                bd=0,
                cursor="hand2",
                command=self.open_units,
            )
            self.buttons.append((button, "operator"))   # the classic theme recolors these
            button.bind("<Enter>", lambda event, b=button: self.on_hover(b, "operator", True))
            button.bind("<Leave>", lambda event, b=button: self.on_hover(b, "operator", False))

        self.sci_frame.rowconfigure(6, weight=1, uniform="row")
        button.grid(row=6, column=0, columnspan=2, sticky="nsew", padx=4, pady=4)

    def open_units(self, event=None):
        """Open the unit converter (or bring it to the front if it is open)."""
        if self.units_window is not None and self.units_window.exists():
            self.units_window.show()
            return "break"

        self.units_window = UnitWindow(
            self.root,
            self.theme_name,
            state=self.settings.get("units"),
            on_change=self.remember_units,
            on_use=self.use_converted_value,
        )
        return "break"

    def remember_units(self, state: dict):
        """Keep the last category and units, so they are there next time."""
        self.settings["units"] = state
        save_settings(self.settings)

    def use_converted_value(self, text: str):
        """Put a converted number on the calculator's screen."""
        if hasattr(self, "insert_number"):
            self.insert_number(text)             # provided by the math feature
        else:
            self.expression = text
            self.just_calculated = True
            self.update_display()

    def apply_theme(self):
        super().apply_theme()
        if self.units_window is not None and self.units_window.exists():
            self.units_window.set_theme(self.theme_name)