# TASK: QA CONTRACT TESTS (TDD)

## 1. OBJECTIVE
Write the **Failing Tests** (Contract Tests) that define the expected behavior of the AB-Company website.
The Backend/Frontend developer will later write code to pass these tests.

## 2. INPUT
- `TASKS_CONTEXT.md` (Tech stack: Vitest, React Testing Library).
- `docs/api_spec.md` (Interfaces for CompanyContacts, Hero, Services, etc.).

## 3. REQUIRED TESTS

### A. Data Integrity (`tests/unit/content.test.ts`)
Write a test that imports `companyData` (which doesn't exist yet) and asserts:
- `companyName` is "AB-Company".
- `phone` is "+79659903160".
- `email` is "ticketbad@gmail.com".
- `whatsappUrl` correctly formats the phone number.

### B. Component Contracts (`tests/unit/components.test.tsx`)
Mock the components and assert they render correct props:
- **Hero:** Check it renders `headline`, `subhead`, and exactly 4 `stats`.
- **ServicesGrid:** Check it renders 4 service items.
- **MarketplaceModule:** Check it renders metrics (x3.9, x4.2, x4.5).
- **CasesPreview:** Check it renders 3 case cards.

### C. Page Structure (`tests/e2e/home.spec.ts` - Mocked)
Since E2E is heavy, write a *structural unit test* for the Home Page:
- Assert that `<main>` contains: `<Hero>`, `<ServicesGrid>`, `<MarketplaceModule>`, `<CasesPreview>`, `<LeadForm>`.
- Assert header contains contact info.

## 4. EXECUTION RULES
- **DO NOT** implement the components. Only import them (they will fail to resolve, which is fine, or mock them as "any").
- **DO NOT** write the content.ts file.
- The tests **MUST FAIL** or compile with errors (Red phase).

## 5. OUTPUT
- `tests/unit/content.test.ts`
- `tests/unit/components.test.tsx`
- `vitest.config.ts` (Setup basic config)
