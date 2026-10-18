# Test 13: the per-shot read of fez 143's monitor jobs (rule, fixed before the arrays are opened)

Status: draft for the author's review, 18 October 2026. Once approved, this file is hashed, the hash is posted in a public issue, and the file is published unchanged with the read. No job is submitted and no hardware time is used: the test reads the per-shot results of jobs already run, which the provider returns for a completed job by its id.

## 1. The question

The monitor jobs of tests 11 and 12 report no switch within an execution span and a weight that is flat within a span to below shot noise. That reading assumes a repeat is a moment: that a repeat's shots were taken together, one repeat after another, so that the series of repeats is a series in time. The provider's record does not say in what order the shots of a span's circuits ran. If a span's shots run interleaved across its circuits (the first shot of every circuit, then the second, and so on), every repeat averages the same stretch of time and the series of repeats is not a series in time at all.

Test 12's recount found a marker that bears on this: at the antiphase wait 143's two lines give nearly opposite outcomes in the Y quadrature (about 0.96 and 0.04), and the repeat-to-repeat scatter of Y is about half of binomial at 1,000 shots and a fifth of binomial at 500 shots, while X is binomial. The per-shot bit arrays answer the question directly, and this rule fixes how they are read before anyone looks.

Nothing here names a cause for any change on the record. Nothing here changes the verdicts of tests 11 and 12, which stand as their rules define them; what is at stake is what those verdicts mean about time inside a span.

## 2. The jobs

Three jobs on ibm_fez, qubit 143, all complete and all already published with their counts:

| job | test | positions | shots per position | wait |
|---|---|---|---|---|
| `db9t7v424mrc7384ibh0` | 11, job 2 (monitor) | 300 | 1,000 | 5.6 µs |
| `db9t919gv2cc73e61ljg` | 11, job 3 (monitor) | 300 | 1,000 | 5.6 µs |
| `dba168hgv2cc73e6732g` | 12 (short monitor) | 250 | 500 | 5.6 µs |

Beside them, read with no verdict: `db9t6ek24mrc7384i83g` (test 11, job 1, the shuffled design at 1,500 shots), whose waits differ by position.

## 3. The fetch, and what is hashed before anything is read

1. For each job, the runner fetches the result by job id and keeps, for every position, the per-shot bit array of the single classical bit, in the order the provider returns it. If the provider's result carries only counts and no per-shot data for a job, the runner records that and the job is NOT AVAILABLE; the read proceeds on the jobs that are.
2. The arrays are written to one file per job (`shots-t13-<test>-job<n>.npz`, one array per position, 0 and 1, length equal to the shots), with the fetch time in UTC and the provider's result metadata beside it. Each file's SHA-256 is recorded in `shots-t13-hashes-before-analysis.txt` before any script of section 5 runs. The runner opens no array by eye and computes nothing from them before that record exists.
3. The counts recomputed from each array (the number of ones and zeros per position) must equal the counts in the published `counts-t11-job2.json`, `counts-t11-job3.json` and `counts-t12.json` position for position. A mismatch on any position stops the read of that job and is reported as it stands.
4. The execution spans are taken from the published counts files' execution metadata, not fetched again.

The per-shot data are the provider's record. Whether the order in which the provider returns a position's shots is the order in which they ran is exactly what the readings of section 5 test; the rule assumes nothing about it.

## 4. Definitions

For a job, the whole repeats of a span and the straddling repeats are as test 11's and test 12's analyses define them (a repeat is X then Y; a straddling repeat has its two positions in different spans). All readings are per span, on the whole repeats of that span.

The quadrature of record for a job is the one in which the two lines sit farther apart: Y if |sin θ| > |cos θ| for the job's median phase θ, else X. For the three jobs θ is between −2.1 and −1.8 rad, so the quadrature of record is Y; the rule still computes it. The other quadrature is read beside.

For a span with n whole repeats and N shots per position, the bit matrix M has n rows (the repeats' positions in the quadrature of record, in repeat order) and N columns (shot index as returned). p_i is row i's mean, p̄ the mean of the p_i. m_j is column j's mean over the n rows.

## 5. The readings, with their verdict words

**(a) Shared time at equal shot index.** The variance of the m_j over j, divided by what independent shots would give, (1/n)·mean_i p_i(1 − p_i):

- ratio above 3: **SHARED** (at the same shot index, the circuits of the span saw the same state far more often than independence allows);
- ratio below 1.5: **INDEPENDENT** (in the order returned, no shared structure across circuits at equal shot index);
- between: **UNDECIDED**.

INDEPENDENT is a statement about the returned order; if the provider returns shots in an order other than the one they ran in, SHARED structure would be hidden by it, and the rule says so.

**(b) The correlation time of the sweep means.** The autocorrelation of the sequence m_j at lags 1 to 80, and the first lag at which it falls below 1/e of (1 minus the independent-noise share of the lag-0 variance). The lag is converted to seconds by the sweep time, the span's duration divided by N, and reported as the correlation time of the shared state in sweeps and in seconds. Read only when (a) is SHARED and the lag is 3 or more; otherwise reported as "under three sweeps" (under independence the lag is noise, 1 in most trials and up to 21 in the desk check, which is why it is read only under SHARED). The per-row lag-1 autocorrelation in shot order, averaged over rows, is reported beside, with 1/√(nN) as its standard error.

**(c) The scatter check.** The variance of the p_i over i, divided by p̄(1 − p̄)/N, for both quadratures, recomputed from the arrays. It must equal the figure from the counts (test 12's recount: Y 0.22, 0.19, 0.32; X 0.75, 1.17, 0.95), which checks the arrays against the counts a second way. Beside it, the residual prediction if the state were shared: [b·p_u(1 − p_u) + (1 − b)·p_l(1 − p_l)] / [p̄(1 − p̄)], with b the span's weight, p_u and p_l the two lines' values in that quadrature from R0 = 0.4749 and the span's mean phase, reported for comparison and not used in any verdict.

**The verdict of the test** is reading (a)'s word for the quadrature of record, per span, and a job's word is SHARED if every span is SHARED, INDEPENDENT if every span is INDEPENDENT, and MIXED otherwise. Three jobs give three words. Nothing is pooled across jobs.

## 6. What the words mean, fixed now

- **SHARED in every job:** within a span the repeats sample the same time, the monitor's within-span series is not a time series, and the within-span statements of tests 11 and 12 ("no switch within a span", "flat within a span") are true by construction and say nothing about time inside a span. The per-span levels, the level changes at boundaries, the changes across jobs and stamps stand. Reading (b) then gives the first measurement of how long the state holds on the sweep clock.
- **INDEPENDENT in every job:** in the returned order no shared structure is visible; the sub-binomial scatter of Y remains unexplained by this reading and is recorded as open; the within-span statements keep their time reading at the repeat's resolution, with the caveat on returned order stated.
- **MIXED or UNDECIDED anywhere:** reported as it stands; no pooled word.

No outcome changes any published verdict. The outcome changes the prose around them, in a later amendment under its own ruling.

## 7. What is not read

The X quadrature's and job 1's readings are beside, without verdict words. No wait other than the monitor's is read for a verdict. No qubit other than 143. No cause is named for the sharing if it is found: whether the provider interleaves shots, in what pattern, and why, are the provider's to say; this rule reads only what the arrays show.

## 8. The reporting

`report-t13.md` with: the availability of per-shot data per job; the hashes of the arrays before analysis; the counts check per job; the three verdict words with the ratios per span; the correlation times per span where read; the scatter checks; the beside readings; a sentence stating the returned-order caveat. `fits-t13.json` with every number. The arrays themselves are kept in the hand-back folder with their hashes; whether they are published is the author's call (they are large: about 0.3 MB per job as bits, more as text).

## 9. The desk check

`desk-check-t13-mantri.py`, run before the hash on a synthetic span of 49 repeats at 500 shots with lines at 0.96 and 0.04 and b = 0.344: case 1, independent shots; case 2, shots interleaved sweep by sweep with a telegraph state of mean dwell 1 s; case 3, interleaved with dwell 20 ms (under one sweep of 29 ms); case 4, interleaved with dwell 100 ms. Required: case 1 INDEPENDENT in 100 of 100 with no correlation time read; cases 2 to 4 SHARED in 100 of 100 (a dwell shorter than a sweep still shares the state across the circuits that run inside it); case 2's correlation time read in 100 of 100. Mantri's rates (seed 13390): case 1 ratio median 1.00 (0.85 to 1.15), INDEPENDENT 100, 1/e lag 1 (1 to 21), nothing read; case 2 ratio median 40 (25 to 41), SHARED 100, lag-1 autocorrelation 0.77, scatter ratio 0.18, 1/e lag 15 (7 to 62), correlation time read in 100, median 0.43 s; case 3 ratio median 18, SHARED 100, lag-1 0.03, scatter 0.51, 1/e lag 1, nothing read; case 4 ratio median 34, SHARED 100, lag-1 0.44, scatter 0.24, 1/e lag 2 to 3, read in 44 of 100, median 0.087 s. The correlation time of a two-state process with these rates is about 0.45 of the mean dwell (0.45 s for case 2, 0.045 s for case 4, under two sweeps), which is what the check recovers; the rule therefore reports a correlation time, never a dwell.

The runner reruns the desk check after the read and records its rates beside these.
