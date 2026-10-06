# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""NOTICE names every package that pyproject.toml declares (Amendment A3, 4.5)."""

import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def declared() -> set[str]:
    py = tomllib.loads((ROOT / "pyproject.toml").read_text())
    reqs = list(py["build-system"]["requires"]) + list(py["project"]["dependencies"])
    for extra in py["project"]["optional-dependencies"].values():
        reqs += extra
    return {re.match(r"[A-Za-z0-9_.-]+", r).group(0).lower() for r in reqs}


def test_every_declared_package_is_in_notice():
    notice = (ROOT / "NOTICE").read_text().lower()
    names = declared()
    assert {"requests", "ply"} <= names
    missing = sorted(n for n in names if not re.search(rf"(?<![a-z0-9-]){re.escape(n)}(?![a-z0-9-])", notice))
    assert not missing, f"not in NOTICE: {missing}"
