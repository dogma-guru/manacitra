# Copyright 2026 Anish Patel
# SPDX-License-Identifier: Apache-2.0
"""The experimental Cirq path: a simulation of a published noise model, never hardware."""

import numpy as np
import pytest

pytest.importorskip("cirq_google")
pytest.importorskip("ply")

from manacitra.backends.cirq_sim import CirqSimBackend, cirq_block, qubit_numbers  # noqa: E402
from manacitra.backends.simulator import PairNoise, exact_distribution_numpy  # noqa: E402
from manacitra.circuits import ideal_value  # noqa: E402


@pytest.fixture(scope="module")
def pauli():
    return CirqSimBackend(noise="pauli")


def test_device_as_published(pauli):
    t = pauli.target()
    assert t.n_qubits == 105 and len(t.coupling_map) == 182 and t.two_qubit_gate == "cz"
    assert "not a measurement" in t.notes[0]


@pytest.mark.parametrize("label", ["A no", "A off", "B no", "B off"])
def test_ideal_through_qasm_and_cirq(label):
    be = CirqSimBackend(noise="none")
    assert abs(be.distribution(label, (0, 1))[3] - ideal_value(label)) < 1e-6


def test_three_native_cz(pauli):
    import cirq

    c = cirq_block("A off", pauli.grid(0), pauli.grid(1))
    assert sum(1 for op in c.all_operations() if isinstance(op.gate, cirq.CZPowGate)) == 3


def test_same_published_noise_same_distribution_as_the_simulator(pauli):
    e = pauli.target().coupling_map[0]
    f = pauli.target().pairs[e]
    n0, n1 = (qubit_numbers(pauli.cal, pauli.grid(q)) for q in e)
    pn = PairNoise(
        p2=f.two_qubit_error,
        p1=(n0["rb_pauli_error_1q"], n1["rb_pauli_error_1q"]),
        readout=((n0["p00_error"], n0["p11_error"]), (n1["p00_error"], n1["p11_error"])),
    )
    for label in ("A no", "A off"):
        assert np.abs(pauli.distribution(label, e) - exact_distribution_numpy(label, pn)).max() < 1e-12
