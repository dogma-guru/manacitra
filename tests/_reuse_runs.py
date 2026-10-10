# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""Kickoffs 43 to 47 (findings 11 to 13), recomputed from the archived counts in data/ibm_fez/k43-map.json to
k47-wait.json.

Each function takes the data files as loaded and returns the analysis in the shape the run archived it (under
archived/analysis), so that tests/_reproduce.py compares the two field by field. The rules are the runs' own, fixed
before the data (Kickoff 43 with its Amendment A1). The bootstraps keep each run's seed and its order of random draws,
so an interval reproduces exactly under the runs' numpy (2.5) and agrees to 10⁻³ elsewhere (the "resampled-shots" mark
in tests/expected_fields.json, as for Kickoff 33's intervals).

This is a test helper, not part of the package: no command reads these runs, and a probe that measures a wait loss
is a later step, by plan (Amendment A17).
"""

from __future__ import annotations

import math
from collections import defaultdict

import numpy as np

from manacitra import archive as ar
from manacitra.verdicts import map_verdict, persistence_day

N_BOOT = 10_000
Z90 = 1.6448536269514722  # the 95th percentile of the standard normal, as Kickoff 43's analysis wrote it
DEAD_FLOOR = 0.5  # the dead-pair floor on the plain level (Kickoff 43, section 2; kept by Amendment A1)
#: Amendment A1's score, the gate-weighted sum of |1 - k|, and the two rules reported beside it, not run
SCORES = {"distance": lambda k: abs(1 - k), "as_fixed": lambda k: 1 - k, "capped": lambda k: 1 - min(k, 1)}
CIRCS, COMPS, PLACES = ("XOR_5", "BV_10", "Mul_13", "Sym_9"), ("no_reuse", "reuse"), ("map", "calibration")
#: Kickoff 44's constants, as its analysis wrote them: circuit A's gap (rounded to six places, as in the kickoff) and
#: the level's sensitivity to a reset residual, from the exact probe ideal (0.9621 per unit)
GAP_A = 0.037765
DLEVEL = 0.9621
TAU_R0 = 836 * 4e-9  # Kickoff 44's R0 delay, measure plus reset on every qubit tested (836 dt of 4 ns)


def pct(a) -> list[float]:
    lo, hi = np.percentile(a, [5, 95])
    return [float(lo), float(hi)]


def _nan_to_none(x):
    """The data files keep a quantity not measured as null (NaN is not JSON); the recompute does the same."""
    if isinstance(x, dict):
        return {k: _nan_to_none(v) for k, v in x.items()}
    if isinstance(x, list):
        return [_nan_to_none(v) for v in x]
    if isinstance(x, float) and not math.isfinite(x):
        return None
    return x


def _bits(key: str) -> str:
    """A Qiskit key with classical bit 0 first."""
    return key.replace(" ", "")[::-1]


def outcome(key: str, clbits) -> str:
    """The outcome on these classical bits, the last listed bit first, as the ideal distributions are keyed."""
    b = _bits(key)
    return "".join(b[c] for c in reversed(clbits))


def _corr(x, y) -> float:
    return float(np.corrcoef(x, y)[0, 1])


# =========================================================================== Kickoff 43, Job 1: the map
def k43_map(rec: dict) -> dict:
    """The whole-chip map as Kickoff 35 computed a day (the package's own functions), the dead-pair filter, the map
    rule with r_AB not measured (circuit A only: DIAGNOSTIC cannot be reached), and the couplers with k above 1.2."""
    day = ar.full_chip_day(rec)
    pd, lv = persistence_day(day), ar.full_chip_levels(day)
    level, k, x = np.array(lv["P_no"]), np.array(pd["k"]), np.array(day["x"])
    k1, k2 = np.array(pd["k_first_copies"]), np.array(pd["k_second_copies"])
    keep = level >= DEAD_FLOOR
    rs_f, rkx_f = _corr(k1[keep], k2[keep]), _corr(k[keep], x[keep])
    nan = float("nan")
    edges = [list(e) for e in day["edges"]]
    return {
        "edges": edges,
        "k": pd["k"],
        "k_first": pd["k_first_copies"],
        "k_second": pd["k_second_copies"],
        **lv,
        "mean_k": pd["mean_k"],
        "sd_k_between_edges": pd["sd_k_between_edges"],
        "mean_shot_se": pd["shot_noise_sd"],
        "r_split": pd["r_split"],
        "reliability_spearman_brown": pd["reliability"],
        "r_k_x": pd["r_k_x"],
        "x": day["x"],
        "plain_level": level.tolist(),
        "dead_pair_floor": DEAD_FLOOR,
        "dead_pairs": [edges[i] for i in np.flatnonzero(~keep)],
        "n_working_pairs": int(keep.sum()),
        "after_dead_pair_filter": {"r_split": rs_f, "r_k_x": rkx_f},
        "map_verdict_all_edges": _nan_to_none(
            map_verdict(pd["r_split"]["pearson"], nan, nan, nan, pd["r_k_x"]["pearson"]).as_dict()
        ),
        "map_verdict_after_filter": _nan_to_none(map_verdict(rs_f, nan, nan, nan, rkx_f).as_dict()),
        "usable_couplers_k_above_1p2": [
            [edges[i], float(k[i]), float(level[i])] for i in range(len(k)) if keep[i] and x[i] < 1.0 and k[i] > 1.2
        ],
    }


# =========================================================================== Kickoff 43: the placements
def _chains(adj: dict, w: int) -> list[tuple]:
    """Every simple chain of w qubits, once each (first end below the last)."""
    out = []

    def dfs(p, seen):
        if len(p) == w:
            if p[0] < p[-1]:
                out.append(tuple(p))
            return
        for n in sorted(adj[p[-1]]):
            if n not in seen:
                seen.add(n)
                p.append(n)
                dfs(p, seen)
                p.pop()
                seen.discard(n)

    for q in sorted(adj):
        dfs([q], {q})
    return out


def _couplers(chain) -> list[tuple]:
    return [tuple(sorted((chain[i], chain[i + 1]))) for i in range(len(chain) - 1)]


def k43_placements(map_rec: dict, run_rec: dict, coupling_map: dict) -> dict:
    """Kickoff 43's map placement, recomputed: an exhaustive search over every simple chain of w qubits on ibm_fez's
    coupling map, both orientations, scored by Amendment A1's rule (the gate-weighted sum of |1 - k|, weights the CZ
    count on each line position), after excluding any chain with a coupler below the dead-pair floor or with a
    published CZ error of 1.0; ties by the lower sum of the published score x. The as-fixed rule (1 - k) and the capped
    rule (1 - min(k, 1)) are searched the same way, beside it. k and the plain level are this record's map, recomputed
    from its counts; the published figures are the map job's (Job 2 was built 4 minutes later, under the same published
    calibration stamp, and the figures it recorded on every chosen chain are the same). Beside each cell's two chains:
    their scores under all three rules, their x, and the k and plain level on their couplers."""
    m = k43_map(map_rec)
    kmap = {tuple(sorted(e)): v for e, v in zip(m["edges"], m["k"])}
    level = {tuple(sorted(e)): v for e, v in zip(m["edges"], m["P_no"])}
    cz = {tuple(sorted(r["edge"])): r["cz_error"] for r in map_rec["published_at_submission"]}
    ro = {q: v for r in map_rec["published_at_submission"] for q, v in zip(r["edge"], r["readout_error"])}
    adj = defaultdict(set)
    for a, b in coupling_map["edges"]:
        adj[a].add(b)
        adj[b].add(a)
    cache: dict = {}
    out = {}
    for cell, row in run_rec["placements"].items():
        w, wts = row["w"], row["cz_per_line_position"]
        chains = cache.setdefault(w, _chains(adj, w))

        def search(rule, chains=chains, wts=wts):
            best, n_scored, n_excluded = None, 0, 0
            for ch in chains:
                es = _couplers(ch)
                if any(e not in kmap or level[e] < DEAD_FLOOR or cz.get(e, 1.0) >= 1.0 for e in es):
                    n_excluded += 1
                    continue
                xs = sum(cz[e] + ro[e[0]] + ro[e[1]] for e in es)
                for orient in (ch, ch[::-1]):
                    s = sum(wt * SCORES[rule](kmap[e]) for wt, e in zip(wts, _couplers(orient)))
                    n_scored += 1
                    if best is None or s < best[0] - 1e-12 or (abs(s - best[0]) <= 1e-12 and xs < best[1]):
                        best = (s, xs, list(orient))
            return {
                "rule": rule,
                "chain": best[2],
                "score": best[0],
                "sum_x": best[1],
                "n_orientations_scored": n_scored,
                "n_chains_excluded": n_excluded,
            }

        def beside(chain, wts=wts):
            es = _couplers(chain)
            return {
                "x_sum": sum(cz.get(e, 1.0) + ro[e[0]] + ro[e[1]] for e in es),
                "map_scores": {r: sum(wt * f(kmap[e]) for wt, e in zip(wts, es)) for r, f in SCORES.items()},
                "k_on_couplers": [kmap[e] for e in es],
                "plain_level_on_couplers": [level[e] for e in es],
            }

        mp = search("distance")
        cal = row["calibration"]["chain"]
        out[cell] = {
            "map": {**mp, **beside(mp["chain"])},
            "calibration": beside(cal),
            "beside_not_run": {r: search(r) for r in ("as_fixed", "capped")},
            "same_chain": mp["chain"] == cal,
            "same_qubit_set": sorted(mp["chain"]) == sorted(cal),
        }
    return out


# =========================================================================== Kickoff 43, Job 2: F, G and the verdict
def _readout_adjusted(dist: dict, clbits, errs) -> dict:
    """Invert a per-bit confusion matrix on the whole outcome distribution (keys ordered as outcome() writes them);
    errs[i] = (P(read 1 | prepared 0), P(read 0 | prepared 1)) for clbits[i]. Negative entries clipped, renormalised.
    An adjustment from published figures, not a measurement."""
    n = len(clbits)
    v = np.zeros(2**n)
    for k, p in dist.items():
        v[int(k, 2)] += p
    t = v.reshape((2,) * n)
    for i in range(n):
        axis = n - 1 - i
        p10, p01 = errs[i]
        M = np.array([[1 - p10, p01], [p10, 1 - p01]])
        t = np.moveaxis(np.tensordot(np.linalg.inv(M), t, axes=([1], [axis])), 0, axis)
    v = np.clip(t.reshape(-1), 0, None)
    v /= v.sum()
    return {format(i, f"0{n}b"): float(x) for i, x in enumerate(v) if x > 0}


def _fidelity(p: dict, q: dict) -> float:
    return float(sum(np.sqrt(p.get(k, 0.0) * q[k]) for k in q) ** 2)


def k43_reuse(rec: dict) -> dict:
    """Kickoff 43, section 5 and what it reports beside the verdict: F per cell (the squared Hellinger overlap of the
    cell's pooled counts with the circuit's exact ideal, uncorrected for readout), G per circuit and its mean, the 90%
    bootstrap intervals (10,000 resamples, seed 4343043: copies drawn with replacement within each cell, each redrawn
    from a multinomial at its observed frequencies), the verdict (margin 0.005), the readout-adjusted F from the
    published readout errors, the copy-to-copy variances and the interval widths against shot noise alone."""
    circ, shots, delta = rec["circuits"], rec["meta"]["shots_per_circuit"], rec["fixed_before_the_data"]["margin"]
    cells: dict = {}
    for o, cts in zip(rec["order"], rec["counts"]):
        cells.setdefault(tuple(o["cell"]), []).append((o["copy"], cts))
    support = {c: sorted(circ[c]["ideal"]) for c in CIRCS}
    q = {c: np.array([circ[c]["ideal"][k] for k in support[c]]) for c in CIRCS}
    V, full = {}, {}
    for key, copies in cells.items():
        c = key[0]
        rows, pooled = [], {}
        for _, cts in sorted(copies, key=lambda z: z[0]):
            d: dict = {}
            for b, n in cts.items():
                k = outcome(b, circ[c]["measured_clbits"])
                d[k] = d.get(k, 0) + n
                pooled[k] = pooled.get(k, 0) + n
            vec = [d.get(k, 0) for k in support[c]]
            rows.append(vec + [sum(d.values()) - sum(vec)])
        V[key], full[key] = np.array(rows, float), pooled

    def F_of(vc, c):
        return np.sqrt(vc[..., :-1] / vc.sum(-1, keepdims=True) * q[c]).sum(-1) ** 2

    F = {key: float(F_of(v.sum(0), key[0])) for key, v in V.items()}
    rng = np.random.default_rng(rec["fixed_before_the_data"]["bootstrap"]["seed"])
    boot = {key: np.empty(N_BOOT) for key in V}
    shot_boot = {key: np.empty(N_BOOT) for key in V}
    for key in sorted(V):
        v, c = V[key], key[0]
        freq, pooled = v / v.sum(1, keepdims=True), v.sum(0)
        for s in range(0, N_BOOT, 500):
            r = min(500, N_BOOT - s)
            idx = rng.integers(0, v.shape[0], size=(r, v.shape[0]))
            boot[key][s : s + r] = F_of(rng.multinomial(shots, freq[idx]).sum(1), c)
            shot_boot[key][s : s + r] = F_of(rng.multinomial(int(pooled.sum()), pooled / pooled.sum(), size=r), c)

    def summary(fn):
        b, sb = fn(boot), fn(shot_boot)
        lo, hi = pct(b)
        slo, shi = pct(sb)
        return {
            "point": float(fn(F)),
            "ci90": [lo, hi],
            "width": hi - lo,
            "shot_only_boot_ci90": [slo, shi],
            "shot_only_boot_width": shi - slo,
        }

    def G(m):
        return lambda S: np.mean([S[(c, m, "map")] - S[(c, m, "calibration")] for c in CIRCS], axis=0)

    def Gc(c, m):
        return lambda S: S[(c, m, "map")] - S[(c, m, "calibration")]

    out = {
        "G_reuse": summary(G("reuse")),
        "G_no_reuse": summary(G("no_reuse")),
        "Delta": summary(lambda S: G("reuse")(S) - G("no_reuse")(S)),
    }
    N = 5 * shots
    for name, ms in (("G_reuse", ("reuse",)), ("G_no_reuse", ("no_reuse",)), ("Delta", COMPS)):
        var = sum(F[(c, m, p)] * (1 - F[(c, m, p)]) / N for c in CIRCS for m in ms for p in PLACES) / 16
        out[name]["shot_only_formula_width"] = float(2 * Z90 * np.sqrt(var))
        out[name]["ratio_width_to_shot_only_formula"] = out[name]["width"] / out[name]["shot_only_formula_width"]
        out[name]["ratio_width_to_shot_only_boot"] = out[name]["width"] / out[name]["shot_only_boot_width"]
    lo, hi = out["G_reuse"]["ci90"]
    verdict = "NOT USEFUL FOR REUSE" if hi < delta else ("USEFUL FOR REUSE" if lo > 0 else "NOT SETTLED")
    per = {
        c: {
            "G_reuse": summary(Gc(c, "reuse")),
            "G_no_reuse": summary(Gc(c, "no_reuse")),
            "Delta": summary(lambda S, c=c: Gc(c, "reuse")(S) - Gc(c, "no_reuse")(S)),
        }
        for c in CIRCS
    }
    res_cells = {}
    for key in sorted(V):
        c, m, p = key
        fc = F_of(V[key], c)
        shot_var = float(np.mean(fc * (1 - fc)) / shots)
        clbits = circ[c]["measured_clbits"]
        line_of = circ[c][m]["measuring_line_of_clbit"]
        row = rec["placements"][f"{c}|{m}"][p]
        errs = []
        for cb in clbits:
            L = line_of[str(cb)]
            a, e = row["published_readout_asym"][L], row["published_readout_error"][L]
            errs.append((a["p10"], a["p01"]) if a else (e, e))
        tot = sum(full[key].values())
        dist = {k: v / tot for k, v in full[key].items()}
        res_cells[f"{c}|{m}|{p}"] = {
            "F": F[key],
            "F_per_copy": fc.tolist(),
            "copy_to_copy_var": float(np.var(fc, ddof=1)),
            "shot_only_var_per_copy": shot_var,
            "copy_var_ratio_to_shot": float(np.var(fc, ddof=1) / shot_var) if shot_var > 0 else None,
            "F_boot_ci90": pct(boot[key]),
            "F_readout_adjusted": _fidelity(_readout_adjusted(dist, clbits, errs), circ[c]["ideal"]),
            "chain": row["chain"],
            "shots_pooled": int(tot),
        }
    ro = {
        m: float(
            np.mean(
                [
                    res_cells[f"{c}|{m}|map"]["F_readout_adjusted"]
                    - res_cells[f"{c}|{m}|calibration"]["F_readout_adjusted"]
                    for c in CIRCS
                ]
            )
        )
        for m in COMPS
    }
    hw = out["G_reuse"]["width"] / 2
    return {
        "cells": res_cells,
        **out,
        "verdict": verdict,
        "verdict_conditions": {
            "G_reuse_ci90_entirely_below_delta": hi < delta,
            "G_reuse_ci90_entirely_above_0": lo > 0,
        },
        "per_circuit": per,
        "n_circuits_Delta_positive": sum(per[c]["Delta"]["point"] > 0 for c in CIRCS),
        "same_chain": {f"{c}|{m}": rec["placements"][f"{c}|{m}"]["same_chain"] for c in CIRCS for m in COMPS},
        "readout_adjusted_G": {
            "G_reuse": ro["reuse"],
            "G_no_reuse": ro["no_reuse"],
            "Delta": ro["reuse"] - ro["no_reuse"],
        },
        "rerun_shots_per_cell_for_half_width_delta_over_2": int(np.ceil(N * (hw / (delta / 2)) ** 2)),
    }


def k43_resets_on(rec: dict) -> dict:
    """Per cell and placement, how many resets fall on each physical qubit: the circuit's resets per line position,
    placed on the chain."""
    out = {}
    for cell, row in rec["placements"].items():
        c, m = cell.split("|")
        per_line = rec["circuits"][c][m]["resets_per_line"]
        out[cell] = {
            p: {str(q): n for q, n in sorted(zip(row[p]["chain"], per_line), key=lambda z: -z[1]) if n} for p in PLACES
        }
    return out


# =========================================================================== Kickoff 44: the reuse-cost probe
def k44_probe(rec: dict) -> dict:
    """Kickoff 44, sections 3, 4 and 6: per instance (round, orientation, pair) and per qubit the mid-circuit error
    e_m, the levels L_R and L_R0, the reset residual eps = (L_R0 - L_R) / 0.9621 and the cost c = e_m + eps; the
    verdict on D = mean c over T minus mean c over C (margin 0.02; bootstrap 10,000, seed 4444, the two copies drawn
    with replacement within each circuit and each redrawn from a multinomial over the bits of the pairs that enter D);
    the probe's own verdict; and the lines beside them, among them the correction found after the data (the control
    idles b in |1>, so its decay, 1 - exp(-tau/T1) with the published T1, biases eps low)."""
    circs, counts, pub = rec["circuits"], rec["counts"], rec["published_at_build"]
    T, C = rec["sets"]["T"], rec["sets"]["C"]
    margin, seed = rec["fixed_before_the_data"]["delta_c"], rec["fixed_before_the_data"]["bootstrap"]["seed"]

    def pair_bits(key, i):
        b = _bits(key)
        return b[3 * i], b[3 * i + 1], b[3 * i + 2]

    tally = {}
    for r, cts in zip(circs, counts):
        for i in range(r["n_pairs"]):
            m0 = p11 = tot = 0
            for key, v in cts.items():
                m, f, s = pair_bits(key, i)
                tot += v
                m0 += v * (m == "0")
                p11 += v * (f == "1" and s == "1")
            tally[(r["round"], r["orientation"], r["kind"], r["offset"], r["copy"], i)] = (m0, p11, tot)
    first = {
        (r["round"], r["orientation"]): r for r in circs if r["copy"] == 1 and r["kind"] == "R" and r["offset"] == "no"
    }
    inst = []
    for (rn, o), r in first.items():
        for i, (f, s) in enumerate(r["pairs"]):
            b, a = (f, s) if o == "b_first" else (s, f)

            def g(kind, off, copies, field, rn=rn, o=o, i=i):
                num = sum(tally[(rn, o, kind, off, c, i)][field] for c in copies)
                den = sum(tally[(rn, o, kind, off, c, i)][2] for c in copies)
                return num / den, den

            row = {"round": rn, "orientation": o, "pair": [f, s], "b": b, "a": a}
            for lab, copies in (("pooled", (1, 2)), ("copy1", (1,)), ("copy2", (2,))):
                em_no, nn = g("R", "no", copies, 0)
                em_off, no_ = g("R", "off", copies, 0)
                e_m = (em_no * nn + em_off * no_) / (nn + no_)
                LR, nR = g("R", "no", copies, 1)
                LR0, nR0 = g("R0", "no", copies, 1)
                PRoff, _ = g("R", "off", copies, 1)
                PR0off, _ = g("R0", "off", copies, 1)
                eps = (LR0 - LR) / DLEVEL
                d = {
                    "e_m": e_m,
                    "L_R": LR,
                    "L_R0": LR0,
                    "dL": LR0 - LR,
                    "eps": eps,
                    "c": e_m + eps,
                    "k_R": (PRoff - LR) / GAP_A,
                    "k_R0": (PR0off - LR0) / GAP_A,
                }
                if lab == "pooled":
                    se_em = np.sqrt(e_m * (1 - e_m) / (nn + no_))
                    se_eps = np.sqrt(LR * (1 - LR) / nR + LR0 * (1 - LR0) / nR0) / DLEVEL
                    d.update(
                        {
                            "se_e_m": float(se_em),
                            "se_eps": float(se_eps),
                            "se_c": float(np.hypot(se_em, se_eps)),
                            "se_L": float(np.sqrt(LR * (1 - LR) / nR)),
                        }
                    )
                row[lab] = d
            inst.append(row)
    byq = defaultdict(list)
    for k, row in enumerate(inst):
        byq[row["b"]].append(k)
    qtab = {}
    for qb, ks in byq.items():
        e = {
            f: float(np.mean([inst[k]["pooled"][f] for k in ks]))
            for f in ("e_m", "eps", "c", "L_R", "L_R0", "dL", "k_R", "k_R0")
        }
        for h in ("copy1", "copy2"):
            for f in ("e_m", "eps", "c"):
                e[f"{h}_{f}"] = float(np.mean([inst[k][h][f] for k in ks]))
        for f in ("c", "e_m", "eps"):
            e[f"se_{f}"] = float(np.sqrt(sum(inst[k]["pooled"][f"se_{f}"] ** 2 for k in ks)) / len(ks))
        e["n_instances"] = len(ks)
        e.update({f: pub[str(qb)][f] for f in ("readout_error", "init_error", "prob_meas0_prep1")})
        qtab[qb] = e
    order = sorted(qtab, key=lambda z: -qtab[z]["c"])
    for rank, qb in enumerate(order, 1):
        qtab[qb]["rank_c_worst_first"] = rank
    quarter = int(np.ceil(len(order) / 4))

    def pt(f):
        return float(np.mean([qtab[z][f] for z in T]) - np.mean([qtab[z][f] for z in C]))

    rel = defaultdict(set)
    for qb in T + C:
        for k in byq[qb]:
            key = (inst[k]["round"], inst[k]["orientation"])
            rel[key].add(first[key]["pairs"].index(inst[k]["pair"]))
    groups = defaultdict(dict)
    for r, cts in zip(circs, counts):
        key = (r["round"], r["orientation"])
        if key not in rel:
            continue
        idx = sorted(rel[key])
        marg = defaultdict(int)
        for k, v in cts.items():
            marg[tuple(pair_bits(k, i) for i in idx)] += v
        outs = list(marg)
        w = np.array([marg[o] for o in outs], float)
        X_m0 = np.array([[o[j][0] == "0" for j in range(len(idx))] for o in outs], float)
        X_11 = np.array([[o[j][1] == "1" and o[j][2] == "1" for j in range(len(idx))] for o in outs], float)
        groups[(key, r["kind"], r["offset"])][r["copy"]] = (idx, w, X_m0, X_11)
    rng = np.random.default_rng(seed)
    bm0, bp11, bn, sm0, sp11 = {}, {}, {}, {}, {}
    for (key, kind, off), cp in groups.items():
        idx = cp[1][0]
        tot = {c: cp[c][1].sum() for c in (1, 2)}
        acc_m0, acc_11, acc_n = np.zeros((N_BOOT, len(idx))), np.zeros((N_BOOT, len(idx))), np.zeros(N_BOOT)
        sacc_m0, sacc_11 = np.zeros((N_BOOT, len(idx))), np.zeros((N_BOOT, len(idx)))
        for slot in range(2):
            pick = rng.integers(1, 3, size=N_BOOT)
            for c in (1, 2):
                _, w, Xm, X1 = cp[c]
                sel = pick == c
                n = int(sel.sum())
                if n:
                    dr = rng.multinomial(int(tot[c]), w / w.sum(), size=n)
                    acc_m0[sel] += dr @ Xm
                    acc_11[sel] += dr @ X1
                    acc_n[sel] += tot[c]
            _, w, Xm, X1 = cp[slot + 1]
            dr = rng.multinomial(int(tot[slot + 1]), w / w.sum(), size=N_BOOT)
            sacc_m0 += dr @ Xm
            sacc_11 += dr @ X1
        for j, i in enumerate(idx):
            bm0[(key, kind, off, i)], bp11[(key, kind, off, i)], bn[(key, kind, off, i)] = (
                acc_m0[:, j],
                acc_11[:, j],
                acc_n,
            )
            sm0[(key, kind, off, i)], sp11[(key, kind, off, i)] = sacc_m0[:, j], sacc_11[:, j]
    nshot = {g: sum(cp[c][1].sum() for c in (1, 2)) for g, cp in groups.items()}

    def qboot(qb, m0, p11, nn):
        vals = {"e_m": [], "eps": [], "c": []}
        for k in byq[qb]:
            key = (inst[k]["round"], inst[k]["orientation"])
            i = first[key]["pairs"].index(inst[k]["pair"])
            n_no, n_off = nn(key, "R", "no", i), nn(key, "R", "off", i)
            em = (m0[(key, "R", "no", i)] + m0[(key, "R", "off", i)]) / (n_no + n_off)
            eps = (p11[(key, "R0", "no", i)] / nn(key, "R0", "no", i) - p11[(key, "R", "no", i)] / n_no) / DLEVEL
            vals["e_m"].append(em)
            vals["eps"].append(eps)
            vals["c"].append(em + eps)
        return {f: np.mean(v, axis=0) for f, v in vals.items()}

    fullb = {qb: qboot(qb, bm0, bp11, lambda key, kind, off, i: bn[(key, kind, off, i)]) for qb in T + C}
    shotb = {qb: qboot(qb, sm0, sp11, lambda key, kind, off, i: nshot[(key, kind, off)]) for qb in T + C}
    D = {}
    for f in ("c", "e_m", "eps"):
        b = np.mean([fullb[z][f] for z in T], axis=0) - np.mean([fullb[z][f] for z in C], axis=0)
        s = np.mean([shotb[z][f] for z in T], axis=0) - np.mean([shotb[z][f] for z in C], axis=0)
        lo, hi = pct(b)
        slo, shi = pct(s)
        D[f] = {
            "point": pt(f),
            "ci90": [lo, hi],
            "width": hi - lo,
            "shot_only_ci90": [slo, shi],
            "shot_only_width": shi - slo,
            "ratio_width_to_shot_only": (hi - lo) / (shi - slo),
        }
    lo, hi = D["c"]["ci90"]
    qs = sorted(qtab)
    probe = {}
    for name, f, pred in (
        ("e_m", "e_m", "readout_error"),
        ("eps", "eps", "init_error"),
        ("eps_vs_readout_all_qubits_beside", "eps", "readout_error"),
    ):
        qq = [z for z in qs if qtab[z][pred] is not None]
        h1 = np.array([qtab[z][f"copy1_{f}"] for z in qq])
        h2 = np.array([qtab[z][f"copy2_{f}"] for z in qq])
        zz = np.array([qtab[z][pred] for z in qq], float)
        rs, rp = _corr(h1, h2), _corr([qtab[z][f] for z in qq], zz)
        rxz, ryz = _corr(h1, zz), _corr(h2, zz)
        pr = float((rs - rxz * ryz) / np.sqrt((1 - rxz**2) * (1 - ryz**2)))
        v = "NOISE" if rs < 0.5 else ("REDUNDANT" if abs(rp) >= 0.5 and pr < 0.3 else "DIAGNOSTIC")
        probe[name] = {
            "verdict": v,
            "r_split": rs,
            "spearman_split": _corr(np.argsort(np.argsort(h1)), np.argsort(np.argsort(h2))),
            "predictor": pred,
            "r_with_predictor": rp,
            "partial_split_given_predictor": pr,
            "n_qubits": len(qq),
            "qubits_without_predictor": [z for z in qs if qtab[z][pred] is None],
        }
    cv = np.array([row["copy1"]["c"] - row["copy2"]["c"] for row in inst])
    shot_var_diff = np.array([4 * row["pooled"]["se_c"] ** 2 for row in inst])
    fields = ("e_m", "eps", "c", "L_R", "L_R0", "k_R", "k_R0")
    # after the data: the control's decay in |1> over its delay, from the published T1
    decay = {z: 1 - math.exp(-TAU_R0 / pub[str(z)]["T1"]) for z in qs}
    eps_adj = {z: qtab[z]["eps"] + decay[z] for z in qs}
    ratio = sorted(
        ((z, qtab[z]["e_m"] / pub[str(z)]["readout_error"], qtab[z]["e_m"], pub[str(z)]["readout_error"]) for z in qs),
        key=lambda t: -t[1],
    )
    return {
        "verdict": "NOT SUPPORTED" if hi < margin else ("SUPPORTED" if lo > 0 else "NOT SETTLED"),
        "verdict_conditions": {"D_ci90_entirely_below_delta_c": hi < margin, "D_ci90_entirely_above_0": lo > 0},
        "D": D,
        "T": T,
        "C": C,
        "T_C_table": {
            str(z): {
                **{
                    f: qtab[z][f]
                    for f in (
                        "e_m",
                        "eps",
                        "c",
                        "se_c",
                        "L_R",
                        "L_R0",
                        "k_R",
                        "k_R0",
                        "n_instances",
                        "rank_c_worst_first",
                        "readout_error",
                        "init_error",
                    )
                },
                "set": "T" if z in T else "C",
            }
            for z in T + C
        },
        "q142_in_worst_quarter_of_c": qtab[142]["rank_c_worst_first"] <= quarter,
        "q117_in_worst_quarter_of_c": qtab[117]["rank_c_worst_first"] <= quarter,
        "worst_quarter_size": quarter,
        "n_tested_qubits": len(order),
        "probe_verdict": probe,
        "copy_to_copy_ratio_to_shot": float(np.mean(cv**2) / np.mean(shot_var_diff)),
        "chip_summary": {
            f: {
                "mean": float(np.mean([qtab[z][f] for z in qs])),
                "median": float(np.median([qtab[z][f] for z in qs])),
                "min": float(np.min([qtab[z][f] for z in qs])),
                "max": float(np.max([qtab[z][f] for z in qs])),
            }
            for f in fields
        },
        "per_qubit_sorted_by_c": [{"qubit": z, **qtab[z]} for z in order],
        "per_instance": inst,
        "beside_after_data": {
            "t1_decay_in_R0": {
                "tau_s": TAU_R0,
                "mean_decay_prob": float(np.mean([decay[z] for z in qs])),
                "median_eps_raw": float(np.median([qtab[z]["eps"] for z in qs])),
                "median_eps_T1_adjusted": float(np.median([eps_adj[z] for z in qs])),
                "r_eps_with_minus_decay_prob": _corr([qtab[z]["eps"] for z in qs], [-decay[z] for z in qs]),
                "D_c_with_T1_adjusted_eps": float(
                    np.mean([qtab[z]["c"] + decay[z] for z in T]) - np.mean([qtab[z]["c"] + decay[z] for z in C])
                ),
                "per_qubit_T_C": {
                    str(z): {
                        "T1_us": pub[str(z)]["T1"] * 1e6,
                        "decay_prob": decay[z],
                        "eps_T1_adjusted": eps_adj[z],
                        "c_T1_adjusted": qtab[z]["c"] + decay[z],
                    }
                    for z in T + C
                },
            },
            "e_m_over_published_readout": {
                "median": float(np.median([t[1] for t in ratio])),
                "top8": [list(t) for t in ratio[:8]],
                "rank_of_142": [t[0] for t in ratio].index(142) + 1,
            },
        },
    }


# =========================================================================== Kickoffs 45 to 47: Part A, the circuit
def part_a_cells(rec: dict, xor5: dict, cells, seed: int) -> tuple[dict, dict]:
    """F per cell for Kickoff 43's XOR_5 reuse circuit (Kickoff 43's method: pooled copies, the squared Hellinger
    overlap with the exact ideal, uncorrected), its 90% bootstrap interval (10,000 resamples, copies with replacement
    within the cell, each redrawn from a multinomial), and the class: LOW if the interval lies entirely below 0.3, HIGH
    if entirely above 0.6, MIDDLE otherwise. Returns the cells and their bootstrap draws."""
    clb, ideal = xor5["measured_clbits"], xor5["ideal"]
    sup = sorted(ideal)
    q = np.array([ideal[k] for k in sup])
    rows = defaultdict(list)
    for lab, cts in zip(rec["labels"], rec["counts"]):
        if lab["part"] != "A":
            continue
        d: dict = defaultdict(int)
        for key, v in cts.items():
            d[outcome(key, clb)] += v
        vec = [d.get(k, 0) for k in sup]
        rows[lab["cell"]].append(vec + [sum(d.values()) - sum(vec)])

    def F(V):
        return np.sqrt(V[..., :-1] / V.sum(-1, keepdims=True) * q).sum(-1) ** 2

    rng = np.random.default_rng(seed)
    out, boots = {}, {}
    for cell in cells:
        V = np.array(rows[cell], float)
        freq = V / V.sum(1, keepdims=True)
        boot = np.empty(N_BOOT)
        for s in range(0, N_BOOT, 1000):
            r = min(1000, N_BOOT - s)
            idx = rng.integers(0, V.shape[0], size=(r, V.shape[0]))
            boot[s : s + r] = F(rng.multinomial(int(V[0].sum()), freq[idx]).sum(1))
        lo, hi = pct(boot)
        fc = F(V)
        boots[cell] = boot
        out[cell] = {
            "F": float(F(V.sum(0))),
            "ci90": [lo, hi],
            "F_per_copy": fc.tolist(),
            "copy_to_copy_var": float(np.var(fc, ddof=1)),
            "class": "LOW" if hi < 0.3 else ("HIGH" if lo > 0.6 else "MIDDLE"),
            "shots": int(V.sum()),
        }
    return out, boots


# =========================================================================== Kickoff 45
K45_KINDS = ("P0", "P1", "I1", "I2", "K1", "K2", "K3")


def k45_collapse(rec: dict, xor5: dict) -> dict:
    """Kickoff 45. Part A: the collapse (REPEATS if cell A's interval lies entirely below 0.3, RECOVERED if entirely
    above 0.6) and the fixed patterns. Part B, per qubit, pooled over the two mirror copies: the excess idle loss
    x(tau) = [P1 - I(tau)] - P1 (1 - exp(-tau/T1)), the residual after k retirements r_k = P(final 1 | Kk) - P0, and the
    mid-circuit errors; H_idle on x(10 us) and H_repeat on r_3 (margin 0.02; bootstrap 10,000, seed 4545)."""
    fixed = rec["fixed_before_the_data"]
    T, C, margin = rec["sets"]["T"], rec["sets"]["C"], fixed["margin"]
    seed_a, seed_b = fixed["bootstrap"]["seed_A"], fixed["bootstrap"]["seed_B"]
    cells, _ = part_a_cells(rec, xor5, sorted({lab["cell"] for lab in rec["labels"] if lab["part"] == "A"}), seed_a)
    cl = {c: v["class"] for c, v in cells.items()}
    A = cells["A"]
    collapse = "REPEATS" if A["ci90"][1] < 0.3 else ("RECOVERED" if A["ci90"][0] > 0.6 else "NOT SETTLED")
    patterns = []
    if collapse == "REPEATS":
        if cl["B"] == "HIGH":
            patterns.append(
                "B HIGH: the collapse follows the orientation: the twice-retired line on 142 (or 142 retired twice) "
                "is the cause"
            )
        if cl["B"] == "LOW" and cl["E"] == "HIGH":
            patterns.append("B LOW, E HIGH: the collapse needs 142 and 144 in the chain together, not 141")
        if cl["B"] == "LOW" and cl["E"] == "LOW":
            patterns.append("B LOW, E LOW: the region 141 to 144 fails under reuse whichever way the lines sit")
        if cl["D"] == "LOW" or cl["C"] == "LOW":
            patterns.append(
                "D LOW or C LOW: the circuit fails broadly that day, not only in the region; the region reading is "
                "withdrawn"
            )
        if cl["F"] == "LOW":
            patterns.append("F LOW: the region has degraded even without reuse; Kickoff 43's contrast no longer holds")
        if not patterns:
            patterns.append("no fixed pattern holds: reported as observed, without a reading")
    pub = rec["published_at_build"]
    n = len(pub)
    tau = {k: v * rec["tau_dt"]["dt_s"] for k, v in (("I1", rec["tau_dt"]["tau1"]), ("I2", rec["tau_dt"]["tau2"]))}
    copies = defaultdict(list)
    for lab, cts in zip(rec["labels"], rec["counts"]):
        if lab["part"] == "B":
            copies[lab["kind"]].append((lab["copy"], cts))
    copies = {k: [c for _, c in sorted(v, key=lambda z: z[0])] for k, v in copies.items()}
    nb = {k: (int(k[1]) + 1 if k.startswith("K") else 1) for k in K45_KINDS}

    def bitmat(cts, kind, qubits):
        """The bits of these qubits (each qubit's nb bits) for every outcome, in the counts' own order."""
        keys = [k.replace(" ", "") for k in cts]
        width = len(keys[0])
        B = np.frombuffer("".join(keys).encode(), np.uint8).reshape(len(keys), width)[:, ::-1] - ord("0")
        cols = [q * nb[kind] + j for q in qubits for j in range(nb[kind])]
        return B[:, cols].astype(np.int8), np.array(list(cts.values()), float)

    allq = list(range(n))
    S = {}
    for kind in K45_KINDS:
        acc, tot = np.zeros(n * nb[kind]), 0
        for cts in copies[kind]:
            X, w = bitmat(cts, kind, allq)
            acc += w @ X
            tot += w.sum()
        S[kind] = (acc / tot).reshape(n, nb[kind])
    half = {}
    for h in (0, 1):
        half[h] = {}
        for kind in K45_KINDS:
            X, w = bitmat(copies[kind][h], kind, allq)
            half[h][kind] = ((w @ X) / w.sum()).reshape(n, nb[kind])
    T1 = np.array([pub[str(i)]["T1"] for i in range(n)], float)

    def quantities(St, T1v, ax):
        P0, P1 = St["P0"][..., 0], St["P1"][..., 0]
        out = {"P0": P0, "P1": P1, "I1": St["I1"][..., 0], "I2": St["I2"][..., 0]}
        for t in ("I1", "I2"):
            out[f"x_{t}"] = (P1 - St[t][..., 0]) - P1 * (1 - np.exp(-tau[t] / T1v))
        for k in (1, 2, 3):
            out[f"r_{k}"] = St[f"K{k}"][..., k] - P0
        out["K3_mid_err"] = 1 - St["K3"][..., :3]
        out["first_mid_err"] = np.mean([1 - St[f"K{k}"][..., 0] for k in (1, 2, 3)], axis=0)
        return out

    Q = quantities(S, T1, None)
    Qh = {h: quantities(half[h], T1, None) for h in (0, 1)}
    idx = sorted(set(T + C + [125, 124, 123]))
    T1s = T1[idx]
    mats = {k: [bitmat(c, k, idx) for c in copies[k]] for k in K45_KINDS}
    rng = np.random.default_rng(seed_b)
    boot, sboot = {}, {}
    for k in K45_KINDS:
        boot[k], sboot[k] = np.zeros((N_BOOT, len(idx), nb[k])), np.zeros((N_BOOT, len(idx), nb[k]))
        for s in range(0, N_BOOT, 1000):
            r = min(1000, N_BOOT - s)
            acc, n_acc = np.zeros((r, len(idx) * nb[k])), np.zeros(r)
            sacc, sn = np.zeros((r, len(idx) * nb[k])), np.zeros(r)
            for slot in range(2):
                pick = rng.integers(0, 2, size=r)
                for c in (0, 1):
                    sel = pick == c
                    if sel.any():
                        X, w = mats[k][c]
                        dr = rng.multinomial(int(w.sum()), w / w.sum(), size=int(sel.sum()))
                        acc[sel] += dr @ X
                        n_acc[sel] += w.sum()
                X, w = mats[k][slot]
                dr = rng.multinomial(int(w.sum()), w / w.sum(), size=r)
                sacc += dr @ X
                sn += w.sum()
            boot[k][s : s + r] = (acc / n_acc[:, None]).reshape(r, len(idx), nb[k])
            sboot[k][s : s + r] = (sacc / sn[:, None]).reshape(r, len(idx), nb[k])
    QB, QS = quantities(boot, T1s, None), quantities(sboot, T1s, None)
    pos = {q: i for i, q in enumerate(idx)}
    verdicts = {}
    for name, f in (("H_idle", "x_I2"), ("H_repeat", "r_3")):
        point = float(np.mean([Q[f][q] for q in T]) - np.mean([Q[f][q] for q in C]))
        b = QB[f][:, [pos[q] for q in T]].mean(1) - QB[f][:, [pos[q] for q in C]].mean(1)
        sb = QS[f][:, [pos[q] for q in T]].mean(1) - QS[f][:, [pos[q] for q in C]].mean(1)
        lo, hi = pct(b)
        slo, shi = pct(sb)
        verdicts[name] = {
            "quantity": f,
            "D": point,
            "ci90": [lo, hi],
            "shot_only_ci90": [slo, shi],
            "width_ratio": (hi - lo) / (shi - slo),
            "verdict": "NOT SUPPORTED" if hi < margin else ("SUPPORTED" if lo > 0 else "NOT SETTLED"),
            "conditions": {"entirely_below_margin": hi < margin, "entirely_above_0": lo > 0},
        }
    x141, ci141 = Q["x_I1"][141], pct(QB["x_I1"][:, pos[141]])
    table = {}
    for q in idx:
        row = {"set": "T" if q in T else ("C" if q in C else "chain D")}
        for f in ("P0", "P1", "I1", "I2", "x_I1", "x_I2", "r_1", "r_2", "r_3", "first_mid_err"):
            row[f] = float(Q[f][q])
        for f in ("x_I1", "x_I2", "r_1", "r_2", "r_3", "first_mid_err"):
            row[f + "_ci90"] = pct(QB[f][:, pos[q]])
        row["K3_mid_err"] = Q["K3_mid_err"][q].tolist()
        row.update({k: pub[str(q)][k] for k in ("T1", "T2", "readout_error", "init_error")})
        table[str(q)] = row
    chip = [
        {
            "qubit": i,
            **{f: float(Q[f][i]) for f in ("x_I1", "x_I2", "r_1", "r_2", "r_3", "first_mid_err")},
            "K3_mid_err": Q["K3_mid_err"][i].tolist(),
            "P0": float(Q["P0"][i]),
            "P1": float(Q["P1"][i]),
            "T1": pub[str(i)]["T1"],
            "T2": pub[str(i)]["T2"],
            "readout_error": pub[str(i)]["readout_error"],
        }
        for i in range(n)
    ]
    ro142 = pub["142"]["readout_error"]

    def rank(f):
        r = np.argsort(np.argsort(-Q[f]))
        return {str(q): int(r[q] + 1) for q in idx}

    part_b = {
        "verdicts": verdicts,
        "anomaly_141": {"x_I1": float(x141), "ci90": ci141, "repeats": bool(x141 >= 0.05 and ci141[0] > 0.03)},
        "q142_first_mid_err": float(Q["first_mid_err"][142]),
        "q142_readout": ro142,
        "q142_ratio": float(Q["first_mid_err"][142] / ro142),
        "q142_above_5x": bool(Q["first_mid_err"][142] > 5 * ro142),
        "table": table,
        "rank_worst_first": {"x_I2": rank("x_I2"), "r_3": rank("r_3")},
        "split_half_r_whole_chip": {
            f: _corr(Qh[0][f], Qh[1][f]) for f in ("x_I1", "x_I2", "r_1", "r_2", "r_3", "first_mid_err")
        },
        "chip_sorted_by_x_I2": sorted(chip, key=lambda z: -z["x_I2"]),
        "chip_sorted_by_r_3": sorted(chip, key=lambda z: -z["r_3"]),
        "chip_summary": {
            f: {
                "median": float(np.median(Q[f])),
                "mean": float(np.mean(Q[f])),
                "min": float(np.min(Q[f])),
                "max": float(np.max(Q[f])),
            }
            for f in ("x_I1", "x_I2", "r_1", "r_2", "r_3", "first_mid_err", "P0", "P1")
        },
    }
    without141 = [q for q in T if q != 141]
    couplers = {
        c: ["-".join(map(str, sorted(e))) for e in _couplers(v["chain"])] for c, v in rec["cells"].items() if c != "F"
    }
    return {
        "part_A": {"cells": cells, "collapse": collapse, "classes": cl, "patterns": patterns},
        "part_B": part_b,
        "beside_after_data": {
            "D_x_I2_without_141": float(
                np.mean([Q["x_I2"][q] for q in without141]) - np.mean([Q["x_I2"][q] for q in C])
            ),
            "x_I2_138_in_C": float(Q["x_I2"][138]),
            "x_I2_141": float(Q["x_I2"][141]),
            "couplers_by_cell": couplers,
            "q142_P1": float(Q["P1"][142]),
            "q142_published_prob_meas0_prep1": pub["142"]["prob_meas0_prep1"],
            "q142_first_mid_err_k45": float(Q["first_mid_err"][142]),
        },
    }


# =========================================================================== Kickoff 46
K46_TARGET = ((143, 142), (143, 144))
K46_CONTROL = ((131, 130), (131, 132), (131, 138), (124, 123), (124, 125))


def k46_middle(rec: dict, xor5: dict) -> dict:
    """Kickoff 46. Part A: the six chains and the fixed patterns (read only if A is LOW and C is HIGH). Part B, per
    (spectator s, neighbour c), pooled over the two copies: P(s = 0) in S, S1 and S0; d = P0(S1) - P0(S); i = P0(S0) -
    P0(S1); c's mid-circuit error; H_spectator on d (margin 0.05; bootstrap 10,000, seed 4646). Beside, after the
    data: the spectator's P(1) in S0 against what its published T2 (and readout error) predicts over the wait."""
    fixed = rec["fixed_before_the_data"]
    seed_a, seed_b = fixed["bootstrap"]["seed_A"], fixed["bootstrap"]["seed_B"]
    margin = fixed["margin_B"]
    cells, _ = part_a_cells(rec, xor5, ["A", "G", "H", "J", "K", "C"], seed_a)
    cl = {c: v["class"] for c, v in cells.items()}
    gate = None
    if cl["A"] != "LOW":
        gate = "A is not LOW: the collapse did not repeat; cells reported descriptively, Part A not interpreted"
    elif cl["C"] != "HIGH":
        gate = "C is not HIGH: a broad bad hour; Part A not interpreted"
    patterns = []
    if gate is None:
        if cl["G"] == "LOW" and cl["H"] == "LOW" and cl["J"] == "HIGH" and cl["K"] == "HIGH":
            patterns.append(
                "143 as the middle line, the reading made after Kickoff 45: the collapse follows 143 being live "
                "while its neighbours retire"
            )
        if cl["H"] == "LOW" and cl["J"] == "LOW" and cl["G"] == "HIGH":
            patterns.append("coupler 143-144 under reuse, whichever qubit is in the middle")
        if cl["G"] == "HIGH" and cl["H"] == "HIGH":
            patterns.append("142 and 144 together: neither alone, with 143 in the middle, is enough")
        if cl["G"] == "LOW" and cl["H"] == "HIGH" and cl["K"] == "LOW":
            patterns.append("142 retired next to a live neighbour")
        if not patterns:
            patterns.append("no fixed pattern holds: reported as observed, with no reading")
    copies = defaultdict(dict)
    for lab, cts in zip(rec["labels"], rec["counts"]):
        if lab["part"] == "B":
            copies[(lab["s"], lab["c"], lab["variant"])][lab["copy"]] = cts

    def vec(cts):
        v = np.zeros(4)
        for key, n in cts.items():
            b = _bits(key)
            v[int(b[0]) * 2 + int(b[1])] += n
        return v

    V = {k: np.array([vec(c[1]), vec(c[2])]) for k, c in copies.items()}

    def p_s0(x):
        return (x[..., 0] + x[..., 1]) / x.sum(-1)

    def c_err(x):
        return (x[..., 0] + x[..., 2]) / x.sum(-1)

    point = {k: v.sum(0) for k, v in V.items()}
    rng = np.random.default_rng(seed_b)
    boot = {}
    for k in sorted(V):
        v = V[k]
        f, n = v / v.sum(1, keepdims=True), int(v[0].sum())
        acc = np.zeros((N_BOOT, 4))
        for _ in range(2):
            pick = rng.integers(0, 2, size=N_BOOT)
            for c in (0, 1):
                sel = pick == c
                acc[sel] += rng.multinomial(n, f[c], size=int(sel.sum()))
        boot[k] = acc
    table = {}
    for s, c in sorted({(s, c) for s, c, _ in V}):
        d = p_s0(point[(s, c, "S1")]) - p_s0(point[(s, c, "S")])
        i = p_s0(point[(s, c, "S0")]) - p_s0(point[(s, c, "S1")])
        table[f"{s};{c}"] = {
            "s": s,
            "c": c,
            "set": "target" if (s, c) in K46_TARGET else ("control" if (s, c) in K46_CONTROL else "beside"),
            "P0_S": float(p_s0(point[(s, c, "S")])),
            "P0_S1": float(p_s0(point[(s, c, "S1")])),
            "P0_S0": float(p_s0(point[(s, c, "S0")])),
            "d": float(d),
            "d_ci90": pct(p_s0(boot[(s, c, "S1")]) - p_s0(boot[(s, c, "S")])),
            "i": float(i),
            "i_ci90": pct(p_s0(boot[(s, c, "S0")]) - p_s0(boot[(s, c, "S1")])),
            "c_mid_err": float(c_err(point[(s, c, "S")])),
            "c_mid_err_ci90": pct(c_err(boot[(s, c, "S")])),
            "d_copy1": float(p_s0(V[(s, c, "S1")][0]) - p_s0(V[(s, c, "S")][0])),
            "d_copy2": float(p_s0(V[(s, c, "S1")][1]) - p_s0(V[(s, c, "S")][1])),
        }

    def dB(pr):
        return p_s0(boot[(pr[0], pr[1], "S1")]) - p_s0(boot[(pr[0], pr[1], "S")])

    Dp = np.mean([table[f"{s};{c}"]["d"] for s, c in K46_TARGET]) - np.mean(
        [table[f"{s};{c}"]["d"] for s, c in K46_CONTROL]
    )
    lo, hi = pct(np.mean([dB(p) for p in K46_TARGET], axis=0) - np.mean([dB(p) for p in K46_CONTROL], axis=0))
    pub = rec["published_at_build"]
    ro142 = pub["142"]["readout_error"]
    c142 = table["143;142"]["c_mid_err"]
    # after the data: the spectator's P(1) in S0, against its published T2 (and T2 plus readout) over the wait
    tau = rec["part_B_circuits"]["143|142|S0"]["durations_dt"]
    wait = (tau["measure_plus_reset_dt"] + tau["x_dt"]) * 4e-9
    spect = {}
    for key, row in table.items():
        t2 = pub[str(row["s"])]["T2"]
        pred = 0.5 * (1 - math.exp(-wait / t2))
        spect[key] = {
            "P1_S0": 1 - row["P0_S0"],
            "pred_T2": pred,
            "pred_T2_plus_readout": pred + pub[str(row["s"])]["readout_error"],
            "T2_us": t2 * 1e6,
        }
    return {
        "part_A": {"cells": cells, "classes": cl, "gate": gate, "patterns": patterns},
        "part_B": {
            "H_spectator": {
                "D": float(Dp),
                "ci90": [lo, hi],
                "verdict": "NOT SUPPORTED" if hi < margin else ("SUPPORTED" if lo > 0 else "NOT SETTLED"),
                "margin": margin,
                "conditions": {"entirely_below_margin": hi < margin, "entirely_above_0": lo > 0},
            },
            "table": table,
            "d_143_136_vs_targets": {f"d_143_{c}": table[f"143;{c}"]["d"] for c in (136, 142, 144)},
            "c_mid_err_142": c142,
            "q142_mid_err_over_readout": c142 / ro142,
            "q142_above_5x": bool(c142 > 5 * ro142),
        },
        "beside_after_data": {"spectator_P1_in_S0_vs_T2": spect, "tau_s0_s": wait, "q142_mid_err_k46": c142},
    }


# =========================================================================== Kickoff 47
def _ramsey_fit(taus, p1):
    from scipy.optimize import curve_fit

    t, y = np.array(taus, float), np.array(p1, float)
    c0 = y[0]

    def model(tt, a, T, f):
        return c0 + a * (1 - np.exp(-tt / T) * np.cos(2 * np.pi * f * tt))

    best = None
    for f0 in np.linspace(0.0, 0.5, 11):
        try:
            popt, pcov = curve_fit(model, t, y, p0=[0.3, 5.0, f0], bounds=([0, 0.05, 0], [0.7, 1e4, 1.0]), maxfev=20000)
        except Exception:
            continue
        sse = float(np.sum((model(t, *popt) - y) ** 2))
        if best is None or sse < best[0]:
            best = (sse, popt, pcov)
    if best is None:
        return None
    sse, popt, pcov = best
    err = np.sqrt(np.clip(np.diag(pcov), 0, None))
    return {
        "a": float(popt[0]),
        "T_us": float(popt[1]),
        "f_MHz": float(popt[2]),
        "a_err": float(err[0]),
        "T_err": float(err[1]),
        "f_err": float(err[2]),
        "sse": sse,
    }


def _echo_fit(taus, p1):
    from scipy.optimize import curve_fit

    t, y = np.array(taus, float), np.array(p1, float)
    c0 = y[0]

    def model(tt, a, T):
        return c0 + a * (1 - np.exp(-tt / T))

    try:
        popt, pcov = curve_fit(model, t, y, p0=[0.3, 20.0], bounds=([0, 0.05], [0.7, 1e5]), maxfev=20000)
    except Exception as ex:
        return {"error": type(ex).__name__}
    err = np.sqrt(np.clip(np.diag(pcov), 0, None))
    return {"a": float(popt[0]), "T_us": float(popt[1]), "a_err": float(err[0]), "T_err": float(err[1])}


def k47_wait(rec: dict, xor5: dict) -> dict:
    """Kickoff 47. Part A: the three chains without and with XY4 refocusing; H_phase on the circuit (SUPPORTED if A1
    is HIGH; read only if C0 and C1 are HIGH and A0 is LOW) and the gain from refocusing on each chain with its interval
    (seed 4747043). Part B, per qubit, pooled over the two copies: Ramsey and echo P(1) at each wait, with intervals
    (bootstrap 10,000, seed 4747, copies with replacement, each redrawn binomially); r = R(3.4) - R(0), e = E(3.4) -
    E(0); the kind of loss on 143 (REFOCUSABLE if the interval of r - 3e lies entirely above 0); beside, a damped-cosine
    fit of each Ramsey curve and an exponential fit of each echo curve, labelled as fits."""
    fixed = rec["fixed_before_the_data"]
    seed_a, seed_b = fixed["bootstrap"]["seed_A"], fixed["bootstrap"]["seed_B"]
    cells, boots = part_a_cells(rec, xor5, ["A0", "A1", "J0", "J1", "C0", "C1"], seed_a)
    for v in cells.values():
        del v["copy_to_copy_var"], v["shots"]
    cl = {c: v["class"] for c, v in cells.items()}
    gains = {
        k: {"gain": cells[f"{k}1"]["F"] - cells[f"{k}0"]["F"], "ci90": pct(boots[f"{k}1"] - boots[f"{k}0"])}
        for k in ("A", "J", "C")
    }
    if cl["C0"] != "HIGH" or cl["C1"] != "HIGH":
        gate, verdict = "C0 or C1 is not HIGH: the chip or the refocusing is misbehaving; the rest is not read", None
    elif cl["A0"] != "LOW":
        gate, verdict = "A0 is not LOW: the collapse did not repeat; reported descriptively", None
    else:
        gate, verdict = None, {"HIGH": "SUPPORTED", "LOW": "NOT SUPPORTED", "MIDDLE": "NOT SETTLED"}[cl["A1"]]
    taus = rec["taus_us"]
    raw = defaultdict(dict)
    for lab, cts in zip(rec["labels"], rec["counts"]):
        if lab["part"] == "B":
            raw[(lab["group"], lab["tau_us"], lab["variant"])][lab["copy"]] = cts
    rng = np.random.default_rng(seed_b)
    qubits = {}
    for g, qs in sorted(rec["groups"].items(), key=lambda z: int(z[0])):
        for i, q in enumerate(qs):
            P, B = {}, {}
            for tau in taus:
                for v in ("R", "E"):
                    ones, tots = [], []
                    for c in (1, 2):
                        cts = raw[(int(g), tau, v)][c]
                        ones.append(sum(n for k, n in cts.items() if _bits(k)[i] == "1"))
                        tots.append(sum(cts.values()))
                    ones, tots = np.array(ones), np.array(tots)
                    P[(tau, v)] = ones.sum() / tots.sum()
                    acc1, accn = np.zeros(N_BOOT), np.zeros(N_BOOT)
                    for _ in range(2):
                        pick = rng.integers(0, 2, size=N_BOOT)
                        acc1 += rng.binomial(tots[pick], ones[pick] / tots[pick])
                        accn += tots[pick]
                    B[(tau, v)] = acc1 / accn
            r, e = P[(3.4, "R")] - P[(0, "R")], P[(3.4, "E")] - P[(0, "E")]
            rb, eb = B[(3.4, "R")] - B[(0, "R")], B[(3.4, "E")] - B[(0, "E")]
            ci_r, ci_e, ci_r3e, ci_3e2r = pct(rb), pct(eb), pct(rb - 3 * eb), pct(3 * eb - 2 * rb)
            if ci_r[1] < 0.10:
                kind = "NOT REPRODUCED"
            elif ci_r3e[0] > 0:
                kind = "REFOCUSABLE"
            elif ci_3e2r[0] > 0:
                kind = "NOT REFOCUSABLE"
            else:
                kind = "MIXED"
            ram, ech = [P[(t, "R")] for t in taus], [P[(t, "E")] for t in taus]
            ram_ci = [pct(B[(t, "R")]) for t in taus]
            osc = [
                [taus[a], taus[b], ram[a], ram[b]]
                for a in range(len(taus))
                for b in range(a + 1, len(taus))
                if ram[b] < ram[a] - 0.1 and ram_ci[b][1] < ram_ci[a][0]
            ]
            qubits[str(q)] = {
                "group": int(g),
                "ramsey_P1": dict(zip(map(str, taus), ram)),
                "ramsey_ci90": dict(zip(map(str, taus), ram_ci)),
                "echo_P1": dict(zip(map(str, taus), ech)),
                "echo_ci90": dict(zip(map(str, taus), [pct(B[(t, "E")]) for t in taus])),
                "ramsey_loss": {str(t): P[(t, "R")] - P[(0, "R")] for t in taus},
                "echo_loss": {str(t): P[(t, "E")] - P[(0, "E")] for t in taus},
                "r_3p4": r,
                "r_ci90": ci_r,
                "e_3p4": e,
                "e_ci90": ci_e,
                "r_minus_3e_ci90": ci_r3e,
                "three_e_minus_2r_ci90": ci_3e2r,
                "kind_of_loss": kind,
                "ramsey_fit": _ramsey_fit(taus, ram),
                "echo_fit": _echo_fit(taus, ech),
                "oscillation_pairs": osc,
            }
    return {
        "part_A": {"cells": cells, "classes": cl, "gate": gate, "H_phase": verdict, "gains_beside": gains},
        "part_B": {
            "verdict_143": qubits["143"]["kind_of_loss"],
            "oscillation_143": bool(qubits["143"]["oscillation_pairs"]),
            "qubits": qubits,
        },
    }


def k47_beside(rec: dict, k47: dict, k46: dict) -> dict:
    """Kickoff 47's lines after the data, beside the verdicts: 143's and 144's loss over a wait of 3.4 us here and,
    in Kickoff 46, P(1) after its S0 wait of 3.37 us (143's lowest and highest of three, 144's two); chain J here; and
    143's idle windows in chain A, as scheduled."""
    s0 = k46["beside_after_data"]["spectator_P1_in_S0_vs_T2"]
    p143 = [s0[k]["P1_S0"] for k in ("143;136", "143;142", "143;144")]
    q = k47["part_B"]["qubits"]
    return {
        "q143_loss_k46_S0_3p37us": [min(p143), max(p143)],
        "q143_ramsey_loss_k47_3p4us": q["143"]["r_3p4"],
        "q144_loss_k46": [s0["144;143"]["P1_S0"], s0["144;145"]["P1_S0"]],
        "q144_ramsey_loss_k47": q["144"]["r_3p4"],
        "J0_k47": k47["part_A"]["cells"]["J0"]["F"],
        "idle_windows_143_in_A_dt": rec["refocusing"]["cells"]["A0"]["idle_windows_dt_before"]["143"],
    }
