# Probe 03: what a program-set result carries on Cepheus-1-108Q, report of both attempts

Run on 21 October 2026 by Claude Code, the Braket runner, under the rule `braket-probe-03-program-set-rule.md` (SHA-256 `b9748919eb26918976fbfd4ff0028899294cffbc97975e1cb6167e570811fb27`, the hash posted in public issue 76 of `dogma-guru/manacitra`, created 20:29:34 UTC and not edited since). Attempt 1 ran on the go "Oct 21, issue 76, Mantri's predictions are sealed". Attempt 2 ran under the author's ruling, quoted in the runner prompt for attempt 2, "Yes, let's try one resubmission", which allowed one unchanged resubmission under the same rule and no edit to any program, on the go "Oct 21 2026, Issue 76, "Mantri's predictions are sealed"". The copy of the rule matched the hash in the issue at both goes. No file whose name contains SEALED was read.

This is a probe, not a test. Nothing in this report is a finding, and nothing in it is adopted by its writing. Attempt 1's own report, files and hand-back are kept unchanged under `attempt-1/`.

## 1. The four words

| word | value | from |
|---|---|---|
| 1 | **REJECTED** | at both attempts `CreateQuantumTask` returned `ValidationException`, reason `ProgramSetValidationFailed`; no task was created |
| 2 | NOT APPLICABLE | no result |
| 3 | NOT APPLICABLE | no result |
| 4 | NOT APPLICABLE | no result |

The same bytes were refused twice. The serialised program set at attempt 2 hashed to `7b283c57b488513b9cd0a489d8db53e69df6b88aab8befac3a5fb4e6f5ba89d2`, the hash of attempt 1's `raw/program-set-ir.json`, checked before the call (section 4).

## 2. The two refusals side by side

| | attempt 1 | attempt 2 |
|---|---|---|
| call made (UTC) | 2026-10-21T20:38:21Z | 2026-10-21T21:17:11Z |
| refusal returned (UTC) | 2026-10-21T20:38:45Z | 2026-10-21T21:17:36Z |
| seconds from call to refusal | 24 | 25 |
| tags | `probe-03`: `program-set` | `probe-03`: `program-set`, `attempt-2`: `resubmission` |
| error code | `ValidationException` | `ValidationException` |
| reason | `ProgramSetValidationFailed` | `ProgramSetValidationFailed` |
| program 0 | `["Validation timed out"]` | `["Validation timed out"]` |
| program 1 | `["Validation timed out"]` | `["Validation timed out"]` |
| saved error file, SHA-256 | `ac97c6ef33dd1d5328bbb57afac31734650e9223bfb026fadd2251134cc3b82e` | `ac97c6ef33dd1d5328bbb57afac31734650e9223bfb026fadd2251134cc3b82e` |

**The second error is the same text as the first.** The two saved files (`attempt-1/raw/creation-error.txt` and `raw/creation-error.txt`) are identical byte for byte, and the service's response fields compare equal one by one. The saved files leave out the response's request metadata, so a request identifier, which would differ, is not part of either.

The error, quoted in full (both attempts):

```
"Message": "Validation failed for one or more programs. See 'programSetValidationFailures' for details. First failure:\n{'programIndex': 0, 'errors': ['Validation timed out']}\nRerun the task and catch the exception for more details",
"Code": "ValidationException"
"message": "Validation failed for one or more programs. See 'programSetValidationFailures' for details.",
"reason": "ProgramSetValidationFailed",
"programSetValidationFailures": [
  {"programIndex": 0, "errors": ["Validation timed out"]},
  {"programIndex": 1, "errors": ["Validation timed out"]}
]
```

What the error states and what it does not. It states that validation of each of the two programs timed out. It does not name OpenQASM text, a `cal` block, a verbatim box, a frame, a waveform or any line of either program, and it does not say that any of these is unsupported in a program set. The word REJECTED is the word the runner prompts fix for a refused creation. Whether a validation timeout returned twice for the same bytes is a rejection of the programs, in the sense of rule section 1 item 3, or a service condition present at both times, is not decided by anything that came back.

After attempt 2 a read call (`search_quantum_tasks` on this device, created since 20:30 UTC) returned no task. No task exists from either attempt. No program was rewritten and no further task was submitted.

## 3. Before each submission

| check | attempt 1 | attempt 2 |
|---|---|---|
| spending limit for this device (read only, not changed) | 20:35:41; period covers today; remaining covered [cost] | 21:10:48; the same |
| price list estimate, one task of 200 shots | [cost] | [cost] |
| device and window | 20:35:48; ONLINE; 12251 s left in the 16:00 to 23:59:59 window; queues 0 | 21:10:50; ONLINE; 10149 s left in the same window; queues 0 |
| program set action in the properties | version 1, `maximumExecutables` 100, `maximumTotalShots` 200000 | unchanged |

The account's own spending figures are not recorded in this hand-back.

## 4. The properties, the qubit and the serialised set

At attempt 1 the qubit and d were chosen by rule section 2. At attempt 2 nothing was chosen: the runner prompt fixed the qubit, d and the programs, and the properties were read once before the call for the record only.

| | attempt 1 read | attempt 2 read |
|---|---|---|
| read at (UTC) | 20:38:20 | 21:17:10 |
| `service.updatedAt` | 2026-10-21T20:32:02+00:00 | 2026-10-21T21:02:03+00:00 |
| qubit with the longest published T2 | **99** (no tie) | 99 (recorded only) |
| qubit 99, T2 | 34.90 µs (3.48978147743928e-05 s) | 34.90 µs (3.48978147743928e-05 s) |
| qubit 99, T1 | 30.87 µs (3.086777375838068e-05 s) | 30.87 µs (3.086777375838068e-05 s) |
| qubit 99, readout fidelity (`READOUT`) | 0.982 | 0.982 |
| qubit 99, single qubit RB (`RANDOMIZED_BENCHMARKING`) | 0.99942 (standard error 1.03e-05) | 0.99942 |
| qubit 99, simultaneous RB (`SIMULTANEOUS_RANDOMIZED_BENCHMARKING`) | 0.99851 | not recorded at this read |
| next longest T2 | qubit 90 at 26.04 µs, qubit 7 at 23.90 µs | not recorded |

The per qubit figures carry no timestamps of their own; `service.updatedAt` is the timestamp for each. **d = 30900 ns**, attempt 1's T1 rounded to the nearest 100 ns, under the 60 µs cap. The frames are `Transmon_99_charge_tx` (drive), `Transmon_99_readout_tx` and `Transmon_99_readout_rx` (readout), published at both reads.

The rule asks for a second read of the properties when the result is fetched. There was no result at either attempt, so there was no second read.

The serialised set. Built as `ProgramSet([E1 text, E2 text], shots_per_executable=100)` from the two strings and sent with `shots=200`. The form saved to `raw/program-set-ir.json` is the action as the SDK serialises it, rewritten with one space indentation, as attempt 1 saved it. At attempt 2 that form hashed to `7b283c57b488513b9cd0a489d8db53e69df6b88aab8befac3a5fb4e6f5ba89d2`, equal to attempt 1's, and the file is identical to attempt 1's byte for byte. The compact action actually sent hashes to `9afd5c89507a5873251930fadfd0c1db94de87306b2e91e06f1145503e0a2be8`; attempt 1's compact action was not saved, but it is the same serialisation of the same object. The guard checked the saved form hash at the call and again on the request below the call.

## 5. The program texts

Both attempts submitted the same two texts, attempt 1's filled programs. In each, `rx(pi)` is written as the Braket SDK writes it, `rx(3.141592653589793)`.

### Executable 1 (E1), one play of d, then the barrier

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
    barrier Transmon_99_charge_tx, Transmon_99_readout_tx, Transmon_99_readout_rx;
}
b[0] = measure $99;
```

SHA-256 `63eb31af921a4fb2e6c844c32b404c51da7725972ea90742a519e8603ebcdaae`. This is byte for byte the program probe 02 submitted as Task B1.

### Executable 2 (E2), two plays of d, then the barrier

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
    play(Transmon_99_charge_tx, wait_d);
    barrier Transmon_99_charge_tx, Transmon_99_readout_tx, Transmon_99_readout_rx;
}
b[0] = measure $99;
```

SHA-256 `a00a679a705fb7cae25e92687fe0228a81bc4ff1d943ed8a40c4e6be765e2761`. This is not probe 02's A2: A2 had the two plays and no barrier.

## 6. How the SDK divided the shots

From the installed SDK's code (1.127.3.post0; `attempt-1/sdk-program-set-notes.md` has the file and line for each):

| stage | what the SDK does |
|---|---|
| submission | nothing is divided; `shots=200` is sent to `CreateQuantumTask` as the task total; `shots_per_executable` is not serialised |
| shots omitted | the SDK would send `shots_per_executable` times the number of executables |
| fetch | the SDK sets the shots for each executable to `requestedShots` divided by the number of executables; it reads no per executable count |
| result without per shot data | the SDK builds a `measurements` array from `measurementProbabilities` and sets `measurements_from_device` to False |

The SDK's own counts before each submission: `total_executables` 2, `shots_per_executable` 100, `total_shots` 200, executables enumerated as (0, 0, 0) then (1, 0, 0). How the service would have divided the shots is not known, since nothing ran.

The item added by the runner prompt for attempt 2 (each executable's `measurements_from_device` flag, and whether the raw result carries `measurements` or only `measurementProbabilities`) is not applicable: there was no result.

## 7. Beside, no word

| | fraction of ones |
|---|---|
| E1 | none (did not run) |
| E2 | none (did not run) |
| probe 02 B1, single task, same text as E1 | 0.39 |
| probe 02 A2, single task, two plays and no barrier | 0.20 |

Whether the executable with two plays had the lower fraction: not applicable. Compiled programs: none returned.

Three dated facts, side by side, with no cause named. The text of E1 was accepted as a single program task by `CreateQuantumTask` on this device at 19:59:55 UTC today (probe 02, Task B1, created then), and it ran. The same text, as program index 0 of a program set, was refused at 20:38:45 UTC and again at 21:17:36 UTC, each time with "Validation timed out".

## 8. Cost and times

| | attempt 1 | attempt 2 |
|---|---|---|
| tracker cost at the end | **[cost]** | **[cost]** |
| submission (call made) | 20:38:21 | 21:17:11 |
| refusal returned | 20:38:45 | 21:17:36 |
| creation, end, fetch | none | none |

The total across both attempts is [cost]. No task was created, so no task ARN was issued.

## 9. Beside this report

| file | what it is |
|---|---|
| `attempt-1/` | attempt 1's hand-back as it was, with its own report, `SHA256SUMS` and redaction log |
| `braket-probe-03-program-set-rule.md`, `rule.sha256` | the rule as copied again for attempt 2, and its hash |
| `go.log` | the ruling for attempt 2, the go and the hash check |
| `pre-go-checks.md` | attempt 2's checks before the go, without the account's figures |
| `programs/` | attempt 1's filled programs as resubmitted, with their hashes |
| `raw/` | the properties and device record at attempt 2's read, the serialised program set, the creation error |
| `run-log.json`, `run.log`, `run-stdout.log` | attempt 2's runner record |
| `scripts/` | attempt 2's scripts as run |
| `SHA256SUMS`, `redaction-log.md`, `raw-redaction-log.md` | hashes of every file, attempt 1's included; the final search; the search made as each raw file was saved |
