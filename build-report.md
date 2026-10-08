# Build report: Kickoff 01, the initial implementation

Branch `feat/initial-implementation`, 5 October 2026. Built by Claude Code (Opus 5.5) in the confirmed clone of the
repository (`manacitra/` in the author's projects folder), default branch `main`. Nothing was submitted to any
provider; every test runs on simulation or on the archived results. Updated for the kickoff's section 7b (sealing and
signing; see section 8), for Amendment A1 (ownership and the open items; see section 10), for Amendment A2 (the
Rigetti result, and what a kickoff is; see section 11) and for Amendment A3 (fixes from the independent review; see
section 12). Pull request #1 was merged before A2 was applied, so A2 and A3 are on the branch
`feat/amendments-a2-a3`, in a new pull request into `main`.

**Summary.**
- Every reproduction test passes. Every archived statistic recomputes from the archived counts. Across 2,992 numeric
  values, the largest difference is 1.1·10⁻¹⁶, against the 10⁻⁶ bar. *(Narrowed by Amendment A4, section 14: the
  comparison then covered only the fields present on both sides, so "every archived statistic" overclaimed. The
  inventoried fields are now listed in `tests/expected_fields.json`, and the rest, with reasons, in
  `tests/excluded_fields.json`.)*
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
| Kickoff 31, ibm_fez | p(r_AB), one-sided | p < 1/10000 (0 of 10000) | p < 1/10000 (0 of 10000) | 0.0e+00 |
| Kickoff 31, ibm_fez | r_Ax | -0.178918 | -0.178918 | 0.0e+00 |
| Kickoff 31, ibm_fez | r_AB.x | 0.816163 | 0.816163 | 0.0e+00 |
| Kickoff 31, ibm_fez | mean k_A | 0.821755 | 0.821755 | 0.0e+00 |
| Kickoff 31, ibm_fez | S4: r against the settling run | 0.677643 | 0.677643 | 0.0e+00 |
| Kickoff 31, ibm_kingston | verdict | DIAGNOSTIC | DIAGNOSTIC | same |
| Kickoff 31, ibm_kingston | r_split(k_A) | 0.899652 | 0.899652 | 0.0e+00 |
| Kickoff 31, ibm_kingston | r_AB | 0.894305 | 0.894305 | 0.0e+00 |
| Kickoff 31, ibm_kingston | p(r_AB), one-sided | p < 1/10000 (0 of 10000) | p < 1/10000 (0 of 10000) | 0.0e+00 |
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
| Kickoff 33, ibm_fez | p(partial), one-sided | p = 0.0012 (12 of 10000) | p = 0.0012 (12 of 10000) | 0.0e+00 |
| Kickoff 33, ibm_fez | mean W | 0.995174 | 0.995174 | 0.0e+00 |
| Kickoff 33, ibm_kingston | verdict | NOT SETTLED | NOT SETTLED | same |
| Kickoff 33, ibm_kingston | G (top 8 by map minus top 8 by x) | 0.000447 | 0.000447 | 0.0e+00 |
| Kickoff 33, ibm_kingston | G 90% interval, low | 0.000132 | 0.000132 | 0.0e+00 |
| Kickoff 33, ibm_kingston | G 90% interval, high | 0.000759 | 0.000759 | 0.0e+00 |
| Kickoff 33, ibm_kingston | r(W, k_prior) | 0.292295 | 0.292295 | 0.0e+00 |
| Kickoff 33, ibm_kingston | partial r(W, k_prior | x) | 0.292302 | 0.292302 | 0.0e+00 |
| Kickoff 33, ibm_kingston | p(partial), one-sided | p = 0.0732 (732 of 10000) | p = 0.0732 (732 of 10000) | 0.0e+00 |
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

**Verified offline against the real SDK (6 October 2026; see section 13).** Every call was checked against
`openquantum-sdk` 0.4.3 and `openquantum-sdk-qiskit` 0.3.3, installed but never connected:
- each method exists with the argument names it is given: `from_saved_account`, `get_backend_class`,
  `upload_job_input`, `prepare_job`, the private `_wait_for_preparation` and `_resolve_organization_id`,
  `create_job`, `get_job`, `download_job_output` and `get_credit_balance`;
- so does every model field and enum member the adapter reads or sets.

The `[openquantum]` extra is now limited to those versions (A3 addition, section 12).

**Still untested, because they need the network and an account:**
- the live responses;
- the enum values' meaning on the platform (their UUIDs);
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
| Kickoff 34b, Rigetti Cepheus-1-108Q | p(r_AB), one-sided | p < 1/10000 (0 of 10000) | p < 1/10000 (0 of 10000) | 0.0e+00 |
| Kickoff 34b, Rigetti Cepheus-1-108Q | mean k_A | -0.284317 | -0.284317 | 0.0e+00 |
| Kickoff 34b, Rigetti Cepheus-1-108Q | leave-one-out (without 101-102): verdict | MAP PRESENT | MAP PRESENT | same |
| Kickoff 34b, Rigetti Cepheus-1-108Q | leave-one-out: r_split(k_A) | 0.972867 | 0.972867 | 0.0e+00 |
| Kickoff 34b, Rigetti Cepheus-1-108Q | leave-one-out: r_AB | 0.956238 | 0.956238 | 0.0e+00 |
| Kickoff 34b, Rigetti Cepheus-1-108Q | r(L_s, L_main) | -0.057658 | -0.057658 | 0.0e+00 |
| Kickoff 34b, Rigetti Cepheus-1-108Q | r(L_wave1, L_wave2) | 0.930650 | 0.930650 | 0.0e+00 |
| Kickoff 34b, after the fact: 20 pairs | verdict, rule applied | MAP PRESENT | MAP PRESENT | same |
| Kickoff 34b, after the fact: 20 pairs | r_split(k_A) | 0.842281 | 0.842281 | 0.0e+00 |
| Kickoff 34b, after the fact: 20 pairs | r_AB | 0.791168 | 0.791168 | 0.0e+00 |
| Kickoff 34b, after the fact: 20 pairs | p(r_AB), one-sided | p = 0.0004 (4 of 10000) | p = 0.0004 (4 of 10000) | 0.0e+00 |

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

## 12. Amendment A3: fixes from the independent review

**The review.** An OpenAI Codex agent reviewed commit `a982814` (A1 applied, A2 not yet) against the rubric. Its
marks were 30 PASS, 8 FAIL and 3 CANNOT CHECK. Its report and the three probe checks were read from its hand-back
archive, outside the repository. Every core number still reproduces after the fixes (the acceptance table, 15 cases,
all within 10⁻⁶).

**Where this landed.** Pull request #1 was merged into `main` at 23:44 UTC on 5 October, before A2 was applied. A2
and A3 are therefore on a new branch, `feat/amendments-a2-a3`, in a new pull request into `main`, at the author's
instruction (the amendment says #1). Nothing is merged.

**Each finding, what changed, and the test that now covers it.**

| review ID | finding | what was changed | test |
|---|---|---|---|
| E2 (Major) | a backend's public `submit()` bypassed the submit-once guard | `GuardedSubmit` in `backends/base.py`: on IBM and Open Quantum the public `submit()` is the guard (ledger record before sending, a repeat refused unless `allow_resubmit=True`, the override logged), and the raw send is the private `_send()`. The simulators keep a direct `submit()`, and their docstrings say why. The README's "a job already sent once is refused" now names the library as well as the CLI. | `test_ibm_fake.py::test_the_public_submit_is_the_guard`, `test_openquantum_recorded.py::test_the_public_submit_is_the_guard`; the CLI and `submit_once` tests unchanged and passing |
| E3 (Major) | Open Quantum: budgets did not add up across waves; a cached quote was trusted at send time | `_preflight`, run immediately before sending. It re-reads the balance and every task's preparation, then checks five things: the quote's own tests; the quote's age (10 minutes at most); each task's plan and price; the ledger's reservations plus this job against the budget; and the balance after against the floor. Any failure refuses the send and names the check (logged as "refused", not as a send). A passing job's credits are reserved in the ledger before sending; a failed send keeps its reservation; a fetch settles it. | `test_two_waves_against_a_budget_that_fits_one`, `test_the_balance_is_read_again_at_send_time`, `test_an_expired_quote_is_refused`, `test_a_price_change_after_the_quote_is_refused`, `test_a_failed_send_keeps_its_reservation_until_a_fetch_settles_it`, `test_a_fetch_settles_the_reservation` |
| E3, IBM part (passed) | the cap and the unreadable-usage checks | kept as they were; the public `submit()` now reaches them through the guard | `test_cap_refuses_before_anything_is_sent`, `test_no_usage_no_submission`, `test_snapshot_service_never_submits` |
| F1, scope | "every pair at once" | the README's opening, the pipeline's alt text and the pipeline diagram now say: on a set of non-overlapping qubit pairs at once (27 in the published runs); every coupler can be covered in a few rounds. `MapJob`'s docstring says the same. | README wording |
| F1, cause | "the share belongs to the pair's own gate" | Kickoff 32's finding is now "The gap between the best and worst pairs persisted when their neighbours were idle", with the sentence on what it rules out and what it does not separate. THE GATE stays as the sealed rule's name, explained as "not explained by the tested neighbours"; the kickoffs table's question and verdict say the same. | README wording |
| F1, timing | rules and predictions "fixed" or "sealed" before the data, with no records in the release | each such statement (the opening, the pipeline's paragraph, alt text and diagram note, finding 2's leave-one-out, and A2's kickoff section) now says "according to the author's dated records, which are not part of this release". Added: from this release on, new commitments can be checked by anyone with `manacitra seal` and, once signing is on, a public timestamp; the published runs cannot be checked that way. `docs/index.md` section 3 carries the same qualifier. | README wording |
| F1, status | "running" and "under way" undated | Kickoff 35 is "running as of 6 October 2026" (the open question, the kickoffs table, the pipeline diagram). The Rigetti line has been a finding since A2. | README wording |
| F1, workflow | the pipeline implied the verdict gates selection and Manacitra runs the user's job | the README says what each step does: `manacitra pick` ranks pairs from a map, does not check the verdict, and warns; Manacitra does not run your job. In the pipeline diagram, Run is drawn dashed, as "Run (yours)". `pick` now prints a warning on stderr when the verdict is not DIAGNOSTIC or MAP PRESENT. | `test_cli.py::test_pick_warns_when_the_verdict_is_not_usable`, `test_pick_is_quiet_on_a_usable_map` |
| F1, pinning (the review's qualifications) | the pinning rationale was only in this report | two sentences in `docs/index.md` section 1: why the circuits are pinned, and that they cannot be shown gate-for-gate identical to the circuits sent in Kickoffs 31 to 33 | documentation |
| F1, finding 5 | "every number … to a test" was broader than the tests | narrowed in the README and `docs/index.md` to: every measured statistic in the README is checked by a test; times, ranges and counts are taken from the data files and listed in `tests/test_readme_numbers.py`. This report never made the broader claim. New assertions cover the displayed metadata. | `test_every_ibm_run_time_shown` (7 cases), `test_the_rigetti_times_shown`, `test_the_payoff_prior_is_about_two_hours_older`, `test_the_published_score_range_on_the_chip_map`, `test_the_isolation_group_sizes`, `test_finding_2_the_second_vendor` |
| F1, times | the data index truncated 12:36:54 to 12:36, while the README rounded it to 12:37 | one convention everywhere: the nearest minute | the same time tests |
| E5 (Blocker under the rubric) | the public bot address `41898282+github-actions[bot]@users.noreply.github.com` appears twice | kept, and allow-listed in `tools/scan_patterns.py` as that exact string, with a comment. The scan had passed only because its email pattern stopped at `]`, so it never saw the address. The pattern now reads brackets, so any other bracketed address is caught, and the allow-list carries the policy. The DCO test's address, split in two before, is now written whole. | `test_scan.py::test_the_bot_address_is_allowed_and_nothing_else` |
| A5 (Minor) | metadata overclaimed "every file" | each JSON's `meta` carries six fields (processor, provider, kickoff, utc, shots per circuit, sources), with "not applicable" where a field does not apply. The coupling maps carry the snapshot (qiskit-ibm-runtime 0.50.0, `FakeFez` and `FakeKingston`), the SHA-256 of each snapshot's `conf_*.json`, and the extraction time: they were re-extracted at 00:41:38 UTC on 6 October, with edges identical to those first committed. `data/README.md` describes the fields by kind. Only `meta` changed in the IBM and simulated files. | `test_data_meta.py` (39 tests) |
| G2 (Minor) | the chip map encoded values by shade alone | the measured pairs are drawn thicker the better they are, on both maps, and the main map numbers each pair by its rank. `docs/diagrams/chip-map-table.md`, generated with the diagram, lists rank, pair, k, x and rank by x, and the README's caption links to it. The alt text says so. | `test_the_chip_map_table_matches_the_data` |
| H2 (Minor) | missing headers | the short header added to `src/manacitra/backends/__init__.py`, `.githooks/pre-commit` (after the shebang) and the three workflow files | `test_headers.py` (every Python file, the hook and the workflows) |
| H3 (Minor) | NOTICE omitted requests and PLY | requests (Apache 2.0) and PLY (BSD 3-Clause) added. So that the test can cover every package `pyproject.toml` declares, NOTICE also lists the build and development tools (setuptools, wheel, pytest, ruff; MIT), under their own heading. | `test_notice.py` |
| A2 note (portability) | the `git check-ignore` seal test failed outside a git repository | it skips, with its reason, outside a git work tree. Checked on a `git archive` extraction: 8 passed, 1 skipped. | `test_seal.py::test_the_seals_folder_is_ignored_by_git` |
| B6 (passed; the interpretation) | a permutation p of zero reported as 0 | zero exceedances is reported as "p < 1/N (0 of N)", and other values as "p = … (k of N)" (`stats.format_p`). This covers the verdict printout and the acceptance table. The archived values are unchanged, and the rows above in sections 2 and 11 are shown in the new form. | `test_stats.py::test_a_permutation_p_of_zero_is_reported_as_a_bound` |

**The reviewer's fake-service checks, rerun against the fixed code.** These are the reviewer's own calls (its
`probes.py`, the Open Quantum part), with the recorded-shape fake service and each probe given its own ledger:

| probe | at `a982814` | now |
|---|---|---|
| the same eight-task job, `submit()` twice | 16 tasks created, no ledger | 8 created; the second call refused: "this job … was already sent …; pass allow_resubmit … to send it again" |
| two 24-credit waves against a 30-credit budget | 16 tasks, 48 credits of quoted work accepted | 8 created; the second wave refused: "quote test failed: within_budget; budget: 24 reserved + 24 for this job > 30" |
| the balance drops to 0 after the quote, floor 10 | 8 tasks created | none created; refused: "balance floor: balance now 0 - 24 < floor 10" |

**Readings and choices, logged.**
- **IBM and Open Quantum log a refusal differently.** An IBM cap refusal is still logged as an attempt ("sending",
  then "failed"), so a retry needs the override. This is the behaviour the kept tests check. An Open Quantum preflight
  refusal is logged as "refused", which is not a send, and no reservation is made.
- **What the budget counts.** The budget counts every reservation in its scope, settled or not: a settled one was
  spent, and an open one may have been. The scope is provider:processor:job name, so a new run with the same job name
  and ledger shares the budget. The docstring says to give such a run its own ledger or job name. No reservation is
  released automatically.
- **The quote's lifetime of 10 minutes is a local policy.** The platform's own quote lifetime is not known.
- **Not exercised against the network.** Re-reading each preparation uses the SDK's private `_wait_for_preparation`,
  as the quote already did. It is tested only against the fake service.
- **Four displayed times changed** under the nearest-minute rule:
  - ibm_kingston's payoff, 15:22 to 15:23 (README and data index);
  - the Rigetti screen, 18:54 to 18:55;
  - the Rigetti main job, 22:14 to 22:15 (README, the data index, and the notes in the Rigetti files, rebuilt with a
    `utc` field; their counts and analyses are unchanged);
  - in the data index only, ibm_fez's map, 12:36 to 12:37, and the simulated runs, 18:34 to 18:35.
  The Kickoff 34 test task stays 17:01, as its source gives it to the minute.
- **The rubric's three CANNOT CHECK items** are unchanged and still need the network or tools this machine lacks: a
  fresh install (A1), CFF schema validation (H5) and a full licence inventory (H8).

**Two additions to A3, approved by the author on 6 October, before the next review.**

| addition | what was changed | test |
|---|---|---|
| the dataset when it is not beside the source | `archive.data_dir()` looks in three places, in order: `--data` on the command line (`set_data_dir`), then `$MANACITRA_DATA`, then `data/` beside the source (an install from a clone). A folder counts only if it holds `SHA256SUMS`. If none is found, it stops with `DataNotFound`, which says to `git clone` the repository and then install from the clone, or set `MANACITRA_DATA` or `--data`. A wrong folder is named. The command line prints that message and exits 2, and `--data` holds for one command only; a file argument not found as given is looked up inside the dataset. A conftest hook turns `DataNotFound` in a test into a skip with that reason. `data/` stays out of the wheel: it holds only the package and its metadata (checked by building it). The README describes both install routes. | `test_data_location.py`: a clone finds its data; the stop and its wording; the environment variable; a wrong folder; the command line with and without `--data` |
| Open Quantum's SDK versions | `[openquantum]` now requires `openquantum-sdk>=0.4.3,<0.5` and `openquantum-sdk-qiskit>=0.3.3,<0.4`. At import, and again when the service is first created, the adapter checks that the SDK's `SchedulerClient` has `_wait_for_preparation` and `_resolve_organization_id`. If either is missing, it stops with `SDKIncompatible`, naming both methods, the missing one or ones, the version they were checked against, and the install command. With no SDK installed, the import checks nothing, so the adapter's helpers stay usable. | `test_openquantum_recorded.py`: the import stops in a fresh process with a fake SDK that lacks one method, and passes with one that has both; the message when both are missing; the extra's pins |

**Checked in a plain install.** A non-editable install of the working tree, from a fresh export, with every extra:
- it resolved `openquantum-sdk` 0.4.3 and `openquantum-sdk-qiskit` 0.3.3, and `check_sdk()` passes against the real
  SDK;
- with no data: 159 tests pass and 61 skip, each with the dataset's reason, and none fail. Before the addition, 59
  failed;
- with `MANACITRA_DATA` set to the export's `data/`: 257 pass, and 1 skips (the `git check-ignore` test, outside a
  work tree);
- the command line without data exits 2 with the message, and with `--data` gives the verdict; example 2 stops with
  the same message, and runs with `MANACITRA_DATA` set.

**After the amendment:**
- 258 tests pass, and Ruff is clean;
- every pinned circuit is its exact unitary (to 6.7·10⁻¹⁶);
- `data/SHA256SUMS` was regenerated;
- the scan is clean on the full tree (99 files scanned; the PNG diagrams skipped).

**Not in this amendment, and not done:**
- merging;
- making the repository public;
- turning on signing;
- publishing kickoff texts or sealed predictions;
- any provider submission.

## 13. The review's three CANNOT CHECK items, run with the network (6 October 2026)

All of this ran in throwaway environments outside the repository, with Python 3.14.7, the only version on this
machine. Nothing was sent to any provider, and no account was used.

| review ID | check | result |
|---|---|---|
| A1 | a fresh environment, from a `git archive` export of this branch, with `pip install -e ".[ibm,aer,cirq,openquantum,docs,dev]"` from PyPI | **passes.** The install took 24 s. 248 tests pass and 1 is skipped (the `git check-ignore` test, as expected outside a work tree). Ruff is clean. All 15 acceptance cases are within 10⁻⁶. Example 1 runs, and the six diagrams build. CI on the pull request passes on Python 3.11 and 3.13. |
| H5 | `cffconvert --validate -i CITATION.cff` (cffconvert 2.0.0) | **passes**: "Citation metadata are valid according to schema version 1.2.0." |
| H8 | the licence of every installed package, from that full install (`pip-licenses` 5.5.5, run from a separate environment so it is not counted) | **No GPL, LGPL or AGPL package, and none unknown.** The 76 packages are Apache 2.0, BSD, MIT, ISC, PSF or MIT-0/MIT-CMU, with three carrying MPL-2.0 (certifi, tqdm, and part of orjson). MPL-2.0 is file-level copyleft and binds only modified or distributed copies of those files; Manacitra depends on them and does not include them, as NOTICE says. The inventory reads each package's own metadata; it is not a legal review. |

**Found on the way: a plain install has no data.** With `pip install .` (not editable), 59 tests fail with
`FileNotFoundError`. `archive.data_dir()` looks for `data/` beside the source tree, and an installed package has no
`data/`. The README documented only the editable install from a clone, which works. Fixed by the A3 addition in section 12:
a clear stop, `MANACITRA_DATA` and `--data`, and both routes in the README.

**The Open Quantum adapter against the real SDK, offline.** Section 5 listed the real SDK calls as untested without
the network. With `openquantum-sdk` 0.4.3 and `openquantum-sdk-qiskit` 0.3.3 installed, their code was read; no account
was used and no request sent:
- every method the adapter calls exists with the argument names it passes: `get_backend_class`,
  `upload_job_input`, `prepare_job`, `_wait_for_preparation(preparation_id, timeout, interval)`,
  `_resolve_organization_id`, `create_job`, `get_job`, `download_job_output` and `get_credit_balance`;
- every model field it reads or sets exists (`JobPreparationCreate`, `JobCreate`, `JobPreparationResultResponse`,
  `CreditBalanceRead`, `JobRead`, `QuotePlan`, `QueuePriority`);
- `ExecutionPlanType.PUBLIC` and `QueuePriorityType.STANDARD` exist.

**Every call is verified against SDK 0.4.3 offline. The live responses are still untested.** Two of the methods,
`_wait_for_preparation` and `_resolve_organization_id`, are private and may change without notice. The extra is now
limited to the checked versions, and the adapter stops at import if either method is missing (section 12).

## 14. Amendment A4: fixes from the second review (6 October 2026)

**The review.** A second independent review, by an OpenAI Codex agent in run mode, against the rubric as revised on
6 October, of commit `481cb93`. Its marks were 41 PASS, 3 FAIL and 0 CANNOT CHECK, with 258 tests passing. It
reproduced every Section B number with its own code. Its report and probes were read from its hand-back folder,
outside the repository, and are not copied into it.

**Numbering.** The amendment asks for "a section 13, as A3 did for section 12". Section 13 already holds the review's
three CANNOT CHECK items, so this is section 14.

**Every number still reproduces.** That includes every statistic brought under test here for the first time (below).
Nothing in `data/` changed, and all 21 files match `data/SHA256SUMS`.

**Each finding, what changed, and the test that now covers it.**

| review ID | finding | what was changed | test |
|---|---|---|---|
| R1 (Blocker; E2) | the guard's ledger lookup and its reservation were separate, unlocked steps: two callers held after both had read the ledger both sent one job | **One lock around the check.** Every spending path (IBM and Open Quantum, library and command line) goes through `submit_once`, which takes an exclusive lock on `ledger.jsonl.lock` beside the ledger. It uses `fcntl.flock` on POSIX and `msvcrt.locking` on Windows, and each acquisition opens its own descriptor, so the lock holds between processes and between threads. **In order, under the lock:** the ledger is read again from disk; the job hash is checked against earlier sends and open reservations; the backend's `_reserve` does the budget accounting from those entries; the reservation and the "sending" record are written in one write, then flushed and fsynced. The lock is released, and only then is the job sent. **Timeout.** A caller that cannot take the lock within 30 s is refused (`LockTimeout`) and sends nothing. **Durability.** Every ledger write is flushed and fsynced. A last line without its newline (a crash mid-write) is ignored when read and cut off before the next write; any other line that is not JSON stops the read. No new dependency. | `test_guard_concurrency.py`: `test_two_processes_one_job_exactly_one_send`, `test_a_held_lock_refuses_after_the_timeout`, `test_a_crash_after_the_reservation_still_refuses_a_repeat`, `test_an_unfinished_write_is_ignored_and_cut_off`, `test_a_corrupt_line_in_the_middle_stops_the_read`, and `test_the_reviewers_thread_race` (the reviewer's barrier script, adapted to the fake backend in `tests/_fakes.py`) |
| R1, budgets | ledger budgets were not atomic across callers | **Open Quantum:** committed credits are settled charges plus open reservations, as in A3, now read and checked under the lock. **IBM:** the cap check is now the usage read from the provider, plus the estimates of every open IBM reservation, plus this job's estimate, against the cap. The estimate is reserved in the ledger. A fetch that reports the job's charged time settles the reservation. | `test_two_processes_two_jobs_one_open_quantum_budget`, `test_two_processes_two_jobs_one_ibm_cap`; `test_ibm_fake.py`: `test_open_reservations_count_against_the_cap`, `test_a_fetch_without_the_charged_time_settles_nothing` |
| R1, after a failure | — | As A3 said: a reservation from a failed or ambiguous send stays until a fetch settles it, and a repeat needs `allow_resubmit=True` (`--allow-resubmit`). The override is logged with the caller's reason (`reason=`, `--resubmit-reason`); without one, it logs "none given". | `test_a_failed_send_keeps_its_ibm_reservation`, `test_a_resubmission_logs_the_reason`; the A3 Open Quantum tests, unchanged and passing |
| R3 (Major; F1) | the acceptance comparison read only the keys present on both sides and let some missing keys and type changes through; the settling run's `archived.analysis` was never compared | **The inventory.** `tests/expected_fields.json` lists, per acceptance case, every archived field it recomputes, by its path in the data file, with a rename (`"as"`) where the recomputed value sits at another path: 1,055 fields, 38 of them renamed. Every field is compared at 10⁻⁶, and none states its own tolerance. **The exclusions.** `tests/excluded_fields.json` names every other field of every data file, with a one-line reason each (201 entries). **The strict comparison** (`tests/_reproduce.py`) fails when a listed field is missing on either side, its type differs (a number against `None`, a string or a list; a list of another length; a dictionary with other keys), a recomputed number is not finite, or the difference exceeds 10⁻⁶. **The inventory test** fails when a field is in neither file or in both, when a listed or excluded path does not exist, or when an exclusion has no reason. | `test_field_inventory.py` (33 tests); `test_reproduction.py` |
| R3, k29 | the settling analysis, z among it, was not under test | `archive.settle_analysis` recomputes it from the archived P(11) table (the settling run archived no counts), with its decision rule. The case "Kickoff 31 step 0" is renamed "Kickoff 29 settling run and Kickoff 31 step 0". | **It reproduces with a difference of 0.0 on every field**, on both processors: z = 21.75267698823275 (ibm_fez) and 18.24544062466692 (ibm_kingston); verdict SETTLED-DETECTED on both. The ideal values differ by 2.2·10⁻¹⁶. |
| R3, mutations | — | **Four mutations, in memory**, each on one inventoried statistic: set to 999, removed, set to `None`, set to NaN. **Where:** ibm_fez's settling run (z), ibm_kingston's Kickoff 31 leave-one-out (r_AB), ibm_fez's Kickoff 33 shots-resampled interval, and Rigetti's r_AB. **Result:** each mutation fails the comparison and names the field. The files on disk are hashed before and after each test and never change. **End to end:** two more tests mutate the loaded record and rerun the whole case from the data, as the reviewer's probe did. | `test_a_mutated_statistic_fails_the_comparison` (16 cases), `test_the_reviewers_probe_end_to_end` (2), `test_the_comparison_is_strict` (9), `test_the_comparison_reports_a_missing_key_and_a_type_change` |
| R3, prose | README:43 and CONTRIBUTING claimed "every archived statistic" | **README and CONTRIBUTING.** Both now say: "Every statistic listed in `tests/expected_fields.json` is recomputed from the archived counts and compared at 10⁻⁶. Fields that cannot be recomputed from this release are named, with reasons, in `tests/excluded_fields.json`." The A3 wording on README numbers is kept. **Elsewhere:** the same narrowing is in `docs/index.md` section 7, the CHANGELOG and `test_reproduction.py`'s docstring. Section 0's summary line in this report keeps its words, with a dated note that this amendment narrows it. | wording |
| R2 (Blocker under the rubric; E5) | the reviewed zip shipped the working `.git`: reflogs, and 15 unreachable commit objects | **No history is rewritten**, by the author's ruling of 6 October: public authorship identities in git metadata are allowed. **The archive script.** `tools/make_review_archive.sh` makes a fresh `git clone --no-local --single-branch --branch <branch>`. It then removes the clone's own traces: the remote, a local path; the remote-tracking refs; and every reflog, which would name whoever cloned and the path cloned from. It runs both scans, and stops without writing anything on a finding. Only then does it zip the clone and write the zip's SHA-256 beside it. **Documentation:** `CONTRIBUTING.md`, under "Independent review". | **The script on `94f1928`:** 30 reachable commits; one ref; no reflog; no remote; 0 unreachable objects (`git fsck --unreachable --no-reflogs` in the extracted archive); no local path anywhere in its `.git`. Both scans are clean. The zip's SHA-256 was `7fbb9a37…77c3`. It is a check of the script, not the archive for the re-review: that one is made on the commit to be reviewed. |
| R2, the scan | — | **What it reads.** `tools/scan_secrets.py --git` reads the author, the committer and every address in the message of every commit reachable from any ref. It reports any address not approved for its role. **The approved list.** It is in `tools/scan_patterns.py` (`GIT_IDENTITIES`), written as escaped regular expressions so the tree scan does not match it: the author's public address as author, committer and in `Signed-off-by:`; the assistant's no-reply address in `Co-Authored-By:` only; GitHub's no-reply address as committer. **Unchanged:** the default tree scan. | `test_scan.py`: `test_the_approved_identities_pass_in_their_roles`, `test_anything_else_is_a_finding` (8 cases), `test_this_repository_has_only_approved_identities`, `test_the_approved_list_carries_no_address_the_tree_scan_would_match`. On this repository at `94f1928`: clean, 30 reachable commits. |

**What R3 brought under test for the first time, all reproducing.** 9,905 values in the 15 cases, the largest
difference 1.9·10⁻⁷ (before: 2,992 numeric values, through the lenient comparison). New, beside the settling runs:

- Kickoff 31: the leave-one-out (`archived/robustness`, by `verdicts.leave_one_out`), the hours since the settling
  run, the settling run's time, and the per-circuit P(11) table.
- Kickoff 32: each test pair's group, its four levels and its shots, ibm_kingston's line for pair 16-23, the selection's
  k_A and k_B from Kickoff 31's map, and the per-circuit P(11) table.
- Kickoff 33: the per-circuit scores with readout correction, the measured distributions, P(11) of A without and with
  the offset, the predictors, the shots-resampled 90% intervals, and the hours since Kickoff 32's job and its ID.
- Kickoff 36: each arm's per-circuit P(11) table, and arm 2's correlations of k_A and k_B with the planted error.
- Kickoff 34b: the bit-order check, the two waves' levels, the dead-pair filter's excluded pairs, the screen's pair
  rule applied again to its L_s (passing, taken, the counts, the 27 pairs), the screen's L_s on the 11 shared pairs,
  and whether the test run's low pairs stayed below 0.5 in the screen.

**The reviewer's probes, rerun against the fixed code.** Both scripts were copied, byte for byte (SHA-256
`e91988f7…1cdc` and `bec820a0…6c25`), with their relative paths pointed at this checkout.

`adversarial.py`, the thread race. At `481cb93` it reported `{"sends": 2, "distinct_job_hashes": 1,
"override_flags": [false, false]}`.
- **Unmodified, it now stops at its concurrent step.** Its earlier sections complete: the four verdict cases give
  NOISE, NOISE, DIAGNOSTIC and MAP PRESENT, there are 256 map and 72 payoff boundary checks, and the sequential guard
  gives `{"sends": 2, "override_flags": [false, true]}`. Then line 71 (`f.result()`) raises:
  `ResubmitRefused: refused: this job (hash 06771dba88d2) was already sent at 2026-10-06T02:53:20Z; its reservation
  from 2026-10-06T02:53:20Z (no amount) is open; pass allow_resubmit (CLI: --allow-resubmit) to send it again`.
- **With that one line changed** to collect each thread's exception instead of raising, it reports:
  `{"outcomes": ["ResubmitRefused", "sent"], "sends": 1, "distinct_job_hashes": 1, "override_flags": [false]}`.
  Its ledger holds one "reserved", one "sending" and one "sent".
- **Across processes as well.** The same race, run in two processes against the reviewed commit, sent twice; against
  the fix it sends once.

`coverage_probe.py`, the z mutation. At `481cb93` it reported `"acceptance_rows_and_diffs_unchanged": true`,
33 leaves compared, worst difference 0.0. Now:

```json
{"missing_key": [[0.0, ".checked"], [Infinity, ".omitted (missing on the recomputed side)"]],
 "numeric_changed_to_none": [[0.0, ".checked"], [Infinity, ".omitted (type: recomputed None, archived number)"]],
 "archived_path": "ibm_fez/k29-settle.json: archived.analysis.z", "original_z": 21.75267698823275,
 "mutated_in_memory_z": 999, "acceptance_rows_and_diffs_unchanged": false, "compared_leaves": 157,
 "worst_difference": 977.2473230117672}
```

**The excluded fields and their reasons** (`tests/excluded_fields.json`, 201 entries, grouped here by reason).

| reason | fields (in which files) |
|---|---|
| record metadata (provenance, sources, identifiers, descriptions), not a statistic | `meta` (all 19 files) |
| the provider's job times, record metadata; the hours between runs are recomputed from them where archived | `timestamps` (the 8 IBM runs) |
| the provider's usage record for the job, metadata | `usage` (the 8 IBM runs) |
| input: the archived counts, from which the statistics are recomputed | `counts` (10 files) |
| input: the pairs, the circuit order, the halves, the plan, the coupling map | `pairs`, `order`, `order35`, `halves`, `plan`, `edges`, `rounds`, the selection's pairs, groups and dense pairs, Rigetti's 11 shared pairs and two dropped pairs, the screen's candidate pairs and edge indices |
| input: the provider's published figures at submission, read from the provider | `published_at_submission`; the settling runs' `x` |
| input: the settling run archived no counts; this P(11) table is what its analysis is recomputed from | `k29-settle.json: per_circuit_P11` (both) |
| a copy of another field, not a statistic | `k29-settle.json: archived/k31_baseline/x`; `k31-map.json: archived/analysis/S4/calibration_last_update_at_submission`; `k36-persistence.json: arm1_verdict` |
| metadata: the provider's calibration date; a note that no calibration snapshot was returned | `k31-map.json: calibration`; Rigetti `calibration_snapshot(s)` |
| a record of the provider's transpiler at submission; the transpiled circuits as sent are not in this release | `transpile_checks` (Kickoff 31 and 33, both processors) |
| the selection's checks and records, made on the coupling map before the run | `k32-isolation.json: selection/group_balance`, `distance_checks`, `all_distance_checks_ok`, `replacements` |
| a note or definition in words, not a statistic | Rigetti: `L_s_definition`, `pair_rule/rule`, the descriptive notes, `fixed`, `pairs`, `L_main`, `definition`, `label`, `program_widths`, `archived/analysis/S3`, `archived/robustness/note`; persistence: `layout_note`, `layout`, `x_rule`, `seeds`, and the original `rule`'s wording (its verdict is compared); the arms' `model` and `seeds` |
| needs the screening run's counts, which are not in this release (only its L_s per candidate is) | `screen.json: bit_order_check`, `pair_rule/candidates/[*]/L_s` (the pair rule is recomputed from these) |
| needs Kickoff 34's test run, whose levels are in this release only for the 11 shared pairs | `main.json: …/test_vs_screen_27_test_pairs/r`; the shared pairs' `test_17_01` levels (an input) |
| input: the simulated days, their seeds and scrambles, the arms' noise models, numbers and published scores | persistence `static/days`, `scrambled/days`, `day_seeds`, `scramble`, `shots_per_circuit`, `noise_source_arm`; the arms' `arm`, `pairs`, `x` |
| the simulation's ground truth, from the noise model without shot noise; not a statistic of the archived counts, and not recomputed by the acceptance suite | the arms' `exact_P_per_variant`, `exact_k_no_shot_noise`, `exact_sd_kA_no_shot_noise`, `exact_r_kA_x_no_shot_noise` |
| the planted map's design, computed from the noise-free model before the simulated runs; the planted model is tested in `tests/test_simulator.py` | `k36-planted.json`, every field but `meta` and the planted errors themselves (an input) |
| input: Kickoff 33's workload, drawn from its seed; checked against a fresh draw by `tests/test_workload.py` | `k33-workload.json: unitaries`, `circuits/[*]/ideal` |
| a noise-free check of the workload's synthesis at design time; `tests/test_workload.py` checks the same property | `k33-workload.json: circuits/[*]/synthesised_noise_free`, `W_noise_free`, `max_abs_1_minus_W_noise_free` |

**Readings and choices, logged.**
- **A recorded reversal: an IBM cap refusal is now "refused", not a send.** A3 logged a cap refusal as "sending" then
  "failed", so that a retry needed the override; section 12 listed this as a difference between IBM and Open
  Quantum. With the cap checked under the lock before anything is reserved, both providers now log a refusal before
  sending the same way, and a job refused at the cap goes without the override once the usage allows it.
  `test_cap_refuses_before_anything_is_sent` was changed to say so.
- **What runs before the lock.** The provider's reads run before the lock (`_preflight`), so the lock never spans a
  network call: IBM's usage and the transpile checks; Open Quantum's quote, preparations, balance and earlier wave.
  Only the accounting against the ledger runs under it (`_reserve`). A refusal from either is logged as "refused".
- **The Open Quantum balance floor** uses the balance read before the lock and, as in A3, does not subtract other
  open reservations. The budget does count them. To bound concurrent spending, set `budget_credits`.
- **IBM reservations share one scope, `ibm`.** The usage window is the account's, across processors. Several accounts
  sharing one ledger would count each other's reservations, which errs toward refusing.
- **A reservation whose send failed, with no job created, never settles by itself**, because there is nothing to
  fetch. As A3 specified, it keeps counting against the cap or the budget in that ledger. A logged way to release
  one by hand is not in this amendment.
- **After the send.** If the lock cannot be taken to write the "sent" or "failed" record, the record is printed
  rather than lost. The reservation written before the send already refuses a repeat.
- **Not run on Windows.** The `msvcrt.locking` path has not been run: this machine is macOS, and CI runs Linux.
- **The settling analysis's formula.** It was read from the runner's script for the settling runs, outside the
  repository. That script's hash on disk differs from the one recorded in the ibm_fez file (`7ccce2…`): it is the
  later copy for ibm_kingston, whose predictions note says it kept the same decision rule. The formula reproduces
  every archived field on both processors with a difference of 0.0.
- **The bit-order check's formula.** It was read from Kickoff 34b's script, whose hash matches the one recorded in
  `main.json` (`5678d9…`). Its `ideal` differs by 1.9·10⁻⁷, within 10⁻⁶: the script computed it from six-place
  constants, and the package from the exact unitary.
- **Kickoff 32's analysis takes Kickoff 31's k_A from the archived file**, as before; the Kickoff 31 case compares
  that k_A with its recomputation.
- **What `excluded_fields.json` holds, for the author's ruling.** The prescribed sentence names fields "that cannot
  be recomputed from this release". To make the inventory total, the file also holds inputs and metadata. It also
  holds three groups this release could recompute in principle and does not: the simulated arms' ground truth, the
  planted map's design, and the workload's noise-free check. Each says so in its reason. Whether to bring them under
  test, or keep them excluded, is the author's call.
- **The GitHub Actions bot is not approved as a git identity.** The rubric's E5 approves it "in workflows and the
  sign-off checker", so the `--git` scan approves it in no git role. Once signing is on, the workflow's own commits
  would be findings unless the list adds it as their author and committer. That needs a ruling before signing is
  turned on.
- **New package functions.**
  - New: `archive.settle_analysis`, `archive.isolation_p11`, `archive.bit_order_check`, `archive.screen_pair_rule`
    and `circuits.ideal_exact`.
  - More fields from existing functions: `archive.isolation_analysis` (each row's group, levels and shots),
    `archive.payoff_from_record` (scores, distributions, levels, predictors) and `archive.rigetti_map` (the bit-order
    check and the wave levels).
- **The date.** The amendment is dated 6 October. This machine's local date was still 5 October when the work began;
  the ledger times above are already 6 October in UTC.

**After the amendment:**
- 314 tests pass (258 before; 56 new), and Ruff is clean;
- the identifier scan is clean on the full tree, and the git identity scan is clean on every reachable commit (30 at
  `94f1928`, before this report's commit);
- nothing in `data/` changed, and `data/SHA256SUMS` still matches.

**Not in this amendment, and not done:**
- merging;
- making the repository public;
- turning on signing;
- rewriting git history;
- publishing kickoff texts or sealed predictions;
- any provider submission.

## 15. Amendment A5: the Kickoff 37 result (6 October 2026)

**The source, checked before anything was copied.** The hand-back folder's `SHA256SUMS` passes on all 39 files. The
archive's SHA-256 is `f4d3e6d7351f…ee50`, as the amendment states and as its `.sha256` file records. The archive,
unpacked into a scratch folder, is identical to the folder. The folder was only read.

**What was copied** into `data/rigetti_cepheus_1_108q/`:

| file | contents |
|---|---|
| `k37-placement.json` | the pairs of each program (P27: 27 pairs on 54 qubits; P53: 53 pairs on 106 qubits); the bit reading, with n = 54 or 106; the label, wave, task and program of each task; the raw counts of all six tasks, as bitstring-to-count tables, each summing to 8000; each task's P(11) per pair; and, under `archived`, untouched from `results-37.json`: the measures (Pearson and Spearman, and the two correlations behind each d), the verdict with its conditions, the Spearman reading and the A1 and A2 readings, the gap, the completion order, and the descriptive lines (against Kickoff 34b, and the crowding lean) |
| `k37-after-the-fact.json` | `after-the-fact-37.json`'s checks, labelled "computed after seeing the data, outside the verdict", with the source's own label kept in `meta` |
| `k37-P27-A-no.qasm`, `k37-P53-A-no.qasm` | the two programs as sent, byte for byte (see below) |

Each JSON file's `meta` gives the processor ("Rigetti Cepheus-1-108Q, through Open Quantum, Public plan"), the UTC
creation and completion time of every task, 8000 shots per task, "Kickoff 37" as the source, each source file's
SHA-256, the archive's and the script's SHA-256, and the line on the second wave as the amendment words it.
`k37-placement.json`'s `meta` also gives the two programs' SHA-256 values (`81e1e149…` and `d312052a…`, Kickoff 34b's
`01-A-no.qasm` and `screen-A-no.qasm`).

**The programs.** The amendment says to leave them out "unless the identifier scan passes on them". It passed on both
(`tools/scan_secrets.py` on the two files: clean), so they are copied. If the clause was meant only to permit this,
not to ask for it, removing them is two files, two index rows and two checksum lines.

**What was left out:** the task IDs (and the task names); the credit balances, quotes and cost record; the raw
provider records and the platform's processed copies; the preparations; the target reads; the runner's sealed
predictions, its report and its plot; the run log; the reproduction file and the program check file (their results
are recorded above and in `meta`); and the per-task spread table in `results-37.json` (mean level, between-pair SD,
shot-noise SD), which the amendment's list does not name. The report's carried sentence is not copied; no file in
`data/` contains it.

**The inventory.** Two new acceptance cases, "Kickoff 37, Rigetti Cepheus-1-108Q" and "Kickoff 37, after the fact".

- `tests/expected_fields.json`: 86 fields of `k37-placement.json` (the six P(11) tables, every measure, every verdict
  field including the readings' text, the gap's seconds, minutes, midpoint gap and short-gap flag, the completion
  order, the four lines against Kickoff 34b and every crowding-lean field) and 65 of `k37-after-the-fact.json` (every
  field but the three below). No field is renamed.
- `tests/excluded_fields.json`, 10 entries:

| file | path | reason |
|---|---|---|
| `k37-placement.json` | `meta` | record metadata; the gap and the run order are recomputed from the task times in it |
| | `programs` | input: each program's pairs and size |
| | `bit_order` | a definition in words |
| | `tasks` | input: label, wave, task and program of each task |
| | `counts` | input: the counts the statistics are recomputed from |
| | `archived/gap/definition` | a definition in words |
| | `archived/descriptive/crowding_lean/note` | a note in words |
| `k37-after-the-fact.json` | `meta` | record metadata |
| | `label` | a note in words |
| | `selection_note` | a note in words; its two SDs (0.039 and 0.042) are checked at its rounding by `test_k37_selection_note_sds` |

**The recompute.** `archive.placement_or_drift` recomputes Kickoff 37 from `k37-placement.json`'s counts and task
times, with `main.json` and `screen.json` for the lines against Kickoff 34b. `archive.placement_rule` is the rule, with
its thresholds fixed as module constants (control ≥ 0.7; W: both d < 0.4; N: both d ≥ 0.7; T: both t < 0.4; S: both
t ≥ 0.7; short gap under 60 minutes). It sits in its own section of `archive.py`, after Kickoff 34b's, and like
`settle_analysis` it recomputes one archived run's own rule: no new verdict in `verdicts.py`, no new command. The
amendment's "beside settle_analysis" was read as "in the same way as"; the function is not next to it in the file.

**Reproduction.** Every listed field, compared strictly: 380 values in `k37-placement.json` and 80 in
`k37-after-the-fact.json`, the largest difference 0.0 in both.

| statistic | archived | recomputed | amendment |
|---|---|---|---|
| each task's P(11), 6 tasks | | difference 0.0 | at 10⁻⁶ |
| c_1 | 0.9983836521792997 | the same | 0.998384 |
| c_2 | 0.997482026465647 | the same | 0.997482 |
| d_1 | 0.06899004265600006 | the same | 0.068990 |
| d_2 | −0.2521745164008942 | the same | −0.252175 |
| t27 | 0.9680385015171348 | the same | 0.968 |
| t53 | 0.7584356165289697 | the same | 0.758 |
| gap | 32,950 s (549.17 min) | the same, from the completion times in `meta` (11:31:39 minus 02:22:29) | 9 h 09 min |
| verdict | PLACEMENT; W and S true, N and T false | the same, from the fixed thresholds | PLACEMENT |
| wave 1 P27 against 34b's main-job "A no" levels (the mean of its four identical tasks, from `main.json`'s counts), 27 pairs | 0.98877 | the same | 0.989 |
| wave 1 P53 against 34b's screen levels (`screen.json`), 53 pairs | 0.97595 | the same | 0.976 |

The Spearman values, the two lines beside them (against 34b's first "A no" task alone, 0.947; on the 27 shared pairs
of the screen, 0.850), the completion order, the crowding lean and every after-the-fact check also reproduce with a
difference of 0.0. `test_k37_as_amendment_a5_states_it` checks the amendment's figures at its stated precision, and
`test_the_placement_rule_at_its_thresholds` checks each verdict of the rule at its boundaries. No number failed to
reproduce.

**The mutation test.** `archived/measures/d_2/pearson` in `k37-placement.json` joins the mutation list in
`tests/test_field_inventory.py`. Set in memory to 999, removed, set to None or set to NaN, it fails the comparison,
which names the field; the files on disk are unchanged (4 tests).

**README lines changed**, as the amendment words them:
1. the findings' opening line: "The findings come from runs on 5 and 6 October 2026.";
2. finding 6, after finding 5;
3. finding 2: the sentence on the five excluded pairs, after the dead-pair sentence;
4. "How long a map lasts": the Rigetti sentences replaced (the placement-records sentence and the Kickoff 35 and 36
   sentences kept);
5. the new "has not shown" bullet on why the program matters;
6. the Open Quantum guidance, in the extras paragraph, with the verbatim-mode sentence kept after it;
7. Limits: "Three processors, two days", ending "on 5 and 6 October 2026.";
8. the kickoffs table's row for 37, after 36; Kickoff 35's row unchanged.

**The README tests.** Seven new tests in `tests/test_readme_numbers.py` check every new number and time against the
data at the README's rounding, with times to the nearest minute: the waves' 00:45 to 02:22 and 11:31 to 11:35 UTC (the
first creation to the last completion of each wave); the second wave's completions within 3 minutes; 0.997 to 0.998,
0.97 and 0.76, 0.99 and 0.98, 0.07 and −0.25; PLACEMENT; the 9-hour gap; the five excluded pairs at 0.70 to 0.84
under the screen program (the same five pairs as Kickoff 34b's dead-pair filter); the dates; the table row; and the
new guidance. Two earlier tests were changed because the README no longer shows what they checked: the screen's and
the test task's times (18:55 and 17:01 UTC) left with the replaced sentences, so `test_the_rigetti_times_shown` now
checks only the main job's, and the test of the 0.10 to 0.23 and 0.93 lines is renamed `test_kickoff_34b_across_runs`
(those lines are still shown in `docs/index.md`).

**Other files changed to match.**
- `data/README.md`: the index rows for the two new files; the programs; the date line; the Kickoff 37 counts format;
  and what was left out.
- `data/SHA256SUMS`: rewritten, 25 files; `--check` passes.
- The adapter's docs (`docs/index.md`, section 5, and `backends/openquantum.py`'s docstring): the same guidance
  sentence, replacing "use a map only within the job that measured it". `docs/index.md` also gains a Kickoff 37 row
  in its reproduction table, and its "Lived facts" line now says 5 and 6 October.
- `tests/test_data_meta.py`: a run record's UTC may now start with 2026-10-06 as well as 2026-10-05.
- `CHANGELOG.md`: the dataset line names Kickoff 37.

**Scans.**
- The identifier scan on the full tree: clean (110 files).
- The git identity scan (`--git`): clean on every reachable commit (32 at `983bd8c`, before this amendment's
  commits).

**Readings for the author's ruling.** Each names a checkable difference. The text was written as the amendment gives
it; nothing here was changed on my own reading.
- **"Over a day."** The README's "a fixed program's pair levels held over about 9 hours and over a day (Kickoff 37)"
  rests on the lines against Kickoff 34b. Those compare wave 1 (completions 01:24 to 02:22 UTC, 6 October) with
  34b's screen (completed 18:55 UTC) and main job (22:15 to 22:29 UTC) on 5 October: about 3 to 7.5 hours apart,
  across a change of date. The longest gap over which a program's levels were compared is 9 h 09 min, between
  Kickoff 37's own waves. "The day before", in finding 6, is right as a calendar date.
- **"Each program agreed with itself: r = 0.997 to 0.998 minutes apart."** Only the 27-pair program ran twice in a
  wave; the 53-pair program ran once per wave, so it has no minutes-apart repeat. Its self-agreement is t53 = 0.76
  across the waves and 0.98 against 34b.
- **The adapter's docs keep the Kickoff 34b sentence** after the new guidance: levels held within a job (r = 0.93)
  "but not between runs a few hours apart". It is still a true record of 34b, but it now sits next to Kickoff 37's
  finding that those runs differed in program, not only in time.

**After the amendment:**
- 340 tests pass (314 before; 26 new), and Ruff is clean;
- the identifier scan is clean on the full tree, and the git identity scan is clean on every reachable commit;
- `data/SHA256SUMS` matches every file.

**Not in this amendment, and not done:**
- Kickoff 35's data;
- Kickoff 38;
- merging, making the repository public, or turning on signing;
- any provider submission.

## 16. Amendment A6: fixes from the third review (6 October 2026)

**The review.** A third independent review, by an OpenAI Codex agent in offline run mode, of commit `983bd8c` (the A4
commit). Its marks were 38 PASS, 3 FAIL and 3 CANNOT CHECK, with 314 tests passing. The three CANNOT CHECK items
(fresh install, CITATION validation, the licences of the Open Quantum extras) needed the network, which the reviewer
did not have; section 13 covers them from a networked run. Its report and probes were read from its hand-back folder,
outside the repository. Only `balance_race.py` was taken from it, adapted into `tests/`; its SHA-256,
`78c3ee19…0600`, matches the folder's `SHA256SUMS`.

**Line numbers.** The amendment cites `openquantum.py` lines 487 to 495 and 497 to 504, from the reviewed commit. At
`73b570c` (after A5's docstring lines) the same code was at 487 to 496 and 498 to 505.

**Every number still reproduces.** The full suite passes, the acceptance cases among it. Nothing in `data/` changed,
and `data/SHA256SUMS` matches every file.

**Each finding, what changed, and the test that now covers it.**

| review ID | finding | what was changed | test |
|---|---|---|---|
| E3 (Major) | Open Quantum's balance floor was checked in `_preflight`, before the lock, and `_reserve` never counted open reservations against it. Two processes, each reading a balance of 122 credits, each sent a wave of 24 against a floor of 90, leaving 74 | **The rule** (module docstring of `backends/base.py`; `docs/index.md` section 6): every spending check on a shared quantity (an account balance, a run budget, a usage cap) is decided in `_reserve`, under the ledger's lock, against every open reservation that draws on that quantity. A check made before the lock is only an early refusal. **The floor, under the lock:** the balance read in `_preflight`, less the credits of every open reservation on the same account, less this job's quote, must stay at or above the floor. A refusal names each open reservation it counted (job hash, credits, time reserved). **No double counting in the unsafe direction:** an open reservation is counted until a fetch settles it, even if its charge may already show in the balance; the docstrings of `base.py` and `OpenQuantumBackend` say so. **The account** is the saved account's name; the ledger records it as a hash (`account_scope`), and each reservation now carries it. **The early checks:** the quote's `balance_after_at_least_floor` test now counts open reservations too, read without the lock. `_preflight` no longer checks the floor, because the deciding check follows it at once with the same balance, and two checks would have given the same refusal twice | `test_guard_concurrency.py`: `test_two_processes_one_open_quantum_balance_floor` (the reviewer's race: one sends, the other is refused with the floor and the counted reservation named) and `test_the_reviewers_balance_race` (`balance_race.py`, adapted; its worker is `balance_race_worker` in `tests/_fakes.py`, beside A4's thread race). `test_openquantum_recorded.py`: `test_a_settled_reservation_no_longer_counts_against_the_floor`, `test_open_reservations_on_the_account_count_against_the_floor`, `test_the_floor_counts_every_job_name_on_the_account_and_no_other_account`, `test_a_reservation_from_before_a6_counts_against_every_account`. Changed: `test_the_balance_is_read_again_at_send_time`, which matches the new refusal text |
| E3, item 5: the order of settlement | found here, not by the reviewer: a "settled" record settled every reservation of its job hash, wherever it stood. A job sent again with the override after its first send was fetched had its new reservation counted as settled at once, so neither the IBM cap nor the new floor counted it | `Ledger.all_reservations` reads the ledger in order. A "settled" record settles only an open reservation of its hash written before it. A fetch now records the task IDs it fetched (`job_ids`, both providers), and the record settles the reservation whose send created them, or nothing; a record without IDs (from before A6) settles the earliest open one | `test_a_settled_record_settles_only_an_earlier_open_reservation`; `test_a_resubmitted_job_is_not_settled_by_the_earlier_fetch` |
| E3, item 5: settled after the read | found here, not by the reviewer: the balance (Open Quantum) and the usage (IBM) are read before the lock. Another process's reservation, settled between that read and the lock, stopped counting, though the figure read did not include its charge | Each `_preflight` notes the ledger's length before the provider read (`ledger_mark`). Under the lock, `Ledger.unsettled_at` counts a reservation as settled only if its settlement was already in the ledger at that mark. This applies to the floor and to the IBM cap | `test_a_reservation_settled_after_the_balance_read_still_counts`; `test_ibm_fake.py`: `test_a_reservation_settled_after_the_usage_read_still_counts`. With `unsettled_at` changed to ignore the mark, both fail |
| E3, item 5: the CLI's ledger | found here: `manacitra map --submit --ledger PATH` quoted against the default ledger, and gave the backend no ledger, so a later fetch through that backend settled into the default ledger | The command builds its ledger first and gives it to the backend before the quote. Its "sent" line now says to fetch with a backend given that ledger | covered by the guard's tests; the CLI's submit path is not run by any test, since it needs a provider |
| F1 (Minor) | "from the archived counts" overstated the inputs | `README.md` (line 45) and `CONTRIBUTING.md` (line 25) now say the statistics are recomputed "from the archived inputs: the raw counts where the release includes them; for the Kickoff 29 settling runs and some Rigetti comparisons, the archived probability or level tables, whose counts are not in this release; and, for elapsed times, the archived timestamps", with the rest of the sentence and the pointer to `tests/excluded_fields.json` kept. CONTRIBUTING's paragraph was rewrapped to the file's width | wording |
| E5 (Blocker under the rubric) | GitHub Actions' public bot address appears in this report and in `tests/test_dco.py` and `tests/test_scan.py`, outside the two files the rubric approved | **No change.** The rubric is being revised to approve the address anywhere in the tracked tree. `tools/scan_patterns.py` already allows it tree-wide: its `ALLOW` entry `github-actions-bot` matches the exact address in any file, with no restriction by file, so there was nothing to widen. The other approved identities keep their roles | the identifier scan, clean |

**Every spending check, and where it is decided** (section 1, item 5). "Early" means before the ledger's lock:
an early refusal only. "Deciding" means under the lock, against the ledger as read under it.

| backend | check | evaluated in | where | counts open reservations |
|---|---|---|---|---|
| guard | the same job already sent or reserved | `submit_once`, first quick check | early | its own job hash |
| guard | the same, again | `submit_once`, `_repeat_check` | **deciding** | its own job hash |
| guard | the ledger's lock taken within 30 s | `Ledger.lock` | at the lock | — |
| Open Quantum | every task quoted at the expected credits, on the Public plan, prepared, shots echoed | `quote()`, then `_preflight` (the quote's tests must have passed) | early; per job, not a shared quantity | — |
| Open Quantum | the budget: committed in the run's scope plus this job | `quote()` (`within_budget`) | early | yes, read without the lock |
| Open Quantum | the balance floor | `quote()` (`balance_after_at_least_floor`) | early | yes, read without the lock (new) |
| Open Quantum | the quote younger than `quote_valid_s`; each preparation still completed, on the Public plan, at the expected price; the earlier wave completed | `_preflight` | early; per job | — |
| Open Quantum | the budget | `_reserve` | **deciding** | yes: settled and open, in the run's scope |
| Open Quantum | the balance floor | `_reserve` (new; it was in `_preflight`) | **deciding** | yes: every open reservation on the account, including any settled after the balance read |
| IBM | the usage can be read | `_preflight` | early; no usage read, no send | — |
| IBM | 3 CZ per pair, no swaps, layout kept, every pair with a reported CZ | `_preflight` (`transpile`) | early; per job | — |
| IBM | the cap, for a look before submitting | `check_cap()`, not called by the guard | early | yes, read without the lock |
| IBM | the cap: used, plus open reservations, plus this job's estimate | `_reserve` | **deciding** | yes: every open IBM reservation, including any settled after the usage read (new) |

The simulators spend nothing and have no checks. No other spending path exists: every spending send goes through
`submit_once` (A3).

**The reviewer's `balance_race.py`, rerun.** The script was run unmodified from a scratch copy, with
`MANACITRA_REVIEW_ROOT` pointing at this checkout. Its output, less the ledger records it also prints:

Before the fix (at `73b570c`):

```json
{"initial_balance": 122, "floor": 90, "budget": 100,
 "process_results": [{"who": "a", "result": "sent", "quote": 24, "tasks": 8},
                     {"who": "b", "result": "sent", "quote": 24, "tasks": 8}],
 "sent_tasks": 16, "reserved_total": 48, "balance_after_if_charged": 74, "floor_breached": true}
```

After:

```json
{"initial_balance": 122, "floor": 90, "budget": 100,
 "process_results": [{"who": "b", "result": "sent", "quote": 24, "tasks": 8},
                     {"who": "a", "result": "SpendRefused", "message": "refused before sending: balance floor: balance
                      122 - open reservations 24 - 24 for this job = 74 < floor 90; open reservations on the saved
                      account 'default': b9a3674ab905 (24 credits, reserved 2026-10-06T15:11:05Z)"}],
 "sent_tasks": 8, "reserved_total": 24, "balance_after_if_charged": 98, "floor_breached": false}
```

Only the floor refused process a. Its quote had passed, because the quote ran before process b reserved anything, so
the deciding check is the one under the lock.

**Readings and choices, logged.**
- **A recorded reversal.** Section 14 said: "The Open Quantum balance floor uses the balance read before the lock
  and, as in A3, does not subtract other open reservations." That is retired by this amendment. The floor now
  subtracts them, under the lock.
- **What "the same account" means.** The saved account's local name (`account="default"` by default). Two saved
  names for one organization count as two accounts; the docstring says to reach one organization through one saved
  name. The organization's ID would identify the account exactly, but it is never stored, and a hash of it would be
  derived from it. The ledger holds a hash of the local name, not the name.
- **Reservations from before A6** carry no account. Each Open Quantum one among them is counted against every
  account, which can only refuse too much.
- **One ledger per account.** The floor sees only the reservations in its own ledger. The old advice, "give the run
  its own ledger or job name", now says job name only, because a separate ledger hides its reservations from the
  floor.
- **Waves double count until fetched.** A first wave's charge may show in the balance while its reservation is open,
  so a second wave counts it twice. To avoid refusing a second wave that would fit, fetch the first before sending it.
  This is the direction item 3 accepts.
- **The settlement fixes go beyond the reviewer's finding.** They came from checking every spending check against the
  rule (item 5), and both were in the unsafe direction. They change what `Ledger.reservations` reports for a
  resubmitted job, and nothing else that the earlier tests saw.
- **The bot address in git metadata.** Unchanged: as section 14 noted, the `--git` scan approves the bot in no git
  role. The revised rubric concerns the tracked tree; the git roles were left alone, as the amendment says.
- **"From the archived counts" elsewhere.** The amendment names README line 45 and CONTRIBUTING line 25. The same
  phrase remains in the docstrings of `tests/_reproduce.py`, `tests/test_reproduction.py`, `tests/test_rigetti.py` and
  `src/manacitra/archive.py`, in `examples/02_map_from_archive.py`, and in README line 149, about the ibm_fez example.
  Some of these are true as they stand: the ibm_fez and Kickoff 34b statistics do come from counts. They were left
  for the author's ruling.

**After the amendment:**
- 350 tests pass (340 before; 10 new, 1 changed), and Ruff is clean;
- the identifier scan is clean on the full tree, and the git identity scan is clean on every reachable commit (35,
  before this amendment's commit);
- nothing in `data/` changed, and `data/SHA256SUMS` matches every file.

**Not in this amendment, and not done:**
- merging, making the repository public, or turning on signing;
- any provider submission;
- new adapters (IQM, Braket). When they come, they follow the rule above from the start.

The full rubric pass runs once, on the commit to be made public, with network access, so that the three CANNOT CHECK
items can be checked too.

## 17. Amendment A7: Kickoffs 35, 38, 40, 41 and 42 in the dataset (7 October 2026)

**The sources, checked before anything was copied.** Each of the five hand-back archives matches its `.sha256` file and
the SHA-256 the amendment gives, and every file in each archive matches its inner `SHA256SUMS` (24, 32, 219, 105 and
106 files). Each run's file records the archive's SHA-256 and each source file's.

**The Amazon patterns came first** (section 7). Before anything was copied from `hardware-40`, `-41` or `-42`,
`tools/scan_patterns.py` gained six patterns, written with character classes so that the file does not match itself:
Amazon resource names (their prefix, in any case, at a word boundary); S3 bucket addresses; a twelve-digit number
standing alone (an account number); the access-key and secret-key field names; and access-key IDs (the four-letter
prefix and 16 upper-case letters or digits). Region and profile names are not matched. One allowance was needed: a quoted
key of exactly twelve 0s and 1s, a six-pair counts key (Kickoff 32's groups), is not an account number. Any other
twelve-digit string is still a finding. `test_scan.py` gained two tests: each kind caught, and regions, counts keys,
fractions and 11- or 13-digit numbers left alone.

**The scan on the source folders.** All five were scanned with the new patterns before copying. Every finding was in a
file left out:
- the Braket discovery records and runner scripts (resource names, an access-key field name);
- Kickoff 38's provider records, preparations, submission record and run log (UUIDs);
- IBM's usage `details` (a metric UUID, dropped as for the other IBM files);
- the scripts, reports and logs (vocabulary-boundary words).

The compiled programs, the programs as sent and every results file scanned clean, and were copied. After copying, the
tree scan and the `--git` scan are clean.

**What was copied, and what was left out.** As the amendment lists, file by file; `data/README.md` gives the index, the
two new Formats entries and the copying paragraph.
- **Kickoff 35** (`ibm_fez/`): `k35-layout.json`, `k35-day1.json` to `k35-day3.json` and `k35-persistence.json`. Left out:
  the plots, the predictions and report, `compare-k36.json` and its script, the usage records beyond each day's charged
  seconds, and each day's usage `details`.
- **Kickoff 38**: `k38-activity.json`, and `k38-P53i-A-no.qasm` as sent. P27 and P53 are byte-identical to
  `k37-P27-A-no.qasm` and `k37-P53-A-no.qasm`, which `meta` says, with the three hashes. Left out: task IDs, balances,
  quotes, provider records, processed copies, preparations, the self-test, the plot, the predictions and report.
- **Kickoff 40**: the seven `k40-*.json` files, `compiled/k40/` (50 programs, by stage) and `programs/k40/` (50, by
  stage).
- **Kickoff 41**: the three `k41-*.json` files and `compiled/k41/` (30).
- **Kickoff 42**: the five `k42-*.json` files, `compiled/k42/` (36, by day) and `programs/k42/` (18).

For the Braket runs, everything from the submission records was left out (each figures file carries the figures,
placeholder counts and calibration times, copied without ARNs), with the cost records, quotes, discovery records,
predictions, reports and plots. Each results file records `redactions: []`, so the compiled programs in the archives
are as Braket returned them. The unredacted copies were never in the archives and were not seen.

**Labels added beside archived blocks; nothing archived was changed.**
- Kickoff 35's robustness block: "descriptive, outside the verdict; computed after seeing the data".
- Kickoff 38's direction leans: "leans, outside the verdict".
- Kickoff 40's stage 1 lines against Kickoff 37: "descriptive, outside the reading".
- Kickoff 41's same-day lines: "a ceiling a user holding yesterday's map would not have".
- Kickoff 42's line against Kickoff 41: "beside the verdicts".
- Each after-the-fact file: "computed after seeing the data".
- Kickoff 38's file carries the amendment's line on Kickoff 40, and Kickoff 42's day files carry the line on its
  Amendment A1.

**The recomputes, in `archive.py`.** None is a public verdict or a command.
- Kickoff 35: `full_chip_day` and `full_chip_persistence`, which call `verdicts.persistence_analysis`, as the amendment
  says.
- Kickoff 38: `footprint_or_activity` with its rule `activity_rule`, beside `placement_or_drift`; and `p53i_checks`,
  which reads the builder's five checks back from the three programs' texts.
- The Braket route (Kickoffs 40 to 42):
  - `braket_outcomes`: the `measured_qubits` reading;
  - `compiled_record`: the records check on a compiled program;
  - `braket_placement`, `braket_map` (which calls `analyse_map`) and `braket_payoff` (which calls `analyse_payoff`);
  - `braket_figures_check`.
- Kickoff 41: `pinned_map_persistence` with `pinned_map_rule`, beside `placement_or_drift`; and `day_old_payoff`.
- Kickoff 42: `offset_scan`, with `scan_fit`, `scan_day`, `scan_persistence` (V4), `scan_fingerprints` (V5 and the
  switch) and `scan_after_the_fact`. The ideal curve is `scan_ideal`, from the package's own `circuits.unitary`.

**Reproduction, run by run.** Fourteen new acceptance cases compare 18,410 values; the largest difference is
3.0·10⁻¹⁵ (a readout-corrected W in Kickoff 40's stage 3). Every value the amendment states is also checked, at the
precision it states, by `test_k35_as_amendment_a7_states_it` and the four tests beside it.

| case | fields listed | values compared | largest difference | verdict |
|---|---|---|---|---|
| Kickoff 35, ibm_fez | 160 | 6,530 | 4.4·10⁻¹⁶ | HOLDS (original rule; A1 beside it, HOLDS) |
| Kickoff 38 | 162 | 496 | 0 | ACTIVITY |
| Kickoff 40, stage 1, placement | 79 | 301 | 0 | PINNED |
| Kickoff 40, stage 2, the map | 340 | 1,355 | 0 | DIAGNOSTIC |
| Kickoff 40, after the fact | 15 | 15 | 0 | (rule applied: DIAGNOSTIC) |
| Kickoff 40, stage 3, the payoff | 416 | 2,257 | 3.0·10⁻¹⁵ | NOT SETTLED |
| Kickoff 40, figures and ideal values | 344 | 1,133 | 1.0·10⁻¹⁵ | |
| Kickoff 41, Part A | 372 | 1,461 | 0 | HOLDS (today's map DIAGNOSTIC) |
| Kickoff 41, Part B | 213 | 1,138 | 6.1·10⁻¹⁶ | level USEFUL; kept share NOT SETTLED |
| Kickoff 41, figures and programs | 139 | 147 | 0 | |
| Kickoff 42, Day 1 | 417 | 1,483 | 0 | V1 SPREAD, V2 MIXED, V3 DOES NOT |
| Kickoff 42, Day 2 | 515 | 1,820 | 0 | V4 HOLDS (amended), PARTIAL (original); V5 HOLDS; switch MIXED |
| Kickoff 42, after the fact | 37 | 45 | 0 | |
| Kickoff 42, ideal values, figures and programs | 205 | 229 | 0 | |

What each case covers:
- **Every compiled program was read back** (414 Braket tasks over the three runs): every pair ran on its named qubits.
- **Kickoff 35's flagged line**, on 172 edges with each day's reliability recomputed on the subset (0.928, 0.972,
  0.942): corrected r 0.830, 0.428, 0.736, and a worst-decile overlap of 8 of 17. It is now the package's `flagged`
  block.
- **Kickoff 35's other descriptive checks** reproduce exactly, including the seeded shot redraw (seed 35, 2,000 draws).
- **Kickoff 38's five builder checks** are recomputed from the three `.qasm` files in `data/`, and pass.
- **Kickoff 40's ideal values.** The ideal distributions and the 24 unitaries are identical (difference 0.0) to a fresh
  draw with `workload.draw_unitaries(33)` and to `workload/k33-workload.json`: they are Kickoff 33's circuits, as the
  file says.
- **Kickoff 41's programs.** Each file's SHA-256 is recomputed from `programs/k40/`: all 30 match. The task order of
  Kickoff 42 is drawn again with seed 42, and its five programs shared with Kickoff 40 are byte-identical to Kickoff
  40's.
- **Kickoff 42's ideal curve** from the package agrees with `k42-ideal.json` to 0.0 (the amendment asks for 10⁻⁶).

**Cross-checks against the files already in `data/`, all recomputed, none read from an archived analysis.**
- **Kickoff 38 against 37.** T2 against the mean of Kickoff 37's four P27 tasks: r = 0.852 on 27 pairs. T3 against
  the mean of its two P53 tasks: r = 0.880 on 53.
- **Kickoff 40 against 34b and 37.** Stage 2's k_A against Kickoff 34b's, recomputed by `rigetti_map` from its counts:
  r = −0.17 on 20 shared working pairs. Stage 1's levels against Kickoff 37's 27-pair program: −0.18; against its
  53-pair program: 0.24.
- **Kickoff 41 against 40.** Every persistence measure takes Kickoff 40's map from its recompute. Part B's priors are
  Kickoff 40's level and k_A, recomputed.
- **Kickoff 42 against 40 and 41.** V3 takes Kickoff 40's k_A, recomputed. The line beside the verdicts takes Kickoff
  41's W, recomputed: r = −0.47 on 24 pairs, and −0.26 without the two fits at the grid's edge.

**Findings, and how they were resolved.**
- **A Kickoff 35 field did not reproduce at first: the best-decile overlap** (amendment: 12 of 18). `persistence_
  analysis` gave 11 of 18. The cause: on Day 3, three edges tie exactly at k = 1.2710, at ranks 18 to 20, and
  `_decile_overlap` used numpy's default (unstable) sort, so which tied edge counted was arbitrary. The runner's
  cross-check said "52 of 52". It ran Kickoff 36's `k35_analysis.py`, not the package's `verdicts.py`, and that file
  specifies "ties in k broken by edge order". Per the reasoning discipline (no patching around), the work stopped and
  the author was asked. **The author's ruling (7 October): break ties by edge order.** `_decile_overlap` now uses a
  stable sort. That changes no Kickoff 36 number: both simulated sets give the same overlaps as before. It makes 12 of
  18, and `test_decile_ties_are_broken_by_edge_order` plants a tie.
- **A seed I first got wrong.** Kickoff 41's runner sets one seed, 41, for every permutation and bootstrap
  (`k40.SEED = 41`, and "Seed 41" in its sealed predictions). I first wrote 40 into the file's `meta`. The p-values
  then differed by 10⁻⁴ to 5·10⁻³ while everything else matched. With 41, everything matches. The archive was right.
- **Five places where the README text the amendment gives did not match the data.** **The author's ruling (7
  October): correct them to the data.** Each is checked by a test in `test_readme_numbers.py`.
  1. Finding 7 said the four IBM-flagged pairs "carry the most extreme values on the chip". Three do (27-28, 72-73 and
     32-33 are among the six largest |k| on every day). 71-72 ranks 99th, 170th and 171th of 176. It now says "and
     three of them carry the most extreme values on the chip; without all four ...". Section 5.1's "three of the four"
     was already right.
  2. Finding 8 said "SD of k 1.1, against 0.3 on ibm_fez". Kickoff 31's ibm_fez SD of k_A is 0.20 (ibm_kingston
     0.25). It now says "against 0.2 on Kickoff 31's ibm_fez pairs".
  3. Finding 10 said 11-12 and 72-73 "read about 0.3 higher on the same seven programs on both days". 11-12 did (+0.33,
     +0.35). 72-73 read +0.21, then +0.11, which is why the switch is MIXED. The sentence now says so.
  4. Finding 8 gave "15:06 to 16:20 UTC". Kickoff 40's tasks ran from 15:17 (first creation) to 15:50 (last end).
     15:06 is when its runner read its amendment, and its log ends at 15:54. It now says "15:17 to 15:50 UTC".
  5. Finding 10 gave Day 1 at "17:45 UTC". The first task was created at 17:45:43, which is 17:46 under the
     nearest-minute convention. It now says 17:46.
- **A scope word in the amendment, for the record.** For Kickoff 41's Part B it says "mean W 0.945 on 23 pairs". 0.945
  is the mean over all 25 pairs; over the 23 pairs with x it is 0.952. Nothing in the README states it. The test checks
  0.945 over 25.

**Readings and choices, logged.**
- **Rounding.** Kickoff 42's fitted shifts lie on the grid's 0.005 steps, so a two-place figure such as −1.025 rounds
  half away from zero to the amendment's −1.03. The tests of stated numbers allow exactly half a unit in the last
  place.
- **"IBM's figures for them did not move"** (finding 7, the two pairs on qubit 149), kept as the amendment wrote it.
  Their k went from −1.31 and 0.06 to −4.78 and −4.08, then to 2.83 and 0.64. Their x varied by up to 16% (0.054 to
  0.069). The test checks the swing in k against a bound of 20% on x.
- **The "why" sentence for the flagged block.** The amendment gives its sense, not its words ("k is not a kept fraction
  for a pair whose no-offset level is near 0.2"). The four flagged edges read 0.19 to 0.39 without the offset, against
  a chip median of 0.89, and the README says that.
- **`pick --by`.** It already existed, with choices `k` and `x`, undocumented and untested. It now takes `kept-share`
  (the default) and `level`, as the amendment says, and keeps `x`. `k` stays as a name for `kept-share`, so earlier
  invocations work. `pick_pairs` is unchanged. The level is each pair's mean P(A no), as `kept_from_order` returns it.
- **The flagged block** is in `analyse_map` and `persistence_analysis`, empty when nothing is flagged. The vendor's flag
  is read:
  - from IBM's published two-qubit errors, in `archive.map_from_record` and in `manacitra verdict` on an archived file;
  - from the target's figures, in `manacitra map`, written into the counts file's `meta`;
  - from Braket's figures, in `braket_map`.

  `verdict_lines` prints the block only when a pair is flagged. In a Braket run the placeholder pairs have no x, so
  they are already outside the verdict set.
- **Kickoff 42's after-the-fact definitions** (the edge pairs, the shared programs) were not in the runner's script.
  They are taken from its note and checked against the archive, which they reproduce at 0.0.
- **The runner's flagged-edge rule** was a CZ error of at least 0.5; the amendment's is exactly 1.0. On all three days
  they pick the same four edges.

**Tests.** `test_flagged.py` covers:
- the flag and Braket's score, including Kickoff 40's x for every pair;
- a planted flag in a map, with the dead-pair filter, and in persistence;
- Kickoff 35's four edges.

`test_cli.py` tests each `--by` choice against the ranking it should give, that `--by level` changes the pick, and that
`--by x` stops without a score. Five more mutation tests change one field of each new recompute in memory:
- the Kickoff 35 verdict;
- the Kickoff 38 verdict;
- the Braket map verdict;
- Kickoff 41's p_k;
- Kickoff 42's V5.

Each, in four ways, fails the comparison and names the field.

**The inventory.**
- `tests/expected_fields.json` gains 3,414 fields in the 14 cases (4,620 in all).
- `tests/excluded_fields.json` gains 260 entries over 21 files (471 in all), each with its reason. The commonest
  reasons are: inputs (the counts, the tasks with their measured qubits, the pairs, the orders); metadata; notes; the
  provider's figures as read; the runners' design-time synthesis checks; and the placeholder counts for the whole chip,
  which need figures not in this release.
- `test_field_inventory.py` passes.

**The README lines changed:**
- the opening line of the findings;
- finding 2's new sentences;
- finding 6's last sentences;
- findings 7 to 10, with the five corrections above;
- the flagged-pairs paragraph;
- the three "has not shown" bullets;
- the Limits bullet and the new one;
- the Open Quantum guidance, in the README, the adapter's docs and `docs/index.md`;
- the pipeline sentence for `--by level`, and the guidance on choosing the score and the dead-pair filter;
- the kickoffs table: Kickoff 35's row, and four new rows.

`docs/index.md` gains:
- the tie rule and the flagged-pairs paragraph in the persistence rule;
- `--by level`, `published_score_braket` and the dead-pair sentence under choosing pairs;
- a section on the Braket route and its records (no adapter yet);
- the reproduction table's new rows;
- the new dates in section 8.

**The dataset after the addition.**
- `data/` grows from 43 MB to 127 MB, 231 files in `SHA256SUMS`.
- Kickoff 35's three day files are 6.1 MB each, Kickoff 40's map and payoff 9.7 and 12.8 MB, Kickoff 41's map 9.7 MB,
  and Kickoff 42's day files 9.7 MB each.
- The compiled programs and programs as sent add 4.2 and 2.6 MB.
- No file is near GitHub's 100 MB limit.
- **The review archive still carries all of it.** `tools/make_review_archive.sh` zips a fresh single-branch clone, so
  the data are in it twice over, as files and as git objects (compressed). Run on `4ec6ffa`, the commit before this
  report, both scans passed (41 reachable commits) and it wrote a zip of 45.4 MB (45,406,720 bytes) that carries
  Kickoff 35's files.

**Pictures, at the author's request (not part of the amendment).** A subagent drew five candidate images of how the
map works, into an untracked `review-images/` folder. One caption used a word outside the vocabulary boundary (W3),
which was replaced. The author ranked c2, c4 and c5 best and c3 just below, and asked for all three best ones. Each is
now drawn from `data/` by `docs/make_diagrams.py`, as SVG with a PNG; the seven earlier diagrams regenerate byte for
byte. Each has alt text and a caption whose numbers `tests/test_readme_numbers.py` checks.
- **`three-checks.svg`** (c2) is the README's third picture, after the map. It shows Kickoff 31 on ibm_fez as the map
  rule's three checks. The draft left out check 2's p < 0.05 condition; the picture shows it ("p < 1/10000").
- **`whole-chip-days.svg`** (c4) follows the findings list, for finding 7: Kickoff 35's 176 couplers on each day, and
  the published score. The draft gave the score's rank correlation with Day 1's map as "0.08", with its sign flipped;
  the picture gives it as measured, −0.08, "none to speak of".
- **`map-explainer.svg`** (c5) opens `docs/index.md`. It is the whole method in one picture, so it repeats the README's
  first three pictures. Its "carries over" tile now shows the p condition too.

Diagrams 8 and 9 draw thin lines across the whole chip. They use the house blue ramp without its lightest step, which
fails 2:1 contrast against the background; the existing chip map keeps the full ramp.

**CI had been failing since Amendment A4, and nobody had noticed.** Since `983bd8c`, CI on this pull request had
failed in the acceptance tests. Sections 14 to 16 did not report it, and my A6 summary said only that checks were
running. After this amendment's push, I looked. The cause was the seeded resampling fields: their draws come from
numpy's random generators.
- **The shots-resampled intervals** (Kickoff 33, and Kickoff 40's stage 3) differ by 3·10⁻⁶ to 3.2·10⁻⁴ on Linux, even
  with numpy 2.5.3, the runs' version. A multinomial draw can turn on the last bit of a probability, which differs
  between platforms. On this macOS machine they match exactly.
- **Kickoff 42's bootstrap SDs** (binomial draws) match on Linux with numpy 2.5.3, but differ by up to 0.013 with numpy
  2.4.6. That is the newest numpy for Python 3.11, which CI tests; numpy 2.5 needs Python 3.12.
- **Everything else**, every verdict, correlation and fit and all 414 compiled-program records, passed on both CI jobs.

I first proposed pinning numpy 2.5 for development and CI, and the author agreed. That could not work, for both reasons
above, so I went back to the author with the facts. **The author's ruling (7 October): a separate tolerance for these
fields only, recorded as a change to A4's "every field at 10⁻⁶".**
- The shots-resampled intervals are compared at 10⁻³. That is about three times the largest difference seen, and below
  the Monte Carlo error of a 2,000-draw percentile.
- The bootstrap SDs are compared at 10⁻⁶ under numpy 2.5 or later, and named as not compared under an older numpy.
- A missing field, a type change or a value that is not finite is never relaxed. Every other field stays at 10⁻⁶
  everywhere.

The rule is `resampling_rule` in `tests/_reproduce.py` (with `RESAMPLED_SHOTS` and `RESAMPLED_BOOT`), with
`test_the_resampling_rule`. The README, CONTRIBUTING, `docs/index.md`, `expected_fields.json`'s description and the
acceptance table say so. Under numpy 2.4.6, installed apart from the project's environment, `test_reproduction.py`
and `test_field_inventory.py` pass: 120 tests. The mutation tests still fail on a mutated interval: a change to 999,
a removal, None or NaN is far beyond 10⁻³ or not finite.

**After the amendment:**
- 469 tests pass (350 before; 119 new);
- Ruff is clean;
- the identifier scan is clean on the full tree, and the git identity scan is clean on every reachable commit;
- `data/SHA256SUMS` matches every file.

**Not in this amendment, and not done:**
- Kickoff 39;
- an Amazon Braket adapter (Kickoff 02);
- merging, making the repository public, or turning on signing;
- any provider submission.

## 18. Amendment A8: fixes from the fourth review (7 October 2026)

**The review.** Codex, in run mode, on the archive at `0f3cf610a1a8`: 47 PASS, 5 FAIL, 0 CANNOT CHECK; one Major and
four Minor findings, no Blockers. Every finding is accepted. The archived statistics reproduced in the reviewer's own
code, and the 469 tests and the CI run on that exact commit passed.

**The standing rule this amendment adopts.** A test that calls the package's reader on both sides of a comparison does
not test the reader. So the expected values in the new tests come from `tests/_independent_readings.py`. That script
uses the standard library and numpy, and does not import `manacitra`. It decodes each record by its reading, as the data
README describes it, and the tests carry its output as literals, with a comment saying so.

**Each finding, the fix, and the test that now covers it.**

| ID | finding | the fix | test |
|---|---|---|---|
| R1 (Major) | `pick`, `verdict` and `report` read every archive with IBM's bit positions. On Kickoff 40's map, `pick --by level` gave 60-61, 13-14, 42-43, …, sharing one pair with the right eight, and `verdict` gave MAP PRESENT, r_split 0.983, r_AB 0.675. Kickoff 41's map and Open Quantum's `main.json` (r_split 0.991, r_AB 0.877) were misread too. Reproduced exactly here before the fix. | **The data.** Every record with counts declares `meta.bit_reading`: `qiskit-adjacent` (the 9 IBM files), `openquantum-reversed` (`main.json`, Kickoffs 37 and 38), `braket-measured-qubits` (the 7 Braket files) or `per-pair` (the 3 simulations). That is 22 records, and the field was inserted as one line at the top of each `meta` block, so nothing else in a file changed (34 lines in all). Where positions or tasks do not all measure the same pairs (Kickoffs 32, 35, 37, 38, and 40's stage 1), `meta.bit_reading_note` says how they are laid out. The two Braket map records name their figures record in `meta.figures_file` and `meta.figures_part`. **The reader.** `archive.p11_table` dispatches on the field, to the one reader per reading that the route-aware recomputes also use (`p11_from_bitstrings`, `p11_classical_index`, `braket_p11`); `rigetti_map` and `braket_map` now call it. A record without the field, or with an unknown value, is refused (`UndeclaredReading`), naming the field. A record whose positions measure different pairs, or whose counts are per task, has no single table and is refused (`NotATable`). **The commands.** They read an archived map through `archive.map_view`, which gives that run's own analysis: `map_from_record` on every pair for IBM; `rigetti_map`'s working pairs for Open Quantum; `braket_map`'s verdict set, with x from the figures record, for Braket. A record that is not a map run is refused (`NotAMap`). `verdict` names the reading and the set it used. With `--no-score` or `--perm-seed`, it runs the rule again on the same pairs. | `test_bit_readings.py`: `verdict` on `main.json` (MAP PRESENT, 0.985 and 0.971 on 22), on `k40-map.json` (DIAGNOSTIC, 0.9737, 0.8115, r_Ax 0.198 on 23, x from `k40-figures.json`) and on `k41-map.json` (DIAGNOSTIC, 0.816, 0.904). `pick --by level` and `--by x` on Kickoff 40, against the independent literals. A missing and an unknown reading refused by all three commands. The dispatch shown to matter: the same counts declared `qiskit-adjacent` give exactly the old wrong eight. Non-maps and non-tables refused. The commands agree with the acceptance cases. `test_data_meta.py`: every record with counts declares one of the four values, and no other record does. The Kickoff 31 pick test is kept. |
| R2 (Minor) | The data index covered the 42 JSON records, not the program files. | The data README says that `meta` blocks belong to the JSON records, and that the program files are data under `data/LICENSE`, indexed by a generated catalogue. `tools/program_catalogue.py` writes `data/PROGRAMS.md`, read from the run records that sent or returned each file: one row per file, with its kind (as sent, or compiled as returned), the run and task, the processor and route, the task's UTC times and shots, and its SHA-256. A file sent more than once has one line per use: Kickoff 40's stage 2 and 3 programs carry Kickoff 41's re-sends, the Kickoff 37 programs carry Kickoff 38's, and `k37-P27-A-no.qasm` also carries Kickoff 34b's main-job use, from the `programs` entry in `main.json`'s meta. `SHA256SUMS` includes the catalogue. | `test_program_catalogue.py`: the catalogue regenerated byte for byte; every program file has a row and every row an existing file, with its SHA-256 checked; the catalogue is in `SHA256SUMS`; `k37-P27-A-no.qasm`'s row lists Kickoff 34b's use, Kickoff 37's four and Kickoff 38's one. |
| R3 (Minor) | "The whole gain is one pair … the two picks otherwise tie" said more than the test measured. | Finding 9 now says: "The gain is dominated by one pair: Rigetti's figures rated 94-95 sixth best of 23, and it was the worst on the workload. The three pairs only the level pick chose and the two only the x pick chose, apart from 94-95, differ in mean fidelity by 0.0001." The kickoffs table's "one pair" became "dominated by one pair". The counterfactual with 94-95 removed from the pool is left out. | `test_finding_9_the_level_only_pairs_against_the_x_only_pairs_apart_from_94_95`: the two sets (0-1, 24-25, 87-88 against 22-23, 65-66) and the difference, 0.00013 to 10⁻⁴. The independent script (`k41_one_pair`) computes W from the raw counts and gives 0.00013, 94-95 sixth by x, and 94-95 the worst. |
| R4 (Minor) | "Neither has been tested on a third chip" (the kept share was tested on ibm_kingston), and "did not move" for x on qubit 149. | The README and `docs/index.md` now say: "the kept share chose better pairs on ibm_fez and was not settled on ibm_kingston; the plain level … chose better pairs on the Rigetti processor, on the same day and a day later, where the kept share did not … On the Rigetti processor both scores were scored against the published figures in the same payoff runs; no run has yet compared the two scores against each other under a rule fixed in advance." Finding 7 now says: "while k fell by 3.5 and 4.1 on Day 2 and came back by 4.7 and 7.6 on Day 3, and x changed by at most 16%." | `test_the_scores_compared_on_each_chip`: ibm_kingston's NOT SETTLED, and both sentences in the README and in `docs/index.md`. In `test_finding_7`: k's falls on Day 2 round to 3.5 and 4.1 and its rises on Day 3 to 4.7 and 7.6, and the largest change in x rounds to 16% (16.2% and 15.4%). |
| R5 (Minor) | The pipeline diagram's footer still said Kickoff 35 was running. | The footer now reads "Persistence (how long a map lasts) is a fifth step: on ibm_fez a whole-chip map held for two days (finding 7); beyond that is open." Regenerated: only `pipeline.svg` and `pipeline.png` changed, and the other eight diagrams (and the chip-map table) are byte for byte. | `RETIRED`, one list of the phrases the README has retired, each with the amendment that retired it. The README is checked against it, and so are `docs/index.md` (by the author's ruling of 7 October) and the text of every SVG in `docs/diagrams/`, extracted from the XML. With the old `pipeline.svg` put back, the test fails on it. |
| R6 (note) | `resampling_rule` chose the relaxed fields by a pattern on their names. | The 28 relaxed fields are marked on the field itself in `tests/expected_fields.json`: `"compare": "resampled-shots"` (9) or `"compare": "resampled-bootstrap"` (19). The rule reads the mark, and `load_inventory` refuses an unknown mark. The patterns are gone. | `test_the_marked_fields_are_exactly_the_intended_ones` lists the 28. `test_the_resampling_rule` checks that an unmarked field with the same name is compared at 10⁻⁶. |

**Readings and choices, logged.**
- **What the commands now refuse.** A record that is not a map run: the isolation runs (Kickoff 32), the payoffs (Kickoffs 33, 40 and 41), the whole-chip days (Kickoff 35), the placement and activity runs (Kickoffs 37, 38 and 40's stage 1) and the scans (Kickoff 42). Before, some of these were decoded silently, wrongly. A counts file written by `manacitra map` is read as before.
- **Where a pick ranks.** `pick` ranks within the set the run's verdict uses, so it never ranks a pair the run excluded: every pair for IBM, the working pairs for Open Quantum, the verdict set for Braket. Kickoff 40's level pick on that set is the eight the amendment gives.
- **71 QASM files, not 70.** The catalogue lists 116 Quil and 71 QASM files: Kickoff 40's 50 programs as sent, Kickoff 42's 18, and the three Open Quantum programs. The review counted 70.
- **Three readings, resolved by the author's rulings of 7 October**, after the first push of this amendment:
  - **Finding 7's moves.** "k swung by 3 to 4" fit only the fall. It now gives the measured moves: "while k fell by 3.5
    and 4.1 on Day 2 and came back by 4.7 and 7.6 on Day 3, and x changed by at most 16%." `test_finding_7` checks all
    four numbers and the 16%.
  - **The two scores.** On the Rigetti processor, the level and the kept share were each scored against the published
    figures in the same payoff runs, not against each other. The README and `docs/index.md` now say: "On the Rigetti
    processor both scores were scored against the published figures in the same payoff runs; no run has yet compared
    the two scores against each other under a rule fixed in advance."
  - **Kickoff 34b's program.** `main.json`'s meta gains a `programs` entry, inserted as one line with nothing else in
    the file changed. It names `k37-P27-A-no.qasm` as the main job's position 1 ("A no", the run's `01-A-no.qasm`),
    with its SHA-256, and says that the other 15 of its 16 programs as sent are not in this release. The catalogue row
    for that file now lists Kickoff 34b's use beside Kickoff 37's four and Kickoff 38's one.
    `test_the_p27_program_lists_every_run_that_sent_it` checks it. Kickoff 34b recorded times per wave, so its line
    gives wave 1's submission and its last completion, and says so.

  The phrases these replace are on the retired list, which is checked against the README, `docs/index.md` and the text
  of every diagram. `docs/index.md` was added to the check by the author's ruling of 7 October; it carries none of
  the phrases. The build report keeps the old phrases on purpose, as the record of them.
- **The figures file is found beside the record.** `map_view` reads `meta.figures_file` from the record's own folder, so a copied map record needs its figures record beside it. The tests copy both.

**After the amendment:**
- 541 tests pass at the amendment's first push (469 before; 72 new, most of them one per data record or per
  diagram), and 543 after the rulings of 7 October (two new: the catalogue's Kickoff 34b line, and `docs/index.md` against the
  retired list);
- Ruff is clean;
- under numpy 2.4.6, installed apart from the project's environment, the reproduction, inventory and reading tests pass (134);
- the identifier scan is clean on the full tree, and the git identity scan is clean on every reachable commit;
- `data/SHA256SUMS` matches every file, the catalogue included.

**Not in this amendment, and not done:**
- Kickoff 39;
- an Amazon Braket adapter (Kickoff 02);
- merging, making the repository public, or turning on signing;
- any provider submission.

The rubric is revised beside this amendment, outside the repository (G2's count, C3c's expected picks, A5's scope).

## 19. Amendment A9: the repository's home (7 October 2026)

**What happened.** The author transferred the repository from the author's account to the organisation. Its home is now
`https://github.com/dogma-guru/manacitra`; the old address, `github.com/dogmaguru/manacitra`, redirects. A citation and
a signing identity should name the home, not a redirect, from the first public commit.

**The eight replacements**, `github.com/dogmaguru/manacitra` to `github.com/dogma-guru/manacitra`, and nowhere else:

| file | line | what |
|---|---|---|
| `README.md` | 139 | the `git clone` line |
| `README.md` | 144 | the `pip install "git+https://..."` line |
| `README.md` | 182 | the citation |
| `CITATION.cff` | 11 | `repository-code` |
| `pyproject.toml` | 45 | `Repository` under the project URLs |
| `src/manacitra/archive.py` | 28 | `REPOSITORY`, the address the data-not-found message prints |
| `tests/test_data_location.py` | 34 | the assertion on that message |
| `docs/index.md` | 398 | `--cert-identity` in the documented verify command |

The documented identity named `refs/heads/main`, so only the owner changed. It now reads
`https://github.com/dogma-guru/manacitra/.github/workflows/sign.yml@refs/heads/main`.

**The signing workflow needs no change.** `.github/workflows/sign.yml` builds the identity it verifies from the
repository's own name, on line 82 (signing on a push) and on line 113 (signing a release). Both lines read
`verify-cert-identity: https://github.com/${{ github.repository }}/.github/workflows/sign.yml@${{ github.ref }}`, so the
identity follows the repository's home. Signing stays off.

**The build report keeps the old address twice**, in section 6's ruling on the repository URL and in section 8's
description of the documented identity. It is the record of what was true when each section was written, so those
lines are not rewritten.

**The test.** `tests/test_repository_home.py` holds one constant,
`HOME = "https://github.com/dogma-guru/manacitra"`, and three checks:
- `archive.REPOSITORY`, `CITATION.cff`'s `repository-code`, `pyproject.toml`'s `Repository` and the README's citation
  line each equal it, and the README's two install lines and the docs' verify command contain it;
- no file that git tracks, other than `build-report.md`, contains the old owner's path (`github.com/` followed by the
  old owner and a slash). The check walks `git ls-files`, skips binaries by extension and names any offender. With the
  old address put back into `CONTRIBUTING.md`, it failed and named `CONTRIBUTING.md:104`;
- every documented `--cert-identity` in `docs/index.md` starts with `HOME + "/.github/workflows/sign.yml@"`.

**A reading, logged: the scan's allow-list.** The identifier scan allowed W7 inside the repository's address only as
the one exact string ruled on in section 6, so the new address was a finding (`vocabulary-w7`) until the scan allowed
it. `tools/scan_patterns.py` now allows the new address as one more exact string (`repository-home`). It keeps the old
one (`repository-url`), because the build report keeps it, and the new test keeps the old address out of every other
file. The boundary is no wider: the organisation's name outside this repository's address, and the organisation's
address with another repository, are still findings. `tests/test_scan.py` checks the new address as allowed and both
of those as flagged. The amendment's text did not name this change; without it, the replacements would fail the
scan.

**Before going public: the scan over the whole history, and a ruling.** Going public publishes every commit, not only
the tree, so the tree scan was also run on every file version reachable from the repository's refs on GitHub (its
branches and the pull requests' refs: 7 refs, 522 file versions). Personal paths and the local user name are not found
anywhere. It found one thing: two versions of `tests/test_scan.py` from 5 October (commits `a917519` and `a2beea3`,
on `main` through pull request 1) hold W7's two words as a test sample, at line 33. When they were written, W7's
pattern needed both words, so splitting the string kept the line clean. Amendment A1 then widened the pattern to the
first word on its own, which these versions now match. The current file splits the word itself. **The author's ruling
of 7 October:** accept it and go public with the history as it is. It is the organisation's own name, in a test of the
scan, and A4's ruling stands: no history is rewritten. The git identity scan is clean on every reachable commit.

**After the amendment:**
- 549 tests pass (543 before; 6 new: the three above and three scan cases);
- Ruff is clean;
- the identifier scan is clean on the full tree, and the git identity scan is clean on every reachable commit;
- `data/` is unchanged, and `data/SHA256SUMS` matches every file;
- `CHANGELOG.md` gains one line under the first version: the repository's home is `github.com/dogma-guru/manacitra`.
- **The first CI run under the organisation** was on `d1d8250`, this amendment's commit. The `ci` workflow on the push
  is run 37703906284, and on the pull request it is run 37703907727. Each has three jobs, not two: the scan, and the
  tests on Python 3.11 and 3.13. All three passed in both runs, and `dco` (37703907725) and `sign` (37703906278) passed
  too. The organisation's Actions policy blocked nothing: the repository allows all actions and does not require SHA
  pinning, so no setting was changed. Signing stays off: the repository variable `MANACITRA_SIGN` is `false`, and the
  gate signs only on `true`.
- **Correction, after the merge.** This section first said "the workflows pin by SHA anyway". Only the Sigstore action
  in `sign.yml` is pinned by SHA; `actions/checkout@v4` and `actions/setup-python@v5` are pinned by their major-version
  tag in all three workflows. The sentence is corrected above.
- **CI runs once per change, after the merge** (the author's ruling of 7 October). `ci` ran twice on every pushed
  commit of a pull request, once for the push and once for the pull request, and the tests take 14 to 19 minutes a
  run. It now runs on pull requests and on pushes to `main` only. `dco` and `sign` are unchanged.
- **The tests run in parallel, after the merge** (the author's ruling of 7 October). CI runs
  `pytest -q -n auto --dist loadfile` (`pytest-xdist`, added to the `dev` extra; CONTRIBUTING gives the same command).
  `loadfile` keeps each test file on one worker, so a file's shared fixtures, such as the one that recomputes all 31
  acceptance cases, are computed once, not once per worker. Locally (10 cores, 4 workers), all 549 tests pass in 142 s,
  against 300 to 380 s in one process, and 180 s with tests spread across workers one by one.
  On GitHub's runners the gain was smaller. In the first parallel run (on `559bfb9`), the tests took 732 s on Python
  3.11 and 787 s on 3.13, against 1,147 s and 866 s in one process (on `d1d8250`).

**After going public (7 October).**
- **Public.** The author made the repository public after the merge (`5a826cd`) and the follow-up on `main`
  (`00de44c`). The git identity scan was then clean on every reachable commit (59).
- **Signing on.** The author set `MANACITRA_SIGN` to `true`. The signing run for `559bfb9` (run 37710677835) was run
  again, with the gate now open. It signed the 233 targets `tools/sign_targets.py` lists, and verified each against the
  workflow's identity. The bot committed the bundles to `main` as `17ecfaf`.
- **What the first bundle commit broke, and the fix.** These checks had run only without bundles in the tree:
  - The data tests read every `.json` file under `data/` as a run record, so each bundle failed three of them. With the
    index, the field inventory and the README's run dates, that was 704 failures.
  - `archive.fez_or_kingston` in the package read the bundles beside the IBM records too.
  - `tools/sha256sums.py` and the tree scan already skipped bundles.

  The fix:
  - `archive.is_bundle` and `archive.records()` (every run record, without bundles) are now used by those tests and
    by `fez_or_kingston`. `test_the_signing_bundles_are_not_records` checks it.
  - **The bot's identity.** The git identity scan flagged the bundle commit's author and committer, GitHub Actions'
    bot. Amendment A3 approved that exact address for the bundle commits, and the DCO check exempts them. But A4's list
    of identities in git metadata did not name it. It is now approved as author and committer only.
- **Funding.** The author asked for all three links:
  - `FUNDING.yml` (Patreon) in the organisation's `.github` repository, which GitHub uses for every organisation
    repository without its own. A Sponsor button also needs Sponsorships ticked in each repository's settings.
  - `Funding` under `[project.urls]` in `pyproject.toml`.
  - A "Support" section in the README.

  The Patreon address carries W7 as one word, so the scan allows that exact address (`patreon`), by the author's
  ruling of 7 October. The name on its own is still a finding. `tests/test_scan.py` checks the address as allowed and
  the name elsewhere as flagged.
- 552 tests pass, and both scans are clean.

**Not in this amendment, and not done:**
- Kickoff 39;
- an Amazon Braket adapter (Kickoff 02);
- merging, making the repository public, or turning on signing;
- any provider submission;
- the organisation's `.github` repository (its profile README and `FUNDING.yml`), which the author handles.

## 20. Amendment A10: the public posture, Part 1 (7 October 2026)

**The posture, as the author ruled it.** One committer. Anyone may fork, read, cite, run and reuse the code and the
data under their licences. Pull requests from outside the repository are not accepted at this time, and questions and
problems go to Issues. Part 1 is the files, on the branch `feat/public-posture` from `main` at `52fea94`. Part 2 is
the GitHub settings, which are the author's to change, and nothing here touches them. Nothing in `data/` changed.

**Files added:**
- `.github/workflows/outside-pr.yml`: closes a pull request from a fork, with one comment;
- `.github/PULL_REQUEST_TEMPLATE.md`: three lines (the third blank);
- `.github/ISSUE_TEMPLATE/`: `reproduction.yml`, `new-processor.yml`, `other.yml` and `config.yml` (blank issues on,
  no external links);
- `SECURITY.md`: the private route for a security report;
- `.github/CODEOWNERS`: one line naming the author's account as owner of every path, by the author's ruling of 7
  October, until a team exists;
- `tests/test_public_posture.py`: four tests (below).

**Files changed:**
- `CONTRIBUTING.md`: a new first section, "What is accepted", and "Before a pull request" became "Before a change";
- `README.md`: the posture sentence, beside the Patreon line;
- `.github/workflows/sign.yml`: the `build-release` job, and its header;
- `docs/index.md` section 9: the release identity and its verify command;
- `tools/scan_patterns.py` and `tests/test_scan.py`: the `CODEOWNERS` line;
- `.gitignore`: `review-images/`;
- `CHANGELOG.md`.

**Why `pull_request_target` is safe in `outside-pr.yml`.**
- **The risk.** This trigger runs in the repository's own context, with a token that can write to pull requests. That
  is dangerous only when the workflow checks out or runs the fork's code.
- **What this workflow does.** Its one job runs only when the head repository is not this one. Its one step calls
  `gh pr close --comment` with fixed text.
- **What it reads from the event.** Only the pull request's number and the head repository's name. Never the fork's
  title, body, branch or files.
- **What it holds.** No checkout and no `uses:` at all, and the permission `pull-requests: write` only.
- **What it leaves alone.** Pull requests from branches inside the repository (the author's, and Dependabot's, which
  GitHub opens from inside it) are not closed.
- **The test.** `test_an_outside_pull_request_is_closed_without_running_its_code` checks every one of these points,
  including the exact set of event fields read. With a checkout step added, it fails.

**The release path, which had never run.**
- **The problem.** Before this amendment, `sign.yml`'s `sign-release` job (lines 95 to 115 at `52fea94`) downloaded
  the release's assets into `dist/` (line 107) and signed `./dist/*` (line 111). A release made from a tag carries only
  GitHub's automatic source archives. `gh release download` does not fetch those, so the job had nothing to sign, and
  the step could fail on an empty glob.
- **The new job.** `build-release` (lines 99 to 118) runs only on the `release` event. It checks out the tag, installs
  `build`, runs `python -m build` (line 112), writes `dist/SHA256SUMS`, and runs `gh release upload "$TAG" dist/*`
  (line 118).
- **Signing.** `sign-release` (line 120) now `needs: [gate, build-release]` (line 121). It downloads the three assets
  (line 132), signs them (line 136) and attaches the bundles (line 140). It still verifies against the identity
  `sign.yml@${{ github.ref }}`, which on a release is `refs/tags/<tag>`.
- **Documentation.** `docs/index.md` section 9 now says that a release's assets are signed under that identity, while
  the data files stay signed under `@refs/heads/main`, and gives the verify command for the `v0.1.0` wheel.
- **Checked here, not on GitHub.** The build was run from a clean export of this branch in a fresh environment.
  `python -m build` made `manacitra-0.1.0.tar.gz` (184 KB) and `manacitra-0.1.0-py3-none-any.whl` (121 KB), which do not
  carry `data/`, and the identifier scan is clean on their 82 files.
- **The test.** `test_the_release_is_built_before_it_is_signed` reads `sign.yml` job by job. It checks the order, that
  `build-release` runs only on `release`, the `needs`, and the identity. With `needs` set back to `gate`, it fails.
- **Not done.** The tag and the release are the author's (Part 2, step 8). No tag was made.

**Readings, logged.**
- **Where the README sentence goes.** The amendment says "in the last section, beside the Patreon line". The Patreon
  line is in "Support", the section before "Licence", so the sentence sits beside it there.
- **CONTRIBUTING's licence section is kept,** as the amendment says. It still describes contributions "accepted under
  the Apache License 2.0": the terms of any contribution, which today means the author's own branches.
- **The scan.** The new files tripped the scan once: the `CODEOWNERS` line carries W7 as one word. The scan now allows
  that exact line (`codeowners`), and `test_scan.py` checks the line as allowed and the account name elsewhere as
  flagged. `tools/scan_secrets.py` itself is unchanged.
- **No new access token was needed.** Pushes go over SSH, and the pull request is opened with the existing token.

**Hygiene.**
- **The drafts folder.** `review-images/` is ignored.
- **No stray drafts.** No section drafts sit outside `build/`.
- **The latest bot commit is clean.** `17ecfaf`, the first bundle commit, adds 233 files, and every one is a
  `.sigstore.json` bundle.

**After Part 1:**
- 558 tests pass (552 before; 6 new: the four above and two scan cases);
- Ruff is clean;
- the identifier scan is clean on the full tree, the new files among it, and the git identity scan is clean on every
  reachable commit;
- **CI on the branch** (`6090196`, pull request 3): `ci` run 37718304005 passed. Its jobs were the scan, and the tests
  on Python 3.11 and 3.13, which took 734 s and 509 s. `dco` (37718303983) and `sign` (37718284750) passed too. `ci` ran
  once, on the pull request only, as the trigger set after the merge intends.

**Not in Part 1, and not done:**
- any GitHub setting;
- tagging or releasing;
- Kickoff 39;
- the Braket adapter (Kickoff 02);
- any provider submission.

## 21. Amendment A11: fixes from the first public trial (7 October 2026)

**The trial.** Codex, in run mode, worked from the public address alone, at `52fea94`. Its marks were 35 PASS, 14 FAIL
and 4 CANNOT CHECK.

**What passed:**
- the installs, the Python block and the three examples;
- the three independent recomputations: k for 106-107 and 20-21, the payoff at 35.55%, and Kickoff 35 at r 0.8616 and
  9 of 18;
- the manifest and the acceptance table;
- four signatures, the three negative controls and the transparency-log entry;
- the scan over the whole history.

**Where the fourteen FAILs went.** A11 sorts them as follows, and names the IDs given here. The trial's own report,
which would list every FAIL by ID, is not in this repository. A per-item list needs it.

| group | count | IDs named in A11 | disposition |
|---|---|---|---|
| the trial's own mistakes | 5 | — | corrected in the rubric (r1) |
| closed by A10 Part 1, or by settings the author made on 7 October | 4 | — | nothing more here |
| the organisation's and Patreon's pages | 2 | H4a (with R-C) | the author's (A11, "For the author") |
| this amendment | 3 | C5, C2, G3/D2 | fixes 1, 2 and 3 below; the small fixes of item 4 answer A6, A7 and G3 |

**The rulings, as A11 records them.**
- **R-A (the job IDs; the trial's Blocker H1b).** The eleven IBM `meta.job_id` values stay. They are provenance, kept
  on purpose since the first implementation and listed in a column of the data README's table. They are not
  credentials or account identifiers. The Open Quantum task IDs and the Braket task ARNs were left out and stay out.
  No history is rewritten. `data/README.md` now says so under Formats ("Job IDs").
- **R-B (the organisation's contact; Blocker H4c).** The organisation's public contact address is approved. It
  appears nowhere in this repository, and nothing here changed.
- **R-C (the Patreon page; H4a).** It is the author's page, out of scope here.

**Two of the author's rulings, made when A11 arrived:**
- **The merge method.** A11's pull request is merged with a merge commit, not squashed. A11 says the repository is
  squash-only, but it is not: merge commits, squash and rebase are all allowed. A squash with only the pull request's
  title as its message would drop every `Signed-off-by` line from `main`.
- **The title.** `.zenodo.json` carries A11's title, "Manacitra: a map of your qubits". `CITATION.cff` and the
  README's citation line take the same title, so that all three agree.

**1. `report` says what it reports (C5).**
- **Before**, `manacitra report ibm_fez/k31-map.json` printed only the table:

  ```
  | pair | k_A | k_B | published x |
  |---|---|---|---|
  | [106, 107] | 1.061 | 1.014 | 0.0160 |
  ```

- **Now**, it prints what `verdict` prints, byte for byte, then a blank line, then the table:

  ```
  Kickoff 31 (the map)
    processor: ibm_fez
    UTC: 2026-10-05T12:36:54.116023Z
  read as qiskit-adjacent; all 27 pairs
  verdict: DIAGNOSTIC  (map rule (Kickoff 31))
    r_split_A = 0.8677
    r_AB = 0.8213
    p_AB: p < 1/10000 (0 of 10000)
    r_AB_given_x = 0.8162
    r_Ax = -0.1789
    [ ] noise: r_split < 0.3
    [x] r_split >= 0.5
    [x] r_AB >= 0.4 with p < 0.05
    [x] r_AB.x >= 0.3
    [x] |r_Ax| < 0.5
    [ ] redundant trigger

  | pair | k_A | k_B | published x |
  ...
  ```

- **How.** Both commands call one function, `cli.context_and_verdict`: the context from `meta` (kickoff, processor,
  UTC time), the reading and the pair set, then `verdict_lines`. So `verdict` gained the three context lines too, and
  A8's tests that began at "read as" now find that line among the output.
- **Tests.** `test_report_gives_the_verdict_before_its_table` runs on `ibm_fez/k31-map.json` and on
  `rigetti_cepheus_1_108q/k40-map.json`. It checks that `report`'s output begins with `verdict`'s, followed by the
  table, and that the header names the processor and the reading. `docs/index.md` section 4 describes the output.

**2. The simulator is not a dry run (C2).**
- **The first line.** `manacitra map` now prints `local simulation; nothing sent to a provider` first when the backend
  is local. It prints `dry run; nothing sent; add --submit to submit` first on a provider backend without `--submit`.
  The old last line of a dry run ("nothing was sent. Add --submit to send it once.") is gone, since it said the same.
- **`map --help`** and the module docstring carry both sentences.
- **The README's sentence** (in "Install and try it") now reads: "a provider backend is a dry run unless `--submit`
  is given; the simulator runs at once, on your machine, and sends nothing". CONTRIBUTING's rule and `docs/index.md`
  section 6 say the same.
- **Tests.** `test_the_simulator_says_it_is_local`, `test_ibm_is_a_dry_run_without_submit` (its first line) and
  `test_map_help_says_both`.

**3. The payoff recompute, documented (G3, D2).**
- **The data README** now gives the four facts the trial had to infer: the prior map is Kickoff 32's dense condition,
  not `k31-map.json`; each R1 to R8 ran twice and is pooled per pair (16,000 shots); the fidelity is the squared
  Hellinger overlap against `circuits[j].ideal`, on uncorrected counts, state order q0 + 2 q1; and the published pick
  uses the x recorded at submission. It also gives both picks and the two mean errors. Finding 4 in the README says
  the same in one sentence and names `examples/03_pick_pairs.py`.
- **Independent check.** The values come from `tests/_independent_readings.py`'s new `k33_payoff`, which does not
  import the package. It gives the map's pick 106-107, 88-89, 151-152, 94-95, 142-143, 129-130, 13-14, 114-115, and
  the published pick 22-23, 5-6, 85-86, 70-71, 114-115, 123-124, 142-143, 106-107. Pooled shots are 16,000 per circuit
  per pair. The mean errors are 0.002213 and 0.003434, which is 35.55% less.
- **One correction to A11.** These picks are what `examples/03_pick_pairs.py` prints, not "the README's pick": the
  README does not list them.
- **Tests.** `tests/test_payoff_recompute.py` checks that the example (through the package) prints those picks and
  errors, that the record's order implies the pooling, that the archived analysis's picks agree, and that both READMEs
  say it.

**4. Small documentation fixes (G3, A6, A7).**
- **Setup.** The clone block creates and activates a virtual environment before `pip install`. `pip install -e
  ".[dev,aer]"` is named as the install that gives `pytest`, beside the clone block and beside the reproduction
  sentence.
- **The Python block** is labelled "paste this into a Python session". That was the runner's choice: the README's
  three examples are already files.
- **Sealing.** Under picture 6 there is now a four-command example: `seal`, `reveal`, `verify`, and a one-byte change
  that gives NO MATCH with exit status 1, all run here before writing. One sentence says what the record shows: the
  file existed when its hash was posted, and the time comes only from where it was posted, because the record's
  `sealed_utc` is the sealing machine's clock.
- **The transparency log.** `docs/index.md` section 9 says where a bundle's `logIndex` is (under
  `verificationMaterial.tlogEntries`) and gives the search page. It also says that `sigstore verify` needs no account,
  while the Actions job logs need a signed-in GitHub account.
- **`CITATION.cff`'s abstract** names the Rigetti Cepheus-1-108Q runs, through Open Quantum and Amazon Braket, beside
  the IBM and simulated ones.
- **A fixed version.** The citation paragraph says how to cite a commit until `v0.1.0` is tagged. The release
  follow-up removes that sentence.
- **`.github/FUNDING.yml`** gives the Patreon page as `custom:`. `test_the_three_patreon_references_agree` checks it,
  the README's Support section and `pyproject.toml`.
- **`.zenodo.json`** is exactly A11's text. `test_the_zenodo_metadata_matches_the_citation` checks that it parses, and
  that its title and creator are `CITATION.cff`'s. The README has no topics line, so the keyword check is skipped, as
  A11 allows.
- **A slip of mine, fixed.** `docs/index.md` section 4 said "the kept share chose the better pairs on ibm_fez"
  twice in one sentence, a slip from A8. It is fixed.

**5. A bug A10 Part 2's step 5 test found: re-signing a changed file.**
- **What happened.** The step 5 test merged a change to `data/README.md` (pull request 4, merged as `ba0c558`). The
  signing run that followed, 37722980126, failed: the Sigstore action refused to overwrite the file's existing bundle
  ("Refusing to overwrite outputs without --overwrite").
- **What it meant.** No signed file had changed before, so re-signing had never run. Until a fix lands, the bundles of
  `data/README.md` and `data/SHA256SUMS` on `main` cover their earlier contents, and checking those two files against
  their bundles fails.
- **The ruleset is not the cause.** The rules on `main` block deletion and force-pushes, and the run failed before
  it pushed anything.
- **The fix.** `sign.yml`'s `sign-files` job now removes the old bundles of the files it is about to sign, in a step
  just before Sign. This amendment changes both files again, so its merge re-signs them.
- **The test.** `test_a_changed_file_loses_its_old_bundle_before_it_is_signed_again` checks the step and its place.
  With the step removed, it fails.

**After the amendment:**
- **Tests:** 570 pass (558 before; 12 new);
- **Ruff:** clean;
- **The identifier scan:** clean on the full tree, the new files among it. `.zenodo.json` carries "Dogma LLC", which
  the ownership allowance already covers;
- **The git identity scan:** clean on every reachable commit;
- **Data:** only `data/README.md` and its line in `data/SHA256SUMS` changed under `data/`.

**Merge and release (8 October 2026).**
- **The merges.**
  - Pull request 4, A10's step 5 test, was merged as `ba0c558`.
  - Pull request 5, this amendment, was merged as `05de88e`, with a merge commit, by the author's ruling. Its checks
    had passed: `ci` 37723470730, `dco` 37723470966 and `sign` 37723450747.
  - The signing run on `main` after the merge (37724865784) re-signed `data/README.md` and `data/SHA256SUMS`, with the
    stale-bundle fix in place. The bot committed them as `d37d0a2`.
- **Checked before tagging.** All 233 signed files in the tree verified with `sigstore` 4.5.0 against
  `…/sign.yml@refs/heads/main`, and every file in `data/` has a bundle. The git identity scan was clean on 70 commits.
- **The tag.** `v0.1.0` is annotated and unsigned, as the author chose. It is on `d37d0a2`, not on the merge commit, by
  the author's ruling, so that the release and its archive carry bundles that verify. On the merge commit, the two
  files' bundles were still the stale ones.
- **The release.** It was published at <https://github.com/dogma-guru/manacitra/releases/tag/v0.1.0>, with the 0.1.0
  section of `CHANGELOG.md` as its notes.
- **The release's signing run, 37726252431.** `gate`, `build-release` and `sign-release` passed. The release carries
  the sdist, the wheel and `SHA256SUMS`, each with its `.sigstore.json` bundle.
  - **Not in the plan.** The action also signed and attached GitHub's two source archives (`v0.1.0.tar.gz`, `v0.1.0.zip`).
- **The asset, verified from a fresh download:**

  ```
  $ sigstore verify identity manacitra-0.1.0-py3-none-any.whl --cert-identity https://github.com/dogma-guru/manacitra/.github/workflows/sign.yml@refs/tags/v0.1.0 --cert-oidc-issuer https://token.actions.githubusercontent.com
  OK: manacitra-0.1.0-py3-none-any.whl
  ```

  - The sdist and `SHA256SUMS` verify too, and `shasum -a 256 -c SHA256SUMS` passes on both packages.
  - **The negative control.** Against `…@refs/heads/main`, the wheel fails (exit status 1).
- **The DOI.** Zenodo archived the release as "Manacitra: a map of your qubits", v0.1.0. The version DOI is
  `10.5281/zenodo.23228519`, and the concept DOI, for every version, is `10.5281/zenodo.23228518`. The author confirmed
  both from Zenodo's GitHub page. The follow-up branch `chore/v0.1.0-doi` makes these changes:
  - the version DOI goes into `CITATION.cff` and the README's citation;
  - the badge, linking to the concept DOI, goes at the top of the README;
  - the fixed-commit sentence is removed;
  - `CITATION.cff`'s `date-released` (2026-10-05 before) and the CHANGELOG heading ("unreleased" before) are set to
    the release date, 8 October 2026.

  `test_the_release_doi_is_cited_everywhere` checks all of this.

## 22. The README restructured (8 October 2026)

**Why.** The author asked for a README that is easy to follow, with links within it and with sections broken out
where that is the standard way. A survey of thirteen research projects and guides found them all under about 1,150 words:
- quantum and physics research software: Mitiq, qiskit-experiments, qiskit-device-benchmarking, Cirq, ReCirq,
  PennyLane and QuTiP;
- reproducible-research guidance: Papers with Code's research-code guide, rOpenSci, the Turing Way, the AEA
  replication template, Standard Readme and Make a README;
- two scientific Python libraries: scikit-learn and astropy.

Manacitra's README had 6,100 words. The common order is what it is, install, a minimal example, links to the
documentation, citation, and the licence last. Papers with Code's guide keeps a table of results in the README, each tied
to a command. A subagent made the survey, from the projects' own pages; its counts are approximate, and the author did
not take it as a ruling.

**What moved, unchanged.** The text was cut from the README at exact line ranges, into four pages in `docs/`:
- `docs/findings.md`: the reproduction note, the ten findings (each with an anchor, `#finding-1` to `#finding-10`), the
  whole-chip picture, the flagged-pairs note, and what has not been shown;
- `docs/method.md`: the six pictures and the sealing example;
- `docs/kickoffs.md`: how the results were made, with the kickoffs table;
- `docs/install.md`: the plain-package install, the extras and the provider backends, and the checks made before
  anything is sent.

Every line of the old README is on one of the five pages word for word, except six lines, all deliberate: "in the
README" became "in the README and on this page"; two bold labels became headings; "Every result above" became a link to
the findings; the "long version" pointer moved into the documentation list; and the plain-package paragraph was split
under a heading. Image and file paths were rewritten for the `docs/` folder.

**The README now** has 125 lines and about 1,900 words. It carries:
- the name, the DOI badge and a one-line contents list;
- "What it does", with the chip map (picture 2, with its explanation) under it, and `pick --by level` named beside
  the kept share (both from the author's review of the first draft: the chip map is what explains the project at a
  glance, and the table's rows 8 and 9 rely on the plain level);
- a table of the ten findings: the number links to the full finding, then the finding's own bold headline word for
  word, the processor, the kickoff and date, and the verdict as the kickoffs table gives it;
- what would discredit the map, and the Limits, unchanged;
- one picture, the pipeline, with a link to the method;
- install and a quickstart;
- three commands to reproduce the numbers;
- a documentation index;
- citation, support and licence, the licence last.

**One correction while building the table.** Finding 10's verdict cell first showed only "the per-program pattern HOLDS
a day later", which left out the kickoff's other verdicts. It now reads as the kickoffs table does: "SPREAD, MIXED, DOES
NOT; the per-program pattern HOLDS a day later".

**The tests.**
- `tests/test_readme_numbers.py` reads the README and its four pages together as one text, so every number it checked
  is still checked wherever it now sits, and a retired phrase cannot come back on any of them. Three checks of image
  paths now read the page and path each image moved to.
- New: `test_the_findings_table_matches_the_findings` checks that each row's headline is the finding's own sentence,
  that its kickoffs are the ones the finding names, and that every capitalised verdict word is in that kickoff's row of
  the kickoffs table. Changing one headline word makes it fail.
- New: `test_every_link_resolves` checks every relative link and in-page anchor on all five pages. A broken anchor
  makes it fail.
- `docs/index.md` points to the new pages, and says the README's checks cover them.

**After the change:** 578 tests pass (571 before; 7 new: the table check, a link check per page, and the front page's
pictures and `--by level` sentence); Ruff is clean;
both scans are clean. Nothing in `data/` or `src/` changed, and no number changed.

## 23. Release v0.1.1 (8 October 2026)

**What it carries.** The README restructured (section 22). No behaviour, data or published number changed since
`v0.1.0`. The version is 0.1.1 in `pyproject.toml`, the package, `CITATION.cff` and the README's citation, and
`test_the_version_is_the_same_everywhere` keeps them together, with a dated changelog entry.

**The citation's DOI, by the author's ruling of 8 October.** Zenodo mints a version's DOI only after the release, but
it archives the repository as tagged. So from this version on, the citation uses the concept DOI,
`10.5281/zenodo.23228518`, which always resolves to the latest version. The archived snapshot is then correct as
tagged, and a release needs no DOI follow-up. The README names v0.1.0's own DOI, `10.5281/zenodo.23228519`, for an
exact citation. `test_the_citation_uses_the_concept_doi` checks both.

**The release path is unchanged:** the merge, then signing on `main` (a bundle commit only if a signed file changed),
the annotated tag, the release with the changelog's 0.1.1 entry as its notes, and `gate`, `build-release` and
`sign-release`.

**The release (8 October 2026).**
- **The merge.** Pull request 8 was merged as `0b2ba5a`, with a merge commit, on the author's go-ahead, after its
  checks passed: `ci` 37779998272, `dco` 37779998282 and `sign` 37779992593.
- **After the merge.** Signing (37781657492) and CI (37781657441) on `main` passed. No signed file changed, so there
  was no bundle commit, and the tag is on the merge commit itself.
- **Checked before tagging.** All 233 signed files in the tree verified against `…/sign.yml@refs/heads/main`. Every
  file in `data/` has a bundle, and the git identity scan was clean on 78 commits.
- **The tag and the release.** `v0.1.1` is annotated and unsigned, on `0b2ba5a`. The release is at
  <https://github.com/dogma-guru/manacitra/releases/tag/v0.1.1>, with the changelog's 0.1.1 entry as its notes.
- **The release's signing run, 37784027125.** `gate`, `build-release` and `sign-release` passed. The release carries
  the sdist, the wheel and `SHA256SUMS`, and GitHub's two source archives, each with its `.sigstore.json` bundle.
- **Verified from a fresh download, with `sigstore` 4.5.0:**

  ```
  $ sigstore verify identity manacitra-0.1.1-py3-none-any.whl manacitra-0.1.1.tar.gz SHA256SUMS --cert-identity https://github.com/dogma-guru/manacitra/.github/workflows/sign.yml@refs/tags/v0.1.1 --cert-oidc-issuer https://token.actions.githubusercontent.com
  OK: manacitra-0.1.1-py3-none-any.whl
  OK: manacitra-0.1.1.tar.gz
  OK: SHA256SUMS
  ```

  `shasum -a 256 -c SHA256SUMS` passes on both packages. The negative control: against `…@refs/tags/v0.1.0`, the
  wheel fails (exit status 1).
- **Zenodo.** It archived the release as v0.1.1, with its own DOI, `10.5281/zenodo.23239929`, under the concept DOI
  `10.5281/zenodo.23228518`. The concept DOI now resolves to the v0.1.1 record, so the citation and the badge point to
  the latest version with no follow-up.

**The version DOI in the README, by the author's ruling of 8 October.** The citation paragraph's example of a version's
own DOI was still v0.1.0's beside "version 0.1.1" in the citation line. It now names v0.1.1's DOI. Each release updates
that one line once Zenodo has minted the DOI, and adds the version to `VERSION_DOIS` in
`tests/test_repository_home.py`. The test checks that the README names the latest published version's DOI. The author
preferred this to wording that names no version, which would hide a number a reader might want. The repository has no
release checklist file. This step is written down here and in the test.

## 24. Amendment A12: three sentences back on the README (8 October 2026)

**The second trial.** Codex, in run mode, worked from the public address alone, at `0b2ba5a` (v0.1.1). Its marks were
41 PASS, 7 FAIL and 4 CANNOT CHECK, with no Blocker. Everything that runs, reproduces or verifies passed again:
- both installs, the Python block and the three examples;
- `report`, now byte-identical to `verdict` before its table;
- the three independent recomputations, the manifest and the acceptance table;
- four signatures, three negative controls and the transparency log entry;
- the release assets, and the scan over the whole history (78 commits, 839 blobs, nothing unapproved).

**Where the seven FAILs went**, as A12 sorts them:

| group | count | disposition |
|---|---|---|
| the organisation's and Patreon's pages | 2 | the author's; A11's text stands |
| the repository's topics, empty in the About box | 1 | the author's |
| a rubric mismatch | 1 | corrected in the rubric (r3) |
| this amendment | 3 | C2, F and B2, below |

**1. Three sentences back on the README (C2, F, B2).** The restructure of 8 October left each of them only on a
linked page. Each is now on the README itself, and the full text stays on the docs pages:
- **Under "Install and try it", beside the plain-package paragraph**, how to point an install at a clone's data:
  "Point an install at a clone's data with `manacitra --data /path/to/manacitra/data verdict ibm_fez/k31-map.json` or
  `MANACITRA_DATA`; `--data` goes before the subcommand."
- **In the same section:** "A provider backend sends nothing unless `--submit` is given; the simulator runs at once,
  on your machine, and sends nothing."
- **Under "The idea", after the sentence naming `docs/method.md`:** "The published runs predate this release, so their
  sealed predictions rest on the author's dated records; from the first public release on, new commitments can be
  checked by anyone with `manacitra seal` and the signing log."

`test_the_readme_itself_says_how_to_point_at_the_data_and_what_is_sent` checks all three on the README alone, not on
the joined pages.

**2. The release steps carry the DOI line.**
- **Where the steps live now.** A12 says to add the line "to the release steps in `docs/index.md` section 9 (or
  wherever the release steps live)". No release steps were written down anywhere, so section 9 gains a short
  "Releasing" list: the four steps v0.1.0 and v0.1.1 took.
  1. a release pull request that sets the version everywhere, with `CITATION.cff` keeping the concept DOI;
  2. the merge and signing on `main`, then the annotated tag, on the bot's bundle commit if a signed file changed;
  3. the release and its verification against `@refs/tags/vX.Y.Z`;
  4. once Zenodo has minted it, the version's own DOI in the README's citation parenthetical and in `VERSION_DOIS`.
- **The test.** `test_the_release_steps_carry_the_doi_line` keeps step 4 there.

**After the amendment:**
- **Tests:** 581 pass (579 before; 2 new);
- **Ruff:** clean;
- **The identifier scan:** clean on the full tree;
- **The git identity scan:** clean on every reachable commit;
- **Data:** nothing in `data/` changed.

**The merge method.** A12 says "squash on merge". The author's ruling of 8 October is a normal merge commit, as for
every pull request since pull request 3, so that every commit keeps its `Signed-off-by` line on `main`.

**One test assertion removed.** `test_the_citation_uses_the_concept_doi` also required that the changelog's top entry
not be "Unreleased", which held for the v0.1.1 release pull request. This amendment rightly adds an "Unreleased" entry,
so the assertion goes. What it protected, a dated entry for the current version, is still checked by
`test_the_version_is_the_same_everywhere`.
