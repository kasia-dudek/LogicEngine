import React from 'react';

export default function LawsPanel({ data, onPickStep, pickedIndex, onApplyLaw }) {
  const steps = data?.laws?.steps || data?.steps || [];
  const result = data?.laws?.result || data?.result;

  const applyAlternative = async (step, lawName, stepIndex) => {
    try {
      const apiUrl = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000';
      
      console.log(`Zastosuj alternatywne prawo: ${lawName} w kroku ${stepIndex}`);
      console.log('Step:', step);
      console.log('Path:', step.path);
      
      // Zastosuj alternatywne prawo
      const resp = await fetch(`${apiUrl}/laws_apply`, {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({
          expr: step.before_tree,   // UWAGA: używamy wyrażenia PRZED krokiem
          path: step.path,
          law: lawName
        })
      });
      
      const data = await resp.json();
      console.log('Response from /laws_apply:', data);
      
      if (!resp.ok || !data.ok) {
        // Pokaż błąd
        console.error('Błąd:', data.error);
        return;
      }
      
      // Mamy nowe wyrażenie po zastosowaniu alternatywy.
      // Teraz przelicz kroki od tego miejsca w górę:
      const resp2 = await fetch(`${apiUrl}/laws`, {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ expr: data.after_tree })
      });
      
      const sim = await resp2.json();
      console.log('Response from /laws:', sim);
      
      // Zbuduj nową listę kroków: poprzednie + nowe
      const newSteps = [
        ...steps.slice(0, stepIndex), // Zachowaj poprzednie kroki
        {
          ...step,
          law: lawName, // Zastąp nazwę prawa
          after_subexpr: data.after_subexpr, // Zastąp wynik
          after_tree: data.after_tree // Zastąp całe wyrażenie
        },
        ...sim.steps // Dodaj nowe kroki od nowego stanu
      ];
      
      console.log('Nowe kroki:', newSteps);
      
      // Zbuduj nowe dane
      const newLawsData = {
        ...sim,
        steps: newSteps,
        result: sim.result
      };
      
      // Zaktualizuj panel praw
      if (onApplyLaw) {
        onApplyLaw(newLawsData);
      }
      
    } catch (error) {
      console.error('Błąd podczas zastosowania alternatywy:', error);
    }
  };

  if (!steps.length) {
    return <div className="text-gray-500">Brak kroków lub nie wykryto miejsc do uproszczenia.</div>;
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="text-sm text-gray-600">
        Uproszczone: <span className="font-mono text-green-700 font-semibold">{result}</span>
      </div>
      <ol className="space-y-3">
        {steps.map((s, i) => (
          <li key={i} className={`p-3 rounded-xl border ${pickedIndex===i ? 'border-blue-500 bg-blue-50' : 'border-gray-200 bg-white'}`}>
            <div className="flex items-center justify-between">
              <div className="font-semibold text-blue-700">Krok {i+1}: {s.law}</div>
            </div>
            {s.note && <div className="text-xs text-gray-500 mt-1">{s.note}</div>}
            <div className="mt-2 text-sm">
              <span className="font-mono text-gray-600">{s.before_subexpr}</span>
              <span className="mx-2">→</span>
              <span className="font-mono text-green-700">{s.after_subexpr}</span>
            </div>
            {s.applicable_here.length > 0 && (
              <div className="text-xs text-gray-500 mt-2">
                Inne prawa możliwe w tym miejscu:&nbsp;
                {s.applicable_here.map((law) => (
                  <button
                    key={law}
                    onClick={() => applyAlternative(s, law, i)}
                    className="inline-flex items-center px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 border border-amber-300 mr-1 hover:bg-amber-200"
                    title={`Zastosuj: ${law}`}
                  >
                    {law}
                  </button>
                ))}
              </div>
            )}
          </li>
        ))}
      </ol>
    </div>
  );
} 