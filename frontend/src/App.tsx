import React, { useState } from 'react';
import ResultScreen from './components/ResultScreen';

function StartScreen({ onAnalyze }) {
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

  const handleAnalyze = (input) => {
    setInput(input);
    setScreen('result');
  };

  return (
    <div className="min-h-screen">
      {screen === 'start' && <StartScreen onAnalyze={handleAnalyze} />}
      {screen === 'result' && <ResultScreen input={input} onBack={() => setScreen('start')} />}
    </div>
  );
}

export default App;
