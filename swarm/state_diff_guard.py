#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

try:
    # Support both:
    # - `python3 swarm/state_diff_guard.py`
    # - `python3 -m swarm.state_diff_guard`
    from .transition_state import ALLOWED_TRANSITIONS
    from .validate_state import PHASE_TO_ROLE, ValidationError, _canonicalize_phase
except ImportError:  # pragma: no cover
    from transition_state import ALLOWED_TRANSITIONS  # type: ignore
    from validate_state import PHASE_TO_ROLE, ValidationError, _canonicalize_phase  # type: ignore


@dataclass(frozen=True)
class DiffResult:
    ok: bool
    changed: bool
    errors: list[str]
    base_ref: str
    head_ref: str


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


def _is_sha256_hex(s: str) -> bool:
    return bool(re.fullmatch(r"[0-9a-f]{64}", s))


def _looks_like_iso_z(s: str) -> bool:
    # We keep this loose to avoid false negatives while still blocking obvious garbage.
    return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}T[^\\s]+Z", s))


def _state_changed(base: str, head: str, state_path: str) -> bool:
    out = _run_git(["diff", "--name-only", f"{base}...{head}", "--", state_path])
    return any(ln.strip() == state_path for ln in out.splitlines())


def _validate_state_transition(
    *,
    base_ref: str,
    head_ref: str,
    state_path: str,
) -> DiffResult:
    errors: list[str] = []

    if not _state_changed(base_ref, head_ref, state_path):
        return DiffResult(ok=True, changed=False, errors=[], base_ref=base_ref, head_ref=head_ref)

    base_state = _load_json_from_git(base_ref, state_path)
    head_state = _load_json_from_git(head_ref, state_path)

    base_next_raw = base_state.get("next_phase")
    head_current_raw = head_state.get("current_phase")
    head_next_raw = head_state.get("next_phase")

    if not isinstance(base_next_raw, str):
        errors.append("Base swarm_state.json.next_phase must be a string.")
        base_next = None
    else:
        try:
            base_next = _canonicalize_phase(base_next_raw)
        except ValidationError as e:
            errors.append(f"Base next_phase invalid: {e}")
            base_next = None

    if not isinstance(head_current_raw, str):
        errors.append("Head swarm_state.json.current_phase must be a string.")
        head_current = None
    else:
        try:
            head_current = _canonicalize_phase(head_current_raw)
        except ValidationError as e:
            errors.append(f"Head current_phase invalid: {e}")
            head_current = None

    if not isinstance(head_next_raw, str):
        errors.append("Head swarm_state.json.next_phase must be a string.")
        head_next = None
    else:
        try:
            head_next = _canonicalize_phase(head_next_raw)
        except ValidationError as e:
            errors.append(f"Head next_phase invalid: {e}")
            head_next = None

    if base_next and head_current and head_current != base_next:
        errors.append(
            f"Invalid transition semantics: head.current_phase={head_current} must equal base.next_phase={base_next}."
        )

    if base_next and head_next and (base_next, head_next) not in ALLOWED_TRANSITIONS:
        allowed = sorted([b for (a, b) in ALLOWED_TRANSITIONS if a == base_next])
        errors.append(
            f"Illegal transition: {base_next} -> {head_next}. Allowed next phases: {allowed}"
        )

    # Required sequence must remain stable: changing it weakens enforcement.
    if base_state.get("required_phase_sequence") != head_state.get("required_phase_sequence"):
        errors.append("required_phase_sequence must not change in a PR (protected invariant).")

    # Lock status must not be silently toggled in a PR.
    if base_state.get("is_locked") != head_state.get("is_locked"):
        errors.append("is_locked must not change in a PR (protected invariant).")

    base_hist = base_state.get("history")
    head_hist = head_state.get("history")
    if not isinstance(base_hist, list) or not isinstance(head_hist, list):
        errors.append("history must be a JSON array in both base and head swarm_state.json.")
    else:
        if len(head_hist) != len(base_hist) + 1:
            errors.append("history must be append-only with exactly 1 new entry per transition PR.")
        else:
            if head_hist[: len(base_hist)] != base_hist:
                errors.append("history prefix mismatch: base history must be preserved verbatim (append-only).")

            new_entry = head_hist[-1]
            if not isinstance(new_entry, dict):
                errors.append("history new entry must be an object.")
            else:
                phase_raw = new_entry.get("phase")
                by_role = new_entry.get("by_role")
                at = new_entry.get("at")
                if not isinstance(phase_raw, str):
                    errors.append("history new entry: phase must be a string.")
                else:
                    try:
                        entry_phase = _canonicalize_phase(phase_raw)
                    except ValidationError as e:
                        errors.append(f"history new entry: invalid phase: {e}")
                        entry_phase = None
                    else:
                        if base_next and entry_phase != base_next:
                            errors.append("history new entry: phase must equal base.next_phase.")

                if base_next:
                    expected_role = PHASE_TO_ROLE.get(base_next)
                    if not expected_role:
                        errors.append(f"Internal error: no role mapping for phase {base_next}.")
                    else:
                        if not isinstance(by_role, str) or by_role != expected_role:
                            errors.append(
                                f"history new entry: by_role must be {expected_role!r} for phase {base_next}."
                            )

                if not isinstance(at, str) or not at or not _looks_like_iso_z(at):
                    errors.append("history new entry: at must be an ISO-8601 timestamp ending with 'Z'.")

                evidence = new_entry.get("evidence")
                if evidence is not None:
                    if not isinstance(evidence, dict):
                        errors.append("history new entry: evidence must be null or an object.")
                    else:
                        sha = evidence.get("sha256")
                        if sha is not None and (not isinstance(sha, str) or not _is_sha256_hex(sha)):
                            errors.append("history new entry: evidence.sha256 must be a 64-char lowercase hex string.")

    ok = not errors
    return DiffResult(ok=ok, changed=True, errors=errors, base_ref=base_ref, head_ref=head_ref)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate that swarm_state.json changes in a PR are append-only and represent exactly one legal transition."
    )
    parser.add_argument("--base", required=True, help="Base git ref/sha")
    parser.add_argument("--head", required=True, help="Head git ref/sha")
    parser.add_argument("--state", default="swarm_state.json", help="Repo-relative path to swarm_state.json")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    args = parser.parse_args(argv)

    try:
        res = _validate_state_transition(base_ref=args.base, head_ref=args.head, state_path=args.state)
    except ValidationError as e:
        if args.json:
            sys.stdout.write(
                json.dumps(
                    {
                        "ok": False,
                        "changed": True,
                        "errors": [str(e)],
                        "base_ref": args.base,
                        "head_ref": args.head,
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n"
            )
        else:
            sys.stderr.write(f"ERROR: {e}\n")
        return 1

    if args.json:
        sys.stdout.write(
            json.dumps(
                {
                    "ok": res.ok,
                    "changed": res.changed,
                    "errors": res.errors,
                    "base_ref": res.base_ref,
                    "head_ref": res.head_ref,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
    else:
        if not res.changed:
            sys.stdout.write("OK: swarm_state.json unchanged.\n")
        elif res.ok:
            sys.stdout.write("OK: swarm_state.json transition is legal and append-only.\n")
        else:
            sys.stderr.write("ERROR: swarm_state.json transition is invalid:\n")
            for e in res.errors:
                sys.stderr.write(f"- {e}\n")

    return 0 if res.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

