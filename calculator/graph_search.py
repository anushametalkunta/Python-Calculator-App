# calculator/graph_search.py
# Searching a graph: finding where a curve crosses a given y value, and
# making sure a point is visible. There are no windows here, so it is testable.

from __future__ import annotations

from typing import Callable

from .graphing import Function, View, format_value

SAMPLES = 2000          # how many x values we look at when searching
MAX_SOLUTIONS = 50      # stop after this many solutions
MAX_REFINEMENTS = 300   # safety limit for the slower "touching" search


def difference(function: Function, target: float) -> Callable[[float], float | None]:
    """A function that gives f(x) - target, or None where f has no value."""
    def g(x: float) -> float | None:
        y = function(x)
        return None if y is None else y - target

    return g


def bisect(g: Callable[[float], float | None], a: float, b: float, g_a: float) -> float | None:
    """Narrow down a sign change between a and b until we are very close to it."""
    for _ in range(80):
        middle = (a + b) / 2
        g_middle = g(middle)
        if g_middle is None:
            return None
        if g_middle == 0:
            return middle
        if (g_a < 0) == (g_middle < 0):
            a, g_a = middle, g_middle
        else:
            b = middle
    return (a + b) / 2


def smallest_abs(g: Callable[[float], float | None], a: float, b: float) -> float:
    """Find where |g| is smallest between a and b (for curves that only touch)."""
    def h(x: float) -> float:
        value = g(x)
        return float("inf") if value is None else abs(value)

    for _ in range(100):
        one_third = a + (b - a) / 3
        two_thirds = b - (b - a) / 3
        if h(one_third) < h(two_thirds):
            b = two_thirds
        else:
            a = one_third
    return (a + b) / 2


def find_crossings(
    function: Function,
    target: float,
    x_min: float,
    x_max: float,
    samples: int = SAMPLES,
    limit: int = MAX_SOLUTIONS,
) -> list[float]:
    """Every x between x_min and x_max where function(x) equals target.

    It looks for places where the curve goes from below the target to above it
    (or the other way round), then zooms in on each one. Curves that only touch
    the target, like x^2 touching 0, are found as well. Jumps across an
    asymptote (like 1/x at 0) are NOT counted as solutions.
    """
    if not x_max > x_min or samples < 3:
        return []

    g = difference(function, target)
    step = (x_max - x_min) / (samples - 1)
    xs = [x_min + i * step for i in range(samples)]
    values = [g(x) for x in xs]
    tolerance = 1e-6 * max(1.0, abs(target))

    solutions: list[float] = []
    refinements = 0

    def add(x: float) -> None:
        if abs(x) < 1e-12:
            x = 0.0
        if all(abs(x - known) > step * 0.5 for known in solutions):
            solutions.append(x)

    def is_solution(x: float) -> bool:
        value = g(x)
        return value is not None and abs(value) <= tolerance

    for i in range(samples):
        value = values[i]
        if value is None:
            continue

        if value == 0:                                   # landed exactly on it
            add(xs[i])
        elif i + 1 < samples and values[i + 1] is not None and value * values[i + 1] < 0:
            root = bisect(g, xs[i], xs[i + 1], value)    # the curve crosses here
            if root is not None and is_solution(root):
                add(root)
        elif (
            0 < i < samples - 1
            and values[i - 1] is not None
            and values[i + 1] is not None
            and value * values[i - 1] > 0
            and value * values[i + 1] > 0
            and abs(value) <= abs(values[i - 1])
            and abs(value) <= abs(values[i + 1])
            and refinements < MAX_REFINEMENTS
        ):
            refinements += 1                             # it might just touch here
            root = smallest_abs(g, xs[i - 1], xs[i + 1])
            if is_solution(root):
                add(root)

        if len(solutions) >= limit:
            break

    return sorted(solutions)


def matches_everywhere(
    function: Function, target: float, x_min: float, x_max: float, count: int = 50
) -> bool:
    """True if the curve IS the line y = target (like y = 3 and target 3)."""
    g = difference(function, target)
    tolerance = 1e-9 * max(1.0, abs(target))
    for i in range(count):
        value = g(x_min + (x_max - x_min) * i / (count - 1))
        if value is None or abs(value) > tolerance:
            return False
    return True


def reveal_point(view: View, x: float, y: float) -> View:
    """Move the view (without zooming) so that the point (x, y) is inside it."""
    new = view.copy()
    if not new.x_min <= x <= new.x_max:
        shift = x - (new.x_min + new.x_max) / 2
        new.x_min += shift
        new.x_max += shift
    if not new.y_min <= y <= new.y_max:
        shift = y - (new.y_min + new.y_max) / 2
        new.y_min += shift
        new.y_max += shift
    return new


def describe_crossings(target: float, solutions: list[float], shown: int = 6) -> str:
    """A sentence like: y = 0 at x = -3.14159, 0, 3.14159"""
    text = ", ".join(format_value(x) for x in solutions[:shown])
    sentence = f"y = {format_value(target)} at x = {text}"
    extra = len(solutions) - shown
    if extra > 0:
        sentence += f"  ... and {extra} more"
    return sentence