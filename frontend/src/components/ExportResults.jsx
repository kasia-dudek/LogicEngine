import React, { useState } from 'react';
import Toast from './Toast';

/**
 * Eksport wyników do PDF przez system print
 */
export default function ExportResults({ data, input, onExportToPrint }) {
  const [toast, setToast] = useState({ message: '', type: 'success' });

  const handleExportPDF = () => {
    if (!data || !input) {
      setToast({ message: 'Błąd eksportu: brak danych', type: 'error' });
      return;
    }
    
    // Wywołaj funkcję eksportu do print
    if (onExportToPrint) {
      onExportToPrint(data, input);
    }
  };

  const handleExportJSON = () => {
    if (!data) {
      setToast({ message: 'Błąd eksportu JSON: brak danych', type: 'error' });
      return;
    }
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'wyniki.json';
    a.click();
    setToast({ message: 'Eksport do JSON zakończony pomyślnie', type: 'success' });
  };

  return (
    <div className="flex flex-col items-center mt-4 space-y-2">
      <button
        className="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700 transition font-semibold"
        onClick={handleExportPDF}
      >
        Eksportuj do PDF
      </button>
      <button
        className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition font-semibold"
        onClick={handleExportJSON}
      >
        Eksportuj do JSON
      </button>
      <Toast
        message={toast.message}
        type={toast.type}
        onClose={() => setToast({ message: '', type: 'success' })}
      />
    </div>
  );
}
