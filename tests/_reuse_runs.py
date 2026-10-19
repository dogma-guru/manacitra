# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""Kickoffs 43 to 48 (findings 11 to 14), recomputed from the archived counts in data/ibm_fez/k43-map.json to
k48-wait-test.json.

Each function takes the data files as loaded and returns the analysis in the shape the run archived it (under
archived/analysis), so that tests/_reproduce.py compares the two field by field. The rules are the runs' own, fixed
before the data (Kickoff 43 with its Amendment A1). The bootstraps keep each run's seed and its order of random draws,
so an interval reproduces exactly under the runs' numpy (2.5) and agrees to 10⁻³ elsewhere (the "resampled-shots" mark
in tests/expected_fields.json, as for Kickoff 33's intervals).

This is a test helper, not part of the package: no command reads these runs. Kickoff 48's circuits were built by the
package (manacitra.wait, Amendment A18), and its recompute uses the package's analysis wherever it covers the quantity
(Amendment A19).
"""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import UTC, datetime

import numpy as np

from manacitra import archive as ar
from manacitra import wait
from manacitra.verdicts import map_verdict, persistence_day
from manacitra.wait import part_b_losses

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
    # Part B by the package's own analysis (manacitra.wait, Amendment A18), with Kickoff 47's groups, waits and rule
    groups = [qs for _, qs in sorted(rec["groups"].items(), key=lambda z: int(z[0]))]
    losses = part_b_losses(
        rec["labels"], rec["counts"], groups, rec["taus_us"], reference=3.4, seed=seed_b, wait_key="tau_us"
    )
    rename = {
        "r": "r_3p4",
        "e": "e_3p4",
        "r_minus_ke_ci90": "r_minus_3e_ci90",
        "ke_minus_jr_ci90": "three_e_minus_2r_ci90",
    }
    qubits = {q: {rename.get(k, k): v for k, v in row.items()} for q, row in losses.items()}
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


# =========================================================================== Kickoff 48
def _wait_test_keys() -> tuple[list[str], np.ndarray]:
    """The wait test's 64 outcomes in the run's order (the ideal's 32 sorted, then the other 32 in counting order),
    and the ideal's probability of each."""
    ideal = wait.wait_test_ideal()
    n = wait.WAIT_TEST_CLBITS
    keys = sorted(ideal) + [k for k in (format(i, f"0{n}b") for i in range(2**n)) if k not in ideal]
    return keys, np.array([ideal.get(k, 0.0) for k in keys])


def k48_wait_test(rec: dict) -> dict:
    """Kickoff 48, the wait test on hardware. Part A: on each chain, the wait test's F without and with XY4 refocusing,
    pooled over its copies, by the package's analysis (manacitra.wait.analyse_wait_run), with the run's 90% bootstrap
    interval (copies with replacement, each redrawn from a multinomial; seed bootstrap_A) and class. Part B by the
    package (manacitra.wait.part_b_losses; seed bootstrap_B). The prediction, H48's rule as fixed before the run:
    F_pred = F_ref x (1 - dP_R(T_M)), dP_R(T_M) the waiting qubit's Ramsey loss at the circuit's wait; d_M = F_no -
    F_pred, with a joint bootstrap of both parts (seed joint), in the run's order: chain by chain, F_no and F_ref, then
    P_R(T_M) and P_R(0). Then the verdict and what the run reported beside it."""
    m, fixed = rec["meta"], rec["fixed_before_the_data"]
    seeds = m["seeds"]
    n_boot = seeds["n_boot"]
    labels, counts = rec["labels"], rec["counts"]
    dt = m["T_M"]["dt_s"]
    keys, q = _wait_test_keys()

    def F(V):
        return np.sqrt(V / V.sum(-1, keepdims=True) * q).sum(-1) ** 2

    cells = defaultdict(list)
    for lab, cts in zip(labels, counts):
        if lab["part"] == "W":
            d: dict = defaultdict(int)
            for k, n in cts.items():
                d[k.replace(" ", "")[-wait.WAIT_TEST_CLBITS :]] += n
            cells[(str(lab["M"]), lab["variant"])].append([d.get(k, 0) for k in keys])

    def draw(rng, name, v):
        V = np.array(cells[(name, v)], float)
        freq = V / V.sum(1, keepdims=True)
        idx = rng.integers(0, V.shape[0], size=(n_boot, V.shape[0]))
        return F(rng.multinomial(int(V[0].sum()), freq[idx]).sum(1))

    def cls(ci):
        return "LOW" if ci[1] < 0.3 else ("HIGH" if ci[0] > 0.6 else "MIDDLE")

    rng_a = np.random.default_rng(seeds["bootstrap_A"])
    part_a = {}
    for name in m["chains"]:
        mine = [(lab, cts) for lab, cts in zip(labels, counts) if lab["part"] == "W" and str(lab["M"]) == name]
        wt = wait.analyse_wait_run([lab for lab, _ in mine], [c for _, c in mine], dt)["wait_test"]
        part_a[name] = {}
        for v, key in (("no", "F_no"), ("refocus", "F_refocus")):
            ci = pct(draw(rng_a, name, v))
            V = np.array(cells[(name, v)], float)
            part_a[name][v] = {
                "F": wt[key],
                "ci90": ci,
                "class": cls(ci),
                "F_per_copy": wt["F_per_copy"][v],
                "copies": int(V.shape[0]),
                "shots": int(V.sum()),
            }

    waits = list(m["waits_dt"])
    part_b = part_b_losses(
        labels,
        counts,
        [tuple(g) for g in m["groups"]],
        waits,
        reference=fixed["reference_wait_dt"],
        seed=seeds["bootstrap_B"],
        wait_key="tau_dt",
        waits_us=[w * dt * 1e6 for w in waits],
    )

    raw: dict = defaultdict(dict)
    pos = {}
    for lab, cts in zip(labels, counts):
        if lab["part"] == "B":
            raw[(lab["group"], lab["tau_dt"], lab["variant"])][lab["copy"]] = cts
            for i, qq in enumerate(lab["qubits"]):
                pos[qq] = (lab["group"], i)

    def ramsey_tallies(qubit, tau):
        g, i = pos[qubit]
        ones = [sum(n for k, n in raw[(g, tau, "R")][c].items() if _bits(k)[i] == "1") for c in (1, 2)]
        return np.array(ones), np.array([sum(raw[(g, tau, "R")][c].values()) for c in (1, 2)])

    margin, floor = fixed["margin"], fixed["informative_floor"]
    rng = np.random.default_rng(seeds["joint"])
    pred = {}
    for name, chain in m["chains"].items():
        M = chain[1]
        tm = wait.even_wait(m["T_M"]["per_chain"][name]["T_M_dt"])
        b = {v: draw(rng, name, v) for v in ("no", "refocus")}
        pr = {}
        for tau in (tm, 0):
            o, t = ramsey_tallies(M, tau)
            acc1, accn = np.zeros(n_boot), np.zeros(n_boot)
            for _ in range(2):
                pick = rng.integers(0, 2, size=n_boot)
                acc1 += rng.binomial(t[pick], o[pick] / t[pick])
                accn += t[pick]
            pr[tau] = acc1 / accn
        loss = part_b[str(M)]["ramsey_loss"][str(tm)]
        loss_b = pr[tm] - pr[0]
        f_no, f_ref = part_a[name]["no"]["F"], part_a[name]["refocus"]["F"]
        f_pred = f_ref * (1 - loss)
        ci_d, ci_loss = pct(b["no"] - b["refocus"] * (1 - loss_b)), pct(loss_b)
        pred[name] = {
            "chain": chain,
            "M": M,
            "T_M_dt": tm,
            "T_M_us": tm * dt * 1e6,
            "dP_R_TM": loss,
            "dP_R_TM_ci90": ci_loss,
            "F_no": f_no,
            "F_ref": f_ref,
            "F_pred": f_pred,
            "d_M": f_no - f_pred,
            "d_M_ci90": ci_d,
            "informative": ci_loss[0] > floor,
            "inside_margin": ci_d[0] > -margin and ci_d[1] < margin,
            "outside_margin": ci_d[0] > margin or ci_d[1] < -margin,
            "gain": f_ref - f_no,
            "gain_ci90": pct(b["refocus"] - b["no"]),
            "gain_class": f"{part_a[name]['no']['class']} -> {part_a[name]['refocus']['class']}",
        }
    if any(p["outside_margin"] for p in pred.values()):
        verdict = "DISAGREE"
    elif all(p["inside_margin"] for p in pred.values()):
        verdict = "AGREE"
    else:
        verdict = "NOT SETTLED"
    informative = [n for n, p in pred.items() if p["informative"]]
    if not informative:
        verdict += ", uninformative"
    # beside the verdict, as the run reported it: 143's kind of loss, whether its offset is still there, and the
    # oscillation sign, a fall of more than 0.1 with separated intervals from 8 us or T_M to the last wait (16 us)
    q143 = part_b["143"]
    ram, ci = q143["ramsey_P1"], q143["ramsey_ci90"]
    last = str(waits[-1])
    osc = [
        [int(a), waits[-1], ram[a], ram[last]]
        for a in ("2000", str(pred["143"]["T_M_dt"]))
        if ram[last] < ram[a] - 0.1 and ci[last][1] < ci[a][0]
    ]
    return {
        "H48": verdict,
        "informative_chains": informative,
        "prediction": pred,
        "part_A": part_a,
        "part_B": part_b,
        "waits_dt": waits,
        "beside": {
            "q143_kind_of_loss_3p4us": q143["kind_of_loss"],
            "q143_r_3p4": q143["r"],
            "offset_still_there": bool(q143["r_ci90"][0] > 0.1),
            "oscillation_143_8_or_TM_to_16us": osc,
            "kinds": {k: v["kind_of_loss"] for k, v in part_b.items()},
        },
    }


# =========================================================================== Kickoffs 49 to 53 (Amendment A22)
def k49_wait_test(rec: dict, k48: dict) -> dict:
    """Kickoff 49, the wait test on a second day: Kickoff 48's recompute (k48_wait_test), unchanged, on Kickoff 49's
    counts with its seeds, as the run computed it; then what the run reported beside the verdict, against Kickoff 48's
    archived analysis (k48: that record): each qubit's kind of loss on both days, 143's Ramsey loss at 3.4 us, the
    Ramsey fits labelled as fits, each chain's d_M beside Kickoff 48's, and the calibration stamps."""
    r = k48_wait_test(rec)
    a48 = k48["archived"]["analysis"]
    pb = r["part_B"]
    fits = {}
    for q, v in pb.items():
        f = v["ramsey_fit"]
        fits[q] = (
            None
            if f is None
            else {
                "offset_kHz": f["f_MHz"] * 1e3,
                "offset_err_kHz": f["f_err"] * 1e3,
                "decay_us": f["T_us"],
                "amplitude": f["a"],
                "label": "a fit (manacitra.wait.ramsey_fit), not a measurement",
            }
        )
    d_beside = {
        n: {
            "d_M_k49": p["d_M"],
            "d_M_ci90_k49": p["d_M_ci90"],
            "d_M_k48": a48["prediction"][n]["d_M"],
            "d_M_ci90_k48": a48["prediction"][n]["d_M_ci90"],
            "dP_R_TM_k49": p["dP_R_TM"],
            "dP_R_TM_k48": a48["prediction"][n]["dP_R_TM"],
            "informative_k49": p["informative"],
            "informative_k48": a48["prediction"][n]["informative"],
        }
        for n, p in r["prediction"].items()
    }
    run = rec["run"]
    stamps = {
        "at_build": run["calibration_at_build"],
        "at_submission": run["calibration_at_submission"],
        "after_fetch": run["calibration_after_fetch"],
        "k48": run["calibration_k48"],
    }
    k48_utc = _utc(k48["run"]["calibration_at_build"])
    days = {k: (_utc(v) - k48_utc).total_seconds() / 86400 for k, v in stamps.items() if k != "k48"}
    return {
        "verdict": r["H48"],
        **r,
        "beside": {
            **r["beside"],
            "kinds_k47_rule_3p4us": {q: v["kind_of_loss"] for q, v in pb.items()},
            "kinds_k48": {q: v["kind_of_loss"] for q, v in a48["part_B"].items()},
            "q143_r_ci90": pb["143"]["r_ci90"],
            "q143_r_k48": a48["part_B"]["143"]["r"],
            "ramsey_fits": fits,
            "ramsey_fits_k48_kHz": {
                q: (None if v["ramsey_fit"] is None else v["ramsey_fit"]["f_MHz"] * 1e3)
                for q, v in a48["part_B"].items()
            },
            "d_M_beside_k48": d_beside,
            "calibration_stamps": stamps,
            "days_since_k48_stamp": days,
        },
    }


def _utc(stamp: str):
    """A calibration stamp, as IBM's properties give it (an offset, or a trailing UTC), as a UTC datetime."""
    from datetime import datetime

    s = stamp.replace(" UTC", "+00:00") if stamp.endswith(" UTC") else stamp
    return datetime.fromisoformat(s).astimezone(UTC)


def _cells_and_bits(labels, counts, key):
    """The runs' tallies from the counts, as Kickoffs 50 to 53's analyses made them: for each wait-test position, the
    64 outcomes in the recompute's order (_wait_test_keys); for each Ramsey position, M's ones and shots from its own
    bit (the label's m_clbit); each listed by copy. key(label) names a position's cell."""
    keys, _ = _wait_test_keys()
    cells, bits, pooled = defaultdict(list), defaultdict(list), defaultdict(lambda: defaultdict(int))
    for lab, cts in zip(labels, counts):
        k_ = key(lab)
        if lab["part"] == "W":
            d: dict = defaultdict(int)
            for k, n in cts.items():
                kk = k.replace(" ", "")[-wait.WAIT_TEST_CLBITS :]
                d[kk] += n
                pooled[k_][kk] += n
            cells[k_].append((lab["copy"], [d.get(k, 0) for k in keys]))
        else:
            i = lab["m_clbit"]
            ones = sum(n for k, n in cts.items() if k.replace(" ", "")[::-1][i] == "1")
            bits[k_].append((lab["copy"], ones, sum(cts.values())))
    for dd in (cells, bits):
        for k in dd:
            dd[k].sort(key=lambda x: x[0])
    return cells, bits, pooled


def _draws(rng, n_boot: int, cells, bits):
    """The two draws of Kickoffs 50 to 53's joint bootstrap, from one random stream: a wait-test cell's F (the copies
    with replacement, each redrawn from a multinomial) and a Ramsey's P(1) (the copies with replacement, each redrawn
    binomially)."""
    _, q = _wait_test_keys()

    def F(V):
        return np.sqrt(V / V.sum(-1, keepdims=True) * q).sum(-1) ** 2

    def draw_F(key):
        V = np.array([x[1] for x in cells[key]], float)
        freq = V / V.sum(1, keepdims=True)
        idx = rng.integers(0, V.shape[0], size=(n_boot, V.shape[0]))
        return F(rng.multinomial(int(V[0].sum()), freq[idx]).sum(1))

    def draw_P(key):
        o = np.array([x[1] for x in bits[key]])
        t = np.array([x[2] for x in bits[key]])
        acc1, accn = np.zeros(n_boot), np.zeros(n_boot)
        for _ in range(len(o)):
            pick = rng.integers(0, len(o), size=n_boot)
            acc1 += rng.binomial(t[pick], o[pick] / t[pick])
            accn += t[pick]
        return acc1 / accn

    return draw_F, draw_P


def _p1(bits, key) -> float:
    return sum(x[1] for x in bits[key]) / sum(x[2] for x in bits[key])


def _stamps(rec: dict, earlier: str, name: str) -> tuple[dict, dict]:
    """The calibration stamps at build, submission and fetch beside an earlier run's, and the hours since it."""
    run = rec["run"]
    stamps = {
        "at_build": run["calibration_at_build"],
        "at_submission": run["calibration_at_submission"],
        "after_fetch": run["calibration_after_fetch"],
        name: earlier,
    }
    t0 = _utc(earlier)
    return stamps, {k: (_utc(v) - t0).total_seconds() / 3600 for k, v in stamps.items() if k != name}


#: Kickoff 50's figures from Kickoff 49 and Kickoff 51's from Kickoff 50, as the analyses carried them (the earlier
#: reports' roundings, beside the verdicts; tests/test_readme_numbers.py checks them against those runs' recomputes)
K49_144_AS_CARRIED = {"F_no": 0.786, "F_ref": 0.896, "dP_R_TM": 0.326, "d_M": 0.182}
K50_D0_AS_CARRIED = {"144": 0.044, "143": -0.014}


def k50_neighbour(rec: dict) -> dict:
    """Kickoff 50, the neighbour test, as its analysis fixed it before the data: per M (144, then 143), F_no and F_ref
    by the package's analysis (manacitra.wait.analyse_wait_run), M's P(1) in R0 to R3, E0, E1 and Z from its own bit,
    loss = P(1) - P(1) of Z; Delta_active = loss(R0) - loss(R1), d0 and d1; one joint bootstrap (seed bootstrap). H50
    on 144, the gap first."""
    m, fixed = rec["meta"], rec["fixed_before_the_data"]
    seeds, dt = m["seeds"], m["T_M"]["dt_s"]
    labels, counts = rec["labels"], rec["counts"]
    order, ramsey = ("144", "143"), ("Z", "R0", "R1", "R2", "R3", "E0", "E1")

    def key(lab):
        return (str(lab["M"]), lab["variant"]) if lab["part"] == "W" else (str(lab["M"]), lab["circuit"])

    cells, bits, _ = _cells_and_bits(labels, counts, key)
    draw_F, draw_P = _draws(np.random.default_rng(seeds["bootstrap"]), seeds["n_boot"], cells, bits)
    out = {}
    for M in order:
        mine = [(lab, cts) for lab, cts in zip(labels, counts) if str(lab["M"]) == M and lab["part"] == "W"]
        wt = wait.analyse_wait_run([lab for lab, _ in mine], [c for _, c in mine], dt)["wait_test"]
        Fb = {"no": draw_F((M, "no")), "refocus": draw_F((M, "refocus"))}
        Pb = {c: draw_P((M, c)) for c in ramsey}
        P = {c: _p1(bits, (M, c)) for c in ramsey}
        loss = {c: P[c] - P["Z"] for c in ramsey if c != "Z"}
        loss_b = {c: Pb[c] - Pb["Z"] for c in ramsey if c != "Z"}
        f_no, f_ref = wt["F_no"], wt["F_refocus"]
        q_ = {
            "F_no": f_no,
            "F_no_ci90": pct(Fb["no"]),
            "F_ref": f_ref,
            "F_ref_ci90": pct(Fb["refocus"]),
            "F_per_copy": wt["F_per_copy"],
            "P1": P,
            "P1_ci90": {c: pct(Pb[c]) for c in ramsey},
            "shots": {c: [x[2] for x in bits[(M, c)]] for c in ramsey},
            "loss": loss,
            "loss_ci90": {c: pct(v) for c, v in loss_b.items()},
            "delta_active": loss["R0"] - loss["R1"],
            "delta_active_ci90": pct(loss_b["R0"] - loss_b["R1"]),
            "d0": f_no - f_ref * (1 - loss["R0"]),
            "d0_ci90": pct(Fb["no"] - Fb["refocus"] * (1 - loss_b["R0"])),
            "d1": f_no - f_ref * (1 - loss["R1"]),
            "d1_ci90": pct(Fb["no"] - Fb["refocus"] * (1 - loss_b["R1"])),
            "state_split_R0_minus_R2": loss["R0"] - loss["R2"],
            "state_split_ci90": pct(loss_b["R0"] - loss_b["R2"]),
            "readout_split_R0_minus_R3": loss["R0"] - loss["R3"],
            "readout_split_ci90": pct(loss_b["R0"] - loss_b["R3"]),
            "echo_active_E0_minus_E1": loss["E0"] - loss["E1"],
            "echo_active_ci90": pct(loss_b["E0"] - loss_b["E1"]),
        }
        lo, hi = q_["d1_ci90"]
        mg = fixed["d1_margin_beside"]
        q_["d1_vs_0p15"] = "inside" if (lo > -mg and hi < mg) else ("outside" if (lo > mg or hi < -mg) else "neither")
        out[M] = q_
    p = out["144"]
    reproduced = p["d0_ci90"][0] > fixed["reproduced_floor"]
    lo, hi = p["delta_active_ci90"]
    if lo > fixed["supported"]:
        h50 = "SUPPORTED"
    elif hi < -fixed["supported"]:
        h50 = "OPPOSITE"
    elif lo > -fixed["not_supported_band"] and hi < fixed["not_supported_band"]:
        h50 = "NOT SUPPORTED"
    else:
        h50 = "NOT SETTLED"
    verdict = f"{h50}, REPRODUCED" if reproduced else f"{h50} (Kickoff 49's gap not present today)"
    stamps, hours = _stamps(rec, "2026-10-13 16:08:33 UTC", "k49")
    return {
        "verdict": verdict,
        "H50": h50,
        "reproduced": reproduced,
        "per_M": out,
        "beside": {
            "delta_active_143": out["143"]["delta_active"],
            "delta_active_143_ci90": out["143"]["delta_active_ci90"],
            "d1": {M: [out[M]["d1"], out[M]["d1_ci90"], out[M]["d1_vs_0p15"]] for M in order},
            "calibration_stamps": stamps,
            "hours_since_k49_stamp": hours,
            "k49_144": dict(K49_144_AS_CARRIED),
        },
    }


def _fit3(lm, l0, lp) -> dict:
    """Kickoff 51's fit: loss(phi) = a sin^2((phi + theta) / 2) + b through the points at -90, 0 and +90 degrees,
    a >= 0."""
    c = (lp + lm) / 2
    ks, kc = (lp - lm) / 2, c - l0
    k = np.hypot(ks, kc)
    return {"theta_deg": np.degrees(np.arctan2(ks, kc)), "a": 2 * k, "b": c - k}


def k51_known_offset(rec: dict) -> dict:
    """Kickoff 51, a known offset, as its analysis fixed it before the data: per M (144, then 143) and phi in {-90, 0,
    +90}, F_no(phi) and F_ref against the phi = 0 parity ideal, M's losses in R0, R1 and R2; d(phi) with each and the
    swings A, A1, A2; the three-point fits of R0's and R2's losses, labelled as fits; one joint bootstrap (seed
    bootstrap). H51."""
    m, fixed = rec["meta"], rec["fixed_before_the_data"]
    seeds = m["seeds"]
    labels, counts = rec["labels"], rec["counts"]
    order, phis = ("144", "143"), (-90, 0, 90)
    cells, bits, pooled = _cells_and_bits(labels, counts, lambda lab: (str(lab["M"]), lab["circuit"], lab["phi_deg"]))
    draw_F, draw_P = _draws(np.random.default_rng(seeds["bootstrap"]), seeds["n_boot"], cells, bits)
    ideal = wait.wait_test_ideal()
    out = {}
    for M in order:
        wkeys = [(M, "W-no", p) for p in phis] + [(M, "W-ref", 0)]
        rkeys = [(M, "Z", 0)] + [(M, k, p) for k in ("R0", "R1", "R2") for p in phis]
        Fb = {k: draw_F(k) for k in wkeys}
        Pb = {k: draw_P(k) for k in rkeys}
        Fp = {k: wait.fidelity(dict(pooled[k]), ideal) for k in wkeys}
        P = {k: _p1(bits, k) for k in rkeys}
        z = (M, "Z", 0)
        loss = {(c, p): P[(M, c, p)] - P[z] for c in ("R0", "R1", "R2") for p in phis}
        loss_b = {(c, p): Pb[(M, c, p)] - Pb[z] for c in ("R0", "R1", "R2") for p in phis}
        f_ref, f_ref_b = Fp[(M, "W-ref", 0)], Fb[(M, "W-ref", 0)]
        res = {
            "F_no": {str(p): Fp[(M, "W-no", p)] for p in phis},
            "F_no_ci90": {str(p): pct(Fb[(M, "W-no", p)]) for p in phis},
            "F_ref": f_ref,
            "F_ref_ci90": pct(f_ref_b),
            "P1_Z": P[z],
            "P1_Z_ci90": pct(Pb[z]),
            "loss": {f"{c}|{p:+d}": v for (c, p), v in loss.items()},
            "loss_ci90": {f"{c}|{p:+d}": pct(v) for (c, p), v in loss_b.items()},
        }
        for tag, c in (("", "R0"), ("1", "R1"), ("2", "R2")):
            d = {p: Fp[(M, "W-no", p)] - f_ref * (1 - loss[(c, p)]) for p in phis}
            db = {p: Fb[(M, "W-no", p)] - f_ref_b * (1 - loss_b[(c, p)]) for p in phis}
            res[f"d{tag or '0'}"] = {str(p): v for p, v in d.items()}
            res[f"d{tag or '0'}_ci90"] = {str(p): pct(db[p]) for p in phis}
            res[f"A{tag}"] = (d[90] - d[-90]) / 2
            res[f"A{tag}_ci90"] = pct((db[90] - db[-90]) / 2)
            res[f"mean_abs_d{tag or '0'}"] = float(np.mean([abs(d[p]) for p in phis]))
        for c in ("R0", "R2"):
            f = _fit3(*(loss[(c, p)] for p in phis))
            fb = _fit3(*(loss_b[(c, p)] for p in phis))
            th = f["theta_deg"]
            wrapped = th + (fb["theta_deg"] - th + 180) % 360 - 180
            res[f"fit_{c}"] = {
                "theta_deg": float(th),
                "theta_ci90": pct(wrapped),
                "a": float(f["a"]),
                "b": float(f["b"]),
                "label": "a fit (exact through the three points), not a measurement",
            }
        res["R1_tracks_better_than_R0"] = res["mean_abs_d1"] < res["mean_abs_d0"]
        lo, hi = res["A_ci90"]
        res["A_outside_0p05"] = lo > fixed["supported_outside"] or hi < -fixed["supported_outside"]
        res["A_inside_0p03"] = lo > -fixed["not_supported_inside"] and hi < fixed["not_supported_inside"]
        out[M] = res
    if any(out[M]["A_outside_0p05"] for M in order):
        verdict = "SUPPORTED"
    elif all(out[M]["A_inside_0p03"] for M in order):
        verdict = "NOT SUPPORTED"
    else:
        verdict = "NOT SETTLED"
    stamps, hours = _stamps(rec, "2026-10-13 17:32:21 UTC", "k50")
    return {
        "verdict": verdict,
        "per_M": out,
        "beside": {
            "d_at_0_k51": {M: out[M]["d0"]["0"] for M in order},
            "d0_k50": dict(K50_D0_AS_CARRIED),
            "calibration_stamps": stamps,
            "hours_since_k50_stamp": hours,
        },
    }


K52_PHIS = (0, 60, 120, 180, 240, 300)
_K52_X = np.column_stack([np.ones(6), np.cos(np.radians(K52_PHIS)), np.sin(np.radians(K52_PHIS))])
_K52_PINV = np.linalg.pinv(_K52_X)


def _wrap(x):
    """Degrees wrapped to (-180, +180]."""
    w = (np.asarray(x, float) + 180.0) % 360.0 - 180.0
    return np.where(w <= -180.0, w + 360.0, w)


def _fit6(y):
    """Kickoff 52's fit: OLS of y(phi) = c + b cos(phi) + s sin(phi) over the six phases (on the last axis)."""
    coef = np.asarray(y, float) @ _K52_PINV.T
    return coef[..., 0], coef[..., 1], coef[..., 2]


def theta_ramsey(y):
    """A Ramsey's fitted offset from its losses over the six phases: atan2(s, -b), in degrees."""
    _, b, s = _fit6(y)
    return np.degrees(np.arctan2(s, -b))


def theta_wait_test(y):
    """The wait test's fitted offset from F_no over the six phases: atan2(-s, b), in degrees."""
    _, b, s = _fit6(y)
    return np.degrees(np.arctan2(-s, b))


def k52_phase_sweep(rec: dict) -> dict:
    """Kickoff 52, the phase sweep, as its analysis fixed it before the data: per M (143, then 144), F_no(phi) at six
    phases and F_ref, M's losses in R0 and R1; the fitted offsets theta_W, theta_R0 and theta_R1; Delta = theta_W -
    theta_R0 and the two parts beside it; one joint bootstrap (seed bootstrap), refitting on every resample. H52a and
    H52b."""
    m, fixed = rec["meta"], rec["fixed_before_the_data"]
    seeds = m["seeds"]
    labels, counts = rec["labels"], rec["counts"]
    order, name = ("143", "144"), {"143": "H52a", "144": "H52b"}
    margin = fixed["margin_deg"]

    def near(draws, point):
        return point + _wrap(np.asarray(draws) - point)

    def verdict_of(ci):
        lo, hi = ci
        if lo > margin or hi < -margin:
            return "DIFFERENT"
        if lo > -margin and hi < margin:
            return "SAME"
        return "NOT SETTLED"

    cells, bits, pooled = _cells_and_bits(labels, counts, lambda lab: (str(lab["M"]), lab["circuit"], lab["phi_deg"]))
    draw_F, draw_P = _draws(np.random.default_rng(seeds["bootstrap"]), seeds["n_boot"], cells, bits)
    ideal = wait.wait_test_ideal()
    out = {}
    for M in order:
        wkeys = [(M, "W-no", p) for p in K52_PHIS] + [(M, "W-ref", 0)]
        rkeys = [(M, "Z", 0)] + [(M, c, p) for c in ("R0", "R1") for p in K52_PHIS]
        Fb = {k: draw_F(k) for k in wkeys}
        Pb = {k: draw_P(k) for k in rkeys}
        Fp = {k: wait.fidelity(dict(pooled[k]), ideal) for k in wkeys}
        P = {k: _p1(bits, k) for k in rkeys}
        z = (M, "Z", 0)
        y = {"W": np.array([Fp[(M, "W-no", p)] for p in K52_PHIS])}
        yb = {"W": np.stack([Fb[(M, "W-no", p)] for p in K52_PHIS], -1)}
        for c in ("R0", "R1"):
            y[c] = np.array([P[(M, c, p)] - P[z] for p in K52_PHIS])
            yb[c] = np.stack([Pb[(M, c, p)] - Pb[z] for p in K52_PHIS], -1)
        th = {
            "W": float(theta_wait_test(y["W"])),
            "R0": float(theta_ramsey(y["R0"])),
            "R1": float(theta_ramsey(y["R1"])),
        }
        thb = {"W": theta_wait_test(yb["W"]), "R0": theta_ramsey(yb["R0"]), "R1": theta_ramsey(yb["R1"])}
        diffs = {}
        for dn, (a, b) in (
            ("Delta_W_minus_R0", ("W", "R0")),
            ("W_minus_R1", ("W", "R1")),
            ("R1_minus_R0", ("R1", "R0")),
        ):
            pt = float(_wrap(th[a] - th[b]))
            diffs[dn] = {"deg": pt, "ci90": pct(near(_wrap(thb[a] - thb[b]), pt))}
        fits = {}
        for c in ("W", "R0", "R1"):
            c0, b, s = _fit6(y[c])
            fits[c] = {
                "theta_deg": th[c],
                "theta_ci90": pct(near(thb[c], th[c])),
                "c": float(c0),
                "b": float(b),
                "s": float(s),
                "amplitude": float(math.hypot(b, s)),
                "residuals": (y[c] - _K52_X @ np.array([c0, b, s])).tolist(),
                "y": y[c].tolist(),
                "label": "a fit (OLS of c + b cos phi + s sin phi over the six phases), fixed before the data",
            }
        f_ref, f_ref_b = Fp[(M, "W-ref", 0)], Fb[(M, "W-ref", 0)]
        resid = {}
        for t, c in (("d0", "R0"), ("d1", "R1")):
            resid[t] = {str(p): float(y["W"][i] - f_ref * (1 - y[c][i])) for i, p in enumerate(K52_PHIS)}
            resid[t + "_ci90"] = {
                str(p): pct(yb["W"][:, i] - f_ref_b * (1 - yb[c][:, i])) for i, p in enumerate(K52_PHIS)
            }
        out[M] = {
            "verdict_name": name[M],
            "verdict": verdict_of(diffs["Delta_W_minus_R0"]["ci90"]),
            **diffs,
            "fits": fits,
            "R1_closer_than_R0": abs(diffs["W_minus_R1"]["deg"]) < abs(diffs["Delta_W_minus_R0"]["deg"]),
            "F_no": {str(p): Fp[(M, "W-no", p)] for p in K52_PHIS},
            "F_no_ci90": {str(p): pct(Fb[(M, "W-no", p)]) for p in K52_PHIS},
            "F_ref": f_ref,
            "F_ref_ci90": pct(f_ref_b),
            "P1_Z": P[z],
            "P1_Z_ci90": pct(Pb[z]),
            "loss": {f"{c}|{p}": float(y[c][i]) for c in ("R0", "R1") for i, p in enumerate(K52_PHIS)},
            "loss_ci90": {f"{c}|{p}": pct(yb[c][:, i]) for c in ("R0", "R1") for i, p in enumerate(K52_PHIS)},
            **resid,
        }
    stamps, hours = _stamps(rec, "2026-10-13 17:32:21 UTC", "k51")
    return {
        "H52a": out["143"]["verdict"],
        "H52b": out["144"]["verdict"],
        "per_M": out,
        "beside": {"calibration_stamps": stamps, "hours_since_k51_stamp": hours},
    }


def _margin_rule(cs, d_key: str, loss_key: str, margin: float, floor: float) -> tuple[str, list]:
    """Kickoff 53's rule on a list of cells: informative if the loss interval lies entirely above the floor; DISAGREE if
    any informative cell's residual interval lies entirely outside the margin, AGREE if every one's lies entirely
    inside, NOT SETTLED otherwise, with ", uninformative" if no cell is informative."""
    inf = [c for c in cs if c[loss_key + "_ci90"][0] > floor]
    out_ = [c for c in inf if c[d_key + "_ci90"][0] > margin or c[d_key + "_ci90"][1] < -margin]
    inside = [c for c in inf if c[d_key + "_ci90"][0] > -margin and c[d_key + "_ci90"][1] < margin]
    v = "DISAGREE" if out_ else ("AGREE" if len(inside) == len(inf) else "NOT SETTLED")
    if not inf:
        v += ", uninformative"
    return v, [c["cell"] for c in inf]


def _revised_check(rec: dict, order, labels=None, counts=None, phis=(0, 90)) -> tuple[dict, list]:
    """Kickoff 53's analysis, as fixed before its data and reused unchanged by Kickoffs 54, 55, 57, 59 and 62
    (analyse_53.py): per chain in the given order and phi in phis ({0, +90} for Kickoffs 53 to 55; Kickoff 57's analysis
    passes the phi* circuits labelled 0, with phis (0,)), F_no(phi), F_ref and M's losses in R0 and R1; the revised
    residual d1 with R1's loss and the original d0 with R0's; one joint bootstrap (seed bootstrap). The verdict on the
    cells informative by R1, and the original rule's verdict beside it. Returns the analysis and its cells."""
    m, fixed = rec["meta"], rec["fixed_before_the_data"]
    seeds = m["seeds"]
    labels, counts = (rec["labels"], rec["counts"]) if labels is None else (labels, counts)
    margin, floor = fixed["margin"], fixed["informative_floor"]

    def rule(cs, d_key, loss_key):
        return _margin_rule(cs, d_key, loss_key, margin, floor)

    cells, bits, pooled = _cells_and_bits(labels, counts, lambda lab: (str(lab["M"]), lab["circuit"], lab["phi_deg"]))
    draw_F, draw_P = _draws(np.random.default_rng(seeds["bootstrap"]), seeds["n_boot"], cells, bits)
    ideal = wait.wait_test_ideal()
    per_cell, per_chain = [], {}
    for M in order:
        wkeys = [(M, "W-no", p) for p in phis] + [(M, "W-ref", 0)]
        rkeys = [(M, "Z", 0)] + [(M, c, p) for c in ("R0", "R1") for p in phis]
        Fb = {k: draw_F(k) for k in wkeys}
        Pb = {k: draw_P(k) for k in rkeys}
        Fp = {k: wait.fidelity(dict(pooled[k]), ideal) for k in wkeys}
        P = {k: _p1(bits, k) for k in rkeys}
        z = (M, "Z", 0)
        f_ref, f_ref_b = Fp[(M, "W-ref", 0)], Fb[(M, "W-ref", 0)]
        per_chain[M] = {"F_ref": f_ref, "F_ref_ci90": pct(f_ref_b), "P1_Z": P[z], "P1_Z_ci90": pct(Pb[z])}
        for p in phis:
            l0, l1 = P[(M, "R0", p)] - P[z], P[(M, "R1", p)] - P[z]
            l0b, l1b = Pb[(M, "R0", p)] - Pb[z], Pb[(M, "R1", p)] - Pb[z]
            fno, fnob = Fp[(M, "W-no", p)], Fb[(M, "W-no", p)]
            per_cell.append(
                {
                    "cell": f"{M}|{p:+d}",
                    "M": M,
                    "phi_deg": p,
                    "F_no": fno,
                    "F_no_ci90": pct(fnob),
                    "F_ref": f_ref,
                    "loss_R0": l0,
                    "loss_R0_ci90": pct(l0b),
                    "loss_R1": l1,
                    "loss_R1_ci90": pct(l1b),
                    "F_pred1": f_ref * (1 - l1),
                    "d1": fno - f_ref * (1 - l1),
                    "d1_ci90": pct(fnob - f_ref_b * (1 - l1b)),
                    "F_pred0": f_ref * (1 - l0),
                    "d0": fno - f_ref * (1 - l0),
                    "d0_ci90": pct(fnob - f_ref_b * (1 - l0b)),
                }
            )
    for c in per_cell:
        c["informative_R1"] = c["loss_R1_ci90"][0] > floor
        c["informative_R0"] = c["loss_R0_ci90"][0] > floor
        c["d1_inside"] = c["d1_ci90"][0] > -margin and c["d1_ci90"][1] < margin
        c["d1_outside"] = c["d1_ci90"][0] > margin or c["d1_ci90"][1] < -margin
        c["abs_d1_lt_abs_d0"] = abs(c["d1"]) < abs(c["d0"])
    verdict, informative = rule(per_cell, "d1", "loss_R1")
    v0, inf0 = rule(per_cell, "d0", "loss_R0")
    inf_cells = [c for c in per_cell if c["informative_R1"]]
    out = {
        "verdict": verdict,
        "informative_cells": informative,
        "cells": per_cell,
        "chains": per_chain,
        "beside": {
            "original_rule_verdict": v0,
            "original_rule_informative_cells": inf0,
            "mean_abs_d1_informative": float(np.mean([abs(c["d1"]) for c in inf_cells])) if inf_cells else None,
            "mean_abs_d0_informative": float(np.mean([abs(c["d0"]) for c in inf_cells])) if inf_cells else None,
            "mean_abs_d1_all": float(np.mean([abs(c["d1"]) for c in per_cell])),
            "mean_abs_d0_all": float(np.mean([abs(c["d0"]) for c in per_cell])),
            "abs_d1_lt_abs_d0": {c["cell"]: c["abs_d1_lt_abs_d0"] for c in per_cell},
            "phi0_cells_informative_on_their_own": [
                c["cell"] for c in per_cell if c["phi_deg"] == 0 and c["informative_R1"]
            ],
        },
    }
    return out, per_cell


def k53_revised_check(rec: dict) -> dict:
    """Kickoff 53, the revised check on new chains, as its analysis fixed it before the data: per chain in the drawn
    order and phi in {0, +90}, F_no(phi), F_ref and M's losses in R0 and R1; the revised residual d1 with R1's loss and
    the original d0 with R0's; one joint bootstrap (seed bootstrap). H53 on the cells informative by R1, and the
    original rule's verdict beside it."""
    order = [str(c["chain"][1]) for c in rec["chain_draw"]["drawn"]]
    r, _ = _revised_check(rec, order)
    run = rec["run"]
    return {
        "H53": r["verdict"],
        "informative_cells": r["informative_cells"],
        "cells": r["cells"],
        "chains": r["chains"],
        "beside": r["beside"],
        "chain_order": order,
        "calibration_stamps": {
            "at_build": run["calibration_at_build"],
            "at_submission": run["calibration_at_submission"],
            "after_fetch": run["calibration_after_fetch"],
            "chains_drawn_under": rec["chain_draw"]["calibration_stamp"],
            "k52_after_fetch": "2026-10-13 18:56:54 UTC",
        },
    }


# --------------------------------------------------------------------------- Kickoffs 54 and 55 (Amendment A23)
PHIS4 = (0, 90, 180, 270)
_X4 = np.column_stack([np.ones(4), np.cos(np.radians(PHIS4)), np.sin(np.radians(PHIS4))])
_P4 = np.linalg.pinv(_X4)


def _fit4(y):
    """Kickoffs 54 and 55's fit, fixed before their data: OLS of the loss c + b cos(phi) + s sin(phi) over 0, 90, 180
    and 270 degrees (on the last axis); theta = atan2(s, -b) in degrees, and the amplitude."""
    coef = np.asarray(y, float) @ _P4.T
    c, b, s = coef[..., 0], coef[..., 1], coef[..., 2]
    return np.degrees(np.arctan2(s, -b)), np.hypot(b, s), c, b, s


def _beside_tallies(labels, counts):
    """M's bit per (M, circuit, phi) over the circuits that are not wait tests, by copy; and, where a label names them,
    the neighbours' bits (Kickoff 54's single-neighbour Ramseys measure L1 and L3)."""
    m_bits, n_bits = defaultdict(list), defaultdict(list)
    for lab, cts in zip(labels, counts):
        if lab["part"] == "W":
            continue
        key = (str(lab["M"]), lab["circuit"], lab["phi_deg"])

        def bit(i, cts=cts):
            return sum(n for k, n in cts.items() if k.replace(" ", "")[::-1][i] == "1")

        tot = sum(cts.values())
        m_bits[key].append((lab["copy"], bit(lab["m_clbit"]), tot))
        if "l1_clbit" in lab:
            n_bits[key].append((lab["copy"], bit(lab["l1_clbit"]), bit(lab["l3_clbit"]), tot))
    for d in (m_bits, n_bits):
        for k in d:
            d[k].sort(key=lambda x: x[0])
    return m_bits, n_bits


def _lean(cells) -> dict:
    d1 = [c["d1"] for c in cells]
    inf = [c["d1"] for c in cells if c["informative_R1"]]
    return {
        "d1": {c["cell"]: c["d1"] for c in cells},
        "mean_d1": float(np.mean(d1)),
        "n_d1_above_zero": int(sum(x > 0 for x in d1)),
        "n_cells": len(d1),
        "mean_d1_informative": float(np.mean(inf)) if inf else None,
    }


def _beside_r1_fits(rec: dict, order, pulses: bool, with_bs: bool, neighbour_ms=()) -> dict:
    """Beside the verdict of Kickoffs 54 and 55, from their own bootstrap (seed bootstrap_beside), in the order their
    analyses fixed: per M, P(1) of Z, X1 (and Kickoff 54's XY4), R1 at 0, 90, 180 and 270 (the copies with
    replacement, each redrawn binomially), refitting on every resample; then Kickoff 54's single-neighbour Ramseys on
    144 and 143. P(0|1) = 1 - P(1) after X; the pulses' cost, P(1) after H, XY4, H, and minus Z's; the R1 fit; and, on
    each neighbour qubit, the shifts of the single-neighbour fits from the both-idle one, their sum against the joint
    shift, and the 143-144 pair seen from each end."""
    seeds = rec["meta"]["seeds"]
    n_boot = seeds["n_boot"]
    m_bits, n_bits = _beside_tallies(rec["labels"], rec["counts"])
    rng = np.random.default_rng(seeds["bootstrap_beside"])

    def draw(key):
        o = np.array([x[1] for x in m_bits[key]])
        t = np.array([x[2] for x in m_bits[key]])
        acc1, accn = np.zeros(n_boot), np.zeros(n_boot)
        for _ in range(len(o)):
            pick = rng.integers(0, len(o), size=n_boot)
            acc1 += rng.binomial(t[pick], o[pick] / t[pick])
            accn += t[pick]
        return acc1 / accn

    P = {k: sum(x[1] for x in v) / sum(x[2] for x in v) for k, v in m_bits.items()}
    out: dict = {"readout_P0_given_1": {}, **({"pulse_cost": {}} if pulses else {}), "R1_fit": {}}
    Pb = {}
    for M in order:
        keys = [(M, "Z", 0), (M, "X1", 0)] + ([(M, "XY4", 0)] if pulses else []) + [(M, "R1", p) for p in PHIS4]
        for k in keys:
            Pb[k] = draw(k)
        z, zb = P[(M, "Z", 0)], Pb[(M, "Z", 0)]
        out["readout_P0_given_1"][M] = {"P0_given_1": 1 - P[(M, "X1", 0)], "ci90": pct(1 - Pb[(M, "X1", 0)])}
        if pulses:
            x = (M, "XY4", 0)
            out["pulse_cost"][M] = {
                "P1": P[x],
                "P1_ci90": pct(Pb[x]),
                "P1_minus_Z": P[x] - z,
                "P1_minus_Z_ci90": pct(Pb[x] - zb),
            }
        y = np.array([P[(M, "R1", p)] - z for p in PHIS4])
        yb = np.stack([Pb[(M, "R1", p)] - zb for p in PHIS4], -1)
        th, amp, c, b, s = _fit4(y)
        thb, ampb, *_ = _fit4(yb)
        fit = {
            "loss": dict(zip(map(str, PHIS4), y.tolist())),
            "theta_deg": float(th),
            "theta_ci90": pct(th + _wrap(thb - th)),
            "amplitude": float(amp),
            "amplitude_ci90": pct(ampb),
            "c": float(c),
        }
        if with_bs:
            fit |= {"b": float(b), "s": float(s)}
        fit["residuals"] = (y - _X4 @ np.array([c, b, s])).tolist()
        fit["label"] = "a fit (OLS over the four phases), fixed before the data"
        out["R1_fit"][M] = fit
    if not neighbour_ms:
        return out
    out["neighbours"] = {}
    draws_l1 = {}
    for M in neighbour_ms:
        z, zb = P[(M, "Z", 0)], Pb[(M, "Z", 0)]
        th, thb, fits = {}, {}, {}
        for v in ("idle", "L1", "L3", "both"):
            ks = [(M, f"N-{v}", p) for p in PHIS4]
            for k in ks:
                Pb[k] = draw(k)
            y = np.array([P[k] - z for k in ks])
            yb = np.stack([Pb[k] - zb for k in ks], -1)
            t_, amp, c, b, s = _fit4(y)
            tb, ampb, *_ = _fit4(yb)
            th[v], thb[v] = float(t_), tb

            def nb(p, i, v=v, M=M):
                rows = n_bits[(M, f"N-{v}", p)]
                return sum(x[i] for x in rows) / sum(x[3] for x in rows)

            fits[v] = {
                "loss": dict(zip(map(str, PHIS4), y.tolist())),
                "theta_deg": float(t_),
                "theta_ci90": pct(t_ + _wrap(tb - t_)),
                "amplitude": float(amp),
                "amplitude_ci90": pct(ampb),
                "residuals": (y - _X4 @ np.array([c, b, s])).tolist(),
                "neighbour_bits_P1": {str(p): {"L1_P1": nb(p, 1), "L3_P1": nb(p, 2)} for p in PHIS4},
            }
        shift = {v: float(_wrap(th[v] - th["idle"])) for v in ("L1", "L3", "both")}
        shift_b = {v: shift[v] + _wrap(_wrap(thb[v] - thb["idle"]) - shift[v]) for v in ("L1", "L3", "both")}
        ssum = float(_wrap(shift["L1"] + shift["L3"]))
        ssum_b = ssum + _wrap(_wrap(shift_b["L1"] + shift_b["L3"]) - ssum)
        smb = float(_wrap(ssum - shift["both"]))
        out["neighbours"][M] = {
            "fits": fits,
            "shift_deg": shift,
            "shift_ci90": {v: pct(shift_b[v]) for v in shift},
            "sum_of_singles_deg": ssum,
            "sum_of_singles_ci90": pct(ssum_b),
            "sum_minus_both_deg": smb,
            "sum_minus_both_ci90": pct(smb + _wrap((ssum_b - shift_b["both"]) - smb)),
        }
        draws_l1[M] = shift_b["L1"]
    a, b_ = out["neighbours"]["144"], out["neighbours"]["143"]
    d = float(_wrap(a["shift_deg"]["L1"] - b_["shift_deg"]["L1"]))
    out["pair_143_144"] = {
        "from_144_only_143_in_1": a["shift_deg"]["L1"],
        "from_144_ci90": a["shift_ci90"]["L1"],
        "from_143_only_144_in_1": b_["shift_deg"]["L1"],
        "from_143_ci90": b_["shift_ci90"]["L1"],
        "difference_deg": d,
        "difference_ci90": pct(d + _wrap((draws_l1["144"] - draws_l1["143"]) - d)),
    }
    return out


def _verdict_positions(rec: dict):
    """The positions Kickoffs 54 and 55 passed to Kickoff 53's analysis: the verdict's (parts W and R) only."""
    vl = [(lab, c) for lab, c in zip(rec["labels"], rec["counts"]) if lab["part"] in ("W", "R")]
    return [lab for lab, _ in vl], [c for _, c in vl]


def k54_day_two(rec: dict) -> dict:
    """Kickoff 54, Day 2: Kickoff 53's analysis, unchanged, on the six fixed chains in the rule's order, with its seed
    (bootstrap, 54); H54 on the cells informative by R1, the original rule beside it, the lean; and, from their own
    bootstrap (bootstrap_beside), P(0|1), the pulses' cost, the R1 fits over four phases and the single-neighbour
    shifts on 144 and 143."""
    order = [str(c[1]) for c in rec["meta"]["chains"]]
    labels, counts = _verdict_positions(rec)
    r, cells = _revised_check(rec, order, labels, counts)
    return {
        "H54": r["verdict"],
        "informative_cells": r["informative_cells"],
        "cells": r["cells"],
        "chains": r["chains"],
        "original_rule_and_comparison": r["beside"],
        "lean": _lean(cells),
        "beside": _beside_r1_fits(rec, order, pulses=True, with_bs=False, neighbour_ms=("144", "143")),
    }


def k55_kingston(rec: dict) -> dict:
    """Kickoff 55, the revised check on ibm_kingston: Kickoff 53's analysis, unchanged, on the four chains drawn at
    build, in the drawn order, with its seed (bootstrap, 55); H55, the original rule beside it, the lean; and, from
    their own bootstrap (bootstrap_beside), P(0|1) and the R1 fits over four phases."""
    order = [str(c["chain"][1]) for c in rec["chain_draw"]["drawn"]]
    labels, counts = _verdict_positions(rec)
    r, cells = _revised_check(rec, order, labels, counts)
    run = rec["run"]
    return {
        "H55": r["verdict"],
        "informative_cells": r["informative_cells"],
        "cells": r["cells"],
        "chains": r["chains"],
        "original_rule_and_comparison": r["beside"],
        "lean": _lean(cells),
        "beside": _beside_r1_fits(rec, order, pulses=False, with_bs=True),
        "n_positions_to_verdict": len(labels),
        "calibration_stamps": {
            "chains_drawn_under": rec["chain_draw"]["calibration_stamp"],
            "at_build": run["calibration_at_build"],
            "at_submission": run["calibration_at_submission"],
            "after_fetch": run["calibration_after_fetch"],
        },
    }


# --------------------------------------------------------------------------- Kickoffs 56 to 62 (Amendment A24)
#: Kickoff 56's verdict, fixed before the data (k56-rule.md): LARGE outside +-10 degrees, SMALL inside +-5
K56_LARGE_DEG, K56_SMALL_DEG = 10.0, 5.0


def k56_phase_sweep(rec: dict) -> dict:
    """Kickoff 56, the phase sweep on finding 20's chains, as its analysis fixed it before the data (analyse_56.py,
    through Kickoff 52's fits): per M (7, 43, 18), F_no(phi) at six phases and F_ref, M's losses in R0 and R1; the
    fitted offsets theta_W, theta_R0 and theta_R1; the leftover L = theta_W - theta_R1 and the two differences beside
    it; d1 and d0 at every phase and their means (the lean); one joint bootstrap (seed bootstrap), refitting on every
    resample; after the three M, the pulse-cost circuit's P(1) from the same generator. H56a to H56c."""
    seeds = rec["meta"]["seeds"]
    order, name = ("7", "43", "18"), {"7": "H56a", "43": "H56b", "18": "H56c"}
    lo_deg, sm_deg = K56_LARGE_DEG, K56_SMALL_DEG

    def near(draws, point):
        return point + _wrap(np.asarray(draws) - point)

    def verdict_of(ci):
        lo, hi = ci
        if lo > lo_deg or hi < -lo_deg:
            return "LARGE"
        if lo > -sm_deg and hi < sm_deg:
            return "SMALL"
        return "NOT SETTLED"

    cells, bits, pooled = _cells_and_bits(
        rec["labels"], rec["counts"], lambda lab: (str(lab["M"]), lab["circuit"], lab["phi_deg"])
    )
    draw_F, draw_P = _draws(np.random.default_rng(seeds["bootstrap"]), seeds["n_boot"], cells, bits)
    ideal = wait.wait_test_ideal()
    out, zdraws = {}, {}
    for M in order:
        wkeys = [(M, "W-no", p) for p in K52_PHIS] + [(M, "W-ref", 0)]
        rkeys = [(M, "Z", 0)] + [(M, c, p) for c in ("R0", "R1") for p in K52_PHIS]
        Fb = {k: draw_F(k) for k in wkeys}
        Pb = {k: draw_P(k) for k in rkeys}
        Fp = {k: wait.fidelity(dict(pooled[k]), ideal) for k in wkeys}
        P = {k: _p1(bits, k) for k in rkeys}
        z = (M, "Z", 0)
        zdraws[M] = (P[z], Pb[z])
        y = {"W": np.array([Fp[(M, "W-no", p)] for p in K52_PHIS])}
        yb = {"W": np.stack([Fb[(M, "W-no", p)] for p in K52_PHIS], -1)}
        for c in ("R0", "R1"):
            y[c] = np.array([P[(M, c, p)] - P[z] for p in K52_PHIS])
            yb[c] = np.stack([Pb[(M, c, p)] - Pb[z] for p in K52_PHIS], -1)
        th = {"W": wait.sweep_fit(y["W"], "W-no")["theta_deg"]}
        th |= {c: wait.sweep_fit(y[c], c)["theta_deg"] for c in ("R0", "R1")}
        thb = {"W": theta_wait_test(yb["W"]), "R0": theta_ramsey(yb["R0"]), "R1": theta_ramsey(yb["R1"])}
        diffs = {}
        for dn, (a, b) in (("L_W_minus_R1", ("W", "R1")), ("W_minus_R0", ("W", "R0")), ("R1_minus_R0", ("R1", "R0"))):
            pt = wait.leftover(th[a], th[b])
            diffs[dn] = {"deg": pt, "ci90": pct(near(_wrap(thb[a] - thb[b]), pt))}
        fits = {}
        for c in ("W", "R0", "R1"):
            c0, b, s = _fit6(y[c])
            _, bb, sb = _fit6(yb[c])
            fits[c] = {
                "theta_deg": th[c],
                "theta_ci90": pct(near(thb[c], th[c])),
                "c": float(c0),
                "b": float(b),
                "s": float(s),
                "amplitude": float(math.hypot(b, s)),
                "amplitude_ci90": pct(np.hypot(bb, sb)),
                "residuals": (y[c] - _K52_X @ np.array([c0, b, s])).tolist(),
                "y": y[c].tolist(),
                "label": "a fit (OLS of c + b cos phi + s sin phi over the six phases), fixed before the data",
            }
        f_ref, f_ref_b = Fp[(M, "W-ref", 0)], Fb[(M, "W-ref", 0)]
        resid = {}
        for t, c in (("d0", "R0"), ("d1", "R1")):
            dp = y["W"] - f_ref * (1 - y[c])
            db = yb["W"] - f_ref_b[:, None] * (1 - yb[c])
            resid[t] = {str(p): float(dp[i]) for i, p in enumerate(K52_PHIS)}
            resid[t + "_ci90"] = {str(p): pct(db[:, i]) for i, p in enumerate(K52_PHIS)}
            resid[f"mean_{t}"] = float(dp.mean())
            resid[f"mean_{t}_ci90"] = pct(db.mean(1))
        out[M] = {
            "verdict_name": name[M],
            "verdict": verdict_of(diffs["L_W_minus_R1"]["ci90"]),
            **diffs,
            "fits": fits,
            "F_no": {str(p): Fp[(M, "W-no", p)] for p in K52_PHIS},
            "F_no_ci90": {str(p): pct(Fb[(M, "W-no", p)]) for p in K52_PHIS},
            "F_ref": f_ref,
            "F_ref_ci90": pct(f_ref_b),
            "P1_Z": P[z],
            "P1_Z_ci90": pct(Pb[z]),
            "loss": {f"{c}|{p}": float(y[c][i]) for c in ("R0", "R1") for i, p in enumerate(K52_PHIS)},
            "loss_ci90": {f"{c}|{p}": pct(yb[c][:, i]) for c in ("R0", "R1") for i, p in enumerate(K52_PHIS)},
            **resid,
            "lean_mean_d1": resid["mean_d1"],
            "lean_mean_d1_ci90": resid["mean_d1_ci90"],
        }
    for M in order:
        k = (M, "XY4", 0)
        pz, pzb = zdraws[M]
        pb, p = draw_P(k), _p1(bits, k)
        out[M]["pulse_cost"] = {"P1": p, "P1_ci90": pct(pb), "P1_minus_Z": p - pz, "P1_minus_Z_ci90": pct(pb - pzb)}
    run = rec["run"]
    return {
        **{name[M]: out[M]["verdict"] for M in order},
        "per_M": out,
        "calibration_stamps": {
            "at_build": run["calibration_at_build"],
            "at_submission": run["calibration_at_submission"],
            "after_fetch": run["calibration_after_fetch"],
        },
    }


def _jobs(rec: dict) -> dict:
    """A record's labels and counts, split by the job each position's label names."""
    out: dict = {}
    for lab, cts in zip(rec["labels"], rec["counts"]):
        out.setdefault(lab["job"], ([], []))
        out[lab["job"]][0].append(lab)
        out[lab["job"]][1].append(cts)
    return out


def _sweep_peaks(labels1, counts1, order) -> dict:
    """The peak procedure on job 1, from the point estimate, with the package's fit and peak (Kickoffs 57 to 62's
    analyse_57.peaks): per M, R1's P(1) at the six phases, the copies pooled; theta_R1; phi*."""
    _, bits, _ = _cells_and_bits(labels1, counts1, lambda lab: (str(lab["M"]), lab["phi_deg"]))
    out = {}
    for M in order:
        y = [_p1(bits, (M, p)) for p in wait.SWEEP_PHASES_DEG]
        f = wait.sweep_fit(y, "R1")
        out[M] = {"P1": y, "fit": f, "theta_R1_deg": f["theta_deg"], "phi_star_deg": wait.peak_phase(f["theta_deg"])}
    return out


def _peak_check(rec: dict, order) -> tuple[dict, dict]:
    """Kickoff 57's analysis (analyse_57.py), reused unchanged by Kickoffs 59 and 62 with their seeds: the verdict by
    Kickoff 53's analysis on the phi* circuits, W-ref and Z (`_revised_check`, with the phi* circuits labelled 0);
    beside it, from one generator with the verdict's seed that first repeats the verdict's draws, the check at +90 on
    the same chains, the original rule at phi* and at +90, job 1's fits with their intervals, and the drift between the
    jobs. phi* is recomputed from job 1's counts by the package (`_sweep_peaks`) and must equal the peaks recorded
    before job 2. Returns the analysis (its verdict under "H") and the jobs."""
    jobs = _jobs(rec)
    (labels1, counts1), (labels2, counts2) = jobs[1], jobs[2]
    seeds, fixed = rec["meta"]["seeds"], rec["fixed_before_the_data"]
    margin, floor = fixed["margin"], fixed["informative_floor"]
    peaks = _sweep_peaks(labels1, counts1, order)
    phistar = {M: peaks[M]["phi_star_deg"] for M in order}
    recorded = {M: rec["peaks"]["peaks"][M]["phi_star_deg"] for M in order}
    if phistar != recorded:
        raise RuntimeError(f"the peaks recomputed from job 1 ({phistar}) are not the peaks recorded ({recorded})")
    sel = [
        ({**lab, "phi_deg": 0}, cts)
        for lab, cts in zip(labels2, counts2)
        if lab["role"] == "peak" or lab["circuit"] in ("W-ref", "Z")
    ]
    r53, _ = _revised_check(rec, order, [x[0] for x in sel], [x[1] for x in sel], phis=(0,))

    cells, bits, pooled = _cells_and_bits(labels2, counts2, lambda lab: (str(lab["M"]), lab["circuit"], lab["role"]))
    _, bits1, _ = _cells_and_bits(labels1, counts1, lambda lab: (str(lab["M"]), "R1-sweep", lab["phi_deg"]))
    bits.update(bits1)
    draw_F, draw_P = _draws(np.random.default_rng(seeds["bootstrap"]), seeds["n_boot"], cells, bits)
    ideal = wait.wait_test_ideal()
    P = {k: _p1(bits, k) for k in bits}
    Fp = {k: wait.fidelity(dict(v), ideal) for k, v in pooled.items()}
    Fb, Pb = {}, {}
    for M in order:  # the verdict's draws, in Kickoff 53's order
        for k in ((M, "W-no", "peak"), (M, "W-ref", "ref")):
            Fb[k] = draw_F(k)
        for k in ((M, "Z", "zero"), (M, "R0", "peak"), (M, "R1", "peak")):
            Pb[k] = draw_P(k)
    c53 = {c["M"]: c for c in r53["cells"]}
    same = True
    for M in order:
        z, zb, fr, frb = P[(M, "Z", "zero")], Pb[(M, "Z", "zero")], Fp[(M, "W-ref", "ref")], Fb[(M, "W-ref", "ref")]
        l1, l1b = P[(M, "R1", "peak")] - z, Pb[(M, "R1", "peak")] - zb
        d1, d1ci = Fp[(M, "W-no", "peak")] - fr * (1 - l1), pct(Fb[(M, "W-no", "peak")] - frb * (1 - l1b))
        same = same and abs(d1 - c53[M]["d1"]) < 1e-12 and np.allclose(d1ci, c53[M]["d1_ci90"], rtol=0, atol=1e-12)
    if not same:
        raise RuntimeError("the joint generator does not repeat Kickoff 53's verdict draws")
    for M in order:
        Fb[(M, "W-no", "plus90")] = draw_F((M, "W-no", "plus90"))
        for k in ((M, "R0", "plus90"), (M, "R1", "plus90")):
            Pb[k] = draw_P(k)
    p90 = []
    for M in order:
        z, zb, fr, frb = P[(M, "Z", "zero")], Pb[(M, "Z", "zero")], Fp[(M, "W-ref", "ref")], Fb[(M, "W-ref", "ref")]
        fno, fnob = Fp[(M, "W-no", "plus90")], Fb[(M, "W-no", "plus90")]
        l0, l0b = P[(M, "R0", "plus90")] - z, Pb[(M, "R0", "plus90")] - zb
        l1, l1b = P[(M, "R1", "plus90")] - z, Pb[(M, "R1", "plus90")] - zb
        c = {
            "cell": f"{M}|+90",
            "M": M,
            "phi_deg": 90,
            "F_no": fno,
            "F_no_ci90": pct(fnob),
            "F_ref": fr,
            "loss_R0": l0,
            "loss_R0_ci90": pct(l0b),
            "loss_R1": l1,
            "loss_R1_ci90": pct(l1b),
            "d1": fno - fr * (1 - l1),
            "d1_ci90": pct(fnob - frb * (1 - l1b)),
            "d0": fno - fr * (1 - l0),
            "d0_ci90": pct(fnob - frb * (1 - l0b)),
        }
        c["informative_R1"] = c["loss_R1_ci90"][0] > floor
        c["informative_R0"] = c["loss_R0_ci90"][0] > floor
        p90.append(c)
    v90, inf90 = _margin_rule(p90, "d1", "loss_R1", margin, floor)
    v90_0, inf90_0 = _margin_rule(p90, "d0", "loss_R0", margin, floor)
    fits1 = {}
    for M in order:
        ks = [(M, "R1-sweep", p) for p in K52_PHIS]
        for k in ks:
            Pb[k] = draw_P(k)
        y = np.array([P[k] for k in ks])
        yb = np.stack([Pb[k] for k in ks], -1)
        c0, b, s = (float(v) for v in _fit6(y))
        _, bb, sb = _fit6(yb)
        th, thb = float(theta_ramsey(y)), theta_ramsey(yb)
        fits1[M] = {
            "theta_R1_deg": th,
            "theta_ci90": pct(th + _wrap(thb - th)),
            "amplitude": math.hypot(b, s),
            "amplitude_ci90": pct(np.hypot(bb, sb)),
            "c": c0,
            "b": b,
            "s": s,
            "residuals": (y - _K52_X @ np.array([c0, b, s])).tolist(),
            "P1": dict(zip(map(str, K52_PHIS), y.tolist())),
            "phi_star_from_this_fit": wait.peak_phase(th),
        }
    drift = {}
    for M in order:
        ph, f = math.radians(phistar[M]), fits1[M]
        p1_fit = f["c"] + f["b"] * math.cos(ph) + f["s"] * math.sin(ph)
        p1_j2, z = P[(M, "R1", "peak")], P[(M, "Z", "zero")]
        drift[M] = {
            "phi_star_deg": phistar[M],
            "R1_P1_job2": p1_j2,
            "R1_P1_job1_fit_at_phi_star": p1_fit,
            "difference_P1": p1_j2 - p1_fit,
            "R1_loss_job2": p1_j2 - z,
            "R1_loss_job1_fit_minus_job2_Z": p1_fit - z,
            "job1_fit_maximum_P1": f["c"] + f["amplitude"],
        }
    d1 = [c["d1"] for c in r53["cells"]]
    out = {
        "H": r53["verdict"],
        "informative_cells": r53["informative_cells"],
        "cells_phi_star": r53["cells"],
        "chains": r53["chains"],
        "phi_star_deg": phistar,
        "original_rule_at_phi_star": {
            "verdict": r53["beside"]["original_rule_verdict"],
            "informative": r53["beside"]["original_rule_informative_cells"],
        },
        "comparison_at_phi_star": r53["beside"],
        "check_at_plus90": {
            "cells": p90,
            "verdict": v90,
            "informative_cells": inf90,
            "original_rule_verdict": v90_0,
            "original_rule_informative_cells": inf90_0,
        },
        "lean_phi_star": {
            "d1": {c["M"]: c["d1"] for c in r53["cells"]},
            "mean_d1": float(np.mean(d1)),
            "n_d1_above_zero": int(sum(x > 0 for x in d1)),
        },
        "job1_fits": fits1,
        "drift": drift,
        "joint_generator_repeats_analyse_53": same,
    }
    return out, jobs


def _drawn_order(rec: dict) -> list:
    return [str(c["chain"][1]) for c in rec["chain_draw"]["drawn"]]


def k57_peak_check(rec: dict) -> dict:
    """Kickoff 57, the check at the peak phase on ibm_kingston (analyse_57.py): H57 on the four phi* cells, and beside
    it the check at +90, the original rule, job 1's fits and the drift."""
    r, _ = _peak_check(rec, _drawn_order(rec))
    return {"H57": r.pop("H"), **r}


def k59_peak_check_day_two(rec: dict) -> dict:
    """Kickoff 59, the check at the peak phase on a second calibration day (analyse_59.py: Kickoff 57's analysis with
    its seeds), and each waiting qubit's zero-wait baseline beside it."""
    r, _ = _peak_check(rec, _drawn_order(rec))
    out = {"H59": r.pop("H"), **r}
    out["zero_wait_baseline"] = {
        M: {"P1_Z": v["P1_Z"], "P1_Z_ci90": v["P1_Z_ci90"], "above_0.1": v["P1_Z"] > 0.1}
        for M, v in r["chains"].items()
    }
    out["zero_wait_baseline_any_above_0.1"] = [M for M, v in out["zero_wait_baseline"].items() if v["above_0.1"]]
    return out


#: Kickoff 58's figures from Kickoffs 55 and 56, as its analysis carried them (k58-rule.md quotes the same)
K56_THETA_R1_AS_CARRIED = {"7": 16.26, "43": -37.32, "18": -38.11}
K56_IMPLIED_PEAK_AS_CARRIED = {"7": 164, "43": 217, "18": 218}
K55_D1_PLUS90_AS_CARRIED = {"7": 0.257, "43": 0.160, "18": 0.073}


def k58_placement(rec: dict) -> dict:
    """Kickoff 58, the placement comparison on finding 20's chains (analyse_58.py): per chain, d1 at phi* and at +90 in
    one job, D = |d1(+90)| - |d1(phi*)| and H58a to H58c by the 0.02 band; beside, the original rule's D0, the margin at
    each placement, job 1's fit beside Kickoff 56's, the drift and the +90 cells beside Kickoff 55's. One joint
    bootstrap (seed bootstrap) in the analysis's order."""
    fixed, seeds = rec["fixed_before_the_data"], rec["meta"]["seeds"]
    band, margin, floor = fixed["band"], fixed["margin"], fixed["informative_floor"]
    order, name = ("7", "43", "18"), {"7": "H58a", "43": "H58b", "18": "H58c"}
    jobs = _jobs(rec)
    (labels1, counts1), (labels2, counts2) = jobs[1], jobs[2]
    peaks = _sweep_peaks(labels1, counts1, order)
    phistar = {M: peaks[M]["phi_star_deg"] for M in order}
    if phistar != {M: rec["peaks"]["peaks"][M]["phi_star_deg"] for M in order}:
        raise RuntimeError("the peaks recomputed from job 1 are not the peaks recorded")

    def verdict_of(ci):
        lo, hi = ci
        if lo > band:
            return "PEAK SMALLER"
        if hi < -band:
            return "PLUS-90 SMALLER"
        return "NOT SEPARATED"

    def margin_of(ci):
        lo, hi = ci
        if lo > -margin and hi < margin:
            return "inside"
        if lo > margin or hi < -margin:
            return "outside"
        return "across"

    cells, bits, pooled = _cells_and_bits(labels2, counts2, lambda lab: (str(lab["M"]), lab["circuit"], lab["role"]))
    _, bits1, _ = _cells_and_bits(labels1, counts1, lambda lab: (str(lab["M"]), "R1-sweep", lab["phi_deg"]))
    bits.update(bits1)
    draw_F, draw_P = _draws(np.random.default_rng(seeds["bootstrap"]), seeds["n_boot"], cells, bits)
    ideal = wait.wait_test_ideal()
    P = {k: _p1(bits, k) for k in bits}
    Fp = {k: wait.fidelity(dict(v), ideal) for k, v in pooled.items()}
    Fb, Pb = {}, {}
    for M in order:
        for k in ((M, "W-no", "peak"), (M, "W-no", "plus90"), (M, "W-ref", "ref")):
            Fb[k] = draw_F(k)
        for k in ((M, "Z", "zero"), (M, "R1", "peak"), (M, "R1", "plus90")):
            Pb[k] = draw_P(k)
    for M in order:
        for k in ((M, "R0", "peak"), (M, "R0", "plus90")):
            Pb[k] = draw_P(k)
    for M in order:
        for p in K52_PHIS:
            Pb[(M, "R1-sweep", p)] = draw_P((M, "R1-sweep", p))
    per = {}
    for M in order:
        z, zb = P[(M, "Z", "zero")], Pb[(M, "Z", "zero")]
        fr, frb = Fp[(M, "W-ref", "ref")], Fb[(M, "W-ref", "ref")]
        cell, cellb = {}, {}
        for role in ("peak", "plus90"):
            fno, fnob = Fp[(M, "W-no", role)], Fb[(M, "W-no", role)]
            c = {"phi_deg": phistar[M] if role == "peak" else 90, "F_no": fno, "F_no_ci90": pct(fnob)}
            for r_, R in (("1", "R1"), ("0", "R0")):
                lo, lb = P[(M, R, role)] - z, Pb[(M, R, role)] - zb
                d, db = fno - fr * (1 - lo), fnob - frb * (1 - lb)
                c.update({f"loss_{R}": lo, f"loss_{R}_ci90": pct(lb), f"d{r_}": d, f"d{r_}_ci90": pct(db)})
                cellb[(role, r_)] = db
            c["informative_R1"] = c["loss_R1_ci90"][0] > floor
            c["informative_R0"] = c["loss_R0_ci90"][0] > floor
            c["d1_margin"] = margin_of(c["d1_ci90"])
            c["d0_margin"] = margin_of(c["d0_ci90"])
            cell[role] = c
        D = abs(cell["plus90"]["d1"]) - abs(cell["peak"]["d1"])
        Db = np.abs(cellb[("plus90", "1")]) - np.abs(cellb[("peak", "1")])
        D0 = abs(cell["plus90"]["d0"]) - abs(cell["peak"]["d0"])
        D0b = np.abs(cellb[("plus90", "0")]) - np.abs(cellb[("peak", "0")])
        ks = [(M, "R1-sweep", p) for p in K52_PHIS]
        y = np.array([P[k] for k in ks])
        yb = np.stack([Pb[k] for k in ks], -1)
        c0, b, s = (float(v) for v in _fit6(y))
        _, bb, sb = _fit6(yb)
        th, thb = float(theta_ramsey(y)), theta_ramsey(yb)
        ph = math.radians(phistar[M])
        p1_fit = c0 + b * math.cos(ph) + s * math.sin(ph)
        per[M] = {
            "verdict_name": name[M],
            "verdict": verdict_of(pct(Db)),
            "phi_star_deg": phistar[M],
            "D": D,
            "D_ci90": pct(Db),
            "cells": cell,
            "F_ref": fr,
            "F_ref_ci90": pct(frb),
            "P1_Z": z,
            "P1_Z_ci90": pct(zb),
            "original_rule": {"D0": D0, "D0_ci90": pct(D0b), "verdict_by_the_same_band": verdict_of(pct(D0b))},
            "job1_fit": {
                "theta_R1_deg": th,
                "theta_ci90": pct(th + _wrap(thb - th)),
                "amplitude": math.hypot(b, s),
                "amplitude_ci90": pct(np.hypot(bb, sb)),
                "c": c0,
                "b": b,
                "s": s,
                "residuals": (y - _K52_X @ np.array([c0, b, s])).tolist(),
                "P1": dict(zip(map(str, K52_PHIS), y.tolist())),
                "kickoff_56_theta_R1_deg": K56_THETA_R1_AS_CARRIED[M],
                "theta_minus_kickoff_56_deg": float(_wrap(th - K56_THETA_R1_AS_CARRIED[M])),
                "kickoff_56_implied_peak_deg": K56_IMPLIED_PEAK_AS_CARRIED[M],
            },
            "drift": {
                "R1_P1_job2_at_phi_star": P[(M, "R1", "peak")],
                "R1_P1_job1_fit_at_phi_star": p1_fit,
                "difference_P1": P[(M, "R1", "peak")] - p1_fit,
                "R1_loss_job2": P[(M, "R1", "peak")] - z,
                "R1_loss_job1_fit_minus_job2_Z": p1_fit - z,
            },
            "plus90_beside_kickoff_55": {
                "d1_this_run": cell["plus90"]["d1"],
                "d1_ci90_this_run": cell["plus90"]["d1_ci90"],
                "d1_kickoff_55": K55_D1_PLUS90_AS_CARRIED[M],
            },
        }
    return {**{name[M]: per[M]["verdict"] for M in order}, "per_chain": per}


def k61_readout(rec: dict) -> dict:
    """Kickoff 61, the readout check on ibm_fez (analyse_61.py): per qubit of the sixteen, P(1|0) from A, P(0|1) from B
    and e = (P(1|0) + P(0|1)) / 2, the copies pooled, with one bootstrap (seed bootstrap) in the analysis's order (A
    and B drawn jointly over the sixteen qubits, then M-zero, M-one and Z per M); each qubit CONSISTENT or INCONSISTENT
    with the published readout error at the stamp in force at submission and at each later stamp dated before the job
    finished; H61; beside it, e below 0.05, each M alone against together, and the zero-wait baselines."""
    m, fixed = rec["meta"], rec["fixed_before_the_data"]
    seeds, qubits, ms = m["seeds"], [int(q) for q in m["qubits"]], [int(x) for x in m["M"]]
    n_boot, chunk = seeds["n_boot"], 1_000
    floor, at = 0.02, fixed["not_readable_at_or_above"]

    def tol(p):
        return max(floor, p / 2)

    g: dict = {}
    for lab, cts in zip(rec["labels"], rec["counts"]):
        g.setdefault((lab["circuit"], lab["M"]), []).append(
            (lab["copy"], {k.replace(" ", ""): int(n) for k, n in cts.items()})
        )
    for k in g:
        g[k].sort(key=lambda x: x[0])
    rng = np.random.default_rng(seeds["bootstrap"])
    n = len(qubits)

    def joint(key, flip):
        copies = g[key]
        keys = sorted({k for _, d in copies for k in d})
        B = np.array([[int(k[::-1][i]) for i in range(n)] for k in keys], dtype=np.int64)
        if flip:
            B = 1 - B
        V = np.array([[d.get(k, 0) for k in keys] for _, d in copies], float)
        tot = V.sum(1)
        point = (V.sum(0) @ B) / tot.sum()
        freq = V / tot[:, None]
        draws = np.zeros((n_boot, n))
        idx = rng.integers(0, V.shape[0], size=(n_boot, V.shape[0]))
        for s in range(0, n_boot, chunk):
            acc, accn = np.zeros((min(chunk, n_boot - s), n)), np.zeros(min(chunk, n_boot - s))
            for j in range(V.shape[0]):
                pick = idx[s : s + chunk, j]
                acc += rng.multinomial(tot[pick].astype(np.int64), freq[pick]) @ B
                accn += tot[pick]
            draws[s : s + chunk] = acc / accn[:, None]
        return point, draws

    def single(key, target):
        copies = g[key]
        o = np.array([sum(v for k, v in d.items() if k[-1] == str(target)) for _, d in copies])
        t = np.array([sum(d.values()) for _, d in copies])
        acc1, accn = np.zeros(n_boot), np.zeros(n_boot)
        for _ in range(len(o)):
            pick = rng.integers(0, len(o), size=n_boot)
            acc1 += rng.binomial(t[pick], o[pick] / t[pick])
            accn += t[pick]
        return float(o.sum() / t.sum()), acc1 / accn

    p10, p10b = joint(("A", None), flip=False)
    p01, p01b = joint(("B", None), flip=True)
    e, eb = (p10 + p01) / 2, (p10b + p01b) / 2
    alone = {}
    for M in ms:
        a10, a10b = single(("M-zero", M), 1)
        a01, a01b = single(("M-one", M), 0)
        z1, z1b = single(("Z", M), 1)
        i = qubits.index(M)
        alone[str(M)] = {
            "alone": {
                "P10": a10,
                "P10_ci90": pct(a10b),
                "P01": a01,
                "P01_ci90": pct(a01b),
                "e": (a10 + a01) / 2,
                "e_ci90": pct((a10b + a01b) / 2),
            },
            "together": {
                "P10": float(p10[i]),
                "P10_ci90": pct(p10b[:, i]),
                "P01": float(p01[i]),
                "P01_ci90": pct(p01b[:, i]),
                "e": float(e[i]),
                "e_ci90": pct(eb[:, i]),
            },
            "alone_minus_together": {
                "P10": a10 - float(p10[i]),
                "P10_ci90": pct(a10b - p10b[:, i]),
                "P01": a01 - float(p01[i]),
                "P01_ci90": pct(a01b - p01b[:, i]),
            },
            "Z_P1": z1,
            "Z_P1_ci90": pct(z1b),
            "Z_above_0.1": z1 > 0.1,
        }
    per_q = {
        str(q): {
            "P10": float(p10[i]),
            "P10_ci90": pct(p10b[:, i]),
            "P01": float(p01[i]),
            "P01_ci90": pct(p01b[:, i]),
            "e": float(e[i]),
            "e_ci90": pct(eb[:, i]),
            "e_below_0.05": bool(e[i] < 0.05),
        }
        for i, q in enumerate(qubits)
    }
    # the stamp in force at submission, then each distinct stamp dated after it and no later than the job's finish
    stamps = rec["calibration_record"]["stamps"]
    s0 = rec["run"]["calibration_at_submission_utc"]
    fin = _utc(rec["timestamps"]["finished"].replace("Z", "+00:00"))
    by_stamp: dict = {}
    for row in stamps:
        by_stamp.setdefault(row["stamp_utc"], row)
    pubs = {"at submission": by_stamp[s0]}
    for st, row in sorted(by_stamp.items()):
        if _utc(st.replace("Z", "+00:00")) > _utc(s0.replace("Z", "+00:00")) and _utc(st.replace("Z", "+00:00")) <= fin:
            pubs[f"new stamp {st}"] = row
    import json

    comparisons = {}
    for lab, row in pubs.items():
        pub = json.loads(row["readout_error_16"])
        v, rows = {}, {}
        for q in qubits:
            p = pub[str(q)]
            ci = per_q[str(q)]["e_ci90"]
            lo, hi = ci
            v[str(q)] = "CONSISTENT" if (lo <= p + tol(p) and hi >= p - tol(p)) else "INCONSISTENT"
            rows[str(q)] = {
                "p": p,
                "tolerance": tol(p),
                "accepted_range": [p - tol(p), p + tol(p)],
                "e": per_q[str(q)]["e"],
                "e_ci90": ci,
                "e_minus_p": per_q[str(q)]["e"] - p,
                "verdict": v[str(q)],
            }
        n_in = sum(x == "INCONSISTENT" for x in v.values())
        H = "PUBLISHED READABLE" if n_in == 0 else ("PUBLISHED NOT READABLE" if n_in >= at else "MIXED")
        comparisons[lab] = {
            "stamp_utc": row["stamp_utc"],
            "per_qubit": rows,
            "n_inconsistent": n_in,
            "inconsistent": [q for q in v if v[q] == "INCONSISTENT"],
            "H61": H,
        }
    return {
        "H61": comparisons["at submission"]["H61"],
        "H61_by_stamp": {k: c["H61"] for k, c in comparisons.items()},
        "per_qubit": per_q,
        "comparisons": comparisons,
        "beside": {
            "all_e_below_0.05": all(r["e_below_0.05"] for r in per_q.values()),
            "qubits_e_at_or_above_0.05": [q for q, r in per_q.items() if not r["e_below_0.05"]],
            "alone_against_together": alone,
            "any_Z_above_0.1": any(a["Z_above_0.1"] for a in alone.values()),
        },
    }


def k62_survey(rec: dict) -> tuple[dict, dict]:
    """Kickoff 62's survey (job 0) by the package's readout_errors: per qubit P(1|0), P(0|1) and e, the copies pooled,
    with the 3% screen the rule fixed; and the published values at the survey's submission, from the record."""
    lab0, cnt0 = _jobs(rec)[0]
    s0 = [c for lab, c in sorted(zip(lab0, cnt0), key=lambda x: x[0]["copy"]) if lab["circuit"] == "S0"]
    s1 = [c for lab, c in sorted(zip(lab0, cnt0), key=lambda x: x[0]["copy"]) if lab["circuit"] == "S1"]
    errs = wait.readout_errors(s0, s1, rec["design"]["survey"]["screen"])
    pub = {q: {k: v["value"] for k, v in row.items()} for q, row in rec["published_at_the_stamp"]["qubits"].items()}
    return errs, pub


def k62_peak_check_fez(rec: dict) -> dict:
    """Kickoff 62, the check at the peak phase on ibm_fez, drawn on measured readout (analyse_62.py: Kickoff 59's
    analysis with its seeds): H62 on the four phi* cells and the list beside it; each M's readout measured alone in job
    2 beside the survey's and the published values; and the survey against the published table, with the counts each
    readout screen alone excludes."""
    order = _drawn_order(rec)
    r, jobs = _peak_check(rec, order)
    out = {"H62": r.pop("H"), **r}
    out["zero_wait_baseline"] = {
        M: {"P1_Z": v["P1_Z"], "P1_Z_ci90": v["P1_Z_ci90"], "above_0.1": v["P1_Z"] > 0.1}
        for M, v in r["chains"].items()
    }
    out["zero_wait_baseline_any_above_0.1"] = [M for M, v in out["zero_wait_baseline"].items() if v["above_0.1"]]
    labels2, counts2 = jobs[2]
    _, bits, _ = _cells_and_bits(
        [lab for lab in labels2 if lab["circuit"] in ("P10", "P01")],
        [c for lab, c in zip(labels2, counts2) if lab["circuit"] in ("P10", "P01")],
        lambda lab: (str(lab["M"]), lab["circuit"]),
    )
    ro = {}
    for M in order:
        p10, p01 = bits[(M, "P10")], bits[(M, "P01")]
        ro[M] = {
            "P1_given_0": sum(x[1] for x in p10) / sum(x[2] for x in p10),
            "P1_given_0_by_copy": [x[1] / x[2] for x in p10],
            "P0_given_1": 1 - sum(x[1] for x in p01) / sum(x[2] for x in p01),
            "P0_given_1_by_copy": [1 - x[1] / x[2] for x in p01],
            "shots": {"P10": [x[2] for x in p10], "P01": [x[2] for x in p01]},
        }
        ro[M]["mean_of_the_two"] = (ro[M]["P1_given_0"] + ro[M]["P0_given_1"]) / 2
    out["readout_measured"] = ro
    errs, pub = k62_survey(rec)
    fields = ("readout_error", "prob_meas1_prep0", "prob_meas0_prep1")
    out["readout_beside"] = {
        M: {
            "alone_job2": {k: ro[M][k] for k in ("P1_given_0", "P0_given_1", "mean_of_the_two")},
            "survey_job0": {k: errs[M][k] for k in ("P1_given_0", "P0_given_1", "e")},
            **{
                w: {k: pub[M][k] for k in fields}
                for w in ("published_at_survey_submission", "published_at_job2_running", "published_at_job2_submission")
            },
        }
        for M in order
    }
    stamp = rec["run"]["0"]["calibration_at_submission_utc"]
    assert (
        stamp
        == rec["run"]["2"]["calibration_at_submission_utc"]
        == rec["calibration_record"]["stamps"][-1]["stamp_utc"]
    )
    out["readout_published_stamps"] = {
        "at_job2_running": {"stamp_utc": stamp},
        "at_job2_submission": {"stamp_utc": stamp},
        "at_survey_submission": stamp,
        "job2_running_utc_by_ibm": rec["timestamps"]["2"]["running"],
    }
    e = np.array([v["e"] for v in errs.values()])
    p = np.array([pub[q]["readout_error"] for q in errs])
    meas = sorted(int(q) for q, v in errs.items() if v["above_limit"])
    pubs = sorted(int(q) for q in errs if pub[q]["readout_error"] > 0.03)
    lab0, cnt0 = jobs[0]
    shots = {
        c: [sum(x.values()) for lab, x in sorted(zip(lab0, cnt0), key=lambda y: y[0]["copy"]) if lab["circuit"] == c]
        for c in ("S0", "S1")
    }
    draw = rec["chain_draw"]
    out["survey_against_table"] = {
        "summary": {
            "n_qubits": len(errs),
            "shots": shots,
            "e_min": float(e.min()),
            "e_max": float(e.max()),
            "e_median": float(np.median(e)),
            "n_measured_above_3pct": len(meas),
            "measured_above_3pct": meas,
            "p_min": float(p.min()),
            "p_max": float(p.max()),
            "p_median": float(np.median(p)),
            "n_published_above_3pct": len(pubs),
            "published_above_3pct": pubs,
            "above_3pct_both": sorted(set(meas) & set(pubs)),
            "above_3pct_measured_only": sorted(set(meas) - set(pubs)),
            "above_3pct_published_only_count": len(set(pubs) - set(meas)),
        },
        "stamp_utc": stamp,
        "per_qubit": {q: {"e": v["e"], "published_readout_error": pub[q]["readout_error"]} for q, v in errs.items()},
        "chains_each_exclusion_alone_over_all_candidates": draw["each_exclusion_alone_over_all_candidates"],
        "chains_each_exclusion_alone_over_candidates_without_a_used_qubit": draw[
            "each_exclusion_alone_over_candidates_without_a_used_qubit"
        ],
        "chains_readout_screens_over_candidates_without_a_used_qubit": draw[
            "readout_screens_over_candidates_without_a_used_qubit"
        ],
    }
    return out


# --------------------------------------------------------------------------- test 7 (Amendment A25)
#: Test 7's seeds, as its rule and its analysis's docstring fixed them before the data
T7_SEEDS = {
    "S_starts": 7302,
    "P_random_starts": 7303,
    "bootstrap": 7304,
    "T_random_starts": 7305,
    "periodogram_noise": 7306,
}
#: The rule's thresholds, the caller's to pass: the held-out margin, delta's floor in MHz, b's edges
T7_RULE = {"margin": 0.01, "delta_floor_mhz": 0.005, "b_edges": (0.05, 0.95)}
T7_N_NOISE = 1_000
T7_WAIT_TEST_WAIT_US = 10.45  # the wait test's own wait on 143, as the rule names it
#: Beside the verdict, as analyse_t7.py fixed them: the telegraph model T (version 4's, with its bounds and grid
#: starts), the four-tone sideband model at finding 21's shifts, and the published rates set beside gamma
T7_T_BOUNDS = ((0, 0, 0.5, -0.3, 0, 0, 0), (1, 1, 1e4, 0.3, 2 * np.pi, 10, 0.3))
T7_T_NAMES = ("c", "A", "tau_prime_us", "Delta0_MHz", "phi0_rad", "gamma_per_us", "delta_MHz")
T7_T_GRID = ((0.015, 0.03, 0.05), (0.003, 0.03), ((0.0, 0.005, 0.003), (0.0, 0.005, 0.03)))
T7_SHIFT_DEG, T7_SHIFT_US = {"144": -28.4, "142": -8.7, "both": -40.5}, 10.444
T7_OFFSETS_MHZ = {k: v / (360.0 * T7_SHIFT_US) for k, v in T7_SHIFT_DEG.items()}
T7_4_NAMES = ("c", "A", "tau_us", "Delta_MHz", "phi0_rad", "w144", "w142", "wboth")
T7_4_BOUNDS = ((0, 0, 0.5, -0.3, 0, 0.0, 0.0, 0.0), (1, 1, 1e4, 0.3, 2 * np.pi, 1.0, 1.0, 1.0))
T7_RATES_PER_S = {
    "parity switching on IBM Falcon devices": [3, 5],
    "Riste et al.": [1300, 1300],
    "two-level-system fluctuators": [0.004, 0.5],
}


def _t7_g(t, gam, dl):
    """The telegraph factor e^{-gam t} [cosh(k t) + (gam / k) sinh(k t)], k = sqrt(gam^2 - (2 pi dl)^2) (test 7's T)."""
    t = np.asarray(t, float)
    k = np.sqrt(gam**2 - (2 * np.pi * dl) ** 2 + 0j)
    if abs(k) < 1e-9:
        return np.exp(-gam * t) * (1 + gam * t)
    return np.real(0.5 * ((1 + gam / k) * np.exp((k - gam) * t) + (1 - gam / k) * np.exp(-(k + gam) * t)))


def _t7_model_T(p, t, ph):
    c, A, tau, D, p0, gam, dl = p
    return c + A * np.exp(-t / tau) * _t7_g(t, gam, dl) * np.cos(2 * np.pi * D * t + p0 + ph)


def _t7_model_4(p, t, ph):
    c, A, tau, D, p0, w1, w2, w3 = p
    env = A * np.exp(-t / tau)
    s1, s2, s3 = T7_OFFSETS_MHZ["144"], T7_OFFSETS_MHZ["142"], T7_OFFSETS_MHZ["both"]
    return c + env * (
        (1 - w1 - w2 - w3) * np.cos(2 * np.pi * D * t + p0 + ph)
        + w1 * np.cos(2 * np.pi * (D + s1) * t + p0 + ph)
        + w2 * np.cos(2 * np.pi * (D + s2) * t + p0 + ph)
        + w3 * np.cos(2 * np.pi * (D + s3) * t + p0 + ph)
    )


def _t7_counts(rec: dict):
    """Per copy, quadrature and wait, the shots that read 1 and the shots; each quadrature's scheduled waits; the
    readout circuits' (ones, shots) per copy."""
    ones, n, t_us = np.zeros((2, 2, 64), int), np.zeros((2, 2, 64), int), np.full((2, 2, 64), np.nan)
    ro = {"P10": [None, None], "P01": [None, None]}
    for lab, cts, sh in zip(rec["labels"], rec["counts"], rec["shots"]):
        tot = sum(cts.values())
        assert tot == sh
        k1 = sum(v for key, v in cts.items() if key[-1] == "1")
        cp = lab["copy"] - 1
        if lab["circuit"] in ("X", "Y"):
            q, i = "XY".index(lab["circuit"]), int(lab["t_requested_us"])
            ones[cp, q, i], n[cp, q, i], t_us[cp, q, i] = k1, tot, float(lab["scheduled_wait_us"])
        else:
            ro[lab["circuit"]][cp] = (k1, tot)
    assert not np.isnan(t_us).any() and (t_us[0] == t_us[1]).all()
    return ones, n, t_us[0], ro


def _t7_best(model, starts, bounds, t, ph, y, sig, names):
    from scipy.optimize import least_squares

    best, sts = None, []
    for p in starts:
        try:
            r = least_squares(lambda q: (model(q, t, ph) - y) / sig, p, bounds=bounds, max_nfev=4000)
            sts.append(int(r.status))
        except (ValueError, FloatingPointError):
            sts.append("exception")
            continue
        if best is None or r.cost < best.cost:
            best = r
    chi2, k = float(2 * best.cost), len(best.x)
    fit = {
        "params": dict(zip(names, [float(v) for v in best.x])),
        "chi2": chi2,
        "n_points": len(y),
        "dof": len(y) - k,
        "chi2_per_dof": chi2 / (len(y) - k) if len(y) > k else None,
        "largest_abs_residual_sigma": float(np.max(np.abs(best.fun))),
        "n_starts": len(starts),
    }
    return fit, sts


def _t7_failed(sts) -> int:
    return sum(1 for s in sts if s == "exception" or (isinstance(s, int) and s <= 0))


def _t7_pct(a, q=(5, 95)):
    a = np.asarray(a, float)
    a = a[~np.isnan(a)]
    return [float(v) for v in np.percentile(a, q)] if len(a) else [None, None]


def _t7_band(D, dl, b):
    reach = abs(D) + dl
    return {
        "P_lines_kHz": [(D + dl) * 1e3, (D - dl) * 1e3],
        "P_reach_kHz": reach * 1e3,
        "P_outside_band": bool(reach > 0.25 + 1e-12),
        "P_presses_band": bool(reach >= 0.25 - 0.001),
        "P_b_at_edge": bool(b < 0.05 or b > 0.95),
    }


def _t7_published(rec: dict):
    """The stamp in force at the submission and every distinct stamp read from then to the fetch, with 143's
    published values, from the calibration record's reads."""
    rows = rec["calibration_record"]["stamps"]
    keep = (
        "stamp_utc",
        "q143_readout_error",
        "q143_prob_meas1_prep0",
        "q143_prob_meas0_prep1",
        "q143_T1_us",
        "q143_T2_us",
        "q142_prob_meas1_prep0",
        "q144_prob_meas1_prep0",
    )

    def pick(r):
        return {k: (r[k] if k == "stamp_utc" else (None if r[k] in ("", None) else float(r[k]))) for k in keep}

    sub = [r for r in rows if r["kind"].startswith("submission")]
    k0 = rows.index(sub[-1])
    during = []
    for r in rows[k0:]:
        if not during or during[-1]["stamp_utc"] != r["stamp_utc"]:
            during.append({**pick(r), "first_read_utc": r["utc"], "kind": r["kind"]})
    return {
        "rows": len(rows),
        "at_submission": {**pick(sub[-1]), "read_utc": sub[-1]["utc"]},
        "distinct_from_submission_to_fetch": during,
    }


def _t7_env_mean(env, se, tq, lo, hi):
    m = (tq >= lo - 1e-9) & (tq <= hi + 1e-9)
    k = int(m.sum())
    return [float(np.mean(env[m])), float(np.sqrt(np.sum(se[m] ** 2)) / k), k]


def _t7_envelope_tests(env, env_se, tX):
    """The windows and tests the rule's item 4 fixed: the means over 20 to 22, 31 to 33, 41 to 43 and 52 to 54 us, the
    three contrasts in standard errors, and the largest rise of the 5-wait running mean above its running minimum."""
    means = {
        k: _t7_env_mean(env, env_se, tX, a, b)
        for k, (a, b) in {"20_22": (20, 22), "31_33": (31, 33), "41_43": (41, 43), "52_54": (52, 54)}.items()
    }

    def z(a, b):
        return (a[0] - b[0]) / math.hypot(a[1], b[1])

    rev = {
        "20_22_over_31_33_in_se": z(means["20_22"], means["31_33"]),
        "41_43_over_31_33_in_se": z(means["41_43"], means["31_33"]),
        "41_43_over_52_54_in_se": z(means["41_43"], means["52_54"]),
    }
    rm = np.convolve(env, np.ones(5) / 5, mode="valid")
    rm_se = np.sqrt(np.convolve(env_se**2, np.ones(5), mode="valid")) / 5
    run_min, rise = np.inf, []
    for v, s_ in zip(rm, rm_se):
        run_min = min(run_min, v)
        rise.append((v - run_min) / s_)
    as_read = all(v > 3 for v in rev.values())
    reading = "revivals and nodes as read" if as_read else ("a monotone fall" if max(rise) <= 3 else "neither")
    return means, rev, float(max(rise)), reading


def t7_ramsey_xy(rec: dict, seeds: dict = T7_SEEDS) -> tuple[dict, dict]:
    """Test 7 (finding 28) from its counts: the rule's S and P fits, held-out errors, bootstrap and verdict by the
    package (`manacitra.wait.ramsey_xy_fit`, with the rule's thresholds passed in and the verdict's words written
    here); and, as analyse_t7.py fixed them before the data, the items beside the verdict: the telegraph model T and
    gamma, the weight, the beat nodes, the envelope's test, the detuning beside the archive, the periodograms of P's
    residuals and the four-tone sideband check, the readout, the scheduled waits and the published values. T and the
    four-tone model are refitted on the bootstrap's own draws (the same generator; the refits draw nothing). Returns
    the analysis and the bootstrap record, in the shape the run archived them. seeds: the rule's, unless another stream
    is asked for (the movement study of the intervals)."""
    from scipy.optimize import least_squares
    from scipy.signal import lombscargle

    ones, n, tq, ro = _t7_counts(rec)
    nn = n.sum(0)
    yq = ones.sum(0) / nn
    se_q = np.sqrt(yq * (1 - yq) / nn)
    E, O = np.arange(0, 64, 2), np.arange(1, 64, 2)
    s = seeds
    fit = wait.ramsey_xy_fit(
        tq, ones, n, E, seeds=(s["S_starts"], s["P_random_starts"], s["bootstrap"]), n_boot=2000, **T7_RULE
    )
    fS, fP = fit["S"], fit["P"]

    def stack2(a, idx):
        return np.concatenate([a[0][idx], a[1][idx]])

    ph_all = np.array([0.0, -np.pi / 2])[:, None] * np.ones((2, 64))
    te, phe, ye, ne = stack2(tq, E), stack2(ph_all, E), stack2(yq, E), stack2(nn, E)
    to, pho, yo = stack2(tq, O), stack2(ph_all, O), stack2(yq, O)
    se = np.sqrt(np.clip(ye * (1 - ye), 1 / ne, None) / ne)
    xS, xP = list(fS["params"].values()), list(fP["params"].values())

    def full(f, model, x):
        res = (model(x, te, phe) - ye) / se
        return {
            "params": f["params"],
            "chi2": f["chi2"],
            "n_points": f["n_points"],
            "dof": f["dof"],
            "chi2_per_dof": f["chi2"] / f["dof"],
            **({"largest_abs_residual_sigma": float(np.max(np.abs(res)))} if model is wait._ramsey_s else {}),
            "n_starts": f["starts"],
        }

    fs, fp = full(fS, wait._ramsey_s, xS), full(fP, wait._ramsey_p, xP)
    mae_s, mae_p = fS["held_out_error"], fP["held_out_error"]

    # beside: T and the four-tone fit on the same fit set
    sp = fS["params"]
    D = sp["Delta_MHz"]
    gd, gg, gx = T7_T_GRID
    t_starts = [
        [sp["c"], sp["A"], sp["tau_us"], D + k * d, sp["phi0_rad"], g, d] for d in gd for k in (0, 1, -1) for g in gg
    ]
    t_starts += [[sp["c"], sp["A"], sp["tau_us"], D + sh, sp["phi0_rad"], g, d] for sh, d, g in gx]
    lo, hi = (np.array(b, float) for b in T7_T_BOUNDS)
    t_starts = [list(np.clip(x, lo, hi)) for x in t_starts]
    rng_t = np.random.default_rng(s["T_random_starts"])
    t_starts += [list(lo + (hi - lo) * rng_t.random(len(lo))) for _ in range(20)]
    ft, st_t = _t7_best(_t7_model_T, t_starts, T7_T_BOUNDS, te, phe, ye, se, T7_T_NAMES)
    mae_t = float(np.mean(np.abs(_t7_model_T(list(ft["params"].values()), to, pho) - yo)))
    starts4 = [
        [sp["c"], sp["A"], sp["tau_us"], D, sp["phi0_rad"], a, b, a * b] for a in (0, 0.05, 0.2) for b in (0, 0.05, 0.2)
    ]
    f4, st_4 = _t7_best(_t7_model_4, starts4, T7_4_BOUNDS, te, phe, ye, se, T7_4_NAMES)
    f4 = {k: f4[k] for k in ("params", "chi2", "n_points", "dof", "n_starts")}
    f4["offsets_kHz"] = {k: v * 1e3 for k, v in T7_OFFSETS_MHZ.items()}
    mae_4 = float(np.mean(np.abs(_t7_model_4(list(f4["params"].values()), to, pho) - yo)))

    # the bootstrap's draws again (the generator as the package draws it), with P, T and the four-tone model refitted
    rng = np.random.default_rng(s["bootstrap"])
    ones_e, n_e, shots = ones[:, :, E], nn[:, E], int(n[0, 0, 0])
    xT, x4 = list(ft["params"].values()), list(f4["params"].values())
    draws = {"P": np.full((2000, 7), np.nan), "T": np.full((2000, 7), np.nan), "four_tone": np.full((2000, 8), np.nan)}
    st_r = {"P": [], "T": [], "four_tone": []}
    p_bounds = (np.array([0, 0, 0.5, -0.125, 0, 0.0, 0.0]), np.array([1, 1, 1e4, 0.125, 2 * np.pi, 0.125, 1.0]))
    for k in range(2000):
        pick = rng.integers(0, 2, size=ones_e.shape)
        src = np.take_along_axis(ones_e, pick, axis=0) / shots
        yb = rng.binomial(shots, src).sum(0) / n_e
        yb = np.concatenate([yb[0], yb[1]])
        sb = np.sqrt(np.clip(yb * (1 - yb), 1 / ne, None) / ne)
        for name, model, x0, bounds in (
            ("P", wait._ramsey_p, xP, p_bounds),
            ("T", _t7_model_T, xT, T7_T_BOUNDS),
            ("four_tone", _t7_model_4, x4, T7_4_BOUNDS),
        ):
            try:
                r = least_squares(
                    lambda q, m=model, yb=yb, sb=sb: (m(q, te, phe) - yb) / sb, x0, bounds=bounds, max_nfev=4000
                )
                st_r[name].append(int(r.status))
                draws[name][k] = r.x
            except (ValueError, FloatingPointError):
                st_r[name].append("exception")
    pct = fit["bootstrap"]["percentiles_5_50_95"]
    d_lo, d_hi = pct["delta_MHz"][0], pct["delta_MHz"][2]
    b_lo, b_hi = pct["b"][0], pct["b"][2]
    assert [d_lo, d_hi] == _t7_pct(draws["P"][:, 5]) and [b_lo, b_hi] == _t7_pct(draws["P"][:, 6])
    cl = fit["clauses"]
    if cl["S_within_the_margin_of_P_or_below"] and (
        cl["delta_lower_bound_below_the_floor"] or cl["b_interval_reaches_an_edge"]
    ):
        verdict = "NO RESOLVED SPLIT"
    elif (
        cl["P_below_S_by_more_than_the_margin"]
        and cl["delta_lower_bound_above_the_floor"]
        and cl["b_interval_inside_the_edges"]
    ):
        verdict = "TWO FIXED FREQUENCIES"
    else:
        verdict = "NOT SETTLED"
    clauses = {
        "S_within_0.01_of_P_or_smaller": cl["S_within_the_margin_of_P_or_below"],
        "P_smaller_than_S_by_more_than_0.01": cl["P_below_S_by_more_than_the_margin"],
        "delta_lower_bound_below_5_kHz": cl["delta_lower_bound_below_the_floor"],
        "delta_lower_bound_above_5_kHz": cl["delta_lower_bound_above_the_floor"],
        "b_interval_reaches_an_edge": cl["b_interval_reaches_an_edge"],
        "b_interval_inside_0.05_0.95": cl["b_interval_inside_the_edges"],
    }

    # beside 1: T
    g_lo, g_hi = _t7_pct(draws["T"][:, 5])
    gp = ft["params"]["gamma_per_us"]
    t_lines = _t7_band(ft["params"]["Delta0_MHz"], ft["params"]["delta_MHz"], 0.5)
    t_lines.pop("P_b_at_edge")
    beside_T = {
        "fit": ft,
        "held_out_error": mae_t,
        "gamma_per_us": gp,
        "gamma_ci90_per_us": [g_lo, g_hi],
        "gamma_per_s": gp * 1e6,
        "gamma_ci90_per_s": [None if v is None else v * 1e6 for v in (g_lo, g_hi)],
        "delta_T_kHz": ft["params"]["delta_MHz"] * 1e3,
        "delta_T_ci90_kHz": [None if v is None else v * 1e3 for v in _t7_pct(draws["T"][:, 6])],
        "lines_against_the_band": {k.replace("P_", "T_"): v for k, v in t_lines.items()},
        "published_rates_per_s": T7_RATES_PER_S,
        "starts_failed": _t7_failed(st_t),
        "starts_run": len(st_t),
        "refits_failed": _t7_failed(st_r["T"]),
        "note": "a diagnostic: no verdict reads gamma",
    }

    # beside 3 and 4: the envelope, the nodes, the span
    c_s = sp["c"]
    zx, zy = yq[0] - c_s, yq[1] - c_s
    env = np.sqrt(zx**2 + zy**2)
    env_se = np.sqrt((zx * se_q[0]) ** 2 + (zy * se_q[1]) ** 2) / np.where(env > 0, env, np.nan)
    tX = tq[0]
    dl_p = fp["params"]["delta_MHz"]
    nodes = []
    for m in (1, 3, 5):
        tn = m / (4 * dl_p)
        i = int(np.argmin(np.abs(tX - tn)))
        nodes.append(
            {
                "k": m,
                "t_us": tn,
                "in_span": bool(tn <= tX.max()),
                "nearest_wait_us": float(tX[i]),
                "X_P1": float(yq[0][i]),
                "X_se": float(se_q[0][i]),
                "Y_P1": float(yq[1][i]),
                "Y_se": float(se_q[1][i]),
                "envelope": float(env[i]),
                "envelope_se": float(env_se[i]),
            }
        )
    t_max = float(max(tq[0].max(), tq[1].max()))
    m4, rev, rise, reading4 = _t7_envelope_tests(env, env_se, tX)

    # beside 6: the periodograms of P's residuals, and the sideband check
    predq = np.stack([wait._ramsey_p(xP, tq[0], 0.0), wait._ramsey_p(xP, tq[1], -np.pi / 2)])
    res = yq - predq
    f_khz = np.arange(2.0, 500.0 + 1e-9, 0.5)
    w = 2 * np.pi * f_khz * 1e-3

    def ls(tt, r):
        return lombscargle(tt, r - r.mean(), w)

    fz = np.concatenate([-f_khz[::-1], f_khz]) * 1e-3
    Ez = [np.exp(-2j * np.pi * np.outer(fz, tq[0])), np.exp(-2j * np.pi * np.outer(fz, tq[1]))]

    def cz(rx, ry):
        return np.abs(Ez[0] @ rx + 1j * (Ez[1] @ ry)) ** 2 / len(rx)

    pls, pcz = [ls(tq[0], res[0]), ls(tq[1], res[1])], cz(res[0], res[1])
    rng_n = np.random.default_rng(s["periodogram_noise"])
    mx = {"X": [], "Y": [], "complex": []}
    pc = np.clip(predq, 0, 1)
    for _ in range(T7_N_NOISE):
        rn = rng_n.binomial(nn, pc) / nn - pc
        mx["X"].append(ls(tq[0], rn[0]).max())
        mx["Y"].append(ls(tq[1], rn[1]).max())
        mx["complex"].append(cz(rn[0], rn[1]).max())
    floors = {k: float(np.percentile(v, 95)) for k, v in mx.items()}

    def peaks(p, f, floor):
        out = [
            {"f_kHz": float(f[i]), "height": float(p[i]), "over_floor": float(p[i] / floor)}
            for i in range(len(p))
            if p[i] > floor and (i == 0 or p[i] >= p[i - 1]) and (i == len(p) - 1 or p[i] >= p[i + 1])
        ]
        return sorted(out, key=lambda d: -d["height"])

    pk = {
        "X": peaks(pls[0], f_khz, floors["X"]),
        "Y": peaks(pls[1], f_khz, floors["Y"]),
        "complex": peaks(pcz, fz * 1e3, floors["complex"]),
    }
    top = {
        "X": {"f_kHz": float(f_khz[np.argmax(pls[0])]), "height": float(pls[0].max())},
        "Y": {"f_kHz": float(f_khz[np.argmax(pls[1])]), "height": float(pls[1].max())},
        "complex": {"f_kHz": float(fz[np.argmax(pcz)] * 1e3), "height": float(pcz.max())},
    }
    wts = {k: f4["params"][k] for k in ("w144", "w142", "wboth")}
    w_ci = {k: _t7_pct(draws["four_tone"][:, 5 + j]) for j, k in enumerate(("w144", "w142", "wboth"))}
    resolved = [k for k in wts if w_ci[k][0] is not None and w_ci[k][0] > 0.01]
    side = (
        "NO SIDEBAND RESOLVED"
        if not resolved
        else (
            "SIDEBANDS AT THE NEIGHBOUR SHIFTS"
            if all(wts[k] <= 0.10 for k in resolved)
            else "WEIGHTS ABOVE A FEW PER CENT"
        )
    )

    # beside 7: readout
    def rate(pair, one_is_error):
        per = []
        for k1, tot in pair:
            p = k1 / tot if one_is_error else 1 - k1 / tot
            per.append({"p": p, "se": math.sqrt(p * (1 - p) / tot), "shots": tot})
        k1s, tots = sum(k for k, _ in pair), sum(t_ for _, t_ in pair)
        p = k1s / tots if one_is_error else 1 - k1s / tots
        return {"pooled": p, "pooled_se": math.sqrt(p * (1 - p) / tots), "per_copy": per}

    p10, p01 = rate(ro["P10"], True), rate(ro["P01"], False)
    pub = _t7_published(rec)
    sub_pub = pub["at_submission"]
    readout = {
        "P(1|0)": p10,
        "P(0|1)": p01,
        "e": (p10["pooled"] + p01["pooled"]) / 2,
        "e_se": 0.5 * math.hypot(p10["pooled_se"], p01["pooled_se"]),
        "published_at_submission": {
            k: sub_pub.get(k)
            for k in ("stamp_utc", "q143_readout_error", "q143_prob_meas1_prep0", "q143_prob_meas0_prep1")
        },
    }
    per_wait = [
        {
            "t_requested_us": i,
            "t_scheduled_us": {"X": float(tq[0][i]), "Y": float(tq[1][i])},
            "set": "fit" if i % 2 == 0 else "held out",
            "X": {
                "P1": float(yq[0][i]),
                "se": float(se_q[0][i]),
                "copies": [int(ones[0, 0, i]), int(ones[1, 0, i])],
                "shots": int(nn[0][i]),
            },
            "Y": {
                "P1": float(yq[1][i]),
                "se": float(se_q[1][i]),
                "copies": [int(ones[0, 1, i]), int(ones[1, 1, i])],
                "shots": int(nn[1][i]),
            },
            "envelope": float(env[i]),
            "envelope_se": float(env_se[i]),
            "residual_P": {"X": float(res[0][i]), "Y": float(res[1][i])},
        }
        for i in range(64)
    ]
    scheduled = [
        {
            "t_requested_us": i,
            "scheduled_us": {"X": float(tq[0][i]), "Y": float(tq[1][i])},
            "difference_us": {"X": float(tq[0][i] - i), "Y": float(tq[1][i] - i)},
        }
        for i in range(64)
    ]
    analysis = {
        "verdict": verdict,
        "deciding": {
            "held_out_error_S": mae_s,
            "held_out_error_P": mae_p,
            "P_minus_S": mae_p - mae_s,
            "delta_ci90_kHz": [d_lo * 1e3, d_hi * 1e3],
            "b_ci90": [b_lo, b_hi],
            "clauses": clauses,
            "bootstrap_refits_returned": fit["bootstrap"]["returned"],
            "bootstrap_refits_failed_to_converge": fit["bootstrap"]["refits_failed"],
        },
        "fits": {
            "S": fs,
            "P": fp,
            "P_lines": _t7_band(fp["params"]["Delta0_MHz"], dl_p, fp["params"]["b"]),
            "starts": {
                "S": {"run": fS["starts"], "failed_to_converge": fS["starts_failed"]},
                "P": {"run": fP["starts"], "failed_to_converge": fP["starts_failed"]},
            },
        },
        "beside": {
            "1_telegraph_T": beside_T,
            "2_weight": {
                "b": fp["params"]["b"],
                "b_ci90": [b_lo, b_hi],
                "equal_weight": 0.5,
                "shirizly_exception": 0.368,
                "ci_contains_0.5": b_lo <= 0.5 <= b_hi,
                "ci_contains_0.368": b_lo <= 0.368 <= b_hi,
            },
            "3_beat_nodes": {
                "delta_P_kHz": dl_p * 1e3,
                "nodes": nodes,
                "wait_test_wait_us": T7_WAIT_TEST_WAIT_US,
                "t_max_us": t_max,
                "split_with_first_node_at_the_span_end_kHz": 1e3 / (4 * t_max),
                "delta_ci90_upper_kHz": d_hi * 1e3,
                "decay_absorbed_per_us": 1 / fs["params"]["tau_us"] - 1 / fp["params"]["tau_prime_us"],
                "tau_S_us": fs["params"]["tau_us"],
                "tau_prime_P_us": fp["params"]["tau_prime_us"],
            },
            "4_reading_23p7_kHz": {
                "means": m4,
                "contrasts_in_se": rev,
                "running_mean_max_rise_in_se": rise,
                "reading": reading4,
                "note": "a reading recorded before the data; the verdict does not depend on it",
            },
            "5_detuning_and_T2": {
                "S_Delta_kHz": sp["Delta_MHz"] * 1e3,
                "S_abs_Delta_kHz": abs(sp["Delta_MHz"]) * 1e3,
                "P_Delta0_kHz": fp["params"]["Delta0_MHz"] * 1e3,
                "P_lines_kHz": _t7_band(fp["params"]["Delta0_MHz"], dl_p, fp["params"]["b"])["P_lines_kHz"],
                "archive_kHz": {"2026-10-11": [47.1, 1.8], "2026-10-13": [40.4, 3.2]},
                "archive_note": "sizes, fitted on the X quadrature alone",
                "tau_S_us": fs["params"]["tau_us"],
                "tau_prime_P_us": fp["params"]["tau_prime_us"],
                "published_at_submission": {k: sub_pub.get(k) for k in ("stamp_utc", "q143_T1_us", "q143_T2_us")},
            },
            "6_more_than_two": {
                "periodogram": {
                    "f_kHz": [2.0, 500.0, 0.5],
                    "floors_95": floors,
                    "peaks_above_floor": pk,
                    "largest": top,
                    "reading": "MORE THAN TWO" if any(pk.values()) else "no peak above the floor",
                    "resolution_kHz": 1e3 / t_max,
                },
                "sideband_check": {
                    "fit": f4,
                    "held_out_error": mae_4,
                    "weights": wts,
                    "weights_ci90": w_ci,
                    "resolved": resolved,
                    "reading": side,
                    "published_neighbour_prob_meas1_prep0_at_submission": {
                        k: sub_pub.get(k) for k in ("q142_prob_meas1_prep0", "q144_prob_meas1_prep0")
                    },
                    "published_note": "IBM publishes no excited-state population; prob_meas1_prep0 is a readout "
                    "figure, given as the nearest published quantity",
                    "starts_failed": _t7_failed(st_4),
                    "refits_failed": _t7_failed(st_r["four_tone"]),
                },
                "note": "neighbour sidebands sit on one side at a few per cent; a parity split is two-sided at "
                "near-equal weights",
            },
            "7_readout": readout,
            "8_scheduled_waits": {
                "all_equal_to_requested": all(abs(x["difference_us"][q]) < 1e-9 for x in scheduled for q in ("X", "Y")),
                "largest_abs_difference_us": max(abs(x["difference_us"][q]) for x in scheduled for q in ("X", "Y")),
                "waits": scheduled,
            },
            "9_published_from_submission_to_fetch": pub,
        },
        "per_wait": per_wait,
    }
    boot = {
        "meta": {
            "seed": s["bootstrap"],
            "n_boot": 2000,
            "names": {"P": list(wait.RAMSEY_XY_NAMES["P"]), "T": list(T7_T_NAMES), "four_tone": list(T7_4_NAMES)},
            "point_fits": {"P": xP, "T": xT, "four_tone": x4},
            "status_failed": {k: _t7_failed(v) for k, v in st_r.items()},
        },
        "draws": {k: [[None if np.isnan(x) else float(x) for x in row] for row in v] for k, v in draws.items()},
    }
    return analysis, boot


def t7_readings(rec: dict, analysis: dict, seeds: dict = T7_SEEDS) -> dict:
    """Test 7's readings after the data (reading_t7.py; not in the rule, and the verdict reads none of them): A, the
    copies' agreement (`manacitra.wait.copies_check`); B, the upper line's weight each Ramsey position implies, in
    execution order, P's other parameters held at the point fit; C, P refitted on each half of the run; D, the
    envelope centred on P's c, with item 4's windows and tests."""
    from scipy.stats import chi2

    P = analysis["fits"]["P"]["params"]
    cP, A, tau, D0, p0, dl = (P[k] for k in ("c", "A", "tau_prime_us", "Delta0_MHz", "phi0_rad", "delta_MHz"))
    labs, cts, shots = rec["labels"], rec["counts"], rec["shots"]
    agree, rows_a = {}, []
    for group, keep in (("ramsey", ("X", "Y")), ("readout", ("P10", "P01"))):
        idx = [k for k, lab in enumerate(labs) if lab["circuit"] in keep]
        chk = wait.copies_check([labs[k] for k in idx], [cts[k] for k in idx])
        z = [c["z"] for c in chk["circuits"]]
        agree[group] = {
            "n": chk["dof"],
            "sum_z2": chk["sum_z2"],
            "per_dof": chk["per_dof"],
            "p_value": float(chi2.sf(chk["sum_z2"], chk["dof"])),
            "n_abs_z_over_3": int(sum(abs(x) > 3 for x in z)),
            "largest_abs_z": float(max(abs(x) for x in z)),
        }
        for c in chk["circuits"]:
            rows_a.append(
                {
                    "circuit": c["label"]["circuit"],
                    "t_requested_us": c["label"]["t_requested_us"],
                    "copy1": c["P1"][0],
                    "copy2": c["P1"][1],
                    "z": c["z"],
                    "positions": [idx[c["positions"][0]], idx[c["positions"][1]]],
                }
            )
    rows_a.sort(key=lambda r: (r["circuit"], -1 if r["t_requested_us"] is None else r["t_requested_us"]))

    pos = [
        {
            "k": k,
            "circuit": lab["circuit"],
            "t": lab.get("scheduled_wait_us"),
            "ones": sum(v for key, v in ct.items() if key[-1] == "1"),
            "n": n,
        }
        for k, (lab, ct, n) in enumerate(zip(labs, cts, shots))
    ]
    rows = []
    for p in pos:
        if p["circuit"] not in ("X", "Y"):
            continue
        ph = 0.0 if p["circuit"] == "X" else -math.pi / 2
        t, n = p["t"], p["n"]
        y = p["ones"] / n
        e = A * math.exp(-t / tau)
        a1 = math.cos(2 * math.pi * (D0 + dl) * t + p0 + ph)
        a2 = math.cos(2 * math.pi * (D0 - dl) * t + p0 + ph)
        lev = e * (a1 - a2)
        if abs(lev) < 0.35:
            continue
        rows.append(
            {
                "k": p["k"],
                "circuit": p["circuit"],
                "t_us": t,
                "b_pos": (y - cP - e * a2) / lev,
                "se": math.sqrt(max(y * (1 - y), 1 / n) / n) / abs(lev),
            }
        )
    bpos, bse = np.array([r["b_pos"] for r in rows]), np.array([r["se"] for r in rows])
    ks = np.array([r["k"] for r in rows])
    blocks = []
    for j in range(10):
        m = (ks >= 26 * j) & (ks < 26 * (j + 1))
        if m.any():
            w = 1 / bse[m] ** 2
            blocks.append(
                {
                    "positions": [26 * j, 26 * (j + 1) - 1],
                    "n": int(m.sum()),
                    "weighted_mean": float(np.sum(w * bpos[m]) / np.sum(w)),
                    "se": float(1 / math.sqrt(np.sum(w))),
                    "spread_sd": float(np.std(bpos[m])),
                }
            )
    w = 1 / bse**2
    mu_all = float(np.sum(w * bpos) / np.sum(w))
    order = {
        "n_positions": len(rows),
        "lever_min": 0.35,
        "weighted_mean": mu_all,
        "chi2_per_dof_against_one_weight": float(np.mean(((bpos - mu_all) / bse) ** 2)),
        "lag1_autocorrelation": float(np.corrcoef(bpos[:-1], bpos[1:])[0, 1]),
        "blocks_of_26": blocks,
        "positions": rows,
    }

    halves = {}
    for name, lo, hi in (("first half (positions 0 to 129)", 0, 130), ("second half (positions 130 to 259)", 130, 260)):
        sel = [p for p in pos if lo <= p["k"] < hi and p["circuit"] in ("X", "Y")]
        t = np.array([p["t"] for p in sel])
        ph = np.array([0.0 if p["circuit"] == "X" else -math.pi / 2 for p in sel])
        n = np.array([p["n"] for p in sel], float)
        y = np.array([p["ones"] for p in sel]) / n
        hv = _t7_fit_points(t, ph, y, n, seeds)
        q = hv["P"]["params"]
        halves[name] = {
            "n_points": len(sel),
            "S": {
                "chi2": hv["S"]["chi2"],
                "dof": hv["S"]["dof"],
                "Delta_kHz": hv["S"]["params"]["Delta_MHz"] * 1e3,
                "c": hv["S"]["params"]["c"],
            },
            "P": {
                "chi2": hv["P"]["chi2"],
                "dof": hv["P"]["dof"],
                "lines_kHz": [(q["Delta0_MHz"] + q["delta_MHz"]) * 1e3, (q["Delta0_MHz"] - q["delta_MHz"]) * 1e3],
                "b": q["b"],
                "delta_kHz": q["delta_MHz"] * 1e3,
                "Delta0_kHz": q["Delta0_MHz"] * 1e3,
                "tau_prime_us": q["tau_prime_us"],
                "c": q["c"],
                "A": q["A"],
            },
        }

    pw = analysis["per_wait"]
    tX = np.array([r["t_scheduled_us"]["X"] for r in pw])
    yx, yy = np.array([r["X"]["P1"] for r in pw]), np.array([r["Y"]["P1"] for r in pw])
    sx, sy = np.array([r["X"]["se"] for r in pw]), np.array([r["Y"]["se"] for r in pw])
    zx, zy = yx - cP, yy - cP
    env = np.sqrt(zx**2 + zy**2)
    env_se = np.sqrt((zx * sx) ** 2 + (zy * sy) ** 2) / env
    means, rev, rise, reading = _t7_envelope_tests(env, env_se, tX)
    envelope = {
        "centre": cP,
        "centre_note": "P's c; the rule-fixed item 4 used S's c",
        "means": means,
        "contrasts_in_se": rev,
        "running_mean_max_rise_in_se": rise,
        "reading": reading,
        "local_minima_us": [float(tX[i]) for i in range(1, 63) if env[i] < env[i - 1] and env[i] < env[i + 1]],
        "local_maxima_us": [float(tX[i]) for i in range(1, 63) if env[i] > env[i - 1] and env[i] > env[i + 1]],
        "values": [float(v) for v in env],
        "P_nodes_us": [k / (4 * dl) for k in (1, 3, 5, 7, 9, 11)],
        "P_revivals_us": [k / (2 * dl) for k in (1, 2, 3, 4, 5)],
    }
    return {
        "note": "readings after the data; not in t7-rule.md; the verdict does not read them",
        "A_copy_agreement": {**agree, "circuits": rows_a},
        "B_weight_in_execution_order": order,
        "C_P_on_each_half_of_the_run": halves,
        "D_envelope_recentred_on_P_c": envelope,
        "job_running_utc": rec["timestamps"],
    }


def _t7_fit_points(t, ph, y, n, seeds: dict = T7_SEEDS) -> dict:
    """S and P fitted to single positions (each its own point, as reading C fits each half of the run), with the
    package's models, bounds and start layouts and the rule's seeds, every point fitted. The package's ramsey_xy_fit
    pools copies on a grid of waits, which a half of the run is not."""
    from scipy.optimize import least_squares

    sig = np.sqrt(np.clip(y * (1 - y), 1 / n, None) / n)
    s_lo, s_hi = (np.array(b, float) for b in wait.RAMSEY_XY_S_BOUNDS)
    rng_s, rng_p = np.random.default_rng(seeds["S_starts"]), np.random.default_rng(seeds["P_random_starts"])

    def uniform(lo, hi, k, rng):
        return [list(lo + (hi - lo) * rng.random(len(lo))) for _ in range(k)]

    def best(model, starts, bounds, names):
        b = None
        for p in starts:
            try:
                r = least_squares(lambda q: (model(q, t, ph) - y) / sig, p, bounds=bounds, max_nfev=4000)
            except (ValueError, FloatingPointError):
                continue
            if b is None or r.cost < b.cost:
                b = r
        return {
            "params": dict(zip(names, (float(v) for v in b.x))),
            "chi2": float(2 * b.cost),
            "dof": len(y) - len(b.x),
        }

    S = best(wait._ramsey_s, uniform(s_lo, s_hi, 40, rng_s), (s_lo, s_hi), wait.RAMSEY_XY_NAMES["S"])
    sp = S["params"]
    p_lo = np.array([0, 0, 0.5, -0.125, 0, 0.0, 0.0])
    p_hi = np.array([1, 1, 1e4, 0.125, 2 * np.pi, 0.125, 1.0])
    grid = [
        [sp["c"], sp["A"], sp["tau_us"], sp["Delta_MHz"] + k * d, sp["phi0_rad"], d, bb]
        for d in wait.RAMSEY_XY_P_GRID_DELTA_MHZ
        for k in (0, 1, -1)
        for bb in wait.RAMSEY_XY_P_GRID_B
    ]
    grid += [
        [sp["c"], sp["A"], sp["tau_us"], sp["Delta_MHz"], sp["phi0_rad"], d, bb]
        for d, bb in wait.RAMSEY_XY_P_GRID_EXTRA
    ]
    starts = [list(np.clip(x, p_lo, p_hi)) for x in grid] + uniform(p_lo, p_hi, 20, rng_p)
    P = best(wait._ramsey_p, starts, (p_lo, p_hi), wait.RAMSEY_XY_NAMES["P"])
    return {"S": S, "P": P}


# --------------------------------------------------------------------------- test 7's execution spans (Amendment A26)
def t7_spans(spans: dict, shots: int = 1500) -> dict:
    """The quantities test 7's span record derives from the provider's own fields (each span's start and stop, read as
    UTC, and the positions and shots it ran): each span's duration and runs of positions, the gaps between spans in
    start order, and whether every position ran in exactly one span with all its shots (test 7's 1,500 unless the
    caller names a job's own, A27)."""
    from datetime import datetime

    def t(s):
        return datetime.fromisoformat(s)

    rows = spans["spans"]
    order = sorted(range(len(rows)), key=lambda i: rows[i]["start_utc"])
    cover: dict = {}
    for r in rows:
        for p in r["positions"]:
            cover.setdefault(p, []).append((r["span"], r["shots_per_position"][str(p)]))
    return {
        "n_spans": len(rows),
        "spans": [
            {
                "duration_s": (t(r["stop_utc"]) - t(r["start_utc"])).total_seconds(),
                "size_shots": sum(r["shots_per_position"].values()),
                "n_positions": len(r["positions"]),
                "position_runs": _runs(r["positions"]),
            }
            for r in rows
        ],
        "spans_in_start_order": order,
        "gaps": [
            {
                "after_span": a,
                "before_span": b,
                "gap_s": (t(rows[b]["start_utc"]) - t(rows[a]["stop_utc"])).total_seconds(),
            }
            for a, b in zip(order, order[1:])
        ],
        "every_position_in_exactly_one_span_with_all_its_shots": all(
            len(c) == 1 and c[0][1] == shots for c in cover.values()
        )
        and sorted(cover) == list(range(spans["n_positions"])),
        "positions_in_more_than_one_span": sorted(p for p, c in cover.items() if len(c) > 1),
        "positions_in_no_span": sorted(set(range(spans["n_positions"])) - set(cover)),
    }


def _runs(idx) -> list:
    out: list = []
    for i in sorted(idx):
        if out and i == out[-1][1] + 1:
            out[-1][1] = i
        else:
            out.append([i, i])
    return out


def t7_span_readings(rec: dict, spans: dict) -> dict:
    """Test 7's readings against its execution spans (A26; readings after the data, not in the rule): the upper line's
    weight per span, by the method of the ten blocks (each Ramsey position's implied weight, P held at its archived fit,
    where the lever is at least 0.35, averaged with inverse-variance weights); the blocks that hold the span boundaries;
    the nearest three positions passing the lever on either side of each boundary; and the copies check split by
    whether a circuit's two copies ran in the same span or in different ones (`manacitra.wait.copies_check`)."""
    span_of = {p: r["span"] for r in spans["spans"] for p in r["positions"]}
    pos = rec["archived"]["readings_after_the_data"]["B_weight_in_execution_order"]["positions"]
    per_span = []
    for r in spans["spans"]:
        rows = [x for x in pos if span_of[x["k"]] == r["span"]]
        b, se = np.array([x["b_pos"] for x in rows]), np.array([x["se"] for x in rows])
        w = 1 / se**2
        mu = float(np.sum(w * b) / np.sum(w))
        per_span.append(
            {
                "span": r["span"],
                "positions": [min(r["positions"]), max(r["positions"])],
                "n_positions_passing_the_lever": len(rows),
                "weighted_mean": mu,
                "se": float(1 / math.sqrt(np.sum(w))),
                "spread_sd": float(np.std(b)),
                "chi2_per_dof_against_one_weight": float(np.mean(((b - mu) / se) ** 2)),
            }
        )
    starts = sorted(min(r["positions"]) for r in spans["spans"])[1:]
    bounds = {}
    for name, first in zip(("first", "second"), starts):
        j = first // 26
        bounds[name] = {
            "between_positions": [first - 1, first],
            "block": j + 1,
            "block_positions": [26 * j, 26 * (j + 1) - 1],
            "before": [{"position": x["k"], "weight": x["b_pos"]} for x in pos if x["k"] < first][-3:],
            "after": [{"position": x["k"], "weight": x["b_pos"]} for x in pos if x["k"] >= first][:3],
        }
    labs, cts = rec["labels"], rec["counts"]
    idx = [k for k, lab in enumerate(labs) if lab["circuit"] in ("X", "Y")]
    chk = wait.copies_check([labs[k] for k in idx], [cts[k] for k in idx])
    rows = []
    for c in chk["circuits"]:
        ks = [idx[c["positions"][0]], idx[c["positions"][1]]]
        sp = [span_of[k] for k in ks]
        rows.append(
            {
                "circuit": c["label"]["circuit"],
                "t_requested_us": c["label"]["t_requested_us"],
                "positions": ks,
                "spans": sp,
                "same_span": sp[0] == sp[1],
                "z": c["z"],
            }
        )
    rows.sort(key=lambda r: (r["circuit"], r["t_requested_us"]))
    split = {}
    for name, keep in (("same_span", True), ("cross_span", False)):
        z = [r["z"] for r in rows if r["same_span"] is keep]
        s = float(np.sum(np.square(z)))
        split[name] = {
            "n": len(z),
            "sum_z2": s,
            "per_dof": s / len(z),
            "n_abs_z_over_3": int(sum(abs(x) > 3 for x in z)),
        }
    return {
        "weight_per_span": per_span,
        "span_boundaries": bounds,
        "copies_by_span": {**split, "circuits": rows},
    }


# --------------------------------------------------------------------------- tests 8 to 11 (A27, finding 29)
#: Test 10's rule: the phase's floors and thresholds, the usable conditions, the verdict words
T10_RULE = {"s_floor": 0.02, "abs_min": 0.3, "n_se": 5.0, "level_se": 3.0}
T10_E_MAX, T10_R_MIN = 0.03, 0.08
T10_VERDICTS = ("QUIET", "SWITCHES AT BOUNDARIES ONLY", "SWITCHES WITHIN SPANS")
#: Test 11's rule: the monitor's wait, the weight's threshold, its words
T11_WAIT_US, T11_W_MIN = 5.6, 0.10
T11_WEIGHT_WORDS = {
    "QUIET": "WEIGHT QUIET",
    "SWITCHES AT BOUNDARIES ONLY": "WEIGHT SWITCHES AT BOUNDARIES ONLY",
    "SWITCHES WITHIN SPANS": "WEIGHT SWITCHES WITHIN SPANS",
}
#: Test 11's job 1 seeds (rulings-t11.md) and test 9's job 1 seeds and rule (its analysis record's meta)
T11_SEEDS = {
    "S_starts": 7302,
    "P_random_starts": 7303,
    "bootstrap": 11304,
    "T_random_starts": 7305,
    "periodogram_noise": 7306,
}
T9_SEEDS = {"S_random_starts": 9304, "P_random_starts": 9305, "bootstrap_root": 9306}
T9_RULE = {"margin": 0.01, "delta_floor_mhz": 0.005, "b_edges": (0.05, 0.95)}


def _gz(name: str) -> dict:
    """A gzip file of data/ beside a record (the counts of tests 8 to 10, their analysis records), as JSON."""
    import gzip
    import json

    return json.loads(gzip.decompress((ar.data_dir() / name).read_bytes()))


def _ones_per_qubit(rec: dict) -> np.ndarray:
    """Per position and per qubit of the job's set (classical bit k is the set's k-th qubit), the shots that read 1."""
    n = len(rec["qubits"])
    out = np.zeros((len(rec["counts"]), n), int)
    for pos, cts in enumerate(rec["counts"]):
        for key, c in cts.items():
            b = _bits(key)
            for j in range(n):
                if b[j] == "1":
                    out[pos, j] += c
    return out


def _span_record(execution_metadata: dict) -> list[dict]:
    return [
        {k: s[k] for k in ("span", "positions", "start_utc", "stop_utc", "duration_s")}
        for s in execution_metadata["execution_spans"]
    ]


def _verdict(usable: bool, n_within: int, n_boundary: int) -> str:
    if not usable:
        return "NOT USABLE"
    if n_within >= 1:
        return "SWITCHES WITHIN SPANS"
    return "SWITCHES AT BOUNDARIES ONLY" if n_boundary >= 1 else "QUIET"


def _pooled(vs) -> str:
    vs = [v for v in vs if v and v != "NOT USABLE"]
    if not vs:
        return "NOT USABLE"
    for word in ("SWITCHES WITHIN SPANS", "SWITCHES AT BOUNDARIES ONLY"):
        if word in vs:
            return word
    return "QUIET"


def t10_monitor(rec: dict) -> dict:
    """Test 10 (finding 29): every qubit's phase per repeat, its switches within spans and at boundaries, its levels and
    slopes, and its verdict, per job, from the counts and the provider's span record, by the package's monitor_phase
    with the rule's thresholds; the counts of verdicts and the verdicts pooled over jobs 1 and 2."""
    survey = rec["archived"]["survey"]["qubits"]
    keep = (
        "c",
        "wait_us",
        "kHz_per_rad",
        "n_within",
        "n_boundary",
        "n_spans_not_consecutive_switches",
        "within_time_s",
        "within_rate_per_s",
        "within_rate_ci90_per_s",
        "straddling_repeats",
        "pi_sized_differences",
        "levels",
        "n_levels",
        "slopes",
        "repeat_period_s",
        "repeats_per_span",
        "job_mean_phase",
    )
    per_job, counts = {}, {}
    for j in ("1", "2", "3"):
        c = _gz(f"ibm_kingston/{rec['jobs'][j]['counts_file']['file']}")
        ones, spans = _ones_per_qubit(c), _span_record(c["execution_metadata"])
        out = {}
        for k, q in enumerate(c["qubits"]):
            wait_us = float(c["waits"]["X"][str(q)]["requested_us"])
            r = wait.monitor_phase(ones[:, k], c["labels"], spans, wait_us, shots=c["shots"][0], **T10_RULE)
            e0 = survey.get(str(q), {}).get("e")
            usable = (e0 is None or e0 <= T10_E_MAX) and r["median_r"] >= T10_R_MIN
            out[str(q)] = {
                "verdict": _verdict(usable, r["n_within"], r["n_boundary"]),
                "usable": usable,
                "usable_reasons": {"e_job0": e0, "median_r": r["median_r"]},
                **{x: r[x] for x in keep},
            }
        per_job[j] = out
        ok = [v for v in out.values() if v["usable"]]
        counts[j] = {w: sum(1 for v in ok if v["verdict"] == w) for w in T10_VERDICTS} | {
            "NOT USABLE": len(out) - len(ok)
        }
    pooled = {q: _pooled([per_job[j][q]["verdict"] for j in ("1", "2") if q in per_job[j]]) for q in per_job["1"]}
    pcount = {w: sum(1 for v in pooled.values() if v == w) for w in (*T10_VERDICTS, "NOT USABLE")}
    return {"count_by_job": counts, "count_pooled_S": pcount, "pooled": pooled, "per_job": per_job}


def _t11_job(rec: dict, job: int) -> dict:
    idx = [k for k, lab in enumerate(rec["labels"]) if lab["job"] == job]
    labels = [{a: b for a, b in rec["labels"][k].items() if a != "job"} for k in idx]
    return {"labels": labels, "counts": [rec["counts"][k] for k in idx], "shots": [rec["shots"][k] for k in idx]}


def _ones_c0(counts) -> list[int]:
    return [sum(n for key, n in c.items() if _bits(key)[0] == "1") for c in counts]


def t11_monitor(rec: dict) -> dict:
    """Test 11's jobs 2 and 3 (finding 29): the monitor's phase and weight per repeat, the switches, the weight per
    span, the boundary table and the verdicts, per job, by the package's monitor_phase and monitor_weight with the
    rule's thresholds and job 1's R0; the verdicts pooled over the two jobs; the gap between them."""
    R0 = rec["archived"]["analysis"]["R0"]
    out = {}
    for j in (2, 3):
        d = _t11_job(rec, j)
        spans = _span_record(rec["jobs"][str(j)]["execution_metadata"])
        ph = wait.monitor_phase(_ones_c0(d["counts"]), d["labels"], spans, T11_WAIT_US, shots=d["shots"][0], **T10_RULE)
        w = wait.monitor_weight(
            ph, R0["value"], exchange=R0["branches_exchanged"], abs_min=T11_W_MIN, n_se=T10_RULE["n_se"]
        )
        usable = ph["median_r"] >= T10_R_MIN
        pv = _verdict(usable, ph["n_within"], ph["n_boundary"])
        wv = _verdict(usable, w["n_within_w"], w["n_boundary_w"])
        rows = [{**x, **{k: y[k] for k in ("branch", "w", "se_w")}} for x, y in zip(ph["repeats"], w["repeats"])]
        out[str(j)] = {
            "phase_verdict": pv,
            "weight_verdict": T11_WEIGHT_WORDS.get(wv, wv),
            "phase": {k: v for k, v in ph.items() if k not in ("repeats", "pairs")},
            "weight": {k: v for k, v in w.items() if k not in ("repeats", "pairs", "boundary_table")},
            "boundary_table": {
                part: [
                    {
                        **x,
                        "phase_over_5_se": abs(x["d_phase"]) > 5 * x["se_phase"],
                        "w_over_5_se": abs(x["d_w"]) > 5 * x["se_w"],
                    }
                    for x in rows_
                ]
                for part, rows_ in w["boundary_table"].items()
            },
            "repeats": rows,
            "series": {k: [x[k] for x in rows] for k in ("k", "theta", "r", "w", "s", "se_w", "span", "straddles")},
        }
    a = [x for x in out["2"]["repeats"] if not x["straddles"]][-1]
    b = [x for x in out["3"]["repeats"] if not x["straddles"]][0]
    se_p, se_w = math.hypot(a["s"], b["s"]), math.hypot(a["se_w"], b["se_w"])
    d_p = wait._wrap(b["theta"] - a["theta"])
    gap = {
        "job2_last_k": a["k"],
        "job3_first_k": b["k"],
        "d_phase": d_p,
        "se_phase": se_p,
        "phase_differs_by_more_than_5_se": abs(d_p) > 5 * se_p,
        "d_w": b["w"] - a["w"],
        "se_w": se_w,
        "w_differs_by_more_than_5_se": abs(b["w"] - a["w"]) > 5 * se_w,
    }
    back = {v: k for k, v in T11_WEIGHT_WORDS.items()}
    pooled = {
        "phase": _pooled([out[j]["phase_verdict"] for j in out]),
        "weight": T11_WEIGHT_WORDS.get(_pooled([back.get(out[j]["weight_verdict"]) for j in out])),
    }
    return {"jobs": out, "pooled": pooled, "gap": gap}


def t11_job1(rec: dict) -> dict:
    """Test 11's job 1 (finding 29): test 7's analysis on day 2, by the functions test 11 ran (t7_ramsey_xy,
    t7_readings, t7_spans, t7_span_readings), with the seeds of its rulings; the weight change across each span boundary
    from the plain means of the three positions on either side (its ruling 3); R0 and the antiphase wait from P."""
    d = _t11_job(rec, 1)
    rows = []
    for r in rec["calibration_record"]["stamps"]:
        if r["kind"].startswith("job 1 "):
            rows.append({**r, "kind": r["kind"][len("job 1 ") :]})
    doc = {**d, "timestamps": rec["jobs"]["1"]["timestamps"], "calibration_record": {"stamps": rows}}
    analysis, _ = t7_ramsey_xy(doc, T11_SEEDS)
    readings = t7_readings(doc, analysis, T11_SEEDS)
    doc["archived"] = {"readings_after_the_data": readings}
    spans = {"spans": rec["jobs"]["1"]["execution_metadata"]["execution_spans"], "n_positions": len(d["labels"])}
    sr = t7_span_readings(doc, spans)
    changes = {}
    for name, b in sr["span_boundaries"].items():
        bw, aw = [x["weight"] for x in b["before"]], [x["weight"] for x in b["after"]]
        ch = float(np.mean(aw) - np.mean(bw))
        changes[name] = {
            "between_positions": b["between_positions"],
            "before": b["before"],
            "after": b["after"],
            "mean_before": float(np.mean(bw)),
            "mean_after": float(np.mean(aw)),
            "change": ch,
            "at_least_0p10": abs(ch) >= T11_W_MIN,
        }
    P = analysis["fits"]["P"]["params"]
    return {
        "verdict": "CONFIRMED ON DAY 2" if analysis["verdict"] == "TWO FIXED FREQUENCIES" else "NOT CONFIRMED ON DAY 2",
        "package_verdict": analysis["verdict"],
        "analysis": analysis,
        "readings_after_the_data": readings,
        "spans_derived": t7_spans(spans),
        "span_readings_A26": sr,
        "weight_changes_across_boundaries": {
            "boundaries": changes,
            "n_at_least_0p10": sum(1 for c in changes.values() if c["at_least_0p10"]),
            "n_boundaries": len(changes),
        },
        "R0_for_the_monitor": P["A"] * math.exp(-T11_WAIT_US / P["tau_prime_us"]),
        "antiphase_wait_from_day2_split_us": 1.0 / (4 * P["delta_MHz"]),
    }


def t9_job1_43_134(rec: dict) -> dict:
    """Test 9's job 1 on 43 and 134 (finding 29): test 7's rule on day 2, by the package's ramsey_xy_fit with the rule's
    thresholds and the run's seeds (S's random starts 9304, P's 9305, the bootstrap SeedSequence([9306, qubit])), the
    verdict read from its clauses by test 7's table."""
    c = _gz(f"ibm_kingston/{rec['jobs']['1']['counts_file']['file']}")
    ones = _ones_per_qubit(c)
    quads = {"X": 0, "Y": 1}
    n0 = int(c["shots"][0])
    out = {}
    for q in (43, 134):
        j = c["qubits"].index(q)
        y = np.zeros((2, 2, 64), int)
        t = np.full((2, 64), np.nan)
        for k, lab in enumerate(c["labels"]):
            if lab["circuit"] in quads:
                qd, i = quads[lab["circuit"]], int(lab["t_requested_us"])
                y[lab["copy"] - 1, qd, i] = ones[k, j]
                t[qd, i] = lab["t_requested_us"]
        seeds = (T9_SEEDS["S_random_starts"], T9_SEEDS["P_random_starts"], T9_SEEDS["bootstrap_root"] + (q << 32))
        r = wait.ramsey_xy_fit(t, y, n0, np.arange(0, 64, 2), seeds=seeds, n_boot=2000, **T9_RULE)
        cl = r["clauses"]
        pc = r["bootstrap"]["percentiles_5_50_95"]
        if cl["S_within_the_margin_of_P_or_below"] and (
            cl["delta_lower_bound_below_the_floor"] or cl["b_interval_reaches_an_edge"]
        ):
            v = "NO RESOLVED SPLIT"
        elif (
            cl["P_below_S_by_more_than_the_margin"]
            and cl["delta_lower_bound_above_the_floor"]
            and cl["b_interval_inside_the_edges"]
        ):
            v = "TWO FIXED FREQUENCIES"
        else:
            v = "NOT SETTLED"
        out[str(q)] = {
            "verdict": v,
            "S": r["S"],
            "P": r["P"],
            "band": r["band"],
            "clauses": cl,
            "deciding": {
                "held_out_error_S": r["S"]["held_out_error"],
                "held_out_error_P": r["P"]["held_out_error"],
                "P_minus_S": r["P"]["held_out_error"] - r["S"]["held_out_error"],
                "delta_ci90_kHz": [pc["delta_MHz"][0] * 1e3, pc["delta_MHz"][2] * 1e3],
                "b_ci90": [pc["b"][0], pc["b"][2]],
            },
            "bootstrap": {k: r["bootstrap"][k] for k in ("draws", "returned", "refits_failed", "percentiles_5_50_95")},
        }
    return out


def kingston_spans(rec: dict) -> dict:
    """Tests 8 and 9's execution spans: each job's durations, runs of positions and gaps, derived from the provider's
    starts, stops and positions as A26 derived test 7's (t7_spans), with each job's shots per position from its
    record (the estimate's shots over its positions)."""
    runs = {"t8": ar.load("ibm_kingston/t8-survey.json"), "t9": ar.load("ibm_kingston/t9-day2-scan.json")}
    out = []
    for j in rec["jobs"]:
        job = runs[j["test"]]["jobs"][str(j["job"])]
        shots = job["pre_submission_estimate"]["shots"] // job["positions"]
        out.append(t7_spans({"spans": j["spans"], "n_positions": j["n_positions"]}, shots))
    return {"jobs": out}


# --------------------------------------------------------------------------- tests 16 and 17, the per-shot reads (A28)
#: Test 15's words, as tests 16 and 17 apply them: SHARED above 3, INDEPENDENT below 1.5; at a boundary NO CHANGE at or
#: under 2, BETWEEN over 2 to 3, CHANGE over 3; test 17's middle test, the middle third of a job's time, MIDDLE HIGH at
#: a Z of 2.0 or more and NOT SEEN under 1.0
T15_SHARED, T15_INDEPENDENT, T15_NO_CHANGE, T15_CHANGE = 3.0, 1.5, 2.0, 3.0
T17_MIDDLE, T17_Z_HIGH, T17_Z_LOW = (1 / 3, 2 / 3), 2.0, 1.0


def _t15_word(z: float) -> str:
    return "NO CHANGE" if z <= T15_NO_CHANGE else ("BETWEEN" if z <= T15_CHANGE else "CHANGE")


def per_shot_span(r: dict) -> dict:
    """One span's readings in its quadrature of record, recomputed through the package (A28) from the sweep means its
    read published: at four places, recovered exactly as k/n over the span's rows, so that a mean on the threshold falls
    as it fell in the read; the shot-noise share, the duration and the rows are the record's. The sd at the lag used,
    its ceiling at three sweeps, and beside it the sd at one sweep less and more and at the 20th to 80th threshold."""
    n = r["n_rows"]
    k = np.rint(np.asarray(r["sweep_means"], float) * n)
    assert np.all(np.abs(k / n - np.asarray(r["sweep_means"])) < 6e-5)
    m = k / n
    T = r["duration_s"]
    sweep = T / len(m)
    v_obs = float(m.var(ddof=1))
    ratio = v_obs / r["v_ind"]
    a = wait.two_state_reading(m, sweep, v_ind=r["v_ind"])
    b = wait.two_state_reading(m, sweep, v_ind=r["v_ind"], percentiles=(20, 80))
    out = {
        "n_shots": len(m),
        "sweep_s": sweep,
        "v_obs": v_obs,
        "ratio": ratio,
        "word_of_the_ratio": "SHARED"
        if ratio > T15_SHARED
        else ("INDEPENDENT" if ratio < T15_INDEPENDENT else "UNDECIDED"),
        "excess_over_independent": a["excess_over_shot_noise"],
        "acf_lags_1_to_200": a["acf"],
        "lag_1_over_e": a["lag"],
        "threshold": a["threshold"],
        "threshold_20_80": b["threshold"],
        "duty_b": a["duty"],
        "duty_b_at_threshold_20_80": b["duty"],
        "switches": a["switches"],
        "n_runs": a["n_runs"],
        "dwell_high_s": a["dwell_high_s"],
        "dwell_low_s": a["dwell_low_s"],
        "quarter_span_duties": a["quarter_span_duties"],
        "mid_sweep_fraction_middle_fifth": a["mid_sweep_fraction"],
    }
    if len(m) >= 1000:
        out["acf_lags_490_to_510"] = wait.sweep_autocorrelation(m, range(490, 511))
    if out["word_of_the_ratio"] == "SHARED":
        e = wait.time_average_sd(a["duty"], a["lag"], sweep, T)
        used = e["sweeps_used"]
        out |= {
            "tau_c_sweeps_used": used,
            "tau_c_s": e["tau_c_s"],
            "tau_c_ceiling": e["at_ceiling"],
            "telegraph_sd": e["sd"],
            "telegraph_sd_tau_minus_1": wait.time_average_sd(a["duty"], used - 1, sweep, T, ceiling=None)["sd"],
            "telegraph_sd_tau_plus_1": wait.time_average_sd(a["duty"], used + 1, sweep, T, ceiling=None)["sd"],
            "telegraph_sd_at_threshold_20_80": wait.time_average_sd(b["duty"], used, sweep, T, ceiling=None)["sd"],
        }
    return out


def per_shot_job(job: dict) -> dict:
    """A monitor job of a per-shot read: every span of 143 in its quadrature of record (per_shot_span), with the duty
    on the weight's branch, the branch read from the span's published mean phase (test 15's rule: b where the
    quadrature's component of that phase is negative, else 1 - b)."""
    wd = job["qubits"]["143"]["waits"]["monitor"]
    q = wd["quadrature_of_record"]
    spans = []
    for s in wd["spans"]:
        if q not in s:
            spans.append({})
            continue
        r = per_shot_span(s[q])
        g = math.sin(s["theta_bar"]) if q == "Y" else math.cos(s["theta_bar"])
        branch = "b" if g < 0 else "1 - b"
        spans.append(
            {"span": s["span"], q: r, "w_branch": branch, "w_duty": r["duty_b"] if branch == "b" else 1 - r["duty_b"]}
        )
    return {"quadrature": q, "spans": spans}


def _pair(ra: dict, rb: dict, published=None) -> dict:
    """Test 15's boundary row between two SHARED spans, by the package's boundary_ratio, with its sensitivities."""
    br = wait.boundary_ratio(ra["duty_b"], ra["telegraph_sd"], rb["duty_b"], rb["telegraph_sd"])
    t2 = wait.boundary_ratio(
        ra["duty_b_at_threshold_20_80"],
        ra["telegraph_sd_at_threshold_20_80"],
        rb["duty_b_at_threshold_20_80"],
        rb["telegraph_sd_at_threshold_20_80"],
    )
    sens = {"threshold_20_80": {**t2, "word": _t15_word(t2["ratio"])}}
    for name, key in (
        ("tau_minus_1_sweep", "telegraph_sd_tau_minus_1"),
        ("tau_plus_1_sweep", "telegraph_sd_tau_plus_1"),
    ):
        x = wait.boundary_ratio(ra["duty_b"], ra[key], rb["duty_b"], rb[key])
        sens[name] = {"combined_sd": x["combined_sd"], "ratio": x["ratio"], "word": _t15_word(x["ratio"])}
    row = {**br, "word": _t15_word(br["ratio"]), "sensitivity": sens}
    row["word_changes_under_sensitivity"] = sorted(k for k, v in sens.items() if v["word"] != row["word"])
    if published:
        z = abs(published["difference"]) / br["combined_sd"]
        row["published_difference_over_the_same_sd"] = {"ratio": z, "word": _t15_word(z)}
    return row


def per_shot_boundaries(rec: dict, jobs: dict, keys) -> list:
    """Every adjacent pair of spans within each job, in the order the read lists them."""
    out = []
    for b in rec["boundaries"]:
        if b["job"] not in keys:
            continue
        j = jobs[b["job"]]
        sp = {s["span"]: s for s in j["spans"] if s}
        ra, rb = sp[b["spans"][0]][j["quadrature"]], sp[b["spans"][1]][j["quadrature"]]
        out.append({"duties": [ra["duty_b"], rb["duty_b"]], **_pair(ra, rb, b.get("published"))})
    return out


def _job_mean(job: dict) -> dict:
    sp = [s for s in job["spans"] if s]
    q = job["quadrature"]
    r = [s[q] for s in sp]
    return {
        "w_branches": sorted({s["w_branch"] for s in sp}),
        "span_w_duties": [s["w_duty"] for s in sp],
        "job_mean_w_duty": float(np.mean([s["w_duty"] for s in sp])),
        "job_sd": math.sqrt(sum(x["telegraph_sd"] ** 2 for x in r)) / len(r),
        "span_tau_c_s": [x["tau_c_s"] for x in r],
        "tau_c_median_s": float(np.median([x["tau_c_s"] for x in r])),
    }


def _between(a: dict, b: dict) -> dict:
    """Two jobs' mean duties on the weight's branch over their combined sd (test 15's); none where a branch differs."""
    if len(a["w_branches"]) != 1 or a["w_branches"] != b["w_branches"]:
        return {"word": None}
    d = b["job_mean_w_duty"] - a["job_mean_w_duty"]
    sd = math.hypot(a["job_sd"], b["job_sd"])
    return {"difference": d, "combined_sd": sd, "ratio": abs(d) / sd, "word": _t15_word(abs(d) / sd)}


def t16_day3_read(rec: dict, t15: dict, day3: dict) -> dict:
    """Test 16 (finding 30): day 3's monitor spans, boundaries and jobs from the read's published sweep means, through
    the package (per_shot_span); day 2's spans the same way from test 15's record; the day means on the weight's branch,
    each over six spans, with each day's sd the root sum of squares over six; the middle span less the mean of the ends
    (beside, not a test); job 1's published weights per span, their sd at the borrowed tau_c (the median of day 3's)."""
    a = rec["archived"]["analysis"]
    jobs = {k: per_shot_job(a["jobs"][k]) for k in ("d3-job2", "d3-job3")}
    day2 = {k: per_shot_job(t15["archived"]["analysis"]["jobs"][k]) for k in ("t11-job2", "t11-job3")}
    js = [_job_mean(jobs[k]) for k in ("d3-job2", "d3-job3")]
    between = _between(*js)
    w2 = [s["w_duty"] for k in day2 for s in day2[k]["spans"]]
    s2 = [s["Y"]["telegraph_sd"] for k in day2 for s in day2[k]["spans"]]
    w3 = [s["w_duty"] for k in jobs for s in jobs[k]["spans"]]
    s3 = [s["Y"]["telegraph_sd"] for k in jobs for s in jobs[k]["spans"]]
    m2, m3 = float(np.mean(w2)), float(np.mean(w3))
    sd2, sd3 = math.sqrt(sum(x * x for x in s2)) / len(s2), math.sqrt(sum(x * x for x in s3)) / len(s3)
    means = {
        "day_mean_duties": [m2, m3],
        "day_sds": [sd2, sd3],
        "difference": m3 - m2,
        "combined_sd": math.hypot(sd2, sd3),
        "difference_over_sd": (m3 - m2) / math.hypot(sd2, sd3),
    }
    mm = []
    for j in (*day2.values(), *jobs.values()):
        r = [s["Y"] for s in j["spans"]]
        d = r[1]["duty_b"] - (r[0]["duty_b"] + r[2]["duty_b"]) / 2
        sd = math.sqrt(r[1]["telegraph_sd"] ** 2 + (r[0]["telegraph_sd"] ** 2 + r[2]["telegraph_sd"] ** 2) / 4)
        mm.append({"middle_minus_mean_of_ends": d, "telegraph_sd": sd, "difference_over_sd": d / sd})
    tau = float(np.median([s["Y"]["tau_c_s"] for j in jobs.values() for s in j["spans"]]))
    w = [x["weighted_mean"] for x in day3["archived"]["analysis"]["jobs"]["1"]["span_readings_A26"]["weight_per_span"]]
    sp1 = sorted(day3["jobs"]["1"]["execution_metadata"]["execution_spans"], key=lambda s: s["start_utc"])
    dur = [x["duration_s"] for x in sp1]
    sds = [math.sqrt(2 * x * (1 - x) * tau / T) for x, T in zip(w, dur)]
    rows = []
    for i in range(len(w) - 1):
        d = w[i + 1] - w[i]
        sd = math.hypot(sds[i], sds[i + 1])
        rows.append({"difference": d, "combined_sd": sd, "ratio": abs(d) / sd, "word": _t15_word(abs(d) / sd)})
    return {
        "jobs": jobs,
        "boundaries": per_shot_boundaries(a, jobs, ("d3-job2", "d3-job3")),
        "between_jobs": {"jobs": js, "rows": [between]},
        "day2": day2,
        "beside_day_means": means,
        "beside_middle_minus_ends": mm,
        "job1_borrowed": {"tau_c_borrowed_s": tau, "telegraph_sd_borrowed": sds, "rows": rows},
    }


def _line(t, y, sd) -> dict:
    """A straight line of duty on time, weighted by 1 / sd², and its slope over its sd (test 17's beside)."""
    t, y, w = np.asarray(t, float), np.asarray(y, float), 1 / np.asarray(sd, float) ** 2
    X = np.stack([np.ones_like(t), t], axis=1)
    G = X.T @ (X * w[:, None])
    a0, b0 = np.linalg.solve(G, X.T @ (w * y))
    se = math.sqrt(np.linalg.inv(G)[1, 1])
    return {"intercept": float(a0), "slope_per_unit_t": float(b0), "slope_sd": se, "slope_over_sd": float(b0) / se}


def _contrast(rows: list, duty: str, sd: str) -> dict:
    mid = [r for r in rows if T17_MIDDLE[0] <= r["t"] <= T17_MIDDLE[1]]
    oth = [r for r in rows if not (T17_MIDDLE[0] <= r["t"] <= T17_MIDDLE[1])]
    sd_mid = math.sqrt(sum(r[sd] ** 2 for r in mid)) / len(mid)
    sd_oth = math.sqrt(sum(r[sd] ** 2 for r in oth)) / len(oth)
    C = float(np.mean([r[duty] for r in mid])) - float(np.mean([r[duty] for r in oth]))
    s = math.hypot(sd_mid, sd_oth)
    return {
        "C": C,
        "sd": s,
        "C_over_sd": C / s,
        "sd_mid": sd_mid,
        "sd_other": sd_oth,
        "mid_spans": [r["span"] for r in mid],
        "other_spans": [r["span"] for r in oth],
    }


def t17_read(rec: dict) -> dict:
    """Test 17 (finding 30): every monitor span of A1, A2 and B1 from the read's published sweep means through the
    package (per_shot_span); the boundary rows; the jobs' means and the rows between adjacent jobs; and the middle test
    its rule fixed: each span's centre t as a fraction of the job's time from the provider's starts and stops, the
    contrast C of the spans with t in [1/3, 2/3] against the others with its sd, Z = (sum of C / sd) / sqrt(n) over the
    contributing jobs, and its word; beside, Z at the 20th to 80th threshold and the weighted line of duty on t."""
    a = rec["archived"]["per_shot_read"]
    keys = ("A1", "A2", "B1")
    jobs = {k: per_shot_job(a["jobs"][k]) for k in keys}
    js = {k: _job_mean(jobs[k]) for k in keys}
    middle = []
    for k in keys:
        sp = sorted(a["jobs"][k]["spans"], key=lambda s: s["start_utc"])
        t0 = datetime.fromisoformat(sp[0]["start_utc"])
        L = (datetime.fromisoformat(sp[-1]["stop_utc"]) - t0).total_seconds()
        cen = {}
        for s in sp:
            u0, u1 = datetime.fromisoformat(s["start_utc"]), datetime.fromisoformat(s["stop_utc"])
            cen[s["span"]] = ((u0 - t0).total_seconds() + (u1 - u0).total_seconds() / 2) / L
        rows = []
        for s in jobs[k]["spans"]:
            r = s["Y"]
            rows.append(
                {
                    "span": s["span"],
                    "t": cen[s["span"]],
                    "duty": r["duty_b"],
                    "sd": r["telegraph_sd"],
                    "duty_2080": r["duty_b_at_threshold_20_80"],
                    "sd_2080": r["telegraph_sd_at_threshold_20_80"],
                }
            )
        c = _contrast(rows, "duty", "sd")
        middle.append(
            {
                "job": k,
                "spans": [{"span": r["span"], "t": r["t"]} for r in rows],
                **c,
                "beside_threshold_20_80": _contrast(rows, "duty_2080", "sd_2080"),
                "beside_line_duty_on_t": _line(
                    [r["t"] for r in rows], [r["duty"] for r in rows], [r["sd"] for r in rows]
                ),
            }
        )
    n = len(middle)
    Z = sum(x["C_over_sd"] for x in middle) / math.sqrt(n)
    word = "MIDDLE HIGH" if Z >= T17_Z_HIGH else ("NOT SEEN" if Z < T17_Z_LOW else "UNDECIDED")
    return {
        "jobs": jobs,
        "boundaries": per_shot_boundaries(a, jobs, keys),
        "between_jobs_job_rows": js,
        "between_jobs": [_between(js[x], js[y]) for x, y in zip(keys, keys[1:])],
        "middle_test": {
            "jobs": middle,
            "pooled": {
                "n_contributing_jobs": n,
                "Z": Z,
                "word": word,
                "beside_Z_at_threshold_20_80": sum(x["beside_threshold_20_80"]["C_over_sd"] for x in middle)
                / math.sqrt(n),
            },
        },
    }
