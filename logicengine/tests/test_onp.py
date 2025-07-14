import pytest
from src.logicengine.onp import to_onp, ONPError

@pytest.mark.parametrize("expr,expected", [
    ("(A ∧ B) ∨ ¬C", "A B ∧ C ¬ ∨"),
    ("A → (B ↔ C)", "A B C ↔ →"),
    ("¬A", "A ¬"),
    ("A", "A"),
])
def test_to_onp(expr, expected):
    onp = to_onp(expr)
    assert onp == expected

@pytest.mark.parametrize("expr", [
    "(A & B)",
    "A ++ B",
    "(A ∧ B",
    "A 2 B",
])
def test_onp_invalid(expr):
    with pytest.raises(ONPError):
        to_onp(expr) 