# Swarm Guards (Level 1 + Level 2)

This folder contains **programmatic guards** that turn the constitution from "soft text" into executable gates.

## Level 1 (OpenClaw/Danny AI Orchestrated)
Use these scripts **before** and **after** each agent action.

### One-Command Wrapper (Recommended)
If you want a single entrypoint that runs the full Level 1 enforcement chain:
```bash
python3 swarm/orchestrate.py \
  --role <architect|qa|backend|frontend|analyst> \
  --command "<TEST_COMMAND>" \
  --to <NEXT_PHASE> \
  --note "what changed"
```

Notes:
- This tool is designed for the Fix Loop: it transitions state even if the command fails, as long as evidence capture succeeds.
- The command exit code is recorded inside the transition note and the append-only evidence index.

### 1) Pre-Action: State Validation (Hard Stop)
```bash
python3 swarm/validate_state.py --role <architect|qa|backend|frontend|analyst>
```

### 2) After Changes: Policy Guard (Separation of Concerns)
```bash
python3 swarm/policy_guard.py --role <architect|qa|backend|frontend|analyst>
```

### 3) Run Real Tests and Capture Raw Output
Run the appropriate commands for the current project (as defined by `TASKS_CONTEXT.md`), redirecting stdout/stderr:
```bash
set -o pipefail
<TEST_COMMAND> 2>&1 | tee /tmp/swarm_test_output.txt
exit_code=${PIPESTATUS[0]}
```

Alternatively, use the wrapper:
```bash
python3 swarm/run_and_capture.py --command "<TEST_COMMAND>" --phase "<CURRENT_PHASE>" --task-id "<TASK_ID>"
```

### 4) Append Evidence (Append-Only) + Store Immutable Raw Output
```bash
python3 swarm/capture_test_output.py \
  --input /tmp/swarm_test_output.txt \
  --command "<TEST_COMMAND>" \
  --exit-code "$exit_code" \
  --phase "<CURRENT_PHASE>" \
  --task-id "<TASK_ID>"
```

### 5) Transition State (Only Supported Writer)
```bash
python3 swarm/transition_state.py \
  --role <architect|qa|backend|frontend|analyst> \
  --to <NEXT_PHASE> \
  --evidence /tmp/swarm_test_output.txt \
  --note "short reason"
```

### 5.1) Switch Execution Lane (Only Supported Lane Writer)
```bash
python3 swarm/set_execution_lane.py \
  --lane <FULL|FAST_UI> \
  --reason "why lane is changing"
```
Notes:
- lane switch is allowed only at architecture boundary unless `--force` is used for recovery.
- script updates `execution_lane` + `required_phase_sequence` atomically.

### 6) Analyst Feedback Artifact
```bash
python3 swarm/create_feedback.py \
  --task-id "<TASK_ID>" \
  --run-id "<RUN_ID>" \
  --evidence /tmp/swarm_test_output.txt \
  --summary "what failed and why"
```

## Optional Integrity (Tamper-Evidence)
If the orchestrator can keep secrets out of the agent runtime, set:
- `SWARM_STATE_HMAC_KEY` to require/verify `swarm_state.json` signatures.
- `SWARM_LOG_HMAC_KEY` to chain-sign `tasks/logs/CI_LOGS.md` run blocks.

Guards will verify signatures when the keys are present.

---

## Level 2 (GitHub Actions + Branch Protection)
In L2 mode, GitHub Actions is the authoritative PASS/FAIL source.

### PR Gate (Wait -> Merge)
The orchestrator can hard-lock merges using:
```bash
export GITHUB_TOKEN=...   # or GH_TOKEN
export GITHUB_REPO=owner/repo

python3 swarm/gh_pr_gate.py --pr <PR_NUMBER> --merge
```

This will:
1. Wait for required checks on the PR head SHA to be present and green.
2. Merge the PR (default: squash).

If any required check fails, the script exits non-zero and prints the failing checks.

Optional:
- `--approve` can be used only if the token user is allowed to approve that PR.
  GitHub forbids approving your own PR, so `--approve` will fail if the PR author == token user.
