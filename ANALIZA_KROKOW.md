# Analiza sekwencji kroków upraszczania

## Wyrażenie wejściowe
`((A∨(A∧B))∧(A∨¬A)∧(C∨¬(B∧¬C)∨¬A))∨(A∧B∧C)`

## Problemy zidentyfikowane

### 1. Kontradykcje nie są usuwane natychmiast (Kroki 2-5)

**Problem:** W kroku 2-5 powstają wyrażenia typu `(¬A∧A)` które powinny być usunięte jako kontradykcje, ale nie są.

**Przykład:**
- Krok 2: `(A∧A∧(C∨¬(B∧¬C)∨¬A))∨(¬A∧A∧(C∨¬(B∧¬C)∨¬A))`
  - Term `(¬A∧A∧...)` zawiera kontradykcję `A∧¬A` i powinien być usunięty

**Przyczyna:** `build_contradiction_steps` jest wywoływane na początku i po `convert_to_dnf_with_laws`, ale NIE jest wywoływane po każdym kroku dystrybucji w `simplify_with_laws`.

**Rozwiązanie:** Wywołać `build_contradiction_steps` po każdym kroku generowanym przez `simplify_with_laws`, jeśli wyrażenie jest w DNF.

### 2. Proces kończy się przed osiągnięciem minimalnego DNF (Po kroku 10)

**Problem:** Po kroku 10 wyrażenie jest `(A∧¬B)∨(A∧B∧C)∨(A∧B∧¬(B∧¬C))∨(A∧C)∨(A∧¬(B∧¬C))`, co NIE jest minimalnym DNF.

**Przykład absorpcji możliwej:**
- `(A∧¬B)` może pochłonąć `(A∧¬B∧¬C)` → `(A∧¬B)` (zostać)
- `(A∧C)` może być pochłonięte przez `(A∧B∧C)` → `(A∧B∧C)` (zostać)

**Przyczyna:** 
1. `simplify_with_laws` generuje kroki 1-10
2. Kod sprawdza `laws_completed` - jeśli False, przechodzi do sekcji z `merge_edges`
3. Jeśli `merge_edges` jest puste, próbuje wygenerować kroki absorpcji TYLKO jeśli `current_canon != qm_result_canon`
4. Ale jeśli `simplify_with_laws` już wygenerował kroki, kod może nie sprawdzać czy wyrażenie jest minimalne

**Rozwiązanie:** Po `simplify_with_laws`, sprawdzić czy ostatni krok jest minimalnym DNF. Jeśli nie, wywołać `build_absorb_steps` i kontynuować do osiągnięcia minimalnego DNF.

### 3. Brak kontradykcji w kroku 2-5

**Szczegółowa analiza:**
- Krok 2: `(A∧A∧(C∨¬(B∧¬C)∨¬A))∨(¬A∧A∧(C∨¬(B∧¬C)∨¬A))`
  - Term `(¬A∧A∧...)` zawiera kontradykcję
  - Powinien być zamieniony na `0` i usunięty

**Rozwiązanie:** Wywołać `build_contradiction_steps` po każdym kroku `simplify_with_laws`, jeśli wyrażenie jest w DNF.

### 4. Brak absorpcji po kroku 10

**Szczegółowa analiza wyrażenia końcowego:**
```
(A∧¬B)∨(A∧B∧C)∨(A∧B∧¬(B∧¬C))∨(A∧C)∨(A∧¬(B∧¬C))
```

**Możliwe absorpcje:**
1. `(A∧¬B)` vs `(A∧¬B∧¬C)`: `{A, ¬B}` ⊆ `{A, ¬B, ¬C}` → usunąć `(A∧¬B∧¬C)`
2. `(A∧C)` vs `(A∧B∧C)`: `{A, C}` ⊆ `{A, B, C}` → usunąć `(A∧C)`
3. `(A∧¬(B∧¬C))` vs `(A∧B∧¬(B∧¬C))`: drugie może być nadmiarowe

**Rozwiązanie:** Po `simplify_with_laws`, wywołać `build_absorb_steps` i kontynuować do osiągnięcia minimalnego DNF.

## Plan naprawy

1. **Dodać wywołanie `build_contradiction_steps` po każdym kroku `simplify_with_laws`:**
   - W pętli generującej kroki z `simplify_with_laws`, po każdym kroku sprawdzić czy wyrażenie jest w DNF
   - Jeśli tak, wywołać `build_contradiction_steps` i dodać kroki do listy

2. **Dodać sprawdzenie minimalności po `simplify_with_laws`:**
   - Po wygenerowaniu kroków z `simplify_with_laws`, sprawdzić czy ostatni krok jest minimalnym DNF
   - Jeśli nie, wywołać `build_absorb_steps` i kontynuować do osiągnięcia minimalnego DNF

3. **Upewnić się, że proces nie kończy się przedwcześnie:**
   - Sprawdzić czy wyrażenie końcowe jest minimalnym DNF (porównanie z QM result)
   - Jeśli nie, kontynuować z absorpcją/innymi krokami


