# calculator/unit_window.py
# The unit converter window. The math is in units.py; this file only
# shows it and reacts to what you type and click.

from __future__ import annotations

import tkinter as tk
from typing import Callable

from .logic import CalcError, format_number
from .themes import FONT_NAME, THEMES
from .units import (
    CATEGORY_NAMES,
    DEFAULT_UNITS,
    convert,
    format_result,
    parse_amount,
    ratio_text,
    units_for,
)


class UnitWindow:
    """A window that converts a number between units, live as you type."""

    def __init__(
        self,
        master,
        theme_name: str,
        state: dict | None = None,
        on_change: Callable[[dict], None] | None = None,
        on_use: Callable[[str], None] | None = None,
    ):
        self.on_change = on_change
        self.on_use = on_use
        self.theme = THEMES[theme_name]
        self.last_result = None             # the latest converted number (None if none)

        # Start with the category and units used last time
        state = state if isinstance(state, dict) else {}
        category = state.get("category")
        if category not in CATEGORY_NAMES:
            category = "Length"
        units = units_for(category)
        from_unit, to_unit = state.get("from"), state.get("to")
        default_from, default_to = DEFAULT_UNITS[category]
        if from_unit not in units:
            from_unit = default_from
        if to_unit not in units:
            to_unit = default_to

        self.window = tk.Toplevel(master)
        self.window.title("Unit converter")
        self.window.geometry("480x430+650+40")
        self.window.minsize(440, 400)

        self.category_var = tk.StringVar(value=category)
        self.from_var = tk.StringVar(value=from_unit)
        self.to_var = tk.StringVar(value=to_unit)
        self.amount_var = tk.StringVar(value="1")
        self.result_var = tk.StringVar(value="")
        self.note_var = tk.StringVar(value="")
        self.status_var = tk.StringVar(value="Type a number. Calculations like 1/4 work too.")

        self.frames = []
        self.labels = []
        self.sub_labels = []
        self.entries = []
        self.menus = []
        self.buttons = []

        self.build()
        self.refill_unit_menus()
        self.set_theme(theme_name)
        self.amount_var.trace_add("write", self.on_amount_changed)
        self.update_result()

    # ----- building the window -----

    def build(self):
        body = tk.Frame(self.window)
        body.pack(fill="both", expand=True, padx=20, pady=18)
        body.columnconfigure(1, weight=1)
        self.frames.append(body)

        def add_label(text, row):
            label = tk.Label(body, text=text, font=(FONT_NAME, 11), anchor="w")
            label.grid(row=row, column=0, sticky="w", pady=8, padx=(0, 12))
            self.labels.append(label)

        def add_menu(variable, values, row, column, span=1):
            menu = tk.OptionMenu(body, variable, *values)
            menu.configure(
                width=9, font=(FONT_NAME, 11), relief="flat",
                highlightthickness=0, bd=0, cursor="hand2",
            )
            menu.grid(row=row, column=column, columnspan=span, sticky="ew", pady=8, padx=(8, 0))
            self.menus.append(menu)
            return menu

        add_label("Category", 0)
        self.category_menu = add_menu(self.category_var, CATEGORY_NAMES, 0, 1, span=2)

        add_label("From", 1)
        self.amount_entry = tk.Entry(
            body, textvariable=self.amount_var, font=(FONT_NAME, 18),
            relief="flat", highlightthickness=1,
        )
        self.amount_entry.grid(row=1, column=1, sticky="ew", pady=8, ipady=6)
        self.entries.append(self.amount_entry)
        self.from_menu = add_menu(self.from_var, units_for(self.category_var.get()), 1, 2)

        self.swap_button = tk.Button(
            body, text="Swap units", font=(FONT_NAME, 10), relief="flat", bd=0,
            padx=12, pady=3, cursor="hand2", command=self.swap_units,
        )
        self.swap_button.grid(row=2, column=1, pady=2)
        self.buttons.append(self.swap_button)

        add_label("To", 3)
        self.result_label = tk.Label(
            body, textvariable=self.result_var, font=(FONT_NAME, 18),
            anchor="w", padx=10, pady=8,
        )
        self.result_label.grid(row=3, column=1, sticky="ew", pady=8)
        self.to_menu = add_menu(self.to_var, units_for(self.category_var.get()), 3, 2)

        self.note_label = tk.Label(body, textvariable=self.note_var, font=(FONT_NAME, 10), anchor="w")
        self.note_label.grid(row=4, column=0, columnspan=3, sticky="w", pady=(8, 4))
        self.sub_labels.append(self.note_label)

        buttons = tk.Frame(body)
        buttons.grid(row=5, column=0, columnspan=3, sticky="w", pady=(10, 4))
        self.frames.append(buttons)

        self.copy_button = tk.Button(
            buttons, text="Copy result", font=(FONT_NAME, 10), relief="flat", bd=0,
            padx=14, pady=4, cursor="hand2", command=self.copy_result,
        )
        self.copy_button.pack(side="left")
        self.buttons.append(self.copy_button)

        self.use_button = tk.Button(
            buttons, text="Use in calculator", font=(FONT_NAME, 10), relief="flat", bd=0,
            padx=14, pady=4, cursor="hand2", command=self.use_result,
        )
        self.use_button.pack(side="left", padx=8)

        self.status_label = tk.Label(body, textvariable=self.status_var, font=(FONT_NAME, 10), anchor="w")
        self.status_label.grid(row=6, column=0, columnspan=3, sticky="w", pady=(10, 0))
        self.sub_labels.append(self.status_label)

        self.amount_entry.bind("<Return>", self.use_result_if_ready)

    def fill_menu(self, menu_widget, values, handler):
        """Replace the items of a drop-down menu."""
        menu = menu_widget["menu"]
        menu.delete(0, "end")
        for value in values:
            menu.add_command(label=value, command=lambda v=value: handler(v))

    def refill_unit_menus(self):
        """Fill the three drop-downs: categories, and the units of the current category."""
        units = units_for(self.category_var.get())
        self.fill_menu(self.category_menu, CATEGORY_NAMES, self.choose_category)
        self.fill_menu(self.from_menu, units, self.choose_from)
        self.fill_menu(self.to_menu, units, self.choose_to)

    # ----- window control -----

    def exists(self) -> bool:
        return bool(self.window.winfo_exists())

    def show(self):
        self.window.lift()
        self.window.focus_force()

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
        self.result_label.configure(bg=theme["display_bg"], fg=theme["display_fg"])

        for entry in self.entries:
            entry.configure(
                bg=theme["display_bg"],
                fg=theme["display_fg"],
                insertbackground=theme["display_fg"],
                highlightbackground=theme["number"]["active"],
                highlightcolor=theme["equals"]["bg"],
            )
        for menu_button in self.menus:
            menu_button.configure(
                bg=theme["function"]["bg"],
                fg=theme["function"]["fg"],
                activebackground=theme["function"]["active"],
                activeforeground=theme["function"]["fg"],
            )
            menu_button["menu"].configure(
                bg=theme["display_bg"],
                fg=theme["display_fg"],
                activebackground=theme["equals"]["bg"],
                activeforeground="#ffffff",
                bd=0,
            )
        for button in self.buttons:
            button.configure(
                bg=theme["function"]["bg"],
                fg=theme["function"]["fg"],
                activebackground=theme["function"]["active"],
                activeforeground=theme["function"]["fg"],
            )
        self.use_button.configure(
            bg=theme["equals"]["bg"],
            fg=theme["equals"]["fg"],
            activebackground=theme["equals"]["active"],
            activeforeground=theme["equals"]["fg"],
        )

    # ----- choosing -----

    def current_state(self) -> dict:
        return {
            "category": self.category_var.get(),
            "from": self.from_var.get(),
            "to": self.to_var.get(),
        }

    def save_state(self):
        if self.on_change is not None:
            self.on_change(self.current_state())

    def choose_category(self, category: str):
        """A new category was picked: show its units and start with its default pair."""
        self.category_var.set(category)
        default_from, default_to = DEFAULT_UNITS[category]
        self.from_var.set(default_from)
        self.to_var.set(default_to)
        self.refill_unit_menus()
        self.update_result()
        self.save_state()

    def choose_from(self, unit: str):
        self.from_var.set(unit)
        self.update_result()
        self.save_state()

    def choose_to(self, unit: str):
        self.to_var.set(unit)
        self.update_result()
        self.save_state()

    def swap_units(self):
        """Exchange the 'from' and 'to' units."""
        from_unit, to_unit = self.from_var.get(), self.to_var.get()
        self.from_var.set(to_unit)
        self.to_var.set(from_unit)
        self.update_result()
        self.save_state()

    # ----- converting -----

    def on_amount_changed(self, *args):
        self.update_result()

    def update_result(self):
        """Convert the typed number and show the answer."""
        category = self.category_var.get()
        from_unit, to_unit = self.from_var.get(), self.to_var.get()
        self.note_var.set(ratio_text(category, from_unit, to_unit))

        text = self.amount_var.get().strip()
        if text == "":
            self.last_result = None
            self.result_var.set("")
            return

        try:
            result = convert(parse_amount(text), category, from_unit, to_unit)
        except CalcError as error:
            self.last_result = None
            self.result_var.set("—")
            self.status_var.set(str(error))
            return

        self.last_result = result
        self.result_var.set(format_result(result))
        self.status_var.set("Type a number. Calculations like 1/4 work too.")

    # ----- the buttons -----

    def copy_result(self):
        """Copy the converted number to the clipboard."""
        if self.last_result is None:
            self.status_var.set("Nothing to copy yet.")
            return
        self.window.clipboard_clear()
        self.window.clipboard_append(format_result(self.last_result))
        self.status_var.set("Copied to the clipboard.")

    def use_result(self):
        """Send the converted number to the calculator's screen."""
        if self.last_result is None:
            self.status_var.set("Nothing to send yet.")
            return
        if self.on_use is not None:
            self.on_use(format_number(self.last_result))
            self.status_var.set("Sent to the calculator.")

    def use_result_if_ready(self, event=None):
        self.use_result()