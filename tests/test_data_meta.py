# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""Every JSON file in data/ has the six meta fields that apply to its kind, and "not applicable" for the others."""

import re

import pytest

from manacitra import archive

NA = "not applicable"
STANDARD = ("processor", "provider", "kickoff", "utc", "shots_per_circuit", "sources")
FILES = sorted(p.relative_to(archive.data_dir()).as_posix() for p in archive.data_dir().rglob("*.json"))


def test_the_index_lists_every_file():
    index = (archive.data_dir() / "README.md").read_text()
    assert FILES and all(f"`{f}`" in index for f in FILES)


@pytest.mark.parametrize("path", FILES)
def test_the_six_fields(path):
    m = archive.load(path)["meta"]
    assert all(m.get(k) not in (None, "") for k in STANDARD), [k for k in STANDARD if m.get(k) in (None, "")]
    if m["sources"] != NA:
        assert all(re.fullmatch(r"[0-9a-f]{64}", s["sha256"]) for s in m["sources"])


@pytest.mark.parametrize("path", [f for f in FILES if f.endswith("coupling-map.json")])
def test_coupling_maps_name_their_snapshot(path):
    m = archive.load(path)["meta"]
    assert (m["kickoff"], m["utc"], m["shots_per_circuit"]) == (NA, NA, NA)
    assert m["snapshot"]["package"] == "qiskit-ibm-runtime" and m["snapshot"]["version"] and m["snapshot"]["class"]
    assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", m["extracted_utc"])


@pytest.mark.parametrize("path", [f for f in FILES if not f.endswith("coupling-map.json")])
def test_run_records_name_a_kickoff_and_a_time(path):
    m = archive.load(path)["meta"]
    assert m["kickoff"].startswith("Kickoff") and m["utc"].startswith("2026-10-05")
    assert m["shots_per_circuit"] == NA or isinstance(m["shots_per_circuit"], int)
