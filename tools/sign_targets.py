# Copyright 2026 Anish Patel
# SPDX-License-Identifier: Apache-2.0
"""List the files the signing workflow signs: every *.commit.json, and every file in data/, that has no Sigstore
bundle beside it yet or that changed between two commits. Prints them separated by spaces (none: an empty line).

    python tools/sign_targets.py [--before SHA] [--after SHA]
"""

import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUNDLE = ".sigstore.json"


def git(*args) -> list[str]:
    out = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
    return [line for line in out.stdout.splitlines() if line] if out.returncode == 0 else []


def is_target(path: str) -> bool:
    if path.endswith(BUNDLE):
        return False
    return path.endswith(".commit.json") or path.startswith("data/")


def targets(before: str | None, after: str | None) -> list[str]:
    tracked = [p for p in git("ls-files") if is_target(p)]
    changed = set()
    if before and after and set(before) != {"0"}:
        changed = set(git("diff", "--name-only", before, after))
    return sorted(p for p in tracked if not (ROOT / (p + BUNDLE)).exists() or p in changed)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--before")
    ap.add_argument("--after")
    a = ap.parse_args()
    print(" ".join(targets(a.before, a.after)))
