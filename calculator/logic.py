# calculator_logic.py
# The math for our calculator. No windows or buttons here.
# Instead of Python's eval(), we use our own small "parser" that reads
# the text and works out the answer step by step.

from __future__ import annotations

import math
import re
from typing import Callable

MAX_VALUE = 1e15  # answers bigger than this show "Number too large"


class CalcError(Exception):
    """Raised when a calculation cannot be done. The message is shown to the user."""


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

def format_number(value: float) -> str:
    """Turn a number into clean text. For example, 5.0 becomes '5'."""
    value = round(value, 10)  # fixes tiny errors like 0.1 + 0.2 = 0.30000000000000004
    if value == int(value):
        return str(int(value))
    # Show as a normal decimal and remove extra zeros at the end
    return f"{value:.10f}".rstrip("0").rstrip(".")


# ---------------------------------------------------------------------------
# The parser
# ---------------------------------------------------------------------------

# Trigonometry works in DEGREES, so sin(30) = 0.5
FUNCTIONS: dict[str, Callable[[float], float]] = {
    "sin": lambda x: math.sin(math.radians(x)),
    "cos": lambda x: math.cos(math.radians(x)),
    "tan": lambda x: math.tan(math.radians(x)),
    "log": math.log10,
    "ln": math.log,
    "exp": math.exp,
    "sqrt": math.sqrt,
    "cbrt": lambda x: math.copysign(abs(x) ** (1 / 3), x),
    "abs": abs,
    "floor": lambda x: float(math.floor(x)),
    "ceil": lambda x: float(math.ceil(x)),
    "round": lambda x: float(math.floor(x + 0.5) if x >= 0 else math.ceil(x - 0.5)),
    "sinh": math.sinh,
    "cosh": math.cosh,
    "tanh": math.tanh,
}

# These return degrees but are deliberately excluded from graph FUNCTIONS.
ANGLE_FUNCTIONS: dict[str, Callable[[float], float]] = {
    "asin": lambda x: math.degrees(math.asin(x)),
    "acos": lambda x: math.degrees(math.acos(x)),
    "atan": lambda x: math.degrees(math.atan(x)),
}

def _whole_number_allow_negative(value: float) -> int:
    if not math.isfinite(value):
        raise CalcError("Number too large")
    rounded = round(value)
    if abs(value - rounded) > 1e-9:
        raise CalcError("Invalid input")
    return int(rounded)

def _gcd_values(*values: float) -> float:
    return float(math.gcd(*(_whole_number_allow_negative(v) for v in values)))

def _lcm_values(*values: float) -> float:
    return float(math.lcm(*(_whole_number_allow_negative(v) for v in values)))

def _root(x: float, n: float) -> float:
    if not math.isfinite(n) or abs(n - round(n)) > 1e-9 or n == 0:
        raise ValueError("Invalid root")
    degree = int(round(n))
    if x < 0:
        if degree % 2 == 0:
            raise ValueError("Invalid root")
        return -((-x) ** (1 / degree))
    return x ** (1 / degree)

def _logb(x: float, base: float) -> float:
    if x <= 0 or base <= 0 or base == 1:
        raise ValueError("Invalid logarithm")
    return math.log(x, base)

MULTI_FUNCTIONS: dict[str, tuple[Callable[..., float], int, int | None]] = {
    "gcd": (_gcd_values, 2, None),
    "lcm": (_lcm_values, 2, None),
    "min": (min, 2, None),
    "max": (max, 2, None),
    "hypot": (math.hypot, 2, None),
    "angle": (lambda y, x: math.degrees(math.atan2(y, x)), 2, 2),
    "logb": (_logb, 2, 2),
    "root": (_root, 2, 2),
}


CONSTANTS: dict[str, float] = {
    "pi": math.pi,
    "e": math.e,
}

# ---------------------------------------------------------------------------
# Whole-number math: factorial (n!), combinations (nCr) and permutations (nPr)
# ---------------------------------------------------------------------------

MAX_FACTORIAL = 170      # 171! is too big to fit in a float
MAX_COUNT_SIZE = 1000    # for nCr and nPr: bigger n is slow, and the answers are huge anyway


def whole_number(value: float) -> int:
    """Turn a number into a whole number, or raise CalcError if it is not one."""
    if not math.isfinite(value):
        raise CalcError("Number too large")
    rounded = round(value)
    if abs(value - rounded) > 1e-9 or rounded < 0:
        raise CalcError("Invalid input")
    return int(rounded)


def factorial_of(value: float) -> float:
    """5 -> 120.  Only whole numbers from 0 upwards are allowed."""
    n = whole_number(value)
    if n > MAX_FACTORIAL:
        raise CalcError("Number too large")
    return float(math.factorial(n))


def count_selections(name: str, n_value: float, k_value: float) -> float:
    """nCr (name 'ncr'): ways to choose k things from n, order ignored.
    nPr (name 'npr'): ways to choose k things from n, order matters."""
    n = whole_number(n_value)
    k = whole_number(k_value)
    if k > n:
        raise CalcError("Invalid input")
    if n > MAX_COUNT_SIZE:
        raise CalcError("Number too large")
    try:
        result = math.comb(n, k) if name == "ncr" else math.perm(n, k)
        return float(result)
    except OverflowError:
        raise CalcError("Number too large")


# One token is a number, a word (like sin), or a single symbol (like +)
TOKEN_PATTERN = re.compile(r"\s*(?:(\d+\.?\d*|\.\d+)|([a-z]+)|(.))")


def tokenize(text: str) -> list[tuple[str, str]]:
    """Cut the text into pieces. Example: '2+sin(30)' -> numbers, words, symbols."""
    tokens: list[tuple[str, str]] = []
    position = 0
    text = text.rstrip()
    while position < len(text):
        match = TOKEN_PATTERN.match(text, position)
        if match is None:
            raise CalcError("Invalid input")
        number, word, symbol = match.groups()
        if number is not None:
            tokens.append(("number", number))
        elif word is not None:
            tokens.append(("word", word))
        else:
            tokens.append(("symbol", symbol))
        position = match.end()
    return tokens


class Parser:
    """Reads a list of tokens and calculates the answer.

    The rules (from weakest to strongest binding):
        expression  = term        (+ or -)       term ...
        term        = combination (* or /)       combination ...
        combination = factor      (nCr or nPr)   factor ...
        factor      = - factor   |   power
        power       = postfix  [ ^ factor ]
        postfix     = atom  [ ! ] ...
        atom        = number | constant | variable | function(expression) | (expression)
    """

    def __init__(self, tokens: list[tuple[str, str]], variables: dict[str, float]):
        self.tokens = tokens
        self.variables = variables
        self.position = 0

    # --- helpers to look at and move through the tokens ---

    def peek(self) -> str | None:
        """Look at the current symbol without moving. Returns None at the end."""
        if self.position < len(self.tokens):
            kind, value = self.tokens[self.position]
            return value if kind == "symbol" else None
        return None

    def peek_word(self) -> str | None:
        """Look at the current word (like ncr) without moving. None if it is not a word."""
        if self.position < len(self.tokens):
            kind, value = self.tokens[self.position]
            return value if kind == "word" else None
        return None

    def take(self) -> tuple[str, str]:
        """Return the current token and move to the next one."""
        if self.position >= len(self.tokens):
            raise CalcError("Invalid input")
        token = self.tokens[self.position]
        self.position += 1
        return token

    def expect(self, symbol: str) -> None:
        """The next token must be this symbol, otherwise it is an error."""
        if self.peek() != symbol:
            raise CalcError("Invalid input")
        self.position += 1

    # --- the grammar rules ---

    def parse(self) -> float:
        value = self.expression()
        if self.position != len(self.tokens):  # leftovers mean something is wrong
            raise CalcError("Invalid input")
        return value

    def expression(self) -> float:
        value = self.term()
        while self.peek() in ("+", "-"):
            operator = self.take()[1]
            right = self.term()
            value = value + right if operator == "+" else value - right
        return value

    def term(self) -> float:
        value = self.combination()
        while self.peek() in ("*", "/"):
            operator = self.take()[1]
            right = self.combination()
            if operator == "*":
                value = value * right
            else:
                if right == 0:
                    raise CalcError("Cannot divide by 0")
                value = value / right
        return value

    def combination(self) -> float:
        value = self.factor()
        while self.peek_word() in ("ncr", "npr"):
            name = self.take()[1]
            right = self.factor()
            value = count_selections(name, value, right)
        return value

    def factor(self) -> float:
        if self.peek() == "-":
            self.position += 1
            return -self.factor()
        return self.power()

    def postfix(self) -> float:
        value = self.atom()
        while self.peek() == "!":          # 5!  means 5 factorial
            self.position += 1
            value = factorial_of(value)
        return value

    def power(self) -> float:
        base = self.postfix()
        if self.peek() == "^":
            self.position += 1
            exponent = self.factor()  # the right side may be negative: 2^-3
            return safe_power(base, exponent)
        return base

    def atom(self) -> float:
        kind, value = self.take()

        if kind == "number":
            return float(value)

        if kind == "symbol" and value == "(":
            inner = self.expression()
            self.expect(")")
            return inner

        if kind == "word":
            if value in FUNCTIONS or value in ANGLE_FUNCTIONS:
                self.expect("(")
                argument = self.expression()
                self.expect(")")
                function = FUNCTIONS.get(value, ANGLE_FUNCTIONS.get(value))
                return apply_math_function(function, argument)
            if value in MULTI_FUNCTIONS:
                self.expect("(")
                arguments = [self.expression()]
                while self.peek() == ",":
                    self.position += 1
                    arguments.append(self.expression())
                self.expect(")")
                function, minimum, maximum = MULTI_FUNCTIONS[value]
                if len(arguments) < minimum or (maximum is not None and len(arguments) > maximum):
                    raise CalcError("Invalid input")
                return apply_multi_function(function, arguments)
            if value in CONSTANTS:
                return CONSTANTS[value]
            if value in self.variables:
                return self.variables[value]

        raise CalcError("Invalid input")


def apply_math_function(function: Callable[[float], float], argument: float) -> float:
    """Run sin, cos, log... and turn Python's errors into friendly ones."""
    try:
        return function(argument)
    except ValueError:      # for example log(0) or ln(-1)
        raise CalcError("Invalid input")
    except OverflowError:
        raise CalcError("Number too large")



def apply_multi_function(function: Callable[..., float], arguments: list[float]) -> float:
    """Run a multi-argument function and normalize Python errors."""
    try:
        return float(function(*arguments))
    except ZeroDivisionError:
        raise CalcError("Cannot divide by 0")
    except (ValueError, TypeError):
        raise CalcError("Invalid input")
    except OverflowError:
        raise CalcError("Number too large")


def safe_power(base: float, exponent: float) -> float:
    """Calculate base ^ exponent without crashing."""
    try:
        return math.pow(base, exponent)
    except OverflowError:
        raise CalcError("Number too large")
    except ValueError:      # for example (-8) ^ 0.5 or 0 ^ -1
        if base == 0 and exponent < 0:
            raise CalcError("Cannot divide by 0")
        raise CalcError("Invalid input")


def evaluate(expression: str, variables: dict[str, float] | None = None) -> float:
    """Calculate text like '2+3*4' and return a number.
    Raises CalcError (with a friendly message) if it cannot be done.
    'variables' lets other code supply values, such as {'x': 2.0} for graphs."""
    # Replace the symbols on our buttons with symbols the parser understands
    text = (
        expression.replace("×", "*").replace("÷", "/").replace("π", "pi")
        .replace("nCr", "ncr").replace("nPr", "npr")
    )
    try:
        tokens = tokenize(text)
        if not tokens:
            raise CalcError("Invalid input")
        result = Parser(tokens, variables or {}).parse()
    except RecursionError:      # absurdly deep brackets
        raise CalcError("Invalid input")
    except OverflowError:
        raise CalcError("Number too large")

    if not math.isfinite(result) or abs(result) > MAX_VALUE:
        raise CalcError("Number too large")
    return result


def calculate(expression: str) -> str:
    """Take text like '2+3*4' and return the answer (or an error message) as text."""
    if expression.strip() == "":
        return ""
    try:
        return format_number(evaluate(expression))
    except CalcError as error:
        return str(error)


# ---------------------------------------------------------------------------
# Helpers used by the % and scientific buttons
# ---------------------------------------------------------------------------

def find_last_number(expression: str) -> tuple[int, str] | None:
    """Find the last number in the text. Returns (start_position, number_text)."""
    match = re.search(r"\d+\.?\d*$|\.\d+$", expression)
    if match is None:
        return None

    start = match.start()
    # A minus sign belongs to the number if it is at the very start
    # or comes right after an operator or bracket (like the - in 5×-3)
    if start >= 1 and expression[start - 1] == "-":
        if start == 1 or expression[start - 2] in "+-×÷^(":
            start -= 1
    return start, expression[start:]


def apply_percent(expression: str) -> str:
    """Turn the last number into a percentage, like a phone calculator.

    After + or - it means a percentage OF what came before:
        50+20%   ->  50+10      (20% of 50)
        200-10%  ->  200-20     (10% of 200)
    Anywhere else it simply divides by 100:
        200×5%   ->  200×0.05
        50%      ->  0.5
    """
    found = find_last_number(expression)
    if found is None:
        return expression  # no number at the end, so do nothing

    start, number_text = found
    value = float(number_text)
    before = expression[:start]

    if len(before) > 1 and before[-1:] in ("+", "-"):
        try:
            base = evaluate(before[:-1])         # the part before the + or -
            return before + format_number(base * value / 100)
        except CalcError:
            pass                                 # not a clean calculation: just divide by 100

    return before + format_number(value / 100)


def apply_function(expression: str, name: str) -> tuple[str, str | None]:
    """Apply sqrt, square, reciprocal or negate to the last number.
    Returns (new_expression, error_message). error_message is None if all is well."""
    found = find_last_number(expression)
    if found is None:
        return expression, None  # nothing to work on

    start, number_text = found
    prefix = expression[:start]  # everything before the last number
    value = float(number_text)

    if name == "negate":
        if number_text.startswith("-"):
            new_text = prefix + number_text[1:]           # -5 becomes 5
        elif prefix.endswith("+"):
            new_text = prefix[:-1] + "-" + number_text    # 5+3 becomes 5-3
        elif prefix.endswith("-"):
            new_text = prefix[:-1] + "+" + number_text    # 5-3 becomes 5+3
        else:
            new_text = prefix + "-" + number_text         # 5 becomes -5
        return new_text, None

    try:
        if name == "sqrt":
            if value < 0:
                return expression, "Invalid input"
            result = math.sqrt(value)
        elif name == "square":
            result = value ** 2
        elif name == "reciprocal":
            if value == 0:
                return expression, "Cannot divide by 0"
            result = 1 / value
        else:
            return expression, "Invalid input"

        return prefix + format_number(result), None
    except (ValueError, OverflowError):
        return expression, "Invalid input"