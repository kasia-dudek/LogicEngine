import React, { useState } from 'react';
import { Tooltip } from './Glossary';

const InteractiveGuide = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [currentGuide, setCurrentGuide] = useState(0);

  const guides = [
    {
      title: "Krok 1: Tabela prawdy i mintermy",
      content: (
        <div className="space-y-3">
          <p>W pierwszym kroku tworzymy tabelę prawdy dla naszego wyrażenia logicznego.</p>
          <div className="bg-blue-50 p-3 rounded border border-blue-200">
            <strong>Co robimy:</strong>
            <ul className="mt-2 space-y-1 text-sm">
              <li>• Wypisujemy wszystkie możliwe kombinacje wartości zmiennych</li>
              <li>• Obliczamy wynik funkcji dla każdej kombinacji</li>
              <li>• Zaznaczamy wiersze z wynikiem 1 - to są <Tooltip term="minterm">mintermy</Tooltip></li>
            </ul>
          </div>
          <div className="bg-yellow-50 p-3 rounded border border-yellow-200">
            <strong>Dlaczego to ważne:</strong> Mintermy reprezentują przypadki, gdy nasza funkcja jest prawdziwa. 
            Będziemy ich potrzebować do uproszczenia wyrażenia.
          </div>
        </div>
      )
    },
    {
      title: "Krok 2: Grupowanie mintermów",
      content: (
        <div className="space-y-3">
          <p>Grupujemy mintermy według liczby jedynek w ich reprezentacji binarnej.</p>
          <div className="bg-blue-50 p-3 rounded border border-blue-200">
            <strong>Co robimy:</strong>
            <ul className="mt-2 space-y-1 text-sm">
              <li>• Liczymy jedynki w zapisie binarnym każdego mintermu</li>
              <li>• Grupujemy mintermy z tą samą liczbą jedynek</li>
              <li>• Tworzymy grupy: 0 jedynek, 1 jedynka, 2 jedynki, itd.</li>
            </ul>
          </div>
          <div className="bg-yellow-50 p-3 rounded border border-yellow-200">
            <strong>Dlaczego to ważne:</strong> Tylko mintermy z sąsiednich grup mogą być łączone. 
            To znacznie przyspiesza proces upraszczania.
          </div>
        </div>
      )
    },
    {
      title: "Krok 3: Znajdowanie implikantów pierwszorzędnych",
      content: (
        <div className="space-y-3">
          <p>Łączymy mintermy różniące się tylko jedną pozycją, tworząc implikanty pierwszorzędne.</p>
          <div className="bg-blue-50 p-3 rounded border border-blue-200">
            <strong>Co robimy:</strong>
            <ul className="mt-2 space-y-1 text-sm">
              <li>• Łączymy mintermy z sąsiednich grup różniące się jedną pozycją</li>
              <li>• Różniącą się pozycję zastępujemy myślnikiem (-)</li>
              <li>• Powtarzamy proces, aż nie można już nic połączyć</li>
            </ul>
          </div>
          <div className="bg-yellow-50 p-3 rounded border border-yellow-200">
            <strong>Dlaczego to ważne:</strong> <Tooltip term="implikant pierwszorzędny">Implikanty pierwszorzędne</Tooltip> 
            to maksymalnie uproszczone wyrażenia pokrywające pewne mintermy.
          </div>
        </div>
      )
    },
    {
      title: "Krok 4: Tabela pokrycia",
      content: (
        <div className="space-y-3">
          <p>Tworzymy tabelę pokazującą, które implikanty pokrywają które mintermy.</p>
          <div className="bg-blue-50 p-3 rounded border border-blue-200">
            <strong>Co robimy:</strong>
            <ul className="mt-2 space-y-1 text-sm">
              <li>• Tworzymy tabelę z mintermami w wierszach i implikantami w kolumnach</li>
              <li>• Zaznaczamy ✔ tam, gdzie implikant pokrywa minterm</li>
              <li>• Szukamy mintermów pokrytych tylko przez jeden implikant</li>
            </ul>
          </div>
          <div className="bg-yellow-50 p-3 rounded border border-yellow-200">
            <strong>Dlaczego to ważne:</strong> <Tooltip term="tabela pokrycia">Tabela pokrycia</Tooltip> 
            pomaga nam znaleźć <Tooltip term="implikant istotny">implikanty istotne</Tooltip> - te, które muszą być wybrane.
          </div>
        </div>
      )
    },
    {
      title: "Krok 5: Implikanty istotne",
      content: (
        <div className="space-y-3">
          <p>Identyfikujemy implikanty, które są jedynym pokryciem pewnych mintermów.</p>
          <div className="bg-blue-50 p-3 rounded border border-blue-200">
            <strong>Co robimy:</strong>
            <ul className="mt-2 space-y-1 text-sm">
              <li>• Szukamy mintermów pokrytych tylko przez jeden implikant</li>
              <li>• Te implikanty to <Tooltip term="implikant istotny">implikanty istotne</Tooltip></li>
              <li>• Musimy je wybrać - inaczej niektóre mintermy nie będą pokryte</li>
            </ul>
          </div>
          <div className="bg-yellow-50 p-3 rounded border border-yellow-200">
            <strong>Dlaczego to ważne:</strong> Implikanty istotne muszą być w końcowym rozwiązaniu. 
            To gwarantuje, że wszystkie mintermy będą pokryte.
          </div>
        </div>
      )
    },
    {
      title: "Krok 6: Minimalne pokrycie",
      content: (
        <div className="space-y-3">
          <p>Używamy metody Petricka do znalezienia najmniejszego zestawu implikantów.</p>
          <div className="bg-blue-50 p-3 rounded border border-blue-200">
            <strong>Co robimy:</strong>
            <ul className="mt-2 space-y-1 text-sm">
              <li>• Wybieramy implikanty istotne (z poprzedniego kroku)</li>
              <li>• Używamy <Tooltip term="metoda Petricka">metody Petricka</Tooltip> dla pozostałych</li>
              <li>• Znajdujemy najmniejszy zestaw pokrywający wszystkie mintermy</li>
            </ul>
          </div>
          <div className="bg-yellow-50 p-3 rounded border border-yellow-200">
            <strong>Dlaczego to ważne:</strong> To daje nam minimalne pokrycie - najkrótsze możliwe wyrażenie logiczne.
          </div>
        </div>
      )
    },
    {
      title: "Krok 7: Wynik końcowy",
      content: (
        <div className="space-y-3">
          <p>Sumujemy wybrane implikanty, otrzymując zminimalizowane wyrażenie.</p>
          <div className="bg-blue-50 p-3 rounded border border-blue-200">
            <strong>Co robimy:</strong>
            <ul className="mt-2 space-y-1 text-sm">
              <li>• Bierzemy wszystkie wybrane implikanty</li>
              <li>• Łączymy je operatorem alternatywy (∨)</li>
              <li>• Otrzymujemy zminimalizowaną postać <Tooltip term="DNF">DNF</Tooltip></li>
            </ul>
          </div>
          <div className="bg-yellow-50 p-3 rounded border border-yellow-200">
            <strong>Dlaczego to ważne:</strong> To jest nasz końcowy wynik - najkrótsze wyrażenie reprezentujące tę samą funkcję logiczną.
          </div>
        </div>
      )
    }
  ];

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="bg-purple-100 hover:bg-purple-200 text-purple-700 px-4 py-2 rounded-full text-sm font-medium transition-colors border border-purple-300 flex items-center gap-2"
      >
        Przewodnik krok po kroku
      </button>
      
      {isOpen && (
        <div className="absolute z-50 w-96 bg-white border border-gray-300 rounded-lg shadow-lg mt-2 right-0">
          <div className="p-4 border-b border-gray-200">
            <div className="flex justify-between items-center mb-3">
              <h3 className="font-semibold text-gray-800">Przewodnik metody Quine-McCluskey</h3>
              <button
                onClick={() => setIsOpen(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            
            {/* Nawigacja */}
            <div className="flex justify-between items-center mb-4">
              <button
                onClick={() => setCurrentGuide(Math.max(0, currentGuide - 1))}
                disabled={currentGuide === 0}
                className="px-3 py-1 bg-gray-100 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed rounded text-sm"
              >
                ← Poprzedni
              </button>
              <span className="text-sm text-gray-600">
                {currentGuide + 1} z {guides.length}
              </span>
              <button
                onClick={() => setCurrentGuide(Math.min(guides.length - 1, currentGuide + 1))}
                disabled={currentGuide === guides.length - 1}
                className="px-3 py-1 bg-gray-100 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed rounded text-sm"
              >
                Następny →
              </button>
            </div>
          </div>
          
          <div className="p-4 max-h-96 overflow-y-auto">
            <h4 className="font-semibold text-lg text-gray-800 mb-3">
              {guides[currentGuide].title}
            </h4>
            {guides[currentGuide].content}
          </div>
          
          {/* Wskaźniki kroków */}
          <div className="p-4 border-t border-gray-200">
            <div className="flex justify-center space-x-2">
              {guides.map((_, index) => (
                <button
                  key={index}
                  onClick={() => setCurrentGuide(index)}
                  className={`w-2 h-2 rounded-full ${
                    index === currentGuide ? 'bg-purple-500' : 'bg-gray-300'
                  }`}
                />
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default InteractiveGuide;
