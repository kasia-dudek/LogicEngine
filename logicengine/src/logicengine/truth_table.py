from typing import List, Dict, Any
from itertools import product
from .parser import LogicParser, LogicExpressionError

class TruthTableError(Exception):
    pass

def _replace_operators(expr: str) -> str:
    """Zamienia operatory logiczne na odpowiedniki Pythona."""
    return (
        expr.replace('¬', ' not ')
            .replace('∧', ' and ')
            .replace('∨', ' or ')
            .replace('→', ' <= ')
            .replace('↔', ' == ')
    )

def generate_truth_table(expr: str, force_vars: List[str] = None) -> List[Dict[str, Any]]:
    """Generuje tabelę prawdy dla wyrażenia logicznego.

    Args:
        expr (str): Wyrażenie logiczne.
        force_vars (List[str], optional): Lista zmiennych do użycia w tabeli.

    Returns:
        List[Dict[str, Any]]: Tabela prawdy jako lista słowników.
    """
    try:
        parsed_expr = LogicParser.parse(expr)
    except LogicExpressionError as e:
        raise TruthTableError(f"Błąd parsowania wyrażenia: {e}")

    vars = force_vars if force_vars else sorted(set(ch for ch in parsed_expr if ch.isalpha()))
    if not vars and expr not in {'0', '1'}:
        raise TruthTableError("Brak zmiennych w wyrażeniu.")

    table = []
    # Użyj standardowej kolejności binarnej: 00, 01, 10, 11
    order = list(product([0, 1], repeat=len(vars)))

    for idx, values in enumerate(order):
        row = {var: val for var, val in zip(vars, values)}
        if expr == '0':
            row['result'] = 0
        elif expr == '1':
            row['result'] = 1
        else:
            eval_expr = _replace_operators(parsed_expr)
            for var, val in row.items():
                eval_expr = eval_expr.replace(var, str(val))
            try:
                row['result'] = int(eval(eval_expr, {"__builtins__": {}}, {
                    "and": lambda x, y: x and y,
                    "or": lambda x, y: x or y,
                    "not": lambda x: not x
                }))
            except Exception as e:
                raise TruthTableError(f"Błąd ewaluacji wyrażenia: {e}")
        table.append(row)
    return table