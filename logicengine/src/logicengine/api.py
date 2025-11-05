"""HTTP API for the logic engine (FastAPI)."""

from __future__ import annotations
from typing import List, Optional, Tuple, Union, Any as TypingAny
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .parser import LogicExpressionError, validate_and_standardize
from .truth_table import generate_truth_table, TruthTableError
from .ast import generate_ast, ASTError, normalize_bool_ast
from .onp import to_onp, ONPError
from .kmap import simplify_kmap, KMapError
from .qm import simplify_qm, QMError
from .tautology import is_tautology
from .contradiction import is_contradiction
from .laws import simplify_with_laws, apply_law_once, pretty_with_tokens, find_subtree_span_by_path, pretty
from .minimal_forms import compute_minimal_forms
from .engine import simplify_to_minimal_dnf, TooManyVariables
from .rules import LIST_OF_RULES, Rule
from .rewriter import find_matches, apply_match

app = FastAPI(title="Logic Engine API")

# ---------- CORS configuration ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- I/O models ----------
class ExprRequest(BaseModel):
    expr: str

class LawsRequest(BaseModel):
    expr: str
    mode: str = "mixed"  # "algebraic", "axioms", "mixed"

class SimplifyDNFRequest(BaseModel):
    expr: str
    var_limit: int = 8

class ApplyLawRequest(BaseModel):
    expr: str
    path: List[List[Union[str, int, None]]]  # Format JSON: [["args", 0], ["args", 1], ...] lub [["child", null]]
    law: str
    
    def get_path(self):
        """Convert path from JSON format to Python tuples."""
        result = []
        for item in self.path:
            if isinstance(item, list) and len(item) == 2:
                # item is ["args", 0] or ["child", null]
                result.append((item[0], item[1]))
            else:
                result.append((item[0] if isinstance(item, (list, tuple)) and len(item) > 0 else "", None))
        return result


class RulesListRequest(BaseModel):
    pass  # Empty for now


class RulesMatchesRequest(BaseModel):
    expr: str
    ruleId: str


class RulesApplyRequest(BaseModel):
    expr: str
    ruleId: str
    matchId: str

# ---------- endpoints ----------

@app.post("/standardize")
def standardize(req: ExprRequest):
    try:
        std = validate_and_standardize(req.expr)
        return {"standardized": std}
    except LogicExpressionError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/truth_table")
def truth_table(req: ExprRequest):
    try:
        std_expr = validate_and_standardize(req.expr)
        table = generate_truth_table(std_expr)
        return {"truth_table": table}
    except (LogicExpressionError, TruthTableError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/ast")
def ast(req: ExprRequest):
    try:
        std_expr = validate_and_standardize(req.expr)
        ast = generate_ast(std_expr)
        return {"ast": ast}
    except (LogicExpressionError, ASTError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/onp")
def onp(req: ExprRequest):
    try:
        std_expr = validate_and_standardize(req.expr)
        out = to_onp(std_expr)
        return {"onp": out}
    except (LogicExpressionError, ONPError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/kmap")
def kmap(req: ExprRequest):
    try:
        std_expr = validate_and_standardize(req.expr)
        data = simplify_kmap(std_expr)
        return data  # contains: kmap, groups, all_groups, result, steps, vars, minterms, axis
    except (LogicExpressionError, KMapError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/qm")
def qm(req: ExprRequest):
    try:
        std_expr = validate_and_standardize(req.expr)
        data = simplify_qm(std_expr)
        return data  # contains: result, steps, expr_for_tests
    except (LogicExpressionError, QMError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/tautology")
def tautology(req: ExprRequest):
    try:
        std_expr = validate_and_standardize(req.expr)
        return {"is_tautology": is_tautology(std_expr)}
    except Exception:
        # implementation returns False on errors
        return {"is_tautology": False}


@app.post("/contradiction")
def contradiction(req: ExprRequest):
    try:
        std_expr = validate_and_standardize(req.expr)
        return {"is_contradiction": is_contradiction(std_expr)}
    except Exception:
        # implementation returns False on errors
        return {"is_contradiction": False}


@app.post("/laws")
def laws(req: LawsRequest):
    try:
        std_expr = validate_and_standardize(req.expr)
        data = simplify_with_laws(std_expr, mode=req.mode)
        return data  # contains: result, steps, normalized_ast, mode
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/laws_apply")
def laws_apply(req: ApplyLawRequest):
    """Apply a specific law at a given path for preview or alternative simplification."""
    try:
        std_expr = validate_and_standardize(req.expr)
        path = req.get_path()
        result = apply_law_once(std_expr, path, req.law)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/minimal_forms")
def minimal_forms(req: ExprRequest):
    """Returns all minimal forms for display in ResultScreen/MinimalForms.jsx."""
    try:
        std_expr = validate_and_standardize(req.expr)
        return compute_minimal_forms(std_expr)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/simplify_dnf")
def simplify_dnf(req: SimplifyDNFRequest):
    """Simplify to minimal DNF with step-by-step trace."""
    try:
        return simplify_to_minimal_dnf(req.expr, var_limit=req.var_limit)
    except TooManyVariables as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def _convert_path_to_tuple_path(path: List[int], node: Any) -> List[Tuple[str, Optional[int]]]:
    """
    Convert path from List[int] format (used by rewriter) to List[Tuple[str, Optional[int]]] format.
    
    The List[int] format from rewriter._walk():
    - For NOT nodes: path_prefix + [0] means child
    - For AND/OR nodes: path_prefix + [i] means args[i]
    """
    result: List[Tuple[str, Optional[int]]] = []
    current = node
    
    for idx in path:
        if isinstance(current, dict):
            op = current.get("op")
            if op == "NOT":
                # In rewriter, NOT child is always at index 0
                result.append(("child", None))
                current = current.get("child")
            elif op in {"AND", "OR"}:
                # In rewriter, AND/OR args are indexed directly
                result.append(("args", idx))
                args = current.get("args", [])
                if idx < len(args):
                    current = args[idx]
                else:
                    # Invalid path - break early
                    break
            else:
                # Unknown operator - cannot proceed
                break
        else:
            # Leaf node - cannot proceed
            break
    
    return result


@app.post("/rules/list")
def rules_list(req: RulesListRequest):
    """Return list of available rules."""
    try:
        rules = [
            {
                "id": rule.id,
                "name": rule.name,
            }
            for rule in LIST_OF_RULES
        ]
        return {"rules": rules}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/rules/matches")
def rules_matches(req: RulesMatchesRequest):
    """Find matches for a specific rule in an expression."""
    try:
        std_expr = validate_and_standardize(req.expr)
        
        # Find rule by ID
        rule = None
        for r in LIST_OF_RULES:
            if r.id == req.ruleId:
                rule = r
                break
        
        if not rule:
            raise HTTPException(status_code=404, detail=f"Rule '{req.ruleId}' not found")
        
        # Generate AST and normalize
        legacy_ast = generate_ast(std_expr)
        node = normalize_bool_ast(legacy_ast, expand_imp_iff=True)
        
        # Find matches using rewriter
        matches = find_matches(rule, node)
        
        # Generate pretty string with tokens for span calculation
        before_str, before_spans_map = pretty_with_tokens(node)
        
        # Convert matches to response format with spans
        result_matches = []
        for match in matches:
            # Convert path format
            tuple_path = _convert_path_to_tuple_path(match.path, node)
            
            # Get focus expression (the matched subtree)
            focus_expr = match.focus_expr
            focus_pretty = pretty(focus_expr)
            
            # Get preview expression (after applying rule)
            preview_ast = match.preview_ast
            preview_pretty = pretty(preview_ast)
            
            # Calculate spans in code-points
            from .laws import find_subtree_span_by_path_cp
            before_span = find_subtree_span_by_path_cp(tuple_path, node)
            
            # For after_span, we need to calculate from preview_ast
            # The transformed subtree is at the same path
            after_str, after_spans_map = pretty_with_tokens(preview_ast)
            after_span = find_subtree_span_by_path_cp(tuple_path, preview_ast)
            
            # Create lists in tuple format (code-points)
            before_highlight_spans_cp = [(before_span["start"], before_span["end"])] if before_span else []
            after_highlight_spans_cp = [(after_span["start"], after_span["end"])] if after_span else []
            
            result_matches.append({
                "matchId": match.match_id,
                "focusPretty": focus_pretty,
                "previewExpr": preview_pretty,
                "before_str": before_str,
                "after_str": after_str,
                "before_highlight_spans_cp": before_highlight_spans_cp if before_highlight_spans_cp else None,
                "after_highlight_spans_cp": after_highlight_spans_cp if after_highlight_spans_cp else None,
                "path": [[key, idx] for key, idx in tuple_path],
            })
        
        return {
            "matches": result_matches,
            "before_str": before_str,
            "after_str": None,  # Not applicable for matches endpoint
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/rules/apply")
def rules_apply(req: RulesApplyRequest):
    """Apply a specific rule match to an expression."""
    try:
        std_expr = validate_and_standardize(req.expr)
        
        # Find rule by ID
        rule = None
        for r in LIST_OF_RULES:
            if r.id == req.ruleId:
                rule = r
                break
        
        if not rule:
            raise HTTPException(status_code=404, detail=f"Rule '{req.ruleId}' not found")
        
        # Generate AST and normalize
        legacy_ast = generate_ast(std_expr)
        node = normalize_bool_ast(legacy_ast, expand_imp_iff=True)
        
        # Find matches
        matches = find_matches(rule, node)
        
        # Find the specific match
        target_match = None
        for m in matches:
            if m.match_id == req.matchId:
                target_match = m
                break
        
        if not target_match:
            raise HTTPException(status_code=404, detail=f"Match '{req.matchId}' not found")
        
        # Calculate spans BEFORE applying (code-points)
        before_str, before_spans_map = pretty_with_tokens(node)
        tuple_path = _convert_path_to_tuple_path(target_match.path, node)
        from .laws import find_subtree_span_by_path_cp
        before_span = find_subtree_span_by_path_cp(tuple_path, node)
        
        # Apply the match
        after_ast = apply_match(rule, node, target_match)
        
        # Calculate spans AFTER applying (code-points)
        after_str, after_spans_map = pretty_with_tokens(after_ast)
        # The transformed subtree is at the same path
        after_span = find_subtree_span_by_path_cp(tuple_path, after_ast)
        
        # Calculate metrics (for compatibility with frontend)
        from .laws import count_nodes, count_literals
        
        def count_operators(n: Any) -> int:
            if not isinstance(n, dict):
                return 0
            op = n.get("op")
            if op in {"AND", "OR", "NOT"}:
                return 1 + (sum(count_operators(a) for a in n.get("args", [])) if op in {"AND", "OR"} else count_operators(n.get("child")))
            return 0
        
        def neg_depth_sum(n: Any, depth: int = 0) -> int:
            if not isinstance(n, dict):
                return 0
            op = n.get("op")
            if op == "NOT":
                return depth + neg_depth_sum(n.get("child"), depth + 1)
            elif op in {"AND", "OR"}:
                return sum(neg_depth_sum(a, depth) for a in n.get("args", []))
            return 0
        
        metrics_before = {
            "operators": count_operators(node),
            "literals": count_literals(node),
            "neg_depth_sum": neg_depth_sum(node),
        }
        
        metrics_after = {
            "operators": count_operators(after_ast),
            "literals": count_literals(after_ast),
            "neg_depth_sum": neg_depth_sum(after_ast),
        }
        
        # Create lists in tuple format (code-points)
        before_highlight_spans_cp = [(before_span["start"], before_span["end"])] if before_span else []
        after_highlight_spans_cp = [(after_span["start"], after_span["end"])] if after_span else []
        
        return {
            "exprAfter": after_str,
            "metricsBefore": metrics_before,
            "metricsAfter": metrics_after,
            "before_highlight_spans_cp": before_highlight_spans_cp if before_highlight_spans_cp else None,
            "after_highlight_spans_cp": after_highlight_spans_cp if after_highlight_spans_cp else None,
            "before_str": before_str,
            "after_str": after_str,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

