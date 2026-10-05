# Copyright 2026 Anish Patel
# SPDX-License-Identifier: Apache-2.0
"""The Cirq simulation path (experimental). Needs the [cirq] extra.

**This is a simulator only. It is not hardware access**: it signs in to nothing and calls no Quantum Engine. It loads
the median calibration that Cirq ships for a Quantum Virtual Machine processor (willow_pink by default), builds a noise
model from those published figures, and simulates each pair on its own as an exact two-qubit density matrix, as
Kickoff 36 did. Its output is what a published noise model does, not what any chip does.

Ported from Kickoff 36:

* the circuits are synthesised in Qiskit with exactly 3 CZ, exported to OpenQASM 2, imported into Cirq, and their
  single-qubit runs merged to PhasedXZ;
* the published score x per pair is the two-qubit Pauli error plus both readout errors, readout error = (p00 error +
  p11 error) / 2;
* the "pauli" noise model: after each CZ an optional planted Z over-rotation, then two-qubit depolarizing at the pair's
  Pauli error; after each single-qubit gate, depolarizing at the qubit's RB Pauli error; readout flips per qubit;
* the "qvm" noise model: the QVM's own noise model from the same calibration.

Qubits are numbered by their position in the processor's sorted qubit list, so pairs are integer pairs as elsewhere.
"""

from __future__ import annotations

import math

import numpy as np

from .base import Estimate, JobHandle, MapCounts, MapJob, PairFigures, Target, utc_now

PROCESSOR = "willow_pink"


def load_qvm(processor: str = PROCESSOR):
    """The QVM's median calibration, device and noise properties (all shipped with cirq-google; no network)."""
    import cirq_google as cg
    from cirq_google.engine import virtual_engine_factory as vef

    cal = vef.load_median_device_calibration(processor)
    dev = vef.create_device_from_processor_id(processor)
    props = vef.load_device_noise_properties(processor)
    return cal, dev, props, cg.NoiseModelFromGoogleNoiseProperties(props)


def cal_value(cal, metric, key) -> float:
    return float(cal[metric][key][0])


def qubit_numbers(cal, q) -> dict:
    e0 = cal_value(cal, "single_qubit_p00_error", (q,))  # P(read 1 | prepared 0)
    e1 = cal_value(cal, "single_qubit_p11_error", (q,))  # P(read 0 | prepared 1)
    p1 = cal_value(cal, "single_qubit_rb_pauli_error_per_gate", (q,))
    return {"p00_error": e0, "p11_error": e1, "readout_error": (e0 + e1) / 2, "rb_pauli_error_1q": p1}


def pair_cz_error(cal, a, b) -> float:
    m = cal["two_qubit_parallel_cz_gate_xeb_pauli_error_per_cycle"]
    return float((m.get((a, b)) or m.get((b, a)))[0])


def readout_channel(e0: float, e1: float):
    import cirq

    K0 = np.diag([math.sqrt(1 - e0), math.sqrt(1 - e1)])
    K1 = np.array([[0.0, math.sqrt(e1)], [0.0, 0.0]])  # 1 -> 0
    K2 = np.array([[0.0, 0.0], [math.sqrt(e0), 0.0]])  # 0 -> 1
    return cirq.KrausChannel([K0, K1, K2])


def cirq_block(label: str, qa, qb, measure: bool = True):
    """Qiskit's 3-CZ synthesis, through OpenQASM 2, into Cirq on qa (the pair's first qubit) and qb; runs merged."""
    import cirq
    import qiskit.qasm2
    from cirq.contrib.qasm_import import circuit_from_qasm

    from .simulator import pair_block

    c = circuit_from_qasm(qiskit.qasm2.dumps(pair_block(label)))
    c = c.transform_qubits({cirq.NamedQubit("q_0"): qa, cirq.NamedQubit("q_1"): qb})
    c = cirq.merge_single_qubit_gates_to_phxz(c)
    c = cirq.Circuit(c.all_operations(), strategy=cirq.InsertStrategy.EARLIEST)
    if measure:
        c.append(cirq.Moment(cirq.measure(qa, qb, key="m")))
    return c


def pauli_noise_model(cal, plant: dict | None = None):
    """Kickoff 36's arm 1 (plant None) or arm 2 (plant = {frozenset((qa, qb)): delta})."""
    import cirq

    plant = plant or {}

    class _M(cirq.NoiseModel):
        def noisy_moment(self, moment, system_qubits):
            if any(cirq.is_measurement(op) for op in moment):
                ro = []
                for op in moment:
                    for q in op.qubits:
                        n = qubit_numbers(cal, q)
                        ro.append(readout_channel(n["p00_error"], n["p11_error"]).on(q))
                return [cirq.Moment(ro), moment]
            out, planted, noise = [moment], [], []
            for op in moment:
                if len(op.qubits) == 2:
                    a, b = op.qubits
                    d = plant.get(frozenset((a, b)))
                    if d is not None:
                        planted += [cirq.rz(d).on(a), cirq.rz(d).on(b)]
                    noise.append(cirq.depolarize(pair_cz_error(cal, a, b), n_qubits=2).on(a, b))
                elif len(op.qubits) == 1:
                    noise.append(
                        cirq.depolarize(qubit_numbers(cal, op.qubits[0])["rb_pauli_error_1q"]).on(op.qubits[0])
                    )
            if planted:
                out.append(cirq.Moment(planted))
            if noise:
                out.append(cirq.Moment(noise))
            return out

    return _M()


def exact_distribution(circuit, model, qa, qb) -> np.ndarray:
    """[P(s)] for s = a + 2 b (a the first qubit's bit): the noisy circuit to the readout channel, then the diagonal."""
    import cirq

    nc = cirq.Circuit(model.noisy_moments(circuit, sorted([qa, qb]))) if model is not None else circuit
    nc = cirq.Circuit(m for m in nc if not any(cirq.is_measurement(op) for op in m))
    rho = cirq.DensityMatrixSimulator(dtype=np.complex128).simulate(nc, qubit_order=[qa, qb]).final_density_matrix
    p = np.clip(np.real(np.diag(rho)), 0, None)
    p = p / p.sum()
    # Cirq's order is qa most significant: index = 2 a + b; reorder to s = a + 2 b
    return np.array([p[0], p[2], p[1], p[3]])


class CirqSimBackend:
    """A simulator only: the QVM's published calibration as a noise model. spends nothing, needs no account."""

    name = "cirq_sim"
    spends = False

    def __init__(self, processor: str = PROCESSOR, noise: str = "pauli", plant: dict | None = None, seed: int = 36):
        if noise not in ("pauli", "qvm", "none"):
            raise ValueError("noise is pauli, qvm or none")
        self.processor = processor
        self.noise = noise
        self.seed = seed
        self.cal, self.device, self.props, self.qvm_model = load_qvm(processor)
        self.qubits = sorted(self.device.metadata.qubit_set)
        self.plant_by_index = plant or {}
        self._cache: dict = {}
        self._results: dict = {}

    def grid(self, i: int):
        return self.qubits[i]

    def _model(self):
        if self.noise == "none":
            return None
        if self.noise == "qvm":
            return self.qvm_model
        plant = {frozenset((self.grid(a), self.grid(b))): d for (a, b), d in self.plant_by_index.items()}
        return pauli_noise_model(self.cal, plant)

    def distribution(self, label: str, pair) -> np.ndarray:
        key = (label, tuple(pair))
        if key not in self._cache:
            qa, qb = self.grid(pair[0]), self.grid(pair[1])
            self._cache[key] = exact_distribution(cirq_block(label, qa, qb), self._model(), qa, qb)
        return self._cache[key]

    def target(self) -> Target:
        idx = {q: i for i, q in enumerate(self.qubits)}
        m = self.cal["two_qubit_parallel_cz_gate_xeb_pauli_error_per_cycle"]
        figs, cmap = {}, []
        for (a, b), v in m.items():
            key = tuple(sorted((idx[a], idx[b])))
            if key in figs:
                continue
            ro = (qubit_numbers(self.cal, a)["readout_error"], qubit_numbers(self.cal, b)["readout_error"])
            if idx[a] > idx[b]:
                ro = ro[::-1]
            err = float(v[0])
            figs[key] = PairFigures(key, err, ro, err + ro[0] + ro[1], {"calibration": "QVM median"})
            cmap.append(key)
        return Target(
            "cirq_sim",
            self.processor,
            len(self.qubits),
            cmap,
            "cz",
            figs,
            None,
            notes=["a simulation of a published noise model; not a measurement of any device"],
        )

    def estimate(self, job: MapJob) -> Estimate:
        return Estimate(0.0, "s", "local simulation; nothing is spent")

    def submit(self, job: MapJob) -> JobHandle:
        outcomes = []
        for pos in job.active_positions:
            label = job.order[pos - 1]
            o = np.zeros((len(job.pairs), 4), dtype=np.int64)
            for i, p in enumerate(job.pairs):
                rng = np.random.default_rng(np.random.SeedSequence(self.seed, spawn_key=(pos, i)))
                o[i] = rng.multinomial(job.shots, self.distribution(label, p))
            outcomes.append(o)
        hid = f"cirq-{job.job_hash(self.name, self.processor)[:12]}-{len(self._results)}"
        handle = JobHandle.for_job(self.name, self.processor, [hid], job)
        self._results[hid] = MapCounts(
            handle.pairs,
            handle.order,
            job.shots,
            outcomes,
            {"provider": "cirq_sim (simulation only)", "noise": self.noise, "utc": utc_now()},
        )
        return handle

    def fetch(self, handle: JobHandle) -> MapCounts:
        return self._results[handle.job_ids[0]]
