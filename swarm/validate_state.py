#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hmac
import json
import os
import sys
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any, Iterable, Optional


CANONICAL_PHASES: set[str] = {
    "INIT",
    "ARCHITECT",
    "QA_CONTRACT",
    "BACKEND",
    "ANALYST_CI_GATE",
    "FRONTEND",
    "QA_E2E",
    "ANALYST_FINAL",
    "COMPLETE",
}

# Accept legacy phase names and collapse sub-phases to canonical stages.
PHASE_ALIASES: dict[str, str] = {
    "ARCHITECT_DESIGN": "ARCHITECT",
    "ARCHITECT_PORT_FIX": "ARCHITECT",
    "QA_CONTRACT_TESTS": "QA_CONTRACT",
    "BACKEND_IMPLEMENTATION": "BACKEND",
    "BACKEND_HARDENING_COMPLETE": "BACKEND",
    "ANALYST_AUDIT": "ANALYST_CI_GATE",
    "FRONTEND_IMPLEMENTATION": "FRONTEND",
    "QA_E2E_VALIDATION": "QA_E2E",
    "QA_VALIDATION_COMPLETE": "QA_E2E",
    "ANALYST_FINAL_SIGNOFF": "ANALYST_FINAL",
    "QA_VALIDATION": "QA_E2E",
}

PHASE_TO_ROLE: dict[str, str] = {
    "INIT": "orchestrator",
    "ARCHITECT": "architect",
    "QA_CONTRACT": "qa",
    "BACKEND": "backend",
    "ANALYST_CI_GATE": "analyst",
    "FRONTEND": "frontend",
    "QA_E2E": "qa",
    "ANALYST_FINAL": "analyst",
    "COMPLETE": "orchestrator",
}

DEFAULT_REQUIRED_PHASE_SEQUENCE: list[str] = [
    "ARCHITECT",
    "QA_CONTRACT",
    "BACKEND",
    "ANALYST_CI_GATE",
    "FRONTEND",
    "QA_E2E",
    "ANALYST_FINAL",
]

EXECUTION_LANES: set[str] = {"FULL", "FAST_UI"}

LANE_REQUIRED_PHASE_SEQUENCE: dict[str, list[str]] = {
    "FULL": list(DEFAULT_REQUIRED_PHASE_SEQUENCE),
    "FAST_UI": [
        "ARCHITECT",
        "FRONTEND",
        "QA_E2E",
        "ANALYST_FINAL",
    ],
}

ROLE_ALIASES: dict[str, str] = {
    "arch": "architect",
    "architect": "architect",
    "qa": "qa",
    "backend": "backend",
    "dev": "backend",
    "developer": "backend",
    "frontend": "frontend",
    "analyst": "analyst",
    "orchestrator": "orchestrator",
    "ci": "orchestrator",
}


class ValidationError(Exception):
    pass


def _canonicalize_phase(raw: str) -> str:
    p = (raw or "").strip()
    if not p:
        raise ValidationError("Empty phase value is not allowed.")

    u = p.upper()
    if u in CANONICAL_PHASES:
        return u
    if u in PHASE_ALIASES:
        return PHASE_ALIASES[u]

    # Fallback collapsing: keep the workflow strict while tolerating legacy sub-phase names.
    if u.startswith("ARCHITECT"):
        return "ARCHITECT"
    if u.startswith("BACKEND"):
        return "BACKEND"
    if u.startswith("FRONTEND"):
        return "FRONTEND"
    if u.startswith("ANALYST_FINAL") or (u.startswith("ANALYST") and "FINAL" in u):
        return "ANALYST_FINAL"
    if u.startswith("ANALYST"):
        return "ANALYST_CI_GATE"
    if u.startswith("QA"):
        if "CONTRACT" in u:
            return "QA_CONTRACT"
        if "E2E" in u or "VALIDATION" in u:
            return "QA_E2E"
        raise ValidationError(
            f"Ambiguous QA phase name: {raw!r}. Use 'QA_CONTRACT' or 'QA_E2E' (or add an alias)."
        )

    raise ValidationError(f"Unknown phase name: {raw!r}. Add it to PHASE_ALIASES or use a canonical phase.")


def _normalize_role(raw: str) -> str:
    r = (raw or "").strip().lower()
    if not r:
        raise ValidationError("Role is required.")
    if r in ROLE_ALIASES:
        return ROLE_ALIASES[r]
    raise ValidationError(f"Unknown role: {raw!r}. Expected one of: {sorted(set(ROLE_ALIASES.values()))}")


def _normalize_lane(raw: Any) -> str:
    if raw is None:
        return "FULL"
    if not isinstance(raw, str):
        raise ValidationError(f"execution_lane must be a string when present, got: {type(raw).__name__}")
    lane = raw.strip().upper()
    if lane in EXECUTION_LANES:
        return lane
    raise ValidationError(f"Unknown execution_lane: {raw!r}. Allowed lanes: {sorted(EXECUTION_LANES)}")


def _load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as e:
        raise ValidationError(f"Missing required file: {path}") from e
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON in {path}: {e}") from e
    if not isinstance(data, dict):
        raise ValidationError(f"State file must contain a JSON object, got: {type(data).__name__}")
    return data


def _iter_history_phases(history: Any) -> Iterable[str]:
    if history is None:
        return []
    if not isinstance(history, list):
        raise ValidationError("'history' must be a JSON array.")
    for item in history:
        if isinstance(item, str):
            yield item
            continue
        if isinstance(item, dict) and isinstance(item.get("phase"), str):
            yield item["phase"]
            continue
        raise ValidationError(
            "history entries must be strings or objects with a string 'phase' field."
        )


def _compute_state_hmac(state: dict[str, Any], key: bytes) -> str:
    # Stable canonical bytes: sorted keys, no whitespace. Exclude existing integrity fields.
    payload = dict(state)
    payload.pop("state_hmac", None)
    integrity = payload.get("integrity")
    if isinstance(integrity, dict):
        integrity = dict(integrity)
        integrity.pop("hmac", None)
        payload["integrity"] = integrity
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hmac.new(key, raw, digestmod="sha256").hexdigest()


def _validate_required_sequence(
    timeline: list[str],
    required_sequence: list[str],
) -> None:
    # Ensure no later required phase appears without all earlier required phases present.
    missing_prefix: list[str] = []
    for phase in required_sequence:
        if phase in timeline:
            if missing_prefix:
                raise ValidationError(
                    "Required phase order violated. "
                    f"Found {phase} but missing earlier required phases: {missing_prefix}"
                )
        else:
            missing_prefix.append(phase)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Validate swarm_state.json and role/phase invariants.")
    parser.add_argument("--state", default="swarm_state.json", help="Path to swarm_state.json")
    parser.add_argument("--role", help="Acting role to validate against next_phase (architect|qa|backend|analyst|frontend).")
    parser.add_argument("--require-hmac", action="store_true", help="Fail if HMAC key is configured but state is unsigned/invalid.")
    parser.add_argument("--json", action="store_true", help="Emit a machine-readable JSON result.")
    args = parser.parse_args(argv)

    state_path = Path(args.state)
    state = _load_json(state_path)

    errors: list[str] = []
    warnings: list[str] = []

    is_locked = state.get("is_locked")
    if is_locked not in (True, False):
        errors.append("'is_locked' must be a boolean.")
    elif is_locked is True:
        errors.append("State is locked (is_locked=true). Orchestrator must unlock explicitly.")

    raw_current = state.get("current_phase")
    raw_next = state.get("next_phase")
    if not isinstance(raw_current, str):
        errors.append("'current_phase' must be a string.")
        canonical_current = None
    else:
        try:
            canonical_current = _canonicalize_phase(raw_current)
        except ValidationError as e:
            errors.append(str(e))
            canonical_current = None

    if not isinstance(raw_next, str):
        errors.append("'next_phase' must be a string.")
        canonical_next = None
    else:
        try:
            canonical_next = _canonicalize_phase(raw_next)
        except ValidationError as e:
            errors.append(str(e))
            canonical_next = None

    try:
        lane = _normalize_lane(state.get("execution_lane"))
    except ValidationError as e:
        errors.append(str(e))
        lane = "FULL"
    lane_default_seq = list(LANE_REQUIRED_PHASE_SEQUENCE.get(lane, DEFAULT_REQUIRED_PHASE_SEQUENCE))

    # Required phase sequence is lane-bound by default.
    required_seq_raw = state.get("required_phase_sequence")
    if required_seq_raw is None:
        required_seq = list(lane_default_seq)
        warnings.append(
            "Missing 'required_phase_sequence'; using lane default sequence "
            f"for execution_lane={lane!r}."
        )
    elif isinstance(required_seq_raw, list) and all(isinstance(x, str) for x in required_seq_raw):
        try:
            required_seq = [_canonicalize_phase(x) for x in required_seq_raw]
        except ValidationError as e:
            errors.append(f"Invalid required_phase_sequence: {e}")
            required_seq = list(lane_default_seq)
        else:
            allow_custom = bool(state.get("allow_custom_sequence") is True)
            if required_seq != lane_default_seq and not allow_custom:
                errors.append(
                    "required_phase_sequence must match execution_lane default unless "
                    "allow_custom_sequence=true."
                )
            elif required_seq != lane_default_seq and allow_custom:
                warnings.append(
                    "Using custom required_phase_sequence with allow_custom_sequence=true. "
                    "Ensure this is intentional."
                )
    else:
        errors.append("'required_phase_sequence' must be an array of strings when present.")
        required_seq = list(lane_default_seq)

    history_phases_raw = list(_iter_history_phases(state.get("history")))
    canonical_timeline: list[str] = []
    for p in history_phases_raw:
        try:
            canonical_timeline.append(_canonicalize_phase(p))
        except ValidationError as e:
            errors.append(f"history: {e}")

    # Ensure current_phase is represented in the timeline (some legacy files duplicate it in history; that's fine).
    if canonical_current and (not canonical_timeline or canonical_timeline[-1] != canonical_current):
        canonical_timeline.append(canonical_current)

    if canonical_timeline:
        try:
            _validate_required_sequence(canonical_timeline, required_seq)
        except ValidationError as e:
            errors.append(str(e))

    # Prevent skipping required phases via next_phase.
    if canonical_next and canonical_next in required_seq:
        next_idx = required_seq.index(canonical_next)
        completed = set(canonical_timeline)
        missing = [p for p in required_seq[:next_idx] if p not in completed]
        if missing:
            errors.append(
                f"Phase skip detected: next_phase={canonical_next} but missing required phases: {missing}"
            )

    # Lane-specific phase constraints.
    if lane == "FAST_UI":
        disallowed = {"QA_CONTRACT", "BACKEND", "ANALYST_CI_GATE"}
        if canonical_current in disallowed:
            errors.append(
                f"execution_lane=FAST_UI does not allow current_phase={canonical_current}. "
                "Use execution_lane=FULL for backend/contract cycles."
            )
        if canonical_next in disallowed:
            errors.append(
                f"execution_lane=FAST_UI does not allow next_phase={canonical_next}. "
                "Use execution_lane=FULL for backend/contract cycles."
            )

    # Role-to-next_phase validation.
    if canonical_next:
        expected_role = PHASE_TO_ROLE.get(canonical_next)
        if expected_role is None:
            errors.append(f"Internal error: no role mapping for phase {canonical_next}.")
        elif args.role:
            try:
                role = _normalize_role(args.role)
            except ValidationError as e:
                errors.append(str(e))
            else:
                if role != expected_role:
                    errors.append(
                        f"Role/phase mismatch: role={role!r} cannot execute next_phase={canonical_next!r}. "
                        f"Expected role: {expected_role!r}."
                    )

    # Optional tamper-evidence: HMAC signing of swarm_state.json
    hmac_key = os.environ.get("SWARM_STATE_HMAC_KEY")
    if hmac_key:
        stored_hmac = state.get("state_hmac")
        integrity = state.get("integrity")
        if isinstance(integrity, dict) and isinstance(integrity.get("hmac"), str):
            stored_hmac = integrity["hmac"]

        computed = _compute_state_hmac(state, hmac_key.encode("utf-8"))
        if not isinstance(stored_hmac, str) or not stored_hmac:
            msg = "State HMAC key is configured but swarm_state.json is not signed (missing state_hmac/integrity.hmac)."
            if args.require_hmac:
                errors.append(msg)
            else:
                warnings.append(msg)
        elif not hmac.compare_digest(stored_hmac, computed):
            errors.append("swarm_state.json integrity check failed (HMAC mismatch). File may have been edited directly.")

    ok = not errors
    if args.json:
        payload = {
            "ok": ok,
            "errors": errors,
            "warnings": warnings,
            "canonical": {
                "current_phase": canonical_current,
                "next_phase": canonical_next,
                "execution_lane": lane,
                "required_phase_sequence": required_seq,
            },
        }
        sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    else:
        for w in warnings:
            sys.stderr.write(f"WARNING: {w}\n")
        for e in errors:
            sys.stderr.write(f"ERROR: {e}\n")
        if ok and args.role and canonical_next:
            sys.stdout.write(
                f"OK: role {args.role!r} may execute next_phase {canonical_next!r}.\n"
            )
        elif ok:
            sys.stdout.write("OK: swarm_state.json is valid.\n")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
