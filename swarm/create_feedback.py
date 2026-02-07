#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Optional

from validate_state import ValidationError, _canonicalize_phase, _load_json


def _utc_now_compact() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).strftime("%Y%m%dT%H%M%SZ")


def _sha256_file(path: Path) -> str:
    h = sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _extract_failure_snippet(text: str, max_lines: int = 80) -> str:
    lines = text.splitlines()
    interesting: list[str] = []
    pat = re.compile(r"(FAIL|ERROR|Error:|AssertionError|Traceback|Unhandled|Exception)", re.IGNORECASE)
    for ln in lines:
        if pat.search(ln):
            interesting.append(ln)
    if not interesting:
        # Fallback: tail
        interesting = lines[-max_lines:]
    if len(interesting) > max_lines:
        interesting = interesting[-max_lines:]
    return "\n".join(interesting)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Create an Analyst feedback artifact (fix_required.md).")
    parser.add_argument("--state", default="swarm_state.json", help="Path to swarm_state.json")
    parser.add_argument("--task-id", default="", help="Task id (recommended).")
    parser.add_argument("--phase", default="", help="Phase name (defaults to swarm_state.next_phase).")
    parser.add_argument("--run-id", default="", help="CI run id (Level 2) or local run id (Level 1).")
    parser.add_argument("--evidence", default="", help="Path to evidence file (raw test output/attestation).")
    parser.add_argument("--summary", default="", help="1-3 sentence summary.")
    parser.add_argument("--output", default="", help="Output path. Default: tasks/feedback/<task-id>/fix_required.md or tasks/feedback/fix_required.md")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite output if it exists (discouraged).")
    args = parser.parse_args(argv)

    state = _load_json(Path(args.state))
    next_phase_raw = state.get("next_phase")
    if not isinstance(next_phase_raw, str):
        raise ValidationError("swarm_state.json.next_phase must be a string.")
    inferred_phase = _canonicalize_phase(next_phase_raw)

    phase = _canonicalize_phase(args.phase) if args.phase else inferred_phase
    feedback_id = f"FB-{_utc_now_compact()}"

    evidence_obj = None
    snippet = ""
    if args.evidence:
        evidence_path = Path(args.evidence)
        if not evidence_path.exists():
            raise ValidationError(f"Evidence file not found: {evidence_path}")
        digest = _sha256_file(evidence_path)
        evidence_obj = {"path": str(evidence_path), "sha256": digest}
        try:
            text = evidence_path.read_text(encoding="utf-8", errors="replace")
            snippet = _extract_failure_snippet(text)
        except Exception:
            snippet = ""

    if args.output:
        out_path = Path(args.output)
    else:
        if args.task_id:
            out_path = Path("tasks/feedback") / args.task_id / "fix_required.md"
        else:
            out_path = Path("tasks/feedback/fix_required.md")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists() and not args.overwrite:
        raise ValidationError(f"Feedback file already exists (immutability): {out_path}. Use --overwrite only if necessary.")

    md = []
    md.append("# FIX REQUIRED")
    md.append("")
    md.append("## Metadata")
    if args.task_id:
        md.append(f"- task_id: {args.task_id}")
    md.append(f"- feedback_id: {feedback_id}")
    md.append(f"- phase: {phase}")
    if args.run_id:
        md.append(f"- run_id: {args.run_id}")
    if evidence_obj:
        md.append(f"- evidence_path: `{evidence_obj['path']}`")
        md.append(f"- evidence_sha256: `{evidence_obj['sha256']}`")
    md.append("")
    md.append("## Summary")
    md.append(args.summary.strip() or "CI/test execution failed. Fixes below are mandatory.")
    md.append("")
    md.append("## Evidence (Authoritative)")
    md.append("- Required checks/gates: <fill explicitly>")
    md.append("- Failing tests/errors: <fill explicitly>")
    md.append("")
    if snippet.strip():
        md.append("## Failure Snippet (From Evidence)")
        md.append("```text")
        md.append(snippet.rstrip("\n"))
        md.append("```")
        md.append("")
    md.append("## Required Fixes (Non-Negotiable)")
    md.append("1. <file/path>: <exact change required>")
    md.append("2. <file/path>: <exact change required>")
    md.append("")
    md.append("## Exit Criteria (Gate Conditions)")
    md.append("- All required gates are green.")
    md.append("- Provide the new run_id/evidence reference in the phase report.")
    md.append("")

    out_path.write_text("\n".join(md).strip() + "\n", encoding="utf-8")
    sys.stdout.write(f"OK: wrote feedback {feedback_id} -> {out_path}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

