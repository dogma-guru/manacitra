# Test 7, version 5.1 report: the desk power check, KEPT

Runner's hand-back for `tests/t7-steady-or-switching-143/kickoff-t7-steady-or-switching-v5.1-DRAFT-2026-10-16.md`, its desk power check section only, under ruling R5 as taken by the author on October 16. Run on 16 October 2026, 16:43 to 20:46 UTC, on this machine: 10 cores (4 performance, 6 efficiency), 10 worker processes with one thread each. Nothing from the hardware section and nothing from the "Beside the verdict" diagnostics was run. The telegraph model was not fitted, and no provider was called. Nothing here is adopted, and nothing goes to hardware without the author's go.

**The question, in one line.** Under the version 5.1 design (64 waits from 0 to 63 µs, X and Y quadratures, two copies of 1,500 shots) and rule, does the rule return the generating verdict in at least 80% of simulated draws at 88 or more of the 117 counted grid points?

**Verdict: KEPT. 106 of the 117 counted points return the generating verdict in at least 80% of draws; 88 were needed.** By generating verdict:

- NO RESOLVED SPLIT: 25 of 27 points.
- TWO FIXED FREQUENCIES: 81 of 90 points.

The grid is complete: 135 of 135 points, 27,000 draws, in one run of 3.79 h of wall time, against a projection of 3.42 h and a line of twelve hours. Every step passed its line:

- **Step 1, the fit check:** 2 of 480 fits missed.
- **Step 2, the timing:** projected the grid at 3.4 h.
- **Step 3, the grid:** ran to the end without a restart, and no line was dropped.

**Both of round 5's defects are gone from the draws.**

- **The alias:** 0 of 27,000 draws put a P line outside the band, and none came within 1 kHz of it. The largest |Δ0| + δ over all draws is 210.5 kHz.
- **The edge:** 1,736 draws put b's point fit at an edge, all of them at NO RESOLVED SPLIT points (δ = 0 and 3 kHz). The weight clause reads every one of them as a lone line, and all returned NO RESOLVED SPLIT. No draw at a TWO FIXED FREQUENCIES point or a boundary point put b at an edge.

Kinds:

- **Computed facts of this run:** the keep verdict, the counts and every fraction below.
- **What they are about:** simulated draws of the kickoff's two models with binomial shot noise. The run is a power check of the design and its rule, not a statement about qubit 143.
- **Readings for the threshold:** the pass fractions by δ, by b and by τ, never changes. The rule, the threshold and the grid are as R5 fixed them.

## The eleven failing points: two kinds, both about resolution, neither a defect

1. **Span at τ = 15 µs (9 points): the beat does not move the held-out error by the rule's 0.01.**
   - **δ = 8 kHz, at every Δ0 and both weights (#5, #6, #50, #51, #95, #96): 0% each.** P's held-out error beats S's by a median of 0.0064 to 0.0065 at b = 0.5 and 0.0053 to 0.0055 at b = 0.37, at most 0.0091, under the 0.01 margin. In every draw, δ's lower bound is above 5 kHz and b's interval lies inside (0.05, 0.95): the fit finds the split, but the held-out error does not move enough to count it.
   - **δ = 11 kHz with b = 0.37 (#8, #53, #98): 48% to 54%.** The margin's median sits at 0.0099 to 0.0101, on the line.
   - **The same split at b = 0.5 (#7, #52, #97) passes at 93% to 96%,** with a median margin of 0.0117 to 0.0119.
   - **Why:** with a 15 µs decay, the fringe is mostly gone before an 8 kHz beat develops. At b = 0.37 the beat is shallower than at equal weights, so it needs a larger split to reach the margin.
2. **Threshold at τ = 150 µs (2 points): a 3 kHz split resolved, below the 5 kHz threshold.**
   - **#76 (Δ0 55 kHz) returns NO RESOLVED SPLIT in 79.5% of draws, #121 (Δ0 75 kHz) in 73.5%,** both at δ = 3 kHz and b = 0.5. #31 (Δ0 40 kHz) passes at 86.5%.
   - **What the fits show:** P fits δ at 3.00 kHz, with a median interval of 2.90 to 3.12 kHz. In 20.5% and 26.5% of the draws, P's held-out error beats S's by more than 0.01, so S is not within 0.01. With δ's lower bound under 5 kHz, those draws are NOT SETTLED, as the rule intends.
   - **At b = 0.37 the same three points pass at 98%,** with a median margin of 0.0083 against 0.0093 at b = 0.5.

## The threshold reading: where the design resolves the beat (a reading, not a change)

The held-out margin of 0.01 decides where a split counts as resolved, more than the precision of δ does:

- **At τ = 60 and 150 µs, the 5 kHz boundary points are resolved in every draw.** P beats S by more than 0.01, and δ is fitted at 5.00 kHz with a median interval of 4.92 to 5.08 kHz (τ 60 µs) and 4.95 to 5.05 kHz (τ 150 µs). Because the truth sits on the threshold, the lower bound straddles it, and the draws return NOT SETTLED (97% and 98.5%) or TWO FIXED FREQUENCIES (3% and 1.5%).
- **At τ = 15 µs, P never beats S by 0.01 at δ = 5 kHz.** These points return NO RESOLVED SPLIT in 92.7% of draws, since δ's median interval, 4.43 to 5.94 kHz, puts its lower bound under 5.
- **At τ = 60 µs, a 3 kHz split moves the held-out error by a median of 0.0052,** and every draw is NO RESOLVED SPLIT. At τ = 150 µs and b = 0.5, it moves it by 0.0093, and one draw in five crosses the margin.

Read together:

| τ | the beat is resolved by the held-out error from |
|---|---|
| 15 µs | about 11 kHz at equal weights; 15 kHz at b = 0.37 |
| 60 µs | 5 kHz, but not 3 |
| 150 µs | 5 kHz, and 3 kHz in a fifth of the draws at equal weights |

The 5 kHz threshold sits below what a 15 µs decay can resolve and at the edge of what 60 and 150 µs resolve. That is the reading the kickoff asked for, for a later version's threshold. Nothing here changes it.

## Step 1: the fit check (passed)

Every (Δ0, δ) pair of the grid at τ = 60 µs and b = 0.5 (24 pairs; at δ = 0 the generating model is S), ten draws each with the grid's own seeds. Each draw's 40-start S and P fits were run against references of 244 S starts and 800 P starts, under the new P bounds. All 800 reference starts lie inside the new bounds, so the reference is round 5's unchanged.

- **Misses: 2 of 480 fits (0.42%), against a stop line of 5%.** S missed 0 of 240, P 2 of 240 (0.8%).
- **Both misses are P fits at δ = 0** (S generating): #15 draw 7 (Δ0 40 kHz), shortfall 1.63, and #105 draw 6 (Δ0 75 kHz), shortfall 4.57.
- **Largest S shortfall:** 3.2·10⁻⁵. No 40-start fit beat its reference by more than 10⁻⁵.
- **Against the new bound:** none of the 240 P fits has |Δ0| + δ within 1 kHz of 250 kHz, and none of the 240 reference fits does. The largest reach is 172.7 kHz.

Wall time 4.8 minutes (16:43:04 to 16:47:51 UTC).

## Step 2: the timing (under the line)

Round 5's six points, 200 draws each, under the new seeds, bounds and rule:

| # | Δ0 kHz | τ µs | δ kHz | b | generating | NRS / 2F / NS, % | ≥ 80% | round 5's generating share | CPU s per draw |
|---|---|---|---|---|---|---|---|---|---|
| 60 | 55 | 60 | 0 | none | NO RESOLVED SPLIT | 100 / 0 / 0 | yes | 24.5% | 3.89 |
| 43 | 40 | 150 | 50 | 0.5 | TWO FIXED FREQUENCIES | 0 / 100 / 0 | yes | 54% | 6.16 |
| 102 | 75 | 15 | 30 | 0.37 | TWO FIXED FREQUENCIES | 0 / 100 / 0 | yes | 73.5% | 5.40 |
| 77 | 55 | 150 | 3 | 0.37 | NO RESOLVED SPLIT | 98 / 0 / 2 | yes | 76.5% | 2.43 |
| 22 | 40 | 60 | 11 | 0.5 | TWO FIXED FREQUENCIES | 0 / 100 / 0 | yes | 52% | 3.76 |
| 95 | 75 | 15 | 8 | 0.5 | TWO FIXED FREQUENCIES | 0 / 0 / 100 | no | 0% | 5.72 |

- **CPU seconds per draw:** mean 4.56, median 4.34, largest 13.19.
- **Projection, as the kickoff fixes it:** 4.56 s × 27,000 draws ÷ 10 workers = **3.42 h**, against the twelve-hour line. From the timing's own wall time (555.5 s for 1,200 draws) it is 3.47 h.
- **NOT SETTLED at the δ = 0 point:** 0 of 200 (round 5: 151 of 200). b's point fit is at an edge in 184 of the 200 draws and b's interval reaches an edge in 199, so the weight clause carries them.
- **Draws whose best P fit lies outside the band, over all six points:** 0. That is the expected number, since the bound forbids it. Draws pressing within 1 kHz of 250 kHz: 0.
- **Wall time:** 9.3 minutes (16:48:03 to 16:57:19 UTC).

The grid draws the timed points with the same seeds, so its lines for these six reproduce the timing's fractions exactly.

## Step 3: the grid (complete)

| | |
|---|---|
| start and end | under `nohup` at 16:57:34 UTC; finished at 20:44:45 UTC |
| wall time | 13,631 s (3.79 h), 11% over the projection |
| order | the 117 counted points first, then the 18 boundary points |
| restarts | none; no last line dropped; no point in flight discarded |
| CPU | 37.8 h; 5.05 s per draw (the timing's six points: 4.56) |
| results | `results-t7v51.jsonl`, one line per point with every draw; the run's record is `grid-run-t7v51.json` |

## The tables

The sections from here to the convergence counts are `tables_t7v51.py`'s output, as run on `results-t7v51.jsonl` (it also wrote `keep-t7v51.json`). NRS, 2F and NS stand for NO RESOLVED SPLIT, TWO FIXED FREQUENCIES and NOT SETTLED.

### Keep: KEPT: 106 of 117 counted points return the generating verdict in at least 80% of draws (88 of 117 needed); 135 of 135 points written.

| generating verdict | points at or above 80% |
|---|---|
| NO RESOLVED SPLIT | 25 of 27 |
| TWO FIXED FREQUENCIES | 81 of 90 |

### The alias and the edge, over every draw written

- **The alias:** 0 of 27000 draws have P's point fit outside the band (|Δ0| + δ above 250 kHz). 0 press against it (within 1 kHz of 250 kHz), at points [].
- **The edge:** 1736 of 27000 draws have b's point fit below 0.05 or above 0.95; 2207 have b's interval reaching an edge. Those with the point fit at an edge returned NO RESOLVED SPLIT 1736, TWO FIXED FREQUENCIES 0, NOT SETTLED 0.
  - generating NO RESOLVED SPLIT: b's point fit at an edge in 1736 of 5400 draws, b's interval reaching an edge in 2207
  - generating TWO FIXED FREQUENCIES: b's point fit at an edge in 0 of 18000 draws, b's interval reaching an edge in 0
  - generating either: b's point fit at an edge in 0 of 3600 draws, b's interval reaching an edge in 0

### The pass fraction by δ and by b (a reading for the threshold, not a change)

| δ kHz | points | generating | at or above 80% | mean share NRS / 2F / NS, % |
|---|---|---|---|---|
| 0 | 9 | NO RESOLVED SPLIT | 9 of 9 | 100 / 0 / 0 |
| 3 | 18 | NO RESOLVED SPLIT | 16 of 18 | 96.2 / 0 / 3.8 |
| 5 | 18 | either (boundary) | not counted | 30.9 / 1.5 / 67.6 |
| 8 | 18 | TWO FIXED FREQUENCIES | 12 of 18 | 0 / 66.7 / 33.3 |
| 11 | 18 | TWO FIXED FREQUENCIES | 15 of 18 | 0 / 91.1 / 8.9 |
| 15 | 18 | TWO FIXED FREQUENCIES | 18 of 18 | 0 / 100 / 0 |
| 30 | 18 | TWO FIXED FREQUENCIES | 18 of 18 | 0 / 99.3 / 0.7 |
| 50 | 18 | TWO FIXED FREQUENCIES | 18 of 18 | 0 / 100 / 0 |

| b | counted points at or above 80% (δ > 0) | mean share of the generating verdict |
|---|---|---|
| 0.5 | 49 of 54 | 92.9% |
| 0.37 | 48 of 54 | 91.5% |

| δ kHz | b | at or above 80% | mean share NRS / 2F / NS, % |
|---|---|---|---|
| 3 | 0.5 | 7 of 9 | 93.3 / 0 / 6.7 |
| 3 | 0.37 | 9 of 9 | 99.2 / 0 / 0.8 |
| 5 | 0.5 | not counted | 30.6 / 1.4 / 68 |
| 5 | 0.37 | not counted | 31.2 / 1.6 / 67.2 |
| 8 | 0.5 | 6 of 9 | 0 / 66.7 / 33.3 |
| 8 | 0.37 | 6 of 9 | 0 / 66.7 / 33.3 |
| 11 | 0.5 | 9 of 9 | 0 / 98.2 / 1.8 |
| 11 | 0.37 | 6 of 9 | 0 / 84 / 16 |
| 15 | 0.5 | 9 of 9 | 0 / 100 / 0 |
| 15 | 0.37 | 9 of 9 | 0 / 100 / 0 |
| 30 | 0.5 | 9 of 9 | 0 / 99.3 / 0.7 |
| 30 | 0.37 | 9 of 9 | 0 / 99.3 / 0.7 |
| 50 | 0.5 | 9 of 9 | 0 / 100 / 0 |
| 50 | 0.37 | 9 of 9 | 0 / 100 / 0 |

| τ µs | δ 0 | δ 3 | δ 5 | δ 8 | δ 11 | δ 15 | δ 30 | δ 50 |
|---|---|---|---|---|---|---|---|---|
| 15 | 3 of 3 | 6 of 6 | not counted | 0 of 6 | 3 of 6 | 6 of 6 | 6 of 6 | 6 of 6 |
| 60 | 3 of 3 | 6 of 6 | not counted | 6 of 6 | 6 of 6 | 6 of 6 | 6 of 6 | 6 of 6 |
| 150 | 3 of 3 | 4 of 6 | not counted | 6 of 6 | 6 of 6 | 6 of 6 | 6 of 6 | 6 of 6 |

### The full table

Fractions of 200 draws, in %: NRS / 2F / NS. Medians over the draws: P's fitted δ, δ's 90% lower bound, P's fitted b. Edge: draws with b's point fit at an edge. At round 5's six timed points, round 5's generating share is given in brackets.

| # | Δ0 kHz | τ µs | δ kHz | b | role | generating | NRS/2F/NS | ≥ 80% | median P δ kHz | median δ lower bound kHz | median P b | edge draws |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 40 | 15 | 0 |  | counted | NO RESOLVED SPLIT | 100/0/0 | yes | 30.9 | 22.1 | 0.93 | 156 |
| 1 | 40 | 15 | 3 | 0.5 | counted | NO RESOLVED SPLIT | 100/0/0 | yes | 3.8 | 2.8 | 0.53 | 17 |
| 2 | 40 | 15 | 3 | 0.37 | counted | NO RESOLVED SPLIT | 99.5/0/0.5 | yes | 3.8 | 2.8 | 0.38 | 25 |
| 3 | 40 | 15 | 5 | 0.5 | boundary (δ = 5) | either | 91.5/0/8.5 |  | 5.1 | 4.5 | 0.51 | 0 |
| 4 | 40 | 15 | 5 | 0.37 | boundary (δ = 5) | either | 92.5/0/7.5 |  | 5.1 | 4.4 | 0.37 | 0 |
| 5 | 40 | 15 | 8 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/0/100 | **no** | 8.0 | 7.6 | 0.50 | 0 |
| 6 | 40 | 15 | 8 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/0/100 | **no** | 8.0 | 7.5 | 0.37 | 0 |
| 7 | 40 | 15 | 11 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/96/4 | yes | 11.0 | 10.7 | 0.50 | 0 |
| 8 | 40 | 15 | 11 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/48/52 | **no** | 11.0 | 10.6 | 0.37 | 0 |
| 9 | 40 | 15 | 15 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 15.0 | 14.6 | 0.50 | 0 |
| 10 | 40 | 15 | 15 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 15.0 | 14.6 | 0.37 | 0 |
| 11 | 40 | 15 | 30 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 30.0 | 29.5 | 0.50 | 0 |
| 12 | 40 | 15 | 30 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 30.0 | 29.6 | 0.37 | 0 |
| 13 | 40 | 15 | 50 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 50.0 | 49.6 | 0.50 | 0 |
| 14 | 40 | 15 | 50 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 50.0 | 49.6 | 0.37 | 0 |
| 15 | 40 | 60 | 0 |  | counted | NO RESOLVED SPLIT | 100/0/0 | yes | 38.8 | 35.4 | 0.98 | 186 |
| 16 | 40 | 60 | 3 | 0.5 | counted | NO RESOLVED SPLIT | 100/0/0 | yes | 3.0 | 2.8 | 0.50 | 0 |
| 17 | 40 | 60 | 3 | 0.37 | counted | NO RESOLVED SPLIT | 100/0/0 | yes | 3.0 | 2.8 | 0.37 | 0 |
| 18 | 40 | 60 | 5 | 0.5 | boundary (δ = 5) | either | 0/1.5/98.5 |  | 5.0 | 4.9 | 0.50 | 0 |
| 19 | 40 | 60 | 5 | 0.37 | boundary (δ = 5) | either | 0/5/95 |  | 5.0 | 4.9 | 0.37 | 0 |
| 20 | 40 | 60 | 8 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 8.0 | 7.9 | 0.50 | 0 |
| 21 | 40 | 60 | 8 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 8.0 | 7.9 | 0.37 | 0 |
| 22 | 40 | 60 | 11 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 (52) | yes | 11.0 | 10.9 | 0.50 | 0 |
| 23 | 40 | 60 | 11 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 11.0 | 10.9 | 0.37 | 0 |
| 24 | 40 | 60 | 15 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 15.0 | 14.9 | 0.50 | 0 |
| 25 | 40 | 60 | 15 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 15.0 | 14.9 | 0.37 | 0 |
| 26 | 40 | 60 | 30 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 30.0 | 29.9 | 0.50 | 0 |
| 27 | 40 | 60 | 30 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 30.0 | 29.9 | 0.37 | 0 |
| 28 | 40 | 60 | 50 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 50.0 | 49.9 | 0.50 | 0 |
| 29 | 40 | 60 | 50 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 50.0 | 49.9 | 0.37 | 0 |
| 30 | 40 | 150 | 0 |  | counted | NO RESOLVED SPLIT | 100/0/0 | yes | 38.4 | 36.3 | 0.95 | 192 |
| 31 | 40 | 150 | 3 | 0.5 | counted | NO RESOLVED SPLIT | 86.5/0/13.5 | yes | 3.0 | 2.9 | 0.50 | 0 |
| 32 | 40 | 150 | 3 | 0.37 | counted | NO RESOLVED SPLIT | 97.5/0/2.5 | yes | 3.0 | 2.9 | 0.37 | 0 |
| 33 | 40 | 150 | 5 | 0.5 | boundary (δ = 5) | either | 0/1.5/98.5 |  | 5.0 | 5.0 | 0.50 | 0 |
| 34 | 40 | 150 | 5 | 0.37 | boundary (δ = 5) | either | 0/1/99 |  | 5.0 | 4.9 | 0.37 | 0 |
| 35 | 40 | 150 | 8 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 8.0 | 7.9 | 0.50 | 0 |
| 36 | 40 | 150 | 8 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 8.0 | 7.9 | 0.37 | 0 |
| 37 | 40 | 150 | 11 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 11.0 | 10.9 | 0.50 | 0 |
| 38 | 40 | 150 | 11 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 11.0 | 10.9 | 0.37 | 0 |
| 39 | 40 | 150 | 15 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 15.0 | 14.9 | 0.50 | 0 |
| 40 | 40 | 150 | 15 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 15.0 | 14.9 | 0.37 | 0 |
| 41 | 40 | 150 | 30 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/97/3 | yes | 30.0 | 29.9 | 0.50 | 0 |
| 42 | 40 | 150 | 30 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/99.5/0.5 | yes | 30.0 | 29.9 | 0.37 | 0 |
| 43 | 40 | 150 | 50 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 (54) | yes | 50.0 | 49.9 | 0.50 | 0 |
| 44 | 40 | 150 | 50 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 50.0 | 49.9 | 0.37 | 0 |
| 45 | 55 | 15 | 0 |  | counted | NO RESOLVED SPLIT | 100/0/0 | yes | 24.5 | 17.1 | 0.84 | 151 |
| 46 | 55 | 15 | 3 | 0.5 | counted | NO RESOLVED SPLIT | 100/0/0 | yes | 3.8 | 3.0 | 0.51 | 30 |
| 47 | 55 | 15 | 3 | 0.37 | counted | NO RESOLVED SPLIT | 100/0/0 | yes | 3.7 | 2.9 | 0.43 | 24 |
| 48 | 55 | 15 | 5 | 0.5 | boundary (δ = 5) | either | 95/0/5 |  | 5.1 | 4.5 | 0.50 | 0 |
| 49 | 55 | 15 | 5 | 0.37 | boundary (δ = 5) | either | 94/0/6 |  | 5.1 | 4.4 | 0.37 | 0 |
| 50 | 55 | 15 | 8 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/0/100 | **no** | 8.0 | 7.6 | 0.50 | 0 |
| 51 | 55 | 15 | 8 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/0/100 | **no** | 8.0 | 7.5 | 0.37 | 0 |
| 52 | 55 | 15 | 11 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/95/5 | yes | 11.0 | 10.6 | 0.50 | 0 |
| 53 | 55 | 15 | 11 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/54/46 | **no** | 11.0 | 10.6 | 0.37 | 0 |
| 54 | 55 | 15 | 15 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 15.0 | 14.6 | 0.50 | 0 |
| 55 | 55 | 15 | 15 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 15.0 | 14.6 | 0.37 | 0 |
| 56 | 55 | 15 | 30 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 30.0 | 29.6 | 0.50 | 0 |
| 57 | 55 | 15 | 30 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 30.0 | 29.5 | 0.37 | 0 |
| 58 | 55 | 15 | 50 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 50.0 | 49.6 | 0.50 | 0 |
| 59 | 55 | 15 | 50 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 50.0 | 49.5 | 0.37 | 0 |
| 60 | 55 | 60 | 0 |  | counted | NO RESOLVED SPLIT | 100/0/0 (24.5) | yes | 25.1 | 22.9 | 0.99 | 184 |
| 61 | 55 | 60 | 3 | 0.5 | counted | NO RESOLVED SPLIT | 100/0/0 | yes | 3.0 | 2.8 | 0.49 | 0 |
| 62 | 55 | 60 | 3 | 0.37 | counted | NO RESOLVED SPLIT | 100/0/0 | yes | 3.0 | 2.8 | 0.37 | 0 |
| 63 | 55 | 60 | 5 | 0.5 | boundary (δ = 5) | either | 0/3.5/96.5 |  | 5.0 | 4.9 | 0.50 | 0 |
| 64 | 55 | 60 | 5 | 0.37 | boundary (δ = 5) | either | 0/3/97 |  | 5.0 | 4.9 | 0.37 | 0 |
| 65 | 55 | 60 | 8 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 8.0 | 7.9 | 0.50 | 0 |
| 66 | 55 | 60 | 8 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 8.0 | 7.9 | 0.37 | 0 |
| 67 | 55 | 60 | 11 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 11.0 | 10.9 | 0.50 | 0 |
| 68 | 55 | 60 | 11 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 11.0 | 10.9 | 0.37 | 0 |
| 69 | 55 | 60 | 15 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 15.0 | 14.9 | 0.50 | 0 |
| 70 | 55 | 60 | 15 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 15.0 | 14.9 | 0.37 | 0 |
| 71 | 55 | 60 | 30 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 30.0 | 29.9 | 0.50 | 0 |
| 72 | 55 | 60 | 30 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 30.0 | 29.9 | 0.37 | 0 |
| 73 | 55 | 60 | 50 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 50.0 | 49.9 | 0.50 | 0 |
| 74 | 55 | 60 | 50 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 50.0 | 49.9 | 0.37 | 0 |
| 75 | 55 | 150 | 0 |  | counted | NO RESOLVED SPLIT | 100/0/0 | yes | 39.9 | 37.0 | 0.99 | 193 |
| 76 | 55 | 150 | 3 | 0.5 | counted | NO RESOLVED SPLIT | 79.5/0/20.5 | **no** | 3.0 | 2.9 | 0.50 | 0 |
| 77 | 55 | 150 | 3 | 0.37 | counted | NO RESOLVED SPLIT | 98/0/2 (76.5) | yes | 3.0 | 2.9 | 0.37 | 0 |
| 78 | 55 | 150 | 5 | 0.5 | boundary (δ = 5) | either | 0/2/98 |  | 5.0 | 5.0 | 0.50 | 0 |
| 79 | 55 | 150 | 5 | 0.37 | boundary (δ = 5) | either | 0/1.5/98.5 |  | 5.0 | 4.9 | 0.37 | 0 |
| 80 | 55 | 150 | 8 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 8.0 | 7.9 | 0.50 | 0 |
| 81 | 55 | 150 | 8 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 8.0 | 7.9 | 0.37 | 0 |
| 82 | 55 | 150 | 11 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 11.0 | 10.9 | 0.50 | 0 |
| 83 | 55 | 150 | 11 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 11.0 | 10.9 | 0.37 | 0 |
| 84 | 55 | 150 | 15 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 15.0 | 14.9 | 0.50 | 0 |
| 85 | 55 | 150 | 15 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 15.0 | 14.9 | 0.37 | 0 |
| 86 | 55 | 150 | 30 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/96.5/3.5 | yes | 30.0 | 30.0 | 0.50 | 0 |
| 87 | 55 | 150 | 30 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/97/3 | yes | 30.0 | 29.9 | 0.37 | 0 |
| 88 | 55 | 150 | 50 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 50.0 | 49.9 | 0.50 | 0 |
| 89 | 55 | 150 | 50 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 50.0 | 49.9 | 0.37 | 0 |
| 90 | 75 | 15 | 0 |  | counted | NO RESOLVED SPLIT | 100/0/0 | yes | 19.9 | 12.7 | 0.93 | 156 |
| 91 | 75 | 15 | 3 | 0.5 | counted | NO RESOLVED SPLIT | 100/0/0 | yes | 3.6 | 2.7 | 0.54 | 22 |
| 92 | 75 | 15 | 3 | 0.37 | counted | NO RESOLVED SPLIT | 100/0/0 | yes | 3.8 | 2.8 | 0.44 | 23 |
| 93 | 75 | 15 | 5 | 0.5 | boundary (δ = 5) | either | 89/0/11 |  | 5.1 | 4.5 | 0.49 | 0 |
| 94 | 75 | 15 | 5 | 0.37 | boundary (δ = 5) | either | 94/0/6 |  | 5.0 | 4.4 | 0.38 | 0 |
| 95 | 75 | 15 | 8 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/0/100 (0) | **no** | 8.0 | 7.6 | 0.50 | 0 |
| 96 | 75 | 15 | 8 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/0/100 | **no** | 8.0 | 7.5 | 0.37 | 0 |
| 97 | 75 | 15 | 11 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/93/7 | yes | 11.0 | 10.6 | 0.50 | 0 |
| 98 | 75 | 15 | 11 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/54/46 | **no** | 11.0 | 10.6 | 0.37 | 0 |
| 99 | 75 | 15 | 15 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 15.0 | 14.6 | 0.50 | 0 |
| 100 | 75 | 15 | 15 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 15.0 | 14.6 | 0.37 | 0 |
| 101 | 75 | 15 | 30 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 30.0 | 29.6 | 0.50 | 0 |
| 102 | 75 | 15 | 30 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 (73.5) | yes | 30.0 | 29.5 | 0.37 | 0 |
| 103 | 75 | 15 | 50 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 50.0 | 49.6 | 0.50 | 0 |
| 104 | 75 | 15 | 50 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 50.0 | 49.5 | 0.37 | 0 |
| 105 | 75 | 60 | 0 |  | counted | NO RESOLVED SPLIT | 100/0/0 | yes | 29.2 | 26.3 | 0.99 | 184 |
| 106 | 75 | 60 | 3 | 0.5 | counted | NO RESOLVED SPLIT | 100/0/0 | yes | 3.0 | 2.8 | 0.50 | 0 |
| 107 | 75 | 60 | 3 | 0.37 | counted | NO RESOLVED SPLIT | 100/0/0 | yes | 3.0 | 2.8 | 0.37 | 0 |
| 108 | 75 | 60 | 5 | 0.5 | boundary (δ = 5) | either | 0/2.5/97.5 |  | 5.0 | 4.9 | 0.50 | 0 |
| 109 | 75 | 60 | 5 | 0.37 | boundary (δ = 5) | either | 0/2.5/97.5 |  | 5.0 | 4.9 | 0.37 | 0 |
| 110 | 75 | 60 | 8 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 8.0 | 7.9 | 0.50 | 0 |
| 111 | 75 | 60 | 8 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 8.0 | 7.9 | 0.37 | 0 |
| 112 | 75 | 60 | 11 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 11.0 | 10.9 | 0.50 | 0 |
| 113 | 75 | 60 | 11 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 11.0 | 10.9 | 0.37 | 0 |
| 114 | 75 | 60 | 15 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 15.0 | 14.9 | 0.50 | 0 |
| 115 | 75 | 60 | 15 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 15.0 | 14.9 | 0.37 | 0 |
| 116 | 75 | 60 | 30 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 30.0 | 29.9 | 0.50 | 0 |
| 117 | 75 | 60 | 30 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 30.0 | 29.9 | 0.37 | 0 |
| 118 | 75 | 60 | 50 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 50.0 | 49.9 | 0.50 | 0 |
| 119 | 75 | 60 | 50 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 50.0 | 49.9 | 0.37 | 0 |
| 120 | 75 | 150 | 0 |  | counted | NO RESOLVED SPLIT | 100/0/0 | yes | 37.1 | 35.0 | 0.99 | 193 |
| 121 | 75 | 150 | 3 | 0.5 | counted | NO RESOLVED SPLIT | 73.5/0/26.5 | **no** | 3.0 | 2.9 | 0.50 | 0 |
| 122 | 75 | 150 | 3 | 0.37 | counted | NO RESOLVED SPLIT | 98/0/2 | yes | 3.0 | 2.9 | 0.37 | 0 |
| 123 | 75 | 150 | 5 | 0.5 | boundary (δ = 5) | either | 0/1.5/98.5 |  | 5.0 | 5.0 | 0.50 | 0 |
| 124 | 75 | 150 | 5 | 0.37 | boundary (δ = 5) | either | 0/1.5/98.5 |  | 5.0 | 4.9 | 0.37 | 0 |
| 125 | 75 | 150 | 8 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 8.0 | 7.9 | 0.50 | 0 |
| 126 | 75 | 150 | 8 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 8.0 | 7.9 | 0.37 | 0 |
| 127 | 75 | 150 | 11 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 11.0 | 10.9 | 0.50 | 0 |
| 128 | 75 | 150 | 11 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 11.0 | 10.9 | 0.37 | 0 |
| 129 | 75 | 150 | 15 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 15.0 | 14.9 | 0.50 | 0 |
| 130 | 75 | 150 | 15 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 15.0 | 14.9 | 0.37 | 0 |
| 131 | 75 | 150 | 30 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 30.0 | 29.9 | 0.50 | 0 |
| 132 | 75 | 150 | 30 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/97/3 | yes | 30.0 | 29.9 | 0.37 | 0 |
| 133 | 75 | 150 | 50 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 50.0 | 49.9 | 0.50 | 0 |
| 134 | 75 | 150 | 50 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | yes | 50.0 | 49.9 | 0.37 | 0 |

### Compact: each cell is NRS / 2F / NS in %, ✓ or ✗ for a counted point at or above 80% or below it

| δ kHz | b | generating | Δ0 40, τ 15 | Δ0 40, τ 60 | Δ0 40, τ 150 | Δ0 55, τ 15 | Δ0 55, τ 60 | Δ0 55, τ 150 | Δ0 75, τ 15 | Δ0 75, τ 60 | Δ0 75, τ 150 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 |  | NO RESOLVED SPLIT | 100/0/0 ✓ | 100/0/0 ✓ | 100/0/0 ✓ | 100/0/0 ✓ | 100/0/0 ✓ | 100/0/0 ✓ | 100/0/0 ✓ | 100/0/0 ✓ | 100/0/0 ✓ |
| 3 | 0.5 | NO RESOLVED SPLIT | 100/0/0 ✓ | 100/0/0 ✓ | 86.5/0/13.5 ✓ | 100/0/0 ✓ | 100/0/0 ✓ | 79.5/0/20.5 ✗ | 100/0/0 ✓ | 100/0/0 ✓ | 73.5/0/26.5 ✗ |
| 3 | 0.37 | NO RESOLVED SPLIT | 99.5/0/0.5 ✓ | 100/0/0 ✓ | 97.5/0/2.5 ✓ | 100/0/0 ✓ | 100/0/0 ✓ | 98/0/2 ✓ | 100/0/0 ✓ | 100/0/0 ✓ | 98/0/2 ✓ |
| 5 | 0.5 | either | 91.5/0/8.5 | 0/1.5/98.5 | 0/1.5/98.5 | 95/0/5 | 0/3.5/96.5 | 0/2/98 | 89/0/11 | 0/2.5/97.5 | 0/1.5/98.5 |
| 5 | 0.37 | either | 92.5/0/7.5 | 0/5/95 | 0/1/99 | 94/0/6 | 0/3/97 | 0/1.5/98.5 | 94/0/6 | 0/2.5/97.5 | 0/1.5/98.5 |
| 8 | 0.5 | TWO FIXED FREQUENCIES | 0/0/100 ✗ | 0/100/0 ✓ | 0/100/0 ✓ | 0/0/100 ✗ | 0/100/0 ✓ | 0/100/0 ✓ | 0/0/100 ✗ | 0/100/0 ✓ | 0/100/0 ✓ |
| 8 | 0.37 | TWO FIXED FREQUENCIES | 0/0/100 ✗ | 0/100/0 ✓ | 0/100/0 ✓ | 0/0/100 ✗ | 0/100/0 ✓ | 0/100/0 ✓ | 0/0/100 ✗ | 0/100/0 ✓ | 0/100/0 ✓ |
| 11 | 0.5 | TWO FIXED FREQUENCIES | 0/96/4 ✓ | 0/100/0 ✓ | 0/100/0 ✓ | 0/95/5 ✓ | 0/100/0 ✓ | 0/100/0 ✓ | 0/93/7 ✓ | 0/100/0 ✓ | 0/100/0 ✓ |
| 11 | 0.37 | TWO FIXED FREQUENCIES | 0/48/52 ✗ | 0/100/0 ✓ | 0/100/0 ✓ | 0/54/46 ✗ | 0/100/0 ✓ | 0/100/0 ✓ | 0/54/46 ✗ | 0/100/0 ✓ | 0/100/0 ✓ |
| 15 | 0.5 | TWO FIXED FREQUENCIES | 0/100/0 ✓ | 0/100/0 ✓ | 0/100/0 ✓ | 0/100/0 ✓ | 0/100/0 ✓ | 0/100/0 ✓ | 0/100/0 ✓ | 0/100/0 ✓ | 0/100/0 ✓ |
| 15 | 0.37 | TWO FIXED FREQUENCIES | 0/100/0 ✓ | 0/100/0 ✓ | 0/100/0 ✓ | 0/100/0 ✓ | 0/100/0 ✓ | 0/100/0 ✓ | 0/100/0 ✓ | 0/100/0 ✓ | 0/100/0 ✓ |
| 30 | 0.5 | TWO FIXED FREQUENCIES | 0/100/0 ✓ | 0/100/0 ✓ | 0/97/3 ✓ | 0/100/0 ✓ | 0/100/0 ✓ | 0/96.5/3.5 ✓ | 0/100/0 ✓ | 0/100/0 ✓ | 0/100/0 ✓ |
| 30 | 0.37 | TWO FIXED FREQUENCIES | 0/100/0 ✓ | 0/100/0 ✓ | 0/99.5/0.5 ✓ | 0/100/0 ✓ | 0/100/0 ✓ | 0/97/3 ✓ | 0/100/0 ✓ | 0/100/0 ✓ | 0/97/3 ✓ |
| 50 | 0.5 | TWO FIXED FREQUENCIES | 0/100/0 ✓ | 0/100/0 ✓ | 0/100/0 ✓ | 0/100/0 ✓ | 0/100/0 ✓ | 0/100/0 ✓ | 0/100/0 ✓ | 0/100/0 ✓ | 0/100/0 ✓ |
| 50 | 0.37 | TWO FIXED FREQUENCIES | 0/100/0 ✓ | 0/100/0 ✓ | 0/100/0 ✓ | 0/100/0 ✓ | 0/100/0 ✓ | 0/100/0 ✓ | 0/100/0 ✓ | 0/100/0 ✓ | 0/100/0 ✓ |

### Failing counted points, by kind

**span (the beat not resolved in the held-out error: P not better by 0.01):** 9 points

- #5 (Δ0 40, τ 15, δ 8, b 0.5; TWO FIXED FREQUENCIES 0%): span (the beat not resolved in the held-out error: P not better by 0.01): P better by 0.01 in 0%, δ lower bound > 5 kHz in 100%, b interval inside in 100%; the draws went NRS 0%, 2F 0%, NS 100%; alias draws 0, edge draws 0
- #6 (Δ0 40, τ 15, δ 8, b 0.37; TWO FIXED FREQUENCIES 0%): span (the beat not resolved in the held-out error: P not better by 0.01): P better by 0.01 in 0%, δ lower bound > 5 kHz in 100%, b interval inside in 100%; the draws went NRS 0%, 2F 0%, NS 100%; alias draws 0, edge draws 0
- #8 (Δ0 40, τ 15, δ 11, b 0.37; TWO FIXED FREQUENCIES 48%): span (the beat not resolved in the held-out error: P not better by 0.01): P better by 0.01 in 48%, δ lower bound > 5 kHz in 100%, b interval inside in 100%; the draws went NRS 0%, 2F 48%, NS 52%; alias draws 0, edge draws 0
- #50 (Δ0 55, τ 15, δ 8, b 0.5; TWO FIXED FREQUENCIES 0%): span (the beat not resolved in the held-out error: P not better by 0.01): P better by 0.01 in 0%, δ lower bound > 5 kHz in 100%, b interval inside in 100%; the draws went NRS 0%, 2F 0%, NS 100%; alias draws 0, edge draws 0
- #51 (Δ0 55, τ 15, δ 8, b 0.37; TWO FIXED FREQUENCIES 0%): span (the beat not resolved in the held-out error: P not better by 0.01): P better by 0.01 in 0%, δ lower bound > 5 kHz in 100%, b interval inside in 100%; the draws went NRS 0%, 2F 0%, NS 100%; alias draws 0, edge draws 0
- #53 (Δ0 55, τ 15, δ 11, b 0.37; TWO FIXED FREQUENCIES 54%): span (the beat not resolved in the held-out error: P not better by 0.01): P better by 0.01 in 54%, δ lower bound > 5 kHz in 100%, b interval inside in 100%; the draws went NRS 0%, 2F 54%, NS 46%; alias draws 0, edge draws 0
- #95 (Δ0 75, τ 15, δ 8, b 0.5; TWO FIXED FREQUENCIES 0%): span (the beat not resolved in the held-out error: P not better by 0.01): P better by 0.01 in 0%, δ lower bound > 5 kHz in 100%, b interval inside in 100%; the draws went NRS 0%, 2F 0%, NS 100%; alias draws 0, edge draws 0
- #96 (Δ0 75, τ 15, δ 8, b 0.37; TWO FIXED FREQUENCIES 0%): span (the beat not resolved in the held-out error: P not better by 0.01): P better by 0.01 in 0%, δ lower bound > 5 kHz in 100%, b interval inside in 100%; the draws went NRS 0%, 2F 0%, NS 100%; alias draws 0, edge draws 0
- #98 (Δ0 75, τ 15, δ 11, b 0.37; TWO FIXED FREQUENCIES 54%): span (the beat not resolved in the held-out error: P not better by 0.01): P better by 0.01 in 54%, δ lower bound > 5 kHz in 100%, b interval inside in 100%; the draws went NRS 0%, 2F 54%, NS 46%; alias draws 0, edge draws 0

**threshold (the split resolved below 5 kHz: S not within 0.01 of P):** 2 points

- #76 (Δ0 55, τ 150, δ 3, b 0.5; NO RESOLVED SPLIT 79.5%): threshold (the split resolved below 5 kHz: S not within 0.01 of P): S within 0.01 in 79.5%, δ lower bound < 5 kHz in 100%, b interval at an edge in 0%; the draws went NRS 79.5%, 2F 0%, NS 20.5%; alias draws 0, edge draws 0
- #121 (Δ0 75, τ 150, δ 3, b 0.5; NO RESOLVED SPLIT 73.5%): threshold (the split resolved below 5 kHz: S not within 0.01 of P): S within 0.01 in 73.5%, δ lower bound < 5 kHz in 100%, b interval at an edge in 0%; the draws went NRS 73.5%, 2F 0%, NS 26.5%; alias draws 0, edge draws 0

### Convergence and cost

starts that failed to converge: {'S': 43275, 'P': 18591, 'refits': 1} of {'S': 1080000, 'P': 1080000, 'refits': 5400000}
CPU: 37.8 h over the points written; 5.05 CPU-s per draw

## Convergence, in words

Starts that failed to converge count least_squares status 0 (the evaluation limit) or an exception. Over the grid:

| fits | failed to converge |
|---|---|
| S starts | 43,275 of 1,080,000 (4.0%) |
| P starts | 18,591 of 1,080,000 (1.7%) |
| refits | 1 of 5,400,000 |

Each fit keeps the best of its forty starts. The fit check, on the same procedure, found 2 misses in 480.

## Beside: each archived run alone, S and P under the new bounds, one quadrature (a reading, no verdict)

Recomputed from the counts first (Kickoffs 47, 48, 49 by `part_b_losses`; 52 by `k52_phase_sweep`): equal to the archive, largest difference 0. The archive holds X only, so each fit is one-quadrature. In X alone, (Δ0, δ, b, φ0) and (−Δ0, δ, 1 − b, −φ0) are the same fringe, so Δ0's sign and the weights' order are not determined. The P starts are version 5.1's, seeded SeedSequence([7676, 9000, run]). The earlier rounds' fits are read from their hand-back folders, unchanged.

| run | points | S: χ² / dof; \|Δ\| kHz, τ µs | P, version 5.1: χ² / dof; Δ0 kHz, δ kHz, b, τ' µs | P, round 5 (old bounds): Δ0, δ, b | T, rounds 2 / 3 / 4: \|Δ0\| kHz, δ kHz, γ /µs, τ' µs |
|---|---|---|---|---|---|
| K47 | 6 | 2.2 / 1; 47.2, 10⁴ (bound) | 2.1 / −1; 2.4, 50.2, 0.46, 10⁴ (A at its bound, 1) | 176.9, 123.5, 0.017 (a line at 300 kHz, outside the new band) | 47.2, 0, 0.44 / 8.96 / 3.16, 10⁴ |
| K48 | 8 | 11.8 / 3; 57.9, 6.96 | 0.74 / 1; −29.7, 50.0, 0.73, 7.5 (A at its bound) | 29.7, 50.0, 0.27: the X-alone mirror, same χ² | 48.5, 23.7, 0.060, 10⁴ in all three (χ² 1.50 / 1) |
| K49 | 8 | 30.2 / 3; 51.7, 4.41 | 0.82 / 1; 38.2, 26.1, 0.25, 10⁴ (bound) | −38.2, 26.1, 0.75: the mirror, same χ² | 20.2 / 21.5 / 20.1, 49.2 / 48.3 / 49.2, 0.109 / 0.106 / 0.109, 3.1·10³ / 99 / 6.1·10³ (χ² 13.9 to 14.0 / 1) |
| K52 | 6 | 3.3 / 1; 175.3, 6.6·10³ | 3.3 / −1; 42.4, 12.2, 0.44, 217 | 270.5, 241.2, 0.78 | 26.1 / 20.3 / 273.1, 100.3 / 75.6 / 14.2, 0.012 / 7.86 / 0.59, 54 / 283 / 2.5·10³ |

- **Kickoffs 48 and 49 land where round 5's P landed,** as the mirror of the same fit. Neither moved under the new bounds, since both fits sat inside the band:
  - K48 is a split of 50.0 kHz with weights 0.27 and 0.73 and the amplitude at its bound, where rounds 2 to 4's telegraph put 23.7 kHz.
  - K49 is a split of 26.1 kHz, where the telegraph put about 49 kHz.
  - With one degree of freedom each, eight points determine neither split under either model, as R5 and the kickoff now say.
- **Kickoff 47 does not determine P** (dof −1). Round 5's P parked a weak line at 300 kHz; the new band forbids that, and P now lands on two near-equal lines at 52.6 and −47.8 kHz with χ² 2.10, against S's single line at 47.2 kHz with χ² 2.16 and two fewer parameters.
- **Kickoff 52 is one wait swept in phase.** No model's frequency is determined there, and S's |Δ| moves with the starts: 271.6 kHz in round 4, 275.7 in round 5, 175.3 here.
- **L-03's files carry no fit of these runs of their own.** The 23.7 kHz split is rounds 2 to 4's telegraph fit, which L-03 reported, as R5 corrects.

## What the test cannot say

- Nothing about qubit 143 itself. These are simulated draws of the kickoff's S and P models with binomial shot noise. There is no drift, no readout error, no telegraph noise and no third line.
- The power check's 200 warm-started refits stand in for the 2,000-draw bootstrap the rule uses on hardware data. The keep verdict is for the design under that substitute.
- A keep on this grid covers its Δ0, τ, δ and b values, and nothing outside them (a b nearer the edges, a τ below 15 µs, a split above 50 kHz).
- Whether R5's bound and weight clauses behave the same on hardware noise is a hardware question.

## Departures, and why

1. **None in the procedure.** Every stage ran as the kickoff and the prompt order: the fit check, the timing, the grid under `nohup`, then the beside fits (20:45:01 to 20:45:31 UTC, after the grid, so as not to share its cores).
2. **The open choices are round 5's, as R5 fixes them:** the 800-start P reference with b in {0.2, 0.4, 0.6, 0.8}, the point order Δ0, τ, δ, b, and the six timing points.
3. **The bootstrap, confirmed:** round 5's script already drew the copies with replacement per wait and per quadrature, then redrew the shots, then refitted P jointly over both quadratures. No line of it changed (item C of the script's docstring).
4. **Reporting records added** (item E of the docstring): each draw's two fitted lines, whether P's fit lies outside the band or within 1 kHz of it, and whether b's point fit or b's interval is at an edge. The fit check also records each P fit's Δ0, δ and b. No verdict reads any of them.
5. **`tables_t7v51.py` was adjusted twice before this report was written.** The first print rounded #76's 79.5% to "80", which read as a pass beside its ✗. Per cent is now shown to the half a fraction of 200 draws can take. The kinds' labels were also renamed to say what each clause means. Neither change touches a count, and the script in the folder is the one whose output is below.
6. **"CPU seconds per draw"** is worker wall time per draw, as rounds 3 to 5 measured it.
7. **The commit:** the branch `findings/k56-k62-peak-placement` still exists (its head is 8063610, with 9b260fb in its history). The run used the same clone at 9b260fb as rounds 1 to 5, with `tests/handback/t7/pretest_t7.py` imported unchanged (its SHA-256 checked against t7's `SHA256SUMS`, no bytecode written).
8. **The script's source:** `power_t7v51.py` is `../t7v5/power_t7v5.py` (SHA-256 bbc06e8c9affbef702cda4bd468a5e7ca98494196dfde490368a15bf8271385b) with version 5.1's changes, each stated in its docstring before any number was computed. It ran every stage at SHA-256 663280741fe5dcb6728e4bca5ef55afc759dac5823225b02981bd88929e4b41a. Round 5's folder is unchanged and still verifies.

## Versions

Python 3.14.8; numpy 2.5.4; scipy 1.18.1; qiskit 2.5.2; qiskit-aer 0.17.2 (installed, not used); manacitra 0.6.0, installed editable from a clone of the repository at 9b260fb5f0537736a3de400eca7cafd043ae815b.

Bounds:

- **S, as version 4's** (`pretest_t7.py`'s): c, A in [0, 1]; τ in [0.5, 10⁴] µs; Δ in [−0.3, 0.3] MHz; φ0 in [0, 2π].
- **P, version 5.1's:** c, A, τ' and φ0 the same; Δ0 in [−0.125, 0.125] MHz; δ in [0, 0.125] MHz; b in [0, 1].

## Files

- `power_t7v51.py`: the script as run (stages `fitcheck`, `time`, `grid`, `beside`).
- `fitcheck-t7v51.json`: step 1, every pair, draw and miss, each P fit's Δ0, δ and b, and the band count.
- `timing-t7v51.json`: step 2, the six points with every draw, the projection, the line and the band and edge counts.
- `results-t7v51.jsonl`: step 3, one line per grid point (135), each with its 200 draws.
- `grid-run-t7v51.json`: the grid's run record (start, end, script hash, points written).
- `tables_t7v51.py`, `keep-t7v51.json`: the keep computation and the tables above, from the JSONL.
- `beside-t7v51.json`: the archived runs' S and P fits under the new bounds, with the recompute and the earlier rounds' fits beside them.
- `SHA256SUMS`: over this folder.

The `t7`, `t7v2`, `t7v3`, `t7v4` and `t7v5` folders still verify against their `SHA256SUMS`.
