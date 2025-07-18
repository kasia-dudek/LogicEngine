import React from 'react';

const groupColors = [
  'bg-blue-200 border-blue-400',
  'bg-green-200 border-green-400',
  'bg-yellow-200 border-yellow-400',
  'bg-pink-200 border-pink-400',
  'bg-purple-200 border-purple-400',
  'bg-orange-200 border-orange-400',
  'bg-red-200 border-red-400',
  'bg-teal-200 border-teal-400',
];

function getGrayCodeLabels(n) {
  // Zwraca etykiety w kodzie Graya dla n zmiennych
  if (n === 1) return ['0', '1'];
  if (n === 2) return ['0', '1'];
  if (n === 3 || n === 4) return ['00', '01', '11', '10'];
  return [];
}

function KMapDisplay({ kmap, groups, result }) {
  console.log('KMapDisplay props:', { kmap, groups, result });
  if (!kmap || !Array.isArray(kmap) || kmap.length === 0 || !Array.isArray(kmap[0])) {
    return <div className="text-red-600 font-semibold">Brak poprawnych danych do wyświetlenia mapy Karnaugha.<br/>Sprawdź, czy wyrażenie nie ma zbyt wielu zmiennych (max 4) i czy backend zwraca dane.</div>;
  }

  // Ustal liczbę zmiennych na podstawie rozmiaru mapy
  const nRows = kmap.length;
  const nCols = kmap[0].length;
  const nVars = Math.round(Math.log2(nRows * nCols));
  const rowLabels = getGrayCodeLabels(nRows);
  const colLabels = getGrayCodeLabels(nCols);

  // Mapa: [wiersz][kolumna] => numer grupy (lub 0)
  const highlightMap = Array.from({ length: nRows }, (_, i) =>
    Array.from({ length: nCols }, (_, j) => 0)
  );
  if (groups) {
    groups.forEach((group, gidx) => {
      if (group.cells) {
        group.cells.forEach(([row, col]) => {
          if (highlightMap[row] && highlightMap[row][col] !== undefined) {
            highlightMap[row][col] = gidx + 1; // numer grupy
          }
        });
      }
    });
  }

  return (
    <div className="flex flex-col items-center">
      <div className="overflow-x-auto">
        <table className="border-2 border-blue-300 rounded-2xl shadow-xl mb-4 bg-white animate-fade-in">
          <thead>
            <tr>
              <th className="w-8 h-8"></th>
              {colLabels.map((cl, j) => (
                <th key={j} className="px-3 py-2 text-blue-700 bg-blue-50 border-b-2 border-blue-200 text-base font-bold text-center">{cl}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {kmap.map((row, i) => (
              <tr key={i}>
                <th className="px-3 py-2 text-blue-700 bg-blue-50 border-r-2 border-blue-200 text-base font-bold text-center">{rowLabels[i]}</th>
                {row.map((val, j) => {
                  const groupIdx = highlightMap[i][j];
                  const color = groupIdx ? groupColors[(groupIdx - 1) % groupColors.length] : 'bg-white';
                  const border = groupIdx ? groupColors[(groupIdx - 1) % groupColors.length].split(' ')[1] : 'border-gray-300';
                  return (
                    <td
                      key={j}
                      className={`w-14 h-14 text-center border-2 ${color} ${border} font-bold relative transition-all duration-200`}
                    >
                      <span className="text-lg">{val}</span>
                      {groupIdx ? (
                        <span className="absolute top-1 right-1 text-xs font-semibold text-blue-900">G{groupIdx}</span>
                      ) : null}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="flex gap-2 mb-4 flex-wrap justify-center">
        {groups && groups.map((g, idx) => (
          <div key={idx} className={`px-3 py-1 rounded-xl ${groupColors[idx % groupColors.length]} border-2 font-semibold text-xs flex items-center gap-2`}>
            <span className="w-3 h-3 rounded-full inline-block" style={{ background: 'rgba(0,0,0,0.15)' }}></span>
            Grupa {idx + 1}: <span className="font-mono">{g.expr || ''}</span>
          </div>
        ))}
      </div>
      <div className="text-lg text-blue-700 mb-2 font-semibold">Uproszczone: <span className="font-mono text-green-700">{result}</span></div>
      <div className="text-xs text-gray-500 max-w-lg text-center">
        Każda grupa (kolor) odpowiada fragmentowi wyrażenia logicznego. Grupy są dobierane tak, by pokryć wszystkie jedynki w mapie Karnaugha możliwie najmniejszą liczbą prostych wyrażeń.
      </div>
    </div>
  );
}

export default KMapDisplay; 