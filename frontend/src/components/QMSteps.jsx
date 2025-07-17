import React from 'react';

function QMSteps({ steps }) {
  if (!steps || steps.length === 0) {
    return <div className="text-gray-500">Brak danych do wyświetlenia kroków QM.</div>;
  }
  return (
    <div className="space-y-4">
      {steps.map((step, idx) => (
        <div key={idx} className="bg-gray-100 p-4 rounded-md shadow-sm">
          <div className="font-semibold mb-1">{step.step}</div>
          <pre className="text-sm text-gray-700 whitespace-pre-wrap">{JSON.stringify(step.data, null, 2)}</pre>
        </div>
      ))}
    </div>
  );
}

export default QMSteps; 