# Data

The archived runs behind the README's measured statistics, one JSON file per run. Licensed CC BY 4.0 ([`LICENSE`](LICENSE));
please cite the repository ([`CITATION.cff`](../CITATION.cff)).

Every JSON record has a `meta` block with the same six fields, filled by the kind of file, and "not applicable" where a
field does not apply (`tests/test_data_meta.py` checks this):

- **Run records** (the IBM, Rigetti and simulated runs): the processor, the provider, the kickoff it came from, the
  UTC time the job ran, the shots per circuit, and the SHA-256 of each source file it was copied from (the source
  files are the author's run records, not in this repository).
- **Coupling maps** (topology only): the processor and provider; the snapshot they were read from (the package, its
  version and the class), the SHA-256 of the snapshot's source file, and the time they were extracted. No kickoff, run
  time or shots.
- **Inputs with no shots** (`simulated/k36-planted.json`, the planted angles; `workload/k33-workload.json`, the
  workload's ideal distributions): no shots, and the workload has no processor or provider.

The counts are as the provider returned them; the analyses the original runs wrote are kept under `archived`,
untouched, so `tests/test_reproduction.py` can recompute every statistic from the counts and compare. Times here and in
the README are rounded to the nearest minute.

| file | what | processor | kickoff | UTC | shots per circuit | IBM job ID | source files (SHA-256) |
|---|---|---|---|---|---|---|---|
| `ibm_fez/coupling-map.json` | coupling map, topology only | ibm_fez | not applicable | not applicable (extracted 2026-10-06 00:42) | not applicable |  | qiskit-ibm-runtime 0.50.0 offline snapshot (FakeFez): `fez/conf_fez.json` (`74e356537d86…`) |
| `ibm_fez/k29-settle.json` | settling run: circuit A, three variants, P(11) only (no counts archived) | ibm_fez | Kickoff 29 (settling run) | 2026-10-05 02:24 | 4000 | `db1gkmeegvvc73bhjkd0` | `settle-results.json` (`35aa9c5332bb…`), `settle-submit.json` (`a3ab8899ce5b…`) |
| `ibm_fez/k31-map.json` | the map: circuits A and B, 18 circuits, counts | ibm_fez | Kickoff 31 (the map) | 2026-10-05 12:37 | 8000 | `db1pjp6egvvc73bi00m0` | `results-31-ibm_fez.json` (`a756b0a4a413…`), `submit-31-ibm_fez.json` (`f621a2fce473…`), `robustness-31.json` (`e3d96aada436…`) |
| `ibm_fez/k32-isolation.json` | alone or crowded: dense and spread conditions, counts | ibm_fez | Kickoff 32 (alone or crowded) | 2026-10-05 13:17 | 8000 | `db1q6k6egvvc73bi0qug` | `results-32-ibm_fez.json` (`ac9f3aa70d39…`), `submit-32-ibm_fez.json` (`2e6aadc776eb…`) |
| `ibm_fez/k33-payoff.json` | the payoff: readout calibration, circuit A, 8 random circuits, counts | ibm_fez | Kickoff 33 (the payoff) | 2026-10-05 15:20 | 8000 | `db1rp0rid5ic73eriu3g` | `results-33-ibm_fez.json` (`926a3388e90d…`), `submit-33-ibm_fez.json` (`c928cc5f28a8…`) |
| `ibm_fez/k35-layout.json` | Kickoff 35: the 176 edges in 3 rounds of disjoint pairs, fixed on Day 1, and the offline dry run | ibm_fez | Kickoff 35 | 2026-10-05 17:01 | 4000 |  | `layout-35.json` (`31213ed00521…`), `dryrun-35.json` (`4b38f8bf23f4…`) |
| `ibm_fez/k35-day1.json` | Kickoff 35, Day 1: all 176 edges, circuit A, 12 circuits in the mirror order, counts | ibm_fez | Kickoff 35 | 2026-10-05 17:02 | 4000 | `db1tg5n2iglc7396ikjg` | `results-35-day1.json` (`de7ada9772a4…`), `submit-35-day1.json` (`9a8673dc751c…`) |
| `ibm_fez/k35-day2.json` | Kickoff 35, Day 2: as Day 1, counts | ibm_fez | Kickoff 35 | 2026-10-06 14:56 | 4000 | `db2gnu68v0ts73c2qd40` | `results-35-day2.json` (`5ec09c83dd98…`), `submit-35-day2.json` (`79b3187d3fce…`) |
| `ibm_fez/k35-day3.json` | Kickoff 35, Day 3: as Day 1, counts | ibm_fez | Kickoff 35 | 2026-10-07 14:21 | 4000 | `db35ao7r11fs7397rv90` | `results-35-day3.json` (`15f1d578aef5…`), `submit-35-day3.json` (`3218b367a275…`) |
| `ibm_fez/k35-persistence.json` | Kickoff 35 across the three days: the correlations, the decile overlaps, the verdict under the original rule and Amendment A1, and descriptive checks computed after seeing the data | ibm_fez | Kickoff 35 | 2026-10-05 17:02, 2026-10-06 14:56 and 2026-10-07 14:21 | 4000 |  | `across-35.json` (`d5bfb6554540…`), `a1-35.json` (`01761dbbf492…`), `robustness-35.json` (`cf47f38d4d69…`) |
| `ibm_kingston/coupling-map.json` | coupling map, topology only | ibm_kingston | not applicable | not applicable (extracted 2026-10-06 00:42) | not applicable |  | qiskit-ibm-runtime 0.50.0 offline snapshot (FakeKingston): `kingston/conf_kingston.json` (`9947a3cf6902…`) |
| `ibm_kingston/k29-settle.json` | settling run: circuit A, three variants, P(11) only (no counts archived) | ibm_kingston | Kickoff 29 (settling run) | 2026-10-05 12:14 | 4000 | `db1p77megvvc73bhvghg` | `settle-results-ibm_kingston.json` (`20c61aaf9b2b…`), `settle-submit-ibm_kingston.json` (`6f244b7277c7…`) |
| `ibm_kingston/k31-map.json` | the map: circuits A and B, 18 circuits, counts | ibm_kingston | Kickoff 31 (the map) | 2026-10-05 12:38 | 8000 | `db1pkfrid5ic73erg7cg` | `results-31-ibm_kingston.json` (`8e6078ba5ceb…`), `submit-31-ibm_kingston.json` (`4560a3e8490f…`), `robustness-31.json` (`e3d96aada436…`) |
| `ibm_kingston/k32-isolation.json` | alone or crowded: dense and spread conditions, counts | ibm_kingston | Kickoff 32 (alone or crowded) | 2026-10-05 13:23 | 8000 | `db1q7deegvvc73bi0rpg` | `results-32-ibm_kingston.json` (`025680a47f71…`), `submit-32-ibm_kingston.json` (`1c54024e4e4a…`) |
| `ibm_kingston/k33-payoff.json` | the payoff: readout calibration, circuit A, 8 random circuits, counts | ibm_kingston | Kickoff 33 (the payoff) | 2026-10-05 15:23 | 8000 | `db1s1davog1s73fij0qg` | `results-33-ibm_kingston.json` (`f6137d1e175a…`), `submit-33-ibm_kingston.json` (`b8695fdc8080…`) |
| `rigetti_cepheus_1_108q/screen.json` | the screen: L_s for each of 53 candidate pairs, and the pair rule's outcome (no counts) | Rigetti Cepheus-1-108Q, through Open Quantum, Public plan | Kickoff 34b | 2026-10-05 17:27 to 18:55 | 8000 |  | `screen-34b.json` (`4a5533e36e94…`), `pairs-34b.json` (`ec96db2515a3…`), `submit-34b.json` (`e34a2f658b69…`), `run.log` (`99f1769e32ad…`) |
| `rigetti_cepheus_1_108q/main.json` | the map: circuits A and B, 16 circuits, counts; the dead-pair filter, the analysis, the sealed leave-one-out, the descriptive lines | Rigetti Cepheus-1-108Q, through Open Quantum, Public plan | Kickoff 34b | 2026-10-05 22:15 to 22:29 | 8000 |  | `results-34b.json` (`3ee41a9a61fe…`), `robustness-34b.json` (`2f4ceb72b7a3…`), `after-the-fact-34b.json` (`ce900fe414f6…`), `submit-34b.json` (`e34a2f658b69…`), `run.log` (`99f1769e32ad…`) |
| `rigetti_cepheus_1_108q/after-the-fact.json` | the 20-pair check without 13-14 and 101-102: computed after seeing the data, outside the verdict | Rigetti Cepheus-1-108Q, through Open Quantum, Public plan | Kickoff 34b | 2026-10-05 22:15 to 22:29 | 8000 |  | `after-the-fact-34b.json` (`ce900fe414f6…`) |
| `rigetti_cepheus_1_108q/k37-placement.json` | placement or drift: two fixed Kickoff 34b programs (27 and 53 pairs), three tasks per wave, two waves, counts; the measures, the verdict, the gap, the run order and the descriptive lines | Rigetti Cepheus-1-108Q, through Open Quantum, Public plan | Kickoff 37 | 2026-10-06 00:45 to 11:35 | 8000 |  | `results-37.json` (`46718ab11dc5…`), `submit-37.json` (`84fc6574fc3d…`), `programs-37.json` (`fe978a47c719…`), and the six `raw/output-*.json` files (each SHA-256 in `meta`) |
| `rigetti_cepheus_1_108q/k37-after-the-fact.json` | checks on Kickoff 37 computed after seeing the data, outside the verdict | Rigetti Cepheus-1-108Q, through Open Quantum, Public plan | Kickoff 37 | 2026-10-06 00:45 to 11:35 | 8000 |  | `after-the-fact-37.json` (`c3c8bc0379ac…`) |
| `rigetti_cepheus_1_108q/k38-activity.json` | footprint or activity: P53i (P53's qubits, P27's gates), P27 and P53, four tasks in one wave, counts; the P53i builder's checks, the measures, the verdict and the descriptive lines | Rigetti Cepheus-1-108Q, through Open Quantum, Public plan | Kickoff 38 | 2026-10-06 13:42 to 13:46 | 8000 |  | `results-38.json` (`c0fbddad67cc…`), and the 5 raw result files (each SHA-256 in `meta`) |
| `rigetti_cepheus_1_108q/k40-pairs.json` | Kickoff 40's 27 pairs (Kickoff 34b's by name), the coupling-map comparison, x and the placeholder rule at discovery | Rigetti Cepheus-1-108Q, through Amazon Braket, pinned | Kickoff 40 | 2026-10-06 15:07 | not applicable |  | `pairs-40.json` (`9156756bcfcb…`) |
| `rigetti_cepheus_1_108q/k40-placement.json` | stage 1, placement: X, Y, Y', X (circuit A without the offset), counts and measured qubits; c, d, the records check on each compiled program, the reading | Rigetti Cepheus-1-108Q, through Amazon Braket, pinned | Kickoff 40 | 2026-10-06 15:17 to 15:35 | 8000 |  | `results-40-1.json` (`91d03439ca02…`), and the 4 raw result files (each SHA-256 in `meta`) |
| `rigetti_cepheus_1_108q/k40-map.json` | stage 2, the map: circuits A and B, 18 circuits, counts and measured qubits; the dead-pair filter, the statistics, the verdict, the sealed leave-one-out, the line against Kickoff 34b, the records check | Rigetti Cepheus-1-108Q, through Amazon Braket, pinned | Kickoff 40 | 2026-10-06 15:41 to 15:44 | 8000 |  | `results-40-2.json` (`2570522a2814…`), and the 18 raw result files (each SHA-256 in `meta`) |
| `rigetti_cepheus_1_108q/k40-after-the-fact.json` | stage 2's verdict set without 42-43 and 94-95: computed after seeing the data, outside the verdict | Rigetti Cepheus-1-108Q, through Amazon Braket, pinned | Kickoff 40 | 2026-10-06 15:41 to 15:44 | 8000 |  | `after-the-fact-40-2.json` (`d1aa2b692bde…`) |
| `rigetti_cepheus_1_108q/k40-payoff.json` | stage 3, the payoff: readout calibration, circuit A, the 8 random circuits, counts and measured qubits; W, the correlations, picks and gains on the pairs with x, the verdict, the records check | Rigetti Cepheus-1-108Q, through Amazon Braket, pinned | Kickoff 40 | 2026-10-06 15:49 to 15:50 | 8000 |  | `results-40-3.json` (`26e5852992cd…`), and the 28 raw result files (each SHA-256 in `meta`) |
| `rigetti_cepheus_1_108q/k40-ideal.json` | the ideal values of circuits A and B, and the 8 random circuits' ideal distributions (Kickoff 33's circuits, the same seed) | Rigetti Cepheus-1-108Q, through Amazon Braket, pinned | Kickoff 40 | 2026-10-06 14:57 | not applicable |  | `ideal-40.json` (`69c3f1e5d95a…`) |
| `rigetti_cepheus_1_108q/k40-figures.json` | Braket's per-pair figures at each stage's submission, the placeholder counts and the calibration times | Rigetti Cepheus-1-108Q, through Amazon Braket, pinned | Kickoff 40 | 2026-10-06 15:17 | not applicable |  | `figures-at-submission-40.json` (`7c725f212b1d…`) |
| `rigetti_cepheus_1_108q/k41-map.json` | Part A, the map a day later: Kickoff 40's stage 2 programs re-sent, counts and measured qubits; today's map, the persistence measures against Kickoff 40, the verdict, the records check | Rigetti Cepheus-1-108Q, through Amazon Braket, pinned | Kickoff 41 | 2026-10-07 15:05 to 15:46 | 8000 |  | `results-41-A.json` (`a4d6f3570fb1…`), and the 18 raw result files (each SHA-256 in `meta`) |
| `rigetti_cepheus_1_108q/k41-payoff.json` | Part B, the payoff with the day-old scores: calibrations and one copy of each random circuit, counts and measured qubits; W, the level's and the kept share's lines, the same-day ceiling, the records check | Rigetti Cepheus-1-108Q, through Amazon Braket, pinned | Kickoff 41 | 2026-10-07 15:58 | 8000 |  | `results-41-B.json` (`4073c3c8cd4b…`), and the 12 raw result files (each SHA-256 in `meta`) |
| `rigetti_cepheus_1_108q/k41-figures.json` | Braket's per-pair figures at each part's submission, and each program's SHA-256 against Kickoff 40's | Rigetti Cepheus-1-108Q, through Amazon Braket, pinned | Kickoff 41 | 2026-10-07 15:06 | not applicable |  | `figures-at-submission-41.json` (`6da49586eb38…`), `programs-41.json` (`93dfd6f2fa00…`) |
| `rigetti_cepheus_1_108q/k42-day1.json` | the offset scan, Day 1: circuit A at nine offsets and B at nine, counts and measured qubits; P(11), the fits, V1 to V3, the records check | Rigetti Cepheus-1-108Q, through Amazon Braket, pinned | Kickoff 42 | 2026-10-06 17:46 to 17:47 | 8000 |  | `results-42-day1.json` (`89bf94e0f296…`), and the 18 raw result files (each SHA-256 in `meta`) |
| `rigetti_cepheus_1_108q/k42-day2.json` | the offset scan, Day 2: as Day 1, with V4 under both rules, V5, the switch and the line against Kickoff 41 | Rigetti Cepheus-1-108Q, through Amazon Braket, pinned | Kickoff 42 | 2026-10-07 16:17 to 16:18 | 8000 |  | `results-42-day2.json` (`e83078394142…`), and the 18 raw result files (each SHA-256 in `meta`) |
| `rigetti_cepheus_1_108q/k42-after-the-fact.json` | Day 1 without the fits at the grid's edge, and the programs shared with Kickoff 40: computed after seeing the data, outside the verdicts | Rigetti Cepheus-1-108Q, through Amazon Braket, pinned | Kickoff 42 | 2026-10-06 17:46 to 17:47 | 8000 |  | `after-the-fact-42-day1.json` (`602ff20c1758…`) |
| `rigetti_cepheus_1_108q/k42-ideal.json` | the exact P(11) of circuits A and B at each scan offset, and the synthesised programs' agreement with it | Rigetti Cepheus-1-108Q, through Amazon Braket, pinned | Kickoff 42 | 2026-10-06 17:21 | not applicable |  | `ideal-42.json` (`2bb2afbe919d…`) |
| `rigetti_cepheus_1_108q/k42-figures.json` | Braket's per-pair figures at each day's submission; the task order (seed 42) and each program's SHA-256 and checks | Rigetti Cepheus-1-108Q, through Amazon Braket, pinned | Kickoff 42 | 2026-10-06 17:46 | not applicable |  | `figures-at-submission-42.json` (`8a6321c60ee0…`), `programs-42.json` (`e6614fb7c024…`) |
| `simulated/k36-arm1.json` | simulated: published figures only (arm 1), counts | willow_pink (simulated) | Kickoff 36 (can the method say no?) | 2026-10-05 18:35 | 8000 |  | `results-36-arm1.json` (`ae51bb5f09a8…`) |
| `simulated/k36-arm2.json` | simulated: plus a planted map (arm 2), counts | willow_pink (simulated) | Kickoff 36 (can the method say no?) | 2026-10-05 18:35 | 8000 |  | `results-36-arm2.json` (`47ce0c225c81…`) |
| `simulated/k36-arm3.json` | simulated: the QVM's own noise model (arm 3), counts | willow_pink (simulated) | Kickoff 36 (can the method say no?) | 2026-10-05 18:35 | 8000 |  | `results-36-arm3.json` (`994078d11c32…`) |
| `simulated/k36-persistence.json` | simulated: three days, static and scrambled | willow_pink (simulated) | Kickoff 36 (can the method say no?) | 2026-10-05 18:35 | 4000 |  | `persistence-36.json` (`b8f2aa8e2a56…`) |
| `simulated/k36-planted.json` | simulated: the planted angles | willow_pink (simulated) | Kickoff 36 (can the method say no?) | 2026-10-05 18:35 | not applicable |  | `planted-36.json` (`d5909071bcdc…`) |
| `workload/k33-workload.json` | the 8 random workload circuits: unitaries and ideal distributions | not applicable | Kickoff 33 (the payoff) | 2026-10-05 14:58 | not applicable |  | `ideal-33.json` (`4920266b130a…`) |

All IBM runs but Kickoff 35, and Kickoff 34b's Rigetti run, are from 5 October 2026; Kickoff 35 ran once a day on 5, 6 and 7 October; Kickoffs 37, 38 and 40 are from 6 October, Kickoff 41 from 7 October, and Kickoff 42 from 6 and 7 October. Every Kickoff 35 file and every Rigetti file's `meta` block also gives the SHA-256 of the whole hand-back archive. The Rigetti processor was reached by two routes: through Open Quantum (Kickoffs 34b, 37 and 38), where placement is not recorded, and through Amazon Braket (Kickoffs 40, 41 and 42), where each program names its physical qubits inside one verbatim box and the compiled program returned with each task shows where each pair ran. The processor column says which. Beside the JSON files, `rigetti_cepheus_1_108q/k37-P27-A-no.qasm` and `k37-P53-A-no.qasm` are the two programs Kickoff 37 sent, exactly as sent; they are Kickoff 34b's main-job "A no" program and its screen program, byte for byte, and their SHA-256 values are also in `k37-placement.json`'s `meta`. Kickoff 38 sent them again, with a third, `k38-P53i-A-no.qasm`, as sent. For the Amazon Braket runs, `rigetti_cepheus_1_108q/programs/k40/` (by stage) and `programs/k42/` hold the programs as sent (Kickoff 41 re-sent Kickoff 40's files; `k41-figures.json` gives each file's SHA-256), and `compiled/k40/`, `compiled/k41/` and `compiled/k42/` hold the compiled program Amazon Braket returned with each task, exactly as returned, one per task: these are the placement records. `meta` blocks belong to the JSON records; the program files (`.qasm`, `.quil`) are data too, under [`LICENSE`](LICENSE), and [`PROGRAMS.md`](PROGRAMS.md) indexes every one of them: the run and task it belongs to, the processor and route, the task's UTC times and shots, and its SHA-256, generated from the run records by `tools/program_catalogue.py`. The simulated files are a local simulation of the noise model that Cirq
publishes for willow_pink (median calibration of 16 August 2024): they are not a measurement of any device.

## Formats

Every record with `counts` declares how to read them in `meta.bit_reading`, one of four values, and the package refuses
a record that declares none: `qiskit-adjacent` (the IBM files), `openquantum-reversed` (the Open Quantum files),
`braket-measured-qubits` (the Amazon Braket files) and `per-pair` (the simulations). Each is described below. Where a
record's positions or tasks do not all measure the same pairs, `meta.bit_reading_note` says how they are laid out; a
Braket map names its figures record in `meta.figures_file` (and `meta.figures_part`).

- **IBM counts** (`counts` in the `k31`, `k32` and `k33` files): one dict per circuit position, as Qiskit returns them.
  The rightmost character is classical bit 0; pair *i* is measured into bits 2*i* (its first qubit) and 2*i* + 1 (its
  second). In `k32-isolation.json` each position measures only that condition's active pairs, in the order of
  `selection.dense_pairs` (condition D) or `selection.groups` (S1, S2).
- **Rigetti counts** (`counts` in `rigetti_cepheus_1_108q/main.json`): one plain dict per circuit position, as the platform returned it, with 54-character keys. Pair *i* is measured into classical bits *i* (its first qubit) and 53 − *i* (its second), and classical bit *k* is the character at position 53 − *k* of the key. The main job ran as 16 tasks in two waves of 8; the UTC times are in `meta`. No calibration snapshot was returned, so there is no published score and the map rule is capped at MAP PRESENT.
- **Rigetti counts, Kickoff 37** (`counts` in `rigetti_cepheus_1_108q/k37-placement.json`): one plain dict per task, keyed by the task's label (`wave1-T1` to `wave2-T3`), as the platform returned it. The same reading with n = 54 (P27) or 106 (P53): pair *i* is in classical bits *i* and n − 1 − *i*, and classical bit *k* is the character at position n − 1 − *k* of the n-character key. Each task's creation and completion time is in `meta`.
- **ibm_fez, Kickoff 35** (`counts` in `ibm_fez/k35-day*.json`): 12 circuits a day, each measuring one round of up to
  60 disjoint pairs (`rounds`, R1 to R3), in the mirror order of `order`. The Qiskit reading: the rightmost character
  is classical bit 0, and pair *i* of the circuit's round is measured into bits 2*i* (its first qubit) and 2*i* + 1.
- **Rigetti counts, Kickoff 38** (`counts` in `k38-activity.json`): one plain dict per task (T1 to T4), in Kickoff 37's
  reading, with n = 54 (P27) or 106 (P53, P53i).
- **Rigetti counts, Amazon Braket** (`counts` in the `k40`, `k41` and `k42` files): one plain dict per task, as Amazon
  Braket returned it, with the task's `measured_qubits` in `tasks`. Character *j* of a key belongs to
  `measured_qubits[j]`. A pair's two-outcome state is *s* = *q0* + 2 *q1*, *q0* being the pair's first qubit (the low
  bit), as in Kickoff 33. The pair's published score is x = (1 − CZ fidelity) + (1 − readout fidelity) of each qubit,
  from Braket's standardized device properties at submission; a CZ fidelity of exactly 0.5 is the platform's
  placeholder and means no published figure (x is None).
- **Simulated counts** (`k36-arm*.json`): per circuit, per pair, a dict over `00`, `01`, `10`, `11`, the first character
  being the pair's first qubit.
- **Published figures** (`published_at_submission`): per pair, the two-qubit error, both readout errors, T1 and T2, the
  score x = two-qubit error + both readout errors, and the dates IBM gave for them, as read at submission.
- **Order**: `order` lists the circuit at each position. A, B: the two test circuits; `no`, `off`, `wrong`: no offset,
  the offset, the offset with the wrong sign. `R1` to `R8`: the random workload circuits. `CAL ab`: readout calibration.
- **Job IDs**: the eleven IBM `meta.job_id` values (the "IBM job ID" column above) stay, on purpose. They are
  provenance, kept since the first release, and they are not credentials or account identifiers. The Open Quantum task
  IDs and the Amazon Braket task ARNs were left out and stay out.

**Recomputing Kickoff 33's payoff on ibm_fez** (`ibm_fez/k33-payoff.json`; finding 4's 35.6%) from the raw counts
takes four things the record does not spell out:
- **The prior map is Kickoff 32's dense condition** (`ibm_fez/k32-isolation.json`, the positions with all 27 pairs
  active), not `k31-map.json`. Per pair, it is the mean P(11) of the "off" positions minus that of the "no" positions.
- **The workload's counts are pooled.** Each random circuit, R1 to R8, ran at two positions, and the two are pooled
  per pair (16,000 shots) before the fidelity.
- **The fidelity** is the squared Hellinger overlap, (Σ √(p_s q_s))², against `circuits[j].ideal` in
  `workload/k33-workload.json`. The state order is s = q0 + 2 q1, and the counts are uncorrected. A pair's W is its
  mean over the eight circuits, and its error is 1 − W.
- **The published pick** uses the x recorded in `published_at_submission`, lowest first. The map's pick is the eight
  highest prior values.

`python examples/03_pick_pairs.py` makes both picks. The map's pick is 106-107, 88-89, 151-152, 94-95, 142-143,
129-130, 13-14, 114-115. The published figures' pick is 22-23, 5-6, 85-86, 70-71, 114-115, 123-124, 142-143,
106-107. The mean error is 0.00221 for the map's pick and 0.00343 for the published pick, 35.6% less. These values
come from `tests/_independent_readings.py` (`k33_payoff`), which does not import the package.

## Checksums and signatures

`SHA256SUMS` holds a plain SHA-256 of every file here, for catching corrupted files (`python tools/sha256sums.py
--check`). Signing has been on since 7 October 2026: each file has a Sigstore bundle beside it (`FILE.sigstore.json`),
which shows who published it and when, and a file that changes is signed again when the change lands on `main`.
`docs/index.md` gives the command to verify one.

## What was changed when copying

Nothing in the counts or the analyses. From IBM's usage blocks, the `details` list was dropped, because it carries
IBM's internal metric identifier; the charged seconds and status are kept. From Kickoff 34b, left out: the provider task IDs, the credit balances, the raw provider records, the programs as sent, the screen's counts, and the runner's sealed predictions and its report. From Kickoff 37, left out: the provider task IDs, the credit balances and quotes, the raw provider records and the platform's processed copies, the preparations, and the runner's predictions and its report, including the report's carried sentence. The programs as sent are copied, because the identifier scan passed on them. From Kickoff 35, left out: the plots, the runner's predictions and report, its cross-check with Kickoff 36's code and that script (the cross-check is a fact for the build report), and the usage records beyond each job's charged seconds; from each day's usage block, the `details` list. From Kickoff 38, left out: the task IDs, the credit balances and quotes, the raw provider records and the platform's processed copies, the preparations, the self-test, the plot, and the runner's predictions and report, with its carried sentence. From Kickoffs 40, 41 and 42, left out: the task ARNs and everything else from the submission records (each run's figures file carries the figures, placeholder counts and calibration times copied from them, without ARNs), the cost records and quotes, the discovery records, the runners' predictions and reports, the plots, and the unredacted copies of the compiled programs, which were never in the hand-back archives; no redaction was needed. The labels "computed after seeing the data", "leans, outside the verdict" and Kickoff 41's "a ceiling a user holding yesterday's map would not have" were added beside the archived blocks they describe; nothing archived was changed. Before any Amazon Braket file was copied, the identifier scan gained patterns for Amazon resource names, bucket addresses, account numbers and access keys, and passed on every copied file. In `main.json`, the across-run correlations on the 11 pairs shared by the test task, the screen and the main job keep the source's label: they were computed after seeing the data. The source folders' names are not recorded.
