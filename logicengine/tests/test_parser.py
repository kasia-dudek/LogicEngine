import pytest
from src.logicengine.parser import LogicParser, LogicExpressionError

@pytest.mark.parametrize("expr,expected", [
    ("(A ∧ B) ∨ ¬C", "(A∧B)∨¬C"),
    ("A → (B ↔ C)", "A→(B↔C)"),
    ("¬A", "¬A"),
    ("A | B", "A∨B"),
    ("A & B", "A∧B"),
    ("A + B", "A∨B"),
    ("A => B", "A→B"),
    ("A <=> B", "A↔B"),
])
def test_standardize_and_validate(expr, expected):
    std = LogicParser.standardize(expr)
    assert std == expected
    # nie powinno rzucać wyjątku
    LogicParser.validate(std)

@pytest.mark.parametrize("expr", [
    "(A & B",      # brak nawiasu
    "A ++ B",      # podwójny operator
    "A 2 B",       # niepoprawny znak
    "A ∧ (B ∨)",   # operator na końcu
    "(A ∧) ∨ B",   # operator na końcu nawiasu
    "A ∧ ∧ B",     # podwójny operator
])
def test_invalid_expressions(expr):
    std = LogicParser.standardize(expr)
    with pytest.raises(LogicExpressionError):
        LogicParser.validate(std) 