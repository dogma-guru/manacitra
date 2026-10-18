"""Mantri's desk check of the test 10 rule (phase monitor), before the hash."""
import numpy as np
from scipy import stats

NREP = 148; SHOTS = 1000; C = 0.5
SPANS = [(0, 99), (100, 199), (200, 299)]   # positions; readout at 0,1 and 298,299; repeat k occupies 2+2k, 3+2k
S_FLOOR = 0.02; JUMP = 0.3; NSIG = 5.0; R_FLOOR = 0.08


def span_of_pos(p):
    for i, (a, b) in enumerate(SPANS):
        if a <= p <= b: return i


def repeat_spans():
    out = []
    for k in range(NREP):
        p1, p2 = 2 + 2 * k, 3 + 2 * k
        out.append((span_of_pos(p1), span_of_pos(p2)))
    return out


def analyse(px, py, rng=None):
    vx, vy = px - C, py - C
    th = np.arctan2(vy, vx); r = np.hypot(vx, vy)
    sig = np.sqrt((px * (1 - px) + py * (1 - py)) / (2 * SHOTS))
    s = np.maximum(sig / np.maximum(r, 1e-9), S_FLOOR)
    usable = np.median(r) >= R_FLOOR
    rs = repeat_spans()
    straddle = [a != b for a, b in rs]
    span = [a for a, b in rs]
    d = np.diff(th); d = (d + np.pi) % (2 * np.pi) - np.pi
    thr = np.maximum(JUMP, NSIG * np.sqrt(s[:-1] ** 2 + s[1:] ** 2))
    sw = np.abs(d) > thr
    n_within = n_boundary = 0; where_w = []; where_b = []
    for k in range(NREP - 1):
        if straddle[k] or straddle[k + 1]: continue
        if not sw[k]: continue
        if span[k] == span[k + 1]: n_within += 1; where_w.append(k + 1)
        else: n_boundary += 1; where_b.append(k + 1)
    # levels: plateaus between switches
    cuts = [0] + [k for k in range(1, NREP) if sw[k - 1]] + [NREP]
    plateaus = []
    unw = np.concatenate([[th[0]], th[0] + np.cumsum(d)])
    for a, b in zip(cuts[:-1], cuts[1:]):
        w = 1 / s[a:b] ** 2
        plateaus.append(((w * unw[a:b]).sum() / w.sum(), np.sqrt(1 / w.sum()), b - a))
    # distinct levels modulo 2pi
    levels = []
    for m, se, n in plateaus:
        for L in levels:
            dd = (m - L[0] + np.pi) % (2 * np.pi) - np.pi
            if abs(dd) <= 3 * np.sqrt(se ** 2 + L[1] ** 2): break
        else:
            levels.append((m, se))
    if not usable: v = 'NOT USABLE'
    elif n_within >= 1: v = 'SWITCHES WITHIN SPANS'
    elif n_boundary >= 1: v = 'SWITCHES AT BOUNDARIES ONLY'
    else: v = 'QUIET'
    # slope per span
    slopes = []
    for i in range(3):
        idx = [k for k in range(NREP) if span[k] == i and not straddle[k]]
        kk = np.array(idx, float); yy = unw[idx]; ww = 1 / s[idx] ** 2
        A = np.column_stack([np.ones(len(kk)), kk]) * np.sqrt(ww)[:, None]
        bl, *_ = np.linalg.lstsq(A, yy * np.sqrt(ww), rcond=None); slopes.append(bl[1])
    return dict(v=v, n_within=n_within, n_boundary=n_boundary, where_w=where_w, where_b=where_b,
                levels=levels, nlev=len(levels), plateaus=plateaus, slopes=slopes, r_med=np.median(r))


def fringe(A, tau, t_us, f_khz, phi=0.3):
    env = A * np.exp(-t_us / tau); w = 2 * np.pi * f_khz * 1e-3 * t_us + phi
    return C + env * np.cos(w), C + env * np.sin(w)


def make_case(name, rng):
    A, tau, t = 0.45, 100.0, 20.0
    f = np.full(NREP, 20.0)
    if name == '1 steady':
        pass
    elif name == '2 weak':
        A, tau = 0.3, 30.0
    elif name == '3 step 4 kHz at 30 and 80':
        f[30:80] += 4.0
    elif name == '4 step 1 kHz at 30 and 80':
        f[30:80] += 1.0
    elif name == '5 step 4 kHz at the boundaries':
        f[49:99] += 4.0   # repeat index 49 is the first repeat in span 1 (positions 100,101); span 2 starts at repeat 99
    elif name == '7 drift 2 kHz':
        f = 20.0 + 2.0 * np.arange(NREP) / (NREP - 1)
    if name == '6 telegraph antiphase 43':
        A, tau, t = 0.4, 56.6, 46.0
        lines = (-5.97, -16.86)
        state = 0; st = []
        for k in range(NREP):
            st.append(state)
            if rng.random() < 1 / 20: state ^= 1
        st = np.array(st)
        f = np.where(st == 0, lines[0], lines[1])
        nsw = int((np.diff(st) != 0).sum())
        px, py = fringe(A, tau, t, f)
        return px, py, dict(planted_switch_count=nsw, planted_at=[k + 1 for k in range(NREP - 1) if st[k + 1] != st[k]])
    if name == '8 mixed within repeat':
        A, tau, t = 0.4, 56.6, 46.0
        px1, py1 = fringe(A, tau, t, -5.97); px2, py2 = fringe(A, tau, t, -16.86)
        px = np.full(NREP, 0.5 * (px1 + px2)); py = np.full(NREP, 0.5 * (py1 + py2))
        return px, py, {}
    px, py = fringe(A, tau, t, f)
    return px, py, {}


CASES = ['1 steady', '2 weak', '3 step 4 kHz at 30 and 80', '4 step 1 kHz at 30 and 80',
         '5 step 4 kHz at the boundaries', '6 telegraph antiphase 43', '7 drift 2 kHz', '8 mixed within repeat']


def run(ntrial=100, seed=10390):
    rs = repeat_spans()
    first_in_span = [min(k for k in range(NREP) if rs[k][0] == i and rs[k][0] == rs[k][1]) for i in range(3)]
    print("first whole repeat of each span (0-based):", first_in_span, "straddling repeats:", [k for k in range(NREP) if rs[k][0] != rs[k][1]])
    for name in CASES:
        rng = np.random.default_rng([seed, CASES.index(name)])
        counts = {}; extra = []
        for tr in range(ntrial):
            px, py, info = make_case(name, rng)
            kx = rng.binomial(SHOTS, np.clip(px, 0, 1)) / SHOTS
            ky = rng.binomial(SHOTS, np.clip(py, 0, 1)) / SHOTS
            res = analyse(kx, ky)
            counts[res['v']] = counts.get(res['v'], 0) + 1
            if name.startswith('3') or name.startswith('4'):
                extra.append(res['where_w'] == [30, 80])
            if name.startswith('5'):
                extra.append((res['n_within'], res['n_boundary']))
            if name.startswith('6'):
                sep = None
                if res['nlev'] >= 2:
                    sep = abs((res['levels'][1][0] - res['levels'][0][0] + np.pi) % (2 * np.pi) - np.pi)
                extra.append((abs(res['n_within'] + res['n_boundary'] - info['planted_switch_count']) <= 1,
                              sep is not None and abs(sep - np.pi) < 0.3, res['nlev']))
            if name.startswith('7'):
                extra.append(np.mean(res['slopes']) / (2 * np.pi * 20e-3) * 100)  # kHz per 100 repeats
            if name.startswith('8'):
                extra.append(res['r_med'])
        line = f"{name}: {counts}"
        if name.startswith('3') or name.startswith('4'): line += f"; both switches at the planted repeats {np.mean(extra):.2f}"
        if name.startswith('5'): line += f"; (n_within, n_boundary) modes {stats.mode([e for e in extra], keepdims=False)}"
        if name.startswith('6'): line += f"; count within 1 {np.mean([e[0] for e in extra]):.2f}; separation ~pi {np.mean([e[1] for e in extra]):.2f}; levels median {np.median([e[2] for e in extra])}"
        if name.startswith('7'): line += f"; slope median {np.median(extra):.2f} kHz per 100 repeats (planted 1.36)"
        if name.startswith('8'): line += f"; median r {np.median(extra):.3f}"
        print(line)


if __name__ == '__main__':
    run()
