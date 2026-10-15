# Kickoff 58: the rule, fixed before the run

Written 14 October 2026, before either job was built or submitted. Author: Anish Patel. This file states the design, the analysis and the verdict rule for Kickoff 58. Its SHA-256 is posted publicly before the run, and the file is published unchanged after it.

## The question

The check predicts how Manacitra's wait test fares from a Ramsey in which the waiting qubit's neighbours do exactly what they do in the circuit (the active-neighbour Ramsey): F_pred = F_ref × (1 − loss). On 14 October 2026, on ibm_kingston, Kickoff 56 measured the wait test's offset against that Ramsey's on three chains: about 37° on qubit 7 (chain 6-7-8), about 12° on qubit 43 (chain 42-43-44) and 0° on qubit 18 (chain 31-18-11). Kickoff 57 then ran the check at the Ramsey's loss maximum on four new chains and it passed, but so did the check at +90° on the same chains, so the two placements were not separated.

This run is a placement comparison, not a pass-rate test. The chains are the three whose offsets Kickoff 56 measured, chosen for that reason. On each, is the check's residual smaller at the Ramsey's loss maximum than at +90°?

## The code

Manacitra at commit `e45f15d8e2de1796d552bad401e696ce9ba0be3a`, installed unedited. The circuits come from the package:

- the wait test: `build_wait_test(chain, refocus, backend, phase)`;
- the active-neighbour Ramsey: `build_wait_ramsey(chain, backend, phase)`;
- the idle-neighbour Ramsey: `build_wait_ramsey(chain, backend, neighbours="idle", phase)`.

The zero-wait baseline is the one used since Kickoff 50. The choice of phase is made outside the package, by the procedure below.

## The chains

Fixed here, not drawn: 6-7-8 (M = 7), 42-43-44 (M = 43) and 31-18-11 (M = 18), each written L1-M-L3 with M waiting. They were used in Kickoffs 55 and 56 and are chosen because their offsets are measured. No result on them enters any pass rate of the check.

## The run: two jobs on ibm_kingston

Settings for both jobs: dynamical decoupling, gate twirling and measurement twirling all off.

### Job 1: the sweep

- **Per chain:** R1(φ), the active-neighbour Ramsey, at φ ∈ {0°, 60°, 120°, 180°, 240°, 300°}, as one RZ on M right after its first H.
- **Shots:** 18 circuits, each run as 2 copies of 2,000 shots. Interleaving seed 5801.

### The peak phase, from job 1

For each chain:

1. Take M's P(1) from its own bit, with the copies pooled.
2. Fit y(φ) = c + b·cos φ + s·sin φ by ordinary least squares over the six phases.
3. Set θ_R1 = atan2(s, −b).
4. **The peak phase:** φ* = 180° − θ_R1, wrapped to [0°, 360°) and rounded to the nearest whole degree.

φ* is computed from the point estimate only, and is recorded before job 2 is built.

### Job 2: the comparison

- **Per chain, for the verdict:**
  - W-no(φ*) and R1(φ*);
  - W-no(+90°) and R1(+90°);
  - W-ref, the wait test with XY4 refocusing;
  - Z, the zero-wait baseline.

  18 circuits, each run as 2 copies of 3,000 shots.
- **Per chain, beside the verdict:** R0(φ*) and R0(+90°), the idle-neighbour Ramsey. 6 circuits, each run as 2 copies of 1,500 shots.
- **Interleaving seed:** 5802.

### When

- **The window.** Before building, read ibm_kingston's published calibration stamps for the previous 48 hours. Find each day's stamp that changed T1 on more than half the qubits, and each day's stamp that changed CZ errors on more than half the edges. Neither job is submitted inside the window from 30 minutes before the next expected T1 stamp to 30 minutes after the next expected CZ stamp. Each expected stamp is the last one plus the mean of the day-to-day intervals seen. If the 48 hours show no such pattern, record that, and no window applies.
- **Job 1** is not submitted later than 2 hours before the window opens.
- **Job 2** is submitted after job 1's peaks are recorded. If it cannot be submitted before the window opens, it waits until the window closes. The record says so, and the peaks are not recomputed.

## The analysis

On job 2's counts:

- **Loss** = M's P(1) minus M's P(1) in Z.
- **F_no(φ) and F_ref** are squared Hellinger overlaps with the wait test's φ = 0 parity ideal.
- **The residual:** d1(φ) = F_no(φ) − F_ref × (1 − loss_R1(φ)), at φ* and at +90°.
- **The comparison:** D = |d1(+90°)| − |d1(φ*)|, per chain. D above zero means the residual is smaller at the peak.
- **Intervals:** 90% intervals from one joint bootstrap, seed 58, 10,000 draws. For each circuit, the copies are drawn with replacement and each drawn copy's shots are redrawn (Kickoff 52's method). φ* is held fixed.

## The verdict

Given separately for each chain: **H58a** on 7, **H58b** on 43 and **H58c** on 18.

| verdict | condition |
|---|---|
| **PEAK SMALLER** | D's interval lies entirely above +0.02 |
| **PLUS-90 SMALLER** | D's interval lies entirely below −0.02 |
| **NOT SEPARATED** | otherwise |

The band of ±0.02 is fixed so that a difference inside it, whichever its sign, is not called a separation.

## Reported beside the verdict, not used in it

1. **The margin test at each placement:** whether each cell is informative (loss_R1 interval entirely above 0.2), and whether its d1 interval lies entirely inside, entirely outside, or across [−0.15, +0.15].
2. **The original rule (R0):** d0 at φ* and at +90°, and D0 = |d0(+90°)| − |d0(φ*)|, with intervals.
3. **Job 1's fits:** θ_R1 and the amplitude per chain, with intervals, beside Kickoff 56's θ_R1 (+16.3°, −37.3°, −38.1°) and φ* beside the phase Kickoff 56's fit implies (164°, 217°, 218°).
4. **The drift between the jobs:** R1's loss at φ* in job 2, beside the loss job 1's fit gives at φ*.
5. **This run's +90° cells beside Kickoff 55's** (d1 +0.257, +0.160, +0.073 on 7, 43 and 18).
6. **The calibration record:**
   - the stamp at build, at each submission, every 5 minutes until each job finishes, and after each fetch;
   - for each new stamp, which published values changed;
   - each job's status changes, with their times.

The rule is not changed after the data, whatever they show.
