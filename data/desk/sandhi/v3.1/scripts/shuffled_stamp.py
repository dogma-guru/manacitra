#!/usr/bin/env python3
"""Recompute shuffled weights, copies by span, and stamp observables from input only."""
from pathlib import Path
import sys, json, gzip, hashlib, datetime, platform, re
import numpy as np
import scipy
from scipy.stats import chi2

BASE = Path(__file__).resolve().parents[1]
INPUT = BASE / 'input'
LOG = BASE / 'shuffled-stamp-commands.log'
def log(message):
    with LOG.open('a') as f:
        f.write(datetime.datetime.now(datetime.timezone.utc).isoformat() + ' ' + message + '\n')
def read(name):
    log('READ input/' + name)
    p = INPUT / name
    return json.loads(gzip.open(p, 'rt').read() if p.suffix == '.gz' else p.read_text())
def source(file, field):
    return {'file': 'input/' + file, 'field': field}
def dump(name, value):
    (BASE / name).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    log('WRITE ' + name)
def count(rows, key):
    chosen = [r for r in rows if r.get(key) is not None]
    return {'events': sum(bool(r[key]) for r in chosen), 'trials': len(chosen)}

log('COMMAND ' + ' '.join([sys.executable, '-I', str(Path(__file__).resolve())]))
log('VERSIONS ' + json.dumps({'python': platform.python_version(), 'numpy': np.__version__, 'scipy': scipy.__version__, 'float': 'float64', 'randomness': 'none'}))
hashes = []
for line in (INPUT / 'SHA256SUMS').read_text().splitlines():
    expected, name = line.split(maxsplit=1)
    name = name.lstrip('*')
    actual = hashlib.sha256((INPUT / name).read_bytes()).hexdigest()
    hashes.append({'file': 'input/' + name, 'expected': expected, 'actual': actual, 'equal': actual == expected})
assert all(x['equal'] for x in hashes)
log('HASH CHECK all ' + str(len(hashes)) + ' input digests equal')
for rule in ['kickoff-model-01-v3-errata-2026-10-17.md', 'kickoff-model-01-v3-gated-states-2026-10-17.md', 'kickoff-model-01-v2-gated-states-2026-10-17.md']:
    (INPUT / rule).read_text()
    log('READ authority input/' + rule)

spanrec = read('span-check/spans-t9.json')
spancompare = read('span-check/span-compare-t9.json')
t7 = read('t7/fits-t7.json')
t7read = read('t7/reading-t7.json')
t11 = read('t11/fits-t11.json')
t8 = {j: read(f't8/fits-t8-job{j}.json') for j in [1, 2, 3]}
t9 = {j: read(f't9/fits-t9-job{j}.json') for j in [1, 2, 3]}
t10 = read('t10/fits-t10.json.gz')
beside9 = read('t9/beside-t9.json')

spans = {}
for ji, j in enumerate(spanrec['jobs']):
    order = j['spans_in_start_order']
    span_by_id = {s['span']: (si, s) for si, s in enumerate(j['spans'])}
    ss = [span_by_id[s][1] for s in order]
    spans[(j['test'], j['job'])] = {
        'spans': ss, 'gaps': j['gaps'],
        'sources': [source('span-check/spans-t9.json', f'jobs[{ji}].spans'), source('span-check/spans-t9.json', f'jobs[{ji}].gaps')]}
js = t11['jobs']['1']['spans_derived']
ss = []
for si, s in enumerate(js['spans']):
    positions = [p for a, b in s['position_runs'] for p in range(a, b + 1)]
    ss.append({'span': si, 'positions': positions, **s})
spans[('t11', 1)] = {'spans': ss, 'gaps': js['gaps'], 'sources': [source('t11/fits-t11.json', 'jobs.1.spans_derived')]}

jobs = []
jobs.append({'test': 't7', 'job': 1, 'qubit': 143, 'processor': 'ibm_fez', 'verdict': t7['verdict'], 'usable': True, 'b': t7['fits']['P']['params']['b'],
    'positions': t7read['B_weight_in_execution_order']['positions'], 'position_source': source('t7/reading-t7.json', 'B_weight_in_execution_order.positions'),
    'copies': [(i,c) for i,c in enumerate(t7read['A_copy_agreement']['circuits']) if c['circuit'] in ['X','Y']], 'copies_source': source('t7/reading-t7.json', 'A_copy_agreement.circuits'),
    'eligibility_sources': [source('t7/fits-t7.json','verdict'),source('t7/fits-t7.json','fits.P.params.b')]})
for test, data in [('t8',t8), ('t9',{1:t9[1]})]:
    for j, d in data.items():
        for q, x in sorted(d['qubits'].items(), key=lambda p: int(p[0])):
            file = f'{test}/fits-{test}-job{j}.json'; pre = f'qubits.{q}'
            jobs.append({'test':test, 'job':j, 'qubit':int(q), 'processor':'ibm_kingston', 'verdict':x['verdict'], 'usable':x['usable'], 'b':x['P']['params']['b'],
                'positions': x['weight_in_execution_order'].get('positions',[]), 'position_source': source(file,pre+'.weight_in_execution_order.positions'),
                'copies': list(enumerate(x['copies_check']['ramsey']['circuits'])), 'copies_source': source(file,pre+'.copies_check.ramsey.circuits'),
                'eligibility_sources':[source(file,pre+'.verdict'),source(file,pre+'.usable'),source(file,pre+'.P.params.b')]})
j11 = t11['jobs']['1']; rd11 = j11['readings_after_the_data']
jobs.append({'test':'t11','job':1,'qubit':143,'processor':'ibm_fez','verdict':j11['analysis']['verdict'],'usable':True,'b':j11['analysis']['fits']['P']['params']['b'],
    'positions': rd11['B_weight_in_execution_order']['positions'], 'position_source': source('t11/fits-t11.json','jobs.1.readings_after_the_data.B_weight_in_execution_order.positions'),
    'copies':[(i,c) for i,c in enumerate(rd11['A_copy_agreement']['circuits']) if c['circuit'] in ['X','Y']], 'copies_source':source('t11/fits-t11.json','jobs.1.readings_after_the_data.A_copy_agreement.circuits'),
    'eligibility_sources':[source('t11/fits-t11.json','jobs.1.analysis.verdict'),source('t11/fits-t11.json','jobs.1.analysis.fits.P.params.b')]})

ledger = {k: [] for k in ['weight_boundaries','weight_span_means','weight_eligibility','skipped_weight_jobs','copies_same_span','copies_pair_rows','copies_job_totals','stamps','stamps_alternative_job2','stamp_pair2_unavailable','split_observable']}
notes = {'hash_check':{'n':len(hashes),'all_equal':True},'versions':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,'dtype':'float64','randomness':'none'},'reading_differences':[], 'methods': {}}
notes['methods'] = {
 'weight_span_mean':'Inverse variance weighted mean of archived b_pos with se equal to one over square root of summed inverse variances. P held at its archived fit. No additional scatter inflation.',
 'weight_own':'Absolute difference of adjacent span means strictly greater than five combined standard errors.',
 'weight_fixed':'Absolute difference of plain means at nearest three passing positions on each side of the boundary at least 0.10. Submitted position order is the available order inside each span.',
 'copies':'Archived per circuit z squared, Ramsey X and Y only, grouped by provider span membership. Each same span group compared strictly above chi2.ppf(0.999,n). The n is the number of copy pairs. Readout pairs excluded.',
 'split_interval':'Difference divided by quadrature combination of half widths of the two archived 90 percent intervals. Full width and Gaussian equivalent standard error conventions also reported. No distributional fit.',
 'stamp_primary':'Test 8 job 1 against test 9 job 1 on their common usable qubits. Event is absolute S.params.Delta_MHz change at least 0.004 MHz or change of the shuffled verdict kind.'}

for x in jobs:
    test,j,q=x['test'],x['job'],x['qubit']
    ident={k:x[k] for k in ['test','job','qubit','processor','verdict']}
    eligible=x['usable'] and x['verdict'] in ['TWO FIXED FREQUENCIES','NOT SETTLED'] and 0.05 < x['b'] < 0.95
    sr=spans.get((test,j))
    subset_key = f'{test}_job{j}' if test!='t7' else 't7'
    # The selected list is the actual span comparison qubit table, intersected with eligibility.
    selected=bool(str(q) in spancompare['interleaved'].get(subset_key,{}).get('qubits',{}))
    if test=='t7':
        selected=True
    er={**ident,'design':'shuffled','b':x['b'],'usable':x['usable'],'eligible':eligible,'span_record_available':sr is not None,'selected_subset':selected,'sources':x['eligibility_sources']}
    ledger['weight_eligibility'].append(er)
    if eligible and sr is None:
        ledger['skipped_weight_jobs'].append({**er,'reason':'No provider execution span record in the supplied input. No boundary trial can be assigned.'})
    if sr is None or not x['usable']:
        continue
    mapping={p:s['span'] for s in sr['spans'] for p in s['positions']}
    assert len(mapping)==260
    if eligible:
        means=[]
        for s in sr['spans']:
            ids=[i for i,p in enumerate(x['positions']) if mapping[p['k']]==s['span']]
            pp=[x['positions'][i] for i in ids]
            values=np.array([p['b_pos'] for p in pp],dtype=np.float64)
            errors=np.array([p['se'] for p in pp],dtype=np.float64)
            if len(pp)==0:
                mu=se=chisq=None
            else:
                inv=1/errors**2; mu=float(np.sum(values*inv)/np.sum(inv)); se=float(1/np.sqrt(np.sum(inv))); chisq=float(np.sum(((values-mu)/errors)**2))
            m={**ident,'design':'shuffled','span':s['span'],'n':len(pp),'positions':[p['k'] for p in pp],'position_array_indices':ids,'mean':mu,'se':se,'chi2':chisq,'dof':max(0,len(pp)-1),'selected_subset':selected,'sources':[x['position_source'],*sr['sources']]}
            if test=='t11':
                archived=j11['span_readings_A26']['weight_per_span'][s['span']]
                m['archived_A26_mean']=archived['weighted_mean'];m['archived_A26_se']=archived['se'];m['recomputed_minus_archived_mean']=mu-archived['weighted_mean'];m['recomputed_minus_archived_se']=se-archived['se']
                m['sources'].append(source('t11/fits-t11.json',f'jobs.1.span_readings_A26.weight_per_span[{s["span"]}]'))
                assert np.isclose(mu,archived['weighted_mean'],rtol=0,atol=1e-14)
                assert np.isclose(se,archived['se'],rtol=0,atol=1e-14)
            means.append(m);ledger['weight_span_means'].append(m)
        for bi,(before,after) in enumerate(zip(means,means[1:]),1):
            boundary_pos=min(sr['spans'][bi]['positions'])
            pp=sorted(x['positions'],key=lambda z:z['k'])
            nearbefore=[z for z in pp if z['k']<boundary_pos][-3:]
            nearafter=[z for z in pp if z['k']>=boundary_pos][:3]
            n_ok=len(nearbefore)==len(nearafter)==3
            fixedbefore=float(np.mean([z['b_pos'] for z in nearbefore])) if n_ok else None
            fixedafter=float(np.mean([z['b_pos'] for z in nearafter])) if n_ok else None
            ok=before['n']>0 and after['n']>0
            difference=after['mean']-before['mean'] if ok else None
            se=float(np.hypot(before['se'],after['se'])) if ok else None
            fixedchange=fixedafter-fixedbefore if n_ok else None
            row={**ident,'channel':'B','design':'shuffled','boundary':bi,'spans':[before['span'],after['span']],'boundary_position':boundary_pos,'gap_s':sr['gaps'][bi-1]['gap_s'],
                'span_mean_before':before['mean'],'span_mean_after':after['mean'],'span_se_before':before['se'],'span_se_after':after['se'],'span_n_before':before['n'],'span_n_after':after['n'],
                'change_own':difference,'combined_se':se,'floor_own':5*se if ok else None,'z_own':abs(difference)/se if ok else None,'event_own':bool(abs(difference)>5*se) if ok else None,
                'nearest_three_before':nearbefore,'nearest_three_after':nearafter,'plain_mean_before':fixedbefore,'plain_mean_after':fixedafter,'change_fixed':fixedchange,'floor_fixed':0.10,'event_fixed':bool(abs(fixedchange)>=0.10) if n_ok else None,
                'selected_subset':selected,'sources':[x['position_source'],*sr['sources'],*x['eligibility_sources']]}
            if test=='t11':
                fixed_arch=j11['weight_changes_across_boundaries']['boundaries'][['first','second'][bi-1]]
                row['archived_fixed_change']=fixed_arch['change'];row['sources'].append(source('t11/fits-t11.json',f'jobs.1.weight_changes_across_boundaries.boundaries.{["first","second"][bi-1]}'))
                assert abs(fixedchange-fixed_arch['change'])<1e-14
            if selected and test!='t11':
                compkey='t7_job1' if test=='t7' else f'{test}_job{j}'
                rec=spancompare['interleaved'].get(compkey,{})
                if str(q) in rec.get('qubits',{}):
                    published=rec['qubits'][str(q)]['near_boundaries'][str(boundary_pos)]
                    row['tabulated_rounded_nearest_three_change']=float(np.mean([p[1] for p in published['after']])-np.mean([p[1] for p in published['before']]))
                    row['sources'].append(source('span-check/span-compare-t9.json',f'interleaved.{compkey}.qubits.{q}.near_boundaries.{boundary_pos}'))
            ledger['weight_boundaries'].append(row)
    # All usable shuffled records with spans enter copies, irrespective of weight eligibility.
    pairrows=[]
    for ci,c in x['copies']:
        si=[mapping[p] for p in c['positions']]
        pair={**ident,'design':'shuffled','circuit':c['circuit'],'wait_us':c.get('t_requested_us'),'positions':c['positions'],'spans':si,'same_span':si[0]==si[1], 'z':float(c['z']),'z2':float(np.float64(c['z'])**2),
            'sources':[{'file':x['copies_source']['file'],'field':x['copies_source']['field']+f'[{ci}]'},*sr['sources']]}
        pairrows.append(pair);ledger['copies_pair_rows'].append(pair)
    for s in sr['spans']:
        same=[p for p in pairrows if p['same_span'] and p['spans'][0]==s['span']]
        n=len(same); total=float(np.sum([p['z2'] for p in same],dtype=np.float64)); threshold=float(chi2.ppf(0.999,n)) if n else None
        ledger['copies_same_span'].append({**ident,'design':'shuffled','span':s['span'],'n':n,'dof':n,'sum_z2':total,'chi2_threshold_999':threshold,'p_upper':float(chi2.sf(total,n)) if n else None,'event_lower_floor':bool(total>threshold) if n else None,'frequency_size_kHz':None,
            'pair_positions':[p['positions'] for p in same],'sources':[x['copies_source'],*sr['sources']]})
    same=[p for p in pairrows if p['same_span']];cross=[p for p in pairrows if not p['same_span']]
    ledger['copies_job_totals'].append({**ident,'same_span':{'n':len(same),'sum_z2':float(np.sum([p['z2'] for p in same],dtype=np.float64))},'cross_span':{'n':len(cross),'sum_z2':float(np.sum([p['z2'] for p in cross],dtype=np.float64))},'sources':[x['copies_source'],*sr['sources']]})

# Calibration crossing 1. The explicit job 1 population and the source table extension are separate.
for ix,b in enumerate(beside9['test8_beside_test9']):
    q=str(b['qubit']); j=b['test8_job']; a=t8[j]['qubits'][q]; z=t9[1]['qubits'][q]
    fa=f't8/fits-t8-job{j}.json';fz='t9/fits-t9-job1.json';p=f'qubits.{q}'
    eligible=bool(a['usable'] and z['usable']);delta=float((np.float64(z['S']['params']['Delta_MHz'])-np.float64(a['S']['params']['Delta_MHz']))*1000)
    kindchange=a['verdict']!=z['verdict']
    row={'channel':'S','pair':'pair1','design':'shuffled','processor':'ibm_kingston','qubit':int(q),'test_before':'t8','job_before':j,'test_after':'t9','job_after':1,
        'stamp_before':t8[j]['meta']['published_snapshot_last_update'],'stamp_after':t9[1]['meta']['published_snapshot_last_update'],'same_calendar_day':True,'eligible':eligible,
        'Delta_MHz_before':a['S']['params']['Delta_MHz'],'Delta_MHz_after':z['S']['params']['Delta_MHz'],'change_kHz':delta,'floor_kHz':4.0,'kind_before':a['verdict'],'kind_after':z['verdict'],'kind_event':kindchange,'frequency_event':abs(delta)>=4.0,'event':bool(kindchange or abs(delta)>=4.0) if eligible else None,'primary':j==1,
        'sources':[source(fa,p+'.S.params.Delta_MHz'),source(fz,p+'.S.params.Delta_MHz'),source(fa,p+'.verdict'),source(fz,p+'.verdict'),source(fa,p+'.usable'),source(fz,p+'.usable'),source(fa,'meta.published_snapshot_last_update'),source(fz,'meta.published_snapshot_last_update'),source('t9/beside-t9.json',f'test8_beside_test9[{ix}]')]}
    ledger['stamps' if j==1 else 'stamps_alternative_job2'].append(row)

# The additional 143 stamp crossing uses S detuning. P frame is a separate reported observable.
sa=t7['fits']['S']['params']['Delta_MHz']; sz=j11['analysis']['fits']['S']['params']['Delta_MHz']
pa=t7['fits']['P']['params']['Delta0_MHz']; pz=j11['analysis']['fits']['P']['params']['Delta0_MHz']
stamps11=(INPUT/'t11/stamps-t11.csv').read_text().splitlines()
import csv,io
stamp11rows=list(csv.DictReader(io.StringIO('\n'.join(stamps11))))
log('READ input/t11/stamps-t11.csv')
notes['stamp11_csv_columns']=list(stamp11rows[0])
stamp11values=sorted(set(row['stamp_utc'] for row in stamp11rows))
assert len(stamp11values)==1
ledger['stamps'].append({'channel':'S','pair':'t7_to_t11','design':'shuffled','processor':'ibm_fez','qubit':143,'test_before':'t7','job_before':1,'test_after':'t11','job_after':1,'eligible':True,
    'stamp_before':t7['beside']['9_published_from_submission_to_fetch']['at_submission']['stamp_utc'],'stamp_after':stamp11values[0],'same_calendar_day':False,
    'Delta_MHz_before':sa,'Delta_MHz_after':sz,'change_kHz':float((sz-sa)*1000),'floor_kHz':4.0,'kind_before':t7['verdict'],'kind_after':j11['analysis']['verdict'],'kind_event':t7['verdict']!=j11['analysis']['verdict'],'frequency_event':abs(sz-sa)>=0.004,'event':bool(abs(sz-sa)>=0.004 or t7['verdict']!=j11['analysis']['verdict']),'primary':True,
    'P_Delta0_MHz_before':pa,'P_Delta0_MHz_after':pz,'P_frame_change_kHz':float((pz-pa)*1000),
    'sources':[source('t7/fits-t7.json','fits.S.params.Delta_MHz'),source('t11/fits-t11.json','jobs.1.analysis.fits.S.params.Delta_MHz'),source('t7/fits-t7.json','fits.P.params.Delta0_MHz'),source('t11/fits-t11.json','jobs.1.analysis.fits.P.params.Delta0_MHz'),source('t7/fits-t7.json','verdict'),source('t11/fits-t11.json','jobs.1.analysis.verdict'),source('t7/fits-t7.json','beside.9_published_from_submission_to_fetch.at_submission.stamp_utc'),source('t11/stamps-t11.csv','stamp_utc')]})

# Pair 2 cannot be reduced to S detuning from a monitor level alone. Retain all overlaps.
for ja in [1,2,3]:
    aqs=t9[ja]['qubits']
    for jb in [1,2,3]:
        zqs=t10['jobs'][str(jb)]['per_qubit']
        for q in sorted(set(aqs)&set(zqs),key=int):
            a,z=aqs[q],zqs[q]; factor=z['kHz_per_rad'];levels=z['levels']
            afile=f't9/fits-t9-job{ja}.json';zf='t10/fits-t10.json.gz'; ap=f'qubits.{q}';zp=f'jobs.{jb}.per_qubit.{q}'
            afield=ap+'.S.params.Delta_MHz' if ja==1 else ap+'.Delta_bar_kHz'
            afreq=a['S']['params']['Delta_MHz']*1000 if ja==1 else a['Delta_bar_kHz']
            record={'channel':'S','pair':'pair2','qubit':int(q),'processor':'ibm_kingston','test_before':'t9','job_before':ja,'test_after':'t10','job_after':jb,'design_before':'shuffled' if ja==1 else 'scan','design_after':'monitor','usable_before':a['usable'],'usable_after':z['usable'], 'eligible':False,'event':None,'status':'not reconstructable under the stated S definition',
                'reason':'The monitor has no S fit. Its level is a phase at one wait. The records do not supply a common absolute frequency reference and branch choice for a conversion to S detuning. The monitor verdict concerns temporal changes, not the number of lines.',
                'kind_before':a['verdict'],'monitor_verdict_after':z['verdict'],'before_frequency_kHz':afreq,'monitor_wait_us':z['wait_us'],'monitor_kHz_per_rad':factor,'monitor_job_mean_phase':z['job_mean_phase'],'monitor_levels':levels,
                'alternative_zero_phase_reference_kHz':[lev['mean']*factor for lev in levels],
                'alternative_job_mean_reference_kHz':[(lev['mean']-z['job_mean_phase'])*factor for lev in levels],
                'frequency_alias_period_kHz':1000/z['wait_us'],'alternative_event':None,
                'sources':[source(afile,afield),source(afile,ap+'.verdict'),source(afile,ap+'.usable'),source(zf,zp+'.levels'),source(zf,zp+'.job_mean_phase'),source(zf,zp+'.kHz_per_rad'),source(zf,zp+'.wait_us'),source(zf,zp+'.verdict'),source(zf,zp+'.usable'),source('rules/t10-rule.md','The wait per qubit; Reported beside the verdicts item 4')]}
            ledger['stamp_pair2_unavailable'].append(record)

# Split observable: apply both TWO FIXED FREQUENCIES exactly.
def splitrow(test_before,job_before,q,a,b,delta_a,delta_b,cia,cib,sources):
    eligible=a=='TWO FIXED FREQUENCIES' and b=='TWO FIXED FREQUENCIES'
    hw=float(np.hypot((cia[1]-cia[0])/2,(cib[1]-cib[0])/2));change=float(delta_b-delta_a)
    return {'test_before':test_before,'job_before':job_before,'test_after':'t11' if q==143 else 't9','job_after':1,'qubit':q,'kind_before':a,'kind_after':b,'eligible':eligible,'fitted':False,'delta_before_kHz':delta_a,'delta_after_kHz':delta_b,'ci90_before_kHz':cia,'ci90_after_kHz':cib,'change_kHz':change,'combined_interval_half_width_kHz':hw,'change_in_combined_interval_units':change/hw if eligible else None,'change_in_combined_full_interval_units':change/(2*hw) if eligible else None,'change_in_gaussian_equivalent_standard_errors':change/(hw/1.6448536269514722) if eligible else None,'status':'reported beside' if eligible else 'unavailable because both verdicts must be TWO FIXED FREQUENCIES','sources':sources}
ledger['split_observable'].append(splitrow('t7',1,143,t7['verdict'],j11['analysis']['verdict'],t7['fits']['P']['params']['delta_MHz']*1000,j11['analysis']['fits']['P']['params']['delta_MHz']*1000,t7['deciding']['delta_ci90_kHz'],j11['analysis']['deciding']['delta_ci90_kHz'],[source('t7/fits-t7.json','fits.P.params.delta_MHz'),source('t7/fits-t7.json','deciding.delta_ci90_kHz'),source('t7/fits-t7.json','verdict'),source('t11/fits-t11.json','jobs.1.analysis.fits.P.params.delta_MHz'),source('t11/fits-t11.json','jobs.1.analysis.deciding.delta_ci90_kHz'),source('t11/fits-t11.json','jobs.1.analysis.verdict')]))
for jb in [1,3]:
    a=t8[jb]['qubits']['43'];b=t9[1]['qubits']['43']
    ledger['split_observable'].append(splitrow('t8',jb,43,a['verdict'],b['verdict'],a['P']['params']['delta_MHz']*1000,b['P']['params']['delta_MHz']*1000,a['deciding']['delta_ci90_kHz'],b['deciding']['delta_ci90_kHz'],[source(f't8/fits-t8-job{jb}.json','qubits.43.P.params.delta_MHz'),source(f't8/fits-t8-job{jb}.json','qubits.43.deciding.delta_ci90_kHz'),source(f't8/fits-t8-job{jb}.json','qubits.43.verdict'),source('t9/fits-t9-job1.json','qubits.43.P.params.delta_MHz'),source('t9/fits-t9-job1.json','qubits.43.deciding.delta_ci90_kHz'),source('t9/fits-t9-job1.json','qubits.43.verdict')]))

w=ledger['weight_boundaries']; old=[r for r in w if r['test']!='t11'];selected=[r for r in old if r['selected_subset']]
cold=[r for r in ledger['copies_same_span'] if r['test'] in ['t8','t9']]
notes['summary']={
 'weight_complete_own':count(w,'event_own'),'weight_complete_fixed':count(w,'event_fixed'),
 'weight_tests7to9_own':count(old,'event_own'),'weight_tests7to9_fixed':count(old,'event_fixed'),
 'weight_selected_tests7to9_own':count(selected,'event_own'),'weight_selected_tests7to9_fixed':count(selected,'event_fixed'),
 'weight_by_job':{f'{t}_job{j}':{'own':count([r for r in w if r['test']==t and r['job']==j],'event_own'),'fixed':count([r for r in w if r['test']==t and r['job']==j],'event_fixed')} for t,j in sorted(set((r['test'],r['job']) for r in w))},
 'copies_tests8to9':count(cold,'event_lower_floor'),'copies_outliers_tests8to9':[{k:r[k] for k in ['test','job','qubit','span','n','sum_z2','chi2_threshold_999','p_upper']} for r in cold if r['event_lower_floor']],
 'copies_with_t7_t11':count(ledger['copies_same_span'],'event_lower_floor'),
 'stamp_pair1_job1':count([r for r in ledger['stamps'] if r['pair']=='pair1'],'event'),
 'stamp_pair1_job2_alternative':count(ledger['stamps_alternative_job2'],'event'),
 'stamp_pair1_all63_alternative':count([r for r in ledger['stamps'] if r['pair']=='pair1']+ledger['stamps_alternative_job2'],'event'),
 'stamp_primary_pooled':count(ledger['stamps'],'event'),
 'pair2_rows':len(ledger['stamp_pair2_unavailable']),'pair2_distinct_qubits':len(set(r['qubit'] for r in ledger['stamp_pair2_unavailable']))}
notes['reading_differences']=[
 {'topic':'Weight population','reading':'The complete eligible set with available provider span records is primary. The original span comparison selected set is retained separately. Test 8 job 2 eligible records lack spans and are skipped.','sources':[source('kickoff-model-01-v3-gated-states-2026-10-17.md','sections 0 and 2.2'),source('span-check/spans-t9.json','jobs')]},
 {'topic':'Stamp pair 1 population','reading':'The text names test 8 job 1 but also says 63 qubits. The table has 47 from job 1 plus 16 from job 2. The stated job 1 pair is primary; all 63 and the extra 16 are reported beside.','sources':[source('kickoff-model-01-v2-gated-states-2026-10-17.md','section 2.4 channel S'),source('t9/beside-t9.json','test8_beside_test9[*].test8_job')]},
 {'topic':'Stamp pair 2','reading':'No S event is fitted for an unlike phase observable without a common absolute reference. Zero phase and job mean phase conversions remain explicit alternatives without event classification.','sources':[source('rules/t10-rule.md','The wait per qubit; Reported beside the verdicts item 4')]},
 {'topic':'143 crossing','reading':'S detuning and P frame movement are different fields. The errata is applied to S.','sources':[source('kickoff-model-01-v3-errata-2026-10-17.md','item 2')]},
 {'topic':'43 split','reading':'The test 9 verdict is NOT SETTLED. Its split difference cannot enter the observable restricted to TWO FIXED FREQUENCIES on both records. Both test 8 readings remain beside.','sources':[source('t9/fits-t9-job1.json','qubits.43.verdict')]},
 {'topic':'Test 11 first shuffled boundary','reading':'The exact ratio of the span mean difference to its combined standard error is reported in the ledger. The errata replaces the earlier wording of twenty with about thirteen.','sources':[source('kickoff-model-01-v3-errata-2026-10-17.md','item 4')]}
]
# Resolve every ledger source field against its supplied input, and check pair coverage.
source_cache={};source_n=0;json_field_n=0;csv_field_n=0
for rows in ledger.values():
    if not isinstance(rows,list): continue
    for row in rows:
        for s in row.get('sources',[]):
            source_n+=1;p=BASE/s['file'];assert p.is_file()
            if p.suffix in ['.json','.gz']:
                if p not in source_cache:
                    source_cache[p]=json.loads(gzip.open(p,'rt').read() if p.suffix=='.gz' else p.read_text())
                obj=source_cache[p]
                for token in re.findall(r'[^.\[\]]+',s['field']):
                    obj=obj[int(token)] if isinstance(obj,list) else obj[token]
                json_field_n+=1
            elif p.suffix=='.csv':
                assert s['field'] in next(csv.DictReader(io.StringIO(p.read_text())))
                csv_field_n+=1
for row in ledger['copies_job_totals']:
    assert row['same_span']['n']+row['cross_span']['n']==128
notes['validation']={'all_source_files_exist':True,'source_references':source_n,'json_field_references_resolved':json_field_n,'csv_field_references_resolved':csv_field_n,'copies_128_pairs_per_usable_job_qubit':True,'test11_A26_means_and_errors_match_recomputation_at_absolute_tolerance':1e-14,'test11_nearest_three_changes_match_recomputation_at_absolute_tolerance':1e-14}
ledger['meta']={'kind':'computed facts of archived records','sources_root':'input','float_dtype':'float64','randomness':'none','input_hashes_all_equal':True,'input_hash_count':len(hashes),'summary':notes['summary']}
dump('shuffled-stamp-ledger.json',ledger)
dump('shuffled-stamp-notes.json',notes)
print(json.dumps(notes['summary'],indent=2))
