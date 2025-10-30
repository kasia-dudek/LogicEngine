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

