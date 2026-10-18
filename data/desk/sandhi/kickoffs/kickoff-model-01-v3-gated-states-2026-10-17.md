# Kickoff Model 01, version 3: the gated states, with test 11 and the weight channel at the record's own resolution

Date: October 17, 2026. Author: Anish Patel. Prepared with Mantri (main). For: a desk runner with no hardware access (run 3, on the desk runner, in a fresh session, from the bundle `model-01-bundle-v3-2026-10-17.zip`). No job is submitted anywhere; nothing here touches the public repository, the website or the support ticket. The bundle carries the records of tests 7 to 11 and this kickoff; it carries no output of runs 1 or 2, and the runner is not given any.

Why version 3. Run 2 (version 2, October 17) gave a four-channel model that passed its own check per channel and wrote bets for test 11, which ran the same evening on ibm_fez qubit 143 (one shuffled job under test 7's rule; two monitor jobs at the antiphase wait, 148 repeats each on a 0.6 s clock). Three of the four bets held; the weight bet did not, and the reason is a defect of the kickoff, not of the record: the weight channel's floor was a fixed 0.10, set from one example, and test 11's weight changed across a span boundary by 0.063 in span means at twenty standard errors, invisible to the channel. The frequency channels learned per-record floors in version 2; the weight channel learns them here. Test 11 also added what the earlier records could not: the weight read on a one-second clock within spans (nothing moved) and across boundaries (it did), a weight walk across an hour under one stamp, and a split that did not move across a calibration stamp while the frame moved by 63 kHz.

Three sentences to carry verbatim: "The model is a kinetic description; it names no cause." "A record below its own floor is censored, not absent." "The predictions are the model's, written before the run they predict, and they are what can prove it wrong."

## 0. Rules and conventions

- Kinds: every event count and exposure is a computed fact of the archived records; every rate and interval is a model's output; the readings in section 6 are readings. No sentence says why a state changes.
- No dashes; no "proves", "reveals", "kill", "verified", "benchmark"; no vendor or machine ranking; no cause named; "switch", "event", "state" and "channel" are the model's words and are defined in section 2. "Telegraph", "parity", "defect" and "channel" in the biological sense do not appear in the report (the test 7 and test 11 records carry a diagnostic named "telegraph"; quote it only by its field name).
- The bundle is the only input. Nothing is fetched. The bundle's `SHA256SUMS` is checked first and the check reported.
- float64; seeds recorded; every figure in the report traceable to a file and a field in the bundle.
- **Where a definition cannot be applied as written, say so and record every alternative beside; where the choice is between a selected subset and the complete eligible set, the complete set is primary**, whatever counts fewer events. (Version 2's "count fewer events" tie-break sent run 2 to a selected weight population; it is retired.)
- Deliverables, in a folder `model-01-v3/`: `report-model-01-v3.md`; `events-model-01-v3.json`; `rates-model-01-v3.json`; `dependence-model-01-v3.json`; `model-check-model-01-v3.json`; `estimators-model-01-v3.json` (section 2.6); `predictions-model-01-v3.md` and `.json` (section 7, written last); the scripts as run; `run.log`; `SHA256SUMS`.

## 1. The data, in the bundle

Tests 7 to 10 as version 2 listed them (`t7/`, `t8/`, `t9/`, `t10/`, `span-check/`, `rules/`; field names as version 2 named them). New:

| test | processor | design | files |
|---|---|---|---|
| 11 | ibm_fez, qubit 143 | job 1: test 7's design on day 2 (260 shuffled positions, 2 copies × 1,500 shots); jobs 2 and 3: the monitor at 5.6 µs, 148 repeats of X then Y at 1,000 shots, 300 circuits, fixed order, about a minute apart | `t11/fits-t11.json` (job 1's fits, A26-style per-span weights at `jobs.1.span_readings_A26`, the nearest-three boundary changes at `jobs.1.weight_changes_across_boundaries`; the monitor jobs' θ_k, r_k, s_k, w_k, spans, switches, levels under `jobs.2` and `jobs.3`; `R0`; `gap_between_jobs_2_and_3`; `counts_of_the_run`), `t11/counts-t11-job{1,2,3}.json` (the raw counts with labels and the execution metadata), `t11/report-t11.md`, `t11/tables-t11-series.md`, `t11/rulings-t11.md`, `t11/stamps-t11.csv`, `rules/t11-rule.md` |

Facts of test 11's record the runner reads before anything else (`t11/report-t11.md` sections 1, 4 and 6): the provider's spans were 101, 100 and 99 positions; in job 2 position 100 ran in the first span and position 99 in the second; every span boundary of both monitor jobs fell inside a repeat (job 2: repeats 49, 50, 100; job 3: 50, 100); the gaps at one boundary of each job were 14 to 15 s and at the other 5 ms; the stamp (18:48:16 UTC, October 17) did not change across the three jobs; the gap between jobs 2 and 3 was 63.5 s.

## 2. The events, defined before any count

Version 2's definitions stand except where this section changes them: the line observation (A at most 1.0; r at least 0.08), the per-record threshold T_k for frequency (2.1), the alternation exclusion (2.2), the straddling repeat for the scans (2.3), the frequency channels W and F with 4 kHz censoring and the record's-own-floor count beside, the kind events, the copies check split by span, the stamp channel S.

### 2.1 Span assignment and the boundary pair, for every design

A position belongs to the span the provider's record places it in, whatever its number; a repeat belongs to the span that ran both of its circuits; a repeat whose circuits ran in different spans is a straddling repeat, excluded from the within channel. **The boundary pair at a span boundary is the last whole repeat before it and the first whole repeat after it, whether or not a straddling repeat lies between them** (this is test 11's boundary table and version 2's scan convention, now one rule for monitors and scans). Where two straddling repeats lie at one boundary (test 11 job 2, repeats 49 and 50), the pair is 48 and 51. The gap of the boundary is the provider's gap between the spans. Test 10's boundary counts are unchanged by this (no repeat straddled); test 11's gain four boundary trials in phase and four in weight that the rule's own verdict count could not test.

### 2.2 The weight observed per span, at the record's own resolution

For every usable job in which a weight is defined (a shuffled job whose verdict is TWO FIXED FREQUENCIES or NOT SETTLED with b inside (0.05, 0.95); a monitor job on a confirmed two-line qubit at its antiphase wait, which is test 11's jobs 2 and 3 only), the **weight per span** is: for a shuffled job, the inverse-variance mean of the upper line's implied weight over the positions passing the lever in that span, with its standard error (A26's method; the fits files' `weight_in_execution_order.positions` for the kingston jobs and 143's test 7 record, `jobs.1.span_readings_A26` for test 11); for a monitor job, the mean of w_k over the span's whole repeats, with the larger of the propagated error and the scatter over √n. **A weight boundary event at the record's own resolution** is a difference of adjacent span means exceeding five times its combined standard error. Beside it, **the fixed-floor count**: the nearest-three plain-mean change at 0.10 (version 2's definition, test 11's ruling 3), so that run 2's ledger and the model's scored bet stay comparable. Both counts are fitted (p_B at the record's resolution, primary; p_B at 0.10, beside). Every eligible qubit-job with a span record enters; the span check's tabulated set is reported as the subset it is.

### 2.3 The weight within a span (channel W_B), monitor jobs only

A consecutive pair of whole repeats inside one span in a monitor job with a defined weight is a within-span weight trial; it is an event when |w_(k+1) − w_k| exceeds the larger of 0.10 and five times the combined standard error (test 11's rule), **and, beside, at the record's own resolution**: each span's scatter of w_k about its mean (χ² per degree of freedom) and a weighted straight-line slope of w_k against k per span, reported, so that a walk within a span that no single pair resolves is on the record. Exposure as for channel W (the repeat period from the span record). Test 11 supplies 285 pairs; the channel's rate λ_B is fitted on them alone and said to be so.

### 2.4 Between jobs (the gap class), frequency and weight

Version 2's between-jobs frequency class stands (test 10: 1 in 63 at 4 kHz). A **between-jobs weight trial** is the last span's weight of one job against the first span's weight of the next job on the same qubit under the same stamp, **only where both are the same estimator**: test 11's jobs 2 to 3 (monitor to monitor) is one trial; job 1 to job 2 (shuffled to monitor) is not a trial and goes to section 2.6. The event rule is 2.2's. Reported separately, never pooled with p_B.

### 2.5 The stamp channel, extended

Version 2's channel S stands (pair 1, 16 of 47). Add: **143 across the stamp between test 7 and test 11** (one crossing: the S fit's detuning moved by about 63 kHz, an event; the kind did not change). And a second stamp observable, reported beside and not fitted: **the split across a stamp**, δ on day 2 against day 1 for every qubit that was TWO FIXED FREQUENCIES on both (143: 44.82 to 44.70 kHz; kingston's 43 between tests 8 and 9 if both intervals are in the records), with the difference in units of the combined interval.

### 2.6 The two weight estimators, compared before either predicts

Test 11 holds the same qubit's weight by two methods within one hour under one stamp: the shuffled job's per-position implied weight (P held at its fit) and the monitor's w_k from r_k and R0. The runner tabulates, in `estimators-model-01-v3.json`: job 1's per-span weights and its whole-job b; jobs 2 and 3's per-span weights; the gap in time between job 1's last span and job 2's first; R0 and its sensitivity (how much w moves for a 10 percent change in R0); and the statement of what each estimator assumes (the shuffled fit: one weight over the positions it averages; the monitor: equal amplitude and decay on both lines, exact antiphase). No reconciliation is attempted and no number from one estimator is corrected by the other. The predictions in section 7 that concern the monitor use the monitor's estimator and say so; those that concern a shuffled job use the shuffled estimator.

## 3. The model

Five fitted channels: λ_F within a span (frequency, 4 kHz, censored); λ_B within a span (weight, monitor only); p_F at a boundary (frequency); p_B at a boundary (weight, at the record's own resolution; the 0.10 count beside); p_S across a stamp. Poisson for the λ's, Binomial for the p's, Jeffreys priors, posterior medians and 5th to 95th percentiles, as version 2. Classes as version 2, plus for p_B: design (shuffled against monitor), processor record (143 against the kingston qubits), gap length (5 ms, under 1 s, 1 to 3 s, over 3 s, the 14 to 15 s gaps of test 11 as their own bin). The between-jobs classes and the split observable are reported, not fitted into any p.

## 4. The dependence tests

As version 2, per channel; across channels only F against B. Add: p_B at the record's resolution, shuffled against monitor (Fisher); and the gap-length split for p_B, since test 11 put a 14 s gap and a 5 ms gap in each job.

## 5. The model's own check

As version 2, per channel, 1,000 draws, with the sensitivity per channel. Add: the check of run 2's four bets against test 11's record, computed here from the ledger (the counts at the floors the bets were written at), as a table: bet, number, outcome, inside or outside its interval. This is the model's scorecard and is a computed fact, not a reading.

## 6. Readings, labelled

One paragraph each: the shape in five rates (whether the within-span rates are consistent with zero on both channels; whether p_B at the record's resolution is of a different order from the 0.10 count; where the gap class sits); what the span-mean steps and the hour's walk are and are not (levels per span that differ; no claim about what sets them; the estimator caveat); the floors, now per channel, and what each leaves out.

## 7. The predictions, written last, for the author to hash before the next run

From the fitted rates and nothing else, each from the channel named and the estimator named:

1. **A third day of test 11 on 143** (the same three jobs, under whatever stamp is in force): the probability of at least one weight boundary event at the record's own resolution in the shuffled job's two boundaries, and in the monitor's four; of at least one within-span weight switch in about 170 s (λ_B) and the expected within-span scatter; of at least one phase switch at any boundary or within spans (p_F, λ_F, at the record's own floor, about 23 kHz); of a weight change between the two monitor jobs at the record's resolution; and, across the stamp, of the frame moving by 4 kHz or more (p_S) and of the split staying within 0.5 kHz of 44.7 (from the split observable's spread, stated as a reading if the counts do not support a rate).
2. **Scan and monitor back to back on kingston under one stamp, on test 10's set S:** as version 2, from p_F and λ_F, with the boundary pair of 2.1.
3. **Even odds of one within-span event,** frequency (λ_F) and weight (λ_B), in qubit-seconds, both floors.
4. **What would count against the model:** per channel, the predictive intervals for the declared trial counts; any within-span weight event in the next 1,000 monitor pairs at the 0.10 floor; a split that moves by more than 1 kHz across a stamp on a confirmed two-line qubit.

Each prediction carries the interval it comes from. These are the model's bets, not the author's or Mantri's; Mantri's bets on the same runs are sealed separately.

## 8. Runs and the comparison

Run 3 is on the desk runner in a fresh session. Mantri compares its ledger with run 2's row by row on the records both runs saw (tests 7 to 10): the frequency ledgers should be identical, the weight ledger should differ only by the record's-own-resolution column and the straddling-pair rule (which adds no kingston trial), and any other difference is a difference in reading the records and is settled by the records.

## 9. What changed from version 2, and why

1. The weight floor of 0.10 was fixed from one example and hid test 11's 0.063 step (twenty standard errors in span means). Version 3 reads weight events at the record's own resolution, with the 0.10 count beside (2.2). Mantri's error, in versions 1 and 2.
2. The boundary pair across a straddling repeat is one rule for monitors and scans (2.1), after test 11's four boundaries fell inside repeats and the rule's verdict count had no trials. Mantri's error in the test 11 rule, inherited from test 10.
3. The within-span weight channel exists (2.3), because test 11 read it.
4. Between-jobs weight trials (2.4), same estimator only.
5. The stamp channel takes 143's crossing and the split observable (2.5).
6. The two weight estimators are tabulated before either predicts (2.6).
7. The "count fewer events" tie-break is retired for "the complete eligible set is primary" (section 0), after run 2 showed it selects a population.

No record changed. No rule changed. The model's form is the same with one more fitted channel and the weight channel's floor replaced.
