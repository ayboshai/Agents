#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from validate_state import DEFAULT_REQUIRED_PHASE_SEQUENCE, ValidationError, _canonicalize_phase, _iter_history_phases, _load_json


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _to_history_objects(legacy_history: list[str]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for p in legacy_history:
        out.append(
            {
                "phase": _canonicalize_phase(p),
                "at": None,
                "by_role": None,
                "note": f"migrated from legacy phase {p!r}",
                "legacy_phase": p,
                "evidence": None,
            }
        )
    return out


def _insert_missing_required_phases(history: list[dict[str, Any]], required_seq: list[str]) -> list[dict[str, Any]]:
    phases = [h["phase"] for h in history if isinstance(h.get("phase"), str)]
    # If a later required phase exists but an earlier required phase is missing, insert the missing one
    # immediately before the first occurrence of that later phase.
    for i, phase in enumerate(required_seq):
        if phase in phases:
            continue
        # find a later required phase that exists to anchor insertion
        anchor_idx = None
        for later in required_seq[i + 1 :]:
            if later in phases:
                anchor_idx = phases.index(later)
                break
        if anchor_idx is None:
            # Nothing later exists yet; do not insert proactively.
            continue
        insert_obj = {
            "phase": phase,
            "at": None,
            "by_role": None,
            "note": "Inserted by migration to satisfy required phase order (legacy run).",
            "legacy_phase": None,
            "evidence": None,
        }
        history.insert(anchor_idx, insert_obj)
        phases.insert(anchor_idx, phase)
    return history


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Migrate legacy swarm_state.json to the current schema (best-effort).")
    parser.add_argument("--state", default="swarm_state.json", help="Path to swarm_state.json")
    parser.add_argument("--out", default="", help="Output path. Default: overwrite --state.")
    parser.add_argument("--enforcement-level", default="L1", help="Set enforcement level (L1 or L2).")
    parser.add_argument("--task-id", default="", help="Optional task id to stamp into the migrated state.")
    args = parser.parse_args(argv)

    state_path = Path(args.state)
    legacy = _load_json(state_path)

    raw_current = legacy.get("current_phase")
    raw_next = legacy.get("next_phase")
    if not isinstance(raw_current, str) or not isinstance(raw_next, str):
        raise ValidationError("Legacy state must contain string fields: current_phase and next_phase.")

    legacy_history = list(_iter_history_phases(legacy.get("history")))
    history_objs = _to_history_objects(legacy_history)
    required_seq = list(DEFAULT_REQUIRED_PHASE_SEQUENCE)
    history_objs = _insert_missing_required_phases(history_objs, required_seq)

    migrated: dict[str, Any] = {
        "schema_version": "1.0",
        "enforcement_level": args.enforcement_level.strip().upper(),
        "task_id": args.task_id or legacy.get("task_id") or "",
        "task_path": legacy.get("task_path") or "",
        "current_phase": _canonicalize_phase(raw_current),
        "next_phase": _canonicalize_phase(raw_next),
        "is_locked": bool(legacy.get("is_locked", False)),
        "required_phase_sequence": required_seq,
        "history": history_objs,
        "migrated_at": _utc_now_iso(),
        "legacy_snapshot": {
            "raw": legacy,
        },
    }

    out_path = Path(args.out) if args.out else state_path
    out_path.write_text(json.dumps(migrated, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")
    sys.stdout.write(f"OK: migrated state written to {out_path}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

