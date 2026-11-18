# Test 20: qubit 143 on ibm_fez on a fifth date: the scan, two monitors, and the desk model's first design a second time (rule, fixed before any job is built)

Status: draft for the author's review, 14 November 2026. Once approved, this file is renamed `t20-rule.md`. It is then hashed, the hash is posted in a public issue, and the file is published unchanged with the run. Its per-shot read is fixed here too, before any job runs.

## 1. The questions

The record of qubit 143 on ibm_fez covers four dates, 16, 17, 19 and 21 October 2026. The last scan across waits ran on 19 October; the last monitors ran on 21 October (test 18).

1. **After three weeks and more, is 143 still two fixed frequencies, and at what split and weight?** Test 7's rule on a new date, as test 11's job 1 ran it.
2. **Does its state behave as on the record?** Test 18's two monitor jobs again at the 5.6 µs wait: per span, the sharing, duty, τ_c and boundary words under test 15's definitions.
3. **Does the desk model's first design hold on a second run?** Sandhi version 4.1 posted its bets for design D1 in issue 68, before test 17. Test 18 scored them once. This test scores the same posted bets on a later run.
4. **The two D1 bets that need a shuffled job** (`shuffled_weight_A26`, `shuffled_sd`) have not been scored. They are scored here only if the scorer accepts the scan as that job (section 6).

No cause is named for any sharing, switching, difference or shape.

## 2. The jobs

**Settings for every job:**

- dynamical decoupling, gate twirling and measurement twirling off;
- no readout error mitigation;
- qubit 143 alone, every other qubit idle in |0⟩.

Each job is submitted once. A failed, cancelled or refused job is recorded and not resubmitted.

**On the Open Plan instance, named in the go by its saved name, in the private record only.**

- **Job 1, the scan:** test 7's rule as written and hashed on 16 October (`t7-rule.md`), as test 11's job 1 ran it.
  - 64 waits, 0 to 63 µs, X and Y at each, and the two readout circuits: 130 circuits.
  - Each run as 2 copies of 1,500 shots, interleaving seed 20301.
  - The same fits; the bootstrap of 2,000 draws with seed 20304; the same verdict.
- **Job 2, the monitor:** test 18's job 1 exactly, which is test 11's job 2.
  - 300 circuits: the two readout circuits, 148 repeats of X then Y at 5.6 µs, the two readout circuits.
  - 1,000 shots each; submitted in that order, not interleaved.
  - **The wait is 5.6 µs, fixed.** It is not changed by job 1's result. The wait that job 1's split would give is reported beside it.
- **Job 3, the monitor again:** the same circuits rebuilt, submitted as soon as job 2's result is fetched.

**R0, for the weight per repeat:**

- if job 1 runs and returns TWO FIXED FREQUENCIES, R0 is job 1's P fit at 5.6 µs;
- otherwise R0 is 0.4770, as test 18 used it, and the weight series carries that caveat.

**The estimates:**

- job 1: the measured rate per shot of the most recent job of the same design in the hand-back folder (test 11 day 3's job 1) times 390,000 shots;
- jobs 2 and 3: test 18's measured monitor, 82 s each;
- each with the half-again margin.

**The allowance, and which job gives way.** The remaining allowance is read and recorded, with the UTC time, before each job, in the private record.

- If, before job 1, the allowance covers all three estimates with their margins, all three run in order.
- If it covers the two monitors with their margins but not the scan as well, **the scan is not run.** That is recorded, R0 is 0.4770, and question 1 reports no verdict.
- If it covers less than the two monitors, job 2 runs alone if its own estimate with the margin is covered, and is read as test 18's rule reads a single job. Otherwise nothing is submitted and the record says so.
- After job 1, each later job is submitted only if its estimate with the margin is within the allowance read before it.

**For every job:**

- the published stamps of the previous 48 hours, and the window, as test 7's rule states; no job goes in inside ibm_fez's computed calibration window or while the day's cycle is in progress;
- the structural checks of test 12's rule, on the circuits as built and on the backend's snapshot: every instruction on 143; the gate sequence and the scheduled wait; the noiseless P(1) as the circuit's form requires; the positions in the rule's order;
- the decision recorded before the build;
- the result's execution metadata saved with the counts at fetch;
- after each fetch, the per-shot results fetched as test 13's `fetch_t13.py` does, and every array file's SHA-256 recorded in a hashes-before-analysis file before any reading runs.

**Past midnight.** The go covers a job submitted after 23:59 UTC of its date if the hold is for the day's cycle or the stamp. The wait and its cause are recorded, and the date stays the go's.

## 3. The analysis from the counts

**Job 1:** test 7's analysis and verdict, as test 11's rule states them for its job 1.

- The verdict is read as **CONFIRMED ON THE FIFTH DATE** if TWO FIXED FREQUENCIES, else **NOT CONFIRMED ON THE FIFTH DATE**.
- δ, b and their intervals are set beside those of 16, 17 and 19 October.
- The per-span weights, and the copies check split by span, are computed as amendment A26 computed them.

**Jobs 2 and 3:**

- test 12's steps 1 to 10, at 1,000 shots, 148 repeats and the R0 of section 2;
- test 11's phase and weight words per job, and test 12's level word;
- test 11's pooled words over the two jobs, and the phase difference across the gap between them, reported beside.

Test 11's bets on Model 01 version 2 are not read.

**If the lines have moved.** If job 1 is NOT CONFIRMED, or its split 2δ differs from 89.6 kHz by more than 9 kHz, the report states that 5.6 µs is no longer the antiphase wait of the qubit as measured that day. Every word of jobs 2 and 3 is still computed and reported, with that note. The note is not a verdict and changes no word.

## 4. The per-shot read

For jobs 2 and 3, test 15's definitions apply unchanged: its rule, sections 4 to 7, with test 13's whole repeats and quadrature of record.

- **Per span:** the sharing ratio and word; threshold duty; τ_c and telegraph sd; switches and dwells; quarter-span duties; mid-sweep fraction.
- **At every adjacent pair of spans:** the boundary word, with both sensitivities.
- **For each job:** the job verdict word.

A NO CHANGE is no evidence of a change in the duty under the stationary two-state model; it does not show the duties equal (A27, ruling R3).

Job 1's per-shot arrays are fetched and hashed with the others. They are read only as the scorer requires.

**Beside, no word:**

- each job's mean duty and the run's mean under test 15's definitions, set beside every monitor job at 5.6 µs on 17, 19 and 21 October, each labelled by its design and shot count;
- the run means as the public record states them: 0.330, 0.341 and 0.313 (finding 30), and test 18's 0.300, each labelled with its run;
- the gap between jobs 2 and 3 as the provider's execution record gives it.

No rule tests a change between dates, and this one does not.

## 5. The middle of a job

Test 17's middle test is not applied. Tests 17 and 18 read it NOT SEEN twice, and their record stands as written.

## 6. Sandhi version 4.1's scorer, on D1, a second run

Run once, unchanged, on jobs 2 and 3 as D1's two monitor jobs, from the files listed in its `FORECAST-SHA256SUMS` (digest `7903a281…b083`).

- **Before it runs:** check those files, and check the predictions files against their posted digests (`5b2e45de…628f` and `a30488be…fc54`).
- **The supplied inputs:** C1, the actual design; C2, the actual sweep time.
- **The shuffled job.** Job 1 is supplied as D1's shuffled job only if the scorer's README accepts a job of test 7's form as that job. Then C3 is job 1's A26 weights per span. If the README does not, or job 1 did not run, no shuffled job is supplied and the two bets that need one are reported as not scored. The runner records which, and the README lines it relied on, before the scorer runs.
- **If its compiled library does not load,** it is rebuilt from its hashed source, with the compiler, the command and the new digest recorded. Any other failure is reported, not repaired.
- The scorecard is reported as written. The scorer's test 15 readings are set beside this rule's.

**What a second run is, stated now.**

- D1's bets were written for "the next 143 monitor run". Test 18 was that run.
- This test applies the same posted bets, unchanged, to a later run. Nothing in the bets or the scorer is refitted in between.
- This scorecard is labelled **D1, SECOND RUN**. It is set beside test 18's and is not pooled with it. It is not quoted as D1's scorecard without the label.
- A family that counts against the model here counts against it for this run. The report does not explain it away by the weeks between, and does not name a cause.

## 7. What the words mean, fixed now

The verdict and boundary words are test 7's, test 11's, test 12's and test 15's. CONFIRMED ON THE FIFTH DATE means only that test 7's rule returned TWO FIXED FREQUENCIES on this date's job 1. Nothing in the run's report is adopted by its writing, and the rule is not changed after the data, whatever they show.

## 8. The reporting

The hand-back:

- `report-t20.md`: the stamps, estimates and decisions without allowance figures, the scan's fits and verdict, the spans, the words, the per-shot tables and the scorecard;
- `fits-t20.json`, with the per-span weights beside the scorecard;
- the counts files with execution metadata;
- the per-shot arrays and their hashes-before-analysis file (not published);
- `scorecard-t20.json`;
- `hash-check-t20.md`;
- the scripts as run;
- `SHA256SUMS`.

Job names and tags carry the test number only. The instance is named by its saved name only, and only in the private record.

## 9. The desk check

The scan's rule is test 7's and the per-shot definitions are test 15's. Test 15's desk check is rerun unchanged after the read, through the live code, and reported beside the run.
