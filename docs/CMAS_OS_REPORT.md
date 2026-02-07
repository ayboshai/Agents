# CMAS-OS Report: Reliable, Non-Bypassable Swarm Execution

## Purpose
This report consolidates:
- your follow-up correspondence (primary source),
- the second analyst's specification (secondary input),
and produces a single recommended approach that maximizes **reliability**, **non-bypassability**, and **objective quality gates** across heterogeneous projects (web apps, trading bots, etc.).

This document is written to be dropped into the repo as an implementation blueprint and audit checklist.

---

## 0) Mandatory Dynamic Context Loading (Project-Dependent Truth)

### 0.1 Read Order (Hard Requirement for Every Agent, Every Phase)
Before doing any work (including “small fixes”), the acting role MUST read and treat as binding:
1. `config/personas/<role>.md` (static role persona)
2. `TASKS_CONTEXT.md` (dynamic project contract: stack + constraints + quality targets)
3. Task spec: `tasks/queue/**` (or `swarm_state.json.task_path`)
4. Contracts/specs: `docs/**` referenced by the task (at minimum `docs/api_spec.md` if present)
5. Workflow law: `SWARM_CONSTITUTION.md` (or the canonical constitution file)
6. State machine: `swarm_state.json` (must match the acting role via `next_phase`)
7. Latest open feedback (if any): `tasks/feedback/<task_id>/**`

If any required file is missing, the agent MUST stop and request/create it only if that role is responsible for it per `swarm_state.json`.

### 0.2 How `TASKS_CONTEXT.md` Controls Technology and Quality Criteria
`TASKS_CONTEXT.md` is the only dynamic source-of-truth for:
- tech stack and allowed libraries,
- domain constraints (finance/SEO/security/latency),
- acceptance targets (performance, a11y, determinism),
- testing posture (integration/E2E requirements).

Static personas provide universal behavior (“senior quality bar”), but MUST adapt decisions to `TASKS_CONTEXT.md`.
Example: “Finance/HFT” implies Decimal, concurrency paranoia, testnet/sandbox integration; “Marketing site” implies SEO metadata, a11y, performance budgets.

---

## 1) What Your Correspondence Established (Non-Negotiables)

1. **Analyst as quality gate is mandatory.**
   - On every CI FAIL: Analyst reads authoritative CI evidence and writes actionable feedback.
   - Dev fixes and re-commits; loop repeats until Analyst allows progression.
2. **QA must be split into two non-skippable phases:**
   - QA(Contract/TDD) runs BEFORE Dev and writes the “contract in code” (tests).
   - QA(E2E) runs AFTER Frontend and verifies full user journey against a real running system.
3. **Fix Loop is mandatory** and must be driven by CI failures (not by “belief”).
4. **Universal personas alone are insufficient**; the correct model is:
   - static personas + dynamic per-project context (`TASKS_CONTEXT.md` / `TECH_STACK.md`).
5. **Soft rules are not enough**: markdown rules can be ignored.
   - This directly caused the protocol violation you observed (skipping QA/Analyst).
6. **The “CI_LOGS.md forgery incident” is a design bug.**
   - If an agent can write “SUCCESS” into a file and the Analyst trusts it, then PASS/FAIL is forgeable.
   - Therefore PASS/FAIL cannot be derived from in-repo markdown alone.
7. **The “Ideal Code” algorithm must be enforced**: production code (no placeholders), refactor, remove AI-slop, deep tests, LARP-audit, prod checklist, final audit, then “fix everything remaining”.

---

## 2) Second Analyst Spec: What’s Strong vs What Must Be Changed

### 2.1 Strong / Keep
- Clear violation taxonomy (V01..V12) and explicit invariants.
- Explicit must/must-not/should sets.
- Hybrid approach (static personas + `TASKS_CONTEXT.md` injection).
- State machine as law (`swarm_state.json`) + guard script concept.
- Explicit conflict resolution for “never try/catch” vs “handle errors”.
- Fix Loop protocol defined as a first-class workflow.

### 2.2 Weak / Risky / Must Change
1. **Treating `tasks/logs/CI_LOGS.md` as authoritative.**
   - If the file is editable via normal commits, an agent can forge it.
   - Even if “policy forbids edits”, enforcement must be programmatic and non-bypassable (CI + branch protection).
2. **Approvals stored as editable JSON without cryptographic/CI provenance.**
   - “Approval in `swarm_state.json`” is forgeable unless the file is only mutated by CI under strict protection.
3. **Allowing any actor to update `swarm_state.json` freely.**
   - State transitions must be validated by CI; mutations must be restricted by phase policy.
4. **Workflow reliance on “manual review”.**
   - Manual review is not a hard lock; it’s advisory unless enforced by branch protection and required checks.

---

## 3) Root Cause of the Protocol Violation You Highlighted

Why an agent could skip QA/Analyst and still claim completion:
- The protocol existed as text, not as an execution barrier.
- PASS/FAIL was inferred from a mutable file (`CI_LOGS.md`), not from CI status checks/attestations.
- There was no non-bypassable rule that blocks progression/merge when gates are missing.

Corrective action is not “be more careful”; it is converting the workflow into **enforced invariants**:
- state-guard (phase enforcement),
- policy-guard (who may change what),
- CI as the only PASS/FAIL source,
- protected approvals and required checks.

---

## 4) Recommended Best Approach (High Quality + Non-Bypassable)

### 4.1 Canonical Phase Order (Must Not Change)
`ARCHITECT → QA(Contract/TDD) → BACKEND → ANALYST(CI gate) → FRONTEND → QA(E2E) → ANALYST(Final acceptance)`

QA is never skippable (especially E2E).

### 4.2 Single Source of Truth for PASS/FAIL (Anti-Forgery)
PASS/FAIL MUST be derived only from:
- GitHub Actions required status checks, and
- a CI-generated attestation artifact (e.g. `swarm-ci-attestation.json`) uploaded as an artifact (not hand-authored).

`tasks/logs/**` MAY exist for convenience, but MUST be treated as non-authoritative.

### 4.3 Minimal “Necessary and Sufficient” Hard Locks
The smallest set of programmatic safeguards that blocks the known failure modes:
1. **State Guard (CI + orchestrator):**
   - Validate `swarm_state.json` schema and legal transitions.
   - Hard-fail if acting role != `next_phase`.
   - Hard-fail if a transition skips mandatory phases (QA/E2E).
2. **Policy Guard (CI):**
   - Enforce allowed file-change surface per phase:
     - QA phases can change `tests/**` but not production code.
     - Dev phases can change production code but cannot change QA-owned tests.
     - Analyst can only write feedback/reports, not change production logic or tests.
     - Architect owns CI/workflows, constitution, and schemas.
3. **No-Mocks Guard (CI):**
   - Fail if mocking APIs are used in tests that would hide broken logic (`vi.mock`, `jest.mock`, patching core modules, etc.).
4. **No-Placeholders Guard (CI):**
   - Fail on `TODO|FIXME|placeholder|stub|not implemented` in production paths at merge time.
5. **Mandatory E2E Gate (CI required check):**
   - Playwright (or equivalent) MUST run against a real server/build.
6. **Approval non-forgeability:**
   - “Approved” must be verifiable as:
     - required checks green, and
     - protected review/environment approval (Analyst), and
     - CI attestation artifact referencing the exact commit SHA and run id.

### 4.4 Prompt-Optimizer vs Swarm Engine (Boundary)
- `prompt-optimizer` is a skill to generate high-quality prompts/personas/tasks.
- `codex-swarm-engine` (CMAS-OS) is a workflow system that enforces:
  - phase order, gates, evidence, approvals, and fix loops.

---

## 5) “Ideal Code” Algorithm (Enforced Checklist for Every Dev/QA Phase)

This must be present in the canonical constitution and referenced by personas.
It is not optional and cannot be skipped.

1. **Write real production code.**
   - No stubs, placeholders, fake success paths.
   - Handle errors and edge cases as you implement.
   - Use try/catch or other “protective patterns” only when necessary (see conflict rules below).
   - If stuck or the plan is invalid, STOP and escalate to Architect/Analyst instead of guessing.
   - End the phase with: (a) a concise outcome summary; (b) a list of what is still blocked.
2. **Code quality refactor pass.**
   - Compactness: remove duplication and excess code.
   - Idiomatic logic: simplify control flow.
   - Cleanliness: consistent naming and structure.
   - Reliability: boundary conditions, performance, determinism.
3. **Remove AI-slop.**
   - Remove over-engineering, useless abstractions, verbose comments,
     impossible-case “defensive” code, enterprise patterns in small modules.
4. **Deep testing beyond happy path.**
   - Boundaries, invalid inputs, error paths.
   - Real integrations (no mocks of logic).
   - Concurrency/async races where applicable.
5. **LARP evaluation.**
   - Detect: fake returns, hardcode pretending to be dynamic, swallowed errors,
     async without await, “validation” that validates nothing, untested paths.
   - Immediately fix all issues found; maintain a TODO list until empty.
6. **Production readiness checklist.**
   - All tests pass in real execution (CI).
   - Errors are handled and logged (not swallowed).
   - Config externalized; no secrets in repo.
   - Perf sanity check, dependencies pinned, rollback plan, monitoring/alerts plan.
   - Each item must be confirmed by evidence or a tracked task.
7. **Final audit of the last task.**
   - Does it solve the original problem fully?
   - What was skipped/assumed?
   - What can break in production?
   - Create TODOs for all gaps and immediately fix them.

Finally: **Fix everything remaining**:
- list open questions/bugs/TODOs,
- prioritize,
- fix one-by-one fully,
- validate each fix by real execution,
- rerun full test suite after changes,
- do not claim completion until no problems remain.

---

## 6) Conflict Resolution Rules (Example: try/catch vs error handling)

### 6.1 Forbidden
- Empty catches (`catch {}` / `except: pass`) and any swallowing of errors.
- “Try/catch everywhere” as superstition.

### 6.2 Allowed (Necessity Test)
Try/catch is allowed only if it satisfies all:
1. Necessity: you must add context, map error domains, ensure cleanup, or produce a deterministic error contract.
2. Evidence: the error path is tested (integration/E2E) and observable.
3. Non-swallowing: you either (a) handle and return a correct error contract, or (b) rethrow after logging/context.

---

## 7) Implementation Blueprint (Repo + CI)

### 7.1 Repository Contract (Minimum)
Required:
- `SWARM_CONSTITUTION.md` (canonical law)
- `TASKS_CONTEXT.md`
- `swarm_state.json`
- `config/personas/*.md`
- `tasks/queue/`, `tasks/feedback/`, `tasks/reports/`
- `docs/` (contracts)

Recommended:
- `swarm/` with guard scripts:
  - `swarm/validate_state.py`
  - `swarm/policy_guard.py`
  - `swarm/no_mocks_guard.py`
  - `swarm/no_placeholders_guard.py`
  - `swarm/ci_attest.py`
- `.github/workflows/ci.yml` with required checks
- `.github/CODEOWNERS` enforcing separation of concerns

### 7.2 Approval Protocol (Non-Forgeable)
Define “Approved” as the conjunction:
- required CI checks are green for the merge commit/PR head SHA,
- Analyst-protected approval exists (CODEOWNERS review and/or GitHub environment approval),
- CI attestation artifact exists for that run and matches SHA.

Do NOT use “Approved” text in markdown as proof.

---

## 8) Validation Checklist (New Context Window)
Use this at the start of every new session:
1. Confirm canonical law exists: `SWARM_CONSTITUTION.md`.
2. Load `TASKS_CONTEXT.md` and restate: stack + critical constraints + gates.
3. Read `swarm_state.json` and confirm: your role == `next_phase`.
4. Confirm QA non-skippable: both QA phases are present in the legal transition table.
5. Confirm CI is authoritative:
   - required checks exist in `.github/workflows/ci.yml`,
   - branch protection requires them (out of band GitHub setting),
   - CI attestation exists for latest run.
6. Confirm anti-deception guards exist and are required:
   - no-mocks guard
   - no-placeholders guard
7. Confirm there are no open feedback items for the current `task_id`.
8. Confirm completion is forbidden unless:
   - all required checks green including E2E,
   - no TODO/FIXME in production paths,
   - Analyst final acceptance conditions are satisfied.

---

## 9) Practical Recommendation Summary
Best-quality approach is a **hybrid**:
- keep the second analyst’s strict taxonomy and state machine philosophy,
- adopt a stronger anti-forgery model:
  - CI status checks + CI attestation are the only PASS/FAIL authority,
  - repo logs are non-authoritative,
  - approvals cannot be authored by the same actor and must be protected/CI-verifiable,
- enforce separation of concerns via policy guard + CODEOWNERS + branch protection,
- treat QA (Contract + E2E) as non-skippable phases.

