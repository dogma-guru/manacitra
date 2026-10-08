# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""Fake providers for the guard's tests: no network, no account, placeholder identifiers only.

They live in a module of their own, not in a test file, so that a child process started by multiprocessing (spawn)
can import them: the concurrent-submission tests in tests/test_guard_concurrency.py run each caller in its own process.
Each child records a send by creating a file in a directory the parent reads, because a child's memory is its own.
"""

from __future__ import annotations

import json
import sys
import types
from pathlib import Path
from types import SimpleNamespace

from manacitra.backends.base import GuardedSubmit, JobHandle, MapJob

FIX = Path(__file__).parent / "fixtures" / "openquantum"
PUB, STD = "00000000-0000-0000-0000-000000000001", "00000000-0000-0000-0000-000000000003"
ORG = "00000000-0000-0000-0000-000000000099"
OQ_PAIRS = [(0, 1), (2, 3), (5, 6)]
IBM_PAIRS = [(114, 115), (70, 71), (142, 143)]


def record_send(sends_dir, tag: str) -> None:
    """One file per send, so the parent can count the sends of every process."""
    import uuid

    d = Path(sends_dir)
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{tag}-{uuid.uuid4().hex}").write_text(tag)


def sends(sends_dir) -> list[str]:
    d = Path(sends_dir)
    return sorted(p.read_text() for p in d.iterdir()) if d.exists() else []


# --------------------------------------------------------------------------- a minimal spending backend
class FakeSpender(GuardedSubmit):
    """A spending backend whose send only records itself. barrier: both callers wait there inside _preflight, after
    the quick repeat check and before the guard's lock, which is the reviewer's scheduling point. crash: the process
    exits between the reservation and the send, with no clean-up, as a crash would."""

    name = "fake"
    processor = "local-only"

    def __init__(self, ledger, sends_dir, barrier=None, crash=False):
        self.ledger, self.sends_dir, self.barrier, self.crash = ledger, sends_dir, barrier, crash

    def _preflight(self, job, ledger):
        if self.barrier is not None:
            self.barrier.wait(timeout=30)
        return {}

    def _send(self, job):
        if self.crash:
            import os

            os._exit(17)
        record_send(self.sends_dir, job.name)
        return JobHandle.for_job(self.name, self.processor, [f"fake-{job.name}"], job)


# --------------------------------------------------------------------------- Open Quantum: the SDK and the service
def ns(d):
    return json.loads(json.dumps(d), object_hook=lambda x: SimpleNamespace(**x))


def sdk_stub_modules() -> dict:
    """The SDK's enums and request models, stubbed with placeholder identifiers."""
    enums = types.ModuleType("openquantum_sdk.enums")
    enums.ExecutionPlanType = SimpleNamespace(PUBLIC=SimpleNamespace(value=PUB))
    enums.QueuePriorityType = SimpleNamespace(STANDARD=SimpleNamespace(value=STD))
    models = types.ModuleType("openquantum_sdk.models")
    models.JobPreparationCreate = lambda **kw: kw
    models.JobCreate = lambda **kw: kw
    pkg = types.ModuleType("openquantum_sdk")
    return {"openquantum_sdk": pkg, "openquantum_sdk.enums": enums, "openquantum_sdk.models": models}


class FakeScheduler:
    def __init__(self, price=3, status="Completed", sends_dir=None):
        self.price, self.status, self.sends_dir = price, status, sends_dir
        self.uploads, self.created, self.outputs = [], [], {}

    def get_backend_class(self, code):
        return json.loads((FIX / "backend_class.json").read_text())

    def _resolve_organization_id(self, _):
        return ORG

    def upload_job_input(self, file_content):
        self.uploads.append(file_content.decode())
        return f"upload-{len(self.uploads)}"

    def prepare_job(self, req):
        assert req["organization_id"] == ORG and req["shots"] == 8000
        return SimpleNamespace(id=f"prep-{len(self.uploads)}")

    def _wait_for_preparation(self, preparation_id, timeout, interval):
        d = json.loads((FIX / "preparation.json").read_text())
        d["quote"][0]["price"] = self.price
        return ns(d)

    def create_job(self, req):
        assert req["execution_plan_id"] == PUB and req["queue_priority_id"] == STD
        jid = f"task-{len(self.created) + 1}"
        self.created.append(jid)
        if self.sends_dir is not None:
            record_send(self.sends_dir, "task")
        return SimpleNamespace(id=jid, status="Pending")

    def get_job(self, jid):
        rec = json.loads((FIX / "job_record.json").read_text())
        return SimpleNamespace(
            id=jid, status=self.status, message=None, calibration_data_url=rec["calibration_data_url"]
        )

    def download_job_output(self, r):
        return self.outputs[r.id]


class FakeOQService:
    def __init__(self, **kw):
        self.scheduler = FakeScheduler(**kw)
        bal = json.loads((FIX / "balance.json").read_text())
        self.management = SimpleNamespace(get_credit_balance=lambda org: SimpleNamespace(**bal))


# --------------------------------------------------------------------------- IBM: the runtime client
class FakeIBMService:
    def __init__(self, used=310.0, fail_usage=False):
        from qiskit_ibm_runtime.fake_provider import FakeFez

        self._b = FakeFez()
        self.used = used
        self.fail_usage = fail_usage
        self.jobs = {}

    def backend(self, name):
        return self._b

    def usage(self):
        if self.fail_usage:
            raise RuntimeError("no usage")
        return {
            "usage_consumed_seconds": self.used,
            "usage_limit_seconds": 600,
            "usage_remaining_seconds": 600 - self.used,
            "instance_" + "crn": "placeholder-not-a-real-value",
            "plan_" + "id": "placeholder",
            "by_instance": {"x": 1},
            "usage_period": {"start_time": "2026-09-07", "end_time": "2026-10-05"},
        }

    def job(self, job_id):
        return self.jobs[job_id]


class FakeRuntimeJob:
    def __init__(self, job_id, n_circuits, n_pairs, charged_s=30):
        self._id = job_id
        ones = "11" * n_pairs
        mixed = "01" + "11" * (n_pairs - 1)
        self._counts = [{ones: 7000, mixed: 1000} for _ in range(n_circuits)]
        self.charged_s = charged_s

    def job_id(self):
        return self._id

    def status(self):
        return "DONE"

    def result(self):
        return [
            SimpleNamespace(data=SimpleNamespace(c=SimpleNamespace(get_counts=lambda c=c: c))) for c in self._counts
        ]

    def metrics(self):
        return {"timestamps": {"running": "2026-10-05T12:00:00Z"}, "usage": {"qpu_charge_time_seconds": self.charged_s}}


class RecordingSampler:
    """A sampler factory whose run() records a send in sends_dir."""

    def __init__(self, service, sends_dir, n_pairs):
        self.service, self.sends_dir, self.n_pairs = service, sends_dir, n_pairs

    def __call__(self, mode):
        outer = self

        class _S:
            def run(self, pubs):
                record_send(outer.sends_dir, "ibm")
                jid = f"fakejob{len(outer.service.jobs) + 1:013d}"
                outer.service.jobs[jid] = FakeRuntimeJob(jid, len(pubs), outer.n_pairs)
                return outer.service.jobs[jid]

        return _S()


# --------------------------------------------------------------------------- what each child process runs
def _report(queue, who, fn):
    try:
        h = fn()
        queue.put((who, "sent", ",".join(h.job_ids)))
    except BaseException as e:  # noqa: BLE001 - every outcome goes back to the parent
        queue.put((who, type(e).__name__, str(e)))


def child_fake(who, ledger_path, sends_dir, barrier, queue, job_name="same", lock_timeout=30.0, crash=False):
    from manacitra.backends.base import Ledger

    be = FakeSpender(Ledger(ledger_path, lock_timeout=lock_timeout), sends_dir, barrier, crash=crash)
    _report(queue, who, lambda: be.submit(MapJob([(0, 1)], name=job_name), log=lambda m: None))


def child_openquantum(who, ledger_path, sends_dir, barrier, queue, positions, budget, floor=None):
    for name, mod in sdk_stub_modules().items():
        sys.modules[name] = mod
    from manacitra.backends import openquantum as oq
    from manacitra.backends.base import Ledger

    class Barriered(oq.OpenQuantumBackend):
        def _preflight(self, job, ledger, **kw):
            pre = super()._preflight(job, ledger, **kw)
            barrier.wait(timeout=30)
            return pre

    svc = FakeOQService(sends_dir=sends_dir)
    floor = {} if floor is None else {"balance_floor": floor}
    be = Barriered(service=svc, budget_credits=budget, ledger=Ledger(ledger_path), **floor)
    job = MapJob(OQ_PAIRS, positions=positions)

    def go():
        be.estimate(job)
        return be.submit(job, log=lambda m: None)

    _report(queue, who, go)


def balance_race_worker(who, ledger, sends_dir, barrier, queue):
    """The worker of the reviewer's balance_race.py (third review, Amendment A6), as written but for the imports and
    the layout: a barrier after preflight, a budget of 100, a floor of 90, wave a positions 1 to 8, wave b 9 to 16."""
    sys.modules.update(sdk_stub_modules())
    from manacitra.backends.base import Ledger
    from manacitra.backends.openquantum import OpenQuantumBackend

    class Synchronized(OpenQuantumBackend):
        def _preflight(self, job, ledger, **kw):
            pre = super()._preflight(job, ledger, **kw)
            barrier.wait(timeout=30)
            return pre

    backend = Synchronized(
        service=FakeOQService(sends_dir=Path(sends_dir)), budget_credits=100, balance_floor=90, ledger=Ledger(ledger)
    )
    job = MapJob(OQ_PAIRS, positions=list(range(1, 9)) if who == "a" else list(range(9, 17)))
    try:
        quote = backend.estimate(job)
        h = backend.submit(job, log=lambda _: None)
        queue.put({"who": who, "result": "sent", "quote": quote.amount, "tasks": len(h.job_ids)})
    except Exception as e:
        queue.put({"who": who, "result": type(e).__name__, "message": str(e)})


def child_ibm(who, ledger_path, sends_dir, barrier, queue, positions, cap_s):
    from manacitra.backends.base import Ledger
    from manacitra.backends.ibm import IBMBackend

    class Barriered(IBMBackend):
        def _preflight(self, job, ledger, **kw):
            pre = super()._preflight(job, ledger, **kw)
            barrier.wait(timeout=60)
            return pre

    svc = FakeIBMService(used=310.0)
    be = Barriered(
        "ibm_fez",
        service=svc,
        cap_s=cap_s,
        sampler_factory=RecordingSampler(svc, sends_dir, len(IBM_PAIRS)),
        ledger=Ledger(ledger_path),
    )
    _report(queue, who, lambda: be.submit(MapJob(IBM_PAIRS, positions=positions, shots=1000), log=lambda m: None))


def hold_lock(ledger_path, held, release):
    """Take the ledger's lock in this process and keep it until told to release it."""
    from manacitra.backends.base import Ledger

    with Ledger(ledger_path).lock():
        held.set()
        release.wait(timeout=60)
