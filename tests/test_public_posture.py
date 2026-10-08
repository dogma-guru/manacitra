# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""Amendment A10: the public posture (one committer; forks welcome; outside pull requests closed; Issues the door) and
the release path, which builds the package from the tag before it is signed.

The workflows are read as text, job by job, so that the tests need no YAML parser."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GH = ROOT / ".github"
SENTENCE = "Forks are welcome; pull requests are not accepted at this time, and questions go to Issues"


def jobs(workflow: str) -> dict[str, str]:
    """Each job's block under `jobs:`, in the file's order."""
    body = (GH / "workflows" / workflow).read_text().split("\njobs:\n", 1)[1]
    parts = re.split(r"^  ([a-z][a-z0-9-]*):\n", body, flags=re.M)[1:]
    return dict(zip(parts[::2], parts[1::2]))


def test_the_release_is_built_before_it_is_signed():
    j = jobs("sign.yml")
    order = list(j)
    assert order.index("build-release") < order.index("sign-release"), order
    build, sign = j["build-release"], j["sign-release"]
    assert re.findall(r"^    if: (.+)$", build, re.M) == ["github.event_name == 'release'"]
    assert "python -m build" in build and "SHA256SUMS" in build and 'gh release upload "$TAG" dist/*' in build
    assert re.search(r"^    needs: \[gate, build-release\]$", sign, re.M)
    assert "github.event_name == 'release'" in sign
    assert (
        "verify-cert-identity: https://github.com/${{ github.repository }}/.github/workflows/sign.yml@${{ github.ref }}"
        in sign
    )
    assert "github.event_name != 'release'" in j["sign-files"]


def test_a_changed_file_loses_its_old_bundle_before_it_is_signed_again():
    """Amendment A11: the signing action refuses to overwrite a bundle, so the first re-signing of a changed file
    (data/README.md, run 37722980126) failed. The old bundles of the files to sign are removed first."""
    steps = re.split(r"^      - ", jobs("sign.yml")["sign-files"], flags=re.M)
    names = [re.search(r"name: (.+)", s).group(1) for s in steps if re.search(r"name: (.+)", s)]
    assert names.index("Remove the old bundles of files signed again") == names.index("Sign") - 1
    remove = next(s for s in steps if "Remove the old bundles" in s)
    assert 'for f in $FILES; do rm -f -- "$f.sigstore.json"; done' in remove
    assert "FILES: ${{ steps.list.outputs.files }}" in remove


def test_an_outside_pull_request_is_closed_without_running_its_code():
    text = (GH / "workflows" / "outside-pr.yml").read_text()
    assert re.search(r"^  pull_request_target:\n    types: \[opened\]$", text, re.M)
    assert re.search(r"^permissions:\n  pull-requests: write\n\n", text, re.M)
    (close,) = jobs("outside-pr.yml").values()
    assert "if: github.event.pull_request.head.repo.full_name != github.repository" in close
    assert "uses:" not in close and "checkout" not in close, "it must check out and run nothing"
    # only the number and the head repository's name are read from the event, never the fork's own text
    assert set(re.findall(r"github\.event\.[a-z_.]+", text)) == {
        "github.event.pull_request.head.repo.full_name",
        "github.event.pull_request.number",
    }
    assert SENTENCE in text and 'gh pr close "$PR"' in text


def test_the_posture_is_stated_where_a_stranger_looks():
    readme, contributing = (ROOT / "README.md").read_text(), (ROOT / "CONTRIBUTING.md").read_text()
    assert f"{SENTENCE} ([`CONTRIBUTING.md`](CONTRIBUTING.md))." in readme
    heads = re.findall(r"^## (.+)$", contributing, re.M)
    assert heads[:3] == ["What is accepted", "Set up", "Before a change"], heads
    assert "Before a pull request" not in contributing
    template = (GH / "PULL_REQUEST_TEMPLATE.md").read_text()
    assert template.startswith("Pull requests from outside this repository are not accepted at this time")
    security = " ".join((ROOT / "SECURITY.md").read_text().split())
    assert "Report a vulnerability" in security and "seven days" in security and "no bounty" in security
    assert (GH / "CODEOWNERS").read_text().count("\n") == 1


def test_the_issue_forms():
    forms = GH / "ISSUE_TEMPLATE"
    assert sorted(p.name for p in forms.iterdir()) == [
        "config.yml",
        "new-processor.yml",
        "other.yml",
        "reproduction.yml",
    ]
    config = (forms / "config.yml").read_text()
    assert "blank_issues_enabled: true" in config and "contact_links" not in config
    labels = re.findall(r"^      label: (.+)$", (forms / "reproduction.yml").read_text(), re.M)
    assert labels == [
        "File and field",
        "The value the README states",
        "The value you got",
        "Python and numpy versions",
        "The commit",
        "The command",
    ]
    labels = re.findall(r"^      label: (.+)$", (forms / "new-processor.yml").read_text(), re.M)
    assert labels == [
        "Vendor and route",
        "Can placement be pinned?",
        "What the published figures are called there",
        "What you tried",
    ]
    assert len(re.findall(r"^  - type: ", (forms / "other.yml").read_text(), re.M)) == 1
