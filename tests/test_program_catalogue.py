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


def test_the_p27_program_lists_every_run_that_sent_it():
    """Kickoff 34b's main job named its position-1 program in main.json's meta (Amendment A8, at the author's
    request); Kickoff 37 sent it four times and Kickoff 38 once."""
    row = next(line for line in (DATA / "PROGRAMS.md").read_text().splitlines() if "k37-P27-A-no.qasm" in line)
    uses = row.split(" | ")[2].split("<br>")
    assert uses[0].startswith("Kickoff 34b: main job, position 1, A no")
    assert sum(u.startswith("Kickoff 37:") for u in uses) == 4 and sum(u.startswith("Kickoff 38:") for u in uses) == 1
