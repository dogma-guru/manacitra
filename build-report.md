# Build report: Kickoff 01, the initial implementation

Branch `feat/initial-implementation`, 5 October 2026. Built by Claude Code (Opus 5.5) in the confirmed clone of the
repository (`manacitra/` in the author's projects folder), default branch `main`. Nothing was submitted to any
provider; every test runs on simulation or on the archived results. Updated for the kickoff's section 7b (sealing and
signing; see section 8), for Amendment A1 (ownership and the open items; see section 10) and for Amendment A2 (the
Rigetti result, and what a kickoff is; see section 11).

**Summary.**
- Every reproduction test passes. Every archived statistic recomputes from the archived counts. Across 2,992 numeric
  values, the largest difference is 1.1·10⁻¹⁶, against the 10⁻⁶ bar.
- 152 tests pass, Ruff is clean, and the identifier scan is clean on the whole tree.
- The first CI run failed one test on Linux. The cause was real: the three-CZ synthesis gives different single-qubit
  layers on different platforms. The circuits are now pinned (section 7).
- Section 7b is in place: `seal`, `reveal` and `verify`, with their tests, and a signing workflow that stays off. Its
  gate was dry-run on this branch and skipped as required (section 8).
- The two rulings asked for in section 6 were given in Amendment A1:
  - kingston's payoff is 16%;
  - the repository address stays.
  Section 10 records the amendment's changes.

## 1. Paths: what the kickoff named, and what was read

| kickoff names | read from | note |
|---|---|---|
| `<W1>-classical-runner/kickoff29/hardware-31/` | the same | Kickoff 31 |
| `.../kickoff29/hardware/` (as Kickoff 32) | `.../kickoff29/hardware/` holds Kickoff 29's settling runs; Kickoff 32 is in `.../kickoff29/hardware-32/` | both were read |
| `<W1>-ibm/hardware-33/` | `<W1>-classical-runner/kickoff29/hardware-33/` | the `<W1>-ibm/` folder has no `hardware-33/` |
| `hardware-35` (for the IBM backend) | `<W1>-classical-runner/kickoff29/hardware-35/` | read for the layout, the usage read and Amendment A1; no data copied |
| `<W1>-oq/hardware-34b/`, `<W1>-google/run-36/` | the same | |

Folder names are written with `<W1>` for the first word of the kickoff's section 1 list (see section 3).

All source folders were read only. The dataset builder ran from the session's scratch directory, not from the
repository, because it names the source folders.

## 2. The acceptance table

Produced by `python tools/acceptance_table.py`. The first table gives the headline statistics. The second covers every
numeric value compared in each case: every number in the archived analysis that the port also computes. A difference
of 0.0e+00 means the two values are bit-identical; the path shown beside it is then arbitrary.

The kickoff's acceptance bar, case by case:

- **Kickoff 31.** ibm_fez and ibm_kingston are both DIAGNOSTIC, and r_split, r_AB and r_Ax reproduce.
- **Kickoff 33.** ibm_fez is USEFUL with G = +0.0012, and ibm_kingston is NOT SETTLED.
- **Kickoff 36.** Arm 1 is NOISE and arm 2 is DIAGNOSTIC.

Every case meets the bar. The other cases (the settling-run baseline, Kickoff 32, arm 3 and the persistence days)
were reproduced too.

| case | statistic | archived | reproduced | difference |
|---|---|---|---|---|
| Kickoff 31, ibm_fez | verdict | DIAGNOSTIC | DIAGNOSTIC | same |
| Kickoff 31, ibm_fez | r_split(k_A) | 0.867691 | 0.867691 | 0.0e+00 |
| Kickoff 31, ibm_fez | r_AB | 0.821290 | 0.821290 | 0.0e+00 |
| Kickoff 31, ibm_fez | p(r_AB), one-sided | 0.000000 | 0.000000 | 0.0e+00 |
| Kickoff 31, ibm_fez | r_Ax | -0.178918 | -0.178918 | 0.0e+00 |
| Kickoff 31, ibm_fez | r_AB.x | 0.816163 | 0.816163 | 0.0e+00 |
| Kickoff 31, ibm_fez | mean k_A | 0.821755 | 0.821755 | 0.0e+00 |
| Kickoff 31, ibm_fez | S4: r against the settling run | 0.677643 | 0.677643 | 0.0e+00 |
| Kickoff 31, ibm_kingston | verdict | DIAGNOSTIC | DIAGNOSTIC | same |
| Kickoff 31, ibm_kingston | r_split(k_A) | 0.899652 | 0.899652 | 0.0e+00 |
| Kickoff 31, ibm_kingston | r_AB | 0.894305 | 0.894305 | 0.0e+00 |
| Kickoff 31, ibm_kingston | p(r_AB), one-sided | 0.000000 | 0.000000 | 0.0e+00 |
| Kickoff 31, ibm_kingston | r_Ax | -0.047039 | -0.047039 | 0.0e+00 |
| Kickoff 31, ibm_kingston | r_AB.x | 0.897572 | 0.897572 | 0.0e+00 |
| Kickoff 31, ibm_kingston | mean k_A | 0.827333 | 0.827333 | 0.0e+00 |
| Kickoff 31, ibm_kingston | S4: r against the settling run | 0.896921 | 0.896921 | 0.0e+00 |
| Kickoff 31 step 0, ibm_fez settling run | baseline r_split | 0.739101 | 0.739101 | 0.0e+00 |
| Kickoff 31 step 0, ibm_fez settling run | baseline r(k, x) | -0.267361 | -0.267361 | 0.0e+00 |
| Kickoff 31 step 0, ibm_kingston settling run | baseline r_split | 0.683759 | 0.683759 | 0.0e+00 |
| Kickoff 31 step 0, ibm_kingston settling run | baseline r(k, x) | -0.130583 | -0.130583 | 0.0e+00 |
| Kickoff 32, ibm_fez | verdict | THE GATE | THE GATE | same |
| Kickoff 32, ibm_fez | Gap_D | 0.436361 | 0.436361 | 0.0e+00 |
| Kickoff 32, ibm_fez | Gap_S | 0.431810 | 0.431810 | 0.0e+00 |
| Kickoff 32, ibm_fez | F | 0.010430 | 0.010430 | 0.0e+00 |
| Kickoff 32, ibm_kingston | verdict | THE GATE | THE GATE | same |
| Kickoff 32, ibm_kingston | Gap_D | 0.457186 | 0.457186 | 0.0e+00 |
| Kickoff 32, ibm_kingston | Gap_S | 0.444084 | 0.444084 | 0.0e+00 |
| Kickoff 32, ibm_kingston | F | 0.028658 | 0.028658 | 0.0e+00 |
| Kickoff 33, ibm_fez | verdict | USEFUL | USEFUL | same |
| Kickoff 33, ibm_fez | G (top 8 by map minus top 8 by x) | 0.001221 | 0.001221 | 0.0e+00 |
| Kickoff 33, ibm_fez | G 90% interval, low | 0.000442 | 0.000442 | 0.0e+00 |
| Kickoff 33, ibm_fez | G 90% interval, high | 0.002134 | 0.002134 | 0.0e+00 |
| Kickoff 33, ibm_fez | r(W, k_prior) | 0.618411 | 0.618411 | 0.0e+00 |
| Kickoff 33, ibm_fez | partial r(W, k_prior | x) | 0.603074 | 0.603074 | 0.0e+00 |
| Kickoff 33, ibm_fez | p(partial), one-sided | 0.001200 | 0.001200 | 0.0e+00 |
| Kickoff 33, ibm_fez | mean W | 0.995174 | 0.995174 | 0.0e+00 |
| Kickoff 33, ibm_kingston | verdict | NOT SETTLED | NOT SETTLED | same |
| Kickoff 33, ibm_kingston | G (top 8 by map minus top 8 by x) | 0.000447 | 0.000447 | 0.0e+00 |
| Kickoff 33, ibm_kingston | G 90% interval, low | 0.000132 | 0.000132 | 0.0e+00 |
| Kickoff 33, ibm_kingston | G 90% interval, high | 0.000759 | 0.000759 | 0.0e+00 |
| Kickoff 33, ibm_kingston | r(W, k_prior) | 0.292295 | 0.292295 | 0.0e+00 |
| Kickoff 33, ibm_kingston | partial r(W, k_prior | x) | 0.292302 | 0.292302 | 0.0e+00 |
| Kickoff 33, ibm_kingston | p(partial), one-sided | 0.073200 | 0.073200 | 0.0e+00 |
| Kickoff 33, ibm_kingston | mean W | 0.996823 | 0.996823 | 0.0e+00 |
| Kickoff 36, arm 1 | verdict | NOISE | NOISE | same |
| Kickoff 36, arm 1 | r_split(k_A) | 0.100870 | 0.100870 | 0.0e+00 |
| Kickoff 36, arm 1 | r_AB | -0.036457 | -0.036457 | 0.0e+00 |
| Kickoff 36, arm 1 | r_Ax | -0.003486 | -0.003486 | 0.0e+00 |
| Kickoff 36, arm 1 | r_AB.x | -0.037068 | -0.037068 | 0.0e+00 |
| Kickoff 36, arm 2 | verdict | DIAGNOSTIC | DIAGNOSTIC | same |
| Kickoff 36, arm 2 | r_split(k_A) | 0.640893 | 0.640893 | 0.0e+00 |
| Kickoff 36, arm 2 | r_AB | 0.755024 | 0.755024 | 0.0e+00 |
| Kickoff 36, arm 2 | r_Ax | -0.151363 | -0.151363 | 0.0e+00 |
| Kickoff 36, arm 2 | r_AB.x | 0.757355 | 0.757355 | 0.0e+00 |
| Kickoff 36, arm 3 | verdict | DIAGNOSTIC | DIAGNOSTIC | same |
| Kickoff 36, arm 3 | r_split(k_A) | 0.928093 | 0.928093 | 0.0e+00 |
| Kickoff 36, arm 3 | r_AB | 0.834712 | 0.834712 | 0.0e+00 |
| Kickoff 36, arm 3 | r_Ax | -0.123020 | -0.123020 | 0.0e+00 |
| Kickoff 36, arm 3 | r_AB.x | 0.833915 | 0.833915 | 0.0e+00 |
| Kickoff 36, persistence, static days | verdict, original rule | PARTIAL | PARTIAL | same |
| Kickoff 36, persistence, static days | corrected r(k2, k3) | 0.516698 | 0.516698 | 0.0e+00 |
| Kickoff 36, persistence, scrambled days | verdict, original rule | PARTIAL | PARTIAL | same |
| Kickoff 36, persistence, scrambled days | corrected r(k2, k3) | 0.018566 | 0.018566 | 0.0e+00 |

| case | numeric values compared | largest difference | within 1e-6 |
|---|---|---|---|
| Kickoff 31, ibm_fez | 114 | 0.0e+00 (`.wrong_sign_kept_A[9]`) | yes |
| Kickoff 31, ibm_kingston | 114 | 0.0e+00 (`.wrong_sign_kept_A[9]`) | yes |
| Kickoff 31 step 0, ibm_fez settling run | 33 | 0.0e+00 (`.r_split.spearman`) | yes |
| Kickoff 31 step 0, ibm_kingston settling run | 33 | 0.0e+00 (`.r_split.spearman`) | yes |
| Kickoff 32, ibm_fez | 110 | 0.0e+00 (`.se_gap_S`) | yes |
| Kickoff 32, ibm_kingston | 110 | 0.0e+00 (`.se_gap_S`) | yes |
| Kickoff 33, ibm_fez | 882 | 1.1e-16 (`.mean_W_rc`) | yes |
| Kickoff 33, ibm_kingston | 882 | 0.0e+00 (`.readout_confusion[9][3][3]`) | yes |
| Kickoff 36, arm 1 | 80 | 0.0e+00 (`.shot_noise_sd_per_pair.B`) | yes |
| Kickoff 36, arm 2 | 80 | 0.0e+00 (`.shot_noise_sd_per_pair.B`) | yes |
| Kickoff 36, arm 3 | 80 | 0.0e+00 (`.shot_noise_sd_per_pair.B`) | yes |
| Kickoff 36, persistence, static days | 287 | 0.0e+00 (`.per_day.3.shot_noise_sd`) | yes |
| Kickoff 36, persistence, scrambled days | 287 | 0.0e+00 (`.per_day.3.shot_noise_sd`) | yes |

## 3. The vocabulary boundary: every word renamed or stripped

The seven words of the kickoff's section 1 are referred to here as W1 to W7, in the kickoff's order, so that this file
passes the scan too.

| where | word | what was done |
|---|---|---|
| source folder names (`<W1>-classical-runner`, `<W1>-google`, `<W1>-oq`, `<W1>-ibm`) | W1 | Not recorded anywhere in the repository. `data/` gives each source by file name and SHA-256 only, and the builder that names the folders stays outside the repository. |
| the ported scripts' "carried sentence" (each run report's first paragraph names W4) | W4 | Not ported. The code's docstrings describe the circuit as what it is: a four-site Hamiltonian encoded in two qubits. |
| Kickoff 34b's job name | none | The source had already chosen a neutral name. The adapter's default is `kept-share`. |
| `CITATION.cff`, `pyproject.toml`, `README.md`: the repository URL | W7 (the hosting organisation's name, as one word) | **Kept, and allow-listed in the scan as that one exact URL.** This needs the author's ruling; see section 6. |
| the archived data | none | The scan found none of the seven words in any copied file. |

The only other change made in copying data was not a vocabulary change. Every IBM usage block (8 files) lost its
`details` list, which carries IBM's metric UUID. The charged seconds, value, unit and status were kept.

## 4. The identifier scan on the full tree

```
$ python tools/scan_secrets.py
identifier scan: clean (86 files)
```

The tree has 91 tracked files; the 5 PNG diagrams are binary and skipped. The result is the same with `CI=1`, which
turns off the run-time user-name pattern.

**What the scan catches:**
- IBM CRNs and 44-character API keys;
- instance, client-ID, client-secret, organization-ID and token fields;
- UUIDs, bearer tokens, JWTs and private keys;
- email addresses;
- macOS, Linux and Windows home paths;
- the seven words;
- the user name of whoever runs it (outside CI);
- any literals given in `MANACITRA_SCAN_EXTRA`.

**What it allows:**
- IBM job IDs (20 lower-case characters);
- the repository URL;
- the synthetic `00000000-0000-0000-0000-…` identifiers in the test fixtures.

**What it skips:** binary files, and `*.sigstore.json` bundles. The bundles are public signatures, base64 certificates
and log entries written by the signing workflow; their base64 would trip the token patterns by chance.

**How it is checked:**
- The pattern file writes each word with a character class, so the file matches none of its own patterns; a test
  checks this.
- The pre-commit hook (`.githooks/pre-commit`, enabled with `git config core.hooksPath .githooks`) ran on every commit
  on this branch.
- CI runs the scan on the whole tree.

## 5. Experimental adapters, and what could not be tested without the network

**Open Quantum** (`backends/openquantum.py`, from Kickoff 34b's runner). Ported:
- account loading through `OpenQuantumService.from_saved_account`;
- discovery and the target;
- the fixed native program template, the OpenQASM 3 writer and parser, and the program checks;
- the quote and its tests (credits per task, Public plan, budget, balance floor);
- the wave submission, with the rule that wave 2 waits for wave 1;
- the classical-index counts reading and the bit-order covariance check.

The docstring carries both caveats: recompilation and placement cannot be inspected on the Public plan, and no
calibration snapshot is returned.

**Tested against recorded-shape responses.** The fixtures keep the field names and shapes of the 34b records, but every
value and identifier is synthetic, so that none of 34b's running data enters the repository. The SDK's enums and
request models are stubbed in the test.

**Not tested without the network:**
- the real SDK calls: `from_saved_account`, `get_backend_class`, `upload_job_input`, `prepare_job`, the private
  `_wait_for_preparation` and `_resolve_organization_id`, `create_job`, `get_job`, `download_job_output` and
  `get_credit_balance`;
- the real enum values (platform UUIDs);
- whether the platform still returns a plain counts dict.

**Cirq simulation** (`backends/cirq_sim.py`, from Kickoff 36). It is a simulator only, and its docstring says so. It
was tested in full, because the QVM calibration ships with cirq-google. On the device, it gives 105 qubits and 182
couplers, as Kickoff 36 recorded. Noise-free, the ideal values hold to 10⁻⁶. Under the same published Pauli noise, it
gives the same distribution as the simulator backend to 10⁻¹². It needs `ply`, which the source environment had and
the `[cirq]` extra now lists.

**IBM** (not marked experimental). It was tested against a fake runtime and the offline FakeFez snapshot, covering:
- the transpile checks;
- the ledger before sending;
- the refusal of a second send, and the logged override;
- the cap, and a missing usage read;
- the pub format (circuit, None, shots);
- the target's figures and the counts parsing.

**Not tested without the network:**
- a real SamplerV2 run;
- the live `service.usage()` field names (the port assumes `usage_consumed_seconds`, as the sources read it);
- `job.metrics()`;
- the classical register's name `c` on live results (the port falls back to the first register).

## 6. What needs the author's ruling, and what could not be verified

**Needed a ruling (given in Amendment A1; see section 10).**

1. **ibm_kingston's payoff: 16%, not 18%.** Ruled: 16% stands. The kickoff says "On ibm_kingston, 18% less". The figure that gives
   ibm_fez's 35% is the mean of (1 − W) for the map's 8 pairs against that of the published pick. From the archived
   counts it gives:
   - ibm_fez: 35.6% (0.00221 against 0.00343);
   - ibm_kingston: 16.1% (0.00234 against 0.00278).

   Other readings do not give 18% either:

   | reading | ibm_kingston |
   |---|---|
   | the readout-corrected W_rc | 21.8% |
   | the published pick's error over the map's | 1.19 (19% more) |
   | the mean of per-circuit ratios | 3.3% |

   Kickoff 33's report gives no kingston percentage. The README states 16% and 35.6%, and
   `tests/test_readme_numbers.py` checks both. Nothing in the code was changed to fit.
2. **The repository URL.** Ruled: the address stays. `github.com/dogmaguru/manacitra` carries W7 as one word. CITATION.cff must name the
   repository, so the URL is kept in `CITATION.cff`, `pyproject.toml` and the README, and allow-listed in the scan as
   that exact string. Options:
   - keep it;
   - move the repository to another organisation;
   - drop the URL from those three files, which leaves CITATION.cff without a repository.

**Decisions taken, logged here.**

- **Diagram 1 uses dots joined by the gap, not bars.** A gap of 0.038 in P(11) is invisible on bars that start at 0,
  and bars on an axis that starts at 0.80 misstate size. The two outcomes and the gap are as the kickoff asked; only
  the mark differs.
- **The persistence rule's gap.** Under the original rule, a condition on an undefined corrected r is "not met". This
  is Kickoff 36's reading, and the one A1 formalised. Kickoff 35's runner instead clamped a non-positive reliability to
  10⁻⁹, which would have produced a very large corrected r. The two readings agree whenever every reliability is
  positive, as on ibm_fez's Day 1 (0.972).
- **Decile size.** The decile is round(0.1·n), as in Kickoff 35's runner and A1. Kickoff 36's module used ceil(0.1·n).
  The two agree for 27 and for 176 edges.
- **Test order.** FADES is tested before HOLDS, as in Kickoff 35's runner and A1. A result that meets both is flagged.
- **A1 on the simulated persistence data (new numbers, not reproductions).**
  - Static days: NOT SETTLED (too noisy), because only Day 3 passes the reliability floor.
  - Scrambled days: FADES.
  - The original rule gives PARTIAL on both, as archived.
- **Edge colouring.** The kickoff says "greedy"; Kickoff 35's source used rustworkx's bipartite edge colouring. The
  port keeps the source's method as the default and offers greedy as an option. On ibm_fez it gives 3 rounds of 60, 59
  and 57 pairs, as in Kickoff 35's log; greedy reports its own round count.
- **Ties in choosing pairs by score** go to the lower pair, as in Kickoff 36. Kickoff 31's original used insertion
  order. The two differ only on exactly equal scores.
- **The simulator's single-qubit noise** applies once per merged single-qubit layer. Kickoff 36 applied it once per
  merged PhasedXZ gate, which is the same structure; the cross-check above confirms it.

**Added beyond the kickoff's layout.**
- `src/manacitra/archive.py`: reads `data/` back into the core. It holds Kickoff 32's isolation analysis as a
  reproduction, not as a fourth public rule.
- `tests/_reproduce.py` and `tools/acceptance_table.py`.
- `tests/test_readme_numbers.py`.

**Data beyond the list.**
- Both settling runs (fez and kingston): fez's is needed for Kickoff 31's step 0 and S4.
- The two coupling maps, from qiskit-ibm-runtime 0.50.0's offline snapshots: needed for the chip map, and for building
  the docs with no account.
- `k36-planted.json`.

No Kickoff 35 data was copied, because that run is still going.

**Licence text.** The full CC BY 4.0 legal code was not copied into `data/LICENSE` and `docs/LICENSE`. They state the
licence and link to the legal code; nothing was downloaded.

**Could not verify.**
- **Python 3.11 and 3.13 locally.** Only Python 3.14 is on this machine; CI runs 3.11 and 3.13 (section 7).
- **GitHub's rendering** of the README and the SVGs. The PNG fallbacks were inspected locally.
- **`CITATION.cff` against its schema**: `cffconvert` is not installed.
- **Any live provider call** (section 5).
- **The 18% figure** (above).

## 7. The first CI run, and why the circuits are now pinned

The first CI run (Linux, Python 3.11 and 3.13) passed every reproduction test and failed one other test. The
planted-error sensitivity dk_A/dδ came out at −4.06 per radian on 3.13 and −5.90 on 3.11, against −4.01 on this
machine, all with Qiskit 2.5.2.

**The cause.** Qiskit's three-CZ synthesis is numerical, and its single-qubit layers vary with the platform's linear
algebra. On 3.13 even numpy and scipy were the same versions as here. The unitary is the same on every platform, so
ideal values and the reproduction of archived counts are not affected. But a coherent error after each CZ lands
differently on different layers. A map made with circuits synthesised on one machine is therefore not strictly
comparable with one made on another, and re-synthesising elsewhere would not run what the hardware ran.

**The fix.** `src/manacitra/pinned_circuits.json` ships every circuit the package runs as an exact gate list:
- the six test variants;
- the eight workload circuits;
- the Open Quantum native template.

They were generated on this machine with Qiskit 2.5.2, the machine and version the published runs used, and `block()`
loads them. `block(label, synthesise=True)` still synthesises afresh. `tools/pin_circuits.py --check`, which the tests
run, confirms each is its exact unitary (to 6.7·10⁻¹⁶).

**Checks against the sources:**
- The pinned Open Quantum template matches the programs Kickoff 34b actually sent, angle for angle, on all four
  variants.
- The pinned IBM-side blocks match the gate counts Kickoff 36 recorded on all four variants (13 rz, 8 or 11 sx, 3 CZ).
- They give Kickoff 36's sensitivity (−4.01 and −1.50 per radian).

**What could not be verified:** that the pinned blocks are gate for gate the circuits Kickoffs 31 to 33 sent to IBM.
Those runs' records keep transpile checks, not the circuits. The pinned blocks come from the same code, Qiskit
version and machine, and they agree with everything that was recorded.

## 8. Sealing and signing (section 7b)

**Commitments.** `src/manacitra/seal.py` and `manacitra seal | reveal | verify`:
- `seal` draws a 32-byte salt with `secrets.token_bytes` and keeps it in `.seals/FILE.salt` (git-ignored).
- It writes `FILE.commit.json`: the algorithm, SHA-256(salt ‖ file), the UTC time and the tool version.
- It prints the hash to post.
- `reveal` checks the salt before adding it to the record.

The seal tests (`tests/test_seal.py`, 9, all passing):

| test | result |
|---|---|
| round trip: seal, reveal, verify gives MATCH; the salt is not in the record before the reveal | pass |
| a one-byte change to the file: NO MATCH | pass |
| a wrong salt, given by hand or written into the record: NO MATCH | pass |
| a commit record with the salt missing: fails, saying it has not been revealed yet | pass |
| reveal refuses a file changed since sealing, and leaves the record unrevealed | pass |
| a file is sealed once; a second seal is refused | pass |
| two files with the same content get different hashes (fresh salts) | pass |
| the command line: seal, verify (fails before reveal), reveal, verify (MATCH) | pass |
| `.seals/` is ignored by git | pass |

**Keyless signing.** `.github/workflows/sign.yml` uses `sigstore/gh-action-sigstore-python`, pinned to v3.5.0's
commit, with `id-token: write`.
- **What it signs:** every `*.commit.json` and every file in `data/` on the default branch, choosing those with no
  bundle yet or changed in the push (`tools/sign_targets.py`), and every release artifact.
- **Where the bundles go:** it commits the `FILE.sigstore.json` bundles beside the files, and attaches release bundles
  to the release.
- **Checking its own output:** it verifies each signature against this workflow's identity right after signing.
- **Documentation:** `docs/index.md` section 9 gives the exact `sigstore verify identity` command, with the expected
  certificate identity (`https://github.com/dogmaguru/manacitra/.github/workflows/sign.yml@refs/heads/main`) and
  issuer (`https://token.actions.githubusercontent.com`). The command's form was checked against sigstore 4.5.0's
  CLI.

**The gate, dry run.** The push of commit `26b8954` to this branch ran the workflow (run 37380885335) with the
repository variable unset. The gate job logged:

```
MANACITRA_SIGN:
MANACITRA_SIGN is not 'true': signing is off. Nothing is sent to Sigstore.
```

Both signing jobs, `sign-files` and `sign-release`, were **skipped**, and nothing was sent to Sigstore. `gh variable
list` shows no repository variables, and the repository is private.

**Not verified:**
- **Signing itself.** It cannot be exercised without turning the gate on, which writes a public log entry naming the
  repository.
- **The bundle commit-back and the release attachment.** They will first run when the author sets
  `MANACITRA_SIGN=true`.
- **Branch protection.** If `main` has rules, the push of the bundles by `github-actions[bot]` may be refused; this
  needs checking then.

**Plain hashes.** `data/SHA256SUMS` was added (18 files, checked by a test and by `tools/sha256sums.py --check`)
beside the `sources` hashes in each data file's `meta` block.

**Diagram 5**, "How to check a sealed prediction" (`docs/diagrams/sealed-prediction.svg`): a timeline of seal and post
the hash, run the job, reveal the salt, and anyone verifies, with one line under each step on what it shows. It is
in the README after the payoff.

## 9. Versions used

Python 3.14.7, qiskit 2.5.2, qiskit-aer 0.17.2, qiskit-ibm-runtime 0.50.0, numpy 2.5.3, scipy 1.18.1, rustworkx 0.18.1,
cirq-core and cirq-google 1.7.0, ply 3.11, matplotlib 3.11.2, ruff 0.16.10, pytest 9.1.1; sigstore 4.5.0 (in a
scratch environment, only to check the verification command's form). qiskit, numpy and scipy are
the same versions the source runs recorded.

## 10. Amendment A1: ownership, and the open items

**The author's rulings, as received.**
- The copyright holder is Dogma LLC (doing business as Dogma Guru), a New York limited liability company; Anish
  Patel stays the author.
- ibm_kingston's payoff is 16%. The README's figure and the test that checks it (`tests/test_readme_numbers.py`) stay
  as they were.
- The repository address stays.

**The changes, one by one.**

| # | change | what was done |
|---|---|---|
| 1 | copyright lines | "Copyright 2026 Anish Patel" replaced by "Copyright 2026 Dogma LLC" in all 46 files that carried it: every source file header, `NOTICE`, `CONTRIBUTING.md`, `data/LICENSE` and `docs/LICENSE`. No other copyright line remains. |
| 2 | `NOTICE` | The first lines are now "Manacitra / Copyright 2026 Dogma LLC (doing business as Dogma Guru) / Developed by Anish Patel." The rest is unchanged. |
| 3 | `CITATION.cff` | Unchanged: Anish Patel is the author, and nothing about ownership is in it. |
| 4 | `pyproject.toml` | Confirmed: `authors = [{ name = "Anish Patel" }]` and `license = "Apache-2.0"` (with `license-files = ["LICENSE", "NOTICE"]`). Nothing changed. |
| 5 | README | The licence section now names the code's licence (Apache 2.0), the data and docs' licence (CC BY 4.0), and the copyright holder, Dogma LLC (Dogma Guru). The last line is "Manacitra is developed by Anish Patel and published by Dogma Guru." |
| 6 | the vocabulary boundary | See below. |
| 7 | contributions | Apache 2.0, inbound as outbound, with no CLA. Each commit carries a DCO sign-off. A CI check fails a pull request with an unsigned commit and exempts the signing bot. See below. |
| 8 | the CC BY 4.0 text | Fetched from creativecommons.org (`legalcode.txt`, HTTP 200, 396 lines, SHA-256 `9ba9550a…`). The full legal code is now in `data/LICENSE` and `docs/LICENSE`, under a short preamble naming the licence and the copyright holder. |
| 9 | this section | |

**6. The vocabulary boundary, narrowed.** I read W7 as covering its first word on its own, since the amendment lists
"Dogma LLC" among the strings W7 may appear in. The scan's W7 pattern was widened to match: before, it caught only the
two words together; now it also catches the first word alone, in any case and spacing. A word that merely begins the
same way does not match ("dogmatic").

The allow-list holds exactly these strings, case-sensitive:
- "Dogma LLC";
- "Dogma LLC (doing business as Dogma Guru)" (the NOTICE line);
- "Dogma LLC (Dogma Guru)" (the README's licence line);
- "published by Dogma Guru" (the README's publisher line);
- the repository URL.

The trade name is not allowed on its own, only inside those ownership and publisher lines. The pattern file writes them
with a character class, so it matches none of its own patterns.

The new tests (`tests/test_scan.py`):
- W7 is still flagged in eight other contexts: the trade name in other prose, the one-word form outside the
  repository URL, another repository under the same organisation, upper case, an underscore, the first word alone, a
  reworded ownership line, and a capitalised "Published by".
- Each of the five allowed strings passes.
- "dogmatic" is not flagged.

The other six words stay banned everywhere, as before.

**7. Contributions.**
- **`CONTRIBUTING.md`:**
  - contributions are accepted under the Apache License 2.0, inbound as outbound, with no contributor licence
    agreement;
  - data and documentation are contributed under CC BY 4.0, the licence they are published under (my addition, so
    that each part keeps one licence);
  - each commit carries a `Signed-off-by:` line certifying the Developer Certificate of Origin 1.1, linked rather than
    copied;
  - the header template now names Dogma LLC.
- **The check:** `.github/workflows/dco.yml` runs `tools/check_dco.py` on every pull request. It fails if any commit
  in the pull request lacks a `Signed-off-by: Name <address>` line at the start of a line. Commits authored by
  `github-actions[bot]` (the Sigstore bundle commits) are exempt.
- **Tests** (`tests/test_dco.py`, on a throwaway repository):
  - signed commits pass;
  - an unsigned commit fails and is named;
  - a sign-off quoted mid-line does not count;
  - the bot is exempt.

**Signing off this branch.** All 12 earlier commits on this branch lacked a sign-off, so the new check would have
failed this pull request. On the author's go, the branch was rebased with `git rebase --signoff main`, so every commit
now carries a `Signed-off-by:` line under the branch's git identity. It was then force-pushed with
`--force-with-lease`. The commit hashes changed and the contents did not: the rebased tree is identical to the one
tested. `python tools/check_dco.py main HEAD` passes locally.

**The scan on the full tree afterwards.**

```
$ python tools/scan_secrets.py
identifier scan: clean (89 files)
$ CI=1 python tools/scan_secrets.py
identifier scan: clean (89 files)
```

After the amendment: 170 tests pass, Ruff is clean, and `data/SHA256SUMS` was regenerated for the changed
`data/LICENSE`.

**Not in this amendment, and not done:**
- merging the pull request;
- making the repository public;
- turning on signing;
- anything about the IP assignment.

## 11. Amendment A2: the Rigetti result, and what a kickoff is

**The source, checked before anything was copied.**
- The hand-back archive's SHA-256 is `9357a5f7…df97b28`, as the amendment gives it. The `.sha256` file beside it and
  a second copy elsewhere in the author's folders give the same hash.
- Every line of the folder's `SHA256SUMS` checks (109 files), and the folder is identical to the unpacked archive.
- The folder was read only. The builder ran from the session's scratch directory, as before, because it names the
  source folder.

**The new acceptance rows** (`python tools/acceptance_table.py`):

| case | statistic | archived | reproduced | difference |
|---|---|---|---|---|
| Kickoff 34b, Rigetti Cepheus-1-108Q | verdict | MAP PRESENT | MAP PRESENT | same |
| Kickoff 34b, Rigetti Cepheus-1-108Q | working pairs | 22.000000 | 22.000000 | 0.0e+00 |
| Kickoff 34b, Rigetti Cepheus-1-108Q | r_split(k_A) | 0.985388 | 0.985388 | 0.0e+00 |
| Kickoff 34b, Rigetti Cepheus-1-108Q | r_AB | 0.970614 | 0.970614 | 0.0e+00 |
| Kickoff 34b, Rigetti Cepheus-1-108Q | p(r_AB), one-sided | 0.000000 | 0.000000 | 0.0e+00 |
| Kickoff 34b, Rigetti Cepheus-1-108Q | mean k_A | -0.284317 | -0.284317 | 0.0e+00 |
| Kickoff 34b, Rigetti Cepheus-1-108Q | leave-one-out (without 101-102): verdict | MAP PRESENT | MAP PRESENT | same |
| Kickoff 34b, Rigetti Cepheus-1-108Q | leave-one-out: r_split(k_A) | 0.972867 | 0.972867 | 0.0e+00 |
| Kickoff 34b, Rigetti Cepheus-1-108Q | leave-one-out: r_AB | 0.956238 | 0.956238 | 0.0e+00 |
| Kickoff 34b, Rigetti Cepheus-1-108Q | r(L_s, L_main) | -0.057658 | -0.057658 | 0.0e+00 |
| Kickoff 34b, Rigetti Cepheus-1-108Q | r(L_wave1, L_wave2) | 0.930650 | 0.930650 | 0.0e+00 |
| Kickoff 34b, after the fact: 20 pairs | verdict, rule applied | MAP PRESENT | MAP PRESENT | same |
| Kickoff 34b, after the fact: 20 pairs | r_split(k_A) | 0.842281 | 0.842281 | 0.0e+00 |
| Kickoff 34b, after the fact: 20 pairs | r_AB | 0.791168 | 0.791168 | 0.0e+00 |
| Kickoff 34b, after the fact: 20 pairs | p(r_AB), one-sided | 0.000400 | 0.000400 | 0.0e+00 |

| case | numeric values compared | largest difference | within 1e-6 |
|---|---|---|---|
| Kickoff 34b, Rigetti Cepheus-1-108Q | 686 | 0.0e+00 (`.working_pairs[9][1]`) | yes |
| Kickoff 34b, after the fact: 20 pairs | 11 | 0.0e+00 (`.sd_kA`) | yes |

The 686 values compared for the main job cover:
- the per-circuit P(11) table;
- the whole archived analysis (k_A, k_B, their halves, the spreads, S1 and S2);
- the dead-pair filter;
- the sealed leave-one-out;
- the descriptive lines.

The new tests (`tests/test_rigetti.py`), all passing:

| test | checks |
|---|---|
| `test_the_bit_reading_gives_the_archived_p11_exactly` | the amendment's reading, written out literally, gives the archived P(11) exactly (equality, not tolerance); so does the package's reader; the adapter reads the same key positions |
| `test_the_layout_is_the_published_one` | the 16-circuit order, the halves, 8000 shots, permutation seed 34 |
| `test_the_dead_pair_filter_excludes_five_and_leaves_22` | 0-1, 56-57, 63-64, 87-88 and 99-100 excluded; 22 working |
| `test_the_headline_statistics` | r_split(k_A) = 0.985388 and r_AB = 0.970614, to 10⁻⁶ |
| `test_the_verdict_is_map_present_under_the_capped_rule` | MAP PRESENT, by the capped rule, with no S3 |
| `test_the_sealed_leave_one_out_without_101_102` | the dropped pair is 101-102, and the verdict stays MAP PRESENT |
| `test_after_the_fact_20_pairs_without_13_14_and_101_102` | r_split 0.842 and r_AB 0.791, MAP PRESENT; the file carries its after-the-fact label |
| `test_nothing_left_out_came_in` | no task IDs, credit or balance fields, or provider-record fields in the three files |

`tests/test_readme_numbers.py` gained three tests: the new finding's numbers, the persistence question's Rigetti
numbers, and the name line, word for word.

**What was copied** (`data/rigetti_cepheus_1_108q/`, 7.6 MB):

| file | contents |
|---|---|
| `screen.json` | L_s for each of the 53 candidates; the pair rule, its outcome and the 27 pairs taken; the screen's bit-order check |
| `main.json` | the 27 pairs; the order and halves; the main job's bit-order check; the per-circuit P(11); the counts; and under `archived`: the dead-pair filter (with the working pairs), the analysis (k_A, k_B, the halves, S1, S2, the verdict), the sealed leave-one-out, and the descriptive lines r(L_s, L_main), r(k_A, L_s), r(L_wave1, L_wave2) and the across-run correlations |
| `after-the-fact.json` | the 20-pair check, labelled "computed after seeing the data, outside the verdict"; the source's own label is kept beside it |

Each `meta` block gives:
- the processor, as the amendment words it;
- the UTC times of the screen and of both waves of the main job, from the source's submit record and log;
- 8000 shots per circuit;
- "Kickoff 34b" as the source;
- each source file's SHA-256, the archive's SHA-256 and the source script's.

**What was left out:**
- the 16 main-job task IDs and the screen's (UUIDs);
- the credit balances and charges;
- the raw provider records;
- the programs as sent;
- the runner's sealed predictions and its report.

I also did not copy the screen's counts, because the amendment names only the levels and the pair rule for
`screen.json`; this is my reading. The cost is that L_s is archived as computed, not recomputed from counts. The
counts would add 0.9 MB and could be copied on the author's ruling. The programs as sent were not copied either. The
pinned Open Quantum template already matches them angle for angle (section 7).

**Three readings, logged.**
- **The across-run correlations keep their label.** The amendment places "the across-run correlations on the shared
  pairs" in `main.json`. In the source, the correlations on the 11 pairs shared by the test task, the screen and the
  main job are in the after-the-fact file. So in `main.json` each line records when it was fixed:
  - the 27-pair test-against-screen r (−0.16) was fixed before any main-job data (34b's section 5);
  - the 11-pair figures (0.10 to 0.23) and the screen-against-main r on all 27 chosen pairs (0.004) carry the
    source's after-the-fact label.
  The README's "r between 0.10 and 0.23" says "computed after seeing the data" for the same reason. The
  amendment's wording did not ask for this; the source labels the figures so.
- **The 27-pair test-against-screen r is archived, not recomputed.** It needs Kickoff 34's 27 test levels, which are
  not in 34b's archive. The 11-pair figures recompute, because 34b's after-the-fact file carries those 11 test levels.
- **The source's medians** of k_A and k_B (in its after-the-fact file) were not copied. They follow directly from the
  archived k values.

**The scan on the full tree.**

```
$ python tools/scan_secrets.py
identifier scan: clean (94 files)
$ CI=1 python tools/scan_secrets.py
identifier scan: clean (94 files)
```

The tree has 100 tracked files; the 6 PNG diagrams are binary and skipped. The source report uses W4 once, and it
was not copied. The scan finds none of the seven words in the copied files.

**The README.**
- **Findings.** A new finding 2: the map exists on a second vendor's chip, within one job. The old findings 2 to 4
  are now 3 to 5. "All four findings" is now "All five".
- **The persistence question** now covers both platforms:
  - ibm_fez, r = 0.68 over ten hours;
  - Rigetti through Open Quantum, 0.10 to 0.23 between runs and 0.93 within a job;
  - the two ordinary causes, placement and drift, and that the data cannot separate them;
  - the sentence that the difference is between the platforms' placement records, not the vendors' machines or
    products;
  - Kickoff 35 still running.
- **The second-vendor item** under "What it has not shown" became the question the capped rule cannot answer.
- **Limits.** "Two processors, one day" became "Three processors, one day".
- **The Open Quantum line** was added to the extras paragraph, to the adapter's docstring and to `docs/index.md`
  section 5.
- **New section** "How the results were made: kickoffs". It has the brief's contents, the four practices, the Kickoff
  36 line, diagram 6, the table of Kickoffs 31 to 36, the one sentence on the kickoff texts, and the credit line as
  given.
- **Placement, and a move.** The amendment places the new section after the findings and before installation. In
  this README, installation came before the findings. So "Install and try it" moved down, below the new section. The
  order is now: the findings, Limits, kickoffs, then installation. I read Limits as part of the findings. **This
  reorders the README and needs the author's look.**
- **The name line is unchanged**, as section 4 asks. The earlier version of A2 was never applied here, so nothing
  needed restoring. A test now checks the line word for word.
- **Related updates.** `docs/index.md` sections 7 and 8, `data/README.md` and `CHANGELOG.md` were updated to match.

**Diagram 6** (`docs/diagrams/kickoff.svg`, PNG beside it, made by `docs/make_diagrams.py`):
- the seven steps as a vertical timeline, with one line under each;
- a note on amendments below;
- alt text in the README.

The first draft was a horizontal row. It overlapped, and the author found it crowded. It was redrawn vertically, with
one short line per step. Regenerating left the other five diagrams byte-identical.

**After the amendment:** 184 tests pass, Ruff is clean, `data/SHA256SUMS` covers 21 files, and the acceptance table
covers 15 cases, all within 10⁻⁶.

**Not in this amendment, and not done:**
- merging;
- making the repository public;
- turning on signing;
- any provider submission;
- the Kickoff 35 data;
- publishing kickoff texts or sealed predictions.
