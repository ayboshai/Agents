#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional


DEFAULT_CODE_DIRS = ("app", "components", "data", "lib", "src")


@dataclass(frozen=True)
class Finding:
    path: Path
    line_no: int
    line: str
    token: str


TOKENS: list[tuple[str, re.Pattern[str]]] = [
    ("TODO", re.compile(r"\bTODO\b")),
    ("FIXME", re.compile(r"\bFIXME\b")),
    ("placeholder", re.compile(r"\bplaceholder\b", re.IGNORECASE)),
    ("stub", re.compile(r"\bstub\b", re.IGNORECASE)),
    ("not implemented", re.compile(r"\bnot\s+implemented\b", re.IGNORECASE)),
]


def _iter_files(root: Path, dirs: Iterable[str]) -> Iterable[Path]:
    for d in dirs:
        base = root / d
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if not p.is_file():
                continue
            if any(part in {"node_modules", ".next", "dist", "build"} for part in p.parts):
                continue
            if p.suffix.lower() in {".ts", ".tsx", ".js", ".jsx", ".py"}:
                yield p


def _scan_file(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return findings
    for idx, line in enumerate(text.splitlines(), start=1):
        for token, pat in TOKENS:
            if pat.search(line):
                findings.append(Finding(path=path, line_no=idx, line=line.rstrip("\n"), token=token))
    return findings


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Fail if placeholders/TODOs exist in production code paths.")
    parser.add_argument("--root", default=".", help="Repo root")
    parser.add_argument("--dirs", nargs="*", default=list(DEFAULT_CODE_DIRS), help="Code directories to scan")
    args = parser.parse_args(argv)

    root = Path(args.root)
    findings: list[Finding] = []
    for f in _iter_files(root, args.dirs):
        findings.extend(_scan_file(f))

    if not findings:
        sys.stdout.write("OK: no placeholders/TODOs found in production code paths.\n")
        return 0

    sys.stderr.write("ERROR: placeholders/TODOs detected in production code paths.\n")
    for item in findings:
        sys.stderr.write(f"- {item.token}: {item.path}:{item.line_no}: {item.line}\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
