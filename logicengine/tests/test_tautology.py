import pytest
from logicengine.tautology import is_tautology

@pytest.mark.parametrize("expr,expected", [
    ("A ∨ ¬A", True),  # tautologia
    ("A ∧ B", False),   # nie-tautologia
    ("A → (B ∨ ¬B)", True),  # tautologia implikacji
    ("A ∧ ¬A", False),  # sprzeczność
    ("1", True),        # stała prawda
    ("0", False),       # stała fałsz
])
def test_is_tautology(expr, expected):
    assert is_tautology(expr) == expected 