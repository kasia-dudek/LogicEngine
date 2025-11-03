// QMSteps.jsx — układ: pasek narzędzi u góry + jedna szeroka kolumna
import React, { useState } from 'react';
import { Tooltip } from './Glossary';
import InteractiveGuide from './InteractiveGuide';
import Glossary from './Glossary';
import ConnectionVisualization from './ConnectionVisualization';
import AnimatedStep from './AnimatedStep';

/* --- UI helpers --- */
function SectionTitle({ children }) {
  return (
    <h3 className="text-sm font-semibold uppercase tracking-wide text-blue-700 mb-2">
      {children}
    </h3>
  );
}

function StepCard({ title, subtitle, children, tone = 'default', onInfoHover, onInfoLeave, showInfo = false, tooltipContent }) {
  const tones = {
    default: 'bg-white border-blue-100',
    info: 'bg-blue-50 border-blue-200',
    success: 'bg-green-50 border-green-200',
  };
  const toneCls = tones[tone] || tones.default;
  return (
    <div className={`rounded-xl shadow p-4 border ${toneCls}`}>
      {title && (
        <div className="font-bold text-blue-800 mb-1 flex items-center gap-2">
          <span>{title}</span>
          {showInfo && (
            <span className="relative inline-block">
              <button
                type="button"
                onMouseEnter={onInfoHover}
                onMouseLeave={onInfoLeave}
                className="w-5 h-5 rounded-full bg-blue-100 text-blue-700 text-xs flex items-center justify-center border border-blue-300 hover:bg-blue-200 transition-colors"
                aria-label="Wyjaśnienie kroku"
                title="Wyjaśnienie tego kroku"
              >
                ?
              </button>
              {tooltipContent && (
                <div className="absolute z-[9999] w-80 p-3 mt-2 bg-gray-900 text-white text-sm rounded-lg shadow-lg border border-gray-700 transform -translate-x-1/2 left-1/2">
                  <div className="font-semibold text-blue-300 mb-1">{title}</div>
                  <div className="text-gray-200">{tooltipContent}</div>
                  <div className="absolute -top-1 left-1/2 transform -translate-x-1/2 w-2 h-2 bg-gray-900 rotate-45 border-l border-t border-gray-700"></div>
                </div>
              )}
            </span>
          )}
        </div>
      )}
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

// Helper component for collapsible explanations
function CollapsibleExplanation({ title, children, color = 'blue' }) {
  const [isExpanded, setIsExpanded] = useState(false);
  
  const colorMap = {
    blue: { button: 'text-blue-600 hover:text-blue-800', close: 'text-blue-600 hover:text-blue-800' },
    purple: { button: 'text-purple-600 hover:text-purple-800', close: 'text-purple-600 hover:text-purple-800' },
    orange: { button: 'text-orange-600 hover:text-orange-800', close: 'text-orange-600 hover:text-orange-800' },
    indigo: { button: 'text-indigo-600 hover:text-indigo-800', close: 'text-indigo-600 hover:text-indigo-800' },
  };
  
  const colors = colorMap[color] || colorMap.blue;
  
  return (
    <div>
      <div className="flex items-center gap-2 mb-2">
        <h4 className="text-sm font-semibold text-gray-700">{title}</h4>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className={`${colors.button} text-xs font-bold`}
          title={isExpanded ? "Ukryj wyjaśnienie" : "Pokaż wyjaśnienie"}
        >
          ℹ️
        </button>
      </div>
      
      {isExpanded && (
        <InfoCallout color={color}>
          <div className="flex justify-between items-start">
            <div className="flex-1">
              {children}
            </div>
            <button
              onClick={() => setIsExpanded(false)}
              className={`${colors.close} font-bold ml-2`}
            >
              ✕
            </button>
          </div>
        </InfoCallout>
      )}
    </div>
  );
}

function Table({ headers, rows, highlightCells = [], greenRows = [] }) {
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
          {rows.map((row, i) => {
            const isGreenRow = greenRows.includes(i);
            return (
              <tr key={i} className={isGreenRow ? 'bg-green-100' : ''}>
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
            );
          })}
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
      <Table
        headers={headers}
        rows={rows.map(r => ([
          <span className="font-mono">{r.i}</span>,
          <span className="font-mono">{r.bin}</span>,
          ...r.vals.map((v, j) => <span className="font-mono" key={j}>{v}</span>),
          <span className={`font-mono ${r.result === 1 ? 'text-green-800 font-semibold' : 'text-gray-700'}`}>{r.result}</span>,
        ]))}
        highlightCells={rows
          .map((r, i) => (r.result === 1 ? [[i, headers.length - 1]] : []))
          .flat()}
        greenRows={rows.map((r, i) => r.result === 1 ? i : -1).filter(i => i !== -1)}
      />

      <InfoCallout color="green">
        <strong>Mintermy:</strong> 
        <div className="mt-2">
          <Table
            headers={['Minterm', 'Binarnie']}
            rows={minterms.map(m => {
              const row = rows.find(r => r.i === m);
              const binary = row ? row.binary || m.toString(2).padStart(vars.length, '0') : m.toString(2).padStart(vars.length, '0');
              return [
                <span className="font-mono">m{m}</span>,
                <span className="font-mono">{binary}</span>
              ];
            })}
          />
        </div>
      </InfoCallout>
    </div>
  );
}

/* --- Pasek narzędzi (jeden rząd, nad krokami) --- */
function ToolsBar() {
  const [showGuide, setShowGuide] = useState(false);
  const [showGlossary, setShowGlossary] = useState(false);

  return (
    <div className="w-full">
      <div className="rounded-xl border border-gray-200 bg-white shadow p-3">
        <div className="flex flex-wrap gap-3 items-center justify-center">
          <button 
            type="button"
            className="bg-indigo-500 hover:bg-indigo-600 text-white font-medium py-3 px-6 rounded-full border-0 transition-colors text-sm cursor-pointer pointer-events-auto z-10 relative"
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              setShowGuide(!showGuide);
              setShowGlossary(false);
            }}
          >
            Przewodnik interaktywny
          </button>

          <button 
            type="button"
            className="bg-slate-500 hover:bg-slate-600 text-white font-medium py-3 px-6 rounded-full border-0 transition-colors text-sm cursor-pointer pointer-events-auto z-10 relative"
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              setShowGlossary(!showGlossary);
              setShowGuide(false);
            }}
          >
            Słownik pojęć
          </button>
        </div>
        
        {showGuide && (
          <div className="mt-4 p-4 rounded-lg border bg-gray-50">
            <InteractiveGuide />
          </div>
        )}
        
        {showGlossary && (
          <div className="mt-4 p-4 rounded-lg border bg-gray-50">
            <Glossary />
          </div>
        )}
      </div>
    </div>
  );
}

/* --- Render poszczególnych kroków --- */
function renderStep(step, stepIndex, hoveredStepIndex, setHoveredStepIndex, getStepExplanation) {
  const { data } = step;
  const explanation = getStepExplanation(step);
  const isHovered = hoveredStepIndex === stepIndex;

  if (step.step.includes('Tabela prawdy')) {
    return (
      <StepCard 
        title={step.step} 
        showInfo={true}
        onInfoHover={() => setHoveredStepIndex(stepIndex)}
        onInfoLeave={() => setHoveredStepIndex(null)}
        tooltipContent={isHovered ? explanation : null}
      >
        <TruthTable vars={data.vars} rows={data.rows} />
      </StepCard>
    );
  }

  if (step.step.includes('Znajdź mintermy')) {
    return (
      <StepCard 
        title={step.step} 
        showInfo={true}
        onInfoHover={() => setHoveredStepIndex(stepIndex)}
        onInfoLeave={() => setHoveredStepIndex(null)}
        tooltipContent={isHovered ? explanation : null}
      >
        <Table
          headers={['Indeks', 'Binarnie']}
          rows={data.minterms.map(m => [<span className="font-mono">m{m}</span>, <span className="font-mono">{m.toString(2)}</span>])}
        />
      </StepCard>
    );
  }

  if (step.step.includes('Grupowanie mintermów')) {
    return (
      <StepCard 
        title={step.step} 
        showInfo={true}
        onInfoHover={() => setHoveredStepIndex(stepIndex)}
        onInfoLeave={() => setHoveredStepIndex(null)}
        tooltipContent={isHovered ? explanation : null}
      >
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
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
      <StepCard 
        title={step.step} 
        showInfo={true}
        onInfoHover={() => setHoveredStepIndex(stepIndex)}
        onInfoLeave={() => setHoveredStepIndex(null)}
        tooltipContent={isHovered ? explanation : null}
      >

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
      <StepCard 
        title={step.step} 
        showInfo={true}
        onInfoHover={() => setHoveredStepIndex(stepIndex)}
        onInfoLeave={() => setHoveredStepIndex(null)}
        tooltipContent={isHovered ? explanation : null}
      >

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
      <StepCard 
        title="Krok 5: Implikanty istotne" 
        showInfo={true}
        onInfoHover={() => setHoveredStepIndex(stepIndex)}
        onInfoLeave={() => setHoveredStepIndex(null)}
        tooltipContent={isHovered ? explanation : null}
      >
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

  if (step.step.includes('Petrick: dystrybucja')) {
    return (
      <StepCard 
        title={step.step} 
        showInfo={true}
        onInfoHover={() => setHoveredStepIndex(stepIndex)}
        onInfoLeave={() => setHoveredStepIndex(null)}
        tooltipContent={isHovered ? explanation : null}
      >
        <div className="space-y-3">
          <InfoCallout color="indigo">
            <div className="font-mono text-sm">{data.opis}</div>
          </InfoCallout>
          {data.remaining_minterms && (
            <div>
              <SectionTitle>Pozostałe mintermy</SectionTitle>
              <div className="flex flex-wrap gap-2">
                {data.remaining_minterms.map((m, i) => (
                  <span key={i} className="font-mono bg-gray-100 px-2 py-1 rounded border text-sm">m{m}</span>
                ))}
              </div>
            </div>
          )}
          {data.pi_choices && (
            <div>
              <SectionTitle>Wybory PI dla każdego mintermu</SectionTitle>
              <div className="space-y-2">
                {data.pi_choices.map((pis, i) => (
                  <div key={i} className="bg-purple-50 border border-purple-200 rounded-lg p-2">
                    <div className="text-xs text-purple-700 font-semibold mb-1">Minterm m{data.remaining_minterms[i]}:</div>
                    <div className="flex flex-wrap gap-2">
                      {pis.map((pi, j) => (
                        <span key={j} className="font-mono text-sm text-purple-800">{pi}</span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </StepCard>
    );
  }

  if (step.step.includes('Petrick: absorpcja')) {
    return (
      <StepCard 
        title={step.step} 
        showInfo={true}
        onInfoHover={() => setHoveredStepIndex(stepIndex)}
        onInfoLeave={() => setHoveredStepIndex(null)}
        tooltipContent={isHovered ? explanation : null}
      >
        <InfoCallout color="green">
          <div className="font-mono text-sm">{data.opis}</div>
        </InfoCallout>
      </StepCard>
    );
  }

  if (step.step.includes('Minimalne pokrycie')) {
    return (
      <StepCard 
        title={step.step} 
        showInfo={true}
        onInfoHover={() => setHoveredStepIndex(stepIndex)}
        onInfoLeave={() => setHoveredStepIndex(null)}
        tooltipContent={isHovered ? explanation : null}
      >
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
      <StepCard 
        title="Wynik" 
        tone="success"
        showInfo={true}
        onInfoHover={() => setHoveredStepIndex(stepIndex)}
        onInfoLeave={() => setHoveredStepIndex(null)}
        tooltipContent={isHovered ? explanation : null}
      >
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
    <StepCard 
      title={step.step}
      showInfo={true}
      onInfoHover={() => setHoveredStepIndex(stepIndex)}
      onInfoLeave={() => setHoveredStepIndex(null)}
    >
      {isHovered && (
        <div className="absolute left-0 top-full mt-2 z-40 w-80 bg-white border border-gray-300 rounded-lg shadow-xl p-3 text-xs">
          <div className="font-semibold text-blue-700 mb-1">{step.step}</div>
          <div className="text-gray-700">{explanation}</div>
        </div>
      )}
      <pre className="text-xs text-gray-600 whitespace-pre-wrap">
        {JSON.stringify(data, null, 2)}
      </pre>
    </StepCard>
  );
}

/* --- Główny komponent --- */
export default function QMSteps({ steps, error }) {
  const [hoveredStepIndex, setHoveredStepIndex] = useState(null);

  const getStepExplanation = (step) => {
    const stepName = step.step;
    
    if (stepName.includes('Tabela prawdy')) {
      return "Tabela prawdy pokazuje wszystkie możliwe kombinacje wartości zmiennych i wynik wyrażenia dla każdej kombinacji. Wiersze z wynikiem 1 to mintermy - kombinacje, dla których wyrażenie jest prawdziwe.";
    }
    
    if (stepName.includes('Znajdź mintermy')) {
      return "Mintermy to kombinacje zmiennych, dla których wyrażenie przyjmuje wartość 1. Każdy minterm reprezentuje jeden wiersz tabeli prawdy z wynikiem 1.";
    }
    
    if (stepName.includes('Grupowanie mintermów')) {
      return "Mintermy są grupowane według liczby jedynek w ich reprezentacji binarnej. To przygotowanie do łączenia sąsiednich mintermów.";
    }
    
    if (stepName.includes('implikantów pierwszorzędnych')) {
      return "Implikanty pierwszorzędne (PI) to największe możliwe grupy mintermów różniących się jednym bitem. W miejscu różnicy wstawiamy '-' (don't care).";
    }
    
    if (stepName.includes('Tabela pokrycia')) {
      return "Tabela pokrycia pokazuje, które implikanty pierwszorzędne pokrywają które mintermy. To podstawa do wyboru minimalnego pokrycia.";
    }
    
    if (stepName.includes('Implikanty istotne') || stepName.includes('Zasada implikanty')) {
      return "Implikanty istotne to te, które są jedynym pokryciem pewnego mintermu. Muszą być uwzględnione w ostatecznym rozwiązaniu.";
    }
    
    if (stepName.includes('Petrick: dystrybucja')) {
      return "Formuła Petricka to iloczyn sum reprezentujący wszystkie możliwe pokrycia pozostałych mintermów. Każda suma w iloczynie reprezentuje PI, które pokrywają dany minterm.";
    }
    
    if (stepName.includes('Petrick: absorpcja')) {
      return "Na tym etapie znajdujemy minimalny iloczyn z formuły Petricka, co odpowiada najmniejszemu pokryciu pozostałych mintermów.";
    }
    
    if (stepName.includes('Minimalne pokrycie')) {
      return "Metoda Petricka znajduje najmniejszy zbiór implikantów pierwszorzędnych, który pokrywa wszystkie mintermy. To daje nam minimalne wyrażenie.";
    }
    
    if (stepName.includes('Uproszczone wyrażenie')) {
      return "To końcowy wynik - minimalne wyrażenie w postaci DNF (Disjunctive Normal Form), które jest równoważne z oryginalnym wyrażeniem.";
    }
    
    return "Ten krok jest częścią algorytmu Quine-McCluskey do minimalizacji wyrażeń logicznych.";
  };

  if (error) {
    return (
      <div className="text-center p-8 bg-yellow-50 border border-yellow-200 rounded-lg">
        <div className="text-yellow-800 font-semibold mb-2">
          ⚠️ Uproszczanie metodą Quine-McCluskey niedostępne
        </div>
        <div className="text-yellow-700">
          {error}
        </div>
      </div>
    );
  }

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
            {renderStep(step, idx, hoveredStepIndex, setHoveredStepIndex, getStepExplanation)}
          </AnimatedStep>
        ))}
      </div>
    </div>
  );
}
