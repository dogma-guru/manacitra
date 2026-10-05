# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
import numpy as np

from manacitra import keptshare as ks
from manacitra.circuits import ORDER_16


def test_kept_share_definition():
    assert ks.kept_share(1.0, 0.962235, "A") == 1.0 or abs(ks.kept_share(1.0, 0.962235, "A") - 1) < 1e-12
    assert abs(ks.kept_share(0.9, 0.9, "B")) < 1e-15
    assert np.allclose(ks.kept_share([0.95, 0.93], [0.93, 0.93], "A"), [0.02 / 0.037765, 0])


def synthetic_table(kA, kB, base=0.9):
    """P per position: no-offset at base, offset at base + k * gap, identical copies."""
    kA, kB = np.asarray(kA), np.asarray(kB)
    rows = []
    for label in ORDER_16:
        circ, v = label.split()
        k = kA if circ == "A" else kB
        gap = 0.037765 if circ == "A" else 0.142037
        rows.append(base + (k * gap if v == "off" else 0 * k))
    return np.array(rows)


def test_kept_from_order_and_halves():
    kA, kB = np.array([0.2, 0.8, 1.0]), np.array([0.5, 0.9, 1.1])
    P = synthetic_table(kA, kB)
    assert np.allclose(ks.kept_from_order(P, ORDER_16, "A")[0], kA)
    assert np.allclose(ks.kept_from_order(P, ORDER_16, "B")[0], kB)
    h1, h2 = ks.split_halves(P, ORDER_16, "A")
    assert np.allclose(h1, kA) and np.allclose(h2, kA)


def test_shot_noise_sd():
    sd = ks.shot_noise_sd(0.95, 0.92, 32000, 32000, "A")
    assert abs(sd - np.sqrt(0.95 * 0.05 / 32000 + 0.92 * 0.08 / 32000) / 0.037765) < 1e-12
    assert abs(ks.expected_shot_noise_sd(0.95, 0.92, 32000) - sd) < 1e-12


def test_bitstring_parsing():
    # two pairs: pair 0 on clbits 0, 1; pair 1 on clbits 2, 3; rightmost character is clbit 0
    counts = {"1111": 5, "0011": 3, "1100": 2, "0110": 10}
    p = ks.p11_from_bitstrings(counts, 2)
    assert np.allclose(p, [8 / 20, 7 / 20])
    o = ks.pair_outcomes_from_bitstrings(counts, 2)
    # "0110": clbit0 = 0, clbit1 = 1, clbit2 = 1, clbit3 = 0 -> pair 0 s = 0 + 2 = 2; pair 1 s = 1
    assert o[0].tolist() == [2, 0, 10, 8] and o[1].tolist() == [3, 10, 0, 7]
    assert np.allclose(ks.p11_from_outcomes(o), p)
