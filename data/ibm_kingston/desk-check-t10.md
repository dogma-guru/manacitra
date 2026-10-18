# Test 10, stage 1a: the desk check of the rule's analysis and verdict (17 October 2026)

Runner's desk check for `tests/t10-phase-monitor/t10-rule.md`. Its SHA-256 is `89633a8d496eb7a9344c8c20187e0283fa0be69fe650b5b7b08bafdae96e8013` and its size 14,901 bytes. The hash was checked at 15:52:23 UTC on 17 October 2026, before anything else was read. It equals the one the author gave in chat and the one in `t10-rule.sha256` beside the rule, and the file still matched at 16:16:25 UTC on 17 October. `t10-rule-DRAFT.md` was not read. `desk-check-t10-mantri.py` beside the rule was not read either: it is not on the runner prompt's reading list, and this check is written independently of it.

Offline: no job was built for the provider and nothing was submitted. No sealed file and no scorecard or Mantri read was opened.

Kinds: every rate, count and statistic below is a model's output, from counts simulated with binomial shot noise from stated fringes. Each describes the rule's behaviour on those fringes and nothing about any qubit of ibm_kingston. Section 3 holds readings beyond the rule's list, labelled as such.

**Every required rate in the rule's last section is met.** The table is in section 2.

## 1. What was run

**The analysis and the verdict** (`phase_t10.py`), exactly as the rule states them, per qubit per job:

1. **The midpoint c:** the mean of the four readout circuits' P(1), P10 and P01 at the start and at the end.
2. **Per repeat k = 1 to 148:** P_X,k and P_Y,k from its two circuits; θ_k = atan2(P_Y,k − c, P_X,k − c); r_k the vector's length; s_k = σ_k / r_k with σ_k² = (P_X(1 − P_X) + P_Y(1 − P_Y)) / (2 × 1,000), floored at 0.02 rad.
3. **Usable:** e from job 0 at or below 3% (passed in by the caller) and the median r_k at least 0.08.
4. **The spans:** each repeat takes the span that ran both its circuits; a repeat whose two circuits ran in different spans is named, excluded from the switch counts, and its θ_k still reported.
5. **The unwrapped phase:** successive differences wrapped to (−π, π]; a difference of exactly π in size is flagged with its sign undetermined.
6. **A switch** between repeats k and k + 1: the wrapped difference's size above the larger of 0.3 rad and 5 √(s_k² + s_(k+1)²); within a span if both ran in one span, at a boundary if they ran in consecutive spans.
7. **The counts:** n_within and n_boundary; the within-span time; the within-span rate with its 90% Poisson interval.
8. **The levels:** the plateaus between switches, each with its weighted mean phase; two plateaus within 3 √(se₁² + se₂²) of each other are the same level.
9. **The slope per span:** a weighted straight-line fit of the unwrapped θ_k against k over the span's repeats, in rad per repeat and in kHz per minute at the qubit's wait.
10. **The dwell times** and the Kolmogorov test, for a qubit with n_within at least 8 pooled.

The verdict: QUIET if n_within = 0 and n_boundary = 0; SWITCHES AT BOUNDARIES ONLY if n_within = 0 and n_boundary ≥ 1; SWITCHES WITHIN SPANS if n_within ≥ 1; NOT USABLE if not usable. The pooled verdict over jobs 1 and 2 and the dwell-time word (MEMORYLESS at a Kolmogorov p-value of 0.01 or more, NOT MEMORYLESS below) are `pooled_verdict` and `dwell_word`.

**Readings of the rule's text, fixed here before any data** (the script's docstring carries them):

1. **"Consecutive spans"** are consecutive in start order. A pair of repeats in two spans that are not consecutive is recorded as such and counted in neither count.
2. **A pair separated by an excluded repeat** (one that straddled two spans) is not tested. The unwrapped phase steps across the excluded repeat by the wrapped difference of its neighbours.
3. **The within-span time** is the number of tested within-span pairs times the span's repeat period, the span's duration over the number of repeats assigned to it.
4. **The 90% Poisson interval** is Garwood's central interval: χ²(0.05; 2n) / 2 and χ²(0.95; 2n + 2) / 2, over the time, with the lower end 0 when n is 0.
5. **The plateaus** are the runs of included repeats between switches, each with the weighted mean of its unwrapped phase (weights 1 / s_k²) and its standard error 1 / √(the sum of the weights).
6. **"The same level"** is closed by linking: if A matches B and B matches C, all three are one level, even where A and C alone would not match. A level's mean is its plateaus' weighted mean, each taken relative to the first, wrapped.
7. **The slope** is fitted over a span's included repeats, where there are at least 3. The kHz per minute is the rad per repeat × 1 / (2π t) × 60 / the span's repeat period. One radian at 20 µs is 7.96 kHz, the rule's 8.0.
8. **A dwell time** is a plateau opened and closed by within-span switches, inside one span, with no untested pair in it. Its length is its number of repeats times its span's repeat period.
9. **The Kolmogorov test** is SciPy's `kstest` against an exponential with location 0 and scale the dwell times' mean. The standard deviation over the mean uses ddof 1. The test also needs at least two dwell times; with fewer, no word is given and the dwell times are listed, as the rule says for fewer than 8 switches.

**The simulated job:**

- **The positions:** the rule's 300, P10 and P01, then 148 repeats of X then Y, then P10 and P01, each 1,000 shots drawn binomially. There is no readout error, so the readout circuits read 0 and 1 and c is near 0.5.
- **The fringe,** in the models' convention: P_X = c + A e^(−t/τ) Re(z) and P_Y = c + A e^(−t/τ) Im(z), with z = Σ w exp(i(2πft + π)) over the lines, so a one-line X fringe reads 0.05 at zero wait.
- **The defaults:** amplitude 0.45, decay 100 µs, wait 20 µs, as the rule's section states. The line frequency, which the rule leaves open, is 10 kHz here.
- **The simulated execution record:** spans of positions 0 to 99, 100 to 199 and 200 to 299, each 28.2 s long and 0.7 s apart. Span 0 runs P10, P01 and repeats 1 to 49; span 1 runs repeats 50 to 99; span 2 runs repeats 100 to 148, P10 and P01. The boundary pairs are (49, 50) and (99, 100), and the repeat periods are 0.576, 0.564 and 0.576 s.

**The cases,** the rule's eight in its order, 100 trials each. A change in a line is set at the first circuit of the stated repeat.

1. One line steady.
2. The same at amplitude 0.3 with a 30 µs decay (r 0.154).
3. A step from 10 to 14 kHz at repeat 30 and back at repeat 80: the planted switches are the pairs (29, 30) and (79, 80), both within spans.
4. The same with a 1 kHz step.
5. A 4 kHz step over repeats 50 to 99, so the planted switches are the two boundary pairs.
6. A two-state telegraph between 43's lines at 46 µs, amplitude 0.4 and decay 56.6 µs (r 0.178):
   - the lines are −5.97 and −16.86 kHz, test 8's, so at 46 µs their phases differ by 3.147 rad;
   - the state is the same for both circuits of a repeat and flips between repeats with probability 1/20 (a mean dwell of 20 repeats);
   - the planted number of switches is the number of flips.
7. One line drifting from 10 to 12 kHz, linear in position from the first repeat circuit to the last.
8. 43's two lines at 46 µs with the weight drawn fresh per shot at 0.5, so each position's P(1) is the mean of the two lines'.

The counts of trial j of case c come from `default_rng(SeedSequence([10390, c, j]))`, and case 6's flips from the same stream.

Versions: Python 3.14.8, NumPy 2.5.3, SciPy 1.18.1. Wall time: 0.7 s for the 800 trials in one process, 0.9 ms per analysis.

## 2. The rates

| # | case | required | QUIET | AT BOUNDARIES ONLY | WITHIN SPANS | NOT USABLE | median r | met |
|---|---|---|---|---|---|---|---|---|
| 1 | one line steady | QUIET ≥ 95% | 100 | 0 | 0 | 0 | 0.369 | yes |
| 2 | amplitude 0.3, 30 µs decay | QUIET ≥ 95% | 100 | 0 | 0 | 0 | 0.155 | yes |
| 3 | 4 kHz step at repeat 30, back at 80 | WITHIN SPANS ≥ 95%; both at the planted repeats ≥ 90% | 0 | 0 | 100 | 0 | 0.369 | yes |
| 4 | 1 kHz step | recorded | 100 | 0 | 0 | 0 | 0.369 | |
| 5 | 4 kHz step at both boundaries | AT BOUNDARIES ONLY ≥ 95% | 0 | 100 | 0 | 0 | 0.369 | yes |
| 6 | antiphase telegraph at 46 µs | WITHIN SPANS ≥ 95%; count within one ≥ 90%; separation within 0.3 rad of π ≥ 90% | 0 | 0 | 100 | 0 | 0.178 | yes |
| 7 | 2 kHz drift across the job | no switch ≥ 95% | 100 | 0 | 0 | 0 | 0.369 | yes |
| 8 | weight 0.5 drawn per shot | recorded | 0 | 0 | 0 | 100 | 0.019 | |

**The extra quantities the rule names:**

- **Case 3:** both switches were found at the planted pairs, (29, 30) and (79, 80), within spans, in 100 of 100. Every trial found exactly those two switches and no others, and returned two levels.
- **Case 5:** n_within 0 and n_boundary 2 in 100 of 100, at the planted pairs (49, 50) and (99, 100) every time.
- **Case 6:**
  - The planted flips per trial ran from 1 to 14, median 7.
  - The switches found, within spans and at boundaries together, equalled the planted number in 100 of 100, so within one in 100.
  - In 8 trials a flip fell on a boundary pair and was counted there; those trials still read SWITCHES WITHIN SPANS from their other flips.
  - Two levels in 100 of 100. Their separation: median 3.129 rad, range 3.090 to 3.142, within 0.3 rad of π in 100 of 100.
- **Case 7:** no switch called in 100 of 100. The slope per span:

  | span | planted, kHz per minute | median found | 5th to 95th percentile |
  |---|---|---|---|
  | 0 | 1.414 | 1.400 | 1.07 to 1.93 |
  | 1 | 1.442 | 1.489 | 0.92 to 2.17 |
  | 2 | 1.414 | 1.406 | 0.74 to 1.95 |

  The planted slope is 0.0136 kHz (0.0017 rad at 20 µs) per repeat, through each span's repeat period from the record. For comparison, case 1's steady line gave medians of −0.01, 0.04 and 0.00 kHz per minute, with 5th to 95th percentiles within about ±0.6.
- **Case 4:** QUIET in 100 of 100, with no switch in any trial. A 1 kHz step at 20 µs is 0.126 rad, below the 0.3 rad floor; the rule names that floor, about 2.4 kHz at 20 µs, as a limit.
- **Case 8:** NOT USABLE in 100 of 100, median r 0.0186 (range 0.016 to 0.021).

These rates and quantities match the figures the rule's text records for the check made before the hash. The runner did not read that check's script.

## 3. Readings beyond the rule's list (no required rate)

**Near the floor on r** (`desk_t10_floor.py`): one line steady at 10 kHz, 20 µs wait, 100 µs decay, with the amplitude set so that r is 0.08 to 0.15. The desk check's positions, spans and counts otherwise; 100 trials each; seeds SeedSequence([10391, case, trial]).

| r planted | 0.08 | 0.09 | 0.10 | 0.12 | 0.15 |
|---|---|---|---|---|---|
| QUIET | 85 | 100 | 100 | 100 | 100 |
| NOT USABLE | 15 | 0 | 0 | 0 | 0 |
| median of the median r | 0.0815 | 0.0915 | 0.1011 | 0.1212 | 0.1507 |

No switch was called at any r. At the floor itself about one trial in seven falls below 0.08 by shot noise and returns NOT USABLE.

**The switch threshold against r** (arithmetic on the rule's formula, at c = 0.5 and 1,000 shots, where σ_k² = (0.5 − r²) / 2,000). The 5-standard-error term exceeds the 0.3 rad floor wherever r is below 0.33:

| r | 0.08 | 0.10 | 0.15 | 0.178 | 0.20 | 0.30 | 0.33 and above |
|---|---|---|---|---|---|---|---|
| threshold, rad | 1.39 | 1.11 | 0.73 | 0.61 | 0.54 | 0.34 | 0.30 |
| at 20 µs, kHz | 11.1 | 8.8 | 5.8 | 4.8 | 4.3 | 2.7 | 2.4 |

So the 2.4 kHz limit the rule names holds for r of 0.33 or more. On a weaker fringe the smallest switch the rule can call is larger, up to 11 kHz at the floor. A switch of π, as on the antiphase qubits, is above the threshold at every usable r.

**The size of a switch** (`desk_t10_sizes.py`, the desk check's counts and seeds for cases 3 and 5). The planted step is 4 kHz (0.503 rad at 20 µs).

| case | median size up | median size down | sd per switch | median levels' separation | its sd |
|---|---|---|---|---|---|
| 3 | +4.03 kHz | −4.08 kHz | 0.42 and 0.44 kHz | 4.02 kHz | 0.06 kHz |
| 5 | +4.03 kHz | −4.04 kHz | 0.48 and 0.46 kHz | 4.01 kHz | 0.06 kHz |

A single switch's size carries about 0.4 kHz of shot noise at r 0.37, while the levels' separation carries about 0.06. The dry run's simulated qubit 0, with the same plant, returned switch sizes of 3.45 and −3.43 kHz and levels 4.05 kHz apart (`dry-run-t10.md`, section 3). That is within this spread.

## 4. The wall time of the live analysis

- **The dry run's three simulated jobs:** 72, 72 and 60 qubits, from reading the counts files to every beside item, took 1.32 s in one process (`analyse_t10.py`).
- **About 80 qubits and three jobs:** about 1.5 s, since the work is linear in qubits.

## 5. Files

In `stage1/`, beside this report and `dry-run-t10.md`:

- **Scripts:** `phase_t10.py`, `desk_t10.py`, `desk_t10_floor.py` and `desk_t10_sizes.py`.
- **Records:** `desk-t10.json` (every trial's verdict, counts, switches, levels and slopes, and the per-case rates), `desk-t10-floor.json` and `desk-t10-sizes.json`.

Nothing here is adopted. The author reads this and the dry run, seals the predictions, and gives the go in chat or does not.
