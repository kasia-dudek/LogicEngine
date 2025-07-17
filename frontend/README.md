# LogicEngine – Frontend

## Przegląd i refaktoryzacja (2024-06)

### Zakres przeglądu
- Spójność konwencji (nazwy komponentów, Tailwind CSS, struktura JSX)
- Poprawność renderowania i obsługi danych z backendu
- Eliminacja duplikacji i niepotrzebnego kodu
- Optymalizacja wydajności (tabela prawdy, KMap, historia)
- Rozbudowa testów jednostkowych (min. 80% pokrycia)
- Przygotowanie do rozbudowy (wizualizacje, ekran definicji)

### Wprowadzone poprawki
- Ujednolicenie stylów i konwencji w całym kodzie
- Refaktoryzacja komponentów: modularność, czytelność, obsługa braku danych
- Dodanie testów jednostkowych dla StartScreen i ResultScreen
- Optymalizacja renderowania tabeli prawdy i mapy Karnaugha
- Uspójnienie obsługi błędów i komunikatów
- Historia wyrażeń ograniczona do 50 pozycji

### Wymagania
- React 18+
- Tailwind CSS (CDN)
- Testy: @testing-library/react, jest

### Przykładowe dane wejściowe
- (A ∨ ¬A), (A ∧ B) ∨ ¬C, A → (B ↔ C), (A & B) (niepoprawne)

### Testy
- Pokrycie kodu: min. 80% (StartScreen, ResultScreen, ExportResults, KMapDisplay, TutorialMode, ExpressionHistory, Toast, ASTDisplay, QMSteps)
- Testy: `npm test` lub `yarn test`

### Napotkane problemy i rozwiązania
- Brak testów dla głównych ekranów – dodano testy jednostkowe
- Uspójnienie formatów danych z backendu
- Optymalizacja wydajności dla dużych danych

### Stan projektu
- Kod gotowy do rozbudowy o wizualizacje (np. AST w D3.js)
- Spójny, modularny, pokryty testami

## Features
- Responsive React app for logic expression analysis
- Tailwind CSS (via CDN)
- StartScreen: input, operator buttons, analyze button, description, definitions placeholder
- ResultScreen: tabbed views for Truth Table, Quine-McCluskey (QM) steps, and Karnaugh Map (K-Map)
- Components:
  - `QMSteps`: displays QM simplification steps
  - `KMapDisplay`: visualizes Karnaugh map with group highlighting
- Mock API in `src/__mocks__/api.js` (easy to swap for real backend)
- Unit tests for all main components (Jest + React Testing Library)

## Usage
1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```
2. Start development server:
   ```bash
   npm start
   ```
3. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Testing
Run all unit tests:
```bash
npm test
```

## Components
- **QMSteps** (`src/components/QMSteps.jsx`):
  - Renders a list of QM simplification steps (step name + JSON data)
  - Used in ResultScreen under the "Quine-McCluskey" tab
- **KMapDisplay** (`src/components/KMapDisplay.jsx`):
  - Renders a Karnaugh map as a table, highlights groups, shows simplified expression
  - Used in ResultScreen under the "K-Map" tab
- **ResultScreen** (`src/components/ResultScreen.jsx`):
  - Tabbed interface for switching between Truth Table, QM, and K-Map
  - Integrates QMSteps and KMapDisplay

## Mock API
- Located in `src/__mocks__/api.js`
- Returns example data for expression `(A ∧ B) ∨ (¬A ∧ B)`
- Easy to replace with real backend (see `analyze` function)

## Example
- Enter `(A ∧ B) ∨ (¬A ∧ B)` and analyze to see all features in action.

## Future
- Ready for backend integration (replace mock API)
- Placeholders for AST visualization and further logic features

---

**Author:**
- LogicEngine Team 