# Manacitra

**Manacitra makes a map of a quantum processor's qubit pairs: which pairs keep a small, known difference and which lose it, and it uses the map to choose pairs for a job.** The name is the Sanskrit *māna* (measure) and *citra* (picture): *mānacitra*, the Hindi word for a map. The name is measure-picture, map; it says nothing about minds.

## What it does

Manacitra runs two short circuits on every pair of a processor at once. The two circuits use the same three two-qubit gates and differ only in single-qubit angles, so an exact model knows the difference between their outcomes in advance: 0.037765 for the main circuit. Each pair keeps some share of that difference, its **kept share** k, and the shares of all the pairs form the map. Three rules, fixed before any data was taken, then say whether the map is real (it repeats and carries over to a second circuit), whether the provider's published error rates already contain it, and whether choosing pairs by it does better on unrelated work. The tool then picks the pairs that kept the most, and your job runs on them.

It maps pairs. It does not rank machines.

## The idea in five pictures

### 1. The kept share

![Two circuits on one pair of qubits, identical except for their single-qubit gates, shown as two rows of boxes joined by the same three CZ gates. Beside them, three pairs of dots on a P(11) axis: the exact model's outcomes, 0.962 without the offset and 1.000 with it, a gap of 0.038; ibm_fez pair 106-107, 0.923 and 0.963, a gap of 0.040, k = 1.06; ibm_fez pair 20-21, 0.824 and 0.833, a gap of 0.008, k = 0.22.](docs/diagrams/kept-share.svg)

The two circuits encode a four-site Hamiltonian in two qubits; the offset makes the transfer from 00 to 11 exact, so the model's P(11) moves from 0.962 to 1.000. On ibm_fez on 5 October 2026, pair [106, 107] moved by 0.040, slightly more than the model's 0.038 (k = 1.06). Pair [20, 21] moved by 0.008 (k = 0.22): the same gates, the same difference in angles, and most of the difference was gone. Both pairs ran in the same job, with 32,000 shots per variant each. (A PNG version of every diagram sits beside the SVG in `docs/diagrams/`.)

### 2. The map

![ibm_fez's heavy-hex coupling map with 27 pairs drawn as thick segments shaded from light blue (kept least, k = 0.22) to dark blue (kept most, k = 1.06), and other couplers in light grey. Beside it, a smaller copy of the same map with the same 27 pairs shaded by IBM's published error score, from light (highest error, 0.021) to dark (lowest error, 0.011). The two shadings differ pair by pair.](docs/diagrams/chip-map.svg)

The left map is ibm_fez's 27 pairs from Kickoff 31 (5 October 2026, 12:37 UTC), each coloured by its kept share. The small map on the right colours the same pairs by the published score x (the pair's two-qubit error plus both qubits' readout errors, as IBM reported them at submission). Dark means better on both. The two pictures order the pairs differently: across these 27 pairs, k and x correlate at r = −0.18.

### 3. The pipeline

![Four boxes in a row joined by arrows: Map (in: 16 short circuits on every pair at once; out: k per pair), Verdict (in: k from two circuits, split halves, published x; out: NOISE, REDUNDANT, DIAGNOSTIC or NOT SETTLED), Pick (in: the map; out: the n pairs that kept the most), Run (in: your job on the picked pairs). A dashed note above the Map box says that in the author's use the rules and predictions are sealed before the map job is sent.](docs/diagrams/pipeline.svg)

Map, then verdict, then pick, then run. The verdict decides whether the map is worth using at all: a map that does not repeat is NOISE, and a map the published figures already explain is REDUNDANT. In the author's own use, the rules and a set of predictions were written down and hashed before each job was sent, so no verdict was chosen after seeing the data.

### 4. The payoff

![A scatter of 27 ibm_fez pairs: the kept share measured about two hours earlier on the horizontal axis, and fidelity on eight random two-qubit circuits on the vertical axis. The 8 pairs with the highest kept share are filled blue; the 8 with the lowest published error are ringed in orange; some pairs carry both. Dashed lines mark each pick's mean: error 0.0022 for the map's pick and 0.0034 for the published pick. The title reads: choosing by the map, 35.6% less error than choosing by the published rates.](docs/diagrams/payoff.svg)

On ibm_fez on 5 October 2026, the map measured at 13:17 UTC chose 8 pairs, and the published error rates chose another 8. At 15:20 UTC all 27 pairs ran eight random circuits, unrelated to the map, with nine CZ gates each. The map's 8 pairs had a mean error of 0.0022 against 0.0034 for the published pick: 35.6% less. The absolute numbers are small, because every pair's fidelity was above 0.98.

### 5. How to check a sealed prediction

![A timeline of four steps. 1, seal and post the hash (manacitra seal): shows the file existed then, without showing what it says. 2, run the job: the file stays as it was. 3, reveal the salt (manacitra reveal): publishes the file and its salt. 4, anyone verifies (manacitra verify): a match shows the predictions came before the results.](docs/diagrams/sealed-prediction.svg)

This one is for a stranger who wants to know whether the predictions came before the results. `manacitra seal` commits to a file with a salted SHA-256 hash, which is posted somewhere the producer cannot edit; after the run, `manacitra reveal` publishes the salt, and `manacitra verify` lets anyone check that the file is the one committed to. Once the repository is public, a CI workflow also signs every commit record and every data file with Sigstore's keyless signing, which records who signed and when in a public log ([`docs/index.md`](docs/index.md#9-sealing-and-signing)).

## Install and try it

Manacitra needs Python 3.11 or later. It is not yet on PyPI; install it from a clone:

```bash
git clone https://github.com/dogmaguru/manacitra.git
cd manacitra
pip install -e ".[aer]"
```

Then, on the simulator, with no account:

```python
from manacitra.backends.base import MapJob
from manacitra.backends.simulator import NoiseModel, SimulatorBackend
from manacitra.layout import pick_pairs
from manacitra.verdicts import analyse_map

pairs = [(2 * i, 2 * i + 1) for i in range(27)]
noise, _ = NoiseModel.random(pairs, seed=1).planted(sigma=0.03)  # a hidden per-pair map
sim = SimulatorBackend(noise, seed=7)
counts = sim.fetch(sim.submit(MapJob(pairs)))
result = analyse_map(counts.p11(), counts.order, x=sim.target().x_of(pairs))
print(result["verdict"]["verdict"], [pairs[i] for i in pick_pairs(result["kA"], 8)])
```

It prints `DIAGNOSTIC` and the eight pairs that kept the most. Three longer examples are in `examples/`: the simulator end to end, the ibm_fez numbers reproduced from the archived counts, and the payoff choice.

Extras: `[ibm]` for IBM Quantum, `[aer]` for Qiskit Aer, `[docs]` for the diagrams; `[openquantum]` and `[cirq]` are experimental. The command line is `manacitra map | pick | verdict | persist | report`, and it is a dry run unless `--submit` is given.

**Before anything is sent to a provider:** the estimate and the ledger entry are printed; a job already sent once is refused unless `--allow-resubmit` is given (and that is logged); on IBM the usage is read and the job refused above a cap (540 s of the 600 s window by default); and any transpiled circuit without exactly three CZ on every pair is refused. Credentials come only from each provider's own saved account, never from this repository.

## What it has shown, and what it has not

All four findings come from runs on 5 October 2026. The counts are in `data/`, and every statistic below reproduces from them (`pytest tests/test_reproduction.py`).

1. **Each pair keeps its own share, and the share repeats** (Kickoff 31; ibm_fez at 12:37 UTC, ibm_kingston at 12:38 UTC; 27 pairs each). Within one job, the map from one half of the circuits correlates with the map from the other half at r = 0.87 (ibm_fez) and 0.90 (ibm_kingston). It carries over to a second circuit with a different gap and its own reference: r = 0.82 and 0.89. The published score does not account for it (r = −0.18 and −0.05). Verdict on both: DIAGNOSTIC.
2. **The share belongs to the pair's own gate, not to its neighbours** (Kickoff 32; ibm_fez at 13:17 UTC, ibm_kingston at 13:23 UTC). The six pairs that kept the most and the six that kept the least were run again, once with all 27 pairs active and once with no two active pairs coupled. The gap between the two groups did not close when the neighbours were idle: the closed fraction was 0.01 on ibm_fez (90% interval −0.21 to 0.21) and 0.03 on ibm_kingston (−0.09 to 0.16).
3. **On ibm_fez, choosing pairs by the map gave 35.6% less error on unrelated random circuits than choosing by the published error rates** (Kickoff 33; 15:20 UTC). Gain in fidelity G = +0.0012, 90% interval +0.0004 to +0.0021; verdict USEFUL. **On ibm_kingston (15:22 UTC), 16% less, not statistically settled**: G = +0.0004 (+0.0001 to +0.0008), but the map's partial correlation with the workload, after removing the published score, was 0.29 (p = 0.073), short of the rule's 0.3 and p < 0.05. Verdict: NOT SETTLED.
4. **The rule can say no** (Kickoff 36, a simulation of the noise model Cirq publishes for Google's willow_pink, run on a laptop; not a measurement of any device). When every difference between pairs came from the published figures, the rule called the map NOISE: those differences were too small to repeat above shot noise. When a per-pair error was planted outside the published figures, the rule found it (DIAGNOSTIC).

**What it has not shown:**

- **How long a map lasts.** On ibm_fez, the map from 02:24 UTC still correlated at r = 0.68 with the map ten hours later, across a recalibration. A three-day test of the whole chip is running (Kickoff 35). The same simulation found that the persistence rule, at that test's shot count, could not tell a fixed map from a scrambled one; the rule was amended (A1) to set a reliability floor, and Manacitra reports both forms.
- **Whether the same property exists on a second vendor's chip.** A run on a Rigetti processor is under way (Kickoff 34b). Its adapter is included as experimental, and nothing here claims the property beyond the two IBM processors.

What would discredit the map: a NOISE verdict (it does not repeat), a REDUNDANT verdict (the published figures already carry it), NOT USEFUL (it picks no better pairs), or FADES (it does not last long enough to plan by).

## Limits

- **One circuit family.** Every map comes from one encoded four-site Hamiltonian, at two strengths of its diagonal coupling (circuits A and B). Other circuits might order the pairs differently.
- **Two processors, one day.** The hardware results are from ibm_fez and ibm_kingston on 5 October 2026.
- **Small absolute differences.** The gap is 0.038 in P(11), and the payoff is about a tenth of a percentage point of fidelity on the random workload.
- **No claim about any device's design.** A pair's kept share is a measurement of what it did with these circuits; it says nothing about why, or about how the processor was built.

The long version, including the three rules with their thresholds and how to reproduce every number here, is in [`docs/index.md`](docs/index.md).

## How to cite

Please cite the software and, if you use them, the data, using [`CITATION.cff`](CITATION.cff):

> Patel, A. (2026). *Manacitra: a map of a quantum processor's qubit pairs* (version 0.1.0) [Software and data]. https://github.com/dogmaguru/manacitra

## Licence

The code is licensed under the Apache License 2.0 ([`LICENSE`](LICENSE), [`NOTICE`](NOTICE)). The data in `data/` and the documentation in `docs/` are licensed under Creative Commons Attribution 4.0 ([`data/LICENSE`](data/LICENSE), [`docs/LICENSE`](docs/LICENSE)). The copyright holder is Dogma LLC (Dogma Guru).

Manacitra is developed by Anish Patel and published by Dogma Guru.
