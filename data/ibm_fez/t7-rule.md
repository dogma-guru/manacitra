# Test 7: the rule, fixed before the run

Written 16 October 2026, before any job was built or submitted. Author: Anish Patel. This file states the design, the analysis and the verdict rule for test 7 on ibm_fez qubit 143. Its SHA-256 is posted publicly before the run, and the file is published unchanged after it.

## The question

Qubit 143 on ibm_fez has been the waiting qubit in Manacitra's wait test since Kickoff 47. Its Ramsey fringe has been measured at a handful of waits on four days, and the fitted frequency moved between days by more than its intervals allowed. Two readings of the archived points fit them equally well with eight points: one line with ordinary decay, or two fixed frequencies present at once, as a charge-parity split would give. Eight points cannot tell them apart. This test measures the fringe at 64 waits in two quadratures, so that they can be.

Is 143's Ramsey fringe, over a 63 µs span on one day, one line with ordinary decay (or a split too small for the span to resolve), or two fixed frequencies present at once?

The design and the rule below were checked on the desk before this file was written: on a grid of 135 simulated qubits spanning the archive's offsets, decays from 15 to 150 µs, splits from 0 to 50 kHz and two weights, the rule returned the generating verdict in at least 80% of 200 noisy draws at 106 of 117 counted points (88 were needed). The eleven that failed are splits of 8 to 11 kHz on a 15 µs decay, where the beat does not develop before the fringe is gone, and 3 kHz splits on a 150 µs decay, which the span resolves but the threshold calls unresolved. The record of that check is published with this test.

## The code

Manacitra at the v0.7.0 release, commit `b782d00238b7df40e1fbfd4da674968cf653c8d7` (the tag `v0.7.0`), installed unedited. The circuits come from the package's Part B Ramsey on one qubit, `part_b_circuit(1, wait_dt, "R")` (H, a delay of wait_dt, H, measure), placed on qubit 143 by `to_backend(qc, [143], backend)` with the neighbours idle in |0⟩, as `build_wait_ramsey(..., neighbours="idle")` does at the circuit's own wait:

- **X(t):** `part_b_circuit(1, wait_dt, "R")` at the wait t.
- **Y(t):** the same circuit with an S† (`SdgGate`) inserted on the qubit right before the final H, the way `build_wait_ramsey` inserts its phase gate after the first H; so the Y fringe is the X fringe advanced by a quarter turn.

Each wait t in µs is converted to dt with the backend's `dt` and made even with `even_wait` to the target's granularity; the wait actually scheduled for each circuit is recorded at build and used as t in the analysis. No gate is applied to any other qubit. Nothing in the package is edited.

## The run: one job on ibm_fez

Settings: dynamical decoupling, gate twirling and measurement twirling all off; no readout error mitigation.

- **Waits:** t = 0, 1, 2, ..., 63 µs, 64 waits.
- **Circuits:** X(t) and Y(t) at every wait, 128 circuits; plus two readout circuits on 143 alone, measure with no gate (P(1|0)) and X then measure (P(0|1)), 130 circuits in all.
- **Shots:** every circuit run as 2 copies of 1,500 shots. If the backend's estimate of the job's machine time at build exceeds the account's allowance for one job, every circuit runs as 2 copies of 1,000 shots instead; the choice and the estimate are recorded before submission, and no other change is made. Interleaving seed 7301.
- **One job, submitted once.** If it fails or is cancelled by the provider, the record says so and the test reports no verdict; it is not resubmitted under this rule.

### When

- **The window.** Before building, read ibm_fez's published calibration stamps for the previous 48 hours. Find each day's stamp that changed T1 on more than half the qubits, and each day's stamp that changed CZ errors on more than half the edges. The job is not submitted inside the window from 30 minutes before the next expected T1 stamp to 30 minutes after the next expected CZ stamp. Each expected stamp is the last one plus the mean of the day-to-day intervals seen. If the 48 hours show no such pattern, or the day-to-day interval lies outside 20 to 30 hours, record that, and the computed window does not apply.
- **In every case,** no job is submitted while the current day's cycle is in progress: from a stamp at which T1 changed on more than half the qubits until 30 minutes after the next stamp at which CZ errors changed on more than half the edges.

## The analysis

P(1) for 143 at each wait in each quadrature, copies pooled, with its binomial standard error. The zero-wait circuits are the first wait of each quadrature and are fitted with the rest.

### The two models

- **S, one line:** X(t) = c + A e^{−t/τ} cos(2πΔt + φ0); Y(t) = c + A e^{−t/τ} sin(2πΔt + φ0). Five parameters shared across the quadratures. Bounds: c, A in [0, 1]; τ in [0.5, 10⁴] µs; Δ in [−0.3, 0.3] MHz; φ0 in [0, 2π].
- **P, two fixed frequencies with a free weight:** X(t) = c + A e^{−t/τ'} [b cos(2π(Δ0 + δ)t + φ0) + (1 − b) cos(2π(Δ0 − δ)t + φ0)]; Y(t) the same with sin. Seven parameters. Bounds: c, A, τ', φ0 as S's; Δ0 in [−0.125, 0.125] MHz; δ in [0, 0.125] MHz; b in [0, 1]. The band on Δ0 and δ is the band the fitted waits can tell apart: at 2 µs spacing a line at f and at f ± 500 kHz are the same function on the fitted points.

### The fit and the held-out error

Both models are fitted jointly over the two quadratures by weighted least squares, each point weighted by its binomial standard error, on the even waits (0, 2, ..., 62 µs; 32 waits per quadrature). Each model's prediction is then evaluated on the odd waits (1, 3, ..., 63 µs), and its **held-out error** is the mean absolute difference between prediction and measurement over those 64 points.

**Starts:** 40 per model; the best χ² is kept; starts that fail to converge are counted and reported.

- **S:** 40 random starts, uniform within the bounds, from NumPy's `default_rng(7302)`.
- **P:** 20 grid starts and 20 random starts. The grid starts take c, A, τ' and φ0 from the S fit and (Δ0, δ, b) from Δ0 in {Δ_S, Δ_S + δ_s, Δ_S − δ_s}, δ_s in {5, 15, 50} kHz, b in {0.5, 0.3} (eighteen), plus (Δ_S, 8 kHz, 0.5) and (Δ_S, 30 kHz, 0.5). The random starts are uniform within the bounds from `default_rng(7303)`.

### The intervals

One bootstrap, 2,000 draws, seed 7304: for each circuit, the two copies are drawn with replacement, and each drawn copy's shots are redrawn from its own P(1); both quadratures are drawn in the same way, independently, in the same draw. P is refitted on each draw, started from the point fit. The 90% intervals of δ and of b are the 5th and 95th percentiles over the draws.

## The verdict

**H7, one line or two:**

| verdict | condition |
|---|---|
| **NO RESOLVED SPLIT** | S's held-out error is within 0.01 of P's or smaller, and either δ's 90% lower bound is below 5 kHz or b's 90% interval reaches an edge (lower bound at or below 0.05, or upper bound at or above 0.95) |
| **TWO FIXED FREQUENCIES** | P's held-out error is smaller than S's by more than 0.01, δ's 90% lower bound is above 5 kHz, and b's 90% interval lies inside (0.05, 0.95) |
| **NOT SETTLED** | otherwise |

NO RESOLVED SPLIT covers one line with ordinary decay, a split too small for the span to resolve, and switching too fast to see; the design does not separate them. TWO FIXED FREQUENCIES carries δ's interval and b's interval with it. Both fits, both held-out errors and all intervals are reported whatever the verdict.

## Reported beside the verdict, not used in it

1. **The telegraph diagnostic.** A third model, T, in which the qubit switches between the two frequencies at a rate γ (the telegraph factor g(t) = e^{−γt}[cosh κt + (γ/κ) sinh κt], κ = √(γ² − (2πδ)²), multiplying the steady fringe), fitted jointly in both quadratures on the same fitted waits, with γ's point fit and 90% interval from the same bootstrap. γ is reported beside the published rates for charge-parity switching and two-level-system fluctuators on transmons, and no verdict reads it.
2. **The weight:** b's interval beside the equal-weight case and the published exception (one qubit in 127 at b = 0.368, Shirizly, Misguich and Landa 2024).
3. **The beat nodes.** Under TWO FIXED FREQUENCIES, the node times 1/(4δ), 3/(4δ) and 5/(4δ) from the fitted δ, beside the wait test's own wait on 143 (10.45 µs), and the measured P(1) at the nearest waits; under NO RESOLVED SPLIT, the largest split the span could have resolved and the decay the fit absorbed.
4. **A reading recorded before the data.** The archive's telegraph fit of Kickoff 48 put a split of 23.7 kHz on 143, which would put the first node at 10.5 µs, where the wait test waits; a two-line fit of the same eight points put 50 kHz instead; eight points determine neither. If the fringe shows revivals near 21 and 42 µs and nodes near 32 and 53 µs, the first reading survives; a monotone fall discredits it. This is a reading, and the verdict does not depend on it.
5. **The fitted Δ (or Δ0)** beside the archive's values on earlier days (47.1 ± 1.8 kHz on 11 October; 40.4 ± 3.2 kHz on 13 October), and the published T2 of 143 at the stamp in force beside the fitted τ, with no claim about the published figure.
6. **More than two lines.** The residual periodogram of the P fit over 2 kHz to 500 kHz, and the sideband check at the neighbours' shifts recorded in finding 21, with the note that neighbour sidebands sit on one side at a few per cent and a parity split is two-sided at near-equal weights.
7. **Readout:** P(1|0) and P(0|1) measured on 143 alone in the same job, beside the published readout error at the stamp in force.
8. **The scheduled waits** against the requested ones, and any difference.
9. **The calibration record:** the stamp at build, at submission, every 5 minutes until the job finishes, and after the fetch; for each new stamp, which published values changed; the job's status changes with their times.

The rule is not changed after the data, whatever they show.
