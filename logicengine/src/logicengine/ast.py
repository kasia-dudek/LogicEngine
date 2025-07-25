import logging
from .parser import LogicParser, LogicExpressionError

logger = logging.getLogger(__name__)

class ASTError(Exception):
    pass

def generate_ast(expr: str):
    try:
        std = LogicParser.parse(expr)
    except LogicExpressionError as e:
        logger.error(f"Błąd parsera: {e}")
        raise ASTError(f"Błąd parsera: {e}")
    # Rekurencyjny parser do AST
    def parse_expr(s):
        # Pomocnicze funkcje
        def find_main_operator(s):
            min_prio = 100
            idx = -1
            depth = 0
            for i, ch in enumerate(s):
                if ch == '(': depth += 1
                elif ch == ')': depth -= 1
                elif depth == 0 and ch in OP_PRIOS:
                    prio = OP_PRIOS[ch]
                    if prio <= min_prio:
                        min_prio = prio
                        idx = i
            return idx
        s = s.strip()
        if not s:
            logger.error('Puste wyrażenie')
            raise ASTError("Puste wyrażenie")
        # Zdejmuj zewnętrzne nawiasy tylko jeśli całe wyrażenie jest w nawiasach
        while s and s[0] == '(' and s[-1] == ')' and LogicParser._check_parentheses(s):
            depth = 0
            is_outer = True
            for i, ch in enumerate(s):
                if ch == '(': depth += 1
                elif ch == ')': depth -= 1
                if depth == 0 and i != len(s) - 1:
                    is_outer = False
                    break
            if is_outer:
                s = s[1:-1].strip()
            else:
                break
        if s and s[0] == '¬':
            node = {"node": "¬", "child": parse_expr(s[1:])}
            return node
        idx = find_main_operator(s)
        if idx == -1:
            if s in LogicParser.VALID_VARS:
                return s
            logger.error(f'Nieprawidłowy atom: {s}')
            raise ASTError(f"Nieprawidłowy atom: {s}")
        op = s[idx]
        left = s[:idx]
        right = s[idx+1:]
        if op in {"∧", "∨", "→", "↔", "⊕", "↑", "↓", "≡"}:
            node = {"node": op, "left": parse_expr(left), "right": parse_expr(right)}
            return node
        logger.error(f'Nieznany operator: {op}')
        raise ASTError(f"Nieznany operator: {op}")
    # Priorytety operatorów (niższa liczba = niższy priorytet)
    OP_PRIOS = {"↔": 1, "≡": 1, "→": 2, "⊕": 3, "↑": 3, "↓": 3, "∨": 4, "∧": 5}
    # ¬ jest unarny, obsługiwany osobno
    try:
        return parse_expr(std)
    except ASTError as e:
        logger.error(f"Błąd AST: {e}")
        raise 