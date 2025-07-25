import logging
from .truth_table import generate_truth_table, TruthTableError
from .parser import LogicExpressionError

# Usuń lub zakomentuj logger.error (zostaw tylko krytyczne błędy produkcyjne)

def is_tautology(expr: str) -> bool:
    """
    Sprawdza, czy wyrażenie logiczne jest tautologią (zawsze prawdziwe).
    Args:
        expr (str): Wyrażenie logiczne.
    Returns:
        bool: True jeśli tautologia, False w przeciwnym razie.
    """
    try:
        table = generate_truth_table(expr)
        # Tautologia: wszystkie wyniki muszą być True (1)
        return all(row['result'] for row in table)
    except (LogicExpressionError, TruthTableError) as e:
        # logger.error(f"Błąd sprawdzania tautologii: {e}")
        return False 