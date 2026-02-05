import type { MarketplaceMetrics } from '../data/content';

interface MarketplaceModuleProps {
  title: string;
  description: string;
  benefits: string[];
  metrics: MarketplaceMetrics;
}

export default function MarketplaceModule({
  title,
  description,
  benefits,
  metrics,
}: MarketplaceModuleProps) {
  return (
    <section className="bg-blue-900 text-white">
      <div className="mx-auto grid max-w-6xl gap-8 px-6 py-16 lg:grid-cols-2">
        <div>
          <h2 className="text-3xl font-bold">{title}</h2>
          <p className="mt-4 text-blue-100">{description}</p>
          <ul className="mt-6 list-disc space-y-2 pl-5 text-blue-100">
            {benefits.map((benefit) => (
              <li key={benefit}>{benefit}</li>
            ))}
          </ul>
        </div>

        <div className="grid gap-4 sm:grid-cols-3 lg:grid-cols-1">
          <article className="rounded-xl bg-white/10 p-4">
            <p className="text-sm text-blue-100">Валовая прибыль</p>
            <p className="text-3xl font-bold">{metrics.grossProfitMultiplier}</p>
          </article>
          <article className="rounded-xl bg-white/10 p-4">
            <p className="text-sm text-blue-100">Выручка</p>
            <p className="text-3xl font-bold">{metrics.revenueMultiplier}</p>
          </article>
          <article className="rounded-xl bg-white/10 p-4">
            <p className="text-sm text-blue-100">Товарооборот</p>
            <p className="text-3xl font-bold">{metrics.turnoverMultiplier}</p>
          </article>
        </div>
      </div>
    </section>
  );
}
