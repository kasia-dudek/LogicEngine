"""
Axiomatic layer for logical expression simplification.

This module provides:
- Meta-variable representation
- Unification algorithm
- Axiom instantiation
- Axiom-based rewriting rules
"""

from typing import Any, Dict, List, Optional, Set
from .ast import normalize_bool_ast, canonical_str
from .laws import VAR, CONST, NOT, AND, OR


def META(name: str) -> Dict[str, Any]:
    """Create a meta-variable for pattern matching."""
    return {"op": "META", "name": name}


def IMP(a: Any, b: Any) -> Dict[str, Any]:
    """Create an implication node."""
    return {"op": "IMP", "left": a, "right": b}


def IFF(a: Any, b: Any) -> Dict[str, Any]:
    """Create a biconditional node."""
    return {"op": "IFF", "left": a, "right": b}


def unify(pattern: Any, term: Any, env: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """
    Unify pattern with term, returning substitution environment.
    
    Args:
        pattern: Pattern to match (may contain META variables)
        term: Term to match against
        env: Existing substitution environment
        
    Returns:
        Substitution environment if unification succeeds, None otherwise
    """
    if env is None:
        env = {}
    
    # Handle meta-variables
    if isinstance(pattern, dict) and pattern.get("op") == "META":
        var_name = pattern["name"]
        if var_name in env:
            # Check if existing binding unifies
            return unify(env[var_name], term, env)
        else:
            # New binding
            env[var_name] = term
            return env
    
    # Handle constants
    if isinstance(pattern, dict) and pattern.get("op") == "CONST":
        if isinstance(term, dict) and term.get("op") == "CONST":
            return env if pattern["value"] == term["value"] else None
        return None
    
    # Handle variables
    if isinstance(pattern, dict) and pattern.get("op") == "VAR":
        if isinstance(term, dict) and term.get("op") == "VAR":
            return env if pattern["name"] == term["name"] else None
        return None
    
    # Handle operators - check operation type first
    if not (isinstance(pattern, dict) and isinstance(term, dict)):
        return None
    
    if pattern.get("op") != term.get("op"):
        return None
    
    op = pattern["op"]
    
    # Handle unary operators
    if op == "NOT":
        return unify(pattern["child"], term["child"], env)
    
    # Handle binary operators
    if op in ["AND", "OR", "IMP", "IFF"]:
        # For commutative operators, try both orderings
        if op in ["AND", "OR"]:
            # Handle args format for AND/OR
            if "args" in pattern and "args" in term:
                if len(pattern["args"]) != len(term["args"]):
                    return None
                
                # For binary AND/OR, try both orderings
                if len(pattern["args"]) == 2:
                    # Try direct order
                    env1 = unify(pattern["args"][0], term["args"][0], env.copy())
                    if env1 is not None:
                        env2 = unify(pattern["args"][1], term["args"][1], env1)
                        if env2 is not None:
                            return env2
                    
                    # Try swapped order
                    env1 = unify(pattern["args"][0], term["args"][1], env.copy())
                    if env1 is not None:
                        env2 = unify(pattern["args"][1], term["args"][0], env1)
                        if env2 is not None:
                            return env2
                    return None
                else:
                    # For n-ary operations, try to match in order
                    current_env = env.copy()
                    for i, (p_arg, t_arg) in enumerate(zip(pattern["args"], term["args"])):
                        current_env = unify(p_arg, t_arg, current_env)
                        if current_env is None:
                            return None
                    return current_env
            else:
                return None
        else:
            # Non-commutative operators (IMP, IFF) use left/right
            env1 = unify(pattern["left"], term["left"], env)
            if env1 is not None:
                return unify(pattern["right"], term["right"], env1)
            return None
    
    return None


def instantiate(pattern: Any, env: Dict[str, Any]) -> Any:
    """
    Instantiate pattern with substitution environment.
    
    Args:
        pattern: Pattern to instantiate
        env: Substitution environment
        
    Returns:
        Instantiated term
    """
    if isinstance(pattern, dict):
        if pattern.get("op") == "META":
            var_name = pattern["name"]
            if var_name in env:
                return instantiate(env[var_name], env)
            else:
                return pattern  # Unbound meta-variable
        
        # Recursively instantiate subterms
        result = pattern.copy()
        if "left" in pattern:
            result["left"] = instantiate(pattern["left"], env)
        if "right" in pattern:
            result["right"] = instantiate(pattern["right"], env)
        if "child" in pattern:
            result["child"] = instantiate(pattern["child"], env)
        if "args" in pattern:
            result["args"] = [instantiate(arg, env) for arg in pattern["args"]]
        
        return result
    
    return pattern


# Axiom schemas
AXIOMS = [
    {
        "id": 1,
        "name": "A1",
        "lhs": IMP(META("p"), META("q")),
        "rhs": OR([NOT(META("p")), META("q")]),
        "dir": "lhs2rhs",
        "explain": "Implication to OR: (p→q) ⇒ (¬p ∨ q)"
    },
    {
        "id": 2,
        "name": "A2", 
        "lhs": IFF(META("p"), META("q")),
        "rhs": OR([AND([META("p"), META("q")]), AND([NOT(META("p")), NOT(META("q"))])]),
        "dir": "lhs2rhs",
        "explain": "Biconditional to CNF: (p↔q) ⇒ (p∧q) ∨ (¬p∧¬q)"
    },
    {
        "id": 12,
        "name": "A12",
        "lhs": IMP(META("p"), AND([META("q"), NOT(META("q"))])),
        "rhs": NOT(META("p")),
        "dir": "lhs2rhs", 
        "explain": "A12: [p → (q ∧ ¬q)] ⇒ ¬p"
    }
]


def axioms_matches(node: Any) -> List[Dict[str, Any]]:
    """
    Find axiom matches in the given node.
    
    Args:
        node: AST node to search for matches
        
    Returns:
        List of axiom match objects
    """
    matches = []
    
    # Import here to avoid circular imports
    from .laws import iter_nodes
    
    for path, sub in iter_nodes(node):
        for axiom in AXIOMS:
            # Try lhs2rhs direction
            if axiom["dir"] in ["lhs2rhs", "both"]:
                env = unify(axiom["lhs"], sub)
                if env is not None:
                    after = instantiate(axiom["rhs"], env)
                    # Normalize and expand IMP/IFF
                    after = normalize_bool_ast(after, expand_imp_iff=True)
                    
                    # Check if this step actually reduces measure
                    # For desugaring axioms (A1, A2), allow measure increase
                    from .laws import measure
                    is_desugaring = axiom["id"] in [1, 2]  # A1, A2 are desugaring axioms
                    if is_desugaring or measure(after) <= measure(sub):
                        matches.append({
                            "law": f"Aksjomat {axiom['id']} ({axiom['name']})",
                            "note": axiom["explain"],
                            "path": path,
                            "before": sub,
                            "after": after,
                            "meta_subst": env,
                            "axiom_id": axiom["id"],
                            "axiom_name": axiom["name"],
                            "source": "axiom"
                        })
            
            # Try rhs2lhs direction
            if axiom["dir"] in ["rhs2lhs", "both"]:
                env = unify(axiom["rhs"], sub)
                if env is not None:
                    after = instantiate(axiom["lhs"], env)
                    # Normalize and expand IMP/IFF
                    after = normalize_bool_ast(after, expand_imp_iff=True)
                    
                    # Check if this step actually reduces measure
                    # For desugaring axioms (A1, A2), allow measure increase
                    from .laws import measure
                    is_desugaring = axiom["id"] in [1, 2]  # A1, A2 are desugaring axioms
                    if is_desugaring or measure(after) <= measure(sub):
                        matches.append({
                            "law": f"Aksjomat {axiom['id']} ({axiom['name']})",
                            "note": axiom["explain"],
                            "path": path,
                            "before": sub,
                            "after": after,
                            "meta_subst": env,
                            "axiom_id": axiom["id"],
                            "axiom_name": axiom["name"],
                            "source": "axiom"
                        })
    
    return matches


# Mapping of algebraic laws to their axiomatic sources
DERIVED_FROM_AXIOMS = {
    "Absorpcja (∨)": ["A8", "A9", "A11"],
    "De Morgan: ¬(A ∧ B) → ¬A ∨ ¬B": ["A3", "A4"],
    "Idempotencja (∨)": ["A6", "A7"],
    "Idempotencja (∧)": ["A6", "A7"], 
    "Element neutralny (∨)": ["A6"],
    "Element neutralny (∧)": ["A6"],
    "Element pochłaniający (∨)": ["A6"],
    "Element pochłaniający (∧)": ["A6"],
    "Konsensus": ["A11"],
    "Pokrywanie": ["A1", "A11"]
}