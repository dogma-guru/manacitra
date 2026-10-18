# Model 01 future predictions, version 3, run 3.1

These are model outputs for a future run, written after the report and rates. The JSON records the source file hashes, assumptions, trial counts and calculation paths. No earlier run output supplied an input.

The predictions are the model's, written before the run they predict, and they are what can prove it wrong.

Probability intervals and predictive count intervals answer different questions. The table uses the probability at the posterior median rate, its 90 percent parameter interval, and the count interval integrated over the parameter posterior.

| Forecast | Channel and estimator | Probability of at least one | Probability interval | Predictive count interval |
|---|---|---|---|---|
| Two shuffled weight boundaries | B, shuffled | 0.665626 | 0.505365 to 0.801086 | 0 to 2 |
| Four monitor weight boundaries | B, monitor | 0.999993 | 0.982735 to 1 | 2 to 4 |
| Within monitor weight over 170 seconds | W_B, monitor | 0.205895 | 0.00199063 to 0.85725 | 0 to 3 |
| Four monitor frequency boundaries | F, phase | 0.0078719 | 0.00117458 to 0.0257657 | 0 to 0 |
| Within monitor frequency over 170 seconds | W, phase | 0.0015439 | 1.33546e-05 to 0.012962 | 0 to 0 |
| One composite stamp crossing | S, S detuning or kind | 0.355184 | 0.248983 to 0.472002 | 0 to 1 |

For any frequency event across those four boundaries or 170 seconds within spans, the probability at the median rates is 0.00940365; the joint posterior probability interval is 0.00238467 to 0.0312721. The integrated predictive probability is 0.0132833. This uses the stated channel independence.

Every weight boundary forecast uses the posterior for its own design and estimator. The fixed 0.10 forecasts remain beside in JSON. The frequency forecast uses the own floor pooled rate, with a monitor only sensitivity beside. The archived monitor thresholds are about 18 to 23 kHz, with individual pair variation. A fitted rate across unequal own floors is not a calibrated universal 23 kHz rate.

A probability for the weight change between monitor jobs is unavailable: the requested five channel model has no fitted gap probability. The observed gap is one event in one trial and remains separate. Substituting a boundary probability would change its referent.

The kinetic rate does not predict within span scatter. JSON supplies the recorded scatter and a conditional calculation from the recorded errors if independent Gaussian errors recur. That additional noise assumption is explicitly a reading. The observed chi squared per degree of freedom spans 0.462 to 0.597. The reference mean of 1 uses an equal variance Gaussian approximation; the recorded errors differ slightly. The reported noise scale is the square root of expected sample variance, not an expectation of sample standard deviation.

The stamp row predicts an S detuning change of at least 4 kHz or a kind change. It does not identify the probability that the P frame moves. Only one eligible split crossing is available, with a change of about −0.118 kHz; no probability is assigned to staying within 0.5 kHz of 44.7. This is a reading only.

For scan and monitor back to back on set S, the source mask scenarios follow. The future provider spans and errors decide actual eligibility. The all eligible scenario has two boundaries for each of the 68 qubits and is also saved in JSON.

| Design | Eligible boundary trials in source mask | Expected count | Predictive count interval | Eligible within exposure, seconds |
|---|---|---|---|---|
| scan | 77 | 0.240625 | 0 to 1 | 2692.06 |
| monitor | 125 | 0.390625 | 0 to 2 | 5839.95 |

Even odds time is reported in qubit seconds. The first time transforms the median rate. The separate integrated time averages uncertainty in that rate.

| Channel and floor | Time at median rate | 90 percent parameter time interval | Integrated predictive even odds time |
|---|---|---|---|
| W at 4kHz | 62221.9 | 7368.81 to 7.19888e+06 | 61257.5 |
| W at own | 76263.9 | 9031.78 to 8.82349e+06 | 75081.9 |
| W_B at fixed0.10 | 511.128 | 60.5319 to 59135.9 | 503.207 |
| W_B at own | 511.128 | 60.5319 to 59135.9 | 503.207 |

For each declared trial count, a count outside its saved predictive interval in either direction counts against the associated transfer. The kickoff also names any within weight event in the next 1,000 eligible monitor pairs at the fixed floor, and a split change above 1 kHz across a stamp on a qubit confirmed on both sides. The first is stricter than a generic predictive interval test; its actual interval and probability are saved in JSON. A nonexponential dwell distribution could count against the Poisson assumption if events accumulate.

These forecasts require eligible records. A censored observation is not scored as a zero event. The author can hash these files before the future run.
