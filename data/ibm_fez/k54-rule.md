# Kickoff 54: the rule, fixed before the run

Written 14 October 2026, before the job was built or submitted. Author: Anish Patel. This file states the design, the analysis and the verdict rule for Kickoff 54. Its SHA-256 is posted publicly before the run, and the file is published unchanged after it.

## The question

On 13 October 2026 (Kickoff 53), on ibm_fez, a revised check passed on four chains it had never seen. The revised check predicts how Manacitra's wait test fares from a Ramsey in which the waiting qubit's neighbours do exactly what they do in the circuit. Does it pass again on a second day, under a different daily calibration, built by the code that would be released?

## The code

Manacitra at commit `e45f15d8e2de1796d552bad401e696ce9ba0be3a`, installed unedited, the head of the pull request that makes the active-neighbour Ramsey the default. The circuits come from the package:

- the wait test: `build_wait_test(chain, refocus, backend, phase)`;
- the active-neighbour Ramsey: `build_wait_ramsey(chain, backend)`, its default;
- the idle-neighbour Ramsey: `build_wait_ramsey(chain, backend, neighbours="idle")`.

The zero-wait baseline is the one used since Kickoff 50.

## The chains

- Kickoff 53's four: 31-30-29, 75-74-73, 120-121-116 and 96-103-104.
- Two more: 143-144-145 and 144-143-142.

Each is written L1-M-L3, with M waiting. The chains are fixed here, not drawn.

## The run

- **Processor:** ibm_fez, one job.
- **The phases:** φ ∈ {0°, +90°}, as one RZ on M right after its first H.
- **Per chain and per φ:**
  - W-no(φ), the wait test without refocusing;
  - R1(φ), the active-neighbour Ramsey;
  - R0(φ), the idle-neighbour Ramsey.
- **Per chain, at φ = 0 only:** W-ref (the wait test with XY4 refocusing) and Z (the zero-wait baseline).
- **Shots:** 48 circuits for the verdict, each run as 2 copies of 3,500 shots.
- **Beside the verdict:** the circuits listed under "Reported beside the verdict", each 2 copies of 1,500 shots.
- **Settings:** dynamical decoupling, gate twirling and measurement twirling all off. Interleaving seed 5454.
- **When:** not before 21:00 UTC on 14 October 2026, and not between 03:00 and 09:00 UTC on any day.

## The analysis

As in Kickoff 53:

- **Loss** = M's P(1) minus M's P(1) in Z.
- **F_no(φ) and F_ref** are squared Hellinger overlaps with the wait test's φ = 0 parity ideal.
- **The residual:** d1(φ) = F_no(φ) − F_ref × (1 − loss_R1(φ)).
- **Cells:** a cell is one chain at one φ, twelve in all. A cell is informative if its loss_R1 interval lies entirely above 0.2.
- **Intervals:** 90% intervals from one joint bootstrap over shots and copies, seed 54.

## The verdict

**H54, the revised rule on a second day:**

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
4. **The refocusing pulses' own cost on each M:** H, the four XY4 pulses back to back with no wait, H, measure.
5. **The active-neighbour Ramsey at φ = 180° and 270° on every chain,** so that with 0° and 90° it can be fitted as c + b·cos φ + s·sin φ. That splits a steady offset (the phase) from random dephasing (the amplitude).
6. **One neighbour at a time, on 144 (chain 143-144-145) and 143 (chain 144-143-142),** at φ ∈ {0°, 90°, 180°, 270°}:
   - a Ramsey on M over T_M with both neighbours idle;
   - the same with only L1 put in |1⟩ before the wait;
   - with only L3 put in |1⟩;
   - with both put in |1⟩.

   Each is fitted as in item 5, and each shift is the fitted phase minus that of the both-idle Ramsey. Reported beside them:
   - the two views of the 143 to 144 pair (from 144 with only 143 in |1⟩, and from 143 with only 144 in |1⟩), and their difference;
   - on each qubit, the sum of the two single-neighbour shifts against the both-neighbour shift.
7. **The calibration record:**
   - IBM's calibration stamp at build, at submission, every 5 minutes until the job finishes, and after the fetch;
   - for each new stamp, which published values changed since the previous one;
   - the job's status changes, with their times.

The rule is not changed after the data, whatever they show.
