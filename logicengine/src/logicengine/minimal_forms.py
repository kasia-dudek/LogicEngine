# minimal_forms.py
"""Compute minimal forms (DNF, CNF) – exact minimization for up to 4 vars.
DNF minimal via Quine–McCluskey + Petrick; CNF minimal by duality from ¬f.
"""

from __future__ import annotations
from typing import Dict, Any, List, Tuple, Set, Iterable, Optional

from .parser import LogicParser
from .truth_table import generate_truth_table
from .utils import to_bin


def compute_minimal_forms(expr: str) -> Dict[str, Any]:
    """
    Returns dictionary with minimal DNF and minimal CNF (not only canonical).
    For n > 4 we bail out as 'Too complex' to keep things fast and deterministic.
    """
    notes: List[str] = []

    try:
        std = LogicParser.standardize(expr)
        table = generate_truth_table(std)
        if not table:
            return _error_payload("Empty truth table (input contains no variables?)")
        vars_ = [k for k in table[0].keys() if k != "result"]
        n = len(vars_)
    except Exception as e:
        return _error_payload(f"Parsing/standardization error: {e}")

    # complexity limitation (16 rows)
    if n > 4:
        return _too_complex_payload(vars_, n)

    try:
        ones  = [i for i, r in enumerate(table) if r["result"] == 1]
        zeros = [i for i, r in enumerate(table) if r["result"] == 0]

        if not ones:
            notes.append("Contradiction → DNF=0, CNF=0.")
            dnf_expr = "0"
            cnf_expr = "0"
            dnf_terms, dnf_lits = (0, 0)
            cnf_terms, cnf_lits = (0, 0)
        elif not zeros:
            notes.append("Tautology → DNF=1, CNF=1.")
            dnf_expr = "1"
            cnf_expr = "1"
            dnf_terms, dnf_lits = (1, 0)
            cnf_terms, cnf_lits = (1, 0)
        else:
            # ---- minimal DNF via QM ----
            dnf_implicants = _qm_minimize(ones, n)  # implicants in pattern form like "1-0"
            dnf_expr = _patterns_to_dnf(dnf_implicants, vars_)
            dnf_terms, dnf_lits = _count_terms_literals_conj(dnf_expr)

            # ---- minimal CNF via dual: minimize ¬f (its DNF), then negate literals ----
            comp_implicants = _qm_minimize(zeros, n)  # implicants of g = ¬f
            cnf_expr = _comp_implicants_to_cnf(comp_implicants, vars_)
            cnf_terms, cnf_lits = _count_terms_literals_disj(cnf_expr)

        return {
            "vars": vars_,
            "dnf": {"expr": dnf_expr, "terms": dnf_terms, "literals": dnf_lits},
            "cnf": {"expr": cnf_expr, "terms": cnf_terms, "literals": cnf_lits},
            # disabled (UI placeholders)
            "anf": {"expr": "Disabled", "monomials": 0},
            "nand": {"expr": "Disabled", "gates": 0},
            "nor": {"expr": "Disabled", "gates": 0},
            "andonly": {"expr": "Disabled", "literals": 0},
            "oronly": {"expr": "Disabled", "literals": 0},
            "notes": notes,
        }
    except Exception as e:
        return _error_payload(f"Computation error: {e}")


# ----------------- Quine–McCluskey core -----------------

def _qm_minimize(minterms: List[int], nvars: int) -> List[str]:
    """
    Quine–McCluskey minimization.
    Returns a list of implicant patterns of length nvars over {'0','1','-'}.
    Uses Petrick's method to select a minimum-literal cover (then min-terms).
    """
    if not minterms:
        return []  # f == 0

    # 1) group by number of ones
    groups: Dict[int, Set[Tuple[str, frozenset[int]]]] = {}
    for m in sorted(set(minterms)):
        b = to_bin(m, nvars) if nvars else ""
        groups.setdefault(b.count("1"), set()).add((b, frozenset([m])))

    # 2) iteratively combine
    prime: Set[Tuple[str, frozenset[int]]] = set()
    while groups:
        next_groups: Dict[int, Set[Tuple[str, frozenset[int]]]] = {}
        marked: Set[Tuple[str, frozenset[int]]] = set()

        keys = sorted(groups.keys())
        for i, k in enumerate(keys[:-1]):
            for term1 in groups[k]:
                for term2 in groups[keys[i+1]]:
                    patt = _combine(term1[0], term2[0])
                    if patt is not None:
                        marked.add(term1); marked.add(term2)
                        cov = term1[1] | term2[1]
                        next_groups.setdefault(patt.count("1"), set()).add((patt, frozenset(cov)))

        # collect unmarked as primes
        for gset in groups.values():
            for t in gset:
                if t not in marked:
                    prime.add(t)

        groups = next_groups

    # 3) prime implicants set
    primes = list(prime)  # (pattern, covered_minterms)

    # 4) cover table and Petrick to find minimal set
    # essential primes
    coverage: Dict[int, List[int]] = {}
    for idx, (_, cov) in enumerate(primes):
        for m in cov:
            coverage.setdefault(m, []).append(idx)

    essential_idx: Set[int] = set()
    for m, idxs in coverage.items():
        if len(idxs) == 1:
            essential_idx.add(idxs[0])

    covered = set()
    for ei in essential_idx:
        covered |= set(primes[ei][1])

    remaining_minterms = sorted(set(minterms) - covered)

    if not remaining_minterms:
        chosen_idx = sorted(essential_idx)
    else:
        # Petrick: build sum-of-products over remaining minterms
        prod: List[Set[int]] = [set([i]) for i in coverage[remaining_minterms[0]]]
        for m in remaining_minterms[1:]:
            choices = [set([i]) for i in coverage[m]]
            prod = _petrick_multiply(prod, choices)
            prod = _petrick_absorb(prod)

        # evaluate cost: (total literals, then number of implicants)
        def cost(choice: Set[int]) -> Tuple[int, int]:
            pats = [primes[i][0] for i in choice | essential_idx]
            lits = sum(p.count("0") + p.count("1") for p in pats)
            return (lits, len(choice | essential_idx))

        best = min(prod, key=cost)
        chosen_idx = sorted(essential_idx | best)

    # return patterns
    return [primes[i][0] for i in chosen_idx]


def _combine(a: str, b: str) -> Optional[str]:
    """Combine two patterns differing in exactly one fixed bit."""
    if len(a) != len(b):
        return None
    diff = 0
    out = []
    for x, y in zip(a, b):
        if x == y:
            out.append(x)
        else:
            if x != '-' and y != '-':
                diff += 1
                out.append('-')
            else:
                return None
    return ''.join(out) if diff == 1 else None


def _petrick_multiply(P: List[Set[int]], Q: List[Set[int]]) -> List[Set[int]]:
    """Boolean multiplication on sets-of-sets."""
    res: List[Set[int]] = []
    for p in P:
        for q in Q:
            res.append(p | q)
    return res


def _petrick_absorb(sets: List[Set[int]]) -> List[Set[int]]:
    """Remove supersets (absorption)."""
    unique: List[Set[int]] = []
    for s in sets:
        if any(sup <= s for sup in sets if sup is not s):
            continue
        if not any(s == u for u in unique):
            unique.append(s)
    return unique


# ----------------- formatting & counting -----------------

def _patterns_to_dnf(patterns: List[str], vars_: List[str]) -> str:
    if not patterns:
        return "0"
    if len(vars_) == 0:
        return "1"
    terms: List[str] = []
    for p in patterns:
        lits: List[str] = []
        for i, ch in enumerate(p):
            if ch == '1':
                lits.append(vars_[i])
            elif ch == '0':
                lits.append(f"¬{vars_[i]}")
        terms.append(" ∧ ".join(lits) if lits else "1")
    return " ∨ ".join(terms)

def _comp_implicants_to_cnf(patterns: List[str], vars_: List[str]) -> str:
    """
    patterns are implicants of g=¬f (DNF). CNF(f) = ∧ (∨ ¬lit) for each implicant.
    """
    if not patterns:
        return "1"  # ¬f == 0 ⇒ f == 1
    if len(vars_) == 0:
        return "0"  # ¬f == 1 ⇒ f == 0

    clauses: List[str] = []
    for p in patterns:
        # Implicant of g is conj of some literals; negate each → disjunction for CNF
        lits: List[str] = []
        for i, ch in enumerate(p):
            if ch == '1':
                # g has Xi → clause gets ¬Xi
                lits.append(f"¬{vars_[i]}")
            elif ch == '0':
                # g has ¬Xi → clause gets Xi
                lits.append(vars_[i])
            # '-' (don't care) → brak literału w tej klauzuli
        clause = " ∨ ".join(lits) if lits else "1"
        clauses.append(clause)
    # Jeśli któraś klauzula jest "1", całe CNF staje się "1 ∧ ..." = ...
    # ale taka sytuacja nie powinna wystąpić dla sensownych implicantów.
    return " ∧ ".join(clauses) if len(clauses) > 1 else clauses[0]


def _count_terms_literals_conj(expr: str) -> Tuple[int, int]:
    if expr == "0":
        return (0, 0)
    if expr == "1":
        return (1, 0)
    terms = [t.strip() for t in expr.split("∨") if t.strip()]
    lit_count = 0
    for t in terms:
        lits = [x.strip() for x in t.split("∧") if x.strip()]
        lit_count += len(lits)
    return len(terms), lit_count

def _count_terms_literals_disj(expr: str) -> Tuple[int, int]:
    if expr == "0":
        return (0, 0)
    if expr == "1":
        return (1, 0)
    clauses = [t.strip() for t in expr.split("∧") if t.strip()]
    lit_count = 0
    for c in clauses:
        lits = [x.strip() for x in c.split("∨") if x.strip()]
        lit_count += len(lits)
    return len(clauses), lit_count


# ----------------- payload helpers -----------------

def _too_complex_payload(vars_: List[str], n: int) -> Dict[str, Any]:
    return {
        "vars": vars_,
        "dnf": {"expr": "Too complex", "terms": 0, "literals": 0},
        "cnf": {"expr": "Too complex", "terms": 0, "literals": 0},
        "anf": {"expr": "Disabled", "monomials": 0},
        "nand": {"expr": "Disabled", "gates": 0},
        "nor": {"expr": "Disabled", "gates": 0},
        "andonly": {"expr": "Disabled", "literals": 0},
        "oronly": {"expr": "Disabled", "literals": 0},
        "notes": [f"Expression has {n} variables - too complex to process"],
    }

def _error_payload(msg: str) -> Dict[str, Any]:
    return {
        "vars": [],
        "dnf": {"expr": msg, "terms": 0, "literals": 0},
        "cnf": {"expr": msg, "terms": 0, "literals": 0},
        "anf": {"expr": "Disabled", "monomials": 0},
        "nand": {"expr": "Disabled", "gates": 0},
        "nor": {"expr": "Disabled", "gates": 0},
        "andonly": {"expr": "Disabled", "literals": 0},
        "oronly": {"expr": "Disabled", "literals": 0},
        "notes": [msg],
    }
