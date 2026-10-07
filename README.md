# Manacitra

**Manacitra makes a map of a quantum processor's qubit pairs: which pairs keep a small, known difference and which lose it, and it uses the map to choose pairs for a job.** The name is the Sanskrit *māna* (measure) and *citra* (picture): *mānacitra*, the Hindi word for a map. The name is measure-picture, map; it says nothing about minds.

## What it does

Manacitra runs two short circuits on a set of non-overlapping qubit pairs at once (27 in the published runs); every coupler on a chip can be covered in a few rounds. The two circuits use the same three two-qubit gates and differ only in single-qubit angles, so an exact model knows the difference between their outcomes in advance: 0.037765 for the main circuit. Each pair keeps some share of that difference, its **kept share** k, and the shares of all the pairs form the map. Three rules, fixed before any data was taken (according to the author's dated records, which are not part of this release), then say whether the map is real (it repeats and carries over to a second circuit), whether the provider's published error rates already contain it, and whether choosing pairs by it does better on unrelated work. `manacitra pick` then ranks the pairs from a map, highest kept share first. It does not check the verdict (it warns when the verdict is not DIAGNOSTIC or MAP PRESENT), and Manacitra does not run your own job: you run it on the pairs you choose.

It maps pairs. It does not rank machines.

## The idea in five pictures

### 1. The kept share

![Two circuits on one pair of qubits, identical except for their single-qubit gates, shown as two rows of boxes joined by the same three CZ gates. Beside them, three pairs of dots on a P(11) axis: the exact model's outcomes, 0.962 without the offset and 1.000 with it, a gap of 0.038; ibm_fez pair 106-107, 0.923 and 0.963, a gap of 0.040, k = 1.06; ibm_fez pair 20-21, 0.824 and 0.833, a gap of 0.008, k = 0.22.](docs/diagrams/kept-share.svg)

The two circuits encode a four-site Hamiltonian in two qubits; the offset makes the transfer from 00 to 11 exact, so the model's P(11) moves from 0.962 to 1.000. On ibm_fez on 5 October 2026, pair [106, 107] moved by 0.040, slightly more than the model's 0.038 (k = 1.06). Pair [20, 21] moved by 0.008 (k = 0.22): the same gates, the same difference in angles, and most of the difference was gone. Both pairs ran in the same job, with 32,000 shots per variant each. (A PNG version of every diagram sits beside the SVG in `docs/diagrams/`.)

### 2. The map

![ibm_fez's heavy-hex coupling map with 27 pairs drawn as segments shaded from light blue (kept least, k = 0.22) to dark blue (kept most, k = 1.06), each also drawn thicker the more it kept and numbered by its rank (1 = kept most), and other couplers in light grey. Beside it, a smaller copy of the same map with the same 27 pairs shaded by IBM's published error score, from light (highest error, 0.021) to dark (lowest error, 0.011). The two shadings differ pair by pair.](docs/diagrams/chip-map.svg)

The left map is ibm_fez's 27 pairs from Kickoff 31 (5 October 2026, 12:37 UTC), each coloured by its kept share. Each pair is also drawn thicker the more it kept, and numbered by its rank; every pair's k, x and ranks are in [a table](docs/diagrams/chip-map-table.md). The small map on the right colours the same pairs by the published score x (the pair's two-qubit error plus both qubits' readout errors, as IBM reported them at submission). Dark means better on both. The two pictures order the pairs differently: across these 27 pairs, k and x correlate at r = −0.18.

### 3. The pipeline

![Four boxes in a row joined by arrows: Map (in: 16 short circuits on a set of non-overlapping qubit pairs at once (27 in the published runs); every coupler on a chip can be covered in a few rounds; out: k per pair), Verdict (in: k from two circuits, split halves, published x; out: NOISE, REDUNDANT, DIAGNOSTIC, MAP PRESENT or NOT SETTLED), Pick (in: the map; out: the n pairs that kept the most, ranked without checking the verdict), Run, drawn dashed (your own job, run by you on the picked pairs, not by Manacitra). A dashed note above the Map box says that, according to the author's dated records, which are not part of this release, the rules and predictions were sealed before each map job was sent.](docs/diagrams/pipeline.svg)

Map, then verdict, then pick, then run. The verdict says whether the map is worth using at all: a map that does not repeat is NOISE, and a map the published figures already explain is REDUNDANT. Manacitra computes the map and the verdict; `manacitra pick` ranks pairs from the map and does not check the verdict, though it warns when the verdict is not DIAGNOSTIC or MAP PRESENT; and you run your own job. `manacitra pick --by level` ranks by the plain level instead, which chose better pairs on the Rigetti processor where the kept share did not (findings 8 and 9). In the author's own use, the rules and a set of predictions were written down and hashed before each job was sent, according to the author's dated records, which are not part of this release. From this release on, new commitments can be checked by anyone with `manacitra seal` and, once signing is on, a public timestamp; the runs published here predate this release and cannot be checked that way.

Which to rank by, from the two chips: on ibm_fez the kept share chose the better pairs (Kickoff 33); on the Rigetti processor the plain level, each pair's mean P(11) on circuit A without the offset, did, on the same day and a day later (Kickoffs 40 and 41), and the kept share did not. Neither has been tested on a third chip. The dead-pair filter uses the run's own levels, never a list from an earlier day: on the Rigetti processor, dead pairs came and went between consecutive days (18-19 came back; 72-73 and 76-77 went).

### 4. The payoff

![A scatter of 27 ibm_fez pairs: the kept share measured about two hours earlier on the horizontal axis, and fidelity on eight random two-qubit circuits on the vertical axis. The 8 pairs with the highest kept share are filled blue; the 8 with the lowest published error are ringed in orange; some pairs carry both. Dashed lines mark each pick's mean: error 0.0022 for the map's pick and 0.0034 for the published pick. The title reads: choosing by the map, 35.6% less error than choosing by the published rates.](docs/diagrams/payoff.svg)

On ibm_fez on 5 October 2026, the map measured at 13:17 UTC chose 8 pairs, and the published error rates chose another 8. At 15:20 UTC all 27 pairs ran eight random circuits, unrelated to the map, with nine CZ gates each. The map's 8 pairs had a mean error of 0.0022 against 0.0034 for the published pick: 35.6% less. The absolute numbers are small, because every pair's fidelity was above 0.98.

### 5. How to check a sealed prediction

![A timeline of four steps. 1, seal and post the hash (manacitra seal): shows the file existed then, without showing what it says. 2, run the job: the file stays as it was. 3, reveal the salt (manacitra reveal): publishes the file and its salt. 4, anyone verifies (manacitra verify): a match shows the predictions came before the results.](docs/diagrams/sealed-prediction.svg)

This one is for a stranger who wants to know whether the predictions came before the results. `manacitra seal` commits to a file with a salted SHA-256 hash, which is posted somewhere the producer cannot edit; after the run, `manacitra reveal` publishes the salt, and `manacitra verify` lets anyone check that the file is the one committed to. Once the repository is public, a CI workflow also signs every commit record and every data file with Sigstore's keyless signing, which records who signed and when in a public log ([`docs/index.md`](docs/index.md#9-sealing-and-signing)).

## What it has shown, and what it has not

The findings come from runs on 5 to 7 October 2026. The counts are in `data/`. Every statistic listed in `tests/expected_fields.json` is recomputed from the archived inputs: the raw counts where the release includes them; for the Kickoff 29 settling runs and some Rigetti comparisons, the archived probability or level tables, whose counts are not in this release; and, for elapsed times, the archived timestamps, and compared at 10⁻⁶, except the seeded resampling fields: the intervals that also resample shots, at 10⁻³, and Kickoff 42's bootstrap SDs, at 10⁻⁶ under numpy 2.5 or later (`tests/_reproduce.py`, `RESAMPLED`). Fields that cannot be recomputed from this release are named, with reasons, in `tests/excluded_fields.json`. Both lists are checked by `pytest tests/test_reproduction.py tests/test_field_inventory.py`. Every measured statistic in the README is checked by a test; times, ranges and counts are taken from the data files and listed in `tests/test_readme_numbers.py`.

1. **Each pair keeps its own share, and the share repeats** (Kickoff 31; ibm_fez at 12:37 UTC, ibm_kingston at 12:38 UTC; 27 pairs each). Within one job, the map from one half of the circuits correlates with the map from the other half at r = 0.87 (ibm_fez) and 0.90 (ibm_kingston). It carries over to a second circuit with a different gap and its own reference: r = 0.82 and 0.89. The published score does not account for it (r = −0.18 and −0.05). Verdict on both: DIAGNOSTIC.
2. **The map exists on a second vendor's chip, within one job** (Kickoff 34b; Rigetti Cepheus-1-108Q, through Open Quantum, 5 October 2026, main job 22:15 to 22:29 UTC). A screening run chose 27 pairs, and 22 of them were working pairs in the main job. Kickoff 37 later found that the five pairs excluded here read low only under this program: under the 53-pair screen program they read 0.70 to 0.84. Kickoff 40 later ran the same 27 named pairs on this processor through a route that records placement, and found that this job's pair levels do not match the pinned levels (r = −0.17 on the 20 shared working pairs). The pair names in this job are labels, not locations; the within-job finding stands as measured. Within that job, each pair's kept share repeated (the split halves correlate at r = 0.985) and carried over from circuit A to circuit B (r = 0.971). Verdict: MAP PRESENT. Two pairs whose offset circuits collapsed, 13-14 and 101-102, inflate these Pearson figures. Without them, on 20 pairs, the repeat check is 0.84 and the carry-over 0.79, and the rule still gives MAP PRESENT; this 20-pair figure was computed after seeing the data. (The leave-one-out check, fixed before the run according to the author's dated records, which are not part of this release, drops 101-102 alone and also gives MAP PRESENT.) The chip publishes no per-pair figures, so the test cannot say whether the map adds anything beyond them.
3. **The gap between the best and worst pairs persisted when their neighbours were idle** (Kickoff 32; ibm_fez at 13:17 UTC, ibm_kingston at 13:23 UTC). The six pairs that kept the most and the six that kept the least were run again, once with all 27 pairs active and once with no two active pairs coupled. The gap between the two groups did not close when the neighbours were idle: the closed fraction was 0.01 on ibm_fez (90% interval −0.21 to 0.21) and 0.03 on ibm_kingston (−0.09 to 0.16). The result rules out crowding by the tested neighbours as the cause; it does not separate the two-qubit gate from single-qubit control, readout or drift. The sealed rule's verdict on both is named THE GATE; here that name means "not explained by the tested neighbours".
4. **On ibm_fez, choosing pairs by the map gave 35.6% less error on unrelated random circuits than choosing by the published error rates** (Kickoff 33; 15:20 UTC). Gain in fidelity G = +0.0012, 90% interval +0.0004 to +0.0021; verdict USEFUL. **On ibm_kingston (15:23 UTC), 16% less, not statistically settled**: G = +0.0004 (+0.0001 to +0.0008), but the map's partial correlation with the workload, after removing the published score, was 0.29 (p = 0.073), short of the rule's 0.3 and p < 0.05. Verdict: NOT SETTLED.
5. **The rule can say no** (Kickoff 36, a simulation of the noise model Cirq publishes for Google's willow_pink, run on a laptop; not a measurement of any device). When every difference between pairs came from the published figures, the rule called the map NOISE: those differences were too small to repeat above shot noise. When a per-pair error was planted outside the published figures, the rule found it (DIAGNOSTIC).
6. **On the Rigetti processor, a pair's level depends on the program that measures it, not on the hour** (Kickoff 37; Rigetti Cepheus-1-108Q, through Open Quantum, 6 October 2026; first wave 00:45 to 02:22 UTC, second wave 11:31 to 11:35 UTC). Two programs from Kickoff 34b were sent again, unchanged: the main job's 27-pair program and the 53-pair screen, which contains the same 27 pairs. Each program agreed with itself: r = 0.997 to 0.998 minutes apart, 0.97 (27-pair) and 0.76 (53-pair) across about 9 hours, and 0.99 and 0.98 against its own Kickoff 34b run the day before. The two programs did not agree with each other on the 27 pairs they share: r = 0.07 in the first wave and −0.25 in the second, when all three tasks ran within 3 minutes. Verdict, by a rule fixed before the run according to the author's dated records: PLACEMENT, read as "the levels depend on the program". Kickoff 38 (6 October 2026, 13:42 to 13:46 UTC) then sent a third program that measures the 53-pair program's 106 qubits but runs only the 27-pair program's gates: it read like the 27-pair program (r = 0.99) and not like the 53-pair one (r = −0.15), so what moves the levels is the program's gate graph, not which qubits it measures (verdict ACTIVITY). Kickoff 40 then ran named pairs on the same processor through Amazon Braket, where the compiled program returned with each task shows where each pair ran, and found that neither of Kickoff 37's programs had run its pairs on the named qubits (r = −0.18 and 0.24 against the pinned levels). The levels depended on the program because the program's gates decided where the pairs went. The second wave was planned two hours after the first and ran nine hours after it, so the two-hour question was not tested.
7. **On ibm_fez, a map of the whole chip held for two days** (Kickoff 35; all 176 coupled pairs in 3 rounds, one job a day on 5, 6 and 7 October 2026 at 17:02, 14:56 and 14:21 UTC, across two daily recalibrations). The map from Day 3 correlates with Day 1 at r = 0.86 (0.89 after correcting for each day's own repeatability), and 9 of the 18 worst pairs on Day 1 were still among the 18 worst on Day 3, exactly the rule's bar of 50%. Verdict: HOLDS, under the rule fixed before the run and under its amendment. The decile condition is met with no margin, and a repeat could as easily have read PARTIAL; the correlations are the solid part. Four pairs that IBM lists at a two-qubit error of 1.0 ran, and three of them carry the most extreme values on the chip; without all four the corrected correlation from Day 1 to Day 3 is 0.74. On Day 2 both pairs on one qubit fell sharply and recovered on Day 3, while IBM's figures for them did not move. IBM's published score is steadier day to day than the map (r = 0.99) and does not predict it (r between 0.07 and −0.07).
8. **On the Rigetti processor, with placement pinned, the map is DIAGNOSTIC** (Kickoff 40; Rigetti Cepheus-1-108Q through Amazon Braket, 6 October 2026, 15:17 to 15:50 UTC; Kickoff 34b's 27 named pairs). Through this route each program names its physical qubits inside a verbatim box, and the compiled program returned with each task shows every pair on its named qubits; a pair's level was the same with 27 pairs running or with half of them (d = 0.99), so the reading is PINNED. On the 23 working pairs with published figures, the map repeated (r = 0.97), carried over to circuit B (r = 0.81) and was not explained by Rigetti's figures (r = 0.20): DIAGNOSTIC, the first such verdict beyond IBM. The payoff on the same day was NOT SETTLED for the kept share; beside it, choosing by the plain level (the no-offset P(11)) gave 31% less error than choosing by the published figures. The between-pair spread is large here (SD of k 1.1, against 0.2 on Kickoff 31's ibm_fez pairs), and a few pairs carry negative k, where the offset circuit goes wrong.
9. **The pinned Rigetti map lasted a day, and the day-old level chose better pairs** (Kickoff 41; the same programs re-sent on 7 October 2026, 15:05 to 15:58 UTC, 23 to 24 hours after Kickoff 40). The kept share correlated with the previous day's at r = 0.85 (0.61 without the two extreme pairs) and the plain level at r = 0.80: HOLDS. Choosing 8 pairs by the previous day's plain level gave 27% less error on the random workload than choosing by Rigetti's figures read that day (G = +0.0122, 90% interval +0.0077 to +0.0168): USEFUL. The whole gain is one pair: Rigetti's figures rated 94-95 sixth best of 23, and it was the worst on the workload; the two picks otherwise tie. The previous day's kept share was NOT SETTLED, as on the day before. Dead pairs changed between the days: 18-19 was back, 72-73 and 76-77 were gone.
10. **On the Rigetti processor, a pair's response to a particular program repeats a day later, and a smooth shift of the offset does not describe it** (Kickoff 42; the same pairs, pinned, circuit A at nine offsets and circuit B at nine, 6 October 2026 at 17:46 UTC and 7 October at 16:17 UTC). The ideal curve shifted and scaled fits fewer than one pair in ten within twice the shot noise, and the fitted shift does not explain the kept share (r = +0.24). What repeats is each pair's pattern over the 18 programs: pooled r = 0.85 a day later, median per-pair r = 0.98, with two pairs at 0.04. Pair 94-95 has a dip at exactly the designed offset rather than a moved peak; pair 11-12 read about 0.3 higher on the same seven programs on both days, and 72-73 read 0.21 higher on the first day and 0.11 on the second. The fitted shifts also repeat once the pairs whose fit ran to the grid's edge are set aside (r = 0.72 for A, 0.90 for B; HOLDS under the amended rule, PARTIAL under the original). This is the evidence behind the sentence that a map is a map for one family of circuits.

Beside every verdict, Manacitra also reports the headline statistics without the pairs a vendor has flagged as not measured or not working (an IBM two-qubit error of exactly 1.0; a Braket CZ fidelity of exactly 0.5, its placeholder for no figure). The verdict still counts every pair that runs, as the kickoffs fixed it. On ibm_fez, three of the four flagged edges carried the most extreme k on the chip, and k is not a kept fraction for a pair whose no-offset level is far below the ideal 0.96: these four read 0.19 to 0.39, against a median of 0.89 on the chip.

**What it has not shown:**

- **How long a map lasts beyond two days.** On ibm_fez a whole-chip map held for two days (finding 7); on the Rigetti processor a pinned map held for one (finding 9). Neither has been measured over a week. Through Open Quantum, where placement is not recorded, a fixed program's levels held over about 9 hours and a day (Kickoff 37), but its pair names did not locate the physical qubits that ran (finding 6).
- **Why some pairs respond to particular programs on the Rigetti processor.** Kickoff 42 found the response and found that it repeats; it did not identify a cause. Coherent error that depends on the single-qubit frame is the ordinary explanation and is not tested here.
- **Whether the kept share chooses better pairs on the Rigetti processor.** Twice NOT SETTLED (findings 8 and 9). The plain level did, both times. On ibm_fez the kept share did and the level was not tested as a chooser.

What would discredit the map: a NOISE verdict (it does not repeat), a REDUNDANT verdict (the published figures already carry it), NOT USEFUL (it picks no better pairs), or FADES (it does not last long enough to plan by).

## Limits

- **One circuit family.** Every map comes from one encoded four-site Hamiltonian, at two strengths of its diagonal coupling (circuits A and B). Other circuits might order the pairs differently.
- **Three processors, three days.** The hardware results are from ibm_fez and ibm_kingston, and from Rigetti Cepheus-1-108Q through Open Quantum and through Amazon Braket, all on 5 to 7 October 2026.
- **Two routes to one processor.** The Rigetti findings through Open Quantum (2, 6) and through Amazon Braket (8 to 10) are from the same processor, but only the Braket route records where each pair ran. The difference between them is a difference between the two platforms' placement records, not between the vendors' machines.
- **Small absolute differences.** The gap is 0.038 in P(11), and the payoff is about a tenth of a percentage point of fidelity on the random workload.
- **No claim about any device's design.** A pair's kept share is a measurement of what it did with these circuits; it says nothing about why, or about how the processor was built.

The long version, including the three rules with their thresholds and how to reproduce the numbers here, is in [`docs/index.md`](docs/index.md).

## How the results were made: kickoffs

Every result above came from a kickoff: a written brief, fixed before a run (according to the author's dated records, which are not part of this release). A brief states:

- the question;
- the exact circuits, and how pairs are chosen;
- the shot counts;
- the analysis;
- the verdict rule, with every threshold;
- the cost or time cap;
- what goes in the hand-back.

![A vertical timeline of seven numbered steps, one line under each. 1, Brief: the question and every rule, fixed in writing. 2, Sealed predictions: hashed and timed before any data exist. 3, Go: the author approves each submission in chat. 4, Run: each job is sent once, never resubmitted. 5, Hand-back: code, data, a report and checksums. 6, Independent check: the results recomputed with separate code. 7, Scorecard: every prediction marked; nothing edited. A note below: a rule changes only by a dated amendment, before the data it governs are seen, and the original rule is still reported beside the new one.](docs/diagrams/kickoff.svg)

The practices below are as the author's dated records describe them; those records are not part of this release. From this release on, new commitments can be checked by anyone with `manacitra seal` and, once signing is on, a public timestamp; the runs published here cannot be checked that way.

- **Predictions are sealed before the run.** The AI that carries out the kickoff writes its own predictions and records their hash and time before any data exist. The author's predictions are kept separately, unseen by the runner. Both are marked afterwards and never edited.
- **Every submission needs a go.** Nothing goes to hardware without the author's go for that submission, given in chat. Each job is submitted once and never resubmitted.
- **The hand-back is checked independently.** The runner returns code, data, a report and checksums. The results are then rechecked with separate code, and a scorecard marks every prediction and records the verdict.
- **Changes are written down.** If a rule has to change, it changes by a dated amendment, before the data it governs are seen, and the original rule is still reported beside the new one.
- **The rules were tested too.** Kickoff 36 tested the rules themselves, on a simulated chip where the right answers were set in advance.

| kickoff | question | platform | verdict | data, in `data/` |
|---|---|---|---|---|
| 31, 5 October 2026 | Does each pair keep its own share, and does the share repeat? | ibm_fez, ibm_kingston | DIAGNOSTIC on both | `ibm_fez/k31-map.json`, `ibm_kingston/k31-map.json`, with the settling runs (`k29-settle.json`) |
| 32, 5 October 2026 | Does the gap between pairs persist when their neighbours are idle? | ibm_fez, ibm_kingston | THE GATE on both (not explained by the tested neighbours) | `ibm_fez/k32-isolation.json`, `ibm_kingston/k32-isolation.json` |
| 33, 5 October 2026 | Does choosing pairs by the map do better on unrelated work? | ibm_fez, ibm_kingston | USEFUL on ibm_fez; NOT SETTLED on ibm_kingston | `ibm_fez/k33-payoff.json`, `ibm_kingston/k33-payoff.json`, `workload/k33-workload.json` |
| 34, 5 October 2026 | Does the map exist on a second vendor's chip? | Rigetti Cepheus-1-108Q, through Open Quantum | closed at the test; replaced by 34b | none |
| 34b, 5 October 2026 | The same question, with a screening run to choose the pairs first | Rigetti Cepheus-1-108Q, through Open Quantum | MAP PRESENT | `rigetti_cepheus_1_108q/` |
| 35, 5 to 7 October 2026 | How long does a map of the whole chip last? | ibm_fez | HOLDS over two days (the decile condition exactly on its bar) | `ibm_fez/k35-day1.json` to `k35-day3.json`, `k35-persistence.json`, `k35-layout.json` |
| 36, 5 October 2026 | Can the rule say no? | a simulation of the noise model Cirq publishes for willow_pink, run on a laptop | NOISE without a planted map; DIAGNOSTIC with one | `simulated/` |
| 37, 6 October 2026 | Did the Rigetti levels change between runs because of the program or because of time? | Rigetti Cepheus-1-108Q, through Open Quantum | PLACEMENT (the levels depend on the program; they held over about 9 hours) | `rigetti_cepheus_1_108q/k37-placement.json` |
| 38, 6 October 2026 | Do the Rigetti levels follow the program's measured footprint or its gate activity? | Rigetti Cepheus-1-108Q, through Open Quantum | ACTIVITY (the gate graph decides; the measured footprint does not) | `rigetti_cepheus_1_108q/k38-activity.json`, `k38-P53i-A-no.qasm` |
| 40, 6 October 2026 | With placement pinned, is the Rigetti map DIAGNOSTIC, and does it choose better pairs? | Rigetti Cepheus-1-108Q, through Amazon Braket | PINNED; DIAGNOSTIC; payoff NOT SETTLED (the plain level beside it, 31% less error) | `rigetti_cepheus_1_108q/k40-*.json`, `compiled/k40/` |
| 41, 7 October 2026 | Does the pinned map last a day, and does the day-old level choose better pairs? | Rigetti Cepheus-1-108Q, through Amazon Braket | HOLDS; the level USEFUL (27% less error, one pair); the kept share NOT SETTLED | `rigetti_cepheus_1_108q/k41-*.json`, `compiled/k41/` |
| 42, 6 to 7 October 2026 | Do the weak pairs have their own best offset, and does it last? | Rigetti Cepheus-1-108Q, through Amazon Braket | SPREAD, MIXED, DOES NOT; the per-program pattern HOLDS a day later | `rigetti_cepheus_1_108q/k42-*.json`, `compiled/k42/` |

The kickoff texts and the sealed predictions are kept and dated, and are not part of this release.

Kickoffs were written by Anish Patel with an AI assistant and carried out by AI coding agents; the hardware submissions were each approved by him.

## Install and try it

Manacitra needs Python 3.11 or later. It is not yet on PyPI. There are two ways to install it.

**From a clone, editable: the route for reproducing the published numbers.** The archived dataset in `data/` comes
with the clone and is found automatically.

```bash
git clone https://github.com/dogmaguru/manacitra.git
cd manacitra
pip install -e ".[aer]"
```

**As a plain package**, with `pip install ".[aer]"` from a clone or `pip install "git+https://github.com/dogmaguru/manacitra"`. This installs the package only: the dataset is not in the wheel. The simulator and the backends work without it. Anything that reads the archive needs a clone's `data/` folder: the reproductions, examples 2 and 3, and `manacitra verdict` on an archived run. Point at it in one of two ways:

```bash
export MANACITRA_DATA=/path/to/manacitra/data
```

```bash
manacitra --data /path/to/manacitra/data verdict ibm_fez/k31-map.json
```

Without either, Manacitra stops and says how to get the data. In a plain install, the tests that need it are skipped, with that reason.

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

Extras: `[ibm]` for IBM Quantum, `[aer]` for Qiskit Aer, `[docs]` for the diagrams; `[openquantum]` and `[cirq]` are experimental. `[openquantum]` is limited to the SDK versions every adapter call was checked against (openquantum-sdk 0.4.3 and later 0.4 releases), and the adapter stops at import if the installed SDK lacks the two private methods it calls. On Open Quantum, a pair named in a program is not the physical pair: Kickoff 40 showed that the same named pairs, sent through a route that records placement, ran on other qubits than Open Quantum's programs had used. Use a map there only with the exact program that measured it, and read its pair names as labels. Placement cannot be pinned, because the platform's preprocessing breaks the provider's verbatim mode. The command line is `manacitra map | pick | verdict | persist | report`, and it is a dry run unless `--submit` is given.

**Before anything is sent to a provider:** the estimate and the ledger entry are printed; a job already sent once is refused unless `--allow-resubmit` (in Python, `allow_resubmit=True`) is given, and that is logged, whether it is sent from the command line or through a backend's `submit()`; the check and the reservation are made under one lock that every process shares, so two commands started together cannot both send one job; on Open Quantum, the balance, the quote and the budget across waves are checked again immediately before sending, and the balance floor counts every credit reserved on the account and not yet settled; on IBM the usage is read, and the job is refused if the usage plus the estimates of jobs not yet counted plus this one would pass a cap (540 s of the 600 s window by default); and any transpiled circuit without exactly three CZ on every pair is refused. Credentials come only from each provider's own saved account, never from this repository.

## How to cite

Please cite the software and, if you use them, the data, using [`CITATION.cff`](CITATION.cff):

> Patel, A. (2026). *Manacitra: a map of a quantum processor's qubit pairs* (version 0.1.0) [Software and data]. https://github.com/dogmaguru/manacitra

## Licence

The code is licensed under the Apache License 2.0 ([`LICENSE`](LICENSE), [`NOTICE`](NOTICE)). The data in `data/` and the documentation in `docs/` are licensed under Creative Commons Attribution 4.0 ([`data/LICENSE`](data/LICENSE), [`docs/LICENSE`](docs/LICENSE)). The copyright holder is Dogma LLC (Dogma Guru).

Manacitra is developed by Anish Patel and published by Dogma Guru.
