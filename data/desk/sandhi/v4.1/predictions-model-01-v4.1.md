# Model 01 version 4.1 predictions

The model is a kinetic description; it names no cause.

The sweep clock is the returned order; seconds are conditional on that order being chronological.

The predictions are the model's, written before the run they predict, and they are what can count against it.

These are model outputs from the conditional empirical day extension over 15 spans, five monitor jobs and three UTC dates. The third date is included in the fit. The predictions address a future run; they are not predictions of day 3.

## Designs and calibration

Next 143 monitor run, two jobs, 300 positions each, 1000 shots, 5.6 microseconds X then Y, any span counts.

One longer job of the same circuits, 600 positions, 1000 shots, about six spans.

C1 at scoring time through actual design. Nominal intervals never gate eligibility. C2 actual sweep time with donor endpoint range widened ten percent on each side. C3 supplied per span A26 weights.

The actual span counts may differ between jobs. The full eligible design is primary. The JSON retains each nominal design and every indexed boundary probability.

## Nominal intervals

| Quantity | D1 nominal 90 percent interval | D2 nominal 90 percent interval |
|---|---|---|
| `threshold_duty` | 0.242 to 0.452 | 0.242 to 0.448 |
| `model_duty` | 0.242486 to 0.451225 | 0.241523 to 0.447757 |
| `t15_tau_sweeps` | 3 to 13 | 3 to 13 |
| `t15_tau_seconds` | 0.0825409 to 0.357546 | 0.0830816 to 0.36002 |
| `model_ell_sweeps` | 2.30526 to 11.6329 | 2.34442 to 11.8508 |
| `model_ell_seconds` | 0.0632205 to 0.320689 | 0.0649261 to 0.328193 |
| `q_H_X` | 0.641742 to 0.734124 | 0.641125 to 0.734215 |
| `q_L_X` | 0.265606 to 0.364421 | 0.265385 to 0.3639 |
| `q_H_Y` | 0.773392 to 0.919793 | 0.773515 to 0.919624 |
| `q_L_Y` | 0.0545092 to 0.136347 | 0.0546199 to 0.136242 |
| `job_mean_duty_difference` | −0.0710167 to 0.0716833 | unavailable |
| `shuffled_weight_A26` | 0.245208 to 0.454959 | unavailable |
| `shuffled_sd` | 0.0268543 to 0.065166 | unavailable |

D1 uses day 3 design metadata as a nominal example. D2 uses six equal position blocks with first and last readout pairs excluded and the mean donor sweep time. These examples do not predict the future execution metadata.

## Nominal counts and probabilities

| Design | Every span SHARED | Any likelihood rejection at one percent | Every returned order fit preferred |
|---|---|---|---|
| D1 | 1 | 0.69 | 1 |
| D2 | 1 | 0.59 | 1 |

A probability estimate of one is a finite simulation estimate. Monte Carlo intervals and counts are in the JSON. The order preference probability is conditional on simulating in returned order; it is not a probability that the returned order is chronological.

| Design | Boundary word | Expected count | Nominal 90 percent count interval |
|---|---|---|---|
| D1 | NO CHANGE | 3.7965 | 3 to 4 |
| D1 | BETWEEN | 0.1815 | 0 to 1 |
| D1 | CHANGE | 0.022 | 0 to 0 |
| D1 | NOT READ | 0 | 0 to 0 |
| D2 | NO CHANGE | 4.786 | 4 to 5 |
| D2 | BETWEEN | 0.1965 | 0 to 1 |
| D2 | CHANGE | 0.0175 | 0 to 0 |
| D2 | NOT READ | 0 | 0 to 0 |

## What would count against the model

| Design | Family | Nominal cutoff | Bets |
|---|---|---|---|
| D1 | duty | 6 | 12 |
| D1 | correlation | 9 | 24 |
| D1 | emissions | 4 | 8 |
| D2 | duty | 6 | 12 |
| D2 | correlation | 9 | 24 |
| D2 | emissions | 3 | 4 |

Family cutoffs are the smallest miss counts whose one sided 95 percent Monte Carlo upper probability is below five percent. The actual design is calibrated again at scoring time. Any 143 monitor span reading INDEPENDENT or UNDECIDED counts against sharing. More than one monitor span with a dwell probability below 0.01 counts against the dwell description. A CHANGE boundary counts against its prediction where that indexed boundary had CHANGE probability below five percent. The list is unchanged from v4.

No channel is added for the middle span pattern, and no prediction beyond stationarity within a job is issued for it. The shuffled weight remains the v4 assumption about a second estimator, now read from its supplied fits. The observed borrowed sd remains unavailable without a unique specified population length.

Both archive rehearsals are computation checks, not prospective validation. The author and Mantri may recount what they can. Nothing here is adopted.
