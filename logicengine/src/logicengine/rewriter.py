from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Union
import copy
import hashlib

from .rules import Rule, Pattern, Var
from .ast import normalize_bool_ast, canonical_str, equals

@dataclass
class Match:
    match_id: str
    path: List[int]
    bindings: Dict[str, Any]
    preview_ast: Any
    focus_expr: Any

def _match_node(pat: Union[Pattern, Var], node: Any, bindings: Dict[str, Any]) -> bool:
    # node is assumed normalized
    if isinstance(pat, Var):
        name = pat.name
        if name in bindings:
            return equals(bindings[name], node)
        bindings[name] = node
        return True

    if not isinstance(pat, Pattern):
        return False

    if pat.op == 'VAR':
        if isinstance(node, dict) and node.get('op') == 'VAR':
            if len(pat.args) == 1 and isinstance(pat.args[0], str):
                return node.get('name') == pat.args[0]
        return False

    if pat.op == 'CONST':
        if isinstance(node, dict) and node.get('op') == 'CONST':
            if len(pat.args) == 1 and pat.args[0] in {0, 1}:
                return node.get('value') == pat.args[0]
        return False

    if pat.op == 'NOT':
        if not (isinstance(node, dict) and node.get('op') == 'NOT'):
            return False
        return _match_node(pat.args[0], node.get('child'), bindings)

    if pat.op in {'AND', 'OR'}:
        if not (isinstance(node, dict) and node.get('op') == pat.op):
            return False
        targets = node.get('args', [])
        pat_args = list(pat.args)
        used = [False] * len(targets)

        def backtrack(i: int) -> bool:
            if i == len(pat_args):
                return True
            for j, t in enumerate(targets):
                if used[j]:
                    continue
                saved = dict(bindings)
                if _match_node(pat_args[i], t, bindings):
                    used[j] = True
                    if backtrack(i + 1):
                        return True
                # restore
                bindings.clear()
                bindings.update(saved)
                used[j] = False
            return False

        return backtrack(0)

    return False

def _substitute(rhs: Union[Pattern, Var], bindings: Dict[str, Any]) -> Any:
    if isinstance(rhs, Var):
        return bindings[rhs.name]
    if isinstance(rhs, Pattern):
        if rhs.op == 'NOT':
            return {'op': 'NOT', 'child': _substitute(rhs.args[0], bindings)}
        if rhs.op in {'AND', 'OR'}:
            return {'op': rhs.op, 'args': [_substitute(a, bindings) for a in rhs.args]}
        if rhs.op == 'VAR':
            return {'op': 'VAR', 'name': rhs.args[0] if rhs.args else '?'}
        if rhs.op == 'CONST':
            return {'op': 'CONST', 'value': rhs.args[0] if rhs.args else 0}
    raise ValueError('Unsupported RHS in substitute')

def _get_subtree(node: Any, path: List[int]) -> Any:
    cur = node
    for idx in path:
        if isinstance(cur, dict) and cur.get('op') in {'AND', 'OR'}:
            cur = cur.get('args')[idx]
        elif isinstance(cur, dict) and cur.get('op') == 'NOT':
            cur = cur.get('child')
        else:
            raise IndexError('Invalid path during get')
    return cur

def _set_subtree(node: Any, path: List[int], new_sub: Any) -> Any:
    if not path:
        return new_sub
    cur = copy.deepcopy(node)
    ref = cur
    for i, idx in enumerate(path):
        if i == len(path) - 1:
            if ref.get('op') in {'AND', 'OR'}:
                ref['args'][idx] = new_sub
            elif ref.get('op') == 'NOT':
                ref['child'] = new_sub
            else:
                raise IndexError('Invalid path target')
            break
        if ref.get('op') in {'AND', 'OR'}:
            ref = ref['args'][idx]
        elif ref.get('op') == 'NOT':
            ref = ref['child']
        else:
            raise IndexError('Invalid path descend')
    return cur

def _walk(node: Any, path_prefix: List[int], out: List[Tuple[List[int], Any]]):
    out.append((path_prefix, node))
    if isinstance(node, dict):
        if node.get('op') in {'AND', 'OR'}:
            for i, child in enumerate(node.get('args', [])):
                _walk(child, path_prefix + [i], out)
        elif node.get('op') == 'NOT':
            _walk(node.get('child'), path_prefix + [0], out)

def find_matches(rule: Rule, ast_node: Any) -> List[Match]:
    root = normalize_bool_ast(ast_node)
    locations: List[Tuple[List[int], Any]] = []
    _walk(root, [], locations)
    seen = set()
    matches: List[Match] = []
    for path, sub in locations:
        bindings: Dict[str, Any] = {}
        if _match_node(rule.lhs, sub, bindings):
            rhs_sub = _substitute(rule.rhs, bindings)
            after = _set_subtree(root, path, rhs_sub)
            after_norm = normalize_bool_ast(after)

            focus_can = canonical_str(sub)
            after_can = canonical_str(after_norm)
            stable_key = f"{rule.id}|{'/'.join(map(str, path))}|{focus_can}|{after_can}"
            match_id = hashlib.sha1(stable_key.encode('utf-8')).hexdigest()

            key = (tuple(path), after_can)
            if key in seen:
                continue
            seen.add(key)

            matches.append(Match(
                match_id=match_id,
                path=path,
                bindings=bindings,
                preview_ast=after_norm,
                focus_expr=sub,
            ))
    return matches

def apply_match(rule: Rule, ast_node: Any, match: Match) -> Any:
    root = normalize_bool_ast(ast_node)
    recomputed = [m for m in find_matches(rule, ast_node) if m.match_id == match.match_id]
    if not recomputed:
        raise ValueError('Match no longer valid')
    m = recomputed[0]
    rhs_sub = _substitute(rule.rhs, m.bindings)
    after = _set_subtree(root, m.path, rhs_sub)
    return normalize_bool_ast(after)
