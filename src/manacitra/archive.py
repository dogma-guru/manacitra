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
REPOSITORY = "https://github.com/dogmaguru/manacitra"
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


def p11_table(rec: dict) -> np.ndarray:
    """Per circuit, per pair P(11), from the archived counts (IBM bitstrings or per-pair outcome dicts)."""
    if "counts" not in rec:
        return np.asarray(rec["per_circuit_P11"], float)
    rows = []
    for c in rec["counts"]:
        if isinstance(c, list):  # per pair {"00": n, "01": n, "10": n, "11": n}
            rows.append([pc["11"] / sum(pc.values()) for pc in c])
        else:
            rows.append(p11_from_bitstrings(c, len(rec["pairs"])))
    return np.asarray(rows, float)


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
    if "published_at_submission" in rec:
        pub = rec["published_at_submission"]
        x = [r["x"] for r in pub]
        cz = [r["cz_error"] for r in pub]
        ro = [sum(r["readout_error"]) for r in pub]
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
    P = np.array([p11_classical_index(c, len(pairs)) for c in rec["counts"]])
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


def workload_ideal(path="workload/k33-workload.json") -> list:
    return [c["ideal"] for c in load(path)["circuits"]]


def fez_or_kingston(processor: str) -> dict:
    """Every archived IBM file for one processor, keyed by run."""
    d = data_dir() / processor
    return {p.stem: json.loads(p.read_text()) for p in sorted(d.glob("*.json"))}
