# TASKS_CONTEXT

## Project Type
SwarmOS mini-cycle validation: prove that the L2 pipeline (state machine + CI required checks + merge gate) works end-to-end on a real PR.

## Stack
- Language: Node.js (JS/TS) + Python 3.11 (guards)
- Framework: none (minimal HTTP server for E2E)
- Storage: none
- Testing: Vitest
- E2E: Playwright (Chromium)

## Critical Constraints
1. **Mandatory E2E:** the `tests/e2e` suite MUST exist and run in CI.
2. **No mocks for internal logic:** test real code paths; do not replace the system-under-test with mocks.
3. **No stubs/placeholders:** production paths must be fully implemented.
4. **Evidence-based gates:** PASS/FAIL comes from CI required checks (L2) or captured stdout/stderr (L1).
5. **L2-first:** no direct pushes to `main`; merge only via PR after required checks are green.

## Non-Functional Targets
- Reliability: CI must be deterministic; no flaky tests.
- Security: no secrets in repo; tokens/keys only via environment.
- Performance: CI should complete within ~5 minutes for this repo.
