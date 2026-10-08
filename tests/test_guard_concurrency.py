# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""Amendment A4, R1: submit-once holds across processes. Every caller here is its own process (multiprocessing,
spawn), except the reviewer's thread race, kept as written against the fake backend. Each pair of callers meets at a
barrier inside the backend's preflight, after the quick repeat check, so both reach the guard's lock together."""

import multiprocessing as mp
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import pytest
from _fakes import FakeSpender, balance_race_worker, child_fake, child_ibm, child_openquantum, hold_lock, sends

from manacitra.backends.base import Ledger, LockTimeout, MapJob, ResubmitRefused

CTX = mp.get_context("spawn")


def run_pair(target, args_a, args_b, timeout=120):
    """Start two processes that meet at a barrier; return their outcomes, keyed by who."""
    barrier, queue = CTX.Barrier(2), CTX.Queue()
    procs = [
        CTX.Process(target=target, args=(who, *a[:2], barrier, queue, *a[2:]))
        for who, a in (("a", args_a), ("b", args_b))
    ]
    for p in procs:
        p.start()
    out = dict((w, (kind, msg)) for w, kind, msg in (queue.get(timeout=timeout) for _ in procs))
    for p in procs:
        p.join(timeout=timeout)
    return out


def test_two_processes_one_job_exactly_one_send(tmp_path):
    ledger, sent = tmp_path / "ledger.jsonl", tmp_path / "sends"
    out = run_pair(child_fake, (ledger, sent), (ledger, sent))
    kinds = sorted(k for k, _ in out.values())
    assert kinds == ["ResubmitRefused", "sent"], out
    assert len(sends(sent)) == 1
    (msg,) = [m for k, m in out.values() if k == "ResubmitRefused"]
    assert "was already sent at" in msg and "its reservation from" in msg and "is open" in msg
    events = [e["event"] for e in Ledger(ledger).entries()]
    assert events.count("reserved") == 1 and events.count("sending") == 1 and events.count("sent") == 1


def test_two_processes_two_jobs_one_open_quantum_budget(tmp_path):
    """Two waves of 24 credits against a budget of 30, from two processes at once: exactly one sends."""
    pytest.importorskip("qiskit")
    ledger, sent = tmp_path / "ledger.jsonl", tmp_path / "sends"
    out = run_pair(child_openquantum, (ledger, sent, list(range(1, 9)), 30), (ledger, sent, list(range(9, 17)), 30))
    kinds = sorted(k for k, _ in out.values())
    assert kinds == ["SpendRefused", "sent"], out
    (msg,) = [m for k, m in out.values() if k == "SpendRefused"]
    assert "budget: 24 reserved + 24 for this job > 30" in msg
    assert len(sends(sent)) == 8  # one wave's eight tasks
    led = Ledger(ledger)
    assert [e["credits"] for e in led.entries() if e["event"] == "reserved"] == [24]


def test_two_processes_one_open_quantum_balance_floor(tmp_path):
    """Amendment A6, the reviewer's race: balance 122, floor 90, budget 100. Two waves of 24 credits from two
    processes, meeting after preflight. Each fits the budget (48 <= 100) and each alone keeps the floor (122 - 24 =
    98), but together they would leave 74. Exactly one sends; the other is refused, naming the floor and the open
    reservation it counted."""
    pytest.importorskip("qiskit")
    ledger, sent = tmp_path / "ledger.jsonl", tmp_path / "sends"
    out = run_pair(
        child_openquantum, (ledger, sent, list(range(1, 9)), 100, 90), (ledger, sent, list(range(9, 17)), 100, 90)
    )
    kinds = sorted(k for k, _ in out.values())
    assert kinds == ["SpendRefused", "sent"], out
    (msg,) = [m for k, m in out.values() if k == "SpendRefused"]
    assert "balance floor: balance 122 - open reservations 24 - 24 for this job = 74 < floor 90" in msg
    assert "budget" not in msg
    (res,) = [e for e in Ledger(ledger).entries() if e["event"] == "reserved"]
    assert res["credits"] == 24 and res["job_hash"][:12] in msg
    assert len(sends(sent)) == 8


def test_two_processes_two_jobs_one_ibm_cap(tmp_path):
    """Two jobs of 5.6 s each (2 circuits x 1000 shots) with 310 s used and a cap of 320 s: exactly one sends."""
    pytest.importorskip("qiskit_ibm_runtime")
    ledger, sent = tmp_path / "ledger.jsonl", tmp_path / "sends"
    out = run_pair(child_ibm, (ledger, sent, [1, 2], 320.0), (ledger, sent, [3, 4], 320.0), timeout=300)
    kinds = sorted(k for k, _ in out.values())
    assert kinds == ["CapExceeded", "sent"], out
    (msg,) = [m for k, m in out.values() if k == "CapExceeded"]
    assert "used 310 s + open reservations 5.6 s + estimate 5.6 s > cap 320 s" in msg
    assert sends(sent) == ["ibm"]


def test_a_held_lock_refuses_after_the_timeout(tmp_path):
    """Another process holds the ledger's lock: a third caller waits the timeout, then refuses, and sends nothing."""
    ledger, sent = tmp_path / "ledger.jsonl", tmp_path / "sends"
    held, release = CTX.Event(), CTX.Event()
    holder = CTX.Process(target=hold_lock, args=(ledger, held, release))
    holder.start()
    try:
        assert held.wait(timeout=60)
        be = FakeSpender(Ledger(ledger, lock_timeout=1.0), sent)
        t0 = time.monotonic()
        with pytest.raises(LockTimeout, match=r"could not be taken within 1 s"):
            be.submit(MapJob([(0, 1)]), log=lambda m: None)
        assert time.monotonic() - t0 >= 1.0
        assert sends(sent) == [] and Ledger(ledger).entries() == []
    finally:
        release.set()
        holder.join(timeout=60)
    # with the lock free again, the job goes
    FakeSpender(Ledger(ledger, lock_timeout=1.0), sent).submit(MapJob([(0, 1)]), log=lambda m: None)
    assert sends(sent) == ["kept-share"]


def test_a_crash_after_the_reservation_still_refuses_a_repeat(tmp_path):
    """A process dies between the reservation write and the send. A new process finds the reservation on disk and
    refuses the repeat; the override sends it, and is logged."""
    ledger, sent = tmp_path / "ledger.jsonl", tmp_path / "sends"
    queue = CTX.Queue()
    p = CTX.Process(target=child_fake, args=("crash", ledger, sent, None, queue), kwargs={"crash": True})
    p.start()
    p.join(timeout=60)
    assert p.exitcode == 17 and sends(sent) == []
    assert [e["event"] for e in Ledger(ledger).entries()] == ["reserved", "sending"]
    p = CTX.Process(target=child_fake, args=("again", ledger, sent, None, queue))
    p.start()
    who, kind, msg = queue.get(timeout=60)
    p.join(timeout=60)
    assert (who, kind) == ("again", "ResubmitRefused") and "is open" in msg
    assert sends(sent) == []
    be = FakeSpender(Ledger(ledger), sent)
    be.submit(
        MapJob([(0, 1)], name="same"), allow_resubmit=True, reason="the first process crashed", log=lambda m: None
    )
    assert sends(sent) == ["same"]
    assert [e for e in Ledger(ledger).entries() if e["event"] == "sending"][-1]["resubmit_reason"] == (
        "the first process crashed"
    )


def test_an_unfinished_write_is_ignored_and_cut_off(tmp_path):
    """A crash in the middle of a write leaves a last line with no newline: nothing that depended on it happened."""
    path = tmp_path / "ledger.jsonl"
    led = Ledger(path)
    led.append({"event": "refused", "job_hash": "x", "utc": "t"})
    with path.open("a") as f:
        f.write('{"event": "reserved", "job_ha')
    assert [e["event"] for e in led.entries()] == ["refused"]
    led.append({"event": "settled", "job_hash": "x", "utc": "t"})
    assert [e["event"] for e in led.entries()] == ["refused", "settled"]
    assert path.read_text().count("\n") == 2


def test_a_corrupt_line_in_the_middle_stops_the_read(tmp_path):
    path = tmp_path / "ledger.jsonl"
    path.write_text('{"event": "sending"}\nnot json\n{"event": "sent"}\n')
    with pytest.raises(ValueError, match="line 2 is not a ledger record"):
        Ledger(path).entries()


def test_the_reviewers_thread_race(tmp_path):
    """The reviewer's adversarial.py, adapted to the fake backend: two threads of one process meet at a barrier in
    _preflight, after the quick repeat check. Before A4 both sent. Now exactly one does."""
    sent = tmp_path / "sends"
    be = FakeSpender(Ledger(tmp_path / "ledger.jsonl"), sent, threading.Barrier(2))
    job = MapJob([(0, 1)])
    with ThreadPoolExecutor(2) as pool:
        futures = [pool.submit(be.submit, job, log=lambda m: None) for _ in range(2)]
    outcomes = sorted(type(f.exception()).__name__ if f.exception() else "sent" for f in futures)
    assert outcomes == ["ResubmitRefused", "sent"]
    assert len(sends(sent)) == 1
    assert [e["allow_resubmit"] for e in be.ledger.entries() if e["event"] == "sending"] == [False]
    with pytest.raises(ResubmitRefused):
        be.barrier = None
        be.submit(job)


def test_the_reviewers_balance_race(tmp_path):
    """The reviewer's balance_race.py (third review), adapted: two processes, a barrier after preflight, a budget of
    100 credits and a floor of 90 against a balance of 122, waves of 24. Before A6 both sent and the balance would have
    fallen to 74. Now the floor holds."""
    pytest.importorskip("qiskit")
    ledger, sent = tmp_path / "ledger.jsonl", tmp_path / "sends"
    barrier, q = CTX.Barrier(2), CTX.Queue()
    ps = [CTX.Process(target=balance_race_worker, args=(w, str(ledger), str(sent), barrier, q)) for w in ("a", "b")]
    for p in ps:
        p.start()
    outputs = [q.get(timeout=90) for _ in ps]
    for p in ps:
        p.join(timeout=30)
    reservations = [e for e in Ledger(ledger).entries() if e["event"] == "reserved"]
    spent = sum(e["credits"] for e in reservations)
    assert sorted(o["result"] for o in outputs) == ["SpendRefused", "sent"], outputs
    assert len(sends(sent)) == 8 and spent == 24
    assert 122 - spent >= 90  # floor_breached is False


def test_a_settled_record_settles_only_an_earlier_open_reservation(tmp_path):
    """Amendment A6: settlement is read in order. A settled record naming task IDs settles the reservation whose send
    created them; one without IDs (before A6) settles the earliest open reservation of its hash; neither reaches a
    reservation written after it."""
    led = Ledger(tmp_path / "ledger.jsonl")
    for e in (
        {"event": "reserved", "job_hash": "h", "scope": "s", "credits": 3},
        {"event": "sent", "job_hash": "h", "handle": {"job_ids": ["t1"]}},
        {"event": "settled", "job_hash": "h", "job_ids": ["t1"]},
        {"event": "reserved", "job_hash": "h", "scope": "s", "credits": 3},
        {"event": "sent", "job_hash": "h", "handle": {"job_ids": ["t2"]}},
        {"event": "settled", "job_hash": "h", "job_ids": ["t1"]},  # the first send, fetched again
    ):
        led.append({"utc": "t", **e})
    assert [r["settled"] for r in led.reservations("s")] == [True, False]
    led.append({"event": "settled", "job_hash": "h", "utc": "t"})  # no IDs: the earliest open one
    assert [r["settled"] for r in led.reservations("s")] == [True, True]
    led.append({"event": "reserved", "job_hash": "h", "utc": "t", "scope": "s", "credits": 3})
    assert [r["settled"] for r in led.reservations("s")] == [True, True, False]
