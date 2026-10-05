# Copyright 2026 Anish Patel
# SPDX-License-Identifier: Apache-2.0
"""The stand-in workload of Kickoff 33: random two-qubit circuits unrelated to the test circuits, and a pair's score.

Eight circuits R1 to R8, each a product of three Haar-random two-qubit unitaries drawn with numpy default_rng(33) in a
fixed order (circuit 1's unitaries 1, 2, 3, then circuit 2's, and so on). Each unitary is synthesised with exactly three
CZ, so every circuit carries nine. A pair's score W is the mean over the circuits of the classical (Hellinger) fidelity
(sum_s sqrt(p_s q_s))^2, with p the ideal output distribution and q the measured one. W_rc is the same after readout
correction (inverse confusion matrix, projected to the probability simplex).

Outcome index s = a + 2 b, a being the bit of the pair's first qubit and b of its second (Qiskit's order on the pair).
These circuits are a stand-in workload for choosing pairs, not a benchmark of any machine.
"""

from __future__ import annotations

import math

import numpy as np

SEED = 33
N_CIRCUITS = 8
DEPTH = 3
#: Kickoff 33's 28-circuit order: readout calibration, then two mirrored blocks
CAL_STATES = ["00", "01", "10", "11"]  # written b a; index s = a + 2 b
BLOCK1 = ["A no", "A off"] + [f"R{j}" for j in range(1, 9)] + ["A off", "A no"]
BLOCK2 = ["A no", "A off"] + [f"R{j}" for j in range(8, 0, -1)] + ["A off", "A no"]
ORDER_PAYOFF = [f"CAL {s}" for s in CAL_STATES] + BLOCK1 + BLOCK2


def haar(rng: np.random.Generator) -> np.ndarray:
    """A Haar-random 4x4 unitary: complex Gaussian (real part drawn before imaginary), QR, phases fixed by diag(R)."""
    Z = (rng.normal(size=(4, 4)) + 1j * rng.normal(size=(4, 4))) / math.sqrt(2)
    Q, R = np.linalg.qr(Z)
    d = np.diag(R)
    return Q * (d / np.abs(d))


def draw_unitaries(seed: int = SEED, n_circuits: int = N_CIRCUITS, depth: int = DEPTH) -> list[list[np.ndarray]]:
    rng = np.random.default_rng(seed)
    return [[haar(rng) for _ in range(depth)] for _ in range(n_circuits)]


def workload_block(units: list[np.ndarray]):
    """One random circuit on a pair: each unitary with exactly three CZ, in order."""
    from qiskit import QuantumCircuit

    from .circuits import synthesise_three_cz

    qc = QuantumCircuit(2)
    for U in units:
        qc.compose(synthesise_three_cz(U), qubits=[0, 1], inplace=True)
    return qc


def ideal_distribution(units: list[np.ndarray]) -> np.ndarray:
    """The exact output distribution over s = a + 2 b of the product U3 U2 U1 on |00>."""
    prod = np.eye(4, dtype=complex)
    for U in units:
        prod = U @ prod
    return np.abs(prod[:, 0]) ** 2


def ideal_distributions(seed: int = SEED) -> list[np.ndarray]:
    return [ideal_distribution(u) for u in draw_unitaries(seed)]


def hellinger_fidelity(p, q) -> float:
    """The classical (Hellinger) fidelity (sum_s sqrt(p_s q_s))^2."""
    return float(np.sum(np.sqrt(np.clip(p, 0, None) * np.clip(q, 0, None))) ** 2)


def simplex_projection(v) -> np.ndarray:
    """The Euclidean projection of v onto the probability simplex."""
    v = np.asarray(v, float)
    u = np.sort(v)[::-1]
    css = np.cumsum(u)
    rho = np.nonzero(u * np.arange(1, len(v) + 1) > (css - 1))[0][-1]
    th = (css[rho] - 1) / (rho + 1)
    return np.maximum(v - th, 0)


def aggregate(outcomes_by_position, order) -> dict[str, np.ndarray]:
    """Sum per-pair outcome counts (n_pairs, 4) over every position that carries the same label."""
    agg: dict[str, np.ndarray] = {}
    for label, o in zip(order, outcomes_by_position):
        agg[label] = agg.get(label, 0) + np.asarray(o, float)
    return agg


def readout_confusion(agg: dict[str, np.ndarray]) -> np.ndarray:
    """Per pair, M[measured, prepared] from the four calibration circuits."""
    first = agg[f"CAL {CAL_STATES[0]}"]
    M = np.zeros((first.shape[0], 4, 4))
    for s, st in enumerate(CAL_STATES):
        d = agg[f"CAL {st}"]
        M[:, :, s] = d / d.sum(axis=1, keepdims=True)
    return M


def workload_scores(agg: dict[str, np.ndarray], ideal: list, confusion: np.ndarray | None = None) -> dict:
    """W per pair and per circuit, and W_rc if a confusion matrix is given (Kickoff 33's analysis)."""
    n = agg["R1"].shape[0]
    n_c = len(ideal)
    W_c, Wrc_c, Q, ns = np.zeros((n, n_c)), np.zeros((n, n_c)), np.zeros((n, n_c, 4)), np.zeros((n, n_c))
    for j in range(n_c):
        d = agg[f"R{j + 1}"]
        q = d / d.sum(axis=1, keepdims=True)
        p = np.asarray(ideal[j], float)
        for i in range(n):
            Q[i, j] = q[i]
            ns[i, j] = d[i].sum()
            W_c[i, j] = hellinger_fidelity(p, q[i])
            if confusion is not None:
                Wrc_c[i, j] = hellinger_fidelity(p, simplex_projection(np.linalg.solve(confusion[i], q[i])))
    out = {"W_per_circuit": W_c, "W": W_c.mean(axis=1), "measured_dists": Q, "shots": ns}
    if confusion is not None:
        out.update({"W_rc_per_circuit": Wrc_c, "W_rc": Wrc_c.mean(axis=1)})
    return out
