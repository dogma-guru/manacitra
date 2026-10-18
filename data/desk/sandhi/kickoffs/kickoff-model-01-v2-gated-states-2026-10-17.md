# Kickoff Model 01, version 2: the gated states. A kinetic model of the kingston and fez records, with the event definitions corrected after run 1

Date: October 17, 2026. Author: Anish Patel. Prepared with Mantri (main). For: a desk runner with no hardware access (run 2, on the desk runner, from the bundle `model-01-bundle-v2-2026-10-17.zip`). No job is submitted anywhere; nothing here touches the public repository, the website or the support ticket. The bundle carries the same records as run 1's bundle and this kickoff in place of the first; it carries no output of run 1, and the runner is not given any.

Why version 2. Run 1 (the desk runner, October 17, from `model-01-bundle-2026-10-17.zip`) did what version 1 said and reported where version 1 was wrong. Five of its definitions let noise and fitting artefacts into the event counts, and one pooled two different observables into one probability. The errors were the kickoff's, which is to say Mantri's, and they are listed in section 9 so that the runner can see what changed and why. The model itself (section 3) is unchanged in form; it gains one channel, because the boundary channel of version 1 was two channels.

Three sentences to carry verbatim: "The model is a kinetic description; it names no cause." "A record below its own floor is censored, not absent." "The predictions are the model's, written before the run they predict, and they are what can prove it wrong."

## 0. Rules and conventions

- Kinds: every event count and exposure is a computed fact of the archived records; every rate and interval is a model's output; the readings in section 6 are readings. No sentence says why a state changes.
- No dashes; no "proves", "reveals", "kill", "verified", "benchmark"; no vendor or machine ranking; no cause named; "switch", "event", "state" and "channel" are the model's words and are defined in section 2. "Telegraph", "parity", "defect" and "channel" in the biological sense do not appear in the report.
- The bundle is the only input. Nothing is fetched. The bundle's `SHA256SUMS` is checked first and the check reported.
- float64; seeds recorded; every figure in the report traceable to a file and a field in the bundle.
- Where a definition cannot be applied to a record, say so, apply the reading that counts fewer events, and record the alternatives beside.
- Deliverables, in a folder `model-01-v2/`: `report-model-01-v2.md`; `events-model-01-v2.json` (every trial, per qubit, per test, per channel, with its floor, its exposure, its event flag and, where a pair is excluded, the reason); `rates-model-01-v2.json`; `dependence-model-01-v2.json`; `model-check-model-01-v2.json`; `predictions-model-01-v2.md` and `.json` (section 7, written last, to be hashed by the author before October 20); the scripts as run; `run.log`; `SHA256SUMS`.

## 1. The data, in the bundle

| test | processor | design | files used |
|---|---|---|---|
| 7 | ibm_fez, qubit 143 | 64-wait two-quadrature Ramsey, 260 shuffled circuits, 2 copies × 1,500 shots | `t7/fits-t7.json`, `t7/reading-t7.json`, `t7/report-t7-hardware.md`; the spans in `span-check/spans-t9.json` |
| 8 | ibm_kingston, 132 qubits | the same per qubit, jobs 1 and 2 on disjoint sets, job 3 on 43 and 134 | `t8/fits-t8-job1.json`, `job2`, `job3`, `t8/report-t8.md`; the spans of jobs 1 and 3 in `span-check/spans-t9.json` |
| 9 | ibm_kingston | job 1: the same on 67 qubits; jobs 2 and 3: an 8-wait scan, 18 repeats in fixed order, 292 circuits | `t9/fits-t9-job1.json`, `job2`, `job3`, `t9/beside-t9.json`, `t9/report-t9.md`, `span-check/spans-t9.json`, `span-check/span-compare-t9.json`, `t9/span-check-t9.md` |
| 10 | ibm_kingston | one wait per qubit, 148 repeats in fixed order, 300 circuits; jobs 1 and 2 on S, 3 on S′ | `t10/fits-t10.json.gz`, `t10/report-t10.md`, `t10/tables-t10-*.md` (the spans are in the fits file's `jobs.<n>.execution_record`; the per-repeat angle, length and standard error in `jobs.<n>.per_qubit.<q>.repeats`) |
| A26 | ibm_fez, 143 | the weight per span and the copies check split by span | `t7/a26-span-figures.md` (0.457, 0.315, 0.274; same-span Σz² 34.9 on 43, cross-span 836.8 on 85) |

The rule files `rules/t7-rule.md`, `t8-rule.md`, `t9-rule.md`, `t10-rule.md` are in the bundle for the designs and floors. The runner reads the reports' section 1 and the fits files' `meta` before anything else. Field names used below: test 9's per-repeat `Delta_MHz`, `A`, `s_MHz` (the bootstrap standard error with the rule's 0.25 kHz floor applied) and `chi2`; test 10's per-repeat angle, length and standard error as the fits file names them, with `kHz_per_rad` per qubit.

## 2. The events, defined before any count

An **event** is a change of a qubit's state between two consecutive observations of it. An **observation** is one repeat of test 9's scan or one repeat of test 10's monitor (one line fit or one phase), or, for the shuffled jobs, one execution span. The definitions:

### 2.1 Line observations and the per-record threshold

A repeat is a **line observation** when its fit describes a line: in test 9, the fitted amplitude A is at most 1.0; in test 10, the length r is at least 0.08 (both as in version 1). A repeat that is not a line observation is a **non-line observation**.

Every consecutive pair of line observations (k, k+1) carries **the record's own threshold** T_k, in kHz, which is what that record could have resolved as a change:

- test 9: T_k = max(1.0, 5 × sqrt(s_k² + s_{k+1}²) × 1000), with s in MHz from `s_MHz` (the rule's STEPPED gap clause: a gap above 1 kHz and above five gap standard errors);
- test 10: T_k = max(0.3, 5 × sqrt(s_k² + s_{k+1}²)) × kHz_per_rad, with s in radians (the rule's switch clause; 7.96 kHz per radian at 20 µs, 26.5 at 6 µs, 3.46 at 46 µs).

### 2.2 The alternation exclusion (test 9 only)

The per-repeat one-line fit near zero detuning has two solutions of similar χ² at different frequencies and different amplitudes, and the fit returns one or the other from repeat to repeat. A consecutive pair of test 9 line observations is **an alternating pair** when the two amplitudes differ by more than one third of their mean: |A_k − A_{k+1}| > (A_k + A_{k+1}) / 6. An alternating pair is not an event, whatever its frequency change, and contributes no exposure; it is written to the ledger with the reason `alternation`, and every qubit with at least one alternating pair is listed in the report with its pairs. The rule is the amplitude, not the frequency, because the frequency jump of an alternating pair (4 to 7 kHz on the kingston records) is the size the model is looking for and cannot be told from an event by its size. Run 1 counted these pairs as events; section 9 records it.

### 2.3 Straddling repeats (test 9's scans)

A repeat whose circuits were executed in more than one span, by the span record (`span-check/spans-t9.json`, each span's positions; a repeat is 16 consecutive positions in the scan's circuit order as `t9/report-t9.md` section 1 gives it), is **a straddling repeat**. A straddling repeat is neither a within-span observation nor a boundary observation: it is excluded from both channels and written to the ledger with the reason `straddling`. The boundary trial at that span boundary is the pair (last whole repeat before, first whole repeat after); the within-span pairs are the consecutive whole repeats on one side. Test 10 has no straddling repeats (the fits file's `beside.1_straddling_repeats` is empty for every job); the runner confirms this from the execution record and says so.

### 2.4 The four channels

1. **Frequency, within a span (channel W).** A consecutive pair of line observations inside one span, neither straddling, not alternating, is a within-span trial. It is **an event at the 4 kHz floor** when the change of the one-line frequency is at least max(4.0, T_k) kHz (test 9: |ΔDelta_MHz| × 1000; test 10: the wrapped phase step × kHz_per_rad). **Censoring:** a pair whose T_k is above 4.0 kHz could not have resolved a 4 kHz change and is censored: it contributes no exposure and no count to the 4 kHz channel, and the censored qubit-seconds are reported per test beside the exposure. A second count, **at the record's own floor** (an event when the change is at least T_k, every uncensored and censored pair contributing exposure), is reported beside the 4 kHz count for every test; this second count is what the tests' own reports called a switch or a step, and must reproduce their switch counts (test 10: 0 within spans; test 9: the STEPPED and MOVING change points away from boundaries, less the alternating pairs).
2. **Frequency, at a span boundary (channel F).** A pair of line observations that are the last whole repeat of one span and the first whole repeat of the next (the straddling repeat, if any, between them excluded) is a boundary trial. The same 4 kHz floor with the same censoring, and the same second count at the record's own floor beside. Each trial is tagged with its boundary (first or second of the job), its gap in seconds from the span record, and its test.
3. **Weight, at a span boundary (channel B), for the shuffled jobs only** (tests 7 and 8, and test 9's job 1), and only for qubits whose job verdict was TWO FIXED FREQUENCIES or NOT SETTLED with b inside (0.05, 0.95): a change of the upper line's implied weight across a span boundary of at least **0.10**, read from the nearest three positions passing the lever on each side as the span check tabulated them (`span-compare-t9.json`, item 3; `t7/a26-span-figures.md` for 143). Run 1 found ten such trials (143: 2; test 8 job 1: 4; test 8 job 3: 2; test 9 job 1: 2); the runner recounts them from the records and reports the list. **Channel B is never pooled with channel F.** They are different observables on different qubits under different designs, and run 1's model failed its own check because version 1 pooled them (section 9).
4. **Stamp (channel S).** A usable qubit observed under two calibration stamps: pair 1, test 8's job 1 (stamp 04:31:04 UTC, October 17) against test 9's job 1 (14:06:47 UTC, October 17), 63 qubits, from `t9/beside-t9.json`; pair 2, test 9's jobs (14:06:47) against test 10's (16:22:59 UTC, October 17), the qubits common to both, with test 10's level converted to a frequency at the qubit's wait. An event is a change of the S fit's detuning of at least 4 kHz, or a change of verdict kind (one line, two lines, not settled, not usable). The two pairs are reported separately and pooled; both stamp crossings are on one calendar day and the report says so.

**Kind events** (a transition between a line observation and a non-line observation that persists for at least two consecutive repeats, in either direction: test 9's 134 at repeat 7 and 120 at repeat 14 in job 2 are the examples) are counted and listed beside, with the span position of each (within, at a boundary, or at a straddling repeat), and not fitted.

**The within-span stationarity of the shuffled jobs** is read as in version 1: the copies check split by span, computed for every usable qubit of test 8's jobs 1 and 3 and test 9's job 1 from the per-circuit z and the span record; a qubit-span whose same-span pairs give Σz² above the 99.9th percentile of χ² on their degrees of freedom carries a within-span disagreement of unknown size, counted in a lower-floor channel reported beside and not fitted. Run 1 found four of 441 (test 8 job 1: 97; job 3: 43; test 9 job 1: 38 and 47); the runner recounts.

**Exposures.** Channel W: the qubit-seconds between consecutive uncensored within-span line observations, from the span durations and the repeat counts (test 9: the span's duration divided by its whole repeats; test 10: the per-qubit `repeat_period_s`), summed per test, with the censored qubit-seconds and the alternation-excluded and straddling-excluded qubit-seconds each reported beside. Channels F and B: trials, counted. Channel S: crossings, counted. The 130 s gap between test 10's jobs 1 and 2 (one stamp) is a trial of its own class, counted in channel F's ledger with the tag `between jobs` and reported separately, not pooled.

## 3. The model

Each qubit is a system with discrete states. Transitions occur through four channels:

- **within a span:** a Poisson process with rate λ per qubit-second (channel W, at the 4 kHz floor);
- **at a boundary between spans, frequency:** a Bernoulli trial with probability p_F per qubit-boundary (channel F, at the 4 kHz floor);
- **at a boundary between spans, weight:** a Bernoulli trial with probability p_B per qubit-boundary (channel B, at the 0.10 floor, two-line qubits in shuffled jobs only);
- **at a calibration stamp:** a Bernoulli trial with probability p_S per qubit-stamp crossing (channel S).

The likelihood is the product over records of Poisson(n_W | λ × exposure_W) × Binomial(n_F | N_F, p_F) × Binomial(n_B | N_B, p_B) × Binomial(n_S | N_S, p_S). Priors are Jeffreys (Gamma(1/2, 0) on λ; Beta(1/2, 1/2) on each p). Report the posterior median and the 5th and 95th percentiles of each rate, pooled and in the classes below, and the posterior probability that λ is below 10⁻⁴ per qubit-second. Report the same four posteriors a second time at the record's-own-floor counts (every pair contributing), labelled as such, so that the two floors can be read side by side.

**Classes,** fitted separately where the counts allow and pooled where they do not: for W and F, the scan design (test 9's jobs 2 and 3) against the monitor (test 10); the first boundary of a job against the second; the gap length (under 1 s, 1 to 3 s, over 3 s; the 130 s between jobs separately); the stamp of the day (test 9's afternoon against test 10's). For B: the first boundary against the second; 143 against the kingston qubits. For S: pair 1 against pair 2.

## 4. The dependence tests

For each class split within a channel, a two-sided Fisher exact test on the trial counts (F, B, S) and a likelihood-ratio test on the within-span counts (W), with p-values reported and nothing called significant: the report says which splits the data can and cannot distinguish at these counts. Across channels, one test only: channel F against channel B, reported as the statement that they differ (which is why they are two channels), with the Fisher p. The one split with a reading already on the record, the second boundary against the first in test 10 (one qubit over five standard errors at the second in each of three jobs, none at the first), is tested at the five-standard-error level as well as at the 4 kHz floor, both reported.

## 5. The model's own check

Simulate the model at the fitted rates on each test's exposures and trials 1,000 times, **per channel**, and report how often the simulated counts fall inside the observed counts' range per test and channel; a test and channel whose observed count lies outside the simulated 5th to 95th percentiles is named as the one the model does not describe. Then the sensitivity, per channel: at λ's 95th percentile, how many qubit-seconds of monitor time give a 90% chance of one within-span event; at p_F's interval, how many qubit-boundaries give a 90% chance of three frequency events; at p_B's interval, how many two-line boundary crossings give a 90% chance of three weight events.

## 6. Readings, labelled

One paragraph each, no more: what the four rates say about the shape (whether the within-span rate is consistent with zero at both floors; whether the boundary is one number on frequency and another on weight, and how far apart; whether the stamp probability is of a different order from both); what the non-line observations and the alternating pairs are and are not (a state the one-line model cannot describe, and a fitting artefact, with no claim about what either is); and the limit the 4 kHz floor sets, with the count of boundary steps between 1 and 4 kHz in test 9 that the floor leaves out (from the record's-own-floor count less the 4 kHz count in channel F) stated as the number the model does not see.

## 7. The predictions, written last, for the author to hash before October 20

From the fitted rates and nothing else, each from the channel named:

1. **For a test 10 monitor job on ibm_fez's 143 at 5.6 µs** (three spans, two boundaries, about 93 s of monitor time; at 5.6 µs the floor is 0.3 rad × 28.4 kHz per radian, about 8.5 kHz, so the record's own floor applies and the 4 kHz channel is censored there, which the prediction says) and a second such job 130 s later: the probability of at least one boundary frequency event in the four boundaries, from **p_F** at the record's own floor; the probability of at least one within-span event in 186 s, from **λ** at the record's own floor; and, separately, the probability that the same qubit shows at least one weight event across the two boundaries of a repeat of test 7's shuffled design on the same day, from **p_B**. The three are three predictions, not one.
2. **For a repeat of test 9's scan and test 10's monitor back to back on kingston under one stamp, on test 10's set S:** the expected number of boundary frequency events in each at the 4 kHz floor, with intervals, from p_F by design class where the data distinguish the classes and pooled where they do not.
3. **The number of qubit-seconds of monitor time at which the model gives even odds of one within-span event,** from λ at the 4 kHz floor and at the record's own floor, both.
4. **For the next stamp crossing on kingston** (whichever two jobs on a common set are next run under different stamps): the expected fraction of qubits moving by 4 kHz or changing kind, from p_S.
5. **What would count against the model:** a within-span event rate above λ's 95th percentile in the next 10,000 uncensored qubit-seconds; a boundary frequency count outside p_F's predicted interval in either direction; a weight event count on two-line qubits outside p_B's interval; a dwell time distribution, if within-span events ever accumulate, that is not exponential.

Each prediction carries the interval it comes from. These are the model's bets, not the author's or Mantri's; the author's and Mantri's bets on the same runs are sealed separately.

## 8. Two runs, and the comparison

Run 1 was on the desk runner from the version 1 bundle. Run 2 is on the desk runner from this bundle, in a fresh session with no access to run 1's output. The comparison, made by Mantri afterwards, is row by row: on `events-model-01-v2.json` against run 1's ledger (a difference in an event count is a difference in reading the records and is settled by the records; the alternating pairs and the straddling repeats are where the two ledgers are expected to differ, by construction), and on `rates-model-01-v2.json` (a difference in a rate at equal counts is a difference in code and is settled by the likelihood as written here).

## 9. What changed from version 1, and why (Mantri's errors, recorded)

1. Version 1 said "the 4 kHz floor is above every record's own threshold". False: at 6 µs the test 10 floor is 7.96 kHz, and on weak fringes at 20 µs the five-standard-error term runs to 4.6 to 10.6 kHz. Run 1's 23 literal within events in test 10 were all below the records' own thresholds. Version 2 defines the per-record threshold (2.1), censors pairs that could not resolve 4 kHz (2.4), and reports the record's-own-floor count beside.
2. Version 1's non-line criterion (A above 1.0) did not exclude the fitter's two-solution alternation near zero detuning when the second solution's amplitude is below 1.0. Run 1's within events in test 9's scans (3 in job 2, 15 in job 3) were almost all such pairs (frequency jumping 4 to 7 kHz each time the amplitude jumped between two values). Version 2 adds the alternation exclusion (2.2), on the amplitude.
3. Version 1 gave no convention for repeats that straddle a span; run 1 found that repeats 7 and 13 of the scans do, and under its conservative reading no scan boundary trial existed. Version 2 states the convention (2.3).
4. Version 1 pooled the weight channel (two-line qubits, shuffled jobs, 7 of 10 in run 1) and the frequency channel (any qubit, monitor, 1 of 379) into one boundary probability; run 1's model failed its own check for that reason (Fisher p of order 10⁻¹² between the two). Version 2 has four channels, B and F never pooled (2.4, 3).
5. Version 1 called the first stamp crossing "two days"; the two stamps are 04:31 and 14:06 UTC on October 17. Version 2 says one day (2.4, channel S).
6. Version 1's fez prediction transferred the pooled boundary probability to a monitor on 143. Version 2 asks for three separate predictions from the three channels that apply (7.1).

No record changed. No rule changed. The model's form is the same with one more channel.
