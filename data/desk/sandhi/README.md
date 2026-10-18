# Sandhi: the gated states

The desk model of finding 29 ([`../../../docs/findings.md`](../../../docs/findings.md#finding-29)): a kinetic description of the records of tests 7 to 11 on ibm_fez and ibm_kingston, with five fitted rates: a frequency change between adjacent repeats of an execution span, a frequency change at a span boundary, a weight change at a span boundary, a change across a calibration stamp, and a weight change between adjacent repeats of a span. It was fitted on the desk, from a bundle of those tests' records and nothing else, with no hardware. It is not a run record and not counts of any device.

**Set down at version 3.** By ruling R2 of Amendment A27 (18 October 2026), after tests 13 and 15 read the per-shot record, the model is set down at version 3, its files kept here as published. Where tests 13 and 15 read SHARED, the means at equal returned shot index across a span's circuits varied far beyond independent shots; read as a state the circuits share, adjacent repeats of a span average the same stretch of time, so there its two channels within a span count what the design cannot make nonzero; and its channel for the weight at a span boundary was fitted to level differences read at the shots' binomial error, where the error of a span's weight is that of a time average (finding 29, part (d)). No later version is published here.

Its report carries three sentences:

> "The model is a kinetic description; it names no cause." "A record below its own floor is censored, not absent." "The predictions are the model's, written before the run they predict, and they are what can prove it wrong."

**The name.** The author named the model Sandhi on 17 October 2026 (`kickoffs/ruling-sandhi-the-model-name-2026-10-17.md`); its files keep the lineage "Model 01" in their names. The run published here is version 3, run 3.1. Three runs preceded it, runs 1 to 3; their outputs are not published, and the kickoffs of versions 2 and 3, with version 3's errata, are the record of what changed between them.

**Its bets for the next run** were written last, from the fitted rates alone, before that run:

| file | SHA-256 |
|---|---|
| `v3.1/predictions-model-01-v3.md` | `745059e38db0e54f4bcef2bc8cad17a2fde40223f0a1dde75982a621817a38a3` |
| `v3.1/predictions-model-01-v3.json` | `02b8003461f948991217be683bc0706f611da57ac4e03d53ca8745274fc019b4` |

The author posted these two digests with test 12's rule in [issue 59](https://github.com/dogma-guru/manacitra/issues/59), before test 12's run on 143 on 18 October 2026.

## The kickoffs

The kickoffs are not hashed records. Each is as written but for one change: the desk runner's service, where a kickoff names it, is written "the desk runner". The SHA-256 of each as read and as published:

| file | as read | as published |
|---|---|---|
| `kickoffs/kickoff-model-01-v2-gated-states-2026-10-17.md` | `624cde22e5fdf3a599b8b19823a49c7fe0c3e1b5f27571f51b755b2b354108a6` | `bcf20d5403c1655c10498145cfa5606c6a362c782da1d0c022dd704e4521f5e0` |
| `kickoffs/kickoff-model-01-v3-gated-states-2026-10-17.md` | `7876c649abf2f75f7dc75aff749411b2a545c37f2d3861eea85e95138b2fb947` | `89e760a1b66a88e5a39907c0197487ff93961ca1c4e1718bbf9775f183aafbc1` |
| `kickoffs/kickoff-model-01-v3-errata-2026-10-17.md` | `881ec9b4c124f8bf8974a3898b4e4bc568d3de8b2be28824a23bf3f6c105a4a3` | `881ec9b4c124f8bf8974a3898b4e4bc568d3de8b2be28824a23bf3f6c105a4a3` |
| `kickoffs/ruling-sandhi-the-model-name-2026-10-17.md` | `4acf1ec9dc3e06dd60faf5fd1a52960f14ec5950e8ce1e55461a004c852ab8cb` | `4acf1ec9dc3e06dd60faf5fd1a52960f14ec5950e8ce1e55461a004c852ab8cb` |

The replacements:

- `kickoff-model-01-v2-gated-states-2026-10-17.md`, line 3 (1 time).
- `kickoff-model-01-v2-gated-states-2026-10-17.md`, line 5 (1 time).
- `kickoff-model-01-v2-gated-states-2026-10-17.md`, line 103 (2 times).
- `kickoff-model-01-v3-gated-states-2026-10-17.md`, line 3 (1 time).
- `kickoff-model-01-v3-gated-states-2026-10-17.md`, line 85 (1 time).

## The run, version 3.1

`v3.1/` holds the run's files as delivered, each checked against the run's `SHA256SUMS` before it was copied, and that `SHA256SUMS`, which lists every file of the delivery. Start with `v3.1/report-model-01-v3.md`, then `v3.1/predictions-model-01-v3.md`.

| file | SHA-256 |
|---|---|
| `v3.1/report-model-01-v3.md` | `03607747e5396660d1cefa57c8f722aa8fe224e75e4251bde2f7b2a3b5e3509d` |
| `v3.1/dependence-model-01-v3.json` | `869540b208d010870984a6ad333c1960f92261be8b98e88ea265d650338676f9` |
| `v3.1/model-check-model-01-v3.json` | `336d92fe528b8a18e7dffc67ac1ee679d72ec3a156a12a71dfc9b31570abfb60` |
| `v3.1/estimators-model-01-v3.json` | `b9761b7547eda81db969630587a15011a8fe90b11c594e8970f3fdac1185502a` |
| `v3.1/historical-scorecard.json` | `99793bdf9cb09ebf837f998d3fd2a6a3d1a2762e240b374d979140facb716567` |
| `v3.1/predictions-model-01-v3.md` | `745059e38db0e54f4bcef2bc8cad17a2fde40223f0a1dde75982a621817a38a3` |
| `v3.1/predictions-model-01-v3.json` | `02b8003461f948991217be683bc0706f611da57ac4e03d53ca8745274fc019b4` |
| `v3.1/validation.json` | `bbab366791dbd20e9f5b98cf531a1450832abd7f8a8a89821971352680491c37` |
| `v3.1/runtime.json` | `cb4971bfb31c8043c6faaa1643237761abea89d4da78f026d3a6db094841b251` |
| `v3.1/README.md` | `4d0be6072eeabe4676b8c16395063c62c5610766e0ff152d8d1329e02f8110e7` |
| `v3.1/scripts/check_input.py` | `d4d11135db6bcae2a65e9be5593dfc29b3ba85d94ffc5abf7feb8921eb10143f` |
| `v3.1/scripts/export_run_log.py` | `1c74aa51eae2ec281de0f7787a4c5c36a3d27153dc28ee1da81ff15937ff5c75` |
| `v3.1/scripts/fit_model.py` | `bae01a2f2b2ff9fcedbcc1be89d4272c6b9485d91331453d498705e41a027648` |
| `v3.1/scripts/frequency.py` | `1194544856deecdacf3a25b1fa9da227bb3a7e7c5187fdc9386a8204bf9e1029` |
| `v3.1/scripts/frequency_stat_audit.py` | `7b2d59fdfbd78100a2f59287b815a02d2ac67716a552dea460a059ddbefff5a7` |
| `v3.1/scripts/monitor11.py` | `1b05bf21192592710e03742ac6bf456de8ace573191a1c5b0160905408cafc45` |
| `v3.1/scripts/normalize.py` | `8b89f0c90f290670ff8933484fb3d3388cce640e3f703e5777bc1b14dd9b971c` |
| `v3.1/scripts/package_output.py` | `959976f072860c951c46e8fd87ad2197330ea8582354c0e2bda216c0d070bb51` |
| `v3.1/scripts/prediction_audit.py` | `143d1bf1a3b9db9fdd4c15f257c02cf24cbca9f0e84c14323e70396065700a85` |
| `v3.1/scripts/scorecard.py` | `bd01c00249c433bf4cf6ce3235e69e25da7202257b54deb185153936d21f443e` |
| `v3.1/scripts/shuffled_stamp.py` | `c2f08e7605b9e06f4827419936f6ea6a56a884bbd402d0ef2e5b65958a9eac61` |
| `v3.1/scripts/statistics_core.py` | `2a99447dfe5f7b0fe972ad9382d8f7c831b05dc24f5e3f61b583c486f1aaae07` |
| `v3.1/scripts/validate_output.py` | `ad31736f9c7bb3166cd554914c451b6368a295dfa5dd4c16f914b6d9799ea789` |
| `v3.1/scripts/write_predictions.py` | `37c1e1c7e23340317d35764825b403952b4be810d3a99b49360c5131d9eff8af` |
| `v3.1/scripts/write_report.py` | `ffc9e1e3bf6329ea3fd651f944d63b112e3bad2b2f8f10564cb3f2255d2ba6dc` |
| `v3.1/SHA256SUMS` | `6d052a5f19236a5b3d24f381b1fa69d3524e3c065a1e0e55762478da45b2d325` |

**Attached to the 0.9.0 release as assets**, not kept here, for size; each SHA-256 is also in `v3.1/SHA256SUMS`:

| file | bytes | SHA-256 |
|---|---|---|
| `rates-model-01-v3.json` | 10,584,236 | `90fd456ed792ebcb1feaf784eb205e93b0c7da924f772a2287711c56f8101302` |
| `shuffled-stamp-ledger.json` | 16,905,551 | `0190303cea8602b3b665b11da00b6224523c5c46a4bbc5b70c453e2a6c00907d` |
| `normalized-trials.json` | 25,072,515 | `184303bb1067942d39a6ab4652da31fd489f48d1dc5e94cc164bf5cce3c6fab1` |

Two ledgers are attached as copies, each with one change (Amendment A27, ruling R1): its one `command` field, which recorded the command as run with the path of the runner's environment, is written "[the desk runner's environment]". Every other byte is as delivered. The SHA-256 of each as the run hashed it, in `v3.1/SHA256SUMS`, and as published:

| file | bytes as published | SHA-256 as hashed in the run | SHA-256 as published |
|---|---|---|---|
| `events-model-01-v3.json` | 56,420,073 | `1f7e1557fd5c2200d5bf7ce510eedd763e57e662ead175cffc2d3b014f066afa` | `000a75d40761f6f28ce9221134fe700d3a883538ffbb89dbd1346259e8350618` |
| `frequency-ledger.json` | 67,327,928 | `d426efb2afc0fb1cd06c73b7e4601c76fae73d9e651132fe1929569e5888fde0` | `14ceaf554d9a843d35c72b406fd6d9b6814eb7f8f48a559f56fe2d574043b73f` |

**Not published:** `run.log`, the run's command record (SHA-256 `539f846fa08b20dfc615e3cab3331a57b3f49ffa3adb91c4b5b4960d0aaec662`, in `v3.1/SHA256SUMS`); it names the desk runner's service and the paths of the runner's own folders throughout, and it is not a record anything is recomputed from. Also not here: the run's copy of its input (`input/`, the records of tests 7 to 11 as the bundle held them; the published records are in `../../ibm_fez/` and `../../ibm_kingston/`), its command logs, its notes and its audits.

**Rerunning it.** The run's own `README.md` gives the commands, in order, from the run's folder with its input copy beside it, under Python 3.14.8, NumPy 2.5.4 and SciPy 1.18.1. The scripts read only that folder.

