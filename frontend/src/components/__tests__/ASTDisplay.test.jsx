import React from 'react';
import { render, screen } from '@testing-library/react';
import ASTDisplay from '../ASTDisplay';

describe('ASTDisplay', () => {
  it('renders AST tree for simple expression', () => {
    const ast = {
      node: '∨',
      left: { node: '∧', left: 'A', right: 'B' },
      right: { node: '¬', child: 'C' }
    };
    render(<ASTDisplay ast={ast} />);
    // Sprawdź, czy SVG jest renderowane
    expect(screen.getByRole('img', { hidden: true })).toBeInTheDocument();
    // Sprawdź, czy teksty węzłów są obecne
    expect(screen.getByText('∨')).toBeInTheDocument();
    expect(screen.getByText('∧')).toBeInTheDocument();
    expect(screen.getByText('A')).toBeInTheDocument();
    expect(screen.getByText('B')).toBeInTheDocument();
    expect(screen.getByText('¬')).toBeInTheDocument();
    expect(screen.getByText('C')).toBeInTheDocument();
  });

  it('shows message when no AST', () => {
    render(<ASTDisplay ast={null} />);
    expect(screen.getByText(/Brak danych/)).toBeInTheDocument();
  });
}); 