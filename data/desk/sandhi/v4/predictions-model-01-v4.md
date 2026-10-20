# Model 01 version 4 predictions

The primary hierarchy does not issue an unrestricted forecast for a third date. It has means for only the two observed dates. The numerical predictions below are a separate conditional empirical day extension, whose additional assumptions are in `forecast-plan.json`.

The model is a kinetic description; it names no cause.

The sweep clock is the returned order; seconds are conditional on that order being chronological.

The predictions are the model's, written before the run they predict, and they are what can count against it.

These predictions address the planned 20 October 2026 run of test 11 on qubit 143. Their source class has nine spans, three monitor jobs and two UTC dates. Test 14 is excluded from that class. The emissions draw on only two dates, so their future distribution is an empirical assumption with little independent support.

## Sharing and boundary probabilities

| Spans per job | Every span SHARED | Expected NO CHANGE count | Expected BETWEEN count | Expected CHANGE count | Any own likelihood rejection at 1 percent |
|---|---:|---:|---:|---:|---:|
| 2 | 1 | 1.895 | 0.09 | 0.015 | 0.62 |
| 3 | 1 | 3.7765 | 0.1985 | 0.025 | 0.8 |
| 4 | 1 | 5.6745 | 0.282 | 0.0435 | 0.84 |

A sharing estimate of one records 2000 successes in 2000 simulated days. Its 90 percent Monte Carlo interval is about 0.998503 to one, and it remains a finite conditional simulation estimate. Counts cover adjacent spans within both monitor jobs. The likelihood probability also includes the comparison between jobs. Each indexed boundary has its own CHANGE probability in the JSON; the scorer does not substitute the pooled probability. The pooled uncertainty is computed over independent simulated days. Likelihood probabilities use the first 100 simulated days per scenario, with 400 null draws for every comparison. Their Monte Carlo intervals are in the JSON.

## Duties, lengths and emissions

| Quantity | Two spans per job | Three spans per job | Four spans per job |
|---|---|---|---|
| `threshold_duty` | 0.242 to 0.453 | 0.244 to 0.452 | 0.25 to 0.456 |
| `model_duty` | 0.24213 to 0.45321 | 0.24333 to 0.45319 | 0.25014 to 0.45579 |
| `t15_tau_sweeps` | 3 to 12 | 3 to 13 | 3 to 12 |
| `t15_tau_seconds` | 0.081829 to 0.35007 | 0.081829 to 0.37495 | 0.081829 to 0.35007 |
| `model_ell_sweeps` | 1.9974 to 11.503 | 1.9565 to 12.07 | 1.992 to 11.237 |
| `model_ell_seconds` | 0.053552 to 0.33177 | 0.052831 to 0.35225 | 0.053707 to 0.32605 |
| `q_H_X` | 0.64066 to 0.73504 | 0.64072 to 0.73534 | 0.64072 to 0.73544 |
| `q_L_X` | 0.26455 to 0.36524 | 0.26471 to 0.365 | 0.26448 to 0.36513 |
| `q_H_Y` | 0.77245 to 0.92031 | 0.77253 to 0.92036 | 0.77225 to 0.92008 |
| `q_L_Y` | 0.054313 to 0.13665 | 0.05438 to 0.13671 | 0.054289 to 0.1366 |
| `job_mean_duty_difference` | −0.088025 to 0.0831 | −0.07435 to 0.06375 | −0.06075 to 0.06 |
| `shuffled_weight_A26` | 0.23793 to 0.4539 | 0.2424 to 0.4554 | 0.2488 to 0.45624 |
| `shuffled_sd` | 0.024063 to 0.063599 | 0.023862 to 0.063243 | 0.023989 to 0.061844 |

All table entries are 90 percent intervals conditional on the declared empirical day extension and its row and duration scenarios. The actual row allocations, shot count and monitor circuits must match before a calibrated verdict is assigned. A matching span count alone is insufficient. Other designs retain raw uncalibrated comparisons. Seconds require the additional donor duration assumption. The first 1000 complete simulated days define intervals. The next 1000 calibrate misses jointly. A future family containing an unavailable quantity is not fully testable; missing quantities are not silently removed from the family.

The shuffled weight uses an explicit assumption that A26 is within 0.011 of time averaged duty, a comparison not made on one shuffled job. Its sd uses the population length and the archived shuffled span durations. The complete A26 estimator is absent, so the scorer reports that computed target unavailable. No substitute weight is scored.

The actual future returned order probability is not issued because chronology is not established by this record. The JSON gives an additional conditional probability that every returned order fit is preferred, under simulation in returned order. This is a model conditional preference, not a probability that the provider returns chronological data.

## What counts against the conditional model

| Spans per job | Duty family cutoff and bets | Correlation family cutoff and bets | Emission family cutoff and bets |
|---|---|---|---|
| 2 | 5 of 8 | 8 of 16 | 3 of 8 |
| 3 | 7 of 12 | 9 of 24 | 3 of 8 |
| 4 | 9 of 16 | 13 of 32 | 3 of 8 |

The cutoff is the smallest count whose one sided 95 percent Monte Carlo upper probability is below five percent. The smallest count using the point probability estimate is also listed in the JSON. The calibration preserves day and job dependence, including the paired estimates and repeated units.

Any monitor span reading INDEPENDENT or UNDECIDED counts against sharing. More than one monitor span with dwell probability below 0.01 counts against the dwell description. A boundary reading CHANGE counts against its conditional forecast when that specific boundary was assigned CHANGE probability below five percent. The known middle fifth mismatch, the two archived dwell failures and the reference sensitivity remain limits when these predictions are read.

The scorer and its local dependencies are hashed with these files in `FORECAST-SHA256SUMS`. It reads the future arrays, metadata and counts, reports unavailable definitions, and writes a scorecard. Its successful archival rehearsal is a computation check, not a prospective score. Nothing here is adopted by the report.
