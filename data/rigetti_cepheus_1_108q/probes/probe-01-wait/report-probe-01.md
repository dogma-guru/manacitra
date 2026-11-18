# Probe 01: the wait on Cepheus-1-108Q, report

Run on 21 October 2026 by Claude Code, the Braket runner, under the rule `braket-probe-01-wait-rule.md` (SHA-256 `1d60b3b1ae8796d47197ea9bd58bb8d4f8fd3b8671aa8cf1a5d4191a49c1afb6`, the hash posted in public issue 74 of `dogma-guru/manacitra`, created 13:46:28 UTC). The author's go named the date, the issue and the words "Mantri's predictions are sealed". No file whose name contains SEALED was read.

This is a probe, not a test. Nothing in this report is a finding, and nothing in it is adopted by its writing.

## 1. The answer in two words

| word | value | from |
|---|---|---|
| Reading (section 4) | **ACTS AS TIME** | r = 0.47 / 0.95 = 0.495, below 0.6 |
| Compiled program (section 4) | **WAIT PRESENT** | a zero amplitude pulse of 30.9 µs in the compiled program, quoted in section 6 |

The wait that ran was Task D, the zero amplitude pulse. Tasks B and C, the `delay` statement inside and outside a verbatim box, were rejected at creation.

## 2. Attempts before the run

The probe was started three times. Only the third produced results. The first two are kept in the hand-back as `attempt-1/` and `attempt-2/`.

| attempt | UTC | what happened | quantum task created | spend |
|---|---|---|---|---|
| 1 | 13:47:40 | Task A refused at creation: `Attempted to spend outside the spending limit time window for the device.` The account's spending limit on this device had a time period of 6 to 8 October. The author changed it to 20 to 22 October. | no | [cost] |
| 2 | 14:05:51 | On the author's override of the availability window rule, Task A was submitted outside a window and sat QUEUED. At the author's request it was cancelled at 14:51:27 (CANCELLED 14:51:32). It never ran. | yes, cancelled while QUEUED | [cost] held as queued spend on the limit, released to [cost] after the cancel |
| 3 | 16:00:33 onward | Run as the runner prompt is written, inside the 16:00 to 23:59 window. | A and D | tracker [cost] |

The author ruled in chat, in words quoted in `go.log`, that Task A could be sent again after attempt 1 and that the probe could restart from the beginning after attempt 2. In attempt 1 the runner's script first filed the spending limit error as a program rejection. That filing was corrected in the attempt's run log, with the original value kept, and the script was changed to stop on every creation error so the runner reads it before the next letter. The script that ran attempt 1 is kept as `scripts/run_probe-as-run-20261021T134740Z.py`. Attempts 2 and 3 ran `scripts/run_probe.py` as it stands in this hand-back. Attempt 3 did not use its `--outside-window` option.

Everything below is attempt 3.

## 3. The pre-submission read and the qubit

The properties were read at **16:00:33 UTC**, one second before Task A was submitted. The properties carry `service.updatedAt` **2026-10-21T15:32:05Z**. The per qubit figures carry no timestamps of their own, so that is the timestamp for each figure below.

| | value |
|---|---|
| Qubit with the longest published T2 | **99** (no tie) |
| T2 | 34.90 µs (3.48978147743928e-05 s) |
| T1 | 30.87 µs (3.086777375838068e-05 s) |
| Readout fidelity (`READOUT`) | 0.984 |
| Single qubit RB (`RANDOMIZED_BENCHMARKING`) | 0.99942 (standard error 1.03e-05) |
| Simultaneous RB (`SIMULTANEOUS_RANDOMIZED_BENCHMARKING`) | 0.99851 (standard error 4.49e-05) |
| Next longest T2 | qubit 90 at 26.04 µs, qubit 7 at 23.90 µs |
| Device status at the read | ONLINE; normal queue 10, priority queue 1 |

**d = 30900 ns**: the T1 above, rounded to the nearest 100 ns. It is under the 60 µs cap, so the cap did not apply. The drive frame is `Transmon_99_charge_tx`, as published.

## 4. The tasks

Each program was filled from its template after the read, hashed and saved, and submitted once with 100 shots and the tags `probe-01` and its letter. In each program `rx(pi)` is written as the Braket SDK writes it, `rx(3.141592653589793)`.

### Task A, the control

```
OPENQASM 3.0;
bit[1] b;
#pragma braket verbatim
box{
rx(3.141592653589793) $99;
}
b[0] = measure $99;
```

SHA-256 `de3530ac214f61e087ac7407a3e2762425178c9f590c5198c276c680f2f2015b`. **Ran.** 95 ones in 100 shots, p_A = 0.95. Measured qubit 99.

### Task B, `delay` inside a verbatim box

```
OPENQASM 3.0;
bit[1] b;
#pragma braket verbatim
box{
rx(3.141592653589793) $99;
delay[30900ns] $99;
}
b[0] = measure $99;
```

SHA-256 `f1b6c190c2c3ed4f773b5371f523d2312e3b836c5fb3aefbe970cf7184b443bb`. **Rejected at creation**, verbatim:

> An error occurred (ValidationException) when calling the CreateQuantumTask operation: [line 6] Function argument '$99' is not defined

Line 6 is the `delay` statement.

### Task C, `delay` outside a verbatim box

```
OPENQASM 3.0;
bit[1] b;
rx(3.141592653589793) $99;
delay[30900ns] $99;
b[0] = measure $99;
```

SHA-256 `7b2f1cf8770eb0d1c54afceea7175649a4393ca7580af755abe81bff8fd4b7ab`. **Rejected at creation**, verbatim:

> An error occurred (ValidationException) when calling the CreateQuantumTask operation: [line 4] Function argument '$99' is not defined

Line 4 is the `delay` statement.

### Task D, the wait at pulse level

```
OPENQASM 3.0;
bit[1] b;
cal {
    waveform wait_d = constant(30900ns, 0.0);
}
#pragma braket verbatim
box{
rx(3.141592653589793) $99;
}
cal {
    play(Transmon_99_charge_tx, wait_d);
}
b[0] = measure $99;
```

SHA-256 `640f4eb75a752688aa5d29a9b3c1ce17d5efcb0ed2bf0aee45196a1ef05bdffa`. **Ran.** 47 ones in 100 shots, p_W = 0.47. Measured qubit 99.

## 5. The reading

| task | ones | shots | fraction of ones |
|---|---|---|---|
| A (control) | 95 | 100 | p_A = 0.95 |
| D (wait) | 47 | 100 | p_W = 0.47 |

r = p_W / p_A = 0.47 / 0.95 = **0.495**. The bands fixed in section 4 of the rule are ACTS AS TIME below 0.6, NOT AS TIME above 0.85, UNDECIDED between. The word is **ACTS AS TIME**. No other number is read for this word.

## 6. The compiled program

The result of each task that ran carries `additionalMetadata.rigettiMetadata.compiledProgram`. Task D's, verbatim:

```
PRAGMA INITIAL_REWIRING "NAIVE"
DECLARE ro BIT[1]
PRAGMA PRESERVE_BLOCK
RX(3.141592653589793) 99
PRAGMA END_PRESERVE_BLOCK
NONBLOCKING PULSE 99 "Transmon-99_charge_tx" flat(duration: 3.09e-05, iq: 0.0 + 0.0*i)
MEASURE 99 ro[0]
```

The quoted line is `NONBLOCKING PULSE 99 "Transmon-99_charge_tx" flat(duration: 3.09e-05, iq: 0.0 + 0.0*i)`: a pulse of 30.9 µs at amplitude zero between the RX and the MEASURE. The word is **WAIT PRESENT**. The line carries the keyword `NONBLOCKING`. The rule's words do not separate a blocking pulse from a nonblocking one, and this report does not read it. Task A's compiled program is the same without that line.

## 7. Cost

Each figure is the `braket.tracking.Tracker` estimate. Tasks C and D were sent from fresh processes after the runner read each rejection, and each fresh process carried forward the total recorded before it.

| point | UTC | tracker total | this task |
|---|---|---|---|
| before Task A | 16:00:33 | [cost] | |
| after Task A | 16:00:48 | [cost] | [cost] |
| after Task B (rejected) | 16:00:49 | [cost] | [cost] |
| after Task C (rejected) | 16:01:16 | [cost] | [cost] |
| after Task D | 19:23:20 | [cost] | [cost] |
| end | 19:23:20 | **[cost]** | |

No hard stop was reached. The highest per task figure was [cost] against [cost], and the total was [cost] against [cost]. The attempt 2 task, cancelled while queued, is not in these figures because its tracker process was stopped before the cancel. The spending limit showed its [cost] as queued spend and then [cost] queued after the cancel.

## 8. Times

| task | submitted | created (service `createdAt`) | ended (service `endedAt`) | result saved |
|---|---|---|---|---|
| A | 16:00:34 | 16:00:37.270 | 16:00:38.426 | 16:00:48 |
| B | 16:00:48 | not created; rejection 16:00:49 | | |
| C | 16:01:15 | not created; rejection 16:01:16 | | |
| D | 16:01:25 | 16:01:27.208 | 19:23:11.932 | 19:23:20 |

Task D was QUEUED from 16:01:27 until it was seen COMPLETED at 19:23:19. It ended 3 hours 22 minutes after Task A ended. No properties were read at the time Task D ran, so the qubit's published figures at that time are not in this hand-back. Section 5 of the rule names no cause for any figure, and none is named here for this interval.

## 9. What is not read

No T1 is fitted. No cause is named for any figure, including the interval between A and D and the `NONBLOCKING` keyword. No comparison with any other device is made, and no device is ranked. The per shot arrays are saved in the order returned (`raw/task-A-measurements.json`, `raw/task-D-measurements.json`), and nothing here depends on that order.

## 10. The hand-back

* `report-probe-01.md`, this file.
* `braket-probe-01-wait-rule.md` and `rule.sha256`.
* `go.log`: the go, the author's rulings quoted, the spending limit readings.
* `run-log.json`, `run.log`: attempt 3's record, including the runner's reading of each rejection.
* `programs/`: the templates written before the go, the filled programs as submitted, and `filled.sha256`.
* `raw/`: the pre-submission properties and device read; for A and D, the full result object, the task metadata, the states seen, the per shot measurements and `additionalMetadata`; for B and C, the error text.
* `attempt-1/`, `attempt-2/`: the same kinds of record for the two earlier attempts.
* `scripts/`: the scripts as run.
* `SHA256SUMS` over the hand-back, then `redaction-log.md`, the final search of every file. `raw-redaction-log.md` is the search made as each raw file was first saved.

Task ARNs, the results bucket and the account number were redacted from every saved file, as the redaction logs record. The device ARN carries no account number and is kept.
