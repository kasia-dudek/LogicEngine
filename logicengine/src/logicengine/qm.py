import logging
from typing import List, Dict, Any, Set, Tuple
from itertools import product
from .parser import LogicParser, LogicExpressionError
from .truth_table import generate_truth_table, TruthTableError
from .utils import to_bin, bin_to_expr, count_literals

logger = logging.getLogger(__name__)

class QMError(Exception):
    """Wyjątek dla błędów algorytmu Quine'a-McCluskeya."""
    pass

def simplify_qm(expr: str) -> Dict[str, Any]:
    """Upraszcza wyrażenie logiczne za pomocą algorytmu Quine'a-McCluskeya."""
    steps = []
    try:
        parsed_expr = LogicParser.parse(expr)
        table = generate_truth_table(expr)
    except LogicExpressionError as e:
        logger.error(f"Błąd parsowania: {e}")
        raise
    except TruthTableError as e:
        logger.error(f"Błąd generowania tabeli prawdy: {e}")
        raise QMError(f"Błąd generowania tabeli prawdy: {e}")

    vars = [k for k in table[0] if k != 'result']
    if not vars:
        raise QMError("Brak zmiennych w wyrażeniu.")
    if len(vars) > 4:
        raise QMError("Obsługiwane są maksymalnie 4 zmienne.")

    minterms = [i for i, row in enumerate(table) if row['result']]
    steps.append({
        "step": "Krok 1: Znajdź mintermy",
        "data": {
            "minterms": minterms,
            "opis": "Indeksy wierszy tabeli prawdy, gdzie wyrażenie jest prawdziwe (wynik = 1)."
        }
    })

    if not minterms:
        contradiction_expr = ' ∧ '.join([f'{v} ∧ ¬{v}' for v in vars]) if vars else '0'
        steps.append({
            "step": "Krok 2: Sprzeczność",
            "data": {
                "result": "0",
                "opis": "Wyrażenie jest zawsze fałszywe (brak mintermów).",
                "expr_for_tests": contradiction_expr
            }
        })
        steps.append({
            "step": "Krok 7: Uproszczone wyrażenie",
            "data": {
                "result": "0",
                "opis": "Końcowe wyrażenie logiczne: sprzeczność."
            }
        })
        try:
            tt_orig = generate_truth_table(expr, force_vars=vars)
            tt_simp = generate_truth_table(contradiction_expr, force_vars=vars)
            verification = tt_orig == tt_simp
            verification_desc = "Tabela prawdy sprzeczności jest zgodna z oryginalną." if verification else "Błąd: Tabela prawdy sprzeczności różni się od oryginalnej."
        except Exception as e:
            verification = False
            verification_desc = f"Błąd weryfikacji: {e}"
            logger.error(f"Błąd weryfikacji sprzeczności: {e}")
        steps.append({
            "step": "Krok 8: Weryfikacja poprawności",
            "data": {
                "zgodność": verification,
                "opis": verification_desc
            }
        })
        return {"result": "0", "steps": steps, "expr_for_tests": contradiction_expr}

    if len(minterms) == 2**len(vars):
        tautology_expr = ' ∨ '.join([f'{v} ∨ ¬{v}' for v in vars]) if vars else '1'
        steps.append({
            "step": "Krok 2: Tautologia",
            "data": {
                "result": "1",
                "opis": "Wyrażenie jest zawsze prawdziwe (wszystkie kombinacje są mintermami).",
                "expr_for_tests": tautology_expr
            }
        })
        steps.append({
            "step": "Krok 7: Uproszczone wyrażenie",
            "data": {
                "result": "1",
                "opis": "Końcowe wyrażenie logiczne: tautologia."
            }
        })
        try:
            tt_orig = generate_truth_table(expr, force_vars=vars)
            tt_simp = generate_truth_table(tautology_expr, force_vars=vars)
            verification = tt_orig == tt_simp
            verification_desc = "Tabela prawdy tautologii jest zgodna z oryginalną." if verification else "Błąd: Tabela prawdy tautologii różni się od oryginalnej."
        except Exception as e:
            verification = False
            verification_desc = f"Błąd weryfikacji: {e}"
            logger.error(f"Błąd weryfikacji tautologii: {e}")
        steps.append({
            "step": "Krok 8: Weryfikacja poprawności",
            "data": {
                "zgodność": verification,
                "opis": verification_desc
            }
        })
        return {"result": "1", "steps": steps, "expr_for_tests": tautology_expr}

    groups = {}
    for m in minterms:
        binary = to_bin(m, len(vars))
        ones = binary.count('1')
        groups.setdefault(ones, []).append(binary)
    steps.append({
        "step": "Krok 2: Grupowanie mintermów według liczby jedynek",
        "data": {
            "groups": {k: sorted(v) for k, v in groups.items()},
            "opis": "Mintermy są grupowane według liczby jedynek w ich binarnym zapisie."
        }
    })

    all_prime_implicants: List[Tuple[str, List[int]]] = []
    current = [(to_bin(m, len(vars)), [m]) for m in minterms]
    combine_steps = []
    seen = set()

    while current:
        next_round = []
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
                    combined[idx] = '-'
                    combined = ''.join(combined)
                    merged_ms = sorted(set(ms1 + ms2))
                    key = (combined, tuple(merged_ms))
                    if key not in marked:
                        next_round.append((combined, merged_ms))
                        marked.add(key)
                    pairs.append({"from": [b1, b2], "to": combined, "minterms": merged_ms})

        combine_steps.append({
            "round": len(combine_steps) + 1,
            "pairs": pairs,
            "next": next_round
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

    unique_prime = dict((b, ms) for b, ms in all_prime_implicants)
    all_prime_implicants = list(unique_prime.items())
    steps.append({
        "step": "Krok 3: Wyznaczanie implikantów pierwszorzędnych",
        "data": {
            "rounds": combine_steps,
            "prime_implicants": [
                {"binary": b, "minterms": ms, "expr": bin_to_expr(b, vars)}
                for b, ms in all_prime_implicants
            ],
            "opis": "Iteracyjne łączenie mintermów w celu znalezienia wszystkich implikantów pierwszorzędnych."
        }
    })
    # logger.info(f"Prime implicants: {all_prime_implicants}")

    table_cover: Dict[int, List[str]] = {}
    for b, ms in all_prime_implicants:
        for m in ms:
            table_cover.setdefault(m, []).append(b)
    steps.append({
        "step": "Krok 4: Tabela pokrycia",
        "data": {
            "cover": {str(k): sorted(v) for k, v in table_cover.items()},
            "opis": "Pokazuje, które implikanty pierwszorzędne pokrywają każdy minterm."
        }
    })

    essential = set()
    covered = set()
    for m, bs in table_cover.items():
        if len(bs) == 1:
            essential.add(bs[0])
            covered.add(m)
    steps.append({
        "step": "Krok 5: Zasada implikanty",
        "data": {
            "essential": sorted(essential),
            "covered_minterms": sorted(covered),
            "opis": "Implikanty pierwszorzędne pokrywające mintermy, które nie są pokrywane przez inne PI."
        }
    })

    remaining = set(minterms) - covered
    min_cover = list(essential)

    if remaining:
        minterm_to_pis = [[b for b, ms in all_prime_implicants if m in ms] for m in remaining]
        if not minterm_to_pis:
            # logger.warning("Brak dodatkowych implikantów dla pozostałych mintermów.")
            pass
        else:
            all_combos = list(product(*minterm_to_pis))
            best_combo = None
            best_len = float('inf')
            best_literals = float('inf')
            orig_tt = generate_truth_table(expr, force_vars=vars)

            for combo in all_combos:
                combo_set = set(combo)
                covered_minterms = set()
                for b in combo_set.union(min_cover):
                    for b2, ms in all_prime_implicants:
                        if b == b2:
                            covered_minterms.update(ms)

                if covered_minterms != set(minterms):
                    continue

                literals = sum(count_literals(b) for b in combo_set)
                if len(combo_set) < best_len or (len(combo_set) == best_len and literals < best_literals):
                    best_combo = combo_set
                    best_len = len(combo_set)
                    best_literals = literals

            if best_combo:
                min_cover.extend(best_combo)

    min_cover = sorted(set(min_cover))
    steps.append({
        "step": "Krok 6: Minimalne pokrycie (metoda Petricka)",
        "data": {
            "cover": [
                {"binary": b, "expr": bin_to_expr(b, vars)}
                for b in min_cover
            ],
            "opis": "Wybór minimalnego zestawu PI pokrywających wszystkie mintermy."
        }
    })

    simplified = ' ∨ '.join(bin_to_expr(b, vars) for b in min_cover) if min_cover else '0'
    steps.append({
        "step": "Krok 7: Uproszczone wyrażenie",
        "data": {
            "result": simplified,
            "opis": "Końcowe wyrażenie logiczne po uproszczeniu metodą Quine'a-McCluskeya."
        }
    })

    try:
        tt_orig = generate_truth_table(expr, force_vars=vars)
        tt_simp = generate_truth_table(simplified if simplified != '0' else 'A ∧ ¬A', force_vars=vars)
        verification = tt_orig == tt_simp
        verification_desc = "Tabela prawdy uproszczonego wyrażenia jest identyczna z oryginalną." if verification else "Błąd: Tabela prawdy uproszczonego wyrażenia różni się od oryginalnej."
    except Exception as e:
        verification = False
        verification_desc = f"Błąd weryfikacji: {e}"
        logger.error(f"Błąd weryfikacji: {e}")

    steps.append({
        "step": "Krok 8: Weryfikacja poprawności",
        "data": {
            "zgodność": verification,
            "opis": verification_desc
        }
    })

    # logger.info(f"Uproszczone wyrażenie: {simplified}")
    return {"result": simplified, "steps": steps, "expr_for_tests": simplified}