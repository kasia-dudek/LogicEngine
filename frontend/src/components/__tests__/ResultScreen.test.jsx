import 'jest';
jest.mock('jspdf', () => {
  return function () {
    return {
      setFont: jest.fn(),
      setFontSize: jest.fn(),
      text: jest.fn(),
      save: jest.fn(),
    };
  };
});

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import ResultScreen from '../ResultScreen';

jest.mock('d3', () => ({
  select: () => ({
    selectAll: () => ({
      remove: () => {},
      data: () => ({
        enter: () => ({
          append: () => ({
            attr: function () { return this; },
            text: function () { return this; }
          })
        })
      })
    }),
    attr: function () { return this; },
    data: function () { return { enter: () => ({ append: () => ({ attr: function () { return this; }, text: function () { return this; } }) }) }; }
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

jest.mock('../../__mocks__/api', () => ({
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
    await act(async () => {
      render(<ResultScreen input="(A ∧ B) ∨ ¬C" onBack={jest.fn()} />);
    });
    await screen.findByText('Tabela prawdy');
    expect(screen.getByText('Tabela prawdy')).toBeInTheDocument();
    fireEvent.click(screen.getByText('Quine-McCluskey'));
    expect(screen.getByText('QM step 1')).toBeInTheDocument();
    fireEvent.click(screen.getByText('K-Map'));
    expect(screen.getByText('Uproszczone:')).toBeInTheDocument();
    fireEvent.click(screen.getByText('AST'));
    expect(screen.getByText(/Brak danych|AST/)).toBeInTheDocument();
  });

  it('obsługuje błąd API', async () => {
    jest.spyOn(require('../../__mocks__/api'), 'analyze').mockImplementationOnce(async () => { throw new Error('API error'); });
    await act(async () => {
      render(<ResultScreen input="(A ∧ B) ∨ ¬C" onBack={jest.fn()} />);
    });
    await screen.findByText(/API error/);
  });

  it('obsługuje kliknięcie przycisku powrotu', async () => {
    const onBack = jest.fn();
    await act(async () => {
      render(<ResultScreen input="(A ∧ B) ∨ ¬C" onBack={onBack} />);
    });
    await screen.findByText('Tabela prawdy');
    fireEvent.click(screen.getByText(/Wróć/));
    expect(onBack).toHaveBeenCalled();
  });
}); 