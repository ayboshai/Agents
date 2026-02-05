import type { HeroStat } from '../data/content';

interface HeroProps {
  headline: string;
  subhead: string;
  stats: HeroStat[];
}

export default function Hero({ headline, subhead, stats }: HeroProps) {
  return (
    <section className="bg-gradient-to-b from-blue-50 to-white" id="hero">
      <div className="mx-auto max-w-6xl px-6 py-16">
        <h1 className="max-w-4xl text-4xl font-bold leading-tight text-slate-900 md:text-5xl">{headline}</h1>
        <p className="mt-6 max-w-3xl text-lg text-slate-600">{subhead}</p>
        <div className="mt-8 flex flex-wrap gap-3">
          <button className="rounded-md bg-blue-600 px-5 py-3 font-semibold text-white hover:bg-blue-700" type="button">
            Оставить заявку
          </button>
          <button className="rounded-md border border-blue-600 px-5 py-3 font-semibold text-blue-700 hover:bg-blue-50" type="button">
            Позвонить нам
          </button>
        </div>

        <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {stats.map((stat) => (
            <article className="rounded-xl border border-blue-100 bg-white p-4" key={stat.title}>
              <h3 className="text-lg font-semibold text-slate-900">{stat.title}</h3>
              <p className="mt-2 text-sm text-slate-600">{stat.description}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
