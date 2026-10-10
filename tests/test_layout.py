# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
import json

import numpy as np

from manacitra import archive, layout


def fez_edges():
    return [tuple(e) for e in json.loads((archive.data_dir() / "ibm_fez" / "coupling-map.json").read_text())["edges"]]


def test_disjoint_pairs_by_score():
    scores = {(0, 1): 0.03, (1, 2): 0.01, (2, 3): 0.02, (3, 4): 0.015, (4, 5): 0.05}
    out = layout.disjoint_pairs_by_score(scores)
    assert [p for p, _ in out] == [(1, 2), (3, 4)]
    assert [p for p, _ in layout.disjoint_pairs_by_score(scores, 1)] == [(1, 2)]
    assert layout.published_score(0.002, 0.004, 0.005) == 0.011


def test_disjoint_pairs_in_order():
    edges = [(0, 1), (1, 0), (1, 2), (2, 3), (4, 5)]
    out = layout.disjoint_pairs_in_order(edges)
    assert [c["pair"] for c in out] == [(0, 1), (2, 3), (4, 5)]
    assert [c["edge_index"] for c in out] == [0, 3, 4]


def test_fez_splits_into_three_rounds():
    edges = fez_edges()
    assert len(edges) == 176 and layout.max_degree(edges) == 3
    rounds, method = layout.edge_rounds(edges)
    assert len(rounds) == 3 and "bipartite" in method
    assert sorted(len(r) for r in rounds) == [57, 59, 60]  # as on ibm_fez in Kickoff 35
    assert sum(len(r) for r in rounds) == 176
    g_rounds, _ = layout.edge_rounds(edges, method="greedy")
    assert sum(len(r) for r in g_rounds) == 176 and len(g_rounds) >= 3  # the count is reported, not assumed


def test_separated_and_pick():
    nb = layout.neighbours([(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)])
    assert not layout.separated((0, 1), (2, 3), nb)
    assert layout.separated((0, 1), (3, 4), nb)
    assert layout.pick_pairs([0.5, 0.9, 0.1], 2) == [1, 0]
    assert layout.pick_pairs([0.5, 0.9, 0.1], 2, highest=False) == [2, 0]


# --------------------------------------------------------------------------- Amendment A15: pick by distance from k = 1
def test_pick_by_kept_share_ranks_by_distance_from_the_ideal():
    """A pair at k 4.6 (plain level 0.52, above the dead-pair floor) is not a pair that kept more: it is the furthest
    from the ideal and is not picked; a pair at k 1.0 is picked first; a dead pair is left out."""
    k = [0.80, 4.60, 1.00, 1.10, 0.95, 1.05]
    level = [0.90, 0.52, 0.93, 0.91, 0.30, 0.92]
    got = layout.pick_by_kept_share(k, 3, level)
    assert got[0] == 2 and 1 not in got and 4 not in got
    assert got == [2, 5, 3]  # |1 - k|: 0.00, 0.05, 0.10 (the 0.95 pair is dead)
    assert layout.pick_by_kept_share([0.9, 1.1], 2) == [0, 1], "ties go to the lower index"
    assert layout.pick_pairs(k, 1) == [1], "highest first, as Kickoff 33 ran it, takes the k 4.6 pair"


def test_on_kickoff_35s_whole_chip_map():
    """Day 3 of Kickoff 35 (ibm_fez, all 176 couplers): among the usable pairs, highest first puts 33-34 first (its k
    is far above 1 at a plain level near 0.5); by distance from the ideal it is not in the top 8. Read from the file."""
    import json

    an = json.loads((archive.data_dir() / "ibm_fez" / "k35-day3.json").read_text())["archived"]["analysis"]
    edges, k, level = [tuple(e) for e in an["edges"]], np.asarray(an["k"]), np.asarray(an["P_no"])
    usable = layout.usable_pairs(level)
    highest = max(usable, key=lambda i: k[i])
    assert edges[highest] == (33, 34) and k[highest] > 4 and level[highest] < 0.55
    assert edges.index((33, 34)) not in layout.pick_by_kept_share(k, 8, level)


def test_the_historical_rule_reproduces_kickoff_33s_pick():
    """On the Kickoff 33 prior map (Kickoff 32's dense condition), highest first gives the archived map pick, the
    literal in tests/test_payoff_recompute.py that tests/_independent_readings.py computed without the package."""
    from test_payoff_recompute import INDEPENDENT

    fez = archive.fez_or_kingston("ibm_fez")
    k31, k32, k33 = fez["k31-map"], fez["k32-isolation"], fez["k33-payoff"]
    prior = archive.isolation_analysis(k32, k31["pairs"], k31["archived"]["analysis"]["kA"])
    assert [k33["pairs"][i] for i in layout.pick_pairs(prior["kD_all27"], 8)] == INDEPENDENT["pick_by_map"]
