# Codex Swarm Architecture: Browser-Driven GitOps & TDD (v2.1 - Production Grade)

**Canonical Law:** `SWARM_CONSTITUTION.md` is the single source of truth. This document is a human-readable overview only.

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

**STATE MACHINE IS LAW:** The entire workflow is governed by `swarm_state.json`.

### Hard Locks (No “soft rules”)
Before executing any agent, the Orchestrator (OpenClaw/Danny AI) MUST run:
- `python3 swarm/validate_state.py --role <role>` (hard stop on mismatch)

After the agent produced changes, the Orchestrator MUST run:
- `python3 swarm/policy_guard.py --role <role>` (separation of concerns)
- `python3 swarm/no_mocks_guard.py` (no mocks in tests)
- `python3 swarm/no_placeholders_guard.py` (no TODO/FIXME/placeholders in prod paths)

Evidence MUST be captured from real command execution:
- `python3 swarm/capture_test_output.py ...` writes append-only `tasks/logs/CI_LOGS.md` + stores raw output in `tasks/evidence/**`.

State transitions MUST be applied only via:
- `python3 swarm/transition_state.py ...`

### Canonical Phase Order (Non-Skippable)
1. `ARCHITECT`
2. `QA_CONTRACT` (contract/TDD tests before code)
3. `BACKEND`
4. `ANALYST_CI_GATE` (reads evidence, triggers Fix Loop)
5. `FRONTEND`
6. `QA_E2E` (real E2E on a running system)
7. `ANALYST_FINAL` (final acceptance)

**Fix Loop:** Any FAIL routes to Analyst feedback (`tasks/feedback/**`) and returns work to the responsible dev phase until gates pass.

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
