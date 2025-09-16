# utils.py
"""Utility helpers for the logic engine."""

from __future__ import annotations
from typing import Any, Dict, List


def to_bin(m: int, n: int) -> str:
    """Return m as a zero-padded binary string of length n."""
    return format(m, f"0{n}b")


def bin_to_expr(mask: str, vars_: List[str]) -> str:
    """
    Convert a mask like '1-0' to a product term using vars_ order.
    '1' -> VAR, '0' -> ¬VAR, '-' -> skip (don't care).
    Empty product becomes '1'.
    """
    terms: List[str] = []
    for i, ch in enumerate(mask):
        if ch == "-":
            continue
        if ch == "1":
            terms.append(vars_[i])
        elif ch == "0":
            terms.append(f"¬{vars_[i]}")
    return " ∧ ".join(terms) if terms else "1"


def count_literals(expr: str) -> int:
    """Count literal occurrences in a flat expression string (A or ¬A)."""
    return sum(c.isupper() for c in expr)


def compute_metrics(node: Any) -> Dict[str, int]:
    """
    Compute basic metrics on a normalized Boolean AST.

    Returns:
        operators: number of AND/OR/NOT nodes
        literals: number of VAR occurrences (NOT VAR counts as one literal)
        neg_depth_sum: sum of negation depths over all literals
    """
    def walk(n: Any, neg_depth: int) -> Dict[str, int]:
        if not isinstance(n, dict):
            return {"operators": 0, "literals": 0, "neg_depth_sum": 0}

        op = n.get("op")

        if op == "CONST":
            return {"operators": 0, "literals": 0, "neg_depth_sum": 0}

        if op == "VAR":
            return {"operators": 0, "literals": 1, "neg_depth_sum": neg_depth}

        if op == "NOT":
            c = walk(n.get("child"), neg_depth + 1)
            return {
                "operators": c["operators"] + 1,
                "literals": c["literals"],
                "neg_depth_sum": c["neg_depth_sum"],
            }

        if op in {"AND", "OR"}:
            acc = {"operators": 1, "literals": 0, "neg_depth_sum": 0}
            for a in n.get("args", []):
                r = walk(a, neg_depth)
                acc["operators"] += r["operators"]
                acc["literals"] += r["literals"]
                acc["neg_depth_sum"] += r["neg_depth_sum"]
            return acc

        # unknown node
        return {"operators": 0, "literals": 0, "neg_depth_sum": 0}

    return walk(node, 0)
