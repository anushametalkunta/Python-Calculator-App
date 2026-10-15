# tests/test_units.py
# Tests for the unit converter math (units.py). No windows are needed.

import pytest

from calculator.logic import CalcError
from calculator.units import (
    CATEGORY_NAMES,
    DEFAULT_UNITS,
    convert,
    format_result,
    parse_amount,
    ratio_text,
    units_for,
)


# ----- well-known conversions -----

@pytest.mark.parametrize("category, value, from_unit, to_unit, expected", [
    ("Length", 1, "mi", "km", 1.609344),
    ("Length", 1, "in", "cm", 2.54),
    ("Length", 100, "cm", "m", 1),
    ("Length", 1, "ft", "in", 12),
    ("Length", 1, "yd", "ft", 3),
    ("Length", 1, "nmi", "m", 1852),
    ("Length", 5, "km", "mi", 3.1068559611866697),
    ("Mass", 1, "kg", "lb", 2.2046226218487757),
    ("Mass", 1, "lb", "oz", 16),
    ("Mass", 1, "st", "lb", 14),
    ("Mass", 1, "t", "kg", 1000),
    ("Speed", 60, "mph", "m/s", 26.8224),
    ("Speed", 36, "km/h", "m/s", 10),
    ("Speed", 1, "kn", "km/h", 1.852),
    ("Area", 1, "acre", "m²", 4046.8564224),
    ("Area", 1, "ha", "m²", 10000),
    ("Area", 1, "ft²", "in²", 144),
    ("Volume", 1, "gal", "L", 3.785411784),
    ("Volume", 1, "gal", "qt", 4),
    ("Volume", 1, "cup", "fl oz", 8),
    ("Volume", 1, "m³", "L", 1000),
    ("Volume", 3, "tsp", "tbsp", 1),
    ("Time", 1, "h", "s", 3600),
    ("Time", 1, "day", "h", 24),
    ("Time", 1, "week", "day", 7),
    ("Data", 8, "bit", "B", 1),
    ("Data", 1, "KiB", "B", 1024),
    ("Data", 1, "GiB", "MiB", 1024),
    ("Data", 1, "GB", "MB", 1000),
])
def test_known_conversions(category, value, from_unit, to_unit, expected):
    assert convert(value, category, from_unit, to_unit) == pytest.approx(expected)


@pytest.mark.parametrize("value, from_unit, to_unit, expected", [
    (100, "°C", "°F", 212),
    (0, "°C", "°F", 32),
    (212, "°F", "°C", 100),
    (-40, "°C", "°F", -40),
    (-40, "°F", "°C", -40),
    (0, "°C", "K", 273.15),
    (0, "K", "°C", -273.15),
    (373.15, "K", "°C", 100),
    (98.6, "°F", "°C", 37),
    (0, "K", "°F", -459.67),
])
def test_temperature(value, from_unit, to_unit, expected):
    assert convert(value, "Temperature", from_unit, to_unit) == pytest.approx(expected)


# ----- the same unit, and zero -----

def test_same_unit_changes_nothing():
    assert convert(42.5, "Length", "km", "km") == pytest.approx(42.5)
    assert convert(42.5, "Temperature", "°C", "°C") == pytest.approx(42.5)


def test_zero_stays_zero():
    assert convert(0, "Mass", "kg", "lb") == 0


def test_negative_numbers_work_for_normal_units():
    assert convert(-5, "Length", "km", "m") == pytest.approx(-5000)


# ----- going there and back always gives the original number -----

def test_every_unit_pair_round_trips():
    for category in CATEGORY_NAMES:
        units = units_for(category)
        for from_unit in units:
            for to_unit in units:
                there = convert(123.456, category, from_unit, to_unit)
                back = convert(there, category, to_unit, from_unit)
                assert back == pytest.approx(123.456), (category, from_unit, to_unit)


# ----- errors never crash -----

@pytest.mark.parametrize("value, unit", [(-300, "°C"), (-500, "°F"), (-1, "K")])
def test_below_absolute_zero(value, unit):
    with pytest.raises(CalcError):
        convert(value, "Temperature", unit, "°C")


def test_absolute_zero_itself_is_fine():
    assert convert(-273.15, "Temperature", "°C", "K") == pytest.approx(0)


def test_unknown_things_are_rejected():
    with pytest.raises(CalcError):
        convert(1, "Length", "km", "banana")
    with pytest.raises(CalcError):
        convert(1, "Length", "banana", "km")
    with pytest.raises(CalcError):
        convert(1, "Colors", "red", "blue")
    with pytest.raises(CalcError):
        convert(1, "Temperature", "°C", "furlong")
    with pytest.raises(CalcError):
        units_for("Colors")


def test_units_from_the_wrong_category_are_rejected():
    with pytest.raises(CalcError):
        convert(1, "Length", "km", "kg")


# ----- the list of categories and units -----

def test_every_category_has_units_and_defaults():
    assert len(CATEGORY_NAMES) == 8
    for category in CATEGORY_NAMES:
        units = units_for(category)
        assert len(units) >= 3
        assert len(set(units)) == len(units)          # no duplicates
        first, second = DEFAULT_UNITS[category]
        assert first in units and second in units and first != second


# ----- reading the typed number -----

@pytest.mark.parametrize("text, expected", [
    ("5", 5),
    ("2.5", 2.5),
    ("-3", -3),
    ("1,234.5", 1234.5),
    ("1/4", 0.25),
    ("2*3", 6),
    ("2×3", 6),
    ("  7  ", 7),
    ("pi", 3.141592653589793),
])
def test_parse_amount(text, expected):
    assert parse_amount(text) == pytest.approx(expected)


@pytest.mark.parametrize("text", ["abc", "5+", "1/0", "", "1e5x", "9" * 20])
def test_bad_amounts_are_rejected(text):
    with pytest.raises(CalcError):
        parse_amount(text)


# ----- showing the result -----

@pytest.mark.parametrize("value, expected", [
    (0, "0"),
    (-0.0, "0"),
    (1000, "1000"),
    (2.54, "2.54"),
    (1 / 3, "0.3333333333"),
    (1.0000000000001, "1"),
    (1e-7, "1e-07"),
    (-12.5, "-12.5"),
    (212.00000000000003, "212"),
])
def test_format_result(value, expected):
    assert format_result(value) == expected


def test_ratio_text():
    assert ratio_text("Length", "km", "m") == "1 km = 1000 m"
    assert ratio_text("Temperature", "°C", "°F") == "1 °C = 33.8 °F"
    assert ratio_text("Length", "mi", "km") == "1 mi = 1.609344 km"