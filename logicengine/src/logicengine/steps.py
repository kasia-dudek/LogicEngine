# steps.py
"""Step model for simplification tracking."""

from dataclasses import dataclass, field
from typing import Any, List, Literal, Optional, Dict

RuleName = Literal[
    "Eliminacja złożonych operatorów",
    "De Morgan (¬(A∧B))",
    "De Morgan (¬(A∨B))",
    "Podwójna negacja",
    "Idempotencja (∨)",
    "Idempotencja (∧)",
    "Neutralny (∨0)",
    "Neutralny (∧1)",
    "Pochłaniający (∨1)",
    "Pochłaniający (∧0)",
    "Komplementarność (∨¬X)",
    "Komplementarność (∧¬X)",
    "Pochłanianie (∨)",
    "Pochłanianie (∧)",
    "Konsensus",
    "QM: łączenie sąsiednich mintermów",
    "QM: powstanie prime implicants",
    "QM: essential PI",
    "Petrick: dystrybucja",
    "Petrick: absorpcja",
    "Formatowanie"
]


@dataclass
class Step:
    """Single step in the simplification process."""
    before_str: str                      # canonical string before step
    after_str: str                       # canonical string after step
    rule: RuleName                       # rule applied
    location: Optional[List[int]] = None  # path in AST (e.g., indices in args)
    details: Dict[str, Any] = field(default_factory=dict)  # e.g., minterm ids, masks, PI ids
    proof: Dict[str, Any] = field(default_factory=dict)   # {'method':'tt-hash','equal':bool,'hash_before':..., 'hash_after':...}

