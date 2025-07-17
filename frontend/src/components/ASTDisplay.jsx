import React, { useRef, useEffect } from 'react';
import * as d3 from 'd3';

function ASTDisplay({ ast }) {
  const svgRef = useRef(null);

  useEffect(() => {
    if (!ast || !svgRef.current) return;
    // Czyść SVG
    d3.select(svgRef.current).selectAll('*').remove();
    // Przekształć AST do formatu d3.hierarchy
    function toHierarchy(node) {
      if (!node) return null;
      if (typeof node === 'string') return { name: node };
      if (node.node) {
        if (node.left && node.right) {
          return {
            name: node.node,
            children: [toHierarchy(node.left), toHierarchy(node.right)].filter(Boolean)
          };
        } else if (node.child) {
          return {
            name: node.node,
            children: [toHierarchy(node.child)].filter(Boolean)
          };
        }
      }
      return { name: '?' };
    }
    const root = d3.hierarchy(toHierarchy(ast));
    const treeLayout = d3.tree().size([400, 200]);
    treeLayout(root);
    const svg = d3.select(svgRef.current)
      .attr('viewBox', '0 0 420 220')
      .attr('width', '100%')
      .attr('height', 220);
    // Krawędzie
    svg.selectAll('path.link')
      .data(root.links())
      .enter()
      .append('path')
      .attr('class', 'link')
      .attr('d', d3.linkVertical()
        .x(d => d.x + 10)
        .y(d => d.y + 20))
      .attr('stroke', '#6b7280')
      .attr('stroke-width', 2)
      .attr('fill', 'none');
    // Węzły
    const node = svg.selectAll('g.node')
      .data(root.descendants())
      .enter()
      .append('g')
      .attr('class', 'node')
      .attr('transform', d => `translate(${d.x + 10},${d.y + 20})`);
    node.append('circle')
      .attr('r', 18)
      .attr('fill', '#3b82f6')
      .attr('stroke', '#1e40af')
      .attr('stroke-width', 2);
    node.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '0.35em')
      .attr('fill', 'white')
      .attr('font-size', 16)
      .text(d => d.data.name);
  }, [ast]);

  if (!ast) {
    return <div className="text-gray-500">Brak danych do wyświetlenia AST.</div>;
  }
  return (
    <div className="flex flex-col items-center">
      <svg ref={svgRef} className="w-full max-w-xl bg-white rounded shadow-md" />
      <div className="text-xs text-gray-500 mt-2">Kliknij węzeł, aby zobaczyć szczegóły (wkrótce).</div>
    </div>
  );
}

export default ASTDisplay; 