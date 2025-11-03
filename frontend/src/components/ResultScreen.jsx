// ResultScreen.jsx
import React, { useState, useEffect, useRef } from 'react';
import QMSteps from './QMSteps';
import KMapDisplay from './KMapDisplay';
import ASTDisplay from './ASTDisplay';
import LogicGatesDisplay from './LogicGatesDisplay';
import Toast from './Toast';
import ExportResults from './ExportResults';
import SimplifyDNF from './SimplifyDNF';
import { getAstStepsNoVars, evalAst, getStepArgs } from '../utils/astHelpers';

const TABS = [
  { key: 'truth', label: 'Tabela prawdy' },
  { key: 'qm', label: 'Quine-McCluskey' },
  { key: 'kmap', label: 'K-Map' },
  { key: 'simplify_dnf', label: 'Prawa logiczne' },
];


/* -------------------------------- Component -------------------------------- */
export default function ResultScreen({ input, onBack, saveToHistory, onExportToPrint, onShowDefinitions }) {
  const [tab, setTab] = useState('truth');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [data, setData] = useState(null);
  const [toast, setToast] = useState({ message: '', type: 'success' });
  const [slideStep, setSlideStep] = useState(0);
  const [highlightExpr, setHighlightExpr] = useState(null);
  const [showTruthTableLegend, setShowTruthTableLegend] = useState(false);
  const [showDnfLegend, setShowDnfLegend] = useState(false);
  const [showCnfLegend, setShowCnfLegend] = useState(false);
  const tableScrollRef = useRef(null);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(false);

  const resetHighlighting = () => {
    setHighlightExpr(null);
    setSlideStep(0);
  };

  useEffect(() => {
    resetHighlighting();
  }, [input]);

  // Auto-scroll table to the right when step changes (to show new column)
  // Scroll first, then check position to update arrow buttons
  useEffect(() => {
    if (tableScrollRef.current && tab === 'truth') {
      const container = tableScrollRef.current;
      let checkTimeout;
      
      // First, scroll to maximum right to show the newest column
      const scrollTimeout = setTimeout(() => {
        container.scrollLeft = container.scrollWidth;
        
        // After scrolling, wait a bit and then check position to update arrow buttons
        checkTimeout = setTimeout(() => {
          if (tableScrollRef.current) {
            const container = tableScrollRef.current;
            setCanScrollLeft(container.scrollLeft > 0);
            setCanScrollRight(container.scrollLeft < container.scrollWidth - container.clientWidth - 1);
          }
        }, 50);
      }, 100);
      
      return () => {
        clearTimeout(scrollTimeout);
        if (checkTimeout) clearTimeout(checkTimeout);
      };
    }
  }, [slideStep, tab]);

  // Check scroll position and update arrow buttons (for manual scrolling)
  useEffect(() => {
    const checkScrollPosition = () => {
      if (tableScrollRef.current && tab === 'truth') {
        const container = tableScrollRef.current;
        setCanScrollLeft(container.scrollLeft > 0);
        setCanScrollRight(container.scrollLeft < container.scrollWidth - container.clientWidth - 1);
      }
    };

    const container = tableScrollRef.current;
    if (container) {
      container.addEventListener('scroll', checkScrollPosition);
      // Check initially with delay to let auto-scroll finish first
      const timeoutId = setTimeout(checkScrollPosition, 200);
      const timeoutId2 = setTimeout(checkScrollPosition, 400);
      
      window.addEventListener('resize', checkScrollPosition);

      return () => {
        clearTimeout(timeoutId);
        clearTimeout(timeoutId2);
        container.removeEventListener('scroll', checkScrollPosition);
        window.removeEventListener('resize', checkScrollPosition);
      };
    }
  }, [slideStep, data, tab]);

  const scrollTableLeft = () => {
    if (tableScrollRef.current) {
      const container = tableScrollRef.current;
      // Scroll by larger amount to reveal more columns
      container.scrollBy({ left: -300, behavior: 'smooth' });
    }
  };

  const scrollTableRight = () => {
    if (tableScrollRef.current) {
      const container = tableScrollRef.current;
      // Scroll by larger amount to reveal more columns
      container.scrollBy({ left: 300, behavior: 'smooth' });
    }
  };

  /* Fetch full analysis from backend API */
  useEffect(() => {
    const apiUrl = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000';

    const fetchData = async () => {
      setLoading(true);
      setError('');
      setToast({ message: '', type: 'success' });

      try {
        if (apiUrl) {
          // Quick probe (also gives standardized form)
          let probe;
          try {
            const probeRes = await fetch(`${apiUrl}/standardize`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ expr: input }),
            });
            if (!probeRes.ok) {
              // Try to get error details from response
              let errorMessage = `HTTP ${probeRes.status}`;
              try {
                const errorData = await probeRes.json();
                if (errorData.detail) {
                  errorMessage = errorData.detail;
                }
              } catch (parseError) {
                // If we can't parse error response, use status code
              }
              throw new Error(errorMessage);
            }
            probe = await probeRes.json();
          } catch (e) {
            setError(`Błąd walidacji: ${e.message}`);
            setLoading(false);
            setToast({ message: `Błąd: ${e.message}`, type: 'error' });
            return;
          }

          // Parallel calls with shorter timeout
          const fetchWithTimeout = (url, options, timeout = 5000) =>
            Promise.race([
              fetch(url, options),
              new Promise((_, reject) => setTimeout(() => reject(new Error('Timeout')), timeout)),
            ]);

          // Split into two batches to reduce server load
          const [astRes, onpRes, truthRes, tautRes, contrRes] = await Promise.allSettled([
            fetchWithTimeout(`${apiUrl}/ast`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ expr: input }),
            }).then(r => r.json()),
            fetchWithTimeout(`${apiUrl}/onp`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ expr: input }),
            }).then(r => r.json()),
            fetchWithTimeout(`${apiUrl}/truth_table`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ expr: input }),
            }).then(r => r.json()),
            fetchWithTimeout(`${apiUrl}/tautology`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ expr: input }),
            }).then(r => r.json()),
            fetchWithTimeout(`${apiUrl}/contradiction`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ expr: input }),
            }).then(r => r.json()),
          ]);

          // Second batch - more complex operations
          const [kmapRes, qmRes, minimalFormsRes] = await Promise.allSettled([
            fetchWithTimeout(`${apiUrl}/kmap`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ expr: input }),
            }).then(async r => {
              if (!r.ok) {
                const errorData = await r.json();
                throw new Error(errorData.detail || `HTTP ${r.status}`);
              }
              return r.json();
            }),
            fetchWithTimeout(`${apiUrl}/qm`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ expr: input }),
            }).then(async r => {
              if (!r.ok) {
                const errorData = await r.json();
                throw new Error(errorData.detail || `HTTP ${r.status}`);
              }
              return r.json();
            }),
            fetchWithTimeout(`${apiUrl}/minimal_forms`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ expr: input }),
            }).then(async r => {
              if (!r.ok) {
                const errorData = await r.json();
                throw new Error(errorData.detail || `HTTP ${r.status}`);
              }
              return r.json();
            }),
          ]);

          // Helper function to extract data from Promise.allSettled results
          const getResult = (result) => {
            if (result.status === 'fulfilled') {
              return { data: result.value, error: null };
            } else {
              // Extract error message from rejected promise
              let errorMessage = 'Nieznany błąd';
              if (result.reason && result.reason.message) {
                errorMessage = result.reason.message;
              } else if (result.reason && typeof result.reason === 'string') {
                errorMessage = result.reason;
              }
              return { data: null, error: errorMessage };
            }
          };
          
          const astResult = getResult(astRes);
          const onpResult = getResult(onpRes);
          const truthResult = getResult(truthRes);
          const tautResult = getResult(tautRes);
          const contrResult = getResult(contrRes);
          const kmapResult = getResult(kmapRes);
          const qmResult = getResult(qmRes);
          const minimalFormsResult = getResult(minimalFormsRes);

          const res = {
            expression: input,
            standardized: probe.standardized,
            ast: astResult.data?.ast || null,
            ast_error: astResult.error,
            onp: onpResult.data?.onp || null,
            onp_error: onpResult.error,
            truth_table: truthResult.data?.truth_table || null,
            truth_error: truthResult.error,
            kmap: kmapResult.data || null,
            kmap_error: kmapResult.error,
            kmap_simplification: kmapResult.data || null,
            qm: qmResult.data || null,
            qm_error: qmResult.error,
            is_tautology: tautResult.data?.is_tautology || false,
            taut_error: tautResult.error,
            is_contradiction: contrResult.data?.is_contradiction || false,
            contr_error: contrResult.error,
            minimal_forms: minimalFormsResult.data || null,
            minimal_forms_error: minimalFormsResult.error,
          };

          setData(res);
          setLoading(false);
          setToast({ message: 'Analiza wyrażenia zakończona!', type: 'success' });
          
          // Zapisz do historii (bez duplikatów)
          if (saveToHistory) {
            saveToHistory(input, res);
          }
          return;
        }

        // This should not happen as we set default API URL
        setError('Brak skonfigurowanego URL API');
        setLoading(false);
        setToast({ message: 'Brak skonfigurowanego URL API', type: 'error' });
      } catch (e) {
        setError(e.message || 'Błąd API');
        setLoading(false);
        setToast({ message: `Błąd: ${e.message}`, type: 'error' });
      }
    };

    fetchData();
  }, [input, saveToHistory]);

  if (loading) return <div className="text-center p-8">Ładowanie...</div>;
  if (error) return <div className="text-red-600 text-center p-8">{error}</div>;
  if (!data) return null;

  const kmapData = data.kmap_simplification || data.kmap || {};
  const truthVars = data.truth_table && data.truth_table.length
    ? Object.keys(data.truth_table[0]).filter(k => k !== 'result')
    : [];

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gradient-to-br from-blue-50 to-white p-4">
      <Toast
        message={toast.message}
        type={toast.type}
        onClose={() => setToast({ message: '', type: 'success' })}
      />

      <div className="max-w-5xl w-full bg-white rounded-3xl shadow-2xl p-4 border border-blue-100 animate-fade-in mx-auto">
          <button className="mb-6 text-blue-600 hover:underline text-lg font-semibold" onClick={onBack}>
            &larr; Wróć
          </button>

          <h1 className="text-3xl font-extrabold mb-6 text-center text-blue-700 tracking-tight drop-shadow">
            Wynik analizy
          </h1>

          {/* Summary cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div className="bg-blue-50 rounded-xl p-4 border border-blue-100">
              <div className="text-xs text-blue-700 font-semibold uppercase">Wpisane wyrażenie</div>
              <div className="font-mono text-lg break-all">{data.expression}</div>
            </div>

            <div className="bg-green-50 rounded-xl p-4 border border-green-100">
              <div className="text-xs text-green-700 font-semibold uppercase">Pokrycie prawdy</div>
              {data.truth_table && data.truth_table.length > 0 ? (
                <div className="font-mono text-lg break-all">
                  {Math.round((data.truth_table.filter(row => row.result === 1).length / data.truth_table.length) * 100)}% ({data.truth_table.filter(row => row.result === 1).length} z {data.truth_table.length})
                </div>
              ) : (
                <span className="text-gray-400">Brak danych</span>
              )}
            </div>

            <div className="bg-yellow-50 rounded-xl p-4 border border-yellow-100">
              <div className="text-xs text-yellow-700 font-semibold uppercase">ONP</div>
              <div className="font-mono text-lg break-all">
                {data.onp || <span className="text-gray-400">Brak</span>}
              </div>
            </div>

            {/* Dwie osobne komórki obok siebie */}
            <div className="flex gap-4">
              {/* Lewa komórka - Tautologia */}
              <div className="bg-purple-50 rounded-xl p-4 border border-purple-100 flex-1">
                <div className="text-xs text-purple-700 font-semibold uppercase">Tautologia?</div>
                <div className="font-mono text-lg">
                  {data.is_tautology === true ? (
                    <span className="text-green-700 font-bold">TAK</span>
                  ) : data.is_tautology === false ? (
                    <span className="text-red-700 font-bold">NIE</span>
                  ) : (
                    <span className="text-gray-400">Brak</span>
                  )}
                </div>
              </div>
              
              {/* Prawa komórka - Sprzeczność */}
              <div className="bg-purple-50 rounded-xl p-4 border border-purple-100 flex-1">
                <div className="text-xs text-purple-700 font-semibold uppercase">Sprzeczność?</div>
                <div className="font-mono text-lg">
                  {data.is_contradiction === true ? (
                    <span className="text-red-700 font-bold">TAK</span>
                  ) : data.is_contradiction === false ? (
                    <span className="text-green-700 font-bold">NIE</span>
                  ) : (
                    <span className="text-gray-400">Brak</span>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* DNF/CNF Row */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            {/* DNF Card */}
            <div className="bg-blue-50 rounded-xl p-4 border border-blue-100 relative">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2">
                  <div className="text-xs text-blue-700 font-semibold uppercase">DNF (Suma iloczynów)</div>
                  <div className="relative">
                    <button
                      type="button"
                      onMouseEnter={() => setShowDnfLegend(true)}
                      onMouseLeave={() => setShowDnfLegend(false)}
                      className="w-5 h-5 rounded-full bg-blue-100 text-blue-700 text-xs flex items-center justify-center border border-blue-300 hover:bg-blue-200 transition-colors"
                      aria-label="Wyjaśnienie DNF"
                      title="Wyjaśnienie DNF"
                    >
                      ?
                    </button>
                    {showDnfLegend && (
                      <div className="absolute z-50 w-80 p-3 mt-2 bg-gray-900 text-white text-sm rounded-lg shadow-lg border border-gray-700 transform -translate-x-1/2 left-1/2">
                        <div className="font-semibold text-blue-300 mb-1">DNF (Disjunctive Normal Form)</div>
                        <div className="text-gray-200">
                          <strong>Metoda:</strong> Quine-McCluskey + Petrick<br/>
                          <strong>Opis:</strong> Suma iloczynów literałów (mintermy). Każdy minterm reprezentuje jeden wiersz tabeli prawdy z wynikiem 1.<br/>
                          <strong>Przykład:</strong> (A∧B) ∨ (¬A∧C) ∨ (B∧¬C)
                        </div>
                        <div className="absolute -top-1 left-1/2 transform -translate-x-1/2 w-2 h-2 bg-gray-900 rotate-45 border-l border-t border-gray-700"></div>
                      </div>
                    )}
                  </div>
                </div>
                {/* Statystyki w górnym prawym rogu */}
                <div className="text-xs">
                  <div className="bg-gray-100 px-2 py-1 rounded">
                    <span className="text-gray-500">Terminy:</span> <span className="font-bold text-blue-600">{data.minimal_forms?.dnf?.terms || 0}</span> | 
                    <span className="text-gray-500"> Literały:</span> <span className="font-bold text-blue-600">{data.minimal_forms?.dnf?.literals || 0}</span>
                  </div>
                </div>
              </div>
              <div className="font-mono text-lg break-all">
                {data.minimal_forms?.dnf?.expr || <span className="text-gray-400">Brak</span>}
              </div>
            </div>

            {/* CNF Card */}
            <div className="bg-green-50 rounded-xl p-4 border border-green-100 relative">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2">
                  <div className="text-xs text-green-700 font-semibold uppercase">CNF (Iloczyn sum)</div>
                  <div className="relative">
                    <button
                      type="button"
                      onMouseEnter={() => setShowCnfLegend(true)}
                      onMouseLeave={() => setShowCnfLegend(false)}
                      className="w-5 h-5 rounded-full bg-green-100 text-green-700 text-xs flex items-center justify-center border border-green-300 hover:bg-green-200 transition-colors"
                      aria-label="Wyjaśnienie CNF"
                      title="Wyjaśnienie CNF"
                    >
                      ?
                    </button>
                    {showCnfLegend && (
                      <div className="absolute z-50 w-80 p-3 mt-2 bg-gray-900 text-white text-sm rounded-lg shadow-lg border border-gray-700 transform -translate-x-1/2 left-1/2">
                        <div className="font-semibold text-green-300 mb-1">CNF (Conjunctive Normal Form)</div>
                        <div className="text-gray-200">
                          <strong>Metoda:</strong> Duality via Quine-McCluskey + Petrick<br/>
                          <strong>Opis:</strong> Iloczyn sum literałów (maxtermy). Każdy maxterm reprezentuje jeden wiersz tabeli prawdy z wynikiem 0.<br/>
                          <strong>Przykład:</strong> (A∨B) ∧ (¬A∨C) ∧ (B∨¬C)
                        </div>
                        <div className="absolute -top-1 left-1/2 transform -translate-x-1/2 w-2 h-2 bg-gray-900 rotate-45 border-l border-t border-gray-700"></div>
                      </div>
                    )}
                  </div>
                </div>
                {/* Statystyki w górnym prawym rogu */}
                <div className="text-xs">
                  <div className="bg-gray-100 px-2 py-1 rounded">
                    <span className="text-gray-500">Terminy:</span> <span className="font-bold text-green-600">{data.minimal_forms?.cnf?.terms || 0}</span> | 
                    <span className="text-gray-500"> Literały:</span> <span className="font-bold text-green-600">{data.minimal_forms?.cnf?.literals || 0}</span>
                  </div>
                </div>
              </div>
              <div className="font-mono text-lg break-all">
                {data.minimal_forms?.cnf?.expr || <span className="text-gray-400">Brak</span>}
              </div>
            </div>
          </div>

          {/* AST always visible below summary cards */}
          {data?.ast && (
            <div className="mt-4 mb-4 p-6 bg-white rounded-2xl shadow-lg border border-gray-100">
              <h3 className="text-xl font-bold text-gray-800 mb-4">Drzewo składniowe (AST)</h3>
              <ASTDisplay ast={data.ast} highlightExpr={highlightExpr} />
            </div>
          )}

        {/* Tabs */}
        <div className="mb-4">
          <div className="flex gap-2 mb-4 justify-center">
            {TABS.map(t => (
              <button
                key={t.key}
                className={`px-6 py-2 rounded-full font-semibold text-lg shadow-sm transition-all border-2 ${
                  tab === t.key
                    ? 'bg-blue-600 text-white border-blue-600 scale-105'
                    : 'bg-gray-100 text-blue-700 border-blue-200 hover:bg-blue-100'
                }`}
                onClick={() => {
                  setTab(t.key);
                  resetHighlighting();
                }}
              >
                {t.label}
              </button>
            ))}
          </div>

          <div className="bg-gray-50 p-6 rounded-2xl shadow-inner min-h-[180px] transition-all">
            {/* Truth table with binary index and highlighting of 1s */}
            {tab === 'truth' && (
              <div className="overflow-x-auto">
                {data.truth_table && data.truth_table.length > 0 ? (
                  <>
                    <div className="flex items-center gap-2 mb-4">
                      <h3 className="text-xl font-bold text-gray-800">Tabela prawdy</h3>
                      <button
                        className="w-6 h-6 rounded-full bg-blue-100 hover:bg-blue-200 text-blue-700 flex items-center justify-center text-sm font-bold"
                        onClick={() => setShowTruthTableLegend(!showTruthTableLegend)}
                        title="Wyjaśnienie tabeli prawdy"
                      >
                        ?
                      </button>
                    </div>
                    {showTruthTableLegend && (
                      <div className="bg-blue-50 border-l-4 border-blue-500 p-4 mb-4 rounded">
                        <button
                          className="float-right text-blue-700 hover:text-blue-900 text-xl font-bold"
                          onClick={() => setShowTruthTableLegend(false)}
                        >
                          ✕
                        </button>
                        <h4 className="font-bold text-blue-900 mb-2">Wyjaśnienie tabeli prawdy:</h4>
                        <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
                          <li><strong>Wiersze z wynikiem 1</strong> (podświetlone na zielono) to <strong>mintermy</strong> - kombinacje zmiennych, dla których wyrażenie jest prawdziwe</li>
                          <li><strong>Kroki obliczeń (slajdy):</strong> Prezentacja krok po kroku, jak wygląda obliczenie każdego podwyrażenia</li>
                          <li><strong>Podświetlona kolumna (żółta):</strong> Aktualnie obliczany krok w drzewie AST</li>
                          <li><strong>Niebieskie kolumny:</strong> Argumenty potrzebne do obliczenia aktualnego kroku</li>
                          <li>Przyciski "Wstecz" i "Dalej" pozwalają przejść przez wszystkie kroki obliczeń</li>
                        </ul>
                      </div>
                    )}
                    <table className="min-w-full border border-gray-300 rounded">
                      <thead>
                        <tr>
                          {truthVars.map(v => (
                            <th key={v} className="px-3 py-1 border-b bg-gray-100 text-gray-700">
                              {v}
                            </th>
                          ))}
                          <th className="px-3 py-1 border-b bg-gray-100 text-gray-700">Wynik</th>
                        </tr>
                      </thead>
                      <tbody>
                        {data.truth_table.map((row, i) => {
                          const isOne = row.result === 1;
                          return (
                            <tr key={i} className={isOne ? 'bg-green-100' : ''}>
                              {truthVars.map(v => (
                                <td key={v} className="px-3 py-1 border-b text-center">
                                  {row[v]}
                                </td>
                              ))}
                              <td
                                className={`px-3 py-1 border-b text-center font-semibold ${
                                  isOne ? 'text-green-800' : 'text-gray-700'
                                }`}
                              >
                                {row.result}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>

                    {/* Slide-by-slide derivation table */}
                    <div className="mt-8">
                      <h3 className="font-semibold text-blue-700 mb-2 text-lg">Kroki obliczeń (slajdy):</h3>
                      {data.ast && data.truth_table && data.truth_table.length > 0 ? (
                        (() => {
                          const steps = getAstStepsNoVars(data.ast);
                          const allColNodes = [
                            ...truthVars.map(v => ({ expr: v, node: v })),
                            ...steps,
                          ];
                          const allColValues = allColNodes.map(col =>
                            typeof col.node === 'string'
                              ? data.truth_table.map(row => row[col.node])
                              : data.truth_table.map(row => evalAst(col.node, row))
                          );

                          const shownColNames = [
                            ...truthVars,
                            ...steps.slice(0, Math.min(slideStep + 1, steps.length)).map(s => s.expr),
                          ];
                          const shownColValues = allColValues.slice(0, truthVars.length + Math.min(slideStep + 1, steps.length));
                          const currentStep = steps[slideStep] || null;
                          const argNames = currentStep ? getStepArgs(currentStep) : [];

                          return (
                            <div>
                              <div className="flex gap-2 mb-2 items-center">
                                <button
                                  className="px-3 py-1 rounded bg-blue-100 text-blue-700 font-bold disabled:opacity-50"
                                  onClick={() => setSlideStep(s => Math.max(0, s - 1))}
                                  disabled={slideStep === 0}
                                >
                                  Wstecz
                                </button>
                                <span className="text-sm">
                                  Krok {steps.length ? Math.min(slideStep + 1, steps.length) : 0} z {steps.length}
                                </span>
                                <button
                                  className="px-3 py-1 rounded bg-blue-100 text-blue-700 font-bold disabled:opacity-50"
                                  onClick={() => setSlideStep(s => Math.min(steps.length - 1, s + 1))}
                                  disabled={steps.length === 0 || slideStep === steps.length - 1}
                                >
                                  Dalej
                                </button>
                              </div>

                              {/* Table container */}
                              <div className="relative">
                                <div ref={tableScrollRef} className="scrollable-steps-table">
                                  <table className="min-w-full border border-blue-200 rounded-xl text-sm">
                                  <thead>
                                    <tr>
                                      {shownColNames.map((name, idx) => {
                                        const isCurrent = idx === shownColNames.length - 1 && steps.length > 0;
                                        const isArg = argNames.includes(name);
                                        const headerCls = isCurrent
                                          ? 'bg-yellow-100 font-bold'
                                          : isArg
                                          ? 'bg-blue-100 font-bold'
                                          : 'bg-blue-50';
                                        return (
                                          <th key={name} className={`px-3 py-2 border-b text-blue-900 ${headerCls}`}>
                                            <div className="truncate max-w-xs font-mono text-xs" title={name}>
                                              {name}
                                            </div>
                                          </th>
                                        );
                                      })}
                                    </tr>
                                  </thead>
                                  <tbody>
                                    {data.truth_table.map((row, i) => (
                                      <tr key={i}>
                                        {shownColValues.map((vals, idx) => {
                                          const isCurrent = idx === shownColNames.length - 1 && steps.length > 0;
                                          const isArg = argNames.includes(shownColNames[idx]);
                                          return (
                                            <td
                                              key={idx}
                                              className={`px-3 py-2 border-b text-center whitespace-nowrap ${
                                                isCurrent ? 'bg-yellow-50 font-bold' : isArg ? 'bg-blue-50 font-bold' : ''
                                              }`}
                                            >
                                              {vals[i]}
                                            </td>
                                          );
                                        })}
                                      </tr>
                                    ))}
                                  </tbody>
                                </table>
                                </div>
                              </div>
                              
                              {/* Scroll arrows below table */}
                              {(canScrollLeft || canScrollRight) && (
                                <div className="flex justify-center gap-4 mt-3">
                                  <button
                                    onClick={scrollTableLeft}
                                    disabled={!canScrollLeft}
                                    className={`rounded-full w-8 h-8 flex items-center justify-center transition-all shadow-sm border ${
                                      canScrollLeft
                                        ? 'bg-gray-100 hover:bg-gray-200 text-gray-600 hover:text-gray-800 border-gray-300 cursor-pointer'
                                        : 'bg-gray-50 text-gray-300 border-gray-200 cursor-not-allowed opacity-50'
                                    }`}
                                    aria-label="Przewiń w lewo"
                                    title="Przewiń w lewo"
                                  >
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                                    </svg>
                                  </button>
                                  
                                  <button
                                    onClick={scrollTableRight}
                                    disabled={!canScrollRight}
                                    className={`rounded-full w-8 h-8 flex items-center justify-center transition-all shadow-sm border ${
                                      canScrollRight
                                        ? 'bg-gray-100 hover:bg-gray-200 text-gray-600 hover:text-gray-800 border-gray-300 cursor-pointer'
                                        : 'bg-gray-50 text-gray-300 border-gray-200 cursor-not-allowed opacity-50'
                                    }`}
                                    aria-label="Przewiń w prawo"
                                    title="Przewiń w prawo"
                                  >
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                    </svg>
                                  </button>
                                </div>
                              )}
                              
                              <div className="mt-2 text-xs text-gray-500">
                                Podświetlona kolumna to aktualnie obliczany krok. Kolumny niebieskie to argumenty tego kroku.
                              </div>
                            </div>
                          );
                        })()
                      ) : (
                        <div className="text-gray-400 italic">(Brak danych AST lub tabeli prawdy)</div>
                      )}
                    </div>
                  </>
                ) : (
                  <div className="text-gray-500">Brak danych do wyświetlenia tabeli prawdy.</div>
                )}
              </div>
            )}

            {tab === 'qm' && (
              <div>
                <QMSteps steps={data.qm?.steps} error={data.qm_error} />
              </div>
            )}

            {tab === 'kmap' && (
              <KMapDisplay
                kmap={kmapData.kmap}
                groups={kmapData.groups}
                all_groups={kmapData.all_groups}
                result={kmapData.result}
                vars={kmapData.vars}
                minterms={kmapData.minterms}
                error={data.kmap_error}
              />
            )}

            {tab === 'simplify_dnf' && (
              <SimplifyDNF expression={input} loading={loading} />
            )}
          </div>


          {/* Logic Gates always visible below AST */}
          {/* Logic gates display - temporarily hidden */}
          {/* {data?.ast && (
            <div className="mt-8 p-6 bg-white rounded-2xl shadow-lg border border-gray-100">
              <h3 className="text-xl font-bold text-gray-800 mb-4">Bramki logiczne</h3>
              <LogicGatesDisplay ast={data.ast} expression={data.expression} highlightExpr={highlightExpr} />
            </div>
          )} */}

        </div>

        <ExportResults data={data} input={input} onExportToPrint={onExportToPrint} />
      </div>
    </div>
  );
}
