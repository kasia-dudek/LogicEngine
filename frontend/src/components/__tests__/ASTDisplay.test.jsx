import React from 'react';
import { render, screen } from '@testing-library/react';
import ASTDisplay from '../ASTDisplay';
import * as d3 from 'd3';

jest.mock('d3', () => ({
  select: () => ({
    selectAll: () => ({
      remove: () => {},
      data: () => ({
        enter: () => ({
          append: () => {
            const obj = {
              attr: function () { return obj; },
              text: function () { return obj; },
              append: function () { return obj; }
            };
            return obj;
          }
        })
      })
    }),
    attr: function () { return this; },
    data: function () { return { enter: () => ({ append: () => {
      const obj = {
        attr: function () { return obj; },
        text: function () { return obj; },
        append: function () { return obj; }
      };
      return obj;
    } }) }; }
  }),
  hierarchy: () => ({
    links: () => [],
    descendants: () => [],
  }),
  tree: () => ({
    size: function () { return () => {}; }
  }),
  linkVertical: () => {
    const obj = {
      x: function () { return obj; },
      y: function () { return obj; }
    };
    return obj;
  },
}));

describe('ASTDisplay', () => {
  it('renders AST tree for simple expression', () => {
    const ast = {
      node: '∨',
      left: { node: '∧', left: 'A', right: 'B' },
      right: { node: '¬', child: 'C' }
    };
    render(<ASTDisplay ast={ast} />);
    // Sprawdź, czy SVG jest renderowane
    expect(document.querySelector('svg')).not.toBeNull();
  });

  it('shows message when no AST', () => {
    render(<ASTDisplay ast={null} />);
    expect(screen.getByText(/Brak danych/)).toBeInTheDocument();
  });
}); 