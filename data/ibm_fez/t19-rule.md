# Test 19: the published readout table of ibm_fez against a measured one, on new dates (rule, fixed before any job is built)

Status: draft for the author's review, 14 November 2026. Once approved, this file is renamed `t19-rule.md`. It is then hashed, the hash is posted in a public issue, and the file is published unchanged with the run.

## 1. The question

On 15 October 2026 a survey job on ibm_fez (Kickoff 62, job 0) measured the readout error of every qubit and set it beside the published value at the stamp in force. The published value sat more than 0.05 above the measured one on 105 of 156 qubits, within 0.01 on 13, and below it by more than 0.01 on one. That count was description. No rule tested it.

This test puts a rule on it. On a new date, and on up to six further dates: does the published readout error of ibm_fez sit above the measured one, and on one side only?

No cause is named for any difference between a published and a measured value.

## 2. The job, one per date

Kickoff 62's survey, unchanged:

- **S0:** every operational qubit of the processor prepared in |0⟩ and measured, with no gate.
- **S1:** X on every operational qubit, then measured.
- **Shots:** 2 circuits, each run as 2 copies of 2,000 shots. The interleaving seed is 1900 plus the date's number (1901 on date 1).
- **Settings:** dynamical decoupling, gate twirling and measurement twirling off; no readout error mitigation.
- A qubit the backend reports as not operational is listed and not read.

On the Open Plan instance, named in the go by its saved name, in the private record only.

**For every date's job:**

- the published stamps of the previous 48 hours, and the window, as test 7's rule states; no job goes in inside ibm_fez's computed calibration window or while the day's cycle is in progress;
- the structural checks, on the circuits as built and on the backend's snapshot: S0 carries no gate and S1 exactly one X on every qubit read; every qubit read is measured into its own bit; the noiseless P(1) is 0 for S0 and 1 for S1;
- the instance's remaining allowance read and recorded, with the UTC time, in the private record;
- the estimate: Kickoff 62's survey as measured, 4 s; with the half-again margin, 6 s; the job is submitted only if that is within the allowance;
- the decision recorded before the build;
- the stamp at build, at submission and after the fetch;
- the published `readout_error`, P(1|0) and P(0|1) of every qubit at the stamp in force at submission, saved before the job is submitted. If a new stamp appears before the job finishes, both tables are saved;
- the result's execution metadata saved with the counts at fetch.

Each date's job is submitted once. A failed, cancelled or refused job is recorded and not resubmitted, and that date reports no word.

## 3. The dates

- **Date 1** is the date of the first go.
- **Each further date needs its own go,** naming its date and the public issue that carries this rule's hash. Mantri's expectations for the series are sealed once, before date 1.
- **At most seven dates.** Every date falls within 14 days of date 1.
- **Each date's job** runs at least 20 hours after the previous date's job, and under a later published stamp.
- **Past midnight.** A go covers a job submitted after 23:59 UTC of its date if the hold is for the day's cycle or the stamp. The wait and its cause are recorded, and the date stays the go's.
- **A date's report is handed back before the next date's go.**

The rule is not changed between dates, whatever a date shows.

## 4. The analysis, per date

For every qubit read:

- **P(1|0)** from S0 and **P(0|1)** from S1, the copies pooled, 4,000 shots each.
- **The measured readout error:** e = (P(1|0) + P(0|1)) / 2, the same average the published `readout_error` is defined as.
- **Its standard error:** se = ½ √(P(1|0)(1 − P(1|0)) / 4,000 + P(0|1)(1 − P(0|1)) / 4,000), floored at 0.0005.
- **The published readout error** p, at the stamp in force at submission.
- **The difference:** d = p − e.

**The class of each qubit:**

| class | condition |
|---|---|
| **PUBLISHED ABOVE** | d > 0.05 and d > 3 se |
| **MEASURED ABOVE** | −d > 0.01 and −d > 3 se |
| **AGREE** | \|d\| at or below the larger of 0.01 and 3 se |
| **BETWEEN** | every other qubit |

The thresholds 0.05 and 0.01 are the ones 15 October's count was stated in.

## 5. The word, per date

With n the number of qubits read:

| word | condition |
|---|---|
| **ONE-SIDED GAP** | PUBLISHED ABOVE on at least a quarter of n, and MEASURED ABOVE on no more than a tenth as many qubits as PUBLISHED ABOVE |
| **TABLE DESCRIBES THE DEVICE** | PUBLISHED ABOVE on fewer than one in twenty of n, and MEASURED ABOVE on fewer than one in twenty of n |
| **MIXED** | otherwise |

If two published tables were in force during the job, the word is computed against each. The date's word is the one at the stamp in force at submission; the other is reported beside it.

## 6. The series

From the second date on, each report restates every date read, its word, and the days the dates span.

| series word | condition |
|---|---|
| **GAP ON EVERY DATE** | every date read is ONE-SIDED GAP |
| **GAP ON NO DATE** | no date read is ONE-SIDED GAP |
| **GAP ON SOME DATES** | otherwise |

- The series word is always given with the number of dates and the days they span, and is not quoted without them.
- The series is called **A WEEK OF DATES** only if it holds at least five dates spanning at least six days. A shorter series is named by its count.
- 15 October is not a date of this series. Its figures are set beside the series, under item 3 below.

## 7. Reported beside the words, not used in them

1. **The chip at a glance,** per date: the median of e and of p; the number of qubits above 0.03 measured, and published.
2. **The per-qubit table,** per date: P(1|0), P(0|1), e, se, p, d and the class.
3. **15 October under this rule:** Kickoff 62's survey and published table, from its published files, classed as section 4 classes them. This changes nothing in Kickoff 62's record.
4. **The same qubits or different ones:** of the qubits PUBLISHED ABOVE on a date, how many were so on each earlier date and on 15 October; the rank correlation of d between each pair of dates.
5. **The table across stamps:** for the 48 hours before each date's job, the number of qubits whose published readout error changed by more than 0.01 between consecutive stamps.
6. **Qubit 143:** its e and p on each date.
7. **The stamps,** the backend list at build, the estimate and the decision. No allowance figure appears in a public file.

## 8. What the words mean, fixed now

Each word means only what sections 4 to 6 compute. A ONE-SIDED GAP says the published values sat above the measured ones on that date under that stamp; it does not say why, and it does not say the device read badly or well. Nothing in a report is adopted by its writing, and the rule is not changed after the data, whatever they show.

## 9. The reporting

The hand-back, per date N:

- `report-t19-dN.md`: the stamps, the estimate and the decision without allowance figures, the counts per class, the word, the series so far, and the items of section 7;
- `survey-t19-dN.json`: the counts with the execution metadata;
- `published-t19-dN.json`: the published table or tables in force;
- `classes-t19-dN.json`;
- `hash-check-t19.md`, once, on date 1, and re-read on each later date;
- the scripts as run;
- `SHA256SUMS`.

Job names and tags carry the test number only. The instance is named by its saved name only, and only in the private record.

## 10. The desk check

The classes and the words are run on synthetic chips of 156 qubits at 4,000 shots per state, 200 chips per case:

1. the published table tracking the measured values within 0.003: TABLE DESCRIBES THE DEVICE on at least 95 percent;
2. 15 October's shape (105 qubits published 0.06 to 0.43 above, 13 within 0.003, 37 between, one below by 0.02): ONE-SIDED GAP on at least 95 percent;
3. half the chip scattered by 0.06 to 0.20 in either direction: MIXED on at least 95 percent;
4. the gap on 30 qubits only: recorded;
5. a table that is another day's measured values, with no lean either way: recorded.

The thresholds are kept only if every required rate is met. A change before the hash is recorded here with its reason.

**Mantri's check before the hash** (15 November 2026, 02:40 UTC; measured values drawn to resemble 15 October's, median 0.0098 with 25 qubits between 0.03 and 0.38, which is a stand-in and a limit of the check): case 1, 200 of 200; case 2, 200 of 200; case 3, 200 of 200; case 4 read MIXED in 200 of 200; case 5 read MIXED in 200 of 200 (medians of 16 qubits PUBLISHED ABOVE and 35 MEASURED ABOVE). No threshold changed.

**The runner's check after the hash** uses Kickoff 62's own measured values as the chip, and is published with the run.
