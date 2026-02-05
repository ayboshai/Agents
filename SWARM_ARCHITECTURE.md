# Codex Swarm Architecture: Browser-Driven GitOps & TDD (v2.1 - Production Grade)

> **The 7 Commandments of Engineering Excellence:**
> 1.  **Real Code Only:** No stubs, no placeholders. Handle errors and edge cases immediately.
> 2.  **Code Quality:** Refactor for compactness, simplicity, and consistency.
> 3.  **No AI-Slop:** Remove over-engineering, generic wrappers, and verbose comments.
> 4.  **Deep Testing:** Beyond happy path. **NO MOCKS** for internal logic.
> 5.  **LARP Detection:** Critically audit code for fake implementations.
> 6.  **Production Ready:** Config externalized, secrets managed, performance checked.
> 7.  **Final Audit:** Verify real execution and solve the root problem.

## 1. System Overview
**Components:**
1.  **OpenClaw (Orchestrator & Deployer):** Manages local files, browser relay, git sync, **and runs the final staging server**.
2.  **GitHub (State & CI/CD):** Serves as the message bus and CI runner.
3.  **Codex (Worker):** The LLM execution engine.

## 2. Workflow Lifecycle (The "Quality Loop")

**STATE MACHINE:** The entire workflow is governed by `swarm_state.json`. Before executing any agent, the Orchestrator (Danny AI) **MUST** verify that the agent's role matches the `next_phase` in the state file. After completion, the state file **MUST** be updated. This is a hard, programmatic rule to prevent skipping steps.

### Phase 1-6 (As before: Architect -> QA -> Dev -> QA(E2E) -> Analyst -> Fix Loop)
...

### Phase 7: Staging Deployment & Real-World Validation (NEW)
7.  **OpenClaw (Deployer):**
    *   Pulls the final `main` branch.
    *   Runs `npm run build && npm run start` on a specified port (e.g., 3001).
8.  **QA (Real-World E2E):**
    *   Runs Playwright tests against the **LIVE STAGING SERVER** (`http://<server_ip>:3001`).
    *   **Goal:** Catch environment-specific bugs (e.g., CORS, file paths).
9.  **Analyst (Final Sign-off):**
    *   Reviews the live test results.
    *   If PASS -> **Final Approval**.
    *   If FAIL -> Creates a high-priority `fix_request.md` for environmental issues.

## 3. Agent Persona Updates
*   **Architect:** Must now consider `.env.local` for port configuration.
*   **QA:** E2E tests must be runnable against a configurable `baseURL`.
*   **Analyst:** Final check must include server logs if available.
