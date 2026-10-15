# tests/test_graphing.py
# Tests for the graph math (graphing.py). No windows are needed for these.

import math

import pytest

from calculator.graphing import (
    View,
    auto_y_range,
    compile_formula,
    nice_step,
    prepare_formula,
    sample_points,
    split_segments,
    tick_values,
    ticks_with_labels,
)
from calculator.logic import CalcError


def words(text):
    """The formula as a list of its pieces, for easy comparing."""
    return [value for _, value in prepare_formula(text)]


# ----- reading formulas -----

@pytest.mark.parametrize("text, expected", [
    ("x^2", ["x", "^", "2"]),
    ("2x", ["2", "*", "x"]),
    ("2sin(x)", ["2", "*", "sin", "(", "x", ")"]),
    ("(x+1)(x-1)", ["(", "x", "+", "1", ")", "*", "(", "x", "-", "1", ")"]),
    ("xsin(x)", ["x", "*", "sin", "(", "x", ")"]),
    ("y = x^2", ["x", "^", "2"]),
    ("f(x) = 2x+1", ["2", "*", "x", "+", "1"]),
    ("x**2", ["x", "^", "2"]),
    ("pi x", ["pi", "*", "x"]),
    ("e^x", ["e", "^", "x"]),
    ("SIN(X)", ["sin", "(", "x", ")"]),
    ("2×x", ["2", "*", "x"]),
])
def test_prepare_formula(text, expected):
    assert words(text) == expected


@pytest.mark.parametrize("text", ["", "   ", "hello(", "a+b", "x$", "x=2", "5" * 201])
def test_bad_formulas_are_rejected(text):
    with pytest.raises(CalcError):
        prepare_formula(text)


# ----- calculating f(x) -----

@pytest.mark.parametrize("formula, x, expected", [
    ("x^2", 3, 9),
    ("2x+1", 2, 5),
    ("(x+1)(x-1)", 4, 15),
    ("1/x", 4, 0.25),
    ("x^-2", 2, 0.25),
    ("-x^2", 3, -9),
    ("e^x", 0, 1),
    ("2pi", 0, 2 * math.pi),
    ("ln(x)", math.e, 1),
    ("log(x)", 1000, 3),
])
def test_compile_formula(formula, x, expected):
    assert compile_formula(formula)(x) == pytest.approx(expected)


@pytest.mark.parametrize("formula, x", [
    ("1/x", 0),
    ("ln(x)", -1),
    ("log(x)", 0),
    ("x^0.5", -4),
    ("2^x", 5000),
    ("tan(x)", math.pi / 2),
    ("2 3", 1),
])
def test_undefined_points_give_none(formula, x):
    assert compile_formula(formula)(x) is None


def test_radians_and_degrees():
    assert compile_formula("sin(x)", radians=True)(math.pi / 2) == pytest.approx(1)
    assert compile_formula("sin(x)", radians=False)(90) == pytest.approx(1)
    assert compile_formula("cos(2x)", radians=True)(math.pi) == pytest.approx(1)
    assert compile_formula("sin(cos(x))", radians=True)(0) == pytest.approx(math.sin(1))
    assert compile_formula("2sin(x)+3", radians=True)(math.pi / 2) == pytest.approx(5)


# ----- sampling -----

def test_sample_points_covers_the_range():
    points = sample_points(compile_formula("x"), -5, 5, 11)
    assert len(points) == 11
    assert points[0] == (-5, -5)
    assert points[-1][0] == pytest.approx(5)


def test_sample_points_never_has_fewer_than_two():
    assert len(sample_points(compile_formula("x"), 0, 1, 0)) == 2


# ----- choosing the view -----

def test_auto_range_for_sine():
    low, high = auto_y_range(sample_points(compile_formula("sin(x)"), -10, 10, 400))
    assert -1.5 < low < -1.0
    assert 1.0 < high < 1.5


def test_auto_range_ignores_spikes():
    low, high = auto_y_range(sample_points(compile_formula("tan(x)"), -10, 10, 400))
    assert high - low < 100


def test_auto_range_for_a_flat_line():
    low, high = auto_y_range(sample_points(compile_formula("3"), -10, 10, 50))
    assert low < 3 < high


def test_auto_range_with_no_values():
    assert auto_y_range([(0, None), (1, None)]) == (-10.0, 10.0)


# ----- not drawing across gaps -----

def test_segments_break_where_undefined():
    points = [(0, 1.0), (1, 2.0), (2, None), (3, 4.0), (4, 5.0)]
    assert split_segments(points, 0, 10) == [[(0, 1.0), (1, 2.0)], [(3, 4.0), (4, 5.0)]]


def test_segments_break_at_asymptotes():
    points = [(0, 1.0), (1, 2.0), (2, 1000.0), (3, -1000.0), (4, -2.0), (5, -1.0)]
    segments = split_segments(points, -3, 3)
    assert len(segments) == 2


def test_lonely_points_are_dropped():
    assert split_segments([(0, 1.0), (1, None), (2, 3.0)], 0, 10) == []


def test_one_for_x_squared_has_one_segment():
    points = sample_points(compile_formula("x^2"), -10, 10, 300)
    assert len(split_segments(points, -10, 110)) == 1


# ----- tick marks -----

@pytest.mark.parametrize("span, expected", [
    (20, 2), (10, 1), (1, 0.1), (100, 10), (0.5, 0.05),
])
def test_nice_step(span, expected):
    assert nice_step(span) == pytest.approx(expected)


def test_tick_values():
    ticks = tick_values(-10, 10)
    assert ticks[0] == -10 and ticks[-1] == 10
    assert 0 in ticks
    assert len(ticks) == 11


def test_tick_values_for_a_backwards_range():
    assert tick_values(5, 5) == []
    assert tick_values(5, 1) == []


def test_tick_labels():
    assert [label for _, label in ticks_with_labels(-10, 10)][:3] == ["-10", "-8", "-6"]
    assert [label for _, label in ticks_with_labels(0, 1, 5)] == [
        "0.0", "0.2", "0.4", "0.6", "0.8", "1.0",
    ]


def test_zero_is_never_negative_zero():
    labels = [label for _, label in ticks_with_labels(-1, 1, 4)]
    assert "-0.0" not in labels and "-0" not in labels


# ----- the view -----

def test_pixel_conversion_round_trip():
    view = View(-5, 15, -2, 8)
    px, py = view.to_pixel(3.5, 1.25, 400, 300)
    x, y = view.to_data(px, py, 400, 300)
    assert (x, y) == pytest.approx((3.5, 1.25))


def test_corners():
    view = View(0, 10, 0, 10)
    assert view.to_pixel(0, 10, 200, 100) == (0, 0)       # top left
    assert view.to_pixel(10, 0, 200, 100) == (200, 100)   # bottom right


def test_panning_moves_the_view_opposite_to_the_drag():
    view = View(0, 10, 0, 10).panned(100, 0, 200, 100)    # drag right by half the width
    assert (view.x_min, view.x_max) == pytest.approx((-5, 5))
    view = View(0, 10, 0, 10).panned(0, 50, 200, 100)     # drag down by half the height
    assert (view.y_min, view.y_max) == pytest.approx((5, 15))


def test_zoom_keeps_the_point_under_the_mouse_fixed():
    view = View(-10, 10, -10, 10)
    before = view.to_data(300, 100, 400, 300)
    zoomed = view.zoomed(0.5, 300, 100, 400, 300)
    after = zoomed.to_data(300, 100, 400, 300)
    assert after == pytest.approx(before)
    assert zoomed.x_max - zoomed.x_min == pytest.approx(10)


def test_zoom_has_limits():
    view = View(-1e-9, 1e-9, -1e-9, 1e-9)
    assert view.zoomed(0.5, 10, 10, 100, 100) is view
    huge = View(-1e11, 1e11, -1e11, 1e11)
    assert huge.zoomed(10, 10, 10, 100, 100) is huge