import React, { useState } from 'react';
import jsPDF from 'jspdf';
import Toast from './Toast';

export default function ExportResults({ data }) {
  const [toast, setToast] = useState({ message: '', type: 'success' });

  const handleExportPDF = () => {
    if (!data) {
      setToast({ message: 'Błąd eksportu PDF: brak danych', type: 'error' });
      return;
    }
    try {
      const doc = new jsPDF();
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(16);
      doc.text(`Analiza wyrażenia: ${data.expression || ''}`, 10, 15);
      doc.setFontSize(12);
      let y = 25;
      if (data.truth_table) {
        doc.text('Tabela prawdy:', 10, y);
        y += 6;
        const cols = Object.keys(data.truth_table[0] || {});
        doc.setFont('helvetica', 'normal');
        doc.text(cols.join(' | '), 10, y);
        y += 6;
        data.truth_table.forEach(row => {
          doc.text(cols.map(c => String(row[c])).join(' | '), 10, y);
          y += 6;
        });
        y += 4;
      }
      if (data.qm) {
        doc.setFont('helvetica', 'bold');
        doc.text('Quine-McCluskey:', 10, y);
        y += 6;
        doc.setFont('helvetica', 'normal');
        if (data.qm.result) {
          doc.text(`Wynik: ${data.qm.result}`, 10, y);
          y += 6;
        }
        if (data.qm.steps) {
          data.qm.steps.forEach((step, i) => {
            doc.text(`Krok ${i + 1}: ${step.description || JSON.stringify(step)}`, 10, y);
            y += 6;
          });
        }
        y += 4;
      }
      if (data.kmap) {
        doc.setFont('helvetica', 'bold');
        doc.text('K-Map:', 10, y);
        y += 6;
        doc.setFont('helvetica', 'normal');
        if (data.kmap.result) {
          doc.text(`Wynik: ${data.kmap.result}`, 10, y);
          y += 6;
        }
        if (data.kmap.kmap) {
          doc.text('K-Map: ' + JSON.stringify(data.kmap.kmap), 10, y);
          y += 6;
        }
        y += 4;
      }
      if (data.ast) {
        doc.setFont('helvetica', 'bold');
        doc.text('AST:', 10, y);
        y += 6;
        doc.setFont('helvetica', 'normal');
        doc.text(JSON.stringify(data.ast), 10, y);
        y += 6;
      }
      doc.save('analiza_wyrazenia.pdf');
      setToast({ message: 'Eksport do PDF zakończony pomyślnie', type: 'success' });
    } catch (e) {
      setToast({ message: 'Błąd eksportu PDF: ' + e.message, type: 'error' });
    }
  };

  const handleExportJSON = () => {
    if (!data) {
      setToast({ message: 'Błąd eksportu JSON: brak danych', type: 'error' });
      return;
    }
    try {
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'analiza_wyrazenia.json';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      setToast({ message: 'Eksport do JSON zakończony pomyślnie', type: 'success' });
    } catch (e) {
      setToast({ message: 'Błąd eksportu JSON: ' + e.message, type: 'error' });
    }
  };

  return (
    <div className="flex gap-4 mt-4">
      <button
        className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 font-semibold"
        onClick={handleExportPDF}
      >
        Eksportuj do PDF
      </button>
      <button
        className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 font-semibold"
        onClick={handleExportJSON}
      >
        Eksportuj do JSON
      </button>
      <Toast message={toast.message} type={toast.type} onClose={() => setToast({ message: '', type: 'success' })} />
    </div>
  );
} 