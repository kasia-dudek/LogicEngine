import logging
from typing import List, Dict, Any, Tuple
from .parser import LogicParser, LogicExpressionError
from .truth_table import generate_truth_table, TruthTableError
from .utils import to_bin, bin_to_expr, count_literals

logger = logging.getLogger(__name__)

class KMapError(Exception):
    """Wyjątek dla błędów mapy Karnaugh."""
    pass

def simplify_kmap(expr: str) -> Dict[str, Any]:
    """Upraszcza wyrażenie logiczne za pomocą mapy Karnaugh."""
    steps = []
    try:
        parsed_expr = LogicParser.parse(expr)
        table = generate_truth_table(expr)
    except LogicExpressionError as e:
        logger.error(f"Błąd parsowania: {e}")
        raise
    except TruthTableError as e:
        logger.error(f"Błąd generowania tabeli prawdy: {e}")
        raise KMapError(f"Błąd generowania tabeli prawdy: {e}")

    vars = sorted(set(ch for ch in parsed_expr if ch.isalpha()))
    n = len(vars)
    if n < 1 or n > 4:
        logger.error("Zbyt wiele lub za mało zmiennych dla Mapy Karnaugh")
        raise KMapError("Obsługiwane są wyrażenia z 1-4 zmiennymi")

    minterms = [i for i, row in enumerate(table) if row['result']]
    steps.append({
        "step": "Krok 1: Znajdź mintermy",
        "data": {
            "minterms": minterms,
            "opis": "Indeksy wierszy tabeli prawdy, gdzie wynik = 1."
        }
    })

    if not minterms:
        contradiction_expr = ' ∧ '.join([f'{v} ∧ ¬{v}' for v in vars]) if vars else '0'
        steps.append({
            "step": "Krok 2: Sprzeczność",
            "data": {
                "result": "0",
                "opis": "Wyrażenie jest zawsze fałszywe (brak mintermów).",
                "expr_for_tests": contradiction_expr
            }
        })
        steps.append({
            "step": "Krok 3: Uproszczone wyrażenie",
            "data": {
                "result": "0",
                "opis": "Końcowe wyrażenie logiczne: sprzeczność."
            }
        })
        try:
            tt_orig = generate_truth_table(expr, force_vars=vars)
            tt_simp = generate_truth_table(contradiction_expr, force_vars=vars)
            verification = tt_orig == tt_simp
            verification_desc = "Tabela prawdy sprzeczności jest zgodna z oryginalną." if verification else "Błąd: Tabela prawdy sprzeczności różni się od oryginalnej."
        except Exception as e:
            verification = False
            verification_desc = f"Błąd weryfikacji: {e}"
            logger.error(f"Błąd weryfikacji sprzeczności: {e}")
        steps.append({
            "step": "Krok 4: Weryfikacja poprawności",
            "data": {
                "zgodność": verification,
                "opis": verification_desc
            }
        })
        kmap, kmap_order = _generate_kmap(minterms, n, vars)
        groups = _find_groups(kmap, n, kmap_order, vars)
        simplified, group_exprs = _groups_to_expr(groups, vars, n, kmap_order)
        return {
            "kmap": kmap,
            "groups": groups,
            "result": simplified,
            "steps": steps,
            "expr_for_tests": contradiction_expr
        }

    if len(minterms) == 2**n:
        tautology_expr = ' ∨ '.join([f'{v} ∨ ¬{v}' for v in vars]) if vars else '1'
        steps.append({
            "step": "Krok 2: Tautologia",
            "data": {
                "result": "1",
                "opis": "Wyrażenie jest zawsze prawdziwe (wszystkie kombinacje są mintermami).",
                "expr_for_tests": tautology_expr
            }
        })
        steps.append({
            "step": "Krok 3: Uproszczone wyrażenie",
            "data": {
                "result": "1",
                "opis": "Końcowe wyrażenie logiczne: tautologia."
            }
        })
        try:
            tt_orig = generate_truth_table(expr, force_vars=vars)
            tt_simp = generate_truth_table(tautology_expr, force_vars=vars)
            verification = tt_orig == tt_simp
            verification_desc = "Tabela prawdy tautologii jest zgodna z oryginalną." if verification else "Błąd: Tabela prawdy tautologii różni się od oryginalnej."
        except Exception as e:
            verification = False
            verification_desc = f"Błąd weryfikacji: {e}"
            logger.error(f"Błąd weryfikacji tautologii: {e}")
        steps.append({
            "step": "Krok 4: Weryfikacja poprawności",
            "data": {
                "zgodność": verification,
                "opis": verification_desc
            }
        })
        kmap, kmap_order = _generate_kmap(minterms, n, vars)
        groups = _find_groups(kmap, n, kmap_order, vars)
        simplified, group_exprs = _groups_to_expr(groups, vars, n, kmap_order)
        return {
            "kmap": kmap,
            "groups": groups,
            "result": simplified,
            "steps": steps,
            "expr_for_tests": tautology_expr
        }

    kmap, kmap_order = _generate_kmap(minterms, n, vars)
    groups = _find_groups(kmap, n, kmap_order, vars)
    simplified, group_exprs = _groups_to_expr(groups, vars, n, kmap_order)
    steps.append({
        "step": "Krok 2: Utwórz mapę Karnaugh",
        "data": {
            "kmap": kmap,
            "order": kmap_order,
            "opis": "Mapa Karnaugh dla mintermów, uporządkowana w kodzie Graya."
        }
    })

    steps.append({
        "step": "Krok 3: Grupowanie mintermów",
        "data": {
            "groups": groups,
            "opis": "Grupy mintermów (1, 2, 4, 8) do uproszczenia."
        }
    })

    steps.append({
        "step": "Krok 4: Uproszczenie",
        "data": {
            "groups_expr": group_exprs,
            "result": simplified,
            "opis": "Wyrażenie uproszczone na podstawie grup w mapie Karnaugh."
        }
    })

    try:
        tt_orig = generate_truth_table(expr, force_vars=vars)
        tt_simp = generate_truth_table(simplified if simplified != '0' else 'A ∧ ¬A', force_vars=vars)
        verification = tt_orig == tt_simp
        verification_desc = "Tabela prawdy uproszczonego wyrażenia jest identyczna z oryginalną." if verification else "Błąd: Tabela prawdy uproszczonego wyrażenia różni się od oryginalnej."
    except Exception as e:
        verification = False
        verification_desc = f"Błąd weryfikacji: {e}"
        logger.error(f"Błąd weryfikacji: {e}")

    steps.append({
        "step": "Krok 5: Weryfikacja poprawności",
        "data": {
            "zgodność": verification,
            "opis": verification_desc
        }
    })

    return {
        "kmap": kmap,
        "groups": groups,
        "result": simplified,
        "steps": steps,
        "expr_for_tests": simplified
    }

def _generate_kmap(minterms: List[int], n: int, vars: List[str]) -> Tuple[List[List[int]], List[int]]:
    """Generuje mapę Karnaugh w formacie 2D i kolejność Graya."""
    if n == 1:
        order = [0, 1]
        kmap = [[1 if i in minterms else 0 for i in order]]
        return kmap, order
    if n == 2:
        order = [0, 1]
        kmap = [[1 if (r*2+c) in minterms else 0 for c in order] for r in order]
        return kmap, order
    if n == 3:
        order = [0, 1, 3, 2]
        kmap = [[1 if (r*4+c) in minterms else 0 for c in order] for r in order[:2]]
        return kmap, order
    if n == 4:
        order = [0, 1, 3, 2]
        kmap = [[1 if (r*4+c) in minterms else 0 for c in order] for r in order]
        return kmap, order
    raise KMapError("Obsługiwane są tylko 1-4 zmienne")

def _find_groups(kmap: List[List[int]], n: int, order: List[int], vars: List[str]) -> List[Dict[str, Any]]:
    """Znajduje grupy (1, 2, 4, 8) w mapie Karnaugh."""
    groups = []
    rows = len(kmap)
    cols = len(kmap[0])
    visited = [[False] * cols for _ in range(rows)]

    if n == 4:
        for r in range(0, rows, 2):
            for c in range(0, cols, 2):
                if all(kmap[(r + dr) % rows][(c + dc) % cols] == 1 and not visited[(r + dr) % rows][(c + dc) % cols]
                       for dr in [0, 1, 2, 3] for dc in [0, 1] if dr == 0 or dc == 0):
                    cells = [(r + dr, c + dc) for dr in [0, 1, 2, 3] for dc in [0, 1] if dr == 0 or dc == 0]
                    for rr, cc in cells:
                        visited[rr % rows][cc % cols] = True
                    minterms = _cells_to_minterms(cells, n, order)
                    groups.append({"cells": cells, "size": 8, "minterms": minterms})

    for r in range(rows):
        for c in range(cols):
            if r < rows - 1 and c < cols - 1:
                if all(kmap[(r + dr) % rows][(c + dc) % cols] == 1 and not visited[(r + dr) % rows][(c + dc) % cols]
                       for dr in [0, 1] for dc in [0, 1]):
                    cells = [(r + dr, c + dc) for dr in [0, 1] for dc in [0, 1]]
                    for rr, cc in cells:
                        visited[rr % rows][cc % cols] = True
                    minterms = _cells_to_minterms(cells, n, order)
                    groups.append({"cells": cells, "size": 4, "minterms": minterms})
            if n >= 3 and r < rows:
                if all(kmap[r][(c + dc) % cols] == 1 and not visited[r][(c + dc) % cols] for dc in range(4)):
                    cells = [(r, (c + dc) % cols) for dc in range(4)]
                    for rr, cc in cells:
                        visited[rr][cc] = True
                    minterms = _cells_to_minterms(cells, n, order)
                    groups.append({"cells": cells, "size": 4, "minterms": minterms})
            if n == 4 and c < cols:
                if all(kmap[(r + dr) % rows][c] == 1 and not visited[(r + dr) % rows][c] for dr in range(4)):
                    cells = [(r + dr, c) for dr in range(4)]
                    for rr, cc in cells:
                        visited[rr][cc] = True
                    minterms = _cells_to_minterms(cells, n, order)
                    groups.append({"cells": cells, "size": 4, "minterms": minterms})

    for r in range(rows):
        for c in range(cols):
            if c < cols - 1:
                if kmap[r][c] == 1 and kmap[r][(c + 1) % cols] == 1 and not visited[r][c] and not visited[r][(c + 1) % cols]:
                    cells = [(r, c), (r, (c + 1) % cols)]
                    for rr, cc in cells:
                        visited[rr][cc] = True
                    minterms = _cells_to_minterms(cells, n, order)
                    groups.append({"cells": cells, "size": 2, "minterms": minterms})
            if r < rows - 1:
                if kmap[r][c] == 1 and kmap[(r + 1) % rows][c] == 1 and not visited[r][c] and not visited[(r + 1) % rows][c]:
                    cells = [(r, c), ((r + 1) % rows, c)]
                    for rr, cc in cells:
                        visited[rr][cc] = True
                    minterms = _cells_to_minterms(cells, n, order)
                    groups.append({"cells": cells, "size": 2, "minterms": minterms})

    for r in range(rows):
        for c in range(cols):
            if kmap[r][c] == 1 and not visited[r][c]:
                cells = [(r, c)]
                visited[r][c] = True
                minterms = _cells_to_minterms(cells, n, order)
                groups.append({"cells": cells, "size": 1, "minterms": minterms})

    return groups

def _cells_to_minterms(cells: List[Tuple[int, int]], n: int, order: List[int]) -> List[int]:
    """Zamienia współrzędne komórek na mintermy."""
    if n == 1:
        return [order[c] for r, c in cells]
    if n == 2:
        return [order[r] * 2 + order[c] for r, c in cells]
    if n == 3:
        return [order[r] * 4 + order[c] for r, c in cells]
    if n == 4:
        return [order[r] * 4 + order[c] for r, c in cells]
    return []

def _groups_to_expr(groups: List[Dict[str, Any]], vars: List[str], n: int, order: List[int]) -> Tuple[str, List[Dict]]:
    """Zamienia grupy na uproszczone wyrażenie logiczne."""
    exprs = []
    group_exprs = []

    for group in groups:
        minterms = group["minterms"]
        if not minterms:
            continue
        binaries = [to_bin(m, n) for m in minterms]
        common = ['-' for _ in range(n)]
        for i in range(n):
            values = {b[i] for b in binaries}
            if len(values) == 1:
                common[i] = values.pop()
        binary_repr = ''.join(common)
        expr = bin_to_expr(binary_repr, vars)
        if expr:
            exprs.append(expr)
        group_exprs.append({
            "size": group["size"],
            "cells": group["cells"],
            "minterms": minterms,
            "expr": expr
        })

    simplified = ' ∨ '.join(exprs) if exprs else '0'
    return simplified, group_exprs