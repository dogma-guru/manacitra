# Copyright 2026 Anish Patel
# SPDX-License-Identifier: Apache-2.0
import numpy as np
import pytest
from qiskit import QuantumCircuit

from manacitra import circuits as c


@pytest.mark.parametrize("label", [f"{k} {v}" for k in "AB" for v in ("no", "off", "wrong")])
def test_ideal_values_by_statevector(label):
    assert abs(c.ideal_p11(label) - c.ideal_value(label)) < 1e-6


def test_gaps_and_tstar():
    assert c.GAP == {"A": 0.037765, "B": 0.142037}
    assert c.CIRCUITS["A"].gap == 0.037765 and c.CIRCUITS["B"].gap == 0.142037
    assert abs(c.tstar(0.125) - 4 * np.pi / np.sqrt(65)) < 1e-12
    assert abs(c.tstar(0.25) - 2 * np.pi / np.sqrt(17)) < 1e-12


@pytest.mark.parametrize("label", ["A no", "A off", "B no", "B off", "A wrong"])
def test_exactly_three_cz_and_exact_unitary(label):
    from qiskit.quantum_info import Operator

    qc = c.block(label)
    assert qc.count_ops()["cz"] == 3
    circ, _ = c.parse_label(label)
    u = c.unitary(c.CIRCUITS[circ].c, c.offset_of(label))
    assert abs(abs(np.vdot(Operator(qc).data.flatten(), u.flatten())) / 4 - 1) < 1e-10


def test_variants_differ_only_in_single_qubit_angles():
    a, b = c.block("A no"), c.block("A off")
    pos = lambda qc: [i for i, ins in enumerate(qc.data) if ins.operation.name == "cz"]  # noqa: E731
    assert len(pos(a)) == len(pos(b)) == 3


def test_orders_and_halves():
    assert c.ORDER_16 == c.ORDER_18[:16]
    assert c.HALVES["A"] == ([1, 2, 15, 16], [7, 8, 9, 10])
    for circ, (h1, h2) in c.HALVES.items():
        for h in (h1, h2):
            labels = [c.ORDER_16[p - 1] for p in h]
            assert sorted(labels) == sorted([f"{circ} no", f"{circ} no", f"{circ} off", f"{circ} off"])


def test_parallel_circuit_and_gate_count():
    qc = c.parallel_circuit("A off", 3)
    pairs = [(0, 1), (2, 3), (4, 5)]
    assert c.require_three_per_pair(qc.remove_final_measurements(inplace=False), pairs)["two_qubit_per_pair"] == [3]


def test_refuses_anything_but_three_per_pair():
    qc = QuantumCircuit(4)
    for _ in range(3):
        qc.cz(0, 1)
    for _ in range(4):
        qc.cz(2, 3)
    with pytest.raises(ValueError, match="refused"):
        c.require_three_per_pair(qc, [(0, 1), (2, 3)])
    qc2 = QuantumCircuit(4)
    for _ in range(3):
        qc2.cz(0, 1)
        qc2.cz(2, 3)
    qc2.cz(1, 2)  # a gate between two pairs
    with pytest.raises(ValueError, match="refused"):
        c.require_three_per_pair(qc2, [(0, 1), (2, 3)])
    qc3 = QuantumCircuit(4)
    for _ in range(3):
        qc3.cz(0, 1)
        qc3.cz(2, 3)
    qc3.swap(0, 1)
    with pytest.raises(ValueError, match="refused"):
        c.require_three_per_pair(qc3, [(0, 1), (2, 3)])


def test_unknown_label():
    with pytest.raises(ValueError):
        c.parse_label("C no")


def test_pinned_circuits_are_the_exact_unitaries():
    """The package runs pinned gate lists, the same on every platform; each must be its exact unitary."""
    import subprocess
    import sys
    from pathlib import Path

    tool = Path(__file__).resolve().parent.parent / "tools" / "pin_circuits.py"
    assert subprocess.run([sys.executable, str(tool), "--check"], capture_output=True).returncode == 0


def test_block_is_pinned_and_synthesis_is_equivalent():
    from qiskit.quantum_info import Operator

    for label in ("A no", "B off"):
        pinned, fresh = c.block(label), c.block(label, synthesise=True)
        assert c.circuit_record(pinned) == c.pinned()["blocks"][label]
        u, v = Operator(pinned).data, Operator(fresh).data
        assert abs(abs(np.vdot(u.flatten(), v.flatten())) / 4 - 1) < 1e-10
