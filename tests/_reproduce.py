# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""The acceptance bar: recompute archived statistics from the archived counts and compare them, field by field.

What is compared is listed in tests/expected_fields.json, not inferred: for each case, every archived field it
recomputes, by its path in the data file, with the path of the recomputed value where the two differ (a rename). What
is not compared is listed, with a reason each, in tests/excluded_fields.json. tests/test_field_inventory.py checks
that every field of every data file is in exactly one of the two.

The comparison is strict (Amendment A4, R3). A listed field fails when it is missing on either side; when its type
differs (a number against None, a string or a list; a list of another length; a dictionary with other keys); when a
recomputed number is not finite; or when the difference exceeds the tolerance, 10⁻⁶ for every field.

Each case returns its headline rows (name, archived, reproduced) and the comparison of every listed field, as
(absolute difference, path); a failure of any other kind is reported as an infinite difference with the reason in the
path. Used by tests/test_reproduction.py and tools/acceptance_table.py.
"""

from __future__ import annotations

import json
import math
from datetime import datetime
from functools import cache
from pathlib import Path

import numpy as np

from manacitra import archive as ar
from manacitra import stats
from manacitra.verdicts import leave_one_out, persistence_analysis

HERE = Path(__file__).resolve().parent
TOL = 1e-6
INF = float("inf")


# --------------------------------------------------------------------------- the inventory
def load_inventory() -> dict:
    inv = json.loads((HERE / "expected_fields.json").read_text())
    if inv["tolerance"] != TOL:
        raise ValueError(f"expected_fields.json states tolerance {inv['tolerance']}, the comparison uses {TOL}")
    for case, groups in inv["cases"].items():
        for g in groups:
            for field, opt in g["fields"].items():
                if set(opt) - {"as"}:
                    raise ValueError(f"{case}: {g['file']}: {field}: unknown option {sorted(set(opt) - {'as'})}")
    return inv


def load_exclusions() -> dict:
    return json.loads((HERE / "excluded_fields.json").read_text())


def split(path: str) -> list:
    return [int(p[1:-1]) if p.startswith("[") else p for p in path.split("/") if p]


def get(tree, path: str):
    """The value at a path ('archived/analysis/S1/r_split_A/pearson', '[3]' for a list index). KeyError if absent."""
    for part in split(path):
        try:
            tree = tree[part]
        except (KeyError, IndexError, TypeError):
            raise KeyError(path) from None
    return tree


def _is_number(v) -> bool:
    return isinstance(v, (int, float, np.integer, np.floating)) and not isinstance(v, (bool, np.bool_))


def _is_list(v) -> bool:
    return isinstance(v, (list, tuple, np.ndarray))


def _kind(v) -> str:
    if v is None:
        return "None"
    if isinstance(v, (bool, np.bool_)):
        return "bool"
    if _is_number(v):
        return "number"
    if isinstance(v, str):
        return "string"
    if _is_list(v):
        return "list"
    if isinstance(v, dict):
        return "dictionary"
    return type(v).__name__


def leaf_diffs(mine, archived, path="", out=None):
    """Compare a recomputed value with an archived one, strictly, as (absolute difference, path) per leaf.

    Dictionaries must have the same keys and lists the same length; a key on one side only, a type that differs, or a
    recomputed number that is not finite is reported as an infinite difference, with the reason in the path."""
    out = [] if out is None else out
    km, ka = _kind(mine), _kind(archived)
    if km != ka:
        out.append((INF, f"{path} (type: recomputed {km}, archived {ka})"))
    elif km == "dictionary":
        for k in mine:
            if k not in archived:
                out.append((INF, f"{path}.{k} (missing on the archived side)"))
        for k in archived:
            if k not in mine:
                out.append((INF, f"{path}.{k} (missing on the recomputed side)"))
            else:
                leaf_diffs(mine[k], archived[k], f"{path}.{k}", out)
    elif km == "list":
        if len(mine) != len(archived):
            out.append((INF, f"{path} (length {len(mine)} against {len(archived)})"))
        for i, (a, b) in enumerate(zip(mine, archived)):
            leaf_diffs(a, b, f"{path}[{i}]", out)
    elif km == "number":
        if not math.isfinite(float(mine)):
            out.append((INF, f"{path} (recomputed value {float(mine)} is not finite)"))
        elif not math.isfinite(float(archived)):
            out.append((INF, f"{path} (archived value {float(archived)} is not finite)"))
        else:
            out.append((abs(float(mine) - float(archived)), path))
    elif km in ("bool", "string"):
        out.append(
            (0.0 if mine == archived else INF, path if mine == archived else f"{path} ({mine!r} against {archived!r})")
        )
    elif km == "None":
        out.append((0.0, f"{path} (None on both sides)"))
    else:
        out.append((INF, f"{path} (cannot compare {km})"))
    return out


def compare(case: str, recomputed: dict, docs: dict) -> list:
    """Every field the inventory lists for this case: the archived value (from docs, the data files as loaded) against
    the recomputed one (from recomputed, keyed by file in the same way), strictly."""
    leaves = []
    for g in load_inventory()["cases"][case]:
        f = g["file"]
        for field, opt in g["fields"].items():
            where = f"{f}: {field}"
            try:
                a = get(docs[f], field)
            except KeyError:
                leaves.append((INF, f"{where} (missing in the archived file)"))
                continue
            try:
                m = get(recomputed[f], opt.get("as", field))
            except KeyError:
                leaves.append((INF, f"{where} (missing on the recomputed side, as {opt.get('as', field)})"))
                continue
            leaves += leaf_diffs(m, a, where)
    return leaves


def _is_array(v) -> bool:
    return _is_list(v) and all(_is_number(x) or x is None or (_is_list(x) and _is_array(x)) for x in v)


def data_fields(doc, path=()):
    """Every field of a data file, as a path: a scalar, or a list of numbers (or of lists of numbers) taken whole.
    Dictionaries and other lists are descended into."""
    if isinstance(doc, dict):
        for k, v in doc.items():
            yield from data_fields(v, (*path, str(k)))
    elif _is_list(doc) and not _is_array(doc):
        for i, v in enumerate(doc):
            yield from data_fields(v, (*path, f"[{i}]"))
    else:
        yield "/".join(path)


def _rows(build) -> list:
    """The headline rows. If an archived field they show is missing or of another type, one row says so; the field
    comparison names the field."""
    try:
        return build()
    except (KeyError, IndexError, TypeError):
        return [("headline rows", "an archived field they show is missing or of another type", "see the comparison")]


def _pearson(d):
    return d["pearson"]


def _hours(t0: str, t1: str) -> float:
    def t(s):
        return datetime.fromisoformat(s.replace("Z", "+00:00"))

    return (t(t1) - t(t0)).total_seconds() / 3600


# --------------------------------------------------------------------------- the cases
def clear_caches() -> None:
    """Forget every recomputed case, so the next call loads the data again (the mutation tests use it)."""
    for fn in (k31, k31_baseline, k32, k31_map, k33, k36, k36_persistence, k34b, k34b_after_the_fact):
        fn.cache_clear()


@cache
def k31(processor):
    f = ar.fez_or_kingston(processor)
    m, s = f["k31-map"], f["k29-settle"]
    prev = ar.previous_k_for(m, s)
    an = ar.map_from_record(m, prev_k=prev)
    an["S4"].update(
        {
            "hours_since_previous_run": _hours(s["timestamps"]["running"], m["timestamps"]["running"]),
            "previous_run_utc": s["timestamps"]["running"],
        }
    )
    P = ar.p11_table(m)
    loo = leave_one_out(
        P,
        m["order"],
        x=m["published_at_submission"] and [r["x"] for r in m["published_at_submission"]],
        seed=m["meta"].get("permutation_seed", 31),
        prev_k=prev,
        shots=m["meta"]["shots_per_circuit"],
    )
    robustness = {
        "dropped_pair": m["pairs"][loo["dropped_index"]],
        "r_split_A": loo["S1"]["r_split_A"],
        "r_AB": loo["S2"]["r_AB"],
        "p_AB": loo["S2"]["p_one_sided"],
        "r_Ax": loo["S3"]["r_Ax"],
        "r_AB_given_x": loo["S3"]["r_AB_given_x"],
        "S4": loo["S4"]["r_vs_previous"],
        "verdict_rule_applied": loo["verdict"]["verdict"],
    }
    file = f"{processor}/k31-map.json"
    leaves = compare(
        f"Kickoff 31, {processor}",
        {file: {"archived": {"analysis": an, "robustness": robustness}, "per_circuit_P11": P.tolist()}},
        {file: m},
    )
    arch = m["archived"]["analysis"]
    rows = _rows(
        lambda: [
            ("verdict", arch["verdict"], an["verdict"]["verdict"]),
            ("r_split(k_A)", _pearson(arch["S1"]["r_split_A"]), _pearson(an["S1"]["r_split_A"])),
            ("r_AB", _pearson(arch["S2"]["r_AB"]), _pearson(an["S2"]["r_AB"])),
            ("p(r_AB), one-sided", arch["S2"]["p_one_sided"], an["S2"]["p_one_sided"]),
            ("r_Ax", _pearson(arch["S3"]["r_Ax"]), _pearson(an["S3"]["r_Ax"])),
            ("r_AB.x", arch["S3"]["r_AB_given_x"], an["S3"]["r_AB_given_x"]),
            ("mean k_A", arch["mean_kA"], an["mean_kA"]),
            (
                "S4: r against the settling run",
                _pearson(arch["S4"]["r_vs_5_october"]),
                _pearson(an["S4"]["r_vs_previous"]),
            ),
        ]
    )
    return rows, leaves


@cache
def k31_baseline(processor):
    """Kickoff 29's settling run (its own analysis, recomputed from its P(11) table) and Kickoff 31's step 0."""
    s = ar.fez_or_kingston(processor)["k29-settle"]
    b = ar.settle_baseline(s)
    settle = ar.settle_analysis(s)
    file = f"{processor}/k29-settle.json"
    leaves = compare(
        f"Kickoff 29 settling run and Kickoff 31 step 0, {processor}",
        {file: {"archived": {**settle, "k31_baseline": b}}},
        {file: s},
    )
    arch, a = s["archived"]["k31_baseline"], s["archived"]["analysis"]
    rows = _rows(
        lambda: [
            ("settling verdict", a["verdict"], settle["analysis"]["verdict"]),
            ("settling mean d", a["mean_d"], settle["analysis"]["mean_d"]),
            ("settling z", a["z"], settle["analysis"]["z"]),
            ("baseline r_split", _pearson(arch["r_split"]), _pearson(b["r_split"])),
            ("baseline r(k, x)", _pearson(arch["r_k_x"]), _pearson(b["r_k_x"])),
        ]
    )
    return rows, leaves


@cache
def k32(processor):
    f = ar.fez_or_kingston(processor)
    m, i = f["k31-map"], f["k32-isolation"]
    iso = ar.isolation_analysis(i, m["pairs"], m["archived"]["analysis"]["kA"])
    an31 = k31_map(processor)
    k31_of = {tuple(p): (an31["kA"][j], an31["kB"][j]) for j, p in enumerate(m["pairs"])}
    selection = {
        side: [
            {"kA_31": k31_of[tuple(r["pair"])][0], "kB_31": k31_of[tuple(r["pair"])][1]} for r in i["selection"][side]
        ]
        for side in ("worst6", "best6")
    }
    recomputed = {"archived": {"analysis": dict(iso)}, "selection": selection, "per_circuit_P11": ar.isolation_p11(i)}
    rows16 = [r for r in iso["rows"] if tuple(r["pair"]) == (16, 23)]
    if rows16:  # ibm_kingston archived the worst pair of its map on its own line
        r = rows16[0]
        recomputed["archived"]["analysis"]["pair_16_23"] = {
            "kD": r["kD"],
            "kA31": k31_of[(16, 23)][0],
            "kS": r["kS"],
            "delta": r["delta"],
            "se_delta": r["se_delta"],
        }
    file = f"{processor}/k32-isolation.json"
    leaves = compare(f"Kickoff 32, {processor}", {file: recomputed}, {file: i})
    arch = i["archived"]["analysis"]
    rows = _rows(
        lambda: [
            ("verdict", arch["verdict"], iso["verdict"]),
            ("Gap_D", arch["gap_D"], iso["gap_D"]),
            ("Gap_S", arch["gap_S"], iso["gap_S"]),
            ("F", arch["F"], iso["F"]),
        ]
    )
    return rows, leaves, iso


@cache
def k31_map(processor):
    f = ar.fez_or_kingston(processor)
    m, s = f["k31-map"], f["k29-settle"]
    return ar.map_from_record(m, prev_k=ar.previous_k_for(m, s))


@cache
def k33(processor):
    f = ar.fez_or_kingston(processor)
    iso = k32(processor)[2]
    p, i = f["k33-payoff"], f["k32-isolation"]
    pay = ar.payoff_from_record(p, iso["kD_all27"], iso["L_D_all27"], ar.workload_ideal(), shots_interval=True)
    pay["kickoff32_job"] = i["meta"]["job_id"]
    pay["hours_since_kickoff32_job"] = _hours(i["timestamps"]["running"], p["timestamps"]["running"])
    file = f"{processor}/k33-payoff.json"
    leaves = compare(f"Kickoff 33, {processor}", {file: {"archived": {"analysis": pay}}}, {file: p})
    arch = p["archived"]["analysis"]
    c, ca = pay["correlations"]["W"], arch["correlations"]["W"]
    rows = _rows(
        lambda: [
            ("verdict", arch["verdict"], pay["verdict"]["verdict"]),
            ("G (top 8 by map minus top 8 by x)", arch["gains"]["k_prior"]["G"], pay["gains"]["k_prior"]["G"]),
            ("G 90% interval, low", arch["gains"]["k_prior"]["ci90"][0], pay["gains"]["k_prior"]["ci90"][0]),
            ("G 90% interval, high", arch["gains"]["k_prior"]["ci90"][1], pay["gains"]["k_prior"]["ci90"][1]),
            ("r(W, k_prior)", _pearson(ca["k_prior"]), _pearson(c["k_prior"])),
            ("partial r(W, k_prior | x)", ca["partial_k_prior_given_x"], c["partial_k_prior_given_x"]),
            ("p(partial), one-sided", ca["p_partial_one_sided"], c["p_partial_one_sided"]),
            ("mean W", arch["mean_W"], pay["mean_W"]),
        ]
    )
    return rows, leaves, pay


@cache
def k36(arm):
    file = f"simulated/k36-arm{arm}.json"
    r = ar.load(file)
    an = ar.map_from_record(r)
    recomputed = {"archived": {"analysis": an}, "per_circuit_P11": ar.p11_table(r).tolist()}
    if "r_kA_delta" in r:  # arm 2: the map against the planted error per pair
        planted = {json.dumps(d["pair"]): d["delta_rad"] for d in ar.load("simulated/k36-planted.json")["deltas"]}
        delta = [planted[json.dumps(p["qubits"])] for p in r["pairs"]]
        recomputed["r_kA_delta"] = stats.corr(an["kA"], delta)
        recomputed["r_kB_delta"] = stats.corr(an["kB"], delta)
    leaves = compare(f"Kickoff 36, arm {arm}", {file: recomputed}, {file: r})
    arch = r["archived"]["analysis"]
    rows = _rows(
        lambda: [
            ("verdict", arch["verdict"], an["verdict"]["verdict"]),
            ("r_split(k_A)", _pearson(arch["S1"]["r_split_A"]), _pearson(an["S1"]["r_split_A"])),
            ("r_AB", _pearson(arch["S2"]["r_AB"]), _pearson(an["S2"]["r_AB"])),
            ("r_Ax", _pearson(arch["S3"]["r_Ax"]), _pearson(an["S3"]["r_Ax"])),
            ("r_AB.x", arch["S3"]["r_AB_given_x"], an["S3"]["r_AB_given_x"]),
        ]
    )
    return rows, leaves


@cache
def k36_persistence(kind):
    file = "simulated/k36-persistence.json"
    doc = ar.load(file)
    p = doc[kind]
    a = persistence_analysis(p["days"])
    leaves = compare(f"Kickoff 36, persistence, {kind} days", {file: {kind: {"analysis": a}}}, {file: doc})
    arch = p["analysis"]
    rows = _rows(
        lambda: [
            ("verdict, original rule", arch["verdict"], a["original_rule"]["verdict"]),
            ("corrected r(k2, k3)", arch["across"]["corrected"]["23"], a["across"]["corrected"]["23"]),
        ]
    )
    return rows, leaves, a


@cache
def k34b():
    main, screen = f"{ar.RIGETTI}/main.json", f"{ar.RIGETTI}/screen.json"
    m, s = ar.load(main), ar.load(screen)
    r = ar.rigetti_map(m, s)
    an, arch = r["analysis"], m["archived"]
    d = r["descriptive"]
    Ls = {tuple(c["pair"]): c["L_s"] for c in s["pair_rule"]["candidates"]}
    shared = arch["descriptive"]["across_runs"]
    recomputed_main = {
        "per_circuit_P11": r["P"].tolist(),
        "bit_order_check": r["bit_order_check"],
        "archived": {
            "analysis": an,
            "dead_pair_filter": {
                **an["dead_pair_filter"],
                "excluded_pairs": [
                    {"pair": list(r["pairs"][j]), "mean_P11_A_no": an["dead_pair_filter"]["mean_P_A_no"][j]}
                    for j in an["dead_pair_filter"]["excluded"]
                ],
                "working_pairs": [list(p) for p in r["working_pairs"]],
            },
            "robustness": {
                "dropped_pair": list(r["leave_one_out"]["dropped_pair"]),
                "r_split_A": r["leave_one_out"]["S1"]["r_split_A"],
                "r_AB": r["leave_one_out"]["S2"]["r_AB"],
                "p_AB": r["leave_one_out"]["S2"]["p_one_sided"],
                "verdict_rule_applied": r["leave_one_out"]["verdict"]["verdict"],
            },
            "descriptive": {
                "r_Ls_vs_Lmain": {"r": d["r_Ls_vs_Lmain"]},
                "r_kA_vs_Ls": {"r": d["r_kA_vs_Ls"]},
                "r_Lwave1_vs_Lwave2": {"L_wave1": d["L_wave1"], "L_wave2": d["L_wave2"], "r": d["r_Lwave1_vs_Lwave2"]},
                "across_runs": {
                    "test_vs_screen_27_test_pairs": {
                        "test_low_pairs_still_below_0_5": {
                            key: Ls[tuple(int(q) for q in key.split("-"))] < 0.5
                            for key in shared["test_vs_screen_27_test_pairs"]["test_low_pairs_still_below_0_5"]
                        }
                    },
                    "shared_pairs_in_all_three_runs": {
                        "screen_18_54": [Ls[tuple(p)] for p in shared["shared_pairs_in_all_three_runs"]["pairs"]],
                        "main_22_14_to_22_29": d["main_shared"],
                        "r_test_main": d["r_test_main"],
                        "r_screen_main": d["r_screen_main"],
                        "r_test_screen": d["r_test_screen"],
                    },
                    "screen_vs_main_all_27_chosen": {"r": d["r_screen_main_all_27_chosen"]},
                },
            },
        },
    }
    leaves = compare(
        "Kickoff 34b, Rigetti Cepheus-1-108Q",
        {main: recomputed_main, screen: {"pair_rule": ar.screen_pair_rule(s)}},
        {main: m, screen: s},
    )
    a = arch["analysis"]
    ra, da = arch["robustness"], arch["descriptive"]
    loo = r["leave_one_out"]
    rows = _rows(
        lambda: [
            ("verdict", a["verdict"], an["verdict"]["verdict"]),
            ("working pairs", float(len(a["kA"])), float(len(r["working_pairs"]))),
            ("r_split(k_A)", _pearson(a["S1"]["r_split_A"]), _pearson(an["S1"]["r_split_A"])),
            ("r_AB", _pearson(a["S2"]["r_AB"]), _pearson(an["S2"]["r_AB"])),
            ("p(r_AB), one-sided", a["S2"]["p_one_sided"], an["S2"]["p_one_sided"]),
            ("mean k_A", a["mean_kA"], an["mean_kA"]),
            ("leave-one-out (without 101-102): verdict", ra["verdict_rule_applied"], loo["verdict"]["verdict"]),
            ("leave-one-out: r_split(k_A)", _pearson(ra["r_split_A"]), _pearson(loo["S1"]["r_split_A"])),
            ("leave-one-out: r_AB", _pearson(ra["r_AB"]), _pearson(loo["S2"]["r_AB"])),
            ("r(L_s, L_main)", _pearson(da["r_Ls_vs_Lmain"]["r"]), _pearson(d["r_Ls_vs_Lmain"])),
            ("r(L_wave1, L_wave2)", _pearson(da["r_Lwave1_vs_Lwave2"]["r"]), _pearson(d["r_Lwave1_vs_Lwave2"])),
        ]
    )
    return rows, leaves, r


@cache
def k34b_after_the_fact():
    """Computed after seeing the data, outside the verdict: the rule without 13-14 and 101-102."""
    file = f"{ar.RIGETTI}/after-the-fact.json"
    doc = ar.load(file)
    arch = doc["without_13-14_and_101-102"]
    a = k34b()[2]["after_the_fact_20"]
    mine = {
        "n": a["n_pairs"],
        "r_split_A": a["S1"]["r_split_A"],
        "r_split_B": a["S1"]["r_split_B"],
        "r_AB": a["S2"]["r_AB"],
        "p_AB": a["S2"]["p_one_sided"],
        "mean_kA": a["mean_kA"],
        "mean_kB": a["mean_kB"],
        "sd_kA": a["sd_kA_between_pairs"],
        "verdict_rule_applied": a["verdict"]["verdict"],
    }
    leaves = compare("Kickoff 34b, after the fact: 20 pairs", {file: {"without_13-14_and_101-102": mine}}, {file: doc})
    rows = _rows(
        lambda: [
            ("verdict, rule applied", arch["verdict_rule_applied"], a["verdict"]["verdict"]),
            ("r_split(k_A)", _pearson(arch["r_split_A"]), _pearson(a["S1"]["r_split_A"])),
            ("r_AB", _pearson(arch["r_AB"]), _pearson(a["S2"]["r_AB"])),
            ("p(r_AB), one-sided", arch["p_AB"], a["S2"]["p_one_sided"]),
        ]
    )
    return rows, leaves


CASES = {
    "Kickoff 31, ibm_fez": lambda: k31("ibm_fez"),
    "Kickoff 31, ibm_kingston": lambda: k31("ibm_kingston"),
    "Kickoff 29 settling run and Kickoff 31 step 0, ibm_fez": lambda: k31_baseline("ibm_fez"),
    "Kickoff 29 settling run and Kickoff 31 step 0, ibm_kingston": lambda: k31_baseline("ibm_kingston"),
    "Kickoff 32, ibm_fez": lambda: k32("ibm_fez")[:2],
    "Kickoff 32, ibm_kingston": lambda: k32("ibm_kingston")[:2],
    "Kickoff 33, ibm_fez": lambda: k33("ibm_fez")[:2],
    "Kickoff 33, ibm_kingston": lambda: k33("ibm_kingston")[:2],
    "Kickoff 36, arm 1": lambda: k36(1),
    "Kickoff 36, arm 2": lambda: k36(2),
    "Kickoff 36, arm 3": lambda: k36(3),
    "Kickoff 36, persistence, static days": lambda: k36_persistence("static")[:2],
    "Kickoff 36, persistence, scrambled days": lambda: k36_persistence("scrambled")[:2],
    "Kickoff 34b, Rigetti Cepheus-1-108Q": lambda: k34b()[:2],
    "Kickoff 34b, after the fact: 20 pairs": k34b_after_the_fact,
}

#: The acceptance bar as the kickoff states it (the other cases are reproduced too)
REQUIRED = {
    "Kickoff 31, ibm_fez": "DIAGNOSTIC",
    "Kickoff 31, ibm_kingston": "DIAGNOSTIC",
    "Kickoff 33, ibm_fez": "USEFUL",
    "Kickoff 33, ibm_kingston": "NOT SETTLED",
    "Kickoff 36, arm 1": "NOISE",
    "Kickoff 36, arm 2": "DIAGNOSTIC",
    "Kickoff 34b, Rigetti Cepheus-1-108Q": "MAP PRESENT",
}
