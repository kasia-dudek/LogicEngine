import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import App from './App';

describe('LogicEngine App', () => {
  it('renders StartScreen and allows input', () => {
    render(<App />);
    expect(screen.getByText(/LogicEngine/i)).toBeInTheDocument();
    const input = screen.getByPlaceholderText(/np. \(A ∧ B\) → ¬C/i);
    fireEvent.change(input, { target: { value: 'A∧B' } });
    expect((input as HTMLInputElement).value).toBe('A∧B');
  });

  it('shows ResultScreen after analyze', async () => {
    render(<App />);
    const input = screen.getByPlaceholderText(/np. \(A ∧ B\) → ¬C/i);
    fireEvent.change(input, { target: { value: 'A∧B' } });
    fireEvent.click(screen.getByRole('button', { name: /Analizuj/i }));
    expect(await screen.findByText(/Wynik analizy/i)).toBeInTheDocument();
    expect(screen.getByText(/Wyrażenie:/i)).toBeInTheDocument();
    expect(screen.getByText('A∧B')).toBeInTheDocument();
    expect(screen.getByText(/Tabela prawdy/i)).toBeInTheDocument();
  });
});
