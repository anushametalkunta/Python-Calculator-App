
from flask import Flask, jsonify, request, send_from_directory
import ast
import math
import operator

app = Flask(__name__, static_folder="web", static_url_path="")

OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
}

UNARY = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

FUNCTIONS = {
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log10,
    "ln": math.log,
    "abs": abs,
    "exp": math.exp,
}

CONSTANTS = {
    "pi": math.pi,
    "e": math.e,
}


def safe_calculate(expression):
    if not isinstance(expression, str) or len(expression) > 200:
        raise ValueError("Invalid expression.")

    tree = ast.parse(expression, mode="eval")

    def evaluate(node):
        if isinstance(node, ast.Expression):
            return evaluate(node.body)

        if isinstance(node, ast.Constant):
            if type(node.value) in (int, float):
                return node.value
            raise ValueError("Numbers only.")

        if isinstance(node, ast.Name):
            if node.id in CONSTANTS:
                return CONSTANTS[node.id]
            raise ValueError("Unknown constant.")

        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in OPERATORS:
                raise ValueError("Unsupported operator.")

            left = evaluate(node.left)
            right = evaluate(node.right)

            if op_type is ast.Pow and abs(right) > 100:
                raise ValueError("Exponent is too large.")

            return OPERATORS[op_type](left, right)

        if isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in UNARY:
                raise ValueError("Unsupported operator.")
            return UNARY[op_type](evaluate(node.operand))

        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            name = node.func.id
            if name not in FUNCTIONS or node.keywords:
                raise ValueError("Unsupported function.")

            args = [evaluate(arg) for arg in node.args]
            return FUNCTIONS[name](*args)

        raise ValueError("Invalid expression.")

    result = evaluate(tree)

    if isinstance(result, complex) or not math.isfinite(result):
        raise ValueError("Result is not a finite real number.")

    if abs(result) > 1e100:
        raise ValueError("Result is too large.")

    return result


@app.route("/")
def home():
    return send_from_directory("web", "index.html")


@app.route("/api/calculate", methods=["POST"])
def calculate():
    data = request.get_json(silent=True) or {}

    try:
        result = safe_calculate(data.get("expression"))
        return jsonify({"result": result})
    except (ValueError, TypeError, SyntaxError, ZeroDivisionError, OverflowError):
        return jsonify({"error": "Invalid calculation. Check your expression."}), 400


if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)