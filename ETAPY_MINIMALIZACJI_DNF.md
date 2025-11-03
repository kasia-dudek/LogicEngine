# ETAPY MINIMALIZACJI DO DNF PRAWAMI LOGICZNYMI

## CEL
Transformacja wyrażenia logicznego do minimalnej postaci DNF (Disjunctive Normal Form) przy użyciu wyłącznie praw algebry Boole'a.

---

## FAZA I: NORMALIZACJA WYRAŻENIA

### 1. Standaryzacja składni
- **Input**: Wyrażenie w dowolnym formacie (`A && B`, `A & B`, `A∧B`)
- **Output**: Kanoniczny format (`A∧B`)
- **Operatory**:
  - `!`, `~`, `¬` → `¬`
  - `&`, `&&`, `∧` → `∧`
  - `|`, `||`, `+`, `∨` → `∨`
  - `^`, `<>`, `⊕` → `⊕`
  - `->`, `=>`, `→` → `→`
  - `<->`, `<=>`, `==`, `=`, `≡`, `↔` → `↔`

### 2. Wprowadzenie negacji do literałów (Prawo De Morgana)
- **Cele**: Eliminacja negacji złożonych, usunięcie implikacji i równoważności
- **Reguły**:
  - `¬(A ∧ B)` → `¬A ∨ ¬B`
  - `¬(A ∨ B)` → `¬A ∧ ¬B`
  - `¬(¬A)` → `A` (podwójna negacja)
  - `A → B` → `¬A ∨ B` (implikacja)
  - `A ↔ B` → `(A ∧ B) ∨ (¬A ∧ ¬B)` (równoważność)

**Przykład**:
```
¬(A ∧ B) → ¬A ∨ ¬B
```

### 3. Rozprowadzenie koniunkcji względem alternatywy (Dystrybutywność)
- **Cel**: Przekształcenie do formy sumy iloczynów (SOP)
- **Reguły**:
  - **AND nad OR**: `A ∧ (B ∨ C)` → `(A ∧ B) ∨ (A ∧ C)`
  - **Kontrolled distribution**: tylko gdy redukuje liczbę literałów

**Przykład**:
```
A ∧ (B ∨ C) → (A ∧ B) ∨ (A ∧ C)
```

### 4. Uporządkowanie i uproszczenia lokalne
- **Spłaszczanie**: `A ∧ (B ∧ C)` → `A ∧ B ∧ C`
- **Deduplikacja**: usunięcie duplikatów
- **Sortowanie**: uporządkowanie literałów według kanonu
- **Kluczowe prawa**:
  - **Idempotencja**: `X ∧ X` → `X`, `X ∨ X` → `X`
  - **Absorpcja**: `X ∨ (X ∧ Y)` → `X`, `X ∧ (X ∨ Y)` → `X`
  - **Element neutralny**: `X ∧ 1` → `X`, `X ∨ 0` → `X`
  - **Element pochłaniający**: `X ∧ 0` → `0`, `X ∨ 1` → `1`
  - **Kontradykcja**: `A ∧ ¬A` → `0`
  - **Tautologia**: `A ∨ ¬A` → `1`
  - **Absorpcja z negacją**: `X ∨ (¬X ∧ Y)` → `X ∨ Y`, `X ∧ (¬X ∨ Y)` → `X ∧ Y`

**Przykłady**:
```
A ∨ A → A                    (idempotencja)
A ∨ (A ∧ B) → A             (absorpcja)
A ∧ 0 → 0                   (element pochłaniający)
A ∧ ¬A → 0                  (kontradykcja)
A ∨ (¬A ∧ B) → A ∨ B        (absorpcja z negacją)
```

### 5. Rozwinięcie do kanonicznej DNF
- **Cel**: Każdy minterm zawiera wszystkie zmienne (pozytywne lub zanegowane)
- **Metoda**: Rozwinięcie Shannona: `f = x∧f|x ⊕ ¬x∧f|¬x`
- **Strategia**: Iteracyjne zastosowanie `X → X∧(v∨¬v)` dla brakujących zmiennych

**Przykład**:
```
A → A∧(B∨¬B) → (A∧B)∨(A∧¬B)
```

---

## FAZA II: MINIMALIZACJA (QM BRIDGE)

### 6. QM Planowanie (niewidoczne w UI)
- **Algorytm**: Quine-McCluskey
- **Kroki**:
  1. Tabela prawdy i mintermy
  2. Grupowanie według liczby jedynek
  3. Wyznaczanie implikantów pierwszorzędnych (PI)
  4. Tabela pokrycia
  5. Implikanty istotne
  6. Dobór reszty (Petrick's method)
  7. Redundancy pruning
- **Output**: Lista wybranych PI + plan łączenia

### 7. Odsłonięcie par do scalania
- **Cel**: Upewnienie się, że mintermy różniące się jedną zmienną są obecne w AST
- **Strategia**: 
  - Jeśli para `(A∧B∧C)` i `(A∧B∧¬C)` nie jest obecna, użyj tożsamości:
    - `X → X∧(v∨¬v)` (element neutralny ∧1)
    - `X∧(v∨¬v) → (X∧v) ∨ (X∧¬v)` (dystrybutywność)
- **Kroki**:
  1. **Tożsamość**: `(A∧B) → (A∧B)∧(C∨¬C)`
  2. **Dystrybutywność**: `(A∧B)∧(C∨¬C) → (A∧B∧C)∨(A∧B∧¬C)`

**Nazwa kroku**: "Odsłonięcie pary (tożsamość)" / "Odsłonięcie pary (Dystrybucja)"

### 8. Scalanie par mintermów (3 kroki)
- **Cel**: Połączenie mintermów różniących się jedną zmienną
- **Przykład**: `(A∧B∧C) ∨ (A∧B∧¬C)` → `A∧B`

**KROK 1: Faktoryzacja**
- **Reguła**: `XY ∨ X¬Y → X(Y ∨ ¬Y)`
- **Nazwa**: "Rozdzielność (faktoryzacja)"
- **Przykład**:
```
(A∧B∧C) ∨ (A∧B∧¬C) → A∧B∧(C∨¬C)
```

**KROK 2: Tautologia**
- **Reguła**: `Y ∨ ¬Y → 1`
- **Nazwa**: "Tautologia"
- **Przykład**:
```
A∧B∧(C∨¬C) → A∧B∧1
```

**KROK 3: Element neutralny**
- **Reguła**: `X ∧ 1 → X`
- **Nazwa**: "Element neutralny"
- **Przykład**:
```
A∧B∧1 → A∧B
```

### 9. Czyszczenie końcowe (absorpcja + idempotencja)
- **Cel**: Usunięcie nadmiarowych terminów z DNF
- **Metoda**: Stabilizacja (iteracja do momentu braku zmian)

**REGUŁA 1: Idempotencja (∨)**
- `X ∨ X → X`
- **Nazwa**: "Idempotencja (∨)"

**REGUŁA 2: Absorpcja (∨)**
- `X ∨ (X∧Y) → X`
- **Nazwa**: "Absorpcja (∨)"
- **Algorytm**: Jeśli term `T1` zawiera wszystkie literały termu `T2`, usuń `T2`

**Przykład**:
```
(A∧B) ∨ (A∧B∧C) → A∧B
```

---

## FAZA III: WERYFIKACJA I GARANCJE

### 10. Weryfikacja poprawności
- **Metoda**: Hash tablicy prawdy dla każdego kroku
- **Gwarancja**: `TT(before) == TT(after)` dla wszystkich kroków

### 11. Weryfikacja minimalności
- **Kryterium**: Liczba literałów w wyniku ≤ liczba literałów w QM minimal DNF
- **Fallback**: Jeśli prawa nie osiągają minimalności, użyj QM result

### 12. Ciągłość kroków
- **Gwarancja**: `steps[i-1].after_str == steps[i].before_str` (po kanonizacji)
- **Enforcement**: Każdy krok operuje na pełnym AST, nie na poddrzewie

### 13. Limit zmiennych
- **Ograniczenie**: ≤ 8 zmiennych (QM wykładniczy)
- **Powód**: Tablica prawdy 2^n, Petrick's method ma złożoność wykładniczą

---

## PEŁNA LISTA PRAW LOGICZNYCH

### 1. Negacja
- `¬1` → `0`
- `¬0` → `1`
- `¬(¬A)` → `A`

### 2. De Morgan
- `¬(A ∧ B)` → `¬A ∨ ¬B`
- `¬(A ∨ B)` → `¬A ∧ ¬B`

### 3. Idempotencja
- `A ∧ A` → `A`
- `A ∨ A` → `A`

### 4. Element neutralny
- `A ∧ 1` → `A`
- `A ∨ 0` → `A`

### 5. Element pochłaniający
- `A ∧ 0` → `0`
- `A ∨ 1` → `1`

### 6. Kontradykcja
- `A ∧ ¬A` → `0`

### 7. Tautologia / Dopełnienie
- `A ∨ ¬A` → `1`

### 8. Dystrybutywność
- `A ∧ (B ∨ C)` → `(A ∧ B) ∨ (A ∧ C)`
- `A ∨ (B ∧ C)` → `(A ∨ B) ∧ (A ∨ C)`

### 9. Absorpcja
- `A ∨ (A ∧ B)` → `A`
- `A ∧ (A ∨ B)` → `A`
- `A ∨ (¬A ∧ B)` → `A ∨ B`
- `A ∧ (¬A ∨ B)` → `A ∧ B`

### 10. Faktoryzacja
- `(A∧X) ∨ (A∧Y)` → `A∧(X∨Y)`
- `(A∨X) ∧ (A∨Y)` → `A∨(X∧Y)` (dual)

### 11. Konsensus (SOP)
- `AB ∨ ¬AC ∨ BC` → `AB ∨ ¬AC`

### 12. Pokrywanie
- `A ∨ (A ∧ B)` → `A` (SOP)
- `A ∧ (A ∨ B)` → `A` (POS)

### 13. Redundancja (POS)
- `(A∨B∨C) ∧ (A∨B)` → `A∨B` (tautologia usuwana)

---

## PRZYKŁAD KOMPLETNY: A∧(B→C)

### Input: `A ∧ (B → C)`

**KROK 1: Implikacja** (`rules.py` A1)
```
A ∧ (B → C)
```
**De Morgan / Implikacja**:
```
A ∧ (¬B ∨ C)
```

**KROK 2: Dystrybutywność**
```
A ∧ (¬B ∨ C)
```
**Rozdzielność**:
```
(A ∧ ¬B) ∨ (A ∧ C)
```

**KROK 3: QM Bridge** (jeśli potrzebne)
- QM plan: minimal DNF = `(A ∧ ¬B) ∨ (A ∧ C)` (już minimalne!)

**Wynik**: `(A ∧ ¬B) ∨ (A ∧ C)` ✓

---

## GARANCJE SYSTEMU

### 1. Poprawność (Correctness)
- ✅ `TT(input) == TT(output)` dla ≤ 8 zmiennych
- ✅ Każdy krok zweryfikowany hashem TT

### 2. Minimalność (Minimality)
- ✅ `literals(result) ≤ literals(QM_minimal)`
- ✅ Fallback do QM jeśli prawa nie osiągają minimum

### 3. Boolean Laws Only in UI
- ✅ Cała ścieżka w UI to wyłącznie prawa Boole'a
- ✅ QM działa jako planista (niewidoczny)
- ✅ Brak "kroków QM" w interfejsie

### 4. Ciągłość (Continuity)
- ✅ `prev.after_str == next.before_str` dla wszystkich kroków
- ✅ Każdy krok operuje na pełnym AST

### 5. Zbieżność (Convergence)
- ✅ Stabilizacja po max 50 iteracjach
- ✅ Detekcja oscylacji (early stop)
- ✅ Maksymalnie 100 kroków głównych

---

## PRZYKŁAD ZŁOŻONY: (A∧B∧C)∨(A∧B∧¬C)∨(A∧C∧¬B)∨(B∧C∧¬A)

### QM Minimal: `(B∧C) ∨ (A∧C) ∨ (A∧B)`

**Kroki upraszczania**:

**KROK 1-3**: Merge `(A∧B∧C)` + `(A∧B∧¬C)` → `A∧B`
- Factoring: `(A∧B∧C) ∨ (A∧B∧¬C)` → `A∧B∧(C∨¬C)`
- Tautology: `A∧B∧(C∨¬C)` → `A∧B∧1`
- Neutral: `A∧B∧1` → `A∧B`

**KROK 4**: Cleanup (absorpcja niepotrzebna w tym przypadku)

**KROK 5-7**: Merge `(A∧C∧¬B)` + `(B∧C∧¬A)` → `C` (jeśli QM wymaga)

**Wynik finalny**: `A∧B ∨ A∧C ∨ B∧C` (12 literałów → 6 literałów) ✓

---

## BIBLIOGRAFIA

- Quine, W.V. (1955). "A way to simplify truth functions"
- McCluskey, E.J. (1956). "Minimization of Boolean functions"
- Petrick, S.R. (1956). "A direct determination of the irredundant forms of a Boolean function"
- Brown, F.M. (2012). "Boolean Reasoning: The Logic of Boolean Equations"
- Knuth, D.E. (2011). "The Art of Computer Programming, Volume 4A"

---

**Data utworzenia**: 2025-01-11  
**Wersja**: 1.0  
**Projekt**: LogicEngine

