# LogicEngine

Platforma webowa do nauki logiki zdań z modularnym silnikiem logicznym.

## Funkcje
- Parsowanie i walidacja wyrażeń logicznych (¬, ∧, ∨, →, ↔, zmienne A-Z, nawiasy)
- Standaryzacja wyrażeń
- Generowanie tabeli prawdy (do 4 zmiennych)
- Przygotowana struktura pod rozbudowę (Mapa Karnaugh, Quine-McCluskey, AST, ONP)

## Wymagania
- Python 3.10+
- [Poetry](https://python-poetry.org/)

## Instalacja
```bash
poetry install
```

## Uruchomienie
```bash
poetry run python main.py
```

## Testy
```bash
poetry run pytest
```

## Przykłady wyrażeń
Poprawne:
- (A ∧ B) ∨ ¬C
- A → (B ↔ C)
- ¬A

Niepoprawne:
- (A & B)
- A ++ B
- (A ∧ B
