"""Write the completed data and model report before the future predictions."""
from pathlib import Path
import json,sys,math
ROOT=Path(__file__).resolve().parents[1]
def load(n):return json.loads((ROOT/n).read_text())
f=load('frequency-ledger.json');fn=load('frequency-notes.json');s=load('shuffled-stamp-ledger.json');sn=load('shuffled-stamp-notes.json')
m=load('monitor11-ledger.json');e=load('estimators-model-01-v3.json');r=load('rates-model-01-v3.json')
d=load('dependence-model-01-v3.json');c=load('model-check-model-01-v3.json');h=load('historical-scorecard.json');runtime=load('runtime.json')
out=[]
def put(x=''):out.append(x)
def table(headers,rows):
    put('| '+' | '.join(headers)+' |');put('| '+' | '.join(['---']*len(headers))+' |')
    for row in rows:put('| '+' | '.join(str(x).replace('|',' / ') for x in row)+' |')
    put()
def num(x):
    return f'{x:.6g}'.replace('-','−') if isinstance(x,(float,int)) else str(x)
def rate_row(label,v):
    return [label,f"{v['events']} / {v['trials']}",num(v['exposure_s']),num(v['median']),f"{num(v['q05'])} to {num(v['q95'])}"]

put('# Model 01, version 3, run 3.1')
put('\n17 October 2026. Bundle only desk computation. No hardware submission.\n')
put('The model is a kinetic description; it names no cause.\n')
put('A record below its own floor is censored, not absent.\n')
put("The predictions are the model's, written before the run they predict, and they are what can prove it wrong.\n")
put('## 1. Input and standing of the statements\n')
put('All 48 listed input files match their SHA256 digests. The archive matches its supplied sidecar, and its extracted file inventory has no missing or unlisted file. The archive digest is `8684b8f3e3d2cf52ea50a5ea518ae4475264c0d2f7d45d1590846ea4ff1c4299`. Sources: `input-hash-check.json` and `input-recheck.json`.\n')
put('The errata was read before the version 3 and inherited version 2 kickoffs. The required report sections and fits metadata were read before analysis. No earlier run output was opened. Initial prompt discovery searched the local memory registry and filenames; unrelated review entries were not used as inputs. Each ledger agent received only this run directory and its instructions. Installed numerical libraries supplied the runtime, with no scientific file imported from their host project. Nothing was fetched.\n')
put('Counts, exposures and arithmetic below are computed facts of the archived records. Posteriors, intervals and future probabilities are model outputs conditional on the declared likelihood and priors. Section 6 contains assistant readings. These readings have not been adopted by the author or Mantri. Hash agreement establishes file identity to the supplied manifest, not an independent certification of hardware observations.\n')
put(f"Arithmetic uses float64 with Python {runtime['python'].split()[0]}, NumPy {runtime['numpy']} and SciPy {runtime['scipy']}. The model check uses seed 310017 and 1,000 simulations per eligible cell. Source fitting seeds are preserved in the input fits metadata and command record; no fit was rerun. `run.log` retains exact current run command inputs and the runtime record.\n")
put('The output folder is `model-01-v3.1/`, as the runner prompt specifies. The kickoff listed version 3 basenames, which are retained inside it. The supplied input copy is included for a portable rerun.\n')

put('## 2. Event ledgers and definitions\n')
put('### 2.1 Frequency and the required count comparison\n')
put('The primary population is every repeat pair satisfying the explicit line observation criterion. The alternate filter that first removes an entire unusable qubit job is retained in each frequency row and summary. This choice changes some own floor denominators, but changes none of the requested 4 kHz counts. No alternative was selected to reduce a count.\n')
rows=[]
for test,job in [(9,2),(9,3),(10,1),(10,2),(10,3)]:
    w=f['summaries'][f't{test}j{job}:within_span']; b=f['summaries'][f't{test}j{job}:span_boundary']
    rows.append([f'{test}, job {job}',f"{w['events_4khz']} / {w['n_4khz']}",f"{b['events_4khz']} / {b['n_4khz']}",f"{w['events_own']} / {w['n_own']}",f"{b['events_own']} / {b['n_own']}",'exact'])
table(['Test and job','Within at 4 kHz','Boundary at 4 kHz','Within at own floor','Boundary at own floor','Required comparison'],rows)
put('Sources: `frequency-ledger.json:summaries`, `required_count_comparisons` and the source file and field recorded on each row. Test 11 adds 0 / 285 within trials and 0 / 4 boundary trials at its own phase floor. Every one is censored at 4 kHz; it adds no 4 kHz exposure.\n')
table(['Test and job','Exposure at 4 kHz, s','Exposure at own floor, s','Censored exposure, s'],[
    [f'{test}, job {job}',num(f['summaries'][f't{test}j{job}:within_span']['exposure_4khz_s']),num(f['summaries'][f't{test}j{job}:within_span']['exposure_own_s']),num(f['summaries'][f't{test}j{job}:within_span']['censored_exposure_s'])]
    for test,job in [(9,2),(9,3),(10,1),(10,2),(10,3)]]+
    [['11, jobs 2 and 3','0',num(m['summary']['W']['exposure_own_s']),num(m['summary']['W']['censored_exposure_s'])]])
put('The pair threshold uses the recorded errors. The required endpoint calculation gives zero test 9 scan boundary events at both floors. Thus the own floor count minus the 4 kHz count is zero in that ledger. It does not reproduce the source fitted level change counts: 22 reported change points use fits across several repeats and are a different observable. Every change point and its relation to the endpoint exclusions is retained in `frequency-ledger.json:source_fitted_level_changes_separate_observable`. This is a difference in applying the requested definitions, not a reconciliation by changing the event rule.\n')
put('Provider positions assign spans. Test 10 has no straddling repeat. Test 9 straddles are excluded; bridge boundary pairs use the last and first whole repeats. For test 11 job 2 the bridge pairs are (48, 51) and (99, 101); for job 3 they are (49, 51) and (99, 101). Job 2 actually has 100, 101 and 99 provider positions in its spans because position 100 precedes 99. The general 101, 100, 99 wording does not apply to that job. Sources: `frequency-ledger.json:span_assignments`; `monitor11-ledger.json:execution_mapping`.\n')
put('Every alternating qubit and its pairs follows. The row pointers distinguish within pairs, excluded adjacent pairs and bridge boundary pairs. Source: `frequency-ledger.json:alternating_qubits`.\n')
table(['Test and job','Qubit','Pairs'],[[f"{a['test']}, job {a['job']}",a['qubit'],', '.join('('+', '.join(map(str,p['pair']))+')' for p in a['pairs'])] for a in f['alternating_qubits']])
put('Exclusion exposure is kept beside the fitted exposure. For straddles it is a nominal duration from the relevant span periods; the source provides no individual circuit clock time. A pair can have more than one reason, so the reason totals must not be added. Sources: `frequency-ledger.json:summaries` and `ambiguities`.\n')
table(['Test and job','Alternation excluded nominal s','Straddling excluded nominal s'],[[f'{test}, job {job}',num(sum(v['excluded_exposure_s_by_reason_overlapping']['alternation'] for v in f['summaries'].values() if v['test']==test and v['job']==job)),num(sum(v['excluded_exposure_s_by_reason_overlapping']['straddling'] for v in f['summaries'].values() if v['test']==test and v['job']==job))] for test,job in [(9,2),(9,3),(10,1),(10,2),(10,3)]])
put(f"Kind transitions are reported outside the rate fits. Requiring the destination kind to persist for at least two repeats yields {fn['kind_event_count']} events; requiring both runs to last at least two yields {fn['kind_event_count_both_runs_alternative']}. The wording only explicitly requires destination persistence. Every transition, run length and span position is listed in `frequency-ledger.json:kind_transitions`; selected events are in `kind_events`. This includes test 9 job 2 qubit 134 at repeat 7 and qubit 120 at repeat 14. No rate is fitted to these counts.\n")

put('### 2.2 Weight boundaries, complete eligible population\n')
table(['Design and record','Own resolution events / trials','Fixed 0.10 events / trials'],[
    [k.replace('_',' '),f"{v['own']['events']} / {v['own']['trials']}",f"{v['fixed']['events']} / {v['fixed']['trials']}"] for k,v in sn['summary']['weight_by_job'].items()]+
    [['All shuffled','16 / 38','11 / 38'],['Test 11 monitors','4 / 4','1 / 4'],['Pooled descriptive comparison','20 / 42','12 / 42'],['Original selected subset before test 11','9 / 10','7 / 10']])
put('Sources: `shuffled-stamp-ledger.json:weight_boundaries` and `monitor11-ledger.json:trials`. Span means use inverse variance weighting for shuffled positions and plain means over whole repeats for monitors. Monitor errors are the larger of propagated and scatter errors. The own resolution boundary rule is strictly above five combined errors. The fixed column uses the plain means of the nearest three eligible positions or whole repeats on each side at 0.10. The monitor endpoint rule is a separate retained observable and gives 0 / 4, including the last bridge change of 0.110621 against its 0.112742 threshold.\n')
put('Four eligible test 8 job 2 records, qubits 10, 67, 115 and 149, have no provider span record in this bundle. They are skipped explicitly in `shuffled-stamp-ledger.json:skipped_weight_jobs`. Test 11 job 1 first boundary is 13.1774 combined errors, agreeing with the errata’s correction.\n')

put('### 2.3 The monitor weight within spans\n')
table(['Job','Span','Whole repeats','Mean weight','Adopted error','Chi squared / df','Slope per repeat','Slope error'],[
    [x['job'],x['span'],x['n_repeats'],num(x['mean_w']),num(x['se']),num(x['chi2_per_dof']),num(x['weighted_slope_w_per_repeat']),num(x['weighted_slope_se'])] for x in m['per_span']])
put('The means rounded to three decimals are 0.340, 0.392, 0.360 and 0.323, 0.350, 0.237, exactly as requested. There are 0 / 285 within weight events over 167.735524 seconds at max(0.10, five combined errors), and also zero at five combined errors alone. Nine adjacent pairs touch straddling repeats and are excluded. Raw counts reconstruct the saved radius, angle, errors and weight to within 1e−12. Sources: `monitor11-ledger.json:per_span`, `trials`, `raw_recomputation_checks`.\n')

put('### 2.4 Gaps, stamps, copies and split\n')
put('The test 10 gap is 130.111131 seconds: 1 / 63 frequency events at 4 kHz and 1 / 68 at the own floor. Test 11’s gap is 63.518444 seconds: 0 / 1 frequency events at its own floor and 1 / 1 weight events from the last and first span means. The weight change is −0.0368211, or 11.1697 combined errors. These gap records are separate from boundary fits. The transition from test 11 job 1 to job 2 is excluded from weight trials because the estimators differ. Sources: each ledger’s gap rows and `rates-model-01-v3.json:separate_gap_classes`.\n')
put('Stamp pair 1 is 16 / 47 on the specified test 8 job 1 and test 9 job 1 intersection; the version 3 kickoff explicitly names this count. Both stamps lie on 17 October. The inherited version 2 wording also names 63: its table includes 16 further qubits from test 8 job 2. Those add 9 events, yielding 25 / 63 as an explicit alternative. Adding 143’s crossing to the primary population gives 17 / 48. That crossing spans 16 to 17 October. Sources: `shuffled-stamp-ledger.json:stamps`, `stamps_alternative_job2`.\n')
put('For 143, `S.params.Delta_MHz` changes by −152.823169 kHz, while `P.params.Delta0_MHz` changes by −62.723613 kHz. The S event uses the former. A P frame change and an S detuning change are not interchangeable. The second requested stamp comparison is not reconstructable as written: the monitor supplies a phase at one wait without an identified common absolute frequency reference and branch, and its temporal verdict is not a line count kind. All 322 candidate comparisons over 121 distinct qubits, source fields, and zero phase and job mean reference alternatives are retained with null event flags in `stamp_pair2_unavailable`. No invented conversion enters the S fit.\n')
put('A copies disagreement means the same span sum of squared z exceeds the 99.9th percentile of chi squared on the number of copy pairs. The copies recount gives 4 / 441 same span disagreements in the requested tests 8 and 9 population. They are test 8 job 1 qubit 97 span 1; test 8 job 3 qubit 43 span 1; and test 9 job 1 qubits 38 and 47 span 1. Their size in kHz is not available and they are not fitted. Including tests 7 and 11 gives 4 / 447. The complete copy pair and span tables are in `copies_pair_rows` and `copies_same_span`.\n')
put('The only eligible split crossing is 143: 44.823202 to 44.704968 kHz, a difference of −0.118234 kHz. This is −1.01667 times the quadrature combined 90 percent interval half widths, or −1.67227 Gaussian equivalent standard errors if that conversion is imposed. Both full width and half width conventions are retained. Qubit 43’s test 9 verdict is NOT SETTLED, so it does not meet the requirement that both records say TWO FIXED FREQUENCIES. The split observable is not fitted. Source: `shuffled-stamp-ledger.json:split_observable`.\n')

put('### 2.5 Estimator comparison\n')
put('The full estimator table is `estimators-model-01-v3.json`. Job 1 has whole job b = 0.466151 with interval 0.457970 to 0.474017 and span means 0.495725, 0.432947, 0.448104. The shuffled calculation holds P at its fit and assumes one weight over the positions averaged. The monitor uses radius and R0 and assumes equal amplitude and decay on the two lines and exact antiphase. The job 1 final span to job 2 first span gap is 56.773459 seconds under one stamp. No value is corrected using the other estimator.\n')
R=e['R0'];put('R0 = 0.474867539876 and its sensitivity are fully tabulated in `estimators-model-01-v3.json:R0`. For a branch below one half, w = (1 − r/R0) / 2. Multiplying R0 by a factor a moves w by (0.5 − w)(1 − 1/a). The file gives each span at factors 0.9 and 1.1 using its actual radius. This is a sensitivity calculation, not an error correction.\n')

put('## 3. Rates, with their standing as model outputs\n')
put('The likelihood uses independent Poisson trials for within exposure and Binomial trials for boundaries or stamps, with Jeffreys priors. The table gives posterior medians and the 5th and 95th percentiles. Within rates are per qubit second; the others are probabilities per eligible trial. The independence assumption is not established by this fit.\n')
table(['Channel and floor','Events / trials','Exposure s','Median','90 percent interval'],[rate_row(k.replace('|',' at '),v) for k,v in r['pooled'].items()])
put('Channel B is fitted by design for prediction. The pooled row above is only a comparison.\n')
table(['Design and floor','Events / trials','Exposure s','Median','90 percent interval'],[rate_row(design+' at '+floor,v) for floor in ['own','fixed0.10'] for design,v in r['classes']['B|'+floor]['design'].items()])
put('Sources: `rates-model-01-v3.json:pooled` and `classes`, each with normalized source row identifiers. Class fits also retain design, stamp, boundary ordinal, gap bin and processor record as applicable. The 5 ms and 14 to 15 s monitor bins remain distinct.\n')
table(['Within channel and floor','Posterior probability rate below 0.0001'],[[k.replace('|',' at '),num(v['probability_rate_below_1e_minus_4'])] for k,v in r['pooled'].items() if v['family']=='poisson'])

put('## 4. Dependence comparisons\n')
put('Every requested pairwise class contrast is in `dependence-model-01-v3.json:tests`. The following table gives the Binomial contrasts; all Poisson contrasts have zero events in both groups, likelihood ratio zero and p = 1, which does not establish equal rates. No multiplicity correction or clustered sampling model is implied.\n')
table(['Channel','Floor','Split','Classes','Two sided Fisher p'],[[str(t.get('channel',t.get('channels'))),str(t.get('floor',t.get('floors'))),t['dimension'],', '.join(t.get('classes',[])),num(t['p_value'])] for t in d['tests'] if t['test']=='Fisher exact'])
put('The B design contrast compares event rates under different errors and estimators. Its p value does not identify a cause or remove the instruction to predict within each design. Across channels, only F against B is tested. At five combined errors alone, test 10 first boundaries give 0 / 190 and second boundaries 3 / 190; controls give 0 / 570. The 0.3 rad floor and 4 kHz censoring change which of those differences enter F. Sources: `frequency-ledger.json:supplementary_five_se` and the final dependence test.\n')

put('## 5. Model check and historical scorecard\n')
put('For each eligible test and channel, 1,000 draws at the fitted posterior median use that cell’s exposure or trial count. B uses its matching design. A second simulation draws rates from their posteriors. The observed count is treated as a singleton range; the exact match fraction is reported. These are checks against the data used for fitting, not prospective validation.\n')
table(['Channel','Floor','Test','Design model','Observed','Simulated 90 percent count interval','Exact match fraction','Inside'],[
    [x['channel'],x['floor'],x['test'],x['design_model'],x.get('observed'),str(x.get('fixed_median_count_interval_90','not testable')),num(x.get('fraction_equal_observed','not testable')),x.get('observed_inside_fixed_interval','censored')]
    for x in c['cells']])
put('No eligible observed cell lies outside its simulated 5th to 95th percentiles. Test 11 frequency at 4 kHz is explicitly censored and not testable. Stamp pair 2 is unavailable. Source: `model-check-model-01-v3.json`.\n')
put('Sensitivity at the upper rate percentile, and boundary trial counts required for a 90 percent chance of at least three events, follow. These are model outputs, not resource or hardware assurances.\n')
sens=[]
for key,value in c['sensitivity'].items():
    if 'exposure_for_90_percent_one_event_at_rate_q95' in value:
        sens.append([key.replace('|',' at '),'qubit seconds for one event',num(value['exposure_for_90_percent_one_event_at_rate_q95'])])
    else:
        for label,z in value.items():sens.append([key.replace('|',' at ')+' '+label,'trials for three events at low, median, high p',f"{z['trials_for_90_percent_at_least_three_at_q05']}, {z['at_median']}, {z['at_q95']}"])
table(['Model','Target','Required amount'],sens)
put('The four historical outcomes are recomputed below. The original sealed files are not in the bundle; their quoted numbers are in `input/t11/fits-t11.json:counts_of_the_run` and `input/rules/t11-rule.md`. A probability interval cannot be scored by asking whether an observed zero is inside it. Where the quoted count interval is missing, the literal inside or outside question is unavailable. For comparison, the last column uses an explicitly reconstructed Jeffreys predictive count interval from the pre test 11 ledger and the declared trial count. It is not presented as the original sealed interval.\n')
table(['Bet','Quoted probability','Outcome count','Quoted count comparison','Reconstructed 90 percent count interval'],[
    [h['rows'][0]['bet'],'0.008, interval 0.001 to 0.026',0,'Quoted count 0 matches','0 to 0'],
    [h['rows'][1]['bet'],'0.002',0,'Interval absent','0 to 0'],
    [h['rows'][2]['bet'],'0.52, interval 0.35 to 0.69; selected subset 0.91',0,'Interval absent','0 to 2'],
    [h['rows'][3]['bet'],'About 1 in 60',0,'Interval absent','0 to 0']])
put('The named weight occurrence did not happen at 0.10. That outcome lies inside the reconstructed count interval and does not by itself contradict an event probability of 0.52. The own resolution weight event is a changed observable and is not used to rescore the old fixed floor bet. The within frequency design quoted about 186 seconds; actual eligible time is 167.735524 seconds. Sources and both selected and complete population reconstructions are in `historical-scorecard.json`.\n')

put('## 6. Readings, labelled as assistant interpretations\n')
put('The counts contain no within frequency event and no within monitor weight event under the stated rules. This supports small rates over these exposures, but zero is a boundary value outside the continuous Jeffreys posterior’s support and is not established as an exact rate. The own resolution B estimates sit above the fixed 0.10 estimates, especially in the monitor class. The gap class contains an observed monitor weight change, but one trial supplies no separately specified kinetic rate. The stamp probability concerns its composite S definition and does not directly estimate P frame movement.\n')
put('The monitor span means differ and the successive jobs contain a further span mean difference under the same recorded stamp. Within individual spans the measured scatter and fitted slopes do not supply a resolved walk under these calculations. The record therefore supports differing span levels and an across job sequence, without choosing what sets those levels. The shuffled and monitor estimates rest on different assumptions, so the sequence must retain the estimator boundary.\n')
put('Each floor hides a different part of the record. The 4 kHz frequency fit omits censored pairs; the own frequency fit combines thresholds of different sizes. The within weight event rate tests pair changes, while the boundary weight probability tests means over spans. The copies disagreements have no calibrated frequency size. Non line observations and amplitude alternation are features of the one line representation and its exclusions, not an identified mechanism. None of these counts determines a dwell distribution or a distribution of within span weight scatter from the kinetic rates alone.\n')

put('## 7. Future predictions and handoff\n')
put('The future forecasts are in `predictions-model-01-v3.json` and `predictions-model-01-v3.md`, written last from these frozen model outputs. Those files name the channel, design, estimator, eligible exposure and interval for each numerical forecast, and mark quantities that this model cannot predict. The author can hash them before any future run. They are the model’s forecasts, not the author’s or Mantri’s.\n')
put('All source ledgers are preserved in `events-model-01-v3.json`. The split, copies, excluded pairs, alternate populations, kind persistence alternatives and unavailable records remain beside the fitted channels. Scripts and the full input copy permit reproduction. `SHA256SUMS` covers every delivered file except itself.\n')
(ROOT/'report-model-01-v3.md').write_text('\n'.join(out)+'\n')
print('Report written before future predictions')
