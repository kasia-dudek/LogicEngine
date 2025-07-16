import logging
from .parser import LogicParser, LogicExpressionError
from .truth_table import generate_truth_table, TruthTableError
from .ast import generate_ast, ASTError
from .onp import to_onp, ONPError
from .kmap import simplify_kmap, KMapError
from .qm import simplify_qm, QMError
from .tautology import is_tautology
from typing import Any, Dict

logger = logging.getLogger(__name__)

class LogicEngine:
    """
    Główny silnik integrujący wszystkie funkcjonalności logiki zdań.
    """
    @staticmethod
    def analyze(expr: str) -> Dict[str, Any]:
        result = {"expression": expr}
        try:
            # Parsowanie i standaryzacja
            parsed = LogicParser.parse(expr)
            result["parsed"] = parsed
        except LogicExpressionError as e:
            logger.error(f"Parser error: {e}")
            result["error"] = f"Parser error: {e}"
            return result
        # Tabela prawdy
        try:
            truth_table = generate_truth_table(expr)
            result["truth_table"] = truth_table
        except TruthTableError as e:
            logger.error(f"Truth table error: {e}")
            result["truth_table_error"] = str(e)
        # AST
        try:
            ast = generate_ast(expr)
            result["ast"] = ast
        except ASTError as e:
            logger.error(f"AST error: {e}")
            result["ast_error"] = str(e)
        # ONP
        try:
            onp = to_onp(expr)
            result["onp"] = onp
        except ONPError as e:
            logger.error(f"ONP error: {e}")
            result["onp_error"] = str(e)
        # Karnaugh
        try:
            kmap = simplify_kmap(expr)
            result["kmap_simplification"] = kmap
        except KMapError as e:
            logger.error(f"KMap error: {e}")
            result["kmap_error"] = str(e)
        # Quine-McCluskey
        try:
            qm = simplify_qm(expr)
            result["qm_simplification"] = qm
        except QMError as e:
            logger.error(f"QM error: {e}")
            result["qm_error"] = str(e)
        # Tautologia
        try:
            result["is_tautology"] = is_tautology(expr)
        except Exception as e:
            logger.error(f"Tautology check error: {e}")
            result["tautology_error"] = str(e)
        return result 