# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""The two-quadrature Ramsey's fit and the copies check (Amendment A25, finding 28): manacitra.wait.ramsey_xy_fit on
fringes with stated lines, on one line at the run's shot counts, and on the Nyquist alias; manacitra.wait.copies_check
on copies from one binomial and from two. The circuits and the checks on test 7's own counts are in test_wait.py. Kept
in a file of its own: the check on one line fits 100 draws by the rule's procedure, about three minutes."""

import math
from pathlib import Path

import numpy as np
import pytest

from manacitra import wait


def _two_lines(D0, dl, b, tau, t, ph, c=0.5, A=0.48, phi0=math.pi):
    env = A * np.exp(-t / tau)
    return c + env * (
        b * np.cos(2 * np.pi * (D0 + dl) * t + phi0 + ph) + (1 - b) * np.cos(2 * np.pi * (D0 - dl) * t + phi0 + ph)
    )


def _fringe(p_of, shots, rng=None, copies=2):
    """Counts of the two quadratures at the waits 0 to 63 µs: exact (shots times P(1)) or binomial."""
    t = np.arange(64.0)
    p = np.stack([p_of(t, 0.0), p_of(t, -np.pi / 2)])
    if rng is None:
        return np.broadcast_to(np.round(p * shots), (copies, 2, 64)).astype(int), t
    return rng.binomial(shots, p, size=(copies, 2, 64)), t


def test_the_fit_recovers_two_stated_lines():
    """Amendment A25, 1c (the fit): on an exact two-line fringe at Delta0 48.7 kHz, delta 44.8 kHz, b 0.355 and tau'
    128 µs, P returns them within 0.1 kHz and 0.005, beats S on the held-out waits, and its lines sit inside the band
    of the even waits (125 kHz each, 250 kHz in all)."""
    ones, t = _fringe(lambda t, ph: _two_lines(0.0487, 0.0448, 0.355, 128.0, t, ph), 10**7)
    r = wait.ramsey_xy_fit(t, ones, 10**7, np.arange(0, 64, 2), seeds=(1, 2, 3), n_boot=20)
    q = r["P"]["params"]
    assert q["Delta0_MHz"] == pytest.approx(0.0487, abs=1e-4) and q["delta_MHz"] == pytest.approx(0.0448, abs=1e-4)
    assert q["b"] == pytest.approx(0.355, abs=0.005) and q["tau_prime_us"] == pytest.approx(128.0, rel=0.01)
    assert r["P"]["held_out_error"] < 1e-4 < r["S"]["held_out_error"]
    assert r["band"] == {"spacing_us": 2.0, "nyquist_MHz": 0.25, "Delta0_bound_MHz": 0.125, "delta_bound_MHz": 0.125}
    assert "clauses" not in r
    assert r["fit_waits"] == list(range(0, 64, 2)) and r["held_out_waits"] == list(range(1, 64, 2))


@pytest.mark.slow
def test_one_line_reads_as_no_resolved_split_at_the_runs_shots():
    """Amendment A25, 1c (the fit): on a one-line fringe (delta = 0; Delta 55 kHz, tau 60 µs, the power check's shape),
    at the run's shot counts (two copies of 1,500), P's b interval reaches an edge or its delta interval reaches below
    5 kHz in at least 95 of 100 binomial draws: the power check's NO RESOLVED SPLIT behaviour. The thresholds are passed
    in; the package fixes none. (The bootstrap here has 100 refits per draw, as a stand-in for the rule's 2,000.)"""
    rng = np.random.default_rng(2525)
    hits = 0
    for _ in range(100):
        ones, t = _fringe(lambda t, ph: _two_lines(0.055, 0.0, 0.5, 60.0, t, ph), 1500, rng)
        seeds = [int(x) for x in rng.integers(0, 2**31, 3)]
        r = wait.ramsey_xy_fit(
            t, ones, 1500, np.arange(0, 64, 2), seeds=seeds, n_boot=100, delta_floor_mhz=0.005, b_edges=(0.05, 0.95)
        )
        c = r["clauses"]
        hits += c["b_interval_reaches_an_edge"] or c["delta_lower_bound_below_the_floor"]
        assert set(c) == {
            "delta_lower_bound_above_the_floor",
            "delta_lower_bound_below_the_floor",
            "b_interval_inside_the_edges",
            "b_interval_reaches_an_edge",
        }
    assert hits >= 95


def test_the_band_rejects_the_nyquist_alias():
    """Amendment A25, 1c (the alias): the even waits are 2 µs apart, so a line at f and one at f + 500 kHz are the same
    function on every fitted wait. The band holds P's lines to |f| <= 250 kHz: on a fringe whose upper line sits at
    f + 500 kHz, P puts it at f, inside the band, and the held-out waits, where the two differ, show the alias."""
    f_up, f_lo = 0.0935, 0.0038
    D0, dl = (f_up + 0.5 + f_lo) / 2, (f_up + 0.5 - f_lo) / 2
    band = wait.ramsey_xy_band(np.arange(0, 64, 2))
    assert band["nyquist_MHz"] == 0.25 and abs(D0) + dl > band["nyquist_MHz"] and D0 > band["Delta0_bound_MHz"]
    ones, t = _fringe(lambda t, ph: _two_lines(D0, dl, 0.355, 128.0, t, ph), 10**7)
    r = wait.ramsey_xy_fit(t, ones, 10**7, np.arange(0, 64, 2), seeds=(1, 2, 3), n_boot=10)
    lines = sorted(r["P"]["lines_MHz"])
    assert r["P"]["reach_MHz"] <= 0.25 + 1e-12
    assert lines == pytest.approx([f_lo, f_up], abs=1e-4)
    assert r["P"]["chi2"] < 1e-3 and r["P"]["held_out_error"] > 0.1


def test_the_copies_check():
    """Amendment A25, 1c (the copies check): two copies drawn from one binomial give a sum of z² near its degrees of
    freedom; copies drawn from two different P(1) do not. The package fixes no threshold."""
    rng = np.random.default_rng(28)
    p = rng.uniform(0.1, 0.9, 128)

    def record(p1, p2, n=1500):
        labels, counts = [], []
        for i, (a, b) in enumerate(zip(p1, p2)):
            for copy, pp in ((1, a), (2, b)):
                k = int(rng.binomial(n, pp))
                labels.append({"circuit": "X", "t_requested_us": i, "copy": copy})
                counts.append({"1": k, "0": n - k})
        return labels, counts

    same = wait.copies_check(*record(p, p))
    assert same["dof"] == 128 and abs(same["sum_z2"] - 128) < 4 * math.sqrt(2 * 128)
    moved = wait.copies_check(*record(p, np.clip(p + 0.05, 0, 1)))
    assert moved["sum_z2"] > 4 * moved["dof"]
    row = same["circuits"][0]
    assert row["label"] == {"circuit": "X", "t_requested_us": 0} and row["copies"] == [1, 2]
    with pytest.raises(ValueError, match="exactly two copies"):
        wait.copies_check([{"circuit": "X", "copy": 1}], [{"1": 1, "0": 1}])


def test_the_telegraph_fit_inside_and_outside_the_band():
    """Finding 28's check after the data on its telegraph diagnostic (a test helper's fit, not the package's): from
    each of 40 other draws of its 20 random starts (seeds 1 to 40), beside the rule's 20 grid starts, the telegraph
    model held inside the band P is held to returns the run's fit, gamma at zero; with its own wider bounds, 19 of the
    40 reach a lower chi-square with its lines outside the band, where gamma, about 0.012 per µs, stands in for the
    decay and the held-out error is 0.18 to 0.20. The finding quotes these numbers."""
    import _reuse_runs as R

    from manacitra import archive

    rec = archive.load("ibm_fez/t7-ramsey-xy.json")
    ones, n, tq, _ = R._t7_counts(rec)
    nn = n.sum(0)
    yq = ones.sum(0) / nn
    E, O = np.arange(0, 64, 2), np.arange(1, 64, 2)
    ph = np.array([0.0, -np.pi / 2])[:, None] * np.ones((2, 64))

    def stack(a, i):
        return np.concatenate([a[0][i], a[1][i]])

    te, phe, ye, ne = stack(tq, E), stack(ph, E), stack(yq, E), stack(nn, E)
    to, pho, yo = stack(tq, O), stack(ph, O), stack(yq, O)
    se = np.sqrt(np.clip(ye * (1 - ye), 1 / ne, None) / ne)
    a = rec["archived"]["analysis"]
    sp, ft = a["fits"]["S"]["params"], a["beside"]["1_telegraph_T"]["fit"]
    gd, gg, gx = R.T7_T_GRID
    grid = [
        [sp["c"], sp["A"], sp["tau_us"], sp["Delta_MHz"] + k * d, sp["phi0_rad"], g, d]
        for d in gd
        for k in (0, 1, -1)
        for g in gg
    ]
    grid += [[sp["c"], sp["A"], sp["tau_us"], sp["Delta_MHz"] + sh, sp["phi0_rad"], g, d] for sh, d, g in gx]
    band = ((0, 0, 0.5, -0.125, 0, 0, 0), (1, 1, 1e4, 0.125, 2 * np.pi, 10, 0.125))
    lower, gammas, maes = 0, [], []
    for bounds in (band, R.T7_T_BOUNDS):
        lo, hi = (np.array(b, float) for b in bounds)
        for seed in range(1, 41):
            rng = np.random.default_rng(seed)
            starts = [list(np.clip(x, lo, hi)) for x in grid] + [
                list(lo + (hi - lo) * rng.random(7)) for _ in range(20)
            ]
            f, _ = R._t7_best(R._t7_model_T, starts, bounds, te, phe, ye, se, R.T7_T_NAMES)
            p = f["params"]
            if bounds is band:
                assert f["chi2"] == pytest.approx(ft["chi2"], abs=1e-6) and p["gamma_per_us"] < 1e-12, seed
                assert p["delta_MHz"] == pytest.approx(ft["params"]["delta_MHz"], abs=1e-9)
            elif f["chi2"] < ft["chi2"] - 1:
                lower += 1
                assert abs(p["Delta0_MHz"]) + p["delta_MHz"] > 0.25
                gammas.append(p["gamma_per_us"])
                maes.append(float(np.mean(np.abs(R._t7_model_T(list(p.values()), to, pho) - yo))))
    assert lower == 19
    assert {round(g, 3) for g in gammas} == {0.012}
    assert (f"{min(maes):.2f}", f"{max(maes):.2f}") == ("0.18", "0.20")
    item = " ".join((Path(__file__).resolve().parents[1] / "docs" / "findings.md").read_text().split())
    assert (
        "held inside the band P is held to, the telegraph model returns the same fit from each of 40 other draws of "
        "its random starts; with its own wider bounds, 19 of those 40 draws reach a lower χ² with its lines outside "
        "that band, where γ, about 0.012 per µs, stands in for the decay and the held-out error is 0.18 to "
        "0.20." in item
    )
