# Copyright 2026 Anish Patel
# SPDX-License-Identifier: Apache-2.0
"""The identifier scan: it catches what it must, and the whole tree is clean."""

import re
import sys
from pathlib import Path

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
        "vocabulary-w7": "Dogma" + " Guru",
    }
    for name, text in samples.items():
        assert name in hits(text), name


def test_allows_job_ids_and_placeholders():
    assert not hits('"job_id": "db1pjp6egvvc73bi00m0"')
    assert not hits("00000000-0000-0000-0000-000000000001")
    assert not hits("a string during a run of measuring")  # word boundaries hold


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
