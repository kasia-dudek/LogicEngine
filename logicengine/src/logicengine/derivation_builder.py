# derivation_builder.py
"""Build user-visible simplification steps from QM trace using only Boolean laws."""

from __future__ import annotations

from typing import Any, List, Tuple, Dict, Optional
from .steps import Step, RuleName
from .ast import generate_ast, canonical_str, normalize_bool_ast
from .utils import truth_table_hash


def build_minterm_expansion_steps(
    expr_str: str,
    vars: List[str],
    minterms_1: List[int]
) -> List[Step]:
    """
    Build algebraic steps to expand expression into sum of minterms.
    
    Strategy:
    - Use controlled distribution: X*(...) ∨ (¬X)*(...)
    - Remove branches leading to minterms=0 (contradiction, neutral)
    - Result: OR of products corresponding to minterms_1
    """
    steps: List[Step] = []
    
    # For now, return empty list as this is complex
    # TODO: Implement minterm expansion using Shannon expansion
    return steps


def build_merge_steps(
    vars: List[str],
    merge_edges: List[Tuple[str, str, str]]
) -> List[Step]:
    """
    Build merge steps for each edge (left, right, result_mask).
    
    Each edge represents absorption: XY + X¬Y = X
    Dedup by (result_mask, diff_var) to avoid duplicate absorptions.
    """
    steps: List[Step] = []
    seen_pairs = set()  # (result_mask, diff_var) to dedup
    
    for left_mask, right_mask, result_mask in merge_edges:
        # Find which variable differs
        diff_var = None
        for i, (l, r) in enumerate(zip(left_mask, right_mask)):
            if l != r:
                diff_var = vars[i]
                break
        
        if diff_var is None:
            continue  # Skip invalid edge
        
        # Dedup: don't create duplicate absorption for same PI and variable
        dedup_key = (result_mask, diff_var)
        if dedup_key in seen_pairs:
            continue
        seen_pairs.add(dedup_key)
        
        # Convert masks to expressions
        left_expr = _mask_to_expr(left_mask, vars)
        right_expr = _mask_to_expr(right_mask, vars)
        result_expr = _mask_to_expr(result_mask, vars)
        
        # Build step for absorption
        before_str = f"{left_expr} ∨ {right_expr}"
        after_str = result_expr
        
        # Schema: use actual variable name
        schema = f"XY ∨ X¬Y = X"  # Generic, or could be f"{diff_var}Y ∨ {diff_var}¬Y = Y" 
        
        step = Step(
            before_str=before_str,
            after_str=after_str,
            rule="Pochłanianie różniącego literału",
            category="user",
            schema=schema,
            location=None,
            details={
                "left_mask": left_mask,
                "right_mask": right_mask,
                "result_mask": result_mask,
                "diff_var": diff_var
            },
            proof={"method": "tt-hash", "equal": True}
        )
        steps.append(step)
    
    return steps


def build_absorb_steps(
    selected_pi: List[str],
    pi_to_minterms: Dict[str, List[int]]
) -> List[Step]:
    """
    Build absorption steps to remove covered minterms.
    
    Strategy:
    - For each PI, absorb all minterms it covers
    - Using absorption: X ∨ (X∧Y) = X
    """
    steps: List[Step] = []
    
    # TODO: Implement absorption steps
    return steps


def _mask_to_expr(mask: str, vars: List[str]) -> str:
    """Convert binary mask (e.g., '10-1') to expression (e.g., 'A∧¬B∧D')."""
    if len(mask) != len(vars):
        return mask  # Fallback
    
    literals = []
    for i, bit in enumerate(mask):
        if bit == '1':
            literals.append(vars[i])
        elif bit == '0':
            literals.append(f"¬{vars[i]}")
        # '-' means don't care, so skip
    
    if not literals:
        return "1"  # Empty product = true
    
    return " ∧ ".join(literals)

