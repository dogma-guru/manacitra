"""Mantri's desk check of the test 13 rule (the per-shot read of fez 143's monitor jobs), before the hash.

Readings as the rule fixes them: (a) the equal-index variance ratio with SHARED above 3 and INDEPENDENT below 1.5;
(b) the correlation time of the sweep means, the first lag at which the autocorrelation falls below 1/e of the
excess over independent noise, read only when SHARED and the lag is 3 or more; (c) the scatter ratio.

Three cases, 100 trials each, on a synthetic span of 49 whole repeats at 500 shots (test 12's span 0):
  1 independent: every shot draws its line independently with probability b;
  2 interleaved, slow: shots run sweep by sweep across the span's circuits; the line switches on a
    telegraph clock with dwell 1 s (about 34 sweeps of 29 ms);
  3 interleaved, fast: the same with dwell 20 ms (under one sweep), which should look independent
    to reading (a) and leave a weak trace in (b).
Lines in Y at 0.96 and 0.04 (test 12's values); b = 0.344.
"""
import numpy as np

NCIRC = 49; SHOTS = 500; B = 0.344; PU, PL = 0.96, 0.04
SPAN_S = 14.42; SWEEP_S = SPAN_S / SHOTS; SHOT_S = SPAN_S / (NCIRC * SHOTS)
RATIO_SHARED = 3.0; RATIO_INDEP = 1.5; AC_FLOOR = 0.05


def lines_interleaved(rng, dwell_s):
    """Line per (sweep, circuit) in execution order: sweep-major, circuit-minor."""
    n = SHOTS * NCIRC
    t = np.arange(n) * SHOT_S
    # asymmetric telegraph with duty b and mean dwell dwell_s (mean of the two dwells)
    ku = 1 / (2 * dwell_s * B); kl = 1 / (2 * dwell_s * (1 - B))  # rates up->down, down->up
    state = rng.random() < B; out = np.empty(n, bool); i = 0
    while i < n:
        rate = ku if state else kl
        dur = rng.exponential(1 / rate); m = max(1, int(dur / SHOT_S)); out[i:i + m] = state; i += m; state = not state
    return out.reshape(SHOTS, NCIRC).T  # [circuit, shot index]


def outcomes(rng, line):
    p = np.where(line, PU, PL); return (rng.random(p.shape) < p).astype(np.int8)


def readings(bits):
    p = bits.mean(axis=1)                      # per circuit P1
    pbar = p.mean()
    # (a) equal-index cross-circuit means
    mj = bits.mean(axis=0)
    v_obs = mj.var(ddof=1); v_ind = (p * (1 - p)).mean() / NCIRC
    ratio = v_obs / v_ind
    # (b) lag-1 autocorrelation in shot order, averaged over circuits
    x = bits - p[:, None]
    ac = np.mean([np.sum(r[1:] * r[:-1]) / np.sum(r * r) if np.sum(r * r) > 0 else 0 for r in x])
    se_ac = 1 / np.sqrt(SHOTS * NCIRC)
    # (c) per-circuit scatter against binomial
    scat = p.var(ddof=1) / (pbar * (1 - pbar) / SHOTS)
    verdict_a = 'SHARED' if ratio > RATIO_SHARED else ('INDEPENDENT' if ratio < RATIO_INDEP else 'UNDECIDED')
    verdict_b = 'CORRELATED' if ac > max(AC_FLOOR, 5 * se_ac) else 'NOT CORRELATED'
    # (b) the correlation time of the sweep means
    x = mj - mj.mean(); v0 = np.sum(x * x)
    acf = np.array([np.sum(x[l:] * x[:-l]) / v0 for l in range(1, 81)])
    excess = 1 - v_ind / v_obs if v_obs > 0 else 0
    below = np.where(acf < excess / np.e)[0]
    lag_e = int(below[0]) + 1 if len(below) else 81
    tau = lag_e * SWEEP_S if (verdict_a == 'SHARED' and lag_e >= 3) else None
    return ratio, ac, scat, verdict_a, verdict_b, lag_e, tau


def run(ntrial=100, seed=13390):
    rng = np.random.default_rng(seed)
    for name, dwell in [('1 independent', None), ('2 interleaved, dwell 1 s', 1.0), ('3 interleaved, dwell 20 ms', 0.02),
                        ('4 interleaved, dwell 100 ms', 0.1)]:
        res = []
        for _ in range(ntrial):
            if dwell is None:
                line = rng.random((NCIRC, SHOTS)) < B
            else:
                line = lines_interleaved(rng, dwell)
            res.append(readings(outcomes(rng, line)))
        ratios = np.array([r[0] for r in res]); acs = np.array([r[1] for r in res]); sc = np.array([r[2] for r in res])
        va = [r[3] for r in res]; vb = [r[4] for r in res]; lags = np.array([r[5] for r in res])
        taus = [r[6] for r in res]; nread = sum(t is not None for t in taus)
        tau_med = np.median([t for t in taus if t is not None]) if nread else float('nan')
        print(f"case {name}: ratio median {np.median(ratios):.2f} [{ratios.min():.2f}, {ratios.max():.2f}]; "
              f"lag-1 ac median {np.median(acs):.3f}; scatter ratio median {np.median(sc):.2f}; "
              f"(a) {dict(zip(*np.unique(va, return_counts=True)))}; (b) {dict(zip(*np.unique(vb, return_counts=True)))}; "
              f"1/e lag median {np.median(lags):.0f} [{lags.min()}, {lags.max()}]; correlation time read in {nread}, median {tau_med:.3f} s"
              f" (true mean dwell {dwell}; sweep {SWEEP_S:.3f} s)")


if __name__ == '__main__':
    run()
