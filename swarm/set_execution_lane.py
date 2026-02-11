#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Optional

try:
    import fcntl  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover
    fcntl = None  # type: ignore[assignment]

try:
    from .validate_state import (
        LANE_REQUIRED_PHASE_SEQUENCE,
        ValidationError,
        _canonicalize_phase,
        _compute_state_hmac,
        _normalize_lane,
    )
except ImportError:  # pragma: no cover
    from validate_state import (  # type: ignore
        LANE_REQUIRED_PHASE_SEQUENCE,
        ValidationError,
        _canonicalize_phase,
        _compute_state_hmac,
        _normalize_lane,
    )


def _load_json(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError as e:
        raise ValidationError(f"Missing state file: {path}") from e
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON in {path}: {e}") from e
    if not isinstance(data, dict):
        raise ValidationError(f"State file must be a JSON object, got {type(data).__name__}")
    return data


def _lock_exclusive(f) -> None:
    if fcntl is None:
        return
    fcntl.flock(f, fcntl.LOCK_EX)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Set swarm execution lane (FULL or FAST_UI) with a hard-lock check.\n"
            "This updates execution_lane and required_phase_sequence together."
        )
    )
    parser.add_argument("--state", default="swarm_state.json", help="Path to swarm_state.json")
    parser.add_argument("--lane", required=True, help="FULL or FAST_UI")
    parser.add_argument("--reason", default="", help="Reason for lane switch")
    parser.add_argument("--force", action="store_true", help="Allow switching lane outside ARCHITECT boundary")
    parser.add_argument("--dry-run", action="store_true", help="Validate and print new state without writing")
    args = parser.parse_args(argv)

    state_path = Path(args.state)
    with state_path.open("r+", encoding="utf-8") as f:
        _lock_exclusive(f)
        original = f.read()
        state = _load_json(state_path)

        lane = _normalize_lane(args.lane)
        current_lane = _normalize_lane(state.get("execution_lane"))
        if lane == current_lane:
            print(f"OK: execution_lane already {lane}")
            return 0

        cur_raw = state.get("current_phase")
        nxt_raw = state.get("next_phase")
        if not isinstance(cur_raw, str) or not isinstance(nxt_raw, str):
            raise ValidationError("State must contain string fields current_phase and next_phase.")

        current_phase = _canonicalize_phase(cur_raw)
        next_phase = _canonicalize_phase(nxt_raw)

        if not args.force:
            # Lane switch must happen at architecture boundary to avoid partial mixed cycles.
            safe_current = {"INIT", "ARCHITECT", "COMPLETE"}
            safe_next = {"ARCHITECT", "FRONTEND", "QA_CONTRACT"}
            if current_phase not in safe_current or next_phase not in safe_next:
                raise ValidationError(
                    "Lane switch is only allowed at architecture boundary "
                    f"(current={current_phase}, next={next_phase}). Use --force only for recovery."
                )

        state["execution_lane"] = lane
        state["required_phase_sequence"] = list(LANE_REQUIRED_PHASE_SEQUENCE[lane])
        if args.reason:
            state["lane_reason"] = args.reason

        hmac_key = os.environ.get("SWARM_STATE_HMAC_KEY")
        if hmac_key:
            state["state_hmac"] = _compute_state_hmac(state, hmac_key.encode("utf-8"))

        rendered = json.dumps(state, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
        if args.dry_run:
            print(rendered)
            return 0

        backup_path = state_path.with_suffix(state_path.suffix + ".bak")
        try:
            backup_path.write_text(original, encoding="utf-8")
        except OSError:
            pass

        f.seek(0)
        f.truncate()
        f.write(rendered)
        f.flush()
        try:
            os.fsync(f.fileno())
        except OSError:
            pass

        print(f"OK: execution_lane switched {current_lane} -> {lane}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())

