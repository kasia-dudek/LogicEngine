import React, { useMemo } from 'react';

/**
 * Komponent do wyświetlania wyrażeń logicznych z kolorowanymi nawiasami
 * Nawiasy są kolorowane według poziomów zagnieżdżenia
 */
export default function ColoredExpression({ expression, className = "", highlightRange = null, highlightText = null, highlightClass = "" }) {
  // 1) Delikatne czyszczenie nawiasów bez kosztownych obliczeń
  //    - (A) -> A
  //    - (¬A) -> ¬A
  //    - ((...)) -> (...)
  //    - Usuwamy wielokrotne podwójne nawiasy w granicach maxIterations, aby uniknąć pętli
  const cleanedExpression = useMemo(() => {
    if (!expression) return '';
    
    try {
      let result = String(expression);

      // Szybkie wyjście dla bardzo krótkich wyrażeń
      if (result.length < 4) return result;

      // Usuwanie prostych przypadków w ograniczonej pętli
      const maxIterations = 6;
      for (let i = 0; i < maxIterations; i++) {
        const before = result;

        // (A) -> A  (pojedynczy literal)
        result = result.replace(/\(([A-Z])\)/g, '$1');

        // (¬A) -> ¬A  (negacja pojedynczego literalu)
        result = result.replace(/\(¬([A-Z])\)/g, '¬$1');

        // ((X)) -> (X)  (redukcja podwójnych nawiasów bez zagnieżdżeń wewnątrz matcha)
        result = result.replace(/\(\(([^()]+)\)\)/g, '($1)');

        // (X) -> X  (usunięcie zewnętrznych nawiasów jeśli całe wyrażenie jest w jednym nawiasie)
        if (result.startsWith('(') && result.endsWith(')')) {
          const inner = result.slice(1, -1);
          // Sprawdź czy nawiasy są zbalansowane w środku
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

        if (result === before) break; // nic się nie zmieniło → koniec
      }

      return result;
    } catch (_) {
      // W razie jakiegokolwiek problemu użyj oryginału — bezpieczeństwo i responsywność ważniejsze
      return String(expression);
    }
  }, [expression]);

  // Oblicz highlightRange z highlightText po czyszczeniu wyrażenia
  const computedHighlightRange = useMemo(() => {
    if (highlightRange) return highlightRange;
    if (highlightText && cleanedExpression) {
      // Normalizuj highlightText tak samo jak wyrażenie (usuń spacje)
      const normalizedHighlight = String(highlightText).replace(/\s+/g, '').trim();
      const normalizedExpression = cleanedExpression.replace(/\s+/g, '').trim();
      
      let index = normalizedExpression.indexOf(normalizedHighlight);
      if (index !== -1) {
        return {
          start: index,
          end: index + normalizedHighlight.length,
          class: highlightClass || "bg-yellow-100"
        };
      }
      
      // Jeśli nie znaleziono, spróbuj bez zewnętrznych nawiasów w highlightText
      if (normalizedHighlight.startsWith('(') && normalizedHighlight.endsWith(')')) {
        const highlightWithoutParens = normalizedHighlight.slice(1, -1);
        index = normalizedExpression.indexOf(highlightWithoutParens);
        if (index !== -1) {
          return {
            start: index,
            end: index + highlightWithoutParens.length,
            class: highlightClass || "bg-yellow-100"
          };
        }
      }
    }
    return null;
  }, [cleanedExpression, highlightRange, highlightText, highlightClass]);

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
          <span key={`highlight-${highlightStart}`} className={`${computedHighlightRange.class} px-1 rounded border`}>
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
        <span key={`highlight-${highlightStart}`} className={`${computedHighlightRange.class} px-1 rounded border`}>
          {highlightBuffer.join('')}
        </span>
      );
    }

    return result;
  };

  return (
    <span className={`font-mono ${className}`}>
      {renderExpression(cleanedExpression)}
    </span>
  );
}
