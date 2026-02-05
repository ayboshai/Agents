# TASK: E2E HARDENING (PLAYWRIGHT)

## 1. OBJECTIVE
Write **Real E2E Tests** (Playwright) to enforce the "No LARP" policy.
These tests will run against a real built Next.js application, not just JSDOM.

## 2. SCOPE
- **Submission Flow:** Verify that submitting the form triggers a real network request (POST `/api/leads`) and shows a visible success message.
- **Validation:** Verify that empty fields show ARIA-compliant error messages.
- **SEO:** Verify `<title>`, `<meta name="description">`, and OpenGraph tags exist.
- **404:** Verify visiting `/cases/fake-slug` returns a 404 status and user-friendly error page.

## 3. EXECUTION
- Create `tests/e2e/submission.spec.ts`.
- Use `page.request.post` or intercept network traffic to verify the API call.
- **Constraint:** Do not mock the *internal* API handler. The test must fail if `app/api/leads/route.ts` does not exist.

## 4. OUTPUT
- `tests/e2e/submission.spec.ts`
- `playwright.config.ts` (Configured for localhost:3000)
