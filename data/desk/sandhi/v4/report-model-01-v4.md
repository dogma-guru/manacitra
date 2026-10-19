# Model 01 version 4

## The three required checks

1. The threshold duties reproduce test 15 for all twelve eligible spans on 143, including test 14. Every compared value and its reference are in `record-audit.json`, field `reproductions`.
2. The sharing ratios reproduce test 13 on its nine monitor spans and test 15 on all twenty seven eligible spans. The complete audit contains 1740 matching field comparisons, with no differences above the stated tolerance of 1e−12. Source: `record-audit.json`, fields `reproduction_count` and `reproduction_mismatches`.
3. The supplied scorer was run on all three test 11 array files. Its monitor quantities reproduce all 84 archived field checks with no mismatch. The shuffled job is read beside. This is a computation check on training records, not prospective validation. Source: `scorer-test.json`, field `archived_reproduction`.

The model is a kinetic description; it names no cause.

The sweep clock is the returned order; seconds are conditional on that order being chronological.

The predictions are the model's, written before the run they predict, and they are what can count against it.

## Record and scope

Only the supplied runner prompt, version 4 archive and its digest were read as scientific inputs. No external record was fetched. The external Python installation supplied numerical libraries only, with isolated mode enabled. The clock read was 19 October 2026 at 02:31:40 UTC, which was 18 October in America/New_York. The bundle itself is dated 18 October.

The outer archive digest matches. All 60 files listed by the inner manifest match. All 24 present entries in the array hash records match. The two absent entries name the test 9 array and metadata, which the bundle explicitly omits and which are outside this run. No absent entry is called a hash mismatch. All included arrays reproduce their supplied counts. Source: `record-audit.json`, fields `files`, `arrays` and `jobs`; independent calculation in `independent-audit.json`.

The complete fitted set contains 27 qubit spans in 10 qubit jobs: 12 spans on 143, and 15 eligible spans on the other supplied processor record. The primary 143 hierarchy contains nine spans from three monitor jobs on two UTC dates. Test 14 is beside it because its own rule returned NOT USABLE. All 561 excluded multi qubit spans and six shuffled span quadratures are read beside. Source: `series-base.json`, `beside-record.json` and `record-audit.json`.

Counts, ratios, threshold duties and series are computed facts of the supplied record. Rates, stationary duties, emission contrasts, intervals and probabilities are model outputs. The readings below are labelled interpretations of these outputs. No record here is adopted by this report.

## Definitions and their limits

The array metadata gives rounded span times and sizes but no position membership. It cannot govern membership as written in the kickoff. The detailed counts metadata supplies membership, and agrees with the archived fits on whole repeats and excluded straddlers. Both checks and the limitation are retained. No position was assigned from a remembered or external record. Source: `record-audit.json`, field `jobs`.

Rows are whole repeats of one wait and quadrature. The shared state clock is the returned shot index. Every fitted series, its row positions, counts, row totals, source digest, posterior high state probability and decoded path is in `data-model-01-v4.json`. The primary exchangeability check uses the pooled mean binomial denominator of test 15; the mean row denominator is retained beside. A one sided upper probability below 0.01 is the declared flag. Only test 14 span 0 is flagged, and it is fitted anyway.

The exact forward likelihood uses float64 and a stationary initial distribution independently in every span. Emissions are shared across all eligible spans of a qubit job. Both transition probabilities remain unrestricted inside the unit interval. H is the state with the larger emission in the quadrature of record. The stationary duty u/(u+d), posterior mean occupancy, decoded occupancy and threshold duty remain separate fields.

One span, test 10 job 2 qubit 95 span 1, has fitted 1−u−d at or below zero. Its requested real positive correlation length is unavailable. A fit of the same complete qubit job constrained to positive correlation is beside it, with its likelihood loss. Bootstrap length intervals state how many draws have a defined length, so an interval on defined draws is explicitly conditional. Source: `fits-model-01-v4.json`, field `undefined_ell_alternatives` and each bootstrap interval.

No formal two mode criterion appears in test 15. The beside record therefore marks that criterion unavailable and retains quantiles, the middle fifth fraction, and histogram alternatives at two bin counts without a finding word. The full A26 estimator is also absent from the bundle; the scorer reports its future computed weight unavailable instead of reconstructing an unstated estimator.

## Fits

Each qubit job has 400 parametric bootstrap draws. No reduction was needed. Emission free fits and the alternative returned order fits use the same complete eligible sets. Between job comparisons keep emissions separate by job under both switching hypotheses. Source: `fits-model-01-v4.json`, fields `jobs`, `spans` and `boundaries`.

| Span | Model duty | 90 percent interval | Model length in sweeps | 90 percent interval | Threshold duty | Test 15 length in sweeps |
|---|---:|---|---:|---|---:|---:|
| `t10-job1-q11-s0` | 0.2357 | 0.2069 to 0.2651 | 0.6767 | 0.5664 to 0.7961 | 0.214 | 3 ceiling |
| `t10-job1-q11-s1` | 0.2101 | 0.1861 to 0.233 | 0.5889 | 0.4702 to 0.6897 | 0.209 | 3 ceiling |
| `t10-job1-q11-s2` | 0.2186 | 0.1935 to 0.246 | 0.5831 | 0.4762 to 0.7035 | 0.217 | 3 ceiling |
| `t10-job1-q95-s0` | 0.1395 | 0.1221 to 0.1629 | 0.3323 | 0.2046 to 0.4461 | 0.237 | 3 ceiling |
| `t10-job1-q95-s1` | 0.1462 | 0.1276 to 0.1677 | 0.3867 | 0.2603 to 0.4934 | 0.196 | 3 ceiling |
| `t10-job1-q95-s2` | 0.1196 | 0.102 to 0.1383 | 0.4684 | 0.3436 to 0.579 | 0.203 | 3 ceiling |
| `t10-job1-q120-s1` | 0.0193 | 1.874e−06 to 0.07106 | 18.76 | 2.451 to 36.23 | 0.285 | 11 |
| `t10-job2-q11-s0` | 0.2303 | 0.2039 to 0.2566 | 0.5632 | 0.44 to 0.6662 | 0.216 | 3 ceiling |
| `t10-job2-q11-s1` | 0.2079 | 0.184 to 0.2322 | 0.5471 | 0.4219 to 0.6606 | 0.207 | 3 ceiling |
| `t10-job2-q11-s2` | 0.2334 | 0.2052 to 0.2572 | 0.6135 | 0.5035 to 0.7301 | 0.213 | 3 ceiling |
| `t10-job2-q95-s0` | 0.1411 | 0.1203 to 0.1635 | 0.4589 | 0.3259 to 0.588 | 0.214 | 3 ceiling |
| `t10-job2-q95-s1` | 0.1425 | 0.1249 to 0.1614 | unavailable | 0.1435 to 0.3507 | 0.207 | 3 ceiling |
| `t10-job2-q95-s2` | 0.134 | 0.1162 to 0.1543 | 0.3297 | 0.2062 to 0.4475 | 0.199 | 3 ceiling |
| `t10-job2-q120-s0` | 0.01649 | 1.627e−06 to 0.06011 | 15.95 | 3.27 to 41.55 | 0.299 | 11 |
| `t10-job2-q120-s1` | 0.04319 | 0.004993 to 0.1002 | 9.914 | 3.397 to 18.43 | 0.358 | 22 |
| `t11-job2-q143-s0` | 0.3584 | 0.3029 to 0.4155 | 2.321 | 2.016 to 2.691 | 0.335 | 5 |
| `t11-job2-q143-s1` | 0.42 | 0.3644 to 0.4752 | 2.412 | 2.084 to 2.817 | 0.403 | 6 |
| `t11-job2-q143-s2` | 0.3825 | 0.3363 to 0.4335 | 1.672 | 1.46 to 1.909 | 0.358 | 4 |
| `t11-job3-q143-s0` | 0.3192 | 0.2466 to 0.394 | 4.464 | 3.625 to 5.477 | 0.314 | 5 |
| `t11-job3-q143-s1` | 0.3377 | 0.2628 to 0.4219 | 5.381 | 4.223 to 6.586 | 0.341 | 6 |
| `t11-job3-q143-s2` | 0.2278 | 0.158 to 0.3122 | 5.175 | 3.915 to 6.496 | 0.23 | 7 |
| `t12-job1-q143-s0` | 0.3736 | 0.2475 to 0.5002 | 6.726 | 4.819 to 9.13 | 0.356 | 6 |
| `t12-job1-q143-s1` | 0.36 | 0.2538 to 0.4726 | 5.477 | 4.04 to 7.201 | 0.344 | 5 |
| `t12-job1-q143-s2` | 0.1988 | 0.08022 to 0.3363 | 9.576 | 5.092 to 15.25 | 0.206 | 10 |
| `t14-job1-q143-s0` | 0.4252 | 0.293 to 0.5434 | 5.629 | 4.307 to 7.236 | 0.434 | 6 |
| `t14-job1-q143-s1` | 0.3607 | 0.2623 to 0.488 | 5.343 | 4.013 to 7.035 | 0.368 | 6 |
| `t14-job1-q143-s2` | 0.464 | 0.267 to 0.6528 | 14.09 | 9.121 to 21.88 | 0.462 | 25 |

Every row above is keyed by its span id in `fits-model-01-v4.json` and `checks-model-01-v4.json`, field `test15_comparison`. The seconds comparison is also complete there. A ceiling is not a measured correlation time. Differences are retained rather than adjusted away.

| Qubit job | Free emission log likelihood gain |
|---|---:|
| `t10-job1-q11` | 15.8635 |
| `t10-job1-q95` | 33.7736 |
| `t10-job1-q120` | 0 |
| `t10-job2-q11` | 15.5306 |
| `t10-job2-q95` | 12.5028 |
| `t10-job2-q120` | 6.38934 |
| `t11-job2-q143` | 45.6685 |
| `t11-job3-q143` | 30.0826 |
| `t12-job1-q143` | 11.8984 |
| `t14-job1-q143` | 15.2325 |

The returned order comparison contains every 1000 shot fitted span. Its full two likelihoods are in `fits-model-01-v4.json`, field `spans`. The comparison fits the same job shared emission structure in each order and resets the state at each span. It does not establish chronological execution.

## Hierarchy and boundaries

The hierarchy is a normal normal maximum marginal likelihood fit on logit duty and natural log correlation length, with a separate mean per UTC date and one common between span spread for each transformed parameter. Within span errors are standard deviations of the 400 transformed bootstrap estimates. Profile likelihood intervals include zero when supported; hierarchy bootstrap intervals from 400 draws are beside them. The two marginal hierarchies do not estimate a cross parameter covariance.

| Set | Duty spread | 90 percent profile interval | Length spread | 90 percent profile interval |
|---|---:|---|---:|---|
| Primary nine spans | 0.09985 | 0 to 0.3216 | 0.3772 | 0.2521 to 0.6099 |
| Including test 14, twelve spans | 0.07216 | 0 to 0.2742 | 0.3714 | 0.2549 to 0.5688 |

Source: `hierarchy-model-01-v4.json`, fields `primary.parameters` and `with_test14.parameters`. The duty spread interval includes zero in both readings. The length spread interval is above zero in both. These are model outputs on transformed scales.

| Comparison | Likelihood ratio | Calibrated probability | Duty difference | Log length difference | Test 15 word |
|---|---:|---:|---:|---:|---|
| `t10-job1-q11-s0` to `t10-job1-q11-s1` | 1.67876 | 0.4314 | −0.02528 | −0.1429 | NO CHANGE |
| `t10-job1-q11-s1` to `t10-job1-q11-s2` | 0.156267 | 0.9277 | 0.008377 | −0.009035 | NO CHANGE |
| `t10-job1-q95-s0` to `t10-job1-q95-s1` | 0.342654 | 0.8229 | 0.006672 | 0.1515 | NO CHANGE |
| `t10-job1-q95-s1` to `t10-job1-q95-s2` | 3.47779 | 0.1621 | −0.02536 | 0.2256 | NO CHANGE |
| `t10-job2-q11-s0` to `t10-job2-q11-s1` | 1.05572 | 0.611 | −0.02278 | −0.03293 | NO CHANGE |
| `t10-job2-q11-s1` to `t10-job2-q11-s2` | 1.54096 | 0.4389 | 0.02539 | 0.1156 | NO CHANGE |
| `t10-job2-q95-s0` to `t10-job2-q95-s1` | 5.90724 | 0.05237 | 0.001926 | unavailable | NO CHANGE |
| `t10-job2-q95-s1` to `t10-job2-q95-s2` | 1.6626 | 0.404 | −0.008109 | unavailable | NO CHANGE |
| `t10-job2-q120-s0` to `t10-job2-q120-s1` | 2.19321 | 0.3965 | 0.02669 | −0.4757 | NO CHANGE |
| `t11-job2-q143-s0` to `t11-job2-q143-s1` | 1.7031 | 0.3741 | 0.06202 | 0.04033 | NO CHANGE |
| `t11-job2-q143-s1` to `t11-job2-q143-s2` | 8.94062 | 0.01746 | −0.0377 | −0.3665 | NO CHANGE |
| `t11-job3-q143-s0` to `t11-job3-q143-s1` | 1.16909 | 0.616 | 0.01873 | 0.1871 | NO CHANGE |
| `t11-job3-q143-s1` to `t11-job3-q143-s2` | 3.0276 | 0.2244 | −0.11 | −0.03929 | NO CHANGE |
| `t12-job1-q143-s0` to `t12-job1-q143-s1` | 0.638187 | 0.7307 | −0.01386 | −0.2067 | NO CHANGE |
| `t12-job1-q143-s1` to `t12-job1-q143-s2` | 8.73016 | 0.009975 | −0.1617 | 0.5577 | NO CHANGE |
| `t14-job1-q143-s0` to `t14-job1-q143-s1` | 0.420021 | 0.793 | −0.06448 | −0.05564 | NO CHANGE |
| `t14-job1-q143-s1` to `t14-job1-q143-s2` | 11.2243 | 0.009975 | 0.1033 | 0.9695 | NO CHANGE |
| `t11-job2` to `t11-job3` | 134.793 | 0.002494 | −0.09184 | 0.8731 | NO CHANGE |
| `t11-job3` to `t12-job1` | 5.43871 | 0.06733 | 0.01775 | 0.3167 | NO CHANGE |
| `t12-job1` to `t14-job1` | 2.49615 | 0.2893 | 0.1019 | 0.02428 | NO CHANGE |

Each probability uses 400 null draws and the plus one correction. Each difference interval uses 400 alternative draws and is in the same comparison object in `boundaries-model-01-v4.json`. No word is assigned to the likelihood comparison. The copied words name exact source fields. Initial line search failures are retained in `boundaries-initial-attempt.json`; deterministic retries at the same candidate resolved all remaining flags.

Leaving one job out is the only out of sample model check permitted by this record before the planned run. The two held out test 11 jobs retain a same date class in training. Holding out test 12 removes the only primary job from its date, so that date mean has no primary prediction; a pooled remaining class extension is explicitly beside it. The complete per span intervals and inside flags, with the held out fit error included, are in `hierarchy-model-01-v4.json`, field `leave_one_job_out`.

## Beside and own checks

| Test 14 control | Model high emission minus low emission | 90 percent interval |
|---|---:|---|
| X | −0.01131 | −0.01792 to −0.004461 |
| Y | −0.02276 | −0.03181 to −0.01491 |

These contrasts come from the joint four circuit fit, with 400 bootstrap draws. The job remains NOT USABLE under its own rule. Source: `fits-model-01-v4.json`, field `test14_inphase_control`.

Every eligible pair in the same set and span is included in the co switching table: 12 pairs, with correlations at lag zero and at lags one through five in both directions, each compared with 200 circular shifts. The primary exact binary calculation gives zero pairs above the lag zero 99th percentile and one above the separately calibrated maximum across all eleven lags. It makes no statement that a pair is coupled. Source: `checks-model-01-v4.json`, fields `co_switching` and `co_switching_summary`.

A centered floating calculation had counted one lag zero exceedance with a margin of only 2.78e−17. Recalculation from exact integer binary counts makes this an equality. The original table, the corrected table and the dated correction are retained. This is a numerical correction, not a changed threshold.

| Recovery source | Trials | Inner draws per trial | Smallest coverage | Largest coverage |
|---|---:|---:|---:|---:|
| `t12-job1-q143-s1` | 200 | 400 | 0.895 | 0.935 |
| `t12-job1-q143-s2` | 200 | 400 | 0.88 | 0.955 |
| `t14-job1-q143-s2` | 200 | 400 | 0.83 | 0.94 |
| `t10-job1-q11-s0` | 200 | 400 | 0.87 | 0.92 |

The four sources are the lowest, lower middle and highest fitted duties among all twelve 143 spans, and the first eligible other processor span in the declared ordering. All 800 outer trials and 320000 inner refits are retained. Recovery bias and coverage for every emission, duty and length are in `checks-model-01-v4.json`, field `recovery`. Coverage ranges from 0.83 to 0.955, and no parameter meets the below 0.80 limitation rule. This simulation checks the estimator under its own model; it is not a finding about model adequacy on the record.

The primary dwell comparison is testable in 25 of 27 spans. Two 143 spans, test 11 job 2 spans 0 and 1, have probabilities below 0.01, respectively 0.0069965 and 0.0009995. The kickoff trigger requires more than two such 143 spans, so it is not triggered. The two remaining untestable spans have no complete low state dwell. The first and last dwells are censored in both record and finite window reference. The uncensored geometric reference alternative has no probability below 0.01; the result is sensitive to the stated reference construction. Source: `checks-model-01-v4.json`, fields `dwell_summary` and `fit_against_record`.

The complete autocorrelation comparison covers lags one through twenty, including binomial observation variance and a finite window alternative. The middle fifth comparison exposes a substantial strain in test 11 job 2: observed fractions 0.080, 0.078 and 0.094 against fitted mixture fractions about 0.0000285, 0.0000241 and 0.0000285. The alternative prediction within the observed bounds is retained as well. Source: `checks-model-01-v4.json`, field `fit_against_record`, entries for those spans, fields `record_mid_sweep` and `mid_sweep`.

## Prediction scope

The stated primary hierarchy has a fixed mean for each of two observed dates. It does not identify the mean of a third date, a population of future emissions, future span membership or future durations. Consequently the hierarchy alone does not issue unrestricted predictions for the third date. That limit is explicit for every requested family; no missing parameter is silently supplied.

A separate conditional empirical day extension provides numerical intervals and probabilities. It chooses one observed date once for the whole simulated day, preserves a shared population mean across both jobs, and shares one emission vector across each job. The additional date, emission, row allocation and duration assumptions are recorded before simulation in `forecast-plan.json`. They rest on nine spans, three monitor jobs and two UTC dates. They are model assumptions, not further observations.

Each scenario has 2000 complete simulated days. The first 1000 set the marginal intervals; the remaining 1000 calibrate joint family misses with shared day and job dependence. A conservative Monte Carlo upper bound determines the primary cutoff, with the point estimate cutoff and independent binomial calculation beside. The likelihood rejection probability uses the first 100 simulated days per scenario, each with 400 null draws at every relevant boundary. All intervals carry the conditional scope. A sharing estimate of one records 2000 successes in 2000 simulated days, with a 90 percent Monte Carlo interval of about 0.998503 to one. It remains a finite conditional simulation estimate. Calibrated scoring also requires the actual row allocations, shot count and monitor circuits to match the stated scenario; a matching span count alone is insufficient. Quantities outside that template remain raw comparisons without a calibrated family decision. Seconds comparisons carry the additional donor duration assumption.

The shuffled weight interval assumes its estimator lies within 0.011 of the time averaged duty. That relation was not compared on one shuffled job. Its sd also borrows the population correlation length in seconds and the archived shuffled span durations. The absent complete A26 method means the corresponding future computed score remains unavailable. The real future order probability is not issued; an order preference probability conditional on generation in returned order is beside it.

## Conditional prediction intervals

| Spans per job | Duty under threshold | Fitted duty | Test 15 length in sweeps | Fitted length in sweeps | All spans sharing probability |
|---|---|---|---|---|---:|
| 2 | 0.242 to 0.453 | 0.2421 to 0.4532 | 3 to 12 | 1.997 to 11.5 | 1 |
| 3 | 0.244 to 0.452 | 0.2433 to 0.4532 | 3 to 13 | 1.957 to 12.07 | 1 |
| 4 | 0.25 to 0.456 | 0.2501 to 0.4558 | 3 to 12 | 1.992 to 11.24 | 1 |

Source: `predictive-summary.json`, field `scenarios`. The full emission intervals, conditional seconds, expected boundary counts, count intervals, joint miss cutoffs, job mean difference and uncertainty on estimated probabilities are in the prediction files. Those files are written after this report and the completed checks, ready for the author to hash before the planned run.

## Readings, labelled

Reading of fit: the model supplies an inspectable description of shared states, posterior occupancy and transition statistics. Its agreement with its own recovery simulations does not remove the middle fifth mismatch, the improvement from free emissions, the two dwell comparisons or the undefined positive correlation length. The dwell conclusion also depends on the explicitly retained reference construction. The record therefore supports a descriptive fit with visible strain, not an unrestricted claim of adequacy.

Reading of spread: under the stated hierarchy, the duty spread is not distinguished from zero at the profile interval used here, while the correlation length spread exceeds the modelled within span uncertainty. This answers the requested spread question within the stated classes and error model. It does not identify a third date population.

Reading of co switching: the table compares decoded paths under circular shifts and states its counts. It does not identify a connection between qubits, explain a shared pattern or assign its origin. The exact tie correction shows why the raw correlations and null draws are retained.

Reading of resolution: the model cannot see events faster than one sweep, a change of emissions inside a span, or a state beyond its two state description. A time conversion further depends on chronological returned order and even sweep spacing. These limits remain attached to the conditional predictions.

## Sequence, corrections and reproducibility

Required source reading preceded analysis code. Data construction preceded fits. An early execution of the beside readings and own checks overlapped the final hierarchy and boundary work, so it is retained as a declared pilot rather than presented as the requested serial execution. After complete stage 3 at 02:48:46 UTC, the full official checks were replayed from 02:49:33 UTC with the same seeds and choices. The final numerical correction and checks completed at 02:55:07 UTC. Predictions were simulated only after that completion.

The pilot and official recovery parameter summaries agree exactly. Numerical retry differences in individual vectors are at most about 1.07e−13, with one interval endpoint differing by 4.44e−16. The pilot optimizer flags are retained; no remaining official recovery flag remains. An early provisional assembly of the stage 3 file occurred before boundary retries finished and was replaced after the complete process; both command records remain. The initial forecast run was replayed solely to record convergence status for both order fits. No choice was made by which result was preferred. A separate audit refitted all 600 jobs from the first 100 simulated days of each scenario with the scorer initialisation. The largest differences were about 0.0000997 in duty and 0.00511 sweeps in length, with no change in interval inclusion. All 348000 saved predictive quantity values were defined. The audit covers that stored subset, not every forecast refit. Sources: `checks-model-01-v4.json`, field `completion_audit`, and `forecast-estimator-audit.json`.

Scripts, command records, seeds, versions, raw bootstrap draws, failed initial attempts, independent audit, scorer rehearsal and final hashes are included. The numerical runtime is Python 3.14.8, NumPy 2.5.4 and SciPy 1.18.1. The C likelihood is checked against exhaustive short paths, and the independent audit recomputes likelihoods, posteriors, paths, boundaries, hierarchy and recovery summaries without importing the main fit implementation. `run.log` records commands and links each component log.

The author and Mantri may read these records and recount what they can. This report adopts nothing.
