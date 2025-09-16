import React, { useState } from 'react';

const Tooltip = ({ children, term }) => {
  const [isVisible, setIsVisible] = useState(false);
  const definition = glossary[term] || 'Definicja nie znaleziona';

  return (
    <span className="relative inline-block">
      <span
        className="cursor-help underline decoration-dotted decoration-blue-400 text-blue-600 hover:text-blue-800 transition-colors"
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
      >
        {children}
      </span>
      {isVisible && (
        <div className="absolute z-50 w-80 p-3 mt-2 bg-gray-900 text-white text-sm rounded-lg shadow-lg border border-gray-700 transform -translate-x-1/2 left-1/2">
          <div className="font-semibold text-blue-300 mb-1">{term}</div>
          <div className="text-gray-200">{definition}</div>
          <div className="absolute -top-1 left-1/2 transform -translate-x-1/2 w-2 h-2 bg-gray-900 rotate-45 border-l border-t border-gray-700"></div>
        </div>
      )}
    </span>
  );
};

const glossary = {
  'minterm': 'Minterm to iloczyn wszystkich zmiennych w ich postaci bezpośredniej lub zanegowanej, który daje wartość 1 dla dokładnie jednej kombinacji wartości zmiennych.',
  'implikant': 'Implikant to iloczyn zmiennych (lub ich negacji), który pokrywa jeden lub więcej mintermów. Implikant pierwszorzędny to taki, który nie może być dalej uproszczony.',
  'implikant pierwszorzędny': 'Implikant pierwszorzędny (PI) to implikant, który nie może być dalej uproszczony przez łączenie z innymi implikantami. To maksymalnie uproszczone wyrażenie pokrywające pewne mintermy.',
  'implikant istotny': 'Implikant istotny to implikant pierwszorzędny, który jest jedynym pokryciem pewnego mintermu. Musi być wybrany, bo inaczej ten minterm nie będzie pokryty w końcowym wyniku.',
  'tabela pokrycia': 'Tabela pokrycia pokazuje, które implikanty pierwszorzędne pokrywają które mintermy. Używana do znajdowania implikantów istotnych i minimalnego pokrycia.',
  'metoda Petricka': 'Metoda Petricka to algorytm znajdowania minimalnego pokrycia w tabeli pokrycia. Tworzy funkcję boolowską i znajduje jej minimalne rozwiązanie.',
  'DNF': 'DNF (Disjunctive Normal Form) to postać normalna alternatywna - suma iloczynów zmiennych i ich negacji.',
  'karnaugh': 'Mapa Karnaugha to graficzna metoda upraszczania funkcji boolowskich, alternatywna do metody Quine-McCluskey.',
  'ONP': 'ONP (Odwrotna Notacja Polska) to sposób zapisu wyrażeń matematycznych, w którym operatory są umieszczone po swoich argumentach.',
  'tautologia': 'Tautologia to wyrażenie logiczne, które jest zawsze prawdziwe, niezależnie od wartości zmiennych.',
  'binarnie': 'Reprezentacja binarna to zapis liczby w systemie dwójkowym (0 i 1). W logice, 0 oznacza fałsz, a 1 oznacza prawdę.',
  'grupowanie': 'Grupowanie mintermów według liczby jedynek w reprezentacji binarnej pozwala na efektywne łączenie tylko tych, które różnią się jedną pozycją.',
  'łączenie': 'Łączenie mintermów to proces upraszczania, w którym łączymy mintermy różniące się jedną pozycją, zastępując różniącą się pozycję myślnikiem (-).'
};

const Glossary = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTerm, setSelectedTerm] = useState(null);

  const filteredTerms = Object.entries(glossary).filter(([term, definition]) =>
    term.toLowerCase().includes(searchTerm.toLowerCase()) ||
    definition.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="bg-blue-100 hover:bg-blue-200 text-blue-700 px-3 py-1 rounded-full text-sm font-medium transition-colors border border-blue-300"
      >
        📚 Słownik pojęć
      </button>
      
      {isOpen && (
        <div className="absolute z-50 w-96 bg-white border border-gray-300 rounded-lg shadow-lg mt-2 right-0">
          <div className="p-4 border-b border-gray-200">
            <div className="flex justify-between items-center mb-3">
              <h3 className="font-semibold text-gray-800">Słownik pojęć</h3>
              <button
                onClick={() => setIsOpen(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            <input
              type="text"
              placeholder="Szukaj pojęcia..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          <div className="max-h-80 overflow-y-auto">
            {filteredTerms.length > 0 ? (
              <div className="p-2">
                {filteredTerms.map(([term, definition]) => (
                  <div
                    key={term}
                    className={`p-2 rounded cursor-pointer transition-colors ${
                      selectedTerm === term ? 'bg-blue-50 border border-blue-200' : 'hover:bg-gray-50'
                    }`}
                    onClick={() => setSelectedTerm(selectedTerm === term ? null : term)}
                  >
                    <div className="font-medium text-blue-700 text-sm">{term}</div>
                    {selectedTerm === term && (
                      <div className="mt-1 text-xs text-gray-600">{definition}</div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-4 text-gray-500 text-sm text-center">
                Nie znaleziono pojęć pasujących do wyszukiwania
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export { Tooltip, glossary };
export default Glossary;
