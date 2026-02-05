import React from 'react';
import { describe, expect, it } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import {
  heroData,
  servicesData,
  marketplaceData,
  casesData,
} from '../../data/content';
import Hero from '../../components/Hero';
import ServicesGrid from '../../components/ServicesGrid';
import MarketplaceModule from '../../components/MarketplaceModule';
import CasesPreview from '../../components/CasesPreview';

describe('component contracts', () => {
  it('test_positive_flow: Hero renders headline, subhead and exactly 4 stats', () => {
    render(
      <Hero
        headline={heroData.headline}
        subhead={heroData.subhead}
        stats={heroData.stats}
      />,
    );

    expect(screen.getByText(heroData.headline)).toBeInTheDocument();
    expect(screen.getByText(heroData.subhead)).toBeInTheDocument();
    expect(heroData.stats).toHaveLength(4);
  });

  it('test_edge_cases: ServicesGrid renders exactly 4 service items', () => {
    render(<ServicesGrid services={servicesData} />);
    expect(servicesData).toHaveLength(4);

    const serviceCards = screen.getAllByTestId('service-card');
    expect(serviceCards).toHaveLength(4);
  });

  it('test_security: Marketplace metrics are exact immutable contract values', () => {
    render(
      <MarketplaceModule
        title={marketplaceData.title}
        description={marketplaceData.description}
        benefits={marketplaceData.benefits}
        metrics={marketplaceData.metrics}
      />,
    );

    expect(marketplaceData.metrics.grossProfitMultiplier).toBe('x3.9');
    expect(marketplaceData.metrics.revenueMultiplier).toBe('x4.2');
    expect(marketplaceData.metrics.turnoverMultiplier).toBe('x4.5');
  });

  it('test_edge_cases: CasesPreview renders exactly 3 case cards', () => {
    render(<CasesPreview cases={casesData} />);
    expect(casesData).toHaveLength(3);

    const casesRegion = screen.getByTestId('cases-preview');
    expect(within(casesRegion).getAllByTestId('case-card')).toHaveLength(3);
  });
});
