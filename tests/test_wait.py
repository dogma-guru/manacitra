# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""Amendment A18: Kickoff 47's Part B and the wait test, built by the package (manacitra.wait), checked three ways:
against the archive, instruction by instruction and verdict by verdict; exactly, by the package's own simulator; and on
Qiskit Aer, with a frequency offset planted by a noise pass written here (every delay on the chosen qubit becomes the
delay and an RZ of 2 pi f t). The Aer tests use no vendor noise model and no device data: they run on a synthetic
three-qubit target whose durations are round numbers chosen here."""

import hashlib
import json
import math
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


# --------------------------------------------------------------------------- Part B against Kickoff 47's archive
def test_part_b_matches_kickoff_47_instruction_by_instruction(fez):
    """Part B, built here for Kickoff 47's groups and waits on the snapshot, equals Kickoff 47's own builder's
    circuits as the archive records them (part_B_structure), instruction by instruction, and their operation counts
    equal those recorded from the circuits as sent (part_B_circuits); the order is the run's."""
    rec = archive.load(K47)
    us_of = {dt: us for us, dt in rec["tau_dt"].items()}
    built = wait.part_b(wait.KICKOFF_47_GROUPS, wait.KICKOFF_47_WAITS_DT)
    seen = set()
    for e in built:
        lab = e["label"]
        key = f"g{lab['group']}|{us_of[lab['tau_dt']]}|{lab['variant']}"
        if key in seen:
            continue
        seen.add(key)
        got = wait.structure(wait.to_backend(e["circuit"], e["layout"], fez))
        want = rec["part_B_structure"]["circuits"][key]
        assert [r[:3] for r in got] == [r[:3] for r in want], key
        assert all(a[3] == pytest.approx(b[3], abs=1e-12) for a, b in zip(got, want)), key
        isa = wait.to_backend(e["circuit"], e["layout"], fez)
        assert ops(isa) == rec["part_B_circuits"][key]["count_ops"], key
        assert rec["part_B_circuits"][key]["qubits"] == e["layout"]
    assert seen == set(rec["part_B_structure"]["circuits"]) == set(rec["part_B_circuits"])
    canon = json.dumps(rec["part_B_structure"]["circuits"], sort_keys=True, separators=(",", ":"))
    assert hashlib.sha256(canon.encode()).hexdigest() == rec["part_B_structure"]["circuits_sha256"]
    ours = [
        (x["label"]["group"], float(us_of[x["label"]["tau_dt"]]), x["label"]["variant"], x["label"]["copy"])
        for x in built
    ]
    theirs = [(a["group"], float(a["tau_us"]), a["variant"], a["copy"]) for a in rec["labels"] if a["part"] == "B"]
    assert ours == theirs


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


def aer_counts(circuits, shots, seed, **noise):
    """Every circuit run on Aer with its own shots; with sign_switch, each shot's offset is +f or -f, drawn per shot."""
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
            cts: dict = {}
            for i in range(n):
                key = plus[i] if sign[i] else minus[i]
                cts[key] = cts.get(key, 0) + 1
            out[k] = cts
    return out


@pytest.fixture(scope="module")
def synthetic_run():
    pytest.importorskip("qiskit_aer")
    be = synthetic_backend()
    circuits, labels, shots = wait.wait_run((0, 1, 2), be)
    return be, circuits, labels, shots


def analysed(synthetic_run, **noise):
    be, circuits, labels, shots = synthetic_run
    res = wait.analyse_wait_run(labels, aer_counts(circuits, shots, seed=1818, **noise), be.dt)
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


def test_offline_no_offset(synthetic_run):
    """No offset: Part B reads NOT REPRODUCED on every qubit, and the wait test's F with and without refocusing
    differ by less than 0.05."""
    w, q = analysed(synthetic_run)
    assert {row["kind_of_loss"] for row in q.values()} == {"NOT REPRODUCED"}
    assert abs(w["F_refocus"] - w["F_no"]) < 0.05


def test_offline_a_steady_offset_on_m(synthetic_run):
    """A steady 47 kHz on M: the Ramsey loss at 3.4 us within 0.03 of 0.229 (exactly, (1 - cos(2 pi f 3.4 us)) / 2
    = 0.232), the echo loss below 0.02, REFOCUSABLE; the wait test's F above 0.9 with refocusing and at least 0.3 lower
    without. The end lines, with no offset, read NOT REPRODUCED."""
    w, q = analysed(synthetic_run, f_hz=F_OFFSET)
    m = q[str(wait.M)]
    assert abs(m["r"] - 0.229) < 0.03 and m["e"] < 0.02 and m["kind_of_loss"] == "REFOCUSABLE"
    assert w["F_refocus"] > 0.9 and w["F_no"] <= w["F_refocus"] - 0.3
    assert q[str(wait.L1)]["kind_of_loss"] == q[str(wait.L3)]["kind_of_loss"] == "NOT REPRODUCED"


def test_offline_an_offset_that_switches_sign_per_shot(synthetic_run):
    """+47 kHz or -47 kHz on M, drawn per shot: REFOCUSABLE."""
    w, q = analysed(synthetic_run, f_hz=F_OFFSET, sign_switch=True)
    assert q[str(wait.M)]["kind_of_loss"] == "REFOCUSABLE"
    assert w["F_refocus"] > 0.9 and w["F_no"] <= w["F_refocus"] - 0.3


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
