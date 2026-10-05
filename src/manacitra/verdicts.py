# Copyright 2026 Anish Patel
# SPDX-License-Identifier: Apache-2.0
"""The three verdict rules, each a pure function of its inputs that returns the verdict and every number it used.

* The map rule (Kickoff 31; capped form from Kickoff 34, Amendment A1): does a per-pair map exist, and does the
  published score already carry it? NOISE, REDUNDANT, DIAGNOSTIC, NOT SETTLED; MAP PRESENT when no published score
  exists.
* The payoff rule (Kickoff 33): does choosing pairs by a prior map do better on unrelated work than choosing by the
  published score? USEFUL, NOT USEFUL, NOT SETTLED.
* The persistence rule (Kickoff 35 with Amendment A1, the original rule returned beside it): how much of a map
  survives from day to day? HOLDS, FADES, PARTIAL, NOT SETTLED (too noisy).

What would discredit the map: a NOISE or REDUNDANT verdict (it does not repeat, or the published score already holds
it); NOT USEFUL (it picks no better pairs); FADES (it does not last long enough to schedule by).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass, field

import numpy as np

from . import stats
from .circuits import CIRCUITS, GAP, HALVES, ORDER_16
from .keptshare import kept_from_order

# --------------------------------------------------------------------------- thresholds, fixed in the kickoffs
MAP_NOISE_BELOW = 0.3  # r_split(k_A) < 0.3: NOISE
MAP_REPEAT_AT_LEAST = 0.5  # r_split(k_A) >= 0.5
MAP_TRANSFER_AT_LEAST = 0.4  # r_AB >= 0.4
MAP_P_BELOW = 0.05  # one-sided permutation p < 0.05
MAP_PARTIAL_AT_LEAST = 0.3  # r_AB.x >= 0.3
MAP_REDUNDANT_PARTIAL = 0.15  # r_AB.x < 0.15 (with r_AB >= 0.4): REDUNDANT
MAP_SCORE_EXPLAINS = 0.5  # |r_Ax| >= 0.5: REDUNDANT

PAYOFF_PARTIAL_AT_LEAST = 0.3
PAYOFF_P_BELOW = 0.05
PAYOFF_NOT_USEFUL_PARTIAL = 0.15

PERSIST_HOLDS_AT_LEAST = 0.7  # corrected r >= 0.7
PERSIST_FADES_BELOW = 0.5  # corrected r < 0.5
PERSIST_DECILE_ORIGINAL = 0.5  # worst-decile overlap, original rule
PERSIST_DECILE_A1 = 0.4  # worst-decile overlap, Amendment A1
PERSIST_RELIABILITY_FLOOR = 0.5

DEAD_PAIR_FLOOR = 0.5  # Kickoff 34 A1: a pair whose mean P(A no) is below this is not working


@dataclass
class Verdict:
    """A rule's outcome: the verdict, the rule's name, every input it used, and each condition as tested."""

    verdict: str
    rule: str
    inputs: dict
    conditions: dict = field(default_factory=dict)
    note: str | None = None

    def as_dict(self) -> dict:
        return asdict(self)


# =========================================================================== the map rule
def map_verdict(
    r_split_A: float, r_AB: float, p_AB: float, r_AB_x: float | None = None, r_Ax: float | None = None
) -> Verdict:
    """Kickoff 31's rule, or, when no published score exists (r_Ax and r_AB_x both None), Kickoff 34 A1's capped rule.

    Full rule, tested in this order:
      NOISE        r_split(k_A) < 0.3
      REDUNDANT    r_split >= 0.5, and either |r_Ax| >= 0.5, or r_AB >= 0.4 with r_AB.x < 0.15
      DIAGNOSTIC   r_split >= 0.5, r_AB >= 0.4 with p < 0.05, r_AB.x >= 0.3 and |r_Ax| < 0.5
      NOT SETTLED  anything else
    Capped rule (no published score): NOISE as above; MAP PRESENT if r_split >= 0.5 and r_AB >= 0.4 with p < 0.05;
    NOT SETTLED otherwise.
    """
    inputs = {"r_split_A": r_split_A, "r_AB": r_AB, "p_AB": p_AB, "r_AB_given_x": r_AB_x, "r_Ax": r_Ax}
    repeats = r_split_A >= MAP_REPEAT_AT_LEAST
    transfers = r_AB >= MAP_TRANSFER_AT_LEAST and p_AB < MAP_P_BELOW
    if r_Ax is None and r_AB_x is None:
        cond = {
            "noise: r_split < 0.3": r_split_A < MAP_NOISE_BELOW,
            "r_split >= 0.5": repeats,
            "r_AB >= 0.4 with p < 0.05": transfers,
        }
        if r_split_A < MAP_NOISE_BELOW:
            v = "NOISE"
        elif repeats and transfers:
            v = "MAP PRESENT"
        else:
            v = "NOT SETTLED"
        return Verdict(
            v,
            "map rule, capped (no published score; Kickoff 34 A1)",
            inputs,
            cond,
            "no published per-pair score: the verdict is capped at MAP PRESENT",
        )
    if r_Ax is None or r_AB_x is None:
        raise ValueError("give both r_Ax and r_AB_x, or neither")
    redundant = repeats and (
        abs(r_Ax) >= MAP_SCORE_EXPLAINS or (r_AB >= MAP_TRANSFER_AT_LEAST and r_AB_x < MAP_REDUNDANT_PARTIAL)
    )
    cond = {
        "noise: r_split < 0.3": r_split_A < MAP_NOISE_BELOW,
        "r_split >= 0.5": repeats,
        "r_AB >= 0.4 with p < 0.05": transfers,
        "r_AB.x >= 0.3": r_AB_x >= MAP_PARTIAL_AT_LEAST,
        "|r_Ax| < 0.5": abs(r_Ax) < MAP_SCORE_EXPLAINS,
        "redundant trigger": redundant,
    }
    if r_split_A < MAP_NOISE_BELOW:
        v = "NOISE"
    elif redundant:
        v = "REDUNDANT"
    elif repeats and transfers and r_AB_x >= MAP_PARTIAL_AT_LEAST and abs(r_Ax) < MAP_SCORE_EXPLAINS:
        v = "DIAGNOSTIC"
    else:
        v = "NOT SETTLED"
    return Verdict(v, "map rule (Kickoff 31)", inputs, cond)


def analyse_map(
    P,
    order: Sequence[str] = ORDER_16,
    x=None,
    cz_error=None,
    readout_error=None,
    shots: int = 8000,
    seed: int = 31,
    prev_k=None,
    halves=None,
    dead_pair_floor: float | None = None,
    n_permutations: int = stats.N_PERMUTATIONS,
) -> dict:
    """Kickoff 31's analysis and verdict from a per-circuit, per-pair P(11) table.

    P: one row per circuit position in `order` (Kickoff 31's 18 or Kickoff 34's 16), one column per pair.
    x: the published per-pair score (two-qubit error plus both readout errors), or None if the provider publishes none.
    cz_error, readout_error (sum of both qubits): reported beside x, not used in the verdict.
    seed: the permutation seed (each published run used its kickoff number: 31, 34, 36).
    prev_k: an earlier run's k_A for the same pairs; adds S4 (persistence, not in the verdict).
    dead_pair_floor: if given, pairs whose mean P(A no) is below it are excluded first (Kickoff 34 A1), and logged.
    """
    P = np.asarray(P, float)
    halves = halves or HALVES
    out: dict = {}
    keep = np.arange(P.shape[1])
    if dead_pair_floor is not None:
        a_no = np.mean([P[i] for i, label in enumerate(order) if label == "A no"], axis=0)
        keep = np.flatnonzero(a_no >= dead_pair_floor)
        out["dead_pair_filter"] = {
            "floor": dead_pair_floor,
            "mean_P_A_no": a_no.tolist(),
            "excluded": [int(i) for i in range(P.shape[1]) if i not in set(keep.tolist())],
        }
        P = P[:, keep]
        x = None if x is None else np.asarray(x, float)[keep]
        cz_error = None if cz_error is None else np.asarray(cz_error, float)[keep]
        readout_error = None if readout_error is None else np.asarray(readout_error, float)[keep]
        prev_k = None if prev_k is None else np.asarray(prev_k, float)[keep]
        if len(keep) < 20:
            out["verdict"] = Verdict(
                "NOT SETTLED",
                "map rule",
                {"n_working_pairs": int(len(keep))},
                {},
                "too few working pairs (fewer than 20)",
            ).as_dict()
            return out
    n = P.shape[1]
    kA, offA, noA = kept_from_order(P, order, "A")
    kB, offB, noB = kept_from_order(P, order, "B")
    kA1, kA2 = kept_from_order(P, order, "A", halves["A"][0])[0], kept_from_order(P, order, "A", halves["A"][1])[0]
    kB1, kB2 = kept_from_order(P, order, "B", halves["B"][0])[0], kept_from_order(P, order, "B", halves["B"][1])[0]
    copies = {label: sum(1 for ll in order if ll == label) for label in dict.fromkeys(order)}
    mean_P = {
        label: float(np.mean([P[i] for i, ll in enumerate(order) if ll == label], axis=0).mean())
        for label in dict.fromkeys(order)
    }
    shot_sd = {
        c: float(
            np.mean(np.sqrt(o * (1 - o) / (copies[f"{c} off"] * shots) + q * (1 - q) / (copies[f"{c} no"] * shots)))
            / GAP[c]
        )
        for c, o, q in (("A", offA, noA), ("B", offB, noB))
    }
    out.update(
        {
            "n_pairs": n,
            "pair_index": keep.tolist(),
            "mean_P": mean_P,
            "kA": kA.tolist(),
            "kB": kB.tolist(),
            "kA_half1": kA1.tolist(),
            "kA_half2": kA2.tolist(),
            "kB_half1": kB1.tolist(),
            "kB_half2": kB2.tolist(),
            "mean_kA": float(kA.mean()),
            "mean_kB": float(kB.mean()),
            "sd_kA_between_pairs": float(kA.std(ddof=1)),
            "sd_kB_between_pairs": float(kB.std(ddof=1)),
            "shot_noise_sd_per_pair": shot_sd,
            "S1": {"r_split_A": stats.corr(kA1, kA2), "r_split_B": stats.corr(kB1, kB2)},
            "S2": {"r_AB": stats.corr(kA, kB), "p_one_sided": stats.permutation_p(kA, kB, seed, True, n_permutations)},
        }
    )
    if x is not None:
        x = np.asarray(x, float)
        out["S3"] = {
            "r_Ax": stats.corr(kA, x),
            "p_Ax_two_sided": stats.permutation_p(kA, x, seed, False, n_permutations),
            "r_AB_given_x": stats.partial_r(kA, kB, x),
        }
        if cz_error is not None:
            out["S3"]["r_A_cz"] = stats.corr(kA, np.asarray(cz_error, float))
        if readout_error is not None:
            out["S3"]["r_A_readout"] = stats.corr(kA, np.asarray(readout_error, float))
    else:
        out["S3"] = "not available (no published per-pair score)"
    if "A wrong" in order:
        f = CIRCUITS["A"]
        wA = (P[list(order).index("A wrong")] - noA) / (f.ideal_wrong - f.ideal_no)
        out["wrong_sign_kept_A"] = wA.tolist()
        out["r_kA_wrongA"] = stats.corr(kA, wA)
    if prev_k is not None:
        prev_k = np.asarray(prev_k, float)
        out["S4"] = {
            "r_vs_previous": stats.corr(kA, prev_k),
            "p_one_sided": stats.permutation_p(kA, prev_k, seed, True, n_permutations),
        }
    s3 = out["S3"] if isinstance(out["S3"], dict) else {}
    v = map_verdict(
        out["S1"]["r_split_A"]["pearson"],
        out["S2"]["r_AB"]["pearson"],
        out["S2"]["p_one_sided"],
        s3.get("r_AB_given_x"),
        s3["r_Ax"]["pearson"] if s3 else None,
    )
    out["verdict"] = v.as_dict()
    return out


def leave_one_out(P, order: Sequence[str] = ORDER_16, x=None, seed: int = 31, prev_k=None, **kw) -> dict:
    """Descriptive only: the map rule without the pair whose k_A lies farthest from the mean (Kickoff 31's check)."""
    P = np.asarray(P, float)
    kA = kept_from_order(P, order, "A")[0]
    d = int(np.argmax(np.abs(kA - kA.mean())))
    keep = [i for i in range(P.shape[1]) if i != d]
    sub = analyse_map(
        P[:, keep],
        order,
        None if x is None else np.asarray(x)[keep],
        seed=seed,
        prev_k=None if prev_k is None else np.asarray(prev_k)[keep],
        **kw,
    )
    return {"note": "descriptive, not a verdict: the rule without the most extreme pair", "dropped_index": d, **sub}


# =========================================================================== the payoff rule
def payoff_verdict(partial_r: float, p_partial: float, gain_ci90: Sequence[float]) -> Verdict:
    """Kickoff 33's rule.

    USEFUL       partial r(W, k_prior | x) >= 0.3 with p < 0.05, and the gain's 90% interval lies above 0
    NOT USEFUL   partial r < 0.15, or the gain's 90% interval lies entirely at or below 0
    NOT SETTLED  anything else
    """
    lo, hi = gain_ci90
    cond = {
        "partial >= 0.3 with p < 0.05": partial_r >= PAYOFF_PARTIAL_AT_LEAST and p_partial < PAYOFF_P_BELOW,
        "gain interval above 0": lo > 0,
        "partial < 0.15": partial_r < PAYOFF_NOT_USEFUL_PARTIAL,
        "gain interval at or below 0": hi <= 0,
    }
    if partial_r >= PAYOFF_PARTIAL_AT_LEAST and p_partial < PAYOFF_P_BELOW and lo > 0:
        v = "USEFUL"
    elif partial_r < PAYOFF_NOT_USEFUL_PARTIAL or hi <= 0:
        v = "NOT USEFUL"
    else:
        v = "NOT SETTLED"
    return Verdict(
        v,
        "payoff rule (Kickoff 33)",
        {"partial_r": partial_r, "p_partial": p_partial, "gain_ci90": [float(lo), float(hi)]},
        cond,
    )


def top_n(values, n: int = 8, largest: bool = True) -> list[int]:
    """Indices of the n largest (or smallest) values, as Kickoff 33 picked them."""
    v = np.asarray(values, float)
    return [int(i) for i in np.argsort(-v if largest else v)[:n]]


def analyse_payoff(
    W_per_circuit,
    k_prior,
    x,
    L_prior=None,
    k_now=None,
    L_now=None,
    W_rc_per_circuit=None,
    seed: int = 33,
    n_pick: int = 8,
    n_boot: int = stats.N_PERMUTATIONS,
    n_permutations: int = stats.N_PERMUTATIONS,
    shots_interval: dict | None = None,
) -> dict:
    """Kickoff 33's analysis and verdict.

    W_per_circuit: per pair (rows), the Hellinger fidelity on each workload circuit (columns); W is the row mean.
    k_prior: the map measured before the workload ran. x: the published score at submission (lower is better).
    L_prior, k_now, L_now: reported beside the verdict. W_rc_per_circuit: the readout-corrected W, also beside it.
    shots_interval: optional {"counts": (pairs, circuits) shot totals, "dists": (pairs, circuits, 4) measured
    distributions, "ideal": (circuits, 4)}: adds the interval that also resamples shots (not in the verdict).
    """
    W_c = np.asarray(W_per_circuit, float)
    W = W_c.mean(axis=1)
    k_prior, x = np.asarray(k_prior, float), np.asarray(x, float)
    preds = {"k_prior": k_prior, "x": x}
    for name, v in (("L_prior", L_prior), ("k_now", k_now), ("L_now", L_now)):
        if v is not None:
            preds[name] = np.asarray(v, float)
    scores = {"W": W_c}
    if W_rc_per_circuit is not None:
        scores["W_rc"] = np.asarray(W_rc_per_circuit, float)
    corrs = {}
    for wname, wc in scores.items():
        w = wc.mean(axis=1)
        corrs[wname] = {name: stats.corr(w, v) for name, v in preds.items()}
        corrs[wname]["p_k_prior_one_sided"] = stats.permutation_p(w, k_prior, seed, True, n_permutations)
        rw, rk = stats.residuals(w, x), stats.residuals(k_prior, x)
        corrs[wname]["partial_k_prior_given_x"] = float(stats.corr(rw, rk)["pearson"])
        corrs[wname]["p_partial_one_sided"] = stats.permutation_p(rw, rk, seed, True, n_permutations)
    picks = {"k_prior": top_n(k_prior, n_pick), "x": top_n(x, n_pick, largest=False)}
    for name in ("L_prior", "k_now"):
        if name in preds:
            picks[name] = top_n(preds[name], n_pick)
    rng = np.random.default_rng(seed)
    gains = {}
    for sel in [s for s in ("k_prior", "L_prior", "k_now") if s in picks]:
        g, ci, _ = stats.bootstrap_gain_over_circuits(W_c, picks[sel], picks["x"], seed, n_boot, rng=rng)
        gains[sel] = {
            "G": g,
            "ci90": ci,
            "overlap_with_x_pick": len(set(picks[sel]) & set(picks["x"])),
            "error_ratio": float((1 - W[picks[sel]].mean()) / (1 - W[picks["x"]].mean())),
        }
        if shots_interval is not None:
            gains[sel]["ci90_circuits_and_shots_not_in_verdict"] = _shots_interval(
                shots_interval, picks[sel], picks["x"], seed
            )
    c = corrs["W"]
    v = payoff_verdict(c["partial_k_prior_given_x"], c["p_partial_one_sided"], gains["k_prior"]["ci90"])
    out = {
        "W": W.tolist(),
        "mean_W": float(W.mean()),
        "correlations": corrs,
        "picks": picks,
        "gains": gains,
        "verdict": v.as_dict(),
    }
    if "W_rc" in scores:
        out["W_rc"] = scores["W_rc"].mean(axis=1).tolist()
        out["mean_W_rc"] = float(scores["W_rc"].mean())
    if "L_prior" in preds:
        out["level_beats_k"] = abs(c["L_prior"]["pearson"]) > abs(c["k_prior"]["pearson"])
    return out


def _shots_interval(spec: dict, pick, reference, seed: int, n: int = 2000) -> list[float]:
    """Beside the verdict only (Kickoff 33): resample circuits and, within each, the shots (multinomial)."""
    from .workload import hellinger_fidelity

    rng2 = np.random.default_rng(seed + 1000)
    ns, Q, p_id = (
        np.asarray(spec["counts"]),
        np.asarray(spec["dists"], float),
        [np.asarray(p, float) for p in spec["ideal"]],
    )
    n_pairs, n_c = ns.shape
    boots = []
    for _ in range(n):
        jj = rng2.integers(0, n_c, n_c)
        Wb = np.zeros(n_pairs)
        for i in range(n_pairs):
            Wb[i] = np.mean(
                [hellinger_fidelity(p_id[j], rng2.multinomial(int(ns[i, j]), Q[i, j]) / ns[i, j]) for j in jj]
            )
        boots.append(Wb[list(pick)].mean() - Wb[list(reference)].mean())
    return [float(np.percentile(boots, 5)), float(np.percentile(boots, 95))]


# =========================================================================== the persistence rule
#: Kickoff 35's 12-circuit mirror order: each round's pairs run "A no" / "A off", first copies at 1 to 6.
ORDER_PERSIST = [
    ("R1", "no"),
    ("R1", "off"),
    ("R2", "no"),
    ("R2", "off"),
    ("R3", "no"),
    ("R3", "off"),
    ("R3", "off"),
    ("R3", "no"),
    ("R2", "off"),
    ("R2", "no"),
    ("R1", "off"),
    ("R1", "no"),
]


def day_from_rounds(rounds: dict[str, list], P_by_position, x_by_edge: dict, shots: int = 4000) -> dict:
    """One day's input for persistence_analysis from Kickoff 35's layout: rounds {"R1": [edge, ...], ...} and the
    per-position P(11) of each round's edges in ORDER_PERSIST."""
    obs: dict = {}
    for pos, ((rname, variant), P) in enumerate(zip(ORDER_PERSIST, P_by_position), start=1):
        for e, p in zip(rounds[rname], P):
            obs.setdefault(tuple(e), []).append({"position": pos, "variant": variant, "n11": p * shots, "shots": shots})
    edges = [tuple(e) for r in rounds.values() for e in r]
    return {"edges": edges, "x": [x_by_edge[e] for e in edges], "obs": [obs[e] for e in edges]}


def _k_obs(obs, positions=None):
    sel = [o for o in obs if positions is None or o["position"] in positions]
    off = [o["n11"] / o["shots"] for o in sel if o["variant"] == "off"]
    no = [o["n11"] / o["shots"] for o in sel if o["variant"] == "no"]
    n_off = sum(o["shots"] for o in sel if o["variant"] == "off")
    n_no = sum(o["shots"] for o in sel if o["variant"] == "no")
    po, pn = float(np.mean(off)), float(np.mean(no))
    return (po - pn) / GAP["A"], po, pn, n_off, n_no


def persistence_day(day: dict) -> dict:
    """Kickoff 35 section 3, per day: k per edge, its spread and shot noise, r_split (positions 1 to 6 against 7 to
    12), the Spearman-Brown reliability, and r(k, x)."""
    ks, sds, k1, k2 = [], [], [], []
    for obs in day["obs"]:
        k, po, pn, n_off, n_no = _k_obs(obs)
        ks.append(k)
        sds.append(float(np.sqrt(po * (1 - po) / n_off + pn * (1 - pn) / n_no) / GAP["A"]))
        k1.append(_k_obs(obs, range(1, 7))[0])
        k2.append(_k_obs(obs, range(7, 13))[0])
    rs = stats.corr_or_none(k1, k2)
    return {
        "n_edges": len(ks),
        "k": ks,
        "k_first_copies": k1,
        "k_second_copies": k2,
        "mean_k": float(np.mean(ks)),
        "sd_k_between_edges": float(np.std(ks, ddof=1)),
        "shot_noise_sd": float(np.mean(sds)),
        "r_split": rs,
        "reliability": stats.spearman_brown(rs["pearson"]),
        "r_k_x": stats.corr_or_none(ks, day["x"]),
    }


def _decile_overlap(ka, kb, worst: bool = True) -> tuple[float, int]:
    """The share of day a's worst (or best) decile still in day b's; the decile is round(0.1 n) edges, at least 1."""
    ka, kb = np.asarray(ka, float), np.asarray(kb, float)
    m = max(1, int(round(0.1 * len(ka))))
    if worst:
        a, b = set(np.argsort(ka)[:m]), set(np.argsort(kb)[:m])
    else:
        a, b = set(np.argsort(-ka)[:m]), set(np.argsort(-kb)[:m])
    return len(a & b) / m, m


def persistence_verdict_original(
    c12: float | None, c13: float | None, worst_overlap_13: float | None, n_days: int
) -> Verdict:
    """Kickoff 35 section 4, as written before Amendment A1.

      FADES     corrected r(k1, k2) < 0.5
      HOLDS     corrected r(k1, k3) >= 0.7, and the worst-decile overlap Day 1 to Day 3 >= 50%
      PARTIAL   anything else
    With two days: HOLDS or FADES from r(k1, k2) alone, stated as "one day only". A condition on an undefined
    corrected r (a reliability that is not positive) is not met; the original rule did not say, and Amendment A1
    was written to close that gap.
    """
    inputs = {
        "corrected_r_12": c12,
        "corrected_r_13": c13,
        "worst_decile_overlap_13": worst_overlap_13,
        "n_days": n_days,
    }
    note = None
    if n_days >= 3:
        fades = c12 is not None and c12 < PERSIST_FADES_BELOW
        holds = (
            c13 is not None
            and c13 >= PERSIST_HOLDS_AT_LEAST
            and worst_overlap_13 is not None
            and worst_overlap_13 >= PERSIST_DECILE_ORIGINAL
        )
        v = "FADES" if fades else ("HOLDS" if holds else "PARTIAL")
        if fades and holds:
            note = "both the FADES and HOLDS conditions are met; FADES is tested first"
    elif n_days == 2:
        fades = c12 is not None and c12 < PERSIST_FADES_BELOW
        holds = c12 is not None and c12 >= PERSIST_HOLDS_AT_LEAST
        v = "FADES" if fades else ("HOLDS" if holds else "PARTIAL")
        note = "one day only: the verdict is from r(k1, k2) alone"
    else:
        fades = holds = False
        v, note = "PARTIAL", "fewer than two days"
    return Verdict(
        v, "persistence rule, original (Kickoff 35 section 4)", inputs, {"fades": fades, "holds": holds}, note
    )


def persistence_verdict_a1(
    reliability: dict[int, float | None],
    corrected: dict[tuple[int, int], float | None],
    worst_overlap: dict[tuple[int, int], float],
) -> Verdict:
    """Kickoff 35 with Amendment A1.

    A day whose Spearman-Brown reliability is below 0.5 is too noisy and is not used. With the days that pass:
      FADES     corrected r of the first two passing days < 0.5
      HOLDS     corrected r of the earliest and latest passing days >= 0.7, and their worst-decile overlap >= 40%
      PARTIAL   anything else
      NOT SETTLED (too noisy)   fewer than two days pass
    """
    passing = sorted(d for d, rel in reliability.items() if rel is not None and rel >= PERSIST_RELIABILITY_FLOOR)
    inputs = {"reliability": {str(d): r for d, r in reliability.items()}, "days_passing": passing}
    if len(passing) < 2:
        return Verdict(
            "NOT SETTLED (too noisy)",
            "persistence rule (Kickoff 35, Amendment A1)",
            inputs,
            {},
            "fewer than two days pass the reliability floor of 0.5",
        )
    fade_pair, hold_pair = (passing[0], passing[1]), (passing[0], passing[-1])
    cf, ch, wov = corrected[fade_pair], corrected[hold_pair], worst_overlap[hold_pair]
    inputs.update(
        {
            "fades_pair": list(fade_pair),
            "corrected_r_fades_pair": cf,
            "holds_pair": list(hold_pair),
            "corrected_r_holds_pair": ch,
            "worst_decile_overlap_holds_pair": wov,
        }
    )
    fades = cf is not None and cf < PERSIST_FADES_BELOW
    holds = ch is not None and ch >= PERSIST_HOLDS_AT_LEAST and wov >= PERSIST_DECILE_A1
    v = "FADES" if fades else ("HOLDS" if holds else "PARTIAL")
    note = "both the FADES and HOLDS conditions are met; FADES is tested first" if fades and holds else None
    return Verdict(v, "persistence rule (Kickoff 35, Amendment A1)", inputs, {"fades": fades, "holds": holds}, note)


def persistence_analysis(days: dict) -> dict:
    """Kickoff 35's analysis across days, with the verdict under Amendment A1 and the original rule beside it.

    days: {day number: {"edges": [...], "x": [published score per edge], "obs": [[{"position", "variant",
    "n11", "shots"}, ...] per edge]}}; positions 1 to 12 in ORDER_PERSIST. See day_from_rounds for Kickoff 35's layout.
    """
    days = {int(d): v for d, v in days.items()}
    present = sorted(days)
    per_day = {d: persistence_day(days[d]) for d in present}

    def common_edges(ds):
        keys = [[tuple(e) if isinstance(e, list) else e for e in days[d]["edges"]] for d in ds]
        common = set(keys[0]).intersection(*keys[1:])
        return [e for e in keys[0] if e in common]

    def vec(d, key, edges):
        idx = {(tuple(e) if isinstance(e, list) else e): i for i, e in enumerate(days[d]["edges"])}
        src = per_day[d]["k"] if key == "k" else days[d]["x"]
        return np.array([src[idx[e]] for e in edges], float)

    rel = {d: per_day[d]["reliability"] for d in present}
    common = common_edges(present)
    across: dict = {"edges_on_all_days": len(common), "raw": {}, "corrected": {}, "x_raw": {}}
    for a, b in ((1, 2), (2, 3), (1, 3)):
        if a in days and b in days:
            r = stats.corr_or_none(vec(a, "k", common), vec(b, "k", common))
            across["raw"][f"{a}{b}"] = r
            across["corrected"][f"{a}{b}"] = stats.disattenuated(r["pearson"], rel[a], rel[b])
            across["x_raw"][f"{a}{b}"] = stats.corr_or_none(vec(a, "x", common), vec(b, "x", common))
    first, last = present[0], present[-1]
    wo, m = _decile_overlap(vec(first, "k", common), vec(last, "k", common), True)
    bo, _ = _decile_overlap(vec(first, "k", common), vec(last, "k", common), False)
    across.update(
        {"decile_size": m, f"worst_decile_overlap_{first}{last}": wo, f"best_decile_overlap_{first}{last}": bo}
    )
    across["map_or_score_persists_more"] = {
        k: (
            None
            if r["pearson"] is None or across["x_raw"][k]["pearson"] is None
            else ("map" if r["pearson"] > across["x_raw"][k]["pearson"] else "published score")
        )
        for k, r in across["raw"].items()
    }

    original = persistence_verdict_original(
        across["corrected"].get("12"),
        across["corrected"].get("13"),
        across.get("worst_decile_overlap_13"),
        len(present),
    )
    # Amendment A1: correlations over the edges common to the days that pass, pair by pair
    passing = sorted(d for d in present if rel[d] is not None and rel[d] >= PERSIST_RELIABILITY_FLOOR)
    corrected_a1, worst_a1 = {}, {}
    if len(passing) >= 2:
        common_p = common_edges(passing)
        for a, b in {(passing[0], passing[1]), (passing[0], passing[-1])}:
            r = stats.corr_or_none(vec(a, "k", common_p), vec(b, "k", common_p))["pearson"]
            corrected_a1[(a, b)] = stats.disattenuated(r, rel[a], rel[b])
            worst_a1[(a, b)] = _decile_overlap(vec(a, "k", common_p), vec(b, "k", common_p), True)[0]
    a1 = persistence_verdict_a1(rel, corrected_a1, worst_a1)
    return {
        "per_day": {str(d): per_day[d] for d in present},
        "across": across,
        "verdict": a1.as_dict(),
        "original_rule": original.as_dict(),
    }
