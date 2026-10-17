# The desk power check before test 7

The record of how test 7's rule (finding 28, [`../../ibm_fez/t7-rule.md`](../../ibm_fez/t7-rule.md)) was reached: a power check of the design and its rule, run on the desk on 16 October 2026 before the rule was fixed and hashed. It simulates the two models of the rule with binomial shot noise; it is not a measurement of any device. Its verdict: KEPT. On a grid of 135 simulated qubits, with 200 draws at each, the rule returned the generating verdict in at least 80% of draws at 106 of the 117 counted points, where 88 were needed. The keep criterion is fixed in the version 5.1 kickoff below, and `report-t7v51.md` names the eleven points that failed, by kind. Five earlier versions of the design preceded version 5.1 and are recorded elsewhere, not here.

The files are as they were handed back, each checked against the hand-back's `SHA256SUMS` before it was copied, except where the table says otherwise. The scripts and reports name paths in the author's working folders, which begin `tests/` and are not this repository's `tests/` folder or any part of this repository.

| file | what | SHA-256 |
|---|---|---|
| `kickoff-t7-steady-or-switching-v5.1-DRAFT-2026-10-16.md` | the version 5.1 kickoff: the models, the grid, the keep criterion and the order of the run, with what changed from versions 4 and 5 | `ccbef15f1e6602fa1a5491eef3772007611317803cebd10541c855883a8dd9f0` |
| `report-t7v51.md` | the runner's report: the fit check, the timing, the grid, the keep and its tables | `ab65d1524618c11e43f28072ff431439516798c799de4974f53f541b95ce3111` |
| `power_t7v51.py` | the script as run (stages `fitcheck`, `time`, `grid`, `beside`) | `a1c178a8b6054ddb5492405f30dbc05fd2502438dbb6699a9bd337533c01ee3c` |
| `tables_t7v51.py` | the keep computation and the tables, from the grid's results | `5c6e75d9cd3157598d450f2f480bc9947fa0040f4ef7698901f5e6cd77cd362a` |
| `keep-t7v51.json` | the keep and every point's verdict fractions | `06cacb4fb58d293f685f822f43fb7bcfe35a6f335a19b0649e56251982f66531` |
| `fitcheck-t7v51.json` | step 1, the fit check | `abc40212769f686d93d032c143df7807a64dfff3acdec22c7cf2d6ea59205eaa` |
| `timing-t7v51.json` | step 2, the timing, with every draw of its six points | `05d34be47a08f0098e5158b0018fdc728df4dad64569ef4b7863bf7386bbee9e` |
| `grid-run-t7v51.json` | step 3's run record: its start and end, the script's SHA-256 as run, the order of the points and the points written, 135 in one run with no restart | `53f19059c8fe9ec9b355d9869d3237bbdac9273e1c08bf4842f33d64c9cca960` |
| `beside-t7v51.json` | beside the check: the two models fitted to each archived run on 143 alone, one quadrature | `2e299cab16bdd273551b5c2ec92aee54faa0acb3b931be46b7f41a32f7e0de1d` |
| `../t7/pretest_t7.py` | the pre-test's script, which `power_t7v51.py` imports for the one-line model and its fit | `7cb62fecbd50184cc75d31960d2504129b4d21653d5b7003cae9c2f831f72cdc` |

**Two files differ from the copies handed back,** each in the first line of its docstring, which named the author's working folder; nothing else in either file changed:

- `power_t7v51.py`: handed back and run as `663280741fe5dcb6728e4bca5ef55afc759dac5823225b02981bd88929e4b41a`;
- `../t7/pretest_t7.py`: handed back and run as `a701a0711c5f832feb041cc32fbafc21fb97b0fe6e967a9b1748a03c721ea6c9`.

`power_t7v51.py` checks `pretest_t7.py` against `../t7/SHA256SUMS`, which holds the published copy's SHA-256. The JSON records name each script by its SHA-256 as run.

"DRAFT" in the version 5.1 kickoff's name is the author's working label; the design was fixed by the rule, not by the kickoff.

**The grid's results** (`results-t7v51.jsonl`, one line per grid point with all 200 draws; 21,973,170 bytes) are not in this repository. They are attached to the 0.8.0 release as an asset, with this SHA-256:

`27c29bc2c242312ff9b2ab3b22c987263aa2900ebdcf966c24e0fcc1369b1a48`

**Rerunning it.** The scripts need a clone of this repository checked out at `9b260fb` with its package imported from that checkout (`pretest_t7.py` checks both), and they write their outputs beside themselves, so run them in a copy of `data/desk/`:

```bash
MANACITRA_REPO=/path/to/clone-at-9b260fb python power_t7v51.py fitcheck
```

then `time` and `grid`, in that order (the grid ran 3.8 hours on ten cores). Take `grid-run-t7v51.json` out of the copy before the grid stage: the stage reads it as its own run record and stops once twelve hours have passed since the first start it records. The `beside` stage and `tables_t7v51.py` also read records of versions 2 to 5 of the design, which are not published here; `tables_t7v51.py` reads round 5's timing record for one bracketed column of its tables, and so does not run from this repository alone. `keep-t7v51.json` holds every point's verdict fractions, from which the keep is counted again by `tests/test_readme_numbers.py`.
