from pathlib import Path
import sys,json,collections,time
sys.path.insert(0,str(Path(__file__).resolve().parent))
import numpy as np
from hmm_model import fit_job,fit_grouped,simulate_span
HERE=Path(__file__).resolve().parent
def ci(a):
    a=np.asarray([np.nan if x is None else x for x in a]);v=a[np.isfinite(a)];return {'ci90':np.quantile(v,[.05,.95]).tolist() if len(v) else None,'finite':len(v),'total':len(a)}
def delta(a,b):return {'delta_b':b['b']-a['b'],'delta_log_ell':float(np.log(b['ell']/a['ell'])) if a['ell'] and b['ell'] else None}
def boundary_test_spans(spans,draws=400,seed=40118200,interval_draws=400):
    alt=fit_job(spans);null=fit_job(spans,common_rates=True);obs=max(0.,2*(alt['loglik']-null['loglik']));rng=np.random.default_rng(seed);lrs=[];failures=[];ds=[]
    for k in range(draws):
        sim=[simulate_span(s,f,null['q_H'],null['q_L'],rng) for s,f in zip(spans,null['spans'])];n=fit_job(sim,common_rates=True,starts=1,return_series=False);a=fit_job(sim,starts=1,return_series=False);lrs.append(max(0.,2*(a['loglik']-n['loglik'])))
        if not a['success'] or not n['success']:failures.append({'phase':'null','draw':k,'alternative':a['attempts'],'null':n['attempts']})
    for k in range(interval_draws):
        sim=[simulate_span(s,f,alt['q_H'],alt['q_L'],rng) for s,f in zip(spans,alt['spans'])];a=fit_job(sim,starts=1,return_series=False);ds.append(delta(*a['spans']))
        if not a['success']:failures.append({'phase':'interval','draw':k,'alternative':a['attempts']})
    return {'ids':[s['id'] for s in spans],'null':null,'alternative':alt,'LR':obs,'p_bootstrap':float((1+np.sum(np.asarray(lrs)>=obs))/(draws+1)),'null_draws':draws,'interval_draws':interval_draws,'seed':seed,**delta(*alt['spans']),'difference_intervals':{k:ci([d[k] for d in ds]) for k in ('delta_b','delta_log_ell')},'null_LR_draws':lrs,'difference_draws':ds,'failures':failures}
def boundary_test_job_pair(groups,draws=400,seed=40118300,interval_draws=400):
    null=fit_grouped(groups,rates_per_group=False);alt=fit_grouped(groups,rates_per_group=True);obs=max(0.,2*(alt['loglik']-null['loglik']));rng=np.random.default_rng(seed);lrs=[];ds=[];failures=[]
    def simulation(f):return [[simulate_span(s,v,g['q_H'],g['q_L'],rng) for s,v in zip(ss,g['spans'])] for ss,g in zip(groups,f['groups'])]
    for k in range(draws):
        sim=simulation(null);n=fit_grouped(sim,False,1);a=fit_grouped(sim,True,1);lrs.append(max(0.,2*(a['loglik']-n['loglik'])))
        if not a['success'] or not n['success']:failures.append({'phase':'null','draw':k,'alternative':a['attempts'],'null':n['attempts']})
    for k in range(interval_draws):
        sim=simulation(alt);a=fit_grouped(sim,True,1);ds.append(delta(a['groups'][0]['spans'][0],a['groups'][1]['spans'][0]))
        if not a['success']:failures.append({'phase':'interval','draw':k,'alternative':a['attempts']})
    return {'jobs':[g[0]['job'] for g in groups],'null':null,'alternative':alt,'interpretation':'One rate pair per job over all its eligible spans; job emissions separate in both fits','LR':obs,'p_bootstrap':float((1+np.sum(np.asarray(lrs)>=obs))/(draws+1)),'null_draws':draws,'interval_draws':interval_draws,'seed':seed,**delta(alt['groups'][0]['spans'][0],alt['groups'][1]['spans'][0]),'difference_intervals':{k:ci([d[k] for d in ds]) for k in ('delta_b','delta_log_ell')},'null_LR_draws':lrs,'difference_draws':ds,'failures':failures}
def main():
    spans=json.loads((HERE/'series-base.json').read_text())['spans'];groups=collections.defaultdict(list)
    for s in spans:groups[s['job']+'-q'+str(s['qubit'])].append(s)
    ref=json.loads((HERE.parent/'model-01-v4-input/model-01-bundle-v4-2026-10-18/t15/fits-t15.json').read_text())
    out={'within_jobs':[],'between_jobs':[],'method':'Parametric null calibration with (exceedances plus one) over (draws plus one); percentile differences from independent alternative simulations; no comparison word','draws_per_comparison':400}
    index=0
    for key,ss in groups.items():
        for a,b in zip(ss[:-1],ss[1:]):
            if b['span']!=a['span']+1:continue
            t=time.perf_counter();v=boundary_test_spans([a,b],seed=40118200+index);ri=next(i for i,x in enumerate(ref['boundaries']) if x['job']==a['job'] and x['qubit']==a['qubit'] and x['spans']==[a['span'],b['span']]);v['t15_word']=ref['boundaries'][ri]['word'];v['t15_word_source']=f"t15/fits-t15.json boundaries[{ri}].word";out['within_jobs'].append(v);index+=1
            (HERE/'boundaries-model-01-v4.json').write_text(json.dumps(out,indent=2,allow_nan=False));print(key,a['span'],b['span'],v['LR'],v['p_bootstrap'],'seconds',time.perf_counter()-t,flush=True)
    fez=[g for g in groups.values() if g[0]['processor']=='ibm_fez'];fez.sort(key=lambda g:g[0]['start_utc'])
    for k,(a,b) in enumerate(zip(fez[:-1],fez[1:])):
        t=time.perf_counter();v=boundary_test_job_pair([a,b],seed=40118300+k);ri=next(i for i,x in enumerate(ref['between_jobs_143']['rows']) if x['jobs']==[a[0]['job'],b[0]['job']]);v['t15_word']=ref['between_jobs_143']['rows'][ri]['word'];v['t15_word_source']=f't15/fits-t15.json between_jobs_143.rows[{ri}].word';out['between_jobs'].append(v);(HERE/'boundaries-model-01-v4.json').write_text(json.dumps(out,indent=2,allow_nan=False));print('between',a[0]['job'],b[0]['job'],v['LR'],v['p_bootstrap'],'seconds',time.perf_counter()-t,flush=True)
if __name__=='__main__':main()
