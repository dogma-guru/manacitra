# Kickoff Model 01, version 4 (Sandhi v4): a two-state model on the per-shot record

Date: 18 October 2026. Author: Anish Patel. Prepared with Mantri (main). For: a desk runner with no hardware access, on the desk runner in a fresh session, from the bundle `model-01-bundle-v4-2026-10-18.zip`. No job is submitted anywhere; nothing here touches the public repository, the website or the support ticket. The bundle carries the records of tests 10 to 15 and this kickoff. It carries no output of any earlier model run, and the runner is not given any.

**Why version 4.** Version 3 was set down on 18 October under ruling R2 of Amendment A27. Its weight channels read a span's weight at shot-noise error, as if every shot were an independent look. Test 13 read the per-shot record and found that within an execution span every circuit sees the same state at the same shot index (SHARED), that on ibm_fez qubit 143 the state switches between two levels every few tenths of a second, and that a span's published weight equals the fraction of the span's returned indices in one state (the duty) to within 0.011. Test 15 restated every boundary on the record under the error of a time average of a two-state process and found seventeen of seventeen read boundaries at NO CHANGE. Version 4 models what the per-shot record shows directly: a two-state process on the sweep clock, observed through the circuits of a span.

Three sentences to carry verbatim: "The model is a kinetic description; it names no cause." "The sweep clock is the returned order; seconds are conditional on that order being chronological." "The predictions are the model's, written before the run they predict, and they are what can count against it."

## 0. Rules and conventions

- **Kinds.** Every count, duty, ratio and sweep series computed from the arrays is a computed fact of the record; every rate, interval and probability from a fit is the model's output; the paragraphs of section 7 are readings, labelled. No sentence says why a state changes, why spans share a state, or what the two states are.
- **Words.** No dashes in prose; no "proves", "reveals", "kill", "verified", "benchmark", "pre-registered"; no vendor or machine ranking (the two processors are compared only as records of the same quantities, never as better or worse); no cause named. "Parity" and "defect" do not appear. "Telegraph error" may appear only as the name test 15 gives its error term.
- **The bundle is the only input.** Nothing is fetched. Check every file against the bundle's `SHA256SUMS` first, and every array against the hashes-before-analysis file of the test that fetched it (`t13/shots-t13-hashes-before-analysis.txt`, `t15/shots-t15-hashes-before-analysis.txt`); report both checks. A mismatch stops the use of that file.
- **Numerics.** float64; every seed recorded; every number in the report traceable to a file and a field in the bundle or to a named output file of this run.
- **Where a definition cannot be applied as written,** say so, record every alternative beside, and do not choose by outcome. Where the choice is between a selected subset and the complete eligible set, the complete set is primary.
- **Deliverables,** in a folder `model-01-v4/`: `report-model-01-v4.md`; `data-model-01-v4.json` (section 2's series as fitted, one entry per qubit, job and span); `fits-model-01-v4.json` (section 3); `checks-model-01-v4.json` (section 5); `predictions-model-01-v4.md` and `predictions-model-01-v4.json` (section 6, written last); `score_model_01_v4.py` (section 6.4); the scripts as run; `run.log`; `SHA256SUMS`.

## 1. The data, in the bundle

| folder | test | processor | design | what v4 uses |
|---|---|---|---|---|
| `t11/` | 11 | ibm_fez, 143 | job 1: shuffled waits (test 7's design); jobs 2 and 3: monitor at 5.6 µs (the antiphase wait), X then Y per repeat, 300 positions, 1,000 shots, three spans each | counts files (circuit labels, execution metadata), `fits-t11.json`, `report-t11.md`, `stamps-t11.csv` |
| `t12/` | 12 | ibm_fez, 143 | the short monitor at 5.6 µs, 250 positions, 500 shots | as above |
| `t13/` | 13 | (read only) | the per-shot arrays of test 11 jobs 1 to 3 and test 12, and the read that found SHARED | `shots-t13-*.npz` (one key per position, `pNNN`, shots in returned order, 0 and 1) with `*-meta.json` (the provider's execution spans as returned); `fits-t13.json`; `report-t13.md`; `read_t13.py` |
| `t14/` | 14 | ibm_fez, 143 | the in-phase control: two waits per repeat (5.6 µs antiphase, 11.2 µs in phase), 248 positions, 500 shots; its rule returned NOT USABLE (median antiphase amplitude 0.0758, under the gate of 0.08) | counts, fits, report, stamps |
| `t10/` | 10 | ibm_kingston | the phase monitor, three jobs, sets of 68, 68 and 56 qubits, 300 positions, 1,000 shots | counts (gz), `sets-t10.json`, report, stamps |
| `t15/` | 15 | (read only) | the per-shot arrays of test 10's three jobs, test 11's job 1 and test 14 (multi-qubit arrays are shots by the set's qubits, little-endian clbit order as the meta file states), and the error-model read | `shots-t15-*.npz` and meta; `fits-t15.json` (per span: sharing ratio, threshold, duty, τ_c, switches, dwells, mid-sweep fraction, quarter-span duties, boundary words); `report-t15.md`; `tables-t15.md`; `read_t15.py`; `desk-check-t15-mantri.py` |
| `rules/` | 10 to 15 | | the rules as hashed and published | read for definitions |

Read first, in this order: `report-t13.md` and `report-t15.md` in full; `rules/t13-rule.md` and `rules/t15-rule.md` sections 4 to 6; the reports of tests 11, 12 and 14, sections 1 and the span tables. Span membership per position is the one the test 13 and 15 reads used (their fits files), checked against the meta files' execution spans; any disagreement is reported and the meta files govern.

## 2. The series the model sees

For each job, qubit and span: the **rows** are the whole repeats' positions at one circuit (one wait, one quadrature), as test 13 defines them; the **sweep index** j is the shot index in returned order; the **sweep count** n_j(c) is the number of ones at index j over the rows of circuit c in the span, out of R(c) rows. A monitor span of test 11 has two circuits (X and Y at 5.6 µs); test 12 the same; test 14 four (X and Y at each of two waits); a kingston span one series per qubit per circuit, as test 15 read it.

**Eligible qubit-spans:** every span of tests 11 (jobs 2 and 3), 12 and 14 on 143; every kingston qubit-span that test 15's fits record as SHARED. The kingston qubits test 15 records as INDEPENDENT or NOT SEPARABLE, and test 11's job 1, are read beside (section 4) and not fitted into any rate.

Before any fit, check per span that the rows of one circuit are exchangeable: the scatter of the rows' means against binomial (test 15's within-span check). A span that fails is fitted anyway and flagged.

## 3. The model

### 3.1 Form

Per qubit-span, a two-state Markov chain on the sweep index, states H and L, with switching probabilities per sweep u (L to H) and d (H to L). Given the state at index j, the counts n_j(c) are independent Binomial(R(c), q_H(c)) or Binomial(R(c), q_L(c)) across circuits. Derived: the duty b = u / (u + d); the correlation length in sweeps ℓ = −1 / ln(1 − u − d); the mean dwells 1/d and 1/u in sweeps. The seconds per sweep is the span's duration over its shots per position, and every quantity in seconds is reported as conditional on the returned order being chronological sweeps spaced evenly across the span.

**The emission parameters q_H(c), q_L(c) are shared across the spans of one job** (the circuits are identical across spans; what the record asks is whether the switching moves). The switching (u, d) is fitted per span. A fit with the emissions free per span is reported beside, with the likelihood difference.

Fit by maximum likelihood (forward algorithm, exact), with intervals from a parametric bootstrap of 400 draws per qubit-job (seed recorded); report the posterior state probability series and the decoded path (Viterbi) per span in `data-model-01-v4.json`.

### 3.2 The hierarchy, for 143

Across 143's eligible spans, the span parameters (logit b, ln ℓ) are drawn from a population with a mean per test-day class and a between-span spread σ_b, σ_ℓ. Fit it with each span's bootstrap uncertainty as its within-span error (a normal-normal model on the transformed scale is enough; say which). The question this answers is the one version 3 asked at the wrong error: **is the span-to-span spread of the duty and the correlation length larger than each span's own uncertainty?** Report σ_b and σ_ℓ with intervals, and the same with test 14 excluded. Primary: tests 11 (jobs 2 and 3) and 12; with test 14 beside, labelled as a job whose rule returned NOT USABLE.

### 3.3 Between spans and between jobs

For each adjacent pair of spans of one job and one qubit, and for each adjacent pair of 143's monitor jobs: the likelihood ratio of one (u, d) for both against one each, calibrated by a parametric bootstrap under the shared fit (400 draws), with the differences Δb and Δ ln ℓ and their intervals. No verdict word is attached here; the test 15 boundary word for the same pair is copied beside from `fits-t15.json`.

### 3.4 The returned order at 1,000 shots

Test 15 reported the autocorrelation of the sweep means at lags 490 to 510 for the 1,000-shot jobs, for the question whether the returned order is one sweep order or two interleaved blocks. For every 1,000-shot qubit-span, fit the chain in the returned order (primary) and in the order that interleaves the two halves (0, 500, 1, 501, ...), and report both log-likelihoods. No word.

## 4. Beside, not fitted

- **Test 14's in-phase wait.** If the two levels are in phase at 11.2 µs, the in-phase circuits' emissions should be equal in the two states. Report q_H − q_L at the in-phase wait with its interval, from the joint four-circuit fit. This is the control's own check, as a computed fact; no word.
- **Co-switching on kingston.** For every pair of eligible kingston qubits in one set and one span, the correlation of their decoded state paths at lag 0 and at lags ±1 to ±5 sweeps, against a circular-shift null (200 shifts, seed recorded). Report the table and the count of pairs above the null's 99th percentile. No word, no cause, and no claim that a pair is coupled.
- **Test 11's job 1 and the INDEPENDENT or NOT SEPARABLE kingston qubits:** the sweep-mean series' lag-1 autocorrelation and two-mode check per span, as test 15 defines them, copied or recomputed, labelled.

## 5. The model's own checks

1. **Recovery on the desk.** Simulate spans from the fitted parameters of three 143 spans (the lowest, middle and highest fitted duty) and of one kingston qubit-span, 200 spans each, through the same rows and shot counts; refit; report the bias and the coverage of the 90 percent bootstrap interval for b, ℓ and the emissions. Coverage under 80 percent for any parameter is reported as a limit of the fit and carried into section 6.
2. **The fit against the record.** Per qubit-span: the dwell-time distributions of the decoded path against the chain's geometric dwells (a two-sample test, p reported); the autocorrelation of the sweep means against the chain's prediction at lags 1 to 20; the mid-sweep fraction (test 15's definition) against the chain's prediction. Count the qubit-spans with p under 0.01 on the dwell test; if more than two of 143's spans fail it, say plainly that a two-state Markov chain does not describe 143's record and write the predictions anyway, labelled.
3. **The agreement with test 15.** The fitted duty against test 15's threshold duty, and ℓ in seconds against test 15's τ_c, per span, in one table. Differences are reported, not reconciled.
4. **Leave one job out.** Refit the 143 hierarchy without each of test 11's job 2, test 11's job 3 and test 12 in turn, predict the held-out job's span duties and correlation lengths from the population, and report whether each falls inside its 90 percent predictive interval. This is the only out-of-sample check the record allows before the 20th, and it is reported as such.

## 6. The predictions, written last, for the author to hash before the next run

### 6.1 The run they are for

A third day of test 11's design on ibm_fez qubit 143, planned for 20 October 2026 under test 11's rule as hashed: job 1, test 7's shuffled design; jobs 2 and 3, the monitor at 5.6 µs, X then Y, 300 positions, 1,000 shots, submitted about a minute apart. The spans, their number and their boundaries are the provider's and are not known in advance; every prediction is stated per span or as a count over whatever spans occur, with its interval computed for two, three and four spans per job.

### 6.2 The predictions

From the 143 hierarchy (section 3.2, primary class) and nothing else:

1. **Sharing.** The probability that every monitor span reads SHARED under test 15's sharing ratio (above 3).
2. **The duty per monitor span:** the 90 percent predictive interval for a new span's duty under test 15's threshold definition, and under the model's fitted duty.
3. **The correlation time per monitor span:** the 90 percent predictive interval for test 15's τ_c in sweeps and, conditionally, in seconds; and for the model's ℓ.
4. **The emissions:** the predictive intervals for q_H and q_L at X and at Y, so that a day on which the two levels themselves move is visible apart from a day on which only the duty moves. If the record holds only two days, say how little this interval rests on.
5. **The boundaries:** the expected count and the 90 percent predictive count of boundaries reading NO CHANGE, BETWEEN and CHANGE under test 15's words, over the monitor jobs' boundaries; and the probability that the model's own likelihood ratio (section 3.3) rejects a shared switching at 1 percent at any monitor boundary.
6. **Between the two monitor jobs:** the 90 percent predictive interval for the difference of their job-mean duties.
7. **Job 1 (shuffled).** Its spans' published weights under A26's method, predicted from the population duty through the relation the record shows on 143's monitors (published weight equal to the duty within 0.011), labelled as an assumption about a second estimator that the record has not compared on one job; with the telegraph sd at the population ℓ beside.
8. **The returned order:** whether the 1,000-shot spans favour the returned order or the interleaved order (section 3.4), as a probability if the record supports one, otherwise "not issued" with the reason.

Each prediction carries its interval, the class it comes from, and the number of spans or jobs it rests on.

### 6.3 What would count against the model

Stated before the run, from the model's own intervals:

- For each family of k bets at 90 percent intervals (the span duties, the span correlation times, the emissions), the smallest number of misses whose probability under the model is under 5 percent; that many misses or more counts against the model.
- Any 143 monitor span reading INDEPENDENT or UNDECIDED under test 15's sharing ratio.
- More than one monitor span failing the dwell test of section 5.2 at p under 0.01.
- A boundary reading CHANGE where the model gave CHANGE a probability under 5 percent.

### 6.4 How the predictions will be scored

`score_model_01_v4.py` takes the 20th's per-shot arrays in the bundle's format (one npz per job, keys `pNNN`, with a meta file carrying the execution spans) and the 20th's counts files, computes every predicted quantity by the definitions above and test 15's, and writes the scorecard. It is hashed with the predictions and is run on the 20th's arrays unchanged. Test it on test 11's arrays here and include that output.

## 7. Readings, labelled

One paragraph each, no cause: what the two-state description fits and where it strains (section 5.2); whether the span-to-span spread exceeds the within-span uncertainty, which is version 3's question at the right error; what the co-switching table does and does not show; what the model cannot see (anything faster than one sweep, anything that changes the emissions within a span, any state beyond two).

## 8. What changed from version 3, and why

1. The weight is a duty of a shared two-state process, fitted on the per-shot record; version 3 read span means at shot-noise error (Mantri's error, carried into the record by ruling R2).
2. Within-span weight channels are gone: within a span the design shows every circuit the same state, so no within-span weight event at the repeat clock can be nonzero by construction.
3. Boundary channels are replaced by a likelihood comparison of the switching parameters across spans, with test 15's words beside.
4. The frequency and stamp channels of version 3 are not carried. Version 4 is the state model only; the frame and its moves stay with the tests' rules.
5. A hierarchy across spans asks the version 3 question at the right error.
6. The scorer is written and hashed with the predictions.

No record changed. No rule changed.
