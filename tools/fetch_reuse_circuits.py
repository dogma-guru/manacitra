# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""Fetch the four public circuits of Kickoffs 43 to 47, check them, and recompute their exact ideal outputs.

    python tools/fetch_reuse_circuits.py DIR

The circuits are not in this release, because their licences are unclear: the CaQR repository, the source of XOR_5,
BV_10 and Sym_9, carries no licence; QASMBench's licence allows redistribution, but its multiply circuit (Mul_13)
credits a repository that carries none. So data/ibm_fez/k43-reuse.json keeps, for each circuit, the repository, the
commit, the path and the SHA-256 of the file the runs used, and this script fetches them.

Each file is downloaded at that commit into DIR, which must be a new or empty folder, and refused if its SHA-256
differs. Then the circuit's exact output distribution, on the classical bits the runs measured, is computed with
Qiskit's statevector and compared with the ideal archived in k43-reuse.json. A file with no measurements is measured
as the runs measured it: every qubit that takes part in a gate, the k-th of them into classical bit k.

It does not rebuild the compiled reuse circuits. They came from a reimplementation of QR-Map's Tapering (Kim et al.,
ISCA 2025, doi 10.1145/3695053.3731020), written for the study from the paper and not in this release; their SHA-256,
their structure (lines, CZ count on each line position, measurements and resets per line) and their exact ideal
outputs are in k43-reuse.json.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RECORD = ROOT / "data" / "ibm_fez" / "k43-reuse.json"


def raw_url(source: dict) -> str:
    owner_repo = source["repository"].removeprefix("github.com/")
    return f"https://raw.githubusercontent.com/{owner_repo}/{source['commit']}/{source['path']}"


def exact_distribution(qasm_text: str, measured_clbits: list[int]) -> dict[str, float]:
    """The exact output distribution of an OpenQASM 2 circuit on these classical bits, the last listed first."""
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Statevector

    qc = QuantumCircuit.from_qasm_str(qasm_text)
    body, measured, used = QuantumCircuit(qc.num_qubits), {}, set()
    for inst in qc.data:
        qubits = [qc.find_bit(b).index for b in inst.qubits]
        if inst.operation.name == "measure":
            measured[qc.find_bit(inst.clbits[0]).index] = qubits[0]
        elif inst.operation.name != "barrier":
            used |= set(qubits)
            body.append(inst.operation, qubits)
    if not measured:
        measured = dict(enumerate(sorted(used)))
    out: dict[str, float] = {}
    for key, p in Statevector(body).probabilities_dict().items():
        bits = key[::-1]  # qubit 0 first
        k = "".join(bits[measured[c]] for c in reversed(measured_clbits))
        out[k] = out.get(k, 0.0) + float(p)
    return {k: v for k, v in out.items() if v > 1e-12}


def total_variation(p: dict, q: dict) -> float:
    return 0.5 * sum(abs(p.get(k, 0.0) - q.get(k, 0.0)) for k in set(p) | set(q))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("dir", type=Path, help="a new or empty folder for the downloaded files")
    a = ap.parse_args(argv)
    if a.dir.exists() and any(a.dir.iterdir()):
        print(f"{a.dir} is not empty: give a new or empty folder", file=sys.stderr)
        return 2
    a.dir.mkdir(parents=True, exist_ok=True)
    circuits = json.loads(RECORD.read_text())["circuits"]
    bad = 0
    for name, c in circuits.items():
        src = c["source"]
        data = urllib.request.urlopen(raw_url(src), timeout=60).read()
        got = hashlib.sha256(data).hexdigest()
        if got != src["sha256"]:
            print(f"{name}: SHA-256 {got} differs from the archived {src['sha256']}; not kept", file=sys.stderr)
            bad += 1
            continue
        path = a.dir / Path(src["path"]).name
        path.write_bytes(data)
        tvd = total_variation(exact_distribution(data.decode(), c["measured_clbits"]), c["ideal"])
        ok = tvd < 1e-6
        bad += not ok
        verdict = "" if ok else ", DIFFERS"
        print(f"{name}: {path.name}, SHA-256 matches; exact ideal against the archive, TVD {tvd:.1e}{verdict}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
