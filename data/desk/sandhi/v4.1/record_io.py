"""Record quantities from the supplied arrays and labels."""
from __future__ import annotations
import collections
import datetime
import gzip
import hashlib
import json
import math
import re
from pathlib import Path
import numpy as np


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def jload(path):
    p = Path(path)
    return json.load(gzip.open(p)) if p.suffix == '.gz' else json.loads(p.read_text())


def native(value):
    if isinstance(value, dict):
        return {str(k): native(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [native(v) for v in value]
    if isinstance(value, np.ndarray):
        return native(value.tolist())
    if isinstance(value, np.generic):
        return native(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def save(path, value):
    Path(path).write_text(json.dumps(native(value), indent=1, allow_nan=False) + '\n')


def acf(x, lags):
    z = np.asarray(x, dtype=np.float64)
    z = z - z.mean()
    den = float(z @ z)
    return [float(z[l:] @ z[:-l] / den) if den > 0 and 0 < l < len(z) else None for l in lags]


def runs(s):
    s = np.asarray(s, dtype=bool)
    changes = np.flatnonzero(s[1:] != s[:-1]) + 1
    bounds = np.r_[0, changes, len(s)]
    return np.diff(bounds), s[bounds[:-1]]


def record_reading(M, duration_s, include_means=True):
    M = np.asarray(M, dtype=np.float64)
    rows, N = M.shape
    p = M.mean(axis=1)
    m = M.mean(axis=0)
    vo = float(m.var(ddof=1))
    vi = float(np.mean(p * (1 - p)) / rows)
    ratio = vo / vi if vi else float('inf')
    word = 'SHARED' if ratio > 3 else 'INDEPENDENT' if ratio < 1.5 else 'UNDECIDED'
    a = acf(m, range(1, min(200, N - 1) + 1))
    target = (1 - vi / vo) / math.e if vo else 0
    below = [j + 1 for j, v in enumerate(a) if v is not None and v < target]
    lag = below[0] if below else min(200, N - 1) + 1
    pp = np.percentile(m, [10, 20, 50, 80, 90])
    threshold = float((pp[0] + pp[4]) / 2)
    threshold2 = float((pp[1] + pp[3]) / 2)
    state = m > threshold
    b = float(state.mean())
    b2 = float((m > threshold2).mean())
    lens, states = runs(state)
    sweep = float(duration_s / N)
    tau = max(3, lag) if word == 'SHARED' else None
    lo, hi = pp[0] + np.array([.4, .6]) * (pp[4] - pp[0])
    rowacf = [acf(row, [1])[0] or 0 for row in M]
    def sd(bb, ll):
        return float(np.sqrt(2 * bb * (1 - bb) * ll / N)) if ll else None
    out = dict(n_rows=rows, n_shots=N, duration_s=duration_s, sweep_s=sweep,
               ratio=ratio, v_obs=vo, v_ind=vi, word_of_the_ratio=word,
               pbar=float(p.mean()), p_rows=p, sweep_lag1_autocorrelation=a[0],
               row_lag1_autocorrelation_mean=float(np.mean(rowacf)), row_lag1_se=1 / math.sqrt(rows*N),
               acf_lags_1_to_200=a, acf_threshold=target, lag_1_over_e=lag,
               lag_found_within_200=bool(below), percentiles_10_20_50_80_90=pp,
               threshold=threshold, threshold_20_80=threshold2, duty_b=b,
               duty_b_at_threshold_20_80=b2, one_minus_b=1-b,
               switches=len(lens)-1, dwell_high_s=float(lens[states].mean()*sweep) if states.any() else None,
               dwell_low_s=float(lens[~states].mean()*sweep) if (~states).any() else None,
               threshold_dwell_lengths=lens, threshold_dwell_states=states,
               n_runs=len(lens), quarter_span_duties=[float(v.mean()) for v in np.array_split(state,4)],
               mid_sweep_fraction_middle_fifth=float(np.mean((m>=lo)&(m<=hi))),
               middle_fifth_bounds=[lo,hi], fraction_between_0p2_and_0p8=float(np.mean((m>.2)&(m<.8))),
               tau_c_read=word=='SHARED' and lag>=3, tau_c_sweeps_used=tau,
               tau_c_s=tau*sweep if tau else None, tau_c_ceiling=lag<3 if tau else None,
               telegraph_sd=sd(b,tau), telegraph_sd_tau_minus_1=sd(b,tau-1 if tau else None),
               telegraph_sd_tau_plus_1=sd(b,tau+1 if tau else None),
               telegraph_sd_at_threshold_20_80=sd(b2,tau))
    if include_means:
        out['sweep_means'] = m
    if N >= 1000:
        out['acf_lags_490_to_510'] = acf(m, range(490, 511))
    out['switch_counts_inflated'] = N == 1000 and out['mid_sweep_fraction_middle_fifth'] > .10
    return out


def exchangeability(M):
    M = np.asarray(M, dtype=np.float64)
    R, N = M.shape
    p = M.mean(axis=1)
    den = float(np.mean(p * (1 - p)) / N)
    alternate = float(np.var(p, ddof=1) / den) if den > 0 and R > 1 else None
    alt_den = float(p.mean() * (1-p.mean())/N)
    ratio = float(np.var(p,ddof=1)/alt_den) if alt_den>0 and R>1 else None
    out = dict(ratio=ratio, mean_row_binomial_denominator_ratio=alternate, dof=R-1,
               primary_definition='Variance of row means with ddof one over pooled mean binomial variance',
               source='t15/read_t15.py within_span_scatter_against_binomial',
               failure_gate='Upper tail probability below 0.01, a declared v4 implementation choice')
    try:
        from scipy.stats import chi2
        out['p_upper'] = float(chi2.sf(ratio*(R-1), R-1)) if ratio is not None else None
        out['flag'] = out['p_upper'] is not None and out['p_upper'] < .01
        out['ratio_interval_90'] = chi2.ppf([.05,.95],R-1)/(R-1)
    except ImportError:
        out.update(p_upper=None, flag=None, note='Scipy is unavailable')
    return out


def two_mode_alternatives(m):
    m = np.asarray(m, dtype=np.float64)
    out = {'defined_test': None, 'status': 'unavailable',
           'reason': 'No two mode test or decision threshold is defined by the supplied test 15 rule or reading script',
           'alternatives_kind': 'Descriptive computed quantities without a decision word',
           'percentiles_10_50_90': np.percentile(m,[10,50,90])}
    for bins in (11,21):
        hist,edges=np.histogram(m,bins=bins,range=(0,1))
        peaks=[i for i in range(bins) if hist[i]>0 and hist[i]>(hist[i-1] if i else -1) and hist[i]>(hist[i+1] if i+1<bins else -1)]
        out[f'histogram_{bins}_bins']={'counts':hist,'edges':edges,'strict_local_peak_bins':peaks}
    return out


def counts_check(arr, rec):
    failures=[]; bit_failures=[]
    for pos,(cts,N) in enumerate(zip(rec['counts'],rec['shots'])):
        M=arr.get(f'p{pos:03d}')
        if M is None or M.shape[0] != N or not np.isin(M,[0,1]).all():
            failures.append({'position':pos,'reason':'Missing array or invalid shape or bit'});continue
        M=M.reshape(N,-1);bits=M.shape[1]
        encoded=np.ascontiguousarray((M[:,::-1]+48).astype(np.uint8)).view(f'S{bits}').ravel()
        observed=collections.Counter(x.decode() for x in encoded)
        expected={k.replace(' ',''):int(v) for k,v in cts.items() if int(v)}
        if dict(observed)!=expected:
            failures.append({'position':pos,'reason':'Histogram differs'})
        ones=np.zeros(bits,dtype=np.int64)
        for k,v in expected.items():ones+=np.array([int(c) for c in k[::-1]],dtype=np.int64)*v
        bad=np.flatnonzero(M.sum(axis=0)!=ones)
        if len(bad):bit_failures.append({'position':pos,'clbits':bad.tolist()})
    return dict(positions=len(rec['counts']),arrays=len(arr),histogram_mismatches=failures,
                marginal_mismatches=bit_failures,pass_check=not failures and not bit_failures and len(arr)==len(rec['counts']))


def read_arrays(path):
    with np.load(path,allow_pickle=False) as z:
        return {k:np.asarray(z[k]).reshape(len(z[k]),-1) for k in z.files}


def meta_spans(meta, rec):
    candidate=meta.get('execution_spans') or meta.get('execution_metadata',{}).get('execution_spans')
    if not candidate:
        candidate=meta.get('result_metadata',{}).get('execution',{}).get('execution_spans')
    recorded=rec.get('execution_metadata',{}).get('execution_spans') or []
    if isinstance(candidate,list) and all('positions' in s for s in candidate):
        spans=[dict(s) for s in sorted(candidate,key=lambda s:s['start_utc'])]
        for i,s in enumerate(spans):
            s.setdefault('span',i)
            if 'duration_s' not in s:
                start=datetime.datetime.fromisoformat(s['start_utc'].replace('Z','+00:00'))
                stop=datetime.datetime.fromisoformat(s['stop_utc'].replace('Z','+00:00'))
                s['duration_s']=(stop-start).total_seconds()
        comparison={'exact_membership_available':True,'source':'array meta','matches_counts':all(s.get('positions')==r.get('positions') for s,r in zip(spans,recorded)) and len(spans)==len(recorded)}
    else:
        spans=sorted(recorded,key=lambda s:s['start_utc'])
        parsed=re.findall(r"start='([^']+)', stop='([^']+)', size=(\d+)",str(candidate))
        comparisons=[]
        for item,s in zip(parsed,spans):
            start,stop,size=item
            comparisons.append(dict(span=s['span'],start_to_second_equal=s['start_utc'][:19].replace('T',' ')==start,
                                    stop_to_second_equal=s['stop_utc'][:19].replace('T',' ')==stop,size_equal=int(size)==s.get('size_shots')))
        comparison={'exact_membership_available':False,'source':'counts execution_metadata.execution_spans',
                    'reason':'Array meta stores rounded span summaries without position membership',
                    'alternatives':{'meta_only':'Membership unavailable; no series can be built',
                                    'counts_exact':'Exact position membership available and used',
                                    'fits_only':'Whole repeat counts available as a comparison only'},
                    'meta_repr':candidate,'summary_comparison':comparisons,'summary_span_count_equal':len(parsed)==len(spans)}
    if not spans:raise ValueError('No usable span membership')
    return spans,comparison


def median_phase(theta):
    theta=np.asarray(theta,dtype=np.float64)
    ref=np.angle(np.exp(1j*theta).mean())
    wrapped=(theta-ref+np.pi)%(2*np.pi)-np.pi
    return float((ref+np.median(wrapped)+np.pi)%(2*np.pi)-np.pi)


def monitor_series(arr, rec, meta, job, qubits=None):
    spans,span_audit=meta_spans(meta,rec)
    pos_span={p:s['span'] for s in spans for p in s['positions']}
    labels=rec['labels'];qcols=rec.get('qubits',[rec.get('qubit',143)])
    repeat_positions=collections.defaultdict(list)
    for i,l in enumerate(labels):
        if l.get('repeat') is not None and l['circuit'] in ('X','Y'):repeat_positions[l['repeat']].append(i)
    whole={s['span']:[k for k,ps in sorted(repeat_positions.items()) if all(pos_span.get(p)==s['span'] for p in ps)] for s in spans}
    straddle=[k for k,ps in sorted(repeat_positions.items()) if len({pos_span.get(p) for p in ps})!=1]
    is14=any(l.get('wait')=='control' for l in labels)
    waits=['antiphase','control'] if is14 else ['monitor']
    ro=[i for i,l in enumerate(labels) if l['circuit'] in ('P10','P01')]
    out=[]
    for col,q in enumerate(qcols):
        if qubits is not None and q not in qubits:continue
        c=float(np.mean([arr[f'p{i:03d}'][:,col].mean() for i in ro]))
        circuit_defs=[];qrecords={};medians={}
        for wait in waits:
            pp={quad:{l['repeat']:i for i,l in enumerate(labels) if l['circuit']==quad and l.get('repeat') is not None and (not is14 or l.get('wait')==wait)} for quad in ['X','Y']}
            theta=[math.atan2(arr[f'p{pp["Y"][k]:03d}'][:,col].mean()-c,arr[f'p{pp["X"][k]:03d}'][:,col].mean()-c) for k in sorted(pp['X'])]
            med=median_phase(theta);qrecords[wait]='Y' if abs(math.sin(med))>abs(math.cos(med)) else 'X';medians[wait]=med
            for quad in ['X','Y']:circuit_defs.append((wait,quad,pp[quad]))
        for s in spans:
            ks=whole[s['span']]
            if len(ks)<2:continue
            circuits=[];n=[];R=[];checks=[];reads=[]
            for wait,quad,positions in circuit_defs:
                selected=[positions[k] for k in ks]
                M=np.stack([arr[f'p{i:03d}'][:,col] for i in selected]).astype(np.float64)
                n.append(M.sum(axis=0));R.append(len(M));checks.append(exchangeability(M));reads.append(record_reading(M,s['duration_s']))
                times=sorted({labels[i].get('t_requested_us') for i in selected if labels[i].get('t_requested_us') is not None})
                circuits.append({'wait':wait,'quadrature':quad,'wait_us':times[0] if len(times)==1 else None,
                                 'wait_us_values':times,'positions':selected,'row_means':M.mean(axis=1),'shot_count':M.shape[1]})
            rc=next(i for i,(wait,quad,_) in enumerate(circuit_defs) if wait==waits[0] and quad==qrecords[waits[0]])
            out.append(dict(id=f'{job}-q{q}-s{s["span"]}',job=job,test=job.split('-')[0],qubit=q,span=s['span'],
                            job_id=rec['job_id'],processor=rec.get('backend'),date=s['start_utc'][:10],
                            n=np.asarray(n,dtype=np.float64),R=np.asarray(R,dtype=np.float64),record_c=rc,
                            duration_s=s['duration_s'],sweep_s=s['duration_s']/len(n[0]),start_utc=s['start_utc'],stop_utc=s['stop_utc'],
                            whole_repeats=ks,straddling_repeats=straddle,circuits=circuits,quadrature_of_record=qrecords,
                            median_phase=medians,exchangeability=checks,exchangeability_flag=any(x.get('flag') for x in checks),
                            readings=reads,t15=reads[rc],span_membership_source=span_audit['source']))
    return out,dict(span_audit=span_audit,whole_repeats={str(k):v for k,v in whole.items()},straddling_repeats=straddle)


def boundary(a,b):
    aa=a.get('t15',a);bb=b.get('t15',b)
    out={'duties':[aa['duty_b'],bb['duty_b']],'difference':bb['duty_b']-aa['duty_b']}
    if aa['word_of_the_ratio']!='SHARED' or bb['word_of_the_ratio']!='SHARED':
        return out|{'word':'NOT READ','combined_sd':None,'ratio':None}
    sd=math.hypot(aa['telegraph_sd'],bb['telegraph_sd']);z=abs(out['difference'])/sd if sd else 0
    return out|{'combined_sd':sd,'ratio':z,'word':'NO CHANGE' if z<=2 else 'BETWEEN' if z<=3 else 'CHANGE'}
