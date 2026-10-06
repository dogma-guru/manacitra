# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""IBM Quantum through Qiskit Runtime (SamplerV2). Needs the [ibm] extra.

Credentials come only from Qiskit Runtime's own saved-account mechanism (QiskitRuntimeService()) or its environment
variables; nothing here reads, prints, logs or stores a token, a CRN, an instance or an account.

Before any submission:

1. the usage is read from the runtime client (numbers and dates only; every identifier field is dropped);
2. the job is estimated at 0.3 ms per shot plus 5 s (Kickoffs 32 to 35; the observed rate was about 0.28 ms);
3. every circuit is transpiled onto the pairs and refused unless each pair carries exactly 3 CZ, nothing is routed,
   and the layout is kept;
4. under the ledger's lock, the job is refused if used + the estimates of every open IBM reservation + this job's
   estimate exceeds the cap (default 540 s of the Open plan's 600 s window). The provider's usage figure lags a
   submission, so the open reservations stand in for jobs it does not yet count. This job's estimate is reserved in
   the ledger before it is sent; a fetch that reports the job's charged time settles the reservation.

Each pub is (circuit, None, shots): the second slot holds parameter values, and passing (circuit, shots) is rejected by
the sampler (the fix recorded in Kickoff 33's scorecard).
"""

from __future__ import annotations

import re

from ..circuits import parallel_circuit, require_three_per_pair
from ..keptshare import pair_outcomes_from_bitstrings
from .base import (
    Estimate,
    GuardedSubmit,
    JobHandle,
    Ledger,
    MapCounts,
    MapJob,
    PairFigures,
    SpendRefused,
    Target,
    utc_now,
)

SECONDS_PER_SHOT = 0.3e-3
OVERHEAD_S = 5.0
CAP_S = 540.0
#: The ledger scope of IBM reservations: the usage window is the account's, across processors
IBM_SCOPE = "ibm"
_ID_FIELD = re.compile(r"id|crn|instance|account|email|name|user|plan|token|key", re.I)


class CapExceeded(SpendRefused):
    pass


class UsageUnavailable(SpendRefused):
    pass


def estimate_seconds(total_shots: int) -> float:
    return SECONDS_PER_SHOT * total_shots + OVERHEAD_S


def safe_usage(raw: dict) -> dict:
    """The usage response with every identifier-like field dropped: numbers, booleans and dates only."""
    keep = {}
    for k, v in (raw or {}).items():
        if _ID_FIELD.search(k):
            continue
        if isinstance(v, dict):
            keep[k] = {kk: str(vv) for kk, vv in v.items() if not _ID_FIELD.search(kk)}
        elif isinstance(v, (int, float, bool)) or v is None:
            keep[k] = v
    keep["read_utc"] = utc_now()
    return keep


class IBMBackend(GuardedSubmit):
    """IBM Quantum through Qiskit Runtime. submit() is the submit-once guard (GuardedSubmit): _preflight reads the
    usage and checks the transpiled circuits, _reserve checks the cap against the ledger's open reservations under the
    ledger's lock, and _send sends."""

    name = "ibm"
    spends = True

    def __init__(
        self,
        processor: str,
        service=None,
        cap_s: float = CAP_S,
        sampler_factory=None,
        seed_transpiler: int = 31,
        optimization_level: int = 1,
        ledger: Ledger | None = None,
    ):
        self.processor = processor
        self.ledger = ledger
        self._service = service
        self.cap_s = cap_s
        self._sampler_factory = sampler_factory
        self.seed_transpiler = seed_transpiler
        self.optimization_level = optimization_level
        self.usage_log: list[dict] = []
        self._prepared: dict[str, tuple] = {}

    # -- the runtime client, created lazily from the saved account
    @property
    def service(self):
        if self._service is None:
            from qiskit_ibm_runtime import QiskitRuntimeService

            self._service = QiskitRuntimeService()
        return self._service

    def backend(self):
        return self.service.backend(self.processor)

    # -- the protocol
    def target(self) -> Target:
        b = self.backend()
        t = b.target
        gate = next((g for g in ("cz", "ecr", "cx") if g in t.operation_names), "unknown")
        props = None
        try:
            props = b.properties()
        except Exception:
            props = None
        readout = {}
        for q in range(b.num_qubits):
            m = t["measure"].get((q,)) if "measure" in t.operation_names else None
            readout[q] = m.error if m is not None else None
        qubits = {}
        for q in range(b.num_qubits):
            qp = t.qubit_properties[q] if t.qubit_properties else None
            qubits[q] = {"readout_error": readout[q], "T1_s": getattr(qp, "t1", None), "T2_s": getattr(qp, "t2", None)}
        pairs, cmap = {}, []
        for (a, b2), ip in t[gate].items() if gate in t.operation_names else []:
            key = (min(a, b2), max(a, b2))
            if key not in pairs:
                cmap.append(key)
            err = ip.error if ip is not None else None
            prev = pairs.get(key)
            if prev is not None and prev.two_qubit_error is not None and (err is None or prev.two_qubit_error <= err):
                continue
            ro = (readout[key[0]], readout[key[1]])
            x = err + ro[0] + ro[1] if err is not None and None not in ro else None
            stamps = {}
            if props is not None:
                try:
                    stamps["two_qubit_error"] = str(props.gate_property(gate, [a, b2])["gate_error"][1])
                    stamps["readout"] = [str(props.qubit_property(q)["readout_error"][1]) for q in key]
                except Exception:
                    pass
            pairs[key] = PairFigures(key, err, ro, x, stamps)
        notes = []
        if props is not None:
            notes.append(f"properties last updated {props.last_update_date}")
        return Target("ibm", self.processor, b.num_qubits, cmap, gate, pairs, qubits, notes=notes)

    def estimate(self, job: MapJob) -> Estimate:
        return Estimate(estimate_seconds(job.total_shots), "s", f"0.3 ms x {job.total_shots} shots + 5 s")

    def usage(self) -> dict:
        try:
            raw = self.service.usage()
        except Exception as e:
            raise UsageUnavailable(
                f"the runtime client gave no usage ({type(e).__name__}); read it on the platform "
                "dashboard and decide before submitting"
            ) from None
        u = safe_usage(raw)
        if "usage_consumed_seconds" not in u:
            raise UsageUnavailable("the usage response has no usage_consumed_seconds")
        self.usage_log.append(u)
        return u

    def _cap(self, job: MapJob, used: float, open_s: float) -> dict:
        est = estimate_seconds(job.total_shots)
        total = used + open_s + est
        return {
            "used_s": used,
            "open_reservations_s": open_s,
            "estimate_s": est,
            "total_s": total,
            "cap_s": self.cap_s,
            "within_cap": total <= self.cap_s,
        }

    @staticmethod
    def _cap_failure(rec: dict) -> str:
        return (
            f"used {rec['used_s']:.0f} s + open reservations {rec['open_reservations_s']:.1f} s + estimate "
            f"{rec['estimate_s']:.1f} s > cap {rec['cap_s']:.0f} s"
        )

    def check_cap(self, job: MapJob) -> dict:
        """The cap as it stands now: the usage read now, plus the ledger's open IBM reservations, plus this job. For a
        look before submitting; the guard checks it again under the ledger's lock."""
        u = self.usage()
        rec = {
            **self._cap(job, float(u["usage_consumed_seconds"]), self._ledger().open_seconds(IBM_SCOPE)),
            "read_utc": u["read_utc"],
        }
        if not rec["within_cap"]:
            raise CapExceeded("refused: " + self._cap_failure(rec))
        return rec

    def _preflight(self, job: MapJob, ledger: Ledger) -> dict:
        """Before the lock: the usage (refused if it cannot be read) and the transpile checks."""
        u = self.usage()
        backend = self.backend()
        isa, checks = self.transpile(job, backend)
        self._prepared[job.job_hash(self.name, self.processor)] = (backend, isa, checks)
        return {"used_s": float(u["usage_consumed_seconds"]), "read_utc": u["read_utc"]}

    def _reserve(self, job: MapJob, pre: dict, entries: list[dict]) -> tuple[list[str], dict]:
        """Under the lock: used + every open IBM reservation + this job's estimate, against the cap."""
        rec = {
            **self._cap(job, pre["used_s"], self._ledger().open_seconds(IBM_SCOPE, entries)),
            "read_utc": pre["read_utc"],
        }
        self._last_cap = rec
        if not rec["within_cap"]:
            return [self._cap_failure(rec)], {}
        return [], {"scope": IBM_SCOPE, "seconds": rec["estimate_s"], "used_s_at_send": rec["used_s"]}

    def _refusal(self, failed: list[str]) -> CapExceeded:
        return CapExceeded("refused: " + "; ".join(failed))

    def transpile(self, job: MapJob, backend=None) -> tuple[list, list[dict]]:
        """Every active circuit on the pairs, each checked: exactly 3 CZ per pair, no swaps, layout kept."""
        from qiskit.transpiler import generate_preset_pass_manager

        backend = backend or self.backend()
        t = backend.target
        missing = [p for p in job.pairs if (t["cz"].get(p) or t["cz"].get(p[::-1])) is None]
        if missing:
            raise ValueError(f"refused: pairs without a reported CZ today: {missing}")
        layout = [q for p in job.pairs for q in p]
        pm = generate_preset_pass_manager(
            backend=backend,
            optimization_level=self.optimization_level,
            initial_layout=layout,
            seed_transpiler=self.seed_transpiler,
        )
        isa, checks = [], []
        built: dict = {}
        for pos in job.active_positions:
            label = job.order[pos - 1]
            if label not in built:
                built[label] = parallel_circuit(label, len(job.pairs))
            tc = pm.run(built[label])
            init = list(tc.layout.initial_index_layout(filter_ancillas=True))
            rec = {
                "position": pos,
                "label": label,
                **require_three_per_pair(tc, job.pairs),
                "layout_kept": init == layout,
            }
            if not rec["layout_kept"]:
                raise ValueError(f"refused: the transpiler moved the layout at position {pos}")
            checks.append(rec)
            isa.append(tc)
        return isa, checks

    def _send(self, job: MapJob) -> JobHandle:
        """The raw send, reached only through submit() after the guard has reserved the job: SamplerV2."""
        h = job.job_hash(self.name, self.processor)
        backend, isa, checks = self._prepared.pop(h, None) or (self.backend(), *self.transpile(job))
        pubs = [(c, None, job.shots) for c in isa]
        if self._sampler_factory is None:
            from qiskit_ibm_runtime import SamplerV2

            sampler = SamplerV2(mode=backend)
        else:
            sampler = self._sampler_factory(mode=backend)
        rj = sampler.run(pubs)
        handle = JobHandle.for_job(self.name, self.processor, [rj.job_id()], job)
        self.last_submission = {"cap": getattr(self, "_last_cap", None), "checks": checks, "handle": handle}
        return handle

    def fetch(self, handle: JobHandle) -> MapCounts:
        rj = self.service.job(handle.job_ids[0])
        status = str(rj.status())
        if "DONE" not in status:
            raise RuntimeError(f"job {handle.job_ids[0]} is {status}; nothing fetched")
        res = rj.result()
        outcomes = []
        for k in range(len(handle.order)):
            data = res[k].data
            reg = data.c if hasattr(data, "c") else next(iter(data.values()))
            outcomes.append(pair_outcomes_from_bitstrings(reg.get_counts(), len(handle.pairs)))
        meta = {"provider": "ibm", "processor": self.processor, "job_id": handle.job_ids[0]}
        try:
            m = rj.metrics()
            meta["timestamps"] = m.get("timestamps")
            meta["charged_s"] = (m.get("usage") or {}).get("qpu_charge_time_seconds")
        except Exception:
            pass
        if meta.get("charged_s") is not None:  # the provider now counts this job: its reservation is settled
            self._ledger().append(
                {"event": "settled", "job_hash": handle.job_hash, "utc": utc_now(), "charged_s": meta["charged_s"]}
            )
        return MapCounts(handle.pairs, handle.order, handle.shots, outcomes, meta)


class SnapshotService:
    """An offline stand-in for the runtime client: qiskit-ibm-runtime's fake_provider snapshot of a processor, for dry
    runs with no account. It reports no usage, so a submission through it is always refused."""

    def __init__(self, processor: str):
        from qiskit_ibm_runtime import fake_provider

        name = "Fake" + processor.removeprefix("ibm_").capitalize()
        if not hasattr(fake_provider, name):
            raise ValueError(f"no offline snapshot named {name} in qiskit_ibm_runtime.fake_provider")
        self._backend = getattr(fake_provider, name)()

    def backend(self, name: str):
        return self._backend

    def usage(self):
        raise UsageUnavailable("an offline snapshot has no usage; nothing can be submitted through it")
