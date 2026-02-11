#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Optional

try:
    # Support both:
    # - `python3 swarm/policy_guard.py` (flat imports)
    # - `python3 -m swarm.policy_guard` (package imports)
    from .validate_state import (
        PHASE_TO_ROLE,
        ValidationError,
        _canonicalize_phase,
        _load_json,
        _normalize_role,
    )
except ImportError:  # pragma: no cover
    from validate_state import (  # type: ignore
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
    # Evidence must only be written by orchestrator scripts.
    "tasks/logs/**",
    "tasks/evidence/**",
]

CODEOWNERS_PATH = ".github/CODEOWNERS"
ALLOW_CODEOWNERS_ENV = "CMAS_ALLOW_CODEOWNERS_EDIT"

ROLE_ALLOW_GLOBS_AGENT: dict[str, list[str]] = {
    # Architect owns system law, contracts, and infrastructure.
    "architect": [
        "SWARM_CONSTITUTION.md",
        "SWARM_ARCHITECTURE.md",
        "TASKS_CONTEXT.md",
        "README.md",
        ".gitignore",
        "package.json",
        "package-lock.json",
        "tsconfig.json",
        "vitest.config.ts",
        "playwright.config.ts",
        "next-env.d.ts",
        "swarm_state.json",
        "docs/**",
        "config/personas/**",
        ".github/**",
        "githooks/**",
        "swarm/**",
        "requirements.txt",
        # Project scaffolding (allowed only in ARCHITECT phase).
        "app/**",
        "components/**",
        "data/**",
        "lib/**",
        "public/**",
        "src/**",
        "tests/**",
        "workflows/**",
        "tasks/queue/**",
        # Phase report is mandatory in constitution for every phase.
        "tasks/reports/**",
        # Cleanup for project reset (do not touch tasks/logs/** or tasks/evidence/**).
        "tasks/completed/**",
        "tasks/changes/**",
        "tasks/feedback/**",
    ],
    # QA owns tests and test configuration.
    "qa": [
        "tests/**",
        "vitest.config.ts",
        "playwright.config.ts",
        "package.json",
        "package-lock.json",
        "scripts/test.sh",
        "TASKS_CONTEXT.md",
        "swarm_state.json",
        "tasks/reports/**",
        "tasks/changes/**",
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
        "swarm_state.json",
        "tasks/reports/**",
        "tasks/changes/**",
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
        "swarm_state.json",
        "tasks/reports/**",
        "tasks/changes/**",
    ],
    # Analyst owns feedback/reports only (no code).
    "analyst": [
        "tasks/feedback/**",
        "tasks/reports/**",
        "tasks/completed/**",
        "tasks/changes/**",
        "docs/**",
        "swarm_state.json",
    ],
    # Orchestrator may write evidence/state/logs.
    "orchestrator": [
        "swarm_state.json",
        "tasks/logs/**",
        "tasks/evidence/**",
        "tasks/reports/**",
        "tasks/queue/**",
        "tasks/completed/**",
        "tasks/changes/**",
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


def _load_json_from_git(ref: str, path: str) -> dict[str, Any]:
    if Path(path).is_absolute():
        raise ValidationError("--state must be a repo-relative path in diff mode (CI).")
    raw = _run_git(["show", f"{ref}:{path}"])
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON in {ref}:{path}: {e}") from e
    if not isinstance(data, dict):
        raise ValidationError(f"{ref}:{path} must contain a JSON object, got: {type(data).__name__}")
    return data


def _state_changed(base: str, head: str, state_path: str) -> bool:
    out = _run_git(["diff", "--name-only", f"{base}...{head}", "--", state_path])
    return any(ln.strip() == state_path for ln in out.splitlines())


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


def _is_allowed(
    path: str,
    role: str,
    actor: str,
    *,
    state_path: str,
    allow_state_edit: bool,
    allow_codeowners_edit: bool,
) -> tuple[bool, str]:
    if path == state_path and not allow_state_edit and actor != "orchestrator":
        return False, f"{state_path} is orchestrator-only in working-tree mode. Use transition_state.py."

    if path == CODEOWNERS_PATH and not allow_codeowners_edit:
        return (
            False,
            f"{CODEOWNERS_PATH} is protected; set --allow-codeowners-edit or {ALLOW_CODEOWNERS_ENV}=1 to modify it.",
        )

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
    parser.add_argument(
        "--allow-codeowners-edit",
        action="store_true",
        help=f"Allow editing {CODEOWNERS_PATH} (normally forbidden to prevent weakening enforcement).",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output.")
    args = parser.parse_args(argv)

    role_phase_source = "base.next_phase"
    if args.base:
        if not args.head:
            raise ValidationError("--head is required when --base is set.")
        changed = _changed_files_diff(args.base, args.head)
        mode = "diff"
        state = _load_json_from_git(args.base, args.state)
        state_ref = args.base
        if _state_changed(args.base, args.head, args.state):
            try:
                head_state = _load_json_from_git(args.head, args.state)
                head_current_raw = head_state.get("current_phase")
                if isinstance(head_current_raw, str):
                    head_current = _canonicalize_phase(head_current_raw)
                    state = dict(state)
                    state["next_phase"] = head_current
                    role_phase_source = "head.current_phase"
            except ValidationError:
                pass
    else:
        changed = _changed_files_working_tree()
        mode = "working_tree"
        state = _load_json(Path(args.state))
        state_ref = "working_tree"

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

    allow_codeowners_edit = bool(args.allow_codeowners_edit or os.environ.get(ALLOW_CODEOWNERS_ENV) == "1")
    allow_state_edit = mode == "diff"

    violations: list[Violation] = []
    for p in changed:
        ok, reason = _is_allowed(
            p,
            role=role,
            actor=("orchestrator" if actor == "orchestrator" else "agent"),
            state_path=args.state,
            allow_state_edit=allow_state_edit,
            allow_codeowners_edit=allow_codeowners_edit,
        )
        if not ok:
            violations.append(Violation(path=p, reason=reason))

    ok = not violations
    if args.json:
        payload = {
            "ok": ok,
            "mode": mode,
            "state_ref": state_ref,
            "role_phase_source": role_phase_source,
            "role": role,
            "actor": actor,
            "next_phase": next_phase,
            "allow_state_edit": allow_state_edit,
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
