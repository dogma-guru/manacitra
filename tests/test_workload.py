# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
import numpy as np
import pytest

from manacitra import archive, workload


def test_the_draw_matches_the_archive():
    arch = archive.load("workload/k33-workload.json")
    units = workload.draw_unitaries(33)
    for c, ac in zip(units, arch["unitaries"]):
        for U, au in zip(c, ac):
            assert np.abs(U - (np.array(au["re"]) + 1j * np.array(au["im"]))).max() < 1e-12
    for p, ac in zip(workload.ideal_distributions(33), arch["circuits"]):
        assert np.abs(p - np.array(ac["ideal"])).max() < 1e-12


@pytest.mark.parametrize("j", range(8))
def test_nine_cz_and_noise_free_fidelity_one(j):
    from qiskit.quantum_info import Statevector

    units = workload.draw_unitaries(33)[j]
    qc = workload.workload_block(units)
    assert qc.count_ops()["cz"] == 9
    q = Statevector(qc).probabilities()
    assert abs(1 - workload.hellinger_fidelity(workload.ideal_distribution(units), q)) < 1e-12


def test_hellinger_and_simplex():
    p = np.array([0.5, 0.5, 0, 0])
    assert workload.hellinger_fidelity(p, p) == pytest.approx(1.0)
    assert workload.hellinger_fidelity(p, np.array([0, 0, 0.5, 0.5])) == 0.0
    s = workload.simplex_projection(np.array([0.7, 0.5, -0.1, -0.1]))
    assert abs(s.sum() - 1) < 1e-12 and (s >= 0).all()


def test_order():
    assert len(workload.ORDER_PAYOFF) == 28 and workload.ORDER_PAYOFF[4:6] == ["A no", "A off"]
