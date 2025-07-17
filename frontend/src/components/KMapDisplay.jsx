import React from 'react';

function KMapDisplay({ kmap, groups, result }) {
  if (!kmap || kmap.length === 0) {
    return <div className="text-gray-500">Brak danych do wyświetlenia mapy Karnaugh.</div>;
  }

  // Tworzymy mapę podświetleń: [wiersz][kolumna] => true jeśli należy do grupy
  const highlightMap = Array.from({ length: kmap.length }, (_, i) =>
    Array.from({ length: kmap[0].length }, (_, j) => false)
  );
  if (groups) {
    groups.forEach(group => {
      if (group.cells) {
        group.cells.forEach(([row, col]) => {
          if (highlightMap[row] && highlightMap[row][col] !== undefined) {
            highlightMap[row][col] = true;
          }
        });
      }
    });
  }

  return (
    <div className="flex flex-col items-center">
      <div className="overflow-x-auto">
        <table className="border border-gray-300 rounded mb-2">
          <tbody>
            {kmap.map((row, i) => (
              <tr key={i}>
                {row.map((val, j) => (
                  <td
                    key={j}
                    className={`w-12 h-12 text-center border ${highlightMap[i][j] ? 'bg-blue-200 font-bold' : ''}`}
                  >
                    {val}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="text-sm text-gray-700 mb-2">Uproszczone: <span className="font-semibold">{result}</span></div>
      {groups && groups.length > 0 && (
        <div className="text-xs text-gray-500">Grupy: {groups.map((g, idx) => g.expr ? <span key={idx} className="mx-1">{g.expr}</span> : null)}</div>
      )}
    </div>
  );
}

export default KMapDisplay; 