# parser.py
"""Standardize and validate logical expressions."""

import re
from .validation import validate as base_validate, ValidationError


class LogicExpressionError(Exception):
    pass


OPERATOR_MAP = {
    '&': '∧',
    '|': '∨',
    '+': '∨',
    '~': '¬',
    '!': '¬',
    '=>': '→',
    '->': '→',
    '<=>': '↔',
    '<->': '↔',
    '^': '⊕',
    '↑': '↑',
    '↓': '↓',
    '≡': '↔',
    # Keep standard operators as-is
    '∧': '∧',
    '∨': '∨',
    '¬': '¬',
    '→': '→',
    '↔': '↔',
    '⊕': '⊕',
}

BINARY_OPERATORS = {'∧', '∨', '⊕', '↑', '↓', '→', '↔', '≡'}
UNARY_OPERATORS = {'¬'}
ALL_OPERATORS = BINARY_OPERATORS | UNARY_OPERATORS


class LogicParser:
    VALID_VARS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

    @staticmethod
    def standardize(expr: str) -> str:
        if expr is None:
            raise LogicExpressionError("Wyrażenie nie może być puste.")
        s = str(expr)

        # Replace multi-char operators first to avoid overlaps
        for a, b in (('<=>', '↔'), ('<->', '↔'), ('=>', '→'), ('->', '→')):
            s = s.replace(a, b)

        # Replace remaining aliases
        for alt, std in OPERATOR_MAP.items():
            if alt in {'<=>', '<->', '=>', '->'}:
                continue
            s = s.replace(alt, std)

        # Strip whitespace but preserve operators
        return re.sub(r"\s+", "", s)

    @staticmethod
    def validate(expr: str) -> None:
        # Delegate to base validator (chars, parentheses, basic shape)
        try:
            base_validate(expr)
        except ValidationError as e:
            raise LogicExpressionError(str(e))

        # Lightweight token walk for common syntax errors
        prev = None  # 'var' | 'op' | '(' | ')'
        depth = 0

        for ch in expr:
            if ch in LogicParser.VALID_VARS or ch in {'0', '1'}:
                if prev == ')':
                    raise LogicExpressionError("Brak operatora między ')' a zmienną")
                prev = 'var'
                continue

            if ch == '(':
                if prev in {'var', ')'}:
                    raise LogicExpressionError("Brak operatora przed '('")
                depth += 1
                prev = '('
                continue

            if ch == ')':
                if prev in {'op', '('}:
                    raise LogicExpressionError("Puste nawiasy lub operator przed ')'")
                depth -= 1
                if depth < 0:
                    raise LogicExpressionError("Niezgodna liczba nawiasów.")
                prev = ')'
                continue

            if ch in ALL_OPERATORS:
                if ch in UNARY_OPERATORS:
                    if prev in {'var', ')'}:
                        raise LogicExpressionError("Nieprawidłowe użycie negacji")
                    prev = 'op'
                    continue
                if prev not in {'var', ')'}:
                    raise LogicExpressionError("Operator binarny w niepoprawnym miejscu")
                prev = 'op'
                continue

            raise LogicExpressionError(f"Niedozwolony znak: {ch}")

        if depth != 0:
            raise LogicExpressionError("Niezgodna liczba nawiasów.")
        if prev == 'op':
            raise LogicExpressionError("Wyrażenie nie może kończyć się operatorem")

    @staticmethod
    def parse(expr: str) -> str:
        std = LogicParser.standardize(expr)
        LogicParser.validate(std)
        return std


def validate_and_standardize(expr: str) -> str:
    std = LogicParser.standardize(expr)
    LogicParser.validate(std)
    return std
