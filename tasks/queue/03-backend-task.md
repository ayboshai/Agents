# TASK: IMPLEMENTATION (GREEN PHASE)

## 1. OBJECTIVE
Implement the missing data and components to pass the failing QA tests.
**GOAL:** Turn Red tests into Green tests.

## 2. INPUT
- `TASKS_CONTEXT.md` (Tech stack: Next.js, Tailwind).
- `docs/api_spec.md` (Interfaces).
- `tests/` (The failing tests you must satisfy).

## 3. REQUIRED ACTIONS

### A. Data Layer (`data/content.ts`)
Implement the `companyData`, `heroData`, `servicesData`, `marketplaceData`, `casesData` objects exactly as required by `tests/unit/content.test.ts`.
- **Constraint:** Use exact strings ("AB-Company", "+79659903160", etc.) from the Task 01 description.

### B. Components (`components/*.tsx`)
Create the following components with Tailwind styling (match logisoft.ru vibe: Blue/White, Clean).
1.  **Header:** Sticky, with Logo + Contacts + CTA.
2.  **Hero:** H1, Subhead, 4 Stats grid.
3.  **ServicesGrid:** Grid of 4 cards (Implementation, Adaptation, Rent, Marketplaces).
4.  **MarketplaceModule:** Feature block with metrics (x3.9, etc.).
5.  **CasesPreview:** 3 cards with "Read more" links.
6.  **LeadForm:** Simple form with validation logic (console.log on submit is fine for MVP).

### C. Page Assembly (`app/page.tsx`)
Assemble the components into the Landing Page.
- Ensure `<main>` contains the sections with correct `data-testid` attributes (as required by `home.spec.ts`):
  - `hero-section`
  - `services-grid-section`
  - `marketplace-module-section`
  - `cases-preview-section`
  - `lead-form-section`

## 4. EXECUTION RULES
- **Strict TypeScript:** Define interfaces (or import if shared).
- **Test IDs:** You MUST add `data-testid="..."` to wrapper elements so tests can find them.
- **Styling:** Use Tailwind CSS for professional look immediately.

## 5. OUTPUT
- `data/content.ts`
- `components/*.tsx`
- `app/page.tsx`
- `app/layout.tsx` (Basic layout)
