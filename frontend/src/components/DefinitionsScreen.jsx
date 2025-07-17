import React, { useState } from 'react';
import { analyze } from '../__mocks__/api';

const CONCEPTS = [
  {
    key: 'truth_table',
    name: 'Tabela prawdy',
    description: 'Pokazuje wszystkie możliwe kombinacje wartości zmiennych i wynik wyrażenia logicznego.',
    example: '(A ∧ B) ∨ ¬C',
  },
  {
    key: 'minterm',
    name: 'Minterm',
    description: 'Minterm to wiersz tabeli prawdy, dla którego wyrażenie przyjmuje wartość 1.',
    example: '(A ∧ B) ∨ ¬C',
  },
  {
    key: 'prime_implicant',
    name: 'Implikant pierwszorzędowy',
    description: 'Najprostsza forma wyrażenia logicznego, która pokrywa minterm(y).',
    example: '(A ∧ B) ∨ ¬C',
  },
  {
    key: 'kmap',
    name: 'Mapa Karnaugh',
    description: 'Graficzna metoda upraszczania wyrażeń logicznych.',
    example: '(A ∧ B) ∨ ¬C',
  },
  {
    key: 'ast',
    name: 'AST (Abstrakcyjne Drzewo Składniowe)',
    description: 'Struktura drzewiasta reprezentująca składnię wyrażenia logicznego.',
    example: '(A ∧ B) ∨ ¬C',
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
    <div className="min-h-screen bg-gray-50 flex flex-col items-center p-4">
      <div className="w-full max-w-3xl">
        <button className="mb-6 text-blue-600 hover:underline" onClick={onBack}>&larr; Powrót</button>
        <h1 className="text-2xl font-bold mb-6 text-center">Definicje pojęć logicznych</h1>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {CONCEPTS.map(concept => (
            <div key={concept.key} className="bg-white shadow-md p-4 rounded-md flex flex-col justify-between">
              <div>
                <div className="text-lg font-semibold mb-2">{concept.name}</div>
                <div className="text-gray-600 mb-4">{concept.description}</div>
              </div>
              <button
                className="mt-auto bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition font-semibold"
                onClick={() => handleShowExample(concept)}
              >
                Pokaż przykład
              </button>
            </div>
          ))}
        </div>
      </div>
      {modal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-lg p-6 max-w-lg w-full relative overflow-y-auto max-h-[90vh]">
            <button className="absolute top-2 right-2 text-gray-500 hover:text-gray-800" onClick={closeModal}>✕</button>
            <h2 className="text-xl font-bold mb-4">Przykład: {CONCEPTS.find(c => c.key === modal)?.name}</h2>
            {loading ? (
              <div className="text-center">Ładowanie...</div>
            ) : modalData ? (
              <>
                {modalData.truth_table && modalData.truth_table.length > 0 && (
                  <div className="mb-4">
                    <div className="font-semibold mb-1">Tabela prawdy</div>
                    <div className="overflow-x-auto">
                      <table className="min-w-full border border-gray-300 rounded">
                        <thead>
                          <tr>
                            {Object.keys(modalData.truth_table[0]).map(col => (
                              <th key={col} className="px-3 py-1 border-b bg-gray-100 text-gray-700">{col}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {modalData.truth_table.map((row, i) => (
                            <tr key={i}>
                              {Object.values(row).map((val, j) => (
                                <td key={j} className="px-3 py-1 border-b text-center">{val}</td>
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
                    <div className="font-semibold">Uproszczenie QM:</div>
                    <div className="font-mono bg-gray-100 px-2 py-1 rounded inline-block">{modalData.qm.result}</div>
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