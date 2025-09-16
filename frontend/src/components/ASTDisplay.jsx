// frontend/src/components/ASTDisplay.jsx
import React, { useRef, useEffect, useState, useMemo } from 'react';
import * as d3 from 'd3';

/** Opisy operatorów (tooltip) */
export const OP_DEFS = {
  '∧': { name: 'Koniunkcja (AND)', desc: 'Prawda tylko gdy oba argumenty są prawdziwe.',
    table: [['A','B','A ∧ B'], [0,0,0],[0,1,0],[1,0,0],[1,1,1]] },
  '∨': { name: 'Alternatywa (OR)', desc: 'Prawda gdy przynajmniej jeden argument jest prawdziwy.',
    table: [['A','B','A ∨ B'], [0,0,0],[0,1,1],[1,0,1],[1,1,1]] },
  '→': { name: 'Implikacja (A → B)', desc: 'Fałsz tylko gdy A=1 i B=0.',
    table: [['A','B','A → B'], [0,0,1],[0,1,1],[1,0,0],[1,1,1]] },
  '↔': { name: 'Równoważność (A ↔ B)', desc: 'Prawda gdy oba argumenty mają tę samą wartość.',
    table: [['A','B','A ↔ B'], [0,0,1],[0,1,0],[1,0,0],[1,1,1]] },
  '≡': { name: 'Równoważność (XNOR)', desc: 'Prawda, gdy oba argumenty mają tę samą wartość.',
    table: [['A','B','A ≡ B'], [0,0,1],[0,1,0],[1,0,0],[1,1,1]] },
  '⊕': { name: 'XOR', desc: 'Prawda, gdy dokładnie jeden argument jest prawdziwy.',
    table: [['A','B','A ⊕ B'], [0,0,0],[0,1,1],[1,0,1],[1,1,0]] },
  '↑': { name: 'NAND', desc: 'Negacja koniunkcji.',
    table: [['A','B','A ↑ B'], [0,0,1],[0,1,1],[1,0,1],[1,1,0]] },
  '↓': { name: 'NOR', desc: 'Negacja alternatywy.',
    table: [['A','B','A ↓ B'], [0,0,1],[0,1,0],[1,0,0],[1,1,0]] },
  '¬': { name: 'Negacja (NOT)', desc: 'Zwraca przeciwną wartość logiczną.',
    table: [['A','¬A'], [0,1],[1,0]] },
};

/* ====== Obsługa dwóch formatów AST: legacy (node/left/right/child) i normalized (op/args/child) ====== */
const OP_MAP = new Map([
  ['NOT', '¬'],
  ['AND', '∧'],
  ['OR', '∨'],
  ['IMPLIES', '→'],
  ['IFF', '↔'],
  ['XOR', '⊕'],
  ['NAND', '↑'],
  ['NOR', '↓'],
  ['XNOR', '≡'],
]);

function opSymbol(node) {
  if (!node || typeof node !== 'object') return undefined;
  if (node.node) return node.node;
  if (node.op) return OP_MAP.get(node.op) || node.op;
  return undefined;
}

/* ----- Tekst poddrzewa (do tooltipu i highlightu) ----- */
function subtreeText(n) {
  if (!n) return '?';
  if (typeof n === 'string') return n;
  
  // Handle legacy AST format: {node: '¬', child: ...} or {node: '∧', left: ..., right: ...}
  if (n.node) {
    const op = n.node;
    if (op === '¬') {
      const child = subtreeText(n.child);
      return `¬(${child})`;
    }
    if (op === '∧') {
      const left = subtreeText(n.left);
      const right = subtreeText(n.right);
      return `(${left} ∧ ${right})`;
    }
    if (op === '∨') {
      const left = subtreeText(n.left);
      const right = subtreeText(n.right);
      return `(${left} ∨ ${right})`;
    }
    // Other binary operators
    const left = subtreeText(n.left);
    const right = subtreeText(n.right);
    return `(${left} ${op} ${right})`;
  }
  
  // Handle normalized AST format: {op: 'NOT', child: ...} or {op: 'AND', args: [...]}
  if (n.op) {
    const op = n.op;
    if (op === 'NOT') {
      const child = subtreeText(n.child);
      return `¬(${child})`;
    }
    if (op === 'AND') {
      const args = (n.args || []).map(subtreeText);
      return `(${args.join(' ∧ ')})`;
    }
    if (op === 'OR') {
      const args = (n.args || []).map(subtreeText);
      return `(${args.join(' ∨ ')})`;
    }
    if (op === 'VAR') {
      return n.name || '?';
    }
    if (op === 'CONST') {
      return n.value?.toString() || '?';
    }
  }
  
  return '?';
}

/* ----- Liczba liści (do wyznaczenia szerokości) ----- */
function leafCount(n) {
  if (!n) return 0;
  if (typeof n === 'string') return 1;
  
  // Handle legacy AST format: {node: '¬', child: ...} or {node: '∧', left: ..., right: ...}
  if (n.node) {
    const op = n.node;
    if (op === '¬') {
      return leafCount(n.child);
    }
    if (op === '∧' || op === '∨') {
      const left = leafCount(n.left);
      const right = leafCount(n.right);
      return left + right;
    }
    // Other binary operators
    const left = leafCount(n.left);
    const right = leafCount(n.right);
    return left + right;
  }
  
  // Handle normalized AST format: {op: 'NOT', child: ...} or {op: 'AND', args: [...]}
  if (n.op) {
    const op = n.op;
    if (op === 'NOT') {
      return leafCount(n.child);
    }
    if (op === 'AND' || op === 'OR') {
      const args = n.args || [];
      return args.reduce((sum, arg) => sum + leafCount(arg), 0);
    }
    if (op === 'VAR' || op === 'CONST') {
      return 1;
    }
  }
  
  return 1;
}

/* ----- AST -> hierarchia d3 ----- */
function toHierarchy(node) {
  if (!node) return null;
  if (typeof node === 'string') return { name: node, type: 'var', raw: node };
  
  // Handle legacy AST format: {node: '¬', child: ...} or {node: '∧', left: ..., right: ...}
  if (node.node) {
    const op = node.node;
    if (op === '¬') {
      const child = toHierarchy(node.child);
      return { name: '¬', type: 'op', raw: node, children: child ? [child] : [] };
    }
    if (op === '∧') {
      const left = toHierarchy(node.left);
      const right = toHierarchy(node.right);
      return { name: '∧', type: 'op', raw: node, children: [left, right].filter(Boolean) };
    }
    if (op === '∨') {
      const left = toHierarchy(node.left);
      const right = toHierarchy(node.right);
      return { name: '∨', type: 'op', raw: node, children: [left, right].filter(Boolean) };
    }
    // Other binary operators
    const left = toHierarchy(node.left);
    const right = toHierarchy(node.right);
    return { name: op, type: 'op', raw: node, children: [left, right].filter(Boolean) };
  }
  
  // Handle normalized AST format: {op: 'NOT', child: ...} or {op: 'AND', args: [...]}
  if (node.op) {
    const op = node.op;
    if (op === 'NOT') {
      const child = toHierarchy(node.child);
      return { name: '¬', type: 'op', raw: node, children: child ? [child] : [] };
    }
    if (op === 'AND') {
      const args = (node.args || []).map(toHierarchy).filter(Boolean);
      return { name: '∧', type: 'op', raw: node, children: args };
    }
    if (op === 'OR') {
      const args = (node.args || []).map(toHierarchy).filter(Boolean);
      return { name: '∨', type: 'op', raw: node, children: args };
    }
    if (op === 'VAR') {
      return { name: node.name || '?', type: 'var', raw: node, children: [] };
    }
    if (op === 'CONST') {
      return { name: node.value?.toString() || '?', type: 'const', raw: node, children: [] };
    }
  }
  
  return { name: '?', type: 'unknown', raw: node };
}

/* =================== KOMPONENT =================== */
export default function ASTDisplay({ ast, highlightExpr }) {
  const svgRef = useRef(null);
  const [tooltip, setTooltip] = useState({ visible: false, x: 0, y: 0, content: null });

  /* 1) Precompute hierarchię i wymiary TYLKO gdy zmienia się AST */
  const memo = useMemo(() => {
    if (!ast) return null;
    const rootH = toHierarchy(ast);
    const root = d3.hierarchy(rootH, d => d.children || []);
    const depth = root.height + 1;
    const leaves = Math.max(1, leafCount(ast));
    const margin = 60;
    const nodeW = 140;
    const svgW = Math.max(440, leaves * nodeW + margin * 2);
    const svgH = 120 + 120 * depth;
    const layout = d3.tree().size([svgW - margin * 2, svgH - 100]);
    layout(root);
    return { root, svgW, svgH, margin };
  }, [ast]);

  /* 2) Rysowanie statyczne – tylko kiedy zmieni się AST */
  useEffect(() => {
    if (!memo || !svgRef.current) return;
    const { root, svgW, svgH, margin } = memo;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    svg.attr('viewBox', `0 0 ${svgW} ${svgH}`).attr('width', '100%').attr('height', svgH);

    // defs (gradienty, cień)
    const defs = svg.append('defs');
    const edgeGrad = defs.append('linearGradient').attr('id', 'edge-grad')
      .attr('x1','0%').attr('y1','0%').attr('x2','100%').attr('y2','0%');
    edgeGrad.selectAll('stop').data([
      { offset: '0%', color: '#60a5fa' },
      { offset: '100%', color: '#818cf8' },
    ]).enter().append('stop').attr('offset', d => d.offset).attr('stop-color', d => d.color);

    const nodeGrad = defs.append('radialGradient').attr('id','node-grad');
    nodeGrad.selectAll('stop').data([
      { offset: '0%', color: '#a5b4fc' },
      { offset: '100%', color: '#3b82f6' },
    ]).enter().append('stop').attr('offset', d => d.offset).attr('stop-color', d => d.color);

    defs.append('filter').attr('id','shadow')
      .html('<feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="#000" flood-opacity="0.15" />');

    // krawędzie
    svg.append('g').attr('class', 'links')
      .selectAll('line')
      .data(root.links())
      .enter().append('line')
      .attr('x1', d => d.source.x + margin)
      .attr('y1', d => d.source.y + margin)
      .attr('x2', d => d.target.x + margin)
      .attr('y2', d => d.target.y + margin)
      .attr('stroke','#3b82f6')
      .attr('stroke-width',3)
      .attr('fill','none');

    // węzły
    const gNodes = svg.append('g').attr('class', 'nodes')
      .selectAll('g.node')
      .data(root.descendants())
      .enter().append('g')
      .attr('class','node')
      .attr('transform', d => `translate(${d.x + margin},${d.y + margin})`)
      .style('cursor','pointer');

    gNodes.append('circle')
      .attr('r',24)
      .attr('fill', d => d.data.type === 'op' ? 'url(#node-grad)' : '#bbf7d0')
      .attr('stroke', d => d.data.type === 'op' ? '#1e40af' : '#059669')
      .attr('stroke-width',3)
      .attr('filter','url(#shadow)');

    gNodes.append('text')
      .attr('text-anchor','middle')
      .attr('dy','0.35em')
      .attr('fill', d => d.data.type === 'op' ? 'white' : '#059669')
      .attr('font-size',22)
      .attr('font-weight',700)
      .text(d => d.data.name);

    // interakcje (tooltips)
    gNodes
      .on('mouseenter', function (event, d) {
        d3.select(this).select('circle').attr('stroke','#f59e42').attr('stroke-width',5);
        let content;
        const sym = d.data.name;
        if (d.data.type === 'op' && OP_DEFS[sym]) {
          const def = OP_DEFS[sym];
          content = (
            <div>
              <div className="font-bold text-base mb-1">{def.name}</div>
              <div className="mb-2 text-xs">{def.desc}</div>
              <div className="mb-2 font-mono text-xs">Poddrzewo: {subtreeText(d.data.raw)}</div>
              <table className="border border-blue-200 rounded mb-1 text-xs">
                <tbody>
                  {def.table.map((r, i) => (
                    <tr key={i}>
                      {r.map((c, j) => (
                        <td key={j} className={`px-2 py-1 border ${i === 0 ? 'bg-blue-100 font-semibold' : ''}`}>{c}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          );
        } else if (d.data.type === 'var') {
          content = (
            <div>
              <div className="font-bold text-base mb-1">Zmienna: {d.data.name}</div>
              <div className="mb-2 text-xs">Zmienna logiczna (0/1).</div>
            </div>
          );
        } else {
          content = <div className="font-mono text-xs">Poddrzewo: {subtreeText(d.data.raw)}</div>;
        }
        const svgEl = svgRef.current;
        const pt = svgEl.createSVGPoint(); pt.x = d.x + margin; pt.y = d.y + margin;
        const ctm = svgEl.getScreenCTM();
        const { x, y } = pt.matrixTransform(ctm);
        const rect = svgEl.parentNode.getBoundingClientRect();
        setTooltip({ visible: true, x: x - rect.left + 40, y: y - rect.top, content });
      })
      .on('mouseleave', function () {
        d3.select(this).select('circle')
          .attr('stroke', d => d.data.type === 'op' ? '#1e40af' : '#059669')
          .attr('stroke-width',3);
        setTooltip({ visible: false, x: 0, y: 0, content: null });
      });
  }, [memo]);

  /* 3) Szybkie podświetlenie – bez przerysowywania całego SVG */
  useEffect(() => {
    if (!svgRef.current) return;
    const svg = d3.select(svgRef.current);
    const circles = svg.selectAll('g.nodes > g.node > circle');
    circles.attr('stroke-width',3).attr('stroke', function() {
      const d = d3.select(this.parentNode).datum();
      return d.data.type === 'op' ? '#1e40af' : '#059669';
    });
    if (!highlightExpr) return;
    circles.each(function () {
      const d = d3.select(this.parentNode).datum();
      if (subtreeText(d.data.raw) === highlightExpr) {
        d3.select(this).attr('stroke','#10b981').attr('stroke-width',6);
      }
    });
  }, [highlightExpr]);

  if (!ast) return <div className="text-gray-500">Brak danych do wyświetlenia AST.</div>;

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-full" style={{ maxWidth: 1200 }}>
        <svg
          ref={svgRef}
          className="w-full bg-gradient-to-br from-blue-50 to-white rounded-2xl shadow-xl border border-blue-100"
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
      <div className="text-xs text-gray-500 mt-2">
        Najedź na węzeł, aby zobaczyć definicję operatora i zapis poddrzewa.
      </div>
    </div>
  );
}
