"""
Integration tests for axiomatic layer.
"""

import pytest
from src.logicengine.axioms import (
    META, IMP, IFF, unify, instantiate, axioms_matches,
    AXIOMS, DERIVED_FROM_AXIOMS
)
from src.logicengine.laws import VAR, CONST, NOT, AND, OR, measure
from src.logicengine.ast import generate_ast, normalize_bool_ast, canonical_str


class TestUnification:
    """Test unification algorithm."""
    
    def test_meta_variable_binding(self):
        """Test meta-variable binding."""
        pattern = META("p")
        term = VAR("x")
        env = unify(pattern, term)
        assert env == {"p": VAR("x")}
    
    def test_constant_unification(self):
        """Test constant unification."""
        pattern = CONST(1)
        term = CONST(1)
        env = unify(pattern, term)
        assert env == {}
        
        pattern = CONST(1)
        term = CONST(0)
        env = unify(pattern, term)
        assert env is None
    
    def test_variable_unification(self):
        """Test variable unification."""
        pattern = VAR("x")
        term = VAR("x")
        env = unify(pattern, term)
        assert env == {}
        
        pattern = VAR("x")
        term = VAR("y")
        env = unify(pattern, term)
        assert env is None
    
    def test_not_unification(self):
        """Test NOT operator unification."""
        pattern = NOT(META("p"))
        term = NOT(VAR("x"))
        env = unify(pattern, term)
        assert env == {"p": VAR("x")}
    
    def test_and_unification_commutative(self):
        """Test AND operator unification (commutative)."""
        pattern = AND([META("p"), META("q")])
        term = AND([VAR("x"), VAR("y")])
        env = unify(pattern, term)
        assert env == {"p": VAR("x"), "q": VAR("y")}
        
        # Test swapped order
        term = AND([VAR("y"), VAR("x")])
        env = unify(pattern, term)
        assert env == {"p": VAR("y"), "q": VAR("x")}
    
    def test_or_unification_commutative(self):
        """Test OR operator unification (commutative)."""
        pattern = OR([META("p"), META("q")])
        term = OR([VAR("x"), VAR("y")])
        env = unify(pattern, term)
        assert env == {"p": VAR("x"), "q": VAR("y")}
    
    def test_imp_unification_non_commutative(self):
        """Test IMP operator unification (non-commutative)."""
        pattern = IMP(META("p"), META("q"))
        term = IMP(VAR("x"), VAR("y"))
        env = unify(pattern, term)
        assert env == {"p": VAR("x"), "q": VAR("y")}
        
        # Test that different variable assignment works
        term = IMP(VAR("y"), VAR("x"))
        env = unify(pattern, term)
        assert env == {"p": VAR("y"), "q": VAR("x")}


class TestInstantiation:
    """Test instantiation algorithm."""
    
    def test_simple_instantiation(self):
        """Test simple instantiation."""
        pattern = META("p")
        env = {"p": VAR("x")}
        result = instantiate(pattern, env)
        assert result == VAR("x")
    
    def test_complex_instantiation(self):
        """Test complex instantiation."""
        pattern = AND([META("p"), NOT(META("q"))])
        env = {"p": VAR("x"), "q": VAR("y")}
        result = instantiate(pattern, env)
        expected = AND([VAR("x"), NOT(VAR("y"))])
        assert result == expected


class TestAxiomMatching:
    """Test axiom matching."""
    
    def test_implication_to_or_axiom(self):
        """Test A1: (p→q) ⇒ (¬p ∨ q)."""
        # Test with simple implication
        expr = IMP(VAR("a"), VAR("b"))
        matches = axioms_matches(expr)
        
        assert len(matches) == 1
        match = matches[0]
        assert match["axiom_id"] == 1
        assert match["axiom_name"] == "A1"
        assert match["source"] == "axiom"
        
        # Check that the result is normalized OR with correct components
        after = match["after"]
        assert after["op"] == "OR"
        assert len(after["args"]) == 2
        # Check if both ¬a and b are present (order may vary due to normalization)
        components = {canonical_str(arg) for arg in after["args"]}
        expected_components = {canonical_str(NOT(VAR("a"))), canonical_str(VAR("b"))}
        assert components == expected_components
    
    def test_biconditional_to_cnf_axiom(self):
        """Test A2: (p↔q) ⇒ (p∧q) ∨ (¬p∧¬q)."""
        expr = IFF(VAR("a"), VAR("b"))
        matches = axioms_matches(expr)
        
        assert len(matches) == 1
        match = matches[0]
        assert match["axiom_id"] == 2
        assert match["axiom_name"] == "A2"
        assert match["source"] == "axiom"
    
    def test_a12_axiom(self):
        """Test A12: [p → (q ∧ ¬q)] ⇒ ¬p."""
        expr = IMP(VAR("a"), AND([VAR("b"), NOT(VAR("b"))]))
        matches = axioms_matches(expr)
        
        assert len(matches) >= 1
        # Find A12 match (should be the best one)
        a12_match = None
        for match in matches:
            if match["axiom_id"] == 12:
                a12_match = match
                break
        
        assert a12_match is not None
        assert a12_match["axiom_name"] == "A12"
        assert a12_match["source"] == "axiom"
        
        # Check that the result is NOT(a)
        expected = NOT(VAR("a"))
        assert canonical_str(a12_match["after"]) == canonical_str(expected)
    
    def test_measure_reduction(self):
        """Test that axiom matches only return steps that reduce measure."""
        # This should not match because it would increase measure
        expr = OR([NOT(VAR("a")), VAR("b")])
        matches = axioms_matches(expr)
        
        # Should not suggest converting back to implication
        assert len(matches) == 0


class TestIntegration:
    """Test integration with existing system."""
    
    def test_implication_desugar(self):
        """Test implication desugaring in axioms mode."""
        expr_str = "A -> B"
        expr = normalize_bool_ast(generate_ast(expr_str), expand_imp_iff=False)
        
        matches = axioms_matches(expr)
        assert len(matches) == 1
        
        match = matches[0]
        assert match["source"] == "axiom"
        assert match["axiom_id"] == 1
        
        # A1 is desugaring axiom - may increase measure but should convert to OR
        assert match["after"]["op"] == "OR"
    
    def test_biconditional_desugar(self):
        """Test biconditional desugaring in axioms mode."""
        expr_str = "A <-> B"
        expr = normalize_bool_ast(generate_ast(expr_str), expand_imp_iff=False)
        
        matches = axioms_matches(expr)
        assert len(matches) == 1
        
        match = matches[0]
        assert match["source"] == "axiom"
        assert match["axiom_id"] == 2
        
        # A2 is desugaring axiom - may increase measure but should convert to OR
        assert match["after"]["op"] == "OR"
    
    def test_a12_application(self):
        """Test A12 application."""
        expr_str = "A -> (B & ~B)"
        expr = normalize_bool_ast(generate_ast(expr_str), expand_imp_iff=False)
        
        matches = axioms_matches(expr)
        assert len(matches) >= 1
        
        # Find A12 match (should be the best one)
        a12_match = None
        for match in matches:
            if match["axiom_id"] == 12:
                a12_match = match
                break
        
        assert a12_match is not None
        assert a12_match["source"] == "axiom"
        
        # Check that result is ~A
        expected = normalize_bool_ast(generate_ast("~A"), expand_imp_iff=False)
        assert canonical_str(a12_match["after"]) == canonical_str(expected)
    
    def test_no_measure_increase(self):
        """Test that no axiom increases measure."""
        # Test various expressions that should not be expanded
        test_exprs = [
            "~A | B",  # Should not convert back to A -> B
            "A | B",   # Should not convert to anything
            "A & B",   # Should not convert to anything
        ]
        
        for expr_str in test_exprs:
            expr = normalize_bool_ast(generate_ast(expr_str), expand_imp_iff=False)
            matches = axioms_matches(expr)
            
            for match in matches:
                assert measure(match["after"]) < measure(match["before"])


class TestDerivedFromAxioms:
    """Test mapping of algebraic laws to axioms."""
    
    def test_derived_from_axioms_mapping(self):
        """Test that DERIVED_FROM_AXIOMS mapping is complete."""
        # Check that all expected laws are mapped
        expected_laws = [
            "Absorpcja (∨)",
            "De Morgan: ¬(A ∧ B) → ¬A ∨ ¬B",
            "Idempotencja (∨)",
            "Idempotencja (∧)",
            "Element neutralny (∨)",
            "Element neutralny (∧)",
            "Element pochłaniający (∨)",
            "Element pochłaniający (∧)",
            "Konsensus",
            "Pokrywanie"
        ]
        
        for law in expected_laws:
            assert law in DERIVED_FROM_AXIOMS
            assert isinstance(DERIVED_FROM_AXIOMS[law], list)
            assert len(DERIVED_FROM_AXIOMS[law]) > 0
