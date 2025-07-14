from .parser import LogicParser, LogicExpressionError
from .truth_table import generate_truth_table, TruthTableError

def main():
    expr = input("Podaj wyrażenie logiczne: ")
    try:
        std = LogicParser.parse(expr)
        print(f"Wyrażenie po standaryzacji: {std}")
        table = generate_truth_table(expr)
        print("Tabela prawdy:")
        for row in table:
            print(row)
    except (LogicExpressionError, TruthTableError) as e:
        print(f"Błąd: {e}")

if __name__ == "__main__":
    main() 