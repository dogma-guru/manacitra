# Test 7, version 5.1, round 5c on the second machine: the second source. KEPT, as on the main machine

**The question, in one line:** run on a second machine with the same script and seeds, does the version-5.1 power check return the same keep verdict and the same draws as round 5b?

**Verdict from the second machine's draws alone: KEPT. 106 of the 117 counted points return the generating verdict in at least 80% of draws; 88 were needed.** NO RESOLVED SPLIT: 25 of 27 points. TWO FIXED FREQUENCIES: 81 of 90 points. Round 5b on the main machine: the same, 106 of 117 (25 of 27; 81 of 90). No point passes on one machine and fails on the other.

**The comparison:** the verdict fractions are equal at 131 of the 135 points. They differ at 4 points (42, 86, 87 and 132, all at δ = 30 kHz and τ = 150 µs), each by 0.5 or 1.0 percentage points of the 200 draws. Behind them are 8 of the 27,000 draws whose verdict differs between the machines (two of them at point 41, where they cancel). All 8 trace to a fit that converged differently: on one machine, P's best point fit of its 40 starts sits in a distant minimum (χ² 10,614 to 19,473 against 44 to 75 on the other), and that draw returns NOT SETTLED. The second machine's fit is the one that missed in 3 draws, the main machine's in 5.

Run from 2026-10-16 17:08:31 UTC to 2026-10-18 17:26:34 UTC (48.30 h of wall time, one start, no restart) on 3 worker processes, with the script `power_t7v51.py` unchanged (SHA-256 663280741fe5dcb6728e4bca5ef55afc759dac5823225b02981bd88929e4b41a, the file round 5b's fit check and grid ran) and seed root 7676. Nothing went to hardware and no provider was called. Nothing here is adopted; the author reviews.

**Kinds.** The keep verdicts, fractions, counts and differences are computed facts of the two runs' records. The draws are a model's output on simulated data. Where something is a reading after the data, it is labelled as one.

## The machines

| | The second machine (round 5c) | main machine (round 5b) |
|---|---|---|
| platform | macOS 26.6.2, x86_64, Intel i9-9980HK, 8 physical and 16 logical cores | macOS, arm64, 10 cores |
| Python | 3.13.15 | 3.14.8 |
| numpy, scipy, qiskit, manacitra | 2.5.4, 1.18.1, 2.5.2, 0.6.0 | 2.5.4, 1.18.1, 2.5.2, 0.6.0 |
| workers | 3 (the author's instruction, for the power; below) | 10 |
| wall time for the grid | 48.30 h | 3.79 h |

The only version difference is Python's; numpy and scipy, which do the fitting, match. The full environment is in `round5c-environment.txt`.

## The comparison, point for point and draw for draw

`compare_t7v51_round5c.py` read the two result files and nothing else (`compare-t7v51-round5c.json` holds every point and every differing draw).

**Same draws.** The simulated data are the same on both machines: S's χ² on the fit waits agrees to within 5·10⁻⁵ in every one of the 27,000 draws, and no draw has an S χ² gap above 1.

**The 8 draws whose verdict differs** (all traced; none reconciled):

| point | draw | The second machine | main | P's χ², the second machine | P's χ², main | δ's 90% lower bound, the second machine / main (kHz) | b's 90% interval, the second machine / main | the fit that missed |
|---|---|---|---|---|---|---|---|---|
| 41 | 9 | NOT SETTLED | TWO FIXED FREQUENCIES | 16,284.8 | 47.5 | 39.76 / 29.90 | 0.810 to 0.836 / 0.497 to 0.507 | The second machine's |
| 41 | 48 | TWO FIXED FREQUENCIES | NOT SETTLED | 70.7 | 17,730.1 | 29.97 / 80.06 | 0.493 to 0.504 / 0.856 to 0.877 | main's |
| 42 | 53 | TWO FIXED FREQUENCIES | NOT SETTLED | 61.1 | 10,747.9 | 29.92 / 48.61 | 0.369 to 0.382 / 0.916 to 0.933 | main's |
| 86 | 121 | TWO FIXED FREQUENCIES | NOT SETTLED | 59.7 | 19,473.1 | 29.89 / 59.45 | 0.492 to 0.503 / 0.869 to 0.893 | main's |
| 86 | 176 | TWO FIXED FREQUENCIES | NOT SETTLED | 65.8 | 18,623.6 | 29.96 / 79.22 | 0.495 to 0.508 / 0.881 to 0.901 | main's |
| 87 | 60 | NOT SETTLED | TWO FIXED FREQUENCIES | 10,613.6 | 70.4 | 108.31 / 29.91 | 0.905 to 0.927 / 0.365 to 0.377 | The second machine's |
| 87 | 106 | NOT SETTLED | TWO FIXED FREQUENCIES | 10,752.8 | 75.4 | 79.70 / 29.92 | 0.902 to 0.922 / 0.365 to 0.378 | The second machine's |
| 132 | 129 | TWO FIXED FREQUENCIES | NOT SETTLED | 43.5 | 10,865.4 | 29.92 / 57.77 | 0.367 to 0.379 / 0.075 to 0.093 | main's |

The fractions this moves: point 42, TWO FIXED FREQUENCIES +0.5 points on the second machine; point 86, +1.0; point 87, −1.0; point 132, +0.5 (NOT SETTLED by the opposite amount); point 41, zero (one each way). Every one of the five points is a counted TWO FIXED FREQUENCIES point at or above 96% on both machines, so no 80% test moves.

As a reading: the 8 are the same failure on both platforms. In a few draws at δ = 30 kHz and τ = 150 µs, the 40-start procedure's best P fit is a distant minimum: one line on the wrong side of zero, or a split two to three times too wide with b near an edge. Which draws it happens on depends on the floating-point path, which differs between the two platforms. Each machine's own grid carries its share of such draws as NOT SETTLED. The fit check (round 5b: 2 of 480 fits missed) did not sample τ = 150 µs, where all 8 sit.

**Fits that differ without moving a verdict.**

- **P's χ²:** four more points (30, 60, 75 and 120) carry a P χ² gap between 1.4 and 1.9 in some draw, with the verdict the same.
- **Start statuses:** the per-start statuses (a start reaching the evaluation limit or not) differ in 11,076 of the 27,000 draws, without changing the best fit except in the 8 above.
- **Starts that failed to converge:** S 43,220 on the second machine against 43,275 on the main machine, of 1,080,000; P 18,591 on both, of 1,080,000; refits 1 on both, of 5,400,000.

**Held-out errors that differ while the fits agree** (a fact, not traced; a question for Mantri). In 430 draws, S's held-out error differs between the machines by more than 10⁻⁶, by up to 1.4·10⁻³. Across them, S's χ² agrees to within 4·10⁻⁵, its fitted Δ to 0.009 kHz and its τ to 0.004 µs. 393 of the 430 sit at the two points with a line at 125 kHz: points 118 and 133 (Δ0 = 75 kHz, δ = 50 kHz, b = 0.5, τ = 60 and 150 µs). The largest gap is at point 118, draw 4. There S's held-out error is 0.0920 on the second machine against 0.0934 on the main machine, and P's 0.008675 against 0.008629, while S's χ² agrees to 10⁻¹², its Δ to 3·10⁻⁸ kHz, its τ to 10⁻⁶ µs and P's stored values to 10⁻⁸. The fit waits' χ² agree, so the gap lies in the prediction at the held-out waits. The draw records do not store S's c, A and φ0, so the trace stops there. No verdict moved: at points 118 and 133, P beats S on the held-out waits by at least 0.083 in every draw on both machines, eight times the rule's margin.

**The alias and the edge** (round 5b's own lines, counted by its `tables_t7v51.py` on both files):

- **The alias:** 0 of 27,000 draws on either machine have P outside the band, and 0 press against it.
- **The edge:** b's point fit sits at an edge in 1,735 draws on the second machine and 1,736 on the main machine. b's interval reaches an edge in 2,210 and 2,207. All of these draws are at the NO RESOLVED SPLIT points, and all returned NO RESOLVED SPLIT.

## The run on the second machine

**Power.** The machine's adapter negotiated 60 W, less than the grid draws at full load. The day before, on 35 W, the battery had emptied and the machine shut down. On the author's instruction, the run used **3 workers**, not the prompt's 14, until the power is fixed. A battery guard ran beside the grid: every minute it read the battery's signed current and paused workers (SIGSTOP) while the battery discharged, then resumed them (SIGCONT). It signalled only the grid's own workers. A paused draw is delayed, not changed: every draw is fixed by its seed. The guard's three versions, each swapped without touching the grid:

| guard | from (UTC) | hours | share of time at 0 / 1 / 2 / 3 workers | mean workers | why it was replaced |
|---|---|---|---|---|---|
| v1 | 2026-10-16 17:08 | 0.08 | 0 / 100 / 0 / 0% | 1.00 | macOS held the battery at about 80% (0 mA), and v1 probed upward only above 95%, so it would have held one worker for good |
| v2 | 2026-10-16 17:13 | 26.07 | 58.9 / 26.9 / 9.0 / 5.2% | 0.61 | it stepped down two workers at once, so a mild drain at 2 (median −441 mA) sent it to 0 for ten minutes, while 1 worker alone drained in 11 readings only |
| v3 | 2026-10-17 19:17 | 22.16 | 5.3 / 31.7 / 33.5 / 29.5% | 1.87 | (ran to the end; steps down one worker at a time) |

The battery stayed between 71.7% and 76.1% for the whole run. The CPU speed limit read between 98 and 100 at every check.

**Pace.** The first day's poll (2026-10-17 19:15:48 UTC, 26.1 h in) found 36 points written. That pace projected 98 h for the grid. Under guard v3 the remaining 99 points took 22.15 h, and the grid ended at 48.30 h. The second poll (2026-10-19 02:05:34 UTC) found it complete.

**Wall and worker time.** 173,883 s of wall time; one start, no restart, no line dropped. The workers' recorded seconds sum to 144.9 h (19.32 s per draw) against the main machine's 37.8 h (5.05 s per draw). The second machine's figure includes the time each draw spent paused, so it is not a measure of compute.

## What this cannot say

- Nothing about qubit 143; these are simulated draws of the kickoff's models.
- It does not test the hardware design beyond what round 5b's power check says; it repeats that check on another platform.
- It does not say how often the 40-start procedure misses at points other than these; the 8 misses are the ones that changed a verdict on one machine and not the other.

## Departures from the prompt, and why

1. **The script ran inside a wrapper.** `power_t7v51.py` is imported unchanged by `run_t7v51_round5c.py`, which calls its own `grid_points`, `grid_order`, `one_draw`, `summarise_point` and `meta`. The wrapper drops the main machine's twelve-hour line (the prompt: no line applies), uses the second machine's file names (`results-t7v51-round5c.jsonl`, `grid-run-t7v51-round5c.json`) and sets the worker count. The script as written for the main machine would not have run here: it reads round 5b's timing file, stops at twelve hours and fixes 10 workers.
2. **3 workers, not 14,** on the author's instruction of October 16 to limit the processors until the second machine's power is fixed.
3. **The battery guard,** in three versions (above), with the reasons for each swap. Its log is `battery-guard.log`; its summary is `guard-summary-t7v51-round5c.json`.
4. **qiskit pinned to 2.5.2,** the main machine's version; unpinned, pip took 2.6.0, released October 16. qiskit does not enter a draw.
5. **A fresh copy of the repository,** because round 3's copy had been moved to the second machine's Trash on October 16 at the author's request. It was made as a sparse checkout of 9b260fb without the commit's two files named "sealed" (`round5c-environment.txt`).
6. **Step 1's commands:** `free -g` and `top -bn1` do not exist on macOS. `sysctl`, `top -l`, `pmset` and `ioreg` stood in for them.
7. **The close step** (the version-5 run) was done when the prompt was first pasted and is recorded in `tests/handback/t7v5/second-machine-stopped-2026-10-16.md`. SIGINT was ignored by the background job, so SIGTERM stopped it, and its orphaned workers were ended by their process numbers.
8. **The second daily poll** came 30.8 h after the first, not 24 h: it waited on the main machine's clock. The grid had ended 8.6 h before it.
9. **The counting.** The second machine's keep verdict and its own tables were produced by round 5b's `tables_t7v51.py`, run unchanged in a scratch copy of its folder layout with the second machine's file under the name it reads, so round 5b's folder was not touched. Its output is `tables-t7v51-on-round5c-draws.md`. The side-by-side tables below are `tables_t7v51_round5c.py`'s, and agree with round 5b's script on both files.

## Files

- **The script as run:** `power_t7v51.py`.
- **Run control:** `run_t7v51_round5c.py`, `battery_guard.py`, `battery_guard_v2.py`, `battery_guard_v3.py`, `start.sh`, `status.sh`.
- **The results:** `results-t7v51-round5c.jsonl` (135 lines, the per-draw records inside); `grid-run-t7v51-round5c.json` (the run log: meta, order, the one start).
- **The guard's record:** `battery-guard.log`; `guard-summary-t7v51-round5c.json`.
- **The comparison:** `compare_t7v51_round5c.py` and its output `compare-t7v51-round5c.json`.
- **The tables:** `tables_t7v51_round5c.py`; `tables-t7v51-on-round5c-draws.md`.
- **This report and the environment:** this report; `round5c-environment.txt`.
- **The manifest:** `SHA256SUMS` over the folder.

The copy on the second machine is left in place.

## The tables

`tables_t7v51_round5c.py`'s output, as run on the two result files. Fractions are NO RESOLVED SPLIT / TWO FIXED FREQUENCIES / NOT SETTLED, in % of the 200 draws; bold marks the four points whose fractions differ.

- **The second machine (round 5c): KEPT**, 106 of 117 counted points at or above 80% (88 needed); NO RESOLVED SPLIT 25 of 27, TWO FIXED FREQUENCIES 81 of 90.
- **the main machine (round 5b): KEPT**, 106 of 117 counted points at or above 80% (88 needed); NO RESOLVED SPLIT 25 of 27, TWO FIXED FREQUENCIES 81 of 90.

### The pass fraction by δ (counted points at or above 80%; mean share NRS / 2F / NS, % of draws)

| δ kHz | points | generating | The second machine: at or above 80% | main: at or above 80% | The second machine: mean shares | main: mean shares |
|---|---|---|---|---|---|---|
| 0 | 9 | NO RESOLVED SPLIT | 9 of 9 | 9 of 9 | 100/0/0 | 100/0/0 |
| 3 | 18 | NO RESOLVED SPLIT | 16 of 18 | 16 of 18 | 96.2/0/3.8 | 96.2/0/3.8 |
| 5 | 18 | either (boundary) | not counted | not counted | 30.9/1.5/67.6 | 30.9/1.5/67.6 |
| 8 | 18 | TWO FIXED FREQUENCIES | 12 of 18 | 12 of 18 | 0/66.7/33.3 | 0/66.7/33.3 |
| 11 | 18 | TWO FIXED FREQUENCIES | 15 of 18 | 15 of 18 | 0/91.1/8.9 | 0/91.1/8.9 |
| 15 | 18 | TWO FIXED FREQUENCIES | 18 of 18 | 18 of 18 | 0/100/0 | 0/100/0 |
| 30 | 18 | TWO FIXED FREQUENCIES | 18 of 18 | 18 of 18 | 0/99.3/0.7 | 0/99.3/0.7 |
| 50 | 18 | TWO FIXED FREQUENCIES | 18 of 18 | 18 of 18 | 0/100/0 | 0/100/0 |

### The pass fraction by b (counted points with δ > 0; mean share of the generating verdict)

| b | The second machine: at or above 80% | main: at or above 80% | The second machine: mean share | main: mean share |
|---|---|---|---|---|
| 0.5 | 49 of 54 | 49 of 54 | 92.9% | 92.9% |
| 0.37 | 48 of 54 | 48 of 54 | 91.5% | 91.5% |

### The full table over the 135 points (fractions NRS / 2F / NS, % of 200 draws)

| # | Δ0 kHz | τ µs | δ kHz | b | role | generating | The second machine | main | ≥ 80%, the second machine / main | draws differing |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 40 | 15 | 0 |  | counted | NO RESOLVED SPLIT | 100/0/0 | 100/0/0 | yes / yes |  |
| 1 | 40 | 15 | 3 | 0.5 | counted | NO RESOLVED SPLIT | 100/0/0 | 100/0/0 | yes / yes |  |
| 2 | 40 | 15 | 3 | 0.37 | counted | NO RESOLVED SPLIT | 99.5/0/0.5 | 99.5/0/0.5 | yes / yes |  |
| 3 | 40 | 15 | 5 | 0.5 | boundary (δ = 5) | either | 91.5/0/8.5 | 91.5/0/8.5 |  /  |  |
| 4 | 40 | 15 | 5 | 0.37 | boundary (δ = 5) | either | 92.5/0/7.5 | 92.5/0/7.5 |  /  |  |
| 5 | 40 | 15 | 8 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/0/100 | 0/0/100 | **no** / **no** |  |
| 6 | 40 | 15 | 8 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/0/100 | 0/0/100 | **no** / **no** |  |
| 7 | 40 | 15 | 11 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/96/4 | 0/96/4 | yes / yes |  |
| 8 | 40 | 15 | 11 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/48/52 | 0/48/52 | **no** / **no** |  |
| 9 | 40 | 15 | 15 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 10 | 40 | 15 | 15 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 11 | 40 | 15 | 30 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 12 | 40 | 15 | 30 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 13 | 40 | 15 | 50 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 14 | 40 | 15 | 50 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 15 | 40 | 60 | 0 |  | counted | NO RESOLVED SPLIT | 100/0/0 | 100/0/0 | yes / yes |  |
| 16 | 40 | 60 | 3 | 0.5 | counted | NO RESOLVED SPLIT | 100/0/0 | 100/0/0 | yes / yes |  |
| 17 | 40 | 60 | 3 | 0.37 | counted | NO RESOLVED SPLIT | 100/0/0 | 100/0/0 | yes / yes |  |
| 18 | 40 | 60 | 5 | 0.5 | boundary (δ = 5) | either | 0/1.5/98.5 | 0/1.5/98.5 |  /  |  |
| 19 | 40 | 60 | 5 | 0.37 | boundary (δ = 5) | either | 0/5/95 | 0/5/95 |  /  |  |
| 20 | 40 | 60 | 8 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 21 | 40 | 60 | 8 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 22 | 40 | 60 | 11 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 23 | 40 | 60 | 11 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 24 | 40 | 60 | 15 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 25 | 40 | 60 | 15 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 26 | 40 | 60 | 30 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 27 | 40 | 60 | 30 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 28 | 40 | 60 | 50 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 29 | 40 | 60 | 50 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 30 | 40 | 150 | 0 |  | counted | NO RESOLVED SPLIT | 100/0/0 | 100/0/0 | yes / yes |  |
| 31 | 40 | 150 | 3 | 0.5 | counted | NO RESOLVED SPLIT | 86.5/0/13.5 | 86.5/0/13.5 | yes / yes |  |
| 32 | 40 | 150 | 3 | 0.37 | counted | NO RESOLVED SPLIT | 97.5/0/2.5 | 97.5/0/2.5 | yes / yes |  |
| 33 | 40 | 150 | 5 | 0.5 | boundary (δ = 5) | either | 0/1.5/98.5 | 0/1.5/98.5 |  /  |  |
| 34 | 40 | 150 | 5 | 0.37 | boundary (δ = 5) | either | 0/1/99 | 0/1/99 |  /  |  |
| 35 | 40 | 150 | 8 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 36 | 40 | 150 | 8 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 37 | 40 | 150 | 11 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 38 | 40 | 150 | 11 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 39 | 40 | 150 | 15 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 40 | 40 | 150 | 15 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 41 | 40 | 150 | 30 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/97/3 | 0/97/3 | yes / yes | 2 |
| 42 | 40 | 150 | 30 | 0.37 | counted | TWO FIXED FREQUENCIES | **0/100/0** | **0/99.5/0.5** | yes / yes | 1 |
| 43 | 40 | 150 | 50 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 44 | 40 | 150 | 50 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 45 | 55 | 15 | 0 |  | counted | NO RESOLVED SPLIT | 100/0/0 | 100/0/0 | yes / yes |  |
| 46 | 55 | 15 | 3 | 0.5 | counted | NO RESOLVED SPLIT | 100/0/0 | 100/0/0 | yes / yes |  |
| 47 | 55 | 15 | 3 | 0.37 | counted | NO RESOLVED SPLIT | 100/0/0 | 100/0/0 | yes / yes |  |
| 48 | 55 | 15 | 5 | 0.5 | boundary (δ = 5) | either | 95/0/5 | 95/0/5 |  /  |  |
| 49 | 55 | 15 | 5 | 0.37 | boundary (δ = 5) | either | 94/0/6 | 94/0/6 |  /  |  |
| 50 | 55 | 15 | 8 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/0/100 | 0/0/100 | **no** / **no** |  |
| 51 | 55 | 15 | 8 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/0/100 | 0/0/100 | **no** / **no** |  |
| 52 | 55 | 15 | 11 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/95/5 | 0/95/5 | yes / yes |  |
| 53 | 55 | 15 | 11 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/54/46 | 0/54/46 | **no** / **no** |  |
| 54 | 55 | 15 | 15 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 55 | 55 | 15 | 15 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 56 | 55 | 15 | 30 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 57 | 55 | 15 | 30 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 58 | 55 | 15 | 50 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 59 | 55 | 15 | 50 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 60 | 55 | 60 | 0 |  | counted | NO RESOLVED SPLIT | 100/0/0 | 100/0/0 | yes / yes |  |
| 61 | 55 | 60 | 3 | 0.5 | counted | NO RESOLVED SPLIT | 100/0/0 | 100/0/0 | yes / yes |  |
| 62 | 55 | 60 | 3 | 0.37 | counted | NO RESOLVED SPLIT | 100/0/0 | 100/0/0 | yes / yes |  |
| 63 | 55 | 60 | 5 | 0.5 | boundary (δ = 5) | either | 0/3.5/96.5 | 0/3.5/96.5 |  /  |  |
| 64 | 55 | 60 | 5 | 0.37 | boundary (δ = 5) | either | 0/3/97 | 0/3/97 |  /  |  |
| 65 | 55 | 60 | 8 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 66 | 55 | 60 | 8 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 67 | 55 | 60 | 11 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 68 | 55 | 60 | 11 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 69 | 55 | 60 | 15 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 70 | 55 | 60 | 15 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 71 | 55 | 60 | 30 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 72 | 55 | 60 | 30 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 73 | 55 | 60 | 50 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 74 | 55 | 60 | 50 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 75 | 55 | 150 | 0 |  | counted | NO RESOLVED SPLIT | 100/0/0 | 100/0/0 | yes / yes |  |
| 76 | 55 | 150 | 3 | 0.5 | counted | NO RESOLVED SPLIT | 79.5/0/20.5 | 79.5/0/20.5 | **no** / **no** |  |
| 77 | 55 | 150 | 3 | 0.37 | counted | NO RESOLVED SPLIT | 98/0/2 | 98/0/2 | yes / yes |  |
| 78 | 55 | 150 | 5 | 0.5 | boundary (δ = 5) | either | 0/2/98 | 0/2/98 |  /  |  |
| 79 | 55 | 150 | 5 | 0.37 | boundary (δ = 5) | either | 0/1.5/98.5 | 0/1.5/98.5 |  /  |  |
| 80 | 55 | 150 | 8 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 81 | 55 | 150 | 8 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 82 | 55 | 150 | 11 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 83 | 55 | 150 | 11 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 84 | 55 | 150 | 15 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 85 | 55 | 150 | 15 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 86 | 55 | 150 | 30 | 0.5 | counted | TWO FIXED FREQUENCIES | **0/97.5/2.5** | **0/96.5/3.5** | yes / yes | 2 |
| 87 | 55 | 150 | 30 | 0.37 | counted | TWO FIXED FREQUENCIES | **0/96/4** | **0/97/3** | yes / yes | 2 |
| 88 | 55 | 150 | 50 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 89 | 55 | 150 | 50 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 90 | 75 | 15 | 0 |  | counted | NO RESOLVED SPLIT | 100/0/0 | 100/0/0 | yes / yes |  |
| 91 | 75 | 15 | 3 | 0.5 | counted | NO RESOLVED SPLIT | 100/0/0 | 100/0/0 | yes / yes |  |
| 92 | 75 | 15 | 3 | 0.37 | counted | NO RESOLVED SPLIT | 100/0/0 | 100/0/0 | yes / yes |  |
| 93 | 75 | 15 | 5 | 0.5 | boundary (δ = 5) | either | 89/0/11 | 89/0/11 |  /  |  |
| 94 | 75 | 15 | 5 | 0.37 | boundary (δ = 5) | either | 94/0/6 | 94/0/6 |  /  |  |
| 95 | 75 | 15 | 8 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/0/100 | 0/0/100 | **no** / **no** |  |
| 96 | 75 | 15 | 8 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/0/100 | 0/0/100 | **no** / **no** |  |
| 97 | 75 | 15 | 11 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/93/7 | 0/93/7 | yes / yes |  |
| 98 | 75 | 15 | 11 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/54/46 | 0/54/46 | **no** / **no** |  |
| 99 | 75 | 15 | 15 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 100 | 75 | 15 | 15 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 101 | 75 | 15 | 30 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 102 | 75 | 15 | 30 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 103 | 75 | 15 | 50 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 104 | 75 | 15 | 50 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 105 | 75 | 60 | 0 |  | counted | NO RESOLVED SPLIT | 100/0/0 | 100/0/0 | yes / yes |  |
| 106 | 75 | 60 | 3 | 0.5 | counted | NO RESOLVED SPLIT | 100/0/0 | 100/0/0 | yes / yes |  |
| 107 | 75 | 60 | 3 | 0.37 | counted | NO RESOLVED SPLIT | 100/0/0 | 100/0/0 | yes / yes |  |
| 108 | 75 | 60 | 5 | 0.5 | boundary (δ = 5) | either | 0/2.5/97.5 | 0/2.5/97.5 |  /  |  |
| 109 | 75 | 60 | 5 | 0.37 | boundary (δ = 5) | either | 0/2.5/97.5 | 0/2.5/97.5 |  /  |  |
| 110 | 75 | 60 | 8 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 111 | 75 | 60 | 8 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 112 | 75 | 60 | 11 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 113 | 75 | 60 | 11 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 114 | 75 | 60 | 15 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 115 | 75 | 60 | 15 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 116 | 75 | 60 | 30 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 117 | 75 | 60 | 30 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 118 | 75 | 60 | 50 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 119 | 75 | 60 | 50 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 120 | 75 | 150 | 0 |  | counted | NO RESOLVED SPLIT | 100/0/0 | 100/0/0 | yes / yes |  |
| 121 | 75 | 150 | 3 | 0.5 | counted | NO RESOLVED SPLIT | 73.5/0/26.5 | 73.5/0/26.5 | **no** / **no** |  |
| 122 | 75 | 150 | 3 | 0.37 | counted | NO RESOLVED SPLIT | 98/0/2 | 98/0/2 | yes / yes |  |
| 123 | 75 | 150 | 5 | 0.5 | boundary (δ = 5) | either | 0/1.5/98.5 | 0/1.5/98.5 |  /  |  |
| 124 | 75 | 150 | 5 | 0.37 | boundary (δ = 5) | either | 0/1.5/98.5 | 0/1.5/98.5 |  /  |  |
| 125 | 75 | 150 | 8 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 126 | 75 | 150 | 8 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 127 | 75 | 150 | 11 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 128 | 75 | 150 | 11 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 129 | 75 | 150 | 15 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 130 | 75 | 150 | 15 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 131 | 75 | 150 | 30 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 132 | 75 | 150 | 30 | 0.37 | counted | TWO FIXED FREQUENCIES | **0/97.5/2.5** | **0/97/3** | yes / yes | 1 |
| 133 | 75 | 150 | 50 | 0.5 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
| 134 | 75 | 150 | 50 | 0.37 | counted | TWO FIXED FREQUENCIES | 0/100/0 | 0/100/0 | yes / yes |  |
