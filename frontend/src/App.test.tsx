import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';

test('renders app with login page by default', () => {
  render(<App />);
  const heading = screen.getByText(/Login/i);
  expect(heading).toBeInTheDocument();
});
