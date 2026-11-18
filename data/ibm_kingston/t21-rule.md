# Test 21: qubits 11 and 95 on ibm_kingston, a scan and two monitors on a faster clock (rule, fixed before any job is built)

Status: draft for the author's review, 16 November 2026. Once approved, this file is renamed `t21-rule.md`. It is then hashed, the hash is posted in a public issue, and the file is published unchanged with the run. Its per-shot read is fixed here too, before any job runs.

## 1. What this test is, and what it is not

In October, qubits 11 and 95 of ibm_kingston each returned TWO FIXED FREQUENCIES under test 7's rule (test 9), and in test 10's monitor jobs both read SHARED in every span under test 15's definitions, with duties near 0.21. Their switching could not be timed: on that design one sweep took about 31 ms, and the correlation time of both qubits read under three sweeps.

This test looks at the same two qubits again, more than four weeks later, on a clock five and three times faster.

1. **Are the two lines still there, and where?** Test 7's scan on both qubits at once, as test 9's job 1 ran it.
2. **Is the state still shared within a sweep?** Two short monitor jobs, read per shot.
3. **Can the switching be timed?** The correlation time, on sweeps of about 6 ms and about 11 ms.

**No model is scored by this test.** The desk model's posted bets are about one qubit of another processor and say nothing here. This run's record may be used to build a later version of a model. It cannot score any model whose bets are posted after it.

No cause is named for any sharing, switching, difference or shape.

## 2. The jobs

**Settings for every job:**

- dynamical decoupling, gate twirling and measurement twirling off;
- no readout error mitigation;
- qubits 11 and 95 together in every circuit, each measured into its own bit; every other qubit idle in |0⟩, with no instruction on it.

Each job is submitted once. A failed, cancelled or refused job is recorded and not resubmitted.

**On the Open Plan instance, named in the go by its saved name, in the private record only.**

- **Job 1, the scan:** test 9's job 1 on the set of these two qubits.
  - For each wait of 0, 1, ..., 63 µs, one X circuit and one Y circuit holding test 7's single-qubit sequence on both qubits, and the two readout circuits: 130 circuits.
  - Each run as 2 copies of 1,500 shots, interleaving seed 21302.
- **Job 2, the fast monitor.** Test 10's circuit form, with each qubit at its own wait: 6 µs on qubit 11 and 20 µs on qubit 95, test 10's waits, fixed. They are not changed by job 1's result; the waits job 1's splits would give are reported beside them.
  - The two readout circuits (measure; X then measure), then 8 repeats of X then Y, then the two readout circuits: **20 positions, 3,200 shots each**, submitted in that order, not interleaved.
- **Job 3, the wide monitor.** The same, with 16 repeats: **36 positions, 1,800 shots each**.
- Each job is built only after the previous job's result is fetched.

**The estimates:**

- job 1: the measured rate per shot of test 9's job 1 times 390,000 shots;
- jobs 2 and 3: test 10's job 1 rate per shot times 64,000 and 64,800 shots;
- each with the half-again margin.

**The allowance, and which job gives way.** The remaining allowance is read and recorded, with the UTC time, before each job, in the private record.

- If, before job 1, the allowance covers all three estimates with their margins, all three run in order.
- If it covers the two monitors with their margins but not the scan as well, **the scan is not run.** That is recorded, and question 1 reports no word.
- If it covers less than both monitors, job 2 runs alone if its own estimate with the margin is covered. Otherwise nothing is submitted and the record says so.
- After the first job, each later job is submitted only if its estimate with the margin is within the allowance read before it.

**For every job:**

- the published stamps of ibm_kingston for the previous 48 hours, and the window, as test 7's rule states; no job goes in inside the computed calibration window or while the day's cycle is in progress. **If the 48 hours hold no stamp at which T1 changed on more than half the qubits, no cycle is in progress and the clause does not hold a job.** The check is made before each job;
- the structural checks, on the circuits as built and on the backend's snapshot: every instruction on qubit 11 or 95; the two qubits do not share an edge; each carries exactly its gate sequence with its own scheduled wait; the noiseless P(1) as each circuit's form requires; the positions in the rule's order;
- the decision recorded before the build;
- the result's execution metadata saved with the counts at fetch;
- after each fetch, the per-shot results fetched as test 15's section 3 states for positions that hold more than one qubit, and every array file's SHA-256 recorded in a hashes-before-analysis file before any reading runs.

**The date.** The go names the UTC date. A job submitted after 23:59 UTC of that date is covered only if the hold is for the day's cycle or the stamp; the wait and its cause are recorded.

## 3. Usable

A qubit is usable in a job if its measured readout error, from that job's own four readout circuits, is at or below 0.03. A qubit that is not usable in a job is reported with its numbers and gets no word from that job.

## 4. The scan (job 1)

For each qubit, test 9's analysis of its job 1 on that qubit's bit, which is test 7's: the same fits, bounds and band; start layouts from seeds 21304 and 21305; the bootstrap of 2,000 draws seeded SeedSequence([21306, qubit]).

- **The verdict, per qubit,** is test 7's table unchanged: NO RESOLVED SPLIT, TWO FIXED FREQUENCIES, NOT SETTLED.
- **The word, per qubit:** CONFIRMED ON A LATER DATE if TWO FIXED FREQUENCIES, else NOT CONFIRMED ON A LATER DATE.
- **Beside,** October's readings from test 9: qubit 11, δ 41.05 kHz (40.91 to 41.21) and b 0.881 (0.873 to 0.890); qubit 95, δ 12.67 kHz (12.43 to 12.92) and b 0.061 (0.050 to 0.073). Differences are reported, not reconciled.
- **Beside,** the wait at which each qubit's two lines would be in antiphase on this date.

## 5. The per-shot read of the monitors (jobs 2 and 3)

The read uses the package's own functions (`sharing_ratio`, `two_state_reading`, `time_average_sd`, `boundary_ratio`). Its sharing words are this test's own. Test 15's thresholds were set for spans of about 49 rows and do not carry to 8 or 16.

**The layout.**

- The spans are the execution record's. If a span holds whole positions, its rows are the whole repeats inside it. If a span holds a slice of the shots of every position, its series is that slice of every row. Any other layout is recorded, and the job's read reports no word.
- For a qubit, a quadrature and a span: the bit matrix has one row per whole repeat and one column per shot index as returned; m_j is column j's mean; the sweep time is the span's duration over its shots per position.
- **The quadrature of record,** per qubit and per job, is the one of X and Y whose rows give the larger sharing ratio over the whole job.

**The sharing word, per qubit and per span.**

- The ratio, from `sharing_ratio`.
- **The shared share:** (ratio − 1) divided by (rows − 1).
- **The permutation null:** the ratio recomputed 200 times with each row's shot order permuted independently, seed 21401.

| word | condition |
|---|---|
| **SHARED** | the ratio lies above all 200 permuted ratios, and the shared share is at least 0.05 |
| **NO SHARED STATE SEEN** | the ratio lies at or below the 95th percentile of the permuted ratios |
| **UNDECIDED** | otherwise |

NO SHARED STATE SEEN does not say the shots are independent of each other in time. A qubit with one line, or with two lines that do not separate in either quadrature at its wait, reads this way whatever the shot order.

**The timing word, for a SHARED span.** From `two_state_reading`, with the correlation lag as test 13's reading (b) defines it:

| word | condition |
|---|---|
| **TIMED** | the lag is 3 sweeps or more |
| **FASTER THAN THE CLOCK** | the lag is under 3 sweeps |

For a TIMED span, τ_c is the lag times the sweep time. For a span that is FASTER THAN THE CLOCK, three sweeps is reported as a ceiling.

**The duty, for a SHARED span.**

- **The separation:** with each sweep assigned to a state by the span's threshold, the mean outcome of the rows in the high state less that in the low state.
- **The duty is read** only if the separation is at least 0.55. It is then the fraction of the series in the high state, never folded, with its error as a time average from `time_average_sd`.
- Otherwise the span is marked **DUTY NOT READ**, and the threshold duty is listed beside with no word.

**Between adjacent spans of one job,** where both duties are read: test 15's boundary word, with `boundary_ratio`.

A NO CHANGE is no evidence of a change in the duty under the stationary two-state model; it does not show the duties equal (A27, ruling R3).

**The times are on the sweep clock:** the returned order, in seconds only if it is chronological and even.

## 6. Reported beside the words, not used in them

1. **The emissions:** for each qubit, job and span, the mean outcome of the X rows and of the Y rows in each state, the states assigned by the span's threshold in the quadrature of record.
2. **The scan beside the monitors:** where job 1 returns TWO FIXED FREQUENCIES for a qubit, the positions its P fit gives the two lines in the X and Y plane at the monitor's wait, in `ramsey_xy_fit`'s own convention, set beside the emissions. If this cannot be computed in the package's convention without a new assumption, it is left out and the report says so.
3. **The switches and dwells,** the quarter-span duties and the mid-sweep fraction, as `two_state_reading` returns them.
4. **The two clocks beside each other:** each qubit's τ_c and duty in job 2 and in job 3, and the gap between the two jobs as the execution records give it. No word.
5. **October beside:** test 10's readings of the same qubits under test 15 (duties 0.20 to 0.24; correlation time under three sweeps of 31 ms; dwells of about 0.05 and 0.19 s by the threshold crossings).
6. **Readout** of each qubit from each job's readout circuits, beside the published value at the stamp in force.
7. **The stamps,** the backend list at build, the estimates and the decisions. No allowance figure appears in a public file.

## 7. What the words mean, fixed now

Each word means only what sections 4 and 5 compute. TIMED says the correlation of the sweep series outlasted three sweeps on this clock; it does not say the process is a two-state process, or a stationary one. Nothing in the run's report is adopted by its writing, and the rule is not changed after the data, whatever they show.

## 8. The reporting

The hand-back:

- `report-t21.md`: the stamps, estimates and decisions without allowance figures, the scan's fits and words, the spans, the per-shot tables and the items of section 6;
- `fits-t21.json`;
- the counts files with execution metadata;
- the per-shot arrays and their hashes-before-analysis file (not published);
- `hash-check-t21.md`;
- the desk check as the runner ran it;
- the scripts as run;
- `SHA256SUMS`.

Job names and tags carry the test number only. The instance is named by its saved name only, and only in the private record.

## 9. The desk check

The read of section 5 is run on a simulated stationary two-state process, sampled shot by shot in sweep order at test 10's measured time per shot, 100 jobs per case and per layout:

1. **October's dwells (0.050 and 0.187 s), emissions 0.80 and 0.15.** Required on both layouts: SHARED and TIMED on at least 95; τ_c within a factor of 1.5 of the process's own on at least 85; the duty read on at least 95, and within 0.05 of the process's own on at least 85.
2. The same dwells with emissions 0.72 and 0.22: recorded.
3. The same dwells with emissions 0.65 and 0.30: recorded.
4. Twice as fast: recorded.
5. Ten times as fast: recorded.
6. As slow as fez 143: recorded.
7. **One state, no switching.** Required on both layouts: SHARED on no more than 1.
8. A small duty, 0.06 (dwells of 0.012 and 0.187 s): recorded.

The thresholds are kept only if every required rate is met. A change before the hash is recorded here with its reason.

**Mantri's check before the hash** (17 November 2026, 01:30 to 01:40 UTC; `desk-check-t21-mantri.py` and its output are filed beside this rule):

| case | layout | SHARED | TIMED | median lag | τ_c within 1.5 | duty read | duty within 0.05 |
|---|---|---|---|---|---|---|---|
| 1 | job 2 | 100 | 100 | 8 | 97 | 100 | 92 |
| 1 | job 3 | 100 | 100 | 5 | 94 | 100 | 96 |
| 2 | job 2 | 100 | 100 | 8 | 94 | 0 | not read |
| 2 | job 3 | 100 | 100 | 4 | 91 | 0 | not read |
| 3 | job 2 | 100 | 100 | 8 | 89 | 0 | not read |
| 3 | job 3 | 100 | 100 | 4 | 95 | 0 | not read |
| 4 | job 2 | 100 | 100 | 4 | 69 | 100 | 94 |
| 4 | job 3 | 100 | 82 | 3 | 18 | 97 | 95 |
| 5 | job 2 | 100 | 0 | 2 | 0 | 0 | not read |
| 5 | job 3 | 100 | 0 | 1 | 0 | 0 | not read |
| 6 | job 2 | 100 | 100 | 31 | 92 | 100 | 62 |
| 6 | job 3 | 100 | 100 | 17 | 86 | 100 | 55 |
| 7 | job 2 | 0 | 0 | | | | |
| 7 | job 3 | 0 | 0 | | | | |
| 8 | job 2 | 100 | 80 | 3 | 20 | 0 | not read |
| 8 | job 3 | 100 | 2 | 2 | 0 | 0 | not read |

Every required rate is met. What the check shows, as limits of the design:

- **The correlation time reads high.** At October's dwells the read returns a median of 0.051 s on job 2 and 0.057 s on job 3 where the process's own is 0.040 s. The 1/e crossing of a sweep series overstates a short correlation time by about a quarter to a half.
- **The wide monitor is near its floor at twice October's speed** (case 4: a lag of 3, and τ_c within the factor on 18 of 100). The fast monitor is the clock; the wide monitor is the better read of the duty.
- **A process ten times faster is seen and not timed** (case 5: SHARED on every job, FASTER THAN THE CLOCK on every job).
- **In case 6 the duty misses by the process's own scatter,** not by the read: a 20 s job holds about 26 of that process's cycles.
- **Sharing is seen at every emission pair tried; the duty is read only where the states separate** (cases 2 and 3 are marked DUTY NOT READ on every job, as the gate intends).
- **One state:** SHARED on 0 of 100 on both layouts; UNDECIDED on 6 and 7; NO SHARED STATE SEEN on 94 and 93.
- **A duty under one in ten cannot be read by this threshold** (case 8). The threshold sits midway between the 10th and 90th percentiles of the series, and at a duty of 0.06 both lie in one state. The threshold duty then reads near 0.3 to 0.4, which is wrong; the separation falls to about 0.3, and the gate marks every such job DUTY NOT READ. October's scan put qubit 95's weight at 0.061, so this case is a live one.

A first form of this check, with test 15's threshold of 3 on the ratio, read case 1 as SHARED by a margin of a tenth and case 3 as not shared at all. The ratio cannot exceed the row count, so that threshold was dropped for the permutation null before this draft was written.

**The runner's check after the hash** is run with the runner's own code for the read, and is published with the run.
