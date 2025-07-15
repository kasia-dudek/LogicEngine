import logging
from .parser import LogicParser, LogicExpressionError
from .truth_table import generate_truth_table, TruthTableError
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class QMError(Exception):
    pass

def simplify_qm(expr: str) -> Dict[str, Any]:
    steps = []
    try:
        std = LogicParser.parse(expr)
        table = generate_truth_table(expr)
    except (LogicExpressionError, TruthTableError) as e:
        logger.error(f"Błąd parsera lub tabeli prawdy: {e}")
        raise QMError(f"Błąd parsera lub tabeli prawdy: {e}")
    vars = sorted([k for k in table[0] if k != 'result'])
    n = len(vars)
    if n < 1 or n > 4:
        logger.error("Zbyt wiele lub za mało zmiennych dla Quine-McCluskey")
        raise QMError("Obsługiwane są wyrażenia z 1-4 zmiennymi")
    # Krok 1: mintermy
    minterms = [i for i, row in enumerate(table) if row['result']]
    steps.append({"step": "Find minterms", "minterms": minterms})
    if not minterms:
        steps.append({"step": "Sprzeczność", "result": "0"})
        return {"result": "0", "steps": steps}
    if len(minterms) == 2**n:
        steps.append({"step": "Tautologia", "result": "1"})
        return {"result": "1", "steps": steps}
    # Krok 2: grupowanie mintermów wg liczby jedynek
    groups = {}
    for m in minterms:
        ones = bin(m).count('1')
        groups.setdefault(ones, []).append(_to_bin(m, n))
    steps.append({"step": "Group minterms by ones", "groups": groups})
    # Krok 3: łączenie mintermów (iteracyjnie)
    all_prime = []
    used = set()
    current = [(_to_bin(m, n), [m]) for m in minterms]
    combine_steps = []
    while True:
        next_round = []
        marked = set()
        pairs = []
        for i in range(len(current)):
            for j in range(i+1, len(current)):
                b1, ms1 = current[i]
                b2, ms2 = current[j]
                diff = [(a != b) for a, b in zip(b1, b2)]
                if sum(diff) == 1:
                    idx = diff.index(True)
                    combined = list(b1)
                    combined[idx] = '-'
                    combined = ''.join(combined)
                    if (combined, tuple(sorted(ms1+ms2))) not in marked:
                        next_round.append((combined, sorted(ms1+ms2)))
                        marked.add((combined, tuple(sorted(ms1+ms2))))
                    pairs.append({"from": [b1, b2], "to": combined})
        combine_steps.append({"round": len(combine_steps)+1, "pairs": pairs, "next": next_round})
        # Zaznacz nieużyte (prime implicants)
        used_in_this = set()
        for c, ms in next_round:
            for m in ms:
                used_in_this.add(tuple(ms))
        for b, ms in current:
            if not any(set(ms).issubset(set(nr[1])) for nr in next_round):
                all_prime.append((b, ms))
        if not next_round:
            break
        current = next_round
    steps.append({"step": "Combine minterms", "rounds": combine_steps, "prime_implicants": all_prime})
    # Krok 4: tabela pokrycia (prime implicants vs minterms)
    table_cover = {}
    for b, ms in all_prime:
        for m in ms:
            table_cover.setdefault(m, []).append(b)
    steps.append({"step": "Prime implicant chart", "cover": table_cover})
    # Krok 5: wybór zasadniczych implikantów
    essential = set()
    for m, bs in table_cover.items():
        if len(bs) == 1:
            essential.add(bs[0])
    steps.append({"step": "Essential prime implicants", "essential": list(essential)})
    # Krok 6: wynik końcowy (dla edukacji: połącz prime implicants OR)
    simplified = ' ∨ '.join(_bin_to_expr(b, vars) for b in essential) if essential else ' ∨ '.join(_bin_to_expr(b, vars) for b, _ in all_prime)
    steps.append({"step": "Simplified expression", "result": simplified})
    return {"result": simplified, "steps": steps}

def _to_bin(m: int, n: int) -> str:
    return format(m, f'0{n}b')

def _bin_to_expr(b: str, vars: List[str]) -> str:
    terms = []
    for i, ch in enumerate(b):
        if ch == '-':
            continue
        if ch == '1':
            terms.append(vars[i])
        else:
            terms.append(f'¬{vars[i]}')
    return '∧'.join(terms) if terms else '1' 