# Kickoff 56: the rule, fixed before the run

Written 14 October 2026, before the job was built or submitted. Author: Anish Patel. This file states the design, the analysis and the verdict rule for Kickoff 56. Its SHA-256 is posted publicly before the run, and the file is published unchanged after it.

## The question

On 14 October 2026 (Kickoff 55), on ibm_kingston, the revised check missed on chain 6-7-8 at an added phase of +90° (d1 = +0.257), lay across its margin on 42-43-44, and held on 31-18-11.

The revised check predicts how Manacitra's wait test fares from a Ramsey in which the waiting qubit's neighbours do exactly what they do in the circuit. On ibm_fez (Kickoff 52), the wait test's effective offset differed from that Ramsey's by only 3.5° and 4.8°.

On these three Kingston chains, how far does the wait test's effective offset sit from the active-neighbour Ramsey's?

## The code

Manacitra at commit `e45f15d8e2de1796d552bad401e696ce9ba0be3a`, installed unedited. The circuits come from the package:

- the wait test: `build_wait_test(chain, refocus, backend, phase)`;
- the active-neighbour Ramsey: `build_wait_ramsey(chain, backend)`;
- the idle-neighbour Ramsey: `build_wait_ramsey(chain, backend, neighbours="idle")`.

The zero-wait baseline is the one used since Kickoff 50.

## The chains

Fixed here, not drawn: Kickoff 55's 6-7-8, 42-43-44 and 31-18-11, each written L1-M-L3 with M waiting.

## The run

- **Processor:** ibm_kingston, one job.
- **The phases:** φ ∈ {0°, 60°, 120°, 180°, 240°, 300°}, as one RZ on M right after its first H.
- **Per waiting qubit and per φ:**
  - W-no(φ), the wait test without refocusing;
  - R1(φ), the active-neighbour Ramsey;
  - R0(φ), the idle-neighbour Ramsey.
- **Per waiting qubit, once each:**
  - W-ref, the wait test with XY4 refocusing;
  - Z, the zero-wait baseline;
  - the pulse-cost circuit (H on M, the four XY4 pulses back to back with no wait, H, measure).
- **Shots:** 63 circuits, each run as 2 copies of 3,000 shots.
- **Settings:** dynamical decoupling, gate twirling and measurement twirling all off. Interleaving seed 5656.
- **When:** not inside ibm_kingston's calibration window, computed at build time by Kickoff 55's procedure: from 30 minutes before the next expected T1 stamp to 30 minutes after the next expected CZ stamp, using the previous 48 hours of published stamps.

## The analysis

- **Loss** = M's P(1) minus M's P(1) in Z.
- **F_no(φ)** is the squared Hellinger overlap with the wait test's φ = 0 parity ideal.
- **The fits.** For each waiting qubit and each instrument, fit y(φ) = c + b·cos φ + s·sin φ by ordinary least squares over the six phases, with the copies pooled.
  - For R0 and R1, y is the loss, and θ = atan2(s, −b).
  - For W-no, y is F_no, and θ = atan2(−s, b).
- **The leftover:** L = θ_W − θ_R1, wrapped to (−180°, +180°], per waiting qubit.
- **Intervals:** 90% intervals from one joint bootstrap over shots and copies, seed 56, refitting on every resample.

The verdict uses fitted phases. The fit is fixed here, before the data.

## The verdict

Given separately for each waiting qubit: **H56a** on 7, **H56b** on 43 and **H56c** on 18.

| verdict | condition |
|---|---|
| **LARGE** | L's interval lies entirely outside [−10°, +10°] |
| **SMALL** | L's interval lies entirely inside [−5°, +5°] |
| **NOT SETTLED** | otherwise |

## Reported beside the verdict, not used in it

1. **The idle Ramsey's part:** θ_W − θ_R0, and θ_R1 − θ_R0, with intervals.
2. **Each fit's amplitude and residuals.**
3. **The residuals at every phase:**
   - d1(φ) = F_no(φ) − F_ref × (1 − loss_R1(φ));
   - d0(φ), the same with R0.
4. **The lean:** the mean of d1 over the six phases, per waiting qubit.
5. **The pulse cost:** the pulse-cost circuit's P(1) minus Z's, per waiting qubit.
6. **The calibration record:**
   - the stamp at build, at submission, every 5 minutes until the job finishes, and after the fetch;
   - for each new stamp, which published values changed;
   - the job's status changes, with their times.

The rule is not changed after the data, whatever they show.
