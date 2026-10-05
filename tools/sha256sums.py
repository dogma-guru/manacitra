# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""Write, or check, data/SHA256SUMS: a plain SHA-256 of every file in data/, for catching corrupted files.

    python tools/sha256sums.py --check
    python tools/sha256sums.py --write

These hashes catch accidents only. Who published the data, and when, is shown by the Sigstore bundles that the signing
workflow writes beside each file once signing is on (docs/index.md, "Sealing and signing").
"""

import argparse
import hashlib
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
SUMS = DATA / "SHA256SUMS"


def files() -> list[Path]:
    return sorted(p for p in DATA.rglob("*") if p.is_file() and p != SUMS and not p.name.endswith(".sigstore.json"))


def table() -> str:
    return "".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(DATA).as_posix()}\n" for p in files())


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.write:
        SUMS.write_text(table())
        print(f"wrote {SUMS} ({len(files())} files)")
        sys.exit(0)
    ok = SUMS.exists() and SUMS.read_text() == table()
    print("data/SHA256SUMS matches every file" if ok else "data/SHA256SUMS does not match data/; see --write")
    sys.exit(0 if ok else 1)
