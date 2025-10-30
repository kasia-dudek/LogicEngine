"""HTTP API for the logic engine (FastAPI)."""

from __future__ import annotations
from typing import List, Optional, Tuple, Union, Any as TypingAny
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .parser import LogicExpressionError, validate_and_standardize
from .truth_table import generate_truth_table, TruthTableError
from .ast import generate_ast, ASTError
from .onp import to_onp, ONPError
from .kmap import simplify_kmap, KMapError
from .qm import simplify_qm, QMError
from .tautology import is_tautology
from .contradiction import is_contradiction
from .laws import simplify_with_laws, apply_law_once
from .minimal_forms import compute_minimal_forms
from .engine import simplify_to_minimal_dnf, TooManyVariables

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

