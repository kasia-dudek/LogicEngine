from .parser import LogicParser, LogicExpressionError
from .truth_table import generate_truth_table, TruthTableError
from .ast import generate_ast, ASTError
from .onp import to_onp, ONPError
from .kmap import simplify_kmap, KMapError
from .qm import simplify_qm, QMError
import json
from logicengine.engine import LogicEngine

# Usuń wszystkie print statements z kodu produkcyjnego

if __name__ == "__main__":
    # Przykładowe wyrażenie logiczne
    expr = "(A ∧ B) ∨ ¬C"
    # Analiza wyrażenia przez LogicEngine
    result = LogicEngine.analyze(expr)
    # Wypisz wynik w formacie JSON (ładnie sformatowany)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    main() 