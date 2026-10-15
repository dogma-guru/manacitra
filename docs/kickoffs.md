# How the results were made: kickoffs

Every result in the [findings](findings.md) came from a kickoff: a written brief, fixed before a run (according to the author's dated records, which are not part of this release). A brief states:

- the question;
- the exact circuits, and how pairs are chosen;
- the shot counts;
- the analysis;
- the verdict rule, with every threshold;
- the cost or time cap;
- what goes in the hand-back.

![A vertical timeline of seven numbered steps, one line under each. 1, Brief: the question and every rule, fixed in writing. 2, Sealed predictions: hashed and timed before any data exist. 3, Go: the author approves each submission in chat. 4, Run: each job is sent once, never resubmitted. 5, Hand-back: code, data, a report and checksums. 6, Independent check: the results recomputed with separate code. 7, Scorecard: every prediction marked; nothing edited. A note below: a rule changes only by a dated amendment, before the data it governs are seen, and the original rule is still reported beside the new one.](diagrams/kickoff.svg)

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
| 41, 7 October 2026 | Does the pinned map last a day, and does the day-old level choose better pairs? | Rigetti Cepheus-1-108Q, through Amazon Braket | HOLDS; the level USEFUL (27% less error, dominated by one pair); the kept share NOT SETTLED | `rigetti_cepheus_1_108q/k41-*.json`, `compiled/k41/` |
| 42, 6 to 7 October 2026 | Do the weak pairs have their own best offset, and does it last? | Rigetti Cepheus-1-108Q, through Amazon Braket | SPREAD, MIXED, DOES NOT; the per-program pattern HOLDS a day later | `rigetti_cepheus_1_108q/k42-*.json`, `compiled/k42/` |
| 43, 10 October 2026 | Does placing reuse circuits by the map beat Qiskit's calibration-based placement? With Amendment A1, fixed before the run: a chain scores each coupler's distance from k = 1, not 1 − k | ibm_fez | USEFUL FOR REUSE (mostly the map's chains avoiding qubit 143); the map's own verdict NOT SETTLED (circuit A only) | `ibm_fez/k43-map.json`, `ibm_fez/k43-reuse.json` (the circuits by source and SHA-256; `tools/fetch_reuse_circuits.py` fetches them) |
| 44, 10 October 2026 | Are a reset and a mid-circuit measurement worse on the qubits where Kickoff 43's reuse circuits failed? | ibm_fez | NOT SUPPORTED; the probe DIAGNOSTIC | `ibm_fez/k44-reset.json` |
| 45, 10 October 2026 | Does the collapse repeat, and do idle loss or repeated retirements explain it? | ibm_fez | the collapse REPEATS; idle loss SUPPORTED by its rule, carried by one qubit; repeated retirement NOT SUPPORTED | `ibm_fez/k45-collapse.json` |
| 46, 10 October 2026 | Is qubit 143 disturbed when its neighbours are retired? | ibm_fez | no fixed pattern holds; a neighbour's retirement NOT SUPPORTED | `ibm_fez/k46-middle.json` |
| 47, 10 October 2026 | Does phase build up on 143 while it waits, and do refocusing pulses save the circuit? | ibm_fez | H_phase SUPPORTED (refocusing restored the circuit); the loss on 143 REFOCUSABLE | `ibm_fez/k47-wait.json` |
| 48, 11 October 2026 | Does a qubit's Ramsey loss, measured at the circuit's own wait length, predict how much a reuse-shaped circuit loses when that qubit waits in it? | ibm_fez | AGREE, informative (three of five chains); 143's loss REFOCUSABLE again | `ibm_fez/k48-wait-test.json` (the circuits built by `manacitra.wait` at `f28642a`, which rebuilds them) |
| 49, 13 October 2026 | Does finding 14's rule hold on a second day, unchanged? | ibm_fez | DISAGREE (144's d_M entirely above +0.15); the rule held on 143, 142 and 124; 143's loss REFOCUSABLE again | `ibm_fez/k49-wait-test.json` (the circuits built by `manacitra.wait` at `a55354d`, which rebuilds them); the rule, `ibm_fez/k49-rule.md` |
| 50, 13 October 2026 | Does what the waiting qubit's neighbours do change how much phase it loses? | ibm_fez | NOT SUPPORTED (Kickoff 49's gap not present today); neighbours in the excited state added 0.25 to 0.35 of loss; their readout alone added none | `ibm_fez/k50-neighbour-test.json`; the rule, `ibm_fez/k50-rule.md` |
| 51, 13 October 2026 | With a known phase added, does the wait test see a different effective offset from an idle-neighbour Ramsey? | ibm_fez | SUPPORTED on 144; the design nearly blind on 143 | `ibm_fez/k51-known-offset.json`; the rule, `ibm_fez/k51-rule.md` |
| 52, 13 October 2026 | With the phase swept all the way round, does the wait test's effective offset differ from an idle-neighbour Ramsey's? | ibm_fez | DIFFERENT on 143 and on 144; the active-neighbour Ramsey closer on both | `ibm_fez/k52-phase-sweep.json`; the rule, `ibm_fez/k52-rule.md` |
| 53, 13 October 2026 | Does the revised check, with an active-neighbour Ramsey, predict the wait test on chains it has never run on? | ibm_fez | AGREE (five informative cells); the original check would have given DISAGREE | `ibm_fez/k53-revised-check.json` (with the chain draw); the rule, `ibm_fez/k53-rule.md` |
| 54, 15 October 2026 | Does the revised check hold on a second day, on the same six chains, built by the code under review? | ibm_fez | AGREE (seven informative cells); the original check would have given DISAGREE; one neighbour at a time, the shifts added up and the 143-144 pair gave the same shift from either end | `ibm_fez/k54-revised-check-day-2.json` (with the first submission, cancelled in the queue, and the record between the two); the rule, `ibm_fez/k54-rule.md` |
| 55, 14 October 2026 | Does the revised check hold on a second processor, on chains drawn by the same procedure? | ibm_kingston | DISAGREE (one of four informative cells); the original check would have given DISAGREE on all four | `ibm_kingston/k55-revised-check.json` (with the chain draw and the window); the rule, `ibm_kingston/k55-rule.md` |
| 56, 14 and 15 October 2026 | On finding 20's three chains, how far does the wait test's offset sit from the active-neighbour Ramsey's (the leftover), measured by a six-phase sweep? | ibm_kingston | LARGE on 7, NOT SETTLED on 43, SMALL on 18; the lean positive on all three | `ibm_kingston/k56-phase-sweep.json`; the rule, `ibm_kingston/k56-rule.md` |
| 57, 15 October 2026 | Does the check pass on new chains when it is run at the phase where the active-neighbour Ramsey's loss is greatest, fixed by a sweep in a first job? | ibm_kingston | AGREE (four cells at the peak phase, every one informative); the check at +90° AGREE beside it | `ibm_kingston/k57-peak-check.json` (with the chain draw and the peaks); the rule, `ibm_kingston/k57-rule.md` |
| 58, 15 October 2026 | On finding 20's chains, is the check's residual smaller at the peak phase than at +90°? | ibm_kingston | PEAK SMALLER on 7 and 43; NOT SEPARATED on 18, whose leftover is zero | `ibm_kingston/k58-placement-comparison.json` (with the peaks); the rule, `ibm_kingston/k58-rule.md` |
| 59, 15 October 2026 | Does the check at the peak phase pass on a second calibration day, on four more new chains? | ibm_kingston | AGREE (four cells at the peak phase, every one informative) | `ibm_kingston/k59-peak-check-day-2.json` (with the chain draw and the peaks); the rule, `ibm_kingston/k59-rule.md` |
| 60, 15 October 2026 | The check at the peak phase on a second processor, with the chains drawn on the published readout | ibm_fez | stopped at the draw: no candidate chain survived the published readout screen; no job | `ibm_fez/k60-draw-stopped.json`; the rule, `ibm_fez/k60-rule.md` |
| 61, 15 October 2026 | On finding 21's sixteen qubits, does the readout error measured directly agree with the published one? | ibm_fez | PUBLISHED NOT READABLE (thirteen of sixteen qubits INCONSISTENT, every one measured below its published value) | `ibm_fez/k61-readout-check.json`; the rule, `ibm_fez/k61-rule.md`, and its superseded version 1, `ibm_fez/k61-rule-v1-superseded.md` |
| 62, 15 October 2026 | Does the check at the peak phase pass on a second processor, with the chains drawn on a survey of every qubit's measured readout? | ibm_fez | AGREE (four cells at the peak phase, every one informative); the check at +90° AGREE beside it | `ibm_fez/k62-peak-check.json` (with the survey, the chain draw and the peaks); the rule, `ibm_fez/k62-rule.md` |

The kickoff texts and the sealed predictions are kept and dated, and are not part of this release.

Kickoffs were written by Anish Patel with an AI assistant and carried out by AI coding agents; the hardware submissions were each approved by him.

Back to the [README](../README.md).
