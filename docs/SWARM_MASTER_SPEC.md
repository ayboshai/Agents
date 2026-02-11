# CMAS-OS Master Specification (Autonomous Mode)

## Purpose
Single source of truth for autonomous Swarm operation:
- enforce rules in code (not in prose only),
- route work by lane (`FULL` vs `FAST_UI`),
- require Codex executor attestation,
- auto-stop with blocker snapshots,
- support resumable operation across context windows.

## 1) Hard Locks in Code
Implemented hard locks:
1. `skills/swarm-os/scripts/run.py`
- default `READ_ONLY` unless request starts with `RUN:` / `ВЫПОЛНИ:`
- canonical sync guard (`main` + `pull --ff-only`) before execution
- explicit queue-task requirement in write mode for coding roles
- automatic feature-branch creation (no direct writes to canonical branch)
- autonomous L2 path: push -> PR -> required checks -> merge -> pull
- blocker snapshot creation on failure
2. `swarm/validate_state.py`
- role/phase guard
- skip detection
- lane-aware sequence validation
3. `swarm/transition_state.py`
- only state writer
- lane-aware transition graph
- append-only history + file lock + backup
4. `swarm/state_diff_guard.py`
- validates one legal transition per PR
- protects lane changes (allowed only at ARCHITECT boundary)
5. `swarm/policy_guard.py`
- separation-of-concerns allowlists
- role inference in diff mode uses `head.current_phase` when state changes

## 2) Execution Lanes
`execution_lane` in `swarm_state.json` controls allowed workflow:

### FULL (default)
`ARCHITECT -> QA_CONTRACT -> BACKEND -> ANALYST_CI_GATE -> FRONTEND -> QA_E2E -> ANALYST_FINAL`

### FAST_UI
`ARCHITECT -> FRONTEND -> QA_E2E -> ANALYST_FINAL`

Rules:
- lane switch is done only via `swarm/set_execution_lane.py`
- lane switch allowed only at architecture boundary unless forced for recovery
- `required_phase_sequence` must match lane default (unless explicitly custom-enabled)

## 3) Executor Attestation (Mandatory)
A valid run must contain:
- `EXECUTOR: codex-cli (codex exec)`
- `EXECUTOR_VERSION: ...`
- `WRAPPER_MODE: READ_ONLY|WRITE`
- `L2_AUTOMATION: OK` (write mode)

If missing: treat run as invalid and rerun through `/swarm-os` skill.

## 4) Auto Classification and Routing
`run.py` routing policy:
- explicit lane hint wins (`LANE: FAST_UI` / `РЕЖИМ: FAST_UI`)
- otherwise heuristic classifier:
  - UI/cosmetic-heavy request -> `FAST_UI`
  - backend/integration/API request -> `FULL`
- classifier result is printed in attestation.

## 5) Auto Stop and Rollback Behavior
On blocker:
- wrapper writes `tasks/reports/<task_id>/BLOCKER-<timestamp>.md`
- returns `L2_AUTOMATION: FAILED` and never advances phase

FAST_UI regression path:
- if L2 fails on UI-critical checks (`tests/e2e` etc), wrapper attempts auto-rollback:
  - generate `tasks/feedback/fix_required_auto.md`
  - transition state back to `FRONTEND` where valid
  - push rollback commit on current feature branch (best effort)

## 6) Recovery / Resume Contract
To resume in a new context window:
1. read `ACTIVE_SWARM_PROJECT.md`
2. read project `swarm_state.json`
3. run:
```bash
python3 swarm/validate_state.py --role <role_from_next_phase> --json
```
4. continue only if attestation markers exist in the previous step output.

## 7) Operator Commands (Canonical)
Read-only diagnostics:
```text
Swarm OS: Работаем в <project>. Проверь состояние и blockers.
```

Write execution:
```text
Swarm OS: RUN: Работаем в <project>.
Определи next_phase и выполни ровно одну фазу по явной задаче tasks/queue/<file>.md.
```

FAST_UI explicit:
```text
Swarm OS: RUN: Работаем в <project>. LANE: FAST_UI.
Выполни фазу по tasks/queue/<file>.md без пропуска gates.
```

## 8) Quality Gate (Done Criteria)
Phase is done only when:
1. PR merged to `main`
2. required checks green
3. `main` is clean and synced with `origin/main`
4. `swarm_state.json.next_phase` advanced legally
5. attestation markers present

