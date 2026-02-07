#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional


class OrchestrateError(RuntimeError):
    pass


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _script_path(name: str) -> Path:
    return Path(__file__).resolve().parent / name


def _run(cmd: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


def _run_py(script_name: str, args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    script = _script_path(script_name)
    return _run([sys.executable, str(script), *args], cwd=cwd)


def _load_state(state_path: Path) -> dict:
    try:
        data = json.loads(state_path.read_text(encoding="utf-8"))
    except FileNotFoundError as e:
        raise OrchestrateError(f"Missing state file: {state_path}") from e
    except json.JSONDecodeError as e:
        raise OrchestrateError(f"Invalid JSON in state file {state_path}: {e}") from e
    if not isinstance(data, dict):
        raise OrchestrateError("swarm_state.json must be a JSON object.")
    return data


def _parse_last_run(ci_logs_path: Path) -> dict[str, str]:
    """
    Extract the last run block metadata written by capture_test_output.py.

    We intentionally parse from the end to tolerate legacy/manual content above.
    """
    if not ci_logs_path.exists():
        raise OrchestrateError(f"CI logs not found: {ci_logs_path}")

    lines = ci_logs_path.read_text(encoding="utf-8", errors="replace").splitlines()
    # Find last "## Run:" header.
    run_header_idx = None
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].startswith("## Run: "):
            run_header_idx = i
            break
    if run_header_idx is None:
        raise OrchestrateError("Unable to locate last run header ('## Run: ...') in CI_LOGS.md.")

    run_id = lines[run_header_idx].split("## Run: ", 1)[1].strip()

    # Scan within the block for evidence path.
    evidence = ""
    for ln in lines[run_header_idx:]:
        if ln.startswith("## Run: ") and ln != lines[run_header_idx]:
            break
        m = re.match(r"^- evidence: `([^`]+)`\s*$", ln)
        if m:
            evidence = m.group(1)
            break

    if not evidence:
        raise OrchestrateError(f"Unable to locate '- evidence: `...`' for run {run_id}.")

    return {"run_id": run_id, "evidence": evidence}


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Single-command Level 1 orchestration wrapper.\n"
            "Runs the enforcement chain:\n"
            "  1) validate_state.py (hard stop)\n"
            "  2) policy_guard.py (separation of concerns)\n"
            "  3) no_mocks_guard.py + no_placeholders_guard.py\n"
            "  4) run_and_capture.py (real command + append-only evidence)\n"
            "  5) transition_state.py (only supported state writer)\n"
            "\n"
            "Note: This tool is for L1 (OpenClaw/Danny AI) usage. L2 (GitHub Actions) uses .github/workflows/ci.yml."
        )
    )
    parser.add_argument("--state", default="swarm_state.json", help="Path to swarm_state.json")
    parser.add_argument("--role", required=True, help="Acting role (architect|qa|backend|frontend|analyst)")
    parser.add_argument("--to", required=True, help="Next phase to set (validated by transition graph).")
    parser.add_argument("--command", required=True, help="Real command to execute (tests/build/etc).")
    parser.add_argument("--task-id", default="", help="Task id (optional; defaults from swarm_state.json.task_id).")
    parser.add_argument("--note", default="", help="Short note for the state transition.")
    parser.add_argument("--actor", default="orchestrator", help="Actor for evidence capture (default: orchestrator).")
    parser.add_argument(
        "--allow-codeowners-edit",
        action="store_true",
        help="Allow editing .github/CODEOWNERS (normally forbidden).",
    )
    parser.add_argument("--ci-logs", default="tasks/logs/CI_LOGS.md", help="Path to append-only CI_LOGS.md")
    args = parser.parse_args(argv)

    repo_root = _repo_root()
    state_path = (repo_root / args.state).resolve() if not Path(args.state).is_absolute() else Path(args.state)
    ci_logs_path = (repo_root / args.ci_logs).resolve() if not Path(args.ci_logs).is_absolute() else Path(args.ci_logs)

    # 1) Hard-stop state validation.
    p = _run_py("validate_state.py", ["--state", str(state_path), "--role", args.role], cwd=repo_root)
    sys.stdout.write(p.stdout)
    if p.returncode != 0:
        return p.returncode

    # Infer phase/task-id from the current state (authoritative).
    state = _load_state(state_path)
    phase = str(state.get("next_phase") or "")
    task_id = args.task_id or str(state.get("task_id") or "")

    # 2) Separation-of-concerns: forbid editing outside the role allowlist.
    policy_args = ["--state", str(state_path), "--role", args.role]
    if args.allow_codeowners_edit:
        policy_args.append("--allow-codeowners-edit")
    p = _run_py("policy_guard.py", policy_args, cwd=repo_root)
    sys.stdout.write(p.stdout)
    if p.returncode != 0:
        return p.returncode

    # 3) Hard quality gates.
    p = _run_py("no_mocks_guard.py", [], cwd=repo_root)
    sys.stdout.write(p.stdout)
    if p.returncode != 0:
        return p.returncode

    p = _run_py("no_placeholders_guard.py", [], cwd=repo_root)
    sys.stdout.write(p.stdout)
    if p.returncode != 0:
        return p.returncode

    # 4) Real execution + evidence capture (append-only).
    p = _run_py(
        "run_and_capture.py",
        [
            "--command",
            args.command,
            "--actor",
            args.actor,
            "--phase",
            phase,
            "--task-id",
            task_id,
            "--out",
            str(ci_logs_path),
        ],
        cwd=repo_root,
    )
    sys.stdout.write(p.stdout)
    cmd_exit = p.returncode
    if cmd_exit == 2:
        # run_and_capture reserves 2 for capture failures.
        sys.stderr.write("ERROR: evidence capture failed; refusing to transition state.\n")
        return 2

    # Extract evidence pointer from the append-only index.
    last = _parse_last_run(ci_logs_path)
    evidence_path = (repo_root / last["evidence"]).resolve() if not Path(last["evidence"]).is_absolute() else Path(last["evidence"])

    # 5) State transition. Note contains the command exit code and run id for auditability.
    note = (args.note.strip() + " ").rstrip() + f"(cmd_exit={cmd_exit}, run_id={last['run_id']})"
    p = _run_py(
        "transition_state.py",
        [
            "--state",
            str(state_path),
            "--role",
            args.role,
            "--to",
            args.to,
            "--evidence",
            str(evidence_path),
            "--note",
            note,
        ],
        cwd=repo_root,
    )
    sys.stdout.write(p.stdout)
    if p.returncode != 0:
        return p.returncode

    # Orchestration success means: gates ran + evidence captured + state transitioned.
    # The underlying command exit code is embedded in the transition note and CI_LOGS evidence.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

