# Probe 02: the scaling of the wait on Cepheus-1-108Q, report

Run on 21 October 2026 by Claude Code, the Braket runner, under the rule `braket-probe-02-scaling-rule.md` (SHA-256 `024783547852c52ab9f834c2a85f10d2eb73227aef73b8cc0ec895013acb8e41`, the hash posted in public issue 75 of `dogma-guru/manacitra`, created 19:53:46 UTC). The author first sent the hash in chat, then the go: "Oct 21, 2026, Mantri's predictions are sealed, issue 75". The copy of the rule matched the hash in chat and in the issue. No file whose name contains SEALED was read.

This is a probe, not a test. Nothing in this report is a finding, and nothing in it is adopted by its writing.

## 1. The answer in two words

| word | value | from |
|---|---|---|
| Scaling (section 4) | **SCALES** | r1 = 0.53 / 0.96 = 0.552 and r2 = 0.20 / 0.53 = 0.377, both below 0.6 |
| Barrier (section 4) | **BARRIER ADDS WAIT** | D = 0.53 minus 0.39 = 0.140, above 2s = 0.099 |

All four tasks were accepted at creation and completed. No program was rejected.

## 2. Before the submission

| check | UTC | what was found |
|---|---|---|
| Spending limit for this device (read only, not changed) | 19:57:05 | time period 20 October 00:00:00 to 22 October 23:59:59 UTC, covering today; the remaining amount covered [cost] |
| Device and window | 19:59:26 | ONLINE; inside the 16:00 to 23:59:59 window, 14433 seconds left; normal queue 0, priority queue 0 |

The account's own spending figures are not recorded in this hand-back.

## 3. The pre-submission read and the qubit

The properties were read at **19:59:47 UTC**, one second before Task A0 was submitted. They carry `service.updatedAt` **2026-10-21T19:32:03Z**. The per qubit figures carry no timestamps of their own, so that is the timestamp for each figure below.

| | value |
|---|---|
| Qubit with the longest published T2 | **99** (no tie) |
| T2 | 34.90 µs (3.48978147743928e-05 s) |
| T1 | 30.87 µs (3.086777375838068e-05 s) |
| Readout fidelity (`READOUT`) | 0.982 |
| Single qubit RB (`RANDOMIZED_BENCHMARKING`) | 0.99942 (standard error 1.03e-05) |
| Simultaneous RB (`SIMULTANEOUS_RANDOMIZED_BENCHMARKING`) | 0.99851 |
| Next longest T2 | qubit 90 at 26.04 µs, qubit 7 at 23.90 µs |

**d = 30900 ns**: the T1 above, rounded to the nearest 100 ns. It is under the 60 µs cap, so the cap did not apply. 2d is written as two consecutive plays of the same 30900 ns waveform.

The frames, as the properties name them at the read: drive `Transmon_99_charge_tx`, readout `Transmon_99_readout_tx` and `Transmon_99_readout_rx`. All three are published.

## 4. The tasks

Each program was filled from its template after the read, hashed and saved, and submitted once with the tag `probe-02` and its label. In each program `rx(pi)` is written as the Braket SDK writes it, `rx(3.141592653589793)`. A0 and A1 hash the same as probe 01's Task A and Task D, which they are.

### Task A0, no wait, 100 shots

```
OPENQASM 3.0;
bit[1] b;
#pragma braket verbatim
box{
rx(3.141592653589793) $99;
}
b[0] = measure $99;
```

SHA-256 `de3530ac214f61e087ac7407a3e2762425178c9f590c5198c276c680f2f2015b`. **Ran.** 96 ones in 100 shots, p_0 = 0.96. Measured qubit 99.

### Task A1, one play of d, 200 shots

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

SHA-256 `640f4eb75a752688aa5d29a9b3c1ce17d5efcb0ed2bf0aee45196a1ef05bdffa`. **Ran.** 106 ones in 200 shots, p_d = 0.53. Measured qubit 99.

### Task A2, two plays of d, 100 shots

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
}
b[0] = measure $99;
```

SHA-256 `6330fa0a2351b9146cb903d6a54410b069da42558a7c7134e1129187be066761`. **Ran.** 20 ones in 100 shots, p_2d = 0.20. Measured qubit 99.

### Task B1, one play of d then a barrier, 200 shots

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

SHA-256 `63eb31af921a4fb2e6c844c32b404c51da7725972ea90742a519e8603ebcdaae`. **Ran.** Accepted at creation. 78 ones in 200 shots, p_B = 0.39. Measured qubit 99.

## 5. The properties at each fetch

The properties were read again as each result was fetched. Every read carries the same `service.updatedAt` as the pre-submission read, and qubit 99's figures did not move between reads.

| task | properties read (UTC) | `service.updatedAt` | T1 of qubit 99 | T2 of qubit 99 |
|---|---|---|---|---|
| pre-submission | 19:59:47 | 2026-10-21T19:32:03Z | 3.086777375838068e-05 s | 3.48978147743928e-05 s |
| A0 | 19:59:56 | 2026-10-21T19:32:03Z | 3.086777375838068e-05 s | 3.48978147743928e-05 s |
| A1 | 19:59:57 | 2026-10-21T19:32:03Z | 3.086777375838068e-05 s | 3.48978147743928e-05 s |
| A2 | 19:59:58 | 2026-10-21T19:32:03Z | 3.086777375838068e-05 s | 3.48978147743928e-05 s |
| B1 | 19:59:59 | 2026-10-21T19:32:03Z | 3.086777375838068e-05 s | 3.48978147743928e-05 s |

## 6. The reading

| task | ones | shots | fraction of ones |
|---|---|---|---|
| A0 (no wait) | 96 | 100 | p_0 = 0.96 |
| A1 (one d) | 106 | 200 | p_d = 0.53 |
| A2 (two d) | 20 | 100 | p_2d = 0.20 |
| B1 (one d, barrier) | 78 | 200 | p_B = 0.39 |

**On scaling.** r1 = p_d / p_0 = 0.53 / 0.96 = **0.552**. r2 = p_2d / p_d = 0.20 / 0.53 = **0.377**. Both are below 0.6. The word is **SCALES**.

**On the barrier.** D = p_d minus p_B = 0.53 minus 0.39 = **0.140**. s = √(0.53 × 0.47 / 200 + 0.39 × 0.61 / 200) = **0.0493**, so 2s = 0.0987. D is above 2s. The word is **BARRIER ADDS WAIT**.

No other number is read for either word.

## 7. Beside, no word

| pair | implied T1 | published T1 at the pre-submission read | published T1 at the fetch |
|---|---|---|---|
| A0 and A1: d / ln(p_0 / p_d) = 30.9 µs / ln(0.96 / 0.53) | 52.02 µs | 30.87 µs | 30.87 µs (A0 and A1) |
| A1 and A2: d / ln(p_d / p_2d) = 30.9 µs / ln(0.53 / 0.20) | 31.71 µs | 30.87 µs | 30.87 µs (A1 and A2) |

These are reported as numbers and not interpreted.

## 8. The compiled programs

Each result carries `additionalMetadata.rigettiMetadata.compiledProgram`. Verbatim:

**A0**, no pulse lines:

```
PRAGMA INITIAL_REWIRING "NAIVE"
DECLARE ro BIT[1]
PRAGMA PRESERVE_BLOCK
RX(3.141592653589793) 99
PRAGMA END_PRESERVE_BLOCK
MEASURE 99 ro[0]
```

**A1**, one pulse:

```
PRAGMA INITIAL_REWIRING "NAIVE"
DECLARE ro BIT[1]
PRAGMA PRESERVE_BLOCK
RX(3.141592653589793) 99
PRAGMA END_PRESERVE_BLOCK
NONBLOCKING PULSE 99 "Transmon-99_charge_tx" flat(duration: 3.09e-05, iq: 0.0 + 0.0*i)
MEASURE 99 ro[0]
```

**A2**, two pulses:

```
PRAGMA INITIAL_REWIRING "NAIVE"
DECLARE ro BIT[1]
PRAGMA PRESERVE_BLOCK
RX(3.141592653589793) 99
PRAGMA END_PRESERVE_BLOCK
NONBLOCKING PULSE 99 "Transmon-99_charge_tx" flat(duration: 3.09e-05, iq: 0.0 + 0.0*i)
NONBLOCKING PULSE 99 "Transmon-99_charge_tx" flat(duration: 3.09e-05, iq: 0.0 + 0.0*i)
MEASURE 99 ro[0]
```

**B1**, one pulse, then a `FENCE` line where the barrier was written:

```
PRAGMA INITIAL_REWIRING "NAIVE"
DECLARE ro BIT[1]
PRAGMA PRESERVE_BLOCK
RX(3.141592653589793) 99
PRAGMA END_PRESERVE_BLOCK
NONBLOCKING PULSE 99 "Transmon-99_charge_tx" flat(duration: 3.09e-05, iq: 0.0 + 0.0*i)
FENCE 99
MEASURE 99 ro[0]
```

| task | pulse lines | keyword | other line between the RX block and MEASURE |
|---|---|---|---|
| A0 | 0 | | none |
| A1 | 1 | `NONBLOCKING` | none |
| A2 | 2 | `NONBLOCKING` on each | none |
| B1 | 1 | `NONBLOCKING` | `FENCE 99` |

As section 2 asks, the record is that A2's compiled program carries **two pulses**, not one. The compiled frame name is written `Transmon-99_charge_tx` and the published one `Transmon_99_charge_tx`; both are quoted as they appear.

## 9. Cost

Each figure is the `braket.tracking.Tracker` estimate for this probe, from one Tracker wrapping the whole session. The Tracker prices a task at its creation.

| point | UTC | tracker total | this task |
|---|---|---|---|
| before A0 | 19:59:48 | [cost] | |
| after A0 submission | 19:59:52 | [cost] | [cost] |
| after A1 submission | 19:59:53 | [cost] | [cost] |
| after A2 submission | 19:59:54 | [cost] | [cost] |
| after B1 submission | 19:59:55 | [cost] | [cost] |
| end, after all four results | 19:59:59 | **[cost]** | |

No hard stop was reached. The highest per task figure was [cost] against [cost], and the total was [cost] against [cost]. The Tracker's statistics: 4 tasks COMPLETED, 600 shots.

## 10. Times

| task | submitted | created (service `createdAt`) | ended (service `endedAt`) | result fetched and saved |
|---|---|---|---|---|
| A0 | 19:59:48 | 19:59:52.602 | 19:59:53.341 | 19:59:55 |
| A1 | 19:59:53 | 19:59:53.639 | 19:59:54.302 | 19:59:56 |
| A2 | 19:59:54 | 19:59:54.500 | 19:59:55.866 | 19:59:57 |
| B1 | 19:59:54 | 19:59:55.269 | 19:59:56.170 | 19:59:58 |

The four were submitted in order within seven seconds, without waiting for results. Each ended within about two seconds of its creation, so they did not sit in a queue together: A0 had ended before A1 was created, and A1 before A2. Polling began after the last submission, so the only state the runner saw for each task was COMPLETED, first seen at the fetch time above; the service's `createdAt` and `endedAt` bound the rest of the state history. Section 5 of the rule names no cause for any time, and none is named here.

## 11. What is not read

No T1 is claimed. No cause is named for any figure, difference, keyword, the `FENCE` line or any time. No comparison with any other device is made, and no device is ranked. The per shot arrays are saved in the order returned (`raw/task-<label>-measurements.json`), and nothing here depends on that order.

## 12. The hand-back

* `report-probe-02.md`, this file.
* `braket-probe-02-scaling-rule.md` and `rule.sha256`.
* `go.log`: the go, the spending limit check (without the account's figures), the window check, the start of the run.
* `run-log.json`, `run.log`, `run-stdout.log`: the run's record.
* `programs/`: the templates written before the submission with `templates.sha256`, the filled programs as submitted, and `filled.sha256`.
* `raw/`: the pre-submission properties and device read; the properties and device read at each fetch; for each task, the full result object, the task metadata, the states seen, the per shot measurements and `additionalMetadata` with the compiled program.
* `scripts/`: the scripts as run. `run_probe.py` and its timestamped copy `run_probe-as-run-*.py` are the same file; `run_probe-probe01-start.py` is probe 01's script as it stands in probe 01's hand-back, the starting point; `check_limit.py` and `check_window.py` make read calls only; `finalize.py` assembled this hand-back.
* `SHA256SUMS` over the hand-back, then `redaction-log.md`, the final search of every file. `raw-redaction-log.md` is the search made as each raw file was first saved.

Task ARNs, the results bucket and the account number were redacted from every saved file, as the redaction logs record. The device ARN carries no account number and is kept. The first final search stopped on twelve digit runs inside the rule's SHA-256 hash and on the spending limit's field names written as code in two scripts; after the runner checked that none of those runs is the account number, the search was narrowed for those two cases only, as `go.log` records and the scripts' comments date.
