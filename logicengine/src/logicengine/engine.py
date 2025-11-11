# engine.py
"""Main logic engine integrating analysis steps."""

from typing import Any, Dict, List, Optional, Tuple
import copy

from .parser import validate_and_standardize, LogicExpressionError
from .truth_table import generate_truth_table, TruthTableError
from .ast import generate_ast, ASTError
from .onp import to_onp, ONPError
from .kmap import simplify_kmap, KMapError
from .qm import simplify_qm, QMError
from .tautology import is_tautology
from .contradiction import is_contradiction
from .laws import (
    simplify_with_laws,
    measure,
    pretty_with_tokens,
    laws_matches,
    find_subtree_span_by_path_cp,
    find_subtree_span_by_path,
    pretty,
    set_by_path,
    iter_nodes,
    NOT,
    AND,
    OR,
    CONST,
    to_lit,
)
from .ast import collect_variables, canonical_str, normalize_bool_ast, generate_ast
from .utils import truth_table_hash, equivalent, bin_to_expr
from .steps import Step, RuleName, StepCategory
from .derivation_builder import build_minterm_expansion_steps, build_merge_steps, build_absorb_steps, build_contradiction_steps, is_dnf, ensure_pair_present
from .minimal_forms import compute_minimal_forms


TRIVIAL_LAW_NAMES = {
    "Idempotentność (∨)",
    "Idempotentność (∧)",
    "Element neutralny (A∨0)",
    "Element neutralny (A∧1)",
    "Element pochłaniający (A∨1)",
    "Element pochłaniający (A∧0)",
    "Podwójna negacja",
    "Absorpcja (∨)",
    "Absorpcja (∧)",
    "Absorpcja z negacją",
    "Absorpcja z negacją (dual)",
    "Kontradykcja (A ∧ ¬A)",
    "Dopełnienie (A ∨ ¬A)",
    "De Morgan: ¬(A ∧ B) → ¬A ∨ ¬B",
    "De Morgan: ¬(A ∨ B) → ¬A ∧ ¬B",
}

COMPLEMENT_LAW_NAMES = {
    "Dopełnienie (A ∨ ¬A)",
    "Kontradykcja (A ∧ ¬A)",
    "Element neutralny (A∨0)",
    "Element neutralny (A∧1)",
}

LAW_PRIORITY_ORDER = [
    "Kontradykcja (A ∧ ¬A)",
    "Dopełnienie (A ∨ ¬A)",
    "Element pochłaniający (A∧0)",
    "Element pochłaniający (A∨1)",
    "Element neutralny (A∧1)",
    "Element neutralny (A∨0)",
    "Idempotentność (∧)",
    "Idempotentność (∨)",
    "Absorpcja (∧)",
    "Absorpcja (∨)",
    "Absorpcja z negacją",
    "Absorpcja z negacją (dual)",
    "Dystrybutywność (A∨B)∧C",
    "Dystrybutywność A∧(B∨C)",
    "De Morgan: ¬(A ∧ B) → ¬A ∨ ¬B",
    "De Morgan: ¬(A ∨ B) → ¬A ∧ ¬B",
    "Podwójna negacja",
]

LAW_TO_RULE_NAME = {
    "Idempotentność (∨)": "Idempotentność (∨)",
    "Idempotentność (∧)": "Idempotentność (∧)",
    "Element neutralny (A∨0)": "Element neutralny (A∨0)",
    "Element neutralny (A∧1)": "Element neutralny (A∧1)",
    "Element pochłaniający (A∨1)": "Element pochłaniający (A∨1)",
    "Element pochłaniający (A∧0)": "Element pochłaniający (A∧0)",
    "Podwójna negacja": "Podwójna negacja",
    "Absorpcja (∨)": "Absorpcja (∨)",
    "Absorpcja (∧)": "Absorpcja (∧)",
    "Absorpcja z negacją": "Absorpcja z negacją",
    "Absorpcja z negacją (dual)": "Absorpcja z negacją (dual)",
    "Kontradykcja (A ∧ ¬A)": "Kontradykcja (A ∧ ¬A)",
    "Dopełnienie (A ∨ ¬A)": "Dopełnienie (A ∨ ¬A)",
    "De Morgan: ¬(A ∧ B) → ¬A ∨ ¬B": "De Morgan (¬(A∧B))",
    "De Morgan: ¬(A ∨ B) → ¬A ∧ ¬B": "De Morgan (¬(A∨B))",
    "Dystrybutywność (A∨B)∧C": "Dystrybutywność (A∨B)∧C",
    "Dystrybutywność A∧(B∨C)": "Dystrybutywność A∧(B∨C)",
}


def _law_priority(law_name: str) -> int:
    try:
        return LAW_PRIORITY_ORDER.index(law_name)
    except ValueError:
        return len(LAW_PRIORITY_ORDER)


def _law_to_rule_name(law_name: str) -> RuleName:
    mapped = LAW_TO_RULE_NAME.get(law_name)
    if mapped:
        return mapped  # type: ignore[return-value]
    if law_name in LAW_TO_RULE_NAME.values():
        return law_name  # type: ignore[return-value]
    return "Formatowanie"


def _apply_law_match(
    current_ast: Any,
    match: Dict[str, Any],
    vars_list: List[str],
) -> Tuple[Optional[Step], Any]:
    def _find_non_overlapping_span(base_arr: List[str], sub_arr: List[str], used_mask: List[bool]) -> Optional[Tuple[int, int]]:
        if not sub_arr:
            return None
        max_start = len(base_arr) - len(sub_arr)
        for i in range(max_start + 1):
            if any(used_mask[i + j] for j in range(len(sub_arr))):
                continue
            if base_arr[i:i + len(sub_arr)] == sub_arr:
                for j in range(len(sub_arr)):
                    used_mask[i + j] = True
                return (i, i + len(sub_arr))
        return None

    law_name = match.get("law")
    path = match.get("path")
    before_sub = match.get("before")
    after_sub = match.get("after")
    
    if not law_name or before_sub is None or after_sub is None:
        return (None, current_ast)
    
    rule_name = _law_to_rule_name(law_name)
    
    # Prepare BEFORE state
    before_ast = copy.deepcopy(current_ast)
    before_str, _ = pretty_with_tokens(before_ast)
    before_canon = canonical_str(before_ast)
    before_subexpr_str = pretty(before_sub)
    before_subexpr_canon = canonical_str(before_sub)
    
    before_highlight_span = find_subtree_span_by_path_cp(path, before_ast) if path else None
    before_highlight_spans_cp = None
    if before_highlight_span:
        before_highlight_spans_cp = [(before_highlight_span["start"], before_highlight_span["end"])]
    
    # Apply transformation
    updated_ast = set_by_path(current_ast, path, after_sub) if path else after_sub
    updated_ast = normalize_bool_ast(updated_ast, expand_imp_iff=True)
    after_str, _ = pretty_with_tokens(updated_ast)
    after_canon = canonical_str(updated_ast)
    after_subexpr_str = pretty(after_sub)
    after_subexpr_canon = canonical_str(after_sub)
    
    # Locate transformed subexpression in AFTER state
    after_highlight_spans_cp = None
    sub_after_norm = normalize_bool_ast(after_sub, expand_imp_iff=True)
    target_canon = canonical_str(sub_after_norm)
    for after_path, after_node in iter_nodes(updated_ast):
        if canonical_str(after_node) == target_canon:
            span = find_subtree_span_by_path_cp(after_path, updated_ast)
            if span:
                after_highlight_spans_cp = [(span["start"], span["end"])]
            break
    if after_highlight_spans_cp is None and path:
        span = find_subtree_span_by_path_cp(path, updated_ast)
        if span:
            after_highlight_spans_cp = [(span["start"], span["end"])]
    
    if after_highlight_spans_cp:
        spans_len = sum(max(0, end - start) for start, end in after_highlight_spans_cp)
        if spans_len < len(after_subexpr_str):
            after_highlight_spans_cp = None

    if rule_name == "Dystrybutywność A∧(B∨C)":
        distributed_terms = []
        if isinstance(after_sub, dict) and after_sub.get("op") == "OR":
            for term in after_sub.get("args", []):
                term_norm = normalize_bool_ast(term, expand_imp_iff=True)
                term_pretty, _ = pretty_with_tokens(term_norm)
                distributed_terms.append(term_pretty)
        if distributed_terms:
            base_arr = list(after_str)
            used_mask = [False] * len(base_arr)
            spans = []
            for term_str in distributed_terms:
                span_tuple = _find_non_overlapping_span(base_arr, list(term_str), used_mask)
                if span_tuple:
                    spans.append(span_tuple)
            if spans:
                after_highlight_spans_cp = spans

    if after_highlight_spans_cp is None and after_subexpr_str:
        base_arr = list(after_str)
        used_mask = [False] * len(base_arr)
        span_tuple = _find_non_overlapping_span(base_arr, list(after_subexpr_str), used_mask)
        if span_tuple:
            after_highlight_spans_cp = [span_tuple]
    elif (
        after_highlight_spans_cp
        and after_subexpr_str
        and rule_name != "Dystrybutywność A∧(B∨C)"
    ):
        extracted = "".join(after_str[start:end] for start, end in after_highlight_spans_cp)
        if after_subexpr_str not in extracted:
            after_highlight_spans_cp = None

    hash_before = truth_table_hash(vars_list, before_str)
    hash_after = truth_table_hash(vars_list, after_str)
    
    step = Step(
        before_str=before_str,
        after_str=after_str,
        rule=rule_name,
        category="user",
        proof={
            "method": "tt-hash",
            "equal": hash_before == hash_after,
            "hash_before": hash_before,
            "hash_after": hash_after,
        },
        before_canon=before_canon,
        after_canon=after_canon,
        before_subexpr=before_subexpr_str,
        after_subexpr=after_subexpr_str,
        before_subexpr_canon=before_subexpr_canon,
        after_subexpr_canon=after_subexpr_canon,
        before_highlight_spans_cp=before_highlight_spans_cp,
        after_highlight_spans_cp=after_highlight_spans_cp,
    )
    
    return step, updated_ast


def run_fixpoint(
    ast_node: Any,
    vars_list: List[str],
    allowed_laws: Optional[set] = None,
    max_iterations: int = 64,
) -> Tuple[Any, List[Step]]:
    """
    Apply selected Boolean laws iteratively until a fixpoint is reached.
    Returns the transformed AST and list of generated steps.
    """
    if allowed_laws is None:
        allowed_laws = TRIVIAL_LAW_NAMES
    
    current_ast = normalize_bool_ast(ast_node, expand_imp_iff=True)
    steps: List[Step] = []
    seen_canon = {canonical_str(current_ast)}
    
    for _ in range(max_iterations):
        matches = [
            m for m in laws_matches(current_ast)
            if m.get("law") in allowed_laws
        ]
        if not matches:
            break
        
        matches.sort(key=lambda m: (_law_priority(m.get("law", "")), measure(m.get("after"))))
        
        applied = False
        for match in matches:
            step, updated_ast = _apply_law_match(current_ast, match, vars_list)
            if step is None:
                continue
            steps.append(step)
            current_ast = updated_ast
            canon = canonical_str(current_ast)
            if canon in seen_canon:
                applied = True
                break
            seen_canon.add(canon)
            applied = True
            break
        
        if not applied:
            break
    
    return current_ast, steps


def _ast_from_steps(current_ast: Any, new_steps: List[Step]) -> Any:
    if not new_steps:
        return current_ast
    last = new_steps[-1]
    after_str = last.after_str
    if not after_str:
        return current_ast
    try:
        return normalize_bool_ast(generate_ast(after_str), expand_imp_iff=True)
    except Exception:
        return current_ast


def push_negations_to_literals(
    ast_node: Any,
    vars_list: List[str],
) -> Tuple[Any, List[Step]]:
    """Apply De Morgan and double-negation until negations touch only literals."""
    current_ast = normalize_bool_ast(ast_node, expand_imp_iff=True)
    steps: List[Step] = []
    seen_canon = {canonical_str(current_ast)}

    while True:
        applied = False
        for path, sub in iter_nodes(current_ast):
            if not isinstance(sub, dict):
                continue
            if sub.get("op") != "NOT":
                continue
            
            child = sub.get("child")
            match: Optional[Dict[str, Any]] = None
            
            if isinstance(child, dict) and child.get("op") == "NOT":
                match = {
                    "law": "Podwójna negacja",
                    "path": path,
                    "before": copy.deepcopy(sub),
                    "after": copy.deepcopy(child.get("child")),
                }
            elif isinstance(child, dict) and child.get("op") in {"AND", "OR"}:
                inner_args = child.get("args", [])
                if child.get("op") == "AND":
                    after_args = [NOT(copy.deepcopy(arg)) for arg in inner_args]
                    after = OR(after_args)
                    law_name = "De Morgan: ¬(A ∧ B) → ¬A ∨ ¬B"
                else:
                    after_args = [NOT(copy.deepcopy(arg)) for arg in inner_args]
                    after = AND(after_args)
                    law_name = "De Morgan: ¬(A ∨ B) → ¬A ∧ ¬B"
                match = {
                    "law": law_name,
                    "path": path,
                    "before": copy.deepcopy(sub),
                    "after": after,
                }
            
            if not match:
                continue
            
            step, current_ast = _apply_law_match(current_ast, match, vars_list)
            if step:
                steps.append(step)
                applied = True
            break
        if not applied:
            break
    
    return current_ast, steps


def apply_complement_laws(
    ast_node: Any,
    vars_list: List[str],
) -> Tuple[Any, List[Step]]:
    """
    Reduce subexpressions of the form A∨¬A and A∧¬A (plus resulting neutral elements)
    before heavier transformations such as distribution.
    """
    current_ast = normalize_bool_ast(ast_node, expand_imp_iff=True)
    steps: List[Step] = []
    seen_canon = {canonical_str(current_ast)}

    while True:
        applied = False
        for path, sub in iter_nodes(current_ast):
            if not isinstance(sub, dict):
                continue
            op = sub.get("op")
            if op not in {"OR", "AND"}:
                continue

            args = sub.get("args", [])
            if len(args) < 2:
                continue

            lits = [to_lit(arg) for arg in args]
            if None in lits:
                continue
            lit_set = set(lits)

            if op == "OR" and any((name, not polarity) in lit_set for name, polarity in lits):
                match = {
                    "law": "Dopełnienie (A ∨ ¬A)",
                    "path": path,
                    "before": copy.deepcopy(sub),
                    "after": CONST(1),
                }
            elif op == "AND" and any((name, not polarity) in lit_set for name, polarity in lits):
                match = {
                    "law": "Kontradykcja (A ∧ ¬A)",
                    "path": path,
                    "before": copy.deepcopy(sub),
                    "after": CONST(0),
                }
            else:
                continue

            step, current_ast = _apply_law_match(current_ast, match, vars_list)
            if step:
                steps.append(step)
                canon = canonical_str(current_ast)
                if canon in seen_canon:
                    return current_ast, steps
                seen_canon.add(canon)
                applied = True
            break

        if not applied:
            break

    return current_ast, steps


def distribute_to_dnf(
    ast_node: Any,
    vars_list: List[str],
) -> Tuple[Any, List[Step]]:
    """Distribute conjunction over disjunction to reach DNF using Boolean laws."""
    current_ast = normalize_bool_ast(ast_node, expand_imp_iff=True)
    steps: List[Step] = []
    seen_canon = {canonical_str(current_ast)}

    while True:
        applied = False
        for path, sub in iter_nodes(current_ast):
            if not isinstance(sub, dict):
                continue
            if sub.get("op") != "AND":
                continue

            args = sub.get("args", [])
            target_idx = None
            for idx, arg in enumerate(args):
                if isinstance(arg, dict) and arg.get("op") == "OR" and len(arg.get("args", [])) >= 2:
                    target_idx = idx
                    break
            if target_idx is None:
                continue

            or_node = args[target_idx]
            other_args = [copy.deepcopy(a) for i, a in enumerate(args) if i != target_idx]
            distributed_terms = []
            for or_arg in or_node.get("args", []):
                term_args = [copy.deepcopy(or_arg)] + [copy.deepcopy(a) for a in other_args]
                if len(term_args) == 1:
                    distributed_terms.append(term_args[0])
                else:
                    distributed_terms.append({"op": "AND", "args": term_args})

            match = {
                "law": "Dystrybutywność A∧(B∨C)",
                "path": path,
                "before": copy.deepcopy(sub),
                "after": {"op": "OR", "args": distributed_terms},
            }
            step, current_ast = _apply_law_match(current_ast, match, vars_list)
            if step:
                steps.append(step)
                canon = canonical_str(current_ast)
                if canon in seen_canon:
                    return current_ast, steps
                seen_canon.add(canon)
                applied = True
            break
        if not applied:
            break
    
    return current_ast, steps


def _simplify_with_dnf_pipeline(expr: str, var_limit: int) -> Dict[str, Any]:
    input_std = validate_and_standardize(expr)
    legacy_ast = generate_ast(input_std)
    current_ast = normalize_bool_ast(legacy_ast, expand_imp_iff=True)
    
    vars_list = collect_variables(current_ast)
    if len(vars_list) > var_limit:
        raise TooManyVariables(f"Expression has {len(vars_list)} variables, maximum is {var_limit}")
    
    initial_canon = canonical_str(current_ast)
    step_objects: List[Step] = []
    
    legacy_pretty, _ = pretty_with_tokens(legacy_ast)
    normalized_pretty, _ = pretty_with_tokens(current_ast)
    if legacy_pretty != normalized_pretty and ("→" in legacy_pretty or "↔" in legacy_pretty or "⊕" in legacy_pretty or "↑" in legacy_pretty or "↓" in legacy_pretty):
        elim_step = Step(
            before_str=legacy_pretty,
            after_str=normalized_pretty,
            rule="Eliminacja złożonych operatorów",
            category="user",
            proof={"method": "rewrite"},
            before_canon=canonical_str(legacy_ast),
            after_canon=initial_canon,
            before_subexpr=legacy_pretty,
            after_subexpr=normalized_pretty,
            before_subexpr_canon=canonical_str(legacy_ast),
            after_subexpr_canon=initial_canon,
        )
        step_objects.append(elim_step)
    
    current_ast, fix_steps = run_fixpoint(current_ast, vars_list, TRIVIAL_LAW_NAMES)
    step_objects.extend(fix_steps)
    
    current_ast, nnf_steps = push_negations_to_literals(current_ast, vars_list)
    step_objects.extend(nnf_steps)
    
    current_ast, complement_steps_1 = apply_complement_laws(current_ast, vars_list)
    step_objects.extend(complement_steps_1)
    
    current_ast, post_complement_fix = run_fixpoint(current_ast, vars_list, TRIVIAL_LAW_NAMES)
    step_objects.extend(post_complement_fix)
    
    current_ast, complement_steps_2 = apply_complement_laws(current_ast, vars_list)
    step_objects.extend(complement_steps_2)
    
    current_ast, distribution_steps = distribute_to_dnf(current_ast, vars_list)
    step_objects.extend(distribution_steps)
    
    current_ast, complement_steps_3 = apply_complement_laws(current_ast, vars_list)
    step_objects.extend(complement_steps_3)
    
    current_ast, final_cleanup_steps = run_fixpoint(current_ast, vars_list, TRIVIAL_LAW_NAMES)
    step_objects.extend(final_cleanup_steps)
    
    current_ast = normalize_bool_ast(current_ast, expand_imp_iff=True)
    if not is_dnf(current_ast):
        raise RuntimeError("DNF conversion did not finish")
    
    dnf_str, _ = pretty_with_tokens(current_ast)
    dnf_canon = canonical_str(current_ast)
    
    pre_steps_dicts: List[Dict[str, Any]] = [copy.deepcopy(step.__dict__) for step in step_objects]
    
    result_vars = collect_variables(current_ast)
    if len(result_vars) == 0:
        return {
            "input_std": input_std,
            "vars": vars_list,
            "initial_canon": initial_canon,
            "steps": pre_steps_dicts,
            "result_dnf": dnf_str,
            "is_already_minimal": len(step_objects) == 0,
        }
    
    legacy_result = _legacy_simplify_to_minimal_dnf(dnf_str, var_limit)
    legacy_steps = copy.deepcopy(legacy_result.get("steps", []))
    combined_steps = pre_steps_dicts + legacy_steps
    
    if legacy_steps:
        expected_before = pre_steps_dicts[-1]["after_str"] if pre_steps_dicts else dnf_str
        if legacy_steps[0].get("before_str") != expected_before:
            legacy_steps[0]["before_str"] = expected_before
            legacy_steps[0]["before_canon"] = dnf_canon
        combined_steps = pre_steps_dicts + legacy_steps
    
    result_dnf = legacy_result.get("result_dnf", dnf_str)
    final_ast = normalize_bool_ast(generate_ast(result_dnf), expand_imp_iff=True)
    final_canon = canonical_str(final_ast)
    final_measure = measure(final_ast)
    
    try:
        qm_result = simplify_qm(input_std)
        qm_summary = qm_result.get("summary", {})
        qm_expr = qm_result.get("result", result_dnf)
        qm_ast = normalize_bool_ast(generate_ast(qm_expr), expand_imp_iff=True)
        qm_canon = canonical_str(qm_ast)
        qm_measure_vals = measure(qm_ast)
    except Exception:
        qm_summary = {}
        qm_expr = result_dnf
        qm_canon = final_canon
        qm_measure_vals = final_measure
    
    original_ast = normalize_bool_ast(legacy_ast, expand_imp_iff=True)
    is_already_minimal = canonical_str(original_ast) == final_canon and not step_objects
    
    return {
        "input_std": input_std,
        "vars": vars_list,
        "initial_canon": initial_canon,
        "steps": combined_steps,
        "result_dnf": result_dnf,
        "is_already_minimal": is_already_minimal,
    }


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


def _legacy_simplify_to_minimal_dnf(expr: str, var_limit: int = 8) -> Dict[str, Any]:
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
    
    # Get QM result early to compare with laws result
    qm_result = None
    qm_dnf_str = None
    qm_measure = None
    qm_dnf_canon = None
    if len(vars_list) >= 1:
        try:
            qm_result = simplify_qm(input_std)
            from .utils import bin_to_expr
            summary = qm_result.get("summary", {})
            selected_pi = summary.get("selected_pi", [])
            pi_terms = []
            for pi_mask in selected_pi:
                pi_term = bin_to_expr(pi_mask, vars_list)
                pi_terms.append(pi_term)
            qm_dnf_str = " ∨ ".join(pi_terms) if pi_terms else "0"
            qm_ast = generate_ast(qm_dnf_str)
            qm_ast = normalize_bool_ast(qm_ast, expand_imp_iff=True)
            qm_measure = measure(qm_ast)
            qm_dnf_canon = canonical_str(qm_ast)
        except Exception:
            pass
    
    # Convert laws result steps to our Step model with verification
    # Only include laws steps if they lead to a result that's at least as minimal as QM
    laws_steps_to_include = []
    essential_law_names = {
        "De Morgan: ¬(A ∧ B) → ¬A ∨ ¬B",
        "De Morgan: ¬(A ∨ B) → ¬A ∧ ¬B",
    }
    laws_result_final = laws_result.get("result", "")
    
    # Check if laws result is worse than QM - if so, skip only non-essential laws steps
    skip_nonessential_law_steps = False
    if qm_measure and laws_result_final and laws_result_final not in ["?", ""]:
        try:
            laws_final_ast = generate_ast(laws_result_final)
            laws_final_ast = normalize_bool_ast(laws_final_ast, expand_imp_iff=True)
            laws_final_measure = measure(laws_final_ast)
            # If laws result has significantly more literals than QM, skip non-essential laws steps
            if laws_final_measure[0] > qm_measure[0] * 1.2:  # 20% tolerance
                print(
                    f"Skipping non-essential laws steps: laws result has {laws_final_measure[0]} literals, "
                    f"QM has {qm_measure[0]}"
                )
                skip_nonessential_law_steps = True
        except Exception:
            pass
    
    if "steps" in laws_result:
        # Check if final result is good - if so, include all steps regardless of intermediate measures
        final_result_is_good = False
        if qm_measure and laws_result_final and laws_result_final not in ["?", ""]:
            try:
                laws_final_ast = generate_ast(laws_result_final)
                laws_final_ast = normalize_bool_ast(laws_final_ast, expand_imp_iff=True)
                laws_final_measure = measure(laws_final_ast)
                # Final result is good if it's not worse than QM
                final_result_is_good = (laws_final_measure[0] <= qm_measure[0] * 1.2)
            except Exception:
                pass
        
        for law_step in laws_result["steps"]:
            before_str = law_step.get("before_tree", "")
            after_str = law_step.get("after_tree", "")
            law_name = law_step.get("law", "")
            is_essential_law = law_name in essential_law_names
            
            # Skip oscillation steps
            if law_name == "Zatrzymano (oscylacja)":
                continue
            
            if skip_nonessential_law_steps and not is_essential_law:
                continue
            
            # Only check intermediate measures if final result is not good
            # If final result is good, include all steps (they may have intermediate larger measures)
            if not is_essential_law and not final_result_is_good and qm_measure and after_str:
                try:
                    after_ast = generate_ast(after_str)
                    after_ast = normalize_bool_ast(after_ast, expand_imp_iff=True)
                    after_measure = measure(after_ast)
                    # Only include step if it doesn't make result worse than QM
                    if after_measure[0] > qm_measure[0] * 1.5:  # Allow some tolerance
                        # Result is getting too large, stop including laws steps
                        break
                except Exception:
                    pass
            
            laws_steps_to_include.append(law_step)
    
    # Only add laws steps if final result is reasonable
    if laws_steps_to_include:
        for law_step in laws_steps_to_include:
            before_str = law_step.get("before_tree", "")
            after_str = law_step.get("after_tree", "")
            law_name = law_step.get("law", "")
            
            # Skip steps with invalid results
            if after_str in ["?", ""] or before_str in ["?", ""]:
                continue
            
            # Verify equivalence for each step
            try:
                from .utils import truth_table_hash
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
            
            # FIRST: Check if input expression is already minimal DNF
            # This avoids generating unnecessary steps that just transform and back
            input_ast_check = normalize_bool_ast(node, expand_imp_iff=True)
            input_is_dnf_check = is_dnf(input_ast_check)
            input_already_minimal = False
            if input_is_dnf_check:
                input_canon_check = canonical_str(input_ast_check)
                qm_result_str_check = qm_result.get("result", "")
                qm_result_ast_check = generate_ast(qm_result_str_check)
                qm_result_ast_check = normalize_bool_ast(qm_result_ast_check, expand_imp_iff=True)
                qm_result_canon_check = canonical_str(qm_result_ast_check)
                input_measure_check = measure(input_ast_check)
                qm_measure_check = measure(qm_result_ast_check)
                
                if input_canon_check == qm_result_canon_check and input_measure_check[0] == qm_measure_check[0]:
                    input_already_minimal = True
                    steps = []
            
            if not input_already_minimal:
                current_ast = None  # Initialize to None, will be set below
                if steps:
                    current_ast = generate_ast(steps[-1].after_str)
                    current_ast = normalize_bool_ast(current_ast, expand_imp_iff=True)
                else:
                    current_ast = node
                
                # Remove contradictions after simplify_with_laws steps
                # This ensures contradictions created during distribution are removed immediately
                contradiction_steps = build_contradiction_steps(current_ast, vars_list)
                if contradiction_steps:
                    steps.extend(contradiction_steps)
                    current_ast = generate_ast(contradiction_steps[-1].after_str)
                    current_ast = normalize_bool_ast(current_ast, expand_imp_iff=True)
                
                # Check if current expression is in DNF but not minimal
                # If so, apply absorption to reach minimal DNF
                current_is_dnf_after_laws = is_dnf(current_ast)
                
                # Always check if we need to continue simplification, even if not in DNF yet
                # Get QM result for comparison
                qm_result_str_check = qm_result.get("result", "") if qm_result else ""
                qm_result_ast_check = None
                qm_result_canon_check = None
                qm_measure_check = None
                if qm_result_str_check:
                    qm_result_ast_check = generate_ast(qm_result_str_check)
                    qm_result_ast_check = normalize_bool_ast(qm_result_ast_check, expand_imp_iff=True)
                    qm_result_canon_check = canonical_str(qm_result_ast_check)
                    qm_measure_check = measure(qm_result_ast_check)
                
                # Always try to continue simplification if we have steps and QM result
                # This ensures we continue even if expression is not yet in DNF
                if steps and qm_result_ast_check:
                    # Compare with QM result to check if minimal
                    current_canon_after_laws = canonical_str(current_ast)
                    current_measure_after_laws = measure(current_ast)
                    
                    # If not minimal, apply absorption iteratively until minimal DNF is reached
                    # Also continue if expression is in DNF but not minimal
                    needs_simplification = (
                        not qm_result_ast_check or 
                        current_canon_after_laws != qm_result_canon_check or 
                        current_measure_after_laws[0] > qm_measure_check[0]
                    )
                    
                    if needs_simplification:
                        # Iteratively apply absorption until we reach minimal DNF
                        max_absorb_iterations = 50  # Increased to allow more iterations
                        for absorb_iteration in range(max_absorb_iterations):
                            # Check if we've reached minimal DNF
                            current_canon_iter = canonical_str(current_ast)
                            current_measure_iter = measure(current_ast)
                            if current_canon_iter == qm_result_canon_check and current_measure_iter[0] <= qm_measure_check[0]:
                                # Reached minimal DNF
                                break
                            
                            # Track if we made any progress in this iteration
                            made_progress = False
                            
                            # Apply absorption
                            absorb_steps = build_absorb_steps(current_ast, vars_list, selected_pi, pi_to_minterms)
                            if absorb_steps:
                                steps.extend(absorb_steps)
                                current_ast = generate_ast(absorb_steps[-1].after_str)
                                current_ast = normalize_bool_ast(current_ast, expand_imp_iff=True)
                                made_progress = True
                                
                                # Remove contradictions that may have been created
                                contradiction_steps = build_contradiction_steps(current_ast, vars_list)
                                if contradiction_steps:
                                    steps.extend(contradiction_steps)
                                    current_ast = generate_ast(contradiction_steps[-1].after_str)
                                    current_ast = normalize_bool_ast(current_ast, expand_imp_iff=True)
                                
                                # After absorption, try to apply more laws to simplify complex terms
                                # This helps with cases like ¬(B∧¬C) that can be expanded
                                from .laws import pretty
                                current_expr_str = pretty(current_ast)
                                additional_laws = simplify_with_laws(current_expr_str, max_steps=20, mode="mixed")
                                if additional_laws.get("steps") and len(additional_laws["steps"]) > 0:
                                    # Only add steps that actually simplify (reduce literal count)
                                    current_measure = measure(current_ast)
                                    for law_step in additional_laws["steps"]:
                                        after_str = law_step.get("after_tree", "")
                                        if after_str and after_str not in ["?", ""]:
                                            try:
                                                after_ast = generate_ast(after_str)
                                                after_ast = normalize_bool_ast(after_ast, expand_imp_iff=True)
                                                after_measure = measure(after_ast)
                                                # Only include if it reduces literal count or keeps same but changes structure
                                                if after_measure[0] <= current_measure[0]:
                                                    from .utils import truth_table_hash
                                                    hash_before = truth_table_hash(vars_list, current_expr_str)
                                                    hash_after = truth_table_hash(vars_list, after_str)
                                                    if hash_before == hash_after and len(hash_before) > 0:
                                                        before_str, _ = pretty_with_tokens(current_ast)
                                                        after_str, _ = pretty_with_tokens(after_ast)
                                                        step = Step(
                                                            before_str=before_str,
                                                            after_str=after_str,
                                                            rule=law_step.get("law", "Prawa logiczne"),
                                                            location=law_step.get("path"),
                                                            details={},
                                                            proof={"method": "tt-hash", "equal": True},
                                                            before_subexpr=law_step.get("before_subexpr"),
                                                            after_subexpr=law_step.get("after_subexpr"),
                                                            before_canon=canonical_str(current_ast),
                                                            after_canon=canonical_str(after_ast),
                                                            before_subexpr_canon=law_step.get("before_subexpr_canon"),
                                                            after_subexpr_canon=law_step.get("after_subexpr_canon"),
                                                            before_highlight_span=law_step.get("before_highlight_span"),
                                                            after_highlight_span=law_step.get("after_highlight_span")
                                                        )
                                                        steps.append(step)
                                                        current_ast = after_ast
                                                        current_expr_str = after_str
                                                        current_measure = after_measure
                                                        made_progress = True
                                                        # Check if we've reached minimal DNF
                                                        current_canon_check = canonical_str(current_ast)
                                                        if current_canon_check == qm_result_canon_check and current_measure[0] <= qm_measure_check[0]:
                                                            break
                                            except Exception:
                                                continue
                            
                            # If no progress was made, try one more time with laws only
                            if not made_progress:
                                from .laws import pretty
                                current_expr_str = pretty(current_ast)
                                # Try with more steps to allow complex transformations
                                additional_laws = simplify_with_laws(current_expr_str, max_steps=30, mode="mixed")
                                if additional_laws.get("steps") and len(additional_laws["steps"]) > 0:
                                    current_measure = measure(current_ast)
                                    for law_step in additional_laws["steps"]:
                                        after_str = law_step.get("after_tree", "")
                                        if after_str and after_str not in ["?", ""]:
                                            try:
                                                after_ast = generate_ast(after_str)
                                                after_ast = normalize_bool_ast(after_ast, expand_imp_iff=True)
                                                after_measure = measure(after_ast)
                                                # Accept if it doesn't increase literal count
                                                if after_measure[0] <= current_measure[0]:
                                                    from .utils import truth_table_hash
                                                    hash_before = truth_table_hash(vars_list, current_expr_str)
                                                    hash_after = truth_table_hash(vars_list, after_str)
                                                    if hash_before == hash_after and len(hash_before) > 0:
                                                        before_str, _ = pretty_with_tokens(current_ast)
                                                        after_str, _ = pretty_with_tokens(after_ast)
                                                        step = Step(
                                                            before_str=before_str,
                                                            after_str=after_str,
                                                            rule=law_step.get("law", "Prawa logiczne"),
                                                            location=law_step.get("path"),
                                                            details={},
                                                            proof={"method": "tt-hash", "equal": True},
                                                            before_subexpr=law_step.get("before_subexpr"),
                                                            after_subexpr=law_step.get("after_subexpr"),
                                                            before_canon=canonical_str(current_ast),
                                                            after_canon=canonical_str(after_ast),
                                                            before_subexpr_canon=law_step.get("before_subexpr_canon"),
                                                            after_subexpr_canon=law_step.get("after_subexpr_canon"),
                                                            before_highlight_span=law_step.get("before_highlight_span"),
                                                            after_highlight_span=law_step.get("after_highlight_span")
                                                        )
                                                        steps.append(step)
                                                        current_ast = after_ast
                                                        current_expr_str = after_str
                                                        current_measure = after_measure
                                                        made_progress = True
                                                        # Re-check if we've reached minimal DNF
                                                        current_canon_check = canonical_str(current_ast)
                                                        if current_canon_check == qm_result_canon_check and current_measure[0] <= qm_measure_check[0]:
                                                            break
                                            except Exception:
                                                continue
                            
                            # If still no progress after trying laws, check if we're done
                            if not made_progress:
                                # Final check: are we at minimal DNF?
                                final_canon_check = canonical_str(current_ast)
                                final_measure_check = measure(current_ast)
                                if final_canon_check == qm_result_canon_check and final_measure_check[0] <= qm_measure_check[0]:
                                    break
                                # If not minimal and no progress, don't break - continue to next iteration
                                # The problem might be that build_absorb_steps needs to be called again
                                # after laws have been applied, or we need to force absorption detection
                                # Continue to next iteration to try again
                                continue
                        
                        # After iterative absorption, update current_ast to reflect final state
                        if steps:
                            current_ast = generate_ast(steps[-1].after_str)
                            current_ast = normalize_bool_ast(current_ast, expand_imp_iff=True)
                            
                            # Verify that we actually reached minimal DNF after absorption
                            # If not, we need to continue in the next section
                            final_canon_after_absorb = canonical_str(current_ast)
                            final_measure_after_absorb = measure(current_ast)
                            if final_canon_after_absorb != qm_result_canon_check or final_measure_after_absorb[0] > qm_measure_check[0]:
                                # Not minimal yet - will continue in next section
                                # Make sure laws_completed is False so we continue
                                pass
                        else:
                            # No steps from iterative absorption - use current_ast as is
                            # This ensures current_ast is set for the next section
                            pass
            
            laws_result_str = None
            if steps:
                laws_result_str = steps[-1].after_str
            else:
                laws_result_str = laws_result.get("result", "")
            
            laws_completed = False
            
            if laws_result_str and laws_result_str not in ["?", ""]:
                try:
                    from .utils import truth_table_hash
                    laws_hash = truth_table_hash(vars_list, laws_result_str)
                    qm_hash = truth_table_hash(vars_list, qm_result.get("result", ""))
                    # First check if laws_result_str is in DNF format
                    # If not, we can't accept it as completed even if hashes match
                    laws_ast_check = generate_ast(laws_result_str)
                    laws_ast_check = normalize_bool_ast(laws_ast_check, expand_imp_iff=True)
                    laws_is_dnf = is_dnf(laws_ast_check)
                    
                    # Check if result is minimal DNF (not just equivalent)
                    # Compare canonical forms and literal counts
                    laws_canon_check = canonical_str(laws_ast_check)
                    qm_result_str_check = qm_result.get("result", "")
                    qm_result_ast_check = generate_ast(qm_result_str_check)
                    qm_result_ast_check = normalize_bool_ast(qm_result_ast_check, expand_imp_iff=True)
                    qm_result_canon_check = canonical_str(qm_result_ast_check)
                    laws_measure_check = measure(laws_ast_check)
                    qm_measure_check = measure(qm_result_ast_check)
                    
                    # Only set laws_completed if hashes match AND result is in DNF AND result is minimal
                    is_minimal = (laws_canon_check == qm_result_canon_check and laws_measure_check[0] <= qm_measure_check[0])
                    laws_completed = (laws_hash == qm_hash and len(laws_hash) > 0 and laws_is_dnf and is_minimal)
                    
                    # Additional check: if no steps but TT hashes match, verify canonical equality
                    # This catches cases where laws didn't find any simplifications but TT is equivalent
                    if laws_completed and not steps:
                        # Build QM canonical string
                        from .utils import bin_to_expr
                        pi_terms = []
                        for pi_mask in selected_pi:
                            pi_term = bin_to_expr(pi_mask, vars_list)
                            pi_terms.append(pi_term)
                        qm_dnf_str = " ∨ ".join(pi_terms) if pi_terms else "0"
                        qm_dnf_ast = generate_ast(qm_dnf_str)
                        qm_dnf_ast = normalize_bool_ast(qm_dnf_ast, expand_imp_iff=True)
                        qm_dnf_canon = canonical_str(qm_dnf_ast)
                        
                        # Compare with laws result canonical
                        laws_ast = generate_ast(laws_result_str)
                        laws_ast = normalize_bool_ast(laws_ast, expand_imp_iff=True)
                        laws_canon = canonical_str(laws_ast)
                        
                        if laws_canon != qm_dnf_canon:
                            print(f"Warning: TT hashes match but canonical forms differ, proceeding with QM merge")
                            laws_completed = False
                    
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
                                # Check literal count - this is the primary minimality criterion
                                last_measure = measure(last_ast_check)
                                qm_expr_str = qm_result.get("result", "")
                                qm_ast = generate_ast(qm_expr_str)
                                qm_ast = normalize_bool_ast(qm_ast, expand_imp_iff=True)
                                qm_measure = measure(qm_ast)
                                
                                # Only accept if same or fewer literals
                                if last_measure[0] <= qm_measure[0]:
                                    laws_completed = True
                                    print(f"Laws result is minimal DNF after removing oscillation (literals: {last_measure[0]})")
                                # Don't accept if more literals, even if PI sets match
                except Exception:
                    laws_completed = False
            
            # Even if laws_completed is True, we need to verify that the result is actually minimal
            # and continue with absorption if it's not
            # Get current AST from steps to check minimality
            if laws_completed and steps:
                # Check if the last step is actually minimal
                last_ast_check = generate_ast(steps[-1].after_str)
                last_ast_check = normalize_bool_ast(last_ast_check, expand_imp_iff=True)
                last_canon_check = canonical_str(last_ast_check)
                last_measure_check = measure(last_ast_check)
                
                qm_result_str_check = qm_result.get("result", "")
                qm_result_ast_check = generate_ast(qm_result_str_check)
                qm_result_ast_check = normalize_bool_ast(qm_result_ast_check, expand_imp_iff=True)
                qm_result_canon_check = canonical_str(qm_result_ast_check)
                qm_measure_check = measure(qm_result_ast_check)
                
                # If not minimal, continue with absorption
                if last_canon_check != qm_result_canon_check or last_measure_check[0] > qm_measure_check[0]:
                    # Not minimal - reset laws_completed and continue
                    laws_completed = False
                    # Set current_ast for continuation
                    current_ast = last_ast_check
            
            # If laws didn't complete, we need to build steps from scratch
            # This can happen when laws_result is not in DNF format
            # BUT: Skip if input is already minimal DNF (checked above)
            if not laws_completed and not input_already_minimal:
                # Build user-visible algebraic steps from QM plan
                # Get current AST from last step's after string
                # Note: current_ast may already be set after iterative absorption above
                # But if iterative absorption didn't complete, we need to continue here
                if current_ast is None:
                    if steps:
                        current_expr = steps[-1].after_str
                        current_ast = generate_ast(current_expr)
                        current_ast = normalize_bool_ast(current_ast, expand_imp_iff=True)
                    else:
                        # No laws steps, start from initial normalized AST
                        # Don't use laws_result.get("normalized_ast") as it might already have factorization applied
                        current_ast = node
                else:
                    # current_ast is already set from iterative absorption above
                    # But we need to verify it's the latest state
                    if steps:
                        current_expr = steps[-1].after_str
                        current_ast_check = generate_ast(current_expr)
                        current_ast_check = normalize_bool_ast(current_ast_check, expand_imp_iff=True)
                        # Use the latest state from steps
                        current_ast = current_ast_check
                
                # Check if expression is already minimal DNF before generating steps
                current_is_dnf = is_dnf(current_ast)
                if current_is_dnf:
                    # Compare with QM result to check if already minimal
                    current_canon = canonical_str(current_ast)
                    qm_result_str = qm_result.get("result", "")
                    qm_result_ast = generate_ast(qm_result_str)
                    qm_result_ast = normalize_bool_ast(qm_result_ast, expand_imp_iff=True)
                    qm_result_canon = canonical_str(qm_result_ast)
                    
                    # Check if canonical forms match and measures are equal (already minimal)
                    current_measure = measure(current_ast)
                    qm_measure = measure(qm_result_ast)
                    
                    if current_canon == qm_result_canon and current_measure[0] == qm_measure[0]:
                        # Expression is already minimal DNF - no steps needed
                        # Mark this in the result so frontend can display appropriate message
                        print(f"Expression is already minimal DNF: {current_canon}")
                        # Skip all step generation - steps list will remain empty
                        # Frontend should check if steps is empty and result_dnf matches input
                        pass
                    else:
                        # Expression is in DNF but not minimal - continue with simplification
                        pass
                
                # If we have no steps, we still need to convert to DNF using logical laws
                # Check if current AST is already in DNF
                if not steps and not current_is_dnf:
                    # The expression is not in DNF - convert it using distribution laws
                    from .derivation_builder import convert_to_dnf_with_laws
                    
                    dnf_ast, dnf_steps = convert_to_dnf_with_laws(current_ast, vars_list)
                    
                    if dnf_steps:
                        steps.extend(dnf_steps)
                        current_ast = dnf_ast
                        
                        contradiction_steps = build_contradiction_steps(current_ast, vars_list)
                        if contradiction_steps:
                            steps.extend(contradiction_steps)
                            current_ast = generate_ast(contradiction_steps[-1].after_str)
                            current_ast = normalize_bool_ast(current_ast, expand_imp_iff=True)
                    else:
                        # convert_to_dnf_with_laws didn't work - fall back to canonical DNF as last resort
                        minterms_1 = summary.get("minterms_1", []) if summary else []
                        if minterms_1:
                            from .utils import bin_to_expr
                            from .laws import pretty_with_tokens
                            from .utils import truth_table_hash
                            canonical_terms = []
                            from .qm import _pad_bin
                            for minterm in minterms_1:
                                term = bin_to_expr(_pad_bin(minterm, len(vars_list)), vars_list)
                                canonical_terms.append(term)
                            canonical_dnf_str = " ∨ ".join(canonical_terms) if canonical_terms else "0"
                            canonical_dnf_ast = generate_ast(canonical_dnf_str)
                            canonical_dnf_ast = normalize_bool_ast(canonical_dnf_ast, expand_imp_iff=True)
                            
                            before_str, _ = pretty_with_tokens(current_ast)
                            after_str, _ = pretty_with_tokens(canonical_dnf_ast)
                            before_canon = canonical_str(current_ast)
                            after_canon = canonical_str(canonical_dnf_ast)
                            
                            is_equal = (truth_table_hash(vars_list, before_str) == truth_table_hash(vars_list, after_str))
                            
                            conversion_step = Step(
                                before_str=before_str,
                                after_str=after_str,
                                rule="Konwersja do DNF",
                                category="user",
                                location=None,
                                proof={"method": "tt-hash", "equal": is_equal},
                                before_canon=before_canon,
                                after_canon=after_canon,
                                before_subexpr=before_str,
                                after_subexpr=after_str,
                                before_subexpr_canon=before_canon,
                                after_subexpr_canon=after_canon,
                                before_highlight_spans_cp=None,
                                after_highlight_spans_cp=None,
                            )
                            steps.append(conversion_step)
                            current_ast = canonical_dnf_ast
                
                # Skip step generation if expression is already minimal DNF
                current_canon_check = canonical_str(current_ast)
                qm_result_str_check = qm_result.get("result", "")
                qm_result_ast_check = generate_ast(qm_result_str_check)
                qm_result_ast_check = normalize_bool_ast(qm_result_ast_check, expand_imp_iff=True)
                qm_result_canon_check = canonical_str(qm_result_ast_check)
                current_measure_check = measure(current_ast)
                qm_measure_check = measure(qm_result_ast_check)
                
                is_already_minimal_dnf = (current_is_dnf and 
                                         current_canon_check == qm_result_canon_check and 
                                         current_measure_check[0] == qm_measure_check[0])
                
                # IMPORTANT: Even if expression is in DNF, if it's not minimal, we must continue
                # This ensures we continue simplification after laws steps even if expression is already in DNF
                if current_is_dnf and not is_already_minimal_dnf:
                    # Expression is in DNF but not minimal - force continuation with absorption
                    # This handles cases where laws steps end with DNF but not minimal DNF
                    pass  # Will continue to next section
                
                # Continue with merge steps if available, OR generate simplification steps if already in DNF
                if not is_already_minimal_dnf and merge_edges:
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
                            
                            single_edge_steps = build_merge_steps(working_ast, vars_list, [(left_mask, right_mask, result_mask)])
                            if single_edge_steps:
                                steps.extend(single_edge_steps)
                                working_ast = generate_ast(single_edge_steps[-1].after_str)
                                working_ast = normalize_bool_ast(working_ast, expand_imp_iff=True)
                                made_progress = True
                                processed_edges.add(edge_key)
                                
                                contradiction_steps = build_contradiction_steps(working_ast, vars_list)
                                if contradiction_steps:
                                    steps.extend(contradiction_steps)
                                    working_ast = generate_ast(contradiction_steps[-1].after_str)
                                    working_ast = normalize_bool_ast(working_ast, expand_imp_iff=True)
                                immediate_cleanup = build_absorb_steps(working_ast, vars_list, selected_pi, pi_to_minterms)
                                if immediate_cleanup:
                                    steps.extend(immediate_cleanup)
                                    working_ast = generate_ast(immediate_cleanup[-1].after_str)
                                    working_ast = normalize_bool_ast(working_ast, expand_imp_iff=True)
                                
                                # Check if we've reached the goal after cleanup
                                if steps:
                                    current_canon_check = canonical_str(working_ast)
                                    if current_canon_check == qm_dnf_canon:
                                        # Success! We've reached the minimal DNF
                                        break
                                
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
                            
                            # Try to apply final cleanup to remove redundant terms
                            final_cleanup = build_absorb_steps(final_ast, vars_list, selected_pi, pi_to_minterms)
                            if final_cleanup:
                                steps.extend(final_cleanup)
                                print(f"Applied final cleanup: {len(final_cleanup)} steps")
                elif not is_already_minimal_dnf:
                    # No merge_edges - but expression might still need simplification
                    # Check if current_ast is already minimal by comparing with QM result
                    if current_is_dnf:
                        # Expression is in DNF, check if it needs simplification
                        current_canon = canonical_str(current_ast)
                        qm_result_str = qm_result.get("result", "")
                        qm_result_ast = generate_ast(qm_result_str)
                        qm_result_ast = normalize_bool_ast(qm_result_ast, expand_imp_iff=True)
                        qm_result_canon = canonical_str(qm_result_ast)
                        current_measure = measure(current_ast)
                        qm_measure = measure(qm_result_ast)
                        
                        # If they're different, we need to generate steps to simplify
                        if current_canon != qm_result_canon or current_measure[0] > qm_measure[0]:
                            # Try to generate steps using iterative absorption
                            # This handles cases where we can absorb redundant terms
                            working_ast = current_ast
                            
                            # Iteratively apply absorption until we reach minimal DNF
                            max_absorb_iterations = 50  # Increased from 20
                            for absorb_iteration in range(max_absorb_iterations):
                                # Check if we've reached minimal DNF
                                current_canon_iter = canonical_str(working_ast)
                                current_measure_iter = measure(working_ast)
                                if current_canon_iter == qm_result_canon and current_measure_iter[0] <= qm_measure[0]:
                                    # Reached minimal DNF
                                    break
                                
                                # Try absorption
                                absorb_steps = build_absorb_steps(working_ast, vars_list, selected_pi, pi_to_minterms)
                                if absorb_steps:
                                    steps.extend(absorb_steps)
                                    # Update working_ast
                                    working_ast = generate_ast(absorb_steps[-1].after_str)
                                    working_ast = normalize_bool_ast(working_ast, expand_imp_iff=True)
                                    
                                    # Remove contradictions that may have been created
                                    contradiction_steps = build_contradiction_steps(working_ast, vars_list)
                                    if contradiction_steps:
                                        steps.extend(contradiction_steps)
                                        working_ast = generate_ast(contradiction_steps[-1].after_str)
                                        working_ast = normalize_bool_ast(working_ast, expand_imp_iff=True)
                                    
                                    # After absorption, try to apply more laws to simplify complex terms
                                    from .laws import pretty
                                    current_expr_str = pretty(working_ast)
                                    additional_laws = simplify_with_laws(current_expr_str, max_steps=30, mode="mixed")
                                    if additional_laws.get("steps") and len(additional_laws["steps"]) > 0:
                                        current_measure = measure(working_ast)
                                        for law_step in additional_laws["steps"]:
                                            after_str = law_step.get("after_tree", "")
                                            if after_str and after_str not in ["?", ""]:
                                                try:
                                                    after_ast = generate_ast(after_str)
                                                    after_ast = normalize_bool_ast(after_ast, expand_imp_iff=True)
                                                    after_measure = measure(after_ast)
                                                    # Accept if it doesn't increase literal count
                                                    if after_measure[0] <= current_measure[0]:
                                                        from .utils import truth_table_hash
                                                        hash_before = truth_table_hash(vars_list, current_expr_str)
                                                        hash_after = truth_table_hash(vars_list, after_str)
                                                        if hash_before == hash_after and len(hash_before) > 0:
                                                            before_str, _ = pretty_with_tokens(working_ast)
                                                            after_str, _ = pretty_with_tokens(after_ast)
                                                            step = Step(
                                                                before_str=before_str,
                                                                after_str=after_str,
                                                                rule=law_step.get("law", "Prawa logiczne"),
                                                                location=law_step.get("path"),
                                                                details={},
                                                                proof={"method": "tt-hash", "equal": True},
                                                                before_subexpr=law_step.get("before_subexpr"),
                                                                after_subexpr=law_step.get("after_subexpr"),
                                                                before_canon=canonical_str(working_ast),
                                                                after_canon=canonical_str(after_ast),
                                                                before_subexpr_canon=law_step.get("before_subexpr_canon"),
                                                                after_subexpr_canon=law_step.get("after_subexpr_canon"),
                                                                before_highlight_span=law_step.get("before_highlight_span"),
                                                                after_highlight_span=law_step.get("after_highlight_span")
                                                            )
                                                            steps.append(step)
                                                            working_ast = after_ast
                                                            current_expr_str = after_str
                                                            current_measure = after_measure
                                                            # Re-check if we've reached minimal DNF
                                                            current_canon_check = canonical_str(working_ast)
                                                            if current_canon_check == qm_result_canon and current_measure[0] <= qm_measure[0]:
                                                                break
                                                except Exception:
                                                    continue
                                else:
                                    # No more absorption steps - try laws one more time
                                    from .laws import pretty
                                    current_expr_str = pretty(working_ast)
                                    additional_laws = simplify_with_laws(current_expr_str, max_steps=30, mode="mixed")
                                    if additional_laws.get("steps") and len(additional_laws["steps"]) > 0:
                                        current_measure = measure(working_ast)
                                        for law_step in additional_laws["steps"]:
                                            after_str = law_step.get("after_tree", "")
                                            if after_str and after_str not in ["?", ""]:
                                                try:
                                                    after_ast = generate_ast(after_str)
                                                    after_ast = normalize_bool_ast(after_ast, expand_imp_iff=True)
                                                    after_measure = measure(after_ast)
                                                    if after_measure[0] <= current_measure[0]:
                                                        from .utils import truth_table_hash
                                                        hash_before = truth_table_hash(vars_list, current_expr_str)
                                                        hash_after = truth_table_hash(vars_list, after_str)
                                                        if hash_before == hash_after and len(hash_before) > 0:
                                                            before_str, _ = pretty_with_tokens(working_ast)
                                                            after_str, _ = pretty_with_tokens(after_ast)
                                                            step = Step(
                                                                before_str=before_str,
                                                                after_str=after_str,
                                                                rule=law_step.get("law", "Prawa logiczne"),
                                                                location=law_step.get("path"),
                                                                details={},
                                                                proof={"method": "tt-hash", "equal": True},
                                                                before_subexpr=law_step.get("before_subexpr"),
                                                                after_subexpr=law_step.get("after_subexpr"),
                                                                before_canon=canonical_str(working_ast),
                                                                after_canon=canonical_str(after_ast),
                                                                before_subexpr_canon=law_step.get("before_subexpr_canon"),
                                                                after_subexpr_canon=law_step.get("after_subexpr_canon"),
                                                                before_highlight_span=law_step.get("before_highlight_span"),
                                                                after_highlight_span=law_step.get("after_highlight_span")
                                                            )
                                                            steps.append(step)
                                                            working_ast = after_ast
                                                            current_expr_str = after_str
                                                            current_measure = after_measure
                                                            # Re-check if we've reached minimal DNF
                                                            current_canon_check = canonical_str(working_ast)
                                                            if current_canon_check == qm_result_canon and current_measure[0] <= qm_measure[0]:
                                                                break
                                                except Exception:
                                                    continue
                                    else:
                                        # No more laws steps - check if we're done
                                        final_canon_check = canonical_str(working_ast)
                                        final_measure_check = measure(working_ast)
                                        if final_canon_check == qm_result_canon and final_measure_check[0] <= qm_measure[0]:
                                            break
                                        # If not minimal and no progress, break to avoid infinite loop
                                        break
                            
                            # Update current_ast to final state
                            current_ast = working_ast
                            current_canon = canonical_str(working_ast)
                            
                            # If still not minimal, generate merge_edges from QM selected_pi
                            # This allows us to use build_merge_steps even when QM didn't provide merge_edges
                            if current_canon != qm_result_canon and selected_pi and pi_to_minterms:
                                # Build merge_edges from selected_pi
                                # For each PI, find pairs of minterms that can be merged to form it
                                from .utils import to_bin
                                synthetic_merge_edges = []
                                seen_edges = set()
                                
                                for pi_mask in selected_pi:
                                    covered_minterms = list(pi_to_minterms.get(pi_mask, []))
                                    # For each pair of minterms covered by this PI
                                    for i, m1 in enumerate(covered_minterms):
                                        for m2 in covered_minterms[i+1:]:
                                            # Check if these two minterms differ by exactly one bit
                                            m1_bin = to_bin(m1, len(vars_list))
                                            m2_bin = to_bin(m2, len(vars_list))
                                            
                                            diff_count = sum(1 for a, b in zip(m1_bin, m2_bin) if a != b)
                                            if diff_count == 1:
                                                # These can be merged - create merge edge
                                                # left_mask and right_mask are the binary representations
                                                edge_key = (m1_bin, m2_bin, pi_mask)
                                                if edge_key not in seen_edges:
                                                    synthetic_merge_edges.append((m1_bin, m2_bin, pi_mask))
                                                    seen_edges.add(edge_key)
                                
                                # Use synthetic merge_edges to generate steps
                                if synthetic_merge_edges:
                                    merge_steps = build_merge_steps(working_ast, vars_list, synthetic_merge_edges)
                                    if merge_steps:
                                        steps.extend(merge_steps)
                                        # Update working_ast
                                        working_ast = generate_ast(merge_steps[-1].after_str)
                                        working_ast = normalize_bool_ast(working_ast, expand_imp_iff=True)
                                        current_canon = canonical_str(working_ast)
                                        
                                        # Apply cleanup after merge
                                        if current_canon != qm_result_canon:
                                            final_cleanup = build_absorb_steps(working_ast, vars_list, selected_pi, pi_to_minterms)
                                            if final_cleanup:
                                                steps.extend(final_cleanup)
                                
                                # If still no steps generated, create a fallback step
                                if not steps:
                                    from .laws import pretty_with_tokens
                                    from .utils import truth_table_hash
                                    
                                    before_str, _ = pretty_with_tokens(current_ast)
                                    after_str = qm_result_str
                                    before_canon = canonical_str(current_ast)
                                    after_canon = qm_result_canon
                                    
                                    is_equal = (truth_table_hash(vars_list, before_str) == truth_table_hash(vars_list, after_str))
                                    
                                    if is_equal:
                                        # Create a step showing the simplification
                                        simplification_step = Step(
                                            before_str=before_str,
                                            after_str=after_str,
                                            rule="Uproszczenie DNF",
                                            category="user",
                                            location=None,
                                            proof={"method": "tt-hash", "equal": is_equal},
                                            before_canon=before_canon,
                                            after_canon=after_canon,
                                            before_subexpr=before_str,
                                            after_subexpr=after_str,
                                            before_subexpr_canon=before_canon,
                                            after_subexpr_canon=after_canon,
                                            before_highlight_spans_cp=None,
                                            after_highlight_spans_cp=None,
                                        )
                                        steps.append(simplification_step)
            
            # Validate continuity: prev.after_canon == next.before_canon
            # Enforce hard continuity - remove steps that break the chain
            i = 0
            while i < len(steps) - 1:
                prev_after = steps[i].after_canon if steps[i].after_canon else steps[i].after_str
                next_before = steps[i + 1].before_canon if steps[i + 1].before_canon else steps[i + 1].before_str
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
    
    # Check if expression was already minimal DNF (no steps generated)
    # Use the flag set earlier if available, otherwise check again
    is_already_minimal = False
    if not steps:
        # Check if input is already minimal DNF
        input_ast = normalize_bool_ast(node, expand_imp_iff=True)
        input_is_dnf = is_dnf(input_ast)
        if input_is_dnf:
            input_canon = canonical_str(input_ast)
            input_measure = measure(input_ast)
            if result_dnf and result_dnf not in ["0", "1"]:
                result_ast = generate_ast(result_dnf)
                result_ast = normalize_bool_ast(result_ast, expand_imp_iff=True)
                result_canon = canonical_str(result_ast)
                result_measure = measure(result_ast)
                if input_canon == result_canon and input_measure[0] == result_measure[0]:
                    is_already_minimal = True
    
    return {
        "input_std": input_std,
        "vars": vars_list,
        "initial_canon": initial_canon,
        "steps": [s.__dict__ for s in steps],  # Convert to dict for JSON
        "result_dnf": result_dnf,
        "is_already_minimal": is_already_minimal,  # Flag indicating expression was already minimal
    }


def simplify_to_minimal_dnf(expr: str, var_limit: int = 8) -> Dict[str, Any]:
    try:
        return _simplify_with_dnf_pipeline(expr, var_limit)
    except Exception as pipeline_error:
        print(f"Warning: new DNF pipeline failed ({pipeline_error}), falling back to legacy")
        return _legacy_simplify_to_minimal_dnf(expr, var_limit)
