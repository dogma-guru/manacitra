# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""The experimental Open Quantum adapter against recorded-shape responses. Never the network."""

import json
import sys
import types
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from manacitra.backends import openquantum as oq
from manacitra.backends.base import MapJob
from manacitra.circuits import ORDER_16

FIX = Path(__file__).parent / "fixtures" / "openquantum"
PUB, STD = "00000000-0000-0000-0000-000000000001", "00000000-0000-0000-0000-000000000003"
ORG = "00000000-0000-0000-0000-000000000099"
PAIRS = [(0, 1), (2, 3), (5, 6)]


def ns(d):
    return json.loads(json.dumps(d), object_hook=lambda x: SimpleNamespace(**x))


@pytest.fixture(autouse=True)
def sdk_stub(monkeypatch):
    """The SDK's enums and request models, stubbed with placeholder identifiers."""
    enums = types.ModuleType("openquantum_sdk.enums")
    enums.ExecutionPlanType = SimpleNamespace(PUBLIC=SimpleNamespace(value=PUB))
    enums.QueuePriorityType = SimpleNamespace(STANDARD=SimpleNamespace(value=STD))
    models = types.ModuleType("openquantum_sdk.models")
    models.JobPreparationCreate = lambda **kw: kw
    models.JobCreate = lambda **kw: kw
    pkg = types.ModuleType("openquantum_sdk")
    for name, mod in (("openquantum_sdk", pkg), ("openquantum_sdk.enums", enums), ("openquantum_sdk.models", models)):
        monkeypatch.setitem(sys.modules, name, mod)


class FakeScheduler:
    def __init__(self, price=3, status="Completed"):
        self.price, self.status = price, status
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
        return SimpleNamespace(id=jid, status="Pending")

    def get_job(self, jid):
        rec = json.loads((FIX / "job_record.json").read_text())
        return SimpleNamespace(
            id=jid, status=self.status, message=None, calibration_data_url=rec["calibration_data_url"]
        )

    def download_job_output(self, r):
        return self.outputs[r.id]


class FakeService:
    def __init__(self, **kw):
        self.scheduler = FakeScheduler(**kw)
        bal = json.loads((FIX / "balance.json").read_text())
        self.management = SimpleNamespace(get_credit_balance=lambda org: SimpleNamespace(**bal))


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
