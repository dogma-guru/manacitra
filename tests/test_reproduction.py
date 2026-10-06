# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""The acceptance bar: every field listed in tests/expected_fields.json reproduces to 1e-6 from the archived counts
in data/, compared strictly (tests/_reproduce.py)."""

import numpy as np
import pytest
from _reproduce import CASES, REQUIRED, TOL, k37

from manacitra import archive


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


def test_k37_as_amendment_a5_states_it():
    """Amendment A5: the measures at the stated precision, the gap from the archived completion times, the verdict
    from the rule's fixed thresholds, and the two lines against Kickoff 34b."""
    r = k37()[2]
    m = {k: v["pearson"] for k, v in r["measures"].items()}
    assert [round(m[k], 6) for k in ("c_1", "c_2", "d_1", "d_2")] == [0.998384, 0.997482, 0.068990, -0.252175]
    assert (round(m["t27"], 3), round(m["t53"], 3)) == (0.968, 0.758)
    assert divmod(round(r["gap"]["seconds"] / 60), 60) == (9, 9)
    assert r["verdict"]["on_pearson"] == "PLACEMENT" and r["verdict"]["conditions"] == {
        "W": True,
        "N": False,
        "T": False,
        "S": True,
    }
    assert archive.placement_rule(m["c_1"], m["c_2"], m["d_1"], m["d_2"], m["t27"], m["t53"])[0] == "PLACEMENT"
    d = r["descriptive"]
    assert (d["r_T1w1_vs_34b_main_A_no_mean_of_four"]["n"], d["r_T2w1_vs_34b_screen"]["n"]) == (27, 53)
    assert round(d["r_T1w1_vs_34b_main_A_no_mean_of_four"]["pearson"], 3) == 0.989
    assert round(d["r_T2w1_vs_34b_screen"]["pearson"], 3) == 0.976


@pytest.mark.parametrize(
    "c,d,t,verdict",
    [
        ((0.69, 0.99), (0.1, 0.1), (0.9, 0.9), "NOT SETTLED (unstable)"),
        ((0.9, 0.9), (0.39, 0.1), (0.7, 0.9), "PLACEMENT"),
        ((0.9, 0.9), (0.7, 0.8), (0.1, 0.39), "DRIFT"),
        ((0.9, 0.9), (0.1, 0.1), (0.1, 0.1), "BOTH"),
        ((0.9, 0.9), (0.7, 0.7), (0.7, 0.7), "NEITHER"),
        ((0.9, 0.9), (0.4, 0.1), (0.9, 0.9), "MIXED"),
    ],
)
def test_the_placement_rule_at_its_thresholds(c, d, t, verdict):
    assert archive.placement_rule(*c, *d, *t)[0] == verdict


def test_k37_selection_note_sds():
    note = archive.load(f"{archive.RIGETTI}/k37-after-the-fact.json")["selection_note"]
    r = k37()[2]
    rec = archive.load(f"{archive.RIGETTI}/k37-placement.json")
    p53 = [tuple(p) for p in rec["programs"]["P53"]["pairs"]]
    at = [p53.index(tuple(p)) for p in rec["programs"]["P27"]["pairs"]]
    sds = [np.std(np.array(r["per_task_P11"][f"wave{w}-T2"])[at], ddof=1) for w in (1, 2)]
    assert f"SD {sds[0]:.3f} and {sds[1]:.3f}" in note
