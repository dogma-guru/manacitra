# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""Reading the archived runs in data/ back into the core functions.

Every function here recomputes from the archived counts (or, for the settling runs, which archived no counts, from
the archived P(11) table) and never from an archived analysis. The archived analyses are kept in each file under
"archived" so the recomputed numbers can be checked against them; tests/test_reproduction.py does exactly that.
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path

import numpy as np

from . import stats
from .circuits import CIRCUITS, GAP
from .keptshare import kept_from_order, p11_from_bitstrings, pair_outcomes_from_bitstrings
from .verdicts import analyse_map, analyse_payoff, leave_one_out
from .workload import ORDER_PAYOFF, aggregate, readout_confusion, workload_scores

#: Where data/ sits when the package is installed from a clone (pip install -e .)
BESIDE_SOURCE = Path(__file__).resolve().parents[2] / "data"
ENV = "MANACITRA_DATA"
REPOSITORY = "https://github.com/dogma-guru/manacitra"
_chosen: Path | None = None


class DataNotFound(FileNotFoundError):
    """The archived dataset (data/) was not found. It ships with the repository, not with the package."""


def _is_dataset(d: Path) -> bool:
    return d.is_dir() and (d / "SHA256SUMS").is_file()


def set_data_dir(path) -> None:
    """Use this folder as data/ for the rest of the process (the command line's --data). None clears it."""
    global _chosen
    _chosen = None if path is None else Path(path).expanduser().resolve()


def data_dir() -> Path:
    """The archived dataset's folder: the one given by set_data_dir (CLI: --data), else $MANACITRA_DATA, else data/
    beside the source tree (an install from a clone). Raises DataNotFound, saying how to get it and set it."""
    given = _chosen or (Path(os.environ[ENV]).expanduser() if os.environ.get(ENV) else None)
    if given is not None:
        if _is_dataset(given):
            return given
        raise DataNotFound(
            f"{given} is not the Manacitra dataset (no SHA256SUMS in it). Point --data or {ENV} at the data/ folder "
            f"of a clone of {REPOSITORY}."
        )
    if _is_dataset(BESIDE_SOURCE):
        return BESIDE_SOURCE
    raise DataNotFound(
        "the Manacitra dataset (data/) was not found. It ships with the repository, not with the package. Get it "
        f"with: git clone {REPOSITORY}. Then either install from the clone (pip install -e .), or point at it with "
        f"{ENV}=/path/to/manacitra/data (on the command line: manacitra --data /path/to/manacitra/data ...)."
    )


def resolve(path) -> Path:
    """A file as given if it exists; otherwise the same path inside the dataset (data_dir())."""
    p = Path(path)
    if p.is_absolute() or p.exists():
        return p
    return data_dir() / p


def load(path) -> dict:
    return json.loads(resolve(path).read_text())


#: The bit readings a counts record can declare in meta.bit_reading (Amendment A8, R1); the data README's Formats
#: section describes each
BIT_READINGS = ("qiskit-adjacent", "openquantum-reversed", "braket-measured-qubits", "per-pair")


class UndeclaredReading(ValueError):
    """A counts record without a declared bit reading, or with one this package does not know: nothing is decoded."""


class NotATable(ValueError):
    """A counts record whose positions do not all measure the run's pairs (per task, or per round, or per condition):
    it has no single per-circuit, per-pair table, and its own recompute reads it."""


def bit_reading(rec: dict) -> str:
    """The record's declared bit reading, or UndeclaredReading, naming the field."""
    reading = (rec.get("meta") or {}).get("bit_reading")
    if reading is None:
        raise UndeclaredReading(
            "meta.bit_reading is missing: a record with counts must declare its bit reading, one of "
            f"{', '.join(BIT_READINGS)}; nothing was decoded"
        )
    if reading not in BIT_READINGS:
        raise UndeclaredReading(
            f"meta.bit_reading is {reading!r}, not one of {', '.join(BIT_READINGS)}; nothing was decoded"
        )
    return reading


def p11_table(rec: dict) -> np.ndarray:
    """Per circuit, per pair P(11), from the archived counts, read by the record's declared bit reading
    (meta.bit_reading; Amendment A8): one reader per reading, the same ones the route-aware recomputes use.

    * qiskit-adjacent (IBM): the rightmost character is classical bit 0; pair i is bits 2i and 2i + 1
      (p11_from_bitstrings);
    * openquantum-reversed: pair i is classical bits i and n - 1 - i, classical bit k at position n - 1 - k
      (p11_classical_index);
    * braket-measured-qubits: character j of a key belongs to the task's measured_qubits[j] (braket_p11);
    * per-pair (the simulations): per pair, counts of 00, 01, 10 and 11.

    A record with no counts (the settling runs) gives its archived P(11) table. A record without a declared reading,
    or with an unknown one, is refused (UndeclaredReading); one whose positions do not all measure the run's pairs is
    refused too (NotATable)."""
    if "counts" not in rec:
        return np.asarray(rec["per_circuit_P11"], float)
    reading = bit_reading(rec)
    counts = rec["counts"]
    if not isinstance(counts, list):
        raise NotATable("its counts are per task, not per circuit position; its own recompute reads them")
    if "pairs" not in rec:
        raise NotATable(
            "it has no run-wide list of pairs: its positions measure different pairs (by round or by "
            "condition); its own recompute reads them"
        )
    pairs = [tuple(p["qubits"]) if isinstance(p, dict) else tuple(p) for p in rec["pairs"]]
    if reading == "per-pair":
        return np.asarray([[pc["11"] / sum(pc.values()) for pc in c] for c in counts], float)
    if reading == "braket-measured-qubits":
        tasks = rec["tasks"]
        return np.array([braket_p11(c, t["measured_qubits"], pairs) for c, t in zip(counts, tasks)])
    width = {len(k.replace(" ", "")) for c in counts for k in list(c)[:1]}
    if width != {2 * len(pairs)}:
        raise NotATable(
            f"its keys are {sorted(width)} bits wide, not {2 * len(pairs)} for its {len(pairs)} pairs: its positions "
            "measure different pairs; its own recompute reads them"
        )
    if reading == "openquantum-reversed":
        return np.array([p11_classical_index(c, len(pairs)) for c in counts])
    return np.asarray([p11_from_bitstrings(c, len(pairs)) for c in counts], float)


# --------------------------------------------------------------------------- Kickoff 29's settling run and the baseline
SETTLE_ORDER = ["A no", "A off", "A wrong", "A wrong", "A off", "A no"]


def settle_k(rec: dict) -> np.ndarray:
    """k_A per pair from a settling run (both copies of each variant)."""
    return kept_from_order(np.asarray(rec["per_circuit_P11"], float), rec["order"], "A")[0]


def settle_baseline(rec: dict) -> dict:
    """Kickoff 31's step 0: the map from a settling run, its first-copy against last-copy repeat, r(k, x), and r(k, the
    wrong sign's kept share)."""
    P = np.asarray(rec["per_circuit_P11"], float)
    d = GAP["A"]
    f = CIRCUITS["A"]
    k1, k2 = (P[1] - P[0]) / d, (P[4] - P[5]) / d
    k = ((P[1] + P[4]) / 2 - (P[0] + P[5]) / 2) / d
    kw = ((P[2] + P[3]) / 2 - (P[0] + P[5]) / 2) / (f.ideal_wrong - f.ideal_no)
    x = np.asarray(rec["x"], float)
    return {"r_split": stats.corr(k1, k2), "r_k_x": stats.corr(k, x), "r_k_wrong": stats.corr(k, kw), "k": k.tolist()}


SETTLE_VARIANTS = {"no offset": "A no", "offset": "A off", "wrong sign": "A wrong"}


def settle_analysis(rec: dict) -> dict:
    """Kickoff 29's settling run, recomputed from its archived P(11) table (the run archived no counts).

    Per pair, each variant's P(11) is the mean of its two copies; d = P(offset) - P(no offset). The standard error is
    the spread of d over the pairs, sd(d) / sqrt(n); z = mean(d) / SE. The shot-noise standard error of mean(d) is
    sqrt(mean over pairs of P_off (1 - P_off) + P_no (1 - P_no)) / (2 shots) / n), each variant having two copies of
    `shots` shots. The repetitions pair the first copies of offset and no offset (repetition 1) and the last copies
    (repetition 2). The settling run's decision rule: SETTLED-DETECTED if z >= 3 and SE <= 0.004; SETTLED-NULL if
    SE <= 0.004 and z < 2; otherwise NOT SETTLED. The ideal values are each variant's exact P(11)."""
    from .circuits import ideal_exact

    P_c = np.asarray(rec["per_circuit_P11"], float)
    order = list(rec["order"])
    n = P_c.shape[1]
    shots = rec["meta"]["shots_per_circuit"]
    P = {
        v: P_c[[i for i, lab in enumerate(order) if lab == lab_v]].mean(axis=0) for v, lab_v in SETTLE_VARIANTS.items()
    }
    d = P["offset"] - P["no offset"]
    w = P["wrong sign"] - P["no offset"]
    mean_d, se = float(d.mean()), float(d.std(ddof=1) / math.sqrt(n))
    z = mean_d / se if se > 0 else float("inf")
    if z >= 3 and se <= 0.004:
        verdict = "SETTLED-DETECTED"
    elif se <= 0.004 and z < 2:
        verdict = "SETTLED-NULL"
    else:
        verdict = "NOT SETTLED"
    var = P["offset"] * (1 - P["offset"]) + P["no offset"] * (1 - P["no offset"])
    shot_se = float(math.sqrt(np.mean(var) / (2 * shots) / n))
    first, last = order.index, (lambda lab: len(order) - 1 - order[::-1].index(lab))
    rep = {
        "1": float(np.mean(P_c[first("A off")] - P_c[first("A no")])),
        "2": float(np.mean(P_c[last("A off")] - P_c[last("A no")])),
    }
    return {
        "analysis": {
            "P_per_pair": {v: P[v].tolist() for v in P},
            "mean_P": {v: float(P[v].mean()) for v in P},
            "d_per_pair": d.tolist(),
            "mean_d": mean_d,
            "se_d_between_pairs": se,
            "z": z,
            "shot_noise_se_of_mean_d": shot_se,
            "pairs_offset_above_no": int(np.sum(d > 0)),
            "pairs_wrong_below_no": int(np.sum(w < 0)),
            "mean_wrong_minus_no": float(w.mean()),
            "mean_d_by_repetition": rep,
            "verdict": verdict,
        },
        "ideal": {v: ideal_exact(lab) for v, lab in SETTLE_VARIANTS.items()},
    }


# --------------------------------------------------------------------------- Kickoff 31: the map
def map_from_record(rec: dict, prev_k=None, seed: int | None = None, **kw) -> dict:
    """The map rule on an archived map run (Kickoff 31 on IBM, Kickoff 36 in simulation)."""
    P = p11_table(rec)
    from .layout import vendor_flag

    flagged = None
    if "published_at_submission" in rec:
        pub = rec["published_at_submission"]
        x = [r["x"] for r in pub]
        cz = [r["cz_error"] for r in pub]
        ro = [sum(r["readout_error"]) for r in pub]
        flagged = [vendor_flag(two_qubit_error=c) for c in cz]
    else:
        x = rec.get("x")
        cz = [p["cz_pauli_error"] for p in rec["pairs"]] if rec["pairs"] and isinstance(rec["pairs"][0], dict) else None
        ro = [sum(p["readout_error"]) for p in rec["pairs"]] if cz is not None else None
    seed = seed if seed is not None else rec["meta"].get("permutation_seed", 31)
    return analyse_map(
        P,
        rec["order"],
        x=x,
        cz_error=cz,
        readout_error=ro,
        shots=rec["meta"]["shots_per_circuit"],
        seed=seed,
        prev_k=prev_k,
        flagged=flagged,
        **kw,
    )


def previous_k_for(rec: dict, settle: dict) -> np.ndarray:
    """The settling run's k_A for the map run's pairs, in the map run's order (Kickoff 31's S4)."""
    k = settle_k(settle)
    idx = {tuple(p): i for i, p in enumerate(settle["pairs"])}
    return np.array([k[idx[tuple(p)]] for p in rec["pairs"]])


# --------------------------------------------------------------------------- Kickoff 32: alone or crowded
def isolation_analysis(rec: dict, k31_pairs, k31_kA, seed: int = 32) -> dict:
    """Kickoff 32's analysis, recomputed from counts: each test pair's k with all 27 pairs active (D) and with only
    separated test pairs active (S), the gap between the six that kept most and the six that kept least in each
    condition, and the closed fraction F = 1 - Gap_S / Gap_D with its bootstrap interval. Also the dense map of all
    27 pairs (kD_all27), which Kickoff 33 used as its prior map.

    Verdict, as fixed in Kickoff 32: MAP NOT PRESENT (Gap_D < 0.2), CROWDED (F >= 0.6 and the worst six gain at least
    3 SE), THE GATE (F <= 0.25 and Gap_S >= 3 SE: the pair's own two-qubit gate), MIXED otherwise.
    """
    sel, plan, shots = rec["selection"], rec["plan"], rec["meta"]["shots_per_circuit"]

    def pairs_of(cond):
        return [tuple(p) for p in (sel["dense_pairs"] if cond == "D" else sel["groups"][int(cond[1:]) - 1])]

    agg: dict = {}
    for (cond, v), c in zip(plan, rec["counts"]):
        prs = pairs_of(cond)
        for p, val in zip(prs, p11_from_bitstrings(c, len(prs))):
            agg.setdefault((p, "D" if cond == "D" else "S", v), []).append(val)

    def k_and_se(p, mode):
        no, off = np.mean(agg[(p, mode, "no")]), np.mean(agg[(p, mode, "off")])
        n = len(agg[(p, mode, "no")]) * shots
        return (off - no) / GAP["A"], math.sqrt(no * (1 - no) / n + off * (1 - off) / n) / GAP["A"]

    group_of = {tuple(q): g + 1 for g, grp in enumerate(sel["groups"]) for q in grp}
    rows = []
    for side in ("worst", "best"):
        for r in sel[f"{side}6"]:
            p = tuple(r["pair"])
            kD, seD = k_and_se(p, "D")
            kS, seS = k_and_se(p, "S")
            rows.append(
                {
                    "pair": list(p),
                    "side": side,
                    "group": group_of[p],
                    "kD": kD,
                    "kS": kS,
                    "delta": kS - kD,
                    "se_delta": math.hypot(seD, seS),
                    **{
                        f"P_{v}_{mode}": float(np.mean(agg[(p, mode, v)])) for mode in ("D", "S") for v in ("no", "off")
                    },
                    "shots_per_variant": len(agg[(p, "D", "no")]) * shots,
                }
            )
    W = [r for r in rows if r["side"] == "worst"]
    B = [r for r in rows if r["side"] == "best"]

    def mean(rs, key):
        return float(np.mean([r[key] for r in rs]))

    def se_m(rs, key):
        return float(np.std([r[key] for r in rs], ddof=1) / math.sqrt(len(rs)))

    gapD, gapS = mean(B, "kD") - mean(W, "kD"), mean(B, "kS") - mean(W, "kS")
    se_gapS = math.hypot(se_m(B, "kS"), se_m(W, "kS"))
    F = 1 - gapS / gapD
    rng = np.random.default_rng(seed)
    wD, wS = np.array([r["kD"] for r in W]), np.array([r["kS"] for r in W])
    bD, bS = np.array([r["kD"] for r in B]), np.array([r["kS"] for r in B])
    Fs = []
    for _ in range(10_000):
        iw, ib = rng.integers(0, 6, 6), rng.integers(0, 6, 6)
        gd = bD[ib].mean() - wD[iw].mean()
        gs = bS[ib].mean() - wS[iw].mean()
        Fs.append(1 - gs / gd if gd != 0 else np.nan)
    ci = [float(np.nanpercentile(Fs, 5)), float(np.nanpercentile(Fs, 95))]
    dW, dW_se = mean(W, "delta"), se_m(W, "delta")
    kD_all = []
    for p in [tuple(q) for q in k31_pairs]:
        kD_all.append((np.mean(agg[(p, "D", "off")]) - np.mean(agg[(p, "D", "no")])) / GAP["A"])
    no_D = [np.mean(agg[(tuple(p), "D", "no")]) for p in k31_pairs]
    if gapD < 0.2:
        v = "MAP NOT PRESENT"
    elif F >= 0.6 and dW >= 3 * dW_se:
        v = "CROWDED"
    elif F <= 0.25 and gapS >= 3 * se_gapS:
        v = "THE GATE"
    else:
        v = "MIXED"
    return {
        "rows": rows,
        "gap_D": gapD,
        "gap_S": gapS,
        "se_gap_S": se_gapS,
        "F": F,
        "F_ci90": ci,
        "mean_delta_worst": dW,
        "se_delta_worst": dW_se,
        "mean_delta_best": mean(B, "delta"),
        "se_delta_best": se_m(B, "delta"),
        "kD_all27": kD_all,
        "L_D_all27": [float(n / CIRCUITS["A"].ideal_no) for n in no_D],
        "r_kD_vs_kA31_all27": float(np.corrcoef(kD_all, k31_kA)[0, 1]),
        "verdict": v,
    }


def isolation_p11(rec: dict) -> list[list[float]]:
    """Kickoff 32's P(11) per circuit, for the pairs active in that circuit (all 27 in D, one group in S1 and S2)."""
    sel = rec["selection"]
    out = []
    for (cond, _), c in zip(rec["plan"], rec["counts"]):
        n = len(sel["dense_pairs"]) if cond == "D" else len(sel["groups"][int(cond[1:]) - 1])
        out.append([float(v) for v in p11_from_bitstrings(c, n)])
    return out


# --------------------------------------------------------------------------- Kickoff 33: the payoff
def payoff_from_record(rec: dict, k_prior, L_prior, ideal: list, shots_interval: bool = False, **kw) -> dict:
    """The payoff rule on an archived payoff run, with the prior map from an earlier run."""
    n = len(rec["pairs"])
    outcomes = [pair_outcomes_from_bitstrings(c, n) for c in rec["counts"]]
    agg = aggregate(outcomes, rec.get("order", ORDER_PAYOFF))
    M = readout_confusion(agg)
    ws = workload_scores(agg, ideal, M)
    pno = agg["A no"][:, 3] / agg["A no"].sum(axis=1)
    poff = agg["A off"][:, 3] / agg["A off"].sum(axis=1)
    k_now, L_now = (poff - pno) / GAP["A"], pno / CIRCUITS["A"].ideal_no
    x = [r["x"] for r in rec["published_at_submission"]]
    spec = {"counts": ws["shots"], "dists": ws["measured_dists"], "ideal": ideal} if shots_interval else None
    out = analyse_payoff(
        ws["W_per_circuit"],
        k_prior,
        x,
        L_prior=L_prior,
        k_now=k_now,
        L_now=L_now,
        W_rc_per_circuit=ws["W_rc_per_circuit"],
        seed=rec["meta"].get("seed", 33),
        shots_interval=spec,
        **kw,
    )
    out.update(
        {
            "W_per_circuit": ws["W_per_circuit"].tolist(),
            "W_rc_per_circuit": ws["W_rc_per_circuit"].tolist(),
            "measured_dists": np.asarray(ws["measured_dists"]).tolist(),
            "k_now": k_now.tolist(),
            "L_now": L_now.tolist(),
            "P_A_no": pno.tolist(),
            "P_A_off": poff.tolist(),
            "readout_confusion": M.tolist(),
            "predictors": {
                "k_prior": list(map(float, k_prior)),
                "x": x,
                "L_prior": list(map(float, L_prior)),
                "k_now": k_now.tolist(),
                "L_now": L_now.tolist(),
            },
        }
    )
    return out


# --------------------------------------------------------------------------- Kickoff 34b: the map on Rigetti
RIGETTI = "rigetti_cepheus_1_108q"


def p11_classical_index(counts: dict[str, int], n_pairs: int) -> np.ndarray:
    """P(11) per pair in Kickoff 34b's classical-index reading: pair i is measured into classical bits i and
    2N - 1 - i, and classical bit k is the character at position 2N - 1 - k of the 2N-character key."""
    n = 2 * n_pairs
    tot = sum(counts.values())
    p = np.zeros(n_pairs)
    for key, m in counts.items():
        for i in range(n_pairs):
            if key[n - 1 - i] == "1" and key[i] == "1":
                p[i] += m
    return p / tot


def bit_order_check(counts, pairs, order) -> dict:
    """Kickoff 34b's bit-order check on the main job: per pair, P(11) - P(a = 1) P(b = 1) in the classical-index
    reading, averaged over the pairs and the B-no circuits; it passes when that is above zero. The ideal it is shown
    beside is circuit B without the offset, noise-free: P(11) - P(a = 1) P(b = 1) from the exact distribution."""
    from .backends.openquantum import outcomes_from_output, pair_covariance
    from .circuits import CIRCUITS, unitary

    covs = [pair_covariance(outcomes_from_output(c, pairs)).mean() for c, lab in zip(counts, order) if lab == "B no"]
    cov = float(np.mean(covs))
    p = np.abs(unitary(CIRCUITS["B"].c, None)[:, 0]) ** 2  # outcomes 00, 01, 10, 11 (s = a + 2 b)
    ideal = float(p[3] - (p[1] + p[3]) * (p[2] + p[3]))
    return {"mean_pair_covariance_B_no": cov, "ideal": ideal, "passes": cov > 0}


def screen_pair_rule(screen: dict) -> dict:
    """Kickoff 34b's pair rule, applied again to the screen's L_s: a candidate passes at L_s >= 0.5; the 27 highest
    passing are taken, ties to the lower edge index; fewer than 20 passing stops."""
    cands = screen["pair_rule"]["candidates"]
    passing = [c for c in cands if c["L_s"] >= 0.5]
    taken = sorted(passing, key=lambda c: (-c["L_s"], c["edge_index"]))[:27]
    ids = {c["edge_index"] for c in taken}
    return {
        "candidates": [{"passes_floor": c["L_s"] >= 0.5, "taken": c["edge_index"] in ids} for c in cands],
        "n_passing": len(passing),
        "n_taken": len(taken),
        "enough": len(passing) >= 20,
        "taken_pairs": [c["pair"] for c in sorted(taken, key=lambda c: c["edge_index"])],
    }


def rigetti_map(rec: dict, screen: dict | None = None) -> dict:
    """Kickoff 34b recomputed from the archived counts: the dead-pair filter, the capped map rule on the working pairs,
    the sealed leave-one-out, the 20-pair check computed after the fact, and the descriptive lines beside the verdict
    (those that need the screen's levels only if `screen` is given)."""
    pairs = [tuple(p) for p in rec["pairs"]]
    P = p11_table(rec)
    order, seed, shots = rec["order"], rec["meta"]["permutation_seed"], rec["meta"]["shots_per_circuit"]
    halves = {c: tuple(h) for c, h in rec["halves"].items()}
    an = analyse_map(P, order, shots=shots, seed=seed, halves=halves, dead_pair_floor=rec["meta"]["dead_pair_floor"])
    keep = an["pair_index"]
    W = P[:, keep]
    loo = leave_one_out(W, order, seed=seed, shots=shots, halves=halves)
    extreme = {(13, 14), (101, 102)}
    twenty = [j for j, i in enumerate(keep) if pairs[i] not in extreme]
    after = analyse_map(W[:, twenty], order, shots=shots, seed=seed, halves=halves)
    a_no = np.array(an["dead_pair_filter"]["mean_P_A_no"])
    L1, L2 = (P[0] + P[7]) / 2, (P[8] + P[15]) / 2
    d = {"L_wave1": L1.tolist(), "L_wave2": L2.tolist(), "r_Lwave1_vs_Lwave2": stats.corr(L1, L2)}
    if screen is not None:
        Ls_all = {tuple(c["pair"]): c["L_s"] for c in screen["pair_rule"]["candidates"]}
        Ls = np.array([Ls_all[pairs[i]] for i in keep])
        shared = rec["archived"]["descriptive"]["across_runs"]["shared_pairs_in_all_three_runs"]
        idx = {p: i for i, p in enumerate(pairs)}
        test = np.array(shared["test_17_01"])
        scr = np.array([Ls_all[tuple(p)] for p in shared["pairs"]])
        main = np.array([a_no[idx[tuple(p)]] for p in shared["pairs"]])
        d.update(
            {
                "r_Ls_vs_Lmain": stats.corr(Ls, a_no[keep]),
                "r_kA_vs_Ls": stats.corr(an["kA"], Ls),
                "main_shared": main.tolist(),
                "r_test_main": stats.corr(test, main),
                "r_screen_main": stats.corr(scr, main),
                "r_test_screen": stats.corr(test, scr),
                "r_screen_main_all_27_chosen": stats.corr([Ls_all[p] for p in pairs], a_no),
            }
        )
    return {
        "P": P,
        "pairs": pairs,
        "bit_order_check": bit_order_check(rec["counts"], pairs, order),
        "analysis": an,
        "working_pairs": [pairs[i] for i in keep],
        "excluded_pairs": [pairs[i] for i in an["dead_pair_filter"]["excluded"]],
        "leave_one_out": {**loo, "dropped_pair": pairs[keep[loo["dropped_index"]]]},
        "after_the_fact_20": after,
        "descriptive": d,
    }


# --------------------------------------------------------------------------- Kickoff 37: placement or drift
#: Kickoff 37's thresholds, fixed before the run: the control and S/N at 0.7 or above, W/T below 0.4, and the short-gap
#: label under 60 minutes
PLACEMENT_HIGH, PLACEMENT_LOW, PLACEMENT_SHORT_GAP_S = 0.7, 0.4, 3600


def _corr_n(a, b) -> dict:
    return {**stats.corr(a, b), "n": len(a)}


def _utc_seconds(s: str) -> int:
    from datetime import datetime

    return int(datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp())


def placement_rule(c1, c2, d1, d2, t27, t53) -> tuple[str, dict]:
    """Kickoff 37's rule. If c_1 or c_2 is below 0.7, NOT SETTLED (unstable). Otherwise W: d_1 and d_2 below 0.4;
    N: both at or above 0.7; T: t27 and t53 below 0.4; S: both at or above 0.7. PLACEMENT = W and S, DRIFT = N and T,
    BOTH = W and T, NEITHER = N and S, MIXED otherwise."""
    hi, lo = PLACEMENT_HIGH, PLACEMENT_LOW
    if c1 < hi or c2 < hi:
        return "NOT SETTLED (unstable)", {}
    cond = {
        "W": d1 < lo and d2 < lo,
        "N": d1 >= hi and d2 >= hi,
        "T": t27 < lo and t53 < lo,
        "S": t27 >= hi and t53 >= hi,
    }
    for v, (a, b) in {"PLACEMENT": "WS", "DRIFT": "NT", "BOTH": "WT", "NEITHER": "NS"}.items():
        if cond[a] and cond[b]:
            return v, cond
    return "MIXED", cond


def placement_or_drift(rec: dict, main34b: dict | None = None, screen34b: dict | None = None) -> dict:
    """Kickoff 37, recomputed from its archived counts and task times. Like settle_analysis, this recomputes one
    archived run's own rule; it is not a public verdict and has no command.

    Two programs from Kickoff 34b ran unchanged as three tasks per wave (T1 = P27, T2 = P53, T3 = P27), in two waves.
    Level L = P(11) per pair per task, in Kickoff 34b's classical-index reading. Per wave w, on the 27 P27 pairs:
    c_w = r(T1, T3); d_w = the mean of r(T1, T2) and r(T3, T2), T2 restricted to the 27 pairs. Across the waves:
    t27 = r(the mean of T1 and T3 in wave 1, the same in wave 2); t53 = r(T2 in wave 1, T2 in wave 2), on 53 pairs.
    The gap is the first wave 2 completion minus the last wave 1 completion; the mean completion times are beside it.
    The verdict's readings are Amendments A1 and A2's, with N the gap in hours, rounded.

    Outside the verdict: the crowding lean (A1), and, given Kickoff 34b's main job and screen, wave 1's T1 against
    34b's "A no" levels (the mean of its four identical tasks, and its first alone) and wave 1's T2 against 34b's screen
    levels. The checks computed after seeing the data are under "after_the_fact"."""
    p27 = [tuple(p) for p in rec["programs"]["P27"]["pairs"]]
    p53 = [tuple(p) for p in rec["programs"]["P53"]["pairs"]]
    at = [p53.index(p) for p in p27]
    tasks = {t["label"]: t for t in rec["meta"]["tasks"]}
    L = {
        t["label"]: p11_classical_index(rec["counts"][t["label"]], rec["programs"][t["program"]]["n_pairs"])
        for t in rec["tasks"]
    }
    waves = ("wave1", "wave2")
    m: dict = {}
    for i, w in enumerate(waves, 1):
        T1, T2, T3 = L[f"{w}-T1"], L[f"{w}-T2"][at], L[f"{w}-T3"]
        m[f"c_{i}"] = _corr_n(T1, T3)
        r12, r32 = _corr_n(T1, T2), _corr_n(T3, T2)
        m[f"d_{i}"] = {
            "pearson": (r12["pearson"] + r32["pearson"]) / 2,
            "spearman": (r12["spearman"] + r32["spearman"]) / 2,
            "r_T1_T2": r12,
            "r_T3_T2": r32,
            "n": len(at),
        }
    mean_w = {w: (L[f"{w}-T1"] + L[f"{w}-T3"]) / 2 for w in waves}
    m["t27"] = _corr_n(mean_w["wave1"], mean_w["wave2"])
    m["t53"] = _corr_n(L["wave1-T2"], L["wave2-T2"])
    names = ("c_1", "c_2", "d_1", "d_2", "t27", "t53")
    v, cond = placement_rule(*(m[k]["pearson"] for k in names))
    vs, conds = placement_rule(*(m[k]["spearman"] for k in names))

    done = {w: [_utc_seconds(t["completed_utc"]) for t in tasks.values() if t["label"].startswith(w)] for w in waves}
    gap = min(done["wave2"]) - max(done["wave1"])
    short = gap < PLACEMENT_SHORT_GAP_S
    h = round(gap / 3600)
    readings = {
        "N_hours": h,
        "PLACEMENT": f"program-dependent (placement or crowding); the chip's levels held over about {h} hours",
        "DRIFT": f"time-dependent over about {h} hours; the chip changed, or the compiler re-placed after a "
        "recalibration; the design cannot separate the two",
        "BOTH": f"program-dependent (placement or crowding), and time-dependent over about {h} hours (the chip "
        "changed, or the compiler re-placed after a recalibration)",
        "NEITHER": f"neither shows: not program-dependent, and the levels held over about {h} hours",
    }
    order = {
        w: [
            t["task"]
            for t in sorted((t for t in tasks.values() if t["label"].startswith(w)), key=lambda t: t["completed_utc"])
        ]
        for w in waves
    }

    desc: dict = {}
    if main34b is not None and screen34b is not None:
        P = np.array([p11_classical_index(c, len(main34b["pairs"])) for c in main34b["counts"]])
        assert [tuple(p) for p in main34b["pairs"]] == p27, "Kickoff 34b's main job ran the P27 pairs, in this order"
        a_no = P[[i for i, lab in enumerate(main34b["order"]) if lab == "A no"]]
        Ls_of = {tuple(c["pair"]): c["L_s"] for c in screen34b["pair_rule"]["candidates"]}
        Ls = np.array([Ls_of[p] for p in p53])
        desc = {
            "r_T1w1_vs_34b_main_A_no_mean_of_four": _corr_n(L["wave1-T1"], a_no.mean(axis=0)),
            "r_T1w1_vs_34b_main_position1": _corr_n(L["wave1-T1"], a_no[0]),
            "r_T2w1_vs_34b_screen": _corr_n(L["wave1-T2"], Ls),
            "r_T2w1_on_27_vs_34b_screen_on_27": _corr_n(L["wave1-T2"][at], Ls[at]),
        }
    shots = rec["meta"]["shots_per_task"]
    crowd: dict = {}
    for w in waves:
        T1, T2, T3 = L[f"{w}-T1"], L[f"{w}-T2"][at], L[f"{w}-T3"]

        def var(p):
            return p * (1 - p) / shots

        m1, m3 = 3 * np.sqrt(var(T2) + var(T1)), 3 * np.sqrt(var(T2) + var(T3))
        hi = [list(p27[i]) for i in range(len(p27)) if T2[i] - T1[i] > m1[i] and T2[i] - T3[i] > m3[i]]
        lo = [list(p27[i]) for i in range(len(p27)) if T1[i] - T2[i] > m1[i] and T3[i] - T2[i] > m3[i]]
        crowd[w] = {
            "mean_T2_minus_T1": float(np.mean(T2 - T1)),
            "mean_T2_minus_T3": float(np.mean(T2 - T3)),
            "n_T2_higher_than_both": len(hi),
            "n_T2_lower_than_both": len(lo),
            "pairs_higher": hi,
            "pairs_lower": lo,
        }
    desc["crowding_lean"] = crowd

    after: dict = {}
    if main34b is not None:
        excluded = sorted(
            (float(np.mean(a_no[:, i])), i)
            for i in range(len(p27))
            if np.mean(a_no[:, i]) < main34b["meta"]["dead_pair_floor"]
        )
        five = [i for _, i in excluded]
        keep = [i for i in range(len(p27)) if i not in five]
        T2k = {w: L[f"{w}-T2"][at][keep] for w in waves}
        after["without_34b_five_low_pairs"] = {
            "pairs_dropped": [list(p27[i]) for i in five],
            "n": len(keep),
            "d_1_pearson_T1_vs_T2": _corr_n(L["wave1-T1"][keep], T2k["wave1"]),
            "d_2_pearson_T1_vs_T2": _corr_n(L["wave2-T1"][keep], T2k["wave2"]),
            "t27": _corr_n(mean_w["wave1"][keep], mean_w["wave2"][keep]),
        }
        after["the_five_low_pairs"] = {
            f"{p27[i][0]}-{p27[i][1]}": {
                f"{t}_w{w[-1]}": float(L[f"{w}-{t}"][at[i] if t == "T2" else i])
                for w in waves
                for t in ("T1", "T3", "T2")
            }
            for i in five
        }
    others = [j for j in range(len(p53)) if j not in at]
    after["t53_split"] = {
        "on_the_27_P27_pairs": _corr_n(L["wave1-T2"][at], L["wave2-T2"][at]),
        "on_the_26_other_pairs": _corr_n(L["wave1-T2"][others], L["wave2-T2"][others]),
    }
    change = sorted(range(len(p53)), key=lambda j: -abs(L["wave2-T2"][j] - L["wave1-T2"][j]))[:6]
    after["largest_P53_changes_wave1_to_wave2"] = [
        {"pair": list(p53[j]), "w1": float(L["wave1-T2"][j]), "w2": float(L["wave2-T2"][j])} for j in change
    ]
    return {
        "per_task_P11": {k: v.tolist() for k, v in L.items()},
        "measures": m,
        "verdict": {
            "on_pearson": v,
            "conditions": cond,
            "spearman_reading_beside": vs,
            "spearman_conditions": conds,
            "time_half_label": "short gap" if short else "normal",
            "readings_per_amendments_A1_A2": readings,
        },
        "gap": {
            "seconds": gap,
            "minutes": gap / 60,
            "midpoint_to_midpoint_minutes": float(np.mean(done["wave2"]) - np.mean(done["wave1"])) / 60,
            "short_gap": short,
        },
        "completion_order": order,
        "descriptive": desc,
        "after_the_fact": after,
    }


# --------------------------------------------------------------------------- Kickoff 38: footprint or activity
#: Kickoff 38's thresholds, fixed before the run
ACTIVITY_HIGH, ACTIVITY_LOW = 0.7, 0.4
ACTIVITY_READINGS = {
    "FOOTPRINT": "The levels follow which qubits the program measures, not which pairs run gates. Consistent with "
    "placement chosen by the program's footprint, or with crowding at readout from measuring more qubits. Crowding by "
    "gate activity is not needed.",
    "ACTIVITY": "The levels follow which pairs run gates. Consistent with crowding by the other active pairs, or with "
    "the compiler placing pairs by gate connectivity. The design does not separate these two.",
    "MIXED": "Report f and a, and which conditions held.",
    "NOT SETTLED (unstable)": "The same program did not agree with itself.",
    "NOT SETTLED (no difference today)": "The difference to be explained did not appear.",
}


def activity_rule(c, d, f, a) -> tuple[str, dict]:
    """Kickoff 38's rule. NOT SETTLED (unstable) if the control c < 0.7; NOT SETTLED (no difference today) if the
    difference to explain d >= 0.4; then FOOTPRINT if f >= 0.7 and a < 0.4, ACTIVITY if a >= 0.7 and f < 0.4, MIXED
    otherwise."""
    hi, lo = ACTIVITY_HIGH, ACTIVITY_LOW
    if c < hi:
        return "NOT SETTLED (unstable)", {"c_ge_0.7": False}
    if d >= lo:
        return "NOT SETTLED (no difference today)", {"c_ge_0.7": True, "d_lt_0.4": False}
    cond = {
        "c_ge_0.7": True,
        "d_lt_0.4": True,
        "f_ge_0.7": f >= hi,
        "a_lt_0.4": a < lo,
        "a_ge_0.7": a >= hi,
        "f_lt_0.4": f < lo,
    }
    if cond["f_ge_0.7"] and cond["a_lt_0.4"]:
        return "FOOTPRINT", cond
    if cond["a_ge_0.7"] and cond["f_lt_0.4"]:
        return "ACTIVITY", cond
    return "MIXED", cond


def _qasm_kind(line: str) -> str:
    s = line.strip()
    if not s:
        return "blank"
    if s.startswith("OPENQASM"):
        return "header"
    if s.startswith("bit["):
        return "decl"
    if " = measure $" in s:
        return "measure"
    return "gate"


def p53i_checks(p27_text: str, p53_text: str, p53i_text: str, p27_pairs, p53_pairs) -> dict:
    """Kickoff 38's five checks on the built program P53i, from the three programs' texts: P53i is P53 without every
    gate line on a qubit of the 26 pairs not in P27, and runs exactly P27's gate lines, in P27's order."""
    import re
    from collections import Counter

    def qubits(line):
        return {int(q) for q in re.findall(r"\$(\d+)", line)}

    p27, p53 = [tuple(p) for p in p27_pairs], [tuple(p) for p in p53_pairs]
    shared = [p for p in p53 if p in set(p27)]
    idle = [p for p in p53 if p not in set(p27)]
    shared_q, idle_q = {q for p in shared for q in p}, {q for p in idle for q in p}
    L53, L27, Li = (t.splitlines(keepends=True) for t in (p53_text, p27_text, p53i_text))

    def of(lines, k):
        return [ln for ln in lines if _qasm_kind(ln) == k]

    g53, g27, gi = of(L53, "gate"), of(L27, "gate"), of(Li, "gate")
    m53, mi, m27 = of(L53, "measure"), of(Li, "measure"), of(L27, "measure")
    mixed = [ln.rstrip() for ln in g53 if qubits(ln) & shared_q and qubits(ln) & idle_q]
    cz = [ln for ln in gi if ln.strip().startswith("cz ")]
    cz_per_pair = Counter(tuple(sorted(qubits(ln))) for ln in cz)
    same_multiset, same_order = Counter(gi) == Counter(g27), gi == g27
    checks = {
        "1_every_remaining_gate_line_only_on_shared_qubits": all(qubits(ln) and qubits(ln) <= shared_q for ln in gi),
        "2_remaining_gate_lines_are_P53s_shared_lines_in_P53_order": gi == [ln for ln in g53 if qubits(ln) <= shared_q]
        and not mixed,
        "3_three_cz_per_shared_pair_81_in_all_none_elsewhere": len(cz) == 81
        and set(cz_per_pair) == {tuple(sorted(p)) for p in shared}
        and set(cz_per_pair.values()) == {3},
        "4_measurement_lines_byte_identical_to_P53": len(mi) == 106 and "".join(mi) == "".join(m53),
        "5_gate_lines_same_multiset_as_P27": same_multiset,
        "5_gate_lines_same_order_as_P27": same_order,
    }
    measured = {k: {q for x in m for q in qubits(x)} for k, m in (("P53i", mi), ("P27", m27))}
    return {
        "n_pairs_P27": len(p27),
        "n_pairs_P53": len(p53),
        "n_shared": len(shared),
        "n_idle": len(idle),
        "P27_pairs_all_in_P53": set(p27) <= set(p53),
        "idle_pairs": [list(p) for p in idle],
        "line_counts": {
            k: {"total": len(L), "gate": len(of(L, "gate")), "measure": len(of(L, "measure"))}
            for k, L in (("P53", L53), ("P27", L27), ("P53i", Li))
        },
        "P53_gate_lines_touching_shared_and_idle_qubits": mixed,
        "non_gate_lines_identical_to_P53": [x for x in L53 if _qasm_kind(x) != "gate"]
        == [x for x in Li if _qasm_kind(x) != "gate"],
        "P53i_is_P53_minus_idle_gate_lines": Li
        == [ln for ln in L53 if not (_qasm_kind(ln) == "gate" and qubits(ln) & idle_q)],
        "how_P53i_differs_from_P27": {
            "gate_lines": "identical in content and order"
            if same_order
            else ("same multiset, different order" if same_multiset else "different"),
            "declaration": [next(x.strip() for x in L if _qasm_kind(x) == "decl") for L in (Li, L27)],
            "header_same": of(Li, "header") == of(L27, "header"),
            "measured_qubits": {k: len(v) for k, v in measured.items()},
            "extra_measured_qubits_in_P53i": sorted(measured["P53i"] - measured["P27"]),
        },
        "checks": checks,
        "all_five_pass": all(checks.values()),
    }


def footprint_or_activity(rec: dict, k37: dict | None = None, main34b: dict | None = None) -> dict:
    """Kickoff 38, recomputed from its archived counts and task times. Like placement_or_drift, this recomputes one
    archived run's own rule; it is not a public verdict and has no command.

    Four tasks in one wave: T1 = P53i, T2 = P27, T3 = P53, T4 = P53i. Level L = P(11) per pair per task, in Kickoff
    34b's classical-index reading. On the 27 P27 pairs (T1, T3 and T4 restricted to them): c = r(T1, T4), the control;
    d = r(T2, T3), the difference to explain; f = r(mean of T1 and T4, T3); a = r(mean of T1 and T4, T2). The rule is
    activity_rule, on Pearson, with the Spearman reading beside it.

    Outside the verdict: the spread of each task's levels; the idle pairs of P53i (which run no gates); Kickoff 34b's
    five low pairs (those below its dead-pair floor, given its main job); the direction leans; and, given Kickoff 37's
    record, T2 against the mean of 37's four P27 tasks and T3 against the mean of its two P53 tasks."""
    prog = {t["label"]: t["program"] for t in rec["meta"]["tasks"]}
    n_of = {k: v["n_pairs"] for k, v in rec["programs"].items()}
    L = {t: p11_classical_index(rec["counts"][t], n_of[p]) for t, p in prog.items()}
    p27 = [tuple(p) for p in rec["programs"]["P27"]["pairs"]]
    p53 = [tuple(p) for p in rec["programs"]["P53"]["pairs"]]
    idx = [p53.index(p) for p in p27]
    idle = [i for i in range(len(p53)) if i not in idx]
    T1, T2, T3, T4 = L["T1"][idx], L["T2"], L["T3"][idx], L["T4"][idx]
    mi = (T1 + T4) / 2
    m = {"c": _corr_n(T1, T4), "d": _corr_n(T2, T3), "f": _corr_n(mi, T3), "a": _corr_n(mi, T2)}
    v, cond = activity_rule(*(m[k]["pearson"] for k in "cdfa"))
    vs, conds = activity_rule(*(m[k]["spearman"] for k in "cdfa"))
    shots = rec["meta"]["shots_per_task"]

    def shot_sd(x):
        return float(np.mean(np.sqrt(x * (1 - x) / shots)))

    spread = {}
    for t in ("T1", "T2", "T3", "T4"):
        on27 = L[t] if prog[t] == "P27" else L[t][idx]
        spread[t] = {
            "program": prog[t],
            "mean_L_on_27": float(on27.mean()),
            "between_pair_sd_on_27": float(on27.std(ddof=1)),
            "shot_noise_sd_on_27": shot_sd(on27),
        }
        if prog[t] != "P27":
            spread[t].update(
                {
                    "mean_L_all_53": float(L[t].mean()),
                    "between_pair_sd_all_53": float(L[t].std(ddof=1)),
                    "shot_noise_sd_all_53": shot_sd(L[t]),
                }
            )
    done = {t["label"]: t["completed_utc"] for t in rec["meta"]["tasks"]}
    span = max(map(_utc_seconds, done.values())) - min(map(_utc_seconds, done.values()))
    timing = {
        "completion_order": [t for t, _ in sorted(done.items(), key=lambda kv: (kv[1], kv[0]))],
        "completion_span_minutes": span / 60,
        "span_over_3_hours": span > 3 * 3600,
    }
    idle_lv: dict = {
        t: {
            "mean": float(L[t][idle].mean()),
            "max": float(L[t][idle].max()),
            "max_pair": list(p53[idle[int(np.argmax(L[t][idle]))]]),
            "above_0.2": [[list(p53[i]), float(L[t][i])] for i in idle if L[t][i] > 0.2],
        }
        for t in ("T1", "T4")
    }
    idle_lv["T1_T4_pooled_mean"] = float(np.mean([L["T1"][idle], L["T4"][idle]]))
    mi53 = (L["T1"] + L["T4"]) / 2
    desc: dict = {"idle_pairs_P53i": idle_lv}
    if main34b is not None:
        P = np.array([p11_classical_index(c, len(main34b["pairs"])) for c in main34b["counts"]])
        a_no = P[[i for i, lab in enumerate(main34b["order"]) if lab == "A no"]].mean(axis=0)
        low = [tuple(main34b["pairs"][i]) for i in range(len(a_no)) if a_no[i] < main34b["meta"]["dead_pair_floor"]]
        five = {
            f"{a}-{b}": {
                "T1_P53i": float(L["T1"][p53.index((a, b))]),
                "T2_P27": float(L["T2"][p27.index((a, b))]),
                "T3_P53": float(L["T3"][p53.index((a, b))]),
                "T4_P53i": float(L["T4"][p53.index((a, b))]),
                "mean_T1_T4": float(mi53[p53.index((a, b))]),
            }
            for a, b in low
        }
        desc["five_P27_low_pairs"] = five
        desc["five_low_count"] = {
            "T1_ge_0.6": sum(x["T1_P53i"] >= 0.6 for x in five.values()),
            "T4_ge_0.6": sum(x["T4_P53i"] >= 0.6 for x in five.values()),
            "mean_T1_T4_ge_0.6": sum(x["mean_T1_T4"] >= 0.6 for x in five.values()),
        }
    desc["direction"] = {
        "mean_T3_minus_meanT1T4_on_27": float(np.mean(T3 - mi)),
        "mean_meanT1T4_minus_T2_on_27": float(np.mean(mi - T2)),
    }
    if k37 is not None:
        r37 = placement_or_drift(k37)["per_task_P11"]
        ref27 = np.mean([r37[k] for k in ("wave1-T1", "wave1-T3", "wave2-T1", "wave2-T3")], axis=0)
        ref53 = np.mean([r37[k] for k in ("wave1-T2", "wave2-T2")], axis=0)
        desc["against_37"] = {
            "r_T2_vs_37_mean_P27": _corr_n(L["T2"], ref27),
            "mean_T2_minus_37_P27": float(np.mean(L["T2"] - ref27)),
            "r_T3_vs_37_mean_P53_all_53": _corr_n(L["T3"], ref53),
            "r_T3_vs_37_mean_P53_on_27": _corr_n(L["T3"][idx], ref53[idx]),
            "mean_T3_minus_37_P53": float(np.mean(L["T3"] - ref53)),
        }
    return {
        "per_task_P11": {t: L[t].tolist() for t in L},
        "shared_index_in_P53": idx,
        "idle_index_in_P53": idle,
        "counts_meta": {
            t: {
                "program": prog[t],
                "shots": sum(rec["counts"][t].values()),
                "distinct_keys": len(rec["counts"][t]),
                "key_width": 2 * n_of[prog[t]],
            }
            for t in prog
        },
        "spread": spread,
        "measures": m,
        "verdict": {
            "on_pearson": v,
            "conditions": cond,
            "spearman_reading_beside": vs,
            "spearman_conditions": conds,
            "readings": {k: ACTIVITY_READINGS[k] for k in (v, vs)},
        },
        "timing": timing,
        "descriptive": desc,
    }


# --------------------------------------------------------------------------- Amazon Braket, pinned: Kickoffs 40 to 42
BRAKET_HALVES = {"A": ([1, 2, 15, 16], [7, 8, 9, 10]), "B": ([3, 4, 13, 14], [5, 6, 11, 12])}
#: The verdict set needs at least this many working pairs with a published x; otherwise the map rule is capped
BRAKET_MIN_PAIRS = 20


def braket_outcomes(counts: dict[str, int], measured_qubits, pairs) -> np.ndarray:
    """Per pair, the counts of the four outcomes s = q0 + 2 q1 (q0 the pair's first qubit), in the Amazon Braket
    reading: character j of a counts key belongs to measured_qubits[j]."""
    col = {int(q): j for j, q in enumerate(measured_qubits)}
    out = np.zeros((len(pairs), 4))
    for key, m in counts.items():
        for i, (a, b) in enumerate(pairs):
            out[i, int(key[col[a]]) + 2 * int(key[col[b]])] += m
    return out


def braket_p11(counts, measured_qubits, pairs) -> np.ndarray:
    o = braket_outcomes(counts, measured_qubits, pairs)
    return o[:, 3] / o.sum(axis=1)


def braket_covariance(counts, measured_qubits, pairs) -> np.ndarray:
    """Per pair, P(11) - P(q0 = 1) P(q1 = 1): the bit-order check (above zero on average when the reading is right)."""
    o = braket_outcomes(counts, measured_qubits, pairs)
    p = o / o.sum(axis=1, keepdims=True)
    return p[:, 3] - (p[:, 1] + p[:, 3]) * (p[:, 2] + p[:, 3])


def braket_cz_wanted(label: str) -> int:
    """CZ per pair a program should carry: 0 for a readout calibration, 9 for a random circuit, 3 otherwise."""
    return 0 if label.startswith("CAL") else (9 if label.startswith("R") else 3)


def compiled_record(text: str | None, pairs, cz_wanted: int) -> dict:
    """Does a compiled program, as Amazon Braket returned it, run every pair on its named qubits? The qubits a pair ran
    on are the qubits its gates act on in the compiled program (Kickoff 40, Amendment A1.1): CZ per named pair, gates
    and measurements elsewhere, and the measured qubits. No program, or one that cannot be read, has no record."""
    import re
    from collections import Counter

    if not text:
        return {"present": False, "why": "no compiled program returned"}
    cz_re = re.compile(r"^\s*CZ\s+(\d+)\s+(\d+)\s*$", re.I)
    one_re = re.compile(r"^\s*(RX|RZ)\(([^)]*)\)\s+(\d+)\s*$", re.I)
    meas_re = re.compile(r"^\s*MEASURE\s+(\d+)\s+\w+\[(\d+)\]\s*$", re.I)
    cz, oneq, meas, other = [], [], {}, []
    for ln in text.splitlines():
        if m := cz_re.match(ln):
            cz.append(tuple(sorted((int(m.group(1)), int(m.group(2))))))
        elif m := one_re.match(ln):
            oneq.append(int(m.group(3)))
        elif m := meas_re.match(ln):
            meas[int(m.group(1))] = int(m.group(2))
        elif ln.strip():
            other.append(ln.strip())
    if not cz and not oneq and not meas:
        return {"present": False, "why": "unreadable: no gate or measurement line recognised"}
    named = {tuple(sorted(p)) for p in pairs}
    in_pairs = {q for p in pairs for q in p}
    czc = Counter(cz)
    used = {q for e in cz for q in e} | set(oneq) | set(meas)
    placed = used <= in_pairs and set(meas) == in_pairs
    if cz_wanted:
        matches = bool(czc) and set(czc) <= named and all(czc.get(p, 0) == cz_wanted for p in named) and placed
    else:
        matches = placed
    return {
        "present": True,
        "n_lines": len(text.splitlines()),
        "cz_total": len(cz),
        "cz_per_named_pair": sorted({czc.get(p, 0) for p in named}),
        "cz_wanted": cz_wanted,
        "cz_on_unnamed_edges": sorted([list(e) for e in czc if e not in named]),
        "qubits_used_outside_names": sorted(used - in_pairs),
        "named_qubits_unused": sorted(in_pairs - used),
        "measured_qubits_equal_names": set(meas) == in_pairs,
        "other_line_kinds": sorted({ln.split()[0].split("(")[0].upper() for ln in other})[:20],
        "matches_names": matches,
    }


def _with_n(tree, n: int):
    """Every correlation in a result (a dict with pearson and spearman) with its number of pairs beside it."""
    if isinstance(tree, dict):
        if set(tree) == {"pearson", "spearman"}:
            return {**tree, "n": n}
        return {k: _with_n(v, n) for k, v in tree.items()}
    return tree


def braket_placement(rec: dict, compiled: dict | None = None, k37: dict | None = None) -> dict:
    """Kickoff 40's stage 1, recomputed from its counts and compiled programs: X (all 27 pairs) twice, Y and Y' (the
    halves) once each, circuit A without the offset. c = r(X1, X4), the control; d = r(mean of the two X, the halves
    put together); the records check on each task's compiled program; the reading, by the rule fixed before the run
    (NOT SETTLED (unstable) if c < 0.7; MOVED if the records are present and do not match the names; PINNED if they
    match, or are absent, and d >= 0.7; CROWDING if they match and d < 0.4; MIXED otherwise). Outside the reading,
    given Kickoff 37's record: the X levels against its 27-pair and 53-pair programs' levels on the same named pairs."""
    pairs = [tuple(p) for p in rec["pairs"]]
    sets = {k: [tuple(p) for p in v] for k, v in rec["task_pairs"].items()}
    tasks = {t["task_label"]: t for t in rec["tasks"]}
    P = {tl: dict(zip(sets[tl], braket_p11(rec["counts"][tl], tasks[tl]["measured_qubits"], sets[tl]))) for tl in tasks}
    x1, x4 = np.array([P["T1-X"][p] for p in pairs]), np.array([P["T4-X"][p] for p in pairs])
    halves = {**P["T2-Y"], **P["T3-Yp"]}
    y = np.array([halves[p] for p in pairs])
    xm = (x1 + x4) / 2
    c, d = _corr_n(x1, x4), _corr_n(xm, y)
    records = {}
    if compiled is not None:
        records = {
            tl: compiled_record(compiled.get(tl), sets[tl], braket_cz_wanted(tasks[tl]["label"])) for tl in tasks
        }
    present = bool(records) and all(r["present"] for r in records.values())
    match = all(r.get("matches_names") for r in records.values()) if present else None
    if c["pearson"] < PLACEMENT_HIGH:
        reading = "NOT SETTLED (unstable)"
    elif present and not match:
        reading = "MOVED"
    elif (match or not present) and d["pearson"] >= PLACEMENT_HIGH:
        reading = "PINNED"
    elif match and d["pearson"] < PLACEMENT_LOW:
        reading = "CROWDING"
    else:
        reading = "MIXED"
    out = {
        "pairs": [list(p) for p in pairs],
        "P11": {tl: [P[tl][p] for p in sets[tl]] for tl in tasks},
        "X_mean_T1_T4": xm.tolist(),
        "Y_union_Yp": y.tolist(),
        "c": c,
        "d": d,
        "records": records,
        "records_present": present,
        "records_match_names": match,
        "reading": reading,
        "bit_order_check_mean_pair_covariance": {
            tl: float(braket_covariance(rec["counts"][tl], tasks[tl]["measured_qubits"], sets[tl]).mean())
            for tl in tasks
        },
        "means": {"X_T1": float(x1.mean()), "X_T4": float(x4.mean()), "Y_union_Yp": float(y.mean())},
    }
    if k37 is not None:
        r37 = placement_or_drift(k37)["per_task_P11"]
        p27 = [tuple(p) for p in k37["programs"]["P27"]["pairs"]]
        p53 = [tuple(p) for p in k37["programs"]["P53"]["pairs"]]
        l27 = dict(zip(p27, np.mean([r37[k] for k in ("wave1-T1", "wave1-T3", "wave2-T1", "wave2-T3")], axis=0)))
        l53 = dict(zip(p53, np.mean([r37[k] for k in ("wave1-T2", "wave2-T2")], axis=0)))
        a27, a53 = np.array([l27[p] for p in pairs]), np.array([l53[p] for p in pairs])
        out["descriptive_outside_reading"] = {
            "r_X_vs_k37_27pair_program": _corr_n(xm, a27),
            "r_X_vs_k37_53pair_program": _corr_n(xm, a53),
            "k37_27pair_levels": a27.tolist(),
            "k37_53pair_levels_on_27": a53.tolist(),
        }
    return out


def _braket_figures(figures: dict, pairs) -> dict:
    """Per pair: x (None for Braket's placeholder), the CZ error and the sum of both readout errors."""
    from .layout import published_score_braket

    out = {}
    for f in figures["figures_at_submission"]:
        out[tuple(f["pair"])] = {
            "x": published_score_braket(f["cz_fidelity"], *f["readout_fidelity"]),
            "cz_error": 1 - f["cz_fidelity"],
            "readout_error_sum": 2 - sum(f["readout_fidelity"]),
        }
    return {p: out[p] for p in pairs}


def braket_figures_check(figures: dict, pairs=None) -> dict:
    """Braket's figures for the run's pairs, read back: per pair, x by published_score_braket (None for the
    placeholder) and whether the CZ figure is the placeholder; how many of the pairs carry it, and which."""
    from .layout import BRAKET_CZ_PLACEHOLDER, published_score_braket

    rows = figures["figures_at_submission"] if "figures_at_submission" in figures else figures
    hit = [f["pair"] for f in rows if f["cz_fidelity"] == BRAKET_CZ_PLACEHOLDER]
    return {
        "per_pair": [
            {
                "x": published_score_braket(f["cz_fidelity"], *f["readout_fidelity"]),
                "cz_error": None if f["cz_fidelity"] == BRAKET_CZ_PLACEHOLDER else 1 - f["cz_fidelity"],
                "readout_error": [1 - r for r in f["readout_fidelity"]],
                "cz_figure_is_placeholder_0p5": f["cz_fidelity"] == BRAKET_CZ_PLACEHOLDER,
            }
            for f in rows
        ],
        "n_with_x": sum(f["cz_fidelity"] != BRAKET_CZ_PLACEHOLDER for f in rows),
        "in_our_set": len(hit),
        "our_pairs_hit": hit,
    }


def braket_map(
    rec: dict, figures: dict, compiled: dict | None = None, main34b: dict | None = None, stage1=None
) -> dict:
    """Kickoff 40's stage 2 (and Kickoff 41's Part A), recomputed from the counts: the bit-order check, the dead-pair
    filter (mean P(A no) below 0.5), Kickoff 31's statistics on every working pair, and the map rule on the verdict set:
    the working pairs with a published x, if at least 20 (else the rule is capped at MAP PRESENT on all working
    pairs). The sealed leave-one-out drops the verdict set's pair farthest from its mean k_A. Outside the verdict:
    given Kickoff 34b's main job, r(k_A) on the working pairs shared with it; given stage 1's recompute, its X levels
    against this run's mean P(A no); the prior map for a payoff (k_A and L on every working pair); and the records
    check on each compiled program. The flagged block names the pairs Braket gives a placeholder for."""
    from .layout import vendor_flag

    pairs = [tuple(p) for p in rec["pairs"]]
    order, seed = rec["order"], rec["meta"]["permutation_seed"]
    shots = rec["tasks"][0]["shots"]
    halves = {k: tuple(v) for k, v in rec["halves"].items()} if "halves" in rec else BRAKET_HALVES
    tasks = rec["tasks"]
    P = p11_table(rec)
    cov = float(
        np.mean(
            [
                braket_covariance(c, t["measured_qubits"], pairs).mean()
                for c, t, lab in zip(rec["counts"], tasks, order)
                if lab == "B no"
            ]
        )
    )
    a_no = np.mean([P[i] for i, lab in enumerate(order) if lab == "A no"], axis=0)
    floor = rec["meta"]["dead_pair_floor"]
    keep = [i for i in range(len(pairs)) if a_no[i] >= floor]
    fig = _braket_figures(figures, pairs)
    raw = {tuple(f["pair"]): f for f in figures["figures_at_submission"]}
    with_x = [i for i in keep if fig[pairs[i]]["x"] is not None]
    out: dict = {
        "pairs": [list(p) for p in pairs],
        "order": list(order),
        "per_circuit_P11": P.tolist(),
        "bit_order_check": {"mean_pair_covariance_B_no": cov, "passes": cov > 0},
        "dead_pair_filter": {
            "threshold": floor,
            "mean_P11_A_no": a_no.tolist(),
            "excluded": [
                {"pair": list(pairs[i]), "mean_P11_A_no": float(a_no[i])} for i in range(len(pairs)) if i not in keep
            ],
            "working_pairs": [list(pairs[i]) for i in keep],
        },
        "n_working": len(keep),
        "n_working_with_x": len(with_x),
        "working_without_x": [list(pairs[i]) for i in keep if i not in with_x],
    }
    kw = {"shots": shots, "seed": seed, "halves": halves}
    flags = [vendor_flag(cz_fidelity=raw[pairs[i]]["cz_fidelity"]) for i in keep]
    allw = analyse_map(P[:, keep], order, flagged=flags, **kw)
    out["all_working"] = _with_n(allw, len(keep))
    capped = len(with_x) < BRAKET_MIN_PAIRS
    vset = keep if capped else with_x

    def stats_on(idx):
        if capped:
            return analyse_map(P[:, idx], order, **kw)
        return analyse_map(
            P[:, idx],
            order,
            x=[fig[pairs[i]]["x"] for i in idx],
            cz_error=[fig[pairs[i]]["cz_error"] for i in idx],
            readout_error=[fig[pairs[i]]["readout_error_sum"] for i in idx],
            **kw,
        )

    s = stats_on(vset)
    out["verdict_set"] = {
        "pairs": [list(pairs[i]) for i in vset],
        "capped_at_MAP_PRESENT": capped,
        "definition": "all working pairs (fewer than 20 have x)" if capped else "working pairs with x",
    }
    out["verdict_stats"] = _with_n(s, len(vset))
    out["verdict"] = s["verdict"]["verdict"]
    kA = np.array(s["kA"])
    drop = int(np.argmax(np.abs(kA - kA.mean())))
    v2 = [k for j, k in enumerate(vset) if j != drop]
    s2 = _with_n(stats_on(v2), len(v2))
    out["leave_one_out"] = {
        "dropped_pair": list(pairs[vset[drop]]),
        "r_split_A": s2["S1"]["r_split_A"],
        "r_AB": s2["S2"]["r_AB"],
        "p_AB": s2["S2"]["p_one_sided"],
        "S3": s2["S3"] if isinstance(s2["S3"], dict) else None,
        "verdict_rule_applied": s2["verdict"]["verdict"],
    }
    desc: dict = {}
    if main34b is not None:
        r34 = rigetti_map(main34b)
        k34 = dict(zip(r34["working_pairs"], r34["analysis"]["kA"]))
        kall = dict(zip([pairs[i] for i in keep], allw["kA"]))
        shared = [p for p in kall if p in k34]
        desc["r_kA_vs_34b_kA_shared_working"] = _corr_n([kall[p] for p in shared], [k34[p] for p in shared])
        desc["shared_pairs"] = [list(p) for p in shared]
    if stage1 is not None:
        x1 = dict(zip([tuple(p) for p in stage1["pairs"]], stage1["X_mean_T1_T4"]))
        desc["r_stage1_X_vs_stage2_A_no_all27"] = _corr_n([x1[p] for p in pairs], a_no)
    out["descriptive"] = desc
    out["k_prior_for_stage3"] = {
        "pairs": [list(pairs[i]) for i in keep],
        "kA": allw["kA"],
        "L": (a_no[keep] / CIRCUITS["A"].ideal_no).tolist(),
    }
    if compiled is not None:
        out["records"] = {
            t["task_label"]: compiled_record(compiled.get(t["task_label"]), pairs, braket_cz_wanted(t["label"]))
            for t in tasks
        }
    return out


def braket_map_without(analysis: dict, rec: dict, figures: dict, drop) -> dict:
    """The map rule's statistics on a recomputed verdict set without the given pairs (an after-the-fact check)."""
    pairs = [tuple(p) for p in rec["pairs"]]
    P = np.asarray(analysis["per_circuit_P11"])
    fig = _braket_figures(figures, pairs)
    drop = {tuple(p) for p in drop}
    idx = [pairs.index(tuple(p)) for p in analysis["verdict_set"]["pairs"] if tuple(p) not in drop]
    halves = {k: tuple(v) for k, v in rec["halves"].items()}
    s = analyse_map(
        P[:, idx],
        rec["order"],
        x=[fig[pairs[i]]["x"] for i in idx],
        shots=rec["tasks"][0]["shots"],
        seed=rec["meta"]["permutation_seed"],
        halves=halves,
    )
    return _with_n(s, len(idx))


def braket_payoff(rec: dict, figures: dict, k_prior: dict, ideal_R: list, compiled: dict | None = None) -> dict:
    """Kickoff 40's stage 3 (and Kickoff 41's Part B), recomputed from the counts: Kickoff 33's payoff analysis on the
    set S of the run's pairs that have a published x (Amendment A1.2). k_prior: {"pairs", "kA", "L"}, the prior map
    on every working pair. W and W_rc per pair from the counts and the ideal distributions; the correlations, picks
    and gains on S (permutation and bootstrap seed 40); the relative error reduction beside each gain; the verdict by
    Kickoff 33's rule. The interval that also resamples shots (outside the verdict) is drawn as the run drew it: for
    each pick, only the pairs in that pick or the x pick, from numpy default_rng(seed + 1000)."""
    from .verdicts import analyse_payoff
    from .workload import aggregate, hellinger_fidelity, readout_confusion, workload_scores

    pairs = [tuple(p) for p in rec["pairs"]]
    n = len(pairs)
    tasks = rec["tasks"]
    seed = rec["meta"]["seed"]
    outcomes = [braket_outcomes(c, t["measured_qubits"], pairs) for c, t in zip(rec["counts"], tasks)]
    agg = aggregate(outcomes, rec["order"])
    M = readout_confusion(agg)
    ideal = [np.asarray(r["ideal"], float) for r in ideal_R]
    ws = workload_scores(agg, ideal, M)
    W_c, Wrc_c = ws["W_per_circuit"], ws["W_rc_per_circuit"]
    pno = agg["A no"][:, 3] / agg["A no"].sum(axis=1)
    poff = agg["A off"][:, 3] / agg["A off"].sum(axis=1)
    k_now, L_now = (poff - pno) / GAP["A"], pno / CIRCUITS["A"].ideal_no
    kpd = dict(zip(map(tuple, k_prior["pairs"]), k_prior["kA"]))
    Lpd = dict(zip(map(tuple, k_prior["pairs"]), k_prior["L"]))
    kp, Lp = np.array([kpd[p] for p in pairs]), np.array([Lpd[p] for p in pairs])
    fig = _braket_figures(figures, pairs)
    S = [i for i in range(n) if fig[pairs[i]]["x"] is not None]
    x = np.array([fig[pairs[i]]["x"] for i in S])
    an = analyse_payoff(
        W_c[S],
        kp[S],
        x,
        L_prior=Lp[S],
        k_now=k_now[S],
        L_now=L_now[S],
        W_rc_per_circuit=Wrc_c[S],
        seed=seed,
    )
    picks = {k: [S[i] for i in v] for k, v in an["picks"].items()}
    W = W_c.mean(axis=1)
    p_id = [np.asarray(r["ideal"], float) for r in ideal_R]
    ns, Q = ws["shots"], ws["measured_dists"]
    gains = {}
    for sel, g in an["gains"].items():
        rng2 = np.random.default_rng(seed + 1000)
        boots2 = []
        for _ in range(2000):
            jj = rng2.integers(0, W_c.shape[1], W_c.shape[1])
            Wb = np.zeros(n)
            for i in set(picks[sel]) | set(picks["x"]):
                Wb[i] = np.mean(
                    [hellinger_fidelity(p_id[j], rng2.multinomial(int(ns[i, j]), Q[i, j]) / ns[i, j]) for j in jj]
                )
            boots2.append(Wb[picks[sel]].mean() - Wb[picks["x"]].mean())
        ek, ex = float((1 - W[picks[sel]]).mean()), float((1 - W[picks["x"]]).mean())
        gains[sel] = {
            "G": g["G"],
            "ci90": g["ci90"],
            "ci90_circuits_and_shots_not_in_verdict": [
                float(np.percentile(boots2, 5)),
                float(np.percentile(boots2, 95)),
            ],
            "overlap_with_x_pick": g["overlap_with_x_pick"],
            "mean_error_pick": ek,
            "mean_error_x_pick": ex,
            "relative_error_reduction": 1 - ek / ex,
        }
    out = {
        "pairs": [list(p) for p in pairs],
        "set_S_with_x": [list(pairs[i]) for i in S],
        "pairs_without_x": [list(pairs[i]) for i in range(n) if i not in S],
        "W": W.tolist(),
        "W_rc": Wrc_c.mean(axis=1).tolist(),
        "W_per_circuit": W_c.tolist(),
        "W_rc_per_circuit": Wrc_c.tolist(),
        "measured_dists": np.asarray(Q).tolist(),
        "readout_confusion": M.tolist(),
        "k_now": k_now.tolist(),
        "L_now": L_now.tolist(),
        "k_prior": kp.tolist(),
        "L_prior": Lp.tolist(),
        "x_on_S": x.tolist(),
        "mean_W": float(W.mean()),
        "mean_W_rc": float(Wrc_c.mean()),
        "mean_W_on_S": float(W[S].mean()),
        "correlations_on_S": _with_n(an["correlations"], len(S)),
        "picks": {k: [list(pairs[i]) for i in v] for k, v in picks.items()},
        "gains": gains,
        "level_beats_k": an["level_beats_k"],
        "verdict": an["verdict"]["verdict"],
        "verdict_detail": an["verdict"],
    }
    if compiled is not None:
        out["records"] = {
            t["task_label"]: compiled_record(compiled.get(t["task_label"]), pairs, braket_cz_wanted(t["label"]))
            for t in tasks
        }
    return out


# --------------------------------------------------------------------------- Kickoff 41: the pinned map, a day later
#: Kickoff 41's two extreme pairs (k_A below -2 on 6 October) and its persistence rule's thresholds, fixed beforehand
K41_EXTREMES = [(42, 43), (94, 95)]
PERSIST_PINNED = {"reliable": 0.5, "min_pairs": 18, "holds": 0.5, "p": 0.05, "extremes": 0.3, "fades": 0.2}


def pinned_map_rule(rel_today, rel_before, n_both, p_k, p_k_p, p_k_prime) -> str:
    """Kickoff 41's persistence rule. NOT SETTLED (too noisy) if either day's r_split(k_A) is below 0.5 or fewer than
    18 pairs work on both days; HOLDS if p_k >= 0.5 with p < 0.05 and p_k' >= 0.3; HOLDS (carried by the extremes) if
    p_k' < 0.3; FADES if p_k < 0.2; PARTIAL otherwise."""
    t = PERSIST_PINNED
    if rel_today is None or rel_today < t["reliable"] or rel_before < t["reliable"] or n_both < t["min_pairs"]:
        return "NOT SETTLED (too noisy)"
    if p_k >= t["holds"] and p_k_p < t["p"]:
        return "HOLDS" if p_k_prime >= t["extremes"] else "HOLDS (carried by the extremes)"
    if p_k < t["fades"]:
        return "FADES"
    return "PARTIAL"


def pinned_map_persistence(
    today: dict, before: dict, figures_today: dict, figures_before: dict, pairs, seed: int = 41
) -> dict:
    """Kickoff 41's Part A against Kickoff 40's stage 2: a recompute for this archived pair of runs, not a public
    verdict and not a command. today, before: braket_map's recompute of each day. On P_both, the pairs working on both
    days: p_k = r(k_A today, k_A before), with its one-sided permutation p (seed 41); p_k' the same without 42-43 and
    94-95; p_L = r(mean P(A no) today, before) on all pairs. The rule is pinned_map_rule, with each day's r_split(k_A)
    on its verdict set as the reliability. Beside it: p_k corrected by both days' full-length reliabilities, the two
    extreme pairs today, whether Kickoff 40's dead pairs are dead today, and r(x today, x before)."""
    pairs = [tuple(p) for p in pairs]
    kb = dict(zip(map(tuple, before["dead_pair_filter"]["working_pairs"]), before["all_working"]["kA"]))
    kt = dict(zip(map(tuple, today["dead_pair_filter"]["working_pairs"]), today["all_working"]["kA"]))
    both = [p for p in pairs if p in kb and p in kt]
    a, b = np.array([kt[p] for p in both]), np.array([kb[p] for p in both])
    pk = {"r": _corr_n(a, b), "p_one_sided": stats.permutation_p(a, b, seed, True), "pairs": [list(p) for p in both]}
    both2 = [p for p in both if p not in K41_EXTREMES]
    pk2 = {"r": _corr_n([kt[p] for p in both2], [kb[p] for p in both2]), "n": len(both2)}
    pL = _corr_n(today["dead_pair_filter"]["mean_P11_A_no"], before["dead_pair_filter"]["mean_P11_A_no"])
    rel_t = today["verdict_stats"]["S1"]["r_split_A"]["pearson"]
    rel_y = before["verdict_stats"]["S1"]["r_split_A"]["pearson"]
    v = pinned_map_rule(rel_t, rel_y, len(both), pk["r"]["pearson"], pk["p_one_sided"], pk2["r"]["pearson"])
    full_t, full_y = stats.spearman_brown(rel_t), stats.spearman_brown(rel_y)
    xt = {tuple(f["pair"]): f for f in figures_today["figures_at_submission"]}
    xy = {tuple(f["pair"]): f for f in figures_before["figures_at_submission"]}
    from .layout import published_score_braket

    def x_of(f):
        return published_score_braket(f["cz_fidelity"], *f["readout_fidelity"])

    bx = [p for p in pairs if x_of(xy[p]) is not None and x_of(xt[p]) is not None]
    dead_before = [tuple(e["pair"]) for e in before["dead_pair_filter"]["excluded"]]
    dead_today = [tuple(e["pair"]) for e in today["dead_pair_filter"]["excluded"]]
    beside = {
        "disattenuated_p_k": float(pk["r"]["pearson"] / math.sqrt(full_t * full_y)),
        "reliability_full_length": {"today": full_t, "kickoff40": full_y},
        "extremes_today_kA": {f"{p[0]}-{p[1]}": kt.get(p) for p in K41_EXTREMES},
        "extremes_still_below_minus_2": {f"{p[0]}-{p[1]}": kt.get(p) is not None and kt[p] < -2 for p in K41_EXTREMES},
        "kickoff40_dead_still_dead": {f"{p[0]}-{p[1]}": p in dead_today for p in dead_before},
        "r_x_today_vs_yesterday": _corr_n([x_of(xt[p]) for p in bx], [x_of(xy[p]) for p in bx]),
        "n_x_both_days": len(bx),
    }
    return {
        "P_both": [list(p) for p in both],
        "p_k": pk,
        "p_k_prime": pk2,
        "p_L": pL,
        "reliabilities": {"today_r_split_kA": rel_t, "kickoff40_r_split_kA": rel_y},
        "verdict": v,
        "beside": beside,
    }


def _day_old_pick(W, W_c, S, score, x, seed: int = 41) -> dict:
    """Kickoff 41's payoff for one prior score on the pick set S: the partial r(W, score | x) with its one-sided
    permutation p; the top 8 by the score against the top 8 by x (lowest), ties to the earlier pair; G with its 90%
    bootstrap interval over circuits (10,000 draws); the verdict by Kickoff 33's rule. Seed 41 for both."""
    from .verdicts import payoff_verdict

    w, s = W[S], score[S]
    rw, rs = stats.residuals(w, x), stats.residuals(s, x)
    pr = float(stats.corr(rw, rs)["pearson"])
    pp = stats.permutation_p(rw, rs, seed, True)
    pk = [S[i] for i in np.argsort(-s, kind="stable")[:8]]
    px = [S[i] for i in np.argsort(x, kind="stable")[:8]]
    G, ci, _ = stats.bootstrap_gain_over_circuits(W_c, pk, px, seed, 10_000)
    ek, ex = float((1 - W[pk]).mean()), float((1 - W[px]).mean())
    return {
        "partial_r_given_x": pr,
        "p_one_sided": pp,
        "r_W_score": _corr_n(w, s),
        "pick": pk,
        "x_pick": px,
        "G": G,
        "ci90": ci,
        "overlap": len(set(pk) & set(px)),
        "relative_error_reduction": 1 - ek / ex,
        "verdict": payoff_verdict(pr, pp, ci).verdict,
    }


def day_old_payoff(
    rec: dict, figures: dict, before: dict, ideal_R: list, today: dict | None = None, compiled=None
) -> dict:
    """Kickoff 41's Part B, recomputed from its counts: W per pair on the 8 random circuits (one copy each), its
    readout-corrected form and its shot noise (delta method), scored against Kickoff 40's level (mean P(A no)) and
    kept share (k_A), each by _day_old_pick, on the pairs with a published x today. Given Part A's recompute, the same
    picks with today's level and kept share: the same-day ceiling."""
    from .layout import published_score_braket
    from .workload import aggregate, readout_confusion, workload_scores

    pairs = [tuple(p) for p in rec["pairs"]]
    n = len(pairs)
    outcomes = [braket_outcomes(c, t["measured_qubits"], pairs) for c, t in zip(rec["counts"], rec["tasks"])]
    agg = aggregate(outcomes, rec["order"])
    M = readout_confusion(agg)
    ideal = [np.asarray(r["ideal"], float) for r in ideal_R]
    ws = workload_scores(agg, ideal, M)
    W_c, Wrc_c = ws["W_per_circuit"], ws["W_rc_per_circuit"]
    W, Wrc = W_c.mean(axis=1), Wrc_c.mean(axis=1)
    shot_var = np.zeros((n, W_c.shape[1]))
    for j, p in enumerate(ideal):
        d = agg[f"R{j + 1}"]
        q = d / d.sum(axis=1, keepdims=True)
        for i in range(n):
            g = np.sqrt(np.clip(p, 0, None) / np.clip(q[i], 1e-12, None)) * np.sqrt(W_c[i, j])
            shot_var[i, j] = (np.sum(q[i] * g**2) - np.sum(q[i] * g) ** 2) / d[i].sum()
    sd_W = np.sqrt(shot_var.sum(axis=1) / W_c.shape[1] ** 2)
    p27 = [tuple(p) for p in before["dead_pair_filter"]["working_pairs"]]
    Lb = dict(zip(map(tuple, before["pairs"]), before["dead_pair_filter"]["mean_P11_A_no"]))
    kb = dict(zip(p27, before["all_working"]["kA"]))
    L_prior, k_prior = np.array([Lb[p] for p in pairs]), np.array([kb[p] for p in pairs])
    f = {tuple(r["pair"]): r for r in figures["figures_at_submission"]}
    xs = [published_score_braket(f[p]["cz_fidelity"], *f[p]["readout_fidelity"]) for p in pairs]
    S = [i for i in range(n) if xs[i] is not None]
    x = np.array([xs[i] for i in S])
    seed = rec["meta"]["seed"]
    L, K = _day_old_pick(W, W_c, S, L_prior, x, seed), _day_old_pick(W, W_c, S, k_prior, x, seed)

    def named(block):
        return {
            **block,
            "pick": [list(pairs[i]) for i in block["pick"]],
            "x_pick": [list(pairs[i]) for i in block["x_pick"]],
        }

    out = {
        "pairs": [list(p) for p in pairs],
        "pick_set": [list(pairs[i]) for i in S],
        "pairs_without_x": [list(pairs[i]) for i in range(n) if i not in S],
        "W": W.tolist(),
        "W_rc": Wrc.tolist(),
        "W_per_circuit": W_c.tolist(),
        "readout_confusion": M.tolist(),
        "shot_noise_sd_W": sd_W.tolist(),
        "median_shot_noise_sd_W": float(np.median(sd_W)),
        "L_prior": L_prior.tolist(),
        "k_prior": k_prior.tolist(),
        "x_on_pick_set": x.tolist(),
        "level": named(L),
        "kept_share": named(K),
        "r_W_x": _corr_n(W[S], x),
        "r_Wrc_L_prior": _corr_n(Wrc[S], L_prior[S]),
        "mean_W": float(W.mean()),
        "overlap_L_pick_k_pick": len(set(L["pick"]) & set(K["pick"])),
    }
    if today is not None:
        Lt = dict(zip(map(tuple, today["pairs"]), today["dead_pair_filter"]["mean_P11_A_no"]))
        kt = dict(zip(map(tuple, today["dead_pair_filter"]["working_pairs"]), today["all_working"]["kA"]))
        same = {"level": named(_day_old_pick(W, W_c, S, np.array([Lt[p] for p in pairs]), x, seed))}
        S2 = [i for i in S if pairs[i] in kt]
        if len(S2) >= 9:
            kk = np.array([kt.get(p, np.nan) for p in pairs])
            same["kept_share"] = named(_day_old_pick(W, W_c, S2, kk, np.array([xs[i] for i in S2]), seed))
        out["same_day"] = same
    if compiled is not None:
        out["records"] = {
            t["task_label"]: compiled_record(compiled.get(t["task_label"]), pairs, braket_cz_wanted(t["label"]))
            for t in rec["tasks"]
        }
    return out


# --------------------------------------------------------------------------- Kickoff 42: the offset scan
#: Kickoff 42's scan, fixed before the run: nine offsets per family around the designed peak, the delta grid, the seed,
#: the edge rule of its Amendment A1.1, the seven programs its A1.3 named from Day 1, and the pairs it watched
SCAN = {
    "A": {"peak": -0.5, "offsets": [-1.25, -1.0, -0.75, -0.5, -0.25, 0.0, 0.25, 0.5, 0.75]},
    "B": {"peak": -1.0, "offsets": [-1.75, -1.5, -1.25, -1.0, -0.75, -0.5, -0.25, 0.0, 0.25]},
}
SCAN_GRID = np.round(np.arange(-1.5, 1.5 + 1e-9, 0.005), 3)
SCAN_SEED, SCAN_PERMUTATIONS, SCAN_BOOT = 42, 10_000, 1000
SCAN_EDGE = 1.495
SCAN_SWITCH_HIGH = {("A", -1.25), ("A", -1.0), ("A", -0.75), ("A", 0.75), ("B", -1.75), ("B", -1.5), ("B", -1.25)}
SCAN_WATCH = [(94, 95), (42, 43), (18, 19)]
_SCAN_CURVES: dict = {}


def scan_ideal(family: str, a: float) -> float:
    """The exact P(11) of a family's circuit at offset a (no offset term at all when a is 0)."""
    from .circuits import unitary

    return float(abs(unitary(CIRCUITS[family].c, None if a == 0 else a)[3, 0]) ** 2)


def scan_curve(family: str) -> np.ndarray:
    """P_ideal(a - delta) for every delta of the grid (rows) and every scan offset a (columns)."""
    if family not in _SCAN_CURVES:
        offs, memo = SCAN[family]["offsets"], {}
        F = np.zeros((len(SCAN_GRID), len(offs)))
        for i, d in enumerate(SCAN_GRID):
            for j, a in enumerate(offs):
                key = round(a - d, 3)
                if key not in memo:
                    memo[key] = scan_ideal(family, key)
                F[i, j] = memo[key]
        _SCAN_CURVES[family] = F
    return _SCAN_CURVES[family]


def scan_fit(Y, family: str):
    """Fit each row of Y (P(11) at the nine offsets) by b + v P_ideal(a - delta): for every delta of the grid the least
    squares b and v, keeping the smallest residual with v > 0. Returns delta, v, b, the rms residual and whether a fit
    with v > 0 was found."""
    F = scan_curve(family)
    fm = F.mean(axis=1, keepdims=True)
    Fc = F - fm
    Y = np.atleast_2d(np.asarray(Y, float))
    ym = Y.mean(axis=1, keepdims=True)
    v = (Y - ym) @ Fc.T / (Fc**2).sum(axis=1)
    b = ym - v * fm.T
    res = ((Y[:, None, :] - (b[:, :, None] + v[:, :, None] * F[None, :, :])) ** 2).sum(axis=2)
    res = np.where(v > 0, res, np.inf)
    k = np.argmin(res, axis=1)
    i = np.arange(Y.shape[0])
    return SCAN_GRID[k], v[i, k], b[i, k], np.sqrt(res[i, k] / Y.shape[1]), np.isfinite(res[i, k])


def _scan_vertex(y, offs):
    j = int(np.argmax(y))
    lo = min(max(j - 2, 0), len(y) - 5)
    c2, c1, _ = np.polyfit(np.array(offs[lo : lo + 5]), np.array(y[lo : lo + 5]), 2)
    return float(-c1 / (2 * c2)) if c2 < 0 else None


def _scan_p(a, b, direction: str) -> float:
    """One-sided permutation p of Pearson r(a, b), seed 42: the share of shuffles with r >= the observed r
    ("greater") or r <= it ("less")."""
    from scipy.stats import pearsonr

    rng = np.random.default_rng(SCAN_SEED)
    r0 = pearsonr(a, b)[0]
    rs = np.array([pearsonr(a, rng.permutation(b))[0] for _ in range(SCAN_PERMUTATIONS)])
    return float(np.mean(rs >= r0)) if direction == "greater" else float(np.mean(rs <= r0))


def scan_levels(rec: dict) -> dict:
    """Per family, P(11) per pair (rows) at each scan offset (columns), from the counts."""
    pairs = [tuple(p) for p in rec["pairs"]]
    P = {f: np.zeros((len(pairs), len(SCAN[f]["offsets"]))) for f in SCAN}
    for t, c in zip(rec["tasks"], rec["counts"]):
        P[t["family"]][:, SCAN[t["family"]]["offsets"].index(t["offset"])] = braket_p11(c, t["measured_qubits"], pairs)
    return P


def scan_day(rec: dict, figures: dict, before: dict, compiled: dict | None = None) -> dict:
    """One day of Kickoff 42, recomputed from its counts: the per-pair fits with their bootstrap SD (1000 binomial
    redraws per pair and family, seed 42, A's pairs first), and V1 to V3 on the working pairs (peak P(11) on A at least
    0.5): V1, the spread of delta_A against its bootstrap noise; V2, delta_A against delta_B; V3, delta_A against
    Kickoff 40's k_A (before: braket_map's recompute of Kickoff 40's stage 2). Beside the verdicts: the watched pairs,
    |delta_A| against the CZ error, the share of fits within twice the shot noise, and the mean deltas."""
    pairs = [tuple(p) for p in rec["pairs"]]
    P = scan_levels(rec)
    shots = rec["tasks"][0]["shots"]
    rng = np.random.default_rng(SCAN_SEED)
    working = [i for i in range(len(pairs)) if P["A"][i].max() >= 0.5]
    per = {}
    for fam in ("A", "B"):
        Y, offs = P[fam], SCAN[fam]["offsets"]
        d, v, b, rms, ok = scan_fit(Y, fam)
        bsd = np.zeros(len(pairs))
        for i in range(len(pairs)):
            Yb = rng.binomial(shots, np.clip(Y[i], 0, 1), size=(SCAN_BOOT, len(offs))) / shots
            bsd[i] = scan_fit(Yb, fam)[0].std(ddof=1)
        vx = [_scan_vertex(Y[i], offs) for i in range(len(pairs))]
        per[fam] = {
            "delta": d.tolist(),
            "v": v.tolist(),
            "b": b.tolist(),
            "rms": rms.tolist(),
            "fit_found": ok.tolist(),
            "boot_sd": bsd.tolist(),
            "shot_sd_mean": np.sqrt(np.clip(Y * (1 - Y), 0, None) / shots).mean(axis=1).tolist(),
            "at_grid_edge": (np.abs(d) >= 1.5).tolist(),
            "vertex": vx,
            "vertex_shift": [None if x is None else x - SCAN[fam]["peak"] for x in vx],
            "peak_P11": Y.max(axis=1).tolist(),
        }
    W = working
    dA, dB = np.array(per["A"]["delta"])[W], np.array(per["B"]["delta"])[W]
    sdA, med = float(dA.std(ddof=1)), float(np.median(np.array(per["A"]["boot_sd"])[W]))
    v1 = "SPREAD" if sdA >= 2 * med else "NOT SETTLED (no spread)"
    r2, p2 = _corr_n(dA, dB), _scan_p(dA, dB, "greater")
    md = float(np.mean(np.abs(dA - dB)))
    if r2["pearson"] >= 0.6 and p2 < 0.05 and md < 0.25:
        v2 = "CONSISTENT SHIFT"
    else:
        v2 = "CIRCUIT-SPECIFIC" if r2["pearson"] < 0.3 else "MIXED"
    k40 = dict(zip(map(tuple, before["dead_pair_filter"]["working_pairs"]), before["all_working"]["kA"]))
    both = [i for i in W if pairs[i] in k40]
    dA3, kA3 = np.array(per["A"]["delta"])[both], np.array([k40[pairs[i]] for i in both])
    r3, p3 = _corr_n(dA3, kA3), _scan_p(dA3, kA3, "less")
    if r3["pearson"] <= -0.6 and p3 < 0.05:
        v3 = "EXPLAINS"
    else:
        v3 = "DOES NOT" if r3["pearson"] > -0.3 else "PARTLY"
    shape = float(np.mean([per[f]["rms"][i] <= 2 * per[f]["shot_sd_mean"][i] for f in ("A", "B") for i in W]))
    from .layout import published_score_braket

    fig = {tuple(f["pair"]): f for f in figures["figures_at_submission"]}
    withcz = [
        i
        for i in W
        if published_score_braket(fig[pairs[i]]["cz_fidelity"], *fig[pairs[i]]["readout_fidelity"]) is not None
    ]
    rcz = _corr_n(np.abs(np.array(per["A"]["delta"])[withcz]), [1 - fig[pairs[i]]["cz_fidelity"] for i in withcz])
    keys = ("delta", "v", "b", "rms", "boot_sd", "peak_P11", "vertex")
    watch = {
        f"{a}-{b}": {fam: {k: per[fam][k][pairs.index((a, b))] for k in keys} for fam in ("A", "B")}
        for a, b in SCAN_WATCH
    }
    out = {
        "pairs": [list(p) for p in pairs],
        "working": [list(pairs[i]) for i in W],
        "excluded": [
            {"pair": list(pairs[i]), "max_P11_A": float(P["A"][i].max())} for i in range(len(pairs)) if i not in W
        ],
        "P11": {f: P[f].tolist() for f in P},
        "offsets": {f: SCAN[f]["offsets"] for f in SCAN},
        "fits": per,
        "V1": {"sd_deltaA_across_working": sdA, "median_boot_sd_deltaA": med, "verdict": v1},
        "V2": {"r": r2, "p_one_sided": p2, "mean_abs_dA_minus_dB": md, "verdict": v2, "ruled": v1 == "SPREAD"},
        "V3": {
            "r_deltaA_vs_k40_kA": r3,
            "p_one_sided_negative": p3,
            "pairs": [list(pairs[i]) for i in both],
            "verdict": v3,
            "ruled": v1 == "SPREAD",
        },
        "beside": {
            "watch_pairs": watch,
            "r_abs_deltaA_vs_cz_error": rcz,
            "n_cz": len(withcz),
            "shape_fraction_rms_le_2_shot": shape,
            "mean_deltaA_working": float(dA.mean()),
            "mean_deltaB_working": float(dB.mean()),
        },
    }
    if compiled is not None:
        out["records"] = {
            t["task_label"]: compiled_record(compiled.get(t["task_label"]), pairs, braket_cz_wanted(t["family"]))
            for t in rec["tasks"]
        }
    return out


def scan_persistence(day1: dict, day2: dict, amended: bool) -> dict:
    """V4: does each pair's fitted shift repeat from Day 1 to Day 2, per family, on the pairs working both days?
    Amended (Kickoff 42, A1.1): pairs whose fit reached |delta| >= 1.495 on either day are left out, and a family with
    fewer than 15 left is NOT SETTLED (too few). HOLDS if both families have r >= 0.5 with one-sided p < 0.05; FADES if
    both have r < 0.2; PARTIAL otherwise; NOT SETTLED (too noisy) if Day 1's V1 was not SPREAD."""
    w = [tuple(p) for p in day1["working"] if p in day2["working"]]
    pairs = [tuple(p) for p in day1["pairs"]]
    out: dict = {
        "rule": "amended (A1.1)" if amended else "original rule",
        "pairs_working_both_days": [list(p) for p in w],
    }
    for fam in ("A", "B"):
        idx = [pairs.index(p) for p in w]
        left = []
        if amended:
            d1, d2 = day1["fits"][fam]["delta"], day2["fits"][fam]["delta"]
            left = [pairs[i] for i in idx if abs(d1[i]) >= SCAN_EDGE or abs(d2[i]) >= SCAN_EDGE]
            idx = [i for i in idx if pairs[i] not in left]
        a = np.array(day1["fits"][fam]["delta"])[idx]
        b = np.array(day2["fits"][fam]["delta"])[idx]
        out[fam] = {"n": len(idx), "left_out": [list(p) for p in left]}
        if amended and len(idx) < 15:
            out[fam]["status"] = "NOT SETTLED (too few)"
            continue
        out[fam].update({"r": _corr_n(a, b), "p_one_sided": _scan_p(a, b, "greater")})
    if day1["V1"]["verdict"] != "SPREAD":
        v = "NOT SETTLED (too noisy)"
    elif any("status" in out[f] for f in ("A", "B")):
        v = "NOT SETTLED (too few)"
    elif all(out[f]["r"]["pearson"] >= 0.5 and out[f]["p_one_sided"] < 0.05 for f in ("A", "B")):
        v = "HOLDS"
    elif all(out[f]["r"]["pearson"] < 0.2 for f in ("A", "B")):
        v = "FADES"
    else:
        v = "PARTIAL"
    out["verdict"] = v
    return out


def scan_fingerprints(day1: dict, day2: dict) -> dict:
    """V5 (Kickoff 42, A1.3): each pair's fingerprint is its 18 P(11) (A's nine offsets, then B's) minus its own mean.
    Pooled over the pairs working both days, r(Day 1, Day 2), with a one-sided permutation p that shuffles the program
    labels within each pair (10,000, seed 42); the per-pair r. HOLDS if r >= 0.5 with p < 0.05; FADES if r < 0.2;
    PARTIAL otherwise. The switch: for 11-12 and 72-73, mean P(11) on the seven programs named from Day 1 minus the
    other eleven; SWITCH REPEATS if both are at least 0.20 on Day 2, SWITCH GONE if both are below 0.05, MIXED
    otherwise. The theory is discredited if V5 FADES together with SWITCH GONE."""
    from scipy.stats import pearsonr

    pairs = [tuple(p) for p in day1["pairs"]]
    w = [pairs.index(tuple(p)) for p in day1["working"] if p in day2["working"]]
    progs = [(f, a) for f in ("A", "B") for a in SCAN[f]["offsets"]]
    X1 = np.hstack([np.array(day1["P11"][f]) for f in ("A", "B")])
    X2 = np.hstack([np.array(day2["P11"][f]) for f in ("A", "B")])
    F1 = X1[w] - X1[w].mean(axis=1, keepdims=True)
    F2 = X2[w] - X2[w].mean(axis=1, keepdims=True)
    r0 = pearsonr(F1.ravel(), F2.ravel())[0]
    rng = np.random.default_rng(SCAN_SEED)
    hits = 0
    for _ in range(SCAN_PERMUTATIONS):
        shuffled = np.array([row[rng.permutation(len(progs))] for row in F2])
        hits += pearsonr(F1.ravel(), shuffled.ravel())[0] >= r0
    p = hits / SCAN_PERMUTATIONS
    per = {f"{pairs[i][0]}-{pairs[i][1]}": float(pearsonr(F1[j], F2[j])[0]) for j, i in enumerate(w)}
    pF = _corr_n(F1.ravel(), F2.ravel())
    verdict = "HOLDS" if pF["pearson"] >= 0.5 and p < 0.05 else ("FADES" if pF["pearson"] < 0.2 else "PARTIAL")
    hi = [k for k, pg in enumerate(progs) if pg in SCAN_SWITCH_HIGH]
    lo = [k for k in range(len(progs)) if k not in hi]
    sw = {}
    for pr in [(11, 12), (72, 73)]:
        i = pairs.index(pr)
        sw[f"{pr[0]}-{pr[1]}"] = {
            "day2_high_minus_low": float(X2[i, hi].mean() - X2[i, lo].mean()),
            "day1_high_minus_low": float(X1[i, hi].mean() - X1[i, lo].mean()),
        }
    d = [x["day2_high_minus_low"] for x in sw.values()]
    sv = "SWITCH REPEATS" if all(x >= 0.20 for x in d) else ("SWITCH GONE" if all(x < 0.05 for x in d) else "MIXED")
    return {
        "pairs": [list(pairs[i]) for i in w],
        "p_F": pF,
        "p_one_sided": p,
        "per_pair_r": per,
        "median_per_pair_r": float(np.median(list(per.values()))),
        "verdict": verdict,
        "switch": {"high_programs": sorted(f"{f}{a:+.2f}" for f, a in SCAN_SWITCH_HIGH), "pairs": sw, "verdict": sv},
        "discredited": verdict == "FADES" and sv == "SWITCH GONE",
    }


def scan_after_the_fact(day1: dict, before: dict) -> dict:
    """Computed after seeing Day 1, outside the verdicts: Day 1's statistics without the working pairs whose fit ran to
    the grid's edge (|delta| = 1.5 on A or B); and Day 1's five programs shared with Kickoff 40's stage 2 (A at -0.5,
    0 and +0.5; B at -1 and 0) against that run's mean P(11) on the same programs, with the k_A they give against
    Kickoff 40's k_A. before: braket_map's recompute of Kickoff 40's stage 2."""
    pairs = [tuple(p) for p in day1["pairs"]]
    fA, fB = day1["fits"]["A"], day1["fits"]["B"]
    W = [pairs.index(tuple(p)) for p in day1["working"]]
    edge = [i for i in W if fA["at_grid_edge"][i] or fB["at_grid_edge"][i]]
    keep = [i for i in W if i not in edge]
    dA, dB = np.array(fA["delta"])[keep], np.array(fB["delta"])[keep]
    k40 = dict(zip(map(tuple, before["dead_pair_filter"]["working_pairs"]), before["all_working"]["kA"]))
    both = [i for i in keep if pairs[i] in k40]
    dA3, kA3 = np.array(fA["delta"])[both], np.array([k40[pairs[i]] for i in both])
    P40, order40 = np.asarray(before["per_circuit_P11"]), before["order"]

    def mean40(label):
        return P40[[i for i, lab in enumerate(order40) if lab == label]].mean(axis=0)

    PA, PB = np.array(day1["P11"]["A"]), np.array(day1["P11"]["B"])
    col = {f: {a: j for j, a in enumerate(SCAN[f]["offsets"])} for f in SCAN}
    shared = {
        "A_off": (PA[:, col["A"][-0.5]], "A off"),
        "A_no": (PA[:, col["A"][0.0]], "A no"),
        "A_wrong": (PA[:, col["A"][0.5]], "A wrong"),
        "B_off": (PB[:, col["B"][-1.0]], "B off"),
        "B_no": (PB[:, col["B"][0.0]], "B no"),
    }
    kA1 = (PA[:, col["A"][-0.5]] - PA[:, col["A"][0.0]]) / GAP["A"]
    w40 = [pairs.index(p) for p in map(tuple, before["dead_pair_filter"]["working_pairs"])]
    rms = np.array(fA["rms"])[keep] / np.array(fA["shot_sd_mean"])[keep]
    return {
        "edge_pairs": [list(pairs[i]) for i in edge],
        "n": len(keep),
        "sd_deltaA": float(dA.std(ddof=1)),
        "median_boot_sd_deltaA": float(np.median(np.array(fA["boot_sd"])[keep])),
        "mean_deltaA": float(dA.mean()),
        "mean_deltaB": float(dB.mean()),
        "median_deltaA": float(np.median(dA)),
        "median_deltaB": float(np.median(dB)),
        "r_dA_dB": _corr_n(dA, dB),
        "p_dA_dB": _scan_p(dA, dB, "greater"),
        "mean_abs_dA_minus_dB": float(np.mean(np.abs(dA - dB))),
        "r_dA_k40kA": _corr_n(dA3, kA3),
        "p_dA_k40kA_negative": _scan_p(dA3, kA3, "less"),
        "rms_over_shot_median_A": float(np.median(rms)),
        "shared_programs": {
            **{f"r_Day1_vs_K40_{k}": _corr_n(v, mean40(lab)) for k, (v, lab) in shared.items()},
            "r_kA_from_shared_programs_Day1_vs_K40_kA": _corr_n(kA1[w40], before["all_working"]["kA"]),
            "kA_Day1_9495_4243": [float(kA1[pairs.index((94, 95))]), float(kA1[pairs.index((42, 43))])],
        },
    }


def offset_scan(day1_rec: dict, day2_rec: dict, figures: dict, before: dict, compiled=None, k41_payoff=None) -> dict:
    """Kickoff 42, recomputed from both days' counts: a different measurement from the map, a recompute for this
    archived run, and not a command. Each day by scan_day; Day 2 adds V4 under the amended rule (which governs) and
    under the original rule, V5 and the switch. Beside the verdicts, given Kickoff 41's Part B recompute: r(Kickoff
    41's W, |delta_A| on Day 1), on all the pairs both have and without those whose Day 1 fit reached the grid's edge.
    compiled: {"day1": {...}, "day2": {...}}, the compiled programs by task label."""
    compiled = compiled or {}
    an1 = scan_day(day1_rec, figures["day1"], before, compiled.get("day1"))
    an2 = scan_day(day2_rec, figures["day2"], before, compiled.get("day2"))
    out = {
        "day1": an1,
        "day2": an2,
        "V4_amended_governs": scan_persistence(an1, an2, True),
        "V4_original_rule": scan_persistence(an1, an2, False),
        "V5": scan_fingerprints(an1, an2),
    }
    if k41_payoff is not None:
        pairs = [tuple(p) for p in an1["pairs"]]
        Wk = dict(zip(map(tuple, k41_payoff["pairs"]), k41_payoff["W"]))
        both = [p for p in pairs if p in Wk and list(p) in an1["working"]]
        dA = {p: abs(an1["fits"]["A"]["delta"][pairs.index(p)]) for p in both}
        edge = [
            p
            for p in both
            if an1["fits"]["A"]["at_grid_edge"][pairs.index(p)] or an1["fits"]["B"]["at_grid_edge"][pairs.index(p)]
        ]
        rest = [p for p in both if p not in edge]
        out["beside_k41"] = {
            "r_all": _corr_n([Wk[p] for p in both], [dA[p] for p in both]),
            "n": len(both),
            "r_without_grid_edge_fits": _corr_n([Wk[p] for p in rest], [dA[p] for p in rest]),
            "grid_edge_pairs": [list(p) for p in edge],
        }
    return out


# --------------------------------------------------------------------------- Kickoff 35: all of ibm_fez, three days
def full_chip_day(rec: dict) -> dict:
    """One Kickoff 35 day as persistence_analysis takes it, from the archived counts: per edge, the counts of 11 at
    each position of the mirror order, the published score x, and the vendor's flag (an IBM two-qubit error of exactly
    1.0). In each circuit, pair i of its round is read from Qiskit bits 2i and 2i + 1."""
    from .layout import vendor_flag
    from .verdicts import ORDER_PERSIST

    assert [tuple(o) for o in rec["order"]] == ORDER_PERSIST, "Kickoff 35's mirror order"
    obs: dict = {}
    for pos, ((rname, variant), c) in enumerate(zip(ORDER_PERSIST, rec["counts"]), start=1):
        rnd = rec["rounds"][rname]
        for e, row in zip(rnd, pair_outcomes_from_bitstrings(c, len(rnd))):
            obs.setdefault(tuple(e), []).append(
                {"position": pos, "variant": variant, "n11": int(row[3]), "shots": int(row.sum())}
            )
    pub = {tuple(r["edge"]): r for r in rec["published_at_submission"]}
    edges = [tuple(e) for rnd in rec["rounds"].values() for e in rnd]
    return {
        "edges": edges,
        "x": [pub[e]["x"] for e in edges],
        "obs": [obs[e] for e in edges],
        "flags": [vendor_flag(two_qubit_error=pub[e]["cz_error"]) for e in edges],
    }


def full_chip_levels(day: dict) -> dict:
    """Per edge, P(11) without and with the offset (both copies) and the shot-noise SE of k."""
    from .verdicts import _k_obs

    rows = [_k_obs(o) for o in day["obs"]]
    return {
        "P_no": [r[2] for r in rows],
        "P_off": [r[1] for r in rows],
        "shot_se_per_edge": [
            math.sqrt(po * (1 - po) / n_off + pn * (1 - pn) / n_no) / GAP["A"] for _, po, pn, n_off, n_no in rows
        ],
    }


def _restricted(days: dict, keep) -> dict:
    keep = set(keep)
    out = {}
    for d, day in days.items():
        idx = [i for i, e in enumerate(day["edges"]) if tuple(e) in keep]
        out[d] = {k: [day[k][i] for i in idx] for k in ("edges", "x", "obs")}
    return out


def _persistence_block(a: dict) -> dict:
    """A persistence analysis in the shape of Kickoff 35's descriptive blocks."""
    ac = a["across"]
    return {
        "n_edges": ac["edges_on_all_days"],
        "reliability": {d: v["reliability"] for d, v in a["per_day"].items()},
        "pairs": {
            f"{k[0]}-{k[1]}": {
                "r_k": ac["raw"][k]["pearson"],
                "rho_k": ac["raw"][k]["spearman"],
                "corrected_r_k": ac["corrected"][k],
                "r_x": ac["x_raw"][k]["pearson"],
                "rho_x": ac["x_raw"][k]["spearman"],
            }
            for k in ac["raw"]
        },
        "decile_size": ac["decile_size"],
        "worst_decile_overlap_1_to_3": ac["worst_decile_overlap_13"],
    }


def full_chip_persistence(day_recs: dict) -> dict:
    """Kickoff 35 recomputed from its three days' counts: persistence_analysis (the verdict under the original rule,
    Amendment A1's beside it, and the flagged block), and the descriptive checks computed after seeing the data
    (outside the verdict): the line without the vendor's flagged edges, the core of edges within 1 of each day's
    median k, the rank-based corrected r, the k at ranks 17 to 20, the worst-decile overlap with each edge's k redrawn
    from its shot noise (seed 35, 2000 draws), a first look at the trend, and the six largest moves from Day 2 to
    Day 3. Like settle_analysis, this recomputes one archived run; it is not a new command."""
    from .verdicts import persistence_analysis

    days = {int(d): full_chip_day(r) for d, r in day_recs.items()}
    a = persistence_analysis(days)
    levels = {d: full_chip_levels(days[d]) for d in days}
    E = days[1]["edges"]
    assert all(days[d]["edges"] == E for d in days), "one layout on every day"
    k = {d: np.array(a["per_day"][str(d)]["k"]) for d in days}
    flagged = {d: sorted(e for e, f in zip(days[d]["edges"], days[d]["flags"]) if f) for d in days}
    fb = a["flagged"]["without"]
    without_flagged = {
        "n_edges": fb["n_edges"],
        "reliability": fb["reliability"],
        "pairs": {
            f"{p[0]}-{p[1]}": {
                "r_k": fb["raw"][p]["pearson"],
                "rho_k": fb["raw"][p]["spearman"],
                "corrected_r_k": fb["corrected"][p],
                "r_x": fb["x_raw"][p]["pearson"],
                "rho_x": fb["x_raw"][p]["spearman"],
            }
            for p in fb["raw"]
        },
        "decile_size": fb["decile_size"],
        "worst_decile_overlap_1_to_3": fb["worst_decile_overlap_13"],
    }
    core_mask = np.all([np.abs(k[d] - np.median(k[d])) < 1 for d in days], axis=0)
    core = [e for e, m in zip(E, core_mask) if m]
    core_a = persistence_analysis(_restricted(days, core))
    rs = {d: a["per_day"][str(d)]["r_split"]["spearman"] for d in days}
    rel_s = {d: 2 * r / (1 + r) for d, r in rs.items()}
    rank_corrected = {
        f"{p}-{q}": stats.corr(k[p], k[q])["spearman"] / math.sqrt(rel_s[p] * rel_s[q])
        for p, q in ((1, 2), (2, 3), (1, 3))
    }
    rng = np.random.default_rng(35)
    se1, se3 = np.array(levels[1]["shot_se_per_edge"]), np.array(levels[3]["shot_se_per_edge"])
    m = a["across"]["decile_size"]
    ov = []
    for _ in range(2000):
        x1, x3 = k[1] + rng.normal(0, se1), k[3] + rng.normal(0, se3)
        ov.append(len(set(np.argsort(x1, kind="stable")[:m]) & set(np.argsort(x3, kind="stable")[:m])) / m)
    ov = np.array(ov)
    mean12 = (k[1] + k[2]) / 2

    def trend(mask):
        return {
            "day2_alone": {"r": stats.corr(k[2][mask], k[3][mask])["pearson"], "rho": rs_of(k[2][mask], k[3][mask])},
            "mean_day1_day2": {
                "r": stats.corr(mean12[mask], k[3][mask])["pearson"],
                "rho": rs_of(mean12[mask], k[3][mask]),
            },
        }

    def rs_of(u, v):
        return stats.corr(u, v)["spearman"]

    moves = sorted(range(len(E)), key=lambda i: -abs(k[3][i] - k[2][i]))[:6]
    robustness = {
        "ibm_cz_error_1_edges_by_day": {str(d): [list(e) for e in v] for d, v in flagged.items()},
        "without_ibm_flagged_edges": without_flagged,
        "core_within_1_of_median": _persistence_block(core_a),
        "rank_based_corrected": rank_corrected,
        "day1_k_at_ranks_17_to_20": np.sort(k[1])[16:20].tolist(),
        "day3_k_at_ranks_17_to_20": np.sort(k[3])[16:20].tolist(),
        "worst_overlap_shot_redraw": {
            "draws": 2000,
            "median": float(np.median(ov)),
            "p5": float(np.percentile(ov, 5)),
            "p95": float(np.percentile(ov, 95)),
            "share_at_or_above_0.5": float((ov >= 0.5).mean()),
            "share_at_or_above_0.4": float((ov >= 0.4).mean()),
        },
        "trend_first_look": {"all": trend(np.ones(len(E), bool)), "core": trend(core_mask)},
        "largest_moves_2_to_3": [[list(E[i]), float(k[2][i]), float(k[3][i])] for i in moves],
    }
    return {"analysis": a, "levels": levels, "robustness": robustness, "rank_based_reliability": rel_s}


# --------------------------------------------------------------------------- an archived map, as the commands read it
class NotAMap(ValueError):
    """An archived record that is not a map run: its circuits are not circuits A and B without and with the offset."""


MAP_LABELS = {"A no", "A off", "B no", "B off"}


def map_view(rec: dict, where: Path | None = None) -> dict:
    """An archived map run as `manacitra pick`, `verdict` and `report` read it (Amendment A8, R1): by its declared bit
    reading, with the analysis its acceptance case computes, so that a command and the reproduction agree.

    * qiskit-adjacent and per-pair (IBM, the simulations): map_from_record, on every pair; x from
      published_at_submission (or the record's x), and the vendor's flag from the published two-qubit errors.
    * openquantum-reversed (Kickoff 34b's main job): rigetti_map, on the working pairs (its dead-pair filter); no x.
    * braket-measured-qubits (Kickoffs 40 and 41): braket_map, on the verdict set (the working pairs with a published
      figure), with x from the figures record that meta.figures_file names (the part meta.figures_part), found beside
      the record in `where`.

    Returns the verdict set's pairs, its columns of the P(11) table, the order, x on the set (or None), the flags, the
    analysis (with the verdict), the permutation seed, the shots per circuit, the halves, and a line saying which pairs
    the set holds."""
    order = rec.get("order")
    if not (isinstance(order, list) and all(isinstance(o, str) for o in order) and MAP_LABELS <= set(order)):
        raise NotAMap("this record is not a map run: its circuits are not circuits A and B without and with the offset")
    reading = bit_reading(rec)
    P = p11_table(rec)
    pairs = [tuple(p["qubits"]) if isinstance(p, dict) else tuple(p) for p in rec["pairs"]]
    meta = rec["meta"]
    seed, shots = meta.get("permutation_seed", 31), meta.get("shots_per_circuit", 8000)
    halves = {k: tuple(v) for k, v in rec["halves"].items()} if "halves" in rec else None
    flags, note = None, f"all {len(pairs)} pairs"
    if reading in ("qiskit-adjacent", "per-pair"):
        from .layout import vendor_flag

        an = map_from_record(rec)
        keep = list(range(len(pairs)))
        if "published_at_submission" in rec:
            x = [r["x"] for r in rec["published_at_submission"]]
            flags = [vendor_flag(two_qubit_error=r.get("cz_error")) for r in rec["published_at_submission"]]
        else:
            x = rec.get("x")
    elif reading == "openquantum-reversed":
        an = rigetti_map(rec)["analysis"]
        keep, x = an["pair_index"], None
        note = f"the {len(keep)} working pairs of {len(pairs)} (the run's dead-pair filter, mean P(A no) below 0.5 out)"
    else:
        if "figures_file" not in meta:
            raise NotAMap("meta.figures_file is missing: a Braket map takes its published figures from that record")
        figures = json.loads(((where or Path(".")) / meta["figures_file"]).read_text())[meta["figures_part"]]
        r = braket_map(rec, figures)
        an = r["verdict_stats"]
        keep = [pairs.index(tuple(p)) for p in r["verdict_set"]["pairs"]]
        capped = r["verdict_set"]["capped_at_MAP_PRESENT"]
        fig = _braket_figures(figures, pairs)
        x = None if capped else [fig[pairs[i]]["x"] for i in keep]
        note = (
            f"the verdict set, {len(keep)} of {len(pairs)} pairs: the working ones (mean P(A no) at least 0.5) with a "
            f"published figure in {meta['figures_file']}"
        )
    return {
        "pairs": [pairs[i] for i in keep],
        "P": P[:, keep],
        "order": order,
        "x": x,  # already on the set: every pair for IBM and the simulations, the verdict set for Braket
        "flags": None if flags is None else [flags[i] for i in keep],
        "analysis": an,
        "seed": seed,
        "shots": shots,
        "halves": halves,
        "reading": reading,
        "set": note,
    }


def workload_ideal(path="workload/k33-workload.json") -> list:
    return [c["ideal"] for c in load(path)["circuits"]]


def fez_or_kingston(processor: str) -> dict:
    """Every archived IBM file for one processor, keyed by run."""
    d = data_dir() / processor
    return {p.stem: json.loads(p.read_text()) for p in sorted(d.glob("*.json"))}
