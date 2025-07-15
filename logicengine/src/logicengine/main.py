from .parser import LogicParser, LogicExpressionError
from .truth_table import generate_truth_table, TruthTableError
from .ast import generate_ast, ASTError
from .onp import to_onp, ONPError
from .kmap import simplify_kmap, KMapError
import json

def main():
    expr = input("Podaj wyrażenie logiczne: ")
    try:
        std = LogicParser.parse(expr)
        print(f"Wyrażenie po standaryzacji: {std}")
        table = generate_truth_table(expr)
        print("Tabela prawdy:")
        for row in table:
            print(row)
        ast = generate_ast(expr)
        print("AST:")
        print(json.dumps(ast, ensure_ascii=False, indent=2))
        onp = to_onp(expr)
        print("ONP:")
        print(onp)
        kmap = simplify_kmap(expr)
        print("Kroki Mapy Karnaugh:")
        print(json.dumps(kmap["steps"], ensure_ascii=False, indent=2))
        print(f"Uproszczone wyrażenie (K-map): {kmap['result']}")
    except (LogicExpressionError, TruthTableError, ASTError, ONPError, KMapError) as e:
        print(f"Błąd: {e}")

if __name__ == "__main__":
    main() 