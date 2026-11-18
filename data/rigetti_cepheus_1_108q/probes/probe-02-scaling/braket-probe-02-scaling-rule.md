# Probe 02: does the pulse-level wait on Cepheus-1-108Q scale with its length

Author: Anish Patel. Prepared with Mantri (main). Written 21 October 2026, after probe 01 (issue 74).

**What this is.** A probe, not a test. Probe 01 showed that a zero-amplitude pulse on the drive frame is accepted and acts as time: an excited qubit read 0.47 after one published T1, against 0.95 with no wait. The compiler emitted that pulse as `NONBLOCKING`. This probe asks two things probe 01 could not: whether twice the wait gives twice the decay, and whether a barrier between the drive frame and the readout frames changes what the measurement waits for. It makes no claim about the qubit, the chip or any model, and nothing in its report is a finding.

## 1. The hard stops

1. At most **four** quantum tasks, each submitted **once**: two of 100 shots and two of 200 shots, as section 3 gives them. No hybrid job, no program set, no simulator run.
2. The `braket.tracking.Tracker` wraps the whole session. Stop if the estimated cost after any task exceeds **$0.40** per task or **$1.50** in total.
3. Stop and report on any error that is not a rejection of a program. A rejection is an answer and is recorded; a refusal by the account's spending limit or by the availability window is not a rejection and is reported before anything else is sent.
4. Nothing in any file, task name or tag names an account, bucket, key, email, ARN with an account number, or any dollar total other than the tracker's figures for this probe. Task names and tags carry only `probe-02` and the task's label.

## 2. The qubit and the wait, by rule

Within ten minutes before the first submission, read the device properties and save them. The qubit is **the one with the longest published T2 at that read**. Record its T1, T2, readout fidelity and single-qubit RB at that read, with `service.updatedAt`.

**d** is that qubit's published T1 at the read, rounded to the nearest 100 ns, capped at 60 µs. The wait of **2d** is written as **two consecutive plays of the d waveform**, so that each waveform is one the device accepted in probe 01, and the report records whether the compiled program carries two pulses or one.

The frames are the published ones: `Transmon_<n>_charge_tx` for the drive, and the readout frames `Transmon_<n>_readout_tx` and `Transmon_<n>_readout_rx`, as the properties name them at the read.

**Read the properties again** when each task's result is fetched, and record the qubit's published T1 and T2 at that time beside the task. The reads cost nothing and let a later reader see whether the figures moved between tasks.

## 3. The tasks, in order, submitted within a few minutes of each other

Every task is one circuit on the qubit as a physical qubit, with `rx(pi)` inside a verbatim box, then the wait (if any) in a `cal` block, then the measurement. The programs are probe 01's Task D with the wait changed.

- **Task A0, no wait, 100 shots.** Probe 01's Task A, re-run on this day so that every comparison is within one session.
- **Task A1, one play of d, 200 shots.** Probe 01's Task D, at 200 shots.
- **Task A2, two plays of d, 100 shots.**
- **Task B1, one play of d followed by a barrier across the drive frame and the two readout frames, 200 shots.** The barrier is written in the `cal` block as `barrier Transmon_<n>_charge_tx, Transmon_<n>_readout_tx, Transmon_<n>_readout_rx;` after the play. If the program is rejected at creation, record the full error text; the probe continues without B1 and the barrier words below read REJECTED.

Submit A0, A1, A2 and B1 in that order without waiting for results, so that all four queue together. A rejected program is not resubmitted with a change.

Save for every task, accepted or rejected: the program text as submitted and its hash, the task's state history, the full result object, the per-shot measurement array in the order returned, and `additionalMetadata` in full, including the compiled program.

## 4. The reading

Let p_0, p_d, p_2d and p_B be the fractions of ones in A0, A1, A2 and B1. Let r1 = p_d / p_0 and r2 = p_2d / p_d. If a wait of d is a wait of its stated length, each extra d multiplies the excited fraction by about e^(−1), so r1 and r2 should both sit near 0.37 (a little above, for the readout floor). The words, fixed before the run:

**On scaling:**

- **SCALES:** r1 < 0.6 and r2 < 0.6.
- **SATURATES:** r1 < 0.6 and r2 > 0.85 (the second d added nothing).
- **NOT AS TIME:** r1 > 0.85.
- **UNDECIDED:** otherwise.

**On the barrier,** if B1 ran: the difference D = p_d − p_B, with its combined binomial standard error s = √(p_d(1−p_d)/200 + p_B(1−p_B)/200).

- **BARRIER ADDS WAIT:** D > 2s.
- **BARRIER CHANGES NOTHING:** |D| < s.
- **UNDECIDED:** otherwise.
- **REJECTED:** if B1 was refused at creation, with the error quoted.

**Beside, no word:** the implied T1 from each pair, d / ln(p_0 / p_d) and d / ln(p_d / p_2d), each with the published T1 at the pre-submission read and at the fetch, reported as numbers and not interpreted; and for each compiled program, the pulse lines quoted verbatim, with the keyword (`NONBLOCKING` or otherwise) and the count of pulses.

## 5. What is not read

No T1 is claimed. No cause is named for any figure, difference, keyword or queue time. No comparison with any other device. The returned shot order is recorded as returned and nothing depends on it.

## 6. The report

`report-probe-02.md`, prose and tables, no dashes: the pre-submission read and the qubit; d; each task's program, outcome, counts and fraction; the properties at each fetch; r1, r2, the scaling word; D, s and the barrier word; the beside numbers; every compiled program's pulse lines; the tracker's cost before, after each task and at the end; the UTC time of every submission, creation, end and fetch. Beside it: the raw result files, the programs as submitted, the scripts as run, `SHA256SUMS`, and a redaction log.

Then stop and tell the author the hand-back is ready.

## 7. Rules

- Each task is submitted once. The only edits are the four labelled programs.
- No dashes in prose. None of "proves", "reveals", "kill", "verified" or "benchmark" in the report's prose (a provider's field name is quoted as a field name).
- No vendor or machine ranking.
- Nothing in the report is adopted by its writing.
