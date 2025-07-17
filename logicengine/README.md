# LogicEngine – Backend

## Przegląd i refaktoryzacja (2024-06)

### Zakres przeglądu
- Spójność nazewnictwa, struktury, formatowania (PEP 8)
- Poprawność logiki i matematyki (parser, tabela prawdy, AST, ONP, KMap, QM, tautologia)
- Eliminacja duplikacji i niepotrzebnego kodu
- Optymalizacja wydajności (KMap, QM, tabela prawdy)
- Rozbudowa testów jednostkowych i integracyjnych (min. 80% pokrycia)
- Spójność formatu JSON z frontendem

### Wprowadzone poprawki
- Refaktoryzacja parsera, AST, ONP, KMap, QM, tautologii
- Wydzielenie funkcji pomocniczych do utils.py
- Uspójnienie obsługi błędów i komunikatów
- Rozbudowa testów jednostkowych i integracyjnych
- Optymalizacja algorytmów dla 4 zmiennych

### Wymagania
- Python 3.10+
- sympy, pytest, pytest-cov

### Przykładowe dane wejściowe
- (A ∨ ¬A), (A ∧ B) ∨ ¬C, A → (B ↔ C), (A & B) (niepoprawne)

### Testy
- Pokrycie kodu: min. 80% (`pytest --cov`)
- Testy: `pytest`

### Napotkane problemy i rozwiązania
- Duplikacja funkcji pomocniczych – wydzielono do utils.py
- Uspójnienie formatów danych dla frontendu
- Optymalizacja algorytmów uproszczeń

### Stan projektu
- Kod gotowy do rozbudowy, modularny, pokryty testami
- Wyniki w formacie JSON zgodnym z frontendem

## Opis
LogicEngine to modularny silnik do nauki logiki zdań, obsługujący parser, tabelę prawdy, ONP, AST, Mapę Karnaugh i algorytm Quine'a-McCluskeya (QM). Każdy moduł generuje czytelne, edukacyjne kroki w formacie JSON, gotowe do wizualizacji w frontendzie.

## Funkcje
- Parsowanie i walidacja wyrażeń logicznych (¬, ∧, ∨, →, ↔, zmienne A-Z, nawiasy)
- Standaryzacja wyrażeń
- Generowanie tabeli prawdy (do 4 zmiennych)
- Przygotowana struktura pod rozbudowę (Mapa Karnaugh, Quine-McCluskey, AST, ONP)

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

## Algorytm Quine'a-McCluskeya (QM)

### Funkcjonalność
- Uproszczenie wyrażeń logicznych do postaci minimalnej.
- Szczegółowe kroki upraszczania w formacie JSON, z opisami w języku polskim.
- Obsługa do 4 zmiennych.
- Wyniki zgodne z Mapą Karnaugh i tabelą prawdy.
- Obsługa błędów i przypadków brzegowych (tautologia, sprzeczność, pojedyncza zmienna).

### Przykład użycia
```python
from logicengine.qm import simplify_qm
result = simplify_qm("(A ∧ B) ∨ (¬A ∧ B)")
print(result["result"])  # A ∨ B
for step in result["steps"]:
    print(step)
```

### Przykładowe dane wejściowe i wynik
**Wejście:**
```
(A ∧ B) ∨ (¬A ∧ B)
```
**Wynik:**
```
{
  "result": "A ∨ B",
  "steps": [
    {"step": "Krok 1: Znajdź mintermy (przypadki, gdy wyrażenie jest prawdziwe)", "data": {"minterms": [2, 3], "opis": "Indeksy wierszy tabeli prawdy, gdzie wynik = 1."}},
    {"step": "Krok 2: Grupowanie mintermów wg liczby jedynek", "data": {"groups": {1: ["10"], 2: ["11"]}, "opis": "Mintermy pogrupowane według liczby jedynek w zapisie binarnym."}},
    {"step": "Krok 3: Łączenie mintermów i wyznaczanie implikantów pierwszorzędnych", "data": {"rounds": [...], "prime_implicants": [...], "opis": "Iteracyjne łączenie mintermów w celu znalezienia wszystkich PI."}},
    {"step": "Krok 4: Tabela pokrycia mintermów przez PI", "data": {"cover": {2: ["1-"], 3: ["1-"]}, "opis": "Które PI pokrywają które mintermy."}},
    {"step": "Krok 5: Zasada implikanty (PI pokrywające unikalnie minterm)", "data": {"essential": ["1-"], "opis": "PI, które pokrywają mintermy niepokryte przez inne PI."}},
    {"step": "Krok 6: Minimalne pokrycie (Petrick)", "data": {"cover": ["1-"], "opis": "Wybór minimalnego zbioru PI pokrywających wszystkie mintermy."}},
    {"step": "Krok 7: Wynik końcowy", "data": {"result": "A ∨ B", "opis": "Uproszczone wyrażenie logiczne."}},
    {"step": "Krok 8: Weryfikacja", "data": {"zgodność": true, "opis": "Porównanie tabeli prawdy oryginału i uproszczenia."}}
  ]
}
```

### Format kroków (steps)
Każdy krok to słownik z kluczem `step` (opis w języku polskim) i `data` (szczegóły, np. mintermy, grupy, pokrycia, opis).

### Testowanie
- Testy jednostkowe: `pytest`, `pytest-cov` (pokrycie >80%).
- Testy porównują QM z Mapą Karnaugh i tabelą prawdy.
- Obsługa błędów i przypadków brzegowych.

### Zmiany w QM
- Naprawiono metodę Petricka (zawsze wybiera minimalne pokrycie).
- Usunięto duplikację kodu (wspólne funkcje w utils.py).
- Dodano szczegółowe, edukacyjne opisy kroków.
- Poprawiono obsługę błędów i walidację wejścia.

## Kontakt
Projekt edukacyjny. Autor: Kasia & AI
