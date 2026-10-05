# Copyright 2026 Anish Patel
# SPDX-License-Identifier: Apache-2.0
import numpy as np

from manacitra import stats


def test_corr_and_none():
    a = np.arange(10.0)
    r = stats.corr(a, 2 * a + 1)
    assert abs(r["pearson"] - 1) < 1e-12 and abs(r["spearman"] - 1) < 1e-12
    assert stats.corr_or_none(a, np.ones(10)) == {"pearson": None, "spearman": None}


def test_permutation_p_is_seeded_and_sided():
    rng = np.random.default_rng(0)
    a = rng.normal(size=27)
    b = a + rng.normal(size=27)
    p1 = stats.permutation_p(a, b, seed=31)
    assert p1 == stats.permutation_p(a, b, seed=31)
    assert p1 < 0.01
    assert stats.permutation_p(a, -b, seed=31) > 0.99
    assert stats.permutation_p(a, -b, seed=31, one_sided=False) < 0.01


def test_partial_r_removes_a_shared_cause():
    rng = np.random.default_rng(1)
    x = rng.normal(size=500)
    a = x + 0.1 * rng.normal(size=500)
    b = x + 0.1 * rng.normal(size=500)
    assert stats.corr(a, b)["pearson"] > 0.9
    assert abs(stats.partial_r(a, b, x)) < 0.15


def test_spearman_brown_and_correction():
    assert stats.spearman_brown(0.5) == 2 * 0.5 / 1.5
    assert stats.spearman_brown(None) is None and stats.spearman_brown(-1.0) is None
    assert stats.disattenuated(0.5, 0.25, 1.0) == 1.0
    assert stats.disattenuated(0.5, -0.1, 0.8) is None
    assert stats.disattenuated(None, 0.5, 0.8) is None


def test_bootstrap_gain():
    W = np.array([[1.0, 1.0], [1.0, 1.0], [0.9, 0.9], [0.9, 0.9]])
    g, ci, _ = stats.bootstrap_gain_over_circuits(W, [0, 1], [2, 3], seed=33, n=200)
    assert abs(g - 0.1) < 1e-12 and abs(ci[0] - 0.1) < 1e-12 and abs(ci[1] - 0.1) < 1e-12
