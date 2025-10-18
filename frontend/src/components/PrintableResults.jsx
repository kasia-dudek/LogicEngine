// PrintableResults.jsx
import React, { useEffect } from 'react';
import QMSteps from './QMSteps';
import KMapDisplay from './KMapDisplay';
import ASTDisplay from './ASTDisplay';
import LogicGatesDisplay from './LogicGatesDisplay';

/* ---------- AST helpers (reused from ResultScreen) ---------- */
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
  if (typeof node === 'string') {
    if (node === '0') return 0;
    if (node === '1') return 1;
    return row[node] || 0;
  }
  if (node.node === '¬') return 1 - evalAst(node.child, row);
  if (node.node === '∧') return evalAst(node.left, row) && evalAst(node.right, row);
  if (node.node === '∨') return evalAst(node.left, row) || evalAst(node.right, row);
  if (node.node === '→') return (1 - evalAst(node.left, row)) || evalAst(node.right, row);
  if (node.node === '↔') return evalAst(node.left, row) === evalAst(node.right, row);
  return null;
}

function computeStepValues(ast, truthTable) {
  const steps = getAstStepsNoVars(ast);
  return steps.map(step => ({
    ...step,
    values: truthTable.map(row => evalAst(step.node, row))
  }));
}

function getStepArgs(step) {
  if (!step.node) return [];
  if (typeof step.node === 'string') return [step.node];
  if (step.node.node === '¬') return getStepArgs({ node: step.node.child });
  if (['∧', '∨', '→', '↔'].includes(step.node.node)) {
    return [
      ...getStepArgs({ node: step.node.left }),
      ...getStepArgs({ node: step.node.right })
    ];
  }
  return [];
}

export default function PrintableResults({ data, input, onBack }) {

  useEffect(() => {
    // Automatycznie wywołaj druk po zamontowaniu
    const timer = setTimeout(() => {
      window.print();
    }, 500);

    return () => clearTimeout(timer);
  }, []);

  const handleBack = () => {
    if (onBack) {
      onBack();
    }
  };

  if (!data || !input) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Brak danych do eksportu</h1>
          <p className="text-gray-600 mb-6">Nie znaleziono danych do wygenerowania raportu.</p>
          <button
            onClick={handleBack}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Wróć
          </button>
        </div>
      </div>
    );
  }

  const kmapData = data.kmap_simplification || data.kmap || {};
  const truthVars = data.truth_table && data.truth_table.length
    ? Object.keys(data.truth_table[0]).filter(k => k !== 'result')
    : [];
  
  const astSteps = data.ast ? computeStepValues(data.ast, data.truth_table || []) : [];

  return (
    <div className="print-container">
      {/* Print-only header */}
      <div className="print-only mb-8 text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Raport analizy wyrażenia logicznego</h1>
        <p className="text-gray-600">Wygenerowano: {new Date().toLocaleString('pl-PL')}</p>
        <button
          onClick={handleBack}
          className="mt-4 bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors print:hidden"
        >
          Wróć
        </button>
      </div>

      {/* Summary Cards */}
      <div className="mb-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="bg-blue-50 rounded-xl p-4 border border-blue-100 print:bg-blue-100">
            <div className="text-xs text-blue-700 font-semibold uppercase">Wpisane wyrażenie</div>
            <div className="font-mono text-lg break-all">{input}</div>
          </div>

          <div className="bg-green-50 rounded-xl p-4 border border-green-100 print:bg-green-100">
            <div className="text-xs text-green-700 font-semibold uppercase">Uproszczone (QM)</div>
            <div className="font-mono text-lg break-all">
              {data.qm?.result || <span className="text-gray-400">Brak</span>}
            </div>
          </div>

          <div className="bg-yellow-50 rounded-xl p-4 border border-yellow-100 print:bg-yellow-100">
            <div className="text-xs text-yellow-700 font-semibold uppercase">ONP</div>
            <div className="font-mono text-lg break-all">
              {data.onp || <span className="text-gray-400">Brak</span>}
            </div>
          </div>

          {/* Tautology and Contradiction */}
          <div className="flex gap-4">
            <div className="bg-purple-50 rounded-xl p-4 border border-purple-100 flex-1 print:bg-purple-100">
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
            
            <div className="bg-purple-50 rounded-xl p-4 border border-purple-100 flex-1 print:bg-purple-100">
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
      </div>

      {/* Truth Table */}
      <div className="mb-8 print:page-break-inside-avoid">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">Tabela prawdy</h2>
        <div className="bg-white rounded-xl border border-gray-200 p-6 print:shadow-none">
          {data.truth_table && data.truth_table.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full border border-gray-300 rounded">
                <thead>
                  <tr>
                    {truthVars.map(v => (
                      <th key={v} className="px-3 py-2 border-b bg-gray-100 text-gray-700 print:bg-gray-200">
                        {v}
                      </th>
                    ))}
                    <th className="px-3 py-2 border-b bg-gray-100 text-gray-700 print:bg-gray-200">Wynik</th>
                  </tr>
                </thead>
                <tbody>
                  {data.truth_table.map((row, i) => {
                    const isOne = row.result === 1;
                    return (
                      <tr key={i} className={isOne ? 'bg-green-50 print:bg-green-100' : ''}>
                        {truthVars.map(v => (
                          <td key={v} className="px-3 py-2 border-b text-center">
                            {row[v]}
                          </td>
                        ))}
                        <td
                          className={`px-3 py-2 border-b text-center font-semibold ${
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
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">Brak danych tabeli prawdy</p>
          )}
        </div>
      </div>

      {/* AST Steps Table */}
      {astSteps.length > 0 && (
        <div className="mb-8 print:page-break-inside-avoid">
          <h2 className="text-2xl font-bold text-gray-800 mb-4">Kroki obliczeń (AST)</h2>
          <div className="bg-white rounded-xl border border-gray-200 p-6 print:shadow-none">
            <div className="overflow-x-auto">
              <table className="min-w-full border border-gray-300 rounded">
                <thead>
                  <tr>
                    <th className="px-3 py-2 border-b bg-gray-100 text-gray-700 print:bg-gray-200">Wyrażenie</th>
                    {truthVars.map(v => (
                      <th key={v} className="px-2 py-1 border-b bg-gray-100 text-gray-700 text-xs print:bg-gray-200">
                        {v}
                      </th>
                    ))}
                    <th className="px-3 py-2 border-b bg-gray-100 text-gray-700 print:bg-gray-200">Wynik</th>
                  </tr>
                </thead>
                <tbody>
                  {astSteps.map((step, i) => {
                    const stepArgs = getStepArgs(step);
                    const hasAllVars = truthVars.every(v => stepArgs.includes(v));
                    return (
                      <tr key={i} className={hasAllVars ? 'bg-blue-50 print:bg-blue-100' : ''}>
                        <td className="px-3 py-2 border-b font-mono text-sm">{step.expr}</td>
                        {truthVars.map(v => {
                          const stepVars = getStepArgs(step);
                          const value = stepVars.includes(v) ? step.values[0] : '-';
                          return (
                            <td key={v} className="px-2 py-1 border-b text-center text-xs">
                              {value}
                            </td>
                          );
                        })}
                        <td className="px-3 py-2 border-b text-center font-semibold">
                          {hasAllVars ? 'Wszystkie zmienne' : 'Częściowe'}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* QM Steps */}
      {data.qm?.steps && (
        <div className="mb-8 print:page-break-after-always">
          <h2 className="text-2xl font-bold text-gray-800 mb-4">Kroki Quine-McCluskey</h2>
          <div className="bg-white rounded-xl border border-gray-200 p-6 print:shadow-none">
            <QMSteps steps={data.qm.steps} />
          </div>
        </div>
      )}

      {/* K-Map */}
      {kmapData.kmap && (
        <div className="mb-8 print:page-break-after-always">
          <h2 className="text-2xl font-bold text-gray-800 mb-4">Mapa Karnaugh</h2>
          <div className="bg-white rounded-xl border border-gray-200 p-6 print:shadow-none">
            <KMapDisplay
              kmap={kmapData.kmap}
              groups={kmapData.groups}
              all_groups={kmapData.all_groups}
              result={kmapData.result}
              vars={kmapData.vars}
              minterms={kmapData.minterms}
            />
          </div>
        </div>
      )}

      {/* AST */}
      {data.ast && (
        <div className="mb-8 print:page-break-inside-avoid">
          <h2 className="text-2xl font-bold text-gray-800 mb-4">Drzewo składniowe (AST)</h2>
          <div className="bg-white rounded-xl border border-gray-200 p-6 print:shadow-none">
            <ASTDisplay ast={data.ast} />
          </div>
        </div>
      )}

      {/* Logic Gates */}
      {data.ast && (
        <div className="mb-8 print:page-break-inside-avoid">
          <h2 className="text-2xl font-bold text-gray-800 mb-4">Bramki logiczne</h2>
          <div className="bg-white rounded-xl border border-gray-200 p-6 print:shadow-none">
            <LogicGatesDisplay ast={data.ast} />
          </div>
        </div>
      )}

      {/* Minimal Forms (Placeholder) */}
      <div className="mb-8 print:page-break-inside-avoid">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">Formy minimalne</h2>
        <div className="bg-white rounded-xl border border-gray-200 p-6 print:shadow-none">
          <p className="text-gray-500 text-center py-8">Funkcja tymczasowo wyłączona</p>
        </div>
      </div>

      {/* Print footer */}
      <div className="print-only mt-8 text-center text-sm text-gray-500">
        <p>Wygenerowano przez Logic Engine - {new Date().toLocaleString('pl-PL')}</p>
      </div>
    </div>
  );
}
