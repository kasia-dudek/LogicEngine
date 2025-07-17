import React, { useState, useEffect } from 'react';
import QMSteps from './QMSteps';
import KMapDisplay from './KMapDisplay';
import ASTDisplay from './ASTDisplay';
import Toast from './Toast';
import ExportResults from './ExportResults';
import { analyze } from '../__mocks__/api';

const TABS = [
  { key: 'truth', label: 'Tabela prawdy' },
  { key: 'qm', label: 'Quine-McCluskey' },
  { key: 'kmap', label: 'K-Map' },
  { key: 'ast', label: 'AST' },
];

function ResultScreen({ input, onBack }) {
  const [tab, setTab] = useState('truth');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [data, setData] = useState(null);
  const [toast, setToast] = useState({ message: '', type: 'success' });

  useEffect(() => {
    setLoading(true);
    setError('');
    setToast({ message: '', type: 'success' });
    // Wersja z prawdziwym API (jeśli ustawiono REACT_APP_API_URL)
    const apiUrl = process.env.REACT_APP_API_URL;
    const fetchData = async () => {
      try {
        let res;
        if (apiUrl) {
          const response = await fetch(`${apiUrl}/api/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ expression: input })
          });
          if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error || 'API error');
          }
          res = await response.json();
        } else {
          res = await analyze(input);
        }
        setData(res);
        setLoading(false);
        setToast({ message: 'Expression analyzed successfully!', type: 'success' });
      } catch (e) {
        setError(e.message || 'API error');
        setLoading(false);
        setToast({ message: `Error: ${e.message}`, type: 'error' });
      }
    };
    fetchData();
  }, [input]);

  if (loading) return <div className="text-center p-8">Ładowanie...</div>;
  if (error) return <div className="text-red-600 text-center p-8">{error}</div>;
  if (!data) return null;

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50 p-4">
      <Toast message={toast.message} type={toast.type} onClose={() => setToast({ message: '', type: 'success' })} />
      <div className="max-w-2xl w-full bg-white rounded-lg shadow-lg p-8">
        <button className="mb-4 text-blue-600 hover:underline" onClick={onBack}>&larr; Wróć</button>
        <h1 className="text-2xl font-bold mb-4 text-center">Wynik analizy</h1>
        <div className="mb-4">
          <span className="font-semibold">Wyrażenie:</span> <span className="font-mono bg-gray-100 px-2 py-1 rounded">{data.expression}</span>
        </div>
        <div className="mb-6">
          <div className="flex gap-2 mb-4 justify-center">
            {TABS.map(t => (
              <button
                key={t.key}
                className={`px-4 py-2 rounded-t ${tab === t.key ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700'} font-semibold`}
                onClick={() => setTab(t.key)}
              >
                {t.label}
              </button>
            ))}
          </div>
          <div className="bg-gray-50 p-4 rounded-b shadow-inner min-h-[180px]">
            {tab === 'truth' && (
              <div className="overflow-x-auto">
                {data.truth_table && data.truth_table.length > 0 ? (
                  <table className="min-w-full border border-gray-300 rounded">
                    <thead>
                      <tr>
                        {Object.keys(data.truth_table[0]).map(col => (
                          <th key={col} className="px-3 py-1 border-b bg-gray-100 text-gray-700">{col}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {data.truth_table.map((row, i) => (
                        <tr key={i}>
                          {Object.values(row).map((val, j) => (
                            <td key={j} className="px-3 py-1 border-b text-center">{val}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <div className="text-gray-500">Brak danych do wyświetlenia tabeli prawdy.</div>
                )}
              </div>
            )}
            {tab === 'qm' && (
              <QMSteps steps={data.qm?.steps} />
            )}
            {tab === 'kmap' && (
              <KMapDisplay kmap={data.kmap?.kmap} groups={data.kmap?.groups} result={data.kmap?.result} />
            )}
            {tab === 'ast' && (
              <ASTDisplay ast={data.ast} />
            )}
          </div>
        </div>
        <ExportResults data={data} />
        <div className="mt-6">
          <h2 className="text-lg font-semibold mb-2">Przyszłe funkcje (placeholder)</h2>
          <div className="bg-gray-100 rounded p-2 text-sm text-gray-500">Tu pojawią się kolejne analizy, np. minimalizacja, ONP, K-map, QM, tautologie.</div>
        </div>
      </div>
    </div>
  );
}

export default ResultScreen; 