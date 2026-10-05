# Copyright 2026 Anish Patel
# SPDX-License-Identifier: Apache-2.0
"""End to end on the simulator, no account needed.

27 simulated pairs get published-style figures (two-qubit error, readout errors). Half the run plants a hidden map:
each pair's CZ is followed by its own small Z over-rotation, which the published figures know nothing about. The map
rule should call the first map noise or redundant, and find the second.
"""

from manacitra.backends.base import MapJob
from manacitra.backends.simulator import NoiseModel, SimulatorBackend
from manacitra.layout import pick_pairs
from manacitra.report import verdict_lines
from manacitra.verdicts import analyse_map

pairs = [(2 * i, 2 * i + 1) for i in range(27)]
published = NoiseModel.random(pairs, seed=1)
planted, deltas = published.planted(sigma=0.03, seed=3602)

for name, noise in (("published figures only", published), ("plus a hidden per-pair map", planted)):
    sim = SimulatorBackend(noise, seed=7)
    counts = sim.fetch(sim.submit(MapJob(pairs, shots=8000)))
    x = sim.target().x_of(pairs)
    analysis = analyse_map(counts.p11(), counts.order, x=x, seed=36)
    print(f"\n{name}\n" + verdict_lines(analysis))

best = pick_pairs(analysis["kA"], n=8)
print("\nthe 8 pairs that kept most of the gap:", [pairs[i] for i in best])
