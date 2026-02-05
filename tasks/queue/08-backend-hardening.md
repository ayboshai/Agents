# TASK: BACKEND HARDENING & REFACTOR

## 1. OBJECTIVE
Refactor the current implementation to be **Production Grade**, based on the audit from `tasks/feedback/hardening_plan.md`.

## 2. INPUTS
- `tasks/feedback/hardening_plan.md` (Your TODO list).
- The current codebase (`src/`, `components/`, `data/`).

## 3. CRITICAL ACTIONS (Must Be Completed)
1.  **Implement Real API Endpoint:**
    - Create `app/api/leads/route.ts`.
    - It must accept a POST request with the form payload.
    - **Use Zod for validation on the server.** If validation fails, return a 400 error.
    - On success, return a 200 OK response. (No database connection needed yet, just a successful API response).
2.  **Refactor LeadForm Component:**
    - Use `fetch` to POST data to your new `/api/leads` endpoint.
    - Implement loading/submitting state (disable button).
    - Implement success and error states (show a message to the user).
    - **Use Zod on the client** for instant validation feedback.
3.  **Centralize Content:**
    - Move hardcoded strings ("Name", "Phone", "Read more", etc.) from components into `data/content.ts`.
4.  **Implement SEO Metadata:**
    - Add a `metadata` export to `app/layout.tsx` with a proper title, description, and OG tags.

## 4. FINAL INSTRUCTION (NEW PROTOCOL)
After you have committed your changes to a new branch, you **must** automatically create a Pull Request against the `main` branch using your internal tools. **Do not wait for a manual button click.**

## 5. OUTPUT
- Production-ready, refactored code that passes all previous and new tests.
- An automatically created Pull Request.
