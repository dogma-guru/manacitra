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


def test_pick_warns_when_the_verdict_is_not_usable(tmp_path, capsys):
    """Amendment A3, 2.5: a map with no planted per-pair error is NOISE; pick still ranks, and warns."""
    out = tmp_path / "noise.json"
    assert main(["map", "--backend", "simulator", "--n-pairs", "27", "--seed", "1", "--out", str(out)]) == 0
    assert "verdict: NOISE" in capsys.readouterr().out
    assert main(["pick", str(out), "--n", "5"]) == 0
    got = capsys.readouterr()
    assert "warning: this map's verdict is NOISE" in got.err and got.out.count("k_A") == 5


def test_pick_is_quiet_on_a_usable_map(capsys):
    assert main(["pick", str(archive.data_dir() / "ibm_fez" / "k31-map.json"), "--n", "3"]) == 0
    assert capsys.readouterr().err == ""


def _picked(text):
    return [json.loads(line.split("]")[0].strip() + "]") for line in text.splitlines()[1:]]


@pytest.mark.parametrize("by", ["kept-share", "level", "x", "k"])
def test_pick_by(by, capsys):
    """Amendment A7, 5.2: --by kept-share (the default, and its earlier name k), --by level (each pair's mean P(A no),
    highest first) and --by x (the published score, lowest first), on Kickoff 31's ibm_fez map."""
    import numpy as np

    from manacitra.keptshare import kept_from_order

    path = archive.data_dir() / "ibm_fez" / "k31-map.json"
    rec = archive.load(path)
    k, _, level = kept_from_order(archive.p11_table(rec), rec["order"], "A")
    x = np.array([r["x"] for r in rec["published_at_submission"]])
    want = {"kept-share": np.argsort(-k), "k": np.argsort(-k), "level": np.argsort(-level), "x": np.argsort(x)}[by][:6]
    assert main(["pick", str(path), "--n", "6", "--by", by]) == 0
    out = capsys.readouterr().out
    assert _picked(out) == [rec["pairs"][i] for i in want]
    assert {"kept-share": "kept share", "k": "kept share", "level": "plain level", "x": "published score"}[by] in out


def test_pick_by_level_differs_from_the_default(capsys):
    """On Kickoff 31's ibm_fez map the two rankings differ, so the option changes the pick."""
    path = str(archive.data_dir() / "ibm_fez" / "k31-map.json")
    main(["pick", path, "--n", "8"])
    by_k = _picked(capsys.readouterr().out)
    main(["pick", path, "--n", "8", "--by", "level"])
    assert _picked(capsys.readouterr().out) != by_k


def test_pick_by_x_needs_a_published_score(tmp_path, capsys):
    out = tmp_path / "m.json"
    main(["map", "--backend", "simulator", "--n-pairs", "27", "--seed", "1", "--out", str(out)])
    capsys.readouterr()
    d = json.loads(out.read_text())
    d["meta"]["x"] = None  # as a map from a provider that publishes no score
    out.write_text(json.dumps(d))
    with pytest.raises(SystemExit, match="no published score"):
        main(["pick", str(out), "--by", "x"])
