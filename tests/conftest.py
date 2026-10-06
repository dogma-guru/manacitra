# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""Every test gets its own submission ledger, so no test writes one into the working directory."""

import pytest


@pytest.fixture(autouse=True)
def _own_ledger(tmp_path, monkeypatch):
    monkeypatch.setenv("MANACITRA_LEDGER", str(tmp_path / "ledger.jsonl"))
