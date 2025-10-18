import React, { useState } from 'react';
import { Tooltip } from './Glossary';

const KeyConceptsSummary = () => {
  const [isExpanded, setIsExpanded] = useState(false);

  const concepts = [
    {
      term: 'minterm',
      definition: 'Iloczyn wszystkich zmiennych w ich postaci bezpośredniej lub zanegowanej, który daje wartość 1 dla dokładnie jednej kombinacji wartości zmiennych.',
      example: 'A ∧ B (dla A=1, B=1)',
      color: 'blue'
    },
    {
      term: 'implikant pierwszorzędny',
      definition: 'Implikant, który nie może być dalej uproszczony przez łączenie z innymi implikantami.',
      example: 'A ∨ ¬B',
      color: 'green'
    },
    {
      term: 'implikant istotny',
      definition: 'Implikant pierwszorzędny, który jest jedynym pokryciem pewnego mintermu.',
      example: 'Musi być wybrany!',
      color: 'red'
    },
    {
      term: 'tabela pokrycia',
      definition: 'Tabela pokazująca, które implikanty pokrywają które mintermy.',
      example: 'Używana do znajdowania implikantów istotnych',
      color: 'purple'
    },
    {
      term: 'metoda Petricka',
      definition: 'Algorytm znajdowania minimalnego pokrycia w tabeli pokrycia.',
      example: 'Znajduje najmniejszy zestaw implikantów',
      color: 'orange'
    },
    {
      term: 'DNF',
      definition: 'Postać normalna alternatywna - suma iloczynów zmiennych i ich negacji.',
      example: 'A ∨ (B ∧ C)',
      color: 'indigo'
    }
  ];

  const getColorClasses = (color) => {
    const colorMap = {
      blue: 'bg-blue-50 border-blue-200 text-blue-800',
      green: 'bg-green-50 border-green-200 text-green-800',
      red: 'bg-red-50 border-red-200 text-red-800',
      purple: 'bg-purple-50 border-purple-200 text-purple-800',
      orange: 'bg-orange-50 border-orange-200 text-orange-800',
      indigo: 'bg-indigo-50 border-indigo-200 text-indigo-800'
    };
    return colorMap[color] || 'bg-gray-50 border-gray-200 text-gray-800';
  };

  return (
    <div className="bg-white rounded-xl shadow p-4 mb-6 border border-gray-200">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between text-left"
      >
        <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
          Kluczowe pojęcia metody Quine-McCluskey
          <span className="text-sm text-gray-500">({concepts.length} pojęć)</span>
        </h3>
        <span className="text-gray-400 text-xl">
          {isExpanded ? '−' : '+'}
        </span>
      </button>
      
      {isExpanded && (
        <div className="mt-4 space-y-3">
          <div className="text-sm text-gray-600 mb-4">
            Poniżej znajdziesz najważniejsze pojęcia używane w metodzie Quine-McCluskey. 
            Kliknij na podkreślone terminy w tekście, aby zobaczyć ich definicje.
          </div>
          
          <div className="grid gap-3 md:grid-cols-2">
            {concepts.map((concept, index) => (
              <div 
                key={index}
                className={`p-3 rounded-lg border ${getColorClasses(concept.color)}`}
              >
                <div className="font-semibold mb-1">
                  <Tooltip term={concept.term}>{concept.term}</Tooltip>
                </div>
                <div className="text-sm mb-2">
                  {concept.definition}
                </div>
                <div className="text-xs font-mono bg-white bg-opacity-50 px-2 py-1 rounded">
                  <strong>Przykład:</strong> {concept.example}
                </div>
              </div>
            ))}
          </div>
          
          <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <div className="text-sm text-yellow-800">
              <strong>Wskazówka:</strong> Te pojęcia są kluczowe dla zrozumienia metody Quine-McCluskey. 
              Wróć do tego podsumowania, gdy będziesz potrzebować przypomnienia definicji.
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default KeyConceptsSummary;
