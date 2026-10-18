#!/usr/bin/env python3
"""Independent arithmetic and scope audit of this run's final predictions.

Run with a Python runtime providing NumPy and SciPy. The prediction helper is
not imported. Predictive count quantiles use probability recurrences, and the
joint probability interval is checked by numerical integration.
"""
from pathlib import Path
from datetime import datetime, timezone
import gzip
import hashlib
import json
import math
import sys

import numpy as np
import scipy
from scipy import integrate, optimize, special, stats

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    return json.loads((ROOT / name).read_text())


def digest(name):
    return hashlib.sha256((ROOT / name).read_bytes()).hexdigest()


def audit():
    pred = load("predictions-model-01-v3.json")
    rates = load("rates-model-01-v3.json")
    monitor = load("monitor11-ledger.json")
    shuffled = load("shuffled-stamp-ledger.json")
    normalized = load("normalized-trials.json")["rows"]
    events = load("events-model-01-v3.json")
    md = (ROOT / "predictions-model-01-v3.md").read_text()
    result = dict(audited_utc=datetime.now(timezone.utc).isoformat(),
                  kind="Independent checks of computed predictions and stated scope",
                  prediction_written_utc=pred["written_utc"],
                  prediction_json_sha256=digest("predictions-model-01-v3.json"),
                  prediction_markdown_sha256=digest("predictions-model-01-v3.md"),
                  versions=dict(python=sys.version, numpy=np.__version__, scipy=scipy.__version__),
                  methods="Separate probability formulas, integer PMF recurrences, numerical integration of the joint posterior probability, and direct source mask recounts",
                  checks=[], findings=[], section7_coverage=[])

    def check(name, passed, detail=None):
        row = dict(check=name, passed=bool(passed))
        if detail is not None:
            row["detail"] = detail
        result["checks"].append(row)
        return bool(passed)

    def close(name, observed, expected, rel=2e-11, absolute=2e-12):
        return check(name, np.allclose(observed, expected, rtol=rel, atol=absolute),
                     dict(observed=observed, independently_computed=expected))

    def walk(obj, path=""):
        if isinstance(obj, dict):
            yield path, obj
            for key, val in obj.items():
                yield from walk(val, path + "." + key)
        elif isinstance(obj, list):
            for k, val in enumerate(obj):
                yield from walk(val, path + f"[{k}]")

    def resolve_rate(path):
        value = rates
        remaining = path
        while remaining:
            matches = [key for key in value if remaining == key or remaining.startswith(key + ".")]
            key = max(matches, key=len)
            value = value[key]
            remaining = remaining[len(key):].lstrip(".")
        return value

    def comparable_rate(rate):
        return {k: v for k, v in rate.items() if k != "row_ids"}

    rate_values = [comparable_rate(v) for _, v in walk(rates) if "posterior" in v and "family" in v]
    prediction_nodes = [(path, v) for path, v in walk(pred) if "source_rate" in v]
    check("All scalar prediction source rates occur in the frozen rates file",
          all(v["source_rate"] in rate_values for _, v in prediction_nodes))
    for path, node in prediction_nodes:
        r = node["source_rate"]
        if "rate_path" in node:
            check(path + " source rate path", r == comparable_rate(resolve_rate(node["rate_path"])))
        if r["family"] == "binomial":
            a, b = r["posterior"]["alpha"], r["posterior"]["beta"]
            n = node["trials"]
            p0 = math.exp(special.betaln(a, b + n) - special.betaln(a, b))
            mean_count = n * a / (a + b)
            transform = lambda p: 1 - (1 - p) ** n
            probability = p0
            cumulative = p0
            values = [p0]
            for k in range(1, n + 1):
                probability *= (n - k + 1) * (a + k - 1) / (k * (b + n - k))
                cumulative += probability
                values.append(cumulative)
            bounds = [next(k for k, c in enumerate(values) if c >= q) for q in (0.05, 0.95)]
            check(path + " proper Jeffreys binomial parameters", a == r["events"] + 0.5 and b == r["trials"] - r["events"] + 0.5)
        else:
            a, b = r["posterior"]["shape"], r["posterior"]["rate"]
            exposure = node["exposure_s"]
            p0 = (b / (b + exposure)) ** a
            mean_count = a * exposure / b
            transform = lambda lam: 1 - math.exp(-exposure * lam)
            probability = p0
            cumulative = p0
            values = [p0]
            k = 0
            while cumulative < 0.95:
                k += 1
                probability *= (a + k - 1) * exposure / (k * (b + exposure))
                cumulative += probability
                values.append(cumulative)
                assert k < 100000
            bounds = [next(k for k, c in enumerate(values) if c >= q) for q in (0.05, 0.95)]
            check(path + " proper Jeffreys Poisson parameters", a == r["events"] + 0.5 and b == r["exposure_s"])
        close(path + " probability at median", node["probability_at_least_one_at_median"], transform(r["median"]))
        close(path + " parameter probability interval", node["probability_at_least_one_parameter_interval_90"], [transform(r["q05"]), transform(r["q95"])])
        close(path + " integrated probability", node["posterior_predictive_probability_at_least_one"], 1 - p0)
        close(path + " expected count", node["expected_count_posterior_mean"], mean_count)
        check(path + " predictive count interval from PMF recurrence", node["posterior_predictive_count_interval_90"] == bounds,
              dict(observed=node["posterior_predictive_count_interval_90"], independently_computed=bounds))
    result["scalar_prediction_nodes_checked"] = len(prediction_nodes)

    third = pred["third_day"]
    for design, n in (("shuffled", 2), ("monitor", 4)):
        for suffix, floor in (("", "own"), ("_fixed_beside", "fixed0.10")):
            node = third["weight_boundaries_" + design + suffix]
            check("B design matching " + design + suffix,
                  node["source_rate"] == comparable_rate(rates["classes"]["B|" + floor]["design"][design])
                  and node["design"] == node["estimator"] == design and node["trials"] == n)

    joint = third["any_frequency_boundary_or_within"]
    f = rates["pooled"]["F|own"]
    w = rates["pooled"]["W|own"]
    a, b = f["posterior"]["alpha"], f["posterior"]["beta"]
    shape, rate = w["posterior"]["shape"], w["posterior"]["rate"]
    count, time = joint["boundary_trials"], joint["within_exposure_s"]
    p0 = math.exp(special.betaln(a, b + count) - special.betaln(a, b)) * (rate / (rate + time)) ** shape
    close("Joint integrated probability", joint["posterior_predictive_probability_at_least_one"], 1 - p0)
    close("Joint probability at median rates", joint["probability_at_median_rates"], 1 - (1 - f["median"]) ** count * math.exp(-time * w["median"]))

    def joint_cdf(probability):
        limit = -math.log1p(-probability)
        def integrand(u):
            p = -math.expm1(-u / count)
            log_beta_pdf = (a - 1) * math.log(p) + (b - 1) * math.log1p(-p) - special.betaln(a, b)
            gamma_cdf = special.gammainc(shape, rate * (limit - u) / time)
            return math.exp(log_beta_pdf - u / count) / count * gamma_cdf
        return integrate.quad(integrand, 0, limit, epsabs=1e-10, epsrel=1e-10, limit=200)[0]

    exact_quantiles = [optimize.brentq(lambda x: joint_cdf(x) - q, 1e-10, 0.9, xtol=1e-13) for q in (0.05, 0.5, 0.95)]
    observed_quantiles = [joint["probability_parameter_interval_90"][0], joint["probability_posterior_median"], joint["probability_parameter_interval_90"][1]]
    cdfs = [joint_cdf(q) for q in observed_quantiles]
    differences = [abs(got - target) for got, target in zip(cdfs, (0.05, 0.5, 0.95))]
    tolerances = [5 * math.sqrt(q * (1 - q) / pred["draws_for_joint_parameter_interval"]) for q in (0.05, 0.5, 0.95)]
    check("Joint simulated quantiles agree with numerical integration within five Monte Carlo standard errors",
          all(d <= t for d, t in zip(differences, tolerances)),
          dict(saved_quantiles=observed_quantiles, integrated_quantiles=exact_quantiles,
               integrated_cdfs_at_saved_quantiles=cdfs, cdf_tolerances=tolerances))
    rng = np.random.default_rng(pred["seed"])
    ps = rng.beta(a, b, pred["draws_for_joint_parameter_interval"])
    ls = rng.gamma(shape, 1 / rate, pred["draws_for_joint_parameter_interval"])
    draws = 1 - (1 - ps) ** count * np.exp(-time * ls)
    close("Joint seeded simulation reproducibility", observed_quantiles, np.quantile(draws, [0.05, 0.5, 0.95]).tolist(), absolute=2e-14)

    for key, node in pred["even_odds"].items():
        r = resolve_rate(node["rate_path"])
        a, b = r["posterior"]["shape"], r["posterior"]["rate"]
        close("Even odds at median " + key, node["at_posterior_median_rate"], math.log(2) / r["median"])
        close("Even odds interval order " + key, node["parameter_interval_90"], [math.log(2) / r["q95"], math.log(2) / r["q05"]])
        time = node["posterior_predictive_even_odds_time"]
        close("Integrated even odds survival " + key, (b / (b + time)) ** a, 0.5)

    t10 = json.loads(gzip.decompress((ROOT / "input/t10/fits-t10.json.gz").read_bytes()))
    qset = set(map(int, t10["jobs"]["1"]["qubits"]))
    check("Source set S identity", pred["scan_monitor"]["set_S"]["qubits"] == sorted(qset) and len(qset) == 68)
    for design, test, job in (("scan", 9, 2), ("monitor", 10, 1)):
        eligible = [r for r in normalized if r["test"] == test and r["job"] == job and r["qubit"] in qset and r["floor"] == "4kHz" and r["pool"] == "main" and r["included"]]
        b = [r for r in eligible if r["channel"] == "F"]
        w = [r for r in eligible if r["channel"] == "W"]
        node = pred["scan_monitor"][design]
        check("Source boundary mask " + design, node["template_boundary_trials"] == len(b))
        close("Source exposure mask " + design, node["template_within_exposure_s"], math.fsum(r["exposure_s"] for r in w))
        check("All eligible scenario " + design, node["all_set_S_boundaries_eligible_scenario"]["trials"] == 2 * len(qset))

    written = datetime.fromisoformat(pred["written_utc"]).timestamp()
    source_checks = []
    for name, saved in pred["source_hashes"].items():
        entry = dict(file=name, current_sha256=digest(name), saved_sha256=saved,
                     hash_matches=digest(name) == saved,
                     mtime_before_prediction=(ROOT / name).stat().st_mtime <= written)
        source_checks.append(entry)
    check("Frozen source hashes match", all(x["hash_matches"] for x in source_checks), source_checks)
    check("Frozen source modification times precede prediction creation", all(x["mtime_before_prediction"] for x in source_checks))
    check("Hashed events embed the monitor source", events["monitor11"] == monitor)
    check("Hashed events embed the shuffled source", events["shuffled_weight_stamps_copies"] == shuffled)
    check("Prediction files follow all frozen source modification times",
          all((ROOT / "predictions-model-01-v3.json").stat().st_mtime >= (ROOT / name).stat().st_mtime and
              (ROOT / "predictions-model-01-v3.md").stat().st_mtime >= (ROOT / name).stat().st_mtime for name in pred["source_hashes"]))
    result["freeze_order_scope"] = "Checks current hashes and local recorded file times. The command trace records generation order. These checks make no claim about a future hardware run."
    missing = [name for name in ("normalized-trials.json", "scripts/write_predictions.py", "scripts/statistics_core.py") if name not in pred["source_hashes"]]
    if missing:
        result["findings"].append(dict(severity="provenance improvement", files=missing,
            description="Direct dependencies are outside the prediction source hash map. The final package manifest may cover them, but adding them here makes the prediction freeze self contained."))

    # The supplied scatter statistic uses the arithmetic mean with slightly
    # unequal individual errors, so an ordinary chi squared reference is an
    # equal variance approximation. Preserve that distinction in this audit.
    scatter_rows = []
    for x in monitor["per_span"]:
        errors = np.asarray([monitor["repeat_series"][str(x["job"])][k - 1]["se_w"] for k in x["repeats"]])
        n = len(errors)
        exact_expectation = (n - 2 + float(sum(errors ** 2) * sum(1 / errors ** 2)) / n ** 2) / (n - 1)
        scatter_rows.append(dict(job=x["job"], span=x["span"], exact_gaussian_expectation_chi2_per_dof=exact_expectation,
                                 root_expected_sample_variance=math.sqrt(float(np.mean(errors ** 2)))))
    result["scatter_reference_detail"] = scatter_rows
    scatter_text = json.dumps(third["within_span_scatter"]).lower()
    if "approxim" not in scatter_text:
        result["findings"].append(dict(severity="small wording correction",
            description="The chi squared reference for an arithmetic mean with unequal errors is an equal variance approximation. The exact expected value differs from one by at most 0.0000037 here. The displayed square root of mean variance is a noise scale rather than the expectation of sample standard deviation."))

    coverage = [
        ("7.1 shuffled and monitor B probabilities", "answered", "Matching design posteriors and estimators, with two and four boundaries"),
        ("7.1 within weight probability over about 170 seconds", "answered", "W_B posterior and declared exposure"),
        ("7.1 expected within scatter", "explicitly unavailable as a kinetic prediction", "No scatter law is specified by the event rate; a conditional noise reading is supplied separately"),
        ("7.1 any phase event at boundaries or within spans", "answered", "Joint probability uses conditional independence with unequal own floor transfer caveat"),
        ("7.1 weight change between monitor jobs", "explicitly unavailable", "The five fitted channels specify no gap probability; one gap trial is reported separately"),
        ("7.1 frame movement across a stamp", "scoped answer", "S composite probability is given; P frame probability is not identified by S detuning or kind"),
        ("7.1 split within 0.5 kHz of 44.7", "reading only", "One eligible crossing supplies no fitted split spread or sampling law"),
        ("7.2 scan and monitor on set S", "answered with scenarios", "Source mask and all 68 eligible qubit scenarios are explicit; future errors determine the actual mask"),
        ("7.3 even odds at both floors", "answered", "Frequency and weight parameter time intervals and integrated time are distinct"),
        ("7.4 predictive intervals and counterconditions", "answered", "Intervals declared per scenario; any weight event in 1000 eligible pairs and split change above 1 kHz are explicitly retained")]
    result["section7_coverage"] = [dict(item=a, status=b, reason=c) for a, b, c in coverage]
    check("Gap probability is not substituted by B", "Not identified" in third["between_monitor_jobs_weight"]["status"] and "source_rate" not in third["between_monitor_jobs_weight"])
    check("Split probability is not fitted from one crossing", third["split_near_44p7"]["eligible_crossings"] == 1 and "no fitted probability" in third["split_near_44p7"]["status"])
    check("Noise reading is separate from kinetic prediction", third["within_span_scatter"]["extra_assumption_is_fitted_kinetic_prediction"] is False)
    check("P frame and S detuning remain distinct", "Not separately identified" in third["stamp_composite"]["P_frame_probability_status"])
    check("Countercondition keeps 1000 weight pairs", any(c.get("declared_pairs") == 1000 for c in pred["counterconditions"]))
    check("Countercondition retains split change above 1 kHz", any(c.get("channel") == "split" and "1 kHz" in c["rule"] for c in pred["counterconditions"]))

    # Audit rounded displayed forecasts without reusing the writer's helper.
    labels = ["weight_boundaries_shuffled", "weight_boundaries_monitor", "weight_within", "frequency_boundaries", "frequency_within", "stamp_composite"]
    for key in labels:
        node = third[key]
        check("Markdown numeric forecast " + key, format(node["probability_at_least_one_at_median"], ".6g") in md)
    for key, node in pred["even_odds"].items():
        check("Markdown even odds " + key, format(node["at_posterior_median_rate"], ".6g") in md)
    check("Markdown names probability and predictive count distinctions", "Probability intervals and predictive count intervals answer different questions" in md)
    check("Markdown names four unavailable or scoped observables", all(word in md for word in ("gap probability", "does not predict within span scatter", "does not identify the probability that the P frame moves", "no probability is assigned")))
    result["all_numeric_and_scope_checks_pass"] = all(x["passed"] for x in result["checks"])
    result["check_count"] = len(result["checks"])
    result["failed_checks"] = [x for x in result["checks"] if not x["passed"]]
    result["status"] = "Passed with listed wording or provenance findings" if result["all_numeric_and_scope_checks_pass"] and result["findings"] else ("Passed" if result["all_numeric_and_scope_checks_pass"] else "Failed checks require review")
    (ROOT / "prediction-audit.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({k: result[k] for k in ("status", "check_count", "scalar_prediction_nodes_checked", "findings", "failed_checks")}, indent=2))


if __name__ == "__main__":
    audit()
