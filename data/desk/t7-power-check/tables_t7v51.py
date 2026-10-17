"""Test 7, version 5.1: the keep verdict and the report's tables, from results-t7v51.jsonl (counting only).

Reads results-t7v51.jsonl (one line per grid point) and, read only, ../t7v5/timing-t7v5.json for round 5's six timed
points. Prints, in markdown: the keep verdict over the counted points written (117 counted, 88 needed); the counts by
generating verdict; the alias and the edge, each on its own line, counting every draw that shows either; the pass
fraction by delta, by b and by both (a reading for the threshold, never a change); the full table; a compact matrix; the
failing counted points with the rule's clauses each draw met; convergence; and the cost. Writes keep-t7v51.json.

The alias: a draw whose P point fit has |Delta0| + delta above 250 kHz (outside the band; version 5.1's bounds forbid
it), with those within 1 kHz of 250 kHz counted beside as pressing against the band. The edge: a draw whose P point fit
has b below 0.05 or above 0.95 (round 5's reading); beside it, the draws whose b interval reaches an edge (the rule's
clause).

Usage:  python tables_t7v51.py
"""

from __future__ import annotations

import json
from pathlib import Path
from statistics import median

HERE = Path(__file__).resolve().parent
V = ("NO RESOLVED SPLIT", "TWO FIXED FREQUENCIES", "NOT SETTLED")
N_POINTS, N_COUNTED, NEEDED = 135, 117, 88

pts = [json.loads(x) for x in (HERE / "results-t7v51.jsonl").read_text().splitlines() if x.strip()]
pts.sort(key=lambda p: p["index"])
r5 = json.loads((HERE.parent / "t7v5" / "timing-t7v5.json").read_text())["points"]


def pct(x):
    """Per cent to the half per cent a fraction of 200 draws can take (79.5, not a rounded 80)."""
    return f"{100 * x:.1f}".rstrip("0").rstrip(".")


def bstr(b):
    return "" if b is None else f"{b}"


def role(p):
    return "boundary (δ = 5)" if p["boundary"] else "counted"


def frac(d, f):
    return sum(1 for x in d if f(x)) / len(d)


def clauses(d):
    """The share of draws meeting each clause of the rule."""
    return {
        "S within 0.01": frac(d, lambda x: x["mae_S"] <= x["mae_P"] + 0.01),
        "P better by 0.01": frac(d, lambda x: x["mae_P"] < x["mae_S"] - 0.01),
        "δ lower bound < 5": frac(d, lambda x: x["delta_ci90_kHz"][0] < 5),
        "δ lower bound > 5": frac(d, lambda x: x["delta_ci90_kHz"][0] > 5),
        "b interval reaches an edge": frac(d, lambda x: x["b_ci90_reaches_edge"]),
        "b interval inside": frac(d, lambda x: not x["b_ci90_reaches_edge"]),
    }


def kind(p):
    """The failing point's kind, from the clause its draws met least, with every clause's share and the alias and edge."""
    d = p["draws"]
    c = clauses(d)
    al = sum(x["P_outside_band"] for x in d)
    ed = sum(x["P_b_at_edge"] for x in d)
    f = p["fraction"]
    if p["generating_verdict"] == "NO RESOLVED SPLIT":
        either = frac(d, lambda x: x["delta_ci90_kHz"][0] < 5 or x["b_ci90_reaches_edge"])
        need = {"threshold (the split resolved below 5 kHz: S not within 0.01 of P)": c["S within 0.01"], "split (neither δ's lower bound below 5 kHz nor b's interval at an edge)": either}
        detail = (f"S within 0.01 in {pct(c['S within 0.01'])}%, δ lower bound < 5 kHz in {pct(c['δ lower bound < 5'])}%, "
                  f"b interval at an edge in {pct(c['b interval reaches an edge'])}%")
    else:
        need = {"span (the beat not resolved in the held-out error: P not better by 0.01)": c["P better by 0.01"], "split (δ lower bound not above 5 kHz)": c["δ lower bound > 5"],
                "weight (b interval reaches an edge)": c["b interval inside"]}
        detail = (f"P better by 0.01 in {pct(c['P better by 0.01'])}%, δ lower bound > 5 kHz in {pct(c['δ lower bound > 5'])}%, "
                  f"b interval inside in {pct(c['b interval inside'])}%")
    k = min(need, key=need.get)
    return (f"{k}: {detail}; the draws went NRS {pct(f['NO RESOLVED SPLIT'])}%, 2F {pct(f['TWO FIXED FREQUENCIES'])}%, "
            f"NS {pct(f['NOT SETTLED'])}%; alias draws {al}, edge draws {ed}"), k


counted = [p for p in pts if p["counted"]]
n_pass = sum(bool(p["passes_80"]) for p in counted)
counted_complete = len(counted) == N_COUNTED
all_draws = [x for p in pts for x in p["draws"]]
alias = {"draws": sum(x["P_outside_band"] for x in all_draws), "pressing": sum(x["P_presses_band"] for x in all_draws),
         "points_with_pressing": sorted({p["index"] for p in pts for x in p["draws"] if x["P_presses_band"]})}
edge = {
    "draws_b_point_fit_at_edge": sum(x["P_b_at_edge"] for x in all_draws),
    "draws_b_interval_reaches_edge": sum(x["b_ci90_reaches_edge"] for x in all_draws),
    "by_generating": {g: {"b_point_fit_at_edge": sum(x["P_b_at_edge"] for p in pts if p["generating_verdict"] == g for x in p["draws"]),
                          "b_interval_reaches_edge": sum(x["b_ci90_reaches_edge"] for p in pts if p["generating_verdict"] == g for x in p["draws"]),
                          "draws": sum(len(p["draws"]) for p in pts if p["generating_verdict"] == g)}
                      for g in ("NO RESOLVED SPLIT", "TWO FIXED FREQUENCIES", "either")},
    "edge_draws_returning": {v: sum(x["P_b_at_edge"] and x["verdict"] == v for x in all_draws) for v in V},
}
keep = {
    "points_written": len(pts),
    "complete": len(pts) == N_POINTS,
    "n_counted_written": len(counted),
    "n_counted_passing_80": n_pass,
    "needed": NEEDED,
    "verdict": ("KEPT" if n_pass >= NEEDED else "NOT KEPT") if counted_complete else "INCOMPLETE",
    "failing_counted_points": [p["index"] for p in counted if not p["passes_80"]],
    "failing_by_kind": {},
    "by_generating_verdict": {
        g: {"pass": sum(bool(p["passes_80"]) for p in counted if p["generating_verdict"] == g),
            "of": sum(p["generating_verdict"] == g for p in counted)}
        for g in ("NO RESOLVED SPLIT", "TWO FIXED FREQUENCIES")
    },
    "alias": alias,
    "edge": edge,
    "by_delta": {}, "by_b": {}, "by_delta_and_b": {}, "by_tau_and_delta": {},
    "starts_failed": {k: sum(p["starts_failed"][k] for p in pts) for k in ("S", "P", "refits")},
    "starts_run": {k: sum(p["starts_run"][k] for p in pts) for k in ("S", "P", "refits")},
    "cpu_hours": sum(p["cpu_seconds"] for p in pts) / 3600,
    "cpu_seconds_per_draw_mean": sum(p["cpu_seconds"] for p in pts) / max(1, sum(p["n_draws"] for p in pts)),
}
for p in counted:
    if not p["passes_80"]:
        keep["failing_by_kind"].setdefault(kind(p)[1], []).append(p["index"])
for dl in sorted({p["delta_kHz"] for p in pts}):
    q = [p for p in pts if p["delta_kHz"] == dl]
    keep["by_delta"][str(dl)] = {"points": len(q), "counted": all(p["counted"] for p in q),
                                 "pass": sum(bool(p["passes_80"]) for p in q if p["counted"]),
                                 "mean_fraction": {v: sum(p["fraction"][v] for p in q) / len(q) for v in V}}
for b in (0.5, 0.37):
    q = [p for p in counted if p["b"] == b]
    keep["by_b"][str(b)] = {"pass": sum(bool(p["passes_80"]) for p in q), "of": len(q),
                            "mean_fraction_generating": sum(p["fraction_generating_verdict"] for p in q) / max(1, len(q))}
for dl in sorted({p["delta_kHz"] for p in pts if p["delta_kHz"] > 0}):
    for b in (0.5, 0.37):
        q = [p for p in pts if p["delta_kHz"] == dl and p["b"] == b]
        if q:
            keep["by_delta_and_b"][f"{dl}|{b}"] = {"points": len(q), "pass": sum(bool(p["passes_80"]) for p in q if p["counted"]),
                                                   "mean_fraction": {v: sum(p["fraction"][v] for p in q) / len(q) for v in V}}
for tau in (15, 60, 150):
    for dl in sorted({p["delta_kHz"] for p in pts}):
        q = [p for p in pts if p["tau_us"] == tau and p["delta_kHz"] == dl]
        if q:
            keep["by_tau_and_delta"][f"{tau}|{dl}"] = {"points": len(q), "pass": sum(bool(p["passes_80"]) for p in q if p["counted"]),
                                                       "counted": all(p["counted"] for p in q)}
(HERE / "keep-t7v51.json").write_text(json.dumps({"keep": keep, "per_point": [{k: v for k, v in p.items() if k != "draws"} for p in pts]}, indent=1))

print(f"## Keep: {keep['verdict']}: {n_pass} of {len(counted)} counted points return the generating verdict in at least 80% of draws "
      f"({NEEDED} of {N_COUNTED} needed); {len(pts)} of {N_POINTS} points written.\n")
print("| generating verdict | points at or above 80% |")
print("|---|---|")
for g in ("NO RESOLVED SPLIT", "TWO FIXED FREQUENCIES"):
    b = keep["by_generating_verdict"][g]
    print(f"| {g} | {b['pass']} of {b['of']} |")

print("\n## The alias and the edge, over every draw written\n")
print(f"- **The alias:** {alias['draws']} of {len(all_draws)} draws have P's point fit outside the band (|Δ0| + δ above 250 kHz). "
      f"{alias['pressing']} press against it (within 1 kHz of 250 kHz), at points {alias['points_with_pressing']}.")
e = edge
print(f"- **The edge:** {e['draws_b_point_fit_at_edge']} of {len(all_draws)} draws have b's point fit below 0.05 or above 0.95; "
      f"{e['draws_b_interval_reaches_edge']} have b's interval reaching an edge. Those with the point fit at an edge returned "
      + ", ".join(f"{v} {e['edge_draws_returning'][v]}" for v in V) + ".")
for g, v in e["by_generating"].items():
    print(f"  - generating {g}: b's point fit at an edge in {v['b_point_fit_at_edge']} of {v['draws']} draws, "
          f"b's interval reaching an edge in {v['b_interval_reaches_edge']}")

print("\n## The pass fraction by δ and by b (a reading for the threshold, not a change)\n")
print("| δ kHz | points | generating | at or above 80% | mean share NRS / 2F / NS, % |")
print("|---|---|---|---|---|")
for dl, v in keep["by_delta"].items():
    gen = "either (boundary)" if dl == "5" else ("NO RESOLVED SPLIT" if dl in ("0", "3") else "TWO FIXED FREQUENCIES")
    passed = f"{v['pass']} of {v['points']}" if v["counted"] else "not counted"
    print(f"| {dl} | {v['points']} | {gen} | {passed} | " + " / ".join(pct(v["mean_fraction"][x]) for x in V) + " |")
print("\n| b | counted points at or above 80% (δ > 0) | mean share of the generating verdict |")
print("|---|---|---|")
for b, v in keep["by_b"].items():
    print(f"| {b} | {v['pass']} of {v['of']} | {pct(v['mean_fraction_generating'])}% |")
print("\n| δ kHz | b | at or above 80% | mean share NRS / 2F / NS, % |")
print("|---|---|---|---|")
for k, v in keep["by_delta_and_b"].items():
    dl, b = k.split("|")
    passed = "not counted" if dl == "5" else f"{v['pass']} of {v['points']}"
    print(f"| {dl} | {b} | {passed} | " + " / ".join(pct(v["mean_fraction"][x]) for x in V) + " |")
print("\n| τ µs | " + " | ".join(f"δ {dl}" for dl in sorted({p['delta_kHz'] for p in pts})) + " |")
print("|---|" + "---|" * len({p["delta_kHz"] for p in pts}))
for tau in (15, 60, 150):
    cells = []
    for dl in sorted({p["delta_kHz"] for p in pts}):
        v = keep["by_tau_and_delta"].get(f"{tau}|{dl}")
        cells.append("" if v is None else ("not counted" if not v["counted"] else f"{v['pass']} of {v['points']}"))
    print(f"| {tau} | " + " | ".join(cells) + " |")

print("\n## The full table\n")
print("Fractions of 200 draws, in %: NRS / 2F / NS. Medians over the draws: P's fitted δ, δ's 90% lower bound, P's fitted b. "
      "Edge: draws with b's point fit at an edge. At round 5's six timed points, round 5's generating share is given in brackets.\n")
print("| # | Δ0 kHz | τ µs | δ kHz | b | role | generating | NRS/2F/NS | ≥ 80% | median P δ kHz | median δ lower bound kHz | median P b | edge draws |")
print("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for p in pts:
    f = p["fraction"]
    d = p["draws"]
    ok = "" if p["passes_80"] is None else ("yes" if p["passes_80"] else "**no**")
    old = r5.get(str(p["index"]))
    oldtxt = "" if old is None or old["fraction_generating_verdict"] is None else f" ({pct(old['fraction_generating_verdict'])})"
    print(f"| {p['index']} | {p['Delta0_kHz']} | {p['tau_us']} | {p['delta_kHz']} | {bstr(p['b'])} | {role(p)} | {p['generating_verdict']} | "
          + "/".join(pct(f[v]) for v in V) + f"{oldtxt} | {ok} | {median(x['P_delta_kHz'] for x in d):.1f} | "
          f"{median(x['delta_ci90_kHz'][0] for x in d):.1f} | {median(x['P_b'] for x in d):.2f} | {sum(x['P_b_at_edge'] for x in d)} |")

print("\n## Compact: each cell is NRS / 2F / NS in %, ✓ or ✗ for a counted point at or above 80% or below it\n")
cols = [(D, tau) for D in (40, 55, 75) for tau in (15, 60, 150)]
print("| δ kHz | b | generating | " + " | ".join(f"Δ0 {D}, τ {tau}" for D, tau in cols) + " |")
print("|---|---|---|" + "---|" * len(cols))
for dl, b in sorted({(p["delta_kHz"], p["b"]) for p in pts}, key=lambda z: (z[0], -(z[1] or 1))):
    cells = []
    for D, tau in cols:
        p = next((q for q in pts if q["delta_kHz"] == dl and q["b"] == b and q["Delta0_kHz"] == D and q["tau_us"] == tau), None)
        if p is None:
            cells.append("not run")
            continue
        f = p["fraction"]
        mark = "" if p["passes_80"] is None else (" ✓" if p["passes_80"] else " ✗")
        cells.append("/".join(pct(f[v]) for v in V) + mark)
    p0 = next(q for q in pts if q["delta_kHz"] == dl and q["b"] == b)
    print(f"| {dl} | {bstr(b)} | {p0['generating_verdict']} | " + " | ".join(cells) + " |")

print("\n## Failing counted points, by kind\n")
for k, idx in keep["failing_by_kind"].items():
    print(f"**{k}:** {len(idx)} points\n")
    for p in counted:
        if p["index"] in idx:
            print(f"- #{p['index']} (Δ0 {p['Delta0_kHz']}, τ {p['tau_us']}, δ {p['delta_kHz']}, b {bstr(p['b'])}; {p['generating_verdict']} "
                  f"{pct(p['fraction_generating_verdict'])}%): {kind(p)[0]}")
    print()

print("## Convergence and cost\n")
print(f"starts that failed to converge: {keep['starts_failed']} of {keep['starts_run']}")
print(f"CPU: {keep['cpu_hours']:.1f} h over the points written; {keep['cpu_seconds_per_draw_mean']:.2f} CPU-s per draw")
