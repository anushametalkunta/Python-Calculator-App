# calculator/app.py
# Puts the pieces together: the classic or modern calculator, plus the extra features.

from __future__ import annotations

from .graph_feature import GraphMixin
from .math_feature import MoreMathMixin
from .programmer_feature import ProgrammerMixin
from .units_feature import UnitsMixin


def build_app_class(modern: bool):
    """Return the calculator class to use.
    modern=True needs CustomTkinter and raises ImportError if it is missing."""
    if modern:
        from .modern_ui import ModernCalculatorApp as Base
    else:
        from .ui import CalculatorApp as Base

    class App(ProgrammerMixin, UnitsMixin, GraphMixin, MoreMathMixin, Base):
        modern_widgets = modern

    return App