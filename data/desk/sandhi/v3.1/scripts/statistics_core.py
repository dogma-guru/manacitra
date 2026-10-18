"""Binary64 Jeffreys inference and explicit simulation conventions for run 3.1."""
import math
import numpy as np
from scipy import stats

QUANTILES = np.array([0.05, 0.5, 0.95], dtype=np.float64)

def fit(rows, family):
    rows = [r for r in rows if r['included']]
    n = sum(int(r['event']) for r in rows)
    exposure = float(sum(r['exposure_s'] for r in rows))
    count = len(rows)
    if not count or (family == 'poisson' and exposure <= 0):
        return {'family': family, 'events': n, 'trials': count,
                'exposure_s': exposure, 'status': 'No eligible exposure'}
    if family == 'poisson':
        a, b = n + .5, exposure
        dist = stats.gamma(a, scale=1/b)
        posterior = {'shape': a, 'rate': b}
    else:
        a, b = n + .5, count - n + .5
        dist = stats.beta(a, b)
        posterior = {'alpha': a, 'beta': b}
    lo, median, hi = map(float, dist.ppf(QUANTILES))
    out = {'family': family, 'events': n, 'trials': count, 'exposure_s': exposure,
           'posterior': posterior, 'q05': lo, 'median': median, 'q95': hi,
           'row_ids': [r['id'] for r in rows]}
    if family == 'poisson':
        out['probability_rate_below_1e_minus_4'] = float(dist.cdf(1e-4))
    return out

def lrt_poisson(groups):
    ns = np.asarray([sum(int(r['event']) for r in g) for g in groups], dtype=np.float64)
    es = np.asarray([sum(r['exposure_s'] for r in g) for g in groups], dtype=np.float64)
    if np.any(es <= 0):
        return {'status': 'No exposure in a class'}
    if ns.sum() == 0:
        return {'statistic': 0., 'p_value': 1., 'df': len(groups)-1,
                'note': 'No event contrast; the asymptotic reference cannot establish equal rates'}
    expected = ns.sum() * es / es.sum()
    mask = ns > 0
    stat = float(2*np.sum(ns[mask] * np.log(ns[mask]/expected[mask])))
    return {'statistic': stat, 'p_value': float(stats.chi2.sf(stat,len(groups)-1)),
            'df': len(groups)-1, 'reference': 'Asymptotic likelihood ratio reference'}

def fisher(a, b):
    ea = sum(int(r['event']) for r in a); eb = sum(int(r['event']) for r in b)
    table = [[ea,len(a)-ea],[eb,len(b)-eb]]
    answer = stats.fisher_exact(table, alternative='two-sided')
    odds = float(answer.statistic)
    return {'table': table, 'odds_ratio': odds if math.isfinite(odds) else str(odds),
            'p_value': float(answer.pvalue), 'alternative': 'two sided'}

def min_trials_three(p, target=.9):
    if p <= 0: return None
    low, high = 3, 3
    while stats.binom.sf(2,high,p) < target: high *= 2
    while low < high:
        mid = (low+high)//2
        if stats.binom.sf(2,mid,p) >= target: high=mid
        else: low=mid+1
    return int(low)

def predict(rate, trials=None, exposure=None):
    """Probability parameter interval and integrated count interval are distinct."""
    if rate['family'] == 'binomial':
        a=rate['posterior']['alpha']; b=rate['posterior']['beta']
        any_event=lambda p: float(-np.expm1(trials*np.log1p(-p)))
        dist=stats.betabinom(trials,a,b)
        mean_count=float(trials*a/(a+b))
        integrated_any=float(1-dist.pmf(0))
    else:
        a=rate['posterior']['shape']; b=rate['posterior']['rate']
        any_event=lambda lam: float(-np.expm1(-exposure*lam))
        dist=stats.nbinom(a,b/(b+exposure))
        mean_count=float(exposure*a/b)
        integrated_any=float(1-dist.pmf(0))
    return {'trials': trials, 'exposure_s': exposure,
            'probability_at_least_one_at_median': any_event(rate['median']),
            'probability_at_least_one_parameter_interval_90': [any_event(rate['q05']),any_event(rate['q95'])],
            'posterior_predictive_probability_at_least_one': integrated_any,
            'expected_count_posterior_mean': mean_count,
            'count_at_rate_median': float(trials*rate['median'] if trials is not None else exposure*rate['median']),
            'posterior_predictive_count_interval_90': list(map(int,dist.ppf([.05,.95]))),
            'source_rate': {k:v for k,v in rate.items() if k!='row_ids'}}
