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
from pathlib import Path

import numpy as np

from . import stats
from .circuits import CIRCUITS, GAP
from .keptshare import kept_from_order, p11_from_bitstrings, pair_outcomes_from_bitstrings
from .verdicts import analyse_map, analyse_payoff
from .workload import ORDER_PAYOFF, aggregate, readout_confusion, workload_scores

DATA = Path(__file__).resolve().parents[2] / "data"


def data_dir() -> Path:
    """The repository's data/ directory (when installed from a clone)."""
    return DATA


def load(path) -> dict:
    p = Path(path)
    if not p.is_absolute() and not p.exists():
        p = DATA / p
    return json.loads(p.read_text())


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

    rows = []
    for side in ("worst", "best"):
        for r in sel[f"{side}6"]:
            p = tuple(r["pair"])
            kD, seD = k_and_se(p, "D")
            kS, seS = k_and_se(p, "S")
            rows.append(
                {"pair": list(p), "side": side, "kD": kD, "kS": kS, "delta": kS - kD, "se_delta": math.hypot(seD, seS)}
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
            "k_now": k_now.tolist(),
            "L_now": L_now.tolist(),
            "readout_confusion": M.tolist(),
        }
    )
    return out


def workload_ideal(path="workload/k33-workload.json") -> list:
    return [c["ideal"] for c in load(path)["circuits"]]


def fez_or_kingston(processor: str) -> dict:
    """Every archived IBM file for one processor, keyed by run."""
    d = DATA / processor
    return {p.stem: json.loads(p.read_text()) for p in sorted(d.glob("*.json"))}
