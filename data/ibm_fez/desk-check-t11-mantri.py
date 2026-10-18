"""Mantri's desk check of the test 11 monitor rule on fez 143 at 5.6 us, before the hash."""
import numpy as np

NREP = 148; SHOTS = 1000
SPANS = [(0, 99), (100, 199), (200, 299)]
S_FLOOR = 0.02; JUMP = 0.3; NSIG = 5.0; R_FLOOR = 0.08; W_JUMP = 0.10
# test 7's P fit on 143
C, A, TAU, D0, DEL, B = 0.49, 0.487, 128.3, 48.66, 44.82, 0.355   # kHz for D0, DEL
T = 5.6
R0 = A * np.exp(-T / TAU)


def span_of_pos(p):
    for i, (a, b) in enumerate(SPANS):
        if a <= p <= b: return i


def repeat_spans():
    return [(span_of_pos(2 + 2 * k), span_of_pos(3 + 2 * k)) for k in range(NREP)]


def fringe(b, f_shift=0.0, phi=0.3):
    """two lines at D0 +- DEL (kHz) plus a common shift, weight b on the upper line, at wait T"""
    env = A * np.exp(-T / TAU)
    wu = 2 * np.pi * (D0 + DEL + f_shift) * 1e-3 * T + phi
    wl = 2 * np.pi * (D0 - DEL + f_shift) * 1e-3 * T + phi
    px = C + env * (b * np.cos(wu) + (1 - b) * np.cos(wl))
    py = C + env * (b * np.sin(wu) + (1 - b) * np.sin(wl))
    return px, py


def analyse(px, py, c=C, r0=R0):
    vx, vy = px - c, py - c
    th = np.arctan2(vy, vx); r = np.hypot(vx, vy)
    sig = np.sqrt((px * (1 - px) + py * (1 - py)) / (2 * SHOTS))
    s = np.maximum(sig / np.maximum(r, 1e-9), S_FLOOR)
    usable = np.median(r) >= R_FLOOR
    rs = repeat_spans(); straddle = [a != b for a, b in rs]; span = [a for a, b in rs]
    d = np.diff(th); d = (d + np.pi) % (2 * np.pi) - np.pi
    thr = np.maximum(JUMP, NSIG * np.sqrt(s[:-1] ** 2 + s[1:] ** 2))
    sw = np.abs(d) > thr
    # weight per repeat: branch by distance from the job's median phase
    med = np.angle(np.mean(np.exp(1j * th)))
    dist = np.abs((th - med + np.pi) % (2 * np.pi) - np.pi)
    w = np.where(dist <= np.pi / 2, (1 - r / r0) / 2, (1 + r / r0) / 2)
    se_w = sig / (2 * r0)
    dw = np.diff(w); thr_w = np.maximum(W_JUMP, NSIG * np.sqrt(se_w[:-1] ** 2 + se_w[1:] ** 2))
    sww = np.abs(dw) > thr_w
    out = dict(usable=usable, r_med=float(np.median(r)), w_med=float(np.median(w)), thr_med=float(np.median(thr)),
               thr_w_med=float(np.median(thr_w)), dsize=[], w_span=[])
    for key, flags in (('p', sw), ('w', sww)):
        nw = nb = 0; ww = []; bb = []
        for k in range(NREP - 1):
            if straddle[k] or straddle[k + 1] or not flags[k]: continue
            if span[k] == span[k + 1]: nw += 1; ww.append(k + 1)
            else: nb += 1; bb.append(k + 1)
        out[key] = (nw, nb, ww, bb)
        if key == 'p': out['dsize'] = [abs(d[k]) for k in [x - 1 for x in bb]]
    for i in range(3):
        idx = [k for k in range(NREP) if span[k] == i and not straddle[k]]
        out['w_span'].append(float(np.mean(w[idx])))
    def word(nw, nb):
        if not usable: return 'NOT USABLE'
        return 'SWITCHES WITHIN SPANS' if nw else ('SWITCHES AT BOUNDARIES ONLY' if nb else 'QUIET')
    out['vp'] = word(*out['p'][:2]); out['vw'] = word(*out['w'][:2])
    return out


def make_case(name):
    b = np.full(NREP, B); f = np.zeros(NREP)
    if name == '2 weight step to 0.15 at 30 and 80': b[30:80] = 0.15
    elif name == '2b weight step to 0.20 at 30 and 80': b[30:80] = 0.20
    elif name == '3 weight flip to 0.645 at the boundaries': b[49:99] = 0.645
    elif name == '4 common step 4 kHz at 30 and 80': f[30:80] = 4.0
    elif name == '5 common step 40 kHz at 30 and 80': f[30:80] = 40.0
    elif name == '5b common step 12 kHz at 30 and 80': f[30:80] = 12.0
    elif name == '5c common step 30 kHz at 30 and 80': f[30:80] = 30.0
    elif name == '6 weight fresh per shot at 0.5': b[:] = 0.5
    px = np.empty(NREP); py = np.empty(NREP)
    for k in range(NREP):
        px[k], py[k] = fringe(b[k], f[k])
    return px, py


CASES = ['1 steady', '2 weight step to 0.15 at 30 and 80', '2b weight step to 0.20 at 30 and 80',
         '3 weight flip to 0.645 at the boundaries', '4 common step 4 kHz at 30 and 80',
         '5 common step 40 kHz at 30 and 80', '5c common step 30 kHz at 30 and 80', '5b common step 12 kHz at 30 and 80', '6 weight fresh per shot at 0.5']


def run(ntrial=100, seed=11390):
    print(f"R0 {R0:.3f}; antiphase r {R0*abs(2*B-1):.3f}; phase difference of the lines {2*np.pi*2*DEL*1e-3*T/np.pi:.3f} pi")
    for name in CASES:
        rng = np.random.default_rng([seed, CASES.index(name)])
        cp = {}; cw = {}; ex = []
        for tr in range(ntrial):
            px, py = make_case(name)
            kx = rng.binomial(SHOTS, np.clip(px, 0, 1)) / SHOTS
            ky = rng.binomial(SHOTS, np.clip(py, 0, 1)) / SHOTS
            res = analyse(kx, ky)
            cp[res['vp']] = cp.get(res['vp'], 0) + 1; cw[res['vw']] = cw.get(res['vw'], 0) + 1
            if name.startswith('1'): ex.append((abs(res['w_med'] - B) <= 0.05, res['thr_med'], res['thr_w_med']))
            if name.startswith('2'): ex.append(res['w'][2] == [30, 80])
            if name.startswith('3'): ex.append((res['p'][3] == [49, 99], all(abs(x - np.pi) < 0.5 for x in res['dsize']),
                                                abs(res['w_span'][1] - 0.645) <= 0.05))
            if name.startswith('5'): ex.append(res['p'][2] == [30, 80])
            if name.startswith('6'): ex.append(res['r_med'])
        line = f"{name}: phase {cp}; weight {cw}"
        if name.startswith('1'):
            line += f"; w median within 0.05 of 0.355: {np.mean([e[0] for e in ex]):.2f}; median phase threshold {np.median([e[1] for e in ex]):.2f} rad = {np.median([e[1] for e in ex])*28.42:.1f} kHz; median weight threshold {np.median([e[2] for e in ex]):.3f}"
        if name.startswith('2'): line += f"; both weight switches at 30 and 80: {np.mean(ex):.2f}"
        if name.startswith('3'): line += f"; boundary switches at 49 and 99: {np.mean([e[0] for e in ex]):.2f}; each within 0.5 rad of pi: {np.mean([e[1] for e in ex]):.2f}; middle-span weight within 0.05 of 0.645: {np.mean([e[2] for e in ex]):.2f}"
        if name.startswith('5'): line += f"; both phase switches at 30 and 80: {np.mean(ex):.2f}"
        if name.startswith('6'): line += f"; median r {np.median(ex):.3f}"
        print(line)


if __name__ == '__main__':
    run()
