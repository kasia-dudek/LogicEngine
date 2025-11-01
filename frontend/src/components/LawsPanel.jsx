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

// Znajdź najdłuższy wspólny ciąg znaków (dla fallbacku)
function findLongestCommonSubstring(str1, str2) {
  let longest = '';
  let longestIndex = -1;
  
  for (let i = 0; i < str1.length; i++) {
    for (let len = Math.min(str1.length - i, str2.length); len > longest.length; len--) {
      const substr = str1.substring(i, i + len);
      const idx = str2.indexOf(substr);
      if (idx !== -1 && substr.length > longest.length) {
        longest = substr;
        longestIndex = idx;
      }
    }
  }
  
  if (longest.length > 2) {
    return { start: longestIndex, end: longestIndex + longest.length };
  }
  return null;
}

// Sprawdź czy fragment występuje w wyrażeniu (również w innej kolejności dla OR/AND)
// Zwraca obiekt {start, end} - ZAWSZE zwraca wynik (nigdy null)
function findFragmentInExpression(fragment, expression) {
  if (!fragment || !expression) {
    // Jeśli brak danych, zwróć całe wyrażenie
    return { start: 0, end: expression ? normalizeExpr(expression).length : 0 };
  }
  
  const normFragment = normalizeExpr(fragment);
  const normExpr = normalizeExpr(expression);
  
  // 1. Najpierw spróbuj dokładnego dopasowania
  let index = normExpr.indexOf(normFragment);
  if (index !== -1) {
    return { start: index, end: index + normFragment.length };
  }
  
  // 2. Spróbuj znaleźć fragment bez zewnętrznych nawiasów (jeśli są)
  if (normFragment.startsWith('(') && normFragment.endsWith(')')) {
    const fragmentWithoutParens = normFragment.slice(1, -1);
    index = normExpr.indexOf(fragmentWithoutParens);
    if (index !== -1) {
      return { start: index, end: index + fragmentWithoutParens.length };
    }
  }
  
  // 3. Dla OR - sprawdź wszystkie permutacje części
  if (normFragment.includes('∨')) {
    try {
      const fragmentParts = parseOrParts(normFragment);
      
      // Spróbuj każdą permutację części OR
      if (fragmentParts.length === 2) {
        const reversed = fragmentParts[1] + '∨' + fragmentParts[0];
        index = normExpr.indexOf(reversed);
        if (index !== -1) {
          return { start: index, end: index + reversed.length };
        }
      }
      
      // Znajdź wszystkie części w wyrażeniu
      const foundParts = [];
      for (const part of fragmentParts) {
        index = normExpr.indexOf(part);
        if (index !== -1) {
          foundParts.push({ part, index, length: part.length });
        }
      }
      
      // Jeśli znaleziono wszystkie części, zwróć zakres je obejmujący
      if (foundParts.length === fragmentParts.length && foundParts.length > 0) {
        const start = Math.min(...foundParts.map(p => p.index));
        const end = Math.max(...foundParts.map(p => p.index + p.length));
        return { start, end };
      }
      
      // Jeśli znaleziono chociaż jedną część, użyj jej
      if (foundParts.length > 0) {
        const best = foundParts.reduce((a, b) => b.length > a.length ? b : a);
        return { start: best.index, end: best.index + best.length };
      }
    } catch (e) {
      // Kontynuuj
    }
  }
  
  // 4. Dla AND - sprawdź wszystkie permutacje części
  if (normFragment.includes('∧')) {
    try {
      const fragmentParts = parseAndParts(normFragment);
      const exprParts = parseAndParts(normExpr);
      
      // Sprawdź czy wszystkie części fragmentu występują w wyrażeniu (dowolna kolejność)
      const foundParts = [];
      for (const part of fragmentParts) {
        // Szukaj dokładnego dopasowania lub zawierania
        for (const exprPart of exprParts) {
          if (exprPart === part) {
            const idx = normExpr.indexOf(exprPart);
            if (idx !== -1) {
              foundParts.push({ part: exprPart, index: idx, length: exprPart.length });
              break;
            }
          } else if (exprPart.includes(part) || part.includes(exprPart)) {
            const idx = normExpr.indexOf(exprPart);
            if (idx !== -1) {
              foundParts.push({ part: exprPart, index: idx, length: exprPart.length });
              break;
            }
          }
        }
      }
      
      // Jeśli znaleziono wszystkie części, zwróć zakres
      if (foundParts.length === fragmentParts.length && foundParts.length > 0) {
        const start = Math.min(...foundParts.map(p => p.index));
        const end = Math.max(...foundParts.map(p => p.index + p.length));
        return { start, end };
      }
      
      // Jeśli znaleziono chociaż jedną część
      if (foundParts.length > 0) {
        const best = foundParts.reduce((a, b) => b.length > a.length ? b : a);
        return { start: best.index, end: best.index + best.length };
      }
      
      // Spróbuj zamienionej kolejności dla 2 części
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
  
  // 5. Fallback: znajdź najdłuższy wspólny substring (zawsze zwróci wynik jeśli fragment ma > 2 znaki)
  const lcs = findLongestCommonSubstring(normFragment, normExpr);
  if (lcs) {
    return lcs;
  }
  
  // 6. Ostatnia deska ratunku: podświetl pierwsze znaki fragmentu jeśli występują
  if (normFragment.length > 0) {
    const firstChar = normFragment[0];
    index = normExpr.indexOf(firstChar);
    if (index !== -1) {
      return { start: index, end: Math.min(index + normFragment.length, normExpr.length) };
    }
  }
  
  // 7. Jeśli wszystko zawiodło, podświetl całe wyrażenie (lepsze niż nic)
  return { start: 0, end: normExpr.length };
}

function HighlightedExpression({ 
  beforeSubexpr, 
  afterSubexpr, 
  fullExpression, 
  className = "", 
  strategy = "auto",
  canonExpression = null,
  highlightSpan = null,
  beforeSubexprCanon = null,
  afterSubexprCanon = null
}) {
  if (!fullExpression) return null;

  const target = strategy === "before" ? beforeSubexpr : strategy === "after" ? afterSubexpr : (afterSubexpr || beforeSubexpr);
  const targetCanon = strategy === "before" ? beforeSubexprCanon : strategy === "after" ? afterSubexprCanon : (afterSubexprCanon || beforeSubexprCanon);
  
  if (!target) {
    return <ColoredExpression expression={fullExpression} className={className} />;
  }

  // Używamy zielonego koloru dla obu (przed i po) dla spójności
  const highlightClass = "bg-green-100 text-green-800 border-green-300";

  // Use canonical highlighting if available, otherwise fall back to substring matching
  return (
    <ColoredExpression 
      expression={fullExpression} 
      canonExpression={canonExpression}
      className={className}
      highlightText={targetCanon || target}
      highlightSpan={highlightSpan}
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
        beforeCanon: data.before_canon,
        afterCanon: data.after_canon,
        beforeSubCanon: data.before_subexpr_canon,
        afterSubCanon: data.after_subexpr_canon,
        beforeSpan: data.before_highlight_span,
        afterSpan: data.after_highlight_span,
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

      {/* Legend */}
      <div className="text-xs text-gray-600 bg-green-50 px-3 py-1.5 rounded-full border border-green-200 flex items-center gap-2">
        <span className="inline-block w-3 h-3 bg-green-500 rounded-full flex-shrink-0"></span>
        <span>Zielony podkreśla fragment zmieniany w tym kroku (Przed) oraz nowo powstały fragment (Po).</span>
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
                    canonExpression={s.before_canon}
                    className="text-gray-800"
                    strategy="before"
                    highlightSpan={s.before_highlight_span}
                    beforeSubexprCanon={s.before_subexpr_canon}
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
                    canonExpression={s.after_canon}
                    className="text-blue-700"
                    highlightSpan={s.after_highlight_span}
                    beforeSubexprCanon={s.before_subexpr_canon}
                    afterSubexprCanon={s.after_subexpr_canon}
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
                    <div className="text-xs space-y-2">
                      <div className="break-all">
                        <span className="text-gray-600 font-medium mb-1 block">Przed:</span>
                        <div className="bg-amber-50 px-2 py-1 rounded border">
                          <ColoredExpression 
                            expression={s.before_tree} 
                            canonExpression={previewData.beforeCanon}
                            className="text-gray-700" 
                            highlightText={previewData.beforeSubCanon || previewData.before}
                            highlightSpan={previewData.beforeSpan}
                          />
                        </div>
                      </div>
                      <div className="text-center text-gray-400">→</div>
                      <div className="break-all">
                        <span className="text-gray-600 font-medium mb-1 block">Po:</span>
                        <div className="bg-blue-50 px-2 py-1 rounded border">
                          <ColoredExpression 
                            expression={previewData.afterTree || previewData.after} 
                            canonExpression={previewData.afterCanon}
                            className="text-green-700" 
                            highlightText={previewData.afterSubCanon || previewData.after}
                            highlightSpan={previewData.afterSpan}
                          />
                        </div>
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