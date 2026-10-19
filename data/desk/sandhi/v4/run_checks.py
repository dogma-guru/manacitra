#!/usr/bin/env python3
"""Model 01 v4 own checks, using only this run and the sealed bundle.

All floating point calculations use float64. Choices are recorded in output
before any reported outcomes. This file does not write predictions.
"""
from __future__ import annotations

import argparse
import datetime as dt
import itertools
import hashlib
import concurrent.futures
import json
import math
import os
from pathlib import Path
import sys
import time
import traceback

import numpy as np
import scipy
from scipy.stats import binom

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
MASTER_SEED = 104195001

CHOICES = {
    "dtype": "float64",
    "scope": "Every eligible qubit span is primary.",
    "dwell": "Exclude the first and last run as censored. Compare each state's complete decoded runs with an equal size sample of complete runs from independent stationary chains of the original finite length. Use a two sample KS statistic with a permutation p value that retains ties. The span p is min(1, 2 times the smaller state p). Direct uncensored geometric draws are reported beside.",
    "dwell_limit": "The fitted rates and decoded path came from the same record. The permutation p values do not calibrate estimation of the rates or state decoding.",
    "coswitch": "Pearson correlation on overlapping indices at each lag. Positive lag compares the first path at j with the second at j plus lag. Circular shifts of the second path are sampled uniformly from 1 through N minus 1 with replacement. Lag zero and the maximum signed correlation over all eleven lags have separate null percentiles. All lagwise values are retained.",
    "acf": "Observed autocorrelation is the test 15 centered lagged dot product divided by its full centered sum of squares. Primary prediction is the stationary Markov covariance including the binomial emission variance. A finite window ratio of expected centered covariance sums is beside; it is not the exact expectation of the ratio.",
    "mid": "The observed fraction uses inclusive middle fifth bounds from empirical percentiles 10 and 90 as test 15. The primary model fraction uses the same construction on the exact stationary binomial mixture. The model mass inside the observed bounds is beside.",
    "recovery_selection": "Sort all twelve eligible 143 spans by fitted duty then identity. Select first, lower median and last. Kingston uses first lexicographic eligible identity.",
    "recovery": "Simulate 200 independent stationary spans per selected source using the original row and shot counts. Refit each synthetic span alone, then use 400 independent parametric bootstrap refits per interval unless an explicitly recorded compute reduction applies. Intervals are percentile 5 to 95. All fits and all parameter draws remain in the output.",
    "recovery_emissions": "The record model shares emissions across a job. The recovery experiment requested spans, so each synthetic span estimates its own emission parameters with the same model family. This is a single span recovery check, not coverage for the joint job estimator.",
    "recovery_optimizer": "Each recovery refit uses one optimizer start with all parameters free. The outer simulation refit starts at its generating emissions and rates. Each bootstrap refit starts at the synthetic span fit. The outer data use individual Bernoulli rows; bootstrap data use their exactly equivalent binomial sufficient counts with the same original row and shot counts. The record fits used four starts. Optimizer failures are retained alongside their returned parameter values.",
    "correlation_length": "ell exists only if 0 < 1 minus u minus d < 1. Undefined values are retained and never converted to a positive length. An interval with undefined bootstrap values is labelled conditional on the length existing.",
    "test15_tau": "Where test 15 used three sweeps as a ceiling, its numeric value is reported explicitly as a ceiling rather than a measured correlation time.",
}


def clean(x):
    if isinstance(x, dict):
        return {str(k): clean(v) for k, v in x.items()}
    if isinstance(x, (list, tuple, np.ndarray)):
        return [clean(v) for v in x]
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating, float)):
        return float(x) if np.isfinite(x) else None
    if isinstance(x, np.bool_):
        return bool(x)
    return x


def write_json(path, obj):
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(clean(obj), indent=2, allow_nan=False) + "\n")
    temp.replace(path)


def run_parts(path):
    x = np.asarray(path, dtype=np.int8)
    bounds = np.r_[0, np.flatnonzero(np.diff(x)) + 1, len(x)]
    return np.diff(bounds), x[bounds[:-1]]


def stationary_path(N, u, d, rng):
    b = u / (u + d)
    state = int(rng.random() < b)
    ans = np.empty(N, dtype=np.int8)
    j = 0
    while j < N:
        dwell = int(rng.geometric(d if state else u))
        stop = min(j + dwell, N)
        ans[j:stop] = state
        j = stop
        state = 1 - state
    return ans


def ks_permutation(a, b, rng, permutations=2000):
    a, b = np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64)
    if not len(a) or not len(b):
        return {"status": "not testable", "reason": "No complete dwell in at least one sample", "n_observed": len(a), "n_reference": len(b), "p": None}
    values = np.unique(np.r_[a, b])
    ca = np.searchsorted(np.sort(a), values, side="right") / len(a)
    cb = np.searchsorted(np.sort(b), values, side="right") / len(b)
    stat = float(np.max(np.abs(ca - cb)))
    bins = np.searchsorted(values, np.r_[a, b])
    total = np.bincount(bins, minlength=len(values))
    # Hypergeometric allocation is exactly a permutation of pooled labels.
    draw_counts = rng.multivariate_hypergeometric(total, len(a), size=permutations)
    left = np.cumsum(draw_counts, axis=1) / len(a)
    right = np.cumsum(total[None, :] - draw_counts, axis=1) / len(b)
    null_stats = np.max(np.abs(left - right), axis=1)
    exceed = int(np.count_nonzero(null_stats >= stat - 1e-14))
    return {"status": "computed", "n_observed": len(a), "n_reference": len(b), "statistic": stat, "p": (exceed + 1) / (permutations + 1), "permutations": permutations, "null_exceedances": exceed}


def dwell_check(path, u, d, seed, permutations=2000):
    rng = np.random.default_rng(seed)
    lengths, states = run_parts(path)
    complete_lengths, complete_states = lengths[1:-1], states[1:-1]
    observed = [complete_lengths[complete_states == s] for s in (0, 1)]
    ref = [[], []]
    windows = 0
    # Take complete runs from full independent windows; never complete the
    # terminal run beyond the original observation window.
    while any(len(ref[s]) < len(observed[s]) for s in (0, 1)) and windows < 10000:
        lens, sts = run_parts(stationary_path(len(path), u, d, rng))
        for s in (0, 1):
            ref[s].extend(lens[1:-1][sts[1:-1] == s].tolist())
        windows += 1
    out = {"seed": seed, "finite_window_simulations": windows, "observed_total_runs": len(lengths), "censored_boundary_runs": min(len(lengths), 2), "censored_runs": [{"state": int(states[i]), "observed_length": int(lengths[i])} for i in sorted(set([0, len(lengths) - 1]))], "states": {}}
    for s in (0, 1):
        finite = np.asarray(ref[s][:len(observed[s])], dtype=np.float64)
        direct = rng.geometric(d if s else u, size=len(observed[s])).astype(np.float64)
        primary = ks_permutation(observed[s], finite, rng, permutations)
        alternate = ks_permutation(observed[s], direct, rng, permutations)
        out["states"]["H" if s else "L"] = {"exit_probability": d if s else u, "complete_observed_dwells": observed[s], "finite_window_reference_dwells": finite, "uncensored_geometric_reference_dwells": direct, "finite_window_test": primary, "uncensored_geometric_test": alternate}
    for kind, field in [("finite_window_test", "p_span"), ("uncensored_geometric_test", "p_span_uncensored_alternative")]:
        ps = [out["states"][s][kind]["p"] for s in ("L", "H")]
        out[field] = min(1.0, 2 * min(ps)) if all(p is not None for p in ps) else None
    out["under_0p01"] = out["p_span"] < 0.01 if out["p_span"] is not None else None
    return clean(out)


def acf_observed(x, lags):
    x = np.asarray(x, dtype=np.float64)
    x = x - x.mean()
    denom = np.dot(x, x)
    return [float(np.dot(x[k:], x[:-k]) / denom) if denom > 0 and k < len(x) else None for k in lags]


def acf_check(n, R, qH, qL, b, rho):
    n, R = np.asarray(n, dtype=np.float64), np.asarray(R, dtype=np.float64)
    qH, qL = np.asarray(qH, dtype=np.float64), np.asarray(qL, dtype=np.float64)
    N = n.shape[1]
    lag = np.arange(1, 21)
    ans = []
    for c in range(len(R)):
        signal = float(b * (1 - b) * (qH[c] - qL[c]) ** 2)
        noise = float((b * qH[c] * (1 - qH[c]) + (1 - b) * qL[c] * (1 - qL[c])) / R[c])
        gamma = signal * np.power(rho, np.arange(N, dtype=np.int64))
        gamma[0] += noise
        var0 = gamma[0]
        cov_to_mean = (np.cumsum(gamma) + np.cumsum(gamma)[::-1] - gamma[0]) / N
        var_mean = float(cov_to_mean.mean())
        denom = N * (var0 - var_mean)
        corrected = [float(((N-k) * gamma[k] - cov_to_mean[:N-k].sum() - cov_to_mean[k:].sum() + (N-k)*var_mean) / denom) if denom > 0 else None for k in lag]
        observed = acf_observed(n[c] / R[c], lag)
        predicted = signal * np.power(rho, lag) / var0 if var0 > 0 else np.full(20, np.nan)
        ans.append({"circuit_index": c, "lags": lag, "observed": observed, "model_stationary": predicted, "observed_minus_stationary": np.asarray(observed, dtype=np.float64) - predicted, "model_finite_window_ratio_of_expectations": corrected, "latent_variance": signal, "binomial_emission_variance": noise, "total_variance": float(var0)})
    return clean(ans)


def middle_fraction(n, R, qH, qL, b):
    y = np.asarray(n, dtype=np.float64) / int(R)
    p10, p90 = np.percentile(y, [10, 90])
    observed_bounds = p10 + np.array([0.4, 0.6]) * (p90 - p10)
    observed = float(np.mean((y >= observed_bounds[0]) & (y <= observed_bounds[1])))
    k = np.arange(int(R) + 1)
    pmf = b * binom.pmf(k, int(R), qH) + (1-b) * binom.pmf(k, int(R), qL)
    pmf /= pmf.sum()
    support = k.astype(np.float64) / R
    cdf = np.cumsum(pmf)
    q10, q90 = support[np.searchsorted(cdf, [0.1, 0.9])]
    model_bounds = q10 + np.array([0.4, 0.6]) * (q90 - q10)
    predicted = float(pmf[(support >= model_bounds[0]) & (support <= model_bounds[1])].sum())
    alternate = float(pmf[(support >= observed_bounds[0]) & (support <= observed_bounds[1])].sum())
    return clean({"observed_percentiles_10_90": [p10, p90], "observed_bounds": observed_bounds, "observed_fraction": observed, "model_percentiles_10_90": [q10, q90], "model_bounds": model_bounds, "model_fraction": predicted, "difference_observed_minus_model": observed - predicted, "model_fraction_in_observed_bounds": alternate, "binomial_mixture_support": support, "binomial_mixture_probabilities": pmf})


def lag_corr(x, y, lag):
    x, y = np.asarray(x, dtype=np.float64), np.asarray(y, dtype=np.float64)
    if lag > 0:
        x, y = x[:-lag], y[lag:]
    elif lag < 0:
        x, y = x[-lag:], y[:lag]
    x, y = x-x.mean(), y-y.mean()
    den = math.sqrt(float(np.dot(x, x) * np.dot(y, y)))
    return float(np.dot(x, y) / den) if den > 0 else None


def binary_lag_corr(x, y, lag):
    """Pearson correlation from exact integer sufficient counts for bit paths."""
    x, y = np.asarray(x,dtype=np.int64), np.asarray(y,dtype=np.int64)
    if lag > 0:
        x,y = x[:-lag],y[lag:]
    elif lag < 0:
        x,y = x[-lag:],y[:lag]
    N, sx, sy, sxy = len(x),int(x.sum()),int(y.sum()),int(np.dot(x,y))
    den = math.sqrt(sx*(N-sx)*sy*(N-sy))
    return (N*sxy-sx*sy)/den if den else None


def coswitch_pair(x, y, seed, shifts=200, correlation=lag_corr):
    rng = np.random.default_rng(seed)
    lags = np.arange(-5, 6)
    observed = [correlation(x, y, lag) for lag in lags]
    if any(v is None for v in observed):
        return {"status": "not testable", "reason": "At least one decoded path has zero variance", "seed": seed, "lags": lags, "observed": observed}
    offsets = rng.integers(1, len(y), size=shifts)
    null = np.array([[correlation(x, np.roll(y, int(off)), lag) for lag in lags] for off in offsets], dtype=np.float64)
    observed = np.asarray(observed, dtype=np.float64)
    q99 = np.percentile(null, 99, axis=0)
    max_null = np.max(null, axis=1)
    max_obs = float(np.max(observed))
    max_q99 = float(np.percentile(max_null, 99))
    return clean({"status": "computed", "seed": seed, "lags": lags, "observed": observed, "shifts": shifts, "shift_offsets": offsets, "null_correlations": null, "null_99_percentile_by_lag": q99, "above_99_by_lag": observed > q99, "empirical_p_by_lag": (1 + np.sum(null >= observed[None,:], axis=0)) / (shifts + 1), "lag0_above_99": bool(observed[5] > q99[5]), "max_signed_correlation": max_obs, "max_signed_null_99_percentile": max_q99, "max_signed_above_99": max_obs > max_q99, "max_signed_empirical_p": float((1 + np.sum(max_null >= max_obs)) / (shifts + 1))})


def param_vector(fit):
    span = fit["spans"][0]
    return [span["b"], span.get("ell")] + list(fit["q_H"]) + list(fit["q_L"])


def recovery_case(source_span, source_job_fit, source_fit, seed, draws=200, bootstrap=400, log=None):
    from hmm_model import fit_job, simulate_span
    rng = np.random.default_rng(seed)
    qH, qL = np.asarray(source_job_fit["q_H"], dtype=np.float64), np.asarray(source_job_fit["q_L"], dtype=np.float64)
    names = ["b", "ell"] + [f"q_H[{i}]" for i in range(len(qH))] + [f"q_L[{i}]" for i in range(len(qL))]
    truth = [source_fit["b"], source_fit.get("ell")] + list(qH) + list(qL)
    trials = []
    start = time.perf_counter()
    for trial in range(draws):
        trial_start = time.perf_counter()
        sim_seed = int(rng.integers(0, 2**32 - 1))
        boot_seed = int(rng.integers(0, 2**32 - 1))
        try:
            sim = simulate_span(source_span, source_fit, qH, qL, np.random.default_rng(sim_seed), with_rows=True)
            fit = fit_job([sim], q_init=np.stack([qL, qH]), rate_init=[[source_fit['u'], source_fit['d']]], starts=1, return_series=False)
            estimate = param_vector(fit)
            boot_rng = np.random.default_rng(boot_seed)
            samples, failures = [], []
            for j in range(bootstrap):
                try:
                    bs = simulate_span(sim, fit["spans"][0], fit["q_H"], fit["q_L"], boot_rng)
                    bf = fit_job([bs], q_init=np.stack([fit["q_L"], fit["q_H"]]), rate_init=[[fit['spans'][0]['u'], fit['spans'][0]['d']]], starts=1, return_series=False)
                    if not bf['success']:
                        failures.append({"draw": j, "optimizer_returned_unsuccessful": True, "attempts": bf['attempts']})
                    samples.append(param_vector(bf))
                except Exception as exc:
                    failures.append({"draw": j, "error": repr(exc)})
            intervals, coverage, undefined = [], [], []
            for k, target in enumerate(truth):
                values = [s[k] for s in samples if s[k] is not None and np.isfinite(s[k])]
                undefined.append(len(samples) - len(values))
                interval = np.percentile(values, [5, 95]).tolist() if values else [None, None]
                intervals.append(interval)
                coverage.append(bool(interval[0] <= target <= interval[1]) if target is not None and interval[0] is not None else None)
            trials.append({"trial": trial, "simulation_seed": sim_seed, "bootstrap_seed": boot_seed, "estimate": estimate, "interval90": intervals, "covers_truth": coverage, "undefined_bootstrap_values": undefined, "bootstrap_draws": samples, "bootstrap_failures": failures, "fit_success": fit['success'], "fit_attempts": fit['attempts'], "fit_loglik": fit["loglik"], "elapsed_seconds": time.perf_counter() - trial_start})
        except Exception as exc:
            trials.append({"trial": trial, "simulation_seed": sim_seed, "bootstrap_seed": boot_seed, "error": repr(exc), "traceback": traceback.format_exc(), "elapsed_seconds": time.perf_counter() - trial_start})
        if log and ((trial + 1) % 10 == 0 or trial == 0):
            log(f"recovery {source_span.get('id', '')} trial {trial + 1}/{draws} elapsed {time.perf_counter()-start:.3f}s")
    summary = []
    for k, name in enumerate(names):
        estimates = [t["estimate"][k] for t in trials if "estimate" in t and t["estimate"][k] is not None]
        coverage = [t["covers_truth"][k] for t in trials if "covers_truth" in t and t["covers_truth"][k] is not None]
        conditional = sum(t["undefined_bootstrap_values"][k] > 0 for t in trials if "undefined_bootstrap_values" in t)
        coverage_value = float(np.mean(coverage)) if coverage else None
        summary.append({"parameter": name, "truth": truth[k], "mean_estimate": float(np.mean(estimates)) if estimates else None, "bias": float(np.mean(estimates) - truth[k]) if estimates and truth[k] is not None else None, "defined_estimates": len(estimates), "coverage90": coverage_value, "coverage_denominator": len(coverage), "trials_with_conditional_interval": conditional, "below_0p80": coverage_value < 0.8 if coverage_value is not None else None})
    return clean({"seed": seed, "draws_requested": draws, "bootstrap_draws_requested_per_trial": bootstrap, "parameter_names": names, "truth": truth, "summary": summary, "trials": trials, "elapsed_seconds": time.perf_counter() - start})


def self_check():
    rng = np.random.default_rng(MASTER_SEED)
    identical = ks_permutation([1, 2, 2, 3], [1, 2, 2, 3], rng, 2000)
    assert identical['p'] == 1 and identical['statistic'] == 0
    separated = ks_permutation(np.ones(20), np.full(20, 10), rng, 2000)
    assert separated['p'] <= 1 / 2001 + 1e-15 and separated['statistic'] == 1
    # Compare the finite window autocovariance expression to an explicit
    # centered covariance matrix, independently of the fast expression.
    N, R, b, qH, qL, rho = 30, 40, .3, .85, .1, .7
    n = np.zeros((1, N), dtype=np.float64)
    ac = acf_check(n, [R], [qH], [qL], b, rho)[0]
    sig = b*(1-b)*(qH-qL)**2
    noise = (b*qH*(1-qH)+(1-b)*qL*(1-qL))/R
    index = np.arange(N)
    cov = sig * rho**np.abs(index[:,None]-index[None,:]) + noise*np.eye(N)
    center = np.eye(N)-np.ones((N,N))/N
    covc = center@cov@center
    expected = [float(np.diag(covc, k).sum()/np.trace(covc)) for k in range(1,21)]
    error = float(np.max(np.abs(np.array(expected)-ac['model_finite_window_ratio_of_expectations'])))
    assert error < 1e-13
    mix = middle_fraction(np.arange(41), R, qH, qL, b)
    assert abs(sum(mix['binomial_mixture_probabilities'])-1) < 1e-14
    return {'seed': MASTER_SEED, 'identical_sample_ks_p': identical['p'], 'separated_sample_ks_p': separated['p'], 'finite_window_acf_explicit_covariance_max_error': error, 'mixture_probability_sum': sum(mix['binomial_mixture_probabilities'])}


def log_line(message):
    text = dt.datetime.now(dt.timezone.utc).isoformat() + ' ' + message
    print(text, flush=True)
    with (HERE / 'checks-run.log').open('a') as stream:
        stream.write(text + '\n')


def recovery_worker(args):
    source, jobfit, spanfit, seed, draws, bootstrap = args
    result = recovery_case(source, jobfit, spanfit, seed, draws, bootstrap, log_line)
    result['source_id'] = source['id']
    result['original_R'] = source['R']
    result['original_shots'] = len(source['n'][0])
    return result


def audit_completed_output(output_path, pilot_path):
    """Recompute summaries from retained draws and compare the preserved pilot."""
    current = json.loads(output_path.read_text())
    pilot = json.loads(pilot_path.read_text())
    assert current['status'] == 'complete'
    out = {'pilot_file':str(pilot_path.name),'pilot_sha256':hashlib.sha256(pilot_path.read_bytes()).hexdigest(),'production_outer_trials':0,'production_bootstrap_refits':0,'summary_recomputation':{},'pilot_comparison':{},'failures_retained':{'outer_exceptions':0,'outer_optimizer_unsuccessful':0,'bootstrap_failures':0}}
    for sid, case in current['recovery'].items():
        max_interval_error = 0.0
        coverage_flags_equal = True
        estimates = []
        coverages = []
        for trial in case['trials']:
            out['production_outer_trials'] += 1
            if 'error' in trial:
                out['failures_retained']['outer_exceptions'] += 1
                continue
            out['failures_retained']['outer_optimizer_unsuccessful'] += not trial['fit_success']
            out['failures_retained']['bootstrap_failures'] += len(trial['bootstrap_failures'])
            draws = np.asarray(trial['bootstrap_draws'],dtype=np.float64)
            out['production_bootstrap_refits'] += len(draws)
            ci = np.nanpercentile(draws,[5,95],axis=0).T
            saved = np.asarray(trial['interval90'],dtype=np.float64)
            max_interval_error = max(max_interval_error,float(np.nanmax(np.abs(ci-saved))))
            truth = np.asarray(case['truth'],dtype=np.float64)
            recomputed = (ci[:,0]<=truth)&(truth<=ci[:,1])
            valid = np.isfinite(truth)&np.isfinite(ci[:,0])
            coverage_flags_equal &= all(bool(recomputed[k])==trial['covers_truth'][k] for k in np.flatnonzero(valid))
            estimates.append(trial['estimate'])
            coverages.append([float(recomputed[k]) if valid[k] else np.nan for k in range(len(truth))])
        estimate_means = np.nanmean(np.array(estimates,dtype=np.float64),axis=0)
        covers = np.nanmean(np.asarray(coverages,dtype=np.float64),axis=0)
        saved_means = np.array([r['mean_estimate'] for r in case['summary']],dtype=np.float64)
        saved_bias = np.array([r['bias'] for r in case['summary']],dtype=np.float64)
        saved_cov = np.array([r['coverage90'] for r in case['summary']],dtype=np.float64)
        summary = {'max_interval_endpoint_difference':max_interval_error,'all_coverage_flags_equal':coverage_flags_equal,'max_mean_estimate_difference':float(np.nanmax(np.abs(estimate_means-saved_means))),'max_bias_difference':float(np.nanmax(np.abs(estimate_means-np.asarray(case['truth'])-saved_bias))),'max_coverage_difference':float(np.nanmax(np.abs(covers-saved_cov)))}
        out['summary_recomputation'][sid] = summary
        prior = pilot['recovery'][sid]
        comparison = {'parameter_summary_exact_match':case['summary']==prior['summary'],'outer_trial_count_match':len(case['trials'])==len(prior['trials']),'trial_results':[]}
        for trial, previous in zip(case['trials'],prior['trials']):
            row = {'trial':trial['trial']}
            for field in ['estimate','interval90','covers_truth','undefined_bootstrap_values','bootstrap_draws','bootstrap_failures','fit_success']:
                if trial.get(field) != previous.get(field):
                    row[field+'_changed'] = True
                    if field in ('estimate','interval90','bootstrap_draws') and field in trial and field in previous:
                        aa,bb = np.asarray(trial[field],dtype=np.float64),np.asarray(previous[field],dtype=np.float64)
                        row[field+'_max_absolute_difference'] = float(np.nanmax(np.abs(aa-bb))) if aa.shape==bb.shape else None
            if len(row)>1:
                comparison['trial_results'].append(row)
        comparison['changed_trial_count'] = len(comparison['trial_results'])
        out['pilot_comparison'][sid] = comparison
    out['other_tables_exact_match'] = {key:current[key]==pilot[key] for key in ('co_switching','co_switching_summary','fit_against_record','dwell_summary','test15_comparison','recovery_limits')}
    out['count_requirements_met'] = out['production_outer_trials']==800 and out['production_bootstrap_refits']==320000
    out['maximum_summary_recomputation_error'] = max(v for row in out['summary_recomputation'].values() for k,v in row.items() if k!='all_coverage_flags_equal')
    out['algorithm_file_sha256'] = {name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in ('run_checks.py','hmm_model.py','hmm_core.c','hmm_core.dylib')}
    current['completion_audit'] = clean(out)
    write_json(output_path,current)
    log_line('Completion audit ' + json.dumps(clean({k:v for k,v in out.items() if k not in ('pilot_comparison','algorithm_file_sha256')})))
    return out


def audit_binary_correlations(output_path,fits_path):
    current = json.loads(output_path.read_text())
    fits = {f['id']:f for f in json.loads(fits_path.read_text())['spans']}
    old_rows = current['co_switching']
    new_rows = []
    changed = []
    for row in old_rows:
        left,right = row['source_ids']
        new = coswitch_pair(fits[left]['path'],fits[right]['path'],row['seed'],row['shifts'],correlation=binary_lag_corr)
        new.update({k:row[k] for k in ('job','span','qubits','source_ids')})
        if new.get('lag0_above_99')!=row.get('lag0_above_99') or new.get('max_signed_above_99')!=row.get('max_signed_above_99'):
            changed.append({'source_ids':row['source_ids'],'old_lag0_above_99':row.get('lag0_above_99'),'new_lag0_above_99':new.get('lag0_above_99'),'old_max_signed_above_99':row.get('max_signed_above_99'),'new_max_signed_above_99':new.get('max_signed_above_99'),'old_lag0_comparison_margin':row['observed'][5]-row['null_99_percentile_by_lag'][5],'new_lag0_comparison_margin':new['observed'][5]-new['null_99_percentile_by_lag'][5]})
        new_rows.append(new)
    current['co_switching_centered_float_alternative'] = old_rows
    current['co_switching_centered_float_summary'] = current['co_switching_summary']
    current['co_switching'] = new_rows
    current['co_switching_summary'] = {'eligible_pairs':len(new_rows),'testable_pairs':sum(r['status']=='computed' for r in new_rows),'lag0_above_null99':sum(r.get('lag0_above_99',False) for r in new_rows),'max_signed_over_lags_above_null99':sum(r.get('max_signed_above_99',False) for r in new_rows)}
    current['binary_correlation_numerical_correction'] = {'utc':dt.datetime.now(dt.timezone.utc).isoformat(),'reason':'One strict comparison was decided by rounding of centered binary arrays at 2.8 times 10 to the power minus 17. The primary Pearson correlations are recomputed from exact integer bit counts, using the same paths, lags and shift offsets. The original centered floating calculation is retained beside. No statistical threshold or sample changed.','formula':'(N n11 minus n1 n2) divided by sqrt(n1 (N minus n1) n2 (N minus n2))','changed_rows':changed}
    current['choices']['coswitch_numeric'] = current['binary_correlation_numerical_correction']['reason']
    current['completion_audit']['before_binary_correction_other_tables_exact_match'] = current['completion_audit']['other_tables_exact_match'].copy()
    current['completion_audit']['other_tables_exact_match']['co_switching'] = False
    current['completion_audit']['other_tables_exact_match']['co_switching_summary'] = current['co_switching_summary']==current['co_switching_centered_float_summary']
    current['completion_audit']['algorithm_file_sha256']['run_checks.py'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    write_json(output_path,current)
    log_line('Binary correlation numerical correction ' + json.dumps(current['binary_correlation_numerical_correction']) + ' summary ' + json.dumps(current['co_switching_summary']))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', type=Path, default=HERE / 'series-base.json')
    parser.add_argument('--fits', type=Path, default=HERE / 'fits-stage3.json')
    parser.add_argument('--output', type=Path, default=HERE / 'checks-part.json')
    parser.add_argument('--recovery-draws', type=int, default=200)
    parser.add_argument('--bootstrap', type=int, default=400)
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--pilot-only', action='store_true')
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--reduction-reason')
    parser.add_argument('--audit-pilot',type=Path)
    parser.add_argument('--audit-binary-correlations',action='store_true')
    args = parser.parse_args()
    if args.audit_binary_correlations:
        log_line('COMMAND ' + ' '.join([sys.executable, '-I', str(Path(__file__).resolve())] + sys.argv[1:]))
        audit_binary_correlations(args.output,args.fits)
        return
    if args.audit_pilot:
        log_line('COMMAND ' + ' '.join([sys.executable, '-I', str(Path(__file__).resolve())] + sys.argv[1:]))
        audit_completed_output(args.output,args.audit_pilot)
        return
    if (args.bootstrap < 400 or args.recovery_draws < 200) and not args.reduction_reason:
        raise ValueError('Reduced draws require an explicit recorded reason')
    started = time.perf_counter()
    log_line('COMMAND ' + ' '.join([sys.executable, '-I', str(Path(__file__).resolve())] + sys.argv[1:]))
    log_line(f'Python {sys.version.split()[0]} NumPy {np.__version__} SciPy {scipy.__version__} master seed {MASTER_SEED}')
    data = json.loads(args.data.read_text())['spans']
    allfits = json.loads(args.fits.read_text())
    by_id = {f['id']: f for f in allfits['spans']}
    assert len(data) == 27 and set(by_id) == {s['id'] for s in data}, 'Every eligible span must have a fit'
    fingerprints = {str(p.name): hashlib.sha256(p.read_bytes()).hexdigest() for p in [args.data, args.fits]}
    old = json.loads(args.output.read_text()) if args.resume and args.output.exists() else {}
    if old and old.get('input_sha256') != fingerprints:
        raise ValueError('Resume input hashes differ')
    out = {'choices': CHOICES, 'seed': MASTER_SEED, 'versions': {'python': sys.version, 'numpy': np.__version__, 'scipy': scipy.__version__}, 'input_sha256': fingerprints, 'eligible_span_count': len(data), 'self_checks': self_check(), 'co_switching': [], 'recovery': old.get('recovery', {}), 'recovery_draws_requested': args.recovery_draws, 'bootstrap_draws_requested_per_trial': args.bootstrap, 'compute_reduction': args.reduction_reason, 'status': 'section 4'}
    # Section 4 is completed before section 5.
    grouped = {}
    for s in data:
        if s['processor'] == 'ibm_kingston':
            grouped.setdefault((s['job'], s['span']), []).append(s)
    pair_index = 0
    for (job, span), items in sorted(grouped.items()):
        for left, right in itertools.combinations(sorted(items, key=lambda s:s['qubit']), 2):
            result = coswitch_pair(by_id[left['id']]['path'], by_id[right['id']]['path'], MASTER_SEED + 100 + pair_index)
            result.update({'job': job, 'span': span, 'qubits': [left['qubit'], right['qubit']], 'source_ids': [left['id'], right['id']]})
            out['co_switching'].append(result)
            pair_index += 1
    out['co_switching_summary'] = {'eligible_pairs': pair_index, 'testable_pairs': sum(r['status']=='computed' for r in out['co_switching']), 'lag0_above_null99': sum(r.get('lag0_above_99', False) for r in out['co_switching']), 'max_signed_over_lags_above_null99': sum(r.get('max_signed_above_99', False) for r in out['co_switching'])}
    log_line('Section 4 co switching complete for ' + str(pair_index) + ' pairs')
    # Section 5.1. Selection is deterministic, before recovery draws.
    fez = sorted([s for s in data if s['qubit']==143 and s['processor']=='ibm_fez'], key=lambda s:(by_id[s['id']]['b'],s['id']))
    kingston = sorted([s for s in data if s['processor']=='ibm_kingston'], key=lambda s:s['id'])
    selected = [fez[0], fez[(len(fez)-1)//2], fez[-1], kingston[0]]
    out['recovery_selection'] = [{'id':s['id'], 'b':by_id[s['id']]['b'], 'rank': rank} for s, rank in zip(selected, ['lowest of twelve', 'lower median of twelve', 'highest of twelve', 'first lexicographic Kingston'])]
    out['status'] = 'section 5 recovery'
    work = []
    for index, source in enumerate(selected):
        sf = by_id[source['id']]
        jf = allfits['jobs'][sf['group']]['shared_emissions_fit']
        work.append((source,jf,sf,MASTER_SEED+10000+index,args.recovery_draws,args.bootstrap))
    if old.get('recovery_timing_pilot'):
        out['recovery_timing_pilot'] = old['recovery_timing_pilot']
    else:
        pilot = []
        for source, jf, sf, seed, _, _ in work:
            result = recovery_case(source,jf,sf,seed+1000,draws=1,bootstrap=20)
            pilot.append(result)
        seconds = sum(r['elapsed_seconds'] for r in pilot)
        out['recovery_timing_pilot'] = {'trials': pilot, 'total_refits': 84, 'seconds': seconds, 'projected_full_serial_seconds': seconds/84*(4*200*401), 'planned_workers': args.workers}
        log_line('Pilot 84 refits seconds ' + str(seconds) + ' projected full serial seconds ' + str(out['recovery_timing_pilot']['projected_full_serial_seconds']))
    write_json(args.output,out)
    if args.pilot_only:
        log_line('Pilot saved before full recovery')
        return
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as pool:
        pending = {pool.submit(recovery_worker, task): task[0]['id'] for task in work if task[0]['id'] not in out['recovery']}
        for future in concurrent.futures.as_completed(pending):
            sid = pending[future]
            out['recovery'][sid] = future.result()
            write_json(args.output,out)
            log_line('Saved recovery source ' + sid)
    out['recovery_limits'] = [{'source_id':sid, **row} for sid,result in out['recovery'].items() for row in result['summary'] if row['below_0p80']]
    # Section 5.2. No excluded or failed span is dropped from these tables.
    out['fit_against_record'] = []
    out['test15_comparison'] = []
    for i, source in enumerate(sorted(data,key=lambda s:s['id'])):
        f = by_id[source['id']]
        record_c = source['record_c']
        n, R = np.array(source['n'],dtype=np.float64), np.array(source['R'],dtype=np.float64)
        dwell = dwell_check(f['path'],f['u'],f['d'],MASTER_SEED+1000+i)
        mids = [middle_fraction(n[c],R[c],f['q_H'][c],f['q_L'][c],f['b']) for c in range(len(R))]
        out['fit_against_record'].append({'id':source['id'],'job':source['job'],'qubit':source['qubit'],'processor':source['processor'],'test':source['test'],'record_c':record_c,'fit_success':allfits['jobs'][f['group']]['shared_emissions_fit']['success'],'dwell':dwell,'autocorrelation':acf_check(n,R,f['q_H'],f['q_L'],f['b'],f['rho']),'mid_sweep':mids,'record_mid_sweep':mids[record_c]})
        t15 = source['t15']
        ell_s = f['ell']*source['sweep_s'] if f['ell'] is not None else None
        tau = t15.get('tau_c_s')
        out['test15_comparison'].append({'id':source['id'],'source_reference':source.get('t15_reference_source'),'model_duty':f['b'],'test15_threshold_duty':t15['duty_b'],'duty_difference':f['b']-t15['duty_b'],'model_ell_sweeps':f['ell'],'model_ell_seconds':ell_s,'test15_tau_sweeps_used':t15.get('tau_c_sweeps_used'),'test15_tau_seconds':tau,'test15_tau_ceiling':t15.get('tau_c_ceiling'),'test15_tau_word':t15.get('tau_c_word'),'ell_seconds_minus_test15_tau_numeric':ell_s-tau if ell_s is not None and tau is not None else None})
    fail = [r for r in out['fit_against_record'] if r['dwell']['under_0p01']]
    fezfail = [r for r in fail if r['processor']=='ibm_fez' and r['qubit']==143]
    out['dwell_summary'] = {'all_span_count':len(data),'testable_count':sum(r['dwell']['p_span'] is not None for r in out['fit_against_record']),'under_0p01_count':len(fail),'under_0p01_ids':[r['id'] for r in fail],'qubit143_count':len(fez),'qubit143_under_0p01_count':len(fezfail),'qubit143_under_0p01_ids':[r['id'] for r in fezfail],'qubit143_primary_count':9,'qubit143_primary_under_0p01_count':sum(r['test']!='t14' for r in fezfail),'more_than_two_143_fail':len(fezfail)>2,'required_statement':'A two state Markov chain does not describe 143\'s record. The predictions are still issued as the model\'s, with this limit.' if len(fezfail)>2 else None}
    out['status'] = 'complete'
    out['elapsed_seconds_this_command'] = time.perf_counter()-started
    write_json(args.output,out)
    log_line('All checks complete elapsed seconds ' + str(out['elapsed_seconds_this_command']))


if __name__ == '__main__':
    main()
