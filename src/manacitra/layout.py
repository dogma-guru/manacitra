# Copyright 2026 Anish Patel
# SPDX-License-Identifier: Apache-2.0
"""Pairs on a coupling map: disjoint pairs, rounds of disjoint pairs that cover every edge, and pair choice by score.

* disjoint_pairs_by_score: Kickoff 31's choose_pairs. Score x = two-qubit error plus both readout errors, lowest first,
  greedy, no qubit used twice.
* disjoint_pairs_in_order: Kickoff 34b's candidate rule, for a provider that publishes no score: edges in index order,
  each counted once, a pair accepted if neither qubit is taken.
* edge_rounds: every edge, split into the fewest rounds of disjoint pairs. A heavy-hex map has no qubit with more than
  three neighbours and no odd cycle, so three rounds suffice (Konig's edge-colouring theorem); the round count is
  reported, never assumed.
* pick_pairs: the n pairs with the highest kept share (or lowest published score).
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

import numpy as np

Edge = tuple[int, int]


def published_score(two_qubit_error: float, readout_a: float, readout_b: float) -> float:
    """x = two-qubit error + readout error of each qubit (the score the published pair choice used)."""
    return two_qubit_error + readout_a + readout_b


def undirected(edges: Iterable[Sequence[int]]) -> list[Edge]:
    """Each coupled pair once, whichever way round, in first-seen order."""
    seen, out = set(), []
    for a, b in edges:
        key = (min(a, b), max(a, b))
        if key not in seen:
            seen.add(key)
            out.append(key)
    return out


def disjoint_pairs_by_score(scores: dict[Edge, float], n: int | None = None) -> list[tuple[Edge, float]]:
    """Greedy disjoint pairs, lowest score first (Kickoff 31's choose_pairs); ties go to the lower pair."""
    best: dict[Edge, float] = {}
    for (a, b), v in scores.items():
        if v is None:
            continue
        key = (min(a, b), max(a, b))
        best[key] = min(best.get(key, float("inf")), v)
    used, out = set(), []
    for (a, b), v in sorted(best.items(), key=lambda kv: (kv[1], kv[0])):
        if a in used or b in used:
            continue
        out.append(((a, b), v))
        used |= {a, b}
        if n is not None and len(out) == n:
            break
    return out


def disjoint_pairs_in_order(edges: Sequence[Sequence[int]]) -> list[dict]:
    """Kickoff 34b's candidates: edges in index order, each once, accepted if neither qubit is taken, to the end."""
    seen, used, out = set(), set(), []
    for idx, (a, b) in enumerate(edges):
        key = (min(a, b), max(a, b))
        if key in seen:
            continue
        seen.add(key)
        if a in used or b in used:
            continue
        out.append({"edge_index": idx, "pair": (a, b)})
        used |= {a, b}
    return out


def edge_rounds(edges: Iterable[Sequence[int]], method: str = "auto") -> tuple[list[list[Edge]], str]:
    """Split every edge into rounds of disjoint pairs. Returns (rounds, the method used).

    method "auto" uses rustworkx's bipartite edge colouring (as Kickoff 35 did on ibm_fez, which gives the maximum
    degree in rounds on a bipartite map) and falls back to Misra-Gries on a map that is not bipartite. "greedy" takes
    the edges in order and puts each in the first round where both its qubits are free.
    """
    es = undirected(edges)
    if method == "greedy":
        rounds: list[list[Edge]] = []
        busy: list[set[int]] = []
        for a, b in es:
            for r, used in enumerate(busy):
                if a not in used and b not in used:
                    rounds[r].append((a, b))
                    used |= {a, b}
                    break
            else:
                rounds.append([(a, b)])
                busy.append({a, b})
        used_method = "greedy"
    else:
        import rustworkx as rx

        g = rx.PyGraph()
        n = 1 + max(max(e) for e in es)
        g.add_nodes_from(range(n))
        idx = {g.add_edge(a, b, None): (a, b) for a, b in es}
        try:
            col = rx.graph_bipartite_edge_color(g)
            used_method = "rustworkx.graph_bipartite_edge_color"
        except Exception as ex:  # not bipartite
            col = rx.graph_misra_gries_edge_color(g)
            used_method = f"rustworkx.graph_misra_gries_edge_color ({type(ex).__name__})"
        k = max(col.values()) + 1
        rounds = [[idx[i] for i, c in sorted(col.items()) if c == r] for r in range(k)]
    for R in rounds:
        qs = [q for e in R for q in e]
        if len(qs) != len(set(qs)):
            raise AssertionError("a round holds two pairs that share a qubit")
    return rounds, used_method


def max_degree(edges: Iterable[Sequence[int]]) -> int:
    deg: dict[int, int] = {}
    for a, b in undirected(edges):
        deg[a] = deg.get(a, 0) + 1
        deg[b] = deg.get(b, 0) + 1
    return max(deg.values()) if deg else 0


def neighbours(edges: Iterable[Sequence[int]]) -> dict[int, set[int]]:
    nb: dict[int, set[int]] = {}
    for a, b in edges:
        nb.setdefault(a, set()).add(b)
        nb.setdefault(b, set()).add(a)
    return nb


def separated(p: Sequence[int], q: Sequence[int], nb: dict[int, set[int]]) -> bool:
    """True if no qubit of pair p is a qubit of q or coupled to one (graph distance at least 2; Kickoff 32)."""
    for a in p:
        if a in q or nb.get(a, set()) & set(q):
            return False
    return True


def pick_pairs(values, n: int = 8, highest: bool = True) -> list[int]:
    """Indices of the n pairs with the highest values (a kept-share map) or the lowest (a published score)."""
    v = np.asarray(values, float)
    return [int(i) for i in np.argsort(-v if highest else v)[:n]]
