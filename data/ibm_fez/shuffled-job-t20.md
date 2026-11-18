# Test 20: the shuffled job, recorded before the scorer runs

Recorded at 2026-11-17T00:38:21Z (UTC), after the per-shot read and before the scorer was started.

- **Decision: job 1 is supplied as D1's shuffled job** (rulings-t20.md, ruling 1). Its conditions hold: job 1 ran (dbtq0p1jbrss73a6s8l0, DONE), and its fits carry usable per span weights.
- **C3, job 1's A26 weights per span**, from `fits-t20-job1.json` (SHA-256 39bedba78d8beb6e5ae73c044ac781847702ad816672788c683c60377bc066d4), which carries `span_readings_A26` exactly 1 time: span 0: 0.4653 from 40 positions; span 1: 0.5326 from 37 positions; span 2: 0.4382 from 27 positions.
- **The README lines relied on** (as quoted in ruling 1): `README.md` line 40, lines 46 and 47, and line 52; `score_model_01_v4_1.py` line 7; `calibration_v4_1.py` lines 149 to 166 (`read_a26`).
- **The bets:** `shuffled_weight_A26` is scored. `shuffled_sd` is reported as not scored, naming the scorer's line 217 (ruling 2). The scorer is not edited.
