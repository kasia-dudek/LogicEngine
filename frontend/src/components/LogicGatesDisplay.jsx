// frontend/src/components/LogicGatesDisplay.jsx
import React, { useRef, useEffect, useState, useMemo } from 'react';
import * as d3 from 'd3';
import { OP_DEFS } from './ASTDisplay';

/* ---------- Konfiguracja wyglądu / layoutu ---------- */
const INPUT_RAIL   = 260;  // odległość szyny wejściowej od środka bramki
const OUTPUT_RAIL  = 220;  // długość linii wyjścia do Y
const V_GAP        = 96;   // pionowy rozstaw bramek na tym samym poziomie
const GATE_SPACING = 180;  // odległość pozioma pomiędzy poziomami
const MARGIN       = 70;   // marginesy rysunku

/* Kolory dla poszczególnych zmiennych wejściowych */
const VAR_COLORS = [
  '#2563eb', // A
  '#059669', // B
  '#7c3aed', // C
  '#ea580c', // D
  '#db2777', // E
  '#0891b2', '#65a30d', '#9333ea', '#f59e0b', '#0ea5e9',
];

/* ---------- Słowniki bramek ---------- */
const GATE_MAP = {
  NOT:    { symbol: 'NOT', name: 'NOT',     inputs: 1, color: '#dc2626' },
  AND:    { symbol: 'AND', name: 'AND',     inputs: 2, color: '#2563eb' },
  OR:     { symbol: 'OR',  name: 'OR',      inputs: 2, color: '#059669' },
  NAND:   { symbol: 'NAND',name: 'NAND',    inputs: 2, color: '#d97706' },
  NOR:    { symbol: 'NOR', name: 'NOR',     inputs: 2, color: '#7c3aed' },
  XOR:    { symbol: 'XOR', name: 'XOR',     inputs: 2, color: '#0891b2' },
  XNOR:   { symbol: 'XNOR',name: 'XNOR',    inputs: 2, color: '#db2777' },
  IMPLIES:{ symbol: '→',   name: 'IMPLIES', inputs: 2, color: '#ea580c' },
  IFF:    { symbol: '↔',   name: 'IFF',     inputs: 2, color: '#65a30d' },
};

const SYMBOL_MAP = {
  '¬': 'NOT',
  '∧': 'AND',
  '∨': 'OR',
  '↑': 'NAND',
  '↓': 'NOR',
  '⊕': 'XOR',
  '≡': 'XNOR',
  '→': 'IMPLIES',
  '↔': 'IFF',
};

// Mapowanie typów bramek na symbole operatorów dla tooltipów
const GATE_TO_SYMBOL = {
  'NOT': '¬',
  'AND': '∧',
  'OR': '∨',
  'NAND': '↑',
  'NOR': '↓',
  'XOR': '⊕',
  'XNOR': '≡',
  'IMPLIES': '→',
  'IFF': '↔',
};

/* =======================================================
   AST -> graf bramek
======================================================= */
function astToGates(node, nextId = 0) {
  if (!node) return { gates: [], connections: [], nextId, output: null };

  if (typeof node === 'string') {
    return { gates: [], connections: [], nextId, output: `input:${node}` };
  }
  if (node.op === 'VAR') {
    const label = node.name || node.var || 'X';
    return { gates: [], connections: [], nextId, output: `input:${label}` };
  }
  if (node.op === 'CONST') {
    const label = node.value ? '1' : '0';
    return { gates: [], connections: [], nextId, output: `input:${label}` };
  }

  if (node.node && !node.op) {
    const op = SYMBOL_MAP[node.node] || node.node;
    if (op === 'NOT') return astToGates({ op: 'NOT', child: node.child }, nextId);
    if (['AND','OR','NAND','NOR','XOR','XNOR','IMPLIES','IFF'].includes(op)) {
      return astToGates({ op, args: [node.left, node.right] }, nextId);
    }
  }

  if (!node.op) return { gates: [], connections: [], nextId, output: null };
  const op = node.op;
  const gateDef = GATE_MAP[op];
  if (!gateDef) return { gates: [], connections: [], nextId, output: null };

  if (op === 'NOT') {
    const inG = astToGates(node.child, nextId + 1);
    const myId = nextId;
    const gateNode = {
      id: myId, type: 'NOT', x: 0, y: 0,
      inputs: [inG.output],
      output: `gate_${myId}`,
      gate: gateDef,
    };
    return {
      gates: [gateNode, ...inG.gates],
      connections: [...inG.connections, { from: inG.output, to: `gate_${myId}` }],
      nextId: inG.nextId,
      output: `gate_${myId}`,
    };
  }

  const args = node.args && node.args.length ? node.args : [node.left, node.right].filter(Boolean);
  if (!args.length) return { gates: [], connections: [], nextId, output: null };

  let acc = { gates: [], connections: [], nextId, output: null };
  for (let i = 0; i < args.length; i++) {
    const g = astToGates(args[i], acc.nextId + 1);
    if (i === 0) {
      acc = { gates: [...g.gates], connections: [...g.connections], nextId: g.nextId, output: g.output };
      continue;
    }
    const myId = acc.nextId;
    const gateType = SYMBOL_MAP[op] || op; // Mapuj symbol na typ bramki
    const gateNode = {
      id: myId, type: gateType, x: 0, y: 0,
      inputs: [acc.output, g.output],
      output: `gate_${myId}`,
      gate: gateDef,
    };
    acc = {
      gates: [gateNode, ...acc.gates, ...g.gates],
      connections: [
        ...acc.connections,
        ...g.connections,
        { from: acc.output, to: `gate_${myId}` },
        { from: g.output,  to: `gate_${myId}` },
      ],
      nextId: myId + 1,
      output: `gate_${myId}`,
    };
  }
  return acc;
}

/* =======================================================
   Rysowanie pojedynczej bramki
======================================================= */
function drawGate(svg, gate, x, y) {
  const group = svg.append('g').attr('class', 'gate').attr('transform', `translate(${x}, ${y})`);
  const width = 84, height = 64;

  const stroke = '#1f2937';
  const face = gate.gate.color;

  if (gate.type === 'NOT') {
    group.append('polygon')
      .attr('points', `-${width/2},-${height/2} ${width/2-6},0 -${width/2},${height/2}`)
      .attr('fill', face).attr('stroke', stroke).attr('stroke-width', 2);
    group.append('circle')
      .attr('cx', width/2 + 4).attr('cy', 0).attr('r', 6)
      .attr('fill', 'white').attr('stroke', stroke).attr('stroke-width', 2);
  } else if (gate.type === 'AND' || gate.type === 'NAND') {
    group.append('path')
      .attr('d', `M -${width/2},-${height/2} L ${width/2-18},-${height/2} A 18,18 0 0,1 ${width/2-18},${height/2} L -${width/2},${height/2} Z`)
      .attr('fill', face).attr('stroke', stroke).attr('stroke-width', 2);
    if (gate.type === 'NAND') {
      group.append('circle')
        .attr('cx', width/2 - 10).attr('cy', 0).attr('r', 6)
        .attr('fill', 'white').attr('stroke', stroke).attr('stroke-width', 2);
    }
  } else if (gate.type === 'OR' || gate.type === 'NOR' || gate.type === 'XOR') {
    group.append('path')
      .attr('d', `M -${width/2-2},-${height/2} Q -${width/2+14},0 -${width/2-2},${height/2} L ${width/2-18},${height/2} A 18,18 0 0,1 ${width/2-18},-${height/2} Z`)
      .attr('fill', face).attr('stroke', stroke).attr('stroke-width', 2);
    if (gate.type === 'XOR') {
      group.append('path')
        .attr('d', `M -${width/2+6},-${height/2} Q -${width/2+22},0 -${width/2+6},${height/2}`)
        .attr('fill', 'none').attr('stroke', stroke).attr('stroke-width', 2);
    }
    if (gate.type === 'NOR') {
      group.append('circle')
        .attr('cx', width/2 - 10).attr('cy', 0).attr('r', 6)
        .attr('fill', 'white').attr('stroke', stroke).attr('stroke-width', 2);
    }
  } else {
    group.append('rect')
      .attr('x', -width/2).attr('y', -height/2)
      .attr('width', width).attr('height', height)
      .attr('rx', 16).attr('ry', 16)
      .attr('fill', face).attr('stroke', stroke).attr('stroke-width', 2);
  }

  // Pozycjonowanie tekstu - przesunięcie w lewo dla asymetrycznych bramek
  let textX = 0;
  if (gate.type === 'NOT') {
    textX = -8; // NOT ma trójkąt, tekst przesunięty w lewo
  } else if (gate.type === 'AND' || gate.type === 'NAND') {
    textX = -8; // AND ma D-kształt, tekst przesunięty w lewo
  } else if (gate.type === 'OR' || gate.type === 'NOR' || gate.type === 'XOR') {
    textX = -8; // OR ma zakrzywiony kształt, tekst przesunięty w lewo
  }

  group.append('text')
    .attr('x', textX).attr('text-anchor', 'middle').attr('dy', '0.35em')
    .attr('fill', 'white').attr('font-size', 16).attr('font-weight', 'bold')
    .text(gate.gate.symbol);


  return group;
}

/* ---------- pomocnicze ---------- */
function inputDyForIndex(gate, idx) {
  if (gate.gate.inputs !== 2) return 0;
  return idx === 0 ? -16 : 16;
}

// Rzeczywiste krawędzie bramek - linie "wchodzą" w bramki o 1-2px żeby wizualnie się łączyły
function getGateLeftEdge(gate) {
  const width = 110;
  const overlap = 2; // linie wchodzą w bramkę o 2px
  
  if (gate.type === 'OR' || gate.type === 'NOR' || gate.type === 'XOR') {
    // OR: lewa krawędź na -53, linia wchodzi w bramkę
    return gate.x - (width/2 - 2) + overlap;
  }
  // Pozostałe bramki: lewa krawędź na -55, linia wchodzi w bramkę
  return gate.x - width/2 + overlap;
}

function getGateRightEdge(gate) {
  const width = 110;
  const overlap = 2; // linie wchodzą w bramkę o 2px
  
  if (gate.type === 'NOT') {
    // NOT: prawa krawędź na 49, linia wchodzi w bramkę
    return gate.x + (width/2 - 6) - overlap;
  } else if (gate.type === 'AND' || gate.type === 'NAND' || gate.type === 'OR' || gate.type === 'NOR' || gate.type === 'XOR') {
    // AND/OR: prawa krawędź na 37, linia wchodzi w bramkę
    return gate.x + (width/2 - 18) - overlap;
  }
  // Pozostałe bramki: prawa krawędź na 55, linia wchodzi w bramkę
  return gate.x + width/2 - overlap;
}

/* =======================================================
   Połączenia – ortogonalne ścieżki (gate→gate)
======================================================= */
function drawConnection(gConns, from, to, gates) {
  const toGate = gates.find(g => g.output === to);
  if (!toGate) return;

  if (from.startsWith('input:')) return;

  const toIdx = Math.max(0, toGate.inputs.indexOf(from));
  const toY   = toGate.y + inputDyForIndex(toGate, toIdx);
  const toX   = getGateLeftEdge(toGate); // rzeczywista lewa krawędź bramki

  const fromGate = gates.find(g => g.output === from);
  if (!fromGate) return;

  const fromX = getGateRightEdge(fromGate); // rzeczywista prawa krawędź bramki
  const fromY = fromGate.y;
  const midX  = (fromX + toX) / 2;

  gConns.append('path')
    .attr('d', `M ${fromX} ${fromY} L ${midX} ${fromY} L ${midX} ${toY} L ${toX} ${toY}`)
    .attr('stroke', '#3b82f6').attr('stroke-width', 3)
    .attr('fill', 'none').attr('opacity', 0.9);
}

/* =======================================================
   WSPÓLNE WEJŚCIA: jedna magistrala + JEDNA kolumna rozgałęzień
   — z kolorami per zmienna i stałym rozstawem pinów (bez nakładania).
======================================================= */
function drawSharedInputs(gConns, gLabels, gates, railX) {
  // Zbierz cele per zmienna
  const byVar = new Map();
  gates.forEach(gate => {
    gate.inputs.forEach((inp, idx) => {
      if (!inp.startsWith('input:')) return;
      const label = inp.slice('input:'.length);
      const toY   = gate.y + inputDyForIndex(gate, idx);
      const toX   = getGateLeftEdge(gate); // rzeczywista lewa krawędź bramki
      const list  = byVar.get(label) || [];
      list.push({ toX, toY });
      byVar.set(label, list);
    });
  });

  const labels = Array.from(byVar.keys()).sort();
  if (!labels.length) return;

  // Różne kolumny rozgałęzień dla każdej zmiennej (żeby linie się nie pokrywały)
  const BRANCH_BASE = railX + 30;
  const BRANCH_STEP = 15; // odległość między kolumnami

  // GLOBALNY zakres Y wszystkich celów – posłuży do rozstawienia pinów
  const allYs = [];
  byVar.forEach(arr => arr.forEach(t => allYs.push(t.toY)));
  const globalMin = Math.min(...allYs);
  const globalMax = Math.max(...allYs);
  const PAD = 18;
  const bandMin = globalMin - PAD;
  const bandMax = globalMax + PAD;

  // Stały rozstaw pinów (żeby A/B się nie nakładały)
  const PIN_STACK = 26;
  const centerY   = (bandMin + bandMax) / 2;

  labels.forEach((label, i) => {
    const targets = byVar.get(label);
    const color   = VAR_COLORS[i % VAR_COLORS.length];
    
    // Każda zmienna ma swoją kolumnę zagięcia
    const BRANCH_COL = BRANCH_BASE + i * BRANCH_STEP;

    // pin umieszczamy według indeksu, symetrycznie wokół centerY
    const yPin = Math.round(centerY + (i - (labels.length - 1) / 2) * PIN_STACK);

    // zakres pnia dla TEJ zmiennej (między jej celami)
    const ys   = targets.map(t => t.toY);
    const yMin = Math.min(...ys);
    const yMax = Math.max(...ys);

    // PIN + etykieta
    gLabels.append('text')
      .attr('x', railX - 16).attr('y', yPin + 5).attr('text-anchor', 'end')
      .attr('fill', '#111827').attr('font-size', 16).attr('font-weight', 'bold')
      .text(label);

    // pin -> kolumna (każda zmienna ma swoją kolumnę)
    gConns.append('path')
      .attr('d', `M ${railX} ${yPin} L ${BRANCH_COL} ${yPin}`)
      .attr('stroke', color).attr('stroke-width', 3).attr('fill', 'none').attr('opacity', 0.95);

    // pionowy pień zmiennej
    if (yMax !== yMin) {
      gConns.append('path')
        .attr('d', `M ${BRANCH_COL} ${yMin} L ${BRANCH_COL} ${yMax}`)
        .attr('stroke', color).attr('stroke-width', 3).attr('fill', 'none').attr('opacity', 0.95);
    }

    // połącz pin z pniem, jeśli pin wypadł poza [yMin,yMax]
    if (yPin < yMin) {
      gConns.append('path')
        .attr('d', `M ${BRANCH_COL} ${yPin} L ${BRANCH_COL} ${yMin}`)
        .attr('stroke', color).attr('stroke-width', 3).attr('fill', 'none').attr('opacity', 0.95);
    } else if (yPin > yMax) {
      gConns.append('path')
        .attr('d', `M ${BRANCH_COL} ${yPin} L ${BRANCH_COL} ${yMax}`)
        .attr('stroke', color).attr('stroke-width', 3).attr('fill', 'none').attr('opacity', 0.95);
    }

    // odnogi do pinów bramek + kropeczki „T”
    targets.forEach(({ toX, toY }) => {
      gConns.append('path')
        .attr('d', `M ${BRANCH_COL} ${toY} L ${toX} ${toY}`)
        .attr('stroke', color).attr('stroke-width', 3).attr('fill', 'none').attr('opacity', 0.95);

    });
  });
}

/* Wyjście Y – linia + pin + etykieta */
function drawOutputY(gConns, gLabels, lastGate) {
  if (!lastGate) return;
  const fromX = getGateRightEdge(lastGate); // rzeczywista prawa krawędź bramki
  const fromY = lastGate.y;
  const endX  = lastGate.x + OUTPUT_RAIL;
  const endY  = fromY;

  gConns.append('path')
    .attr('d', `M ${fromX} ${fromY} L ${endX} ${endY}`)
    .attr('stroke', '#3b82f6').attr('stroke-width', 3)
    .attr('fill', 'none').attr('opacity', 0.95);

  gLabels.append('text')
    .attr('x', endX + 18).attr('y', endY + 5).attr('text-anchor', 'start')
    .attr('fill', '#1f2937').attr('font-size', 16).attr('font-weight', 'bold')
    .text('Y');
}

/* =======================================================
   Komponent
======================================================= */
export default function LogicGatesDisplay({ ast }) {
  const svgRef = useRef(null);
  const [tooltip, setTooltip] = useState({ visible: false, x: 0, y: 0, content: null });

  const gatesData = useMemo(() => {
    if (!ast) return { gates: [], connections: [], output: null };
    return astToGates(ast);
  }, [ast]);

  useEffect(() => {
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    if (!gatesData.gates.length) {
      const w = 820, h = 240;
      svg.attr('viewBox', `0 0 ${w} ${h}`).attr('width', '100%').attr('height', h);
      svg.append('text')
        .attr('x', w/2).attr('y', 36).attr('text-anchor', 'middle')
        .attr('fill', '#374151').attr('font-size', 18).attr('font-weight', 'bold')
      return;
    }

    const defs = svg.append('defs');
    defs.append('linearGradient')
      .attr('id', 'lineGradient').attr('x1', '0%').attr('y1', '0%').attr('x2', '100%').attr('y2', '0%')
      .selectAll('stop')
      .data([{o:'0% ',c:'#3b82f6'},{o:'100%',c:'#1d4ed8'}])
      .enter().append('stop').attr('offset', d=>d.o).attr('stop-color', d=>d.c);


    defs.append('filter').attr('id', 'gateShadow')
      .append('feDropShadow').attr('dx', 2).attr('dy', 2).attr('stdDeviation', 3).attr('flood-opacity', 0.28);

    const gateLevels = new Map();
    const markLevels = (id, level=0) => {
      if (gateLevels.has(id)) return;
      gateLevels.set(id, level);
      const g = gatesData.gates.find(x => x.id === id);
      if (!g) return;
      g.inputs.forEach(inp => { if (inp.startsWith('gate_')) markLevels(parseInt(inp.slice(5), 10), level + 1); });
    };
    const outputs = gatesData.gates.filter(g => !gatesData.connections.some(c => c.from === g.output));
    outputs.forEach(g => markLevels(g.id, 0));

    const levelGroups = new Map();
    gatesData.gates.forEach(g => {
      const lv = gateLevels.get(g.id) ?? 0;
      if (!levelGroups.has(lv)) levelGroups.set(lv, []);
      levelGroups.get(lv).push(g);
    });

    const maxLevel = Math.max(...Array.from(levelGroups.keys()));
    const leftOffset  = MARGIN + INPUT_RAIL;
    const rightExtra  = MARGIN + OUTPUT_RAIL + 90;
    const svgH = 380;
    const svgW = Math.max(760, leftOffset + maxLevel*GATE_SPACING + rightExtra);

    svg.attr('viewBox', `0 0 ${svgW} ${svgH}`).attr('height', svgH).attr('width', '100%');

    levelGroups.forEach((arr, level) => {
      const levelX = leftOffset + (maxLevel - level) * GATE_SPACING;
      const levelY = svgH/2;
      arr.forEach((g, i) => {
        g.x = levelX;
        g.y = levelY + (i - (arr.length - 1)/2) * V_GAP;
      });
    });

    const minGateX = Math.min(...gatesData.gates.map(g => g.x));
    const railX    = minGateX - INPUT_RAIL;

    const gConns  = svg.append('g').attr('class', 'layer-conns');
    const gGates  = svg.append('g').attr('class', 'layer-gates');
    const gLabels = svg.append('g').attr('class', 'layer-labels');

    gatesData.gates.forEach(gate => {
      const g = drawGate(gGates, gate, gate.x, gate.y);
      g.selectAll('path, rect, polygon').attr('filter', 'url(#gateShadow)');
        g.on('mouseenter', (event) => {
          g.selectAll('path, rect, polygon').attr('stroke', '#f59e0b').attr('stroke-width', 3);
          
          // Pobierz definicję operatora z OP_DEFS
          const symbol = GATE_TO_SYMBOL[gate.type];
          const opDef = OP_DEFS[symbol];
          
          
          const content = (
            <div>
              {opDef ? (
                <>
                  <div className="font-bold text-base mb-1">{opDef.name}</div>
                  <div className="mb-2 text-xs">{opDef.desc}</div>
                  <div className="mb-2 text-xs">Bramka logiczna | Wejścia: {gate.gate.inputs}</div>
                  {opDef.table && (
                    <table className="border border-blue-200 rounded mb-1 text-xs">
                      <tbody>
                        {opDef.table.map((row, i) => (
                          <tr key={i}>
                            {row.map((cell, j) => (
                              <td key={j} className={`px-2 py-1 border ${i === 0 ? 'bg-blue-100 font-semibold' : ''}`}>
                                {cell}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </>
              ) : (
                <>
                  <div className="font-bold text-base mb-1">BŁĄD: {gate.type}</div>
                  <div className="mb-2 text-xs">Bramka logiczna</div>
                  <div className="text-xs">Wejścia: {gate.gate.inputs}</div>
                  <div className="text-xs text-red-400">Symbol: {symbol}</div>
                </>
              )}
            </div>
          );
          // Użyj tej samej metody co w AST
          const svgEl = svgRef.current;
          const pt = svgEl.createSVGPoint(); 
          pt.x = gate.x; 
          pt.y = gate.y;
          const ctm = svgEl.getScreenCTM();
          const { x, y } = pt.matrixTransform(ctm);
          const rect = svgEl.parentNode.getBoundingClientRect();
          const tooltipX = x - rect.left + 40;
          const tooltipY = y - rect.top;
          setTooltip({ visible: true, x: tooltipX, y: tooltipY, content });
        }).on('mouseleave', () => {
          g.selectAll('path, rect, polygon').attr('stroke', '#1f2937').attr('stroke-width', 2);
          setTooltip({ visible: false, x: 0, y: 0, content: null });
        });
    });

    gatesData.connections.forEach(c => drawConnection(gConns, c.from, c.to, gatesData.gates));
    drawSharedInputs(gConns, gLabels, gatesData.gates, railX);

    const lastGate = gatesData.gates.find(g => !gatesData.connections.some(c => c.from === g.output));
    if (lastGate) drawOutputY(gConns, gLabels, lastGate);

    svg.append('text')
      .attr('x', svgW/2).attr('y', 34).attr('text-anchor', 'middle')
      .attr('fill', '#374151').attr('font-size', 18).attr('font-weight', 'bold')
      .text('Schemat bramek logicznych');

  }, [gatesData]);

  if (!ast) return <div className="text-gray-500">Brak danych do wyświetlenia bramek logicznych.</div>;

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-full" style={{ maxWidth: 1280 }}>
        <svg
          ref={svgRef}
          className="w-full bg-gradient-to-br from-blue-50 via-white to-purple-50 rounded-2xl shadow-2xl border border-gray-300"
        />
        {tooltip.visible && (
          <div
            className="absolute z-50 px-3 py-2 rounded-xl bg-blue-700 text-white text-xs font-semibold shadow-lg pointer-events-none animate-fade-in"
            style={{ left: tooltip.x, top: tooltip.y, minWidth: 120 }}
          >
            {tooltip.content}
          </div>
        )}
      </div>
      <div className="text-sm text-gray-600 mt-3 font-medium">
        Najedź na bramkę, aby zobaczyć definicję operatora i tabelę prawdy
      </div>
    </div>
  );
}
