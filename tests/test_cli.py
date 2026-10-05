# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
import importlib.util
import json

import pytest

from manacitra import archive
from manacitra.cli import main


def test_verdict_on_the_archive(capsys):
    assert main(["verdict", str(archive.data_dir() / "simulated" / "k36-arm1.json")]) == 0
    assert "verdict: NOISE" in capsys.readouterr().out


def test_map_on_the_simulator_then_pick(tmp_path, capsys):
    out = tmp_path / "m.json"
    assert (
        main(
            ["map", "--backend", "simulator", "--n-pairs", "27", "--planted", "0.03", "--seed", "1", "--out", str(out)]
        )
        == 0
    )
    assert "verdict: DIAGNOSTIC" in capsys.readouterr().out
    assert len(json.loads(out.read_text())["outcomes"]) == 16
    assert main(["pick", str(out), "--n", "5"]) == 0
    assert capsys.readouterr().out.count("k_A") == 5


@pytest.mark.skipif(importlib.util.find_spec("qiskit_ibm_runtime") is None, reason="needs the [ibm] extra")
def test_ibm_is_a_dry_run_without_submit(capsys):
    assert main(["map", "--backend", "ibm", "--processor", "ibm_fez", "--offline", "--pairs", "114-115,70-71"]) == 0
    out = capsys.readouterr().out
    assert "nothing was sent" in out and "3 CZ per pair" in out


def test_report_table(capsys):
    assert main(["report", str(archive.data_dir() / "ibm_fez" / "k31-map.json")]) == 0
    assert capsys.readouterr().out.startswith("| pair | k_A | k_B | published x |")
