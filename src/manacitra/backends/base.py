# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""The backend protocol, the provider-independent job and counts, and the submit-once guard.

A backend does four things:

    target()        the coupling map, the native two-qubit gate, and the per-pair and per-qubit figures with their
                    timestamps, or None where the provider publishes none
    estimate(job)   the expected processor time or credits
    submit(job)     a handle
    fetch(handle)   counts in a provider-independent form: per circuit, per pair, the four outcomes indexed
                    s = a + 2 b (a the bit of the pair's first qubit, b of its second)

The submit-once guard lives here, not in any backend: submit_once() refuses a second submission of the same job hash
unless allow_resubmit is given, which is itself logged with the caller's reason. A backend that spends (IBM, Open
Quantum) inherits GuardedSubmit, so its public submit() is that guard and its raw send is the private _send(); there
is no unguarded public path. Backends that spend nothing (the simulators) keep a direct submit() and skip the ledger.

The check and the reservation are one step (Amendment A4). Under an interprocess lock on a file beside the ledger, the
guard reads the ledger again, refuses a job already sent or reserved, does the budget accounting against every
reservation (_reserve), and writes and fsyncs the reservation and the "sending" record. The lock is then released and
the job sent, so two processes cannot both send one job, or both spend the last of one budget. The provider reads that
need no ledger (_preflight) run before the lock; a refusal there is logged as "refused", which is not a send.

The rule for every spending check (Amendment A6). A check that depends on a shared quantity (an account balance, a run
budget, a usage cap) is evaluated in _reserve, under the ledger's lock, against every open reservation in the ledger
that draws on the same quantity. A check made before the lock (in a quote, or in _preflight) is only an early refusal;
it is never the deciding one, because another process may reserve between it and the send. A reservation counts as open
until a fetch settles it, even when its charge may already show in a figure the provider reports: that can only refuse
too much, never too little. For the same reason, a reservation settled after the provider's figure was read still
counts against that figure (Ledger.unsettled_at). The rule holds only between callers that share one ledger.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from collections.abc import Sequence
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Protocol, runtime_checkable

import numpy as np

from ..circuits import ORDER_16


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


# --------------------------------------------------------------------------- what a provider publishes
@dataclass
class PairFigures:
    pair: tuple[int, int]
    two_qubit_error: float | None
    readout_error: tuple[float | None, float | None]
    x: float | None
    timestamps: dict = field(default_factory=dict)


@dataclass
class Target:
    provider: str
    processor: str
    n_qubits: int
    coupling_map: list[tuple[int, int]]
    two_qubit_gate: str
    pairs: dict[tuple[int, int], PairFigures] | None = None
    qubits: dict[int, dict] | None = None
    read_utc: str = field(default_factory=utc_now)
    notes: list[str] = field(default_factory=list)

    def x_of(self, pairs: Sequence[Sequence[int]]) -> list[float] | None:
        """The published score of each pair, or None if the provider publishes none."""
        if not self.pairs:
            return None
        out = []
        for a, b in pairs:
            f = self.pairs.get((min(a, b), max(a, b)))
            if f is None or f.x is None:
                return None
            out.append(f.x)
        return out


# --------------------------------------------------------------------------- the job
@dataclass
class MapJob:
    """Every circuit of `order` on all of the job's pairs at once, `shots` each; the pairs must not overlap, so a whole
    chip takes several jobs (rounds). `positions` (1-based) restricts a submission
    to part of the order, for providers that take a job in waves."""

    pairs: list[tuple[int, int]]
    order: list[str] = field(default_factory=lambda: list(ORDER_16))
    shots: int = 8000
    name: str = "kept-share"
    positions: list[int] | None = None

    def __post_init__(self):
        self.pairs = [tuple(int(q) for q in p) for p in self.pairs]
        qs = [q for p in self.pairs for q in p]
        if len(qs) != len(set(qs)):
            raise ValueError("pairs must be disjoint")

    @property
    def active_positions(self) -> list[int]:
        return self.positions or list(range(1, len(self.order) + 1))

    @property
    def total_shots(self) -> int:
        return self.shots * len(self.active_positions)

    def job_hash(self, provider: str, processor: str) -> str:
        from .. import __version__

        body = {
            "provider": provider,
            "processor": processor,
            "pairs": self.pairs,
            "order": self.order,
            "positions": self.active_positions,
            "shots": self.shots,
            "name": self.name,
            "manacitra": __version__,
        }
        return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()


@dataclass
class Estimate:
    amount: float
    unit: str  # "s" or "credits"
    detail: str = ""


@dataclass
class JobHandle:
    provider: str
    processor: str
    job_ids: list[str]
    job_hash: str
    submitted_utc: str = field(default_factory=utc_now)
    positions: list[int] | None = None
    pairs: list[tuple[int, int]] | None = None
    order: list[str] | None = None
    shots: int | None = None

    @classmethod
    def for_job(cls, provider: str, processor: str, job_ids: list[str], job: MapJob) -> JobHandle:
        return cls(
            provider,
            processor,
            job_ids,
            job.job_hash(provider, processor),
            positions=job.active_positions,
            pairs=list(job.pairs),
            order=[job.order[p - 1] for p in job.active_positions],
            shots=job.shots,
        )


@dataclass
class MapCounts:
    """Per circuit position, per pair, the counts of the four outcomes s = a + 2 b."""

    pairs: list[tuple[int, int]]
    order: list[str]
    shots: int
    outcomes: list[np.ndarray]
    meta: dict = field(default_factory=dict)

    def p11(self) -> np.ndarray:
        """Per circuit, per pair P(11)."""
        return np.array([o[:, 3] / o.sum(axis=1) for o in self.outcomes], float)

    def to_json(self) -> dict:
        return {
            "meta": self.meta,
            "pairs": [list(p) for p in self.pairs],
            "order": self.order,
            "shots": self.shots,
            "outcomes": [np.asarray(o).astype(int).tolist() for o in self.outcomes],
        }

    @classmethod
    def from_json(cls, d: dict) -> MapCounts:
        return cls(
            [tuple(p) for p in d["pairs"]],
            d["order"],
            d["shots"],
            [np.asarray(o) for o in d["outcomes"]],
            d.get("meta", {}),
        )


@runtime_checkable
class Backend(Protocol):
    name: str
    processor: str
    spends: bool

    def target(self) -> Target: ...

    def estimate(self, job: MapJob) -> Estimate: ...

    def submit(self, job: MapJob) -> JobHandle: ...

    def fetch(self, handle: JobHandle) -> MapCounts: ...


# --------------------------------------------------------------------------- the submit-once guard
class ResubmitRefused(RuntimeError):
    pass


class SpendRefused(RuntimeError):
    """A spending check failed immediately before sending; the message names every check that failed."""


class LockTimeout(RuntimeError):
    """The ledger's lock could not be taken in time; nothing was checked, reserved or sent."""


#: How long a caller waits for the ledger's lock before refusing (Amendment A4)
LOCK_TIMEOUT_S = 30.0

if os.name == "nt":  # pragma: no cover - Windows is not run on this project's CI
    import msvcrt

    def _try_lock(fd: int) -> bool:
        os.lseek(fd, 0, os.SEEK_SET)
        try:
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        except OSError:
            return False
        return True

    def _unlock(fd: int) -> None:
        os.lseek(fd, 0, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)

else:
    import fcntl

    def _try_lock(fd: int) -> bool:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return False
        return True

    def _unlock(fd: int) -> None:
        fcntl.flock(fd, fcntl.LOCK_UN)


class Ledger:
    """An append-only JSON-lines file of submissions. Default: ./.manacitra/ledger.jsonl, or $MANACITRA_LEDGER.

    Every write takes an exclusive lock on a lock file beside the ledger (ledger.jsonl.lock): fcntl.flock on POSIX,
    msvcrt.locking on Windows, so it holds between processes as well as threads. Each acquisition opens its own file
    descriptor, so two threads of one process exclude each other too. A caller that cannot take the lock within
    lock_timeout seconds (30 by default) is refused with LockTimeout. Every write is flushed and fsynced before the
    lock is released.

    A last line without its newline is a write that never completed (a crash mid-write). Nothing that depended on it
    happened, because every send waits for its records to be fsynced; it is ignored when read and cut off before the
    next write. Any other line that is not JSON stops the read with ValueError.
    """

    def __init__(self, path: str | os.PathLike | None = None, lock_timeout: float = LOCK_TIMEOUT_S):
        self.path = Path(path or os.environ.get("MANACITRA_LEDGER", Path.cwd() / ".manacitra" / "ledger.jsonl"))
        self.lock_timeout = lock_timeout

    @property
    def lock_path(self) -> Path:
        return self.path.with_name(self.path.name + ".lock")

    @contextmanager
    def lock(self):
        """Hold the ledger's interprocess lock, or raise LockTimeout after lock_timeout seconds."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(self.lock_path, os.O_RDWR | os.O_CREAT, 0o644)
        try:
            deadline = time.monotonic() + self.lock_timeout
            while not _try_lock(fd):
                if time.monotonic() >= deadline:
                    raise LockTimeout(
                        f"refused: the ledger's lock ({self.lock_path}) could not be taken within "
                        f"{self.lock_timeout:g} s; another submission may be in progress. Nothing was checked, "
                        "reserved or sent."
                    )
                time.sleep(0.02)
            try:
                yield self
            finally:
                _unlock(fd)
        finally:
            os.close(fd)

    def entries(self) -> list[dict]:
        if not self.path.exists():
            return []
        lines = self.path.read_text().split("\n")
        lines.pop()  # "" after the last newline, or a write that never completed (see the class docstring)
        out = []
        for n, line in enumerate(lines, 1):
            if not line.strip():
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                raise ValueError(f"{self.path}: line {n} is not a ledger record") from None
        return out

    def _write(self, entries: list[dict]) -> None:
        """Append records in one write, then flush and fsync. Called only with the lock held."""
        new = not self.path.exists()
        data = "".join(json.dumps(e, sort_keys=True) + "\n" for e in entries).encode()
        with self.path.open("ab") as f:
            if f.seek(0, os.SEEK_END):
                text = self.path.read_bytes()
                if not text.endswith(b"\n"):  # a write that never completed: cut it off
                    f.truncate(text.rfind(b"\n") + 1)
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        if new and os.name != "nt":  # the new file's directory entry, too
            dfd = os.open(self.path.parent, os.O_RDONLY)
            try:
                os.fsync(dfd)
            finally:
                os.close(dfd)

    def append(self, entry: dict) -> None:
        with self.lock():
            self._write([entry])

    def find(self, job_hash: str) -> list[dict]:
        return [e for e in self.entries() if e.get("job_hash") == job_hash]

    def all_reservations(self, entries: list[dict] | None = None) -> list[dict]:
        """Every reservation in the ledger, in order, each marked settled once a fetch has settled it.

        A "settled" record settles only an open reservation of the same job hash written before it (Amendment A6), so
        a job sent again with allow_resubmit is not taken as settled by the fetch of its earlier send. A settled record
        that names the task IDs it fetched settles the reservation whose send created them, and nothing if none did;
        one without them (written before A6) settles the earliest open reservation of its job hash.
        """
        es = self.entries() if entries is None else entries
        out: list[dict] = []
        open_: dict[str, list[dict]] = {}
        ids: dict[int, list] = {}  # reservation -> the task IDs its send created, keyed by id() of the record
        for e in es:
            event, h = e.get("event"), e.get("job_hash")
            if event == "reserved":
                r = {**e, "settled": False}
                out.append(r)
                open_.setdefault(h, []).append(r)
            elif event in ("sent", "failed"):  # the outcome of the earliest reservation of this hash without one
                created = (e.get("handle") or {}).get("job_ids") if event == "sent" else e.get("job_ids_created")
                r = next((r for r in open_.get(h, []) if id(r) not in ids), None)
                if r is not None:
                    ids[id(r)] = list(created or [])
            elif event == "settled":
                fetched = e.get("job_ids")
                waiting = open_.get(h, [])
                r = next((r for r in waiting if fetched is None or ids.get(id(r)) == list(fetched)), None)
                if r is not None:
                    r["settled"] = True
                    waiting.remove(r)
        return out

    def unsettled_at(self, mark: int, entries: list[dict] | None = None) -> list[dict]:
        """Every reservation in entries that was not settled within the ledger's first `mark` entries.

        For a figure the provider reported (a balance, a usage) when the ledger held `mark` entries: a reservation
        settled after that read may be missing from the figure, so it still counts (Amendment A6). Reading `mark`
        before the provider's figure can only count a reservation too often, never too rarely.
        """
        es = self.entries() if entries is None else entries
        then = self.all_reservations(es[:mark])  # the same reservations, in the same order, as far as they go
        return [r for i, r in enumerate(self.all_reservations(es)) if not (i < len(then) and then[i]["settled"])]

    def reservations(self, scope: str, entries: list[dict] | None = None) -> list[dict]:
        """Every reservation in a budget scope, each marked settled once a fetch has settled it."""
        return [r for r in self.all_reservations(entries) if r.get("scope") == scope]

    def reserved_credits(self, scope: str, entries: list[dict] | None = None) -> float:
        """Credits reserved in a scope, settled or not: a settled reservation was spent, an open one may have been."""
        return float(sum(e["credits"] for e in self.reservations(scope, entries)))

    def open_seconds(self, scope: str, entries: list[dict] | None = None) -> float:
        """Processor seconds reserved in a scope and not yet settled by a fetch."""
        return float(sum(e["seconds"] for e in self.reservations(scope, entries) if not e["settled"]))


def _amount(r: dict) -> str:
    if "credits" in r:
        return f"{r['credits']:g} credits"
    if "seconds" in r:
        return f"{r['seconds']:.1f} s"
    return "no amount"


def _repeat_check(h: str, entries: list[dict], allow_resubmit: bool) -> list[dict]:
    """This job's earlier sends. Refuses (ResubmitRefused) if there is one, or an open reservation, unless
    allow_resubmit; the message names the existing reservation."""
    mine = [e for e in entries if e.get("job_hash") == h]
    earlier = [e for e in mine if e.get("event") == "sending"]
    reserved = [e for e in mine if e.get("event") == "reserved"]
    settled = any(e.get("event") == "settled" for e in mine)
    if (earlier or (reserved and not settled)) and not allow_resubmit:
        held = ""
        if reserved:
            r = reserved[-1]
            scope = f" in scope {r['scope']}" if r.get("scope") else ""
            state = "settled" if settled else "open"
            held = f"; its reservation from {r['utc']} ({_amount(r)}{scope}) is {state}"
        when = f"was already sent at {earlier[0]['utc']}" if earlier else "is already reserved"
        raise ResubmitRefused(
            f"refused: this job (hash {h[:12]}) {when}{held}; "
            "pass allow_resubmit (CLI: --allow-resubmit) to send it again"
        )
    return earlier


def _default_refusal(failed: list[str]) -> SpendRefused:
    return SpendRefused("refused before sending: " + "; ".join(failed))


def submit_once(
    backend: Backend,
    job: MapJob,
    ledger: Ledger | None = None,
    allow_resubmit: bool = False,
    log=print,
    reason: str | None = None,
    **send_kw,
) -> JobHandle:
    """Submit a job once. A second submission of the same job hash is refused unless allow_resubmit is True, and that
    permission is logged with the caller's reason. send_kw go to the backend's _preflight and _send (Open Quantum:
    after, the earlier wave).

    In order:

    1. a quick repeat check against the ledger, so that a repeat is refused before any provider is asked anything;
    2. the backend's _preflight(job, ledger, **send_kw): the provider reads and the checks that need no ledger (the
       usage, the balance, the quote, the transpiled circuits). A refusal here is logged as "refused", not as a send;
    3. under the ledger's interprocess lock: the ledger is read again from disk; the repeat check runs again, against
       earlier sends and open reservations; the backend's _reserve(job, pre, entries) does the budget accounting
       against every reservation in the ledger; and the "reserved" and "sending" records are written and fsynced;
    4. the lock is released, and only then is the job sent. A second caller now finds the reservation and is refused,
       so the lock never spans the send.

    A reservation stays after a failed or ambiguous send, until a fetch settles it.
    """
    if not getattr(backend, "spends", True):
        return backend.submit(job)
    ledger = ledger or getattr(backend, "ledger", None) or Ledger()
    h = job.job_hash(backend.name, backend.processor)
    _repeat_check(h, ledger.entries(), allow_resubmit)
    pre: dict = {}
    preflight = getattr(backend, "_preflight", None)
    if preflight is not None:
        try:
            pre = preflight(job, ledger, **send_kw) or {}
        except Exception as e:
            ledger.append({"event": "refused", "job_hash": h, "utc": utc_now(), "reason": str(e) or type(e).__name__})
            raise
    with ledger.lock():
        entries = ledger.entries()
        earlier = _repeat_check(h, entries, allow_resubmit)
        failed = list(pre.get("failed", []))
        reserve: dict = {}
        account = getattr(backend, "_reserve", None)
        if account is not None:
            more, reserve = account(job, pre, entries)
            failed += more
        if failed:
            err = getattr(backend, "_refusal", _default_refusal)(failed)
            ledger._write([{"event": "refused", "job_hash": h, "utc": utc_now(), "reason": str(err)}])
            raise err
        now = utc_now()
        sending = {
            "event": "sending",
            "job_hash": h,
            "provider": backend.name,
            "processor": backend.processor,
            "utc": now,
            "n_pairs": len(job.pairs),
            "positions": job.active_positions,
            "shots": job.shots,
            "allow_resubmit": bool(allow_resubmit),
            "earlier_sends": len(earlier),
        }
        if earlier:
            sending["resubmit_reason"] = reason or "none given"
        ledger._write([{"event": "reserved", "job_hash": h, "utc": now, **reserve}, sending])
    if earlier:
        log(
            f"resubmitting job {h[:12]} with allow_resubmit, reason: {reason or 'none given'} (logged in {ledger.path})"
        )
    try:
        handle = backend._send(job, **send_kw)
    except Exception as e:
        failed_rec = {"event": "failed", "job_hash": h, "utc": utc_now(), "error": type(e).__name__}
        if getattr(e, "job_ids_created", None) is not None:
            failed_rec["job_ids_created"] = list(e.job_ids_created)
        failed_rec["reservation"] = "kept: the send may have reached the provider; a fetch settles it"
        _record_after_send(ledger, failed_rec, log)
        raise
    _record_after_send(ledger, {"event": "sent", "job_hash": h, "utc": utc_now(), "handle": asdict(handle)}, log)
    return handle


def _record_after_send(ledger: Ledger, entry: dict, log) -> None:
    """A record of something that already happened. If the lock cannot be taken, print it rather than lose it: the
    reservation written before the send already refuses a repeat."""
    try:
        ledger.append(entry)
    except LockTimeout as e:
        log(f"warning: the {entry['event']} record could not be written ({e}): {json.dumps(entry, default=str)}")


class GuardedSubmit:
    """Mixin for a backend that spends: submit() is the submit-once guard, and the backend's _send() does the sending.

    ledger: the backend's own ledger (default: Ledger(), at ./.manacitra/ledger.jsonl or $MANACITRA_LEDGER).

    A backend may define three hooks, each called by submit_once:

        _preflight(job, ledger, **send_kw) -> dict
            the provider reads, before the lock; failed checks go in its "failed" list
        _reserve(job, pre, entries) -> (failed, reservation)
            every check on a shared quantity (a balance, a budget, a cap), under the lock, against the ledger's
            entries as read under it: the deciding check (see the module docstring's rule)
        _refusal(failed) -> SpendRefused
            the exception naming every failed check
    """

    spends = True
    ledger: Ledger | None = None

    def submit(
        self,
        job: MapJob,
        *,
        ledger: Ledger | None = None,
        allow_resubmit: bool = False,
        reason: str | None = None,
        log=print,
        **send_kw,
    ) -> JobHandle:
        """Send the job once, through the guard: refused if this job was sent before, unless allow_resubmit."""
        return submit_once(
            self, job, ledger or self.ledger, allow_resubmit=allow_resubmit, log=log, reason=reason, **send_kw
        )

    def _ledger(self) -> Ledger:
        return self.ledger or Ledger()

    def _send(self, job: MapJob, **send_kw) -> JobHandle:  # pragma: no cover - each backend defines it
        raise NotImplementedError
