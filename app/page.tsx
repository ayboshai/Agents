import CasesPreview from '../components/CasesPreview';
import Header from '../components/Header';
import Hero from '../components/Hero';
import LeadForm from '../components/LeadForm';
import MarketplaceModule from '../components/MarketplaceModule';
import ServicesGrid from '../components/ServicesGrid';
import {
  casesData,
  companyData,
  heroData,
  marketplaceData,
  servicesData,
} from '../data/content';

export default function HomePage() {
  return (
    <>
      <Header contacts={companyData} />
      <main>
        <div data-testid="hero-section">
          <Hero headline={heroData.headline} stats={heroData.stats} subhead={heroData.subhead} />
        </div>
        <div data-testid="services-grid-section">
          <ServicesGrid services={servicesData} />
        </div>
        <div data-testid="marketplace-module-section">
          <MarketplaceModule
            benefits={marketplaceData.benefits}
            description={marketplaceData.description}
            metrics={marketplaceData.metrics}
            title={marketplaceData.title}
          />
        </div>
        <div data-testid="cases-preview-section">
          <CasesPreview cases={casesData} />
        </div>
        <div data-testid="lead-form-section">
          <LeadForm />
        </div>
      </main>
    </>
  );
}
