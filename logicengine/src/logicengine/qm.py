# qm.py
"""Quine–McCluskey simplification with rich, didactic step-by-step data (Polish texts for UI)."""

import logging
from typing import List, Dict, Any, Tuple
from itertools import product

from .truth_table import generate_truth_table, TruthTableError
from .utils import to_bin, bin_to_expr, count_literals

logger = logging.getLogger(__name__)


class QMError(Exception):
    pass


def _pad_bin(i: int, n: int) -> str:
    return format(i, f"0{n}b")


def simplify_qm(expr: str) -> Dict[str, Any]:
    """Simplify a logical expression via Quine–McCluskey and return steps for the UI."""
    steps: List[Dict[str, Any]] = []

    try:
        table = generate_truth_table(expr)
    except TruthTableError as e:
        logger.error(f"Błąd generowania tabeli prawdy: {e}")
        raise QMError(f"Błąd generowania tabeli prawdy: {e}")

    vars_ = [k for k in table[0] if k != "result"]
    if not vars_:
        raise QMError("Brak zmiennych w wyrażeniu.")
    if len(vars_) > 8:
        raise QMError("Obsługiwane są maksymalnie 8 zmiennych (dla większej liczby obliczenia mogą być bardzo wolne).")

    n = len(vars_)

    # Krok 1: pełna tabela prawdy “jak na kartce” + wyróżnione mintermy
    minterms = [i for i, row in enumerate(table) if row["result"]]
    zeros = [i for i, row in enumerate(table) if not row["result"]]
    rows_for_ui = [
        {
            "i": i,
            "bin": _pad_bin(i, n),
            "vals": [row[v] for v in vars_],
            "result": int(row["result"]),
        }
        for i, row in enumerate(table)
    ]
    steps.append({
        "step": "Krok 1: Tabela prawdy i mintermy",
        "data": {
            "opis": "Wypisujemy wszystkie wiersze. Zaznaczamy te z wynikiem 1 (mintermy).",
            "vars": vars_,
            "rows": rows_for_ui,
            "minterms": minterms,
            "zeros": zeros,
        },
    })

    # Szybkie przypadki brzegowe
    if not minterms:
        contradiction_expr = "0"
        steps.append({
            "step": "Krok 7: Uproszczone wyrażenie",
            "data": {"result": "0", "opis": "Wyrażenie jest sprzeczne (brak mintermów)."},
        })
        try:
            tt_orig = generate_truth_table(expr, force_vars=vars_)
            tt_simp = generate_truth_table(contradiction_expr, force_vars=vars_)
            verification = tt_orig == tt_simp
            desc = ("Tabela prawdy sprzeczności jest zgodna z oryginalną."
                    if verification else
                    "Błąd: Tabela prawdy sprzeczności różni się od oryginalnej.")
        except Exception as e:
            verification = False
            desc = f"Błąd weryfikacji: {e}"
            logger.error(f"Błąd weryfikacji sprzeczności: {e}")
        steps.append({
            "step": "Krok 8: Weryfikacja poprawności",
            "data": {"zgodność": verification, "opis": desc},
        })
        return {"result": "0", "steps": steps, "expr_for_tests": contradiction_expr}

    if len(minterms) == 2 ** n:
        tautology_expr = "1"
        steps.append({
            "step": "Krok 7: Uproszczone wyrażenie",
            "data": {"result": "1", "opis": "Wyrażenie jest tautologią (wszystkie wiersze = 1)."},
        })
        try:
            tt_orig = generate_truth_table(expr, force_vars=vars_)
            tt_simp = generate_truth_table(tautology_expr, force_vars=vars_)
            verification = tt_orig == tt_simp
            desc = ("Tabela prawdy tautologii jest zgodna z oryginalną."
                    if verification else
                    "Błąd: Tabela prawdy tautologii różni się od oryginalnej.")
        except Exception as e:
            verification = False
            desc = f"Błąd weryfikacji: {e}"
            logger.error(f"Błąd weryfikacji tautologii: {e}")
        steps.append({
            "step": "Krok 8: Weryfikacja poprawności",
            "data": {"zgodność": verification, "opis": desc},
        })
        return {"result": "1", "steps": steps, "expr_for_tests": tautology_expr}

    # Krok 2: grupowanie mintermów (liczba jedynek)
    groups: Dict[int, List[str]] = {}
    for m in minterms:
        b = to_bin(m, n)
        groups.setdefault(b.count("1"), []).append(b)
    steps.append({
        "step": "Krok 2: Grupowanie mintermów według liczby jedynek",
        "data": {
            "opis": "Grupujemy indeksy według liczby jedynek w zapisie binarnym.",
            "groups": {k: sorted(v) for k, v in groups.items()},
        },
    })

    # Krok 3: budowa PI — pokaż parowania “jak na kartce”
    all_prime_implicants: List[Tuple[str, List[int]]] = []
    current: List[Tuple[str, List[int]]] = [(to_bin(m, n), [m]) for m in minterms]
    combine_steps: List[Dict[str, Any]] = []
    seen = set()

    while current:
        next_round: List[Tuple[str, List[int]]] = []
        marked = set()
        pairs = []

        for i in range(len(current)):
            for j in range(i + 1, len(current)):
                b1, ms1 = current[i]
                b2, ms2 = current[j]
                diff = [a != b for a, b in zip(b1, b2)]
                if sum(diff) == 1:
                    idx = diff.index(True)
                    combined = list(b1)
                    combined[idx] = "-"
                    combined_s = "".join(combined)
                    merged_ms = sorted(set(ms1 + ms2))
                    key = (combined_s, tuple(merged_ms))
                    if key not in marked:
                        next_round.append((combined_s, merged_ms))
                        marked.add(key)
                    pairs.append({
                        "from": [b1, b2],
                        "to": combined_s,
                        "minterms": merged_ms
                    })

        combine_steps.append({
            "round": len(combine_steps) + 1,
            "pairs": pairs,
            "next": next_round,
        })

        for b, ms in current:
            if not any(set(ms).issubset(set(nr[1])) for nr in next_round):
                key = (b, tuple(sorted(ms)))
                if key not in seen:
                    all_prime_implicants.append((b, ms))
                    seen.add(key)

        current = next_round
        if not next_round:
            break

    # Deduplicate PI
    unique_prime = {b: ms for b, ms in all_prime_implicants}
    all_prime_implicants = list(unique_prime.items())

    steps.append({
        "step": "Krok 3: Wyznaczanie implikantów pierwszorzędnych",
        "data": {
            "opis": "Łączymy mintermy różniące się jedną pozycją. Z wyników, których nie da się już połączyć, powstają PI.",
            "rounds": combine_steps,  # do pokazywania “parowani”
            "prime_implicants": [
                {"binary": b, "minterms": ms, "expr": bin_to_expr(b, vars_)}
                for b, ms in all_prime_implicants
            ],
        },
    })

    # Krok 4: tabela pokrycia
    cover: Dict[int, List[str]] = {}
    for b, ms in all_prime_implicants:
        for m in ms:
            cover.setdefault(m, []).append(b)
    steps.append({
        "step": "Krok 4: Tabela pokrycia",
        "data": {
            "opis": "Zaznaczamy, które PI pokrywają który minterm.",
            "cover": {str(k): sorted(v) for k, v in cover.items()},
        },
    })

    # Krok 5: implikanty istotne
    essential = set()
    covered = set()
    for m, bs in cover.items():
        if len(bs) == 1:
            essential.add(bs[0])
            covered.add(m)
    steps.append({
        "step": "Krok 5: Implikanty istotne",
        "data": {
            "opis": "PI, które są jedynym pokryciem pewnych mintermów, wybieramy od razu.",
            "essential": sorted(essential),
            "covered_minterms": sorted(covered),
        },
    })

    # Krok 6: dobór reszty (Petrick) z przejrzystą selekcją
    remaining = set(minterms) - covered
    min_cover = list(essential)

    if remaining:
        minterm_to_pis = [[b for b, ms in all_prime_implicants if m in ms] for m in remaining]
        if minterm_to_pis:
            # Build symbolic Petrick formula for logging
            petrick_formula = " ∏ ".join([f"({' + '.join(pis)})" for pis in minterm_to_pis])
            
            # Add Petrick: dystrybucja step
            steps.append({
                "step": "Petrick: dystrybucja",
                "data": {
                    "opis": f"Formuła Petricka: {petrick_formula}",
                    "remaining_minterms": sorted(remaining),
                    "pi_choices": minterm_to_pis,
                },
            })
            
            all_combos = list(product(*minterm_to_pis))
            best_combo = None
            best_len = float("inf")
            best_literals = float("inf")
            absorption_count = 0

            for combo in all_combos:
                combo_set = set(combo)

                # Czy combo + essential pokrywa wszystko?
                covered_minterms = set()
                for b in combo_set.union(min_cover):
                    for b2, ms in all_prime_implicants:
                        if b == b2:
                            covered_minterms.update(ms)
                if covered_minterms != set(minterms):
                    continue

                # Tie-break: najpierw liczba PI, potem liczba literałów (po wzorcu, nie po tekście)
                lits = sum(count_literals(b) for b in combo_set)
                if len(combo_set) < best_len or (len(combo_set) == best_len and lits < best_literals):
                    best_combo = combo_set
                    best_len = len(combo_set)
                    best_literals = lits

            if best_combo:
                min_cover.extend(best_combo)
                
                # Add Petrick: absorpcja step if we found a simplified combo
                if best_combo and len(best_combo) < len(all_combos):
                    steps.append({
                        "step": "Petrick: absorpcja",
                        "data": {
                            "opis": f"Wybrano minimalne pokrycie: {', '.join(sorted(best_combo))}",
                            "selected_pis": sorted(best_combo),
                        },
                    })

    min_cover = sorted(set(min_cover))
    steps.append({
        "step": "Krok 6: Minimalne pokrycie (metoda Petricka)",
        "data": {
            "opis": "Dobieramy najmniejszy zestaw PI, który domyka pokrycie wszystkich mintermów.",
            "cover": [{"binary": b, "expr": bin_to_expr(b, vars_)} for b in min_cover],
        },
    })

    # Krok 7: wynik
    simplified = " ∨ ".join(bin_to_expr(b, vars_) for b in min_cover) if min_cover else "0"
    steps.append({
        "step": "Krok 7: Uproszczone wyrażenie",
        "data": {"result": simplified, "opis": "Suma wybranych PI daje zminimalizowaną postać DNF."},
    })

    # Krok 8: weryfikacja
    try:
        tt_orig = generate_truth_table(expr, force_vars=vars_)
        tt_simp = generate_truth_table(simplified if simplified != "0" else "0", force_vars=vars_)
        verification = tt_orig == tt_simp
        verification_desc = ("Tabela prawdy uproszczonego wyrażenia jest identyczna z oryginalną."
                             if verification else
                             "Błąd: Tabela prawdy uproszczonego wyrażenia różni się od oryginalnej.")
    except Exception as e:
        verification = False
        verification_desc = f"Błąd weryfikacji: {e}"
        logger.error(f"Błąd weryfikacji: {e}")

    steps.append({
        "step": "Krok 8: Weryfikacja poprawności",
        "data": {"zgodność": verification, "opis": verification_desc},
    })

    # Build summary
    all_pi_masks = [b for b, _ in all_prime_implicants]
    
    # Build merge_edges for derivation builder (only for selected PI)
    merge_edges = []
    for round_data in combine_steps:
        for pair in round_data.get("pairs", []):
            left_mask = pair["from"][0]
            right_mask = pair["from"][1]
            result_mask = pair["to"]
            # Only include if result_mask is in selected PI
            if result_mask in min_cover:
                merge_edges.append((left_mask, right_mask, result_mask))
    
    # Build pi_to_minterms map
    pi_to_minterms = {b: ms for b, ms in all_prime_implicants}
    
    summary = {
        "dnf_terms": len(min_cover),
        "dnf_literals": sum(count_literals(b) for b in min_cover),
        "essential": list(essential),
        "selected_pi": min_cover,
        "all_pi": all_pi_masks,
        "minterms_1": minterms,
        "merge_edges": merge_edges,
        "pi_to_minterms": pi_to_minterms
    }

    return {"result": simplified, "steps": steps, "expr_for_tests": simplified, "tt_equal": verification, "summary": summary}
