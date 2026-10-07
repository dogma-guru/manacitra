# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""Amendment A9: the repository's home is the organisation's address, and every reference names it, not the redirect.

The build report keeps the earlier address where it records what was true when a section was written; no other file
may carry it, so it cannot come back through a copied paragraph."""

import re
import subprocess
import tomllib
from pathlib import Path

import pytest

from manacitra import archive

ROOT = Path(__file__).resolve().parents[1]
HOME = "https://github.com/dogma-guru/manacitra"
OLD = "github.com/dog" + "maguru/"  # assembled at run time, so this file does not name it
BINARY = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".gz", ".npz", ".npy", ".ico", ".woff", ".woff2"}


def _read(name: str) -> str:
    return (ROOT / name).read_text()


def test_every_reference_names_the_home():
    assert archive.REPOSITORY == HOME
    assert re.search(r'^repository-code: "([^"]+)"$', _read("CITATION.cff"), re.M).group(1) == HOME
    assert tomllib.loads(_read("pyproject.toml"))["project"]["urls"]["Repository"] == HOME
    readme = _read("README.md")
    citation = [line for line in readme.splitlines() if line.startswith("> Patel, A. (2026).")]
    assert len(citation) == 1 and citation[0].split()[-1] == HOME
    assert f"git clone {HOME}.git" in readme
    assert f'pip install "git+{HOME}"' in readme
    assert f"--cert-identity {HOME}/" in _read("docs/index.md")


def test_no_tracked_file_but_the_build_report_names_the_old_address():
    try:
        files = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("not a git checkout")
    offenders = []
    for name in files.splitlines():
        path = ROOT / name
        if name == "build-report.md" or path.suffix.lower() in BINARY or not path.is_file():
            continue
        try:
            text = path.read_text()
        except UnicodeDecodeError:
            continue
        offenders += [f"{name}:{i}" for i, line in enumerate(text.splitlines(), 1) if OLD in line]
    assert offenders == [], f"the old address, outside the build report: {offenders}"


def test_the_documented_signing_identity_is_the_home():
    identities = re.findall(r"--cert-identity (\S+)", _read("docs/index.md"))
    assert identities and all(i.startswith(HOME + "/.github/workflows/sign.yml@") for i in identities), identities
