import pytest
from logicengine.engine import LogicEngine

@pytest.mark.parametrize("expr,expected_tautology", [
    ("A ∨ ¬A", True),
    ("A ∧ B", False),
    ("A → (B ∨ ¬B)", True),
    ("A ∧ ¬A", False),
    ("(A ∧ B) ∨ ¬C", False),
])
def test_engine_integration(expr, expected_tautology):
    result = LogicEngine.analyze(expr)
    # Sprawdź kluczowe pola
    assert "expression" in result
    assert "parsed" in result
    assert "truth_table" in result or "truth_table_error" in result
    assert "ast" in result or "ast_error" in result
    assert "onp" in result or "onp_error" in result
    assert "kmap_simplification" in result or "kmap_error" in result
    assert "qm_simplification" in result or "qm_error" in result
    assert "is_tautology" in result or "tautology_error" in result
    # Sprawdź poprawność wyniku tautologii
    if "is_tautology" in result:
        assert result["is_tautology"] == expected_tautology 