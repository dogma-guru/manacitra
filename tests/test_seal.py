# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""Sealed commitments: the round trip, and every way a check must fail."""

import json
import subprocess
from pathlib import Path

import pytest

from manacitra import seal as S
from manacitra.cli import main


@pytest.fixture
def sealed(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    f = tmp_path / "predictions.md"
    f.write_text("verdict on ibm_fez: DIAGNOSTIC (0.6)\n")
    rec = S.seal(f)
    return f, rec


def test_round_trip(sealed):
    f, rec = sealed
    assert rec["salt"] is None and len(rec["hash"]) == 64
    salt_file = Path(".seals") / "predictions.md.salt"
    assert salt_file.exists() and len(bytes.fromhex(salt_file.read_text().strip())) == 32
    assert salt_file.read_text().strip() not in Path("predictions.md.commit.json").read_text()
    S.reveal(f)
    v = S.verify(f)
    assert v.match and v.message.startswith("MATCH")


def test_a_one_byte_change_fails(sealed):
    f, _ = sealed
    S.reveal(f)
    data = bytearray(f.read_bytes())
    data[0] ^= 0x01
    f.write_bytes(bytes(data))
    v = S.verify(f)
    assert not v.match and v.message.startswith("NO MATCH")


def test_a_wrong_salt_fails(sealed):
    f, _ = sealed
    v = S.verify(f, salt_hex="00" * 32)
    assert not v.match and v.message.startswith("NO MATCH")
    rec = json.loads(Path("predictions.md.commit.json").read_text())
    rec["salt"] = "ab" * 32
    Path("predictions.md.commit.json").write_text(json.dumps(rec))
    assert not S.verify(f).match


def test_a_missing_salt_fails_with_a_clear_message(sealed):
    f, _ = sealed
    v = S.verify(f)
    assert not v.match and "has no salt" in v.message and "not been revealed" in v.message


def test_reveal_refuses_a_changed_file(sealed):
    f, _ = sealed
    f.write_text("verdict on ibm_fez: NOISE (0.6)\n")
    with pytest.raises(S.SealError, match="does not match"):
        S.reveal(f)
    assert json.loads(Path("predictions.md.commit.json").read_text())["salt"] is None


def test_a_commitment_is_made_once(sealed):
    f, _ = sealed
    with pytest.raises(S.SealError, match="already sealed"):
        S.seal(f)


def test_salts_differ_between_seals(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    a, b = tmp_path / "a.md", tmp_path / "b.md"
    a.write_text("same")
    b.write_text("same")
    assert S.seal(a)["hash"] != S.seal(b)["hash"]


def test_cli(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    Path("p.md").write_text("k_A mean 0.82 on ibm_fez\n")
    assert main(["seal", "p.md"]) == 0
    assert len(capsys.readouterr().out.strip().splitlines()[-1]) == 64
    assert main(["verify", "p.md"]) == 1
    assert main(["reveal", "p.md"]) == 0
    assert main(["verify", "p.md"]) == 0
    assert "MATCH" in capsys.readouterr().out


def test_the_seals_folder_is_ignored_by_git():
    root = Path(__file__).resolve().parent.parent
    out = subprocess.run(["git", "check-ignore", ".seals/x.md.salt"], cwd=root, capture_output=True, text=True)
    assert out.returncode == 0
