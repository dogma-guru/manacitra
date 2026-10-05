# Copyright 2026 Anish Patel
# SPDX-License-Identifier: Apache-2.0
import numpy as np
import pytest

from manacitra.backends.base import MapJob
from manacitra.backends.simulator import (
    NoiseModel,
    PairNoise,
    SimulatorBackend,
    aer_available,
    exact_distribution_numpy,
    gap_sensitivity,
)
from manacitra.circuits import ideal_value
from manacitra.verdicts import analyse_map, day_from_rounds, persistence_analysis

PAIRS = [(2 * i, 2 * i + 1) for i in range(27)]


@pytest.mark.parametrize("label", ["A no", "A off", "B no", "B off"])
def test_noise_free_matches_ideal(label):
    assert abs(exact_distribution_numpy(label, PairNoise())[3] - ideal_value(label)) < 1e-6


@pytest.mark.skipif(not aer_available(), reason="qiskit-aer not installed")
@pytest.mark.parametrize("label", ["A no", "B off", "R2", "CAL 10"])
def test_aer_and_numpy_agree(label):
    from manacitra.backends.simulator import exact_distribution_aer

    n = PairNoise(p2=0.01, p1=(0.001, 0.0005), readout=((0.01, 0.02), (0.005, 0.03)), delta=0.02)
    assert np.abs(exact_distribution_aer(label, n) - exact_distribution_numpy(label, n)).max() < 1e-12


def test_planted_over_rotation_moves_k_as_in_kickoff_36():
    assert gap_sensitivity("A") == pytest.approx(-4.01, abs=0.01)
    assert gap_sensitivity("B") == pytest.approx(-1.50, abs=0.01)


def test_readout_is_x():
    n = PairNoise(p2=0.01, readout=((0.01, 0.03), (0.02, 0.02)))
    assert n.x == pytest.approx(0.01 + 0.02 + 0.02)


def run(model, seed=7, shots=8000):
    sim = SimulatorBackend(model, seed=seed, engine="numpy")
    c = sim.fetch(sim.submit(MapJob(PAIRS, shots=shots)))
    return analyse_map(c.p11(), c.order, x=sim.target().x_of(PAIRS), shots=shots, seed=36)


def test_the_rule_says_no_and_yes():
    base = NoiseModel.random(PAIRS, seed=1)
    assert run(base)["verdict"]["verdict"] in ("NOISE", "REDUNDANT")
    planted, deltas = base.planted(0.03, seed=3602)
    an = run(planted)
    assert an["verdict"]["verdict"] == "DIAGNOSTIC"
    assert np.corrcoef(an["kA"], [deltas[p] for p in PAIRS])[0, 1] < -0.6


def test_same_seed_same_counts():
    base = NoiseModel.random(PAIRS[:3], seed=1)
    a = SimulatorBackend(base, seed=3, engine="numpy").run(MapJob(PAIRS[:3]))
    b = SimulatorBackend(base, seed=3, engine="numpy").run(MapJob(PAIRS[:3]))
    assert all((x == y).all() for x, y in zip(a.outcomes, b.outcomes))


def persistence_days(model_of_day, shots):
    """Three days of Kickoff 35's design on 27 pairs in three rounds of 9."""
    from manacitra.verdicts import ORDER_PERSIST

    rounds = {f"R{r + 1}": [PAIRS[i] for i in range(27) if i % 3 == r] for r in range(3)}
    days = {}
    for d in (1, 2, 3):
        sim = SimulatorBackend(model_of_day(d), seed=3610 + d, engine="numpy")
        P_by_pos = []
        for pos, (rname, v) in enumerate(ORDER_PERSIST, start=1):
            prs = rounds[rname]
            P_by_pos.append(
                [
                    np.random.default_rng(np.random.SeedSequence(3610 + d, spawn_key=(pos, i))).binomial(
                        shots, sim.distribution(f"A {v}", p)[3]
                    )
                    / shots
                    for i, p in enumerate(prs)
                ]
            )
        x = {p: sim.noise.of(p).x for p in PAIRS}
        days[d] = day_from_rounds(rounds, P_by_pos, x, shots)
    return days


def test_persistence_holds_for_a_fixed_map_and_fades_for_a_scrambled_one():
    base, _ = NoiseModel.random(PAIRS, seed=1).planted(0.03, seed=3602)
    static = persistence_analysis(persistence_days(lambda d: base, 200_000))
    assert static["verdict"]["verdict"] == "HOLDS"
    rng = np.random.default_rng(3620)
    perms = {1: list(range(27)), 2: list(rng.permutation(27)), 3: list(rng.permutation(27))}
    scrambled = persistence_analysis(persistence_days(lambda d: base.permuted(perms[d]), 200_000))
    assert scrambled["verdict"]["verdict"] == "FADES"
    assert scrambled["original_rule"]["verdict"] == "FADES"
