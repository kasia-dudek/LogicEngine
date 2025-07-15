import logging
from .parser import LogicParser, LogicExpressionError
from .truth_table import generate_truth_table, TruthTableError
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class KMapError(Exception):
    pass

def simplify_kmap(expr: str) -> Dict[str, Any]:
    steps = []
    try:
        std = LogicParser.parse(expr)
        table = generate_truth_table(expr)
    except (LogicExpressionError, TruthTableError) as e:
        logger.error(f"Błąd parsera lub tabeli prawdy: {e}")
        raise KMapError(f"Błąd parsera lub tabeli prawdy: {e}")
    vars = sorted([k for k in table[0] if k != 'result'])
    n = len(vars)
    if n < 1 or n > 4:
        logger.error("Zbyt wiele lub za mało zmiennych dla Mapy Karnaugh")
        raise KMapError("Obsługiwane są wyrażenia z 1-4 zmiennymi")
    # Krok 1: mintermy
    minterms = [i for i, row in enumerate(table) if row['result']]
    steps.append({"step": "Find minterms", "minterms": minterms})
    # Krok 2: utwórz mapę Karnaugh (2D)
    kmap, kmap_order = _generate_kmap(minterms, n)
    steps.append({"step": "Create K-map", "kmap": kmap, "order": kmap_order})
    # Krok 3: grupowanie (prosta implementacja: pojedyncze 1, pary, czwórki, ósemki)
    groups = _find_groups(kmap, n)
    steps.append({"step": "Group minterms", "groups": groups})
    # Krok 4: wyznaczanie implikantów i uproszczenie
    simplified, group_exprs = _groups_to_expr(groups, vars, n)
    steps.append({"step": "Simplified expression", "groups_expr": group_exprs, "result": simplified})
    return {"result": simplified, "steps": steps}

def _generate_kmap(minterms: List[int], n: int):
    # Zwraca mapę Karnaugh jako 2D listę i kolejność Gray'a
    if n == 1:
        order = [0, 1]
        kmap = [[1 if i in minterms else 0] for i in order]
        return kmap, order
    if n == 2:
        order = [0, 1]
        kmap = [[1 if (2*r+c) in minterms else 0 for c in order] for r in order]
        return kmap, order
    if n == 3:
        order = [0, 1, 3, 2]  # Gray code
        kmap = [[1 if (4*r+c) in minterms else 0 for c in order] for r in order]
        return kmap, order
    if n == 4:
        order = [0, 1, 3, 2]  # Gray code
        kmap = [[1 if (4*r+c) in minterms else 0 for c in order] for r in order]
        return kmap, order
    raise KMapError("Obsługiwane są tylko 1-4 zmienne")

def _find_groups(kmap, n):
    # Prosta heurystyka: znajdź pojedyncze 1, pary, czwórki, ósemki (nieoptymalne, ale edukacyjne)
    groups = []
    rows = len(kmap)
    cols = len(kmap[0])
    visited = [[False]*cols for _ in range(rows)]
    # Szukaj czwórek (dla 2x2, 4x4)
    if rows >= 2 and cols >= 2:
        for r in range(rows-1):
            for c in range(cols-1):
                if all(kmap[r+dr][c+dc] == 1 and not visited[r+dr][c+dc] for dr in [0,1] for dc in [0,1]):
                    group = [(r+dr, c+dc) for dr in [0,1] for dc in [0,1]]
                    for rr, cc in group:
                        visited[rr][cc] = True
                    groups.append({"cells": group, "size": 4})
    # Szukaj par (poziome i pionowe)
    for r in range(rows):
        for c in range(cols-1):
            if kmap[r][c] == 1 and kmap[r][c+1] == 1 and not visited[r][c] and not visited[r][c+1]:
                groups.append({"cells": [(r,c), (r,c+1)], "size": 2})
                visited[r][c] = visited[r][c+1] = True
    for c in range(cols):
        for r in range(rows-1):
            if kmap[r][c] == 1 and kmap[r+1][c] == 1 and not visited[r][c] and not visited[r+1][c]:
                groups.append({"cells": [(r,c), (r+1,c)], "size": 2})
                visited[r][c] = visited[r+1][c] = True
    # Pojedyncze 1
    for r in range(rows):
        for c in range(cols):
            if kmap[r][c] == 1 and not visited[r][c]:
                groups.append({"cells": [(r,c)], "size": 1})
                visited[r][c] = True
    return groups

def _groups_to_expr(groups, vars, n):
    # Zamienia grupy na wyrażenia logiczne (prosta wersja)
    exprs = []
    for group in groups:
        # Dla uproszczenia: pokaż tylko rozmiar grupy i komórki
        exprs.append(f"group(size={group['size']}, cells={group['cells']})")
    # Wynik końcowy (dla edukacji: połącz grupy OR)
    simplified = ' ∨ '.join(exprs) if exprs else '0'
    return simplified, exprs 