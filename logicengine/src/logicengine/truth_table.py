# truth_table.py
"""Generate a truth table for a logical expression."""

from typing import List, Dict, Any, Optional
from itertools import product

from .onp import to_onp


class TruthTableError(Exception):
    pass


def _vars_in_expr(expr: str) -> List[str]:
    return sorted({ch for ch in expr if ch.isalpha()})


def _eval_rpn(tokens: List[str], env: Dict[str, int]) -> int:
    """Evaluate ONP (RPN) tokens with 0/1 integers."""
    s: List[int] = []

    def b(x: int) -> int:  # clamp to 0/1
        return 1 if x else 0

    for t in tokens:
        if not t:
            continue
        if t.isalpha():  # variable
            s.append(env.get(t, 0))
        elif t in {"0", "1"}:
            s.append(int(t))
        elif t == "¬":
            if not s:
                raise TruthTableError("Błędne wyrażenie (negacja).")
            a = s.pop()
            s.append(b(not a))
        elif t in {"∧", "∨", "⊕", "↑", "↓", "→", "←", "↔", "≡"}:
            if len(s) < 2:
                raise TruthTableError(f"Błędne wyrażenie (operator binarny {t}): za mało argumentów na stosie.")
            b2, b1 = s.pop(), s.pop()

            if t == "∧":
                s.append(b(b1 and b2))
            elif t == "∨":
                s.append(b(b1 or b2))
            elif t == "⊕":
                s.append(b(b1 != b2))
            elif t == "↑":  # NAND
                s.append(b(not (b1 and b2)))
            elif t == "↓":  # NOR
                s.append(b(not (b1 or b2)))
            elif t == "→":  # implication
                s.append(b((not b1) or b2))
            elif t == "←":  # reverse implication (b2 -> b1)
                s.append(b((not b2) or b1))
            elif t in {"↔", "≡"}:  # equivalence
                s.append(b(b1 == b2))
        else:
            raise TruthTableError(f"Nieznany token: {t}")

    if len(s) != 1:
        raise TruthTableError(f"Błędne wyrażenie (stos): pozostało {len(s)} elementów na stosie.")
    return s[0]


def generate_truth_table(expr: str, force_vars: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Return a truth table as a list of rows: {A:0,...,'result':0}."""

    vars_ = force_vars if force_vars is not None else _vars_in_expr(expr)
    if not vars_ and expr not in {"0", "1"}:
        raise TruthTableError("Brak zmiennych w wyrażeniu.")

    if expr in {"0", "1"}:
        val = int(expr)
        return [{"result": val}] if not vars_ else [
            {**{v: a[i] for i, v in enumerate(vars_)}, "result": val}
            for a in product([0, 1], repeat=len(vars_))
        ]

    rpn = to_onp(expr).split()

    table: List[Dict[str, Any]] = []
    for assign in product([0, 1], repeat=len(vars_)):  # 00, 01, 10, 11...
        env = {v: assign[i] for i, v in enumerate(vars_)}
        result = _eval_rpn(rpn, env)
        table.append({**env, "result": result})

    return table
