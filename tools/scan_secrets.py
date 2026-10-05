# Copyright 2026 Anish Patel
# SPDX-License-Identifier: Apache-2.0
"""The identifier scan: fails on any credential, identifier, personal path or out-of-scope word in the tree.

    python tools/scan_secrets.py            scan every file git tracks (or every file, outside a repository)
    python tools/scan_secrets.py --staged   scan only the files staged for commit (the pre-commit hook)
    python tools/scan_secrets.py PATH ...   scan the given files or directories

Exit status 0 when clean, 1 when anything matches. A finding prints the file, the line, the pattern's name and a
masked excerpt; the matched value itself is never printed in full.

The user name of whoever runs the scan is added as a pattern at run time, outside CI (on a CI runner the user name
is a common word). Extra literal values can be passed in the environment variable MANACITRA_SCAN_EXTRA, separated by
commas; they are used and never written anywhere.
"""

from __future__ import annotations

import argparse
import getpass
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scan_patterns import ALLOW, PATTERNS, SKIP_DIRS, SKIP_NAME_ENDINGS, SKIP_SUFFIXES  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def _compile(entries):
    return [(name, re.compile(rx, re.IGNORECASE if "i" in flags else 0)) for name, rx, flags in entries]


def runtime_patterns() -> list[tuple[str, re.Pattern]]:
    out = []
    if not os.environ.get("CI"):
        try:
            user = getpass.getuser()
        except Exception:
            user = ""
        if len(user) >= 3:
            out.append(("local-user-name", re.compile(rf"\b{re.escape(user)}\b", re.IGNORECASE)))
    for i, value in enumerate(v.strip() for v in os.environ.get("MANACITRA_SCAN_EXTRA", "").split(",")):
        if len(value) >= 3:
            out.append((f"extra-{i + 1}", re.compile(re.escape(value), re.IGNORECASE)))
    return out


def mask(text: str) -> str:
    if len(text) <= 4:
        return "*" * len(text)
    return text[:2] + "*" * (len(text) - 4) + text[-2:]


def scan_text(text: str, patterns, allow) -> list[tuple[int, str, str]]:
    findings = []
    allowed_spans = [m.span() for _, rx in allow for m in rx.finditer(text)]

    def is_allowed(span):
        return any(a <= span[0] and span[1] <= b for a, b in allowed_spans)

    for name, rx in patterns:
        for m in rx.finditer(text):
            if is_allowed(m.span()):
                continue
            line = text.count("\n", 0, m.start()) + 1
            findings.append((line, name, mask(m.group(0))))
    return findings


def tracked_files(root: Path) -> list[Path]:
    try:
        out = subprocess.run(
            ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            cwd=root,
            capture_output=True,
            check=True,
        ).stdout
        return [root / p for p in out.decode().split("\0") if p]
    except (OSError, subprocess.CalledProcessError):
        return [p for p in root.rglob("*") if p.is_file()]


def staged_files(root: Path) -> list[Path]:
    out = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "-z", "--diff-filter=ACMR"],
        cwd=root,
        capture_output=True,
        check=True,
    ).stdout
    return [root / p for p in out.decode().split("\0") if p]


def expand(paths: list[Path]) -> list[Path]:
    files = []
    for p in paths:
        if p.is_dir():
            files += [f for f in p.rglob("*") if f.is_file()]
        elif p.is_file():
            files.append(p)
    return files


def skipped(path: Path) -> bool:
    return (
        bool(set(path.parts) & SKIP_DIRS)
        or path.suffix.lower() in SKIP_SUFFIXES
        or path.name.endswith(SKIP_NAME_ENDINGS)
    )


def scan_files(files: list[Path]) -> dict[str, list[tuple[int, str, str]]]:
    patterns = _compile(PATTERNS) + runtime_patterns()
    allow = _compile(ALLOW)
    result = {}
    for f in files:
        if skipped(f) or not f.exists():
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        hits = scan_text(text, patterns, allow)
        if hits:
            try:
                key = str(f.relative_to(ROOT))
            except ValueError:
                key = str(f)
            result[key] = hits
    return result


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("paths", nargs="*", type=Path)
    ap.add_argument("--staged", action="store_true", help="scan only the files staged for commit")
    a = ap.parse_args(argv)
    if a.staged:
        files = staged_files(ROOT)
    elif a.paths:
        files = expand([p.resolve() for p in a.paths])
    else:
        files = tracked_files(ROOT)
    result = scan_files(files)
    n_files = sum(1 for f in files if not skipped(f))
    if not result:
        print(f"identifier scan: clean ({n_files} files)")
        return 0
    for f, hits in sorted(result.items()):
        for line, name, excerpt in hits:
            print(f"{f}:{line}: {name}: {excerpt}")
    print(f"identifier scan: {sum(len(h) for h in result.values())} finding(s) in {len(result)} file(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
