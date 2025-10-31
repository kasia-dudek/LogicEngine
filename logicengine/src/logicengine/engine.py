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
from .laws import simplify_with_laws
from .ast import collect_variables, canonical_str, normalize_bool_ast, generate_ast
from .utils import truth_table_hash, equivalent
from .steps import Step, RuleName, StepCategory
from .derivation_builder import build_minterm_expansion_steps, build_merge_steps, build_absorb_steps
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
                    print(f"Warning: Equivalence check failed for rule: {law_step.get('law', 'Unknown')}")
                    continue
            except Exception as e:
                # If hash computation fails, skip this step
                print(f"Warning: Could not verify step: {e}")
                continue
            
            step = Step(
                before_str=before_str,
                after_str=after_str,
                rule=law_step.get("law", "Formatowanie") if isinstance(law_step.get("law"), str) else "Formatowanie",
                location=law_step.get("path"),
                details={},
                proof={
                    "method": "tt-hash",
                    "equal": is_equal,
                    "hash_before": hash_before,
                    "hash_after": hash_after
                }
            )
            steps.append(step)
    
    # Step 4: Get minimal DNF using QM as planner, then build user-visible steps
    # For expressions with multiple variables, use QM to plan, then derive steps
    if len(vars_list) >= 1:
        try:
            qm_result = simplify_qm(input_std)
            summary = qm_result.get("summary", {})
            
            # Extract QM plan data
            minterms_1 = summary.get("minterms_1", [])
            selected_pi = summary.get("selected_pi", [])
            merge_edges = summary.get("merge_edges", [])
            pi_to_minterms = summary.get("pi_to_minterms", {})
            
            # Build user-visible algebraic steps from QM plan
            # For now, just build merge steps (minterm expansion is complex)
            merge_steps = build_merge_steps(vars_list, merge_edges)
            steps.extend(merge_steps)
            
            # Validate continuity: prev.after_str == next.before_str
            for i in range(len(steps) - 1):
                prev_after = steps[i].after_str
                next_before = steps[i + 1].before_str
                if prev_after != next_before:
                    print(f"Warning: Step discontinuity between steps {i+1} and {i+2}")
                    print(f"  Step {i+1} after:  {prev_after}")
                    print(f"  Step {i+2} before: {next_before}")
            
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
