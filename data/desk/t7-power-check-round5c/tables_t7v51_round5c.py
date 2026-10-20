"""Test 7, version 5.1, round 5c: the report's side-by-side tables, the second machine's draws beside the main machine's (counting only).

Reads results-t7v51-round5c.jsonl (the second machine, round 5c) and results-t7v51.jsonl (the main machine, round 5b) and prints, in
markdown: the keep verdict from each machine's own lines (the 80% test over the 117 counted points, 88 needed) with the
counts by generating verdict; the pass fraction by delta and by b, the two machines side by side; and the full table over
the 135 points, each machine's fractions of NO RESOLVED SPLIT / TWO FIXED FREQUENCIES / NOT SETTLED, its 80% test, and
the number of draws whose verdict differs between the machines. Nothing is fitted or corrected; a difference is shown,
never reconciled.

Usage:  python tables_t7v51_round5c.py <results-t7v51-round5c.jsonl> <results-t7v51.jsonl>
"""

from __future__ import annotations

import json
import sys

V = ("NO RESOLVED SPLIT", "TWO FIXED FREQUENCIES", "NOT SETTLED")
SHORT = {"NO RESOLVED SPLIT": "NRS", "TWO FIXED FREQUENCIES": "2F", "NOT SETTLED": "NS"}


def load(p):
    out = {}
    for line in open(p):
        if line.strip():
            r = json.loads(line)
            out[r["index"]] = r
    return out


def pct(x):
    v = round(100 * x, 1)
    return f"{v:g}"


def frac(r):
    return "/".join(pct(r["fraction"][v]) for v in V)


def keep(lines):
    counted = [r for r in lines.values() if r["counted"]]
    by = {g: (sum(bool(r["passes_80"]) for r in counted if r["generating_verdict"] == g),
              sum(r["generating_verdict"] == g for r in counted)) for g in ("NO RESOLVED SPLIT", "TWO FIXED FREQUENCIES")}
    n = sum(bool(r["passes_80"]) for r in counted)
    return n, len(counted), by, ("KEPT" if n >= 88 else "NOT KEPT") if len(counted) == 117 else None


def mean_shares(rows):
    return "/".join(pct(sum(r["fraction"][v] for r in rows) / len(rows)) for v in V)


def main(pd, pm):
    D, M = load(pd), load(pm)
    for name, L in (("The second machine (round 5c)", D), ("the main machine (round 5b)", M)):
        n, c, by, v = keep(L)
        print(f"- **{name}: {v}**, {n} of {c} counted points at or above 80% (88 needed); NO RESOLVED SPLIT {by['NO RESOLVED SPLIT'][0]} "
              f"of {by['NO RESOLVED SPLIT'][1]}, TWO FIXED FREQUENCIES {by['TWO FIXED FREQUENCIES'][0]} of {by['TWO FIXED FREQUENCIES'][1]}.")
    print("\n### The pass fraction by δ (counted points at or above 80%; mean share NRS / 2F / NS, % of draws)\n")
    print("| δ kHz | points | generating | The second machine: at or above 80% | main: at or above 80% | The second machine: mean shares | main: mean shares |")
    print("|---|---|---|---|---|---|---|")
    for dl in sorted({r["delta_kHz"] for r in D.values()}):
        idx = [i for i in D if D[i]["delta_kHz"] == dl]
        gen = D[idx[0]]["generating_verdict"]
        cnt = D[idx[0]]["counted"]
        a = f"{sum(bool(D[i]['passes_80']) for i in idx)} of {len(idx)}" if cnt else "not counted"
        b = f"{sum(bool(M[i]['passes_80']) for i in idx)} of {len(idx)}" if cnt else "not counted"
        print(f"| {dl:g} | {len(idx)} | {gen if cnt else 'either (boundary)'} | {a} | {b} | {mean_shares([D[i] for i in idx])} | {mean_shares([M[i] for i in idx])} |")
    print("\n### The pass fraction by b (counted points with δ > 0; mean share of the generating verdict)\n")
    print("| b | The second machine: at or above 80% | main: at or above 80% | The second machine: mean share | main: mean share |")
    print("|---|---|---|---|---|")
    for bb in (0.5, 0.37):
        idx = [i for i in D if D[i]["counted"] and D[i]["delta_kHz"] > 0 and D[i]["b"] == bb]
        print(f"| {bb:g} | {sum(bool(D[i]['passes_80']) for i in idx)} of {len(idx)} | {sum(bool(M[i]['passes_80']) for i in idx)} of {len(idx)} | "
              f"{pct(sum(D[i]['fraction_generating_verdict'] for i in idx) / len(idx))}% | {pct(sum(M[i]['fraction_generating_verdict'] for i in idx) / len(idx))}% |")
    print("\n### The full table over the 135 points (fractions NRS / 2F / NS, % of 200 draws)\n")
    print("| # | Δ0 kHz | τ µs | δ kHz | b | role | generating | The second machine | main | ≥ 80%, the second machine / main | draws differing |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for i in sorted(D):
        d, m = D[i], M[i]
        role = "counted" if d["counted"] else "boundary (δ = 5)"
        ok = lambda r: "" if r["passes_80"] is None else ("yes" if r["passes_80"] else "**no**")
        dd = {x["draw"]: x["verdict"] for x in d["draws"]}
        nd = sum(dd[x["draw"]] != x["verdict"] for x in m["draws"])
        fd = frac(d) if frac(d) == frac(m) else f"**{frac(d)}**"
        fm = frac(m) if frac(d) == frac(m) else f"**{frac(m)}**"
        b = "" if d["delta_kHz"] == 0 else f"{d['b']:g}"
        print(f"| {i} | {d['Delta0_kHz']} | {d['tau_us']} | {d['delta_kHz']:g} | {b} | {role} | {d['generating_verdict']} | {fd} | {fm} | "
              f"{ok(d)} / {ok(m)} | {nd or ''} |")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
