# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""The acceptance bar: every field listed in tests/expected_fields.json reproduces to 1e-6 from the archived counts
in data/, compared strictly (tests/_reproduce.py)."""

import pytest
from _reproduce import CASES, REQUIRED, TOL


@pytest.mark.parametrize("case", list(CASES))
def test_every_statistic_reproduces(case):
    rows, leaves = CASES[case]()
    assert leaves, "nothing was compared"
    worst = max(leaves)
    assert worst[0] <= TOL, f"{case}: {worst[1]} differs by {worst[0]:.3g}"
    for name, archived, reproduced in rows:
        if isinstance(archived, str):
            assert reproduced == archived, f"{case}: {name}"


@pytest.mark.parametrize("case,verdict", list(REQUIRED.items()))
def test_required_verdicts(case, verdict):
    rows, _ = CASES[case]()
    assert dict((n, r) for n, _, r in rows)["verdict"] == verdict


def test_k33_fez_gain_as_published():
    rows, _ = CASES["Kickoff 33, ibm_fez"]()
    G = dict((n, r) for n, _, r in rows)["G (top 8 by map minus top 8 by x)"]
    assert round(G, 4) == 0.0012
