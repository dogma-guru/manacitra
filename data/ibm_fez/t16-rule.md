# Test 16: the per-shot read of test 11's third day (rule, fixed before the arrays are opened)

Status: draft for the author's review, 19 October 2026. Once approved, this file is hashed, the hash is posted in a public issue, and the file is published unchanged with the read. No job is submitted and no hardware time is used.

## 1. The question

Test 11 ran on a third day on 19 October 2026 (04:09 to 04:18 UTC, ibm_fez, qubit 143): one shuffled job and two monitor jobs at 5.6 µs. Its per-shot arrays were fetched and hashed and not opened (`tests/handback/t11-day3/shots-t11-day3-hashes-before-analysis.txt`). This test reads them under test 13's and test 15's definitions, unchanged, and runs the desk model Sandhi version 4's scorer on them, unchanged, so that the predictions hashed before the run (digests posted in a public issue before the run: `718a0b86…c5b7481b` for the predictions and `42287f2e…01d7bf` for the scorer) are scored by the code they were hashed with.

No cause is named for any sharing, switching or change.

## 2. The arrays, and what is checked before anything is read

`shots-t11-day3-job1.npz`, `-job2.npz`, `-job3.npz`, each with its `-meta.json`, in `tests/handback/t11-day3/`. Before any reading runs:

1. every array and meta file's SHA-256 equals its line in `shots-t11-day3-hashes-before-analysis.txt`; a mismatch stops the read of that job;
2. the counts recomputed from each array equal the published counts (`counts-t11-day3-job{1,2,3}.json`) position for position; a mismatch stops the read of that job;
3. the spans and each position's span are those of the counts files' execution metadata, as the day 3 report gives them; the meta files' spans are checked against them and any difference is reported.

## 3. The definitions

Every definition is test 15's (its rule, sections 4 to 7), with test 13's whole repeats and quadrature of record, applied without change: the sharing ratio and its words (SHARED above 3, INDEPENDENT below 1.5, UNDECIDED between); the threshold midway between the 10th and 90th percentiles of the sweep means; the duty b; τ_c at the 1/e crossing of the excess autocorrelation, read for SHARED spans with a lag of 3 or more; switches and dwells; the telegraph error √(2 b(1 − b) τ_c / T), at three sweeps as a ceiling where τ_c is under three sweeps; the quarter-span duties; the boundary words NO CHANGE (at or under 2), BETWEEN (over 2 to 3), CHANGE (over 3), with the published weight differences over the same combined sd beside; the between-jobs word from the job means; the mid-sweep fraction; the autocorrelation at lags 490 to 510; the sensitivity of every word to the threshold (20th to 80th midpoint) and to τ_c (plus and minus one sweep).

## 4. What is read

**Jobs 2 and 3 (the monitors):** every item above, per span, both quadratures with the quadrature of record named; the per-job verdict word as test 15's section 5 gives it; the boundary word at each adjacent pair of spans within a job (four); the between-jobs word for jobs 2 and 3, with the gap (186.6 s) on the row.

**Beside, no word:** the same quantities for day 2's monitor jobs, copied from `tests/handback/t15/fits-t15.json`, and the difference of the day-mean duties of day 2 and day 3 over their combined sd, with the stamp change (18:48:16 UTC, 17 October, to 03:21:57 UTC, 19 October) on the row; and, per monitor job, the duty of the middle span minus the mean of the two end spans with its telegraph sd. That last item is labelled **not a test**: the pattern it describes was noticed in these jobs' published weights before this rule (`middle-span-pattern-note`, 19 October), and the duty is not independent of them.

**Job 1 (shuffled):** test 15's section 7 readings on its Y and X positions per span (the sharing ratio as a floor; the per-row lag-1 autocorrelation), no word; its published per-span weights (0.440, 0.521, 0.389) with the telegraph sd at τ_c borrowed from the median of the day 3 monitors' read τ_c, labelled borrowed, and the boundary words beside with that label.

## 5. Sandhi version 4's scorer

The scorer and its dependencies are the files listed in `FORECAST-SHA256SUMS` (digest `1115b9bd…bddfcc2`), copied to `sandhi-v4-scorer/` beside this rule with the predictions files. Before it runs, every file is checked against `FORECAST-SHA256SUMS` and the predictions files against their posted digests; a mismatch stops this section.

Run once, with its defaults (bootstrap 400, dwell permutations 2000, seed 104196401):

`python score_model_01_v4.py --job day3-job2,<array>,<meta>,<counts> --job day3-job3,<array>,<meta>,<counts> --shuffled day3-job1,<array>,<meta>,<counts> --predictions predictions-model-01-v4.json --out scorecard-t16.json`

- The scorer is not edited. If its compiled library (`hmm_core.dylib`) does not load on the runner's machine, it is rebuilt from `hmm_core.c` as listed in `FORECAST-SHA256SUMS`, with the compiler, its version and the command recorded, and the new library's SHA-256 reported beside the listed one; the source file's digest must still match. No other change is allowed.
- If the scorer fails for any other reason, the failure is reported with its message and this section stops; it is not repaired.
- Its scorecard is reported as written, including every quantity it marks unavailable and every applicability difference it records. The scorer's computed duties, sharing ratios and τ_c are set beside this rule's own (section 4) in one table; any difference is reported, not reconciled.

## 6. What the words mean, fixed now

- The verdict words and the boundary words are test 15's and mean what its section 8 says, with this correction carried from A27's ruling R3: a NO CHANGE is no evidence of a change in the duty under the stationary two-state model; it does not show the duties equal.
- The scorecard is the model's, scored by its own code; this test attaches no word to it.
- Nothing in this read is adopted by its report.

## 7. The reporting

`report-t16.md` with the hash checks, the counts checks, the span check, the per-span table for the monitors, the boundary and between-jobs rows, every beside item, the scorer's run (including any rebuild) and its scorecard, and the side-by-side table of section 5; `fits-t16.json` with every number; `scorecard-t16.json` as the scorer wrote it; `hash-check-t16.md`; the scripts as run; `SHA256SUMS`. The arrays stay in the hand-back folder and are not published.

## 8. The desk check

The definitions are test 15's unchanged, so its desk check is the desk check: `desk-check-t15-mantri.py` is run again unchanged after the read (seed 15390, 400 spans per case) and its rates are recorded beside test 15's.
