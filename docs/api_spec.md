# API & Interface Specification — AB-Company Corporate Site

## 1) Scope
This document defines the internal contracts for UI composition, content models, and form interaction for the Next.js implementation.

---

## 2) Route Contract

### `GET /`
- **Purpose:** Render landing page with sections:
  1. Sticky Header
  2. Hero + value stats
  3. Services grid
  4. Marketplace module block
  5. Cases preview cards
  6. Contact form
- **Rendering mode:** Static generation (default), optional revalidate.

### `GET /cases/[slug]`
- **Purpose:** Render full case details selected from canonical cases dataset.
- **Params:**
  - `slug: string` — one of predefined case slugs.
- **Behavior:**
  - Unknown slug -> `notFound()` (404).

---

## 3) Data Model Contracts (`data/content.ts`)

### `CompanyContacts`
```ts
interface CompanyContacts {
  companyName: 'AB-Company';
  phone: '+79659903160';
  email: 'ticketbad@gmail.com';
  telegram: '@Ticket_lucky';
  whatsappUrl: string; // wa.me based link for +79659903160
}
```

### `HeroStat`
```ts
interface HeroStat {
  title: string;       // e.g. "Выгодно"
  description: string; // explanatory copy
}
```

### `ServiceItem`
```ts
interface ServiceItem {
  id: 'implementation' | 'adaptation' | 'rent' | 'marketplaces';
  title: string;
  description: string;
  icon: string; // lucide icon key
}
```

### `MarketplaceMetrics`
```ts
interface MarketplaceMetrics {
  grossProfitMultiplier: 'x3.9';
  revenueMultiplier: 'x4.2';
  turnoverMultiplier: 'x4.5';
}
```

### `CaseStudy`
```ts
interface CaseStudy {
  slug: string;
  title: string;
  location: string;
  problem: string;
  solution: string;
  result: string;
}
```

### `LeadFormPayload`
```ts
interface LeadFormPayload {
  name: string;
  phone: string;
  message: string;
}
```

Validation rules:
- `name`: required, 2..80 chars.
- `phone`: required, includes at least 10 digits.
- `message`: required, 10..1000 chars.

---

## 4) UI Component Interface Contracts

### `Header`
```ts
interface HeaderProps {
  contacts: CompanyContacts;
}
```
- Must show company name, phone, email, telegram, WhatsApp CTA.

### `Hero`
```ts
interface HeroProps {
  headline: string;
  subhead: string;
  stats: HeroStat[]; // exactly 4 items
}
```
- Must expose primary CTA "Оставить заявку" and secondary CTA "Позвонить нам".

### `ServicesGrid`
```ts
interface ServicesGridProps {
  services: ServiceItem[]; // exactly 4 items
}
```

### `MarketplaceModule`
```ts
interface MarketplaceModuleProps {
  title: string;
  description: string;
  benefits: string[]; // 3 items
  metrics: MarketplaceMetrics;
}
```

### `CasesPreview`
```ts
interface CasesPreviewProps {
  cases: CaseStudy[]; // exactly 3 items for MVP
}
```
- Card click navigates to `/cases/[slug]`.

### `LeadForm`
```ts
interface LeadFormProps {
  onSubmit: (payload: LeadFormPayload) => Promise<void> | void;
}
```
- Fields: Name, Phone, Message.
- Submit label: "Оставить заявку".

---

## 5) Testable Acceptance Contracts

1. Header contains `AB-Company` and phone `+79659903160`.
2. Landing page renders exactly 3 case preview cards.
3. Hero contains required headline and both CTA buttons.
4. Services section renders 4 service cards.
5. Contact form exposes required 3 fields and submit action.
6. Cases routes resolve all predefined slugs.

---

## 6) File Structure Plan (Execution Target)

```text
.
├── TASKS_CONTEXT.md
├── app/
│   ├── layout.tsx
│   ├── page.tsx
│   └── cases/
│       └── [slug]/
│           └── page.tsx
├── components/
│   ├── Header.tsx
│   ├── Hero.tsx
│   ├── ServicesGrid.tsx
│   ├── MarketplaceModule.tsx
│   ├── CasesPreview.tsx
│   ├── LeadForm.tsx
│   └── shared/
│       ├── Section.tsx
│       └── Container.tsx
├── data/
│   └── content.ts
├── docs/
│   └── api_spec.md
├── tests/
│   ├── unit/
│   │   ├── header.test.tsx
│   │   └── cases.test.tsx
│   └── e2e/
│       └── landing.spec.ts
└── public/
    └── images/
```

---

## 7) Swarm Execution Sequence

1. **QA (first):** author failing tests for company name, phone rendering, and 3 cases presence.
2. **Frontend:** scaffold Next.js app router structure and shared layout primitives.
3. **Frontend:** implement content contract in `data/content.ts` and wire into presentational components.
4. **Frontend:** implement landing sections in target order with responsive Tailwind styles.
5. **Frontend:** implement `/cases/[slug]` detail pages and card navigation.
6. **QA:** run unit/e2e suite, verify contract compliance.
7. **Frontend:** fix defects and perform final visual parity pass.
