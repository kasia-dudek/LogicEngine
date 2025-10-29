# kmap.py
"""Karnaugh map simplification."""

import logging
from typing import List, Dict, Any, Tuple

from .truth_table import generate_truth_table, TruthTableError
from .utils import to_bin, bin_to_expr, count_literals

logger = logging.getLogger(__name__)


class KMapError(Exception):
    pass


def _default_axis(vars: List[str]) -> Dict[str, List[str]]:
    n = len(vars)
    if n == 1:
        return {"row_vars": [], "col_vars": [vars[0]]}
    if n == 2:
        return {"row_vars": [vars[0]], "col_vars": [vars[1]]}
    if n == 3:
        return {"row_vars": [vars[0]], "col_vars": [vars[1], vars[2]]}
    return {"row_vars": [vars[0], vars[1]], "col_vars": [vars[2], vars[3]]}  # n == 4


def simplify_kmap(expr: str) -> Dict[str, Any]:
    steps: List[Dict[str, Any]] = []

    try:
        table = generate_truth_table(expr)
    except TruthTableError as e:
        raise KMapError(f"Błąd generowania tabeli prawdy: {e}")

    vars_ = sorted({ch for ch in expr if ch.isalpha()})
    n = len(vars_)
    if n < 1 or n > 5:
        raise KMapError("Obsługiwane są wyrażenia z 1-5 zmiennymi (powyżej 5 zmiennych wizualizacja mapy Karnaugha staje się bardzo trudna)")

    minterms = [i for i, row in enumerate(table) if row["result"]]
    steps.append({"step": "Krok 1: Znajdź mintermy", "data": {"minterms": minterms}})

    kmap, order = _generate_kmap(minterms, n)
    pi_groups = _find_groups(kmap, n, order)
    simplified, all_groups = _groups_to_expr(pi_groups, vars_, n, order, minterms)
    selected_groups = [g for g in all_groups if g.get("selected")]

    return {
        "kmap": kmap,
        "groups": selected_groups,
        "all_groups": all_groups,
        "result": simplified,
        "steps": steps,
        "expr_for_tests": simplified,
        "vars": vars_,
        "minterms": minterms,
        "axis": _default_axis(vars_),
    }


def _generate_kmap(minterms: List[int], n: int) -> Tuple[List[List[int]], List[int]]:
    """Build K-map grid and Gray order for n variables (1..4)."""
    if n == 1:
        order = [0, 1]
        grid = [[1 if i in minterms else 0 for i in order]]
        return grid, order
    if n == 2:
        order = [0, 1]
        grid = [[1 if (r * 2 + c) in minterms else 0 for c in order] for r in order]
        return grid, order
    if n == 3:
        order = [0, 1, 3, 2]  # Gray columns
        grid = [[1 if (r * 4 + order[c]) in minterms else 0 for c in range(4)] for r in range(2)]
        return grid, order
    if n == 4:
        order = [0, 1, 3, 2]  # Gray on rows and cols
        grid = [[1 if (order[r] * 4 + order[c]) in minterms else 0 for c in range(4)] for r in range(4)]
        return grid, order
    raise KMapError("Obsługiwane są tylko 1-4 zmienne")


def _cells_to_minterms(cells: List[Tuple[int, int]], n: int, order: List[int]) -> List[int]:
    if n == 1:
        return [order[c] for _, c in cells]
    if n == 2:
        return [order[r] * 2 + order[c] for r, c in cells]
    if n == 3:
        return [r * 4 + order[c] for r, c in cells]
    if n == 4:
        return [order[r] * 4 + order[c] for r, c in cells]
    return []


def _find_groups(kmap: List[List[int]], n: int, order: List[int]) -> List[Dict[str, Any]]:
    """Find prime implicant rectangles (power-of-two sized, wrapping allowed)."""
    rows, cols = len(kmap), len(kmap[0]) if kmap else 0
    if rows == 0 or cols == 0:
        return []

    def pow2_up_to(limit: int) -> List[int]:
        out, x = [1], 2
        while x <= limit:
            out.append(x)
            x *= 2
        return out

    h_opts, w_opts = pow2_up_to(rows), pow2_up_to(cols)

    def rect_cells(r0: int, c0: int, h: int, w: int) -> List[Tuple[int, int]]:
        return [((r0 + dr) % rows, (c0 + dc) % cols) for dr in range(h) for dc in range(w)]

    def cells_to_minterms(cells: List[Tuple[int, int]]) -> List[int]:
        return _cells_to_minterms(cells, n, order)

    groups_map: Dict[frozenset, Dict[str, Any]] = {}

    areas = sorted({h * w for h in h_opts for w in w_opts}, reverse=True)
    for area in areas:
        for h in h_opts:
            if area % h:
                continue
            w = area // h
            if w not in w_opts:
                continue
            for r in range(rows):
                for c in range(cols):
                    cells = rect_cells(r, c, h, w)
                    if all(kmap[rr][cc] == 1 for rr, cc in cells):
                        mints = cells_to_minterms(cells)
                        key = frozenset(mints)
                        if key and key not in groups_map:
                            groups_map[key] = {
                                "cells": cells,
                                "size": len(cells),
                                "minterms": sorted(mints),
                            }

    groups = list(groups_map.values())

    # Keep only prime implicants (not strictly contained in larger ones)
    sets_ = [set(g["minterms"]) for g in groups]
    primes: List[Dict[str, Any]] = []
    for i, gi in enumerate(groups):
        if any(i != j and sets_[i] < sets_[j] for j in range(len(groups))):
            continue
        primes.append(gi)

    primes.sort(key=lambda g: (-g["size"], g["minterms"]))
    return primes


def _groups_to_expr(
    groups: List[Dict[str, Any]],
    vars: List[str],
    n: int,
    order: List[int],
    minterms: List[int],
) -> Tuple[str, List[Dict[str, Any]]]:
    """Mark essential implicants, greedily cover the rest, and build the sum of products."""
    detailed: List[Dict[str, Any]] = []
    for g in groups:
        mints = g["minterms"]
        binaries = [to_bin(m, n) for m in mints]
        common = ['-' for _ in range(n)]
        for i in range(n):
            vals = {b[i] for b in binaries}
            if len(vals) == 1:
                common[i] = vals.pop()
        expr = bin_to_expr(''.join(common), vars)
        if not expr.strip():
            expr = '1'
        detailed.append({**g, "expr": expr, "selected": False})

    ones = set(minterms)
    cover: Dict[int, List[int]] = {m: [] for m in ones}
    for idx, g in enumerate(detailed):
        for m in set(g["minterms"]) & ones:
            cover[m].append(idx)

    selected: List[int] = []
    covered = set()

    # Essential prime implicants
    changed = True
    while changed:
        changed = False
        for m in sorted(ones - covered):
            owners = [i for i in cover[m] if i not in selected]
            if len(owners) == 1:
                i = owners[0]
                selected.append(i)
                covered |= (set(detailed[i]["minterms"]) & ones)
                changed = True

    # Greedy cover for remaining ones
    rem = sorted(ones - covered)
    while rem:
        best_i, best_key = None, None
        for i, g in enumerate(detailed):
            if i in selected:
                continue
            gain = len(set(g["minterms"]) & set(rem))
            if gain == 0:
                continue
            lits = 0 if g["expr"] == "1" else count_literals(g.get("expr", ""))
            key = (gain, g["size"], -lits)
            if best_key is None or key > best_key:
                best_key, best_i = key, i
        if best_i is None:
            break
        selected.append(best_i)
        covered |= (set(detailed[best_i]["minterms"]) & ones)
        rem = sorted(ones - covered)

    selected_terms: List[str] = []
    for i, g in enumerate(detailed):
        if i in selected:
            g["selected"] = True
            if g.get("expr"):
                selected_terms.append(g["expr"])

    simplified = ' ∨ '.join(selected_terms) if selected_terms else '0'
    detailed.sort(key=lambda d: (not d["selected"], -d["size"], d.get("expr", "")))
    return simplified, detailed
