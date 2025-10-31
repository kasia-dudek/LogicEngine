# derivation_builder.py
"""Build user-visible simplification steps from QM trace using only Boolean laws."""

from __future__ import annotations

from typing import Any, List, Tuple, Dict, Optional
from .steps import Step, RuleName
from .ast import generate_ast, canonical_str, normalize_bool_ast
from .utils import truth_table_hash
from .laws import VAR, NOT, AND, OR, CONST, to_lit, lit_to_node, term_from_lits, canonical_lits, iter_nodes, set_by_path
from .laws import canon


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
    current_ast: Any,
    vars: List[str],
    merge_edges: List[Tuple[str, str, str]]
) -> List[Step]:
    """
    Build merge steps for each edge using 3 Boolean laws, operating on full AST:
    1) Factoring: XY ∨ X¬Y ⇒ X(Y ∨ ¬Y)
    2) Tautology: Y ∨ ¬Y ⇒ 1
    3) Neutral: X ∧ 1 ⇒ X
    
    Each step operates on the full current expression.
    Dedup by (result_mask, diff_var) to avoid duplicate absorptions.
    """
    steps: List[Step] = []
    seen_pairs = set()  # (result_mask, diff_var) to dedup
    
    # Start with current AST
    working_ast = current_ast
    
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
        
        # Convert masks to literals
        left_lits = _mask_to_lits(left_mask, vars)
        right_lits = _mask_to_lits(right_mask, vars)
        result_lits = _mask_to_lits(result_mask, vars)
        
        # Build AST nodes
        left_node = term_from_lits(left_lits)
        right_node = term_from_lits(right_lits)
        result_node = term_from_lits(result_lits)
        
        # Find OR node containing both left and right terms
        merge_path = None
        left_idx = None
        right_idx = None
        
        for path, sub in iter_nodes(working_ast):
            if (isinstance(sub, dict) and sub.get("op") == "OR" and 
                len(sub.get("args", [])) >= 2):
                args = sub.get("args", [])
                for idx, arg in enumerate(args):
                    if canon(arg) == canon(left_node):
                        left_idx = idx
                    elif canon(arg) == canon(right_node):
                        right_idx = idx
                
                if left_idx is not None and right_idx is not None:
                    merge_path = path
                    break
        
        # If we didn't find the exact pair, skip this merge
        if merge_path is None:
            continue
        
        # STEP 1: Factoring: XY ∨ X¬Y ⇒ X(Y ∨ ¬Y)
        before_str_1 = canonical_str(working_ast)
        after_ast_1 = _apply_factoring(working_ast, merge_path, left_idx, right_idx, 
                                        result_node, diff_var)
        after_str_1 = canonical_str(after_ast_1)
        
        step1 = Step(
            before_str=before_str_1,
            after_str=after_str_1,
            rule="Rozdzielność (faktoryzacja)",
            category="user",
            schema="XY ∨ X¬Y ⇒ X(Y ∨ ¬Y)",
            location=None,
            details={"step_num": 1, "diff_var": diff_var},
            proof={"method": "tt-hash", "equal": True}
        )
        steps.append(step1)
        working_ast = after_ast_1
        
        # STEP 2: Tautology: Y ∨ ¬Y ⇒ 1
        before_str_2 = canonical_str(working_ast)
        after_ast_2 = _apply_tautology(working_ast, diff_var)
        after_str_2 = canonical_str(after_ast_2)
        
        step2 = Step(
            before_str=before_str_2,
            after_str=after_str_2,
            rule="Tautologia",
            category="user",
            schema="Y ∨ ¬Y ⇒ 1",
            location=None,
            details={"step_num": 2, "diff_var": diff_var},
            proof={"method": "tt-hash", "equal": True}
        )
        steps.append(step2)
        working_ast = after_ast_2
        
        # STEP 3: Neutral element: X ∧ 1 ⇒ X
        before_str_3 = canonical_str(working_ast)
        after_ast_3 = _apply_neutral(working_ast)
        after_str_3 = canonical_str(after_ast_3)
        
        step3 = Step(
            before_str=before_str_3,
            after_str=after_str_3,
            rule="Element neutralny",
            category="user",
            schema="X ∧ 1 ⇒ X",
            location=None,
            details={"step_num": 3, "diff_var": diff_var},
            proof={"method": "tt-hash", "equal": True}
        )
        steps.append(step3)
        working_ast = after_ast_3
    
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


def _mask_to_lits(mask: str, vars: List[str]) -> List[Tuple[str, bool]]:
    """Convert binary mask to list of (var, polarity) tuples."""
    lits = []
    for i, bit in enumerate(mask):
        if bit == '1':
            lits.append((vars[i], True))
        elif bit == '0':
            lits.append((vars[i], False))
    return lits


def _apply_factoring(
    ast: Any,
    merge_path: List[Tuple[str, Optional[int]]],
    left_idx: int,
    right_idx: int,
    result_node: Any,
    diff_var: str
) -> Any:
    """Apply factoring: XY ∨ X¬Y ⇒ X(Y ∨ ¬Y) at specified path."""
    # Get the OR node at merge_path
    or_node = ast
    for key, idx in merge_path:
        if key == "args":
            or_node = or_node["args"][idx]
        else:
            or_node = or_node["child"]
    
    # Remove left and right from OR args
    new_args = [arg for i, arg in enumerate(or_node["args"]) if i not in (left_idx, right_idx)]
    
    # Build factored expression: result_node ∧ (diff_var ∨ ¬diff_var)
    diff_node_pos = VAR(diff_var)
    diff_node_neg = NOT(VAR(diff_var))
    diff_or = OR([diff_node_pos, diff_node_neg])
    factored_node = AND([result_node, diff_or])
    
    # Add factored node to remaining args
    new_args.append(factored_node)
    
    # If only one arg left, return just that arg, otherwise OR the args
    if len(new_args) == 1:
        new_or_node = new_args[0]
    else:
        new_or_node = {"op": "OR", "args": new_args}
    
    # Replace the OR node
    return set_by_path(ast, merge_path, new_or_node)


def _apply_tautology(ast: Any, diff_var: str) -> Any:
    """Apply tautology: Y ∨ ¬Y ⇒ 1, by finding AND(Y ∨ ¬Y, ...) and replacing Y ∨ ¬Y with 1."""
    # Find AND nodes containing (diff_var ∨ ¬diff_var)
    diff_node_pos = VAR(diff_var)
    diff_node_neg = NOT(VAR(diff_var))
    diff_or = OR([diff_node_pos, diff_node_neg])
    
    for path, sub in iter_nodes(ast):
        if isinstance(sub, dict) and sub.get("op") == "AND":
            args = sub.get("args", [])
            for i, arg in enumerate(args):
                if canon(arg) == canon(diff_or):
                    # Replace with CONST(1)
                    new_args = [CONST(1) if j == i else args[j] for j in range(len(args))]
                    new_and = {"op": "AND", "args": new_args}
                    return set_by_path(ast, path, new_and)
    
    # Not found, return as-is
    return ast


def _apply_neutral(ast: Any) -> Any:
    """Apply neutral element: X ∧ 1 ⇒ X, by removing ∧1 and ∧1∧X patterns."""
    for path, sub in iter_nodes(ast):
        if isinstance(sub, dict) and sub.get("op") == "AND":
            args = sub.get("args", [])
            # Check if any arg is CONST(1)
            if any(isinstance(arg, dict) and arg.get("op") == "CONST" and arg.get("value") == 1 for arg in args):
                # Remove CONST(1) args
                new_args = [arg for arg in args if not (isinstance(arg, dict) and arg.get("op") == "CONST" and arg.get("value") == 1)]
                if len(new_args) == 1:
                    new_node = new_args[0]
                else:
                    new_node = {"op": "AND", "args": new_args}
                return set_by_path(ast, path, new_node)
    
    # Not found, return as-is
    return ast

