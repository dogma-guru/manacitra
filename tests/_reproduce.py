# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""The acceptance bar: recompute archived statistics from the archived counts and compare them, field by field.

What is compared is listed in tests/expected_fields.json, not inferred: for each case, every archived field it
recomputes, by its path in the data file, with the path of the recomputed value where the two differ (a rename). What
is not compared is listed, with a reason each, in tests/excluded_fields.json. tests/test_field_inventory.py checks
that every field of every data file is in exactly one of the two.

The comparison is strict (Amendment A4, R3). A listed field fails when it is missing on either side; when its type
differs (a number against None, a string or a list; a list of another length; a dictionary with other keys); when a
recomputed number is not finite; or when the difference exceeds the tolerance, 10⁻⁶ for every field but the seeded
resampling fields below (RESAMPLED), by the author's ruling of 7 October 2026 (Amendment A7).

Each case returns its headline rows (name, archived, reproduced) and the comparison of every listed field, as
(absolute difference, path); a failure of any other kind is reported as an infinite difference with the reason in the
path. Used by tests/test_reproduction.py and tools/acceptance_table.py.
"""

from __future__ import annotations

import json
import math
import re
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

#: The seeded resampling fields, whose draws come from numpy's random generators (Amendment A7, the author's ruling of
#: 7 October 2026). numpy does not keep a generator's stream the same across versions, and a multinomial draw can turn
#: on the last bit of a probability, which differs between platforms. So:
#: * the intervals that also resample shots (multinomial draws, 2,000 per interval) are compared at 10⁻³; the largest
#:   difference seen between platforms is 3.2·10⁻⁴, below a 2,000-draw percentile's own Monte Carlo error;
#: * the bootstrap SDs of Kickoff 42's fits (binomial draws) match on every platform with numpy 2.5, the runs' version,
#:   and are compared at 10⁻⁶ there; with an older numpy they are reported as not compared, by name.
#: Every other field is compared at 10⁻⁶, everywhere.
RESAMPLED_SHOTS = re.compile(r"ci90_circuits_and_shots_not_in_verdict")
RESAMPLED_SHOTS_TOL = 1e-3
RESAMPLED_BOOT = re.compile(r"(^|[/.])boot_sd|median_boot_sd_deltaA")
RESAMPLED_BOOT_NUMPY = (2, 5)


def _numpy_at_least(version) -> bool:
    return tuple(int(x) for x in np.__version__.split(".")[:2]) >= version


def resampling_rule(diff: float, path: str, numpy_ok: bool | None = None) -> tuple[float, str]:
    """A compared leaf under the rule for seeded resampling fields: a shots-resampled interval within 10⁻³ counts as
    agreeing (difference 0, the measured difference named in the path); a bootstrap SD under a numpy older than 2.5 is
    not compared (difference 0, the reason in the path). A difference that is infinite (a missing field, a type change,
    a value that is not finite) is never relaxed."""
    if diff == INF:
        return diff, path
    if RESAMPLED_SHOTS.search(path) and diff <= RESAMPLED_SHOTS_TOL:
        return 0.0, f"{path} (seeded resampling: compared at 1e-3, difference {diff:.3g})"
    ok = _numpy_at_least(RESAMPLED_BOOT_NUMPY) if numpy_ok is None else numpy_ok
    if RESAMPLED_BOOT.search(path) and not ok:
        return 0.0, f"{path} (seeded bootstrap: not compared under numpy {np.__version__}; compared under 2.5 or later)"
    return diff, path


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
            leaves += [resampling_rule(d, p) for d, p in leaf_diffs(m, a, where)]
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
    for fn in (
        k31,
        k31_baseline,
        k32,
        k31_map,
        k33,
        k36,
        k36_persistence,
        k34b,
        k34b_after_the_fact,
        k37_recomputed,
        k37,
        k37_after_the_fact,
        k35_recomputed,
        k35,
        k38,
        k40_stage1,
        k40_stage2,
        k40_stage3,
        k40_placement,
        k40_map,
        k40_after_the_fact,
        k40_payoff,
        k40_inputs,
        k41_today,
        k41_map,
        k41_payoff,
        k41_inputs,
        k41_partB,
        k42_scan,
        k42_day1,
        k42_day2,
        k42_after_the_fact,
        k42_inputs,
    ):
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


@cache
def k37_recomputed():
    R = ar.RIGETTI
    return ar.placement_or_drift(
        ar.load(f"{R}/k37-placement.json"), ar.load(f"{R}/main.json"), ar.load(f"{R}/screen.json")
    )


@cache
def k37():
    """Kickoff 37: the measures, the verdict, the gap, the run order and the descriptive lines, from the counts."""
    file = f"{ar.RIGETTI}/k37-placement.json"
    doc = ar.load(file)
    r = k37_recomputed()
    recomputed = {
        "per_task_P11": r["per_task_P11"],
        "archived": {k: r[k] for k in ("measures", "verdict", "gap", "completion_order", "descriptive")},
    }
    leaves = compare("Kickoff 37, Rigetti Cepheus-1-108Q", {file: recomputed}, {file: doc})
    a, m = doc["archived"], r["measures"]
    rows = _rows(
        lambda: [
            ("verdict", a["verdict"]["on_pearson"], r["verdict"]["on_pearson"]),
            *(
                (name, _pearson(a["measures"][name]), _pearson(m[name]))
                for name in ("c_1", "c_2", "d_1", "d_2", "t27", "t53")
            ),
            ("gap, minutes", a["gap"]["minutes"], r["gap"]["minutes"]),
            (
                "wave 1 P27 against 34b's main-job A no",
                _pearson(a["descriptive"]["r_T1w1_vs_34b_main_A_no_mean_of_four"]),
                _pearson(r["descriptive"]["r_T1w1_vs_34b_main_A_no_mean_of_four"]),
            ),
            (
                "wave 1 P53 against 34b's screen",
                _pearson(a["descriptive"]["r_T2w1_vs_34b_screen"]),
                _pearson(r["descriptive"]["r_T2w1_vs_34b_screen"]),
            ),
        ]
    )
    return rows, leaves, r


@cache
def k37_after_the_fact():
    """Computed after seeing the data, outside the verdict."""
    file = f"{ar.RIGETTI}/k37-after-the-fact.json"
    doc = ar.load(file)
    a = k37_recomputed()["after_the_fact"]
    leaves = compare("Kickoff 37, after the fact", {file: a}, {file: doc})
    w, s = doc["without_34b_five_low_pairs"], doc["t53_split"]
    rows = _rows(
        lambda: [
            (
                "without the five: r(T1, T2), wave 1",
                _pearson(w["d_1_pearson_T1_vs_T2"]),
                _pearson(a["without_34b_five_low_pairs"]["d_1_pearson_T1_vs_T2"]),
            ),
            (
                "without the five: r(T1, T2), wave 2",
                _pearson(w["d_2_pearson_T1_vs_T2"]),
                _pearson(a["without_34b_five_low_pairs"]["d_2_pearson_T1_vs_T2"]),
            ),
            ("without the five: t27", _pearson(w["t27"]), _pearson(a["without_34b_five_low_pairs"]["t27"])),
            (
                "t53 on the other 26 pairs",
                _pearson(s["on_the_26_other_pairs"]),
                _pearson(a["t53_split"]["on_the_26_other_pairs"]),
            ),
        ]
    )
    return rows, leaves


# --------------------------------------------------------------------------- Amendment A7
@cache
def k35_recomputed():
    return ar.full_chip_persistence({d: ar.load(f"ibm_fez/k35-day{d}.json") for d in (1, 2, 3)})


@cache
def k35():
    """Kickoff 35: each day's statistics from its counts, the across-day analysis and both verdicts, Amendment A1's
    lines and the descriptive checks."""
    r = k35_recomputed()
    a, lv = r["analysis"], r["levels"]
    docs = {f"ibm_fez/k35-day{d}.json": ar.load(f"ibm_fez/k35-day{d}.json") for d in (1, 2, 3)}
    file = "ibm_fez/k35-persistence.json"
    docs[file] = ar.load(file)
    recomputed = {}
    for d in (1, 2, 3):
        pd, rec = a["per_day"][str(d)], docs[f"ibm_fez/k35-day{d}.json"]
        recomputed[f"ibm_fez/k35-day{d}.json"] = {
            "per_circuit_P11": [p11_from(c, len(rec["rounds"][rn])) for (rn, _), c in zip(rec["order"], rec["counts"])],
            "archived": {
                "analysis": {
                    "edges": [list(e) for e in ar.full_chip_day(rec)["edges"]],
                    "k": pd["k"],
                    "k_first": pd["k_first_copies"],
                    "k_second": pd["k_second_copies"],
                    **lv[d],
                    "mean_k": pd["mean_k"],
                    "sd_k_between_edges": pd["sd_k_between_edges"],
                    "mean_shot_se": pd["shot_noise_sd"],
                    "r_split": pd["r_split"],
                    "reliability_spearman_brown": pd["reliability"],
                    "r_k_x": pd["r_k_x"],
                }
            },
        }
    ac = a["across"]
    pairs = {
        f"{k[0]}-{k[1]}": {
            "r_k": ac["raw"][k]["pearson"],
            "rho_k": ac["raw"][k]["spearman"],
            "corrected_r_k": ac["corrected"][k],
            "r_x": ac["x_raw"][k]["pearson"],
            "rho_x": ac["x_raw"][k]["spearman"],
        }
        for k in ac["raw"]
    }
    v1 = a["verdict"]["inputs"]
    rel = {d: a["per_day"][d]["reliability"] for d in a["per_day"]}

    def a1_pair(key):
        days = v1[f"{key}_pair"]
        p = f"{days[0]}-{days[1]}"
        return {"days": days, **{f: pairs[p][f] for f in ("r_k", "rho_k", "corrected_r_k")}}

    recomputed[file] = {
        "archived": {
            "across": {
                "days_present": [int(d) for d in a["per_day"]],
                "n_common_edges": ac["edges_on_all_days"],
                "pairs": pairs,
                "decile_size": ac["decile_size"],
                "worst_decile_overlap_1_to_3": ac["worst_decile_overlap_13"],
                "best_decile_overlap_1_to_3": ac["best_decile_overlap_13"],
                "verdict": a["original_rule"]["verdict"],
                "map_or_ibm_persists_more": {
                    f"{k[0]}-{k[1]}": {"published score": "IBM's x", "map": "the map"}[v]
                    for k, v in ac["map_or_score_persists_more"].items()
                },
            },
            "amendment_A1": {
                "days_present": [int(d) for d in a["per_day"]],
                "per_day": {
                    d: {
                        "reliability_spearman_brown": rel[d],
                        "passes_floor": rel[d] >= 0.5,
                        "rank_based_reliability_descriptive": r["rank_based_reliability"][int(d)],
                    }
                    for d in rel
                },
                "days_passing": v1["days_passing"],
                "n_common_edges": ac["edges_on_all_days"],
                "decile_size": ac["decile_size"],
                "fades_pair": a1_pair("fades"),
                "holds_pair": a1_pair("holds"),
                "worst_decile_overlap_holds_pair": v1["worst_decile_overlap_holds_pair"],
                "verdict": a["verdict"]["verdict"],
            },
            "robustness": r["robustness"],
        }
    }
    leaves = compare("Kickoff 35, ibm_fez", recomputed, docs)
    arch = docs[file]["archived"]
    fl = r["robustness"]["without_ibm_flagged_edges"]
    rows = _rows(
        lambda: [
            ("verdict", arch["across"]["verdict"], a["original_rule"]["verdict"]),
            ("verdict, Amendment A1", arch["amendment_A1"]["verdict"], a["verdict"]["verdict"]),
            *(
                (
                    f"corrected r(k{p[0]}, k{p[2]})",
                    arch["across"]["pairs"][p]["corrected_r_k"],
                    pairs[p]["corrected_r_k"],
                )
                for p in ("1-2", "2-3", "1-3")
            ),
            (
                "worst-decile overlap, Day 1 to Day 3",
                arch["across"]["worst_decile_overlap_1_to_3"],
                ac["worst_decile_overlap_13"],
            ),
            (
                "best-decile overlap, Day 1 to Day 3",
                arch["across"]["best_decile_overlap_1_to_3"],
                ac["best_decile_overlap_13"],
            ),
            (
                "without the 4 flagged edges: corrected r(k1, k3)",
                arch["robustness"]["without_ibm_flagged_edges"]["pairs"]["1-3"]["corrected_r_k"],
                fl["pairs"]["1-3"]["corrected_r_k"],
            ),
        ]
    )
    return rows, leaves, r


@cache
def k38():
    """Kickoff 38: the levels, the measures, the verdict, the run order, the descriptive lines and the P53i builder's
    checks, from the counts, the task times and the three programs as sent."""
    R = ar.RIGETTI
    file = f"{R}/k38-activity.json"
    doc = ar.load(file)
    r = ar.footprint_or_activity(doc, ar.load(f"{R}/k37-placement.json"), ar.load(f"{R}/main.json"))
    texts = {
        n: ar.resolve(f"{R}/{n}").read_text() for n in ("k37-P27-A-no.qasm", "k37-P53-A-no.qasm", "k38-P53i-A-no.qasm")
    }
    checks = ar.p53i_checks(*texts.values(), doc["programs"]["P27"]["pairs"], doc["programs"]["P53"]["pairs"])
    recomputed = {"per_task_P11": r["per_task_P11"], "p53i_builder": checks, "archived": r}
    leaves = compare("Kickoff 38, Rigetti Cepheus-1-108Q", {file: recomputed}, {file: doc})
    a, m = doc["archived"], r["measures"]
    rows = _rows(
        lambda: [
            ("verdict", a["verdict"]["on_pearson"], r["verdict"]["on_pearson"]),
            ("Spearman reading", a["verdict"]["spearman_reading_beside"], r["verdict"]["spearman_reading_beside"]),
            *((name, _pearson(a["measures"][name]), _pearson(m[name])) for name in "cdfa"),
            ("P53i builder: all five checks", doc["p53i_builder"]["all_five_pass"], checks["all_five_pass"]),
        ]
    )
    return rows, leaves, r


def _compiled(kick: str, stage: str) -> dict:
    d = ar.data_dir() / ar.RIGETTI / "compiled" / kick / stage
    return {p.stem: p.read_text() for p in sorted(d.glob("*.quil"))}


def _rig(name):
    return f"{ar.RIGETTI}/{name}"


@cache
def k40_stage1():
    return ar.braket_placement(
        ar.load(_rig("k40-placement.json")), _compiled("k40", "stage1"), ar.load(_rig("k37-placement.json"))
    )


@cache
def k40_stage2():
    figs = ar.load(_rig("k40-figures.json"))["stage2"]
    return ar.braket_map(
        ar.load(_rig("k40-map.json")), figs, _compiled("k40", "stage2"), ar.load(_rig("main.json")), k40_stage1()
    )


@cache
def k40_stage3():
    figs = ar.load(_rig("k40-figures.json"))["stage3"]
    ideal = ar.load(_rig("k40-ideal.json"))["R"]
    return ar.braket_payoff(
        ar.load(_rig("k40-payoff.json")), figs, k40_stage2()["k_prior_for_stage3"], ideal, _compiled("k40", "stage3")
    )


@cache
def k40_placement():
    """Kickoff 40, stage 1: the levels, c and d, the records check on every compiled program, and the reading."""
    file = _rig("k40-placement.json")
    doc, r = ar.load(file), k40_stage1()
    leaves = compare("Kickoff 40, stage 1, placement", {file: {"archived": r}}, {file: doc})
    a = doc["archived"]
    rows = _rows(
        lambda: [
            ("verdict", a["reading"], r["reading"]),
            ("c = r(X1, X4)", _pearson(a["c"]), _pearson(r["c"])),
            ("d = r(mean X, Y and Y')", _pearson(a["d"]), _pearson(r["d"])),
            ("every record matches its names", a["records_match_names"], r["records_match_names"]),
            (
                "against Kickoff 37's 27-pair program",
                _pearson(a["descriptive_outside_reading"]["r_X_vs_k37_27pair_program"]),
                _pearson(r["descriptive_outside_reading"]["r_X_vs_k37_27pair_program"]),
            ),
            (
                "against Kickoff 37's 53-pair program",
                _pearson(a["descriptive_outside_reading"]["r_X_vs_k37_53pair_program"]),
                _pearson(r["descriptive_outside_reading"]["r_X_vs_k37_53pair_program"]),
            ),
        ]
    )
    return rows, leaves


@cache
def k40_map():
    """Kickoff 40, stage 2: the dead-pair filter, the statistics, the verdict, the sealed leave-one-out, the line
    against Kickoff 34b and the records check, from the counts and the figures at submission."""
    file = _rig("k40-map.json")
    doc, r = ar.load(file), k40_stage2()
    recomputed = {"archived": {"analysis": r, "records": r["records"]}}
    leaves = compare("Kickoff 40, stage 2, the map", {file: recomputed}, {file: doc})
    a = doc["archived"]["analysis"]
    rows = _rows(
        lambda: [
            ("verdict", a["verdict"], r["verdict"]),
            ("working pairs", float(a["n_working"]), float(r["n_working"])),
            ("working pairs with x", float(a["n_working_with_x"]), float(r["n_working_with_x"])),
            *(
                (name, _pearson(f(a["verdict_stats"])), _pearson(f(r["verdict_stats"])))
                for name, f in (
                    ("r_split(k_A)", lambda s: s["S1"]["r_split_A"]),
                    ("r_AB", lambda s: s["S2"]["r_AB"]),
                    ("r_Ax", lambda s: s["S3"]["r_Ax"]),
                )
            ),
            ("r_AB.x", a["verdict_stats"]["S3"]["r_AB_given_x"], r["verdict_stats"]["S3"]["r_AB_given_x"]),
            ("leave-one-out: r_AB", _pearson(a["leave_one_out"]["r_AB"]), _pearson(r["leave_one_out"]["r_AB"])),
            (
                "k_A against Kickoff 34b's, shared working pairs",
                _pearson(a["descriptive"]["r_kA_vs_34b_kA_shared_working"]),
                _pearson(r["descriptive"]["r_kA_vs_34b_kA_shared_working"]),
            ),
        ]
    )
    return rows, leaves


@cache
def k40_after_the_fact():
    """Computed after seeing the data, outside the verdict: stage 2's verdict set without 42-43 and 94-95."""
    file = _rig("k40-after-the-fact.json")
    doc = ar.load(file)
    s = ar.braket_map_without(
        k40_stage2(), ar.load(_rig("k40-map.json")), ar.load(_rig("k40-figures.json"))["stage2"], [[42, 43], [94, 95]]
    )
    mine = {
        "n": s["n_pairs"],
        "r_split_A": s["S1"]["r_split_A"],
        "r_AB": s["S2"]["r_AB"],
        "p_AB": s["S2"]["p_one_sided"],
        "r_Ax": s["S3"]["r_Ax"],
        "r_AB_given_x": s["S3"]["r_AB_given_x"],
        "rule_applied": s["verdict"]["verdict"],
        "mean_kA": s["mean_kA"],
        "sd_kA": s["sd_kA_between_pairs"],
    }
    leaves = compare("Kickoff 40, after the fact", {file: mine}, {file: doc})
    rows = _rows(
        lambda: [
            ("rule applied", doc["rule_applied"], mine["rule_applied"]),
            ("r_AB", _pearson(doc["r_AB"]), _pearson(mine["r_AB"])),
        ]
    )
    return rows, leaves


@cache
def k40_payoff():
    """Kickoff 40, stage 3: W per pair, the correlations, picks and gains on the pairs with x, and the verdict."""
    file = _rig("k40-payoff.json")
    doc, r = ar.load(file), k40_stage3()
    leaves = compare(
        "Kickoff 40, stage 3, the payoff", {file: {"archived": {"analysis": r, "records": r["records"]}}}, {file: doc}
    )
    a = doc["archived"]["analysis"]
    c, ca = r["correlations_on_S"]["W"], a["correlations_on_S"]["W"]
    rows = _rows(
        lambda: [
            ("verdict", a["verdict"], r["verdict"]),
            ("mean W on S", a["mean_W_on_S"], r["mean_W_on_S"]),
            ("r(W, k_prior)", _pearson(ca["k_prior"]), _pearson(c["k_prior"])),
            ("partial r(W, k_prior | x)", ca["partial_k_prior_given_x"], c["partial_k_prior_given_x"]),
            ("r(W, L_prior)", _pearson(ca["L_prior"]), _pearson(c["L_prior"])),
            ("G, k pick against x pick", a["gains"]["k_prior"]["G"], r["gains"]["k_prior"]["G"]),
            (
                "relative error reduction, k pick",
                a["gains"]["k_prior"]["relative_error_reduction"],
                r["gains"]["k_prior"]["relative_error_reduction"],
            ),
            (
                "relative error reduction, L pick",
                a["gains"]["L_prior"]["relative_error_reduction"],
                r["gains"]["L_prior"]["relative_error_reduction"],
            ),
        ]
    )
    return rows, leaves


def _figures_recomputed(figs: dict) -> dict:
    c = ar.braket_figures_check(figs)
    return {
        "figures_at_submission": c["per_pair"],
        "placeholder_count_at_submission": {"in_our_set": c["in_our_set"], "our_pairs_hit": c["our_pairs_hit"]},
    }


def _ideal_recomputed(doc: dict) -> dict:
    """The ideal values from the circuits' exact unitaries, and the random circuits drawn again with seed 33."""
    from manacitra.circuits import ideal_exact
    from manacitra.workload import draw_unitaries, ideal_distributions

    sv = {k: ideal_exact(k) for k in doc["A_B"]}
    U = draw_unitaries(33)
    return {
        "A_B": {k: {"statevector_P11": sv[k], "diff": sv[k] - doc["A_B"][k]["kickoff"]} for k in doc["A_B"]},
        "max_abs_diff_A_B": max(abs(sv[k] - doc["A_B"][k]["kickoff"]) for k in doc["A_B"]),
        "R": [{"ideal": q.tolist()} for q in ideal_distributions(33)],
        "unitaries": [[{"re": u.real.tolist(), "im": u.imag.tolist()} for u in us] for us in U],
    }


@cache
def k40_inputs():
    """Kickoff 40's figures and ideal values, read back: x from Braket's figures by published_score_braket with the
    placeholder rule, at discovery and at each stage's submission; the ideal values from the circuits' unitaries; and
    the random circuits, drawn again (they are Kickoff 33's)."""
    files = {k: _rig(f"k40-{k}.json") for k in ("pairs", "figures", "ideal")}
    docs = {f: ar.load(f) for f in files.values()}
    pairs = docs[files["pairs"]]
    pc = ar.braket_figures_check(pairs["per_pair"])
    recomputed = {
        files["pairs"]: {
            "per_pair": pc["per_pair"],
            "n_with_x": pc["n_with_x"],
            "placeholder_count": {"in_our_set": pc["in_our_set"], "our_pairs_hit": pc["our_pairs_hit"]},
        },
        files["figures"]: {s: _figures_recomputed(docs[files["figures"]][s]) for s in ("stage1", "stage2", "stage3")},
        files["ideal"]: _ideal_recomputed(docs[files["ideal"]]),
    }
    leaves = compare("Kickoff 40, figures and ideal values", recomputed, docs)
    rows = _rows(lambda: [("pairs with x at discovery", float(pairs["n_with_x"]), float(pc["n_with_x"]))])
    return rows, leaves


@cache
def k41_today():
    figs = ar.load(_rig("k41-figures.json"))["A"]
    return ar.braket_map(
        ar.load(_rig("k41-map.json")), figs, _compiled("k41", "partA"), ar.load(_rig("main.json")), k40_stage1()
    )


@cache
def k41_map():
    """Kickoff 41, Part A: today's map by Kickoff 40's analysis, and the persistence measures against Kickoff 40."""
    file = _rig("k41-map.json")
    doc, today = ar.load(file), k41_today()
    f41, f40 = ar.load(_rig("k41-figures.json"))["A"], ar.load(_rig("k40-figures.json"))["stage2"]
    seed = doc["meta"]["permutation_seed"]
    pm = ar.pinned_map_persistence(today, k40_stage2(), f41, f40, doc["pairs"], seed)
    recomputed = {
        "archived": {
            "analysis": {**pm, "today": today},
            "records": today["records"],
            "records_all_match_names": all(r["matches_names"] for r in today["records"].values()),
        }
    }
    leaves = compare("Kickoff 41, Part A, the map a day later", {file: recomputed}, {file: doc})
    a = doc["archived"]["analysis"]
    rows = _rows(
        lambda: [
            ("verdict", a["verdict"], pm["verdict"]),
            ("today's map", a["today"]["verdict"], today["verdict"]),
            ("p_k", _pearson(a["p_k"]["r"]), _pearson(pm["p_k"]["r"])),
            ("p_k'", _pearson(a["p_k_prime"]["r"]), _pearson(pm["p_k_prime"]["r"])),
            ("p_L", _pearson(a["p_L"]), _pearson(pm["p_L"])),
            (
                "today: r_split(k_A)",
                _pearson(a["today"]["verdict_stats"]["S1"]["r_split_A"]),
                _pearson(today["verdict_stats"]["S1"]["r_split_A"]),
            ),
            (
                "today: r_AB",
                _pearson(a["today"]["verdict_stats"]["S2"]["r_AB"]),
                _pearson(today["verdict_stats"]["S2"]["r_AB"]),
            ),
            (
                "today: r_AB on all 24 working pairs",
                _pearson(a["today"]["all_working"]["S2"]["r_AB"]),
                _pearson(today["all_working"]["S2"]["r_AB"]),
            ),
        ]
    )
    return rows, leaves


@cache
def k41_partB():
    figs = ar.load(_rig("k41-figures.json"))["B"]
    ideal = ar.load(_rig("k40-ideal.json"))["R"]
    return ar.day_old_payoff(
        ar.load(_rig("k41-payoff.json")), figs, k40_stage2(), ideal, k41_today(), _compiled("k41", "partB")
    )


@cache
def k41_payoff():
    """Kickoff 41, Part B: W per pair, both day-old scores' lines, and the same-day ceiling beside them."""
    file = _rig("k41-payoff.json")
    doc = ar.load(file)
    r = k41_partB()
    recomputed = {
        "archived": {
            "analysis": r,
            "records": r["records"],
            "records_all_match_names": all(x["matches_names"] for x in r["records"].values()),
        }
    }
    leaves = compare("Kickoff 41, Part B, the payoff with the day-old scores", {file: recomputed}, {file: doc})
    a = doc["archived"]["analysis"]
    rows = _rows(
        lambda: [
            ("verdict", a["level"]["verdict"], r["level"]["verdict"]),
            ("kept share's verdict", a["kept_share"]["verdict"], r["kept_share"]["verdict"]),
            ("mean W", a["mean_W"], r["mean_W"]),
            *(
                (f"{name}: {k}", a[name][k], r[name][k])
                for name in ("level", "kept_share")
                for k in ("partial_r_given_x", "G", "relative_error_reduction")
            ),
            ("level: G interval, low", a["level"]["ci90"][0], r["level"]["ci90"][0]),
            ("level: G interval, high", a["level"]["ci90"][1], r["level"]["ci90"][1]),
            (
                "same day: level, relative error reduction",
                a["same_day"]["level"]["relative_error_reduction"],
                r["same_day"]["level"]["relative_error_reduction"],
            ),
            (
                "same day: kept share, relative error reduction",
                a["same_day"]["kept_share"]["relative_error_reduction"],
                r["same_day"]["kept_share"]["relative_error_reduction"],
            ),
        ]
    )
    return rows, leaves


@cache
def k41_inputs():
    """Kickoff 41's figures, read back, and the programs it sent: each file's SHA-256 recomputed from Kickoff 40's
    programs as archived in programs/k40/."""
    import hashlib

    file = _rig("k41-figures.json")
    doc = ar.load(file)
    root = ar.data_dir() / ar.RIGETTI
    programs = {
        p: [{"sha256": hashlib.sha256((root / r["file"]).read_bytes()).hexdigest()} for r in doc["programs"][p]]
        for p in "AB"
    }
    recomputed = {
        **{p: _figures_recomputed(doc[p]) for p in "AB"},
        "programs": programs,
        "programs_all_match_kickoff40": all(
            m["sha256"] == r["sha256"] for p in "AB" for m, r in zip(programs[p], doc["programs"][p])
        ),
    }
    leaves = compare("Kickoff 41, figures and programs", {file: recomputed}, {file: doc})
    rows = _rows(
        lambda: [
            (
                "every program matched Kickoff 40's",
                doc["programs_all_match_kickoff40"],
                recomputed["programs_all_match_kickoff40"],
            )
        ]
    )
    return rows, leaves


@cache
def k42_scan():
    days = (ar.load(_rig("k42-day1.json")), ar.load(_rig("k42-day2.json")))
    compiled = {d: _compiled("k42", d) for d in ("day1", "day2")}
    return ar.offset_scan(*days, ar.load(_rig("k42-figures.json")), k40_stage2(), compiled, k41_partB())


def _scan_rows(a, r, names):
    return [(f"{v}: verdict", a[v]["verdict"], r[v]["verdict"]) for v in names]


@cache
def k42_day1():
    """Kickoff 42, Day 1: every P(11), the fits and their bootstrap SD, V1 to V3 and the lines beside them."""
    file = _rig("k42-day1.json")
    doc, r = ar.load(file), k42_scan()["day1"]
    recomputed = {
        "archived": {
            "analysis": r,
            "records": r["records"],
            "records_all_match_names": all(x["matches_names"] for x in r["records"].values()),
        }
    }
    leaves = compare("Kickoff 42, Day 1", {file: recomputed}, {file: doc})
    a = doc["archived"]["analysis"]
    rows = _rows(
        lambda: [
            ("verdict", a["V1"]["verdict"], r["V1"]["verdict"]),
            ("working pairs", float(len(a["working"])), float(len(r["working"]))),
            ("V1: SD of delta_A", a["V1"]["sd_deltaA_across_working"], r["V1"]["sd_deltaA_across_working"]),
            ("V2: r(delta_A, delta_B)", _pearson(a["V2"]["r"]), _pearson(r["V2"]["r"])),
            ("V2: mean |delta_A - delta_B|", a["V2"]["mean_abs_dA_minus_dB"], r["V2"]["mean_abs_dA_minus_dB"]),
            (
                "V3: r(delta_A, Kickoff 40's k_A)",
                _pearson(a["V3"]["r_deltaA_vs_k40_kA"]),
                _pearson(r["V3"]["r_deltaA_vs_k40_kA"]),
            ),
            ("shape check", a["beside"]["shape_fraction_rms_le_2_shot"], r["beside"]["shape_fraction_rms_le_2_shot"]),
            *_scan_rows(a, r, ("V2", "V3")),
        ]
    )
    return rows, leaves


@cache
def k42_day2():
    """Kickoff 42, Day 2: as Day 1, with V4 under both rules, V5, the switch and the line against Kickoff 41."""
    file = _rig("k42-day2.json")
    doc, sc = ar.load(file), k42_scan()
    r = sc["day2"]
    recomputed = {
        "archived": {
            "analysis": r,
            "records": r["records"],
            "records_all_match_names": all(x["matches_names"] for x in r["records"].values()),
            "V4_amended_governs": sc["V4_amended_governs"],
            "V4_original_rule": sc["V4_original_rule"],
            "V4": sc["V4_amended_governs"],
            "V5": sc["V5"],
            "beside_k41": sc["beside_k41"],
        }
    }
    leaves = compare("Kickoff 42, Day 2", {file: recomputed}, {file: doc})
    a = doc["archived"]
    v4, v4o, v5 = sc["V4_amended_governs"], sc["V4_original_rule"], sc["V5"]
    rows = _rows(
        lambda: [
            ("verdict", a["V4_amended_governs"]["verdict"], v4["verdict"]),
            ("V4, original rule", a["V4_original_rule"]["verdict"], v4o["verdict"]),
            ("V5", a["V5"]["verdict"], v5["verdict"]),
            ("the switch", a["V5"]["switch"]["verdict"], v5["switch"]["verdict"]),
            *((f"V4 amended: r, {f}", _pearson(a["V4_amended_governs"][f]["r"]), _pearson(v4[f]["r"])) for f in "AB"),
            *((f"V4 original: r, {f}", _pearson(a["V4_original_rule"][f]["r"]), _pearson(v4o[f]["r"])) for f in "AB"),
            ("V5: pooled r", _pearson(a["V5"]["p_F"]), _pearson(v5["p_F"])),
            ("V5: median per-pair r", a["V5"]["median_per_pair_r"], v5["median_per_pair_r"]),
            (
                "shape check",
                a["analysis"]["beside"]["shape_fraction_rms_le_2_shot"],
                r["beside"]["shape_fraction_rms_le_2_shot"],
            ),
        ]
    )
    return rows, leaves


@cache
def k42_after_the_fact():
    """Computed after seeing Day 1, outside the verdicts."""
    file = _rig("k42-after-the-fact.json")
    doc = ar.load(file)
    a = ar.scan_after_the_fact(k42_scan()["day1"], k40_stage2())
    leaves = compare("Kickoff 42, after the fact", {file: a}, {file: doc})
    rows = _rows(
        lambda: [("r(delta_A, delta_B) without the edge fits", _pearson(doc["r_dA_dB"]), _pearson(a["r_dA_dB"]))]
    )
    return rows, leaves


@cache
def k42_inputs():
    """Kickoff 42's ideal curve from the circuits' own unitaries, its figures read back, and its programs: the task
    order drawn again with seed 42, and every file's SHA-256 recomputed from the programs archived in programs/."""
    import hashlib

    import numpy as np

    files = {k: _rig(f"k42-{k}.json") for k in ("ideal", "figures")}
    docs = {f: ar.load(f) for f in files.values()}
    ideal = docs[files["ideal"]]
    fams = {}
    worst = 0.0
    for f, fam in ideal["families"].items():
        rows = []
        for row in fam["rows"]:
            ex = ar.scan_ideal(f, row["offset"])
            rows.append({"exact_P11": ex, "exact_minus_mantri": ex - row["mantri"]})
            worst = max(worst, abs(round(ex, 3) - row["mantri"]))
        fams[f] = {"rows": rows, "peak_on_scan": max(ar.SCAN[f]["offsets"], key=lambda a: ar.scan_ideal(f, a))}
    figs = docs[files["figures"]]
    root = ar.data_dir() / ar.RIGETTI

    def sha(path):
        return hashlib.sha256((root / path).read_bytes()).hexdigest()

    rng = np.random.default_rng(ar.SCAN_SEED)
    pa, pb = rng.permutation(9), rng.permutation(9)
    order = []
    for k in range(9):
        order += [f"A{ar.SCAN['A']['offsets'][pa[k]]:+.2f}", f"B{ar.SCAN['B']['offsets'][pb[k]]:+.2f}"]
    by_label = {f"{p['family']}{p['offset']:+.2f}": p for p in figs["programs"]["files"]}
    shared = {
        k: {
            "sha256": sha(by_label[k]["file"]),
            "kickoff40_sha256": sha(v["file"]),
            "byte_identical": (root / by_label[k]["file"]).read_bytes() == (root / v["file"]).read_bytes(),
        }
        for k, v in figs["programs"]["shared_with_kickoff40"].items()
    }
    recomputed = {
        files["ideal"]: {"families": fams, "max_abs_rounded_exact_minus_mantri": worst},
        files["figures"]: {
            **{d: _figures_recomputed(figs[d]) for d in ("day1", "day2")},
            "programs": {
                "order_rule": {"A_perm": pa.tolist(), "B_perm": pb.tolist()},
                "order": order,
                "files": [{"sha256": sha(p["file"])} for p in figs["programs"]["files"]],
                "shared_with_kickoff40": shared,
                "shared_all_identical": all(
                    v["byte_identical"] and v["sha256"] == v["kickoff40_sha256"] for v in shared.values()
                ),
            },
        },
    }
    leaves = compare("Kickoff 42, ideal values, figures and programs", recomputed, docs)
    rows = _rows(
        lambda: [
            *(
                (f"ideal A at {row['offset']:+.2f}", row["exact_P11"], r["exact_P11"])
                for row, r in zip(ideal["families"]["A"]["rows"], fams["A"]["rows"])
            ),
            (
                "the five shared programs are Kickoff 40's",
                figs["programs"]["shared_all_identical"],
                recomputed[files["figures"]]["programs"]["shared_all_identical"],
            ),
        ]
    )
    return rows, leaves


def p11_from(counts, n_pairs):
    from manacitra.keptshare import p11_from_bitstrings

    return p11_from_bitstrings(counts, n_pairs).tolist()


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
    "Kickoff 37, Rigetti Cepheus-1-108Q": lambda: k37()[:2],
    "Kickoff 37, after the fact": k37_after_the_fact,
    "Kickoff 35, ibm_fez": lambda: k35()[:2],
    "Kickoff 38, Rigetti Cepheus-1-108Q": lambda: k38()[:2],
    "Kickoff 40, stage 1, placement": k40_placement,
    "Kickoff 40, stage 2, the map": k40_map,
    "Kickoff 40, after the fact": k40_after_the_fact,
    "Kickoff 40, stage 3, the payoff": k40_payoff,
    "Kickoff 40, figures and ideal values": k40_inputs,
    "Kickoff 41, Part A, the map a day later": k41_map,
    "Kickoff 41, Part B, the payoff with the day-old scores": k41_payoff,
    "Kickoff 41, figures and programs": k41_inputs,
    "Kickoff 42, Day 1": k42_day1,
    "Kickoff 42, Day 2": k42_day2,
    "Kickoff 42, after the fact": k42_after_the_fact,
    "Kickoff 42, ideal values, figures and programs": k42_inputs,
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
    "Kickoff 37, Rigetti Cepheus-1-108Q": "PLACEMENT",
    "Kickoff 35, ibm_fez": "HOLDS",
    "Kickoff 38, Rigetti Cepheus-1-108Q": "ACTIVITY",
    "Kickoff 40, stage 1, placement": "PINNED",
    "Kickoff 40, stage 2, the map": "DIAGNOSTIC",
    "Kickoff 40, stage 3, the payoff": "NOT SETTLED",
    "Kickoff 41, Part A, the map a day later": "HOLDS",
    "Kickoff 41, Part B, the payoff with the day-old scores": "USEFUL",
    "Kickoff 42, Day 1": "SPREAD",
    "Kickoff 42, Day 2": "HOLDS",
}
