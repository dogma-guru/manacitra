# Copyright 2026 Anish Patel
# SPDX-License-Identifier: Apache-2.0
"""The simulator backend: always available, spends nothing, needs no account.

Each pair is simulated on its own as an exact two-qubit density matrix (there is no crosstalk in the model, so this is
exact under it), with Qiskit Aer's density-matrix method when qiskit-aer is installed and plain numpy otherwise; the
two engines give the same distribution. Shots are then drawn from that distribution with numpy, one sub-seed per
circuit position and pair, so every run is reproducible.

The noise model, per pair:

* after each CZ: an optional coherent Z over-rotation by delta on both qubits (the planted map of Kickoff 36), then
  two-qubit depolarizing noise with probability p2;
* after each single-qubit layer (the single-qubit gates between two CZs, merged): single-qubit depolarizing noise with
  probability p1 on that qubit;
* at readout: each qubit reads 1 for 0 with probability e0, and 0 for 1 with probability e1.

The published score of a simulated pair is x = p2 + both readout errors, readout error = (e0 + e1) / 2 (Kickoff 36).
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field, replace
from functools import lru_cache

import numpy as np

from ..circuits import CIRCUITS, block
from .base import Estimate, JobHandle, MapCounts, MapJob, PairFigures, Target, utc_now

I2 = np.eye(2, dtype=complex)
PAULI = [
    I2,
    np.array([[0, 1], [1, 0]], complex),
    np.array([[0, -1j], [1j, 0]], complex),
    np.diag([1.0, -1.0]).astype(complex),
]
CZ = np.diag([1, 1, 1, -1]).astype(complex)


@dataclass(frozen=True)
class PairNoise:
    p2: float = 0.0  # two-qubit depolarizing after each CZ
    p1: tuple[float, float] = (0.0, 0.0)  # single-qubit depolarizing per merged layer, (first qubit, second)
    readout: tuple[tuple[float, float], tuple[float, float]] = ((0.0, 0.0), (0.0, 0.0))  # ((e0, e1) first, second)
    delta: float = 0.0  # coherent Z over-rotation after each CZ, radians, both qubits

    @property
    def readout_error(self) -> tuple[float, float]:
        return tuple((e0 + e1) / 2 for e0, e1 in self.readout)

    @property
    def x(self) -> float:
        return self.p2 + sum(self.readout_error)


@dataclass
class NoiseModel:
    pairs: dict[tuple[int, int], PairNoise] = field(default_factory=dict)
    default: PairNoise = field(default_factory=PairNoise)

    def of(self, pair) -> PairNoise:
        return self.pairs.get(tuple(pair), self.default)

    @classmethod
    def random(cls, pairs, seed: int = 0, p2=(0.002, 0.012), p1=(0.0002, 0.0008), readout=(0.004, 0.03)) -> NoiseModel:
        """Per-pair figures drawn uniformly in the given ranges: a stand-in for a provider's published calibration."""
        rng = np.random.default_rng(seed)
        out = {}
        for p in pairs:
            e = [(float(rng.uniform(*readout)), float(rng.uniform(*readout))) for _ in range(2)]
            out[tuple(p)] = PairNoise(
                p2=float(rng.uniform(*p2)), p1=(float(rng.uniform(*p1)), float(rng.uniform(*p1))), readout=(e[0], e[1])
            )
        return cls(out)

    def planted(self, sigma: float, seed: int = 3602) -> tuple[NoiseModel, dict]:
        """This model plus a per-pair Z over-rotation delta_i ~ N(0, sigma), in pair order (Kickoff 36's arm 2)."""
        rng = np.random.default_rng(seed)
        deltas = {p: float(rng.normal(0.0, sigma)) for p in self.pairs}
        return NoiseModel({p: replace(n, delta=deltas[p]) for p, n in self.pairs.items()}, self.default), deltas

    def permuted(self, perm) -> NoiseModel:
        """Pair i takes the noise of pair perm[i] (Kickoff 36's scrambled days)."""
        ps = list(self.pairs)
        return NoiseModel({ps[i]: self.pairs[ps[j]] for i, j in enumerate(perm)}, self.default)


# --------------------------------------------------------------------------- circuits as layers
def pair_block(label: str):
    """The two-qubit circuit of any label the package runs: 'A no', 'B off', ..., 'R1'..'R8', 'CAL 01'."""
    from qiskit import QuantumCircuit

    if label.startswith("CAL"):
        s = ["00", "01", "10", "11"].index(label.split()[1])
        qc = QuantumCircuit(2)
        if s & 1:
            qc.x(0)
        if s & 2:
            qc.x(1)
        return qc
    if label.startswith("R"):
        from ..workload import workload_block

        return workload_block(_units()[int(label[1:]) - 1])
    return block(label)


@lru_cache(maxsize=1)
def _units():
    from ..workload import draw_unitaries

    return draw_unitaries()


@lru_cache(maxsize=64)
def layers(label: str) -> tuple:
    """The block as alternating single-qubit layers (U on the first qubit, U on the second) and 'cz'."""
    from qiskit.quantum_info import Operator

    qc = pair_block(label)
    out, cur = [], [I2.copy(), I2.copy()]
    for ins in qc.data:
        qs = [qc.find_bit(q).index for q in ins.qubits]
        if ins.operation.name == "cz":
            out += [(cur[0], cur[1]), "cz"]
            cur = [I2.copy(), I2.copy()]
        elif ins.operation.name in ("barrier", "measure"):
            continue
        else:
            if len(qs) != 1:
                raise ValueError(f"unexpected two-qubit gate {ins.operation.name} in {label}")
            cur[qs[0]] = Operator(ins.operation).data @ cur[qs[0]]
    out.append((cur[0], cur[1]))
    return tuple(out)


def _is_identity(u: np.ndarray) -> bool:
    return abs(abs(np.trace(u)) - 2) < 1e-12


def _on(u0: np.ndarray, u1: np.ndarray) -> np.ndarray:
    """Qiskit order: the first qubit is the least significant."""
    return np.kron(u1, u0)


def _depolarize_1q(rho, p, qubit):
    if p == 0:
        return rho
    out = (1 - p) * rho
    for P in PAULI[1:]:
        K = _on(P, I2) if qubit == 0 else _on(I2, P)
        out = out + (p / 3) * K @ rho @ K.conj().T
    return out


def _depolarize_2q(rho, p):
    if p == 0:
        return rho
    out = (1 - p) * rho
    for P0, P1 in itertools.product(PAULI, PAULI):
        if P0 is PAULI[0] and P1 is PAULI[0]:
            continue
        K = _on(P0, P1)
        out = out + (p / 15) * K @ rho @ K.conj().T
    return out


def _rz(t):
    return np.diag([np.exp(-0.5j * t), np.exp(0.5j * t)])


def readout_matrix(noise: PairNoise) -> np.ndarray:
    """M[measured s, true s] for s = a + 2 b."""
    m = []
    for e0, e1 in noise.readout:
        m.append(np.array([[1 - e0, e1], [e0, 1 - e1]]))
    return np.kron(m[1], m[0])


def exact_distribution_numpy(label: str, noise: PairNoise) -> np.ndarray:
    rho = np.zeros((4, 4), complex)
    rho[0, 0] = 1
    for item in layers(label):
        if isinstance(item, str):
            rho = CZ @ rho @ CZ
            if noise.delta:
                U = _on(_rz(noise.delta), _rz(noise.delta))
                rho = U @ rho @ U.conj().T
            rho = _depolarize_2q(rho, noise.p2)
        else:
            U = _on(item[0], item[1])
            rho = U @ rho @ U.conj().T
            for q in (0, 1):
                if not _is_identity(item[q]):
                    rho = _depolarize_1q(rho, noise.p1[q], q)
    p = np.clip(np.real(np.diag(rho)), 0, None)
    return readout_matrix(noise) @ (p / p.sum())


def exact_distribution_aer(label: str, noise: PairNoise) -> np.ndarray:
    from qiskit import QuantumCircuit
    from qiskit.circuit.library import UnitaryGate
    from qiskit.quantum_info import Kraus
    from qiskit_aer import AerSimulator

    def kraus_2q(p):
        ops = [np.sqrt(1 - p) * np.eye(4)] + [
            np.sqrt(p / 15) * _on(a, b)
            for a, b in itertools.product(PAULI, PAULI)
            if not (a is PAULI[0] and b is PAULI[0])
        ]
        return Kraus(ops)

    def kraus_1q(p):
        return Kraus([np.sqrt(1 - p) * I2] + [np.sqrt(p / 3) * P for P in PAULI[1:]])

    qc = QuantumCircuit(2)
    for item in layers(label):
        if isinstance(item, str):
            qc.cz(0, 1)
            if noise.delta:
                qc.rz(noise.delta, 0)
                qc.rz(noise.delta, 1)
            if noise.p2:
                qc.append(kraus_2q(noise.p2), [0, 1])
        else:
            for q in (0, 1):
                if not _is_identity(item[q]):
                    qc.append(UnitaryGate(item[q]), [q])
                    if noise.p1[q]:
                        qc.append(kraus_1q(noise.p1[q]), [q])
    qc.save_probabilities()
    res = AerSimulator(method="density_matrix").run(qc).result()
    p = np.clip(np.asarray(res.data(0)["probabilities"], float), 0, None)
    return readout_matrix(noise) @ (p / p.sum())


def aer_available() -> bool:
    try:
        import qiskit_aer  # noqa: F401

        return True
    except ImportError:
        return False


class SimulatorBackend:
    """Runs a MapJob on the noise model at once; submit() returns a handle and fetch() the counts."""

    name = "simulator"
    spends = False

    def __init__(
        self,
        noise: NoiseModel | None = None,
        seed: int = 0,
        engine: str = "auto",
        processor: str = "simulated",
        coupling_map=None,
    ):
        if engine not in ("auto", "aer", "numpy"):
            raise ValueError("engine is auto, aer or numpy")
        self.noise = noise or NoiseModel()
        self.seed = seed
        self.engine = ("aer" if aer_available() else "numpy") if engine == "auto" else engine
        self.processor = processor
        self.coupling_map = coupling_map
        self._results: dict[str, MapCounts] = {}
        self._cache: dict = {}

    def distribution(self, label: str, pair) -> np.ndarray:
        n = self.noise.of(pair)
        key = (label, n)
        if key not in self._cache:
            f = exact_distribution_aer if self.engine == "aer" else exact_distribution_numpy
            self._cache[key] = f(label, n)
        return self._cache[key]

    def target(self) -> Target:
        cmap = [tuple(e) for e in (self.coupling_map or self.noise.pairs.keys())]
        figs = {}
        for p, n in self.noise.pairs.items():
            key = (min(p), max(p))
            figs[key] = PairFigures(key, n.p2, n.readout_error, n.x, {"simulated": True})
        n_q = 1 + max((q for e in cmap for q in e), default=-1)
        return Target(
            "simulator",
            self.processor,
            n_q,
            cmap,
            "cz",
            figs or None,
            None,
            notes=["simulated figures; x = p2 + both readout errors"],
        )

    def estimate(self, job: MapJob) -> Estimate:
        return Estimate(0.0, "s", "local simulation; nothing is spent")

    def run(self, job: MapJob) -> MapCounts:
        outcomes = []
        for pos in job.active_positions:
            label = job.order[pos - 1]
            o = np.zeros((len(job.pairs), 4), dtype=np.int64)
            for i, p in enumerate(job.pairs):
                rng = np.random.default_rng(np.random.SeedSequence(self.seed, spawn_key=(pos, i)))
                o[i] = rng.multinomial(job.shots, self.distribution(label, p))
            outcomes.append(o)
        order = [job.order[p - 1] for p in job.active_positions]
        return MapCounts(
            job.pairs,
            order,
            job.shots,
            outcomes,
            {"provider": "simulator", "engine": self.engine, "seed": self.seed, "utc": utc_now()},
        )

    def submit(self, job: MapJob) -> JobHandle:
        handle_id = f"sim-{job.job_hash(self.name, self.processor)[:12]}-{len(self._results)}"
        self._results[handle_id] = self.run(job)
        return JobHandle.for_job(self.name, self.processor, [handle_id], job)

    def fetch(self, handle: JobHandle) -> MapCounts:
        return self._results[handle.job_ids[0]]


def gap_sensitivity(circuit: str = "A", delta: float = 1e-3) -> float:
    """dk/d(delta) of the planted over-rotation, noise-free (Kickoff 36 found about -4.0 per rad for A)."""
    k = []
    for d in (-delta, delta):
        n = PairNoise(delta=d)
        p_off = exact_distribution_numpy(f"{circuit} off", n)[3]
        p_no = exact_distribution_numpy(f"{circuit} no", n)[3]
        k.append((p_off - p_no) / (CIRCUITS[circuit].ideal_off - CIRCUITS[circuit].ideal_no))
    return (k[1] - k[0]) / (2 * delta)
