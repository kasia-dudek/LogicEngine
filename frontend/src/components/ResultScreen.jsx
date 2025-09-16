// ResultScreen.jsx
import React, { useState, useEffect } from 'react';
import QMSteps from './QMSteps';
import KMapDisplay from './KMapDisplay';
import ASTDisplay from './ASTDisplay';
import Toast from './Toast';
import ExportResults from './ExportResults';
import LawsPanel from './LawsPanel';
import MinimalForms from './MinimalForms'; // eslint-disable-line no-unused-vars
// Removed mock API import - using real backend API

const TABS = [
  { key: 'truth', label: 'Tabela prawdy' },
  { key: 'qm', label: 'Quine-McCluskey' },
  { key: 'kmap', label: 'K-Map' },
  { key: 'laws', label: 'Prawa logiczne' },
];

/* ---------- AST helpers (for slide-by-slide truth-table derivation) ---------- */
function getAstExpr(node) {
  if (!node) return '?';
  if (typeof node === 'string') return node;
  if (node.node === '¬') return `¬(${getAstExpr(node.child)})`;
  if (['∧', '∨', '→', '↔'].includes(node.node)) {
    return `(${getAstExpr(node.left)} ${node.node} ${getAstExpr(node.right)})`;
  }
  return '?';
}

function getAstStepsNoVars(ast) {
  const steps = [];
  const seen = new Set();

  function traverse(node) {
    if (!node || typeof node === 'string') return;

    if (node.node === '¬') {
      traverse(node.child);
      const expr = `¬(${getAstExpr(node.child)})`;
      if (!seen.has(expr)) {
        steps.push({ expr, node });
        seen.add(expr);
      }
    } else if (['∧', '∨', '→', '↔'].includes(node.node)) {
      traverse(node.left);
      traverse(node.right);
      const expr = `(${getAstExpr(node.left)} ${node.node} ${getAstExpr(node.right)})`;
      if (!seen.has(expr)) {
        steps.push({ expr, node });
        seen.add(expr);
      }
    }
  }

  traverse(ast);
  return steps;
}

function evalAst(node, row) {
  if (!node) return null;
  if (typeof node === 'string') return row[node];
  if (node.node === '¬') return Number(!evalAst(node.child, row));
  if (node.node === '∧') return evalAst(node.left, row) & evalAst(node.right, row);
  if (node.node === '∨') return evalAst(node.left, row) | evalAst(node.right, row);
  if (node.node === '→') return Number(!evalAst(node.left, row) | evalAst(node.right, row));
  if (node.node === '↔') return Number(evalAst(node.left, row) === evalAst(node.right, row));
  return null;
}

function computeStepValues(step, truthTable) {
  return truthTable.map(row => evalAst(step.node, row));
}

function getStepArgs(step) {
  if (!step || !step.node) return [];
  if (step.node.node === '¬') return [getAstExpr(step.node.child)];
  if (['∧', '∨', '→', '↔'].includes(step.node.node)) {
    return [getAstExpr(step.node.left), getAstExpr(step.node.right)];
  }
  return [];
}

/* -------------------------------- Component -------------------------------- */
export default function ResultScreen({ input, onBack, saveToHistory }) {
  const [tab, setTab] = useState('truth');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [data, setData] = useState(null);
  const [toast, setToast] = useState({ message: '', type: 'success' });
  const [slideStep, setSlideStep] = useState(0);
  const [currentExpr, setCurrentExpr] = useState(input);
  const [highlightExpr, setHighlightExpr] = useState(null);
  const [pickedLawStep, setPickedLawStep] = useState(null);

  const resetHighlighting = () => {
    setHighlightExpr(null);
    setPickedLawStep(null);
  };

  useEffect(() => {
    setCurrentExpr(input);
    resetHighlighting();
  }, [input]);

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
            if (!probeRes.ok) throw new Error(`HTTP ${probeRes.status}`);
            probe = await probeRes.json();
          } catch (e) {
            setError(`Backend connection failed: ${e.message}`);
            setLoading(false);
            setToast({ message: `Backend niedostępny: ${e.message}`, type: 'error' });
            return;
          }

          // Parallel calls with shorter timeout
          const fetchWithTimeout = (url, options, timeout = 5000) =>
            Promise.race([
              fetch(url, options),
              new Promise((_, reject) => setTimeout(() => reject(new Error('Timeout')), timeout)),
            ]);

          // Split into two batches to reduce server load
          const [astRes, onpRes, truthRes, tautRes] = await Promise.allSettled([
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
          ]);

          // Second batch - more complex operations
          const [kmapRes, qmRes, lawsRes] = await Promise.allSettled([
            fetchWithTimeout(`${apiUrl}/kmap`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ expr: input }),
            }).then(r => r.json()),
            fetchWithTimeout(`${apiUrl}/qm`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ expr: input }),
            }).then(r => r.json()),
            fetchWithTimeout(`${apiUrl}/laws`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ expr: input }),
            }).then(r => r.json()),
          ]);

          // Helper function to extract data from Promise.allSettled results
          const getResult = (result) => result.status === 'fulfilled' ? result.value : null;
          
          const res = {
            expression: input,
            standardized: probe.standardized,
            ast: getResult(astRes)?.ast || null,
            onp: getResult(onpRes)?.onp || null,
            truth_table: getResult(truthRes)?.truth_table || null,
            kmap: getResult(kmapRes) || null,
            kmap_simplification: getResult(kmapRes) || null,
            qm: getResult(qmRes) || null,
            is_tautology: getResult(tautRes)?.is_tautology || false,
            laws: getResult(lawsRes) || null,
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
        setError('No API URL configured');
        setLoading(false);
        setToast({ message: 'No API URL configured', type: 'error' });
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

  const kmapData = data.kmap_simplification || data.kmap || {};
  const truthVars = data.truth_table && data.truth_table.length
    ? Object.keys(data.truth_table[0]).filter(k => k !== 'result')
    : [];
  const nVars = truthVars.length;

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gradient-to-br from-blue-50 to-white p-4">
      <Toast
        message={toast.message}
        type={toast.type}
        onClose={() => setToast({ message: '', type: 'success' })}
      />

      <div className="max-w-4xl w-full bg-white rounded-3xl shadow-2xl p-4 border border-blue-100 animate-fade-in">
        <button className="mb-6 text-blue-600 hover:underline text-lg font-semibold" onClick={onBack}>
          &larr; Wróć
        </button>

        <h1 className="text-3xl font-extrabold mb-6 text-center text-blue-700 tracking-tight drop-shadow">
          Wynik analizy
        </h1>

        {/* Summary cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
          <div className="bg-blue-50 rounded-xl p-4 border border-blue-100">
            <div className="text-xs text-blue-700 font-semibold uppercase">Wpisane wyrażenie</div>
            <div className="font-mono text-lg break-all">{data.expression}</div>
          </div>

          <div className="bg-green-50 rounded-xl p-4 border border-green-100">
            <div className="text-xs text-green-700 font-semibold uppercase">Uproszczone (QM)</div>
            <div className="font-mono text-lg break-all">
              {data.qm?.result || <span className="text-gray-400">Brak</span>}
            </div>
          </div>

          <div className="bg-yellow-50 rounded-xl p-4 border border-yellow-100">
            <div className="text-xs text-yellow-700 font-semibold uppercase">ONP</div>
            <div className="font-mono text-lg break-all">
              {data.onp || <span className="text-gray-400">Brak</span>}
            </div>
          </div>

          <div className="bg-purple-50 rounded-xl p-4 border border-purple-100">
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
        </div>

        {/* Tabs */}
        <div className="mb-8">
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
                            <tr key={i} className={isOne ? 'bg-green-50' : ''}>
                              {truthVars.map(v => (
                                <td key={v} className="px-3 py-1 border-b text-center">
                                  {row[v]}
                                </td>
                              ))}
                              <td
                                className={`px-3 py-1 border-b text-center font-semibold ${
                                  isOne ? 'text-green-700' : 'text-gray-700'
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
                          const allColNames = [...truthVars, ...steps.map(s => s.expr)];
                          const allColNodes = [
                            ...truthVars.map(v => ({ expr: v, node: v })),
                            ...steps,
                          ];
                          const allColValues = allColNodes.map(col =>
                            typeof col.node === 'string'
                              ? data.truth_table.map(row => row[col.node])
                              : computeStepValues(col, data.truth_table)
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

                              <div className="overflow-x-auto">
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
                                          <th key={name} className={`px-2 py-1 border-b text-blue-900 ${headerCls}`}>
                                            {name}
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
                                              className={`px-2 py-1 border-b text-center ${
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

            {tab === 'qm' && <QMSteps steps={data.qm?.steps} />}

            {tab === 'kmap' && (
              <KMapDisplay
                kmap={kmapData.kmap}
                groups={kmapData.groups}
                all_groups={kmapData.all_groups}
                result={kmapData.result}
                vars={kmapData.vars}
                minterms={kmapData.minterms}
              />
            )}

            {tab === 'laws' && (
              <LawsPanel
                data={data}
                onPickStep={(index) => {
                  setPickedLawStep(index);
                  if (data?.laws?.steps?.[index]) {
                    const step = data.laws.steps[index];
                    setHighlightExpr(step.before_subexpr);
                  }
                }}
                onApplyLaw={(newLawsData) => {
                  setData(prev => ({ ...prev, laws: newLawsData }));
                  setToast({ message: 'Zastosowano alternatywne prawo - kroki zaktualizowane', type: 'success' });
                }}
                pickedIndex={pickedLawStep}
              />
            )}
          </div>

          {/* AST always visible below */}
          {data?.ast && (
            <div className="mt-8 p-6 bg-white rounded-2xl shadow-lg border border-gray-100">
              <h3 className="text-xl font-bold text-gray-800 mb-4">Drzewo składniowe (AST)</h3>
              <ASTDisplay ast={data.ast} highlightExpr={highlightExpr} />
            </div>
          )}

          {/* Minimal forms (DNF/CNF/ANF/NAND/NOR/AND/OR) - temporarily disabled */}
          <div className="mt-8">
            <div className="text-center text-gray-500 p-4 bg-gray-50 rounded">
              Formy minimalne tymczasowo wyłączone
            </div>
          </div>
        </div>

        <ExportResults data={data} />
      </div>
    </div>
  );
}
