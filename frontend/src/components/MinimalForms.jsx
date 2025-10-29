// MinimalForms.jsx
import React, { useState } from 'react';
import ColoredExpression from './ColoredExpression';

/**
 * Component presenting minimal forms (DNF, CNF) from backend /minimal_forms.
 * Focuses only on DNF and CNF with legend hidden by default.
 *
 * Props:
 *  - data: object (data from API /minimal_forms)
 */
export default function MinimalForms({ data }) {
  const [showDnfLegend, setShowDnfLegend] = useState(false);
  const [showCnfLegend, setShowCnfLegend] = useState(false);

  if (!data) {
    return (
      <div className="text-center text-gray-500 p-4">
        Brak danych dla form minimalnych
      </div>
    );
  }

  const vars = data?.vars || [];
  const dnf = data?.dnf || {};
  const cnf = data?.cnf || {};
  const notes = data?.notes || [];

  return (
    <div className="w-full max-w-7xl mx-auto px-4 md:px-6">
      {/* Header with explanation */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl md:text-3xl font-extrabold text-blue-700 tracking-tight">
            Formy Minimalne (DNF / CNF)
          </h2>
          {vars.length > 0 && (
            <div className="text-sm text-gray-600 bg-blue-50 px-3 py-1 rounded-full">
              Zmienne: {vars.join(', ')}
            </div>
          )}
        </div>
      </div>

      {/* Main content - 2 column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* DNF */}
        <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center">
              <span className="w-4 h-4 bg-blue-500 rounded-full mr-3"></span>
              <div>
                <h3 className="text-lg font-bold text-gray-800 flex items-center">
                  DNF (Forma dysjunkcyjna)
                  <span className="ml-2 text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                    Suma iloczynów
                  </span>
                </h3>
              </div>
            </div>
            <button
              onClick={() => setShowDnfLegend(!showDnfLegend)}
              className="bg-blue-100 hover:bg-blue-200 text-blue-700 rounded-full w-7 h-7 flex items-center justify-center font-bold text-sm transition-colors ml-2 flex-shrink-0"
              title="Pokaż informacje o metodzie"
            >
              ?
            </button>
          </div>
          
          {/* Legend DNF - ukryta domyślnie */}
          {showDnfLegend && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
              <div className="flex justify-between items-start mb-2">
                <h4 className="text-sm font-semibold text-blue-800">Metoda obliczania DNF:</h4>
                <button
                  onClick={() => setShowDnfLegend(false)}
                  className="text-blue-600 hover:text-blue-800 font-bold"
                >
                  ✕
                </button>
              </div>
              <div className="text-xs text-blue-700 space-y-2">
                <div>
                  <strong>Algorytm:</strong> Quine-McCluskey + Petrick
                </div>
                <div>
                  <strong>Opis:</strong> Metoda Quine-McCluskey znajduje minimalne wyrażenie poprzez systematyczne łączenie termów aż do uzyskania pierwszych implikantów. Metoda Petrick dobiera minimalną liczbę implikantów pokrywającą wszystkie mintermy.
                </div>
                <div className="mt-2 pt-2 border-t border-blue-300">
                  <strong>Terminy:</strong> Liczba iloczynów w sumie | <strong>Literały:</strong> Łączna liczba zmiennych w wyrażeniu
                </div>
              </div>
            </div>
          )}
          
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-gray-600 mb-2 block">Wyrażenie minimalne:</label>
              <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-900">
                <ColoredExpression expression={dnf?.expr || 'Brak danych'} className="text-blue-900" />
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-50 p-3 rounded-lg">
                <div className="text-xs text-gray-500 mb-1">Terminy (iloczyny)</div>
                <div className="text-lg font-bold text-blue-600">{dnf?.terms || 0}</div>
              </div>
              <div className="bg-gray-50 p-3 rounded-lg">
                <div className="text-xs text-gray-500 mb-1">Łącznie literałów</div>
                <div className="text-lg font-bold text-blue-600">{dnf?.literals || 0}</div>
              </div>
            </div>
            
          </div>
        </div>

        {/* CNF */}
        <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center">
              <span className="w-4 h-4 bg-green-500 rounded-full mr-3"></span>
              <div>
                <h3 className="text-lg font-bold text-gray-800 flex items-center">
                  CNF (Forma koniunkcyjna)
                  <span className="ml-2 text-xs bg-green-100 text-green-700 px-2 py-1 rounded">
                    Iloczyn sum
                  </span>
                </h3>
              </div>
            </div>
            <button
              onClick={() => setShowCnfLegend(!showCnfLegend)}
              className="bg-green-100 hover:bg-green-200 text-green-700 rounded-full w-7 h-7 flex items-center justify-center font-bold text-sm transition-colors ml-2 flex-shrink-0"
              title="Pokaż informacje o metodzie"
            >
              ?
            </button>
          </div>
          
          {/* Legend CNF - ukryta domyślnie */}
          {showCnfLegend && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-3 mb-4">
              <div className="flex justify-between items-start mb-2">
                <h4 className="text-sm font-semibold text-green-800">Metoda obliczania CNF:</h4>
                <button
                  onClick={() => setShowCnfLegend(false)}
                  className="text-green-600 hover:text-green-800 font-bold"
                >
                  ✕
                </button>
              </div>
              <div className="text-xs text-green-700 space-y-2">
                <div>
                  <strong>Algorytm:</strong> Dualność funkcji przez Quine-McCluskey + Petrick
                </div>
                <div>
                  <strong>Opis:</strong> CNF dla funkcji f oblicza się najpierw przez znalezienie minimalnego DNF dla funkcji negowanej (¬f) przy użyciu metody Quine-McCluskey + Petrick. Następnie stosuje się dualność: koniunkcje w DNF(¬f) stają się alternatywami w CNF(f), a każdy literał zostaje zanegowany (negacja negacji daje oryginał).
                </div>
                <div className="mt-2 pt-2 border-t border-green-300">
                  <strong>Terminy:</strong> Liczba klauzul w koniunkcji | <strong>Literały:</strong> Łączna liczba zmiennych w wyrażeniu
                </div>
              </div>
            </div>
          )}
          
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-gray-600 mb-2 block">Wyrażenie minimalne:</label>
              <div className="p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-900">
                <ColoredExpression expression={cnf?.expr || 'Brak danych'} className="text-green-900" />
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-50 p-3 rounded-lg">
                <div className="text-xs text-gray-500 mb-1">Terminy (sumy)</div>
                <div className="text-lg font-bold text-green-600">{cnf?.terms || 0}</div>
              </div>
              <div className="bg-gray-50 p-3 rounded-lg">
                <div className="text-xs text-gray-500 mb-1">Łącznie literałów</div>
                <div className="text-lg font-bold text-green-600">{cnf?.literals || 0}</div>
              </div>
            </div>
            
          </div>
        </div>
      </div>

      {/* Notes section */}
      {notes.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-yellow-800 mb-3 flex items-center">
            <span className="w-3 h-3 bg-yellow-500 rounded-full mr-2"></span>
            Uwagi analizy
          </h3>
          <ul className="space-y-2">
            {notes.map((note, index) => (
              <li key={index} className="text-sm text-yellow-700 bg-yellow-100 p-2 rounded">
                {note}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}