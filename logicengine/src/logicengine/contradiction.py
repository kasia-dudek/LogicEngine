"""Contradiction checking functionality."""

from .truth_table import generate_truth_table, TruthTableError
from .parser import LogicExpressionError, validate_and_standardize


def is_contradiction(expr: str) -> bool:
    """
    Check if a logical expression is a contradiction (always false).
    
    Args:
        expr: Logical expression string.
        
    Returns:
        True if contradiction, False otherwise.
        
    Raises:
        Returns False if there's an error in expression processing.
    """
    try:
        std_expr = validate_and_standardize(expr)
        table = generate_truth_table(std_expr)
        return not any(row['result'] for row in table)
    except (LogicExpressionError, TruthTableError):
        return False
