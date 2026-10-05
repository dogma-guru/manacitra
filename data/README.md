# Data

The archived runs behind every number in the README, one JSON file per run. Licensed CC BY 4.0 ([`LICENSE`](LICENSE));
please cite the repository ([`CITATION.cff`](../CITATION.cff)).

Every file has a `meta` block: the processor, the UTC time the job ran, the shots per circuit, the kickoff it came from,
and the SHA-256 of each source file it was copied from (the source files are the author's run records, not in this
repository). The counts are as the provider returned them; the analyses the original runs wrote are kept under
`archived`, untouched, so `tests/test_reproduction.py` can recompute every statistic from the counts and compare.

| file | what | processor | kickoff | UTC | shots per circuit | IBM job ID | source files (SHA-256) |
|---|---|---|---|---|---|---|---|
| `ibm_fez/coupling-map.json` | coupling map, topology only | ibm_fez |  |  |  |  | qiskit-ibm-runtime 0.50.0 offline snapshot (FakeFez) |
| `ibm_fez/k29-settle.json` | settling run: circuit A, three variants, P(11) only (no counts archived) | ibm_fez | Kickoff 29 (settling run) | 2026-10-05 02:24 | 4000 | `db1gkmeegvvc73bhjkd0` | `settle-results.json` (`35aa9c5332bb…`), `settle-submit.json` (`a3ab8899ce5b…`) |
| `ibm_fez/k31-map.json` | the map: circuits A and B, 18 circuits, counts | ibm_fez | Kickoff 31 (the map) | 2026-10-05 12:36 | 8000 | `db1pjp6egvvc73bi00m0` | `results-31-ibm_fez.json` (`a756b0a4a413…`), `submit-31-ibm_fez.json` (`f621a2fce473…`), `robustness-31.json` (`e3d96aada436…`) |
| `ibm_fez/k32-isolation.json` | alone or crowded: dense and spread conditions, counts | ibm_fez | Kickoff 32 (alone or crowded) | 2026-10-05 13:17 | 8000 | `db1q6k6egvvc73bi0qug` | `results-32-ibm_fez.json` (`ac9f3aa70d39…`), `submit-32-ibm_fez.json` (`2e6aadc776eb…`) |
| `ibm_fez/k33-payoff.json` | the payoff: readout calibration, circuit A, 8 random circuits, counts | ibm_fez | Kickoff 33 (the payoff) | 2026-10-05 15:20 | 8000 | `db1rp0rid5ic73eriu3g` | `results-33-ibm_fez.json` (`926a3388e90d…`), `submit-33-ibm_fez.json` (`c928cc5f28a8…`) |
| `ibm_kingston/coupling-map.json` | coupling map, topology only | ibm_kingston |  |  |  |  | qiskit-ibm-runtime 0.50.0 offline snapshot (FakeKingston) |
| `ibm_kingston/k29-settle.json` | settling run: circuit A, three variants, P(11) only (no counts archived) | ibm_kingston | Kickoff 29 (settling run) | 2026-10-05 12:14 | 4000 | `db1p77megvvc73bhvghg` | `settle-results-ibm_kingston.json` (`20c61aaf9b2b…`), `settle-submit-ibm_kingston.json` (`6f244b7277c7…`) |
| `ibm_kingston/k31-map.json` | the map: circuits A and B, 18 circuits, counts | ibm_kingston | Kickoff 31 (the map) | 2026-10-05 12:38 | 8000 | `db1pkfrid5ic73erg7cg` | `results-31-ibm_kingston.json` (`8e6078ba5ceb…`), `submit-31-ibm_kingston.json` (`4560a3e8490f…`), `robustness-31.json` (`e3d96aada436…`) |
| `ibm_kingston/k32-isolation.json` | alone or crowded: dense and spread conditions, counts | ibm_kingston | Kickoff 32 (alone or crowded) | 2026-10-05 13:23 | 8000 | `db1q7deegvvc73bi0rpg` | `results-32-ibm_kingston.json` (`025680a47f71…`), `submit-32-ibm_kingston.json` (`1c54024e4e4a…`) |
| `ibm_kingston/k33-payoff.json` | the payoff: readout calibration, circuit A, 8 random circuits, counts | ibm_kingston | Kickoff 33 (the payoff) | 2026-10-05 15:22 | 8000 | `db1s1davog1s73fij0qg` | `results-33-ibm_kingston.json` (`f6137d1e175a…`), `submit-33-ibm_kingston.json` (`b8695fdc8080…`) |
| `simulated/k36-arm1.json` | simulated: published figures only (arm 1), counts | willow_pink (simulated) | Kickoff 36 (can the method say no?) | 2026-10-05 18:34 | 8000 |  | `results-36-arm1.json` (`ae51bb5f09a8…`) |
| `simulated/k36-arm2.json` | simulated: plus a planted map (arm 2), counts | willow_pink (simulated) | Kickoff 36 (can the method say no?) | 2026-10-05 18:34 | 8000 |  | `results-36-arm2.json` (`47ce0c225c81…`) |
| `simulated/k36-arm3.json` | simulated: the QVM's own noise model (arm 3), counts | willow_pink (simulated) | Kickoff 36 (can the method say no?) | 2026-10-05 18:34 | 8000 |  | `results-36-arm3.json` (`994078d11c32…`) |
| `simulated/k36-persistence.json` | simulated: three days, static and scrambled | willow_pink (simulated) | Kickoff 36 (can the method say no?) | 2026-10-05 18:34 | 4000 |  | `persistence-36.json` (`b8f2aa8e2a56…`) |
| `simulated/k36-planted.json` | simulated: the planted angles | willow_pink (simulated) | Kickoff 36 (can the method say no?) | 2026-10-05 18:34 |  |  | `planted-36.json` (`d5909071bcdc…`) |
| `workload/k33-workload.json` | the 8 random workload circuits: unitaries and ideal distributions | none | Kickoff 33 (the payoff) | 2026-10-05 14:58 |  |  | `ideal-33.json` (`4920266b130a…`) |

All IBM runs are from 5 October 2026. The simulated files are a local simulation of the noise model that Cirq
publishes for willow_pink (median calibration of 16 August 2024): they are not a measurement of any device.

## Formats

- **IBM counts** (`counts` in the `k31`, `k32` and `k33` files): one dict per circuit position, as Qiskit returns them.
  The rightmost character is classical bit 0; pair *i* is measured into bits 2*i* (its first qubit) and 2*i* + 1 (its
  second). In `k32-isolation.json` each position measures only that condition's active pairs, in the order of
  `selection.dense_pairs` (condition D) or `selection.groups` (S1, S2).
- **Simulated counts** (`k36-arm*.json`): per circuit, per pair, a dict over `00`, `01`, `10`, `11`, the first character
  being the pair's first qubit.
- **Published figures** (`published_at_submission`): per pair, the two-qubit error, both readout errors, T1 and T2, the
  score x = two-qubit error + both readout errors, and the dates IBM gave for them, as read at submission.
- **Order**: `order` lists the circuit at each position. A, B: the two test circuits; `no`, `off`, `wrong`: no offset,
  the offset, the offset with the wrong sign. `R1` to `R8`: the random workload circuits. `CAL ab`: readout calibration.

## What was changed when copying

Nothing in the counts or the analyses. From IBM's usage blocks, the `details` list was dropped, because it carries
IBM's internal metric identifier; the charged seconds and status are kept. The source folders' names are not recorded.
