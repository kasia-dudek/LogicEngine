"""Tautology checking functionality."""

from .truth_table import generate_truth_table, TruthTableError
from .parser import LogicExpressionError


def is_tautology(expr: str) -> bool:
    """
    Check if a logical expression is a tautology (always true).
    
    Args:
        expr: Logical expression string.
        
    Returns:
        True if tautology, False otherwise.
        
    Raises:
        Returns False if there's an error in expression processing.
    """
    try:
        table = generate_truth_table(expr)
        return all(row['result'] for row in table)
    except (LogicExpressionError, TruthTableError):
        return False
