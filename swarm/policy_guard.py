#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Optional

from validate_state import (
    PHASE_TO_ROLE,
    ValidationError,
    _canonicalize_phase,
    _load_json,
    _normalize_role,
)


@dataclass(frozen=True)
class Violation:
    path: str
    reason: str


GLOBAL_DENY_GLOBS_AGENT: list[str] = [
    # Evidence/state must only be written by orchestrator scripts.
    "swarm_state.json",
    "tasks/logs/**",
    "tasks/evidence/**",
]

ROLE_ALLOW_GLOBS_AGENT: dict[str, list[str]] = {
    # Architect owns system law, contracts, and infrastructure.
    "architect": [
        "SWARM_CONSTITUTION.md",
        "SWARM_ARCHITECTURE.md",
        "TASKS_CONTEXT.md",
        "docs/**",
        "config/personas/**",
        ".github/**",
        "swarm/**",
        "tasks/queue/**",
    ],
    # QA owns tests and test configuration.
    "qa": [
        "tests/**",
        "vitest.config.ts",
        "playwright.config.ts",
        "package.json",
        "package-lock.json",
        "TASKS_CONTEXT.md",
    ],
    # Backend owns server/business logic (project-specific; keep minimal exclusions).
    "backend": [
        "app/**",
        "components/**",
        "data/**",
        "lib/**",
        "src/**",
        "package.json",
        "package-lock.json",
        "tsconfig.json",
    ],
    # Frontend owns UI code.
    "frontend": [
        "app/**",
        "components/**",
        "data/**",
        "public/**",
        "package.json",
        "package-lock.json",
        "tsconfig.json",
    ],
    # Analyst owns feedback/reports only (no code).
    "analyst": [
        "tasks/feedback/**",
        "tasks/reports/**",
        "tasks/completed/**",
        "docs/**",
    ],
    # Orchestrator may write evidence/state/logs.
    "orchestrator": [
        "swarm_state.json",
        "tasks/logs/**",
        "tasks/evidence/**",
        "tasks/reports/**",
        "tasks/queue/**",
        "tasks/completed/**",
    ],
}

# Additional denies by role (agent mode).
ROLE_DENY_GLOBS_AGENT: dict[str, list[str]] = {
    # Dev must not change QA-owned tests.
    "backend": ["tests/**"],
    "frontend": ["tests/**"],
}


def _run_git(args: list[str]) -> str:
    res = subprocess.run(["git", *args], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise ValidationError(f"git {' '.join(args)} failed: {res.stderr.strip()}")
    return res.stdout


def _changed_files_working_tree() -> list[str]:
    out = _run_git(["status", "--porcelain=v1"])
    files: list[str] = []
    for line in out.splitlines():
        if not line:
            continue
        # Porcelain format: XY <path> (or XY <old> -> <new>)
        path_part = line[3:]
        if " -> " in path_part:
            path_part = path_part.split(" -> ", 1)[1]
        files.append(path_part.strip())
    return sorted(set(files))


def _changed_files_diff(base: str, head: str) -> list[str]:
    out = _run_git(["diff", "--name-only", f"{base}...{head}"])
    files = [ln.strip() for ln in out.splitlines() if ln.strip()]
    return sorted(set(files))


def _matches_any(path: str, globs: Iterable[str]) -> bool:
    return any(fnmatch.fnmatch(path, g) for g in globs)


def _is_allowed(path: str, role: str, actor: str) -> tuple[bool, str]:
    # Actor governs evidence/state writes.
    if actor != "orchestrator" and _matches_any(path, GLOBAL_DENY_GLOBS_AGENT):
        return False, f"Path is orchestrator-only: {path}"

    allow = ROLE_ALLOW_GLOBS_AGENT.get(role, [])
    if not allow:
        return False, f"No allowlist configured for role {role!r}"

    if not _matches_any(path, allow):
        return False, f"Path not in allowlist for role {role!r}: {path}"

    deny = ROLE_DENY_GLOBS_AGENT.get(role, [])
    if deny and _matches_any(path, deny):
        return False, f"Path denied for role {role!r}: {path}"

    return True, ""


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Enforce separation-of-concerns by blocking forbidden file edits.")
    parser.add_argument("--state", default="swarm_state.json", help="Path to swarm_state.json")
    parser.add_argument("--role", help="Acting role (default: inferred from swarm_state.json.next_phase)")
    parser.add_argument("--actor", default="agent", help="Who is performing writes: agent|orchestrator")
    parser.add_argument("--base", help="Base ref for diff mode (CI). If set, --head is required.")
    parser.add_argument("--head", help="Head ref for diff mode (CI).")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output.")
    args = parser.parse_args(argv)

    state = _load_json(Path(args.state))
    next_phase_raw = state.get("next_phase")
    if not isinstance(next_phase_raw, str):
        raise ValidationError("swarm_state.json.next_phase must be a string.")
    next_phase = _canonicalize_phase(next_phase_raw)
    expected_role = PHASE_TO_ROLE.get(next_phase)
    if expected_role is None:
        raise ValidationError(f"Internal error: no role mapping for next_phase={next_phase}.")

    actor = args.actor.strip().lower()
    if actor not in {"agent", "orchestrator"}:
        raise ValidationError("actor must be 'agent' or 'orchestrator'.")

    role = expected_role if not args.role else _normalize_role(args.role)
    if role != expected_role:
        raise ValidationError(
            f"Role/phase mismatch: next_phase={next_phase} expects role={expected_role}, got role={role}."
        )

    if args.base:
        if not args.head:
            raise ValidationError("--head is required when --base is set.")
        changed = _changed_files_diff(args.base, args.head)
        mode = "diff"
    else:
        changed = _changed_files_working_tree()
        mode = "working_tree"

    violations: list[Violation] = []
    for p in changed:
        ok, reason = _is_allowed(p, role=role, actor=("orchestrator" if actor == "orchestrator" else "agent"))
        if not ok:
            violations.append(Violation(path=p, reason=reason))

    ok = not violations
    if args.json:
        payload = {
            "ok": ok,
            "mode": mode,
            "role": role,
            "actor": actor,
            "next_phase": next_phase,
            "changed_files": changed,
            "violations": [v.__dict__ for v in violations],
        }
        sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    else:
        if ok:
            sys.stdout.write(f"OK: policy guard passed ({mode}); {len(changed)} files changed.\n")
        else:
            sys.stderr.write(f"ERROR: policy guard failed ({mode}); violations:\n")
            for v in violations:
                sys.stderr.write(f"- {v.path}: {v.reason}\n")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

