# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""Every source file, the hook and the workflows carry the short header (Amendment A3, 4.4)."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HEADER = "# Copyright 2026 Dogma LLC\n# SPDX-License-Identifier: Apache-2.0\n"


def test_every_file_has_the_header():
    files = [p for d in ("src", "tests", "tools", "docs", "examples") for p in (ROOT / d).rglob("*.py")]
    files += [ROOT / ".githooks" / "pre-commit", *(ROOT / ".github" / "workflows").glob("*.yml")]
    missing = []
    for p in files:
        text = p.read_text()
        if text.startswith("#!"):
            text = text.split("\n", 1)[1]
        if not text.startswith(HEADER):
            missing.append(str(p.relative_to(ROOT)))
    assert not missing, missing
