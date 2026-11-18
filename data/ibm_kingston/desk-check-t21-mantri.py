"""Test 21: Mantri's desk check of the monitor read, before the hash.

A stationary two-state telegraph process is sampled shot by shot in sweep order (shot index outer, positions inner),
at test 10's measured time per shot on ibm_kingston. The read is the rule's section 5, with the package's own
functions (`sharing_ratio`, `two_state_reading`, `time_average_sd` in manacitra's wait.py).

Usage: python desk-check-t21-mantri.py <path to manacitra/src>
"""
import sys, json, numpy as np
sys.path.insert(0, sys.argv[1])
from manacitra import wait as W

T_SHOT = 317e-6                      # 95 s for 300,000 shots (test 10, job 1)
LAYOUTS = {"job 2 (8 repeats, 20 positions, 3,200 shots)": (8, 3200),
           "job 3 (16 repeats, 36 positions, 1,800 shots)": (16, 1800)}
N_PERM, GATE = 200, 0.55

def telegraph(rng, n, d_high, d_low):
    """The state at each executed shot: dwell times drawn exponentially, in units of the time per shot."""
    s = np.ones(n, bool)
    if d_high is None:               # one state only
        return s
    cur = rng.random() < d_high / (d_high + d_low)
    need = int(4 * n * T_SHOT / (d_high + d_low)) + 64
    while True:
        hi = rng.exponential(d_high / T_SHOT, need)
        lo = rng.exponential(d_low / T_SHOT, need)
        dw = np.empty(2 * need)
        dw[0::2], dw[1::2] = (hi, lo) if cur else (lo, hi)
        edges = np.cumsum(dw)
        if edges[-1] >= n:
            break
        need *= 2
    idx = np.searchsorted(edges, np.arange(n), side="right")
    return (idx % 2 == 0) == cur

def read(rng, n_rep, shots, d_high, d_low, q_high, q_low):
    n_pos = 4 + 2 * n_rep
    state = telegraph(rng, n_pos * shots, d_high, d_low).reshape(shots, n_pos)
    y_pos = [3 + 2 * k for k in range(n_rep)]        # 0, 1 readout; X at even, Y at odd; last two readout
    M = (rng.random((shots, n_rep)) < np.where(state[:, y_pos], q_high, q_low)).T.astype(float)
    sr = W.sharing_ratio(M)
    P = rng.permuted(np.repeat(M[None], N_PERM, axis=0), axis=2)      # each row's shot order permuted independently
    perm = P.mean(axis=1).var(axis=1, ddof=1) / sr["v_ind"]             # the rows' means are unchanged, so v_ind is too
    rho = (sr["ratio"] - 1) / (n_rep - 1)
    if sr["ratio"] > perm.max() and rho >= 0.05:
        word = "SHARED"
    elif sr["ratio"] <= np.percentile(perm, 95):
        word = "NO SHARED STATE SEEN"
    else:
        word = "UNDECIDED"
    out = {"word": word, "ratio": sr["ratio"], "rho": rho}
    if word == "SHARED":
        m = M.mean(axis=0)
        ts = W.two_state_reading(m, n_pos * T_SHOT, v_ind=sr["v_ind"])
        high = m > ts["threshold"]
        sep = float(M[:, high].mean() - M[:, ~high].mean()) if high.any() and (~high).any() else 0.0
        out.update(timing="TIMED" if ts["lag"] >= 3 else "FASTER THAN THE CLOCK", lag=ts["lag"],
                   tau=ts["tau_c_s"], duty=ts["duty"], separation=sep, duty_read=sep >= GATE)
    return out

def case(label, d_high, d_low, q_high, q_low, seed, n=100):
    for name, (n_rep, shots) in LAYOUTS.items():
        rng = np.random.default_rng(seed)
        R = [read(rng, n_rep, shots, d_high, d_low, q_high, q_low) for _ in range(n)]
        row = {"case": label, "layout": name, "n": n}
        for w in ("SHARED", "UNDECIDED", "NO SHARED STATE SEEN"):
            row[w] = sum(r["word"] == w for r in R)
        S = [r for r in R if r["word"] == "SHARED"]
        row["TIMED"] = sum(r["timing"] == "TIMED" for r in S)
        row["median ratio"] = round(float(np.median([r["ratio"] for r in R])), 2)
        row["median rho"] = round(float(np.median([r["rho"] for r in R])), 3)
        if S and d_high is not None:
            tau_true = 1 / (1 / d_high + 1 / d_low)
            b_true = d_high / (d_high + d_low)
            row["tau true (s)"] = round(tau_true, 4)
            row["median lag"] = float(np.median([r["lag"] for r in S]))
            row["median tau (s)"] = round(float(np.median([r["tau"] for r in S])), 4)
            row["tau within a factor 1.5"] = sum(tau_true / 1.5 < r["tau"] < 1.5 * tau_true for r in S)
            row["duty read"] = sum(r["duty_read"] for r in S)
            row["duty within 0.05, where read"] = sum(r["duty_read"] and abs(r["duty"] - b_true) < 0.05 for r in S)
            row["median separation"] = round(float(np.median([r["separation"] for r in S])), 2)
        print(json.dumps(row))

if __name__ == "__main__":
    case("1 October's dwells (0.050 and 0.187 s), emissions 0.80 and 0.15", 0.050, 0.187, 0.80, 0.15, 21501)
    case("2 October's dwells, emissions 0.72 and 0.22", 0.050, 0.187, 0.72, 0.22, 21502)
    case("3 October's dwells, emissions 0.65 and 0.30", 0.050, 0.187, 0.65, 0.30, 21503)
    case("4 twice as fast (0.025 and 0.094 s), emissions 0.80 and 0.15", 0.025, 0.094, 0.80, 0.15, 21504)
    case("5 ten times as fast (0.005 and 0.019 s), emissions 0.80 and 0.15", 0.005, 0.019, 0.80, 0.15, 21505)
    case("6 as slow as fez 143 (0.29 and 0.48 s), emissions 0.85 and 0.10", 0.29, 0.48, 0.85, 0.10, 21506)
    case("7 one state, no switching, emission 0.80", None, None, 0.80, 0.80, 21507)
    case("8 a small duty, 0.06 (0.012 and 0.187 s), emissions 0.80 and 0.15", 0.012, 0.187, 0.80, 0.15, 21508)
