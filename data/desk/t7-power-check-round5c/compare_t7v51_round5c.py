"""Test 7, version 5.1, round 5c: the second machine's grid read against the main machine's, point for point and draw for draw.

Reads two files and nothing else: results-t7v51-round5c.jsonl (the second machine, round 5c) and results-t7v51.jsonl (the main
machine, round 5b). Computes nothing of the test: it counts and subtracts. For every point both have written:

- the verdict fractions, and their difference;
- every draw's verdict, and the largest absolute difference in every fitted and derived number of the draw (the
  held-out errors, the chi-squares, S's and P's fitted values, the two 90% intervals), and the convergence counts;
- a draw "differs" when its verdict differs; numbers are reported as differences, never reconciled.

It also computes each machine's keep verdict from its own lines (the 80% test over the 117 counted points, 88 needed).

Usage:  python compare_t7v51_round5c.py <results-t7v51-round5c.jsonl> <results-t7v51.jsonl> [out.json]
"""

from __future__ import annotations

import json
import sys

NUM = ("mae_S", "mae_P", "chi2_S", "chi2_P", "S_Delta_kHz", "S_tau_us", "P_Delta0_kHz", "P_delta_kHz", "P_b", "P_tau_prime_us")
PAIRS = ("delta_ci90_kHz", "b_ci90")
VERDICTS = ("NO RESOLVED SPLIT", "TWO FIXED FREQUENCIES", "NOT SETTLED")


def load(p):
    out = {}
    with open(p) as f:
        for line in f:
            if line.strip():
                r = json.loads(line)
                out[r["index"]] = r
    return out


def keep(lines):
    counted = [r for r in lines.values() if r["counted"]]
    passing = [r for r in counted if r["passes_80"]]
    by = {}
    for g in ("NO RESOLVED SPLIT", "TWO FIXED FREQUENCIES"):
        cg = [r for r in counted if r["generating_verdict"] == g]
        by[g] = {"passing": sum(bool(r["passes_80"]) for r in cg), "of": len(cg)}
    return {"counted_written": len(counted), "passing": len(passing), "needed": 88, "by_generating_verdict": by,
            "verdict": None if len(counted) < 117 else ("KEPT" if len(passing) >= 88 else "NOT KEPT")}


def main(pd, pm, out=None):
    D, M = load(pd), load(pm)
    both = sorted(set(D) & set(M))
    pts, n_draw_diff, n_frac_diff = [], 0, 0
    for i in both:
        d, m = D[i], M[i]
        fd = {v: d["fraction"][v] - m["fraction"][v] for v in VERDICTS}
        frac_same = all(abs(x) < 1e-12 for x in fd.values())
        rec = {"index": i, "fraction_round5c": d["fraction"], "fraction_main": m["fraction"], "fraction_difference": fd,
               "fractions_equal": frac_same, "starts_failed_round5c": d["starts_failed"], "starts_failed_main": m["starts_failed"]}
        if d.get("draws") and m.get("draws"):
            dd = {r["draw"]: r for r in d["draws"]}
            mm = {r["draw"]: r for r in m["draws"]}
            diffs = [k for k in sorted(dd) if dd[k]["verdict"] != mm[k]["verdict"]]
            mx = {}
            for k in NUM:
                mx[k] = max(abs(dd[j][k] - mm[j][k]) for j in dd)
            for k in PAIRS:
                mx[k] = max(max(abs(a - b) for a, b in zip(dd[j][k], mm[j][k])) for j in dd)
            conv = [j for j in dd if dd[j]["starts_failed"] != mm[j]["starts_failed"]]
            rec.update({"draws_compared": len(dd), "draws_verdict_differs": diffs,
                        "draws_verdict_differs_detail": [{"draw": j, "round5c": dd[j]["verdict"], "main": mm[j]["verdict"],
                                                          "round5c_fit": {k: dd[j][k] for k in NUM + PAIRS},
                                                          "main_fit": {k: mm[j][k] for k in NUM + PAIRS},
                                                          "starts_failed_round5c": dd[j]["starts_failed"],
                                                          "starts_failed_main": mm[j]["starts_failed"]} for j in diffs],
                        "largest_abs_difference": mx, "draws_whose_convergence_counts_differ": len(conv)})
            n_draw_diff += len(diffs)
        n_frac_diff += not frac_same
        pts.append(rec)
    res = {"round5c_points": len(D), "main_points": len(M), "points_compared": len(both),
           "points_where_fractions_differ": [p["index"] for p in pts if not p["fractions_equal"]],
           "n_points_where_fractions_differ": n_frac_diff, "draws_whose_verdict_differs": n_draw_diff,
           "keep_round5c": keep(D), "keep_main": keep(M), "points": pts}
    if out:
        with open(out, "w") as f:
            json.dump(res, f, indent=1)
    return res


if __name__ == "__main__":
    r = main(*sys.argv[1:4])
    print(json.dumps({k: v for k, v in r.items() if k != "points"}, indent=1))
    for p in r["points"]:
        line = f"#{p['index']}: fractions {'equal' if p['fractions_equal'] else 'DIFFER'}"
        if "draws_compared" in p:
            line += (f"; {p['draws_compared']} draws, verdict differs in {len(p['draws_verdict_differs'])}; "
                     f"convergence counts differ in {p['draws_whose_convergence_counts_differ']}; largest differences "
                     + ", ".join(f"{k} {v:.2g}" for k, v in p["largest_abs_difference"].items()))
        print(line)
