#!/usr/bin/env python3
"""Recompute Test 11 monitor observations and the specified trial ledgers.

Scientific inputs are restricted to the supplied input directory.  Python float
is IEEE 754 binary64 on the recorded runtime.  No random draws are used.
"""
from __future__ import annotations

import hashlib
import json
import math
import platform
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "input"
FIT_FILE = "t11/fits-t11.json"


def load(name):
    return json.loads((INPUT / name).read_text())


def write(name, value):
    (ROOT / name).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def utc(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=timezone.utc)


def wrap(value):
    return (value + math.pi) % (2 * math.pi) - math.pi


def mean(values):
    return math.fsum(values) / len(values)


def gap_class(gap):
    if gap is None:
        return None
    if gap < 0.01:
        return "5 ms"
    if 14 <= gap < 16:
        return "14 to 15 s"
    if gap < 1:
        return "under 1 s"
    if gap <= 3:
        return "1 to 3 s"
    return "over 3 s"


def base(channel, job, source_file):
    return dict(channel=channel, test=11, job=job, qubit=143,
                processor="ibm_fez", design="monitor", boundary=None,
                gap_s=None, gap_class=None, source_file=source_file,
                source_fields=[], included=True, exclusion_reason=None,
                event_own=None, event_fixed=None, event_4khz=None,
                exposure_s=0.0, exposure_own_s=0.0, exposure_4khz_s=0.0,
                trial_exposure_own=0, trial_exposure_fixed=0,
                trial_exposure_4khz=0, stamp="2026-10-17T18:48:16Z")


def run():
    hashes = []
    for line in (INPUT / "SHA256SUMS").read_text().splitlines():
        expected, name = line.split(maxsplit=1)
        name = name.lstrip("*")
        actual = hashlib.sha256((INPUT / name).read_bytes()).hexdigest()
        hashes.append(dict(file=name, matches=actual == expected))
    assert len(hashes) == 48 and all(row["matches"] for row in hashes)
    fits = load(FIT_FILE)
    raws = {j: load(f"t11/counts-t11-job{j}.json") for j in (1, 2, 3)}
    for raw in raws.values():
        assert raw["calibration_at_submission"] == "2026-10-17 14:48:16-04:00"
        assert raw["calibration_after_fetch"] == raw["calibration_at_submission"]
    p = fits["jobs"]["1"]["analysis"]["fits"]["P"]["params"]
    wait_us = 5.6
    r0 = p["A"] * math.exp(-wait_us / p["tau_prime_us"])
    assert abs(r0 - fits["R0"]["value"]) < 1e-14
    khz_per_rad = 1000 / (2 * math.pi * wait_us)
    exchanged = p["b"] > 0.5
    series = {}
    span_stats = []
    checks = []
    execution = {}
    trials = []
    
    for j in (1, 2, 3):
        raw = raws[j]
        spans = sorted(raw["execution_metadata"]["execution_spans"], key=lambda s: s["start_utc"])
        positions = {}
        for s in spans:
            assert abs((utc(s["stop_utc"]) - utc(s["start_utc"])).total_seconds() - s["duration_s"]) < 1e-8
            for pos in s["positions"]:
                assert pos not in positions
                assert s["shots_per_position"][str(pos)] == raw["shots"][pos]
                positions[pos] = s["span"]
        assert set(positions) == set(range(len(raw["labels"])))
        gaps = [(utc(b["start_utc"]) - utc(a["stop_utc"])).total_seconds() for a, b in zip(spans, spans[1:])]
        execution[j] = dict(spans=spans, position_to_span=positions, gaps_s=gaps)
        if j == 1:
            continue
        file = f"t11/counts-t11-job{j}.json"
        prob = []
        for pos, counts in enumerate(raw["counts"]):
            assert set(counts).issubset({"0", "1"})
            assert sum(counts.values()) == raw["shots"][pos]
            prob.append(counts.get("1", 0) / raw["shots"][pos])
        readout_positions = [i for i, label in enumerate(raw["labels"]) if label["circuit"] in ("P10", "P01")]
        assert readout_positions == [0, 1, 298, 299]
        c = mean([prob[i] for i in readout_positions])
        rows = []
        for k in range(1, 149):
            xp, yp = 2 * k, 2 * k + 1
            for pos, quad in ((xp, "X"), (yp, "Y")):
                assert raw["labels"][pos]["repeat"] == k
                assert raw["labels"][pos]["quadrature"] == quad
                assert raw["labels"][pos]["position"] == pos
            px, py = prob[xp], prob[yp]
            radius = math.hypot(px - c, py - c)
            theta = math.atan2(py - c, px - c)
            sigma = math.sqrt((px * (1 - px) / raw["shots"][xp] + py * (1 - py) / raw["shots"][yp]) / 2)
            circuit_spans = [positions[xp], positions[yp]]
            straddles = circuit_spans[0] != circuit_spans[1]
            rows.append(dict(k=k, PX=px, PY=py, theta=theta, r=radius,
                             sigma=sigma, s=max(0.02, sigma / radius),
                             positions=[xp, yp], spans_of_circuits=circuit_spans,
                             span=None if straddles else circuit_spans[0],
                             straddles=straddles, source_file=file,
                             source_fields=[f"counts[{xp}]", f"counts[{yp}]", f"shots[{xp}]", f"shots[{yp}]", "labels", "execution_metadata.execution_spans"]))
        circle_mean = math.atan2(math.fsum(math.sin(r["theta"]) for r in rows), math.fsum(math.cos(r["theta"]) for r in rows))
        median_phase = statistics.median([circle_mean + wrap(r["theta"] - circle_mean) for r in rows])
        for row in rows:
            near = abs(wrap(row["theta"] - median_phase)) <= math.pi / 2
            sign = -1 if near else 1
            if exchanged:
                sign *= -1
            row.update(w=(1 + sign * row["r"] / r0) / 2,
                       se_w=row["sigma"] / (2 * r0), branch_sign=sign)
        straddlers = [row["k"] for row in rows if row["straddles"]]
        assert straddlers == ({2: [49, 50, 100], 3: [50, 100]}[j])
        assert min(row["r"] for row in rows) >= 0.08
        archived = fits["jobs"][str(j)]["repeats"]
        errors = {key: max(abs(row[key] - other[key]) for row, other in zip(rows, archived)) for key in ("PX", "PY", "theta", "r", "sigma", "s", "w", "se_w")}
        span_match = all(row["span"] == other["span"] and row["straddles"] == other["straddles"] for row, other in zip(rows, archived))
        assert max(errors.values()) < 1e-12 and span_match
        checks.append(dict(job=j, c=c, median_phase=median_phase, circular_mean=circle_mean,
                           R0=r0, max_abs_difference_from_archived=errors,
                           span_assignment_matches=span_match, straddling_repeats=straddlers,
                           source_file=file, comparison_file=FIT_FILE,
                           comparison_field=f"jobs.{j}.repeats"))
        series[j] = rows
        periods = {}
        for s in spans:
            sid = s["span"]
            whole = [row for row in rows if row["span"] == sid]
            n = len(whole)
            period = s["duration_s"] / n
            periods[sid] = period
            weights = [row["w"] for row in whole]
            ses = [row["se_w"] for row in whole]
            avg = mean(weights)
            sd = statistics.stdev(weights)
            propagated = math.sqrt(math.fsum(se * se for se in ses)) / n
            scatter_se = sd / math.sqrt(n)
            var_weights = [1 / se ** 2 for se in ses]
            total_weight = math.fsum(var_weights)
            xbar = math.fsum(row["k"] * w for row, w in zip(whole, var_weights)) / total_weight
            ybar = math.fsum(y * w for y, w in zip(weights, var_weights)) / total_weight
            sxx = math.fsum(w * (row["k"] - xbar) ** 2 for row, w in zip(whole, var_weights))
            slope = math.fsum(w * (row["k"] - xbar) * (y - ybar) for row, y, w in zip(whole, weights, var_weights)) / sxx
            intercept = ybar - slope * xbar
            slope_se = math.sqrt(1 / sxx)
            chi2 = math.fsum(((y - avg) / se) ** 2 for y, se in zip(weights, ses))
            linear_chi2 = math.fsum(((row["w"] - intercept - slope * row["k"]) / row["se_w"]) ** 2 for row in whole)
            stat = dict(test=11, job=j, qubit=143, processor="ibm_fez", design="monitor",
                        span=sid, repeats=[row["k"] for row in whole], n_repeats=n,
                        mean_w=avg, se=max(propagated, scatter_se), se_propagated=propagated,
                        se_scatter=scatter_se, sd_w=sd, chi2=chi2, dof=n - 1,
                        chi2_per_dof=chi2 / (n - 1), weighted_mean_w=ybar,
                        weighted_slope_w_per_repeat=slope, weighted_slope_se=slope_se,
                        slope_z=slope / slope_se, weighted_intercept_w=intercept,
                        linear_fit_chi2=linear_chi2, linear_fit_dof=n - 2,
                        repeat_period_s=period, within_trials=n - 1,
                        within_exposure_s=(n - 1) * period,
                        conditional_expected_sd_from_propagated_errors=math.sqrt(mean([se ** 2 for se in ses])),
                        source_file=file, source_fields=["counts", "shots", "labels", f"execution_metadata.execution_spans[{sid}]"],
                        R0_source=dict(file=FIT_FILE, field="jobs.1.analysis.fits.P.params"))
            other = fits["jobs"][str(j)]["weight"]["per_span"][sid]
            assert abs(stat["mean_w"] - other["mean_w"]) < 1e-12
            span_stats.append(stat)
        execution[j]["periods_s"] = periods
        for a, b in zip(rows, rows[1:]):
            eligible = not a["straddles"] and not b["straddles"] and a["span"] == b["span"]
            touched = sorted(set(a["spans_of_circuits"] + b["spans_of_circuits"]))
            nominal_period = mean([periods[sid] for sid in touched])
            for channel in ("W", "W_B"):
                trial = pair_trial(channel, j, file, a, b, khz_per_rad, eligible)
                trial["exposure_s"] = periods[a["span"]] if eligible else 0.0
                trial["exposure_own_s"] = trial["exposure_s"]
                trial["exposure_4khz_s"] = trial["exposure_s"] if channel == "W" and trial["eligible_4khz"] else 0.0
                trial["nominal_excluded_exposure_s"] = 0.0 if eligible else nominal_period
                trial["nominal_excluded_exposure_convention"] = "Mean of the repeat periods of the spans touched by the four circuits. This is not fitted exposure."
                if not eligible and len(touched) == 2:
                    trial.update(boundary=touched[0] + 1, gap_s=gaps[touched[0]],
                                 gap_class=gap_class(gaps[touched[0]]))
                trials.append(trial)
        for sid in (0, 1):
            before = [row for row in rows if row["span"] == sid]
            after = [row for row in rows if row["span"] == sid + 1]
            a, b = before[-1], after[0]
            expected_pair = {2: [[48, 51], [99, 101]], 3: [[49, 51], [99, 101]]}[j][sid]
            assert [a["k"], b["k"]] == expected_pair
            gap = gaps[sid]
            trial = pair_trial("F", j, file, a, b, khz_per_rad, True)
            trial.update(boundary=sid + 1, gap_s=gap, gap_class=gap_class(gap),
                         trial_exposure_own=1, trial_exposure_4khz=int(trial["eligible_4khz"]))
            trials.append(trial)
            left = next(s for s in span_stats if s["job"] == j and s["span"] == sid)
            right = next(s for s in span_stats if s["job"] == j and s["span"] == sid + 1)
            btrial = weight_span_trial("B", j, file, left, right, before[-3:], after[:3])
            btrial.update(boundary=sid + 1, gap_s=gap, gap_class=gap_class(gap),
                          bridge_pair=expected_pair, bridge_weight_difference=b["w"] - a["w"],
                          bridge_weight_se=math.hypot(a["se_w"], b["se_w"]),
                          bridge_weight_rule_threshold=max(0.10, 5 * math.hypot(a["se_w"], b["se_w"])),
                          bridge_weight_rule_event=abs(b["w"] - a["w"]) > max(0.10, 5 * math.hypot(a["se_w"], b["se_w"])))
            trials.append(btrial)

    gap23 = (utc(execution[3]["spans"][0]["start_utc"]) - utc(execution[2]["spans"][-1]["stop_utc"])).total_seconds()
    left = next(s for s in span_stats if s["job"] == 2 and s["span"] == 2)
    right = next(s for s in span_stats if s["job"] == 3 and s["span"] == 0)
    bt = weight_span_trial("B_gap", [2, 3], ["t11/counts-t11-job2.json", "t11/counts-t11-job3.json"], left, right, series[2][-3:], series[3][:3])
    bt.update(gap_s=gap23, gap_class="between jobs", pooled_with_B=False, estimator="monitor")
    trials.append(bt)
    ft = pair_trial("F_gap", [2, 3], ["t11/counts-t11-job2.json", "t11/counts-t11-job3.json"], series[2][-1], series[3][0], khz_per_rad, True)
    ft.update(gap_s=gap23, gap_class="between jobs", pooled_with_F=False, trial_exposure_own=1,
              exceeds_five_combined_se=abs(ft["signed_phase_difference_rad"]) > 5 * ft["combined_phase_se_rad"])
    trials.append(ft)
    gap12 = (utc(execution[2]["spans"][0]["start_utc"]) - utc(execution[1]["spans"][-1]["stop_utc"])).total_seconds()
    mixed = base("B_gap", [1, 2], [FIT_FILE, "t11/counts-t11-job1.json", "t11/counts-t11-job2.json"])
    mixed.update(included=False, exclusion_reason="different estimators", design="shuffled to monitor",
                 gap_s=gap12, gap_class="between jobs", pooled_with_B=False,
                 source_fields=["jobs.1.span_readings_A26.weight_per_span[2]", "execution_metadata.execution_spans"],
                 estimators=["shuffled implied position weight", "monitor weight from radius and R0"])
    trials.append(mixed)

    means3 = [[round(s["mean_w"], 3) for s in span_stats if s["job"] == j] for j in (2, 3)]
    assert means3 == [[0.340, 0.392, 0.360], [0.323, 0.350, 0.237]]
    summary = {}
    for channel in ("W", "F", "W_B", "B", "B_gap", "F_gap"):
        selected = [t for t in trials if t["channel"] == channel and t["included"]]
        summary[channel] = dict(trials=len(selected), excluded_pairs=sum(t["channel"] == channel and not t["included"] for t in trials),
                                events_own=sum(t["event_own"] is True for t in selected),
                                events_fixed=sum(t["event_fixed"] is True for t in selected),
                                events_five_se=sum(t.get("event_five_se") is True for t in selected),
                                trials_4khz=sum(t.get("eligible_4khz", False) for t in selected),
                                events_4khz=sum(t["event_4khz"] is True for t in selected),
                                exposure_own_s=math.fsum(t["exposure_own_s"] for t in selected),
                                exposure_4khz_s=math.fsum(t["exposure_4khz_s"] for t in selected),
                                censored_exposure_s=math.fsum(t["exposure_own_s"] for t in selected if t.get("censored_4khz", False)))
    assert summary["W_B"]["trials"] == 285
    assert summary["W_B"]["events_own"] == 0
    assert summary["W_B"]["events_five_se"] == 0
    summary["W_B"]["five_se_beside"] = dict(
        threshold="Five combined standard errors with no fixed 0.10 minimum",
        events=summary["W_B"]["events_five_se"], trials=285,
        exposure_s=summary["W_B"]["exposure_own_s"],
        same_counts_as_rule_floor=True,
        reading="The zero event counts and exposure are equal at both floors, so the fitted rates and even odds times are equal.")
    assert summary["B"]["events_own"] == 4
    metadata = dict(kind="Computed facts of the archived records", dtype="IEEE 754 binary64", random_seed=None,
                    seed_note="No random draws", python=sys.version, platform=platform.platform(),
                    input_hash_count=len(hashes), input_hashes_match=True,
                    frequency_comparison="At least the record threshold as inherited from version 2",
                    weight_comparison="Exceeds five combined errors for span means; nearest three plain means at least 0.10 beside",
                    uncertainty_scope="The monitor error formula is conditional on R0 and the readout midpoint. Shared uncertainty in R0 and the midpoint is not in the rule. Sensitivity to R0 is tabulated separately.",
                    within_weight_comparison="Absolute adjacent weight change exceeds max(0.10, five combined errors). Scatter and slope describe resolution beyond adjacent events.")
    write("monitor11-ledger.json", dict(metadata=metadata, summary=summary, trials=trials,
                                         per_span=span_stats, repeat_series=series,
                                         execution_mapping=execution, raw_recomputation_checks=checks))
    job1_spans = fits["jobs"]["1"]["span_readings_A26"]["weight_per_span"]
    sensitivity = []
    for stat in span_stats:
        w = stat["mean_w"]
        minus = 0.5 + (w - 0.5) / 0.9
        plus = 0.5 + (w - 0.5) / 1.1
        sensitivity.append(dict(job=stat["job"], span=stat["span"], mean_w=w,
                                R0_minus_10_percent=r0 * 0.9, w_R0_minus_10_percent=minus,
                                shift_R0_minus_10_percent=minus - w,
                                R0_plus_10_percent=r0 * 1.1, w_R0_plus_10_percent=plus,
                                shift_R0_plus_10_percent=plus - w,
                                derivative_dw_dR0=(0.5 - w) / r0))
    estimators = dict(kind="Computed facts and stated estimator assumptions", reconciliation="No reconciliation is attempted. No value from one estimator is corrected by the other.",
                      source_scope="Supplied input archive only", same_stamp="2026-10-17T18:48:16Z",
                      job1=dict(design="shuffled", whole_job_b=p["b"],
                                whole_job_b_ci90=fits["jobs"]["1"]["analysis"]["deciding"]["b_ci90"],
                                per_span=job1_spans,
                                source_file=FIT_FILE,
                                source_fields=["jobs.1.analysis.fits.P.params.b", "jobs.1.analysis.deciding.b_ci90", "jobs.1.span_readings_A26.weight_per_span"],
                                assumptions="P is held at its fitted values. Each reported mean treats the positions it averages as having one weight. The span mean is the inverse variance mean over positions passing the lever."),
                      monitor=dict(per_span=span_stats, estimator="w=(1 plus branch_sign times r/R0)/2",
                                   assumptions="Both lines have equal amplitude and decay and are exactly at antiphase. R0 and the midpoint are held fixed in the stated standard errors. Branches follow the job median phase and the fitted b."),
                      R0=dict(value=r0, source_file=FIT_FILE,
                              source_fields=["jobs.1.analysis.fits.P.params.A", "jobs.1.analysis.fits.P.params.tau_prime_us"],
                              formula="A exp(negative 5.6/tau_prime_us)", branches_exchanged=exchanged,
                              fixed_wait_us=wait_us,
                              antiphase_wait_from_fit_us=1 / (4 * p["delta_MHz"]),
                              relative_phase_at_wait_rad=4 * math.pi * p["delta_MHz"] * wait_us,
                              sensitivity=sensitivity, sensitivity_formula="w(f R0)=0.5+(w(R0)-0.5)/f with radius and branch held fixed"),
                      job1_to_job2=dict(last_span_stop_utc=execution[1]["spans"][-1]["stop_utc"],
                                       first_span_start_utc=execution[2]["spans"][0]["start_utc"], gap_s=gap12,
                                       source_files=["t11/counts-t11-job1.json", "t11/counts-t11-job2.json"],
                                       source_fields=["execution_metadata.execution_spans[2].stop_utc", "execution_metadata.execution_spans[0].start_utc"],
                                       eligible_weight_trial=False, exclusion_reason="different estimators"),
                      job2_to_job3=dict(gap_s=gap23, last_span_to_first_span_trial=bt,
                                       endpoint_pair_beside=dict(weight_difference=series[3][0]["w"] - series[2][-1]["w"],
                                                                combined_se=math.hypot(series[3][0]["se_w"], series[2][-1]["se_w"]),
                                                                source_file=FIT_FILE, source_field="gap_between_jobs_2_and_3")))
    write("estimators-model-01-v3.json", estimators)
    notes = dict(summary=summary, span_means_rounded3=means3, job1_to_job2_gap_s=gap12,
                 job2_to_job3_gap_s=gap23, boundary_rows=[t for t in trials if t["channel"] in ("F", "B", "B_gap", "F_gap")],
                 raw_recomputation=checks,
                 source_disagreements=[dict(source_file="t11/report-t11.md", field="section 6 item 2",
                    quoted_fragment="One weight difference does",
                    arithmetic="The quoted difference is 4.8 standard errors. Direct recomputation is below five. The original endpoint rule has zero boundary weight events; the span mean rule has four.")],
                 conventions=["Span identifiers and circuit assignments come from the provider positions rather than numerical ranges.",
                              "The within pair exposure is the span duration divided by its whole repeat count.",
                              "A span mean uses the larger of propagated error and sample standard deviation divided by the square root of the whole repeat count.",
                              "Scatter chi squared is calculated about the arithmetic mean with the individual propagated weight errors. The weighted line has an intercept and a slope and uses inverse variance weights.",
                              "The fixed 0.10 boundary count uses three whole repeats on each side and their plain means. The endpoint rule is retained beside.",
                              "The between jobs weight event compares span means and is reported outside B. The mixed estimator transition is excluded.",
                              "Both the frequency and weight within ledgers retain the nine adjacent pairs touching straddling repeats with zero fitted exposure."])
    write("monitor11-notes.json", notes)
    with (ROOT / "monitor11-commands.log").open("a") as log:
        log.write("COMMAND: " + " ".join(sys.argv) + "\n")
        log.write("UTC: " + datetime.now(timezone.utc).isoformat() + "\n")
        log.write("Python: " + sys.version + "\n")
        log.write("Numeric type: IEEE 754 binary64. Libraries: Python standard library. Seeds: no random draws.\n")
        log.write("Input hashes: 48 of 48 match. Outputs: monitor11-ledger.json, estimators-model-01-v3.json, monitor11-notes.json.\n")
    print(json.dumps(dict(summary=summary, span_means=means3, gap12=gap12, gap23=gap23), indent=2))


def pair_trial(channel, job, file, a, b, khz_per_rad, eligible):
    trial = base(channel, job, file)
    trial.update(repeats=[a["k"], b["k"]], spans=[a["span"], b["span"]],
                 positions=[a["positions"], b["positions"]],
                 source_fields=list(dict.fromkeys(a["source_fields"] + b["source_fields"])),
                 included=eligible, exclusion_reason=None if eligible else "straddling",
                 eligible_own=eligible, eligible_4khz=False)
    if channel in ("W", "F", "F_gap"):
        delta = wrap(b["theta"] - a["theta"])
        se = math.hypot(a["s"], b["s"])
        threshold = max(0.3, 5 * se) * khz_per_rad
        resolved = threshold <= 4
        trial.update(signed_phase_difference_rad=delta, combined_phase_se_rad=se,
                     abs_change_kHz=abs(delta) * khz_per_rad, threshold_own_kHz=threshold,
                     threshold_4khz_kHz=max(4.0, threshold), kHz_per_rad=khz_per_rad,
                     eligible_4khz=eligible and resolved, censored_4khz=eligible and not resolved,
                     event_own=abs(delta) * khz_per_rad >= threshold if eligible else None,
                     event_4khz=abs(delta) * khz_per_rad >= max(4.0, threshold) if eligible and resolved else None,
                     exceeds_five_combined_se=abs(delta) > 5 * se if eligible else None)
    else:
        delta = b["w"] - a["w"]
        se = math.hypot(a["se_w"], b["se_w"])
        threshold = max(0.10, 5 * se)
        trial.update(signed_weight_difference=delta, combined_weight_se=se,
                     supporting_sources=[dict(file=FIT_FILE, field="jobs.1.analysis.fits.P.params"),
                                         dict(file="rules/t11-rule.md", field="The analysis of the monitor jobs, items 1, 2 and 6")],
                     threshold_own=threshold, threshold_fixed=0.10,
                     event_own=abs(delta) > threshold if eligible else None,
                     event_fixed=abs(delta) > 0.10 if eligible else None,
                     event_five_se=abs(delta) > 5 * se if eligible else None)
    return trial


def weight_span_trial(channel, job, file, left, right, last3, first3):
    trial = base(channel, job, file)
    delta = right["mean_w"] - left["mean_w"]
    se = math.hypot(left["se"], right["se"])
    near_before = mean([r["w"] for r in last3])
    near_after = mean([r["w"] for r in first3])
    trial.update(spans=[left["span"], right["span"]],
                 source_fields=["counts", "shots", "labels", "execution_metadata.execution_spans"],
                 supporting_sources=[dict(file=FIT_FILE, field="jobs.1.analysis.fits.P.params"),
                                     dict(file="rules/t11-rule.md", field="The analysis of the monitor jobs, items 1, 2 and 6")],
                 estimator="monitor", span_mean_before=left["mean_w"], span_mean_after=right["mean_w"],
                 se_before=left["se"], se_after=right["se"], signed_weight_difference=delta,
                 combined_weight_se=se, threshold_own=5 * se, z=delta / se,
                 event_own=abs(delta) > 5 * se, threshold_fixed=0.10,
                 nearest_three_before=[r["k"] for r in last3], nearest_three_after=[r["k"] for r in first3],
                 nearest_three_plain_mean_before=near_before, nearest_three_plain_mean_after=near_after,
                 nearest_three_signed_change=near_after - near_before,
                 event_fixed=abs(near_after - near_before) >= 0.10,
                 trial_exposure_own=1, trial_exposure_fixed=1)
    return trial


if __name__ == "__main__":
    run()
