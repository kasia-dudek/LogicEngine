import React, { useState } from 'react';
import { analyze } from '../__mocks__/api';

const CONCEPTS = [
  {
    key: 'truth_table',
    name: 'Tabela prawdy',
    description: 'Pokazuje wszystkie możliwe kombinacje wartości zmiennych i wynik wyrażenia logicznego.',
    example: '(A ∧ B) ∨ ¬C',
    tip: 'Tabela prawdy pozwala sprawdzić, czy wyrażenie jest tautologią lub sprzeczne.',
    icon: '📊',
  },
  {
    key: 'minterm',
    name: 'Minterm',
    description: 'Minterm to wiersz tabeli prawdy, dla którego wyrażenie przyjmuje wartość 1.',
    example: '(A ∧ B) ∨ ¬C',
    tip: 'Każde wyrażenie logiczne można zapisać jako sumę mintermów.',
    icon: '1️⃣',
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
    key: 'kmap',
    name: 'Mapa Karnaugh',
    description: 'Graficzna metoda upraszczania wyrażeń logicznych.',
    example: '(A ∧ B) ∨ ¬C',
    tip: 'Grupuj jedynki w mapie, by uprościć wyrażenie.',
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24"><rect x="2" y="2" width="20" height="20" rx="4" fill="#e0e7ff"/><rect x="4" y="4" width="8" height="8" fill="#a5b4fc"/><rect x="12" y="4" width="8" height="8" fill="#fca5a5"/><rect x="4" y="12" width="8" height="8" fill="#bbf7d0"/><rect x="12" y="12" width="8" height="8" fill="#fef08a"/></svg>
    ),
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
    key: 'tautology',
    name: 'Tautologia',
    description: 'Wyrażenie logiczne, które jest zawsze prawdziwe, niezależnie od wartości zmiennych.',
    example: 'A ∨ ¬A',
    tip: 'Tautologie są podstawą dowodzenia w logice.',
    icon: '♾️',
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
    icon: '🧮',
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

  const handleShowExample = async (concept) => {
    setLoading(true);
    setModal(concept.key);
    const data = await analyze(concept.example);
    setModalData(data);
    setLoading(false);
  };

  const closeModal = () => {
    setModal(null);
    setModalData(null);
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
                onClick={() => handleShowExample(concept)}
              >
                <span role="img" aria-label="example">💡</span> Pokaż przykład
              </button>
            </div>
          ))}
        </div>
      </div>
      {modal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-3xl shadow-2xl p-8 max-w-lg w-full relative overflow-y-auto max-h-[90vh] border border-blue-100 animate-fade-in">
            <button className="absolute top-2 right-2 text-gray-500 hover:text-gray-800 text-2xl" onClick={closeModal}>✕</button>
            <h2 className="text-2xl font-bold mb-6 text-blue-700">Przykład: {CONCEPTS.find(c => c.key === modal)?.name}</h2>
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
                {modalData.qm && modalData.qm.result && (
                  <div className="mb-2">
                    <div className="font-semibold text-blue-700">Uproszczenie QM:</div>
                    <div className="font-mono bg-gray-100 px-3 py-2 rounded inline-block text-lg">{modalData.qm.result}</div>
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