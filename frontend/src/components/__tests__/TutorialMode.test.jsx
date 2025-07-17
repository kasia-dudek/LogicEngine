import React from 'react';
import { render, screen, fireEvent, act } from '@testing-library/react';
import TutorialMode from '../TutorialMode';

const steps = [
  {
    step: 'Krok 1: Tabela prawdy',
    description: 'Opis kroku 1',
    data: {
      truth_table: [
        { A: 0, B: 0, result: 0 },
        { A: 0, B: 1, result: 1 },
      ],
    },
  },
  {
    step: 'Krok 2: QM',
    description: 'Opis kroku 2',
    data: {
      qm: { steps: [{ description: 'QM step' }] },
    },
  },
];

describe('TutorialMode', () => {
  it('renderuje pierwszy krok i toasta', () => {
    render(<TutorialMode steps={steps} onBack={jest.fn()} />);
    expect(screen.getByText('Krok 1: Tabela prawdy')).toBeInTheDocument();
    expect(screen.getByText('Opis kroku 1')).toBeInTheDocument();
    expect(screen.getByText('Tabela prawdy')).toBeInTheDocument();
    expect(screen.getByText('A')).toBeInTheDocument();
    expect(screen.getByText('B')).toBeInTheDocument();
    expect(screen.getByText('result')).toBeInTheDocument();
  });

  it('po kliknięciu "Następny krok" renderuje kolejny krok', () => {
    render(<TutorialMode steps={steps} onBack={jest.fn()} />);
    fireEvent.click(screen.getByText('Następny krok'));
    expect(screen.getByText('Krok 2: QM')).toBeInTheDocument();
    expect(screen.getByText('Opis kroku 2')).toBeInTheDocument();
    expect(screen.getByText((text) => text.includes('QM step'))).toBeInTheDocument();
  });

  it('przycisk "Poprzedni krok" działa', () => {
    render(<TutorialMode steps={steps} onBack={jest.fn()} />);
    fireEvent.click(screen.getByText('Następny krok'));
    fireEvent.click(screen.getByText('Poprzedni krok'));
    expect(screen.getByText('Krok 1: Tabela prawdy')).toBeInTheDocument();
  });

  it('wywołuje onBack po kliknięciu "Wróć"', () => {
    const onBack = jest.fn();
    render(<TutorialMode steps={steps} onBack={onBack} />);
    fireEvent.click(screen.getByText((text) => text.includes('Wróć')));
    expect(onBack).toHaveBeenCalled();
  });

  it('obsługuje brak danych tutorialu', () => {
    render(<TutorialMode steps={[]} onBack={jest.fn()} />);
    expect(screen.getByText('Brak danych tutorialu.')).toBeInTheDocument();
  });
}); 