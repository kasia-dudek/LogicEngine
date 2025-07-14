import pytest
from src.logicengine.ast import generate_ast, ASTError

@pytest.mark.parametrize("expr,expected", [
    ("(A ∧ B) ∨ ¬C", {"type": "∨", "left": {"type": "∧", "left": "A", "right": "B"}, "right": {"type": "¬", "child": "C"}}),
    ("A → (B ↔ C)", {"type": "→", "left": "A", "right": {"type": "↔", "left": "B", "right": "C"}}),
    ("¬A", {"type": "¬", "child": "A"}),
    ("A", "A"),
])
def test_generate_ast(expr, expected):
    ast = generate_ast(expr)
    assert ast == expected

@pytest.mark.parametrize("expr", [
    "(A & B)",
    "A ++ B",
    "(A ∧ B",
    "A 2 B",
])
def test_ast_invalid(expr):
    with pytest.raises(ASTError):
        generate_ast(expr) 