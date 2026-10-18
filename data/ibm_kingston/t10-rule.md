# Test 10: the rule, fixed before the run

Written 17 October 2026, before any job was built or submitted. Author: Anish Patel. This file states the design, the analysis and the verdict rule for test 10 on ibm_kingston. Its SHA-256 is posted publicly as an issue before any job is submitted, and the file is published unchanged after the run. The verdict rule is checked on the desk, on simulated traces, before the hash and again by the runner after it; both checks are published with the run.

## The question

The provider's execution record, read after tests 7, 8 and 9, shows that each of those jobs ran as three execution spans of about 100 circuits, and that every large change of a qubit's fringe within a job that those tests reported coincides with a boundary between two spans: finding 28's weight step on ibm_fez 143 (positions 99 to 100), the line switch on ibm_kingston 134 in test 8, the weight changes on 43 in tests 8 and 9, and 18 of the 20 change points found by test 9's scan. The gaps between spans were 5 ms, 6 ms, 0.9 s and 10 s, and the changes occurred at all of them. What those tests cannot say is whether a qubit's fringe also changes within a span, at what rate, and with what distribution of dwell times, because their circuits were shuffled (tests 7 and 8) or their repeats were five seconds long (test 9).

On ibm_kingston, on one day, with one wait per qubit read in two quadratures and repeated in fixed order every 0.6 s through a job: for each qubit, does the fringe's phase switch within an execution span, only at the boundaries between spans, or not at all; at what rate within spans; and, where there are enough switches, are the dwell times memoryless?

## The code

Manacitra at the v0.7.0 release, commit `b782d00238b7df40e1fbfd4da674968cf653c8d7`, installed unedited, for the single-qubit circuit form (`part_b_circuit(1, wait_dt, "R")`, `even_wait`, `to_backend`) and the readout survey. The many-qubit circuits with one wait per qubit, the per-repeat phase, the switch test and the verdict are the run's own script, published with the data and checked on the desk as the last section says. **The result's execution metadata (`execution_spans`, and everything else under the result's `metadata`) is saved with the counts at fetch; a job whose metadata cannot be saved is recorded as such and its spans are retrieved again before analysis.**

## The qubit set, fixed by procedure

1. **Job 0, the readout survey,** as test 9's: every qubit measured in |0⟩, and X on every qubit then measured; 2 circuits, each 2 copies of 2,000 shots, interleaving seed 10301. Measured readout error e per qubit, copies pooled; the published value beside it.
2. **Eligible:** every operational qubit with measured e at or below 3%.
3. **The set S,** on the live coupling map at build, each qubit taken only if eligible and not adjacent to any already taken, in this order: 43, 134, 11, 120, 95 (test 9's two-line and candidate qubits); then 0, 33, 62, 36, 155, 101, 67, 69, 89, 152, 132 (test 9's STEPPED and MOVING qubits of job 2 not already taken, in the order 7-boundary first then the rest ascending); then 28, 118, 38, 54, 47, 80, 128 (test 9's day-2 copies-signature qubits not already taken); then 125, 87, 149, 31, 77, 58, 7, 18; then every remaining eligible qubit in ascending index.
4. **The complement S′:** the same procedure over the eligible qubits not in S, with no seeds.

Both sets, the survey's values and the properties used are recorded before job 1 is submitted. There is no redraw.

## The wait per qubit, fixed here

Each qubit of a set carries its own wait in every circuit of the job (the circuit's duration is the longest wait in it; shorter waits are padded by the delay's own length, with nothing else on the qubit). The waits:

| qubit | wait | why |
|---|---|---|
| 43 | 46 µs | test 8's two lines on 43 are 10.9 kHz apart (−5.97 and −16.86 kHz; test 9's scan plateaus agree): at 1/(2 × 10.9 kHz) the two lines are in antiphase |
| 11 | 6 µs | test 9's lines on 11 are 82.1 kHz apart (3.64 and −78.46): antiphase at 6.1 µs |
| 120 | 6 µs | test 9's lines on 120 are 81.6 kHz apart (72.84 and −8.73): antiphase at 6.1 µs |
| 134 | 12 µs | 134's lines differ between days (43.4 kHz apart in test 8; about 35 and about 74 in test 9's two jobs); 12 µs is antiphase for the test 8 spacing and a frequency monitor otherwise, unambiguous to ±42 kHz |
| every other qubit | 20 µs | a frequency monitor: a phase change of 1 radian is 8.0 kHz, the unambiguous range is ±25 kHz about the job's mean, and the envelope on a median kingston qubit (τ about 100 µs) keeps four fifths of its amplitude |

The scheduled wait of every qubit in every circuit is recorded; the requested and scheduled waits are compared.

## The run: job 1 on S, job 2 on S again, job 3 on S′, as the allowance permits

Settings for every job: dynamical decoupling, gate twirling and measurement twirling all off; no readout error mitigation.

- **One repeat** is two circuits: X (H, delay, H, measure on every qubit of the set, each at its own wait) then Y (the same with S† before the final H), each 1,000 shots.
- **A job** is: the two readout circuits (measure; X then measure), then 148 repeats in the same order every time, then the two readout circuits again: 300 circuits, each 1,000 shots, submitted in that order and not interleaved. The position of each circuit in the result is taken as its place in execution, and the result's execution spans say which positions ran in which span.
- **Job 1, on S.** **Job 2, on S again,** the same circuits rebuilt, submitted only if the allowance left after job 1 is fetched is at least 1.5 × T1 (job 1's machine time as IBM recorded it). **Job 3, on S′,** submitted only if the allowance left after job 2 is fetched (or after job 1, if job 2 did not run) is at least 1.5 × T1. The decisions are recorded before each job is built.
- **Structural checks before submission, on the circuits as built and again on the backend's snapshot:** every instruction acts on a qubit of the set; no two qubits of the set share an edge; each qubit carries exactly the two-gate sequence with its own scheduled wait; the exact noiseless P(1) is 0 for X, 0.5 for Y, 0 and 1 for the readout circuits, on every qubit; the 300 positions are in the rule's order. Any failure stops the run.
- **The estimate:** test 9's job 2 rate per shot times 300,000 shots, with the half-again allowance and IBM's formula beside; job 1 is submitted only if its estimate with the margin is within the instance's remaining allowance as read before it.
- **Each job is submitted once.** A failed or cancelled job is recorded and not resubmitted; its qubits report no verdict.

### When

ibm_kingston's published stamps for the previous 48 hours are read before building; no job is submitted inside the computed window or while the day's cycle is in progress; if the 48 hours show no pattern or the interval lies outside 20 to 30 hours, that is recorded and the window does not apply. The stamp at build, at each submission, every 5 minutes, and after each fetch is recorded.

## The analysis, per qubit, per job

1. **The midpoint c** is the mean of the four readout circuits' P(1) on that qubit (two at the start, two at the end: P(1|0) twice and P(1|1) twice), the level a half-and-half superposition reads.
2. **Per repeat k = 1, ..., 148:** P_X,k and P_Y,k from that repeat's two circuits; the vector v_k = (P_X,k − c, P_Y,k − c); its angle θ_k = atan2(P_Y,k − c, P_X,k − c) and its length r_k. The angle's standard error s_k = σ_k / r_k with σ_k² = (P_X(1 − P_X) + P_Y(1 − P_Y)) / (2 × 1,000), the binomial error of the two proportions, floored at 0.02 rad.
3. **Usable:** measured e at or below 3% in job 0 and the median r_k over the job at least 0.08 (so that s_k is at most about 0.2 rad).
4. **The spans:** from the result's execution metadata, each repeat is assigned the span that ran both of its circuits; a repeat whose two circuits ran in different spans is named and excluded from the switch counts (its θ_k is still reported).
5. **The unwrapped phase:** the series θ_k with each successive difference wrapped to (−π, π]. A difference of exactly π in size is reported with its sign undetermined.
6. **A switch** between consecutive repeats k and k + 1 is counted where |θ_(k+1) − θ_k| (wrapped) exceeds the larger of 0.3 rad and 5 √(s_k² + s_(k+1)²). It is **within a span** if both repeats ran in the same span, **at a boundary** if they ran in consecutive spans.
7. **The counts:** n_within and n_boundary per job; the within-span time, the sum over spans of (the number of consecutive within-span repeat pairs) × the repeat period, where the repeat period is the span's duration from the execution record divided by the number of repeats it ran; the within-span rate n_within per second of within-span time, with its 90% interval from the Poisson distribution.
8. **The levels:** the plateaus between switches, each with its weighted mean phase; two plateaus whose means are within 3 √(the sum of their squared standard errors) are the same level; the number of distinct levels is reported.
9. **The slope within each span:** a weighted straight-line fit of θ_k against k over the repeats of each span, its slope in radians per repeat and in kHz per minute at the qubit's wait, reported for every usable qubit.
10. **The dwell times,** for a qubit with n_within at least 8 pooled over its jobs: the durations of the plateaus bounded by two within-span switches (plateaus cut by a boundary or by the job's ends are excluded), in repeats × the repeat period; their mean, their standard deviation over their mean, and the Kolmogorov test against an exponential distribution with the fitted mean (p-value reported; the test's threshold is 0.01).

## The verdict, per usable qubit, per job

| verdict | condition |
|---|---|
| **QUIET** | n_within = 0 and n_boundary = 0 |
| **SWITCHES AT BOUNDARIES ONLY** | n_within = 0 and n_boundary ≥ 1 |
| **SWITCHES WITHIN SPANS** | n_within ≥ 1 |

A qubit that is not usable is NOT USABLE with its numbers and is not counted. **The pooled verdict** over jobs 1 and 2 for a qubit of S is SWITCHES WITHIN SPANS if either job says so, else SWITCHES AT BOUNDARIES ONLY if either job says so, else QUIET.

**The dwell-time word,** only for qubits with n_within at least 8 pooled: **MEMORYLESS** if the Kolmogorov p-value is at or above 0.01, **NOT MEMORYLESS** otherwise; for fewer than 8 within-span switches no word is given and the dwell times are listed.

**The counts of the run:** the number of usable qubits returning each verdict, by job and pooled; every SWITCHES qubit listed with n_within, n_boundary, its within-span rate and interval, its levels and its wait; the number of qubits with a dwell-time word and which.

## Reported beside the verdicts, not used in them

1. **The execution record of each job:** the spans, their start and stop, their positions and the gaps between them; the repeat period per span; which repeats straddled a span.
2. **The boundary table:** for every usable qubit, the wrapped phase difference across each boundary with its standard error, so that the boundary's effect is on the record for the quiet qubits too; and the count of usable qubits whose phase difference across each boundary exceeds 5 standard errors, beside the count exceeding 5 standard errors across a within-span pair of repeats drawn at the same place in each span (the control for the boundary table).
3. **The antiphase qubits (43, 11, 120, 134):** their θ_k and r_k series in full, the levels found and their separation in radians, and whether the separation is within 0.3 rad of π (two lines in antiphase, the state switching between them) or not (the lines or their spacing are not as fixed).
4. **The frequency reading of the monitors:** for every 20 µs qubit, each level's phase converted to a frequency offset from the job's mean at 8.0 kHz per radian, and each switch's size in kHz.
5. **The two jobs on S beside each other:** per qubit, job 1's and job 2's verdicts and levels, and whether the phase at the end of job 1 and the start of job 2 differ by more than 5 standard errors (the gap between jobs as one more boundary, of minutes).
6. **Readout** from job 0 and from the four in-job readout circuits of each job, beside the published value.
7. **The sets,** the waits requested and scheduled, the calibration record, the estimates and the decisions.

The rule is not changed after the data, whatever they show.

## The desk check, before the hash

The analysis and verdict are run on simulated jobs of 148 repeats with binomial shot noise at 1,000 shots, spans of positions 0 to 99, 100 to 199 and 200 to 299, on a qubit of amplitude 0.45 about c = 0.5 with a 100 µs decay at a 20 µs wait unless stated, 100 trials each: (1) one line, steady: QUIET at 95% or more. (2) The same at amplitude 0.3 with a 30 µs decay (r about 0.15): QUIET at 95% or more. (3) One line stepping by 4 kHz at repeat 30 and back at repeat 80: SWITCHES WITHIN SPANS at 95% or more, with both switches found at the planted repeats in 90% or more. (4) The same with a 1 kHz step: recorded. (5) One line stepping by 4 kHz exactly at the first boundary and back at the second: SWITCHES AT BOUNDARIES ONLY at 95% or more. (6) A two-state telegraph in antiphase at 46 µs on a fringe of amplitude 0.4 with a 56.6 µs decay (43's), the state flipping with a mean dwell of 20 repeats: SWITCHES WITHIN SPANS at 95% or more, the number of switches within one of the planted number in 90% or more, and the levels' separation within 0.3 rad of π in 90% or more. (7) One line drifting by 2 kHz across the job: no switch called in 95% or more, and the slope reported. (8) A fringe whose weight between two antiphase lines changes within every repeat (b drawn fresh per shot at 0.5): NOT USABLE or QUIET, recorded. The thresholds (0.3 rad, five standard errors, the 0.08 floor on r, the 0.02 rad floor on s) are kept only if every required rate is met; a change before the hash is recorded in this section with its reason. Mantri's check before the hash (17 October, 100 trials per case): every required rate met at 100 of 100; both planted switches of case 3 found at their repeats in 100 of 100; case 5 counted 0 within and 2 at boundaries in 100 of 100; case 6's switch count within one of the planted count and the levels' separation within 0.3 rad of π in 100 of 100; case 7 read QUIET with the planted slope recovered; case 4, the 1 kHz step, read QUIET in 100 of 100, so the rule's switch floor at 20 µs is about 2.4 kHz (0.3 rad), which is named as a limit; case 8 read NOT USABLE (median r 0.02). Both checks, Mantri's before the hash and the runner's after it, use binomial noise and exponential decay only, which is a limit of the rule.
