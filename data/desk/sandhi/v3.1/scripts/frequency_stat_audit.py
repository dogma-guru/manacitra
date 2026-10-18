"""Independent current run normalization and statistical audit."""
from pathlib import Path
import collections
import hashlib
import json
import math
import numpy as np
from scipy import stats
ROOT=Path(__file__).resolve().parents[1]
NAMES=['scripts/normalize.py','scripts/statistics_core.py','scripts/fit_model.py','frequency-ledger.json','monitor11-ledger.json','shuffled-stamp-ledger.json','normalized-trials.json','rates-model-01-v3.json','dependence-model-01-v3.json','model-check-model-01-v3.json','report-model-01-v3.md']
snapshot={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in NAMES}
def load(n):return json.loads((ROOT/n).read_text())
f=load('frequency-ledger.json');m=load('monitor11-ledger.json');s=load('shuffled-stamp-ledger.json')
norm=load('normalized-trials.json')['rows'];rates=load('rates-model-01-v3.json');dep=load('dependence-model-01-v3.json');mc=load('model-check-model-01-v3.json')
checks=[];issues=[]
def check(name,ok,details=None):checks.append({'check':name,'pass':bool(ok),'details':details})
def near(a,b):return math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-10)
def gbin(g):
 if g is None:return 'not applicable'
 if .004<=g<=.006:return '5 ms'
 if 14<=g<16:return '14 to 15 s'
 if g<1:return 'under 1 s'
 if g<=3:return '1 to 3 s'
 return 'over 3 s'
expected={}
def expect(source,i,r,ch,floor,included,event,exposure,pool):
 rid=f'{source}:{i}:{floor}'
 spans=r.get('span_pair',r.get('spans',[None]));job=r.get('job',r.get('job_after',0))
 expected[rid]={'channel':ch,'floor':floor,'included':bool(included),'event':bool(event) if included else None,
  'exposure_s':float(exposure) if included else 0.,'pool':pool,'test':int(str(r.get('test',r.get('test_after'))).removeprefix('t')),
  'job':' to '.join(map(str,job)) if isinstance(job,list) else job,'qubit':r['qubit'],'design':r['design'],
  'processor_record':'143' if r.get('processor')=='ibm_fez' else 'kingston qubits',
  'boundary':r.get('boundary'),'gap_s':r.get('gap_s'),'gap_bin':gbin(r.get('gap_s')),
  'span':spans[0] if spans else None,'stamp':r.get('stamp_utc',r.get('stamp',r.get('stamp_after','not available'))),
  'stamp_pair':r.get('pair') if ch=='S' else None,'source_ledger':source,'source_index':i}
for i,r in enumerate(f['rows']):
 for floor,suffix in [('4kHz','4khz'),('own','own')]:
  expect('frequency-ledger.json',i,r,r['channel'],floor,r['eligible_'+suffix],r['event_'+suffix],r['exposure_'+suffix+'_s'],'gap' if r['trial_class']=='between_jobs' else 'main')
for i,r in enumerate(m['trials']):
 ch=r['channel'].removesuffix('_gap');pool='gap' if r['channel'].endswith('_gap') else 'main'
 if ch in ('W','F'):
  variants=[('4kHz',r['eligible_4khz'],r['event_4khz'],r['exposure_4khz_s']),('own',r['eligible_own'],r['event_own'],r['exposure_own_s'])]
 elif ch=='W_B':variants=[('fixed0.10',r['included'],r['event_own'],r['exposure_own_s']),('own',r['included'],r['event_five_se'],r['exposure_own_s'])]
 elif ch=='B':variants=[('fixed0.10',r['included'],r['event_fixed'],0),('own',r['included'],r['event_own'],0)]
 else:raise ValueError(ch)
 for floor,inc,e,ex in variants:expect('monitor11-ledger.json',i,r,ch,floor,inc,e,ex,pool)
for i,r in enumerate(s['weight_boundaries']):
 for floor,key in [('fixed0.10','event_fixed'),('own','event_own')]:expect('shuffled-stamp-ledger.json:weight_boundaries',i,r,'B',floor,r[key] is not None,r[key],0,'main')
for i,r in enumerate(s['stamps']):expect('shuffled-stamp-ledger.json:stamps',i,r,'S','4kHz',r['eligible'],r['event'],0,'main')
nd={r['id']:r for r in norm}
check('normalized row identity coverage',len(norm)==len(nd)==len(expected) and set(nd)==set(expected),{'rows':len(norm)})
diff=[]
for rid,e in expected.items():
 for field,value in e.items():
  if field not in nd[rid] or nd[rid][field]!=value:diff.append({'id':rid,'field':field,'source':value,'normalized':nd[rid].get(field)})
check('every normalized decision exposure class and source reference equals source ledger',not diff,{'differences':diff[:20],'difference_count':len(diff)})
check('complete primary frequency observations retained',all(nd[f'frequency-ledger.json:{i}:own']['included']==r['eligible_own'] for i,r in enumerate(f['rows'])),{'extra_own_rows_beyond_whole_job_usable_filter':sum(r['eligible_own'] and not r['usable_job'] for r in f['rows']), 'alternative_flags_present':all('eligible_own_usable_job_alternative' in r for r in f['rows'])})
check('all eligible shuffled weight boundaries retained',sum(r['included'] for r in norm if r['source_ledger']=='shuffled-stamp-ledger.json:weight_boundaries' and r['floor']=='own')==sum(r['event_own'] is not None for r in s['weight_boundaries']),{'source_rows':len(s['weight_boundaries'])})
main=[r for r in norm if r['included'] and r['pool']=='main'];gap=[r for r in norm if r['included'] and r['pool']=='gap']
rate_diff=[];fits=0

def check_fit(obj,rr,label):
 global fits
 fits+=1;n=sum(r['event'] for r in rr);trials=len(rr);exp=math.fsum(r['exposure_s'] for r in rr)
 checks0=[obj['events']==n,obj['trials']==trials,near(obj['exposure_s'],exp),set(obj.get('row_ids',[]))==set(r['id'] for r in rr)]
 if trials:
  if obj['family']=='poisson':dist=stats.gamma(n+.5,scale=1/exp);post={'shape':n+.5,'rate':exp}
  else:dist=stats.beta(n+.5,trials-n+.5);post={'alpha':n+.5,'beta':trials-n+.5}
  checks0 += [near(obj['posterior'][k],v) for k,v in post.items()]
  checks0 += [near(obj[k],float(dist.ppf(p))) for k,p in [('q05',.05),('median',.5),('q95',.95)]]
  if obj['family']=='poisson':checks0.append(near(obj['probability_rate_below_1e_minus_4'],float(dist.cdf(1e-4))))
 if not all(checks0):rate_diff.append({'fit':label,'checks':checks0})
for key,obj in rates['pooled'].items():
 ch,floor=key.split('|');rr=[r for r in main if r['channel']==ch and r['floor']==floor];check_fit(obj,rr,key)
 for dim,classes in rates['classes'][key].items():
  covered=[]
  check(key+' class labels '+dim,set(classes)==set(str(r.get(dim,'not applicable')) for r in rr))
  for label,value in classes.items():
   selected=[r for r in rr if str(r.get(dim,'not applicable'))==label];covered+=value.get('row_ids',[]);check_fit(value,selected,key+':'+dim+':'+label)
  check(key+' class conservation '+dim,len(covered)==len(set(covered))==len(rr) and set(covered)==set(r['id'] for r in rr))
check('all saved posterior totals parameters quantiles and row memberships match independent formulas',not rate_diff,{'fits_checked':fits,'differences':rate_diff})
check('no between jobs row enters a main posterior',not any(rid in set(r['id'] for r in gap) for obj in rates['pooled'].values() for rid in obj.get('row_ids',[])))
gap_counts=[]
for key,obj in rates['separate_gap_classes'].items():
 ch,floor=key.split('|');rr=[r for r in gap if r['channel']==ch and r['floor']==floor]
 check('separate gap total '+key,obj['events']==sum(r['event'] for r in rr) and obj['trials']==len(rr) and set(obj['row_ids'])==set(r['id'] for r in rr))
 for test in sorted({r['test'] for r in rr}):
  rrr=[r for r in rr if r['test']==test]
  gap_counts.append({'channel':ch,'floor':floor,'test':test,'trials':len(rrr),'events':sum(r['event'] for r in rrr),'gaps_s':sorted({r['gap_s'] for r in rrr})})
# Recompute each Fisher result directly from its saved integer table.
fisher_dif=[];lrt_dif=[]
for i,t in enumerate(dep['tests']):
 if t.get('test')=='Fisher exact' and 'table' in t:
  p=stats.fisher_exact(t['table'],alternative='two-sided').pvalue
  if not near(t['p_value'],float(p)):fisher_dif.append(i)
 if t.get('test')=='Poisson likelihood ratio' and 'channel' in t:
  rr=[r for r in main if r['channel']==t['channel'] and r['floor']==t['floor']]
  nn=[];ee=[]
  for lab in t['classes']:
   sr=[r for r in rr if str(r.get(t['dimension'],'not applicable'))==lab];nn.append(sum(r['event'] for r in sr));ee.append(math.fsum(r['exposure_s'] for r in sr))
  if sum(nn)==0:stat=0;p=1
  else:
   ex=np.asarray(ee)/sum(ee)*sum(nn);stat=2*sum(n*math.log(n/e) for n,e in zip(nn,ex) if n);p=float(stats.chi2.sf(stat,1))
  if not near(t['statistic'],stat) or not near(t['p_value'],p):lrt_dif.append(i)
check('Fisher p values recomputed independently',not fisher_dif,{'differences':fisher_dif})
check('Poisson likelihood ratio p values recomputed independently',not lrt_dif,{'differences':lrt_dif})
# Check simulated count arrays and their summaries without importing the fitting code.
cell_diff=[]
for i,c in enumerate(mc['cells']):
 if 'fixed_counts' not in c:continue
 rr=[r for r in main if r['channel']==c['channel'] and r['floor']==c['floor'] and r['test']==c['test'] and (c['design_model']=='pooled' or r['design']==c['design_model'])]
 a=np.asarray(c['fixed_counts']);b=np.asarray(c['posterior_predictive_counts'])
 tests=[len(a)==1000,len(b)==1000,c['observed']==sum(r['event'] for r in rr),c['trials']==len(rr),near(c['exposure_s'],math.fsum(r['exposure_s'] for r in rr)),
  c['fixed_median_count_interval_90']==list(map(int,np.quantile(a,[.05,.95],method='inverted_cdf'))),
  c['posterior_predictive_count_interval_90']==list(map(int,np.quantile(b,[.05,.95],method='inverted_cdf')))]
 if not all(tests):cell_diff.append({'cell':i,'checks':tests})
check('model check count arrays intervals and cell totals',not cell_diff,{'differences':cell_diff})
# Record scope concerns as of this exact snapshot so a later repair is inspectable.
if any(c.get('job_range_caveat','').startswith('Aggregate simulated counts') for c in mc['cells']):
 issues.append({'id':'aggregate versus job range','status':'present in snapshot','source':'scripts/fit_model.py and model-check-model-01-v3.json','finding':'The alternate job range compares an aggregate simulated count to a per job range. Its caveat is correct, but a matched exposure simulation is needed for that comparison.'})
if not any(t.get('dimension')=='boundary at five standard errors' or 'five' in str(t).lower() for t in dep['tests']):
 issues.append({'id':'five standard error Fisher comparison','status':'not found in snapshot','source':'dependence-model-01-v3.json:tests','finding':'The supplementary source rows alone do not constitute the requested first boundary against second boundary Fisher test.'})
for ch in ['W','F']:
 if not any(c.get('channel')==ch and c.get('floor')=='4kHz' and c.get('test')==11 for c in mc['cells']):
  issues.append({'id':'censored model check cell '+ch,'status':'not found in snapshot','source':'model-check-model-01-v3.json:cells','finding':'Test 11 at 4 kHz has no eligible observations. An explicit not testable entry would keep censoring distinct from an omitted cell.'})
if 'by_test' not in rates['separate_gap_classes'].get('F|own',{}):
 issues.append({'id':'between jobs reporting classes','status':'combined total only in snapshot','source':'rates-model-01-v3.json:separate_gap_classes.F|own','finding':'The own floor gap total combines test 10 and test 11. The audit supplies the individual test totals and exact gaps beside.'})
# The requested monitor boundary contrast is distinct from the pooled contrast.
first10=[r for r in main if r['test']==10 and r['channel']=='F' and r['floor']=='4kHz' and r['boundary']==1]
second10=[r for r in main if r['test']==10 and r['channel']=='F' and r['floor']=='4kHz' and r['boundary']==2]
table10=[[sum(r['event'] for r in first10),len(first10)-sum(r['event'] for r in first10)],[sum(r['event'] for r in second10),len(second10)-sum(r['event'] for r in second10)]]
found10=[t for t in dep['tests'] if t.get('channel')=='F' and t.get('floor')=='4kHz' and t.get('table')==table10]
if not found10:issues.append({'id':'test 10 boundary comparison at 4 kHz','status':'not found in snapshot','source':'dependence-model-01-v3.json:tests','finding':'The required test 10 comparison is a different population from pooled boundaries. Its table is '+str(table10)+'.'})
# Check sensitivity inversion at its exact count boundary.
sensitivity_diff=[]
for key,sens in mc['sensitivity'].items():
 rate=rates['pooled'][key]
 if rate['family']=='poisson':
  if not near(sens['exposure_for_90_percent_one_event_at_rate_q95'],-math.log(.1)/rate['q95']):sensitivity_diff.append(key)
 else:
  for label,values in sens.items():
   rate=rates['pooled'][key] if label=='pooled' else rates['classes'][key]['design'][label]
   for field,qkey in [('trials_for_90_percent_at_least_three_at_q05','q05'),('at_median','median'),('at_q95','q95')]:
    n=values[field];p=rate[qkey]
    if not (stats.binom.sf(2,n,p)>=.9 and (n==3 or stats.binom.sf(2,n-1,p)<.9)):sensitivity_diff.append(key+':'+label+':'+field)
check('sensitivity inversions use correct posterior quantile and smallest trial count',not sensitivity_diff,{'differences':sensitivity_diff})
# Compare the report tables and stated frequency totals to exact source rows.
report=(ROOT/'report-model-01-v3.md').read_text()
for test,job in [(9,2),(9,3),(10,1),(10,2),(10,3)]:
 w=f['summaries'][f't{test}j{job}:within_span'];b=f['summaries'][f't{test}j{job}:span_boundary']
 expected_line=f"| {test}, job {job} | {w['events_4khz']} / {w['n_4khz']} | {b['events_4khz']} / {b['n_4khz']} | {w['events_own']} / {w['n_own']} | {b['events_own']} / {b['n_own']} | exact |"
 check('report exact frequency count row '+f't{test}j{job}',expected_line in report,{'source':'frequency-ledger.json:summaries'})
 expected_exposure='| '+str(test)+', job '+str(job)+' | '+' | '.join(format(w[k],'.6g') for k in ['exposure_4khz_s','exposure_own_s','censored_exposure_s'])+' |'
 check('report rounded frequency exposure row '+f't{test}j{job}',expected_exposure in report,{'source':'frequency-ledger.json:summaries'})
for a in f['alternating_qubits']:
 pairs=', '.join('('+', '.join(map(str,p['pair']))+')' for p in a['pairs'])
 line=f"| {a['test']}, job {a['job']} | {a['qubit']} | {pairs} |"
 check('report alternating pairs '+f"t{a['test']}j{a['job']}q{a['qubit']}",line in report,{'source':'frequency-ledger.json:alternating_qubits'})
check('report distinguishes endpoint frequency and source fitted level changes',str(len(f['source_fitted_level_changes_separate_observable']))+' reported change points' in report and 'different observable' in report)
check('report kind persistence counts and alternatives',str(len(f['kind_events']))+' events' in report and 'yields '+str(sum(r['event_both_runs_persist_two_alternative'] for r in f['kind_transitions'])) in report)
check('report exact between jobs frequency populations','130.111131 seconds: 1 / 63 frequency events at 4 kHz and 1 / 68 at the own floor' in report and '63.518444 seconds: 0 / 1 frequency events at its own floor' in report)
check('report five standard error population totals','first boundaries give 0 / 190 and second boundaries 3 / 190; controls give 0 / 570' in report)
check('report own floor and 4 kHz frequency pooled populations','| W at 4kHz | 0 / 26064 |' in report and '| W at own | 0 / 29123 |' in report and '| F at 4kHz | 1 / 479 |' in report and '| F at own | 1 / 599 |' in report)
final_hashes={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in NAMES}
check('audit source snapshots remained stable',snapshot==final_hashes,{'changed_files':[n for n in NAMES if snapshot[n]!=final_hashes[n]]})
result={'scope':'Independent audit of current run outputs against their current run source ledgers. No earlier run output used.',
 'input_snapshots_sha256':snapshot,'checks':checks,'all_numerical_checks_pass':all(c['pass'] for c in checks),
 'scope_issues':issues,'per_test_gap_counts':gap_counts,'normalized_rows':len(norm),
 'primary_and_alternatives':'Primary complete line observation set is used. Whole job usable alternatives remain in the frequency source ledger. Shuffled source ledger alternatives remain separate and are not silently pooled.',
 'method':'Independent aggregation and scipy distribution formulas. Fitting helpers were read but were not imported or executed by this audit.',
 'randomness':'none'}
(ROOT/'frequency-stat-audit.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
print(json.dumps({'checks':len(checks),'all_numerical_checks_pass':result['all_numerical_checks_pass'],'failed_checks':[c for c in checks if not c['pass']], 'scope_issues':issues,'gap_counts':gap_counts},indent=2))
