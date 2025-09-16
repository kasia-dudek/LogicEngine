"""Validation and equivalence checking for logical expressions."""

from __future__ import annotations
from typing import Any, Dict, Set, List
import random


class ValidationError(Exception):
    """Exception raised for validation errors."""
    pass


def validate(expr: str) -> None:
    """
    Basic validation of expression.
    
    Args:
        expr: Expression to validate.
        
    Raises:
        ValidationError: If expression is empty or None.
    """
    if expr is None or expr == "":
        raise ValidationError("Puste wyrażenie")


def _collect_vars(node: Any, acc: Set[str]) -> None:
    """Collect all variables from normalized AST."""
    if not isinstance(node, dict):
        return
    
    op = node.get('op')
    if op == 'VAR':
        acc.add(node.get('name'))
    elif op == 'NOT':
        _collect_vars(node.get('child'), acc)
    elif op in {'AND', 'OR'}:
        for a in node.get('args', []):
            _collect_vars(a, acc)


def _eval(node: Any, env: Dict[str, int]) -> int:
    """Evaluate normalized AST with given variable assignments."""
    if not isinstance(node, dict):
        # unknown -> treat as false
        return 0
    
    op = node.get('op')
    if op == 'CONST':
        return 1 if node.get('value') == 1 else 0
    if op == 'VAR':
        return 1 if env.get(node.get('name'), 0) else 0
    if op == 'NOT':
        return 0 if _eval(node.get('child'), env) else 1
    if op == 'AND':
        v = 1
        for a in node.get('args', []):
            v = v & _eval(a, env)
            if v == 0:
                break
        return v
    if op == 'OR':
        v = 0
        for a in node.get('args', []):
            v = v | _eval(a, env)
            if v == 1:
                break
        return v
    # unsupported nodes: assume false
    return 0


def equivalent(ast_before: Any, ast_after: Any, var_limit: int = 12) -> bool:
    """
    Check if two normalized boolean ASTs are equivalent.
    
    Args:
        ast_before: First AST to compare.
        ast_after: Second AST to compare.
        var_limit: Safety cap - if >12 vars, use random sampling.
        
    Returns:
        True if ASTs are equivalent, False otherwise.
    """
    vars_set: Set[str] = set()
    _collect_vars(ast_before, vars_set)
    _collect_vars(ast_after, vars_set)
    vars_list = sorted(vars_set)

    n = len(vars_list)
    if n <= var_limit:
        # Exhaustive check for small number of variables
        total = 1 << n
        for mask in range(total):
            env = {vars_list[i]: 1 if (mask >> i) & 1 else 0 for i in range(n)}
            if _eval(ast_before, env) != _eval(ast_after, env):
                return False
        return True

    # Fallback: sample subset of assignments for larger var counts
    SAMPLES = min(5000, 1 << 16)
    for _ in range(SAMPLES):
        env = {v: random.randint(0, 1) for v in vars_list}
        if _eval(ast_before, env) != _eval(ast_after, env):
            return False
    return True
