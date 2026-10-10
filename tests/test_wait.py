# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""Amendment A18: Kickoff 47's Part B and the wait test, built by the package (manacitra.wait), checked three ways:
against the archive, instruction by instruction and verdict by verdict; exactly, by the package's own simulator; and on
Qiskit Aer, with a frequency offset planted by a noise pass written here (every delay on the chosen qubit becomes the
delay and an RZ of 2 pi f t). The Aer tests use no vendor noise model and no device data: they run on a synthetic
three-qubit target whose durations are round numbers chosen here."""

import copy
import hashlib
import json
import math
import re
from types import SimpleNamespace

import numpy as np
import pytest

from manacitra import archive, wait

K47 = "ibm_fez/k47-wait.json"
CHAINS = ((144, 143, 142), (132, 131, 138))


# --------------------------------------------------------------------------- the wait test, exactly
def ops(circuit) -> dict:
    return dict(circuit.count_ops())


def test_the_wait_test_is_written_out_within_its_limits():
    """5 CZ, 6 measures, 3 resets (the limits are 8, 9 and 6), generic gates only, no feed-forward; the end lines are
    retired three times, each reset followed by a new logical qubit on the line that meets M by CZ; M is put in
    superposition before the first wait and turned back only after the last."""
    qc = wait.wait_test_logical()
    o = ops(qc)
    assert o == {"h": 7, "cz": 5, "measure": 6, "reset": 3, "barrier": 6}
    assert o["cz"] <= 8 and o["measure"] <= 9 and o["reset"] <= 6
    names = [(i.operation.name, [qc.find_bit(b).index for b in i.qubits]) for i in qc.data]
    assert not {"if_else", "while_loop", "switch_case", "for_loop"} & set(o)
    resets = [k for k, (n, _) in enumerate(names) if n == "reset"]
    retired = [k for k in resets if any(n == "cz" and names[k][1][0] in q for n, q in names[k + 1 :])]
    assert len(retired) == 3 and {names[k][1][0] for k in retired} == {wait.L1, wait.L3}
    on_m = [n for n, q in names if wait.M in q and n != "barrier"]
    assert on_m[0] == "h" and on_m[-2:] == ["h", "measure"] and on_m.count("h") == 2
    first_reset, last_measure_of_an_end = (
        resets[0],
        max(k for k, (n, q) in enumerate(names) if n == "measure" and q != [wait.M]),
    )
    h_m = [k for k, (n, q) in enumerate(names) if n == "h" and q == [wait.M]]
    assert h_m[0] < first_reset and h_m[1] > last_measure_of_an_end  # in superposition through all three waits


def test_the_exact_ideal_is_the_parity():
    """Each end-line result is a fair coin and M's result is their parity: 32 outcomes of 64, each 1/32."""
    analytic = {}
    for b in range(32):
        bits = [(b >> i) & 1 for i in range(5)]
        key = str(sum(bits) % 2) + "".join(str(x) for x in bits[::-1])
        analytic[key] = 1 / 32
    ideal = wait.wait_test_ideal()
    assert set(ideal) == set(analytic) and all(ideal[k] == pytest.approx(v, abs=1e-12) for k, v in analytic.items())
    assert wait.fidelity(ideal, ideal) == pytest.approx(1.0, abs=1e-12)


def test_the_sensitivity_meets_the_brief():
    """RZ(pi/2) on M inside each wait, and inside only one, takes F from 1 to 0.5: drops of 0.5, against the brief's
    0.4 and 0.1."""
    s = wait.wait_test_sensitivity()
    assert s["F_each_wait"] == pytest.approx(0.5, abs=1e-12) and 1 - s["F_each_wait"] >= 0.4
    assert s["F_one_wait"] == pytest.approx(0.5, abs=1e-12) and 1 - s["F_one_wait"] >= 0.1


@pytest.mark.parametrize("total", [0.3, math.pi / 2, 2.0, math.pi, 4.0, 2 * math.pi])
def test_the_wait_test_reads_the_total_phase(total):
    """F = cos^2(phi / 2) for a total phase phi gained by M over the three waits, however it is split: so a phase
    of 2 pi, from an offset of one cycle per total wait, leaves F at 1. The test cannot see such an offset; Part B's
    Ramsey curve can."""
    ideal = wait.wait_test_ideal()
    for split in ((total, 0, 0), (total / 3,) * 3, (0.2 * total, 0.5 * total, 0.3 * total)):
        f = wait.fidelity(wait.exact_distribution(wait.wait_test_logical(split)), ideal)
        assert f == pytest.approx(math.cos(total / 2) ** 2, abs=1e-9)


def test_the_exact_simulator_against_qiskit():
    """Without mid-circuit measurement, exact_distribution equals Qiskit's statevector probabilities; with a measure
    and a reset, the line reads 0 after the reset."""
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Statevector

    qc = QuantumCircuit(3)
    qc.h(0)
    qc.sx(1)
    qc.cx(0, 2)
    qc.rz(0.7, 2)
    qc.cz(1, 2)
    qc.ry(1.1, 0)
    qc.x(1)
    want = Statevector(qc).probabilities_dict()
    qc.measure_all()
    got = wait.exact_distribution(qc)
    assert set(got) == {k for k, v in want.items() if v > 1e-12}
    assert all(got[k] == pytest.approx(want[k], abs=1e-12) for k in got)
    mr = QuantumCircuit(1, 2)
    mr.h(0)
    mr.measure(0, 0)
    mr.reset(0)
    mr.measure(0, 1)
    assert wait.exact_distribution(mr) == pytest.approx({"00": 0.5, "01": 0.5})


# --------------------------------------------------------------------------- the wait test on ibm_fez's snapshot
@pytest.fixture(scope="module")
def fez():
    pytest.importorskip("qiskit_ibm_runtime")
    from qiskit_ibm_runtime.fake_provider import FakeFez

    return FakeFez()


@pytest.mark.parametrize("chain", CHAINS)
def test_both_variants_are_exact_on_the_snapshot(fez, chain):
    """Built for ibm_fez's offline snapshot, without and with XY4: F = 1 exactly, the same 5 CZ, 6 measures and
    3 resets on the chain, and M idle through three windows each as long as an end line's measure plus reset."""
    ideal = wait.wait_test_ideal()
    plain, refocused = wait.build_wait_test(chain, False, fez), wait.build_wait_test(chain, True, fez)
    waits = wait.wait_lengths(fez, chain)
    for c in (plain, refocused):
        assert wait.fidelity(wait.exact_distribution(c), ideal) == pytest.approx(1.0, abs=1e-9)
        o = ops(c)
        assert (o["cz"], o["measure"], o["reset"]) == (5, 6, 3)
        used = {c.find_bit(b).index for i in c.data if i.operation.name not in ("barrier", "delay") for b in i.qubits}
        assert used == set(chain)
    windows = wait.idle_windows(wait.scheduled(plain, fez.target), chain[1])
    long_ = [w for w in windows if w >= min(v["dt"] for v in waits.values())]
    assert long_ == [waits["L1"]["dt"], waits["L3"]["dt"], waits["L1"]["dt"]]
    xs = [i for i in refocused.data if i.operation.name == "x"]
    assert xs and len(xs) % 4 == 0 and {refocused.find_bit(i.qubits[0]).index for i in xs} <= set(chain)


def test_a_chain_without_couplers_is_refused(fez):
    with pytest.raises(ValueError, match="not a coupler"):
        wait.build_wait_test((144, 143, 0), False, fez)
    with pytest.raises(ValueError):
        wait.build_wait_test((143, 143, 142))
    with pytest.raises(ValueError, match="backend"):
        wait.build_wait_test((144, 143, 142), refocus=True)


def test_a_routed_translation_is_refused(fez):
    """The review: the level-0 pass manager would route a circuit with a CZ off the coupling map. to_backend refuses
    any translation that routed, moved a qubit, touched a qubit not named or changed the two-qubit gate count."""
    from qiskit import QuantumCircuit

    qc = QuantumCircuit(3, 3)
    qc.h(0)
    qc.cz(0, 2)  # 144 and 142 share no coupler
    qc.measure(range(3), range(3))
    with pytest.raises(RuntimeError, match="routed the circuit"):
        wait.to_backend(qc, (144, 143, 142), fez)
    logical = wait.wait_test_logical()
    wait.check_translation(logical, wait.build_wait_test((144, 143, 142), False, fez), (144, 143, 142))
    with pytest.raises(RuntimeError, match="qubits not named"):
        wait.check_translation(logical, wait.build_wait_test((132, 131, 138), False, fez), (144, 143, 142))


# --------------------------------------------------------------------------- Part B against the reconstruction
RECON = "ibm_fez/k47-wait-part-b-reconstruction.json"
RECON_LABEL = "reconstructed on 10 October 2026 by rerunning the original builder; not the circuits as sent"


def part_b_mismatches(built, fez) -> list[str]:
    """Every way a built Part B differs from Kickoff 47's: each circuit, of both copies, against the reconstruction's
    entry for its label, instruction by instruction; its operation counts and qubits against those recorded from the
    circuits as sent (part_B_circuits); the labels against the run's order; and the set of circuits. Empty if none."""
    rec, ref = archive.load(K47), archive.load(RECON)["circuits"]
    us_of = {dt: us for us, dt in rec["tau_dt"].items()}
    out = []
    for e in built:
        lab = e["label"]
        key = f"g{lab['group']}|{us_of.get(lab['tau_dt'])}|{lab['variant']}"
        name = f"{key}, copy {lab['copy']}"
        if key not in ref:
            out.append(f"{name}: not in the reconstruction")
            continue
        isa = wait.to_backend(e["circuit"], e["layout"], fez)
        got, want = wait.structure(isa), ref[key]
        if [r[:3] for r in got] != [r[:3] for r in want] or any(
            a[3] != pytest.approx(b[3], abs=1e-12) for a, b in zip(got, want)
        ):
            out.append(f"{name}: its instructions differ from the reconstruction")
        if ops(isa) != rec["part_B_circuits"][key]["count_ops"] or e["layout"] != rec["part_B_circuits"][key]["qubits"]:
            out.append(f"{name}: its operation counts or qubits differ from those recorded at the run")
    ours = [
        (e["label"]["group"], us_of.get(e["label"]["tau_dt"]), e["label"]["variant"], e["label"]["copy"]) for e in built
    ]
    theirs = [(a["group"], str(a["tau_us"]), a["variant"], a["copy"]) for a in rec["labels"] if a["part"] == "B"]
    if ours != theirs:
        out.append("the circuits are not those of the run, in the run's order")
    if set(ref) != set(rec["part_B_circuits"]):
        out.append("the reconstruction and the record of the run name different circuits")
    return out


def test_part_b_matches_kickoff_47_both_copies(fez):
    """Part B, built here for Kickoff 47's groups and waits on the snapshot: all 48 circuits, both copies, each equal
    instruction by instruction to the reconstruction's entry for its label, with the operation counts recorded from
    the circuits as sent, in the run's order."""
    built = wait.part_b(wait.KICKOFF_47_GROUPS, wait.KICKOFF_47_WAITS_DT)
    assert len(built) == 48 and sum(e["label"]["copy"] == 2 for e in built) == 24
    assert part_b_mismatches(built, fez) == []


def _delay_plus_two(circuit):
    from qiskit.circuit import Delay

    for k, inst in enumerate(circuit.data):
        if inst.operation.name == "delay":
            circuit.data[k] = inst.replace(operation=Delay(inst.operation.duration + 2, unit="dt"))
            return
    raise AssertionError("no delay to change")


@pytest.mark.parametrize(
    "mutation",
    [
        "an extra X, second copy",
        "a changed delay, second copy",
        "a missing circuit",
        "no circuits",
        "an extra X, first copy",
        "a changed delay, first copy",
        "a changed measurement target, second copy",
        "two circuits swapped",
    ],
)
def test_the_part_b_comparison_fails_on_a_changed_circuit(fez, mutation):
    """Controls that must fail (the reviews of pull request 21): one changed circuit of either copy, its measurement
    target included, one missing, two swapped in order, or none at all."""
    built = wait.part_b(wait.KICKOFF_47_GROUPS, wait.KICKOFF_47_WAITS_DT)
    copy = 2 if "second" in mutation else 1
    waited = [e for e in built if e["label"]["copy"] == copy and e["label"]["tau_dt"] > 0]
    if mutation == "no circuits":
        built = []
    elif mutation == "a missing circuit":
        del built[31]
    elif mutation == "two circuits swapped":
        built[3], built[4] = built[4], built[3]
    elif "extra X" in mutation:
        waited[0]["circuit"].x(0)
    elif "measurement target" in mutation:
        c = waited[2]["circuit"]
        k = next(k for k, inst in enumerate(c.data) if inst.operation.name == "measure")
        c.data[k] = c.data[k].replace(clbits=(c.clbits[1],))  # qubit 0 now written to classical bit 1
    else:
        _delay_plus_two(waited[5]["circuit"])
    found = part_b_mismatches(built, fez)
    assert found, mutation
    if mutation == "two circuits swapped":  # each circuit still matches its label; only the order is wrong
        assert found == ["the circuits are not those of the run, in the run's order"]
    if "copy" in mutation:  # the mismatches name the changed circuit, and no other
        at = 0 if "extra X" in mutation else 2 if "measurement" in mutation else 5
        lab = waited[at]["label"]
        us = {dt: us for us, dt in archive.load(K47)["tau_dt"].items()}[lab["tau_dt"]]
        name = f"g{lab['group']}|{us}|{lab['variant']}, copy {copy}: "
        assert name + "its instructions differ from the reconstruction" in found and all(
            f.startswith(name) for f in found
        )


def test_the_reconstruction_is_recorded_and_can_be_repeated(fez):
    """The sidecar names the released archive by its SHA-256, which still matches it (the released file is unchanged);
    its circuits hash to the recorded SHA-256; and the builder's Part B text, run here as the record says, rebuilds
    the same 24 circuits, in the run's order, with nothing of Part A in it."""
    rec, recon = archive.load(K47), archive.load(RECON)
    m = recon["meta"]
    assert m["label"] == RECON_LABEL and m["reconstructed_on"] == "2026-10-10"
    released = (archive.data_dir() / K47).read_bytes()
    assert m["released_archive"] == {"file": K47, "sha256": hashlib.sha256(released).hexdigest()}
    assert m["sources"][0]["sha256"] == rec["meta"]["source_scripts"][0]["sha256"]
    canon = json.dumps(recon["circuits"], sort_keys=True, separators=(",", ":"))
    assert hashlib.sha256(canon.encode()).hexdigest() == m["circuits_sha256"]
    text = m["builder"]["text"]
    assert hashlib.sha256(text.encode()).hexdigest() == m["builder"]["text_sha256"]
    assert not any(
        w in text for w in ("build_A", "order_A", "CHAINS", "CELLS", "SPACING", "Path", "HERE", "import sys")
    )
    assert not re.search(r"[A-Za-z_.]+/[A-Za-z_]", text)  # no path
    ns: dict = {}
    exec(compile(text, "build_B", "exec"), ns)  # the record's own text, as its how_to_repeat says
    isa, _, _ = ns["build_B"](fez)
    assert {f"g{g}|{tau}|{v}": wait.structure(c) for (g, tau, v), c in isa.items()} == recon["circuits"]
    order = [(b["group"], b["tau_us"], b["variant"], b["copy"]) for b in ns["b_list"]()]
    assert order == [(a["group"], a["tau_us"], a["variant"], a["copy"]) for a in rec["labels"] if a["part"] == "B"]


def _k47_losses(**kw):
    rec = archive.load(K47)
    groups = [qs for _, qs in sorted(rec["groups"].items(), key=lambda z: int(z[0]))]
    seed = rec["fixed_before_the_data"]["bootstrap"]["seed_B"]
    return rec, wait.part_b_losses(
        rec["labels"], rec["counts"], groups, rec["taus_us"], reference=3.4, seed=seed, wait_key="tau_us", **kw
    )


def test_the_verdicts_on_kickoff_47s_counts_equal_the_archive():
    """The package's analysis of Kickoff 47's archived counts gives the archived kind of loss on every qubit, and the
    same point losses."""
    rec, got = _k47_losses()
    want = rec["archived"]["analysis"]["part_B"]["qubits"]
    assert set(got) == set(want)
    for q in want:
        assert got[q]["kind_of_loss"] == want[q]["kind_of_loss"], q
        assert got[q]["r"] == pytest.approx(want[q]["r_3p4"], abs=1e-12)
        assert got[q]["e"] == pytest.approx(want[q]["e_3p4"], abs=1e-12)
    assert rec["archived"]["analysis"]["part_B"]["verdict_143"] == got["143"]["kind_of_loss"] == "REFOCUSABLE"


def test_the_rules_thresholds_are_parameters():
    """Kickoff 47's rule in its order, and its thresholds passed in: a floor of 0.25 puts 143's Ramsey loss (interval
    0.215 to 0.231) below it."""
    assert wait.wait_loss_kind([0.0, 0.09], [-1, 1], [-1, 1]) == "NOT REPRODUCED"
    assert wait.wait_loss_kind([0.1, 0.3], [0.01, 0.2], [0.01, 0.2]) == "REFOCUSABLE"
    assert wait.wait_loss_kind([0.1, 0.3], [-0.1, 0.2], [0.01, 0.2]) == "NOT REFOCUSABLE"
    assert wait.wait_loss_kind([0.1, 0.3], [-0.1, 0.2], [-0.1, 0.2]) == "MIXED"
    assert wait.wait_loss_kind([0.1, 0.3], [0.01, 0.2], [0.01, 0.2], floor=0.31) == "NOT REPRODUCED"
    _, got = _k47_losses(floor=0.25, n_boot=2000)
    assert got["143"]["kind_of_loss"] == "NOT REPRODUCED"


@pytest.mark.parametrize(
    "intervals, floor, kind",
    [
        (([0, 0.1], [0, 0], [0, 0]), 0.1, "MIXED"),  # the upper bound equal to the floor is not below it
        (([0, 0.099], [1, 2], [1, 2]), 0.1, "NOT REPRODUCED"),  # below the floor, before the other two
        (([0.1, 0.2], [0, 1], [-1, 0]), 0.1, "MIXED"),  # a lower bound of exactly 0 is not above 0
        (([0.1, 0.2], [-1, 0], [0, 1]), 0.1, "MIXED"),
        (([0.1, 0.2], [1, 2], [1, 2]), 0.1, "REFOCUSABLE"),  # both above 0: REFOCUSABLE is checked first
    ],
)
def test_the_rule_at_its_boundaries(intervals, floor, kind):
    """The review's cases on valid intervals, with the documented strict comparisons."""
    assert wait.wait_loss_kind(*intervals, floor=floor) == kind


@pytest.mark.parametrize(
    "intervals, floor",
    [
        (([math.nan, math.nan], [math.nan, math.nan], [math.nan, math.nan]), 0.1),
        (([0.9, 0.05], [-1, 1], [-1, 1]), 0.1),  # reversed bounds
        (([0.1, 0.2], [0.3, 0.1], [-1, 1]), 0.1),
        (([0.1, 0.2], [-1, 1], [-1, math.inf]), 0.1),
        (([0.1], [-1, 1], [-1, 1]), 0.1),  # one bound
        (([0.1, 0.2], [-1, 0, 1], [-1, 1]), 0.1),  # three bounds
        (([0.1, 0.2], [-1, 1], [-1, 1]), math.nan),  # the floor
        (([0.1, 0.2], [-1, 1], [-1, 1]), math.inf),
    ],
)
def test_the_rule_refuses_an_invalid_interval(intervals, floor):
    """Before the review, NaN intervals read MIXED and the reversed interval NOT REPRODUCED; now each is refused."""
    with pytest.raises(ValueError):
        wait.wait_loss_kind(*intervals, floor=floor)


# --------------------------------------------------------------------------- offline, on Aer, an offset planted here
DT = 4e-9  # the synthetic target's dt; its durations, in dt: one-qubit gates 8, CZ 20, measure 400, reset 400
F_OFFSET = 47e3


def synthetic_backend():
    from qiskit.circuit import Delay, Parameter
    from qiskit.circuit.library import CZGate, Measure, Reset, RZGate, SXGate, XGate
    from qiskit.providers import BackendV2, Options
    from qiskit.transpiler import InstructionProperties, Target

    t = Target(num_qubits=3, dt=DT)

    def each(n_dt):
        return {(q,): InstructionProperties(duration=n_dt * DT) for q in range(3)}

    t.add_instruction(RZGate(Parameter("a")), each(0))
    t.add_instruction(SXGate(), each(8))
    t.add_instruction(XGate(), each(8))
    t.add_instruction(CZGate(), {e: InstructionProperties(duration=20 * DT) for e in ((0, 1), (1, 0), (1, 2), (2, 1))})
    t.add_instruction(Measure(), each(400))
    t.add_instruction(Reset(), each(400))
    t.add_instruction(Delay(Parameter("t")), {(q,): None for q in range(3)})

    class Synthetic(BackendV2):
        def __init__(self):
            super().__init__(name="synthetic-three-qubits")

        @property
        def target(self):
            return t

        @property
        def max_circuits(self):
            return None

        @classmethod
        def _default_options(cls):
            return Options()

        def run(self, *a, **k):
            raise NotImplementedError("a synthetic target for building circuits; Aer runs them")

    return Synthetic()


def planted(circuit, target, qubit: int, f_hz: float = 0.0, t_phi_s: float | None = None):
    """The noise pass: the circuit scheduled with the target's durations, and after every delay on `qubit` an RZ of
    2 pi f t (a steady frequency offset f over the delay's t) or, with t_phi_s, a dephasing channel that takes the
    qubit's coherence down by exp(-t / t_phi_s) (white noise, which no refocusing removes)."""
    from qiskit_aer.noise import phase_damping_error

    s = wait.scheduled(circuit, target)
    out = s.copy_empty_like()
    for inst in s.data:
        out.append(inst)
        if inst.operation.name == "delay" and s.find_bit(inst.qubits[0]).index == qubit:
            t = inst.operation.duration * DT
            if f_hz:
                out.rz(2 * math.pi * f_hz * t, inst.qubits[0])
            if t_phi_s:
                out.append(phase_damping_error(1 - math.exp(-2 * t / t_phi_s)).to_instruction(), inst.qubits)
    return out


def aer_counts(circuits, shots, seed, trace: list | None = None, **noise):
    """Every circuit run on Aer with its own shots; with sign_switch, each shot's offset is +f or -f, drawn per shot:
    each circuit runs once with +f and once with -f, keeping every shot's outcome, and each shot then takes its outcome
    from one of the two by its own sign. With trace, every circuit's signs and kept outcomes are appended to it."""
    from qiskit_aer import AerSimulator

    sim, target = AerSimulator(), synthetic_backend().target
    switch = noise.pop("sign_switch", False)
    by_shots: dict = {}
    for k, n in enumerate(shots):
        by_shots.setdefault(n, []).append(k)
    out = [None] * len(circuits)
    for n, ks in sorted(by_shots.items()):
        if not switch:
            res = sim.run([planted(circuits[k], target, wait.M, **noise) for k in ks], shots=n, seed_simulator=seed)
            for j, k in enumerate(ks):
                out[k] = res.result().get_counts(j)
            continue
        f = noise["f_hz"]
        mem = {
            s: sim.run(
                [planted(circuits[k], target, wait.M, f_hz=s * f) for k in ks],
                shots=n,
                memory=True,
                seed_simulator=seed + (s > 0),
            ).result()
            for s in (1, -1)
        }
        rng = np.random.default_rng(seed)
        for j, k in enumerate(ks):
            sign = rng.integers(0, 2, size=n)
            plus, minus = mem[1].get_memory(j), mem[-1].get_memory(j)
            kept = [plus[i] if sign[i] else minus[i] for i in range(n)]
            cts: dict = {}
            for key in kept:
                cts[key] = cts.get(key, 0) + 1
            out[k] = cts
            if trace is not None:
                trace.append({"circuit": k, "signs": sign, "outcomes": kept})
    return out


@pytest.fixture(scope="module")
def synthetic_run():
    pytest.importorskip("qiskit_aer")
    be = synthetic_backend()
    circuits, labels, shots = wait.wait_run((0, 1, 2), be)
    return be, circuits, labels, shots


_ANALYSED: dict = {}


def analysed(synthetic_run, corrupt=None, **noise):
    """The run's analysis under a noise, made once per noise; corrupt(labels, counts) may change the counts first."""
    be, circuits, labels, shots = synthetic_run
    key = tuple(sorted(noise.items()))
    if key not in _ANALYSED:
        _ANALYSED[key] = aer_counts(circuits, shots, seed=1818, **noise)
    counts = _ANALYSED[key] if corrupt is None else corrupt(labels, copy.deepcopy(_ANALYSED[key]))
    res = wait.analyse_wait_run(labels, counts, be.dt)
    assert res["part_b"]["reference_wait_dt"] == 850  # 3.4 us at the synthetic dt
    return res["wait_test"], res["part_b"]["qubits"]


def test_the_synthetic_run_is_built_as_on_hardware(synthetic_run):
    be, circuits, labels, shots = synthetic_run
    assert wait.wait_lengths(be, (0, 1, 2)) == {
        "L1": {"qubit": 0, "dt": 800, "us": pytest.approx(3.2)},
        "L3": {"qubit": 2, "dt": 800, "us": pytest.approx(3.2)},
    }
    assert len(circuits) == 10 + 48 and sum(shots) == 10 * 10_000 + 48 * 4_000
    ideal = wait.wait_test_ideal()
    for c, lab in zip(circuits, labels):
        if lab["part"] == "W":
            assert wait.fidelity(wait.exact_distribution(c), ideal) == pytest.approx(1.0, abs=1e-9)


def no_offset_failures(w, q) -> list[str]:
    """The no-offset test's conditions that fail: Part B NOT REPRODUCED on every qubit; F above 0.99 with and without
    refocusing (the review: not only a small difference between them); and the two within 0.05."""
    out = []
    if {row["kind_of_loss"] for row in q.values()} != {"NOT REPRODUCED"}:
        out.append("Part B is not NOT REPRODUCED on every qubit")
    if not (w["F_no"] > 0.99 and w["F_refocus"] > 0.99):
        out.append(f"F is not above 0.99: {w['F_no']:.4f} and {w['F_refocus']:.4f}")
    if abs(w["F_refocus"] - w["F_no"]) >= 0.05:
        out.append("F with and without refocusing differ by 0.05 or more")
    return out


def test_offline_no_offset(synthetic_run):
    """No offset: Part B reads NOT REPRODUCED on every qubit, the wait test's F is above 0.99 without and with
    refocusing, and the two differ by less than 0.05."""
    assert no_offset_failures(*analysed(synthetic_run)) == []


def test_the_no_offset_test_fails_on_a_broken_wait_test(synthetic_run):
    """The review's control: every wait-test shot moved to an outcome of the wrong parity (F = 0 for both variants),
    Part B left as it was. The difference between the two F's is still 0, but the test now fails."""

    def broken(labels, counts):
        return [{"100000": sum(c.values())} if lab["part"] == "W" else c for lab, c in zip(labels, counts)]

    w, q = analysed(synthetic_run, corrupt=broken)
    assert w["F_no"] == w["F_refocus"] == 0.0
    assert no_offset_failures(w, q) == ["F is not above 0.99: 0.0000 and 0.0000"]


def test_offline_a_steady_offset_on_m(synthetic_run):
    """A steady 47 kHz on M: the Ramsey loss at 3.4 us within 0.03 of 0.229 (exactly, (1 - cos(2 pi f 3.4 us)) / 2
    = 0.232), the echo loss below 0.02, REFOCUSABLE; the wait test's F above 0.9 with refocusing and at least 0.3 lower
    without. The end lines, with no offset, read NOT REPRODUCED."""
    w, q = analysed(synthetic_run, f_hz=F_OFFSET)
    m = q[str(wait.M)]
    assert abs(m["r"] - 0.229) < 0.03 and m["e"] < 0.02 and m["kind_of_loss"] == "REFOCUSABLE"
    assert w["F_refocus"] > 0.9 and w["F_no"] <= w["F_refocus"] - 0.3
    assert q[str(wait.L1)]["kind_of_loss"] == q[str(wait.L3)]["kind_of_loss"] == "NOT REPRODUCED"


def test_offline_the_rule_cannot_tell_plus_from_minus(synthetic_run):
    """A limitation, recorded as a test: +47 kHz or -47 kHz on M, drawn per shot, reads as the steady offset does.
    Part B and the wait test see M's phase only through its cosine, so they cannot tell +f from -f: the verdict is
    REFOCUSABLE again, and the losses and F's equal the steady offset's within shot noise. That the harness does switch
    per shot is checked apart (test_the_switching_harness_switches); the review found that this test alone cannot."""
    w, q = analysed(synthetic_run, f_hz=F_OFFSET, sign_switch=True)
    ws, qs = analysed(synthetic_run, f_hz=F_OFFSET)
    m, ms = q[str(wait.M)], qs[str(wait.M)]
    assert m["kind_of_loss"] == ms["kind_of_loss"] == "REFOCUSABLE"
    assert w["F_refocus"] > 0.9 and w["F_no"] <= w["F_refocus"] - 0.3
    assert abs(m["r"] - ms["r"]) < 0.03 and abs(m["e"] - ms["e"]) < 0.02
    assert abs(w["F_no"] - ws["F_no"]) < 0.02 and abs(w["F_refocus"] - ws["F_refocus"]) < 0.02


def sign_witness():
    """A circuit that tells +f from -f: Ramsey on M with a quarter-turn readout (H; a wait of 850 dt; S; H; measure).
    A phase phi gives P(1) = (1 + sin phi) / 2: at 47 kHz, 0.92 for +f and 0.08 for -f."""
    from qiskit import QuantumCircuit

    qc = QuantumCircuit(3, 1)
    qc.h(wait.M)
    qc.delay(850, wait.M, unit="dt")
    qc.s(wait.M)
    qc.h(wait.M)
    qc.measure(wait.M, 0)
    return wait.to_backend(qc, (0, 1, 2), synthetic_backend())


WITNESS_SHOTS = 4000
WITNESS_P1 = (1 + math.sin(2 * math.pi * F_OFFSET * 850 * DT)) / 2  # 0.922 for +f; 1 - it for -f


def harness_failures(counts: dict, trace: list) -> list[str]:
    """The switching harness's conditions that fail, on the witness: a sign recorded for every shot; both signs used,
    in numbers within 0.03 of half each; each sign's shots reading as that sign's steady offset (P(1) within 0.03);
    the counts being the kept outcomes; and P(1) overall the mixture of the two (within 0.04 of 0.5)."""
    if len(trace) != 1 or len(trace[0]["signs"]) != WITNESS_SHOTS:
        return ["no sign recorded for each shot"]
    signs, ones = np.asarray(trace[0]["signs"]), np.array([o == "1" for o in trace[0]["outcomes"]])
    out = []
    if set(signs.tolist()) != {0, 1} or abs(signs.mean() - 0.5) >= 0.03:
        out.append(f"the signs are not used about equally: {signs.mean():.3f} of shots took +f")
    else:
        if abs(ones[signs == 1].mean() - WITNESS_P1) >= 0.03 or abs(ones[signs == 0].mean() - (1 - WITNESS_P1)) >= 0.03:
            out.append("a sign's shots do not read as that sign's offset")
    kept: dict = {}
    for o in trace[0]["outcomes"]:
        kept[o] = kept.get(o, 0) + 1
    if kept != counts:
        out.append("the counts are not the kept outcomes")
    if abs(counts.get("1", 0) / WITNESS_SHOTS - 0.5) >= 0.04:
        out.append(f"P(1) is not the mixture: {counts.get('1', 0) / WITNESS_SHOTS:.3f}")
    return out


def test_the_switching_harness_switches():
    """The review: the harness itself, on a circuit where +f and -f differ. Run steady, the witness reads 0.92 with +f
    and 0.08 with -f; switched per shot, both signs are used about equally, each sign's shots read as its own offset,
    and the whole reads as their mixture, 0.5."""
    pytest.importorskip("qiskit_aer")
    c = sign_witness()
    for f, want in ((F_OFFSET, WITNESS_P1), (-F_OFFSET, 1 - WITNESS_P1)):
        steady = aer_counts([c], [WITNESS_SHOTS], seed=7, f_hz=f)[0]
        assert abs(steady.get("1", 0) / WITNESS_SHOTS - want) < 0.03
    trace: list = []
    switched = aer_counts([c], [WITNESS_SHOTS], seed=7, trace=trace, f_hz=F_OFFSET, sign_switch=True)[0]
    assert harness_failures(switched, trace) == []


def test_the_harness_test_fails_with_switching_off():
    """The review's control: with the per-shot switch turned off (the steady offset only), the harness test fails."""
    pytest.importorskip("qiskit_aer")
    trace: list = []
    steady = aer_counts([sign_witness()], [WITNESS_SHOTS], seed=7, trace=trace, f_hz=F_OFFSET)[0]
    assert harness_failures(steady, trace) == ["no sign recorded for each shot"]
    fake = [{"signs": np.ones(WITNESS_SHOTS, int), "outcomes": [k for k, n in steady.items() for _ in range(n)]}]
    assert any("not used about equally" in f for f in harness_failures(steady, fake))
    assert any("not the mixture" in f for f in harness_failures(steady, fake))


def test_offline_a_loss_that_refocusing_cannot_remove(synthetic_run):
    """A control beside the brief's four: white dephasing on M (T_phi 6.66 us, a Ramsey loss of 0.2 at 3.4 us) is
    the same with and without the echo, so the rule reads NOT REFOCUSABLE, and refocusing does not raise the wait
    test's F (gain within 0.05 of 0)."""
    w, q = analysed(synthetic_run, t_phi_s=6.66e-6)
    m = q[str(wait.M)]
    assert abs(m["r"] - 0.2) < 0.03 and abs(m["e"] - m["r"]) < 0.03
    assert m["kind_of_loss"] == "NOT REFOCUSABLE"
    assert abs(w["gain"]) < 0.05 and w["F_no"] < 0.7


# --------------------------------------------------------------------------- the job, through the guard (fakes)
class _Job:
    def __init__(self, jid, counts, charged_s=12):
        self._id, self._counts, self.charged_s = jid, counts, charged_s

    def job_id(self):
        return self._id

    def status(self):
        return "DONE"

    def result(self):
        return [
            SimpleNamespace(data=SimpleNamespace(c=SimpleNamespace(get_counts=lambda c=c: c))) for c in self._counts
        ]

    def metrics(self):
        return {"timestamps": {"running": "2026-10-10T12:00:00Z"}, "usage": {"qpu_charge_time_seconds": 12}}


class _Sampler:
    def __init__(self, service):
        self.service, self.calls, self.options_seen = service, [], []

    def __call__(self, mode):
        outer = self
        opts = SimpleNamespace(
            dynamical_decoupling=SimpleNamespace(enable=True),
            twirling=SimpleNamespace(enable_gates=True, enable_measure=True),
        )

        class _S:
            options = opts

            def run(self, pubs):
                outer.calls.append(pubs)
                outer.options_seen.append(
                    (opts.dynamical_decoupling.enable, opts.twirling.enable_gates, opts.twirling.enable_measure)
                )
                jid = f"fakejob{len(outer.calls):013d}"
                outer.service.jobs[jid] = _Job(jid, [{"0": n} for _, _, n in pubs])
                return outer.service.jobs[jid]

        return _S()


@pytest.fixture
def guarded(tmp_path, fez):
    from _fakes import FakeIBMService

    from manacitra.backends.base import Ledger
    from manacitra.backends.ibm import IBMCircuitsBackend

    svc = FakeIBMService()
    sampler = _Sampler(svc)
    ledger = Ledger(tmp_path / "ledger.jsonl")
    be = IBMCircuitsBackend("ibm_fez", service=svc, sampler_factory=sampler, ledger=ledger, cap_s=600)
    circuits, labels, shots = wait.wait_run((144, 143, 142), fez, copies=1, shots_wait=100, shots_b=50)
    return be, sampler, ledger, circuits, labels, shots


def test_a_wait_job_is_sent_once_with_its_own_pulses(guarded):
    from manacitra.backends.base import ResubmitRefused
    from manacitra.backends.ibm import CircuitJob

    be, sampler, ledger, circuits, labels, shots = guarded
    job = CircuitJob(circuits, labels, shots, name="wait-test")
    h = be.submit(job, log=lambda m: None)
    (pubs,) = sampler.calls
    assert [n for _, _, n in pubs] == shots and all(p[1] is None for p in pubs)
    assert sampler.options_seen == [(False, False, False)]  # no added decoupling, no twirling
    with pytest.raises(ResubmitRefused):
        be.submit(job, log=lambda m: None)
    assert len(sampler.calls) == 1
    run = be.fetch_counts(h)
    assert run["labels"] == labels and [sum(c.values()) for c in run["counts"]] == shots
    assert [e["event"] for e in ledger.entries()][-1] == "settled"


def test_a_wait_jobs_hash_follows_its_circuits(guarded):
    from manacitra.backends.ibm import CircuitJob

    _, _, _, circuits, labels, shots = guarded
    a = CircuitJob(circuits, labels, shots).job_hash("ibm", "ibm_fez")
    assert a == CircuitJob(list(circuits), [dict(x) for x in labels], list(shots)).job_hash("ibm", "ibm_fez")
    assert a != CircuitJob(circuits, labels, [s + 1 for s in shots]).job_hash("ibm", "ibm_fez")
    assert a != CircuitJob(circuits[::-1], labels, shots).job_hash("ibm", "ibm_fez")
    with pytest.raises(ValueError):
        CircuitJob(circuits, labels[:-1], shots)


def test_a_circuit_not_built_for_the_backend_is_refused(guarded):
    from manacitra.backends.ibm import CapExceeded, CircuitJob, IBMCircuitsBackend, SnapshotService, UsageUnavailable

    be, sampler, _, circuits, labels, shots = guarded
    logical = wait.wait_test_logical()
    with pytest.raises(CapExceeded, match="not on the backend"):
        be.submit(CircuitJob([logical], [{"part": "W"}], [10]), log=lambda m: None)
    assert sampler.calls == []
    offline = IBMCircuitsBackend("ibm_fez", service=SnapshotService("ibm_fez"))
    with pytest.raises(UsageUnavailable):
        offline.submit(CircuitJob(circuits, labels, shots), log=lambda m: None)
