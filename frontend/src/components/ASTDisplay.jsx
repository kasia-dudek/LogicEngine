import React, { useRef, useEffect, useState } from 'react';
import * as d3 from 'd3';

export const OP_DEFS = {
  '∧': {
    name: 'Koniunkcja (AND)',
    desc: 'Prawda tylko gdy oba argumenty są prawdziwe.',
    table: [
      ['A', 'B', 'A ∧ B'],
      [0, 0, 0],
      [0, 1, 0],
      [1, 0, 0],
      [1, 1, 1],
    ]
  },
  '∨': {
    name: 'Alternatywa (OR)',
    desc: 'Prawda gdy przynajmniej jeden argument jest prawdziwy.',
    table: [
      ['A', 'B', 'A ∨ B'],
      [0, 0, 0],
      [0, 1, 1],
      [1, 0, 1],
      [1, 1, 1],
    ]
  },
  '→': {
    name: 'Implikacja (A → B)',
    desc: 'Fałsz tylko gdy A=1 i B=0.',
    table: [
      ['A', 'B', 'A → B'],
      [0, 0, 1],
      [0, 1, 1],
      [1, 0, 0],
      [1, 1, 1],
    ]
  },
  '↔': {
    name: 'Równoważność (A ↔ B)',
    desc: 'Prawda gdy oba argumenty mają tę samą wartość.',
    table: [
      ['A', 'B', 'A ↔ B'],
      [0, 0, 1],
      [0, 1, 0],
      [1, 0, 0],
      [1, 1, 1],
    ]
  },
  '¬': {
    name: 'Negacja (NOT)',
    desc: 'Zwraca przeciwną wartość logiczną.',
    table: [
      ['A', '¬A'],
      [0, 1],
      [1, 0],
    ]
  },
  '⊕': {
    name: 'Alternatywa wykluczająca (XOR)',
    desc: 'Prawda, gdy dokładnie jeden argument jest prawdziwy.',
    table: [
      ['A', 'B', 'A ⊕ B'],
      [0, 0, 0],
      [0, 1, 1],
      [1, 0, 1],
      [1, 1, 0],
    ]
  },
  '↑': {
    name: 'NAND (negacja koniunkcji)',
    desc: 'Prawda, gdy nie oba argumenty są prawdziwe.',
    table: [
      ['A', 'B', 'A ↑ B'],
      [0, 0, 1],
      [0, 1, 1],
      [1, 0, 1],
      [1, 1, 0],
    ]
  },
  '↓': {
    name: 'NOR (negacja alternatywy)',
    desc: 'Prawda, gdy oba argumenty są fałszywe.',
    table: [
      ['A', 'B', 'A ↓ B'],
      [0, 0, 1],
      [0, 1, 0],
      [1, 0, 0],
      [1, 1, 0],
    ]
  },
  '≡': {
    name: 'Równoważność (XNOR)',
    desc: 'Prawda, gdy oba argumenty mają tę samą wartość.',
    table: [
      ['A', 'B', 'A ≡ B'],
      [0, 0, 1],
      [0, 1, 0],
      [1, 0, 0],
      [1, 1, 1],
    ]
  },
};

function getSubtreeExpr(node) {
  if (!node) return '?';
  if (typeof node === 'string') return node;
  if (node.node === '¬') return `¬(${getSubtreeExpr(node.child)})`;
  if (['∧', '∨', '→', '↔'].includes(node.node))
    return `(${getSubtreeExpr(node.left)} ${node.node} ${getSubtreeExpr(node.right)})`;
  return '?';
}

function getTreeDepth(node) {
  if (!node || typeof node === 'string') return 1;
  if (node.node === '¬') return 1 + getTreeDepth(node.child);
  if (['∧', '∨', '→', '↔'].includes(node.node))
    return 1 + Math.max(getTreeDepth(node.left), getTreeDepth(node.right));
  return 1;
}

function getTreeWidth(node) {
  if (!node || typeof node === 'string') return 1;
  if (node.node === '¬') return getTreeWidth(node.child);
  if (['∧', '∨', '→', '↔'].includes(node.node))
    return getTreeWidth(node.left) + getTreeWidth(node.right);
  return 1;
}

function getLeafCount(node) {
  if (!node) return 0;
  if (typeof node === 'string') return 1;
  if (node.node === '¬') return getLeafCount(node.child);
  if (['∧', '∨', '→', '↔'].includes(node.node))
    return getLeafCount(node.left) + getLeafCount(node.right);
  return 1;
}

function ASTDisplay({ ast }) {
  const svgRef = useRef(null);
  const [tooltip, setTooltip] = useState({ visible: false, x: 0, y: 0, content: null });
  const [svgHeight, setSvgHeight] = useState(280);
  const [svgWidth, setSvgWidth] = useState(440);

  useEffect(() => {
    if (!ast || !svgRef.current) return;
    d3.select(svgRef.current).selectAll('*').remove();
    function toHierarchy(node) {
      if (!node) return null;
      if (typeof node === 'string') return { name: node, type: 'var', raw: node };
      if (node.node) {
        if (node.left && node.right) {
          return {
            name: node.node,
            type: 'op',
            raw: node,
            children: [toHierarchy(node.left), toHierarchy(node.right)].filter(Boolean)
          };
        } else if (node.child) {
          return {
            name: node.node,
            type: 'op',
            raw: node,
            children: [toHierarchy(node.child)].filter(Boolean)
          };
        }
      }
      return { name: '?', type: 'unknown', raw: node };
    }
    const root = d3.hierarchy(toHierarchy(ast));
    const depth = root.height + 1;
    const leafs = getLeafCount(ast);
    const margin = 60;
    const nodeWidth = 140;
    const svgW = Math.max(440, leafs * nodeWidth + margin * 2);
    const svgH = 120 + 120 * depth;
    setSvgHeight(svgH);
    setSvgWidth(svgW);
    const treeLayout = d3.tree().size([svgW - margin * 2, svgH - 100]);
    treeLayout(root);
    const svg = d3.select(svgRef.current)
      .attr('viewBox', `0 0 ${svgW} ${svgH}`)
      .attr('width', '100%')
      .attr('height', svgH);
    // Krawędzie
    svg.selectAll('path.link')
      .data(root.links())
      .enter()
      .append('path')
      .attr('class', 'link')
      .attr('d', d3.linkVertical()
        .x(d => d.x + margin)
        .y(d => d.y + margin))
      .attr('stroke', 'url(#edge-gradient)')
      .attr('stroke-width', 3)
      .attr('fill', 'none')
      .attr('opacity', 0.7);
    // Gradient dla krawędzi
    svg.append('defs').append('linearGradient')
      .attr('id', 'edge-gradient')
      .attr('x1', '0%').attr('y1', '0%').attr('x2', '100%').attr('y2', '0%')
      .selectAll('stop')
      .data([
        { offset: '0%', color: '#60a5fa' },
        { offset: '100%', color: '#818cf8' }
      ])
      .enter()
      .append('stop')
      .attr('offset', d => d.offset)
      .attr('stop-color', d => d.color);
    // Węzły
    const node = svg.selectAll('g.node')
      .data(root.descendants())
      .enter()
      .append('g')
      .attr('class', 'node')
      .attr('transform', d => `translate(${d.x + margin},${d.y + margin})`)
      .style('cursor', 'pointer')
      .on('mouseenter', function (event, d) {
        d3.select(this).select('circle').attr('stroke', '#f59e42').attr('stroke-width', 5);
        // Tooltip content
        let content = null;
        if (d.data.type === 'op' && OP_DEFS[d.data.name]) {
          const def = OP_DEFS[d.data.name];
          content = (
            <div>
              <div className="font-bold text-base mb-1">{def.name}</div>
              <div className="mb-2 text-xs">{def.desc}</div>
              <div className="mb-2 font-mono text-xs">Poddrzewo: {getSubtreeExpr(d.data.raw)}</div>
              <table className="border border-blue-200 rounded mb-1 text-xs">
                <tbody>
                  {def.table.map((row, i) => (
                    <tr key={i}>
                      {row.map((cell, j) => (
                        <td key={j} className={`px-2 py-1 border ${i === 0 ? 'bg-blue-100 font-semibold' : ''}`}>{cell}</td>
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
              <div className="mb-2 text-xs">Zmienna logiczna, przyjmuje wartość 0 lub 1.</div>
              <div className="mb-2 font-mono text-xs">{d.data.name}</div>
            </div>
          );
        } else {
          content = <div className="font-mono text-xs">Poddrzewo: {getSubtreeExpr(d.data.raw)}</div>;
        }
        const svg = svgRef.current;
        const pt = svg.createSVGPoint();
        pt.x = d.x + margin;
        pt.y = d.y + margin;
        const screenCTM = svg.getScreenCTM();
        const transformed = pt.matrixTransform(screenCTM);
        const containerRect = svg.parentNode.getBoundingClientRect();
        const left = transformed.x - containerRect.left;
        const top = transformed.y - containerRect.top;
        setTooltip({ visible: true, x: left + 40, y: top, content });
      })
      .on('mouseleave', function () {
        d3.select(this).select('circle').attr('stroke', d => d.data.type === 'op' ? '#1e40af' : '#059669').attr('stroke-width', 3);
        setTooltip({ visible: false, x: 0, y: 0, content: null });
      });
    node.append('circle')
      .attr('r', 24)
      .attr('fill', d => d.data.type === 'op' ? 'url(#node-gradient)' : '#bbf7d0')
      .attr('stroke', d => d.data.type === 'op' ? '#1e40af' : '#059669')
      .attr('stroke-width', 3)
      .attr('filter', 'url(#shadow)');
    svg.append('defs').append('radialGradient')
      .attr('id', 'node-gradient')
      .selectAll('stop')
      .data([
        { offset: '0%', color: '#a5b4fc' },
        { offset: '100%', color: '#3b82f6' }
      ])
      .enter()
      .append('stop')
      .attr('offset', d => d.offset)
      .attr('stop-color', d => d.color);
    svg.append('defs').append('filter')
      .attr('id', 'shadow')
      .html('<feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="#000" flood-opacity="0.15" />');
    node.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '0.35em')
      .attr('fill', d => d.data.type === 'op' ? 'white' : '#059669')
      .attr('font-size', 22)
      .attr('font-weight', 700)
      .text(d => d.data.name);
  }, [ast, svgHeight]);

  if (!ast) {
    return <div className="text-gray-500">Brak danych do wyświetlenia AST.</div>;
  }
  return (
    <div className="flex flex-col items-center">
      <div className="relative w-full" style={{ maxWidth: svgWidth }}>
        <svg ref={svgRef} className="w-full bg-gradient-to-br from-blue-50 to-white rounded-2xl shadow-xl border border-blue-100" />
        {tooltip.visible && (
          <div
            className="absolute z-50 px-3 py-2 rounded-xl bg-blue-700 text-white text-xs font-semibold shadow-lg pointer-events-none animate-fade-in"
            style={{ left: tooltip.x, top: tooltip.y, minWidth: 120 }}
          >
            {tooltip.content}
          </div>
        )}
      </div>
      <div className="text-xs text-gray-500 mt-2">Najedź na węzeł, aby zobaczyć definicję i działanie operatora lub poddrzewa.</div>
    </div>
  );
}

export default ASTDisplay; 