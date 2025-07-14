import logging
from .parser import LogicParser, LogicExpressionError

logger = logging.getLogger(__name__)

class ONPError(Exception):
    pass

def to_onp(expr: str) -> str:
    try:
        std = LogicParser.parse(expr)
    except LogicExpressionError as e:
        logger.error(f"Błąd parsera: {e}")
        raise ONPError(f"Błąd parsera: {e}")
    output = []
    stack = []
    # Priorytety operatorów (wyższa liczba = wyższy priorytet)
    priors = {"¬": 5, "∧": 4, "∨": 3, "→": 2, "↔": 1}
    right_assoc = {"¬"}
    i = 0
    while i < len(std):
        ch = std[i]
        if ch in LogicParser.VALID_VARS:
            output.append(ch)
        elif ch == '(': 
            stack.append(ch)
        elif ch == ')':
            while stack and stack[-1] != '(': 
                output.append(stack.pop())
            if not stack:
                logger.error("Niezamknięty nawias w ONP")
                raise ONPError("Niezamknięty nawias")
            stack.pop()
        elif ch in priors:
            while (stack and stack[-1] != '(' and
                   (priors.get(stack[-1], 0) > priors[ch] or
                    (priors.get(stack[-1], 0) == priors[ch] and ch not in right_assoc))):
                output.append(stack.pop())
            stack.append(ch)
        else:
            logger.error(f"Nieprawidłowy znak w ONP: {ch}")
            raise ONPError(f"Nieprawidłowy znak: {ch}")
        i += 1
    while stack:
        if stack[-1] == '(': 
            logger.error("Niezamknięty nawias na końcu ONP")
            raise ONPError("Niezamknięty nawias")
        output.append(stack.pop())
    return ' '.join(output) 