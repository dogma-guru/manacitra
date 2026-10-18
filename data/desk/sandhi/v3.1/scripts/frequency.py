"""Frequency ledger from the supplied input directory only.
Python floats and numpy float64 use IEEE binary64. No randomness is used.
"""
from pathlib import Path
import datetime as dt
import gzip
import hashlib
import json
import platform
import sys
from collections import Counter, defaultdict
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / 'input'
ROWS = []
ASSIGNMENTS = []
TRANSITIONS = []
LEVEL_CHANGES = []
SUPPLEMENT = []
ALTERNATING = defaultdict(list)
D = np.float64


def read(rel):
    path = INPUT / rel
    if rel.endswith('.gz'):
        with gzip.open(path, 'rt') as stream:
            return json.load(stream)
    return json.loads(path.read_text())


def output(name, value):
    (ROOT / name).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def hash_check():
    result = []
    for line in (INPUT / 'SHA256SUMS').read_text().splitlines():
        if not line.strip():
            continue
        expected, rel = line.split(None, 1)
        rel = rel.lstrip('*')
        actual = hashlib.sha256((INPUT / rel).read_bytes()).hexdigest()
        result.append({'file': 'input/' + rel, 'expected': expected, 'actual': actual, 'match': actual == expected})
    if not all(v['match'] for v in result):
        raise ValueError('Input hash difference')
    return result


def mapping(spans, repeats, width, source):
    pos = {}
    for span in spans:
        positions = span.get('positions')
        if positions is None:
            positions = [p for a, b in span['position_runs'] for p in range(a, b + 1)]
        for p in positions:
            if p in pos:
                raise ValueError('Position assigned more than once')
            pos[p] = span['span']
    obs = {}
    for k in range(1, repeats + 1):
        positions = list(range(2 + width * (k - 1), 2 + width * k))
        circuit_spans = [pos[p] for p in positions]
        ss = sorted(set(circuit_spans))
        obs[k] = {'k': k, 'positions': positions, 'circuit_spans': circuit_spans,
                  'span': ss[0] if len(ss) == 1 else None, 'straddling': len(ss) != 1}
    nwhole = Counter(r['span'] for r in obs.values() if not r['straddling'])
    periods = {s['span']: float(D(s['duration_s']) / nwhole[s['span']]) for s in spans}
    # A nominal duration for a removed pair is not an observed clock interval.
    # Its endpoint periods are averaged, with each circuit receiving equal weight.
    for r in obs.values():
        r['nominal_period_s'] = float(np.mean(np.asarray([periods[s] for s in r['circuit_spans']], dtype=np.float64)))
    return obs, periods, nwhole


def gap_bin(gap, between=False):
    if between:
        return 'between_jobs'
    if gap is None:
        return None
    if gap < 1:
        return 'under_1_s'
    if gap <= 3:
        return '1_to_3_s'
    return 'over_3_s'


def wrap(value):
    return D((D(value) + np.pi) % (2 * np.pi) - np.pi)


def make_row(test, job, qubit, a, b, u, v, assignments, usable, source_file, source_fields,
             channel, trial_class, period, boundary=None, gap=None, factor=None, second_job=None):
    ma, mb = assignments
    if test == 9:
        line = [D(u['A']) <= 1, D(v['A']) <= 1]
        se = D(np.hypot(D(u['s_MHz']), D(v['s_MHz'])) * 1000)
        change = D((D(v['Delta_MHz']) - D(u['Delta_MHz'])) * 1000)
        threshold = max(D(1), D(5) * se)
        alternating = bool(all(line) and abs(D(u['A']) - D(v['A'])) > (D(u['A']) + D(v['A'])) / 6)
        endpoint_values = [{f: float(D(r[f])) for f in ['Delta_MHz', 'A', 's_MHz']} for r in [u, v]]
        raw_angle = None
    else:
        line = [D(u['r']) >= D(.08), D(v['r']) >= D(.08)]
        se_rad = D(np.hypot(D(u['s']), D(v['s'])))
        raw_angle = float(wrap(D(v['theta']) - D(u['theta'])))
        change = D(raw_angle) * D(factor)
        se = se_rad * D(factor)
        threshold = max(D(.3), D(5) * se_rad) * D(factor)
        alternating = False
        endpoint_values = [{f: float(D(r[f])) for f in ['theta', 'r', 's']} for r in [u, v]]
    exclusions = []
    if ma['straddling'] or mb['straddling']:
        exclusions.append('straddling')
    if not all(line):
        exclusions.append('non_line')
    if alternating:
        exclusions.append('alternation')
    own = not exclusions
    censored = bool(own and threshold > 4)
    eligible4 = bool(own and not censored)
    row = {
        'id': f't{test}j{job}q{qubit}:{trial_class}:{a}:{b}',
        'channel': channel, 'test': test, 'job': job, 'qubit': int(qubit),
        'processor': 'ibm_kingston', 'design': 'scan' if test == 9 else 'monitor',
        'stamp_utc': '2026-10-17T14:06:47Z' if test == 9 else '2026-10-17T16:22:59Z',
        'trial_class': trial_class, 'second_job': second_job, 'pair': [a, b],
        'span_pair': [ma['span'], mb['span']], 'endpoint_circuit_spans': [ma['circuit_spans'], mb['circuit_spans']],
        'boundary': boundary, 'gap_s': gap, 'gap_class': gap_bin(gap, second_job is not None),
        'source_file': source_file, 'source_fields': source_fields,
        'endpoint_values': endpoint_values, 'line_observations': [bool(x) for x in line],
        'usable_job': bool(usable), 'straddling': bool(ma['straddling'] or mb['straddling']), 'alternating': alternating,
        'signed_change_kHz': float(change), 'change_kHz': float(abs(change)),
        'wrapped_phase_change_rad': raw_angle, 'kHz_per_rad': factor,
        'combined_se_kHz': float(se), 'T_k_kHz': float(threshold),
        'eligible_own': bool(own), 'eligible_4khz': eligible4, 'censored_4khz': censored,
        'exclusion_reasons': exclusions,
        'event_own': bool(abs(change) >= threshold) if own else None,
        'event_4khz': bool(abs(change) >= max(D(4), threshold)) if eligible4 else None,
        'eligible_own_usable_job_alternative': bool(own and usable),
        'eligible_4khz_usable_job_alternative': bool(eligible4 and usable),
        'raw_exposure_s': float(period), 'exposure_own_s': float(period if own else 0),
        'exposure_4khz_s': float(period if eligible4 else 0),
        'censored_exposure_s': float(period if censored else 0),
        'exposure_basis': 'span duration divided by whole repeats' if trial_class == 'within_span' else
                          ('nominal equal circuit weighted endpoint period mean' if trial_class == 'excluded_adjacent' else 'trial count only'),
        'over_5_se_only': bool(abs(change) > 5 * se),
        'kind': 'computed fact of archived records'
    }
    ROWS.append(row)
    if alternating:
        ALTERNATING[(test, job, int(qubit))].append({'pair': [a, b], 'trial_class': trial_class, 'row_id': row['id']})
    return row


def add_transitions(test, job, q, repeats, obs, source_file, prefix, usable):
    line = [r['A'] <= 1 if test == 9 else r['r'] >= .08 for r in repeats]
    for i in range(1, len(line)):
        if line[i] == line[i-1]:
            continue
        before = 1
        while i-1-before >= 0 and line[i-1-before] == line[i-1]:
            before += 1
        after = 1
        while i+after < len(line) and line[i+after] == line[i]:
            after += 1
        a, b = i, i+1
        ma, mb = obs[a], obs[b]
        if ma['straddling'] or mb['straddling']:
            place = 'at_straddling_repeat'
        elif ma['span'] == mb['span']:
            place = 'within_span'
        else:
            place = 'at_boundary'
        TRANSITIONS.append({'test': test, 'job': job, 'qubit': int(q), 'pair': [a,b],
            'from': 'line' if line[i-1] else 'non_line', 'to': 'line' if line[i] else 'non_line',
            'before_run_length': before, 'after_run_length': after,
            'event_destination_persists_two': after >= 2, 'event_both_runs_persist_two_alternative': before >= 2 and after >= 2,
            'location': place, 'span_pair': [ma['span'],mb['span']], 'usable_job': bool(usable),
            'source_file': source_file, 'source_field': prefix+'.repeats',
            'repeat_value_field': 'A' if test == 9 else 'r', 'kind': 'computed fact of archived records'})


def summarize(rows):
    out = {}
    for test, job, cls in sorted(set((r['test'],r['job'],r['trial_class']) for r in rows)):
        rr = [r for r in rows if (r['test'],r['job'],r['trial_class']) == (test,job,cls)]
        name = f't{test}j{job}:{cls}'
        out[name] = {'test': test, 'job': job, 'trial_class': cls, 'candidate_rows': len(rr),
          'n_4khz': sum(r['eligible_4khz'] for r in rr), 'events_4khz': sum(r['event_4khz'] is True for r in rr),
          'n_own': sum(r['eligible_own'] for r in rr), 'events_own': sum(r['event_own'] is True for r in rr),
          'censored_pairs': sum(r['censored_4khz'] for r in rr),
          'exposure_4khz_s': float(sum(r['exposure_4khz_s'] for r in rr)),
          'exposure_own_s': float(sum(r['exposure_own_s'] for r in rr)),
          'censored_exposure_s': float(sum(r['censored_exposure_s'] for r in rr)),
          'excluded_pairs_by_reason_overlapping': {reason: sum(reason in r['exclusion_reasons'] for r in rr) for reason in ['non_line','alternation','straddling']},
          'excluded_exposure_s_by_reason_overlapping': {reason: float(sum(r['raw_exposure_s'] for r in rr if reason in r['exclusion_reasons'])) for reason in ['non_line','alternation','straddling']},
          'usable_job_alternative': {
            'n_4khz': sum(r['eligible_4khz_usable_job_alternative'] for r in rr),
            'n_own': sum(r['eligible_own_usable_job_alternative'] for r in rr),
            'events_4khz': sum(r['event_4khz'] is True and r['usable_job'] for r in rr),
            'events_own': sum(r['event_own'] is True and r['usable_job'] for r in rr),
            'exposure_4khz_s': float(sum(r['exposure_4khz_s'] for r in rr if r['usable_job'])),
            'exposure_own_s': float(sum(r['exposure_own_s'] for r in rr if r['usable_job']))}}
    return out


def main():
    hashes = hash_check()
    spans9 = read('span-check/spans-t9.json')
    for job in [2,3]:
        file = f'input/t9/fits-t9-job{job}.json'
        data = read(file[6:])
        idx, execution = next((i,z) for i,z in enumerate(spans9['jobs']) if z['test']=='t9' and z['job']==job)
        obs, periods, nwhole = mapping(execution['spans'],18,16,'span-check/spans-t9.json')
        assert [k for k,r in obs.items() if r['straddling']] == [7,13]
        ASSIGNMENTS.append({'test':9,'job':job,'source_file':'input/span-check/spans-t9.json',
            'source_field':f'jobs[{idx}]','spans':execution['spans'],'gaps':execution['gaps'],
            'repeats':list(obs.values()),'whole_repeat_counts':dict(nwhole),'repeat_period_s':periods,
            'straddling_repeats':[7,13]})
        boundary_pairs = []
        for bn,g in enumerate(execution['gaps'],1):
            a = max(k for k,r in obs.items() if r['span']==g['after_span'])
            b = min(k for k,r in obs.items() if r['span']==g['before_span'])
            boundary_pairs.append((a,b,bn,g['gap_s']))
        for q,z in data['qubits'].items():
            rr = z['repeats']; prefix = f'qubits.{q}'
            for k in range(1,18):
                ma,mb = obs[k],obs[k+1]
                cls = 'excluded_adjacent' if ma['straddling'] or mb['straddling'] else 'within_span'
                period = float((D(ma['nominal_period_s'])+D(mb['nominal_period_s']))/2)
                make_row(9,job,q,k,k+1,rr[k-1],rr[k],[ma,mb],z['usable'],file,
                    [f'{prefix}.repeats[{k-1}]',f'{prefix}.repeats[{k}]',f'input/span-check/spans-t9.json:jobs[{idx}].spans'],
                    'W',cls,period)
            for a,b,bn,gap in boundary_pairs:
                make_row(9,job,q,a,b,rr[a-1],rr[b-1],[obs[a],obs[b]],z['usable'],file,
                    [f'{prefix}.repeats[{a-1}]',f'{prefix}.repeats[{b-1}]',f'input/span-check/spans-t9.json:jobs[{idx}].gaps[{bn-1}]'],
                    'F','span_boundary',0,bn,gap)
            add_transitions(9,job,q,rr,obs,file,prefix,z['usable'])
            if z['verdict'] in ['STEPPED','MOVING']:
                for k in z['models']['two_levels']['change_repeats']:
                    row = next(r for r in reversed(ROWS) if r['test']==9 and r['job']==job and r['qubit']==int(q) and r['pair']==[k-1,k])
                    LEVEL_CHANGES.append({'test':9,'job':job,'qubit':int(q),'verdict':z['verdict'],'change_repeat':k,
                      'source_file':file,'source_field':f'{prefix}.models.two_levels','level_gap_kHz':float(D(z['models']['two_levels']['gap_MHz'])*1000),
                      'level_gap_se_kHz':float(D(z['models']['two_levels']['se_gap_MHz'])*1000),
                      'endpoint_row_id':row['id'],'endpoint_exclusion_reasons':row['exclusion_reasons'],'endpoint_T_k_kHz':row['T_k_kHz'],
                      'endpoint_change_kHz':row['change_kHz'],'endpoint_event_own':row['event_own'],
                      'counted_in_endpoint_model':False})
    data10 = read('t10/fits-t10.json.gz')
    observations10 = {}
    for job_s,data in data10['jobs'].items():
        job = int(job_s); execution = data['execution_record']; file = 'input/t10/fits-t10.json.gz'
        obs, periods, nwhole = mapping(execution['spans'],148,2,file)
        observations10[job]=obs
        assert not any(r['straddling'] for r in obs.values())
        saved_agreement = []
        for q,z in data['per_qubit'].items():
            for r in z['repeats']:
                m=obs[r['k']]
                saved_agreement.append(m['span']==r['span'] and m['straddling']==r['straddles'] and m['circuit_spans']==r['spans_of_circuits'])
            assert all(abs(periods[int(s)]-v)<1e-12 for s,v in z['repeat_period_s'].items())
        assert all(saved_agreement)
        ASSIGNMENTS.append({'test':10,'job':job,'source_file':file,'source_field':f'jobs.{job}.execution_record',
            'spans':execution['spans'],'gaps_s':execution['gaps_s'],'repeats':list(obs.values()),
            'whole_repeat_counts':dict(nwhole),'repeat_period_s':periods,'straddling_repeats':[],
            'reconstructed_assignment_matches_all_saved_repeats':all(saved_agreement)})
        for q,z in data['per_qubit'].items():
            rr=z['repeats']; prefix=f'jobs.{job}.per_qubit.{q}'
            for k in range(1,148):
                ma,mb=obs[k],obs[k+1]; iswithin=ma['span']==mb['span']
                bn=None if iswithin else mb['span']; gap=None if iswithin else execution['gaps_s'][bn-1]
                make_row(10,job,q,k,k+1,rr[k-1],rr[k],[ma,mb],z['usable'],file,
                    [f'{prefix}.repeats[{k-1}]',f'{prefix}.repeats[{k}]',f'{prefix}.repeat_period_s',f'jobs.{job}.execution_record'],
                    'W' if iswithin else 'F','within_span' if iswithin else 'span_boundary',
                    z['repeat_period_s'][str(ma['span'])] if iswithin else 0,bn,gap,z['kHz_per_rad'])
            add_transitions(10,job,q,rr,obs,file,prefix,z['usable'])
            if z['usable']:
                controls=data10['beside']['2_boundary_table'][job_s]['per_qubit'][q]['control']
                checkpairs=[('boundary',int(b['between_spans'][1]),b['k'],b['k1'],b) for b in data10['beside']['2_boundary_table'][job_s]['per_qubit'][q]['boundaries']]
                checkpairs += [('control',int(c['span']),c['k'],c['k1'],c) for c in controls]
                for kind,num,a,b,saved in checkpairs:
                    u,v=rr[a-1],rr[b-1]; change=wrap(D(v['theta'])-D(u['theta'])); se=D(np.hypot(D(u['s']),D(v['s'])))
                    event=bool(abs(change)>5*se)
                    assert abs(float(change)-saved['d'])<1e-12 and abs(float(se)-saved['se'])<1e-12 and event==saved['over_5_se']
                    SUPPLEMENT.append({'test':10,'job':job,'qubit':int(q),'kind':kind,'boundary_or_span':num,'pair':[a,b],
                        'change_rad':float(change),'se_rad':float(se),'event_5_se_only':event,
                        'line_pair':bool(u['r']>=.08 and v['r']>=.08),'source_file':file,
                        'source_fields':[f'{prefix}.repeats[{a-1}]',f'{prefix}.repeats[{b-1}]'],
                        'saved_comparison_matches':True})
    end = data10['jobs']['1']['execution_record']['spans'][-1]['stop_utc']
    start = data10['jobs']['2']['execution_record']['spans'][0]['start_utc']
    gap = (dt.datetime.fromisoformat(start)-dt.datetime.fromisoformat(end)).total_seconds()
    for q,z in data10['jobs']['1']['per_qubit'].items():
        z2=data10['jobs']['2']['per_qubit'][q]
        assert z['kHz_per_rad']==z2['kHz_per_rad']
        make_row(10,1,q,148,1,z['repeats'][-1],z2['repeats'][0],[observations10[1][148],observations10[2][1]],
            z['usable'] and z2['usable'],'input/t10/fits-t10.json.gz',
            [f'jobs.1.per_qubit.{q}.repeats[147]',f'jobs.2.per_qubit.{q}.repeats[0]',
             'jobs.1.execution_record.spans[2].stop_utc','jobs.2.execution_record.spans[0].start_utc'],
            'F','between_jobs',0,None,gap,z['kHz_per_rad'],2)
    summaries=summarize(ROWS)
    expected={ 't9j2':(509,77,0),'t9j3':(349,55,0),'t10j1':(9100,125,1),'t10j2':(9033,124,0),'t10j3':(7073,98,0)}
    comparisons=[]
    for key,(nw,nf,ef) in expected.items():
        gotw=summaries[key+':within_span']; gotf=summaries[key+':span_boundary']
        actual=[gotw['events_4khz'],gotw['n_4khz'],gotf['events_4khz'],gotf['n_4khz']]
        target=[0,nw,ef,nf]
        comparisons.append({'job':key,'expected_W_events_trials_F_events_trials':target,'computed':actual,
            'matches':actual==target,'interpretation':'same reading' if actual==target else 'difference in reading the records'})
    supplement_summary=[]
    for job in [1,2,3]:
        for kind in ['boundary','control']:
            for number in sorted(set(r['boundary_or_span'] for r in SUPPLEMENT if r['job']==job and r['kind']==kind)):
                rr=[r for r in SUPPLEMENT if r['job']==job and r['kind']==kind and r['boundary_or_span']==number]
                supplement_summary.append({'test':10,'job':job,'kind':kind,'boundary_or_span':number,'trials':len(rr),
                    'events':sum(r['event_5_se_only'] for r in rr),'event_qubits':[r['qubit'] for r in rr if r['event_5_se_only']],
                    'line_pair_trials_alternative':sum(r['line_pair'] for r in rr)})
    ambiguities=[
      {'topic':'whole job usability','primary':'Every pair satisfying the explicit line observation criterion is eligible, including observations from a job labelled not usable.',
       'alternative':'Apply the whole job usable field first. Exact eligibility and aggregate counts are retained beside.',
       'basis':'v3 section 0 makes the complete eligible set primary. v2 section 2 defines line observations at repeat level. The source test rules also give a whole job filter.'},
      {'topic':'kind persistence','primary':'The destination kind lasts at least two consecutive repeats.',
       'alternative':'Require both the source and destination runs to last at least two consecutive repeats. Both flags and run lengths are recorded for every transition.'},
      {'topic':'excluded exposure','primary':'For a removed pair that touches a straddling repeat, the diagnostic duration is the mean of the endpoint nominal periods. Each endpoint averages its circuits equally across the periods of their assigned spans.',
       'alternative':'The exact elapsed time is unavailable because the provider records no time for an individual circuit. These diagnostic durations are not admitted to fitted exposure.',
       'overlap':'Reason totals overlap when a pair is both non line and straddling. They must not be added.'},
      {'topic':'fitted scan levels and endpoint observations','primary':'The prescribed endpoint thresholds produce zero scan frequency events at both floors.',
       'alternative':'The source fits report level changes estimated across several repeats. Every reported change point is retained separately with its endpoint pair and exclusion. A fitted level change is a different observable and is not inserted into this endpoint process.'},
      {'topic':'event comparison','primary':'The kickoff uses at least for frequency event thresholds and above for the supplementary five standard error comparison. Those relations are used literally.'}
    ]
    provenance={'inputs':'supplied input directory only','input_hashes':hashes,'arithmetic':'float64',
      'python':platform.python_version(),'numpy':np.__version__,'seed':None,'randomness':'none',
      'command':str(Path(sys.executable))+' -I scripts/frequency.py',
      'claim_kind':'computed facts of archived records',
      'indexing':'Repeat indices start at 1. Position and JSON array indices start at 0. Boundaries are numbered 1 and 2.'}
    result={'schema_version':'1.0','provenance':provenance,'span_assignments':ASSIGNMENTS,'rows':ROWS,
      'kind_transitions':TRANSITIONS,'kind_events':[r for r in TRANSITIONS if r['event_destination_persists_two']],
      'alternating_qubits':[{'test':t,'job':j,'qubit':q,'pairs':p} for (t,j,q),p in sorted(ALTERNATING.items())],
      'summaries':summaries,'required_count_comparisons':comparisons,
      'supplementary_five_se':{'rows':SUPPLEMENT,'summaries':supplement_summary},
      'source_fitted_level_changes_separate_observable':LEVEL_CHANGES,'ambiguities':ambiguities}
    output('frequency-ledger.json',result)
    notes={'schema_version':'1.0','required_count_comparisons':comparisons,'summaries':summaries,
      'ambiguities':ambiguities,'between_jobs_gap_s':gap,'supplementary_five_se':supplement_summary,
      'kind_event_count':sum(r['event_destination_persists_two'] for r in TRANSITIONS),
      'kind_event_count_both_runs_alternative':sum(r['event_both_runs_persist_two_alternative'] for r in TRANSITIONS),
      'kind_event_counts_by_test_job':dict(Counter(f"t{r['test']}j{r['job']}" for r in TRANSITIONS if r['event_destination_persists_two'])),
      'alternating_qubit_count':len(ALTERNATING),'rows':len(ROWS),'source_level_change_count':len(LEVEL_CHANGES),
      'scan_boundary_floor_difference_count':sum(r['event_own'] is True for r in ROWS if r['test']==9 and r['trial_class']=='span_boundary')-sum(r['event_4khz'] is True for r in ROWS if r['test']==9 and r['trial_class']=='span_boundary')}
    output('frequency-notes.json',notes)
    with (ROOT/'frequency-commands.log').open('a') as stream:
        stream.write('\nRUN '+provenance['command']+'\nPython '+provenance['python']+' numpy '+provenance['numpy']+'\nNo randomness or seeds\nAll '+str(len(hashes))+' input hashes matched\n'+json.dumps(notes,indent=2)+'\n')
    print(json.dumps(notes,indent=2))


if __name__ == '__main__':
    main()
