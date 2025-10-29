# SILNIK UPRASZCZANIA WYRAŻEŃ LOGICZNYCH LOGICENGINE
## Szczegółowy opis algorytmiczny i naukowy

---

## 1. ARCHITEKTURA SYSTEMU

### 1.1 Struktura modułów
- **`parser.py`**: Walidacja i standaryzacja składni wyrażeń logicznych
- **`ast.py`**: Generacja i normalizacja drzewa składniowego (AST)
- **`laws.py`**: Implementacja praw algebraicznych i główny silnik upraszczania
- **`axioms.py`**: System aksjomatyczny z unifikacją meta-zmiennych
- **`validation.py`**: Walidacja składniowa wyrażeń

### 1.2 Przepływ danych
```
Wyrażenie wejściowe → Parser → AST → Normalizacja → Upraszczanie → Wynik
```

---

## 2. PARSER I WALIDACJA

### 2.1 Standaryzacja składni i tokenizacja (`validation.standardize`)
**Źródło prawdy:** Moduł `validation.py` (parser deleguje tutaj).

**Tokenizacja (greedy):**
- Pomija białe znaki, rozpoznaje nawiasy, stałe, operatory i identyfikatory.
- Operatory rozpoznawane zachłannie (najdłuższe dopasowanie najpierw).

**Obsługiwane identyfikatory zmiennych:**
- Wzorzec: `[A-Za-z][A-Za-z0-9_]*` (małe/wielkie litery, cyfry, podkreślenia)
- Przykłady: `a`, `A1`, `foo_bar3`, `X`, `y_2`

**Mapowanie operatorów na symbole kanoniczne:**
- Unary: `!`, `~`, `¬` → `¬`
- Binary: `&`, `&&`, `∧` → `∧`; `|`, `||`, `+`, `∨` → `∨`;
  `^`, `<>`, `⊕` → `⊕`; `->`, `=>`, `→` → `→`;
  `<->`, `<=>`, `==`, `=`, `≡`, `↔` → `↔`

**Kolejność przetwarzania:** Dłuższe operatory mają pierwszeństwo (np. `&&` przed `&`, `<=>` przed `<->`).

**Przykłady standaryzacji:**
- `A && B` → `A∧B`
- `a <-> b` → `a↔b`
- `A || B == C` → `A∨B↔C`
- `A <> B` → `A⊕B`

**Złożoność**: O(n), gdzie n = długość wyrażenia

### 2.2 Walidacja składniowa (`validation.validate`)
**Algorytm automatu skończonego nad tokenami:**

**Stany automatu:**
- `operand` (VAR/CONST lub `(` lub NOT)
- `operator` (BINOP lub `)`)

**Pseudokod walidacji (nad listą tokenów):**
```
ALGORYTM: Walidacja składniowa wyrażenia logicznego
WEJŚCIE: wyrażenie (ciąg znaków)
WYJŚCIE: PRAWDA jeśli poprawne, BŁĄD jeśli niepoprawne

1.  głębokość_nawiasów := 0
2.  poprzedni_stan := START
3.  
4.  DLA każdego tokenu t:
5.      JEŚLI t.kind ∈ {VAR, CONST}:
6.          JEŚLI poprzedni_stan = ')' LUB poprzedni_stan = 'var':
7.              RZUĆ BŁĄD: "Brak operatora między zmiennymi"
8.          poprzedni_stan := 'var'
9.      
10.     INACZEJ JEŚLI t.kind = LPAREN:
11.         JEŚLI poprzedni_stan = 'var' LUB poprzedni_stan = ')':
12.             RZUĆ BŁĄD: "Brak operatora przed nawiasem"
13.         głębokość_nawiasów := głębokość_nawiasów + 1
14.         poprzedni_stan := '('
15.     
16.     INACZEJ JEŚLI t.kind = RPAREN:
17.         JEŚLI poprzedni_stan = 'op' LUB poprzedni_stan = '(':
18.             RZUĆ BŁĄD: "Puste nawiasy lub operator przed ')'"
19.         głębokość_nawiasów := głębokość_nawiasów - 1
20.         JEŚLI głębokość_nawiasów < 0:
21.             RZUĆ BŁĄD: "Niezgodna liczba nawiasów"
22.         poprzedni_stan := ')'
23.     
24.     INACZEJ JEŚLI t.kind to operator:
25.         JEŚLI t.kind = NOT:
26.             JEŚLI poprzedni_stan = 'var' LUB poprzedni_stan = ')':
27.                 RZUĆ BŁĄD: "Nieprawidłowe użycie negacji"
28.             poprzedni_stan := 'op'
29.         INACZEJ (operator binarny):
30.             JEŚLI poprzedni_stan ≠ 'var' I poprzedni_stan ≠ ')':
31.                 RZUĆ BŁĄD: "Operator binarny w niepoprawnym miejscu"
32.             poprzedni_stan := 'op'
33.     
34.     INACZEJ:
35.         RZUĆ BŁĄD: "Nieoczekiwany token"
36. 
37. JEŚLI głębokość_nawiasów ≠ 0:
38.     RZUĆ BŁĄD: "Niezgodna liczba nawiasów"
39. 
40. JEŚLI poprzedni_stan = 'op':
41.     RZUĆ BŁĄD: "Wyrażenie nie może kończyć się operatorem"
42. 
43. ZWRÓĆ PRAWDA
```

**Reguły przejść między stanami (na poziomie tokenów):**
```python
# Poprawne przejścia:
var → op     # A ∧ B (zmienna po operatorze binarnym)
op → var     # A ∧ B (operator po zmiennej)
op → (       # A ∧ (B ∨ C) (operator przed nawiasem)
( → var      # (A ∧ B) (nawias przed zmienną)
( → op       # (¬A) (nawias przed negacją)
) → op       # (A ∧ B) ∨ C (nawias przed operatorem)
) → )        # ((A ∧ B)) (nawias przed nawiasem)

# Błędne przejścia (rzucają wyjątek):
var → (      # A (B - brak operatora między zmienną a nawiasem
var → var    # A B - brak operatora między zmiennymi
op → op      # ∧ ∨ - operator po operatorze
( → )        # () - puste nawiasy
) → var      # ) A - brak operatora po nawiasie
```

**Przykład działania automatu (po standaryzacji):**
```
Wyrażenie: A ∧ (B ∨ ¬C)

Stan: START
Token: A → Stan: var

Stan: var  
Token: ∧ → Stan: op

Stan: op
Token: ( → Stan: (

Stan: (
Token: B → Stan: var

Stan: var
Token: ∨ → Stan: op

Stan: op
Token: ¬ → Stan: op (negacja)

Stan: op
Token: C → Stan: var

Stan: var
Token: ) → Stan: )

Stan: )
Token: EOF → Stan: ACCEPT
```

**Złożoność**: O(n)

---

## 3. GENERACJA DRZEWA SKŁADNIOWEGO (AST)

### 3.1 Parser Pratt (`parse_expression`)
**Algorytm rekurencyjnego parsowania z precedencją:**

**Pseudokod parsera Pratt:**
```
ALGORYTM: Parser Pratt z precedencją operatorów
WEJŚCIE: strumień tokenów, minimalna precedencja
WYJŚCIE: węzeł AST

1.  lewy_operand := PARSER_UNARY_LUB_PODSTAWOWY(strumień)
2.  
3.  DOPÓKI PRAWDA:
4.      operator := PEEK(strumień)  // Sprawdź następny token bez pobierania
5.      
6.      JEŚLI operator nie jest w PRECEDENCJA LUB operator = '¬':
7.          PRZERWIJ pętlę
8.      
9.      precedencja_operatora := PRECEDENCJA[operator]
10.     
11.     JEŚLI precedencja_operatora < minimalna_precedencja:
12.         PRZERWIJ pętlę
13.     
14.     NEXT(strumień)  // Pobierz operator ze strumienia
15.     
16.     JEŚLI operator jest prawostronnie łączny:
17.         następna_minimalna := precedencja_operatora
18.     INACZEJ:
19.         następna_minimalna := precedencja_operatora + 1
20.     
21.     prawy_operand := PARSER_WYRAŻENIE(strumień, następna_minimalna)
22.     
23.     lewy_operand := STWÓRZ_WĘZEŁ(operator, lewy_operand, prawy_operand)
24. 
25. ZWRÓĆ lewy_operand
```

**Implementacja Python:**
```python
def parse_expression(ts: TokenStream, min_prec: int = 0):
    # Parsowanie lewego operandu
    left = parse_unary_or_primary(ts)
    
    # Parsowanie operatorów binarnych z precedencją
    while True:
        op = ts.peek()
        if op not in PRECEDENCE or op == '¬':
            break
        prec = PRECEDENCE[op]
        if prec < min_prec:
            break
        
        ts.next()
        next_min = prec + (0 if op in RIGHT_ASSOC else 1)
        right = parse_expression(ts, next_min)
        left = {"node": op, "left": left, "right": right}
    
    return left
```

**Precedencja operatorów:**
- `¬` (negacja): 5 (najwyższa)
- `∧` (koniunkcja): 4
- `∨` (alternatywa): 3
- `→` (implikacja): 2
- `↔` (równoważność): 1 (najniższa)

**Złożoność**: O(n)

### 3.2 Kanonizacja AST (`_canonicalize`)
**Algorytm normalizacji struktury:**
1. **Mapowanie węzłów**: Konwersja różnych formatów na standardowy
2. **Obsługa operatorów n-arnych**: Rozwijanie do postaci binarnej
3. **Walidacja struktury**: Sprawdzenie poprawności węzłów

---

## 4. NORMALIZACJA BOOLE'OWSKA

### 4.1 Konwersja do postaci boolowskiej (`_to_bool_norm`)
**Mapowanie operatorów:**
- `¬` → `{"op": "NOT", "child": ...}`
- `∧` → `{"op": "AND", "args": [...]}`
- `∨` → `{"op": "OR", "args": [...]}`
- `→` → `{"op": "IMP", "left": ..., "right": ...}`
- `↔` → `{"op": "IFF", "left": ..., "right": ...}`

### 4.2 Rozwijanie implikacji i równoważności (`_expand_imp_iff`)
**Reguły transformacji:**
- **Implikacja**: `p → q` → `¬p ∨ q`
- **Równoważność**: `p ↔ q` → `(p ∧ q) ∨ (¬p ∧ ¬q)`

**Złożoność**: O(n), gdzie n = liczba węzłów AST

### 4.3 Spłaszczanie i deduplikacja (`_flatten_sort_dedupe`)
**Algorytm:**
1. **Spłaszczanie**: Rozwijanie zagnieżdżonych operatorów tego samego typu
   - `A ∧ (B ∧ C)` → `A ∧ B ∧ C`
2. **Deduplikacja**: Usuwanie duplikatów argumentów
3. **Sortowanie**: Porządkowanie według `canonical_str`

**Złożoność**: O(n log n) - sortowanie

---

## 5. SYSTEM PRAW ALGEBRAICZNYCH

### 5.1 Architektura `laws_matches`
**Algorytm iteracyjnego przeszukiwania AST:**

```python
def laws_matches(node: Any) -> List[Dict[str, Any]]:
    out = []
    for path, sub in iter_nodes(node):
        if isinstance(sub, dict):
            op = sub.get("op")
            # Testowanie każdego prawa dla danego operatora
            apply_laws_for_operator(op, sub, path, out)
    return out
```

### 5.2 Kategorie praw logicznych

#### 5.2.1 Prawa negacji
- **Negacja stałej**: `¬1 = 0`, `¬0 = 1`
- **Podwójna negacja**: `¬(¬X) = X`
- **De Morgan**: 
  - `¬(A ∧ B) = ¬A ∨ ¬B`
  - `¬(A ∨ B) = ¬A ∧ ¬B`

#### 5.2.2 Prawa idempotentności
- **Idempotentność AND**: `X ∧ X = X`
- **Idempotentność OR**: `X ∨ X = X`

#### 5.2.3 Prawa elementów neutralnych i pochłaniających
- **Element neutralny AND**: `X ∧ 1 = X`
- **Element neutralny OR**: `X ∨ 0 = X`
- **Element pochłaniający AND**: `X ∧ 0 = 0`
- **Element pochłaniający OR**: `X ∨ 1 = 1`

#### 5.2.4 Prawa kontradykcji i dopełnienia
- **Kontradykcja**: `A ∧ ¬A = 0`
- **Dopełnienie**: `A ∨ ¬A = 1`

#### 5.2.5 Prawa dystrybutywności
- **Dystrybutywność AND**: `A ∧ (B ∨ C) = (A ∧ B) ∨ (A ∧ C)`
- **Dystrybutywność OR**: `A ∨ (B ∧ C) = (A ∨ B) ∧ (A ∨ C)`

#### 5.2.6 Prawa absorpcji
- **Absorpcja OR**: `X ∨ (X ∧ Y) = X`
- **Absorpcja AND**: `X ∧ (X ∨ Y) = X`
- **Absorpcja z negacją**: `X ∨ (¬X ∧ Y) = X ∨ Y`

### 5.3 Prawa SOP (Sum of Products) i POS (Product of Sums)

#### 5.3.1 Konsensus SOP
**Algorytm:**
```python
for var in variables:
    pos_terms = [term - {var} for term in terms if var in term]
    neg_terms = [term - {¬var} for term in terms if ¬var in term]
    for P in pos_terms:
        for N in neg_terms:
            consensus = P ∪ N
            if consensus in terms:
                remove_consensus_from_terms()
```

**Reguła**: `XY + X'Z + YZ = XY + X'Z`

#### 5.3.2 Faktoryzacja SOP
**Algorytm:**
```python
for i, j in combinations(terms, 2):
    common = terms[i] ∩ terms[j]
    if common:
        rest1 = terms[i] - common
        rest2 = terms[j] - common
        factored = common ∧ (rest1 ∨ rest2)
        if measure(factored) < measure(original):
            apply_factorization()
```

#### 5.3.3 Pokrywanie POS (dual)
**Algorytm dualny do SOP:**
- Krótsze sumy pokrywają dłuższe
- `(A ∨ B) ∧ (A ∨ B ∨ C) = (A ∨ B)`

---

## 6. SYSTEM AKSJOMATYCZNY

### 6.1 Meta-zmienne i unifikacja
**Definicja meta-zmiennej:**
```python
def META(name: str) -> Dict[str, Any]:
    return {"op": "META", "name": name}
```

**Pseudokod algorytmu unifikacji:**
```
ALGORYTM: Unifikacja wzorca z termem
WEJŚCIE: wzorzec, term, środowisko_wiazań
WYJŚCIE: środowisko_wiazań jeśli sukces, NULL jeśli brak unifikacji

1.  JEŚLI środowisko_wiazań jest NULL:
2.      środowisko_wiazań := słownik_pusty
3.  
4.  JEŚLI wzorzec to meta-zmienna:
5.      nazwa_zmiennej := wzorzec.nazwa
6.      
7.      JEŚLI nazwa_zmiennej w środowisko_wiazań:
8.          // Sprawdź czy istniejące wiązanie unifikuje się z termem
9.          ZWRÓĆ UNIFIKUJ(środowisko_wiazań[nazwa_zmiennej], term, środowisko_wiazań)
10.     INACZEJ:
11.         // Nowe wiązanie
12.         środowisko_wiazań[nazwa_zmiennej] := term
13.         ZWRÓĆ środowisko_wiazań
14. 
15. JEŚLI wzorzec to stała:
16.     JEŚLI term to stała I wzorzec.wartość = term.wartość:
17.         ZWRÓĆ środowisko_wiazań
18.     INACZEJ:
19.         ZWRÓĆ NULL
20. 
21. JEŚLI wzorzec to zmienna:
22.     JEŚLI term to zmienna I wzorzec.nazwa = term.nazwa:
23.         ZWRÓĆ środowisko_wiazań
24.     INACZEJ:
25.         ZWRÓĆ NULL
26. 
27. JEŚLI wzorzec to operator I term to operator:
28.     JEŚLI wzorzec.typ ≠ term.typ:
29.         ZWRÓĆ NULL
30.     
31.     JEŚLI wzorzec.typ = "NOT":
32.         ZWRÓĆ UNIFIKUJ(wzorzec.dziecko, term.dziecko, środowisko_wiazań)
33.     
34.     JEŚLI wzorzec.typ w {"AND", "OR"}:
35.         JEŚLI wzorzec.argumenty.length ≠ term.argumenty.length:
36.             ZWRÓĆ NULL
37.         
38.         DLA i := 0 DO wzorzec.argumenty.length - 1:
39.             środowisko_wiazań := UNIFIKUJ(wzorzec.argumenty[i], term.argumenty[i], środowisko_wiazań)
40.             JEŚLI środowisko_wiazań jest NULL:
41.                 ZWRÓĆ NULL
42.         
43.         ZWRÓĆ środowisko_wiazań
44. 
45. ZWRÓĆ NULL
```

**Implementacja Python:**
```python
def unify(pattern: Any, term: Any, env: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
    # Meta-zmienna - nowe wiązanie
    if pattern["op"] == "META":
        if pattern["name"] in env:
            return unify(env[pattern["name"]], term, env)
        else:
            env[pattern["name"]] = term
            return env
    
    # Operator - rekurencyjna unifikacja argumentów
    if pattern["op"] == term["op"]:
        return unify_arguments(pattern, term, env)
    
    return None  # Brak unifikacji
```

**Złożoność**: O(n), gdzie n = rozmiar wzorca

### 6.2 Aksjomaty logiczne
**Aksjomat A1 (Implikacja → OR):**
- **Wzorzec**: `p → q`
- **Transformacja**: `¬p ∨ q`
- **Kierunek**: `lhs2rhs`

**Aksjomat A2 (Równoważność → CNF):**
- **Wzorzec**: `p ↔ q`
- **Transformacja**: `(p ∧ q) ∨ (¬p ∧ ¬q)`
- **Kierunek**: `lhs2rhs`

**Aksjomat A12 (Reductio ad absurdum):**
- **Wzorzec**: `p → (q ∧ ¬q)`
- **Transformacja**: `¬p`
- **Kierunek**: `lhs2rhs`

### 6.3 Instancjacja aksjomatów (`instantiate`)
**Algorytm podstawiania:**
```python
def instantiate(pattern: Any, env: Dict[str, Any]) -> Any:
    if pattern["op"] == "META":
        return instantiate(env[pattern["name"]], env)
    
    result = pattern.copy()
    for key in ["left", "right", "child", "args"]:
        if key in pattern:
            result[key] = instantiate(pattern[key], env)
    
    return result
```

---

## 7. ALGORYTM UPRASZCZANIA

### 7.1 Główny silnik (`simplify_with_laws`)
**Algorytm iteracyjny:**

**Pseudokod głównego silnika upraszczania:**
```
ALGORYTM: Upraszczanie wyrażeń logicznych
WEJŚCIE: wyrażenie (ciąg znaków), maksymalna_liczba_kroków
WYJŚCIE: wynik uproszczony, lista kroków

1.  ast := GENERUJ_AST(wyrażenie)
2.  węzeł := NORMALIZUJ_BOOL_AST(ast, rozwiń_implikacje=PRAWDA)
3.  kroki := []
4.  widziane_wyrażenia := zbiór_pusty
5.  
6.  DLA krok := 1 DO maksymalna_liczba_kroków:
7.      dopasowania := []
8.      
9.      // Zbierz dopasowania praw algebraicznych
10.     dopasowania_algebraiczne := ZNAJDŹ_PRAWA_ALGEBRAICZNE(węzeł)
11.     DLA każdego dopasowania w dopasowania_algebraiczne:
12.         dopasowanie.źródło := "algebraiczne"
13.         dopasowania.DODAJ(dopasowanie)
14.     
15.     // Zbierz dopasowania aksjomatów
16.     dopasowania_aksjomatów := ZNAJDŹ_AKSJOMATY(węzeł)
17.     DLA każdego dopasowania w dopasowania_aksjomatów:
18.         dopasowanie.źródło := "aksjomat"
19.         dopasowania.DODAJ(dopasowanie)
20.     
21.     JEŚLI dopasowania jest puste:
22.         PRZERWIJ pętlę
23.     
24.     // Wybierz najlepsze dopasowanie
25.     wybór := WYBIERZ_NAJLEPSZE(węzeł, dopasowania)
26.     JEŚLI wybór jest PUSTY:
27.         PRZERWIJ pętlę
28.     
29.     // Zastosuj transformację
30.     wyrażenie_przed := PRETTY_PRINT(węzeł)
31.     węzeł := ZASTOSUJ_TRANSFORMACJĘ(węzeł, wybór.ścieżka, wybór.po)
32.     węzeł := NORMALIZUJ_BOOL_AST(węzeł)
33.     wyrażenie_po := PRETTY_PRINT(węzeł)
34.     
35.     // Sprawdź oscylację
36.     JEŚLI wyrażenie_po w widziane_wyrażenia:
37.         krok_oscylacji := STWÓRZ_KROK_OSYLACJI(wybór, wyrażenie_przed, wyrażenie_po)
38.         kroki.DODAJ(krok_oscylacji)
39.         PRZERWIJ pętlę
40.     
41.     widziane_wyrażenia.DODAJ(wyrażenie_po)
42.     
43.     // Zapisz krok
44.     krok := STWÓRZ_KROK(wybór, wyrażenie_przed, wyrażenie_po)
45.     kroki.DODAJ(krok)
46.     
47.     JEŚLI wyrażenie_przed = wyrażenie_po:
48.         PRZERWIJ pętlę
49. 
50. ZWRÓĆ {"wynik": PRETTY_PRINT(węzeł), "kroki": kroki}
```

**Implementacja Python:**
```python
def simplify_with_laws(expr: str, max_steps: int = 80) -> Dict[str, Any]:
    # 1. Parsowanie i normalizacja
    ast = generate_ast(expr)
    node = normalize_bool_ast(ast, expand_imp_iff=True)
    
    steps = []
    seen_expressions = set()  # Detekcja oscylacji
    
    for step in range(max_steps):
        # 2. Zbieranie dopasowań
        matches = []
        matches.extend(laws_matches(node))      # Prawa algebraiczne
        matches.extend(axioms_matches(node))    # Aksjomaty
        
        if not matches:
            break
        
        # 3. Wybór najlepszego dopasowania
        choice = pick_best(node, matches)
        if not choice:
            break
        
        # 4. Zastosowanie transformacji
        before_str = pretty(node)
        node = set_by_path(node, choice["path"], choice["after"])
        node = normalize_bool_ast(node)
        after_str = pretty(node)
        
        # 5. Detekcja oscylacji
        if after_str in seen_expressions:
            steps.append(oscillation_step)
            break
        
        seen_expressions.add(after_str)
        
        # 6. Zapisywanie kroku
        steps.append(create_step_record(choice, before_str, after_str))
        
        if before_str == after_str:
            break
    
    return {"result": pretty(node), "steps": steps}
```

### 7.2 Funkcja oceny (`measure`)
**Metryka złożoności:**
```python
def measure(node: Any) -> Tuple[int, int, int]:
    return (
        count_literals(node),    # Liczba literałów
        count_nodes(node),       # Liczba węzłów AST
        len(pretty(node))        # Długość reprezentacji tekstowej
    )
```

**Kryteria preferencji:**
1. **Pierwszorzędne**: Mniejsza metryka złożoności
2. **Drugorzędne**: Prawa algebraiczne nad aksjomatami
3. **Trzeciorzędne**: Krótsza reprezentacja tekstowa

### 7.3 Wybór najlepszego dopasowania (`pick_best`)
**Pseudokod wyboru najlepszego dopasowania:**
```
ALGORYTM: Wybór najlepszego dopasowania
WEJŚCIE: węzeł_AST, lista_dopasowań
WYJŚCIE: najlepsze dopasowanie lub NULL

1.  najlepsze := NULL
2.  najlepsza_metryka := NULL
3.  
4.  DLA każdego dopasowania w lista_dopasowań:
5.      metryka_po := OBLICZ_METRYKĘ(dopasowanie.po)
6.      
7.      JEŚLI najlepsze jest NULL:
8.          najlepsze := dopasowanie
9.          najlepsza_metryka := metryka_po
10.         KONTYNUUJ
11.     
12.     JEŚLI metryka_po < najlepsza_metryka:
13.         najlepsze := dopasowanie
14.         najlepsza_metryka := metryka_po
15.     INACZEJ JEŚLI metryka_po = najlepsza_metryka:
16.         // Rozstrzygnięcie remisu
17.         JEŚLI dopasowanie.źródło = "algebraiczne" I najlepsze.źródło = "aksjomat":
18.             najlepsze := dopasowanie
19.             najlepsza_metryka := metryka_po
20.         INACZEJ JEŚLI dopasowanie.źródło = najlepsze.źródło:
21.             // Preferuj krótszą reprezentację tekstową
22.             JEŚLI DŁUGOŚĆ(PRETTY_PRINT(dopasowanie.po)) < DŁUGOŚĆ(PRETTY_PRINT(najlepsze.po)):
23.                 najlepsze := dopasowanie
24.                 najlepsza_metryka := metryka_po
25. 
26. ZWRÓĆ najlepsze
```

**Implementacja Python:**
```python
def pick_best(node: Any, matches: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    best = None
    best_measure = None
    
    for match in matches:
        after_measure = measure(match["after"])
        
        if best is None or after_measure < best_measure:
            best = match
            best_measure = after_measure
        elif after_measure == best_measure:
            # Tie-breaking: prefer algebraic over axiom
            if match["source"] == "algebraic" and best["source"] == "axiom":
                best = match
            elif match["source"] == best["source"]:
                # Prefer shorter string representation
                if len(pretty(match["after"])) < len(pretty(best["after"])):
                    best = match
    
    return best
```

---

## 8. DETEKCJA OSYLACJI

### 8.1 Mechanizm ochrony
**Algorytm:**
```python
seen_expressions = set()

for step in range(max_steps):
    # ... zastosowanie transformacji ...
    
    if after_str in seen_expressions:
        # Oscylacja wykryta - zatrzymanie
        steps.append(oscillation_step)
        break
    
    seen_expressions.add(after_str)
```

**Złożoność**: O(1) - operacje na zbiorze hash

### 8.2 Warunki zakończenia
1. **Brak dopasowań**: `matches == []`
2. **Oscylacja**: `after_str in seen_expressions`
3. **Maksymalna liczba kroków**: `step >= max_steps`
4. **Brak postępu**: `before_str == after_str`

---

## 9. REPREZENTACJA WYRAŻEŃ

### 9.1 Minimalizacja nawiasów (`canonical_str_minimal`)
**Algorytm oparty na precedencji operatorów:**

```python
def canonical_str_minimal(node: Any, parent_precedence: int = 0) -> str:
    # Precedencja: NOT (100) > AND (2) > OR (3)
    
    if node["op"] == "NOT":
        child_str = canonical_str_minimal(node["child"], 100)
        result = f"¬{child_str}"
        return result if parent_precedence <= 0 or 100 < parent_precedence else f"({result})"
    
    if node["op"] in {"AND", "OR"}:
        symbol = "∧" if node["op"] == "AND" else "∨"
        my_prec = 2 if node["op"] == "AND" else 3
        
        parts = []
        for arg in node["args"]:
            arg_prec = get_precedence(arg)
            arg_parent_prec = my_prec if arg_prec >= my_prec else 0
            parts.append(canonical_str_minimal(arg, arg_parent_prec))
        
        result = f" {symbol} ".join(parts)
        return result if parent_precedence <= 0 or my_prec < parent_precedence else f"({result})"
```

**Reguły nawiasowania:**
- Nawiasy dodawane tylko gdy konieczne dla zachowania precedencji
- Usuwanie nadmiarowych nawiasów zewnętrznych
- Zachowanie nawiasów dla złożonych wyrażeń w negacji

---

## 10. ANALIZA ZŁOŻONOŚCI

### 10.1 Złożoność czasowa
- **Parsowanie**: O(n)
- **Normalizacja**: O(n log n) - sortowanie argumentów
- **Upraszczanie**: O(k × m × n), gdzie:
  - k = maksymalna liczba kroków (80)
  - m = średnia liczba dopasowań na krok
  - n = rozmiar AST
- **Unifikacja**: O(n) na dopasowanie
- **Całkowita**: O(k × m × n)

### 10.2 Złożoność pamięciowa
- **AST**: O(n)
- **Historia kroków**: O(k × n)
- **Zbiór widzianych wyrażeń**: O(k)
- **Całkowita**: O(k × n)

### 10.3 Optymalizacje
1. **Wczesne zatrzymanie**: Przy braku postępu
2. **Detekcja oscylacji**: O(1) sprawdzenie w zbiorze hash
3. **Leniwe obliczanie**: Dopasowania obliczane tylko gdy potrzebne
4. **Cachowanie**: Powtarzające się podwyrażenia

---

## 11. WŁAŚCIWOŚCI ALGORYTMU

### 11.1 Zbieżność
- **Gwarancja**: Algorytm zawsze zbiega (skończona liczba kroków)
- **Optymalność**: Nie gwarantuje globalnego optimum
- **Determinizm**: Wynik zależy od kolejności testowania praw

### 11.2 Kompletność
- **Prawa algebraiczne**: Pokrywają podstawowe transformacje boolowskie
- **Aksjomaty**: Rozszerzają możliwości o wzorce logiczne
- **SOP/POS**: Specjalizowane prawa dla form normalnych

### 11.3 Poprawność
- **Zachowanie semantyki**: Wszystkie transformacje zachowują wartość logiczną
- **Weryfikacja**: Każdy krok może być zweryfikowany przez podstawienie
- **Idempotentność**: Wielokrotne zastosowanie nie zmienia wyniku

---

## 12. PRZYKŁADY DZIAŁANIA

### 12.1 Przykład 1: Podstawowe upraszczanie
**Wejście**: `A ∧ (A ∨ B)`
**Kroki**:
1. **Absorpcja AND**: `A ∧ (A ∨ B)` → `A`
**Wynik**: `A`

### 12.2 Przykład 2: Złożone wyrażenie
**Wejście**: `(A → B) ∧ (B → C)`
**Kroki**:
1. **A1 (implikacja)**: `(A → B)` → `(¬A ∨ B)`
2. **A1 (implikacja)**: `(B → C)` → `(¬B ∨ C)`
3. **Dystrybutywność**: `(¬A ∨ B) ∧ (¬B ∨ C)` → `(¬A ∧ ¬B) ∨ (¬A ∧ C) ∨ (B ∧ ¬B) ∨ (B ∧ C)`
4. **Kontradykcja**: `(B ∧ ¬B)` → `0`
5. **Element neutralny**: `(¬A ∧ ¬B) ∨ (¬A ∧ C) ∨ 0 ∨ (B ∧ C)` → `(¬A ∧ ¬B) ∨ (¬A ∧ C) ∨ (B ∧ C)`

### 12.3 Przykład 3: Detekcja oscylacji
**Wejście**: `A ∨ (¬A ∧ B)`
**Kroki**:
1. **Absorpcja z negacją**: `A ∨ (¬A ∧ B)` → `A ∨ B`
2. **Rozdzielność**: `A ∨ B` → `(A ∨ A) ∨ (A ∨ B)` (przykład oscylacji)
3. **Zatrzymanie**: Wykrycie oscylacji

---

## 13. ROZSZERZENIA I MODYFIKACJE

### 13.1 Dodawanie nowych praw
**Procedura**:
1. Implementacja w `laws_matches`
2. Dodanie testów jednostkowych
3. Weryfikacja zachowania semantyki
4. Dokumentacja reguły

### 13.2 Dodawanie nowych aksjomatów
**Procedura**:
1. Definicja wzorca w `AXIOMS`
2. Implementacja kierunku transformacji
3. Testowanie unifikacji
4. Weryfikacja poprawności logicznej

### 13.3 Optymalizacje wydajności
1. **Cachowanie dopasowań**: Zapamiętywanie wyników `laws_matches`
2. **Równoległe przetwarzanie**: Testowanie praw niezależnie
3. **Heurystyki**: Priorytetyzacja praw według skuteczności
4. **Kompresja AST**: Optymalizacja reprezentacji

---

## 14. WNIOSKI

Silnik upraszczania LogicEngine implementuje zaawansowany system transformacji wyrażeń logicznych, łączący:

1. **Podejście algebraiczne**: Bezpośrednie zastosowanie praw boolowskich
2. **System aksjomatyczny**: Unifikacja wzorców z meta-zmiennymi
3. **Detekcję oscylacji**: Ochrona przed nieskończonymi pętlami
4. **Optymalizację nawiasów**: Minimalizacja reprezentacji tekstowej

Algorytm zapewnia zbieżność, poprawność i efektywność, oferując kompletne narzędzie do analizy i upraszczania wyrażeń logicznych w kontekście edukacyjnym i badawczym.

**Złożoność całkowita**: O(k × m × n), gdzie k ≤ 80, m = średnia liczba dopasowań, n = rozmiar wyrażenia.

**Gwarancje**: Zbieżność w skończonej liczbie kroków, zachowanie semantyki logicznej, detekcja oscylacji.
