import React, { useMemo, useState } from "react";

/**
 * Tryby:
 *  1) BACKEND-ONLY: podaj kmap, groups/all_groups, result.
 *  2) FRONTEND-COMPUTE: dodatkowo podaj vars (string[]) i minterms (number[]):
 *     - dropdowny osi (wiersze/kolumny),
 *     - przeliczanie K-map/PI/wariantów FE,
 *     - tooltipy z mintermem/binarką.
 */

const groupStyles = [
  { cell: "bg-blue-200 border-blue-400", dot: "bg-blue-500" },
  { cell: "bg-green-200 border-green-400", dot: "bg-green-500" },
  { cell: "bg-yellow-200 border-yellow-400", dot: "bg-yellow-500" },
  { cell: "bg-pink-200 border-pink-400", dot: "bg-pink-500" },
  { cell: "bg-purple-200 border-purple-400", dot: "bg-purple-500" },
  { cell: "bg-orange-200 border-orange-400", dot: "bg-orange-500" },
  { cell: "bg-red-200 border-red-400", dot: "bg-red-500" },
  { cell: "bg-teal-200 border-teal-400", dot: "bg-teal-500" },
];

const GRAY = {
  0: [0],
  1: [0, 1],
  2: [0, 1, 3, 2],
};

function grayLabels(bits) {
  if (bits === 0) return [""];
  if (bits === 1) return ["0", "1"];
  if (bits === 2) return ["00", "01", "11", "10"];
  return [];
}

function defaultAxis(vars) {
  const n = vars.length;
  if (n === 1) return { rowVars: [], colVars: [vars[0]] };
  if (n === 2) return { rowVars: [vars[0]], colVars: [vars[1]] };
  if (n === 3) return { rowVars: [vars[0]], colVars: [vars[1], vars[2]] };
  return { rowVars: [vars[0], vars[1]], colVars: [vars[2], vars[3]] };
}

function bitAt(num, posFromMsb, width) {
  return (num >> (width - 1 - posFromMsb)) & 1;
}

function toBin(n, width) {
  return n.toString(2).padStart(width, "0");
}


/** Zbuduj indeks mintermu z wartości bitów przypisanych do zmiennych. */
function assignmentToMinterm(vars, assign) {
  let idx = 0;
  const n = vars.length;
  for (let i = 0; i < n; i++) {
    const v = vars[i];
    idx = (idx << 1) | (assign[v] ? 1 : 0);
  }
  return idx;
}

/** Mapa Karnaugha z mintermów dla zadanej osi. */
function buildKmapFromMinterms(vars, minterms, rowVars, colVars) {
  const rBits = rowVars.length;
  const cBits = colVars.length;
  const rowOrder = GRAY[rBits];
  const colOrder = GRAY[cBits];

  const nRows = rowOrder.length;
  const nCols = colOrder.length;
  const kmap = Array.from({ length: nRows }, () => Array.from({ length: nCols }, () => 0));

  const cellToMint = (ri, ci) => {
    const rVal = rowOrder[ri];
    const cVal = colOrder[ci];
    const assign = {};
    for (let k = 0; k < rBits; k++) assign[rowVars[k]] = !!bitAt(rVal, k, rBits);
    for (let k = 0; k < cBits; k++) assign[colVars[k]] = !!bitAt(cVal, k, cBits);
    return assignmentToMinterm(vars, assign);
  };

  for (let i = 0; i < nRows; i++) {
    for (let j = 0; j < nCols; j++) {
      const m = cellToMint(i, j);
      kmap[i][j] = minterms.includes(m) ? 1 : 0;
    }
  }

  return { kmap, rowOrder, colOrder, cellToMint };
}

/** PI w JS – prostokąty z zawijaniem; dedupe; odrzucanie podgrup. */
function findPI(kmap, cellToMint) {
  const rows = kmap.length;
  const cols = kmap[0].length;

  const pow2 = (limit) => {
    const out = [1];
    for (let x = 2; x <= limit; x *= 2) out.push(x);
    return out;
  };

  const hOpts = pow2(rows);
  const wOpts = pow2(cols);

  const rectCells = (r0, c0, h, w) => {
    const out = [];
    for (let dr = 0; dr < h; dr++) {
      for (let dc = 0; dc < w; dc++) {
        out.push([(r0 + dr) % rows, (c0 + dc) % cols]);
      }
    }
    return out;
  };

  const all = new Map(); // key => group
  const areas = Array.from(new Set(hOpts.flatMap((h) => wOpts.map((w) => h * w)))).sort((a, b) => b - a);

  for (const area of areas) {
    for (const h of hOpts) {
      if (area % h) continue;
      const w = area / h;
      if (!wOpts.includes(w)) continue;
      for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
          const cells = rectCells(r, c, h, w);
          if (cells.every(([rr, cc]) => kmap[rr][cc] === 1)) {
            const mints = cells.map(([rr, cc]) => cellToMint(rr, cc));
            const uniq = [...new Set(mints)].sort((a, b) => a - b);
            const key = uniq.join(",");
            if (!key) continue;
            if (!all.has(key)) all.set(key, { cells, size: cells.length, minterms: uniq });
          }
        }
      }
    }
  }

  const groups = [...all.values()];
  // wywal ściśle zawarte w większych
  const primes = groups.filter((gi, i) => {
    return !groups.some((gj, j) => i !== j && gi.minterms.every((m) => gj.minterms.includes(m)));
  });

  primes.sort((a, b) => b.size - a.size || a.minterms.length - b.minterms.length);
  return primes;
}

/** Wspólny wzorzec binarny i expr dla grupy. Pusty iloczyn => '1'. */
function groupExpr(group, vars, n) {
  const bins = group.minterms.map((m) => toBin(m, n).split(""));
  const common = Array(n).fill("-");
  for (let i = 0; i < n; i++) {
    const set = new Set(bins.map((b) => b[i]));
    if (set.size === 1) common[i] = [...set][0];
  }
  const parts = [];
  for (let i = 0; i < n; i++) {
    if (common[i] === "1") parts.push(vars[i]);
    else if (common[i] === "0") parts.push(`¬${vars[i]}`);
  }
  const expr = parts.length ? `(${parts.join(" ∧ ")})` : "1";
  const literals = parts.length; // dla '1' = 0
  return { pattern: common.join(""), expr, literals };
}

/** Wszystkie minimalne pokrycia (wg. #termów, a potem suma literałów). */
function enumerateMinimalCovers(minterms, groups) {
  const ONES = new Set(minterms);
  const coverMap = {};
  for (const m of ONES) coverMap[m] = [];
  groups.forEach((g, i) => {
    g.cover = g.minterms.filter((m) => ONES.has(m));
    const { expr, literals } = g;
    g.literals = expr === "1" ? 0 : literals;
    g.index = i;
    g.gain = g.cover.length;
    for (const m of g.cover) coverMap[m].push(i);
  });

  // niezbędne
  const essential = new Set();
  for (const m of ONES) {
    const owners = coverMap[m] || [];
    if (owners.length === 1) essential.add(owners[0]);
  }

  const gCoverInto = (g, set) => g.cover.forEach((m) => set.add(m));

  const baseCovered = new Set();
  essential.forEach((i) => gCoverInto(groups[i], baseCovered));
  const remaining = [...ONES].filter((m) => !baseCovered.has(m));

  if (remaining.length === 0) {
    const indices = [...essential].sort((a, b) => a - b);
    const expr = indices.map((i) => groups[i].expr).join(" ∨ ") || "0";
    const lits = indices.reduce((s, i) => s + (groups[i].expr === "1" ? 0 : groups[i].literals), 0);
    return [{ indices, expr, terms: indices.length, literals: lits }];
  }

  let best = { terms: Infinity, literals: Infinity };
  const results = [];

  function dfs(start, picked, covered, litsSum) {
    if (picked.length > best.terms) return;
    if (picked.length === best.terms && litsSum > best.literals) return;

    if (covered.size === ONES.size) {
      if (picked.length < best.terms || (picked.length === best.terms && litsSum < best.literals)) {
        best = { terms: picked.length, literals: litsSum };
        results.length = 0;
      }
      results.push([...picked].sort((a, b) => a - b));
      return;
    }

    for (let i = start; i < groups.length; i++) {
      if (essential.has(i)) continue;
      const g = groups[i];
      if (g.gain === 0) continue;

      const newCovered = new Set(covered);
      gCoverInto(g, newCovered);
      const newPicked = [...picked, i];
      dfs(i + 1, newPicked, newCovered, litsSum + (g.expr === "1" ? 0 : g.literals));
    }
  }

  dfs(0, [], new Set(baseCovered), 0);

  return results.map((idxs) => {
    const indices = [...essential, ...idxs].sort((a, b) => a - b);
    const expr = indices.map((i) => groups[i].expr).join(" ∨ ") || "0";
    const literals = indices.reduce((s, i) => s + (groups[i].expr === "1" ? 0 : groups[i].literals), 0);
    return { indices, expr, terms: indices.length, literals };
  });
}

/** Detekcja zawijania — nie zaznaczaj, gdy grupa pokrywa całą oś. */
function detectWrap(cells, nRows, nCols) {
  const rows = new Set(cells.map(([r]) => r));
  const cols = new Set(cells.map(([, c]) => c));
  const wrapH = cols.has(0) && cols.has(nCols - 1) && cols.size < nCols;
  const wrapV = rows.has(0) && rows.has(nRows - 1) && rows.size < nRows;
  return { wrapH, wrapV };
}

/** ————— PUBLICZNY KOMPONENT ————— */
export default function KMapDisplay(props) {
  const { vars, minterms, error } = props;
  const backendOnly = !Array.isArray(vars) || !Array.isArray(minterms);
  if (backendOnly) return <KMapBackendOnly {...props} error={error} />;
  return <KMapWithAxis {...props} />;
}

/** ————— TRYB: BACKEND ONLY ————— */
function KMapBackendOnly({ kmap, groups = [], all_groups = [], showAll = false, result, error }) {
  if (error) {
    return (
      <div className="text-center p-8 bg-yellow-50 border border-yellow-200 rounded-lg">
        <div className="text-yellow-800 font-semibold mb-2">
          ⚠️ Mapa Karnaugha niedostępna
        </div>
        <div className="text-yellow-700">
          {error}
        </div>
      </div>
    );
  }

  if (!kmap || !Array.isArray(kmap) || !kmap.length || !Array.isArray(kmap[0]) || !kmap[0].length) {
    return (
      <div className="text-red-600 font-semibold">
        Brak poprawnych danych do wyświetlenia mapy Karnaugha.
        <br />Sprawdź, czy wyrażenie nie ma zbyt wielu zmiennych (max 4) i czy backend zwraca dane.
      </div>
    );
  }

  const nRows = kmap.length;
  const nCols = kmap[0].length;
  const rowLabels = grayLabels(nRows === 1 ? 0 : nRows === 2 ? 1 : 2);
  const colLabels = grayLabels(nCols === 1 ? 0 : nCols === 2 ? 1 : 2);

  let incoming = showAll ? all_groups : groups;
  if (!showAll && incoming.length && typeof incoming[0]?.selected === "boolean") {
    incoming = incoming.filter((g) => g.selected);
  }

  const highlightMap = Array.from({ length: nRows }, () => Array.from({ length: nCols }, () => []));
  incoming.forEach((group, gidx) => (group.cells || []).forEach(([r, c]) => highlightMap[r][c].push(gidx + 1)));

  return (
    <KMapTable
      kmap={kmap}
      rowLabels={rowLabels}
      colLabels={colLabels}
      groups={incoming}
      highlightMap={highlightMap}
      result={result}
      showAxisMeta={false}
      axisText={{ rows: "", cols: "" }}
    />
  );
}

/** ————— TRYB: FRONTEND COMPUTE ————— */
function KMapWithAxis({ vars, minterms, result: resultFromBE }) {
  const n = vars.length;
  const [rowVars, setRowVars] = useState(defaultAxis(vars).rowVars);
  const [colVars, setColVars] = useState(defaultAxis(vars).colVars);

  const { kmap, cellToMint } = useMemo(
    () => buildKmapFromMinterms(vars, minterms, rowVars, colVars),
    [vars, minterms, rowVars, colVars]
  );

  const piGroups = useMemo(() => {
    const PIs = findPI(kmap, cellToMint);
    return PIs.map((g) => {
      const { expr, literals } = groupExpr(g, vars, n);
      return { ...g, expr, literals };
    });
  }, [kmap, cellToMint, vars, n]);

  const variants = useMemo(() => enumerateMinimalCovers(minterms, piGroups), [minterms, piGroups]);

  const [variantIdx, setVariantIdx] = useState(0);
  const activeVariant = variants[variantIdx] || { indices: [], expr: resultFromBE, terms: 0, literals: 0 };

  const selectedGroups = activeVariant.indices.map((i) => piGroups[i]);
  const nRows = kmap.length, nCols = kmap[0].length;
  const rowLabels = grayLabels(rowVars.length);
  const colLabels = grayLabels(colVars.length);
  const axisText = { rows: rowVars.join("") || "—", cols: colVars.join("") || "—" };

  const highlightMap = useMemo(() => {
    const map = Array.from({ length: nRows }, () => Array.from({ length: nCols }, () => []));
    selectedGroups.forEach((g, gidx) => (g.cells || []).forEach(([r, c]) => map[r][c].push(gidx + 1)));
    return map;
  }, [selectedGroups, nRows, nCols]);

  const tooltip = (i, j) => {
    const m = cellToMint(i, j);
    const bin = toBin(m, n);
    const assign = vars.map((v, idx) => `${v}=${bin[idx]}`).join(", ");
    return `m=${m}  (${bin})\n${assign}`;
  };

  const controls = (
    <div className="flex items-center gap-3 mb-3 flex-wrap">
      <div className="text-sm text-gray-700">Wiersze:</div>
      {rowVars.length > 0 && (
        <select
          className="px-2 py-1 border rounded"
          value={rowVars[0] || ""}
          onChange={(e) => {
            const v = e.target.value;
            if (n <= 2) {
              setRowVars([v]);
              setColVars(vars.filter((x) => x !== v));
            } else if (n === 3) {
              setRowVars([v]);
              setColVars(vars.filter((x) => x !== v));
            } else {
              const rest = vars.filter((x) => ![v, rowVars[1]].includes(x));
              setRowVars([v, rowVars[1] || rest[0]]);
              setColVars(vars.filter((x) => ![v, rowVars[1] || rest[0]].includes(x)));
            }
          }}
        >
          {vars.map((v) => (
            <option key={v} value={v}>{v}</option>
          ))}
        </select>
      )}
      {n === 4 && (
        <select
          className="px-2 py-1 border rounded"
          value={rowVars[1] || ""}
          onChange={(e) => {
            const v = e.target.value;
            const first = rowVars[0] || vars[0];
            if (v === first) return;
            setRowVars([first, v]);
            setColVars(vars.filter((x) => ![first, v].includes(x)));
          }}
        >
          {vars.filter((x) => x !== rowVars[0]).map((v) => (
            <option key={v} value={v}>{v}</option>
          ))}
        </select>
      )}

      <div className="text-sm text-gray-700 ml-4">Kolumny:</div>
      <div className="px-2 py-1 text-sm bg-gray-50 border rounded">{colVars.join(", ") || "—"}</div>
    </div>
  );

  const variantsPanel = (
    <div className="flex items-center gap-2 mb-3 flex-wrap">
      <span className="text-sm text-gray-700">Warianty pokrycia:</span>
      {variants.length === 0 && <span className="text-sm text-gray-500">brak (zdefiniowane przez BE)</span>}
      {variants.length > 0 && (
        <>
          <div className="flex gap-1">
            {variants.map((v, idx) => (
              <button
                key={idx}
                onClick={() => setVariantIdx(idx)}
                className={`px-2 py-1 text-xs rounded border ${
                  idx === variantIdx ? "bg-blue-600 text-white border-blue-600" : "bg-white border-gray-300"
                }`}
                title={`termy: ${v.terms}, literały: ${v.literals}`}
              >
                {idx + 1}
              </button>
            ))}
          </div>
          <div className="text-xs text-gray-600">
            termy: <b>{activeVariant.terms}</b>, literały: <b>{activeVariant.literals}</b>
          </div>
        </>
      )}
    </div>
  );

  return (
    <div className="flex flex-col items-center">
      {controls}
      {variantsPanel}
      <KMapTable
        kmap={kmap}
        rowLabels={rowLabels}
        colLabels={colLabels}
        groups={selectedGroups}
        highlightMap={highlightMap}
        result={activeVariant.expr || resultFromBE}
        showAxisMeta
        axisText={axisText}
        tooltip={tooltip}
      />
    </div>
  );
}

/** ————— Renderer tabeli + legenda ————— */
function KMapTable({ kmap, rowLabels, colLabels, groups, highlightMap, result, showAxisMeta, axisText, tooltip }) {
  const [active, setActive] = useState(null);

  const anyWrap = useMemo(
    () =>
      groups.some((g) => {
        const { wrapH, wrapV } = detectWrap(g.cells || [], kmap.length, kmap[0]?.length || 1);
        return wrapH || wrapV;
      }),
    [groups, kmap]
  );

  return (
    <>
      {showAxisMeta && (
        <div className="text-sm text-gray-700 mb-2">
          wiersze: <b>{axisText.rows}</b> &nbsp;|&nbsp; kolumny: <b>{axisText.cols}</b>
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="border-2 border-blue-300 rounded-2xl shadow-xl mb-4 bg-white animate-fade-in">
          <thead>
            <tr>
              <th className="w-8 h-8" />
              {colLabels.map((cl, j) => (
                <th
                  key={j}
                  className="px-3 py-2 text-blue-700 bg-blue-50 border-b-2 border-blue-200 text-base font-bold text-center"
                >
                  {cl}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {kmap.map((row, i) => (
              <tr key={i}>
                <th className="px-3 py-2 text-blue-700 bg-blue-50 border-r-2 border-blue-200 text-base font-bold text-center">
                  {rowLabels[i]}
                </th>
                {row.map((val, j) => {
                  const ids = highlightMap[i][j] || [];
                  const first = ids[0] || 0;
                  const style = groupStyles[(first - 1 + groupStyles.length) % groupStyles.length];
                  const cellCls = first ? style.cell : "bg-white";
                  const borderCls = first ? style.cell.split(" ")[1] : "border-gray-300";
                  const isDimmed = active !== null && !ids.includes(active + 1);
                  const title = tooltip ? tooltip(i, j) : undefined;

                  return (
                    <td
                      key={j}
                      className={`w-14 h-14 text-center border-2 ${cellCls} ${borderCls} font-bold relative transition-all duration-200 ${
                        isDimmed ? "opacity-30" : ""
                      }`}
                      title={title}
                    >
                      <span className="text-lg">{val}</span>
                      {first ? (
                        <span className="absolute top-1 right-1 text-xs font-semibold text-blue-900">G{first}</span>
                      ) : null}
                      {ids.length > 1 ? (
                        <div className="absolute bottom-1 right-1 flex gap-0.5">
                          {ids.slice(1, 5).map((id) => {
                            const s = groupStyles[(id - 1) % groupStyles.length];
                            return <span key={id} className={`w-1.5 h-1.5 rounded-full ${s.dot}`} />;
                          })}
                        </div>
                      ) : null}
                      {/* Znak zapytania dla niewybranych grup */}
                      {!first && active === null && (
                        <span className="absolute top-1 right-1 text-xs font-semibold text-gray-400" title="Ta komórka nie jest w żadnej wybranej grupie">?</span>
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* legenda */}
      <div className="flex gap-2 mb-4 flex-wrap justify-center">
        {groups.map((g, idx) => {
          const s = groupStyles[idx % groupStyles.length];
          const activeCls = active === idx ? "ring-2 ring-offset-2 ring-blue-500" : "";
          const { wrapH, wrapV } = detectWrap(g.cells || [], kmap.length, kmap[0]?.length || 1);
          return (
            <button
              key={idx}
              type="button"
              onClick={() => setActive((a) => (a === idx ? null : idx))}
              className={`px-3 py-1 rounded-xl ${s.cell} border-2 font-semibold text-xs flex items-center gap-2 ${activeCls}`}
              title={g.minterms ? `Mintermy: ${g.minterms.join(", ")}` : undefined}
            >
              <span className={`w-3 h-3 rounded-full inline-block ${s.dot}`} />
              Grupa {idx + 1}: <span className="font-mono">{g.expr || ""}</span>
              {(wrapH || wrapV) && (
                <span className="ml-1 opacity-70">
                  {wrapH ? "↔" : ""} {wrapV ? "↕" : ""}
                </span>
              )}
            </button>
          );
        })}
      </div>

      <div className="text-lg text-blue-700 mb-2 font-semibold">
        Uproszczone: <span className="font-mono text-green-700">{result}</span>
      </div>

      {anyWrap && (
        <div className="text-xs text-gray-500 max-w-lg text-center">
          Niektóre grupy zawijają się przez krawędzie mapy (↔/↕). Kliknij chip grupy, aby ją odizolować.
        </div>
      )}
      {!anyWrap && groups.length > 0 && (
      <div className="text-xs text-gray-500 max-w-lg text-center">
          Kropki w komórce pokazują przynależność do dodatkowych grup. Kliknij chip grupy, aby ją odizolować.
      </div>
      )}
    </>
  );
}
