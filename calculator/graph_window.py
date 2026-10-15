# calculator/graph_window.py
# The graph window. The math is in graphing.py; this file only draws it
# and reacts to the mouse.

from __future__ import annotations

import tkinter as tk
from typing import Callable

from .graphing import (
    View,
    auto_y_range,
    compile_formula,
    format_value,
    sample_points,
    split_segments,
    ticks_with_labels,
)
from .graph_search import (
    describe_crossings,
    find_crossings,
    matches_everywhere,
    reveal_point,
)
from .logic import CalcError, evaluate
from .themes import FONT_NAME, THEMES

DEFAULT_FORMULA = "sin(x)"
HINT = "Drag to move the graph. Scroll to zoom. Point at the graph to read values."
FALLBACK_SIZE = (560, 400)       # used before the canvas has a real size


class GraphWindow:
    """A window that draws the graph of a formula in x."""

    def __init__(
        self,
        master,
        theme_name: str,
        formula: str = DEFAULT_FORMULA,
        on_plot: Callable[[str], None] | None = None,
    ):
        self.on_plot = on_plot
        self.view = View()
        self.function = None            # the compiled formula (None until plotted)
        self.radians = True
        self.plotted_formula = None     # the formula that is drawn right now
        self.plotted_radians = True
        self.marks = []                 # points to highlight: [(x, y), ...]
        self.drag_start = None          # (mouse x, mouse y, view) while dragging
        self.theme = THEMES[theme_name]

        self.window = tk.Toplevel(master)
        self.window.title("Graph")
        self.window.geometry("620x640+630+8")
        self.window.minsize(480, 520)

        self.formula_var = tk.StringVar(value=formula)
        self.xmin_var = tk.StringVar(value="-10")
        self.xmax_var = tk.StringVar(value="10")
        self.find_x_var = tk.StringVar(value="2")
        self.find_y_var = tk.StringVar(value="0")
        self.status_var = tk.StringVar(value=HINT)

        self.frames = []
        self.labels = []
        self.entries = []
        self.buttons = []

        self.build_controls()
        self.build_canvas()
        self.set_theme(theme_name)
        self.window.after(80, self.plot)    # plot once the window has its size

    # ----- building the window -----

    def build_controls(self):
        """The formula box, the x range, and the buttons."""
        top = tk.Frame(self.window)
        top.pack(fill="x", padx=12, pady=(12, 4))
        self.frames.append(top)

        label = tk.Label(top, text="f(x) =", font=(FONT_NAME, 13))
        label.pack(side="left")
        self.labels.append(label)

        self.formula_entry = tk.Entry(
            top, textvariable=self.formula_var, font=(FONT_NAME, 13),
            relief="flat", highlightthickness=1,
        )
        self.formula_entry.pack(side="left", fill="x", expand=True, padx=8, ipady=4)
        self.formula_entry.bind("<Return>", self.plot)
        self.entries.append(self.formula_entry)

        self.plot_button = tk.Button(
            top, text="Plot", font=(FONT_NAME, 11), relief="flat", bd=0,
            padx=16, pady=4, cursor="hand2", command=self.plot,
        )
        self.plot_button.pack(side="right")

        options = tk.Frame(self.window)
        options.pack(fill="x", padx=12, pady=(0, 4))
        self.frames.append(options)

        label = tk.Label(options, text="x from", font=(FONT_NAME, 10))
        label.pack(side="left")
        self.labels.append(label)

        for variable in (self.xmin_var, None, self.xmax_var):
            if variable is None:
                label = tk.Label(options, text="to", font=(FONT_NAME, 10))
                label.pack(side="left", padx=4)
                self.labels.append(label)
                continue
            entry = tk.Entry(
                options, textvariable=variable, width=8, font=(FONT_NAME, 10),
                relief="flat", highlightthickness=1,
            )
            entry.pack(side="left", padx=(4, 0), ipady=2)
            entry.bind("<Return>", self.plot)
            self.entries.append(entry)

        self.reset_button = tk.Button(
            options, text="Reset view", font=(FONT_NAME, 10), relief="flat",
            bd=0, padx=10, pady=2, cursor="hand2", command=self.plot,
        )
        self.reset_button.pack(side="right")
        self.buttons.append(self.reset_button)

        self.angle_button = tk.Button(
            options, text="Angles: radians", font=(FONT_NAME, 10), relief="flat",
            bd=0, padx=10, pady=2, cursor="hand2", command=self.toggle_angles,
        )
        self.angle_button.pack(side="right", padx=6)
        self.buttons.append(self.angle_button)

        self.build_find_row()

    def build_find_row(self):
        """Two small searches: type x to get y, or type y to find the x values."""
        row = tk.Frame(self.window)
        row.pack(fill="x", padx=12, pady=(0, 4))
        self.frames.append(row)

        def add_label(text):
            label = tk.Label(row, text=text, font=(FONT_NAME, 10))
            label.pack(side="left", padx=(0, 4))
            self.labels.append(label)

        def add_entry(variable, action):
            entry = tk.Entry(
                row, textvariable=variable, width=8, font=(FONT_NAME, 10),
                relief="flat", highlightthickness=1,
            )
            entry.pack(side="left", ipady=2)
            entry.bind("<Return>", action)
            self.entries.append(entry)

        def add_button(text, action, space):
            button = tk.Button(
                row, text=text, font=(FONT_NAME, 10), relief="flat", bd=0,
                padx=10, pady=2, cursor="hand2", command=action,
            )
            button.pack(side="left", padx=(6, space))
            self.buttons.append(button)

        add_label("At x =")
        add_entry(self.find_x_var, self.find_y)
        add_button("Find y", self.find_y, 18)

        add_label("Where y =")
        add_entry(self.find_y_var, self.find_x)
        add_button("Find x", self.find_x, 0)

    def build_canvas(self):
        """The drawing area and the line of text under it."""
        self.canvas = tk.Canvas(self.window, highlightthickness=0, height=380)
        self.canvas.pack(fill="both", expand=True, padx=12, pady=6)
        self.canvas.bind("<Configure>", self.on_resize)
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<MouseWheel>", self.on_wheel)
        self.canvas.bind("<Motion>", self.on_motion)
        self.canvas.bind("<Leave>", self.on_leave)

        self.status = tk.Label(
            self.window, textvariable=self.status_var, anchor="w", font=(FONT_NAME, 10)
        )
        self.status.pack(fill="x", padx=14, pady=(0, 12))

    # ----- window control -----

    def exists(self) -> bool:
        """True while the window is still open."""
        return bool(self.window.winfo_exists())

    def show(self):
        """Bring the window to the front."""
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
        self.status.configure(bg=theme["window_bg"], fg=theme["sub_fg"])

        for entry in self.entries:
            entry.configure(
                bg=theme["display_bg"],
                fg=theme["display_fg"],
                insertbackground=theme["display_fg"],
                highlightbackground=theme["number"]["active"],
                highlightcolor=theme["equals"]["bg"],
            )
        for button in self.buttons:
            button.configure(
                bg=theme["function"]["bg"],
                fg=theme["function"]["fg"],
                activebackground=theme["function"]["active"],
                activeforeground=theme["function"]["fg"],
            )
        self.plot_button.configure(
            bg=theme["equals"]["bg"],
            fg=theme["equals"]["fg"],
            activebackground=theme["equals"]["active"],
            activeforeground=theme["equals"]["fg"],
        )

        self.canvas.configure(bg=theme["display_bg"])
        self.redraw()

    # ----- plotting -----

    def canvas_size(self) -> tuple[int, int]:
        """The size of the drawing area in pixels."""
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        if width < 50 or height < 50:
            return FALLBACK_SIZE
        return width, height

    def show_status(self, text: str):
        self.status_var.set(text)

    def plot(self, event=None):
        """Read the boxes, calculate the graph and draw it."""
        formula = self.formula_var.get()

        try:
            function = compile_formula(formula, radians=self.radians)
        except CalcError as error:
            self.show_status(f"Formula problem: {error}")
            return

        try:
            x_min = evaluate(self.xmin_var.get())
            x_max = evaluate(self.xmax_var.get())
        except CalcError:
            self.show_status("Check the x range. Use numbers like -10 or -2*pi.")
            return
        if not x_min < x_max:
            self.show_status("The first x must be smaller than the second x.")
            return

        width, _ = self.canvas_size()
        points = sample_points(function, x_min, x_max, self.sample_count(width))
        if all(y is None for _, y in points):
            self.function = None
            self.marks = []
            self.view = View(x_min, x_max, -10.0, 10.0)
            self.redraw()
            self.show_status(
                "Nothing to draw: the formula has no value for any x in this range."
            )
            return

        y_min, y_max = auto_y_range(points)
        self.view = View(x_min, x_max, y_min, y_max)
        self.function = function
        self.plotted_formula = formula.strip()
        self.plotted_radians = self.radians
        self.marks = []
        self.redraw()
        self.show_status(HINT)

        if self.on_plot is not None:
            self.on_plot(formula.strip())

    def toggle_angles(self):
        """Switch sin, cos and tan between radians and degrees, then plot again."""
        self.radians = not self.radians
        self.angle_button.configure(
            text="Angles: radians" if self.radians else "Angles: degrees"
        )
        self.plot()

    @staticmethod
    def sample_count(width: int) -> int:
        """One calculated point for about every pixel, but never too few or too many."""
        return min(max(width, 200), 900)

    def sync_range_boxes(self):
        """Show the current x range in the two boxes."""
        self.xmin_var.set(format_value(self.view.x_min))
        self.xmax_var.set(format_value(self.view.x_max))

    # ----- searching the graph -----

    def ensure_plotted(self) -> bool:
        """Make sure the graph on screen matches the formula box.
        Returns False if there is nothing to search."""
        formula_changed = self.formula_var.get().strip() != self.plotted_formula
        if self.function is None or formula_changed or self.radians != self.plotted_radians:
            self.plot()
        return self.function is not None

    def find_y(self, event=None):
        """Type an x, get the y of the curve there, and mark the point."""
        if not self.ensure_plotted():
            return
        try:
            x = evaluate(self.find_x_var.get())
        except CalcError:
            self.show_status("Type a number for x, like 2 or pi/2.")
            return

        y = self.function(x)
        if y is None:
            self.marks = []
            self.redraw()
            self.show_status(f"The formula has no value at x = {format_value(x)}.")
            return

        self.marks = [(x, y)]
        self.view = reveal_point(self.view, x, y)
        self.sync_range_boxes()
        self.redraw()
        self.show_status(f"f({format_value(x)}) = {format_value(y)}")

    def find_x(self, event=None):
        """Type a y, find every x (in view) where the curve reaches it, and mark them."""
        if not self.ensure_plotted():
            return
        try:
            target = evaluate(self.find_y_var.get())
        except CalcError:
            self.show_status("Type a number for y, like 0 or 2.5.")
            return

        x_min, x_max = self.view.x_min, self.view.x_max
        if matches_everywhere(self.function, target, x_min, x_max):
            self.marks = []
            self.redraw()
            self.show_status(f"The curve is y = {format_value(target)} everywhere here.")
            return

        solutions = find_crossings(self.function, target, x_min, x_max)
        if not solutions:
            self.marks = []
            self.redraw()
            self.show_status(
                f"The curve does not reach y = {format_value(target)} for x between "
                f"{format_value(x_min)} and {format_value(x_max)}. Try a wider x range."
            )
            return

        self.marks = [(x, target) for x in solutions]
        self.view = reveal_point(self.view, solutions[0], target)
        self.sync_range_boxes()
        self.redraw()
        self.show_status(describe_crossings(target, solutions))

    # ----- drawing -----

    def redraw(self):
        """Draw the grid, the axes and the curve."""
        canvas = self.canvas
        theme = self.theme
        width, height = self.canvas_size()
        view = self.view

        canvas.delete("all")

        grid_color = theme["number"]["active"]
        axis_color = theme["sub_fg"]
        text_color = theme["sub_fg"]
        curve_color = theme["equals"]["bg"]

        # Grid lines with numbers
        for value, label in ticks_with_labels(view.x_min, view.x_max, max(4, width // 80)):
            px, _ = view.to_pixel(value, 0, width, height)
            canvas.create_line(px, 0, px, height, fill=grid_color)
            canvas.create_text(
                px + 3, height - 3, text=label, anchor="sw",
                fill=text_color, font=(FONT_NAME, 8),
            )
        for value, label in ticks_with_labels(view.y_min, view.y_max, max(4, height // 60)):
            _, py = view.to_pixel(0, value, width, height)
            canvas.create_line(0, py, width, py, fill=grid_color)
            canvas.create_text(
                4, py - 2, text=label, anchor="sw",
                fill=text_color, font=(FONT_NAME, 8),
            )

        # The two axes (only if they are in view)
        if view.y_min <= 0 <= view.y_max:
            _, py = view.to_pixel(0, 0, width, height)
            canvas.create_line(0, py, width, py, fill=axis_color, width=2)
        if view.x_min <= 0 <= view.x_max:
            px, _ = view.to_pixel(0, 0, width, height)
            canvas.create_line(px, 0, px, height, fill=axis_color, width=2)

        # The curve
        if self.function is not None:
            points = sample_points(
                self.function, view.x_min, view.x_max, self.sample_count(width)
            )
            y_span = view.y_max - view.y_min
            low = view.y_min - 2 * y_span       # keep drawn values from flying off
            high = view.y_max + 2 * y_span
            for segment in split_segments(points, view.y_min, view.y_max):
                coordinates = []
                for x, y in segment:
                    y = min(max(y, low), high)
                    px, py = view.to_pixel(x, y, width, height)
                    coordinates.extend((px, py))
                canvas.create_line(
                    *coordinates, fill=curve_color, width=2,
                    capstyle="round", joinstyle="round",
                )

        # Highlighted points from "Find y" and "Find x"
        for x, y in self.marks[:40]:
            px, py = view.to_pixel(x, y, width, height)
            if not (0 <= px <= width and 0 <= py <= height):
                continue
            canvas.create_oval(
                px - 6, py - 6, px + 6, py + 6,
                fill=theme["operator"]["bg"], outline=theme["display_bg"], width=2,
            )
            canvas.create_text(
                px + 9, py - 9, text=f"({format_value(x)}, {format_value(y)})",
                anchor="sw", fill=theme["display_fg"], font=(FONT_NAME, 9, "bold"),
            )

    # ----- the mouse -----

    def on_resize(self, event=None):
        self.redraw()

    def on_press(self, event):
        self.drag_start = (event.x, event.y, self.view.copy())
        self.canvas.delete("trace")

    def on_drag(self, event):
        if self.drag_start is None:
            return
        start_x, start_y, start_view = self.drag_start
        width, height = self.canvas_size()
        self.view = start_view.panned(event.x - start_x, event.y - start_y, width, height)
        self.sync_range_boxes()
        self.redraw()

    def on_release(self, event):
        self.drag_start = None

    def on_wheel(self, event):
        """Scroll up to zoom in, scroll down to zoom out (around the mouse)."""
        factor = 0.8 if event.delta > 0 else 1.25
        width, height = self.canvas_size()
        self.view = self.view.zoomed(factor, event.x, event.y, width, height)
        self.sync_range_boxes()
        self.redraw()

    def on_motion(self, event):
        """Show x and y of the curve under the mouse, with a dot on the curve."""
        self.canvas.delete("trace")
        if self.function is None or self.drag_start is not None:
            return

        width, height = self.canvas_size()
        x, _ = self.view.to_data(event.x, event.y, width, height)
        y = self.function(x)
        if y is None:
            self.show_status(f"x = {format_value(x)}    (no value here)")
            return

        px, py = self.view.to_pixel(x, y, width, height)
        if 0 <= py <= height:
            self.canvas.create_oval(
                px - 5, py - 5, px + 5, py + 5,
                fill=self.theme["equals"]["bg"], outline=self.theme["display_bg"],
                width=2, tags="trace",
            )
        self.show_status(f"x = {format_value(x)}    y = {format_value(y)}")

    def on_leave(self, event):
        self.canvas.delete("trace")
        self.show_status(HINT)