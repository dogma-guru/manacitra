# Manacitra

[![DOI](https://zenodo.org/badge/1406355471.svg)](https://doi.org/10.5281/zenodo.23228518)

**Manacitra makes a map of a quantum processor's qubit pairs: which pairs keep a small, known difference and which lose it, and it uses the map to choose pairs for a job.** The name is the Sanskrit *māna* (measure) and *citra* (picture): *mānacitra*, the Hindi word for a map. The name is measure-picture, map; it says nothing about minds.

**Contents:** [What it does](#what-it-does) · [Findings](#findings) · [Limits](#limits) · [The idea](#the-idea) · [Install and try it](#install-and-try-it) · [Reproducing the numbers](#reproducing-the-numbers) · [Documentation](#documentation) · [How to cite](#how-to-cite) · [Support](#support) · [Licence](#licence)

## What it does

Manacitra runs two short circuits on a set of non-overlapping qubit pairs at once (27 in the published runs); every coupler on a chip can be covered in a few rounds. The two circuits use the same three two-qubit gates and differ only in single-qubit angles, so an exact model knows the difference between their outcomes in advance: 0.037765 for the main circuit. Each pair keeps some share of that difference, its **kept share** k, and the shares of all the pairs form the map. Three rules, fixed before any data was taken (according to the author's dated records, which are not part of this release), then say whether the map is real (it repeats and carries over to a second circuit), whether the provider's published error rates already contain it, and whether choosing pairs by it does better on unrelated work. `manacitra pick` then ranks the pairs from a map, highest kept share first, or, with `--by level`, by the plain level, which chose better pairs on the Rigetti processor where the kept share did not. It does not check the verdict (it warns when the verdict is not DIAGNOSTIC or MAP PRESENT), and Manacitra does not run your own job: you run it on the pairs you choose.

It maps pairs. It does not rank machines.

![ibm_fez's heavy-hex coupling map with 27 pairs drawn as segments shaded from light blue (kept least, k = 0.22) to dark blue (kept most, k = 1.06), each also drawn thicker the more it kept and numbered by its rank (1 = kept most), and other couplers in light grey. Beside it, a smaller copy of the same map with the same 27 pairs shaded by IBM's published error score, from light (highest error, 0.021) to dark (lowest error, 0.011). The two shadings differ pair by pair.](docs/diagrams/chip-map.svg)

The left map is ibm_fez's 27 pairs from Kickoff 31 (5 October 2026, 12:37 UTC), each coloured by its kept share. Each pair is also drawn thicker the more it kept, and numbered by its rank; every pair's k, x and ranks are in [a table](docs/diagrams/chip-map-table.md). The small map on the right colours the same pairs by the published score x (the pair's two-qubit error plus both qubits' readout errors, as IBM reported them at submission). Dark means better on both. The two pictures order the pairs differently: across these 27 pairs, k and x correlate at r = −0.18.

## Findings

Ten findings, from runs on 5 to 7 October 2026. Each is given in full, with its caveats, in [`docs/findings.md`](docs/findings.md); the number links to it. What has *not* been shown is there too.

| # | finding | where | kickoff, 2026 | verdict |
|---|---|---|---|---|
| [1](docs/findings.md#finding-1) | Each pair keeps its own share, and the share repeats | ibm_fez, ibm_kingston | 31, 5 Oct | DIAGNOSTIC on both |
| [2](docs/findings.md#finding-2) | The map exists on a second vendor's chip, within one job | Rigetti Cepheus-1-108Q, through Open Quantum | 34b, 5 Oct | MAP PRESENT |
| [3](docs/findings.md#finding-3) | The gap between the best and worst pairs persisted when their neighbours were idle | ibm_fez, ibm_kingston | 32, 5 Oct | THE GATE on both (not explained by the tested neighbours) |
| [4](docs/findings.md#finding-4) | On ibm_fez, choosing pairs by the map gave 35.6% less error on unrelated random circuits than choosing by the published error rates | ibm_fez, ibm_kingston | 33, 5 Oct | USEFUL on ibm_fez; NOT SETTLED on ibm_kingston |
| [5](docs/findings.md#finding-5) | The rule can say no | a simulation of willow_pink's published noise | 36, 5 Oct | NOISE without a planted map; DIAGNOSTIC with one |
| [6](docs/findings.md#finding-6) | On the Rigetti processor, a pair's level depends on the program that measures it, not on the hour | Rigetti Cepheus-1-108Q, through Open Quantum | 37, 38, 6 Oct | PLACEMENT; ACTIVITY |
| [7](docs/findings.md#finding-7) | On ibm_fez, a map of the whole chip held for two days | ibm_fez, all 176 coupled pairs | 35, 5 to 7 Oct | HOLDS over two days |
| [8](docs/findings.md#finding-8) | On the Rigetti processor, with placement pinned, the map is DIAGNOSTIC | Rigetti Cepheus-1-108Q, through Amazon Braket | 40, 6 Oct | PINNED; DIAGNOSTIC; payoff NOT SETTLED |
| [9](docs/findings.md#finding-9) | The pinned Rigetti map lasted a day, and the day-old level chose better pairs | Rigetti Cepheus-1-108Q, through Amazon Braket | 41, 7 Oct | HOLDS; the level USEFUL; the kept share NOT SETTLED |
| [10](docs/findings.md#finding-10) | On the Rigetti processor, a pair's response to a particular program repeats a day later, and a smooth shift of the offset does not describe it | Rigetti Cepheus-1-108Q, through Amazon Braket | 42, 6 to 7 Oct | SPREAD, MIXED, DOES NOT; the per-program pattern HOLDS a day later |

What would discredit the map: a NOISE verdict (it does not repeat), a REDUNDANT verdict (the published figures already carry it), NOT USEFUL (it picks no better pairs), or FADES (it does not last long enough to plan by).

## Limits

- **One circuit family.** Every map comes from one encoded four-site Hamiltonian, at two strengths of its diagonal coupling (circuits A and B). Other circuits might order the pairs differently.
- **Three processors, three days.** The hardware results are from ibm_fez and ibm_kingston, and from Rigetti Cepheus-1-108Q through Open Quantum and through Amazon Braket, all on 5 to 7 October 2026.
- **Two routes to one processor.** The Rigetti findings through Open Quantum (2, 6) and through Amazon Braket (8 to 10) are from the same processor, but only the Braket route records where each pair ran. The difference between them is a difference between the two platforms' placement records, not between the vendors' machines.
- **Small absolute differences.** The gap is 0.038 in P(11), and the payoff is about a tenth of a percentage point of fidelity on the random workload.
- **No claim about any device's design.** A pair's kept share is a measurement of what it did with these circuits; it says nothing about why, or about how the processor was built.

## The idea

![Four boxes in a row joined by arrows: Map (in: 16 short circuits on a set of non-overlapping qubit pairs at once (27 in the published runs); every coupler on a chip can be covered in a few rounds; out: k per pair), Verdict (in: k from two circuits, split halves, published x; out: NOISE, REDUNDANT, DIAGNOSTIC, MAP PRESENT or NOT SETTLED), Pick (in: the map; out: the n pairs that kept the most, ranked without checking the verdict), Run, drawn dashed (your own job, run by you on the picked pairs, not by Manacitra). A dashed note above the Map box says that, according to the author's dated records, which are not part of this release, the rules and predictions were sealed before each map job was sent.](docs/diagrams/pipeline.svg)

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

## Reproducing the numbers

```bash
pip install -e ".[dev,aer]"
pytest tests/test_reproduction.py tests/test_field_inventory.py   # every listed statistic, from the archived inputs
python examples/03_pick_pairs.py                                   # finding 4: both picks and the 35.6%
```

Every statistic listed in `tests/expected_fields.json` is recomputed from the archived inputs and compared at 10⁻⁶, with the exceptions named in [`docs/findings.md`](docs/findings.md); every measured number in the README and the findings is checked by a test. How each run was made is in [`docs/kickoffs.md`](docs/kickoffs.md), and the dataset, file by file, in [`data/README.md`](data/README.md).

## Documentation

- [`docs/findings.md`](docs/findings.md): the ten findings in full, and what has not been shown.
- [`docs/method.md`](docs/method.md): the method in six pictures.
- [`docs/kickoffs.md`](docs/kickoffs.md): how the results were made, and every run.
- [`docs/install.md`](docs/install.md): installing without a clone, the extras, the provider backends and their guards.
- [`docs/index.md`](docs/index.md): the long version: the circuits, the three rules with their thresholds, the backends, the safety guards, reproducing every number, and sealing and signing.
- [`data/README.md`](data/README.md): the dataset, its formats, and how to recompute the payoff.
- [`CONTRIBUTING.md`](CONTRIBUTING.md), [`SECURITY.md`](SECURITY.md), [`CHANGELOG.md`](CHANGELOG.md), and [`build-report.md`](build-report.md), the record of how this release was built and checked.

## How to cite

Please cite the software and, if you use them, the data, using [`CITATION.cff`](CITATION.cff):

> Patel, A. (2026). *Manacitra: a map of your qubits* (version 0.1.1) [Software and data]. Zenodo. https://doi.org/10.5281/zenodo.23228518. Source: https://github.com/dogma-guru/manacitra

That DOI is the concept DOI, which the badge at the top also points to: it always resolves to the latest version. Each version also has its own DOI, on its Zenodo record; to cite one version exactly, use that (version 0.1.1: [10.5281/zenodo.23239929](https://doi.org/10.5281/zenodo.23239929)).

## Support

Manacitra is free to use under its licences. If it is useful to you, you can support its work on [Patreon](https://www.patreon.com/DogmaGuru). Forks are welcome; pull requests are not accepted at this time, and questions go to Issues ([`CONTRIBUTING.md`](CONTRIBUTING.md)).

## Licence

The code is licensed under the Apache License 2.0 ([`LICENSE`](LICENSE), [`NOTICE`](NOTICE)). The data in `data/` and the documentation in `docs/` are licensed under Creative Commons Attribution 4.0 ([`data/LICENSE`](data/LICENSE), [`docs/LICENSE`](docs/LICENSE)). The copyright holder is Dogma LLC (Dogma Guru).

Manacitra is developed by Anish Patel and published by Dogma Guru.
