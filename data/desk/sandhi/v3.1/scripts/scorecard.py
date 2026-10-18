"""Score archived quoted bets, separating quoted and reconstructed intervals."""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parent))
from statistics_core import fit,predict
ROOT=Path(__file__).resolve().parents[1]
def load(n):return json.loads((ROOT/n).read_text())
n=load('normalized-trials.json')['rows'];m=load('monitor11-ledger.json');s=load('shuffled-stamp-ledger.json')
source=load('input/t11/fits-t11.json')['counts_of_the_run']
old=[r for r in n if r['test']<11 and r['included']]
def pre(ch,floor,pool='main'):
    return fit([r for r in old if r['channel']==ch and r['floor']==floor and r['pool']==pool], 'poisson' if ch=='W' else 'binomial')
boundary=predict(pre('F','own'),trials=4)
within=predict(pre('W','own'),exposure=186.)
weight=predict(pre('B','fixed0.10'),trials=2)
gap=predict(pre('F','4kHz','gap'),trials=1)
fixed_b=sum(r['event_fixed'] for r in s['weight_boundaries'] if r['test']=='t11')
observed=[m['summary']['F']['events_own'],m['summary']['W']['events_own'],fixed_b,
          int(next(r for r in m['trials'] if r['channel']=='F_gap')['exceeds_five_combined_se'])]
quoted_fields=['phase_switches_at_the_span_boundaries_of_jobs_2_and_3',
               'phase_switches_within_spans_of_jobs_2_and_3',
               'weight_changes_0p10_across_job_1s_span_boundaries',
               'phase_differs_by_more_than_5_se_across_the_gap']
labels=['Frequency boundaries in two monitors','Frequency within two monitors','Weight boundaries in shuffled job','Frequency between monitor jobs']
rows=[]
for label,key,obs,reconstructed in zip(labels,quoted_fields,observed,[boundary,within,weight,gap]):
    ci=reconstructed['posterior_predictive_count_interval_90']
    rows.append({'bet':label,'quoted_source':{'file':'input/t11/fits-t11.json','field':'counts_of_the_run.'+key+'.model'},
        'quoted_forecast':source[key]['model'],'observed_count_recomputed':obs,
        'quoted_count_interval_status':'Quoted predictive count is zero and matches' if key==quoted_fields[0] else 'No predictive count interval supplied; cannot score inside or outside a quoted count interval',
        'reconstructed_from_pre_test11_ledger':reconstructed,
        'inside_reconstructed_count_interval':ci[0]<=obs<=ci[1],
        'reconstruction_is_original_sealed_prediction':False})
result={'kind':'Computed scorecard and separately labelled model reconstruction',
    'note':'Intervals on event probabilities are not intervals on an observed zero or one. Failure of a named event to occur is not itself a parameter interval test.',
    'source_limits':'The original sealed prediction files are absent. Only their quoted values in the rule and fits are available.',
    'within_exposure_note':'The quoted design used 186 seconds; actual whole repeat exposure is 167.7355241020408 seconds.',
    'rows':rows,
    'selected_weight_alternative':{'quoted_probability':.91,'quoted_probability_interval':[.69,.99],
        'reconstruction':predict(fit([{'id':str(i),'included':True,'event':r['event_fixed'],'exposure_s':0.} for i,r in enumerate(s['weight_boundaries']) if r['test']!='t11' and r['selected_subset']],'binomial'),trials=2)}}
(ROOT/'historical-scorecard.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
print([(r['bet'],r['observed_count_recomputed'],r['reconstructed_from_pre_test11_ledger']['posterior_predictive_count_interval_90']) for r in rows])
