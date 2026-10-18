"""Mantri's desk check of the test 12 rule (short monitor on fez 143 at 5.6 us, 500 shots), before the hash."""
import numpy as np

NREP = 123; SHOTS = 500
SPANS = [(0, 100), (101, 200), (201, 249)]
S_FLOOR = 0.02; JUMP = 0.3; NSIG = 5.0; R_FLOOR = 0.08; W_JUMP = 0.10
C, A, TAU, D0, DEL, B = 0.49, 0.487, 128.3, 48.66, 44.82, 0.355
T = 5.6
R0 = 0.4749


def span_of_pos(p):
    for i, (a, b) in enumerate(SPANS):
        if a <= p <= b: return i


def repeat_spans():
    return [(span_of_pos(2 + 2 * k), span_of_pos(3 + 2 * k)) for k in range(NREP)]


def fringe(b, f_shift=0.0, phi=0.3):
    env = A * np.exp(-T / TAU)
    wu = 2 * np.pi * (D0 + DEL + f_shift) * 1e-3 * T + phi
    wl = 2 * np.pi * (D0 - DEL + f_shift) * 1e-3 * T + phi
    return (C + env * (b * np.cos(wu) + (1 - b) * np.cos(wl)),
            C + env * (b * np.sin(wu) + (1 - b) * np.sin(wl)))


def analyse(px, py, c=C, r0=R0):
    vx, vy = px - c, py - c
    th = np.arctan2(vy, vx); r = np.hypot(vx, vy)
    sig = np.sqrt((px * (1 - px) + py * (1 - py)) / (2 * SHOTS))
    s = np.maximum(sig / np.maximum(r, 1e-9), S_FLOOR)
    usable = np.median(r) >= R_FLOOR
    rs = repeat_spans(); straddle = [a != b for a, b in rs]; span = [a for a, b in rs]
    cm = np.angle(np.mean(np.exp(1j * th)))
    med = np.median((th - cm + np.pi) % (2 * np.pi) - np.pi) + cm
    dist = np.abs((th - med + np.pi) % (2 * np.pi) - np.pi)
    w = np.where(dist <= np.pi / 2, (1 - r / r0) / 2, (1 + r / r0) / 2)
    se_w = sig / (2 * r0)
    def dphase(i, j):
        return (th[j] - th[i] + np.pi) % (2 * np.pi) - np.pi
    # within-span pairs
    pw = pb = ww = wb = 0; pw_at = []; ww_at = []; pb_sizes = []
    for k in range(NREP - 1):
        if straddle[k] or straddle[k + 1] or span[k] != span[k + 1]: continue
        thr = max(JUMP, NSIG * np.sqrt(s[k] ** 2 + s[k + 1] ** 2))
        thrw = max(W_JUMP, NSIG * np.sqrt(se_w[k] ** 2 + se_w[k + 1] ** 2))
        if abs(dphase(k, k + 1)) > thr: pw += 1; pw_at.append(k + 1)
        if abs(w[k + 1] - w[k]) > thrw: ww += 1; ww_at.append(k + 1)
    # boundary pairs: last whole before, first whole after
    whole = [k for k in range(NREP) if not straddle[k]]
    levels = []
    for i in range(len(SPANS)):
        idx = [k for k in whole if span[k] == i]
        if not idx: levels.append(None); continue
        m = w[idx].mean(); prop = np.sqrt((se_w[idx] ** 2).sum()) / len(idx); sc = w[idx].std(ddof=1) / np.sqrt(len(idx))
        levels.append((m, max(prop, sc), len(idx)))
    nb = 0; nlev = 0
    for i in range(len(SPANS) - 1):
        before = [k for k in whole if span[k] == i]; after = [k for k in whole if span[k] == i + 1]
        if not before or not after: continue
        a, b = before[-1], after[0]; nb += 1
        thr = max(JUMP, NSIG * np.sqrt(s[a] ** 2 + s[b] ** 2)); thrw = max(W_JUMP, NSIG * np.sqrt(se_w[a] ** 2 + se_w[b] ** 2))
        if abs(dphase(a, b)) > thr: pb += 1; pb_sizes.append(abs(dphase(a, b)))
        if abs(w[b] - w[a]) > thrw: wb += 1
        La, Lb = levels[i], levels[i + 1]
        if abs(Lb[0] - La[0]) > NSIG * np.sqrt(La[1] ** 2 + Lb[1] ** 2): nlev += 1
    def word(nw, nbb):
        if not usable: return 'NOT USABLE'
        return 'WITHIN' if nw else ('BOUNDARIES' if nbb else 'QUIET')
    lev = 'NOT USABLE' if not usable else ('EVERY' if nlev == nb and nb > 0 else ('SOME' if nlev else 'AGREE'))
    return dict(vp=word(pw, pb), vw=word(ww, wb), vl=lev, pw_at=pw_at, ww_at=ww_at, pb_sizes=pb_sizes, nb=nb,
                w_med=float(np.median(w)), r_med=float(np.median(r)), levels=levels,
                thr_med=float(np.median(np.maximum(JUMP, NSIG * np.sqrt(2) * s))),
                thrw_med=float(np.median(np.maximum(W_JUMP, NSIG * np.sqrt(2) * se_w))))


def make_case(name):
    b = np.full(NREP, B); f = np.zeros(NREP)
    if name.startswith('2 '): b[25:75] = 0.10
    elif name.startswith('2b'): b[25:75] = 0.15
    elif name.startswith('3 '): b[50:100] = 0.305; b[100:] = 0.405
    elif name.startswith('4 '): b[50:100] = 0.645
    elif name.startswith('5 '): f[25:75] = 50.0
    elif name.startswith('5b'): f[25:75] = 30.0
    elif name.startswith('5c'): f[25:75] = 12.0
    elif name.startswith('6 '): b[:] = 0.5
    px = np.empty(NREP); py = np.empty(NREP)
    for k in range(NREP): px[k], py[k] = fringe(b[k], f[k])
    return px, py


CASES = ['1 steady', '2 weight step to 0.10 at 25 and 75', '2b weight step to 0.15 at 25 and 75', '3 level steps 0.05 and 0.10 at the boundaries',
         '4 weight flip to 0.645 at the boundaries', '5 common step 50 kHz at 25 and 75',
         '5b common step 30 kHz', '5c common step 12 kHz', '6 weight fresh per shot at 0.5']


def run(ntrial=100, seed=12390):
    rs = repeat_spans()
    print('straddling repeats (1-based):', [k + 1 for k in range(NREP) if rs[k][0] != rs[k][1]],
          f'R0 {R0:.4f} antiphase r {A*np.exp(-T/TAU)*abs(2*B-1):.3f}')
    for name in CASES:
        rng = np.random.default_rng([seed, CASES.index(name)])
        cp = {}; cw = {}; cl = {}; ex = []
        for _ in range(ntrial):
            px, py = make_case(name)
            kx = rng.binomial(SHOTS, np.clip(px, 0, 1)) / SHOTS; ky = rng.binomial(SHOTS, np.clip(py, 0, 1)) / SHOTS
            res = analyse(kx, ky)
            for d, v in ((cp, res['vp']), (cw, res['vw']), (cl, res['vl'])): d[v] = d.get(v, 0) + 1
            if name.startswith('1'): ex.append((abs(res['w_med'] - B) <= 0.05, res['thr_med'], res['thrw_med'], res['levels']))
            if name.startswith('2'): ex.append(res['ww_at'] == [25, 75])
            if name.startswith('4'): ex.append(all(abs(x - np.pi) < 0.6 for x in res['pb_sizes']) and len(res['pb_sizes']) == 2)
            if name.startswith('5'): ex.append(res['pw_at'] == [25, 75])
            if name.startswith('6'): ex.append(res['r_med'])
        line = f"{name}: phase {cp}; weight {cw}; levels {cl}"
        if name.startswith('1'):
            L = ex[0][3]
            line += (f"; w median within 0.05: {np.mean([e[0] for e in ex]):.2f}; phase floor {np.median([e[1] for e in ex]):.2f} rad = "
                     f"{np.median([e[1] for e in ex])*28.42:.0f} kHz; pair weight floor {np.median([e[2] for e in ex]):.3f}; "
                     f"span errors {[round(l[1],4) for l in L]} repeats {[l[2] for l in L]}")
        if name.startswith('2'): line += f"; both weight switches at 25 and 75: {np.mean(ex):.2f}"
        if name.startswith('4'): line += f"; two boundary phase steps each within 0.6 rad of pi: {np.mean(ex):.2f}"
        if name.startswith('5'): line += f"; both phase switches placed: {np.mean(ex):.2f}"
        if name.startswith('6'): line += f"; median r {np.median(ex):.3f}"
        print(line)


if __name__ == '__main__':
    run()
