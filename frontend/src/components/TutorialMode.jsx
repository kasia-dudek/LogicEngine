import React, { useState, useEffect } from 'react';
import QMSteps from './QMSteps';
import KMapDisplay from './KMapDisplay';
import Toast from './Toast';

function TutorialMode({ steps, onBack }) {
  const [stepIdx, setStepIdx] = useState(0);
  const [toast, setToast] = useState({ message: '', type: 'success' });

  useEffect(() => {
    if (steps && steps[stepIdx] && steps[stepIdx].description) {
      setToast({ message: steps[stepIdx].description, type: 'success' });
    }
  }, [stepIdx, steps]);

  if (!steps || steps.length === 0) {
    return <div className="text-center p-8">Brak danych tutorialu.</div>;
  }

  const step = steps[stepIdx];

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50 p-4">
      <Toast message={toast.message} type={toast.type} onClose={() => setToast({ message: '', type: 'success' })} />
      <div className="max-w-2xl w-full bg-white rounded-lg shadow-lg p-8">
        <button className="mb-4 text-blue-600 hover:underline" onClick={onBack}>&larr; Wróć</button>
        <h1 className="text-2xl font-bold mb-4 text-center">Tryb tutorialowy</h1>
        <div className="mb-4">
          <span className="font-semibold">{step.step}</span>
        </div>
        <div className="mb-6">
          {step.data && step.data.truth_table && (
            <div className="mb-4">
              <div className="font-semibold mb-1">Tabela prawdy</div>
              <div className="overflow-x-auto">
                <table className="min-w-full border border-gray-300 rounded">
                  <thead>
                    <tr>
                      {Object.keys(step.data.truth_table[0]).map(col => (
                        <th key={col} className="px-3 py-1 border-b bg-gray-100 text-gray-700">{col}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {step.data.truth_table.map((row, i) => (
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
          {step.data && step.data.qm && step.data.qm.steps && (
            <QMSteps steps={step.data.qm.steps} />
          )}
          {step.data && step.data.kmap && step.data.kmap.kmap && (
            <KMapDisplay kmap={step.data.kmap.kmap} groups={step.data.kmap.groups} result={step.data.kmap.result} />
          )}
        </div>
        <div className="flex justify-between mt-4">
          <button
            className="bg-gray-200 text-gray-700 px-4 py-2 rounded hover:bg-gray-300 font-semibold"
            onClick={() => setStepIdx(idx => Math.max(0, idx - 1))}
            disabled={stepIdx === 0}
          >
            Poprzedni krok
          </button>
          <button
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 font-semibold"
            onClick={() => setStepIdx(idx => Math.min(steps.length - 1, idx + 1))}
            disabled={stepIdx === steps.length - 1}
          >
            Następny krok
          </button>
        </div>
      </div>
    </div>
  );
}

export default TutorialMode; 