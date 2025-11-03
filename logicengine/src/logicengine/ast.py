# ast.py
"""AST generation and normalization for logical expressions."""

import logging
from typing import Any, Dict, List, Optional, Tuple

from .parser import LogicParser, LogicExpressionError

logger = logging.getLogger(__name__)

Path = List[Tuple[str, Optional[int]]]  # ('args', i) or ('child', None)


class ASTError(Exception):
    pass


# Pratt parser config
PRECEDENCE: Dict[str, int] = {
    '¬': 5, '∧': 4, '↑': 4, '∨': 3, '⊕': 3, '↓': 3, '→': 2, '↔': 1, '≡': 1,
}
RIGHT_ASSOC = {'→'}  # Removed ¬, ↔, ≡ as per requirements
BINARY_OPS = {'∧', '∨', '→', '↔', '⊕', '↑', '↓', '≡'}


class TokenStream:
    def __init__(self, s: str):
        self.s = s
        self.i = 0

    def _skip_whitespace(self) -> None:
        """Skip whitespace characters."""
        while self.i < len(self.s) and self.s[self.i].isspace():
            self.i += 1

    def peek(self) -> str:
        self._skip_whitespace()
        return self.s[self.i] if self.i < len(self.s) else ''

    def next(self) -> str:
        self._skip_whitespace()
        ch = self.peek()
        if ch:
            self.i += 1
        return ch

    def eof(self) -> bool:
        self._skip_whitespace()
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
        # Only allow A-Z and 0/1 (strict validation)
        if (ch >= 'A' and ch <= 'Z') or ch in '01':
            node = ch
            ts.next()
        else:
            raise ASTError(f"Nieprawidłowy token: {ch} (dozwolone tylko A-Z i 0/1)")

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
            # Return the single child without guessing operator
            return kids[0]
        if len(kids) > 1:
            # Don't guess operator - raise error for ambiguous structure
            raise ASTError(f"Nie można określić operatora dla {len(kids)} dzieci: {kids}")

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

        # Constant folding rules:
        # For AND: if CONST(0) exists, result is CONST(0); remove CONST(1)
        # For OR: if CONST(1) exists, result is CONST(1); remove CONST(0)
        if op == 'AND':
            has_zero = any(isinstance(a, dict) and a.get('op') == 'CONST' and a.get('value') == 0 for a in unique)
            if has_zero:
                return {'op': 'CONST', 'value': 0}
            # Remove CONST(1) from arguments
            unique = [a for a in unique if not (isinstance(a, dict) and a.get('op') == 'CONST' and a.get('value') == 1)]
            if not unique:
                return {'op': 'CONST', 'value': 1}  # All were CONST(1)
        
        if op == 'OR':
            has_one = any(isinstance(a, dict) and a.get('op') == 'CONST' and a.get('value') == 1 for a in unique)
            if has_one:
                return {'op': 'CONST', 'value': 1}
            # Don't remove CONST(0) here - let laws_matches handle it as "Element neutralny (A∨0)"
            # This allows showing the explicit transformation A∨0 → A
            # unique = [a for a in unique if not (isinstance(a, dict) and a.get('op') == 'CONST' and a.get('value') == 0)]
            # if not unique:
            #     return {'op': 'CONST', 'value': 0}  # All were CONST(0)

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
        
        # If only one element remains, return it directly (not wrapped in AND/OR)
        if len(unique) == 1:
            return unique[0]
        
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
    """Expand IMP and IFF operators to basic NOT/AND/OR.
    Also handles legacy format with 'node': '→'/'↔'.
    """
    if not isinstance(ast, dict):
        return ast
    
    # Handle legacy format: {'node': '→', 'left': ..., 'right': ...}
    if 'node' in ast:
        node_op = ast.get('node')
        if node_op == '→':
            left = _expand_imp_iff(ast.get('left'))
            right = _expand_imp_iff(ast.get('right'))
            return {'op': 'OR', 'args': [{'op': 'NOT', 'child': left}, right]}
        elif node_op in {'↔', '≡'}:
            left = _expand_imp_iff(ast.get('left'))
            right = _expand_imp_iff(ast.get('right'))
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
        # For other node types, continue recursive processing
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
    
    # Handle normalized format: {'op': 'IMP'/'IFF', ...}
    if 'op' not in ast:
        return ast
    
    op = ast['op']
    
    if op == 'IMP':
        # p -> q becomes ~p | q
        left = _expand_imp_iff(ast.get('left'))
        right = _expand_imp_iff(ast.get('right'))
        return {'op': 'OR', 'args': [{'op': 'NOT', 'child': left}, right]}
    
    elif op == 'IFF':
        # p <-> q becomes (p & q) | (~p & ~q)
        left = _expand_imp_iff(ast.get('left'))
        right = _expand_imp_iff(ast.get('right'))
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


def _expand_derived_ops(ast: Any) -> Any:
    """Expand derived operators (⊕, ↑, ↓) to basic NOT/AND/OR.
    Also handles legacy format with 'node': '⊕'/'↑'/'↓'.
    """
    if not isinstance(ast, dict):
        return ast
    
    # Handle legacy format: {'node': '⊕'/'↑'/'↓', ...}
    if 'node' in ast:
        node_op = ast.get('node')
        if node_op == '⊕':
            # XOR: A ⊕ B = (A ∧ ¬B) ∨ (¬A ∧ B)
            left = _expand_derived_ops(ast.get('left'))
            right = _expand_derived_ops(ast.get('right'))
            return {
                'op': 'OR',
                'args': [
                    {'op': 'AND', 'args': [left, {'op': 'NOT', 'child': right}]},
                    {'op': 'AND', 'args': [{'op': 'NOT', 'child': left}, right]}
                ]
            }
        elif node_op == '↑':
            # NAND: A ↑ B = ¬(A ∧ B)
            left = _expand_derived_ops(ast.get('left'))
            right = _expand_derived_ops(ast.get('right'))
            return {'op': 'NOT', 'child': {'op': 'AND', 'args': [left, right]}}
        elif node_op == '↓':
            # NOR: A ↓ B = ¬(A ∨ B)
            left = _expand_derived_ops(ast.get('left'))
            right = _expand_derived_ops(ast.get('right'))
            return {'op': 'NOT', 'child': {'op': 'OR', 'args': [left, right]}}
        # For other node types, continue recursive processing
        result = ast.copy()
        if 'left' in ast:
            result['left'] = _expand_derived_ops(ast['left'])
        if 'right' in ast:
            result['right'] = _expand_derived_ops(ast['right'])
        if 'child' in ast:
            result['child'] = _expand_derived_ops(ast['child'])
        if 'args' in ast:
            result['args'] = [_expand_derived_ops(arg) for arg in ast['args']]
        return result
    
    # Handle normalized format (shouldn't normally happen as _to_bool_norm doesn't create these)
    # But handle just in case
    if 'op' not in ast:
        return ast
    
    op = ast.get('op')
    if op in {'XOR', 'NAND', 'NOR'}:
        left = _expand_derived_ops(ast.get('left'))
        right = _expand_derived_ops(ast.get('right'))
        if op == 'XOR':
            return {
                'op': 'OR',
                'args': [
                    {'op': 'AND', 'args': [left, {'op': 'NOT', 'child': right}]},
                    {'op': 'AND', 'args': [{'op': 'NOT', 'child': left}, right]}
                ]
            }
        elif op == 'NAND':
            return {'op': 'NOT', 'child': {'op': 'AND', 'args': [left, right]}}
        elif op == 'NOR':
            return {'op': 'NOT', 'child': {'op': 'OR', 'args': [left, right]}}
    
    # Recursively process other operators
    result = ast.copy()
    if 'left' in ast:
        result['left'] = _expand_derived_ops(ast['left'])
    if 'right' in ast:
        result['right'] = _expand_derived_ops(ast['right'])
    if 'child' in ast:
        result['child'] = _expand_derived_ops(ast['child'])
    if 'args' in ast:
        result['args'] = [_expand_derived_ops(arg) for arg in ast['args']]
    
    return result


def normalize_bool_ast(ast: Any, expand_imp_iff: bool = True) -> Any:
    """Boolean-only form with flattened n-ary operators.
    
    Steps:
    1. Expand derived operators (⊕, ↑, ↓) first
    2. Convert to boolean-normalized format (_to_bool_norm)
    3. Expand IMP/IFF (created by _to_bool_norm or already present)
    4. Flatten, sort, dedupe
    """
    # First expand derived operators (⊕, ↑, ↓) to NOT/AND/OR
    ast = _expand_derived_ops(ast)
    
    # Convert to boolean-normalized format
    # This handles legacy 'node' format and creates IMP/IFF from →/↔
    ast = _to_bool_norm(ast)
    
    # Expand IMP/IFF to NOT/AND/OR (now in normalized format)
    if expand_imp_iff:
        ast = _expand_imp_iff(ast)
    
    # Flatten, sort, dedupe
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
        if op == 'IMP':
            left = canonical_str(node.get('left'))
            right = canonical_str(node.get('right'))
            return f"({left} → {right})"
        if op == 'IFF':
            left = canonical_str(node.get('left'))
            right = canonical_str(node.get('right'))
            return f"({left} ↔ {right})"
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
    
    Precedence: NOT (1) > AND (2) > OR (3) > other (10)
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
        'NOT': ('¬', 1),  # Lower value = higher priority
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


def collect_variables(node: Any) -> List[str]:
    """Collect all variable names from a boolean-only AST, sorted alphabetically."""
    if not isinstance(node, dict):
        return []
    
    vars_set = set()
    
    def walk(n: Any) -> None:
        if not isinstance(n, dict):
            return
        op = n.get("op")
        if op == "VAR":
            name = n.get("name")
            if name and isinstance(name, str) and name.isupper():
                vars_set.add(name)
        elif op in {"AND", "OR"}:
            for arg in n.get("args", []):
                walk(arg)
        elif op == "NOT":
            walk(n.get("child"))
    
    walk(node)
    return sorted(vars_set)


def pretty_with_spans(node: Any) -> Tuple[str, Dict[str, Tuple[int, int]]]:
    """
    Generate canonical string with code-point spans for each AST node.
    
    Returns:
        text: Normalized string (NFC) with canonical representation
        spans_map: Dict mapping node_id (path) -> (start_cp, end_cp) in code-point indices
    
    All strings are normalized to NFC (important for ¬ and special characters).
    Node IDs are based on AST paths (e.g., [('args', 0), ('args', 1)]).
    """
    import unicodedata
    
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
    
    # Generate text using canonical_str (already NFC normalized)
    text = canonical_str(node)
    text = unicodedata.normalize('NFC', text)
    
    # Remove outer parentheses if needed (match pretty() behavior)
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
    
    # Build spans_map by iterating over nodes and finding their positions
    spans_map: Dict[str, Tuple[int, int]] = {}
    
    # Iterate through all nodes in the AST
    for path, subnode in iter_nodes(node):
        if not isinstance(subnode, dict) or subnode.get('op') in {'VAR', 'CONST'}:
            continue  # Skip leaf nodes
        
        # Create node_id from path
        if path:
            node_id = str(path)
        else:
            node_id = 'root'
        
        # Find position using canonical string matching
        subnode_text = canonical_str(subnode)
        subnode_text = unicodedata.normalize('NFC', subnode_text)
        
        # Try exact match
        pos = text.find(subnode_text)
        if pos != -1:
            spans_map[node_id] = (pos, pos + len(subnode_text))
            continue
        
        # Try without outer parentheses
        if subnode_text.startswith('(') and subnode_text.endswith(')'):
            subnode_no_parens = subnode_text[1:-1]
            pos = text.find(subnode_no_parens)
            if pos != -1:
                spans_map[node_id] = (pos, pos + len(subnode_no_parens))
    
    return text, spans_map
