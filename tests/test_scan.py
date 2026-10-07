# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""The identifier scan: it catches what it must, and the whole tree is clean."""

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import scan_secrets  # noqa: E402
from scan_patterns import ALLOW, PATTERNS  # noqa: E402


def hits(text):
    return {
        name
        for _, name, _ in scan_secrets.scan_text(text, scan_secrets._compile(PATTERNS), scan_secrets._compile(ALLOW))
    }


def test_catches_each_kind():
    # every sample is assembled at run time, so this file holds none of them
    samples = {
        "ibm-cloud-crn": "crn" + ":v1:bluemix:public:quantum-computing:us-east:a/abc123::",
        "ibm-api-key-44": "Ab3" + "x" * 41,
        "bearer-token": "Authorization: " + "Bearer " + "abcdefABCDEF0123456789",
        "email-address": "someone" + "@" + "example.org",
        "home-path-mac": "/" + "Users" + "/someone/project",
        "uuid": "1b4e28ba-2fa1-11d2-883f-" + "0016d3cca427",
        "client-secret-field": "client" + "_secret = 'abcdefgh12345'",
        "vocabulary-w5": "K" + "undala",
        "vocabulary-w7": "Dog" + "ma Guru",
    }
    for name, text in samples.items():
        assert name in hits(text), name


def test_allows_job_ids_and_placeholders():
    assert not hits('"job_id": "db1pjp6egvvc73bi00m0"')
    assert not hits("00000000-0000-0000-0000-000000000001")
    assert not hits("a string during a run of measuring")  # word boundaries hold


def test_catches_each_amazon_kind():
    """Amendment A7, section 7: the Amazon identifiers, before any Amazon Braket file is copied."""
    samples = {
        "aws-arn": "ar" + "n:aws:braket:us-west-1:" + "1" + "23456789012:quantum-task/abc",
        "aws-s3-uri": "S" + "3://some-bucket/results",
        "aws-account-number": '"account": "' + "3" + "84726190573" + '"',
        "aws-access-key-field": "AWS_" + "ACCESS_KEY_ID=x",
        "aws-access-key-id": "AK" + "IA" + "ABCDEFGHIJKLMNOP",
        "aws-secret-field": "aws_" + "secret_access_key = y",
    }
    for name, text in samples.items():
        assert name in hits(text), name


def test_amazon_patterns_leave_regions_numbers_and_counts_keys_alone():
    assert not hits('"region": "us-west-1", "profile": "default"')
    assert not hits('{"010011001100": 4300, "111111111111": 12}')  # six-pair counts keys
    assert not hits("0.123456789012345 1234567890123 12345678901")  # a fraction, 13 digits, 11 digits
    assert "aws-account-number" in hits('{"0123' + '45678912": 1}')  # a quoted twelve digits, not only 0s and 1s
    assert not hits("the learn: section")  # the resource-name pattern needs a word boundary


def test_the_bot_address_is_allowed_and_nothing_else():
    """Amendment A3, 4.1: GitHub's public workflow address passes; any other address, a bot's too, is flagged."""
    assert not hits('git config user.email "41898282+github-actions[bot]@users.noreply.github.com"')
    assert "email-address" in hits("someone[bot]" + "@" + "users.noreply.github.com")
    assert "email-address" in hits("4189828" + "3+github-actions[bot]" + "@" + "users.noreply.github.com")


def test_pattern_file_matches_nothing_of_itself():
    text = (ROOT / "tools" / "scan_patterns.py").read_text()
    assert not hits(text)


def test_runtime_user_name_is_not_written_down():
    import getpass

    user = getpass.getuser()
    text = (ROOT / "tools" / "scan_patterns.py").read_text()
    assert len(user) < 3 or not re.search(rf"\b{re.escape(user)}\b", text, re.I)


def test_whole_tree_is_clean():
    result = scan_secrets.scan_files(scan_secrets.tracked_files(ROOT))
    assert result == {}, result


def test_sigstore_bundles_are_skipped(tmp_path):
    f = tmp_path / "k31-map.json.sigstore.json"
    f.write_text('{"cert": "' + "someone" + "@" + 'example.org"}')
    assert scan_secrets.skipped(f)


def test_data_checksums_match():
    import subprocess

    out = subprocess.run([sys.executable, str(ROOT / "tools" / "sha256sums.py"), "--check"], capture_output=True)
    assert out.returncode == 0, out.stdout


W7 = "Dog" + "ma"  # assembled at run time, so this file holds no instance of the word


@pytest.mark.parametrize(
    "text",
    [
        f"a project of {W7} Guru",  # the trade name outside the publisher and ownership lines
        f"{W7.lower()}guru.com",  # one word, outside the repository URL
        f"see github.com/{W7.lower()}guru/other-repo",
        f"{W7.upper()} GURU",  # another case
        f"{W7}_Guru",  # another spacing
        f"the {W7} series",  # the first word on its own
        f"{W7} LLC (d.b.a. {W7} Guru)",  # the ownership line, reworded
        f"Published by {W7} Guru",  # the publisher line, another case
    ],
)
def test_w7_is_flagged_in_any_other_context(text):
    assert "vocabulary-w7" in hits(text), text


@pytest.mark.parametrize(
    "text",
    [
        f"Copyright 2026 {W7} LLC",
        f"Copyright 2026 {W7} LLC (doing business as {W7} Guru)",
        f"The copyright holder is {W7} LLC ({W7} Guru).",
        f"Manacitra is developed by Anish Patel and published by {W7} Guru.",
        f"https://github.com/{W7.lower()}guru/manacitra",
    ],
)
def test_w7_allowed_only_in_exact_strings(text):
    assert "vocabulary-w7" not in hits(text), text


def test_a_word_that_starts_the_same_is_not_w7():
    assert "vocabulary-w7" not in hits("dog" + "matic")


# --------------------------------------------------------------------------- Amendment A4 (R2): the git identities
AUTHOR = "anish" + "@" + "d" + "ogma.guru"
ASSISTANT = "noreply" + "@" + "anthropic.com"
GITHUB = "noreply" + "@" + "github.com"
STRANGER = "someone" + "@" + "example.org"


def _repo(tmp_path, commits):
    """A throwaway repository; each commit is (author, committer, message)."""
    import subprocess

    def git(*a, env=None):
        subprocess.run(["git", *a], cwd=tmp_path, check=True, capture_output=True, env=env)

    git("init", "-q", "-b", "main")
    for i, (author, committer, msg) in enumerate(commits):
        (tmp_path / f"f{i}").write_text(str(i))
        git("add", ".")
        env = {
            "GIT_AUTHOR_NAME": "a",
            "GIT_AUTHOR_EMAIL": author,
            "GIT_COMMITTER_NAME": "c",
            "GIT_COMMITTER_EMAIL": committer,
            "GIT_CONFIG_GLOBAL": "/dev/null",
            "PATH": __import__("os").environ["PATH"],
            "HOME": str(tmp_path),
        }
        git("commit", "-q", "--no-verify", "--no-gpg-sign", "-m", msg, env=env)
    return tmp_path


def test_the_approved_identities_pass_in_their_roles(tmp_path):
    repo = _repo(
        tmp_path,
        [
            (AUTHOR, AUTHOR, f"feat: one\n\nCo-Authored-By: A <{ASSISTANT}>\nSigned-off-by: B <{AUTHOR}>"),
            (AUTHOR, GITHUB, f"docs: made on the web\n\nSigned-off-by: B <{AUTHOR}>"),
        ],
    )
    assert scan_secrets.scan_git(repo) == []
    assert len(scan_secrets.git_identities(repo)) == 7


@pytest.mark.parametrize(
    "author,committer,trailer,role",
    [
        (STRANGER, AUTHOR, "", "author"),
        (AUTHOR, STRANGER, "", "committer"),
        (ASSISTANT, AUTHOR, "", "author"),  # the assistant's address only as co-author
        (GITHUB, AUTHOR, "", "author"),  # GitHub's only as committer
        (AUTHOR, AUTHOR, f"Co-Authored-By: X <{STRANGER}>", "Co-Authored-By"),
        (AUTHOR, AUTHOR, f"Signed-off-by: X <{ASSISTANT}>", "Signed-off-by"),
        (AUTHOR, AUTHOR, f"Reported-by: X <{AUTHOR}>", "Reported-by"),
        (AUTHOR, AUTHOR, f"Write to {STRANGER} for details.", "message"),
    ],
)
def test_anything_else_is_a_finding(tmp_path, author, committer, trailer, role):
    repo = _repo(tmp_path, [(author, committer, f"fix: something\n\n{trailer}\nSigned-off-by: B <{AUTHOR}>")])
    found = scan_secrets.scan_git(repo)
    assert [r for _, r, _ in found] == [role]


def test_this_repository_has_only_approved_identities():
    import subprocess

    if subprocess.run(["git", "rev-parse"], cwd=ROOT, capture_output=True).returncode != 0:
        pytest.skip("not a git work tree")
    assert scan_secrets.scan_git(ROOT) == []


def test_the_approved_list_carries_no_address_the_tree_scan_would_match():
    from scan_patterns import GIT_IDENTITIES

    for rx, _ in GIT_IDENTITIES:
        assert "email-address" not in hits(rx), rx
