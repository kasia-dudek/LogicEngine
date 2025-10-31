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
          <h3 className="text-lg font-bold text-gray-800">
            Kroki upraszczania {steps.length > 0 && `(${steps.length} krok${steps.length !== 1 ? 'ów' : ''})`}
          </h3>
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
                  <div>
                    <span className="text-xs text-gray-500 font-semibold">Przed:</span>
                    <div className="mt-1 bg-yellow-50 px-2 py-1 rounded border">
                      <ColoredExpression expression={step.before_str} className="text-yellow-700" />
                    </div>
                  </div>
                )}
                
                {typeof step.after_str === 'string' && (
                  <div>
                    <span className="text-xs text-gray-500 font-semibold">Po:</span>
                    <div className="mt-1 bg-blue-50 px-2 py-1 rounded border">
                      <ColoredExpression expression={step.after_str} className="text-blue-700" />
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

