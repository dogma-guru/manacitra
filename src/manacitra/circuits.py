# Copyright 2026 Anish Patel
# SPDX-License-Identifier: Apache-2.0
"""The test circuits: a four-site Hamiltonian encoded in two qubits, in variants differing only in single-qubit angles.

The two qubits' four basis states 00, 01, 10, 11 are the four sites of a square. The Hamiltonian

    H = -(X0 + X1) - c X0 X1 + (a/2)(1 + Z0 Z1)

hops between neighbouring sites (X0, X1), across the diagonal (X0 X1), and puts an on-site potential a on the two sites
00 and 11. Evolved for t* = pi / (2 sqrt(1 + c^2)) from 00, it sends almost everything to 11; P(11) is read.

* With no offset (a = 0) the transfer is not quite perfect: P(11) = 0.962235 for c = 1/8 (circuit A).
* With the offset (a = -1/2 for A) the transfer is exact: P(11) = 1.
* The difference between the two, the gap, is known exactly: 0.037765 for A, 0.142037 for B (c = 1/4, a = -1).

Each variant is the exact two-qubit unitary, synthesised with exactly three CZ gates (forced KAK), so on hardware the
two variants of a circuit carry the same three two-qubit gates and differ only in single-qubit angles. Whatever a pair
does to the gap is therefore about how it carries a small, known difference through the same entangling gates.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy.linalg import expm


@dataclass(frozen=True)
class CircuitFamily:
    """One circuit of the family: the diagonal coupling c and the offset a that makes the transfer exact."""

    name: str
    c: float
    a: float
    ideal_no: float
    ideal_off: float
    ideal_wrong: float

    @property
    def gap(self) -> float:
        """The ideal difference P_off - P_no, rounded as published (6 decimals)."""
        return round(self.ideal_off - self.ideal_no, 6)

    @property
    def t_star(self) -> float:
        return tstar(self.c)


#: The two circuits. Ideal values by statevector, to 1e-6, as published in Kickoff 31.
CIRCUITS = {
    "A": CircuitFamily("A", c=0.125, a=-0.5, ideal_no=0.962235, ideal_off=1.000000, ideal_wrong=0.855691),
    "B": CircuitFamily("B", c=0.25, a=-1.0, ideal_no=0.857963, ideal_off=1.000000, ideal_wrong=0.523441),
}

#: The gap of each circuit, exactly as used in every published kept share.
GAP = {"A": 0.037765, "B": 0.142037}

#: Kickoff 31's 18-circuit order (with the wrong-sign variants at the end).
ORDER_18 = [
    "A no",
    "A off",
    "B no",
    "B off",
    "B off",
    "B no",
    "A off",
    "A no",
    "A no",
    "A off",
    "B no",
    "B off",
    "B off",
    "B no",
    "A off",
    "A no",
    "A wrong",
    "B wrong",
]

#: Kickoff 34's 16-circuit order (no wrong-sign variants); positions 1 to 16 are those of ORDER_18.
ORDER_16 = ORDER_18[:16]

#: The fixed split halves, 1-based positions in ORDER_16 / ORDER_18 (Kickoffs 31 and 34).
HALVES = {"A": ([1, 2, 15, 16], [7, 8, 9, 10]), "B": ([3, 4, 13, 14], [5, 6, 11, 12])}

VARIANTS = ("no", "off", "wrong")


def tstar(c: float) -> float:
    """The transfer time t* = pi / (2 sqrt(1 + c^2))."""
    return math.pi / (2 * math.sqrt(1 + c * c))


def hamiltonian(c: float, a: float | None) -> np.ndarray:
    """H = -(X0 + X1) - c X0 X1 + (a/2)(1 + Z0 Z1) as a 4x4 matrix in Qiskit's qubit order (qubit 0 rightmost)."""
    from qiskit.quantum_info import SparsePauliOp

    terms = [("IX", -1.0), ("XI", -1.0), ("XX", -c)]
    if a is not None:
        terms += [("ZZ", a / 2), ("II", a / 2)]
    return SparsePauliOp.from_list(terms).to_matrix()


def unitary(c: float, a: float | None) -> np.ndarray:
    """The exact evolution exp(-i H t*)."""
    return expm(-1j * hamiltonian(c, a) * tstar(c))


def parse_label(label: str) -> tuple[str, str]:
    """'A no' -> ('A', 'no'); 'B off' -> ('B', 'off'); 'A wrong' -> ('A', 'wrong')."""
    circ, kind = label.split()
    if circ not in CIRCUITS or kind not in VARIANTS:
        raise ValueError(f"unknown circuit label {label!r}")
    return circ, kind


def offset_of(label: str) -> float | None:
    """The offset a of a variant: None for 'no', a for 'off', -a for 'wrong'."""
    circ, kind = parse_label(label)
    a = CIRCUITS[circ].a
    return {"no": None, "off": a, "wrong": -a}[kind]


def ideal_value(label: str) -> float:
    """The published ideal P(11) of a variant."""
    circ, kind = parse_label(label)
    f = CIRCUITS[circ]
    return {"no": f.ideal_no, "off": f.ideal_off, "wrong": f.ideal_wrong}[kind]


def synthesise_three_cz(u: np.ndarray, euler_basis: str = "ZSX"):
    """A two-qubit unitary as a circuit with exactly three CZ gates (TwoQubitBasisDecomposer, forced KAK)."""
    from qiskit.circuit.library import CZGate
    from qiskit.synthesis import TwoQubitBasisDecomposer

    qc = TwoQubitBasisDecomposer(CZGate(), euler_basis=euler_basis)(u, _num_basis_uses=3)
    n_cz = qc.count_ops().get("cz", 0)
    if n_cz != 3:
        raise RuntimeError(f"synthesis gave {n_cz} CZ, not 3")
    return qc


def block(label: str, euler_basis: str = "ZSX"):
    """The two-qubit circuit of a variant: the exact unitary with exactly three CZ, no measurement."""
    circ, _ = parse_label(label)
    return synthesise_three_cz(unitary(CIRCUITS[circ].c, offset_of(label)), euler_basis=euler_basis)


def ideal_p11(label: str) -> float:
    """P(11) of the synthesised variant, by statevector."""
    from qiskit.quantum_info import Statevector

    return float(Statevector(block(label)).probabilities_dict().get("11", 0.0))


def ideal_table() -> dict[str, dict[str, float]]:
    """Every variant's statevector P(11) beside its published value."""
    out = {}
    for circ in CIRCUITS:
        for kind in VARIANTS:
            label = f"{circ} {kind}"
            p = ideal_p11(label)
            out[label] = {"statevector": p, "published": ideal_value(label), "diff": p - ideal_value(label)}
    return out


def parallel_circuit(label: str, n_pairs: int, measure: bool = True):
    """One variant on n pairs at once: pair i on circuit qubits 2i (its first qubit) and 2i + 1 (its second),
    measured into classical bits 2i and 2i + 1."""
    from qiskit import QuantumCircuit

    blk = block(label)
    qc = QuantumCircuit(2 * n_pairs, 2 * n_pairs) if measure else QuantumCircuit(2 * n_pairs)
    for i in range(n_pairs):
        qc.compose(blk, qubits=[2 * i, 2 * i + 1], inplace=True)
    if measure:
        qc.measure(range(2 * n_pairs), range(2 * n_pairs))
    return qc


TWO_QUBIT_GATES = ("cz", "ecr", "cx", "iswap", "rzz", "cp", "swap")


def two_qubit_gates_per_pair(circuit, pairs: list[tuple[int, int]]) -> dict[tuple[int, int], int]:
    """Count the two-qubit gates acting on each pair's physical qubits in a transpiled circuit.

    A gate that touches qubits of two different pairs, or a qubit outside every pair, is counted under the key (-1, -1).
    """
    where = {}
    for p in pairs:
        for q in p:
            where[q] = tuple(p)
    counts = {tuple(p): 0 for p in pairs}
    counts[(-1, -1)] = 0
    for ins in circuit.data:
        if ins.operation.num_qubits != 2 or ins.operation.name in ("barrier", "measure"):
            continue
        qs = [circuit.find_bit(q).index for q in ins.qubits]
        owners = {where.get(q) for q in qs}
        if len(owners) == 1 and None not in owners:
            counts[owners.pop()] += 1
        else:
            counts[(-1, -1)] += 1
    return counts


def require_three_per_pair(circuit, pairs: list[tuple[int, int]], expected: int = 3) -> dict:
    """Refuse a transpiled circuit unless every pair carries exactly `expected` two-qubit gates and nothing else does.

    Returns the check record; raises ValueError on any deviation (a swap, a routed gate, a merged or split gate).
    """
    counts = two_qubit_gates_per_pair(circuit, pairs)
    stray = counts.pop((-1, -1))
    ops = dict(circuit.count_ops())
    bad = {p: n for p, n in counts.items() if n != expected}
    record = {"two_qubit_per_pair": sorted(set(counts.values())), "outside_pairs": stray, "swap": ops.get("swap", 0)}
    if bad or stray or ops.get("swap", 0):
        raise ValueError(
            f"refused: expected {expected} two-qubit gates on every pair and none elsewhere; got {record}"
            + (f", pairs off count {dict(list(bad.items())[:5])}" if bad else "")
        )
    return record
