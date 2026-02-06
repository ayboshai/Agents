import React from 'react';
import { describe, expect, it } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import HomePage from '../../app/page';

describe('home page structure contract (mocked)', () => {
  it('test_positive_flow: <main> includes required section components in order', () => {
    render(<HomePage />);

    const main = screen.getByRole('main');
    const mainScope = within(main);

    expect(mainScope.getByTestId('hero-section')).toBeInTheDocument();
    expect(mainScope.getByTestId('services-grid-section')).toBeInTheDocument();
    expect(mainScope.getByTestId('marketplace-module-section')).toBeInTheDocument();
    expect(mainScope.getByTestId('cases-preview-section')).toBeInTheDocument();
    expect(mainScope.getByTestId('lead-form-section')).toBeInTheDocument();
  });

  it('test_edge_cases: header contains AB-Company contact info', () => {
    render(<HomePage />);

    const header = screen.getByRole('banner');
    expect(within(header).getByText('AB-Company')).toBeInTheDocument();
    expect(within(header).getByText('+79659903160')).toBeInTheDocument();
    expect(within(header).getByText('ticketbad@gmail.com')).toBeInTheDocument();
  });

  it('test_security: no dangerous inline javascript links in primary navigation', () => {
    render(<HomePage />);

    const links = screen.getAllByRole('link');
    for (const link of links) {
      const href = link.getAttribute('href') ?? '';
      expect(href.toLowerCase()).not.toContain('javascript:');
    }
  });
});
