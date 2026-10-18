# Test 9: the rule, fixed before the run

Written 17 October 2026, before any job was built or submitted. Author: Anish Patel. This file states the design, the analysis and the verdict rule for test 9 on ibm_kingston. Its SHA-256 is posted publicly as an issue before any job is submitted, and the file is published unchanged after the run. The verdict rule of job 2 was checked on the desk, on simulated fringes, before this file was hashed, and is checked again by the runner's own independent simulation after the hash and before any job; the runner's check is published with the run, and if it fails a required rate this file is superseded under a new hash before any job is submitted.

## The question

Test 8 ran test 7's rule on 132 qubits of ibm_kingston under one calibration stamp. Two things came out of it that the rule had not asked. First, 43 returned TWO FIXED FREQUENCIES on two jobs eighteen minutes apart, with a split near 5.5 kHz and a weight that moved within each job; and 134 returned it on one job and not on the next, because within the first job its fringe sat on one line for forty seconds and then on another. Second, sixteen qubits, most of them NO RESOLVED SPLIT, carried the copies signature of finding 28: the two copies of each circuit, run seconds apart, disagree beyond shot noise while the readout copies agree. Test 7's design cannot tell a fringe of two lines present at once from a fringe of one line that moves between two values over the job, and it cannot see when within a job a line moved. Both are time questions, and test 7's circuits are shuffled in time on purpose.

Two questions, then, on the same set of qubits on a second day:

1. Under test 7's rule again, does 43 return TWO FIXED FREQUENCIES on a second day, and does 134?
2. With the same circuits run in a fixed order and a short scan repeated through the job, is each qubit's fringe frequency STEADY across the job, STEPPED between two values, or MOVING otherwise; and on the qubits that carry the copies signature, which?

## The code

Manacitra at the v0.7.0 release, commit `b782d00238b7df40e1fbfd4da674968cf653c8d7`, installed unedited, for the single-qubit circuit form (`part_b_circuit(1, wait_dt, "R")`, `even_wait`, `to_backend`) and the readout survey. The test 7 fit is `ramsey_xy_fit` of the public branch `findings/t7-two-frequencies` at commit `b7313bbb8839cafcd215434ff18dc329282f06ca`, or the same function at the v0.8.0 release if it exists by the run; the commit used is recorded. The many-qubit circuits, the per-repeat fit of job 2 and the verdict of job 2 are the run's own script, published with the data, checked on the desk as the last section says.

## The qubit set, fixed by procedure

1. **Job 0, the readout survey,** as test 8's: every qubit of ibm_kingston measured in |0⟩, and X on every qubit then measured; 2 circuits, each 2 copies of 2,000 shots, interleaving seed 9301. Measured readout error per qubit e = (P(1|0) + P(0|1)) / 2, copies pooled. The published readout error at the stamp in force is recorded beside e.
2. **Eligible qubits:** every operational qubit with measured e at or below 3%.
3. **The set, S.** On the live coupling map at build (an edge in either direction counts), take qubits in this order, each taken only if it is eligible and is not adjacent to any qubit already taken: first 43 and 134 (test 8's two candidates); then 125, 87, 67, 149, 31, 77, 155, 28, 96, 58, 65, 47, 126, 101 (the other fourteen records that carried the copies signature in test 8, in descending order of their Ramsey Σz²); then 7 and 18; then every remaining eligible qubit in ascending index. S is the result: an independent set, no two of its qubits adjacent, every qubit outside it idle in |0⟩ throughout jobs 1 and 2.
4. **The complement, S′,** for the conditional job 3: the same procedure over the eligible qubits not in S, with no seeds.

Both sets, the survey's values and the properties used are recorded before job 1 is submitted. There is no redraw.

## The run: job 1 and job 2 on S, job 3 on S′ as the allowance permits

Settings for every job: dynamical decoupling, gate twirling and measurement twirling all off; no readout error mitigation.

- **Job 1, on S, test 7's design.** For each wait t = 0, 1, ..., 63 µs, one X circuit and one Y circuit, each holding test 7's single-qubit sequence on every qubit of S at once (X: H, delay t, H, measure; Y: H, delay t, S†, H, measure), each qubit measured into its own classical bit, no instruction on any qubit outside S; plus two readout circuits on S (measure; X then measure). 130 circuits, each run as 2 copies of 1,500 shots, interleaving seed 9302. The waits are converted with the backend's `dt` and `even_wait`; the scheduled wait of every circuit is recorded.
- **Job 2, on S, the scan in time.** The same single-qubit sequence on every qubit of S at once, at eight waits t = 0, 3, 7, 10, 14, 17, 21, 24 µs, X and Y at each: 16 circuits, which form one repeat. The job is 2 readout circuits (measure; X then measure), then 18 repeats of the 16 circuits in the same order every time (wait ascending, X then Y at each wait), then the 2 readout circuits again: 292 circuits, each 1,000 shots, submitted in that order and not interleaved. The position of each circuit in the job's result is taken as its place in execution, as test 8's positions were.
- **Structural checks before submission, on the circuits as built and again on the backend's snapshot:** every instruction acts on a qubit of the job's set; no two qubits of the set share an edge of the map used; each qubit carries exactly test 7's gate sequence at the scheduled wait; the exact noiseless P(1) is 0 for X, 0.5 for Y, 0 and 1 for the readout circuits, on every qubit of the set. Any failure stops the run.
- **The estimate.** The pre-submission estimate of each job is the rate per shot of the most recent ibm_kingston job in the hand-back folder (test 8's job 1) times the job's shots, with the half-again allowance beside it and IBM's published formula beside that. Jobs 1 and 2 are submitted only if the sum of their estimates, with the half-again margin, is within the instance's remaining allowance as read before job 1; if it is not, the run stops and the record says so. Job 1 is submitted, polled and fetched before job 2 is built.
- **Job 3, on S′, conditional:** job 2's design on S′, submitted only if the allowance left after job 2 is fetched, measured against job 2's machine time as IBM recorded it (T2), is at least 1.5 × T2. If it is less, job 3 does not run and the record says so.
- **Each job is submitted once.** If a job fails or is cancelled by the provider, the record says so and that job's qubits report no verdict; nothing is resubmitted under this rule.

### When

Test 8's job 3 ran under the stamp of 04:31:04 UTC on 17 October 2026. Test 9's jobs are submitted after ibm_kingston's next calibration cycle: the published stamps for the previous 48 hours are read before building; no job is submitted inside the computed window or while the day's cycle is in progress; if the 48 hours show no pattern or the interval lies outside 20 to 30 hours, that is recorded and the window does not apply. The stamp at build is recorded and the report says whether it differs from test 8's; the verdict words below do not depend on it.

## The analysis of job 1, per qubit

Exactly test 8's: for each qubit of S, test 7's analysis on that qubit's bit (P(1) per wait per quadrature, copies pooled, binomial standard error floored at 1/n; S and P fitted jointly over X and Y on the even waits, held out on the odd, with test 7's bounds and band, start layouts from seeds 9304 and 9305; the bootstrap of 2,000 draws seeded SeedSequence([9306, qubit]), copies drawn with replacement per wait and per quadrature, shots redrawn, P refitted from its point fit; the 90% intervals of δ and b). Usable: measured e at or below 3% in job 0 and the larger fitted amplitude at least 0.2.

**The verdict of job 1, per qubit,** is test 7's table unchanged: NO RESOLVED SPLIT, TWO FIXED FREQUENCIES, NOT SETTLED, with the 0.01 margin on the held-out error, the 5 kHz floor on δ's lower bound and the edges 0.05 and 0.95 on b's interval. **For 43 and for 134,** and for no other qubit, a second word is added: CONFIRMED ON DAY 2 if job 1 returns TWO FIXED FREQUENCIES, NOT CONFIRMED ON DAY 2 otherwise, with test 8's readings beside (43: δ 5.45 and 5.83 kHz, b 0.565 and 0.481; 134: lines at 55 and 12 kHz in job 1, one line at 58 kHz in job 3). Differences are reported, not reconciled.

## The analysis of job 2, per qubit

For each qubit of S and each repeat k = 1, ..., 18: P(1) per wait per quadrature from that repeat's circuits alone, binomial standard error floored at 1/n; and one fit of test 7's one-line model S with its decay held fixed: P_X(t) = c + A e^(−t/τ) cos(2πΔt + φ), P_Y(t) = c + A e^(−t/τ) sin(2πΔt + φ) in the quadrature convention of `ramsey_xy_fit` (the sign of Δ follows that convention, so that job 2's Δ̄ and job 1's Δ0 are comparable), with c, A, Δ and φ free and τ held at job 1's fitted S decay for that qubit, clipped to 10 to 400 µs (for a qubit of job 3, which has no job 1 fit, τ is held at 60 µs; the value used is recorded for every qubit). The band for Δ is −125 to 125 kHz, test 7's. The point fit takes the best of a grid over Δ in steps of 0.5 kHz across the band, each step solved by linear least squares in c, A cos φ and A sin φ, then a local least-squares refinement from the best step; no random starts. **The per-repeat frequency Δ_k is this fit's Δ; its standard error s_k is the standard deviation of Δ over a bootstrap of 200 draws, shots redrawn from the repeat's observed proportions and the fit repeated from a 1 kHz grid within 10 kHz of the point fit, seeded SeedSequence([9307, qubit, k]) (9308 for job 3), multiplied by the square root of the fit's reduced χ² where that exceeds 1, and floored at 0.25 kHz.** The fit's χ² over the repeat's 16 points (12 degrees of freedom) is recorded for every repeat.

**Usable in job 2:** measured e at or below 3% in job 0 and the median over repeats of the fitted amplitude A at least 0.2. A qubit that is not usable is reported as NOT USABLE with its numbers and is not counted.

**The three models on the eighteen frequencies,** weighted by 1/s_k²:

- **C, one value:** Δ_k = Δ̄, the weighted mean; χ²_C on 17 degrees of freedom.
- **Two levels:** Δ_k takes one of two values, with at most two transitions in execution order and every run of one value at least 3 repeats long (the patterns AB and ABA); the levels are the weighted means over their repeats; χ²_2 over the best pattern, on 17 − n degrees of freedom where n is the number of transitions (1 or 2).
- **L, a straight line:** Δ_k = α + βk by weighted least squares; χ²_L on 16 degrees of freedom.

## The verdict of job 2, per qubit

| verdict | condition |
|---|---|
| **STEADY** | χ²_C is at or below the 99.9th percentile of χ² on 17 degrees of freedom (40.79) |
| **STEPPED** | not STEADY; the best two-level pattern has χ²_2 at or below the 99.9th percentile of χ² on its degrees of freedom (39.25 on 16; 37.70 on 15); its two levels differ by more than 1 kHz and by more than five times the standard error of their difference (the square root of the sum of the inverse summed weights of the two levels); and χ²_2 is below χ²_L |
| **MOVING** | otherwise |

A STEPPED qubit reports its two levels, the repeat or repeats at which it changed, and the place of each change as a fraction of the job's positions, with the job's recorded machine time beside it. Every usable qubit reports Δ̄, the eighteen Δ_k with their s_k, χ²_C, the best two-level pattern with its χ²_2, and the line's slope β with χ²_L, whatever its verdict.

**The flag ONE-LINE FIT POOR,** reported beside the verdict and not used in it: the median over repeats of the per-repeat fit χ² exceeds 36 (three times its 12 degrees of freedom). On the desk, a fringe of two lines present at once at a split the 24 µs scan resolves (finding 28's lines) returns STEADY with the flag; a fringe of two lines closer than the scan resolves (43's lines) returns STEADY without it. So the flag is what separates "one line, steady" from "two lines present at once, steady" where the scan can see them, and a STEADY without the flag does not say there is one line.

**The counts.** The number of usable qubits returning each verdict, by job and in total, with every STEPPED and MOVING qubit listed with its numbers. There is no chip-level verdict word.

## Reported beside the verdicts, not used in them

1. **The pair, per qubit of S:** job 1's verdict beside job 2's, and the table of counts over the pairs. Readings named after the data and not verdicts: TWO FIXED FREQUENCIES with STEPPED is 134's kind of record in test 8 (two lines at different times); TWO FIXED FREQUENCIES with STEADY and the flag is 143's kind (two lines at once); TWO FIXED FREQUENCIES with STEADY and no flag is a split below the scan's resolution; NO RESOLVED SPLIT with MOVING or STEPPED is one line moving.
2. **The copies check of job 1,** per qubit as test 8's: Σz² over the 128 Ramsey circuits against 128 and over the two readout circuits against 2, with the per-circuit z, and the upper line's implied weight in ten blocks in execution order with P held at its fit; finding 28's signature named where the Ramsey Σz² exceeds 512 with the readout copies agreeing. **The signature beside job 2's verdict** for every qubit of S: the count of signature qubits returning each job 2 verdict.
3. **Test 8 beside test 9,** per qubit of S that was in test 8's sets: both days' job 1 verdicts, δ, b, Δ0, τ′ and Σz²; the count of qubits whose verdict changed between days, by direction.
4. **The telegraph diagnostic** of test 8, T bounded to P's band, on every TWO FIXED FREQUENCIES qubit of job 1.
5. **Readout:** each measured qubit's e from job 0, from job 1's readout circuits, and from job 2's readout circuits at the start and at the end of the job, beside the published value at the stamp in force.
6. **The sets:** S, S′, the eligible qubits left out of every set and why, the map used.
7. **The scheduled waits** against the requested, per job; the order of circuits in each job's result against the order submitted.
8. **The calibration record:** the stamp at build, at each submission, every 5 minutes until each job finishes, and after each fetch; for each new stamp, which published values changed; each job's status changes with their times; and whether the stamp at build differs from test 8's.

The rule is not changed after the data, whatever they show.

## The desk check of job 2's verdict rule

Job 2's analysis and verdict are run on simulated repeats with binomial shot noise at 1,000 shots, on fringes of amplitude 0.45 about 0.5 with a 60 µs decay unless stated, and the rates recorded: one line steady at 20 kHz, and the same at amplitude 0.3 with a 25 µs decay, and the same with a Gaussian envelope of 25 µs; one line stepping from 55 to 12 kHz at the ninth repeat, from 20 to 25 at the eleventh, and from 20 to 22 at the eleventh; one line drifting from 20 to 35 kHz across the job, and from 20 to 22; one line alternating between 20 and 35 kHz every two repeats; two lines at once at finding 28's values with the weight fixed and with it moving from 0.45 to 0.27; two lines at once at 43's values. The required rates: the steady cases return STEADY and the step cases at 5 kHz and above return STEPPED at 95% or more; the 2 kHz step returns STEPPED at 80% or more; the 15 kHz drift and the alternation return MOVING at 90% or more. The 2 kHz drift and the two-line cases are recorded without a requirement.

Before the hash, Mantri's own simulation of the rule ran the two steady cases 100 times each at the thresholds above (STEADY 100 of 100 on both), and all cases in a smaller number of trials. An earlier pass of the same simulation at the 99th percentile had failed the noisier steady case one time in twenty and the 55 to 12 kHz step one time in twenty, both because the per-repeat standard error ran about a fifth small on weak fringes; the percentile moved to 99.9, the standard error is scaled by the fit's reduced χ², and the gap clause was added, and that is the reason the thresholds are what they are. After the hash and before any job, the runner's independent simulation runs every case 100 times and its report is published with the run; a required rate not met supersedes this file under a new hash before any job is submitted. Both simulations use exponential decay and binomial noise only, which is a limit of the rule.
