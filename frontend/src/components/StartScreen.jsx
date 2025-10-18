import React, { useState } from 'react';
import { OP_DEFS } from './ASTDisplay';

function StartScreen({ onSubmit, onDefinitions, onExamples, onHistory }) {
  const [input, setInput] = useState('');
  const [error, setError] = useState('');
  const [opTooltip, setOpTooltip] = useState({ visible: false, x: 0, y: 0, content: null });
  const wrapperRef = React.useRef(null);

  // Mapowanie alternatywnych znaków na standardowe operatory
  const ALT_OPS = [
    { re: /&/g, to: '∧' },
    { re: /\|/g, to: '∨' },
    { re: /~/g, to: '¬' },
    { re: /!/g, to: '¬' },
    { re: /=>/g, to: '→' },
    { re: /->/g, to: '→' },
    { re: /<=>/g, to: '↔' },
    { re: /<->/g, to: '↔' },
    { re: /\^/g, to: '⊕' },
  ];

  // Standaryzacja: zamiana alternatywnych znaków na standardowe
  const standardize = (expr) => {
    let s = expr;
    ALT_OPS.forEach(({ re, to }) => {
      s = s.replace(re, to);
    });
    return s;
  };

  // Sprawdzenie poprawności nawiasów
  const checkParentheses = (expr) => {
    let count = 0;
    for (let ch of expr) {
      if (ch === '(') count++;
      if (ch === ')') count--;
      if (count < 0) return false;
    }
    return count === 0;
  };

  const validate = (expr) => {
    if (!expr.trim()) return 'Wyrażenie nie może być puste.';
    const std = standardize(expr);
    // Niedozwolone znaki (po zamianie alternatyw)
    if (/[^A-Za-z0-9¬∧∨→↔⊕↑↓≡()\s]/.test(std)) return 'Wyrażenie zawiera niedozwolone znaki.';
    if (!checkParentheses(std)) return 'Nawiasy są niepoprawne lub niezrównoważone.';
    // Możesz dodać więcej reguł walidacji (np. podwójne operatory, puste nawiasy)
    return '';
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const err = validate(input);
    if (err) {
      setError(err);
      return;
    }
    setError('');
    // Standaryzacja: usuwanie zbędnych spacji i zamiana alternatywnych znaków
    const standardized = standardize(input.replace(/\s+/g, ''));
    onSubmit(standardized);
  };

  // Kalkulator logiczny - przyciski
  const buttons = [
    'A', 'B', 'C', 'D', 'E', '0', '1',
    '¬', '∧', '∨', '→', '↔', '⊕', '↑', '↓', '≡', '(', ')',
    'spacja', 'usuń'
  ];

  const handleButtonClick = (val) => {
    if (val === 'spacja') {
      setInput(input + ' ');
    } else if (val === 'usuń') {
      setInput(input.slice(0, -1));
    } else {
      setInput(input + val);
    }
  };

  // Funkcja do ustawiania tooltipa - stałe miejsce tuż po prawej stronie ramki kalkulatora
  const handleOpMouseEnter = (e, b) => {
    const wrapperRect = wrapperRef.current?.getBoundingClientRect();
    if (!wrapperRect) return;
    
    const tooltipHeight = 120;
    
    // Tuż po prawej stronie ramki kalkulatora, ale wewnątrz widocznego obszaru
    const left = wrapperRect.right - 350; // 240px szerokość tooltipa + 24px odstęp od prawej krawędzi panelu (więcej w lewo)
    const top = wrapperRect.top + (wrapperRect.height / 2) - (tooltipHeight / 2) - 100; // 20px wyżej
    
    setOpTooltip({
      visible: true,
      x: left,
      y: top,
      content: (
        <div>
          <div className="font-bold text-base mb-1">{OP_DEFS[b].name}</div>
          <div className="mb-2 text-xs">{OP_DEFS[b].desc}</div>
          <table className="border border-blue-200 rounded mb-1 text-xs">
            <tbody>
              {OP_DEFS[b].table.map((row, i) => (
                <tr key={i}>
                  {row.map((cell, j) => (
                    <td key={j} className={`px-2 py-1 border ${i === 0 ? 'bg-blue-100 font-semibold' : ''}`}>{cell}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-white flex flex-col items-center justify-center relative">
      <div ref={wrapperRef} className="max-w-2xl w-full bg-white rounded-3xl shadow-2xl p-10 border border-blue-100 animate-fade-in flex flex-col items-center relative">
        <h1 className="text-4xl font-extrabold mb-6 text-center text-blue-700 tracking-tight drop-shadow">Analiza wyrażeń logicznych</h1>
        <p className="mb-6 text-gray-600 text-center text-lg">Wprowadź wyrażenie logiczne i przeanalizuj je. Skorzystaj z przycisków operatorów, aby ułatwić wpisywanie.</p>
        <form onSubmit={handleSubmit} className="flex flex-col items-center gap-4 w-full">
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            className="border rounded px-3 py-2 w-full text-lg mb-2"
            placeholder="Wpisz wyrażenie logiczne..."
          />
          <div className="flex flex-wrap gap-2 max-w-xl justify-center mb-2 relative">
            {buttons.map(b => {
              const isOp = OP_DEFS[b];
              return (
                <button
                  type="button"
                  key={b}
                  className="bg-gray-200 hover:bg-gray-300 rounded px-3 py-1 font-mono"
                  onClick={() => handleButtonClick(b)}
                  onMouseEnter={isOp ? (e) => handleOpMouseEnter(e, b) : undefined}
                  onMouseLeave={isOp ? () => setOpTooltip({ visible: false, x: 0, y: 0, content: null }) : undefined}
                >
                  {b}
                </button>
              );
            })}
          </div>
          {error && <div className="text-red-600">{error}</div>}
          <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded w-full text-lg">Analizuj</button>
        </form>
        <div className="flex flex-col md:flex-row gap-4 w-full mt-8">
          <button
            type="button"
            className="w-full bg-blue-100 text-blue-700 py-3 rounded-xl hover:bg-blue-200 transition-all font-semibold text-lg shadow-sm border border-blue-100"
            onClick={onExamples}
          >
            Przykłady
          </button>
          <button
            type="button"
            className="w-full bg-gray-100 text-blue-700 py-3 rounded-xl hover:bg-blue-200 transition-all font-semibold text-lg shadow-sm border border-blue-100"
            onClick={onDefinitions}
          >
            <span role="img" aria-label="definitions">📖</span> Definicje pojęć
          </button>
          <button
            type="button"
            className="w-full bg-gray-100 text-blue-700 py-3 rounded-xl hover:bg-blue-200 transition-all font-semibold text-lg shadow-sm border border-blue-100"
            onClick={onHistory}
          >
            <span role="img" aria-label="history">🕑</span> Historia wyrażeń
          </button>
        </div>
        {/* Tooltip panel boczny */}
        {opTooltip.visible && (
          <div
            className="fixed z-[9999] px-4 py-4 rounded-2xl bg-blue-700 text-white text-xs font-semibold shadow-2xl animate-fade-in"
            style={{ 
              left: opTooltip.x, 
              top: opTooltip.y, 
              minWidth: 240, 
              maxWidth: 300 
            }}
          >
            {opTooltip.content}
          </div>
        )}
      </div>
    </div>
  );
}

export default StartScreen; 