import React from 'react';
import { render, screen } from '@testing-library/react';
import QMSteps from '../QMSteps';

describe('QMSteps', () => {
  it('renders steps in order', () => {
    const steps = [
      { step: 'Krok 1', data: { a: 1 } },
      { step: 'Krok 2', data: { b: 2 } },
    ];
    render(<QMSteps steps={steps} />);
    expect(screen.getByText('Krok 1')).toBeInTheDocument();
    expect(screen.getByText('Krok 2')).toBeInTheDocument();
    expect(screen.getByText(/"a": 1/)).toBeInTheDocument();
    expect(screen.getByText(/"b": 2/)).toBeInTheDocument();
  });

  it('shows message when no steps', () => {
    render(<QMSteps steps={[]} />);
    expect(screen.getByText(/Brak danych/)).toBeInTheDocument();
  });
}); 