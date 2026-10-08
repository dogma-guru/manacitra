# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""Amendment A8, R1: pick, verdict and report read every archived file by its declared bit reading.

The expected pairs and statistics below are literals. They were computed by tests/_independent_readings.py, which does
not import manacitra: it decodes each record by its reading as the data README describes it, with numpy alone. A test
that called the package's reader on both sides would not test the reader."""

import copy
import json
import re

import pytest

from manacitra import archive
from manacitra.cli import main

RIG = archive.RIGETTI

# From tests/_independent_readings.py (Amendment A8), run on the archive at 0f3cf61; r rounded to 6 places
INDEPENDENT = {
    "main.json": {"n": 22, "r_split": 0.985388, "r_AB": 0.970614},
    "k40-map.json": {
        "n": 23,
        "r_split": 0.973698,
        "r_AB": 0.811457,
        "r_Ax": 0.198042,
        "pick_by_level": [[101, 102], [81, 82], [99, 100], [56, 57], [0, 1], [24, 25], [87, 88], [13, 14]],
        "pick_by_x": [[99, 100], [81, 82], [94, 95], [56, 57], [101, 102], [65, 66], [29, 30], [89, 98]],
        "pick_by_level_if_read_as_qiskit_adjacent": [
            [60, 61],
            [13, 14],
            [42, 43],
            [29, 30],
            [63, 64],
            [20, 21],
            [67, 68],
            [54, 55],
        ],  # fmt: skip
    },
    "k41-map.json": {"n": 23, "r_split": 0.816423, "r_AB": 0.903928, "r_Ax": -0.003628},
}


def _run(capsys, *args):
    assert main(list(args)) == 0
    return capsys.readouterr().out


def _stat(out: str, name: str) -> float:
    return float(re.search(rf"^  {name} = (-?[0-9.]+)$", out, re.M).group(1))


def _picked(out: str) -> list:
    return [json.loads(line.split("]")[0].strip() + "]") for line in out.splitlines()[1:]]


def _path(name: str) -> str:
    return str(archive.data_dir() / RIG / name)


@pytest.mark.parametrize(
    "name,verdict,read_as",
    [
        ("main.json", "MAP PRESENT", "openquantum-reversed; the 22 working pairs of 27"),
        ("k40-map.json", "DIAGNOSTIC", "braket-measured-qubits; the verdict set, 23 of 27 pairs"),
        ("k41-map.json", "DIAGNOSTIC", "braket-measured-qubits; the verdict set, 23 of 27 pairs"),
    ],
)
def test_verdict_reads_the_declared_reading(name, verdict, read_as, capsys):
    out = _run(capsys, "verdict", _path(name))
    want = INDEPENDENT[name]
    assert out.startswith(f"read as {read_as}") and f"verdict: {verdict} " in out
    assert _stat(out, "r_split_A") == pytest.approx(want["r_split"], abs=5e-5)
    assert _stat(out, "r_AB") == pytest.approx(want["r_AB"], abs=5e-5)
    if "r_Ax" in want:  # x from the figures record that meta.figures_file names
        assert _stat(out, "r_Ax") == pytest.approx(want["r_Ax"], abs=5e-5)


def test_pick_by_level_and_by_x_on_braket(capsys):
    want = INDEPENDENT["k40-map.json"]
    assert _picked(_run(capsys, "pick", _path("k40-map.json"), "--by", "level")) == want["pick_by_level"]
    assert _picked(_run(capsys, "pick", _path("k40-map.json"), "--by", "x")) == want["pick_by_x"]


def _copy_with_meta(tmp_path, name, change):
    rec = copy.deepcopy(archive.load(f"{RIG}/{name}"))
    change(rec["meta"])
    out = tmp_path / name
    out.write_text(json.dumps(rec))
    for f in ("k40-figures.json", "k41-figures.json"):  # the companion figures records, beside it
        (tmp_path / f).write_text((archive.data_dir() / RIG / f).read_text())
    return str(out)


@pytest.mark.parametrize(
    "change,message",
    [
        (lambda m: m.pop("bit_reading"), "meta.bit_reading is missing"),
        (lambda m: m.update(bit_reading="little-endian"), "meta.bit_reading is 'little-endian', not one of"),
    ],
)
def test_an_undeclared_or_unknown_reading_is_refused(change, message, tmp_path):
    path = _copy_with_meta(tmp_path, "k40-map.json", change)
    for cmd in ("verdict", "pick", "report"):
        with pytest.raises(SystemExit, match=re.escape(message)):
            main([cmd, path])


def test_the_dispatch_matters(tmp_path, capsys):
    """The same counts, declared as IBM's adjacent reading: Braket's 54-character keys pass for 27 adjacent pairs, so
    nothing stops the decode, and the pick changes to what the commands gave before Amendment A8."""
    want = INDEPENDENT["k40-map.json"]
    path = _copy_with_meta(tmp_path, "k40-map.json", lambda m: m.update(bit_reading="qiskit-adjacent"))
    misread = _picked(_run(capsys, "pick", path, "--by", "level"))
    assert misread == want["pick_by_level_if_read_as_qiskit_adjacent"] and misread != want["pick_by_level"]


def test_the_ibm_reading_is_named(capsys):
    """Kickoff 31's ibm_fez map, the adjacent reading; test_cli.test_pick_by checks its picks."""
    out = _run(capsys, "verdict", str(archive.data_dir() / "ibm_fez" / "k31-map.json"))
    assert out.startswith("read as qiskit-adjacent; all 27 pairs") and "verdict: DIAGNOSTIC " in out


@pytest.mark.parametrize("name", ["k42-day1.json", "k40-payoff.json", "k37-placement.json"])
def test_records_that_are_not_maps_are_refused(name):
    with pytest.raises(SystemExit, match="refused: .*not a map run"):
        main(["verdict", _path(name)])


def test_records_that_are_not_tables_are_refused_by_the_reader():
    """A record whose positions measure different pairs, or whose counts are per task, has no single table."""
    for path in ("ibm_fez/k32-isolation.json", "ibm_fez/k35-day1.json", f"{RIG}/k38-activity.json"):
        with pytest.raises(archive.NotATable):
            archive.p11_table(archive.load(path))


def test_the_commands_agree_with_the_acceptance_cases():
    """verdict on an archived file gives the verdict and statistics of that file's acceptance case."""
    from _reproduce import k40_stage2, k41_today

    cases = {
        "main.json": archive.rigetti_map(archive.load(f"{RIG}/main.json"))["analysis"],
        "k40-map.json": k40_stage2()["verdict_stats"],
        "k41-map.json": k41_today()["verdict_stats"],
    }
    for name, an in cases.items():
        v = archive.map_view(archive.load(f"{RIG}/{name}"), archive.data_dir() / RIG)["analysis"]
        assert v["verdict"]["verdict"] == an["verdict"]["verdict"]
        assert v["S1"]["r_split_A"]["pearson"] == an["S1"]["r_split_A"]["pearson"]
        assert v["S2"]["r_AB"]["pearson"] == an["S2"]["r_AB"]["pearson"]
        assert v["S2"]["p_one_sided"] == an["S2"]["p_one_sided"]
