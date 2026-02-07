#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hmac
import os
import re
import sys
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Optional


HMAC_ENV = "SWARM_LOG_HMAC_KEY"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _ts(now: datetime) -> str:
    return now.isoformat().replace("+00:00", "Z")


def _sha256_bytes(data: bytes) -> str:
    return sha256(data).hexdigest()


def _read_bytes(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except FileNotFoundError as e:
        raise SystemExit(f"ERROR: input not found: {path}") from e


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _extract_tail_lines(text: str, max_lines: int) -> str:
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text
    return "\n".join(lines[-max_lines:])


def _extract_head_lines(text: str, max_lines: int) -> str:
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text
    return "\n".join(lines[:max_lines])


def _find_last_hmac(ci_logs_md: str) -> str:
    # Convention: each run block includes a line "- hmac: <hex>"
    matches = re.findall(r"^- hmac: ([0-9a-f]{64})\\s*$", ci_logs_md, flags=re.MULTILINE)
    return matches[-1] if matches else ""


def _compute_block_hmac(key: bytes, prev_hmac: str, block: str) -> str:
    payload = (prev_hmac + "\n" + block).encode("utf-8")
    return hmac.new(key, payload, digestmod="sha256").hexdigest()


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Capture real test stdout/stderr and append to tasks/logs/CI_LOGS.md (append-only).")
    parser.add_argument("--input", required=True, help="Path to raw stdout/stderr capture file.")
    parser.add_argument("--command", required=True, help="Command that produced this output (for evidence).")
    parser.add_argument("--exit-code", required=True, type=int, help="Process exit code for the command.")
    parser.add_argument("--actor", default="orchestrator", help="Actor that executed the command (default: orchestrator).")
    parser.add_argument("--phase", default="", help="Phase during which the command was executed (optional).")
    parser.add_argument("--task-id", default="", help="Task id (optional).")
    parser.add_argument("--out", default="tasks/logs/CI_LOGS.md", help="CI log markdown path (append-only).")
    parser.add_argument("--evidence-dir", default="tasks/evidence/test-runs", help="Directory to store immutable raw outputs.")
    parser.add_argument("--max-snippet-lines", type=int, default=200, help="Lines to include for head/tail snippets in CI_LOGS.md.")
    args = parser.parse_args(argv)

    now = _utc_now()
    input_path = Path(args.input)
    out_path = Path(args.out)
    evidence_dir = Path(args.evidence_dir)

    raw = _read_bytes(input_path)
    digest = _sha256_bytes(raw)
    ts_compact = now.strftime("%Y%m%dT%H%M%SZ")
    run_id = f"L1-{ts_compact}-{digest[:8]}"

    _ensure_dir(out_path.parent)
    _ensure_dir(evidence_dir)

    evidence_path = evidence_dir / f"{run_id}_{digest}.log"
    if not evidence_path.exists():
        evidence_path.write_bytes(raw)

    text = raw.decode("utf-8", errors="replace")
    head = _extract_head_lines(text, args.max_snippet_lines)
    tail = _extract_tail_lines(text, args.max_snippet_lines)

    # Construct a deterministic block (excluding hmac) for optional signing.
    block_lines = [
        f"## Run: {run_id}",
        f"- timestamp_utc: {_ts(now)}",
        f"- actor: {args.actor}",
        f"- phase: {args.phase}",
        f"- task_id: {args.task_id}",
        f"- command: `{args.command}`",
        f"- exit_code: {args.exit_code}",
        f"- sha256: {digest}",
        f"- evidence: `{evidence_path}`",
        "",
        "<details>",
        "<summary>stdout/stderr snippets (head + tail)</summary>",
        "",
        "```text",
        "### HEAD",
        head.rstrip("\n"),
        "",
        "### TAIL",
        tail.rstrip("\n"),
        "```",
        "</details>",
        "",
    ]
    block = "\n".join(block_lines)

    existing = out_path.read_text(encoding="utf-8") if out_path.exists() else ""
    prev_hmac = _find_last_hmac(existing)

    key = os.environ.get(HMAC_ENV)
    hmac_line = ""
    if key:
        sig = _compute_block_hmac(key.encode("utf-8"), prev_hmac, block)
        hmac_line = f"- hmac: {sig}\n- prev_hmac: {prev_hmac}\n"

    # Append-only write.
    with out_path.open("a", encoding="utf-8") as f:
        if existing and not existing.endswith("\n"):
            f.write("\n")
        if hmac_line:
            # Put the hmac lines immediately after the header block for easy extraction.
            # We inject them right after the "evidence" line by adding them at the top of the block.
            # Minimal invasive: write header, then hmac, then rest.
            # Reconstruct block with hmac inserted after evidence line.
            lines = block.splitlines(keepends=False)
            # Find evidence line index to insert after.
            insert_at = None
            for i, line in enumerate(lines):
                if line.startswith("- evidence:"):
                    insert_at = i + 1
                    break
            if insert_at is None:
                f.write(block)
            else:
                with_hmac = "\n".join(lines[:insert_at] + hmac_line.rstrip("\n").splitlines() + lines[insert_at:]) + "\n"
                f.write(with_hmac)
        else:
            f.write(block + "\n")

    sys.stdout.write(f"OK: captured {run_id} (exit_code={args.exit_code}, sha256={digest})\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

