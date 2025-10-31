# rules.py

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union


@dataclass(frozen=True)
class Var:
    name: str


@dataclass(frozen=True)
class Pattern:
    op: str  # 'AND' | 'OR' | 'NOT' | 'VAR' | 'CONST'
    args: List[Union["Pattern", Var, str, int]]


@dataclass(frozen=True)
class Rule:
    id: str
    name: str
    lhs: Pattern
    rhs: Union[Pattern, Var]
    side_conditions: List[Any]


def VAR(name: str) -> Var:
    return Var(name)


def P(op: str, *args: Union[Pattern, Var, str, int]) -> Pattern:
    return Pattern(op, list(args))


R_IDEM_OR = Rule(
    id="idempotency_or",
    name="Idempotentność (∨)",
    lhs=P("OR", VAR("X"), VAR("X")),
    rhs=VAR("X"),
    side_conditions=[],
)

R_IDEM_AND = Rule(
    id="idempotency_and",
    name="Idempotentność (∧)",
    lhs=P("AND", VAR("X"), VAR("X")),
    rhs=VAR("X"),
    side_conditions=[],
)

R_NEU_OR_0 = Rule(
    id="neutral_or_0",
    name="Element neutralny (∨0)",
    lhs=P("OR", VAR("X"), P("CONST", 0)),
    rhs=VAR("X"),
    side_conditions=[],
)

R_NEU_AND_1 = Rule(
    id="neutral_and_1",
    name="Element neutralny (∧1)",
    lhs=P("AND", VAR("X"), P("CONST", 1)),
    rhs=VAR("X"),
    side_conditions=[],
)

R_ABSORB_OR_1 = Rule(
    id="absorbing_or_1",
    name="Element pochłaniający (∨1)",
    lhs=P("OR", VAR("X"), P("CONST", 1)),
    rhs=P("CONST", 1),
    side_conditions=[],
)

R_ABSORB_AND_0 = Rule(
    id="absorbing_and_0",
    name="Element pochłaniający (∧0)",
    lhs=P("AND", VAR("X"), P("CONST", 0)),
    rhs=P("CONST", 0),
    side_conditions=[],
)

R_COMP_OR = Rule(
    id="complement_or",
    name="Dopełnienie (X ∨ ¬X)",
    lhs=P("OR", VAR("X"), P("NOT", VAR("X"))),
    rhs=P("CONST", 1),
    side_conditions=[],
)

R_COMP_AND = Rule(
    id="complement_and",
    name="Dopełnienie (X ∧ ¬X)",
    lhs=P("AND", VAR("X"), P("NOT", VAR("X"))),
    rhs=P("CONST", 0),
    side_conditions=[],
)

R_DNEG = Rule(
    id="double_not",
    name="Podwójna negacja",
    lhs=P("NOT", P("NOT", VAR("X"))),
    rhs=VAR("X"),
    side_conditions=[],
)

R_DM_OR = Rule(
    id="demorgan_or",
    name="De Morgan: ¬(A ∨ B) → ¬A ∧ ¬B",
    lhs=P("NOT", P("OR", VAR("A"), VAR("B"))),
    rhs=P("AND", P("NOT", VAR("A")), P("NOT", VAR("B"))),
    side_conditions=[],
)

R_DM_AND = Rule(
    id="demorgan_and",
    name="De Morgan: ¬(A ∧ B) → ¬A ∨ ¬B",
    lhs=P("NOT", P("AND", VAR("A"), VAR("B"))),
    rhs=P("OR", P("NOT", VAR("A")), P("NOT", VAR("B"))),
    side_conditions=[],
)

R_ABS_OR = Rule(
    id="absorption_or",
    name="Absorpcja (∨)",
    lhs=P("OR", VAR("X"), P("AND", VAR("X"), VAR("Y"))),
    rhs=VAR("X"),
    side_conditions=[],
)

R_ABS_AND = Rule(
    id="absorption_and",
    name="Absorpcja (∧)",
    lhs=P("AND", VAR("X"), P("OR", VAR("X"), VAR("Y"))),
    rhs=VAR("X"),
    side_conditions=[],
)

# Factoring rules: XY ∨ X¬Y ⇒ X(Y ∨ ¬Y)
R_FACTOR_OR_1 = Rule(
    id="factor_or_1",
    name="Rozdzielność (faktoryzacja)",
    lhs=P("OR", 
           P("AND", VAR("X"), VAR("Y")),
           P("AND", VAR("X"), P("NOT", VAR("Y")))),
    rhs=P("AND", VAR("X"), P("OR", VAR("Y"), P("NOT", VAR("Y")))),
    side_conditions=[],
)

R_FACTOR_OR_2 = Rule(
    id="factor_or_2",
    name="Rozdzielność (faktoryzacja)",
    lhs=P("OR",
           P("AND", VAR("X"), P("NOT", VAR("Y"))),
           P("AND", VAR("X"), VAR("Y"))),
    rhs=P("AND", VAR("X"), P("OR", P("NOT", VAR("Y")), VAR("Y"))),
    side_conditions=[],
)

LIST_OF_RULES: List[Rule] = [
    R_IDEM_OR,
    R_IDEM_AND,
    R_NEU_OR_0,
    R_NEU_AND_1,
    R_ABSORB_OR_1,
    R_ABSORB_AND_0,
    R_COMP_OR,
    R_COMP_AND,
    R_DNEG,
    R_DM_OR,
    R_DM_AND,
    R_ABS_OR,
    R_ABS_AND,
    R_FACTOR_OR_1,
    R_FACTOR_OR_2,
]
