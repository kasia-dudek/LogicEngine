import React, { useState } from 'react';
import ResultScreen from './components/ResultScreen';
import DefinitionsScreen from './components/DefinitionsScreen';
import TutorialMode from './components/TutorialMode';
import ExpressionHistory from './components/ExpressionHistory';
import { analyze } from './__mocks__/api';

function StartScreen({ onAnalyze, onShowDefinitions, tutorialMode, onToggleTutorial, onShowHistory }) {
  const [input, setInput] = useState('');
  const operators = [
    { label: '¬', value: '¬' },
    { label: '∧', value: '∧' },
    { label: '∨', value: '∨' },
    { label: '→', value: '→' },
    { label: '↔', value: '↔' },
  ];
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50 p-4">
      <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8">
        <h1 className="text-2xl font-bold mb-4 text-center">LogicEngine</h1>
        <p className="mb-4 text-gray-600 text-center">Wprowadź wyrażenie logiczne i przeanalizuj je. Skorzystaj z przycisków operatorów, aby ułatwić wpisywanie.</p>
        <div className="flex gap-2 mb-4 flex-wrap justify-center">
          {operators.map(op => (
            <button
              key={op.value}
              type="button"
              className="bg-blue-100 text-blue-700 px-3 py-1 rounded hover:bg-blue-200 transition"
              onClick={() => setInput(input + op.value)}
            >
              {op.label}
            </button>
          ))}
        </div>
        <input
          className="w-full border border-gray-300 rounded px-3 py-2 mb-4 focus:outline-none focus:ring-2 focus:ring-blue-400"
          type="text"
          placeholder="np. (A ∧ B) → ¬C"
          value={input}
          onChange={e => setInput(e.target.value)}
        />
        <button
          className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 transition font-semibold"
          onClick={() => onAnalyze(input)}
        >
          Analizuj
        </button>
        <button
          className="w-full mt-4 bg-gray-200 text-gray-800 py-2 rounded hover:bg-gray-300 transition font-semibold"
          onClick={onShowDefinitions}
        >
          Definicje pojęć
        </button>
        <button
          className="w-full mt-2 bg-gray-200 text-gray-800 py-2 rounded hover:bg-gray-300 transition font-semibold"
          onClick={onShowHistory}
        >
          Historia wyrażeń
        </button>
        <div className="flex items-center mt-4">
          <input
            id="tutorial-toggle"
            type="checkbox"
            checked={tutorialMode}
            onChange={onToggleTutorial}
            className="mr-2"
          />
          <label htmlFor="tutorial-toggle" className="text-sm text-gray-700 select-none cursor-pointer">
            Tryb tutorialowy
          </label>
        </div>
        <div className="mt-6">
          <h2 className="text-lg font-semibold mb-2">Definicje (placeholder)</h2>
          <div className="bg-gray-100 rounded p-2 text-sm text-gray-500">Tu pojawią się definicje operatorów i pojęć logicznych.</div>
        </div>
      </div>
    </div>
  );
}

function App() {
  const [screen, setScreen] = useState('start');
  const [input, setInput] = useState('');
  const [tutorialMode, setTutorialMode] = useState(false);
  const [tutorialSteps, setTutorialSteps] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [historyItem, setHistoryItem] = useState(null);

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
    if (tutorialMode) {
      setLoading(true);
      setError('');
      try {
        const res = await analyze(input);
        if (res.tutorial_steps && res.tutorial_steps.length > 0) {
          setTutorialSteps(res.tutorial_steps);
          setScreen('tutorial');
          saveToHistory(input, res);
        } else {
          setError('Brak danych tutorialowych.');
        }
      } catch (e) {
        setError(e.message || 'Błąd API');
      } finally {
        setLoading(false);
      }
    } else {
      setScreen('result');
      // Zapisz do historii po analizie klasycznej
      try {
        const res = await analyze(input);
        saveToHistory(input, res);
      } catch {}
    }
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

  const handleToggleTutorial = () => {
    setTutorialMode((prev) => !prev);
  };

  return (
    <div className="min-h-screen">
      {screen === 'start' && (
        <StartScreen
          onAnalyze={handleAnalyze}
          onShowDefinitions={handleShowDefinitions}
          tutorialMode={tutorialMode}
          onToggleTutorial={handleToggleTutorial}
          onShowHistory={handleShowHistory}
        />
      )}
      {screen === 'result' && <ResultScreen input={input} onBack={() => setScreen('start')} />}
      {screen === 'definitions' && <DefinitionsScreen onBack={() => setScreen('start')} />}
      {screen === 'tutorial' && (
        <TutorialMode
          steps={tutorialSteps}
          onBack={() => setScreen('start')}
        />
      )}
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
