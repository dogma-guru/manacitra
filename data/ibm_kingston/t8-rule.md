# Test 8: the rule, fixed before the run

Written 16 October 2026, before any job was built or submitted. Author: Anish Patel. This file states the design, the analysis and the verdict rule for test 8 on ibm_kingston. Its SHA-256 is posted publicly before the run, and the file is published unchanged after it.

## The question

Test 7 (finding 28) found that one qubit on ibm_fez, 143, has a Ramsey fringe of two fixed frequencies about 90 kHz apart at unequal weight, with the weight moving within a three-minute job. One qubit says nothing about any other. Two theories fit it and a single qubit cannot choose between them: that every transmon has the two-frequency structure and differs only in the size of the split, most too small for a 63 µs span to resolve; or that 143 has something of its own. Many qubits measured under the same rule can choose.

On ibm_kingston, on one day, under test 7's rule applied to each qubit, how many qubits of a fixed set return TWO FIXED FREQUENCIES, which ones, at what splits and weights, and does the weight move within the job on them as it did on 143?

The per-qubit rule is test 7's, whose design was checked on the desk before test 7's run (106 of 117 counted grid points at 80%; the record is published with finding 28). What is new here is that many qubits run in one job; the checks for that are fixed below.

## The code

Manacitra at the v0.7.0 release, commit `b782d00238b7df40e1fbfd4da674968cf653c8d7`, installed unedited, for the single-qubit circuit form (`part_b_circuit(1, wait_dt, "R")`, `even_wait`, `to_backend`) and the readout survey. The fit is `ramsey_xy_fit` of the public branch `findings/t7-two-frequencies` at commit `b7313bbb8839cafcd215434ff18dc329282f06ca` (the code finding 28's recompute used, which reproduces test 7's archived fits exactly), or the same function at the v0.8.0 release if it exists by the run; the commit used is recorded. The many-qubit circuits are built by the run's own script, published with the data, under the structural checks below.

## The qubit set, fixed by procedure

1. **Job 0, the readout survey,** as Kickoff 62's: every qubit of ibm_kingston measured in |0⟩, and X on every qubit then measured; 2 circuits, each 2 copies of 2,000 shots, interleaving seed 8301. Measured readout error per qubit e = (P(1|0) + P(0|1)) / 2, copies pooled. The published readout error at the stamp in force is recorded beside e.
2. **Eligible qubits:** every operational qubit with measured e at or below 3%.
3. **The set, S1.** On the live coupling map at build (an edge in either direction counts), take qubits in this order, each taken only if it is eligible and is not adjacent to any qubit already taken: first 7, then 43, then 18 (kingston's qubits of findings 20, 22 and 24); then every remaining eligible qubit in ascending index. S1 is the result: an independent set, no two of its qubits adjacent, every qubit outside it idle in |0⟩ throughout job 1.
4. **The complement, S2,** for the conditional job 2: the same procedure over the eligible qubits not in S1, with no seeds.

Both sets, the survey's values and the properties used are recorded before job 1 is submitted. There is no redraw.

## The run: job 1 on ibm_kingston, job 2 and job 3 as the allowance permits

Settings for every job: dynamical decoupling, gate twirling and measurement twirling all off; no readout error mitigation.

- **Job 1, on S1.** For each wait t = 0, 1, ..., 63 µs, one X circuit and one Y circuit, each holding test 7's single-qubit sequence on every qubit of S1 at once (X: H, delay t, H, measure; Y: H, delay t, S†, H, measure), each qubit measured into its own classical bit, no instruction on any qubit outside S1; plus two readout circuits on S1 (measure; X then measure). 130 circuits, each run as 2 copies of 1,500 shots, interleaving seed 8302. The waits are converted with the backend's `dt` and `even_wait`; the scheduled wait of every circuit is recorded.
- **Structural checks before submission, on the circuits as built and again on the backend's snapshot:** every instruction acts on a qubit of S1; no two qubits of S1 share an edge of the map used; each qubit of S1 carries exactly test 7's gate sequence; the exact noiseless P(1) is 0 for X, 0.5 for Y, 0 and 1 for the readout circuits, on every qubit of S1. Any failure stops the run.
- **The estimate.** The pre-submission estimate is the rate per shot of the most recent ibm_kingston job in the hand-back folder (Kickoff 59) times the job's shots, with the half-again allowance beside it and IBM's published formula beside that. If it exceeds the instance's remaining allowance, every circuit runs as 2 copies of 1,000 shots instead; the choice and the figures are recorded before submission.
- **Job 2, on S2, conditional on the allowance left after job 1 is fetched,** measured against job 1's machine time as IBM recorded it (T1): if the remaining allowance is at least 1.5 × T1, job 2 is job 1's design on S2 at the same shots; if it is at least 1.0 × T1 but less than 1.5 × T1, job 2 runs on S2 at 2 copies of 1,000 shots per circuit (two thirds of job 1's shots, so that its own estimate carries the half-again margin); if it is less than 1.0 × T1, job 2 does not run and the record says so, and S2 is kept as the set a later run would take. Interleaving seed 8303, the same checks, the tier and the figures recorded before submission.
- **Job 3, the confirmation, conditional on the allowance left after job 2 is fetched (or after job 1, if job 2 did not run)** being at least 1.5 × T1. Its set, S3, is every TWO FIXED FREQUENCIES candidate of jobs 1 and 2 that is usable, taken in the order S1's candidates by ascending index then S2's, each taken only if not adjacent on the map to one already taken (candidates within one set are never adjacent; across the two sets they may be). If there is no candidate, job 3 does not run and the record says so. Job 3 is job 1's design on S3 at 2 copies of 1,500 shots, interleaving seed 8307, the same checks, the per-qubit analysis with the bootstrap seeded SeedSequence([8308, qubit]). **A candidate is CONFIRMED if it returns TWO FIXED FREQUENCIES in job 3; otherwise NOT CONFIRMED, with job 3's verdict and numbers beside job 1's or 2's.** Job 3's δ and b are reported beside the first job's, and the difference is reported, not reconciled.
- **Each job is submitted once.** If a job fails or is cancelled by the provider, the record says so and that job's qubits report no verdict; nothing is resubmitted under this rule.

### When

As test 7's rule: ibm_kingston's published stamps for the previous 48 hours are read before building; no job is submitted inside the computed window or while the day's cycle is in progress; if the 48 hours show no pattern or the interval lies outside 20 to 30 hours, that is recorded and the window does not apply.

## The analysis, per qubit

For each qubit of a job's set, exactly test 7's analysis on that qubit's bit: P(1) per wait per quadrature, copies pooled, with the binomial standard error floored at 1/n; S (one line) and P (two lines, free weight) fitted jointly over X and Y on the even waits with the held-out error on the odd waits, with test 7's bounds, the P band from the fit set's spacing, and test 7's start layouts from seeds 8304 (S's random starts) and 8305 (P's); the bootstrap of 2,000 draws seeded SeedSequence([8306, qubit]), copies drawn with replacement per wait and per quadrature, shots redrawn, P refitted from its point fit; the 90% intervals of δ and of b.

**Usable.** A qubit is usable if its measured e in job 0 is at or below 3% and the larger of S's and P's fitted amplitude A is at least 0.2. A qubit that is not usable is reported as NOT USABLE with its numbers and is not counted.

## The verdict, per qubit

Test 7's table, unchanged:

| verdict | condition |
|---|---|
| **NO RESOLVED SPLIT** | S's held-out error is within 0.01 of P's or smaller, and either δ's 90% lower bound is below 5 kHz or b's 90% interval reaches an edge (lower bound at or below 0.05, or upper bound at or above 0.95) |
| **TWO FIXED FREQUENCIES** | P's held-out error is smaller than S's by more than 0.01, δ's 90% lower bound is above 5 kHz, and b's 90% interval lies inside (0.05, 0.95) |
| **NOT SETTLED** | otherwise |

**The survey's count** is the number of usable qubits returning each verdict, by job and in total, with every TWO FIXED FREQUENCIES qubit listed with its δ, b and their intervals. There is no chip-level verdict word. **A TWO FIXED FREQUENCIES on job 1 or 2 is a candidate:** over a set of this size the rule's own error rate on marginal fringes can produce a few, and a candidate is confirmed only by job 3, or by a later job on that qubit under test 7's rule if job 3 does not run. The record says "candidate" wherever it names one, and "confirmed" only after job 3. **The survey's result** is the list of confirmed qubits with their two readings each, the list of candidates not confirmed, and the counts.

Both fits, both held-out errors and all intervals are reported for every qubit whatever the verdict.

## Reported beside the verdicts, not used in them

1. **The copies check, per qubit, fixed here before the data:** Σz² over the 128 Ramsey circuits against 128 degrees of freedom, and over the two readout circuits against 2, with the per-circuit z; and for every usable qubit the upper line's implied weight in execution order in ten blocks, as finding 28's reading did, with P held at its fit. Reported for every qubit, with no threshold; a Σz² far above its degrees of freedom on the Ramsey circuits with the readout copies agreeing is finding 28's signature and is named as such where it appears.
2. **The telegraph diagnostic,** T fitted jointly in both quadratures **with its lines bounded to the same band as P's** (finding 28's check after the data: unbounded, T aliases outside the band and reports a spurious switching rate), γ's point fit and interval from the same bootstrap, for every TWO FIXED FREQUENCIES candidate and every job 3 qubit.
3. **Qubits 7, 43 and 18** each get their own paragraph: their verdict and numbers beside their leftover of finding 22 (−36.7°, −11.7°, 0.0°) and 7's three +90° misses, with no claim that one explains the other; the sealed predictions may bet on them.
4. **The distribution:** δ and b over the TWO FIXED FREQUENCIES candidates; the largest split the span could have resolved on each NO RESOLVED SPLIT qubit; the fitted τ and Δ0 of every usable qubit beside its published T2 and no claim about the published figure.
5. **Readout:** each measured qubit's e from job 0 and from the in-job readout circuits, beside the published value at the stamp in force.
6. **The sets:** S1, S2, S3, the eligible qubits left out of every set and why, the map used.
7. **The scheduled waits** against the requested, per job; and for job 3, each confirmed qubit's weight in execution order beside its job 1 or 2 blocks.
8. **The calibration record:** the stamp at build, at each submission, every 5 minutes until each job finishes, and after each fetch; for each new stamp, which published values changed; each job's status changes with their times.

The rule is not changed after the data, whatever they show.
