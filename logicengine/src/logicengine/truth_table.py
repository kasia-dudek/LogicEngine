from sympy import symbols, sympify
from typing import List, Dict
from .parser import LogicParser, LogicExpressionError

class TruthTableError(Exception):
    pass

def _expr_to_sympy(expr: str):
    # Zamiana operatorów na sympy
    expr = expr.replace('¬', '~').replace('∧', '&').replace('∨', '|').replace('→', '>>').replace('↔', '==')
    return expr

def generate_truth_table(expr: str) -> List[Dict[str, bool]]:
    try:
        std = LogicParser.parse(expr)
    except LogicExpressionError as e:
        raise TruthTableError(f"Błąd parsera: {e}")
    # Wyodrębnij zmienne
    vars = sorted(set([ch for ch in std if ch in LogicParser.VALID_VARS]))
    if len(vars) > 4:
        raise TruthTableError("Obsługiwane są maksymalnie 4 zmienne.")
    expr_sympy = _expr_to_sympy(std)
    syms = symbols(vars)
    try:
        s_expr = sympify(expr_sympy, locals={v: s for v, s in zip(vars, syms)})
    except Exception as e:
        raise TruthTableError(f"Błąd konwersji do sympy: {e}")
    table = []
    for i in range(2 ** len(vars)):
        vals = [(i >> j) & 1 == 1 for j in reversed(range(len(vars)))]
        env = dict(zip(vars, vals))
        try:
            result = bool(s_expr.subs(env))
        except Exception as e:
            raise TruthTableError(f"Błąd ewaluacji: {e}")
        row = {**env, 'result': result}
        table.append(row)
    return table 