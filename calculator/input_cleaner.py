# calculator/input_cleaner.py
# Cleans up text pasted from the clipboard so it is safe to put on the calculator.

from __future__ import annotations

from .logic import CONSTANTS, FUNCTIONS, CalcError, tokenize

MAX_PASTE_LENGTH = 100
WORD_OPERATORS = ("ncr", "npr")        # 5 nCr 2 and 5 nPr 2

# Different "minus" and "times" characters people may copy from web pages
REPLACEMENTS = {
    "−": "-",   # the true minus sign
    "–": "-",   # en dash
    "—": "-",   # em dash
    "·": "×",
}


def clean_pasted_text(text: str) -> str:
    """Return calculator-ready text, or '' if the text is not a calculation.

    Examples:  '1,234.5' -> '1234.5'    '2*3' -> '2×3'    '5 ncr 2' -> '5nCr2'
               'hello' -> ''
    """
    cleaned = text.lower()
    cleaned = "".join(cleaned.split())          # remove spaces, tabs and new lines
    cleaned = cleaned.replace(",", "")          # 1,234.5 -> 1234.5
    cleaned = cleaned.replace("**", "^")

    for old, new in REPLACEMENTS.items():
        cleaned = cleaned.replace(old, new)

    cleaned = cleaned.replace("*", "×").replace("/", "÷").replace("pi", "π")
    cleaned = cleaned.replace("ncr", "nCr").replace("npr", "nPr")

    if cleaned == "" or len(cleaned) > MAX_PASTE_LENGTH:
        return ""

    # Check every piece with the same tokenizer the calculator uses
    check = cleaned.lower().replace("×", "*").replace("÷", "/").replace("π", "pi")
    try:
        tokens = tokenize(check)
    except CalcError:
        return ""

    for kind, value in tokens:
        if (
            kind == "word"
            and value not in FUNCTIONS
            and value not in CONSTANTS
            and value not in WORD_OPERATORS
        ):
            return ""
        if kind == "symbol" and value not in "+-*/^()!":
            return ""

    return cleaned