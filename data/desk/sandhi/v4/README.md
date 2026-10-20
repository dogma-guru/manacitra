# Model 01 version 4 handback

Start with `report-model-01-v4.md`. The complete series and model outputs are in `data-model-01-v4.json`, `fits-model-01-v4.json` and `checks-model-01-v4.json`.

The primary hierarchy cannot identify an unrestricted third date forecast. The prediction files distinguish that limitation from a separate conditional empirical day extension. Read its assumptions and applicability gates before using its numerical tables.

The archive contains the scripts as run, all production bootstrap vectors, the early pilot, numerical corrections, independent audit and component logs. `run.log` collects their command and seed records. `runtime-versions.json` identifies the numerical environment. No requested bootstrap count was reduced.

Check the package from this folder:

```sh
shasum -a 256 -c SHA256SUMS
shasum -a 256 -c FORECAST-SHA256SUMS
```

The scorer requires Python with NumPy and SciPy and the local files listed by the forecast digest. The supplied compiled library is for the recorded macOS environment. The C source is included; `hmm_model.py` compiles it when that library is absent and a C compiler is available.

Run it on the future files with the frozen dependencies:

```sh
python -I score_model_01_v4.py \
  --job day3-job2,shots2.npz,meta2.json,counts2.json \
  --job day3-job3,shots3.npz,meta3.json,counts3.json \
  --shuffled day3-job1,shots1.npz,meta1.json,counts1.json \
  --predictions predictions-model-01-v4.json \
  --bootstrap 400 --seed 104196401 --out day3-scorecard.json
```

The scorer calculates raw quantities even when an actual design falls outside a simulated template. It withholds calibrated decisions in that case. The complete A26 estimator is absent from the input bundle, so its future weight score is explicitly unavailable.

To reproduce the desk run, place the supplied input archive beside this output folder and extract it under `model-01-v4-input/`. The exact extraction, analysis, pilot, retry and official replay commands are recorded in `run.log` and the component logs. Prediction files were written after the report and completed checks. The forecast digest was made after the scoring contract review.
