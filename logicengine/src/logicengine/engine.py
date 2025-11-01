﻿# engine.py
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
from .laws import simplify_with_laws
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
                            from logicengine.laws import measure
                            last_measure = measure(last_ast_check)
                            qm_expr_str = qm_result.get("result", "")
                            qm_ast = generate_ast(qm_expr_str)
                            qm_ast = normalize_bool_ast(qm_ast, expand_imp_iff=True)
                            qm_measure = measure(qm_ast)
                            
                            # If laws result has more literals, it's not truly minimal
                            if last_measure[0] > qm_measure[0]:
                                print(f"Warning: Laws result not minimal, needs cleanup")
                                laws_completed = False
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
                
                # For each merge edge, ensure pair is present, then merge
                working_ast = current_ast
                for left_mask, right_mask, result_mask in merge_edges:
                    # Try to ensure pair is present
                    working_ast, pair_steps = ensure_pair_present(working_ast, vars_list, left_mask, right_mask)
                    if pair_steps:
                        steps.extend(pair_steps)
                    
                    # Now try to merge this pair
                    single_edge_steps = build_merge_steps(working_ast, vars_list, [(left_mask, right_mask, result_mask)])
                    if single_edge_steps:
                        steps.extend(single_edge_steps)
                        # Update working_ast for next iteration
                        working_ast = generate_ast(single_edge_steps[-1].after_str)
                        working_ast = normalize_bool_ast(working_ast, expand_imp_iff=True)
                
                # After all merges, apply absorption cleanup
                absorb_steps = build_absorb_steps(working_ast, vars_list, selected_pi, pi_to_minterms)
                if absorb_steps:
                    steps.extend(absorb_steps)
            
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
            # Verify it matches QM for correctness
            if steps:
                result_dnf = steps[-1].after_str
                # Verify equivalence with QM
                try:
                    final_hash = truth_table_hash(vars_list, result_dnf)
                    qm_hash = truth_table_hash(vars_list, qm_result.get("result", ""))
                    if final_hash != qm_hash:
                        print(f"Warning: Laws couldn't reach minimal DNF, using QM result")
                        print(f"  Last laws step: {result_dnf}")
                        print(f"  QM result: {qm_result.get('result')}")
                        # Use QM result as it's the verified minimal DNF
                        result_dnf = qm_result.get("result", initial_canon)
                except Exception as e:
                    print(f"Warning: Could not verify equivalence: {e}")
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
