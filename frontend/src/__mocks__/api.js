// Mock API do testowania frontendu
export async function analyze(expression) {
  // Przykład dla (A ∧ B) ∨ (¬A ∧ B)
  if (expression === '(A ∧ B) ∨ (¬A ∧ B)') {
    return {
      expression,
      truth_table: [
        { A: 0, B: 0, result: 0 },
        { A: 0, B: 1, result: 1 },
        { A: 1, B: 0, result: 0 },
        { A: 1, B: 1, result: 1 }
      ],
      qm: {
        result: 'B',
        steps: [
          { step: 'Krok 1: Znajdź mintermy', data: { minterms: [1, 3], opis: '...' } },
          { step: 'Krok 2: Grupowanie mintermów', data: { groups: { 1: ['01'], 2: ['11'] }, opis: '...' } },
          { step: 'Krok 7: Uproszczone wyrażenie', data: { result: 'B', opis: '...' } }
        ]
      },
      kmap: {
        result: 'B',
        kmap: [ [0, 1], [0, 1] ],
        order: [0, 1],
        groups: [
          { cells: [[0, 1], [1, 1]], size: 2, minterms: [1, 3], expr: 'B' }
        ]
      }
    };
  }
  // Domyślna odpowiedź
  return {
    expression,
    truth_table: [],
    qm: { result: '', steps: [] },
    kmap: { result: '', kmap: [], order: [], groups: [] }
  };
} 