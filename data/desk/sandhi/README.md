# Sandhi, the desk model

The desk model of findings 29 and 30 ([`../../../docs/findings.md`](../../../docs/findings.md#finding-30)): a kinetic description of the records, fitted on the desk from bundles of those records and nothing else, with no hardware. It is not a run record and not counts of any device. Version 3, named "the gated states" (a dated name, retired with it), described the records of tests 7 to 11 on ibm_fez and ibm_kingston with five fitted rates: a frequency change between adjacent repeats of an execution span, a frequency change at a span boundary, a weight change at a span boundary, a change across a calibration stamp, and a weight change between adjacent repeats of a span. Versions 4 and 4.1 describe the per-shot records of tests 10 to 15 and of test 11's third day as a two-state chain on the sweep clock.

| version | date | what it describes | its bets | posted | scored |
|---|---|---|---|---|---|
| 3, run 3.1 (`v3.1/`) | 17 October 2026 | tests 7 to 11, five rates | the next run | [issue 59](https://github.com/dogma-guru/manacitra/issues/59), with test 12's rule | set down at version 3 (below) |
| 4 (`v4/`) | 18 October 2026 | tests 10 to 15, per shot: per span a two-state chain on the sweep clock, the levels shared by a job's spans, 143's spans drawn from a population | test 11 on a third day | [issue 66](https://github.com/dogma-guru/manacitra/issues/66), before day 3 | on day 3, by test 16: every structural criterion held; no calibrated bet was scored, each outside the modelled support (`v4/scorecard-t16.json`) |
| 4.1 (`v4.1/`) | 19 October 2026 | version 4, its fits extended with day 3; the prediction setup corrected (C1 to C3) | D1, the next two-job monitor run; D2, one 600-position monitor job | [issue 68](https://github.com/dogma-guru/manacitra/issues/68), before test 17 | D2, on test 17's long job: no family counted against it (`v4.1/scorecard-t17.json`); D1 not yet scored |

**Set down at version 3.** By ruling R2 of Amendment A27 (18 October 2026), after tests 13 and 15 read the per-shot record, the model is set down at version 3, its files kept here as published. Where tests 13 and 15 read SHARED, the means at equal returned shot index across a span's circuits varied far beyond independent shots; read as a state the circuits share, adjacent repeats of a span average the same stretch of time, so there its two channels within a span count what the design cannot make nonzero; and its channel for the weight at a span boundary was fitted to level differences read at the shots' binomial error, where the error of a span's weight is that of a time average (finding 29, part (d)). Versions 4 and 4.1, below, model the per-shot record in another form; version 3's files are not changed.

Version 3's report carries three sentences:

> "The model is a kinetic description; it names no cause." "A record below its own floor is censored, not absent." "The predictions are the model's, written before the run they predict, and they are what can prove it wrong."

In plain words: the model describes how the records change and does not say why; a change too small for a record to see is counted as unseen, not as one that did not happen; and its forecasts, written before the run, are the test it can fail.

Versions 4 and 4.1 carry three sentences:

> "The model is a kinetic description; it names no cause." "The sweep clock is the returned order; seconds are conditional on that order being chronological." "The predictions are the model's, written before the run they predict, and they are what can count against it."

In plain words: the model describes how each span switches between two states and does not say why; its clock is the order in which the provider returns the shots, and its times are in seconds only if that is the order in which they ran; and its forecasts, written before the run, are what can count against it.

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
| `kickoffs/kickoff-model-01-v4-2026-10-18.md` | `c032dcc4e0ea0729b88a3778b45db455137e1b87bc7b69286fd35ebb56258221` | `db18b223c371d118cdb9b4d91d2def017bc36be46fb968220bfad6ca67f76586` |
| `kickoffs/kickoff-model-01-v4.1-errata-2026-10-19.md` | `dd5d148f1f84b766202c8a38d3bd7dbc96ec749a92ec9c445d53bd54c2b3ce35` | `cb30269dbe80f55c038d0bfd4ac685c75a50086f9a56d3af26ad2f5efa34b7e0` |

The replacements:

- `kickoff-model-01-v2-gated-states-2026-10-17.md`, line 3 (1 time).
- `kickoff-model-01-v2-gated-states-2026-10-17.md`, line 5 (1 time).
- `kickoff-model-01-v2-gated-states-2026-10-17.md`, line 103 (2 times).
- `kickoff-model-01-v3-gated-states-2026-10-17.md`, line 3 (1 time).
- `kickoff-model-01-v3-gated-states-2026-10-17.md`, line 85 (1 time).
- `kickoff-model-01-v4-2026-10-18.md`, line 3 (1 time).
- `kickoff-model-01-v4.1-errata-2026-10-19.md`, line 3 (1 time).

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

## Versions 4 and 4.1

Version 4 was fitted on 18 October 2026 to the per-shot records of tests 10 to 15 (`kickoffs/kickoff-model-01-v4-2026-10-18.md`). Per span, a two-state chain on the sweep clock, the returned order: the switching fitted per span, the two levels of each circuit shared by a job's spans, and 143's spans drawn from a population, by test-day class. Its bets for test 11's third day were written last and its scorer hashed with them. On day 3 its scorer, run by test 16, found every structural criterion held, and scored no calibrated bet: each comparison lay outside its modelled support, for two gaps in its own forecast template that the scorer reported (the template's whole repeats per span, and its exact list of sweep times).

Version 4.1, on 19 October 2026 (`kickoffs/kickoff-model-01-v4.1-errata-2026-10-19.md`), kept the model and corrected the prediction setup only: C1, the calibration simulated through the scored run's own design; C2, the scored run's own sweep times, calibrated within the record's range widened by a tenth at each end; C3, the shuffled job's weight read from the run's own fits. Its fits add day 3's monitor spans. Version 4.1's review of day 3 was made after the arrays were opened and is not a score. Its bets are for two designs: D1, the next run of two monitor jobs; D2, one monitor job of 600 positions. On test 17's long job, D2, its scorer found no family of its bets counting against it; D1 is not yet scored.

**The prediction digests.** Each version's bets were written last, hashed with its scorer, and posted by the author before the run they predict:

| version | file | SHA-256 | posted |
|---|---|---|---|
| 4 | `v4/predictions-model-01-v4.md` | `718a0b86f3caeb832630a2431f6c14e137d9c0b90ffe10ac877cbc0ac5b7481b` | [issue 66](https://github.com/dogma-guru/manacitra/issues/66), 19 October 2026, 03:30 UTC, before day 3 |
| 4 | `v4/predictions-model-01-v4.json` | `cd8e4b87b64aa818a43b533ed0725cda47af79f1c1be25890743f1c1646f92af` | the same |
| 4 | `v4/FORECAST-SHA256SUMS` | `1115b9bdddb43c0e81a68905709a8025d58106799e69da40f89614e76bddfcc2` | the same |
| 4.1 | `v4.1/predictions-model-01-v4.1.md` | `5b2e45dea15f613d4314a959d5c06bebf0a663a5f1cb7e607f442ce45b98628f` | [issue 68](https://github.com/dogma-guru/manacitra/issues/68), 19 October 2026, 13:01 UTC, before test 17 |
| 4.1 | `v4.1/predictions-model-01-v4.1.json` | `a30488be57eade0df185c594cd83befa5817f8e54261a47423017d0d9814fc54` | the same |
| 4.1 | `v4.1/FORECAST-SHA256SUMS` | `7903a281ccc808ed8dd13c4b316919554879ec29a353f7093642c98b9081b083` | the same |

**The compiled library is not committed.** Each scorer calls a library compiled from the hashed C source, `hmm_core.c`, listed in its `FORECAST-SHA256SUMS`. `hmm_model.py` builds it, as `hmm_core.dylib` beside itself, when it is absent and a C compiler is present, with the line `cc -O3 -shared -fPIC hmm_core.c -o hmm_core.dylib`. The library each run used is named in its `SHA256SUMS`.

**The files.** Each was checked against its run's `SHA256SUMS` (and, for the scorer and its dependencies, `FORECAST-SHA256SUMS`) before it was copied, and the scorecards against their tests' hand-backs. Where the scorer or the runner wrote a local path, it is written "[local path]"; where a run log names the desk runner's service, it is written "the desk runner"; and version 4.1's run log writes its session identifier "[the desk runner's session]" and the name of the variable that holds it "[the desk runner's session variable]", and the handles of the command sessions its polling calls read, "[a command session]". Nothing else in any file changed. Each file's SHA-256 as delivered and as published:

| file | what | SHA-256 as delivered | as published |
|---|---|---|---|
| `v4/report-model-01-v4.md` | the run's report | `8a7a1e5320e5012704f33d9a92b8c1c734c4238b6d0309c929f0a3fb11e6b5c7` | the same |
| `v4/predictions-model-01-v4.md` | its bets for day 3, written last | `718a0b86f3caeb832630a2431f6c14e137d9c0b90ffe10ac877cbc0ac5b7481b` | the same |
| `v4/predictions-model-01-v4.json` | the same bets, as the scorer reads them | `cd8e4b87b64aa818a43b533ed0725cda47af79f1c1be25890743f1c1646f92af` | the same |
| `v4/hierarchy-model-01-v4.json` | the hierarchy across 143's spans | `a302bc25036371fd74d54bc4985a54bdb2e922d2413468e6bb383e062df76aca` | the same |
| `v4/score_model_01_v4.py` | the scorer | `42287f2e3f881b148bfa10f23cfbc190dff2959fc156e0bdb88b6e627601d7bf` | the same |
| `v4/record_io.py` | the scorer's reading of the arrays and records | `89c5b1807fd1deb5b403567eecabd651809a5017a42e2788475245c1db66ac5b` | the same |
| `v4/hmm_model.py` | the two-state chain: the likelihood, the fits and the decoded path | `24f49e97f6b226f6697843b65eeb23522d18816ce2989579f3c02e80856e164b` | the same |
| `v4/hmm_core.c` | the C source of the likelihood library | `b46709c740033e7f14a73174e93f7b706836f3348e1fec9c987ada0819e270a1` | the same |
| `v4/run_boundaries.py` | the likelihood ratio between spans | `2f1cf231a66b9105755f5d8d5ad5c489cdd1c0456cf066f4ad6a58bb02a67191` | the same |
| `v4/run_checks.py` | the model's own checks | `cf7bb72e09b44447d824009a642c76751175b16371084648915d1353d8d73dc5` | the same |
| `v4/scorer-test.json` | the scorer run on test 11's day 2 arrays: a computation check | `202ccf2da5a9722d811d379f5695df406ecd87ecf5144d86e791bae4a01fc3d8` | `9001620add7ef8c1085aa454569efba2dde61740f21c38f74eb3dc28479765c7` |
| `v4/test_hmm_numerics.py` | the library's test against exhaustive short paths | `1f074d4f78abd4fa4f95f6a6c65eac4c76b27141d676560a5642f1b3d9c5c1ab` | the same |
| `v4/hmm-numerics.json` | its output | `9cfc6b5d3741b1c2502bae1a786522d29b298735a1f8802534c84f4b2209faff` | the same |
| `v4/runtime-versions.json` | the numerical environment | `6e9e0b340701b101cab1f6748087482b6b04d7dbcf773b9f8fb9f91be5518fe0` | `dbd8e9e56f0ffed3cd715999950bf31f660b130783dc0fc6f1430cbedaf6efc3` |
| `v4/run.log` | the command record | `30842aa7c44d77daa40ba26fc913387c5fb3e6260b8fdb7f032fa63f73918e9d` | `3bed49ba39bf59a79d107dc95c6f5d4135fb9b80ba09039177f4d31ee352b23a` |
| `v4/README.md` | the run's own README | `b39f7b4581a95dba1de9cdda10f246cb1029369542c398b97ab055ec8b14c80e` | the same |
| `v4/SHA256SUMS` | the run's sums, over every file it delivered | `731dca00b761410d25d706d9777d444a5f0a6b29f42c6fb772510716c406b2a5` | the same |
| `v4/FORECAST-SHA256SUMS` | the sums of the scorer, its dependencies and the predictions, as posted | `1115b9bdddb43c0e81a68905709a8025d58106799e69da40f89614e76bddfcc2` | the same |
| `v4/scorecard-t16.json` | the scorecard on day 3, as test 16 ran the scorer | `9b6112c648c45734c52c6aedc37e58d6fe326bac2647d2708bacf101da2bf829` | `d99f828f31658210fe9a327b1cc4c2d623464c86f8c3dec77503d3ebb89c3be3` |

| file | what | SHA-256 as delivered | as published |
|---|---|---|---|
| `v4.1/report-model-01-v4.1.md` | the run's report | `87a17b647d62af74820dbdcb95b3d8a2832fe05ac4d7adc4b1f85e7a93e3ffc5` | the same |
| `v4.1/predictions-model-01-v4.1.md` | its bets for D1 and D2, written last | `5b2e45dea15f613d4314a959d5c06bebf0a663a5f1cb7e607f442ce45b98628f` | the same |
| `v4.1/predictions-model-01-v4.1.json` | the same bets, as the scorer reads them | `a30488be57eade0df185c594cd83befa5817f8e54261a47423017d0d9814fc54` | the same |
| `v4.1/hierarchy-model-01-v4.1.json` | the hierarchy across 143's spans, with day 3 | `0811a5d7d18c0fdcc2347e802ac4401034f6bd8eb8fb19f3ee51a8e6610ec4a6` | the same |
| `v4.1/score_model_01_v4_1.py` | the scorer, with C1 to C3 | `ae4aed5c957c5c5942629e82a5ccd291141a3038cb2a8aa490ff3f165493632c` | the same |
| `v4.1/calibration_v4_1.py` | the scorer's calibration through the scored run's design (C1, C2) | `0b1e674b4b2f74da4539625983407622dc656e5db53cc16ba38d7e6a15fed40c` | the same |
| `v4.1/calibration-state.json` | the frozen model state the calibration simulates | `10aa29fe32b3e030ff0b5eb7ff2e0d8d936df60322622522febca63c8be4b827` | the same |
| `v4.1/record_io.py` | the scorer's reading of the arrays and records | `89c5b1807fd1deb5b403567eecabd651809a5017a42e2788475245c1db66ac5b` | the same |
| `v4.1/hmm_model.py` | the two-state chain: the likelihood, the fits and the decoded path | `24f49e97f6b226f6697843b65eeb23522d18816ce2989579f3c02e80856e164b` | the same |
| `v4.1/hmm_core.c` | the C source of the likelihood library | `b46709c740033e7f14a73174e93f7b706836f3348e1fec9c987ada0819e270a1` | the same |
| `v4.1/run_boundaries.py` | the likelihood ratio between spans | `2f1cf231a66b9105755f5d8d5ad5c489cdd1c0456cf066f4ad6a58bb02a67191` | the same |
| `v4.1/run_checks.py` | the model's own checks | `cf7bb72e09b44447d824009a642c76751175b16371084648915d1353d8d73dc5` | the same |
| `v4.1/rehearsal-day2.json` | the corrected scorer rehearsed on day 2's arrays: a computation check | `857dca6bdad863fec221457520a5f3c0142665dd4e98bd782e01048aad06d8a3` | `d8f7dcbef0c6a78cf4c2f06c4ffbd6fe4b4c97c1b25b5206df87edc88b3329a4` |
| `v4.1/rehearsal-day3.json` | the same on day 3's arrays | `02029fbbcf9b6b37b524c11a6411e71528d4f9336f83b5fc3564fb9842ac54df` | `cb08a1e2e673dde055770942aff56ea965bdc758b503de4516377712b1f4fccc` |
| `v4.1/scorer-diff-v4.1.md` | every line of the scorer changed from version 4, with C1, C2 or C3 | `2e1bcb3d7f85a051e3dcb816805d341b778ae073715458a9d7a376e65ddff8e1` | the same |
| `v4.1/scorer-diff-audit.json` | the audit of that list | `92443d23de2b8a82647e65a1e205ef668ed68bdd669d74e3310e935b8a0dba11` | the same |
| `v4.1/internal-review-day3.md` | the internal review of day 3, labelled not a score | `2994d96ed48948305b4781217974c1e1688dd97322e58f79615ae3514f3804c8` | the same |
| `v4.1/internal-review-day3.json` | the same, every comparison | `53643b7e05801e83061e8956ea6fa9948a374296c1354d9914d5a28590c9bdc2` | `a0d6f7b79f27748d3f2b522f220c69fe2793a1dc368e77d73363ecf23b222663` |
| `v4.1/audit-part-a.json` | the review's audit against test 16 and version 4's scorecard | `a3fd355c1e38bac48c89d15777ff6aa88a88c8bdeed73d649361d5483b9c3267` | the same |
| `v4.1/audit-part-b.json` | the new fits' audit | `dd9ffe4746ad109c3d2355c2d061d2d2c2864b81c30ab31fdb3c21df1fd515e1` | the same |
| `v4.1/calibration-audit.json` | the recount of the calibration from its saved trials | `13613653501d7e9fc5174eb76cd83712a73b37e38113024287a6c1b16f437d86` | the same |
| `v4.1/seeds-and-versions.json` | the seeds and the numerical environment | `14c2ff984df951f1c3b34bd320d2a57fa59365bfe2c7441383771c2c484363bb` | the same |
| `v4.1/run.log` | the command record | `20430516f24179913a62dab395c1ded718d9d224b6363ae3cc77eb3c766a0811` | `d0f1f54c22f503640f395d4bf4caec32e99cbd4a3380123ba55fb726576aeee7` |
| `v4.1/README.md` | the run's own README | `dcc45eba2d59f0f0d634c147b8812fbdf4a9013221f9481e27588c39c197de28` | the same |
| `v4.1/SHA256SUMS` | the run's sums, over every file it delivered | `f8436f9555f484528bb42c56dfe1e92cf80fef155c91509b097d00f5daa17c11` | the same |
| `v4.1/FORECAST-SHA256SUMS` | the sums of the scorer, its dependencies and the predictions, as posted | `7903a281ccc808ed8dd13c4b316919554879ec29a353f7093642c98b9081b083` | the same |
| `v4.1/scorecard-t17.json` | the scorecard on test 17's long job (D2) | `79f3141ab7649cc6ecb21aceb8ce5b6f1d692901baf4dd35c1e3cfeceae64c0e` | `49998cdfb40b68a82b9cd9d2e0a6245794861ee2046dcefe1417a687ab050fde` |
| `v4.1/scorecard-t17.calibration.json` | that run's calibration through the job's design | `8231d551666bc7e846a96e576eec2960a777a10312c163f6b689d1c4955ae754` | the same |

The replacements, by file:

- `v4/checks-model-01-v4.json`: local paths, 1 time.
- `v4/scorer-test.json`: local paths, 10 times.
- `v4/runtime-versions.json`: local paths, 1 time.
- `v4/run.log`: local paths, 25 times; the service, 1 time.
- `v4/scorecard-t16.json`: local paths, 10 times.
- `v4.1/rehearsal-day2.json`: local paths, 20 times.
- `v4.1/rehearsal-day3.json`: local paths, 20 times.
- `v4.1/internal-review-day3.json`: local paths, 20 times.
- `v4.1/run.log`: local paths, 87 times; the service, 2 times; the session, 1 time; the session variable's name, 3 times; the command sessions' handles, 30 times (six values, on 14 lines).
- `v4.1/scorecard-t17.json`: local paths, 5 times.

**Attached to the 0.10.0 release as assets**, not kept here, for size; each SHA-256 as delivered is in its version's `SHA256SUMS`:

| file | bytes as published | SHA-256 as delivered | as published |
|---|---|---|---|
| `v4/fits-model-01-v4.json` | 11,720,764 | `1ab26796c32ad4c11fafaf40d6ca83da8c63f026adbdc624b12f45f1acd16e93` | the same |
| `v4/checks-model-01-v4.json` | 70,593,293 | `2f3af3de395d1bc355c8c10eb2bbb788ef1b02bb1cf26e40b5ef7425ae65642f` | `bd1192c421174f223f0f3f918d9dff57dcfaae1ddb82df4a24e8a50bc45b378b` |
| `v4.1/fits-model-01-v4.1.json` | 10,312,728 | `3c6fbaa54f5a4af21d5b76ab0eea01f801ab84ca696818b472e13f8132935e65` | the same |

`v4/checks-model-01-v4.json` is attached as a copy whose one local path is written "[local path]".

**Not published:** the rest of each version's delivery (version 4's data series, bootstrap draws, pilot and retry records, predictive simulations and likelihood-ratio results, audits and scripts; version 4.1's input copies, frozen version 4 state, calibration trials, nominal examples, data series and scripts), each named with its SHA-256 in its version's `SHA256SUMS`; the bundles the model was given; and the compiled library.

**Rerunning a scorer.** From the version's folder with the arrays, their meta files and the counts files of the run it scores, by the command line its `README.md` gives; test 17's run of version 4.1's scorer is in [`../../../docs/reproduce.md`](../../../docs/reproduce.md). The arrays are not published. `tests/test_sandhi.py` checks each version's files against its sums and its scorecard's family counts.
