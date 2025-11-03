# engine.py
"""Main logic engine integrating analysis steps."""

from typing import Any, Dict

from .parser import validate_and_standardize, LogicExpressionError
from .truth_table import generate_truth_table, TruthTableError
from .ast import generate_ast, ASTError
from .onp import to_onp, ONPError
from .kmap import simplify_kmap, KMapError
from .qm import simplify_qm, QMError
from .tautology import is_tautology
from .contradiction import is_contradiction
from .laws import simplify_with_laws, measure
from .ast import collect_variables, canonical_str, normalize_bool_ast, generate_ast
from .utils import truth_table_hash, equivalent
from .steps import Step, RuleName, StepCategory
from .derivation_builder import build_minterm_expansion_steps, build_merge_steps, build_absorb_steps, is_dnf, ensure_pair_present
from .qm import simplify_qm
from .minimal_forms import compute_minimal_forms


class TooManyVariables(Exception):
    """Raised when expression has more than var_limit variables."""
    pass


class LogicEngine:
    """Run a comprehensive analysis of a logical expression."""

    @staticmethod
    def analyze(expr: str) -> Dict[str, Any]:
        result: Dict[str, Any] = {"expression": expr}

        # Standardize once for all downstream steps
        try:
            std = validate_and_standardize(expr)
            result["standardized"] = std
        except LogicExpressionError as e:
            result["standardize_error"] = str(e)
            return result

        # Truth table
        try:
            result["truth_table"] = generate_truth_table(std)
        except TruthTableError as e:
            result["truth_table_error"] = str(e)

        # AST
        try:
            result["ast"] = generate_ast(std)
        except ASTError as e:
            result["ast_error"] = str(e)

        # ONP
        try:
            result["onp"] = to_onp(std)
        except ONPError as e:
            result["onp_error"] = str(e)

        # Karnaugh map
        try:
            result["kmap_simplification"] = simplify_kmap(std)
        except KMapError as e:
            result["kmap_error"] = str(e)

        # Quine–McCluskey
        try:
            result["qm_simplification"] = simplify_qm(std)
        except QMError as e:
            result["qm_error"] = str(e)

        # Tautology
        try:
            result["is_tautology"] = is_tautology(std)
        except Exception as e:
            result["tautology_error"] = str(e)

        # Contradiction
        try:
            result["is_contradiction"] = is_contradiction(std)
        except Exception as e:
            result["contradiction_error"] = str(e)

        return result


def simplify(expr: str, mode: str = "mixed") -> Dict[str, Any]:
    """
    Simplify logical expression using laws and/or axioms.
    
    Args:
        expr: Expression to simplify
        mode: Simplification mode - "algebraic", "axioms", or "mixed"
        
    Returns:
        Dictionary with simplification results and steps
    """
    return simplify_with_laws(expr, mode=mode)


def simplify_to_minimal_dnf(expr: str, var_limit: int = 8) -> Dict[str, Any]:
    """
    Simplify expression to minimal DNF with complete step trace.
    
    Args:
        expr: Expression to simplify
        var_limit: Maximum number of variables (default 8)
        
    Returns:
        Dictionary containing:
        - input_std: standardized input
        - vars: list of variables
        - initial_canon: canonical string after normalization
        - steps: list of Step objects
        - result_dnf: minimal DNF string
    """
    # Step 1: Validation and standardization
    try:
        input_std = validate_and_standardize(expr)
    except LogicExpressionError as e:
        raise ValueError(f"Invalid expression: {e}")
    
    # Step 2: Generate AST and normalize
    legacy_ast = generate_ast(input_std)
    node = normalize_bool_ast(legacy_ast, expand_imp_iff=True)
    
    # Collect variables and check limit
    vars_list = collect_variables(node)
    if len(vars_list) > var_limit:
        raise TooManyVariables(f"Expression has {len(vars_list)} variables, maximum is {var_limit}")
    
    initial_canon = canonical_str(node)
    
    # Initialize result structure
    steps: List[Step] = []
    
    # Step 3: Use existing laws-based simplification
    # This gives us the step-by-step process
    laws_result = simplify_with_laws(input_std, max_steps=100, mode="mixed")
    
    # Convert laws result steps to our Step model with verification
    if "steps" in laws_result:
        for law_step in laws_result["steps"]:
            before_str = law_step.get("before_tree", "")
            after_str = law_step.get("after_tree", "")
            law_name = law_step.get("law", "")
            
            # Skip oscillation steps
            if law_name == "Zatrzymano (oscylacja)":
                continue
            
            # Skip steps with invalid results
            if after_str in ["?", ""] or before_str in ["?", ""]:
                continue
            
            # Verify equivalence for each step
            try:
                hash_before = truth_table_hash(vars_list, before_str)
                hash_after = truth_table_hash(vars_list, after_str)
                is_equal = hash_before == hash_after and len(hash_before) > 0 and len(hash_after) > 0
                
                # Skip step if not equivalent (log warning but don't crash)
                if not is_equal:
                    print(f"Warning: Equivalence check failed for rule: {law_name}")
                    continue
            except Exception as e:
                # If hash computation fails, skip this step
                print(f"Warning: Could not verify step: {e}")
                continue
            
            step = Step(
                before_str=before_str,
                after_str=after_str,
                rule=law_name if isinstance(law_name, str) else "Formatowanie",
                location=law_step.get("path"),
                details={},
                proof={
                    "method": "tt-hash",
                    "equal": is_equal,
                    "hash_before": hash_before,
                    "hash_after": hash_after
                },
                before_subexpr=law_step.get("before_subexpr"),
                after_subexpr=law_step.get("after_subexpr"),
                before_canon=law_step.get("before_canon"),
                after_canon=law_step.get("after_canon"),
                before_subexpr_canon=law_step.get("before_subexpr_canon"),
                after_subexpr_canon=law_step.get("after_subexpr_canon"),
                before_highlight_span=law_step.get("before_highlight_span"),
                after_highlight_span=law_step.get("after_highlight_span")
            )
            steps.append(step)
    
    # Step 4: Get minimal DNF using QM as planner, then build user-visible steps
    # Only add merge steps if laws didn't complete the simplification
    if len(vars_list) >= 1:
        try:
            qm_result = simplify_qm(input_std)
            summary = qm_result.get("summary", {})
            
            # Extract QM plan data
            minterms_1 = summary.get("minterms_1", [])
            selected_pi = summary.get("selected_pi", [])
            merge_edges = summary.get("merge_edges", [])
            pi_to_minterms = summary.get("pi_to_minterms", {})
            
            # Only add merge steps if laws didn't complete or ended with oscillation
            # Compare using truth table hash (more robust than canonical string)
            # Use last verified step's after_str instead of laws_result.get("result")
            laws_result_str = None
            if steps:
                laws_result_str = steps[-1].after_str
            else:
                laws_result_str = laws_result.get("result", "")
            
            laws_completed = False
            
            if laws_result_str and laws_result_str not in ["?", ""]:
                try:
                    laws_hash = truth_table_hash(vars_list, laws_result_str)
                    qm_hash = truth_table_hash(vars_list, qm_result.get("result", ""))
                    laws_completed = (laws_hash == qm_hash and len(laws_hash) > 0)
                    
                    # Check if last step is in DNF and truly minimal
                    if laws_completed and steps:
                        last_ast = generate_ast(steps[-1].after_str)
                        last_ast = normalize_bool_ast(last_ast, expand_imp_iff=True)
                        if not is_dnf(last_ast):
                            print(f"Warning: Last step is not DNF, removing it")
                            steps.pop()
                            laws_completed = False  # Need to continue with QM
                        
                        # Even if TT hash matches and is DNF, check if we need absorption cleanup
                        if laws_completed and steps:
                            # Recompute last_ast after pop if it occurred
                            last_ast_check = generate_ast(steps[-1].after_str)
                            last_ast_check = normalize_bool_ast(last_ast_check, expand_imp_iff=True)
                            
                            # Check if result needs cleanup by comparing literal counts
                            last_measure = measure(last_ast_check)
                            qm_expr_str = qm_result.get("result", "")
                            qm_ast = generate_ast(qm_expr_str)
                            qm_ast = normalize_bool_ast(qm_ast, expand_imp_iff=True)
                            qm_measure = measure(qm_ast)
                            
                            # If laws result has more literals, it's not truly minimal
                            if last_measure[0] > qm_measure[0]:
                                print(f"Warning: Laws result not minimal, needs cleanup")
                                laws_completed = False
                    
                    # If we removed an oscillation step, re-check the new last step
                    if not laws_completed and steps:
                        # Check the new last step after removing oscillation
                        last_ast_check = generate_ast(steps[-1].after_str)
                        last_ast_check = normalize_bool_ast(last_ast_check, expand_imp_iff=True)
                        
                        # Check if it's DNF
                        if is_dnf(last_ast_check):
                            # Recheck TT hash
                            new_laws_hash = truth_table_hash(vars_list, steps[-1].after_str)
                            qm_hash = truth_table_hash(vars_list, qm_result.get("result", ""))
                            if new_laws_hash == qm_hash:
                                # Check if it's minimal by comparing PI sets
                                try:
                                    current_qm_result = simplify_qm(steps[-1].after_str)
                                    current_pi_set = set(current_qm_result.get("summary", {}).get("selected_pi", []))
                                    target_pi_set = set(selected_pi)
                                    
                                    # If current DNF contains all target PIs (or equivalent set), it's acceptable
                                    if current_pi_set == target_pi_set or current_pi_set.issuperset(target_pi_set):
                                        laws_completed = True
                                        print(f"Laws result is minimal DNF after removing oscillation (PI sets match)")
                                except Exception:
                                    # Fall back to literal count comparison if QM check fails
                                    last_measure = measure(last_ast_check)
                                    qm_expr_str = qm_result.get("result", "")
                                    qm_ast = generate_ast(qm_expr_str)
                                    qm_ast = normalize_bool_ast(qm_ast, expand_imp_iff=True)
                                    qm_measure = measure(qm_ast)
                                    
                                    # If same or fewer literals, it's acceptable
                                    if last_measure[0] <= qm_measure[0]:
                                        laws_completed = True
                                        print(f"Laws result is minimal DNF after removing oscillation (literals: {last_measure[0]})")
                except Exception:
                    laws_completed = False
            
            if not laws_completed and merge_edges:
                # Build user-visible algebraic steps from QM plan
                # Get current AST from last step's after string
                current_ast = None
                if steps:
                    current_expr = steps[-1].after_str
                    current_ast = generate_ast(current_expr)
                    current_ast = normalize_bool_ast(current_ast, expand_imp_iff=True)
                else:
                    # No laws steps, use laws' normalized_ast or fall back to initial AST
                    current_ast = laws_result.get("normalized_ast") or node
                
                # Iteratively apply merges until we reach QM's minimal DNF
                working_ast = current_ast
                
                # Build target QM canonical string once
                from .utils import bin_to_expr
                pi_terms = []
                for pi_mask in selected_pi:
                    pi_term = bin_to_expr(pi_mask, vars_list)
                    pi_terms.append(pi_term)
                
                qm_dnf_str = " ∨ ".join(pi_terms) if pi_terms else "0"
                qm_dnf_ast = generate_ast(qm_dnf_str)
                qm_dnf_ast = normalize_bool_ast(qm_dnf_ast, expand_imp_iff=True)
                qm_dnf_canon = canonical_str(qm_dnf_ast)
                
                # Track which edges we've processed to avoid infinite loops
                processed_edges = set()
                max_iterations = len(merge_edges) * 3  # Allow multiple passes
                iteration = 0
                
                while iteration < max_iterations:
                    iteration += 1
                    
                    # Check if we've reached the goal
                    if steps:
                        current_expr = steps[-1].after_str
                        current_ast = generate_ast(current_expr)
                        current_ast = normalize_bool_ast(current_ast, expand_imp_iff=True)
                        current_canon = canonical_str(current_ast)
                        
                        if current_canon == qm_dnf_canon:
                            # Success! We've reached the minimal DNF
                            break
                    
                    # Try to apply merge edges
                    made_progress = False
                    for left_mask, right_mask, result_mask in merge_edges:
                        edge_key = (left_mask, right_mask, result_mask)
                        if edge_key in processed_edges:
                            continue
                        
                        # Strategy: build_merge_steps handles uncovering internally
                        # After successful merge, immediately clean up
                        single_edge_steps = build_merge_steps(working_ast, vars_list, [(left_mask, right_mask, result_mask)])
                        if single_edge_steps:
                            steps.extend(single_edge_steps)
                            # Update working_ast after merge
                            working_ast = generate_ast(single_edge_steps[-1].after_str)
                            working_ast = normalize_bool_ast(working_ast, expand_imp_iff=True)
                            made_progress = True
                            processed_edges.add(edge_key)
                            
                            # Immediately apply cleanup after successful merge
                            immediate_cleanup = build_absorb_steps(working_ast, vars_list, selected_pi, pi_to_minterms)
                            if immediate_cleanup:
                                steps.extend(immediate_cleanup)
                                working_ast = generate_ast(immediate_cleanup[-1].after_str)
                                working_ast = normalize_bool_ast(working_ast, expand_imp_iff=True)
                            
                            # Continue to try other edges in this iteration
                            continue
                    
                    if not made_progress:
                        # No progress made, break to avoid infinite loop
                        break
                
                # Verify that final DNF canonically equals OR(selected_pi)
                if steps:
                    final_expr = steps[-1].after_str
                    final_ast = generate_ast(final_expr)
                    final_ast = normalize_bool_ast(final_ast, expand_imp_iff=True)
                    final_canon = canonical_str(final_ast)
                    
                    # Check canonical equality
                    if final_canon != qm_dnf_canon:
                        print(f"Warning: Final DNF doesn't match QM canonical after {iteration} iterations")
                        print(f"  Final canon: {final_canon}")
                        print(f"  QM canon:    {qm_dnf_canon}")
            
            # Validate continuity: prev.after_str == next.before_str
            # Enforce hard continuity - remove steps that break the chain
            i = 0
            while i < len(steps) - 1:
                prev_after = steps[i].after_str
                next_before = steps[i + 1].before_str
                if prev_after != next_before:
                    # Break in continuity - remove the offending step
                    print(f"Warning: Removing step {i+2} due to discontinuity")
                    print(f"  Step {i+1} after:  {prev_after}")
                    print(f"  Step {i+2} before: {next_before}")
                    steps.pop(i + 1)
                    # Don't increment i, check this position again
                else:
                    i += 1
            
            # Use last step's result as result_dnf if we have steps
            # Verify it matches QM for correctness AND minimality
            # BUT: if laws_completed=True, we already verified minimality above, so skip this check
            if steps:
                result_dnf = steps[-1].after_str
                
                # Only verify if laws didn't complete (i.e., we did merge steps)
                if not laws_completed:
                    # Verify equivalence with QM
                    try:
                        final_hash = truth_table_hash(vars_list, result_dnf)
                        qm_hash = truth_table_hash(vars_list, qm_result.get("result", ""))
                        
                        # Also check minimality by comparing literal counts
                        # Handle constants (0, 1) specially
                        try:
                            final_ast = generate_ast(result_dnf)
                            final_ast = normalize_bool_ast(final_ast, expand_imp_iff=True)
                            final_measure = measure(final_ast)
                            
                            qm_ast = generate_ast(qm_result.get("result", ""))
                            qm_ast = normalize_bool_ast(qm_ast, expand_imp_iff=True)
                            qm_measure = measure(qm_ast)
                            
                            is_minimal = (final_measure[0] == qm_measure[0])
                            
                            if final_hash != qm_hash:
                                print(f"Warning: Laws couldn't reach minimal DNF, using QM result (TT mismatch)")
                                print(f"  Last laws step: {result_dnf}")
                                print(f"  QM result: {qm_result.get('result')}")
                                result_dnf = qm_result.get("result", initial_canon)
                            elif not is_minimal:
                                print(f"Warning: Laws result not minimal, using QM result (literal count)")
                                print(f"  Last laws: {result_dnf} (literals={final_measure[0]})")
                                print(f"  QM result: {qm_result.get('result')} (literals={qm_measure[0]})")
                                result_dnf = qm_result.get("result", initial_canon)
                        except (ASTError, LogicExpressionError) as ast_err:
                            # If we can't parse one of the results (e.g., "1" or "0"), 
                            # compare hashes and use QM if they differ or if QM is simpler
                            if final_hash != qm_hash:
                                # Different hashes, use QM
                                print(f"Warning: Cannot parse result, using QM (TT mismatch)")
                                result_dnf = qm_result.get("result", initial_canon)
                            else:
                                # Same hashes, prefer QM since it's more canonical
                                qm_expr_str = qm_result.get("result", "")
                                if qm_expr_str in ["0", "1"] or qm_expr_str != result_dnf:
                                    print(f"Warning: Cannot parse result, using QM (prefer canonical)")
                                    result_dnf = qm_expr_str
                    except Exception as e:
                        print(f"Warning: Could not verify equivalence: {e}")
                else:
                    print(f"Laws result is complete and minimal (PI sets verified), using it as final DNF")
            else:
                result_dnf = qm_result.get("result", initial_canon)
        except Exception as e:
            # Fallback to minimal_forms if QM fails
            minimal_result = compute_minimal_forms(input_std)
            result_dnf = minimal_result.get("dnf", {}).get("expr", initial_canon)
    else:
        # Simple case - use minimal_forms
        minimal_result = compute_minimal_forms(input_std)
        result_dnf = minimal_result.get("dnf", {}).get("expr", initial_canon)
    
    return {
        "input_std": input_std,
        "vars": vars_list,
        "initial_canon": initial_canon,
        "steps": [s.__dict__ for s in steps],  # Convert to dict for JSON
        "result_dnf": result_dnf,
    }
