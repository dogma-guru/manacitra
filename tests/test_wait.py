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
from pathlib import Path
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


# --------------------------------------------------------------------------- Kickoff 48's circuits, rebuilt (A19)
K48 = "ibm_fez/k48-wait-test.json"


def _x_on(circuit, q: int) -> int:
    return sum(1 for i in circuit.data if i.operation.name == "x" and circuit.find_bit(i.qubits[0]).index == q)


def _t_m(circuit, backend, M: int) -> dict:
    """M's wait in the circuit as scheduled (wait.scheduled, padded, so its instructions tile time), as Kickoff 48's
    record defines T_M: from the end of M's first sx (its first H) to the start of its last, in dt; with M's idle
    windows and its whole timeline."""
    t, sch = backend.target, wait.scheduled(circuit, backend.target)
    clock, sx = 0, []
    for inst in sch.data:
        qs = tuple(sch.find_bit(q).index for q in inst.qubits)
        if M not in qs:
            continue
        name = inst.operation.name
        if name == "delay":
            d = int(inst.operation.duration)
        elif name in ("barrier", "rz"):
            d = 0
        else:
            d = int(round(t[name][qs].duration / backend.dt))
        if name == "sx":
            sx.append((clock, clock + d))
        clock += d
    return {
        "first_H_end_dt": sx[0][1],
        "last_H_start_dt": sx[-1][0],
        "T_M_dt": sx[-1][0] - sx[0][1],
        "T_M_us": (sx[-1][0] - sx[0][1]) * backend.dt * 1e6,
        "M_idle_windows_dt": wait.idle_windows(sch, M),
        "M_total_dt": clock,
    }


def test_kickoff_48s_circuits_are_rebuilt_by_the_package(fez):
    """Kickoff 48's circuits were built by manacitra.wait at f28642a, unedited, against the live ibm_fez target. Built
    again here for the offline snapshot, every circuit has the structure the run's dry run recorded on that snapshot
    (operation counts, refocusing pulses on each qubit, exact F = 1, the chain as the layout, and M's wait T_M); the
    unrefocused cells have the live build's counts and checks, and the refocused ones its 12 pulses on M (the end
    lines' pulses depend on the live durations); and Part B, for the live waits, the live build's labels, order and
    counts. The live durations are not in the snapshot, so the live T_M (2,611 dt) is checked as the record states it:
    M's three measure-and-reset windows of 836 dt and three of 6 dt, and five CZs of equal length."""
    rec = archive.load(K48)
    m, off = rec["meta"], rec["offline_build"]
    assert m["built_from"]["commit"].startswith("f28642a") and m["built_from"]["version"] == "0.4.0"
    assert "rebuilds every circuit" in m["built_from"]["rebuild"]
    ideal = wait.wait_test_ideal()
    for name, chain in m["chains"].items():
        M = chain[1]
        plain, refocused = wait.build_wait_test(chain, False, fez), wait.build_wait_test(chain, True, fez)
        assert _t_m(plain, fez, M) == off["T_M"][name], name
        for v, c in (("no", plain), ("refocus", refocused)):
            built = {k: int(n) for k, n in c.count_ops().items()}
            pulses = {str(q): _x_on(c, q) - _x_on(plain, q) for q in chain}
            assert built == off["cells"][f"{name}|{v}"]["count_ops"], (name, v)
            assert pulses == off["cells"][f"{name}|{v}"]["pulses_on_chain"], (name, v)
            assert list(c.layout.initial_index_layout(filter_ancillas=True)) == chain
            assert wait.fidelity(wait.exact_distribution(c), ideal) == pytest.approx(1.0, abs=1e-9)
            live = rec["cells"][f"{name}|{v}"]
            assert all(live["checks"].values()) and live["chain"] == chain and live["M"] == M
            assert pulses[str(M)] == live["pulses_on_chain"][str(M)] == (12 if v == "refocus" else 0)
            if v == "no":
                assert built == live["count_ops"], name
        # T_M is M's idle windows and its five CZs: on the snapshot with its CZ duration, live with five equal ones
        cz = int(round(fez.target["cz"][(chain[0], M)].duration / fez.dt))
        o = off["T_M"][name]
        assert o["T_M_dt"] == sum(o["M_idle_windows_dt"]) + 5 * cz == 2481
        tm = m["T_M"]["per_chain"][name]
        assert tm["M_idle_windows_dt"] == [836, 6, 836, 6, 836, 6] and tm["T_M_dt"] == 2611
        assert (tm["T_M_dt"] - sum(tm["M_idle_windows_dt"])) % 5 == 0
        assert wait.even_wait(tm["T_M_dt"]) == m["T_M"]["used_dt"][0] == 2612
    for key, recs in (("offline", off["part_B_circuits"]), ("live", rec["part_B_circuits"])):
        waits = sorted({r["label"]["tau_dt"] for r in recs})
        assert waits == (off["waits_dt"] if key == "offline" else m["waits_dt"])
        for e, r in zip(wait.part_b([tuple(g) for g in m["groups"]], waits), recs, strict=True):
            isa = wait.to_backend(e["circuit"], e["layout"], fez)
            assert {**e["label"], "qubits": e["layout"]} == r["label"] and r["pass"]
            assert {k: int(n) for k, n in isa.count_ops().items()} == r["count_ops"], (key, r["label"])
    sent = [lab for lab in rec["labels"] if lab["part"] == "B"]
    assert sent == [r["label"] for r in rec["part_B_circuits"]]  # Part B went in the package's order


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


# --------------------------------------------------------------------------- the active-neighbour Ramsey (A22)
#: Kickoff 53's four chains, drawn once by its posted procedure, and the two chains of Kickoffs 50 to 52
A22_CHAINS = {
    "30": (31, 30, 29),
    "74": (75, 74, 73),
    "121": (120, 121, 116),
    "103": (96, 103, 104),
    "144": (143, 144, 145),
    "143": (144, 143, 142),
}
FIXTURE_050 = "fixtures/wait-0.5.0-fakefez.json"


def _timeline(circuit, backend, qubits) -> list[tuple]:
    """(name, qubits, clbits, start, duration) in dt for every instruction on these qubits of a padded circuit: each
    qubit's instructions tile time from 0, and an instruction on several qubits starts when all are free at once.
    Written here, not taken from the package, so the package's own timing is checked against it."""
    t, clock, out = backend.target, {}, []
    for inst in circuit.data:
        qs = [circuit.find_bit(q).index for q in inst.qubits]
        if not set(qs) & set(qubits):
            continue
        name = inst.operation.name
        if name == "delay":
            d = int(inst.operation.duration)
        elif name in ("barrier", "rz"):
            d = 0
        else:
            d = int(round(t[name][tuple(qs)].duration / backend.dt))
        starts = {clock.get(q, 0) for q in qs}
        assert len(starts) == 1, f"not padded at {name} on {qs}"
        s = starts.pop()
        for q in qs:
            clock[q] = s + d
        out.append((name, qs, [circuit.find_bit(c).index for c in inst.clbits], s, d))
    return out


def _scheduled_on_chain(circuit, backend, chain):
    sch = wait.scheduled(circuit, backend.target)
    return _timeline(sch, backend, chain)


def _m_sequence(circuit, m) -> list[tuple]:
    """M's instructions in order: (name, an RZ's angle, else None)."""
    out = []
    for inst in circuit.data:
        if m in [circuit.find_bit(q).index for q in inst.qubits]:
            name = inst.operation.name
            out.append((name, float(inst.operation.params[0]) if name == "rz" else None))
    return out


@pytest.mark.parametrize("name", list(A22_CHAINS))
def test_the_active_ramseys_neighbours_measure_and_reset_when_the_wait_test_does(fez, name):
    """Amendment A22, 1c (timing): on Kickoff 53's four chains and on 143-144-145 and 144-143-142, built for the offline
    ibm_fez snapshot, every measure and reset on L1 and L3 in the active-neighbour Ramsey starts at the same dt, and
    lasts as long, as in the wait test as scheduled; and so does every other instruction on them, the CZs with M aside
    (they are delays now). M's wait, from the end of its first H to the start of its last, is the wait test's T_M."""
    chain = list(A22_CHAINS[name])
    l1, m, l3 = chain
    plain = wait.build_wait_test(chain, False, fez)
    w_tl = _scheduled_on_chain(plain, fez, chain)
    for phase in (0.0, math.pi / 2):
        r_tl = _timeline(wait.build_wait_ramsey(chain, fez, phase=phase), fez, chain)
        for q in (l1, l3):
            events = [(n, s, d, c) for n, qs, c, s, d in w_tl if qs == [q] and n in ("measure", "reset")]
            assert (
                events
                and [(n, s, d, c) for n, qs, c, s, d in r_tl if qs == [q] and n in ("measure", "reset")] == events
            )
            assert len([e for e in events if e[0] == "measure"]) == (3 if q == l1 else 2)
            keep = [(n, s, d) for n, qs, _, s, d in w_tl if q in qs and n not in ("barrier", "delay", "cz")]
            assert [(n, s, d) for n, qs, _, s, d in r_tl if q in qs and n not in ("barrier", "delay", "cz")] == keep
        sx_w = [(s, d) for n, qs, _, s, d in w_tl if n == "sx" and qs == [m]]
        sx_r = [(s, d) for n, qs, _, s, d in r_tl if n == "sx" and qs == [m]]
        assert len(sx_r) == 2 and sx_r == [sx_w[0], sx_w[-1]]
        assert sx_r[1][0] - sum(sx_r[0]) == 2481  # T_M on the snapshot (live: 2,611 dt)
        assert not [1 for n, qs, *_ in r_tl if n == "cz"]


@pytest.mark.parametrize("name", ["30", "144"])
def test_between_its_two_h_gates_m_only_waits(fez, name):
    """Amendment A22, 1c (M's operations): in the active-neighbour Ramsey, M's operations between its two H gates (each
    RZ, SX, RZ) are delays and, when a phase is asked for, the one inserted RZ, right after the first H; barriers, which
    are directives and last 0 dt, aside. The idle-neighbour Ramsey's M does H, a delay, H, and the RZ when asked."""
    chain = list(A22_CHAINS[name])
    m = chain[1]
    for phase in (0.0, math.pi / 2, -math.pi / 2, math.pi):
        for nb in wait.NEIGHBOURS:
            seq = _m_sequence(wait.build_wait_ramsey(chain, fez, nb, phase), m)
            i0 = [n for n, _ in seq].index("sx")
            i1 = len(seq) - 1 - [n for n, _ in seq][::-1].index("sx")
            assert [n for n, _ in seq].count("sx") == 2 and seq[i0 - 1][0] == seq[i0 + 1][0] == "rz"
            assert seq[i1 - 1][0] == seq[i1 + 1][0] == "rz" and seq[-1][0] == "measure"
            between = seq[i0 + 2 : i1 - 1]
            rz = [a for n, a in between if n == "rz"]
            assert {n for n, _ in between} <= {"delay", "barrier", "rz"}
            assert rz == ([phase] if phase else []) and (not phase or between[0] == ("rz", phase))
            assert [n for n, _ in between].count("delay") >= 1


@pytest.mark.parametrize("name", list(A22_CHAINS))
def test_the_ramseys_exact_values(fez, name):
    """Amendment A22, 1c (exact values): by the package's exact simulation, M's P(1) is 0 at a phase of 0, 0.5 at +90
    and -90 degrees and 1 at 180, in both Ramseys; and the wait test with the same phase gives F = cos^2(phase / 2)."""
    chain = list(A22_CHAINS[name])
    ideal = wait.wait_test_ideal()
    for deg, want in ((0, 0.0), (90, 0.5), (-90, 0.5), (180, 1.0)):
        phase = math.radians(deg)
        for nb in wait.NEIGHBOURS:
            p = wait.exact_distribution(wait.build_wait_ramsey(chain, fez, nb, phase))
            assert sum(v for k, v in p.items() if k[0] == "1") == pytest.approx(want, abs=1e-9), (nb, deg)
        f = wait.fidelity(wait.exact_distribution(wait.build_wait_test(chain, False, fez, phase)), ideal)
        assert f == pytest.approx(math.cos(phase / 2) ** 2, abs=1e-9), deg


def test_the_unplaced_wait_test_takes_its_phase_right_after_ms_first_h():
    """A22, ruling R1, A1: built without a backend, the wait test with a known phase carries one RZ(phase) on M,
    directly after M's first H, and nothing at a phase of 0; its exact F against the phase-0 ideal is cos^2(phase / 2)
    at 0, +90, -90 and 180 degrees."""
    ideal = wait.wait_test_ideal()
    for deg in (0, 90, -90, 180):
        phase = math.radians(deg)
        qc = wait.build_wait_test((0, 1, 2), phase=phase)
        on_m = [
            (i.operation.name, [float(x) for x in i.operation.params])
            for i in qc.data
            if wait.M in [qc.find_bit(q).index for q in i.qubits] and len(i.qubits) == 1
        ]
        first_h = [n for n, _ in on_m].index("h")
        rz = [(k, p) for k, (n, p) in enumerate(on_m) if n == "rz"]
        assert first_h == 0 and rz == ([(1, [phase])] if deg else [])
        assert [i.operation.name for i in qc.data][: 2 if deg else 1] == (["h", "rz"] if deg else ["h"])
        assert qc.find_bit(qc.data[0].qubits[0]).index == wait.M
        f = wait.fidelity(wait.exact_distribution(qc), ideal)
        assert f == pytest.approx(math.cos(phase / 2) ** 2, abs=1e-12), deg


def _run_code(record: str, file: str):
    """A run's code as the data record keeps it (verbatim lines of the script as run), executed as a module."""
    import sys
    import types

    text = archive.load(record)["source_code"][file]["text"]
    mod = types.ModuleType(file[:-3])
    mod.__file__ = f"{file}"  # the script's folder is not in this repository; its sys.path lines then add nothing used
    saved = list(sys.path)
    try:
        exec(compile(text, file, "exec"), mod.__dict__)  # the record's own text, as for Kickoff 47's builder
    finally:
        sys.path[:] = saved
    sys.modules[mod.__name__] = mod
    return mod


@pytest.fixture(scope="module")
def hw_code():
    import sys

    before = {k: sys.modules.get(k) for k in ("hw_50", "hw_51")}
    k50 = _run_code("ibm_fez/k50-neighbour-test.json", "hw_50.py")
    k51 = _run_code("ibm_fez/k51-known-offset.json", "hw_51.py")
    yield k50, k51
    for k, v in before.items():
        if v is None:
            sys.modules.pop(k, None)
        else:
            sys.modules[k] = v


@pytest.mark.parametrize("name", list(A22_CHAINS))
def test_the_active_ramsey_is_what_the_hardware_runs_built(fez, hw_code, name):
    """Amendment A22, 1c (equivalence): for the six chains on the offline ibm_fez snapshot, the package's active-
    neighbour Ramsey is structurally identical to Kickoff 50's R1 as hw_50.py builds it (the same operations on the same
    qubits, with the same parameters, at the same times), and with a phase of +90 or -90 degrees to Kickoff 51's R1 as
    hw_51.py builds it. Both scripts run here from the data records' copies. At a phase of 0, Kickoffs 51 to 53 inserted
    an explicit RZ(0) (a frame change of nothing); the package inserts nothing, and the circuits otherwise agree."""
    k50, k51 = hw_code
    chain = list(A22_CHAINS[name])
    c50, info = k50.build_chain(name, chain, fez)
    mine = wait.build_wait_ramsey(chain, fez)
    assert wait.structure(mine) == wait.structure(c50["R1"])
    assert _timeline(mine, fez, chain) == _timeline(c50["R1"], fez, chain)
    assert info["T_M"]["T_dt"] == 2481
    c51, _ = k51.build_chain(name, chain, fez)
    for deg in (-90, 90):
        theirs, ours = c51[("R1", deg)], wait.build_wait_ramsey(chain, fez, phase=math.radians(deg))
        assert wait.structure(ours) == wait.structure(theirs)
        assert _timeline(ours, fez, chain) == _timeline(theirs, fez, chain)
        assert wait.structure(wait.build_wait_test(chain, False, fez, math.radians(deg))) == wait.structure(
            c51[("W-no", deg)]
        )
    zero = [row for row in wait.structure(c51[("R1", 0)]) if row[0] != "rz" or row[3] != [0.0]]
    assert len(zero) == len(wait.structure(c51[("R1", 0)])) - 1 and zero == wait.structure(mine)


def test_the_check_defaults_to_active_neighbours_and_idle_is_050(fez):
    """Amendment A22, 1b: the Ramsey over the circuit's wait defaults to active neighbours. With neighbours="idle" it
    is 0.5.0's instrument exactly: for the six chains, the same circuit, instruction for instruction, as Manacitra at
    a55354d (v0.5.0) built for the offline snapshot: Part B's Ramsey on M alone at T_M made even (the fixture, built
    from a git archive of that commit). The wait test at its default phase of 0 is 0.5.0's too, without and with
    refocusing. Anything else for neighbours, or no backend, is refused."""
    import inspect

    sig = inspect.signature(wait.build_wait_ramsey)
    assert sig.parameters["neighbours"].default == "active" == wait.NEIGHBOURS[0]
    assert sig.parameters["phase"].default == 0.0
    assert inspect.signature(wait.build_wait_test).parameters["phase"].default == 0.0
    fx = json.loads((Path(__file__).parent / FIXTURE_050).read_text())
    assert (
        fx["built_with"]["manacitra_commit"].startswith("a55354d") and fx["built_with"]["manacitra_version"] == "0.5.0"
    )
    assert (
        fx["built_with"]["wait_py_sha256"]
        == archive.load("ibm_fez/k49-wait-test.json")["meta"]["built_from"]["wait_py_sha256"]
    )
    assert sorted(fx["chains"]) == sorted(A22_CHAINS)
    for name, rec in fx["chains"].items():
        chain = list(A22_CHAINS[name])
        assert rec["chain"] == chain
        default = wait.build_wait_ramsey(chain, fez)
        assert wait.structure(default) == wait.structure(wait.build_wait_ramsey(chain, fez, "active"))
        assert wait.structure(wait.build_wait_ramsey(chain, fez, "idle")) == rec["idle"]
        assert wait.structure(default) != rec["idle"]
        assert wait.structure(wait.build_wait_test(chain, False, fez)) == rec["W-no"]
        assert wait.structure(wait.build_wait_test(chain, True, fez)) == rec["W-ref"]
    with pytest.raises(ValueError, match="neighbours is one of"):
        wait.build_wait_ramsey(list(A22_CHAINS["144"]), fez, "quiet")
    with pytest.raises(ValueError, match="needs the backend"):
        wait.build_wait_ramsey(list(A22_CHAINS["144"]), None)


def test_the_prediction_is_the_runs_own():
    """Amendment A22, 1b: predicted_fidelity(F_ref, P(1) at T_M, P(1) at no wait) gives Kickoff 48's F_pred on every
    chain (the idle-neighbour Ramsey's) and Kickoff 53's F_pred1 on every cell (the active one's), from the archived
    quantities; and refuses a value that is not a probability."""
    a48 = archive.load("ibm_fez/k48-wait-test.json")["archived"]["analysis"]
    for n, p in a48["prediction"].items():
        tm = str(p["T_M_dt"])
        p1 = a48["part_B"][n]["ramsey_P1"]
        assert wait.predicted_fidelity(p["F_ref"], p1[tm], p1["0"]) == pytest.approx(p["F_pred"], abs=1e-12), n
    a53 = archive.load("ibm_fez/k53-revised-check.json")["archived"]["analysis"]
    for c in a53["cells"]:
        z = a53["chains"][c["M"]]["P1_Z"]
        assert wait.predicted_fidelity(c["F_ref"], c["loss_R1"] + z, z) == pytest.approx(c["F_pred1"], abs=1e-12)
        assert wait.predicted_fidelity(c["F_ref"], c["loss_R0"] + z, z) == pytest.approx(c["F_pred0"], abs=1e-12)
    for bad in ((1.2, 0.1, 0.0), (0.9, float("nan"), 0.0), (0.9, 0.1, -0.1)):
        with pytest.raises(ValueError, match="probabilities"):
            wait.predicted_fidelity(*bad)


RUNS_A22 = (
    "ibm_fez/k49-wait-test.json",
    "ibm_fez/k50-neighbour-test.json",
    "ibm_fez/k51-known-offset.json",
    "ibm_fez/k52-phase-sweep.json",
    "ibm_fez/k53-revised-check.json",
)


#: Amendment A23: Kickoffs 54 and 55, built by this package at e45f15d
RUNS_A23 = ("ibm_fez/k54-revised-check-day-2.json", "ibm_kingston/k55-revised-check.json")


#: Amendment A24: Kickoffs 56 to 62 (Kickoff 60 stopped at the draw: its record keeps its code and no counts)
RUNS_A24 = (
    "ibm_kingston/k56-phase-sweep.json",
    "ibm_kingston/k57-peak-check.json",
    "ibm_kingston/k58-placement-comparison.json",
    "ibm_kingston/k59-peak-check-day-2.json",
    "ibm_fez/k60-draw-stopped.json",
    "ibm_fez/k61-readout-check.json",
    "ibm_fez/k62-peak-check.json",
)


#: Amendment A25: test 7, the two-quadrature Ramsey on 143
RUNS_A25 = ("ibm_fez/t7-ramsey-xy.json",)


@pytest.mark.parametrize("path", RUNS_A22 + RUNS_A23 + RUNS_A24 + RUNS_A25)
def test_the_runs_code_is_kept_as_verbatim_lines(path):
    """Amendment A22, 2a: each run's analysis and circuit-building code is in its data record, as verbatim line
    ranges of the script as run (named by its SHA-256): each kept text has its recorded SHA-256 and line count,
    compiles, and carries no instance or account name, dollar amount, charge, usage block or path. (From Kickoff 56 on,
    a script's table of reused files names the hand-back scanner, scan_handback.py, by its SHA-256: a file name, not a
    path, kept as the line was run. Test 7's readings after the data, reading_t7.py, are kept whole, since its `main`
    is the readings.)"""
    rec = archive.load(path)
    names = {s["file"]: s["sha256"] for s in rec["meta"]["source_scripts"]}
    assert rec["source_code"]
    for file, code in rec["source_code"].items():
        assert code["file"] == file and code["sha256_as_run"] == names[file]
        text = code["text"]
        assert hashlib.sha256(text.encode()).hexdigest() == code["text_sha256"]
        assert len(text.splitlines()) == sum(b - a + 1 for a, b in code["kept_lines"])
        assert all(b <= code["lines_as_run"] for _, b in code["kept_lines"])
        compile(text, file, "exec")
        bad = re.findall(
            r"paid-|\bINSTANCE\b|instance_label|usd|\$|cap_|charge|\"usage\"|usage_remaining|QiskitRuntimeService"
            r"|literature|preprint|(?<!scan_)handback|/Users|/home/|[\w.+-]+@[\w-]+\.[\w.]+|\btr[a]ce\b",
            text,
            re.I,
        )
        assert not bad, (file, sorted(set(bad)))


@pytest.mark.parametrize("path", RUNS_A23)
def test_kickoffs_54_and_55_are_rebuilt_by_the_package(path):
    """Amendment A23: Kickoffs 54 and 55 built the verdict's circuits with this package at e45f15d, unedited
    (build_wait_test, and build_wait_ramsey with its default and with neighbours="idle"), and R1 at 180 and 270 degrees
    beside it. Built again here, for the offline snapshot each run's dry run used, every one of those circuits has the
    operation counts that dry run recorded, and M's wait T_M is as it recorded."""
    pytest.importorskip("qiskit_ibm_runtime")
    from qiskit_ibm_runtime import fake_provider

    rec = archive.load(path)
    m, off = rec["meta"], rec["offline_build"]
    assert m["built_from"]["commit"].startswith("e45f15d") and m["built_from"]["pull_request"] == 34
    backend = getattr(fake_provider, off["snapshot"]["class"])()
    drawn = off.get("draw_on_snapshot", {}).get("drawn")
    chains = [c["chain"] for c in drawn] if drawn else m["chains"]
    assert {str(c[1]) for c in chains} == set(off["checks"])
    for chain in chains:
        M, checks = chain[1], off["checks"][str(chain[1])]
        built = {
            "W-ref|0": wait.build_wait_test(chain, True, backend),
            **{f"W-no|{p}": wait.build_wait_test(chain, False, backend, math.radians(p)) for p in (0, 90)},
            **{f"R0|{p}": wait.build_wait_ramsey(chain, backend, "idle", math.radians(p)) for p in (0, 90)},
            **{f"R1|{p}": wait.build_wait_ramsey(chain, backend, phase=math.radians(p)) for p in (0, 90, 180, 270)},
        }
        for name, c in built.items():
            recorded = checks[name]["count_ops"]  # as the dry run wrote it: a dictionary, or its JSON text
            recorded = json.loads(recorded) if isinstance(recorded, str) else recorded
            assert {k: int(n) for k, n in c.count_ops().items()} == recorded, (path, M, name)
        assert _t_m(built["W-no|0"], backend, M)["T_M_dt"] == off["T_M"][str(M)]["T_dt"], (path, M)


# --------------------------------------------------------------------------- the check at the peak phase (A24)
def _sweep_p1(theta_deg: float) -> list:
    """M's exact P(1) in the sweep for a Ramsey whose offset is theta, the model of Kickoffs 57 to 62's code tests: a
    loss 0.9 sin²((phi + theta) / 2) above a floor of 0.01."""
    return [0.01 + 0.9 * math.sin(math.radians(p + theta_deg) / 2) ** 2 for p in wait.SWEEP_PHASES_DEG]


@pytest.mark.parametrize("theta,peak", [(0, 180), (40, 140), (-100, 280), (162, 18)])
def test_the_fit_and_the_peak_at_stated_offsets(theta, peak):
    """Amendment A24, 1d: on exact values the fit returns the stated offset and the peak 180 - theta (0, +40, -100 and
    +162 degrees give 180, 140, 280 and 18); on the wait test's series, F = 0.9 cos²((phi + theta) / 2), the wait test's
    offset; and with binomial draws at the kickoffs' shot counts (two copies of 2,000 per phase), within 2 degrees of
    the stated offset under every one of 50 seeds."""
    f = wait.sweep_fit(_sweep_p1(theta))
    assert f["theta_deg"] == pytest.approx(theta, abs=1e-9) and f["max_abs_residual"] < 1e-12
    assert f["amplitude"] == pytest.approx(0.45, abs=1e-12) and wait.peak_phase(f["theta_deg"]) == peak
    fw = wait.sweep_fit([0.9 * math.cos(math.radians(p + theta) / 2) ** 2 for p in wait.SWEEP_PHASES_DEG], "W-no")
    assert fw["theta_deg"] == pytest.approx(theta, abs=1e-9)
    assert wait.leftover(fw["theta_deg"], f["theta_deg"]) == pytest.approx(0.0, abs=1e-9)
    for seed in range(50):
        rng = np.random.default_rng(seed)
        y = [rng.binomial(4000, p) / 4000 for p in _sweep_p1(theta)]
        got = wait.sweep_fit(y)["theta_deg"]
        assert abs(wait.leftover(got, theta)) < 2.0, (theta, seed, got)


def test_the_peak_rounds_halves_up_and_wraps():
    """Kickoff 57's procedure: phi* = 180 - theta_R1 wrapped to [0, 360) and rounded to the nearest whole degree,
    halves up; the leftover wraps to (-180, +180]."""
    assert [wait.peak_phase(t) for t in (0.5, -0.5, 180.0, -180.0, 179.6, 359.0, 16.44)] == [
        180,
        181,
        0,
        0,
        0,
        181,
        164,
    ]
    assert wait.leftover(170, -170) == -20.0 and wait.leftover(-170, 10) == 180.0 and wait.leftover(10, -170) == 180.0
    with pytest.raises(ValueError, match="one finite value per phase"):
        wait.sweep_fit([0.1] * 5)
    with pytest.raises(ValueError, match="one finite value per phase"):
        wait.sweep_fit([0.1] * 5 + [float("nan")])
    with pytest.raises(ValueError, match="series is"):
        wait.sweep_fit([0.1] * 6, "W-ref")


#: Amendment A24: the records whose circuits were built by Kickoff 57's builders, and the snapshot to rebuild them on
PEAK_RUNS = {
    "ibm_kingston/k57-peak-check.json": ("hw_57.py", "FakeKingston"),
    "ibm_kingston/k59-peak-check-day-2.json": ("hw_59.py", "FakeKingston"),
    "ibm_fez/k62-peak-check.json": ("hw_62.py", "FakeFez"),
}


@pytest.fixture(scope="module")
def peak_code():
    """The builders of Kickoffs 57, 59 and 62, run from their data records' copies, with the modules they import:
    hw_50 and hw_51 (Kickoffs 50 and 51's records), analyse_52, analyse_53, analyse_57 and analyse_59 (their runs'
    records). They also import history 01's tabulate_history, which this repository names by its SHA-256 and does not
    keep; the builders do not use it, so an empty module stands in."""
    import sys
    import types

    names = ("hw_50", "hw_51", "analyse_52", "analyse_53", "analyse_57", "analyse_59", "tabulate_history")
    before = {k: sys.modules.get(k) for k in (*names, "hw_57", "hw_59", "hw_62")}
    _run_code("ibm_fez/k50-neighbour-test.json", "hw_50.py")
    _run_code("ibm_fez/k51-known-offset.json", "hw_51.py")
    _run_code("ibm_fez/k52-phase-sweep.json", "analyse_52.py")
    _run_code("ibm_fez/k53-revised-check.json", "analyse_53.py")
    sys.modules["tabulate_history"] = types.ModuleType("tabulate_history")
    _run_code("ibm_kingston/k57-peak-check.json", "analyse_57.py")
    _run_code("ibm_kingston/k59-peak-check-day-2.json", "analyse_59.py")
    yield {path: _run_code(path, file) for path, (file, _) in PEAK_RUNS.items()}
    for k, v in before.items():
        if v is None:
            sys.modules.pop(k, None)
        else:
            sys.modules[k] = v


def _job1_counts(rec: dict, m: int) -> dict:
    out: dict = {}
    for lab, cts in zip(rec["labels"], rec["counts"]):
        if lab["job"] == 1 and lab["M"] == m:
            out.setdefault(lab["phi_deg"], []).append(cts)
    return out


def _on_m(circuit, m: int) -> list:
    """M's instructions in order, delays and barriers left out: (name, parameters)."""
    return [
        (i.operation.name, [round(float(x), 12) for x in i.operation.params])
        for i in circuit.data
        if i.operation.name not in ("delay", "barrier") and m in [circuit.find_bit(q).index for q in i.qubits]
    ]


@pytest.mark.parametrize("path", list(PEAK_RUNS))
def test_the_sweep_and_the_check_are_what_the_hardware_runs_built(peak_code, path):
    """Amendment A24, 1d (equivalence): on the chains of Kickoffs 57, 59 and 62, for the offline snapshot of each
    processor, the package's sweep (`phase_sweep`) is structurally identical to job 1 as the run's own builder builds it
    (the same operations on the same qubits, with the same parameters, at the same times); `peak_check`, fed the run's
    own job 1 counts, returns the peak and the Ramsey's offset the run recorded before job 2 was built; and its job 2,
    W-no and R1 at phi* and at +90 and W-ref, is identical to the builder's job 2 at that phi*. The builder's Z ran on
    the chain's three lines with M into c5; the package's runs on M alone into c0, with M's instructions the same."""
    pytest.importorskip("qiskit_ibm_runtime")
    from qiskit_ibm_runtime import fake_provider

    rec = archive.load(path)
    hw = peak_code[path]
    backend = getattr(fake_provider, PEAK_RUNS[path][1])()
    for chain in rec["meta"]["chains"]:
        m = chain[1]
        theirs1, _, _ = hw.build_job1_chain(chain, backend)
        mine1 = wait.phase_sweep(chain, backend)
        assert (
            [e["label"]["phi_deg"] for e in mine1] == list(wait.SWEEP_PHASES_DEG) == list(rec["meta"]["phis_job1_deg"])
        )
        for e in mine1:
            c = theirs1[("R1", "sweep", e["label"]["phi_deg"])]
            assert wait.structure(e["circuit"]) == wait.structure(c), (path, m, e["label"])
            assert _timeline(e["circuit"], backend, chain) == _timeline(c, backend, chain)
        pc = wait.peak_check(chain, backend, _job1_counts(rec, m))
        recorded = rec["peaks"]["peaks"][str(m)]
        assert (
            pc["peak"]["phi_star_deg"]
            == recorded["phi_star_deg"]
            == rec["archived"]["analysis"]["phi_star_deg"][str(m)]
        )
        assert pc["peak"]["theta_R1_deg"] == pytest.approx(recorded["theta_R1_deg"], abs=1e-9)
        theirs2, _, _ = hw.build_job2_chain(chain, backend, recorded["phi_star_deg"])
        mine2 = {(e["label"]["circuit"], e["label"]["role"]): e for e in pc["circuits"]}
        assert set(mine2) == {
            ("W-no", "peak"),
            ("R1", "peak"),
            ("W-no", "plus90"),
            ("R1", "plus90"),
            ("W-ref", "ref"),
            ("Z", "zero"),
        }
        for (name, role, phi), c in theirs2.items():
            if name in ("R0", "P10", "P01"):
                continue  # beside the check in the kickoffs; not part of the package's job 2
            e = mine2[(name, role)]
            assert e["label"]["phi_deg"] == phi, (path, m, name, role)
            if name == "Z":
                assert _on_m(e["circuit"], m) == _on_m(c, m) and e["label"]["m_clbit"] == 0
                continue
            assert wait.structure(e["circuit"]) == wait.structure(c), (path, m, name, role)
            assert e["label"]["m_clbit"] == 5


def test_the_check_needs_the_whole_sweep(fez):
    """peak_check builds job 2 only from job 1's counts at every phase of the sweep; a missing phase is refused."""
    counts = {p: {"0" * 6: 900, "1" + "0" * 5: 100} for p in wait.SWEEP_PHASES_DEG[:-1]}
    with pytest.raises(ValueError, match="missing \\[300\\]"):
        wait.peak_check([144, 143, 142], fez, counts)


def test_the_survey(fez):
    """Amendment A24, 1d (the survey): on the offline ibm_fez snapshot, S0 and S1 cover every qubit; no instruction acts
    on two or more qubits; qubit i reads into clbit i; S0 has no gate and S1 one X per qubit; each qubit's exact P(1) is
    0 in S0 and 1 in S1 (its own instructions alone, since none touches another qubit); and both are, instruction for
    instruction, what Kickoff 62's builder (hw_62.py, from its record) builds."""
    from qiskit import QuantumCircuit

    survey = {e["label"]["circuit"]: e["circuit"] for e in wait.readout_survey(fez)}
    n = fez.num_qubits
    assert sorted(survey) == ["S0", "S1"] and n == 156
    for name, c in survey.items():
        assert c.num_clbits == n and all(len(i.qubits) == 1 for i in c.data)
        meas = {
            c.find_bit(i.qubits[0]).index: c.find_bit(i.clbits[0]).index
            for i in c.data
            if i.operation.name == "measure"
        }
        assert meas == {q: q for q in range(n)}
        gates = [(i.operation.name, c.find_bit(i.qubits[0]).index) for i in c.data if i.operation.name != "measure"]
        assert gates == ([] if name == "S0" else [("x", q) for q in range(n)])
        for q in (0, 72, 143, 155):
            one = QuantumCircuit(1, 1)
            for i in c.data:
                if c.find_bit(i.qubits[0]).index == q:
                    one.append(i.operation, [0], [0] if i.clbits else [])
            p1 = sum(v for k, v in wait.exact_distribution(one).items() if k[-1] == "1")
            assert p1 == pytest.approx(0.0 if name == "S0" else 1.0, abs=1e-12)


def test_the_survey_is_what_kickoff_62_built(peak_code, fez):
    hw = peak_code["ibm_fez/k62-peak-check.json"]
    theirs, qs = hw.build_survey(fez)
    assert qs == list(range(fez.num_qubits))
    for e in wait.readout_survey(fez):
        assert wait.structure(e["circuit"]) == wait.structure(theirs[(e["label"]["circuit"], None, 0)])


def test_the_readout_errors():
    """readout_errors: P(1|0) from S0, P(0|1) from S1, the copies pooled, e their mean; the screen is the caller's
    number; on Kickoff 62's job 0 counts it gives the survey the run recorded, qubit by qubit, and the 25 qubits above
    3%."""
    s0 = [{"000": 990, "001": 10}, {"000": 980, "100": 20}]
    s1 = {"111": 950, "110": 30, "011": 20}
    r = wait.readout_errors(s0, s1)
    assert r["0"] == pytest.approx({"P1_given_0": 0.005, "P0_given_1": 0.03, "e": 0.0175}, abs=1e-15)
    assert r["2"] == pytest.approx({"P1_given_0": 0.01, "P0_given_1": 0.02, "e": 0.015}, abs=1e-15)
    assert wait.readout_errors(s0, s1, 0.015)["0"]["above_limit"] is True
    with pytest.raises(ValueError, match="different numbers"):
        wait.readout_errors({"00": 1}, {"111": 1})
    with pytest.raises(ValueError, match="finite"):
        wait.readout_errors(s0, s1, float("nan"))
    rec = archive.load("ibm_fez/k62-peak-check.json")
    zero = [c for lab, c in zip(rec["labels"], rec["counts"]) if lab["job"] == 0 and lab["circuit"] == "S0"]
    one = [c for lab, c in zip(rec["labels"], rec["counts"]) if lab["job"] == 0 and lab["circuit"] == "S1"]
    got = wait.readout_errors(zero, one, rec["design"]["survey"]["screen"])
    for q, v in rec["survey"]["qubits"].items():
        assert got[q]["e"] == pytest.approx(v["e"], abs=1e-12) and got[q]["above_limit"] == v["above_3pct_measured"]
    assert sum(v["above_limit"] for v in got.values()) == 25


def test_the_0_6_0_check_is_unchanged():
    """Amendment A24, 1c: build_wait_test, build_wait_ramsey and predicted_fidelity keep their signatures and defaults;
    the peak check's job 2 holds 0.6.0's check at +90 beside it."""
    import inspect

    assert (
        str(inspect.signature(wait.build_wait_test))
        == "(chain: 'Sequence[int]', refocus: 'bool' = False, backend=None, phase: 'float' = 0.0)"
    )
    assert (
        str(inspect.signature(wait.build_wait_ramsey))
        == "(chain: 'Sequence[int]', backend, neighbours: 'str' = 'active', phase: 'float' = 0.0)"
    )
    assert (
        str(inspect.signature(wait.predicted_fidelity))
        == "(f_ref: 'float', p1_wait: 'float', p1_zero: 'float') -> 'float'"
    )
    assert wait.CHECK_PHASE_DEG == 90 and wait.SWEEP_PHASES_DEG == (0, 60, 120, 180, 240, 300)


# --------------------------------------------------------------------------- the two-quadrature Ramsey (A25)
T7 = "ibm_fez/t7-ramsey-xy.json"


def _seq(circuit, q: int) -> list:
    """The qubit's instructions in order: (name, an rz's angle in degrees, or a delay's length in dt)."""
    out = []
    for i in circuit.data:
        if q not in [circuit.find_bit(b).index for b in i.qubits]:
            continue
        op = i.operation
        if op.name == "rz":
            out.append(("rz", round(math.degrees(float(op.params[0])), 6)))
        elif op.name == "delay":
            out.append(("delay", int(op.duration)))
        else:
            out.append((op.name, None))
    return out


def _exact_p1(circuit) -> float:
    return sum(v for k, v in wait.exact_distribution(circuit).items() if k[-1] == "1")


def test_the_two_quadrature_ramsey(fez):
    """Amendment A25, 1c (the circuits): on the offline ibm_fez snapshot, at three waits, X and Y act on one qubit only;
    X is rz, sx, rz, the delay, rz, sx, rz, measure (no delay at no wait); Y is X with one rz(-90°) right before the
    last H (its rz, sx, rz); the delay equals even_wait of the requested wait, and so does the wait as scheduled; the
    exact noiseless P(1) is 0 for X and 0.5 for Y at every wait. The readout circuits measure the qubit alone, P10 with
    no gate and P01 after one X, with exact P(1) 0 and 1."""
    waits = (0, 7, 63)
    built = wait.ramsey_xy(143, fez, waits, readout=True)
    assert [e["label"]["circuit"] for e in built] == ["X"] * 3 + ["Y"] * 3 + ["P10", "P01"]
    for e in built:
        c, lab = e["circuit"], e["label"]
        assert {c.find_bit(b).index for i in c.data for b in i.qubits} == {143}
        assert c.num_clbits == 1 and lab["clbit"] == 0 and lab["qubit"] == 143
    by = {(e["label"]["circuit"], e["label"]["t_requested_us"]): e for e in built}
    for t in waits:
        wdt = wait.even_wait(t * 1e-6 / fez.dt, getattr(fez.target, "granularity", 1) or 1)
        x, y = by[("X", t)], by[("Y", t)]
        sx = _seq(x["circuit"], 143)
        h = [("rz", 90.0), ("sx", None), ("rz", 90.0)]
        assert sx == h + ([("delay", wdt)] if wdt else []) + h + [("measure", None)]
        k = len(sx) - 4
        assert _seq(y["circuit"], 143) == sx[:k] + [("rz", -90.0)] + sx[k:]
        for e in (x, y):
            assert e["label"]["wait_dt"] == wdt == e["label"]["scheduled_wait_dt"]
            assert e["label"]["scheduled_wait_us"] == pytest.approx(t, abs=1e-9)
        assert _exact_p1(x["circuit"]) == pytest.approx(0.0, abs=1e-12)
        assert _exact_p1(y["circuit"]) == pytest.approx(0.5, abs=1e-12)
    assert [n for n, _ in _seq(by[("P10", None)]["circuit"], 143)] == ["measure"]
    assert [n for n, _ in _seq(by[("P01", None)]["circuit"], 143)] == ["x", "measure"]
    assert _exact_p1(by[("P10", None)]["circuit"]) == pytest.approx(0.0, abs=1e-12)
    assert _exact_p1(by[("P01", None)]["circuit"]) == pytest.approx(1.0, abs=1e-12)
    with pytest.raises(ValueError, match="not negative"):
        wait.ramsey_xy(143, fez, [-1.0])


@pytest.fixture(scope="module")
def t7_code():
    """Test 7's builder, hw_t7.py, run from its data record's copy, with the modules it imports: hw_50 and hw_51
    (Kickoffs 50 and 51's records), and an empty module for history 01's tabulate_history, which it does not use to
    build."""
    import sys
    import types

    names = ("hw_50", "hw_51", "tabulate_history", "hw_t7")
    before = {k: sys.modules.get(k) for k in names}
    _run_code("ibm_fez/k50-neighbour-test.json", "hw_50.py")
    _run_code("ibm_fez/k51-known-offset.json", "hw_51.py")
    sys.modules["tabulate_history"] = types.ModuleType("tabulate_history")
    yield _run_code(T7, "hw_t7.py")
    for k, v in before.items():
        if v is None:
            sys.modules.pop(k, None)
        else:
            sys.modules[k] = v


def test_the_two_quadrature_ramsey_is_what_test_7_built(t7_code, fez):
    """Amendment A25, 1c (equivalence): on the offline ibm_fez snapshot, the package's circuits for 143 at the 64 waits,
    X and Y, are structurally identical, instruction for instruction, to what test 7's builder (hw_t7.py, from its
    record) builds, with the same wait in dt and the same wait as scheduled; and its readout circuits put the same
    instructions on 143 as the builder's P10 and P01. The labels' waits are those the run recorded."""
    circ, info = t7_code.build(fez)
    mine = wait.ramsey_xy(143, fez, range(64), readout=True)
    assert len(mine) == len(circ) == 130
    for e in mine:
        lab = e["label"]
        key = (lab["circuit"], None if lab["quadrature"] is None else int(lab["t_requested_us"]))
        if lab["quadrature"] is None:
            assert _on_m(e["circuit"], 143) == _on_m(circ[key], 143), key
            continue
        assert wait.structure(e["circuit"]) == wait.structure(circ[key]), key
        assert lab["wait_dt"] == info[key]["wait_dt"]
        assert lab["scheduled_wait_dt"] == info[key]["scheduled"]["T_dt"]
    rec = archive.load(T7)
    recorded = {(lab["circuit"], lab["t_requested_us"]): lab for lab in rec["labels"] if lab["circuit"] in ("X", "Y")}
    for e in mine[:128]:
        lab, r = e["label"], recorded[(e["label"]["circuit"], e["label"]["t_requested_us"])]
        assert (lab["wait_dt"], lab["scheduled_wait_dt"]) == (r["wait_dt"], r["scheduled_wait_dt"])


def test_the_copies_check_on_test_7():
    """On test 7's counts, the copies check gives the reading after the data the run recorded: a sum of z² of 871.7 on
    128 Ramsey circuits, and 0.95 on the two readout circuits."""
    rec = archive.load(T7)
    a = rec["archived"]["readings_after_the_data"]["A_copy_agreement"]
    for group, keep in (("ramsey", ("X", "Y")), ("readout", ("P10", "P01"))):
        idx = [k for k, lab in enumerate(rec["labels"]) if lab["circuit"] in keep]
        r = wait.copies_check([rec["labels"][k] for k in idx], [rec["counts"][k] for k in idx])
        assert r["dof"] == a[group]["n"] and r["sum_z2"] == pytest.approx(a[group]["sum_z2"], abs=1e-9)


def test_the_earlier_builders_and_fits_are_unchanged():
    """Amendment A25, 1b: the sweep, the peak, the survey and the one-quadrature Ramsey fit keep their signatures and
    defaults (build_wait_test, build_wait_ramsey and predicted_fidelity: test_the_0_6_0_check_is_unchanged)."""
    import inspect

    expected = {
        "phase_sweep": "(chain: 'Sequence[int]', backend, wait_test: 'bool' = False) -> 'list[dict]'",
        "sweep_fit": "(y, series: 'str' = 'R1') -> 'dict'",
        "peak_phase": "(theta_r1_deg: 'float') -> 'int'",
        "leftover": "(theta_w_deg: 'float', theta_r1_deg: 'float') -> 'float'",
        "peak_check": "(chain: 'Sequence[int]', backend, sweep_counts: 'dict') -> 'dict'",
        "readout_survey": "(backend) -> 'list[dict]'",
        "readout_errors": "(counts_zero, counts_one, limit: 'float | None' = None) -> 'dict'",
        "ramsey_fit": "(waits_us, p1) -> 'dict | None'",
    }
    for name, sig in expected.items():
        assert str(inspect.signature(getattr(wait, name))) == sig, name


def test_the_span_read_is_kept_as_verbatim_lines():
    """Amendment A26: the read of test 7's execution spans is in its record as verbatim lines of the script as run,
    named by its SHA-256, without the three lines that listed the other jobs it read: the kept text has its recorded
    SHA-256 and line count, compiles, names this job alone, and carries no instance name, path, email, dollar amount or
    usage figure. It reads the job's result through the account the run used, so, unlike the builders' kept code, it
    calls the account's service, by an instance name it reads from a file and never writes out."""
    rec = archive.load("ibm_fez/spans-t7.json")
    code = rec["source_code"]["span_check_t7.py"]
    assert code["cut_from"]["sha256"] == rec["meta"]["source_scripts"][0]["sha256"]
    text = code["text"]
    assert hashlib.sha256(text.encode()).hexdigest() == code["text_sha256"]
    assert len(text.splitlines()) == sum(b - a + 1 for a, b in code["kept_lines"]) == code["lines_as_run"] - 3
    assert code["dropped_inside_kept_span"] == [21, 22, 23]
    compile(text, "span_check_t7.py", "exec")
    jobs = re.findall(r'\("t\d", \d, "([a-z0-9]{20})"', text)
    assert jobs == [rec["job_id"]] == [archive.load("ibm_fez/t7-ramsey-xy.json")["meta"]["job_id"]]
    bad = re.findall(r"/Users|/home/|[\w.+-]+@[\w-]+\.[\w.]+|\$|instance=\"|usage_|\btr[a]ce\b|charge", text, re.I)
    assert not bad, sorted(set(bad))
