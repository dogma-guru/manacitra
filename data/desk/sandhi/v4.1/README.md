# Model 01 version 4.1 handback

Start with `report-model-01-v4.1.md`. The internal review has its required label in both formats. The prospective files are `predictions-model-01-v4.1.md` and `.json`.

The package contains the supplied input archives and their extracted records, frozen v4 state, new fits, all bootstrap samples, all 2000 trials for each calibration, rehearsals, independent numerical recounts, a complete scorer diff, source scripts and the command log. These records are local artifacts, not a publication or adoption.

The numerical runtime used Python 3.14.8, NumPy 2.5.3 and SciPy 1.18.1, with float64 arithmetic. It used the unchanged bundled C likelihood library. The outer `SHA256SUMS` covers all returned files except itself. `FORECAST-SHA256SUMS` covers the prospective scorer, its dependencies, calibration state and predictions.

## Check the package

Run from this folder:

```bash
shasum -a 256 -c SHA256SUMS
shasum -a 256 -c FORECAST-SHA256SUMS
```

## Repeat the desk computation

Use a Python environment with the recorded libraries. The scripts locate this folder themselves. Run these in order:

```bash
python -I -B scripts/make_state.py v4
python -I -B scripts/run_part_a.py
python -I -B scripts/audit_part_a.py
python -I -B scripts/run_part_b.py
python -I -B scripts/audit_part_b.py
python -I -B scripts/run_forecasts_v4_1.py day2
python -I -B scripts/run_forecasts_v4_1.py day3
python -I -B scripts/run_forecasts_v4_1.py D2
python -I -B scripts/audit_calibration.py
python -I -B scripts/write_diff.py
python -I -B scripts/write_handback.py
```

Matching calibration caches are reused only when the model state, actual design, seed, draw counts and calibration source digest match. Move the corresponding cache JSON aside to regenerate its trials. Every seed and draw count is stored with the output. The exact source construction and shell commands from this chat are appended to `run.log`; the executed scripts are also included.

## Use the prospective scorer

For D1, supply two monitor jobs; for D2, supply one. Paths below are placeholders for the future run. Add a shuffled job and its fits only when available.

```bash
python -I -B score_model_01_v4_1.py \
  --job future-job2,shots-job2.npz,shots-job2-meta.json,counts-job2.json \
  --job future-job3,shots-job3.npz,shots-job3-meta.json,counts-job3.json \
  --shuffled future-job1,shots-job1.npz,shots-job1-meta.json,counts-job1.json \
  --shuffled-fits future-job1,fits-future.json \
  --predictions predictions-model-01-v4.1.json \
  --out future-comparison.json
```

The default calibration uses 2000 complete days, 1000 to set intervals and 1000 to calibrate family misses. Its first 100 days use 400 null draws at each likelihood comparison. Default calibration seed is 41119001. The actual design determines calibration; nominal examples do not gate it. Seconds outside the C2 range remain uncalibrated. A26 weights are read from the supplied fits, and the undefined observed population sd remains unavailable.

The record reproduction check has a precise limit: all 125 record comparisons agree within 10⁻¹², but five have rounding differences, so only 120 are bitwise equal. The unchanged v4 estimator is retained. All unaffected v4 numerical outputs match exactly.
