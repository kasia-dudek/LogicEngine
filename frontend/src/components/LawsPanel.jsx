import React, { useState } from 'react';
import ColoredExpression from './ColoredExpression';

function HighlightedExpression({ beforeSubexpr, afterSubexpr, fullExpression, className = "", strategy = "auto" }) {
  if (!fullExpression) return null;

  const target = strategy === "before" ? beforeSubexpr : strategy === "after" ? afterSubexpr : (afterSubexpr || beforeSubexpr);
  
  if (!target || !fullExpression.includes(target)) {
    return <ColoredExpression expression={fullExpression} className={className} />;
  }

  const highlightClass = strategy === "before" 
    ? "bg-yellow-100 text-yellow-900 border-yellow-300"
    : strategy === "after"
    ? "bg-green-100 text-green-800 border-green-300"
    : "bg-green-100 text-green-800 border-green-300";

  // Użyj highlightText, aby ColoredExpression sam znalazł pozycję po czyszczeniu
  return (
    <span className={`${highlightClass} px-1 rounded border`}>
      <ColoredExpression 
        expression={fullExpression} 
        className={className}
        highlightText={target}
        highlightClass={highlightClass}
      />
    </span>
  );
}

export default function LawsPanel({ data, onPickStep, pickedIndex, onApplyLaw }) {
  const steps = data?.laws?.steps || data?.steps || [];
  const result = data?.laws?.result || data?.result;

  const apiUrl = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000';

  const [hoveredLaw, setHoveredLaw] = useState(null);
  const [previewData, setPreviewData] = useState(null);
  const [infoHoverIndex, setInfoHoverIndex] = useState(null);
  const [hoveredStepIndex, setHoveredStepIndex] = useState(null);

  const previewAlternative = async (step, lawName) => {
    try {
      const resp = await fetch(`${apiUrl}/laws_apply`, {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({
          expr: step.before_tree,
          path: step.path,
          law: lawName
        })
      });
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${resp.status}`);
      }
      const data = await resp.json();
      setPreviewData({
        before: data.before_subexpr || data.before_tree,
        after: data.after_subexpr || data.after_tree,
        afterTree: data.after_tree || data.after,
      });
    } catch (error) {
      setPreviewData(null);
    }
  };

  const applyAlternative = async (step, lawName, stepIndex) => {
    try {
      const resp = await fetch(`${apiUrl}/laws_apply`, {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({
          expr: step.before_tree,
          path: step.path,
          law: lawName
        })
      });
      if (!resp.ok) throw new Error('Nie udało się zastosować alternatywy');
      const data1 = await resp.json();

      const resp2 = await fetch(`${apiUrl}/laws`, {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ expr: data1.after_tree })
      });
      const data2 = await resp2.json();
      
      if (onApplyLaw) onApplyLaw(data2);
    } catch (error) {
      console.error('Błąd podczas zastosowania alternatywy:', error);
    }
  };

  if (!steps || steps.length === 0) {
    return <div className="text-gray-500">Brak kroków lub nie wykryto miejsc do uproszczenia.</div>;
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between mb-2">
        <div className="text-sm text-gray-600">
          Uproszczone: <ColoredExpression expression={result} className="text-green-700 font-semibold" />
        </div>
      </div>

      {/* Kroki */}
      <ol className="space-y-3">
        {steps.map((s, i) => (
          <li key={i} className={`p-3 rounded-xl border ${pickedIndex===i ? 'border-blue-500 bg-blue-50' : 'border-gray-200 bg-white'}`}>
            <div className="flex items-center justify-between">
              <div className="font-semibold text-blue-700 flex items-center gap-2 relative">
                <span>Krok {i+1}: {s.law}</span>
                {/* Ikona z tooltipem wyjaśnienia prawa */}
                <button
                  type="button"
                  onMouseEnter={() => setInfoHoverIndex(i)}
                  onMouseLeave={() => setInfoHoverIndex(null)}
                  className="w-5 h-5 rounded-full bg-blue-100 text-blue-700 text-xs flex items-center justify-center border border-blue-300"
                  aria-label="Wyjaśnienie prawa"
                  title="Wyjaśnienie zastosowanego prawa"
                >
                  ?
                </button>
                {infoHoverIndex === i && (
                  <div className="absolute left-0 top-full mt-2 z-40 w-80 bg-white border border-gray-300 rounded-lg shadow-xl p-3 text-xs">
                    <div className="font-semibold text-blue-700 mb-1">{s.law}</div>
                    <div className="text-gray-700">
                      {s.note || 'Zastosowano to prawo, ponieważ dopasowało się do wskazanego podwyrażenia.'}
                    </div>
                    <div className="mt-2 text-[10px] text-gray-500">
                      {s.source === 'axiom' ? `Aksjomat${s.axiom_id ? ` A${s.axiom_id}` : ''}` : 'Reguła algebraiczna'}
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div className="mt-2 text-sm">
              <div className="mb-2">
                <span className="text-xs text-gray-500 font-semibold">Całe wyrażenie przed krokiem:</span>
                <div className="mt-1 bg-amber-50 px-2 py-1 rounded border">
                  <HighlightedExpression
                    beforeSubexpr={s.before_subexpr}
                    fullExpression={s.before_tree}
                    className="text-gray-800"
                    strategy="before"
                  />
                </div>
              </div>
              <div className="mb-2">
                <span className="text-xs text-gray-500 font-semibold">Podwyrażenie:</span>
                <div className="mt-1">
                  <ColoredExpression expression={s.before_subexpr} className="text-gray-600" />
                  <span className="mx-2">→</span>
                  <ColoredExpression expression={s.after_subexpr} className="text-green-700" />
                </div>
              </div>
              <div className="border-t pt-2">
                <span className="text-xs text-gray-500 font-semibold">Całe wyrażenie po kroku:</span>
                <div className="mt-1 bg-blue-50 px-2 py-1 rounded border">
                  <HighlightedExpression 
                    beforeSubexpr={s.before_subexpr}
                    afterSubexpr={s.after_subexpr}
                    fullExpression={s.after_tree}
                    className="text-blue-700"
                  />
                </div>
              </div>
            </div>

            {s.applicable_here.length > 0 && (
              <div className="text-xs text-gray-500 mt-2 relative">
                Inne prawa możliwe w tym miejscu:&nbsp;
                {s.applicable_here.map((law) => (
                  <button
                    key={law}
                    onClick={() => applyAlternative(s, law, i)}
                    onMouseEnter={async () => {
                      setHoveredLaw(law);
                      setHoveredStepIndex(i);
                      await previewAlternative(s, law);
                    }}
                    onMouseLeave={() => {
                      setHoveredLaw(null);
                      setHoveredStepIndex(null);
                      setPreviewData(null);
                    }}
                    className="inline-flex items-center px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 border border-amber-300 mr-1 hover:bg-amber-200"
                    title={`Zastosuj: ${law}`}
                  >
                    {law}
                  </button>
                ))}
                {hoveredLaw && previewData && hoveredStepIndex === i && (
                  <div className="absolute left-0 top-full mt-2 z-50 w-96 bg-white border border-gray-300 rounded-lg shadow-xl p-3"
                       style={{ minWidth: '320px', maxWidth: '400px' }}>
                    <div className="text-xs font-semibold text-purple-700 mb-2">{hoveredLaw}:</div>
                    <div className="text-xs space-y-1">
                      <div className="break-all">
                        <span className="text-gray-600 font-medium">Przed:</span>
                        <span className="ml-2">
                          <ColoredExpression expression={previewData.before} className="text-gray-700" />
                        </span>
                      </div>
                      <div className="text-center text-gray-400">→</div>
                      <div className="break-all">
                        <span className="text-gray-600 font-medium">Po:</span>
                        <span className="ml-2">
                          <ColoredExpression expression={previewData.after} className="text-green-700" />
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </li>
        ))}
      </ol>
    </div>
  );
} 