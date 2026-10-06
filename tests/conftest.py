# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""Every test gets its own submission ledger, so no test writes one into the working directory. A test that needs the
archived dataset and cannot find it is skipped, with the reason the package gives (how to get the data and set
MANACITRA_DATA), instead of failing."""

import pytest

from manacitra.archive import DataNotFound


@pytest.fixture(autouse=True)
def _own_ledger(tmp_path, monkeypatch):
    monkeypatch.setenv("MANACITRA_LEDGER", str(tmp_path / "ledger.jsonl"))


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if call.excinfo is not None and call.excinfo.errisinstance(DataNotFound):
        report.outcome = "skipped"
        report.longrepr = (str(item.path), item.location[1] or 0, f"Skipped: needs the dataset: {call.excinfo.value}")
