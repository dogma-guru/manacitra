# Kickoff 57: the rule, fixed before the run

Written 14 October 2026, before either job was built or submitted. Author: Anish Patel. This file states the design, the analysis and the verdict rule for Kickoff 57. Its SHA-256 is posted publicly before the run, and the file is published unchanged after it.

## The question

The check predicts how Manacitra's wait test fares from a Ramsey in which the waiting qubit's neighbours do exactly what they do in the circuit (the active-neighbour Ramsey): F_pred = F_ref × (1 − loss). On 14 October 2026 (Kickoff 55), on ibm_kingston, the check missed on one of four cells at an added phase of +90°. A six-phase sweep (Kickoff 56) then measured the wait test's offset against the Ramsey's on those chains as about 37°, about 12° and 0°.

When two shifted curves are compared, the difference is largest on their slopes and smallest at their peaks. At the Ramsey's own loss maximum, a shift between the two enters the check only at second order.

On four new ibm_kingston chains, does the check pass when it is run at the phase where the active-neighbour Ramsey's loss is largest?

## The code

Manacitra at commit `e45f15d8e2de1796d552bad401e696ce9ba0be3a`, installed unedited. The circuits come from the package:

- the wait test: `build_wait_test(chain, refocus, backend, phase)`;
- the active-neighbour Ramsey: `build_wait_ramsey(chain, backend, phase)`;
- the idle-neighbour Ramsey: `build_wait_ramsey(chain, backend, neighbours="idle", phase)`.

The zero-wait baseline is the one used since Kickoff 50. The choice of phase is made outside the package, by the procedure below.

## The chains

Chosen at build time by this procedure, fixed now:

1. **Candidates.** Every chain L1-M-L3 on ibm_kingston's live coupling map in which L1-M and M-L3 are both two-qubit gate edges and L1 ≠ L3.
2. **Exclusions.**
   - Any chain with a qubit used in Kickoff 55 or 56: 6, 7, 8, 11, 18, 31, 42, 43, 44, 139, 154 or 155.
   - Any chain with a qubit that is not operational.
   - Any chain with a qubit whose readout error exceeds 3%, or an edge whose two-qubit gate error exceeds 1%, in the backend's properties at build time. An edge's error is the larger of its listed directions.
3. **The draw.** Sort the remaining chains by (M, L1, L3), shuffle the list with NumPy's `default_rng(5757)`, and take chains in that order, skipping any that shares a qubit with one already taken, until four are taken.

The chains drawn and the properties used are recorded before the first submission. There is no redraw.

## The run: two jobs on ibm_kingston

Settings for both jobs: dynamical decoupling, gate twirling and measurement twirling all off.

### Job 1: the sweep

- **Per chain:** R1(φ), the active-neighbour Ramsey, at φ ∈ {0°, 60°, 120°, 180°, 240°, 300°}, as one RZ on M right after its first H.
- **Shots:** 24 circuits, each run as 2 copies of 2,000 shots. Interleaving seed 5701.

### The peak phase, from job 1

For each chain:

1. Take M's P(1) from its own bit, with the copies pooled.
2. Fit y(φ) = c + b·cos φ + s·sin φ by ordinary least squares over the six phases.
3. Set θ_R1 = atan2(s, −b).
4. **The peak phase:** φ* = 180° − θ_R1, wrapped to [0°, 360°) and rounded to the nearest whole degree.

φ* is computed from the point estimate only, and is recorded before job 2 is built.

### Job 2: the check

- **Per chain, for the verdict:**
  - W-no(φ*), the wait test without refocusing;
  - R1(φ*);
  - W-ref, the wait test with XY4 refocusing;
  - Z, the zero-wait baseline.

  16 circuits, each run as 2 copies of 3,000 shots.
- **Per chain, beside the verdict:**
  - R0(φ*), the idle-neighbour Ramsey;
  - W-no(+90°), R1(+90°) and R0(+90°).

  16 circuits, each run as 2 copies of 1,500 shots.
- **Interleaving seed:** 5702.

### When

- **The window.** Before building, read ibm_kingston's published calibration stamps for the previous 48 hours. Find each day's stamp that changed T1 on more than half the qubits, and each day's stamp that changed CZ errors on more than half the edges. Neither job is submitted inside the window from 30 minutes before the next expected T1 stamp to 30 minutes after the next expected CZ stamp. Each expected stamp is the last one plus the mean of the day-to-day intervals seen. If the 48 hours show no such pattern, record that, and no window applies.
- **Job 1** is not submitted later than 2 hours before the window opens.
- **Job 2** is submitted after job 1's peaks are recorded. If it cannot be submitted before the window opens, it waits until the window closes. The record says so, and the peaks are not recomputed.

## The analysis

As in Kickoffs 53 and 55, on the cells of job 2:

- **Loss** = M's P(1) minus M's P(1) in Z.
- **F_no(φ*) and F_ref** are squared Hellinger overlaps with the wait test's φ = 0 parity ideal.
- **The residual:** d1(φ*) = F_no(φ*) − F_ref × (1 − loss_R1(φ*)).
- **Cells:** a cell is one chain at φ*, four in all. A cell is informative if its loss_R1 interval lies entirely above 0.2.
- **Intervals:** 90% intervals from one joint bootstrap, seed 57, 10,000 draws. For each circuit, the copies are drawn with replacement and each drawn copy's shots are redrawn (Kickoff 52's method). φ* is held fixed.

## The verdict

**H57, the check at the peak phase:**

| verdict | condition |
|---|---|
| **DISAGREE** | any informative cell's d1 interval lies entirely outside [−0.15, +0.15] |
| **AGREE** | every informative cell's d1 interval lies entirely inside [−0.15, +0.15] |
| **NOT SETTLED** | otherwise |

If no cell is informative, the verdict is written with "uninformative" after it.

## Reported beside the verdict, not used in it

1. **The check at +90° on the same chains:** d1(+90°), whether each +90° cell is informative, and the verdict the same conditions would give on those cells.
2. **The original rule:** d0 with R0 in place of R1, at φ* and at +90°, and the verdicts it would give.
3. **Job 1's fits:** θ_R1 and the amplitude per chain, with their residuals and intervals.
4. **The drift between the jobs:** R1's loss at φ* in job 2, beside the loss job 1's fit gives at φ*.
5. **The calibration record:**
   - the stamp at build, at each submission, every 5 minutes until each job finishes, and after each fetch;
   - for each new stamp, which published values changed;
   - each job's status changes, with their times.

The rule is not changed after the data, whatever they show.
