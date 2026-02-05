import type { CompanyContacts } from '../data/content';

interface HeaderProps {
  contacts: CompanyContacts;
}

export default function Header({ contacts }: HeaderProps) {
  return (
    <header className="sticky top-0 z-50 border-b border-blue-100 bg-white/95 backdrop-blur" role="banner">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-6 py-4">
        <a className="text-xl font-bold text-blue-900" href="#hero">
          {contacts.companyName}
        </a>
        <div className="flex flex-wrap items-center gap-4 text-sm text-slate-700">
          <a className="hover:text-blue-700" href={`tel:${contacts.phone}`}>
            {contacts.phone}
          </a>
          <a className="hover:text-blue-700" href={`mailto:${contacts.email}`}>
            {contacts.email}
          </a>
          <a className="hover:text-blue-700" href={`https://t.me/${contacts.telegram.replace('@', '')}`}>
            {contacts.telegram}
          </a>
          <a className="rounded-md bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700" href={contacts.whatsappUrl}>
            WhatsApp
          </a>
        </div>
      </div>
    </header>
  );
}
