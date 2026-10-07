# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""Amendment A8, R2: data/PROGRAMS.md indexes every program file under data/, from the run records."""

import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import program_catalogue  # noqa: E402

DATA = ROOT / "data"


def test_the_catalogue_is_current():
    assert (DATA / "PROGRAMS.md").read_text() == program_catalogue.catalogue()


def test_every_program_file_has_a_row_and_every_row_an_existing_file():
    text = (DATA / "PROGRAMS.md").read_text()
    rows = dict(re.findall(r"^\| `([^`]+)` \|.*\| `([0-9a-f]{64})` \|$", text, re.M))
    files = {p.relative_to(DATA).as_posix() for p in DATA.rglob("*") if p.suffix in (".qasm", ".quil")}
    assert set(rows) == files and len(files) == 187
    for rel, sha in rows.items():
        assert hashlib.sha256((DATA / rel).read_bytes()).hexdigest() == sha, rel


def test_the_catalogue_is_in_the_checksums():
    assert re.search(r"^[0-9a-f]{64}  PROGRAMS\.md$", (DATA / "SHA256SUMS").read_text(), re.M)
