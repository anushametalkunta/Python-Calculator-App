# calculator/units.py
# Unit conversion math. There are no windows here, so it can be tested.

from __future__ import annotations

from .logic import CalcError, evaluate

# For every category: how many "base units" one of each unit is.
# (The base units are: metre, kilogram, metre per second, square metre,
#  litre, second and byte.) Every factor is an exact, official definition.
LINEAR_UNITS: dict[str, dict[str, float]] = {
    "Length": {
        "mm": 0.001, "cm": 0.01, "m": 1.0, "km": 1000.0,
        "in": 0.0254, "ft": 0.3048, "yd": 0.9144, "mi": 1609.344, "nmi": 1852.0,
    },
    "Mass": {
        "mg": 1e-6, "g": 0.001, "kg": 1.0, "t": 1000.0,
        "oz": 0.028349523125, "lb": 0.45359237, "st": 6.35029318,
    },
    "Speed": {
        "m/s": 1.0, "km/h": 1 / 3.6, "mph": 0.44704, "kn": 1852 / 3600, "ft/s": 0.3048,
    },
    "Area": {
        "mm²": 1e-6, "cm²": 1e-4, "m²": 1.0, "km²": 1e6, "ha": 10000.0,
        "in²": 0.00064516, "ft²": 0.09290304, "yd²": 0.83612736,
        "acre": 4046.8564224, "mi²": 2589988.110336,
    },
    "Volume": {
        "mL": 0.001, "L": 1.0, "m³": 1000.0,
        "tsp": 0.00492892159375, "tbsp": 0.01478676478125, "fl oz": 0.0295735295625,
        "cup": 0.2365882365, "pt": 0.473176473, "qt": 0.946352946, "gal": 3.785411784,
    },
    "Time": {
        "ms": 0.001, "s": 1.0, "min": 60.0, "h": 3600.0, "day": 86400.0,
        "week": 604800.0, "year": 31536000.0,
    },
    "Data": {
        "bit": 0.125, "B": 1.0, "KB": 1e3, "MB": 1e6, "GB": 1e9, "TB": 1e12,
        "KiB": 1024.0, "MiB": 1024.0 ** 2, "GiB": 1024.0 ** 3, "TiB": 1024.0 ** 4,
    },
}

TEMPERATURE_UNITS = ("°C", "°F", "K")
ABSOLUTE_ZERO_C = -273.15

CATEGORY_NAMES = [
    "Length", "Mass", "Temperature", "Speed", "Area", "Volume", "Time", "Data",
]

# The two units shown when you open a category
DEFAULT_UNITS = {
    "Length": ("km", "mi"),
    "Mass": ("kg", "lb"),
    "Temperature": ("°C", "°F"),
    "Speed": ("km/h", "mph"),
    "Area": ("m²", "ft²"),
    "Volume": ("L", "gal"),
    "Time": ("h", "min"),
    "Data": ("GB", "MB"),
}


def units_for(category: str) -> list[str]:
    """The unit names of a category, in the order they are shown."""
    if category == "Temperature":
        return list(TEMPERATURE_UNITS)
    if category in LINEAR_UNITS:
        return list(LINEAR_UNITS[category])
    raise CalcError("Unknown category")


def to_celsius(value: float, unit: str) -> float:
    """Any temperature -> degrees Celsius (and nothing can be below absolute zero)."""
    if unit == "°C":
        celsius = value
    elif unit == "°F":
        celsius = (value - 32) * 5 / 9
    elif unit == "K":
        celsius = value - 273.15
    else:
        raise CalcError("Unknown unit")
    if celsius < ABSOLUTE_ZERO_C - 1e-9:
        raise CalcError("Below absolute zero")
    return celsius


def from_celsius(celsius: float, unit: str) -> float:
    """Degrees Celsius -> any temperature."""
    if unit == "°C":
        return celsius
    if unit == "°F":
        return celsius * 9 / 5 + 32
    if unit == "K":
        return celsius + 273.15
    raise CalcError("Unknown unit")


def convert(value: float, category: str, from_unit: str, to_unit: str) -> float:
    """Convert a number from one unit to another in the same category."""
    if category == "Temperature":
        return from_celsius(to_celsius(value, from_unit), to_unit)

    units = LINEAR_UNITS.get(category)
    if units is None or from_unit not in units or to_unit not in units:
        raise CalcError("Unknown unit")
    return value * units[from_unit] / units[to_unit]


def parse_amount(text: str) -> float:
    """Read the number typed by the user. Calculations like 2*3 or 1/4 are fine."""
    return evaluate(text.replace(",", ""))


def format_result(value: float) -> str:
    """A short, clean text for a result: at most 10 significant digits."""
    if value == 0:
        return "0"
    return f"{value:.10g}"


def ratio_text(category: str, from_unit: str, to_unit: str) -> str:
    """For example: '1 km = 0.6213711922 mi'."""
    one = convert(1.0, category, from_unit, to_unit)
    return f"1 {from_unit} = {format_result(one)} {to_unit}"