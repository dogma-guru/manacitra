# Model 01, version 3, run 3.1

17 October 2026. Bundle only desk computation. No hardware submission.

The model is a kinetic description; it names no cause.

A record below its own floor is censored, not absent.

The predictions are the model's, written before the run they predict, and they are what can prove it wrong.

## 1. Input and standing of the statements

All 48 listed input files match their SHA256 digests. The archive matches its supplied sidecar, and its extracted file inventory has no missing or unlisted file. The archive digest is `8684b8f3e3d2cf52ea50a5ea518ae4475264c0d2f7d45d1590846ea4ff1c4299`. Sources: `input-hash-check.json` and `input-recheck.json`.

The errata was read before the version 3 and inherited version 2 kickoffs. The required report sections and fits metadata were read before analysis. No earlier run output was opened. Initial prompt discovery searched the local memory registry and filenames; unrelated review entries were not used as inputs. Each ledger agent received only this run directory and its instructions. Installed numerical libraries supplied the runtime, with no scientific file imported from their host project. Nothing was fetched.

Counts, exposures and arithmetic below are computed facts of the archived records. Posteriors, intervals and future probabilities are model outputs conditional on the declared likelihood and priors. Section 6 contains assistant readings. These readings have not been adopted by the author or Mantri. Hash agreement establishes file identity to the supplied manifest, not an independent certification of hardware observations.

Arithmetic uses float64 with Python 3.14.8, NumPy 2.5.4 and SciPy 1.18.1. The model check uses seed 310017 and 1,000 simulations per eligible cell. Source fitting seeds are preserved in the input fits metadata and command record; no fit was rerun. `run.log` retains exact current run command inputs and the runtime record.

The output folder is `model-01-v3.1/`, as the runner prompt specifies. The kickoff listed version 3 basenames, which are retained inside it. The supplied input copy is included for a portable rerun.

## 2. Event ledgers and definitions

### 2.1 Frequency and the required count comparison

The primary population is every repeat pair satisfying the explicit line observation criterion. The alternate filter that first removes an entire unusable qubit job is retained in each frequency row and summary. This choice changes some own floor denominators, but changes none of the requested 4 kHz counts. No alternative was selected to reduce a count.

| Test and job | Within at 4 kHz | Boundary at 4 kHz | Within at own floor | Boundary at own floor | Required comparison |
| --- | --- | --- | --- | --- | --- |
| 9, job 2 | 0 / 509 | 0 / 77 | 0 / 788 | 0 / 118 | exact |
| 9, job 3 | 0 / 349 | 0 / 55 | 0 / 656 | 0 / 98 | exact |
| 10, job 1 | 0 / 9100 | 1 / 125 | 0 / 9726 | 1 / 133 | exact |
| 10, job 2 | 0 / 9033 | 0 / 124 | 0 / 9738 | 0 / 136 | exact |
| 10, job 3 | 0 / 7073 | 0 / 98 | 0 / 7930 | 0 / 110 | exact |

Sources: `frequency-ledger.json:summaries`, `required_count_comparisons` and the source file and field recorded on each row. Test 11 adds 0 / 285 within trials and 0 / 4 boundary trials at its own phase floor. Every one is censored at 4 kHz; it adds no 4 kHz exposure.

| Test and job | Exposure at 4 kHz, s | Exposure at own floor, s | Censored exposure, s |
| --- | --- | --- | --- |
| 9, job 2 | 2692.06 | 4174.67 | 1482.61 |
| 9, job 3 | 1800.93 | 3385.54 | 1584.61 |
| 10, job 1 | 5839.95 | 6241.79 | 401.843 |
| 10, job 2 | 5801.21 | 6253.39 | 452.18 |
| 10, job 3 | 4285.02 | 4804.18 | 519.152 |
| 11, jobs 2 and 3 | 0 | 167.736 | 167.736 |

The pair threshold uses the recorded errors. The required endpoint calculation gives zero test 9 scan boundary events at both floors. Thus the own floor count minus the 4 kHz count is zero in that ledger. It does not reproduce the source fitted level change counts: 22 reported change points use fits across several repeats and are a different observable. Every change point and its relation to the endpoint exclusions is retained in `frequency-ledger.json:source_fitted_level_changes_separate_observable`. This is a difference in applying the requested definitions, not a reconciliation by changing the event rule.

Provider positions assign spans. Test 10 has no straddling repeat. Test 9 straddles are excluded; bridge boundary pairs use the last and first whole repeats. For test 11 job 2 the bridge pairs are (48, 51) and (99, 101); for job 3 they are (49, 51) and (99, 101). Job 2 actually has 100, 101 and 99 provider positions in its spans because position 100 precedes 99. The general 101, 100, 99 wording does not apply to that job. Sources: `frequency-ledger.json:span_assignments`; `monitor11-ledger.json:execution_mapping`.

Every alternating qubit and its pairs follows. The row pointers distinguish within pairs, excluded adjacent pairs and bridge boundary pairs. Source: `frequency-ledger.json:alternating_qubits`.

| Test and job | Qubit | Pairs |
| --- | --- | --- |
| 9, job 2 | 7 | (5, 6), (6, 7), (6, 8) |
| 9, job 2 | 50 | (4, 5), (5, 6), (11, 12), (13, 14), (15, 16), (17, 18), (12, 14) |
| 9, job 2 | 67 | (2, 3), (3, 4) |
| 9, job 2 | 69 | (15, 16), (16, 17) |
| 9, job 2 | 95 | (1, 2), (9, 10) |
| 9, job 2 | 96 | (16, 17), (17, 18) |
| 9, job 2 | 101 | (2, 3), (4, 5), (5, 6), (6, 7), (6, 8) |
| 9, job 2 | 138 | (9, 10), (16, 17) |
| 9, job 2 | 142 | (6, 7), (11, 12), (12, 13), (14, 15), (17, 18), (6, 8) |
| 9, job 2 | 152 | (5, 6), (6, 7), (7, 8), (8, 9), (9, 10), (11, 12) |
| 9, job 3 | 5 | (1, 2), (2, 3), (3, 4), (4, 5), (13, 14), (14, 15), (12, 14) |
| 9, job 3 | 18 | (7, 8), (8, 9), (13, 14), (14, 15), (6, 8), (12, 14) |
| 9, job 3 | 61 | (1, 2), (7, 8), (8, 9), (11, 12), (13, 14), (15, 16), (16, 17), (6, 8), (12, 14) |
| 9, job 3 | 90 | (2, 3), (3, 4) |
| 9, job 3 | 129 | (13, 14), (14, 15), (15, 16), (17, 18), (12, 14) |
| 9, job 3 | 143 | (15, 16) |

Exclusion exposure is kept beside the fitted exposure. For straddles it is a nominal duration from the relevant span periods; the source provides no individual circuit clock time. A pair can have more than one reason, so the reason totals must not be added. Sources: `frequency-ledger.json:summaries` and `ambiguities`.

| Test and job | Alternation excluded nominal s | Straddling excluded nominal s |
| --- | --- | --- |
| 9, job 2 | 175.074 | 1507.32 |
| 9, job 3 | 124.163 | 1206.9 |
| 10, job 1 | 0 | 0 |
| 10, job 2 | 0 | 0 |
| 10, job 3 | 0 | 0 |

Kind transitions are reported outside the rate fits. Requiring the destination kind to persist for at least two repeats yields 163 events; requiring both runs to last at least two yields 61. The wording only explicitly requires destination persistence. Every transition, run length and span position is listed in `frequency-ledger.json:kind_transitions`; selected events are in `kind_events`. This includes test 9 job 2 qubit 134 at repeat 7 and qubit 120 at repeat 14. No rate is fitted to these counts.

### 2.2 Weight boundaries, complete eligible population

| Design and record | Own resolution events / trials | Fixed 0.10 events / trials |
| --- | --- | --- |
| t11 job1 | 1 / 2 | 0 / 2 |
| t7 job1 | 2 / 2 | 1 / 2 |
| t8 job1 | 5 / 18 | 2 / 18 |
| t8 job3 | 2 / 2 | 2 / 2 |
| t9 job1 | 6 / 14 | 6 / 14 |
| All shuffled | 16 / 38 | 11 / 38 |
| Test 11 monitors | 4 / 4 | 1 / 4 |
| Pooled descriptive comparison | 20 / 42 | 12 / 42 |
| Original selected subset before test 11 | 9 / 10 | 7 / 10 |

Sources: `shuffled-stamp-ledger.json:weight_boundaries` and `monitor11-ledger.json:trials`. Span means use inverse variance weighting for shuffled positions and plain means over whole repeats for monitors. Monitor errors are the larger of propagated and scatter errors. The own resolution boundary rule is strictly above five combined errors. The fixed column uses the plain means of the nearest three eligible positions or whole repeats on each side at 0.10. The monitor endpoint rule is a separate retained observable and gives 0 / 4, including the last bridge change of 0.110621 against its 0.112742 threshold.

Four eligible test 8 job 2 records, qubits 10, 67, 115 and 149, have no provider span record in this bundle. They are skipped explicitly in `shuffled-stamp-ledger.json:skipped_weight_jobs`. Test 11 job 1 first boundary is 13.1774 combined errors, agreeing with the errata’s correction.

### 2.3 The monitor weight within spans

| Job | Span | Whole repeats | Mean weight | Adopted error | Chi squared / df | Slope per repeat | Slope error |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 0 | 48 | 0.340218 | 0.00234385 | 0.585219 | 8.21321e−05 | 0.000169265 |
| 2 | 1 | 49 | 0.391806 | 0.00235089 | 0.568358 | −0.000202156 | 0.000166089 |
| 2 | 2 | 48 | 0.359627 | 0.00235715 | 0.462156 | 0.000166648 | 0.000170259 |
| 3 | 0 | 49 | 0.322806 | 0.00230454 | 0.568314 | 4.68493e−05 | 0.000162851 |
| 3 | 1 | 49 | 0.349991 | 0.00232489 | 0.596562 | −8.50617e−05 | 0.000164409 |
| 3 | 2 | 48 | 0.236767 | 0.00223944 | 0.582905 | 2.29061e−05 | 0.000161643 |

The means rounded to three decimals are 0.340, 0.392, 0.360 and 0.323, 0.350, 0.237, exactly as requested. There are 0 / 285 within weight events over 167.735524 seconds at max(0.10, five combined errors), and also zero at five combined errors alone. Nine adjacent pairs touch straddling repeats and are excluded. Raw counts reconstruct the saved radius, angle, errors and weight to within 1e−12. Sources: `monitor11-ledger.json:per_span`, `trials`, `raw_recomputation_checks`.

### 2.4 Gaps, stamps, copies and split

The test 10 gap is 130.111131 seconds: 1 / 63 frequency events at 4 kHz and 1 / 68 at the own floor. Test 11’s gap is 63.518444 seconds: 0 / 1 frequency events at its own floor and 1 / 1 weight events from the last and first span means. The weight change is −0.0368211, or 11.1697 combined errors. These gap records are separate from boundary fits. The transition from test 11 job 1 to job 2 is excluded from weight trials because the estimators differ. Sources: each ledger’s gap rows and `rates-model-01-v3.json:separate_gap_classes`.

Stamp pair 1 is 16 / 47 on the specified test 8 job 1 and test 9 job 1 intersection; the version 3 kickoff explicitly names this count. Both stamps lie on 17 October. The inherited version 2 wording also names 63: its table includes 16 further qubits from test 8 job 2. Those add 9 events, yielding 25 / 63 as an explicit alternative. Adding 143’s crossing to the primary population gives 17 / 48. That crossing spans 16 to 17 October. Sources: `shuffled-stamp-ledger.json:stamps`, `stamps_alternative_job2`.

For 143, `S.params.Delta_MHz` changes by −152.823169 kHz, while `P.params.Delta0_MHz` changes by −62.723613 kHz. The S event uses the former. A P frame change and an S detuning change are not interchangeable. The second requested stamp comparison is not reconstructable as written: the monitor supplies a phase at one wait without an identified common absolute frequency reference and branch, and its temporal verdict is not a line count kind. All 322 candidate comparisons over 121 distinct qubits, source fields, and zero phase and job mean reference alternatives are retained with null event flags in `stamp_pair2_unavailable`. No invented conversion enters the S fit.

A copies disagreement means the same span sum of squared z exceeds the 99.9th percentile of chi squared on the number of copy pairs. The copies recount gives 4 / 441 same span disagreements in the requested tests 8 and 9 population. They are test 8 job 1 qubit 97 span 1; test 8 job 3 qubit 43 span 1; and test 9 job 1 qubits 38 and 47 span 1. Their size in kHz is not available and they are not fitted. Including tests 7 and 11 gives 4 / 447. The complete copy pair and span tables are in `copies_pair_rows` and `copies_same_span`.

The only eligible split crossing is 143: 44.823202 to 44.704968 kHz, a difference of −0.118234 kHz. This is −1.01667 times the quadrature combined 90 percent interval half widths, or −1.67227 Gaussian equivalent standard errors if that conversion is imposed. Both full width and half width conventions are retained. Qubit 43’s test 9 verdict is NOT SETTLED, so it does not meet the requirement that both records say TWO FIXED FREQUENCIES. The split observable is not fitted. Source: `shuffled-stamp-ledger.json:split_observable`.

### 2.5 Estimator comparison

The full estimator table is `estimators-model-01-v3.json`. Job 1 has whole job b = 0.466151 with interval 0.457970 to 0.474017 and span means 0.495725, 0.432947, 0.448104. The shuffled calculation holds P at its fit and assumes one weight over the positions averaged. The monitor uses radius and R0 and assumes equal amplitude and decay on the two lines and exact antiphase. The job 1 final span to job 2 first span gap is 56.773459 seconds under one stamp. No value is corrected using the other estimator.

R0 = 0.474867539876 and its sensitivity are fully tabulated in `estimators-model-01-v3.json:R0`. For a branch below one half, w = (1 − r/R0) / 2. Multiplying R0 by a factor a moves w by (0.5 − w)(1 − 1/a). The file gives each span at factors 0.9 and 1.1 using its actual radius. This is a sensitivity calculation, not an error correction.

## 3. Rates, with their standing as model outputs

The likelihood uses independent Poisson trials for within exposure and Binomial trials for boundaries or stamps, with Jeffreys priors. The table gives posterior medians and the 5th and 95th percentiles. Within rates are per qubit second; the others are probabilities per eligible trial. The independence assumption is not established by this fit.

| Channel and floor | Events / trials | Exposure s | Median | 90 percent interval |
| --- | --- | --- | --- | --- |
| B at fixed0.10 | 12 / 42 | 0 | 0.287427 | 0.183794 to 0.408794 |
| B at own | 20 / 42 | 0 | 0.47638 | 0.353339 to 0.601395 |
| F at 4kHz | 1 / 479 | 0 | 0.00246794 | 0.000367396 to 0.00812839 |
| F at own | 1 / 599 | 0 | 0.00197381 | 0.000293774 to 0.00650462 |
| S at 4kHz | 17 / 48 | 0 | 0.355184 | 0.248983 to 0.472002 |
| W at 4kHz | 0 / 26064 | 20419.2 | 1.11399e−05 | 9.62855e−08 to 9.4065e−05 |
| W at own | 0 / 29123 | 25027.3 | 9.0888e−06 | 7.8557e−08 to 7.67453e−05 |
| W_B at fixed0.10 | 0 / 285 | 167.736 | 0.00135611 | 1.17212e−05 to 0.0114509 |
| W_B at own | 0 / 285 | 167.736 | 0.00135611 | 1.17212e−05 to 0.0114509 |

Channel B is fitted by design for prediction. The pooled row above is only a comparison.

| Design and floor | Events / trials | Exposure s | Median | 90 percent interval |
| --- | --- | --- | --- | --- |
| monitor at own | 4 / 4 | 0 | 0.947985 | 0.637513 to 0.999538 |
| shuffled at own | 16 / 38 | 0 | 0.421749 | 0.296697 to 0.554002 |
| monitor at fixed0.10 | 1 / 4 | 0 | 0.271807 | 0.0460072 to 0.650707 |
| shuffled at fixed0.10 | 11 / 38 | 0 | 0.291334 | 0.18244 to 0.419411 |

Sources: `rates-model-01-v3.json:pooled` and `classes`, each with normalized source row identifiers. Class fits also retain design, stamp, boundary ordinal, gap bin and processor record as applicable. The 5 ms and 14 to 15 s monitor bins remain distinct.

| Within channel and floor | Posterior probability rate below 0.0001 |
| --- | --- |
| W at 4kHz | 0.956705 |
| W at own | 0.974733 |
| W_B at fixed0.10 | 0.145326 |
| W_B at own | 0.145326 |

## 4. Dependence comparisons

Every requested pairwise class contrast is in `dependence-model-01-v3.json:tests`. The following table gives the Binomial contrasts; all Poisson contrasts have zero events in both groups, likelihood ratio zero and p = 1, which does not establish equal rates. No multiplicity correction or clustered sampling model is implied.

| Channel | Floor | Split | Classes | Two sided Fisher p |
| --- | --- | --- | --- | --- |
| B | fixed0.10 | design | monitor, shuffled | 1 |
| B | fixed0.10 | processor_record | 143, kingston qubits | 1 |
| B | fixed0.10 | boundary | 1, 2 | 0.733718 |
| B | fixed0.10 | gap_bin | 1 to 3 s, 14 to 15 s | 0.514706 |
| B | fixed0.10 | gap_bin | 1 to 3 s, 5 ms | 1 |
| B | fixed0.10 | gap_bin | 1 to 3 s, under 1 s | 0.25222 |
| B | fixed0.10 | gap_bin | 14 to 15 s, 5 ms | 0.464286 |
| B | fixed0.10 | gap_bin | 14 to 15 s, under 1 s | 1 |
| B | fixed0.10 | gap_bin | 5 ms, under 1 s | 0.562281 |
| B | own | design | monitor, shuffled | 0.043286 |
| B | own | processor_record | 143, kingston qubits | 0.0182257 |
| B | own | boundary | 1, 2 | 1 |
| B | own | gap_bin | 1 to 3 s, 14 to 15 s | 0.576471 |
| B | own | gap_bin | 1 to 3 s, 5 ms | 0.0445476 |
| B | own | gap_bin | 1 to 3 s, under 1 s | 0.728237 |
| B | own | gap_bin | 14 to 15 s, 5 ms | 0.375 |
| B | own | gap_bin | 14 to 15 s, under 1 s | 0.537549 |
| B | own | gap_bin | 5 ms, under 1 s | 0.0149068 |
| F | 4kHz | design | monitor, scan | 1 |
| F | 4kHz | boundary | 1, 2 | 0.498956 |
| F | 4kHz | gap_bin | 1 to 3 s, over 3 s | 1 |
| F | 4kHz | gap_bin | 1 to 3 s, under 1 s | 1 |
| F | 4kHz | gap_bin | over 3 s, under 1 s | 1 |
| F | 4kHz | stamp | 2026-10-17T14:06:47Z, 2026-10-17T16:22:59Z | 1 |
| F | own | design | monitor, scan | 1 |
| F | own | boundary | 1, 2 | 1 |
| F | own | gap_bin | 1 to 3 s, 14 to 15 s | 1 |
| F | own | gap_bin | 1 to 3 s, 5 ms | 1 |
| F | own | gap_bin | 1 to 3 s, over 3 s | 1 |
| F | own | gap_bin | 1 to 3 s, under 1 s | 1 |
| F | own | gap_bin | 14 to 15 s, 5 ms | 1 |
| F | own | gap_bin | 14 to 15 s, over 3 s | 1 |
| F | own | gap_bin | 14 to 15 s, under 1 s | 1 |
| F | own | gap_bin | 5 ms, over 3 s | 1 |
| F | own | gap_bin | 5 ms, under 1 s | 1 |
| F | own | gap_bin | over 3 s, under 1 s | 1 |
| F | own | stamp | 2026-10-17T14:06:47Z, 2026-10-17T16:22:59Z | 1 |
| F | own | stamp | 2026-10-17T14:06:47Z, 2026-10-17T18:48:16Z | 1 |
| F | own | stamp | 2026-10-17T16:22:59Z, 2026-10-17T18:48:16Z | 1 |
| S | 4kHz | stamp_pair | pair1, t7_to_t11 | 0.354167 |
| ['F', 'B'] | ['4kHz', 'fixed0.10'] | across channels |  | 1.84944e−13 |
| ['F', 'B'] | ['own', 'own'] | across channels |  | 2.49528e−25 |
| F | five SE only | test10 boundary ordinal | first, second | 0.248021 |
| F | 4kHz | test10 boundary ordinal | first, second | 1 |

The B design contrast compares event rates under different errors and estimators. Its p value does not identify a cause or remove the instruction to predict within each design. Across channels, only F against B is tested. At five combined errors alone, test 10 first boundaries give 0 / 190 and second boundaries 3 / 190; controls give 0 / 570. The 0.3 rad floor and 4 kHz censoring change which of those differences enter F. Sources: `frequency-ledger.json:supplementary_five_se` and the final dependence test.

## 5. Model check and historical scorecard

For each eligible test and channel, 1,000 draws at the fitted posterior median use that cell’s exposure or trial count. B uses its matching design. A second simulation draws rates from their posteriors. The observed count is treated as a singleton range; the exact match fraction is reported. These are checks against the data used for fitting, not prospective validation.

| Channel | Floor | Test | Design model | Observed | Simulated 90 percent count interval | Exact match fraction | Inside |
| --- | --- | --- | --- | --- | --- | --- | --- |
| B | fixed0.10 | 7 | shuffled | 1 | [0, 2] | 0.416 | True |
| B | fixed0.10 | 8 | shuffled | 4 | [3, 9] | 0.138 | True |
| B | fixed0.10 | 9 | shuffled | 6 | [2, 7] | 0.107 | True |
| B | fixed0.10 | 11 | monitor | 1 | [0, 3] | 0.422 | True |
| B | fixed0.10 | 11 | shuffled | 0 | [0, 2] | 0.483 | True |
| B | own | 7 | shuffled | 2 | [0, 2] | 0.17 | True |
| B | own | 8 | shuffled | 7 | [5, 12] | 0.141 | True |
| B | own | 9 | shuffled | 6 | [3, 9] | 0.222 | True |
| B | own | 11 | monitor | 4 | [3, 4] | 0.813 | True |
| B | own | 11 | shuffled | 1 | [0, 2] | 0.504 | True |
| F | 4kHz | 9 | pooled | 0 | [0, 1] | 0.721 | True |
| F | 4kHz | 10 | pooled | 1 | [0, 3] | 0.352 | True |
| F | 4kHz | 11 | pooled | None | not testable | not testable | censored |
| F | own | 9 | pooled | 0 | [0, 2] | 0.648 | True |
| F | own | 10 | pooled | 1 | [0, 2] | 0.349 | True |
| F | own | 11 | pooled | 0 | [0, 0] | 0.989 | True |
| S | 4kHz | 9 | pooled | 16 | [11, 22] | 0.126 | True |
| S | 4kHz | 11 | pooled | 1 | [0, 1] | 0.345 | True |
| W | 4kHz | 9 | pooled | 0 | [0, 0] | 0.95 | True |
| W | 4kHz | 10 | pooled | 0 | [0, 1] | 0.826 | True |
| W | 4kHz | 11 | pooled | None | not testable | not testable | censored |
| W | own | 9 | pooled | 0 | [0, 1] | 0.932 | True |
| W | own | 10 | pooled | 0 | [0, 1] | 0.878 | True |
| W | own | 11 | pooled | 0 | [0, 0] | 0.996 | True |
| W_B | fixed0.10 | 11 | pooled | 0 | [0, 1] | 0.784 | True |
| W_B | own | 11 | pooled | 0 | [0, 1] | 0.795 | True |

No eligible observed cell lies outside its simulated 5th to 95th percentiles. Test 11 frequency at 4 kHz is explicitly censored and not testable. Stamp pair 2 is unavailable. Source: `model-check-model-01-v3.json`.

Sensitivity at the upper rate percentile, and boundary trial counts required for a 90 percent chance of at least three events, follow. These are model outputs, not resource or hardware assurances.

| Model | Target | Required amount |
| --- | --- | --- |
| B at fixed0.10 pooled | trials for three events at low, median, high p | 28, 17, 12 |
| B at fixed0.10 monitor | trials for three events at low, median, high p | 115, 18, 7 |
| B at fixed0.10 shuffled | trials for three events at low, median, high p | 28, 17, 11 |
| B at own pooled | trials for three events at low, median, high p | 14, 10, 7 |
| B at own monitor | trials for three events at low, median, high p | 7, 4, 3 |
| B at own shuffled | trials for three events at low, median, high p | 17, 11, 8 |
| F at 4kHz pooled | trials for three events at low, median, high p | 14485, 2155, 654 |
| F at own pooled | trials for three events at low, median, high p | 18116, 2695, 817 |
| S at 4kHz pooled | trials for three events at low, median, high p | 20, 14, 10 |
| W at 4kHz | qubit seconds for one event | 24478.7 |
| W at own | qubit seconds for one event | 30002.9 |
| W_B at fixed0.10 | qubit seconds for one event | 201.083 |
| W_B at own | qubit seconds for one event | 201.083 |

The four historical outcomes are recomputed below. The original sealed files are not in the bundle; their quoted numbers are in `input/t11/fits-t11.json:counts_of_the_run` and `input/rules/t11-rule.md`. A probability interval cannot be scored by asking whether an observed zero is inside it. Where the quoted count interval is missing, the literal inside or outside question is unavailable. For comparison, the last column uses an explicitly reconstructed Jeffreys predictive count interval from the pre test 11 ledger and the declared trial count. It is not presented as the original sealed interval.

| Bet | Quoted probability | Outcome count | Quoted count comparison | Reconstructed 90 percent count interval |
| --- | --- | --- | --- | --- |
| Frequency boundaries in two monitors | 0.008, interval 0.001 to 0.026 | 0 | Quoted count 0 matches | 0 to 0 |
| Frequency within two monitors | 0.002 | 0 | Interval absent | 0 to 0 |
| Weight boundaries in shuffled job | 0.52, interval 0.35 to 0.69; selected subset 0.91 | 0 | Interval absent | 0 to 2 |
| Frequency between monitor jobs | About 1 in 60 | 0 | Interval absent | 0 to 0 |

The named weight occurrence did not happen at 0.10. That outcome lies inside the reconstructed count interval and does not by itself contradict an event probability of 0.52. The own resolution weight event is a changed observable and is not used to rescore the old fixed floor bet. The within frequency design quoted about 186 seconds; actual eligible time is 167.735524 seconds. Sources and both selected and complete population reconstructions are in `historical-scorecard.json`.

## 6. Readings, labelled as assistant interpretations

The counts contain no within frequency event and no within monitor weight event under the stated rules. This supports small rates over these exposures, but zero is a boundary value outside the continuous Jeffreys posterior’s support and is not established as an exact rate. The own resolution B estimates sit above the fixed 0.10 estimates, especially in the monitor class. The gap class contains an observed monitor weight change, but one trial supplies no separately specified kinetic rate. The stamp probability concerns its composite S definition and does not directly estimate P frame movement.

The monitor span means differ and the successive jobs contain a further span mean difference under the same recorded stamp. Within individual spans the measured scatter and fitted slopes do not supply a resolved walk under these calculations. The record therefore supports differing span levels and an across job sequence, without choosing what sets those levels. The shuffled and monitor estimates rest on different assumptions, so the sequence must retain the estimator boundary.

Each floor hides a different part of the record. The 4 kHz frequency fit omits censored pairs; the own frequency fit combines thresholds of different sizes. The within weight event rate tests pair changes, while the boundary weight probability tests means over spans. The copies disagreements have no calibrated frequency size. Non line observations and amplitude alternation are features of the one line representation and its exclusions, not an identified mechanism. None of these counts determines a dwell distribution or a distribution of within span weight scatter from the kinetic rates alone.

## 7. Future predictions and handoff

The future forecasts are in `predictions-model-01-v3.json` and `predictions-model-01-v3.md`, written last from these frozen model outputs. Those files name the channel, design, estimator, eligible exposure and interval for each numerical forecast, and mark quantities that this model cannot predict. The author can hash them before any future run. They are the model’s forecasts, not the author’s or Mantri’s.

All source ledgers are preserved in `events-model-01-v3.json`. The split, copies, excluded pairs, alternate populations, kind persistence alternatives and unavailable records remain beside the fitted channels. Scripts and the full input copy permit reproduction. `SHA256SUMS` covers every delivered file except itself.

