import React, { useState } from 'react';
import ResultScreen from './components/ResultScreen';
import DefinitionsScreen from './components/DefinitionsScreen';
import TutorialMode from './components/TutorialMode';
import ExpressionHistory from './components/ExpressionHistory';
import StartScreen from './components/StartScreen';
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
  '((A ∧ B) ∨ (C ∧ D)) → (¬D ∨ (A ∧ C))',
  '¬((A ∨ B) ∧ (C ∨ D)) ∨ (D ∧ (A → D))',
  '((A ↔ B) ∧ (C → D)) ∨ (¬A ∧ (B ∨ C))',
  '((A ∧ (B ∨ C)) → (D ∨ A)) ∧ (¬B ∨ (C ∧ D))',
  '((A ∨ B ∨ C) ∧ (D ∨ A)) → (A ∧ ¬D)',
  'A ⊕ B',
  'A ↑ B',
  'A ↓ B',
  'A ≡ B',
];

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
            onSubmit={handleAnalyze}
            onDefinitions={handleShowDefinitions}
            onExamples={() => setShowExamples(true)}
            onHistory={handleShowHistory}
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
      {screen === 'history' && <ExpressionHistory onLoad={handleLoadHistory} onBack={() => setScreen('start')} />}
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
