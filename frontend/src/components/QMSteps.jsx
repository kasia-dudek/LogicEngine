import React from 'react';

function QMTable({ headers, rows }) {
  return (
    <table className="min-w-full border border-gray-300 rounded-xl mb-2 text-sm">
      <thead>
        <tr>
          {headers.map((h, i) => (
            <th key={i} className="px-3 py-2 border-b bg-blue-50 text-blue-700 font-semibold text-center">{h}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, i) => (
          <tr key={i}>
            {row.map((cell, j) => (
              <td key={j} className="px-3 py-2 border-b text-center">{cell}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function renderStep(step, idx) {
  const { data } = step;
  // Krok 1: mintermy
  if (step.step.includes('Znajdź mintermy')) {
    return (
      <div className="bg-white rounded-xl shadow p-4 mb-4 border border-blue-100 animate-fade-in">
        <div className="font-bold text-blue-700 mb-2">Krok {idx + 1}: {step.step}</div>
        <div className="mb-2 text-gray-700">{data.opis}</div>
        <QMTable
          headers={["Indeks", "Binarnie"]}
          rows={data.minterms.map(m => [m, m.toString(2)])}
        />
      </div>
    );
  }
  // Krok 2: grupowanie
  if (step.step.includes('Grupowanie mintermów')) {
    return (
      <div className="bg-white rounded-xl shadow p-4 mb-4 border border-blue-100 animate-fade-in">
        <div className="font-bold text-blue-700 mb-2">Krok {idx + 1}: {step.step}</div>
        <div className="mb-2 text-gray-700">{data.opis}</div>
        <div className="flex flex-wrap gap-4">
          {Object.entries(data.groups).map(([ones, arr], i) => (
            <div key={i} className="bg-blue-50 rounded-lg p-2 flex-1 min-w-[120px]">
              <div className="font-semibold text-blue-600 mb-1">{ones} jedynek</div>
              <div className="flex flex-col gap-1">
                {arr.map((bin, j) => <span key={j} className="font-mono text-base">{bin}</span>)}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }
  // Krok 3: prime implicants
  if (step.step.includes('implikantów pierwszorzędnych')) {
    return (
      <div className="bg-white rounded-xl shadow p-4 mb-4 border border-blue-100 animate-fade-in">
        <div className="font-bold text-blue-700 mb-2">Krok {idx + 1}: {step.step}</div>
        <div className="mb-2 text-gray-700">{data.opis}</div>
        <div className="mb-2 font-semibold text-blue-600">Prime implicants:</div>
        <QMTable
          headers={["Binarnie", "Mintermy", "Wyrażenie"]}
          rows={data.prime_implicants.map(pi => [
            <span className="font-mono">{pi.binary}</span>,
            pi.minterms.join(", "),
            <span className="font-mono">{pi.expr}</span>
          ])}
        />
      </div>
    );
  }
  // Krok 4: tabela pokrycia
  if (step.step.includes('Tabela pokrycia')) {
    const minterms = Object.keys(data.cover);
    const implicants = Array.from(new Set(minterms.flatMap(m => data.cover[m])));
    return (
      <div className="bg-white rounded-xl shadow p-4 mb-4 border border-blue-100 animate-fade-in">
        <div className="font-bold text-blue-700 mb-2">Krok {idx + 1}: {step.step}</div>
        <div className="mb-2 text-gray-700">{data.opis}</div>
        <QMTable
          headers={["Minterm", ...implicants]}
          rows={minterms.map(m => [
            m,
            ...implicants.map(pi => data.cover[m].includes(pi) ? <span className="text-green-600 font-bold">✔</span> : "")
          ])}
        />
      </div>
    );
  }
  // Krok 5: zasada implikanty
  if (step.step.includes('Zasada implikanty')) {
    return (
      <div className="bg-white rounded-xl shadow p-4 mb-4 border border-blue-100 animate-fade-in">
        <div className="font-bold text-blue-700 mb-2">Krok {idx + 1}: {step.step}</div>
        <div className="mb-2 text-gray-700">{data.opis}</div>
        <div className="mb-2 font-semibold text-blue-600">Niezbędne PI:</div>
        <ul className="list-disc ml-6">
          {data.essential.map((pi, i) => <li key={i} className="font-mono text-base text-blue-700">{pi}</li>)}
        </ul>
        <div className="mt-2 text-sm text-gray-600">Pokryte mintermy: {data.covered_minterms.join(", ")}</div>
      </div>
    );
  }
  // Krok 6: minimalne pokrycie
  if (step.step.includes('Minimalne pokrycie')) {
    return (
      <div className="bg-white rounded-xl shadow p-4 mb-4 border border-blue-100 animate-fade-in">
        <div className="font-bold text-blue-700 mb-2">Krok {idx + 1}: {step.step}</div>
        <div className="mb-2 text-gray-700">{data.opis}</div>
        <QMTable
          headers={["Binarnie", "Wyrażenie"]}
          rows={data.cover.map(c => [<span className="font-mono">{c.binary}</span>, <span className="font-mono">{c.expr}</span>])}
        />
      </div>
    );
  }
  // Krok 7: uproszczone wyrażenie
  if (step.step.includes('Uproszczone wyrażenie')) {
    return (
      <div className="bg-green-50 rounded-xl shadow p-4 mb-4 border border-green-200 animate-fade-in">
        <div className="font-bold text-green-700 mb-2">{step.step}</div>
        <div className="mb-2 text-gray-700">{data.opis}</div>
        <div className="text-2xl font-mono text-green-800 bg-white rounded-lg px-4 py-2 inline-block shadow">{data.result}</div>
      </div>
    );
  }
  // Krok 8: weryfikacja
  if (step.step.includes('Weryfikacja')) {
    return (
      <div className="bg-blue-50 rounded-xl shadow p-4 mb-4 border border-blue-200 animate-fade-in">
        <div className="font-bold text-blue-700 mb-2">{step.step}</div>
        <div className="mb-2 text-gray-700">{data.opis}</div>
        <div className={data.zgodność ? "text-green-700 font-bold" : "text-red-700 font-bold"}>
          {data.zgodność ? "Weryfikacja poprawna!" : "Błąd weryfikacji!"}
        </div>
      </div>
    );
  }
  // Domyślnie fallback na JSON
  return (
    <div className="bg-gray-100 rounded-xl shadow p-4 mb-4 border border-gray-200 animate-fade-in">
      <div className="font-bold text-gray-700 mb-2">Krok {idx + 1}: {step.step}</div>
      <pre className="text-xs text-gray-600 whitespace-pre-wrap">{JSON.stringify(data, null, 2)}</pre>
    </div>
  );
}

export default function QMSteps({ steps }) {
  if (!steps || steps.length === 0) {
    return <div className="text-gray-500">Brak danych do wyświetlenia kroków QM.</div>;
  }
  return (
    <div className="space-y-4">
      {steps.map((step, idx) => renderStep(step, idx))}
    </div>
  );
}