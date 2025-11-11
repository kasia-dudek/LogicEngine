# Jak LogicEngine upraszcza wyrażenia prawami logicznymi

Ten dokument w prosty sposób opisuje, co dzieje się wewnątrz zakładki **„Prawa logiczne”**. Wszystkie informacje zostały sprawdzone w aktualnym kodzie (`logicengine/src/logicengine`) – możesz traktować je jako dokładne odzwierciedlenie działania aplikacji. Pojawiające się niżej wzory i przykłady pomagają zrozumieć logikę formalną, ale nie wymagają umiejętności programowania.

---

## 1. Co program robi na wejściu

1. **Walidacja zapisu**  
   Silnik akceptuje zmienne zapisane pojedynczymi wielkimi literami (`A`, `B`, ...). Dozwolone są również stałe `0` (fałsz) i `1` (prawda), nawiasy oraz spacje. Jeśli brakuje nawiasu, pojawiły się dwa operatory pod rząd albo wprowadzono nieznany symbol, zobaczysz komunikat o błędzie zanim pojawi się jakikolwiek krok.  
   *Przykład*: wpis `A &&` zostanie odrzucony z informacją „Wyrażenie nie może kończyć się operatorem”.

2. **Standaryzacja operatorów**  
   Wszystkie popularne skróty są zamieniane na zapis kanoniczny (dokładnie tak, jak w `validation.OPERATOR_MAP`). Dzięki temu dalej pracujemy na wspólnym alfabecie symboli. Najważniejsze odwzorowania:  
   \[
   \begin{aligned}
   &(&,&&,\text{AND},\ ∧\ ) &&\mapsto &&∧,\\
   &(|,||,\text{OR},\ ∨,+) &&\mapsto &&∨,\\
   &(!,~,\text{NOT},\ ¬) &&\mapsto &&¬,\\
   &(->,=>,\rightarrow) &&\mapsto &&→,\\
   &(<=,<-,\leftarrow) &&\mapsto &&←,\\
   &(\leftrightarrow,\equiv,\text{<->}) &&\mapsto &&↔,\\
   &(\wedge) &&\mapsto &&∧,\\
   &(\text{XOR},^,⊕) &&\mapsto &&⊕.
   \end{aligned}
   \]
   Analogicznie traktujemy symbole `↑` (NAND) i `↓` (NOR), które zostają zachowane w zapisie.

3. **Budowa drzewa (AST)**  
   Wyrażenie tekstowe zamieniamy na drzewo składniowe. Każdy węzeł odpowiada jednej operacji logicznej, a liście reprezentują zmienne lub stałe. Dla przykładu zapis `(A ∧ B) ∨ ¬C` staje się drzewem, w którym korzeń to alternatywa `∨`, lewy syn to koniunkcja `∧` (z dziećmi `A`, `B`), a prawy syn to negacja `¬` (dziecko `C`). Taka postać ułatwia późniejsze wyszukiwanie wzorców i stosowanie praw.

4. **Normalizacja operatorów pochodnych**  
   Jeszcze przed zastosowaniem „praw” każde użycie `→`, `←`, `↔`, `≡`, `⊕`, `↑`, `↓` jest rozpisywane przy użyciu wyłącznie `¬`, `∧` i `∨`. Ten etap widać jako **pierwszy krok** na liście – nazwany „Normalizacja operatorów pochodnych” (implementacja: początek `simplify_with_laws`).  
   - Implikacja \(p → q\) staje się \(¬p ∨ q\).  
   - Implikacja odwrotna \(p ← q\) to \(¬q ∨ p\).  
   - Równoważność \(p ↔ q\) przechodzi w \((p ∧ q) ∨ (¬p ∧ ¬q)\).  
   - XOR \(p ⊕ q\) zamienia się w \((p ∨ q) ∧ ¬(p ∧ q)\).  
   - NAND i NOR zostają rozpisane na negację odpowiednio koniunkcji i alternatywy.  
   Dzięki temu dalsze kroki posługują się jedynie trzema podstawowymi operatorami Boole’a.

---

## 2. Jak silnik wybiera następne prawo

Kolejne iteracje funkcji `simplify_with_laws` można traktować jako cykl „znajdź → oceń → zastosuj”:

1. **Zebranie kandydatów** – dla każdego fragmentu drzewa sprawdzamy, czy pasuje do któregoś z wzorców praw (funkcje `laws_matches` i `axioms_matches`). Przykładowo, jeśli w drzewie znajduje się `(X ∧ ¬X)`, do listy trafia prawo „Kontradykcja”.
2. **Priorytety** – `pick_best` przypisuje każdemu kandydatowi rangę:
   1. Kontradykcje, dopełnienia i elementy neutralne (np. `X ∧ ¬X`, `X ∨ ¬X`, `X ∧ 1`)  
      *Efekt*: usuwamy fragment, który zawsze jest fałszywy lub zawsze prawdziwy.
   2. Podwójna negacja (`¬¬X = X`)
   3. Absorpcja (`X ∨ (X ∧ Y) = X`)
   4. Dystrybutywność / rozdzielność (pozwala przejść do formy DNF)
   5. Reguły de Morgana (`¬(X ∧ Y) = ¬X ∨ ¬Y`)
   6. Faktoryzacja (wyciąganie wspólnych czynników)
   7. Konsensus (rzadko stosowane, dodatkowo zweryfikowane tabelą prawdy)
   8. Pozostałe prawa (np. negacja stałej `¬0 = 1`)
3. **Kontrola jakości przed zapisaniem kroku** – jeśli prawo ma zostać wykorzystane, ale zanim dopiszemy je do listy, wykonujemy trzy testy:
   - porównujemy miarę wyrażenia przed i po (liczbę literałów, liczbę węzłów, długość tekstu). Jeśli wynik byłby gorszy, odkładamy parę `(before_canon, after_canon, prawo)` do `skipped_transformations`;
   - sprawdzamy, czy takiej samej zamiany nie odrzuciliśmy już wcześniej – jeżeli tak, pomijamy krok od razu;
   - upewniamy się, że wynik nie pojawił się wcześniej w `seen_expressions`. Gdyby tak było, doszłoby do powtórzenia (oscylacji), więc cofamy zmianę.

### Ilustrujące przykłady

- **Kontradykcja**:  
  Jeżeli w wyrażeniu wystąpi `(A ∧ ¬A) ∨ B`, krok ma postać:  
  `before_tree = (A∧¬A)∨B`, `after_tree = 0∨B` → następnie prawo elementu neutralnego (`0∨B = B`).

- **Reguła de Morgana**:  
  Fragment `¬(A ∧ B)` zostanie zamieniony na `¬A ∨ ¬B`. To przydatne np. przed dystrybucją albo prostym policzeniem zmiennych.

- **Dystrybutywność**:  
  `A ∧ (B ∨ C)` → `(A ∧ B) ∨ (A ∧ C)`. To rozszerza wyrażenie, ale bywa konieczne, by w kolejnym kroku móc zastosować absorpcję.

- **Faktoryzacja**:  
  `(A ∧ X) ∨ (A ∧ Y)` → `A ∧ (X ∨ Y)` (ale tylko jeśli liczba literałów spada).

---

## 3. Co trafia do pojedynczego kroku

Jeżeli kandydat przejdzie wszystkie powyższe filtry, powstaje wpis na liście kroków. Każdy taki wpis zawiera:

- **nazwę prawa** oraz krótką notatkę (`law`, `note`),
- **pełny zapis wyrażenia** przed i po (`before_tree`, `after_tree`),
- **fragment podlegający zmianie** (`before_subexpr`, `after_subexpr`),
- **zakresy do podświetlenia** w tekście (wyliczane przez `pretty_with_tokens`),
- **potwierdzenie równoważności** – porównujemy skróty tabel prawdy (`truth_table_hash`). Jeśli choćby jeden wiersz tabeli różni się między stanem „przed” i „po”, krok jest odrzucany.

*Przykład:*  
Rozważmy krok „Absorpcja” dla wyrażenia `(A ∧ B) ∨ (A ∧ B ∧ C)`.  
- Tabela prawdy dla `before_tree` i `after_tree` (czyli dla `(A ∧ B)`)
  jest identyczna: dla każdej kombinacji `(A,B,C)` wynik jest taki sam.  
- Ponieważ skróty (hashe) tabel są równe, krok zostaje zapisany.

Dodatkowo kanoniczny zapis nowego wyrażenia (`after_canon`) trafia do `seen_expressions`, co zapobiega powrotowi do wcześniej odwiedzonych postaci.

---

## 4. Kiedy lista kroków się kończy

`simplify_with_laws` zatrzymuje się, gdy wystąpi jeden z warunków:

- skończyły się dopasowania (brak nowych praw do zastosowania),
- wykonaliśmy 100 iteracji (`max_steps=100` przekazane z `engine.py`),
- pojawiła się powtórka w `seen_expressions` – wtedy ostatni wpis to krok „Zatrzymano (oscylacja)”.

Po wyjściu z funkcji wynik porównujemy z planem Quine’a–McCluskeya:

- jeśli liczba literałów w wyniku z praw mieści się w granicy 120 % wyniku QM, zachowujemy wszystkie kroki z praw logicznych;
- jeżeli literałów jest więcej niż 120 % wyniku QM, odkładamy cały log z praw (tak jak robi to `skip_all_laws_steps`) i przełączamy się na ścieżkę QM.

### Przykład porównania z QM

Załóżmy, że upraszczanie prawami dało wzór `X`, a algorytm QM – wzór `Y`. 
Jeśli liczba literałów w `X` wynosi 15, a w `Y` – 10, różnica procentowa to 150 %. 
Ponieważ przekracza próg 120 %, w interfejsie zobaczysz wyłącznie kroki QM i wynik `Y`. 
Gdyby `X` miał 11 literałów, uznalibyśmy go za „wystarczająco dobry” i pozostawili kroki z praw.

---

## 5. Co dzieje się dalej

Aktualny przepływ – implementowany w `_simplify_with_dnf_pipeline` – wygląda następująco:

1. **Pas trywialny (fixpoint)** – uruchamiamy `run_fixpoint` z zestawem podstawowych praw (`TRIVIAL_LAW_NAMES`) i powtarzamy go, dopóki wyrażenie przestaje się zmieniać. W tym miejscu pojawiają się m.in. kontradykcja, element neutralny/pchłaniający, absorpcja czy podwójna negacja.
2. **Przepchnięcie negacji do literałów** – `push_negations_to_literals` stosuje jedynie reguły de Morgana i podwójnej negacji, aż każda `¬` stoi bezpośrednio przed zmienną.
3. **Pas komplementów** – `apply_complement_laws` usuwa fragmenty typu `X ∨ ¬X` oraz `X ∧ ¬X`. Zaraz potem ponownie uruchamiamy pas trywialny, aby posprzątać pojawiające się `0` i `1`. Jeżeli uzyskamy czystą stałą (`0` lub `1`), pipeline kończy się już w tym miejscu.
4. **Dystrybucja do DNF** – `distribute_to_dnf` rozprowadza wyłącznie wzorzec `A ∧ (B ∨ C)` → `(A ∧ B) ∨ (A ∧ C)`. Po dystrybucji jeszcze raz wykonujemy pas komplementów oraz pas trywialny, aby natychmiast uprościć rezultat.
5. **Minimalizacja przy użyciu QM (gdy zostały zmienne)** – jeśli końcowe wyrażenie zawiera literały, przekazujemy je do `_legacy_simplify_to_minimal_dnf`. Tam działa dobrze znany most do algorytmu Quine’a–McCluskeya: odsłonięcie par (`ensure_pair_present`), 3‑krokowe scalanie (`build_merge_steps`: faktoryzacja → tautologia → element neutralny) oraz końcowa absorpcja (`build_absorb_steps` i `build_contradiction_steps`). Gdy wynik wcześniejszych etapów to sama stała, tę część pomijamy.

W odróżnieniu od poprzedniej wersji nie pokazujemy już kroków „Dowód równoważności (TT)” ani „Certyfikat minimalności (QM)” – oba sprawdzenia (porównanie haszy tabel prawdy oraz liczby literałów z minimalnym DNF) są wykonywane w tle, lecz nie dodajemy kroków, które wizualnie niczego nie zmieniają. Dzięki temu lista kroków odpowiada wyłącznie realnym transformacjom, a końcowa forma DNF jest zgodna z planem QM.