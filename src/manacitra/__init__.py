# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""Manacitra: a map of a quantum processor's qubit pairs.

Mānacitra, from the Sanskrit māna (measure) and citra (picture), is the Hindi word for a map: a measured picture.

The public API:

    circuits    the two test circuits, their exact three-CZ synthesis and ideal values
    keptshare   k = (P_off - P_no) / gap per pair, its shot noise, the split halves
    stats       Pearson with Spearman, the permutation p, the partial r, the bootstrap
    verdicts    the map rule, the payoff rule, the persistence rule
    layout      disjoint pairs, rounds of disjoint pairs, pair choice
    workload    the random stand-in workload and its score
    backends    simulator (always available), ibm, and the experimental openquantum and cirq_sim
"""

from .circuits import CIRCUITS, GAP, HALVES, ORDER_16, ORDER_18, block, ideal_p11
from .keptshare import kept_from_order, kept_share, shot_noise_sd, split_halves
from .layout import disjoint_pairs_by_score, edge_rounds, pick_pairs
from .verdicts import analyse_map, analyse_payoff, map_verdict, payoff_verdict, persistence_analysis

__version__ = "0.1.2"

__all__ = [
    "CIRCUITS",
    "GAP",
    "HALVES",
    "ORDER_16",
    "ORDER_18",
    "block",
    "ideal_p11",
    "kept_share",
    "kept_from_order",
    "shot_noise_sd",
    "split_halves",
    "disjoint_pairs_by_score",
    "edge_rounds",
    "pick_pairs",
    "analyse_map",
    "analyse_payoff",
    "map_verdict",
    "payoff_verdict",
    "persistence_analysis",
    "__version__",
]
