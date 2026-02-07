# Constitutional Multi-Agent Swarm OS (CMAS-OS)

This document is the **single source of truth** for how the swarm operates and how violations are prevented.

## 0) Dynamic Context Protocol (MANDATORY)

### 0.1 What Every Agent MUST Read (in this exact order)
Before doing **any** work (including "quick fixes"), an agent MUST load and treat as binding:
1. `config/personas/<role>.md` (static persona prompt for the role that is about to act).
2. `TASKS_CONTEXT.md` (dynamic project rules and the quality contract).
3. `docs/api_spec.md` and other `docs/**` referenced by the current task (contracts/specs).
4. `swarm_state.json` (state machine: `current_phase`, `next_phase`, evidence pointers).
5. The current task file in `tasks/queue/**` (or the explicitly referenced task path in `swarm_state.json`).
6. The newest feedback file for the task (if any) in `tasks/feedback/**`.

If any required file is missing or unreadable, the agent MUST stop and request the missing artifact (or create it only if their role is responsible for it by the state machine).

### 0.2 How `TASKS_CONTEXT.md` Controls Tech Choices and Quality Criteria
`TASKS_CONTEXT.md` is the **dynamic constraint set**. Agents MUST:
- Treat the declared stack and constraints as **hard requirements** (e.g., framework, language, testing tools).
- Prefer solutions that minimize dependencies and operational risk **within** that stack.
- Reject or flag any change that violates:
  - **Critical Constraints**
  - **Non-Functional Targets**
  - **Testing & Reliability rules** (especially "NO MOCKS" and "MANDATORY E2E")
- When there is a conflict between a task instruction and `TASKS_CONTEXT.md`, the conflict MUST be resolved by:
  1. Following this constitution (highest priority).
  2. Following `TASKS_CONTEXT.md` constraints.
  3. Escalating to the **Architect** phase to update specs/contracts (never "just do it").

### 0.3 Context Digest (Anti-Hallucination Requirement)
Each phase MUST produce a short "Context Digest" section in its phase report (see `tasks/reports/**` format below):
- The exact constraints from `TASKS_CONTEXT.md` that affect the phase.
- The exact acceptance criteria used for gates.
- The exact commands/checks whose results are used as evidence (CI run IDs, artifact names).

No phase may claim completion without referencing evidence that is verifiable by CI.

### 0.4 Enforcement Levels (Reality vs Target)
This constitution defines two enforcement levels:

1. **Level 1 (L1) Soft Enforcement (Current Reality):** OpenClaw/Danny AI orchestrates work without GitHub Actions.
   - Hard locks are implemented via local guard scripts with non-zero exit codes.
   - Evidence is captured from **real command execution stdout/stderr** and stored immutably in `tasks/evidence/**`.
   - `tasks/logs/CI_LOGS.md` is **append-only** and must be written only by the capture script.
   - This reduces “soft rule” violations, but is not as tamper-proof as Level 2.
2. **Level 2 (L2) Hard Enforcement (Target):** GitHub Actions + Branch Protection + CODEOWNERS.
   - Required checks + CI attestation artifact are the only authoritative PASS/FAIL.
   - Merges to `main` are blocked unless all gates pass.

If L2 is not enabled, L1 MUST be enabled. If neither can run, the system MUST STOP.

---

# A) Threat Model

## A.1 Threat Classes (What Can Go Wrong)
1. **Phase Skipping:** jumping over required roles (especially QA and Analyst) by editing state or "just doing the work".
2. **Role Substitution:** a non-authorized role authoring or approving artifacts (e.g., Dev writing QA approval, QA approving final).
3. **Evidence Forgery:** faking "PASS" by:
   - editing `tasks/logs/**` manually,
   - writing "SUCCESS" text into files,
   - claiming tests ran without CI proof.
4. **Test Deception:** making tests pass without verifying reality via:
   - mocks/stubs of the logic under test,
   - skipped tests, `|| true`, "allow failures",
   - nondeterministic tests that pass by luck.
5. **Implementation Deception (LARP):** shipping:
   - placeholders, stubs, TODOs in production code,
   - fake handlers (`console.log` instead of real behavior),
   - swallowed errors (`catch {}`) that hide failures.
6. **CI Tampering:** disabling gates by:
   - modifying workflows to bypass checks,
   - changing scripts to always exit 0,
   - narrowing CI scope so critical tests do not run.
7. **Approval Forgery:** writing "Approved" without:
   - required CI checks,
   - required review/role sign-off,
   - final evidence and attestation.
8. **Config/Environment Drift:** code "works locally" but fails in CI/staging due to ports, base URLs, secrets, missing build steps.

## A.2 Always-True Invariants (MUST Hold at All Times)
I1. **No phase progression without gates:** `swarm_state.json.next_phase` MUST match the acting role's phase and MUST be validated by a guard (local + CI).
I2. **QA is non-skippable:** both QA phases MUST occur for every task:
   - QA(Contract/TDD) MUST exist and be referenced by evidence.
   - QA(E2E) MUST exist and be referenced by evidence.
I3. **CI is the only source of PASS/FAIL:** human-written files are never authoritative for pass/fail.
I4. **No fake approvals:** "Approved" exists only as a CI-validated attestation (and, where applicable, protected GitHub review/environment approval).
I5. **No mocks of the system under test:** tests MUST exercise real code paths (integration/E2E); mocking internal logic is forbidden.
I6. **No placeholders in production code:** no TODO/FIXME/placeholder/stub behavior in production paths at merge time.
I7. **Main branch stays green:** `main` MUST never contain a commit that fails required checks.
I8. **Fix Loop is mandatory:** any failure MUST produce Analyst feedback, and work MUST iterate until gates pass.

---

# B) Swarm Constitution (Rules)

## B.0 Rule Priority & Conflict Resolution
Rules are evaluated in priority order:
1. **P0 Integrity & Gates:** source of truth, state machine, approvals, CI enforcement.
2. **P1 Correctness & Security:** correct behavior, error handling, input validation, no LARP.
3. **P2 Reliability & Test Quality:** deterministic tests, real integration, E2E coverage, reproducible builds.
4. **P3 Maintainability:** refactors, simplicity, readability, minimal deps.
5. **P4 Speed/Convenience:** anything that optimizes time but never at the expense of P0-P3.

If two rules conflict:
- The higher priority wins.
- The conflict MUST be documented in the phase report with:
  - the exact rules in conflict,
  - the chosen resolution,
  - why it is **necessary** (see B.7).

## B.1 Source of Truth (P0)
1. MUST treat PASS/FAIL as authoritative evidence only from:
   - **L2:** GitHub Actions required status checks + uploaded CI artifacts/attestations.
   - **L1:** captured raw stdout/stderr from real execution stored in `tasks/evidence/**` and referenced by hash (see C.5).
2. MUST NOT treat free-form text (“SUCCESS”, “APPROVED”) in markdown as proof.
3. MUST NOT claim "tests passed" unless referencing:
   - **L2:** CI run id + required check names/conclusions.
   - **L1:** captured evidence run id + exit code + sha256 of raw output.

## B.2 State Machine Enforcement (P0)
1. MUST keep `swarm_state.json` as the canonical workflow state.
2. MUST NOT execute a role unless `swarm_state.json.next_phase` equals that role's phase.
3. MUST validate `swarm_state.json`:
   - **L1:** before every agent invocation (orchestrator hard stop).
   - **L2:** in CI on every PR and on `main`.
4. MUST record phase transitions as explicit events with evidence pointers:
   - **L2:** CI run IDs + artifact names.
   - **L1:** evidence file paths + sha256 hashes.

## B.3 Phase Non-Skippability (P0)
1. MUST execute phases in this order (no skipping):
   - `ARCHITECT`
   - `QA_CONTRACT`
   - `BACKEND`
   - `ANALYST_CI_GATE`
   - `FRONTEND`
   - `QA_E2E`
   - `ANALYST_FINAL`
2. MUST NOT change `next_phase` to a later phase unless all preceding phases have gate evidence recorded.
3. MUST NOT merge to `main` unless `swarm_state.json` indicates that the merge is allowed for the current task and that required gates passed.

## B.4 Test Policy: Real Integration (P0/P2)
1. MUST write tests that exercise real code paths.
2. MUST NOT use mocking frameworks for internal logic (examples, non-exhaustive):
   - `vi.mock`, `jest.mock`, `sinon`, `testdouble`, `mockImplementation`, module-level monkeypatching.
3. MUST NOT skip tests (`test.skip`, `describe.skip`) on `main`.
4. SHOULD prefer:
   - "start the real server and test through HTTP" for backend,
   - "Playwright against a real built app/server" for user journeys.
5. If external dependencies exist (DB, queue, SMTP), MUST use real local equivalents (containers or sandboxes), not mocks.

## B.5 No Placeholders / No AI-Slop (P1/P3)
1. MUST NOT ship placeholder behavior in production code:
   - `TODO`, `FIXME`, `stub`, `placeholder`, "not implemented",
   - `console.log` as a "submission" or "processing" substitute,
   - handlers that accept data but do nothing while claiming success.
2. MUST remove AI-slop before phase completion:
   - generic wrappers, needless abstractions, verbose comments,
   - "manager" classes without real value,
   - dead code and unused exports.

## B.6 Fix Loop (P0)
1. If CI fails, the **Analyst** MUST create a concrete feedback artifact with:
   - failing checks,
   - failing tests,
   - exact files/components suspected,
   - required changes,
   - exit criteria (what must be green).
2. The responsible Dev role (Backend or Frontend) MUST fix and push a new commit.
3. Repeat until CI is green and Analyst approves the gate.

## B.7 Necessity Criteria for Exceptions (P0)
The only allowed "exception" is when strictly necessary to satisfy P0/P1.
An exception MUST satisfy:
1. **Necessity:** no alternative exists that keeps all higher-priority rules.
2. **Minimality:** smallest scope change to resolve the issue.
3. **Evidence:** demonstrated by CI/run logs/measurements.
4. **Reversal:** plan to remove exception (if temporary) with a deadline and a gate.

## B.8 Approval Rules (P0)
1. "Approved" MUST be representable as a verifiable record:
   - required CI checks green, and
   - Analyst sign-off as a protected approval (review/environment), and/or
   - a CI-generated attestation artifact.
2. MUST NOT accept approval text in PR descriptions, markdown files, or commit messages as proof.

## B.9 The "Ideal Code" Algorithm (P1/P2/P3)
Every Dev/QA phase MUST run this 7-step internal checklist before declaring the phase "ready for gate":
1. **Production code, no stubs:** replace placeholder logic with real behavior; handle edge cases.
2. **Refactor for quality:** simplify, remove duplication, consistent patterns.
3. **Delete AI-mess:** remove slop, pointless layers, verbose comments, dead code.
4. **Deep tests:** cover unhappy paths, validation, boundary conditions, race/ordering risks.
5. **LARP audit:** actively search for fake success paths, swallowed errors, "always true" validation.
6. **Prod checklist:** config externalized, secrets safe, perf sanity, deterministic behavior.
7. **Final audit pass:** review the last task end-to-end and fix everything still broken.

---

# C) Enforcement Mechanisms (Hard Locks)

## C.1 Repository Structure (Required)
The repository MUST contain these artifacts (paths are normative; exact names may be extended but not removed):
- `SWARM_CONSTITUTION.md` (this file)
- `TASKS_CONTEXT.md` (dynamic constraints and stack)
- `swarm_state.json` (state machine)
- `config/personas/*.md` (static persona prompts; one per role)
- `tasks/queue/` (task inputs)
- `tasks/feedback/` (Analyst fix requests; immutable records)
- `tasks/reports/<task_id>/` (phase reports; one per phase)
- `docs/` (contracts/specs referenced by tasks)

## C.2 Enforcement Gates (L1 + L2)
### C.2.1 Level 1 (L1) Required Guards (No GitHub Actions)
When GitHub Actions is not enabled, the orchestrator (OpenClaw/Danny AI) MUST implement hard locks by running:

**Before invoking any agent (pre-action hard stop):**
- `python3 swarm/validate_state.py --role <role>`

**After the agent produced changes (separation-of-concerns):**
- `python3 swarm/policy_guard.py --role <role>`
- `python3 swarm/no_mocks_guard.py` (tests must not contain mocks)
- `python3 swarm/no_placeholders_guard.py` (no TODO/FIXME/placeholders in prod paths)

**Evidence capture (the only way to write logs):**
- Run real tests (per `TASKS_CONTEXT.md`) and capture stdout/stderr to a file.
- `python3 swarm/capture_test_output.py --input <file> --command "<cmd>" --exit-code <code> ...`

**State transition (the only way to update swarm_state.json):**
- `python3 swarm/transition_state.py --role <role> --to <NEXT_PHASE> --evidence <file> --note "<reason>"`

If any guard exits non-zero, the orchestrator MUST STOP and must not proceed to the next phase.

### C.2.2 Level 2 (L2) GitHub Actions Gates (Hard Enforcement Target)
CI MUST run on every PR and on `main` with required status checks (names are examples but MUST be fixed and protected):
1. `swarm/state-guard`:
   - validates `swarm_state.json` schema,
   - validates that transitions do not skip phases,
   - validates that required phase artifacts exist.
2. `swarm/policy-guard`:
   - enforces path-level rules per phase (who can change what),
   - blocks edits to CI/gates by non-Architect phases.
3. `quality/static`:
   - lint + typecheck + formatting checks.
4. `quality/no-mocks`:
   - fails if forbidden mocking patterns exist in tests.
5. `tests/unit-integration`:
   - runs the real unit/integration suite.
6. `tests/e2e`:
   - starts the real app/server and runs Playwright E2E.
7. `attest/ci-summary`:
   - uploads `swarm-ci-attestation.json` as an artifact containing:
     - commit SHA, run ID, required check conclusions, environment info.

Branch protection MUST require all of the above checks to pass before merging to `main`.

## C.3 Commit/PR Policy (Anti-Forgery)
1. MUST disallow direct pushes to `main` (protected branch).
2. MUST require PRs with:
   - a `task_id`,
   - the phase being executed,
   - a link/reference to CI evidence (run ID).
3. MUST protect critical files with CODEOWNERS (examples):
   - `.github/workflows/**` -> Architect/DevOps owners only
   - `swarm_state.json`, `SWARM_CONSTITUTION.md` -> Architect owners only
   - `tests/**` -> QA owners required review
4. MUST block PRs that attempt to "approve themselves" by editing approval/log files (policy guard).

## C.4 State Validator / Guard (Hard Block Before Work)
A guard script MUST exist and be used in two places:
1. **Orchestrator hard lock:** before any agent is invoked, the orchestrator MUST run:
   - `guard(role, swarm_state.json)` and abort if mismatch.
2. **CI hard lock (L2):** `swarm/state-guard` job MUST run the same validation and fail if invalid.

Local git hooks (pre-commit/pre-push) SHOULD run the guard for ergonomics, but:
- In **L1** the orchestrator is the hard stop.
- In **L2** CI + branch protection is the non-bypassable gate.

## C.5 Logs and Evidence (Anti "I wrote SUCCESS")
1. Evidence MUST be sourced from:
   - **L2 (preferred):** GitHub Actions run logs + uploaded artifacts (attestation).
   - **L1:** captured raw stdout/stderr from real command execution via `swarm/capture_test_output.py`.
2. In **L1**, the orchestrator MUST:
   - run tests via a real shell command,
   - capture raw output to an evidence file,
   - call `swarm/capture_test_output.py` to append a timestamped block to `tasks/logs/CI_LOGS.md`,
   - store raw output immutably in `tasks/evidence/**` and reference it by sha256.
3. Agents MUST NOT edit `tasks/logs/CI_LOGS.md` directly. Any manual edit is invalid evidence.
4. The Analyst MUST reference evidence, not claims:
   - **L2:** run id + required check conclusions + attestation artifact name.
   - **L1:** run id + exit code + sha256 + evidence path.

## C.6 Approval Protocol (Non-Forgeable)
"Approved" MUST mean:
1. The PR was merged to `main` with all required checks green, AND
2. The final Analyst sign-off exists as a protected action:
   - required GitHub review from an Analyst-owned CODEOWNERS path, and/or
   - GitHub Environment approval, and/or
   - CI-generated attestation artifact signed/identified by the workflow run.

No markdown file stating "APPROVED" is sufficient.

## C.7 Migration Plan (L1 -> L2)
This is the required, non-optional sequence to eliminate the enforcement gap:

1. **Enable L1 everywhere (immediate).**
   - Orchestrator MUST run `swarm/validate_state.py` before every agent.
   - Orchestrator MUST run `swarm/policy_guard.py`, `swarm/no_mocks_guard.py`, `swarm/no_placeholders_guard.py` after changes.
   - Evidence MUST be captured via `swarm/capture_test_output.py`.
   - State MUST be updated only via `swarm/transition_state.py`.
2. **Add L2 CI workflows (repo).**
   - Add `.github/workflows/ci.yml` with required checks mirroring L1 guards.
   - Add `.github/CODEOWNERS` to enforce separation-of-concerns in reviews.
3. **Turn on GitHub Branch Protection (repo settings).**
   - Require all checks, forbid direct pushes, require PRs.
4. **Enable protected approvals (Analyst).**
   - Require Analyst review and/or GitHub Environment approval for final sign-off.
5. **Switch source of truth to L2.**
   - Treat CI status checks + attestation artifacts as the only PASS/FAIL.
   - Keep L1 scripts as local preflight, but never as final authority.

---

# D) Execution Protocol as a Finite State Machine

## D.1 Phases (Canonical Order)
1. `ARCHITECT`
2. `QA_CONTRACT` (TDD contract tests)
3. `BACKEND`
4. `ANALYST_CI_GATE`
5. `FRONTEND`
6. `QA_E2E`
7. `ANALYST_FINAL`

## D.2 Events
- `E_CI_RED` (CI executed and failed; evidence recorded)
- `E_CI_GREEN` (CI executed and passed; evidence recorded)
- `E_FEEDBACK_CREATED` (Analyst feedback file created with required fields)
- `E_FIX_COMMITTED` (Dev commit references feedback ID)
- `E_PHASE_ACCEPTED` (phase report exists + gates satisfied)
- `E_FINAL_APPROVED` (final approval conditions satisfied)

## D.3 Transitions (With Conditions and Artifacts)

### Phase 1: ARCHITECT -> QA_CONTRACT
Entry conditions:
- `swarm_state.json.next_phase == ARCHITECT`
Required outputs:
- `docs/<task_id>/architecture.md`
- `docs/<task_id>/contracts.md` (or updates to `docs/api_spec.md`)
- `tasks/reports/<task_id>/ARCHITECT.md` (with Context Digest)
Gate to advance:
- `swarm/state-guard` passes.
Transition:
- set `next_phase = QA_CONTRACT`.

### Phase 2: QA_CONTRACT -> BACKEND
Entry conditions:
- `next_phase == QA_CONTRACT`
Required outputs:
- `tests/**` additions defining contracts (no mocks; real execution paths)
- `tasks/reports/<task_id>/QA_CONTRACT.md`
Gate to advance:
- CI MUST run and produce evidence:
  - `E_CI_RED` is acceptable here (red phase proof),
  - but tests MUST be runnable and deterministic (no skips).
Transition:
- set `next_phase = BACKEND`.

### Phase 3: BACKEND -> ANALYST_CI_GATE
Entry conditions:
- `next_phase == BACKEND`
Required outputs:
- production code implementing contracts (no placeholders)
- `tasks/reports/<task_id>/BACKEND.md`
Gate to advance:
- CI MUST be green for required checks (`E_CI_GREEN`).
Transition:
- set `next_phase = ANALYST_CI_GATE`.

### Phase 4: ANALYST_CI_GATE -> FRONTEND (PASS) or BACKEND (FAIL)
Entry conditions:
- `next_phase == ANALYST_CI_GATE`
Required outputs:
- If FAIL: `tasks/feedback/<task_id>/fix_required.md` (see template) and `E_FEEDBACK_CREATED`
- If PASS: `tasks/reports/<task_id>/ANALYST_CI_GATE.md` with evidence references
Decision:
- If any required check is not green -> FAIL path:
  - transition to `next_phase = BACKEND`
  - fix loop starts
- If all required checks green -> PASS path:
  - transition to `next_phase = FRONTEND`

### Phase 5: FRONTEND -> QA_E2E
Entry conditions:
- `next_phase == FRONTEND`
Required outputs:
- UI integration, a11y baseline, performance constraints respected
- `tasks/reports/<task_id>/FRONTEND.md`
Gate to advance:
- CI green for required checks (including unit/integration).
Transition:
- set `next_phase = QA_E2E`.

### Phase 6: QA_E2E -> ANALYST_FINAL
Entry conditions:
- `next_phase == QA_E2E`
Required outputs:
- Playwright E2E tests (real server, no mocks)
- `tasks/reports/<task_id>/QA_E2E.md` with E2E scope and evidence pointers
Gate to advance:
- `tests/e2e` check MUST be green (`E_CI_GREEN` for E2E job).
Transition:
- set `next_phase = ANALYST_FINAL`.

### Phase 7: ANALYST_FINAL -> DONE (APPROVED) or FIX LOOP
Entry conditions:
- `next_phase == ANALYST_FINAL`
Required outputs:
- Final acceptance report `tasks/reports/<task_id>/ANALYST_FINAL.md`
Decision:
- If any required check is not green OR any invariant is violated -> create feedback and transition back:
  - to `FRONTEND` (UI/E2E issues) or
  - to `BACKEND` (API/validation/data issues)
- If all invariants hold and evidence is present -> `E_FINAL_APPROVED`:
  - mark task as Approved in a non-forgeable way (see C.6).

---

# E) Minimal Artifact Templates

## E.1 Example `swarm_state.json`
```json
{
  "schema_version": "1.0",
  "task_id": "TASK-2026-02-07-001",
  "task_path": "tasks/queue/01-architect-task.md",
  "current_phase": "FRONTEND",
  "next_phase": "QA_E2E",
  "is_locked": false,
  "phase_history": [
    {
      "phase": "ARCHITECT",
      "report_path": "tasks/reports/TASK-2026-02-07-001/ARCHITECT.md",
      "ci": { "run_id": 1234567890, "conclusion": "success" }
    },
    {
      "phase": "QA_CONTRACT",
      "report_path": "tasks/reports/TASK-2026-02-07-001/QA_CONTRACT.md",
      "ci": { "run_id": 1234567891, "conclusion": "failure", "note": "expected red phase" }
    },
    {
      "phase": "BACKEND",
      "report_path": "tasks/reports/TASK-2026-02-07-001/BACKEND.md",
      "ci": { "run_id": 1234567892, "conclusion": "success" }
    },
    {
      "phase": "ANALYST_CI_GATE",
      "report_path": "tasks/reports/TASK-2026-02-07-001/ANALYST_CI_GATE.md",
      "ci": { "run_id": 1234567892, "conclusion": "success" }
    }
  ],
  "open_feedback": [
    {
      "feedback_id": "FB-2026-02-07-0003",
      "path": "tasks/feedback/TASK-2026-02-07-001/fix_required.md",
      "status": "closed",
      "closed_by_ci_run_id": 1234567892
    }
  ],
  "required_checks": [
    "swarm/state-guard",
    "swarm/policy-guard",
    "quality/no-mocks",
    "tests/unit-integration",
    "tests/e2e"
  ],
  "final_approval": {
    "status": "pending",
    "evidence": null
  }
}
```

## E.2 Example `SWARM_ARCHITECTURE.md` (Outline + Key Rules)
```md
# Swarm Architecture (CMAS-OS)

## Table of Contents
1. Principles (Non-negotiable)
2. Roles and Phase Order
3. State Machine (`swarm_state.json`)
4. Gates (CI as source of truth)
5. Evidence and Attestations
6. Fix Loop Protocol
7. Repository Structure
8. Anti-Mock / Anti-Placeholder Policy
9. Release and Final Approval

## Key Rules (Extract)
- QA phases are mandatory: Contract + E2E.
- No phase skip: `next_phase` must match role; validated locally and in CI.
- CI is the only PASS/FAIL source; no manual logs are trusted.
- No mocks for internal logic; tests must be integration/E2E-first.
- No placeholders/TODOs in production code at merge time.
```

## E.3 Example Feedback: `tasks/feedback/<task_id>/fix_required.md`
```md
# FIX REQUIRED

## Metadata
- task_id: TASK-2026-02-07-001
- feedback_id: FB-2026-02-07-0004
- phase: ANALYST_CI_GATE
- ci_run_id: 1234567899

## Summary (1-3 sentences)
CI is failing. Required gates are not satisfied. Fixes below are mandatory.

## Evidence (Authoritative)
- required_checks:
  - swarm/state-guard: PASS
  - tests/unit-integration: FAIL
  - tests/e2e: FAIL
- artifacts:
  - swarm-ci-attestation.json (from CI run 1234567899)

## Failures (Exact)
1. `tests/e2e/submission.spec.ts` fails: expected POST `/api/leads` to return 2xx, got 500.
2. `tests/unit/content.test.ts` fails: `whatsappUrl` format mismatch.

## Root Cause Hypotheses (Testable)
- `/api/leads` handler throws on invalid payload parsing (server-side validation mismatch).
- WhatsApp normalization differs from contract (digits extraction).

## Required Fixes (Non-negotiable)
1. Make `/api/leads` return deterministic 2xx on valid payload; 4xx on invalid; never swallow errors.
2. Align WhatsApp URL formatting to contract and update the single source of truth.

## Exit Criteria (Gate Conditions)
- CI run MUST be green for:
  - tests/unit-integration
  - tests/e2e
  - quality/no-mocks
- Provide new CI run ID in the phase report.

## Next Phase After Fix
If green: proceed to `FRONTEND`.
If still red: remain in Fix Loop.
```

## E.4 Example `TASKS_CONTEXT.md` (Template)
```md
# TASKS_CONTEXT

## Project Type
<What is being built and for whom>

## Stack (Hard Requirements)
- Framework:
- Language:
- Runtime:
- Testing:
- E2E:
- Deployment target:

## Critical Constraints (MUST)
1. <constraint>
2. <constraint>

## Quality Gates (MUST be enforced by CI)
- No mocks for internal logic.
- Mandatory E2E on every merge to main.
- No skipped tests on main.
- No TODO/FIXME/placeholders in production code.

## Non-Functional Targets
- Performance budget:
- Accessibility baseline:
- Security baseline:
- Determinism (no random/time-based UI without control):

## Repo Conventions
- Content source of truth:
- Config/secrets policy:
- Allowed dependencies policy:
```

## E.5 Example CI Workflow (Pseudo-YAML With Strict Gates)
```yaml
name: ci
on:
  pull_request:
  push:
    branches: [main]

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

jobs:
  state_guard:
    name: swarm/state-guard
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: python3 swarm/validate_state.py --ci

  policy_guard:
    name: swarm/policy-guard
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: python3 swarm/policy_guard.py --base ${{ github.base_ref }} --head ${{ github.sha }}

  static:
    name: quality/static
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 22, cache: npm }
      - run: npm ci
      - run: npm run lint
      - run: npm run typecheck
      - run: npm run format:check

  no_mocks:
    name: quality/no-mocks
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: python3 swarm/no_mocks_guard.py

  unit_integration:
    name: tests/unit-integration
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 22, cache: npm }
      - run: npm ci
      - run: npm test -- --runInBand

  e2e:
    name: tests/e2e
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 22, cache: npm }
      - run: npm ci
      - run: npx playwright install --with-deps
      - run: npm run test:e2e

  attest:
    name: attest/ci-summary
    runs-on: ubuntu-latest
    needs: [state_guard, policy_guard, static, no_mocks, unit_integration, e2e]
    if: ${{ always() }}
    steps:
      - run: |
          # write swarm-ci-attestation.json with run_id, sha, conclusions from needs.*
          # upload as artifact
```

---

# F) Validation Checklist (New Context Window Survival)

Use this checklist to verify that rules persist and cannot be bypassed:
1. `SWARM_CONSTITUTION.md` exists and is referenced by the orchestrator before any run.
2. Every role run begins by reading (and citing) `TASKS_CONTEXT.md`, `swarm_state.json`, and the current `tasks/queue/**` task.
3. `swarm_state.json.next_phase` is checked before invoking any role; mismatches hard-fail.
4. Branch protection on `main` is enabled:
   - no direct push,
   - required status checks include: `swarm/state-guard`, `swarm/policy-guard`, `quality/no-mocks`, `tests/unit-integration`, `tests/e2e`.
5. `.github/workflows/**` is CODEOWNERS-protected; non-Architect phases cannot change CI to bypass gates.
6. `quality/no-mocks` gate fails if any mocking APIs are used in tests.
7. `tests/e2e` runs against a real server/build; failures block merge.
8. No skipped tests on `main` (`*.skip`, `describe.skip`) and no `|| true` patterns in CI scripts.
9. No placeholders/TODO/FIXME in production code paths at merge time (enforced by CI grep gate).
10. Fix Loop observed:
    - when CI fails, an Analyst feedback artifact exists,
    - Dev commits reference the feedback ID,
    - repeated until CI green and Analyst gate pass.
11. No one claims “готово” unless:
    - all required checks are green,
    - there are no open feedback items in `tasks/feedback/<task_id>/`,
    - there are no open TODOs/known bugs recorded for the task,
    - the final approval record is verifiable (CI attestation + protected approval).
