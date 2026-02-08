# TASKS_CONTEXT

## Project Type
Corporate marketing website for **AB-Company** (B2B automation services, 1C focus), implemented as a pixel-accurate clone of logisoft.ru information architecture and visual language with new content.

## Stack
- **Framework:** Next.js (App Router)
- **Language:** TypeScript (repo currently uses non-strict `tsconfig.json`)
- **Styling:** CSS/vanilla styles (do not assume Tailwind unless it is explicitly added to `package.json` + configured)
- **State:** React Hooks (local UI state only)
- **Forms:** Native form + Zod validation (client + server)
- **Testing:** Vitest + React Testing Library
- **E2E:** Playwright (mandatory in CI)
- **Deployment target:** Vercel

## Architecture Style
- **Frontend-only monolith** (single Next.js application)
- Route-level composition using App Router:
  - `/` landing page with modular sections
  - `/cases/[slug]` detailed case pages

## Critical Constraints
1. **No external backend dependency for MVP:** the contact form MUST submit to a real internal API route (`app/api/**`) and return real validation errors. No "fake success" handlers.
2. **Pixel-oriented UI parity:** spacing, typography rhythm, section order and hierarchy aligned with logisoft.ru style baseline.
3. **Content integrity:** all copy and contact data must match source-of-truth task text exactly.
4. **Performance-first:** LCP-focused hero, optimized images, avoid heavy runtime libs.
5. **Accessibility baseline:** semantic headings, form labels, keyboard focus visibility, contrast-safe blue/white palette.
6. **Responsive behavior:** desktop-first clone with robust tablet/mobile adaptation.
7. **Deterministic rendering:** no random values, no time-dependent UI content.
8. **Code boundaries:** business content centralized in typed data layer (`data/content.ts`), components remain presentational.

## Non-Functional Targets
- Lighthouse (desktop): Performance >= 90, Accessibility >= 90, Best Practices >= 90.
- Core Web Vitals-friendly defaults.
- Maintainable component decomposition for swarm parallelism.

## Delivery Boundaries for Swarm
- **Architect:** defines context, file tree, contracts/spec.
- **QA:** writes failing tests first for brand/contacts/cases rendering.
- **Frontend/Backend role:** in this project primarily frontend implementation in Next.js app.
