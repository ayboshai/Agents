# TASK: DEEP CODE AUDIT (HARDENING)

## 1. OBJECTIVE
Perform a **Merciless Code Audit** of the current implementation.
We need to turn this "Happy Path" prototype into **Production Grade** software.

## 2. SCOPE
- `components/LeadForm.tsx`: Does it actually validate? Does it handle API errors? (Currently likely just `console.log`).
- `data/content.ts`: Are types strict?
- `components/*.tsx`: Are there accessibility issues? Hardcoded strings outside of content layer?
- `app/`: Is metadata/SEO configured?

## 3. CHECKLIST (THE "LARP" DETECTOR)
You must flag ANY of the following as **CRITICAL ISSUES**:
1.  **Fake Submissions:** `onSubmit` that only does `console.log` or `alert`.
2.  **Weak Validation:** Checking `text.length > 0` instead of using Zod/React Hook Form.
3.  **Magic Numbers:** Inline styles or arbitrary values instead of Tailwind tokens.
4.  **AI Slop:** Comments like `// This component renders the hero`.
5.  **Missing Error Boundaries:** What happens if `stats` array is empty?
6.  **Type Safety:** Any usage of `any`.

## 4. EXECUTION
1.  Read the code in `src/` (or root components).
2.  Compare against **The 7 Commandments** in `SWARM_ARCHITECTURE.md`.
3.  Generate a detailed remediation plan.

## 5. OUTPUT
- `tasks/feedback/hardening_plan.md`: A structured list of what needs to be fixed.
  - Section 1: Critical (Must fix for Security/Stability).
  - Section 2: Quality (Refactoring, Zod integration).
  - Section 3: Cleanup (Removing comments).
