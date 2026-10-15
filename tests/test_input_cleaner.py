# tests/test_input_cleaner.py
# Tests for the paste-cleaning helper. Run them with:  python -m pytest

import pytest

from calculator.input_cleaner import clean_pasted_text


@pytest.mark.parametrize("pasted, expected", [
    ("1234.5", "1234.5"),
    ("1,234.5", "1234.5"),
    (" 12 + 3 ", "12+3"),
    ("12\n", "12"),
    ("2*3", "2×3"),
    ("10/4", "10÷4"),
    ("5−3", "5-3"),
    ("2**3", "2^3"),
    ("SIN(30)", "sin(30)"),
    ("2*pi", "2×π"),
    ("(2+3)×4", "(2+3)×4"),
])
def test_good_text_is_cleaned(pasted, expected):
    assert clean_pasted_text(pasted) == expected


@pytest.mark.parametrize("pasted", [
    "",
    "   ",
    "hello",
    "spin",
    "$5",
    "5%",
    "__import__('os')",
    "2+3=5",
    "x+1",
    "5" * 101,
])
def test_bad_text_is_rejected(pasted):
    assert clean_pasted_text(pasted) == ""