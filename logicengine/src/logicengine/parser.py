import re
from typing import List

class LogicExpressionError(Exception):
    pass

class LogicParser:
    # Obsługiwane operatory i ich zamienniki
    OPERATORS = {
        '¬': '¬',
        '~': '¬',
        '!': '¬',
        '∧': '∧',
        '&': '∧',
        '^': '∧',
        '∨': '∨',
        '|': '∨',
        '+': '∨',
        '→': '→',
        '=>': '→',
        '⇒': '→',
        '↔': '↔',
        '<=>': '↔',
        '⇔': '↔',
    }
    VALID_VARS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    VALID_CHARS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ() ") | set(OPERATORS.keys()) | set(OPERATORS.values())

    @classmethod
    def standardize(cls, expr: str) -> str:
        # Usuwa spacje, zamienia alternatywne operatory na standardowe
        expr = expr.replace(' ', '')
        for alt, std in cls.OPERATORS.items():
            expr = expr.replace(alt, std)
        return expr

    @classmethod
    def validate(cls, expr: str) -> None:
        # Sprawdza poprawność znaków
        for ch in expr:
            if ch not in cls.VALID_VARS and ch not in '()' and ch not in cls.OPERATORS.values():
                raise LogicExpressionError(f"Nieprawidłowy znak: '{ch}'")
        # Sprawdza poprawność nawiasów
        if not cls._check_parentheses(expr):
            raise LogicExpressionError("Niezamknięty nawias")
        # Sprawdza poprawność operatorów i zmiennych
        if not cls._check_syntax(expr):
            raise LogicExpressionError("Nieprawidłowa składnia wyrażenia")

    @staticmethod
    def _check_parentheses(expr: str) -> bool:
        count = 0
        for ch in expr:
            if ch == '(': count += 1
            elif ch == ')': count -= 1
            if count < 0: return False
        return count == 0

    @classmethod
    def _check_syntax(cls, expr: str) -> bool:
        # Prosty automat: zmienna lub ¬, potem operator lub ) lub koniec
        prev = None
        for i, ch in enumerate(expr):
            if ch in cls.VALID_VARS:
                if prev in cls.VALID_VARS or prev == ')':
                    return False
            elif ch in cls.OPERATORS.values():
                if prev is None or prev in cls.OPERATORS.values() or prev == '(':  # operator na początku, po operatorze lub po (
                    if ch != '¬':
                        return False
            elif ch == '(':
                if prev in cls.VALID_VARS or prev == ')':
                    return False
            elif ch == ')':
                if prev in cls.OPERATORS.values() or prev == '(':  # ) po operatorze lub po (
                    return False
            prev = ch
        if prev in cls.OPERATORS.values() and prev != '¬':
            return False
        return True

    @classmethod
    def parse(cls, expr: str) -> str:
        std = cls.standardize(expr)
        cls.validate(std)
        return std 