# Kickoff Model 01, version 4.1 (Sandhi v4.1): the prediction setup corrected, the model unchanged

Date: 19 October 2026. Author: Anish Patel. Prepared with Mantri (main). For: a desk runner with no hardware access, on the desk runner in a fresh session, from the bundle `model-01-bundle-v4.1-2026-10-19.zip`. No job is submitted anywhere; nothing here touches the public repository, the website or the support ticket.

**The author's ruling, 19 October 2026:** version 4 is kept; version 4.1 corrects the prediction setup only. The model's form, its fits on the record of 18 October, its hierarchy, its empirical day extension and its count-against definitions are not changed by this errata.

**Why.** Version 4's scorer ran on test 11's third day under test 16's rule (issue 67). Every structural criterion held: every span SHARED, no span failing the dwell comparison, no CHANGE at a boundary, no likelihood rejection. But every calibrated bet was marked "outside the modeled support" and none was scored, for two reasons that belong to the setup and not to the run:

1. The three-span scenario fixed whole-repeat counts of 49, 50, 49 per span. Every 1,000-shot monitor job on the record leaves out the repeats that straddle a span boundary, so its spans hold 48 or 49 whole repeats. The template did not match the design it was fitted on.
2. The seconds support was a list of nine donor sweep times compared exactly, so any new sweep time fell outside it.

A third gap, recorded with them: the shuffled job's weight was bet on, but no copy of A26's method was in the bundle, so the scorer could not compute it (Mantri's omission in the version 4 kickoff).

Three sentences to carry verbatim: "The model is a kinetic description; it names no cause." "The sweep clock is the returned order; seconds are conditional on that order being chronological." "The predictions are the model's, written before the run they predict, and they are what can count against it."

## 0. Rules and conventions

Version 4's section 0 stands in full (kinds, words, the bundle as the only input, numerics, the complete set primary). Deliverables, in a folder `model-01-v4.1/`: `report-model-01-v4.1.md`; `scorer-diff-v4.1.md` (every change to the scorer's files, line by line, against version 4's); `internal-review-day3.json` and `.md` (Part A); `fits-model-01-v4.1.json`, `hierarchy-model-01-v4.1.json` (Part B); `predictions-model-01-v4.1.md` and `.json` (written last); `score_model_01_v4_1.py` and its dependencies with `FORECAST-SHA256SUMS`; the scripts as run; `run.log`; `SHA256SUMS`.

## 1. The bundle

| folder | what it holds |
|---|---|
| `v4-input/` | version 4's input bundle, unchanged (`model-01-bundle-v4-2026-10-18.zip`, with its digest) |
| `v4-output/` | version 4's run as returned (`model-01-v4.zip`, with its digest): fits, hierarchy, forecast plan, predictions, scorer |
| `t11-day3/` | test 11's third day: the per-shot arrays and meta files, the counts files, `fits-t11-day3.json` (which holds job 1's A26 per-span weights), `report-t11-day3.md`, `shots-t11-day3-hashes-before-analysis.txt` |
| `t16/` | test 16's rule and hand-back: `t16-rule.md`, `report-t16.md`, `fits-t16.json`, `scorecard-t16.json`, `tables-t16.md` |
| `rules/` | `t11-rule.md` (job 1's A26 method is stated in its job 1 paragraph and in A26's per-span reading as the day 3 report applies it) |

Check every file against the bundle's `SHA256SUMS`, both zips against their digests, and the day 3 arrays against their hashes-before-analysis file, before anything else.

## 2. The corrections (the only changes)

**C1. Calibration conditional on the scored run's own design.** At scoring time, the calibrated intervals, family cutoffs and count intervals are computed by simulating the frozen model through the scored run's actual design: the number of spans per job, the whole repeats per span and circuit after straddling repeats are left out, the shots per position, the circuit schema, and each span's sweep count. These design quantities are known before any outcome is read and carry no information about the switching. The scenario templates remain only to publish nominal intervals for readability, labelled nominal.

**C2. Sweep times.** Quantities in seconds use the scored run's own sweep times. They are calibrated when every span's sweep time lies within the record's donor range widened by 10 percent on each side; otherwise the seconds quantities are reported uncalibrated and the dimensionless ones remain calibrated. No exact-list membership test remains.

**C3. The shuffled weight.** The scorer takes the observed per-span A26 weights from the run's own fits file (`span_readings_A26` or the field the run's report names), rather than recomputing A26. The bet and its interval are unchanged in definition; the scorer now has its observation.

Nothing else in the scorer changes. `scorer-diff-v4.1.md` lists every changed line; any change outside C1 to C3 is a defect of the run.

## 3. Part A: the internal review of day 3 (labelled; not a score)

Run the corrected scorer on test 11's day 3 with **version 4's frozen fits and predictions exactly as hashed** (the files in `v4-output/`, checked against `FORECAST-SHA256SUMS` and the posted digests), not with anything refitted. Report every family's calibrated comparison, every count-against criterion, and the shuffled weight, in `internal-review-day3.md` and `.json`.

**Its label, carried at the top of both files and in every sentence that quotes it:** "Internal review: the setup was corrected after day 3's arrays were opened. These comparisons are not scores and do not count for or against version 4." Day 3's official scorecard stays test 16's.

Beside it, show that the corrected scorer reproduces test 16's 125 test-15 quantities on the same arrays exactly, and reproduces version 4's original scorecard (`scorecard-t16.json`) wherever C1 to C3 do not apply.

## 4. Part B: version 4.1's fits and predictions

1. **The fits.** Version 4's method, unchanged, on the record of 18 October plus test 11's day 3 monitors (jobs 2 and 3, a third UTC date class). The kingston and test 14 classes are carried as version 4 carried them. Report the hierarchy's spreads with day 3 included beside version 4's.
2. **The predictions,** written last, for two designs, each from the fitted hierarchy's empirical day extension (now over three dates), each with its count-against criteria in version 4's form:
   - **D1:** the next run of test 11's monitor design on 143 (5.6 µs, X then Y, 300 positions, 1,000 shots, two jobs), any number of spans.
   - **D2:** one longer monitor job of the same circuits with 600 positions (about six spans), with the per-span duty, τ_c, emissions and the boundary words.
   Calibration for both is C1's: computed at scoring time through the scored run's actual design; the files publish nominal intervals for readability, labelled nominal.
3. **No channel is added.** The middle-span pattern noticed on 19 October is not modeled and not bet on; any prediction the model's form implies about it (it implies none beyond stationarity within a job) is stated as such.
4. **The scorer** `score_model_01_v4_1.py` is hashed with the predictions in `FORECAST-SHA256SUMS`, and rehearsed on day 2's and day 3's arrays; the rehearsals are computation checks, not prospective validation.

## 5. What would count against version 4.1

Version 4's list, unchanged, applied under C1 to C3.

## 6. Readings, labelled

One paragraph each, no cause: what changed in the hierarchy with a third date; whether day 3's slower switching sits inside version 4's length spread or stretches it; what Part A's internal review shows and why it does not count.
