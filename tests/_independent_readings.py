# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""The source of the expected values in tests/test_bit_readings.py (Amendment A8, R1).

This script does not import manacitra. It reads the archived JSON with the standard library, decodes each record's
counts by its own reading, written here from the data README's Formats section, and computes the statistics with numpy
alone. A test that calls the package's reader on both sides of a comparison does not test the reader; so the expected
pairs and statistics in the tests are this script's output, written in as literals.

    python tests/_independent_readings.py       prints every literal the tests use

The three readings:
* Qiskit, adjacent: the rightmost character is classical bit 0, and pair i is bits 2i and 2i + 1;
* Open Quantum, reversed: pair i is classical bits i and n - 1 - i, and classical bit k is the character at position
  n - 1 - k of the n-character key;
* Amazon Braket: character j of a key belongs to measured_qubits[j].

The kept share of a pair is the mean P(11) of the "off" positions minus that of the "no" positions of one circuit,
over all its positions or one fixed half; a correlation does not change if k is divided by the circuit's gap, so the gap
is not needed here. The level is the mean P(11) of the "A no" positions. A pair is working if its level is at least the
record's dead_pair_floor; on Amazon Braket, the verdict set is the working pairs with a published CZ fidelity (not the
placeholder 0.5), and x = (1 - CZ fidelity) + (1 - readout fidelity) of each qubit.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

DATA = Path(__file__).resolve().parents[1] / "data"
RIG = DATA / "rigetti_cepheus_1_108q"


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def p11_qiskit_adjacent(counts: dict, n_pairs: int) -> np.ndarray:
    tot, p = sum(counts.values()), np.zeros(n_pairs)
    for key, m in counts.items():
        bits = key[::-1]  # bits[k] is classical bit k
        for i in range(n_pairs):
            if bits[2 * i] == "1" and bits[2 * i + 1] == "1":
                p[i] += m
    return p / tot


def p11_openquantum_reversed(counts: dict, n_pairs: int) -> np.ndarray:
    n, tot, p = 2 * n_pairs, sum(counts.values()), np.zeros(n_pairs)
    for key, m in counts.items():
        for i in range(n_pairs):
            if key[n - 1 - i] == "1" and key[n - 1 - (n - 1 - i)] == "1":
                p[i] += m
    return p / tot


def p11_braket(counts: dict, measured_qubits: list, pairs: list) -> np.ndarray:
    col = {q: j for j, q in enumerate(measured_qubits)}
    tot, p = sum(counts.values()), np.zeros(len(pairs))
    for key, m in counts.items():
        for i, (a, b) in enumerate(pairs):
            if key[col[a]] == "1" and key[col[b]] == "1":
                p[i] += m
    return p / tot


def kept(P: np.ndarray, order: list, circuit: str, positions=None) -> np.ndarray:
    rows = [i for i, lab in enumerate(order) if lab.startswith(circuit) and (positions is None or i + 1 in positions)]
    off = np.mean([P[i] for i in rows if order[i].endswith("off")], axis=0)
    no = np.mean([P[i] for i in rows if order[i].endswith("no")], axis=0)
    return off - no


def r(a, b) -> float:
    return float(np.corrcoef(a, b)[0, 1])


def level(P: np.ndarray, order: list) -> np.ndarray:
    return np.mean([P[i] for i, lab in enumerate(order) if lab == "A no"], axis=0)


def statistics(P: np.ndarray, order: list, halves: dict, keep: list, x=None) -> dict:
    Pk = P[:, keep]
    kA = kept(Pk, order, "A")
    out = {
        "n": len(keep),
        "r_split": r(kept(Pk, order, "A", halves["A"][0]), kept(Pk, order, "A", halves["A"][1])),
        "r_AB": r(kA, kept(Pk, order, "B")),
    }
    if x is not None:
        out["r_Ax"] = r(kA, x)
    return out


def top8(values: np.ndarray, pairs: list, highest: bool = True) -> list:
    order = np.argsort(-values if highest else values, kind="stable")[:8]
    return [list(pairs[i]) for i in order]


def openquantum_main() -> dict:
    rec = load(RIG / "main.json")
    pairs, order = [tuple(p) for p in rec["pairs"]], rec["order"]
    P = np.array([p11_openquantum_reversed(c, len(pairs)) for c in rec["counts"]])
    keep = [i for i, v in enumerate(level(P, order)) if v >= rec["meta"]["dead_pair_floor"]]
    return statistics(P, order, rec["halves"], keep)


def braket_map(name: str, figures: str, part: str) -> dict:
    rec = load(RIG / name)
    pairs, order = [tuple(p) for p in rec["pairs"]], rec["order"]
    P = np.array([p11_braket(c, t["measured_qubits"], pairs) for c, t in zip(rec["counts"], rec["tasks"])])
    fig = {tuple(f["pair"]): f for f in load(RIG / figures)[part]["figures_at_submission"]}
    lev = level(P, order)
    working = [i for i, v in enumerate(lev) if v >= rec["meta"]["dead_pair_floor"]]
    vset = [i for i in working if fig[pairs[i]]["cz_fidelity"] != 0.5]
    x = np.array(
        [(1 - fig[pairs[i]]["cz_fidelity"]) + sum(1 - f for f in fig[pairs[i]]["readout_fidelity"]) for i in vset]
    )
    out = statistics(P, order, rec["halves"], vset, x)
    vpairs = [pairs[i] for i in vset]
    out["pick_by_level"] = top8(lev[vset], vpairs)
    out["pick_by_x"] = top8(x, vpairs, highest=False)
    # the same counts read with the wrong reading, IBM's adjacent bits, as the commands did before Amendment A8
    W = np.array([p11_qiskit_adjacent(c, len(pairs)) for c in rec["counts"]])
    lw = level(W, order)
    out["pick_by_level_if_read_as_qiskit_adjacent"] = top8(
        lw[[i for i, v in enumerate(lw) if v >= 0.5]], [pairs[i] for i, v in enumerate(lw) if v >= 0.5]
    )
    return out


def outcomes_braket(counts: dict, measured_qubits: list, pairs: list) -> np.ndarray:
    """Per pair, the counts of s = q0 + 2 q1, q0 the pair's first qubit."""
    col = {q: j for j, q in enumerate(measured_qubits)}
    out = np.zeros((len(pairs), 4))
    for key, m in counts.items():
        for i, (a, b) in enumerate(pairs):
            out[i, int(key[col[a]]) + 2 * int(key[col[b]])] += m
    return out


def k41_one_pair() -> dict:
    """Kickoff 41's Part B (Amendment A8, R3): W per pair, the mean over the 8 random circuits of the Hellinger
    fidelity (sum over s of sqrt(p_s q_s)) squared, p the ideal distribution from k40-ideal.json and q the measured one;
    the level pick (the 8 highest of Kickoff 40's mean P(A no)) and the x pick (the 8 lowest x read for Part B), both
    on the pairs with a published figure; and the difference in mean W between the three pairs only the level pick
    chose and the two only the x pick chose other than 94-95."""
    rec = load(RIG / "k41-payoff.json")
    pairs = [tuple(p) for p in rec["pairs"]]
    ideal = [np.array(c["ideal"]) for c in load(RIG / "k40-ideal.json")["R"]]
    q = {}
    for c, t in zip(rec["counts"], rec["tasks"]):
        if t["label"].startswith("R"):
            d = outcomes_braket(c, t["measured_qubits"], pairs)
            q[int(t["label"][1:])] = d / d.sum(axis=1, keepdims=True)
    W = np.array(
        [np.mean([np.sum(np.sqrt(ideal[j - 1] * q[j][i])) ** 2 for j in range(1, 9)]) for i in range(len(pairs))]
    )
    k40 = load(RIG / "k40-map.json")
    p40 = [tuple(p) for p in k40["pairs"]]
    P40 = np.array([p11_braket(c, t["measured_qubits"], p40) for c, t in zip(k40["counts"], k40["tasks"])])
    lev40 = dict(zip(p40, level(P40, k40["order"])))
    fig = {tuple(f["pair"]): f for f in load(RIG / "k41-figures.json")["B"]["figures_at_submission"]}
    S = [i for i, p in enumerate(pairs) if fig[p]["cz_fidelity"] != 0.5]
    x = {i: (1 - fig[pairs[i]]["cz_fidelity"]) + sum(1 - f for f in fig[pairs[i]]["readout_fidelity"]) for i in S}
    L = sorted(S, key=lambda i: -lev40[pairs[i]])[:8]
    X = sorted(S, key=lambda i: x[i])[:8]
    only_L = [i for i in L if i not in X]
    only_X = [i for i in X if i not in L and pairs[i] != (94, 95)]
    return {
        "only_level_pick": [list(pairs[i]) for i in only_L],
        "only_x_pick_apart_from_94_95": [list(pairs[i]) for i in only_X],
        "mean_W_difference": float(W[only_L].mean() - W[only_X].mean()),
        "rank_of_94_95_by_x": sorted(S, key=lambda i: x[i]).index(pairs.index((94, 95))) + 1,
        "worst_W_on_S": list(pairs[min(S, key=lambda i: W[i])]),
    }


def outcomes_qiskit_adjacent(counts: dict, n_pairs: int) -> np.ndarray:
    """Per pair, the counts of s = a + 2 b in IBM's adjacent reading (a is bit 2i, b is bit 2i + 1)."""
    out = np.zeros((n_pairs, 4))
    for key, m in counts.items():
        bits = key[::-1]
        for i in range(n_pairs):
            out[i, int(bits[2 * i]) + 2 * int(bits[2 * i + 1])] += m
    return out


def k33_payoff() -> dict:
    """Kickoff 33 on ibm_fez (Amendment A11, item 3), from the raw counts. The prior map is Kickoff 32's dense
    condition (k32-isolation.json, every position with all 27 pairs active): per pair, the mean P(11) of its "off"
    positions minus that of its "no" positions (dividing by the circuit's gap would not change the ranking). Each
    random circuit R1 to R8 ran at two positions; the two are pooled per pair (16,000 shots) before the fidelity, the
    squared Hellinger overlap (sum over s of sqrt(p_s q_s))^2 against circuits[j].ideal in workload/k33-workload.json,
    state order s = q0 + 2 q1, on uncorrected counts. W is a pair's mean over the eight circuits. The map's pick is the
    8 highest prior k; the published pick the 8 lowest x in published_at_submission. The error is 1 - W."""
    iso, pay = load(DATA / "ibm_fez" / "k32-isolation.json"), load(DATA / "ibm_fez" / "k33-payoff.json")
    dense = [tuple(p) for p in iso["selection"]["dense_pairs"]]
    D = {"no": [], "off": []}
    for (cond, v), c in zip(iso["plan"], iso["counts"]):
        if cond == "D":
            D[v].append(p11_qiskit_adjacent(c, len(dense)))
    k_dense = dict(zip(dense, np.mean(D["off"], axis=0) - np.mean(D["no"], axis=0)))
    pairs = [tuple(p) for p in pay["pairs"]]
    pooled: dict = {}
    for label, c in zip(pay["order"], pay["counts"]):
        if label.startswith("R"):
            pooled[label] = pooled.get(label, 0) + outcomes_qiskit_adjacent(c, len(pairs))
    ideal = [np.array(c["ideal"]) for c in load(DATA / "workload" / "k33-workload.json")["circuits"]]
    W = np.mean(
        [[np.sum(np.sqrt(ideal[j] * pooled[f"R{j + 1}"][i] / pooled[f"R{j + 1}"][i].sum())) ** 2 for j in range(8)]
         for i in range(len(pairs))],
        axis=1,
    )  # fmt: skip
    x = {tuple(r["pair"]): r["x"] for r in pay["published_at_submission"]}
    by_map = top8(np.array([k_dense[p] for p in pairs]), pairs)
    by_x = top8(np.array([x[p] for p in pairs]), pairs, highest=False)
    err = {
        name: float(np.mean([1 - W[pairs.index(tuple(p))] for p in pick]))
        for name, pick in (("map", by_map), ("x", by_x))
    }
    return {
        "pick_by_map": by_map,
        "pick_by_published": by_x,
        "shots_per_circuit_pooled": sorted({int(v.sum(axis=1)[0]) for v in pooled.values()}),
        "error_map_pick": err["map"],
        "error_published_pick": err["x"],
        "less_error_percent": 100 * (1 - err["map"] / err["x"]),
    }


def literals() -> dict:
    return {
        "main.json": openquantum_main(),
        "k40-map.json": braket_map("k40-map.json", "k40-figures.json", "stage2"),
        "k41-map.json": braket_map("k41-map.json", "k41-figures.json", "A"),
        "k41-payoff.json": k41_one_pair(),
        "k33-payoff.json": k33_payoff(),
    }


if __name__ == "__main__":
    for name, values in literals().items():
        print(name)
        for k, v in values.items():
            print(f"  {k}: {round(v, 6) if isinstance(v, float) else v}")
