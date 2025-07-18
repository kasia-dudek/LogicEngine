import React, { useState } from 'react';

function StartScreen({ onSubmit, onDefinitions }) {
  const [input, setInput] = useState('');
  const [error, setError] = useState('');

  const validate = (expr) => {
    if (!expr.trim()) return 'Wyrażenie nie może być puste.';
    if (/[^A-Za-z0-9¬∧∨→↔()\s]/.test(expr)) return 'Wyrażenie zawiera niedozwolone znaki.';
    // Możesz dodać więcej reguł walidacji
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
    // Standaryzacja: usuwanie zbędnych spacji
    const standardized = input.replace(/\s+/g, '');
    onSubmit(standardized);
  };

  // Kalkulator logiczny - przyciski
  const buttons = [
    'A', 'B', 'C', 'D', 'E', '0', '1',
    '¬', '∧', '∨', '→', '↔', '(', ')',
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

  return (
    <form onSubmit={handleSubmit} className="flex flex-col items-center gap-4">
      <input
        type="text"
        value={input}
        onChange={e => setInput(e.target.value)}
        className="border rounded px-3 py-2 w-80"
        placeholder="Wpisz wyrażenie logiczne..."
      />
      <div className="flex flex-wrap gap-2 max-w-xl justify-center mb-2">
        {buttons.map(b => (
          <button
            type="button"
            key={b}
            className="bg-gray-200 hover:bg-gray-300 rounded px-3 py-1 font-mono"
            onClick={() => handleButtonClick(b)}
          >
            {b}
          </button>
        ))}
      </div>
      {error && <div className="text-red-600">{error}</div>}
      <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded">Analizuj</button>
      <button type="button" className="text-blue-600 underline" onClick={onDefinitions}>Definicje pojęć</button>
    </form>
  );
}

export default StartScreen; 