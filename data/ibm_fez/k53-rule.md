# Kickoff 53: the rule, fixed before the run

Written 13 October 2026, before the job was built or submitted. Author: Anish Patel. This file states the design, the analysis and the verdict rule for Kickoff 53. Its SHA-256 is posted publicly before the run, and the file is published unchanged after it.

## The question

Finding 14's rule predicts how a reuse-shaped circuit (Manacitra's wait test) fares from the waiting qubit's Ramsey loss, measured with its neighbours idle. On 13 October 2026 the rule failed once on ibm_fez (Kickoff 49). Kickoffs 50 and 51 found that the waiting qubit's phase depends on what its neighbours are doing, and on qubit 144 a Ramsey with the neighbours active tracked the wait test far better than one with them idle.

This run tests the revised rule on chains the wait test has never run on: **predict the wait test from a Ramsey in which the neighbours do exactly what they do in the circuit.**

## The chains

Chosen at build time by this procedure, fixed now:

1. **Candidates.** Every chain L1-M-L3 on ibm_fez's live coupling map in which L1-M and M-L3 are both two-qubit gate edges and L1 ≠ L3.
2. **Exclusions.**
   - Any chain containing a qubit used by the wait test in Kickoffs 48 to 52: 123, 124, 125, 131, 132, 138, 141, 142, 143, 144 and 145.
   - Any chain with a qubit that is not operational.
   - Any chain with a qubit whose readout error exceeds 3%, or an edge whose two-qubit gate error exceeds 1%, in the backend's properties at build time.
3. **The draw.** Sort the remaining chains by (M, L1, L3), shuffle the list with NumPy's `default_rng(5353)`, and take chains in that order, skipping any that shares a qubit with one already taken, until four are taken.

The chains drawn and the properties used are recorded before submission.

## The run

- **Processor:** ibm_fez, one job.
- **Package:** Manacitra v0.5.0 (commit `a55354d`), unedited.
- **The phases:** φ ∈ {0°, +90°}, applied as rz(φ) on M right after its first H. φ = 0 is the chain as it is; +90° stands in for a known frequency offset over the wait.
- **Per chain and per φ:**
  - **W-no(φ):** the wait test without refocusing, from `manacitra.wait`, with rz(φ) inserted.
  - **R0(φ):** plain Ramsey over the wait test's own wait T_M, neighbours idle, with rz(φ).
  - **R1(φ):** the wait test with every CZ that touches M replaced by a delay of the same length, so the neighbours do exactly what they do in W-no. Plus rz(φ).
- **Per chain, at φ = 0 only:**
  - **W-ref:** the wait test with XY4 refocusing.
  - **Z:** a zero-wait baseline.
- **Shots:** 32 distinct circuits, each run as 2 copies of 3,500 shots: 224,000 shots in all.
- **Settings:** dynamical decoupling, gate twirling and measurement twirling all off. Interleaving seed 5353.

## The analysis

- **Loss** = M's P(1) minus M's P(1) in Z.
- **F_no(φ) and F_ref** are squared Hellinger overlaps with the wait test's φ = 0 parity ideal.
- **The revised prediction and its residual,** per chain and φ:
  - F_pred1(φ) = F_ref × (1 − loss_R1(φ));
  - d1(φ) = F_no(φ) − F_pred1(φ).
- **A cell** is one chain at one φ: eight cells in all.
- **Informative:** a cell is informative if its loss_R1 interval lies entirely above 0.2.
- **Intervals:** 90% intervals from one joint bootstrap over shots and copies, seed 53.

## The verdict

**H53, the revised rule:**

| verdict | condition |
|---|---|
| **DISAGREE** | any informative cell's d1 interval lies entirely outside [−0.15, +0.15] |
| **AGREE** | every informative cell's d1 interval lies entirely inside [−0.15, +0.15] |
| **NOT SETTLED** | otherwise |

If no cell is informative, the verdict is written with "uninformative" after it.

## Reported beside the verdict, not used in it

- The original rule on the same cells: d0(φ) = F_no(φ) − F_ref × (1 − loss_R0(φ)), and the verdict it would give under the same conditions.
- The mean |d1| against the mean |d0| over the informative cells, and per cell whether |d1| < |d0|.
- loss_R0 and loss_R1 per cell.
- Which φ = 0 cells are informative on their own.
- The calibration stamp at build and at run.

The rule is not changed after the data, whatever they show.
