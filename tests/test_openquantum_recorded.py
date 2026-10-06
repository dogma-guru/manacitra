# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""The experimental Open Quantum adapter against recorded-shape responses. Never the network."""

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from _fakes import OQ_PAIRS, ORG, FakeOQService, sdk_stub_modules

from manacitra.backends import openquantum as oq
from manacitra.backends.base import MapJob
from manacitra.circuits import ORDER_16

PAIRS = OQ_PAIRS
FakeService = FakeOQService


@pytest.fixture(autouse=True)
def sdk_stub(monkeypatch):
    """The SDK's enums and request models, stubbed with placeholder identifiers."""
    for name, mod in sdk_stub_modules().items():
        monkeypatch.setitem(sys.modules, name, mod)


def output_for(pairs, outcomes):
    """A plain counts dict in the classical-index reading, from per-pair outcomes (pairs independent)."""
    n = 2 * len(pairs)
    pos = oq.string_positions(pairs)
    counts = {}
    for combo in np.ndindex(*(4,) * len(pairs)):
        m = int(np.prod([outcomes[i][s] for i, s in enumerate(combo)]))
        if m == 0:
            continue
        key = ["0"] * n
        for i, s in enumerate(combo):
            u, v = pos[i]
            key[u], key[v] = str(s & 1), str(s >> 1)
        counts["".join(key)] = counts.get("".join(key), 0) + m
    return counts


def test_target_has_no_score_and_says_why():
    be = oq.OpenQuantumBackend(service=FakeService())
    t = be.target()
    assert t.pairs is None and t.x_of(PAIRS) is None and t.two_qubit_gate == "cz"
    assert any("recompilation" in n for n in t.notes)


def test_programs_hold_three_cz_per_pair_and_one_sequence():
    be = oq.OpenQuantumBackend(service=FakeService())
    progs = be.programs(MapJob(PAIRS, list(ORDER_16)))
    assert len(progs) == 16
    gates, meas = oq.parse(progs[0][2])
    assert sum(g == "cz" for g, _, _ in gates) == 9 and meas == {0: 0, 1: 5, 2: 1, 3: 4, 5: 2, 6: 3}


def test_too_many_qubits_is_refused():
    be = oq.OpenQuantumBackend(service=FakeService())
    with pytest.raises(ValueError, match="refused"):
        be.programs(MapJob([(0, 1), (2, 3), (4, 5), (6, 7)]))  # 8 qubits > the fixture's limit of 7


def test_quote_then_waves():
    svc = FakeService()
    be = oq.OpenQuantumBackend(service=svc, budget_credits=51)
    w1 = MapJob(PAIRS, list(ORDER_16), positions=list(range(1, 9)))
    w2 = MapJob(PAIRS, list(ORDER_16), positions=list(range(9, 17)))
    with pytest.raises(oq.QuoteRefused):
        be.submit(w1)
    est = be.estimate(w1)
    assert est.amount == 24 and est.unit == "credits"
    h1 = be.submit(w1)
    assert h1.job_ids == [f"task-{i}" for i in range(1, 9)] and h1.order == ORDER_16[:8]
    be.estimate(w2)
    svc.scheduler.status = "Running"
    with pytest.raises(RuntimeError, match="not completed"):
        be.submit(w2, after=h1)
    svc.scheduler.status = "Completed"
    h2 = be.submit(w2, after=h1)
    assert len(h2.job_ids) == 8
    assert ORG not in json.dumps(be._quotes) and ORG not in json.dumps(h1.__dict__)


def test_a_price_change_is_refused():
    be = oq.OpenQuantumBackend(service=FakeService(price=4))
    job = MapJob(PAIRS, list(ORDER_16), positions=[1, 2])
    rec = be.quote(job)
    assert not rec["all_pass"] and not rec["tests"]["exact_credits_every_task"]
    with pytest.raises(oq.QuoteRefused):
        be.submit(job)


def test_counts_parsing_round_trip():
    svc = FakeService()
    be = oq.OpenQuantumBackend(service=svc)
    job = MapJob(PAIRS, list(ORDER_16), positions=[1, 2])
    be.estimate(job)
    h = be.submit(job)
    want = [[50, 10, 15, 925], [100, 30, 20, 850], [400, 100, 100, 400]]
    for jid in h.job_ids:
        svc.scheduler.outputs[jid] = output_for(PAIRS, want)
    mc = be.fetch(h)
    got = mc.outcomes[0] / mc.outcomes[0].sum(axis=1, keepdims=True)
    assert np.allclose(got, np.array(want) / 1000)
    assert (oq.pair_covariance(mc.outcomes[0])[:2] > 0).all()


# --------------------------------------------------------------------------- Amendment A3: the guard and the budget
W1 = list(range(1, 9))
W2 = list(range(9, 17))


def wave(positions):
    return MapJob(PAIRS, list(ORDER_16), positions=positions)


def events(be):
    return [e["event"] for e in be.ledger.entries()]


@pytest.fixture
def ledger(tmp_path):
    from manacitra.backends.base import Ledger

    return Ledger(tmp_path / "oq-ledger.jsonl")


def test_the_public_submit_is_the_guard(ledger):
    from manacitra.backends.base import ResubmitRefused

    svc = FakeService()
    be = oq.OpenQuantumBackend(service=svc, ledger=ledger)
    be.estimate(wave(W1))
    be.submit(wave(W1))
    with pytest.raises(ResubmitRefused):
        be.submit(wave(W1))
    assert len(svc.scheduler.created) == 8
    assert events(be) == ["reserved", "sending", "sent"]


def test_two_waves_against_a_budget_that_fits_one(ledger):
    svc = FakeService()
    be = oq.OpenQuantumBackend(service=svc, budget_credits=30, ledger=ledger)
    be.estimate(wave(W1))
    h1 = be.submit(wave(W1))
    rec = be.quote(wave(W2))
    assert rec["committed_credits"] == 24 and not rec["tests"]["within_budget"]
    with pytest.raises(oq.SpendRefused, match=r"budget: 24 reserved \+ 24 for this job > 30"):
        be.submit(wave(W2), after=h1)
    assert len(svc.scheduler.created) == 8
    assert events(be)[-1] == "refused"
    assert ledger.reserved_credits(be.budget_scope) == 24


def test_the_balance_is_read_again_at_send_time(ledger):
    svc = FakeService()
    be = oq.OpenQuantumBackend(service=svc, ledger=ledger)
    assert be.estimate(wave(W1)).amount == 24
    svc.management.get_credit_balance = lambda org: SimpleNamespace(spark_credits=0, full_credits=0)
    with pytest.raises(
        oq.SpendRefused, match=r"balance floor: balance 0 - open reservations 0 - 24 for this job = -24 < floor 10"
    ):
        be.submit(wave(W1))
    assert svc.scheduler.created == [] and "sending" not in events(be) and "reserved" not in events(be)


def test_an_expired_quote_is_refused(ledger):
    svc = FakeService()
    be = oq.OpenQuantumBackend(service=svc, ledger=ledger, quote_valid_s=600)
    be.estimate(wave(W1))
    be._quotes[wave(W1).job_hash(be.name, be.processor)]["quoted_at"] -= 601
    with pytest.raises(oq.QuoteRefused, match="quote expired"):
        be.submit(wave(W1))
    assert svc.scheduler.created == []
    be.estimate(wave(W1))  # quoted again, it goes
    assert len(be.submit(wave(W1)).job_ids) == 8


def test_a_price_change_after_the_quote_is_refused(ledger):
    svc = FakeService()
    be = oq.OpenQuantumBackend(service=svc, ledger=ledger)
    be.estimate(wave(W1))
    svc.scheduler.price = 4
    with pytest.raises(oq.QuoteRefused, match="at 4 credits, expected 3"):
        be.submit(wave(W1))
    assert svc.scheduler.created == []


def test_a_failed_send_keeps_its_reservation_until_a_fetch_settles_it(ledger):
    svc = FakeService()
    be = oq.OpenQuantumBackend(service=svc, budget_credits=30, ledger=ledger)
    create = svc.scheduler.create_job

    def flaky(req):
        if len(svc.scheduler.created) == 2:
            raise ConnectionError("the platform did not answer")
        return create(req)

    svc.scheduler.create_job = flaky
    be.estimate(wave(W1))
    with pytest.raises(ConnectionError):
        be.submit(wave(W1))
    failed = ledger.entries()[-1]
    assert failed["event"] == "failed" and failed["job_ids_created"] == ["task-1", "task-2"]
    (res,) = ledger.reservations(be.budget_scope)
    assert res["credits"] == 24 and not res["settled"]
    # the open reservation still counts: a second wave of 24 would pass 30
    be.estimate(wave(W2))
    with pytest.raises(oq.SpendRefused, match="budget"):
        be.submit(wave(W2))


def test_a_fetch_settles_the_reservation(ledger):
    svc = FakeService()
    be = oq.OpenQuantumBackend(service=svc, ledger=ledger)
    job = wave([1, 2])
    be.estimate(job)
    h = be.submit(job)
    assert not ledger.reservations(be.budget_scope)[0]["settled"]
    for jid in h.job_ids:
        svc.scheduler.outputs[jid] = output_for(PAIRS, [[0, 0, 0, 1000]] * 3)
    be.fetch(h)
    assert ledger.reservations(be.budget_scope)[0]["settled"]


# --------------------------------------------------------------------------- Amendment A6: the floor, under the lock
def test_open_reservations_on_the_account_count_against_the_floor(ledger):
    """Balance 122, floor 90: one wave of 24 leaves 98; a second, with the first still open, would leave 74."""
    svc = FakeService()
    be = oq.OpenQuantumBackend(service=svc, balance_floor=90, ledger=ledger)
    be.estimate(wave(W1))
    h1 = be.submit(wave(W1))
    rec = be.quote(wave(W2))
    assert rec["open_on_account_credits"] == 24 and not rec["tests"]["balance_after_at_least_floor"]
    with pytest.raises(oq.SpendRefused) as e:
        be.submit(wave(W2), after=h1)
    msg = str(e.value)
    assert "balance floor: balance 122 - open reservations 24 - 24 for this job = 74 < floor 90" in msg
    assert f"{h1.job_hash[:12]} (24 credits, reserved " in msg and "on the saved account 'default'" in msg
    assert "quote test failed: balance_after_at_least_floor" in msg  # the early refusal, from the quote, too
    assert len(svc.scheduler.created) == 8 and events(be)[-1] == "refused"


def test_a_settled_reservation_no_longer_counts_against_the_floor(ledger):
    svc = FakeService()
    be = oq.OpenQuantumBackend(service=svc, balance_floor=90, ledger=ledger)
    be.estimate(wave(W1))
    h1 = be.submit(wave(W1))
    assert [r["credits"] for r in be.open_on_account()] == [24]
    for jid in h1.job_ids:
        svc.scheduler.outputs[jid] = output_for(PAIRS, [[0, 0, 0, 1000]] * 3)
    be.fetch(h1)
    assert be.open_on_account() == []
    be.estimate(wave(W2))
    h2 = be.submit(wave(W2), after=h1)  # 122 - 0 open - 24 = 98 >= 90
    reserved = [e for e in ledger.entries() if e["event"] == "reserved"]
    assert len(h2.job_ids) == 8 and reserved[-1]["open_on_account_credits"] == 0
    assert reserved[-1]["account"] == be.account_scope and "default" not in be.account_scope


def test_the_floor_counts_every_job_name_on_the_account_and_no_other_account(ledger):
    svc = FakeService()
    run1 = oq.OpenQuantumBackend(service=svc, balance_floor=90, ledger=ledger, job_name="run-1")
    run1.estimate(wave(W1))
    run1.submit(wave(W1))
    # another run on the same account: its own budget scope, the same balance
    run2 = oq.OpenQuantumBackend(service=svc, balance_floor=90, ledger=ledger, job_name="run-2")
    run2.estimate(wave(W2))
    with pytest.raises(oq.SpendRefused, match="balance floor"):
        run2.submit(wave(W2))
    # another saved account: another balance
    other = oq.OpenQuantumBackend(service=svc, balance_floor=90, ledger=ledger, job_name="run-2", account="second")
    other.estimate(wave(W2))
    other.submit(wave(W2))
    assert len(svc.scheduler.created) == 16


def test_a_reservation_from_before_a6_counts_against_every_account(ledger):
    """A reservation with no account field (written before A6) cannot be placed, so it counts against any account."""
    be = oq.OpenQuantumBackend(service=FakeService(), balance_floor=90, ledger=ledger, account="second")
    ledger.append(
        {"event": "reserved", "job_hash": "a" * 64, "utc": "t", "scope": "openquantum:x:kept-share", "credits": 24}
    )
    ledger.append({"event": "reserved", "job_hash": "b" * 64, "utc": "t", "scope": "ibm", "seconds": 9.8})
    assert [r["job_hash"] for r in be.open_on_account()] == ["a" * 64]
    be.estimate(wave(W1))
    with pytest.raises(
        oq.SpendRefused, match=r"open reservations 24 - 24 for this job = 74 < floor 90; .*aaaaaaaaaaaa"
    ):
        be.submit(wave(W1))


def test_a_resubmitted_job_is_not_settled_by_the_earlier_fetch(ledger):
    """Before A6, any settled record of a job hash settled every reservation of it, including a later re-send's."""
    svc = FakeService()
    be = oq.OpenQuantumBackend(service=svc, ledger=ledger)
    be.estimate(wave(W1))
    h1 = be.submit(wave(W1))
    for jid in h1.job_ids:
        svc.scheduler.outputs[jid] = output_for(PAIRS, [[0, 0, 0, 1000]] * 3)
    be.fetch(h1)
    be.estimate(wave(W1))
    h2 = be.submit(wave(W1), allow_resubmit=True, reason="test", log=lambda m: None)
    assert [r["settled"] for r in ledger.reservations(be.budget_scope)] == [True, False]
    be.fetch(h1)  # fetching the first send again settles nothing new
    assert [r["settled"] for r in ledger.reservations(be.budget_scope)] == [True, False]
    assert [r["credits"] for r in be.open_on_account()] == [24]
    for jid in h2.job_ids:
        svc.scheduler.outputs[jid] = output_for(PAIRS, [[0, 0, 0, 1000]] * 3)
    be.fetch(h2)
    assert [r["settled"] for r in ledger.reservations(be.budget_scope)] == [True, True]


def test_a_reservation_settled_after_the_balance_read_still_counts(ledger):
    """Another process reserves, sends, is charged and is fetched between this send's balance read and its lock. The
    balance read does not show that charge, so the settled reservation must still count against the floor."""
    svc = FakeService()

    class Late(oq.OpenQuantumBackend):
        def _preflight(self, job, led, **kw):
            pre = super()._preflight(job, led, **kw)
            for e in (
                {"event": "reserved", "scope": "openquantum:x:other", "account": self.account_scope, "credits": 24},
                {"event": "sent", "handle": {"job_ids": ["t-other"]}},
                {"event": "settled", "job_ids": ["t-other"]},
            ):
                led.append({"job_hash": "c" * 64, "utc": "t", **e})
            return pre

    be = Late(service=svc, balance_floor=90, ledger=ledger)
    be.estimate(wave(W1))
    with pytest.raises(
        oq.SpendRefused, match=r"open reservations 24 - 24 for this job = 74 < floor 90; .*cccccccccccc"
    ):
        be.submit(wave(W1))
    assert svc.scheduler.created == [] and be.open_on_account() == []  # settled, for any later balance read
    # read again now, the balance is taken to show that charge: the job goes
    be2 = oq.OpenQuantumBackend(service=svc, balance_floor=90, ledger=ledger)
    be2.estimate(wave(W1))
    be2.submit(wave(W1))
    assert len(svc.scheduler.created) == 8


# --------------------------------------------------------------------------- Amendment A3: the SDK's private methods
IMPORT_WITH_FAKE_SDK = """
import sys, types
pkg, clients = types.ModuleType("openquantum_sdk"), types.ModuleType("openquantum_sdk.clients")
class SchedulerClient:
{body}
clients.SchedulerClient = SchedulerClient
pkg.clients = clients
sys.modules["openquantum_sdk"], sys.modules["openquantum_sdk.clients"] = pkg, clients
import manacitra.backends.openquantum
print("imported")
"""


def import_with(body):
    import subprocess

    code = IMPORT_WITH_FAKE_SDK.format(body=body)
    return subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)


def test_an_sdk_without_the_private_methods_stops_the_import():
    p = import_with("    def _wait_for_preparation(self): pass")
    assert p.returncode != 0 and "SDKIncompatible" in p.stderr
    assert "lacks _resolve_organization_id" in p.stderr
    assert "_wait_for_preparation and _resolve_organization_id" in p.stderr and "openquantum-sdk 0.4.3" in p.stderr


def test_an_sdk_with_them_imports():
    p = import_with("    def _wait_for_preparation(self): pass\n    def _resolve_organization_id(self): pass")
    assert p.returncode == 0 and p.stdout.strip() == "imported", p.stderr


def test_the_check_names_both_when_both_are_missing():
    with pytest.raises(oq.SDKIncompatible, match="lacks _wait_for_preparation and _resolve_organization_id"):
        oq.check_sdk(SimpleNamespace(SchedulerClient=object))
    assert oq.check_sdk(SimpleNamespace(SchedulerClient=type("S", (), dict.fromkeys(oq.PRIVATE_SDK_METHODS, len))))


def test_the_extra_is_limited_to_the_checked_versions():
    import tomllib

    py = tomllib.loads((Path(__file__).resolve().parent.parent / "pyproject.toml").read_text())
    extra = py["project"]["optional-dependencies"]["openquantum"]
    assert "openquantum-sdk>=0.4.3,<0.5" in extra and "openquantum-sdk-qiskit>=0.3.3,<0.4" in extra
