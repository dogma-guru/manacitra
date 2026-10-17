"""Test 7, version 5.1 (desk): the power check of the hardware design, under ruling R5.

The kickoff (tests/t7-steady-or-switching-143/kickoff-t7-steady-or-switching-v5.1-DRAFT-2026-10-16.md, its desk power
check section only) fixes the models, the grid, the starts, the rule, the keep criterion and the order of the run. This
script is round 5's, tests/handback/t7v5/power_t7v5.py, SHA-256
bbc06e8c9affbef702cda4bd468a5e7ca98494196dfde490368a15bf8271385b (the script round 5 ran; its folder verifies), with
what version 5.1 changes, each change stated here before any number was computed, and nothing else:

A. P's bounds: Delta0 in [-0.125, 0.125] MHz and delta in [0, 0.125] MHz (round 5: [-0.3, 0.3] and [0, 0.3]), so that
   |Delta0| + delta stays at or below 0.25 MHz, the band the even-microsecond fit set can tell apart; c, A, tau', phi0
   and b bounded as before (c, A in [0, 1]; tau' in [0.5, 1e4] us; phi0 in [0, 2 pi]; b in [0, 1]). S's bounds are
   unchanged (Delta in [-0.3, 0.3] MHz). No fold of a fitted line into the band: the bound replaces the fold. P's random
   starts are drawn uniform within the new bounds; a grid start beyond them is held at the bound, as in round 5. All 800
   starts of the P reference lie inside the new bounds (Delta0 within +-120 kHz, delta at most 70 kHz), so the
   reference is unchanged.
B. The rule's weight clauses. b's 90% interval "reaches an edge" when its lower bound is at or below 0.05 or its upper
   bound at or above 0.95. NO RESOLVED SPLIT: S's held-out error is within 0.01 of P's or smaller, and either delta's
   90% lower bound is below 5 kHz or b's interval reaches an edge. TWO FIXED FREQUENCIES: P's held-out error beats S's by
   more than 0.01, delta's 90% lower bound is above 5 kHz, and b's interval lies inside (0.05, 0.95) (lower bound above
   0.05 and upper bound below 0.95). NOT SETTLED otherwise. The intervals are the 5th and 95th percentiles of the 200
   refits.
C. The bootstrap, confirmed unchanged: round 5's script already draws the copies with replacement per wait and per
   quadrature (one pick for each copy slot, quadrature and wait), then redraws each copy's shots, then refits P jointly
   over both quadratures, warm-started from the draw's P fit. Version 5.1 fixes that reading; no line of it changes.
D. The seed root: SeedSequence([7676, point index, draw index]) (round 5: 7575); the order of use within a draw is
   unchanged (simulation, S's random starts, P's random starts, the bootstrap). The beside fits use [7676, 9000, run].
E. Records, for reporting only (no verdict reads them): each draw also records P's two fitted lines, whether P's point
   fit lies outside the band (|Delta0| + delta above 250 kHz; the bound forbids it), whether it presses against the band
   (|Delta0| + delta within 1 kHz of 250 kHz), whether b's point fit is at an edge (below 0.05 or above 0.95, round 5's
   reading of the edge) and whether b's interval reaches an edge. The fit check also records each P fit's Delta0, delta
   and b (the 40-start fit and the reference) and counts the 40-start P fits within 1 kHz of 250 kHz. The timing also
   counts, over the six points, the draws whose best P fit lies outside the band, and the NOT SETTLED fraction at its
   delta = 0 point.
F. Names: the stage outputs are fitcheck-t7v51.json, timing-t7v51.json, results-t7v51.jsonl, grid-run-t7v51.json and
   beside-t7v51.json; the beside fits are set beside rounds 2 to 4's telegraph fits (t7v2, t7v3, t7v4) and round 5's S
   and P fits (t7v5), read only.

Carried unchanged from round 5's script, as the kickoff and R5 fix them:
- The design: 64 waits, 0 to 63 us in steps of 1 us; X (H, wait, H) and Y (H, wait, S-dagger, H); two copies of 1,500
  shots per wait and quadrature. In the models Y is X with sin in place of cos, written as the cosine's phase minus pi/2,
  so model_S of tests/handback/t7/pretest_t7.py (imported unchanged, its SHA-256 checked against t7's SHA256SUMS, no
  bytecode written) serves both quadratures with ph = 0 for X and -pi/2 for Y. S and P are fitted jointly over both
  quadratures on the even microseconds (64 points); the held-out error is the mean absolute error over the 64
  odd-microsecond points.
- The models: S (five parameters) by pretest_t7.fit; P = c + A e^{-t/tau'} [b cos(2 pi (Delta0 + delta) t + phi0 + ph) +
  (1 - b) cos(2 pi (Delta0 - delta) t + phi0 + ph)], seven parameters, by this script's fit_P, written as the pre-test's
  fit is (weighted least squares on the binomial standard error with p floored at 1/n, least_squares from each start,
  max_nfev 4,000, the best kept). The telegraph model is not fitted.
- The starts: S, 40 uniform within S's bounds. P, 20 grid starts with c, A, tau' and phi0 from the S fit and (Delta0,
  delta, b) from Delta0 in {Delta_S, Delta_S + delta_s, Delta_S - delta_s}, delta_s in {5, 15, 50} kHz, b in {0.5, 0.3}
  (eighteen), plus (Delta_S, 8 kHz, 0.5) and (Delta_S, 30 kHz, 0.5); and 20 uniform within P's bounds.
- The grid: Delta0 in {40, 55, 75} kHz; tau in {15, 60, 150} us; delta in {0, 3, 5, 8, 11, 15, 30, 50} kHz; b in
  {0.5, 0.37} where delta > 0; the shape c = 0.50, A = 0.48, phi0 = pi; 135 points; S generating at delta = 0, P
  otherwise. The point index counts the grid in the order Delta0, tau, delta, b, each as listed (b = 0.5 before 0.37).
- The generating verdicts: NO RESOLVED SPLIT at delta = 0 and 3 kHz; TWO FIXED FREQUENCIES at 8 kHz and above;
  delta = 5 kHz is the boundary ("either", not counted). The keep criterion: the generating verdict in at least 80% of
  draws at 88 or more of the 117 counted points.
- 200 draws per point; 200 refits per draw.
- The fit check: every (Delta0, delta) of the grid at tau = 60 us and b = 0.5 (24 pairs), ten draws each with the grid's
  own seeds; the 40-start S and P fits against references of 244 S starts (tau in {5, 15, 50, 300} us x Delta in 61
  values from -150 to 150 kHz; c = A = 0.5, phi0 = pi) and 800 P starts (tau' in {20, 300} us x Delta0 in 25 values from
  -120 to 120 kHz x b in {0.2, 0.4, 0.6, 0.8} x delta in {5, 20, 40, 70} kHz; c = A = 0.5, phi0 = pi). A fit misses
  when its chi-square exceeds the reference's by more than 1; the stop line is more than 5% of the 480 fits missed
  (recorded per model as well).
- The six timing points: (Delta0, tau, delta, b) = (55, 60, 0, -), (40, 150, 50, 0.5), (75, 15, 30, 0.37),
  (55, 150, 3, 0.37), (40, 60, 11, 0.5), (75, 15, 8, 0.5). The projection is the mean seconds per draw over the six,
  times 27,000 draws, divided by the 10 workers; the line is twelve hours.
- The grid stage: the 117 counted points first, then the 18 boundary points, each in index order; one JSON line per
  point with its per-draw records; on a start it reads results-t7v51.jsonl, drops a last line that does not parse
  (recorded), and skips the points written; it stops itself, terminating its workers, when twelve hours have passed
  since the first grid start recorded in grid-run-t7v51.json.
- The beside fits: S and P (the starts above, P under the new bounds) fitted to each archived run alone, one quadrature
  (the archive holds X only), after recomputing the runs from the counts.
- The convergence record (least_squares status 0 or an exception counts as a start that failed to converge); one thread
  per worker process; 10 workers.

Stages: `fitcheck`, then `time`, then `grid` (under nohup; an optional second argument names the reason for a start),
then `beside`.

Usage:  MANACITRA_REPO=<checkout at 9b260fb> python power_t7v51.py fitcheck|time|grid ["reason"]|beside
"""

from __future__ import annotations

import os

for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(v, "1")

import hashlib  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from multiprocessing import get_context  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import scipy.optimize as _so  # noqa: E402

sys.dont_write_bytecode = True  # nothing is written into the t7 hand-back folder
HERE = Path(__file__).resolve().parent
T7 = HERE.parent / "t7"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


recorded = dict(line.split()[::-1] for line in (T7 / "SHA256SUMS").read_text().splitlines() if line.strip())
if sha(T7 / "pretest_t7.py") != recorded["pretest_t7.py"]:
    sys.exit("pretest_t7.py differs from test 7's hand-back")
sys.path.insert(0, str(T7))
import pretest_t7 as pt  # noqa: E402  the pre-test's S model, bounds and fit, unchanged

# ---- convergence record: pt.fit calls pt.least_squares; wrap it to record each call's status (the fit is unchanged)
STATUS: list = []


def _recording_least_squares(*a, **k):
    try:
        r = _so.least_squares(*a, **k)
    except (ValueError, FloatingPointError):
        STATUS.append("exception")
        raise
    STATUS.append(int(r.status))
    return r


pt.least_squares = _recording_least_squares

SEED = 7676
ROUND5_SCRIPT_SHA256 = "bbc06e8c9affbef702cda4bd468a5e7ca98494196dfde490368a15bf8271385b"
GRID = {
    "Delta0_kHz": (40, 55, 75),
    "tau_us": (15, 60, 150),
    "delta_kHz": (0, 3, 5, 8, 11, 15, 30, 50),
    "b": (0.5, 0.37),
}
SHAPE = {"c": 0.50, "A": 0.48, "phi0": math.pi}
WAITS = np.arange(64) * 1.0  # 0 to 63 us in steps of 1 us
EVEN, ODD = WAITS[0::2], WAITS[1::2]
QUAD_PH = (0.0, -math.pi / 2)  # X, Y: Y is X with sin, the cosine's phase minus pi/2
COPIES, SHOTS = 2, 1500
N_DRAWS, N_REFITS = 200, 200
N_S_STARTS, N_P_RANDOM = 40, 20
P_GRID_DELTA = (0.005, 0.015, 0.05)  # MHz, delta_s
P_GRID_B = (0.5, 0.3)
P_GRID_EXTRA = ((0.008, 0.5), (0.030, 0.5))  # (delta, b) at Delta_S
DELTA_LINE, MARGIN = 0.005, 0.01
B_EDGE = (0.05, 0.95)  # b's interval reaches an edge at or beyond these (version 5.1)
BAND_MHz, BAND_PRESS_MHz = 0.25, 0.001  # the fit set's band; within 1 kHz of it counts as pressed
VERDICTS = ("NO RESOLVED SPLIT", "TWO FIXED FREQUENCIES", "NOT SETTLED")
WORKERS = 10
LINE_HOURS = 12.0
N_GRID_DRAWS = 135 * N_DRAWS  # 27,000
TIMING_POINTS = (
    {"Delta0_kHz": 55, "tau_us": 60, "delta_kHz": 0, "b": None},
    {"Delta0_kHz": 40, "tau_us": 150, "delta_kHz": 50, "b": 0.5},
    {"Delta0_kHz": 75, "tau_us": 15, "delta_kHz": 30, "b": 0.37},
    {"Delta0_kHz": 55, "tau_us": 150, "delta_kHz": 3, "b": 0.37},
    {"Delta0_kHz": 40, "tau_us": 60, "delta_kHz": 11, "b": 0.5},
    {"Delta0_kHz": 75, "tau_us": 15, "delta_kHz": 8, "b": 0.5},
)

# ---- the P model and its bounds (version 5.1's bounds; written here because pretest_t7.fit knows only S and T)
NAMES_P = ["c", "A", "tau_prime_us", "Delta0_MHz", "phi0_rad", "delta_MHz", "b"]
BOUNDS_P = ([pt.BOUNDS["S"][0][0], pt.BOUNDS["S"][0][1], pt.BOUNDS["S"][0][2], -0.125, pt.BOUNDS["S"][0][4], 0.0, 0.0],
            [pt.BOUNDS["S"][1][0], pt.BOUNDS["S"][1][1], pt.BOUNDS["S"][1][2], 0.125, pt.BOUNDS["S"][1][4], 0.125, 1.0])


def model_P(p, t, ph):
    c, A, tau, D, p0, dl, b = p
    env = A * np.exp(-t / tau)
    return c + env * (b * np.cos(2 * np.pi * (D + dl) * t + p0 + ph) + (1 - b) * np.cos(2 * np.pi * (D - dl) * t + p0 + ph))


def band_record(q):
    """P's two fitted lines and where they sit against the fit set's band (reporting only; no verdict reads it)."""
    D, dl, b = q["Delta0_MHz"], q["delta_MHz"], q["b"]
    reach = abs(D) + dl
    return {"P_lines_kHz": [(D + dl) * 1e3, (D - dl) * 1e3], "P_reach_kHz": reach * 1e3,
            "P_outside_band": bool(reach > BAND_MHz + 1e-12), "P_presses_band": bool(reach >= BAND_MHz - BAND_PRESS_MHz),
            "P_b_at_edge": bool(b < B_EDGE[0] or b > B_EDGE[1])}


def fit_P(t, ph, y, sig, starts):
    """P by weighted least squares from each start, the best kept: the pre-test's fit, for the P model."""
    best = None
    for p in starts:
        try:
            r = _recording_least_squares(lambda q: (model_P(q, t, ph) - y) / sig, p, bounds=BOUNDS_P, max_nfev=4000)
        except (ValueError, FloatingPointError):
            continue
        if best is None or r.cost < best.cost:
            best = r
    n, k = len(y), len(best.x)
    chi2 = float(2 * best.cost)
    return {"params": dict(zip(NAMES_P, [float(v) for v in best.x])), "chi2": chi2, "n_points": n, "dof": n - k,
            "chi2_per_dof": chi2 / (n - k) if n > k else None, "n_starts": len(starts)}


def grid_points():
    out = []
    for D in GRID["Delta0_kHz"]:
        for tau in GRID["tau_us"]:
            for dl in GRID["delta_kHz"]:
                for b in ((None,) if dl == 0 else GRID["b"]):
                    out.append({"Delta0_kHz": D, "tau_us": tau, "delta_kHz": dl, "b": b})
    return out


def classify(gp):
    """The point's role in the keep criterion, as the kickoff fixes it."""
    dl = gp["delta_kHz"]
    if dl == 5:
        return {"boundary": True, "generating_verdict": "either", "counted": False}
    gen = "NO RESOLVED SPLIT" if dl in (0, 3) else "TWO FIXED FREQUENCIES"
    return {"boundary": False, "generating_verdict": gen, "counted": True}


def true_curve(gp, t, ph):
    D, tau, dl = gp["Delta0_kHz"] / 1e3, gp["tau_us"], gp["delta_kHz"] / 1e3
    if dl == 0:
        return pt.model_S([SHAPE["c"], SHAPE["A"], tau, D, SHAPE["phi0"]], t, ph)
    return model_P([SHAPE["c"], SHAPE["A"], tau, D, SHAPE["phi0"], dl, gp["b"]], t, ph)


def sigma(y, n):
    return np.sqrt(np.clip(y * (1 - y), 1 / n, None) / n)


def uniform_starts(bounds, k, rng):
    lo, hi = (np.array(b, float) for b in bounds)
    return [list(lo + (hi - lo) * rng.random(len(lo))) for _ in range(k)]


def p_grid_starts(s):
    """Version 5's twenty P grid starts from S's fitted parameters s."""
    D = s["Delta_MHz"]
    out = [[s["c"], s["A"], s["tau_us"], D + k * d, s["phi0_rad"], d, bb] for d in P_GRID_DELTA for k in (0, 1, -1) for bb in P_GRID_B]
    out += [[s["c"], s["A"], s["tau_us"], D, s["phi0_rad"], d, bb] for d, bb in P_GRID_EXTRA]
    lo, hi = (np.array(b, float) for b in BOUNDS_P)
    return [list(np.clip(x, lo, hi)) for x in out]


def fit_S(t, ph, y, sig, rng):
    pt.STARTS = {**pt.STARTS, "S": uniform_starts(pt.BOUNDS["S"], N_S_STARTS, rng)}
    k0 = len(STATUS)
    f = pt.fit("S", t, ph, y, sig)
    f.pop("residuals_in_sigma", None)
    return f, STATUS[k0:]


def fit_P_v51(t, ph, y, sig, fs, rng, starts=None):
    k0 = len(STATUS)
    st = starts if starts is not None else p_grid_starts(fs["params"]) + uniform_starts(BOUNDS_P, N_P_RANDOM, rng)
    f = fit_P(t, ph, y, sig, st)
    return f, STATUS[k0:]


def stack(yq, idx):
    """Both quadratures' points at the wait indices idx: t, ph and y, X first."""
    t = np.concatenate([WAITS[idx], WAITS[idx]])
    ph = np.concatenate([np.full(len(idx), QUAD_PH[0]), np.full(len(idx), QUAD_PH[1])])
    return t, ph, np.concatenate([yq[0][idx], yq[1][idx]])


EVEN_IDX, ODD_IDX = np.arange(0, 64, 2), np.arange(1, 64, 2)


def simulate(gp, rng):
    P = np.stack([true_curve(gp, WAITS, QUAD_PH[0]), true_curve(gp, WAITS, QUAD_PH[1])])  # (quadrature, wait)
    ones = rng.binomial(SHOTS, P, size=(COPIES, 2, len(WAITS)))  # (copy, quadrature, wait)
    return ones, ones.sum(0) / (COPIES * SHOTS)


def one_draw(task):
    """One simulated hardware run at one grid point: the S and P fits, the held-out errors, 200 warm refits of P, the
    verdict."""
    pi, di, gp = task
    t0 = time.perf_counter()
    rng = np.random.default_rng(np.random.SeedSequence([SEED, pi, di]))
    ones, y = simulate(gp, rng)
    n = COPIES * SHOTS
    te, phe, ye = stack(y, EVEN_IDX)
    to, pho, yo = stack(y, ODD_IDX)
    se = sigma(ye, n)
    fs, st_s = fit_S(te, phe, ye, se, rng)
    fp, st_p = fit_P_v51(te, phe, ye, se, fs, rng)
    mae_s = float(np.mean(np.abs(pt.model_S(list(fs["params"].values()), to, pho) - yo)))
    mae_p = float(np.mean(np.abs(model_P(list(fp["params"].values()), to, pho) - yo)))
    x0 = list(fp["params"].values())
    ones_e = ones[:, :, EVEN_IDX]  # (copy, quadrature, even wait)
    dls, bs, st_r = np.empty(N_REFITS), np.empty(N_REFITS), []
    for k in range(N_REFITS):
        pick = rng.integers(0, COPIES, size=ones_e.shape)
        src = np.take_along_axis(ones_e, pick, axis=0) / SHOTS
        yb = rng.binomial(SHOTS, src).sum(0) / n  # (quadrature, even wait)
        yb = np.concatenate([yb[0], yb[1]])
        sb = sigma(yb, n)
        try:
            r = _so.least_squares(lambda q: (model_P(q, te, phe) - yb) / sb, x0, bounds=BOUNDS_P, max_nfev=4000)
            st_r.append(int(r.status))
            dls[k], bs[k] = r.x[5], r.x[6]
        except (ValueError, FloatingPointError):
            st_r.append("exception")
            dls[k], bs[k] = np.nan, np.nan
    ok = ~np.isnan(dls)
    d_lo, d_hi = (float(v) for v in np.percentile(dls[ok], [5, 95]))
    b_lo, b_hi = (float(v) for v in np.percentile(bs[ok], [5, 95]))
    b_reaches_edge = b_lo <= B_EDGE[0] or b_hi >= B_EDGE[1]
    if mae_s <= mae_p + MARGIN and (d_lo < DELTA_LINE or b_reaches_edge):
        v = "NO RESOLVED SPLIT"
    elif mae_p < mae_s - MARGIN and d_lo > DELTA_LINE and B_EDGE[0] < b_lo and b_hi < B_EDGE[1]:
        v = "TWO FIXED FREQUENCIES"
    else:
        v = "NOT SETTLED"
    band = band_record(fp["params"])

    def failed(sts):
        return sum(1 for s in sts if s == "exception" or (isinstance(s, int) and s <= 0))

    return {
        "point": pi,
        "draw": di,
        "verdict": v,
        "mae_S": mae_s,
        "mae_P": mae_p,
        "chi2_S": fs["chi2"],
        "chi2_P": fp["chi2"],
        "S_Delta_kHz": fs["params"]["Delta_MHz"] * 1e3,
        "S_tau_us": fs["params"]["tau_us"],
        "P_Delta0_kHz": fp["params"]["Delta0_MHz"] * 1e3,
        "P_delta_kHz": fp["params"]["delta_MHz"] * 1e3,
        "P_b": fp["params"]["b"],
        "P_tau_prime_us": fp["params"]["tau_prime_us"],
        "delta_ci90_kHz": [d_lo * 1e3, d_hi * 1e3],
        "b_ci90": [b_lo, b_hi],
        "b_ci90_reaches_edge": bool(b_reaches_edge),
        **band,
        "starts_failed": {"S": failed(st_s), "P": failed(st_p), "refits": failed(st_r)},
        "starts_run": {"S": len(st_s), "P": len(st_p), "refits": len(st_r)},
        "seconds": time.perf_counter() - t0,
    }


def summarise_point(gp, rows):
    cls = classify(gp)
    frac = {v: sum(r["verdict"] == v for r in rows) / len(rows) for v in VERDICTS}
    gen = cls["generating_verdict"]
    right = frac.get(gen) if gen in VERDICTS else None
    return {
        **gp,
        **cls,
        "n_draws": len(rows),
        "fraction": frac,
        "fraction_generating_verdict": right,
        "passes_80": None if right is None else right >= 0.8,
        "starts_failed": {k: int(sum(r["starts_failed"][k] for r in rows)) for k in ("S", "P", "refits")},
        "starts_run": {k: int(sum(r["starts_run"][k] for r in rows)) for k in ("S", "P", "refits")},
        "median_mae_S": float(np.median([r["mae_S"] for r in rows])),
        "median_mae_P": float(np.median([r["mae_P"] for r in rows])),
        "cpu_seconds": float(sum(r["seconds"] for r in rows)),
    }


def run_tasks(tasks, fn=None, workers=WORKERS):
    ctx = get_context("spawn")
    with ctx.Pool(workers) as pool:
        return list(pool.imap_unordered(fn or one_draw, tasks, chunksize=4))


def versions():
    import numpy
    import qiskit
    import scipy

    return {"python": sys.version.split()[0], "numpy": numpy.__version__, "scipy": scipy.__version__,
            "qiskit": qiskit.__version__, "manacitra": getattr(pt.manacitra, "__version__", "?")}


def meta(stage):
    return {
        "test": "t7 v5.1, the desk power check",
        "stage": stage,
        "kickoff": "tests/t7-steady-or-switching-143/kickoff-t7-steady-or-switching-v5.1-DRAFT-2026-10-16.md",
        "ruling": "tests/handback/desk-tests-ruling-R5-2026-10-16.md",
        "derived_from": {"file": "tests/handback/t7v5/power_t7v5.py", "sha256": ROUND5_SCRIPT_SHA256},
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "script_sha256": sha(Path(__file__)),
        "fit_script": {"file": "tests/handback/t7/pretest_t7.py", "sha256": sha(T7 / "pretest_t7.py"), "matches_t7_SHA256SUMS": True},
        "repository_commit": pt.head,
        "versions": versions(),
        "grid": GRID, "shape": SHAPE,
        "design": {"waits_us": [0, 63, 1], "quadratures": ["X", "Y"], "fit": "even us, both quadratures (64 points)",
                   "held_out": "odd us, both quadratures (64 points)", "copies": COPIES, "shots": SHOTS},
        "draws_per_point": N_DRAWS, "refits_per_draw": N_REFITS, "seed_root": SEED, "workers": WORKERS,
        "bounds": {"S": pt.BOUNDS["S"], "P": BOUNDS_P, "names": {"S": pt.NAMES["S"], "P": NAMES_P}},
        "rule": {"NO RESOLVED SPLIT": "mae_S <= mae_P + 0.01 and (delta_lo < 5 kHz or b_lo <= 0.05 or b_hi >= 0.95)",
                 "TWO FIXED FREQUENCIES": "mae_P < mae_S - 0.01 and delta_lo > 5 kHz and 0.05 < b_lo and b_hi < 0.95",
                 "NOT SETTLED": "otherwise", "intervals": "5th and 95th percentiles of the 200 refits"},
        "starts": {"S": f"{N_S_STARTS} uniform within S's bounds",
                   "P": "20 grid (c, A, tau', phi0 from the S fit; Delta0 in {Delta_S, Delta_S +- delta_s}, delta_s in {5, 15, 50} kHz, "
                        "b in {0.5, 0.3}; plus (Delta_S, 8 kHz, 0.5) and (Delta_S, 30 kHz, 0.5)) + 20 uniform within P's bounds"},
    }


# ---- the fit check: version 5.1's 40-start fits against 244-start S and 800-start P references
REF_S = [[0.5, 0.5, tau, D, np.pi] for tau in (5, 15, 50, 300) for D in np.linspace(-0.15, 0.15, 61)]
REF_P = [[0.5, 0.5, tau, D, np.pi, dl, b] for tau in (20, 300) for D in np.linspace(-0.12, 0.12, 25)
         for b in (0.2, 0.4, 0.6, 0.8) for dl in (0.005, 0.02, 0.04, 0.07)]
FITCHECK_POINTS = tuple(
    {"Delta0_kHz": D, "tau_us": 60, "delta_kHz": dl, "b": None if dl == 0 else 0.5}
    for D in GRID["Delta0_kHz"]
    for dl in GRID["delta_kHz"]
)
FITCHECK_DRAWS = 10
FITCHECK_LINE = 1.0
FITCHECK_STOP = 0.05


def check_draw(task):
    pi, di, gp = task
    rng = np.random.default_rng(np.random.SeedSequence([SEED, pi, di]))
    ones, y = simulate(gp, rng)
    n = COPIES * SHOTS
    te, phe, ye = stack(y, EVEN_IDX)
    se = sigma(ye, n)
    fs, _ = fit_S(te, phe, ye, se, rng)
    fp, _ = fit_P_v51(te, phe, ye, se, fs, rng)
    pt.STARTS = {**pt.STARTS, "S": REF_S}
    rs = pt.fit("S", te, phe, ye, se)
    rp = fit_P(te, phe, ye, se, REF_P)
    def lands(f):
        q = f["params"]
        return {"Delta0_kHz": q["Delta0_MHz"] * 1e3, "delta_kHz": q["delta_MHz"] * 1e3, "b": q["b"],
                "reach_kHz": (abs(q["Delta0_MHz"]) + q["delta_MHz"]) * 1e3}

    return {"point": pi, "draw": di, "chi2_S_v51": fs["chi2"], "chi2_S_244": rs["chi2"], "chi2_P_v51": fp["chi2"],
            "chi2_P_800": rp["chi2"], "S_worse_by": fs["chi2"] - rs["chi2"], "P_worse_by": fp["chi2"] - rp["chi2"],
            "P_v51": lands(fp), "P_800": lands(rp)}


def stage_fitcheck():
    pts = grid_points()
    tasks = [(pts.index(gp), d, gp) for gp in FITCHECK_POINTS for d in range(FITCHECK_DRAWS)]
    t0 = time.time()
    rows = run_tasks(tasks, check_draw)
    rows.sort(key=lambda r: (r["point"], r["draw"]))
    per, misses = {}, []
    for gp in FITCHECK_POINTS:
        pi = pts.index(gp)
        rr = [r for r in rows if r["point"] == pi]
        per[str(pi)] = {"point": gp, "n": len(rr), "S_missed": sum(r["S_worse_by"] > FITCHECK_LINE for r in rr),
                        "P_missed": sum(r["P_worse_by"] > FITCHECK_LINE for r in rr),
                        "S_worse_by_max": max(r["S_worse_by"] for r in rr), "P_worse_by_max": max(r["P_worse_by"] for r in rr)}
        for r in rr:
            for m in ("S", "P"):
                if r[f"{m}_worse_by"] > FITCHECK_LINE:
                    misses.append({"point": pi, "draw": r["draw"], "model": m, "worse_by": r[f"{m}_worse_by"]})
    s_m, p_m, n = sum(v["S_missed"] for v in per.values()), sum(v["P_missed"] for v in per.values()), len(rows)
    edge_kHz = (BAND_MHz - BAND_PRESS_MHz) * 1e3
    pressed = [{"point": r["point"], "draw": r["draw"], **r["P_v51"]} for r in rows if r["P_v51"]["reach_kHz"] >= edge_kHz]
    pressed_ref = sum(r["P_800"]["reach_kHz"] >= edge_kHz for r in rows)
    out = {"meta": meta("fitcheck"), "wall_seconds": time.time() - t0, "line_chi2": FITCHECK_LINE, "stop_line": FITCHECK_STOP,
           "draws_per_point": FITCHECK_DRAWS, "n_draws": n, "n_fits": 2 * n,
           "S_missed": s_m, "P_missed": p_m, "missed": s_m + p_m, "missed_fraction": (s_m + p_m) / (2 * n),
           "S_missed_fraction": s_m / n, "P_missed_fraction": p_m / n,
           "tripped": (s_m + p_m) / (2 * n) > FITCHECK_STOP,
           "tripped_if_read_per_model": max(s_m, p_m) / n > FITCHECK_STOP,
           "every_miss": misses,
           "P_fits_within_1_kHz_of_250_kHz": len(pressed), "of_P_fits": n, "pressed_fits": pressed,
           "P_reference_fits_within_1_kHz_of_250_kHz": pressed_ref,
           "P_reach_kHz_max": max(r["P_v51"]["reach_kHz"] for r in rows),
           "per_point": per, "rows": rows,
           "references": {"S": "244: tau in {5, 15, 50, 300} us x Delta in linspace(-150, 150 kHz, 61); c = A = 0.5, phi0 = pi",
                          "P": "800: tau' in {20, 300} us x Delta0 in linspace(-120, 120 kHz, 25) x b in {0.2, 0.4, 0.6, 0.8} x "
                               "delta in {5, 20, 40, 70} kHz; c = A = 0.5, phi0 = pi (the runner's layout; round 3's with b for gamma)"},
           "note": "the grid's own draws (same seeds); version 5.1's 40-start fits against the references, under the new P bounds"}
    (HERE / "fitcheck-t7v51.json").write_text(json.dumps(out, indent=1))
    return out


def stage_time():
    fc = json.loads((HERE / "fitcheck-t7v51.json").read_text())
    if fc["tripped"] or fc["tripped_if_read_per_model"]:
        sys.exit("the fit check tripped its line (or would, read per model): stop and report")
    pts = grid_points()
    idx = [pts.index(gp) for gp in TIMING_POINTS]
    t0 = time.time()
    rows = run_tasks([(pi, d, pts[pi]) for pi in idx for d in range(N_DRAWS)])
    wall = time.time() - t0
    per = {}
    for pi in idx:
        rr = sorted([r for r in rows if r["point"] == pi], key=lambda r: r["draw"])
        sp = summarise_point(pts[pi], rr)
        per[str(pi)] = {**sp, "cpu_seconds_per_draw": sp["cpu_seconds"] / N_DRAWS, "draws": rr}
    mean_cpu = float(np.mean([r["seconds"] for r in rows]))
    proj = mean_cpu * N_GRID_DRAWS / WORKERS / 3600
    out = {"meta": meta("time"), "points": per, "wall_seconds_six_points": wall, "cpu_seconds_six_points": float(sum(r["seconds"] for r in rows)),
           "cpu_seconds_per_draw_mean": mean_cpu, "cpu_seconds_per_draw_median": float(np.median([r["seconds"] for r in rows])),
           "cpu_seconds_per_draw_max": float(max(r["seconds"] for r in rows)),
           "grid_draws": N_GRID_DRAWS, "projected_wall_hours_grid": proj,
           "projected_wall_hours_from_wall": wall / len(idx) * len(pts) / 3600,
           "line_hours": LINE_HOURS, "over_the_line": proj > LINE_HOURS,
           "verdict_fractions": {k: v["fraction"] for k, v in per.items()},
           "not_settled_fraction_at_delta_0": next(v["fraction"]["NOT SETTLED"] for v in per.values() if v["delta_kHz"] == 0),
           "draws_P_outside_band": sum(r["P_outside_band"] for r in rows),
           "draws_P_presses_band": sum(r["P_presses_band"] for r in rows),
           "draws_P_b_at_edge": {k: sum(r["P_b_at_edge"] for r in v["draws"]) for k, v in per.items()},
           "draws_b_interval_reaches_edge": {k: sum(r["b_ci90_reaches_edge"] for r in v["draws"]) for k, v in per.items()},
           "note": "seconds per draw are each worker's wall time per draw, as rounds 3 to 5 measured them"}
    (HERE / "timing-t7v51.json").write_text(json.dumps(out, indent=1))
    return out


def grid_order():
    """The counted points first (delta != 5 kHz), then the boundary points, each in index order."""
    pts = grid_points()
    return [i for i, gp in enumerate(pts) if classify(gp)["counted"]] + [i for i, gp in enumerate(pts) if not classify(gp)["counted"]]


def stage_grid():
    tm = json.loads((HERE / "timing-t7v51.json").read_text())
    if tm["over_the_line"]:
        sys.exit("the projection is over the twelve-hour line: stop and report")
    pts = grid_points()
    order = grid_order()
    path = HERE / "results-t7v51.jsonl"
    done, dropped = set(), None
    if path.exists():
        raw = path.read_text()
        lines = [x for x in raw.split("\n") if x.strip()]
        good = []
        for k, x in enumerate(lines):
            try:
                good.append(json.loads(x))
            except json.JSONDecodeError:
                if k == len(lines) - 1:
                    dropped = {"line": k, "length": len(x)}
                else:
                    raise
        if dropped is not None:
            path.write_text("".join(json.dumps(d) + "\n" for d in good))
        done = {d["index"] for d in good}
    log_path = HERE / "grid-run-t7v51.json"
    log = json.loads(log_path.read_text()) if log_path.exists() else {"meta": meta("grid"), "line_hours": LINE_HOURS,
                                                                          "order": order, "runs": []}
    now = time.time()
    first = log["runs"][0]["started_epoch"] if log["runs"] else now
    deadline = first + LINE_HOURS * 3600
    run = {"started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)), "started_epoch": now,
           "reason": sys.argv[2] if len(sys.argv) > 2 else "first start", "script_sha256": sha(Path(__file__)),
           "points_already_written": len(done), "last_line_dropped": dropped}
    log["runs"].append(run)
    log_path.write_text(json.dumps(log, indent=1))
    todo = [pi for pi in order if pi not in done]
    tasks = [(pi, d, pts[pi]) for pi in todo for d in range(N_DRAWS)]
    buf, written, stopped = {}, 0, time.time() > deadline
    if not stopped and tasks:
        pool = get_context("spawn").Pool(WORKERS)
        try:
            for r in pool.imap_unordered(one_draw, tasks, chunksize=4):
                buf.setdefault(r["point"], []).append(r)
                if len(buf[r["point"]]) == N_DRAWS:
                    pi = r["point"]
                    rows = sorted(buf.pop(pi), key=lambda x: x["draw"])
                    line = {"index": pi, **summarise_point(pts[pi], rows),
                            "finished_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "draws": rows}
                    with open(path, "a") as f:
                        f.write(json.dumps(line) + "\n")
                        f.flush()
                        os.fsync(f.fileno())
                    done.add(pi)
                    written += 1
                if time.time() > deadline:
                    stopped = True
                    break
        finally:
            if stopped:
                pool.terminate()
            else:
                pool.close()
            pool.join()
    run.update({"finished_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "wall_seconds": time.time() - now,
                "points_computed_this_run": written, "stopped_at_the_line": stopped, "points_in_flight_discarded": sorted(buf),
                "points_written_total": len(done), "complete": len(done) == len(pts)})
    log["runs"][-1] = run
    log_path.write_text(json.dumps(log, indent=1))
    return run


# ---- the beside fits: each archived run alone (X only), S and P by version 5.1's procedure
def beside_fits():
    Q = "143"
    r47, r48, r49, r52 = pt.load(pt.F47), pt.load(pt.F48), pt.load(pt.F49), pt.load(pt.F52)
    wait, reuse = pt.wait, pt.reuse
    groups47 = [qs for _, qs in sorted(r47["groups"].items(), key=lambda z: int(z[0]))]
    b47 = wait.part_b_losses(r47["labels"], r47["counts"], groups47, r47["taus_us"], reference=3.4,
                             seed=r47["fixed_before_the_data"]["bootstrap"]["seed_B"], wait_key="tau_us")

    def part_b_dt(rec):
        m = rec["meta"]
        w = list(m["waits_dt"])
        dt = m["T_M"]["dt_s"]
        return wait.part_b_losses(rec["labels"], rec["counts"], m["groups"], w, reference=850, seed=m["seeds"]["bootstrap_B"],
                                  wait_key="tau_dt", waits_us=[x * dt * 1e6 for x in w]), w, dt

    b48, w48, dt48 = part_b_dt(r48)
    b49, w49, dt49 = part_b_dt(r49)
    k52 = reuse.k52_phase_sweep(r52)
    _, bits52, _ = reuse._cells_and_bits(r52["labels"], r52["counts"], lambda lab: (str(lab["M"]), lab["circuit"], lab["phi_deg"]))
    ph52 = list(wait.SWEEP_PHASES_DEG)
    recompute = {
        "k47_ramsey_P1_max_abs_difference": pt.maxdiff(b47[Q]["ramsey_P1"], r47["archived"]["analysis"]["part_B"]["qubits"][Q]["ramsey_P1"]),
        "k48_part_B_143_max_abs_difference": pt.maxdiff(b48[Q], r48["archived"]["analysis"]["part_B"][Q]),
        "k49_part_B_143_max_abs_difference": pt.maxdiff(b49[Q], r49["archived"]["analysis"]["part_B"][Q]),
        "k52_per_M_143_max_abs_difference": pt.maxdiff(k52["per_M"][Q], r52["archived"]["analysis"]["per_M"][Q]),
    }
    s47, s48, s49 = pt.ramsey_shots(r47, "tau_us"), pt.ramsey_shots(r48, "tau_dt"), pt.ramsey_shots(r49, "tau_dt")
    t52 = r52["circuits"][Q]["R0|0"]["M_window"]["T_dt"] * r52["meta"]["T_M"]["dt_s"] * 1e6
    runs = {
        "K47": (np.array(r47["taus_us"], float), np.zeros(6), np.array([b47[Q]["ramsey_P1"][str(x)] for x in r47["taus_us"]]),
                np.array([s47[x] for x in r47["taus_us"]], float)),
        "K48": (np.array([x * dt48 * 1e6 for x in w48]), np.zeros(len(w48)), np.array([b48[Q]["ramsey_P1"][str(x)] for x in w48]),
                np.array([s48[x] for x in w48], float)),
        "K49": (np.array([x * dt49 * 1e6 for x in w49]), np.zeros(len(w49)), np.array([b49[Q]["ramsey_P1"][str(x)] for x in w49]),
                np.array([s49[x] for x in w49], float)),
        "K52": (np.full(6, t52), np.radians(ph52), np.array([reuse._p1(bits52, (Q, "R0", p)) for p in ph52]),
                np.array([sum(x[2] for x in bits52[(Q, "R0", p)]) for p in ph52], float)),
    }
    out = {}
    for i, (run, (t, ph, y, n)) in enumerate(runs.items()):
        rng = np.random.default_rng(np.random.SeedSequence([SEED, 9000, i]))
        sig = sigma(y, n)
        fs, _ = fit_S(t, ph, y, sig, rng)
        fp, _ = fit_P_v51(t, ph, y, sig, fs, rng)
        land = {"S": {"abs_Delta_kHz": abs(fs["params"]["Delta_MHz"]) * 1e3, "tau_us": fs["params"]["tau_us"]},
                "P": {"Delta0_kHz": fp["params"]["Delta0_MHz"] * 1e3, "delta_kHz": fp["params"]["delta_MHz"] * 1e3,
                      "b": fp["params"]["b"], "tau_prime_us": fp["params"]["tau_prime_us"]}}
        out[run] = {"n_points": int(len(y)), "S": fs, "P": fp, "lands": land}
    return recompute, out


def stage_beside():
    recompute, beside = beside_fits()
    earlier = {"round 2": ("t7v2", "results-t7v2.json"), "round 3": ("t7v3", "results-t7v3.json"),
               "round 4": ("t7v4", "beside-t7v4.json"), "round 5": ("t7v5", "beside-t7v5.json")}

    def t_lands(f):
        q = f["params"]
        return {"abs_Delta0_kHz": abs(q["Delta0_MHz"]) * 1e3, "delta_kHz": q["delta_MHz"] * 1e3, "gamma_per_us": q["gamma_per_us"],
                "tau_prime_us": q["tau_prime_us"], "chi2": f["chi2"], "dof": f["dof"]}

    def p_lands(f):
        q = f["params"]
        return {"Delta0_kHz": q["Delta0_MHz"] * 1e3, "delta_kHz": q["delta_MHz"] * 1e3, "b": q["b"], "tau_prime_us": q["tau_prime_us"],
                "A": q["A"], "chi2": f["chi2"], "dof": f["dof"]}

    def s_lands(f):
        q = f["params"]
        return {"abs_Delta_kHz": abs(q["Delta_MHz"]) * 1e3, "tau_us": q["tau_us"], "chi2": f["chi2"], "dof": f["dof"]}

    beside_earlier = {}
    for rnd, (folder, name) in earlier.items():
        b = json.loads((HERE.parent / folder / name).read_text())["beside_fits_each_run_alone"]
        beside_earlier[rnd] = {k: {"S": s_lands(v["S"]), **({"T": t_lands(v["T"])} if "T" in v else {}), **({"P": p_lands(v["P"])} if "P" in v else {})}
                               for k, v in b.items()}
    out = {"meta": meta("beside"), "recompute_against_archive": recompute, "beside_fits_each_run_alone": beside,
           "version_51_lands": {k: {"S": s_lands(v["S"]), "P": p_lands(v["P"])} for k, v in beside.items()},
           "earlier_rounds_read_only": beside_earlier,
           "L03_note": "L-03's files carry no fit of these runs of their own; the Kickoff 48 split of 23.7 kHz is rounds 2 to 4's "
                       "telegraph fit, which L-03 reported (the correction R5 records)"}
    (HERE / "beside-t7v51.json").write_text(json.dumps(out, indent=1))
    return out


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else ""
    if stage == "fitcheck":
        r = stage_fitcheck()
        print(json.dumps({k: v for k, v in r.items() if k not in ("rows", "meta")}, indent=1))
    elif stage == "time":
        r = stage_time()
        print(json.dumps({k: (v if k != "points" else {p: {kk: vv for kk, vv in q.items() if kk != "draws"} for p, q in v.items()})
                          for k, v in r.items() if k != "meta"}, indent=1))
    elif stage == "grid":
        r = stage_grid()
        print(json.dumps({k: v for k, v in r.items() if k != "meta"}, indent=1))
    elif stage == "beside":
        r = stage_beside()
        print(json.dumps({k: v for k, v in r.items() if k != "meta"}, indent=1, default=str)[:8000])
    else:
        sys.exit("stage: fitcheck | time | grid | beside")
