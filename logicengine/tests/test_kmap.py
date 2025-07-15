import pytest
from logicengine.kmap import simplify_kmap, KMapError

@pytest.mark.parametrize("expr,expected_result", [
    ("(A ∧ B) ∨ (¬A ∧ B)", None),  # uproszczenie: B
    ("A ∧ (B ∨ ¬C)", None),        # uproszczenie: A∧(B∨¬C) (przykład, uproszczenie zależy od algorytmu)
    ("¬A ∧ ¬B", None),             # uproszczenie: ¬A∧¬B
    ("A", None),                   # uproszczenie: A
])
def test_kmap_simplify(expr, expected_result):
    result = simplify_kmap(expr)
    assert "result" in result
    assert "steps" in result
    assert isinstance(result["steps"], list)
    assert result["result"]  # uproszczone wyrażenie nie jest puste

@pytest.mark.parametrize("expr", [
    "A ∧ B ∧ C ∧ D ∧ E",  # za dużo zmiennych
])
def test_kmap_errors(expr):
    with pytest.raises(KMapError):
        simplify_kmap(expr) 