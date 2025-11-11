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


def _pretty_with_tokens_internal(node: Any, path: Optional[List[Tuple[str, Optional[int]]]] = None, tokens: Optional[List[Dict[str, Any]]] = None, current_pos: int = 0) -> Tuple[str, int]:
    """
    Internal recursive function for pretty_tokens.
    Builds the string and records token positions with node paths.
    
    Returns:
        (text, next_pos) where next_pos is the position after the generated text.
    """
    if tokens is None:
        tokens = []
    
    if path is None:
        path = []
    
    if not isinstance(node, dict):
        # Leaf node (string literal)
        text = str(node)
        tokens.append({
            "node_id": str(path) if path else "root",
            "path": path.copy(),
            "text": text,
            "start": current_pos,
            "end": current_pos + len(text),
            "length": len(text)
        })
        return text, current_pos + len(text)
    
    op = node.get("op")
    
    if op == "VAR":
        name = node.get("name", "?")
        tokens.append({
            "node_id": str(path) if path else "root",
            "path": path.copy(),
            "text": name,
            "start": current_pos,
            "end": current_pos + len(name),
            "length": len(name)
        })
        return name, current_pos + len(name)
    
    if op == "CONST":
        value = str(node.get("value", "?"))
        tokens.append({
            "node_id": str(path) if path else "root",
            "path": path.copy(),
            "text": value,
            "start": current_pos,
            "end": current_pos + len(value),
            "length": len(value)
        })
        return value, current_pos + len(value)
    
    if op == "NOT":
        child = node.get("child")
        child_text, child_end = _pretty_with_tokens_internal(child, path + [("child", None)], tokens, current_pos + 1) if child is not None else ("?", current_pos + 1)
        result = f"¬{child_text}"
        result_end = current_pos + len(result)
        # Record token for this NOT node
        tokens.append({
            "node_id": str(path) if path else "root",
            "path": path.copy(),
            "text": result,
            "start": current_pos,
            "end": result_end,
            "length": len(result)
        })
        return result, result_end
    
    if op in {"AND", "OR"}:
        args = node.get("args", [])
        if not args:
            return "?", current_pos
        
        symbol = "∧" if op == "AND" else "∨"
        parts = []
        pos = current_pos + 1  # Start after opening '('
        # Use same format as canonical_str: no spaces around symbol
        separator = symbol  # No spaces, just the symbol
        
        for i, arg in enumerate(args):
            if i > 0:
                # Add separator before argument (except first)
                pos += len(separator)
            arg_text, pos = _pretty_with_tokens_internal(arg, path + [("args", i)], tokens, pos)
            parts.append(arg_text)
        
        # Build result using same separator format as canonical_str (no spaces)
        inner = separator.join(parts)
        result = f"({inner})"
        result_end = pos + 1  # +1 for closing ')'
        
        # Verify result length matches our position calculation
        if len(result) != (result_end - current_pos):
            # Recalculate if there's a mismatch (shouldn't happen, but safety check)
            result_end = current_pos + len(result)
        
        # Record token for this AND/OR node - WITHOUT outer parentheses
        # The span should only cover the inner content, not the parentheses
        # Parentheses are part of the parent node's syntax, not this node's content
        inner_start = current_pos + 1  # After opening '('
        inner_end = pos  # Before closing ')'
        
        tokens.append({
            "node_id": str(path) if path else "root",
            "path": path.copy(),
            "text": inner,  # Inner content without parentheses
            "start": inner_start,
            "end": inner_end,
            "length": len(inner)
        })
        return result, result_end
    
    # Fallback for other operators
    text = canonical_str(node)
    tokens.append({
        "node_id": str(path) if path else "root",
        "path": path.copy(),
        "text": text,
        "start": current_pos,
        "end": current_pos + len(text),
        "length": len(text)
    })
    return text, current_pos + len(text)


def pretty_with_tokens(node: Any) -> Tuple[str, Dict[str, Tuple[int, int]]]:
    """
    Generate pretty string with token map (node_id -> (start, end)).
    
    Returns:
        (text, spans_map) where:
        - text: The pretty-printed string (with outer parentheses removed if applicable)
        - spans_map: Dict mapping node_id (stringified path) -> (start, end) tuple
    
    This uses the SAME normalization and pretty-printing logic as pretty(),
    ensuring consistency.
    """
    # Normalize node first
    if isinstance(node, dict) and 'op' in node:
        node = normalize_bool_ast(node)
    
    # Build tokens from canonical representation
    tokens = []
    text, _ = _pretty_with_tokens_internal(node, None, tokens, 0)
    
    # Apply outer parentheses removal (same logic as pretty())
    original_text = text
    if text.startswith('(') and text.endswith(')'):
        inner = text[1:-1]
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
            text = inner
    
    # If we removed outer parentheses, adjust all token positions
    if text != original_text:
        offset = 1  # Removed one '(' at start
        adjusted_tokens = []
        for token in tokens:
            # Only adjust if token starts at or after the removed '('
            if token["start"] >= offset:
                adjusted_tokens.append({
                    **token,
                    "start": token["start"] - offset,
                    "end": token["end"] - offset
                })
            elif token["end"] > offset:
                # Token spans the removed '(' - adjust partially
                adjusted_tokens.append({
                    **token,
                    "start": max(0, token["start"] - offset),
                    "end": token["end"] - offset,
                    "text": token["text"][offset:] if token["text"].startswith('(') else token["text"]
                })
            # Tokens before the removed '(' are not included
        tokens = adjusted_tokens
    
    # Build spans_map from tokens (one span per node_id)
    spans_map = {}
    for token in tokens:
        node_id = token["node_id"]
        if node_id not in spans_map:
            spans_map[node_id] = (token["start"], token["end"])
        else:
            # Extend span if token overlaps or is adjacent
            existing_start, existing_end = spans_map[node_id]
            spans_map[node_id] = (
                min(existing_start, token["start"]),
                max(existing_end, token["end"])
            )
    
    return text, spans_map


def find_subtree_span_by_path_cp(subtree_path: Path, full_tree: Any) -> Optional[Dict[str, int]]:
    """
    Find start/end position of subtree in pretty-printed string (code-points).
    Uses token-based mapping for accurate positioning.
    
    Args:
        subtree_path: Path to the subtree (list of (key, idx) tuples)
        full_tree: The full AST tree (normalized)
    
    Returns:
        {"start": int, "end": int} in code-points or None if not found
    """
    try:
        # Normalize tree
        if isinstance(full_tree, dict) and 'op' in full_tree:
            full_tree = normalize_bool_ast(full_tree)
        
        # Generate pretty string with tokens
        display_str, spans_map = pretty_with_tokens(full_tree)
        
        # Convert display_str to code-point array for accurate indexing
        display_arr = list(display_str)  # Array of code-points
        
        # Look up subtree path in spans_map (spans_map is in UTF-16 positions)
        node_id = str(subtree_path) if subtree_path else "root"
        
        utf16_start, utf16_end = None, None
        
        if node_id in spans_map:
            utf16_start, utf16_end = spans_map[node_id]
        else:
            # If exact path not found, try to find by walking the tree
            from .ast import iter_nodes, get_by_path
            
            try:
                subtree = get_by_path(full_tree, subtree_path)
                subtree_canon = canonical_str(subtree) if subtree is not None else None
                if subtree_canon:
                    for path, node in iter_nodes(full_tree):
                        if canonical_str(node) == subtree_canon:
                            test_node_id = str(path) if path else "root"
                            if test_node_id in spans_map:
                                utf16_start, utf16_end = spans_map[test_node_id]
                                break
            except (KeyError, IndexError, TypeError):
                pass
        
        if utf16_start is None or utf16_end is None:
            return None
        
        # Convert UTF-16 positions to code-point positions
        # We need to count code-points up to utf16_start and utf16_end
        cp_start = len(list(display_str[:utf16_start])) if utf16_start > 0 else 0
        cp_end = len(list(display_str[:utf16_end])) if utf16_end > 0 else 0
        
        return {"start": cp_start, "end": cp_end}
    except Exception:
        return None


# Keep old function for backward compatibility (deprecated)
def find_subtree_span_by_path(subtree_path: Path, full_tree: Any) -> Optional[Dict[str, int]]:
    """DEPRECATED: Use find_subtree_span_by_path_cp for code-point positions."""
    return find_subtree_span_by_path_cp(subtree_path, full_tree)


def find_subtree_position(subtree: Any, full_tree: Any) -> Optional[Dict[str, int]]:
    """
    Find start/end position of subtree in pretty-printed string of full tree.
    
    DEPRECATED: Use find_subtree_span_by_path() or find_subtree_span() for AST-based positioning.
    This function is kept for backward compatibility but uses improved logic.
    
    Returns None if not found or error.
    """
    try:
        # Normalize both trees
        if isinstance(subtree, dict) and 'op' in subtree:
            subtree = normalize_bool_ast(subtree)
        if isinstance(full_tree, dict) and 'op' in full_tree:
            full_tree = normalize_bool_ast(full_tree)
        
        # Use token-based approach
        display_str, spans_map = pretty_with_tokens(full_tree)
        
        # Find subtree by searching all nodes
        from .ast import iter_nodes
        subtree_canon = canonical_str(subtree)
        
        for path, node in iter_nodes(full_tree):
            if canonical_str(node) == subtree_canon:
                node_id = str(path) if path else "root"
                if node_id in spans_map:
                    start, end = spans_map[node_id]
                    return {"start": start, "end": end}
        
        # Fallback: try substring matching (less reliable)
        sub_canon = canonical_str(subtree)
        if sub_canon in display_str:
            start = display_str.find(sub_canon)
            return {"start": start, "end": start + len(sub_canon)}
        
        # Try without outer parentheses
        if sub_canon.startswith('(') and sub_canon.endswith(')'):
            sub_no_parens = sub_canon[1:-1]
            if sub_no_parens in display_str:
                start = display_str.find(sub_no_parens)
                return {"start": start, "end": start + len(sub_no_parens)}
        
        return None
    except Exception:
        return None

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


def _multiset_signature(items: Iterable[Any]) -> Dict[str, int]:
    sig: Dict[str, int] = {}
    for item in items:
        key = canon(item)
        sig[key] = sig.get(key, 0) + 1
    return sig


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
            
            # REMOVED: General _is_absorbed_by check - it was too broad and produced incorrect results
            # The correct absorption rules are checked below with specific conditions
            
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

            # Clause reduction: (x ∨ Y) ∧ (¬x ∨ Y) => Y
            or_args_indices = [(idx, a) for idx, a in enumerate(args) if isinstance(a, dict) and a.get("op") == "OR"]
            clause_reduced = False
            for (idx_a, or_a), (idx_b, or_b) in combinations(or_args_indices, 2):
                or_a_args = or_a.get("args", [])
                or_b_args = or_b.get("args", [])
                if len(or_a_args) < 2 or len(or_b_args) < 2:
                    continue
                for lit_idx_a, arg_a in enumerate(or_a_args):
                    lit_a = to_lit(arg_a)
                    if not lit_a:
                        continue
                    for lit_idx_b, arg_b in enumerate(or_b_args):
                        lit_b = to_lit(arg_b)
                        if not lit_b:
                            continue
                        if lit_a[0] != lit_b[0] or lit_a[1] == lit_b[1]:
                            continue

                        rest_a = [copy.deepcopy(x) for i, x in enumerate(or_a_args) if i != lit_idx_a]
                        rest_b = [copy.deepcopy(x) for i, x in enumerate(or_b_args) if i != lit_idx_b]
                        if not rest_a or _multiset_signature(rest_a) != _multiset_signature(rest_b):
                            continue

                        if len(rest_a) == 1:
                            y_part = rest_a[0]
                        else:
                            y_part = {"op": "OR", "args": rest_a}

                        new_and_args = [
                            copy.deepcopy(arg)
                            for k, arg in enumerate(args)
                            if k not in {idx_a, idx_b}
                        ]
                        new_and_args.append(y_part)

                        if not new_and_args:
                            after_node = y_part
                        elif len(new_and_args) == 1:
                            after_node = new_and_args[0]
                        else:
                            after_node = {"op": "AND", "args": new_and_args}

                        before_focus_paths = [
                            path + [("args", idx_a)],
                            path + [("args", idx_b)],
                        ]
                        if isinstance(after_node, dict) and after_node.get("op") == "AND":
                            after_focus_paths = [path + [("args", len(new_and_args) - 1)]]
                        else:
                            after_focus_paths = [path]

                        out.append({
                            "law": "Redukcja klauzul (x∨Y)∧(¬x∨Y)",
                            "path": path,
                            "before": sub,
                            "after": after_node,
                            "before_focus_paths": before_focus_paths,
                            "after_focus_paths": after_focus_paths,
                            "note": "Wspólna część Y zostaje.",
                        })

                        clause_reduced = True
                        break
                    if clause_reduced:
                        break
                if clause_reduced:
                    break
            if clause_reduced:
                continue

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
                            # Remove y from the OR args
                            new_args = [arg for arg in sub["args"] if arg is not y]
                            after = new_args[0] if len(new_args) == 1 else {"op": "OR", "args": new_args}
                            out.append({
                                "law": "Absorpcja (∨)",
                                "path": path,
                                "before": sub,
                                "after": after,
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
                            # Remove y from the AND args
                            new_args = [arg for arg in sub["args"] if arg is not y]
                            after = new_args[0] if len(new_args) == 1 else {"op": "AND", "args": new_args}
                            out.append({
                                "law": "Absorpcja (∧)",
                                "path": path,
                                "before": sub,
                                "after": after,
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
                        if not R1:  # S jest podzbiorem T (S has no extra vars beyond T)
                            # Keep S (the smaller subset term)
                            after = sub["args"][i]
                        else:  # T jest podzbiorem S (T has no extra vars beyond S)
                            # Keep T (the smaller subset term)
                            after = sub["args"][j]
                        
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
                and_indices = [idx for idx, a in enumerate(args) if isinstance(a, dict) and a.get("op") == "AND"]
                if len(and_indices) >= 2:
                    and_args = [args[idx] for idx in and_indices]
                    # Znajdź wspólne czynniki w AND argumentach
                    for i in range(len(and_indices)):
                        for j in range(i + 1, len(and_indices)):
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
                                    # Usuń indeksy and_indices[i] i and_indices[j] z args
                                    indices_to_remove = [and_indices[i], and_indices[j]]
                                    other_args = [arg for idx, arg in enumerate(args) if idx not in indices_to_remove]
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
    
    # Rule priority: contradictions/neutrality > distribution > absorption > factoring > consensus > other
    def rule_priority(rule_name: str) -> int:
        # Highest priority: rules that eliminate contradictions or neutral elements
        if "Kontradykcja" in rule_name or "Dopełnienie" in rule_name or "Element neutralny" in rule_name:
            return 1
        # Second: rules that eliminate negations
        elif "Podwójna negacja" in rule_name:
            return 2
        # Third: absorption (direct simplification)
        elif "Absorpcja" in rule_name:
            return 3
        # Fourth: distribution/expansion
        elif "Dystrybutywność" in rule_name or "Rozdzielność" in rule_name:
            return 4
        # Fifth: De Morgan (simplifies structure)
        elif "De Morgan" in rule_name:
            return 5
        # Sixth: factoring (often worsens form)
        elif "Faktoryzacja" in rule_name:
            return 6
        # Seventh: consensus (buggy, filtered by TT verification)
        elif "Konsensus" in rule_name:
            return 7
        else:
            return 8
    
    best: Optional[Dict[str, Any]] = None
    best_measure = None
    best_priority = None
    
    for m in matches:
        after = m["after"]
        after_measure = measure(after)
        priority = rule_priority(m.get("law", ""))
        
        if best is None:
            best = m
            best_measure = after_measure
            best_priority = priority
            continue
            
        # Primary: prefer higher priority (lower number)
        if priority < best_priority:
            best = m
            best_measure = after_measure
            best_priority = priority
        elif priority == best_priority:
            # Secondary: prefer smaller measure
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

        # Generate pretty strings for display
        before_str, before_spans_map = pretty_with_tokens(node_backup)
        
        # Compute canonical strings and highlight spans for BEFORE state
        before_canon = canonical_str(node_backup)
        before_sub_canon = canonical_str(sub_before)
        # Use path-based span lookup for accurate positioning
        before_highlight_span = find_subtree_span_by_path(path, node_backup)
        
        # Calculate before_highlight_spans_cp
        before_highlight_spans_cp = []
        if before_highlight_span:
            before_highlight_spans_cp.append((before_highlight_span["start"], before_highlight_span["end"]))
        
        node = set_by_path(node, path, sub_after)
        node = normalize_bool_ast(node)
        
        # Generate pretty string for AFTER state
        after_str, after_spans_map = pretty_with_tokens(node)

        # Compute canonical strings and highlight spans for AFTER state
        after_canon = canonical_str(node)
        after_sub_canon = canonical_str(sub_after)
        
        # Find sub_after in node after normalization using canonical comparison
        # This ensures we find the correct transformed subexpression, not just the node at path
        after_highlight_span = None
        after_highlight_spans_cp = []
        sub_after_normalized = normalize_bool_ast(sub_after, expand_imp_iff=True)
        sub_after_canon_search = canonical_str(sub_after_normalized)
        
        # Search for sub_after in node using canonical comparison
        for after_path, after_node in iter_nodes(node):
            after_node_canon = canonical_str(after_node)
            if after_node_canon == sub_after_canon_search:
                # Found it - get span
                after_span = find_subtree_span_by_path_cp(after_path, node)
                if after_span:
                    span_start = after_span["start"]
                    span_end = after_span["end"]
                    
                    # Check if sub_after is a simple variable or constant
                    # If so, don't extend with parentheses
                    is_simple_node = (
                        isinstance(sub_after, dict) and 
                        sub_after.get("op") in {"VAR", "CONST"}
                    )
                    
                    if is_simple_node:
                        # For simple nodes, use the span directly without extending
                        after_highlight_spans_cp.append((span_start, span_end))
                        after_highlight_span = {"start": span_start, "end": span_end}
                    else:
                        # For complex nodes, extend span to include outer parentheses if needed
                        merged_start = span_start
                        for i in range(span_start - 1, -1, -1):
                            if after_str[i] == '(':
                                merged_start = i
                                break
                        
                        merged_end = span_end
                        for i in range(span_end, len(after_str)):
                            if after_str[i] == ')':
                                merged_end = i + 1
                                break
                        
                        after_highlight_spans_cp.append((merged_start, merged_end))
                        after_highlight_span = {"start": merged_start, "end": merged_end}
                    break
        
        # Fallback: if not found, use path-based lookup
        if not after_highlight_span:
            after_highlight_span = find_subtree_span_by_path(path, node)
            if after_highlight_span:
                after_highlight_spans_cp.append((after_highlight_span["start"], after_highlight_span["end"]))
        
        # Also set before_highlight_spans_cp for oscillation step
        before_highlight_spans_cp_osc = []
        if before_highlight_span:
            before_highlight_spans_cp_osc.append((before_highlight_span["start"], before_highlight_span["end"]))
        after_highlight_spans_cp_osc = []
        if after_highlight_span:
            after_highlight_spans_cp_osc.append((after_highlight_span["start"], after_highlight_span["end"]))
        
        # Check for oscillation - use canonical_str for structural comparison
        if after_canon in seen_expressions:
            steps.append({
                "law": "Zatrzymano (oscylacja)",
                "note": "Wykryto oscylację - system zatrzymany",
                "path": path,
                "before_tree": before_str,
                "after_tree": after_str,
                "before_str": before_str,
                "after_str": after_str,
                "before_subexpr": pretty(sub_before),
                "after_subexpr": pretty(sub_after),
                "before_canon": before_canon,
                "after_canon": after_canon,
                "before_subexpr_canon": before_sub_canon,
                "after_subexpr_canon": after_sub_canon,
                "before_span": before_highlight_span,
                "after_span": after_highlight_span,
                "before_highlight_span": before_highlight_span,
                "after_highlight_span": after_highlight_span,
                "before_highlight_spans_cp": before_highlight_spans_cp_osc if len(before_highlight_spans_cp_osc) > 0 else None,
                "after_highlight_spans_cp": after_highlight_spans_cp_osc if len(after_highlight_spans_cp_osc) > 0 else None,
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
        # EXCEPTION: Distribution/Expansion (priority 1 rules) can increase literals temporarily
        is_worse = False
        if choice.get("source") != "axiom":
            law_name = choice.get("law", "")
            is_expansion_rule = ("Dystrybutywność" in law_name or "Rozdzielność" in law_name)
            
            if after_full_measure[0] > before_full_measure[0]:
                # More literals - normally worse
                # But allow it for expansion rules (they may be necessary for DNF)
                if not is_expansion_rule:
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
        if after_canon in seen_expressions and choice.get("source") != "axiom":
            # We've seen this result before - don't repeat
            sub_before_canon = canonical_str(sub_before)
            sub_after_canon = canonical_str(sub_after)
            skipped_transformations.add((sub_before_canon, sub_after_canon, choice.get("law")))
            node = node_backup
            continue

        seen_expressions.add(after_canon)

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
            "before_str": before_str,  # Explicit field for frontend
            "after_str": after_str,    # Explicit field for frontend
            "before_subexpr": pretty(sub_before),
            "after_subexpr": pretty(sub_after),
            "before_canon": before_canon,
            "after_canon": after_canon,
            "before_subexpr_canon": before_sub_canon,
            "after_subexpr_canon": after_sub_canon,
            "before_span": before_highlight_span,  # Span relative to before_str
            "after_span": after_highlight_span,    # Span relative to after_str
            "before_highlight_span": before_highlight_span,  # Keep for backward compatibility
            "after_highlight_span": after_highlight_span,     # Keep for backward compatibility
            "before_highlight_spans_cp": before_highlight_spans_cp if len(before_highlight_spans_cp) > 0 else None,
            "after_highlight_spans_cp": after_highlight_spans_cp if len(after_highlight_spans_cp) > 0 else None,
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
    
    # Generate pretty strings for display with token mapping
    before_str, before_spans_map = pretty_with_tokens(node)
    
    # Compute canonical strings and highlight spans
    before_canon = canonical_str(node)
    before_sub_canon = canonical_str(choice["before"])
    # Use path-based span lookup for accurate positioning
    before_highlight_span = find_subtree_span_by_path(path, node)

    node = set_by_path(node, path, choice["after"])
    node = normalize_bool_ast(node)
    
    # Generate pretty string for AFTER state
    after_str, after_spans_map = pretty_with_tokens(node)
    
    # Compute canonical strings and highlight spans for AFTER state
    after_canon = canonical_str(node)
    after_sub_canon = canonical_str(choice["after"])
    # For after, the subtree is at the same path (we replaced it)
    after_highlight_span = find_subtree_span_by_path(path, node)

    return {
        "ok": True,
        "applied_law": choice["law"],
        "note": choice.get("note", ""),
        "path": path,
        "before_tree": before_str,
        "after_tree": after_str,
        "before_str": before_str,
        "after_str": after_str,
        "before_subexpr": pretty(choice["before"]),
        "after_subexpr": pretty(choice["after"]),
        "before_canon": before_canon,
        "after_canon": after_canon,
        "before_subexpr_canon": before_sub_canon,
        "after_subexpr_canon": after_sub_canon,
        "before_span": before_highlight_span,
        "after_span": after_highlight_span,
        "before_highlight_span": before_highlight_span,
        "after_highlight_span": after_highlight_span,
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
