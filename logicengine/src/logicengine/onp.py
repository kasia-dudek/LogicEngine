# onp.py
"""Convert a logical expression to RPN (ONP) using shunting-yard."""

import logging

logger = logging.getLogger(__name__)


class ONPError(Exception):
    pass


def to_onp(expr: str) -> str:
    # single syntax check (no extra parsing)

    output = []
    stack = []

    # operator precedence (higher = tighter)
    prec = {"¬": 5, "∧": 4, "∨": 3, "⊕": 3, "↑": 3, "↓": 3, "→": 2, "←": 2, "↔": 1, "≡": 1}
    right_assoc = {"¬", "→", "←", "↔", "≡"}

    i = 0
    n = len(expr)
    while i < n:
        ch = expr[i]

        if ch.isspace():
            i += 1
            continue

        if ch.isalpha() or ch in "01":
            output.append(ch)

        elif ch == "(":
            stack.append(ch)

        elif ch == ")":
            while stack and stack[-1] != "(":
                output.append(stack.pop())
            if not stack:
                logger.error("Niezamknięty nawias")
                raise ONPError("Niezamknięty nawias")
            stack.pop()  # drop '('

        elif ch in prec:
            while (
                stack
                and stack[-1] != "("
                and (
                    prec.get(stack[-1], 0) > prec[ch]
                    or (prec.get(stack[-1], 0) == prec[ch] and ch not in right_assoc)
                )
            ):
                output.append(stack.pop())
            stack.append(ch)

        else:
            logger.error(f"Nieprawidłowy znak: {ch}")
            raise ONPError(f"Nieprawidłowy znak: {ch}")

        i += 1

    while stack:
        if stack[-1] == "(":
            logger.error("Niezamknięty nawias")
            raise ONPError("Niezamknięty nawias")
        output.append(stack.pop())

    return " ".join(output)
