import re
from typing import List, Set

class LogicExpressionError(Exception):
    """Wyjątek dla błędów parsowania wyrażeń logicznych."""
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
    # Ograniczone zmienne tylko dla walidacji składni
    VALID_VARS = {'A', 'B', 'C', 'D', 'E'}  # Rozszerzono, aby przepuścić E
    VALID_CHARS = VALID_VARS | {'(', ')'} | set(OPERATORS.keys()) | set(OPERATORS.values()) | {'0', '1'}

    @classmethod
    def standardize(cls, expr: str) -> str:
        """Standaryzuje wyrażenie logiczne, usuwając spacje i zamieniając operatory."""
        expr = expr.strip().replace(' ', '')
        if not expr:
            raise LogicExpressionError("Puste wyrażenie")
        for alt, std in sorted(cls.OPERATORS.items(), key=lambda x: -len(x[0])):
            expr = expr.replace(alt, std)
        return expr

    @classmethod
    def validate(cls, expr: str) -> None:
        """Sprawdza poprawność wyrażenia logicznego."""
        if expr in {'0', '1'}:
            return
        # Sprawdza poprawność znaków
        invalid_chars = set(expr) - cls.VALID_CHARS
        if invalid_chars:
            raise LogicExpressionError(f"Nieprawidłowe znaki: {invalid_chars}")
        # Sprawdza poprawność nawiasów
        if not cls._check_parentheses(expr):
            raise LogicExpressionError("Niezamknięte lub nieprawidłowe nawiasy")
        # Sprawdza poprawność składni
        if not cls._check_syntax(expr):
            raise LogicExpressionError("Nieprawidłowa składnia wyrażenia")

    @staticmethod
    def _check_parentheses(expr: str) -> bool:
        """Sprawdza poprawność nawiasów w wyrażeniu."""
        count = 0
        for ch in expr:
            if ch == '(':
                count += 1
            elif ch == ')':
                count -= 1
            if count < 0:
                return False
        return count == 0

    @classmethod
    def _check_syntax(cls, expr: str) -> bool:
        """Sprawdza poprawność składni wyrażenia logicznego."""
        if not expr:
            return False
        prev = None
        i = 0
        while i < len(expr):
            ch = expr[i]
            if ch in cls.VALID_VARS:
                if prev in cls.VALID_VARS or prev == ')':
                    return False
            elif ch == '¬':
                if i + 1 >= len(expr) or expr[i + 1] not in cls.VALID_VARS and expr[i + 1] != '(':
                    return False
            elif ch in {'∧', '∨', '→', '↔'}:
                if prev is None or prev in {'(', '¬', '∧', '∨', '→', '↔'}:
                    return False
            elif ch == '(':
                if prev in cls.VALID_VARS or prev == ')':
                    return False
            elif ch == ')':
                if prev in {'(', '¬', '∧', '∨', '→', '↔'}:
                    return False
            prev = ch
            i += 1
        if prev in {'∧', '∨', '→', '↔'}:
            return False
        return True

    @classmethod
    def parse(cls, expr: str) -> str:
        """Parsuje wyrażenie logiczne i zwraca jego standaryzowaną formę."""
        if not expr:
            raise LogicExpressionError("Puste wyrażenie")
        std = cls.standardize(expr)
        cls.validate(std)
        return std

    def validate_and_standardize(self, expr: str) -> str:
        if not expr or not expr.strip():
            raise LogicExpressionError('Wyrażenie nie może być puste.')
        # Dopuszczalne znaki: litery, cyfry, operatory logiczne, nawiasy, spacje
        if re.search(r'[^A-Za-z0-9¬∧∨→↔()\s]', expr):
            raise LogicExpressionError('Wyrażenie zawiera niedozwolone znaki.')
        # Standaryzacja: usuwanie zbędnych spacji
        return expr.replace(' ', '')

def validate_and_standardize(expr: str) -> str:
    if not expr or not expr.strip():
        raise LogicExpressionError('Wyrażenie nie może być puste.')
    # Dopuszczalne znaki: litery, cyfry, operatory logiczne, nawiasy, spacje
    if re.search(r'[^A-Za-z0-9¬∧∨→↔()\s]', expr):
        raise LogicExpressionError('Wyrażenie zawiera niedozwolone znaki.')
    # Standaryzacja: usuwanie zbędnych spacji
    return expr.replace(' ', '')