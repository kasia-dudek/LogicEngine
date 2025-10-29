import React, { useState } from 'react';
import ColoredExpression from './ColoredExpression';

// Normalizuj wyrażenie: usuń spacje, znormalizuj białe znaki
function normalizeExpr(expr) {
  if (!expr) return '';
  return String(expr).replace(/\s+/g, '').trim();
}

// Parsuj wyrażenie OR/AND na części (uproszczone - dla prostych przypadków)
function parseOrParts(expr) {
  let level = 0;
  const parts = [];
  let current = '';
  
  for (let i = 0; i < expr.length; i++) {
    const char = expr[i];
    if (char === '(') {
      level++;
      current += char;
    } else if (char === ')') {
      level--;
      current += char;
    } else if (char === '∨' && level === 0) {
      if (current.trim()) parts.push(current.trim());
      current = '';
    } else {
      current += char;
    }
  }
  if (current.trim()) parts.push(current.trim());
  
  return parts.length > 0 ? parts : [expr];
}

function parseAndParts(expr) {
  let level = 0;
  const parts = [];
  let current = '';
  
  for (let i = 0; i < expr.length; i++) {
    const char = expr[i];
    if (char === '(') {
      level++;
      current += char;
    } else if (char === ')') {
      level--;
      current += char;
    } else if (char === '∧' && level === 0) {
      if (current.trim()) parts.push(current.trim());
      current = '';
    } else {
      current += char;
    }
  }
  if (current.trim()) parts.push(current.trim());
  
  return parts.length > 0 ? parts : [expr];
}

// Sprawdź czy fragment występuje w wyrażeniu (również w innej kolejności dla OR/AND)
// Zwraca obiekt {start, end} lub null
function findFragmentInExpression(fragment, expression) {
  if (!fragment || !expression) return null;
  
  const normFragment = normalizeExpr(fragment);
  const normExpr = normalizeExpr(expression);
  
  // 1. Najpierw spróbuj dokładnego dopasowania
  let index = normExpr.indexOf(normFragment);
  if (index !== -1) {
    return { start: index, end: index + normFragment.length };
  }
  
  // 2. Spróbuj znaleźć fragment bez zewnętrznych nawiasów (jeśli są)
  let fragmentWithoutParens = normFragment;
  if (normFragment.startsWith('(') && normFragment.endsWith(')')) {
    fragmentWithoutParens = normFragment.slice(1, -1);
    index = normExpr.indexOf(fragmentWithoutParens);
    if (index !== -1) {
      return { start: index, end: index + fragmentWithoutParens.length };
    }
  }
  
  // 3. Jeśli fragment zawiera ∨, spróbuj zamienionej kolejności
  if (normFragment.includes('∨')) {
    try {
      const fragmentParts = parseOrParts(normFragment);
      if (fragmentParts.length === 2) {
        // Spróbuj zamienionej kolejności
        const reversed = fragmentParts[1] + '∨' + fragmentParts[0];
        index = normExpr.indexOf(reversed);
        if (index !== -1) {
          return { start: index, end: index + reversed.length };
        }
        
        // Spróbuj znaleźć każdą część osobno i zwróć zakres
        const idx1 = normExpr.indexOf(fragmentParts[0]);
        const idx2 = normExpr.indexOf(fragmentParts[1]);
        
        if (idx1 !== -1 && idx2 !== -1) {
          const start = Math.min(idx1, idx2);
          const end = Math.max(idx1 + fragmentParts[0].length, idx2 + fragmentParts[1].length);
          return { start, end };
        }
      }
    } catch (e) {
      // Jeśli parsowanie się nie powiodło, kontynuuj
    }
  }
  
  // 4. Podobnie dla AND - używaj parseAndParts dla złożonych wyrażeń
  if (normFragment.includes('∧')) {
    try {
      const fragmentParts = parseAndParts(normFragment);
      const exprParts = parseAndParts(normExpr);
      
      // Sprawdź czy wszystkie części fragmentu występują w wyrażeniu (w dowolnej kolejności)
      const matchingParts = [];
      for (const part of fragmentParts) {
        for (const exprPart of exprParts) {
          if (exprPart === part || exprPart.includes(part) || part.includes(exprPart)) {
            const idx = normExpr.indexOf(exprPart);
            if (idx !== -1) {
              matchingParts.push({ part: exprPart, index: idx });
              break; // Znaleziono dopasowanie dla tej części
            }
          }
        }
      }
      
      // Jeśli wszystkie części zostały znalezione
      if (matchingParts.length === fragmentParts.length && matchingParts.length > 0) {
        const indices = matchingParts.map(m => m.index);
        const start = Math.min(...indices);
        const end = Math.max(...indices.map((idx, i) => idx + matchingParts[i].part.length));
        return { start, end };
      }
      
      // Dla prostych przypadków z 2 częściami, spróbuj zamienionej kolejności
      if (fragmentParts.length === 2) {
        const reversed = fragmentParts[1] + '∧' + fragmentParts[0];
        index = normExpr.indexOf(reversed);
        if (index !== -1) {
          return { start: index, end: index + reversed.length };
        }
      }
    } catch (e) {
      // Kontynuuj
    }
  }
  
  // 5. Fallback: spróbuj znaleźć chociaż część fragmentu
  // Znajdź najdłuższy substring fragmentu który występuje w wyrażeniu
  for (let len = normFragment.length; len > 3; len--) {
    for (let i = 0; i <= normFragment.length - len; i++) {
      const substring = normFragment.substring(i, i + len);
      const idx = normExpr.indexOf(substring);
      if (idx !== -1) {
        return { start: idx, end: idx + substring.length };
      }
    }
  }
  
  return null;
}

function HighlightedExpression({ beforeSubexpr, afterSubexpr, fullExpression, className = "", strategy = "auto" }) {
  if (!fullExpression) return null;

  const target = strategy === "before" ? beforeSubexpr : strategy === "after" ? afterSubexpr : (afterSubexpr || beforeSubexpr);
  
  if (!target) {
    return <ColoredExpression expression={fullExpression} className={className} />;
  }

  const highlightClass = strategy === "before" 
    ? "bg-yellow-100 text-yellow-900 border-yellow-300"
    : strategy === "after"
    ? "bg-green-100 text-green-800 border-green-300"
    : "bg-green-100 text-green-800 border-green-300";

  // Najpierw spróbuj prostego dopasowania - użyj highlightText, który ColoredExpression sam znormalizuje
  const normTarget = normalizeExpr(target);
  const normFull = normalizeExpr(fullExpression);
  
  // Jeśli fragment jest równy całemu wyrażeniu, podświetl całość
  if (normFull === normTarget) {
    return (
      <span className={`${highlightClass} px-1 rounded border inline-block`}>
        <ColoredExpression 
          expression={fullExpression} 
          className={className}
        />
      </span>
    );
  }
  
  // Jeśli fragment jest zawarty w wyrażeniu
  if (normFull.includes(normTarget)) {
    return (
      <ColoredExpression 
        expression={fullExpression} 
        className={className}
        highlightText={target}
        highlightClass={highlightClass}
      />
    );
  }

  // Jeśli proste dopasowanie nie działa, użyj zaawansowanego wyszukiwania
  const foundRange = findFragmentInExpression(target, fullExpression);
  
  if (!foundRange) {
    // Jeśli nadal nie znaleziono, pokaż wyrażenie bez podświetlenia (ale to nie powinno się często zdarzać)
    return <ColoredExpression expression={fullExpression} className={className} />;
  }

  // Użyj znalezionego zakresu
  // Ale musimy przejść przez cleanedExpression w ColoredExpression
  // Więc przekażemy jako highlightText fragment który znaleźliśmy
  const normExpr = normalizeExpr(fullExpression);
  const foundSubstring = normExpr.substring(foundRange.start, foundRange.end);
  
  return (
    <ColoredExpression 
      expression={fullExpression} 
      className={className}
      highlightText={foundSubstring}
      highlightClass={highlightClass}
    />
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