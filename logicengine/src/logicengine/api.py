"""HTTP API for the logic engine (FastAPI). Polish user messages."""

from __future__ import annotations
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
from .laws import simplify_with_laws
from .minimal_forms import compute_minimal_forms  # <— WAŻNE: minimal forms

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
        return data  # ma klucze: kmap, groups, all_groups, result, steps, vars, minterms, axis
    except (LogicExpressionError, KMapError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/qm")
def qm(req: ExprRequest):
    try:
        std_expr = validate_and_standardize(req.expr)
        data = simplify_qm(std_expr)
        return data  # ma klucze: result, steps, expr_for_tests
    except (LogicExpressionError, QMError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/tautology")
def tautology(req: ExprRequest):
    try:
        std_expr = validate_and_standardize(req.expr)
        return {"is_tautology": is_tautology(std_expr)}
    except Exception:
        # zgodnie z implementacją zwraca False przy błędach
        return {"is_tautology": False}


@app.post("/laws")
def laws(req: ExprRequest):
    try:
        std_expr = validate_and_standardize(req.expr)
        data = simplify_with_laws(std_expr)
        return data  # ma klucze: result, steps, normalized_ast, mode
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# --------- NOWE: minimal forms (DNF/CNF/ANF/NAND/NOR/AND/OR) ---------
@app.post("/minimal_forms")
def minimal_forms(req: ExprRequest):
    """Zwraca wszystkie formy minimalne do wyświetlenia w ResultScreen/MinimalForms.jsx."""
    try:
        std_expr = validate_and_standardize(req.expr)
        data = compute_minimal_forms(std_expr)
        return data
    except Exception as e:
        # komunikat po polsku do UI
        error_msg = str(e)
        if "timeout" in error_msg.lower() or "hang" in error_msg.lower():
            raise HTTPException(status_code=408, detail="Przetwarzanie trwa zbyt długo. Spróbuj z prostszym wyrażeniem.")
        else:
            raise HTTPException(status_code=400, detail=f"Nie udało się policzyć form minimalnych: {e}")