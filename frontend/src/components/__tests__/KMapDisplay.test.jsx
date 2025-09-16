import React from 'react';
import { render, screen } from '@testing-library/react';
import KMapDisplay from '../KMapDisplay';
import * as d3 from 'd3';

jest.mock('d3', () => ({}));

describe('KMapDisplay', () => {
  it('renders K-Map table and highlights groups', () => {
    const kmap = [ [0, 1], [0, 1] ];
    const groups = [ { cells: [[0, 1], [1, 1]], expr: 'B' } ];
    render(<KMapDisplay
      kmap={data.kmap_simplification.kmap}
      groups={data.kmap_simplification.groups}
      all_groups={data.kmap_simplification.all_groups}
      result={data.kmap_simplification.result}
      vars={data.kmap_simplification.vars}          // <—
      minterms={data.kmap_simplification.minterms}  // <—
    />
    );
    expect(screen.getAllByText('B').length).toBeGreaterThan(0);
    // Sprawdź, czy wartości 1 są w tabeli
    expect(screen.getAllByText('1').length).toBeGreaterThan(0);
    // Sprawdź, czy podpis uproszczonego wyrażenia jest widoczny
    expect(screen.getByText(/Uproszczone/)).toBeInTheDocument();
    // Sprawdź, czy grupy są podpisane
    expect(screen.getAllByText('B').length).toBeGreaterThan(0);
  });

  it('shows message when no kmap', () => {
    render(<KMapDisplay
      kmap={data.kmap_simplification.kmap}
      groups={data.kmap_simplification.groups}
      all_groups={data.kmap_simplification.all_groups}
      result={data.kmap_simplification.result}
      vars={data.kmap_simplification.vars}          // <—
      minterms={data.kmap_simplification.minterms}  // <—
    />
    );
    expect(screen.getByText(/Brak danych/)).toBeInTheDocument();
  });
}); 