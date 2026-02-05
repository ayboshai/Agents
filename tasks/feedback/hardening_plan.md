# Hardening Plan — System Analyst Audit (LARP Detector)

## Verdict
**REJECT — current implementation is not production-grade.**

The codebase passes a small test suite, but core user flow and quality requirements still contain fake or under-hardened behavior. Most severe finding: the lead form submission path is a fake implementation (`console.log`) that gives the appearance of working without delivering any business action.

## Evidence Summary

### 1) CI Check (Did tests really run?)
- CI log shows Vitest executed and all discovered tests passed (`11 passed`).
- However, this is **insufficient depth** for a production gate because no tests prove a real submission workflow, network error handling, or metadata/SEO output.

### 2) LARP / Stub / Slop Audit

#### CRITICAL-1 — Fake submission flow in primary lead capture
- **File:** `app/page.tsx`
- **Finding:** `LeadForm` is wired with `onSubmit={(payload) => console.log('Lead submitted:', payload)}`.
- **Why this is critical:** This is explicitly fake behavior (no transport, no persistence, no failure path, no user feedback). It violates the LARP detector checklist and Commandment #1 (Real Code Only).

#### CRITICAL-2 — Submission error path is not handled in UI
- **File:** `components/LeadForm.tsx`
- **Finding:** `await onSubmit(...)` is not wrapped in resilient state handling. If callback rejects, user-facing state is not updated with recovery guidance.
- **Impact:** In real integrations, transient API failures produce silent UX dead-ends or unhandled promise errors.

#### CRITICAL-3 — i18n/content-boundary violation via hardcoded UI strings
- **Files:** `components/LeadForm.tsx`, `components/CasesPreview.tsx`
- **Finding:** Labels/CTA strings such as `Name`, `Phone`, `Message`, `Read more` are hardcoded in components rather than centralized content data.
- **Impact:** Violates project boundary rule requiring business content in `data/content.ts`, creates drift risk and non-deterministic copy governance.

#### CRITICAL-4 — Metadata/SEO baseline missing
- **File:** `app/layout.tsx`
- **Finding:** No Next.js `metadata` export (title/description/open graph/canonical basics).
- **Impact:** Fails scope requirement to verify SEO configuration in `app/` and weakens production readiness.

### 3) Additional Quality Risks

#### QUALITY-1 — Validation is custom and shallow; no schema-level contract
- **File:** `components/LeadForm.tsx`
- **Finding:** Validation is manual length checks and digit counting only.
- **Risk:** Logic duplication and fragile evolution. A schema-based validator (e.g., Zod) would provide composable constraints and better testability.

#### QUALITY-2 — Type model is too rigid in the wrong places
- **File:** `data/content.ts`
- **Finding:** Literal-locked interfaces (`companyName: 'AB-Company'`, metrics as fixed string literals like `'x3.9'`) constrain reuse while not improving runtime safety.
- **Risk:** Artificial type brittleness and noisy future content updates.

#### QUALITY-3 — Accessibility hardening gaps
- **Files:** `components/LeadForm.tsx`, shared UI sections
- **Finding:** Error message lacks ARIA live-region semantics; controls do not expose invalid state (`aria-invalid`) when validation fails.
- **Risk:** Screen reader users may miss critical feedback.

#### QUALITY-4 — Empty-state resilience is not explicit
- **Files:** `components/Hero.tsx`, `components/CasesPreview.tsx`, `components/ServicesGrid.tsx`
- **Finding:** Rendering assumes non-empty arrays. No guard rails or fallback UI for empty datasets.
- **Risk:** Silent blank sections or reduced UX quality if data contracts change.

## Remediation Plan

### Section 1 — Critical (Must fix for Security/Stability)
1. Replace fake `console.log` lead submission with a real submission contract:
   - Implement `app/api/lead/route.ts` (or explicit external integration adapter).
   - Return structured success/error payloads.
   - Add user-visible success and failure states in `LeadForm`.
2. Harden `LeadForm` async flow:
   - Add submitting state (disable button, prevent double-submit).
   - Catch and classify network/server errors.
   - Preserve input values on failure.
3. Move all user-facing copy from component literals to typed content layer (`data/content.ts`), including form labels and case CTA.
4. Add `metadata` export in `app/layout.tsx` (title template, description, OG defaults, robots basics).

### Section 2 — Quality (Refactoring & Validation)
1. Introduce schema validation (Zod) for lead payload:
   - Shared schema for client pre-validation + API route validation.
   - Centralized error map for localized messaging.
2. Rework content typing strategy:
   - Use `as const` on data objects where useful.
   - Avoid overly narrow interface literals unless business invariant truly immutable.
3. Add accessibility semantics:
   - `aria-live="polite"` for status/error region.
   - `aria-invalid` and `aria-describedby` wiring for inputs.
4. Add explicit empty-state rendering for sections dependent on arrays.

### Section 3 — Cleanup (Maintainability)
1. Normalize language consistency in UI copy (currently mixed RU/EN).
2. Replace icon-name strings with typed icon mapping in presentational layer to avoid drift.
3. Expand test matrix:
   - Unit: validation boundary tests and rejected submit callback behavior.
   - Integration: successful form submit + API failure response handling.
   - E2E: complete lead flow assertion with user-visible outcome.

## Action
- **Fix Request Issued** — continue in fix loop; do not release until all Critical items are closed and backed by deep tests.
