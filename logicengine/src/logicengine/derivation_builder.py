# derivation_builder.py
"""Build user-visible simplification steps from QM trace using only Boolean laws."""

from __future__ import annotations

from typing import Any, List, Tuple, Dict, Optional
from .steps import Step, RuleName
from .ast import generate_ast, canonical_str, normalize_bool_ast, canonical_str_minimal
from .utils import truth_table_hash
from .laws import VAR, NOT, AND, OR, CONST, to_lit, lit_to_node, term_from_lits, canonical_lits, iter_nodes, set_by_path
from .laws import canon, pretty


def is_dnf(ast: Any) -> bool:
    """Check if AST is in proper DNF: OR of ANDs of literals."""
    if not isinstance(ast, dict):
        return True  # Single literal
    op = ast.get("op")
    if op == "OR":
        # All args should be products of literals
        return all(_is_product_of_literals(arg) for arg in ast.get("args", []))
    elif op == "AND":
        # Should be product of literals only
        return _is_product_of_literals(ast)
    else:
        return op in ["VAR", "CONST", "NOT"]


def _is_product_of_literals(ast: Any) -> bool:
    """Check if AST is product of literals (no nested OR)."""
    if not isinstance(ast, dict):
        return True  # Single var
    op = ast.get("op")
    if op == "AND":
        # All args should be literals
        return all(_is_literal(arg) for arg in ast.get("args", []))
    else:
        return op in ["VAR", "CONST", "NOT"]


def _is_literal(ast: Any) -> bool:
    """Check if AST is a literal (VAR, NOT VAR, CONST)."""
    if not isinstance(ast, dict):
        return True  # Single var
    op = ast.get("op")
    if op == "VAR" or op == "CONST":
        return True
    if op == "NOT":
        child = ast.get("child")
        return isinstance(child, dict) and child.get("op") == "VAR"
    return False


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
        before_str_1 = pretty(working_ast)
        after_ast_1 = _apply_factoring(working_ast, merge_path, left_idx, right_idx, 
                                        result_node, diff_var)
        after_str_1 = pretty(after_ast_1)
        
        # Verify TT equivalence
        is_equal_1 = (truth_table_hash(vars, before_str_1) == truth_table_hash(vars, after_str_1))
        
        step1 = Step(
            before_str=before_str_1,
            after_str=after_str_1,
            rule="Rozdzielność (faktoryzacja)",
            category="user",
            schema="XY ∨ X¬Y ⇒ X(Y ∨ ¬Y)",
            location=None,
            details={"step_num": 1, "diff_var": diff_var},
            proof={"method": "tt-hash", "equal": is_equal_1}
        )
        steps.append(step1)
        working_ast = after_ast_1
        
        # STEP 2: Tautology: Y ∨ ¬Y ⇒ 1
        before_str_2 = pretty(working_ast)
        after_ast_2 = _apply_tautology(working_ast, diff_var)
        after_str_2 = pretty(after_ast_2)
        
        # Verify TT equivalence
        is_equal_2 = (truth_table_hash(vars, before_str_2) == truth_table_hash(vars, after_str_2))
        
        step2 = Step(
            before_str=before_str_2,
            after_str=after_str_2,
            rule="Tautologia",
            category="user",
            schema="Y ∨ ¬Y ⇒ 1",
            location=None,
            details={"step_num": 2, "diff_var": diff_var},
            proof={"method": "tt-hash", "equal": is_equal_2}
        )
        steps.append(step2)
        working_ast = after_ast_2
        
        # STEP 3: Neutral element: X ∧ 1 ⇒ X
        before_str_3 = pretty(working_ast)
        after_ast_3 = _apply_neutral(working_ast)
        after_str_3 = pretty(after_ast_3)
        
        # Verify TT equivalence
        is_equal_3 = (truth_table_hash(vars, before_str_3) == truth_table_hash(vars, after_str_3))
        
        step3 = Step(
            before_str=before_str_3,
            after_str=after_str_3,
            rule="Element neutralny",
            category="user",
            schema="X ∧ 1 ⇒ X",
            location=None,
            details={"step_num": 3, "diff_var": diff_var},
            proof={"method": "tt-hash", "equal": is_equal_3}
        )
        steps.append(step3)
        working_ast = after_ast_3
    
    return steps


def build_absorb_steps(
    ast: Any,
    vars_list: List[str],
    selected_pi: List[str],
    pi_to_minterms: Dict[str, List[int]]
) -> List[Step]:
    """
    Build absorption steps to remove covered minterms using consensus.
    
    NOTE: Currently disabled because we cannot justify these steps
    with classical Boolean laws only. The consensus theorem requires
    understanding of covering relationships which is QM-specific logic.
    
    Returning empty steps to avoid "cheating" - showing steps that
    aren't actually justified by Boolean laws the user sees.
    """
    steps: List[Step] = []
    
    # DISABLED: This would just replace the expression without actual justification
    # The consensus/covering logic is QM-specific and cannot be explained
    # using only classical Boolean laws that the user sees.
    
    return steps


def _extract_lits_from_term(term: Any) -> List[Tuple[str, bool]]:
    """Extract list of (var, polarity) from a term node."""
    if not isinstance(term, dict):
        # Single literal
        if term.get("op") == "VAR":
            return [(term.get("name"), True)]
        elif term.get("op") == "NOT":
            child = term.get("child")
            if isinstance(child, dict) and child.get("op") == "VAR":
                return [(child.get("name"), False)]
        elif term.get("op") == "CONST":
            return []  # Constants don't have literals
        return []
    
    op = term.get("op")
    if op == "AND":
        # Collect all literals from AND
        lits = []
        for arg in term.get("args", []):
            lits.extend(_extract_lits_from_term(arg))
        return lits
    elif op == "VAR":
        return [(term.get("name"), True)]
    elif op == "NOT":
        child = term.get("child")
        if isinstance(child, dict) and child.get("op") == "VAR":
            return [(child.get("name"), False)]
    
    return []


def ensure_pair_present(
    ast: Any,
    vars_list: List[str],
    left_mask: str,
    right_mask: str
) -> Tuple[Any, List[Step]]:
    """
    Ensure that the two terms (left_mask, right_mask) are present as distinct OR operands.
    
    If they're not present, use controlled distribution to uncover them.
    Returns (new_ast, steps_added).
    
    Strategy: Find the common literals, then distribute to separate the differing variable.
    Example: If we have (A∧B∧C) and need (A∧C) and (A∧¬C), 
    we distribute A∧(B∧C ∨ ¬(B∧C)) to get A∧B∧C ∨ A∧¬B∧C ∨ A∧¬C.
    """
    steps: List[Step] = []
    
    # Convert masks to literals
    left_lits = _mask_to_lits(left_mask, vars_list)
    right_lits = _mask_to_lits(right_mask, vars_list)
    
    # Build AST nodes for the two terms we need
    left_node = term_from_lits(left_lits)
    right_node = term_from_lits(right_lits)
    
    # Check if both nodes already exist as distinct OR operands
    working_ast = ast
    for path, sub in iter_nodes(working_ast):
        if isinstance(sub, dict) and sub.get("op") == "OR":
            args = sub.get("args", [])
            has_left = any(canon(arg) == canon(left_node) for arg in args)
            has_right = any(canon(arg) == canon(right_node) for arg in args)
            if has_left and has_right:
                # Both already present!
                return (working_ast, steps)
    
    # Not both present - need to uncover them via distribution
    # This is complex and needs careful implementation
    # For now, return as-is and let build_merge_steps skip
    
    return (working_ast, steps)


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

