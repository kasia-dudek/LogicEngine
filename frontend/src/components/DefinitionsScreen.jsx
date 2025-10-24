import React, { useState } from 'react';
import ASTDisplay from './ASTDisplay';

const CONCEPTS = [
  {
    key: 'and',
    name: 'Koniunkcja (AND)',
    description: 'Koniunkcja jest prawdziwa tylko wtedy, gdy oba argumenty są prawdziwe.',
    tip: 'Najprostszy operator logiczny – odpowiada "i" w języku naturalnym.',
    icon: '∧',
    learn: 'Koniunkcja (AND) to operacja logiczna, która daje wynik 1 tylko wtedy, gdy oba argumenty są równe 1.',
    examples: [
      'A ∧ B',
      'A ∧ (B ∨ C)',
      '(A ∧ B) ∧ C',
      'A ∧ ¬B',
    ]
  },
  {
    key: 'or',
    name: 'Alternatywa (OR)',
    description: 'Alternatywa jest prawdziwa, gdy przynajmniej jeden argument jest prawdziwy.',
    tip: 'Odpowiada "lub" w języku naturalnym.',
    icon: '∨',
    learn: 'Alternatywa (OR) to operacja logiczna, która daje wynik 1, gdy przynajmniej jeden argument jest równy 1.',
    examples: [
      'A ∨ B',
      'A ∨ (B ∧ C)',
      '(A ∨ B) ∨ C',
      'A ∨ ¬B',
    ]
  },
  {
    key: 'not',
    name: 'Negacja (NOT)',
    description: 'Negacja zamienia wartość logiczną na przeciwną.',
    tip: 'Odpowiada "nie" w języku naturalnym.',
    icon: '¬',
    learn: 'Negacja (NOT) to operacja logiczna, która zamienia 1 na 0 i 0 na 1.',
    examples: [
      '¬A',
      '¬(A ∧ B)',
      '¬(A ∨ B)',
    ]
  },
  {
    key: 'xor',
    name: 'Alternatywa wykluczająca (XOR)',
    description: 'Prawda, gdy dokładnie jeden argument jest prawdziwy.',
    tip: 'Często używana w arytmetyce binarnej.',
    icon: '⊕',
    learn: 'XOR (alternatywa wykluczająca) daje wynik 1, gdy dokładnie jeden z argumentów jest równy 1.',
    examples: [
      'A ⊕ B',
      'A ⊕ (B ∧ C)',
      '(A ∨ B) ⊕ (C ∧ D)',
    ]
  },
  {
    key: 'imp',
    name: 'Implikacja (A → B)',
    description: 'Fałsz tylko wtedy, gdy A=1 i B=0.',
    tip: 'Odpowiada "jeśli... to..." w języku naturalnym.',
    icon: '→',
    learn: 'Implikacja (A → B) jest fałszywa tylko wtedy, gdy A=1 i B=0, w pozostałych przypadkach prawdziwa.',
    examples: [
      'A → B',
      '(A ∧ B) → C',
      'A → (B ∨ C)',
    ]
  },
  {
    key: 'eq',
    name: 'Równoważność (A ↔ B)',
    description: 'Prawda, gdy oba argumenty mają tę samą wartość.',
    tip: 'Odpowiada "wtedy i tylko wtedy, gdy".',
    icon: '↔',
    learn: 'Równoważność (A ↔ B) jest prawdziwa, gdy oba argumenty są równe.',
    examples: [
      'A ↔ B',
      '(A ∧ B) ↔ (C ∨ D)',
      'A ↔ (B ∧ C)',
    ]
  },
  {
    key: 'tautology',
    name: 'Tautologia',
    description: 'Wyrażenie logiczne, które jest zawsze prawdziwe.',
    tip: 'Tautologie są podstawą dowodzenia w logice.',
    icon: '∞',
    learn: 'Tautologia to wyrażenie, które przyjmuje wartość 1 dla każdej możliwej kombinacji zmiennych.',
    examples: [
      'A ∨ ¬A',
      '(A → B) ∨ (B → A)',
      '(A ∧ B) → (A ∨ B)',
    ]
  },
  {
    key: 'kmap',
    name: 'Mapa Karnaugha',
    description: 'Graficzna metoda upraszczania wyrażeń logicznych.',
    tip: 'Idealna do minimalizacji wyrażeń do 4 zmiennych.',
    icon: '🗺',
    learn: 'Mapa Karnaugha pozwala graficznie znaleźć uproszczenie wyrażenia logicznego przez grupowanie jedynek.',
    examples: [
      '(A ∧ B) ∨ (A ∧ ¬B)',
      'A ∨ (B ∧ C)',
      '(A ∧ B) ∨ (C ∧ D)',
    ]
  },
  {
    key: 'truth_table',
    name: 'Tabela prawdy',
    description: 'Pokazuje wszystkie możliwe kombinacje wartości zmiennych i wynik wyrażenia logicznego.',
    example: '(A ∧ B) ∨ ¬C',
    tip: 'Tabela prawdy pozwala sprawdzić, czy wyrażenie jest tautologią lub sprzeczne.',
    icon: 'T',
    examples: [
      'A ∧ B',
      'A ∨ B',
      'A → B',
      'A ↔ B',
      '(A ∧ B) ∨ ¬C',
      '¬(A ∨ B)'
    ],
    moreExamples: [
      'A ∧ B',
      'A ∨ B',
      'A → B',
      'A ↔ B',
      'A ⊕ B',
      'A ↑ B',
      'A ↓ B',
      'A ≡ B',
      '(A ∧ B) ∨ ¬C',
      '¬(A ∨ B)',
    ]
  },
  {
    key: 'minterm',
    name: 'Minterm',
    description: 'Minterm to wiersz tabeli prawdy, dla którego wyrażenie przyjmuje wartość 1.',
    example: '(A ∧ B) ∨ ¬C',
    tip: 'Każde wyrażenie logiczne można zapisać jako sumę mintermów.',
    icon: '1',
  },
  {
    key: 'prime_implicant',
    name: 'Implikant pierwszorzędowy',
    description: 'Najprostsza forma wyrażenia logicznego, która pokrywa minterm(y).',
    example: '(A ∧ B) ∨ ¬C',
    tip: 'Prime implicants są kluczowe w minimalizacji wyrażeń.',
    icon: '🔑',
  },
  {
    key: 'ast',
    name: 'AST (Abstrakcyjne Drzewo Składniowe)',
    description: 'Struktura drzewiasta reprezentująca składnię wyrażenia logicznego.',
    example: '(A ∧ B) ∨ ¬C',
    tip: 'AST pozwala zobaczyć strukturę wyrażenia i kolejność operacji.',
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24"><circle cx="12" cy="4" r="2" fill="#fca5a5"/><circle cx="7" cy="12" r="2" fill="#a5b4fc"/><circle cx="17" cy="12" r="2" fill="#bbf7d0"/><circle cx="12" cy="20" r="2" fill="#fef08a"/><line x1="12" y1="6" x2="7" y2="10" stroke="#888" strokeWidth="2"/><line x1="12" y1="6" x2="17" y2="10" stroke="#888" strokeWidth="2"/><line x1="7" y1="14" x2="12" y2="18" stroke="#888" strokeWidth="2"/><line x1="17" y1="14" x2="12" y2="18" stroke="#888" strokeWidth="2"/></svg>
    ),
  },
  {
    key: 'onp',
    name: 'ONP (Odwrotna Notacja Polska)',
    description: 'Sposób zapisu wyrażeń logicznych bez nawiasów, gdzie operator występuje po argumentach.',
    example: '(A ∧ B) ∨ ¬C',
    tip: 'ONP ułatwia obliczenia komputerowe i parsowanie.',
    icon: '🔄',
  },
  {
    key: 'qm',
    name: 'Metoda Quine-McCluskey',
    description: 'Algorytmiczna metoda minimalizacji wyrażeń logicznych.',
    example: '(A ∧ B) ∨ ¬C',
    tip: 'QM jest szczególnie przydatna dla większej liczby zmiennych.',
    icon: 'Q',
  },
  {
    key: 'logic_operator',
    name: 'Operator logiczny',
    description: 'Symbol oznaczający operację logiczną (¬, ∧, ∨, →, ↔).',
    example: 'A ∧ B',
    tip: 'Poznaj znaczenie każdego operatora, by poprawnie budować wyrażenia.',
    icon: '➕',
  },
  {
    key: 'logic_variable',
    name: 'Zmienna logiczna',
    description: 'Przyjmuje wartość 0 (fałsz) lub 1 (prawda) w wyrażeniu logicznym.',
    example: 'A, B, C',
    tip: 'Zmiennych możesz używać dowolnie, ale każda powinna mieć unikalną nazwę.',
    icon: '🔤',
  },
];

function DefinitionsScreen({ onBack }) {
  const [modal, setModal] = useState(null);
  const [modalData, setModalData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState('');
  const [modalConcept, setModalConcept] = useState(null);

  const handleShowLearn = (concept) => {
    setModalConcept(concept);
    setModal('learn');
  };

  const handleAnalyzeExample = async (example) => {
    setLoading(true);
    setModal('analyze');
    setAnalyzing(example);
    
    try {
      const apiUrl = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000';
      
      // Fetch data from real API
      const [astRes, onpRes, truthRes, kmapRes, qmRes, tautRes] = await Promise.all([
        fetch(`${apiUrl}/ast`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ expr: example }),
        }).then(r => r.json()),
        fetch(`${apiUrl}/onp`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ expr: example }),
        }).then(r => r.json()),
        fetch(`${apiUrl}/truth_table`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ expr: example }),
        }).then(r => r.json()),
        fetch(`${apiUrl}/kmap`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ expr: example }),
        }).then(r => r.json()),
        fetch(`${apiUrl}/qm`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ expr: example }),
        }).then(r => r.json()),
        fetch(`${apiUrl}/tautology`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ expr: example }),
        }).then(r => r.json()),
      ]);

      const data = {
        expression: example,
        ast: astRes.ast,
        onp: onpRes.onp,
        truth_table: truthRes.truth_table,
        kmap: kmapRes,
        qm: qmRes,
        is_tautology: tautRes.is_tautology,
      };
      
      setModalData(data);
    } catch (error) {
      console.error('Error analyzing example:', error);
      setModalData({ error: error.message });
    }
    
    setLoading(false);
  };

  const closeModal = () => {
    setModal(null);
    setModalData(null);
    setAnalyzing('');
    setModalConcept(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-white flex flex-col items-center p-8">
      <div className="w-full max-w-3xl">
        <button className="mb-8 text-blue-600 hover:underline text-lg font-semibold" onClick={onBack}>&larr; Powrót</button>
        <h1 className="text-4xl font-extrabold mb-10 text-center text-blue-700 tracking-tight drop-shadow">Definicje pojęć logicznych</h1>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {CONCEPTS.map(concept => (
            <div key={concept.key} className="bg-white shadow-2xl p-6 rounded-3xl flex flex-col justify-between border border-blue-100 animate-fade-in">
              <div>
                <div className="flex items-center gap-3 mb-3">
                  <span className="text-3xl">{concept.icon}</span>
                  <span className="text-xl font-bold text-blue-700">{concept.name}</span>
                </div>
                <div className="text-gray-600 mb-3 text-base">{concept.description}</div>
                <div className="text-xs text-blue-700 mb-3 italic">{concept.tip}</div>
              </div>
              <button
                className="mt-auto bg-blue-600 text-white px-4 py-2 rounded-xl hover:bg-blue-700 transition-all font-semibold shadow-md text-base"
                onClick={() => handleShowLearn(concept)}
              >
                Dowiedz się więcej
              </button>
            </div>
          ))}
        </div>
      </div>
      {/* Modal edukacyjny z przykładami */}
      {modal === 'learn' && modalConcept && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-3xl shadow-2xl p-8 max-w-2xl w-full relative overflow-y-auto max-h-[90vh] border border-blue-100 animate-fade-in">
            <button className="absolute top-2 right-2 text-gray-500 hover:text-gray-800 text-2xl" onClick={closeModal}>✕</button>
            <h2 className="text-2xl font-bold mb-6 text-blue-700">{modalConcept.name}</h2>
            <div className="mb-4 text-base text-gray-700">{modalConcept.learn}</div>
            <div className="mb-2 font-semibold text-blue-700">Przykłady:</div>
            <div className="flex flex-wrap gap-2 mb-4">
              {modalConcept.examples && modalConcept.examples.map((ex, i) => (
                <button
                  key={i}
                  className="bg-blue-100 hover:bg-blue-200 text-blue-800 font-mono px-3 py-1 rounded-xl transition-all text-base shadow-sm border border-blue-100"
                  onClick={() => handleAnalyzeExample(ex)}
                >
                  {ex}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
      {/* Modal analizy przykładu */}
      {modal === 'analyze' && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-3xl shadow-2xl p-8 max-w-2xl w-full relative overflow-y-auto max-h-[90vh] border border-blue-100 animate-fade-in">
            <button className="absolute top-2 right-2 text-gray-500 hover:text-gray-800 text-2xl" onClick={closeModal}>✕</button>
            <h2 className="text-2xl font-bold mb-6 text-blue-700">Analiza przykładu: <span className="font-mono text-base text-blue-900">{analyzing}</span></h2>
            {loading ? (
              <div className="text-center text-lg">Ładowanie...</div>
            ) : modalData ? (
              <>
                {modalData.truth_table && modalData.truth_table.length > 0 && (
                  <div className="mb-6">
                    <div className="font-semibold mb-2 text-blue-700">Tabela prawdy</div>
                    <div className="overflow-x-auto">
                      <table className="min-w-full border border-gray-300 rounded-xl">
                        <thead>
                          <tr>
                            {Object.keys(modalData.truth_table[0]).map(col => (
                              <th key={col} className="px-3 py-2 border-b bg-gray-100 text-gray-700 text-base">{col}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {modalData.truth_table.map((row, i) => (
                            <tr key={i}>
                              {Object.values(row).map((val, j) => (
                                <td key={j} className="px-3 py-2 border-b text-center text-base">{val}</td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
                {modalData.ast && (
                  <div className="mb-6">
                    <div className="font-semibold mb-2 text-blue-700">AST (Abstrakcyjne Drzewo Składniowe)</div>
                    <div className="bg-white rounded-xl border border-blue-100 shadow p-2">
                      <ASTDisplay ast={modalData.ast} />
                    </div>
                  </div>
                )}
                {modalData.qm && modalData.qm.result && (
                  <div className="mb-2">
                    <div className="font-semibold text-blue-700">Uproszczenie QM:</div>
                    <div className="font-mono bg-gray-100 px-3 py-2 rounded inline-block text-lg">{modalData.qm.result}</div>
                  </div>
                )}
                {modalData.kmap && modalData.kmap.result && (
                  <div className="mb-2">
                    <div className="font-semibold text-blue-700">Uproszczenie K-map:</div>
                    <div className="font-mono bg-gray-100 px-3 py-2 rounded inline-block text-lg">{modalData.kmap.result}</div>
                  </div>
                )}
                {modalData.onp && (
                  <div className="mb-2">
                    <div className="font-semibold text-blue-700">ONP:</div>
                    <div className="font-mono bg-gray-100 px-3 py-2 rounded inline-block text-lg">{modalData.onp}</div>
                  </div>
                )}
                {modalData.is_tautology !== undefined && (
                  <div className="mb-2">
                    <div className="font-semibold text-blue-700">Tautologia?</div>
                    <div className="font-mono text-lg">{modalData.is_tautology ? <span className="text-green-700 font-bold">TAK</span> : <span className="text-red-700 font-bold">NIE</span>}</div>
                  </div>
                )}
              </>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
}

export default DefinitionsScreen; 