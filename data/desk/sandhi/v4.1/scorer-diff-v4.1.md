# Scorer changes for version 4.1

Every source change is listed below with its correction category. Model data added for Part B are separate from these source changes. The internal review wrapper changes presentation labels only and is not part of the prospective scorer.

C1 computes intervals, family cutoffs and count probabilities with the actual design and frozen model state. C2 uses the actual sweep times with a widened donor range and retains calibrated dimensionless comparisons outside it. C3 reads the supplied A26 span weights.

## Existing dependencies

| File | Equal to v4 | SHA256 |
|---|---|---|
| `record_io.py` | True | `89c5b1807fd1deb5b403567eecabd651809a5017a42e2788475245c1db66ac5b` |
| `hmm_model.py` | True | `24f49e97f6b226f6697843b65eeb23522d18816ce2989579f3c02e80856e164b` |
| `hmm_core.c` | True | `b46709c740033e7f14a73174e93f7b706836f3348e1fec9c987ada0819e270a1` |
| `hmm_core.dylib` | True | `70c8f698e67dcc4e2b274fde82459ee5ce3ed5f132161e0a306336eef657529e` |
| `run_boundaries.py` | True | `2f1cf231a66b9105755f5d8d5ad5c489cdd1c0456cf066f4ad6a58bb02a67191` |
| `run_checks.py` | True | `cf7bb72e09b44447d824009a642c76751175b16371084648915d1353d8d73dc5` |

## Scorer replacement blocks

The source is renamed from `score_model_01_v4.py` to `score_model_01_v4_1.py`. The blocks below cover every changed source line. Unchanged context is supplied in the complete diff after them.

### Block 1: C1,C2

```diff
-def applicability(jobs,scenario):
-    differences=[];seconds=[];allocations=scenario.get('row_allocations');schema=scenario.get('circuit_schema')
-    expected_shots=scenario.get('n_shots_per_position');support=scenario.get('sweep_seconds_donor_support',[])
-    if allocations is None or schema is None or expected_shots is None:
-        differences.append({'reason':'The scenario lacks an exact row, circuit or shot specification'})
-    for job in jobs:
-        for index,span in enumerate(job['series']):
-            if allocations is not None and (index>=len(allocations) or list(span['R'])!=allocations[index]):
-                differences.append({'id':span['id'],'field':'R','actual':span['R'],'expected':allocations[index] if index<len(allocations) else None})
-            for ci,circuit in enumerate(span['circuits']):
-                if expected_shots is not None and circuit['shot_count']!=expected_shots:
-                    differences.append({'id':span['id'],'field':'shots','actual':circuit['shot_count'],'expected':expected_shots})
-                if schema is not None:
-                    target=schema[ci] if ci<len(schema) else None
-                    match=target is not None and circuit['quadrature']==target['quadrature'] and circuit.get('wait_us') is not None and abs(circuit['wait_us']-target['wait_us'])<=1e-9
-                    if not match:differences.append({'id':span['id'],'field':'circuit','index':ci,'actual':{'quadrature':circuit['quadrature'],'wait_us':circuit.get('wait_us')},'expected':target})
-            if schema is not None and len(span['circuits'])!=len(schema):
-                differences.append({'id':span['id'],'field':'circuit_count','actual':len(span['circuits']),'expected':len(schema)})
-            inside=any(abs(span['sweep_s']-value)<=1e-12 for value in support)
-            seconds.append({'id':span['id'],'sweep_s':span['sweep_s'],'in_empirical_support':inside,
-                            'inside_empirical_range':bool(support and min(support)<=span['sweep_s']<=max(support))})
-    return {'dimensionless_applicable':not differences,'seconds_applicable':not differences and all(s['in_empirical_support'] for s in seconds),
-            'design_differences':differences,'seconds_support_checks':seconds,
-            'seconds_scope':scenario.get('seconds_scope'),
-            'note':'Outside the modeled design or duration support, raw quantities and interval comparisons remain beside without a calibrated decision'}
-
-
+# C1 and C2 applicability is computed with the actual design in calibration_v4_1.
+
```

### Block 2: C2

```diff
-            family=entry.get('family',quantity)
+            # C2 seconds outside support remain beside; calibrate the dimensionless subfamily.
+            if quantity in ('t15_tau_seconds','model_ell_seconds') and not scenario.get('_applicability',{}).get('seconds_applicable',True):
+                continue
+            family=entry.get('family',quantity)
```

### Block 3: C3

```diff
-'missing_A26':'No implementation or complete definition of A26 is included; no new shuffled weight is calculated'
+'missing_A26':'C3 reads supplied per span A26 weights; no estimator is recomputed'
```

### Block 4: C3

```diff
-            rows.append({'span':s['span'],'quadratures':quadratures,'A26':{'status':'unavailable','reason':result['definitions']['missing_A26']}})
-            add_observation(observations,'shuffled_weight_A26',f'{key} span {s["span"]}',None,reason=result['definitions']['missing_A26'])
-            add_observation(observations,'shuffled_sd',f'{key} span {s["span"]}',None,reason='A26 weight and its population length inputs are needed')
+            from calibration_v4_1 import read_a26
+            a26=read_a26(args.shuffled_fits,key,s['span'])
+            rows.append({'span':s['span'],'duration_s':s['duration_s'],'sweep_s':s['duration_s']/len(next(iter(arr.values()))),'quadratures':quadratures,'A26':a26})
+            add_observation(observations,'shuffled_weight_A26',f'{key} span {s["span"]}',a26.get('value'),reason=a26.get('reason'),source=a26)
+            add_observation(observations,'shuffled_sd',f'{key} span {s["span"]}',None,reason='C3 supplies A26 weight but the v4 definition gives a distribution of population lengths, not one observed scalar; no unique observed sd is defined')
```

### Block 5: C1

```diff
-    scenario_key=str(span_counts[0]) if span_counts and len(set(span_counts))==1 else None
-    scenarios=predictions.get('scenarios',{});scenario=scenarios.get(scenario_key,{})
-    if scenario and len(span_counts)!=scenario.get('n_jobs',2):
-        scenario_key=None;scenario={}
-    result['scenario_applicability']=applicability(result['jobs'],scenario) if scenario else {'dimensionless_applicable':False,'seconds_applicable':False,'reason':'No matching span count scenario'}
-    scenario={**scenario,'_applicability':result['scenario_applicability']}
+    # C1 actual design calibration uses frozen model state and no observed quantities.
+    from calibration_v4_1 import apply_calibration
+    predictions,scenario,calibration=apply_calibration(predictions,result['jobs'],result['shuffled'],args)
+    scenario_key='actual';scenarios=predictions['scenarios']
+    result['calibration']=calibration
+    result['scenario_applicability']=scenario['_applicability']
```

### Block 6: C1,C3

```diff
-    args=p.parse_args()
+    # C1 calibration controls and frozen state; C3 explicitly supplied run fits.
+    p.add_argument('--model-state')
+    p.add_argument('--calibration-cache')
+    p.add_argument('--calibration-seed',type=int,default=41119001)
+    p.add_argument('--calibration-draws',type=int,default=2000)
+    p.add_argument('--calibration-lr-trials',type=int,default=100)
+    p.add_argument('--workers',type=int,default=4)
+    p.add_argument('--shuffled-fits',action='append',default=[],help='C3 key,path to the run fits file')
+    args=p.parse_args()
```

## Complete scorer diff

```diff
--- v4/score_model_01_v4.py
+++ v4.1/score_model_01_v4_1.py
@@ -43,32 +43,7 @@
     return next((n for n in range(1,k+1) if binom.sf(n-1,k,.1)<.05),None)
 
 
-def applicability(jobs,scenario):
-    differences=[];seconds=[];allocations=scenario.get('row_allocations');schema=scenario.get('circuit_schema')
-    expected_shots=scenario.get('n_shots_per_position');support=scenario.get('sweep_seconds_donor_support',[])
-    if allocations is None or schema is None or expected_shots is None:
-        differences.append({'reason':'The scenario lacks an exact row, circuit or shot specification'})
-    for job in jobs:
-        for index,span in enumerate(job['series']):
-            if allocations is not None and (index>=len(allocations) or list(span['R'])!=allocations[index]):
-                differences.append({'id':span['id'],'field':'R','actual':span['R'],'expected':allocations[index] if index<len(allocations) else None})
-            for ci,circuit in enumerate(span['circuits']):
-                if expected_shots is not None and circuit['shot_count']!=expected_shots:
-                    differences.append({'id':span['id'],'field':'shots','actual':circuit['shot_count'],'expected':expected_shots})
-                if schema is not None:
-                    target=schema[ci] if ci<len(schema) else None
-                    match=target is not None and circuit['quadrature']==target['quadrature'] and circuit.get('wait_us') is not None and abs(circuit['wait_us']-target['wait_us'])<=1e-9
-                    if not match:differences.append({'id':span['id'],'field':'circuit','index':ci,'actual':{'quadrature':circuit['quadrature'],'wait_us':circuit.get('wait_us')},'expected':target})
-            if schema is not None and len(span['circuits'])!=len(schema):
-                differences.append({'id':span['id'],'field':'circuit_count','actual':len(span['circuits']),'expected':len(schema)})
-            inside=any(abs(span['sweep_s']-value)<=1e-12 for value in support)
-            seconds.append({'id':span['id'],'sweep_s':span['sweep_s'],'in_empirical_support':inside,
-                            'inside_empirical_range':bool(support and min(support)<=span['sweep_s']<=max(support))})
-    return {'dimensionless_applicable':not differences,'seconds_applicable':not differences and all(s['in_empirical_support'] for s in seconds),
-            'design_differences':differences,'seconds_support_checks':seconds,
-            'seconds_scope':scenario.get('seconds_scope'),
-            'note':'Outside the modeled design or duration support, raw quantities and interval comparisons remain beside without a calibrated decision'}
-
+# C1 and C2 applicability is computed with the actual design in calibration_v4_1.
 
 def score_entries(predictions,observations,scenario):
     rows=[];families=[];buckets={}
@@ -100,6 +75,9 @@
                          'unavailable_units':[x['unit'] for x in scored if x['inside_90'] is None]})
         available=[x for x in scored if x['inside_90'] is not None]
         if scored:
+            # C2 seconds outside support remain beside; calibrate the dimensionless subfamily.
+            if quantity in ('t15_tau_seconds','model_ell_seconds') and not scenario.get('_applicability',{}).get('seconds_applicable',True):
+                continue
             family=entry.get('family',quantity)
             bucket=buckets.setdefault(family,{'observations':[],'quantities':[],'entry_cutoff':None})
             bucket['observations'].extend(scored);bucket['quantities'].append(quantity)
@@ -149,7 +127,7 @@
                            'seconds':'Conditional on returned order being chronological and evenly spaced',
                            't15_tau':'Three sweeps is retained only as a ceiling where the measured lag is below three',
                            'job_boundary':'Two adjacent monitor spans; emissions shared across the compared pair',
-                           'missing_A26':'No implementation or complete definition of A26 is included; no new shuffled weight is calculated'}}
+                           'missing_A26':'C3 reads supplied per span A26 weights; no estimator is recomputed'}}
     result['prediction_scope_note']='Any issued conditional empirical day extension is scored only within its stated assumptions; it is distinct from an unavailable hierarchy only prediction for a new date'
     observations=result['observations'];jobseries=[];dwell_count=0;sharing_failures=[];order_votes=[]
     loaded_jobs=[load_job(spec) for spec in args.job]
@@ -232,9 +210,11 @@
                 pos=[i for i in s['positions'] if rec['labels'][i]['circuit']==quad]
                 M=np.stack([arr[f'p{i:03d}'][:,0] for i in pos]).astype(np.float64)
                 quadratures[quad]={'positions':pos,'reading':record_reading(M,s['duration_s'])}
-            rows.append({'span':s['span'],'quadratures':quadratures,'A26':{'status':'unavailable','reason':result['definitions']['missing_A26']}})
-            add_observation(observations,'shuffled_weight_A26',f'{key} span {s["span"]}',None,reason=result['definitions']['missing_A26'])
-            add_observation(observations,'shuffled_sd',f'{key} span {s["span"]}',None,reason='A26 weight and its population length inputs are needed')
+            from calibration_v4_1 import read_a26
+            a26=read_a26(args.shuffled_fits,key,s['span'])
+            rows.append({'span':s['span'],'duration_s':s['duration_s'],'sweep_s':s['duration_s']/len(next(iter(arr.values()))),'quadratures':quadratures,'A26':a26})
+            add_observation(observations,'shuffled_weight_A26',f'{key} span {s["span"]}',a26.get('value'),reason=a26.get('reason'),source=a26)
+            add_observation(observations,'shuffled_sd',f'{key} span {s["span"]}',None,reason='C3 supplies A26 weight but the v4 definition gives a distribution of population lengths, not one observed scalar; no unique observed sd is defined')
         result['shuffled'].append({'key':key,'source':source,'membership':membership,'spans':rows})
     result['sharing_all_monitor_spans']=not sharing_failures
     result['sharing_spans_counting_against']=sharing_failures
@@ -258,12 +238,12 @@
     add_observation(observations,'returned_order_all_preference','all monitor spans',result['returned_order_all_preference'],
                     reason=None if result['returned_order_all_preference'] is not None else 'The order comparison is not available for every monitor span')
     span_counts=[len(j['series']) for j in result['jobs']]
-    scenario_key=str(span_counts[0]) if span_counts and len(set(span_counts))==1 else None
-    scenarios=predictions.get('scenarios',{});scenario=scenarios.get(scenario_key,{})
-    if scenario and len(span_counts)!=scenario.get('n_jobs',2):
-        scenario_key=None;scenario={}
-    result['scenario_applicability']=applicability(result['jobs'],scenario) if scenario else {'dimensionless_applicable':False,'seconds_applicable':False,'reason':'No matching span count scenario'}
-    scenario={**scenario,'_applicability':result['scenario_applicability']}
+    # C1 actual design calibration uses frozen model state and no observed quantities.
+    from calibration_v4_1 import apply_calibration
+    predictions,scenario,calibration=apply_calibration(predictions,result['jobs'],result['shuffled'],args)
+    scenario_key='actual';scenarios=predictions['scenarios']
+    result['calibration']=calibration
+    result['scenario_applicability']=scenario['_applicability']
     result['prediction_scores'],result['families']=score_entries(predictions,observations,scenario)
     result['unavailable_outcomes']=[{'quantity':quantity,**obs} for quantity,items in observations.items() for obs in items if obs.get('value') is None]
     if args.reference_fits:
@@ -335,6 +315,14 @@
     p.add_argument('--reference-fits',help='Optional archived test 15 fits for a reproduction check only')
     p.add_argument('--bootstrap',type=int,default=400);p.add_argument('--dwell-permutations',type=int,default=2000)
     p.add_argument('--seed',type=int,default=104196401);p.add_argument('--record-only',action='store_true')
+    # C1 calibration controls and frozen state; C3 explicitly supplied run fits.
+    p.add_argument('--model-state')
+    p.add_argument('--calibration-cache')
+    p.add_argument('--calibration-seed',type=int,default=41119001)
+    p.add_argument('--calibration-draws',type=int,default=2000)
+    p.add_argument('--calibration-lr-trials',type=int,default=100)
+    p.add_argument('--workers',type=int,default=4)
+    p.add_argument('--shuffled-fits',action='append',default=[],help='C3 key,path to the run fits file')
     args=p.parse_args()
     if args.bootstrap<1 or args.dwell_permutations<1:raise ValueError('Positive simulation counts required')
     log=Path(__file__).resolve().parent/'data-run.log'
```

## Added calibration dependency

Each line in `calibration_v4_1.py` is an addition. The table gives its exact line number, correction category and text. Shared imports and utilities serve C1. The support function serves C2, and the supplied weight reader serves C3.

| Line | Correction | Source |
|---:|---|---|
| 1 | C1 | <code>"""C1 actual design calibration; C2 actual sweep times; C3 supplied A26 readings."""</code> |
| 2 | C1 | <code>from pathlib import Path</code> |
| 3 | C1 | <code>import copy, hashlib, json, multiprocessing as mp, time</code> |
| 4 | C1 | <code>import numpy as np</code> |
| 5 | C1 | <code>from scipy.special import expit</code> |
| 6 | C1 | <code>from scipy.stats import beta, binom</code> |
| 7 | C1 | <code>from hmm_model import fit_job, simulate_span, derived</code> |
| 8 | C1 | <code>from record_io import native, boundary</code> |
| 9 | C1 | <code># C1 uses the same record estimator as v4.</code> |
| 10 | C1 | <code>from record_io import record_reading</code> |
| 11 | C1 | <code></code> |
| 12 | C1 | <code>FAMILIES={'duty':['threshold_duty','model_duty'],</code> |
| 13 | C1 | <code> 'correlation':['t15_tau_sweeps','t15_tau_seconds','model_ell_sweeps','model_ell_seconds'],</code> |
| 14 | C1 | <code> 'emissions':['q_H_X','q_L_X','q_H_Y','q_L_Y']}</code> |
| 15 | C1 | <code>QUANTITIES=sum(FAMILIES.values(),[])+['job_mean_duty_difference','shuffled_weight_A26','shuffled_sd']</code> |
| 16 | C1 | <code></code> |
| 17 | C1 | <code>def probability(k,n):</code> |
| 18 | C1 | <code>    return {'probability':k/n,'count':int(k),'draws':int(n),'mc_interval_90':[float(beta.ppf(.05,k,n-k+1)) if k else 0.,float(beta.ppf(.95,k+1,n-k)) if k&lt;n else 1.]}</code> |
| 19 | C1 | <code></code> |
| 20 | C1 | <code>def interval(x):</code> |
| 21 | C1 | <code>    a=np.asarray(x,dtype=np.float64);a=a[np.isfinite(a)]</code> |
| 22 | C1 | <code>    return np.quantile(a,[.05,.95]).tolist() if len(a) else None</code> |
| 23 | C1 | <code></code> |
| 24 | C1 | <code>def cutoff(counts,k):</code> |
| 25 | C1 | <code>    n=len(counts);rows=[]</code> |
| 26 | C1 | <code>    for c in range(1,k+1):</code> |
| 27 | C1 | <code>        h=int(np.sum(np.asarray(counts)&gt;=c));upper=float(beta.ppf(.95,h+1,n-h)) if h&lt;n else 1.</code> |
| 28 | C1 | <code>        rows.append({'misses_at_least':c,'estimated_probability':h/n,'one_sided_95_mc_upper':upper})</code> |
| 29 | C1 | <code>    return {'cutoff':next((r['misses_at_least'] for r in rows if r['one_sided_95_mc_upper']&lt;.05),None),</code> |
| 30 | C1 | <code>     'point_probability_cutoff':next((r['misses_at_least'] for r in rows if r['estimated_probability']&lt;.05),None),</code> |
| 31 | C1 | <code>     'k':k,'calibration_draws':n,'tail_table':rows,</code> |
| 32 | C1 | <code>     'independent_binomial_cutoff_beside':next((c for c in range(1,k+1) if binom.sf(c-1,k,.1)&lt;.05),None)}</code> |
| 33 | C1 | <code></code> |
| 34 | C1 | <code>def design_only(jobs,shuffled):</code> |
| 35 | C1 | <code>    """C1 allowlist excludes counts, fitted values, readings and paths."""</code> |
| 36 | C1 | <code>    groups=[]</code> |
| 37 | C1 | <code>    for j in jobs:</code> |
| 38 | C1 | <code>        group=[]</code> |
| 39 | C1 | <code>        for s in j['series']:</code> |
| 40 | C1 | <code>            circuits=[{'quadrature':c['quadrature'],'wait_us':c.get('wait_us'),'shot_count':c['shot_count']} for c in s['circuits']]</code> |
| 41 | C1 | <code>            group.append({'R':list(s['R']),'N':circuits[0]['shot_count'],'circuits':circuits,'sweep_s':s['sweep_s'],</code> |
| 42 | C1 | <code>                          'duration_s':s['duration_s'],'span':s['span']})</code> |
| 43 | C1 | <code>        groups.append(group)</code> |
| 44 | C1 | <code>    return {'jobs':groups,'shuffled':[{'key':j['key'],'spans':[{'span':s['span'],'duration_s':s['duration_s'],'sweep_s':s['sweep_s']} for s in j['spans']]} for j in shuffled]}</code> |
| 45 | C1 | <code></code> |
| 46 | C2 | <code>def support(design,state):</code> |
| 47 | C2 | <code>    donor=state['sweep_seconds_donor_support'];lo=.9*min(donor);hi=1.1*max(donor);width=max(donor)-min(donor)</code> |
| 48 | C2 | <code>    checks=[];diff=[]</code> |
| 49 | C2 | <code>    for ji,g in enumerate(design['jobs']):</code> |
| 50 | C2 | <code>        for si,s in enumerate(g):</code> |
| 51 | C2 | <code>            actual=[(c['quadrature'],c['wait_us']) for c in s['circuits']]</code> |
| 52 | C2 | <code>            if actual!=[('X',5.6),('Y',5.6)] or any(r&lt;=0 for r in s['R']):</code> |
| 53 | C2 | <code>                diff.append({'job':ji,'span':si,'reason':'Emission donor schema is X then Y at 5.6 microseconds with positive rows','actual':actual})</code> |
| 54 | C2 | <code>            checks.append({'job':ji,'span':si,'sweep_s':s['sweep_s'],'in_empirical_support':lo&lt;=s['sweep_s']&lt;=hi,</code> |
| 55 | C2 | <code>                           'inside_empirical_range':min(donor)&lt;=s['sweep_s']&lt;=max(donor),</code> |
| 56 | C2 | <code>                           'inside_range_width_alternative':min(donor)-.1*width&lt;=s['sweep_s']&lt;=max(donor)+.1*width})</code> |
| 57 | C2 | <code>    return {'dimensionless_applicable':not diff,'seconds_applicable':not diff and all(c['in_empirical_support'] for c in checks),</code> |
| 58 | C2 | <code>            'design_differences':diff,'seconds_support_checks':checks,'seconds_range':[lo,hi],</code> |
| 59 | C2 | <code>            'seconds_range_width_alternative':[min(donor)-.1*width,max(donor)+.1*width],</code> |
| 60 | C2 | <code>            'seconds_scope':'C2 actual sweep times within donor endpoint range widened by ten percent',</code> |
| 61 | C2 | <code>            'note':'C1 calibration uses only design quantities. Outside C2 seconds support the dimensionless correlation subfamily remains calibrated.'}</code> |
| 62 | C2 | <code></code> |
| 63 | C1 | <code>_STATE=None;_DESIGN=None;_SEED=None;_LR_DRAWS=None;_LR_TRIALS=None</code> |
| 64 | C1 | <code></code> |
| 65 | C1 | <code>def initialize(state,design,seed,lr_draws,lr_trials):</code> |
| 66 | C1 | <code>    global _STATE,_DESIGN,_SEED,_LR_DRAWS,_LR_TRIALS</code> |
| 67 | C1 | <code>    _STATE=state;_DESIGN=design;_SEED=seed;_LR_DRAWS=lr_draws;_LR_TRIALS=lr_trials</code> |
| 68 | C1 | <code></code> |
| 69 | C1 | <code>def trial(ti):</code> |
| 70 | C1 | <code>    # C1 separate deterministic streams make process scheduling immaterial.</code> |
| 71 | C1 | <code>    rng=np.random.default_rng(np.random.SeedSequence([_SEED,ti]));state=_STATE;design=_DESIGN</code> |
| 72 | C1 | <code>    dates=state['dates'];date=dates[int(rng.integers(len(dates)))];hier=state['hierarchy']['parameters']</code> |
| 73 | C1 | <code>    hb=hier['logit_b']['bootstrap']['samples'][int(rng.integers(len(hier['logit_b']['bootstrap']['samples'])))];hl=hier['log_ell']['bootstrap']['samples'][int(rng.integers(len(hier['log_ell']['bootstrap']['samples'])))];vals={q:[] for q in QUANTITIES}</code> |
| 74 | C1 | <code>    groups=[];read_groups=[];orders=[];failures=[]</code> |
| 75 | C1 | <code>    for ji,template in enumerate(design['jobs']):</code> |
| 76 | C1 | <code>        donors=state['jobs_by_date'][date];donor=donors[int(rng.integers(len(donors)))];boots=state['emission_bootstrap'][donor];em=boots[int(rng.integers(len(boots)))];qH=em['q_H'];qL=em['q_L'];sim=[];rates=[];reads=[]</code> |
| 77 | C1 | <code>        for si,s0 in enumerate(template):</code> |
| 78 | C1 | <code>            b=float(expit(rng.normal(hb['mean_by_day'][date],hb['sigma'])));ell=float(np.exp(rng.normal(hl['mean_by_day'][date],hl['sigma'])));total=float(-np.expm1(-1/ell));rate=derived(b*total,(1-b)*total)</code> |
| 79 | C1 | <code>            s={'id':f'trial{ti}-job{ji+2}-s{si}','job':f'future-job{ji+2}','span':si,'R':s0['R'],'n':np.zeros((len(s0['R']),s0['N']),dtype=np.float64),'record_c':1,'sweep_s':s0['sweep_s'],'duration_s':s0['duration_s']}</code> |
| 80 | C1 | <code>            v=simulate_span(s,rate,qH,qL,rng,with_rows=True);rd=record_reading(v['row_arrays'][1],s['duration_s'],include_means=False);v.pop('row_arrays');v.pop('latent_path');sim.append(v);rates.append([rate['u'],rate['d']]);reads.append(rd)</code> |
| 81 | C1 | <code>            for q,value in [('threshold_duty',rd['duty_b']),('t15_tau_sweeps',rd['tau_c_sweeps_used']),('t15_tau_seconds',rd['tau_c_s'])]:vals[q].append(value)</code> |
| 82 | C1 | <code>        fit=fit_job(sim,q_init=np.array([qL,qH]),rate_init=rates,starts=1,return_series=False)</code> |
| 83 | C1 | <code>        if not fit['success']:failures.append({'trial':ti,'job':ji,'order':'returned','attempts':fit['attempts']})</code> |
| 84 | C1 | <code>        for si,f in enumerate(fit['spans']):</code> |
| 85 | C1 | <code>            vals['model_duty'].append(f['b']);vals['model_ell_sweeps'].append(f['ell']);vals['model_ell_seconds'].append(f['ell']*sim[si]['sweep_s'] if f['ell'] is not None else None)</code> |
| 86 | C1 | <code>        for ci,q in enumerate(('X','Y')):</code> |
| 87 | C1 | <code>            for k in ('q_H','q_L'):vals[k+'_'+q].append(fit[k][ci])</code> |
| 88 | C1 | <code>        if all(s['N']==1000 for s in template):</code> |
| 89 | C1 | <code>            idx=np.column_stack([np.arange(500),np.arange(500,1000)]).ravel()</code> |
| 90 | C1 | <code>            ff=fit_job([{**s,'n':np.asarray(s['n'])[:,idx]} for s in sim],q_init=np.array([qL,qH]),starts=1,return_series=False)</code> |
| 91 | C1 | <code>            if not ff['success']:failures.append({'trial':ti,'job':ji,'order':'interleaved','attempts':ff['attempts']})</code> |
| 92 | C1 | <code>            orders.extend(a['loglik']&gt;b['loglik'] for a,b in zip(fit['spans'],ff['spans']))</code> |
| 93 | C1 | <code>        groups.append(sim);read_groups.append(reads)</code> |
| 94 | C1 | <code>    means=[float(np.mean([r['duty_b'] for r in rr])) for rr in read_groups];vals['job_mean_duty_difference']=[b-a for a,b in zip(means[:-1],means[1:])]</code> |
| 95 | C1 | <code>    # C1 actual shuffled span durations and number of spans; same v4 normal time average definition and 0.011 allowance.</code> |
| 96 | C1 | <code>    for job in design['shuffled']:</code> |
| 97 | C1 | <code>        for s in job['spans']:</code> |
| 98 | C1 | <code>            b=float(expit(rng.normal(hb['mean_by_day'][date],hb['sigma'])));ell=float(np.exp(rng.normal(hl['mean_by_day'][date],hl['sigma'])))</code> |
| 99 | C1 | <code>            dt=float(rng.choice([s['sweep_s'] for g in design['jobs'] for s in g]));sd=float(np.sqrt(2*b*(1-b)*ell*dt/s['duration_s']))</code> |
| 100 | C1 | <code>            vals['shuffled_sd'].append(sd);vals['shuffled_weight_A26'].append(float(np.clip(rng.normal(b,sd),0,1)))</code> |
| 101 | C1 | <code>    words=[boundary(a,b)['word'] for rr in read_groups for a,b in zip(rr[:-1],rr[1:])]</code> |
| 102 | C1 | <code>    lr=[]</code> |
| 103 | C1 | <code>    if ti&lt;_LR_TRIALS:</code> |
| 104 | C1 | <code>        from run_boundaries import boundary_test_spans,boundary_test_job_pair</code> |
| 105 | C1 | <code>        for ji,g in enumerate(groups):</code> |
| 106 | C1 | <code>            for si,(a,b) in enumerate(zip(g[:-1],g[1:])):</code> |
| 107 | C1 | <code>                r=boundary_test_spans([a,b],draws=_LR_DRAWS,seed=_SEED+1000000+ti*10000+ji*100+si,interval_draws=0)</code> |
| 108 | C1 | <code>                lr.append({'key':f'within_job{ji+2}_span{si}_span{si+1}','p':r.get('p_bootstrap'),'failures':r.get('failures',[]),'fit_success':r.get('fit_success')})</code> |
| 109 | C1 | <code>        for ji,(a,b) in enumerate(zip(groups[:-1],groups[1:])):</code> |
| 110 | C1 | <code>            r=boundary_test_job_pair([a,b],draws=_LR_DRAWS,seed=_SEED+2000000+ti*10000+ji,interval_draws=0)</code> |
| 111 | C1 | <code>            lr.append({'key':f'between_job{ji+2}_job{ji+3}','p':r.get('p_bootstrap'),'failures':r.get('failures',[]),'fit_success':r.get('fit_success')})</code> |
| 112 | C1 | <code>    return {'trial':ti,'donor_date':date,'values':vals,'all_shared':all(r['word_of_the_ratio']=='SHARED' for rr in read_groups for r in rr),'boundary_words':words,</code> |
| 113 | C1 | <code>            'boundary_counts':{w:words.count(w) for w in ('NO CHANGE','BETWEEN','CHANGE','NOT READ')},'returned_preference_all':all(orders) if orders else None,'lr':lr,'failures':failures}</code> |
| 114 | C1 | <code></code> |
| 115 | C1 | <code>def calibrate(state,design,seed=41119001,draws=2000,lr_trials=100,lr_draws=400,workers=4):</code> |
| 116 | C1 | <code>    start=time.monotonic();sup=support(design,state)</code> |
| 117 | C1 | <code>    if not sup['dimensionless_applicable']:raise ValueError(sup['design_differences'])</code> |
| 118 | C1 | <code>    if draws&lt;2 or draws%2:raise ValueError('Even positive draw count required')</code> |
| 119 | C1 | <code>    with mp.get_context('spawn').Pool(workers,initializer=initialize,initargs=(state,design,seed,lr_draws,lr_trials)) as pool:</code> |
| 120 | C1 | <code>        trials=[]</code> |
| 121 | C1 | <code>        for t in pool.imap_unordered(trial,range(draws),chunksize=1):</code> |
| 122 | C1 | <code>            trials.append(t)</code> |
| 123 | C1 | <code>            if len(trials)%100==0:print('C1 calibration',len(trials),'of',draws,'elapsed',round(time.monotonic()-start,1),flush=True)</code> |
| 124 | C1 | <code>    trials.sort(key=lambda t:t['trial']);half=draws//2</code> |
| 125 | C1 | <code>    ints={q:interval([x for t in trials[:half] for x in t['values'][q]]) for q in QUANTITIES}</code> |
| 126 | C1 | <code>    if ints['shuffled_weight_A26']:ints['shuffled_weight_A26']=[max(0,ints['shuffled_weight_A26'][0]-.011),min(1,ints['shuffled_weight_A26'][1]+.011)]</code> |
| 127 | C1 | <code>    families={}</code> |
| 128 | C1 | <code>    for fam,qs0 in FAMILIES.items():</code> |
| 129 | C1 | <code>        qs=[q for q in qs0 if sup['seconds_applicable'] or 'seconds' not in q]</code> |
| 130 | C1 | <code>        k=sum(len(trials[0]['values'][q]) for q in qs)</code> |
| 131 | C1 | <code>        misses=[sum(x is None or not ints[q][0]&lt;=x&lt;=ints[q][1] for q in qs for x in t['values'][q]) for t in trials[half:]]</code> |
| 132 | C1 | <code>        families[fam]=cutoff(misses,k)&#124;{'quantities':qs,'seconds_included':sup['seconds_applicable']}</code> |
| 133 | C1 | <code>    keys=[f'within_job{ji+2}_span{si}_span{si+1}' for ji,g in enumerate(design['jobs']) for si in range(len(g)-1)]</code> |
| 134 | C1 | <code>    boundary_probs={k:probability(sum(t['boundary_words'][i]=='CHANGE' for t in trials),draws) for i,k in enumerate(keys)}</code> |
| 135 | C1 | <code>    lrtr=[t for t in trials if t['lr']];lrok=[t for t in lrtr if all(x['p'] is not None and not x['failures'] for x in t['lr'])]</code> |
| 136 | C1 | <code>    lrp=probability(sum(any(x['p']&lt;.01 for x in t['lr']) for t in lrok),len(lrok)) if lrok else None</code> |
| 137 | C1 | <code>    if lrp:lrp.update({'null_draws_per_comparison':lr_draws,'requested_trials':lr_trials,'complete_trials':len(lrok),'per_boundary':{k:probability(sum(next(x['p'] for x in t['lr'] if x['key']==k)&lt;.01 for t in lrok),len(lrok)) for k in [x['key'] for x in lrok[0]['lr']]}})</code> |
| 138 | C1 | <code>    counts=[len(g) for g in design['jobs']]</code> |
| 139 | C1 | <code>    s={'n_spans_per_job':counts[0] if len(set(counts))==1 else None,'span_counts':counts,'n_jobs':len(counts),'scope':'conditional_empirical_day_extension_with_actual_design',</code> |
| 140 | C1 | <code>       'design':design,'_applicability':sup,'draws':draws,'interval_training_draws':half,'joint_calibration_draws':half,'seed':seed,'rng':'PCG64 SeedSequence([seed,trial])',</code> |
| 141 | C1 | <code>       'intervals':ints,'family_miss_thresholds':families,'sharing_all_probability':probability(sum(t['all_shared'] for t in trials),draws),</code> |
| 142 | C1 | <code>       'boundary_counts':{w:{'expected_count':float(np.mean([t['boundary_counts'][w] for t in trials])),'interval_90':interval([t['boundary_counts'][w] for t in trials])} for w in ('NO CHANGE','BETWEEN','CHANGE','NOT READ')},</code> |
| 143 | C1 | <code>       'boundary_change_probabilities':boundary_probs,'any_LR_reject_probability':lrp,</code> |
| 144 | C1 | <code>       'returned_order_all_preference_probability':probability(sum(t['returned_preference_all'] for t in trials),draws) if all(t['returned_preference_all'] is not None for t in trials) else None,</code> |
| 145 | C1 | <code>       'failures':[f for t in trials for f in t['failures']],'elapsed_seconds':time.monotonic()-start,</code> |
| 146 | C1 | <code>       'seconds_scope':sup['seconds_scope'],'assumptions':'Frozen v4 empirical day and emission extension with C1 actual design and C2 actual sweep times.'}</code> |
| 147 | C1 | <code>    return native({'scenario':s,'trials':trials})</code> |
| 148 | C1 | <code></code> |
| 149 | C3 | <code>def read_a26(specs,key,span):</code> |
| 150 | C3 | <code>    # C3 supplied observations only, no estimator reconstruction.</code> |
| 151 | C3 | <code>    for spec in specs:</code> |
| 152 | C3 | <code>        name,path=spec.split(',',1)</code> |
| 153 | C3 | <code>        if name!=key:continue</code> |
| 154 | C3 | <code>        obj=json.loads(Path(path).read_text());found=[]</code> |
| 155 | C3 | <code>        def walk(x,route):</code> |
| 156 | C3 | <code>            if isinstance(x,dict):</code> |
| 157 | C3 | <code>                if 'span_readings_A26' in x:</code> |
| 158 | C3 | <code>                    rows=x['span_readings_A26'].get('weight_per_span',[])</code> |
| 159 | C3 | <code>                    found.extend((r,route+'.span_readings_A26.weight_per_span') for r in rows if r['span']==span)</code> |
| 160 | C3 | <code>                for k,v in x.items():walk(v,route+'.'+k)</code> |
| 161 | C3 | <code>            elif isinstance(x,list):</code> |
| 162 | C3 | <code>                for i,v in enumerate(x):walk(v,route+f'[{i}]')</code> |
| 163 | C3 | <code>        walk(obj,'$')</code> |
| 164 | C3 | <code>        if len(found)!=1:return {'status':'unavailable','reason':'Expected one matching supplied A26 span reading','matches':len(found)}</code> |
| 165 | C3 | <code>        row,field=found[0];return {'status':'available','value':row['weighted_mean'],'source':str(Path(path).resolve()),'sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest(),'field':field,'span':span}</code> |
| 166 | C3 | <code>    return {'status':'unavailable','reason':'No run fits supplied for this shuffled job'}</code> |
| 167 | C3 | <code></code> |
| 168 | C1 | <code>def apply_calibration(predictions,jobs,shuffled,args):</code> |
| 169 | C1 | <code>    state_path=Path(args.model_state or Path(args.predictions).parent/'calibration-state.json')</code> |
| 170 | C1 | <code>    state=json.loads(state_path.read_text());design=design_only(jobs,shuffled)</code> |
| 171 | C1 | <code>    payload={'state_sha256':hashlib.sha256(state_path.read_bytes()).hexdigest(),'design':design,'seed':args.calibration_seed,'draws':args.calibration_draws,'lr_trials':args.calibration_lr_trials,'lr_draws':args.bootstrap,</code> |
| 172 | C1 | <code>             'calibrator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}</code> |
| 173 | C1 | <code>    token=hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest();cache=Path(args.calibration_cache or Path(args.out).with_suffix('.calibration.json'))</code> |
| 174 | C1 | <code>    if cache.exists():</code> |
| 175 | C1 | <code>        result=json.loads(cache.read_text())</code> |
| 176 | C1 | <code>        if result.get('cache_key')!=token:raise ValueError('Calibration cache does not match frozen state, design, seed or code')</code> |
| 177 | C1 | <code>    else:</code> |
| 178 | C1 | <code>        result=calibrate(state,design,args.calibration_seed,args.calibration_draws,args.calibration_lr_trials,args.bootstrap,args.workers)</code> |
| 179 | C1 | <code>        result.update({'cache_key':token,'inputs':payload});cache.write_text(json.dumps(result,separators=(',',':'),allow_nan=False))</code> |
| 180 | C1 | <code>    scenario=result['scenario'];entries=[]</code> |
| 181 | C1 | <code>    for q,inter in scenario['intervals'].items():</code> |
| 182 | C1 | <code>        if inter is None:continue</code> |
| 183 | C1 | <code>        fam=next((f for f,qs in FAMILIES.items() if q in qs),q)</code> |
| 184 | C1 | <code>        entries.append({'id':'actual_design_'+q,'quantity':q,'interval_90':inter,'class':'Frozen empirical day extension under actual design','prediction_scope':scenario['scope'],'family':fam,'status':'issued'})</code> |
| 185 | C1 | <code>    return {**predictions,'entries':entries,'scenarios':{'actual':scenario}},scenario,{'state_sha256':payload['state_sha256'],'cache_key':token,'calibration_file':str(cache.resolve()),'design':design,'failures':scenario['failures'],'seed':args.calibration_seed}</code> |

The calibration state contains the empirical date means, hierarchy bootstrap samples and emission bootstrap samples required by C1. The Part A state is derived solely from hashed v4 files. The prospective state is the Part B refit. Neither source adds a middle span channel.
