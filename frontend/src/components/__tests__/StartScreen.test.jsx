import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import App from '../../App';
import * as d3 from 'd3';

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

beforeEach(() => {
  localStorage.setItem('logicengine_history', JSON.stringify([
    { id: '2025-07-17T13:20:00', expression: '(A ∧ B) ∨ ¬C', result: { foo: 1 } }
  ]));
});
afterEach(() => {
  localStorage.clear();
});

describe('StartScreen', () => {
  it('renderuje przyciski operatorów i input', () => {
    render(<App />);
    expect(screen.getByText('LogicEngine')).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/np. \(A ∧ B\) → ¬C/)).toBeInTheDocument();
    expect(screen.getByText('Analizuj')).toBeInTheDocument();
    expect(screen.getByText('Definicje pojęć')).toBeInTheDocument();
    expect(screen.getByText('Historia wyrażeń')).toBeInTheDocument();
    expect(screen.getByLabelText('Tryb tutorialowy')).toBeInTheDocument();
  });

  it('po kliknięciu operatora dodaje go do inputa', () => {
    render(<App />);
    const input = screen.getByPlaceholderText(/np. \(A ∧ B\) → ¬C/);
    fireEvent.click(screen.getByText('¬'));
    expect(input.value).toContain('¬');
    fireEvent.click(screen.getByText('∧'));
    expect(input.value).toContain('∧');
  });

  it('po kliknięciu "Definicje pojęć" przechodzi do ekranu definicji', () => {
    render(<App />);
    fireEvent.click(screen.getByText('Definicje pojęć'));
    expect(screen.getByText('Definicje pojęć logicznych')).toBeInTheDocument();
  });

  it('po kliknięciu "Historia wyrażeń" przechodzi do ekranu historii', () => {
    render(<App />);
    fireEvent.click(screen.getByText('Historia wyrażeń'));
    expect(screen.getByText('Historia wyrażeń')).toBeInTheDocument();
  });

  it('po kliknięciu "Analizuj" wywołuje analizę', async () => {
    render(<App />);
    const input = screen.getByPlaceholderText(/np. \(A ∧ B\) → ¬C/);
    fireEvent.change(input, { target: { value: '(A ∧ B) ∨ ¬C' } });
    fireEvent.click(screen.getByText('Analizuj'));
    expect(await screen.findByText('Wynik analizy')).toBeInTheDocument();
  });
}); 