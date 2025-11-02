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


def _term_contains(term: Any, required_lits: List[Tuple[str, bool]]) -> bool:
    """Check if a term (product of literals) contains all required literals."""
    # Extract literals from term
    term_lits = []
    if isinstance(term, dict):
        if term.get("op") == "AND":
            for arg in term.get("args", []):
                lit = to_lit(arg)
                if lit:
                    term_lits.append(lit)
        else:
            # Single literal
            lit = to_lit(term)
            if lit:
                term_lits.append(lit)
    
    term_lit_set = set(term_lits)
    required_set = set(required_lits)
    
    # Check if all required literals are present
    return required_set.issubset(term_lit_set)


def build_minterm_expansion_steps(
    product_node: Any,
    vars_list: List[str],
    expand_var: str,
    ast: Any,
    product_path: List[Tuple[str, Optional[int]]]
) -> Tuple[Any, List[Step]]:
    """
    Expand a product term by applying identity: X => X∧(v∨¬v).
    
    Strategy: Apply X => X∧(v∨¬v) => (X∧v) ∨ (X∧¬v)
    
    This expands a single product into a sum of two products.
    For multiple variables, call this function iteratively.
    
    Args:
        product_node: The product AST node to expand
        vars_list: List of all variables
        expand_var: Variable to expand over
        ast: The full AST containing product_node
        product_path: Path to product_node in ast
    
    Returns:
        (updated_ast, list_of_steps)
    """
    steps: List[Step] = []
    working_ast = ast
    current_product = product_node
    current_path = product_path
    
    # Convert product to normalized form for comparison
    current_product_norm = normalize_bool_ast(current_product, expand_imp_iff=True)
    
    if expand_var:
        # Create v∨¬v
        var_node_pos = VAR(expand_var)
        var_node_neg = NOT(VAR(expand_var))
        var_or = OR([var_node_pos, var_node_neg])
        
        # Apply identity: X => X∧(v∨¬v)
        before_str = pretty(working_ast)
        expanded_product = AND([current_product_norm, var_or])
        
        # Replace product in AST
        working_ast = set_by_path(working_ast, current_path, expanded_product)
        working_ast = normalize_bool_ast(working_ast, expand_imp_iff=True)
        after_str_1 = pretty(working_ast)
        
        # Verify TT equivalence
        is_equal_1 = (truth_table_hash(vars_list, before_str) == truth_table_hash(vars_list, after_str_1))
        
        step1 = Step(
            before_str=before_str,
            after_str=after_str_1,
            rule="Neutralny (∧1)",
            category="user",
            location=current_path,
            proof={"method": "tt-hash", "equal": is_equal_1}
        )
        steps.append(step1)
        
        # Now distribute: X∧(v∨¬v) => (X∧v) ∨ (X∧¬v)
        before_str_2 = pretty(working_ast)
        
        # Find the expanded product and distribute it
        # After normalization, it might be in a different form
        # We need to locate where the expanded product ended up
        expanded_product_norm = normalize_bool_ast(expanded_product, expand_imp_iff=True)
        distrib_path = None
        
        for path, sub in iter_nodes(working_ast):
            if canon(sub) == canon(expanded_product_norm):
                distrib_path = path
                break
        
        if distrib_path is None:
            # Can't find - return what we have
            return (working_ast, steps)
        
        # Distribute
        working_ast = _distribute_term(
            working_ast,
            distrib_path,
            current_product_norm,
            var_or
        )
        working_ast = normalize_bool_ast(working_ast, expand_imp_iff=True)
        after_str_2 = pretty(working_ast)
        
        # Verify TT equivalence
        is_equal_2 = (truth_table_hash(vars_list, before_str_2) == truth_table_hash(vars_list, after_str_2))
        
        step2 = Step(
            before_str=before_str_2,
            after_str=after_str_2,
            rule="Rozdzielność (faktoryzacja)",
            category="user",
            location=distrib_path,
            proof={"method": "tt-hash", "equal": is_equal_2}
        )
        steps.append(step2)
        
        # After distribution, we have OR of products
        # For next iteration, we would need to expand each product in the OR
        # This is complex and not currently supported in a single call
        # The function supports expanding by one variable at a time
        # For multiple variables, call it iteratively from the caller
    
    return (working_ast, steps)


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
        
        # Try to find the pair, with iterative uncovering if needed
        merge_path = None
        left_idx = None
        right_idx = None
        max_uncover_iterations = 5  # Safety limit to prevent infinite loops
        
        for uncover_iter in range(max_uncover_iterations):
            # Search for OR node containing both left and right terms
            for path, sub in iter_nodes(working_ast):
                if (isinstance(sub, dict) and sub.get("op") == "OR" and 
                    len(sub.get("args", [])) >= 2):
                    # Reset indices for each OR node
                    left_idx = None
                    right_idx = None
                    args = sub.get("args", [])
                    for idx, arg in enumerate(args):
                        if canon(arg) == canon(left_node):
                            left_idx = idx
                        elif canon(arg) == canon(right_node):
                            right_idx = idx
                    
                    if left_idx is not None and right_idx is not None:
                        merge_path = path
                        break
            
            # If found, break out of uncover loop
            if merge_path is not None:
                break
            
            # Pair not found - try to uncover it
            uncovered_ast, uncovered_steps = ensure_pair_present(working_ast, vars, left_mask, right_mask)
            if uncovered_steps:
                # Add the steps to reveal the pair
                steps.extend(uncovered_steps)
                working_ast = uncovered_ast
                # Continue loop to search again
            else:
                # No steps generated - can't uncover, skip this merge
                break
        
        # If still not found after all iterations, skip
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
    Build absorption steps to clean up DNF: remove duplicates and X ∨ (X∧Y) patterns.
    
    Uses only classical Boolean laws:
    1. Idempotence OR: X ∨ X ⇒ X
    2. Absorption: X ∨ (X∧Y) ⇒ X
    
    No QM knowledge - only local AST patterns.
    """
    steps: List[Step] = []
    working_ast = ast
    
    # Stabilization loop: keep applying until no more changes
    max_iterations = 50
    changed = True
    
    for iteration in range(max_iterations):
        if not changed:
            break
        
        changed = False
        
        # Find OR nodes to apply cleanup rules
        for path, sub in iter_nodes(working_ast):
            if not (isinstance(sub, dict) and sub.get("op") == "OR"):
                continue
            
            args = sub.get("args", [])
            if len(args) < 2:
                continue
            
            # RULE 1: Idempotence OR - remove duplicates
            # X ∨ X ⇒ X
            unique_args = []
            seen_canon = set()
            
            for arg in args:
                arg_canon = canon(arg)
                if arg_canon not in seen_canon:
                    unique_args.append(arg)
                    seen_canon.add(arg_canon)
                else:
                    # Found duplicate - will generate a step
                    changed = True
            
            if len(unique_args) < len(args):
                # Duplicates found - create removal step
                before_str = pretty(working_ast)
                new_or_node = {"op": "OR", "args": unique_args}
                working_ast = set_by_path(working_ast, path, new_or_node)
                working_ast = normalize_bool_ast(working_ast, expand_imp_iff=True)
                after_str = pretty(working_ast)
                
                # Verify TT equivalence
                is_equal = (truth_table_hash(vars_list, before_str) == truth_table_hash(vars_list, after_str))
                
                step = Step(
                    before_str=before_str,
                    after_str=after_str,
                    rule="Idempotencja (∨)",
                    category="user",
                    schema="X ∨ X ⇒ X",
                    location=None,
                    proof={"method": "tt-hash", "equal": is_equal}
                )
                steps.append(step)
                break  # Restart search after each change
            
            # RULE 2: Absorption - X ∨ (X∧Y) ⇒ X
            # Check all pairs
            for i in range(len(args)):
                for j in range(len(args)):
                    if i == j:
                        continue
                    
                    arg_i = args[i]
                    arg_j = args[j]
                    
                    # Check if arg_i is a superset of arg_j
                    # i.e., if arg_i contains all literals of arg_j
                    lits_i = _extract_lits_from_term(arg_i)
                    lits_j = _extract_lits_from_term(arg_j)
                    
                    if lits_i and lits_j:
                        lits_i_set = set(lits_i)
                        lits_j_set = set(lits_j)
                        
                        # Check if j is subset of i (i covers j)
                        if lits_j_set.issubset(lits_i_set):
                            # j is redundant - remove it
                            # First check if canonical forms match (for exact duplicates handled above)
                            if len(lits_i) == len(lits_j):
                                continue  # Already handled by idempotence
                            
                            # Remove arg_j
                            before_str = pretty(working_ast)
                            new_args = [args[k] for k in range(len(args)) if k != j]
                            new_or_node = {"op": "OR", "args": new_args}
                            working_ast = set_by_path(working_ast, path, new_or_node)
                            working_ast = normalize_bool_ast(working_ast, expand_imp_iff=True)
                            after_str = pretty(working_ast)
                            
                            # Verify TT equivalence
                            is_equal = (truth_table_hash(vars_list, before_str) == truth_table_hash(vars_list, after_str))
                            
                            step = Step(
                                before_str=before_str,
                                after_str=after_str,
                                rule="Absorpcja (∨)",
                                category="user",
                                schema="X ∨ (X∧Y) ⇒ X",
                                location=None,
                                proof={"method": "tt-hash", "equal": is_equal}
                            )
                            steps.append(step)
                            changed = True
                            break  # Restart search after each change
                
                if changed:
                    break
            
            if changed:
                break
    
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
    
    If they're not present, use identity X = X∧(v∨¬v) and distribution to uncover them.
    Returns (new_ast, steps_added).
    
    Strategy: Find a common term that can be split by the differing variable.
    Example: If we have (A∧B∧C) and need (A∧B∧¬C), we split (A∧B) by C:
    X = (A∧B), v = C
    X → X∧(C∨¬C) → (X∧C)∨(X∧¬C) → (A∧B∧C)∨(A∧B∧¬C)
    """
    steps: List[Step] = []
    working_ast = ast
    
    # Convert masks to literals
    left_lits = _mask_to_lits(left_mask, vars_list)
    right_lits = _mask_to_lits(right_mask, vars_list)
    
    # Build AST nodes for the two terms we need
    left_node = term_from_lits(left_lits)
    right_node = term_from_lits(right_lits)
    
    # Normalize for comparison (order matters in canon)
    left_node = normalize_bool_ast(left_node, expand_imp_iff=True)
    right_node = normalize_bool_ast(right_node, expand_imp_iff=True)
    
    # Check if both nodes already exist as distinct OR operands
    for path, sub in iter_nodes(working_ast):
        if isinstance(sub, dict) and sub.get("op") == "OR":
            args = sub.get("args", [])
            has_left = any(canon(arg) == canon(left_node) for arg in args)
            has_right = any(canon(arg) == canon(right_node) for arg in args)
            if has_left and has_right:
                # Both already present!
                return (working_ast, steps)
    
    # Not both present - need to uncover them
    # Strategy: Find which variable differs and split a common term by it
    
    # Find the differing variable
    diff_var = None
    for i, (l, r) in enumerate(zip(left_mask, right_mask)):
        if l != r:
            diff_var = vars_list[i]
            break
    
    if diff_var is None:
        return (working_ast, steps)
    
    # Find a term that contains the common literals and could be split
    # Common literals = intersection of left and right literals
    left_lit_set = set(left_lits)
    right_lit_set = set(right_lits)
    common_lits = left_lit_set & right_lit_set
    
    if not common_lits:
        # No common literals - can't use this strategy
        return (working_ast, steps)
    
    # Build common term node
    common_node = term_from_lits(list(common_lits))
    
    # Search for a term in the AST that we can split
    # Strategy: Find a term that contains the common literals AND doesn't have diff_var
    # This will allow clean splitting without contradiction
    split_path = None
    split_term = None
    
    # Build set of literals that should NOT be in the term we split
    diff_lit_pos = (diff_var, True)
    diff_lit_neg = (diff_var, False)
    forbidden_lits = {diff_lit_pos, diff_lit_neg}
    
    for path, sub in iter_nodes(working_ast):
        if isinstance(sub, dict) and sub.get("op") == "OR":
            args = sub.get("args", [])
            for idx, arg in enumerate(args):
                # Try exact match first
                if canon(arg) == canon(common_node):
                    split_path = path + [("args", idx)]
                    split_term = arg
                    break
                
                # Try superset: arg contains all common literals AND doesn't contain diff_var
                if _term_contains(arg, common_lits):
                    # Check if arg doesn't contain diff_var (either polarity)
                    if not _term_contains(arg, [diff_lit_pos]) and not _term_contains(arg, [diff_lit_neg]):
                        split_path = path + [("args", idx)]
                        split_term = arg
                        break
            if split_path:
                break
    
    if split_path is None:
        # No suitable term found - need to inject common_node into the expression
        # Find any OR node to add common_node as a term
        # We'll use identity injection: X becomes X ∨ (Y∧(v∨¬v)) where Y is common
        # Actually simpler: just add common_node ∧ (v∨¬v) as a new term
        injection_path = None
        for path, sub in iter_nodes(working_ast):
            if isinstance(sub, dict) and sub.get("op") == "OR":
                injection_path = path
                break
        
        if injection_path is None:
            # Can't inject - return empty
            return (working_ast, steps)
        
        # Create v∨¬v
        diff_node_pos = VAR(diff_var)
        diff_node_neg = NOT(VAR(diff_var))
        diff_or = OR([diff_node_pos, diff_node_neg])
        
        # Add common_node ∧ (v∨¬v) as a new term to the OR
        # Navigate to the OR node to get its args
        or_node = working_ast
        for key, idx in injection_path:
            if key == "args":
                or_node = or_node["args"][idx]
        
        # Get existing args and add new term
        new_term = AND([common_node, diff_or])
        existing_args = or_node.get("args", [])
        new_args = existing_args + [new_term]
        
        # Create new OR node with extended args
        new_or_node = {"op": "OR", "args": new_args}
        
        before_str_1 = pretty(working_ast)
        working_ast = set_by_path(working_ast, injection_path, new_or_node)
        working_ast = normalize_bool_ast(working_ast, expand_imp_iff=True)
        after_str_1 = pretty(working_ast)
        
        # Verify TT equivalence
        before_hash_1 = truth_table_hash(vars_list, before_str_1)
        after_hash_1 = truth_table_hash(vars_list, after_str_1)
        
        step1 = Step(
            before_str=before_str_1,
            after_str=after_str_1,
            rule="Neutralny (∧1)",
            category="user",
            location=injection_path,
            proof={"method": "tt-hash", "equal": before_hash_1 == after_hash_1}
        )
        steps.append(step1)
        
        # Now we have common_node ∧ (v∨¬v) in the AST
        # Need to find it again and distribute
        target_node_norm = normalize_bool_ast(AND([common_node, diff_or]), expand_imp_iff=True)
        for path, sub in iter_nodes(working_ast):
            if isinstance(sub, dict) and sub.get("op") == "OR":
                args = sub.get("args", [])
                for idx, arg in enumerate(args):
                    if canon(arg) == canon(target_node_norm):
                        split_path = path + [("args", idx)]
                        break
                if split_path:
                    break
    
    if split_path is None:
        # Still can't find - return what we have
        return (working_ast, steps)
    
    # STEP 1 (or 2): Apply identity X = X∧(v∨¬v) or distribute existing X∧(v∨¬v)
    diff_node_pos = VAR(diff_var)
    diff_node_neg = NOT(VAR(diff_var))
    diff_or = OR([diff_node_pos, diff_node_neg])
    
    # Check if this is a distribution step or identity step
    node_to_split = working_ast
    for key, idx in split_path:
        if key == "args":
            node_to_split = node_to_split["args"][idx]
    
    # Check if we already added step1 above (injection case)
    step1_added = (steps and steps[-1].rule == "Neutralny (∧1)")
    
    is_distribution = (canon(node_to_split) == canon(AND([common_node, diff_or])))
    
    if not is_distribution and not step1_added:
        # Apply identity X = X∧(v∨¬v)
        expanded_node = AND([common_node, diff_or])
        
        before_str_1 = pretty(working_ast)
        working_ast = set_by_path(working_ast, split_path, expanded_node)
        after_str_1 = pretty(working_ast)
        
        # Verify TT equivalence for step 1
        before_hash_1 = truth_table_hash(vars_list, before_str_1)
        after_hash_1 = truth_table_hash(vars_list, after_str_1)
        
        step1 = Step(
            before_str=before_str_1,
            after_str=after_str_1,
            rule="Neutralny (∧1)",
            category="user",
            location=split_path,
            proof={"method": "tt-hash", "equal": before_hash_1 == after_hash_1}
        )
        steps.append(step1)
    
    # STEP 2: Distribute X∧(Y∨Z) → (X∧Y)∨(X∧Z)
    # The expanded_node is AND([common_node, diff_or])
    # We need to find it and distribute
    before_str_2 = pretty(working_ast)
    working_ast = _distribute_term(working_ast, split_path, common_node, diff_or)
    working_ast = normalize_bool_ast(working_ast, expand_imp_iff=True)
    after_str_2 = pretty(working_ast)
    
    # Verify TT equivalence for step 2
    before_hash_2 = truth_table_hash(vars_list, before_str_2)
    after_hash_2 = truth_table_hash(vars_list, after_str_2)
    
    step2 = Step(
        before_str=before_str_2,
        after_str=after_str_2,
        rule="Rozdzielność (faktoryzacja)",
        category="user",
        location=split_path,
        proof={"method": "tt-hash", "equal": before_hash_2 == after_hash_2}
    )
    steps.append(step2)
    
    # Now we should have the pair present
    # Verify by checking if both left and right nodes exist
    has_both = False
    for path, sub in iter_nodes(working_ast):
        if isinstance(sub, dict) and sub.get("op") == "OR":
            args = sub.get("args", [])
            has_left = any(canon(arg) == canon(left_node) for arg in args)
            has_right = any(canon(arg) == canon(right_node) for arg in args)
            if has_left and has_right:
                has_both = True
                break
    
    if not has_both:
        # Something went wrong - return what we have
        print(f"Warning: ensure_pair_present failed to create both terms")
    
    return (working_ast, steps)


def _distribute_term(
    ast: Any,
    split_path: List[Tuple[str, Optional[int]]],
    common_node: Any,
    diff_or: Any
) -> Any:
    """Apply distribution: X∧(Y∨Z) → (X∧Y)∨(X∧Z) at the given path."""
    # Navigate to the node
    node = ast
    for key, idx in split_path:
        if key == "args":
            node = node["args"][idx]
    
    # The node should be AND([common_node, diff_or])
    # Replace it with OR([AND([common_node, diff_or's args[0]]), AND([common_node, diff_or's args[1]])])
    
    diff_or_args = diff_or.get("args", [])
    if len(diff_or_args) != 2:
        return ast
    
    distributed_args = [
        AND([common_node, diff_or_args[0]]),
        AND([common_node, diff_or_args[1]])
    ]
    
    new_or_node = OR(distributed_args)
    
    # Replace in AST
    return set_by_path(ast, split_path, new_or_node)


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

