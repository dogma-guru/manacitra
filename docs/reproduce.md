# Rerunning the wait on hardware

The short version is in the [README](../README.md#install-and-try-it). This page says how to rerun [finding 13](findings.md#finding-13)'s Part B and how to run the wait test on a chain you choose, with code the repository owns (`manacitra.wait`, Amendment A18), and what such a rerun is. The wait test ran on hardware in [finding 14](findings.md#finding-14), on five chains of ibm_fez on 11 October 2026, built by this code at `f28642a`. [Finding 15](findings.md#finding-15) ran it again on the same five chains on 13 October 2026, built by this code at `a55354d` (v0.5.0). [Finding 16](findings.md#finding-16)'s neighbour test built its wait tests by this code at `a55354d` and its Ramseys from them, by the transformations kept in its data record; `manacitra.wait.build_wait_ramsey` builds its active-neighbour Ramsey, R1, the same way. [Finding 17](findings.md#finding-17) added a known phase, with circuits built the same way at `a55354d`; the `phase` argument of `build_wait_test` and `build_wait_ramsey` builds them. [Finding 18](findings.md#finding-18) swept that phase all the way round, with circuits built the same way at `a55354d`. [Finding 19](findings.md#finding-19) ran the revised check on four chains drawn at build, with circuits built the same way at `a55354d`. [Finding 20](findings.md#finding-20) ran it on ibm_kingston, on four chains drawn at build, and [finding 21](findings.md#finding-21) ran it again on ibm_fez, on the six chains of findings 16 to 19, each with its circuits built by this code at `e45f15d`, the head of pull request 34, unedited: `build_wait_test` and `build_wait_ramsey`, with its default and with `neighbours="idle"`. Both runs analysed their counts with finding 19's analysis, unchanged, and `tests/_reuse_runs.py` recomputes them the same way (`k55_kingston` and `k54_day_two`). [Finding 22](findings.md#finding-22) swept the phase on finding 20's three chains, [finding 23](findings.md#finding-23) ran the check at the peak phase on four chains drawn at build, [finding 24](findings.md#finding-24) compared the peak phase with +90° on finding 20's chains, [finding 25](findings.md#finding-25) ran the check at the peak phase on a second calibration day, all four on ibm_kingston; on ibm_fez, Kickoff 60 stopped at its draw, [finding 26](findings.md#finding-26) measured the readout of sixteen qubits, and [finding 27](findings.md#finding-27) surveyed every qubit's readout and ran the check at the peak phase on chains drawn on the survey. All seven built their code at `e45f15d`, unedited: the sweep and the check by `build_wait_ramsey` and `build_wait_test`, and finding 26's readout circuits and finding 27's survey outside the package, translated by its `to_backend`. `tests/_reuse_runs.py` recomputes the six that ran (`k56_phase_sweep`, `k57_peak_check`, `k58_placement`, `k59_peak_check_day_two`, `k61_readout`, `k62_peak_check_fez`). The package's `phase_sweep`, `peak_check` and `readout_survey`, written after the runs, build the same circuits ([the method](method.md#the-check-at-the-peak-phase); `tests/test_wait.py`). [Finding 28](findings.md#finding-28) measured qubit 143's Ramsey at every wait from 0 to 63 µs in two quadratures (test 7, on ibm_fez), with its circuits built unedited at `b782d00`, the commit of v0.7.0: Part B's Ramsey by `part_b_circuit`, with an S† inserted for the Y quadrature, translated by `to_backend`. The package's `ramsey_xy`, written after the run, builds the same circuits, and `tests/_reuse_runs.py` recomputes the run from its counts with `ramsey_xy_fit` and `copies_check` (`t7_ramsey_xy`, `t7_readings`). The weight per execution span and the copies check split by span are recomputed from `data/ibm_fez/spans-t7.json` and the archived counts by `t7_spans` and `t7_span_readings`, and `pytest tests/test_reproduction.py -k "execution spans"` compares them with `data/ibm_fez/t7-span-readings.json`. The run's own analysis is kept in its record; in its hand-back it was reproduced with `MANACITRA_REPO=<checkout at 9b260fb> PYTHONPATH=<that checkout>/src python -B analyse_t7.py --counts results-t7-counts.json --stamps stamps-t7.csv`, then `python -B reading_t7.py`. The desk power check that preceded its rule reruns from a copy of `data/desk/` with `MANACITRA_REPO=/path/to/clone-at-9b260fb python power_t7v51.py fitcheck`, then `time` and `grid` ([its README](../data/desk/t7-power-check/README.md)). The archived numbers are reproduced from the archived counts, with no hardware ([Reproducing the numbers](../README.md#reproducing-the-numbers)).

## What a rerun is

A rerun is a new measurement, not a check of the archived one. The chip it runs on is the chip of that day and that calibration: a qubit's wait loss can change between calibrations, and in finding 13 it did. Qubit 144's loss over a wait of about 3.4 µs in superposition went from 0.15 under IBM's 06:12 UTC calibration stamp (Kickoff 46) to 0.012 under the 09:56 UTC stamp (Kickoff 47), on the same morning, while 143's stayed. So a rerun that finds no loss on 143 does not undo finding 13, and one that finds it again does not extend it to another day: each says what that chip did when it ran.

A rerun gets its own brief, written before anything is sent, as [How the results were made](kickoffs.md) describes: the question, the circuits and how the qubits are chosen, the shots, the analysis, the verdict rule with every threshold, the time cap, and what goes in the hand-back. The tools here build and analyse the circuits; the brief is yours.

## What runs

One job, on the chain L1-M-L3 you name (three physical qubits, L1 and L3 each coupled to M by a CZ):

- **The wait test**, without and with XY4 refocusing, five copies of each in an order drawn from a seed, 10,000 shots each. [The method](method.md#the-wait-test) says what it measures.
- **Part B**, as in Kickoff 47: on each qubit of a group, a Ramsey circuit (H, a wait, H, measure) and an echo circuit (the same, with an X halfway through the wait), at waits of 0, 250, 500, 850, 1,000 and 2,000 dt; the qubits of a group are not neighbours and run in parallel, and every circuit runs twice, the second copy in reverse order, 4,000 shots each. The groups default to M alone and to the two end lines together. Built for Kickoff 47's groups and waits on ibm_fez, all 48 circuits, both copies, match a dated reconstruction of Kickoff 47's Part B instruction by instruction, and match the operation counts recorded from the circuits as sent. The reconstruction was made on 10 October 2026 by running the run's own builder again, and its [provenance record](../data/ibm_fez/k47-wait-part-b-reconstruction.json) carries the builder's Part B text, so it can be repeated. Whether the circuits are identical, instruction by instruction, to the ones actually submitted cannot be checked: those were not saved. `tests/test_wait.py` makes these checks.

With the defaults that is 58 circuits and 292,000 shots. The analysis gives the wait test's F without and with refocusing and the gain, and, on each qubit of Part B, the Ramsey and echo losses at the wait nearest 3.4 µs with their 90% intervals and Kickoff 47's kind of loss: NOT REPRODUCED, REFOCUSABLE, NOT REFOCUSABLE or MIXED. The rule's thresholds are parameters of `manacitra.wait.part_b_losses`, defaulting to Kickoff 47's.

## Running it

Install with the IBM and Aer extras, from a clone:

```bash
pip install -e ".[ibm,aer]"
```

A dry run on qiskit-ibm-runtime's offline snapshot of the processor, with no account; it prints M's waits, the circuits drawn, the shot count and the repository's time estimate:

```bash
python examples/04_wait_test.py --processor ibm_fez --chain 144-143-142 --offline
```

Without `--offline` the dry run reads the live backend through your saved IBM account, and still sends nothing. The snapshot's durations can differ from the live ones: M's waits are 786 dt in the snapshot, and in Kickoff 47 143's waits on the live backend were 836, 836 and 842 dt. On the live backend, M's waits are read from its target when the circuits are built. IBM gives its own time estimate only for a job that exists (Qiskit Runtime's `usage_estimation`), so a dry run cannot print it; a submission prints it after sending.

To rerun finding 13's Part B on Kickoff 47's qubits, name its groups; the job then carries the wait test on the chain too:

```bash
python examples/04_wait_test.py --processor ibm_fez --chain 144-143-142 --groups "143,131,124;142,144,125"
```

To send, add `--submit` and a usage cap in seconds, `--cap-s`. The job goes through the same submit-once guard as a map ([Before anything is sent to a provider](install.md#before-anything-is-sent-to-a-provider)): the usage is read, the cap is checked against the ledger's open reservations, and the job is recorded before it is sent; a second send of the same circuits is refused unless `--allow-resubmit` is given, and that is logged. The cap is the repository's check, not the provider's: `--cap-s` is checked against the repository's own estimate of the job's time and the reservations in a ledger that every process on the machine shares. The hard stop is the provider's own limit on your instance. The sampler's own dynamical decoupling and twirling are off, so every circuit runs with exactly the pulses it was built with. The handle is written to `wait-test-handle.json`. Then, once the job is done:

```bash
python examples/04_wait_test.py --fetch wait-test-handle.json
```

This writes the counts to `wait-test-counts.json` and analyses them. A saved counts file is analysed again, offline, with `--analyse wait-test-counts.json`.

Once a backend is created, Manacitra cleans account and instance identifiers, tokens and email addresses from the log records of the IBM and Open Quantum clients (with the IBM client's own libraries) and of `urllib3` and `requests`, and from a provider's error messages before they are stored or shown. If your own program uses those libraries for other services, their records are cleaned too. To keep identifiers out, an ordinary word that follows "instance", "account" or a similar word in a provider's error message may be replaced, and the original message is not kept.

## How the rule was tested offline

As Kickoff 36 tested the map's rule on a simulation with planted answers, `tests/test_wait.py` tests the wait rule on Qiskit Aer with an offset planted by a noise pass written here: every delay on M becomes the delay and an RZ of 2π f t. The circuits are built for a synthetic three-qubit target whose durations are round numbers; no vendor noise model and no device data enter. Fixed before the tests were run:

- **No offset.** Part B reads NOT REPRODUCED, and the wait test's F with and without refocusing differ by less than 0.05.
- **A steady 47 kHz on M.** Part B's Ramsey loss at 3.4 µs is within 0.03 of 0.229, the echo loss is below 0.02, and the verdict is REFOCUSABLE; the wait test's F is above 0.9 with refocusing and at least 0.3 lower without.
- **±47 kHz, the sign drawn per shot.** Part B again reads REFOCUSABLE: the rule does not separate a steady offset from one that switches, as finding 13 says.
- **Kickoff 47's archived counts.** The package's analysis gives the archived kind of loss on all six qubits.

Beside these, a control the rule must say no to: white dephasing on M, which no refocusing removes, reads NOT REFOCUSABLE, and refocusing does not raise the wait test's F. These are tests of the code and the rule on a simulation, not findings.

Back to the [README](../README.md).
