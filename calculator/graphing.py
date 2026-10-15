# calculator/graphing.py
# The math behind the graph window: turning a formula into a function,
# sampling it, choosing a view and tick marks. There are no windows in this
# file, so everything here can be tested automatically.

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Callable

from .logic import CONSTANTS, FUNCTIONS, CalcError, Parser, tokenize

Token = tuple[str, str]
Point = tuple[float, "float | None"]
Function = Callable[[float], "float | None"]

MAX_Y = 1e12                 # bigger values count as "off the chart" (like tan at 90°)
MAX_FORMULA_LENGTH = 200
JUMP_FACTOR = 3.0            # a jump bigger than 3 screens tall is an asymptote
DEGREES_PER_RADIAN = 180 / math.pi
MIN_SPAN = 1e-9              # the most you can zoom in
MAX_SPAN = 1e12              # the most you can zoom out
NAMES = "sin|cos|tan|log|ln|pi|e|x"
TRIG_NAMES = ("sin", "cos", "tan")


# ---------------------------------------------------------------------------
# Turning text into a function of x
# ---------------------------------------------------------------------------

def split_word(word: str) -> list[str]:
    """Split a run of letters into known names: 'xsin' -> ['x', 'sin']."""
    if re.fullmatch(rf"(?:{NAMES})+", word):
        return re.findall(NAMES, word)
    return [word]


def is_value_end(token: Token) -> bool:
    """Can this token be the end of a value? (a number, x, pi, e, or a closing bracket)"""
    kind, value = token
    if kind == "number":
        return True
    if kind == "word":
        return value in CONSTANTS or value == "x"
    return value == ")"


def is_value_start(token: Token) -> bool:
    """Can this token be the start of a value?"""
    kind, value = token
    return kind in ("number", "word") or value == "("


def prepare_formula(text: str) -> list[Token]:
    """Clean up a formula and cut it into tokens. Raises CalcError if it is not usable.

    It understands 'y = ...', 'f(x) = ...' and implicit multiplication,
    so '2x' means 2*x and '(x+1)(x-1)' means (x+1)*(x-1).
    """
    if len(text) > MAX_FORMULA_LENGTH:
        raise CalcError("Formula is too long")

    cleaned = text.strip().lower()
    cleaned = cleaned.replace("×", "*").replace("÷", "/").replace("π", "pi")
    cleaned = cleaned.replace("**", "^")
    cleaned = re.sub(r"^\s*(?:f\s*\(\s*x\s*\)|y)\s*=\s*", "", cleaned)

    if cleaned == "":
        raise CalcError("Type a formula, like sin(x)")

    # Split letters into names, and check that every piece is allowed
    tokens: list[Token] = []
    for kind, value in tokenize(cleaned):
        if kind == "word":
            for name in split_word(value):
                if name not in FUNCTIONS and name not in CONSTANTS and name != "x":
                    raise CalcError(f"Unknown name: {name}")
                tokens.append(("word", name))
        elif kind == "symbol" and value not in "+-*/^()":
            raise CalcError(f"Unexpected symbol: {value}")
        else:
            tokens.append((kind, value))

    # Implicit multiplication: put a * between touching values
    result: list[Token] = []
    for token in tokens:
        if result and is_value_end(result[-1]) and is_value_start(token):
            if not (result[-1][0] == "number" and token[0] == "number"):
                result.append(("symbol", "*"))
        result.append(token)
    return result


def convert_trig_to_radians(tokens: list[Token]) -> list[Token]:
    """Make sin, cos and tan work in radians.

    The calculator's functions work in degrees, so we wrap each argument:
    sin( ... )  becomes  sin( 57.29... * ( ... ) )
    """
    result: list[Token] = []
    stack: list[bool] = []       # for every open bracket: was it a sin/cos/tan call?
    pending = False
    for kind, value in tokens:
        if kind == "symbol" and value == "(":
            result.append((kind, value))
            stack.append(pending)
            if pending:
                result.extend([
                    ("number", repr(DEGREES_PER_RADIAN)),
                    ("symbol", "*"),
                    ("symbol", "("),
                ])
            pending = False
        elif kind == "symbol" and value == ")":
            result.append((kind, value))
            if stack and stack.pop():
                result.append(("symbol", ")"))
            pending = False
        else:
            pending = kind == "word" and value in TRIG_NAMES
            result.append((kind, value))
    return result


def compile_formula(text: str, radians: bool = True) -> Function:
    """Turn a formula like '2x+1' into a Python function f(x).
    The function returns None for any x where the formula has no value."""
    tokens = prepare_formula(text)
    if radians:
        tokens = convert_trig_to_radians(tokens)

    def function(x: float) -> float | None:
        try:
            y = Parser(tokens, {"x": x}).parse()
        except (CalcError, ArithmeticError, ValueError, RecursionError):
            return None
        if not math.isfinite(y) or abs(y) > MAX_Y:
            return None
        return y

    return function


# ---------------------------------------------------------------------------
# Sampling and choosing what to show
# ---------------------------------------------------------------------------

def sample_points(function: Function, x_min: float, x_max: float, count: int) -> list[Point]:
    """Calculate the function at 'count' evenly spaced x values."""
    count = max(2, count)
    step = (x_max - x_min) / (count - 1)
    points: list[Point] = []
    for i in range(count):
        x = x_min + i * step
        points.append((x, function(x)))
    return points


def auto_y_range(points: list[Point]) -> tuple[float, float]:
    """Pick a sensible y range. The most extreme 2% of values are ignored,
    so a spike (like tan near 90°) doesn't squash the rest of the graph."""
    values = sorted(y for _, y in points if y is not None)
    if not values:
        return (-10.0, 10.0)

    last = len(values) - 1
    low = values[int(0.02 * last)]
    high = values[int(0.98 * last)]
    if high - low < 1e-9:           # a flat line, like y = 3
        low -= 1.0
        high += 1.0
    padding = (high - low) * 0.1
    return (low - padding, high + padding)


def split_segments(
    points: list[Point], y_min: float, y_max: float
) -> list[list[tuple[float, float]]]:
    """Cut the points into separate lines, so we never draw a line across
    a gap (where the function is undefined) or across an asymptote."""
    height = y_max - y_min
    segments: list[list[tuple[float, float]]] = []
    current: list[tuple[float, float]] = []
    previous: float | None = None

    for x, y in points:
        broken = y is None or (
            previous is not None and abs(y - previous) > JUMP_FACTOR * height
        )
        if broken:
            segments.append(current)
            current = []
            previous = None
        if y is not None:
            current.append((x, y))
            previous = y
    segments.append(current)

    return [segment for segment in segments if len(segment) >= 2]


# ---------------------------------------------------------------------------
# Tick marks
# ---------------------------------------------------------------------------

def nice_step(span: float, target: int = 8) -> float:
    """A 'nice' distance between tick marks: 1, 2 or 5 times a power of ten."""
    raw = span / target
    exponent = math.floor(math.log10(raw))
    base = raw / 10 ** exponent
    if base < 1.5:
        nice = 1
    elif base < 3.5:
        nice = 2
    elif base < 7.5:
        nice = 5
    else:
        nice = 10
    return nice * 10 ** exponent


def tick_values(low: float, high: float, target: int = 8) -> list[float]:
    """The numbers where grid lines go between low and high."""
    if not high > low:
        return []
    step = nice_step(high - low, target)
    first = math.ceil(low / step)
    last = math.floor(high / step)
    if last - first > 200:
        return []
    return [round(i * step, 12) for i in range(first, last + 1)]


def ticks_with_labels(low: float, high: float, target: int = 8) -> list[tuple[float, str]]:
    """Grid positions together with the text to print next to them."""
    if not high > low:
        return []
    step = nice_step(high - low, target)
    decimals = max(0, -math.floor(math.log10(step)))
    labelled: list[tuple[float, str]] = []
    for value in tick_values(low, high, target):
        if abs(value) < step * 1e-9:
            value = 0.0
        if abs(value) >= 1e7:
            label = f"{value:.3g}"
        else:
            label = f"{value:.{decimals}f}"
        labelled.append((value, label))
    return labelled


def format_value(value: float) -> str:
    """Short text for a number shown while hovering over the graph."""
    return f"{value:.6g}"


# ---------------------------------------------------------------------------
# The view (which part of the graph you are looking at)
# ---------------------------------------------------------------------------

@dataclass
class View:
    """The visible rectangle of the graph, in graph units."""

    x_min: float = -10.0
    x_max: float = 10.0
    y_min: float = -10.0
    y_max: float = 10.0

    def copy(self) -> View:
        return View(self.x_min, self.x_max, self.y_min, self.y_max)

    def to_pixel(self, x: float, y: float, width: float, height: float) -> tuple[float, float]:
        """Graph units -> position on the canvas."""
        px = (x - self.x_min) / (self.x_max - self.x_min) * width
        py = height - (y - self.y_min) / (self.y_max - self.y_min) * height
        return px, py

    def to_data(self, px: float, py: float, width: float, height: float) -> tuple[float, float]:
        """Position on the canvas -> graph units."""
        x = self.x_min + px / width * (self.x_max - self.x_min)
        y = self.y_min + (height - py) / height * (self.y_max - self.y_min)
        return x, y

    def panned(self, dx: float, dy: float, width: float, height: float) -> View:
        """Move the view as if you dragged the graph by (dx, dy) pixels."""
        x_shift = -dx / width * (self.x_max - self.x_min)
        y_shift = dy / height * (self.y_max - self.y_min)
        return View(
            self.x_min + x_shift, self.x_max + x_shift,
            self.y_min + y_shift, self.y_max + y_shift,
        )

    def zoomed(self, factor: float, px: float, py: float, width: float, height: float) -> View:
        """Zoom around a point on the canvas. factor < 1 zooms in, > 1 zooms out."""
        cx, cy = self.to_data(px, py, width, height)
        new = View(
            cx - (cx - self.x_min) * factor, cx + (self.x_max - cx) * factor,
            cy - (cy - self.y_min) * factor, cy + (self.y_max - cy) * factor,
        )
        x_span = new.x_max - new.x_min
        y_span = new.y_max - new.y_min
        if not (MIN_SPAN <= x_span <= MAX_SPAN and MIN_SPAN <= y_span <= MAX_SPAN):
            return self
        return new