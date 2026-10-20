# Changelog

## 0.10.0 (unreleased)

Two runs on ibm_fez's qubit 143 on 19 October 2026 were read per shot, each run and each read under a rule hashed before it. In all eighteen monitor spans read, the state read SHARED. On a job of six spans every boundary read NO CHANGE, which does not show the duties equal; the monitor means of runs on 17 and 19 October were 0.330, 0.341 and 0.313. A pattern noticed in the published weights, a job's middle span above its ends, was tested on new data under a rule fixed before them and read NOT SEEN. The desk model Sandhi, at version 4.1, had its bets for one design hashed before the run, and on that run no family of its bets counted against it; its bets for the other design are not yet scored. `manacitra.wait` gains the per-shot read of a span: the sweep series, the sharing ratio, the duty and correlation time, and the error of a time average; thresholds and words are the caller's. No cause is named.

- Amendment A28: `manacitra.wait` gains the per-shot read of a span, ported from test 15's read, which tests 16 and 17
  ran unchanged: `sweep_series` (one qubit's shots per position, in returned order, made into each span's bit matrix
  of whole repeats and its column means, by `span_assignment`), `sharing_ratio`, `two_state_reading` (the threshold
  between two caller-given percentiles, the duty, the correlation lag and time, the switches, dwells, quarter-span
  duties and mid-sweep fraction), `time_average_sd` (with test 15's ceiling at three sweeps), `boundary_ratio` and
  `sweep_autocorrelation`. Everything else in the package is unchanged. Finding 30 (test 11 on a third day, tests 16
  and 17), with their data in `data/ibm_fez/` (one record per test, in A27's layout; the per-shot arrays named by their
  SHA-256 and not published; the posted rules of tests 16 and 17 published unchanged; the desk checks, hash checks and
  rulings; the run's code as verbatim lines of the scripts as run), and the line of the note of 19 October that test
  17's rule tests, as a dated excerpt (`t17-middle-note-excerpt.md`). `tests/_reuse_runs.py` recomputes day 3's three
  jobs as day 2's are recomputed, and tests 16's and 17's spans, boundaries, jobs and middle test through the package
  from the sweep means their reads published; `tests/test_wait.py` recovers a planted duty and correlation time, and,
  given test 17's arrays (`MANACITRA_SHOTS`), reproduces its long job's read. The desk model Sandhi's versions 4 and 4.1
  in `data/desk/sandhi/v4/` and `v4.1/` (their reports, predictions, fits, hierarchies, checks, scorers with their
  tests and C source, run logs and sums, and their scorecards on test 16 and test 17, the local paths the scorer wrote
  replaced; their large files attached to the release, with their SHA-256 in the folder's README), checked by
  `tests/test_sandhi.py`. Round 5c of the desk power check, version 5.1's grid on a second machine, in
  `data/desk/t7-power-check-round5c/` beside round 5b, its results attached to the release. The README opens with
  finding 30, and its table of findings gains an eleventh row.
- Documentation: a glossary, page headers, a reading order, timings, and the quick start's pick matched to `manacitra
  pick`'s default, from a first reader's notes.

## 0.9.0 (18 October 2026)

Nine records on ibm_kingston and ibm_fez, eight of them tests under rules hashed before each run, asked when a qubit's Ramsey fringe changes within a job. Read by the provider's execution record, every job of 248 to 300 circuits ran as three spans; read per shot, on every qubit where tests 13 and 15 read SHARED (143; 11 and 95 in every span, 120 in half), the means at equal returned shot index across a span's circuits varied far beyond independent shots, read as a state the circuits share, and on 143 the fringe switches between its two lines with correlation lags of 4 to 10 sweeps (about 0.1 to 0.2 s if returned order is chronological), so a span's weight reads as an average over the span whose estimated error is not the shots'. Under that error all 17 weight boundaries read in the monitor jobs show NO CHANGE, where the rules' shot-noise errors had put 143's up to 35.1 apart; between two calibration stamps about a third of the 47 kingston qubits compared (16) changed by 4 kHz or more in the one-line fit, while the split on 143 moved by a tenth of a kilohertz between days. A desk model, Sandhi, described the earlier records with five rates and is set down at version 3; no cause is named. `manacitra.wait` gains the monitor circuits, the span assignment from the provider's execution record, and the per-repeat phase, length and antiphase weight; thresholds and verdicts are the caller's.

- Amendment A27: `manacitra.wait` gains the monitor, `ramsey_monitor` (every qubit of a set at its own wait in one
  circuit, X and Y, between the readout circuits, in a fixed order); the span assignment, `span_assignment` (each
  position's span and each repeat's span or straddling from the provider's execution record, and the gaps); the
  per-repeat phase and length, `monitor_phase` (the switch test between adjacent repeats, the time the tested pairs
  cover, the levels and the slopes against the repeat index, with the caller's floors and thresholds); and the weight at
  antiphase, `monitor_weight`, with `median_phase`. Everything else in the package is unchanged. Finding 29 (tests 8 to
  15), with their data in `data/ibm_kingston/` and `data/ibm_fez/` (one record per test; the counts and the larger
  analysis records as gzip files beside them, named in each record by their SHA-256; the posted rules published
  unchanged; the desk checks; the run's code as verbatim lines of the scripts as run), the span record of tests 8 and 9,
  and the desk model Sandhi in `data/desk/sandhi/` (its kickoffs and naming ruling, and its run 3.1 as delivered, its
  ledgers attached to the release with their SHA-256 in the folder's README). `tests/_reuse_runs.py` recomputes test
  10's verdicts, test 11's three jobs, test 9's job 1 on 43 and 134 and the kingston spans, and `tests/test_sandhi.py`
  checks the model's counts. Tests 13 and 15 read the per-shot results of completed jobs; their records name every
  array by its SHA-256, and the arrays are not published. By ruling R2, finding 29 reads every level per span against
  the error of a time average, Sandhi is set down at version 3, and the finding's first name, "the gated states", is
  retired for "the shared state within a span"; it stays as the dated name of Sandhi's version 3. The README opens with
  finding 29, and its table of findings gains a tenth row.

## 0.8.0 (17 October 2026)

The qubit that waited in the circuits of findings 13 to 18 and 21, ibm_fez's 143, was measured at every wait from 0 to 63 µs in two quadratures under a rule fixed and hashed before the job. Its Ramsey fringe is two fixed frequencies about 90 kHz apart at unequal weight, not one line decaying: the two-line model's held-out error was a quarter of the one-line model's, the split 44.8 kHz, the upper line's weight 0.36 averaged over the job. The weight differed between the job's three execution spans, from about 0.46 to 0.27, which the rule did not assume and finding 28 reports as what the counts show. No cause is named. `manacitra.wait` gains the two-quadrature Ramsey, the one-line and two-line fit with a held-out error and a bootstrap, and a copies check; the rule's thresholds are the caller's. The desk power check that preceded the rule is published beside the data.

- Amendment A25: `manacitra.wait` gains the two-quadrature Ramsey on one qubit, `ramsey_xy` (X and Y at the waits
  the caller names, with the two readout circuits as an optional third series); its fit, `ramsey_xy_fit` (one line and
  two fixed lines with a free weight, fitted jointly over both quadratures on the waits the caller names and scored by
  the held-out error on the others, the two lines held inside the band the fitted waits can tell apart,
  `ramsey_xy_band`, and a bootstrap over the copies and their shots; a rule's thresholds are the caller's); and a
  copies check, `copies_check`. `build_wait_test`, `build_wait_ramsey`, `predicted_fidelity`, the sweep, the peak, the
  survey and `ramsey_fit` are unchanged; `manacitra.archive.records` leaves out `data/desk/`, which holds no run
  records. Finding 28 (test 7), with its data in `data/ibm_fez/t7-ramsey-xy.json` (the counts, the run records, the
  analysis and the readings after the data, and the run's code as verbatim lines of the scripts as run), its posted
  rule published unchanged (`t7-rule.md`), the desk power check that preceded the rule in `data/desk/` (the grid's
  results attached to the release, with their SHA-256 in the folder's README), its recompute in
  `tests/_reuse_runs.py`, a test that the package builds what the run built, and one figure. The README opens with
  finding 28, and its table of findings gains a ninth row.
- Amendment A26: finding 28 reads the weight per execution span, after the provider's execution record, which is
  archived (`data/ibm_fez/spans-t7.json`, with the read as verbatim lines), with the readings against it in
  `data/ibm_fez/t7-span-readings.json` and their recompute in `tests/_reuse_runs.py`.

## 0.7.0 (15 October 2026)

The check can now be placed at the active-neighbour Ramsey's loss maximum: a six-phase sweep fixes each chain's peak phase, and the check runs there, where every cell is informative by construction. `manacitra.wait` gains the sweep, the fit, the peak phase and a readout survey with a per-qubit readout error from measured counts; the 0.6.0 check at +90° is unchanged. Findings 22 to 27, from four runs on ibm_kingston on 14 and 15 October 2026 and two on ibm_fez on 15 October, with their data, and the record of a draw on ibm_fez that found no chain on the published readout table. At the peak phase the check predicted the wait test within ±0.15 on twelve of twelve cells over three runs on new chains on two processors (findings 23, 25 and 27). On ibm_fez a direct measurement found readout errors of 0.004 to 0.021 on sixteen qubits the published table put at up to 0.44, and a survey of all 156 qubits a median of 0.0098 against a published 0.166 (findings 26 and 27).

- Amendment A24: `manacitra.wait` builds the check at the peak phase in two jobs: `phase_sweep` (the active-neighbour
  Ramsey at six phases, with the wait test at the same phases as an optional second series), `sweep_fit` (the fit of
  findings 18 and 22), `peak_phase` and `leftover`, and `peak_check`, which builds the check at the peak phase, with
  0.6.0's check at +90° beside it, from the sweep's counts and returns the peak to record before it runs; and
  `readout_survey` and `readout_errors` measure every qubit's readout error, with any screen's threshold the caller's.
  `build_wait_test`, `build_wait_ramsey` and `predicted_fidelity` are unchanged. Findings 22 to 27 (Kickoffs 56 to 59,
  61 and 62), with their data in `data/ibm_kingston/` and `data/ibm_fez/` (the counts, labelled by job where a run had
  several, the run records, the chain draws, the peaks recorded before each check, Kickoff 62's survey and each run's
  code as verbatim lines of the scripts as run), Kickoff 60's draw that found no chain, the eight posted rule files
  published unchanged, their recomputes in `tests/_reuse_runs.py`, and a test that the package builds what the runs
  built. The README opens with the check at the peak phase, and its table of findings has one row per thread; the
  table with one row per finding moves to `docs/findings.md`.

## 0.6.0 (15 October 2026)

The check's default Ramsey now runs with the waiting qubit's neighbours active, as they are in the circuit; the 0.5.0 instrument remains available as `neighbours="idle"`. Findings 15 to 21, from six runs on ibm_fez on 13 and 15 October 2026 and one on ibm_kingston on 14 October, with their data. The revised check predicted the wait test within ±0.15 on all informative cells on ibm_fez on two days, across a maintenance (findings 19 and 21), and missed on one of four cells on ibm_kingston (finding 20); the original check would have returned DISAGREE in all three runs, and on each of the eight cells where it missed, the active-neighbour Ramsey was the closer instrument.

- Amendment A20: `docs/findings.md` says what was known before findings 13 and 14 (the Ramsey wait against the Hahn
  echo, dynamical decoupling, ADAPT's choice of which idle qubits to refocus, and a study of how to insert refocusing
  for idle qubits of different kinds), and its bullet on placement adds refocusing every idle qubit and ADAPT's choice
  to the comparisons not yet run. `docs/index.md` section 9 says when a version is released, and its release steps
  verify the tree's signed files before tagging. The build report records that check for v0.5.0, run after the release.
  No finding and no behaviour of the package changed.
- Amendment A21: `docs/findings.md`, in what was known before findings 13 and 14, cites a mid-circuit reset experiment
  on ibm_fez (Nature Physics, 2026) as context. No finding and no behaviour of the package changed.
- Amendment A22: `manacitra.wait.build_wait_ramsey` builds the Ramsey over the wait test's own wait, with the neighbours
  active (the new default: the wait test as scheduled, every two-qubit gate on the waiting qubit replaced by a delay of
  its length) or idle (0.5.0's instrument, unchanged); `predicted_fidelity` gives the prediction from F_ref and the two
  Ramsey readings; and `build_wait_test` and `build_wait_ramsey` take a known phase on the waiting qubit (`phase`,
  default 0, which inserts nothing). Findings 15 to 19 (Kickoffs 49 to 53), with their data in `data/ibm_fez/` (the
  counts, the run records and each run's code, as verbatim lines of the scripts as run), the six posted rule files
  published unchanged, their recomputes in `tests/_reuse_runs.py`, and one figure.
- Amendment A23: findings 20 and 21 (Kickoffs 55 and 54), with their data in `data/ibm_kingston/k55-revised-check.json`
  and `data/ibm_fez/k54-revised-check-day-2.json` (the counts, the run records, each run's code as verbatim lines of the
  scripts as run, Kickoff 55's chain draw and window, and Kickoff 54's first submission, cancelled in the queue), the
  two posted rule files published unchanged, their recomputes in `tests/_reuse_runs.py`, and a test that rebuilds both
  runs' circuits with the package. `data/ibm_fez/calibration-history-01.json` is a read-only record of what each of
  ibm_fez's published calibration stamps changed from 9 to 14 October 2026, and findings 16, 18 and 19 and the README
  now say, from it, what the stamps they cite changed. The README opens with the latest findings and why the default
  changed. No behaviour of the package changed.

## 0.5.0 (11 October 2026)

Finding 14, from the wait test on ibm_fez on 11 October 2026, with its data. No behaviour of the package changed.

- Amendment A19: finding 14, from the wait test on ibm_fez on 11 October 2026 (Kickoff 48), with its data in
  `data/ibm_fez/k48-wait-test.json`, its recompute in `tests/_reuse_runs.py`, a test that rebuilds its circuits with
  `manacitra.wait`, and one figure. Ruling R1 edited two sentences of the finding before the merge. No behaviour of the
  package changed.

## 0.4.0 (10 October 2026)

Code to rerun the wait on hardware: Kickoff 47's Part B and the wait test, built by the package for a backend and a
chain you name, with a dated reconstruction of Part B's circuits; and provider text cleaned of account identifiers
on every backend. No finding changed.

- Amendment A18: `manacitra.wait` builds Kickoff 47's Part B for any qubits and waits, and the wait test, a three-line
  circuit written here, on a chain the user names; its analysis gives the Ramsey and echo losses and Kickoff 47's kind
  of loss, with the rule's thresholds as parameters. `examples/04_wait_test.py` builds both for a backend as a dry run,
  sends them only with `--submit`, through the submit-once guard (`IBMCircuitsBackend`), and analyses the counts;
  `docs/reproduce.md` says how to rerun them and what a rerun is. A new data file,
  `k47-wait-part-b-reconstruction.json`, holds a dated reconstruction of Part B's circuits with the builder's text;
  `k47-wait.json` is unchanged. No finding changed.
- Amendment A18, ruling R1: on every backend, a provider's error text is cleaned before the ledger stores it or the
  console shows it, with nothing of the original chained to it, and the log records of the IBM and Open Quantum clients,
  the IBM client's libraries, `requests` and `urllib3` are cleaned as they are made, no other logger's (ruling R2);
  instance names, CRNs, account and hub/group/project identifiers, tokens and email addresses become `[redacted]`. Open
  Quantum's balance-floor refusal names the account by its ledger scope, not by the saved account's name.
  `wait_loss_kind` refuses intervals that are not two finite, ordered bounds; a translation in `manacitra.wait` that
  routes a circuit is refused.

## 0.3.0 (10 October 2026)

Findings 11 to 13, from reuse circuits on ibm_fez on 10 October 2026, with their data. No behaviour of the package changed.

- Amendment A17: findings 11 to 13, from reuse circuits on ibm_fez on 10 October 2026 (Kickoffs 43 to 47), with their data in `data/ibm_fez/`, their recompute in `tests/_reuse_runs.py`, one figure and `tools/fetch_reuse_circuits.py`. No behaviour of the package changed.

## 0.2.0 (10 October 2026)

The default of `manacitra pick` changed: it now ranks pairs by |1 − k|. To get 0.1.x's ranking, use
`--by kept-share-highest`. On the Kickoff 33 map the new default swaps one pair (106-107 for 22-23), whose distances
from 1 differ by 0.003 against shot noise of 0.05. `verdicts.top_n` and every archived reproduction are unchanged.

- Amendment A15: `pick` ranks the kept share by its distance from the ideal, |1 − k|, after the dead-pair filter, and
  reports pairs with k above 1.2 or below 0; `--by kept-share-highest` gives the rule as run in Kickoff 33.

## 0.1.2 (8 October 2026)

Corrections from the second public trial and two source reviews. No behaviour, data or archived number changed; finding 4
gains the reference figures Kickoff 33's rule specified, read from the archive.

- Amendment A12: three sentences are back on the README itself, not only on its linked pages: where `--data` goes
  (before the subcommand), that a provider backend sends nothing without `--submit`, and that the published runs
  predate the release's checkable sealing. `docs/index.md` section 9 lists the release steps, the version DOI line
  among them.
- Amendment A13: finding 6 and the sentences that repeat it now state the Open Quantum placement as a reading of the
  correlation evidence, not a measurement; the route records no placement.
- Amendment A14: finding 4 reports the reference lines Kickoff 33's rule specified: the plain level's pick on both IBM
  chips, and the same-day map's pick; the table carries the absolute gain beside the percentage.

## 0.1.1 (8 October 2026)

The documentation release. No behaviour, data or published number changed. Archived on Zenodo under the concept DOI
[10.5281/zenodo.23228518](https://doi.org/10.5281/zenodo.23228518), which the citation now uses.

- The README is shorter and links out: a table of the ten findings, the limits, two pictures (the chip map and the
  pipeline), install and how to reproduce; the findings in full, the method in six pictures, the kickoffs and the install details moved, unchanged, to
  `docs/findings.md`, `docs/method.md`, `docs/kickoffs.md` and `docs/install.md`. A test checks every link, and that
  each row of the table matches its finding.

## 0.1.0 (8 October 2026)

Tagged `v0.1.0`; archived on Zenodo, DOI [10.5281/zenodo.23228519](https://doi.org/10.5281/zenodo.23228519).

The first version.

- The core: the two test circuits with exact three-CZ synthesis and their ideal values; the kept share and its shot
  noise; the statistics; the map rule, the payoff rule and the persistence rule (with Amendment A1 and the original
  rule beside it); disjoint pairs, rounds of disjoint pairs, pair choice; the random stand-in workload.
- Amendment A7, the core: every analysis reports a `flagged` block beside its verdict, the headline statistics
  without the pairs a vendor flagged as not measured or not working (an IBM two-qubit error of exactly 1.0; a Braket CZ
  fidelity of exactly 0.5); `layout.published_score_braket` and `layout.vendor_flag`; `manacitra pick --by level`, to
  rank by the plain level; and a tie at the decile's edge in the persistence rule now goes to the earlier pair, as
  Kickoff 36's specification says. The identifier scan gained patterns for Amazon identifiers.
- Amendment A8: every archived record with counts declares its bit reading (`meta.bit_reading`: IBM's adjacent bits,
  Open Quantum's reversed index, Amazon Braket's measured qubits, or per pair), and `archive.p11_table` reads by it,
  refusing a record that declares none; `manacitra pick`, `verdict` and `report` read an archived map that way and give
  its run's own analysis (they had read every archive with IBM's bit positions). `data/PROGRAMS.md` catalogues every
  program file in `data/`, generated by `tools/program_catalogue.py`. The seeded resampling fields are marked one by
  one in `tests/expected_fields.json`, not matched by name.
- Amendment A9: the repository's home is `github.com/dogma-guru/manacitra`.
- Amendment A10, the public posture: forks are welcome, and pull requests from outside the repository are not
  accepted at this time (one opened from a fork is closed with a note); questions go to Issues, through three issue
  forms. `SECURITY.md` gives the private route for a security report. A release is built from its tag (the sdist, the
  wheel and their `SHA256SUMS`), attached to the release and signed with Sigstore.
- Amendment A11: `manacitra report` prints the run's context and its verdict, as `verdict` does, before its table;
  `manacitra map` says on its first line whether it is a local simulation or a dry run; the data README documents how
  to recompute Kickoff 33's payoff from the raw counts, and says why the IBM job IDs stay; `.zenodo.json` gives the
  release's archive its description, and the title is now "Manacitra: a map of your qubits".
- Backends: a simulator (Qiskit Aer or numpy, always available) and IBM Quantum (Qiskit Runtime), with the submit-once
  guard, the usage read and the time cap. Experimental: Open Quantum, and a Cirq simulation of a published noise model.
- The dataset: the counts and analyses of the runs on ibm_fez and ibm_kingston (5 October 2026), of the run on Rigetti
  Cepheus-1-108Q through Open Quantum (Kickoff 34b, the same day; Amendment A2), of the run on the same processor
  that tested placement against drift (Kickoff 37, 6 October 2026; Amendment A5) and of the simulated control, with a
  test that recomputes every statistic listed in `tests/expected_fields.json` and compares it at 10⁻⁶; the fields
  not recomputed are named, with reasons, in `tests/excluded_fields.json` (Amendment A4). Amendment A7 adds four runs
  and finishes a fifth, each recomputed from its counts: Kickoff 35 (all 176 couplers of ibm_fez, once a day on 5, 6
  and 7 October; HOLDS), Kickoff 38 (footprint or activity, through Open Quantum; ACTIVITY), and Kickoffs 40, 41 and 42
  (the same Rigetti processor through Amazon Braket, pinned: placement, map and payoff; the map a day later and the
  payoff with the day-old scores; the offset scan), with the compiled programs Braket returned as placement records.
- Pinned circuits: every circuit the package runs ships as an exact gate list, so every platform runs the same
  gate sequences (`src/manacitra/pinned_circuits.json`, `tools/pin_circuits.py`).
- Sealing: `manacitra seal | reveal | verify`, salted SHA-256 commitments. Signing: a gated CI workflow that signs
  commit records, data files and release artifacts with Sigstore's keyless signing (off until `MANACITRA_SIGN` is
  `true`). `data/SHA256SUMS` for catching corrupted files.
- Safety (Amendment A3): every spending submission goes through the submit-once guard; Open Quantum checks the
  balance, the quote and the budget across waves again immediately before sending, and keeps credit reservations in
  the ledger. The dataset is found from a clone, `MANACITRA_DATA` or `--data`, with a clear stop when it is missing.
- Safety (Amendment A4): the guard's check and its reservation are one step under an interprocess lock on the ledger,
  so concurrent processes cannot both send one job or overspend one budget; IBM's cap counts the estimates of open
  reservations. `tools/make_review_archive.sh` makes a review archive from a fresh single-branch clone, and
  `tools/scan_secrets.py --git` checks the reachable git identities against an approved list.
- Safety (Amendment A6): every spending check on a shared quantity is decided under the ledger's lock, against every
  open reservation. Open Quantum's balance floor now counts the open reservations on the same account, so concurrent
  processes cannot together spend below it. A fetch settles only the reservation of the send it fetched.
- The README, the long-form documentation, six diagrams and three examples. The README explains how the results were
  made: kickoffs (Amendment A2).
- Ownership (Kickoff 01, Amendment A1): copyright Dogma LLC (doing business as Dogma Guru), developed by Anish Patel.
  Contributions under Apache 2.0, inbound as outbound, with a Developer Certificate of Origin sign-off checked in CI.
  The full CC BY 4.0 legal code in `data/LICENSE` and `docs/LICENSE`.
