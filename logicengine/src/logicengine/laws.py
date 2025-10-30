# laws.py
"""Algebraic simplification using Boolean laws (step-by-step)."""

from __future__ import annotations
from typing import Any, Dict, List, Tuple, Optional, Iterable
from itertools import combinations
import copy

from .ast import generate_ast, normalize_bool_ast, canonical_str, canonical_str_minimal


def VAR(name: str) -> Dict[str, Any]:
    return {"op": "VAR", "name": name}

def CONST(v: int) -> Dict[str, Any]:
    return {"op": "CONST", "value": 1 if v else 0}

def NOT(x: Any) -> Dict[str, Any]:
    return {"op": "NOT", "child": x}

def AND(args: Iterable[Any]) -> Dict[str, Any]:
    return {"op": "AND", "args": list(args)}

def OR(args: Iterable[Any]) -> Dict[str, Any]:
    return {"op": "OR", "args": list(args)}


def pretty(n: Any) -> str:
    result = canonical_str(n)
    # Usuń zewnętrzne nawiasy jeśli całe wyrażenie jest w jednym nawiasie
    if result.startswith('(') and result.endswith(')'):
        inner = result[1:-1]
        # Sprawdź czy nawiasy są zbalansowane w środku
        balance = 0
        can_remove = True
        for char in inner:
            if char == '(':
                balance += 1
            elif char == ')':
                balance -= 1
            if balance < 0:
                can_remove = False
                break
        if can_remove and balance == 0:
            return inner
    return result

def count_nodes(n: Any) -> int:
    if not isinstance(n, dict):
        return 1
    op = n.get("op")
    if op in {"VAR", "CONST"}:
        return 1
    if op == "NOT":
        return 1 + count_nodes(n["child"])
    if op in {"AND", "OR"}:
        return 1 + sum(count_nodes(a) for a in n["args"])
    if op in {"IMP", "IFF"}:
        return 1 + count_nodes(n.get("left", {})) + count_nodes(n.get("right", {}))
    return 1

def count_literals(n: Any) -> int:
    if not isinstance(n, dict):
        return 0
    op = n.get("op")
    if op == "VAR":
        return 1
    if op == "CONST":
        return 0
    if op == "NOT":
        ch = n.get("child")
        if isinstance(ch, dict) and ch.get("op") == "VAR":
            return 1
        return count_literals(ch)
    if op in {"AND", "OR"}:
        return sum(count_literals(a) for a in n["args"])
    if op in {"IMP", "IFF"}:
        return count_literals(n.get("left", {})) + count_literals(n.get("right", {}))
    return 0

def measure(n: Any) -> Tuple[int, int, int]:
    s = pretty(n)
    return (count_literals(n), count_nodes(n), len(s))


Path = List[Tuple[str, Optional[int]]]  # ('args', i) or ('child', None)

def iter_nodes(node: Any, path: Optional[Path] = None):
    if path is None:
        path = []
    yield path, node
    if isinstance(node, dict):
        op = node.get("op")
        if op in {"AND", "OR"}:
            for i, a in enumerate(node.get("args", [])):
                yield from iter_nodes(a, path + [("args", i)])
        elif op == "NOT":
            ch = node.get("child")
            if ch is not None:
                yield from iter_nodes(ch, path + [("child", None)])

def get_by_path(node: Any, path: Path) -> Any:
    cur = node
    for key, idx in path:
        if key == "args":
            cur = cur["args"][idx]  # type: ignore[index]
        else:
            cur = cur["child"]
    return cur

def set_by_path(node: Any, path: Path, new_sub: Any) -> Any:
    """Set a subtree at path, returning a new tree (does not mutate original)."""
    if not path:
        return new_sub
    # Create a deep copy to avoid mutating the original
    # Note: This copy is necessary to prevent mutations, but caller should also backup if needed
    node = copy.deepcopy(node)
    key, idx = path[-1]
    parent = get_by_path(node, path[:-1])
    if key == "args":
        parent["args"][idx] = new_sub  # type: ignore[index]
    else:
        parent["child"] = new_sub
    return node


Lit = Tuple[str, bool]  # (name, True=positive, False=negated)

def is_lit(x: Any) -> bool:
    return (
        isinstance(x, dict)
        and (x.get("op") == "VAR"
             or (x.get("op") == "NOT"
                 and isinstance(x.get("child"), dict)
                 and x["child"].get("op") == "VAR"))
    )

def to_lit(x: Any) -> Optional[Lit]:
    if not isinstance(x, dict):
        return None
    if x.get("op") == "VAR":
        return (x["name"], True)
    if x.get("op") == "NOT" and isinstance(x.get("child"), dict) and x["child"].get("op") == "VAR":
        return (x["child"]["name"], False)
    return None

def lit_to_node(l: Lit) -> Any:
    name, pos = l
    return VAR(name) if pos else NOT(VAR(name))

def term_is_contradictory(lits: List[Lit]) -> bool:
    s = set()
    for v, p in lits:
        if (v, not p) in s:
            return True
        s.add((v, p))
    return False

def or_factor_is_tautology(lits: List[Lit]) -> bool:
    s = set()
    for v, p in lits:
        if (v, not p) in s:
            return True
        s.add((v, p))
    return False

def term_from_lits(lits: List[Lit]) -> Any:
    if not lits:
        return CONST(1)
    if len(lits) == 1:
        return lit_to_node(lits[0])
    return AND([lit_to_node(l) for l in lits])

def sum_from_lits(lits: List[Lit]) -> Any:
    if not lits:
        return CONST(0)
    if len(lits) == 1:
        return lit_to_node(lits[0])
    return OR([lit_to_node(l) for l in lits])

def canonical_lits(lits: Iterable[Lit]) -> List[Lit]:
    return sorted(set(lits), key=lambda t: (t[0], not t[1]))

def canon(n: Any) -> str:
    return canonical_str(n)


def laws_matches(node: Any) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []

    for path, sub in iter_nodes(node):
        if not isinstance(sub, dict):
            continue
        op = sub.get("op")

        if op == "NOT":
            ch = sub.get("child")
            if isinstance(ch, dict) and ch.get("op") == "CONST":
                v = ch["value"]
                out.append({
                    "law": "Negacja stałej",
                    "path": path,
                    "before": sub,
                    "after": CONST(0 if v else 1),
                    "note": "¬1=0, ¬0=1",
                })
            if isinstance(ch, dict) and ch.get("op") == "NOT":
                out.append({
                    "law": "Podwójna negacja",
                    "path": path,
                    "before": sub,
                    "after": ch["child"],
                    "note": "¬(¬X)=X",
                })
            if isinstance(ch, dict) and ch.get("op") in {"AND", "OR"}:
                inner = ch
                negs = [NOT(a) for a in inner.get("args", [])]
                after = OR(negs) if inner["op"] == "AND" else AND(negs)
                if inner["op"] == "AND":
                    out.append({
                        "law": "De Morgan: ¬(A ∧ B) → ¬A ∨ ¬B",
                        "path": path,
                        "before": sub,
                        "after": after,
                        "note": "¬(∧)=∨",
                    })
                else:
                    out.append({
                        "law": "De Morgan: ¬(A ∨ B) → ¬A ∧ ¬B",
                        "path": path,
                        "before": sub,
                        "after": after,
                        "note": "¬(∨)=∧",
                    })

        # Idempotency
        if op in {"AND", "OR"} and len(sub.get("args", [])) >= 2:
            seen: Dict[str, bool] = {}
            new_args = []
            for a in sub["args"]:
                k = canon(a)
                if k not in seen:
                    seen[k] = True
                    new_args.append(a)
            if len(new_args) < len(sub["args"]):
                if op == "AND":
                    out.append({
                        "law": "Idempotentność (∧)",
                        "path": path,
                        "before": sub,
                        "after": {"op": op, "args": new_args},
                        "note": "X ∧ X = X",
                    })
                else:
                    out.append({
                        "law": "Idempotentność (∨)",
                        "path": path,
                        "before": sub,
                        "after": {"op": op, "args": new_args},
                        "note": "X ∨ X = X",
                    })

        # Identities / domination
        if op == "AND":
            if any(isinstance(a, dict) and a.get("op") == "CONST" and a["value"] == 1 for a in sub["args"]):
                args = [a for a in sub["args"] if not (isinstance(a, dict) and a.get("op") == "CONST" and a["value"] == 1)]
                after = args[0] if len(args) == 1 else {"op": "AND", "args": args}
                out.append({
                    "law": "Element neutralny (A∧1)",
                    "path": path,
                    "before": sub,
                    "after": after,
                    "note": "Element neutralny dla koniunkcji: A∧1 = A",
                })
            if any(isinstance(a, dict) and a.get("op") == "CONST" and a["value"] == 0 for a in sub["args"]):
                out.append({
                    "law": "Element pochłaniający (A∧0)",
                    "path": path,
                    "before": sub,
                    "after": CONST(0),
                    "note": "Element pochłaniający dla koniunkcji: A∧0 = 0",
                })
            
            args = sub.get("args", [])
            for i, a in enumerate(args):
                for j, b in enumerate(args):
                    if i != j and _is_absorbed_by(a, b):
                        new_args = [arg for k, arg in enumerate(args) if k != i]
                        after = new_args[0] if len(new_args) == 1 else {"op": "AND", "args": new_args}
                        out.append({
                            "law": "Absorpcja (∧)",
                            "path": path,
                            "before": sub,
                            "after": after,
                            "note": "A ∧ (A ∨ B) = A",
                        })
                        break
                if len(out) > 0 and out[-1]["law"] == "Absorpcja (∧)":
                    break
            
            args = sub.get("args", [])
            for i, a in enumerate(args):
                if isinstance(a, dict) and a.get("op") == "NOT":
                    child = a.get("child")
                    if isinstance(child, dict) and child.get("op") == "VAR":
                        var_name = child.get("name")
                        # Look for the same variable without negation
                        for j, b in enumerate(args):
                            if i != j and isinstance(b, dict) and b.get("op") == "VAR" and b.get("name") == var_name:
                                out.append({
                                    "law": "Kontradykcja (A ∧ ¬A)",
                                    "path": path,
                                    "before": sub,
                                    "after": CONST(0),
                                    "note": "Kontradykcja: A∧¬A = 0",
                                })
                                break
            
            # Distributivity: (A∨B)∧C = (A∧C)∨(B∧C)
            args = sub.get("args", [])
            for i, a in enumerate(args):
                if isinstance(a, dict) and a.get("op") == "OR":
                    or_args = a.get("args", [])
                    if len(or_args) >= 2:
                        # Find other AND arguments to distribute over
                        other_args = [b for j, b in enumerate(args) if i != j]
                        if other_args:
                            # Create distributed form: (A∧C)∨(B∧C)∨...
                            distributed = []
                            for or_arg in or_args:
                                new_and_args = [or_arg] + other_args
                                if len(new_and_args) == 1:
                                    distributed.append(new_and_args[0])
                                else:
                                    distributed.append({"op": "AND", "args": new_and_args})
                            
                            after = {"op": "OR", "args": distributed}
                            out.append({
                                "law": "Dystrybutywność (A∨B)∧C",
                                "path": path,
                                "before": sub,
                                "after": after,
                                "note": "Dystrybutywność koniunkcji względem alternatywy: (A∨B)∧C = (A∧C)∨(B∧C)",
                            })
                            break
            
            # Distributivity: A∧(B∨C) = (A∧B)∨(A∧C)
            args = sub.get("args", [])
            for i, a in enumerate(args):
                if isinstance(a, dict) and a.get("op") == "OR":
                    or_args = a.get("args", [])
                    if len(or_args) >= 2:
                        # Find other AND arguments to distribute over
                        other_args = [b for j, b in enumerate(args) if i != j]
                        if other_args:
                            # Create distributed form: (A∧B)∨(A∧C)∨...
                            distributed = []
                            for or_arg in or_args:
                                new_and_args = [or_arg] + other_args
                                if len(new_and_args) == 1:
                                    distributed.append(new_and_args[0])
                                else:
                                    distributed.append({"op": "AND", "args": new_and_args})
                            
                            after = {"op": "OR", "args": distributed}
                            out.append({
                                "law": "Dystrybutywność A∧(B∨C)",
                                "path": path,
                                "before": sub,
                                "after": after,
                                "note": "Dystrybutywność koniunkcji względem alternatywy: A∧(B∨C) = (A∧B)∨(A∧C)",
                            })
                            break

        if op == "OR":
            if any(isinstance(a, dict) and a.get("op") == "CONST" and a["value"] == 0 for a in sub["args"]):
                args = [a for a in sub["args"] if not (isinstance(a, dict) and a.get("op") == "CONST" and a["value"] == 0)]
                after = args[0] if len(args) == 1 else {"op": "OR", "args": args}
                out.append({
                    "law": "Element neutralny (A∨0)",
                    "path": path,
                    "before": sub,
                    "after": after,
                    "note": "Element neutralny dla alternatywy: A∨0 = A",
                })
            if any(isinstance(a, dict) and a.get("op") == "CONST" and a["value"] == 1 for a in sub["args"]):
                out.append({
                    "law": "Element pochłaniający (A∨1)",
                    "path": path,
                    "before": sub,
                    "after": CONST(1),
                    "note": "Element pochłaniający dla alternatywy: A∨1 = 1",
                })

            # P ∨ ¬P = 1
            lits_list = [to_lit(x) for x in sub.get("args", [])]
            if None not in lits_list and or_factor_is_tautology([t for t in lits_list if t]):
                out.append({
                                "law": "Dopełnienie (A ∨ ¬A)",
                    "path": path,
                    "before": sub,
                    "after": CONST(1),
                    "note": "Tautologia: A∨¬A = 1",
                })

            # Replace (P ∧ ¬P) factors with CONST(0) in OR
            # This is more explicit and shows the intermediate step
            new_args = []
            replaced = False
            for a in sub["args"]:
                if isinstance(a, dict) and a.get("op") == "AND":
                    lits = [to_lit(x) for x in a.get("args", [])]
                    if None not in lits and term_is_contradictory([t for t in lits if t]):
                        # Replace with CONST(0) instead of removing
                        new_args.append(CONST(0))
                        replaced = True
                    else:
                        new_args.append(a)
                else:
                    new_args.append(a)
            if replaced:
                after = new_args[0] if len(new_args) == 1 else {"op": "OR", "args": new_args}
                out.append({
                    "law": "Kontradykcja (A ∧ ¬A)",
                    "path": path,
                    "before": sub,
                    "after": after,
                    "note": "A∧¬A = 0",
                })

        # Absorption
        if op == "OR":
            # X ∨ (X ∧ Y) = X
            for x in sub["args"]:
                for y in sub["args"]:
                    if x is y:
                        continue
                    if isinstance(y, dict) and y.get("op") == "AND":
                        if any(canon(a) == canon(x) for a in y.get("args", [])):
                            out.append({
                                "law": "Absorpcja (∨)",
                                "path": path,
                                "before": sub,
                                "after": x,
                                "note": "X∨(X∧Y)=X",
                            })
                            break
            # X ∨ (¬X ∧ Y) = X ∨ Y
            lits_of_x = [to_lit(a) for a in sub["args"] if is_lit(a)]
            for a in sub["args"]:
                if isinstance(a, dict) and a.get("op") == "AND":
                    lits = [t for t in (to_lit(x) for x in a.get("args", [])) if t]
                    for lx in lits_of_x:
                        if (lx[0], not lx[1]) in lits:
                            rest = [lit_to_node(l) for l in lits if l != (lx[0], not lx[1])]
                            after = OR([lit_to_node(lx)] + (rest if rest else [CONST(0)]))
                            out.append({
                                "law": "Absorpcja z negacją",
                                "path": path,
                                "before": sub,
                                "after": after,
                                "note": "X∨(¬X∧Y)=X∨Y",
                            })
                            break

        if op == "AND":
            # X ∧ (X ∨ Y) = X
            for x in sub["args"]:
                for y in sub["args"]:
                    if x is y:
                        continue
                    if isinstance(y, dict) and y.get("op") == "OR":
                        if any(canon(a) == canon(x) for a in y.get("args", [])):
                            out.append({
                                "law": "Absorpcja (∧)",
                                "path": path,
                                "before": sub,
                                "after": x,
                                "note": "X∧(X∨Y)=X",
                            })
                            break
            # X ∧ (¬X ∨ Y) = X ∧ Y
            lits_of_x = [to_lit(a) for a in sub["args"] if is_lit(a)]
            for a in sub["args"]:
                if isinstance(a, dict) and a.get("op") == "OR":
                    # Check if all OR arguments are literals (to avoid complex expressions)
                    or_args = a.get("args", [])
                    all_literals = all(to_lit(x) is not None for x in or_args)
                    
                    if all_literals:
                        lits = [t for t in (to_lit(x) for x in or_args) if t]
                        for lx in lits_of_x:
                            if (lx[0], not lx[1]) in lits:
                                rest = [lit_to_node(l) for l in lits if l != (lx[0], not lx[1])]
                                if rest:
                                    after = AND([lit_to_node(lx), OR(rest)])
                                else:
                                    after = lit_to_node(lx)
                                out.append({
                                    "law": "Absorpcja z negacją (dual)",
                                    "path": path,
                                    "before": sub,
                                    "after": after,
                                    "note": "X∧(¬X∨Y)=X∧Y",
                                })
                                break

        # SOP rules: covering / consensus / factorization
        if op == "OR":
            terms: List[List[Lit]] = []
            ok_shape = True
            for a in sub.get("args", []):
                if is_lit(a):
                    terms.append([to_lit(a)])
                elif isinstance(a, dict) and a.get("op") == "AND":
                    lits = [to_lit(x) for x in a.get("args", [])]
                    if None in lits:
                        ok_shape = False
                        break
                    terms.append(canonical_lits([t for t in lits if t]))
                else:
                    ok_shape = False
                    break
            if ok_shape:
                # covering - DISABLED: This logic is fundamentally flawed
                # In logic, more restrictive expressions (with more variables) 
                # cannot be removed by less restrictive ones
                # remove_idx = set()
                # for i, j in combinations(range(len(terms)), 2):
                #     S = set(terms[i]); T = set(terms[j])
                #     if S <= T:
                #         # S is more restrictive (subset), remove T (superset)
                #         remove_idx.add(j)
                #     elif T <= S:
                #         # T is more restrictive (subset), remove S (superset)
                #         remove_idx.add(i)
                # if remove_idx:
                #     new = [a for k, a in enumerate(sub["args"]) if k not in remove_idx]
                #     after = new[0] if len(new) == 1 else {"op": "OR", "args": new}
                #     out.append({
                #         "law": "Pokrywanie (SOP)",
                #         "path": path,
                #         "before": sub,
                #         "after": after,
                #         "note": "krótszy składnik pokrywa dłuższy",
                #     })
                for var in {v for lits in terms for (v, _) in lits}:
                    pos_terms = [set(ls) - {(var, True)} for ls in terms if (var, True) in ls]
                    neg_terms = [set(ls) - {(var, False)} for ls in terms if (var, False) in ls]
                    
                    consensus_candidates = []
                    for P in pos_terms:
                        for N in neg_terms:
                            consensus = canonical_lits(list(P | N))
                            consensus_candidates.append(consensus)
                    
                    to_remove = set()
                    for consensus in consensus_candidates:
                        for idx, term_lits in enumerate(terms):
                            if set(consensus).issubset(set(term_lits)):
                                to_remove.add(idx)
                    
                    if to_remove:
                        new = [a for k, a in enumerate(sub["args"]) if k not in to_remove]
                        after = new[0] if len(new) == 1 else {"op": "OR", "args": new}
                        out.append({
                            "law": "Konsensus (SOP)",
                            "path": path,
                            "before": sub,
                            "after": after,
                            "note": "XY + X'Z + YZ = XY + X'Z",
                        })
                        break
                for i, j in combinations(range(len(terms)), 2):
                    S = set(terms[i]); T = set(terms[j])
                    C = S & T
                    if not C:
                        continue
                    R1 = S - C; R2 = T - C
                    
                    # Sprawdź czy jeden z termów jest podzbiorem drugiego
                    if not R1 or not R2:
                        # Jeden z termów jest podzbiorem drugiego - użyj absorpcji
                        if not R1:  # S jest podzbiorem T
                            # A ∧ B ∨ A = A (absorpcja)
                            after = sub["args"][j]  # użyj większego termu
                        else:  # T jest podzbiorem S
                            # A ∨ A ∧ B = A (absorpcja)
                            after = sub["args"][i]  # użyj większego termu
                        
                        if measure(after) < measure(OR([sub["args"][i], sub["args"][j]])):
                            new_terms = [a for k, a in enumerate(sub["args"]) if k not in {i, j}]
                            new_terms.append(after)
                            after = OR(new_terms)
                            out.append({
                                "law": "Absorpcja (∨)",
                                "path": path,
                                "before": sub,
                                "after": after,
                                "note": "X ∨ X∧Y = X",
                            })
                            break
                        continue
                    
                    C_node = term_from_lits(canonical_lits(list(C)))
                    R1_node = term_from_lits(canonical_lits(list(R1)))
                    R2_node = term_from_lits(canonical_lits(list(R2)))
                    candidate = AND([C_node, OR([R1_node, R2_node])])
                    if measure(candidate) < measure(OR([sub["args"][i], sub["args"][j]])):
                        new_terms = [a for k, a in enumerate(sub["args"]) if k not in {i, j}]
                        new_terms.append(candidate)
                        after = OR(new_terms)
                        out.append({
                            "law": "Faktoryzacja (SOP)",
                            "path": path,
                            "before": sub,
                            "after": after,
                            "note": "wyłącz wspólny czynnik",
                        })
                        break

        # POS (dual)
        if op == "AND":
            sums: List[List[Lit]] = []
            ok_shape = True
            for a in sub.get("args", []):
                if is_lit(a):
                    sums.append([to_lit(a)])
                elif isinstance(a, dict) and a.get("op") == "OR":
                    lits = [to_lit(x) for x in a.get("args", [])]
                    if None in lits:
                        ok_shape = False
                        break
                    sums.append(canonical_lits([t for t in lits if t]))
                else:
                    ok_shape = False
                    break
            if ok_shape:
                # (P∨¬P)=1 → drop factor
                remove_taut = [idx for idx, ls in enumerate(sums) if or_factor_is_tautology(ls)]
                if remove_taut:
                    keep = [a for k, a in enumerate(sub["args"]) if k not in remove_taut]
                    after = keep[0] if len(keep) == 1 else {"op": "AND", "args": keep}
                    out.append({
                        "law": "Redundancja POS (tautologia)",
                        "path": path,
                        "before": sub,
                        "after": after,
                        "note": "(P∨¬P)=1 w czynniku",
                    })
                # covering (dual)
                remove_idx = set()
                for i, j in combinations(range(len(sums)), 2):
                    S = set(sums[i]); T = set(sums[j])
                    if S <= T:
                        remove_idx.add(j)
                    elif T <= S:
                        remove_idx.add(i)
                if remove_idx:
                    new = [a for k, a in enumerate(sub["args"]) if k not in remove_idx]
                    after = new[0] if len(new) == 1 else {"op": "AND", "args": new}
                    out.append({
                        "law": "Pokrywanie (POS)",
                        "path": path,
                        "before": sub,
                        "after": after,
                        "note": "krótsza suma pokrywa dłuższą",
                    })
                # factorization (dual)
                for i, j in combinations(range(len(sums)), 2):
                    S = set(sums[i]); T = set(sums[j])
                    C = S & T
                    if not C:
                        continue
                    R1 = S - C; R2 = T - C
                    C_node = sum_from_lits(canonical_lits(list(C)))
                    R1_node = term_from_lits(canonical_lits(list(R1)))
                    R2_node = term_from_lits(canonical_lits(list(R2)))
                    candidate = OR([C_node, AND([R1_node, R2_node])])
                    if measure(candidate) < measure(AND([sub["args"][i], sub["args"][j]])):
                        new_factors = [a for k, a in enumerate(sub["args"]) if k not in {i, j}]
                        new_factors.append(candidate)
                        after = OR(new_factors)
                        out.append({
                            "law": "Faktoryzacja (POS)",
                            "path": path,
                            "before": sub,
                            "after": after,
                            "note": "wyłącz wspólną sumę",
                        })
                        break

        # Controlled distribution (only when it helps)
        if op == "AND":
            for a in sub["args"]:
                if isinstance(a, dict) and a.get("op") == "OR" and len(a.get("args", [])) >= 2:
                    others = [t for t in sub["args"] if t is not a]
                    distributed = OR([AND([t] + others) for t in a["args"]])
                    if measure(distributed) < measure(sub):
                        out.append({
                            "law": "Rozdzielność (AND→OR)",
                            "path": path,
                            "before": sub,
                            "after": distributed,
                            "note": "X∧(Y∨Z)=(X∧Y)∨(X∧Z)",
                        })
                    break

        if op == "OR":
            for a in sub["args"]:
                if isinstance(a, dict) and a.get("op") == "AND" and len(a.get("args", [])) >= 2:
                    others = [t for t in sub["args"] if t is not a]
                    distributed = AND([OR([t] + others) for t in a["args"]])
                    if measure(distributed) < measure(sub):
                        out.append({
                            "law": "Rozdzielność (OR→AND)",
                            "path": path,
                            "before": sub,
                            "after": distributed,
                            "note": "X∨(Y∧Z)=(X∨Y)∧(X∨Z)",
                        })
                    break
            
            # Faktoryzacja: wyciąganie wspólnych czynników z OR
            # Przykład: (A∧X)∨(A∧Y) = A∧(X∨Y)
            if len(sub["args"]) >= 2:
                args = sub["args"]
                # Szukaj argumentów które są AND
                and_args = [a for a in args if isinstance(a, dict) and a.get("op") == "AND"]
                if len(and_args) >= 2:
                    # Znajdź wspólne czynniki w AND argumentach
                    for i in range(len(and_args)):
                        for j in range(i + 1, len(and_args)):
                            a1_args = and_args[i].get("args", [])
                            a2_args = and_args[j].get("args", [])
                            
                            # Znajdź wspólne czynniki
                            common = []
                            for x in a1_args:
                                if any(canon(x) == canon(y) for y in a2_args):
                                    common.append(x)
                            
                            if common:
                                # Wyciągnij wspólne czynniki
                                remaining1 = [x for x in a1_args if not any(canon(x) == canon(c) for c in common)]
                                remaining2 = [x for x in a2_args if not any(canon(x) == canon(c) for c in common)]
                                
                                # Usuń duplikaty z common (zachowaj tylko unikalne)
                                unique_common = []
                                seen_common = set()
                                for c in common:
                                    c_canon = canon(c)
                                    if c_canon not in seen_common:
                                        unique_common.append(c)
                                        seen_common.add(c_canon)
                                
                                if unique_common:
                                    # Stwórz factored wyrażenie
                                    factor = unique_common[0] if len(unique_common) == 1 else AND(unique_common)
                                    
                                    # Stwórz pozostałą część
                                    rem1_node = remaining1[0] if len(remaining1) == 1 else (AND(remaining1) if remaining1 else CONST(1))
                                    rem2_node = remaining2[0] if len(remaining2) == 1 else (AND(remaining2) if remaining2 else CONST(1))
                                    
                                    # Połącz pozostałości w OR
                                    remaining_or = OR([rem1_node, rem2_node])
                                    
                                    # Stwórz factored result
                                    factored = AND([factor, remaining_or])
                                    
                                    # Dodaj pozostałe argumenty OR
                                    # Użyj indeksów z oryginalnej listy args
                                    and_indices_in_args = []
                                    for k, a in enumerate(args):
                                        if isinstance(a, dict) and a.get("op") == "AND" and (a is and_args[i] or a is and_args[j]):
                                            and_indices_in_args.append(k)
                                    other_args = [a for k, a in enumerate(args) if k not in and_indices_in_args]
                                    if other_args:
                                        factored = OR(other_args + [factored])
                                    
                                    # Sprawdź czy to poprawia measure
                                    if measure(factored) < measure(sub):
                                        out.append({
                                            "law": "Faktoryzacja",
                                            "path": path,
                                            "before": sub,
                                            "after": factored,
                                            "note": "wyciągnij wspólny czynnik: (A∧X)∨(A∧Y)=A∧(X∨Y)",
                                        })
                                        break
                        else:
                            continue
                        break

    return out

# --- driver -------------------------------------------------------------------

def pick_best(node: Any, matches: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not matches:
        return None
    
    best: Optional[Dict[str, Any]] = None
    best_measure = None
    
    for m in matches:
        after = m["after"]
        after_measure = measure(after)
        
        if best is None:
            best = m
            best_measure = after_measure
            continue
            
        # Primary: prefer smaller measure
        if after_measure < best_measure:
            best = m
            best_measure = after_measure
        elif after_measure == best_measure:
            # Tie-break 1: prefer algebraic over axiom
            if m.get("source") == "algebraic" and best.get("source") == "axiom":
                best = m
                best_measure = after_measure
            elif m.get("source") == best.get("source"):
                # Tie-break 2: prefer shorter string representation
                if len(pretty(after)) < len(pretty(best["after"])):
                    best = m
                    best_measure = after_measure
    
    return best

def simplify_with_laws(expr: str, max_steps: int = 80, mode: str = "mixed") -> Dict[str, Any]:
    legacy_ast = generate_ast(expr)
    node = normalize_bool_ast(legacy_ast, expand_imp_iff=True)

    steps: List[Dict[str, Any]] = []
    seen_expressions = set()  # Track seen expressions to detect oscillation
    skipped_transformations = set()  # Track transformations we tried but skipped (not optimal)
    
    for _ in range(max_steps):
        # Collect matches based on mode
        matches = []
        if mode in ("algebraic", "mixed"):
            algebraic_matches = laws_matches(node)
            for match in algebraic_matches:
                match["source"] = "algebraic"
                match["axiom_id"] = None
                match["axiom_subst"] = None
                # Add derived_from_axioms mapping if available
                from .axioms import DERIVED_FROM_AXIOMS
                match["derived_from_axioms"] = DERIVED_FROM_AXIOMS.get(match.get("law", ""), [])
            matches.extend(algebraic_matches)
        
        if mode in ("axioms", "mixed"):
            from .axioms import axioms_matches
            axiom_matches = axioms_matches(node)
            for match in axiom_matches:
                # axiom matches already have source="axiom", axiom_id, etc.
                match["derived_from_axioms"] = []
            matches.extend(axiom_matches)
        
        # Filter out transformations we already tried and skipped
        # Use canonical representations of before/after subexpressions to identify duplicates
        if skipped_transformations:
            filtered_matches = []
            for m in matches:
                before_sub = m.get("before")
                after_sub = m.get("after")
                law = m.get("law")
                if before_sub and after_sub:
                    before_canon = canonical_str(before_sub)
                    after_canon = canonical_str(after_sub)
                    if (before_canon, after_canon, law) not in skipped_transformations:
                        filtered_matches.append(m)
                else:
                    # Keep matches without before/after (shouldn't happen, but safety)
                    filtered_matches.append(m)
            matches = filtered_matches
        
        if not matches:
            break
        choice = pick_best(node, matches)
        if not choice:
            break

        sub_before = choice["before"]
        sub_after = choice["after"]
        path = choice["path"]

        # Save node before modification so we can restore it if we skip this step
        node_backup = copy.deepcopy(node)
        
        before_str = pretty(node)
        node = set_by_path(node, path, sub_after)
        node = normalize_bool_ast(node)
        after_str = pretty(node)

        # Check for oscillation - use canonical_str for structural comparison
        after_canonical = canonical_str(node)
        if after_canonical in seen_expressions:
            steps.append({
                "law": "Zatrzymano (oscylacja)",
                "note": "Wykryto oscylację - system zatrzymany",
                "path": path,
                "before_tree": before_str,
                "after_tree": after_str,
                "before_subexpr": pretty(sub_before),
                "after_subexpr": pretty(sub_after),
                "applicable_here": [],
                "source": "system",
                "axiom_id": None,
                "axiom_subst": None,
                "derived_from_axioms": [],
            })
            break

        # Compare the ENTIRE expression before and after transformation
        # (not just the subexpression) to correctly assess improvement
        before_full_measure = measure(node_backup)
        after_full_measure = measure(node)
        
        # Also check subexpression measure as secondary check
        before_sub_measure = measure(sub_before)
        after_sub_measure = measure(sub_after)

        # Skip ONLY if transformation makes the expression significantly WORSE
        # We allow small regressions (especially in node count) if they might enable
        # further simplifications. This is important for intermediate steps like De Morgan.
        # (unless it's an axiom/desugaring which we always allow)
        
        # Compare measures: (literals, nodes, string_len)
        # A transformation is "significantly worse" if:
        # - It increases literal count (always bad)
        # - OR it increases both node count AND string length by significant amounts
        is_worse = False
        if choice.get("source") != "axiom":
            if after_full_measure[0] > before_full_measure[0]:
                # More literals - definitely worse
                is_worse = True
            elif (after_full_measure[1] > before_full_measure[1] + 2 and 
                  after_full_measure[2] > before_full_measure[2] + 3):
                # Significantly more nodes AND longer string - probably worse
                is_worse = True
            elif (after_full_measure[1] > before_full_measure[1] + 5):
                # Very large increase in nodes - definitely worse
                is_worse = True
        
        if is_worse:
            # Mark this transformation as skipped using canonical representations of subexpressions
            sub_before_canon = canonical_str(sub_before)
            sub_after_canon = canonical_str(sub_after)
            skipped_transformations.add((sub_before_canon, sub_after_canon, choice.get("law")))
            node = node_backup
            continue
        
        # If measure is the same or slightly worse (neutral/acceptable transformation),
        # allow it but check for oscillation to avoid infinite loops
        if after_canonical in seen_expressions and choice.get("source") != "axiom":
            # We've seen this result before - don't repeat
            sub_before_canon = canonical_str(sub_before)
            sub_after_canon = canonical_str(sub_after)
            skipped_transformations.add((sub_before_canon, sub_after_canon, choice.get("law")))
            node = node_backup
            continue

        seen_expressions.add(after_canonical)

        applicable_here = []
        applied_law = choice["law"]
        applied_path_tuple = tuple(path)
        seen_laws = {applied_law}
        
        for m in matches:
            m_path_tuple = tuple(m["path"])
            m_law = m["law"]
            if m_path_tuple == applied_path_tuple and m_law not in seen_laws:
                seen_laws.add(m_law)
                applicable_here.append(m_law)

        steps.append({
            "law": choice["law"],
            "note": choice.get("note", ""),
            "path": path,
            "before_tree": before_str,
            "after_tree": after_str,
            "before_subexpr": pretty(sub_before),
            "after_subexpr": pretty(sub_after),
            "applicable_here": applicable_here,
            "source": choice.get("source", "algebraic"),
            "axiom_id": choice.get("axiom_id"),
            "axiom_subst": choice.get("axiom_subst"),
            "derived_from_axioms": choice.get("derived_from_axioms", []),
        })

        if before_str == after_str:
            break

    return {
        "result": pretty(node),
        "steps": steps,
        "normalized_ast": node,
        "mode": "pedantic",
    }

# --- apply a specific law once ------------------------------------------------

def apply_law_once(expr: str, path: List[List[Optional[int]]], law: str) -> Dict[str, Any]:
    """Apply one selected law (by name) at an exact path."""
    legacy_ast = generate_ast(expr)
    node = normalize_bool_ast(legacy_ast)

    matches = laws_matches(node)
    here = [m for m in matches if m["path"] == path]
    if not here:
        return {"ok": False, "error": "Brak dopasowań w podanej ścieżce.", "available": []}

    cand = [m for m in here if m["law"] == law]
    if not cand:
        return {"ok": False, "error": "Podane prawo nie pasuje w tym miejscu.", "available": [m["law"] for m in here]}

    choice = cand[0]
    before_str = pretty(node)

    node = set_by_path(node, path, choice["after"])
    node = normalize_bool_ast(node)
    after_str = pretty(node)

    return {
        "ok": True,
        "applied_law": choice["law"],
        "note": choice.get("note", ""),
        "path": path,
        "before_tree": before_str,
        "after_tree": after_str,
        "before_subexpr": pretty(choice["before"]),
        "after_subexpr": pretty(choice["after"]),
        "alternatives_here": [m["law"] for m in here],
    }



def _is_absorbed_by(a: Any, b: Any) -> bool:
    if not isinstance(a, dict) or not isinstance(b, dict):
        return False
    
    a_lits = _extract_literals(a)
    b_lits = _extract_literals(b)
    
    return set(a_lits).issubset(set(b_lits))

def _extract_literals(node: Any) -> List[Lit]:
    if isinstance(node, str):
        return [(node, True)]
    
    if not isinstance(node, dict):
        return []
    
    op = node.get("op")
    if op == "VAR":
        return [(node.get("name", "?"), True)]
    elif op == "CONST":
        return []
    elif op == "NOT":
        child = node.get("child")
        if isinstance(child, dict) and child.get("op") == "VAR":
            return [(child.get("name", "?"), False)]
        return []
    elif op in {"AND", "OR"}:
        result = []
        for arg in node.get("args", []):
            result.extend(_extract_literals(arg))
        return result
    
    return []
