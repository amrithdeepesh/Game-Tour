import re


_TOKEN = re.compile(r"\s*(?:(\d+(?:\.\d*)?|\.\d+)|([()+\-*/]))")
_PRECEDENCE = {"+": 1, "-": 1, "*": 2, "/": 2, "u+": 3, "u-": 3}


def evaluate_simple_expression(expression):
    """Evaluate basic arithmetic with a shunting-yard operator stack."""
    if not isinstance(expression, str) or not expression.strip():
        raise ValueError("Enter a valid arithmetic expression.")

    output, operators = [], []
    position, expect_operand, saw_token = 0, True, False
    while position < len(expression):
        if not expression[position:].strip():
            break
        match = _TOKEN.match(expression, position)
        if match is None:
            raise ValueError("Only numbers and +, -, *, /, and parentheses are supported.")
        position = match.end()
        number, symbol = match.groups()
        saw_token = True

        if number is not None:
            if not expect_operand:
                raise ValueError("Enter an operator between numbers.")
            output.append(float(number) if "." in number else int(number))
            expect_operand = False
            continue

        if symbol == "(":
            if not expect_operand:
                raise ValueError("Enter an operator before the opening parenthesis.")
            operators.append(symbol)
            continue

        if symbol == ")":
            if expect_operand:
                raise ValueError("The expression is incomplete.")
            while operators and operators[-1] != "(":
                output.append(operators.pop())
            if not operators:
                raise ValueError("Parentheses do not match.")
            operators.pop()
            expect_operand = False
            continue

        operator = "u" + symbol if expect_operand and symbol in "+-" else symbol
        if expect_operand and operator == symbol:
            raise ValueError("The expression is incomplete.")
        while operators and operators[-1] != "(":
            top = operators[-1]
            higher = _PRECEDENCE[top] > _PRECEDENCE[operator]
            same_and_left_associative = (
                _PRECEDENCE[top] == _PRECEDENCE[operator]
                and operator not in ("u+", "u-")
            )
            if not (higher or same_and_left_associative):
                break
            output.append(operators.pop())
        operators.append(operator)
        expect_operand = True

    if not saw_token or expect_operand:
        raise ValueError("The expression is incomplete.")
    while operators:
        operator = operators.pop()
        if operator == "(":
            raise ValueError("Parentheses do not match.")
        output.append(operator)

    values = []
    for token in output:
        if not isinstance(token, str):
            values.append(token)
        elif token in ("u+", "u-"):
            if not values:
                raise ValueError("The expression is incomplete.")
            value = values.pop()
            values.append(value if token == "u+" else -value)
        else:
            if len(values) < 2:
                raise ValueError("The expression is incomplete.")
            right, left = values.pop(), values.pop()
            if token == "/" and right == 0:
                raise ValueError("Division by zero is not allowed.")
            operation = {
                "+": lambda: left + right,
                "-": lambda: left - right,
                "*": lambda: left * right,
                "/": lambda: left / right,
            }[token]
            values.append(operation())

    if len(values) != 1:
        raise ValueError("Enter a valid arithmetic expression.")
    return values[0]
