# tests/test_programmer.py
# Tests for Programmer mode (programmer.py). No windows are needed.

import pytest

from calculator.logic import CalcError
from calculator.programmer import (
    describe,
    evaluate_int,
    format_binary,
    format_hex,
    format_octal,
    parse_number,
    represent,
)


# ----- numbers in different notations -----

@pytest.mark.parametrize("text, expected", [
    ("255", 255),
    ("0xFF", 255),
    ("0xff", 255),
    ("0XFF", 255),
    ("0b1010", 10),
    ("0B1010", 10),
    ("0o17", 15),
    ("1_000", 1000),
    ("0xFF_FF", 65535),
    ("0", 0),
    ("007", 7),
])
def test_numbers_in_decimal_mode(text, expected):
    assert evaluate_int(text) == expected


@pytest.mark.parametrize("text, base, expected", [
    ("FF", 16, 255),
    ("ff + 1", 16, 256),
    ("DEAD", 16, 0xDEAD),
    ("A and F", 16, 10),
    ("0b1", 16, 0xB1),          # in hex, 0b1 is just a hex number
    ("0x10", 16, 16),
    ("1010", 2, 10),
    ("1111_0000", 2, 240),
    ("17", 8, 15),
    ("0x10", 2, 16),            # a prefix wins over the input base
    ("0b11", 8, 3),
    ("10", 10, 10),
])
def test_input_bases(text, base, expected):
    assert evaluate_int(text, base) == expected


# ----- arithmetic and precedence -----

@pytest.mark.parametrize("text, expected", [
    ("10 + 5 * 2", 20),
    ("(10 + 5) * 2", 30),
    ("10 - 3 - 2", 5),
    ("7 / 2", 3),
    ("-7 / 2", -3),             # cut off towards zero, like C
    ("7 / -2", -3),
    ("-7 / -2", 3),
    ("7 % 3", 1),
    ("-7 % 3", -1),             # the sign follows the first number, like C
    ("7 % -3", 1),
    ("2 * -3", -6),
    ("- -3", 3),
    ("+5", 5),
    ("1 + 2 << 3", 24),         # + binds tighter than <<
    ("6 & 3 | 8", 10),          # & binds tighter than |
    ("5 | 2 ^ 7 & 3", 5),      # & then ^ then |
    ("1 | 2 & 3", 3),
    ("6 ^ 3", 5),
    ("0xFF & 0x0F", 15),
    ("0xF0 | 0x0F", 255),
    ("1 << 8", 256),
    ("256 >> 4", 16),
    ("-16 >> 2", -4),
    ("5 >> 10", 0),
    ("-5 >> 10", -1),
    ("~0", -1),
    ("~5", -6),
    ("-~5", 6),
    ("~(~5)", 5),
    ("1 << 2 << 3", 32),
])
def test_expressions(text, expected):
    assert evaluate_int(text) == expected


# ----- the word operators -----

@pytest.mark.parametrize("text, expected", [
    ("6 AND 3", 2),
    ("6 and 3", 2),
    ("6 or 3", 7),
    ("6 xor 3", 5),
    ("not 0", -1),
    ("NOT 5", -6),
    ("7 mod 4", 3),
    ("1 shl 4", 16),
    ("256 shr 4", 16),
    ("(1 shl 4) or 1", 17),
])
def test_word_operators(text, expected):
    assert evaluate_int(text) == expected


# ----- errors never crash -----

@pytest.mark.parametrize("text, message", [
    ("", "Invalid input"),
    ("   ", "Invalid input"),
    ("5 +", "Invalid input"),
    ("* 5", "Invalid input"),
    ("5 5", "Invalid input"),
    ("(", "Invalid input"),
    (")", "Invalid input"),
    ("(5", "Invalid input"),
    ("5)", "Invalid input"),
    ("()", "Invalid input"),
    ("1 << -1", "Invalid input"),
    ("1 >> -1", "Invalid input"),
    ("1/0", "Cannot divide by 0"),
    ("5 % 0", "Cannot divide by 0"),
    ("1 << 2000", "Shift too large"),
    ("1 << 1024 << 1024 << 1024 << 1024", "Number too large"),
    ("$", "Unexpected character: $"),
    ("5 = 5", "Unexpected character: ="),
    ("abc", "Not a valid decimal number: abc"),
    ("0xZZ", "Not a valid hexadecimal number: 0xZZ"),
    ("0x", "Not a valid hexadecimal number: 0x"),
    ("0b102", "Not a valid binary number: 0b102"),
    ("5and3", "Not a valid decimal number: 5and3"),
    ("1" * 201, "Expression is too long"),
])
def test_errors(text, message):
    with pytest.raises(CalcError) as problem:
        evaluate_int(text)
    assert str(problem.value) == message


def test_digits_must_fit_the_base():
    with pytest.raises(CalcError):
        evaluate_int("2", 2)
    with pytest.raises(CalcError):
        evaluate_int("9", 8)
    with pytest.raises(CalcError):
        evaluate_int("G", 16)


def test_very_deep_brackets_do_not_crash():
    text = "(" * 99 + "1" + ")" * 99
    try:
        assert evaluate_int(text) == 1
    except CalcError:
        pass                    # refusing is fine too: it just must not crash


def test_parse_number_directly():
    assert parse_number("FF", 16) == 255
    with pytest.raises(CalcError):
        parse_number("", 10)


# ----- wrapping to a word size -----

@pytest.mark.parametrize("value, bits, signed, wrapped, shown", [
    (255, 8, False, 255, 255),
    (255, 8, True, 255, -1),
    (-1, 8, False, 255, 255),
    (-1, 8, True, 255, -1),
    (256, 8, False, 0, 0),
    (128, 8, True, 128, -128),
    (127, 8, True, 127, 127),
    (-128, 8, True, 128, -128),
    (65535, 16, True, 65535, -1),
    (-1, 64, False, 2 ** 64 - 1, 2 ** 64 - 1),
    (-1, 64, True, 2 ** 64 - 1, -1),
    (2 ** 63, 64, True, 2 ** 63, -(2 ** 63)),
    (0, 32, True, 0, 0),
])
def test_represent(value, bits, signed, wrapped, shown):
    rep = represent(value, bits, signed)
    assert rep.wrapped == wrapped
    assert rep.shown == shown


@pytest.mark.parametrize("value, bits, signed, fits", [
    (255, 8, False, True),
    (255, 8, True, False),
    (256, 8, False, False),
    (-1, 8, False, False),
    (-128, 8, True, True),
    (-129, 8, True, False),
    (127, 8, True, True),
    (128, 8, True, False),
])
def test_fits(value, bits, signed, fits):
    assert represent(value, bits, signed).fits is fits


def test_both_interpretations_are_always_available():
    rep = represent(200, 8, False)
    assert (rep.unsigned, rep.signed) == (200, -56)
    assert rep.ones == 3


def test_not_in_a_word():
    # ~5 in 8 bits is 1111 1010
    rep = represent(evaluate_int("~5"), 8, False)
    assert format_binary(rep) == "1111 1010"
    assert format_hex(rep) == "FA"
    assert rep.signed == -6


# ----- showing it in each base -----

def test_formats():
    rep = represent(0xABCD, 16, False)
    assert format_hex(rep) == "ABCD"
    assert format_octal(rep) == "125715"
    assert format_binary(rep) == "1010 1011 1100 1101"


def test_binary_is_padded_to_the_full_word():
    assert format_binary(represent(5, 8, False)) == "0000 0101"
    assert format_binary(represent(0, 16, False)) == "0000 0000 0000 0000"
    assert format_binary(represent(1, 32, False)) == "0000 0000 0000 0000 0000 0000 0000 0001"


def test_binary_of_64_bits_uses_two_lines():
    lines = format_binary(represent(-1, 64, False)).split("\n")
    assert len(lines) == 2
    assert all(line == "1111 1111 1111 1111 1111 1111 1111 1111" for line in lines)


def test_hex_and_octal_have_no_leading_zeros():
    assert format_hex(represent(5, 64, False)) == "5"
    assert format_octal(represent(8, 64, False)) == "10"


# ----- the description line -----

def test_describe():
    text = describe(represent(200, 8, True))
    assert "8-bit" in text and "unsigned 200" in text and "signed -56" in text
    assert "3 of 8 bits set" in text
    assert "does not fit" in text                      # 200 does not fit in signed 8 bits


def test_describe_when_it_fits():
    assert "does not fit" not in describe(represent(100, 8, True))


def test_describe_mentions_the_exact_value_when_wrapping():
    text = describe(represent(300, 8, False))
    assert "300" in text and "wraps" in text


# ----- real-world checks -----

def test_subnet_mask():
    # a /24 network mask
    assert evaluate_int("0xFFFFFFFF << 8 & 0xFFFFFFFF") == 0xFFFFFF00
    assert format_hex(represent(evaluate_int("~0xFF"), 32, False)) == "FFFFFF00"


def test_rgb_colour_pieces():
    colour = 0xFF8040
    assert evaluate_int("(0xFF8040 >> 16) & 0xFF") == 0xFF
    assert evaluate_int("(0xFF8040 >> 8) & 0xFF") == 0x80
    assert evaluate_int("0xFF8040 & 0xFF") == 0x40
    assert colour == (0xFF << 16) | (0x80 << 8) | 0x40


def test_power_of_two_check():
    for n in (1, 2, 8, 64, 1024):
        assert evaluate_int(f"{n} & ({n} - 1)") == 0
    assert evaluate_int("6 & (6 - 1)") != 0