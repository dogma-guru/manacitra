# Probe 01: can a qubit wait on Rigetti Cepheus-1-108Q through Amazon Braket

Author: Anish Patel. Prepared with Mantri (main). Written 21 October 2026, after the discovery read of 20 to 21 October.

**What this is.** A probe, not a test. It asks one question the device properties cannot answer: whether a program containing a wait is accepted by this device, and if it runs, whether the wait acts as time. It makes no claim about the qubit, the chip or any model, and nothing in its report is a finding.

**The question in one line.** The properties list no `delay` at any level (gates, OpenQASM operations, pulse functions). Only a submission can say whether a `delay` statement, or a zero-amplitude pulse, is accepted and acts as a wait.

## 1. The hard stops

1. At most **four** quantum tasks, each of **100 shots**, each submitted **once**. No hybrid job, no program set, no simulator run.
2. The `braket.tracking.Tracker` wraps the whole session. Stop if the estimated cost after any task exceeds **$0.40** per task or **$1.50** in total.
3. Stop and report on any error that is not a rejection of the program (a rejection is an answer; a service error is not).
4. Nothing in any file, task name or tag names an account, bucket, key, email or ARN with an account number. Task names and tags carry only `probe-01` and the task's letter.

## 2. The qubit, chosen by a rule

Within ten minutes before the first submission, read the device properties and save them. The probe's qubit is **the qubit with the longest published T2 at that read** (`standardized.oneQubitProperties`, `T2`). Record its T1, T2, readout fidelity and single-qubit RB figure at that read, and their timestamps. (At the last discovery read it was qubit 99: T2 37.3 µs, T1 37.9 µs, readout 0.979.)

**The wait length d** is that qubit's published **T1** at the same read, rounded to the nearest 100 ns, and capped at 60 µs. Record d.

## 3. The tasks, in order

Every task is one circuit on the probe's qubit as a physical qubit, 100 shots, result type Sample (or the default measurement sample). The native gates are `rx` at ±π/2 and ±π, `rz` and `cz`.

- **Task A, the control.** Inside a verbatim box: `rx(pi)` on the qubit; then measure. No wait.
- **Task B, the `delay` statement inside a verbatim box.** The same program with `delay[d] q;` between the `rx(pi)` and the measurement. If Braket or the device rejects the program at creation or at compile, record the full error text and go to Task C.
- **Task C, only if B was rejected: the `delay` statement outside a verbatim box.** The same three lines, no verbatim pragma, the qubit still physical. If rejected, record the error and go to Task D.
- **Task D, only if B and C were rejected: the wait at pulse level.** After the `rx(pi)`, a `cal` block that plays a `constant` waveform of length d and amplitude 0 on the qubit's drive frame (`Transmon_<n>_charge_tx`), then the measurement. The device publishes `supportsLocalPulseElements: false`, so the frame is the published one, not a locally defined one. If rejected, record the error. The probe is then complete with the answer NO at every level tried.

If B runs, C and D are not submitted. If C runs, D is not submitted. The order is fixed so that the cheapest construction is tried first and the probe spends the least it can.

Save for every task, accepted or rejected: the program text as submitted, the task's state history, the full result object, the per-shot measurement array in the order returned, and everything the result carries in `additionalMetadata` (on this provider that may include the compiled native program; if it does, it is the most useful line in the hand-back, because it shows what the wait became).

## 4. The reading

Let p_A be the fraction of ones in Task A, and p_W the fraction of ones in whichever wait task ran (B, C or D). The ratio r = p_W / p_A is read against what a wait of one T1 would do to an excited qubit, about e^(−1) of the control, with these words fixed before the run:

- **ACTS AS TIME:** r < 0.6.
- **NOT AS TIME:** r > 0.85.
- **UNDECIDED:** otherwise.

With 100 shots each, the binomial scatter on each fraction is about 0.05, so these bands are separated by more than their error for a control near 0.95. The reading is reported with the two fractions and their counts, and no other number is read for a word. If no wait task ran, the reading is **NOT ACCEPTED**, with the three error texts.

A second word, on the compiled program if the result carries one: **WAIT PRESENT** if the compiled program contains an instruction that is a wait (a `DELAY`, a zero-amplitude pulse, or an equivalent the runner quotes verbatim), **WAIT ABSENT** if it contains none, **NOT RETURNED** if no compiled program came back.

## 5. What is not read

No T1 is fitted. No cause is named for any figure. No comparison with any other device is made. The qubit's numbers are recorded, not interpreted. The returned shot order is recorded as returned; nothing here depends on it.

## 6. The report

`report-probe-01.md`, in prose and tables with no dashes, with: the pre-submission properties read and the qubit chosen by section 2; d; each task's letter, program, outcome (ran or rejected, with the error verbatim), fractions and counts; the ratio and its word; the compiled-program word with the quoted line; the tracker's cost before, after each task and at the end; the UTC time of every submission and result. Beside it: the raw result files, the programs as submitted, the scripts as run, `SHA256SUMS`, and a redaction log, even if empty.

Then stop and tell the author the hand-back is ready.

## 7. Rules

- Each task is submitted once. A rejected program is not resubmitted with a change; the change is the next lettered task, and only the lettered tasks exist.
- No dashes in prose. None of "proves", "reveals", "kill", "verified" or "benchmark" in the report's prose (a provider's field name is quoted as a field name).
- No vendor or machine ranking.
- Nothing in the report is adopted by its writing.
