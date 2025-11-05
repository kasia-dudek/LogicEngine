# Jak działa upraszczanie prawami logicznymi w programie LogicEngine

## Wprowadzenie

Ten dokument opisuje **bardzo szczegółowo**, krok po kroku, jak program upraszcza wyrażenia logiczne używając praw logicznych. Opis jest przeznaczony dla osób, które znają trochę matematyki (w szczególności logikę matematyczną), ale nie znają programowania.

Wyrażenie logiczne to na przykład: `(A∧B)∨(A∧C)∨D`, gdzie:
- `A`, `B`, `C`, `D` to zmienne (mogą być prawdziwe lub fałszywe)
- `∧` oznacza "i" (koniunkcja)
- `∨` oznacza "lub" (alternatywa)
- `¬` oznacza "nie" (negacja)

Celem programu jest przekształcenie dowolnego wyrażenia logicznego w **minimalną formę DNF** (Disjunctive Normal Form - Suma Iloczynów), czyli najprostszą możliwą postać, która jest równoważna oryginalnemu wyrażeniu.

---

## Faza 1: Przygotowanie wyrażenia

### Krok 1.1: Walidacja i standaryzacja

Program najpierw sprawdza, czy wprowadzone wyrażenie jest poprawne składniowo. Na przykład:
- Czy wszystkie nawiasy są zamknięte?
- Czy operatory są użyte poprawnie?
- Czy zmienne są poprawnie nazwane?

Następnie wyrażenie jest **standaryzowane** - wszystkie różne sposoby zapisu tego samego operatora są zamieniane na jeden standardowy format. Na przykład:
- `&` i `AND` i `∧` → wszystkie stają się `∧`
- `|` i `OR` i `∨` → wszystkie stają się `∨`
- `!` i `NOT` i `¬` → wszystkie stają się `¬`

### Krok 1.2: Parsowanie do drzewa AST

Wyrażenie tekstowe jest zamieniane na **drzewo AST** (Abstract Syntax Tree - Abstrakcyjne Drzewo Składniowe). To jest sposób reprezentacji wyrażenia jako struktury drzewiastej, gdzie:
- Każdy węzeł reprezentuje operację (AND, OR, NOT) lub zmienną
- Liście drzewa to zmienne lub stałe (0, 1)
- Gałęzie łączą operacje z ich argumentami

Na przykład wyrażenie `(A∧B)∨C` jest reprezentowane jako:
```
        OR
       /  \
     AND   C
    /   \
   A     B
```

### Krok 1.3: Normalizacja AST

Drzewo AST jest **normalizowane** - wszystkie operacje, które można uprościć na tym etapie, są upraszczane:
- Implikacje (`→`) i równoważności (`↔`) są zamieniane na operacje AND, OR, NOT
- Zagnieżdżone operacje tego samego typu są spłaszczane (np. `(A∧B)∧C` staje się `A∧B∧C`)
- Kolejność argumentów jest standaryzowana (dla łatwiejszego porównywania)

### Krok 1.4: Sprawdzenie, czy wyrażenie jest już minimalne

Program sprawdza, czy wyrażenie jest już w minimalnej formie DNF. Robi to poprzez:
1. Sprawdzenie, czy wyrażenie jest w formie DNF (suma iloczynów)
2. Porównanie z wynikiem algorytmu Quine-McCluskey (który zawsze znajduje minimalną formę)
3. Jeśli wyrażenie jest już minimalne, program kończy pracę i wyświetla komunikat

---

## Faza 2: Upraszczanie prawami logicznymi (simplify_with_laws)

Jeśli wyrażenie nie jest już minimalne, program zaczyna je upraszczać używając praw logicznych.

### Krok 2.1: Główna pętla upraszczania

Program wykonuje pętlę, która może się powtórzyć maksymalnie 100 razy (lub mniej, jeśli nie ma już co upraszczać). W każdej iteracji:

1. **Wyszukiwanie możliwych przekształceń**: Program przeszukuje całe drzewo AST i szuka miejsc, gdzie można zastosować jakieś prawo logiczne.

2. **Zbieranie wszystkich możliwości**: Program znajduje wszystkie miejsca, gdzie można zastosować prawa logiczne. Na przykład:
   - Jeśli jest `A∧¬A`, można zastosować prawo kontradykcji
   - Jeśli jest `A∨A`, można zastosować prawo idempotencji
   - Jeśli jest `A∧(B∨C)`, można zastosować prawo dystrybutywności
   - I tak dalej...

3. **Filtrowanie**: Program usuwa z listy możliwości te przekształcenia, które już wcześniej próbował i które okazały się nieoptymalne.

### Krok 2.2: Wybór najlepszego prawa do zastosowania

Z wszystkich znalezionych możliwości program wybiera **jedno najlepsze** prawo do zastosowania. Wybór odbywa się według następującej hierarchii priorytetów:

**Priorytet 1 (najwyższy)**: Prawa, które eliminują kontradykcje, tautologie lub elementy neutralne:
- Kontradykcja: `A∧¬A = 0`
- Tautologia: `A∨¬A = 1`
- Element neutralny: `A∧1 = A` lub `A∨0 = A`

**Priorytet 2**: Prawa, które eliminują negacje:
- Podwójna negacja: `¬(¬A) = A`

**Priorytet 3**: Prawa absorpcji (bezpośrednie uproszczenie):
- Absorpcja: `A∨(A∧B) = A`

**Priorytet 4**: Prawa dystrybutywności i rozdzielności (rozszerzają wyrażenie, ale są potrzebne do osiągnięcia DNF):
- Dystrybutywność: `A∧(B∨C) = (A∧B)∨(A∧C)`

**Priorytet 5**: Prawa De Morgana (upraszczają strukturę):
- De Morgan: `¬(A∧B) = ¬A∨¬B` lub `¬(A∨B) = ¬A∧¬B`

**Priorytet 6**: Faktoryzacja (często pogarsza formę, ale może być potrzebna):
- Faktoryzacja: `(A∧B)∨(A∧C) = A∧(B∨C)`

Faktoryzacja jest potrzebna w dwóch sytuacjach:

1. **Podczas łączenia termów w procesie upraszczania do minimalnego DNF**: Gdy program łączy dwa termy, które różnią się tylko jedną zmienną (np. `(A∧B∧C)` i `(A∧B∧¬C)`), najpierw stosuje faktoryzację, aby wyciągnąć wspólny czynnik. Proces wygląda tak:
   - `(A∧B∧C)∨(A∧B∧¬C)` → faktoryzacja → `(A∧B)∧(C∨¬C)` → tautologia → `(A∧B)∧1` → element neutralny → `(A∧B)`
   - W tym przypadku faktoryzacja jest konieczna, aby móc połączyć termy i uprościć wyrażenie.

2. **W ogólnym upraszczaniu prawami logicznymi**: Program może znaleźć miejsca, gdzie dwa termy mają wspólny czynnik i można go wyciągnąć. Na przykład: `(A∧X)∨(A∧Y) = A∧(X∨Y)`. Jednak w tym kontekście faktoryzacja często **pogarsza** formę wyrażenia (bo przekształca sumę iloczynów w iloczyn sum), więc program stosuje ją tylko wtedy, gdy rzeczywiście poprawia miarę wyrażenia (zmniejsza liczbę literałów lub węzłów).

**Priorytet 7**: Konsensus (rzadko używany)

Konsensus to prawo, które pozwala usunąć redundantne termy. Działa ono według wzoru:
- `(A∧B)∨(¬A∧C)∨(B∧C) = (A∧B)∨(¬A∧C)`

Wzór ogólny: `XY ∨ X'Z ∨ YZ = XY ∨ X'Z`, gdzie `X'` oznacza negację `X`.

**Dlaczego to działa?** Term `(B∧C)` jest "pokryty" przez kombinację pierwszych dwóch termów. Jeśli `A` jest prawdziwe, to pierwszy term `(A∧B)` pokrywa przypadek `B`. Jeśli `A` jest fałszywe, to drugi term `(¬A∧C)` pokrywa przypadek `C`. W obu przypadkach trzeci term `(B∧C)` jest zbędny.

W programie konsensus jest rzadko używany, ponieważ:
- Logika jego wykrywania jest skomplikowana i może być błędna
- Często jest weryfikowany przez tabelę prawdy i odrzucany, jeśli nie jest równoważny
- Większość przypadków, które konsensus mógłby uprościć, jest już obsługiwana przez inne prawa (np. absorpcję)

**Priorytet 8**: Inne prawa

Pozostałe prawa logiczne, które mają niższy priorytet, to:

- **Negacja stałej**: `¬1 = 0`, `¬0 = 1` - proste przekształcenie negacji stałych logicznych
- **Idempotencja (∧)**: `X∧X = X` - usuwanie duplikatów w koniunkcji
- **Idempotencja (∨)**: `X∨X = X` - usuwanie duplikatów w alternatywie
- **Element pochłaniający (A∧0)**: `A∧0 = 0` - jeśli w koniunkcji jest fałsz, całość jest fałszywa
- **Element pochłaniający (A∨1)**: `A∨1 = 1` - jeśli w alternatywie jest prawda, całość jest prawdziwa
- **Absorpcja z negacją**: `X∨(¬X∧Y) = X∨Y` - uproszczenie alternatywy, gdy jeden z termów zawiera negację drugiego
- **Absorpcja z negacją (dual)**: `X∧(¬X∨Y) = X∧Y` - uproszczenie koniunkcji, gdy jeden z czynników zawiera negację drugiego
- **Pokrywanie (POS)**: W formie iloczynu sum (CNF), jeśli jedna suma jest podzbiorem drugiej, można usunąć większą sumę. Na przykład: `(A∨B)∧(A∨B∨C) = (A∨B)` - druga suma pokrywa pierwszą, więc jest zbędna
- **Redundancja POS (tautologia)**: W formie iloczynu sum, jeśli któryś z czynników jest tautologią (zawsze prawdziwy, np. `(A∨¬A)`), można go usunąć, bo `X∧1 = X`
- **Rozdzielność (AND→OR)**: `X∧(Y∨Z) = (X∧Y)∨(X∧Z)` - ale tylko wtedy, gdy to poprawia miarę wyrażenia (nie zawsze jest stosowane)
- **Rozdzielność (OR→AND)**: `X∨(Y∧Z) = (X∨Y)∧(X∨Z)` - ale tylko wtedy, gdy to poprawia miarę wyrażenia (nie zawsze jest stosowane)
- **Faktoryzacja (SOP)**: `(A∧B)∨(A∧C) = A∧(B∨C)` - wyciąganie wspólnego czynnika z sumy iloczynów, ale tylko gdy poprawia miarę
- **Faktoryzacja (POS)**: `(A∨B)∧(A∨C) = A∨(B∧C)` - wyciąganie wspólnej sumy z iloczynu sum, ale tylko gdy poprawia miarę

Wszystkie te prawa są stosowane wtedy, gdy program nie znajdzie lepszych opcji z wyższych priorytetów, ale mogą one być pomocne w specyficznych sytuacjach.

Jeśli kilka praw ma ten sam priorytet, program wybiera to, które daje wyrażenie z mniejszą liczbą literałów (zmiennych). Jeśli i to jest równe, wybiera krótsze wyrażenie.

### Krok 2.3: Sprawdzenie, czy przekształcenie jest korzystne

Przed zastosowaniem wybranego prawa program sprawdza, czy przekształcenie rzeczywiście poprawia wyrażenie. Sprawdza:

1. **Czy nie zwiększa liczby literałów**: Jeśli wyrażenie po przekształceniu ma więcej literałów niż przed, a prawo nie jest z priorytetu 4 (dystrybutywność/rozdzielność), to przekształcenie jest odrzucane.

2. **Czy nie zwiększa zbytnio liczby węzłów**: Jeśli wyrażenie staje się znacznie bardziej złożone strukturalnie, przekształcenie może być odrzucone.

3. **Czy nie powoduje oscylacji**: Program pamięta wszystkie wyrażenia, które już widział. Jeśli po przekształceniu otrzymuje wyrażenie, które już wcześniej widział, oznacza to, że wpadł w pętlę (oscylację). W takim przypadku przerywa pracę.

### Krok 2.4: Zastosowanie prawa

Jeśli przekształcenie jest akceptowalne, program:

1. **Zapisuje stan przed przekształceniem**: Zapisuje całe wyrażenie przed zmianą, aby móc je pokazać użytkownikowi.

2. **Zastosowuje prawo**: Znajduje odpowiednie miejsce w drzewie AST i zamienia fragment wyrażenia zgodnie z prawem logicznym. Na przykład:
   - Jeśli ma `A∧(B∨C)` i stosuje dystrybutywność, zamienia to na `(A∧B)∨(A∧C)`

3. **Normalizuje wynik**: Po przekształceniu normalizuje nowe wyrażenie (spłaszcza zagnieżdżenia, standaryzuje kolejność).

4. **Zapisuje stan po przekształceniu**: Zapisuje całe wyrażenie po zmianie.

5. **Oblicza podwyrażenia**: Dla każdego kroku program oblicza:
   - **Podwyrażenie przed**: fragment wyrażenia, który został zmieniony (np. `A∧(B∨C)`)
   - **Podwyrażenie po**: fragment wyrażenia, który powstał po zmianie (np. `(A∧B)∨(A∧C)`)

6. **Oblicza pozycje podświetleń**: Program oblicza dokładne pozycje w tekście, gdzie znajdują się podwyrażenia przed i po, aby móc je podświetlić w interfejsie użytkownika.

7. **Weryfikuje równoważność**: Program sprawdza, czy wyrażenie przed i po przekształceniu są równoważne logicznie (mają tę samą tabelę prawdy). Jeśli nie, krok jest odrzucany.

8. **Tworzy krok**: Program tworzy obiekt "krok", który zawiera wszystkie informacje potrzebne do wyświetlenia użytkownikowi:
   - Nazwę zastosowanego prawa
   - Całe wyrażenie przed
   - Całe wyrażenie po
   - Podwyrażenie przed
   - Podwyrażenie po
   - Pozycje podświetleń
   - Dowód równoważności

### Krok 2.5: Powtórzenie procesu

Po zastosowaniu jednego prawa program wraca do początku pętli i:
1. Sprawdza, czy wyrażenie jest już w formie DNF
2. Jeśli nie, szuka kolejnych możliwości uproszczenia
3. Wybiera najlepsze prawo
4. Stosuje je
5. I tak dalej...

Pętla kończy się, gdy:
- Nie ma już możliwych przekształceń
- Osiągnięto maksymalną liczbę iteracji (100)
- Wykryto oscylację
- Wyrażenie jest już w formie DNF

### Krok 2.6: Porównanie z wynikiem Quine-McCluskey

Po zakończeniu upraszczania prawami logicznymi program:
1. Uruchamia algorytm Quine-McCluskey, który zawsze znajduje minimalną formę DNF
2. Porównuje wynik upraszczania prawami z wynikiem Quine-McCluskey
3. Jeśli wynik prawami ma znacznie więcej literałów niż wynik Quine-McCluskey (np. o 20% więcej), program **odrzuca wszystkie kroki** z upraszczania prawami i przechodzi do fazy 3

---

## Faza 3: Konwersja do DNF (convert_to_dnf_with_laws)

Jeśli wyrażenie nie jest jeszcze w formie DNF, program musi je najpierw skonwertować do DNF używając praw dystrybutywności.

### Krok 3.1: Wyszukiwanie miejsc do dystrybucji

Program przeszukuje drzewo AST i szuka węzłów typu AND, które zawierają węzeł typu OR jako jeden z argumentów. Na przykład:
- `A∧(B∨C)` - tutaj AND zawiera OR
- `(A∨B)∧(C∨D)` - tutaj oba argumenty AND są OR

### Krok 3.2: Zastosowanie dystrybutywności

Dla każdego znalezionego miejsca program stosuje prawo dystrybutywności:
- `A∧(B∨C)` → `(A∧B)∨(A∧C)`

Proces jest następujący:
1. Program znajduje węzeł AND z argumentem OR
2. Bierze wszystkie argumenty OR (np. `B` i `C`)
3. Dla każdego argumentu OR tworzy nowy węzeł AND, łącząc go z pozostałymi argumentami głównego AND
4. Tworzy nowy węzeł OR, który zawiera wszystkie te nowe węzły AND
5. Zastępuje oryginalny węzeł AND tym nowym węzłem OR

### Krok 3.3: Normalizacja i powtórzenie

Po każdej dystrybucji program:
1. Normalizuje wyrażenie
2. Sprawdza, czy jest już w formie DNF
3. Jeśli nie, wraca do kroku 3.1 i szuka kolejnych miejsc do dystrybucji

Proces powtarza się maksymalnie 50 razy (lub do momentu osiągnięcia DNF).

### Krok 3.4: Tworzenie kroków

Dla każdej zastosowanej dystrybucji program tworzy krok, który pokazuje:
- Przed: całe wyrażenie przed dystrybucją
- Po: całe wyrażenie po dystrybucji
- Podwyrażenie przed: fragment, który został rozłożony (np. `A∧(B∨C)`)
- Podwyrażenie po: fragment, który powstał (np. `(A∧B)∨(A∧C)`)
- Pozycje podświetleń: gdzie w tekście znajdują się te fragmenty

---

## Faza 4: Upraszczanie do minimalnego DNF (używając QM jako planu)

Gdy wyrażenie jest już w formie DNF, ale nie jest jeszcze minimalne, program używa algorytmu Quine-McCluskey jako "planu", aby wiedzieć, które pary termów należy połączyć.

### Krok 4.1: Uruchomienie Quine-McCluskey

Program uruchamia algorytm Quine-McCluskey, który:
1. Tworzy tabelę prawdy dla wyrażenia
2. Znajduje wszystkie mintermy (kombinacje zmiennych, dla których wyrażenie jest prawdziwe)
3. Łączy mintermy w pary, które różnią się tylko jedną zmienną
4. Powtarza proces łączenia, aż nie da się już nic połączyć
5. Wybiera minimalny zestaw implikantów pierwszorzędnych (PI), które pokrywają wszystkie mintermy

Wynikiem jest:
- Lista **merge_edges**: pary termów, które należy połączyć (np. `(A∧B∧C)` i `(A∧B∧¬C)` różnią się tylko zmienną `C`)
- Lista **selected_pi**: wybrane implikanty pierwszorzędne (minimalny zestaw pokrywający wszystkie mintermy)

### Krok 4.2: Sprawdzenie, czy potrzebne są dodatkowe kroki

Program sprawdza:
1. Czy wyrażenie jest już minimalne (porównuje z wynikiem QM)
2. Czy są jakieś merge_edges do przetworzenia
3. Jeśli nie ma merge_edges, ale wyrażenie nie jest minimalne, program próbuje wygenerować syntetyczne merge_edges na podstawie selected_pi

**Ważne:** Generowanie syntetycznych merge_edges **nie wpływa na poprawność** programu i wyniku. Oto dlaczego:

- **Syntetyczne merge_edges pochodzą z selected_pi**: `selected_pi` to lista implikantów pierwszorzędnych (PI) wybranych przez algorytm Quine-McCluskey jako minimalne pokrycie wszystkich mintermów. Są to zawsze poprawne, minimalne termy.

- **Każdy syntetyczny merge_edge reprezentuje rzeczywistą możliwość połączenia**: Program znajduje pary mintermów, które:
  - Są pokrywane przez ten sam PI (z selected_pi)
  - Różnią się tylko jedną pozycją bitową (jedną zmienną)
  - Mogą być połączone, aby utworzyć ten PI

- **Każdy krok jest weryfikowany**: Funkcja `build_merge_steps` weryfikuje każdy krok przez porównanie tabel prawdy - jeśli przekształcenie nie jest równoważne, krok jest odrzucany.

- **Proces kończy się na minimalnej formie**: Program porównuje bieżące wyrażenie z wynikiem QM i przerywa, gdy osiągnie minimalną formę.

- **Fallback zapewnia poprawność**: Jeśli nawet syntetyczne merge_edges nie prowadzą do minimalnej formy, program używa fallbackowego kroku, który bezpośrednio pokazuje przejście do minimalnej formy QM (z weryfikacją przez tabelę prawdy).

W praktyce, syntetyczne merge_edges są po prostu "odtworzeniem" informacji, która już była w QM, ale nie została zapisana w formie merge_edges. Są one równie bezpieczne i poprawne, jak oryginalne merge_edges z QM.

### Krok 4.3: Upraszczanie przez absorpcję (build_absorb_steps)

Zanim program zacznie łączyć termy, najpierw usuwa duplikaty i termy pochłaniane przez inne termy.

**Krok 4.3.1: Idempotencja (usuwanie duplikatów)**

Program przeszukuje wszystkie węzły OR i szuka duplikatów. Jeśli znajdzie dwa identyczne termy (np. `(A∧B)` i `(A∧B)`), usuwa jeden z nich, stosując prawo idempotencji: `X∨X = X`.

**Krok 4.3.2: Absorpcja**

Program przeszukuje wszystkie węzły OR i szuka termów, które są pochłaniane przez inne termy. Na przykład:
- Jeśli jest `(A∧B)` i `(A∧B∧C)`, to `(A∧B∧C)` jest pochłaniane przez `(A∧B)` (bo `(A∧B)` jest podzbiorem `(A∧B∧C)`)
- Program usuwa `(A∧B∧C)`, stosując prawo absorpcji: `X∨(X∧Y) = X`

Proces absorpcji jest powtarzany w pętli, aż nie ma już nic do usunięcia (maksymalnie 50 iteracji).

### Krok 4.4: Łączenie termów (build_merge_steps)

Dla każdej pary termów z listy merge_edges program wykonuje proces łączenia. Proces składa się z dwóch faz:

**FAZA 1: Odsłonięcie pary (ensure_pair_present) - tylko jeśli para nie istnieje**

Czasami para termów, które należy połączyć, nie istnieje jeszcze w wyrażeniu. Na przykład:
- QM mówi, że należy połączyć `(A∧B∧C)` i `(A∧B∧¬C)`
- Ale w wyrażeniu może być tylko `(A∧B)` (bez `C`)

W takim przypadku program musi najpierw "odsłonić" parę poprzez dwa kroki:

1. **Prawo tożsamości**: `(A∧B)` → `(A∧B)∧(C∨¬C)`
   - Dodaje `C∨¬C`, które zawsze jest prawdziwe (tożsamość: `X = X∧1`, gdzie `1 = C∨¬C`)

2. **Dystrybucja**: `(A∧B)∧(C∨¬C)` → `(A∧B∧C)∨(A∧B∧¬C)`
   - Rozkłada iloczyn sumy na sumę iloczynów

Teraz para istnieje i można ją połączyć.

**Uwaga:** Jeśli para termów już istnieje w wyrażeniu (np. `(A∧B∧C)∨(A∧B∧¬C)` jest już obecne), program pomija Fazę 1 i przechodzi od razu do Fazy 2.

**FAZA 2: Łączenie pary - zawsze wykonywana**

Gdy para termów już istnieje (albo została odsłonięta w Fazie 1), program wykonuje trzy kolejne kroki, aby ją połączyć:

**Krok 4.4.2: Faktoryzacja (Rozdzielność)**

Program stosuje faktoryzację - odwrotność dystrybucji:
- `(A∧B∧C)∨(A∧B∧¬C)` → `(A∧B)∧(C∨¬C)`
- Wyciąga wspólny czynnik `(A∧B)` przed nawias, a różnicę `(C∨¬C)` wstawia w nawias

**Krok 4.4.3: Tautologia**

Po faktoryzacji program ma `(A∧B)∧(C∨¬C)`. Teraz stosuje prawo tautologii:
- `(C∨¬C)` → `1` (bo `C∨¬C` jest zawsze prawdziwe)

**Krok 4.4.4: Element neutralny**

Po zastosowaniu tautologii program ma `(A∧B)∧1`. Teraz stosuje prawo elementu neutralnego:
- `(A∧B)∧1` → `(A∧B)` (bo `X∧1 = X`)

**Podsumowanie całego procesu:**

**WAŻNE:** Te kroki są wykonywane w kontekście CAŁEGO wyrażenia DNF, nie w izolacji. Przykład pokazuje tylko fragment, który jest zmieniany.

Przykład, gdy para nie istnieje (wyrażenie: `(A∧B)∨(D∧E)`):
1. Faza 1 (odsłonięcie):
   - Tożsamość: `(A∧B)∨(D∧E)` → `(A∧B)∧(C∨¬C)∨(D∧E)` → po normalizacji: `(A∧B∧C)∨(A∧B∧¬C)∨(D∧E)`
   - Dystrybucja: wyrażenie już jest w formie DNF z parą
2. Faza 2 (łączenie):
   - Faktoryzacja: `(A∧B∧C)∨(A∧B∧¬C)∨(D∧E)` → `(A∧B)∧(C∨¬C)∨(D∧E)`
   - Tautologia: `(A∧B)∧(C∨¬C)∨(D∧E)` → `(A∧B)∧1∨(D∧E)`
   - Element neutralny: `(A∧B)∧1∨(D∧E)` → `(A∧B)∨(D∧E)`

**Wynik:** Wyrażenie końcowe `(A∧B)∨(D∧E)` jest prostsze niż początkowe, bo:
- Zamiast potencjalnie mieć `(A∧B∧C)∨(A∧B∧¬C)∨(D∧E)` (3 termy, 6 literałów)
- Mamy `(A∧B)∨(D∧E)` (2 termy, 4 literały)

Przykład, gdy para już istnieje (wyrażenie: `(A∧B∧C)∨(A∧B∧¬C)∨(D∧E)`):
1. Faza 1: pomijana (para już jest w wyrażeniu)
2. Faza 2 (łączenie):
   - Faktoryzacja: `(A∧B∧C)∨(A∧B∧¬C)∨(D∧E)` → `(A∧B)∧(C∨¬C)∨(D∧E)`
   - Tautologia: `(A∧B)∧(C∨¬C)∨(D∧E)` → `(A∧B)∧1∨(D∧E)`
   - Element neutralny: `(A∧B)∧1∨(D∧E)` → `(A∧B)∨(D∧E)`

**Wynik:** Wyrażenie końcowe `(A∧B)∨(D∧E)` jest prostsze niż początkowe (2 termy zamiast 3).

**Dlaczego nie ma zakręcenia się w kółko?**

1. **Kroki są wykonywane w kontekście całego wyrażenia**: Nawet jeśli fragment `(A∧B)` wraca do `(A∧B)`, inne części wyrażenia mogą się zmieniać (np. inne termy mogą być absorbowane lub upraszczane).

2. **Proces kończy się na minimalnej formie QM**: Program porównuje bieżące wyrażenie z wynikiem QM. Jeśli osiągnie minimalną formę (np. `(A∧B)∨(D∧E)` jest minimalne zgodnie z QM), proces się kończy.

3. **Faza 1 jest wykonywana tylko gdy para nie istnieje**: Jeśli w wyrażeniu już jest `(A∧B∧C)∨(A∧B∧¬C)`, Faza 1 jest pomijana (funkcja `ensure_pair_present` zwraca puste kroki).

4. **Cel procesu**: Celem nie jest zmiana pojedynczego termu, ale uproszczenie całego wyrażenia DNF do minimalnej formy. Nawet jeśli niektóre termy "wracają" do wcześniejszej formy, wyrażenie jako całość staje się prostsze (mniej termów, mniej literałów).

**Przykład pokazujący realny przypadek:**

Wyrażenie początkowe: `(A∧B∧C)∨(A∧B∧¬C)∨(A∧B∧D)∨(A∧B∧¬D)∨(E∧F)`

Po łączeniu pierwszej pary `(A∧B∧C)∨(A∧B∧¬C)` → `(A∧B)`: 
- `(A∧B)∨(A∧B∧D)∨(A∧B∧¬D)∨(E∧F)`

Po łączeniu drugiej pary `(A∧B∧D)∨(A∧B∧¬D)` → `(A∧B)`:
- `(A∧B)∨(A∧B)∨(E∧F)` → po idempotencji: `(A∧B)∨(E∧F)`

**Wynik:** `(A∧B)∨(E∧F)` - wyrażenie jest znacznie prostsze niż początkowe (2 termy zamiast 5).

### Krok 4.5: Powtórzenie absorpcji

Po połączeniu wszystkich par program ponownie stosuje absorpcję, aby usunąć wszystkie termy, które stały się zbędne.

### Krok 4.6: Tworzenie kroków

Dla każdego zastosowanego prawa program tworzy krok, który pokazuje:
- Przed: całe wyrażenie przed przekształceniem
- Po: całe wyrażenie po przekształceniu
- Podwyrażenie przed: fragment, który został zmieniony
- Podwyrażenie po: fragment, który powstał
- Pozycje podświetleń: gdzie w tekście znajdują się te fragmenty

---

## Faza 5: Finalizacja i weryfikacja

### Krok 5.1: Weryfikacja wszystkich kroków

Program weryfikuje każdy krok, sprawdzając, czy wyrażenie przed i po przekształceniu są równoważne logicznie. Robi to poprzez:
1. Generowanie tabeli prawdy dla wyrażenia przed
2. Generowanie tabeli prawdy dla wyrażenia po
3. Porównanie tabel prawdy
4. Jeśli tabele są identyczne, krok jest akceptowany
5. Jeśli nie, krok jest odrzucany

### Krok 5.2: Porządkowanie kroków

Program porządkuje wszystkie kroki w logicznej kolejności:
1. Najpierw kroki z upraszczania prawami logicznymi (jeśli były użyte)
2. Potem kroki z konwersji do DNF (jeśli były potrzebne)
3. Na końcu kroki z upraszczania do minimalnego DNF (łączenie termów)

### Krok 5.3: Przygotowanie wyników

Program przygotowuje finalne wyniki:
- Listę wszystkich kroków z pełnymi informacjami
- Końcowe wyrażenie w minimalnej formie DNF
- Informację, czy wyrażenie było już minimalne na początku

---

## Szczegóły techniczne

### Jak program znajduje miejsca do zastosowania praw?

Program przeszukuje drzewo AST **rekurencyjnie** - zaczyna od korzenia i schodzi w dół do każdego węzła. Dla każdego węzła sprawdza:
- Jaki to typ węzła (AND, OR, NOT, VAR, CONST)?
- Jakie ma argumenty?
- Czy można zastosować jakieś prawo logiczne?

Na przykład:
- Jeśli węzeł to AND z argumentami `[A, ¬A]`, program znajduje kontradykcję
- Jeśli węzeł to OR z argumentami `[A, A]`, program znajduje idempotencję
- Jeśli węzeł to AND z argumentami `[A, OR(B, C)]`, program znajduje możliwość dystrybucji

### Jak program oblicza pozycje podświetleń?

Program używa specjalnej funkcji `pretty_with_tokens`, która:
1. Generuje tekstową reprezentację wyrażenia (np. `(A∧B)∨C`)
2. Jednocześnie zapisuje, gdzie w tym tekście znajduje się każdy węzeł drzewa AST
3. Dla każdego węzła zapisuje pozycję początku i końca w tekście

Gdy program chce podświetlić fragment wyrażenia:
1. Znajduje odpowiedni węzeł w drzewie AST
2. Sprawdza jego pozycję w tekście (zapisaną przez `pretty_with_tokens`)
3. Używa tej pozycji do podświetlenia fragmentu w interfejsie użytkownika

### Jak program unika oscylacji?

Program pamięta wszystkie wyrażenia, które już widział (w formie kanonicznej - standaryzowanej). Przed zastosowaniem każdego prawa sprawdza:
1. Czy wyrażenie po przekształceniu jest już w liście widzianych wyrażeń?
2. Jeśli tak, oznacza to oscylację (pętlę) - program przerywa pracę
3. Jeśli nie, dodaje nowe wyrażenie do listy i kontynuuje

### Jak program wybiera najlepsze prawo?

Program używa systemu priorytetów i miar:

1. **Priorytet prawa**: Każde prawo ma przypisany priorytet (1-8). Prawa z niższym numerem są preferowane.

2. **Miara wyrażenia**: Program oblicza "miarę" wyrażenia, która składa się z trzech liczb:
   - Liczba literałów (zmiennych)
   - Liczba węzłów w drzewie
   - Długość tekstowa wyrażenia

3. **Porównywanie**: Program porównuje miary wyrażeń po zastosowaniu różnych praw i wybiera to, które daje najmniejszą miarę (lub najwyższy priorytet).

### Jak program weryfikuje równoważność?

Program używa **tabeli prawdy** do weryfikacji równoważności:
1. Generuje tabelę prawdy dla wyrażenia przed przekształceniem
2. Generuje tabelę prawdy dla wyrażenia po przekształceniu
3. Porównuje wyniki w każdej linii tabeli
4. Jeśli wszystkie wyniki są identyczne, wyrażenia są równoważne

Aby przyspieszyć proces, program używa **hashu tabeli prawdy** - zamiast porównywać całe tabele, porównuje tylko ich skróty (hash), które są znacznie szybsze do obliczenia.

---

## Przykład pełnego procesu

Załóżmy, że mamy wyrażenie: `(A∧(B∨C))∨D`

### Faza 1: Przygotowanie
- Wyrażenie jest poprawne składniowo
- Parsowanie do AST: `OR(AND(A, OR(B, C)), D)`
- Normalizacja: wyrażenie jest już znormalizowane
- Sprawdzenie: wyrażenie nie jest w formie DNF

### Faza 2: Upraszczanie prawami
- Program znajduje możliwość dystrybucji: `A∧(B∨C)`
- Stosuje dystrybucję: `(A∧(B∨C))∨D` → `((A∧B)∨(A∧C))∨D`
- Normalizuje: `(A∧B)∨(A∧C)∨D`
- Sprawdza: wyrażenie jest teraz w formie DNF
- Kończy fazę 2

### Faza 3: Konwersja do DNF
- Nie jest potrzebna, bo wyrażenie jest już w DNF

### Faza 4: Upraszczanie do minimalnego DNF
- Program uruchamia QM i otrzymuje plan: połączyć `(A∧B)` i `(A∧C)` w `A∧(B∨C)`
- Ale to by pogorszyło wyrażenie, więc QM mówi, że wyrażenie jest już minimalne
- Program kończy pracę

### Wynik
- Wyrażenie końcowe: `(A∧B)∨(A∧C)∨D`
- Liczba kroków: 1 (dystrybucja)

---

## Podsumowanie

Proces upraszczania w programie LogicEngine składa się z pięciu głównych faz:

1. **Przygotowanie**: Walidacja, parsowanie, normalizacja, sprawdzenie czy już minimalne
2. **Upraszczanie prawami**: Iteracyjne stosowanie praw logicznych według priorytetów
3. **Konwersja do DNF**: Stosowanie dystrybutywności, jeśli wyrażenie nie jest w DNF
4. **Upraszczanie do minimalnego DNF**: Używanie QM jako planu do łączenia termów
5. **Finalizacja**: Weryfikacja, porządkowanie, przygotowanie wyników

Każdy krok jest weryfikowany pod kątem równoważności logicznej, a program unika oscylacji poprzez śledzenie wszystkich widzianych wyrażeń. Wybór praw jest optymalizowany poprzez system priorytetów i miar złożoności wyrażeń.

