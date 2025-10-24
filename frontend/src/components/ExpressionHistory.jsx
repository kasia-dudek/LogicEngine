import React, { useEffect, useState } from 'react';

const HISTORY_KEY = 'logicengine_history';

function getHistory() {
  try {
    const data = localStorage.getItem(HISTORY_KEY);
    if (!data) return [];
    return JSON.parse(data);
  } catch {
    return [];
  }
}


export default function ExpressionHistory({ onLoad, onBack }) {
  const [history, setHistory] = useState([]);

  useEffect(() => {
    setHistory(getHistory());
  }, []);

  const handleLoad = (item) => {
    if (onLoad) onLoad(item);
  };

  const handleClear = () => {
    localStorage.removeItem(HISTORY_KEY);
    setHistory([]);
  };

  if (history.length === 0) {
    return (
      <div className="max-w-4xl mx-auto p-4">
        {onBack && (
          <button className="mb-6 text-blue-600 hover:underline text-lg font-semibold" onClick={onBack}>&larr; Powrót</button>
        )}
        <div className="bg-gray-100 rounded p-4 text-center text-gray-500">Brak historii wyrażeń.</div>
        <button className="mt-4 bg-gray-200 px-4 py-2 rounded text-gray-700 hover:bg-gray-300" onClick={handleClear} disabled>
          Wyczyść historię
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-4">
      {onBack && (
        <button className="mb-6 text-blue-600 hover:underline text-lg font-semibold" onClick={onBack}>&larr; Powrót</button>
      )}
      <div className="bg-white rounded-2xl shadow-xl p-6 border border-blue-100 animate-fade-in">
        <h2 className="text-2xl font-bold mb-4 text-blue-700">Historia wyrażeń</h2>
        <ul className="divide-y divide-blue-100">
          {history.map(item => (
            <li key={item.id} className="py-3 flex items-center justify-between">
              <span className="font-mono text-blue-900 text-lg">{item.expression}</span>
              <button className="bg-blue-100 text-blue-700 px-3 py-1 rounded hover:bg-blue-200 font-semibold ml-4" onClick={() => handleLoad(item)}>
                Załaduj
              </button>
            </li>
          ))}
        </ul>
        <button className="mt-6 bg-gray-200 px-4 py-2 rounded text-gray-700 hover:bg-gray-300" onClick={handleClear}>
          Wyczyść historię
        </button>
      </div>
    </div>
  );
} 