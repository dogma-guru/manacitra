# Copyright 2026 Anish Patel
# SPDX-License-Identifier: Apache-2.0
"""Open Quantum (experimental): Rigetti processors through Open Quantum's Public plan. Needs the [openquantum] extra.

Ported from Kickoff 34b's runner: the account loading, the program preparation, the quote read in credits, the wave
submission and the counts parsing. Experimental: tested only against recorded-shape responses, never the network.

Two caveats carried from that run:

* **Recompilation and placement cannot be inspected on the Public plan.** The platform may recompile a submitted
  program and place it on other qubits; neither the compiled program nor any rewiring is returned. The check that
  every pair carries exactly 3 CZ applies to the program as sent, not as run.
* **No calibration snapshot is returned.** The provider publishes no per-edge or readout figures, so there is no
  published score x: the map rule is capped at MAP PRESENT (Kickoff 34, Amendment A1), and the dead-pair filter applies.

Credentials come only from the SDK's saved account (OpenQuantumService.from_saved_account); the client ID, the
client secret, the organization ID and any token are never printed, logged or stored. Programs are written on physical
qubits with no verbatim box (the platform's preprocessing closed a box with "};", which the provider rejected), every
single-qubit layer in one fixed native template (rz, rx(pi/2), rz, rx(pi/2), rz), so all variants share one gate
sequence and differ only in rz angles. Pair i is measured into c[i] (its first qubit) and c[2N - 1 - i] (its second),
the classical-index reading fixed in Kickoff 34b.
"""

from __future__ import annotations

import math
import re

import numpy as np

from ..circuits import CIRCUITS, offset_of, parse_label, unitary
from .base import Estimate, JobHandle, MapCounts, MapJob, Target

PROCESSOR = "rigetti:cepheus-1-108q"
CREDITS_PER_TASK = 3
BALANCE_FLOOR = 10


class QuoteRefused(RuntimeError):
    pass


# --------------------------------------------------------------------------- programs
def layers(label: str) -> list:
    """The variant's exact unitary with exactly 3 CZ, as single-qubit layers (2x2 matrices) between the CZs."""
    from qiskit.circuit.library import CZGate
    from qiskit.quantum_info import Operator
    from qiskit.synthesis import TwoQubitBasisDecomposer

    circ, _ = parse_label(label)
    qc = TwoQubitBasisDecomposer(CZGate(), euler_basis="U")(
        unitary(CIRCUITS[circ].c, offset_of(label)), _num_basis_uses=3
    )
    if qc.count_ops().get("cz", 0) != 3:
        raise RuntimeError("synthesis did not give 3 CZ")
    out, cur = [], [np.eye(2, dtype=complex), np.eye(2, dtype=complex)]
    for ins in qc.data:
        qs = [qc.find_bit(q).index for q in ins.qubits]
        if ins.operation.name == "cz":
            out += [tuple(cur), "cz"]
            cur = [np.eye(2, dtype=complex), np.eye(2, dtype=complex)]
        else:
            cur[qs[0]] = Operator(ins.operation).data @ cur[qs[0]]
    out.append(tuple(cur))
    return out


def template(m) -> list:
    """One single-qubit layer as rz, rx(pi/2), rz, rx(pi/2), rz, angles wrapped to (-pi, pi]."""
    from qiskit.synthesis import OneQubitEulerDecomposer

    t, p, lam = OneQubitEulerDecomposer("U").angles(m)

    def w(x):
        return float((x + math.pi) % (2 * math.pi) - math.pi)

    return [("rz", w(lam)), ("rx90",), ("rz", w(t + math.pi)), ("rx90",), ("rz", w(p + math.pi))]


def native_ops(label: str, synthesise: bool = False) -> list[tuple]:
    """The variant as (gate, local qubits, angle): the pinned sequence by default (see circuits.pinned), else a fresh
    synthesis."""
    if not synthesise:
        from ..circuits import pinned

        return [(g, tuple(qs), ang) for g, qs, ang in pinned()["native_rz_rx"][label]]
    seq = []
    for item in layers(label):
        if item == "cz":
            seq.append(("cz", (0, 1), None))
            continue
        for q in (0, 1):
            for g in template(item[q]):
                seq.append(("rz", (q,), g[1]) if g[0] == "rz" else ("rx", (q,), math.pi / 2))
    return seq


def pair_circuit(seq):
    from qiskit import QuantumCircuit

    qc = QuantumCircuit(2)
    for g, qs, ang in seq:
        if g == "cz":
            qc.cz(*qs)
        elif g == "rz":
            qc.rz(ang, qs[0])
        else:
            qc.rx(ang, qs[0])
    return qc


def p11_of(seq) -> float:
    from qiskit.quantum_info import Statevector

    return float(Statevector(pair_circuit(seq)).probabilities_dict().get("11", 0.0))


def bit_of(pairs) -> dict[int, int]:
    """Physical qubit -> classical bit: pair i's first qubit to c[i], its second to c[2N - 1 - i]."""
    n = 2 * len(pairs)
    m = {}
    for i, (a, b) in enumerate(pairs):
        m[a], m[b] = i, n - 1 - i
    return m


def qasm(label: str, pairs) -> str:
    """An OpenQASM 3 program running the variant on every pair at once, on physical qubits."""
    seq = native_ops(label)
    lines = ["OPENQASM 3.0;", f"bit[{2 * len(pairs)}] c;"]
    for g, qs, ang in seq:
        for a, b in pairs:
            phys = (a, b)
            if g == "cz":
                lines.append(f"cz ${a}, ${b};")
            elif g == "rz":
                lines.append(f"rz({ang!r}) ${phys[qs[0]]};")
            else:
                lines.append(f"rx({math.pi / 2!r}) ${phys[qs[0]]};")
    lines += [f"c[{k}] = measure ${q};" for q, k in sorted(bit_of(pairs).items(), key=lambda kv: kv[1])]
    return "\n".join(lines) + "\n"


_RE_GATE = re.compile(r"^(rz|rx)\(([^)]+)\)\s+\$(\d+);$|^cz\s+\$(\d+),\s*\$(\d+);$")
_RE_MEAS = re.compile(r"^c\[(\d+)\] = measure \$(\d+);$")


def parse(text: str):
    lines = text.splitlines()
    if lines[0] != "OPENQASM 3.0;" or not lines[1].startswith("bit["):
        raise ValueError("not a program this module wrote")
    end = next(i for i, ln in enumerate(lines) if _RE_MEAS.match(ln))
    gates, meas = [], {}
    for ln in lines[2:end]:
        m = _RE_GATE.match(ln)
        if not m:
            raise ValueError(f"unexpected line {ln!r}")
        if m.group(1):
            gates.append((m.group(1), (int(m.group(3)),), float(m.group(2))))
        else:
            gates.append(("cz", (int(m.group(4)), int(m.group(5))), None))
    for ln in lines[end:]:
        m = _RE_MEAS.match(ln)
        if not m:
            raise ValueError(f"unexpected line {ln!r}")
        meas[int(m.group(2))] = int(m.group(1))
    return gates, meas


def check_program(text: str, label: str, pairs, coupling_map, qubit_limit: int | None = None) -> dict:
    """3 CZ per pair on coupled edges, rx only at pi/2, nothing outside the pairs, one gate sequence on every pair,
    the measurement layout, and each pair's ideal P(11) to 1e-6."""
    from ..circuits import ideal_value

    edges = {(min(a, b), max(a, b)) for a, b in coupling_map}
    gates, meas = parse(text)
    per_cz, per_p, structure = [], [], set()
    for a, b in pairs:
        loc = {a: 0, b: 1}
        mine = [(g, tuple(loc[q] for q in qs), ang) for g, qs, ang in gates if all(q in loc for q in qs)]
        per_cz.append(sum(g == "cz" for g, _, _ in mine))
        per_p.append(p11_of(mine))
        structure.add(tuple((g, qs) for g, qs, _ in mine))
    in_pairs = {q for pr in pairs for q in pr}
    n = 2 * len(pairs)
    res = {
        "label": label,
        "n_pairs": len(pairs),
        "qubits": n,
        "qubit_limit": qubit_limit,
        "cz_per_pair": sorted(set(per_cz)),
        "cz_off_map": sum(1 for g in gates if g[0] == "cz" and (min(g[1]), max(g[1])) not in edges),
        "gates_outside_pairs": sum(1 for g in gates if not set(g[1]) <= in_pairs),
        "rx_angles": sorted({round(ang, 12) for g, _, ang in gates if g == "rx"}),
        "measure_map_ok": len(meas) == n
        and all(meas[a] == i and meas[b] == n - 1 - i for i, (a, b) in enumerate(pairs)),
        "same_sequence_on_every_pair": len(structure) == 1,
        "max_dev_P11_from_ideal": max(abs(p - ideal_value(label)) for p in per_p),
    }
    res["ok"] = (
        res["cz_per_pair"] == [3]
        and res["cz_off_map"] == 0
        and res["gates_outside_pairs"] == 0
        and res["rx_angles"] == [round(math.pi / 2, 12)]
        and res["measure_map_ok"]
        and res["same_sequence_on_every_pair"]
        and res["max_dev_P11_from_ideal"] < 1e-6
        and (qubit_limit is None or n <= qubit_limit)
    )
    return res


# --------------------------------------------------------------------------- counts
def string_positions(pairs) -> list[tuple[int, int]]:
    """Where each pair's two bits sit in an output key: c[k] is string position n - 1 - k."""
    n = 2 * len(pairs)
    bits = bit_of(pairs)
    return [(n - 1 - bits[a], n - 1 - bits[b]) for a, b in pairs]


def outcomes_from_output(counts: dict[str, int], pairs) -> np.ndarray:
    """Per pair, the four outcome counts s = a + 2 b, from a plain counts dict in the classical-index reading."""
    pos = string_positions(pairs)
    out = np.zeros((len(pairs), 4), dtype=np.int64)
    for key, m in counts.items():
        for i, (u, v) in enumerate(pos):
            out[i, int(key[u]) + 2 * int(key[v])] += m
    return out


def counts_of(out) -> dict[str, int]:
    if isinstance(out, dict) and all(isinstance(v, int) for v in out.values()):
        return {str(k): int(v) for k, v in out.items()}
    raise ValueError(f"unexpected output format: {type(out).__name__}")


def pair_covariance(outcomes) -> np.ndarray:
    """Per pair, P(11) - P(a = 1) P(b = 1): the bit-order check (above zero on average when the reading is right)."""
    o = np.asarray(outcomes, float)
    p = o / o.sum(axis=1, keepdims=True)
    return p[:, 3] - (p[:, 1] + p[:, 3]) * (p[:, 2] + p[:, 3])


# --------------------------------------------------------------------------- the backend
class OpenQuantumBackend:
    """Experimental. service: an OpenQuantumService (created from the saved account when not given)."""

    name = "openquantum"
    spends = True

    def __init__(
        self,
        processor: str = PROCESSOR,
        account: str = "default",
        service=None,
        job_name: str = "kept-share",
        credits_per_task: int = CREDITS_PER_TASK,
        budget_credits: float | None = None,
        balance_floor: float = BALANCE_FLOOR,
    ):
        self.processor = processor
        self.account = account
        self._service = service
        self.job_name = job_name
        self.credits_per_task = credits_per_task
        self.budget_credits = budget_credits
        self.balance_floor = balance_floor
        self._quotes: dict[str, dict] = {}
        self._discovery: dict | None = None

    @property
    def service(self):
        if self._service is None:
            from openquantum_sdk_qiskit import OpenQuantumService

            self._service = OpenQuantumService.from_saved_account(name=self.account)
        return self._service

    def _org(self):
        return self.service.scheduler._resolve_organization_id(None)  # used in calls only; never stored

    def discover(self) -> dict:
        d = self.service.scheduler.get_backend_class(self.processor)
        cap = d["constraint_data"]
        self._discovery = {
            "short_code": d["short_code"],
            "name": d["name"],
            "native_ops": cap.get("native_ops"),
            "limits": cap.get("limits"),
            "n_qubits": cap.get("n_qubits"),
            "vendor_noise_block": cap.get("noise") or {},
            "coupling_map": cap["topology"]["coupling_map"],
        }
        return self._discovery

    def target(self) -> Target:
        d = self._discovery or self.discover()
        names = [o["name"] for o in d["native_ops"] or []]
        gate = next((g for g in ("cz", "iswap", "cphase") if g in names), "unknown")
        from ..layout import undirected

        return Target(
            "openquantum",
            self.processor,
            d["n_qubits"],
            undirected(d["coupling_map"]),
            gate,
            None,
            None,
            notes=[
                "no per-edge or readout figures are published: no x",
                "recompilation and placement cannot be inspected on the Public plan",
            ],
        )

    def balance(self) -> dict:
        b = self.service.management.get_credit_balance(self._org())
        return {"spark_credits": b.spark_credits, "full_credits": b.full_credits}

    def programs(self, job: MapJob) -> list[tuple[int, str, str]]:
        d = self._discovery or self.discover()
        out = []
        for pos in job.active_positions:
            label = job.order[pos - 1]
            text = qasm(label, job.pairs)
            chk = check_program(
                text, label, job.pairs, d["coupling_map"], (d.get("limits") or {}).get("max_qubits_per_job")
            )
            if not chk["ok"]:
                raise ValueError(f"refused: program check failed at position {pos}: {chk}")
            out.append((pos, label, text))
        return out

    def quote(self, job: MapJob, committed_credits: float = 0.0) -> dict:
        """Prepare every task (no charge) and read the Public plan's standard-queue price, then test it."""
        from openquantum_sdk.enums import ExecutionPlanType, QueuePriorityType
        from openquantum_sdk.models import JobPreparationCreate

        sch = self.service.scheduler
        bal = self.balance()
        org = self._org()
        preps = []
        for pos, label, text in self.programs(job):
            up = sch.upload_job_input(file_content=text.encode())
            pr = sch.prepare_job(
                JobPreparationCreate(
                    organization_id=org,
                    backend_class_id=self.processor,
                    name=self.job_name,
                    upload_endpoint_id=up,
                    job_subcategory_id="oth:oth",
                    shots=job.shots,
                    configuration_data={"shots": job.shots},
                    submitted_with="sdk",
                    input_format="qasm",
                )
            )
            res = sch._wait_for_preparation(preparation_id=pr.id, timeout=300, interval=2.0)
            plan = next(p for p in res.quote if p.execution_plan_id == ExecutionPlanType.PUBLIC.value)
            prio = next(q for q in plan.queue_priorities if q.queue_priority_id == QueuePriorityType.STANDARD.value)
            preps.append(
                {
                    "position": pos,
                    "label": label,
                    "preparation": pr.id,
                    "status": res.status,
                    "shots_echoed": res.shots,
                    "plan": plan.name,
                    "credits": plan.price + prio.price_increase,
                }
            )
        q = sum(p["credits"] for p in preps)
        total = bal["spark_credits"] + bal["full_credits"]
        tests = {
            "exact_credits_every_task": all(p["credits"] == self.credits_per_task for p in preps),
            "within_budget": self.budget_credits is None or committed_credits + q <= self.budget_credits,
            "balance_after_at_least_floor": total - q >= self.balance_floor,
            "public_plan_every_task": all(p["plan"] == "Public Plan" for p in preps),
            "every_preparation_completed": all(p["status"] == "Completed" for p in preps),
            "shots_echoed": all(p["shots_echoed"] == job.shots for p in preps),
        }
        rec = {
            "balance_before": bal,
            "quote_credits": q,
            "tests": tests,
            "all_pass": all(tests.values()),
            "preparations": preps,
        }
        self._quotes[job.job_hash(self.name, self.processor)] = rec
        return rec

    def estimate(self, job: MapJob) -> Estimate:
        rec = self.quote(job)
        return Estimate(rec["quote_credits"], "credits", f"{len(rec['preparations'])} tasks; tests {rec['tests']}")

    def submit(self, job: MapJob, after: JobHandle | None = None) -> JobHandle:
        """Create the tasks of a passing quote, once each, never retried. `after`: an earlier wave that must have
        completed first."""
        from openquantum_sdk.enums import ExecutionPlanType, QueuePriorityType
        from openquantum_sdk.models import JobCreate

        rec = self._quotes.get(job.job_hash(self.name, self.processor))
        if not rec or not rec["all_pass"]:
            raise QuoteRefused("refused: no passing quote for this job; run estimate() first and read its tests")
        sch = self.service.scheduler
        if after is not None:
            st = [sch.get_job(j).status for j in after.job_ids]
            if any(s != "Completed" for s in st):
                raise RuntimeError(f"refused: the earlier wave has not completed ({st})")
        ids = []
        for p in rec["preparations"]:
            j = sch.create_job(
                JobCreate(
                    job_preparation_id=p["preparation"],
                    execution_plan_id=ExecutionPlanType.PUBLIC.value,
                    queue_priority_id=QueuePriorityType.STANDARD.value,
                )
            )
            ids.append(j.id)
        return JobHandle.for_job(self.name, self.processor, ids, job)

    def fetch(self, handle: JobHandle) -> MapCounts:
        sch = self.service.scheduler
        outcomes = []
        for jid in handle.job_ids:
            r = sch.get_job(jid)
            if r.status != "Completed":
                raise RuntimeError(f"task at position {handle.job_ids.index(jid) + 1} is {r.status}; nothing fetched")
            outcomes.append(outcomes_from_output(counts_of(sch.download_job_output(r)), handle.pairs))
        return MapCounts(
            handle.pairs,
            handle.order,
            handle.shots,
            outcomes,
            {"provider": "openquantum", "processor": self.processor, "reading": "classical-index (Kickoff 34b)"},
        )
