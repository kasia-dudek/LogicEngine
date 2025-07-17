import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import ExpressionHistory from '../ExpressionHistory';

const mockHistory = [
  { id: '2025-07-17T13:20:00', expression: '(A ∧ B) ∨ ¬C', result: { foo: 1 } },
  { id: '2025-07-17T13:21:00', expression: 'A ∧ B', result: { bar: 2 } },
];

describe('ExpressionHistory', () => {
  beforeEach(() => {
    localStorage.setItem('logicengine_history', JSON.stringify(mockHistory));
  });
  afterEach(() => {
    localStorage.clear();
  });

  it('renderuje historię wyrażeń', () => {
    render(<ExpressionHistory onLoad={jest.fn()} />);
    expect(screen.getByText('(A ∧ B) ∨ ¬C')).toBeInTheDocument();
    expect(screen.getByText('A ∧ B')).toBeInTheDocument();
    expect(screen.getByText('2025-07-17T13:20:00')).toBeInTheDocument();
  });

  it('wywołuje onLoad po kliknięciu "Wczytaj"', () => {
    const onLoad = jest.fn();
    render(<ExpressionHistory onLoad={onLoad} />);
    fireEvent.click(screen.getAllByText('Wczytaj')[0]);
    expect(onLoad).toHaveBeenCalledWith(mockHistory[0]);
  });

  it('czyści historię po kliknięciu "Wyczyść historię"', () => {
    render(<ExpressionHistory onLoad={jest.fn()} />);
    fireEvent.click(screen.getByText('Wyczyść historię'));
    expect(screen.getByText('Brak historii wyrażeń.')).toBeInTheDocument();
    expect(localStorage.getItem('logicengine_history')).toBeNull();
  });

  it('obsługuje pustą historię', () => {
    localStorage.removeItem('logicengine_history');
    render(<ExpressionHistory onLoad={jest.fn()} />);
    expect(screen.getByText('Brak historii wyrażeń.')).toBeInTheDocument();
  });
}); 