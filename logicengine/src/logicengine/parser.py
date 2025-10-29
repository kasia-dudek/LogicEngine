# parser.py
"""Standardize and validate logical expressions.

Public API:
- class LogicExpressionError
- def validate_and_standardize(expr: str) -> str
- class LogicParser with .standardize() and .validate() if you prefer OOP style
"""

from __future__ import annotations
from dataclasses import dataclass

from .validation import (
    ValidationError,
    validate as base_validate,
    standardize as base_standardize,
    validate_and_standardize as base_vas,
)

class LogicExpressionError(Exception):
    pass

class LogicParser:
    @staticmethod
    def standardize(expr: str) -> str:
        try:
            return base_standardize(expr)
        except ValidationError as e:
            # Re-throw as LogicExpressionError to preserve prior public surface if needed
            raise LogicExpressionError(str(e)) from e

    @staticmethod
    def validate(expr: str) -> None:
        try:
            base_validate(expr)
        except ValidationError as e:
            raise LogicExpressionError(str(e)) from e

    @staticmethod
    def parse(expr: str) -> str:
        """Validate and return standardized expression."""
        try:
            return base_vas(expr)
        except ValidationError as e:
            raise LogicExpressionError(str(e)) from e

def validate_and_standardize(expr: str) -> str:
    """Functional entrypoint kept for backward compatibility with existing code."""
    try:
        return base_vas(expr)
    except ValidationError as e:
        raise LogicExpressionError(str(e)) from e
