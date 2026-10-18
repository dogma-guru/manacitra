# Test 14: the in-phase control on fez 143 (rule, fixed before the run)

Status: draft for the author's review, 18 October 2026. Once approved, this file is hashed, the hash is posted in a public issue, and the file is published unchanged with the run. One job, submitted once, on the author's separate go.

## 1. The question

Tests 11 and 12 read the weight of 143's two lines from the fringe length at the antiphase wait, 1/(4δ) = 5.6 µs, through a fixed R0 = 0.4749 taken from test 11's job 1: |1 − 2w| = r/R0. Every level change they report is a change of r read through that constant. A change of the envelope, of the readout, or of the frame would also move r or the phase, and the monitor alone cannot tell them apart. Test 12's level change at the second boundary (−0.137 at 24.6 combined errors) is the case in point: it is a weight change if R0 held, and something else if R0 did not.

At the in-phase wait, 1/(2δ) = 11.2 µs, the two lines are in phase, so the fringe length is the envelope itself whatever the weight (w + (1 − w) = 1), and the phase is the frame's. A repeat that measures both waits reads R0 live beside the weight, and reads the frame beside both. This test adds that control and fixes in advance how each boundary's change is attributed: to the weight, to the envelope, to the frame, or mixed.

The in-phase wait is exact for the split as measured on day 2 (44.70 kHz); a drift of 1 kHz in the split gives a relative phase of 0.14 rad between the lines at 11.2 µs, which changes the control length by under 0.3 percent and is ignored.

Nothing here names a cause. The verdicts of tests 11 and 12 stand as their rules define them; this test reads the same quantities with one more wait beside them.

## 2. The job

- **Processor and qubit:** ibm_fez, qubit 143 alone; every other qubit idle in |0⟩.
- **Circuits:** two readout circuits (measure; X then measure), then **61 repeats** of four circuits in fixed order, X(5.6 µs), Y(5.6 µs), X(11.2 µs), Y(11.2 µs), then the two readout circuits again: **248 circuits**, each **500 shots**, submitted in that order. X is H, the wait, H, measure; Y adds one rz(−90°) before the last H. The waits are 1,400 dt and 2,800 dt.
- **Settings:** dynamical decoupling, gate twirling and measurement twirling off; no readout error mitigation; optimization level 0 on the published layout.
- **Spans:** whatever the execution record says. At the span pitch of about 100 positions seen on this processor, the job crosses two boundaries, near positions 100 and 200, with about 24, 24 and 11 whole repeats on the three spans. A repeat whose four positions fall in more than one span is a straddling repeat and belongs to no span.
- **Stamps and window, allowance, estimate and decision, structural checks, backend list:** as test 12's rule, with 124,000 shots in the estimate (test 11's job 2 rate per shot gives about 34 s; about 51 s with the half-again margin).
- **Submitted once.** A failed or cancelled job is recorded and never resubmitted.

## 3. Definitions

The midpoint c is the mean of the job's four readout circuits as test 12 defines it. For each repeat k and each wait, the vector (P1_X − c, P1_Y − c) gives a phase θ and a length r, with the binomial error σ and the phase error s = max(σ/r, 0.02), exactly as in test 12. Subscripts a (antiphase, 5.6 µs) and c (control, 11.2 µs).

- **R0 live:** R0_k = r_c,k · e^{(11.2 − 5.6)/τ′}, with τ′ = 128.3 µs fixed from test 11's job 1. The factor is 1.045; a 20 percent error in τ′ changes it by under 1 percent, and the sensitivity is reported beside. Its error is σ_c times the factor.
- **The weight, live:** w_k = (1 ∓ r_a,k/R0_k)/2, the branch by the median antiphase phase on one sheet (test 11's ruling), with the error propagated from both lengths. The weight at the fixed R0 = 0.4749 is computed beside and not used in any verdict.
- **The frame:** the control phase θ_c,k, unwrapped along the series.
- **Levels per span:** for each of w, R0 and θ_c, the mean over the span's whole repeats with the larger of the propagated error and the scatter over √n, as in test 12. A level change at a boundary is a difference of adjacent span means above five combined errors.
- **Pairs:** within-span adjacent pairs and the boundary pair (last whole repeat before, first whole after) as in test 12, on the antiphase phase and weight and on the control phase and length, with the same thresholds (phase: max(0.3 rad, 5 SE of the difference); weight: max(0.10, 5 SE); control length: 5 SE).
- **Usable:** median r_a ≥ 0.08 and median r_c ≥ 0.16; otherwise NOT USABLE and no verdict.

## 4. The verdicts

Three level verdicts, each with the words of test 12 (LEVELS DIFFER AT EVERY BOUNDARY, AT SOME, AGREE; WITHIN if any within-span pair switches on that series):

1. **The weight**, from w at the live R0.
2. **The envelope**, from R0 live.
3. **The frame**, from the control phase.

And one **attribution word per crossed boundary**, from the three level tests at that boundary: **NOTHING** (no level changed), **WEIGHT** (only w changed), **ENVELOPE** (only R0 changed), **FRAME** (only the control phase changed), **MIXED** (two or three changed). A boundary with no pair (fewer than one whole repeat on a side) is NO PAIR.

A weight level change read through the fixed R0 that the live reading does not confirm is reported beside as "a fixed-R0 reading not confirmed by the control", with both numbers. It counts in no verdict.

## 5. Floors at 500 shots, from the desk check

Control phase, per pair: about 0.30 rad, 4.3 kHz. R0 level per span: errors about 0.0037, 0.0037, 0.0055 (24, 24, 11 repeats), so a change of about 0.03 in R0 (six percent) resolves at five combined errors. Weight level per span: errors about 0.005, 0.005, 0.0074 at the live R0, a little above test 12's (the control's error enters), so a change of about 0.04 resolves. Frame level per span: a few tenths of a kHz.

**The branch rule's limit**, as in test 12: a common frequency step larger than about π/2 at 5.6 µs (45 kHz) corrupts the antiphase weight series; a frame step of that size shows in the control phase first, and when the control phase steps by more than 1 rad at a boundary the weight's attribution at that boundary is MIXED by rule, whatever the weight level test says.

## 6. Reported beside the verdicts, not used in them

1. The execution record, the straddling repeats and the boundary pairs.
2. The series θ_a, r_a, w (live and fixed), R0, θ_c, r_c per repeat, with spans and branches.
3. The weight per span at the live R0 beside test 12's at the fixed R0 and test 11's, with the hours between.
4. R0 per span beside the fixed 0.4749, and the τ′ sensitivity (the levels recomputed at τ′ = 100 and 160 µs).
5. The frame per span as a frequency (the control phase divided by 2π × 11.2 µs), beside test 12's monitor phase at 5.6 µs.
6. Readout, the stamp, the backend list, the estimate against the actual and the decision, as in test 12.
7. The X and Y repeat-to-repeat scatter against binomial, per wait and span (test 12's recount found Y sub-binomial at the antiphase wait; the control wait's scatter is the first reading of the same quantity at a wait where the lines are in phase).

## 7. The model's numbers

Sandhi (predictions-model-01-v3, digests `745059e3…38a3` and `02b80034…19b4`) has a channel for the weight by levels at monitor boundaries, 0.95 (0.64 to 1.00) per boundary as posted, and no channel for the envelope, the frame or the attribution. After test 12 the count behind that channel is 5 of 6, which no posted file yet carries; the rule quotes the posted number and reports the count beside. The envelope and frame verdicts and the attribution words are scored against Mantri's sealed expectations only.

## 8. The reporting

`report-t14.md` with the three level verdicts, the attribution per boundary, the counts of the run beside the model's number, and every item of section 6; `fits-t14.json` with every number; `counts-t14.json` with the execution metadata, the usage record removed; `stamps-t14.csv`; `hash-check-t14.md`; the script as run; `SHA256SUMS`.

## 9. The desk check

`desk-check-t14-mantri.py`, run before the hash, 100 trials per case, seed 14390, on test 11's day-2 parameters (A 0.487, τ′ 128.3 µs, Δ0 48.66 kHz, δ 44.70 kHz, b 0.344, c 0.4975), spans at positions 0 to 99, 100 to 199, 200 to 247:

| case | required | Mantri's rates |
|---|---|---|
| 1 steady | AGREE on all three; NOTHING at both boundaries, 100 | 100; floors as section 5; R0 median 0.4666 against the true 0.4662 |
| 2 weight levels down 0.06 and 0.14 at the boundaries | weight EVERY; envelope and frame AGREE; WEIGHT at both, at least 95 | 100; 100; 100 |
| 3 envelope down 15 percent at boundary 2, weight fixed | envelope SOME; weight AGREE; ENVELOPE at boundary 2, at least 95 | 100; 100; 100 (the fixed-R0 reading calls no weight change either: a 15 percent envelope change is under its resolution) |
| 3b envelope down 40 percent at boundary 2, weight fixed | as case 3; the fixed-R0 reading calls a weight change in at least 90 while the live reading calls none | ENVELOPE 100; fixed-R0 weight change in 98, live in 0 |
| 4 frame 10 kHz at boundary 1 | frame SOME; FRAME at boundary 1; NOTHING at boundary 2, at least 95 | 100; 100 |
| 5 weight down 0.14 and frame 10 kHz at boundary 2 | MIXED at boundary 2, at least 95 | 100 |
| 6 midpoint up 0.02 at boundary 2 (recorded) | reported | ENVELOPE at boundary 2 in 29, NOTHING in 71; the fixed-R0 reading calls a weight change in 4 |

Case 3b is the reason for the test: a large envelope change read through a fixed R0 is a weight change in nearly every trial, and the control reads it as what it is in every trial. Case 6 is recorded as a limit: the midpoint comes from the job's readout circuits, one value for the whole job, so a readout change inside the job shows partly as an envelope change and partly not at all.

The runner reruns the desk check after the run and records its rates beside these.
