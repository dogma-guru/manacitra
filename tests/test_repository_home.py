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


PATREON = "https://www.patreon.com/DogmaGuru"


def test_the_three_patreon_references_agree():
    """Amendment A11: the Sponsor button comes from this repository's own FUNDING.yml, not only the organisation's."""
    assert (ROOT / ".github" / "FUNDING.yml").read_text() == f"custom: {PATREON}\n"
    assert tomllib.loads(_read("pyproject.toml"))["project"]["urls"]["Funding"] == PATREON
    support = _read("README.md").split("\n## Support\n", 1)[1].split("\n## ", 1)[0]
    assert f"[Patreon]({PATREON})" in support


def test_the_zenodo_metadata_matches_the_citation():
    """Amendment A11: .zenodo.json parses, and its title and creator are CITATION.cff's (the title by the author's
    ruling of 7 October, which the README's citation line also carries)."""
    import json

    z = json.loads(_read(".zenodo.json"))
    cff = _read("CITATION.cff")
    title = re.search(r'^title: "([^"]+)"$', cff, re.M).group(1)
    family = re.search(r"^\s+(?:- )?family-names: (.+)$", cff, re.M).group(1)
    given = re.search(r"^\s+(?:- )?given-names: (.+)$", cff, re.M).group(1)
    assert z["title"] == title == "Manacitra: a map of your qubits"
    assert [c["name"] for c in z["creators"]] == [f"{family}, {given}"]
    version = re.search(r"^version: (.+)$", cff, re.M).group(1)
    assert f"*{title}* (version {version})" in _read("README.md")
    assert z["upload_type"] == "software" and z["license"] == "Apache-2.0"
    topics = re.search(r"^Topics: (.+)$", _read("README.md"), re.M)
    if topics:  # the README carries no topics line today; if it gains one, the keywords must be among its topics
        assert set(z["keywords"]) <= {t.strip(" `") for t in topics.group(1).split(",")}


CONCEPT_DOI = "10.5281/zenodo.23228518"
#: Each published version's own DOI, as Zenodo minted it after the release; a release's follow-up adds its line
VERSION_DOIS = {
    "0.1.0": "10.5281/zenodo.23228519",
    "0.1.1": "10.5281/zenodo.23239929",
    "0.1.2": "10.5281/zenodo.23248147",
    "0.2.0": "10.5281/zenodo.23281215",
    "0.3.0": "10.5281/zenodo.23284875",
    "0.4.0": "10.5281/zenodo.23289535",
    "0.5.0": "10.5281/zenodo.23300255",
    "0.6.0": "10.5281/zenodo.23403048",
    "0.7.0": "10.5281/zenodo.23408345",
    "0.8.0": "10.5281/zenodo.23440342",
    "0.9.0": "10.5281/zenodo.23454906",
}
V010_DOI = VERSION_DOIS["0.1.0"]


def test_the_version_is_the_same_everywhere():
    """pyproject.toml, the package, CITATION.cff and the README's citation name one version (0.10.0 since 20
    October)."""
    import manacitra

    version = tomllib.loads(_read("pyproject.toml"))["project"]["version"]
    assert manacitra.__version__ == version
    assert re.search(r"^version: (.+)$", _read("CITATION.cff"), re.M).group(1) == version
    assert f"(version {version}) [Software and data]" in _read("README.md")
    assert re.search(rf"^## {re.escape(version)} \(\d+ \w+ \d{{4}}\)$", _read("CHANGELOG.md"), re.M), "a dated entry"


def test_the_citation_uses_the_concept_doi():
    """From v0.1.1 the citation uses the concept DOI, which always resolves to the latest version (the author's ruling
    of 8 October). Beside it, the README names the latest published version's own DOI, for an exact citation; each
    release updates that one line once Zenodo has minted the DOI (the author's ruling of 8 October)."""
    assert re.search(r"^doi: (.+)$", _read("CITATION.cff"), re.M).group(1) == CONCEPT_DOI
    # date-released is the current version's release date, as its changelog entry gives it
    import datetime

    version = re.search(r"^version: (.+)$", _read("CITATION.cff"), re.M).group(1)
    day = re.search(rf"^## {re.escape(version)} \((\d+ \w+ \d{{4}})\)$", _read("CHANGELOG.md"), re.M).group(1)
    released = datetime.datetime.strptime(day, "%d %B %Y").date().isoformat()
    assert re.search(r"^date-released: (.+)$", _read("CITATION.cff"), re.M).group(1) == released
    readme = _read("README.md")
    citation = next(line for line in readme.splitlines() if line.startswith("> Patel, A. (2026)."))
    assert f"https://doi.org/{CONCEPT_DOI}." in citation
    assert f"(https://doi.org/{CONCEPT_DOI})" in readme.split("\n## What it does", 1)[0], "the badge, at the top"
    latest = max(VERSION_DOIS, key=lambda v: tuple(map(int, v.split("."))))
    doi = VERSION_DOIS[latest]
    assert f"(version {latest}: [{doi}](https://doi.org/{doi}))" in readme, "the latest published version's own DOI"
    assert readme.count("10.5281/zenodo.") == 4, "the badge, the citation, and one version DOI (twice: text and link)"
    # A23, step 5.5: CITATION.cff lists the concept DOI and the latest published version's own DOI as identifiers
    cff = _read("CITATION.cff")
    ids = re.findall(r"^  - type: doi\n    value: (\S+)\n    description: (.+)$", cff, re.M)
    assert ids == [
        (CONCEPT_DOI, "The concept DOI, which always resolves to the latest version."),
        (doi, f"The DOI of version {latest}."),
    ]
    changelog = _read("CHANGELOG.md")
    assert f"https://doi.org/{V010_DOI}" in changelog and f"https://doi.org/{CONCEPT_DOI}" in changelog


def test_the_release_steps_carry_the_doi_line():
    """Amendment A12: docs/index.md section 9's release steps include the lines each release updates after Zenodo
    mints its DOI (A23: the README's parenthetical, `VERSION_DOIS` and CITATION.cff's identifiers), beside the version
    bump."""
    steps = " ".join(
        _read("docs/index.md").split("**Releasing.**", 1)[1].split("**Plain SHA-256 stays**", 1)[0].split()
    )
    assert "test_the_version_is_the_same_everywhere" in steps and "`CITATION.cff` keeps the concept DOI" in steps
    assert '"version X.Y.Z: <DOI>"' in steps and "`VERSION_DOIS`" in steps


def test_the_release_steps_carry_the_tree_check():
    """Amendment A20: the release steps verify the tree's signed files before tagging, on the terms of the author's
    leave, and the paragraph above them points to the record of v0.5.0's check; section 9 says when a version is cut.
    Ruling R1 (Q4): the paragraph names no version range, so it does not go stale at each release."""
    page = " ".join(_read("docs/index.md").split())
    steps = page.split("**Releasing.**", 1)[1].split("**Plain SHA-256 stays**", 1)[0]
    lead, step_2 = steps.split(" 1. ", 1)[0], steps.split(" 2. ", 1)[1].split(" 3. ", 1)[0]
    assert "(build report section 36)" in lead
    assert (
        "Before tagging, verify every signed file in the tree against the `@refs/heads/main` identity (the tree "
        "check). A release whose runner cannot run it records that in the build report, and the check is run "
        "afterwards."
    ) in step_2
    assert (
        "The verification tool is installed for this check only: an exact `sigstore` version in a throwaway "
        "environment outside the repository, with no credentials, deleted afterwards."
    ) in step_2
    when = page.split("**When to release.**", 1)[1].split("**Releasing.**", 1)[0]
    assert "Several findings may share one version." in when
    assert "versions are not cut for a change that the next one will replace." in when
