import ast
import operator

_OPERATORS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv, ast.USub: operator.neg, ast.UAdd: operator.pos}

def evaluate_simple_expression(expression):
    """Evaluate numeric arithmetic safely with normal operator precedence."""
    try:
        tree = ast.parse(expression, mode="eval")
    except (SyntaxError, TypeError) as exc:
        raise ValueError("Enter a valid arithmetic expression.") from exc

    def visit(node):
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
            left, right = visit(node.left), visit(node.right)
            if isinstance(node.op, ast.Div) and right == 0:
                raise ValueError("Division by zero is not allowed.")
            return _OPERATORS[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp) and type(node.op) in _OPERATORS:
            return _OPERATORS[type(node.op)](visit(node.operand))
        raise ValueError("Only numbers and +, -, *, /, and parentheses are supported.")
    return visit(tree)
