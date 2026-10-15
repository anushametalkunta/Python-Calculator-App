# tests/test_graph_search.py
# Tests for searching a graph (graph_search.py). No windows are needed.

import math

import pytest

from calculator.graph_search import (
    describe_crossings,
    find_crossings,
    matches_everywhere,
    reveal_point,
)
from calculator.graphing import View, compile_formula


def crossings(formula, target, x_min, x_max, **options):
    return find_crossings(compile_formula(formula), target, x_min, x_max, **options)


# ----- where does the curve reach a y value? -----

def test_parabola_reaches_four_twice():
    assert crossings("x^2", 4, -10, 10) == pytest.approx([-2, 2])


def test_a_line_reaches_every_value_once():
    assert crossings("x", 5, -10, 10) == pytest.approx([5])
    assert crossings("2x+1", 0, -10, 10) == pytest.approx([-0.5])


def test_sine_crosses_zero_three_times():
    found = crossings("sin(x)", 0, -4, 4)
    assert found == pytest.approx([-math.pi, 0, math.pi])


def test_sine_crosses_one_half():
    found = crossings("sin(x)", 0.5, 0, 2 * math.pi)
    assert found == pytest.approx([math.pi / 6, 5 * math.pi / 6])


def test_a_curve_that_only_touches_is_found():
    found = crossings("x^2", 0, -10, 10)
    assert len(found) == 1
    assert found[0] == pytest.approx(0, abs=1e-6)


def test_a_double_root_is_found():
    found = crossings("(x-3)^2", 0, -10, 10)
    assert len(found) == 1
    assert found[0] == pytest.approx(3, abs=1e-6)


def test_curve_that_never_gets_there():
    assert crossings("x^2+1", 0, -10, 10) == []
    assert crossings("sin(x)", 2, -10, 10) == []


def test_asymptotes_are_not_solutions():
    assert crossings("1/x", 0, -10, 10) == []
    assert crossings("tan(x)", 1000000, -1, 1) == []


def test_tangent_crosses_zero_at_multiples_of_pi():
    found = crossings("tan(x)", 0, -4, 4)
    assert found == pytest.approx([-math.pi, 0, math.pi])


def test_gaps_in_the_curve_are_skipped():
    assert crossings("ln(x)", 0, -5, 5) == pytest.approx([1])


def test_solutions_come_back_sorted():
    found = crossings("sin(x)", 0, -20, 20)
    assert found == sorted(found)
    assert len(found) == 13


def test_the_limit_is_respected():
    assert len(crossings("sin(x)", 0, -1000, 1000, limit=5)) == 5


def test_a_backwards_range_gives_nothing():
    assert crossings("x", 0, 5, 1) == []


def test_exact_hits_are_found():
    assert crossings("x", 0, -1, 1, samples=3) == [0.0]


# ----- the curve IS the line -----

def test_matches_everywhere():
    assert matches_everywhere(compile_formula("3"), 3, -10, 10)
    assert not matches_everywhere(compile_formula("3"), 4, -10, 10)
    assert not matches_everywhere(compile_formula("x"), 0, -10, 10)
    assert not matches_everywhere(compile_formula("1/x"), 0, -10, 10)


# ----- making a point visible -----

def test_a_point_already_in_view_changes_nothing():
    view = View(0, 10, 0, 10)
    assert reveal_point(view, 5, 5) == view


def test_a_point_off_to_the_right_moves_the_view():
    view = reveal_point(View(0, 10, 0, 10), 20, 5)
    assert (view.x_min, view.x_max) == pytest.approx((15, 25))
    assert (view.y_min, view.y_max) == (0, 10)


def test_a_point_above_moves_the_view_up():
    view = reveal_point(View(0, 10, 0, 10), 5, -30)
    assert (view.y_min, view.y_max) == pytest.approx((-35, -25))
    assert (view.x_min, view.x_max) == (0, 10)


def test_revealing_never_changes_the_zoom():
    original = View(-3, 7, -2, 8)
    moved = reveal_point(original, 100, 100)
    assert moved.x_max - moved.x_min == pytest.approx(10)
    assert moved.y_max - moved.y_min == pytest.approx(10)
    assert original == View(-3, 7, -2, 8)       # the old view is untouched


# ----- the sentence shown to the user -----

def test_describe_crossings():
    assert describe_crossings(0, [-2, 2]) == "y = 0 at x = -2, 2"
    assert describe_crossings(2.5, [1.5]) == "y = 2.5 at x = 1.5"


def test_describe_many_crossings():
    text = describe_crossings(0, [1, 2, 3, 4, 5, 6, 7, 8])
    assert text.startswith("y = 0 at x = 1, 2, 3, 4, 5, 6")
    assert text.endswith("and 2 more")