import React from 'react';
import { render, screen, act } from '@testing-library/react';
import Toast from '../Toast';

describe('Toast', () => {
  it('renders success message', () => {
    render(<Toast message="Success!" type="success" />);
    expect(screen.getByText('Success!')).toBeInTheDocument();
    expect(screen.getByText('Success!').className).toMatch(/bg-green-500/);
  });

  it('renders error message', () => {
    render(<Toast message="Error!" type="error" />);
    expect(screen.getByText('Error!')).toBeInTheDocument();
    expect(screen.getByText('Error!').className).toMatch(/bg-red-500/);
  });

  it('disappears after 3 seconds', () => {
    jest.useFakeTimers();
    const onClose = jest.fn();
    render(<Toast message="Bye!" type="success" onClose={onClose} />);
    act(() => {
      jest.advanceTimersByTime(3000);
    });
    expect(onClose).toHaveBeenCalled();
    jest.useRealTimers();
  });
}); 