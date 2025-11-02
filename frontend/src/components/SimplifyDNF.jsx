import React, { useState, useEffect } from 'react';
import ColoredExpression from './ColoredExpression';

export default function SimplifyDNF({ expression, loading }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [fetching, setFetching] = useState(false);

  useEffect(() => {
    if (!expression || loading) return;

    const fetchSimplifyDNF = async () => {
      setFetching(true);
      setError('');
      
      const apiUrl = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000';
      
      try {
        const response = await fetch(`${apiUrl}/simplify_dnf`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ expr: expression, var_limit: 8 }),
        });
        
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Failed to simplify');
        }
        
        const result = await response.json();
        setData(result);
      } catch (err) {
        setError(err.message);
        console.error('Error simplifying:', err);
      } finally {
        setFetching(false);
      }
    };

    fetchSimplifyDNF();
  }, [expression, loading]);

  if (loading || fetching) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-300 rounded-lg p-4 text-red-700">
        <strong>Błąd upraszczania:</strong> {error}
      </div>
    );
  }

  if (!data) {
    return null;
  }

  const steps = data.steps || [];

  return (
    <div className="space-y-4">
      {/* Final Result */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-6 border-2 border-blue-200">
        <h3 className="text-lg font-bold text-gray-800 mb-2">Wynik minimalny DNF</h3>
        <div className="text-2xl font-mono text-blue-700">
          <ColoredExpression expression={data.result_dnf} />
        </div>
        <div className="mt-2 text-sm text-gray-600">
          Zmienne: {data.vars?.join(', ')}
        </div>
      </div>

      {/* Steps */}
      {steps.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-lg font-bold text-gray-800">
              Kroki upraszczania {steps.length > 0 && `(${steps.length} krok${steps.length !== 1 ? 'ów' : ''})`}
            </h3>
            <div className="text-xs text-gray-600 bg-gray-50 px-3 py-1.5 rounded-full border border-gray-200 flex items-center gap-2">
              <div className="flex items-center gap-2">
                <span className="inline-block w-3 h-3 bg-red-500 rounded-full flex-shrink-0"></span>
                <span className="inline-block w-3 h-3 bg-green-500 rounded-full flex-shrink-0"></span>
              </div>
              <span><span className="text-red-700 font-semibold">Czerwony</span> = fragment zmieniany (PRZED), <span className="text-green-700 font-semibold">Zielony</span> = nowy fragment (PO)</span>
            </div>
          </div>
          {steps.map((step, idx) => (
            <div key={idx} className="bg-white rounded-lg border border-gray-300 shadow-sm">
              <div className="flex items-center gap-3 p-4 border-b border-gray-200 bg-gray-50">
                <span className="flex-shrink-0 w-8 h-8 flex items-center justify-center rounded-full bg-blue-600 text-white font-bold text-sm">
                  {idx + 1}
                </span>
                <div className="flex-1">
                  <div className="font-semibold text-gray-800">
                    {step.rule || 'Krok'}
                  </div>
                  {step.schema && (
                    <div className="text-xs text-gray-500 mt-0.5">
                      {step.schema}
                    </div>
                  )}
                </div>
              </div>
              
              <div className="p-4 space-y-3">
                {typeof step.before_str === 'string' && (
                  <div aria-label="Wyrażenie przed krokiem z podświetlonym fragmentem">
                    <span className="text-xs text-gray-500 font-semibold">Przed:</span>
                    <div className="mt-1 bg-yellow-50 px-2 py-1 rounded border">
                      <ColoredExpression 
                        expression={step.before_str} 
                        canonExpression={step.before_canon}
                        className="text-yellow-700"
                        highlightText={step.before_subexpr_canon || step.before_subexpr}
                        highlightSpan={step.before_highlight_span}
                        highlightClass="bg-red-50 text-red-800 ring-1 ring-red-200 rounded px-0.5"
                      />
                    </div>
                  </div>
                )}
                
                {/* Show subexpression change if available */}
                {(step.before_subexpr || step.after_subexpr) && (
                  <div>
                    <span className="text-xs text-gray-500 font-semibold">Podwyrażenie:</span>
                    <div className="mt-1 flex items-center gap-2">
                      <ColoredExpression 
                        expression={step.before_subexpr || ''} 
                        className="bg-red-50 text-red-800 ring-1 ring-red-200 rounded px-1" 
                      />
                      <span className="mx-2">→</span>
                      <ColoredExpression 
                        expression={step.after_subexpr || ''} 
                        className="bg-green-50 text-green-800 ring-1 ring-green-200 rounded px-1" 
                      />
                    </div>
                  </div>
                )}
                
                {typeof step.after_str === 'string' && (
                  <div aria-label="Wyrażenie po kroku z podświetlonym fragmentem">
                    <span className="text-xs text-gray-500 font-semibold">Po:</span>
                    <div className="mt-1 bg-blue-50 px-2 py-1 rounded border">
                      <ColoredExpression 
                        expression={step.after_str} 
                        canonExpression={step.after_canon}
                        className="text-blue-700"
                        highlightText={step.after_subexpr_canon || step.after_subexpr}
                        highlightSpan={step.after_highlight_span}
                        highlightClass="bg-green-50 text-green-800 ring-1 ring-green-200 rounded px-0.5"
                      />
                    </div>
                  </div>
                )}

                {/* Details for QM steps */}
                {step.details && Object.keys(step.details).length > 0 && (
                  <div className="mt-2 text-xs text-gray-600">
                    {step.details.left_minterm && (
                      <div>Minterm 1: {step.details.left_minterm} ∧ Minterm 2: {step.details.right_minterm}</div>
                    )}
                    {step.details.result_mask && (
                      <div>Wynik: {step.details.result_mask}</div>
                    )}
                  </div>
                )}

                {/* Proof verification */}
                {step.proof && step.proof.method && (
                  <div className="mt-2 flex items-center gap-2 text-xs">
                    {step.proof.equal ? (
                      <span className="text-green-600 flex items-center gap-1">
                        <span>✓</span> Zweryfikowano
                      </span>
                    ) : (
                      <span className="text-red-600 flex items-center gap-1">
                        <span>✗</span> Błąd weryfikacji
                      </span>
                    )}
                    {step.proof.method === 'tt-hash' && (
                      <span className="text-gray-500">(hash TT)</span>
                    )}
                    {step.proof.method === 'qm-trace' && (
                      <span className="text-gray-500">(QM trace)</span>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

