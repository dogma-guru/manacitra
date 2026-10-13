# Kickoff 50: the rule, fixed before the run

Written 13 October 2026, before the job was built or submitted. Author: Anish Patel. This file states the design, the analysis and the verdict rule for Kickoff 50. Its SHA-256 is posted publicly before the run, and the file is published unchanged after it.

## The question

On 13 October 2026 (Kickoff 49), on ibm_fez, finding 14's rule did not hold for qubit 144: a plain Ramsey wait, with its neighbours idle, showed more loss than 144 suffered while waiting in a reuse-shaped circuit, where its neighbours 143 and 145 are measured, reset and reused. Does what the neighbours are doing during the wait change how much phase 144 loses?

## The run

- **Processor:** ibm_fez, one job.
- **The wait test:** built with `manacitra.wait`, unedited, from Manacitra v0.5.0 (commit `a55354d`), on two chains:
  - 143-144-145, where 144 waits (M = 144);
  - 144-143-142, where 143 waits (M = 143), as a control.

  Each chain runs without and with XY4 refocusing, 2 interleaved copies of 5,000 shots.
- **Seven Ramsey and echo circuits on each M,** each 2 copies of 5,000 shots. In each, M's wait equals T_M, the wait test's own (from the end of M's first H to the start of its last, as scheduled without refocusing).
  - **R0:** plain Ramsey (H, wait, H, measure), the neighbours idle in |0⟩.
  - **R1:** the wait test without refocusing, with every CZ that touches M replaced by a delay of the same duration. M then does only H, wait, H, measure, and the neighbours keep every other operation at its scheduled time.
  - **R2:** R0 with the two neighbours put in |1⟩ before the wait.
  - **R3:** R1 with every neighbour operation other than measure and reset replaced by a delay of the same duration: the neighbours stay in |0⟩ and are measured and reset at the same times.
  - **E0, E1:** R0 and R1, each with one refocusing π pulse on M at the middle of the wait.
  - **Z:** M's zero-wait baseline.
- **Settings and seeds:** dynamical decoupling, gate twirling and measurement twirling all off. Interleaving seed 5050; bootstrap seed 50.

## The analysis

- **Loss** = M's P(1) in a circuit minus M's P(1) in Z.
- **Δ_active** = loss(R0) − loss(R1), on 144, with a 90% joint-bootstrap interval.
- **The two residuals.** F_no and F_ref are the wait test's squared Hellinger overlaps with its exact ideal, without and with refocusing.
  - d0 = F_no − F_ref × (1 − loss(R0));
  - d1 = F_no − F_ref × (1 − loss(R1)).

## The verdict

**First, the gap must be present today.** It is **REPRODUCED** if 144's d0 interval lies entirely above +0.10. Otherwise the verdict carries "(Kickoff 49's gap not present today)".

**H50, on 144:**

| verdict | condition |
|---|---|
| **SUPPORTED** | Δ_active's interval lies entirely above +0.10 |
| **OPPOSITE** | entirely below −0.10 |
| **NOT SUPPORTED** | entirely inside [−0.05, +0.05] |
| **NOT SETTLED** | otherwise |

## Reported beside the verdict, not used in it

- The same Δ_active on 143.
- d1 on both qubits.
- loss(R0) − loss(R2), and loss(R0) − loss(R3).
- The echo losses.
- The calibration stamp.

The rule is not changed after the data, whatever they show.
