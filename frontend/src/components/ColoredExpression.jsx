import React, { useMemo } from 'react';

/**
 * Komponent do wyświetlania wyrażeń logicznych z kolorowanymi nawiasami
 * Nawiasy są kolorowane według poziomów zagnieżdżenia
 */
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

export default function ColoredExpression({ 
  expression, 
  className = "", 
  highlightRange = null, 
  highlightText = null, 
  highlightSpan = null,
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

  // If highlightSpan is provided, it refers to canonExpression (before cleanExpression)
  // We need to map indices from original to cleaned string by computing the actual offset
  const mappedHighlightSpan = useMemo(() => {
    if (!highlightSpan || highlightSpan.start === undefined || highlightSpan.end === undefined) {
      return null;
    }
    
    // If we have canonExpression, the span refers to IT, not cleaned version
    if (!canonExpression) {
      // No canonExpression, so span refers to expression after cleanExpression
      return highlightSpan;
    }
    
    // Compute how cleanExpression transformed the string
    const cleanedCanon = cleanExpression(canonExpression);
    if (cleanedCanon === canonExpression) {
      // No transformation, span maps 1:1
      return highlightSpan;
    }
    
    // Transformation happened - need to compute offset mapping
    // Strategy: find how many characters were removed before each position
    const offsetMap = [];
    let origIdx = 0;
    let cleanIdx = 0;
    
    // Build map of how many chars were removed before each original index
    while (origIdx < canonExpression.length || cleanIdx < cleanedCanon.length) {
      if (origIdx < canonExpression.length && cleanIdx < cleanedCanon.length && 
          canonExpression[origIdx] === cleanedCanon[cleanIdx]) {
        // Characters match
        offsetMap[origIdx] = origIdx - cleanIdx;
        origIdx++;
        cleanIdx++;
      } else if (origIdx < canonExpression.length) {
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
      start: highlightSpan.start - offsetAtStart,
      end: highlightSpan.end - offsetAtEnd
    };
  }, [highlightSpan, canonExpression]);

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
      inHighlight = computedHighlightRange && i >= computedHighlightRange.start && i < computedHighlightRange.end;
      
      // Zakończ poprzedni highlight span jeśli wychodzimy z zakresu
      if (wasInHighlight && !inHighlight && highlightBuffer.length > 0) {
        result.push(
          <span key={`highlight-${highlightStart}`} className={computedHighlightRange.class}>
            {highlightBuffer.join('')}
          </span>
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
      result.push(
        <span key={`highlight-${highlightStart}`} className={computedHighlightRange.class}>
          {highlightBuffer.join('')}
        </span>
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
