# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""Amendment A17: the four circuits of Kickoffs 43 to 47 are fetched, not copied. tools/fetch_reuse_circuits.py reads
their sources from the record and recomputes their exact ideal outputs; these tests check it without the network."""

import importlib.util
from pathlib import Path

import pytest

from manacitra import archive

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("fetch_reuse_circuits", ROOT / "tools" / "fetch_reuse_circuits.py")
fetch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fetch)

XOR3 = """OPENQASM 2.0;
include "qelib1.inc";
qreg q[4];
creg c[4];
x q[0];
x q[2];
cx q[0],q[1];
cx q[2],q[1];
"""


def test_the_ideal_of_a_file_without_measurements():
    """Measured as the runs measured such a file: every qubit in a gate, the k-th into classical bit k. Qubit 3 takes
    no gate and is not measured; q1 = q0 xor q2 = 0."""
    assert fetch.exact_distribution(XOR3, [0, 1, 2]) == pytest.approx({"101": 1.0})
    assert fetch.exact_distribution(XOR3 + "measure q[1] -> c[0];\n", [0]) == pytest.approx({"0": 1.0})


def test_the_sources_are_pinned():
    circuits = archive.load("ibm_fez/k43-reuse.json")["circuits"]
    urls = {name: fetch.raw_url(c["source"]) for name, c in circuits.items()}
    assert urls["XOR_5"] == (
        "https://raw.githubusercontent.com/ruadapt/CaQR/0b935d962bffa6e845f2b9548b768f2f558cbe18/benchmarks/xor5_254.qasm"
    )
    assert urls["Mul_13"].startswith(
        "https://raw.githubusercontent.com/pnnl/QASMBench/357b942396d5c2b7cbc1c229c585a6ef5ccaebac/"
    )
    assert fetch.total_variation({"0": 0.5, "1": 0.5}, {"0": 1.0}) == 0.5


def test_a_nonempty_folder_is_refused(tmp_path):
    (tmp_path / "x").write_text("")
    assert fetch.main([str(tmp_path)]) == 2
