# calculator/programmer.py
# The math behind Programmer mode: whole-number calculations with bit
# operations, and showing a number in binary, octal, decimal and hexadecimal.
# There are no windows here, so everything can be tested.

from __future__ import annotations

import re
from dataclasses import dataclass

from .logic import CalcError

WORD_SIZES = (8, 16, 32, 64)
BASE_NUMBERS = {"DEC": 10, "HEX": 16, "OCT": 8, "BIN": 2}
BASE_LABELS = {10: "decimal", 16: "hexadecimal", 8: "octal", 2: "binary"}

MAX_EXPRESSION_LENGTH = 200
MAX_BITS = 4096        # a result with more bits than this is refused
MAX_SHIFT = 1024       # the biggest shift to the left we allow

# The words you can type instead of symbols: 6 AND 3, 1 SHL 4, ...
WORD_OPERATORS = {
    "and": "&", "or": "|", "xor": "^", "not": "~",
    "mod": "%", "shl": "<<", "shr": ">>",
}
WORD_PATTERN = re.compile(r"(?:and|or|xor|not|mod|shl|shr)\b", re.IGNORECASE)
RUN_PATTERN = re.compile(r"[0-9A-Za-z_]+")
PREFIX_BASES = {"0x": 16, "0b": 2, "0o": 8}
DIGITS = {
    2: set("01"),
    8: set("01234567"),
    10: set("0123456789"),
    16: set("0123456789abcdefABCDEF"),
}


# ---------------------------------------------------------------------------
# Reading the text
# ---------------------------------------------------------------------------

def parse_number(run: str, base: int) -> int:
    """Read one number. A prefix (0x, 0b, 0o) overrides the input base,
    except in hexadecimal, where 0b... and 0o... are just hex digits."""
    text = run.replace("_", "")
    prefix = text[:2].lower()
    use_base = base
    if prefix in PREFIX_BASES and not (base == 16 and prefix != "0x"):
        use_base = PREFIX_BASES[prefix]
        text = text[2:]
    if text == "" or any(char not in DIGITS[use_base] for char in text):
        raise CalcError(f"Not a valid {BASE_LABELS[use_base]} number: {run}")
    return int(text, use_base)


def tokenize_int(text: str, base: int) -> list[tuple[str, object]]:
    """Cut the text into numbers ('num') and operators ('op')."""
    tokens: list[tuple[str, object]] = []
    position = 0
    while position < len(text):
        char = text[position]
        if char.isspace():
            position += 1
            continue

        word = WORD_PATTERN.match(text, position)
        if word:
            tokens.append(("op", WORD_OPERATORS[word.group().lower()]))
            position = word.end()
            continue

        run = RUN_PATTERN.match(text, position)
        if run:
            tokens.append(("num", check_size(parse_number(run.group(), base))))
            position = run.end()
            continue

        if text[position:position + 2] in ("<<", ">>"):
            tokens.append(("op", text[position:position + 2]))
            position += 2
            continue
        if char in "+-*/%&|^~()":
            tokens.append(("op", char))
            position += 1
            continue
        raise CalcError(f"Unexpected character: {char}")
    return tokens


# ---------------------------------------------------------------------------
# The parser (the same idea as the calculator's, with C-style precedence)
# ---------------------------------------------------------------------------

def check_size(value: int) -> int:
    """Refuse absurdly large numbers, so nothing can freeze the window."""
    if value.bit_length() > MAX_BITS:
        raise CalcError("Number too large")
    return value


def apply_operator(operator: str, a: int, b: int) -> int:
    """Do one operation on two whole numbers."""
    if operator == "+":
        result = a + b
    elif operator == "-":
        result = a - b
    elif operator == "*":
        result = a * b
    elif operator in ("/", "%"):
        if b == 0:
            raise CalcError("Cannot divide by 0")
        quotient = abs(a) // abs(b)              # like C: cut off towards zero
        if (a < 0) != (b < 0):
            quotient = -quotient
        result = quotient if operator == "/" else a - b * quotient
    elif operator == "<<":
        if b < 0:
            raise CalcError("Invalid input")
        if b > MAX_SHIFT:
            raise CalcError("Shift too large")
        result = a << b
    elif operator == ">>":
        if b < 0:
            raise CalcError("Invalid input")
        result = a >> min(b, MAX_BITS + 1)
    elif operator == "&":
        result = a & b
    elif operator == "|":
        result = a | b
    elif operator == "^":
        result = a ^ b
    else:
        raise CalcError("Invalid input")
    return check_size(result)


class IntParser:
    """Works out whole-number expressions.

    From weakest to strongest:  |   ^   &   << >>   + -   * / %   unary - + ~
    """

    LEVELS = (("|",), ("^",), ("&",), ("<<", ">>"), ("+", "-"), ("*", "/", "%"))

    def __init__(self, tokens: list[tuple[str, object]]):
        self.tokens = tokens
        self.position = 0

    def peek_operator(self) -> str | None:
        if self.position < len(self.tokens):
            kind, value = self.tokens[self.position]
            if kind == "op":
                return value
        return None

    def parse(self) -> int:
        if not self.tokens:
            raise CalcError("Invalid input")
        value = self.level(0)
        if self.position != len(self.tokens):
            raise CalcError("Invalid input")
        return value

    def level(self, index: int) -> int:
        if index == len(self.LEVELS):
            return self.unary()
        value = self.level(index + 1)
        while self.peek_operator() in self.LEVELS[index]:
            operator = self.tokens[self.position][1]
            self.position += 1
            right = self.level(index + 1)
            value = apply_operator(operator, value, right)
        return value

    def unary(self) -> int:
        operator = self.peek_operator()
        if operator in ("-", "+", "~"):
            self.position += 1
            value = self.unary()
            if operator == "-":
                value = -value
            elif operator == "~":
                value = ~value
            return check_size(value)
        return self.primary()

    def primary(self) -> int:
        if self.position >= len(self.tokens):
            raise CalcError("Invalid input")
        kind, value = self.tokens[self.position]
        self.position += 1
        if kind == "num":
            return value
        if kind == "op" and value == "(":
            inner = self.level(0)
            if self.peek_operator() != ")":
                raise CalcError("Invalid input")
            self.position += 1
            return inner
        raise CalcError("Invalid input")


def evaluate_int(text: str, base: int = 10) -> int:
    """Calculate a whole-number expression. Numbers are read in 'base'
    unless they have a 0x, 0b or 0o prefix. Raises CalcError if it fails."""
    text = text.strip()
    if len(text) > MAX_EXPRESSION_LENGTH:
        raise CalcError("Expression is too long")
    try:
        return IntParser(tokenize_int(text, base)).parse()
    except RecursionError:
        raise CalcError("Invalid input")


# ---------------------------------------------------------------------------
# Showing a number in different bases, at a chosen word size
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Representation:
    """One number as it looks in a word of 'bits' bits."""

    raw: int            # the exact result of the calculation
    bits: int           # 8, 16, 32 or 64
    signed_mode: bool   # show the decimal value as signed?
    wrapped: int        # the bit pattern as an unsigned number (0 .. 2^bits - 1)
    unsigned: int
    signed: int
    shown: int          # unsigned or signed, depending on signed_mode
    fits: bool          # False if the exact value did not fit and had to wrap
    ones: int           # how many bits are 1


def represent(value: int, bits: int, signed_mode: bool) -> Representation:
    """Wrap a whole number to a word size (two's complement) and describe it."""
    mask = (1 << bits) - 1
    wrapped = value & mask
    signed = wrapped - (1 << bits) if wrapped >> (bits - 1) else wrapped
    if signed_mode:
        fits = -(1 << (bits - 1)) <= value < (1 << (bits - 1))
    else:
        fits = 0 <= value <= mask
    return Representation(
        raw=value,
        bits=bits,
        signed_mode=signed_mode,
        wrapped=wrapped,
        unsigned=wrapped,
        signed=signed,
        shown=signed if signed_mode else wrapped,
        fits=fits,
        ones=bin(wrapped).count("1"),
    )


def format_hex(rep: Representation) -> str:
    return f"{rep.wrapped:X}"


def format_octal(rep: Representation) -> str:
    return f"{rep.wrapped:o}"


def format_binary(rep: Representation) -> str:
    """The full bit pattern in groups of four, at most 32 bits per line."""
    digits = format(rep.wrapped, f"0{rep.bits}b")
    groups = [digits[i:i + 4] for i in range(0, rep.bits, 4)]
    lines = [" ".join(groups[i:i + 8]) for i in range(0, len(groups), 8)]
    return "\n".join(lines)


def describe(rep: Representation) -> str:
    """A short line of facts about the number."""
    text = (
        f"{rep.bits}-bit   unsigned {rep.unsigned}   signed {rep.signed}"
        f"   {rep.ones} of {rep.bits} bits set"
    )
    if not rep.fits:
        text += f"\nThe exact value {rep.raw} does not fit in {rep.bits} bits, so it wraps."
    return text