# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""Where the archived dataset is found: --data, then $MANACITRA_DATA, then data/ beside the source (Amendment A3)."""

from pathlib import Path

import pytest

from manacitra import archive
from manacitra.cli import main

CLONE = Path(__file__).resolve().parents[1] / "data"  # the tests run from a clone, so its data/ is beside them


@pytest.fixture
def no_clone(tmp_path, monkeypatch):
    """As in a plain (non-editable) install: nothing beside the source, and no setting."""
    monkeypatch.setattr(archive, "BESIDE_SOURCE", tmp_path / "nowhere")
    monkeypatch.delenv("MANACITRA_DATA", raising=False)
    monkeypatch.chdir(tmp_path)
    yield
    archive.set_data_dir(None)


def test_a_clone_finds_its_data():
    """Installed from this clone (editable), the package finds data/ by itself; in a plain install this skips."""
    assert archive.data_dir().resolve() == CLONE and (CLONE / "SHA256SUMS").is_file()


def test_without_data_it_stops_and_says_how(no_clone):
    with pytest.raises(archive.DataNotFound) as e:
        archive.load("ibm_fez/k31-map.json")
    msg = str(e.value)
    assert "git clone https://github.com/dogma-guru/manacitra" in msg
    assert "pip install -e ." in msg and "MANACITRA_DATA=" in msg and "--data" in msg


def test_the_environment_variable(no_clone, monkeypatch):
    monkeypatch.setenv("MANACITRA_DATA", str(CLONE))
    assert archive.load("ibm_fez/k31-map.json")["meta"]["processor"] == "ibm_fez"


def test_a_wrong_folder_is_named(no_clone, tmp_path, monkeypatch):
    monkeypatch.setenv("MANACITRA_DATA", str(tmp_path))
    with pytest.raises(archive.DataNotFound, match="is not the Manacitra dataset"):
        archive.data_dir()


def test_the_command_line(no_clone, capsys):
    assert main(["verdict", "simulated/k36-arm1.json"]) == 2
    err = capsys.readouterr().err
    assert err.startswith("manacitra: the Manacitra dataset (data/) was not found") and "--data" in err
    assert main(["--data", str(CLONE), "verdict", "simulated/k36-arm1.json"]) == 0
    assert "verdict: NOISE" in capsys.readouterr().out
    with pytest.raises(archive.DataNotFound):  # --data holds for that one command only
        archive.data_dir()
