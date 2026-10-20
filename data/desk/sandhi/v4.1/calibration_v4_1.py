"""C1 actual design calibration; C2 actual sweep times; C3 supplied A26 readings."""
from pathlib import Path
import copy, hashlib, json, multiprocessing as mp, time
import numpy as np
from scipy.special import expit
from scipy.stats import beta, binom
from hmm_model import fit_job, simulate_span, derived
from record_io import native, boundary
# C1 uses the same record estimator as v4.
from record_io import record_reading

FAMILIES={'duty':['threshold_duty','model_duty'],
 'correlation':['t15_tau_sweeps','t15_tau_seconds','model_ell_sweeps','model_ell_seconds'],
 'emissions':['q_H_X','q_L_X','q_H_Y','q_L_Y']}
QUANTITIES=sum(FAMILIES.values(),[])+['job_mean_duty_difference','shuffled_weight_A26','shuffled_sd']

def probability(k,n):
    return {'probability':k/n,'count':int(k),'draws':int(n),'mc_interval_90':[float(beta.ppf(.05,k,n-k+1)) if k else 0.,float(beta.ppf(.95,k+1,n-k)) if k<n else 1.]}

def interval(x):
    a=np.asarray(x,dtype=np.float64);a=a[np.isfinite(a)]
    return np.quantile(a,[.05,.95]).tolist() if len(a) else None

def cutoff(counts,k):
    n=len(counts);rows=[]
    for c in range(1,k+1):
        h=int(np.sum(np.asarray(counts)>=c));upper=float(beta.ppf(.95,h+1,n-h)) if h<n else 1.
        rows.append({'misses_at_least':c,'estimated_probability':h/n,'one_sided_95_mc_upper':upper})
    return {'cutoff':next((r['misses_at_least'] for r in rows if r['one_sided_95_mc_upper']<.05),None),
     'point_probability_cutoff':next((r['misses_at_least'] for r in rows if r['estimated_probability']<.05),None),
     'k':k,'calibration_draws':n,'tail_table':rows,
     'independent_binomial_cutoff_beside':next((c for c in range(1,k+1) if binom.sf(c-1,k,.1)<.05),None)}

def design_only(jobs,shuffled):
    """C1 allowlist excludes counts, fitted values, readings and paths."""
    groups=[]
    for j in jobs:
        group=[]
        for s in j['series']:
            circuits=[{'quadrature':c['quadrature'],'wait_us':c.get('wait_us'),'shot_count':c['shot_count']} for c in s['circuits']]
            group.append({'R':list(s['R']),'N':circuits[0]['shot_count'],'circuits':circuits,'sweep_s':s['sweep_s'],
                          'duration_s':s['duration_s'],'span':s['span']})
        groups.append(group)
    return {'jobs':groups,'shuffled':[{'key':j['key'],'spans':[{'span':s['span'],'duration_s':s['duration_s'],'sweep_s':s['sweep_s']} for s in j['spans']]} for j in shuffled]}

def support(design,state):
    donor=state['sweep_seconds_donor_support'];lo=.9*min(donor);hi=1.1*max(donor);width=max(donor)-min(donor)
    checks=[];diff=[]
    for ji,g in enumerate(design['jobs']):
        for si,s in enumerate(g):
            actual=[(c['quadrature'],c['wait_us']) for c in s['circuits']]
            if actual!=[('X',5.6),('Y',5.6)] or any(r<=0 for r in s['R']):
                diff.append({'job':ji,'span':si,'reason':'Emission donor schema is X then Y at 5.6 microseconds with positive rows','actual':actual})
            checks.append({'job':ji,'span':si,'sweep_s':s['sweep_s'],'in_empirical_support':lo<=s['sweep_s']<=hi,
                           'inside_empirical_range':min(donor)<=s['sweep_s']<=max(donor),
                           'inside_range_width_alternative':min(donor)-.1*width<=s['sweep_s']<=max(donor)+.1*width})
    return {'dimensionless_applicable':not diff,'seconds_applicable':not diff and all(c['in_empirical_support'] for c in checks),
            'design_differences':diff,'seconds_support_checks':checks,'seconds_range':[lo,hi],
            'seconds_range_width_alternative':[min(donor)-.1*width,max(donor)+.1*width],
            'seconds_scope':'C2 actual sweep times within donor endpoint range widened by ten percent',
            'note':'C1 calibration uses only design quantities. Outside C2 seconds support the dimensionless correlation subfamily remains calibrated.'}

_STATE=None;_DESIGN=None;_SEED=None;_LR_DRAWS=None;_LR_TRIALS=None

def initialize(state,design,seed,lr_draws,lr_trials):
    global _STATE,_DESIGN,_SEED,_LR_DRAWS,_LR_TRIALS
    _STATE=state;_DESIGN=design;_SEED=seed;_LR_DRAWS=lr_draws;_LR_TRIALS=lr_trials

def trial(ti):
    # C1 separate deterministic streams make process scheduling immaterial.
    rng=np.random.default_rng(np.random.SeedSequence([_SEED,ti]));state=_STATE;design=_DESIGN
    dates=state['dates'];date=dates[int(rng.integers(len(dates)))];hier=state['hierarchy']['parameters']
    hb=hier['logit_b']['bootstrap']['samples'][int(rng.integers(len(hier['logit_b']['bootstrap']['samples'])))];hl=hier['log_ell']['bootstrap']['samples'][int(rng.integers(len(hier['log_ell']['bootstrap']['samples'])))];vals={q:[] for q in QUANTITIES}
    groups=[];read_groups=[];orders=[];failures=[]
    for ji,template in enumerate(design['jobs']):
        donors=state['jobs_by_date'][date];donor=donors[int(rng.integers(len(donors)))];boots=state['emission_bootstrap'][donor];em=boots[int(rng.integers(len(boots)))];qH=em['q_H'];qL=em['q_L'];sim=[];rates=[];reads=[]
        for si,s0 in enumerate(template):
            b=float(expit(rng.normal(hb['mean_by_day'][date],hb['sigma'])));ell=float(np.exp(rng.normal(hl['mean_by_day'][date],hl['sigma'])));total=float(-np.expm1(-1/ell));rate=derived(b*total,(1-b)*total)
            s={'id':f'trial{ti}-job{ji+2}-s{si}','job':f'future-job{ji+2}','span':si,'R':s0['R'],'n':np.zeros((len(s0['R']),s0['N']),dtype=np.float64),'record_c':1,'sweep_s':s0['sweep_s'],'duration_s':s0['duration_s']}
            v=simulate_span(s,rate,qH,qL,rng,with_rows=True);rd=record_reading(v['row_arrays'][1],s['duration_s'],include_means=False);v.pop('row_arrays');v.pop('latent_path');sim.append(v);rates.append([rate['u'],rate['d']]);reads.append(rd)
            for q,value in [('threshold_duty',rd['duty_b']),('t15_tau_sweeps',rd['tau_c_sweeps_used']),('t15_tau_seconds',rd['tau_c_s'])]:vals[q].append(value)
        fit=fit_job(sim,q_init=np.array([qL,qH]),rate_init=rates,starts=1,return_series=False)
        if not fit['success']:failures.append({'trial':ti,'job':ji,'order':'returned','attempts':fit['attempts']})
        for si,f in enumerate(fit['spans']):
            vals['model_duty'].append(f['b']);vals['model_ell_sweeps'].append(f['ell']);vals['model_ell_seconds'].append(f['ell']*sim[si]['sweep_s'] if f['ell'] is not None else None)
        for ci,q in enumerate(('X','Y')):
            for k in ('q_H','q_L'):vals[k+'_'+q].append(fit[k][ci])
        if all(s['N']==1000 for s in template):
            idx=np.column_stack([np.arange(500),np.arange(500,1000)]).ravel()
            ff=fit_job([{**s,'n':np.asarray(s['n'])[:,idx]} for s in sim],q_init=np.array([qL,qH]),starts=1,return_series=False)
            if not ff['success']:failures.append({'trial':ti,'job':ji,'order':'interleaved','attempts':ff['attempts']})
            orders.extend(a['loglik']>b['loglik'] for a,b in zip(fit['spans'],ff['spans']))
        groups.append(sim);read_groups.append(reads)
    means=[float(np.mean([r['duty_b'] for r in rr])) for rr in read_groups];vals['job_mean_duty_difference']=[b-a for a,b in zip(means[:-1],means[1:])]
    # C1 actual shuffled span durations and number of spans; same v4 normal time average definition and 0.011 allowance.
    for job in design['shuffled']:
        for s in job['spans']:
            b=float(expit(rng.normal(hb['mean_by_day'][date],hb['sigma'])));ell=float(np.exp(rng.normal(hl['mean_by_day'][date],hl['sigma'])))
            dt=float(rng.choice([s['sweep_s'] for g in design['jobs'] for s in g]));sd=float(np.sqrt(2*b*(1-b)*ell*dt/s['duration_s']))
            vals['shuffled_sd'].append(sd);vals['shuffled_weight_A26'].append(float(np.clip(rng.normal(b,sd),0,1)))
    words=[boundary(a,b)['word'] for rr in read_groups for a,b in zip(rr[:-1],rr[1:])]
    lr=[]
    if ti<_LR_TRIALS:
        from run_boundaries import boundary_test_spans,boundary_test_job_pair
        for ji,g in enumerate(groups):
            for si,(a,b) in enumerate(zip(g[:-1],g[1:])):
                r=boundary_test_spans([a,b],draws=_LR_DRAWS,seed=_SEED+1000000+ti*10000+ji*100+si,interval_draws=0)
                lr.append({'key':f'within_job{ji+2}_span{si}_span{si+1}','p':r.get('p_bootstrap'),'failures':r.get('failures',[]),'fit_success':r.get('fit_success')})
        for ji,(a,b) in enumerate(zip(groups[:-1],groups[1:])):
            r=boundary_test_job_pair([a,b],draws=_LR_DRAWS,seed=_SEED+2000000+ti*10000+ji,interval_draws=0)
            lr.append({'key':f'between_job{ji+2}_job{ji+3}','p':r.get('p_bootstrap'),'failures':r.get('failures',[]),'fit_success':r.get('fit_success')})
    return {'trial':ti,'donor_date':date,'values':vals,'all_shared':all(r['word_of_the_ratio']=='SHARED' for rr in read_groups for r in rr),'boundary_words':words,
            'boundary_counts':{w:words.count(w) for w in ('NO CHANGE','BETWEEN','CHANGE','NOT READ')},'returned_preference_all':all(orders) if orders else None,'lr':lr,'failures':failures}

def calibrate(state,design,seed=41119001,draws=2000,lr_trials=100,lr_draws=400,workers=4):
    start=time.monotonic();sup=support(design,state)
    if not sup['dimensionless_applicable']:raise ValueError(sup['design_differences'])
    if draws<2 or draws%2:raise ValueError('Even positive draw count required')
    with mp.get_context('spawn').Pool(workers,initializer=initialize,initargs=(state,design,seed,lr_draws,lr_trials)) as pool:
        trials=[]
        for t in pool.imap_unordered(trial,range(draws),chunksize=1):
            trials.append(t)
            if len(trials)%100==0:print('C1 calibration',len(trials),'of',draws,'elapsed',round(time.monotonic()-start,1),flush=True)
    trials.sort(key=lambda t:t['trial']);half=draws//2
    ints={q:interval([x for t in trials[:half] for x in t['values'][q]]) for q in QUANTITIES}
    if ints['shuffled_weight_A26']:ints['shuffled_weight_A26']=[max(0,ints['shuffled_weight_A26'][0]-.011),min(1,ints['shuffled_weight_A26'][1]+.011)]
    families={}
    for fam,qs0 in FAMILIES.items():
        qs=[q for q in qs0 if sup['seconds_applicable'] or 'seconds' not in q]
        k=sum(len(trials[0]['values'][q]) for q in qs)
        misses=[sum(x is None or not ints[q][0]<=x<=ints[q][1] for q in qs for x in t['values'][q]) for t in trials[half:]]
        families[fam]=cutoff(misses,k)|{'quantities':qs,'seconds_included':sup['seconds_applicable']}
    keys=[f'within_job{ji+2}_span{si}_span{si+1}' for ji,g in enumerate(design['jobs']) for si in range(len(g)-1)]
    boundary_probs={k:probability(sum(t['boundary_words'][i]=='CHANGE' for t in trials),draws) for i,k in enumerate(keys)}
    lrtr=[t for t in trials if t['lr']];lrok=[t for t in lrtr if all(x['p'] is not None and not x['failures'] for x in t['lr'])]
    lrp=probability(sum(any(x['p']<.01 for x in t['lr']) for t in lrok),len(lrok)) if lrok else None
    if lrp:lrp.update({'null_draws_per_comparison':lr_draws,'requested_trials':lr_trials,'complete_trials':len(lrok),'per_boundary':{k:probability(sum(next(x['p'] for x in t['lr'] if x['key']==k)<.01 for t in lrok),len(lrok)) for k in [x['key'] for x in lrok[0]['lr']]}})
    counts=[len(g) for g in design['jobs']]
    s={'n_spans_per_job':counts[0] if len(set(counts))==1 else None,'span_counts':counts,'n_jobs':len(counts),'scope':'conditional_empirical_day_extension_with_actual_design',
       'design':design,'_applicability':sup,'draws':draws,'interval_training_draws':half,'joint_calibration_draws':half,'seed':seed,'rng':'PCG64 SeedSequence([seed,trial])',
       'intervals':ints,'family_miss_thresholds':families,'sharing_all_probability':probability(sum(t['all_shared'] for t in trials),draws),
       'boundary_counts':{w:{'expected_count':float(np.mean([t['boundary_counts'][w] for t in trials])),'interval_90':interval([t['boundary_counts'][w] for t in trials])} for w in ('NO CHANGE','BETWEEN','CHANGE','NOT READ')},
       'boundary_change_probabilities':boundary_probs,'any_LR_reject_probability':lrp,
       'returned_order_all_preference_probability':probability(sum(t['returned_preference_all'] for t in trials),draws) if all(t['returned_preference_all'] is not None for t in trials) else None,
       'failures':[f for t in trials for f in t['failures']],'elapsed_seconds':time.monotonic()-start,
       'seconds_scope':sup['seconds_scope'],'assumptions':'Frozen v4 empirical day and emission extension with C1 actual design and C2 actual sweep times.'}
    return native({'scenario':s,'trials':trials})

def read_a26(specs,key,span):
    # C3 supplied observations only, no estimator reconstruction.
    for spec in specs:
        name,path=spec.split(',',1)
        if name!=key:continue
        obj=json.loads(Path(path).read_text());found=[]
        def walk(x,route):
            if isinstance(x,dict):
                if 'span_readings_A26' in x:
                    rows=x['span_readings_A26'].get('weight_per_span',[])
                    found.extend((r,route+'.span_readings_A26.weight_per_span') for r in rows if r['span']==span)
                for k,v in x.items():walk(v,route+'.'+k)
            elif isinstance(x,list):
                for i,v in enumerate(x):walk(v,route+f'[{i}]')
        walk(obj,'$')
        if len(found)!=1:return {'status':'unavailable','reason':'Expected one matching supplied A26 span reading','matches':len(found)}
        row,field=found[0];return {'status':'available','value':row['weighted_mean'],'source':str(Path(path).resolve()),'sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest(),'field':field,'span':span}
    return {'status':'unavailable','reason':'No run fits supplied for this shuffled job'}

def apply_calibration(predictions,jobs,shuffled,args):
    state_path=Path(args.model_state or Path(args.predictions).parent/'calibration-state.json')
    state=json.loads(state_path.read_text());design=design_only(jobs,shuffled)
    payload={'state_sha256':hashlib.sha256(state_path.read_bytes()).hexdigest(),'design':design,'seed':args.calibration_seed,'draws':args.calibration_draws,'lr_trials':args.calibration_lr_trials,'lr_draws':args.bootstrap,
             'calibrator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    token=hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest();cache=Path(args.calibration_cache or Path(args.out).with_suffix('.calibration.json'))
    if cache.exists():
        result=json.loads(cache.read_text())
        if result.get('cache_key')!=token:raise ValueError('Calibration cache does not match frozen state, design, seed or code')
    else:
        result=calibrate(state,design,args.calibration_seed,args.calibration_draws,args.calibration_lr_trials,args.bootstrap,args.workers)
        result.update({'cache_key':token,'inputs':payload});cache.write_text(json.dumps(result,separators=(',',':'),allow_nan=False))
    scenario=result['scenario'];entries=[]
    for q,inter in scenario['intervals'].items():
        if inter is None:continue
        fam=next((f for f,qs in FAMILIES.items() if q in qs),q)
        entries.append({'id':'actual_design_'+q,'quantity':q,'interval_90':inter,'class':'Frozen empirical day extension under actual design','prediction_scope':scenario['scope'],'family':fam,'status':'issued'})
    return {**predictions,'entries':entries,'scenarios':{'actual':scenario}},scenario,{'state_sha256':payload['state_sha256'],'cache_key':token,'calibration_file':str(cache.resolve()),'design':design,'failures':scenario['failures'],'seed':args.calibration_seed}
