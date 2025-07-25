import React, { useState, useEffect } from 'react';
import QMSteps from './QMSteps';
import KMapDisplay from './KMapDisplay';
import ASTDisplay from './ASTDisplay';
import Toast from './Toast';
import ExportResults from './ExportResults';
import { analyze } from '../__mocks__/api';

const TABS = [
  { key: 'truth', label: 'Tabela prawdy' },
  { key: 'qm', label: 'Quine-McCluskey' },
  { key: 'kmap', label: 'K-Map' },
  { key: 'ast', label: 'AST' },
];

function getAstStepsNoVars(ast, variables) {
  const steps = [];
  const seen = new Set();
  function traverse(node) {
    if (!node) return;
    if (typeof node === 'string') {
      return;
    }
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

function getAstExpr(node) {
  if (!node) return '?';
  if (typeof node === 'string') return node;
  if (node.node === '¬') return `¬(${getAstExpr(node.child)})`;
  if (['∧', '∨', '→', '↔'].includes(node.node))
    return `(${getAstExpr(node.left)} ${node.node} ${getAstExpr(node.right)})`;
  return '?';
}

function computeStepValues(step, truthTable, variables) {
  return truthTable.map(row => evalAst(step.node, row));
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

function getStepArgs(step) {
  if (!step || !step.node) return [];
  if (step.node.node === '¬') return [getAstExpr(step.node.child)];
  if (['∧', '∨', '→', '↔'].includes(step.node.node))
    return [getAstExpr(step.node.left), getAstExpr(step.node.right)];
  return [];
}

function ResultScreen({ input, onBack }) {
  const [tab, setTab] = useState('truth');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [data, setData] = useState(null);
  const [toast, setToast] = useState({ message: '', type: 'success' });
  const [selectedRow, setSelectedRow] = useState(null);
  const [slideStep, setSlideStep] = useState(0);

  useEffect(() => {
    setLoading(true);
    setError('');
    setToast({ message: '', type: 'success' });
    const apiUrl = process.env.REACT_APP_API_URL;
    const fetchData = async () => {
      try {
        let res;
        if (apiUrl) {
          const [stdRes, astRes, onpRes, truthRes, kmapRes, qmRes, tautRes] = await Promise.all([
            fetch(`${apiUrl}/standardize`, {
              method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ expr: input })
            }).then(r => r.json()),
            fetch(`${apiUrl}/ast`, {
              method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ expr: input })
            }).then(r => r.json()),
            fetch(`${apiUrl}/onp`, {
              method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ expr: input })
            }).then(r => r.json()),
            fetch(`${apiUrl}/truth_table`, {
              method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ expr: input })
            }).then(r => r.json()),
            fetch(`${apiUrl}/kmap`, {
              method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ expr: input })
            }).then(r => r.json()),
            fetch(`${apiUrl}/qm`, {
              method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ expr: input })
            }).then(r => r.json()),
            fetch(`${apiUrl}/tautology`, {
              method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ expr: input })
            }).then(r => r.json()),
          ]);
          res = {
            expression: input,
            standardized: stdRes.standardized,
            ast: astRes.ast,
            onp: onpRes.onp,
            truth_table: truthRes.truth_table,
            kmap: kmapRes,
            qm: qmRes,
            is_tautology: tautRes.is_tautology
          };
        } else {
          res = await analyze(input);
        }
        setData(res);
        setLoading(false);
        setToast({ message: 'Expression analyzed successfully!', type: 'success' });
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

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gradient-to-br from-blue-50 to-white p-4">
      <Toast message={toast.message} type={toast.type} onClose={() => setToast({ message: '', type: 'success' })} />
      <div className="max-w-4xl w-full bg-white rounded-3xl shadow-2xl p-4 border border-blue-100 animate-fade-in">
        <button className="mb-6 text-blue-600 hover:underline text-lg font-semibold" onClick={onBack}>&larr; Wróć</button>
        <h1 className="text-3xl font-extrabold mb-6 text-center text-blue-700 tracking-tight drop-shadow">Wynik analizy</h1>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
          <div className="bg-blue-50 rounded-xl p-4 border border-blue-100 flex flex-col gap-2">
            <div className="text-xs text-blue-700 font-semibold uppercase">Wpisane wyrażenie</div>
            <div className="font-mono text-lg break-all">{data.expression}</div>
          </div>
          <div className="bg-green-50 rounded-xl p-4 border border-green-100 flex flex-col gap-2">
            <div className="text-xs text-green-700 font-semibold uppercase">Uproszczone (QM)</div>
            <div className="font-mono text-lg break-all">{data.qm?.result || <span className="text-gray-400">Brak</span>}</div>
          </div>
          <div className="bg-yellow-50 rounded-xl p-4 border border-yellow-100 flex flex-col gap-2">
            <div className="text-xs text-yellow-700 font-semibold uppercase">ONP</div>
            <div className="font-mono text-lg break-all">{data.onp || <span className="text-gray-400">Brak</span>}</div>
          </div>
          <div className="bg-purple-50 rounded-xl p-4 border border-purple-100 flex flex-col gap-2">
            <div className="text-xs text-purple-700 font-semibold uppercase">Tautologia?</div>
            <div className="font-mono text-lg">{data.is_tautology === true ? <span className="text-green-700 font-bold">TAK</span> : data.is_tautology === false ? <span className="text-red-700 font-bold">NIE</span> : <span className="text-gray-400">Brak</span>}</div>
          </div>
        </div>
        <div className="mb-8">
          <div className="text-xs text-blue-700 font-semibold uppercase mb-2">AST (Abstrakcyjne Drzewo Składniowe)</div>
          <div className="bg-white rounded-xl border border-blue-100 shadow p-2">
            <ASTDisplay ast={data.ast} />
          </div>
        </div>
        <div className="mb-8">
          <div className="flex gap-2 mb-4 justify-center">
            {TABS.map(t => (
              <button
                key={t.key}
                className={`px-6 py-2 rounded-full font-semibold text-lg shadow-sm transition-all border-2 ${tab === t.key ? 'bg-blue-600 text-white border-blue-600 scale-105' : 'bg-gray-100 text-blue-700 border-blue-200 hover:bg-blue-100'}`}
                onClick={() => setTab(t.key)}
              >
                {t.label}
              </button>
            ))}
          </div>
          <div className="bg-gray-50 p-6 rounded-2xl shadow-inner min-h-[180px] transition-all">
            {tab === 'truth' && (
              <div className="overflow-x-auto">
                {data.truth_table && data.truth_table.length > 0 ? (
                  <>
                  <table className="min-w-full border border-gray-300 rounded">
                    <thead>
                      <tr>
                        {Object.keys(data.truth_table[0]).map(col => (
                          <th key={col} className="px-3 py-1 border-b bg-gray-100 text-gray-700">{col}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {data.truth_table.map((row, i) => (
                        <tr key={i} className={selectedRow === i ? 'bg-blue-100 font-bold' : 'cursor-pointer hover:bg-blue-50'} onClick={() => setSelectedRow(i)}>
                          {Object.values(row).map((val, j) => (
                            <td key={j} className="px-3 py-1 border-b text-center">{val}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  <div className="mt-8">
                    <h3 className="font-semibold text-blue-700 mb-2 text-lg">Kroki obliczeń (slajdy):</h3>
                    {data.ast && data.truth_table && data.truth_table.length > 0 ? (
                      (() => {
                        const variables = Object.keys(data.truth_table[0]).filter(k => k !== 'result');
                        const steps = getAstStepsNoVars(data.ast, variables);
                        const allColNames = [...variables, ...steps.map(s => s.expr)];
                        const allColNodes = [...variables.map(v => ({ expr: v, node: v })), ...steps];
                        const allColValues = allColNodes.map(col =>
                          typeof col.node === 'string'
                            ? data.truth_table.map(row => row[col.node])
                            : computeStepValues(col, data.truth_table, variables)
                        );
                        const shownColNames = [...variables, ...steps.slice(0, slideStep+1).map(s => s.expr)];
                        const shownColValues = [...allColValues.slice(0, variables.length + slideStep + 1)];
                        const currentStep = steps[slideStep];
                        const argNames = getStepArgs(currentStep);
                        return (
                          <div>
                            <div className="flex gap-2 mb-2 items-center">
                              <button className="px-3 py-1 rounded bg-blue-100 text-blue-700 font-bold disabled:opacity-50" onClick={() => setSlideStep(s => Math.max(0, s-1))} disabled={slideStep === 0}>Wstecz</button>
                              <span className="text-sm">Krok {slideStep+1} z {steps.length}</span>
                              <button className="px-3 py-1 rounded bg-blue-100 text-blue-700 font-bold disabled:opacity-50" onClick={() => setSlideStep(s => Math.min(steps.length-1, s+1))} disabled={slideStep === steps.length-1}>Dalej</button>
                            </div>
                            <div className="overflow-x-auto">
                              <table className="min-w-full border border-blue-200 rounded-xl text-sm">
                                <thead>
                                  <tr>
                                    {shownColNames.map((name, idx) => {
                                      let highlight = '';
                                      if (idx === shownColNames.length-1) highlight = 'bg-yellow-100 font-bold';
                                      else if (argNames.includes(name)) highlight = 'bg-blue-100 font-bold';
                                      else highlight = 'bg-blue-50';
                                      return (
                                        <th key={name} className={`px-2 py-1 border-b text-blue-900 ${highlight}`}>{name}</th>
                                      );
                                    })}
                                  </tr>
                                </thead>
                                <tbody>
                                  {data.truth_table.map((row, i) => (
                                    <tr key={i}>
                                      {shownColValues.map((vals, idx) => (
                                        <td key={idx} className={`px-2 py-1 border-b text-center ${idx === shownColNames.length-1 ? 'bg-yellow-50 font-bold' : argNames.includes(shownColNames[idx]) ? 'bg-blue-50 font-bold' : ''}`}>{vals[i]}</td>
                                      ))}
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                            <div className="mt-2 text-xs text-gray-500">Podświetlona kolumna to aktualnie obliczany krok. Kolumny niebieskie to argumenty tego kroku.</div>
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
              <QMSteps steps={data.qm?.steps} />
            )}
            {tab === 'kmap' && (
              <KMapDisplay kmap={data.kmap?.kmap} groups={data.kmap?.groups} result={data.kmap?.result} />
            )}
            {tab === 'ast' && (
              <ASTDisplay ast={data.ast} />
            )}
          </div>
        </div>
        <ExportResults data={data} />
        <div className="mt-6">
          <h2 className="text-lg font-semibold mb-2">Przyszłe funkcje (placeholder)</h2>
          <div className="bg-gray-100 rounded p-2 text-sm text-gray-500">Tu pojawią się kolejne analizy, np. minimalizacja, ONP, K-map, QM, tautologie.</div>
        </div>
      </div>
    </div>
  );
}

export default ResultScreen; 