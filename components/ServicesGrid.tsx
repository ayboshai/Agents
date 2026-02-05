import type { ServiceItem } from '../data/content';

interface ServicesGridProps {
  services: ServiceItem[];
}

export default function ServicesGrid({ services }: ServicesGridProps) {
  return (
    <section className="mx-auto max-w-6xl px-6 py-16">
      <h2 className="text-3xl font-bold text-slate-900">Услуги AB-Company</h2>
      <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {services.map((service) => (
          <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm" data-testid="service-card" key={service.id}>
            <p className="text-xs font-semibold uppercase tracking-wide text-blue-600">{service.icon}</p>
            <h3 className="mt-2 text-lg font-semibold text-slate-900">{service.title}</h3>
            <p className="mt-2 text-sm text-slate-600">{service.description}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
