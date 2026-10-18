"""Mantri's desk check of the test 14 rule (the in-phase control on fez 143), before the hash.

Readings as the rule fixes them: levels per span of the weight at the live R0, of R0 from the control length, and of the
control phase; a level change is a difference of adjacent span means above five combined errors; the attribution per
boundary is NOTHING, WEIGHT, ENVELOPE, FRAME or MIXED; a control phase step above 1 rad at a boundary is MIXED by rule.

One job: 2 readout, then 61 repeats of X(5.6), Y(5.6), X(11.2), Y(11.2), then 2 readout: 248 circuits at 500 shots.
Spans assumed at positions 0 to 99, 100 to 199, 200 to 247 (the record decides); straddling repeats 24 and 49.
"""
import numpy as np

NREP = 61; SHOTS = 500
SPANS = [(0, 99), (100, 199), (200, 247)]
S_FLOOR = 0.02; JUMP = 0.3; NSIG = 5.0; R_FLOOR = 0.08; W_JUMP = 0.10
C, A, TAU, D0, DEL, B = 0.4975, 0.487, 128.3, 48.66, 44.70, 0.344
TA, TC = 5.6, 11.2
ENV_RATIO = np.exp((TC - TA) / TAU)   # r_control * ENV_RATIO = R0 at the antiphase wait (tau' fixed from job 1)
R0_FIXED = 0.4749


def span_of_pos(p):
    for i, (a, b) in enumerate(SPANS):
        if a <= p <= b: return i


def repeat_positions(k):
    return [2 + 4 * k, 3 + 4 * k, 4 + 4 * k, 5 + 4 * k]


def fringe(t, b, f_shift=0.0, phi=0.3, env=1.0, c=C):
    e = A * env * np.exp(-t / TAU)
    wu = 2 * np.pi * (D0 + DEL + f_shift) * 1e-3 * t + phi
    wl = 2 * np.pi * (D0 - DEL + f_shift) * 1e-3 * t + phi
    return (c + e * (b * np.cos(wu) + (1 - b) * np.cos(wl)), c + e * (b * np.sin(wu) + (1 - b) * np.sin(wl)))


def series(px, py, c):
    vx, vy = px - c, py - c
    th = np.arctan2(vy, vx); r = np.hypot(vx, vy)
    sig = np.sqrt((px * (1 - px) + py * (1 - py)) / (2 * SHOTS))
    s = np.maximum(sig / np.maximum(r, 1e-9), S_FLOOR)
    return th, r, sig, s


def wrap(d): return (d + np.pi) % (2 * np.pi) - np.pi


def level_table(x, se, span, whole):
    out = []
    for i in range(len(SPANS)):
        idx = [k for k in whole if span[k] == i]
        if not idx: out.append(None); continue
        m = x[idx].mean(); prop = np.sqrt((se[idx] ** 2).sum()) / len(idx); sc = x[idx].std(ddof=1) / np.sqrt(len(idx))
        out.append((m, max(prop, sc), len(idx)))
    return out


def level_changes(lev, circular=False):
    ch = []
    for i in range(len(SPANS) - 1):
        a, b = lev[i], lev[i + 1]
        if a is None or b is None: ch.append(None); continue
        d = wrap(b[0] - a[0]) if circular else b[0] - a[0]
        ce = np.sqrt(a[1] ** 2 + b[1] ** 2)
        ch.append((d, ce, abs(d) > NSIG * ce))
    return ch


def analyse(pxa, pya, pxc, pyc, c=C, tau=TAU):
    tha, ra, siga, sa = series(pxa, pya, c)
    thc, rc, sigc, sc_ = series(pxc, pyc, c)
    env_ratio = np.exp((TC - TA) / tau)
    R0_live = rc * env_ratio; se_R0 = sigc * env_ratio
    usable = np.median(ra) >= R_FLOOR and np.median(rc) >= 2 * R_FLOOR
    sp = [[span_of_pos(p) for p in repeat_positions(k)] for k in range(NREP)]
    straddle = [len(set(x)) > 1 for x in sp]; span = [x[0] for x in sp]
    whole = [k for k in range(NREP) if not straddle[k]]
    # branch by median antiphase phase on one sheet (test 11's ruling)
    cm = np.angle(np.mean(np.exp(1j * tha))); med = np.median(wrap(tha - cm)) + cm
    dist = np.abs(wrap(tha - med))
    w_live = np.where(dist <= np.pi / 2, (1 - ra / R0_live) / 2, (1 + ra / R0_live) / 2)
    w_fixed = np.where(dist <= np.pi / 2, (1 - ra / R0_FIXED) / 2, (1 + ra / R0_FIXED) / 2)
    se_w_live = np.sqrt((siga / (2 * R0_live)) ** 2 + (ra * se_R0 / (2 * R0_live ** 2)) ** 2)
    se_w_fixed = siga / (2 * R0_FIXED)
    # within-span pair tests on three series: antiphase phase, control phase, control length
    def pairs(th, s, x, se_x, jump, xjump):
        nph = nx = 0
        for k in range(NREP - 1):
            if straddle[k] or straddle[k + 1] or span[k] != span[k + 1]: continue
            thr = max(jump, NSIG * np.sqrt(s[k] ** 2 + s[k + 1] ** 2)); thrx = max(xjump, NSIG * np.sqrt(se_x[k] ** 2 + se_x[k + 1] ** 2))
            if abs(wrap(th[k + 1] - th[k])) > thr: nph += 1
            if abs(x[k + 1] - x[k]) > thrx: nx += 1
        return nph, nx
    a_ph, a_w = pairs(tha, sa, w_live, se_w_live, JUMP, W_JUMP)
    c_ph, c_r = pairs(thc, sc_, rc, sigc, JUMP, 0.0)
    # levels per span
    lev_w = level_table(w_live, se_w_live, span, whole)
    lev_wf = level_table(w_fixed, se_w_fixed, span, whole)
    lev_R0 = level_table(R0_live, se_R0, span, whole)
    # control phase level: circular mean per span with propagated error
    thc_u = np.unwrap(thc)
    lev_phc = level_table(thc_u, sc_, span, whole)
    ch_w = level_changes(lev_w); ch_wf = level_changes(lev_wf); ch_R0 = level_changes(lev_R0); ch_ph = level_changes(lev_phc)
    # attribution per boundary
    attr = []
    for i in range(len(SPANS) - 1):
        if ch_w[i] is None: attr.append('NO PAIR'); continue
        wchg, rchg, pchg = ch_w[i][2], ch_R0[i][2], ch_ph[i][2]
        if ch_ph[i] is not None and abs(ch_ph[i][0]) > 1.0: attr.append('MIXED'); continue   # the branch rule's limit (section 5)
        if not (wchg or rchg or pchg): attr.append('NOTHING')
        elif wchg and not rchg and not pchg: attr.append('WEIGHT')
        elif rchg and not pchg and not wchg: attr.append('ENVELOPE')
        elif pchg and not rchg and not wchg: attr.append('FRAME')
        else: attr.append('MIXED')
    def word(n_within, n_lev):
        if not usable: return 'NOT USABLE'
        return 'WITHIN' if n_within else ('EVERY' if n_lev == 2 else ('SOME' if n_lev else 'AGREE'))
    nlev = lambda ch: sum(1 for x in ch if x and x[2])
    return dict(usable=usable, attr=attr,
                v_weight=word(a_w, nlev(ch_w)), v_env=word(c_r, nlev(ch_R0)), v_frame=word(c_ph, nlev(ch_ph)),
                fixed_vs_live=[(ch_wf[i][2], ch_w[i][2]) for i in range(2) if ch_w[i]],
                R0_med=float(np.median(R0_live)), w_med=float(np.median(w_live)), ra_med=float(np.median(ra)), rc_med=float(np.median(rc)),
                lev_R0=lev_R0, lev_w=lev_w, ch_ph=ch_ph, ch_R0=ch_R0, ch_w=ch_w,
                phc_floor=float(np.median(np.maximum(JUMP, NSIG * np.sqrt(2) * sc_))),
                R0_level_se=[x[1] for x in lev_R0 if x], w_level_se=[x[1] for x in lev_w if x])


def make_case(name):
    b = np.full(NREP, B); f = np.zeros(NREP); env = np.ones(NREP); c = np.full(NREP, C)
    k1 = [k for k in range(NREP) if span_of_pos(repeat_positions(k)[0]) >= 1]
    k2 = [k for k in range(NREP) if span_of_pos(repeat_positions(k)[0]) >= 2]
    if name.startswith('2'):      # weight level steps at both boundaries, control untouched
        b[k1] = B - 0.06; b[k2] = B - 0.14
    if name.startswith('3b'):     # envelope drops 40 percent at the second boundary, weight fixed
        env[k2] = 0.60
    elif name.startswith('3'):    # envelope drops 15 percent at the second boundary, weight fixed
        env[k2] = 0.85
    if name.startswith('4'):      # common frequency shift 10 kHz at the first boundary
        f[k1] = 10.0
    if name.startswith('5'):      # weight step and frame shift together at the second boundary
        b[k2] = B - 0.14; f[k2] = 10.0
    if name.startswith('6'):      # readout midpoint moves 0.02 at the second boundary (envelope and offset)
        c[k2] = C + 0.02
    return b, f, env, c


def run(ntrial=100, seed=14390):
    rng = np.random.default_rng(seed)
    names = ['1 steady', '2 weight levels 0.06 and 0.14', '3 envelope down 15 percent at boundary 2', '3b envelope down 40 percent at boundary 2',
             '4 frame 10 kHz at boundary 1', '5 weight 0.14 and frame 10 kHz at boundary 2', '6 midpoint up 0.02 at boundary 2']
    for name in names:
        b, f, env, c = make_case(name); res = []
        for _ in range(ntrial):
            pxa, pya, pxc, pyc = [], [], [], []
            for k in range(NREP):
                xa, ya = fringe(TA, b[k], f[k], env=env[k], c=c[k]); xc, yc = fringe(TC, b[k], f[k], env=env[k], c=c[k])
                pxa.append(rng.binomial(SHOTS, xa) / SHOTS); pya.append(rng.binomial(SHOTS, ya) / SHOTS)
                pxc.append(rng.binomial(SHOTS, xc) / SHOTS); pyc.append(rng.binomial(SHOTS, yc) / SHOTS)
            res.append(analyse(*map(np.array, (pxa, pya, pxc, pyc))))
        attrs = [tuple(r['attr']) for r in res]
        ua, ca = np.unique(attrs, return_counts=True, axis=0)
        vw = {k: sum(r['v_weight'] == k for r in res) for k in set(r['v_weight'] for r in res)}
        ve = {k: sum(r['v_env'] == k for r in res) for k in set(r['v_env'] for r in res)}
        vf = {k: sum(r['v_frame'] == k for r in res) for k in set(r['v_frame'] for r in res)}
        print(f"case {name}: weight {vw}; envelope {ve}; frame {vf}; attribution {[(tuple(u), int(n)) for u, n in zip(ua, ca)]}")
        if name.startswith('1'):
            print(f"   floors: control phase pair {np.median([r['phc_floor'] for r in res]):.2f} rad = {np.median([r['phc_floor'] for r in res])/(2*np.pi*TC*1e-3):.1f} kHz;"
                  f" R0 level se {np.median([r['R0_level_se'] for r in res], axis=0).round(4)}; w level se {np.median([r['w_level_se'] for r in res], axis=0).round(4)};"
                  f" R0 median {np.median([r['R0_med'] for r in res]):.4f} (true {A*np.exp(-TA/TAU):.4f}); r_a {np.median([r['ra_med'] for r in res]):.3f}; r_c {np.median([r['rc_med'] for r in res]):.3f}")
        if name.startswith('3') or name.startswith('6'):
            fl = [r['fixed_vs_live'] for r in res]
            print(f"   fixed-R0 reading calls a weight change at boundary 2 in {sum(x[1][0] for x in fl)} trials; live-R0 reading in {sum(x[1][1] for x in fl)}")


if __name__ == '__main__':
    run()
