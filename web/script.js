
const display = document.getElementById("display");
const keys = document.getElementById("keys");

let expression = "";
let justCalculated = false;

function updateDisplay(value = expression) {
    display.textContent = value || "0";
}

function clearCalculator() {
    expression = "";
    justCalculated = false;
    updateDisplay();
}

function deleteLast() {
    expression = expression.slice(0, -1);
    justCalculated = false;
    updateDisplay();
}

function addValue(value) {
    if (justCalculated && /[0-9.]/.test(value)) {
        expression = "";
    }

    justCalculated = false;
    expression += value;
    updateDisplay();
}

// Safe arithmetic parser. Does not use eval().
function evaluateExpression(input) {
    const tokens = input.match(
        /\d*\.?\d+(?:e[+-]?\d+)?|[()+\-*/%]/gi
    );

    if (!tokens || tokens.join("") !== input.replace(/\s/g, "")) {
        throw new Error("Invalid expression");
    }

    let position = 0;

    function parseExpression() {
        let value = parseTerm();

        while (tokens[position] === "+" || tokens[position] === "-") {
            const op = tokens[position++];
            const right = parseTerm();
            value = op === "+" ? value + right : value - right;
        }

        return value;
    }

    function parseTerm() {
        let value = parseUnary();

        while (["*", "/", "%"].includes(tokens[position])) {
            const op = tokens[position++];
            const right = parseUnary();

            if ((op === "/" || op === "%") && right === 0) {
                throw new Error("Cannot divide by zero");
            }

            if (op === "*") value *= right;
            if (op === "/") value /= right;
            if (op === "%") value %= right;
        }

        return value;
    }

    function parseUnary() {
        if (tokens[position] === "+") {
            position++;
            return parseUnary();
        }

        if (tokens[position] === "-") {
            position++;
            return -parseUnary();
        }

        return parsePrimary();
    }

    function parsePrimary() {
        const token = tokens[position++];

        if (token === "(") {
            const value = parseExpression();

            if (tokens[position++] !== ")") {
                throw new Error("Missing closing parenthesis");
            }

            return value;
        }

        if (token === undefined || !/^\d/.test(token) && !token.startsWith(".")) {
            throw new Error("Invalid number");
        }

        return Number(token);
    }

    const result = parseExpression();

    if (position !== tokens.length || !Number.isFinite(result)) {
        throw new Error("Invalid calculation");
    }

    return result;
}


async function calculate() {
    if (!expression) return;

    try {
        const result = await calculateUsingPython(expression);

        expression = String(Number(Number(result).toPrecision(12)));
        updateDisplay(expression);
        justCalculated = true;
    } catch (error) {
        updateDisplay("Invalid calculation");
        console.error("Python calculation error:", error);
        justCalculated = false;
    }
}


keys.addEventListener("click", (event) => {
    const button = event.target.closest("button");
    if (!button) return;

    if (button.dataset.action === "clear") {
        clearCalculator();
        return;
    }

    if (button.dataset.action === "delete") {
        deleteLast();
        return;
    }

    if (button.dataset.action === "equals") {
        calculate();
        return;
    }

    if (button.dataset.action === "sign") {
        if (!expression) {
            expression = "-";
        } else if (justCalculated) {
            expression = String(-Number(expression));
        } else {
            expression = `-(${expression})`;
        }

        justCalculated = false;
        updateDisplay();
        return;
    }

    if (button.dataset.value !== undefined) {
        addValue(button.dataset.value);
    }
});

// Keyboard support
document.addEventListener("keydown", (event) => {
    if (event.target.matches("input, select")) return;

    if (/^[0-9.]$/.test(event.key)) {
        addValue(event.key);
    } else if (["+", "-", "*", "/", "%", "(", ")"].includes(event.key)) {
        addValue(event.key);
    } else if (event.key === "Enter" || event.key === "=") {
        event.preventDefault();
        calculate();
    } else if (event.key === "Backspace") {
        deleteLast();
    } else if (event.key === "Escape") {
        clearCalculator();
    }
});

// Sidebar navigation
document.querySelectorAll(".mode").forEach((button) => {
    button.addEventListener("click", () => {
        document.querySelectorAll(".mode").forEach((item) => {
            item.classList.remove("active");
        });

        button.classList.add("active");

        document.querySelectorAll(".panel").forEach((panel) => {
            panel.classList.add("hidden");
        });

        document.getElementById(button.dataset.mode).classList.remove("hidden");
    });
});


document.querySelectorAll("[data-fn]").forEach((button) => {
    button.addEventListener("click", () => {
        const input = document.getElementById("sci-input");
        const output = document.getElementById("sci-result");
        const mode = document.getElementById("angle-mode").value;

        if (input.value.trim() === "") {
            output.textContent = "Please enter a number.";
            return;
        }

        const x = Number(input.value);
        const toRadians = value =>
            mode === "deg" ? value * Math.PI / 180 : value;
        const fromRadians = value =>
            mode === "deg" ? value * 180 / Math.PI : value;

        let result;

        switch (button.dataset.fn) {
            case "sqrt":
                result = Math.sqrt(x);
                break;
            case "square":
                result = x ** 2;
                break;
            case "cube":
                result = x ** 3;
                break;
            case "sin":
                result = Math.sin(toRadians(x));
                break;
            case "cos":
                result = Math.cos(toRadians(x));
                break;
            case "tan":
                result = Math.tan(toRadians(x));
                break;
            case "asin":
                result = fromRadians(Math.asin(x));
                break;
            case "acos":
                result = fromRadians(Math.acos(x));
                break;
            case "atan":
                result = fromRadians(Math.atan(x));
                break;
            case "log":
                result = Math.log10(x);
                break;
            case "ln":
                result = Math.log(x);
                break;
            case "reciprocal":
                result = 1 / x;
                break;
            case "exp":
                result = Math.exp(x);
                break;
            case "abs":
                result = Math.abs(x);
                break;
            case "factorial":
                if (!Number.isInteger(x) || x < 0 || x > 170) {
                    output.textContent =
                        "Factorial requires a whole number from 0 to 170.";
                    return;
                }

                result = 1;
                for (let i = 2; i <= x; i++) {
                    result *= i;
                }
                break;
            default:
                output.textContent = "Unknown function.";
                return;
        }

        if (!Number.isFinite(result)) {
            output.textContent =
                "This calculation is outside the supported range.";
            return;
        }

        output.textContent =
            `Result: ${Number(result.toPrecision(10))}`;
    });
});

// Programming conversions
document.getElementById("program-button").addEventListener("click", () => {
    const input = document.getElementById("program-number");
    const output = document.getElementById("program-output");
    const value = Number(input.value);

    if (
        input.value.trim() === "" ||
        !Number.isSafeInteger(value) ||
        value < 0
    ) {
        output.textContent = "Enter a valid non-negative whole number.";
        return;
    }

    output.textContent =
        `Decimal: ${value}\n` +
        `Binary: ${value.toString(2)}\n` +
        `Octal: ${value.toString(8)}\n` +
        `Hexadecimal: ${value.toString(16).toUpperCase()}`;
});

// Length conversions
const lengthFactors = {
    km: 1000,
    m: 1,
    cm: 0.01,
    mi: 1609.344
};

document.getElementById("unit-button").addEventListener("click", () => {
    const value = Number(document.getElementById("unit-value").value);
    const source = document.getElementById("unit-from").value;
    const target = document.getElementById("unit-to").value;
    const output = document.getElementById("unit-result");

    if (document.getElementById("unit-value").value.trim() === "" ||
        !Number.isFinite(value)) {
        output.textContent = "Enter a valid number.";
        return;
    }

    const result = value * lengthFactors[source] / lengthFactors[target];

    output.textContent =
        `Result: ${Number(result.toPrecision(10))} ${target}`;
});


const graphButton = document.getElementById("graph-button");

graphButton.addEventListener("click", () => {
    const input = document.getElementById("graph-input").value;
    const min = Number(document.getElementById("graph-min").value);
    const max = Number(document.getElementById("graph-max").value);
    const output = document.getElementById("graph-output");

    if (!window.Plotly) {
        output.textContent = "Graph library could not load. Check your internet connection.";
        return;
    }

    if (!Number.isFinite(min) || !Number.isFinite(max) || min >= max) {
        output.textContent = "X minimum must be smaller than X maximum.";
        return;
    }

    const formulas = input.split(";").map(f => f.trim()).filter(Boolean);

    if (!formulas.length || formulas.length > 8) {
        output.textContent = "Enter between 1 and 8 functions.";
        return;
    }

    const xs = [];
    const count = 500;

    for (let i = 0; i < count; i++) {
        xs.push(min + (max - min) * i / (count - 1));
    }

    const traces = [];

    try {
        for (const formula of formulas) {
            const ys = xs.map(x => evaluateGraphFormula(formula, x));

            traces.push({
                x: xs,
                y: ys,
                mode: "lines",
                type: "scatter",
                name: formula
            });
        }

        output.innerHTML = '<div id="graph-chart" style="width:100%;height:480px;"></div>';

        Plotly.newPlot(
            "graph-chart",
            traces,
            {
                title: "Function Graphs",
                paper_bgcolor: "#20232d",
                plot_bgcolor: "#20232d",
                font: { color: "#f5f6fa" },
                xaxis: { title: "x", gridcolor: "#414452", zerolinecolor: "#85899a" },
                yaxis: { title: "y", gridcolor: "#414452", zerolinecolor: "#85899a" },
                margin: { t: 55, r: 25, b: 55, l: 55 },
                legend: { orientation: "h" }
            },
            { responsive: true }
        );
    } catch (error) {
        output.textContent = "Invalid function. Use expressions such as x^2, x+2, sin(x), cos(x), or sqrt(x).";
    }
});

// A small arithmetic parser for graph functions.
// Supported: x, numbers, +, -, *, /, ^, parentheses,
// sin, cos, tan, sqrt, abs, log, ln, and pi.
function evaluateGraphFormula(formula, x) {
    const source = formula
        .replace(/\s+/g, "")
        .replace(/\^/g, "**")
        .replace(/\bpi\b/gi, "PI");

    const tokens = source.match(
        /(?:\d+\.?\d*|\.\d+)(?:e[+-]?\d+)?|PI|x|[a-zA-Z]+|\*\*|[()+\-*/]/gi
    );

    if (!tokens || tokens.join("") !== source) {
        throw new Error("Invalid characters");
    }

    let position = 0;

    const functions = {
        sin: Math.sin,
        cos: Math.cos,
        tan: Math.tan,
        sqrt: Math.sqrt,
        abs: Math.abs,
        log: Math.log10,
        ln: Math.log
    };

    function primary() {
        const token = tokens[position++];

        if (token === "(") {
            const value = addSub();
            if (tokens[position++] !== ")") throw new Error("Missing )");
            return value;
        }

        if (token === "x") return x;
        if (token.toUpperCase() === "PI") return Math.PI;

        if (/^\d/.test(token) || token.startsWith(".")) {
            return Number(token);
        }

        const name = token.toLowerCase();

        if (functions[name]) {
            if (tokens[position++] !== "(") throw new Error("Expected (");
            const value = addSub();
            if (tokens[position++] !== ")") throw new Error("Expected )");
            return functions[name](value);
        }

        throw new Error("Unsupported function");
    }

    function unary() {
        if (tokens[position] === "+") {
            position++;
            return unary();
        }

        if (tokens[position] === "-") {
            position++;
            return -unary();
        }

        return primary();
    }

    function power() {
        const left = unary();

        if (tokens[position] === "**") {
            position++;
            return left ** power();
        }

        return left;
    }

    function multiplyDivide() {
        let value = power();

        while (tokens[position] === "*" || tokens[position] === "/") {
            const op = tokens[position++];
            const right = power();
            value = op === "*" ? value * right : value / right;
        }

        return value;
    }

    function addSub() {
        let value = multiplyDivide();

        while (tokens[position] === "+" || tokens[position] === "-") {
            const op = tokens[position++];
            const right = multiplyDivide();
            value = op === "+" ? value + right : value - right;
        }

        return value;
    }

    const result = addSub();

    if (position !== tokens.length) throw new Error("Invalid expression");

    return Number.isFinite(result) && Math.abs(result) < 1e12
        ? result
        : null;
}
async function calculateUsingPython(expression) {
    const response = await fetch("/api/calculate", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ expression: expression })
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.error || "Calculation failed");
    }

    return data.result;
}