from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .parser import LogicParser, LogicExpressionError, validate_and_standardize
from .truth_table import generate_truth_table, TruthTableError
from .ast import generate_ast, ASTError
from .onp import to_onp, ONPError
from .kmap import simplify_kmap, KMapError
from .qm import simplify_qm, QMError
from .tautology import is_tautology
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

app = FastAPI()

# Pozwól na CORS dla frontendu
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ExprRequest(BaseModel):
    expr: str

@app.post("/standardize")
def standardize_expr(req: ExprRequest):
    try:
        std = validate_and_standardize(req.expr)
        return {"standardized": std}
    except LogicExpressionError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/ast")
def get_ast(req: ExprRequest):
    try:
        std = validate_and_standardize(req.expr)
        ast = generate_ast(std)
        return {"ast": ast}
    except (ASTError, LogicExpressionError) as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/onp")
def get_onp(req: ExprRequest):
    try:
        std = validate_and_standardize(req.expr)
        onp = to_onp(std)
        return {"onp": onp}
    except (ONPError, LogicExpressionError) as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/truth_table")
def get_truth_table(req: ExprRequest):
    try:
        std = validate_and_standardize(req.expr)
        table = generate_truth_table(std)
        return {"truth_table": table}
    except (TruthTableError, LogicExpressionError) as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/kmap")
def get_kmap(req: ExprRequest):
    try:
        std = validate_and_standardize(req.expr)
        kmap = simplify_kmap(std)
        return kmap
    except (KMapError, LogicExpressionError) as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/qm")
def get_qm(req: ExprRequest):
    try:
        std = validate_and_standardize(req.expr)
        qm = simplify_qm(std)
        return qm
    except (QMError, LogicExpressionError) as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/tautology")
def check_tautology(req: ExprRequest):
    try:
        std = validate_and_standardize(req.expr)
        result = is_tautology(std)
        return {"is_tautology": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/", response_class=HTMLResponse)
def root():
    return "<h2>LogicEngine API działa! Użyj frontendu, aby korzystać z aplikacji.</h2>" 