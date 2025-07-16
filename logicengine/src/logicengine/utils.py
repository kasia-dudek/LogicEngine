import logging
from typing import List

logger = logging.getLogger(__name__)

def to_bin(m: int, n: int) -> str:
    """Zamienia liczbę na binarny string o długości n."""
    return format(m, f'0{n}b')

def bin_to_expr(b: str, vars: List[str]) -> str:
    """Zamienia zapis binarny z '-' na wyrażenie logiczne (np. '1-0' -> 'A∧¬C')."""
    terms = []
    for i, ch in enumerate(b):
        if ch == '-':
            continue
        if ch == '1':
            terms.append(vars[i])
        elif ch == '0':
            terms.append(f'¬{vars[i]}')
    expr = '∧'.join(terms) if terms else '1'
    logger.info(f"bin_to_expr: {b} -> {expr}")
    return expr

def count_literals(b: str) -> int:
    """Zlicza liczbę literałów w binarnym stringu (bez '-')."""
    return sum(1 for ch in b if ch != '-') 