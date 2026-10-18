# Test 9, stage 1a: the desk check of job 2's verdict rule (17 October 2026)

Runner's desk check for `tests/t9-kingston-day2/t9-rule.md`. Its SHA-256 is `4858f55e37fbc72b1806ee4033028e30a59c1782009600f4d9d6fa71806181d4` and its size 16,749 bytes. The hash was checked at 10:50:54 UTC on 17 October 2026, before anything else was read. It equals the one the author gave in chat and the one in `t9-rule.sha256` beside the rule, and the file still matched at 11:21:38 UTC on 17 October. `t9-rule-DRAFT.md` was not read.

Offline: no job was built for the provider and nothing was submitted. No sealed file and no scorecard or Mantri read was opened.

Kinds: every rate, count and statistic below is a model's output, from counts simulated with binomial shot noise from stated fringes. Each describes the rule's behaviour on those fringes and nothing about any qubit of ibm_kingston. Section 3 is a reading beyond the rule's list, labelled as one.

**Every required rate in the rule's last section is met.** The table is in section 2.

## 1. What was run

**Job 2's analysis** (`scan_t9.py`), exactly as the rule states it, per repeat:

- **P(1)** per wait per quadrature from the repeat's 16 circuits, with the binomial standard error floored at 1/n (p (1 − p) at least 1/n, test 7's).
- **The model:** S with τ held: P_X = c + A e^(−t/τ) cos(2πΔt + φ), and P_Y the same with sin. That is Y as X with the phase minus π/2, `ramsey_xy_fit`'s convention.
- **The point fit:** a grid over Δ from −125 to 125 kHz in 0.5 kHz steps (501 steps), with c, A cos φ and A sin φ solved by weighted linear least squares at each step. Then a local least-squares refinement from the best step: χ² minimised over Δ within one grid step, with the three linear parameters solved exactly at each Δ. That reaches the minimum a joint refinement of all four reaches from that step. No random starts.
- **The standard error s_k:** the standard deviation (ddof 1) of Δ over 200 bootstrap draws. Each draw redraws the shots binomially from the repeat's observed proportions and repeats the fit from a 1 kHz grid within 10 kHz of the point fit (21 steps), with the same refinement. It is scaled by √(χ²/12) where that exceeds 1 and floored at 0.25 kHz.

**The three models,** weighted by 1/s_k²:

- **C:** the weighted mean, χ²_C on 17 degrees of freedom.
- **Two levels:** every AB pattern (one transition) and every ABA pattern (two), each run at least 3 repeats long, with each level the weighted mean of its repeats; χ²_2 on 17 − n degrees of freedom.
- **L:** a straight line by weighted least squares, χ²_L on 16.

**The verdict and the flag:**

- STEADY if χ²_C ≤ 40.79.
- STEPPED if not STEADY and all of these hold for the best pattern:
  - χ²_2 ≤ 39.25 (16 degrees of freedom) or 37.70 (15);
  - the two levels differ by more than 1 kHz, and by more than 5 √(1/W_A + 1/W_B);
  - χ²_2 < χ²_L.
- MOVING otherwise.
- The flag ONE-LINE FIT POOR is set when the median per-repeat χ² exceeds 36.
- The three thresholds were computed with SciPy as the 99.9th percentiles; they equal the rule's figures.

**Readings of the rule's text, fixed here before any data:**

1. **"The best two-level pattern"** is the pattern with the smallest χ²_2 over all allowed AB and ABA patterns (a tie goes to fewer transitions, then the earlier change).
2. **"The same with a Gaussian envelope of 25 µs"** is run in both readings, amplitude 0.45 and amplitude 0.3 (as in the case before it), and each is held to the steady cases' rate.
3. **The decay held in the desk fits** is the rule's own: job 1's fitted S decay. Here it comes from `ramsey_xy_fit` at `b7313bb` on the case's fringe as test 7's design would record it at the start of the job (64 waits, both quadratures, exact counts at 10⁷ shots), clipped to 10 to 400 µs, and recorded per case. Section 2's sensitivity reading shows what changes when it is held at the generating decay instead.
4. **A moving frequency or weight is set per circuit position:** a step at the first circuit of the stated repeat; a drift linear in position from the first repeat circuit to the last; the alternation by repeat pairs.

**The cases:** the rule's cases, in its order, plus the second reading of the Gaussian case, at 100 trials each. Fringes have amplitude 0.45 about 0.5 with a 60 µs decay unless stated, with φ = π (P(1) 0.05 at zero wait in X) and 1,000 shots per circuit. The counts of trial j of case c come from SeedSequence([9390, c, j]), and repeat k's bootstrap from SeedSequence([9391, c, j, k]).

Versions: Python 3.14.8, NumPy 2.5.3, SciPy 1.18.1. Wall time: 205 s for 1,300 trials on 9 worker processes.

## 2. The rates

| # | case | required | STEADY | STEPPED | MOVING | flag | τ held (µs) | met |
|---|---|---|---|---|---|---|---|---|
| 1 | one line steady at 20 kHz | STEADY ≥ 95% | 100 | 0 | 0 | 0% | 60.0 | yes |
| 2 | the same, amplitude 0.3, 25 µs decay | STEADY ≥ 95% | 100 | 0 | 0 | 0% | 25.0 | yes |
| 3 | the same, Gaussian envelope of 25 µs, amplitude 0.45 | STEADY ≥ 95% | 100 | 0 | 0 | **100%** | 22.8 | yes |
| 4 | the same, Gaussian envelope of 25 µs, amplitude 0.3 | STEADY ≥ 95% | 100 | 0 | 0 | **100%** | 20.8 | yes |
| 5 | a step from 55 to 12 kHz at the ninth repeat | STEPPED ≥ 95% | 0 | 100 | 0 | 0% | 60.0 | yes |
| 6 | a step from 20 to 25 kHz at the eleventh repeat | STEPPED ≥ 95% | 0 | 100 | 0 | 0% | 60.0 | yes |
| 7 | a step from 20 to 22 kHz at the eleventh repeat | STEPPED ≥ 80% | 0 | 100 | 0 | 0% | 60.0 | yes |
| 8 | a drift from 20 to 35 kHz across the job | MOVING ≥ 90% | 0 | 0 | 100 | 0% | 60.0 | yes |
| 9 | a drift from 20 to 22 kHz across the job | recorded | 17 | 11 | 72 | 0% | 60.0 | |
| 10 | alternating 20 and 35 kHz every two repeats | MOVING ≥ 90% | 0 | 0 | 100 | 0% | 60.0 | yes |
| 11 | two lines at once, finding 28's values, weight fixed | recorded | 13 | 1 | 86 | 100% | 63.3 | |
| 12 | the same, the weight moving from 0.45 to 0.27 | recorded | 0 | 76 | 24 | 100% | 76.7 | |
| 13 | two lines at once, 43's values | recorded | 100 | 0 | 0 | 100% | 21.5 | |

No trial returned NOT USABLE. Finding 28's values are Δ0 48.66, δ 44.82 kHz, b 0.355, τ′ 128.3 µs. 43's values are test 8's job 1 fit: Δ0 −11.42, δ 5.45 kHz, b 0.565, τ′ 56.6 µs.

**Where the steps were placed.**

| case | change found at the planted repeat | median levels (kHz) | pattern |
|---|---|---|---|
| 5 | 100 of 100 | 54.99 and 11.99 | AB every time |
| 6 | 100 of 100 | 20.01 and 25.02 | AB every time |
| 7 | 98 of 100 | 19.96 and 22.02 | AB every time |

**Readings of the recorded cases** (a model's output, no requirement):

- **Finding 28's two lines, weight fixed (case 11),** read MOVING in 86 of 100, not STEADY. Each repeat's one-line fit takes one line or the other (median per-repeat χ² 776), so Δ_k jumps between them across the repeats. The rule's text says this fringe "returns STEADY with the flag". Here it returns the flag every time, but STEADY only 13 times in 100.
- **With the weight moving (case 12),** it read STEPPED in 76 of 100, the fit moving from one line to the other as the weight crosses.
- **43's two lines (case 13)** read STEADY in 100 of 100, but with the flag every time (median per-repeat χ² 48.9, against the line at 36). The rule's text says this fringe returns "STEADY without it". The flag comes from the decay held: job 1's S fit puts it at 21.5 µs, where the fringe's own decay is 56.6 µs.
- **One line with a Gaussian decay (cases 3 and 4)** read STEADY every time, with the flag every time, from the same cause.

**A sensitivity reading, not the rule's procedure** (`desk_t9_tau.py`, the same counts with τ held at the decay that generated each fringe):

| case | τ held (µs) | STEADY | STEPPED | MOVING | flag | median per-repeat χ² |
|---|---|---|---|---|---|---|
| 3 | 25 | 100 | 0 | 0 | 100% | 93.7 |
| 4 | 25 | 100 | 0 | 0 | 0% | 29.4 |
| 11 | 128.3 | 1 | 0 | 99 | 100% | 815.4 |
| 12 | 128.3 | 0 | 74 | 26 | 100% | 705.0 |
| 13 | 56.6 | 100 | 0 | 0 | 0% | 15.7 |

- With τ held at the generating decay, 43's lines read STEADY without the flag, as the rule's text says.
- So the difference in case 13 comes from where the rule takes τ, job 1's S fit, and not from the fit or the models.
- Finding 28's lines read MOVING under either τ, so that sentence of the rule's text does not hold in this check under either.
- None of these cases carries a required rate, and none changes whether the rule is met.

## 3. A reading beyond the rule's list: one line steady at a small detuning

The dry run's simulated job 2 returned STEPPED on one qubit planted as one steady line: 108, at −4.1 kHz with an 83 µs decay (`dry-run-t9.md`, section 3).

- **Why:** at so slow a fringe the 24 µs scan sees only a tenth of a cycle. In 3 of its 18 repeats the fit took a second solution, with A near 1 and Δ near −1 kHz, which lifted χ²_C to 62.
- **Why it matters:** test 8 measured |S's Δ| at a median of 6 kHz over kingston's qubits (5th percentile 0.3 kHz), so slow fringes are common there.
- **The grid** (`desk_t9_slow.py`, 100 trials per case, τ held as in section 2): one line steady at each detuning.

| Δ (kHz) | 0 | 1 | 2 | 3 | 4 | 6 | 8 | 12 |
|---|---|---|---|---|---|---|---|---|
| STEADY, 60 µs decay | 100 | 93 | 92 | 99 | 100 | 100 | 100 | 100 |
| STEADY, 120 µs decay | 100 | 100 | 95 | 98 | 100 | 100 | 100 | 100 |

- The others returned STEPPED or MOVING; the flag never fired.
- Between 1 and 3 kHz, one steady line returns STEPPED or MOVING in up to 8 of 100 trials. At 1 and 2 kHz with a 60 µs decay that is below the 95% the rule requires of its steady cases.
- That requirement is written for the rule's own cases, and this case is not among them. So no required rate fails, and the rule stands as hashed.
- The reading for the author: on kingston, a STEPPED or MOVING qubit whose Δ̄ is within about 3 kHz of zero sits where a steady line also lands up to one time in twelve in this check.

## 4. The wall time of the live analysis

- **Job 2 at 200 draws:** 72 simulated qubits took 10.2 s on 9 worker processes (dry run, section 3). About 80 qubits take about 12 s; a second set of about 60 for job 3, about 9 s.
- **Job 1 at 2,000 draws** (test 8's analysis): test 8's live job 1 took 402 s for 78 qubits, so about 7 minutes for about 80.

## 5. Files

In `stage1/`, beside this report and `dry-run-t9.md`:

- **Scripts:** `scan_t9.py`, `desk_t9.py`, `desk_t9_tau.py` and `desk_t9_slow.py`.
- **Records:** `desk-t9.json` (every trial's verdict and statistics, the per-case rates, the decays held), `desk-t9-tau.json` and `desk-t9-slow.json`.

Nothing here is adopted. The author reads this and the dry run, seals his predictions, and gives the go in chat or does not.
