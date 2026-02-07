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

from validate_state import (
    CANONICAL_PHASES,
    DEFAULT_REQUIRED_PHASE_SEQUENCE,
    PHASE_TO_ROLE,
    ValidationError,
    _canonicalize_phase,
    _compute_state_hmac,
    _iter_history_phases,
    _load_json,
    _normalize_role,
)


# Allowed transitions define the non-skippable state machine.
# The set is intentionally small; add transitions only with explicit necessity.
ALLOWED_TRANSITIONS: set[tuple[str, str]] = {
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


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_file(path: Path) -> str:
    h = sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _ensure_required_sequence(state: dict[str, Any]) -> list[str]:
    raw = state.get("required_phase_sequence")
    if isinstance(raw, list) and all(isinstance(x, str) for x in raw):
        return [_canonicalize_phase(x) for x in raw]
    # Default to the standard sequence if missing/malformed.
    state["required_phase_sequence"] = list(DEFAULT_REQUIRED_PHASE_SEQUENCE)
    return list(DEFAULT_REQUIRED_PHASE_SEQUENCE)


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
    state = _load_json(state_path)

    role = _normalize_role(args.role)

    raw_current = state.get("current_phase")
    raw_next = state.get("next_phase")
    if not isinstance(raw_current, str) or not isinstance(raw_next, str):
        raise ValidationError("State must contain string fields: current_phase and next_phase.")

    current_phase = _canonicalize_phase(raw_current)
    executing_phase = _canonicalize_phase(raw_next)  # the phase we are completing now
    next_phase = _canonicalize_phase(args.to)

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

    if (executing_phase, next_phase) not in ALLOWED_TRANSITIONS:
        allowed = sorted([b for (a, b) in ALLOWED_TRANSITIONS if a == executing_phase])
        raise ValidationError(
            f"Illegal transition: {executing_phase} -> {next_phase}. Allowed next phases: {allowed}"
        )

    required_seq = _ensure_required_sequence(state)

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
            "note": args.note,
            "evidence": evidence_obj,
        }
    )
    state["history"] = history_list

    # Optional tamper-evidence HMAC.
    hmac_key = os.environ.get("SWARM_STATE_HMAC_KEY")
    if hmac_key:
        state["state_hmac"] = _compute_state_hmac(state, hmac_key.encode("utf-8"))

    rendered = json.dumps(state, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    if args.dry_run:
        sys.stdout.write(rendered)
        return 0

    state_path.write_text(rendered, encoding="utf-8")
    sys.stdout.write(f"OK: transitioned {executing_phase} -> {next_phase}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

