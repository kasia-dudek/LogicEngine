import React, { useState } from 'react';
import ResultScreen from './components/ResultScreen';
import DefinitionsScreen from './components/DefinitionsScreen';
import TutorialMode from './components/TutorialMode';
import ExpressionHistory from './components/ExpressionHistory';
import { analyze } from './__mocks__/api';

const EXAMPLES = [
  '(A ∧ B) ∨ ¬C',
  'A ∨ (B ∧ C)',
  'A → B',
  'A ↔ B',
  '¬(A ∧ B)',
  'A ∧ (B ∨ C)',
  'A ∨ B ∨ C',
  'A ∧ B ∧ C',
  'A ∨ ¬A',
  'A ∧ ¬A',
  // Dłuższe, ale max 4 zmienne:
  '((A ∧ B) ∨ (C ∧ D)) → (¬D ∨ (A ∧ C))',
  '¬((A ∨ B) ∧ (C ∨ D)) ∨ (D ∧ (A → D))',
  '((A ↔ B) ∧ (C → D)) ∨ (¬A ∧ (B ∨ C))',
  '((A ∧ (B ∨ C)) → (D ∨ A)) ∧ (¬B ∨ (C ∧ D))',
  '((A ∨ B ∨ C) ∧ (D ∨ A)) → (A ∧ ¬D)',
];

function StartScreen({ onAnalyze, onShowDefinitions, onShowHistory, onShowExamples }) {
  const [input, setInput] = useState('');
  const operators = [
    { label: '¬', value: '¬' },
    { label: '∧', value: '∧' },
    { label: '∨', value: '∨' },
    { label: '→', value: '→' },
    { label: '↔', value: '↔' },
  ];
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-white flex flex-col items-center justify-center">
      <div className="max-w-md w-full bg-white rounded-3xl shadow-2xl p-10 border border-blue-100 animate-fade-in">
        <h1 className="text-4xl font-extrabold mb-6 text-center text-blue-700 tracking-tight drop-shadow">LogicEngine</h1>
        <p className="mb-6 text-gray-600 text-center text-lg">Wprowadź wyrażenie logiczne i przeanalizuj je. Skorzystaj z przycisków operatorów, aby ułatwić wpisywanie.</p>
        <div className="flex gap-2 mb-6 flex-wrap justify-center">
          {operators.map(op => (
            <button
              key={op.value}
              type="button"
              className="bg-blue-100 text-blue-700 px-4 py-2 rounded-full hover:bg-blue-200 transition-all shadow-sm text-xl font-bold"
              onClick={() => setInput(input + op.value)}
            >
              {op.label}
            </button>
          ))}
        </div>
        <input
          className="w-full border border-blue-200 rounded-xl px-4 py-3 mb-6 focus:outline-none focus:ring-2 focus:ring-blue-400 shadow-sm text-lg transition-all"
          type="text"
          placeholder="np. (A ∧ B) → ¬C"
          value={input}
          onChange={e => setInput(e.target.value)}
        />
        <button
          className="w-full bg-blue-600 text-white py-3 rounded-xl hover:bg-blue-700 transition-all font-semibold text-lg shadow-md mb-3"
          onClick={() => onAnalyze(input)}
        >
          <span role="img" aria-label="analyze">🔍</span> Analizuj
        </button>
        <button
          className="w-full mt-2 bg-gray-100 text-blue-700 py-3 rounded-xl hover:bg-blue-200 transition-all font-semibold mb-2 shadow-sm border border-blue-100"
          onClick={onShowDefinitions}
        >
          <span role="img" aria-label="definitions">📖</span> Definicje pojęć
        </button>
        <button
          className="w-full bg-gray-100 text-blue-700 py-3 rounded-xl hover:bg-blue-200 transition-all font-semibold shadow-sm border border-blue-100"
          onClick={onShowHistory}
        >
          <span role="img" aria-label="history">🕑</span> Historia wyrażeń
        </button>
        <button
          className="w-full mt-2 bg-gray-100 text-blue-700 py-3 rounded-xl hover:bg-blue-200 transition-all font-semibold shadow-sm border border-blue-100"
          onClick={onShowExamples}
        >
          <span role="img" aria-label="examples">💡</span> Przykłady
        </button>
      </div>
    </div>
  );
}

function App() {
  const [screen, setScreen] = useState('start');
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [historyItem, setHistoryItem] = useState(null);
  const [showExamples, setShowExamples] = useState(false);

  const saveToHistory = (expression, result) => {
    const HISTORY_KEY = 'logicengine_history';
    const MAX_HISTORY = 50;
    const id = new Date().toISOString();
    let history: any[] = [];
    try {
      const data = localStorage.getItem(HISTORY_KEY);
      if (data) history = JSON.parse(data);
    } catch {}
    history.unshift({ id, expression, result });
    localStorage.setItem(HISTORY_KEY, JSON.stringify(history.slice(0, MAX_HISTORY)));
  };

  const handleAnalyze = async (input) => {
    setInput(input);
    setScreen('result');
    // Zapisz do historii po analizie klasycznej
    try {
      const res = await analyze(input);
      saveToHistory(input, res);
    } catch {}
  };

  const handleShowDefinitions = () => {
    setScreen('definitions');
  };

  const handleShowHistory = () => {
    setScreen('history');
  };

  const handleLoadHistory = (item) => {
    setHistoryItem(item);
    setInput(item.expression);
    setScreen('result');
  };

  const handleExample = (expr) => {
    setShowExamples(false);
    handleAnalyze(expr);
  };

  return (
    <div className="min-h-screen">
      {screen === 'start' && (
        <>
          <StartScreen
            onAnalyze={handleAnalyze}
            onShowDefinitions={handleShowDefinitions}
            onShowHistory={handleShowHistory}
            onShowExamples={() => setShowExamples(true)}
          />
          {showExamples && (
            <div className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50">
              <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full relative animate-fade-in border border-blue-100">
                <button className="absolute top-2 right-2 text-gray-500 hover:text-gray-800 text-2xl" onClick={() => setShowExamples(false)}>✕</button>
                <h2 className="text-2xl font-bold mb-6 text-blue-700 text-center">Przykładowe wyrażenia</h2>
                <ul className="space-y-3">
                  {EXAMPLES.map((ex, i) => (
                    <li key={i}>
                      <button
                        className="w-full bg-blue-100 hover:bg-blue-200 text-blue-800 font-mono px-4 py-2 rounded-xl transition-all text-lg text-left shadow"
                        onClick={() => handleExample(ex)}
                      >
                        {ex}
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </>
      )}
      {screen === 'result' && <ResultScreen input={input} onBack={() => setScreen('start')} />}
      {screen === 'definitions' && <DefinitionsScreen onBack={() => setScreen('start')} />}
      {screen === 'history' && <ExpressionHistory onLoad={handleLoadHistory} />}
      {loading && (
        <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-30 z-50">
          <div className="bg-white p-6 rounded shadow text-lg">Ładowanie...</div>
        </div>
      )}
      {error && (
        <div className="fixed bottom-4 left-1/2 transform -translate-x-1/2 bg-red-500 text-white px-4 py-2 rounded shadow z-50">
          {error}
        </div>
      )}
    </div>
  );
}

export default App;
