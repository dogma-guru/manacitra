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

**The boundary (D-02).** Nothing here is a reuse compiler, a port of a published reuse-compilation method, a
restore-and-route step, or an algorithm that decides where to measure and reset. The wait test's measures and resets are
written by hand and fixed in its definition, the same for every chain, and the user names the chain.
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


def build_wait_test(chain: Sequence[int], refocus: bool = False, backend=None):
    """The wait test on the chain L1-M-L3 the user names (three physical qubits, L1 and L3 each coupled to M).

    With a backend: translated to its instructions at optimization level 0 with the chain as the layout, so the
    measures and resets stay where the definition puts them; with refocus=True, XY4 pulses are then inserted into every
    idle window of the chain long enough to hold the sequence (`refocused`). Without a backend, the circuit on three
    lines, unplaced (refocusing needs the backend's durations)."""
    chain = [int(q) for q in chain]
    if len(chain) != 3 or len(set(chain)) != 3:
        raise ValueError("the chain is three distinct qubits, L1-M-L3")
    qc = wait_test_logical()
    if backend is None:
        if refocus:
            raise ValueError("refocusing needs the backend's durations: pass backend")
        return qc
    t = backend.target
    gate = "cz"
    for a, b in ((chain[0], chain[1]), (chain[1], chain[2])):
        if t[gate].get((a, b)) is None and t[gate].get((b, a)) is None:
            raise ValueError(f"refused: {a}-{b} is not a coupler with a CZ on this backend")
    isa = to_backend(qc, chain, backend)
    return refocused(isa, t, chain) if refocus else isa


def wait_lengths(backend, chain: Sequence[int]) -> dict:
    """The waits M sees, from the backend's target: each end line's measure plus reset, in dt and in us."""
    t = backend.target
    out = {}
    for name, q in (("L1", chain[0]), ("L3", chain[2])):
        d = t["measure"][(q,)].duration + t["reset"][(q,)].duration
        out[name] = {"qubit": int(q), "dt": int(round(d / backend.dt)), "us": d * 1e6}
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
