# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
import numpy as np
import pytest

from manacitra import verdicts as v


@pytest.mark.parametrize(
    "args,expected",
    [
        ((0.2, 0.9, 0.0, 0.8, 0.0), "NOISE"),
        ((0.8, 0.9, 0.0, 0.8, 0.6), "REDUNDANT"),  # |r_Ax| >= 0.5
        ((0.8, 0.9, 0.0, 0.1, 0.2), "REDUNDANT"),  # r_AB >= 0.4 with r_AB.x < 0.15
        ((0.8, 0.9, 0.001, 0.8, -0.2), "DIAGNOSTIC"),
        ((0.8, 0.9, 0.06, 0.8, -0.2), "NOT SETTLED"),  # p not below 0.05
        ((0.4, 0.9, 0.0, 0.8, -0.2), "NOT SETTLED"),  # r_split between 0.3 and 0.5
        ((0.8, 0.3, 0.0, 0.8, -0.2), "NOT SETTLED"),  # no transfer
        ((0.8, 0.9, 0.0, 0.2, -0.2), "NOT SETTLED"),  # partial between 0.15 and 0.3
    ],
)
def test_map_rule(args, expected):
    out = v.map_verdict(*args)
    assert out.verdict == expected
    assert set(out.inputs) == {"r_split_A", "r_AB", "p_AB", "r_AB_given_x", "r_Ax"}


@pytest.mark.parametrize(
    "args,expected",
    [
        ((0.2, 0.9, 0.0), "NOISE"),
        ((0.6, 0.5, 0.01), "MAP PRESENT"),
        ((0.45, 0.9, 0.0), "NOT SETTLED"),
        ((0.6, 0.5, 0.2), "NOT SETTLED"),
    ],
)
def test_map_rule_capped_without_a_score(args, expected):
    out = v.map_verdict(*args)
    assert out.verdict == expected and "capped" in out.rule


def test_map_rule_wants_both_or_neither():
    with pytest.raises(ValueError):
        v.map_verdict(0.8, 0.9, 0.0, 0.5, None)


@pytest.mark.parametrize(
    "args,expected",
    [
        ((0.6, 0.001, (0.0004, 0.002)), "USEFUL"),
        ((0.1, 0.4, (0.0001, 0.001)), "NOT USEFUL"),
        ((0.6, 0.001, (-0.002, 0.0)), "NOT USEFUL"),
        ((0.29, 0.07, (0.0001, 0.0008)), "NOT SETTLED"),
        ((0.6, 0.001, (-0.0001, 0.002)), "NOT SETTLED"),
    ],
)
def test_payoff_rule(args, expected):
    assert v.payoff_verdict(*args).verdict == expected


@pytest.mark.parametrize(
    "c12,c13,wo,n,expected",
    [
        (0.9, 0.9, 0.6, 3, "HOLDS"),
        (0.3, 0.9, 0.6, 3, "FADES"),
        (0.9, 0.9, 0.4, 3, "PARTIAL"),
        (None, None, 0.0, 3, "PARTIAL"),
        (0.8, None, None, 2, "HOLDS"),
        (0.2, None, None, 2, "FADES"),
    ],
)
def test_persistence_original(c12, c13, wo, n, expected):
    assert v.persistence_verdict_original(c12, c13, wo, n).verdict == expected


def test_persistence_a1():
    rel = {1: 0.9, 2: 0.9, 3: 0.9}
    corr = {(1, 2): 0.9, (1, 3): 0.8}
    assert v.persistence_verdict_a1(rel, corr, {(1, 3): 0.4}).verdict == "HOLDS"
    assert v.persistence_verdict_a1(rel, corr, {(1, 3): 0.3}).verdict == "PARTIAL"
    assert v.persistence_verdict_a1(rel, {(1, 2): 0.3, (1, 3): 0.9}, {(1, 3): 0.9}).verdict == "FADES"
    assert v.persistence_verdict_a1({1: 0.2, 2: 0.4, 3: 0.9}, {}, {}).verdict == "NOT SETTLED (too noisy)"
    # a day below the floor is skipped: days 2 and 3 are the pair
    out = v.persistence_verdict_a1({1: -0.1, 2: 0.6, 3: 0.7}, {(2, 3): 0.2}, {(2, 3): 0.0})
    assert out.verdict == "FADES" and out.inputs["fades_pair"] == [2, 3]


def _planted_table(n=27, sigma=0.15, noise=0.03, seed=5, x_tied=False):
    from test_keptshare import synthetic_table

    rng = np.random.default_rng(seed)
    true = 0.85 + sigma * rng.normal(size=n)
    x = rng.uniform(0.005, 0.02, n) if not x_tied else 1 - true + 0.001 * rng.normal(size=n)
    P = synthetic_table(true, 0.9 + 0.5 * (true - 0.85), base=0.75)
    P = np.clip(P + noise * 0.037765 * rng.normal(size=P.shape), 0, 1)
    return P, x


def test_analyse_map_finds_a_hidden_map_and_calls_a_published_one_redundant():
    from manacitra.circuits import ORDER_16

    P, x = _planted_table()
    assert v.analyse_map(P, ORDER_16, x=x, seed=1)["verdict"]["verdict"] == "DIAGNOSTIC"
    P, x = _planted_table(x_tied=True)
    assert v.analyse_map(P, ORDER_16, x=x, seed=1)["verdict"]["verdict"] == "REDUNDANT"
    P, _ = _planted_table(sigma=0.0, noise=1.0)
    assert v.analyse_map(P, ORDER_16, x=None, seed=1)["verdict"]["verdict"] == "NOISE"


def test_dead_pair_filter():
    from manacitra.circuits import ORDER_16

    P, _ = _planted_table(n=24)
    P[:, :3] = 0.3  # three broken pairs
    out = v.analyse_map(P, ORDER_16, x=None, dead_pair_floor=0.5)
    assert out["dead_pair_filter"]["excluded"] == [0, 1, 2] and out["n_pairs"] == 21
    P[:, :6] = 0.3
    assert v.analyse_map(P, ORDER_16, dead_pair_floor=0.5)["verdict"]["note"].startswith("too few")


def test_payoff_analysis_on_a_planted_payoff():
    rng = np.random.default_rng(2)
    k = rng.normal(0.9, 0.15, 27)
    x = rng.uniform(0.005, 0.02, 27)
    W = 0.995 + 0.01 * (k[:, None] - 0.9) + 0.0005 * rng.normal(size=(27, 8))
    out = v.analyse_payoff(W, k, x, n_boot=500, n_permutations=500)
    assert out["verdict"]["verdict"] == "USEFUL"
    W0 = 0.995 + 0.0005 * rng.normal(size=(27, 8))
    assert v.analyse_payoff(W0, k, x, n_boot=500, n_permutations=500)["verdict"]["verdict"] != "USEFUL"


def test_decile_ties_are_broken_by_edge_order():
    """Amendment A7: a tie at the decile's edge goes to the earlier edge, as Kickoff 36's specification of the analysis
    says (Kickoff 35's Day 3 had three edges tied at ranks 18 to 20). Before, numpy's default sort left it to chance."""
    from manacitra.verdicts import _decile_overlap

    ka = [0.0, 3.0, 3.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0]  # ten edges: a decile of one; edges 1 and 2 tie for best
    kb = [0.0, 0.0, 9.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0]  # edge 2 is best
    assert _decile_overlap(ka, kb, worst=False) == (0.0, 1)  # edge 1, the earlier, is a's best
    assert _decile_overlap(ka[::-1], kb[::-1], worst=False) == (1.0, 1)  # reversed, edge 2 comes first
    for _ in range(20):  # and the answer does not change from call to call
        assert _decile_overlap(ka, kb, worst=False) == (0.0, 1)
