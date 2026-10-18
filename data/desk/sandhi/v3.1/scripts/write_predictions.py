"""Final scientific generation step. Consume frozen rates; do not revise any fit."""
from pathlib import Path
import sys,json,hashlib,math,gzip,datetime
sys.path.insert(0,str(Path(__file__).resolve().parent))
import numpy as np
from scipy import special,stats
from statistics_core import predict
ROOT=Path(__file__).resolve().parents[1]
def load(n):return json.loads((ROOT/n).read_text())
R=load('rates-model-01-v3.json');N=load('normalized-trials.json')['rows'];M=load('monitor11-ledger.json');S=load('shuffled-stamp-ledger.json')
SEED=310018; DRAWS=100000
rng=np.random.default_rng(SEED)
frozen=['events-model-01-v3.json','rates-model-01-v3.json','dependence-model-01-v3.json',
        'model-check-model-01-v3.json','estimators-model-01-v3.json','report-model-01-v3.md','historical-scorecard.json',
        'normalized-trials.json','monitor11-ledger.json','shuffled-stamp-ledger.json','scripts/write_predictions.py','scripts/statistics_core.py']
hashes={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in frozen}
P={'kind':'Model predictions for a future unobserved run','written_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
   'source_hashes':hashes,'seed':SEED,'draws_for_joint_parameter_interval':DRAWS,
   'interval_conventions':'Parameter probability intervals are transformations of posterior 5th and 95th percentiles. Count intervals integrate over the parameter posterior.',
   'B_prediction_rule':'Each B prediction uses its matching design posterior. No pooled B prediction is made.',
   'third_day':{},'scan_monitor':{},'even_odds':{},'counterconditions':[]}
third=P['third_day']
for design,trials in [('shuffled',2),('monitor',4)]:
    third['weight_boundaries_'+design]={'channel':'B','floor':'own','design':design,'estimator':design,
        'rate_path':'classes.B|own.design.'+design,**predict(R['classes']['B|own']['design'][design],trials=trials)}
    third['weight_boundaries_'+design+'_fixed_beside']={'channel':'B','floor':'fixed0.10','design':design,'estimator':design,
        'rate_path':'classes.B|fixed0.10.design.'+design,**predict(R['classes']['B|fixed0.10']['design'][design],trials=trials)}
third['weight_within']={'channel':'W_B','floor':'max 0.10 and five combined errors','design':'monitor','estimator':'monitor',
    'rate_path':'pooled.W_B|fixed0.10',**predict(R['pooled']['W_B|fixed0.10'],exposure=170.)}
third['frequency_boundaries']={'channel':'F','floor':'each record own threshold','design':'monitor','estimator':'phase',
    'rate_path':'pooled.F|own','pooling_reason':'The design contrasts do not distinguish the observed frequency counts',
    'transfer_limit':'The fitted own floor pools unequal thresholds. This is not an independently calibrated rate for a universal 23 kHz floor.',
    **predict(R['pooled']['F|own'],trials=4)}
third['frequency_within']={'channel':'W','floor':'each record own threshold','design':'monitor','estimator':'phase',
    'rate_path':'pooled.W|own',**predict(R['pooled']['W|own'],exposure=170.)}
a=R['pooled']['F|own']['posterior']['alpha'];b=R['pooled']['F|own']['posterior']['beta']
shape=R['pooled']['W|own']['posterior']['shape'];rate=R['pooled']['W|own']['posterior']['rate']
ps=rng.beta(a,b,DRAWS);ls=rng.gamma(shape,1/rate,DRAWS)
joint=-np.expm1(4*np.log1p(-ps)-170*ls)
no_event_integral=math.exp(special.betaln(a,b+4)-special.betaln(a,b))*(rate/(rate+170))**shape
third['any_frequency_boundary_or_within']={'channels':['F','W'],'boundary_trials':4,'within_exposure_s':170.,
    'probability_at_median_rates':float(-np.expm1(4*np.log1p(-R['pooled']['F|own']['median'])-170*R['pooled']['W|own']['median'])),
    'probability_posterior_median':float(np.median(joint)),
    'probability_parameter_interval_90':list(map(float,np.quantile(joint,[.05,.95]))),
    'posterior_predictive_probability_at_least_one':float(1-no_event_integral),
    'assumption':'Conditional independence of the channels, with the own floor transfer caveat'}
third['monitor_only_frequency_sensitivity']={'boundary':predict(R['classes']['F|own']['design']['monitor'],trials=4),
    'within':predict(R['classes']['W|own']['design']['monitor'],exposure=170.),'status':'Design posterior beside the pooled forecast'}
third['between_monitor_jobs_weight']={'status':'Not identified by the specified model','channel':'gap class reported separately',
    'observed_events':1,'observed_trials':1,'estimator':'monitor',
    'reason':'No gap probability is one of the fitted channels. B is per span boundary and cannot be substituted for a gap trial.',
    'source':'monitor11-ledger.json:trials channel B_gap'}
third['within_span_scatter']={'status':'No scatter distribution is specified by the kinetic rates',
    'reading':'Observed scatter and slopes are descriptive. A no event Poisson rate does not imply a Gaussian noise model.',
    'conditional_noise_only_reading':[{'job':x['job'],'span':x['span'],'n':x['n_repeats'],
        'sqrt_expected_sample_variance_noise_scale_if_recorded_independent_errors_recur':x['conditional_expected_sd_from_propagated_errors'],
        'chi2_per_dof_reference_mean_under_extra_equal_variance_gaussian_approximation':1.,
        'chi2_per_dof_interval_90_under_extra_equal_variance_gaussian_approximation':list(map(float,stats.chi2.ppf([.05,.95],x['dof'])/x['dof'])),
        'observed_chi2_per_dof':x['chi2_per_dof']} for x in M['per_span']],
    'reference_caveat':'The reported noise scale is the square root of expected sample variance, not the expected sample standard deviation. Chi squared about an arithmetic mean uses an equal variance Gaussian approximation because the recorded errors are slightly unequal.',
    'extra_assumption_is_fitted_kinetic_prediction':False,'source':'monitor11-ledger.json:per_span'}
third['stamp_composite']={'channel':'S','observable':'S detuning moves by at least 4 kHz or the verdict kind changes',
    'rate_path':'pooled.S|4kHz',**predict(R['pooled']['S|4kHz'],trials=1),
    'P_frame_probability_status':'Not separately identified. The composite S probability is not a probability for P Delta0 alone.'}
split=next(x for x in S['split_observable'] if x['eligible'])
third['split_near_44p7']={'status':'Reading only; no fitted probability','requested_band_kHz':[44.2,45.2],
    'eligible_crossings':1,'recorded_change_kHz':split['change_kHz'],
    'observed_values_kHz':[split['delta_before_kHz'],split['delta_after_kHz']],
    'reason':'One eligible crossing does not identify a between stamp split spread or a sampling law.',
    'source':'shuffled-stamp-ledger.json:split_observable'}

t10=json.loads(gzip.decompress((ROOT/'input/t10/fits-t10.json.gz').read_bytes()))
qset=set(map(int,t10['jobs']['1']['qubits']))
P['scan_monitor']['set_S']={'qubits':sorted(qset),'n_qubits':len(qset),'source':'input/t10/fits-t10.json.gz:jobs.1.qubits'}
P['scan_monitor']['floor']='4 kHz; eligible observations only'
P['scan_monitor']['rate_choice']='Pooled F and W are primary because the specified design contrasts do not distinguish the counts. Design specific sensitivity is beside.'
for design,test,job in [('scan',9,2),('monitor',10,1)]:
    observed=[x for x in N if x['test']==test and x['job']==job and x['qubit'] in qset and x['floor']=='4kHz' and x['pool']=='main' and x['included']]
    boundaries=[x for x in observed if x['channel']=='F'];within=[x for x in observed if x['channel']=='W']
    exp=sum(x['exposure_s'] for x in within)
    P['scan_monitor'][design]={'design':design,'source_template':{'test':test,'job':job},
        'template_boundary_trials':len(boundaries),'template_within_exposure_s':exp,
        'source_template_qubits_present':sorted({x['qubit'] for x in N if x['test']==test and x['job']==job}),
        'scenario':'Reuse the source eligible mask and exposure on the common qubits. Future errors may change eligibility.',
        'boundary':predict(R['pooled']['F|4kHz'],trials=len(boundaries)),
        'within':predict(R['pooled']['W|4kHz'],exposure=exp),
        'design_specific_boundary_beside':predict(R['classes']['F|4kHz']['design'][design],trials=len(boundaries)),
        'all_set_S_boundaries_eligible_scenario':predict(R['pooled']['F|4kHz'],trials=2*len(qset)),
        'bridge_rule':'Last whole repeat before the provider boundary and first whole repeat after; straddles excluded'}
for key in ['W|4kHz','W|own','W_B|fixed0.10','W_B|own']:
    v=R['pooled'][key]; a=v['posterior']['shape']; b=v['posterior']['rate']
    P['even_odds'][key]={'unit':'qubit seconds','at_posterior_median_rate':math.log(2)/v['median'],
        'parameter_interval_90':[math.log(2)/v['q95'],math.log(2)/v['q05']],
        'posterior_predictive_even_odds_time':b*(2**(1/a)-1),
        'rate_path':'pooled.'+key,
        'distinction':'The parameter transformed time and the integrated posterior predictive time answer different questions.'}
next_pairs=1000;period=M['summary']['W_B']['exposure_own_s']/M['summary']['W_B']['trials']
P['counterconditions'].append({'channel':'W_B','rule':'Any within span weight event in the next 1000 eligible monitor pairs at the specified max 0.10 and five error floor',
    'declared_pairs':next_pairs,'period_s_from_this_record':period,'exposure_s':period*next_pairs,
    'prediction':predict(R['pooled']['W_B|fixed0.10'],exposure=period*next_pairs),
    'standing':'This is the kickoff chosen countercondition. It is stricter than simply falling outside the posterior predictive interval.'})
P['counterconditions'].append({'channel':'split','rule':'An absolute split change above 1 kHz across a stamp on a qubit confirmed as two lines on both records',
    'standing':'A stated future countercondition, not a consequence of a fitted split rate'})
P['counterconditions'].append({'channels':['W','F','B','S'],'rule':'Counts outside the declared posterior predictive intervals in either direction count against the corresponding model transfer',
    'interval_sources':['third_day','scan_monitor'],'minimum_eligible_exposure_required':True,
    'frequency_extra':{'declared_uncensored_qubit_seconds':10000.,**predict(R['pooled']['W|4kHz'],exposure=10000.)}})
P['counterconditions'].append({'channel':'W','rule':'If enough within events accumulate, a dwell distribution inconsistent with the exponential assumption counts against the Poisson model',
    'current_status':'No observed dwell distribution can be fitted from zero within events'})
(ROOT/'predictions-model-01-v3.json').write_text(json.dumps(P,indent=2,allow_nan=False)+'\n')

lines=['# Model 01 future predictions, version 3, run 3.1','',
    'These are model outputs for a future run, written after the report and rates. The JSON records the source file hashes, assumptions, trial counts and calculation paths. No earlier run output supplied an input.','',
    "The predictions are the model's, written before the run they predict, and they are what can prove it wrong.",'',
    'Probability intervals and predictive count intervals answer different questions. The table uses the probability at the posterior median rate, its 90 percent parameter interval, and the count interval integrated over the parameter posterior.','',
    '| Forecast | Channel and estimator | Probability of at least one | Probability interval | Predictive count interval |',
    '|---|---|---|---|---|']
for key,label in [('weight_boundaries_shuffled','Two shuffled weight boundaries'),('weight_boundaries_monitor','Four monitor weight boundaries'),
                  ('weight_within','Within monitor weight over 170 seconds'),('frequency_boundaries','Four monitor frequency boundaries'),
                  ('frequency_within','Within monitor frequency over 170 seconds'),('stamp_composite','One composite stamp crossing')]:
    v=third[key];ci=v['probability_at_least_one_parameter_interval_90'];counts=v['posterior_predictive_count_interval_90']
    lines.append(f"| {label} | {v['channel']}, {v.get('estimator','S detuning or kind')} | {v['probability_at_least_one_at_median']:.6g} | {ci[0]:.6g} to {ci[1]:.6g} | {counts[0]} to {counts[1]} |")
joint=third['any_frequency_boundary_or_within']
lines+=['',f"For any frequency event across those four boundaries or 170 seconds within spans, the probability at the median rates is {joint['probability_at_median_rates']:.6g}; the joint posterior probability interval is {joint['probability_parameter_interval_90'][0]:.6g} to {joint['probability_parameter_interval_90'][1]:.6g}. The integrated predictive probability is {joint['posterior_predictive_probability_at_least_one']:.6g}. This uses the stated channel independence.",'',
    'Every weight boundary forecast uses the posterior for its own design and estimator. The fixed 0.10 forecasts remain beside in JSON. The frequency forecast uses the own floor pooled rate, with a monitor only sensitivity beside. The archived monitor thresholds are about 18 to 23 kHz, with individual pair variation. A fitted rate across unequal own floors is not a calibrated universal 23 kHz rate.','',
    'A probability for the weight change between monitor jobs is unavailable: the requested five channel model has no fitted gap probability. The observed gap is one event in one trial and remains separate. Substituting a boundary probability would change its referent.','',
    'The kinetic rate does not predict within span scatter. JSON supplies the recorded scatter and a conditional calculation from the recorded errors if independent Gaussian errors recur. That additional noise assumption is explicitly a reading. The observed chi squared per degree of freedom spans 0.462 to 0.597. The reference mean of 1 uses an equal variance Gaussian approximation; the recorded errors differ slightly. The reported noise scale is the square root of expected sample variance, not an expectation of sample standard deviation.','',
    'The stamp row predicts an S detuning change of at least 4 kHz or a kind change. It does not identify the probability that the P frame moves. Only one eligible split crossing is available, with a change of about −0.118 kHz; no probability is assigned to staying within 0.5 kHz of 44.7. This is a reading only.','',
    'For scan and monitor back to back on set S, the source mask scenarios follow. The future provider spans and errors decide actual eligibility. The all eligible scenario has two boundaries for each of the 68 qubits and is also saved in JSON.','',
    '| Design | Eligible boundary trials in source mask | Expected count | Predictive count interval | Eligible within exposure, seconds |',
    '|---|---|---|---|---|']
for design in ['scan','monitor']:
    v=P['scan_monitor'][design];b=v['boundary'];ci=b['posterior_predictive_count_interval_90']
    lines.append(f"| {design} | {v['template_boundary_trials']} | {b['expected_count_posterior_mean']:.6g} | {ci[0]} to {ci[1]} | {v['template_within_exposure_s']:.6g} |")
lines+=['','Even odds time is reported in qubit seconds. The first time transforms the median rate. The separate integrated time averages uncertainty in that rate.','',
    '| Channel and floor | Time at median rate | 90 percent parameter time interval | Integrated predictive even odds time |','|---|---|---|---|']
for key,v in P['even_odds'].items():
    ci=v['parameter_interval_90'];lines.append(f"| {key.replace('|',' at ')} | {v['at_posterior_median_rate']:.6g} | {ci[0]:.6g} to {ci[1]:.6g} | {v['posterior_predictive_even_odds_time']:.6g} |")
lines+=['','For each declared trial count, a count outside its saved predictive interval in either direction counts against the associated transfer. The kickoff also names any within weight event in the next 1,000 eligible monitor pairs at the fixed floor, and a split change above 1 kHz across a stamp on a qubit confirmed on both sides. The first is stricter than a generic predictive interval test; its actual interval and probability are saved in JSON. A nonexponential dwell distribution could count against the Poisson assumption if events accumulate.','',
    'These forecasts require eligible records. A censored observation is not scored as a zero event. The author can hash these files before the future run.']
(ROOT/'predictions-model-01-v3.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({'weight_shuffled':third['weight_boundaries_shuffled']['probability_at_least_one_at_median'],
                  'weight_monitor':third['weight_boundaries_monitor']['probability_at_least_one_at_median'],
                  'weight_within':third['weight_within']['probability_at_least_one_at_median'],
                  'scan_mask':P['scan_monitor']['scan']['template_boundary_trials'],'monitor_mask':P['scan_monitor']['monitor']['template_boundary_trials']},indent=2))
