import pytest
from logicengine.qm import simplify_qm, QMError
from logicengine.kmap import simplify_kmap

@pytest.mark.parametrize("expr", [
    "(A ∧ B) ∨ (¬A ∧ B)",
    "A ∧ (B ∨ ¬C)",
    "¬A ∧ ¬B",
    "A",
])
def test_qm_simplify(expr):
    qm = simplify_qm(expr)
    kmap = simplify_kmap(expr)
    assert "result" in qm
    assert "steps" in qm
    assert isinstance(qm["steps"], list)
    assert qm["result"]
    # Wynik QM powinien być logicznie równoważny uproszczeniu K-map (niekoniecznie identyczny tekst)
    assert set(qm["result"].replace(' ', '').split('∨')) == set(kmap["result"].replace(' ', '').split('∨'))

@pytest.mark.parametrize("expr", [
    "A ∧ B ∧ C ∧ D ∧ E",  # za dużo zmiennych
])
def test_qm_errors(expr):
    with pytest.raises(QMError):
        simplify_qm(expr) 