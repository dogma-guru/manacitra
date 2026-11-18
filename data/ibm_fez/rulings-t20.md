# Test 20: the author's rulings

Received in chat on 16 November 2026 (UTC), recorded by the runner at 2026-11-16T23:17:47Z, before the go and before any circuit was built. No data of this test existed. The author states that none changes the rule's text, a word or a threshold.

1. **The shuffled job: job 1 is supplied.** The scorer as delivered and hashed names a job of test 7's form in that place, and the A26 reading is defined on test 7's design. The README's prose is silent, not contrary. If job 1 does not run or gives no usable per span weights, no shuffled job is supplied. Job 1's fits carry `span_readings_A26.weight_per_span`, one weight per span, computed as amendment A26 computed them.

   The lines the ruling rests on, as delivered (`sandhi-v41-scorer/`, checked against `FORECAST-SHA256SUMS`; the README is the model's hand-back README, beside it):
   - `README.md`, line 40: "For D1, supply two monitor jobs; for D2, supply one. Paths below are placeholders for the future run. Add a shuffled job and its fits only when available."
   - `README.md`, lines 46 and 47: `--shuffled future-job1,shots-job1.npz,shots-job1-meta.json,counts-job1.json` and `--shuffled-fits future-job1,fits-future.json`.
   - `README.md`, line 52: "A26 weights are read from the supplied fits, and the undefined observed population sd remains unavailable."
   - `score_model_01_v4_1.py`, line 7 (its usage line): `--shuffled day3-job1,shots1.npz,meta1.json,counts1.json`; test 11 day 3's job 1 was test 7's design.
   - `calibration_v4_1.py`, lines 149 to 166 (`read_a26`): the weight is read from `span_readings_A26.weight_per_span`, the row whose `span` matches, its `weighted_mean`.

2. **One bet, not two.** `shuffled_weight_A26` is scored if ruling 1's conditions are met. `shuffled_sd` is reported as not scored, with the scorer's line 217 named as the reason: the scorer sets it unavailable whatever is supplied ("C3 supplies A26 weight but the v4 definition gives a distribution of population lengths, not one observed scalar; no unique observed sd is defined"). The scorer is not edited.

3. **The date is a UTC date.** The go will be given after 00:00 UTC and will name 17 November 2026. The past midnight clause stands as written.

4. **No cycle, no bar.** Received in chat on 16 November 2026 (UTC), recorded by the runner at 2026-11-16T23:37:34Z, before any circuit was built. The author's words: "“No cycle, no bar” applies to test 20 as it did to test 19. With no stamp in the 48 hours at which T1 changed on more than half the qubits, no cycle is in progress and the clause does not hold a job. The check is made before each of the three jobs, as the rule says. If such a stamp appears between jobs, the clause applies from that stamp as written: no submission until 30 minutes after the next stamp at which CZ errors changed on more than half the edges. The past-midnight clause covers that wait."

   How the runner applies it: before each job, at submission, the cycle check compares ibm_fez's properties read then with the last snapshot of the 48 hour walk. If T1 changed on more than half the qubits since the walk, the submission is refused, the walk is run again, and the clause applies from that stamp as written.
