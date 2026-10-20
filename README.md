# Manacitra

[![DOI](https://zenodo.org/badge/1406355471.svg)](https://doi.org/10.5281/zenodo.23228518)

**Manacitra makes a map of a quantum processor's qubit pairs: which pairs keep a small, known difference and which lose it, and it uses the map to choose pairs for a job.** The name is the Sanskrit *māna* (measure) and *citra* (picture): *mānacitra*, the Hindi word for a map. The name is measure-picture, map; it says nothing about minds.

**Contents:** [Who it is for](#who-it-is-for) · [Latest finding](#latest-finding-the-duty-across-spans-jobs-and-days) · [What it does](#what-it-does) · [Words used here](#words-used-here) · [Findings](#findings) · [Limits](#limits) · [The idea](#the-idea) · [Install and try it](#install-and-try-it) · [Reproducing the numbers](#reproducing-the-numbers) · [Documentation](#documentation) · [How to cite](#how-to-cite) · [Support](#support) · [Licence](#licence)

## Who it is for

Manacitra is for people who run work on shared quantum processors and want to check, on the qubits and pairs they will use, whether the provider's published figures already describe them: researchers choosing qubits or pairs, people checking their own error bars, and anyone studying how a device's results move between runs, execution spans and days. It is also a worked example of measuring in the open. The rule for each newer test is hashed and posted in a public issue before its run or read, all but test 8's, which was posted after its run; every number the runs measured, as this README and the findings give it, is checked by a test against the published files; and the mistakes found along the way are kept beside their corrections. No account or hardware is needed to start: the simulator runs locally, and the archived results reproduce from the published files. The words it uses are listed under [Words used here](#words-used-here).

**How Manacitra and Sandhi relate.** Manacitra measures; Sandhi forecasts. Manacitra is the Python package and its tests: it builds the circuits, reads the counts and, from the per-shot records, gives the quantities the findings report, such as a qubit's duty, its correlation time and the boundary words between execution spans. Sandhi is a desk model kept in [`data/desk/sandhi/`](data/desk/sandhi/README.md), outside the package: since version 4, a two-state model fitted on the desk to Manacitra's records and nothing else, with no hardware. Before a run, Sandhi's predictions for it are hashed and posted in a public issue; after the run, a scorer hashed with the predictions compares them with Manacitra's read of that run. Manacitra's measurements are the record; Sandhi's scorecards say how well a simple model of that record forecasts the next run, and a version that does not describe the record is set down in the open, as version 3 was. Neither names a cause.

## Latest finding: the duty across spans, jobs and days

Two runs on ibm_fez's qubit 143 on 19 October 2026, test 11's design on a third day and one job of six execution spans, were read per shot, each run and each read under a rule hashed before it ([finding 30](docs/findings.md#finding-30)). Across the six spans of one job every boundary read NO CHANGE, each adjacent pair differing by less than twice its combined error, which does not show the duties equal; and the monitor means of runs on 17 and 19 October were 0.330, 0.341 and 0.313. A pattern noticed in the published weights, a job's middle span above its ends, was tested on new data under a rule fixed before them and not seen. The desk model Sandhi, at version 4.1, had its bets for one design hashed before the run and none counted against it, with its bets for the other design not yet scored; no cause is named. To be released as 0.10.0.

## What it does

Manacitra runs two short circuits on a set of non-overlapping qubit pairs at once (27 in the published runs); every coupler on a chip can be covered in a few rounds. The two circuits use the same three two-qubit gates and differ only in single-qubit angles, so an exact model knows the difference between their outcomes in advance: 0.037765 for the main circuit. Each pair keeps some share of that difference, its **kept share** k, and the shares of all the pairs form the map. Three rules, fixed before any data was taken (according to the author's dated records, which are not part of this release), then say whether the map is real (it repeats and carries over to a second circuit), whether the provider's published error rates already contain it, and whether choosing pairs by it does better on unrelated work. `manacitra pick` then ranks the pairs from a map by how close each pair's kept share is to the ideal of 1, |1 − k| (`--by kept-share-highest` gives the highest-first rule Kickoff 33 used), or, with `--by level`, by the plain level, which chose better pairs on the Rigetti processor where the kept share did not. It does not check the verdict (it warns when the verdict is not DIAGNOSTIC or MAP PRESENT), and Manacitra does not run your own job: you run it on the pairs you choose.

It maps pairs. It does not rank machines.

![ibm_fez's heavy-hex coupling map with 27 pairs drawn as segments shaded from light blue (kept least, k = 0.22) to dark blue (kept most, k = 1.06), each also drawn thicker the more it kept and numbered by its rank (1 = kept most), and other couplers in light grey. Beside it, a smaller copy of the same map with the same 27 pairs shaded by IBM's published error score, from light (highest error, 0.021) to dark (lowest error, 0.011). The two shadings differ pair by pair.](docs/diagrams/chip-map.svg)

The left map is ibm_fez's 27 pairs from Kickoff 31 (5 October 2026, 12:37 UTC), each coloured by its kept share. Each pair is also drawn thicker the more it kept, and numbered by its rank; every pair's k, x and ranks are in [a table](docs/diagrams/chip-map-table.md). The small map on the right colours the same pairs by the published score x (the pair's two-qubit error plus both qubits' readout errors, as IBM reported them at submission). Dark means better on both. The two pictures order the pairs differently: across these 27 pairs, k and x correlate at r = −0.18.

## Words used here

One sentence each, taken from the page it links to, where each is defined at length.

- **Kept share** (k): the change in a pair's P(11) between the two circuits as a share of the change the exact model predicts, 0.038 for the main circuit, so that a pair that moved by 0.040 has k = 1.06 and one that moved by 0.008 has k = 0.22 ([the method](docs/method.md#1-the-kept-share)).
- **Map**: the kept shares of all the pairs measured, one per pair, drawn on the chip's coupling map ([the method](docs/method.md#2-the-map)).
- **The map rule's verdicts**: NOISE, the map does not repeat (r_split under 0.3); REDUNDANT, the published score already holds it; DIAGNOSTIC, it repeats, carries over to a second circuit and survives with the published score taken out, which does not explain it; MAP PRESENT, it repeats and carries over where the provider publishes no per-pair figures; NOT SETTLED, anything else ([the rule](docs/index.md#the-map-rule-kickoff-31)).
- **Ramsey fringe**: a qubit's P(1) after H, a wait and H, read across waits, which can be fitted as one line with decay or as two fixed lines, and which a short span of waits does not tell apart ([the method](docs/method.md#the-two-quadrature-ramsey-and-the-two-model-fit)).
- **Execution span**: one of the runs in which a provider may execute a job, each a run of the submitted circuits, with gaps between them, the provider's record giving each span's positions, start and stop ([the method](docs/method.md#the-monitor-and-the-execution-spans)).
- **Boundary**: the place between two adjacent spans of a job, across which changes are set apart from those between adjacent repeats of a span, a repeat whose circuits ran in different spans straddling it ([the method](docs/method.md#the-monitor-and-the-execution-spans)).
- **Sweep**: one returned shot index across a span's repeats; the sweep series is the mean at each returned index, on the sweep clock, the returned order, which is in seconds only if that order is chronological and even ([the method](docs/method.md#reading-a-span-per-shot)).
- **Per-shot read**: a reading of a span from each position's shots one by one, as the provider returns them, rather than from its counts, giving the sweep series, the sharing ratio, the duty, the correlation time and the error of a time average ([the method](docs/method.md#reading-a-span-per-shot)).
- **Duty**: the fraction b of a span's sweep series above the threshold between its two states, never folded ([the method](docs/method.md#reading-a-span-per-shot)).
- **Weight**: the free weight b on the upper of the two fixed lines in the two-line fit, read per repeat by the monitor at antiphase as w ([the method](docs/method.md#the-two-quadrature-ramsey-and-the-two-model-fit)).
- **Correlation time** (τ_c): the first lag at which the autocorrelation of a span's sweep series falls below 1/e of its excess over shot noise, times the sweep time ([the method](docs/method.md#reading-a-span-per-shot)).
- **Desk model** (Sandhi): a kinetic description of the records, fitted on the desk from bundles of those records and nothing else, with no hardware, and not a run record or counts of any device ([its folder](data/desk/sandhi/README.md)).

## Findings

Thirty findings, from runs on 5 to 19 October 2026. Here the findings on one thread share a row, and each number links to its finding; each is given in full, with its caveats, in [`docs/findings.md`](docs/findings.md), which also has [the full table](docs/findings.md#the-findings-in-one-table), one row per finding. What has *not* been shown is there too.

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
| The fringe on 143: one line or two | [28](docs/findings.md#finding-28) | ibm_fez | Measured at every wait from 0 to 63 µs in two quadratures, 143's Ramsey fringe was two fixed frequencies about 90 kHz apart at unequal weight, not one line decaying; the weight differed between the job's execution spans. | TWO FIXED FREQUENCIES |
| When a qubit's fringe changes: the shared state within a span | [29](docs/findings.md#finding-29) | ibm_kingston, ibm_fez | Read per shot, on every qubit where tests 13 and 15 read SHARED (143; 11 and 95 in every span, 120 in half), a span's circuits are dependent at equal returned shot index, read as a shared state; on 143 the fringe switches between its two lines with correlation lags of 4 to 10 sweeps (about 0.1 to 0.2 s if returned order is chronological), a span's weight reads as an average over the span, and against its estimated error all 17 boundaries read show no change; about a third of the 47 kingston qubits compared across two calibration stamps (16) changed by 4 kHz or more; the desk model Sandhi is set down at version 3. | QUIET between adjacent repeats; SWITCHES AT BOUNDARIES ONLY on one qubit; STEADY, STEPPED and MOVING; CONFIRMED ON DAY 2 on 143; LEVELS DIFFER AT SOME at the shots' error; SHARED; NO CHANGE at 17 of 17 |
| The duty across spans, jobs and days | [30](docs/findings.md#finding-30) | ibm_fez | Read per shot on 19 October 2026, every monitor span of 143 read SHARED; across the six spans of one job the duty read NO CHANGE at every boundary, and the monitor means of runs on 17 and 19 October were 0.330, 0.341 and 0.313; a pattern noticed in the published weights was not seen on new data; the desk model Sandhi's version 4.1 had its bets for one design hashed before the run, and none counted against it. | CONFIRMED ON DAY 2, QUIET and WEIGHT QUIET; SHARED; NO CHANGE at five of five; NOT SEEN |

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
- **Two processors, two days, for finding 29.** Finding 29 is from eight tests on ibm_kingston and ibm_fez on 17 and 18 October 2026, six of them jobs, each under one published calibration stamp but for three reads at test 10's first job, and two of them reads of jobs already run, beside test 7's job of the day before; the desk model Sandhi, set down at version 3, describes tests 7 to 11 and no others.
- **One qubit, one processor, for finding 30.** Finding 30 is from two runs on ibm_fez's qubit 143 on 19 October 2026, each under one published calibration stamp, and one read of jobs already run, beside the runs of 17 October; the desk model Sandhi's versions 4 and 4.1 describe the records of tests 10 to 15 and of test 11's third day and no others, and version 4.1 has been scored on one run.
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

How long the tests take: the reproduction subset, `pytest tests/test_reproduction.py tests/test_field_inventory.py`, about 6 minutes on one laptop with 10 cores, and the full suite, `pytest`, about 14 minutes on the same; a first reader reported about 10 minutes for the tests on theirs.

**As a plain package**, installed with `pip install ".[aer]"` from a clone or with `pip install "git+https://github.com/dogma-guru/manacitra"`, Manacitra comes without the dataset. [`docs/install.md`](docs/install.md) says how to point it at a clone's `data/`, and covers the extras, the provider backends and the checks made before anything is sent.

Point an install at a clone's data with `manacitra --data /path/to/manacitra/data verdict ibm_fez/k31-map.json` or `MANACITRA_DATA`; `--data` goes before the subcommand. A provider backend sends nothing unless `--submit` is given; the simulator runs at once, on your machine, and sends nothing.

Then, on the simulator, with no account (paste this into a Python session):

```python
import numpy as np

from manacitra.backends.base import MapJob
from manacitra.backends.simulator import NoiseModel, SimulatorBackend
from manacitra.layout import pick_by_kept_share
from manacitra.verdicts import analyse_map

pairs = [(2 * i, 2 * i + 1) for i in range(27)]
noise, planted = NoiseModel.random(pairs, seed=1).planted(sigma=0.03)  # a hidden per-pair map
sim = SimulatorBackend(noise, seed=7)
counts = sim.fetch(sim.submit(MapJob(pairs)))
result = analyse_map(counts.p11(), counts.order, x=sim.target().x_of(pairs))
print(result["verdict"]["verdict"], [pairs[i] for i in pick_by_kept_share(result["kA"], 8)])

s = result["verdict"]["inputs"]  # the numbers the verdict rests on, with the map rule's thresholds
print(f"r_split {s['r_split_A']:.3f}  (at least 0.5; under 0.3 is NOISE)")
print(f"r_AB    {s['r_AB']:.3f}  (at least 0.4, with p = {s['p_AB']:.4f} under 0.05)")
print(f"r_AB.x  {s['r_AB_given_x']:.3f}  (at least 0.3)")
print(f"r_Ax    {s['r_Ax']:.3f}  (|r_Ax| under 0.5)")

delta = np.array([planted[p] for p in pairs])  # the over-rotation planted on each pair
print("pair, the over-rotation planted, the kept share k_A measured:")
for i in range(0, 27, 3):
    print("   ".join(f"{pairs[j]!s:8} {delta[j]:+.3f} {result['kA'][j]:.3f}" for j in range(i, i + 3)))
print(f"planted against measured, across the 27 pairs: r = {np.corrcoef(delta, result['kA'])[0, 1]:.2f}")
```

It prints `DIAGNOSTIC` and the eight pairs whose kept share is closest to the ideal of 1, the rule `manacitra pick` uses by default. `pick_pairs(k, n)` ranks highest first, the rule Kickoff 33 ran; `pick_by_kept_share` is the default since Amendment A15. Then it prints the four statistics the verdict rests on, each with its threshold in the map rule ([`docs/index.md`](docs/index.md#3-the-three-rules), section 3), and, pair by pair, the over-rotation the simulator planted beside the kept share it measured, with their correlation:

```text
DIAGNOSTIC [(20, 21), (50, 51), (26, 27), (10, 11), (18, 19), (32, 33), (38, 39), (48, 49)]
r_split 0.704  (at least 0.5; under 0.3 is NOISE)
r_AB    0.817  (at least 0.4, with p = 0.0000 under 0.05)
r_AB.x  0.841  (at least 0.3)
r_Ax    -0.004  (|r_Ax| under 0.5)
pair, the over-rotation planted, the kept share k_A measured:
(0, 1)   +0.028 0.879   (2, 3)   -0.008 0.923   (4, 5)   +0.021 0.878
(6, 7)   +0.008 0.824   (8, 9)   +0.017 0.746   (10, 11) -0.013 0.962
(12, 13) +0.021 0.847   (14, 15) +0.037 0.827   (16, 17) +0.019 0.914
(18, 19) -0.035 1.048   (20, 21) -0.028 1.001   (22, 23) +0.026 0.787
(24, 25) +0.017 0.876   (26, 27) -0.010 0.964   (28, 29) -0.056 1.139
(30, 31) +0.031 0.823   (32, 33) +0.016 0.947   (34, 35) +0.026 0.852
(36, 37) +0.001 0.916   (38, 39) -0.025 1.065   (40, 41) +0.055 0.774
(42, 43) +0.016 0.908   (44, 45) +0.021 0.916   (46, 47) +0.018 0.792
(48, 49) +0.002 0.928   (50, 51) -0.027 0.965   (52, 53) -0.054 1.101
planted against measured, across the 27 pairs: r = -0.89
```

A working install prints these lines: DIAGNOSTIC, every statistic past its threshold, and a measured map that tracks the planted one (r = −0.89). Another verdict, a statistic short of its threshold, or a correlation near zero means the install differs from the one that printed them. Three longer examples are in `examples/`: the simulator end to end, the ibm_fez numbers reproduced from the archived counts, and the payoff choice.

A fourth, `examples/04_wait_test.py`, builds finding 13's Part B and the wait test for a backend and chain you name, as a dry run unless `--submit`; [`docs/reproduce.md`](docs/reproduce.md) says how to rerun them on hardware, and why a rerun is a new measurement. The check of findings 14 to 19, which predicts the wait test from the waiting qubit's Ramsey loss over the circuit's own wait (`manacitra.wait.build_wait_ramsey` and `predicted_fidelity`), now runs that Ramsey with the qubit's neighbours active, as they are in the circuit, by default; the idle-neighbour Ramsey, the 0.5.0 behaviour, remains with `neighbours="idle"`. The check at the peak phase is two jobs: `phase_sweep` builds the sweep, and `peak_check` builds the check from its counts, with the peak phase to record before the check runs; `readout_survey` and `readout_errors` measure every qubit's readout ([the method](docs/method.md#the-check-at-the-peak-phase)).

## Reproducing the numbers

```bash
pip install -e ".[dev,aer]"
pytest tests/test_reproduction.py tests/test_field_inventory.py   # every listed statistic, from the archived inputs
python examples/03_pick_pairs.py                                   # finding 4: both picks and the 35.6%
```

Every statistic listed in `tests/expected_fields.json` is recomputed from the archived inputs and compared at 10⁻⁶, with the exceptions named in [`docs/findings.md`](docs/findings.md); every number the runs measured, as the README and the findings give it, is checked by a test. How each run was made is in [`docs/kickoffs.md`](docs/kickoffs.md), and the dataset, file by file, in [`data/README.md`](data/README.md).

## Documentation

**Reading order:** this README, then [`docs/method.md`](docs/method.md), then [`docs/findings.md`](docs/findings.md); [`docs/index.md`](docs/index.md) for the long version; the rest as needed.

- [`docs/findings.md`](docs/findings.md): the thirty findings in full, with a table of all of them, what was known before them, and what has not been shown.
- [`docs/method.md`](docs/method.md): the method in six pictures.
- [`docs/kickoffs.md`](docs/kickoffs.md): how the results were made, and every run.
- [`docs/install.md`](docs/install.md): installing without a clone, the extras, the provider backends and their guards.
- [`docs/reproduce.md`](docs/reproduce.md): rerunning finding 13's Part B and the wait test on hardware, and why a rerun is a new measurement.
- [`docs/index.md`](docs/index.md): the long version: the circuits, the three rules with their thresholds, the backends, the safety guards, reproducing every number, and sealing and signing.
- [`data/README.md`](data/README.md): the dataset, its formats, and how to recompute the payoff.
- [`CONTRIBUTING.md`](CONTRIBUTING.md), [`SECURITY.md`](SECURITY.md), [`CHANGELOG.md`](CHANGELOG.md), and [`build-report.md`](build-report.md), the record of how this release was built and checked.

## How to cite

Please cite the software and, if you use them, the data, using [`CITATION.cff`](CITATION.cff):

> Patel, A. (2026). *Manacitra: a map of your qubits* (version 0.9.0) [Software and data]. Zenodo. https://doi.org/10.5281/zenodo.23228518. Source: https://github.com/dogma-guru/manacitra

That DOI is the concept DOI, which the badge at the top also points to: it always resolves to the latest version. Each version also has its own DOI, on its Zenodo record; to cite one version exactly, use that (version 0.9.0: [10.5281/zenodo.23454906](https://doi.org/10.5281/zenodo.23454906)).

## Support

Manacitra is free to use under its licences. If it is useful to you, you can support its work on [Patreon](https://www.patreon.com/DogmaGuru). Forks are welcome; pull requests are not accepted at this time, and questions go to Issues ([`CONTRIBUTING.md`](CONTRIBUTING.md)).

## Licence

The code is licensed under the Apache License 2.0 ([`LICENSE`](LICENSE), [`NOTICE`](NOTICE)). The data in `data/` and the documentation in `docs/` are licensed under Creative Commons Attribution 4.0 ([`data/LICENSE`](data/LICENSE), [`docs/LICENSE`](docs/LICENSE)). The copyright holder is Dogma LLC (Dogma Guru).

Manacitra is developed by Anish Patel and published by Dogma Guru.
