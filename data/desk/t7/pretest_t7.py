"""Test 7, the desk pre-test: can the archived Ramsey curves on 143 carry the power check?

The kickoff (tests/t7-steady-or-switching-143/kickoff-t7-steady-or-switching-DRAFT-2026-10-15.md, the desk pre-test
section only) says finding 13's and finding 14's Ramsey curves on 143 (Kickoffs 47 and 48, waits 0 to 16 us) and the
six-phase point at 10.444 us (Kickoff 52) are enough to fit the steady model S and the switching model T once, and
then to simulate both fitted models at the hardware design's waits and shots 1,000 times each and count how often the
draft rule returns the right model.

An exploratory fit, not kept, showed before this script was written that a joint fit of the three runs leaves
residuals far beyond their shot noise under both models; the stop line below (chi-square per degree of freedom below
3) is the runner's, set after seeing that, and the subsets beside are readings after the data. What this script does:
1. recomputes from the counts, with the repository's code, every archived number used: 143's Ramsey P(1) at each
   wait in Kickoffs 47 and 48 (manacitra.wait.part_b_losses, as tests/_reuse_runs.py runs it) and Kickoff 52's
   analysis (tests/_reuse_runs.k52_phase_sweep), and 143's R0 P(1) at the six phases from Kickoff 52's counts;
   Kickoff 49's curve and fit (the 40.4 kHz the kickoff quotes) are recomputed beside;
2. fits S and T once, jointly, to the kickoff's three inputs, as the kickoff says: weighted least squares with the
   binomial standard error of each point (p floored at 1/n), the six-phase point entering through the phase probe
   (the RZ(phi) after M's first H adds phi to the fringe's phase), many starts, the best kept. S: P1 = c + A
   exp(-t/tau) cos(2 pi Delta t + phi0 + phi). T: P1 = c + A exp(-t/tau') g(t) cos(2 pi Delta0 t + phi0 + phi), g the
   kickoff's telegraph factor. t in us, frequencies in MHz, gamma in 1/us;
3. checks whether the three runs are one process: the joint fits' chi-square, and the runs' differences at the waits
   they share.
The power simulation is run only if both joint fits describe the data (chi-square per degree of freedom below 3); if
not, the test stops there, as the runner's prompt orders for a kickoff that is wrong against the data, and nothing is
simulated.

Beside (readings, not the test): the same fits on subsets of the runs (Kickoff 48 alone; 48 with 52; 47 with 48; and,
not among the kickoff's inputs, Kickoff 49 alone and 49 with 52, the two runs of 13 October); and three facts of the
model as written, checked numerically: g depends on delta only through delta squared, g = 1 for every gamma when
delta = 0, and g tends to cos(2 pi delta t) as gamma tends to 0.

Usage:  MANACITRA_REPO=<checkout at 9b260fb> python pretest_t7.py
Writes results-t7.json beside this file. Nothing random (the archive's own bootstraps run with their seeds).
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

HERE = Path(__file__).resolve().parent
REPO = Path(os.environ.get("MANACITRA_REPO", "")).resolve()
COMMIT = "9b260fb5f0537736a3de400eca7cafd043ae815b"
if not (REPO / "src" / "manacitra").is_dir():
    sys.exit("set MANACITRA_REPO to a checkout of the manacitra repository at 9b260fb")
head = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
if head != COMMIT:
    sys.exit(f"the checkout is at {head}, not {COMMIT}")
sys.path.insert(0, str(REPO / "tests"))

import manacitra  # noqa: E402
import _reuse_runs as reuse  # noqa: E402
from manacitra import wait  # noqa: E402

if not Path(manacitra.__file__).resolve().is_relative_to(REPO):
    sys.exit("the manacitra package imported is not the checkout's (install it editable from the checkout)")

F47, F48, F49, F52 = (f"data/ibm_fez/{n}" for n in ("k47-wait.json", "k48-wait-test.json", "k49-wait-test.json", "k52-phase-sweep.json"))
Q = "143"
CHI2_OK = 3.0  # chi-square per degree of freedom below which a joint fit is taken to describe the data


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load(rel: str) -> dict:
    return json.loads((REPO / rel).read_text())


def maxdiff(a, b) -> float:
    if isinstance(a, dict) and isinstance(b, dict):
        ks = set(a) & set(b)
        return max([maxdiff(a[k], b[k]) for k in ks] or [0.0])
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)) and len(a) == len(b):
        return max([maxdiff(x, y) for x, y in zip(a, b)] or [0.0])
    if isinstance(a, bool) or isinstance(b, bool):
        return 0.0 if a == b else float("inf")
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(float(a) - float(b))
    if isinstance(a, str) and isinstance(b, str):
        return 0.0 if a == b else float("inf")
    return 0.0


def ramsey_shots(rec, key):
    out = {}
    for lab, c in zip(rec["labels"], rec["counts"]):
        if lab.get("part") == "B" and lab["variant"] == "R" and lab["group"] == 1:
            out[lab[key]] = out.get(lab[key], 0) + sum(c.values())
    return out


# --------------------------------------------------------------------------- the models
def g_factor(t, gam, dl):
    """The kickoff's telegraph factor e^{-gam t} [cosh(k t) + (gam / k) sinh(k t)], k = sqrt(gam^2 - (2 pi dl)^2),
    written as 0.5 [(1 + gam/k) e^{(k - gam) t} + (1 - gam/k) e^{-(k + gam) t}] for stability; k -> 0 by its limit."""
    t = np.asarray(t, float)
    k = np.sqrt(gam**2 - (2 * np.pi * dl) ** 2 + 0j)
    if abs(k) < 1e-9:
        return np.exp(-gam * t) * (1 + gam * t)
    return np.real(0.5 * ((1 + gam / k) * np.exp((k - gam) * t) + (1 - gam / k) * np.exp(-(k + gam) * t)))


def model_S(p, t, ph):
    c, A, tau, D, p0 = p
    return c + A * np.exp(-t / tau) * np.cos(2 * np.pi * D * t + p0 + ph)


def model_T(p, t, ph):
    c, A, tau, D, p0, gam, dl = p
    return c + A * np.exp(-t / tau) * g_factor(t, gam, dl) * np.cos(2 * np.pi * D * t + p0 + ph)


BOUNDS = {
    "S": ([0, 0, 0.5, -0.3, 0], [1, 1, 1e4, 0.3, 2 * np.pi]),
    "T": ([0, 0, 0.5, -0.3, 0, 0, 0], [1, 1, 1e4, 0.3, 2 * np.pi, 10, 0.3]),
}
STARTS = {
    "S": [[0.5, 0.5, tau, D, np.pi] for tau in (5, 15, 50, 300) for D in np.linspace(-0.15, 0.15, 61)],
    "T": [
        [0.5, 0.5, tau, D, np.pi, g, dl]
        for tau in (20, 300)
        for D in np.linspace(-0.12, 0.12, 25)
        for g in (0.001, 0.01, 0.05, 0.3)
        for dl in (0.005, 0.02, 0.04, 0.07)
    ],
}
NAMES = {"S": ["c", "A", "tau_us", "Delta_MHz", "phi0_rad"], "T": ["c", "A", "tau_prime_us", "Delta0_MHz", "phi0_rad", "gamma_per_us", "delta_MHz"]}


def fit(name, t, ph, y, sig):
    model = model_S if name == "S" else model_T
    best = None
    for p in STARTS[name]:
        try:
            r = least_squares(lambda q: (model(q, t, ph) - y) / sig, p, bounds=BOUNDS[name], max_nfev=4000)
        except (ValueError, FloatingPointError):
            continue
        if best is None or r.cost < best.cost:
            best = r
    n, k = len(y), len(best.x)
    chi2 = float(2 * best.cost)
    return {
        "params": dict(zip(NAMES[name], [float(v) for v in best.x])),
        "chi2": chi2,
        "n_points": n,
        "dof": n - k,
        "chi2_per_dof": chi2 / (n - k) if n > k else None,
        "residuals_in_sigma": [float(v) for v in best.fun],
        "largest_abs_residual_sigma": float(np.max(np.abs(best.fun))),
        "n_starts": len(STARTS[name]),
    }


def main():
    t0 = time.time()
    run_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    r47, r48, r49, r52 = load(F47), load(F48), load(F49), load(F52)

    # ---- 1. recompute
    groups47 = [qs for _, qs in sorted(r47["groups"].items(), key=lambda z: int(z[0]))]
    b47 = wait.part_b_losses(
        r47["labels"], r47["counts"], groups47, r47["taus_us"], reference=3.4,
        seed=r47["fixed_before_the_data"]["bootstrap"]["seed_B"], wait_key="tau_us",
    )
    a47 = r47["archived"]["analysis"]["part_B"]["qubits"][Q]

    def part_b_dt(rec):
        m = rec["meta"]
        w = list(m["waits_dt"])
        dt = m["T_M"]["dt_s"]
        return wait.part_b_losses(
            rec["labels"], rec["counts"], m["groups"], w, reference=850, seed=m["seeds"]["bootstrap_B"],
            wait_key="tau_dt", waits_us=[x * dt * 1e6 for x in w],
        ), w, dt

    b48, w48, dt48 = part_b_dt(r48)
    b49, w49, dt49 = part_b_dt(r49)
    a48, a49 = r48["archived"]["analysis"]["part_B"][Q], r49["archived"]["analysis"]["part_B"][Q]
    k52 = reuse.k52_phase_sweep(r52)
    a52 = r52["archived"]["analysis"]
    _, bits52, _ = reuse._cells_and_bits(r52["labels"], r52["counts"], lambda lab: (str(lab["M"]), lab["circuit"], lab["phi_deg"]))
    ph52 = list(wait.SWEEP_PHASES_DEG)
    y52 = [reuse._p1(bits52, (Q, "R0", p)) for p in ph52]
    n52 = [sum(x[2] for x in bits52[(Q, "R0", p)]) for p in ph52]
    T52_dt = r52["circuits"][Q]["R0|0"]["M_window"]["T_dt"]
    t52 = T52_dt * r52["meta"]["T_M"]["dt_s"] * 1e6
    recompute = {
        "k47_part_B_143_max_abs_difference": maxdiff(b47[Q], {**a47, "r": a47["r_3p4"], "e": a47["e_3p4"]}),
        "k47_ramsey_P1_max_abs_difference": maxdiff(b47[Q]["ramsey_P1"], a47["ramsey_P1"]),
        "k48_part_B_143_max_abs_difference": maxdiff(b48[Q], a48),
        "k49_part_B_143_max_abs_difference": maxdiff(b49[Q], a49),
        "k52_per_M_143_max_abs_difference": maxdiff(k52["per_M"][Q], a52["per_M"][Q]),
        "k52_verdicts": {k: (k52[k], a52[k]) for k in ("H52a", "H52b")},
        "k52_R0_P1_minus_Z_vs_archived_loss_max_abs_difference": max(
            abs(y - k52["per_M"][Q]["P1_Z"] - a52["per_M"][Q]["loss"][f"R0|{p}"]) for y, p in zip(y52, ph52)
        ),
        "k48_ramsey_fit_f_kHz": 1e3 * b48[Q]["ramsey_fit"]["f_MHz"],
        "k48_ramsey_fit_f_err_kHz": 1e3 * b48[Q]["ramsey_fit"]["f_err"],
        "k49_ramsey_fit_f_kHz": 1e3 * b49[Q]["ramsey_fit"]["f_MHz"],
        "k49_ramsey_fit_f_err_kHz": 1e3 * b49[Q]["ramsey_fit"]["f_err"],
    }

    # ---- the data, per run
    s47, s48, s49 = ramsey_shots(r47, "tau_us"), ramsey_shots(r48, "tau_dt"), ramsey_shots(r49, "tau_dt")
    runs = {
        "K47": {"utc": r47["meta"]["utc"], "t_us": [float(x) for x in r47["taus_us"]],
                "phi_deg": [0.0] * 6, "P1": [b47[Q]["ramsey_P1"][str(x)] for x in r47["taus_us"]],
                "shots": [s47[x] for x in r47["taus_us"]]},
        "K48": {"utc": r48["meta"]["utc"], "t_us": [x * dt48 * 1e6 for x in w48], "phi_deg": [0.0] * len(w48),
                "P1": [b48[Q]["ramsey_P1"][str(x)] for x in w48], "shots": [s48[x] for x in w48]},
        "K49": {"utc": r49["meta"]["utc"], "t_us": [x * dt49 * 1e6 for x in w49], "phi_deg": [0.0] * len(w49),
                "P1": [b49[Q]["ramsey_P1"][str(x)] for x in w49], "shots": [s49[x] for x in w49]},
        "K52": {"utc": r52["meta"]["utc"], "t_us": [t52] * 6, "phi_deg": [float(p) for p in ph52], "P1": y52, "shots": n52,
                "instrument": "R0, the idle-neighbour Ramsey over T_M, one RZ(phi) after M's first H", "T_dt": T52_dt},
    }

    def stack(names):
        t = np.concatenate([runs[n]["t_us"] for n in names])
        ph = np.radians(np.concatenate([runs[n]["phi_deg"] for n in names]))
        y = np.concatenate([runs[n]["P1"] for n in names])
        n = np.concatenate([runs[n]["shots"] for n in names]).astype(float)
        sig = np.sqrt(np.clip(y * (1 - y), 1 / n, None) / n)
        return t, ph, y, sig

    # ---- 3. are the runs one process? the shared waits
    def compare(a, b):
        out = {}
        for i, t in enumerate(runs[a]["t_us"]):
            for j, u in enumerate(runs[b]["t_us"]):
                if abs(t - u) < 1e-9 and runs[a]["phi_deg"][i] == runs[b]["phi_deg"][j] == 0.0:
                    pa, pb = runs[a]["P1"][i], runs[b]["P1"][j]
                    se = math.sqrt(pa * (1 - pa) / runs[a]["shots"][i] + pb * (1 - pb) / runs[b]["shots"][j])
                    out[f"{t:g}"] = {a: pa, b: pb, "difference": pa - pb, "z": (pa - pb) / se if se else None}
        return out

    shared = {"K47_vs_K48": compare("K47", "K48"), "K48_vs_K49": compare("K48", "K49"), "K47_vs_K49": compare("K47", "K49")}

    # ---- 2. the kickoff's fit, once, jointly; then the subsets beside
    sets = {
        "joint K47 + K48 + K52 (the kickoff's)": ["K47", "K48", "K52"],
        "K48 alone": ["K48"],
        "K48 + K52": ["K48", "K52"],
        "K47 + K48": ["K47", "K48"],
        "K49 alone (not a kickoff input)": ["K49"],
        "K49 + K52 (not a kickoff input; both 13 October)": ["K49", "K52"],
    }
    fits = {}
    for name, names in sets.items():
        t, ph, y, sig = stack(names)
        fits[name] = {"runs": names, "S": fit("S", t, ph, y, sig), "T": fit("T", t, ph, y, sig)}
    joint = fits["joint K47 + K48 + K52 (the kickoff's)"]
    described = all(joint[m]["chi2_per_dof"] is not None and joint[m]["chi2_per_dof"] < CHI2_OK for m in ("S", "T"))

    # ---- facts of the model as written, checked numerically
    tt = np.linspace(0, 31.5, 64)
    facts = {
        "g_even_in_delta_max_abs_difference": float(max(np.max(np.abs(g_factor(tt, g, d) - g_factor(tt, g, -d))) for g in (0.01, 0.1, 1.0) for d in (0.01, 0.05))),
        "g_equals_1_at_delta_0_max_abs_deviation": float(max(np.max(np.abs(g_factor(tt, g, 0.0) - 1)) for g in (0.001, 0.01, 0.1, 1.0, 5.0))),
        "g_at_gamma_1e-6_minus_cos_2pi_delta_t_max_abs": float(max(np.max(np.abs(g_factor(tt, 1e-6, d) - np.cos(2 * np.pi * d * tt))) for d in (0.01, 0.03, 0.05))),
        "d_g_d_delta_at_delta_0_max_abs": float(max(np.max(np.abs((g_factor(tt, g, 1e-7) - g_factor(tt, g, 0.0)) / 1e-7)) for g in (0.01, 0.1, 1.0))),
    }

    import numpy
    import qiskit
    import scipy

    res = {
        "meta": {
            "test": "t7 desk pre-test, the power check on the archived Ramsey curves of 143",
            "kickoff": "tests/t7-steady-or-switching-143/kickoff-t7-steady-or-switching-DRAFT-2026-10-15.md (desk pre-test section only)",
            "run_utc": run_utc,
            "elapsed_s": None,
            "script_sha256": sha(Path(__file__)),
            "repository_commit": head,
            "inputs": {rel: sha(REPO / rel) for rel in (F47, F48, F49, F52, "tests/_reuse_runs.py", "src/manacitra/wait.py")},
            "versions": {
                "python": sys.version.split()[0],
                "numpy": numpy.__version__,
                "scipy": scipy.__version__,
                "qiskit": qiskit.__version__,
                "manacitra": getattr(manacitra, "__version__", "?"),
            },
            "chi2_per_dof_line": CHI2_OK,
        },
        "recompute_against_archive": recompute,
        "runs_143": runs,
        "shared_waits": shared,
        "fits": fits,
        "joint_fits_describe_the_data": described,
        "power_simulation_run": False,
        "verdict": "STOPPED: the kickoff's inputs are not one process under either model; no power simulation was run"
        if not described else "(the power simulation would follow; not written, the joint fits being required first)",
        "model_facts": facts,
    }
    res["meta"]["elapsed_s"] = round(time.time() - t0, 1)
    (HERE / "results-t7.json").write_text(json.dumps(res, indent=1))
    return res


if __name__ == "__main__":
    r = main()
    print("recompute:", json.dumps(r["recompute_against_archive"], indent=0))
    for n, v in r["runs_143"].items():
        print(n, v["utc"], [round(x, 3) for x in v["t_us"]], [round(x, 4) for x in v["P1"]], v["shots"][:2])
    print("shared:", json.dumps(r["shared_waits"], indent=0))
    for name, f in r["fits"].items():
        for m in ("S", "T"):
            x = f[m]
            print(f"{name} | {m}: chi2 {x['chi2']:.1f} dof {x['dof']} per dof {x['chi2_per_dof']} | "
                  + " ".join(f"{k}={v:.4g}" for k, v in x["params"].items()) + f" | max |res| {x['largest_abs_residual_sigma']:.1f} sigma")
    print("described:", r["joint_fits_describe_the_data"], "|", r["verdict"])
    print("facts:", r["model_facts"])
    print("elapsed", r["meta"]["elapsed_s"])
