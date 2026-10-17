# Manacitra

[![DOI](https://zenodo.org/badge/1406355471.svg)](https://doi.org/10.5281/zenodo.23228518)

**Manacitra makes a map of a quantum processor's qubit pairs: which pairs keep a small, known difference and which lose it, and it uses the map to choose pairs for a job.** The name is the Sanskrit *māna* (measure) and *citra* (picture): *mānacitra*, the Hindi word for a map. The name is measure-picture, map; it says nothing about minds.

**Contents:** [Latest finding](#latest-finding-two-frequencies-on-one-qubit) · [What it does](#what-it-does) · [Findings](#findings) · [Limits](#limits) · [The idea](#the-idea) · [Install and try it](#install-and-try-it) · [Reproducing the numbers](#reproducing-the-numbers) · [Documentation](#documentation) · [How to cite](#how-to-cite) · [Support](#support) · [Licence](#licence)

## Latest finding: two frequencies on one qubit

Qubit 143 of ibm_fez, the qubit that waited in the circuits of findings 13 to 18 and 21, was measured at 64 waits in two quadratures under a rule whose SHA-256 was posted before the job ([finding 28](docs/findings.md#finding-28)). Its Ramsey fringe is two fixed frequencies about 90 kHz apart at unequal weight, not one line decaying. Within the three-minute job the weight of the upper line moved from about 0.45 to 0.27, which the rule did not assume and the finding reports as what the counts show. No cause is named. Released as 0.8.0 on 17 October 2026.

## What it does

Manacitra runs two short circuits on a set of non-overlapping qubit pairs at once (27 in the published runs); every coupler on a chip can be covered in a few rounds. The two circuits use the same three two-qubit gates and differ only in single-qubit angles, so an exact model knows the difference between their outcomes in advance: 0.037765 for the main circuit. Each pair keeps some share of that difference, its **kept share** k, and the shares of all the pairs form the map. Three rules, fixed before any data was taken (according to the author's dated records, which are not part of this release), then say whether the map is real (it repeats and carries over to a second circuit), whether the provider's published error rates already contain it, and whether choosing pairs by it does better on unrelated work. `manacitra pick` then ranks the pairs from a map by how close each pair's kept share is to the ideal of 1, |1 − k| (`--by kept-share-highest` gives the highest-first rule Kickoff 33 used), or, with `--by level`, by the plain level, which chose better pairs on the Rigetti processor where the kept share did not. It does not check the verdict (it warns when the verdict is not DIAGNOSTIC or MAP PRESENT), and Manacitra does not run your own job: you run it on the pairs you choose.

It maps pairs. It does not rank machines.

![ibm_fez's heavy-hex coupling map with 27 pairs drawn as segments shaded from light blue (kept least, k = 0.22) to dark blue (kept most, k = 1.06), each also drawn thicker the more it kept and numbered by its rank (1 = kept most), and other couplers in light grey. Beside it, a smaller copy of the same map with the same 27 pairs shaded by IBM's published error score, from light (highest error, 0.021) to dark (lowest error, 0.011). The two shadings differ pair by pair.](docs/diagrams/chip-map.svg)

The left map is ibm_fez's 27 pairs from Kickoff 31 (5 October 2026, 12:37 UTC), each coloured by its kept share. Each pair is also drawn thicker the more it kept, and numbered by its rank; every pair's k, x and ranks are in [a table](docs/diagrams/chip-map-table.md). The small map on the right colours the same pairs by the published score x (the pair's two-qubit error plus both qubits' readout errors, as IBM reported them at submission). Dark means better on both. The two pictures order the pairs differently: across these 27 pairs, k and x correlate at r = −0.18.

## Findings

Twenty-eight findings, from runs on 5 to 16 October 2026. Here the findings on one thread share a row, and each number links to its finding; each is given in full, with its caveats, in [`docs/findings.md`](docs/findings.md), which also has [the full table](docs/findings.md#the-findings-in-one-table), one row per finding. What has *not* been shown is there too.

| thread | findings | where | where it stands | verdicts |
|---|---|---|---|---|
| The kept-share map on IBM processors | [1](docs/findings.md#finding-1), [7](docs/findings.md#finding-7) | ibm_fez, ibm_kingston | Each pair keeps its own share and the share repeats, on both processors; on ibm_fez a map of the whole chip held for two days. | DIAGNOSTIC on both; HOLDS over two days |
| The map on a second vendor's processor | [2](docs/findings.md#finding-2), [6](docs/findings.md#finding-6), [8](docs/findings.md#finding-8), [9](docs/findings.md#finding-9), [10](docs/findings.md#finding-10) | Rigetti Cepheus-1-108Q, through Open Quantum and through Amazon Braket | The map is present there too; with placement pinned it is DIAGNOSTIC and lasted a day, and through a route that records no placement a pair's level followed the program that measured it. | MAP PRESENT; PLACEMENT and ACTIVITY; PINNED and DIAGNOSTIC; HOLDS a day later |
| What the neighbours do not explain | [3](docs/findings.md#finding-3) | ibm_fez, ibm_kingston | The gap between the best and worst pairs persisted when their neighbours were idle. | THE GATE on both (not explained by the tested neighbours) |
| Choosing pairs by the map | [4](docs/findings.md#finding-4), [11](docs/findings.md#finding-11) | ibm_fez, ibm_kingston | On ibm_fez the map chose pairs with 35.6% less error than the published rates did, and reuse circuits it placed scored higher, mostly because its chains avoided one qubit. | USEFUL on ibm_fez, NOT SETTLED on ibm_kingston; USEFUL FOR REUSE |
| The rule can say no | [5](docs/findings.md#finding-5), [26](docs/findings.md#finding-26) | a simulation of willow_pink's published noise; ibm_fez | Without a planted per-pair error a simulation's map read NOISE; on ibm_fez a draw rule refused to draw on the published readout (Kickoff 60), and a direct measurement showed that table did not describe sixteen qubits at that time. | NOISE without a planted map; PUBLISHED NOT READABLE |
| The collapse on 143 and 144, and the wait | [12](docs/findings.md#finding-12), [13](docs/findings.md#finding-13) | ibm_fez | A reuse circuit collapsed on chains around qubits 143 and 144; five explanations were set aside, and refocusing pulses restored the circuit, since 143 lost phase while it waited. | NOT SUPPORTED for the explanations tested; H_phase SUPPORTED; REFOCUSABLE |
| The check and its instrument | [14](docs/findings.md#finding-14), [15](docs/findings.md#finding-15), [16](docs/findings.md#finding-16), [17](docs/findings.md#finding-17), [18](docs/findings.md#finding-18), [19](docs/findings.md#finding-19), [20](docs/findings.md#finding-20), [21](docs/findings.md#finding-21) | ibm_fez, ibm_kingston | A qubit's Ramsey loss over the circuit's own wait predicts how a reuse-shaped circuit fares; with the neighbours active, 0.6.0's default, the check at +90° held on ibm_fez on two days and missed on one cell of four on ibm_kingston. | AGREE; DISAGREE on a second day; SUPPORTED and DIFFERENT; AGREE on new chains; DISAGREE on ibm_kingston |
| The check at the peak phase | [22](docs/findings.md#finding-22), [23](docs/findings.md#finding-23), [24](docs/findings.md#finding-24), [25](docs/findings.md#finding-25), [27](docs/findings.md#finding-27) | ibm_kingston, ibm_fez | Read at the active-neighbour Ramsey's loss maximum, the check predicted the wait test within ±0.15 on twelve of twelve cells over three runs on new chains, on two processors; its residual was not smaller than at +90° on every chain. | LARGE, NOT SETTLED and SMALL; AGREE in three runs; PEAK SMALLER and NOT SEPARATED |
| The fringe on 143: one line or two | [28](docs/findings.md#finding-28) | ibm_fez | Measured at every wait from 0 to 63 µs in two quadratures, 143's Ramsey fringe was two fixed frequencies about 90 kHz apart at unequal weight, not one line decaying; within the job the weight moved. | TWO FIXED FREQUENCIES |

What would discredit the map: a NOISE verdict (it does not repeat), a REDUNDANT verdict (the published figures already carry it), NOT USEFUL (it picks no better pairs), or FADES (it does not last long enough to plan by).

## Limits

- **One circuit family.** Every map comes from one encoded four-site Hamiltonian, at two strengths of its diagonal coupling (circuits A and B). Other circuits might order the pairs differently.
- **Three processors, three days.** The hardware results of findings 1 to 10 are from ibm_fez and ibm_kingston, and from Rigetti Cepheus-1-108Q through Open Quantum and through Amazon Braket, all on 5 to 7 October 2026.
- **One processor, one day, for the reuse findings.** Findings 11 to 13 are from one processor on one day, across three published calibration stamps.
- **One processor, one day, five qubits, for finding 14.** Finding 14 is from one job on ibm_fez on 11 October 2026, under one published calibration stamp.
- **One processor, one day, six waiting qubits, for findings 15 to 19.** Findings 15 to 19 are from five jobs on ibm_fez on 13 October 2026. From finding 15's calibration stamp to finding 19's submission no published T1, T2, readout, gate or CZ value changed; during finding 19's job, at 20:29:58 UTC, IBM published new readout errors on 154 qubits.
- **Two processors, three days, for the active-neighbour check.** On ibm_fez it has run on six waiting qubits, on 13 October 2026 (findings 16 to 19) and again on 15 October (finding 21); on ibm_kingston on four, on 14 October (finding 20). Which of two calibration stamps finding 20's job ran under is not known.
- **Two processors, two calibration days, for the check at the peak phase.** On ibm_kingston it has run on eight waiting qubits of new chains, under the daily calibrations of 14 and 15 October 2026 (findings 23 and 25), and on finding 20's three chains (finding 24); on ibm_fez on four, on 15 October (finding 27).
- **One qubit, one job, one day, for finding 28.** Finding 28 is from one job on ibm_fez on 16 October 2026, on qubit 143 alone, under one published calibration stamp.
- **Two routes to one processor.** The Rigetti findings through Open Quantum (2, 6) and through Amazon Braket (8 to 10) are from the same processor, but only the Braket route records where each pair ran. The difference between them is a difference between the two platforms' placement records, not between the vendors' machines.
- **Small absolute differences.** The gap is 0.038 in P(11), and the payoff is about a tenth of a percentage point of fidelity on the random workload.
- **No claim about any device's design.** A pair's kept share is a measurement of what it did with these circuits; it says nothing about why, or about how the processor was built.

## The idea

![Four boxes in a row joined by arrows: Map (in: 16 short circuits on a set of non-overlapping qubit pairs at once (27 in the published runs); every coupler on a chip can be covered in a few rounds; out: k per pair), Verdict (in: k from two circuits, split halves, published x; out: NOISE, REDUNDANT, DIAGNOSTIC, MAP PRESENT or NOT SETTLED), Pick (in: the map; out: the n pairs whose kept share is closest to the ideal of 1, ranked without checking the verdict), Run, drawn dashed (your own job, run by you on the picked pairs, not by Manacitra). A dashed note above the Map box says that, according to the author's dated records, which are not part of this release, the rules and predictions were sealed before each map job was sent.](docs/diagrams/pipeline.svg)

Map, then verdict, then pick, then run. The verdict says whether the map is worth using at all: a map that does not repeat is NOISE, and a map the published figures already explain is REDUNDANT. Manacitra computes the map and the verdict; `manacitra pick` ranks pairs from the map, and you run your own job. The method, in six pictures (the kept share, the map, the three checks, the pipeline, the payoff, and how to check a sealed prediction), is in [`docs/method.md`](docs/method.md). The published runs predate this release, so their sealed predictions rest on the author's dated records; from the first public release on, new commitments can be checked by anyone with `manacitra seal` and the signing log.

## Install and try it

Manacitra needs Python 3.11 or later. It is not yet on PyPI. There are two ways to install it.

**From a clone, editable: the route for reproducing the published numbers.** The archived dataset in `data/` comes
with the clone and is found automatically.

```bash
git clone https://github.com/dogma-guru/manacitra.git
cd manacitra
python -m venv .venv
source .venv/bin/activate      # on Windows: .venv\Scripts\activate
pip install -e ".[aer]"
```

To run the tests, and with them the reproductions, install `pip install -e ".[dev,aer]"` instead, which adds `pytest`.

**As a plain package**, installed with `pip install ".[aer]"` from a clone or with `pip install "git+https://github.com/dogma-guru/manacitra"`, Manacitra comes without the dataset. [`docs/install.md`](docs/install.md) says how to point it at a clone's `data/`, and covers the extras, the provider backends and the checks made before anything is sent.

Point an install at a clone's data with `manacitra --data /path/to/manacitra/data verdict ibm_fez/k31-map.json` or `MANACITRA_DATA`; `--data` goes before the subcommand. A provider backend sends nothing unless `--submit` is given; the simulator runs at once, on your machine, and sends nothing.

Then, on the simulator, with no account (paste this into a Python session):

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

A fourth, `examples/04_wait_test.py`, builds finding 13's Part B and the wait test for a backend and chain you name, as a dry run unless `--submit`; [`docs/reproduce.md`](docs/reproduce.md) says how to rerun them on hardware, and why a rerun is a new measurement. The check of findings 14 to 19, which predicts the wait test from the waiting qubit's Ramsey loss over the circuit's own wait (`manacitra.wait.build_wait_ramsey` and `predicted_fidelity`), now runs that Ramsey with the qubit's neighbours active, as they are in the circuit, by default; the idle-neighbour Ramsey, the 0.5.0 behaviour, remains with `neighbours="idle"`. The check at the peak phase is two jobs: `phase_sweep` builds the sweep, and `peak_check` builds the check from its counts, with the peak phase to record before the check runs; `readout_survey` and `readout_errors` measure every qubit's readout ([the method](docs/method.md#the-check-at-the-peak-phase)).

## Reproducing the numbers

```bash
pip install -e ".[dev,aer]"
pytest tests/test_reproduction.py tests/test_field_inventory.py   # every listed statistic, from the archived inputs
python examples/03_pick_pairs.py                                   # finding 4: both picks and the 35.6%
```

Every statistic listed in `tests/expected_fields.json` is recomputed from the archived inputs and compared at 10⁻⁶, with the exceptions named in [`docs/findings.md`](docs/findings.md); every measured number in the README and the findings is checked by a test. How each run was made is in [`docs/kickoffs.md`](docs/kickoffs.md), and the dataset, file by file, in [`data/README.md`](data/README.md).

## Documentation

- [`docs/findings.md`](docs/findings.md): the twenty-eight findings in full, with a table of all of them, what was known before them, and what has not been shown.
- [`docs/method.md`](docs/method.md): the method in six pictures.
- [`docs/kickoffs.md`](docs/kickoffs.md): how the results were made, and every run.
- [`docs/install.md`](docs/install.md): installing without a clone, the extras, the provider backends and their guards.
- [`docs/reproduce.md`](docs/reproduce.md): rerunning finding 13's Part B and the wait test on hardware, and why a rerun is a new measurement.
- [`docs/index.md`](docs/index.md): the long version: the circuits, the three rules with their thresholds, the backends, the safety guards, reproducing every number, and sealing and signing.
- [`data/README.md`](data/README.md): the dataset, its formats, and how to recompute the payoff.
- [`CONTRIBUTING.md`](CONTRIBUTING.md), [`SECURITY.md`](SECURITY.md), [`CHANGELOG.md`](CHANGELOG.md), and [`build-report.md`](build-report.md), the record of how this release was built and checked.

## How to cite

Please cite the software and, if you use them, the data, using [`CITATION.cff`](CITATION.cff):

> Patel, A. (2026). *Manacitra: a map of your qubits* (version 0.8.0) [Software and data]. Zenodo. https://doi.org/10.5281/zenodo.23228518. Source: https://github.com/dogma-guru/manacitra

That DOI is the concept DOI, which the badge at the top also points to: it always resolves to the latest version. Each version also has its own DOI, on its Zenodo record; to cite one version exactly, use that (version 0.7.0: [10.5281/zenodo.23408345](https://doi.org/10.5281/zenodo.23408345)).

## Support

Manacitra is free to use under its licences. If it is useful to you, you can support its work on [Patreon](https://www.patreon.com/DogmaGuru). Forks are welcome; pull requests are not accepted at this time, and questions go to Issues ([`CONTRIBUTING.md`](CONTRIBUTING.md)).

## Licence

The code is licensed under the Apache License 2.0 ([`LICENSE`](LICENSE), [`NOTICE`](NOTICE)). The data in `data/` and the documentation in `docs/` are licensed under Creative Commons Attribution 4.0 ([`data/LICENSE`](data/LICENSE), [`docs/LICENSE`](docs/LICENSE)). The copyright holder is Dogma LLC (Dogma Guru).

Manacitra is developed by Anish Patel and published by Dogma Guru.
