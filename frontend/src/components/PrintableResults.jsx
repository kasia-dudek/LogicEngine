import React, { useEffect, useState } from 'react';
import QMSteps from './QMSteps';
import KMapDisplay from './KMapDisplay';
import ASTDisplay from './ASTDisplay';
import LogicGatesDisplay from './LogicGatesDisplay';
import SimplifyDNF from './SimplifyDNF';
import ColoredExpression from './ColoredExpression';
import { getStepArgs, computeStepValues } from '../utils/astHelpers';

export default function PrintableResults({ data, input, onBack }) {
  const [simplifyDnfData, setSimplifyDnfData] = useState(null);
  const [loadingSimplifyDnf, setLoadingSimplifyDnf] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      window.print();
    }, 500);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (!input) return;
    
    const fetchSimplifyDNF = async () => {
      setLoadingSimplifyDnf(true);
      const apiUrl = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000';
      
      try {
        const response = await fetch(`${apiUrl}/simplify_dnf`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ expr: input, var_limit: 8 }),
        });
        
        if (response.ok) {
          const result = await response.json();
          setSimplifyDnfData(result);
        }
      } catch (err) {
        console.error('Error fetching simplify_dnf:', err);
      } finally {
        setLoadingSimplifyDnf(false);
      }
    };

    fetchSimplifyDNF();
  }, [input]);

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
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors print:hidden"
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

  const truthCoverage = data.truth_table && data.truth_table.length > 0
    ? Math.round((data.truth_table.filter(row => row.result === 1).length / data.truth_table.length) * 100)
    : null;

  return (
    <div className="print-container max-w-5xl mx-auto p-4 bg-white">
      <div className="print-only mb-8 text-center border-b pb-4">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Raport analizy wyrażenia logicznego</h1>
        <p className="text-gray-600">Wygenerowano: {new Date().toLocaleString('pl-PL')}</p>
        <button
          onClick={handleBack}
          className="mt-4 bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors print:hidden"
        >
          Wróć
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div className="bg-blue-50 rounded-xl p-4 border border-blue-100 print:bg-blue-100">
          <div className="text-xs text-blue-700 font-semibold uppercase">Wpisane wyrażenie</div>
          <div className="font-mono text-lg break-all">{input}</div>
        </div>

        {truthCoverage !== null && (
          <div className="bg-green-50 rounded-xl p-4 border border-green-100 print:bg-green-100">
            <div className="text-xs text-green-700 font-semibold uppercase">Pokrycie prawdy</div>
            <div className="font-mono text-lg break-all">
              {truthCoverage}% ({data.truth_table.filter(row => row.result === 1).length} z {data.truth_table.length})
            </div>
          </div>
        )}

        <div className="bg-yellow-50 rounded-xl p-4 border border-yellow-100 print:bg-yellow-100">
          <div className="text-xs text-yellow-700 font-semibold uppercase">ONP</div>
          <div className="font-mono text-lg break-all">
            {data.onp || <span className="text-gray-400">Brak</span>}
          </div>
        </div>

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

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div className="bg-blue-50 rounded-xl p-4 border border-blue-100 print:bg-blue-100">
          <div className="flex items-start justify-between mb-2">
            <div className="text-xs text-blue-700 font-semibold uppercase">DNF (Suma iloczynów)</div>
            <div className="text-xs">
              <div className="bg-gray-100 px-2 py-1 rounded">
                <span className="text-gray-500">Terminy:</span> <span className="font-bold text-blue-600">{data.minimal_forms?.dnf?.terms || 0}</span> | 
                <span className="text-gray-500"> Literały:</span> <span className="font-bold text-blue-600">{data.minimal_forms?.dnf?.literals || 0}</span>
              </div>
            </div>
          </div>
          <div className="font-mono text-lg break-all">
            {data.minimal_forms?.dnf?.expr ? (
              <ColoredExpression expression={data.minimal_forms.dnf.expr} />
            ) : (
              <span className="text-gray-400">Brak</span>
            )}
          </div>
        </div>

        <div className="bg-green-50 rounded-xl p-4 border border-green-100 print:bg-green-100">
          <div className="flex items-start justify-between mb-2">
            <div className="text-xs text-green-700 font-semibold uppercase">CNF (Iloczyn sum)</div>
            <div className="text-xs">
              <div className="bg-gray-100 px-2 py-1 rounded">
                <span className="text-gray-500">Terminy:</span> <span className="font-bold text-green-600">{data.minimal_forms?.cnf?.terms || 0}</span> | 
                <span className="text-gray-500"> Literały:</span> <span className="font-bold text-green-600">{data.minimal_forms?.cnf?.literals || 0}</span>
              </div>
            </div>
          </div>
          <div className="font-mono text-lg break-all">
            {data.minimal_forms?.cnf?.expr ? (
              <ColoredExpression expression={data.minimal_forms.cnf.expr} />
            ) : (
              <span className="text-gray-400">Brak</span>
            )}
          </div>
        </div>
      </div>

      {data?.ast && (
        <div className="mb-8 print:page-break-inside-avoid">
          <h2 className="text-2xl font-bold text-gray-800 mb-4">Drzewo składniowe (AST)</h2>
          <div className="bg-white rounded-xl border border-gray-200 p-6 print:shadow-none">
            <ASTDisplay ast={data.ast} />
          </div>
        </div>
      )}

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
                      <tr key={i} className={isOne ? 'bg-green-100 print:bg-green-200' : ''}>
                        {truthVars.map(v => (
                          <td key={v} className="px-3 py-2 border-b text-center">
                            {row[v]}
                          </td>
                        ))}
                        <td
                          className={`px-3 py-2 border-b text-center font-semibold ${
                            isOne ? 'text-green-800 print:text-green-900' : 'text-gray-700'
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

      {simplifyDnfData && (
        <div className="mb-8 print:page-break-after-always">
          <h2 className="text-2xl font-bold text-gray-800 mb-4">Prawa logiczne</h2>
          <div className="bg-white rounded-xl border border-gray-200 p-6 print:shadow-none">
            <SimplifyDNF expression={input} loading={loadingSimplifyDnf} />
          </div>
        </div>
      )}

      {data.qm?.steps && (
        <div className="mb-8 print:page-break-after-always">
          <h2 className="text-2xl font-bold text-gray-800 mb-4">Kroki Quine-McCluskey</h2>
          <div className="bg-white rounded-xl border border-gray-200 p-6 print:shadow-none">
            <QMSteps steps={data.qm.steps} />
          </div>
        </div>
      )}

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

      {data.ast && (
        <div className="mb-8 print:page-break-inside-avoid">
          <h2 className="text-2xl font-bold text-gray-800 mb-4">Bramki logiczne</h2>
          <div className="bg-white rounded-xl border border-gray-200 p-6 print:shadow-none">
            <LogicGatesDisplay ast={data.ast} />
          </div>
        </div>
      )}

      <div className="print-only mt-8 text-center text-sm text-gray-500 border-t pt-4">
        <p>Wygenerowano przez Logic Engine - {new Date().toLocaleString('pl-PL')}</p>
      </div>
    </div>
  );
}
