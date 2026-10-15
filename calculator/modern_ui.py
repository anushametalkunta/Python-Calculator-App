# calculator/modern_ui.py
# The modern look (rounded buttons, smooth light/dark switching) built with
# CustomTkinter. It reuses ALL the behaviour of the classic CalculatorApp in
# ui.py and only replaces the parts you can SEE: the widgets and the colors.

from __future__ import annotations

import customtkinter as ctk

from .themes import FONT_NAME, THEMES
from .ui import (
    BUTTON_LAYOUT,
    MEMORY_LAYOUT,
    SCI_LAYOUT,
    WINDOW_HEIGHT,
    CalculatorApp,
)


EMPTY_LINE = " "   # what the small line shows when there is nothing to say


def pair(key: str, shade: str | None = None) -> tuple[str, str]:
    """Return a (light color, dark color) pair taken from themes.py.
    CustomTkinter picks the right one by itself when the mode changes."""
    def pick(theme_name: str) -> str:
        value = THEMES[theme_name][key]
        return value if shade is None else value[shade]

    return (pick("light"), pick("dark"))


class ModernCalculatorApp(CalculatorApp):
    """The same calculator with a new look."""

    # ----- sizes -----

    def fit_height(self) -> int:
        """A window height that fits this screen."""
        scaling = getattr(self.root, "_get_window_scaling", lambda: 1.0)()
        available = int(self.root.winfo_screenheight() / scaling) - 90
        return max(520, min(700, available))

    # ----- building the window -----

    def create_toggle(self):
        """Create the reference-inspired left navigation and calculator workspace."""
        self.root.geometry(f"760x{self.fit_height()}+80+30")
        self.root.minsize(680, 520)
        self.shell = ctk.CTkFrame(self.root, corner_radius=0, fg_color="transparent")
        self.shell.pack(fill="both", expand=True)
        self.sidebar = ctk.CTkFrame(self.shell, width=158, corner_radius=0,
                                    fg_color=("#eee9e5", "#241d19"))
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        ctk.CTkLabel(self.sidebar, text="◈  CALCULATOR", font=(FONT_NAME, 15, "bold"),
                     anchor="w").pack(fill="x", padx=14, pady=(22, 18))
        self.nav_buttons = []
        nav_items = [
            ("▣  Standard", self.show_standard),
            ("♟  Scientific", self.toggle_scientific),
            ("▥  Graphing", self.open_graph),
            ("</>  Programming", self.open_programmer),
            ("$  Currency", self.open_units),
            ("◇  Volume / Units", self.open_units),
        ]
        for label, command in nav_items:
            btn = ctk.CTkButton(self.sidebar, text=label, command=command,
                anchor="w", height=35, corner_radius=8, border_width=0,
                fg_color="transparent", hover_color=("#d8d0ca", "#3a302a"),
                text_color=("#302720", "#f3eee9"), font=(FONT_NAME, 12))
            btn.pack(fill="x", padx=8, pady=2)
            self.nav_buttons.append(btn)
        ctk.CTkFrame(self.sidebar, height=1, fg_color=("#d3cbc4", "#493c34")).pack(
            fill="x", padx=10, pady=(18, 8))
        ctk.CTkButton(self.sidebar, text="⚙  Settings", command=self.open_settings,
            anchor="w", height=36, corner_radius=8, fg_color="transparent",
            hover_color=("#d8d0ca", "#3a302a"), text_color=("#302720", "#f3eee9"),
            font=(FONT_NAME, 12)).pack(fill="x", padx=8, pady=4, side="bottom")

        self.content = ctk.CTkFrame(self.shell, corner_radius=0, fg_color="transparent")
        self.content.pack(side="left", fill="both", expand=True)
        self.top_bar = ctk.CTkFrame(self.content, fg_color="transparent")
        self.top_bar.pack(fill="x", padx=12, pady=(10, 0))
        self.toggle_button = self.make_link_button("", self.toggle_theme, width=100)
        self.toggle_button.pack(side="right")
        self.history_button = self.make_link_button("History", self.show_history, width=72)
        self.history_button.pack(side="left")
        self.sci_toggle_button = self.make_link_button("Scientific", self.toggle_scientific, width=92)
        self.sci_toggle_button.pack(side="left", padx=4)

    def show_standard(self):
        """Return to the basic keypad view."""
        if self.sci_visible:
            self.toggle_scientific()

    def toggle_scientific(self):
        """Show/hide the scientific keypad without shrinking the sidebar layout."""
        if self.sci_visible:
            self.sci_frame.pack_forget()
            self.sci_toggle_button.configure(text="Scientific")
        else:
            self.sci_frame.pack(side="left", fill="y", padx=(6, 0), pady=6,
                                before=self.button_frame)
            self.sci_toggle_button.configure(text="Standard")
        self.sci_visible = not self.sci_visible

    def open_settings(self):
        """Small settings window for theme and keyboard shortcuts."""
        win = ctk.CTkToplevel(self.root)
        win.title("Calculator Settings")
        win.geometry("360x300")
        win.transient(self.root)
        ctk.CTkLabel(win, text="Settings", font=(FONT_NAME, 22, "bold")).pack(
            anchor="w", padx=20, pady=(18, 10))
        ctk.CTkLabel(win, text="Appearance", font=(FONT_NAME, 14, "bold")).pack(
            anchor="w", padx=20, pady=(8, 2))
        mode = ctk.CTkSegmentedButton(win, values=["Light", "Dark"],
            command=lambda value: self.set_theme_choice(value))
        mode.set(self.theme_name.title())
        mode.pack(fill="x", padx=20, pady=6)
        ctk.CTkLabel(win, text="Keyboard shortcuts", font=(FONT_NAME, 14, "bold")).pack(
            anchor="w", padx=20, pady=(12, 4))
        ctk.CTkLabel(win, text="Enter = calculate    Esc = clear\nCtrl+C = copy    Ctrl+V = paste\nCtrl+G = graph    Ctrl+P = programmer",
            justify="left", anchor="w").pack(fill="x", padx=20)

    def set_theme_choice(self, value):
        target = value.lower()
        if target != self.theme_name:
            self.toggle_theme()

    def make_link_button(self, text, command, width):
        """A small button with no background, like a link."""
        return ctk.CTkButton(
            self.top_bar,
            text=text,
            command=command,
            width=width,
            height=28,
            corner_radius=10,
            border_width=0,
            fg_color="transparent",
            hover_color=pair("function", "bg"),
            text_color=pair("display_fg"),
            font=(FONT_NAME, 14),
        )

    def create_display(self):
        """A rounded screen with a small line on top and the big line below."""
        # Shared font objects. Changing a font's size updates the label by itself.
        self.display_font = ctk.CTkFont(family=FONT_NAME, size=44)
        self.sub_font = ctk.CTkFont(family=FONT_NAME, size=16)

        self.sub_var.set(EMPTY_LINE)

        self.display_frame = ctk.CTkFrame(
            self.content, corner_radius=20, fg_color=("#ffffff", "#302722")
        )
        self.display_frame.pack(fill="x", padx=12, pady=(8, 8))

        self.sub_display = ctk.CTkLabel(
            self.display_frame,
            textvariable=self.sub_var,
            anchor="e",
            font=self.sub_font,
            text_color=pair("sub_fg"),
            fg_color="transparent",
            height=24,
        )
        self.sub_display.pack(fill="x", padx=18, pady=(16, 0))

        self.display = ctk.CTkLabel(
            self.display_frame,
            textvariable=self.display_var,
            anchor="e",
            font=self.display_font,
            text_color=pair("display_fg"),
            fg_color="transparent",
            height=64,
        )
        self.display.pack(fill="x", padx=18, pady=(0, 12))

        # A small "M" in the corner that shows when something is in memory
        self.memory_label = ctk.CTkLabel(
            self.display_frame,
            text="",
            font=(FONT_NAME, 13, "bold"),
            text_color=pair("sub_fg"),
            fg_color="transparent",
            width=20,
        )
        self.memory_label.place(x=16, y=12)

    def create_buttons(self):
        """The memory row, the main grid and the (hidden) scientific panel."""
        self.memory_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        self.memory_frame.pack(fill="x", padx=10)

        self.body = ctk.CTkFrame(self.content, fg_color="transparent")
        self.body.pack(fill="both", expand=True)

        self.sci_frame = ctk.CTkFrame(self.body, fg_color="transparent")

        self.button_frame = ctk.CTkFrame(self.body, fg_color="transparent")
        self.button_frame.pack(
            side="left", fill="both", expand=True, padx=10, pady=(4, 10)
        )

        self.make_grid(self.memory_frame, MEMORY_LAYOUT, columns=4, font_size=11, width=0)
        self.make_grid(self.sci_frame, SCI_LAYOUT, columns=2, font_size=14, width=5)
        self.make_grid(self.button_frame, BUTTON_LAYOUT, columns=4, font_size=16, width=0)

    def make_grid(self, parent, layout, columns, font_size, width):
        """Create a grid of rounded buttons inside 'parent' from a list of rows."""
        for column in range(columns):
            parent.columnconfigure(column, weight=1, uniform="col")
        for row in range(len(layout)):
            parent.rowconfigure(row, weight=1, uniform="row")

        is_memory_row = layout is MEMORY_LAYOUT

        for row_index, row in enumerate(layout):
            column = 0
            for text in row:
                kind = self.pick_kind(text)
                span = 2 if text == "0" else 1

                button = ctk.CTkButton(
                    parent,
                    text=text,
                    font=(FONT_NAME, round(font_size * 1.5)),  # CustomTkinter sizes are in pixels
                    width=40,
                    height=30 if is_memory_row else 40,
                    corner_radius=12,
                    border_width=0,
                    fg_color=pair(kind, "bg"),
                    hover_color=pair(kind, "active"),
                    text_color=pair(kind, "fg"),
                    command=lambda value=text: self.on_button_click(value),
                )
                button.grid(
                    row=row_index, column=column, columnspan=span,
                    sticky="nsew", padx=4, pady=4,
                )
                self.buttons.append((button, kind))
                column += span

    # ----- colors and themes -----

    def apply_theme(self):
        """Switch every widget between light and dark in one step."""
        theme = THEMES[self.theme_name]

        ctk.set_appearance_mode(self.theme_name)   # CustomTkinter recolors all widgets
        self.root.configure(fg_color=("#f0eeec", "#171412"))
        self.shell.configure(fg_color=("#f0eeec", "#171412"))
        self.content.configure(fg_color=("#f0eeec", "#171412"))
        self.toggle_button.configure(text=theme["toggle_text"])
        self.sidebar.configure(fg_color=("#eee9e5", "#241d19"))

        # The history window still uses plain Tkinter widgets, so we color it ourselves
        if self.history_window is not None and self.history_window.winfo_exists():
            self.history_window.configure(bg=theme["window_bg"])
            self.history_listbox.configure(
                bg=theme["display_bg"],
                fg=theme["display_fg"],
                selectbackground=theme["equals"]["bg"],
                selectforeground="#ffffff",
            )

    # ----- the display (fonts here are in pixels) -----

    def update_display(self):
        """Show the current text on the big line."""
        text = self.expression if self.expression != "" else "0"
        self.display_var.set(text)

        if len(text) <= 10:
            size = 44
        elif len(text) <= 16:
            size = 28
        else:
            size = 20
        self.display_font.configure(size=size)

    def set_sub_display(self, text):
        """Show text on the small line above the big one."""
        # An empty label can be drawn wrongly, so an empty line becomes one space
        self.sub_var.set(text if text != "" else EMPTY_LINE)

        self.sub_font.configure(size=16 if len(text) <= 24 else 12)

    def show_error(self, message, sub_text=""):
        """Show an error message on the screen and reset the calculator."""
        self.display_var.set(message)
        self.display_font.configure(size=24)
        self.set_sub_display(sub_text)
        self.expression = ""
        self.just_calculated = False