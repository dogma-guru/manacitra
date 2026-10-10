# The idea in six pictures

## 1. The kept share

![Two circuits on one pair of qubits, identical except for their single-qubit gates, shown as two rows of boxes joined by the same three CZ gates. Beside them, three pairs of dots on a P(11) axis: the exact model's outcomes, 0.962 without the offset and 1.000 with it, a gap of 0.038; ibm_fez pair 106-107, 0.923 and 0.963, a gap of 0.040, k = 1.06; ibm_fez pair 20-21, 0.824 and 0.833, a gap of 0.008, k = 0.22.](diagrams/kept-share.svg)

The two circuits encode a four-site Hamiltonian in two qubits; the offset makes the transfer from 00 to 11 exact, so the model's P(11) moves from 0.962 to 1.000. On ibm_fez on 5 October 2026, pair [106, 107] moved by 0.040, slightly more than the model's 0.038 (k = 1.06). Pair [20, 21] moved by 0.008 (k = 0.22): the same gates, the same difference in angles, and most of the difference was gone. Both pairs ran in the same job, with 32,000 shots per variant each. (A PNG version of every diagram sits beside the SVG in `docs/diagrams/`.)

## 2. The map

![ibm_fez's heavy-hex coupling map with 27 pairs drawn as segments shaded from light blue (kept least, k = 0.22) to dark blue (kept most, k = 1.06), each also drawn thicker the more it kept and numbered by its rank (1 = kept most), and other couplers in light grey. Beside it, a smaller copy of the same map with the same 27 pairs shaded by IBM's published error score, from light (highest error, 0.021) to dark (lowest error, 0.011). The two shadings differ pair by pair.](diagrams/chip-map.svg)

The left map is ibm_fez's 27 pairs from Kickoff 31 (5 October 2026, 12:37 UTC), each coloured by its kept share. Each pair is also drawn thicker the more it kept, and numbered by its rank; every pair's k, x and ranks are in [a table](diagrams/chip-map-table.md). The small map on the right colours the same pairs by the published score x (the pair's two-qubit error plus both qubits' readout errors, as IBM reported them at submission). Dark means better on both. The two pictures order the pairs differently: across these 27 pairs, k and x correlate at r = −0.18.

## 3. The three checks

![Three scatter plots of ibm_fez's 27 pairs from Kickoff 31, each answering one question of the map rule, with its correlation and threshold above it. 1, does it repeat: k from one half of the runs against k from the other half, beside a dashed line of equal values; r = 0.87, needs at least 0.5, passes. 2, does it carry over: k on circuit A against k on circuit B; r = 0.82, p below 1 in 10,000, needs at least 0.4 with p below 0.05, passes. 3, is it already in the published score: k against IBM's published error score x; r = −0.18, needs |r| below 0.5, and the A-to-B correlation with x removed is 0.82, needs at least 0.3, passes. The title gives the verdict: DIAGNOSTIC.](diagrams/three-checks.svg)

The verdict comes from three checks on the same map. It must repeat: each half of the runs, 16,000 shots per variant per pair, gives nearly the same k (r = 0.87). It must carry over to a second circuit with a different gap (r = 0.82). And it must not be what the published score already says: k barely follows x (r = −0.18), and the carry-over survives with x taken out (r = 0.82). All three pass on ibm_fez, so the verdict is DIAGNOSTIC; a map that fails the first is NOISE, and one that x explains is REDUNDANT.

## 4. The pipeline

![Four boxes in a row joined by arrows: Map (in: 16 short circuits on a set of non-overlapping qubit pairs at once (27 in the published runs); every coupler on a chip can be covered in a few rounds; out: k per pair), Verdict (in: k from two circuits, split halves, published x; out: NOISE, REDUNDANT, DIAGNOSTIC, MAP PRESENT or NOT SETTLED), Pick (in: the map; out: the n pairs whose kept share is closest to the ideal of 1, ranked without checking the verdict), Run, drawn dashed (your own job, run by you on the picked pairs, not by Manacitra). A dashed note above the Map box says that, according to the author's dated records, which are not part of this release, the rules and predictions were sealed before each map job was sent.](diagrams/pipeline.svg)

Map, then verdict, then pick, then run. The verdict says whether the map is worth using at all: a map that does not repeat is NOISE, and a map the published figures already explain is REDUNDANT. Manacitra computes the map and the verdict; `manacitra pick` ranks pairs from the map and does not check the verdict, though it warns when the verdict is not DIAGNOSTIC or MAP PRESENT; and you run your own job. `manacitra pick --by level` ranks by the plain level instead, which chose better pairs on the Rigetti processor where the kept share did not (findings 8 and 9). On an archived file, `pick`, `verdict` and `report` read the counts by the bit reading the file declares (`meta.bit_reading`: IBM's, Open Quantum's or Amazon Braket's), refuse a file that declares none, and give the verdict and statistics of that run's own analysis; a Braket map's published score comes from the figures file it names. In the author's own use, the rules and a set of predictions were written down and hashed before each job was sent, according to the author's dated records, which are not part of this release. From this release on, new commitments can be checked by anyone with `manacitra seal` and, once signing is on, a public timestamp; the runs published here predate this release and cannot be checked that way.

Which to rank by: the kept share chose better pairs on ibm_fez and was not settled on ibm_kingston; the plain level, each pair's mean P(11) on circuit A without the offset, chose better pairs on the Rigetti processor, on the same day and a day later, where the kept share did not (Kickoffs 33, 40 and 41). On every payoff run both scores were scored against the published figures: on IBM the kept share was the primary test and the level a reference line; on Rigetti the reverse; no run has yet compared the two scores against each other under a rule fixed in advance. The dead-pair filter uses the run's own levels, never a list from an earlier day: on the Rigetti processor, dead pairs came and went between consecutive days (18-19 came back; 72-73 and 76-77 went).

Distance from the ideal (Amendment A15). k = 1 is the ideal: a pair that kept exactly the circuit's gap. `manacitra pick` ranks the kept share by its distance from it, |1 − k|, smallest first, after the dead-pair filter. A k well above 1 marks a pair whose two circuits are being pulled apart by an error, not one that kept more, as Kickoff 35's whole-chip maps of ibm_fez show: on Days 2 and 3 the usable pair with the highest k was 33-34, at k 4.52 and 4.66, with a plain level of 0.51 and 0.52. The published Kickoff 33 pick was made highest first, from a prior map whose largest k is 1.07; in that range the two rules differ by one pair (106-107 under highest first, 22-23 under |1 − k|), whose distances from 1 differ by 0.003 against a shot noise of about 0.05 in each. `--by kept-share-highest` reproduces Kickoff 33's rule.

## 5. The payoff

![A scatter of 27 ibm_fez pairs: the kept share measured about two hours earlier on the horizontal axis, and fidelity on eight random two-qubit circuits on the vertical axis. The 8 pairs with the highest kept share are filled blue; the 8 with the lowest published error are ringed in orange; some pairs carry both. Dashed lines mark each pick's mean: error 0.0022 for the map's pick and 0.0034 for the published pick. The title reads: choosing by the map, 35.6% less error than choosing by the published rates.](diagrams/payoff.svg)

On ibm_fez on 5 October 2026, the map measured at 13:17 UTC chose 8 pairs, and the published error rates chose another 8. At 15:20 UTC all 27 pairs ran eight random circuits, unrelated to the map, with nine CZ gates each. The map's 8 pairs had a mean error of 0.0022 against 0.0034 for the published pick: 35.6% less. The absolute numbers are small, because every pair's fidelity was above 0.98.

## 6. How to check a sealed prediction

![A timeline of four steps. 1, seal and post the hash (manacitra seal): shows the file existed then, without showing what it says. 2, run the job: the file stays as it was. 3, reveal the salt (manacitra reveal): publishes the file and its salt. 4, anyone verifies (manacitra verify): a match shows the predictions came before the results.](diagrams/sealed-prediction.svg)

This one is for a stranger who wants to know whether the predictions came before the results. `manacitra seal` commits to a file with a salted SHA-256 hash, which is posted somewhere the producer cannot edit; after the run, `manacitra reveal` publishes the salt, and `manacitra verify` lets anyone check that the file is the one committed to. Once the repository is public, a CI workflow also signs every commit record and every data file with Sigstore's keyless signing, which records who signed and when in a public log ([`docs/index.md`](index.md#9-sealing-and-signing)).

```bash
manacitra seal predictions.md      # before the run: prints the hash to post; the salt stays in .seals/
manacitra reveal predictions.md    # after the run: writes the salt into predictions.md.commit.json
manacitra verify predictions.md    # anyone, with the file and its commit record: MATCH
printf 'x' >> predictions.md && manacitra verify predictions.md   # one byte changed: NO MATCH, exit status 1
```

The commit record shows that the file existed when its hash was posted; it does not show when that was. The time
comes only from where the hash was posted (the record's own `sealed_utc` is the sealing machine's clock).

Back to the [README](../README.md).
