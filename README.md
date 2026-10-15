# Manacitra

[![DOI](https://zenodo.org/badge/1406355471.svg)](https://doi.org/10.5281/zenodo.23228518)

**Manacitra makes a map of a quantum processor's qubit pairs: which pairs keep a small, known difference and which lose it, and it uses the map to choose pairs for a job.** The name is the Sanskrit *māna* (measure) and *citra* (picture): *mānacitra*, the Hindi word for a map. The name is measure-picture, map; it says nothing about minds.

**Contents:** [Latest findings](#latest-findings-the-check-runs-with-the-neighbours-active) · [What it does](#what-it-does) · [Findings](#findings) · [Limits](#limits) · [The idea](#the-idea) · [Install and try it](#install-and-try-it) · [Reproducing the numbers](#reproducing-the-numbers) · [Documentation](#documentation) · [How to cite](#how-to-cite) · [Support](#support) · [Licence](#licence)

## Latest findings: the check runs with the neighbours active

Manacitra's check predicts how a reuse-shaped circuit will fare from one qubit's Ramsey loss over the circuit's own wait. Through 0.5.0 that Ramsey ran with the qubit's neighbours idle. Five runs on ibm_fez on 13 October 2026 found that what the neighbours do during the wait shifts the waiting qubit's phase (findings 16 to 18). They also found that a Ramsey in which the neighbours do what they do in the circuit, at the same times, predicted the wait test within ±0.15 on every informative cell of four chains it had never run on, where the idle-neighbour Ramsey missed by about 0.17 on three cells (finding 19).

The active-neighbour Ramsey is now the default (`build_wait_ramsey`). 0.5.0's instrument remains, with `neighbours="idle"`.

On a second day on ibm_fez, 15 October 2026, across a maintenance, the revised check ran again on the six chains of findings 16 to 19 and predicted the wait test within ±0.15 on all seven informative cells, where the idle-neighbour Ramsey would have missed on one (finding 21). On a second processor, ibm_kingston, it missed the margin on one informative cell of four, where the idle-neighbour Ramsey would have missed on all four (finding 20). Released as 0.6.0 on 15 October 2026.

- [15](docs/findings.md#finding-15): On a second day, the rule fixed in finding 14 held on three of four informative chains and failed on one, where the circuit did better than predicted.
- [16](docs/findings.md#finding-16): What a waiting qubit's neighbours do changed how much phase it lost: held in the excited state during the wait they added 0.25 to 0.35 of loss on both qubits tested, their readout alone added none, and finding 15's gap on 144 was gone 33 minutes later.
- [17](docs/findings.md#finding-17): With a known phase added to the waiting qubit, the wait test on 144 answered as if its offset differed from an idle-neighbour Ramsey's; on 143 the design was nearly blind.
- [18](docs/findings.md#finding-18): A full sweep of the known phase measured the difference: the wait test's offset differed from an idle-neighbour Ramsey's by −7.2° on 143 and −21.6° on 144, and an active-neighbour Ramsey sat closer to it on both.
- [19](docs/findings.md#finding-19): The revised check, with an active-neighbour Ramsey, predicted the wait test within ±0.15 on all five informative cells of four chains it had never run on, where the original check would have returned DISAGREE.
- [20](docs/findings.md#finding-20): On a second processor, ibm_kingston, the revised check missed on one of four informative cells, where the original check would have missed on all four; the active-neighbour Ramsey was the closer of the two on every informative cell.
- [21](docs/findings.md#finding-21): On a second day on ibm_fez, across a maintenance and under a new daily calibration, the revised check predicted the wait test within ±0.15 on all seven informative cells, where the original check would have missed on one.

### Why the default changed

In the circuit, the waiting qubit's neighbours are measured, reset and used again while it waits, and a Ramsey with them idle does not see what they do: held in |1⟩ they changed its loss by 0.25 to 0.35, and with a known phase added the circuit answered as if its offset differed from the idle-neighbour Ramsey's (findings 16 to 18). In findings 19 to 21 the idle-neighbour check would have missed the ±0.15 margin on eight cells, on both processors, and on every one of them the active-neighbour Ramsey sat closer to the circuit. The margin itself held on ibm_fez on two days, on twelve informative cells of twelve, and failed on ibm_kingston, on one cell of four (finding 20). The 0.5.0 instrument remains available, with `neighbours="idle"`.

## What it does

Manacitra runs two short circuits on a set of non-overlapping qubit pairs at once (27 in the published runs); every coupler on a chip can be covered in a few rounds. The two circuits use the same three two-qubit gates and differ only in single-qubit angles, so an exact model knows the difference between their outcomes in advance: 0.037765 for the main circuit. Each pair keeps some share of that difference, its **kept share** k, and the shares of all the pairs form the map. Three rules, fixed before any data was taken (according to the author's dated records, which are not part of this release), then say whether the map is real (it repeats and carries over to a second circuit), whether the provider's published error rates already contain it, and whether choosing pairs by it does better on unrelated work. `manacitra pick` then ranks the pairs from a map by how close each pair's kept share is to the ideal of 1, |1 − k| (`--by kept-share-highest` gives the highest-first rule Kickoff 33 used), or, with `--by level`, by the plain level, which chose better pairs on the Rigetti processor where the kept share did not. It does not check the verdict (it warns when the verdict is not DIAGNOSTIC or MAP PRESENT), and Manacitra does not run your own job: you run it on the pairs you choose.

It maps pairs. It does not rank machines.

![ibm_fez's heavy-hex coupling map with 27 pairs drawn as segments shaded from light blue (kept least, k = 0.22) to dark blue (kept most, k = 1.06), each also drawn thicker the more it kept and numbered by its rank (1 = kept most), and other couplers in light grey. Beside it, a smaller copy of the same map with the same 27 pairs shaded by IBM's published error score, from light (highest error, 0.021) to dark (lowest error, 0.011). The two shadings differ pair by pair.](docs/diagrams/chip-map.svg)

The left map is ibm_fez's 27 pairs from Kickoff 31 (5 October 2026, 12:37 UTC), each coloured by its kept share. Each pair is also drawn thicker the more it kept, and numbered by its rank; every pair's k, x and ranks are in [a table](docs/diagrams/chip-map-table.md). The small map on the right colours the same pairs by the published score x (the pair's two-qubit error plus both qubits' readout errors, as IBM reported them at submission). Dark means better on both. The two pictures order the pairs differently: across these 27 pairs, k and x correlate at r = −0.18.

## Findings

Twenty-one findings, from runs on 5 to 15 October 2026. Each is given in full, with its caveats, in [`docs/findings.md`](docs/findings.md); the number links to it. What has *not* been shown is there too.

| # | finding | where | kickoff, 2026 | verdict |
|---|---|---|---|---|
| [1](docs/findings.md#finding-1) | Each pair keeps its own share, and the share repeats | ibm_fez, ibm_kingston | 31, 5 Oct | DIAGNOSTIC on both |
| [2](docs/findings.md#finding-2) | The map exists on a second vendor's chip, within one job | Rigetti Cepheus-1-108Q, through Open Quantum | 34b, 5 Oct | MAP PRESENT |
| [3](docs/findings.md#finding-3) | The gap between the best and worst pairs persisted when their neighbours were idle | ibm_fez, ibm_kingston | 32, 5 Oct | THE GATE on both (not explained by the tested neighbours) |
| [4](docs/findings.md#finding-4) | On ibm_fez, choosing pairs by the map gave 35.6% less error on unrelated random circuits than choosing by the published error rates | ibm_fez, ibm_kingston | 33, 5 Oct | USEFUL on ibm_fez (G = +0.0012 in fidelity); NOT SETTLED on ibm_kingston |
| [5](docs/findings.md#finding-5) | The rule can say no | a simulation of willow_pink's published noise | 36, 5 Oct | NOISE without a planted map; DIAGNOSTIC with one |
| [6](docs/findings.md#finding-6) | On the Rigetti processor, a pair's level depends on the program that measures it, not on the hour | Rigetti Cepheus-1-108Q, through Open Quantum | 37, 38, 6 Oct | PLACEMENT; ACTIVITY |
| [7](docs/findings.md#finding-7) | On ibm_fez, a map of the whole chip held for two days | ibm_fez, all 176 coupled pairs | 35, 5 to 7 Oct | HOLDS over two days |
| [8](docs/findings.md#finding-8) | On the Rigetti processor, with placement pinned, the map is DIAGNOSTIC | Rigetti Cepheus-1-108Q, through Amazon Braket | 40, 6 Oct | PINNED; DIAGNOSTIC; payoff NOT SETTLED |
| [9](docs/findings.md#finding-9) | The pinned Rigetti map lasted a day, and the day-old level chose better pairs | Rigetti Cepheus-1-108Q, through Amazon Braket | 41, 7 Oct | HOLDS; the level USEFUL; the kept share NOT SETTLED |
| [10](docs/findings.md#finding-10) | On the Rigetti processor, a pair's response to a particular program repeats a day later, and a smooth shift of the offset does not describe it | Rigetti Cepheus-1-108Q, through Amazon Braket | 42, 6 to 7 Oct | SPREAD, MIXED, DOES NOT; the per-program pattern HOLDS a day later |
| [11](docs/findings.md#finding-11) | On ibm_fez, reuse circuits placed by the map scored higher than Qiskit's calibration placement, mostly because the map's chains avoided one qubit | ibm_fez | 43, 10 Oct | USEFUL FOR REUSE (G = +0.2246 in fidelity), mostly from avoiding one qubit; the map's own verdict NOT SETTLED |
| [12](docs/findings.md#finding-12) | On ibm_fez, a reuse circuit collapsed on chains around qubits 143 and 144, and five explanations for it were tested and set aside | ibm_fez | 44, 45, 46, 10 Oct | NOT SUPPORTED for one retirement, repeated retirements and a neighbour's retirement; idle loss SUPPORTED by its rule but not tracking the collapse |
| [13](docs/findings.md#finding-13) | Qubit 143 lost phase while it waited in superposition, IBM's echo-measured T2 does not show that kind of loss, and refocusing pulses restored the circuit | ibm_fez | 47, 10 Oct | H_phase SUPPORTED; the loss on 143 REFOCUSABLE |
| [14](docs/findings.md#finding-14) | On ibm_fez, a qubit's Ramsey loss at the circuit's own wait length predicted how a reuse-shaped circuit fared when that qubit waited in it | ibm_fez | 48, 11 Oct | AGREE, informative (three of five chains) |
| [15](docs/findings.md#finding-15) | On a second day, the rule fixed in finding 14 held on three of four informative chains and failed on one, where the circuit did better than predicted | ibm_fez | 49, 13 Oct | DISAGREE; held on three of four informative chains |
| [16](docs/findings.md#finding-16) | What a waiting qubit's neighbours do changed how much phase it lost: held in the excited state during the wait they added 0.25 to 0.35 of loss on both qubits tested, their readout alone added none, and finding 15's gap on 144 was gone 33 minutes later | ibm_fez | 50, 13 Oct | NOT SUPPORTED (Kickoff 49's gap not present) |
| [17](docs/findings.md#finding-17) | With a known phase added to the waiting qubit, the wait test on 144 answered as if its offset differed from an idle-neighbour Ramsey's; on 143 the design was nearly blind | ibm_fez | 51, 13 Oct | SUPPORTED on 144 |
| [18](docs/findings.md#finding-18) | A full sweep of the known phase measured the difference: the wait test's offset differed from an idle-neighbour Ramsey's by −7.2° on 143 and −21.6° on 144, and an active-neighbour Ramsey sat closer to it on both | ibm_fez | 52, 13 Oct | DIFFERENT on 143 and on 144 |
| [19](docs/findings.md#finding-19) | The revised check, with an active-neighbour Ramsey, predicted the wait test within ±0.15 on all five informative cells of four chains it had never run on, where the original check would have returned DISAGREE | ibm_fez | 53, 13 Oct | AGREE on five informative cells; the original check DISAGREE |
| [20](docs/findings.md#finding-20) | On a second processor, ibm_kingston, the revised check missed on one of four informative cells, where the original check would have missed on all four; the active-neighbour Ramsey was the closer of the two on every informative cell | ibm_kingston | 55, 14 Oct | DISAGREE on one of four informative cells; the original check DISAGREE on all four |
| [21](docs/findings.md#finding-21) | On a second day on ibm_fez, across a maintenance and under a new daily calibration, the revised check predicted the wait test within ±0.15 on all seven informative cells, where the original check would have missed on one | ibm_fez | 54, 15 Oct | AGREE on seven informative cells; the original check DISAGREE |

What would discredit the map: a NOISE verdict (it does not repeat), a REDUNDANT verdict (the published figures already carry it), NOT USEFUL (it picks no better pairs), or FADES (it does not last long enough to plan by).

## Limits

- **One circuit family.** Every map comes from one encoded four-site Hamiltonian, at two strengths of its diagonal coupling (circuits A and B). Other circuits might order the pairs differently.
- **Three processors, three days.** The hardware results of findings 1 to 10 are from ibm_fez and ibm_kingston, and from Rigetti Cepheus-1-108Q through Open Quantum and through Amazon Braket, all on 5 to 7 October 2026.
- **One processor, one day, for the reuse findings.** Findings 11 to 13 are from one processor on one day, across three published calibration stamps.
- **One processor, one day, five qubits, for finding 14.** Finding 14 is from one job on ibm_fez on 11 October 2026, under one published calibration stamp.
- **One processor, one day, six waiting qubits, for findings 15 to 19.** Findings 15 to 19 are from five jobs on ibm_fez on 13 October 2026. From finding 15's calibration stamp to finding 19's submission no published T1, T2, readout, gate or CZ value changed; during finding 19's job, at 20:29:58 UTC, IBM published new readout errors on 154 qubits.
- **Two processors, three days, for the active-neighbour check.** On ibm_fez it has run on six waiting qubits, on 13 October 2026 (findings 16 to 19) and again on 15 October (finding 21); on ibm_kingston on four, on 14 October (finding 20). Which of two calibration stamps finding 20's job ran under is not known.
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

A fourth, `examples/04_wait_test.py`, builds finding 13's Part B and the wait test for a backend and chain you name, as a dry run unless `--submit`; [`docs/reproduce.md`](docs/reproduce.md) says how to rerun them on hardware, and why a rerun is a new measurement. The check of findings 14 to 19, which predicts the wait test from the waiting qubit's Ramsey loss over the circuit's own wait (`manacitra.wait.build_wait_ramsey` and `predicted_fidelity`), now runs that Ramsey with the qubit's neighbours active, as they are in the circuit, by default; the idle-neighbour Ramsey, the 0.5.0 behaviour, remains with `neighbours="idle"`.

## Reproducing the numbers

```bash
pip install -e ".[dev,aer]"
pytest tests/test_reproduction.py tests/test_field_inventory.py   # every listed statistic, from the archived inputs
python examples/03_pick_pairs.py                                   # finding 4: both picks and the 35.6%
```

Every statistic listed in `tests/expected_fields.json` is recomputed from the archived inputs and compared at 10⁻⁶, with the exceptions named in [`docs/findings.md`](docs/findings.md); every measured number in the README and the findings is checked by a test. How each run was made is in [`docs/kickoffs.md`](docs/kickoffs.md), and the dataset, file by file, in [`data/README.md`](data/README.md).

## Documentation

- [`docs/findings.md`](docs/findings.md): the twenty-one findings in full, what was known before them, and what has not been shown.
- [`docs/method.md`](docs/method.md): the method in six pictures.
- [`docs/kickoffs.md`](docs/kickoffs.md): how the results were made, and every run.
- [`docs/install.md`](docs/install.md): installing without a clone, the extras, the provider backends and their guards.
- [`docs/reproduce.md`](docs/reproduce.md): rerunning finding 13's Part B and the wait test on hardware, and why a rerun is a new measurement.
- [`docs/index.md`](docs/index.md): the long version: the circuits, the three rules with their thresholds, the backends, the safety guards, reproducing every number, and sealing and signing.
- [`data/README.md`](data/README.md): the dataset, its formats, and how to recompute the payoff.
- [`CONTRIBUTING.md`](CONTRIBUTING.md), [`SECURITY.md`](SECURITY.md), [`CHANGELOG.md`](CHANGELOG.md), and [`build-report.md`](build-report.md), the record of how this release was built and checked.

## How to cite

Please cite the software and, if you use them, the data, using [`CITATION.cff`](CITATION.cff):

> Patel, A. (2026). *Manacitra: a map of your qubits* (version 0.6.0) [Software and data]. Zenodo. https://doi.org/10.5281/zenodo.23228518. Source: https://github.com/dogma-guru/manacitra

That DOI is the concept DOI, which the badge at the top also points to: it always resolves to the latest version. Each version also has its own DOI, on its Zenodo record; to cite one version exactly, use that (version 0.5.0: [10.5281/zenodo.23300255](https://doi.org/10.5281/zenodo.23300255)).

## Support

Manacitra is free to use under its licences. If it is useful to you, you can support its work on [Patreon](https://www.patreon.com/DogmaGuru). Forks are welcome; pull requests are not accepted at this time, and questions go to Issues ([`CONTRIBUTING.md`](CONTRIBUTING.md)).

## Licence

The code is licensed under the Apache License 2.0 ([`LICENSE`](LICENSE), [`NOTICE`](NOTICE)). The data in `data/` and the documentation in `docs/` are licensed under Creative Commons Attribution 4.0 ([`data/LICENSE`](data/LICENSE), [`docs/LICENSE`](docs/LICENSE)). The copyright holder is Dogma LLC (Dogma Guru).

Manacitra is developed by Anish Patel and published by Dogma Guru.
