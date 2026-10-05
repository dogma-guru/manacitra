# Copyright 2026 Anish Patel
# SPDX-License-Identifier: Apache-2.0
"""The kept share k: the fraction of a circuit's known gap that a pair kept.

    k = (P_off - P_no) / gap

with P the measured P(11) of the offset and no-offset variants on that pair, and gap the ideal difference (0.037765 for
circuit A, 0.142037 for circuit B). k = 1 means the pair kept all of the difference; k = 0 means it kept none of it.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np

from .circuits import GAP, HALVES


def kept_share(p_off, p_no, circuit: str = "A"):
    """k = (P_off - P_no) / gap, elementwise."""
    return (np.asarray(p_off, float) - np.asarray(p_no, float)) / GAP[circuit]


def kept_from_order(P, order: Sequence[str], circuit: str, positions: Sequence[int] | None = None):
    """k per pair from a per-circuit, per-pair P(11) table laid out in a fixed order.

    P has one row per circuit position (in `order`) and one column per pair. `positions`, 1-based, restricts the
    circuits used (a split half). Returns (k, mean P_off, mean P_no) per pair.
    """
    P = np.asarray(P, float)
    idx = [
        i for i, label in enumerate(order) if label.startswith(circuit) and (positions is None or (i + 1) in positions)
    ]
    off = np.mean([P[i] for i in idx if order[i].endswith("off")], axis=0)
    no = np.mean([P[i] for i in idx if order[i].endswith("no")], axis=0)
    return (off - no) / GAP[circuit], off, no


def split_halves(P, order: Sequence[str], circuit: str, halves=None):
    """k per pair from each of the two fixed halves (Kickoff 34: A 1, 2, 15, 16 against 7, 8, 9, 10)."""
    h1, h2 = (halves or HALVES)[circuit]
    return kept_from_order(P, order, circuit, h1)[0], kept_from_order(P, order, circuit, h2)[0]


def shot_noise_sd(p_off, p_no, shots_off: float, shots_no: float, circuit: str = "A"):
    """The shot-noise SD of k for one pair, from binomial counting on each variant."""
    p_off, p_no = np.asarray(p_off, float), np.asarray(p_no, float)
    return np.sqrt(p_off * (1 - p_off) / shots_off + p_no * (1 - p_no) / shots_no) / GAP[circuit]


def expected_shot_noise_sd(p_off: float, p_no: float, shots_per_variant: int, circuit: str = "A") -> float:
    """The shot-noise SD of k at a given shot count per variant, for planning a run."""
    return float(
        math.sqrt(p_off * (1 - p_off) / shots_per_variant + p_no * (1 - p_no) / shots_per_variant) / GAP[circuit]
    )


# --------------------------------------------------------------------------- counts to P(11)
def p11_from_bitstrings(counts: dict[str, int], n_pairs: int) -> np.ndarray:
    """P(11) per pair from Qiskit-style bitstring counts (rightmost character = classical bit 0), pair i measured
    into classical bits 2i and 2i + 1."""
    tot = sum(counts.values())
    p = np.zeros(n_pairs)
    for bits, m in counts.items():
        b = bits.replace(" ", "")[::-1]
        for i in range(n_pairs):
            if b[2 * i] == "1" and b[2 * i + 1] == "1":
                p[i] += m
    return p / tot


def pair_outcomes_from_bitstrings(counts: dict[str, int], n_pairs: int) -> np.ndarray:
    """Per pair, the counts of the four outcomes, indexed s = a + 2 b (a the pair's first qubit's bit, b its second's).

    Same bit convention as p11_from_bitstrings. Returns an (n_pairs, 4) integer array.
    """
    out = np.zeros((n_pairs, 4), dtype=np.int64)
    for bits, m in counts.items():
        b = bits.replace(" ", "")[::-1]
        for i in range(n_pairs):
            out[i, int(b[2 * i]) + 2 * int(b[2 * i + 1])] += m
    return out


def p11_from_outcomes(outcomes) -> np.ndarray:
    """P(11) per pair from (n_pairs, 4) outcome counts indexed s = a + 2 b."""
    o = np.asarray(outcomes, float)
    return o[..., 3] / o.sum(axis=-1)
