# steps.py
"""Step model for simplification tracking."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Literal, Optional, Dict, Tuple

__all__ = ["RuleName", "Step", "StepCategory"]

RuleName = Literal[
    "Eliminacja złożonych operatorów",
    "De Morgan (¬(A∧B))",
    "De Morgan (¬(A∨B))",
    "Podwójna negacja",
    "Idempotentność (∨)",
    "Idempotentność (∧)",
    "Element neutralny (A∨0)",
    "Element neutralny (A∧1)",
    "Element pochłaniający (A∨1)",
    "Element pochłaniający (A∧0)",
    "Kontradykcja (A ∧ ¬A)",
    "Dopełnienie (A ∨ ¬A)",
    "Absorpcja (∨)",
    "Absorpcja (∧)",
    "Absorpcja z negacją",
    "Absorpcja z negacją (dual)",
    "Komplementarność (∨¬X)",
    "Komplementarność (∧¬X)",
    "Pochłanianie (∨)",
    "Pochłanianie (∧)",
    "Kontradykcja",
    "Konsensus",
    "Dystrybutywność (A∨B)∧C",
    "Dystrybutywność A∧(B∨C)",
    "Rozdzielność (faktoryzacja)",
    "Element neutralny",
    "QM: łączenie sąsiednich mintermów",
    "QM: powstanie prime implicants",
    "QM: essential PI",
    "Petrick: dystrybucja",
    "Petrick: absorpcja",
    "Zweryfikowano minimalność (QM)",
    "Dowód równoważności (TT)",
    "Certyfikat minimalności (QM)",
    "Formatowanie"
]

StepCategory = Literal["user", "proof", "formatting"]


@dataclass
class Step:
    """Single step in the simplification process."""
    before_str: str                      # canonical string before step
    after_str: str                       # canonical string after step
    rule: RuleName                       # rule applied
    category: StepCategory = "user"      # user (visible), proof (hidden by default), formatting
    schema: Optional[str] = None         # presentation of rule, e.g. "X↔Y ≡ (X∧Y)∨(¬X∧¬Y)"
    substitution: Optional[Dict[str, str]] = None  # mapping symbols to substituted subexpressions
    location: Optional[List[int]] = None  # path in AST (e.g., indices in args)
    details: Dict[str, Any] = field(default_factory=dict)  # e.g., minterm ids, masks, PI ids
    proof: Dict[str, Any] = field(default_factory=dict)   # {'method':'tt-hash','equal':bool,'hash_before':..., 'hash_after':...}
    before_subexpr: Optional[str] = None  # highlighted fragment before (for UI)
    after_subexpr: Optional[str] = None   # highlighted fragment after (for UI)
    before_canon: Optional[str] = None      # canonical full expression before
    after_canon: Optional[str] = None       # canonical full expression after
    before_subexpr_canon: Optional[str] = None  # canonical highlighted fragment before
    after_subexpr_canon: Optional[str] = None   # canonical highlighted fragment after
    # DEPRECATED - kept for backward compatibility only
    before_span: Optional[Dict[str, int]] = None
    after_span: Optional[Dict[str, int]] = None
    before_highlight_span: Optional[Dict[str, int]] = None
    after_highlight_span: Optional[Dict[str, int]] = None
    before_highlight_spans: Optional[List[Dict[str, int]]] = None
    
    # NEW - preferred: code-point spans relative to before_str/after_str
    before_highlight_spans_cp: Optional[List[Tuple[int, int]]] = None  # [(start, end), ...] relative to before_str (code-points, NEW - preferred)
    after_highlight_spans_cp: Optional[List[Tuple[int, int]]] = None   # [(start, end), ...] relative to after_str (code-points, NEW - preferred)
    before_focus_texts: Optional[List[str]] = None  # extracted texts from before_canon[start:end] (code-points)
    after_focus_texts: Optional[List[str]] = None   # extracted texts from after_canon[start:end] (code-points)

