#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

try:
    # Support both:
    # - `python3 swarm/run_and_capture.py`
    # - `python3 -m swarm.run_and_capture`
    from .capture_test_output import main as capture_main
except ImportError:  # pragma: no cover
    from capture_test_output import main as capture_main  # type: ignore


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run a real command, capture stdout/stderr, and append immutable evidence via capture_test_output.py."
    )
    parser.add_argument("--command", required=True, help="Shell command to execute (real run).")
    parser.add_argument("--actor", default="orchestrator", help="Actor executing the command (default: orchestrator).")
    parser.add_argument("--phase", default="", help="Phase label for logging (optional).")
    parser.add_argument("--task-id", default="", help="Task id for logging (optional).")
    parser.add_argument("--out", default="tasks/logs/CI_LOGS.md", help="Append-only markdown log output path.")
    parser.add_argument("--evidence-dir", default="tasks/evidence/test-runs", help="Directory for immutable raw outputs.")
    args = parser.parse_args(argv)

    # We always capture stdout+stderr to a temp file first, then pass it to the append-only capturer.
    with tempfile.NamedTemporaryFile(prefix="swarm_cmd_", suffix=".log", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    proc = subprocess.run(
        args.command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    tmp_path.write_text(proc.stdout, encoding="utf-8")

    capture_args = [
        "--input",
        str(tmp_path),
        "--command",
        args.command,
        "--exit-code",
        str(proc.returncode),
        "--actor",
        args.actor,
        "--phase",
        args.phase,
        "--task-id",
        args.task_id,
        "--out",
        args.out,
        "--evidence-dir",
        args.evidence_dir,
    ]
    capture_rc = capture_main(capture_args)
    if capture_rc != 0:
        sys.stderr.write("ERROR: capture_test_output failed; evidence may be incomplete.\n")
        return 2

    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
