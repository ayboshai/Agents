import type { CaseStudy } from '../data/content';

interface CasesPreviewProps {
  cases: CaseStudy[];
}

export default function CasesPreview({ cases }: CasesPreviewProps) {
  return (
    <section className="mx-auto max-w-6xl px-6 py-16" data-testid="cases-preview">
      <h2 className="text-3xl font-bold text-slate-900">Кейсы клиентов</h2>
      <div className="mt-8 grid gap-5 md:grid-cols-3">
        {cases.map((caseItem) => (
          <article className="rounded-xl border border-slate-200 bg-white p-5" data-testid="case-card" key={caseItem.slug}>
            <p className="text-xs uppercase text-blue-600">{caseItem.location}</p>
            <h3 className="mt-2 text-lg font-semibold text-slate-900">{caseItem.title}</h3>
            <p className="mt-2 text-sm text-slate-600">{caseItem.result}</p>
            <a className="mt-4 inline-block text-sm font-semibold text-blue-700 hover:underline" href={`/cases/${caseItem.slug}`}>
              Read more
            </a>
          </article>
        ))}
      </div>
    </section>
  );
}
