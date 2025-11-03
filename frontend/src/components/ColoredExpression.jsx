import React, { useMemo } from 'react';

/**
 * Komponent do wyświetlania wyrażeń logicznych z kolorowanymi nawiasami
 * Nawiasy są kolorowane według poziomów zagnieżdżenia
 */

// Default color classes
const COLOR_BEFORE = "bg-red-50 text-red-800 ring-1 ring-red-200 rounded px-0.5";
const COLOR_AFTER = "bg-green-50 text-green-800 ring-1 ring-green-200 rounded px-0.5";

// Funkcja do czyszczenia nawiasów - wyodrębniona żeby używać dla fragmentu też
function cleanExpression(expr) {
  if (!expr) return '';
  try {
    let result = String(expr);
    if (result.length < 4) return result;

    const maxIterations = 6;
    for (let i = 0; i < maxIterations; i++) {
      const before = result;
      result = result.replace(/\(([A-Z])\)/g, '$1');
      result = result.replace(/\(¬([A-Z])\)/g, '¬$1');
      result = result.replace(/\(\(([^()]+)\)\)/g, '($1)');
      
      if (result.startsWith('(') && result.endsWith(')')) {
        const inner = result.slice(1, -1);
        let balance = 0;
        let canRemove = true;
        for (let j = 0; j < inner.length; j++) {
          if (inner[j] === '(') balance++;
          else if (inner[j] === ')') balance--;
          if (balance < 0) {
            canRemove = false;
            break;
          }
        }
        if (canRemove && balance === 0) {
          result = inner;
        }
      }

      if (result === before) break;
    }
    return result;
  } catch (_) {
    return String(expr);
  }
}

/**
 * Find text range in target expression using heuristics
 * Returns {start, end} or null if not found
 */
function findTextRange(targetExpression, highlightText) {
  if (!targetExpression || !highlightText) return null;
  
  const cleaned = cleanExpression(highlightText);
  
  // 1. Try exact match
  let index = targetExpression.indexOf(cleaned);
  if (index !== -1) {
    return { start: index, end: index + cleaned.length };
  }
  
  // 2. Try without outer parentheses
  if (cleaned.startsWith('(') && cleaned.endsWith(')')) {
    const withoutParens = cleaned.slice(1, -1);
    index = targetExpression.indexOf(withoutParens);
    if (index !== -1) {
      return { start: index, end: index + withoutParens.length };
    }
  }
  
  // 3. Parse AND/OR parts
  function parseParts(expr, separator) {
    let level = 0;
    const parts = [];
    let current = '';
    for (let i = 0; i < expr.length; i++) {
      const char = expr[i];
      if (char === '(') level++;
      else if (char === ')') level--;
      else if (char === separator && level === 0) {
        if (current.trim()) parts.push(current.trim());
        current = '';
        continue;
      }
      current += char;
    }
    if (current.trim()) parts.push(current.trim());
    return parts.length > 0 ? parts : [expr];
  }
  
  if (cleaned.includes('∧')) {
    const parts = parseParts(cleaned, '∧');
    if (parts.length >= 2) {
      const found = [];
      for (const part of parts) {
        const idx = targetExpression.indexOf(part);
        if (idx !== -1) {
          found.push({ idx, len: part.length });
        }
      }
      if (found.length >= 2 && found.length >= Math.ceil(parts.length / 2)) {
        const start = Math.min(...found.map(f => f.idx));
        const end = Math.max(...found.map(f => f.idx + f.len));
        return { start, end };
      }
      if (found.length > 0) {
        const best = found.reduce((a, b) => b.len > a.len ? b : a);
        return { start: best.idx, end: best.idx + best.len };
      }
    }
  }
  
  if (cleaned.includes('∨')) {
    const parts = parseParts(cleaned, '∨');
    if (parts.length >= 2) {
      const found = [];
      for (const part of parts) {
        const idx = targetExpression.indexOf(part);
        if (idx !== -1) {
          found.push({ idx, len: part.length });
        }
      }
      if (found.length >= 2 && found.length >= Math.ceil(parts.length / 2)) {
        const start = Math.min(...found.map(f => f.idx));
        const end = Math.max(...found.map(f => f.idx + f.len));
        return { start, end };
      }
      if (found.length > 0) {
        const best = found.reduce((a, b) => b.len > a.len ? b : a);
        return { start: best.idx, end: best.idx + best.len };
      }
    }
  }
  
  // 4. LCS fallback
  let longestMatch = '';
  let longestIndex = -1;
  for (let i = 0; i < targetExpression.length; i++) {
    for (let len = Math.min(cleaned.length, targetExpression.length - i); len > longestMatch.length; len--) {
      const substr = targetExpression.substring(i, i + len);
      if (cleaned.includes(substr) && len > longestMatch.length) {
        longestMatch = substr;
        longestIndex = i;
      }
    }
  }
  
  for (let i = 0; i < cleaned.length; i++) {
    for (let len = Math.min(targetExpression.length, cleaned.length - i); len > longestMatch.length; len--) {
      const substr = cleaned.substring(i, i + len);
      const idx = targetExpression.indexOf(substr);
      if (idx !== -1 && len > longestMatch.length) {
        longestMatch = substr;
        longestIndex = idx;
      }
    }
  }
  
  if (longestMatch.length > 2 && longestIndex !== -1) {
    return { start: longestIndex, end: longestIndex + longestMatch.length };
  }
  
  return null;
}

export default function ColoredExpression({ 
  expression, 
  className = "", 
  highlightRange = null, 
  highlightText = null, 
  highlightSpan = null,
  highlightSpansCp = null,
  canonExpression = null,
  highlightClass = "bg-green-100 text-green-900 ring-1 ring-green-300 rounded px-0.5" 
}) {
  // PRIORITY: Use canonical expression if provided, otherwise use regular expression
  // This is THE target string - we count indices and render on this EXACT string
  const target = useMemo(() => {
    const exprToClean = canonExpression || expression;
    return cleanExpression(exprToClean);
  }, [canonExpression, expression]);
  
  // Wyczyść również fragment tak samo jak wyrażenie - to zapewni spójność
  const cleanedHighlightText = useMemo(() => {
    if (!highlightText) return null;
    return cleanExpression(highlightText);
  }, [highlightText]);

  // If highlightSpan is provided, it refers to the expression string (after pretty() but before cleanExpression)
  // We need to map indices from expression to cleaned string by computing the actual offset
  const mappedHighlightSpan = useMemo(() => {
    if (!highlightSpan || highlightSpan.start === undefined || highlightSpan.end === undefined) {
      return null;
    }
    
    // NEW: If span is provided, it's relative to expression (before_str/after_str from backend)
    // which is already pretty-printed but may be cleaned further by cleanExpression()
    // Map from expression to cleaned(target)
    const sourceExpr = expression || '';
    const cleanedSource = cleanExpression(sourceExpr);
    
    if (cleanedSource === sourceExpr) {
      // No transformation by cleanExpression, span maps 1:1
      return highlightSpan;
    }
    
    // Transformation happened - need to compute offset mapping
    // Strategy: find how many characters were removed before each position
    const offsetMap = [];
    let origIdx = 0;
    let cleanIdx = 0;
    
    // Build map of how many chars were removed before each original index
    while (origIdx < sourceExpr.length || cleanIdx < cleanedSource.length) {
      if (origIdx < sourceExpr.length && cleanIdx < cleanedSource.length && 
          sourceExpr[origIdx] === cleanedSource[cleanIdx]) {
        // Characters match
        offsetMap[origIdx] = origIdx - cleanIdx;
        origIdx++;
        cleanIdx++;
      } else if (origIdx < sourceExpr.length) {
        // Character removed from original
        offsetMap[origIdx] = origIdx - cleanIdx;
        origIdx++;
      } else {
        // Additional character in cleaned (shouldn't happen)
        break;
      }
    }
    
    // Map the span using offset
    const offsetAtStart = offsetMap[highlightSpan.start] || 0;
    const offsetAtEnd = offsetMap[Math.min(highlightSpan.end, offsetMap.length - 1)] || 0;
    
    return {
      start: Math.max(0, highlightSpan.start - offsetAtStart),
      end: Math.max(0, highlightSpan.end - offsetAtEnd)
    };
  }, [highlightSpan, expression]);

  // Oblicz highlightRange z highlightText lub highlightSpan
  // CRITICAL: indeksy muszą być liczone na dokładnie tym samym stringu, który renderujemy
  const computedHighlightRange = useMemo(() => {
    // Priority 1: explicit highlightRange
    if (highlightRange) return highlightRange;
    
    // Priority 2: highlightSpan from backend (canonical indices)
    // Use mapped span that accounts for cleanExpression transformations
    if (mappedHighlightSpan && mappedHighlightSpan.start !== undefined && mappedHighlightSpan.end !== undefined) {
      return {
        start: mappedHighlightSpan.start,
        end: mappedHighlightSpan.end,
        class: highlightClass
      };
    }
    
    // Priority 3: highlightText (fallback substring matching)
    // WAZNE: NIE usuwaj spacji - licz indeksy na target, który jest renderowany!
    if (!cleanedHighlightText || !target) return null;
    
    // Używamy target ze spacjami - ten sam string, który trafi do renderowania
    const targetExpression = target;
    const targetHighlight = cleanedHighlightText;
    
    // 1. Spróbuj dokładnego dopasowania
    let index = targetExpression.indexOf(targetHighlight);
    if (index !== -1) {
      return {
        start: index,
        end: index + targetHighlight.length,
        class: highlightClass
      };
    }
    
    // 2. Spróbuj bez zewnętrznych nawiasów w highlightText
    if (targetHighlight.startsWith('(') && targetHighlight.endsWith(')')) {
      const highlightWithoutParens = targetHighlight.slice(1, -1);
      index = targetExpression.indexOf(highlightWithoutParens);
      if (index !== -1) {
        return {
          start: index,
          end: index + highlightWithoutParens.length,
          class: highlightClass
        };
      }
    }
    
    // 3. Fallback dla AND/OR: spróbuj znaleźć wszystkie części fragmentu
    // (nawet jeśli kolejność jest inna)
    // Używamy prostego parsowania z uwzględnieniem nawiasów
    function parseParts(expr, separator) {
      let level = 0;
      const parts = [];
      let current = '';
      for (let i = 0; i < expr.length; i++) {
        const char = expr[i];
        if (char === '(') level++;
        else if (char === ')') level--;
        else if (char === separator && level === 0) {
          if (current.trim()) parts.push(current.trim());
          current = '';
          continue;
        }
        current += char;
      }
      if (current.trim()) parts.push(current.trim());
      return parts.length > 0 ? parts : [expr];
    }
    
    if (targetHighlight.includes('∧')) {
      const highlightParts = parseParts(targetHighlight, '∧');
      if (highlightParts.length >= 2) {
        const foundParts = [];
        for (const part of highlightParts) {
          const idx = targetExpression.indexOf(part);
          if (idx !== -1) {
            foundParts.push({ part, index: idx, length: part.length });
          }
        }
        // Jeśli znaleziono większość części (co najmniej 50%), użyj je
        if (foundParts.length >= 2 && foundParts.length >= Math.ceil(highlightParts.length / 2)) {
          const start = Math.min(...foundParts.map(p => p.index));
          const end = Math.max(...foundParts.map(p => p.index + p.length));
          return {
            start,
            end,
            class: highlightClass
          };
        }
        // Jeśli znaleziono chociaż jedną część, użyj najdłuższą
        if (foundParts.length > 0) {
          const best = foundParts.reduce((a, b) => b.length > a.length ? b : a);
          return {
            start: best.index,
            end: best.index + best.length,
            class: highlightClass
          };
        }
      }
    }
    
    if (targetHighlight.includes('∨')) {
      const highlightParts = parseParts(targetHighlight, '∨');
      if (highlightParts.length >= 2) {
        const foundParts = [];
        for (const part of highlightParts) {
          const idx = targetExpression.indexOf(part);
          if (idx !== -1) {
            foundParts.push({ part, index: idx, length: part.length });
          }
        }
        // Sort by position
        foundParts.sort((a, b) => a.index - b.index);
        
        // Try to find consecutive matches that form the full pattern
        for (let i = 0; i <= foundParts.length - highlightParts.length; i++) {
          const candidate = foundParts.slice(i, i + highlightParts.length);
          // Check if all parts are present
          if (candidate.length === highlightParts.length) {
            const start = candidate[0].index;
            const end = candidate[candidate.length - 1].index + candidate[candidate.length - 1].length;
            // Check if there are no extra parts between them
            const extractedText = targetExpression.substring(start, end);
            // Check: extracted text should have exactly the same number of ∨ separators as highlight
            const highlightOrCount = (targetHighlight.match(/∨/g) || []).length;
            const extractedOrCount = (extractedText.match(/∨/g) || []).length;
            
            // If counts match and all parts are present, it's a valid match
            if (highlightOrCount === extractedOrCount) {
              let allPartsPresent = true;
              for (const part of highlightParts) {
                if (!extractedText.includes(part)) {
                  allPartsPresent = false;
                  break;
                }
              }
              if (allPartsPresent) {
                return {
                  start,
                  end,
                  class: highlightClass
                };
              }
            }
          }
        }
        
        // Fallback: if we found most parts, use them but expand conservatively
        if (foundParts.length >= 2 && foundParts.length >= Math.ceil(highlightParts.length / 2)) {
          const start = Math.min(...foundParts.map(p => p.index));
          const end = Math.max(...foundParts.map(p => p.index + p.length));
          return {
            start,
            end,
            class: highlightClass
          };
        }
        // Jeśli znaleziono chociaż jedną część, użyj najdłuższą
        if (foundParts.length > 0) {
          const best = foundParts.reduce((a, b) => b.length > a.length ? b : a);
          return {
            start: best.index,
            end: best.index + best.length,
            class: highlightClass
          };
        }
      }
    }
    
    // 4. Fallback: znajdź najdłuższy wspólny substring (po obu stronach)
    // Szukaj substringa fragmentu w wyrażeniu
    let longestMatch = '';
    let longestIndex = -1;
    for (let i = 0; i < targetExpression.length; i++) {
      for (let len = Math.min(targetHighlight.length, targetExpression.length - i); len > longestMatch.length; len--) {
        const substr = targetExpression.substring(i, i + len);
        if (targetHighlight.includes(substr) && len > longestMatch.length) {
          longestMatch = substr;
          longestIndex = i;
        }
      }
    }
    
    // Również szukaj w drugą stronę - substringa wyrażenia w fragmencie
    for (let i = 0; i < targetHighlight.length; i++) {
      for (let len = Math.min(targetExpression.length, targetHighlight.length - i); len > longestMatch.length; len--) {
        const substr = targetHighlight.substring(i, i + len);
        const idx = targetExpression.indexOf(substr);
        if (idx !== -1 && len > longestMatch.length) {
          longestMatch = substr;
          longestIndex = idx;
        }
      }
    }
    
    if (longestMatch.length > 2 && longestIndex !== -1) {
      return {
        start: longestIndex,
        end: longestIndex + longestMatch.length,
        class: highlightClass
      };
    }
    
    // 5. Soft fallback: podświetl początek jeśli pierwszy znak się zgadza
    if (targetHighlight.length > 0) {
      const firstChar = targetHighlight[0];
      index = targetExpression.indexOf(firstChar);
      if (index !== -1) {
        return {
          start: index,
          end: Math.min(index + targetHighlight.length, targetExpression.length),
          class: highlightClass
        };
      }
      
      // Spróbuj również znaleźć ostatni znak
      const lastChar = targetHighlight[targetHighlight.length - 1];
      const lastIdx = targetExpression.lastIndexOf(lastChar);
      if (lastIdx !== -1) {
        return {
          start: Math.max(0, lastIdx - targetHighlight.length + 1),
          end: lastIdx + 1,
          class: highlightClass
        };
      }
    }
    
    // 6. No match found - return null instead of highlighting whole expression
    return null;
  }, [target, cleanedHighlightText, highlightRange, mappedHighlightSpan, highlightClass]);

  // Handle multiple spans from backend
  const highlightSpansList = useMemo(() => {
    if (!highlightSpansCp || !Array.isArray(highlightSpansCp) || highlightSpansCp.length === 0) {
      return null;
    }
    // Sort by start, merge overlapping spans
    const sorted = [...highlightSpansCp].sort((a, b) => a[0] - b[0]);
    const merged = [];
    for (const span of sorted) {
      if (merged.length === 0) {
        merged.push(span);
      } else {
        const last = merged[merged.length - 1];
        if (span[0] <= last[1]) {
          // Overlapping or adjacent, merge
          last[1] = Math.max(last[1], span[1]);
        } else {
          merged.push(span);
        }
      }
    }
    return merged;
  }, [highlightSpansCp]);

  if (!expression) return null;

  // Kolory dla różnych poziomów zagnieżdżenia
  const colors = [
    'text-purple-600',  // poziom 0 - fioletowy, lepiej się wyróżnia
    'text-blue-600',    // poziom 1  
    'text-green-600',   // poziom 2
    'text-orange-600',  // poziom 3
    'text-pink-600',    // poziom 4
    'text-indigo-600',  // poziom 5
    'text-teal-600',    // poziom 6
    'text-red-600',     // poziom 7
  ];

  const isInHighlight = (position) => {
    if (computedHighlightRange) {
      return position >= computedHighlightRange.start && position < computedHighlightRange.end;
    }
    if (highlightSpansList) {
      return highlightSpansList.some(span => position >= span[0] && position < span[1]);
    }
    return false;
  };

  const renderExpression = (expr) => {
    const result = [];
    let level = 0;
    let i = 0;
    let highlightBuffer = [];
    let highlightStart = -1;
    let inHighlight = false;

    while (i < expr.length) {
      const char = expr[i];
      const wasInHighlight = inHighlight;
      inHighlight = isInHighlight(i);
      
      // Zakończ poprzedni highlight span jeśli wychodzimy z zakresu
      if (wasInHighlight && !inHighlight && highlightBuffer.length > 0) {
        const className = computedHighlightRange?.class || highlightClass;
        result.push(
          <mark key={`highlight-${highlightStart}`} className={className}>
            {highlightBuffer.join('')}
          </mark>
        );
        highlightBuffer = [];
        highlightStart = -1;
      }
      
      // Rozpocznij nowy highlight span jeśli wchodzimy do zakresu
      if (!wasInHighlight && inHighlight) {
        highlightStart = i;
      }
      
      if (inHighlight) {
        // Gromadź znaki w buforze
        highlightBuffer.push(char);
        // Aktualizuj level dla nawiasów (ale nie renderuj jeszcze)
        if (char === '(') level++;
        else if (char === ')') level--;
      } else {
        // Renderuj normalnie poza highlightem
      if (char === '(') {
        const colorClass = colors[level % colors.length];
        result.push(
          <span key={i} className={`font-bold ${colorClass}`}>
            (
          </span>
        );
        level++;
      } else if (char === ')') {
        level--;
        const colorClass = colors[level % colors.length];
        result.push(
          <span key={i} className={`font-bold ${colorClass}`}>
            )
          </span>
        );
      } else {
        result.push(
          <span key={i}>
            {char}
          </span>
        );
      }
      }
      
      i++;
    }
    
    // Jeśli na końcu nadal jesteśmy w highlightcie, zamknij span
    if (inHighlight && highlightBuffer.length > 0) {
      const className = computedHighlightRange?.class || highlightClass;
      result.push(
        <mark key={`highlight-${highlightStart}`} className={className}>
          {highlightBuffer.join('')}
        </mark>
      );
    }

    return result;
  };

  return (
    <span className={`font-mono ${className}`}>
      {renderExpression(target)}
    </span>
  );
}
