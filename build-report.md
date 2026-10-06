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
