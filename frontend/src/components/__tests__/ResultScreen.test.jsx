import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ResultScreen from '../ResultScreen';

jest.mock('../__mocks__/api', () => ({
  analyze: jest.fn(async (input) => ({
    expression: input,
    truth_table: [
      { A: 0, B: 0, C: 0, result: 1 },
      { A: 1, B: 1, C: 0, result: 1 },
    ],
    qm: { result: 'A ∧ B ∨ ¬C', steps: [{ description: 'QM step 1' }] },
    kmap: { result: 'A ∧ B ∨ ¬C', kmap: [[0,1],[1,0]], groups: [] },
    ast: { node: '∨', left: {}, right: {} },
  }))
}));

describe('ResultScreen', () => {
  it('renderuje dane i przełącza zakładki', async () => {
    render(<ResultScreen input="(A ∧ B) ∨ ¬C" onBack={jest.fn()} />);
    await waitFor(() => expect(screen.getByText('Wynik analizy')).toBeInTheDocument());
    expect(screen.getByText('Tabela prawdy')).toBeInTheDocument();
    fireEvent.click(screen.getByText('Quine-McCluskey'));
    expect(screen.getByText('QM step 1')).toBeInTheDocument();
    fireEvent.click(screen.getByText('K-Map'));
    expect(screen.getByText('Uproszczone:')).toBeInTheDocument();
    fireEvent.click(screen.getByText('AST'));
    expect(screen.getByText(/Brak danych|AST/)).toBeInTheDocument();
  });

  it('obsługuje błąd API', async () => {
    jest.spyOn(require('../__mocks__/api'), 'analyze').mockImplementationOnce(async () => { throw new Error('API error'); });
    render(<ResultScreen input="(A ∧ B) ∨ ¬C" onBack={jest.fn()} />);
    await waitFor(() => expect(screen.getByText(/API error/)).toBeInTheDocument());
  });

  it('obsługuje kliknięcie przycisku powrotu', async () => {
    const onBack = jest.fn();
    render(<ResultScreen input="(A ∧ B) ∨ ¬C" onBack={onBack} />);
    await waitFor(() => expect(screen.getByText('Wynik analizy')).toBeInTheDocument());
    fireEvent.click(screen.getByText(/Wróć/));
    expect(onBack).toHaveBeenCalled();
  });
}); 