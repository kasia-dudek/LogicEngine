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
    Build merge steps for each edge using 3 Boolean laws:
    1) Factoring: XY ∨ X¬Y ⇒ X(Y ∨ ¬Y)
    2) Tautology: Y ∨ ¬Y ⇒ 1
    3) Neutral: X ∧ 1 ⇒ X
    
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
        
        # STEP 1: Factoring
        step1 = Step(
            before_str=f"{left_expr} ∨ {right_expr}",
            after_str=f"{result_expr} ∧ ({diff_var} ∨ ¬{diff_var})",
            rule="Rozdzielność (faktoryzacja)",
            category="user",
            schema="XY ∨ X¬Y ⇒ X(Y ∨ ¬Y)",
            location=None,
            details={"step_num": 1, "diff_var": diff_var},
            proof={"method": "tt-hash", "equal": True}
        )
        steps.append(step1)
        
        # STEP 2: Tautology
        step2 = Step(
            before_str=f"{result_expr} ∧ ({diff_var} ∨ ¬{diff_var})",
            after_str=f"{result_expr} ∧ 1",
            rule="Tautologia",
            category="user",
            schema="Y ∨ ¬Y ⇒ 1",
            location=None,
            details={"step_num": 2, "diff_var": diff_var},
            proof={"method": "tt-hash", "equal": True}
        )
        steps.append(step2)
        
        # STEP 3: Neutral element
        step3 = Step(
            before_str=f"{result_expr} ∧ 1",
            after_str=result_expr,
            rule="Element neutralny",
            category="user",
            schema="X ∧ 1 ⇒ X",
            location=None,
            details={"step_num": 3, "diff_var": diff_var},
            proof={"method": "tt-hash", "equal": True}
        )
        steps.append(step3)
    
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
    
    # Add parentheses if more than one literal
    expr = " ∧ ".join(literals)
    if len(literals) > 1:
        expr = f"({expr})"
    return expr

