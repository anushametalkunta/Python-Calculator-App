
import ast
import math
import operator

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

st.set_page_config(
    page_title="Python Calculator",
    page_icon="🧮",
    layout="wide",
)

st.markdown("""
<style>
.stApp {
    background: #101116;
    color: #f5f5f5;
}
section[data-testid="stSidebar"] {
    background: #252630;
}
.stButton button {
    border-radius: 9px;
    min-height: 42px;
}
div[data-testid="stTextInput"] input {
    background: #252630;
    color: white;
}
</style>
""", unsafe_allow_html=True)

st.title("🧮 Python Calculator")
st.caption("A modern calculator for calculations, graphs and conversions.")

st.sidebar.title("Calculator")
mode = st.sidebar.radio(
    "Choose a tool",
    [
        "Standard",
        "Scientific",
        "Graph Plotting",
        "Programming",
        "Unit Conversion",
    ],
)

# Safe arithmetic evaluator: no eval() or arbitrary Python execution.
BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
}

UNARY_OPERATORS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

FUNCTIONS = {
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    "log": math.log10,
    "ln": math.log,
    "abs": abs,
    "factorial": math.factorial,
    "exp": math.exp,
}

CONSTANTS = {
    "pi": math.pi,
    "e": math.e,
}


def calculate(expression):
    if len(expression) > 200:
        raise ValueError("Expression is too long.")

    tree = ast.parse(expression, mode="eval")

    def evaluate(node):
        if isinstance(node, ast.Expression):
            return evaluate(node.body)

        if isinstance(node, ast.Constant):
            if type(node.value) in (int, float):
                return node.value
            raise ValueError("Only numbers are allowed.")

        if isinstance(node, ast.Name):
            if node.id in CONSTANTS:
                return CONSTANTS[node.id]
            raise ValueError("Unknown constant.")

        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in BINARY_OPERATORS:
                raise ValueError("Unsupported operator.")

            left = evaluate(node.left)
            right = evaluate(node.right)

            if op_type is ast.Pow and abs(right) > 1000:
                raise ValueError("Exponent is too large.")

            result = BINARY_OPERATORS[op_type](left, right)
            return result

        if isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in UNARY_OPERATORS:
                raise ValueError("Unsupported operator.")
            return UNARY_OPERATORS[op_type](evaluate(node.operand))

        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            name = node.func.id
            if name not in FUNCTIONS or node.keywords:
                raise ValueError("Unsupported function.")

            args = [evaluate(arg) for arg in node.args]
            return FUNCTIONS[name](*args)

        raise ValueError("Invalid expression.")

    result = evaluate(tree)

    if isinstance(result, complex) or not math.isfinite(result):
        raise ValueError("Result is outside the supported range.")

    if abs(result) > 1e100:
        raise ValueError("Result is too large.")

    return result


if mode == "Standard":
    st.header("Standard Calculator")
    st.write("Use +, -, *, /, %, and parentheses.")

    expression = st.text_input(
        "Enter calculation",
        placeholder="Example: (10 + 5) * 2",
        key="standard_input",
    )

    if st.button("Calculate", type="primary"):
        try:
            st.success(f"Result: {calculate(expression)}")
        except Exception:
            st.error("Invalid calculation. Check your expression.")

elif mode == "Scientific":
    st.header("Scientific Calculator")
    st.write("Functions: sqrt, sin, cos, tan, log, ln, factorial")
    st.caption("Trigonometric functions use radians.")

    expression = st.text_input(
        "Enter scientific expression",
        placeholder="Example: sqrt(144) + sin(pi / 2)",
        key="scientific_input",
    )

    if st.button("Calculate", type="primary"):
        try:
            st.success(f"Result: {calculate(expression)}")
        except Exception:
            st.error("Invalid expression or unsupported calculation.")

elif mode == "Graph Plotting":
    st.header("Graph Plotting")
    st.write("Plot one or more functions of x.")

    formulas = st.text_input(
        "Enter formula(s), separated by semicolons",
        value="x**2; x + 2; sin(x)",
    )
    x_min = st.number_input("X minimum", value=-10.0)
    x_max = st.number_input("X maximum", value=10.0)

    if st.button("Plot Graph", type="primary"):
        try:
            if x_min >= x_max:
                raise ValueError("X minimum must be less than X maximum.")

            import sympy as sp

            x = sp.symbols("x")
            allowed = {
                "x": x,
                "sin": sp.sin,
                "cos": sp.cos,
                "tan": sp.tan,
                "sqrt": sp.sqrt,
                "log": sp.log,
                "exp": sp.exp,
                "pi": sp.pi,
            }

            fig, ax = plt.subplots()
            fig.patch.set_facecolor("#101116")
            ax.set_facecolor("#252630")
            ax.tick_params(colors="white")
            ax.xaxis.label.set_color("white")
            ax.yaxis.label.set_color("white")
            ax.title.set_color("white")

            xs = np.linspace(x_min, x_max, 800)

            for formula in formulas.split(";"):
                formula = formula.strip()
                if not formula:
                    continue

                expr = sp.sympify(formula, locals=allowed)
                if not expr.free_symbols.issubset({x}):
                    raise ValueError("Only x is allowed as a variable.")

                fn = sp.lambdify(x, expr, modules=["numpy"])
                ys = np.asarray(fn(xs))

                if ys.ndim == 0:
                    ys = np.full_like(xs, ys.item())

                ys = np.broadcast_to(ys, xs.shape).astype(float)
                ys[~np.isfinite(ys)] = np.nan
                ys[np.abs(ys) > 1e6] = np.nan

                ax.plot(xs, ys, label=formula)

            ax.axhline(0, color="gray", linewidth=0.8)
            ax.axvline(0, color="gray", linewidth=0.8)
            ax.grid(True, alpha=0.2)
            ax.legend()
            ax.set_xlabel("x")
            ax.set_ylabel("y")
            ax.set_title("Function Graphs")
            st.pyplot(fig)
            plt.close(fig)

        except Exception:
            st.error("Could not plot the formulas. Check the syntax.")

elif mode == "Programming":
    st.header("Programming Number Converter")

    number = st.number_input(
        "Enter a non-negative integer",
        min_value=0,
        step=1,
        value=10,
    )
    number = int(number)

    st.code(
        f"Decimal:     {number}\n"
        f"Binary:      {bin(number)}\n"
        f"Octal:       {oct(number)}\n"
        f"Hexadecimal: {hex(number)}"
    )

elif mode == "Unit Conversion":
    st.header("Unit Conversion")

    category = st.selectbox(
        "Choose category",
        ["Length", "Weight", "Temperature"],
    )

    if category == "Length":
        units = {
            "Meters": 1,
            "Kilometers": 1000,
            "Centimeters": 0.01,
            "Miles": 1609.344,
            "Feet": 0.3048,
            "Inches": 0.0254,
        }

        value = st.number_input("Value", value=1.0)
        col1, col2 = st.columns(2)

        source = col1.selectbox("From", list(units))
        target = col2.selectbox("To", list(units), index=1)

        if st.button("Convert", type="primary"):
            result = value * units[source] / units[target]
            st.success(f"{value:g} {source} = {result:g} {target}")

    elif category == "Weight":
        units = {
            "Kilograms": 1,
            "Grams": 0.001,
            "Pounds": 0.45359237,
            "Ounces": 0.028349523125,
        }

        value = st.number_input("Value", value=1.0)
        col1, col2 = st.columns(2)

        source = col1.selectbox("From", list(units))
        target = col2.selectbox("To", list(units), index=1)

        if st.button("Convert", type="primary"):
            result = value * units[source] / units[target]
            st.success(f"{value:g} {source} = {result:g} {target}")

    else:
        value = st.number_input("Temperature value", value=0.0)
        col1, col2 = st.columns(2)

        source = col1.selectbox(
            "From", ["Celsius", "Fahrenheit", "Kelvin"]
        )
        target = col2.selectbox(
            "To", ["Celsius", "Fahrenheit", "Kelvin"]
        )

        if st.button("Convert", type="primary"):
            if source == "Celsius":
                celsius = value
            elif source == "Fahrenheit":
                celsius = (value - 32) * 5 / 9
            else:
                celsius = value - 273.15

            if target == "Celsius":
                result = celsius
            elif target == "Fahrenheit":
                result = celsius * 9 / 5 + 32
            else:
                result = celsius + 273.15

            st.success(f"{value:g}° {source} = {result:g}° {target}")

st.sidebar.divider()
st.sidebar.caption("Python Calculator • Web Edition")
