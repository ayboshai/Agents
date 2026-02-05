# TASK: E2E VALIDATION OF HARDENING FIXES

## 1. OBJECTIVE
Validate that the "Hardening" fixes from the Backend developer are complete and correct.

## 2. SCOPE
You must update your Playwright tests (`tests/e2e/submission.spec.ts`) to verify:
1.  **Real Form Submission:**
    - The form POSTs to `/api/leads`.
    - A **successful** submission (API returns 200) shows a success message on the UI.
    - A **failed** submission (API returns 400/500) shows an error message on the UI.
2.  **Zod Validation:**
    - Test client-side validation for empty/invalid inputs (email, phone).
    - The correct error messages appear.
3.  **SEO Metadata:**
    - The page `<title>` is correct.
    - `<meta name="description">` exists and has content.
4.  **Content Centralization:**
    - Check that form labels ("Name", "Phone") are NOT hardcoded in the component, but are rendered from the data layer.

## 3. EXECUTION
- Modify `tests/e2e/submission.spec.ts`.
- You may need to add a "test" script to `package.json` for Playwright (`"test:e2e": "playwright test"`).

## 4. OUTPUT
- Updated Playwright test files that cover all hardening requirements.
- **Auto-create a Pull Request.**
