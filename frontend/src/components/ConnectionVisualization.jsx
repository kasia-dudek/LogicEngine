import React from 'react';

const ConnectionVisualization = ({ pairs, round }) => {
  if (!pairs || pairs.length === 0) {
    return (
      <div className="text-sm text-gray-600 bg-gray-50 p-3 rounded border">
        Brak możliwych połączeń w tej rundzie - wszystkie mintermy już maksymalnie uproszczone.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="text-sm text-gray-600 bg-blue-50 p-2 rounded border border-blue-200">
        <strong>🔗 Wizualizacja połączeń:</strong> Poniżej widzisz, jak mintermy są łączone w pary. 
        Różniąca się pozycja jest zaznaczona na czerwono.
      </div>
      
      <div className="grid gap-3">
        {pairs.map((pair, index) => {
          const from1 = pair.from[0];
          const from2 = pair.from[1];
          const to = pair.to;
          
          // Znajdź różniącą się pozycję
          const findDifference = (str1, str2) => {
            for (let i = 0; i < str1.length; i++) {
              if (str1[i] !== str2[i]) {
                return i;
              }
            }
            return -1;
          };
          
          const diffPos = findDifference(from1, from2);
          
          return (
            <div key={index} className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
              <div className="flex items-center justify-center space-x-4">
                {/* Pierwszy minterm */}
                <div className="text-center">
                  <div className="text-xs text-gray-500 mb-1">Pierwszy minterm</div>
                  <div className="font-mono text-lg bg-blue-50 px-3 py-2 rounded border">
                    {from1.split('').map((char, i) => (
                      <span 
                        key={i} 
                        className={i === diffPos ? 'text-red-600 font-bold bg-red-100 px-1 rounded' : ''}
                      >
                        {char}
                      </span>
                    ))}
                  </div>
                </div>
                
                {/* Strzałka */}
                <div className="flex flex-col items-center">
                  <div className="text-2xl text-purple-600">+</div>
                  <div className="text-xs text-gray-500">łączenie</div>
                </div>
                
                {/* Drugi minterm */}
                <div className="text-center">
                  <div className="text-xs text-gray-500 mb-1">Drugi minterm</div>
                  <div className="font-mono text-lg bg-blue-50 px-3 py-2 rounded border">
                    {from2.split('').map((char, i) => (
                      <span 
                        key={i} 
                        className={i === diffPos ? 'text-red-600 font-bold bg-red-100 px-1 rounded' : ''}
                      >
                        {char}
                      </span>
                    ))}
                  </div>
                </div>
                
                {/* Strzałka do wyniku */}
                <div className="flex flex-col items-center">
                  <div className="text-2xl text-green-600">→</div>
                  <div className="text-xs text-gray-500">wynik</div>
                </div>
                
                {/* Wynik */}
                <div className="text-center">
                  <div className="text-xs text-gray-500 mb-1">Wynik</div>
                  <div className="font-mono text-lg bg-green-50 px-3 py-2 rounded border border-green-300">
                    {to.split('').map((char, i) => (
                      <span 
                        key={i} 
                        className={char === '-' ? 'text-orange-600 font-bold bg-orange-100 px-1 rounded' : ''}
                      >
                        {char}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
              
              {/* Wyjaśnienie */}
              <div className="mt-3 text-xs text-gray-600 bg-gray-50 p-2 rounded">
                <strong>Wyjaśnienie:</strong> Pozycja {diffPos + 1} różni się między mintermami 
                ({from1[diffPos]} vs {from2[diffPos]}), więc zastępujemy ją myślnikiem (-) w wyniku.
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ConnectionVisualization;
