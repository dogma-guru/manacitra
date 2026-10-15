# Kickoff 52: the rule, fixed before the run

Written 13 October 2026, before the job was built or submitted. Author: Anish Patel. This file states the design, the analysis and the verdict rule for Kickoff 52. Its SHA-256 is posted publicly before the run, and the file is published unchanged after it.

## The question

Kickoff 51 (13 October 2026) added known phases of −90°, 0° and +90° to a waiting qubit. On qubit 144, the wait test then answered as if its effective frequency offset differed from the one a plain Ramsey with idle neighbours sees. On qubit 143 the design was nearly blind: a ±90° probe is insensitive when the qubit's own offset is near ±90°, and 143's was near −100°.

This run sweeps the added phase all the way round, so that the sensitivity does not depend on where the qubit's own offset sits. It asks, on 143 and again on 144: does the wait test see a different effective offset from an idle-neighbour Ramsey?

## The method

Between the waiting qubit M's two H gates, every operation on M in the wait test is diagonal. A software phase Rz(φ) on M is therefore equivalent to a frequency offset of φ over the wait. Each instrument's response to φ is a sinusoid whose phase is that instrument's effective offset. Fitting the sinusoid over six evenly spaced φ measures the offset with the same sensitivity wherever it lies.

## The run

- **Processor:** ibm_fez, one job.
- **Package:** Manacitra v0.5.0 (commit `a55354d`), unedited.
- **Waiting qubits:**
  - 143, chain 144-143-142;
  - 144, chain 143-144-145.
- **The phases:** φ ∈ {0°, 60°, 120°, 180°, 240°, 300°}, applied as rz(φ) on M right after its first H.
- **Per waiting qubit and per φ:**
  - **W-no(φ):** the wait test without refocusing, from `manacitra.wait`, with rz(φ) inserted.
  - **R0(φ):** plain Ramsey over the wait test's own wait T_M, neighbours idle, with rz(φ).
  - **R1(φ):** the wait test with every CZ that touches M replaced by a delay of the same length, so the neighbours do exactly what they do in W-no. Plus rz(φ).
- **Per waiting qubit, at φ = 0 only:**
  - **W-ref:** the wait test with XY4 refocusing.
  - **Z:** a zero-wait baseline.
- **Shots:** 40 distinct circuits, each run as 2 copies of 4,000 shots: 320,000 shots in all.
- **Settings:** dynamical decoupling, gate twirling and measurement twirling all off. Interleaving seed 5252.

## The analysis

- **Loss** = M's P(1) minus M's P(1) in Z.
- **F_no(φ)** is the squared Hellinger overlap with the wait test's φ = 0 parity ideal.
- **The fit.** For each waiting qubit and each instrument, fit y(φ) = c + b·cos φ + s·sin φ by ordinary least squares over the six phases, with each phase's two copies pooled.
  - For R0 and R1, y is the loss and the fitted offset is θ = atan2(s, −b).
  - For W-no, y is F_no and the fitted offset is θ = atan2(−s, b).
- **The difference:** Δ = θ_W − θ_R0, wrapped to (−180°, +180°], per waiting qubit.
- **Intervals:** 90% intervals from one joint bootstrap over shots and copies, seed 52, refitting on every resample.

The verdict uses fitted phases. The fit is fixed here, before the data.

## The verdict

Given separately for each waiting qubit: **H52a** on 143 and **H52b** on 144.

| verdict | condition |
|---|---|
| **DIFFERENT** | Δ's interval lies entirely outside [−5°, +5°] |
| **SAME** | Δ's interval lies entirely inside [−5°, +5°] |
| **NOT SETTLED** | otherwise |

## Reported beside the verdict, not used in it

- θ_W − θ_R1 (the part not explained by the neighbours' activity) and θ_R1 − θ_R0 (the part the neighbours' activity explains), each with its interval.
- Whether R1 sits closer to the wait test than R0 does: |θ_W − θ_R1| against |θ_W − θ_R0|.
- Each fit's amplitude and residuals.
- The residuals d0(φ) = F_no(φ) − F_ref × (1 − loss_R0(φ)) and d1(φ) with R1, at every φ.
- The calibration stamp at build and at run.

The rule is not changed after the data, whatever they show.
