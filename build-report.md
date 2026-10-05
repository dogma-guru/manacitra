# Build report: Kickoff 01, the initial implementation

Branch `feat/initial-implementation`, 5 October 2026. Built by Claude Code (Opus 5.5) in the confirmed clone of the
repository (`manacitra/` in the author's projects folder), default branch `main`. Nothing was submitted to any provider; every test runs on simulation
or on the archived results.

**Summary.**
- Every reproduction test passes. Every archived statistic recomputes from the archived counts. Across 2,992 numeric
  values, the largest difference is 1.1·10⁻¹⁶, against the 10⁻⁶ bar.
- 139 tests pass, Ruff is clean, and the identifier scan is clean on the whole tree.
- Two things need the author's ruling (section 6):
  - kingston's payoff figure: the data give 16%, not 18%;
  - the repository's own address carries the hosting organisation's name.

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
identifier scan: clean (76 files)
```

The tree has 80 tracked files; the 4 PNG diagrams are binary and skipped. The result is the same with `CI=1`, which
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

**Needs a ruling.**

1. **ibm_kingston's payoff: 16%, not 18%.** The kickoff says "On ibm_kingston, 18% less". The figure that gives
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
2. **The repository URL.** `github.com/dogmaguru/manacitra` carries W7 as one word. CITATION.cff must name the
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
- **Python 3.11 and 3.13.** Only Python 3.14 is on this machine. Every source file parses under the 3.11 grammar, and
  CI runs 3.11 and 3.13; see the pull request for the result.
- **GitHub's rendering** of the README and the SVGs. The PNG fallbacks were inspected locally.
- **`CITATION.cff` against its schema**: `cffconvert` is not installed.
- **Any live provider call** (section 5).
- **The 18% figure** (above).

## 7. Versions used

Python 3.14.7, qiskit 2.5.2, qiskit-aer 0.17.2, qiskit-ibm-runtime 0.50.0, numpy 2.5.3, scipy 1.18.1, rustworkx 0.18.1,
cirq-core and cirq-google 1.7.0, ply 3.11, matplotlib 3.11.2, ruff 0.16.10, pytest 9.1.1. qiskit, numpy and scipy are
the same versions the source runs recorded.
