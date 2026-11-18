# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""Amendment A29, section 4: the three probes in data/rigetti_cepheus_1_108q/probes/, published as records.

Each rule is byte for byte, its hash the one its issue carried; every file but those the README lists as changed is
byte for byte as its probe's SHA256SUMS gives it; each changed file's two digests are the README's; and outside the
rules no dollar figure is left (ruling R1)."""

import hashlib
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PROBES = ROOT / "data" / "rigetti_cepheus_1_108q" / "probes"
README = (PROBES / "README.md").read_text()
FLAT = " ".join(README.split())
RULES = {
    "probe-01-wait": (
        "braket-probe-01-wait-rule.md",
        "1d60b3b1ae8796d47197ea9bd58bb8d4f8fd3b8671aa8cf1a5d4191a49c1afb6",
        74,
    ),
    "probe-02-scaling": (
        "braket-probe-02-scaling-rule.md",
        "024783547852c52ab9f834c2a85f10d2eb73227aef73b8cc0ec895013acb8e41",
        75,
    ),
    "probe-03-program-set": (
        "braket-probe-03-program-set-rule.md",
        "b9748919eb26918976fbfd4ff0028899294cffbc97975e1cb6167e570811fb27",
        76,
    ),
}
CHANGED = {
    m[0]: (m[1], m[2])
    for m in re.findall(
        r"^\| `(probe-[^`]+)` \| [^|]+ \| [\d,]+ \| `([0-9a-f]{64})` \| `([0-9a-f]{64})` \|$", README, re.M
    )
}


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _sums(folder: Path) -> dict[str, str]:
    return {name: h for h, name in (line.split("  ", 1) for line in (folder / "SHA256SUMS").read_text().splitlines())}


def test_three_folders_and_the_readme_says_what_a_probe_is():
    assert sorted(p.name for p in PROBES.iterdir() if p.is_dir()) == sorted(RULES)
    assert "A probe is not a test, and nothing in it is a finding." in FLAT
    for word in ("ACTS AS TIME", "WAIT PRESENT", "SCALES", "BARRIER ADDS WAIT", "REJECTED", "NOT APPLICABLE"):
        assert word in FLAT


@pytest.mark.parametrize("probe", sorted(RULES))
def test_the_rule_is_byte_for_byte(probe):
    name, sha, issue = RULES[probe]
    rules = sorted((PROBES / probe).rglob("braket-probe-*-rule.md"))
    assert rules and all(_sha(r) == sha for r in rules)  # probe 03 carries its rule twice, once per attempt
    assert (PROBES / probe / "rule.sha256").read_text().split()[0] == sha
    assert f"| `{name}` | `{sha}` | {issue}, 21 October 2026," in README


@pytest.mark.parametrize("probe", sorted(RULES))
def test_every_file_is_as_handed_back_or_listed_as_changed(probe):
    folder = PROBES / probe
    sums = _sums(folder)
    files = sorted(p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file())
    # in probes 01 and 02, redaction-log.md was written after SHA256SUMS (their runner prompts' order)
    outside = {"SHA256SUMS"} | ({"redaction-log.md"} if probe != "probe-03-program-set" else set())
    assert set(files) == set(sums) | outside
    for rel, h in sums.items():
        changed = CHANGED.get(f"{probe}/{rel}")
        if changed:
            assert changed == (h, _sha(folder / rel)) and h != changed[1], rel
        else:
            assert _sha(folder / rel) == h, rel


def test_the_changed_files_and_their_count():
    assert len(CHANGED) == 48
    assert "Two kinds of change, in 48 files" in FLAT and "173 replacements." in FLAT and "4 replacements." in FLAT
    assert sum(_text(p).count("[cost]") for p in PROBES.rglob("*") if p.is_file() and p.name != "README.md") >= 173
    assert sum(_text(p).count('"[the hand-back folder]"') for p in PROBES.rglob("finalize.py")) == 4


def _text(p: Path) -> str:
    return p.read_text()


def test_no_dollar_figure_outside_the_rules():
    """Ruling R1: the rules keep their caps; elsewhere a dollar sign is followed by no figure but qubit 99's name."""
    for p in PROBES.rglob("*"):
        if p.is_file() and not re.fullmatch(r"braket-probe-0[123]-[a-z-]+-rule\.md", p.name):
            t = _text(p)
            assert not re.findall(r"\$(?!99(?!\d))\d", t), p
            assert not re.findall(r'_usd": "(?!\[cost\])', t), p
            assert '"price": "[cost]"' in t or '"price"' not in t, p


def test_the_rules_keep_their_caps():
    for probe, (name, _, _) in RULES.items():
        assert "$0." in _text(PROBES / probe / name)
