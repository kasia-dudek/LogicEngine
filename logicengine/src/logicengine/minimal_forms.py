# minimal_forms.py
"""Compute minimal forms (DNF, CNF, ANF, NAND-only, NOR-only, AND-only, OR-only)."""

from __future__ import annotations
from typing import Dict, Any, List, Tuple
import re

from .parser import LogicParser
from .truth_table import generate_truth_table
from .utils import to_bin


def compute_minimal_forms(expr: str) -> Dict[str, Any]:
    """
    Zwraca słownik z postaciami: DNF, CNF, ANF oraz transformacjami NAND/NOR/AND-only/OR-only.
    Używa TEJ SAMEJ standaryzacji co reszta aplikacji (parser.standardize).
    """
    notes: List[str] = []

    try:
        # Używamy standardowej standaryzacji
        working_expr = LogicParser.standardize(expr)
        table = generate_truth_table(working_expr)
        vars_ = [k for k in table[0].keys() if k != "result"]
        n = len(vars_)
    except Exception as e:
        return _error_payload(f"Błąd parsowania/standaryzacji: {e}")

    # proste ograniczenie złożoności (spójne z UX) - zmniejszamy limit dla szybszego działania
    if n > 4:
        return {
            "vars": vars_,
            "dnf": {"expr": "Zbyt złożone", "terms": 0, "literals": 0},
            "cnf": {"expr": "Zbyt złożone", "terms": 0, "literals": 0},
            "anf": {"expr": "Zbyt złożone", "monomials": 0},
            "nand": {"expr": "Zbyt złożone", "gates": 0},
            "nor": {"expr": "Zbyt złożone", "gates": 0},
            "andonly": {"expr": "Zbyt złożone", "literals": 0},
            "oronly": {"expr": "Zbyt złożone", "literals": 0},
            "notes": [f"Wyrażenie ma {n} zmiennych - zbyt złożone do przetworzenia"],
        }

    try:
        ones  = [i for i, r in enumerate(table) if r["result"] == 1]
        zeros = [i for i, r in enumerate(table) if r["result"] == 0]

        if not ones:
            notes.append("Sprzeczność → wszystkie formy = 0")
        elif not zeros:
            notes.append("Tautologia → wszystkie formy = 1")
        if n > 4:
            notes.append(f"Uwaga: {n} zmiennych - formy mogą być złożone")

        # DNF = suma mintermów (prosta, czytelna postać)
        dnf_expr = _min_sop(ones, vars_) if ones else "0"
        dnf_terms, dnf_lits = _count_terms_literals_conj(dnf_expr)

        # CNF = z zerów przez De Morgana
        cnf_expr = _sop_zeros_to_cnf(zeros, vars_) if zeros else "1"
        cnf_terms, cnf_lits = _count_terms_literals_disj(cnf_expr)

        # ANF (algebra Z2): szybka transformata Möbiusa po tabeli prawdy - pomijamy dla większych wyrażeń
        if n > 3:
            anf_expr, anf_monos = "Zbyt złożone (ANF)", 0
        else:
            anf_expr, anf_monos = _truth_to_anf(table, vars_)

        # Postaci “tylko AND / tylko OR” (z De Morganem)
        and_only = _to_and_only(cnf_expr)
        or_only  = _to_or_only(dnf_expr)

        # NAND-only / NOR-only
        nand_expr, nand_cnt = _to_nand_only(and_only)
        nor_expr,  nor_cnt  = _to_nor_only(or_only)

        return {
            "vars": vars_,
            "dnf":     {"expr": dnf_expr,  "terms": dnf_terms, "literals": dnf_lits},
            "cnf":     {"expr": cnf_expr,  "terms": cnf_terms, "literals": cnf_lits},
            "anf":     {"expr": anf_expr,  "monomials": anf_monos},
            "nand":    {"expr": nand_expr, "gates": nand_cnt},
            "nor":     {"expr": nor_expr,  "gates": nor_cnt},
            "andonly": {"expr": and_only,  "literals": _count_literals(and_only)},
            "oronly":  {"expr": or_only,   "literals": _count_literals(or_only)},
            "notes": notes,
        }
    except Exception as e:
        return _error_payload(f"Błąd obliczeń: {e}")


# ----------------- helpers -----------------

def _error_payload(msg: str) -> Dict[str, Any]:
    return {
        "vars": [],
        "dnf": {"expr": msg, "terms": 0, "literals": 0},
        "cnf": {"expr": msg, "terms": 0, "literals": 0},
        "anf": {"expr": msg, "monomials": 0},
        "nand": {"expr": msg, "gates": 0},
        "nor": {"expr": msg, "gates": 0},
        "andonly": {"expr": msg, "literals": 0},
        "oronly": {"expr": msg, "literals": 0},
        "notes": [msg],
    }


def _min_sop(minterms: List[int], vars_: List[str]) -> str:
    """SOP (sum of minterms) wprost z indeksów – czytelna, spójna składnia."""
    if not minterms:
        return "0"
    n = len(vars_)
    terms: List[str] = []
    for m in minterms:
        b = to_bin(m, n)
        part = []
        for i, bit in enumerate(b):
            part.append(vars_[i] if bit == "1" else f"¬{vars_[i]}")
        terms.append(" ∧ ".join(part) if part else "1")
    return " ∨ ".join(terms) if terms else "0"


def _count_terms_literals_conj(expr: str) -> Tuple[int, int]:
    """Zlicza składniki i literały w DNF (suma iloczynów)."""
    if expr in {"0", "1"}:
        return (0, 0) if expr == "0" else (1, 0)
    terms = [t.strip() for t in expr.split("∨")]
    lit_count = 0
    for t in terms:
        if not t:
            continue
        lits = [x.strip() for x in t.split("∧") if x.strip()]
        lit_count += len(lits)
    return len(terms), lit_count


def _count_terms_literals_disj(expr: str) -> Tuple[int, int]:
    """Zlicza składniki i literały w CNF (iloczyn sum)."""
    if expr in {"0", "1"}:
        return (1, 0) if expr == "1" else (0, 0)
    terms = [t.strip() for t in expr.split("∧")]
    lit_count = 0
    for t in terms:
        if not t:
            continue
        lits = [x.strip() for x in t.split("∨") if x.strip()]
        lit_count += len(lits)
    return len(terms), lit_count


def _sop_zeros_to_cnf(zeros: List[int], vars_: List[str]) -> str:
    """CNF z indeksów zerowych przez zanegowanie SOP(zera)."""
    if not zeros:
        return "1"
    sop_g = _min_sop(zeros, vars_)
    if sop_g == "0":
        return "1"
    # De Morgan: f = ¬g;  g = ∨(∧l_i)  =>  f = ∧(∨¬l_i)
    terms = [t.strip() for t in sop_g.split("∨")] if "∨" in sop_g else [sop_g.strip()]
    cnf_terms = []
    for term in terms:
        if "∧" in term:
            lits = [x.strip() for x in term.split("∧")]
            neg = [x[1:] if x.startswith("¬") else f"¬{x}" for x in lits]
            cnf_terms.append(" ".join([" ∨ ".join(neg)]))
        else:
            cnf_terms.append(term[1:] if term.startswith("¬") else f"¬{term}")
    return cnf_terms[0] if len(cnf_terms) == 1 else " ∧ ".join(cnf_terms)


def _truth_to_anf(table: List[Dict[str, Any]], vars_: List[str]) -> Tuple[str, int]:
    """ANF (XOR-suma iloczynów) wyliczana z tabeli prawdy."""
    n = len(vars_)
    if n == 0:
        return "0", 0
    f = [row["result"] for row in table]
    a = f[:]
    for i in range(n):
        step = 1 << i
        for mask in range(1 << n):
            if mask & step:
                a[mask] ^= a[mask ^ step]
    monos = []
    for mask in range(1 << n):
        if a[mask] == 1:
            if mask == 0:
                monos.append("1")
            else:
                parts = [vars_[i] for i in range(n) if mask & (1 << i)]
                monos.append(" ∧ ".join(parts))
    if not monos:
        return "0", 0
    if len(monos) == 1 and monos[0] == "1":
        return "1", 1
    return " ⊕ ".join(monos), len(monos)


def _to_and_only(cnf_expr: str) -> str:
    """Tylko ∧ i ¬ (bez ∨) – przez De Morgana na poziomie klauzul CNF."""
    if cnf_expr in {"0", "1"}:
        return cnf_expr
    terms = [t.strip() for t in cnf_expr.split("∧")] if "∧" in cnf_expr else [cnf_expr.strip()]
    out: List[str] = []
    for t in terms:
        if "∨" in t:
            lits = [x.strip() for x in t.split("∨")]
            neg = [x[1:] if x.startswith("¬") else f"¬{x}" for x in lits]
            out.append(f"¬({' ∧ '.join(neg)})")
        else:
            out.append(t)
    return out[0] if len(out) == 1 else " ∧ ".join(out)


def _to_or_only(dnf_expr: str) -> str:
    """Tylko ∨ i ¬ (bez ∧) – przez De Morgana na poziomie składników DNF."""
    if dnf_expr in {"0", "1"}:
        return dnf_expr
    terms = [t.strip() for t in dnf_expr.split("∨")] if "∨" in dnf_expr else [dnf_expr.strip()]
    out: List[str] = []
    for t in terms:
        if "∧" in t:
            lits = [x.strip() for x in t.split("∧")]
            neg = [x[1:] if x.startswith("¬") else f"¬{x}" for x in lits]
            out.append(f"¬({' ∨ '.join(neg)})")
        else:
            out.append(t)
    return out[0] if len(out) == 1 else " ∨ ".join(out)


def _to_nand_only(and_only: str) -> Tuple[str, int]:
    """Budowa z samych NAND (⊼)."""
    if and_only in {"0", "1"}:
        return and_only, 0
    expr = and_only

    # ¬X  → (X ⊼ X)
    expr = re.sub(r"(?<![A-Z])¬\s*([A-Z])", r"(\1 ⊼ \1)", expr)

    # (X ∧ Y) → (X ⊼ Y) ⊼ (X ⊼ Y)  – iteracyjnie
    while "∧" in expr:
        expr = re.sub(r"(\([^()]+\)|[A-Z])\s*∧\s*(\([^()]+\)|[A-Z])",
                      r"(\1 ⊼ \2) ⊼ (\1 ⊼ \2)", expr, count=1)
    return expr, expr.count("⊼")


def _to_nor_only(or_only: str) -> Tuple[str, int]:
    """Budowa z samych NOR (⊽)."""
    if or_only in {"0", "1"}:
        return or_only, 0
    expr = or_only

    # ¬X  → (X ⊽ X)
    expr = re.sub(r"(?<![A-Z])¬\s*([A-Z])", r"(\1 ⊽ \1)", expr)

    # (X ∨ Y) → (X ⊽ Y) ⊽ (X ⊽ Y)
    while "∨" in expr:
        expr = re.sub(r"(\([^()]+\)|[A-Z])\s*∨\s*(\([^()]+\)|[A-Z])",
                      r"(\1 ⊽ \2) ⊽ (\1 ⊽ \2)", expr, count=1)
    return expr, expr.count("⊽")


def _count_literals(expr: str) -> int:
    if expr in {"0", "1"}:
        return 0
    # liczymy literały w najprostszej formie: X lub ¬X
    tokens = re.findall(r"¬?\s*[A-Z]", expr)
    return len(tokens)
