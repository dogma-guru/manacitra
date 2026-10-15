# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""Waits in superposition (Amendment A18): Kickoff 47's Part B for any qubits, the wait test, and their analysis.

**Part B** (Kickoff 47, finding 13) puts each qubit of a group in superposition, lets it wait, and reads how much of
the superposition came back, with and without one refocusing pulse:

    Ramsey R(tau): H; delay tau; H; measure
    echo   E(tau): H; delay tau/2; X; delay tau/2; H; measure

The qubits of a group are not neighbours and run in parallel; every circuit runs twice, the second copy in reverse
order. Waits are in units of the backend's dt, even, so that tau/2 is whole. The analysis gives P(1) at every wait,
the Ramsey and echo losses at a reference wait (3.4 us in Kickoff 47) with their bootstrap intervals, and Kickoff 47's
rule for the kind of loss (`wait_loss_kind`), with its thresholds as parameters.

**The wait test** is a three-line circuit written here, on a chain L1-M-L3 that the user names. M, the middle line, is
put in superposition first and waits through three retirements of the end lines. Five logical qubits take turns on the
end lines, L1, L3, L1, L3, L1, each put in superposition and joined to M by one CZ. The first three are retired: each is
measured and its line reset while M waits as long as that measure plus reset on the backend, and each line is then used
again for the next logical qubit on it. The last two are measured at the end, and then M. Each end-line result is a
fair coin, and M's result is their parity, so the exact output is uniform over 32 of the 64 outcomes; F is the squared
Hellinger overlap with it. A phase phi gained by M while it waits takes F to cos²(phi / 2), however the phase is split
between the waits: RZ(pi/2) inside each wait, or inside only one, takes F from 1 to 0.5 (`wait_test_sensitivity`).

**The Ramsey over the circuit's wait** (Amendment A22) is the check of findings 14 to 19: M's Ramsey loss over the
wait test's own wait T_M, from the end of M's first H to the start of its last, as scheduled. `build_wait_ramsey`
builds it with the neighbours "active" (the default): the wait test as scheduled, with every CZ that touches M replaced
by a delay of the same length on both its qubits, so M does only H, wait, H, measure while the end lines do everything
they do in the circuit, at the same times. With the neighbours "idle", it builds 0.5.0's instrument, unchanged: Part
B's Ramsey on M alone at T_M (made even), the instrument of findings 13 and 14. `predicted_fidelity` gives the
prediction, F_pred = F_ref x (1 - (P(1) at T_M - P(1) at no wait)). A known phase, one RZ on M right after its first H,
is the probe of Kickoffs 51 to 53 (`phase`, on both builders and on `build_wait_test`).

**The check at the peak phase** (Amendment A24) is the procedure of Kickoffs 57 to 62, in two jobs. Job 1 is the
sweep (`phase_sweep`): the active-neighbour Ramsey at six phases, with the wait test at the same phases as an optional
second series (Kickoff 56's, which measures the leftover). Its fit (`sweep_fit`) gives the Ramsey's offset theta_R1, and
the peak phase phi* = 180 - theta_R1 (`peak_phase`) is where that Ramsey's loss is greatest. `peak_check` builds job 2
from job 1's counts: the check at phi*, with 0.6.0's check at +90 beside it, and the record of phi* to keep before job 2
runs. `readout_survey` and `readout_errors` measure every qubit's readout error (Kickoff 62's survey); the threshold of
any screen on it is the caller's.

**The boundary (D-02).** Nothing here is a reuse compiler, a port of a published reuse-compilation method, a
restore-and-route step, or an algorithm that decides where to measure and reset. The wait test's measures and resets are
written by hand and fixed in its definition, the same for every chain, and the user names the chain. The peak phase is
where the check is read on a chain the user names; nothing here chooses chains or placements.
"""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Sequence

import numpy as np

from .workload import hellinger_fidelity

#: Kickoff 47's Part B: its groups of non-neighbouring qubits on ibm_fez, its waits (dt of 4 ns) and its reference wait
KICKOFF_47_GROUPS = ((143, 131, 124), (142, 144, 125))
KICKOFF_47_WAITS_DT = (0, 250, 500, 850, 1000, 2000)
REFERENCE_WAIT_DT = 850
N_BOOT = 10_000
#: Kickoff 47's rule for the kind of loss on a qubit, its defaults: NOT REPRODUCED if the Ramsey loss's 90% interval
#: lies entirely below the floor; REFOCUSABLE if the interval of r - 3e lies entirely above 0 (e below a third of r);
#: NOT REFOCUSABLE if the interval of 3e - 2r lies entirely above 0 (e above two thirds of r); MIXED otherwise
LOSS_FLOOR = 0.10
REFOCUS_FACTOR = 3
PERSIST = (3, 2)
#: Kickoff 47's refocusing: XY4, with Y built as X after RZ(pi), the pulses a quarter-window apart
XY4_SPACING = (1 / 8, 1 / 4, 0, 1 / 4, 1 / 4, 0, 1 / 8)
#: The wait test's lines and classical bits: L1 = 0, M = 1, L3 = 2; the end-line results c0 to c4, then M's c5; the
#: first three rounds are retired (measured and reset, the line used again)
L1, M, L3 = 0, 1, 2
WAIT_TEST_ROUNDS = ((L1, 0), (L3, 1), (L1, 2), (L3, 3), (L1, 4))
WAIT_TEST_RETIRED = 3
WAIT_TEST_CLBITS = 6
#: What M's neighbours do in the Ramsey over the wait test's wait (Amendment A22): "active", what they do in the
#: wait test (the default from 0.6.0, findings 16 to 19), or "idle" in |0> (0.5.0's instrument, findings 13 and 14)
NEIGHBOURS = ("active", "idle")
#: The sweep's phases on M, in degrees (Kickoff 52's six, kept by Kickoffs 56 to 62), and the phase of 0.6.0's check
SWEEP_PHASES_DEG = (0, 60, 120, 180, 240, 300)
CHECK_PHASE_DEG = 90


# --------------------------------------------------------------------------- Part B
def even_wait(n_dt: float, granularity: int = 1) -> int:
    """A wait rounded to the nearest multiple of twice the backend's granularity, so that half of it is whole."""
    step = 2 * max(1, int(granularity))
    return int(round(n_dt / step)) * step


def part_b_circuit(n: int, wait_dt: int, variant: str):
    """One Part B circuit on n qubits of a group (qubit i measured into classical bit i): Ramsey ("R") or echo ("E")."""
    from qiskit import QuantumCircuit

    if variant not in ("R", "E"):
        raise ValueError("variant is 'R' (Ramsey) or 'E' (echo)")
    if wait_dt % 2:
        raise ValueError("the wait must be even in dt, so that the echo's half-waits are whole")
    qc = QuantumCircuit(n, n, name=f"{variant}{wait_dt}")
    for i in range(n):
        qc.h(i)
        if variant == "R":
            if wait_dt:
                qc.delay(wait_dt, i, unit="dt")
        else:
            if wait_dt:
                qc.delay(wait_dt // 2, i, unit="dt")
            qc.x(i)
            if wait_dt:
                qc.delay(wait_dt // 2, i, unit="dt")
        qc.h(i)
        qc.measure(i, i)
    return qc


def part_b(groups: Sequence[Sequence[int]] = KICKOFF_47_GROUPS, waits_dt=KICKOFF_47_WAITS_DT, granularity: int = 1):
    """Part B for these groups and waits, in Kickoff 47's order: every group, every wait, Ramsey then echo, then all of
    them again in reverse order (the second copy). Returns one entry per circuit: its label (group, numbered from 1;
    tau_dt; variant; copy), the circuit on the group's qubits in order, and the group as its layout."""
    waits = [even_wait(w, granularity) for w in waits_dt]
    first = [(g, w, v) for g in range(1, len(groups) + 1) for w in waits for v in ("R", "E")]
    out = []
    for copy, seq in ((1, first), (2, first[::-1])):
        for g, w, v in seq:
            qs = [int(q) for q in groups[g - 1]]
            out.append(
                {
                    "label": {"part": "B", "group": g, "tau_dt": w, "variant": v, "copy": copy},
                    "circuit": part_b_circuit(len(qs), w, v),
                    "layout": qs,
                }
            )
    return out


def to_backend(circuit, layout: Sequence[int], backend, seed_transpiler: int = 47):
    """A circuit translated to the backend's instructions at optimization level 0, on these physical qubits, as
    Kickoff 47 translated Part B."""
    from qiskit.transpiler import generate_preset_pass_manager

    pm = generate_preset_pass_manager(
        backend=backend, optimization_level=0, initial_layout=list(layout), seed_transpiler=seed_transpiler
    )
    out = pm.run(circuit)
    check_translation(circuit, out, layout)
    return out


def _two_qubit(circuit) -> dict[str, int]:
    out: dict[str, int] = {}
    for inst in circuit.data:
        if len(inst.qubits) == 2 and inst.operation.name != "barrier":
            out[inst.operation.name] = out.get(inst.operation.name, 0) + 1
    return out


def check_translation(logical, isa, layout: Sequence[int]) -> None:
    """Refuses (RuntimeError) a translation that routed the circuit: a swap, a final layout that moves a qubit, an
    instruction on a qubit not named, or a two-qubit gate count that differs from the circuit's (a swap translated to
    CZ shows here). Optimization level 0 routes only a circuit with a gate off the coupling map, and the circuits here
    have none; this makes sure no other circuit passes silently (A18, ruling R1)."""
    named = {int(q) for q in layout}
    problems = []
    if "swap" in isa.count_ops():
        problems.append("a swap was inserted")
    final = getattr(getattr(isa, "layout", None), "final_layout", None)
    if final is not None and any(isa.find_bit(v).index != p for v, p in final.get_virtual_bits().items()):
        problems.append("the final layout moves a qubit")
    used = {isa.find_bit(q).index for inst in isa.data for q in inst.qubits}
    if not used <= named:
        problems.append(f"instructions on qubits not named: {sorted(used - named)}")
    if _two_qubit(isa) != _two_qubit(logical):
        problems.append(f"two-qubit gates {_two_qubit(logical)} became {_two_qubit(isa)}")
    if problems:
        raise RuntimeError(f"refused: the translation onto {sorted(named)} routed the circuit: " + "; ".join(problems))


def structure(circuit) -> list[list]:
    """Every instruction of a circuit as [name, qubits, clbits, parameters], a delay's parameter being its length in
    dt: what the archive's record of Kickoff 47's Part B holds."""
    out = []
    for inst in circuit.data:
        op = inst.operation
        row = [
            op.name,
            [circuit.find_bit(b).index for b in inst.qubits],
            [circuit.find_bit(b).index for b in inst.clbits],
            [float(p) for p in op.params],
        ]
        if op.name == "delay":
            if op.unit != "dt":
                raise ValueError("a delay not in dt")
            row[3] = [int(op.duration)]
        out.append(row)
    return out


def _interval(name: str, ci) -> tuple[float, float]:
    try:
        lo, hi = (float(x) for x in ci)
    except (TypeError, ValueError):
        raise ValueError(f"{name}: an interval is two numbers, the lower first") from None
    if not (math.isfinite(lo) and math.isfinite(hi)) or lo > hi:
        raise ValueError(f"{name}: an interval's bounds must be finite, the lower not above the upper; got {ci!r}")
    return lo, hi


def wait_loss_kind(r_ci, r_minus_ke_ci, ke_minus_jr_ci, floor: float = LOSS_FLOOR) -> str:
    """Kickoff 47's rule for the kind of loss on one qubit, checked in this order, from the 90% intervals of the
    Ramsey loss r, of r - k e and of k' e - j r (Kickoff 47: k = 3, k' = 3, j = 2).

    Each interval is two finite bounds, the lower first, and the floor is finite; anything else is refused
    (ValueError). The comparisons are strict: an upper bound equal to the floor is not below it, and a lower bound of
    exactly 0 is not above 0."""
    r_ci = _interval("r", r_ci)
    r_minus_ke_ci = _interval("r - k e", r_minus_ke_ci)
    ke_minus_jr_ci = _interval("k' e - j r", ke_minus_jr_ci)
    if not math.isfinite(float(floor)):
        raise ValueError(f"the floor must be finite; got {floor!r}")
    if r_ci[1] < floor:
        return "NOT REPRODUCED"
    if r_minus_ke_ci[0] > 0:
        return "REFOCUSABLE"
    if ke_minus_jr_ci[0] > 0:
        return "NOT REFOCUSABLE"
    return "MIXED"


def _pct(a) -> list[float]:
    lo, hi = np.percentile(a, [5, 95])
    return [float(lo), float(hi)]


def _bits(key: str) -> str:
    return key.replace(" ", "")[::-1]


def ramsey_fit(waits_us, p1) -> dict | None:
    """A fit of a Ramsey curve, P(1) = P(1, 0) + a (1 - exp(-tau / T) cos(2 pi f tau)), tau in us and f in MHz: the best
    of eleven starting offsets from 0 to 0.5 MHz. A fit, beside a verdict, not a measurement of the offset."""
    from scipy.optimize import curve_fit

    t, y = np.array(waits_us, float), np.array(p1, float)
    c0 = y[0]

    def model(tt, a, T, f):
        return c0 + a * (1 - np.exp(-tt / T) * np.cos(2 * np.pi * f * tt))

    best = None
    for f0 in np.linspace(0.0, 0.5, 11):
        try:
            popt, pcov = curve_fit(model, t, y, p0=[0.3, 5.0, f0], bounds=([0, 0.05, 0], [0.7, 1e4, 1.0]), maxfev=20000)
        except Exception:
            continue
        sse = float(np.sum((model(t, *popt) - y) ** 2))
        if best is None or sse < best[0]:
            best = (sse, popt, pcov)
    if best is None:
        return None
    sse, popt, pcov = best
    err = np.sqrt(np.clip(np.diag(pcov), 0, None))
    return {
        "a": float(popt[0]),
        "T_us": float(popt[1]),
        "f_MHz": float(popt[2]),
        "a_err": float(err[0]),
        "T_err": float(err[1]),
        "f_err": float(err[2]),
        "sse": sse,
    }


def echo_fit(waits_us, p1) -> dict:
    """A fit of an echo curve to a decay, P(1) = P(1, 0) + a (1 - exp(-tau / T)), tau in us."""
    from scipy.optimize import curve_fit

    t, y = np.array(waits_us, float), np.array(p1, float)
    c0 = y[0]

    def model(tt, a, T):
        return c0 + a * (1 - np.exp(-tt / T))

    try:
        popt, pcov = curve_fit(model, t, y, p0=[0.3, 20.0], bounds=([0, 0.05], [0.7, 1e5]), maxfev=20000)
    except Exception as ex:
        return {"error": type(ex).__name__}
    err = np.sqrt(np.clip(np.diag(pcov), 0, None))
    return {"a": float(popt[0]), "T_us": float(popt[1]), "a_err": float(err[0]), "T_err": float(err[1])}


def part_b_losses(
    labels: Sequence[dict],
    counts: Sequence[dict],
    groups: Sequence[Sequence[int]],
    waits: Sequence,
    *,
    reference,
    seed: int,
    wait_key: str = "tau_dt",
    waits_us: Sequence[float] | None = None,
    n_boot: int = N_BOOT,
    floor: float = LOSS_FLOOR,
    refocus_factor: int = REFOCUS_FACTOR,
    persist: tuple[int, int] = PERSIST,
) -> dict:
    """Part B's analysis, per qubit, pooled over the two copies: Ramsey and echo P(1) at every wait, with 90%
    intervals (bootstrap: per circuit, the two copies drawn with replacement, each redrawn binomially for the qubit);
    the losses r and e at the reference wait, over the first wait (no wait); the kind of loss (`wait_loss_kind`);
    whether the Ramsey P(1) falls by more than 0.1 between two waits with separated intervals (a sign of oscillation);
    and a fit of each curve (`ramsey_fit`, `echo_fit`, on waits_us; beside the verdict).

    labels and counts: one per circuit position (Qiskit counts; bit i is the group's i-th qubit), the labels naming the
    part ("B"), the group (from 1), the wait under wait_key, the variant and the copy. The random draws come in a fixed
    order from `seed`: every group, every qubit in order, every wait, Ramsey then echo."""
    waits = list(waits)
    waits_us = list(waits) if waits_us is None else list(waits_us)
    base = waits[0]
    raw = defaultdict(dict)
    for lab, cts in zip(labels, counts):
        if lab.get("part") == "B":
            raw[(lab["group"], lab[wait_key], lab["variant"])][lab["copy"]] = cts
    rng = np.random.default_rng(seed)
    out = {}
    for g, qs in enumerate(groups, start=1):
        for i, q in enumerate(qs):
            P, B = {}, {}
            for tau in waits:
                for v in ("R", "E"):
                    ones, tots = [], []
                    for c in (1, 2):
                        cts = raw[(g, tau, v)][c]
                        ones.append(sum(n for k, n in cts.items() if _bits(k)[i] == "1"))
                        tots.append(sum(cts.values()))
                    ones, tots = np.array(ones), np.array(tots)
                    P[(tau, v)] = ones.sum() / tots.sum()
                    acc1, accn = np.zeros(n_boot), np.zeros(n_boot)
                    for _ in range(2):
                        pick = rng.integers(0, 2, size=n_boot)
                        acc1 += rng.binomial(tots[pick], ones[pick] / tots[pick])
                        accn += tots[pick]
                    B[(tau, v)] = acc1 / accn
            r, e = P[(reference, "R")] - P[(base, "R")], P[(reference, "E")] - P[(base, "E")]
            rb, eb = B[(reference, "R")] - B[(base, "R")], B[(reference, "E")] - B[(base, "E")]
            ci_r, ci_e = _pct(rb), _pct(eb)
            ci_rke = _pct(rb - refocus_factor * eb)
            ci_kejr = _pct(persist[0] * eb - persist[1] * rb)
            ram, ech = [P[(t, "R")] for t in waits], [P[(t, "E")] for t in waits]
            ram_ci = [_pct(B[(t, "R")]) for t in waits]
            osc = [
                [waits[a], waits[b], ram[a], ram[b]]
                for a in range(len(waits))
                for b in range(a + 1, len(waits))
                if ram[b] < ram[a] - 0.1 and ram_ci[b][1] < ram_ci[a][0]
            ]
            out[str(q)] = {
                "group": g,
                "ramsey_P1": dict(zip(map(str, waits), ram)),
                "ramsey_ci90": dict(zip(map(str, waits), ram_ci)),
                "echo_P1": dict(zip(map(str, waits), ech)),
                "echo_ci90": dict(zip(map(str, waits), [_pct(B[(t, "E")]) for t in waits])),
                "ramsey_loss": {str(t): P[(t, "R")] - P[(base, "R")] for t in waits},
                "echo_loss": {str(t): P[(t, "E")] - P[(base, "E")] for t in waits},
                "r": r,
                "r_ci90": ci_r,
                "e": e,
                "e_ci90": ci_e,
                "r_minus_ke_ci90": ci_rke,
                "ke_minus_jr_ci90": ci_kejr,
                "kind_of_loss": wait_loss_kind(ci_r, ci_rke, ci_kejr, floor),
                "ramsey_fit": ramsey_fit(waits_us, ram),
                "echo_fit": echo_fit(waits_us, ech),
                "oscillation_pairs": osc,
            }
    return out


# --------------------------------------------------------------------------- exact simulation
def exact_distribution(circuit) -> dict[str, float]:
    """The exact output distribution of a circuit with mid-circuit measurement and reset (no feed-forward), on the
    qubits it acts on: every measurement branches the state, every reset projects it and returns it to 0. Delays and
    barriers do nothing. Keys are Qiskit bitstrings over all classical bits (bit 0 rightmost); a bit never measured
    reads 0."""
    from qiskit.quantum_info import Operator

    acts = sorted(
        {
            circuit.find_bit(b).index
            for inst in circuit.data
            if inst.operation.name not in ("barrier", "delay")
            for b in inst.qubits
        }
    )
    pos = {q: i for i, q in enumerate(acts)}
    n = len(acts)
    idx = np.arange(2**n)
    start = np.zeros(2**n, complex)
    start[0] = 1.0
    branches = [(1.0, start, {})]

    def project(vec, k, outcome):
        return np.where(((idx >> k) & 1) == outcome, vec, 0)

    for inst in circuit.data:
        name = inst.operation.name
        if name in ("barrier", "delay"):
            continue
        qs = [pos[circuit.find_bit(b).index] for b in inst.qubits]
        new = []
        if name in ("measure", "reset"):
            k = qs[0]
            for p, vec, bits in branches:
                for outcome in (0, 1):
                    part = project(vec, k, outcome)
                    w = float(np.vdot(part, part).real)
                    if w <= 1e-14:
                        continue
                    part = part / math.sqrt(w)
                    if name == "measure":
                        new.append((p * w, part, {**bits, circuit.find_bit(inst.clbits[0]).index: outcome}))
                    else:
                        if outcome:
                            part = part[idx ^ (1 << k)]
                        new.append((p * w, part, bits))
            branches = new
            continue
        mat = Operator(inst.operation).data
        m = len(qs)
        for p, vec, bits in branches:
            t = vec.reshape((2,) * n)
            axes = [n - 1 - q for q in qs[::-1]]
            t = np.moveaxis(t, axes, range(m))
            shape = t.shape
            t = (mat @ t.reshape(2**m, -1)).reshape(shape)
            new.append((p, np.moveaxis(t, range(m), axes).reshape(-1), bits))
        branches = new
    out: dict[str, float] = {}
    for p, _, bits in branches:
        key = "".join(str(bits.get(c, 0)) for c in range(circuit.num_clbits - 1, -1, -1))
        out[key] = out.get(key, 0.0) + p
    return {k: v for k, v in out.items() if v > 1e-12}


def fidelity(counts_or_probs: dict, ideal: dict) -> float:
    """The squared Hellinger overlap of a measured distribution (counts or probabilities) with an ideal one."""
    keys = sorted(set(counts_or_probs) | set(ideal))
    tot = sum(counts_or_probs.values())
    p = np.array([ideal.get(k, 0.0) for k in keys])
    q = np.array([counts_or_probs.get(k, 0) / tot for k in keys])
    return hellinger_fidelity(p, q)


# --------------------------------------------------------------------------- the wait test
def wait_test_logical(phase_kicks: Sequence[float] = (0.0, 0.0, 0.0)):
    """The wait test on three lines, L1 = 0, M = 1, L3 = 2, written out by hand:

    H on M. Then five rounds, on L1, L3, L1, L3, L1: H on the end line, CZ between it and M; in the first three a
    barrier, the end line measured (c0, c1, c2) and reset while M waits, and a barrier, the line then taking the next
    logical qubit on it. The last two end-line qubits are measured at the end (c3, c4), then H on M and M measured (c5).
    5 CZ, 6 measures, 3 resets; no feed-forward.

    phase_kicks: an RZ angle applied to M inside each of the three waits (all 0 for the test itself), for the
    sensitivity check."""
    from qiskit import QuantumCircuit

    if len(phase_kicks) != 3:
        raise ValueError("one phase kick per wait, three waits")
    qc = QuantumCircuit(3, WAIT_TEST_CLBITS, name="wait-test")
    qc.h(M)
    for j, (end, c) in enumerate(WAIT_TEST_ROUNDS):
        qc.h(end)
        qc.cz(end, M)
        if j < WAIT_TEST_RETIRED:
            qc.barrier()
            qc.measure(end, c)
            if phase_kicks[j]:
                qc.rz(phase_kicks[j], M)
            qc.reset(end)
            qc.barrier()
    for end, c in WAIT_TEST_ROUNDS[WAIT_TEST_RETIRED:]:
        qc.measure(end, c)
    qc.h(M)
    qc.measure(M, WAIT_TEST_CLBITS - 1)
    return qc


def wait_test_ideal() -> dict[str, float]:
    """The wait test's exact output distribution: each end-line result 0 or 1 with probability 1/2, and M's result
    their parity (32 outcomes, 1/32 each)."""
    return exact_distribution(wait_test_logical())


def wait_test_sensitivity(angle: float = math.pi / 2) -> dict:
    """The exact F of the wait test with an RZ(angle) on M inside every wait, and inside only the first."""
    ideal = wait_test_ideal()
    return {
        "angle": angle,
        "F_each_wait": fidelity(exact_distribution(wait_test_logical((angle, angle, angle))), ideal),
        "F_one_wait": fidelity(exact_distribution(wait_test_logical((angle, 0.0, 0.0))), ideal),
    }


def xy4_sequence():
    """Kickoff 47's XY4 sequence: X, Y, X, Y, with Y built from native gates as X after RZ(pi)."""
    from qiskit.circuit.library import RZGate, XGate

    return [XGate(), RZGate(math.pi), XGate(), XGate(), RZGate(math.pi), XGate()]


def refocused(circuit, target, qubits: Sequence[int]):
    """XY4 refocusing pulses inserted by Qiskit's ALAPScheduleAnalysis and PadDynamicalDecoupling, with the target's
    durations, into every idle window on these qubits long enough to hold the sequence, reset-adjacent windows
    included: as Kickoff 47 refocused its chains."""
    from qiskit.transpiler import PassManager
    from qiskit.transpiler.passes import ALAPScheduleAnalysis, PadDynamicalDecoupling

    out = PassManager(
        [
            ALAPScheduleAnalysis(target=target),
            PadDynamicalDecoupling(
                target=target,
                dd_sequence=xy4_sequence(),
                qubits=list(qubits),
                spacing=list(XY4_SPACING),
                skip_reset_qubits=False,
            ),
        ]
    ).run(circuit)
    out._layout = circuit.layout  # padding adds gates on the same physical qubits; the layout record carries over
    return out


def scheduled(circuit, target):
    """The circuit scheduled as late as possible with the target's durations, its idle windows padded with delays."""
    from qiskit.transpiler import PassManager
    from qiskit.transpiler.passes import ALAPScheduleAnalysis, PadDelay

    out = PassManager([ALAPScheduleAnalysis(target=target), PadDelay(target=target)]).run(circuit)
    out._layout = circuit.layout
    return out


def idle_windows(circuit, qubit: int) -> list[int]:
    """The lengths, in dt, of the delays on one qubit of a scheduled circuit, in order."""
    return [
        int(inst.operation.duration)
        for inst in circuit.data
        if inst.operation.name == "delay" and circuit.find_bit(inst.qubits[0]).index == qubit
    ]


def build_wait_test(chain: Sequence[int], refocus: bool = False, backend=None, phase: float = 0.0):
    """The wait test on the chain L1-M-L3 the user names (three physical qubits, L1 and L3 each coupled to M).

    With a backend: translated to its instructions at optimization level 0 with the chain as the layout, so the
    measures and resets stay where the definition puts them; with refocus=True, XY4 pulses are then inserted into every
    idle window of the chain long enough to hold the sequence (`refocused`). Without a backend, the circuit on three
    lines, unplaced (refocusing needs the backend's durations).

    phase: a known phase, in radians, as one RZ on M right after its first H (Kickoffs 51 to 53's probe, Amendment
    A22), before any refocusing pulses are inserted. At 0, the default, nothing is inserted: the circuit is 0.5.0's."""
    chain = [int(q) for q in chain]
    if len(chain) != 3 or len(set(chain)) != 3:
        raise ValueError("the chain is three distinct qubits, L1-M-L3")
    qc = wait_test_logical()
    if backend is None:
        if refocus:
            raise ValueError("refocusing needs the backend's durations: pass backend")
        if phase:
            from qiskit.circuit import CircuitInstruction
            from qiskit.circuit.library import RZGate

            qc.data.insert(1, CircuitInstruction(RZGate(float(phase)), (qc.qubits[M],)))
        return qc
    t = backend.target
    gate = "cz"
    for a, b in ((chain[0], chain[1]), (chain[1], chain[2])):
        if t[gate].get((a, b)) is None and t[gate].get((b, a)) is None:
            raise ValueError(f"refused: {a}-{b} is not a coupler with a CZ on this backend")
    isa = to_backend(qc, chain, backend)
    if phase:
        isa = _rebuild(isa, _with_phase(_instructions(isa), chain[1], phase), isa.name)
    return refocused(isa, t, chain) if refocus else isa


# --------------------------------------------------------------------------- the Ramsey over the circuit's wait (A22)
def _instructions(circuit) -> list[tuple]:
    """A circuit as a list of (operation, physical qubits, clbits)."""
    return [
        (i.operation, [circuit.find_bit(q).index for q in i.qubits], [circuit.find_bit(c).index for c in i.clbits])
        for i in circuit.data
    ]


def _rebuild(src, ins, name: str):
    """A circuit with src's qubits, clbits, registers and layout record, holding these instructions."""
    out = src.copy_empty_like(name=name)
    for op, qs, cs in ins:
        out.append(op, [out.qubits[i] for i in qs], [out.clbits[j] for j in cs])
    out._layout = src.layout
    return out


def _with_phase(ins: list, m: int, phase: float) -> list:
    """RZ(phase) on M right after the last RZ of M's first H (RZ, SX, RZ in the backend's instructions)."""
    from qiskit.circuit.library import RZGate

    on_m = [k for k, (_, qs, _) in enumerate(ins) if qs == [m]]
    names = [ins[k][0].name for k in on_m]
    i = names.index("sx") if "sx" in names else -1
    if i < 1 or i + 1 >= len(names) or names[i - 1] != "rz" or names[i + 1] != "rz":
        raise RuntimeError("refused: M's first H is not RZ, SX, RZ in the backend's instructions")
    k = on_m[i + 1]
    return ins[: k + 1] + [(RZGate(float(phase)), [m], [])] + ins[k + 1 :]


def _duration(op, qs, target, dt) -> int:
    """An instruction's length in dt: a delay's own, 0 for a barrier or an RZ (a frame change), else the target's."""
    if op.name == "delay":
        if op.unit != "dt":
            raise ValueError("a delay not in dt")
        return int(op.duration)
    if op.name in ("barrier", "rz"):
        return 0
    return int(round(target[op.name][tuple(qs)].duration / dt))


def _chain_schedule(circuit, backend, chain: Sequence[int]) -> list[tuple]:
    """The circuit scheduled by `scheduled`, keeping only the instructions on the chain's qubits."""
    sch = scheduled(circuit, backend.target)
    return [x for x in _instructions(sch) if set(x[1]) <= set(chain)]


def _timeline(ins: list, target, dt, qubits: Sequence[int]) -> list[tuple]:
    """Start times, in dt, of a padded instruction list on these qubits: each qubit's instructions tile time, and every
    instruction on several qubits starts when all of them are free at once. Refuses (RuntimeError) a list that is not
    padded. Returns (index, name, qubits, clbits, start, duration) for each instruction on these qubits."""
    clock: dict = defaultdict(int)
    out = []
    for k, (op, qs, cs) in enumerate(ins):
        if not set(qs) & set(qubits):
            continue
        d = _duration(op, qs, target, dt)
        starts = {clock[q] for q in qs}
        if len(starts) != 1:
            raise RuntimeError(f"not padded at {op.name} on {qs}: clocks {sorted(starts)}")
        s = starts.pop()
        for q in qs:
            clock[q] = s + d
        out.append((k, op.name, qs, cs, s, d))
    return out


def _window(tl: list, m: int) -> dict:
    """M's window: from the end of its first SX (its first H) to the start of its last SX (its last H), in dt."""
    sx = [(s, d) for _, name, qs, _, s, d in tl if name == "sx" and qs == [m]]
    return {"start_dt": sx[0][0] + sx[0][1], "end_dt": sx[-1][0], "T_dt": sx[-1][0] - (sx[0][0] + sx[0][1])}


def build_wait_ramsey(chain: Sequence[int], backend, neighbours: str = "active", phase: float = 0.0):
    """M's Ramsey over the wait test's own wait T_M on the chain L1-M-L3, for the backend (Amendment A22). T_M runs from
    the end of M's first H to the start of its last, in the wait test without refocusing as `scheduled` on the
    backend's target.

    neighbours="active" (the default): the wait test as scheduled, with every two-qubit gate that touches M replaced by
    a delay of the same length on both its qubits, and every other instruction left at its scheduled time. M then does
    only H, wait, H, measure (into the wait test's c5), and L1 and L3 do everything they do in the wait test, at the
    same times: Kickoffs 50 to 53's R1, the instrument of findings 16 to 19.

    neighbours="idle": 0.5.0's instrument, unchanged: Part B's Ramsey (`part_b_circuit`) on M alone at T_M made even
    (`even_wait`), translated by `to_backend`, the neighbours idle in |0>: the instrument of findings 13 and 14.

    phase: a known phase, in radians, as one RZ on M right after its first H, the probe of Kickoffs 51 to 53. At 0, the
    default, nothing is inserted. The prediction from either Ramsey is `predicted_fidelity`."""
    if neighbours not in NEIGHBOURS:
        raise ValueError(f"neighbours is one of {NEIGHBOURS}; got {neighbours!r}")
    if backend is None:
        raise ValueError("the Ramsey over the circuit's wait needs the backend's durations: pass backend")
    chain = [int(q) for q in chain]
    plain = build_wait_test(chain, False, backend)
    t, dt, m = backend.target, backend.dt, chain[1]
    T = _window(_timeline(_chain_schedule(plain, backend, chain), t, dt, chain), m)["T_dt"]
    if neighbours == "idle":
        wait_dt = even_wait(T, getattr(t, "granularity", 1) or 1)
        qc = part_b_circuit(1, wait_dt, "R")
        if phase:
            from qiskit.circuit import CircuitInstruction
            from qiskit.circuit.library import RZGate

            qc.data.insert(1, CircuitInstruction(RZGate(float(phase)), (qc.qubits[0],)))
        return to_backend(qc, [m], backend)
    source = _rebuild(plain, _with_phase(_instructions(plain), m, phase), plain.name) if phase else plain
    ins = []
    for op, qs, cs in _chain_schedule(source, backend, chain):
        if len(qs) == 2 and op.name != "barrier" and m in qs:
            from qiskit.circuit import Delay

            d = _duration(op, qs, t, dt)
            ins += [(Delay(d, unit="dt"), [q], []) for q in qs]
        else:
            ins.append((op, qs, cs))
    return _rebuild(plain, ins, "wait-ramsey")


def predicted_fidelity(f_ref: float, p1_wait: float, p1_zero: float) -> float:
    """The wait test's predicted F without refocusing, F_pred = F_ref x (1 - loss), loss = M's P(1) after the Ramsey
    over the circuit's wait (`build_wait_ramsey`) minus its P(1) with no wait: finding 14's rule with the idle-neighbour
    Ramsey, Kickoff 53's revised rule with the active one (finding 19). f_ref is the wait test's F with refocusing. A
    prediction: the rules test the residual d = F_no - F_pred against a margin fixed before the run."""
    vals = [float(x) for x in (f_ref, p1_wait, p1_zero)]
    if not all(math.isfinite(v) and 0.0 <= v <= 1.0 for v in vals):
        raise ValueError(f"F_ref and the two P(1) are probabilities, finite and in [0, 1]; got {vals}")
    return vals[0] * (1 - (vals[1] - vals[2]))


def wait_lengths(backend, chain: Sequence[int]) -> dict:
    """The waits M sees, from the backend's target: each end line's measure plus reset, in dt and in us."""
    t = backend.target
    out = {}
    for name, q in (("L1", chain[0]), ("L3", chain[2])):
        d = t["measure"][(q,)].duration + t["reset"][(q,)].duration
        out[name] = {"qubit": int(q), "dt": int(round(d / backend.dt)), "us": d * 1e6}
    return out


# --------------------------------------------------------------------------- the check at the peak phase (A24)
def phase_sweep(chain: Sequence[int], backend, wait_test: bool = False) -> list[dict]:
    """Job 1 of the check at the peak phase (Kickoffs 57 to 62): on the chain L1-M-L3 the user names, the
    active-neighbour Ramsey (`build_wait_ramsey`, its default) at each phase of SWEEP_PHASES_DEG, one RZ(phi) on M right
    after its first H. With wait_test=True, the wait test without refocusing (`build_wait_test`) at the same phases
    follows, Kickoff 56's second series, which measures the leftover (`sweep_fit`, `leftover`).

    Returns one entry per circuit: its label (the circuit, "R1" or "W-no", phi in degrees, and the classical bit that
    holds M's result, `m_clbit`) and the circuit. Every circuit has the wait test's six classical bits; M's is c5."""
    out = []
    series = (("R1", False), ("W-no", True)) if wait_test else (("R1", False),)
    for name, is_wait_test in series:
        for deg in SWEEP_PHASES_DEG:
            phase = math.radians(deg)
            qc = (
                build_wait_test(chain, False, backend, phase)
                if is_wait_test
                else build_wait_ramsey(chain, backend, phase=phase)
            )
            label = {"circuit": name, "phi_deg": deg, "m_clbit": WAIT_TEST_CLBITS - 1}
            out.append({"label": label, "circuit": qc})
    return out


def sweep_fit(y, series: str = "R1") -> dict:
    """The fit of Kickoffs 52 and 56 to 62, fixed before their data: y(phi) = c + b cos(phi) + s sin(phi) by ordinary
    least squares over the six phases of SWEEP_PHASES_DEG, in their order.

    For a Ramsey (series "R1" or "R0"), y is M's P(1), or its loss; its offset, the Ramsey's offset, is
    theta = atan2(s, -b), so that its loss is least at phi = -theta and greatest at 180 - theta. For the wait test
    (series "W-no"), y is F without refocusing and theta = atan2(-s, b), so that F is greatest at phi = -theta. Returns
    c, b, s, the amplitude sqrt(b^2 + s^2), theta in degrees, the residuals at each phase and the largest |residual|. A
    fit, beside a verdict, not a measurement of the offset's cause."""
    if series not in ("R1", "R0", "W-no"):
        raise ValueError(f"series is 'R1', 'R0' or 'W-no'; got {series!r}")
    y = np.asarray(y, float)
    if y.shape != (len(SWEEP_PHASES_DEG),) or not np.all(np.isfinite(y)):
        raise ValueError(f"one finite value per phase of {SWEEP_PHASES_DEG}; got {y.tolist()}")
    rad = np.radians(SWEEP_PHASES_DEG)
    x = np.column_stack([np.ones(len(rad)), np.cos(rad), np.sin(rad)])
    c, b, s = (float(v) for v in y @ np.linalg.pinv(x).T)
    theta = math.degrees(math.atan2(-s, b) if series == "W-no" else math.atan2(s, -b))
    resid = y - x @ np.array([c, b, s])
    return {
        "c": c,
        "b": b,
        "s": s,
        "amplitude": math.hypot(b, s),
        "theta_deg": theta,
        "residuals": resid.tolist(),
        "max_abs_residual": float(np.max(np.abs(resid))),
    }


def peak_phase(theta_r1_deg: float) -> int:
    """The peak phase phi* = 180 - theta_R1, the phase at which the active-neighbour Ramsey's loss is greatest, from the
    Ramsey's offset theta_R1 (`sweep_fit`): wrapped to [0, 360) and rounded to the nearest whole degree, halves up
    (Kickoff 57's procedure, from the point estimate only)."""
    x = (180.0 - float(theta_r1_deg)) % 360.0
    return int(math.floor(x + 0.5)) % 360


def leftover(theta_w_deg: float, theta_r1_deg: float) -> float:
    """The leftover: the wait test's offset minus the active-neighbour Ramsey's, theta_W - theta_R1, wrapped to
    (-180, +180] degrees (Kickoff 56)."""
    w = (float(theta_w_deg) - float(theta_r1_deg) + 180.0) % 360.0 - 180.0
    return w + 360.0 if w <= -180.0 else w


def _pooled(counts) -> list[dict]:
    """A counts dictionary, or a list of them (the copies of one circuit), as a list."""
    return [counts] if isinstance(counts, dict) else list(counts)


def _p1_of_bit(counts, clbit: int) -> float:
    """The fraction of shots with classical bit `clbit` read 1, the copies pooled (bit 0 rightmost)."""
    ones = tot = 0
    for cts in _pooled(counts):
        for key, n in cts.items():
            ones += n if _bits(key)[clbit] == "1" else 0
            tot += n
    if not tot:
        raise ValueError("no shots")
    return ones / tot


def peak_check(chain: Sequence[int], backend, sweep_counts: dict) -> dict:
    """Job 2 of the check at the peak phase, from job 1's counts (Kickoffs 57 to 62). sweep_counts maps each phase of
    SWEEP_PHASES_DEG, in degrees, to the counts of `phase_sweep`'s R1 circuit at that phase (a dictionary, or a list
    of them, one per copy, pooled).

    The peak: M's P(1) at each phase (bit 5), the fit (`sweep_fit`), the Ramsey's offset theta_R1 and phi*
    (`peak_phase`), from the point estimate. The circuits: the check at phi*, W-no(phi*) and R1(phi*)
    (`build_wait_test`, `build_wait_ramsey`); 0.6.0's check at +90 beside it, W-no(+90) and R1(+90); the reference
    W-ref, the wait test with refocusing; and Z, M's zero-wait baseline, H, H and a measure on M alone
    (`part_b_circuit` with no wait, translated onto M, its result in c0). Each entry's label names the circuit, its
    role ("peak", "plus90", "ref" or "zero"), phi in degrees and `m_clbit`.

    Returns {"peak": ..., "circuits": [...]}. Record the peak before job 2 runs: phi* is fixed by job 1, not chosen
    after job 2. Each cell's prediction is `predicted_fidelity`(F_ref, R1's P(1), Z's P(1)); one shot count per job
    (qiskit-ibm-runtime 0.49.0 deprecates different shot counts across the circuits of one job)."""
    chain = [int(q) for q in chain]
    missing = [p for p in SWEEP_PHASES_DEG if p not in sweep_counts]
    if missing:
        raise ValueError(f"the sweep's counts at every phase of {SWEEP_PHASES_DEG}; missing {missing}")
    p1 = [_p1_of_bit(sweep_counts[p], WAIT_TEST_CLBITS - 1) for p in SWEEP_PHASES_DEG]
    fit = sweep_fit(p1, "R1")
    phi_star = peak_phase(fit["theta_deg"])
    peak = {
        "chain": chain,
        "M": chain[1],
        "P1": dict(zip(map(str, SWEEP_PHASES_DEG), p1)),
        "fit": fit,
        "theta_R1_deg": fit["theta_deg"],
        "phi_star_unrounded_deg": (180.0 - fit["theta_deg"]) % 360.0,
        "phi_star_deg": phi_star,
    }
    m = WAIT_TEST_CLBITS - 1
    built = []
    for role, deg in (("peak", phi_star), ("plus90", CHECK_PHASE_DEG)):
        phase = math.radians(deg)
        built.append(("W-no", role, deg, m, build_wait_test(chain, False, backend, phase)))
        built.append(("R1", role, deg, m, build_wait_ramsey(chain, backend, phase=phase)))
    built.append(("W-ref", "ref", 0, m, build_wait_test(chain, True, backend)))
    built.append(("Z", "zero", 0, 0, to_backend(part_b_circuit(1, 0, "R"), [chain[1]], backend)))
    circuits = [
        {"label": {"circuit": name, "role": role, "phi_deg": deg, "m_clbit": clbit}, "circuit": qc}
        for name, role, deg, clbit, qc in built
    ]
    return {"peak": peak, "circuits": circuits}


# --------------------------------------------------------------------------- the readout survey (A24)
def readout_survey(backend) -> list[dict]:
    """Kickoff 62's survey: two circuits on every qubit of the backend, qubit i on physical qubit i and measured into
    classical bit i, translated by `to_backend`. S0 measures every qubit with no gate, for P(1|0); S1 puts one X on
    every qubit, then the same measures, for P(0|1). No instruction acts on two or more qubits. Returns one entry per
    circuit, its label and the circuit."""
    from qiskit import QuantumCircuit

    n = int(backend.num_qubits)
    out = []
    for name in ("S0", "S1"):
        qc = QuantumCircuit(n, n, name=name)
        if name == "S1":
            for i in range(n):
                qc.x(i)
        for i in range(n):
            qc.measure(i, i)
        out.append({"label": {"circuit": name, "n_qubits": n}, "circuit": to_backend(qc, list(range(n)), backend)})
    return out


def readout_errors(counts_zero, counts_one, limit: float | None = None) -> dict:
    """Each qubit's readout error from the survey's counts (Kickoff 62): P(1|0) from S0, P(0|1) from S1, each argument
    a counts dictionary or a list of them (the copies, pooled), and e = (P(1|0) + P(0|1)) / 2, the average that IBM's
    published readout error is defined as. Qubit i is classical bit i.

    limit: a screen the caller chooses (Kickoff 62's was 0.03); with it, each qubit's entry says whether e is above it.
    The package fixes no threshold. A measurement at one time: it says nothing about why it differs from any published
    value. Returns {str(qubit): {"P1_given_0", "P0_given_1", "e"[, "above_limit"]}}."""
    if limit is not None and not math.isfinite(float(limit)):
        raise ValueError(f"the limit must be finite; got {limit!r}")

    def tally(counts):
        ones, tot = None, 0
        for cts in _pooled(counts):
            for key, n in cts.items():
                bits = np.frombuffer(_bits(key).encode(), dtype=np.uint8).astype(np.int64) - 48
                ones = bits * n if ones is None else ones + bits * n
                tot += n
        if not tot:
            raise ValueError("no shots")
        return ones / tot

    p10, p1_given_1 = tally(counts_zero), tally(counts_one)
    if p10.shape != p1_given_1.shape:
        raise ValueError("S0 and S1 hold different numbers of classical bits")
    out = {}
    for q, (a, b) in enumerate(zip(p10.tolist(), (1 - p1_given_1).tolist())):
        row = {"P1_given_0": a, "P0_given_1": b, "e": (a + b) / 2}
        if limit is not None:
            row["above_limit"] = row["e"] > float(limit)
        out[str(q)] = row
    return out


# --------------------------------------------------------------------------- a run: the job and its analysis
def default_groups(chain: Sequence[int]) -> tuple[tuple[int, ...], tuple[int, ...]]:
    """Part B's groups for a chain L1-M-L3: M alone, then the two end lines, which are not neighbours."""
    return (int(chain[1]),), (int(chain[0]), int(chain[2]))


def wait_run(
    chain: Sequence[int],
    backend,
    groups: Sequence[Sequence[int]] | None = None,
    waits_dt=KICKOFF_47_WAITS_DT,
    copies: int = 5,
    shots_wait: int = 10_000,
    shots_b: int = 4_000,
    seed: int = 18,
):
    """One job's circuits for the backend: the wait test without and with refocusing on the chain, `copies` times,
    each copy's two in an order drawn from `seed`; then Part B on the groups (default: M alone, then L1 and L3).
    Returns (circuits, labels, shots), each a list with one entry per circuit."""
    groups = [tuple(int(q) for q in g) for g in (groups or default_groups(chain))]
    gran = getattr(backend.target, "granularity", 1) or 1
    circuits, labels, shots = [], [], []
    variants = {"no": build_wait_test(chain, False, backend), "refocus": build_wait_test(chain, True, backend)}
    rng = np.random.default_rng(seed)
    for c in range(1, copies + 1):
        for i in rng.permutation(2):
            v = ("no", "refocus")[i]
            circuits.append(variants[v])
            labels.append({"part": "W", "chain": [int(q) for q in chain], "variant": v, "copy": c})
            shots.append(shots_wait)
    for e in part_b(groups, waits_dt, gran):
        circuits.append(to_backend(e["circuit"], e["layout"], backend))
        labels.append({**e["label"], "qubits": e["layout"]})
        shots.append(shots_b)
    return circuits, labels, shots


def analyse_wait_run(labels: Sequence[dict], counts: Sequence[dict], dt: float, seed: int = 4747) -> dict:
    """A run's analysis: the wait test's F without and with refocusing (pooled over copies, and per copy) and the gain
    from refocusing; Part B's losses per qubit (`part_b_losses`), at the wait nearest 3.4 us, with Kickoff 47's rule."""
    ideal = wait_test_ideal()
    pooled: dict = {"no": {}, "refocus": {}}
    per_copy: dict = {"no": [], "refocus": []}
    for lab, cts in zip(labels, counts):
        if lab.get("part") != "W":
            continue
        out = {}
        for key, n in cts.items():
            k = key.replace(" ", "")[-WAIT_TEST_CLBITS:]
            out[k] = out.get(k, 0) + n
            pooled[lab["variant"]][k] = pooled[lab["variant"]].get(k, 0) + n
        per_copy[lab["variant"]].append(fidelity(out, ideal))
    result: dict = {}
    if pooled["no"] and pooled["refocus"]:
        f0, f1 = fidelity(pooled["no"], ideal), fidelity(pooled["refocus"], ideal)
        result["wait_test"] = {"F_no": f0, "F_refocus": f1, "gain": f1 - f0, "F_per_copy": per_copy}
    b = [lab for lab in labels if lab.get("part") == "B"]
    if b:
        groups: dict = {}
        for lab in b:
            groups.setdefault(lab["group"], tuple(lab["qubits"]))
        waits = sorted({lab["tau_dt"] for lab in b})
        ref = min(waits, key=lambda w: abs(w * dt - 3.4e-6))
        result["part_b"] = {
            "reference_wait_dt": ref,
            "qubits": part_b_losses(
                labels,
                counts,
                [groups[g] for g in sorted(groups)],
                waits,
                reference=ref,
                seed=seed,
                wait_key="tau_dt",
                waits_us=[w * dt * 1e6 for w in waits],
            ),
        }
    return result
