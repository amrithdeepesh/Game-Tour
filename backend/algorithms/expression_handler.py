import re
from data_structures.stack import Stack

_TOKEN = re.compile(r"\s*(?:(\d+(?:\.\d*)?|\.\d+)|([()+\-*/^]))")
_PRECEDENCE = {"+": 1, "-": 1, "*": 2, "/": 2, "^": 3, "u+": 4, "u-": 4}


def parse_and_convert(expression):
    """
    Convert infix expression to postfix using a custom Linked-List Stack.
    Returns:
        postfix (list): tokens in postfix notation
        conversion_steps (list of dict): step-by-step trace showing token, action, and stack state
    """
    if not isinstance(expression, str) or not expression.strip():
        raise ValueError("Enter a valid arithmetic expression.")

    output = []
    op_stack = Stack()
    conversion_steps = []
    position, expect_operand, saw_token = 0, True, False

    while position < len(expression):
        if not expression[position:].strip():
            break
        match = _TOKEN.match(expression, position)
        if match is None:
            raise ValueError(
                "Only numbers and +, -, *, /, ^, and parentheses are supported."
            )
        position = match.end()
        number, symbol = match.groups()
        saw_token = True

        if number is not None:
            if not expect_operand:
                raise ValueError("Enter an operator between numbers.")
            num_val = float(number) if "." in number else int(number)
            output.append(num_val)
            expect_operand = False
            conversion_steps.append({
                "step": len(conversion_steps) + 1,
                "token": str(number),
                "type": "Operand",
                "action": f"Append operand {number} to output",
                "stack": op_stack.display(),
                "output": " ".join(str(x) for x in output)
            })
            continue

        if symbol == "(":
            if not expect_operand:
                raise ValueError("Enter an operator before the opening parenthesis.")
            op_stack.push(symbol)
            conversion_steps.append({
                "step": len(conversion_steps) + 1,
                "token": "(",
                "type": "Left Parenthesis",
                "action": "Push '(' onto operator stack",
                "stack": op_stack.display(),
                "output": " ".join(str(x) for x in output)
            })
            continue

        if symbol == ")":
            if expect_operand:
                raise ValueError("The expression is incomplete.")
            while not op_stack.is_empty() and op_stack.peek() != "(":
                popped = op_stack.pop()
                output.append(popped)
                conversion_steps.append({
                    "step": len(conversion_steps) + 1,
                    "token": ")",
                    "type": "Right Parenthesis",
                    "action": f"Pop '{popped}' from stack to output",
                    "stack": op_stack.display(),
                    "output": " ".join(str(x) for x in output)
                })
            if op_stack.is_empty():
                raise ValueError("Parentheses do not match.")
            op_stack.pop()  # discard '('
            conversion_steps.append({
                "step": len(conversion_steps) + 1,
                "token": ")",
                "type": "Right Parenthesis",
                "action": "Pop and discard matching '('",
                "stack": op_stack.display(),
                "output": " ".join(str(x) for x in output)
            })
            expect_operand = False
            continue

        # Operator handling (+, -, *, /, ^, or unary +/-)
        operator = "u" + symbol if expect_operand and symbol in "+-" else symbol
        if expect_operand and operator == symbol:
            raise ValueError("The expression is incomplete.")

        while not op_stack.is_empty() and op_stack.peek() != "(":
            top = op_stack.peek()
            higher = _PRECEDENCE[top] > _PRECEDENCE[operator]
            same_and_left_associative = (
                _PRECEDENCE[top] == _PRECEDENCE[operator]
                and operator not in ("u+", "u-", "^")
            )
            if not (higher or same_and_left_associative):
                break
            popped = op_stack.pop()
            output.append(popped)
            conversion_steps.append({
                "step": len(conversion_steps) + 1,
                "token": operator,
                "type": "Operator Precedence",
                "action": f"Pop higher/equal precedence '{popped}' to output",
                "stack": op_stack.display(),
                "output": " ".join(str(x) for x in output)
            })

        op_stack.push(operator)
        conversion_steps.append({
            "step": len(conversion_steps) + 1,
            "token": operator,
            "type": "Operator",
            "action": f"Push '{operator}' onto operator stack",
            "stack": op_stack.display(),
            "output": " ".join(str(x) for x in output)
        })
        expect_operand = True

    if not saw_token or expect_operand:
        raise ValueError("The expression is incomplete.")

    while not op_stack.is_empty():
        operator = op_stack.pop()
        if operator == "(":
            raise ValueError("Parentheses do not match.")
        output.append(operator)
        conversion_steps.append({
            "step": len(conversion_steps) + 1,
            "token": "EOF",
            "type": "Flush Stack",
            "action": f"Pop remaining operator '{operator}' to output",
            "stack": op_stack.display(),
            "output": " ".join(str(x) for x in output)
        })

    return output, conversion_steps


def evaluate_postfix(postfix_tokens):
    """
    Evaluate postfix tokens using a custom Linked-List Stack.
    Returns:
        result (float/int): calculated value
        evaluation_steps (list of dict): step-by-step trace showing token, action, and operand stack
    """
    val_stack = Stack()
    evaluation_steps = []

    for token in postfix_tokens:
        if not isinstance(token, str):
            val_stack.push(token)
            evaluation_steps.append({
                "step": len(evaluation_steps) + 1,
                "token": str(token),
                "type": "Operand",
                "action": f"Push {token} onto value stack",
                "stack": val_stack.display()
            })
        elif token in ("u+", "u-"):
            if val_stack.is_empty():
                raise ValueError("The expression is incomplete.")
            value = val_stack.pop()
            new_val = value if token == "u+" else -value
            val_stack.push(new_val)
            evaluation_steps.append({
                "step": len(evaluation_steps) + 1,
                "token": token,
                "type": "Unary Operator",
                "action": f"Apply unary {token} to {value} -> {new_val}",
                "stack": val_stack.display()
            })
        else:
            if len(val_stack) < 2:
                raise ValueError("The expression is incomplete.")
            right = val_stack.pop()
            left = val_stack.pop()
            if token == "/" and right == 0:
                raise ValueError("Division by zero is not allowed.")
            if token == "+":
                res = left + right
            elif token == "-":
                res = left - right
            elif token == "*":
                res = left * right
            elif token == "/":
                res = left / right
            elif token == "^":
                res = left ** right
            else:
                raise ValueError(f"Unsupported operator: {token}")

            val_stack.push(res)
            evaluation_steps.append({
                "step": len(evaluation_steps) + 1,
                "token": token,
                "type": "Binary Operator",
                "action": f"Compute {left} {token} {right} = {res}",
                "stack": val_stack.display()
            })

    if len(val_stack) != 1:
        raise ValueError("Enter a valid arithmetic expression.")

    return val_stack.pop(), evaluation_steps


def evaluate_simple_expression(expression):
    """Evaluate basic arithmetic with a shunting-yard operator stack. Backward-compatible function."""
    postfix, _ = parse_and_convert(expression)
    result, _ = evaluate_postfix(postfix)
    return result


def evaluate_expression_detailed(expression):
    """Full shunting-yard infix-to-postfix and postfix evaluation with comprehensive traces for Data Structures Lab."""
    postfix, conv_steps = parse_and_convert(expression)
    result, eval_steps = evaluate_postfix(postfix)
    clean_postfix = " ".join(str(t) for t in postfix)
    return {
        "expression": expression,
        "postfix": clean_postfix,
        "result": result,
        "conversion_steps": conv_steps,
        "evaluation_steps": eval_steps,
    }
