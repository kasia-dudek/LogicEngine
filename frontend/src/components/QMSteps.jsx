import React from 'react';
import { Tooltip } from './Glossary';
import Glossary from './Glossary';
import ProgressIndicator from './ProgressIndicator';
import InteractiveGuide from './InteractiveGuide';
import ConnectionVisualization from './ConnectionVisualization';
import AnimatedStep from './AnimatedStep';
import KeyConceptsSummary from './KeyConceptsSummary';

function QMTable({ headers, rows, highlightCells = [] }) {
  return (
    <table className="min-w-full border border-gray-300 rounded-xl mb-2 text-sm">
      <thead>
        <tr>
          {headers.map((h, i) => (
            <th
              key={i}
              className="px-3 py-2 border-b bg-blue-50 text-blue-700 font-semibold text-center"
            >
              {h}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, i) => (
          <tr key={i}>
            {row.map((cell, j) => {
              const isHighlighted = highlightCells.some(([rowIdx, colIdx]) => rowIdx === i && colIdx === j);
              return (
                <td 
                  key={j} 
                  className={`px-3 py-2 border-b text-center ${
                    isHighlighted ? 'bg-yellow-100 font-bold' : ''
                  }`}
                >
                  {cell}
                </td>
              );
            })}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function TruthTable({ vars, rows }) {
  const headers = ['Indeks', 'Binarnie', ...vars, 'Wynik'];
  return (
    <div className="mb-4">
      <div className="mb-2 text-sm text-gray-600 bg-blue-50 p-3 rounded-lg border border-blue-200">
        <strong>💡 Co to jest tabela prawdy?</strong><br/>
        Tabela prawdy pokazuje wszystkie możliwe kombinacje wartości zmiennych i wynik funkcji logicznej. 
        <Tooltip term="minterm">Mintermy</Tooltip> to wiersze z wynikiem 1 - reprezentują one przypadki, gdy funkcja jest prawdziwa.
      </div>
      <table className="min-w-full border border-gray-300 rounded-xl mb-2 text-sm">
        <thead>
          <tr>
            {headers.map((h, i) => (
              <th
                key={i}
                className="px-3 py-2 border-b bg-blue-50 text-blue-700 font-semibold text-center"
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr
              key={i}
              className={r.result === 1 ? 'bg-green-50' : ''}
              title={r.result === 1 ? 'Minterm' : 'Nie-minterm'}
            >
              <td className="px-3 py-2 border-b text-center font-mono">{r.i}</td>
              <td className="px-3 py-2 border-b text-center font-mono">{r.bin}</td>
              {r.vals.map((v, j) => (
                <td key={j} className="px-3 py-2 border-b text-center font-mono">
                  {v}
                </td>
              ))}
              <td
                className={
                  'px-3 py-2 border-b text-center font-mono ' +
                  (r.result === 1 ? 'text-green-700 font-bold' : 'text-gray-700')
                }
              >
                {r.result}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="text-sm text-gray-600 bg-green-50 p-2 rounded border border-green-200">
        <strong>✅ Zaznaczone (zielone) wiersze to <Tooltip term="minterm">mintermy</Tooltip>:</strong> 
        <span className="font-mono ml-2">{rows.filter(r => r.result === 1).map(r => r.i).join(', ')}</span>
      </div>
    </div>
  );
}

function Collapsible({ title, children }) {
  return (
    <details className="mb-2 border border-gray-200 rounded-lg bg-white">
      <summary className="px-3 py-2 cursor-pointer select-none text-sm font-semibold text-blue-700">
        {title}
      </summary>
      <div className="px-3 py-2">{children}</div>
    </details>
  );
}

function renderStep(step) {
  const { data } = step;

  // Krok 1: tabela prawdy i mintermy
  if (step.step.includes('Tabela prawdy')) {
    return (
      <div className="bg-white rounded-xl shadow p-4 mb-4 border border-blue-100 animate-fade-in">
        <div className="font-bold text-blue-700 mb-2">{step.step}</div>
        <div className="mb-3 text-gray-700">{data.opis}</div>
        <TruthTable vars={data.vars} rows={data.rows} />
        <div className="text-sm text-gray-600">
          Zaznaczone (zielone) wiersze to mintermy:&nbsp;
          <span className="font-mono">{data.minterms.join(', ')}</span>
        </div>
      </div>
    );
  }

  // Krok 1 (stare nazwy) — fallback na poprzednie brzmienie
  if (step.step.includes('Znajdź mintermy')) {
    return (
      <div className="bg-white rounded-xl shadow p-4 mb-4 border border-blue-100 animate-fade-in">
        <div className="font-bold text-blue-700 mb-2">{step.step}</div>
        <div className="mb-2 text-gray-700">{data.opis}</div>
        <QMTable
          headers={['Indeks', 'Binarnie']}
          rows={data.minterms.map((m) => [m, m.toString(2)])}
        />
      </div>
    );
  }

  // Krok 2: grupowanie
  if (step.step.includes('Grupowanie mintermów')) {
    return (
      <div className="bg-white rounded-xl shadow p-4 mb-4 border border-blue-100 animate-fade-in">
        <div className="font-bold text-blue-700 mb-2">{step.step}</div>
        <div className="mb-3 text-gray-700">{data.opis}</div>
        
        <div className="mb-4 text-sm text-gray-600 bg-purple-50 p-3 rounded-lg border border-purple-200">
          <strong>🔍 Dlaczego grupujemy?</strong><br/>
          <Tooltip term="grupowanie">Grupowanie</Tooltip> mintermów według liczby jedynek w reprezentacji <Tooltip term="binarnie">binarnej</Tooltip> 
          pozwala nam efektywnie znajdować pary, które różnią się tylko jedną pozycją. 
          Tylko mintermy z sąsiednich grup mogą być łączone!
        </div>
        
        <div className="flex flex-wrap gap-4">
          {Object.entries(data.groups).map(([ones, arr], i) => (
            <div key={i} className="bg-blue-50 rounded-lg p-3 flex-1 min-w-[160px] border border-blue-200">
              <div className="font-semibold text-blue-600 mb-2 text-center bg-blue-100 rounded px-2 py-1">
                {ones} jedynek
                <div className="text-xs text-blue-500 mt-1">
                  {ones === '0' ? 'Brak jedynek' : ones === '1' ? 'Jedna jedynka' : `${ones} jedynki`}
                </div>
              </div>
              <div className="flex flex-col gap-2">
                {arr.map((bin, j) => {
                  const mintermIndex = parseInt(bin, 2);
                  return (
                    <div key={j} className="flex items-center justify-between bg-white rounded px-2 py-1 border hover:bg-blue-50 transition-colors">
                      <span className="font-mono text-sm text-gray-700">m{mintermIndex}</span>
                      <span className="font-mono text-sm text-blue-800">{bin}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
        
        <div className="mt-4 text-sm text-gray-600 bg-yellow-50 p-3 rounded border border-yellow-200">
          <strong>💡 Wskazówka:</strong> W następnym kroku będziemy łączyć mintermy z sąsiednich grup (np. grupa z 1 jedynką z grupą z 2 jedynkami). 
          Każde połączenie zastąpi różniącą się pozycję myślnikiem (-).
        </div>
      </div>
    );
  }

  // Krok 3: PI — najpierw proces łączenia, potem wynik
  if (step.step.includes('implikantów pierwszorzędnych')) {
    const pi = data.prime_implicants || [];
    return (
      <div className="bg-white rounded-xl shadow p-4 mb-4 border border-blue-100 animate-fade-in">
        <div className="font-bold text-blue-700 mb-2">{step.step}</div>
        <div className="mb-3 text-gray-700">{data.opis}</div>

        <div className="mb-4 text-sm text-gray-600 bg-orange-50 p-3 rounded-lg border border-orange-200">
          <strong>🔄 Proces łączenia:</strong><br/>
          Łączymy <Tooltip term="minterm">mintermy</Tooltip> różniące się tylko jedną pozycją. 
          Różniącą się pozycję zastępujemy myślnikiem (-). 
          <Tooltip term="implikant pierwszorzędny">Implikanty pierwszorzędne</Tooltip> to te, których nie da się już dalej uproscić.
        </div>

        {/* Najpierw pokazujemy proces łączenia */}
        {(data.rounds || []).map((r) => (
          <div key={r.round} className="mb-4">
            <div className="font-semibold text-purple-600 mb-2 bg-purple-50 p-2 rounded border border-purple-200">
              Runda {r.round}: <Tooltip term="łączenie">Łączenie</Tooltip> mintermów
            </div>
            <ConnectionVisualization pairs={r.pairs} round={r.round} />
          </div>
        ))}

        {/* Potem pokazujemy końcowe implikanty pierwszorzędne */}
        <div className="mt-4 border-t pt-4">
          <div className="font-semibold text-green-600 mb-2 bg-green-50 p-2 rounded border border-green-200">
            Ostateczne <Tooltip term="implikant pierwszorzędny">implikanty pierwszorzędne</Tooltip>
          </div>
          <div className="mb-3 text-sm text-gray-600 bg-green-50 p-2 rounded border border-green-200">
            <strong>✅ Co to oznacza?</strong> Te implikanty nie mogą być już dalej uproszczone. 
            Każdy z nich pokrywa pewne mintermy i będzie kandydatem do końcowego rozwiązania.
          </div>
          <QMTable
            headers={['Reprezentacja binarna', 'Pokryte mintermy', 'Wyrażenie logiczne']}
            rows={pi.map((p) => [
              <span className="font-mono text-sm">{p.binary}</span>,
              <span className="text-xs text-gray-600">m{Array.isArray(p.minterms) ? p.minterms.join(', m') : p.minterms}</span>,
              <span className="font-mono text-sm font-bold text-blue-700">{p.expr}</span>,
            ])}
          />
        </div>
      </div>
    );
  }

  // Krok 4: tabela pokrycia z zaznaczonymi istotnymi
  if (step.step.includes('Tabela pokrycia')) {
    const minterms = Object.keys(data.cover);
    const implicants = Array.from(new Set(minterms.flatMap((m) => data.cover[m])));
    
    // Znajdź implikanty istotne (te które pokrywają tylko jeden minterm)
    const essentialImplicants = new Set();
    minterms.forEach(m => {
      if (data.cover[m].length === 1) {
        essentialImplicants.add(data.cover[m][0]);
      }
    });

    return (
      <div className="bg-white rounded-xl shadow p-4 mb-4 border border-blue-100 animate-fade-in">
        <div className="font-bold text-blue-700 mb-2">{step.step}</div>
        <div className="mb-3 text-gray-700">{data.opis}</div>
        
        <div className="mb-4 text-sm text-gray-600 bg-indigo-50 p-3 rounded-lg border border-indigo-200">
          <strong>📊 Co to jest tabela pokrycia?</strong><br/>
          <Tooltip term="tabela pokrycia">Tabela pokrycia</Tooltip> pokazuje, które <Tooltip term="implikant pierwszorzędny">implikanty pierwszorzędne</Tooltip> 
          pokrywają które <Tooltip term="minterm">mintermy</Tooltip>. Używamy jej do znajdowania <Tooltip term="implikant istotny">implikantów istotnych</Tooltip> 
          i minimalnego pokrycia wszystkich mintermów.
        </div>
        
        <div className="mb-3 text-sm text-orange-600 bg-orange-50 p-3 rounded border border-orange-200">
          <strong>🎯 Klucz do odczytania tabeli:</strong><br/>
          <span className="inline-block bg-green-100 text-green-700 px-2 py-1 rounded mr-2">Kolumny zielone</span> = <Tooltip term="implikant istotny">implikanty istotne</Tooltip><br/>
          <span className="inline-block bg-orange-100 text-orange-700 px-2 py-1 rounded mr-2">Wiersze pomarańczowe</span> = mintermy pokryte tylko przez jeden implikant (samotne)
        </div>
        
        <div className="overflow-x-auto">
          <table className="min-w-full border border-gray-300 rounded-xl mb-2 text-sm">
            <thead>
              <tr>
                <th className="px-3 py-2 border-b bg-blue-50 text-blue-700 font-semibold text-center">Minterm</th>
                {implicants.map((pi) => (
                  <th 
                    key={pi} 
                    className={`px-3 py-2 border-b font-semibold text-center ${
                      essentialImplicants.has(pi) 
                        ? 'bg-green-100 text-green-700' 
                        : 'bg-blue-50 text-blue-700'
                    }`}
                  >
                    {pi}
                    {essentialImplicants.has(pi) && <span className="text-xs block">(istotny)</span>}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {minterms.map((m) => {
                const isEssentialRow = data.cover[m].length === 1;
                return (
                  <tr key={m} className={isEssentialRow ? 'bg-orange-50' : ''}>
                    <td className={`px-3 py-2 border-b text-center font-mono ${
                      isEssentialRow ? 'text-orange-700 font-bold' : 'text-gray-700'
                    }`}>
                      m{m}
                      {isEssentialRow && <span className="text-xs block text-orange-600">(samotny)</span>}
                    </td>
                    {implicants.map((pi) => (
                      <td key={pi} className={`px-3 py-2 border-b text-center ${
                        isEssentialRow && essentialImplicants.has(pi) ? 'bg-green-200' : ''
                      }`}>
                        {data.cover[m].includes(pi) ? (
                          <span className={`font-bold ${
                            isEssentialRow && essentialImplicants.has(pi) ? 'text-green-800' : 'text-green-600'
                          }`}>
                            ✔
                          </span>
                        ) : (
                          ''
                        )}
                      </td>
                    ))}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        
        <div className="mt-3 text-sm text-gray-600 bg-blue-50 p-2 rounded border border-blue-200">
          <strong>💡 Wskazówka:</strong> Szukamy mintermów, które są pokryte tylko przez jeden implikant (wiersze pomarańczowe). 
          Te implikanty muszą być wybrane - to są <Tooltip term="implikant istotny">implikanty istotne</Tooltip>!
        </div>
      </div>
    );
  }

  // Krok 5: implikanty istotne (obsłuż obie nazwy)
  if (step.step.includes('Implikanty istotne') || step.step.includes('Zasada implikanty')) {
    return (
      <div className="bg-white rounded-xl shadow p-4 mb-4 border border-blue-100 animate-fade-in">
        <div className="font-bold text-blue-700 mb-2">{step.step}</div>
        <div className="mb-3 text-gray-700">{data.opis}</div>
        
        <div className="mb-4 text-sm text-gray-600 bg-red-50 p-3 rounded-lg border border-red-200">
          <strong>⚠️ Definicja <Tooltip term="implikant istotny">implikantu istotnego</Tooltip>:</strong><br/>
          To taki <Tooltip term="implikant pierwszorzędny">implikant pierwszorzędny</Tooltip>, który jest jedynym pokryciem pewnego <Tooltip term="minterm">mintermu</Tooltip>. 
          <strong>Musimy go wybrać, bo inaczej ten minterm nie będzie pokryty w końcowym rozwiązaniu!</strong>
        </div>
        
        {data.essential.length ? (
          <div className="mb-4">
            <div className="font-semibold text-green-600 mb-3 bg-green-50 p-2 rounded border border-green-200">
              ✅ Znalezione <Tooltip term="implikant istotny">implikanty istotne</Tooltip>:
            </div>
            <div className="grid gap-3">
              {data.essential.map((pi, i) => (
                <div key={i} className="bg-green-100 border-2 border-green-300 rounded-lg p-4 flex items-center shadow-sm">
                  <span className="text-green-700 font-bold mr-3 text-lg">✓</span>
                  <div>
                    <span className="font-mono text-lg font-bold text-green-800">{pi}</span>
                    <div className="text-sm text-green-600 mt-1">
                      Ten implikant musi być wybrany!
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="text-sm text-gray-600 bg-gray-50 p-3 rounded border">
            <strong>ℹ️ Brak implikantów istotnych</strong> - każdy minterm może być pokryty przez więcej niż jeden implikant. 
            W takim przypadku będziemy musieli użyć <Tooltip term="metoda Petricka">metody Petricka</Tooltip> do znalezienia minimalnego pokrycia.
          </div>
        )}
        
        {data.covered_minterms && data.covered_minterms.length > 0 && (
          <div className="mt-3 text-sm text-gray-600 bg-blue-50 p-3 rounded border border-blue-200">
            <strong>📋 Pokryte mintermy przez implikanty istotne:</strong> 
            <span className="font-mono ml-2">m{data.covered_minterms.join(', m')}</span>
          </div>
        )}
      </div>
    );
  }

  // Krok 6: minimalne pokrycie
  if (step.step.includes('Minimalne pokrycie')) {
    return (
      <div className="bg-white rounded-xl shadow p-4 mb-4 border border-blue-100 animate-fade-in">
        <div className="font-bold text-blue-700 mb-2">{step.step}</div>
        <div className="mb-3 text-gray-700">{data.opis}</div>
        
        <div className="mb-4 text-sm text-gray-600 bg-purple-50 p-3 rounded-lg border border-purple-200">
          <strong>🎯 <Tooltip term="metoda Petricka">Metoda Petricka</Tooltip> w akcji:</strong><br/>
          Wybieramy najmniejszy zestaw <Tooltip term="implikant pierwszorzędny">implikantów pierwszorzędnych</Tooltip>, 
          który pokrywa wszystkie <Tooltip term="minterm">mintermy</Tooltip>. 
          To daje nam minimalne pokrycie - najkrótsze możliwe wyrażenie logiczne.
        </div>
        
        <QMTable
          headers={['Reprezentacja binarna', 'Wyrażenie logiczne']}
          rows={data.cover.map((c) => [
            <span className="font-mono text-sm">{c.binary}</span>,
            <span className="font-mono text-sm font-bold text-blue-700">{c.expr}</span>,
          ])}
        />
        
        <div className="mt-3 text-sm text-gray-600 bg-green-50 p-2 rounded border border-green-200">
          <strong>✅ Wybrane implikanty:</strong> Te implikanty tworzą minimalne pokrycie wszystkich mintermów.
        </div>
      </div>
    );
  }

  // Krok 7: wynik
  if (step.step.includes('Uproszczone wyrażenie')) {
    return (
      <div className="bg-green-50 rounded-xl shadow p-4 mb-4 border border-green-200 animate-fade-in">
        <div className="font-bold text-green-700 mb-2">{step.step}</div>
        <div className="mb-3 text-gray-700">{data.opis}</div>
        
        <div className="mb-4 text-sm text-gray-600 bg-white p-3 rounded-lg border border-green-200">
          <strong>🎉 Gratulacje! Oto wynik:</strong><br/>
          Suma wybranych <Tooltip term="implikant pierwszorzędny">implikantów pierwszorzędnych</Tooltip> daje zminimalizowaną postać <Tooltip term="DNF">DNF</Tooltip>.
          To najkrótsze możliwe wyrażenie logiczne, które reprezentuje tę samą funkcję co oryginalne wyrażenie.
        </div>
        
        <div className="text-center">
          <div className="text-3xl font-mono text-green-800 bg-white rounded-lg px-6 py-4 inline-block shadow-lg border-2 border-green-300">
            {data.result}
          </div>
          <div className="mt-3 text-sm text-gray-600">
            <strong>Postać zminimalizowana</strong> - gotowa do użycia!
          </div>
        </div>
      </div>
    );
  }

  // Krok 8: weryfikacja - pomijamy wyświetlanie użytkownikowi
  if (step.step.includes('Weryfikacja')) {
    return null;
  }

  // Domyślnie: bezpieczny fallback
  return (
    <div className="bg-gray-100 rounded-xl shadow p-4 mb-4 border border-gray-200 animate-fade-in">
      <div className="font-bold text-gray-700 mb-2">{step.step}</div>
      <pre className="text-xs text-gray-600 whitespace-pre-wrap">
        {JSON.stringify(data, null, 2)}
      </pre>
    </div>
  );
}

export default function QMSteps({ steps }) {
  if (!steps || steps.length === 0) {
    return <div className="text-gray-500">Brak danych do wyświetlenia kroków QM.</div>;
  }
  
  // Określ aktualny krok na podstawie pierwszego kroku
  const getCurrentStep = () => {
    if (steps.length === 0) return 1;
    const firstStep = steps[0].step;
    if (firstStep.includes('Tabela prawdy')) return 1;
    if (firstStep.includes('Grupowanie')) return 2;
    if (firstStep.includes('implikantów pierwszorzędnych')) return 3;
    if (firstStep.includes('Tabela pokrycia')) return 4;
    if (firstStep.includes('Implikanty istotne')) return 5;
    if (firstStep.includes('Minimalne pokrycie')) return 6;
    if (firstStep.includes('Uproszczone wyrażenie')) return 7;
    return 1;
  };
  
  return (
    <div className="space-y-4">
      {/* Dodaj podsumowanie kluczowych pojęć */}
      <KeyConceptsSummary />
      
      {/* Dodaj wskaźnik postępu */}
      <ProgressIndicator 
        currentStep={getCurrentStep()} 
        totalSteps={7}
        stepNames={steps.map(s => s.step)}
      />
      
      {/* Dodaj słownik pojęć i przewodnik */}
      <div className="flex justify-between items-center mb-4">
        <InteractiveGuide />
        <Glossary />
      </div>
      
      {/* Wyświetl kroki */}
      {steps.map((step, idx) => (
        <AnimatedStep key={idx} stepNumber={idx + 1} isVisible={true}>
          {renderStep(step, idx)}
        </AnimatedStep>
      ))}
    </div>
  );
}
