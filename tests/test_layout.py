# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
import json

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
