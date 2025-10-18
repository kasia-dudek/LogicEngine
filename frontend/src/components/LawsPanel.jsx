import React from 'react';

export default function LawsPanel({ data, onPickStep, pickedIndex, onApplyLaw }) {
  const steps = data?.laws?.steps || data?.steps || [];
  const result = data?.laws?.result || data?.result;

  const applyAlternative = async (step, lawName, stepIndex) => {
    try {
      const apiUrl = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000';
      
      
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
        body: JSON.stringify({ expr: data.after_tree, mode: 'mixed' })
      });
      
      const sim = await resp2.json();
      
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
              {/* Source indicator */}
              <div className="flex items-center gap-2">
                {s.source === 'axiom' && (
                  <span className="px-2 py-1 text-xs rounded-full bg-purple-100 text-purple-800 border border-purple-300">
                    Aksjomat
                  </span>
                )}
                {s.source === 'algebraic' && (
                  <span className="px-2 py-1 text-xs rounded-full bg-green-100 text-green-800 border border-green-300">
                    Algebraiczne
                  </span>
                )}
              </div>
            </div>
            {s.note && <div className="text-xs text-gray-500 mt-1">{s.note}</div>}
            
            {/* Axiom details */}
            {s.source === 'axiom' && s.axiom_id && (
              <div className="mt-2 p-2 bg-purple-50 rounded-lg border border-purple-200">
                <div className="text-xs text-purple-700 font-semibold">
                  Aksjomat {s.axiom_id} ({s.axiom_name || `A${s.axiom_id}`})
                </div>
                {s.axiom_subst && Object.keys(s.axiom_subst).length > 0 && (
                  <div className="text-xs text-purple-600 mt-1">
                    Podstawienie: {Object.entries(s.axiom_subst).map((entry) => 
                      `${entry[0]} := ${entry[1].name || entry[1]}`
                    ).join(', ')}
                  </div>
                )}
              </div>
            )}
            
            {/* Derived from axioms for algebraic steps */}
            {s.source === 'algebraic' && s.derived_from_axioms && s.derived_from_axioms.length > 0 && (
              <div className="mt-2 p-2 bg-blue-50 rounded-lg border border-blue-200">
                <div className="text-xs text-blue-700">
                  Pochodne z aksjomatów: {s.derived_from_axioms.join(', ')}
                </div>
              </div>
            )}
            
            <div className="mt-2 text-sm">
              <div className="mb-2">
                <span className="text-xs text-gray-500 font-semibold">Podwyrażenie:</span>
                <div className="mt-1">
                  <span className="font-mono text-gray-600">{s.before_subexpr}</span>
                  <span className="mx-2">→</span>
                  <span className="font-mono text-green-700">{s.after_subexpr}</span>
                </div>
              </div>
              
              <div className="border-t pt-2">
                <span className="text-xs text-gray-500 font-semibold">Całe wyrażenie po kroku:</span>
                <div className="mt-1 font-mono text-blue-700 bg-blue-50 px-2 py-1 rounded border">
                  {s.after_tree}
                </div>
              </div>
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