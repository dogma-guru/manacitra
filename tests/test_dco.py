# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""The DCO check, on a throwaway repository."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import check_dco  # noqa: E402


def git(repo, *args, env=None):
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True, env=env).stdout.strip()


def commit(repo, msg, name="A Contributor", email="contributor" + "@" + "example.invalid"):
    import os

    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": name,
        "GIT_AUTHOR_EMAIL": email,
        "GIT_COMMITTER_NAME": name,
        "GIT_COMMITTER_EMAIL": email,
    }
    (repo / "f.txt").write_text((repo / "f.txt").read_text() + msg + "\n" if (repo / "f.txt").exists() else msg)
    git(repo, "add", "f.txt", env=env)
    git(repo, "commit", "-q", "-m", msg, env=env)
    return git(repo, "rev-parse", "HEAD")


def make_repo(tmp_path):
    repo = tmp_path / "r"
    repo.mkdir()
    git(repo, "init", "-q")
    base = commit(repo, "base")
    return repo, base


def test_signed_off_commits_pass(tmp_path):
    repo, base = make_repo(tmp_path)
    head = commit(repo, "feat: one\n\nSigned-off-by: A Contributor <a" + "@" + "example.invalid>")
    assert check_dco.missing_signoff(base, head, cwd=repo) == []


def test_a_commit_without_signoff_fails(tmp_path):
    repo, base = make_repo(tmp_path)
    commit(repo, "feat: one\n\nSigned-off-by: A Contributor <a" + "@" + "example.invalid>")
    head = commit(repo, "fix: two, unsigned")
    bad = check_dco.missing_signoff(base, head, cwd=repo)
    assert [c["message"].splitlines()[0] for c in bad] == ["fix: two, unsigned"]


def test_a_signoff_in_the_middle_of_a_line_does_not_count(tmp_path):
    repo, base = make_repo(tmp_path)
    head = commit(repo, "docs: mention Signed-off-by: in prose")
    assert len(check_dco.missing_signoff(base, head, cwd=repo)) == 1


def test_the_signing_bot_is_exempt(tmp_path):
    repo, base = make_repo(tmp_path)
    head = commit(
        repo,
        "chore: Sigstore bundles for abc1234",
        name="github-actions[bot]",
        email="41898282+github-actions[bot]" + "@users.noreply.github.com",
    )
    assert check_dco.missing_signoff(base, head, cwd=repo) == []
