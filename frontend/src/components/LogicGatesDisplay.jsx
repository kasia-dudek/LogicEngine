// LogicGatesDisplay.jsx - Minimalistyczny schemat bramek logicznych
import React, { useRef, useEffect, useState, useMemo } from 'react';
import * as d3 from 'd3';
import { OP_DEFS } from './ASTDisplay';

// Kolory dla zmiennych wejściowych
const VAR_COLORS = [
  '#2563eb', '#059669', '#7c3aed', '#ea580c', '#db2777', 
  '#0891b2', '#65a30d', '#9333ea', '#f59e0b', '#0ea5e9'
];

// Mapowanie operatorów na typy bramek
const SYMBOL_TO_GATE = {
  '¬': 'NOT',
  '∧': 'AND', 
  '∨': 'OR',
  '↑': 'NAND',
  '↓': 'NOR',
  '⊕': 'XOR',
  '≡': 'XNOR',
  '→': 'IMPLIES',
  '↔': 'IFF'
};

// Konfiguracja bramek - ujednolicone wymiary
const GATE_CONFIG = {
  NOT: { width: 80, height: 50, symbol: '1', color: '#dc2626' },
  AND: { width: 80, height: 50, symbol: '&', color: '#2563eb' },
  OR: { width: 80, height: 50, symbol: '≥1', color: '#059669' },
  NAND: { width: 80, height: 50, symbol: '&', color: '#d97706' },
  NOR: { width: 80, height: 50, symbol: '≥1', color: '#7c3aed' },
  XOR: { width: 80, height: 50, symbol: '=1', color: '#0891b2' },
  XNOR: { width: 80, height: 50, symbol: '=1', color: '#db2777' },
  IMPLIES: { width: 80, height: 50, symbol: '→', color: '#ea580c' },
  IFF: { width: 80, height: 50, symbol: '↔', color: '#65a30d' }
};

// Konwersja AST na bramki
function astToGates(node, nextId = 0) {
  if (!node) return { gates: [], connections: [], nextId, output: null };

  // Zmienne wejściowe
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

  // Obsługa różnych formatów AST
  let op = node.op;
  if (node.node && !node.op) {
    op = SYMBOL_TO_GATE[node.node] || node.node;
  }

  if (!op) return { gates: [], connections: [], nextId, output: null };

  // Bramka NOT
  if (op === 'NOT') {
    const child = node.child || node.args?.[0];
    const childResult = astToGates(child, nextId + 1);
    const gateId = nextId;
    
    return {
      gates: [{
        id: gateId,
        type: 'NOT',
        x: 0, y: 0,
        inputs: [childResult.output],
        output: `gate_${gateId}`
      }, ...childResult.gates],
      connections: [
        ...childResult.connections,
        { from: childResult.output, to: `gate_${gateId}` }
      ],
      nextId: childResult.nextId,
      output: `gate_${gateId}`
    };
  }

  // Bramki dwuwejściowe
  const left = node.left || node.args?.[0];
  const right = node.right || node.args?.[1];
  
  if (!left || !right) return { gates: [], connections: [], nextId, output: null };

  const leftResult = astToGates(left, nextId + 1);
  const rightResult = astToGates(right, leftResult.nextId + 1);
  const gateId = rightResult.nextId;

  return {
    gates: [{
      id: gateId,
      type: op,
      x: 0, y: 0,
      inputs: [leftResult.output, rightResult.output],
      output: `gate_${gateId}`
    }, ...leftResult.gates, ...rightResult.gates],
    connections: [
      ...leftResult.connections,
      ...rightResult.connections,
      { from: leftResult.output, to: `gate_${gateId}` },
      { from: rightResult.output, to: `gate_${gateId}` }
    ],
    nextId: gateId + 1,
    output: `gate_${gateId}`
  };
}

// Rysowanie bramki z ujednoliconymi wymiarami
function drawGate(svg, gate, x, y) {
  const config = GATE_CONFIG[gate.type];
  if (!config) return;

  const group = svg.append('g').attr('class', 'gate').attr('transform', `translate(${x}, ${y})`);
  const width = config.width;
  const height = config.height;
  
  // Wszystkie bramki mają identyczne wymiary zewnętrzne
  group.append('rect')
    .attr('x', -width/2)
    .attr('y', -height/2)
    .attr('width', width)
    .attr('height', height)
    .attr('rx', 8)
    .attr('ry', 8)
    .attr('fill', 'none')
    .attr('stroke', 'none');
  
  // Rysowanie kształtu bramki wewnątrz prostokąta
  if (gate.type === 'NOT') {
    // NOT - trójkąt
    group.append('polygon')
      .attr('points', `-${width/2+8},-${height/2+8} ${width/2-16},0 -${width/2+8},${height/2-8}`)
      .attr('fill', config.color)
      .attr('stroke', '#1f2937')
      .attr('stroke-width', 2);
    
    // Kółko negacji
    group.append('circle')
      .attr('cx', width/2 - 12)
      .attr('cy', 0)
      .attr('r', 6)
      .attr('fill', 'white')
      .attr('stroke', '#1f2937')
      .attr('stroke-width', 2);
      
  } else if (gate.type === 'AND' || gate.type === 'NAND') {
    // AND/NAND - D-kształt
    group.append('path')
      .attr('d', `M -${width/2+8},-${height/2+8} L ${width/2-24},-${height/2+8} A 16,16 0 0,1 ${width/2-24},${height/2-8} L -${width/2+8},${height/2-8} Z`)
      .attr('fill', config.color)
      .attr('stroke', '#1f2937')
      .attr('stroke-width', 2);
    
    if (gate.type === 'NAND') {
      group.append('circle')
        .attr('cx', width/2 - 16)
        .attr('cy', 0)
        .attr('r', 6)
        .attr('fill', 'white')
        .attr('stroke', '#1f2937')
        .attr('stroke-width', 2);
    }
    
  } else if (gate.type === 'OR' || gate.type === 'NOR' || gate.type === 'XOR' || gate.type === 'XNOR') {
    // OR/NOR/XOR/XNOR - zakrzywiony kształt
    group.append('path')
      .attr('d', `M -${width/2+6},-${height/2+8} Q -${width/2+20},0 -${width/2+6},${height/2-8} L ${width/2-24},${height/2-8} A 16,16 0 0,1 ${width/2-24},-${height/2+8} Z`)
      .attr('fill', config.color)
      .attr('stroke', '#1f2937')
      .attr('stroke-width', 2);
    
    if (gate.type === 'XOR' || gate.type === 'XNOR') {
      group.append('path')
        .attr('d', `M -${width/2+14},-${height/2+8} Q -${width/2+28},0 -${width/2+14},${height/2-8}`)
        .attr('fill', 'none')
        .attr('stroke', '#1f2937')
        .attr('stroke-width', 2);
    }
    
    if (gate.type === 'NOR' || gate.type === 'XNOR') {
      group.append('circle')
        .attr('cx', width/2 - 16)
        .attr('cy', 0)
        .attr('r', 6)
        .attr('fill', 'white')
        .attr('stroke', '#1f2937')
        .attr('stroke-width', 2);
    }
    
  } else {
    // Pozostałe bramki - prostokąt
    group.append('rect')
      .attr('x', -width/2+8)
      .attr('y', -height/2+8)
      .attr('width', width-16)
      .attr('height', height-16)
      .attr('rx', 6)
      .attr('ry', 6)
      .attr('fill', config.color)
      .attr('stroke', '#1f2937')
      .attr('stroke-width', 2);
  }

  // Symbol bramki (tylko dla prostokątnych)
  if (gate.type === 'IMPLIES' || gate.type === 'IFF') {
    group.append('text')
      .attr('x', 0)
      .attr('y', 0)
      .attr('text-anchor', 'middle')
      .attr('dy', '0.35em')
      .attr('fill', 'white')
      .attr('font-size', 14)
      .attr('font-weight', 'bold')
      .text(config.symbol);
  }

  return group;
}

// Funkcja pomocnicza do obliczania krawędzi bramek - ujednolicone
function getGateRightEdge(gate) {
  const config = GATE_CONFIG[gate.type];
  const width = config?.width || 80;
  
  // Wszystkie bramki mają tę samą prawą krawędź
  return gate.x + width/2 - 8; // 8px margines od krawędzi
}

function getGateLeftEdge(gate) {
  const config = GATE_CONFIG[gate.type];
  const width = config?.width || 80;
  
  // Wszystkie bramki mają tę samą lewą krawędź
  return gate.x - width/2 + 8; // 8px margines od krawędzi
}

// Rysowanie połączenia
function drawConnection(svg, from, to, gates) {
  const toGate = gates.find(g => g.output === to);
  if (!toGate) return;

  const fromGate = gates.find(g => g.output === from);
  if (!fromGate) return;

  const fromX = getGateRightEdge(fromGate);
  const fromY = fromGate.y;
  const toX = getGateLeftEdge(toGate);
  const toY = toGate.y;

  const midX = (fromX + toX) / 2;

  svg.append('path')
    .attr('d', `M ${fromX} ${fromY} L ${midX} ${fromY} L ${midX} ${toY} L ${toX} ${toY}`)
    .attr('stroke', '#3b82f6')
    .attr('stroke-width', 2)
    .attr('fill', 'none');
}

// Rysowanie wejść
function drawInputs(svg, gates) {
  const inputs = new Map();
  
  gates.forEach(gate => {
    gate.inputs.forEach(input => {
      if (input.startsWith('input:')) {
        const label = input.slice(6);
        if (!inputs.has(label)) {
          inputs.set(label, []);
        }
        inputs.get(label).push(gate);
      }
    });
  });

  const inputLabels = Array.from(inputs.keys()).sort();
  const inputX = Math.min(...gates.map(g => g.x)) - 120;
  
  inputLabels.forEach((label, i) => {
    const color = VAR_COLORS[i % VAR_COLORS.length];
    const y = -100 + i * 40;
    
    // Etykieta wejścia
    svg.append('text')
      .attr('x', inputX - 10)
      .attr('y', y + 5)
      .attr('text-anchor', 'end')
      .attr('fill', '#1f2937')
      .attr('font-size', 16)
      .attr('font-weight', 'bold')
      .text(label);

    // Linia wejściowa
    const targetGates = inputs.get(label);
    const minY = Math.min(...targetGates.map(g => g.y));
    const maxY = Math.max(...targetGates.map(g => g.y));
    
    svg.append('path')
      .attr('d', `M ${inputX} ${y} L ${inputX} ${minY} L ${inputX} ${maxY}`)
      .attr('stroke', color)
      .attr('stroke-width', 3)
      .attr('fill', 'none');

    // Połączenia do bramek
    targetGates.forEach(gate => {
      const gateX = getGateLeftEdge(gate);
      svg.append('path')
        .attr('d', `M ${inputX} ${gate.y} L ${gateX} ${gate.y}`)
        .attr('stroke', color)
        .attr('stroke-width', 2)
        .attr('fill', 'none');
    });
  });
}

// Rysowanie wyjścia
function drawOutput(svg, lastGate) {
  if (!lastGate) return;

  const fromX = getGateRightEdge(lastGate);
  const fromY = lastGate.y;
  const toX = lastGate.x + 100;
  
  svg.append('path')
    .attr('d', `M ${fromX} ${fromY} L ${toX} ${fromY}`)
    .attr('stroke', '#3b82f6')
    .attr('stroke-width', 3)
    .attr('fill', 'none');

  svg.append('text')
    .attr('x', toX + 10)
    .attr('y', fromY + 5)
    .attr('text-anchor', 'start')
    .attr('fill', '#1f2937')
    .attr('font-size', 16)
    .attr('font-weight', 'bold')
    .text('Y');
}

export default function LogicGatesDisplay({ ast, expression }) {
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
      svg.attr('viewBox', '0 0 400 200').attr('width', '100%').attr('height', 200);
      svg.append('text')
        .attr('x', 200).attr('y', 100)
        .attr('text-anchor', 'middle')
        .attr('fill', '#6b7280')
        .attr('font-size', 16)
        .text('Brak bramek do wyświetlenia');
      return;
    }

    // Układanie bramek w poziomach
    const levels = new Map();
    const visited = new Set();
    
    function assignLevel(gateId, level = 0) {
      if (visited.has(gateId)) return;
      visited.add(gateId);
      
      const gate = gatesData.gates.find(g => g.id === gateId);
      if (!gate) return;
      
      if (!levels.has(level)) levels.set(level, []);
      levels.get(level).push(gate);
      
      gate.inputs.forEach(input => {
        if (input.startsWith('gate_')) {
          const inputGateId = parseInt(input.slice(5), 10);
          assignLevel(inputGateId, level + 1);
        }
      });
    }

    // Znajdź bramki wyjściowe (bez połączeń wychodzących)
    const outputGates = gatesData.gates.filter(gate => 
      !gatesData.connections.some(conn => conn.from === gate.output)
    );
    
    outputGates.forEach(gate => assignLevel(gate.id, 0));

    // Pozycjonowanie bramek
    const levelWidth = 200;
    const gateSpacing = 80;
    
    levels.forEach((gates, level) => {
      const x = 300 + (levels.size - 1 - level) * levelWidth;
      gates.forEach((gate, i) => {
        gate.x = x;
        gate.y = (i - (gates.length - 1) / 2) * gateSpacing;
      });
    });

    // Rozmiary SVG
    const minX = Math.min(...gatesData.gates.map(g => g.x)) - 150;
    const maxX = Math.max(...gatesData.gates.map(g => g.x)) + 150;
    const minY = Math.min(...gatesData.gates.map(g => g.y)) - 100;
    const maxY = Math.max(...gatesData.gates.map(g => g.y)) + 100;
    
    const width = maxX - minX;
    const height = maxY - minY + 100;
    
    svg.attr('viewBox', `${minX} ${minY - 50} ${width} ${height}`)
       .attr('width', '100%')
       .attr('height', height);

    // Rysowanie
    gatesData.connections.forEach(conn => 
      drawConnection(svg, conn.from, conn.to, gatesData.gates)
    );
    
    drawInputs(svg, gatesData.gates);
    
    gatesData.gates.forEach(gate => {
      const group = drawGate(svg, gate, gate.x, gate.y);
      
      // Tooltip
      group.on('mouseenter', (event) => {
        const symbol = Object.keys(SYMBOL_TO_GATE).find(s => SYMBOL_TO_GATE[s] === gate.type);
        const opDef = OP_DEFS[symbol];
        
        const content = opDef ? (
          <div>
            <div className="font-bold text-base mb-1">{opDef.name}</div>
            <div className="mb-2 text-xs">{opDef.desc}</div>
            <div className="text-xs">Bramka logiczna</div>
          </div>
        ) : (
          <div>
            <div className="font-bold text-base mb-1">{gate.type}</div>
            <div className="text-xs">Bramka logiczna</div>
          </div>
        );

        const rect = svgRef.current.getBoundingClientRect();
        setTooltip({
          visible: true,
          x: event.clientX - rect.left + 10,
          y: event.clientY - rect.top - 10,
          content
        });
      }).on('mouseleave', () => {
        setTooltip({ visible: false, x: 0, y: 0, content: null });
      }); 
    });

    const lastGate = outputGates[0];
    if (lastGate) drawOutput(svg, lastGate);

    // Tytuł
    svg.append('text')
      .attr('x', (minX + maxX) / 2)
      .attr('y', minY - 20)
      .attr('text-anchor', 'middle')
      .attr('fill', '#374151')
      .attr('font-size', 18)
      .attr('font-weight', 'bold')
      .text('Schemat bramek logicznych');

  }, [gatesData]);

  if (!ast) {
    return <div className="text-gray-500 text-center py-8">Brak danych do wyświetlenia bramek logicznych.</div>;
  }

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-full" style={{ maxWidth: 1200 }}>
        <svg
          ref={svgRef}
          className="w-full bg-gradient-to-br from-blue-50 to-white rounded-xl shadow-lg border border-gray-200"
        />
        {tooltip.visible && (
          <div
            className="absolute z-50 px-3 py-2 rounded-lg bg-blue-700 text-white text-xs font-semibold shadow-lg pointer-events-none"
            style={{ left: tooltip.x, top: tooltip.y }}
          >
            {tooltip.content}
          </div>
        )}
      </div>
      <div className="text-sm text-gray-600 mt-3">
        Najedź na bramkę, aby zobaczyć definicję operatora
      </div>
    </div>
  );
}