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

The submit-once guard lives here, not in any backend: submit_once() writes a ledger record (job hash, provider, UTC
time) before anything is sent, adds the handle once it exists, and refuses a second submission of the same job hash
unless allow_resubmit is given, which is itself logged. A backend that spends (IBM, Open Quantum) inherits
GuardedSubmit, so its public submit() is that guard and its raw send is the private _send(); there is no unguarded
public path. Backends that spend nothing (the simulators) keep a direct submit() and skip the ledger.

A spending backend may also define _preflight(job, ledger, **kw), run after the repeat check and before the ledger's
"sending" record. It refuses with SpendRefused, naming each check that failed (logged as "refused", which is not a
send), or returns a credit reservation, written to the ledger before sending and kept after an ambiguous failure.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from collections.abc import Sequence
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


class Ledger:
    """An append-only JSON-lines file of submissions. Default: ./.manacitra/ledger.jsonl, or $MANACITRA_LEDGER."""

    def __init__(self, path: str | os.PathLike | None = None):
        self.path = Path(path or os.environ.get("MANACITRA_LEDGER", Path.cwd() / ".manacitra" / "ledger.jsonl"))

    def entries(self) -> list[dict]:
        if not self.path.exists():
            return []
        return [json.loads(line) for line in self.path.read_text().splitlines() if line.strip()]

    def append(self, entry: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a") as f:
            f.write(json.dumps(entry, sort_keys=True) + "\n")

    def find(self, job_hash: str) -> list[dict]:
        return [e for e in self.entries() if e.get("job_hash") == job_hash]

    def reservations(self, scope: str) -> list[dict]:
        """Every credit reservation in a budget scope, each marked settled once a fetch has settled its job."""
        es = self.entries()
        settled = {e["job_hash"] for e in es if e.get("event") == "settled"}
        return [
            {**e, "settled": e["job_hash"] in settled}
            for e in es
            if e.get("event") == "reserved" and e["scope"] == scope
        ]

    def reserved_credits(self, scope: str) -> float:
        """Credits reserved in a scope, settled or not: a settled reservation was spent, an open one may have been."""
        return float(sum(e["credits"] for e in self.reservations(scope)))


def submit_once(
    backend: Backend,
    job: MapJob,
    ledger: Ledger | None = None,
    allow_resubmit: bool = False,
    log=print,
    **send_kw,
) -> JobHandle:
    """Submit a job once. The ledger record is written before anything is sent; a second submission of the same job
    hash is refused unless allow_resubmit is True, and that permission is logged. send_kw go to the backend's
    _preflight and _send (Open Quantum: after, the earlier wave)."""
    if not getattr(backend, "spends", True):
        return backend.submit(job)
    ledger = ledger or getattr(backend, "ledger", None) or Ledger()
    h = job.job_hash(backend.name, backend.processor)
    earlier = [e for e in ledger.find(h) if e.get("event") == "sending"]
    if earlier and not allow_resubmit:
        raise ResubmitRefused(
            f"refused: this job (hash {h[:12]}) was already sent at {earlier[0]['utc']}; "
            "pass allow_resubmit (CLI: --allow-resubmit) to send it again"
        )
    reserve = None
    preflight = getattr(backend, "_preflight", None)
    if preflight is not None:
        try:
            reserve = (preflight(job, ledger, **send_kw) or {}).get("reserve")
        except SpendRefused as e:
            ledger.append({"event": "refused", "job_hash": h, "utc": utc_now(), "reason": str(e)})
            raise
    if reserve is not None:
        ledger.append({"event": "reserved", "job_hash": h, "utc": utc_now(), **reserve})
    ledger.append(
        {
            "event": "sending",
            "job_hash": h,
            "provider": backend.name,
            "processor": backend.processor,
            "utc": utc_now(),
            "n_pairs": len(job.pairs),
            "positions": job.active_positions,
            "shots": job.shots,
            "allow_resubmit": bool(allow_resubmit),
            "earlier_sends": len(earlier),
        }
    )
    if earlier:
        log(f"resubmitting job {h[:12]} with allow_resubmit (logged in {ledger.path})")
    try:
        handle = backend._send(job, **send_kw)
    except Exception as e:
        failed = {"event": "failed", "job_hash": h, "utc": utc_now(), "error": type(e).__name__}
        if getattr(e, "job_ids_created", None) is not None:
            failed["job_ids_created"] = list(e.job_ids_created)
        if reserve is not None:
            failed["reservation"] = "kept: the send may have created tasks; a fetch settles it"
        ledger.append(failed)
        raise
    ledger.append({"event": "sent", "job_hash": h, "utc": utc_now(), "handle": asdict(handle)})
    return handle


class GuardedSubmit:
    """Mixin for a backend that spends: submit() is the submit-once guard, and the backend's _send() does the sending.

    ledger: the backend's own ledger (default: Ledger(), at ./.manacitra/ledger.jsonl or $MANACITRA_LEDGER).
    """

    spends = True
    ledger: Ledger | None = None

    def submit(
        self, job: MapJob, *, ledger: Ledger | None = None, allow_resubmit: bool = False, log=print, **send_kw
    ) -> JobHandle:
        """Send the job once, through the guard: refused if this job was sent before, unless allow_resubmit."""
        return submit_once(self, job, ledger or self.ledger, allow_resubmit=allow_resubmit, log=log, **send_kw)

    def _send(self, job: MapJob, **send_kw) -> JobHandle:  # pragma: no cover - each backend defines it
        raise NotImplementedError
