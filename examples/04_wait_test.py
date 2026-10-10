# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""Kickoff 47's Part B and the wait test, on a backend and a chain you name (Amendment A18). A dry run unless --submit.

    python examples/04_wait_test.py --processor ibm_fez --chain 144-143-142 --offline   dry run, offline snapshot
    python examples/04_wait_test.py --processor ibm_fez --chain 144-143-142             dry run, the live backend
    python examples/04_wait_test.py ... --submit --cap-s 300                             send once, through the guard
    python examples/04_wait_test.py --fetch HANDLE.json                                  fetch the counts, analyse them
    python examples/04_wait_test.py --analyse COUNTS.json                                analyse saved counts

The job is the wait test without and with XY4 refocusing on the chain L1-M-L3, five copies of each in an order drawn
from a seed, then Part B (Ramsey and echo at six waits) on M alone and on the two end lines, each circuit twice.
Nothing is sent without --submit. With it, the submit-once guard reads the usage, checks the cap against the ledger's
open reservations, and records the job before sending it; a second send of the same circuits is refused. A dry run
prints the circuits, the shot count and the repository's own time estimate; IBM gives its estimate only once a job
exists (Qiskit Runtime's usage_estimation), so a submission prints it after sending.

A run is a new measurement, with a brief of its own (docs/kickoffs.md): it does not check the archived one.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from manacitra import wait
from manacitra.backends.base import JobHandle
from manacitra.backends.ibm import CircuitJob, IBMCircuitsBackend, SnapshotService, estimate_seconds


def chain_of(text: str) -> list[int]:
    chain = [int(q) for q in text.replace(",", "-").split("-")]
    if len(chain) != 3:
        raise SystemExit("--chain names three qubits, L1-M-L3, for example 144-143-142")
    return chain


def groups_of(text: str | None):
    if not text:
        return None
    return [tuple(int(q) for q in g.split(",")) for g in text.split(";")]


def report(result: dict) -> None:
    w = result.get("wait_test")
    if w:
        print(f"wait test: F without refocusing {w['F_no']:.4f}, with {w['F_refocus']:.4f}; gain {w['gain']:+.4f}")
    b = result.get("part_b")
    if b:
        print(f"Part B, at the wait of {b['reference_wait_dt']} dt:")
        for q, row in b["qubits"].items():
            r, e = row["r"], row["e"]
            kind = row["kind_of_loss"]
            print(f"  qubit {q}: Ramsey loss {r:.3f} {row['r_ci90']}, echo loss {e:.3f} {row['e_ci90']}: {kind}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--processor", default="ibm_fez")
    ap.add_argument("--chain", help="L1-M-L3, three physical qubits, L1 and L3 each coupled to M")
    ap.add_argument("--groups", help="Part B's groups, for example 143,131,124;142,144,125 (default: M; L1 and L3)")
    ap.add_argument("--copies", type=int, default=5)
    ap.add_argument("--shots-wait", type=int, default=10_000)
    ap.add_argument("--shots-b", type=int, default=4_000)
    ap.add_argument(
        "--offline", action="store_true", help="dry run on qiskit-ibm-runtime's offline snapshot, no account"
    )
    ap.add_argument("--submit", action="store_true", help="actually send the job (spends time)")
    ap.add_argument("--cap-s", type=float, default=None, help="with --submit: the usage cap in seconds (required)")
    ap.add_argument("--allow-resubmit", action="store_true", help="allow a second send of the same circuits (logged)")
    ap.add_argument("--resubmit-reason", default=None)
    ap.add_argument("--handle-out", type=Path, default=Path("wait-test-handle.json"))
    ap.add_argument("--fetch", type=Path, help="a handle file written by --submit: fetch the counts and analyse them")
    ap.add_argument("--counts-out", type=Path, default=Path("wait-test-counts.json"))
    ap.add_argument("--analyse", type=Path, help="a counts file written by --fetch: analyse it, offline")
    a = ap.parse_args(argv)

    if a.analyse:
        run = json.loads(a.analyse.read_text())
        report(wait.analyse_wait_run(run["labels"], run["counts"], run["dt"]))
        return 0
    if a.fetch:
        h = json.loads(a.fetch.read_text())
        be = IBMCircuitsBackend(h["processor"])
        run = be.fetch_counts(JobHandle(**h["handle"]))
        run["dt"] = h["dt"]
        a.counts_out.write_text(json.dumps(run, indent=1))
        print(f"counts written to {a.counts_out}")
        report(wait.analyse_wait_run(run["labels"], run["counts"], run["dt"]))
        return 0
    if not a.chain:
        ap.error("--chain is required (unless --fetch or --analyse)")
    chain = chain_of(a.chain)
    if a.offline and a.submit:
        ap.error("an offline snapshot cannot submit anything")
    be = IBMCircuitsBackend(a.processor, service=SnapshotService(a.processor) if a.offline else None)
    backend = be.backend()
    circuits, labels, shots = wait.wait_run(
        chain, backend, groups_of(a.groups), copies=a.copies, shots_wait=a.shots_wait, shots_b=a.shots_b
    )
    job = CircuitJob(circuits, labels, shots, name="wait-test")
    waits = wait.wait_lengths(backend, chain)
    where = "the offline snapshot" if a.offline else "the live backend"
    print(f"{a.processor} ({where}), chain {'-'.join(map(str, chain))}: L1 {chain[0]}, M {chain[1]}, L3 {chain[2]}")
    for name, w in waits.items():
        print(f"  M waits while {name} ({w['qubit']}) is measured and reset: {w['dt']} dt = {w['us']:.3f} us")
    plain = circuits[next(i for i, x in enumerate(labels) if x.get("variant") == "no")]
    refocused = circuits[next(i for i, x in enumerate(labels) if x.get("variant") == "refocus")]
    sched = wait.scheduled(plain, backend.target)
    print(f"  M's idle windows without refocusing (dt): {wait.idle_windows(sched, chain[1])}")
    print(f"  pulses inserted with refocusing: {dict(refocused.count_ops()).get('x', 0)} X in all")
    print("\nThe wait test, as built for the backend (idle qubits not drawn):")
    print(plain.draw(output="text", idle_wires=False, fold=-1))
    print("\nThe same with XY4 refocusing:")
    print(refocused.draw(output="text", idle_wires=False, fold=-1))
    b_first = [i for i, x in enumerate(labels) if x.get("part") == "B" and x["copy"] == 1]
    print(f"\nPart B: {len(b_first)} circuits and their second copy in reverse order; for example:")
    for i in b_first:
        if labels[i]["tau_dt"] == wait.REFERENCE_WAIT_DT:
            print(f"  {labels[i]}")
            print(circuits[i].draw(output="text", idle_wires=False, fold=-1))
    total = job.total_shots
    print(
        f"\n{len(circuits)} circuits, {total:,} shots. The repository's estimate: {estimate_seconds(total):.1f} s "
        "(0.3 ms per shot + 5 s). IBM's own estimate: given only once a job exists (usage_estimation)."
    )
    if not a.submit:
        print("dry run: nothing sent; add --submit (with --cap-s) to send")
        return 0
    if a.cap_s is None:
        ap.error("--submit needs --cap-s, the usage cap in seconds")
    be.cap_s = a.cap_s
    handle = be.submit(job, allow_resubmit=a.allow_resubmit, reason=a.resubmit_reason)
    from dataclasses import asdict

    a.handle_out.write_text(
        json.dumps({"processor": a.processor, "dt": backend.dt, "handle": asdict(handle)}, indent=1)
    )
    print(f"sent: job {handle.job_ids[0]}; handle written to {a.handle_out}")
    try:
        est = be.service.job(handle.job_ids[0]).usage_estimation
        print(f"IBM's estimate: {est}")
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
