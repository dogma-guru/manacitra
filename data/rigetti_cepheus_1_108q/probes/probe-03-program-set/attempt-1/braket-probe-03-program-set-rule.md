# Probe 03: what a program-set result carries on Cepheus-1-108Q

Author: Anish Patel. Prepared with Mantri (main). Written 21 October 2026, after probes 01 and 02 (issues 74 and 75).

**What this is.** A probe, not a test. Probes 01 and 02 settled how a wait is written on this route and that it scales. Any larger design on this route runs as program sets, because the task fee is nearly all of the cost otherwise. Three things a design needs are not documented for program sets: whether each executable's result carries its shots one by one, whether the result carries per-executable timing, and whether the executables run one after another or interleaved. This probe submits one small program set and records what comes back. It makes no claim about the qubit, the chip or any model, and nothing in its report is a finding.

## 1. The hard stops

1. **One** quantum task, a program set of **two executables at 100 shots each** (200 shots in total), submitted **once**. No hybrid job, no simulator run, no second task.
2. The `braket.tracking.Tracker` wraps the session. The task's estimated cost must be under **$0.50**; stop if it is not.
3. Stop and report on any error that is not a rejection of the program. A rejection of the program set is an answer and is recorded in full.
4. Nothing in any file, task name or tag names an account, bucket, key, email, ARN with an account number, or the account's spending totals. Tags carry only `probe-03`.

## 2. The qubit and the wait, by rule

Within ten minutes before the submission, read and save the properties. The qubit is **the one with the longest published T2 at that read**; record its T1, T2, readout fidelity and single-qubit RB, with `service.updatedAt`. **d** is its published T1, rounded to the nearest 100 ns, capped at 60 µs. The frames are the published drive and readout frames of that qubit. Read the properties again when the result is fetched.

## 3. The program set

Two programs, both probe 02's construction, so that the two executables have expected outcomes a reader can tell apart:

- **Executable 1:** `rx(pi)` in a verbatim box, one play of the d waveform on the drive frame, a barrier across the drive and the two readout frames, measure. This is probe 02's B1.
- **Executable 2:** the same with two plays of d before the barrier.

Build the program set from the two OpenQASM texts as written (not from SDK circuit objects), submit with `shots=200`, and record how the SDK divides them. If the SDK or the service refuses OpenQASM text, a `cal` block or a verbatim box inside a program set, record the full error. **Do not rewrite the programs to get past a rejection.** The rejection is the answer; stop.

Save: the two program texts and their hashes, the program-set object as serialised, the task's state history, the full result object as returned, every per-executable result object, every `measurements` attribute as returned (type, shape, first ten rows), the task metadata and `additionalMetadata` in full, including any compiled program per executable.

## 4. The reading

Four words, each fixed before the run, each answered from what came back and nothing else:

1. **ACCEPTED** or **REJECTED:** whether the program set was created and ran. If REJECTED, the error text is quoted and the remaining words read NOT APPLICABLE.
2. **PER-SHOT PRESENT** if each executable's result carries an array of 100 rows, one per shot, in returned order; **PER-SHOT ABSENT** if it carries counts or probabilities only; **PARTIAL** if one does and the other does not, or the array is shorter than the shots.
3. **TIMING PRESENT** if the result or its metadata carries a per-executable time (start, end or both); **TIMING ABSENT** if only task-level times exist. Quote the fields.
4. **ORDER STATED** if any returned field or compiled program states whether the executables ran one after the other or interleaved; **ORDER NOT STATED** otherwise. Quote the field.

**Beside, no word:** the fraction of ones in each executable, with probe 02's B1 (0.39) and A2 (0.20) beside them as the single-task values on the same construction; whether the executable with two plays is the one with the lower fraction; each executable's compiled program, with its pulse and fence lines quoted.

## 5. What is not read

No T1 is claimed. No cause is named for any figure or any time. No comparison with any other device. The returned shot order is recorded as returned.

## 6. The report

`report-probe-03.md`, prose and tables, no dashes: the pre-submission read and the qubit; d; the program texts; how the SDK divided the shots; the four words with the fields that decide them; the beside numbers; the compiled programs; the tracker's cost; the UTC times of submission, creation, end and fetch. Beside it: the raw files, the programs as submitted, the scripts as run, `SHA256SUMS`, and a redaction log.

Then stop and tell the author the hand-back is ready.

## 7. Rules

- One task, submitted once. No edit after a rejection.
- No dashes in prose. None of "proves", "reveals", "kill", "verified" or "benchmark" in the report's prose (a provider's field name is quoted as a field name).
- No vendor or machine ranking.
- Nothing in the report is adopted by its writing.
