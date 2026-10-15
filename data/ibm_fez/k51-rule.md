# Kickoff 51: the rule, fixed before the run

Written 13 October 2026, before the job was built or submitted. Author: Anish Patel. This file states the design, the analysis and the verdict rule for Kickoff 51. Its SHA-256 is posted publicly before the run, and the file is published unchanged after it.

## The question

On ibm_fez, a qubit waiting inside Manacitra's wait test (a reuse-shaped circuit) has neighbours that are measured, reset and reused, while in a plain Ramsey wait its neighbours sit idle. Kickoff 50 (13 October 2026) found that the neighbours' state changes the waiting qubit's phase strongly. Does the wait test therefore see a different effective frequency offset on the waiting qubit than an idle-neighbour Ramsey does?

## The method

Between the waiting qubit M's two H gates, every operation on M in the wait test is diagonal. A software phase Rz(φ) on M is therefore equivalent to a frequency offset of φ over the wait. The run adds known phases φ ∈ {−90°, 0°, +90°} to both instruments and compares how each responds.

## The run

- **Processor:** ibm_fez, one job.
- **Package:** Manacitra v0.5.0 (commit `a55354d`), unedited.
- **Waiting qubits:**
  - 144, chain 143-144-145;
  - 143, chain 144-143-142.
- **Per waiting qubit and per φ:**
  - **W-no(φ):** the wait test without refocusing, from `manacitra.wait`, with rz(φ) on M right after its first H.
  - **R0(φ):** plain Ramsey over the wait test's own wait T_M, neighbours idle, with rz(φ).
  - **R1(φ):** a Ramsey with the neighbours doing exactly what they do in W-no: the wait test with every CZ that touches M replaced by a delay of the same length. Plus rz(φ).
  - **R2(φ):** R0 with both neighbours put in |1⟩ before the wait.
- **Per waiting qubit, at φ = 0 only:**
  - **W-ref:** the wait test with XY4 refocusing.
  - **Z:** a zero-wait baseline.
- **Shots:** each circuit runs 2 copies of 5,000 shots, 56 circuits and 280,000 shots in all.
- **Settings:** dynamical decoupling, gate twirling and measurement twirling all off. Interleaving seed 5151.

## The analysis

- **Loss** = M's P(1) minus M's P(1) in Z.
- **F_no(φ) and F_ref** are squared Hellinger overlaps with the wait test's φ = 0 parity ideal.
- **The residual:** d(φ) = F_no(φ) − F_ref × (1 − loss_R0(φ)).
- **The swing:** A = [d(+90°) − d(−90°)] / 2, per waiting qubit.
- **Intervals:** 90% intervals from one joint bootstrap, seed 51.

## The verdict

| verdict | condition |
|---|---|
| **SUPPORTED** | A's interval lies entirely outside [−0.05, +0.05] on at least one of the two qubits |
| **NOT SUPPORTED** | A's interval lies entirely inside [−0.03, +0.03] on both |
| **NOT SETTLED** | otherwise |

## Reported beside the verdict, not used in it

- The swings A1 and A2, computed with R1 and R2 in place of R0.
- Fits of each Ramsey's loss against φ, labelled as fits.
- The φ = 0 residual on each qubit.
- The calibration stamp.

The rule is not changed after the data, whatever they show.
