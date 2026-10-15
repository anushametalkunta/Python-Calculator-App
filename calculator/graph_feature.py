# calculator/graph_feature.py
# Adds the Graph button (and Ctrl+G) to the calculator. It is a "mixin":
# a small class that adds one feature to whichever calculator it is mixed into.

from __future__ import annotations

import tkinter as tk

from .graph_window import DEFAULT_FORMULA, GraphWindow
from .storage import save_settings
from .themes import FONT_NAME


class GraphMixin:
    """Adds a Graph button to the scientific panel."""

    modern_widgets = False    # app.py sets this to True for the CustomTkinter look
    graph_window = None       # the open graph window, if any

    def create_buttons(self):
        super().create_buttons()
        self.add_graph_button()
        for sequence in ("<Control-g>", "<Control-G>"):
            self.root.bind(sequence, self.open_graph)

    def add_graph_button(self):
        """A wide button under the scientific buttons."""
        if self.modern_widgets:
            import customtkinter as ctk
            from .modern_ui import pair

            button = ctk.CTkButton(
                self.sci_frame,
                text="Graph",
                font=(FONT_NAME, 21),
                width=40,
                height=40,
                corner_radius=12,
                border_width=0,
                fg_color=pair("equals", "bg"),
                hover_color=pair("equals", "active"),
                text_color=pair("equals", "fg"),
                command=self.open_graph,
            )
        else:
            button = tk.Button(
                self.sci_frame,
                text="Graph",
                font=(FONT_NAME, 14),
                width=5,
                relief="flat",
                bd=0,
                cursor="hand2",
                command=self.open_graph,
            )
            self.buttons.append((button, "equals"))   # the classic theme recolors these
            button.bind("<Enter>", lambda event, b=button: self.on_hover(b, "equals", True))
            button.bind("<Leave>", lambda event, b=button: self.on_hover(b, "equals", False))

        self.sci_frame.rowconfigure(5, weight=1, uniform="row")
        button.grid(row=5, column=0, columnspan=2, sticky="nsew", padx=4, pady=4)

    def open_graph(self, event=None):
        """Open the graph window (or bring it to the front if it is open)."""
        if self.graph_window is not None and self.graph_window.exists():
            self.graph_window.show()
            return "break"

        saved = self.settings.get("graph_formula")
        if not isinstance(saved, str) or not 0 < len(saved) <= 200:
            saved = DEFAULT_FORMULA

        self.graph_window = GraphWindow(
            self.root, self.theme_name, saved, on_plot=self.remember_formula
        )
        return "break"

    def remember_formula(self, formula: str):
        """Keep the last formula, so it is there next time."""
        self.settings["graph_formula"] = formula
        save_settings(self.settings)

    def apply_theme(self):
        super().apply_theme()
        if self.graph_window is not None and self.graph_window.exists():
            self.graph_window.set_theme(self.theme_name)