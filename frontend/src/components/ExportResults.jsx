import React, { useState } from 'react';
import Toast from './Toast';
import ExportOptionsModal from './ExportOptionsModal';
import {
  computeOptionAvailability,
  buildDefaultSelection,
  EXPORT_SCHEMA_VERSION,
} from '../utils/exportOptions';

/**
 * Eksport wyników do PDF przez system print
 */
export default function ExportResults({ data, input, onExportToPrint }) {
  const [toast, setToast] = useState({ message: '', type: 'success' });
  const [showModal, setShowModal] = useState(false);

  const handleExportPDF = () => {
    if (!data || !input) {
      setToast({ message: 'Błąd eksportu: brak danych', type: 'error' });
      return;
    }
    
    // Pokaż modal z opcjami
    setShowModal(true);
  };

  const handleConfirmExport = (selectedOptions) => {
    if (!data || !input) {
      setToast({ message: 'Błąd eksportu: brak danych', type: 'error' });
      return;
    }
    
    // Zamknij modal
    setShowModal(false);
    
    // Wywołaj funkcję eksportu do print z opcjami
    if (onExportToPrint) {
      onExportToPrint(data, input, selectedOptions);
    }
  };

  const handleExportJSON = () => {
    if (!data) {
      setToast({ message: 'Błąd eksportu JSON: brak danych', type: 'error' });
      return;
    }
    const expression = typeof input === 'string' && input.trim().length > 0
      ? input
      : (data.expression || '');
    const availability = computeOptionAvailability(data).map(option => ({
      ...option,
      selectedByDefault: option.available,
    }));
    const defaultSelection = buildDefaultSelection(availability, { availableOnly: true });
    const exportPayload = {
      schema: EXPORT_SCHEMA_VERSION,
      exportedAt: new Date().toISOString(),
      source: 'LogicEngine',
      input: {
        expression,
        length: expression.length,
      },
      print: {
        sections: availability,
        defaults: defaultSelection,
      },
      results: data,
    };
    const blob = new Blob([JSON.stringify(exportPayload, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'logic-engine-export.json';
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 0);
    setToast({ message: 'Eksport do JSON zakończony pomyślnie', type: 'success' });
  };

  return (
    <>
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
      
      <ExportOptionsModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        onConfirm={handleConfirmExport}
        data={data}
      />
    </>
  );
}
