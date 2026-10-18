"""Normalize counts without changing a source event definition."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def load(n):return json.loads((ROOT/n).read_text())
f=load('frequency-ledger.json');m=load('monitor11-ledger.json');s=load('shuffled-stamp-ledger.json')
rows=[]
def gap_bin(g):
    if g is None:return 'not applicable'
    if .004<=g<=.006:return '5 ms'
    if 14<=g<16:return '14 to 15 s'
    if g<1:return 'under 1 s'
    if g<=3:return '1 to 3 s'
    return 'over 3 s'
def add(r,channel,floor,included,event,exposure,source,index,pool='main'):
    test=r.get('test',r.get('test_after'))
    test=int(str(test).removeprefix('t'))
    job=r.get('job',r.get('job_after',0))
    if isinstance(job,list):job=' to '.join(map(str,job))
    spans=r.get('span_pair',r.get('spans',[None]))
    rows.append({'id':f'{source}:{index}:{floor}','channel':channel,'floor':floor,'included':bool(included),
        'event':bool(event) if included else None,'exposure_s':float(exposure) if included else 0.,
        'test':test,'job':job,'qubit':r['qubit'],'design':r['design'],
        'processor_record':'143' if r.get('processor')=='ibm_fez' else 'kingston qubits',
        'boundary':r.get('boundary'),'gap_s':r.get('gap_s'),'gap_bin':gap_bin(r.get('gap_s')),
        'span':spans[0] if spans else None,'stamp':r.get('stamp_utc',r.get('stamp',r.get('stamp_after','not available'))),
        'stamp_pair':r.get('pair') if channel=='S' else None,'pool':pool,'source_ledger':source,'source_index':index})
for i,r in enumerate(f['rows']):
    for floor,suffix in [('4kHz','4khz'),('own','own')]:
        add(r,r['channel'],floor,r['eligible_'+suffix],r['event_'+suffix],r['exposure_'+suffix+'_s'],
            'frequency-ledger.json',i,'gap' if r['trial_class']=='between_jobs' else 'main')
for i,r in enumerate(m['trials']):
    ch=r['channel']; pool='gap' if ch.endswith('_gap') else 'main';ch=ch.removesuffix('_gap')
    if ch in ('W','F'):
        for floor,suffix in [('4kHz','4khz'),('own','own')]:
            add(r,ch,floor,r.get('eligible_'+suffix,False),r['event_'+suffix],r['exposure_'+suffix+'_s'],'monitor11-ledger.json',i,pool)
    elif ch=='W_B':
        for floor,event in [('fixed0.10',r['event_own']),('own',r['event_five_se'])]:
            add(r,ch,floor,r['included'],event,r['exposure_own_s'],'monitor11-ledger.json',i,pool)
    elif ch=='B':
        for floor,event in [('fixed0.10',r['event_fixed']),('own',r['event_own'])]:
            add(r,ch,floor,r['included'],event,0,'monitor11-ledger.json',i,pool)
for i,r in enumerate(s['weight_boundaries']):
    for floor,event in [('fixed0.10',r['event_fixed']),('own',r['event_own'])]:
        add(r,'B',floor,event is not None,event,0,'shuffled-stamp-ledger.json:weight_boundaries',i)
for i,r in enumerate(s['stamps']):
    add(r,'S','4kHz',r['eligible'],r['event'],0,'shuffled-stamp-ledger.json:stamps',i)
assert len({r['id'] for r in rows})==len(rows)
(ROOT/'normalized-trials.json').write_text(json.dumps({'source_policy':'No new event decisions; normalization of source ledgers','rows':rows},separators=(',',':'),allow_nan=False)+'\n')
master={'kind':'Computed facts of archived records','frequency':f,'monitor11':m,'shuffled_weight_stamps_copies':s,
        'normalized_trial_file':'normalized-trials.json','normalization_script':'scripts/normalize.py'}
(ROOT/'events-model-01-v3.json').write_text(json.dumps(master,separators=(',',':'),allow_nan=False)+'\n')
print('Normalized rows',len(rows))
