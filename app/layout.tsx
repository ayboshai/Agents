import type { Metadata } from 'next';
import type { ReactNode } from 'react';

interface RootLayoutProps {
  children: ReactNode;
}

export const metadata: Metadata = {
  title: 'AB-Company — Автоматизация 1С и интеграции',
  description:
    'AB-Company внедряет и сопровождает решения 1С, интеграции с маркетплейсами и автоматизацию бизнес-процессов.',
  openGraph: {
    title: 'AB-Company — Автоматизация 1С и интеграции',
    description:
      'Внедрение, адаптация и поддержка 1С для роста прибыли, контроля процессов и масштабирования.',
    type: 'website',
    locale: 'ru_RU',
  },
};

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="ru">
      <body className="bg-white text-slate-900 antialiased">{children}</body>
    </html>
  );
}
