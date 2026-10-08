# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""Every JSON file in data/ has the six meta fields that apply to its kind, and "not applicable" for the others."""

import re

import pytest

from manacitra import archive

NA = "not applicable"
STANDARD = ("processor", "provider", "kickoff", "utc", "shots_per_circuit", "sources")
try:
    FILES = sorted(p.relative_to(archive.data_dir()).as_posix() for p in archive.records())
except archive.DataNotFound as e:
    pytest.skip(f"needs the dataset: {e}", allow_module_level=True)


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
    assert m["kickoff"].startswith("Kickoff") and m["utc"][:10] in ("2026-10-05", "2026-10-06", "2026-10-07")
    assert m["shots_per_circuit"] == NA or isinstance(m["shots_per_circuit"], int)


@pytest.mark.parametrize("path", FILES)
def test_every_counts_record_declares_its_bit_reading(path):
    """Amendment A8, R1: a record with counts says how to read them, in meta.bit_reading, one of four literals."""
    rec = archive.load(path)
    if "counts" in rec:
        assert rec["meta"].get("bit_reading") in (
            "qiskit-adjacent",
            "openquantum-reversed",
            "braket-measured-qubits",
            "per-pair",
        ), path
    else:
        assert "bit_reading" not in rec["meta"], path


def test_the_signing_bundles_are_not_records():
    """The signing workflow writes FILE.sigstore.json beside each signed file; those are signatures, not run records."""
    assert archive.is_bundle("ibm_fez/k31-map.json.sigstore.json") and not archive.is_bundle("ibm_fez/k31-map.json")
    assert not any(archive.is_bundle(p) for p in archive.records())
    assert "k31-map.json.sigstore" not in archive.fez_or_kingston("ibm_fez")
