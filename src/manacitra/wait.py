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

**The monitor and the execution spans** (Amendment A27). `ramsey_monitor` builds every qubit of a set at its own wait
in one circuit, in two quadratures, repeated in a fixed order between the readout circuits. `span_assignment` reads
the provider's execution record: each position's span, each repeat's span or its straddling, and the gaps.
`monitor_phase` gives each repeat's phase and length and the switches between consecutive repeats, within a span or at
a boundary, and `monitor_weight` the weight at the antiphase wait; the floors and thresholds are the caller's.

**The boundary (D-02).** Nothing here is a reuse compiler, a port of a published reuse-compilation method, a
restore-and-route step, or an algorithm that decides where to measure and reset. The wait test's measures and resets are
written by hand and fixed in its definition, the same for every chain, and the user names the chain. The peak phase is
where the check is read on a chain the user names; nothing here chooses chains or placements.
"""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Sequence
from datetime import UTC

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


# --------------------------------------------------------------------------- the two-quadrature Ramsey (A25)
#: The quadratures of the two-quadrature Ramsey and their phase in the models: X is H, wait, H; Y is the same with an
#: S-dagger before the final H, so its fringe is X's with sin in place of cos, the cosine's phase minus pi/2
RAMSEY_XY_QUADRATURES = ("X", "Y")
RAMSEY_XY_PHASE = {"X": 0.0, "Y": -math.pi / 2}
#: The two models' parameters, t in us and frequencies in MHz: S, one line; P, two fixed lines at Delta0 + delta and
#: Delta0 - delta with a free weight b on the upper one
RAMSEY_XY_NAMES = {
    "S": ("c", "A", "tau_us", "Delta_MHz", "phi0_rad"),
    "P": ("c", "A", "tau_prime_us", "Delta0_MHz", "phi0_rad", "delta_MHz", "b"),
}
#: S's bounds, and P's shared ones; P's Delta0 and delta are bounded by the fit set's band (`ramsey_xy_band`)
RAMSEY_XY_S_BOUNDS = ((0.0, 0.0, 0.5, -0.3, 0.0), (1.0, 1.0, 1e4, 0.3, 2 * math.pi))
#: The starts, as test 7's rule fixes them: 40 for S, uniform within its bounds; for P, 20 from the S fit (Delta0 at
#: Delta_S and Delta_S +- delta_s for each delta_s, at each b, then the two extra (delta, b) at Delta_S) and 20 uniform
RAMSEY_XY_S_STARTS = 40
RAMSEY_XY_P_RANDOM_STARTS = 20
RAMSEY_XY_P_GRID_DELTA_MHZ = (0.005, 0.015, 0.05)
RAMSEY_XY_P_GRID_B = (0.5, 0.3)
RAMSEY_XY_P_GRID_EXTRA = ((0.008, 0.5), (0.030, 0.5))


def ramsey_xy(qubit: int, backend, waits_us: Sequence[float], readout: bool = False) -> list[dict]:
    """The two-quadrature Ramsey on one qubit (test 7, finding 28), for the backend, at each wait in µs: X, Part B's
    Ramsey on one qubit (`part_b_circuit`(1, wait_dt, "R"): H, the wait, H, measure), and Y, the same with an S-dagger
    inserted right before the final H, each translated onto the qubit by `to_backend`, the other qubits idle in |0>.
    Each wait is converted with the backend's dt and made even (`even_wait`, the target's granularity), as
    `build_wait_ramsey` makes its idle wait. With readout=True, the two readout circuits on the qubit follow: P10, a
    measure with no gate (P(1|0)), and P01, X then a measure (P(0|1)).

    Returns one entry per circuit, X at every wait, then Y at every wait, then P10 and P01: its label (the circuit, the
    quadrature, the requested wait, the wait in dt, the wait as scheduled on the target, from the end of the qubit's
    first SX to the start of its last, in dt and in µs, the qubit and its classical bit, 0) and the circuit."""
    from qiskit import QuantumCircuit
    from qiskit.circuit import CircuitInstruction
    from qiskit.circuit.library import SdgGate

    q = int(qubit)
    t, dt = backend.target, backend.dt
    gran = getattr(t, "granularity", 1) or 1
    waits = [float(w) for w in waits_us]
    if not all(math.isfinite(w) and w >= 0 for w in waits):
        raise ValueError(f"the waits are finite and not negative, in µs; got {waits}")
    out = []
    for quad in RAMSEY_XY_QUADRATURES:
        for w in waits:
            wait_dt = even_wait(w * 1e-6 / dt, gran)
            qc = part_b_circuit(1, wait_dt, "R")
            if quad == "Y":
                k = max(i for i, x in enumerate(qc.data) if x.operation.name == "h")
                qc.data.insert(k, CircuitInstruction(SdgGate(), (qc.qubits[0],)))
                qc.name = f"Y{wait_dt}"
            isa = to_backend(qc, [q], backend)
            T = _window(_timeline(_chain_schedule(isa, backend, [q]), t, dt, [q]), q)["T_dt"]
            label = {
                "circuit": quad,
                "quadrature": quad,
                "t_requested_us": w,
                "wait_dt": wait_dt,
                "scheduled_wait_dt": T,
                "scheduled_wait_us": T * dt * 1e6,
                "qubit": q,
                "clbit": 0,
            }
            out.append({"label": label, "circuit": isa})
    if readout:
        for name in ("P10", "P01"):
            qc = QuantumCircuit(1, 1, name=f"{name}-{q}")
            if name == "P01":
                qc.x(0)
            qc.measure(0, 0)
            label = {"circuit": name, "quadrature": None, "t_requested_us": None, "qubit": q, "clbit": 0}
            out.append({"label": label, "circuit": to_backend(qc, [q], backend)})
    return out


def _ramsey_s(p, t, ph):
    c, A, tau, D, p0 = p
    return c + A * np.exp(-t / tau) * np.cos(2 * np.pi * D * t + p0 + ph)


def _ramsey_p(p, t, ph):
    c, A, tau, D, p0, dl, b = p
    env = A * np.exp(-t / tau)
    return c + env * (
        b * np.cos(2 * np.pi * (D + dl) * t + p0 + ph) + (1 - b) * np.cos(2 * np.pi * (D - dl) * t + p0 + ph)
    )


def ramsey_xy_band(fit_waits_us) -> dict:
    """The band of line frequencies a fit set can tell apart. Waits a spacing s apart fix a line's frequency only
    modulo 1 / s: a line at f and one at f + 1 / s are the same function at every fitted wait. P's lines are therefore
    held inside the band |f| <= 1 / (2 s), the fit set's Nyquist frequency, by bounding Delta0 to +-1 / (4 s) and delta
    to [0, 1 / (4 s)], so that |Delta0| + delta never exceeds it. s is the smallest spacing of the fitted waits, in µs
    (rounded to 1e-9 µs); at test 7's 2 µs the band is 250 kHz and each bound 125 kHz."""
    w = np.unique(np.round(np.asarray(fit_waits_us, float).ravel(), 9))
    if len(w) < 2:
        raise ValueError("a fit set of at least two distinct waits")
    s = float(np.min(np.diff(w)))
    return {
        "spacing_us": s,
        "nyquist_MHz": 1 / (2 * s),
        "Delta0_bound_MHz": 1 / (4 * s),
        "delta_bound_MHz": 1 / (4 * s),
    }


def _p1_sigma(y, n):
    """The binomial standard error of a P(1), with p (1 - p) floored at 1/n."""
    return np.sqrt(np.clip(y * (1 - y), 1 / n, None) / n)


def _best_of(model, starts, bounds, t, ph, y, sig) -> tuple:
    """Weighted least squares from each start (max_nfev 4,000), the best kept: (the result, the starts that failed to
    converge, counting least_squares' status 0 and an exception)."""
    from scipy.optimize import least_squares

    best, failed = None, 0
    for p in starts:
        try:
            r = least_squares(lambda x: (model(x, t, ph) - y) / sig, p, bounds=bounds, max_nfev=4000)
        except (ValueError, FloatingPointError):
            failed += 1
            continue
        failed += int(r.status) <= 0
        if best is None or r.cost < best.cost:
            best = r
    return best, failed


def ramsey_xy_fit(
    t_us,
    ones,
    shots,
    fit,
    *,
    seeds: Sequence[int],
    n_boot: int = 2000,
    margin: float | None = None,
    delta_floor_mhz: float | None = None,
    b_edges: Sequence[float] | None = None,
) -> dict:
    """The one-line and two-line fits of a two-quadrature Ramsey, with a held-out error and a bootstrap (test 7's
    procedure, finding 28).

    t_us: each quadrature's waits as scheduled, shape (2, W), X first (or (W,) for both). ones: the shots that read 1,
    per copy, quadrature and wait, shape (copies, 2, W); shots: the shots of each, an int or the same shape. fit: the
    fitted waits, a boolean mask or indices over W; the others are held out.

    The models, jointly over X and Y, Y being X with the phase minus pi/2 (`RAMSEY_XY_PHASE`):
      S, one line:  c + A exp(-t / tau) cos(2 pi Delta t + phi0);
      P, two lines: c + A exp(-t / tau') [b cos(2 pi (Delta0 + delta) t + phi0) + (1 - b) cos(2 pi (Delta0 - delta) t
      + phi0)], with Delta0 and delta inside the fit set's band (`ramsey_xy_band`).
    Each is fitted by weighted least squares to the copies' pooled P(1) on the fit set, each point weighted by its
    binomial standard error with p (1 - p) floored at 1/n, from every start, the best kept: S from RAMSEY_XY_S_STARTS
    starts uniform within its bounds (seeds[0]); P from twenty starts on the S fit and RAMSEY_XY_P_RANDOM_STARTS
    uniform within its bounds (seeds[1]). Each model's held-out error is the mean absolute difference between its
    prediction and the pooled P(1) over the held-out waits of both quadratures.

    The bootstrap (seeds[2], n_boot draws): for each fitted wait of each quadrature, the copies drawn with replacement,
    each drawn copy's shots redrawn from its own P(1), and P refitted from its point fit. Returns each of P's
    parameters' 5th, 50th and 95th percentiles over the refits that returned.

    margin, delta_floor_mhz and b_edges are a rule's thresholds, the caller's: given, the result says which of the
    clauses on them hold (P's held-out error below S's by more than the margin, or S's within it; delta's 5th
    percentile above or below the floor; b's interval inside the edges or reaching one). The package fixes none of
    them and names no verdict. A fit, beside a rule's verdict: it says nothing about what makes two lines."""
    rng_s, rng_p, rng_b = (np.random.default_rng(int(s)) for s in seeds)
    ones = np.asarray(ones)
    if ones.ndim != 3 or ones.shape[1] != 2 or ones.shape[0] < 1:
        raise ValueError(f"ones has the shape (copies, 2, waits); got {ones.shape}")
    copies, _, nw = ones.shape
    shots_arr = np.broadcast_to(np.asarray(shots), ones.shape)
    uniform = bool(np.all(shots_arr == shots_arr.flat[0]))
    tq = np.broadcast_to(np.asarray(t_us, float), (2, nw))
    mask = np.zeros(nw, bool)
    mask[np.asarray(fit)] = True
    fi, hi = np.flatnonzero(mask), np.flatnonzero(~mask)
    if len(fi) < 4 or not len(hi):
        raise ValueError("a fit set of at least four waits, and at least one wait held out")
    nn = shots_arr.sum(0)
    yq = ones.sum(0) / nn
    band = ramsey_xy_band(tq[:, fi])
    s_lo, s_hi = (np.array(b, float) for b in RAMSEY_XY_S_BOUNDS)
    p_lo = np.array([*s_lo[:3], -band["Delta0_bound_MHz"], s_lo[4], 0.0, 0.0])
    p_hi = np.array([*s_hi[:3], band["Delta0_bound_MHz"], s_hi[4], band["delta_bound_MHz"], 1.0])

    def stack(idx, a):
        return np.concatenate([a[0][idx], a[1][idx]])

    ph_of = np.array([RAMSEY_XY_PHASE["X"], RAMSEY_XY_PHASE["Y"]])[:, None] * np.ones((2, nw))
    te, phe, ye, ne = stack(fi, tq), stack(fi, ph_of), stack(fi, yq), stack(fi, nn)
    to, pho, yo = stack(hi, tq), stack(hi, ph_of), stack(hi, yq)
    se = _p1_sigma(ye, ne)

    def uniform_starts(lo, hi_, k, rng):
        return [list(lo + (hi_ - lo) * rng.random(len(lo))) for _ in range(k)]

    def result(name, r, failed, n_starts, model):
        chi2 = float(2 * r.cost)
        return {
            "params": dict(zip(RAMSEY_XY_NAMES[name], (float(v) for v in r.x))),
            "chi2": chi2,
            "n_points": len(ye),
            "dof": len(ye) - len(r.x),
            "starts": n_starts,
            "starts_failed": failed,
            "held_out_error": float(np.mean(np.abs(model(r.x, to, pho) - yo))),
        }

    starts_s = uniform_starts(s_lo, s_hi, RAMSEY_XY_S_STARTS, rng_s)
    rs, fails = _best_of(_ramsey_s, starts_s, (s_lo, s_hi), te, phe, ye, se)
    S = result("S", rs, fails, len(starts_s), _ramsey_s)
    c, A, tau, D, p0 = rs.x
    grid = [
        [c, A, tau, D + k * d, p0, d, bb]
        for d in RAMSEY_XY_P_GRID_DELTA_MHZ
        for k in (0, 1, -1)
        for bb in RAMSEY_XY_P_GRID_B
    ]
    grid += [[c, A, tau, D, p0, d, bb] for d, bb in RAMSEY_XY_P_GRID_EXTRA]
    starts_p = [list(np.clip(x, p_lo, p_hi)) for x in grid] + uniform_starts(
        p_lo, p_hi, RAMSEY_XY_P_RANDOM_STARTS, rng_p
    )
    rp, fails = _best_of(_ramsey_p, starts_p, (p_lo, p_hi), te, phe, ye, se)
    P = result("P", rp, fails, len(starts_p), _ramsey_p)
    P["lines_MHz"] = [
        P["params"]["Delta0_MHz"] + P["params"]["delta_MHz"],
        P["params"]["Delta0_MHz"] - P["params"]["delta_MHz"],
    ]
    P["reach_MHz"] = abs(P["params"]["Delta0_MHz"]) + P["params"]["delta_MHz"]

    from scipy.optimize import least_squares

    ones_f, n_f = ones[:, :, fi], shots_arr[:, :, fi]
    n_pool = nn[:, fi]
    draws = np.full((int(n_boot), 7), np.nan)
    refits_failed = 0
    for k in range(int(n_boot)):
        pick = rng_b.integers(0, copies, size=ones_f.shape)
        if uniform:
            n0 = int(shots_arr.flat[0])
            src = np.take_along_axis(ones_f, pick, axis=0) / n0
            yb = rng_b.binomial(n0, src).sum(0) / n_pool
        else:
            nk = np.take_along_axis(n_f, pick, axis=0)
            src = np.take_along_axis(ones_f, pick, axis=0) / nk
            yb = rng_b.binomial(nk, src).sum(0) / n_pool
        yb = np.concatenate([yb[0], yb[1]])
        sb = _p1_sigma(yb, ne)
        try:
            r = least_squares(
                lambda x, yb=yb, sb=sb: (_ramsey_p(x, te, phe) - yb) / sb, rp.x, bounds=(p_lo, p_hi), max_nfev=4000
            )
        except (ValueError, FloatingPointError):
            refits_failed += 1
            continue
        refits_failed += int(r.status) <= 0
        draws[k] = r.x
    ok = ~np.isnan(draws[:, 0])
    pct = {
        name: [float(v) for v in np.percentile(draws[ok, i], [5, 50, 95])] if ok.any() else [math.nan] * 3
        for i, name in enumerate(RAMSEY_XY_NAMES["P"])
    }
    out = {
        "fit_waits": fi.tolist(),
        "held_out_waits": hi.tolist(),
        "band": band,
        "S": S,
        "P": P,
        "bootstrap": {
            "draws": int(n_boot),
            "returned": int(ok.sum()),
            "refits_failed": refits_failed,
            "percentiles_5_50_95": pct,
        },
        "seeds": [int(s) for s in seeds],
        "per_wait": {
            quad: {"t_us": tq[i].tolist(), "P1": yq[i].tolist(), "se": np.sqrt(yq[i] * (1 - yq[i]) / nn[i]).tolist()}
            for i, quad in enumerate(RAMSEY_XY_QUADRATURES)
        },
    }
    if margin is not None or delta_floor_mhz is not None or b_edges is not None:
        clauses: dict = {}
        if margin is not None:
            clauses["P_below_S_by_more_than_the_margin"] = P["held_out_error"] < S["held_out_error"] - float(margin)
            clauses["S_within_the_margin_of_P_or_below"] = S["held_out_error"] <= P["held_out_error"] + float(margin)
        d_lo = pct["delta_MHz"][0]
        if delta_floor_mhz is not None:
            clauses["delta_lower_bound_above_the_floor"] = d_lo > float(delta_floor_mhz)
            clauses["delta_lower_bound_below_the_floor"] = d_lo < float(delta_floor_mhz)
        if b_edges is not None:
            e0, e1 = (float(x) for x in b_edges)
            b_lo, b_hi = pct["b"][0], pct["b"][2]
            clauses["b_interval_inside_the_edges"] = e0 < b_lo and b_hi < e1
            clauses["b_interval_reaches_an_edge"] = b_lo <= e0 or b_hi >= e1
        out["clauses"] = clauses
    return out


def copies_check(labels: Sequence[dict], counts: Sequence[dict], clbit: int = 0) -> dict:
    """Do the two copies of each circuit agree within their shot noise (finding 28)? The positions are grouped by
    their label without its "copy"; each circuit must have exactly two copies. Per circuit, z = (p1 - p2) / sqrt(p (1 -
    p) (1/n1 + 1/n2)), p1 and p2 the copies' P(1) (classical bit `clbit`, bit 0 rightmost), p the pooled P(1), with
    p (1 - p) floored at 1e-9. Returns the sum of z^2 over the circuits, its degrees of freedom (one per circuit), and
    each circuit's label, copies' P(1) and z. A diagnostic: the package fixes no threshold on it. Two copies drawn from
    one binomial give a sum near its degrees of freedom; copies whose P(1) moved between them do not."""
    groups: dict = {}
    order = []
    for k, (lab, cts) in enumerate(zip(labels, counts)):
        key = tuple(sorted((a, repr(b)) for a, b in lab.items() if a != "copy"))
        if key not in groups:
            groups[key] = []
            order.append(key)
        ones = sum(n for bits, n in cts.items() if _bits(bits)[clbit] == "1")
        groups[key].append((lab.get("copy"), k, ones, sum(cts.values())))
    rows, total = [], 0.0
    for key in order:
        g = sorted(groups[key], key=lambda x: (x[0] is None, x[0]))
        if len(g) != 2:
            raise ValueError(f"each circuit has exactly two copies; {dict(key)} has {len(g)}")
        (c1, k1, a, n1), (c2, k2, b, n2) = g
        p1, p2, pp = a / n1, b / n2, (a + b) / (n1 + n2)
        z = (p1 - p2) / math.sqrt(max(pp * (1 - pp), 1e-9) * (1 / n1 + 1 / n2))
        total += z * z
        lab = {name: v for name, v in labels[k1].items() if name != "copy"}
        rows.append({"label": lab, "copies": [c1, c2], "positions": [k1, k2], "P1": [p1, p2], "z": z})
    return {"sum_z2": total, "dof": len(rows), "per_dof": total / len(rows) if rows else math.nan, "circuits": rows}


# --------------------------------------------------------------------------- the monitor and the span reading (A27)
#: The monitor's fixed order: the readout circuits, then each repeat's X then Y, then the readout circuits again
RAMSEY_MONITOR_READOUT = ("P10", "P01")


def ramsey_monitor(waits_us: dict, backend, repeats: int) -> list[dict]:
    """The monitor (tests 10 and 11, finding 29): every qubit of a set at its own wait in one circuit, in two
    quadratures, repeated in a fixed order. waits_us maps each qubit to its wait in µs; the qubits are taken in
    ascending order, qubit k of that order measured into classical bit k. X is `ramsey_xy`'s X on every qubit at its own
    wait, Y the same with the S-dagger before each final H, so the circuit lasts as long as its longest-wait qubit's
    sequence; P10 measures every qubit with no gate and P01 applies X to every qubit, then measures. Each wait is made
    even with the backend's dt and granularity, as `ramsey_xy` makes it. Each distinct circuit is translated once onto
    the set by `to_backend`.

    Returns one entry per position, in the fixed order with no interleaving: P10, P01, then `repeats` repeats of X then
    Y, then P10, P01. Each entry is its label (the position, the block, "start", "monitor" or "end", the repeat from 1,
    the circuit, the quadrature, the qubits and, for X and Y, each qubit's requested wait, wait in dt and wait as
    scheduled from the end of its first SX to the start of its last, in dt) and the circuit."""
    from qiskit import QuantumCircuit
    from qiskit.circuit import CircuitInstruction
    from qiskit.circuit.library import SdgGate

    qs = sorted(int(q) for q in waits_us)
    if not qs or int(repeats) < 1:
        raise ValueError("the set holds at least one qubit and the monitor at least one repeat")
    waits = {q: float(waits_us[q]) for q in qs}
    if not all(math.isfinite(w) and w >= 0 for w in waits.values()):
        raise ValueError(f"the waits are finite and not negative, in µs; got {waits}")
    t, dt = backend.target, backend.dt
    gran = getattr(t, "granularity", 1) or 1
    wait_dt = {q: even_wait(waits[q] * 1e-6 / dt, gran) for q in qs}
    n = len(qs)
    circuits, waits_of = {}, {}
    for quad in RAMSEY_XY_QUADRATURES:
        qc = QuantumCircuit(n, n, name=f"{quad}-monitor-n{n}")
        for k, q in enumerate(qs):
            one = part_b_circuit(1, wait_dt[q], "R")
            if quad == "Y":
                j = max(i for i, x in enumerate(one.data) if x.operation.name == "h")
                one.data.insert(j, CircuitInstruction(SdgGate(), (one.qubits[0],)))
            qc.compose(one, qubits=[k], clbits=[k], inplace=True)
        isa = to_backend(qc, qs, backend)
        tl = _timeline(_chain_schedule(isa, backend, qs), t, dt, qs)
        circuits[quad] = isa
        waits_of[quad] = {
            "t_requested_us": {str(q): waits[q] for q in qs},
            "wait_dt": {str(q): wait_dt[q] for q in qs},
            "scheduled_wait_dt": {str(q): _window(tl, q)["T_dt"] for q in qs},
        }
    for name in RAMSEY_MONITOR_READOUT:
        qc = QuantumCircuit(n, n, name=f"{name}-n{n}")
        if name == "P01":
            qc.x(range(n))
        qc.measure(range(n), range(n))
        circuits[name] = to_backend(qc, qs, backend)
    order = [(name, None, "start") for name in RAMSEY_MONITOR_READOUT]
    for r in range(1, int(repeats) + 1):
        order += [(quad, r, "monitor") for quad in RAMSEY_XY_QUADRATURES]
    order += [(name, None, "end") for name in RAMSEY_MONITOR_READOUT]
    out = []
    for pos, (name, r, block) in enumerate(order):
        label = {
            "position": pos,
            "block": block,
            "repeat": r,
            "circuit": name,
            "quadrature": name if name in RAMSEY_XY_QUADRATURES else None,
            "qubits": qs,
        }
        if name in waits_of:
            label.update(waits_of[name])
        out.append({"label": label, "circuit": circuits[name]})
    return out


def _seconds(x):
    """A span's start or stop as seconds: a number as it is, a datetime or an ISO 8601 string as its POSIX time (a
    string without a zone read as UTC)."""
    from datetime import datetime

    if isinstance(x, (int, float)):
        return float(x)
    if isinstance(x, str):
        x = datetime.fromisoformat(x.replace("Z", "+00:00"))
    if x.tzinfo is None:
        x = x.replace(tzinfo=UTC)
    return x.timestamp()


def span_assignment(spans: Sequence[dict], labels: Sequence[dict] | None = None) -> dict:
    """Which execution span ran each position, as the provider's record says (A26, finding 29). spans is that record for
    one job, one entry per span: its "positions", its "start" and "stop" (or "start_utc" and "stop_utc"; ISO 8601,
    datetimes or seconds), optionally its "span" (else its place in the list) and "duration_s" (else stop minus
    start). The record decides, whatever the position numbers: a span need not be a run of consecutive positions.

    Returns the spans in start order with their durations, the gaps between consecutive spans in seconds, each
    position's span, and the positions in no span. If labels are given, those carrying a "repeat" are grouped by it:
    each repeat's positions, and its span if they all ran in one, else its spans, a straddling repeat. Refuses
    (ValueError) a record that places one position in two spans."""
    rows = []
    for i, s in enumerate(spans):
        start = _seconds(s["start"] if "start" in s else s["start_utc"])
        stop = _seconds(s["stop"] if "stop" in s else s["stop_utc"])
        dur = float(s["duration_s"]) if s.get("duration_s") is not None else stop - start
        rows.append(
            {
                "span": s.get("span", i),
                "start_s": start,
                "stop_s": stop,
                "duration_s": dur,
                "positions": sorted(int(p) for p in s["positions"]),
            }
        )
    rows.sort(key=lambda r: r["start_s"])
    for rank, r in enumerate(rows):
        r["rank"] = rank
    span_of: dict = {}
    for r in rows:
        for p in r["positions"]:
            if p in span_of:
                raise ValueError(f"position {p} lies in spans {span_of[p]} and {r['span']}")
            span_of[p] = r["span"]
    gaps = [{"between": [a["span"], b["span"]], "gap_s": b["start_s"] - a["stop_s"]} for a, b in zip(rows, rows[1:])]
    out = {"spans": rows, "gaps": gaps, "span_of_position": span_of}
    if labels is not None:
        out["positions_in_no_span"] = [p for p in range(len(labels)) if p not in span_of]
        reps: dict = {}
        for p, lab in enumerate(labels):
            if lab.get("repeat") is not None:
                reps.setdefault(lab["repeat"], []).append(p)
        repeats = {}
        for k, ps in reps.items():
            sp = [span_of.get(p) for p in ps]
            one = len(set(sp)) == 1 and sp[0] is not None
            repeats[k] = {
                "positions": ps,
                "span": sp[0] if one else None,
                "spans_of_positions": sp,
                "straddles": not one,
            }
        out["repeats"] = repeats
        out["straddling_repeats"] = sorted(k for k, r in repeats.items() if r["straddles"])
    return out


def _poisson90(n: int, t: float) -> list:
    """The 90% interval of a Poisson rate, n events in time t (Garwood's: chi2(0.05; 2n) / 2 and chi2(0.95; 2n + 2) /
    2, over t; 0 below when n is 0)."""
    from scipy.stats import chi2

    if t <= 0:
        return [None, None]
    lo = 0.0 if n == 0 else chi2.ppf(0.05, 2 * n) / 2
    return [lo / t, chi2.ppf(0.95, 2 * n + 2) / 2 / t]


def _wrap(x: float) -> float:
    """An angle wrapped to (-pi, pi]."""
    y = (x + math.pi) % (2 * math.pi) - math.pi
    return math.pi if y == -math.pi else y


def monitor_phase(
    ones: Sequence[int],
    labels: Sequence[dict],
    spans: Sequence[dict],
    wait_us: float,
    *,
    shots: int,
    s_floor: float,
    abs_min: float,
    n_se: float,
    level_se: float,
) -> dict:
    """The monitor's phase and length per repeat, on one qubit of one job, as test 10's rule reads them (finding 29).
    ones: per position, the shots that read 1 on this qubit; labels: per position, its "circuit" (P10, P01, X or Y) and
    for X and Y its "repeat"; spans: the provider's record (`span_assignment`). The thresholds are the caller's:

      1. c, the midpoint: the mean P(1) of the readout circuits.
      2. Per repeat k: theta_k = atan2(P_Y - c, P_X - c); r_k, the vector's length; s_k = sigma_k / r_k, sigma_k^2 =
         (P_X (1 - P_X) + P_Y (1 - P_Y)) / (2 shots), floored at s_floor; the repeat's span, or straddling.
      3. The pairs of consecutive repeats, neither straddling: the wrapped difference of theta, and a switch where its
         size exceeds max(abs_min, n_se sqrt(s_k^2 + s_(k+1)^2)): within a span, at a boundary (spans consecutive in
         start order), or neither (spans not consecutive).
      4. The within-span time: per span, its tested within-span pairs times its repeat period, its duration over the
         repeats it ran whole; the within-span rate per second with its 90% Poisson interval.
      5. The plateaus between switches, each with its weighted mean phase; the levels, plateaus whose means differ by
         no more than level_se combined errors, linked transitively; the slope of the unwrapped phase in each span.

    The median r_k is returned for the caller's usable rule. Words for what the counts mean are the caller's."""
    p = np.asarray(ones, float) / shots
    asg = span_assignment(spans, labels)
    info = {r["span"]: r for r in asg["spans"]}
    rank = {r["span"]: r["rank"] for r in asg["spans"]}
    ro = [k for k, lab in enumerate(labels) if lab["circuit"] in RAMSEY_MONITOR_READOUT]
    c = float(np.mean(p[ro]))
    xpos, ypos = {}, {}
    for k, lab in enumerate(labels):
        if lab["circuit"] == "X":
            xpos[lab["repeat"]] = k
        elif lab["circuit"] == "Y":
            ypos[lab["repeat"]] = k
    rows = []
    for k in sorted(xpos):
        px, py = p[xpos[k]], p[ypos[k]]
        vx, vy = px - c, py - c
        r = math.hypot(vx, vy)
        sig = math.sqrt((px * (1 - px) + py * (1 - py)) / (2 * shots))
        rep = asg["repeats"][k]
        rows.append(
            {
                "k": k,
                "PX": float(px),
                "PY": float(py),
                "theta": math.atan2(vy, vx),
                "r": r,
                "sigma": sig,
                "s": max(sig / r, s_floor) if r > 0 else math.inf,
                "span": rep["span"],
                "straddles": rep["straddles"],
                "spans_of_circuits": rep["spans_of_positions"],
            }
        )
    nrep = {sp: sum(1 for x in rows if x["span"] == sp) for sp in info}
    period = {sp: (info[sp]["duration_s"] / nrep[sp] if nrep[sp] else None) for sp in info}
    inc = [x for x in rows if not x["straddles"]]
    pairs = []
    for a, b in zip(rows, rows[1:]):
        if a["straddles"] or b["straddles"]:
            continue
        d = _wrap(b["theta"] - a["theta"])
        se = math.sqrt(a["s"] ** 2 + b["s"] ** 2)
        thr = max(abs_min, n_se * se)
        if a["span"] == b["span"]:
            kind = "within"
        elif abs(rank[a["span"]] - rank[b["span"]]) == 1:
            kind = "boundary"
        else:
            kind = "spans not consecutive"
        pairs.append(
            {
                "k": a["k"],
                "k1": b["k"],
                "span_a": a["span"],
                "span_b": b["span"],
                "kind": kind,
                "d": d,
                "se": se,
                "threshold": thr,
                "switch": abs(d) > thr,
                "size_is_pi": abs(abs(d) - math.pi) < 1e-12,
            }
        )
    phi = {}
    if inc:
        phi[inc[0]["k"]] = inc[0]["theta"]
    for a, b in zip(inc, inc[1:]):
        phi[b["k"]] = phi[a["k"]] + _wrap(b["theta"] - a["theta"])
    for x in rows:
        x["phi"] = phi.get(x["k"])
    sw = [q for q in pairs if q["switch"]]
    n_within = sum(1 for q in sw if q["kind"] == "within")
    n_boundary = sum(1 for q in sw if q["kind"] == "boundary")
    within_pairs = {sp: sum(1 for q in pairs if q["kind"] == "within" and q["span_a"] == sp) for sp in info}
    t_within = sum(within_pairs[sp] * period[sp] for sp in info if period[sp])
    sw_after = {q["k"]: q for q in sw}
    tested = {(q["k"], q["k1"]) for q in pairs}
    runs, cur = [], []
    for i, x in enumerate(inc):
        cur.append(x)
        nxt = inc[i + 1] if i + 1 < len(inc) else None
        if nxt is None or (x["k"] in sw_after and sw_after[x["k"]]["k1"] == nxt["k"]):
            runs.append(cur)
            cur = []
    plateaus = []
    for run in runs:
        w = np.array([1 / x["s"] ** 2 for x in run])
        ks = [x["k"] for x in run]
        before = next((q for q in sw if q["k1"] == ks[0]), None)
        after = next((q for q in sw if q["k"] == ks[-1]), None)
        plateaus.append(
            {
                "first_k": ks[0],
                "last_k": ks[-1],
                "n": len(run),
                "mean": float(np.sum(w * np.array([x["phi"] for x in run])) / np.sum(w)),
                "se": float(1 / math.sqrt(np.sum(w))),
                "spans": sorted({x["span"] for x in run}, key=lambda z: rank[z]),
                "untested_pair_inside": any((a, b) not in tested for a, b in zip(ks, ks[1:])),
                "opened_by": before["kind"] if before else None,
                "closed_by": after["kind"] if after else None,
            }
        )
    parent = list(range(len(plateaus)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(len(plateaus)):
        for j in range(i + 1, len(plateaus)):
            a, b = plateaus[i], plateaus[j]
            if abs(_wrap(a["mean"] - b["mean"])) <= level_se * math.sqrt(a["se"] ** 2 + b["se"] ** 2):
                parent[find(i)] = find(j)
    groups: dict = {}
    for i in range(len(plateaus)):
        groups.setdefault(find(i), []).append(i)
    levels = []
    for g in groups.values():
        ref = plateaus[g[0]]["mean"]
        w = np.array([1 / plateaus[i]["se"] ** 2 for i in g])
        rel = np.array([_wrap(plateaus[i]["mean"] - ref) for i in g])
        levels.append(
            {
                "plateaus": g,
                "n_repeats": int(sum(plateaus[i]["n"] for i in g)),
                "mean": _wrap(ref + float(np.sum(w * rel) / np.sum(w))),
                "se": float(1 / math.sqrt(np.sum(w))),
            }
        )
    levels.sort(key=lambda lv: -lv["n_repeats"])
    khz_per_rad = 1000.0 / (2 * math.pi * wait_us)
    slopes = {}
    for sp in sorted(info, key=lambda z: rank[z]):
        xs = [x for x in inc if x["span"] == sp]
        if len(xs) < 3:
            slopes[str(sp)] = None
            continue
        k = np.array([x["k"] for x in xs], float)
        y = np.array([x["phi"] for x in xs])
        w = np.array([1 / x["s"] ** 2 for x in xs])
        X = np.stack([np.ones_like(k), k], axis=1)
        G = X.T @ (X * w[:, None])
        _, b0 = np.linalg.solve(G, X.T @ (w * y))
        slopes[str(sp)] = {
            "rad_per_repeat": float(b0),
            "se_rad_per_repeat": math.sqrt(np.linalg.inv(G)[1, 1]),
            "kHz_per_minute": float(b0) * khz_per_rad * 60.0 / period[sp] if period[sp] else None,
            "n_repeats": len(xs),
        }
    dwell = [
        {
            "first_k": q["first_k"],
            "last_k": q["last_k"],
            "n_repeats": q["n"],
            "span": q["spans"][0],
            "seconds": q["n"] * period[q["spans"][0]],
        }
        for q in plateaus
        if q["opened_by"] == "within"
        and q["closed_by"] == "within"
        and len(q["spans"]) == 1
        and not q["untested_pair_inside"]
    ]
    wmean = None
    if inc:
        w = np.array([1 / x["s"] ** 2 for x in inc])
        wmean = float(np.sum(w * np.array([x["phi"] for x in inc])) / np.sum(w))
    return {
        "c": c,
        "wait_us": float(wait_us),
        "kHz_per_rad": khz_per_rad,
        "median_r": float(np.median([x["r"] for x in rows])),
        "n_within": n_within,
        "n_boundary": n_boundary,
        "n_spans_not_consecutive_switches": sum(1 for q in sw if q["kind"] == "spans not consecutive"),
        "within_time_s": t_within,
        "within_rate_per_s": n_within / t_within if t_within > 0 else None,
        "within_rate_ci90_per_s": _poisson90(n_within, t_within),
        "switches": [{**q, "size_kHz": q["d"] * khz_per_rad} for q in sw],
        "straddling_repeats": [x["k"] for x in rows if x["straddles"]],
        "pi_sized_differences": [q["k"] for q in pairs if q["size_is_pi"]],
        "plateaus": plateaus,
        "levels": levels,
        "n_levels": len(levels),
        "slopes": slopes,
        "dwell": dwell,
        "repeat_period_s": {str(k): v for k, v in period.items()},
        "repeats_per_span": {str(k): v for k, v in nrep.items()},
        "job_mean_phase": wmean,
        "repeats": rows,
        "pairs": pairs,
    }


def median_phase(theta: Sequence[float]) -> float:
    """The median of the angles on one sheet of the circle (test 11's ruling): each wrapped to within pi of their
    circular mean, the median taken, and the result wrapped. On a job whose phase stays in one place it is the
    ordinary median."""
    th = np.asarray(theta, float)
    ref = float(np.angle(np.mean(np.exp(1j * th))))
    return _wrap(ref + float(np.median([_wrap(x - ref) for x in th])))


def monitor_weight(phase: dict, R0: float, *, exchange: bool = False, abs_min: float, n_se: float) -> dict:
    """The weight at antiphase, per repeat, from `monitor_phase`'s result, as test 11's rule reads it (finding 29). At
    the wait 1 / (4 delta) two fixed lines of weights w and 1 - w point in opposite directions, so the fringe's length
    is R0 |1 - 2 w|, R0 the length one line would have there (the caller's, from a fit): w_k = (1 - r_k / R0) / 2 for a
    repeat whose theta_k lies within pi/2 of the job's median phase (`median_phase`), (1 + r_k / R0) / 2 for one a half
    turn away, the two exchanged when exchange is True (a weight above one half on the line the caller names); its
    standard error sigma_k / (2 R0). The pairs are `monitor_phase`'s; a weight switch where |w_(k+1) - w_k| exceeds
    max(abs_min, n_se combined errors), within a span or at a boundary. Per span: the mean of w_k over its repeats that
    ran whole, the standard deviation over the square root of their number, and the propagated error. Beside: the
    boundary table, each pair of included repeats on either side of a span boundary, a straddling repeat between them
    left out, and the pair at each span's middle (test 10's control), in phase and in weight. The thresholds and any
    words are the caller's."""
    rows = phase["repeats"]
    med = median_phase([x["theta"] for x in rows])
    cmean = float(np.angle(np.mean(np.exp(1j * np.asarray([x["theta"] for x in rows])))))
    out_rows, branch_differs = [], []
    for x in rows:
        near = abs(_wrap(x["theta"] - med)) <= math.pi / 2
        if near != (abs(_wrap(x["theta"] - cmean)) <= math.pi / 2):
            branch_differs.append(x["k"])
        lo, hi = (1 - x["r"] / R0) / 2, (1 + x["r"] / R0) / 2
        if exchange:
            lo, hi = hi, lo
        out_rows.append(
            {
                "k": x["k"],
                "span": x["span"],
                "straddles": x["straddles"],
                "branch": "near the median phase" if near else "a half turn away",
                "w": lo if near else hi,
                "se_w": x["sigma"] / (2 * R0),
            }
        )
    by_k = {x["k"]: x for x in out_rows}
    pairs = []
    for q in phase["pairs"]:
        a, b = by_k[q["k"]], by_k[q["k1"]]
        se = math.sqrt(a["se_w"] ** 2 + b["se_w"] ** 2)
        thr = max(abs_min, n_se * se)
        dw = b["w"] - a["w"]
        pairs.append(
            {
                "k": q["k"],
                "k1": q["k1"],
                "span_a": q["span_a"],
                "span_b": q["span_b"],
                "kind": q["kind"],
                "dw": dw,
                "se": se,
                "threshold": thr,
                "switch": abs(dw) > thr,
            }
        )
    sw = [q for q in pairs if q["switch"]]
    spans_in_order = list(dict.fromkeys(x["span"] for x in rows if not x["straddles"]))
    per_span = []
    for sp in spans_in_order:
        xs = [x for x in out_rows if x["span"] == sp and not x["straddles"]]
        w = np.array([x["w"] for x in xs])
        se = np.array([x["se_w"] for x in xs])
        per_span.append(
            {
                "span": sp,
                "n_repeats": len(xs),
                "mean_w": float(np.mean(w)),
                "se_sd_over_sqrt_n": float(np.std(w, ddof=1) / math.sqrt(len(w))) if len(w) > 1 else None,
                "se_propagated": float(math.sqrt(np.sum(se**2)) / len(w)),
                "sd_w": float(np.std(w, ddof=1)) if len(w) > 1 else None,
            }
        )
    ph = {x["k"]: x for x in rows}
    inc = [x for x in out_rows if not x["straddles"]]

    def across(a, b):
        pa, pb = ph[a["k"]], ph[b["k"]]
        d = _wrap(pb["theta"] - pa["theta"])
        se_p = math.sqrt(pa["s"] ** 2 + pb["s"] ** 2)
        dw = b["w"] - a["w"]
        se_w = math.sqrt(a["se_w"] ** 2 + b["se_w"] ** 2)
        return {"k": a["k"], "k1": b["k"], "d_phase": d, "se_phase": se_p, "d_w": dw, "se_w": se_w}

    boundaries = [
        {"between_spans": [a["span"], b["span"]], **across(a, b)}
        for a, b in zip(inc, inc[1:])
        if a["span"] != b["span"]
    ]
    controls = []
    for sp in spans_in_order:
        xs = [x for x in inc if x["span"] == sp]
        if len(xs) >= 2:
            m = len(xs) // 2 - 1
            controls.append({"span": sp, **across(xs[m], xs[m + 1])})
    return {
        "R0": float(R0),
        "branches_exchanged": bool(exchange),
        "median_phase": med,
        "circular_mean_phase": cmean,
        "repeats_whose_branch_differs_under_the_circular_mean": branch_differs,
        "n_within_w": sum(1 for q in sw if q["kind"] == "within"),
        "n_boundary_w": sum(1 for q in sw if q["kind"] == "boundary"),
        "switches_w": sw,
        "per_span": per_span,
        "median_w": float(np.median([x["w"] for x in out_rows])),
        "boundary_table": {"boundaries": boundaries, "control_pairs_at_each_spans_middle": controls},
        "repeats": out_rows,
        "pairs": pairs,
    }


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
