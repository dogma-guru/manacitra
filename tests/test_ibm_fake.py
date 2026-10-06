# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""The IBM backend and the submit-once guard against a fake runtime: no network, no account."""

import json

import numpy as np
import pytest

pytest.importorskip("qiskit_ibm_runtime")

from _fakes import FakeIBMService, FakeRuntimeJob  # noqa: E402

from manacitra.backends.base import Ledger, MapJob, ResubmitRefused, submit_once  # noqa: E402
from manacitra.backends.ibm import CapExceeded, IBMBackend, SnapshotService, UsageUnavailable, safe_usage  # noqa: E402

PAIRS = [(114, 115), (70, 71), (142, 143)]


FakeService = FakeIBMService


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
    be = IBMBackend("ibm_fez", service=svc, sampler_factory=Sampler(svc, ledger.path), ledger=ledger)
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
    # Amendment A4: the cap is checked before anything is reserved, so a cap refusal is "refused", not a send
    (rec,) = ledger.entries()
    assert (
        rec["event"] == "refused"
        and "used 530 s + open reservations 0.0 s + estimate 43.4 s > cap 540 s" in rec["reason"]
    )
    # nothing was sent, so once the usage allows it the job goes without the override
    svc.used = 0.0
    submit_once(be, MapJob(PAIRS, shots=8000), ledger, log=lambda m: None)
    assert len(Sampler.calls) == 1


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


# --------------------------------------------------------------------------- Amendment A4: IBM reservations
def test_open_reservations_count_against_the_cap(setup):
    """The provider's usage lags a submission: an open reservation's estimate counts until a fetch settles it."""
    be, svc, ledger = setup
    be.cap_s = 310.0 + 10.0  # room for one job of 9.8 s (2 circuits x 8000 shots), not two
    j1, j2 = MapJob(PAIRS, positions=[1, 2]), MapJob(PAIRS, positions=[3, 4])
    h1 = be.submit(j1, log=lambda m: None)
    (res,) = ledger.reservations("ibm")
    assert res["seconds"] == pytest.approx(9.8) and not res["settled"]
    with pytest.raises(CapExceeded, match=r"open reservations 9\.8 s \+ estimate 9\.8 s > cap 320 s"):
        be.submit(j2)
    assert len(Sampler.calls) == 1
    # a fetch that reports the charged time settles it: from then on the job is the provider's usage figure to carry
    be.fetch(h1)
    assert ledger.reservations("ibm")[0]["settled"] and ledger.entries()[-1]["charged_s"] == 30
    assert ledger.open_seconds("ibm") == 0
    be.submit(j2, log=lambda m: None)  # 310 s used + nothing open + 9.8 s <= 320 s
    assert len(Sampler.calls) == 2


def test_a_fetch_without_the_charged_time_settles_nothing(setup):
    be, svc, ledger = setup
    h = be.submit(MapJob(PAIRS, positions=[1]), log=lambda m: None)
    svc.jobs[h.job_ids[0]].charged_s = None
    be.fetch(h)
    assert not ledger.reservations("ibm")[0]["settled"]


def test_a_failed_send_keeps_its_ibm_reservation(setup):
    be, svc, ledger = setup

    class Broken:
        def __init__(self, mode):
            pass

        def run(self, pubs):
            raise ConnectionError("the runtime did not answer")

    be._sampler_factory = Broken
    job = MapJob(PAIRS, positions=[1, 2])
    with pytest.raises(ConnectionError):
        be.submit(job)
    assert [e["event"] for e in ledger.entries()] == ["reserved", "sending", "failed"]
    assert ledger.open_seconds("ibm") == pytest.approx(9.8)
    with pytest.raises(ResubmitRefused, match="its reservation from .* \\(9.8 s in scope ibm\\) is open"):
        be.submit(job)


def test_a_resubmission_logs_the_reason(setup):
    be, _, ledger = setup
    job = MapJob(PAIRS, positions=[1])
    be.submit(job, log=lambda m: None)
    msgs = []
    be.submit(job, allow_resubmit=True, reason="the first job was cancelled on the platform", log=msgs.append)
    last = [e for e in ledger.entries() if e["event"] == "sending"][-1]
    assert last["allow_resubmit"] and last["resubmit_reason"] == "the first job was cancelled on the platform"
    assert "the first job was cancelled" in msgs[0]
