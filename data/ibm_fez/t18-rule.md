# Test 18: two monitors on fez 143, the desk model's first design (rule, fixed before any job is built)

Status: draft for the author's review, 20 October 2026. Once approved, this file is renamed `t18-rule.md`. It is then hashed, the hash is posted in a public issue, and the file is published unchanged with the run. Its per-shot read is fixed here too, before any job runs.

## 1. The questions

1. **On a fourth date, does qubit 143's state behave as on the record?**
   - The design is test 11's two monitor jobs, run again on ibm_fez at the antiphase wait: per span, the sharing, duty, τ_c and boundary words under test 15's definitions.
   - The record so far covers 17 October (test 11, day 2) and 19 October (test 11's third day; test 17).
2. **Does the desk model's first design hold?**
   - The desk model Sandhi, version 4.1, posted bets for "the next 143 monitor run, two jobs, 300 positions each, 1,000 shots", design D1, before test 17 ran (issue 68).
   - Test 17 ran a different design, so D1 has not yet been scored. This test is that run.
3. **The middle of a job, a second time.** Test 17's middle test, unchanged, on new jobs. Test 17 read NOT SEEN (Z = −0.97). This test does not pool with it.

No cause is named for any sharing, switching, difference or shape.

## 2. The jobs

**Settings for every job:**

- dynamical decoupling, gate twirling and measurement twirling off;
- no readout error mitigation;
- qubit 143 alone, every other qubit idle in |0⟩.

Each job is submitted once. A failed, cancelled or refused job is recorded and not resubmitted.

**On a pay-as-you-go instance, named in the go by its saved name, in the private record only.**

- **Job 1, the monitor:** test 11's job 2 exactly as its rule fixes it.
  - 300 circuits: the two readout circuits, 148 repeats of X then Y at 5.6 µs, the two readout circuits.
  - 1,000 shots each; submitted in that order, not interleaved.
  - R0 0.4770, test 11 day 3's job 1 fit, as test 17's Part B used it.
- **Job 2, the monitor again:** the same circuits rebuilt, submitted as soon as job 1's result is fetched, as test 11's job 3.
- **The estimate per job:** day 3's measured monitor rate, 82 s for 300,000 shots, so about 82 s; with the half-again margin, 123 s.
- **No shuffled job.** Sandhi's bets that need one (`shuffled_weight_A26`, `shuffled_sd`) are not scored, and the report says so.

**For every job:**

- the published stamps, and the window, as test 7's rule states; no job goes in inside fez's computed calibration window;
- the structural checks of test 12's rule, on the circuits as built and on the backend's snapshot:
  - every instruction on 143;
  - the gate sequence and the scheduled wait;
  - noiseless P(1) of 0, 0.5, 0 and 1;
  - the positions in order;
- the instance's remaining allowance read and recorded, with the UTC time, before each job;
- a job submitted only if its estimate, with the half-again margin, is within the allowance;
- the decision recorded before the build;
- the result's execution metadata saved with the counts at fetch;
- after each fetch, the per-shot results fetched as test 13's `fetch_t13.py` does, and every array file's SHA-256 recorded in a hashes-before-analysis file before any reading runs.

**If job 2 is refused by the allowance clause,** job 1 is read alone:

- the two-job quantities (the job-mean duty difference, the gap) are reported as not available;
- the scorer runs on the actual design if its README allows one monitor job for D1; otherwise the scorer's refusal is recorded and not repaired.

## 3. The analysis from the counts

Test 11's monitor analysis and verdicts, its sections 1 to 10 for jobs 2 and 3, applied to jobs 1 and 2 here, with 148 repeats. The straddling-repeat and boundary-pair rules are applied as test 12 fixes them. The per-span weights from this analysis are Sandhi's A26 weights (its C3).

## 4. The per-shot read

For every monitor job of this test, test 15's definitions apply unchanged: its rule, sections 4 to 7, with test 13's whole repeats and quadrature of record.

- **Per span:**
  - the sharing ratio and word;
  - threshold duty;
  - τ_c and telegraph sd;
  - switches and dwells;
  - quarter-span duties;
  - mid-sweep fraction.
- **At every adjacent pair of spans:** the boundary word, with both sensitivities.
- **For each job:** the job verdict word.

A NO CHANGE is no evidence of a change in the duty under the stationary two-state model; it does not show the duties equal (A27, ruling R3).

**Beside, no word:**

- each job's mean duty and the run's mean, set beside the monitor means of 17 and 19 October;
- the gap between the two jobs as the provider's execution record gives it.

No rule tests a change between dates, and this one does not.

## 5. The middle test, unchanged

Test 17's section 5 applies exactly as written there:

- the normalized position;
- the contrast C and its telegraph sd;
- Z = (Σ C_j / sd_j) / √n over this test's contributing jobs;
- the words MIDDLE HIGH (Z ≥ 2.0), NOT SEEN (Z < 1.0) and UNDECIDED;
- the quantities set beside them.

**This test's Z is its own.** It is not pooled with test 17's. Test 17's Z is set beside it, with no combined word.

**The power, stated now.**

- Assume two three-span jobs and span sds of about 0.07, as on day 3.
- Each job's contrast then has an sd of about 0.086.
- If the middle spans' duty were higher by 0.05, the expected Z is about 0.8.
- This test is more likely to read NOT SEEN or UNDECIDED than MIDDLE HIGH even if that effect were there.
- A MIDDLE HIGH would count for it; neither word names why.

## 6. Sandhi version 4.1's scorer, on D1

Run once, unchanged, on jobs 1 and 2 as the D1 design, from the files listed in its `FORECAST-SHA256SUMS` (digest `7903a281…b083`).

- **Before it runs:** check those files, and check the predictions files against their posted digests (`5b2e45de…628f` and `a30488be…fc54`).
- **The supplied inputs:** C1, the actual design; C2, the actual sweep time; C3, this test's A26 weights per span.
- **No shuffled job is supplied.**
- **If its compiled library does not load,** it is rebuilt from its hashed source, with the compiler, the command and the new digest recorded. Any other failure is reported, not repaired.
- The scorecard is reported as written. The scorer's test 15 readings are set beside this rule's.

## 7. What the words mean, fixed now

The verdict and boundary words are test 15's and test 11's. MIDDLE HIGH, NOT SEEN and UNDECIDED mean only what test 17's section 5 computes. Nothing in the run's report is adopted by its writing, and the rule is not changed after the data, whatever they show.

## 8. The reporting

The hand-back:

- `report-t18.md`: the stamps, estimates and decisions without allowance figures, the spans, the verdicts, the per-shot tables, the middle test and the scorecard;
- `fits-t18.json`;
- the counts files with execution metadata;
- the per-shot arrays and their hashes-before-analysis file (not published);
- `scorecard-t18.json`;
- `hash-check-t18.md`;
- the scripts as run;
- `SHA256SUMS`.

Job names and tags carry the test number only. Instances are named by their saved names only, and only in the private record.

## 9. The desk check

The per-shot definitions are test 15's; its desk check is rerun unchanged after the read. The middle test's false-alarm rate and its power are checked on 2,000 synthetic sets of two three-span jobs, with the record's spans and duties and τ_c 0.2 s:

- with no middle effect, the false-alarm rate;
- with a middle effect of 0.05, the power.

Both are reported beside the normal-approximation figures of section 5.
