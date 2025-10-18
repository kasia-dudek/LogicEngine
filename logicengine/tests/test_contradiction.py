import pytest
from src.logicengine.contradiction import is_contradiction

@pytest.mark.parametrize("expr,expected", [
    ("A & ~A", True),    # sprzeczność
    ("A | ~A", False),   # tautologia (nie sprzeczność)
    ("A & B", False),    # nie-sprzeczność
    ("A -> (B | ~B)", False),  # tautologia implikacji (nie sprzeczność)
    ("1", False),        # stała prawda (nie sprzeczność)
    ("0", True),         # stała fałsz (sprzeczność)
    ("(A & ~A) | B", False),  # nie-sprzeczność (może być prawdziwe gdy B=1)
    ("(A & ~A) & B", True),   # sprzeczność (zawsze fałsz)
])
def test_is_contradiction(expr, expected):
    assert is_contradiction(expr) == expected
