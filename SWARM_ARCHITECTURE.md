# Codex Swarm Architecture: Browser-Driven GitOps & TDD (v2.0 - Production Grade)

> **The 7 Commandments of Engineering Excellence:**
> 1.  **Real Code Only:** No stubs, no placeholders, no "implementation details hidden". Handle errors and edge cases immediately. Full realization.
> 2.  **Code Quality:** Refactor for compactness. No duplication. Idiomatic logic. Consistent naming.
> 3.  **No AI-Slop:** Remove over-engineering, generic wrappers, verbose comments, and "defensive" code for impossible cases.
> 4.  **Deep Testing:** Beyond happy path. Test boundaries, invalid inputs, concurrency. **NO MOCKS** for the logic under test. Integration tests must run real code paths.
> 5.  **LARP Detection:** Critically audit code. Does it return fake data? Is validation hollow? If yes -> FAIL.
> 6.  **Production Ready:** Config externalized. Secrets managed. Performance checked. Logging/Alerting in place.
> 7.  **Final Audit:** Verify real execution. Does it solve the problem? Fix all TODOs before signing off.

## 1. System Overview

**Components:**
1.  **OpenClaw (Orchestrator):** Manages local files, browser relay, and git sync.
2.  **GitHub (State & Exchange):** Serves as the message bus AND the CI/CD runner.
3.  **Codex (Worker):** The LLM execution engine.

## 2. Workflow Lifecycle (The "Quality Loop")

The workflow is strictly sequential with mandatory feedback loops. **Skipping steps is FORBIDDEN.**

### Phase 1: Inception & CI Setup
1.  **Architect:**
    *   Creates `TASKS_CONTEXT.md` (Project Rules).
    *   Creates `.github/workflows/ci.yml` (Real CI is mandatory).
    *   Creates `00-structure.md`.

### Phase 2: The Truth (Contract Testing)
2.  **QA (Contract Mode):**
    *   Writes **Failing Tests** (Red phase).
    *   **Rule:** No mocks for internal logic. Mocks allowed only for external 3rd party APIs (e.g. Stripe), but internal interactions must be real.

### Phase 3: Implementation (Production Grade)
3.  **Backend Developer:**
    *   Writes **Production Code** (no stubs).
    *   Removes "AI Slop" (wrappers, useless comments).
    *   Ensures code passes CI.

### Phase 4: E2E Verification (MANDATORY)
4.  **QA (E2E Mode):**
    *   **Rule:** Must verify the full user flow (Playwright/Selenium).
    *   **Scope:** Click buttons, submit forms, check DB state.
    *   **Goal:** Verify "Real World" functionality, not just unit logic.

### Phase 5: LARP Audit & Analysis
5.  **System Analyst (The Gatekeeper):**
    *   **LARP Check:** Does the code actually work or just look like it works?
    *   **Audit:** Checks for hardcoded fake data pretending to be dynamic.
    *   **Action:** If ANY "fake" logic is found -> **REJECT** with `fix_required.md`.

### Phase 6: The Fix Loop
6.  **Backend/QA:**
    *   Fix issues found by Analyst.
    *   Re-run full test suite.
    *   **Constraint:** Do not declare completion until `TODO` list is empty.

## 3. Dynamic Context Injection
All agents must adhere to `TASKS_CONTEXT.md`.

## 4. Agent Personas (Updated)
*   **Architect:** Infrastructure & CI expert.
*   **QA:** "Mocks are garbage" philosophy. Integration-first.
*   **Backend:** Anti-boilerplate. Production-ready implementation.
*   **Analyst:** LARP Detector.

## 5. Folder Structure
```
/
├── .github/workflows/     # MANDATORY: Real CI/CD
├── TASKS_CONTEXT.md       # Rules
├── src/
├── tests/                 # Integration & E2E (No unit mocks for logic)
└── tasks/
```
