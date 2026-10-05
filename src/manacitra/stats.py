# Copyright 2026 Anish Patel
# SPDX-License-Identifier: Apache-2.0
"""Statistics used by the verdict rules, exactly as in the published runs.

Pearson r with Spearman's rho beside it; a seeded permutation p-value; the partial correlation r_AB.x by residuals of a
straight-line fit on x; the Spearman-Brown reliability; and a bootstrap over circuits for the selection gain.
"""

from __future__ import annotations

import math

import numpy as np
from scipy.stats import pearsonr, spearmanr

N_PERMUTATIONS = 10_000


def corr(a, b) -> dict[str, float]:
    """Pearson r and Spearman rho of two equal-length vectors."""
    return {"pearson": float(pearsonr(a, b)[0]), "spearman": float(spearmanr(a, b)[0])}


def corr_or_none(a, b) -> dict[str, float | None]:
    """As corr, but None where a correlation is undefined (fewer than 3 values, or a constant vector)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) < 3 or np.std(a) == 0 or np.std(b) == 0:
        return {"pearson": None, "spearman": None}
    return corr(a, b)


def permutation_p(a, b, seed: int, one_sided: bool = True, n: int = N_PERMUTATIONS) -> float:
    """The permutation p-value of Pearson r(a, b): b is shuffled n times with numpy default_rng(seed).

    One-sided: the share of shuffles with r >= the observed r. Two-sided: with |r| >= |observed r|.
    """
    rng = np.random.default_rng(seed)
    r0 = pearsonr(a, b)[0]
    rs = np.array([pearsonr(a, rng.permutation(b))[0] for _ in range(n)])
    return float(np.mean(rs >= r0)) if one_sided else float(np.mean(np.abs(rs) >= abs(r0)))


def residuals(y, x):
    """y minus its straight-line fit on x."""
    y, x = np.asarray(y, float), np.asarray(x, float)
    return y - np.polyval(np.polyfit(x, y, 1), x)


def partial_r(a, b, x) -> float:
    """The partial correlation r_ab.x: a and b each regressed on x, the residuals correlated."""
    return float(pearsonr(residuals(a, x), residuals(b, x))[0])


def spearman_brown(r: float | None) -> float | None:
    """The reliability of the full data from a split-half correlation: 2 r / (1 + r). None if undefined."""
    if r is None or r <= -1:
        return None
    return 2 * r / (1 + r)


def disattenuated(r: float | None, rel_a: float | None, rel_b: float | None) -> float | None:
    """r / sqrt(rel_a rel_b), the correlation corrected for noise. None unless both reliabilities are positive."""
    if r is None or rel_a is None or rel_b is None or rel_a <= 0 or rel_b <= 0:
        return None
    return r / math.sqrt(rel_a * rel_b)


def bootstrap_gain_over_circuits(
    per_circuit, pick, reference, seed: int, n: int = N_PERMUTATIONS, rng: np.random.Generator | None = None
) -> tuple[float, list[float], np.ndarray]:
    """The gain G = mean score of `pick` minus mean score of `reference`, with a 90% bootstrap interval over circuits.

    per_circuit has one row per pair and one column per circuit; a pair's score is its mean over circuits. Each
    resample draws the circuits with replacement and recomputes every pair's score and G. Pass `rng` to continue an
    existing generator (as Kickoff 33 did across its three picks); otherwise default_rng(seed) is used.
    """
    W_c = np.asarray(per_circuit, float)
    rng = rng if rng is not None else np.random.default_rng(seed)
    n_c = W_c.shape[1]
    W = W_c.mean(axis=1)
    g = float(W[list(pick)].mean() - W[list(reference)].mean())
    boots = np.empty(n)
    for t in range(n):
        jj = rng.integers(0, n_c, n_c)
        Wb = W_c[:, jj].mean(axis=1)
        boots[t] = Wb[list(pick)].mean() - Wb[list(reference)].mean()
    return g, [float(np.percentile(boots, 5)), float(np.percentile(boots, 95))], boots
