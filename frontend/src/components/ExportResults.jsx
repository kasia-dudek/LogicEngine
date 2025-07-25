import React, { useState } from 'react';
import Toast from './Toast';

export default function ExportResults({ data }) {
  const [toast, setToast] = useState({ message: '', type: 'success' });

  const handleExportPDF = async () => {
    if (!data) {
      setToast({ message: 'Błąd eksportu PDF: brak danych', type: 'error' });
      return;
    }
    const jsPDF = (await import('jspdf')).default;
    const doc = new jsPDF();
    doc.setFont('helvetica');
    doc.setFontSize(14);
    doc.text(`Wyrażenie: ${data.expression}`, 10, 20);
    doc.setFontSize(10);
    doc.text('Tabela prawdy:', 10, 30);
    if (data.truth_table) {
      let y = 40;
      data.truth_table.forEach((row, i) => {
        doc.text(JSON.stringify(row), 10, y + i * 7);
      });
    }
    doc.save('wyniki.pdf');
    setToast({ message: 'Eksport do PDF zakończony pomyślnie', type: 'success' });
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
    <div className="flex flex-col items-center mt-4">
      <button
        className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 transition font-semibold mb-2"
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
      <Toast message={toast.message} type={toast.type} onClose={() => setToast({ message: '', type: 'success' })} />
    </div>
  );
} 