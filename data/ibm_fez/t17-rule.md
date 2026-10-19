# Test 17: the long monitor on fez 143, and short monitors again (rule, fixed before any job is built)

Status: draft for the author's review, 19 October 2026. Once approved, this file is hashed, the hash is posted in a public issue, and the file is published unchanged with the run. Its per-shot read is fixed here too, before any job runs.

## 1. The questions

1. **Over one long job, does qubit 143's state behave as on the record?** One monitor job of 600 positions (about six execution spans) at the antiphase wait: the per-span sharing, duty, τ_c and boundary words under test 15's definitions, and the desk model Sandhi version 4.1's predictions for this design (D2), whose digests were posted before this rule.
2. **Is the middle of a job different?** A pattern was noticed on 19 October in the published weights of 143's three-span jobs: the middle span's duty above the mean of the end spans in every 1,000-shot monitor job (a note dated 19 October, written before this rule and published with the run). Nothing in the record before this rule tested it. This rule states the test before any of its data exist.

No cause is named for any sharing, switching, difference or shape.

## 2. The jobs

Settings for every job: dynamical decoupling, gate twirling and measurement twirling off; no readout error mitigation; qubit 143 alone, every other qubit idle in |0⟩. Each job submitted once; a failed, cancelled or refused job is recorded and not resubmitted.

**Part A, on the open-plan instance (named in the go, by its saved name, in the private record only): short monitors.** Test 12's job exactly as its rule fixes it (250 positions: two readout circuits, 123 repeats of X then Y at 5.6 µs, two readout circuits; 500 shots each; R0 0.4749), run as many times as the allowance clause permits, at most three, each submitted as soon as the previous one's result is fetched. Estimate per job: test 14's measured rate per shot (36 s for 124,000 shots) times 125,000 shots, about 36 s, with the half-again margin, about 54 s.

**Part B, on a pay-as-you-go instance (named in the go likewise): the long monitor (D2).** Test 11's monitor circuits (5.6 µs, X then Y, 1,000 shots each), in one job of 600 positions: two readout circuits, 298 repeats in fixed order, two readout circuits; not interleaved; R0 0.4770, test 11 day 3's job 1 fit. Estimate: day 3's measured monitor rate (82 s for 300,000 shots) times 600,000 shots, 164 s, with the margin 246 s.

**For every job:** the published stamps and the window as test 7's rule states; the structural checks of test 12's rule (every instruction on 143; the gate sequence and scheduled wait; noiseless P(1) of 0, 0.5, 0 and 1; the positions in order) on the circuits as built and on the backend's snapshot; the instance's remaining allowance read and recorded with the UTC time before each job; a job submitted only if its estimate with the half-again margin is within it; the decision recorded before the build; the result's execution metadata saved with the counts at fetch. After each fetch, the per-shot results are fetched as test 13's `fetch_t13.py` does and every array file's SHA-256 recorded in a hashes-before-analysis file before any reading runs.

## 3. The analysis from the counts

Each Part A job: test 12's analysis and verdicts unchanged. Part B: test 11's monitor analysis and verdicts (its sections 1 to 10 for the monitor jobs) with 298 repeats; the straddling-repeat and boundary-pair rules as test 12 fixes them.

## 4. The per-shot read

For every monitor job of this test, test 15's definitions unchanged (its rule, sections 4 to 7, with test 13's whole repeats and quadrature of record): per span, the sharing ratio and word, threshold duty, τ_c, telegraph sd, switches and dwells, quarter-span duties, mid-sweep fraction; the boundary word at every adjacent pair of spans, with both sensitivities; the job verdict word. A NO CHANGE is no evidence of a change in the duty under the stationary two-state model; it does not show the duties equal (A27, ruling R3).

## 5. The middle test, fixed now

For each monitor job of this test with three or more spans:

- **Normalized position:** each span's centre in time, t, as a fraction of the job's first-span start to last-span stop.
- **The contrast:** C = (mean duty of the spans with t in [1/3, 2/3]) minus (mean duty of the other spans), with its telegraph sd from the spans' sd (in quadrature, each mean's sd from its spans). A job with no span centre in [1/3, 2/3] contributes no contrast and is listed.
- **The pooled statistic:** Z = (Σ C_j / sd_j) / √n over the n contributing jobs.
- **The word:** **MIDDLE HIGH** if Z ≥ 2.0; **NOT SEEN** if Z < 1.0; **UNDECIDED** between. Under no middle effect and the telegraph error, MIDDLE HIGH comes up about 2 percent of the time.
- **Beside, no word:** the per-span duties against t; a weighted straight line (a trend in the job) and its slope over sd; for Part B, the duty of each span against its index; the contrast at the threshold sensitivity.
- **The power, stated now:** if the middle spans' duty is higher by 0.05 (the size seen on 19 October), the expected Z from one six-span job and two short three-span jobs is about 1.3; this test is more likely to read UNDECIDED than MIDDLE HIGH even if the effect is there. A NOT SEEN would count against it at that size; a MIDDLE HIGH would count for it; neither names why.

## 6. Sandhi version 4.1's scorer

On Part B only (the D2 design), run once, unchanged, from the files listed in its `FORECAST-SHA256SUMS` (digest `7903a281…b083`), checked before it runs; the predictions files checked against their posted digests (`5b2e45de…628f`, `a30488be…fc54`). If its compiled library does not load, it is rebuilt from its hashed source with the compiler, command and new digest recorded; any other failure is reported, not repaired. The scorecard is reported as written; the scorer's test 15 readings are set beside this rule's.

## 7. What the words mean, fixed now

The verdict and boundary words are test 15's and test 11's. MIDDLE HIGH, NOT SEEN and UNDECIDED mean only what section 5 computes. Nothing in the run's report is adopted by its writing, and the rule is not changed after the data, whatever they show.

## 8. The reporting

`report-t17.md` (the stamps, estimates and decisions without allowance figures, the spans, the verdicts, the per-shot tables, the middle test, the scorecard); `fits-t17.json`; the counts files with execution metadata; the per-shot arrays and their hashes-before-analysis file (not published); `scorecard-t17.json`; `hash-check-t17.md`; the scripts as run; `SHA256SUMS`. Job names and tags carry the test number only. The instances by their saved names only, in the private record only.

## 9. The desk check

The per-shot definitions are test 15's, whose desk check is rerun unchanged after the read. The middle test's false-alarm rate (about 2 percent at Z ≥ 2.0) and its power are stated from the normal approximation under the telegraph error; the runner checks the false-alarm rate on 2,000 synthetic sets of jobs with the record's spans and duties, no middle effect, and τ_c 0.2 s, and reports it beside.
