import React, { useEffect, useState } from 'react';

const HISTORY_KEY = 'logicengine_history';
const MAX_HISTORY = 50;

function getHistory() {
  try {
    const data = localStorage.getItem(HISTORY_KEY);
    if (!data) return [];
    return JSON.parse(data);
  } catch {
    return [];
  }
}

function saveHistory(history) {
  localStorage.setItem(HISTORY_KEY, JSON.stringify(history.slice(0, MAX_HISTORY)));
}

export default function ExpressionHistory({ onLoad }) {
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
        <div className="bg-gray-100 rounded p-4 text-center text-gray-500">Brak historii wyrażeń.</div>
        <button className="mt-4 bg-gray-200 px-4 py-2 rounded text-gray-700 hover:bg-gray-300" onClick={handleClear} disabled>
          Wyczyść historię
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-4">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold">Historia wyrażeń</h2>
        <button className="bg-gray-200 px-4 py-2 rounded text-gray-700 hover:bg-gray-300" onClick={handleClear}>
          Wyczyść historię
        </button>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {history.map(item => (
          <div key={item.id} className="bg-white rounded shadow p-4 flex flex-col">
            <div className="font-mono text-sm break-all mb-2">{item.expression}</div>
            <div className="text-xs text-gray-500 mb-2">{item.id}</div>
            <button
              className="mt-auto bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700 transition"
              onClick={() => handleLoad(item)}
            >
              Wczytaj
            </button>
          </div>
        ))}
      </div>
    </div>
  );
} 