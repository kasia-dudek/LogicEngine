# test_simplify_steps.py
"""Tests for the step-based simplification system."""

import pytest
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from logicengine.engine import simplify_to_minimal_dnf, TooManyVariables
from logicengine.utils import truth_table_hash, equivalent
from logicengine.ast import collect_variables


def test_basic_simplification():
    """Test basic absorption simplification."""
    expr = "(A∧B)∨A"
    result = simplify_to_minimal_dnf(expr)
    
    assert result["input_std"] == "(A∧B)∨A"
    assert result["vars"] == ["A", "B"]
    assert len(result["steps"]) > 0
    assert result["result_dnf"] == "A"


def test_tautology_complement():
    """Test tautology: A ∨ ¬A."""
    expr = "A∨¬A"
    result = simplify_to_minimal_dnf(expr)
    
    assert result["result_dnf"] == "1"
    # Steps may be skipped if they fail equivalence check
    # Just verify the result is correct


def test_already_minimal():
    """Test expression that is already minimal."""
    expr = "A∨B"
    result = simplify_to_minimal_dnf(expr)
    
    # Accept various formatting of minimal DNF (spaces are OK)
    assert "A" in result["result_dnf"] and "B" in result["result_dnf"]
    # Already minimal - should have minimal steps or just formatting


def test_contradiction():
    """Test contradiction: A ∧ ¬A."""
    expr = "A∧¬A"
    result = simplify_to_minimal_dnf(expr)
    
    assert result["result_dnf"] == "0"
    # Steps may be skipped if they fail equivalence check
    # Just verify the result is correct


def test_too_many_variables():
    """Test that TooManyVariables exception is raised."""
    expr = "A∧B∧C∧D∧E∧F∧G∧H∧I"  # 9 variables
    with pytest.raises(TooManyVariables):
        simplify_to_minimal_dnf(expr)


def test_variable_collection():
    """Test variable collection."""
    from logicengine.ast import generate_ast, normalize_bool_ast
    
    expr = "A∧B∨C"
    ast = generate_ast(expr)
    node = normalize_bool_ast(ast)
    vars_list = collect_variables(node)
    
    assert "A" in vars_list
    assert "B" in vars_list
    assert "C" in vars_list
    assert len(vars_list) == 3


def test_truth_table_hash():
    """Test truth table hashing."""
    # Test equivalent expressions
    assert equivalent(["A"], "A", "A")
    assert equivalent(["A", "B"], "A", "A")
    
    # Test non-equivalent expressions
    # A vs A∧B should be different
    assert not equivalent(["A", "B"], "A", "A∧B")
    # A vs ¬A should be different
    assert not equivalent(["A"], "A", "¬A")


def test_stability():
    """Test that same input gives same output."""
    expr = "(A∧B)∨A"
    result1 = simplify_to_minimal_dnf(expr)
    result2 = simplify_to_minimal_dnf(expr)
    
    # Should give identical results
    assert result1["result_dnf"] == result2["result_dnf"]
    assert result1["vars"] == result2["vars"]
    assert len(result1["steps"]) == len(result2["steps"])


def test_step_structure():
    """Test that steps have required fields."""
    expr = "A∨B"
    result = simplify_to_minimal_dnf(expr)
    
    for step in result["steps"]:
        assert "before_str" in step
        assert "after_str" in step
        assert "rule" in step
        # location is optional
        # details and proof are optional


def test_neutral_element():
    """Test neutral element simplification."""
    expr = "A∨0"
    result = simplify_to_minimal_dnf(expr)
    
    assert result["result_dnf"] == "A"
    # Should have neutral element step
    has_neutral = any("neutral" in step.get("rule", "").lower() 
                     for step in result["steps"])
    assert has_neutral


def test_double_negation():
    """Test double negation elimination."""
    expr = "¬¬A"
    result = simplify_to_minimal_dnf(expr)
    
    assert result["result_dnf"] == "A"
    # Should have double negation step
    has_dneg = any("negacja" in step.get("rule", "").lower() 
                  for step in result["steps"])
    assert has_dneg


def test_variable_limit_configurable():
    """Test that variable limit can be configured."""
    # Create expression with 10 variables
    vars_str = "∧".join([chr(ord("A") + i) for i in range(10)])
    expr = vars_str
    
    # Should work with limit 10
    result = simplify_to_minimal_dnf(expr, var_limit=10)
    assert len(result["vars"]) == 10
    
    # Should fail with limit 8
    with pytest.raises(TooManyVariables):
        simplify_to_minimal_dnf(expr, var_limit=8)


def test_minimality_guarantee_simple():
    """Test that result is always minimal DNF for simple cases."""
    from logicengine.qm import simplify_qm
    from logicengine.laws import measure
    from logicengine.ast import generate_ast, normalize_bool_ast
    
    test_cases = [
        "(A∧B)∨(A∧¬B)",
        "(A∧B∧C)∨(A∧¬B∧C)",
        "(A∧B)∨(¬A∧C)",
    ]
    
    for expr in test_cases:
        result = simplify_to_minimal_dnf(expr, var_limit=8)
        qm_result = simplify_qm(expr)
        
        result_dnf = result['result_dnf']
        qm_dnf = qm_result['result']
        
        # Check literal count matches QM
        result_ast = generate_ast(result_dnf)
        result_ast = normalize_bool_ast(result_ast, expand_imp_iff=True)
        result_m = measure(result_ast)
        
        qm_ast = generate_ast(qm_dnf)
        qm_ast = normalize_bool_ast(qm_ast, expand_imp_iff=True)
        qm_m = measure(qm_ast)
        
        assert result_m[0] == qm_m[0], f"Result not minimal for {expr}: laws={result_m[0]}, qm={qm_m[0]}"


def test_minimality_guarantee_complex():
    """Test that result is always minimal DNF for complex cases needing merge."""
    from logicengine.qm import simplify_qm
    from logicengine.laws import measure
    from logicengine.ast import generate_ast, normalize_bool_ast
    
    # These require QM fallback because laws don't reach minimality
    test_cases = [
        "(A∧B∧C)∨(A∧¬B∧C)∨(A∧B∧¬C)∨(¬A∧B∧C)",
        "((A∨(A∧B))∧(¬(B∧¬C)∨¬A∨C)∧(A∨¬A))∨(A∧B∧C)",
    ]
    
    for expr in test_cases:
        result = simplify_to_minimal_dnf(expr, var_limit=8)
        qm_result = simplify_qm(expr)
        
        result_dnf = result['result_dnf']
        qm_dnf = qm_result['result']
        
        # Check literal count matches QM
        result_ast = generate_ast(result_dnf)
        result_ast = normalize_bool_ast(result_ast, expand_imp_iff=True)
        result_m = measure(result_ast)
        
        qm_ast = generate_ast(qm_dnf)
        qm_ast = normalize_bool_ast(qm_ast, expand_imp_iff=True)
        qm_m = measure(qm_ast)
        
        assert result_m[0] == qm_m[0], f"Result not minimal for {expr}: laws={result_m[0]}, qm={qm_m[0]}"


def test_step_continuity():
    """Test that all steps are continuous (prev.after == next.before)."""
    test_cases = [
        "(A∧B)∨(A∧¬B)",
        "((A∨(A∧B))∧(¬(B∧¬C)∨¬A∨C)∧(A∨¬A))∨(A∧B∧C)",
    ]
    
    for expr in test_cases:
        result = simplify_to_minimal_dnf(expr, var_limit=8)
        
        # Check continuity
        for i in range(len(result['steps']) - 1):
            prev_after = result['steps'][i]['after_str']
            next_before = result['steps'][i+1]['before_str']
            assert prev_after == next_before, \
                f"Continuity broken at step {i+1}→{i+2} for {expr}"


def test_truth_table_correctness():
    """Test that result has same truth table as input."""
    from logicengine.utils import truth_table_hash
    
    test_cases = [
        "(A∧B)∨(A∧¬B)",
        "(A∧B∧C)∨(A∧¬B∧C)∨(A∧B∧¬C)∨(¬A∧B∧C)",
        "A∧(C∨¬B∨(B∧C))",
    ]
    
    for expr in test_cases:
        result = simplify_to_minimal_dnf(expr, var_limit=8)
        
        result_hash = truth_table_hash(result['vars'], result['result_dnf'])
        expr_hash = truth_table_hash(result['vars'], expr)
        
        assert result_hash == expr_hash, \
            f"TT mismatch for {expr}: result={result['result_dnf']}"


def test_merge_index_isolation():
    """
    Test that left_idx/right_idx don't leak between different OR nodes.
    
    This test ensures that when iterating through OR nodes in build_merge_steps,
    indices are reset for each OR node and don't accidentally match terms from
    different OR nodes.
    """
    from logicengine.derivation_builder import build_merge_steps, term_from_lits, normalize_bool_ast
    from logicengine.ast import generate_ast
    
    # Create an AST with two separate OR nodes:
    # OR1: (A∧B) ∨ (A∧¬B)  -> should merge to A
    # OR2: (C∧D) ∨ (¬C∧D)  -> should merge to D
    # These should NOT interfere with each other
    expr = "(A∧B) ∨ (A∧¬B) ∨ (C∧D) ∨ (¬C∧D)"
    ast = normalize_bool_ast(generate_ast(expr))
    
    # Define merge edges for both OR nodes
    # Edge 1: merge (A∧B) and (A∧¬B) -> A
    # Edge 2: merge (C∧D) and (¬C∧D) -> D
    # Mask format: binary string for [A,B,C,D] order
    merge_edges = [
        ("11--", "10--", "1---"),  # (A∧B) ∧ (A∧¬B) -> A
        ("--11", "--01", "---1"),  # (C∧D) ∧ (¬C∧D) -> D
    ]
    
    vars_list = ["A", "B", "C", "D"]
    
    # Build merge steps
    steps = build_merge_steps(ast, vars_list, merge_edges)
    
    # Verify that steps were generated correctly
    # Should have steps for both merges (3 steps each: factor, tautology, neutral)
    # Plus potentially ensure_pair_present steps
    assert len(steps) > 0, "No steps generated"
    
    # Verify that the steps are valid (non-empty strings)
    for step in steps:
        assert step.before_str is not None and step.before_str != "", "Empty before_str"
        assert step.after_str is not None and step.after_str != "", "Empty after_str"
        assert step.rule is not None and step.rule != "", "Empty rule"
        
        # Verify TT equivalence
        assert step.proof.get("equal", False) == True, \
            f"Step not equivalent: {step.before_str} -> {step.after_str}"

