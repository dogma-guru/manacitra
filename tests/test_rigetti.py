# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""Kickoff 34b on Rigetti Cepheus-1-108Q (Amendment A2): every figure recomputed from the archived counts."""

import numpy as np
import pytest
from _reproduce import TOL, k34b

from manacitra import archive
from manacitra.backends import openquantum as oq
from manacitra.circuits import HALVES, ORDER_16

MAIN = f"{archive.RIGETTI}/main.json"


def test_the_bit_reading_gives_the_archived_p11_exactly():
    """Pair i in classical bits i and 53 - i; classical bit k is the character at position 53 - k of the key."""
    rec = archive.load(MAIN)
    assert len(rec["pairs"]) == 27

    def pos(k):
        return 53 - k

    P = []
    for counts in rec["counts"]:
        assert {len(k) for k in counts} == {54} and sum(counts.values()) == 8000
        row = []
        for i in range(27):
            first, second = pos(i), pos(53 - i)
            row.append(sum(m for k, m in counts.items() if k[first] == "1" and k[second] == "1") / 8000)
        P.append(row)
    assert P == rec["per_circuit_P11"]
    package = [archive.p11_classical_index(c, 27) for c in rec["counts"]]
    assert np.array_equal(package, np.array(rec["per_circuit_P11"]))
    # the adapter reads the same positions
    assert oq.string_positions([tuple(p) for p in rec["pairs"]]) == [(53 - i, i) for i in range(27)]


def test_the_layout_is_the_published_one():
    rec = archive.load(MAIN)
    assert rec["order"] == ORDER_16
    assert {c: tuple(map(list, h)) for c, h in HALVES.items()} == {c: tuple(h) for c, h in rec["halves"].items()}
    assert rec["meta"]["shots_per_circuit"] == 8000 and rec["meta"]["permutation_seed"] == 34


def test_the_dead_pair_filter_excludes_five_and_leaves_22():
    r = k34b()[2]
    assert r["excluded_pairs"] == [(0, 1), (56, 57), (63, 64), (87, 88), (99, 100)]
    assert len(r["working_pairs"]) == 22


def test_the_headline_statistics():
    an = k34b()[2]["analysis"]
    assert an["S1"]["r_split_A"]["pearson"] == pytest.approx(0.985388, abs=TOL)
    assert an["S2"]["r_AB"]["pearson"] == pytest.approx(0.970614, abs=TOL)


def test_the_verdict_is_map_present_under_the_capped_rule():
    v = k34b()[2]["analysis"]["verdict"]
    assert v["verdict"] == "MAP PRESENT"
    assert "capped" in v["rule"]
    assert v["inputs"]["r_Ax"] is None and v["inputs"]["r_AB_given_x"] is None  # no vendor figures, so no S3
    assert isinstance(k34b()[2]["analysis"]["S3"], str)


def test_the_sealed_leave_one_out_without_101_102():
    loo = k34b()[2]["leave_one_out"]
    assert loo["dropped_pair"] == (101, 102)
    assert loo["verdict"]["verdict"] == "MAP PRESENT"


def test_after_the_fact_20_pairs_without_13_14_and_101_102():
    """Computed after seeing the data, outside the verdict."""
    rec = archive.load(f"{archive.RIGETTI}/after-the-fact.json")
    assert rec["label"] == "computed after seeing the data, outside the verdict"
    a = k34b()[2]["after_the_fact_20"]
    assert a["n_pairs"] == 20
    assert round(a["S1"]["r_split_A"]["pearson"], 3) == 0.842
    assert round(a["S2"]["r_AB"]["pearson"], 3) == 0.791
    assert a["verdict"]["verdict"] == "MAP PRESENT"


def test_nothing_left_out_came_in():
    """No provider task IDs, credit balances or raw provider records in the copied files."""
    import json

    for name in ("screen.json", "main.json", "after-the-fact.json"):
        text = json.dumps(archive.load(f"{archive.RIGETTI}/{name}"))
        for word in ("task_ids", "job_id", "balance", "credit", "record_fields"):
            assert word not in text, (name, word)
