# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""The command line: manacitra map | pick | verdict | persist | report | seal | reveal | verify.

Dry run by default. Nothing is sent to any provider without --submit, and before anything is sent the estimate and
the ledger entry are printed. The simulator spends nothing and runs at once. --data PATH (or $MANACITRA_DATA) names
the archived dataset's folder, for an install that is not from a clone; a file argument not found as given is looked
up inside it.

    manacitra map --backend simulator --pairs 0-1,2-3,... [--planted 0.03]       map pairs on the simulator
    manacitra map --backend ibm --processor ibm_fez --pairs-from-score 27         dry run: transpile, check, estimate
    manacitra map --backend ibm --processor ibm_fez --pairs-file p.json --submit  send once (refused if already sent)
    manacitra verdict data/ibm_fez/k31-map.json                                   the map rule on a counts file
    manacitra pick data/ibm_fez/k31-map.json --n 8                                rank pairs (verdict not checked)
    manacitra persist day1.json day2.json day3.json                               the persistence rule
    manacitra report data/ibm_fez/k31-map.json --figure fez-map.svg               a table, and a chip map
    manacitra seal predictions.md                                                 commit to a file before the run
    manacitra reveal predictions.md                                               publish its salt after the run
    manacitra verify predictions.md                                               anyone checks it
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from . import __version__
from .circuits import ORDER_16
from .report import map_table, verdict_lines


def _parse_pairs(s: str) -> list[tuple[int, int]]:
    return [tuple(int(q) for q in p.split("-")) for p in s.split(",") if p.strip()]


def _load_counts_file(path: str) -> tuple[np.ndarray, list[str], list, list | None, int]:
    """A MapCounts JSON written by `manacitra map`, or an archived map file from data/."""
    from .archive import resolve

    d = json.loads(resolve(path).read_text())
    if "outcomes" in d:
        from .backends.base import MapCounts

        mc = MapCounts.from_json(d)
        return mc.p11(), mc.order, mc.pairs, d.get("meta", {}).get("x"), d.get("meta", {}).get("seed", 31)
    from .archive import p11_table

    x = [r["x"] for r in d["published_at_submission"]] if "published_at_submission" in d else d.get("x")
    pairs = [p["qubits"] if isinstance(p, dict) else p for p in d["pairs"]]
    return p11_table(d), d["order"], pairs, x, d["meta"].get("permutation_seed", 31)


def make_backend(a):
    if a.backend == "simulator":
        from .backends.simulator import NoiseModel, SimulatorBackend

        pairs = _parse_pairs(a.pairs) if a.pairs else [(2 * i, 2 * i + 1) for i in range(a.n_pairs)]
        noise = NoiseModel.random(pairs, seed=a.seed)
        if a.planted:
            noise, _ = noise.planted(a.planted, seed=a.seed + 1)
        return SimulatorBackend(noise, seed=a.seed), pairs
    if a.backend == "ibm":
        from .backends.ibm import IBMBackend, SnapshotService

        service = SnapshotService(a.processor) if a.offline else None
        return IBMBackend(a.processor, service=service, cap_s=a.cap), None
    if a.backend == "openquantum":
        from .backends.openquantum import OpenQuantumBackend

        return OpenQuantumBackend(a.processor or "rigetti:cepheus-1-108q", budget_credits=a.budget), None
    if a.backend == "cirq_sim":
        from .backends.cirq_sim import CirqSimBackend

        return CirqSimBackend(a.processor or "willow_pink", noise="pauli", seed=a.seed), None
    raise SystemExit(f"unknown backend {a.backend}")


def cmd_map(a) -> int:
    from .backends.base import Ledger, MapJob, submit_once
    from .layout import disjoint_pairs_by_score

    backend, pairs = make_backend(a)
    if pairs is None:
        if a.pairs:
            pairs = _parse_pairs(a.pairs)
        elif a.pairs_file:
            pairs = [tuple(p) for p in json.loads(Path(a.pairs_file).read_text())]
        else:
            t = backend.target()
            if not t.pairs:
                raise SystemExit("this provider publishes no per-pair figures; give --pairs or --pairs-file")
            pairs = [p for p, _ in disjoint_pairs_by_score({k: f.x for k, f in t.pairs.items()}, a.pairs_from_score)]
    job = MapJob(pairs, list(ORDER_16), shots=a.shots)
    if backend.spends:
        if not a.submit:
            print(f"dry run: {len(pairs)} pairs, {len(job.order)} circuits x {job.shots} shots on {backend.processor}.")
            if hasattr(backend, "transpile"):
                _, checks = backend.transpile(job)
                print(f"transpile checks: {len(checks)} circuits, 3 CZ per pair, no swaps, layout kept")
                from .backends.ibm import estimate_seconds

                print(f"estimate: {estimate_seconds(job.total_shots):.1f} s (0.3 ms per shot + 5 s)")
            print("nothing was sent. Add --submit to send it once.")
            return 0
        est = backend.estimate(job)
        print(f"estimate: {est.amount:g} {est.unit} ({est.detail})")
        ledger = Ledger(a.ledger)
        print(f"ledger: {ledger.path}, job hash {job.job_hash(backend.name, backend.processor)[:12]}")
        if a.allow_resubmit:
            print(
                "--allow-resubmit given: a second send of this job is allowed and is logged, with the reason: "
                f"{a.resubmit_reason or 'none given'}"
            )
        handle = submit_once(backend, job, ledger, allow_resubmit=a.allow_resubmit, reason=a.resubmit_reason)
        print(f"sent: {handle.job_ids}. Fetch it later with the Python API (backend.fetch(handle)).")
        Path(a.out).write_text(json.dumps({"handle": handle.__dict__}, indent=1, default=list))
        return 0
    counts = backend.fetch(backend.submit(job))
    x = backend.target().x_of(pairs)
    counts.meta.update({"x": x, "seed": a.seed})
    Path(a.out).write_text(json.dumps(counts.to_json()))
    print(f"wrote {a.out}")
    from .verdicts import analyse_map

    an = analyse_map(counts.p11(), counts.order, x=x, shots=a.shots, seed=a.perm_seed)
    print(verdict_lines(an))
    return 0


def cmd_verdict(a) -> int:
    from .verdicts import analyse_map

    P, order, pairs, x, seed = _load_counts_file(a.file)
    an = analyse_map(
        P,
        order,
        x=None if a.no_score else x,
        seed=a.perm_seed or seed,
        dead_pair_floor=0.5 if (x is None or a.no_score) else None,
    )
    print(verdict_lines(an))
    if a.json:
        Path(a.json).write_text(json.dumps(an, indent=1))
    return 0


USABLE_VERDICTS = ("DIAGNOSTIC", "MAP PRESENT")


def cmd_pick(a) -> int:
    """Rank pairs from a map. It does not condition on the verdict; it warns (on stderr) when the map's verdict is not
    DIAGNOSTIC or MAP PRESENT. Running the user's own job on the pairs is the user's step, not Manacitra's."""
    from .keptshare import kept_from_order
    from .layout import pick_pairs
    from .verdicts import analyse_map

    P, order, pairs, x, seed = _load_counts_file(a.file)
    v = analyse_map(P, order, x=x, seed=seed, dead_pair_floor=0.5 if x is None else None)["verdict"]["verdict"]
    if v not in USABLE_VERDICTS:
        print(
            f"warning: this map's verdict is {v}, not DIAGNOSTIC or MAP PRESENT; the ranking below may not be "
            "worth using. pick ranks pairs and does not check the verdict.",
            file=sys.stderr,
        )
    k = kept_from_order(P, order, "A")[0]
    idx = pick_pairs(k, a.n) if a.by == "k" else pick_pairs(x, a.n, highest=False)
    print(f"the {a.n} pairs by {'kept share (highest first)' if a.by == 'k' else 'published score (lowest first)'}:")
    for i in idx:
        print(f"  {list(pairs[i])}  k_A {k[i]:.3f}" + (f"  x {x[i]:.4f}" if x is not None else ""))
    return 0


def cmd_persist(a) -> int:
    from .verdicts import persistence_analysis

    days = {}
    for n, f in enumerate(a.days, start=1):
        days[n] = json.loads(Path(f).read_text())
    out = persistence_analysis(days)
    for name in ("verdict", "original_rule"):
        v = out[name]
        print(f"{v['rule']}: {v['verdict']}" + (f"  ({v['note']})" if v.get("note") else ""))
    if a.json:
        Path(a.json).write_text(json.dumps(out, indent=1, default=str))
    return 0


def cmd_report(a) -> int:
    from .keptshare import kept_from_order

    P, order, pairs, x, _ = _load_counts_file(a.file)
    kA = kept_from_order(P, order, "A")[0]
    kB = kept_from_order(P, order, "B")[0] if any(lbl.startswith("B") for lbl in order) else None
    print(map_table(pairs, kA, kB, x))
    if a.figure:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        from .report import chip_map

        cmap = json.loads(Path(a.coupling_map).read_text())["edges"] if a.coupling_map else [tuple(p) for p in pairs]
        fig, ax = plt.subplots(figsize=(8, 5))
        sm = chip_map(ax, cmap, {tuple(p): float(v) for p, v in zip(pairs, kA)})
        cb = fig.colorbar(sm, ax=ax, shrink=0.6)
        cb.set_label("kept share k_A (higher: kept more)")
        fig.savefig(a.figure, bbox_inches="tight")
        print(f"wrote {a.figure}")
    return 0


def cmd_seal(a) -> int:
    from .seal import SealError, seal

    try:
        rec = seal(a.file, force=a.force)
    except SealError as e:
        print(f"refused: {e}")
        return 1
    print(f"sealed {a.file} at {rec['sealed_utc']}; the salt is in .seals/ (keep it private)")
    print(f"post this hash where you cannot edit it:\n{rec['hash']}")
    return 0


def cmd_reveal(a) -> int:
    from .seal import SealError, reveal

    try:
        rec = reveal(a.file)
    except SealError as e:
        print(f"refused: {e}")
        return 1
    print(f"revealed: the salt for {a.file} is now in its commit record; publish both")
    print(f"salt {rec['salt']}")
    return 0


def cmd_verify_seal(a) -> int:
    from .seal import verify

    v = verify(a.file, a.salt)
    print(v.message)
    return 0 if v.match else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="manacitra", description="A map of a quantum processor's qubit pairs.")
    ap.add_argument("--version", action="version", version=f"manacitra {__version__}")
    ap.add_argument(
        "--data",
        metavar="PATH",
        help="the archived dataset's folder (data/ in a clone); default: $MANACITRA_DATA, else data/ beside the "
        "source when installed from a clone. File arguments not found as given are looked up inside it.",
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    m = sub.add_parser("map", help="map pairs (dry run unless --submit)")
    m.add_argument("--backend", default="simulator", choices=["simulator", "ibm", "openquantum", "cirq_sim"])
    m.add_argument("--processor", default=None)
    m.add_argument("--pairs", help="comma-separated a-b pairs, e.g. 0-1,4-5")
    m.add_argument("--pairs-file", help="a JSON list of [a, b] pairs")
    m.add_argument(
        "--pairs-from-score", type=int, default=27, help="choose this many disjoint pairs by published score"
    )
    m.add_argument("--n-pairs", type=int, default=27, help="simulator: how many pairs")
    m.add_argument("--planted", type=float, default=0.0, help="simulator: plant a map with this SD (radians)")
    m.add_argument("--shots", type=int, default=8000)
    m.add_argument("--seed", type=int, default=0)
    m.add_argument("--perm-seed", type=int, default=31)
    m.add_argument("--cap", type=float, default=540.0, help="ibm: refuse if used + estimate exceeds this many seconds")
    m.add_argument("--budget", type=float, default=None, help="openquantum: refuse above this many credits")
    m.add_argument("--offline", action="store_true", help="ibm: dry run on the offline snapshot, no account")
    m.add_argument("--submit", action="store_true", help="actually send the job (spends time or credits)")
    m.add_argument("--allow-resubmit", action="store_true", help="allow a second send of the same job (logged)")
    m.add_argument("--resubmit-reason", default=None, help="why the job is sent again, logged with --allow-resubmit")
    m.add_argument("--ledger", default=None)
    m.add_argument("--out", default="map-counts.json")
    m.set_defaults(func=cmd_map)

    v = sub.add_parser("verdict", help="the map rule on a counts file")
    v.add_argument("file")
    v.add_argument("--perm-seed", type=int, default=None)
    v.add_argument("--no-score", action="store_true", help="ignore any published score (the capped rule)")
    v.add_argument("--json")
    v.set_defaults(func=cmd_verdict)

    p = sub.add_parser("pick", help="rank pairs from a map; warns when the verdict is not DIAGNOSTIC or MAP PRESENT")
    p.add_argument("file")
    p.add_argument("--n", type=int, default=8)
    p.add_argument("--by", choices=["k", "x"], default="k")
    p.set_defaults(func=cmd_pick)

    s = sub.add_parser("persist", help="the persistence rule over two or three days")
    s.add_argument("days", nargs="+", help="one JSON per day: {edges, x, obs}")
    s.add_argument("--json")
    s.set_defaults(func=cmd_persist)

    r = sub.add_parser("report", help="a table and, optionally, the chip map figure")
    r.add_argument("file")
    r.add_argument("--figure")
    r.add_argument("--coupling-map", help="a coupling-map.json from data/")
    r.set_defaults(func=cmd_report)

    sl = sub.add_parser("seal", help="commit to a file now (salted SHA-256), without showing it")
    sl.add_argument("file")
    sl.add_argument("--force", action="store_true", help="seal again, replacing the earlier commitment")
    sl.set_defaults(func=cmd_seal)

    rv = sub.add_parser("reveal", help="add a sealed file's salt to its commit record, for publication")
    rv.add_argument("file")
    rv.set_defaults(func=cmd_reveal)

    vf = sub.add_parser("verify", help="check a file and its revealed salt against its commit record")
    vf.add_argument("file")
    vf.add_argument("--salt", help="a salt given by hand, in hexadecimal, instead of the revealed one")
    vf.set_defaults(func=cmd_verify_seal)

    a = ap.parse_args(argv)
    from . import archive

    if a.data:
        archive.set_data_dir(a.data)
    try:
        return a.func(a)
    except archive.DataNotFound as e:
        print(f"manacitra: {e}", file=sys.stderr)
        return 2
    finally:
        if a.data:
            archive.set_data_dir(None)


if __name__ == "__main__":
    sys.exit(main())
