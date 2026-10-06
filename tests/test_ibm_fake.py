# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""The IBM backend and the submit-once guard against a fake runtime: no network, no account."""

import json
from types import SimpleNamespace

import numpy as np
import pytest

pytest.importorskip("qiskit_ibm_runtime")

from manacitra.backends.base import Ledger, MapJob, ResubmitRefused, submit_once  # noqa: E402
from manacitra.backends.ibm import CapExceeded, IBMBackend, SnapshotService, UsageUnavailable, safe_usage  # noqa: E402

PAIRS = [(114, 115), (70, 71), (142, 143)]


class FakeService:
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
    def __init__(self, job_id, n_circuits, n_pairs):
        self._id = job_id
        ones = "11" * n_pairs
        mixed = "01" + "11" * (n_pairs - 1)
        self._counts = [{ones: 7000, mixed: 1000} for _ in range(n_circuits)]

    def job_id(self):
        return self._id

    def status(self):
        return "DONE"

    def result(self):
        return [
            SimpleNamespace(data=SimpleNamespace(c=SimpleNamespace(get_counts=lambda c=c: c))) for c in self._counts
        ]

    def metrics(self):
        return {"timestamps": {"running": "2026-10-05T12:00:00Z"}, "usage": {"qpu_charge_time_seconds": 30}}


class Sampler:
    """Records every run; checks that the ledger already holds the 'sending' record when it is called."""

    calls: list = []

    def __init__(self, service, ledger_path):
        self.service, self.ledger_path = service, ledger_path

    def __call__(self, mode):
        outer = self

        class _S:
            def run(self, pubs):
                entries = [json.loads(line) for line in open(outer.ledger_path)]
                assert entries[-1]["event"] == "sending", "the ledger record must be written before sending"
                Sampler.calls.append(pubs)
                jid = f"fakejob{len(Sampler.calls):013d}"
                outer.service.jobs[jid] = FakeRuntimeJob(jid, len(pubs), len(PAIRS))
                return outer.service.jobs[jid]

        return _S()


@pytest.fixture
def setup(tmp_path):
    Sampler.calls = []
    svc = FakeService()
    ledger = Ledger(tmp_path / "ledger.jsonl")
    be = IBMBackend("ibm_fez", service=svc, sampler_factory=Sampler(svc, ledger.path))
    return be, svc, ledger


def test_transpile_checks_every_circuit(setup):
    be, _, _ = setup
    isa, checks = be.transpile(MapJob(PAIRS))
    assert len(isa) == 16 and all(
        c["two_qubit_per_pair"] == [3] and c["swap"] == 0 and c["layout_kept"] for c in checks
    )


def test_submit_once_then_refuse_then_logged_resubmit(setup):
    be, svc, ledger = setup
    job = MapJob(PAIRS, shots=1000)
    h = submit_once(be, job, ledger, log=lambda m: None)
    assert len(Sampler.calls) == 1
    pubs = Sampler.calls[0]
    assert all(len(p) == 3 and p[1] is None and p[2] == 1000 for p in pubs)  # (circuit, None, shots)
    with pytest.raises(ResubmitRefused):
        submit_once(be, job, ledger)
    assert len(Sampler.calls) == 1
    msgs = []
    submit_once(be, job, ledger, allow_resubmit=True, log=msgs.append)
    assert len(Sampler.calls) == 2 and msgs
    sending = [e for e in ledger.entries() if e["event"] == "sending"]
    assert [e["allow_resubmit"] for e in sending] == [False, True]
    assert all(set(e) >= {"job_hash", "provider", "utc"} for e in sending)
    counts = be.fetch(h)
    # the mixed key "01" + "11" + "11" has its leftmost bits on the last pair (rightmost character = bit 0)
    p = counts.p11()
    assert p.shape == (16, 3) and np.allclose(p[:, 2], 7 / 8) and np.allclose(p[:, :2], 1.0)


def test_cap_refuses_before_anything_is_sent(setup):
    be, svc, ledger = setup
    svc.used = 530.0
    with pytest.raises(CapExceeded):
        submit_once(be, MapJob(PAIRS, shots=8000), ledger)
    assert Sampler.calls == []
    assert [e["event"] for e in ledger.entries()] == ["sending", "failed"]
    # a failed attempt still counts: a second try needs the explicit permission
    svc.used = 0.0
    with pytest.raises(ResubmitRefused):
        submit_once(be, MapJob(PAIRS, shots=8000), ledger)


def test_no_usage_no_submission(setup):
    be, svc, ledger = setup
    svc.fail_usage = True
    with pytest.raises(UsageUnavailable):
        be.submit(MapJob(PAIRS))
    assert Sampler.calls == []


def test_estimate_and_safe_usage(setup):
    be, svc, _ = setup
    assert be.estimate(MapJob(PAIRS, shots=8000)).amount == pytest.approx(0.3e-3 * 16 * 8000 + 5)
    u = safe_usage(svc.usage())
    assert set(u) == {
        "usage_consumed_seconds",
        "usage_limit_seconds",
        "usage_remaining_seconds",
        "usage_period",
        "read_utc",
    }


def test_target_reads_published_figures(setup):
    be, _, _ = setup
    t = be.target()
    assert t.two_qubit_gate == "cz" and len(t.coupling_map) == 176
    f = t.pairs[(114, 115)]
    assert f.x == pytest.approx(f.two_qubit_error + sum(f.readout_error))


def test_snapshot_service_never_submits():
    be = IBMBackend("ibm_fez", service=SnapshotService("ibm_fez"))
    with pytest.raises(UsageUnavailable):
        be.submit(MapJob(PAIRS))


def test_the_public_submit_is_the_guard(setup):
    """Amendment A3, 1a: backend.submit() twice refuses the second call before anything is sent."""
    be, _, ledger = setup
    be.ledger = ledger
    job = MapJob(PAIRS, shots=1000)
    be.submit(job, log=lambda m: None)
    assert len(Sampler.calls) == 1
    with pytest.raises(ResubmitRefused):
        be.submit(job)
    assert len(Sampler.calls) == 1
    msgs = []
    be.submit(job, allow_resubmit=True, log=msgs.append)
    assert len(Sampler.calls) == 2 and msgs
    assert [e["allow_resubmit"] for e in ledger.entries() if e["event"] == "sending"] == [False, True]
