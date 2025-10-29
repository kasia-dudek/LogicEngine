# validation.py
"""Validation and standardization for logical expressions.

Supported tokens:
- Variables:    A–Z (optionally extended to identifiers via VAR_REGEX)
- Constants:    0, 1
- Unary:        ¬, !
- Binary:       ∧, ∨, ⊕, →, ↔  and ASCII forms: &, &&, |, ||, ^, ->, <->
- Parentheses:  ( )

Whitespace is ignored.

API:
- class ValidationError(Exception)
- def validate(expr: str) -> None
- def standardize(expr: str) -> str
- def validate_and_standardize(expr: str) -> str
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Optional
import re

# ===== Public Exception =====
class ValidationError(Exception):
    """Exception raised for validation errors (with position info)."""
    def __init__(self, message: str, pos: Optional[int] = None, token: Optional[str] = None):
        if pos is not None and token is not None:
            full = f"{message} w pozycji {pos} (wokół '{token}')"
        elif pos is not None:
            full = f"{message} w pozycji {pos}"
        else:
            full = message
        super().__init__(full)
        self.pos = pos
        self.token = token

# ===== Token model =====
@dataclass(frozen=True)
class Token:
    kind: str   # 'VAR', 'CONST', 'LPAREN', 'RPAREN', 'NOT', 'BINOP'
    value: str  # raw text
    start: int  # start index in original string
    end: int    # end index (exclusive)

# Canonical operator mapping
OPERATOR_MAP = {
    # unary
    '!': '¬',
    '¬': '¬',

    # binary
    '&': '∧',  '&&': '∧',  '∧': '∧',
    '|': '∨',  '||': '∨',  '∨': '∨',
    '^': '⊕',  '⊕': '⊕',
    '↑': '↑',  '↓': '↓',
    '->': '→', '→': '→',
    '<->': '↔','↔': '↔',
    '≡': '≡',
}

# All operator lexemes (greedy match: check longer first)
OP_LEXEMES = sorted(OPERATOR_MAP.keys(), key=len, reverse=True)

# Variable regex: by default only single uppercase letters A–Z.
# If you want multi-letter identifiers, change to r'[A-Za-z][A-Za-z0-9_]*'
VAR_REGEX = r'[A-Z]'

def _is_space(ch: str) -> bool:
    return ch in (' ', '\t', '\n', '\r', '\f', '\v')

def _lex(expr: str) -> List[Token]:
    """Greedy tokenizer with whitespace skipping and precise spans."""
    tokens: List[Token] = []
    i = 0
    n = len(expr)

    while i < n:
        ch = expr[i]

        # skip whitespace
        if _is_space(ch):
            i += 1
            continue

        # parentheses
        if ch == '(':
            tokens.append(Token('LPAREN', '(', i, i+1))
            i += 1
            continue
        if ch == ')':
            tokens.append(Token('RPAREN', ')', i, i+1))
            i += 1
            continue

        # constants 0/1
        if ch in ('0', '1'):
            tokens.append(Token('CONST', ch, i, i+1))
            i += 1
            continue

        # operators (greedy, longest first)
        matched = False
        for op in OP_LEXEMES:
            if expr.startswith(op, i):
                canon = OPERATOR_MAP[op]
                kind = 'NOT' if canon == '¬' and op in ('!', '¬') else 'BINOP'
                tokens.append(Token(kind, op, i, i+len(op)))
                i += len(op)
                matched = True
                break
        if matched:
            continue

        # variables
        # try match regex at position i
        m = re.match(VAR_REGEX, expr[i:])
        if m:
            val = m.group(0)
            tokens.append(Token('VAR', val, i, i+len(val)))
            i += len(val)
            continue

        # otherwise, illegal char
        raise ValidationError("Niedozwolony znak", pos=i, token=expr[i])

    return tokens

def standardize(expr: str) -> str:
    """Return expression with all operators mapped to canonical symbols and spaces removed."""
    tokens = _lex(expr)
    out: List[str] = []
    for t in tokens:
        if t.kind == 'LPAREN' or t.kind == 'RPAREN':
            out.append(t.value)
        elif t.kind == 'CONST':
            out.append(t.value)
        elif t.kind == 'VAR':
            out.append(t.value)
        elif t.kind == 'NOT':
            out.append('¬')
        elif t.kind == 'BINOP':
            out.append(OPERATOR_MAP[t.value])
        else:
            # should never happen
            raise ValidationError("Nieznany token", pos=t.start, token=t.value)
    return ''.join(out)

def validate(expr: str) -> None:
    """Validate syntax. Raises ValidationError if invalid."""
    tokens = _lex(expr)
    if not tokens:
        raise ValidationError("Puste wyrażenie")

    EXPECT_OPERAND = 0
    EXPECT_OPERATOR = 1
    state = EXPECT_OPERAND
    depth = 0
    operand_count = 0  # number of VAR/CONST encountered
    prev_tok = None

    for t in tokens:
        if state == EXPECT_OPERAND:
            if t.kind in ('VAR', 'CONST'):
                operand_count += 1
                state = EXPECT_OPERATOR
            elif t.kind == 'LPAREN':
                depth += 1
                state = EXPECT_OPERAND
            elif t.kind == 'NOT':
                # multiple NOTs allowed before an operand
                state = EXPECT_OPERAND
            else:
                # RPAREN or BINOP here is wrong
                if t.kind == 'RPAREN':
                    raise ValidationError("Puste nawiasy lub brak operandów wewnątrz nawiasów", pos=t.start, token=t.value)
                if t.kind == 'BINOP':
                    # if it's the very first token -> starts with operator
                    if prev_tok is None:
                        raise ValidationError("Wyrażenie nie może zaczynać się operatorem", pos=t.start, token=t.value)
                    raise ValidationError("Oczekiwano operand (zmienna/stała/'(' lub '¬')", pos=t.start, token=t.value)
                raise ValidationError("Oczekiwano operand (zmienna/stała/'(' lub '¬')", pos=t.start, token=t.value)
        else:  # EXPECT_OPERATOR
            if t.kind == 'BINOP':
                # forbid two operators in a row like "A && || B"
                if prev_tok is not None and prev_tok.kind == 'BINOP':
                    raise ValidationError("Dwa operatory pod rząd", pos=t.start, token=t.value)
                state = EXPECT_OPERAND
            elif t.kind == 'RPAREN':
                depth -= 1
                if depth < 0:
                    raise ValidationError("Niezgodna liczba nawiasów", pos=t.start, token=t.value)
                state = EXPECT_OPERATOR
            elif t.kind in ('VAR', 'CONST'):
                # adjacent operands like "AA" or "1A"
                raise ValidationError("Brak operatora między operandami", pos=t.start, token=t.value)
            elif t.kind in ('LPAREN', 'NOT'):
                # missing operator before '(' or '¬'
                raise ValidationError("Brak operatora przed operandem", pos=t.start, token=t.value)
            else:
                raise ValidationError("Oczekiwano operator lub ')'", pos=t.start, token=t.value)

        prev_tok = t

    if depth != 0:
        raise ValidationError("Niezgodna liczba nawiasów")

    if state == EXPECT_OPERAND:
        raise ValidationError("Wyrażenie nie może kończyć się operatorem")

    if operand_count == 0:
        # This catches things like only parentheses "()","(())" which otherwise might have been blocked earlier,
        # but it's a clear, explicit message.
        raise ValidationError("Brak operandów w wyrażeniu")
    
    # Check if expression contains at least one variable
    has_variable = any(t.kind == 'VAR' for t in tokens)
    if not has_variable:
        raise ValidationError("Wyrażenie musi zawierać przynajmniej jedną zmienną")
def validate_and_standardize(expr: str) -> str:
    """Convenience helper used by other modules: validate then return standardized expression."""
    validate(expr)
    return standardize(expr)
