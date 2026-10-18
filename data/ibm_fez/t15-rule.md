# Test 15: the error model of a span's weight, read per shot across the record (rule, fixed before the arrays are opened)

Status: draft for the author's review, 18 October 2026. Once approved, this file is hashed, the hash is posted in a public issue, and the file is published unchanged with the read. No job is submitted and no hardware time is used: the test reads the per-shot results of completed jobs by their ids.

## 1. The question

Test 13 found that within an execution span every circuit sees the same state at the same shot index, that on 143 the state switches between its two lines every few tenths of a second, and that a span's weight is the fraction of time on one line. Every level per span on the record (tests 9 to 12 and 14, A26's span readings, Sandhi's boundary channels) carries an error propagated from binomial shot noise, which is the right noise only when shots sample the state independently. For a shared, slow state the right error of a span's weight is the telegraph's, and the record has not been read with it.

This test fixes the error model and applies it to every monitor job on the record whose per-shot results the provider still returns, so that every weight level change on the record can be restated in units of its own scatter. It also reads the kingston monitor jobs the same way, so that the kingston qubits with two lines get the same treatment as 143. Nothing here changes a published verdict; the verdicts are what their rules computed. What this test gives is the table the next amendment needs.

No cause is named for the switching, the sharing or any change.

## 2. The jobs

Every monitor job on the record, by the job ids in the published counts files:

| job | test | processor | positions | shots | qubits |
|---|---|---|---|---|---|
| test 10, jobs 1 to 3 | the phase monitor | ibm_kingston | 300 each | 1,000 | 68, 68 and 56 (three sets, 192 records) |
| test 11, jobs 2 and 3 | the monitor at 5.6 µs | ibm_fez | 300 each | 1,000 | 143 |
| test 12 | the short monitor | ibm_fez | 250 | 500 | 143 |
| test 14 | the in-phase control | ibm_fez | 248 | 500 | 143 (two waits per repeat) |

Beside them, read without verdict words: test 11's job 1 and test 9's job 2 (the scan), on the readings their designs allow (section 7).

Test 13's arrays for test 11's jobs 2 and 3 and test 12 are reused as fetched and hashed there (`tests/handback/t13/shots-t13-hashes-before-analysis.txt`); they are not fetched again. The others are fetched under section 3.

## 3. The fetch, and what is hashed before anything is read

As test 13's section 3, extended to multi-qubit positions: for a kingston job each position's array is the per-shot bit matrix (shots by the set's qubits, in the published clbit order), stored as 0 and 1. One file per job, the fetch time and the provider's result metadata beside it, the SHA-256 of every array file recorded in `shots-t15-hashes-before-analysis.txt` before any script of section 5 runs. The counts recomputed from each array must equal the published counts position for position (and, for kingston, qubit for qubit); a mismatch stops the read of that job. The spans are taken from the published execution metadata. A job whose per-shot data the provider no longer returns is NOT AVAILABLE and the read proceeds without it.

## 4. Definitions

For a job, a qubit and a span: the whole repeats and the quadrature of record are as test 13 defines them (the quadrature in which |sin θ| or |cos θ| of the qubit's job median phase is larger); the bit matrix M has one row per whole repeat (that quadrature's position) and one column per shot index as returned; m_j is column j's mean; the sweep time is the span's duration over the shots per position.

- **The sharing ratio** (test 13's reading (a)): the variance of m_j over the mean of p_i(1 − p_i) over the rows, divided by the row count. SHARED above 3, INDEPENDENT below 1.5, UNDECIDED between. For a qubit with one line, or lines not separated in the quadrature of record, the ratio is near 1 whatever the shot order, and the word is **NOT SEPARABLE** rather than INDEPENDENT when the qubit's record carries no resolved split (test 10's own record says which); the shot-order question is answered by the separable qubits only.
- **The threshold** between the two states: midway between the 10th and 90th percentiles of m_j. The sweep is in the **high state** when m_j is above it.
- **The duty b:** the fraction of the span's sweeps in the high state, never folded about one half. The weight w of the record corresponds to b or 1 − b by the branch the record published; both are reported.
- **The correlation time τ_c:** the first lag at which the autocorrelation of m_j falls below 1/e of its excess over the shot-noise share of the lag-0 variance (test 13's reading (b)), times the sweep time. Read only for SHARED spans with a lag of 3 or more; otherwise "under three sweeps".
- **The switches and dwells:** the number of threshold crossings of the sweep series; the mean run length in each state, times the sweep time. Reported; the 1,000-shot jobs' counts are marked as inflated where the mid-sweep fraction (section 6) is above 10 percent.
- **The telegraph error of the span's duty:** sd = √(2 b(1 − b) τ_c / T), T the span's duration. For a SHARED span with τ_c under three sweeps, sd is computed at three sweeps and marked as a ceiling.
- **The quarter-span duties:** b over four equal quarters of the span's sweeps, reported as the direct check of the scatter.
- **A boundary word,** for each adjacent pair of spans of one job and one qubit: the difference of the duties over the combined telegraph sd: **NO CHANGE** at or under 2, **BETWEEN** over 2 to 3, **CHANGE** over 3. For the weight published through R0 the same words are given with the published differences over the same combined sd, beside.
- **Between jobs and across stamps,** for 143: the difference of the job-mean duties of adjacent jobs over the combined sd of the job means (each job's sd from its spans in quadrature), the same three words, reported beside; a calibration stamp between two jobs is noted on the row.

## 5. The verdict

There is one verdict word per job: **SHARED** if every separable span is SHARED, **INDEPENDENT** if every separable span is INDEPENDENT, **MIXED** otherwise, **NOT SEPARABLE** if no qubit of the job is separable. And one table, the point of the test: every weight level change on the record that a monitor job carries, restated as its boundary word with the two duties, the combined telegraph sd, the ratio, and the shot-noise ratio the record published beside it.

The counts of the table are the test's result: how many boundaries on the record read CHANGE, BETWEEN and NO CHANGE under the telegraph error, by processor and by job. No word is attached to the counts; the amendment that follows says what they mean.

## 6. Reported beside

- **The mid-sweep fraction** per span: the fraction of sweeps with m_j in the middle fifth between the two lines' values (test 13 found 3 percent at 500 shots and 20 to 26 percent at 1,000 shots on 143).
- **The autocorrelation of m_j at lags 490 to 510** for the 1,000-shot jobs, for the question whether the returned order at 1,000 shots is one sweep order or two interleaved blocks; reported, no word.
- **Test 14's two waits:** the duty and τ_c at the antiphase wait and, at the in-phase wait, the sharing ratio and the sweep-mean series (whose duty should be near one if the two lines are in phase there, which is the control's own check); the in-phase Y scatter above binomial restated per shot.
- **The kingston qubits with two lines** (test 8's and test 9's records name them; 134, 43, 120 at least): their sweep series, duties, τ_c and dwells, beside 143's.
- **τ_c by job and by stamp** for 143, in one table, with the hours between jobs: the question whether the switching rate moves between jobs is put here and not answered.
- **The sensitivity of every boundary word to the threshold** (recomputed at the 20th-to-80th midpoint) and to τ_c (recomputed at the 1/e lag plus and minus one sweep).

## 7. The beside readings of the shuffled and scan jobs

Test 11's job 1 and test 9's job 2 have no repeats of one wait; by the author's ruling for test 13 their readings are per span on the Y positions and separately on the X positions: the sharing ratio (a floor, diluted by the differing waits) and the per-row lag-1 autocorrelation, with no word. For test 9's job 2, whose change points the record placed at the span boundaries, the reading is the same per set, and the report states beside it whether a span's rows differ among themselves by more than shot noise (the within-span scatter of the rows' means against binomial), which is what "the repeats agree within a span up to shot noise" predicts under sharing.

For the shuffled jobs' published weights per span (test 7, test 11's job 1, test 8's and 9's job 1 by A26's method) the telegraph sd is computed with the τ_c of the same qubit's nearest monitor job in time, labelled as borrowed, and the boundary words are given beside with that label.

## 8. What the words mean, fixed now

- A boundary at NO CHANGE under the telegraph error carries no evidence of a change in the duty; the published "level change" at that boundary was the scatter of a time average, whatever its shot-noise ratio.
- A boundary at CHANGE is a change of the duty beyond its own scatter, under the assumption that the process is stationary within each span; the quarter-span duties beside it say whether that assumption looks reasonable there.
- The counts of the table are the finding's; the words of the finding are the next amendment's, under its own ruling.

## 9. The reporting

`report-t15.md` with the availability per job, the hashes before analysis, the counts checks, the verdict word per job, the table of section 5 with its counts, and every beside item; `fits-t15.json` with every number; `hash-check-t15.md`; the scripts as run; `SHA256SUMS`. The arrays stay in the hand-back folder with their hashes and are not published.

## 10. The desk check

`desk-check-t15-mantri.py`, run before the hash on a synthetic span of 49 circuits and 500 sweeps of 28.8 ms (14.4 s) with lines at 0.96 and 0.04, a two-state process generated with duty b and correlation time τ_c, 400 spans per case (seed 15390):

| case | required | Mantri's rates |
|---|---|---|
| b 0.344, τ_c 0.17 s | the empirical sd of the span duty within 15 percent of the formula; τ_c recovered within 15 percent | empirical 0.071, formula 0.073, the rule's median sd 0.073; τ_c 0.173 s |
| b 0.344, τ_c 0.5 s | the same | empirical 0.121, formula 0.125, the rule's median sd 0.113; τ_c 0.432 s (an underestimate of 14 percent, the limit of the 1/e reading at long τ_c) |
| b 0.206, τ_c 0.15 s | the same | empirical 0.059, formula 0.058, median sd 0.060; τ_c 0.144 s |
| b 0.45, τ_c 0.17 s | the same (the duty unfolded) | empirical 0.070, formula 0.076, median sd 0.077; τ_c 0.173 s |
| boundary, no true change | CHANGE in at most 2 percent | NO CHANGE 95.5, BETWEEN 4.0, CHANGE 0.5 |
| boundary, a true change of 0.219 (three single-span sd) | reported | NO CHANGE 59.8, BETWEEN 30.8, CHANGE 9.5 |
| boundary, a true change of 0.137 (test 12's second boundary) | reported | NO CHANGE 74.2, BETWEEN 21.0, CHANGE 4.8 |

The last two rows state the test's resolution plainly: a 14 s span cannot tell a duty change of 0.14 from its own scatter, and a change of 0.22 reads CHANGE in one trial of ten. Longer spans (test 11's 28 s) halve the sd. The runner reruns the desk check after the read and records its rates beside these.
