# tests/test_more_math.py
# Tests for factorial, nCr, nPr and the phone-style % button.

import pytest

from calculator.input_cleaner import clean_pasted_text
from calculator.logic import apply_percent, calculate


# ----- factorial -----

@pytest.mark.parametrize("expression, expected", [
    ("0!", "1"),
    ("1!", "1"),
    ("5!", "120"),
    ("10!", "3628800"),
    ("17!", "355687428096000"),
    ("3!+2", "8"),
    ("2×3!", "12"),
    ("-3!", "-6"),
    ("2^3!", "64"),
    ("3!^2", "36"),
    ("(2+3)!", "120"),
    ("3!!", "720"),
    ("sin(30)+0!", "1.5"),
])
def test_factorial(expression, expected):
    assert calculate(expression) == expected


@pytest.mark.parametrize("expression, expected", [
    ("18!", "Number too large"),
    ("171!", "Number too large"),
    ("200!", "Number too large"),
    ("5!!!", "Number too large"),
    ("2.5!", "Invalid input"),
    ("(0-1)!", "Invalid input"),
    ("!", "Invalid input"),
    ("5!!!!!!!!!!", "Number too large"),
])
def test_factorial_errors(expression, expected):
    assert calculate(expression) == expected


# ----- combinations (nCr) and permutations (nPr) -----

@pytest.mark.parametrize("expression, expected", [
    ("5nCr2", "10"),
    ("10nCr3", "120"),
    ("5nCr0", "1"),
    ("5nCr5", "1"),
    ("52nCr5", "2598960"),
    ("40nCr20", "137846528820"),
    ("2×5nCr2", "20"),           # nCr is worked out before ×
    ("5nCr2+1", "11"),
    ("5nCr2nCr2", "45"),         # (5 nCr 2) nCr 2 = 10 nCr 2
    ("(2+3)nCr2", "10"),
    ("5!nCr2", "7140"),
    ("5nPr2", "20"),
    ("5nPr0", "1"),
    ("5nPr5", "120"),
    ("10nPr3", "720"),
])
def test_combinations_and_permutations(expression, expected):
    assert calculate(expression) == expected


@pytest.mark.parametrize("expression, expected", [
    ("2nCr5", "Invalid input"),
    ("5nPr6", "Invalid input"),
    ("5nCr-1", "Invalid input"),
    ("5.5nCr2", "Invalid input"),
    ("5nCr", "Invalid input"),
    ("nCr5", "Invalid input"),
    ("2000nCr1", "Number too large"),
    ("100nCr50", "Number too large"),
])
def test_combination_errors(expression, expected):
    assert calculate(expression) == expected


# ----- the % button works like a phone calculator -----

@pytest.mark.parametrize("expression, expected", [
    ("50+20", "50+10"),            # 20% of 50
    ("200-10", "200-20"),          # 10% of 200
    ("2×3+10", "2×3+0.6"),         # 10% of (2×3)
    ("(2+3)+10", "(2+3)+0.5"),
    ("100+0", "100+0"),
    ("200×5", "200×0.05"),         # after × or ÷ it just divides by 100
    ("200÷5", "200÷0.05"),
    ("2+3×10", "2+3×0.1"),
    ("5×-50", "5×-0.5"),
    ("50", "0.5"),
    ("-20", "-0.2"),
    ("(5+10", "(5+0.1"),           # the part before is not a clean calculation
    ("100+", "100+"),
    ("", ""),
])
def test_percent(expression, expected):
    assert apply_percent(expression) == expected


def test_percent_gives_the_right_final_answer():
    assert calculate(apply_percent("50+20")) == "60"
    assert calculate(apply_percent("200-10")) == "180"
    assert calculate(apply_percent("80×25")) == "20"
    assert calculate(apply_percent("100+10")) == "110"


# ----- pasting the new symbols -----

@pytest.mark.parametrize("pasted, expected", [
    ("5!", "5!"),
    ("5ncr2", "5nCr2"),
    ("5 nCr 2", "5nCr2"),
    ("5 NPR 2", "5nPr2"),
    ("(2+3)!", "(2+3)!"),
])
def test_pasting_new_symbols(pasted, expected):
    assert clean_pasted_text(pasted) == expected


@pytest.mark.parametrize("pasted", ["5!?", "5 ncx 2", "5%"])
def test_pasting_bad_text_is_still_rejected(pasted):
    assert clean_pasted_text(pasted) == ""