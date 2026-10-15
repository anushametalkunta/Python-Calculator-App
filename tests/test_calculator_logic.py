# tests/test_calculator_logic.py
# Automatic tests for calculator_logic.py. Run them with:  python -m pytest

import pytest

from calculator.logic import (
    CalcError,
    apply_function,
    apply_percent,
    calculate,
    evaluate,
    format_number,
)


# ----- Basic arithmetic -----

@pytest.mark.parametrize("expression, expected", [
    ("2+3", "5"),
    ("2×3+4", "10"),
    ("2+3×4", "14"),
    ("10÷4", "2.5"),
    ("0.1+0.2", "0.3"),
    ("-5+3", "-2"),
    ("5×-2", "-10"),
    ("10-2-3", "5"),
    ("100÷10÷2", "5"),
    ("007+1", "8"),
    ("1÷3", "0.3333333333"),
    ("5.+1", "6"),
])
def test_basic_arithmetic(expression, expected):
    assert calculate(expression) == expected


# ----- Brackets and powers -----

@pytest.mark.parametrize("expression, expected", [
    ("(2+3)×4", "20"),
    ("((2+3))", "5"),
    ("2^10", "1024"),
    ("2^3^2", "512"),       # powers group from the right: 2^(3^2)
    ("2^-1", "0.5"),
    ("-2^2", "-4"),         # the minus applies after the power
    ("9^0.5", "3"),
])
def test_brackets_and_powers(expression, expected):
    assert calculate(expression) == expected


# ----- Scientific functions (degrees) -----

@pytest.mark.parametrize("expression, expected", [
    ("sin(30)", "0.5"),
    ("cos(60)", "0.5"),
    ("tan(45)", "1"),
    ("log(1000)", "3"),
    ("ln(e)", "1"),
    ("2×π", "6.2831853072"),
    ("sin(30)+cos(60)", "1"),
])
def test_scientific(expression, expected):
    assert calculate(expression) == expected


# ----- Errors must never crash -----

@pytest.mark.parametrize("expression, expected", [
    ("5÷0", "Cannot divide by 0"),
    ("1÷(2-2)", "Cannot divide by 0"),
    ("0^-1", "Cannot divide by 0"),
    ("5++", "Invalid input"),
    ("5+", "Invalid input"),
    ("×5", "Invalid input"),
    ("(2+3", "Invalid input"),
    ("2+3)", "Invalid input"),
    ("()", "Invalid input"),
    ("1.2.3", "Invalid input"),
    ("2 3", "Invalid input"),
    ("hello", "Invalid input"),
    ("__import__('os')", "Invalid input"),
    ("2**3", "Invalid input"),
    ("2//3", "Invalid input"),
    ("log(0)", "Invalid input"),
    ("ln(-1)", "Invalid input"),
    ("(-8)^0.5", "Invalid input"),
    ("sin", "Invalid input"),
    ("sin(30", "Invalid input"),
    ("x+1", "Invalid input"),       # x is unknown unless a variable is supplied
    ("9^9^9", "Number too large"),
    ("99999999999×99999999999", "Number too large"),
])
def test_errors(expression, expected):
    assert calculate(expression) == expected


def test_empty_input():
    assert calculate("") == ""
    assert calculate("   ") == ""


def test_very_deep_brackets_do_not_crash():
    assert calculate("(" * 2000 + "1" + ")" * 2000) == "Invalid input"


# ----- evaluate() and variables (used later for graphs) -----

def test_evaluate_with_variable():
    assert evaluate("x×x+1", {"x": 3.0}) == 10.0


def test_evaluate_raises_calc_error():
    with pytest.raises(CalcError):
        evaluate("5÷0")


# ----- format_number -----

@pytest.mark.parametrize("value, expected", [
    (5.0, "5"),
    (2.5, "2.5"),
    (0.1 + 0.2, "0.3"),
    (-0.0, "0"),
    (1 / 3, "0.3333333333"),
])
def test_format_number(value, expected):
    assert format_number(value) == expected


# ----- The % button -----

@pytest.mark.parametrize("expression, expected", [
    ("50", "0.5"),
    ("50+20", "50+10"),
    ("200", "2"),
    ("5×-50", "5×-0.5"),
    ("", ""),
    ("5+", "5+"),
])
def test_percent(expression, expected):
    assert apply_percent(expression) == expected


# ----- The √ x² 1/x ± buttons -----

@pytest.mark.parametrize("expression, name, expected", [
    ("9", "sqrt", ("3", None)),
    ("5+4", "square", ("5+16", None)),
    ("4", "reciprocal", ("0.25", None)),
    ("0", "reciprocal", ("0", "Cannot divide by 0")),
    ("-9", "sqrt", ("-9", "Invalid input")),
    ("5", "negate", ("-5", None)),
    ("-5", "negate", ("5", None)),
    ("5-3", "negate", ("5+3", None)),
    ("5+3", "negate", ("5-3", None)),
    ("5+", "sqrt", ("5+", None)),
])
def test_apply_function(expression, name, expected):
    assert apply_function(expression, name) == expected