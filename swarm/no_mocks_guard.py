#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional


DEFAULT_TEST_DIRS = ("tests",)


@dataclass(frozen=True)
class Finding:
    path: Path
    line_no: int
    line: str
    rule: str


JS_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("vi.mock", re.compile(r"\bvi\.mock\s*\(")),
    ("jest.mock", re.compile(r"\bjest\.mock\s*\(")),
    ("mockImplementation", re.compile(r"\bmockImplementation\b")),
    ("mockReturnValue", re.compile(r"\bmockReturnValue\b")),
    ("spyOn", re.compile(r"\bspyOn\s*\(")),
    ("sinon", re.compile(r"\bsinon\b")),
]

PY_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("unittest.mock", re.compile(r"\bunittest\.mock\b")),
    ("MagicMock", re.compile(r"\bMagicMock\b")),
    ("patch(", re.compile(r"\bpatch\s*\(")),
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
        # Binary or non-utf8: ignore.
        return findings

    rules = JS_RULES if path.suffix.lower() in {".ts", ".tsx", ".js", ".jsx"} else PY_RULES
    for idx, line in enumerate(text.splitlines(), start=1):
        for rule_name, pat in rules:
            if pat.search(line):
                findings.append(Finding(path=path, line_no=idx, line=line.rstrip("\n"), rule=rule_name))
    return findings


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Fail CI if forbidden mocking patterns are present in tests.")
    parser.add_argument("--root", default=".", help="Repo root")
    parser.add_argument("--dirs", nargs="*", default=list(DEFAULT_TEST_DIRS), help="Test directories to scan")
    args = parser.parse_args(argv)

    root = Path(args.root)
    all_findings: list[Finding] = []
    for f in _iter_files(root, args.dirs):
        all_findings.extend(_scan_file(f))

    if not all_findings:
        sys.stdout.write("OK: no forbidden mock patterns found.\n")
        return 0

    sys.stderr.write("ERROR: forbidden mocking patterns detected (mocks are disallowed).\n")
    for finding in all_findings:
        sys.stderr.write(
            f"- {finding.rule}: {finding.path}:{finding.line_no}: {finding.line}\n"
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
