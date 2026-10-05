# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""The acceptance bar: recompute every archived statistic from the archived counts and compare.

Each case returns its headline rows (name, archived, reproduced) and the list of every numeric leaf compared, as
(absolute difference, path). Used by tests/test_reproduction.py and tools/acceptance_table.py.
"""

from __future__ import annotations

from functools import cache

from manacitra import archive as ar
from manacitra.verdicts import persistence_analysis

TOL = 1e-6


def leaf_diffs(mine, archived, path="", out=None):
    """Absolute differences of every numeric leaf present in both structures (lists must match in length)."""
    out = [] if out is None else out
    if isinstance(mine, dict) and isinstance(archived, dict):
        for k in mine:
            if k in archived:
                leaf_diffs(mine[k], archived[k], f"{path}.{k}", out)
    elif isinstance(mine, (list, tuple)) and isinstance(archived, (list, tuple)):
        if len(mine) != len(archived):
            out.append((float("inf"), f"{path} (length {len(mine)} against {len(archived)})"))
        for i, (a, b) in enumerate(zip(mine, archived)):
            leaf_diffs(a, b, f"{path}[{i}]", out)
    elif isinstance(mine, bool) or isinstance(archived, bool):
        if mine != archived:
            out.append((float("inf"), f"{path} ({mine} against {archived})"))
    elif isinstance(mine, (int, float)) and isinstance(archived, (int, float)):
        out.append((abs(float(mine) - float(archived)), path))
    elif mine is None and archived is None:
        pass
    elif isinstance(mine, str) and isinstance(archived, str) and mine != archived:
        out.append((float("inf"), f"{path} ({mine!r} against {archived!r})"))
    return out


def _pearson(d):
    return d["pearson"]


@cache
def k31(processor):
    f = ar.fez_or_kingston(processor)
    m, s = f["k31-map"], f["k29-settle"]
    an = ar.map_from_record(m, prev_k=ar.previous_k_for(m, s))
    arch = dict(m["archived"]["analysis"])
    arch["S4"] = {"r_vs_previous": arch["S4"]["r_vs_5_october"], "p_one_sided": arch["S4"]["p_one_sided"]}
    mine = {k: v for k, v in an.items() if k != "verdict"}
    leaves = leaf_diffs(mine, arch)
    rows = [
        ("verdict", arch["verdict"], an["verdict"]["verdict"]),
        ("r_split(k_A)", _pearson(arch["S1"]["r_split_A"]), _pearson(an["S1"]["r_split_A"])),
        ("r_AB", _pearson(arch["S2"]["r_AB"]), _pearson(an["S2"]["r_AB"])),
        ("p(r_AB), one-sided", arch["S2"]["p_one_sided"], an["S2"]["p_one_sided"]),
        ("r_Ax", _pearson(arch["S3"]["r_Ax"]), _pearson(an["S3"]["r_Ax"])),
        ("r_AB.x", arch["S3"]["r_AB_given_x"], an["S3"]["r_AB_given_x"]),
        ("mean k_A", arch["mean_kA"], an["mean_kA"]),
        ("S4: r against the settling run", _pearson(arch["S4"]["r_vs_previous"]), _pearson(an["S4"]["r_vs_previous"])),
    ]
    return rows, leaves


@cache
def k31_baseline(processor):
    s = ar.fez_or_kingston(processor)["k29-settle"]
    b = ar.settle_baseline(s)
    arch = s["archived"]["k31_baseline"]
    rows = [
        ("baseline r_split", _pearson(arch["r_split"]), _pearson(b["r_split"])),
        ("baseline r(k, x)", _pearson(arch["r_k_x"]), _pearson(b["r_k_x"])),
    ]
    return rows, leaf_diffs(b, arch)


@cache
def k32(processor):
    f = ar.fez_or_kingston(processor)
    m, i = f["k31-map"], f["k32-isolation"]
    iso = ar.isolation_analysis(i, m["pairs"], m["archived"]["analysis"]["kA"])
    arch = i["archived"]["analysis"]
    rows = [
        ("verdict", arch["verdict"], iso["verdict"]),
        ("Gap_D", arch["gap_D"], iso["gap_D"]),
        ("Gap_S", arch["gap_S"], iso["gap_S"]),
        ("F", arch["F"], iso["F"]),
    ]
    return rows, leaf_diffs(iso, arch), iso


@cache
def k33(processor):
    f = ar.fez_or_kingston(processor)
    iso = k32(processor)[2]
    p = f["k33-payoff"]
    pay = ar.payoff_from_record(p, iso["kD_all27"], iso["L_D_all27"], ar.workload_ideal())
    arch = p["archived"]["analysis"]
    mine = {k: v for k, v in pay.items() if k != "verdict"}
    leaves = leaf_diffs(mine, arch)
    leaves += leaf_diffs({"k_prior": iso["kD_all27"], "L_prior": iso["L_D_all27"]}, arch["predictors"], ".predictors")
    c, ca = pay["correlations"]["W"], arch["correlations"]["W"]
    rows = [
        ("verdict", arch["verdict"], pay["verdict"]["verdict"]),
        ("G (top 8 by map minus top 8 by x)", arch["gains"]["k_prior"]["G"], pay["gains"]["k_prior"]["G"]),
        ("G 90% interval, low", arch["gains"]["k_prior"]["ci90"][0], pay["gains"]["k_prior"]["ci90"][0]),
        ("G 90% interval, high", arch["gains"]["k_prior"]["ci90"][1], pay["gains"]["k_prior"]["ci90"][1]),
        ("r(W, k_prior)", _pearson(ca["k_prior"]), _pearson(c["k_prior"])),
        ("partial r(W, k_prior | x)", ca["partial_k_prior_given_x"], c["partial_k_prior_given_x"]),
        ("p(partial), one-sided", ca["p_partial_one_sided"], c["p_partial_one_sided"]),
        ("mean W", arch["mean_W"], pay["mean_W"]),
    ]
    return rows, leaves, pay


@cache
def k36(arm):
    r = ar.load(f"simulated/k36-arm{arm}.json")
    an = ar.map_from_record(r)
    arch = r["archived"]["analysis"]
    rows = [
        ("verdict", arch["verdict"], an["verdict"]["verdict"]),
        ("r_split(k_A)", _pearson(arch["S1"]["r_split_A"]), _pearson(an["S1"]["r_split_A"])),
        ("r_AB", _pearson(arch["S2"]["r_AB"]), _pearson(an["S2"]["r_AB"])),
        ("r_Ax", _pearson(arch["S3"]["r_Ax"]), _pearson(an["S3"]["r_Ax"])),
        ("r_AB.x", arch["S3"]["r_AB_given_x"], an["S3"]["r_AB_given_x"]),
    ]
    return rows, leaf_diffs({k: v for k, v in an.items() if k != "verdict"}, arch)


@cache
def k36_persistence(kind):
    p = ar.load("simulated/k36-persistence.json")[kind]
    a = persistence_analysis(p["days"])
    arch = p["analysis"]
    mine = {"per_day": {d: {**v, "rel": v["reliability"]} for d, v in a["per_day"].items()}, "across": a["across"]}
    rows = [
        ("verdict, original rule", arch["verdict"], a["original_rule"]["verdict"]),
        ("corrected r(k2, k3)", arch["across"]["corrected"]["23"], a["across"]["corrected"]["23"]),
    ]
    return rows, leaf_diffs(mine, arch), a


CASES = {
    "Kickoff 31, ibm_fez": lambda: k31("ibm_fez"),
    "Kickoff 31, ibm_kingston": lambda: k31("ibm_kingston"),
    "Kickoff 31 step 0, ibm_fez settling run": lambda: k31_baseline("ibm_fez"),
    "Kickoff 31 step 0, ibm_kingston settling run": lambda: k31_baseline("ibm_kingston"),
    "Kickoff 32, ibm_fez": lambda: k32("ibm_fez")[:2],
    "Kickoff 32, ibm_kingston": lambda: k32("ibm_kingston")[:2],
    "Kickoff 33, ibm_fez": lambda: k33("ibm_fez")[:2],
    "Kickoff 33, ibm_kingston": lambda: k33("ibm_kingston")[:2],
    "Kickoff 36, arm 1": lambda: k36(1),
    "Kickoff 36, arm 2": lambda: k36(2),
    "Kickoff 36, arm 3": lambda: k36(3),
    "Kickoff 36, persistence, static days": lambda: k36_persistence("static")[:2],
    "Kickoff 36, persistence, scrambled days": lambda: k36_persistence("scrambled")[:2],
}

#: The acceptance bar as the kickoff states it (the other cases are reproduced too)
REQUIRED = {
    "Kickoff 31, ibm_fez": "DIAGNOSTIC",
    "Kickoff 31, ibm_kingston": "DIAGNOSTIC",
    "Kickoff 33, ibm_fez": "USEFUL",
    "Kickoff 33, ibm_kingston": "NOT SETTLED",
    "Kickoff 36, arm 1": "NOISE",
    "Kickoff 36, arm 2": "DIAGNOSTIC",
}
