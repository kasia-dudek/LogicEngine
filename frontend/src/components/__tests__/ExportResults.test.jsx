import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import ExportResults from '../ExportResults';

jest.mock('jspdf', () => {
  return jest.fn().mockImplementation(() => ({
    setFont: jest.fn(),
    setFontSize: jest.fn(),
    text: jest.fn(),
    save: jest.fn(),
  }));
});

global.URL.createObjectURL = jest.fn(() => 'blob:url');

describe('ExportResults', () => {
  const data = {
    expression: '(A ∧ B) ∨ ¬C',
    truth_table: [
      { A: 0, B: 0, C: 0, result: 1 },
      { A: 1, B: 1, C: 0, result: 1 },
    ],
    qm: { result: 'A ∧ B ∨ ¬C', steps: [{ description: 'QM step 1' }] },
    kmap: { result: 'A ∧ B ∨ ¬C', kmap: [[0,1],[1,0]], groups: [] },
    ast: { node: '∨', left: {}, right: {} },
  };

  it('eksportuje do PDF i wyświetla Toast', () => {
    render(<ExportResults data={data} />);
    fireEvent.click(screen.getByText('Eksportuj do PDF'));
    expect(screen.getByText('Eksport do PDF zakończony pomyślnie')).toBeInTheDocument();
  });

  it('eksportuje do JSON i wyświetla Toast', () => {
    render(<ExportResults data={data} />);
    fireEvent.click(screen.getByText('Eksportuj do JSON'));
    expect(screen.getByText('Eksport do JSON zakończony pomyślnie')).toBeInTheDocument();
  });

  it('obsługuje brak danych przy eksporcie PDF', () => {
    render(<ExportResults data={null} />);
    fireEvent.click(screen.getByText('Eksportuj do PDF'));
    expect(screen.getByText('Błąd eksportu PDF: brak danych')).toBeInTheDocument();
  });

  it('obsługuje brak danych przy eksporcie JSON', () => {
    render(<ExportResults data={null} />);
    fireEvent.click(screen.getByText('Eksportuj do JSON'));
    expect(screen.getByText('Błąd eksportu JSON: brak danych')).toBeInTheDocument();
  });
}); 