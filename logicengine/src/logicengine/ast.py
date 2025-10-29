# ast.py
"""AST generation and normalization for logical expressions."""

import logging
from typing import Any, Dict, List, Optional

from .parser import LogicParser, LogicExpressionError

logger = logging.getLogger(__name__)


class ASTError(Exception):
    pass


# Pratt parser config
PRECEDENCE: Dict[str, int] = {
    '¬': 5, '∧': 4, '∨': 3, '⊕': 3, '↑': 3, '↓': 3, '→': 2, '↔': 1, '≡': 1,
}
RIGHT_ASSOC = {'¬', '→', '↔', '≡'}
BINARY_OPS = {'∧', '∨', '→', '↔', '⊕', '↑', '↓', '≡'}


class TokenStream:
    def __init__(self, s: str):
        self.s = s
        self.i = 0

    def peek(self) -> str:
        return self.s[self.i] if self.i < len(self.s) else ''

    def next(self) -> str:
        ch = self.peek()
        if ch:
            self.i += 1
        return ch

    def eof(self) -> bool:
        return self.i >= len(self.s)


def parse_expression(ts: TokenStream, min_prec: int = 0) -> Any:
    """Pratt parser. Nodes:
       - unary:  {'node':'¬','child':...}
       - binary: {'node':OP,'left':...,'right':...}
       - leaf:   'A' / '0' / '1'
    """
    ch = ts.peek()
    if ch == '':
        raise ASTError("Nieoczekiwany koniec wyrażenia")

    if ch == '¬':  # unary NOT
        ts.next()
        node: Any = {"node": '¬', "child": parse_expression(ts, PRECEDENCE['¬'])}
    elif ch == '(':
        ts.next()
        node = parse_expression(ts, 0)
        if ts.next() != ')':
            raise ASTError("Brak zamykającego nawiasu")
    else:
        if ch.isalpha() or ch in '01':
            node = ch
            ts.next()
        else:
            raise ASTError(f"Nieprawidłowy token: {ch}")

    while True:  # binary chaining with precedence/associativity
        op = ts.peek()
        if op not in PRECEDENCE or op == '¬':
            break
        prec = PRECEDENCE[op]
        if prec < min_prec:
            break
        ts.next()
        next_min = prec + (0 if op in RIGHT_ASSOC else 1)
        rhs = parse_expression(ts, next_min)
        node = {"node": op, "left": node, "right": rhs}
    return node


# --- Canonicalization helpers (defensive) ---

def _guess_unary_child(raw: Dict[str, Any]) -> Optional[Any]:
    for key in ('child', 'right', 'left', 'operand', 'arg', 'argument', 'expr'):
        if key in raw and raw[key] is not None:
            return raw[key]
    ch = raw.get('children')
    if isinstance(ch, list) and ch:
        return ch[0]
    for v in raw.values():
        if isinstance(v, dict) and (v.get('node') or v.get('left') or v.get('right') or v.get('child')):
            return v
        if isinstance(v, list):
            for it in v:
                if isinstance(it, dict) and (it.get('node') or it.get('left') or it.get('right') or it.get('child')):
                    return it
        if isinstance(v, str) and (v in ('0', '1') or v.isalpha()):
            return v
    return None


def _canonicalize(node: Any) -> Any:
    """Convert unknown shapes to the canonical shape used by parse_expression()."""
    if node is None:
        return None
    if isinstance(node, str):
        if node not in {'0', '1'} and not node.isalpha():
            return node
        return node
    if not isinstance(node, dict):
        return node

    op = node.get('node')

    if op == '¬':
        return {"node": '¬', "child": _canonicalize(_guess_unary_child(node))}

    if op in BINARY_OPS:
        left = node.get('left')
        right = node.get('right')
        ch = node.get('children')
        if (left is None or right is None) and isinstance(ch, list):
            if left is None and len(ch) >= 1:
                left = ch[0]
            if right is None and len(ch) >= 2:
                right = ch[1]
        return {"node": op, "left": _canonicalize(left), "right": _canonicalize(right)}

    if 'children' in node and isinstance(node['children'], list) and node['children']:
        kids = [_canonicalize(k) for k in node['children']]
        if len(kids) == 1:
            return {"node": '¬', "child": kids[0]}
        if len(kids) >= 2:
            return {"node": '∧', "left": kids[0], "right": kids[1]}

    return str(node)

def generate_ast(expr: str) -> Dict[str, Any]:
    """Return canonical AST for UI rendering."""
    try:
        std = LogicParser.parse(expr)
    except LogicExpressionError as e:
        logger.error(f"Parser error: {e}")
        raise ASTError(str(e))

    try:
        ts = TokenStream(std)
        raw_ast = parse_expression(ts, 0)
        if not ts.eof():
            raise ASTError("Nieoczekiwane znaki po wyrażeniu")
        return _canonicalize(raw_ast)
    except ASTError:
        raise
    except Exception as e:
        logger.error(f"AST generation error: {e}")
        raise ASTError(str(e))


# --- Boolean-only normalized representation ---

def _to_bool_norm(node: Any) -> Any:
    """Map canonical/legacy shapes to boolean-only form."""
    if node is None:
        return None

    if isinstance(node, str):
        if node in {'0', '1'}:
            return {'op': 'CONST', 'value': int(node)}
        if node.isalpha():
            return {'op': 'VAR', 'name': node}
        return node

    if not isinstance(node, dict):
        return node

    if 'node' in node:
        op = node['node']
        if op == '¬':
            return {'op': 'NOT', 'child': _to_bool_norm(_guess_unary_child(node))}
        if op in {'∧', '∨'}:
            left = _to_bool_norm(node.get('left'))
            right = _to_bool_norm(node.get('right'))
            return {'op': 'AND', 'args': [left, right]} if op == '∧' else {'op': 'OR', 'args': [left, right]}
        if op == '→':
            left = _to_bool_norm(node.get('left'))
            right = _to_bool_norm(node.get('right'))
            return {'op': 'IMP', 'left': left, 'right': right}
        if op in {'↔', '≡'}:
            left = _to_bool_norm(node.get('left'))
            right = _to_bool_norm(node.get('right'))
            return {'op': 'IFF', 'left': left, 'right': right}
        left = _to_bool_norm(node.get('left'))
        right = _to_bool_norm(node.get('right'))
        return {'op': op, 'left': left, 'right': right}

    if 'op' in node:
        op = node['op']
        if op == 'NOT':
            return {'op': 'NOT', 'child': _to_bool_norm(node.get('child'))}
        if op in {'AND', 'OR'}:
            return {'op': op, 'args': [_to_bool_norm(a) for a in node.get('args', [])]}
        if op == 'VAR':
            return {'op': 'VAR', 'name': node.get('name')}
        if op == 'CONST':
            return {'op': 'CONST', 'value': node.get('value')}

    return node


def _flatten_sort_dedupe(node: Any) -> Any:
    """Flatten AND/OR, sort, and remove duplicates."""
    if not isinstance(node, dict) or 'op' not in node:
        return node

    op = node['op']
    if op in {'AND', 'OR'}:
        args: List[Any] = node.get('args', [])
        if not args:
            return node

        flat: List[Any] = []
        for arg in args:
            a = _flatten_sort_dedupe(arg)
            if isinstance(a, dict) and a.get('op') == op:
                flat.extend(a.get('args', []))
            else:
                flat.append(a)

        unique: List[Any] = []
        for a in flat:
            if not any(equals(a, ex) for ex in unique):
                unique.append(a)

        # Sort with stable, deterministic ordering that preserves relative positions
        # when possible, while ensuring consistency across transformations
        def sort_key(x: Any) -> tuple:
            """Sort key for consistent ordering"""
            canon = canonical_str(x)
            
            # Type-based ordering for consistency:
            # For AND: CONST(1) at end, then other elements
            # For OR: CONST(0) at start, then other elements  
            # Within same type: sort alphabetically/structurally
            type_priority = 0
            secondary_key = ''
            
            if isinstance(x, dict) and 'op' in x:
                x_op = x['op']
                if x_op == 'CONST':
                    val = x.get('value', 0)
                    # For AND: 1 comes last. For OR: 0 comes first
                    if op == 'AND':
                        type_priority = 100 if val == 1 else 50
                    else:  # OR (op == 'OR')
                        type_priority = 0 if val == 0 else 50
                    secondary_key = str(val)
                elif x_op == 'VAR':
                    type_priority = 10
                    secondary_key = x.get('name', '?')
                elif x_op == 'NOT':
                    type_priority = 20
                    child = x.get('child', {})
                    if isinstance(child, dict) and child.get('op') == 'VAR':
                        secondary_key = child.get('name', '?')
                    else:
                        secondary_key = canonical_str(child)
                elif x_op == 'AND':
                    type_priority = 30
                    # For AND, sort args and use as key
                    args = x.get('args', [])
                    args_keys = sorted(canonical_str(a) for a in args)
                    secondary_key = ','.join(args_keys)
                elif x_op == 'OR':
                    type_priority = 40
                    # For OR, sort args and use as key
                    args = x.get('args', [])
                    args_keys = sorted(canonical_str(a) for a in args)
                    secondary_key = ','.join(args_keys)
                else:
                    type_priority = 99
                    secondary_key = str(x)
            else:
                type_priority = 99
                secondary_key = str(x)
            
            return (type_priority, secondary_key, canon)
        
        unique.sort(key=sort_key)
        return {'op': op, 'args': unique}

    if 'child' in node:
        node['child'] = _flatten_sort_dedupe(node['child'])
    if 'left' in node:
        node['left'] = _flatten_sort_dedupe(node['left'])
    if 'right' in node:
        node['right'] = _flatten_sort_dedupe(node['right'])
    if 'args' in node:
        node['args'] = [_flatten_sort_dedupe(a) for a in node['args']]
    return node


def _expand_imp_iff(ast: Any) -> Any:
    """Expand IMP and IFF operators to basic NOT/AND/OR."""
    if not isinstance(ast, dict) or 'op' not in ast:
        return ast
    
    op = ast['op']
    
    if op == 'IMP':
        # p -> q becomes ~p | q
        left = _expand_imp_iff(ast['left'])
        right = _expand_imp_iff(ast['right'])
        return {'op': 'OR', 'args': [{'op': 'NOT', 'child': left}, right]}
    
    elif op == 'IFF':
        # p <-> q becomes (p & q) | (~p & ~q)
        left = _expand_imp_iff(ast['left'])
        right = _expand_imp_iff(ast['right'])
        return {
            'op': 'OR',
            'args': [
                {'op': 'AND', 'args': [left, right]},
                {'op': 'AND', 'args': [
                    {'op': 'NOT', 'child': left},
                    {'op': 'NOT', 'child': right}
                ]}
            ]
        }
    
    # Recursively process other operators
    result = ast.copy()
    if 'left' in ast:
        result['left'] = _expand_imp_iff(ast['left'])
    if 'right' in ast:
        result['right'] = _expand_imp_iff(ast['right'])
    if 'child' in ast:
        result['child'] = _expand_imp_iff(ast['child'])
    if 'args' in ast:
        result['args'] = [_expand_imp_iff(arg) for arg in ast['args']]
    
    return result


def normalize_bool_ast(ast: Any, expand_imp_iff: bool = True) -> Any:
    """Boolean-only form with flattened n-ary operators."""
    if expand_imp_iff:
        ast = _expand_imp_iff(ast)
    ast = _to_bool_norm(ast)
    if expand_imp_iff:
        ast = _expand_imp_iff(ast)  # Expand again after _to_bool_norm creates IFF/IMP
    return _flatten_sort_dedupe(ast)


def canonical_str(node: Any) -> str:
    """Canonical string for structural compare/sort."""
    if node is None:
        return '?'
    if isinstance(node, str):
        return node
    if not isinstance(node, dict):
        return str(node)

    if 'op' in node:
        op = node['op']
        if op == 'NOT':
            return f"¬({canonical_str(node.get('child'))})"
        if op in {'AND', 'OR'}:
            args = node.get('args', [])
            if not args:
                return '?'
            symbol = '∧' if op == 'AND' else '∨'
            return f"({symbol.join(canonical_str(a) for a in args)})"
        if op == 'VAR':
            return node.get('name', '?')
        if op == 'CONST':
            return str(node.get('value', '?'))
        left = canonical_str(node.get('left'))
        right = canonical_str(node.get('right'))
        return f"({left} {op} {right})"

    if 'node' in node:
        op = node['node']
        if op == '¬':
            return f"¬({canonical_str(_guess_unary_child(node))})"
        if op in {'∧', '∨', '→', '↔', '⊕', '↑', '↓', '≡'}:
            left = canonical_str(node.get('left'))
            right = canonical_str(node.get('right'))
            return f"({left} {op} {right})"

    return str(node)


def canonical_str_minimal(node: Any, parent_precedence: int = 0) -> str:
    """Minimal string representation with fewer parentheses based on operator precedence.
    
    Precedence: NOT (100) > AND (2) > OR (3) > other (10)
    Lower precedence value = higher priority.
    """
    if node is None:
        return '?'
    if isinstance(node, str):
        return node
    if not isinstance(node, dict):
        return str(node)
    
    try:
        return _canonical_str_minimal_internal(node, parent_precedence)
    except (RecursionError, MemoryError):
        return canonical_str(node)


def _canonical_str_minimal_internal(node: Any, parent_precedence: int = 0) -> str:
    if node is None:
        return '?'
    if isinstance(node, str):
        return node
    if not isinstance(node, dict):
        return str(node)

    op_map = {
        'NOT': ('¬', 100),
        'AND': ('∧', 2),
        'OR': ('∨', 3),
    }
    
    if 'op' in node:
        op = node['op']
        
        # Variable or constant
        if op == 'VAR':
            return node.get('name', '?')
        if op == 'CONST':
            return str(node.get('value', '?'))
        
        symbol, my_prec = op_map.get(op, (op, 10))
        
        if op == 'NOT':
            child = _canonical_str_minimal_internal(node.get('child'), my_prec)
            if isinstance(child, str) and len(child) == 1 and child.isupper():
                result = f"¬{child}"
            elif isinstance(child, str) and not child.startswith('(') and not ' ' in child:
                result = f"¬{child}"
            elif isinstance(child, str) and child.startswith('(') and child.endswith(')') and len(child) == 3:
                result = f"¬{child[1:-1]}"
            elif isinstance(child, str) and not child.startswith('(') and ' ' in child and not child.startswith('¬'):
                result = f"¬({child})"
            else:
                result = f"¬{child}"
            return result if parent_precedence <= 0 or my_prec < parent_precedence else f"({result})"
        
        if op in {'AND', 'OR'}:
            args = node.get('args', [])
            if not args:
                return '?'
            
            def get_arg_precedence(arg_node):
                if not isinstance(arg_node, dict) or 'op' not in arg_node:
                    return None
                arg_op = arg_node.get('op')
                return op_map.get(arg_op, ('', 10))[1] if arg_op in {'NOT', 'AND', 'OR'} else None
            
            parts = []
            for arg in args:
                arg_prec = get_arg_precedence(arg)
                arg_parent_prec = my_prec if arg_prec is None or arg_prec >= my_prec else 0
                arg_str = _canonical_str_minimal_internal(arg, arg_parent_prec)
                parts.append(arg_str)
            
            inner = f" {symbol} ".join(parts)
            
            if parent_precedence <= 0:
                return inner
            elif my_prec < parent_precedence:
                return inner
            else:
                return f"({inner})"
        
        left = _canonical_str_minimal_internal(node.get('left'), 10)
        right = _canonical_str_minimal_internal(node.get('right'), 10)
        result = f"{left} {op} {right}"
        if parent_precedence <= 0:
            return result
        return f"({result})"

    if 'node' in node:
        op = node['node']
        symbol, my_prec = op_map.get(op, (op, 10))
        
        if op == '¬':
            child = _canonical_str_minimal_internal(_guess_unary_child(node), my_prec)
            if isinstance(child, str) and not child.startswith('(') and ' ' in child and not child.startswith('¬'):
                result = f"¬({child})"
            else:
                result = f"¬{child}"
            return result if parent_precedence <= 0 or my_prec < parent_precedence else f"({result})"
        
        if op in {'∧', '∨', '→', '↔', '⊕', '↑', '↓', '≡'}:
            my_prec = 2 if op == '∧' else 3 if op == '∨' else 10
            left = _canonical_str_minimal_internal(node.get('left'), my_prec)
            right = _canonical_str_minimal_internal(node.get('right'), my_prec)
            
            result = f"{left} {op} {right}"
            if parent_precedence <= 0 or my_prec < parent_precedence:
                return result
            return f"({result})"

    return str(node)


def equals(a: Any, b: Any) -> bool:
    """Structural equality via canonical_str."""
    if a is None or b is None:
        return a is b
    if isinstance(a, str) or isinstance(b, str):
        return a == b
    if not isinstance(a, dict) or not isinstance(b, dict):
        return a == b
    return canonical_str(a) == canonical_str(b)
