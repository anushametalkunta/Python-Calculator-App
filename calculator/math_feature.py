# calculator/math_feature.py
# Adds a row of extra math buttons: n!  nCr  nPr  Ans. Like the graph feature,
# it is a "mixin": a small class that adds one feature to the calculator.

from __future__ import annotations

import re
import tkinter as tk

from .logic import find_last_number
from .themes import THEMES

MATH_LAYOUT = [
    ["n!", "nCr", "nPr", "Ans"],
]
MATH_BUTTONS = ("n!", "nCr", "nPr", "Ans")
COMBINATION_NAMES = ("nCr", "nPr")
VALUE_ENDINGS = ")πe!.0123456789"     # characters that can end a number or value


class MoreMathMixin:
    """Adds factorial, combinations, permutations and the last answer (Ans)."""

    modern_widgets = False
    math_frame = None

    # ----- building -----

    def create_buttons(self):
        super().create_buttons()
        self.add_math_row()

    def add_math_row(self):
        """A row of small buttons between the memory row and the main buttons."""
        if self.modern_widgets:
            import customtkinter as ctk

            self.math_frame = ctk.CTkFrame(self.root, fg_color="transparent")
            padx = 10
        else:
            self.math_frame = tk.Frame(self.root)
            padx = 6
        self.math_frame.pack(fill="x", padx=padx, after=self.memory_frame)
        self.make_grid(self.math_frame, MATH_LAYOUT, columns=4, font_size=11, width=0)

    def pick_kind(self, text):
        """The new buttons use the grey 'function' color."""
        if text in MATH_BUTTONS:
            return "function"
        return super().pick_kind(text)

    def apply_theme(self):
        super().apply_theme()
        if self.math_frame is not None and not self.modern_widgets:
            self.math_frame.configure(bg=THEMES[self.theme_name]["window_bg"])

    # ----- the new buttons -----

    def on_button_click(self, text):
        if text in MATH_BUTTONS:
            self.press_math(text)
            return
        super().on_button_click(text)

    def press_math(self, text):
        if text == "Ans":
            self.insert_answer()
        elif text == "n!":
            self.add_factorial()
        else:
            self.add_combination(text)

    def ends_with_value(self) -> bool:
        """True if the screen ends with something that is a number or a value."""
        return self.expression[-1:] != "" and self.expression[-1] in VALUE_ENDINGS

    def add_factorial(self):
        """Put ! after the number: 5 becomes 5!"""
        if not self.ends_with_value():
            self.flash_message("Type a number first")
            return
        self.expression += "!"
        self.just_calculated = False
        self.update_display()

    def add_combination(self, name):
        """Put nCr or nPr between two numbers: 5 becomes 5nCr, then type the second number."""
        if self.expression.endswith(COMBINATION_NAMES):
            self.expression = self.expression[:-3] + name       # change nCr to nPr (or back)
        elif self.ends_with_value():
            self.expression += name
        else:
            self.flash_message("Type a number first")
            return
        self.just_calculated = False
        self.update_display()

    def last_answer(self):
        """The result of the most recent calculation (kept in the history), or None."""
        if not self.history:
            return None
        return self.history[-1].rsplit(" = ", 1)[-1]

    def insert_answer(self):
        """The Ans button: type the last answer, like typing the number yourself."""
        answer = self.last_answer()
        if answer is None:
            self.flash_message("No answer yet")
            return
        self.insert_number(answer)

    def insert_number(self, text):
        if self.just_calculated:
            self.expression = ""
            self.just_calculated = False

        found = find_last_number(self.expression)
        if found is not None:
            self.expression = self.expression[:found[0]] + text   # replace the number being typed
        else:
            if self.expression[-1:] in (")", "π", "e", "!"):
                self.expression += "×"
            self.expression += text

        self.just_calculated = re.search(r"[+\-×÷^()πe!]", self.expression[1:]) is None
        self.update_display()

    # ----- small changes to how the existing buttons behave -----

    def add_digit(self, text):
        if self.expression.endswith("!") and not self.just_calculated:
            self.expression += "×"                      # 5!2 means 5!×2
        super().add_digit(text)

    def add_open_token(self, token):
        if self.expression.endswith("!") and not self.just_calculated:
            self.expression += "×"                      # 5!sin( means 5!×sin(
        super().add_open_token(token)

    def add_operator(self, text):
        for name in COMBINATION_NAMES:
            if self.expression.endswith(name):          # an operator replaces a dangling nCr
                self.expression = self.expression[:-len(name)]
                break
        super().add_operator(text)

    def press_backspace(self):
        for name in COMBINATION_NAMES:
            if self.expression.endswith(name):          # backspace removes all of nCr at once
                self.just_calculated = False
                self.expression = self.expression[:-len(name)]
                return
        super().press_backspace()

    def on_key_press(self, event):
        if event.char == "!":
            self.on_button_click("n!")
        elif event.char in ("a", "A"):
            self.on_button_click("Ans")
        else:
            super().on_key_press(event)