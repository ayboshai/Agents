# Constitutional Multi-Agent Swarm OS (CMAS-OS)

This repository is a **state-machine enforced** multi-agent engineering workflow where:
- Phases are **non-skippable** (Architect -> QA -> Dev -> Analyst -> ...).
- PASS/FAIL is **evidence-based** (CI required checks in L2, captured stdout/stderr in L1).
- "Soft rules" in markdown are backed by **hard gates** (exit codes) in `swarm/`.

## Single Source of Truth
- `SWARM_CONSTITUTION.md` (law)
- `swarm_state.json` (state machine)
- `TASKS_CONTEXT.md` (dynamic project constraints and tech choices)

## Two Enforcement Levels
### Level 1 (L1) Soft-Infra, Hard Gates (Current Reality)
Use when you run via OpenClaw/Danny AI or any local orchestrator without GitHub branch protection.
- Gates are enforced by Python stdlib scripts in `swarm/` (exit code != 0 blocks progress).
- Test evidence is captured from **real command output** and appended to `tasks/logs/CI_LOGS.md`.

### Level 2 (L2) Hard Enforcement (Target)
Use when GitHub Actions + Branch Protection are available.
- `.github/workflows/ci.yml` defines the required checks.
- CI run logs + uploaded attestation artifact are the authoritative PASS/FAIL.

## GitHub Actions Without a Codex/OpenAI API Key
Yes: GitHub Actions does **not** require any Codex/OpenAI API key unless you explicitly call an LLM API from the workflow.

This repository’s CI (`.github/workflows/ci.yml`) only runs deterministic gates:
- state machine validation
- separation-of-concerns policy guard
- anti-mock + anti-placeholder guards
- unit/integration tests
- E2E tests

Codex Web can open PRs; GitHub Actions runs and reports PASS/FAIL; humans/roles follow `swarm_state.json` to decide the next phase.

## Quick Start
### L1: One-Command Gate + Evidence + Transition
```bash
python3 swarm/orchestrate.py \
  --role qa \
  --command "npm test" \
  --to BACKEND \
  --note "Contract tests updated"
```

### L2: Enable Required Checks
1. Enable GitHub Actions.
2. Configure Branch Protection on `main` with required checks from `ci.yml`:
   - `swarm/state-guard`
   - `swarm/policy-guard`
   - `quality/no-mocks`
   - `quality/no-placeholders`
   - `tests/unit-integration`
   - `tests/e2e`
3. Replace placeholders in `.github/CODEOWNERS` with real GitHub handles/teams.

## Developer Hooks (Optional, Local)
Trackable pre-commit hooks live in `githooks/`.
```bash
git config core.hooksPath githooks
```
