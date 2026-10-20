#!/usr/bin/env python3
"""Score future arrays using the frozen definitions of Model 01 v4.

Example:
  python score_model_01_v4.py --job day3-job2,shots2.npz,meta2.json,counts2.json \
    --job day3-job3,shots3.npz,meta3.json,counts3.json \
    --shuffled day3-job1,shots1.npz,meta1.json,counts1.json \
    --predictions predictions-model-01-v4.json --out scorecard.json

The program reads no network resource. Its only records are its arguments.
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import argparse
import datetime
import math
import platform
import numpy as np
import scipy
from scipy.stats import binom
from record_io import sha,jload,save,read_arrays,counts_check,monitor_series,record_reading,meta_spans,boundary,native


def load_job(spec):
    parts=spec.split(',')
    if len(parts)!=4:raise ValueError('Job argument requires key,array,meta,counts')
    key,ap,mp,cp=parts
    arr=read_arrays(ap);meta=jload(mp);rec=jload(cp)
    check=counts_check(arr,rec)
    if not check['pass_check']:raise ValueError(f'Counts do not agree for {key}')
    source={'job':key,'array':str(Path(ap).resolve()),'array_sha256':sha(ap),'meta':str(Path(mp).resolve()),'meta_sha256':sha(mp),'counts':str(Path(cp).resolve()),'counts_sha256':sha(cp),'counts_check':check}
    return key,arr,meta,rec,source


def calibrated_boundary(spans,draws,seed):
    from run_boundaries import boundary_test_spans
    return boundary_test_spans(spans,draws=draws,seed=seed,interval_draws=0)


def family_cutoff(k):
    return next((n for n in range(1,k+1) if binom.sf(n-1,k,.1)<.05),None)


# C1 and C2 applicability is computed with the actual design in calibration_v4_1.

def score_entries(predictions,observations,scenario):
    rows=[];families=[];buckets={}
    for entry in predictions.get('entries',[]):
        quantity=entry.get('quantity');interval=entry.get('interval_90');matches=observations.get(quantity)
        out={'id':entry.get('id'),'quantity':quantity,'class':entry.get('class'),'interval_90':interval,
             'prediction_scope':entry.get('prediction_scope')}
        if entry.get('status') not in (None,'issued','computed','available'):
            rows.append(out|{'status':'not scored','reason':entry.get('reason',entry.get('status'))});continue
        if entry.get('spans_per_job') is not None and entry['spans_per_job'] != scenario.get('n_spans_per_job'):
            rows.append(out|{'status':'not applicable to observed span count','spans_per_job':entry['spans_per_job']});continue
        if matches is None:
            rows.append(out|{'status':'not scored','reason':'Quantity has no scoring definition in this scorer'});continue
        scored=[]
        for obs in matches:
            value=obs.get('value')
            available=value is not None and interval is not None and len(interval)==2
            support=scenario.get('_applicability',{})
            applicable=support.get('dimensionless_applicable',True)
            if quantity in ('t15_tau_seconds','model_ell_seconds','shuffled_sd'):
                applicable=applicable and support.get('seconds_applicable',True)
            valid=available and applicable
            scored.append(obs|{'inside_90':bool(interval[0]<=value<=interval[1]) if valid else None,
                               'uncalibrated_inside_90_beside':bool(interval[0]<=value<=interval[1]) if available and not applicable else None,
                               'status':'scored' if valid else 'unavailable',
                               'reason':obs.get('reason') if applicable else 'Observed design or duration lies outside the modeled support'})
        rows.append(out|{'status':'computed','observations':scored,'expected_bets':len(scored),
                         'scored_bets':sum(x['inside_90'] is not None for x in scored),
                         'unavailable_units':[x['unit'] for x in scored if x['inside_90'] is None]})
        available=[x for x in scored if x['inside_90'] is not None]
        if scored:
            # C2 seconds outside support remain beside; calibrate the dimensionless subfamily.
            if quantity in ('t15_tau_seconds','model_ell_seconds') and not scenario.get('_applicability',{}).get('seconds_applicable',True):
                continue
            family=entry.get('family',quantity)
            bucket=buckets.setdefault(family,{'observations':[],'quantities':[],'entry_cutoff':None})
            bucket['observations'].extend(scored);bucket['quantities'].append(quantity)
            if entry.get('miss_count_against') is not None:bucket['entry_cutoff']=entry['miss_count_against']
    for family,bucket in buckets.items():
        all_obs=bucket['observations'];available=[x for x in all_obs if x['inside_90'] is not None]
        k=len(available);misses=sum(not x['inside_90'] for x in available)
        calibration=scenario.get('family_miss_thresholds',{}).get(family,bucket['entry_cutoff'])
        cutoff=calibration.get('cutoff') if isinstance(calibration,dict) else calibration
        calibrated=calibration is not None
        expected_k=calibration.get('k',len(all_obs)) if isinstance(calibration,dict) else len(all_obs)
        complete=k==len(all_obs) and k==expected_k
        missing=[{'unit':x['unit'],'reason':x.get('reason','Quantity or its interval unavailable')} for x in all_obs if x['inside_90'] is None]
        families.append({'family':family,'quantities':bucket['quantities'],'bets_scored':k,'misses':misses,
                         'expected_bets':expected_k,'observed_bets':len(all_obs),'unavailable_outcomes':missing,
                         'smallest_miss_count_under_0p05':cutoff,
                         'counts_against':(misses>=cutoff if cutoff is not None else False) if calibrated and complete else None,
                         'status':'scored' if calibrated and complete else 'not fully testable',
                         'reason':None if calibrated and complete else 'Missing outcome or scenario family size differs' if not complete else 'Model family calibration was not supplied',
                         'cutoff_source':'Model simulation in supplied predictions' if calibrated else 'Model family calibration was not supplied',
                         'calibration':calibration,'independent_binomial_cutoff_beside':family_cutoff(k)})
    return rows,families


def add_observation(observations,quantity,unit,value,**extra):
    observations.setdefault(quantity,[]).append({'unit':unit,'value':value,**extra})


def fit_status(fit):
    if fit is None:return {'status':'unavailable','success':False,'reason':'Model fit was not run','attempts':[]}
    success=fit.get('success') is True
    return {'status':'converged' if success else 'unavailable','success':success,
            'reason':None if success else 'Model fit did not report successful numerical convergence',
            'gradient_max':fit.get('gradient_max'),'attempts':fit.get('attempts',[])}


def score(args):
    from hmm_model import fit_job
    from run_checks import dwell_check
    predictions=jload(args.predictions) if args.predictions else {}
    result={'schema':'model01_v4_scorecard_1','computed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'prediction_file':str(Path(args.predictions).resolve()) if args.predictions else None,'prediction_sha256':sha(args.predictions) if args.predictions else None,
            'versions':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__},
            'seed':args.seed,'bootstrap_draws':args.bootstrap,'record_only':args.record_only,
            'jobs':[],'boundaries':[],'between_jobs':[],'shuffled':[],'observations':{},
            'definitions':{'H':'Higher emission in the recorded quadrature',
                           'seconds':'Conditional on returned order being chronological and evenly spaced',
                           't15_tau':'Three sweeps is retained only as a ceiling where the measured lag is below three',
                           'job_boundary':'Two adjacent monitor spans; emissions shared across the compared pair',
                           'missing_A26':'C3 reads supplied per span A26 weights; no estimator is recomputed'}}
    result['prediction_scope_note']='Any issued conditional empirical day extension is scored only within its stated assumptions; it is distinct from an unavailable hierarchy only prediction for a new date'
    observations=result['observations'];jobseries=[];dwell_count=0;sharing_failures=[];order_votes=[]
    loaded_jobs=[load_job(spec) for spec in args.job]
    loaded_jobs.sort(key=lambda x:meta_spans(x[2],x[3])[0][0]['start_utc'])
    if len({job[3]['job_id'] for job in loaded_jobs})!=len(loaded_jobs):
        raise ValueError('The same monitor job was supplied more than once')
    result['job_order_source']='Ascending start of the first execution span'
    for ji,(key,arr,meta,rec,source) in enumerate(loaded_jobs):
        spans,membership=monitor_series(arr,rec,meta,key,qubits=[143])
        if not spans:raise ValueError('No monitor spans could be formed')
        fit=fit_job(spans) if not args.record_only else None
        order_fit=None
        if fit and all(len(s['n'][0])==1000 for s in spans):
            order=np.column_stack([np.arange(500),np.arange(500,1000)]).ravel()
            order_fit=fit_job([{**s,'n':np.asarray(s['n'])[:,order]} for s in spans])
        status=fit_status(fit);order_status=fit_status(order_fit)
        jr={'key':key,'source':source,'membership':membership,'series':spans,'fit':fit,
            'fit_status':status,'interleaved_fit_status':order_status,'dwell_checks':[],'order':[]}
        jobseries.append(spans)
        for si,s in enumerate(spans):
            rd=s['t15'];unit=s['id']
            add_observation(observations,'threshold_duty',unit,rd['duty_b'])
            add_observation(observations,'t15_tau_sweeps',unit,rd['tau_c_sweeps_used'],ceiling=rd['tau_c_ceiling'])
            add_observation(observations,'t15_tau_seconds',unit,rd['tau_c_s'],ceiling=rd['tau_c_ceiling'])
            add_observation(observations,'sharing_ratio',unit,rd['ratio'],word=rd['word_of_the_ratio'])
            if rd['word_of_the_ratio']!='SHARED':sharing_failures.append(unit)
            if status['success']:
                sf=fit['spans'][si]
                add_observation(observations,'model_duty',unit,sf['b'])
                ell_reason=sf.get('ell_status') if sf['ell'] is None else None
                add_observation(observations,'model_ell_sweeps',unit,sf['ell'],reason=ell_reason)
                add_observation(observations,'model_ell_seconds',unit,sf['ell']*s['sweep_s'] if sf['ell'] is not None else None,reason=ell_reason)
                dc=dwell_check(sf['path'],sf['u'],sf['d'],args.seed+1000+ji*100+si,args.dwell_permutations)
                jr['dwell_checks'].append({'id':unit,**dc});dwell_count+=int(dc['under_0p01'] is True)
            else:
                for quantity in ('model_duty','model_ell_sweeps','model_ell_seconds'):
                    add_observation(observations,quantity,unit,None,reason=status['reason'])
                jr['dwell_checks'].append({'id':unit,'status':'unavailable','reason':status['reason'],'under_0p01':None})
            order_valid=status['success'] and order_status['success']
            llr=fit['spans'][si]['loglik'] if fit else None
            lli=order_fit['spans'][si]['loglik'] if order_fit else None
            delta=llr-lli if llr is not None and lli is not None else None
            if order_valid:order_votes.append(delta>0)
            jr['order'].append({'id':unit,'returned_loglik':llr,'interleaved_loglik':lli,
                                'returned_minus_interleaved':delta if order_valid else None,
                                'unconverged_difference_beside':delta if not order_valid else None,
                                'status':'scored' if order_valid else 'unavailable',
                                'reason':None if order_valid else status['reason'] or order_status['reason'],
                                'estimator':'Emissions shared across all spans of this job in both orders'})
        for i,c in enumerate(spans[0]['circuits']):
            for state in ['H','L']:
                add_observation(observations,f'q_{state}_{c["quadrature"]}',key,
                                fit[f'q_{state}'][i] if status['success'] else None,
                                circuit_index=i,wait=c['wait'],reason=status['reason'])
        for bi,(a,b) in enumerate(zip(spans[:-1],spans[1:])):
            br={'job':key,'spans':[a['span'],b['span']],
                'boundary_key':f'within_job{ji+2}_span{bi}_span{bi+1}','test15':boundary(a,b)}
            if not args.record_only:br['likelihood_ratio']=calibrated_boundary([a,b],args.bootstrap,args.seed+10000+1000*ji+bi)
            result['boundaries'].append(br)
        result['jobs'].append(jr)
    for ji,(left,right) in enumerate(zip(result['jobs'][:-1],result['jobs'][1:])):
        aa=left['series'];bb=right['series'];ba=float(np.mean([s['t15']['duty_b'] for s in aa]));bd=float(np.mean([s['t15']['duty_b'] for s in bb]))
        sd_a=math.sqrt(sum((s['t15']['telegraph_sd'] or 0)**2 for s in aa))/len(aa);sd_b=math.sqrt(sum((s['t15']['telegraph_sd'] or 0)**2 for s in bb))/len(bb)
        available=all(s['t15']['telegraph_sd'] is not None for s in aa+bb);sd=math.hypot(sd_a,sd_b);z=abs(bd-ba)/sd if available and sd else None
        br={'jobs':[left['key'],right['key']],'job_mean_threshold_duties':[ba,bd],'difference':bd-ba,'combined_sd':sd if available else None,
            'ratio':z,'word':('NO CHANGE' if z<=2 else 'BETWEEN' if z<=3 else 'CHANGE') if z is not None else 'NOT READ'}
        add_observation(observations,'job_mean_duty_difference',f'{left["key"]} to {right["key"]}',bd-ba)
        if not args.record_only:
            try:
                from run_boundaries import boundary_test_job_pair
                br['likelihood_ratio']=boundary_test_job_pair([aa,bb],draws=args.bootstrap,seed=args.seed+50000+ji,interval_draws=0)
            except ImportError:
                br['likelihood_ratio']={'status':'unavailable','reason':'Between job likelihood implementation is not available in this package'}
        result['between_jobs'].append(br)
    for spec in args.shuffled:
        key,arr,meta,rec,source=load_job(spec);spans,membership=meta_spans(meta,rec);rows=[]
        for s in spans:
            quadratures={}
            for quad in ['X','Y']:
                pos=[i for i in s['positions'] if rec['labels'][i]['circuit']==quad]
                M=np.stack([arr[f'p{i:03d}'][:,0] for i in pos]).astype(np.float64)
                quadratures[quad]={'positions':pos,'reading':record_reading(M,s['duration_s'])}
            from calibration_v4_1 import read_a26
            a26=read_a26(args.shuffled_fits,key,s['span'])
            rows.append({'span':s['span'],'duration_s':s['duration_s'],'sweep_s':s['duration_s']/len(next(iter(arr.values()))),'quadratures':quadratures,'A26':a26})
            add_observation(observations,'shuffled_weight_A26',f'{key} span {s["span"]}',a26.get('value'),reason=a26.get('reason'),source=a26)
            add_observation(observations,'shuffled_sd',f'{key} span {s["span"]}',None,reason='C3 supplies A26 weight but the v4 definition gives a distribution of population lengths, not one observed scalar; no unique observed sd is defined')
        result['shuffled'].append({'key':key,'source':source,'membership':membership,'spans':rows})
    result['sharing_all_monitor_spans']=not sharing_failures
    result['sharing_spans_counting_against']=sharing_failures
    dwell_checks=[check for job in result['jobs'] for check in job['dwell_checks']]
    dwell_complete=bool(dwell_checks) and all(check.get('under_0p01') is not None for check in dwell_checks)
    result['monitor_dwell_failures_under_0p01']=dwell_count if dwell_complete else None
    result['observed_monitor_dwell_failures_under_0p01_beside']=dwell_count if not args.record_only else None
    result['monitor_dwell_tests_complete']=dwell_complete
    result['more_than_one_monitor_dwell_failure']=dwell_count>1 if dwell_complete or dwell_count>1 else None
    result['boundary_counts']={word:sum(b['test15']['word']==word for b in result['boundaries']) for word in ['NO CHANGE','BETWEEN','CHANGE','NOT READ']}
    validlr=[x['likelihood_ratio'] for x in result['boundaries']+result['between_jobs'] if 'p_bootstrap' in x.get('likelihood_ratio',{})]
    result['any_monitor_boundary_LR_p_under_0p01']=any(x['p_bootstrap']<.01 for x in validlr) if validlr else None
    result['own_LR_scope']='Adjacent spans within each monitor job and adjacent monitor jobs'
    result['returned_order_favoured_span_count']=sum(order_votes) if order_votes else None
    result['returned_order_span_count']=len(order_votes)
    expected_order_spans=sum(len(j['series']) for j in result['jobs'])
    result['returned_order_all_preference']=all(order_votes) if order_votes and len(order_votes)==expected_order_spans else None
    for word,n in result['boundary_counts'].items():add_observation(observations,'boundary_count_'+word.lower().replace(' ','_'),'all monitor boundaries',n)
    add_observation(observations,'any_boundary_LR_reject_0p01','all monitor boundaries',result['any_monitor_boundary_LR_p_under_0p01'])
    add_observation(observations,'sharing_all_monitor_spans','all monitor spans',result['sharing_all_monitor_spans'])
    add_observation(observations,'returned_order_all_preference','all monitor spans',result['returned_order_all_preference'],
                    reason=None if result['returned_order_all_preference'] is not None else 'The order comparison is not available for every monitor span')
    span_counts=[len(j['series']) for j in result['jobs']]
    # C1 actual design calibration uses frozen model state and no observed quantities.
    from calibration_v4_1 import apply_calibration
    predictions,scenario,calibration=apply_calibration(predictions,result['jobs'],result['shuffled'],args)
    scenario_key='actual';scenarios=predictions['scenarios']
    result['calibration']=calibration
    result['scenario_applicability']=scenario['_applicability']
    result['prediction_scores'],result['families']=score_entries(predictions,observations,scenario)
    result['unavailable_outcomes']=[{'quantity':quantity,**obs} for quantity,items in observations.items() for obs in items if obs.get('value') is None]
    if args.reference_fits:
        reference=jload(args.reference_fits);checks=[]
        for job in result['jobs']:
            key=job['key']
            if key not in reference['jobs']:continue
            old=reference['jobs'][key]['qubits']['143']['waits']['monitor']
            for span in job['series']:
                before=next(s for s in old['spans'] if s['span']==span['span'])
                for ci,c in enumerate(span['circuits']):
                    for field in ['ratio','threshold','duty_b','lag_1_over_e','tau_c_s','telegraph_sd','mid_sweep_fraction_middle_fifth']:
                        computed=span['readings'][ci][field];published=before[c['quadrature']][field]
                        difference=computed-published if computed is not None and published is not None else None
                        checks.append({'job':key,'span':span['span'],'quadrature':c['quadrature'],'field':field,
                                       'computed':computed,'published':published,'difference':difference,
                                       'equal':abs(difference)<=1e-12 if difference is not None else computed is published})
        result['archived_reproduction']={'source':str(Path(args.reference_fits).resolve()),'sha256':sha(args.reference_fits),'checks':checks,
                                        'count':len(checks),'mismatches':sum(not c['equal'] for c in checks)}
    result['scenario_scores']=[]
    result['actual_span_counts']=span_counts;result['matching_scenario']=scenario_key if scenario_key in scenarios else None
    if scenario_key in scenarios:
        design_applicable=result['scenario_applicability']['dimensionless_applicable']
        count_scores=[]
        for word,observed in result['boundary_counts'].items():
            pred=scenario.get('boundary_counts',{}).get(word,{})
            interval=pred.get('interval_90') if isinstance(pred,dict) else None
            count_scores.append({'word':word,'observed':observed,'interval_90':interval,
                                 'inside_90':bool(interval[0]<=observed<=interval[1]) if interval and design_applicable else None,
                                 'uncalibrated_inside_90_beside':bool(interval[0]<=observed<=interval[1]) if interval and not design_applicable else None,
                                 'status':'scored' if interval and design_applicable else 'outside modeled design' if interval else 'not issued'})
        probability_events=[]
        for field,observed in [('sharing_all_probability',result['sharing_all_monitor_spans']),('any_LR_reject_probability',result['any_monitor_boundary_LR_p_under_0p01'])]:
            probability_record=scenario.get(field)
            probability=probability_record.get('probability') if isinstance(probability_record,dict) else probability_record
            probability_events.append({'prediction':field,'probability':probability,'observed':observed,
                                       'calibration':probability_record,
                                       'brier_score':(float(observed)-probability)**2 if probability is not None and observed is not None and design_applicable else None,
                                       'status':'scored' if probability is not None and observed is not None and design_applicable else 'unavailable'})
        order_prediction=scenario.get('returned_order_all_preference_probability')
        order_probability=order_prediction.get('probability') if isinstance(order_prediction,dict) else order_prediction
        order_observed=result['returned_order_all_preference']
        probability_events.append({'prediction':'returned_order_all_preference_probability','probability':order_probability,
                                   'observed_all_preference':order_observed,'calibration':order_prediction,
                                   'brier_score':(float(order_observed)-order_probability)**2 if order_probability is not None and order_observed is not None and design_applicable else None,
                                   'status':'scored' if order_probability is not None and order_observed is not None and design_applicable else 'unavailable'})
        low_change=[]
        per_boundary=scenario.get('boundary_change_probabilities',{})
        for index,br in enumerate(result['boundaries']):
            prediction=per_boundary.get(br['boundary_key']) if isinstance(per_boundary,dict) else per_boundary[index] if isinstance(per_boundary,list) and index<len(per_boundary) else None
            probability=prediction.get('probability') if isinstance(prediction,dict) else prediction
            low_change.append({'job':br['job'],'spans':br['spans'],'boundary_key':br['boundary_key'],'boundary_index':index,
                               'word':br['test15']['word'],'predicted_CHANGE_probability':probability,
                               'status':'scored' if probability is not None and design_applicable else 'unavailable',
                               'reason':'Outside modeled design' if not design_applicable else None if probability is not None else 'Matching boundary probability was not supplied',
                               'counts_against':br['test15']['word']=='CHANGE' and probability<.05 if probability is not None and design_applicable else None})
        result['scenario_scores'].append({'scenario':scenario_key,'scope':scenario.get('scope'),'assumptions':scenario.get('assumptions'),
                                         'count_intervals':count_scores,'probability_events':probability_events,
                                         'boundary_CHANGE_against_low_probability':low_change,
                                         'any_boundary_CHANGE_against_low_probability':any(x['counts_against'] for x in low_change) if any(x['counts_against'] is not None for x in low_change) else None})
    return native(result)


def main():
    p=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--job',action='append',default=[],required=True,help='key,array,meta,counts for a monitor job')
    p.add_argument('--shuffled',action='append',default=[],help='key,array,meta,counts for a shuffled job')
    p.add_argument('--predictions');p.add_argument('--out',required=True)
    p.add_argument('--reference-fits',help='Optional archived test 15 fits for a reproduction check only')
    p.add_argument('--bootstrap',type=int,default=400);p.add_argument('--dwell-permutations',type=int,default=2000)
    p.add_argument('--seed',type=int,default=104196401);p.add_argument('--record-only',action='store_true')
    # C1 calibration controls and frozen state; C3 explicitly supplied run fits.
    p.add_argument('--model-state')
    p.add_argument('--calibration-cache')
    p.add_argument('--calibration-seed',type=int,default=41119001)
    p.add_argument('--calibration-draws',type=int,default=2000)
    p.add_argument('--calibration-lr-trials',type=int,default=100)
    p.add_argument('--workers',type=int,default=4)
    p.add_argument('--shuffled-fits',action='append',default=[],help='C3 key,path to the run fits file')
    args=p.parse_args()
    if args.bootstrap<1 or args.dwell_permutations<1:raise ValueError('Positive simulation counts required')
    log=Path(__file__).resolve().parent/'data-run.log'
    with log.open('a') as f:
        f.write(datetime.datetime.now(datetime.timezone.utc).isoformat()+' command '+sys.executable+' -I '+' '.join(sys.argv)+'\n')
        f.write(f'Python {platform.python_version()} numpy {np.__version__} scipy {scipy.__version__}; seed {args.seed}; boundary draws {args.bootstrap}; dwell permutations {args.dwell_permutations}\n')
    result=score(args);save(args.out,result)
    print('Scorecard written',args.out,'monitor spans',sum(len(x['series']) for x in result['jobs']),'boundary counts',result['boundary_counts'],flush=True)


if __name__=='__main__':main()
