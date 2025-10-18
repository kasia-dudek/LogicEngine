// QMSteps.jsx — układ: pasek narzędzi u góry + jedna szeroka kolumna
import React from 'react';
import Glossary, { Tooltip } from './Glossary';
import InteractiveGuide from './InteractiveGuide';
import ConnectionVisualization from './ConnectionVisualization';
import AnimatedStep from './AnimatedStep';
import KeyConceptsSummary from './KeyConceptsSummary';

/* --- UI helpers --- */
function SectionTitle({ children }) {
  return (
    <h3 className="text-sm font-semibold uppercase tracking-wide text-blue-700 mb-2">
      {children}
    </h3>
  );
}

function StepCard({ title, subtitle, children, tone = 'default' }) {
  const tones = {
    default: 'bg-white border-blue-100',
    info: 'bg-blue-50 border-blue-200',
    success: 'bg-green-50 border-green-200',
  };
  const toneCls = tones[tone] || tones.default;
  return (
    <div className={`rounded-xl shadow p-4 border ${toneCls}`}>
      {title && <div className="font-bold text-blue-800 mb-1">{title}</div>}
      {subtitle && <div className="text-sm text-gray-600 mb-3">{subtitle}</div>}
      {children}
    </div>
  );
}

function InfoCallout({ children, color = 'blue' }) {
  const map = {
    blue: 'bg-blue-50 border-blue-200 text-gray-700',
    purple: 'bg-purple-50 border-purple-200 text-gray-700',
    green: 'bg-green-50 border-green-200 text-gray-700',
    yellow: 'bg-yellow-50 border-yellow-200 text-gray-700',
    orange: 'bg-orange-50 border-orange-200 text-gray-700',
    red: 'bg-red-50 border-red-200 text-gray-700',
    indigo: 'bg-indigo-50 border-indigo-200 text-gray-700',
    gray: 'bg-gray-50 border-gray-200 text-gray-700',
  };
  return (
    <div className={`text-sm p-3 rounded-lg border ${map[color] || map.blue}`}>
      {children}
    </div>
  );
}

function Table({ headers, rows, highlightCells = [] }) {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full border border-gray-200 rounded-xl text-sm">
        <thead>
          <tr>
            {headers.map((h, i) => (
              <th key={i} className="px-3 py-2 border-b bg-gray-50 text-gray-700 font-semibold text-center">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}>
              {row.map((cell, j) => {
                const isHighlighted = highlightCells.some(([ri, cj]) => ri === i && cj === j);
                return (
                  <td
                    key={j}
                    className={`px-3 py-2 border-b text-center ${isHighlighted ? 'bg-yellow-100 font-semibold' : ''}`}
                  >
                    {cell}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function TruthTable({ vars, rows }) {
  const headers = ['Indeks', 'Binarnie', ...vars, 'Wynik'];
  const minterms = rows.filter(r => r.result === 1).map(r => r.i);

  return (
    <div className="space-y-3">
      <InfoCallout color="blue">
        <strong>Tabela prawdy.</strong> Wszystkie kombinacje zmiennych i wynik funkcji.
        <span className="ml-1">Wiersze z wynikiem 1 to <Tooltip term="minterm">mintermy</Tooltip>.</span>
      </InfoCallout>

      <Table
        headers={headers}
        rows={rows.map(r => ([
          <span className="font-mono">{r.i}</span>,
          <span className="font-mono">{r.bin}</span>,
          ...r.vals.map((v, j) => <span className="font-mono" key={j}>{v}</span>),
          <span className={`font-mono ${r.result === 1 ? 'text-green-700 font-semibold' : 'text-gray-700'}`}>{r.result}</span>,
        ]))}
        highlightCells={rows
          .map((r, i) => (r.result === 1 ? [[i, headers.length - 1]] : []))
          .flat()}
      />

      <InfoCallout color="green">
        <strong>Mintermy:</strong> <span className="font-mono ml-1">m{minterms.join(', m')}</span>
      </InfoCallout>
    </div>
  );
}

/* --- Pasek narzędzi (jeden rząd, nad krokami) --- */
function ToolsBar() {
  return (
    <div className="w-full">
      <div className="rounded-xl border border-gray-200 bg-white shadow p-3">
        <div className="flex flex-wrap gap-3 items-stretch">
          <details className="group flex-1 min-w-[220px]">
            <summary className="cursor-pointer select-none px-3 py-2 rounded-lg bg-blue-50 border border-blue-200 text-blue-800 text-sm font-semibold hover:bg-blue-100">
              Skrót pojęć
            </summary>
            <div className="mt-3 p-3 rounded-lg border bg-gray-50">
              <KeyConceptsSummary />
            </div>
          </details>

          <details className="group flex-1 min-w-[220px]">
            <summary className="cursor-pointer select-none px-3 py-2 rounded-lg bg-indigo-50 border border-indigo-200 text-indigo-800 text-sm font-semibold hover:bg-indigo-100">
              Przewodnik interaktywny
            </summary>
            <div className="mt-3 p-3 rounded-lg border bg-gray-50">
              <InteractiveGuide />
            </div>
          </details>

          <details className="group flex-1 min-w-[220px]">
            <summary className="cursor-pointer select-none px-3 py-2 rounded-lg bg-slate-50 border border-slate-200 text-slate-800 text-sm font-semibold hover:bg-slate-100">
              Słownik
            </summary>
            <div className="mt-3 p-3 rounded-lg border bg-gray-50">
              <Glossary />
            </div>
          </details>
        </div>
      </div>
    </div>
  );
}

/* --- Render poszczególnych kroków --- */
function renderStep(step) {
  const { data } = step;

  if (step.step.includes('Tabela prawdy')) {
    return (
      <StepCard title={step.step} subtitle={data.opis}>
        <TruthTable vars={data.vars} rows={data.rows} />
      </StepCard>
    );
  }

  if (step.step.includes('Znajdź mintermy')) {
    return (
      <StepCard title={step.step} subtitle={data.opis}>
        <Table
          headers={['Indeks', 'Binarnie']}
          rows={data.minterms.map(m => [<span className="font-mono">m{m}</span>, <span className="font-mono">{m.toString(2)}</span>])}
        />
      </StepCard>
    );
  }

  if (step.step.includes('Grupowanie mintermów')) {
    return (
      <StepCard title={step.step} subtitle={data.opis}>
        <InfoCallout color="purple">
          Grupowanie wg liczby jedynek w zapisie <Tooltip term="binarnie">binarnym</Tooltip>. Łączone są wyłącznie grupy sąsiednie (różnica 1 bitu).
        </InfoCallout>

        <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {Object.entries(data.groups).map(([ones, arr], i) => (
            <div key={i} className="bg-blue-50 rounded-lg p-3 border border-blue-200">
              <div className="font-semibold text-blue-700 mb-2 text-center">{ones} jedynek</div>
              <div className="flex flex-col gap-1">
                {arr.map((bin, j) => {
                  const idx = parseInt(bin, 2);
                  return (
                    <div key={j} className="flex items-center justify-between bg-white rounded px-2 py-1 border">
                      <span className="font-mono text-sm text-gray-700">m{idx}</span>
                      <span className="font-mono text-sm text-blue-800">{bin}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </StepCard>
    );
  }

  if (step.step.includes('implikantów pierwszorzędnych')) {
    const pi = data.prime_implicants || [];
    return (
      <StepCard title={step.step} subtitle={data.opis}>
        <InfoCallout color="orange">
          Łączenie mintermów różniących się jednym bitem → w różniącym miejscu wstaw „-”.
          <Tooltip term="implikant pierwszorzędny">PI</Tooltip> nie da się dalej połączyć.
        </InfoCallout>

        {(data.rounds || []).map((r) => (
          <div key={r.round} className="mt-4">
            <SectionTitle>Runda {r.round}</SectionTitle>
            <ConnectionVisualization pairs={r.pairs} round={r.round} />
          </div>
        ))}

        <div className="mt-4">
          <SectionTitle>Lista PI</SectionTitle>
          <Table
            headers={['Reprezentacja binarna', 'Pokryte mintermy', 'Wyrażenie']}
            rows={pi.map(p => [
              <span className="font-mono">{p.binary}</span>,
              <span className="text-xs">m{Array.isArray(p.minterms) ? p.minterms.join(', m') : p.minterms}</span>,
              <span className="font-mono font-semibold text-blue-700">{p.expr}</span>,
            ])}
          />
        </div>
      </StepCard>
    );
  }

  if (step.step.includes('Tabela pokrycia')) {
    const minterms = Object.keys(data.cover);
    const implicants = Array.from(new Set(minterms.flatMap(m => data.cover[m])));

    const essential = new Set();
    minterms.forEach(m => {
      if (data.cover[m].length === 1) essential.add(data.cover[m][0]);
    });

    return (
      <StepCard title={step.step} subtitle={data.opis}>
        <InfoCallout color="indigo">
          Tabela pokazuje, które PI pokrywają dane mintermy. Kolumna „istotna” jest jedynym pokryciem pewnego mintermu.
        </InfoCallout>

        <div className="mt-3 overflow-x-auto">
          <table className="min-w-full border border-gray-200 rounded-xl text-sm">
            <thead>
              <tr>
                <th className="px-3 py-2 border-b bg-gray-50 text-gray-700 text-center">Minterm</th>
                {implicants.map(pi => (
                  <th
                    key={pi}
                    className={`px-3 py-2 border-b text-center ${essential.has(pi) ? 'bg-green-100 text-green-800' : 'bg-gray-50 text-gray-700'}`}
                  >
                    {pi}{essential.has(pi) && <span className="block text-[10px]">(istotny)</span>}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {minterms.map(m => {
                const lonely = data.cover[m].length === 1;
                return (
                  <tr key={m} className={lonely ? 'bg-orange-50' : ''}>
                    <td className={`px-3 py-2 border-b text-center font-mono ${lonely ? 'text-orange-700 font-semibold' : ''}`}>
                      m{m}{lonely && <span className="block text-[10px] text-orange-600">samotny</span>}
                    </td>
                    {implicants.map(pi => (
                      <td key={pi} className={`px-3 py-2 border-b text-center ${lonely && essential.has(pi) ? 'bg-green-200' : ''}`}>
                        {data.cover[m].includes(pi) ? <span className="font-bold text-green-700">✔</span> : ''}
                      </td>
                    ))}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </StepCard>
    );
  }

  if (step.step.includes('Implikanty istotne') || step.step.includes('Zasada implikanty')) {
    return (
      <StepCard title="Krok 5: Implikanty istotne" subtitle={data.opis}>
        {data.essential?.length ? (
          <div className="grid gap-2">
            {data.essential.map((pi, i) => (
              <div key={i} className="bg-green-50 border border-green-200 rounded-lg p-3 flex items-center gap-2">
                <span className="text-green-700">✓</span>
                <span className="font-mono font-semibold text-green-800">{pi}</span>
              </div>
            ))}
          </div>
        ) : (
          <InfoCallout color="gray">Brak implikantów istotnych — przejście do metody Petricka.</InfoCallout>
        )}
        {data.covered_minterms?.length > 0 && (
          <InfoCallout color="blue">
            <strong>Pokryte mintermy:</strong> <span className="font-mono ml-1">m{data.covered_minterms.join(', m')}</span>
          </InfoCallout>
        )}
      </StepCard>
    );
  }

  if (step.step.includes('Minimalne pokrycie')) {
    return (
      <StepCard title={step.step} subtitle={data.opis}>
        <InfoCallout color="purple">
          <Tooltip term="metoda Petricka">Metoda Petricka</Tooltip> wybiera najmniejszy zbiór PI pokrywający wszystkie mintermy.
        </InfoCallout>
        <div className="mt-3">
          <Table
            headers={['Reprezentacja binarna', 'Wyrażenie logiczne']}
            rows={data.cover.map(c => [
              <span className="font-mono">{c.binary}</span>,
              <span className="font-mono font-semibold text-blue-700">{c.expr}</span>
            ])}
          />
        </div>
      </StepCard>
    );
  }

  if (step.step.includes('Uproszczone wyrażenie')) {
    return (
      <StepCard title="Wynik" tone="success">
        <div className="text-center">
          <div className="text-2xl font-mono text-green-800 bg-white rounded-lg px-5 py-3 inline-block shadow border border-green-200">
            {data.result}
          </div>
          <div className="mt-2 text-xs text-gray-600">
            Zminimalizowana postać <Tooltip term="DNF">DNF</Tooltip>.
          </div>
        </div>
      </StepCard>
    );
  }

  if (step.step.includes('Weryfikacja')) {
    return null;
  }

  return (
    <StepCard title={step.step}>
      <pre className="text-xs text-gray-600 whitespace-pre-wrap">
        {JSON.stringify(data, null, 2)}
      </pre>
    </StepCard>
  );
}

/* --- Główny komponent --- */
export default function QMSteps({ steps }) {
  if (!steps || steps.length === 0) {
    return <div className="text-gray-500">Brak danych do wyświetlenia kroków QM.</div>;
  }

  return (
    <div className="space-y-4">
      {/* Pasek narzędzi w jednym rzędzie */}
      <ToolsBar />

      {/* Kroki w jednej, szerokiej kolumnie */}
      <div className="space-y-4">
        {steps.map((step, idx) => (
          <AnimatedStep key={idx} stepNumber={idx + 1} isVisible={true}>
            {renderStep(step)}
          </AnimatedStep>
        ))}
      </div>
    </div>
  );
}
