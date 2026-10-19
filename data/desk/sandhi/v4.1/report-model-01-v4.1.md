# Model 01 version 4.1

## Three required checks

1. All 125 test 15 comparisons agree at test 16’s stated absolute tolerance of 10⁻¹²; 120 are exactly equal and five differ by at most 2.7755575615628914 × 10⁻¹⁷. Literal bitwise equality for all 125 is not met. The unchanged v4 estimator already has these differences from the independent test 16 reading, so changing it would exceed C1 to C3. Source: `audit-part-a.json/comparison_125`.
2. All 107393 compared leaves outside C1 to C3 reproduce the original v4 handback exactly after required presentation label normalization. Numerical differences are zero. Execution time, file locations and corrected calibration products are excluded explicitly. Source: `audit-part-a.json/unaffected_v4_scorecard`.
3. `scorer-diff-v4.1.md` lists every scorer replacement line and every line of the added calibration dependency, with C1, C2 or C3 attribution. All six inherited scorer dependencies are byte equal to v4. Reapplying the listed replacements reconstructs the entire scorer. Source: `scorer-diff-audit.json`.

The model is a kinetic description; it names no cause.

The sweep clock is the returned order; seconds are conditional on that order being chronological.

The predictions are the model's, written before the run they predict, and they are what can count against it.

## Scope, integrity and sequence

This is a local desk run dated 19 October 2026. Scientific inputs come only from the supplied v4.1 bundle. A memory registry was consulted for workflow orientation before the bundle was read; no earlier result was imported from that registry. The required prompt, kickoffs, reports and predictions were read before analysis code was written. No external scientific source was fetched.

The outer archive digest matches. All 23 manifest entries, both inner archive digests, and all six day 3 array and metadata entries match. All 78 entries of the returned v4 manifest and all nine forecast entries match. The forecast manifest digest is `1115b9bdddb43c0e81a68905709a8025d58106799e69da40f89614e76bddfcc2`, matching the value carried by test 16. The inner input checks comprise 60 manifest entries and 24 present array record entries. The two absent test 9 files are explicitly omitted by that bundle. Sources: `integrity.json`, `frozen-integrity.json`, `v4-input-integrity.json`.

Corrections C1 to C3 were implemented first. Part A used the frozen v4 files. The Part A numerical audit completed before Part B began. The new fits then supplied the three date hierarchy. Rehearsals and nominal simulations completed before the prediction files were written. All simulation counts were retained without a compute reduction.

The hash parser initially encountered prose in a hash record and later trailing annotations in six filenames. Both parser issues were corrected before those files were analyzed. The first Part A audit also compared six required presentation labels literally; the correction normalizes labels only. An unused original applicability function was removed under C1 and C2 while the first Part A computation was running; it had no call site in that computation. No numerical method changed. These events remain in `run.log`.

## Kinds and definitions

Counts, sweep series, threshold duties and supplied A26 weights are computed facts of the supplied record. HMM rates, stationary duties, hierarchy spreads, simulated intervals and probabilities are model outputs. The final three paragraphs are readings. No result is adopted by this report.

The C1 calibration receives only row counts after straddling repeats are removed, circuit schema, shots, sweep counts, durations and span counts. The design extraction is unchanged when counts, fits and observed A26 weights are replaced. The calibration handles unequal span counts and one monitor job. Nominal templates are display examples, not admission gates.

C2 uses every actual sweep time. Its primary range is 0.9 times the smallest donor time through 1.1 times the largest. Padding each endpoint by ten percent of the range width is retained as an alternative; both include every day 3 span. Outside the primary range, seconds comparisons remain uncalibrated and the correlation criterion uses a separately calibrated dimensionless subfamily. The full set of observed quantities remains displayed.

C3 reads `span_readings_A26/weight_per_span/weighted_mean` from the supplied run fits and records its source digest and span. It does not reconstruct A26. The borrowed shuffled sd has no unique observed population length scalar in the frozen definition, so it remains unavailable; the alternatives are listed in the internal review. The weight interval definition retains the absolute 0.011 allowance.

## Part A

Internal review: the setup was corrected after day 3's arrays were opened. These comparisons are not scores and do not count for or against version 4. Duty has 0 misses in 12 comparisons, correlation has 0 in 24, and emissions has 0 in 8; the calibrated cutoffs are 7, 9 and 4 respectively.

Internal review: the setup was corrected after day 3's arrays were opened. These comparisons are not scores and do not count for or against version 4. One of the three A26 weights is outside its interval, while all four within job boundary words are NO CHANGE and no structural criterion is met.

Internal review: the setup was corrected after day 3's arrays were opened. These comparisons are not scores and do not count for or against version 4. The complete per unit comparisons, probabilities, boundary criteria and unavailable definitions are in `internal-review-day3.md` and `.json`; the official day 3 handback remains test 16’s.

## Part B fits and hierarchy

The primary hierarchy has 15 spans from five monitor jobs on three UTC dates. Including test 14 gives 18 spans from six jobs. Test 14 remains NOT USABLE under its own rule and is beside the primary set. The 15 eligible kingston spans and all original job fits and bootstrap files are carried exactly. Existing job parameters do not share a likelihood with the new jobs, so adding the new records does not require changing those job fits. Sources: `fits-model-01-v4.1.json`, `data-model-01-v4.1.json`, `hierarchy-model-01-v4.1.json` and `audit-part-b.json`.

Each new monitor job uses 400 parametric bootstrap draws with the unchanged float64 forward likelihood. Both fits and all 800 bootstrap refits converged. The hierarchy uses the unchanged normal normal maximum marginal likelihood method and 400 draws per transformed parameter and set. New within job and adjacent job boundary comparisons use 400 null and 400 alternative draws. Original alternatives, control fits and boundaries remain in the fits file.

| Set | Parameter | v4 spread | v4 90 percent profile interval | v4.1 spread | v4.1 90 percent profile interval |
|---|---|---|---|---|---|
| primary | logit_b | 0.0998504 | 0 to 0.321585 | 0 | 0 to 0.200037 |
| primary | log_ell | 0.377158 | 0.252078 to 0.609853 | 0.296522 | 0.210659 to 0.432717 |
| with_test14 | logit_b | 0.0721557 | 0 to 0.274236 | 0 | 0 to 0.182933 |
| with_test14 | log_ell | 0.371414 | 0.25494 to 0.568776 | 0.300514 | 0.215694 to 0.429471 |

The spreads above are on the logit duty and natural log length scales. The duty profile includes zero, and the length profile remains above zero. The hierarchy bootstrap samples and profile intervals are retained, along with the earlier leave one job out record labelled as carried.

## Rehearsal and numerical checks

The corrected scorer was rehearsed on both day 2 and day 3 arrays using the v4.1 state. These are computation checks on opened records, not prospective validation. A separate Python log domain forward calculation agrees with all six new span likelihoods within 6.04 × 10⁻¹⁰. Every old job fit and bootstrap file remains equal to its frozen counterpart. Sources: `rehearsal-day2.json`, `rehearsal-day3.json` and `audit-part-b.json`.

Every actual design or nominal calibration uses 2000 complete simulated days, with 1000 for interval construction and 1000 for joint family miss calibration. Its first 100 days receive likelihood comparisons with 400 null draws at every relevant boundary. Draw counts, seeds, every trial, convergence flags and Monte Carlo intervals are retained. The independent calibration audit recounts intervals, boundary probabilities and family cutoffs from the saved trials. Source: `calibration-audit.json`.

## Prediction scope

D1 is the next two job monitor run with 300 positions per job, 1000 shots and X then Y at 5.6 µs on 143, with any number of spans. Its nominal example uses day 3 design metadata. D2 is one job of the same circuits with 600 positions, nominally six spans. Its nominal example has six contiguous blocks of 100 positions and a donor mean sweep time. Actual intervals and criteria for both are recomputed from the future design at scoring time.

The empirical day extension now chooses one of three observed UTC dates uniformly once per simulated day and draws emission vectors from a job on that date. This preserves the v4 extension and its limits; it does not establish a population of future dates or emissions. There is no additional middle span parameter, channel or bet. No prediction beyond stationarity within a job is issued for that pattern.

## Readings, labelled

Reading of the third date: adding six spans narrows the duty spread profile and moves its fitted value to zero. The fitted log length spread decreases from about 0.377 to 0.297 but remains above zero in its profile interval. Within this model, the new date does not require larger between span spreads.

Reading of slower switching: the six day 3 fitted lengths and test 15 correlation times lie inside the original v4 nominal three span intervals, and also inside the corrected conditional intervals. The new date mean is higher than the earlier date means, while its spans do not enlarge the fitted common length spread. This is a statement about the fitted description and its intervals.

Internal review: the setup was corrected after day 3's arrays were opened. These comparisons are not scores and do not count for or against version 4. Reading of the internal review: correcting the design opens comparisons that the original support gates withheld, and exposes the one shuffled weight outside its interval; it does not create a prospective test because the arrays were already opened when the setup was corrected.

The author and Mantri may read these records and recount what they can. Nothing here is adopted.
