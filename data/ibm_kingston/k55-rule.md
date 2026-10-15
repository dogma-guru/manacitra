# Kickoff 55: the rule, fixed before the run

Written 14 October 2026, before the job was built or submitted. Author: Anish Patel. This file states the design, the analysis and the verdict rule for Kickoff 55. Its SHA-256 is posted publicly before the run, and the file is published unchanged after it.

## The question

On 13 October 2026 (Kickoff 53), on ibm_fez, a revised check passed on four chains it had never seen. The revised check predicts how Manacitra's wait test fares from a Ramsey in which the waiting qubit's neighbours do exactly what they do in the circuit. Does it pass on a second processor, ibm_kingston, on chains drawn by the same fixed procedure?

## The code

Manacitra at commit `e45f15d8e2de1796d552bad401e696ce9ba0be3a`, installed unedited. The circuits come from the package:

- the wait test: `build_wait_test(chain, refocus, backend, phase)`;
- the active-neighbour Ramsey: `build_wait_ramsey(chain, backend)`, its default;
- the idle-neighbour Ramsey: `build_wait_ramsey(chain, backend, neighbours="idle")`.

The zero-wait baseline is the one used since Kickoff 50.

## The chains

Chosen at build time by this procedure, fixed now:

1. **Candidates.** Every chain L1-M-L3 on ibm_kingston's live coupling map in which L1-M and M-L3 are both two-qubit gate edges and L1 ≠ L3.
2. **Exclusions.**
   - Any chain with a qubit that is not operational.
   - Any chain with a qubit whose readout error exceeds 3%, or an edge whose two-qubit gate error exceeds 1%, in the backend's properties at build time. An edge's error is the larger of its listed directions.
3. **The draw.** Sort the remaining chains by (M, L1, L3), shuffle the list with NumPy's `default_rng(5555)`, and take chains in that order, skipping any that shares a qubit with one already taken, until four are taken.

The chains drawn and the properties used are recorded before submission. There is no redraw.

## The run

- **Processor:** ibm_kingston, one job.
- **The phases:** φ ∈ {0°, +90°}, as one RZ on M right after its first H.
- **Per chain and per φ:**
  - W-no(φ), the wait test without refocusing;
  - R1(φ), the active-neighbour Ramsey;
  - R0(φ), the idle-neighbour Ramsey.
- **Per chain, at φ = 0 only:** W-ref (the wait test with XY4 refocusing) and Z (the zero-wait baseline).
- **Shots:**
  - 32 circuits for the verdict, each run as 2 copies of 3,500 shots;
  - the circuits listed under "Reported beside the verdict", each 2 copies of 1,500 shots.
- **Settings:** dynamical decoupling, gate twirling and measurement twirling all off. Interleaving seed 5555.
- **When.** Before building, read ibm_kingston's published calibration stamps for the previous 48 hours. Find each day's stamp that changed T1 on more than half the qubits, and each day's stamp that changed CZ errors on more than half the edges. The job is not submitted inside the window from 30 minutes before the next expected T1 stamp to 30 minutes after the next expected CZ stamp. Each expected stamp is the last one plus the mean of the day-to-day intervals seen. If the 48 hours show no such pattern, record that, and no window applies.

## The analysis

As in Kickoff 53:

- **Loss** = M's P(1) minus M's P(1) in Z.
- **F_no(φ) and F_ref** are squared Hellinger overlaps with the wait test's φ = 0 parity ideal.
- **The residual:** d1(φ) = F_no(φ) − F_ref × (1 − loss_R1(φ)).
- **Cells:** a cell is one chain at one φ, eight in all. A cell is informative if its loss_R1 interval lies entirely above 0.2.
- **Intervals:** 90% intervals from one joint bootstrap over shots and copies, seed 55.

## The verdict

**H55, the revised rule on a second processor:**

| verdict | condition |
|---|---|
| **DISAGREE** | any informative cell's d1 interval lies entirely outside [−0.15, +0.15] |
| **AGREE** | every informative cell's d1 interval lies entirely inside [−0.15, +0.15] |
| **NOT SETTLED** | otherwise |

If no cell is informative, the verdict is written with "uninformative" after it.

## Reported beside the verdict, not used in it

1. **The original rule on the same cells:** d0(φ) with R0 in place of R1, and the verdict it would give under the same conditions.
2. **The lean:** each d1, the mean d1, and how many cells have d1 above zero.
3. **Readout of |1⟩ on each M:** an X followed by a measurement, giving P(0 | 1).
4. **The active-neighbour Ramsey at φ = 180° and 270° on every chain,** fitted with 0° and 90° as c + b·cos φ + s·sin φ.
5. **The calibration record:**
   - the stamp at build, at submission, every 5 minutes until the job finishes, and after the fetch;
   - for each new stamp, which published values changed;
   - the job's status changes, with their times.

The rule is not changed after the data, whatever they show.
