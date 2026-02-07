# Implementation Report (2026-02-07): Closing the Enforcement Gap (L1 + L2)

## Goal
Implement the third analyst’s critical review recommendations:
- eliminate the “documents assume GitHub Actions, reality is OpenClaw” enforcement gap,
- provide **Level 1 (no GitHub)** hard-stop guards with real evidence capture,
- keep **Level 2 (GitHub Actions)** as the target hard enforcement path,
- ensure the repo ends in a consistent state that can be re-reviewed by an Analyst.

## What Was Implemented

### 1) Level 1 (Current Reality): Programmatic Guards (Exit-code hard locks)
Added `swarm/` guard scripts (stdlib-only Python) that the orchestrator MUST run:
- `swarm/validate_state.py`
  - validates `swarm_state.json` schema, role/phase match, non-skippable required phase order
  - supports legacy phase aliases and collapses sub-phases to canonical stages
  - optional tamper-evidence verification with `SWARM_STATE_HMAC_KEY`
- `swarm/transition_state.py`
  - **the only supported writer** for `swarm_state.json` in normal operation
  - enforces a strict allowed-transition graph (prevents phase skipping)
  - records evidence pointers (path + sha256) when provided
  - optional state signing with `SWARM_STATE_HMAC_KEY`
- `swarm/capture_test_output.py`
  - append-only writer for `tasks/logs/CI_LOGS.md`
  - stores raw stdout/stderr immutably in `tasks/evidence/test-runs/**`
  - optional chained HMAC signing via `SWARM_LOG_HMAC_KEY`
- `swarm/run_and_capture.py`
  - runs a real shell command, captures stdout/stderr, and pipes it through `capture_test_output.py`
- `swarm/policy_guard.py`
  - enforces separation-of-concerns by blocking forbidden file edits (allowlist per role)
  - supports CI diff mode (`--base/--head`) and local working-tree mode
  - blocks agent writes to `swarm_state.json` and `tasks/logs/**` unless `--actor orchestrator`
- `swarm/no_mocks_guard.py`
  - fails if forbidden mock patterns are found in tests (`vi.mock`, `jest.mock`, `patch()`, `MagicMock`, etc.)
- `swarm/no_placeholders_guard.py`
  - fails on `TODO/FIXME/placeholder/stub/not implemented` in production code paths
- `swarm/create_feedback.py`
  - generates an Analyst `fix_required.md` artifact with evidence references and failure snippet
- `swarm/migrate_state.py`
  - one-time migration helper to upgrade legacy `swarm_state.json` to the current schema

### 2) Evidence Layer / Repo Structure (L1)
Created required directories:
- `tasks/reports/.gitkeep`
- `tasks/evidence/test-runs/.gitkeep`

### 3) Constitution Updated for L1 + L2
Updated `SWARM_CONSTITUTION.md` to explicitly define:
- **Level 1** enforcement (OpenClaw orchestrator MUST run scripts and capture evidence)
- **Level 2** enforcement (GitHub Actions + required checks + branch protection)
- updated “Source of Truth” and “Logs & Evidence” sections to support L1 without allowing forgery
- added `C.7 Migration Plan (L1 -> L2)`

### 4) State Machine Normalization
Upgraded `swarm_state.json` to schema `1.0` with:
- `enforcement_level: L1`
- `required_phase_sequence` (canonical 7-phase sequence)
- history migrated to structured entries
- legacy snapshot embedded under `legacy_snapshot.raw`

### 5) Level 2 (Target): GitHub Actions + CODEOWNERS (Repo-side)
Added:
- `.github/workflows/ci.yml` (required checks: state guard, policy guard, no-mocks, no-placeholders, unit/integration, e2e, attestation artifact)
- `.github/CODEOWNERS` (template owners; must be replaced with real GH teams/users)

### 6) Test Tooling Made Runnable (So Gates Are Real)
Fixed the local test interface so CI can run:
- `package.json`
  - added `test` and `test:unit` scripts
  - added dev dependencies: `vitest`, `jsdom`, `@testing-library/react`, `@testing-library/jest-dom`
- `vitest.config.ts`
  - added `setupFiles`
  - restricted include patterns to `tests/unit/**` and excluded `tests/e2e/**`
- `tests/setup.ts`
  - loads jest-dom matchers for Vitest

Note: Playwright browsers are installed via `npx playwright install --with-deps chromium` in CI workflow.

## Files Added / Modified (Audit List)

### Added
- `swarm/validate_state.py`
- `swarm/transition_state.py`
- `swarm/capture_test_output.py`
- `swarm/run_and_capture.py`
- `swarm/policy_guard.py`
- `swarm/no_mocks_guard.py`
- `swarm/no_placeholders_guard.py`
- `swarm/create_feedback.py`
- `swarm/migrate_state.py`
- `swarm/README.md`
- `tests/setup.ts`
- `.github/workflows/ci.yml`
- `.github/CODEOWNERS`
- `tasks/reports/.gitkeep`
- `tasks/evidence/test-runs/.gitkeep`
- `docs/IMPLEMENTATION_REPORT_2026-02-07.md`

### Modified
- `SWARM_CONSTITUTION.md` (L1/L2 enforcement, evidence rules, migration plan)
- `SWARM_ARCHITECTURE.md` (removed placeholder “...”, added guard script references)
- `swarm_state.json` (migrated schema + required sequence)
- `package.json` (test scripts + devDependencies)
- `package-lock.json` (updated by `npm install`)
- `vitest.config.ts` (exclude E2E, add setup)

## How An Analyst Can Re-Review This Implementation
1. Verify state guard works (must be a hard-stop):
   - `python3 swarm/validate_state.py --role analyst`
2. Verify guards run and return non-zero on violations:
   - `python3 swarm/no_mocks_guard.py`
   - `python3 swarm/no_placeholders_guard.py`
3. Verify tests run as real evidence:
   - `npm test`
   - `npx playwright install --with-deps chromium` (if needed locally)
   - `npm run test:e2e`
4. Verify evidence capture path is non-manual:
   - run any command via `python3 swarm/run_and_capture.py --command "<cmd>"`
   - confirm a new immutable raw output exists in `tasks/evidence/test-runs/**`
   - confirm a new block was appended to `tasks/logs/CI_LOGS.md`
5. Verify constitution reflects reality (L1) and target (L2):
   - read `SWARM_CONSTITUTION.md` sections `0.4`, `B.1`, `C.2.*`, `C.5`, `C.7`

