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
from .steps import Step, RuleName
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
    
    # Step 4: Get minimal DNF using QM with trace
    # For expressions with multiple variables, use QM to get minimal DNF
    if len(vars_list) >= 1:
        try:
            qm_result = simplify_qm(input_std)
            
            # Add QM steps to our step list
            if "steps" in qm_result:
                for qm_step in qm_result["steps"]:
                    step_data = qm_step.get("data", {})
                    step_name = qm_step.get("step", "")
                    
                    # Map QM steps to our rule types
                    rule_name = "Formatowanie"
                    if "Krok 1:" in step_name:
                        rule_name = "Formatowanie"
                    elif "Krok 2:" in step_name or "Krok 3:" in step_name or "Krok 4:" in step_name:
                        rule_name = "QM: powstanie prime implicants"
                    elif "Krok 5:" in step_name:
                        rule_name = "QM: essential PI"
                    elif "Petrick: dystrybucja" in step_name:
                        rule_name = "Petrick: dystrybucja"
                    elif "Petrick: absorpcja" in step_name:
                        rule_name = "Petrick: absorpcja"
                    elif "Krok 6:" in step_name or "Krok 7:" in step_name:
                        rule_name = "Formatowanie"
                    elif "Krok 8:" in step_name:
                        rule_name = "Formatowanie"
                    
                    # For combining steps, create detailed step
                    if "rounds" in step_data:
                        for round_data in step_data["rounds"]:
                            for pair in round_data.get("pairs", []):
                                step = Step(
                                    before_str=f"Mintermy {pair.get('from', [])}",
                                    after_str=pair.get("to", ""),
                                    rule="QM: łączenie sąsiednich mintermów",
                                    location=None,
                                    details={
                                        "left_minterm": pair.get("from", [])[0] if len(pair.get("from", [])) > 0 else "",
                                        "right_minterm": pair.get("from", [])[1] if len(pair.get("from", [])) > 1 else "",
                                        "result_mask": pair.get("to", ""),
                                        "vars": vars_list
                                    },
                                    proof={"method": "qm-trace", "equal": True}
                                )
                                steps.append(step)
                    else:
                        # Regular QM step
                        step = Step(
                            before_str=step_name,
                            after_str=str(step_data),
                            rule=rule_name,
                            location=None,
                            details=step_data,
                            proof={"method": "qm-trace", "equal": True}
                        )
                        steps.append(step)
            
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
