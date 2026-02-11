#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hmac
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Optional

try:
    import fcntl  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover (non-POSIX)
    fcntl = None  # type: ignore[assignment]

try:
    # Support both:
    # - `python3 swarm/transition_state.py`
    # - `python3 -m swarm.transition_state`
    from .validate_state import (
        DEFAULT_REQUIRED_PHASE_SEQUENCE,
        LANE_REQUIRED_PHASE_SEQUENCE,
        PHASE_TO_ROLE,
        ValidationError,
        _canonicalize_phase,
        _compute_state_hmac,
        _iter_history_phases,
        _normalize_lane,
        _normalize_role,
    )
except ImportError:  # pragma: no cover
    from validate_state import (  # type: ignore
        DEFAULT_REQUIRED_PHASE_SEQUENCE,
        LANE_REQUIRED_PHASE_SEQUENCE,
        PHASE_TO_ROLE,
        ValidationError,
        _canonicalize_phase,
        _compute_state_hmac,
        _iter_history_phases,
        _normalize_lane,
        _normalize_role,
    )


# Allowed transitions define the non-skippable state machine.
FULL_ALLOWED_TRANSITIONS: set[tuple[str, str]] = {
    ("INIT", "ARCHITECT"),
    ("ARCHITECT", "QA_CONTRACT"),
    ("QA_CONTRACT", "BACKEND"),
    ("BACKEND", "ANALYST_CI_GATE"),
    ("ANALYST_CI_GATE", "BACKEND"),  # Fix loop
    ("ANALYST_CI_GATE", "FRONTEND"),
    ("ANALYST_CI_GATE", "ARCHITECT"),  # escalation to architecture changes
    ("FRONTEND", "QA_E2E"),
    ("FRONTEND", "ANALYST_CI_GATE"),  # unit/integration failures routed to Analyst
    ("QA_E2E", "ANALYST_FINAL"),
    ("QA_E2E", "ANALYST_CI_GATE"),  # E2E failures routed to Analyst
    ("ANALYST_FINAL", "COMPLETE"),
    ("ANALYST_FINAL", "FRONTEND"),
    ("ANALYST_FINAL", "BACKEND"),
    ("ANALYST_FINAL", "ARCHITECT"),
}

FAST_UI_ALLOWED_TRANSITIONS: set[tuple[str, str]] = {
    ("INIT", "ARCHITECT"),
    ("ARCHITECT", "FRONTEND"),
    ("FRONTEND", "QA_E2E"),
    ("FRONTEND", "ARCHITECT"),  # escalation to planning if UI scope changed
    ("QA_E2E", "ANALYST_FINAL"),
    ("QA_E2E", "FRONTEND"),  # auto-rollback loop for UI regressions
    ("ANALYST_FINAL", "COMPLETE"),
    ("ANALYST_FINAL", "FRONTEND"),
    ("ANALYST_FINAL", "ARCHITECT"),
}

ALLOWED_TRANSITIONS_BY_LANE: dict[str, set[tuple[str, str]]] = {
    "FULL": FULL_ALLOWED_TRANSITIONS,
    "FAST_UI": FAST_UI_ALLOWED_TRANSITIONS,
}

# Backward-compatible export used by state_diff_guard.
ALLOWED_TRANSITIONS: set[tuple[str, str]] = set().union(*ALLOWED_TRANSITIONS_BY_LANE.values())


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_file(path: Path) -> str:
    h = sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _ensure_required_sequence(state: dict[str, Any], *, lane: str) -> list[str]:
    lane_default = list(LANE_REQUIRED_PHASE_SEQUENCE.get(lane, DEFAULT_REQUIRED_PHASE_SEQUENCE))
    raw = state.get("required_phase_sequence")
    if isinstance(raw, list) and all(isinstance(x, str) for x in raw):
        seq = [_canonicalize_phase(x) for x in raw]
        allow_custom = bool(state.get("allow_custom_sequence") is True)
        if seq != lane_default and not allow_custom:
            raise ValidationError(
                "required_phase_sequence must match execution_lane default unless allow_custom_sequence=true."
            )
        return seq
    # Default to the standard sequence if missing/malformed.
    state["required_phase_sequence"] = list(lane_default)
    return list(lane_default)


def _load_json_from_text(path: Path, text: str) -> dict[str, Any]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON in {path}: {e}") from e
    if not isinstance(data, dict):
        raise ValidationError(f"State file must contain a JSON object, got: {type(data).__name__}")
    return data


def _lock_exclusive(f) -> None:
    if fcntl is None:
        return
    fcntl.flock(f, fcntl.LOCK_EX)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Transition swarm_state.json (the only supported writer).")
    parser.add_argument("--state", default="swarm_state.json", help="Path to swarm_state.json")
    parser.add_argument("--role", required=True, help="Acting role performing the current next_phase.")
    parser.add_argument(
        "--to",
        required=True,
        help="Next phase to set after completing the current next_phase.",
    )
    parser.add_argument("--evidence", help="Path to an evidence file (raw test output, attestation, etc.).")
    parser.add_argument("--note", default="", help="Short transition note (why / what happened).")
    parser.add_argument("--dry-run", action="store_true", help="Validate and print the new state without writing.")
    args = parser.parse_args(argv)

    state_path = Path(args.state)
    try:
        with state_path.open("r+", encoding="utf-8") as f:
            _lock_exclusive(f)
            original_text = f.read()
            state = _load_json_from_text(state_path, original_text)

            role = _normalize_role(args.role)

            raw_current = state.get("current_phase")
            raw_next = state.get("next_phase")
            if not isinstance(raw_current, str) or not isinstance(raw_next, str):
                raise ValidationError("State must contain string fields: current_phase and next_phase.")

            executing_phase = _canonicalize_phase(raw_next)  # the phase we are completing now
            next_phase = _canonicalize_phase(args.to)
            lane = _normalize_lane(state.get("execution_lane"))
            state["execution_lane"] = lane

            if state.get("is_locked") is True:
                raise ValidationError("State is locked (is_locked=true). Cannot transition.")

            expected_role = PHASE_TO_ROLE.get(executing_phase)
            if expected_role is None:
                raise ValidationError(f"Internal error: no role mapping for phase {executing_phase}.")
            if role != expected_role:
                raise ValidationError(
                    f"Role/phase mismatch: role={role!r} cannot complete next_phase={executing_phase!r}. "
                    f"Expected role: {expected_role!r}."
                )

            lane_allowed = ALLOWED_TRANSITIONS_BY_LANE.get(lane, FULL_ALLOWED_TRANSITIONS)
            if (executing_phase, next_phase) not in lane_allowed:
                allowed = sorted([b for (a, b) in lane_allowed if a == executing_phase])
                raise ValidationError(
                    f"Illegal transition for execution_lane={lane}: {executing_phase} -> {next_phase}. "
                    f"Allowed next phases: {allowed}"
                )

            required_seq = _ensure_required_sequence(state, lane=lane)

            # Enforce "no skipping" via next_phase. Allow fix loops backwards.
            if next_phase in required_seq:
                idx_next = required_seq.index(next_phase)
                timeline = [_canonicalize_phase(p) for p in _iter_history_phases(state.get("history"))]
                timeline.append(executing_phase)
                completed = set(timeline)
                missing = [p for p in required_seq[:idx_next] if p not in completed]
                if missing:
                    raise ValidationError(
                        f"Skip detected: cannot transition to {next_phase} without completing required phases: {missing}"
                    )

            evidence_obj = None
            if args.evidence:
                evidence_path = Path(args.evidence)
                if not evidence_path.exists():
                    raise ValidationError(f"Evidence file not found: {evidence_path}")
                evidence_obj = {
                    "path": str(evidence_path),
                    "sha256": _sha256_file(evidence_path),
                }

            # Update state (canonical fields remain present).
            state["current_phase"] = executing_phase
            state["next_phase"] = next_phase

            history_list: list[Any] = list(state.get("history") or [])
            history_list.append(
                {
                    "phase": executing_phase,
                    "at": _utc_now_iso(),
                    "by_role": role,
                    "lane": lane,
                    "note": args.note,
                    "evidence": evidence_obj,
                }
            )
            state["history"] = history_list
            state["last_updated"] = _utc_now_iso()

            # Optional tamper-evidence HMAC.
            hmac_key = os.environ.get("SWARM_STATE_HMAC_KEY")
            if hmac_key:
                state["state_hmac"] = _compute_state_hmac(state, hmac_key.encode("utf-8"))

            rendered = json.dumps(state, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
            if args.dry_run:
                sys.stdout.write(rendered)
                return 0

            # Backup before write (best-effort recovery). Keep outside git via `*.bak` ignore.
            backup_path = state_path.with_suffix(state_path.suffix + ".bak")
            try:
                backup_path.write_text(original_text, encoding="utf-8")
            except OSError:
                # Non-fatal: backups are a safety net, but transitions must remain deterministic.
                pass

            f.seek(0)
            f.truncate()
            f.write(rendered)
            f.flush()
            try:
                os.fsync(f.fileno())
            except OSError:
                # fsync can fail on some filesystems; the state file is still written.
                pass

            sys.stdout.write(f"OK: transitioned {executing_phase} -> {next_phase}\n")
            return 0
    except FileNotFoundError as e:
        raise ValidationError(f"Missing required file: {state_path}") from e


if __name__ == "__main__":
    raise SystemExit(main())
