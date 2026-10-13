# Kickoff 49: the rule, fixed before the run

Written 13 October 2026, before the job was built or submitted. Author: Anish Patel. This file states the design, the analysis and the verdict rule for Kickoff 49. Its SHA-256 is posted publicly before the run, and the file is published unchanged after it.

## The question

Does the rule of Kickoff 48 (finding 14 of Manacitra, 11 October 2026) hold on a later day, unchanged? The rule: a qubit's Ramsey loss, measured at a reuse-shaped circuit's own wait length, predicts how the circuit fares when that qubit waits in it.

## The run

- **Processor:** ibm_fez, one job.
- **Circuits:** built with `manacitra.wait`, unedited, from Manacitra v0.5.0 (commit `a55354d`).
- **Part A, the wait test:**
  - five chains (L1-M-L3): 144-143-142, 143-144-145, 141-142-143, 132-131-138 and 125-124-123;
  - each chain without refocusing and with XY4 refocusing on M;
  - 3 interleaved copies of 5,000 shots per cell.
- **T_M:** the time from the end of M's first H to the start of its last, in the circuit without refocusing as scheduled on the live backend at build time. It is recorded before submission.
- **Part B, Ramsey and echo:**
  - groups {143, 131, 124} and {142, 144, 125};
  - waits 0, 1, 2, 3.4, 4 and 8 µs, each chain's T_M, and 16 µs;
  - each circuit twice, 2,000 shots each.
- **Settings:** dynamical decoupling, gate twirling and measurement twirling all off. Interleaving seed 4949.

## The analysis

- **F** is the squared Hellinger overlap of the measured distribution with the wait test's exact ideal output.
  - F_no is F without refocusing, and F_ref is F with refocusing.
- **ΔP_R(T_M)** is M's Ramsey loss at T_M: P(1) at T_M minus P(1) at no wait.
- **The prediction and residual,** for each chain:
  - F_pred = F_ref × (1 − ΔP_R(T_M));
  - d_M = F_no − F_pred.

  Each has a 90% interval from a joint bootstrap of both parts, seed 49.
- **The code:** computed with the same code as Kickoff 48's recompute in the Manacitra repository.

## The verdict

- **DISAGREE** if any chain's d_M interval lies entirely outside [−0.15, +0.15].
- **AGREE** if every chain's d_M interval lies entirely inside [−0.15, +0.15].
- **NOT SETTLED** otherwise.
- **Informative.** A chain is informative if its ΔP_R(T_M) interval lies entirely above 0.2. If no chain is informative, the verdict is written with "uninformative" after it.

## Reported beside the verdict, not used in it

- Each Part B qubit's kind of loss at 3.4 µs, by `wait_loss_kind` with its default thresholds.
- Whether 143's offset is still present, with a fit labelled as a fit.
- The oscillation sign on 143.
- Each chain's d_M beside Kickoff 48's.
- The calibration stamp at build and at run.

The rule is not changed after the data, whatever they show.
