"""Fit only the normalized ledger of this run. Predictions are a separate final step."""
from pathlib import Path
import sys,json,itertools,math
sys.path.insert(0,str(Path(__file__).resolve().parent))
import numpy as np
from scipy import stats
from statistics_core import fit,lrt_poisson,fisher,min_trials_three

ROOT=Path(__file__).resolve().parents[1]
ROWS=json.loads((ROOT/'normalized-trials.json').read_text())['rows']
SEED=310017
RNG=np.random.default_rng(SEED)
DRAWS=1000

def dump(name,data):
    (ROOT/name).write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')

def family(channel): return 'poisson' if channel in ('W','W_B') else 'binomial'

def eligible(channel,floor):
    return [r for r in ROWS if r['channel']==channel and r['floor']==floor and r['included'] and r['pool']=='main']

rate_groups={}
for r in ROWS:
    if r['pool']=='main': rate_groups[(r['channel'],r['floor'])]=None
rate_groups=dict(sorted(rate_groups.items()))
RATES={'kind':'Model output','priors':{'poisson':'Gamma shape one half and rate zero','binomial':'Beta one half and one half'},
       'quantiles':[.05,.5,.95],'primary_weight_prediction_rule':'Match design; pooled weight posterior is descriptive only',
       'pooled':{},'classes':{},'separate_gap_classes':{}}
DEP={'kind':'Computed tests conditional on trial definitions','tests':[],
     'caution':'Trials can share a qubit and a job. These simple tests do not establish independence or equal rates.'}
dimensions={'W':['design','stamp','test'], 'W_B':['job','span'],
            'F':['design','boundary','gap_bin','stamp'],
            'B':['design','processor_record','boundary','gap_bin'], 'S':['stamp_pair']}
for (channel,floor) in rate_groups:
    key=channel+'|'+floor; rows=eligible(channel,floor)
    fam=family(channel)
    RATES['pooled'][key]=fit(rows,fam)
    classes={}
    for dim in dimensions[channel]:
        labels=sorted({str(r.get(dim,'not applicable')) for r in rows})
        partitions={label:[r for r in rows if str(r.get(dim,'not applicable'))==label] for label in labels}
        classes[dim]={label:fit(g,fam) for label,g in partitions.items()}
        for a,b in itertools.combinations(labels,2):
            result=lrt_poisson([partitions[a],partitions[b]]) if fam=='poisson' else fisher(partitions[a],partitions[b])
            DEP['tests'].append({'channel':channel,'floor':floor,'dimension':dim,'classes':[a,b],
                                 'test':'Poisson likelihood ratio' if fam=='poisson' else 'Fisher exact',**result})
    RATES['classes'][key]=classes
for ca,fa,cb,fb in [('F','4kHz','B','fixed0.10'),('F','own','B','own')]:
    DEP['tests'].append({'channels':[ca,cb],'floors':[fa,fb],'test':'Fisher exact','dimension':'across channels',
                         **fisher(eligible(ca,fa),eligible(cb,fb)),
                         'interpretation':'Different observables and selected eligible populations; association does not identify a mechanism'})
for channel,floor in sorted({(r['channel'],r['floor']) for r in ROWS if r['pool']=='gap'}):
    group=[r for r in ROWS if r['channel']==channel and r['floor']==floor and r['pool']=='gap' and r['included']]
    RATES['separate_gap_classes'][channel+'|'+floor]={'events':sum(int(r['event']) for r in group),'trials':len(group),
        'row_ids':[r['id'] for r in group], 'status':'Reported separately and not fitted into a boundary probability'}
    RATES['separate_gap_classes'][channel+'|'+floor]['by_test']={str(test):{
        'events':sum(int(r['event']) for r in group if r['test']==test),
        'trials':sum(r['test']==test for r in group),
        'gaps_s':sorted({r['gap_s'] for r in group if r['test']==test})} for test in sorted({r['test'] for r in group})}

# Extra t10 test uses five combined errors without the 0.3 rad floor.
extra=json.loads((ROOT/'frequency-ledger.json').read_text()).get('supplementary_five_se',{})
DEP['test10_five_se_source']=extra
extra_rows=extra.get('rows',[])
first=[{'event':r['event_5_se_only']} for r in extra_rows if r['kind']=='boundary' and r['boundary_or_span']==1]
second=[{'event':r['event_5_se_only']} for r in extra_rows if r['kind']=='boundary' and r['boundary_or_span']==2]
DEP['tests'].append({'channel':'F','floor':'five SE only','dimension':'test10 boundary ordinal',
    'classes':['first','second'],'test':'Fisher exact',**fisher(first,second)})
t10_f4=[x for x in eligible('F','4kHz') if x['test']==10]
DEP['tests'].append({'channel':'F','floor':'4kHz','dimension':'test10 boundary ordinal',
    'classes':['first','second'],'test':'Fisher exact',
    **fisher([x for x in t10_f4 if x['boundary']==1],[x for x in t10_f4 if x['boundary']==2])})

CHECK={'kind':'Model output conditional on the same data used for fitting','seed':SEED,'draws_per_cell':DRAWS,
       'simulation_convention':'Fixed posterior median primary; posterior predictive simulation beside',
       'range_convention':'Exact observed count is a singleton range. Every simulation uses the exposure and trials of the observed cell.',
       'cells':[],'sensitivity':{},'historical_scorecard_source':'historical-scorecard.json'}
for channel,floor in rate_groups:
    key=channel+'|'+floor; rows=eligible(channel,floor); fam=family(channel)
    tests=sorted({r['test'] for r in ROWS if r['channel']==channel and r['floor']==floor and r['pool']=='main'})
    for test in tests:
        # Each B design has its own prediction model even when shown within one test.
        design_labels=sorted({r['design'] for r in rows if r['test']==test}) if channel=='B' else ['pooled']
        for design in design_labels:
            cell=[r for r in rows if r['test']==test and (design=='pooled' or r['design']==design)]
            rate=RATES['classes'][key]['design'][design] if channel=='B' else RATES['pooled'][key]
            observed=sum(int(r['event']) for r in cell)
            exposure=float(sum(r['exposure_s'] for r in cell)); n=len(cell)
            if n==0:
                CHECK['cells'].append({'channel':channel,'floor':floor,'test':test,'design_model':design,
                    'trials':0,'exposure_s':0.,'observed':None,'status':'Censored; no eligible trial. Not testable.'})
                continue
            if fam=='poisson':
                fixed=RNG.poisson(rate['median']*exposure,DRAWS)
                p=rate['posterior']; sampled=RNG.gamma(p['shape'],1/p['rate'],DRAWS)
                pp=RNG.poisson(sampled*exposure)
            else:
                fixed=RNG.binomial(n,rate['median'],DRAWS)
                p=rate['posterior']; sampled=RNG.beta(p['alpha'],p['beta'],DRAWS)
                pp=RNG.binomial(n,sampled)
            interval=list(map(int,np.quantile(fixed,[.05,.95],method='inverted_cdf')))
            pp_interval=list(map(int,np.quantile(pp,[.05,.95],method='inverted_cdf')))
            CHECK['cells'].append({'channel':channel,'floor':floor,'test':test,'design_model':design,
                'trials':n,'exposure_s':exposure,'observed':observed,'fixed_median_count_interval_90':interval,
                'observed_inside_fixed_interval':interval[0]<=observed<=interval[1],
                'fraction_equal_observed':float(np.mean(fixed==observed)),
                'posterior_predictive_count_interval_90':pp_interval,
                'observed_inside_posterior_predictive_interval':pp_interval[0]<=observed<=pp_interval[1],
                'fixed_counts':fixed.tolist(),'posterior_predictive_counts':pp.tolist()})
    rate=RATES['pooled'][key]
    if fam=='poisson' and 'posterior' in rate:
        CHECK['sensitivity'][key]={'exposure_for_90_percent_one_event_at_rate_q95':-math.log(.1)/rate['q95'],
                                  'unit':'qubit seconds'}
    elif 'posterior' in rate:
        targets={'pooled':rate}
        if channel=='B':targets.update(RATES['classes'][key]['design'])
        CHECK['sensitivity'][key]={label:{'trials_for_90_percent_at_least_three_at_q05':min_trials_three(v['q05']),
                'at_median':min_trials_three(v['median']),'at_q95':min_trials_three(v['q95'])} for label,v in targets.items()}
CHECK['cells_not_described_at_fixed_median']=[{k:v for k,v in c.items() if k not in ('fixed_counts','posterior_predictive_counts')} for c in CHECK['cells'] if c.get('observed_inside_fixed_interval') is False]
CHECK['unavailable_stamp_pair2']={'status':'Not testable under the S definition','source':'shuffled-stamp-ledger.json:stamp_pair2_unavailable',
    'reason':'A phase at one wait lacks an identified common absolute frequency reference and a mapped kind.'}
dump('rates-model-01-v3.json',RATES)
dump('dependence-model-01-v3.json',DEP)
dump('model-check-model-01-v3.json',CHECK)
print(json.dumps({k:{q:v[q] for q in ('events','trials','exposure_s','q05','median','q95') if q in v} for k,v in RATES['pooled'].items()},indent=2))
