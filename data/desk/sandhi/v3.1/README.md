# Model 01, version 3, run 3.1

Start with `report-model-01-v3.md`, then `predictions-model-01-v3.md`.

The folder contains the complete supplied input, all event ledgers, posterior tables, dependence calculations, model checks, estimator comparison, future predictions, source hashes, independent audits and command record. The report records unavailable definitions and alternate readings explicitly.

The kickoff named version 3 files; those basenames remain inside this run 3.1 folder.

Reproduction uses Python 3.14.8, NumPy 2.5.4 and SciPy 1.18.1. Use a Python environment with those libraries. From this folder run the following commands in order:

```bash
python3 scripts/check_input.py
python3 scripts/frequency.py
python3 scripts/shuffled_stamp.py
python3 scripts/monitor11.py
python3 scripts/normalize.py
python3 scripts/fit_model.py
python3 scripts/scorecard.py
python3 scripts/write_report.py
python3 scripts/write_predictions.py
python3 scripts/frequency_stat_audit.py
python3 scripts/prediction_audit.py
python3 scripts/validate_output.py
```

The last scientific generation step is the future predictions. Audits, command export and archive creation follow. Prediction timestamps will change on a rerun; numerical results use recorded deterministic seeds. Do not silently replace a sealed prediction file after its future experiment.

`run.log` includes exact tool inputs for the current run, runtime versions, current simulation seeds and original fitting metadata from the supplied archive. The command export script is operational provenance and requires the current session trace path. It is not needed to reproduce any scientific result.

`SHA256SUMS` covers the delivered files except itself. The ZIP digest is in its adjacent sidecar. The hash manifest also includes the retained input manifest and independent audit reports.
