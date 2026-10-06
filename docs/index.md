# Manacitra, the long version

This page explains the circuit and why its gap is known, the three rules and their thresholds, the backends, the
safety guards, how to reproduce the README's measured statistics from `data/`, and how sealing and signing work. The
README is the short version.

## 1. The circuit, and why the gap is known

Two qubits have four basis states, 00, 01, 10 and 11. Treat them as the four corners (sites) of a square. The
Hamiltonian

    H = −(X₀ + X₁) − c·X₀X₁ + (a/2)(1 + Z₀Z₁)

moves amplitude along the square's sides (X₀ flips one qubit, X₁ the other), across its diagonal (X₀X₁ flips both,
with strength c), and puts an on-site potential a on the two sites 00 and 11. Start in 00 and evolve for

    t* = π / (2 √(1 + c²))

and almost everything arrives at 11. Read P(11), the share of shots that read 11.

| circuit | c | t* | P(11), no offset (a = 0) | P(11), offset | P(11), wrong sign | gap |
|---|---|---|---|---|---|---|
| A | 1/8 | 4π/√65 = 1.558666 | 0.962235 | 1.000000 (a = −1/2) | 0.855691 (a = +1/2) | 0.037765 |
| B | 1/4 | 2π/√17 = 1.523896 | 0.857963 | 1.000000 (a = −1) | 0.523441 (a = +1) | 0.142037 |

The values are computed exactly, by statevector, from the 4×4 matrix (`manacitra.circuits.ideal_table()`; every one
agrees with the table to better than 5·10⁻⁷). With the offset the transfer is perfect; without it, a little amplitude
is left behind. So the **gap**, the difference between the two outcomes, is known in advance: 0.037765 for A and
0.142037 for B.

Each variant is the exact two-qubit unitary exp(−iHt*), synthesised with **exactly three CZ gates** by Qiskit's
`TwoQubitBasisDecomposer` with the number of basis uses forced to three. Three CZ suffice for any two-qubit unitary,
so both variants of a circuit carry the same three entangling gates and differ only in single-qubit angles. Whatever
a pair does to the gap is therefore about how its gates carry a small, known difference. The code refuses any
transpiled circuit in which a pair carries anything other than three two-qubit gates, or in which any two-qubit gate
lies outside the pairs (`circuits.require_three_per_pair`).

**Why the circuits are pinned.** Qiskit's three-CZ synthesis is numerical, and its single-qubit layers differ from
one platform's linear algebra to another's; the unitary is the same, but an error after each CZ lands differently on
different layers, so the package ships every circuit it runs as an exact gate list (`pinned_circuits.json`, checked
by `tools/pin_circuits.py --check`). The pinned circuits come from the same code, Qiskit version and machine as the
published runs, but they cannot be shown gate-for-gate identical to the circuits sent in Kickoffs 31 to 33, whose
records keep transpile checks rather than the circuits themselves.

## 2. The kept share

For one pair,

    k = (P_off − P_no) / gap

with P_off and P_no the measured P(11) of the offset and no-offset variants. k = 1: the pair kept the whole
difference. k = 0: it kept none of it. k can exceed 1, or fall below 0, by noise or by an error that happens to push
the variants apart or together.

**The job.** All pairs run at once. Kickoff 34's 16-circuit order is the default (`circuits.ORDER_16`):

    A no, A off, B no, B off, B off, B no, A off, A no, A no, A off, B no, B off, B off, B no, A off, A no

Kickoff 31 used the same 16 and then the two wrong-sign variants (`ORDER_18`). At 8000 shots per circuit, each
variant has 32,000 shots per pair.

**The split halves**, fixed in advance: for A, positions 1, 2, 15, 16 against 7, 8, 9, 10; for B, positions 3, 4, 13,
14 against 5, 6, 11, 12. Each half takes one copy from each end of the order, so slow drift cancels from the
comparison.

**Shot noise.** The SD of k from counting alone is √(P_off(1 − P_off)/N_off + P_no(1 − P_no)/N_no) / gap
(`keptshare.shot_noise_sd`). On ibm_fez on 5 October 2026, at 32,000 shots per variant, it was 0.055 for k_A,
against a spread between pairs of 0.205.

## 3. The three rules

Each rule is a pure function in `manacitra.verdicts` that returns the verdict, the rule's name, every input it used,
and each condition as tested. The thresholds were fixed before the data they were first applied to, according to the author's dated records, which are not part of this release.

### The map rule (Kickoff 31)

The statistics, across pairs (Pearson r, with Spearman's ρ reported beside each):

- **r_split**: k_A from one half against k_A from the other. Does the map repeat within the job?
- **r_AB**: k_A against k_B, with a one-sided permutation p (10,000 shuffles, seeded). Does it carry over to a
  second circuit with a different gap and its own no-offset reference?
- **r_Ax**: k_A against the published score x (two-qubit error plus both readout errors).
- **r_AB·x**, the partial correlation: k_A and k_B each regressed on x, the residuals correlated. Does the transfer
  survive once the published score is removed?

The verdict, tested in this order:

| verdict | condition |
|---|---|
| NOISE | r_split < 0.3 |
| REDUNDANT | r_split ≥ 0.5, and either \|r_Ax\| ≥ 0.5, or r_AB ≥ 0.4 with r_AB·x < 0.15 |
| DIAGNOSTIC | r_split ≥ 0.5, r_AB ≥ 0.4 with p < 0.05, r_AB·x ≥ 0.3, and \|r_Ax\| < 0.5 |
| NOT SETTLED | anything else |

**When the provider publishes no per-pair figures** (Kickoff 34, Amendment A1), there is no x, and the verdict is
capped: NOISE as above; **MAP PRESENT** if r_split ≥ 0.5 and r_AB ≥ 0.4 with p < 0.05; NOT SETTLED otherwise. Pairs
whose mean P(11) for "A no" is below 0.5 are excluded first (a random outcome gives 0.25, so such a pair is not
working, and broken pairs would hand the correlations a trivial map); fewer than 20 working pairs gives NOT SETTLED.

What would discredit the map: NOISE (it does not repeat) or REDUNDANT (the published score already holds it).

### The payoff rule (Kickoff 33)

A map measured earlier (k_prior) chooses 8 pairs; the published score chooses another 8 (the 8 lowest x). Then every
pair runs 8 random two-qubit circuits, each three Haar-random unitaries with three CZ apiece (`workload.py`). A pair's
score W is the mean classical (Hellinger) fidelity, (Σ_s √(p_s q_s))², between the ideal and the measured
distribution.

- **G** = mean W of the map's 8 − mean W of the published 8, with a 90% bootstrap interval over the 8 circuits
  (10,000 resamples, seed 33).
- **The partial r(W, k_prior | x)**, with a one-sided permutation p on the residuals.

| verdict | condition |
|---|---|
| USEFUL | partial r ≥ 0.3 with p < 0.05, and G's 90% interval lies above 0 |
| NOT USEFUL | partial r < 0.15, or G's 90% interval lies entirely at or below 0 |
| NOT SETTLED | anything else |

Reported beside the verdict: the readout-corrected W_rc, the same correlations for the no-offset level L, and the
error ratio (1 − W of the map's pick) / (1 − W of the published pick), from which the README's "35.6% less error"
comes. What would discredit the map's use: NOT USEFUL.

### The persistence rule (Kickoff 35, with Amendment A1)

The map is measured on several days. Per day: k per pair; r_split between the first copies (positions 1 to 6) and
the second (7 to 12); the day's reliability by the Spearman-Brown formula, rel = 2·r_split/(1 + r_split). Across
days: r(k_a, k_b), and the **corrected r** = r / √(rel_a · rel_b), which removes the part of the day-to-day drop that
is only noise; and the **worst-decile overlap**, the share of the first day's worst tenth of pairs still in the last
day's worst tenth (round(0.1·n) pairs).

**Under Amendment A1** (the verdict Manacitra returns):

| verdict | condition |
|---|---|
| NOT SETTLED (too noisy) | fewer than two days have reliability ≥ 0.5 |
| FADES | the first two days that pass have corrected r < 0.5 |
| HOLDS | the earliest and latest days that pass have corrected r ≥ 0.7 and a worst-decile overlap ≥ 40% |
| PARTIAL | anything else |

**The original rule** is returned beside it (`original_rule`): FADES if corrected r(k₁, k₂) < 0.5; HOLDS if corrected
r(k₁, k₃) ≥ 0.7 and the worst-decile overlap from Day 1 to Day 3 ≥ 50%; PARTIAL otherwise; with two days, HOLDS or
FADES from r(k₁, k₂) alone. The original rule did not say what follows when a day's reliability is not positive and
its corrected r is undefined; here a condition on an undefined value is not met. Amendment A1 was written to close
that gap, after Kickoff 36's simulation found that a day's split-half r can fall below zero by chance at Kickoff 35's
shot count. In both forms FADES is tested before HOLDS, and a result meeting both is flagged.

What would discredit the map's persistence: FADES.

## 4. Choosing pairs

- `layout.disjoint_pairs_by_score`: Kickoff 31's rule. Score every coupled pair by x, take the lowest, never use a
  qubit twice.
- `layout.disjoint_pairs_in_order`: Kickoff 34b's rule for a provider that publishes no score. Take edges in index
  order and accept a pair if neither qubit is taken.
- `layout.edge_rounds`: every coupled pair, split into the fewest rounds of disjoint pairs, so a whole chip can be
  mapped in a few circuits. A heavy-hex map has no qubit with more than three neighbours and no odd cycle, so three
  rounds suffice; on ibm_fez's 176 couplers the rounds hold 60, 59 and 57 pairs. The round count is computed and
  reported, never assumed; a plain greedy colouring is also available (`method="greedy"`).
- `layout.pick_pairs`: the n pairs with the highest k (or the lowest x).

## 5. The backends

Every backend offers `target()` (the coupling map, the native two-qubit gate, the per-pair and per-qubit figures
with their timestamps, or `None` where a provider publishes none), `estimate(job)`, `submit(job)` and `fetch(handle)`.
`fetch` returns counts in one form for every provider: per circuit, per pair, the four outcomes indexed s = a + 2b,
with a the bit of the pair's first qubit and b its second.

- **simulator** (always available). Each pair is simulated on its own as an exact two-qubit density matrix, with
  Qiskit Aer's density-matrix method if installed and numpy otherwise; the two agree to 10⁻¹⁵. Noise per pair:
  two-qubit depolarizing after each CZ; single-qubit depolarizing after each merged single-qubit layer; readout
  flips; and, as an option, a coherent Z over-rotation δ on both qubits after each CZ, the planted map of Kickoff 36.
  Noise-free, k_A moves by −4.01 per radian of δ (and k_B by −1.50), as Kickoff 36 found. Shots are drawn with numpy
  from one sub-seed per circuit position and pair, so runs reproduce.
- **ibm** (`[ibm]`): Qiskit Runtime's SamplerV2. See the guards below. `SnapshotService` runs a dry run on the
  offline snapshot that qiskit-ibm-runtime ships, with no account; it cannot submit.
- **openquantum** (`[openquantum]`, experimental): Rigetti processors through Open Quantum's Public plan, ported from
  Kickoff 34b. Programs are written on physical qubits in one fixed native template, so all variants share one gate
  sequence and differ only in rz angles. Two caveats: the platform's recompilation and qubit placement cannot be
  inspected on the Public plan, so the three-CZ check applies to the program as sent, not as run; and no calibration
  snapshot is returned, so there is no x and the map rule is capped. Tested only against recorded-shape responses.
  The extra is limited to the SDK versions every adapter call was checked against offline (openquantum-sdk 0.4.3,
  openquantum-sdk-qiskit 0.3.3; live responses are still untested), and the module stops at import, naming them, if
  the installed SDK lacks the two private methods it calls (`_wait_for_preparation`, `_resolve_organization_id`).
  On Open Quantum, use a map only with the exact program that measured it. The same named pairs read by a different
  program gave unrelated levels (Kickoff 37), so a map cannot yet be used there to choose pairs for a different
  program. Placement cannot be pinned, because the platform's preprocessing breaks the provider's verbatim mode. In
  Kickoff 34b, pair levels held within a job (r = 0.93) but not between runs a few hours apart (r between 0.10 and
  0.23 on the shared pairs, computed after seeing the data).
- **cirq_sim** (`[cirq]`, experimental): **a simulator only, not hardware access.** It loads the median calibration
  that Cirq ships for a Quantum Virtual Machine processor (willow_pink by default) and simulates each pair under
  either Kickoff 36's Pauli model built from those published figures or the QVM's own noise model. Under the same
  published Pauli noise it gives the same distributions as the simulator backend, to 10⁻¹².

## 6. The safety guards

- **Dry run by default.** `manacitra map` sends nothing without `--submit`.
- **The estimate first.** Before a send, the estimate is printed: on IBM, 0.3 ms per shot plus 5 s (the observed
  rate was about 0.28 ms); on Open Quantum, the platform's own quote in credits.
- **Submit once.** `backends/base.py` refuses a second send of the same job hash. `--allow-resubmit` (in Python,
  `allow_resubmit=True`) overrides that and is itself recorded, with the reason given (`--resubmit-reason`). The check
  and the reservation are one step: under an exclusive lock on a file beside the ledger (`fcntl.flock` on POSIX,
  `msvcrt.locking` on Windows, so it holds between processes as well as threads), the guard reads the ledger again,
  refuses a job already sent or reserved, does the budget accounting against every reservation, and writes and fsyncs
  the reservation and a "sending" record (job hash, provider, processor, UTC time). Only then is the lock released and
  the job sent, so two commands started together cannot both send one job, or both spend the last of one budget. A
  caller that cannot take the lock within 30 seconds is refused and sends nothing. A refusal before sending (a cap, a
  quote, a budget) is recorded as "refused", which is not a send. A reservation from a send that failed, or whose
  outcome is unknown, stays until a fetch settles it, and a second attempt needs the override. This holds for the
  library as well as the command line: a spending backend's public `submit()` is the guard, and its raw send is the
  private `_send()`. The simulators, which send nothing to a provider, keep a direct `submit()`. The ledger lives in
  `./.manacitra/ledger.jsonl` (or `$MANACITRA_LEDGER`) and holds no credentials.
- **The IBM cap.** The usage is read from the runtime client before every submission (numbers and dates only; every
  identifier field is dropped). The provider's figure lags a submission, so a job is refused if the usage, plus the
  estimates of every open IBM reservation in the ledger, plus this job's estimate, exceeds the cap: 540 s of the Open
  plan's 600 s window by default. The estimate is reserved before sending, and a fetch that reports the job's charged
  time settles it. No usage read, no submission.
- **The Open Quantum tests.** Every task must be quoted at the expected credits, on the Public plan, within the
  budget, leaving the balance above the floor; a second wave is refused until the first has completed. The checks run
  again immediately before sending: the balance is read again; the quote must be younger than 10 minutes and every
  task still prepared at the expected price; the credits already committed in the ledger for the run (its budget scope,
  provider:processor:job name; settled charges and open reservations, read under the ledger's lock) plus this job must
  stay within the budget; and the balance after must stay at or above the floor. Any failure refuses the send and names the check. A job's credits are reserved in the ledger before it is
  sent; after a failed send, which may have created tasks, the reservation stays until a fetch settles it.
- **Three CZ per pair.** Every transpiled circuit is checked: exactly three two-qubit gates per pair, none outside the
  pairs, no swaps, the layout kept.
- **Credentials.** Only from each provider's own saved-account mechanism or environment variables. Nothing in this
  repository reads a credential file, and nothing prints, logs or stores a token, an account or instance identifier,
  a client ID or secret, or an email address.
- **The identifier scan.** `tools/scan_secrets.py` fails on credentials, identifiers, email addresses and home paths
  anywhere in the tree. It runs in CI and, once `git config core.hooksPath .githooks` is set, on every commit.

## 7. Reproducing the README's numbers

The dataset ships with the repository, not with the package. From a clone installed with `pip install -e .` it is
found by itself; with a plain install, point at a clone's `data/` with `MANACITRA_DATA` (or `manacitra --data`).
Without it, Manacitra stops and says how to get it, and the tests that need it are skipped with that reason.

```bash
pip install -e ".[dev]"
pytest tests/test_reproduction.py     # every field in tests/expected_fields.json, from the counts, to 1e-6
pytest tests/test_field_inventory.py  # every field of data/ listed once: compared, or excluded with a reason
pytest tests/test_readme_numbers.py   # the README's statistics, times, ranges and counts
python tools/acceptance_table.py      # the table of archived against reproduced values
python examples/02_map_from_archive.py
python examples/03_pick_pairs.py
python docs/make_diagrams.py          # the six diagrams, from data/
```

Every measured statistic in the README is checked by a test; times, ranges and counts are taken from the data files
and listed in `tests/test_readme_numbers.py`. Times are rounded to the nearest minute, everywhere.

Where each README number comes from:

| README number | file in `data/` | how |
|---|---|---|
| gap 0.037765; ideal 0.962, 1.000 | (the model) | `circuits.ideal_table()` |
| pair [106, 107] k = 1.06; pair [20, 21] k = 0.22; 32,000 shots | `ibm_fez/k31-map.json` | `archive.map_from_record` |
| r_split 0.87 / 0.90, r_AB 0.82 / 0.89, r_Ax −0.18 / −0.05, DIAGNOSTIC | `ibm_*/k31-map.json` | `archive.map_from_record` |
| r = 0.68 against the run ten hours earlier | `ibm_fez/k29-settle.json`, `k31-map.json` | `archive.previous_k_for`, S4 |
| closed fraction 0.01 (−0.21, 0.21) and 0.03 (−0.09, 0.16) | `ibm_*/k32-isolation.json` | `archive.isolation_analysis` |
| 35.6% less error; G +0.0012 (+0.0004, +0.0021); USEFUL | `ibm_fez/k33-payoff.json` (prior map from `k32-isolation.json`) | `archive.payoff_from_record` |
| 16% less; G +0.0004 (+0.0001, +0.0008); partial 0.29, p 0.073; NOT SETTLED | `ibm_kingston/k33-payoff.json` | the same |
| NOISE without a planted map, DIAGNOSTIC with one | `simulated/k36-arm1.json`, `k36-arm2.json` | `archive.map_from_record` |
| Rigetti: 22 working pairs of 27; r_split 0.985, r_AB 0.971; MAP PRESENT; without 101-102, MAP PRESENT | `rigetti_cepheus_1_108q/main.json` | `archive.rigetti_map` |
| Rigetti, after the fact: 20 pairs, r_split 0.84, r_AB 0.79, MAP PRESENT | `rigetti_cepheus_1_108q/after-the-fact.json` | `archive.rigetti_map` |
| Rigetti: r = 0.93 between the waves; 0.10 to 0.23 across runs | `rigetti_cepheus_1_108q/main.json`, `screen.json` | `archive.rigetti_map` |
| Rigetti, Kickoff 37: r = 0.997 to 0.998 minutes apart, 0.97 and 0.76 across about 9 hours, 0.07 and −0.25 between the programs; PLACEMENT; 0.99 and 0.98 against Kickoff 34b; the five excluded pairs at 0.70 to 0.84 under the screen program | `rigetti_cepheus_1_108q/k37-placement.json` (with `main.json` and `screen.json` for the lines against Kickoff 34b) | `archive.placement_or_drift` |

The two simulated persistence sets (`simulated/k36-persistence.json`) give PARTIAL under the original rule on both,
as Kickoff 36 reported. Under Amendment A1 the same data give NOT SETTLED (too noisy) for the static days (only Day 3
passes the reliability floor) and FADES for the scrambled days. Those two A1 verdicts are computed here; they are not
in Kickoff 36's own report.

## 8. What kind of claim each part is

- **Lived facts**: the counts in `data/`, as two IBM processors and one Rigetti processor returned them on 5 and 6
  October 2026, and the simulation outputs, as run on the author's computer on 5 October.
- **Established findings**: the model values (the ideal P(11) of each variant) and the published calibrations used
  (IBM's figures at submission; the QVM's median calibration).
- **Falsifiable theory**: that the kept share is a per-pair property that published figures do not carry, that it
  picks better pairs for other work, and that it lasts long enough to plan by. Each part names what would discredit it
  (section 3). On two IBM processors on one day, the first held on both, the second held on one and was not settled
  on the other, and the third is open. On the Rigetti processor, a per-pair map was present within one job; with no
  published figures there, whether they carry it cannot be tested.

## 9. Sealing and signing

A SHA-256 hash beside a file only catches accidents: whoever can change the file can recompute the hash. To show a
stranger **who** sealed something and **when**, the hash has to sit somewhere the producer cannot edit, with a public
timestamp. Manacitra does this in two layers.

### Commitments (in the package)

```bash
manacitra seal predictions.md      # before the run
manacitra reveal predictions.md    # after the run
manacitra verify predictions.md    # anyone, any time after the reveal
```

- **`seal`** draws a 32-byte random salt (`secrets.token_bytes`), keeps it in `.seals/predictions.md.salt` (the
  `.seals/` folder is git-ignored), and writes `predictions.md.commit.json`: the algorithm, the hash SHA-256(salt ‖
  file), the UTC time and the tool's version. It prints the hash, to be posted somewhere the producer cannot edit, such
  as the chat with the reader. A file is sealed once; sealing it again is refused.
- **`reveal`** checks that the salt opens the commitment and then adds it to the commit record, for publication.
- **`verify`** recomputes the hash from the file and the revealed salt and says plainly whether they match. A commit
  record whose salt has not been revealed cannot be checked yet, and `verify` says so.
- The salt is why the hash can be posted early: without it, a short prediction ("DIAGNOSTIC") could be guessed by
  hashing the few possible answers.

### Keyless signing with a public timestamp (in CI)

`.github/workflows/sign.yml` signs with Sigstore's keyless signing, through the official action
(`sigstore/gh-action-sigstore-python`, pinned to v3.5.0). The workflow has `id-token: write`, gets a short-lived
certificate tied to its own GitHub identity, and writes each signature to Sigstore's public transparency log with a
timestamp. There is no key to store, rotate or keep secret.

- **What is signed:** every `*.commit.json` file and every file in `data/` when it lands on the default branch (those
  with no bundle yet, or changed in that push; `tools/sign_targets.py` lists them), and every release artifact. Each
  bundle is committed beside the file it covers, as `FILE.sigstore.json`. Release bundles are attached to the release.
- **The gate:** a log entry is public and names this repository and workflow, so signing runs only when the
  repository variable `MANACITRA_SIGN` is `true`. It stays unset while the repository is private. The workflow's
  `gate` job runs on every push and states its decision in the log.

**To verify a signed file** (here, one data file):

```bash
pip install sigstore
sigstore verify identity data/ibm_fez/k31-map.json \
  --cert-identity https://github.com/dogmaguru/manacitra/.github/workflows/sign.yml@refs/heads/main \
  --cert-oidc-issuer https://token.actions.githubusercontent.com
```

`sigstore` finds the bundle `data/ibm_fez/k31-map.json.sigstore.json` beside the file. The expected certificate
identity is this repository's signing workflow on the default branch, and the issuer is GitHub Actions' OIDC issuer.
For a release artifact, the identity ends in `@refs/tags/<the release tag>`. For a sealed prediction, verify both: the
commit record's signature (`sigstore verify identity predictions.md.commit.json ...`), which shows who published the
commitment and when, and the commitment itself (`manacitra verify predictions.md`), which shows the file is the one
committed to.

**Plain SHA-256 stays** for catching corrupted files: `data/SHA256SUMS` (checked by `python tools/sha256sums.py
--check` and by the tests) and the `sources` hashes in every data file's `meta` block.
