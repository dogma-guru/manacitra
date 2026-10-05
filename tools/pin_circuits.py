# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""Write, or check, src/manacitra/pinned_circuits.json: every circuit the package runs, as an exact gate list.

    python tools/pin_circuits.py --check    every pinned circuit is its exact unitary (the test suite does this too)
    python tools/pin_circuits.py --write    synthesise afresh and overwrite the pinned file (do not, without a reason)

Qiskit's three-CZ synthesis is numerical; its single-qubit layers can differ between platforms' linear-algebra
libraries while the unitary stays the same. A coherent error after each CZ then lands differently, so a map made with
circuits synthesised on one machine is not strictly comparable with a map made with another's. The package therefore
runs pinned circuits, generated once with the Qiskit the published runs used (2.5.2), on the machine they ran from.
"""

import argparse
import json
import platform
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "src" / "manacitra" / "pinned_circuits.json"
VARIANTS = [f"{c} {v}" for c in "AB" for v in ("no", "off", "wrong")]


def write():
    import qiskit

    from manacitra.backends import openquantum as oq
    from manacitra.circuits import block, circuit_record
    from manacitra.workload import draw_unitaries, workload_block

    blocks = {label: circuit_record(block(label, synthesise=True)) for label in VARIANTS}
    for j, units in enumerate(draw_unitaries(33), start=1):
        blocks[f"R{j}"] = circuit_record(workload_block(units))
    native = {
        label: [[g, list(qs), ang] for g, qs, ang in oq.native_ops(label, synthesise=True)]
        for label in ("A no", "A off", "B no", "B off")
    }
    meta = {
        "description": "every circuit the package runs, as an exact gate list; see tools/pin_circuits.py",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "qiskit": qiskit.__version__,
        "numpy": np.__version__,
        "platform": f"{platform.system()} {platform.machine()}",
        "blocks": "TwoQubitBasisDecomposer(CZ, euler_basis='ZSX'), three basis uses; "
        "workload R1..R8 from default_rng(33)",
        "native_rz_rx": "Kickoff 34b's template: TwoQubitBasisDecomposer(CZ, euler_basis='U'), each single-qubit "
        "layer as rz, rx(pi/2), rz, rx(pi/2), rz",
    }
    OUT.write_text(json.dumps({"meta": meta, "blocks": blocks, "native_rz_rx": native}, indent=1) + "\n")
    print(f"wrote {OUT}")


def check() -> int:
    from qiskit.quantum_info import Operator

    from manacitra.backends.openquantum import native_ops, pair_circuit
    from manacitra.circuits import CIRCUITS, offset_of, parse_label, pinned_block, unitary
    from manacitra.workload import draw_unitaries

    def same(u, v):
        return abs(abs(np.vdot(u.flatten(), v.flatten())) / 4 - 1)

    worst = 0.0
    for label in VARIANTS:
        c, _ = parse_label(label)
        qc = pinned_block(label)
        assert qc.count_ops()["cz"] == 3, label
        worst = max(worst, same(Operator(qc).data, unitary(CIRCUITS[c].c, offset_of(label))))
    for j, units in enumerate(draw_unitaries(33), start=1):
        prod = units[2] @ units[1] @ units[0]
        qc = pinned_block(f"R{j}")
        assert qc.count_ops()["cz"] == 9
        worst = max(worst, same(Operator(qc).data, prod))
    for label in ("A no", "A off", "B no", "B off"):
        c, _ = parse_label(label)
        worst = max(
            worst, same(Operator(pair_circuit(native_ops(label))).data, unitary(CIRCUITS[c].c, offset_of(label)))
        )
    print(f"every pinned circuit is its exact unitary to {worst:.1e}")
    return 0 if worst < 1e-9 else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.write:
        write()
    sys.exit(check())
