"""Mantri's desk check of the test 15 rule (the error model of a span's weight), before the hash.

The duty is the fraction of sweeps in the high state (m_j above the threshold midway between the 10th and 90th
percentiles), never folded about one half; the telegraph sd is sqrt(2 b (1 - b) tau_c / T) with tau_c from the 1/e lag
of the sweep means' autocorrelation after the shot-noise share of lag 0 is removed; a boundary word is NO CHANGE at or
under two combined sd, BETWEEN to three, CHANGE above three.

A synthetic monitor span: n circuits, N sweeps, a two-state process with duty b and correlation time tau_c on the
sweep clock, lines at p_u and p_l in the quadrature of record, binomial outcomes per circuit per sweep.
Checks: (1) the telegraph standard deviation sqrt(2 b (1 - b) tau_c / T) against the empirical scatter of the span's
duty over 400 synthetic spans; (2) the boundary words NO CHANGE / BETWEEN / CHANGE at their rates when the true duty
does not change and when it changes by three telegraph sd; (3) the recovered tau_c and b against the truth.
"""
import numpy as np

N_CIRC = 49; N_SWEEP = 500; SWEEP_S = 0.0288; T = N_SWEEP * SWEEP_S
PU, PL = 0.96, 0.04


def telegraph(rng, b, tau_c, n):
    """State per sweep: an asymmetric two-state Markov chain with duty b and correlation time tau_c (seconds)."""
    ku = (1 - b) / tau_c; kl = b / tau_c            # rates out of the minority (up) and out of the dominant (down)
    pu_stay = np.exp(-ku * SWEEP_S); pl_stay = np.exp(-kl * SWEEP_S)
    s = np.empty(n, bool); s[0] = rng.random() < b
    r = rng.random(n)
    for j in range(1, n):
        s[j] = (r[j] < pu_stay) if s[j - 1] else (r[j] >= pl_stay)
    return s


def span(rng, b, tau_c):
    s = telegraph(rng, b, tau_c, N_SWEEP)
    p = np.where(s, PU, PL)
    M = (rng.random((N_CIRC, N_SWEEP)) < p[None, :]).astype(np.int8)
    return M, s


def read(M, sweep_s=SWEEP_S):
    """The rule's readings on one span's bit matrix: threshold, duty, tau_c, dwells, the telegraph sd."""
    mj = M.mean(axis=0); n = M.shape[0]
    lo, hi = np.percentile(mj, [10, 90]); thr = (lo + hi) / 2
    s = mj > thr
    b = s.mean()                                   # the duty of the high state; never folded about one half
    # correlation time from the autocorrelation of m_j, the shot-noise share of lag 0 removed
    p = M.mean(axis=1); v_ind = (p * (1 - p)).mean() / n
    x = mj - mj.mean(); v0 = np.sum(x * x); v_obs = mj.var(ddof=1)
    acf = np.array([np.sum(x[l:] * x[:-l]) / v0 for l in range(1, 201)])
    excess = max(1 - v_ind / v_obs, 1e-9)
    below = np.where(acf < excess / np.e)[0]
    lag = int(below[0]) + 1 if len(below) else 201
    tau_c = lag * sweep_s
    T_span = M.shape[1] * sweep_s
    sd = np.sqrt(2 * b * (1 - b) * tau_c / T_span)
    ch = np.flatnonzero(np.diff(s.astype(int))); nsw = len(ch)
    return dict(b=b, tau_c=tau_c, sd=sd, nsw=nsw, thr=thr, ratio=v_obs / v_ind)


def word(d, sd):
    z = abs(d) / sd
    return 'NO CHANGE' if z <= 2 else ('BETWEEN' if z <= 3 else 'CHANGE')


def run(seed=15390, ntrial=400):
    rng = np.random.default_rng(seed)
    for b_true, tau_true in [(0.344, 0.17), (0.344, 0.5), (0.206, 0.15), (0.45, 0.17)]:
        duties = []; taus = []; sds = []
        for _ in range(ntrial):
            M, s = span(rng, b_true, tau_true); r = read(M)
            duties.append(r['b']); taus.append(r['tau_c']); sds.append(r['sd'])
        duties = np.array(duties); emp = duties.std(ddof=1)
        formula = np.sqrt(2 * b_true * (1 - b_true) * tau_true / T)
        print(f"b {b_true} tau_c {tau_true}s T {T:.1f}s: duty mean {duties.mean():.3f}; empirical sd of the span duty {emp:.3f}; "
              f"formula with true tau {formula:.3f}; median of the rule's sd {np.median(sds):.3f}; recovered tau_c median {np.median(taus):.3f}s")
    # boundary words
    rng = np.random.default_rng(seed + 1)
    for name, shift in [('no change', 0.0), ('change of three sd', 3 * np.sqrt(2 * 0.344 * 0.656 * 0.17 / T)), ('change of 0.137', 0.137)]:
        words = []
        for _ in range(ntrial):
            M1, _ = span(rng, 0.344, 0.17); M2, _ = span(rng, 0.344 - shift, 0.17)
            r1, r2 = read(M1), read(M2)
            sd = np.sqrt(r1['sd'] ** 2 + r2['sd'] ** 2)
            words.append(word(r2['b'] - r1['b'], sd))
        u, c = np.unique(words, return_counts=True)
        print(f"boundary, {name} (shift {shift:.3f}): {dict(zip(u, (c / ntrial * 100).round(1)))} percent")


if __name__ == '__main__':
    run()
