import React, { useState } from 'react';
import Toast from './Toast';

/**
 * Estetyczny eksport PDF:
 * - A4, pt, spójne marginesy
 * - autoTable dla tabel (zawijanie, nagłówki, podsumowania)
 * - eleganckie fallbacki jeśli brak danych / pluginów
 * - opcjonalny zrzut K-Map i AST (jeśli istnieje element w DOM z data-export-kmap / data-export-ast)
 */
export default function ExportResults({ data }) {
  const [toast, setToast] = useState({ message: '', type: 'success' });

  const COLORS = {
    primary: [30, 58, 138],      // navy-ish
    accent: [59, 130, 246],      // blue
    text: [33, 33, 33],
    subtle: [120, 120, 120],
    green: [16, 185, 129],
    red: [239, 68, 68],
    chipBg: [248, 250, 252],     // #f8fafc
  };

  // Pomocnicze: nagłówek sekcji
  const sectionHeader = (doc, title, x, y) => {
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(16);
    doc.setTextColor(...COLORS.primary);
    doc.text(title, x, y);
    return y + 18;
  };

  const addKeyValue = (doc, label, value, x, y, maxWidth) => {
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(12);
    doc.setTextColor(...COLORS.primary);
    doc.text(label, x, y);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(...COLORS.text);
    const lines = doc.splitTextToSize(value ?? '—', maxWidth);
    doc.text(lines, x, y + 14);
    return y + 14 + lines.length * 12;
  };

  const ensurePage = (doc, y, marginTop, marginBottom) => {
    const pageH = doc.internal.pageSize.getHeight();
    if (y > pageH - marginBottom) {
      doc.addPage();
      return marginTop;
    }
    return y;
  };

  // Opcjonalne przechwycenie obrazu (K-Map, AST)
  const captureToImage = async (selector, scale = 2) => {
    const root = document.querySelector(selector);
    if (!root) return null;
    try {
      const html2canvas = (await import('html2canvas')).default;
      const canvas = await html2canvas(root, { scale, backgroundColor: null });
      return canvas.toDataURL('image/png');
    } catch {
      return null;
    }
  };

  const handleExportPDF = async () => {
    if (!data) {
      setToast({ message: 'Błąd eksportu PDF: brak danych', type: 'error' });
      return;
    }

    // Debug: sprawdź jakie dane są dostępne
    console.log('=== DEBUG PDF EXPORT ===');
    console.log('Data object:', data);
    console.log('Expression:', data.expression);
    console.log('Truth table:', data.truth_table);
    console.log('ONP:', data.onp);
    console.log('Tautology:', data.is_tautology);
    console.log('QM:', data.qm);
    console.log('Laws:', data.laws);
    console.log('K-Map:', data.kmap);
    console.log('========================');

    try {
      const jsPDF = (await import('jspdf')).default;
      const autoTable = (await import('jspdf-autotable')).default;
      
      const doc = new jsPDF();
      
      // Ustawienia stylu
      doc.setFont('helvetica');
      doc.setTextColor(30, 58, 138); // Niebieski kolor podobny do strony
      
      let y = 20;
      const margin = 20;
      const pageWidth = doc.internal.pageSize.width;
      const contentWidth = pageWidth - 2 * margin;
      
      // Tytuł główny - zmniejsz czcionkę żeby się zmieścił
      doc.setFontSize(20);
      doc.setFont('helvetica', 'bold');
      doc.text('Wynik analizy wyrażenia logicznego', pageWidth / 2, y, { align: 'center' });
      
      y += 20;
      
      // Wyrażenie
      doc.setFontSize(16);
      doc.setFont('helvetica', 'bold');
      doc.text('Wyrażenie:', margin, y);
      y += 8;
      doc.setFontSize(14);
      doc.setFont('helvetica', 'normal');
      doc.text(data.expression || 'Brak', margin, y);
      
      y += 20;
      
      // Sekcja podstawowych wyników
      doc.setFontSize(16);
      doc.setFont('helvetica', 'bold');
      doc.text('Podstawowe wyniki:', margin, y);
      y += 15;
      
      // Tabela prawdy - używamy autoTable dla lepszego formatowania
      if (data.truth_table && data.truth_table.length > 0) {
        console.log('Rendering truth table with', data.truth_table.length, 'rows');
        doc.setFontSize(12);
        doc.setFont('helvetica', 'bold');
        doc.text('Tabela prawdy:', margin, y);
        y += 8;
        
        // Przygotuj dane dla autoTable
        const headers = Object.keys(data.truth_table[0] || {});
        const tableData = data.truth_table.slice(0, 10).map(row => 
          headers.map(header => String(row[header]))
        );
        
        // Dodaj tabelę z autoTable
        autoTable(doc, {
          head: [headers],
          body: tableData,
          startY: y,
          margin: { left: margin },
          styles: {
            fontSize: 9,
            cellPadding: 3,
            headStyles: {
              fillColor: [59, 130, 246],
              textColor: [255, 255, 255],
              fontStyle: 'bold'
            },
            alternateRowStyles: {
              fillColor: [248, 250, 252]
            }
          },
          columnStyles: {
            [headers.length - 1]: { fontStyle: 'bold', fillColor: [254, 243, 199] } // Ostatnia kolumna (result) - żółte tło
          }
        });
        
        // Pobierz pozycję Y po tabeli
        y = doc.lastAutoTable.finalY + 10;
        
        if (data.truth_table.length > 10) {
          doc.setFontSize(8);
          doc.setFont('helvetica', 'italic');
          doc.text(`... i ${data.truth_table.length - 10} więcej wierszy`, margin, y);
          y += 8;
        }
        
        y += 10;
      } else {
        console.log('No truth table data available');
      }
      
      // ONP
      if (data.onp) {
        console.log('Rendering ONP:', data.onp);
        doc.setFontSize(12);
        doc.setFont('helvetica', 'bold');
        doc.text('ONP (Notacja polska):', margin, y);
        y += 8;
        doc.setFontSize(10);
        doc.setFont('helvetica', 'normal');
        doc.text(data.onp, margin, y);
        y += 15;
      } else {
        console.log('No ONP data available');
      }
      
      // Tautologia
      if (data.is_tautology !== undefined) {
        console.log('Rendering tautology:', data.is_tautology);
        doc.setFontSize(12);
        doc.setFont('helvetica', 'bold');
        doc.text('Tautologia:', margin, y);
        y += 8;
        doc.setFontSize(10);
        doc.setFont('helvetica', 'normal');
        
        // Ustaw kolor w zależności od wyniku
        if (data.is_tautology) {
          doc.setTextColor(34, 197, 94); // Zielony
        } else {
          doc.setTextColor(239, 68, 68); // Czerwony
        }
        
        doc.text(data.is_tautology ? 'TAK' : 'NIE', margin, y);
        doc.setTextColor(30, 58, 138); // Przywróć niebieski
        y += 15;
      } else {
        console.log('No tautology data available');
      }

      // Sprawdź czy potrzebna nowa strona
      if (y > 200) {
        doc.addPage();
        y = 20;
      }
      
      // Quine-McCluskey
      if (data.qm && data.qm.steps) {
        console.log('Rendering QM with', data.qm.steps.length, 'steps');
        doc.setFontSize(16);
        doc.setFont('helvetica', 'bold');
        doc.text('Quine-McCluskey:', margin, y);
        y += 15;
        
        data.qm.steps.forEach((step, stepIndex) => {
          // Sprawdź czy potrzebna nowa strona przed rozpoczęciem kroku
          if (y > 200) {
            doc.addPage();
            y = 20;
          }
          
          // Tło dla każdego kroku
          doc.setFillColor(248, 250, 252);
          doc.rect(margin - 5, y - 5, contentWidth + 10, 35, 'F');
          doc.setDrawColor(226, 232, 240);
          doc.rect(margin - 5, y - 5, contentWidth + 10, 35, 'S');
          
          // Napraw duplikację nazw kroków - usuń "Krok X: Krok X:" i zostaw tylko "Krok X:"
          let stepTitle = step.step || '';
          if (stepTitle.includes('Krok ')) {
            // Znajdź pierwsze wystąpienie "Krok X:" i usuń duplikaty
            const match = stepTitle.match(/Krok \d+:/);
            if (match) {
              stepTitle = stepTitle.replace(new RegExp(`${match[0]} `, 'g'), '');
              stepTitle = match[0] + ' ' + stepTitle;
            }
          }
          
          doc.setFontSize(12);
          doc.setFont('helvetica', 'bold');
          doc.setTextColor(59, 130, 246);
          doc.text(stepTitle, margin, y);
          y += 8;
          
          // Dodaj szczegółowe dane kroku
          if (step.data) {
            // Renderuj tabele jeśli są dostępne
            if (step.data.minterms && Array.isArray(step.data.minterms)) {
              // Sprawdź czy tabela się zmieści
              if (y > 220) {
                doc.addPage();
                y = 20;
              }
              
              doc.setFontSize(9);
              doc.setFont('helvetica', 'normal');
              doc.setTextColor(75, 85, 99);
              doc.text('Mintermy:', margin, y);
              y += 6;
              
              // Tabela mintermów
              const mintermData = step.data.minterms.map(m => [String(m)]);
              autoTable(doc, {
                head: [['Minterm']],
                body: mintermData,
                startY: y,
                margin: { left: margin },
                styles: {
                  fontSize: 8,
                  cellPadding: 2,
                  headStyles: {
                    fillColor: [59, 130, 246],
                    textColor: [255, 255, 255],
                    fontStyle: 'bold'
                  }
                },
                tableWidth: contentWidth * 0.3
              });
              y = doc.lastAutoTable.finalY + 5;
            }
            
            // Renderuj grupowane mintermy
            if (step.data.grupy && Array.isArray(step.data.grupy)) {
              // Sprawdź czy tabela się zmieści
              if (y > 220) {
                doc.addPage();
                y = 20;
              }
              
              doc.setFontSize(9);
              doc.setFont('helvetica', 'normal');
              doc.setTextColor(75, 85, 99);
              doc.text('Grupowane mintermy:', margin, y);
              y += 6;
              
              const grupyData = step.data.grupy.map(g => [String(g)]);
              autoTable(doc, {
                head: [['Grupa']],
                body: grupyData,
                startY: y,
                margin: { left: margin },
                styles: {
                  fontSize: 8,
                  cellPadding: 2,
                  headStyles: {
                    fillColor: [34, 197, 94],
                    textColor: [255, 255, 255],
                    fontStyle: 'bold'
                  }
                },
                tableWidth: contentWidth * 0.3
              });
              y = doc.lastAutoTable.finalY + 5;
            }
            
            // Renderuj implikanty
            if (step.data.implikanty && Array.isArray(step.data.implikanty)) {
              // Sprawdź czy tabela się zmieści
              if (y > 220) {
                doc.addPage();
                y = 20;
              }
              
              doc.setFontSize(9);
              doc.setFont('helvetica', 'normal');
              doc.setTextColor(75, 85, 99);
              doc.text('Implikanty:', margin, y);
              y += 6;
              
              const implikantyData = step.data.implikanty.map(i => [String(i)]);
              autoTable(doc, {
                head: [['Implikant']],
                body: implikantyData,
                startY: y,
                margin: { left: margin },
                styles: {
                  fontSize: 8,
                  cellPadding: 2,
                  headStyles: {
                    fillColor: [251, 191, 36],
                    textColor: [255, 255, 255],
                    fontStyle: 'bold'
                  }
                },
                tableWidth: contentWidth * 0.3
              });
              y = doc.lastAutoTable.finalY + 5;
            }
            
            // Renderuj inne dane jeśli są dostępne
            if (step.data.opis) {
              doc.setFontSize(9);
              doc.setFont('helvetica', 'normal');
              doc.setTextColor(75, 85, 99);
              doc.text(step.data.opis, margin, y);
              y += 8;
            }
          }
          
          y += 10;
        });
        
        if (data.qm.result) {
          y += 5;
          doc.setFontSize(12);
          doc.setFont('helvetica', 'bold');
          doc.setTextColor(30, 58, 138);
          doc.text('Wynik QM:', margin, y);
          y += 8;
          doc.setFontSize(10);
          doc.setFont('helvetica', 'normal');
          doc.setTextColor(34, 197, 94);
          doc.text(data.qm.result, margin, y);
          y += 15;
        }
      } else {
        console.log('No QM data available');
      }
      
      // Sprawdź czy potrzebna nowa strona
      if (y > 200) {
        doc.addPage();
        y = 20;
      }
      
      // Prawa logiczne
      if (data.laws && data.laws.steps) {
        console.log('Rendering Laws with', data.laws.steps.length, 'steps');
        doc.setFontSize(16);
        doc.setFont('helvetica', 'bold');
        doc.text('Prawa logiczne:', margin, y);
        y += 15;
        
        data.laws.steps.forEach((step, stepIndex) => {
          if (y > 250) {
            doc.addPage();
            y = 20;
          }
          
          // Tło dla każdego kroku
          doc.setFillColor(254, 243, 199);
          doc.rect(margin - 5, y - 5, contentWidth + 10, 30, 'F');
          doc.setDrawColor(251, 191, 36);
          doc.rect(margin - 5, y - 5, contentWidth + 10, 30, 'S');
          
          doc.setFontSize(12);
          doc.setFont('helvetica', 'bold');
          doc.setTextColor(194, 65, 12);
          doc.text(`Krok ${stepIndex + 1}: ${step.law}`, margin, y);
          y += 8;
          
          if (step.note) {
            doc.setFontSize(9);
            doc.setFont('helvetica', 'italic');
            doc.setTextColor(120, 113, 108);
            doc.text(step.note, margin, y);
            y += 6;
          }
          
          doc.setFontSize(10);
          doc.setFont('helvetica', 'normal');
          doc.setTextColor(75, 85, 99);
          doc.text(`${step.before_subexpr} → ${step.after_subexpr}`, margin, y);
          y += 10;
        });
        
        if (data.laws.result) {
          y += 5;
          doc.setFontSize(12);
          doc.setFont('helvetica', 'bold');
          doc.setTextColor(30, 58, 138);
          doc.text('Uproszczone wyrażenie:', margin, y);
          y += 8;
          doc.setFontSize(10);
          doc.setFont('helvetica', 'normal');
          doc.setTextColor(34, 197, 94);
          doc.text(data.laws.result, margin, y);
          y += 15;
        }
      } else {
        console.log('No Laws data available');
      }
      
      // Sprawdź czy potrzebna nowa strona
      if (y > 200) {
        doc.addPage();
        y = 20;
      }
      
      // K-Map
      if (data.kmap && data.kmap.result) {
        console.log('Rendering K-Map:', data.kmap.result);
        doc.setFontSize(16);
        doc.setFont('helvetica', 'bold');
        doc.text('Karnaugh Map:', margin, y);
        y += 15;
        
        doc.setFontSize(12);
        doc.setFont('helvetica', 'bold');
        doc.text('Wynik K-Map:', margin, y);
        y += 8;
        doc.setFontSize(10);
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(34, 197, 94);
        doc.text(data.kmap.result, margin, y);
        y += 15;
      } else {
        console.log('No K-Map data available');
      }
      
      // Sprawdź czy potrzebna nowa strona
      if (y > 200) {
        doc.addPage();
        y = 20;
      }
      
      // Minimal Forms
      if (data.minimal_forms) {
        console.log('Rendering Minimal Forms');
        doc.setFontSize(16);
        doc.setFont('helvetica', 'bold');
        doc.text('Minimal Forms:', margin, y);
        y += 15;
        
        // DNF
        doc.setFontSize(12);
        doc.setFont('helvetica', 'bold');
        doc.text('DNF (SOP):', margin, y);
        y += 8;
        doc.setFontSize(10);
        doc.setFont('helvetica', 'normal');
        doc.text(data.minimal_forms.dnf.expr, margin, y);
        y += 8;
        doc.setFontSize(8);
        doc.setTextColor(100, 100, 100);
        doc.text(`termy: ${data.minimal_forms.dnf.terms}, literały: ${data.minimal_forms.dnf.literals}`, margin, y);
        y += 12;
        
        // CNF
        doc.setFontSize(12);
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(30, 58, 138);
        doc.text('CNF (POS):', margin, y);
        y += 8;
        doc.setFontSize(10);
        doc.setFont('helvetica', 'normal');
        doc.text(data.minimal_forms.cnf.expr, margin, y);
        y += 8;
        doc.setFontSize(8);
        doc.setTextColor(100, 100, 100);
        doc.text(`termy: ${data.minimal_forms.cnf.terms}, literały: ${data.minimal_forms.cnf.literals}`, margin, y);
        y += 12;
        
        // ANF
        doc.setFontSize(12);
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(30, 58, 138);
        doc.text('ANF:', margin, y);
        y += 8;
        doc.setFontSize(10);
        doc.setFont('helvetica', 'normal');
        doc.text(data.minimal_forms.anf.expr, margin, y);
        y += 8;
        doc.setFontSize(8);
        doc.setTextColor(100, 100, 100);
        doc.text(`jednomiany: ${data.minimal_forms.anf.monomials}`, margin, y);
        y += 12;
        
        // NAND
        doc.setFontSize(12);
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(30, 58, 138);
        doc.text('NAND-only:', margin, y);
        y += 8;
        doc.setFontSize(10);
        doc.setFont('helvetica', 'normal');
        doc.text(data.minimal_forms.nand.expr, margin, y);
        y += 8;
        doc.setFontSize(8);
        doc.setTextColor(100, 100, 100);
        doc.text(`bramki: ${data.minimal_forms.nand.gates}`, margin, y);
        y += 12;
        
        // NOR
        doc.setFontSize(12);
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(30, 58, 138);
        doc.text('NOR-only:', margin, y);
        y += 8;
        doc.setFontSize(10);
        doc.setFont('helvetica', 'normal');
        doc.text(data.minimal_forms.nor.expr, margin, y);
        y += 8;
        doc.setFontSize(8);
        doc.setTextColor(100, 100, 100);
        doc.text(`bramki: ${data.minimal_forms.nor.gates}`, margin, y);
        y += 12;
        
        // AND-only
        doc.setFontSize(12);
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(30, 58, 138);
        doc.text('AND-only:', margin, y);
        y += 8;
        doc.setFontSize(10);
        doc.setFont('helvetica', 'normal');
        doc.text(data.minimal_forms.andonly.expr, margin, y);
        y += 8;
        doc.setFontSize(8);
        doc.setTextColor(100, 100, 100);
        doc.text(`literały: ${data.minimal_forms.andonly.literals}`, margin, y);
        y += 12;
        
        // OR-only
        doc.setFontSize(12);
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(30, 58, 138);
        doc.text('OR-only:', margin, y);
        y += 8;
        doc.setFontSize(10);
        doc.setFont('helvetica', 'normal');
        doc.text(data.minimal_forms.oronly.expr, margin, y);
        y += 8;
        doc.setFontSize(8);
        doc.setTextColor(100, 100, 100);
        doc.text(`literały: ${data.minimal_forms.oronly.literals}`, margin, y);
        y += 12;
        
        // Notes
        if (data.minimal_forms.notes && data.minimal_forms.notes.length > 0) {
          y += 5;
          doc.setFontSize(10);
          doc.setFont('helvetica', 'bold');
          doc.setTextColor(59, 130, 246);
          doc.text('Uwagi:', margin, y);
          y += 8;
          doc.setFontSize(8);
          doc.setFont('helvetica', 'normal');
          doc.setTextColor(100, 100, 100);
          for (const note of data.minimal_forms.notes) {
            doc.text(`• ${note}`, margin, y);
            y += 6;
          }
        }
      } else {
        console.log('No Minimal Forms data available');
      }

      // Stopka
      const pageCount = doc.internal.getNumberOfPages();
      console.log('PDF generated with', pageCount, 'pages');
      
      for (let i = 1; i <= pageCount; i++) {
        doc.setPage(i);
        doc.setFontSize(8);
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(100, 100, 100);
        doc.text(`Strona ${i} z ${pageCount}`, pageWidth - margin, doc.internal.pageSize.height - 10, { align: 'right' });
        doc.text(`Wygenerowano: ${new Date().toLocaleString('pl-PL')}`, margin, doc.internal.pageSize.height - 10);
      }
      
      // Zapisz PDF
      const filename = `analiza_${data.expression?.replace(/[^a-zA-Z0-9]/g, '_') || 'wyrazenia'}.pdf`;
      console.log('Saving PDF as:', filename);
      doc.save(filename);
      setToast({ message: 'Eksport do PDF zakończony pomyślnie', type: 'success' });
      
    } catch (error) {
      console.error('Błąd eksportu PDF:', error);
      setToast({ message: `Błąd eksportu PDF: ${error.message}`, type: 'error' });
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
      <Toast
        message={toast.message}
        type={toast.type}
        onClose={() => setToast({ message: '', type: 'success' })}
      />
    </div>
  );
}
