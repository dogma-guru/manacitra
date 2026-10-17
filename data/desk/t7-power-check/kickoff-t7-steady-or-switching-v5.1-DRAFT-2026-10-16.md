# Test 7, version 5.1: no resolved split, or two fixed frequencies, on qubit 143 (hardware; draft, with a desk power check)

Date: October 16, 2026. Author: Anish Patel. Prepared with Mantri (main). Version 5.1 under ruling R5 of the desk tests, replacing version 5 of the same day after round 5 stopped on two defects in version 5's model and bounds (the alias and the edge; `tests/handback/t7v5/report-t7v5.md`); version 5 is kept beside versions 1 to 4 as the record. Version 5 was drafted under R4 (the author's instruction of October 16 to start version 5 after round 4b and run its power check overnight), replacing version 4, abandoned by the author's ruling of the same day. **Draft.** The desk power check runs tonight; the hardware part runs only after the author's go, with a hashed rule and sealed predictions. Nothing goes to hardware under version 4.

## What changed from version 5, and why (ruling R5; round 5's stop)

Round 5 passed version 5's fit check (6 of 480 missed) and its timing (4.6 h projected) and stopped before the grid on two defects the timed draws showed, both Mantri's:

1. **The alias.** The fit uses the even microseconds, a 2 µs spacing, which fixes a line's frequency only modulo 500 kHz: a line at f and one at f ± 500 kHz predict the same values at every fitted point and opposite values at every held-out point. Version 5's bounds let P's lines reach ±600 kHz, so every P fit had an exact twin on the fit set, and in 32% of the timed draws the optimiser chose the twin that fails on the held-out set, sending the draw to NOT SETTLED for a reason that has nothing to do with the beat. Version 5.1 bounds P's lines inside the band the fit set can tell apart: Δ0 in [−125, 125] kHz and δ in [0, 125] kHz, so |Δ0| + δ never exceeds 250 kHz; the grid's widest line (75 + 50 kHz) and 143's recorded offsets (40 to 58 kHz) sit inside. S's bound stays, since S's twin lies outside its bound for every |Δ| the grid uses. Version 4 carried the same alias at a lower rate (12.3% of round 4b's draws); it is recorded there.
2. **The edge.** At b = 0 or 1 the P model is one line and δ is undetermined, so a steady fringe could be fitted as a lone line with any δ, and δ's bootstrap interval then sat narrowly around an arbitrary value: at the δ = 0 timed point, 131 of 200 draws did this and most returned NOT SETTLED. Version 5.1 reads the weight in the rule: a lone line is no resolved split, and a resolved split needs a resolved second line.
3. **The bootstrap over two quadratures** is fixed as the runner read it: copies drawn with replacement per wait and per quadrature, then the shots redrawn, and the joint refit. On hardware the X and Y circuits are separate circuits with separate copies, so their copies are independent and this is the right reading.
4. **A misattribution corrected.** Version 5 called the 23.7 kHz split of Kickoff 48 "L-03's fit"; it is the telegraph fit of rounds 2 to 4's beside tables, which L-03 reported. Round 5's P fit of the same eight points lands elsewhere (a split of 50 kHz with weights 0.27 and 0.73, with the amplitude at its bound), so the eight points do not determine the split under either model. The beat-node reading below is kept as a reading with its disconfirmer, now with that stated.

The grid, the keep criterion, the span, the shots, the Y quadrature and the two verdicts carry from version 5. The fit check and the timing run again, since both measured the changed procedure.

## What changed from version 4, and why (ruling R4; L-03; the Shirizly reading note)

Literature check L-03 (October 16) found the telegraph factor, the frequency hopping and the two-frequency parity fringe on the record, the last fitted on every qubit of an IBM cloud device by Shirizly, Misguich and Landa (2024), and found no published transmon mechanism switching at the rate version 4's SWITCHING verdict required (10,000 switches a second against published rates of 0.004 to 1,300). Version 5 makes four changes, each a reversal written as one and triggered by established findings, not by a result.

1. **SWITCHING is retired from the verdicts to a diagnostic.** The verdicts are NO RESOLVED SPLIT, TWO FIXED FREQUENCIES and NOT SETTLED. The telegraph fit is still made on hardware data and its switching rate γ is reported beside the verdict, with the published rates beside it; no verdict reads γ. Retiring the verdict does not delete the regime from the model; the diagnostic is where a surprise would show.
2. **The two-line model gets a free weight.** Shirizly et al. found one qubit in 127 whose two parities carried unequal weights (0.368 against 0.632). Version 4's symmetric model could not represent that fringe; version 5's P model (below) is their Eq. A4 with the weight b fitted.
3. **The Y quadrature is added.** Shirizly et al. measure the fringe along X and Y; the pair separates the detuning from the split by the fringe's phase and fixes the detuning's sign. The job doubles its circuits at the same waits; the shots per copy drop so the machine time stays near the allowance.
4. **The split threshold is examined by the power check rather than carried.** The rule keeps 5 kHz as the threshold to be hashed; the grid samples splits of 3, 5, 8 and 11 kHz, the published range on IBM Eagle qubits, and the report says at which splits the design resolves the beat, as a reading for a later version, never as a change made after the data.

The span, the shots per wait, the readout circuits in-job, the bootstrap, the keep criterion's 80% over three quarters, the checkpoint per point and the timing on a spread all carry from version 4.

## The question

Whether 143's Ramsey fringe is one line with ordinary decay (or a split too small for the span to resolve), or two fixed frequencies present at once over the job's span, as a charge-parity split would give. Which it is decides whether a peak phase fixed from a sweep stays valid, and whether the wait test's loss at the circuit's own wait is a decay or a beat node (the reading recorded before the data, below).

## The models, fixed now

Ramsey on 143 alone, neighbours idle, measured in two quadratures: X (H, wait, H, measure) and Y (H, wait, S†, H, measure; the phase gate before the final H, so that the Y fringe is the X fringe advanced by a quarter turn). Each quadrature's P(1) against the wait t:

- **S (steady):** X(t) = c + A e^{−t/τ} cos(2πΔt + φ0); Y(t) = c + A e^{−t/τ} sin(2πΔt + φ0). Five parameters, shared across the quadratures.
- **P (two fixed frequencies, free weight):** X(t) = c + A e^{−t/τ'} [b cos(2π(Δ0 + δ)t + φ0) + (1 − b) cos(2π(Δ0 − δ)t + φ0)]; Y the same with sin. Seven parameters: c, A, τ', Δ0, δ ≥ 0, φ0, b in [0, 1]. At b = 1/2 this is cos(2πδt) times the steady fringe, Shirizly's Eq. A5; δ ≥ 0 removes the b ↔ 1 − b degeneracy.
- **T (telegraph), diagnostic only on hardware data:** version 4's T model, in both quadratures (the Re and Im of the same complex fringe); its γ and δ are reported beside the verdict. Not simulated in the power check.

Both S and P are fitted jointly over the two quadratures by weighted least squares with each point's binomial standard error, on the even microseconds (0, 2, ..., 62 µs; 32 waits per quadrature), with the prediction on the odd microseconds (1, 3, ..., 63 µs). The held-out error is the mean absolute error over the 64 held-out points.

**Starts.** 40 per point fit for each model; the best is kept; starts that fail to converge are counted.

- **S:** 40 random starts, uniform within the bounds.
- **P:** 20 grid starts and 20 random starts uniform within the bounds. The grid starts take c, A, τ' and φ0 from the S fit, and (Δ0, δ, b) from: Δ0 in {Δ_S, Δ_S + δ_s, Δ_S − δ_s}, δ_s in {5, 15, 50} kHz, b in {0.5, 0.3}, eighteen starts; plus (Δ_S, 8 kHz, 0.5) and (Δ_S, 30 kHz, 0.5), twenty.
- **Bounds:** version 4's for c, A, τ (τ') and φ0; S's Δ as version 4's ([−0.3, 0.3] MHz); P's Δ0 in [−0.125, 0.125] MHz and δ in [0, 0.125] MHz, so that |Δ0| + δ stays at or below the 250 kHz the fit set can tell apart (ruling R5); b in [0, 1]. The report states them.

## The rule (to be fixed and hashed on the go)

Intervals: the archive's bootstrap (copies drawn with replacement per wait and per quadrature, then the shots redrawn, and P refitted jointly over both quadratures), 2,000 draws on hardware data, each refit started from the point fit; the 90% interval of δ and of b from the draws.

- **NO RESOLVED SPLIT:** S's mean absolute held-out error is within 0.01 of P's or smaller, and either the 90% lower bound of δ is below 5 kHz or b's 90% interval reaches an edge (its lower bound at or below 0.05, or its upper bound at or above 0.95: a lone line, or a second line whose weight is not resolved). (One line with ordinary decay, or a split too small for the span to resolve, or switching too fast to see; the design does not separate them.)
- **TWO FIXED FREQUENCIES:** P's held-out error is smaller than S's by more than 0.01, the 90% lower bound of δ is above 5 kHz, and b's 90% interval lies inside (0.05, 0.95): a second line of resolved weight. The verdict carries δ's interval and b's interval.
- **NOT SETTLED** otherwise.

Report both fits, both held-out errors and all intervals whatever the verdict.

## The desk power check (tonight, on one machine)

**The grid:** Δ0 in {40, 55, 75} kHz; τ in {15, 60, 150} µs; δ in {0, 3, 5, 8, 11, 15, 30, 50} kHz; b in {0.5, 0.37} where δ > 0 (0.37 is Shirizly's exception); the shape in the `ramsey_fit` form (c = 0.50, A = 0.48, φ0 = π in the models' form). Per (Δ0, τ): one point at δ = 0 and fourteen at δ > 0, fifteen; 135 points. For each, simulate the hardware design below with binomial shot noise in both quadratures, 200 draws, seeded as SeedSequence([7676, point, draw]), a new root so that the draws are version 5.1's own and not version 5's; apply the rule with the bootstrap replaced, for the power check only, by 200 refits per draw warm-started from that draw's point fit; record the fraction of draws returning each verdict, each draw's fits, intervals and convergence, and the point's CPU seconds.

**The generating verdict:** NO RESOLVED SPLIT for δ = 0 and δ = 3 kHz (a split below the threshold is, by the verdict's own definition, not resolved); TWO FIXED FREQUENCIES for δ of 8 kHz and above; δ = 5 kHz is the rule's boundary, reported with "either" and not counted.

**The keep criterion:** over the 117 counted points (δ ≠ 5 kHz), the design is kept if the rule returns the generating verdict in at least 80% of draws over at least three quarters of them (88). The report names every failing point, sorts the failures by kind, and gives, beside the verdict, the pass fraction by δ and by b: where the beat is resolved and where it is not, as a reading for the threshold of a later version, which is not changed here.

**Before the grid, in this order, each with a stop line:**

1. **The fit check:** every (Δ0, δ) pair of the grid (24) at τ = 60 µs and b = 0.5, ten draws each; each draw's S and P point fits under the 40-start procedure, against reference fits of 244 S starts and 800 P starts. A fit misses when its χ² is worse than the reference's by more than 1. Stop line: more than 5% of fits missed.
2. **The timing:** six grid points end to end, 200 draws each, including one at δ = 0, one at δ = 50 kHz, one at b = 0.37, one at τ = 150 µs and one at δ = 3 kHz; project the grid from the mean CPU seconds per draw across the six, times 27,000 draws, divided by the workers.
3. **The line: twelve hours of wall time** on this machine (overnight; the checkpoint per point makes a stop lossless). If the projection exceeds twelve hours, stop and report; if the run reaches twelve hours, stop it and report the points done.

**The run:** under `nohup`, counted points first, one JSON line per point as it finishes, resumable from the last line written.

**Beside the power check, as a reading:** fit S and P to each archived run alone (Kickoffs 47, 48, 49, 52; the archive has the X quadrature only, so the fit is one-quadrature) and report Δ0, δ and b with no verdict; beside rounds 2 to 4's telegraph fits and round 5's S and P fits of the same runs. The hand-back folder is `tests/handback/t7v51/`.

## The hardware design (after the power check)

Ramsey on 143 (the package's Part B "R" circuit at a given wait, and the same with the S† before the final H for the Y quadrature), 64 waits from 0 to 63 µs in steps of 1 µs, two quadratures, two copies, **1,500 shots each** (384,000 shots, one job), neighbours idle, the zero-wait baseline as the first wait of each quadrature; the two readout circuits on 143 in the same job (the R1 ruling on same-job matrices), 1,500 shots each, two copies. One job, one stamp recorded at build, submission, polls and fetch. The shots per copy drop from version 4's 2,000 so the job's machine time stays near the allowance with the circuits doubled; if the allowance will not take it, the fallback is 1,000 shots per copy, re-simulated before the hash.

## A reading recorded before the data, with its disconfirmer (from the Shirizly reading note)

The telegraph fit of Kickoff 48 in rounds 2 to 4's beside tables put 143's split at 23.7 kHz with no decay: the fringe's fall as a beat, not a decay. Round 5's two-line fit of the same eight points put it at 50 kHz with unequal weights instead, so eight points do not determine the split under either model, and the number below is one fit's. A beat of 23.7 kHz has its first node at 1/(4δ) = 10.5 µs; the reuse circuit's wait is 10.45 µs. If 143 is a parity-split qubit near 24 kHz, the wait test's loss is the beat's first node, which an echo restores and an echo-measured T2 does not show, as finding 13 described. The hardware data decide: a split near 24 kHz shows revivals near 21 and 42 µs and nodes near 32 and 53 µs; a decaying steady fringe shows no revival. The scorecard reads this beside the verdict and names which it saw. The author's sealed predictions may bet on it or against it.

## Beside the verdict (hardware data)

- **The telegraph diagnostic:** T fitted in both quadratures; γ's point fit and 90% interval, beside the published rates (parity on IBM Falcon 3 to 5 per second; Ristè et al. about 1,300; two-level systems 0.004 to 0.5). A γ above 10,000 per second with a resolved split is reported as a surprise and goes to the ticket as a question.
- **The weight:** b's interval, beside Shirizly's 0.368 exception and the equal-weight case.
- **The beat nodes:** under TWO FIXED FREQUENCIES, the node times 1/(4δ), 3/(4δ), 5/(4δ) beside T_M = 10.45 µs, and what a six-phase sweep at 10.444 µs would have read; under NO RESOLVED SPLIT, the largest split the span could have resolved (about 4 kHz) and the decay the fit absorbed.
- The fitted Δ (or Δ0) against 47.1 ± 1.8 kHz (11 October) and 40.4 ± 3.2 kHz (13 October); the day-to-day movement of P(1) at 8 µs on the record; the published T2 at the stamp beside the fitted τ, with no claim about IBM's figure.
- **The two fixed diagnostics for more than two frequencies,** as version 4 fixed them (the residual periodogram, 2 kHz to 500 kHz, resolution about 16 kHz; the sideband check at finding 21's shifts, with the symmetry note from L-03: neighbour sidebands sit on one side at a few per cent, a parity split is two-sided at near-equal weights).

## Boundaries

The standing ones. One qubit's noise; no ranking of machines; no claim about the cause of the published table's values; the vocabulary boundary if any of this is written for the public repository. The first verdict is never written as "steady." The retirement of SWITCHING is a dated event with its reason on the record (L-03, section 12; R4).
