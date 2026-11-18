# Test 21: the runner's desk check (t21-rule.md section 9)

Run with the runner's own code for the read (`read_core_t21.py`, calling `sharing_ratio`, `two_state_reading`, `time_average_sd` and `boundary_ratio` at manacitra v0.10.0) by `desk_t21.py`, started 2026-11-17T01:54:52Z, before any job and before Mantri's script or its output file was opened. The rule's own table of Mantri's rates, in section 9, was read with the rule. Its full output is `desk-t21.json`.

**Every required rate is met.**

- **Case 1, on both layouts:** SHARED and TIMED, τ_c within a factor of 1.5, the duty read, and the duty within 0.05 are all at or above the rule's 95, 85, 95 and 85.
- **Case 7, one state, on both layouts:** SHARED on 0 of 100, so at or below 1.

The simulation is a stationary two-state process, sampled shot by shot in sweep order at test 10's measured time per shot. That time is 0.31660 ms: the summed duration of test 10 job 1's three spans over their summed shots. Each layout is one span holding every position: 20 positions of 3,200 shots for job 2, and 36 of 1,800 for job 3. There are 100 jobs per case and per layout.

## The runner's rates, with Mantri's beside them in brackets

Mantri's numbers are from `desk-check-t21-mantri.out`, which was opened after this check ran.

| case | layout | SHARED | SHARED and TIMED | median lag | τ_c within 1.5 | duty read | duty within 0.05 | UNDECIDED |
|---|---|---|---|---|---|---|---|---|
| 1 | job 2 | 100 (100) | 100 (100) | 8.0 (8.0) | 90 (97) | 100 (100) | 88 (92) | 0 (0) |
| 1 | job 3 | 100 (100) | 100 (100) | 4.0 (5.0) | 94 (94) | 100 (100) | 96 (96) | 0 (0) |
| 2 | job 2 | 100 (100) | 100 (100) | 8.0 (8.0) | 94 (94) | 0 (0) | 0 (0) | 0 (0) |
| 2 | job 3 | 100 (100) | 100 (100) | 4.0 (4.0) | 97 (91) | 0 (0) | 0 (0) | 0 (0) |
| 3 | job 2 | 100 (100) | 100 (100) | 8.0 (8.0) | 92 (89) | 0 (0) | 0 (0) | 0 (0) |
| 3 | job 3 | 100 (100) | 100 (100) | 4.0 (4.0) | 91 (95) | 0 (0) | 0 (0) | 0 (0) |
| 4 | job 2 | 100 (100) | 100 (100) | 4.0 (4.0) | 71 (69) | 100 (100) | 97 (94) | 0 (0) |
| 4 | job 3 | 100 (100) | 86 (82) | 3.0 (3.0) | 0 (18) | 98 (97) | 97 (95) | 0 (0) |
| 5 | job 2 | 100 (100) | 0 (0) | 2.0 (2.0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| 5 | job 3 | 100 (100) | 0 (0) | 1.0 (1.0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| 6 | job 2 | 100 (100) | 100 (100) | 30.0 (31.0) | 88 (92) | 100 (100) | 58 (62) | 0 (0) |
| 6 | job 3 | 100 (100) | 100 (100) | 16.0 (17.0) | 90 (86) | 100 (100) | 60 (55) | 0 (0) |
| 7 | job 2 | 0 (0) | 0 (0) |  () |  () | 0 () | 0 () | 12 (6) |
| 7 | job 3 | 0 (0) | 0 (0) |  () |  () | 0 () | 0 () | 12 (7) |
| 8 | job 2 | 100 (100) | 86 (80) | 3.0 (3.0) | 0 (20) | 0 (0) | 0 (0) | 0 (0) |
| 8 | job 3 | 100 (100) | 1 (2) | 2.0 (2.0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) |

## Choices the rule leaves to the runner, made before the check ran (`desk_t21.py`'s docstring)

- **Which state is which.** The state with each case's first dwell carries its first emission. So October's 0.050 s state reads 0.80, and case 8's 0.012 s state is the high state, with a duty of 0.06.
- **The quadratures.** The X rows carry the case's emissions. The Y rows carry no separation: both states read the mean of the two emissions. The quadrature of record is chosen by the rule's larger sharing ratio over the whole job.
- **The process's own values.** The process starts in its stationary distribution. Its own τ_c is d1 d2 / (d1 + d2), and its own duty is d1 / (d1 + d2). The duty is judged against that stationary duty; the fraction of the job actually spent in the high state is recorded beside it.
- **Case 6.** "As slow as fez 143" is taken as duty 0.344 and τ_c 0.17 s, test 15's desk case for 143. That gives dwells of 0.259 and 0.494 s.
- **Cases 4 to 8.** They keep case 1's emissions. Case 7 holds one state, reading 0.80.
- **The seeds.** The simulation's seeds are SeedSequence([21901, case, layout, trial]). The read's permutation seed is the rule's 21401, made fresh for every span read, as the real read uses it.

## Differences from Mantri's rates

All the differences are in cases the rule records without a requirement, or are within trial scatter on case 1.

- **τ_c within 1.5, cases 4 and 8.** The runner counts only spans that read TIMED, since for a span faster than the clock the rule reports three sweeps as a ceiling rather than a τ_c. Mantri's counts also take spans with a lag under 3 sweeps. On case 4's job 3 layout this gives 0 here against Mantri's 18. On case 8's job 2 layout it gives 0 against Mantri's 20.
- **Case 6.** Mantri used dwells of 0.29 and 0.48 s with emissions 0.85 and 0.10. The runner used 0.259 and 0.494 s with 0.80 and 0.15. The duty within 0.05 reads 58 and 60 here, against Mantri's 62 and 55.
- **Case 7, UNDECIDED.** This reads 12 of 100 here, against Mantri's 6 and 7. The runner's quadrature of record is the larger of two ratios that are both pure noise in this case, which raises the ratio that is read. SHARED stays at 0.
- **Case 1.** τ_c within 1.5 reads 90 and 94 here, against 97 and 94. The duty within 0.05 reads 88 and 96, against 92 and 96. The rule asks for at least 85 and 85.

## A rehearsal on real data, beside the check

The read was run on test 10's jobs 1 and 2, cut down to qubits 11 and 95 at the same waits as tests 10 and 21. On that data, per span:
- the sharing ratios equal test 15's published values to every printed digit;
- the thresholds equal test 15's to every printed digit;
- the threshold duties lie between 0.196 and 0.237.

On test 10's 31 ms clock, every span of both qubits reads SHARED, FASTER THAN THE CLOCK and DUTY NOT READ. That is a rehearsal of the code, not a reading of this test.
