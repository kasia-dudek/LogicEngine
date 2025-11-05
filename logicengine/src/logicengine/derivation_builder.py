# derivation_builder.py
"""Build user-visible simplification steps from QM trace using only Boolean laws."""

from __future__ import annotations

import copy
from typing import Any, List, Tuple, Dict, Optional
from .steps import Step, RuleName
from .ast import generate_ast, canonical_str, normalize_bool_ast, canonical_str_minimal, pretty_with_spans
from .utils import truth_table_hash
from .laws import VAR, NOT, AND, OR, CONST, to_lit, lit_to_node, term_from_lits, canonical_lits, iter_nodes, set_by_path
from .laws import canon, pretty, pretty_with_tokens, find_subtree_span_by_path_cp, term_is_contradictory
from .laws import _pretty_with_tokens_internal


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


def convert_to_dnf_with_laws(ast: Any, vars_list: List[str]) -> Tuple[Any, List[Step]]:
    """
    Convert AST to DNF using logical laws (distribution) step by step.
    Returns (dnf_ast, steps).
    """
    steps: List[Step] = []
    working_ast = ast
    
    # Keep applying distribution until we reach DNF
    max_iterations = 50
    for iteration in range(max_iterations):
        if is_dnf(working_ast):
            break
        
        # Find AND nodes that contain OR (these need distribution)
        # Pattern: AND(..., OR(...), ...) → distribute OR over other AND args
        distribution_applied = False
        
        for path, node in iter_nodes(working_ast):
            if isinstance(node, dict) and node.get("op") == "AND":
                args = node.get("args", [])
                
                # Find OR argument
                or_idx = None
                or_node = None
                for idx, arg in enumerate(args):
                    if isinstance(arg, dict) and arg.get("op") == "OR":
                        or_idx = idx
                        or_node = arg
                        break
                
                if or_idx is not None and or_node is not None:
                    # Found AND with OR argument - apply distribution
                    # A∧(B∨C) → (A∧B)∨(A∧C)
                    or_args = or_node.get("args", [])
                    other_and_args = [arg for i, arg in enumerate(args) if i != or_idx]
                    
                    # Create distributed terms: (A∧B), (A∧C), ...
                    distributed_terms = []
                    for or_arg in or_args:
                        # Combine or_arg with other_and_args
                        new_term_args = [or_arg] + other_and_args
                        if len(new_term_args) == 1:
                            distributed_terms.append(new_term_args[0])
                        else:
                            distributed_terms.append({"op": "AND", "args": new_term_args})
                    
                    # Create OR of distributed terms
                    distributed_result = {"op": "OR", "args": distributed_terms} if len(distributed_terms) > 1 else distributed_terms[0]
                    
                    # Generate step
                    before_str, _ = pretty_with_tokens(working_ast)
                    before_canon = canonical_str(working_ast)
                    
                    # Calculate subexpressions
                    before_subexpr = node
                    after_subexpr = distributed_result
                    before_subexpr_str = pretty(before_subexpr)
                    after_subexpr_str = pretty(after_subexpr)
                    before_subexpr_canon = canonical_str(before_subexpr)
                    after_subexpr_canon = canonical_str(after_subexpr)
                    
                    # Calculate spans
                    before_highlight_spans_cp = []
                    before_span = find_subtree_span_by_path_cp(path, working_ast) if path else None
                    if before_span:
                        before_highlight_spans_cp.append((before_span["start"], before_span["end"]))
                    
                    working_ast_temp = set_by_path(working_ast, path, distributed_result)
                    working_ast_temp = normalize_bool_ast(working_ast_temp, expand_imp_iff=True)
                    
                    contradiction_steps = build_contradiction_steps(working_ast_temp, vars_list)
                    if contradiction_steps:
                        working_ast = generate_ast(contradiction_steps[-1].after_str)
                        working_ast = normalize_bool_ast(working_ast, expand_imp_iff=True)
                    else:
                        working_ast = working_ast_temp
                    
                    after_str, _ = pretty_with_tokens(working_ast)
                    after_canon = canonical_str(working_ast)
                    
                    after_highlight_spans_cp = []
                    
                    # Strategy: First try to find after_subexpr as a complete subtree in working_ast
                    # using canonical comparison
                    after_subexpr_normalized = normalize_bool_ast(after_subexpr, expand_imp_iff=True)
                    after_subexpr_canon_search = canonical_str(after_subexpr_normalized)
                    
                    found_after_subexpr = False
                    for after_path, after_node in iter_nodes(working_ast):
                        after_node_canon = canonical_str(after_node)
                        if after_node_canon == after_subexpr_canon_search:
                            # Found it - get span
                            after_span = find_subtree_span_by_path_cp(after_path, working_ast)
                            if after_span:
                                # Extend span to include outer parentheses if needed
                                span_start = after_span["start"]
                                span_end = after_span["end"]
                                
                                # Check if after_subexpr is a simple node (VAR, CONST)
                                is_simple_node = (
                                    isinstance(after_subexpr_normalized, dict) and 
                                    after_subexpr_normalized.get("op") in {"VAR", "CONST"}
                                )
                                
                                if not is_simple_node:
                                    # For complex nodes, extend span to include outer parentheses if needed
                                    merged_start = span_start
                                    for i in range(span_start - 1, -1, -1):
                                        if after_str[i] == '(':
                                            merged_start = i
                                            break
                                    
                                    merged_end = span_end
                                    for i in range(span_end, len(after_str)):
                                        if after_str[i] == ')':
                                            merged_end = i + 1
                                            break
                                    
                                    after_highlight_spans_cp.append((merged_start, merged_end))
                                else:
                                    # For simple nodes, use the span directly without extending
                                    after_highlight_spans_cp.append((span_start, span_end))
                                found_after_subexpr = True
                                break
                    
                    # If not found as complete subtree, try to find all terms from distributed_result
                    # After normalization, distributed_result's terms may be scattered as separate OR arguments
                    # We need to find all of them and combine their spans
                    if not found_after_subexpr and isinstance(distributed_result, dict) and distributed_result.get("op") == "OR":
                        distributed_terms = distributed_result.get("args", [])
                        
                        # Find all distributed terms in working_ast
                        # They should be arguments of the root OR (or a parent OR)
                        found_term_spans = []
                        for dist_term in distributed_terms:
                            dist_term_normalized = normalize_bool_ast(dist_term, expand_imp_iff=True)
                            dist_term_canon = canonical_str(dist_term_normalized)
                            
                            # Search for this term in working_ast
                            # It should be an argument of an OR node (preferably root OR)
                            for after_path, after_node in iter_nodes(working_ast):
                                after_node_canon = canonical_str(after_node)
                                if after_node_canon == dist_term_canon:
                                    # Check if it's an OR argument (not nested)
                                    is_or_arg = False
                                    if after_path:
                                        # Check if parent is OR
                                        parent_path = after_path[:-1]
                                        parent_node = working_ast
                                        for key, idx in parent_path:
                                            if key == "args":
                                                parent_node = parent_node["args"][idx]
                                        if isinstance(parent_node, dict) and parent_node.get("op") == "OR":
                                            is_or_arg = True
                                    else:
                                        # Root node - check if it's OR
                                        if isinstance(working_ast, dict) and working_ast.get("op") == "OR":
                                            is_or_arg = True
                                    
                                    if is_or_arg:
                                        term_span = find_subtree_span_by_path_cp(after_path, working_ast)
                                        if term_span:
                                            # Extend span to include outer parentheses if needed
                                            span_start = term_span["start"]
                                            span_end = term_span["end"]
                                            
                                            # Find opening parenthesis before span
                                            merged_start = span_start
                                            for i in range(span_start - 1, -1, -1):
                                                if after_str[i] == '(':
                                                    merged_start = i
                                                    break
                                            
                                            # Find closing parenthesis after span
                                            merged_end = span_end
                                            for i in range(span_end, len(after_str)):
                                                if after_str[i] == ')':
                                                    merged_end = i + 1
                                                    break
                                            
                                            found_term_spans.append((merged_start, merged_end))
                                        break
                        
                        # If we found all terms (or at least most of them), combine their spans
                        # We need at least 2 terms to create a meaningful highlight
                        if len(found_term_spans) >= min(2, len(distributed_terms)):
                            # Sort by start position
                            found_term_spans.sort(key=lambda s: s[0])
                            
                            # Merge spans to cover the entire fragment (A∧B)∨(A∧C)
                            # Include opening parenthesis before first term and closing parenthesis after last term
                            first_term_start = found_term_spans[0][0]
                            last_term_end = found_term_spans[-1][1]
                            
                            # Find the opening parenthesis before the first term
                            merged_start = first_term_start
                            for i in range(first_term_start - 1, -1, -1):
                                if after_str[i] == '(':
                                    merged_start = i
                                    break
                            
                            # Find the closing parenthesis after the last term
                            merged_end = last_term_end
                            for i in range(last_term_end, len(after_str)):
                                if after_str[i] == ')':
                                    merged_end = i + 1
                                    break
                            
                            # The merged span should cover from opening ( to closing )
                            # This includes the ∨ operators between terms
                            after_highlight_spans_cp.append((merged_start, merged_end))
                    else:
                        # distributed_result is a single term (shouldn't happen, but handle it)
                        distributed_result_normalized = normalize_bool_ast(distributed_result, expand_imp_iff=True)
                        distributed_result_canon = canonical_str(distributed_result_normalized)
                        
                        for after_path, after_node in iter_nodes(working_ast):
                            if canonical_str(after_node) == distributed_result_canon:
                                after_span = find_subtree_span_by_path_cp(after_path, working_ast)
                                if after_span:
                                    after_highlight_spans_cp.append((after_span["start"], after_span["end"]))
                                break
                    
                    # Fallback: if not found, try to find by path
                    if not after_highlight_spans_cp:
                        # The distributed_result should be at the same path where we replaced it
                        # But after normalization, it might be at a different location
                        # Try the original path first
                        after_span = find_subtree_span_by_path_cp(path, working_ast) if path else None
                        if after_span:
                            after_highlight_spans_cp.append((after_span["start"], after_span["end"]))
                    
                    # Verify equivalence
                    is_equal = (truth_table_hash(vars_list, before_str) == truth_table_hash(vars_list, after_str))
                    
                    step = Step(
                        before_str=before_str,
                        after_str=after_str,
                        rule="Dystrybutywność (A∧(B∨C))",
                        category="user",
                        schema="A∧(B∨C) → (A∧B)∨(A∧C)",
                        location=path,
                        proof={"method": "tt-hash", "equal": is_equal},
                        before_canon=before_canon,
                        after_canon=after_canon,
                        before_subexpr=before_subexpr_str,
                        after_subexpr=after_subexpr_str,
                        before_subexpr_canon=before_subexpr_canon,
                        after_subexpr_canon=after_subexpr_canon,
                        before_highlight_spans_cp=before_highlight_spans_cp if before_highlight_spans_cp else None,
                        after_highlight_spans_cp=after_highlight_spans_cp if after_highlight_spans_cp else None,
                    )
                    steps.append(step)
                    distribution_applied = True
                    break  # Restart search after each change
        
        if not distribution_applied:
            # No more distributions possible - should be in DNF now
            break
    
    return (working_ast, steps)


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


def _find_spans_for_subtree(subtree: Any, full_tree: Any, path: Optional[List] = None) -> Tuple[List[Tuple[int, int]], str]:
    """
    Find code-point spans for a subtree within full_tree using pretty_with_spans.
    
    Args:
        subtree: The AST node to find
        full_tree: The full AST tree
        path: Optional path to the subtree (for faster lookup)
    
    Returns:
        Tuple of (spans, text) where:
        - spans: List of (start_cp, end_cp) tuples in code-point indices
        - text: The generated text from pretty_with_spans (for consistency)
    """
    if subtree is None or full_tree is None:
        return ([], "")
    
    # Normalize both to ensure consistency
    subtree = normalize_bool_ast(subtree, expand_imp_iff=True)
    full_tree = normalize_bool_ast(full_tree, expand_imp_iff=True)
    
    # Get spans map from pretty_with_spans
    text, spans_map = pretty_with_spans(full_tree)
    
    # Find the node_id for subtree
    # If path provided, use it; otherwise search spans_map
    spans = []
    if path is not None:
        node_id = str(path)
        if node_id in spans_map:
            spans = [spans_map[node_id]]
    else:
        # Search all nodes in full_tree to find matching subtree
        for test_path, test_node in iter_nodes(full_tree):
            # Normalize for comparison
            test_node = normalize_bool_ast(test_node, expand_imp_iff=True)
            if canon(test_node) == canon(subtree):
                test_node_id = str(test_path) if test_path else 'root'
                if test_node_id in spans_map:
                    spans = [spans_map[test_node_id]]
                    break
    
    if spans:
        return (spans, text)
    
    # Fallback: try canonical string matching
    subtext, _ = pretty_with_spans(subtree)
    
    # Try exact match
    pos = text.find(subtext)
    if pos != -1:
        return ([(pos, pos + len(subtext))], text)
    
    # Try without outer parentheses
    if subtext.startswith('(') and subtext.endswith(')'):
        subtext_no_parens = subtext[1:-1]
        pos = text.find(subtext_no_parens)
        if pos != -1:
            return ([(pos, pos + len(subtext_no_parens))], text)
    
    return ([], text)


def _extract_focus_text(text: str, spans_cp: List[Tuple[int, int]]) -> List[str]:
    """
    Extract text fragments from text using code-point spans.
    
    Args:
        text: The full text (already NFC normalized)
        spans_cp: List of (start_cp, end_cp) in code-point indices
    
    Returns:
        List of extracted text fragments
    """
    if not spans_cp or not text:
        return []
    
    # Convert to list of code-points
    cps = list(text)
    
    results = []
    for start, end in spans_cp:
        if 0 <= start < end <= len(cps):
            fragment = ''.join(cps[start:end])
            results.append(fragment)
    
    return results


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
        before_str, _ = pretty_with_tokens(working_ast)
        before_canon_1 = canonical_str(working_ast)
        
        # Calculate span for current_product_norm before transformation
        before_highlight_span_1 = find_subtree_span_by_path_cp(current_path, working_ast) if current_path else None
        
        expanded_product = AND([current_product_norm, var_or])
        
        # Replace product in AST
        working_ast = set_by_path(working_ast, current_path, expanded_product)
        working_ast = normalize_bool_ast(working_ast, expand_imp_iff=True)
        after_str_1, _ = pretty_with_tokens(working_ast)
        after_canon_1 = canonical_str(working_ast)
        
        # After: expanded_product is at current_path
        after_highlight_span_1 = find_subtree_span_by_path_cp(current_path, working_ast) if current_path else None
        
        # Verify TT equivalence
        is_equal_1 = (truth_table_hash(vars_list, before_str) == truth_table_hash(vars_list, after_str_1))
        
        step1 = Step(
            before_str=before_str,
            after_str=after_str_1,
            rule="Neutralny (∧1)",
            category="user",
            location=current_path,
            proof={"method": "tt-hash", "equal": is_equal_1},
            before_canon=before_canon_1,
            after_canon=after_canon_1,
            before_span=before_highlight_span_1,
            after_span=after_highlight_span_1,
            before_highlight_span=before_highlight_span_1,
            after_highlight_span=after_highlight_span_1
        )
        steps.append(step1)
        
        # Now distribute: X∧(v∨¬v) => (X∧v) ∨ (X∧¬v)
        before_str_2, _ = pretty_with_tokens(working_ast)
        before_canon_2 = canonical_str(working_ast)
        
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
        
        # Calculate span for expanded_product before distribution
        before_highlight_span_2 = find_subtree_span_by_path_cp(distrib_path, working_ast) if distrib_path else None
        
        # Distribute
        working_ast = _distribute_term(
            working_ast,
            distrib_path,
            current_product_norm,
            var_or
        )
        working_ast = normalize_bool_ast(working_ast, expand_imp_iff=True)
        after_str_2, _ = pretty_with_tokens(working_ast)
        after_canon_2 = canonical_str(working_ast)
        
        # After: distributed result is at distrib_path (replaces expanded_product)
        after_highlight_span_2 = find_subtree_span_by_path_cp(distrib_path, working_ast) if distrib_path else None
        
        # Verify TT equivalence
        is_equal_2 = (truth_table_hash(vars_list, before_str_2) == truth_table_hash(vars_list, after_str_2))
        
        step2 = Step(
            before_str=before_str_2,
            before_canon=before_canon_2,
            after_canon=after_canon_2,
            before_span=before_highlight_span_2,
            after_span=after_highlight_span_2,
            before_highlight_span=before_highlight_span_2,
            after_highlight_span=after_highlight_span_2,
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
    
    # Start with current AST, normalize it first
    working_ast = normalize_bool_ast(current_ast, expand_imp_iff=True)
    
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
        
        # Normalize for comparison (order matters in canon)
        left_node = normalize_bool_ast(left_node, expand_imp_iff=True)
        right_node = normalize_bool_ast(right_node, expand_imp_iff=True)
        result_node = normalize_bool_ast(result_node, expand_imp_iff=True)
        
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
        # Generate pretty strings with tokens for accurate span calculation
        before_str_1, _ = pretty_with_tokens(working_ast)
        before_canon_1 = canonical_str(working_ast)
        
        after_ast_1 = _apply_factoring(working_ast, merge_path, left_idx, right_idx, 
                                        result_node, diff_var)
        after_ast_1 = normalize_bool_ast(after_ast_1, expand_imp_iff=True)
        after_str_1, _ = pretty_with_tokens(after_ast_1)
        after_canon_1 = canonical_str(after_ast_1)
        
        # Compute subexpression for highlighting
        # Before: the OR of left and right terms (the two being factored)
        # After: the factored expression result_node ∧ (diff_var ∨ ¬diff_var)
        diff_node_pos = VAR(diff_var)
        diff_node_neg = NOT(VAR(diff_var))
        diff_or = OR([diff_node_pos, diff_node_neg])
        factored_node = AND([result_node, diff_or])
        
        or_node_before = working_ast
        for key, idx in merge_path:
            if key == "args":
                or_node_before = or_node_before["args"][idx]
        
        # Build the pair being merged
        args_before = or_node_before.get("args", [])
        left_arg = args_before[left_idx] if left_idx is not None else None
        right_arg = args_before[right_idx] if right_idx is not None else None
        
        if left_arg and right_arg:
            before_subexpr = OR([left_arg, right_arg])
            after_subexpr = factored_node
        else:
            before_subexpr = None
            after_subexpr = None
        
        before_subexpr_str = pretty(before_subexpr) if before_subexpr else None
        after_subexpr_str = pretty(after_subexpr) if after_subexpr else None
        before_subexpr_canon = canonical_str(before_subexpr) if before_subexpr else None
        after_subexpr_canon = canonical_str(after_subexpr) if after_subexpr else None
        
        # Calculate spans using path-based lookup
        # For before: the OR node is at merge_path, so use that path directly
        before_highlight_span = find_subtree_span_by_path_cp(merge_path, working_ast) if before_subexpr else None
        
        # For after: need to find the path to factored_node in after_ast_1
        # The factored node should be at merge_path in after_ast_1 (same location as OR was)
        after_highlight_span = find_subtree_span_by_path_cp(merge_path, after_ast_1) if after_subexpr else None
        
        # Compute code-point spans using pretty_with_spans
        before_spans_cp = []
        after_spans_cp = []
        before_text = None
        after_text = None
        
        # For Rozdzielność: Before has TWO separate spans (left_arg and right_arg)
        if left_arg is not None:
            spans_left, text_left = _find_spans_for_subtree(left_arg, working_ast)
            before_spans_cp.extend(spans_left)
            before_text = text_left
        if right_arg is not None:
            spans_right, text_right = _find_spans_for_subtree(right_arg, working_ast)
            before_spans_cp.extend(spans_right)
            if not before_text:
                before_text = text_right
        
        # After has ONE span (the factored result)
        if after_subexpr is not None:
            spans_after, text_after = _find_spans_for_subtree(after_subexpr, after_ast_1)
            after_spans_cp.extend(spans_after)
            after_text = text_after
        
        # Extract focus texts using the text from pretty_with_spans, not canonical_str
        # This ensures spans indices match the text
        before_focus_texts = _extract_focus_text(before_text, before_spans_cp) if before_text else []
        after_focus_texts = _extract_focus_text(after_text, after_spans_cp) if after_text else []
        
        # Verify TT equivalence
        is_equal_1 = (truth_table_hash(vars, before_str_1) == truth_table_hash(vars, after_str_1))
        
        # Create step with spans relative to before_str/after_str
        step1_dict = {
            "before_str": before_str_1,
            "after_str": after_str_1,
            "rule": "Rozdzielność (faktoryzacja)",
            "category": "user",
            "schema": "XY ∨ X¬Y ⇒ X(Y ∨ ¬Y)",
            "location": None,
            "details": {"step_num": 1, "diff_var": diff_var},
            "proof": {"method": "tt-hash", "equal": is_equal_1},
            "before_canon": before_canon_1,
            "after_canon": after_canon_1,
            "before_subexpr": before_subexpr_str,
            "after_subexpr": after_subexpr_str,
            "before_subexpr_canon": before_subexpr_canon,
            "after_subexpr_canon": after_subexpr_canon,
            "before_span": before_highlight_span,  # Span relative to before_str
            "after_span": after_highlight_span,    # Span relative to after_str
            "before_highlight_span": before_highlight_span,  # Keep for backward compatibility
            "after_highlight_span": after_highlight_span,     # Keep for backward compatibility
            "before_highlight_spans_cp": before_spans_cp if before_spans_cp else None,
            "after_highlight_spans_cp": after_spans_cp if after_spans_cp else None,
            "before_focus_texts": before_focus_texts if before_focus_texts else None,
            "after_focus_texts": after_focus_texts if after_focus_texts else None
        }
        step1 = Step(**step1_dict)
        steps.append(step1)
        # Don't normalize - use _flatten_only to preserve structure for next step
        # Store the flattened version for continuity
        working_ast = _flatten_only(after_ast_1)
        
        # STEP 2: Tautology: Y ∨ ¬Y ⇒ 1
        # IMPORTANT: before_str_2 must equal after_str_1 from step 1 (continuity)
        before_str_2 = after_str_1  # Use after_str_1 from step 1 to ensure continuity
        before_canon_2 = after_canon_1  # Use after_canon_1 from step 1
        
        after_ast_2 = _apply_tautology(working_ast, diff_var)
        # Don't normalize yet - we want to show A∨(A∧1) as the result
        # normalize_bool_ast would apply idempotence (A∨A → A) which is a separate law
        # We'll only do minimal flattening to ensure structure is correct for pretty printing
        after_ast_2_flattened = _flatten_only(after_ast_2)
        # Use pretty_with_tokens_no_norm to avoid normalization that would deduplicate
        after_str_2, _ = pretty_with_tokens_no_norm(after_ast_2_flattened)
        after_canon_2 = canonical_str(after_ast_2_flattened)
        
        # Compute subexpression for highlighting
        diff_node_pos = VAR(diff_var)
        diff_node_neg = NOT(VAR(diff_var))
        diff_or = OR([diff_node_pos, diff_node_neg])
        
        before_subexpr_2 = diff_or
        after_subexpr_2 = CONST(1)
        
        before_subexpr_str_2 = pretty(before_subexpr_2)
        after_subexpr_str_2 = pretty(after_subexpr_2)
        before_subexpr_canon_2 = canonical_str(before_subexpr_2)
        after_subexpr_canon_2 = canonical_str(after_subexpr_2)
        
        # Find path to diff_or in working_ast (it's inside the factored node from step 1)
        # The factored node is at merge_path, and diff_or is its second child (args[1])
        # So path is merge_path + [("args", 1)]
        diff_or_path = merge_path + [("args", 1)]
        before_highlight_span_2 = find_subtree_span_by_path_cp(diff_or_path, working_ast)
        
        # For after: CONST(1) replaces diff_or at the same path
        after_highlight_span_2 = find_subtree_span_by_path_cp(diff_or_path, after_ast_2)
        
        # Compute code-point spans for Tautology (single span before and after)
        before_spans_cp_2, before_text_2 = _find_spans_for_subtree(before_subexpr_2, working_ast) if before_subexpr_2 else ([], "")
        after_spans_cp_2, after_text_2 = _find_spans_for_subtree(after_subexpr_2, after_ast_2) if after_subexpr_2 else ([], "")
        before_focus_texts_2 = _extract_focus_text(before_text_2, before_spans_cp_2) if before_text_2 else []
        after_focus_texts_2 = _extract_focus_text(after_text_2, after_spans_cp_2) if after_text_2 else []
        
        # Verify TT equivalence
        is_equal_2 = (truth_table_hash(vars, before_str_2) == truth_table_hash(vars, after_str_2))
        
        step2_dict = {
            "before_str": before_str_2,
            "after_str": after_str_2,
            "rule": "Tautologia",
            "category": "user",
            "schema": "Y ∨ ¬Y ⇒ 1",
            "location": None,
            "details": {"step_num": 2, "diff_var": diff_var},
            "proof": {"method": "tt-hash", "equal": is_equal_2},
            "before_canon": before_canon_2,
            "after_canon": after_canon_2,
            "before_subexpr": before_subexpr_str_2,
            "after_subexpr": after_subexpr_str_2,
            "before_subexpr_canon": before_subexpr_canon_2,
            "after_subexpr_canon": after_subexpr_canon_2,
            "before_span": before_highlight_span_2,
            "after_span": after_highlight_span_2,
            "before_highlight_span": before_highlight_span_2,
            "after_highlight_span": after_highlight_span_2,
            "before_highlight_spans_cp": before_spans_cp_2 if before_spans_cp_2 else None,
            "after_highlight_spans_cp": after_spans_cp_2 if after_spans_cp_2 else None,
            "before_focus_texts": before_focus_texts_2 if before_focus_texts_2 else None,
            "after_focus_texts": after_focus_texts_2 if after_focus_texts_2 else None
        }
        step2 = Step(**step2_dict)
        steps.append(step2)
        
        # STEP 3: Neutral element: X ∧ 1 ⇒ X
        # IMPORTANT: before_str_3 must equal after_str_2 (continuity)
        before_str_3 = after_str_2  # Use after_str_2 from step 2 to ensure continuity
        before_canon_3 = after_canon_2  # Use after_canon_2 from step 2
        
        # Find the AND node with CONST(1) BEFORE flattening
        # Use after_ast_2 (not after_ast_2_flattened) to find the node with CONST(1)
        # because _flatten_only might have changed the structure
        before_subexpr_3 = None
        after_subexpr_3 = None
        neutral_path = None
        
        # Search in after_ast_2 (before flatten) for AND node with CONST(1)
        # This ensures we find the node with CONST(1) in its original structure
        found_in_ast = False
        for path, sub in iter_nodes(after_ast_2):
            if isinstance(sub, dict) and sub.get("op") == "AND":
                args = sub.get("args", [])
                has_const_1 = any(isinstance(arg, dict) and arg.get("op") == "CONST" and arg.get("value") == 1 for arg in args)
                if has_const_1:
                    # Store the original node with CONST(1) - this is what we want to show
                    # Use deep copy to preserve the structure with CONST(1)
                    before_subexpr_3 = copy.deepcopy(sub)
                    # Find the corresponding path in the flattened version for later use
                    neutral_path = path
                    # Compute what it will become (remove CONST(1))
                    new_args = [arg for arg in args if not (isinstance(arg, dict) and arg.get("op") == "CONST" and arg.get("value") == 1)]
                    if len(new_args) == 1:
                        after_subexpr_3 = copy.deepcopy(new_args[0])
                    else:
                        after_subexpr_3 = {"op": "AND", "args": copy.deepcopy(new_args)} if new_args else None
                    found_in_ast = True
                    break
        
        # If we didn't find it in AST structure, try to extract from after_str_2
        # This can happen if the structure was modified but the string still contains "∧1"
        if not found_in_ast and "∧1" in after_str_2:
            import re
            # Find expressions containing "∧1" in after_str_2
            # Pattern: find parenthesized expressions like (A∧¬B∧1) or (A∧1∧B)
            pattern = r'\([^()]*∧1[^()]*\)'
            matches = re.findall(pattern, after_str_2)
            if matches:
                # Use the first match that contains "∧1"
                # Parse it to get the structure
                match_str = matches[0]
                try:
                    # Remove outer parentheses and parse
                    inner = match_str[1:-1]  # Remove ( and )
                    parsed_ast = generate_ast(inner)
                    # Normalize to boolean form
                    parsed_ast_bool = _to_bool_norm(parsed_ast)
                    # Check if it's an AND node
                    if isinstance(parsed_ast_bool, dict) and parsed_ast_bool.get("op") == "AND":
                        before_subexpr_3 = parsed_ast_bool
                        # Compute after_subexpr by removing CONST(1)
                        args = parsed_ast_bool.get("args", [])
                    new_args = [arg for arg in args if not (isinstance(arg, dict) and arg.get("op") == "CONST" and arg.get("value") == 1)]
                    if len(new_args) == 1:
                        after_subexpr_3 = new_args[0]
                    else:
                            after_subexpr_3 = {"op": "AND", "args": new_args} if new_args else None
                        # Find path in working_ast for highlighting (approximate)
                        neutral_path = None
                        for path, sub in iter_nodes(working_ast):
                            if isinstance(sub, dict) and sub.get("op") == "AND":
                                sub_args = sub.get("args", [])
                                # Check if this AND matches our after_subexpr (without CONST(1))
                                if after_subexpr_3:
                                    if canonical_str(sub) == canonical_str(after_subexpr_3):
                                        neutral_path = path
                    break
                except Exception:
                    # If parsing fails, continue with original logic
                    pass
        
        # Store the flattened version for continuity with next step
        working_ast = after_ast_2_flattened
        
        # If we didn't find an AND with CONST(1), skip this step
        if not before_subexpr_3 or not neutral_path:
            # Skip step 3 - no neutral element to remove
            return steps
        
        # Verify that before_subexpr_3 actually contains CONST(1) in its structure
        # If not, something went wrong - but we should have found it above
        if isinstance(before_subexpr_3, dict) and before_subexpr_3.get("op") == "AND":
            args = before_subexpr_3.get("args", [])
            has_const_1 = any(isinstance(arg, dict) and arg.get("op") == "CONST" and arg.get("value") == 1 for arg in args)
            if not has_const_1:
                # This shouldn't happen, but if it does, skip this step
                return steps
        
        # Generate before_subexpr_str_3 and after_subexpr_str_3
        # Similar to "Neutralny (∨0)" which uses before_subexpr="0" and after_subexpr=""
        # We want to show "A∧¬B∧1" → "A∧¬B"
        
        # Strategy: First try to get the string from after_str_2 (which should contain "∧1")
        # This is more reliable than trying to reconstruct from AST structure
        import re
        before_subexpr_str_3 = None
        
        # Get the term without CONST(1) first to use for matching
        if after_subexpr_3:
            after_subexpr_str_3_temp, _ = pretty_with_tokens_no_norm(after_subexpr_3)
            # Remove outer parentheses for matching
            after_subexpr_str_3_temp_clean = after_subexpr_str_3_temp.strip("()")
        else:
            after_subexpr_str_3_temp = ""
            after_subexpr_str_3_temp_clean = ""
        
        # Find expressions containing "∧1" in after_str_2
        # Pattern: find parenthesized expressions like (A∧¬B∧1) or (A∧1∧B)
        pattern = r'\([^()]*∧1[^()]*\)'
        matches = re.findall(pattern, after_str_2)
        if matches:
            # Try to find a match that contains our subexpr (without "1")
            for match in matches:
                # Remove "∧1" or "1∧" from match and check if it matches after_subexpr_str_3_temp
                match_without_1 = match.replace("∧1", "").replace("1∧", "").strip("()")
                if match_without_1 == after_subexpr_str_3_temp_clean or match_without_1.replace("(", "").replace(")", "") == after_subexpr_str_3_temp_clean.replace("(", "").replace(")", ""):
                    before_subexpr_str_3 = match
                    break
        
        # If we didn't find it in after_str_2, try to reconstruct from AST
        if not before_subexpr_str_3:
            # Try to get the string representation with CONST(1)
            # Use pretty_with_tokens_no_norm to avoid normalization
            before_subexpr_str_3, _ = pretty_with_tokens_no_norm(before_subexpr_3)
            
            # Double-check that the string contains "1"
            if "1" not in before_subexpr_str_3:
                # Try to reconstruct from structure by adding CONST(1)
                if isinstance(before_subexpr_3, dict) and before_subexpr_3.get("op") == "AND":
                    args = before_subexpr_3.get("args", [])
                    non_const_args = [arg for arg in args if not (isinstance(arg, dict) and arg.get("op") == "CONST" and arg.get("value") == 1)]
                    # Reconstruct with CONST(1) explicitly added
                    before_subexpr_3_reconstructed = {"op": "AND", "args": non_const_args + [CONST(1)]}
                    before_subexpr_str_3_reconstructed, _ = pretty_with_tokens_no_norm(before_subexpr_3_reconstructed)
                    
                    # If reconstructed string contains "1", use it
                    if "1" in before_subexpr_str_3_reconstructed:
                        before_subexpr_3 = before_subexpr_3_reconstructed
                        before_subexpr_str_3 = before_subexpr_str_3_reconstructed
        
        # Generate after_subexpr_str_3 - this should be the term without CONST(1)
        if after_subexpr_3:
            after_subexpr_str_3, _ = pretty_with_tokens_no_norm(after_subexpr_3)
        else:
            # If after_subexpr_3 is None, it means all args were CONST(1) - this shouldn't happen
            # But if it does, use empty string like in "Neutralny (∨0)"
            after_subexpr_str_3 = ""
        
        before_subexpr_canon_3 = canonical_str(before_subexpr_3)
        after_subexpr_canon_3 = canonical_str(after_subexpr_3) if after_subexpr_3 else ""
        
        # Use path-based span lookup
        before_highlight_span_3 = find_subtree_span_by_path_cp(neutral_path, working_ast)
        
        after_ast_3 = _apply_neutral(working_ast)
        # Don't normalize yet - normalize_bool_ast would apply idempotence (A∨A → A)
        # which is a separate law that should be in a separate step
        # We'll only flatten to ensure structure is valid for pretty printing
        after_ast_3_flattened = _flatten_only(after_ast_3)
        # Use pretty_with_tokens_no_norm to avoid normalization that would deduplicate
        after_str_3, _ = pretty_with_tokens_no_norm(after_ast_3_flattened)
        after_canon_3 = canonical_str(after_ast_3_flattened)
        
        # For after: if after_subexpr_3 is a single element, it might be at the same path or a parent path
        # First try the same path (if it's still an AND with multiple args)
        if after_subexpr_3:
            after_highlight_span_3 = find_subtree_span_by_path_cp(neutral_path, after_ast_3)
            # If not found at same path, search for it (it might have been lifted to parent)
            if not after_highlight_span_3:
                # Search for the node in after_ast_3 using structural comparison
                after_subexpr_canon = canonical_str(after_subexpr_3)
                for path, node in iter_nodes(after_ast_3):
                    node_canon = canonical_str(node)
                    if node_canon == after_subexpr_canon:
                        after_highlight_span_3 = find_subtree_span_by_path_cp(path, after_ast_3)
                        break
                # If still not found, try searching by matching the pretty string
                if not after_highlight_span_3 and after_subexpr_str_3:
                    after_subexpr_pretty = after_subexpr_str_3
                    for path, node in iter_nodes(after_ast_3):
                        node_pretty = pretty(node)
                        if node_pretty == after_subexpr_pretty:
                            after_highlight_span_3 = find_subtree_span_by_path_cp(path, after_ast_3)
                            break
        else:
            after_highlight_span_3 = None
        
        # Compute code-point spans for Neutral element (single span before and after)
        before_spans_cp_3, before_text_3 = _find_spans_for_subtree(before_subexpr_3, working_ast) if before_subexpr_3 else ([], "")
        after_spans_cp_3, after_text_3 = _find_spans_for_subtree(after_subexpr_3, after_ast_3) if after_subexpr_3 else ([], "")
        before_focus_texts_3 = _extract_focus_text(before_text_3, before_spans_cp_3) if before_text_3 else []
        after_focus_texts_3 = _extract_focus_text(after_text_3, after_spans_cp_3) if after_text_3 else []
        
        # Verify TT equivalence
        is_equal_3 = (truth_table_hash(vars, before_str_3) == truth_table_hash(vars, after_str_3))
        
        step3_dict = {
            "before_str": before_str_3,
            "after_str": after_str_3,
            "rule": "Element neutralny",
            "category": "user",
            "schema": "X ∧ 1 ⇒ X",
            "location": None,
            "details": {"step_num": 3, "diff_var": diff_var},
            "proof": {"method": "tt-hash", "equal": is_equal_3},
            "before_canon": before_canon_3,
            "after_canon": after_canon_3,
            "before_subexpr": before_subexpr_str_3,
            "after_subexpr": after_subexpr_str_3,
            "before_subexpr_canon": before_subexpr_canon_3,
            "after_subexpr_canon": after_subexpr_canon_3,
            "before_span": before_highlight_span_3,
            "after_span": after_highlight_span_3,
            "before_highlight_span": before_highlight_span_3,
            "after_highlight_span": after_highlight_span_3,
            "before_highlight_spans_cp": before_spans_cp_3 if before_spans_cp_3 else None,
            "after_highlight_spans_cp": after_spans_cp_3 if after_spans_cp_3 else None,
            "before_focus_texts": before_focus_texts_3 if before_focus_texts_3 else None,
            "after_focus_texts": after_focus_texts_3 if after_focus_texts_3 else None
        }
        step3 = Step(**step3_dict)
        steps.append(step3)
        # Store the flattened version for continuity with next step
        working_ast = after_ast_3_flattened
        
        # STEP 4: Idempotence (if needed): A ∨ A ⇒ A
        # Check if we have A∨A after removing 1 from A∨(A∧1)
        # This happens when after_step3 we have A∨A
        # IMPORTANT: before_str_4 must equal after_str_3 (continuity)
        before_str_4 = after_str_3  # Use after_str_3 from step 3 to ensure continuity
        before_canon_4 = after_canon_3  # Use after_canon_3 from step 3
        
        # Check if we have an OR node with duplicate arguments
        idempotence_applied = False
        for path, sub in iter_nodes(working_ast):
            if isinstance(sub, dict) and sub.get("op") == "OR":
                args = sub.get("args", [])
                # Check for duplicates using canonical comparison
                seen_canon = set()
                duplicates = []
                for i, arg in enumerate(args):
                    arg_canon = canonical_str(arg)
                    if arg_canon in seen_canon:
                        duplicates.append((i, arg, arg_canon))
                    else:
                        seen_canon.add(arg_canon)
                
                if duplicates:
                    # Found duplicates - apply idempotence
                    before_subexpr_4 = sub
                    # Use pretty_with_tokens_no_norm to avoid normalization
                    # This ensures before_subexpr shows A∨A (not just A)
                    before_subexpr_str_4, _ = pretty_with_tokens_no_norm(before_subexpr_4)
                    before_subexpr_canon_4 = canonical_str(before_subexpr_4)
                    
                    # Remove duplicates
                    unique_args = []
                    seen_canon_unique = set()
                    for arg in args:
                        arg_canon = canonical_str(arg)
                        if arg_canon not in seen_canon_unique:
                            unique_args.append(arg)
                            seen_canon_unique.add(arg_canon)
                    
                    if len(unique_args) == 1:
                        after_subexpr_4 = unique_args[0]
                    else:
                        after_subexpr_4 = {"op": "OR", "args": unique_args}
                    
                    # Use pretty_with_tokens_no_norm to avoid normalization
                    # This ensures before_subexpr shows A∨A (not just A)
                    after_subexpr_str_4, _ = pretty_with_tokens_no_norm(after_subexpr_4)
                    after_subexpr_canon_4 = canonical_str(after_subexpr_4)
                    
                    # Apply idempotence
                    after_ast_4 = set_by_path(working_ast, path, after_subexpr_4)
                    after_ast_4 = _flatten_only(after_ast_4)  # Only flatten, don't dedupe again
                    # Use pretty_with_tokens_no_norm to avoid normalization
                    after_str_4, _ = pretty_with_tokens_no_norm(after_ast_4)
                    after_canon_4 = canonical_str(after_ast_4)
                    
                    # Calculate spans
                    before_highlight_span_4 = find_subtree_span_by_path_cp(path, working_ast)
                    after_highlight_span_4 = find_subtree_span_by_path_cp(path, after_ast_4) if path else None
                    if not after_highlight_span_4 and after_subexpr_4:
                        # Search for after_subexpr_4 in after_ast_4
                        after_subexpr_canon_search = canonical_str(after_subexpr_4)
                        for after_path, after_node in iter_nodes(after_ast_4):
                            if canonical_str(after_node) == after_subexpr_canon_search:
                                after_highlight_span_4 = find_subtree_span_by_path_cp(after_path, after_ast_4)
                                break
                    
                    # Compute code-point spans
                    before_spans_cp_4, before_text_4 = _find_spans_for_subtree(before_subexpr_4, working_ast) if before_subexpr_4 else ([], "")
                    after_spans_cp_4, after_text_4 = _find_spans_for_subtree(after_subexpr_4, after_ast_4) if after_subexpr_4 else ([], "")
                    before_focus_texts_4 = _extract_focus_text(before_text_4, before_spans_cp_4) if before_text_4 else []
                    after_focus_texts_4 = _extract_focus_text(after_text_4, after_spans_cp_4) if after_text_4 else []
                    
                    # Verify TT equivalence
                    is_equal_4 = (truth_table_hash(vars, before_str_4) == truth_table_hash(vars, after_str_4))
                    
                    step4_dict = {
                        "before_str": before_str_4,
                        "after_str": after_str_4,
                        "rule": "Idempotencja (∨)",
                        "category": "user",
                        "schema": "A ∨ A ⇒ A",
                        "location": path,
                        "details": {"step_num": 4},
                        "proof": {"method": "tt-hash", "equal": is_equal_4},
                        "before_canon": before_canon_4,
                        "after_canon": after_canon_4,
                        "before_subexpr": before_subexpr_str_4,
                        "after_subexpr": after_subexpr_str_4,
                        "before_subexpr_canon": before_subexpr_canon_4,
                        "after_subexpr_canon": after_subexpr_canon_4,
                        "before_span": before_highlight_span_4,
                        "after_span": after_highlight_span_4,
                        "before_highlight_span": before_highlight_span_4,
                        "after_highlight_span": after_highlight_span_4,
                        "before_highlight_spans_cp": before_spans_cp_4 if before_spans_cp_4 else None,
                        "after_highlight_spans_cp": after_spans_cp_4 if after_spans_cp_4 else None,
                        "before_focus_texts": before_focus_texts_4 if before_focus_texts_4 else None,
                        "after_focus_texts": after_focus_texts_4 if after_focus_texts_4 else None
                    }
                    step4 = Step(**step4_dict)
                    steps.append(step4)
                    working_ast = after_ast_4
                    idempotence_applied = True
                    break
        
        if not idempotence_applied:
            # No idempotence needed - we're done
            pass
    
    return steps


def build_contradiction_steps(
    ast: Any,
    vars_list: List[str]
) -> List[Step]:
    """
    Build steps to remove contradictory terms (A∧¬A = 0) from DNF expression.
    
    Uses Boolean laws:
    1. Kontradykcja: (A∧...∧¬A∧...) = 0 (replace contradictory term with 0)
    2. Element neutralny (A∨0): Remove 0 from OR (A∨0 = A)
    
    This function should be called early in the simplification process to remove
    contradictions immediately, before other rules are applied.
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
        
        for path, sub in iter_nodes(working_ast):
            if not (isinstance(sub, dict) and sub.get("op") == "OR"):
                continue
            
            args = sub.get("args", [])
            if len(args) == 0:
                continue
            
            new_args = []
            has_contradiction = False
            
            for arg in args:
                if isinstance(arg, dict) and arg.get("op") == "AND":
                    and_args = arg.get("args", [])
                    lits = [to_lit(x) for x in and_args]
                    lits_filtered = [t for t in lits if t is not None]
                    
                    if len(lits_filtered) > 0 and term_is_contradictory(lits_filtered):
                        has_contradiction = True
                        changed = True
                    else:
                        new_args.append(arg)
                else:
                    new_args.append(arg)
            
            if has_contradiction:
                before_str, _ = pretty_with_tokens(working_ast)
                before_canon = canonical_str(working_ast)
                
                before_highlight_spans_cp = []
                contradictory_terms = []
                for arg in args:
                    if isinstance(arg, dict) and arg.get("op") == "AND":
                        and_args = arg.get("args", [])
                        lits = [to_lit(x) for x in and_args]
                        lits_filtered = [t for t in lits if t is not None]
                        if len(lits_filtered) > 0 and term_is_contradictory(lits_filtered):
                            contradictory_terms.append(arg)
                
                for term in contradictory_terms:
                    for term_path, term_node in iter_nodes(working_ast):
                        if isinstance(term_node, dict) and canonical_str(term_node) == canonical_str(term):
                            term_span = find_subtree_span_by_path_cp(term_path, working_ast)
                            if term_span:
                                before_highlight_spans_cp.append((term_span["start"], term_span["end"]))
                            break
                
                # Remove contradictory terms (they become 0, which will be removed)
                # If all terms are contradictory, result is CONST(0)
                if len(new_args) == 0:
                    after_ast = CONST(0)
                elif len(new_args) == 1:
                    after_ast = new_args[0]
                else:
                    after_ast = {"op": "OR", "args": new_args}
                
                # Now remove CONST(0) if present (element neutralny)
                if isinstance(after_ast, dict) and after_ast.get("op") == "OR":
                    final_args = []
                    has_zero = False
                    for arg in after_ast.get("args", []):
                        if isinstance(arg, dict) and arg.get("op") == "CONST" and arg.get("value") == 0:
                            has_zero = True
                            # Don't add 0 (will be removed)
                        else:
                            final_args.append(arg)
                    
                    if has_zero:
                        if len(final_args) == 0:
                            after_ast = CONST(0)
                        elif len(final_args) == 1:
                            after_ast = final_args[0]
                        else:
                            after_ast = {"op": "OR", "args": final_args}
                
                after_ast = normalize_bool_ast(after_ast, expand_imp_iff=True)
                after_str, _ = pretty_with_tokens(after_ast)
                after_canon = canonical_str(after_ast)
                
                before_subexpr_str = " ∨ ".join([pretty(t) for t in contradictory_terms])
                after_subexpr_str = "0" if len(contradictory_terms) > 0 else pretty(after_ast)
                
                after_highlight_spans_cp = []
                
                step = Step(
                    rule="Kontradykcja",
                    before_str=before_str,
                    after_str=after_str,
                    before_canon=before_canon,
                    after_canon=after_canon,
                    before_subexpr=before_subexpr_str,
                    after_subexpr=after_subexpr_str,
                    before_subexpr_canon=canonical_str(contradictory_terms[0]) if contradictory_terms else "",
                    after_subexpr_canon="0",
                    before_highlight_spans_cp=before_highlight_spans_cp if len(before_highlight_spans_cp) > 0 else None,
                    after_highlight_spans_cp=after_highlight_spans_cp if len(after_highlight_spans_cp) > 0 else None,
                )
                steps.append(step)
                
                if path:
                    working_ast = set_by_path(working_ast, path, after_ast)
                else:
                    working_ast = after_ast
                working_ast = normalize_bool_ast(working_ast, expand_imp_iff=True)
                
                break
        
        for path, sub in iter_nodes(working_ast):
            if not (isinstance(sub, dict) and sub.get("op") == "OR"):
                continue
            
            args = sub.get("args", [])
            has_zero = any(
                isinstance(a, dict) and a.get("op") == "CONST" and a.get("value") == 0
                for a in args
            )
            
            if has_zero:
                new_args = [
                    a for a in args
                    if not (isinstance(a, dict) and a.get("op") == "CONST" and a.get("value") == 0)
                ]
                
                if len(new_args) == 0:
                    after_ast = CONST(0)
                elif len(new_args) == 1:
                    after_ast = new_args[0]
                else:
                    after_ast = {"op": "OR", "args": new_args}
                
                after_ast = normalize_bool_ast(after_ast, expand_imp_iff=True)
                
                # Generate step for element neutralny
                before_str, _ = pretty_with_tokens(working_ast)
                after_str, _ = pretty_with_tokens(after_ast)
                before_canon = canonical_str(working_ast)
                after_canon = canonical_str(after_ast)
                
                # Find 0 in working_ast for highlighting
                before_highlight_spans_cp = []
                for zero_path, zero_node in iter_nodes(working_ast):
                    if isinstance(zero_node, dict) and zero_node.get("op") == "CONST" and zero_node.get("value") == 0:
                        zero_span = find_subtree_span_by_path_cp(zero_path, working_ast)
                        if zero_span:
                            before_highlight_spans_cp.append((zero_span["start"], zero_span["end"]))
                
                step = Step(
                    rule="Neutralny (∨0)",
                    before_str=before_str,
                    after_str=after_str,
                    before_canon=before_canon,
                    after_canon=after_canon,
                    before_subexpr="0",
                    after_subexpr="",
                    before_subexpr_canon="0",
                    after_subexpr_canon="",
                    before_highlight_spans_cp=before_highlight_spans_cp if len(before_highlight_spans_cp) > 0 else None,
                    after_highlight_spans_cp=None,
                )
                steps.append(step)
                
                if path:
                    working_ast = set_by_path(working_ast, path, after_ast)
                else:
                    working_ast = after_ast
                working_ast = normalize_bool_ast(working_ast, expand_imp_iff=True)
                
                changed = True
                break
    
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
                before_str, _ = pretty_with_tokens(working_ast)
                before_canon_val = canonical_str(working_ast)
                
                # Calculate span for the OR node being modified
                before_span = find_subtree_span_by_path_cp(path, working_ast) if path else None
                
                new_or_node = {"op": "OR", "args": unique_args}
                working_ast = set_by_path(working_ast, path, new_or_node)
                working_ast = normalize_bool_ast(working_ast, expand_imp_iff=True)
                after_str, _ = pretty_with_tokens(working_ast)
                after_canon_val = canonical_str(working_ast)
                
                # After span - same path (OR node is still there, just with fewer args)
                after_span = find_subtree_span_by_path_cp(path, working_ast) if path else None
                
                # Verify TT equivalence
                is_equal = (truth_table_hash(vars_list, before_str) == truth_table_hash(vars_list, after_str))
                
                step = Step(
                    before_str=before_str,
                    after_str=after_str,
                    rule="Idempotencja (∨)",
                    category="user",
                    schema="X ∨ X ⇒ X",
                    location=None,
                    proof={"method": "tt-hash", "equal": is_equal},
                    before_canon=before_canon_val,
                    after_canon=after_canon_val,
                    before_span=before_span,
                    after_span=after_span
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
                    
                    # Check absorption: X ∨ (X∧Y) ⇒ X
                    # We remove the term that is a superset (contains more literals)
                    # For example: (A∧C) ∨ (A∧B∧C) ⇒ (A∧C) (remove A∧B∧C)
                    # Or: (A∧B∧C) ∨ (A∧C) ⇒ (A∧C) (remove A∧B∧C)
                    # So we check if one is subset of the other, and remove the superset
                    lits_i = _extract_lits_from_term(arg_i)
                    lits_j = _extract_lits_from_term(arg_j)
                    
                    if lits_i and lits_j:
                        lits_i_set = set(lits_i)
                        lits_j_set = set(lits_j)
                        
                        # Determine which term to remove
                        term_to_remove_idx = None
                        if lits_j_set.issubset(lits_i_set) and len(lits_i) > len(lits_j):
                            # arg_i is superset of arg_j - remove arg_i
                            term_to_remove_idx = i
                        elif lits_i_set.issubset(lits_j_set) and len(lits_j) > len(lits_i):
                            # arg_j is superset of arg_i - remove arg_j
                            term_to_remove_idx = j
                        
                        if term_to_remove_idx is not None:
                            # Found absorption opportunity
                            # First check if canonical forms match (for exact duplicates handled above)
                            if len(lits_i) == len(lits_j):
                                continue  # Already handled by idempotence
                            
                            # Remove the superset term
                            before_str, _ = pretty_with_tokens(working_ast)
                            before_canon_val = canonical_str(working_ast)
                            
                            # Calculate span for the OR node being modified
                            before_span = find_subtree_span_by_path_cp(path, working_ast) if path else None
                            
                            # Remove the term at term_to_remove_idx
                            new_args = [args[k] for k in range(len(args)) if k != term_to_remove_idx]
                            new_or_node = {"op": "OR", "args": new_args}
                            working_ast = set_by_path(working_ast, path, new_or_node)
                            working_ast = normalize_bool_ast(working_ast, expand_imp_iff=True)
                            after_str, _ = pretty_with_tokens(working_ast)
                            after_canon_val = canonical_str(working_ast)
                            
                            # After span - same path
                            after_span = find_subtree_span_by_path_cp(path, working_ast) if path else None
                            
                            # Verify TT equivalence
                            is_equal = (truth_table_hash(vars_list, before_str) == truth_table_hash(vars_list, after_str))
                            
                            step = Step(
                                before_str=before_str,
                                after_str=after_str,
                                rule="Absorpcja (∨)",
                                category="user",
                                schema="X ∨ (X∧Y) ⇒ X",
                                location=None,
                                proof={"method": "tt-hash", "equal": is_equal},
                                before_canon=before_canon_val,
                                after_canon=after_canon_val,
                                before_span=before_span,
                                after_span=after_span
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
        # Debug: print injection block (commented out for production)
        # print(f"DEBUG: Entering injection block for common_node={canonical_str(common_node)}, diff_var={diff_var}")
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
        
        # Generate pretty strings with tokens
        before_str_1, _ = pretty_with_tokens(working_ast)
        before_canon_1 = canonical_str(working_ast)
        
        # Compute subexpression for highlighting BEFORE transformation
        before_subexpr_1 = common_node
        after_subexpr_1 = new_term
        
        before_subexpr_str_1 = pretty(before_subexpr_1)
        after_subexpr_str_1 = pretty(after_subexpr_1)
        before_subexpr_canon_1 = canonical_str(before_subexpr_1)
        after_subexpr_canon_1 = canonical_str(after_subexpr_1)
        
        # Find position in BEFORE state using path-based lookup
        # common_node might not be directly in working_ast, so we need to find its path
        # Search for it first
        common_node_path = None
        common_node_canon = canonical_str(common_node)
        for path, node in iter_nodes(working_ast):
            if canonical_str(node) == common_node_canon:
                common_node_path = path
                break
        
        before_highlight_span_1 = find_subtree_span_by_path_cp(common_node_path, working_ast) if common_node_path else None
        
        # Apply transformation
        working_ast = set_by_path(working_ast, injection_path, new_or_node)
        working_ast = normalize_bool_ast(working_ast, expand_imp_iff=True)
        after_str_1, _ = pretty_with_tokens(working_ast)
        after_canon_1 = canonical_str(working_ast)
        
        # Find position in AFTER state - find new_term in working_ast after normalization
        # Use canonical comparison to find the correct node
        new_term_normalized = normalize_bool_ast(new_term, expand_imp_iff=True)
        new_term_canon = canonical_str(new_term_normalized)
        
        after_highlight_span_1 = None
        after_highlight_spans_cp_1 = []
        
        # Search for new_term in working_ast using canonical comparison
        for after_path, after_node in iter_nodes(working_ast):
            after_node_canon = canonical_str(after_node)
            if after_node_canon == new_term_canon:
                # Found it - check if it's an OR argument (not nested)
                is_or_arg = False
                if after_path:
                    # Check if parent is OR
                    parent_path = after_path[:-1]
                    parent_node = working_ast
                    for key, idx in parent_path:
                        if key == "args":
                            parent_node = parent_node["args"][idx]
                    if isinstance(parent_node, dict) and parent_node.get("op") == "OR":
                        is_or_arg = True
                else:
                    # Root node - check if it's OR
                    if isinstance(working_ast, dict) and working_ast.get("op") == "OR":
                        is_or_arg = True
                
                if is_or_arg:
                    after_span = find_subtree_span_by_path_cp(after_path, working_ast)
                    if after_span:
                        # Extend span to include outer parentheses
                        # The span from find_subtree_span_by_path_cp doesn't include outer parentheses
                        # So we need to extend: start from opening ( before span, end at closing ) after span
                        span_start = after_span["start"]
                        span_end = after_span["end"]
                        
                        # Find the opening parenthesis before the span
                        merged_start = span_start
                        for i in range(span_start - 1, -1, -1):
                            if after_str_1[i] == '(':
                                merged_start = i
                                break
                        
                        # Find the closing parenthesis after the span
                        merged_end = span_end
                        for i in range(span_end, len(after_str_1)):
                            if after_str_1[i] == ')':
                                merged_end = i + 1
                                break
                        
                        after_highlight_spans_cp_1.append((merged_start, merged_end))
                        after_highlight_span_1 = {"start": merged_start, "end": merged_end}  # Keep for backward compatibility
                        break  # Found and added span, exit loop
                # If span not found but node matches, continue searching (might be nested)
        
        # If we didn't find it using exact canonical match, try a more flexible approach
        # Use pretty_with_tokens to get the same format as after_str_1
        if len(after_highlight_spans_cp_1) == 0:
            new_term_pretty, _ = pretty_with_tokens(normalize_bool_ast(new_term, expand_imp_iff=True))
            # Look for the subexpression in after_str_1
            # Try to find it as a substring (may be without outer parentheses in pretty_with_tokens output)
            if new_term_pretty in after_str_1:
                idx = after_str_1.find(new_term_pretty)
                if idx >= 0:
                    # Always try to find surrounding parentheses
                    merged_start = idx
                    for i in range(idx - 1, -1, -1):
                        if after_str_1[i] == '(':
                            merged_start = i
                            break
                    merged_end = idx + len(new_term_pretty)
                    for i in range(merged_end, len(after_str_1)):
                        if after_str_1[i] == ')':
                            merged_end = i + 1
                            break
                    after_highlight_spans_cp_1.append((merged_start, merged_end))
                    after_highlight_span_1 = {"start": merged_start, "end": merged_end}
        
        # Final fallback: if still not found, use after_subexpr_str to find the highlight
        # This should match what's in after_subexpr_str_1
        if len(after_highlight_spans_cp_1) == 0 and after_subexpr_str_1:
            # Try to find after_subexpr_str_1 in after_str_1
            # Remove outer parentheses if present
            search_str = after_subexpr_str_1
            if search_str.startswith('(') and search_str.endswith(')'):
                # Try with and without parentheses
                search_variants = [search_str, search_str[1:-1]]
            else:
                search_variants = [search_str]
            
            for variant in search_variants:
                if variant in after_str_1:
                    idx = after_str_1.find(variant)
                    if idx >= 0:
                        # Find surrounding parentheses
                        merged_start = idx
                        for i in range(idx - 1, -1, -1):
                            if after_str_1[i] == '(':
                                merged_start = i
                                break
                        merged_end = idx + len(variant)
                        for i in range(merged_end, len(after_str_1)):
                            if after_str_1[i] == ')':
                                merged_end = i + 1
                                break
                        after_highlight_spans_cp_1.append((merged_start, merged_end))
                        after_highlight_span_1 = {"start": merged_start, "end": merged_end}
                        break
        
        # Ultimate fallback: if we know the new_term should be at the start of the OR expression
        # (since it was just added), try to find it by looking for the pattern
        # This is a reliable fallback when other methods fail
        if len(after_highlight_spans_cp_1) == 0:
            # new_term is (C∧¬A)∧(B∨¬B) which normalizes to C∧¬A∧(B∨¬B)
            # In after_str_1 it should appear as (C∧¬A∧(B∨¬B)) at the start
            # Try to match the pattern: starts with (C∧¬A or similar
            if after_str_1.startswith('('):
                # Find the first complete parenthesized expression
                depth = 0
                for i, char in enumerate(after_str_1):
                    if char == '(':
                        depth += 1
                    elif char == ')':
                        depth -= 1
                        if depth == 0:
                            # Found the first complete expression
                            after_highlight_spans_cp_1.append((0, i + 1))
                            after_highlight_span_1 = {"start": 0, "end": i + 1}
                            break
        
        # Verify TT equivalence
        before_hash_1 = truth_table_hash(vars_list, before_str_1)
        after_hash_1 = truth_table_hash(vars_list, after_str_1)
        
        # Calculate before_highlight_spans_cp for common_node
        before_highlight_spans_cp_1 = []
        if before_highlight_span_1:
            before_highlight_spans_cp_1.append((before_highlight_span_1["start"], before_highlight_span_1["end"]))
        
        # Final check: ensure after_highlight_spans_cp_1 is populated
        # This should have been done by the ultimate fallback above, but double-check here
        # This is the last chance before creating step1_dict
        if len(after_highlight_spans_cp_1) == 0:
            if after_str_1 and after_str_1.startswith('('):
                depth = 0
                for i, char in enumerate(after_str_1):
                    if char == '(':
                        depth += 1
                    elif char == ')':
                        depth -= 1
                        if depth == 0:
                            after_highlight_spans_cp_1.append((0, i + 1))
                            after_highlight_span_1 = {"start": 0, "end": i + 1}
                            break
        
        # Debug: print final state (commented out for production)
        # print(f"DEBUG: after_highlight_spans_cp_1 = {after_highlight_spans_cp_1}, len = {len(after_highlight_spans_cp_1)}")
        # print(f"DEBUG: after_str_1 = {after_str_1}")
        # print(f"DEBUG: after_str_1.startswith('(') = {after_str_1.startswith('(') if after_str_1 else False}")
        
        step1_dict = {
            "before_str": before_str_1,
            "after_str": after_str_1,
            "rule": "Odsłonięcie pary (tożsamość)",
            "category": "user",
            "location": injection_path,
            "proof": {"method": "tt-hash", "equal": before_hash_1 == after_hash_1},
            "before_canon": before_canon_1,
            "after_canon": after_canon_1,
            "before_subexpr": before_subexpr_str_1,
            "after_subexpr": after_subexpr_str_1,
            "before_subexpr_canon": before_subexpr_canon_1,
            "after_subexpr_canon": after_subexpr_canon_1,
            "before_span": before_highlight_span_1,
            "after_span": after_highlight_span_1,
            "before_highlight_span": before_highlight_span_1,
            "after_highlight_span": after_highlight_span_1,
            "before_highlight_spans_cp": before_highlight_spans_cp_1 if len(before_highlight_spans_cp_1) > 0 else None,
            "after_highlight_spans_cp": after_highlight_spans_cp_1 if len(after_highlight_spans_cp_1) > 0 else None,
        }
        step1 = Step(**step1_dict)
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
    step1_added = (steps and steps[-1].rule == "Odsłonięcie pary (tożsamość)")
    
    is_distribution = (canon(node_to_split) == canon(AND([common_node, diff_or])))
    
    if not is_distribution and not step1_added:
        # Apply identity X = X∧(v∨¬v)
        expanded_node = AND([common_node, diff_or])
        
        # Generate pretty strings with tokens
        before_str_1, _ = pretty_with_tokens(working_ast)
        before_canon_1 = canonical_str(working_ast)
        
        # Compute subexpression for highlighting
        before_subexpr_1 = node_to_split
        after_subexpr_1 = expanded_node
        
        before_subexpr_str_1 = pretty(before_subexpr_1)
        after_subexpr_str_1 = pretty(after_subexpr_1)
        before_subexpr_canon_1 = canonical_str(before_subexpr_1)
        after_subexpr_canon_1 = canonical_str(after_subexpr_1)
        
        # Find position in BEFORE state using path-based lookup
        before_highlight_span_1 = find_subtree_span_by_path_cp(split_path, working_ast) if split_path else None
        
        # Apply transformation
        working_ast = set_by_path(working_ast, split_path, expanded_node)
        working_ast = normalize_bool_ast(working_ast, expand_imp_iff=True)
        after_str_1, _ = pretty_with_tokens(working_ast)
        after_canon_1 = canonical_str(working_ast)
        
        # Find position in AFTER state - find expanded_node in working_ast after normalization
        # Use canonical comparison to find the correct node
        expanded_node_normalized = normalize_bool_ast(expanded_node, expand_imp_iff=True)
        expanded_node_canon = canonical_str(expanded_node_normalized)
        
        after_highlight_span_1 = None
        after_highlight_spans_cp_1 = []
        
        # Search for expanded_node in working_ast using canonical comparison
        for after_path, after_node in iter_nodes(working_ast):
            after_node_canon = canonical_str(after_node)
            if after_node_canon == expanded_node_canon:
                # Found it - check if it's an OR argument (not nested)
                is_or_arg = False
                if after_path:
                    # Check if parent is OR
                    parent_path = after_path[:-1]
                    parent_node = working_ast
                    for key, idx in parent_path:
                        if key == "args":
                            parent_node = parent_node["args"][idx]
                    if isinstance(parent_node, dict) and parent_node.get("op") == "OR":
                        is_or_arg = True
                else:
                    # Root node - check if it's OR
                    if isinstance(working_ast, dict) and working_ast.get("op") == "OR":
                        is_or_arg = True
                
                if is_or_arg:
                    after_span = find_subtree_span_by_path_cp(after_path, working_ast)
                    if after_span:
                        # Extend span to include outer parentheses
                        span_start = after_span["start"]
                        span_end = after_span["end"]
                        
                        # Find the opening parenthesis before the span
                        merged_start = span_start
                        for i in range(span_start - 1, -1, -1):
                            if after_str_1[i] == '(':
                                merged_start = i
                                break
                        
                        # Find the closing parenthesis after the span
                        merged_end = span_end
                        for i in range(span_end, len(after_str_1)):
                            if after_str_1[i] == ')':
                                merged_end = i + 1
                                break
                        
                        after_highlight_spans_cp_1.append((merged_start, merged_end))
                        after_highlight_span_1 = {"start": merged_start, "end": merged_end}
                        break
        
        # Fallback: if not found, use pretty_with_tokens to find it
        if len(after_highlight_spans_cp_1) == 0:
            expanded_node_pretty, _ = pretty_with_tokens(expanded_node_normalized)
            if expanded_node_pretty in after_str_1:
                idx = after_str_1.find(expanded_node_pretty)
                if idx >= 0:
                    # Find surrounding parentheses
                    merged_start = idx
                    for i in range(idx - 1, -1, -1):
                        if after_str_1[i] == '(':
                            merged_start = i
                            break
                    merged_end = idx + len(expanded_node_pretty)
                    for i in range(merged_end, len(after_str_1)):
                        if after_str_1[i] == ')':
                            merged_end = i + 1
                            break
                    after_highlight_spans_cp_1.append((merged_start, merged_end))
                    after_highlight_span_1 = {"start": merged_start, "end": merged_end}
        
        # Ultimate fallback: find first parenthesized expression
        if len(after_highlight_spans_cp_1) == 0 and after_str_1.startswith('('):
            depth = 0
            for i, char in enumerate(after_str_1):
                if char == '(':
                    depth += 1
                elif char == ')':
                    depth -= 1
                    if depth == 0:
                        after_highlight_spans_cp_1.append((0, i + 1))
                        after_highlight_span_1 = {"start": 0, "end": i + 1}
                        break
        
        # Calculate before_highlight_spans_cp
        before_highlight_spans_cp_1 = []
        if before_highlight_span_1:
            before_highlight_spans_cp_1.append((before_highlight_span_1["start"], before_highlight_span_1["end"]))
        
        # Verify TT equivalence for step 1
        before_hash_1 = truth_table_hash(vars_list, before_str_1)
        after_hash_1 = truth_table_hash(vars_list, after_str_1)
        
        step1_dict = {
            "before_str": before_str_1,
            "after_str": after_str_1,
            "rule": "Odsłonięcie pary (tożsamość)",
            "category": "user",
            "location": split_path,
            "proof": {"method": "tt-hash", "equal": before_hash_1 == after_hash_1},
            "before_canon": before_canon_1,
            "after_canon": after_canon_1,
            "before_subexpr": before_subexpr_str_1,
            "after_subexpr": after_subexpr_str_1,
            "before_subexpr_canon": before_subexpr_canon_1,
            "after_subexpr_canon": after_subexpr_canon_1,
            "before_span": before_highlight_span_1,
            "after_span": after_highlight_span_1,
            "before_highlight_span": before_highlight_span_1,
            "after_highlight_span": after_highlight_span_1,
            "before_highlight_spans_cp": before_highlight_spans_cp_1 if len(before_highlight_spans_cp_1) > 0 else None,
            "after_highlight_spans_cp": after_highlight_spans_cp_1 if len(after_highlight_spans_cp_1) > 0 else None,
        }
        step1 = Step(**step1_dict)
        steps.append(step1)
    
    # STEP 2: Distribute X∧(Y∨Z) → (X∧Y)∨(X∧Z)
    # The expanded_node is AND([common_node, diff_or])
    # We need to find it and distribute
    before_str_2, _ = pretty_with_tokens(working_ast)
    before_canon_2 = canonical_str(working_ast)
    
    # Compute subexpression for highlighting
    expanded_node = AND([common_node, diff_or])
    left_term = AND([common_node, diff_node_pos])
    right_term = AND([common_node, diff_node_neg])
    distributed_result = OR([left_term, right_term])
    
    # Normalize both to match what will be in the AST
    expanded_node = normalize_bool_ast(expanded_node, expand_imp_iff=True)
    distributed_result = normalize_bool_ast(distributed_result, expand_imp_iff=True)
    
    before_subexpr_2 = expanded_node
    after_subexpr_2 = distributed_result
    
    before_subexpr_str_2 = pretty(before_subexpr_2)
    after_subexpr_str_2 = pretty(after_subexpr_2)
    before_subexpr_canon_2 = canonical_str(before_subexpr_2)
    after_subexpr_canon_2 = canonical_str(after_subexpr_2)
    
    # Find position in BEFORE state using path-based lookup
    before_highlight_span_2 = find_subtree_span_by_path_cp(split_path, working_ast) if split_path else None
    
    # Apply transformation
    working_ast = _distribute_term(working_ast, split_path, common_node, diff_or)
    working_ast = normalize_bool_ast(working_ast, expand_imp_iff=True)
    after_str_2, _ = pretty_with_tokens(working_ast)
    after_canon_2 = canonical_str(working_ast)
    
    # Find position in AFTER state - distributed_result is at split_path (replaces expanded_node)
    after_highlight_span_2 = find_subtree_span_by_path_cp(split_path, working_ast) if split_path else None
    
    # Verify TT equivalence for step 2
    before_hash_2 = truth_table_hash(vars_list, before_str_2)
    after_hash_2 = truth_table_hash(vars_list, after_str_2)
    
    step2_dict = {
        "before_str": before_str_2,
        "after_str": after_str_2,
        "rule": "Odsłonięcie pary (Dystrybucja)",
        "category": "user",
        "location": split_path,
        "proof": {"method": "tt-hash", "equal": before_hash_2 == after_hash_2},
        "before_canon": before_canon_2,
        "after_canon": after_canon_2,
        "before_subexpr": before_subexpr_str_2,
        "after_subexpr": after_subexpr_str_2,
        "before_subexpr_canon": before_subexpr_canon_2,
        "after_subexpr_canon": after_subexpr_canon_2,
        "before_span": before_highlight_span_2,
        "after_span": after_highlight_span_2,
        "before_highlight_span": before_highlight_span_2,
        "after_highlight_span": after_highlight_span_2
    }
    step2 = Step(**step2_dict)
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


def pretty_with_tokens_no_norm(node: Any) -> Tuple[str, Dict[str, Tuple[int, int]]]:
    """
    Generate pretty string with token map WITHOUT normalizing (no deduplication).
    This ensures continuity between steps - each step shows only its own transformation.
    """
    # Build tokens from non-normalized representation
    tokens = []
    text, _ = _pretty_with_tokens_internal(node, None, tokens, 0)
    
    # Apply outer parentheses removal (same logic as pretty())
    if text.startswith('(') and text.endswith(')'):
        inner = text[1:-1]
        balance = 0
        can_remove = True
        for char in inner:
            if char == '(':
                balance += 1
            elif char == ')':
                balance -= 1
            if balance < 0:
                can_remove = False
                break
        if balance == 0 and can_remove:
            text = inner
    
    # Build spans_map from tokens
    spans_map: Dict[str, Tuple[int, int]] = {}
    for token in tokens:
        node_id = token.get("path")
        if node_id is not None:
            node_id_str = str(node_id) if isinstance(node_id, list) else str(node_id)
            token_start = token.get("start", 0)
            token_end = token.get("end", 0)
            
            if node_id_str not in spans_map:
                spans_map[node_id_str] = (token_start, token_end)
            else:
                # Extend span if token overlaps or is adjacent
                existing_start, existing_end = spans_map[node_id_str]
                spans_map[node_id_str] = (
                    min(existing_start, token_start),
                    max(existing_end, token_end)
                )
    
    return text, spans_map


def _flatten_only(ast: Any) -> Any:
    """
    Flatten AND/OR nodes but don't dedupe or apply other laws.
    This ensures structure is correct for pretty printing without applying idempotence.
    """
    if not isinstance(ast, dict) or 'op' not in ast:
        return ast
    
    op = ast.get('op')
    if op in {'AND', 'OR'}:
        args = ast.get('args', [])
        if not args:
            return ast
        
        # Flatten nested operators of the same type
        flat = []
        for arg in args:
            if isinstance(arg, dict) and arg.get('op') == op:
                flat.extend(arg.get('args', []))
            else:
                flat.append(_flatten_only(arg))
        
        # Return flattened structure without deduplication
        if len(flat) == 1:
            return flat[0]
        return {"op": op, "args": flat}
    
    # Recursively flatten children
    if 'child' in ast:
        ast = dict(ast)
        ast['child'] = _flatten_only(ast['child'])
    if 'left' in ast:
        ast = dict(ast)
        ast['left'] = _flatten_only(ast['left'])
    if 'right' in ast:
        ast = dict(ast)
        ast['right'] = _flatten_only(ast['right'])
    if 'args' in ast:
        ast = dict(ast)
        ast['args'] = [_flatten_only(a) for a in ast['args']]
    
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

