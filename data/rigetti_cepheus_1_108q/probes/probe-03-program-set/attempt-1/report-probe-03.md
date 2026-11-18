# Probe 03: what a program-set result carries on Cepheus-1-108Q, report

Run on 21 October 2026 by Claude Code, the Braket runner, under the rule `braket-probe-03-program-set-rule.md` (SHA-256 `b9748919eb26918976fbfd4ff0028899294cffbc97975e1cb6167e570811fb27`, the hash posted in public issue 76 of `dogma-guru/manacitra`, created 20:29:34 UTC). The author's go: "Oct 21, issue 76, Mantri's predictions are sealed". The copy of the rule matched the hash in the issue. No file whose name contains SEALED was read.

This is a probe, not a test. Nothing in this report is a finding, and nothing in it is adopted by its writing.

## 1. The four words

| word | value | from |
|---|---|---|
| 1 | **REJECTED** | `CreateQuantumTask` returned `ValidationException`, reason `ProgramSetValidationFailed`, at 20:38:45 UTC; no task was created |
| 2 | NOT APPLICABLE | no result |
| 3 | NOT APPLICABLE | no result |
| 4 | NOT APPLICABLE | no result |

The error, quoted in full from the service's response (saved verbatim in `raw/creation-error.txt`):

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

What the error states and what it does not. It states that validation of each of the two programs timed out. It does not name OpenQASM text, a `cal` block, a verbatim box, a frame, a waveform or any line of either program, and it does not say that any of these is unsupported in a program set. The word REJECTED is given because the runner prompt fixes it for a refused creation ("the probe is complete with the word REJECTED"). Whether a validation timeout is a rejection of the programs, in the sense of rule section 1 item 3, or a service condition at that moment, is not decided by anything that came back. That question is left to the author.

The SDK's own message says "Rerun the task". Under rule sections 1 and 7 nothing was rerun, no program was rewritten, and no second task was submitted. A read call at the end (`search_quantum_tasks` on this device, created since 20:30 UTC) returned no task, so no task exists from this probe.

## 2. Before the submission

| check | UTC | what was found |
|---|---|---|
| Spending limit for this device (read only, not changed) | 20:35:41 | its time period covers today; the remaining amount covered [cost] |
| Price list estimate, one task of 200 shots (the Tracker's own lookup) | 20:35:41 | [cost] |
| Device and window | 20:35:48 | ONLINE; inside the 16:00 to 23:59:59 window, 12251 seconds left; normal queue 0, priority queue 0 |
| Program set action in the properties | 20:35:48 | `braket.ir.openqasm.program_set`, version 1, `maximumExecutables` 100, `maximumTotalShots` 200000 |

The account's own spending figures are not recorded in this hand-back.

## 3. The pre-submission read and the qubit

The properties were read at **20:38:20 UTC**, one second before the submission. They carry `service.updatedAt` **2026-10-21T20:32:02+00:00**. The per qubit figures carry no timestamps of their own, so that is the timestamp for each figure below.

| | value |
|---|---|
| Qubit with the longest published T2 | **99** (no tie) |
| T2 | 34.90 µs (3.48978147743928e-05 s) |
| T1 | 30.87 µs (3.086777375838068e-05 s) |
| Readout fidelity (`READOUT`) | 0.982 |
| Single qubit RB (`RANDOMIZED_BENCHMARKING`) | 0.99942 (standard error 1.03e-05) |
| Simultaneous RB (`SIMULTANEOUS_RANDOMIZED_BENCHMARKING`) | 0.99851 |
| Next longest T2 | qubit 90 at 26.04 µs, qubit 7 at 23.90 µs |

**d = 30900 ns**: the T1 above, rounded to the nearest 100 ns. It is under the 60 µs cap, so the cap did not apply.

The frames, as the properties name them at the read: drive `Transmon_99_charge_tx`, readout `Transmon_99_readout_tx` and `Transmon_99_readout_rx`. All three are published.

The rule asks for a second read of the properties when the result is fetched. There was no result, so there was no second read.

## 4. The program texts

Both were filled from their templates after the read, hashed and saved. In each, `rx(pi)` is written as the Braket SDK writes it, `rx(3.141592653589793)`.

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

SHA-256 `63eb31af921a4fb2e6c844c32b404c51da7725972ea90742a519e8603ebcdaae`. This is byte for byte the program probe 02 submitted as Task B1 (same hash).

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

## 5. The program set and how the SDK divided the shots

The program set was built as `ProgramSet([E1 text, E2 text], shots_per_executable=100)` from the two strings, not from SDK circuit objects, and submitted once with `device.run(program_set, shots=200, tags={"probe-03": "program-set"})`. The serialised set is `raw/program-set-ir.json` (SHA-256 `7b283c57b488513b9cd0a489d8db53e69df6b88aab8befac3a5fb4e6f5ba89d2`): schema `braket.ir.openqasm.program_set` version 1, two programs, each with `source` and `inputs` (null).

The SDK's own counts before the submission: `total_executables` 2, `shots_per_executable` 100, `total_shots` 200, executables enumerated as (0, 0, 0) then (1, 0, 0).

How the installed SDK (1.127.3.post0) divides the shots, read from its code (`sdk-program-set-notes.md` has the file and line for each):

| stage | what the SDK does |
|---|---|
| submission | nothing is divided; `shots=200` is sent to `CreateQuantumTask` as the task total; `shots_per_executable` is not serialised |
| shots omitted | the SDK would send `shots_per_executable` times the number of executables |
| fetch | the SDK sets the shots for each executable to `requestedShots` divided by the number of executables; it reads no per executable count |
| result without per shot data | the SDK builds a `measurements` array from `measurementProbabilities` and sets `measurements_from_device` to False |

How the service would have divided them is not known from this probe, since nothing ran.

## 6. Beside, no word

| | fraction of ones |
|---|---|
| E1 | none (did not run) |
| E2 | none (did not run) |
| probe 02 B1, single task, same text as E1 | 0.39 |
| probe 02 A2, single task, two plays and no barrier | 0.20 |

Whether the executable with two plays had the lower fraction: not applicable. Compiled programs: none returned.

Two dated facts, side by side, with no cause named. The text of E1 was accepted as a single program task by `CreateQuantumTask` on this device at 19:59:55 UTC today (probe 02, Task B1, created then), and it ran. The same text, as program index 0 of a program set, was refused at 20:38:45 UTC with "Validation timed out".

## 7. Cost and times

| | value |
|---|---|
| Tracker cost at the end | **[cost]** (no task was created) |
| Submission (call made) | 2026-10-21T20:38:21Z |
| Refusal returned | 2026-10-21T20:38:45Z (24 seconds after the call) |
| Creation | none |
| End | none |
| Fetch | none |

## 8. Beside this report

| file | what it is |
|---|---|
| `braket-probe-03-program-set-rule.md`, `rule.sha256` | the rule as copied, and its hash |
| `go.log` | the go and the hash check |
| `pre-go-checks.md` | the checks before the go, without the account's figures |
| `sdk-program-set-notes.md` | the reading of the SDK's program set code |
| `programs/` | the templates, the filled programs as submitted, their hashes |
| `raw/` | the properties and device record at the read, the serialised program set, the creation error |
| `run-log.json`, `run.log`, `run-stdout.log` | the runner's record |
| `scripts/` | the scripts as run, with probe 02's runner and helpers kept as the starting copies |
| `SHA256SUMS`, `redaction-log.md`, `raw-redaction-log.md` | hashes of every file; the final search; the search made as each raw file was saved |

The task ARN would carry the account number; none was issued.
