# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""The README's measured statistics, and the times, ranges and counts it shows, recomputed from data/ and compared at
the README's own rounding (times: to the nearest minute).

The README links to four pages in docs/ that carry most of its text: the findings in full, the method in six pictures,
the kickoffs, and the install details. Every check here reads the README and those pages together, as one text: a
number moved between them is still checked, and a retired phrase cannot come back on any of them."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np
import pytest
from _reproduce import (
    k31,
    k32,
    k33,
    k34b,
    k35_recomputed,
    k36,
    k37,
    k38,
    k40_stage1,
    k40_stage2,
    k40_stage3,
    k41_partB,
    k41_today,
    k42_scan,
)

from manacitra import archive, wait

ROOT = Path(__file__).resolve().parents[1]
#: The README and the pages it links to for its findings, method, kickoffs and install details
README_PAGES = (
    "README.md",
    "docs/findings.md",
    "docs/method.md",
    "docs/kickoffs.md",
    "docs/install.md",
    "docs/reproduce.md",
)
README = "\n\n".join((ROOT / p).read_text() for p in README_PAGES)


def r(x, nd):
    return round(float(x), nd)


def hhmm(utc: str) -> str:
    """A UTC time as the README shows it: rounded to the nearest minute, the one convention used everywhere."""
    t = datetime.fromisoformat(utc.replace("Z", "+00:00")) + timedelta(seconds=30)
    return t.strftime("%H:%M")


def test_the_picture_of_the_kept_share():
    run = archive.load("ibm_fez/k31-map.json")
    an = archive.map_from_record(run)
    P = archive.p11_table(run)
    no = np.mean([P[i] for i, lbl in enumerate(run["order"]) if lbl == "A no"], axis=0)
    off = np.mean([P[i] for i, lbl in enumerate(run["order"]) if lbl == "A off"], axis=0)
    k = np.array(an["kA"])
    good, poor = int(np.argmax(k)), int(np.argmin(k))
    assert run["pairs"][good] == [106, 107] and run["pairs"][poor] == [20, 21]
    assert (r(no[good], 3), r(off[good], 3), r(off[good] - no[good], 3), r(k[good], 2)) == (0.923, 0.963, 0.040, 1.06)
    assert (r(no[poor], 3), r(off[poor], 3), r(off[poor] - no[poor], 3), r(k[poor], 2)) == (0.824, 0.833, 0.008, 0.22)
    assert run["order"].count("A no") * run["meta"]["shots_per_circuit"] == 32_000


def test_finding_1():
    for proc, rs, rab, rax in (("ibm_fez", 0.87, 0.82, -0.18), ("ibm_kingston", 0.90, 0.89, -0.05)):
        rows = {n: v for n, _, v in k31(proc)[0]}
        assert rows["verdict"] == "DIAGNOSTIC"
        assert (r(rows["r_split(k_A)"], 2), r(rows["r_AB"], 2), r(rows["r_Ax"], 2)) == (rs, rab, rax)


def test_finding_2():
    for proc, F, lo, hi in (("ibm_fez", 0.01, -0.21, 0.21), ("ibm_kingston", 0.03, -0.09, 0.16)):
        iso = k32(proc)[2]
        assert (r(iso["F"], 2), r(iso["F_ci90"][0], 2), r(iso["F_ci90"][1], 2)) == (F, lo, hi)


@pytest.mark.parametrize(
    "proc,less,G,lo,hi,verdict",
    [
        ("ibm_fez", 35.6, 0.0012, 0.0004, 0.0021, "USEFUL"),
        ("ibm_kingston", 16.1, 0.0004, 0.0001, 0.0008, "NOT SETTLED"),
    ],
)
def test_finding_3(proc, less, G, lo, hi, verdict):
    pay = k33(proc)[2]
    g = pay["gains"]["k_prior"]
    assert r(100 * (1 - g["error_ratio"]), 1) == less
    assert (r(g["G"], 4), r(g["ci90"][0], 4), r(g["ci90"][1], 4)) == (G, lo, hi)
    assert pay["verdict"]["verdict"] == verdict
    if proc == "ibm_fez":
        W = np.array(pay["W"])
        assert min(W) > 0.98
        err_k, err_x = 1 - W[pay["picks"]["k_prior"]].mean(), 1 - W[pay["picks"]["x"]].mean()
        assert (r(err_k, 4), r(err_x, 4)) == (0.0022, 0.0034)
    else:
        c = pay["correlations"]["W"]
        assert (r(c["partial_k_prior_given_x"], 2), r(c["p_partial_one_sided"], 3)) == (0.29, 0.073)


def test_finding_4():
    assert {n: v for n, _, v in k36(1)[0]}["verdict"] == "NOISE"
    assert {n: v for n, _, v in k36(2)[0]}["verdict"] == "DIAGNOSTIC"


def test_the_open_question_on_persistence():
    f = archive.fez_or_kingston("ibm_fez")
    rows = {n: v for n, _, v in k31("ibm_fez")[0]}
    assert r(rows["S4: r against the settling run"], 2) == 0.68
    t = [datetime.fromisoformat(f[n]["meta"]["utc"].replace("Z", "+00:00")) for n in ("k29-settle", "k31-map")]
    assert round((t[1] - t[0]).total_seconds() / 3600) == 10


def test_the_chip_map_correlation():
    rows = {n: v for n, _, v in k31("ibm_fez")[0]}
    assert r(rows["r_Ax"], 2) == -0.18


def test_finding_2_the_second_vendor():
    run = k34b()[2]
    an, a20 = run["analysis"], run["after_the_fact_20"]
    assert (len(run["pairs"]), len(run["working_pairs"])) == (27, 22)
    assert (r(an["S1"]["r_split_A"]["pearson"], 3), r(an["S2"]["r_AB"]["pearson"], 3)) == (0.985, 0.971)
    assert an["verdict"]["verdict"] == "MAP PRESENT"
    assert (a20["n_pairs"], r(a20["S1"]["r_split_A"]["pearson"], 2), r(a20["S2"]["r_AB"]["pearson"], 2)) == (
        20,
        0.84,
        0.79,
    )
    assert a20["verdict"]["verdict"] == "MAP PRESENT"
    assert (
        run["leave_one_out"]["dropped_pair"] == (101, 102)
        and run["leave_one_out"]["verdict"]["verdict"] == "MAP PRESENT"
    )
    rec = archive.load(f"{archive.RIGETTI}/main.json")
    w = rec["meta"]["utc_main_job"]
    assert (hhmm(w["wave_1_completed"][0]), hhmm(w["wave_2_completed"][1])) == ("22:15", "22:29")


def test_kickoff_34b_across_runs():
    """Kickoff 34b's lines across runs, as docs/index.md and the adapter's docs still show them (the README replaced
    them with Kickoff 37's result, Amendment A5)."""
    d = k34b()[2]["descriptive"]
    across = [d[k]["pearson"] for k in ("r_test_main", "r_screen_main", "r_test_screen")]
    assert (r(min(across), 2), r(max(across), 2)) == (0.10, 0.23)
    assert r(d["r_Lwave1_vs_Lwave2"]["pearson"], 2) == 0.93
    shared = archive.load(f"{archive.RIGETTI}/main.json")["archived"]["descriptive"]["across_runs"]
    assert shared["shared_pairs_in_all_three_runs"]["label"].startswith("after the fact")


def test_the_name_line_is_kept():
    """The clause is there for a reason (Amendment A2, section 4): keep it word for word."""
    assert "The name is measure-picture, map; it says nothing about minds." in README


# --------------------------------------------------------------------------- Amendment A3: the displayed metadata
@pytest.mark.parametrize(
    "path,shown",
    [
        ("ibm_fez/k31-map.json", "12:37"),
        ("ibm_kingston/k31-map.json", "12:38"),
        ("ibm_fez/k32-isolation.json", "13:17"),
        ("ibm_kingston/k32-isolation.json", "13:23"),
        ("ibm_fez/k33-payoff.json", "15:20"),
        ("ibm_kingston/k33-payoff.json", "15:23"),
    ],
)
def test_every_ibm_run_time_shown(path, shown):
    rec = archive.load(path)
    assert rec["meta"]["utc"].startswith("2026-10-05")
    assert hhmm(rec["meta"]["utc"]) == shown
    assert f"{shown} UTC" in README


def test_the_rigetti_times_shown():
    m = archive.load(f"{archive.RIGETTI}/main.json")["meta"]
    assert hhmm(m["utc_main_job"]["wave_1_completed"][0]) == "22:15" and "main job 22:15 to 22:29 UTC" in README
    assert hhmm(m["utc_main_job"]["wave_2_completed"][1]) == "22:29"


def test_the_payoff_prior_is_about_two_hours_older():
    f = archive.fez_or_kingston("ibm_fez")
    t = [datetime.fromisoformat(f[n]["meta"]["utc"].replace("Z", "+00:00")) for n in ("k32-isolation", "k33-payoff")]
    assert round((t[1] - t[0]).total_seconds() / 3600) == 2


def test_the_published_score_range_on_the_chip_map():
    x = [p["x"] for p in archive.load("ibm_fez/k31-map.json")["published_at_submission"]]
    assert (len(x), r(max(x), 3), r(min(x), 3)) == (27, 0.021, 0.011)
    assert "highest error, 0.021" in README and "lowest error, 0.011" in README


def test_the_isolation_group_sizes():
    for proc in ("ibm_fez", "ibm_kingston"):
        sel = archive.load(f"{proc}/k32-isolation.json")["selection"]
        assert (len(sel["best6"]), len(sel["worst6"]), len(sel["dense_pairs"])) == (6, 6, 27)
    assert "The six pairs that kept the most and the six that kept the least" in README
    assert "once with all 27 pairs active" in README


def test_the_chip_map_table_matches_the_data():
    """Amendment A3, 4.3: the accessible table beside diagram 2 lists every pair's k and x, as the data give them."""
    run = archive.load("ibm_fez/k31-map.json")
    k = dict(zip(map(tuple, run["pairs"]), archive.map_from_record(run)["kA"]))
    x = {tuple(p["pair"]): p["x"] for p in run["published_at_submission"]}
    table = (Path(__file__).resolve().parents[1] / "docs" / "diagrams" / "chip-map-table.md").read_text()
    rows = [line.split(" | ") for line in table.splitlines() if line.startswith("| ") and line[2].isdigit()]
    assert [int(row[0].lstrip("| ")) for row in rows] == list(range(1, 28))
    for _, pair, kv, xv, _ in rows:
        p = tuple(int(q) for q in pair.split("-"))
        assert (kv, xv.rstrip(" |")) == (f"{k[p]:.3f}", f"{x[p]:.4f}")
    assert "](diagrams/chip-map-table.md)" in (ROOT / "docs" / "method.md").read_text()


# --------------------------------------------------------------------------- Amendment A5: Kickoff 37
K37 = f"{archive.RIGETTI}/k37-placement.json"


def _utc(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def test_the_findings_dates():
    assert "The findings come from runs on 5 to 19 October 2026." in README  # A28: test 11 on day 3, tests 16 and 17
    assert "Thirty findings, from runs on 5 to 19 October 2026." in README
    # a reconstruction (A18, ruling R1: Kickoff 47's Part B circuits) is a record about a run, not a run; nor is a
    # record of the provider's published calibration stamps (A23: calibration history 01)
    runs = [
        p
        for p in archive.records()
        if p.parent.name != "simulated"
        and "k33-workload" not in p.name
        and "reconstruction" not in p.name
        and "calibration-history" not in p.name
    ]
    days = {archive.load(p)["meta"]["utc"][:10] for p in runs if not p.name.endswith("coupling-map.json")}
    assert days == {
        "2026-10-05",
        "2026-10-06",
        "2026-10-07",
        "2026-10-10",
        "2026-10-11",
        "2026-10-13",
        "2026-10-14",
        "2026-10-15",
        "2026-10-16",
        "2026-10-17",
        "2026-10-18",
        "2026-10-19",
    }
    # Amendment A28: finding 30, test 11 on a third day, test 16's read of it and test 17, on 19 October 2026
    day10 = sorted(p.name for p in runs if archive.load(p)["meta"]["utc"][:10] == "2026-10-19")
    assert day10 == ["t11-day3-monitor.json", "t16-day3-per-shot-read.json", "t17-long-monitor.json"]
    assert sum("counts" in archive.load(p) for p in runs if p.name in day10) == 2
    # Amendment A27: finding 29, four tests on 17 October 2026 on two processors, and the span check's record
    day8 = sorted(p.name for p in runs if archive.load(p)["meta"]["utc"][:10] == "2026-10-17")
    assert day8 == [
        "spans-t8-t9.json",
        "t10-monitor.json",
        "t11-day2-monitor.json",
        "t8-survey.json",
        "t9-day2-scan.json",
    ]
    # A27, ruling R2: tests 12 and 14 ran jobs on 18 October, and tests 13 and 15 read jobs already run, that day
    day9 = sorted(p.name for p in runs if archive.load(p)["meta"]["utc"][:10] == "2026-10-18")
    assert day9 == [
        "t12-short-monitor.json",
        "t13-per-shot-read.json",
        "t14-in-phase-control.json",
        "t15-error-model-read.json",
    ]
    assert sum("counts" in archive.load(p) for p in runs if p.name in day9) == 2
    assert (
        "- **Two processors, two days, for finding 29.** Finding 29 is from eight tests on ibm_kingston and ibm_fez on "
        "17 and 18 October 2026, six of them jobs, each under one published calibration stamp but for three reads at "
        "test 10's first job, and two of them reads of jobs already run" in README
    )
    # Amendment A25: finding 28, one job on 16 October 2026, on 143 alone, under one stamp
    day7 = sorted(p.name for p in runs if archive.load(p)["meta"]["utc"][:10] == "2026-10-16")
    assert day7 == ["spans-t7.json", "t7-ramsey-xy.json", "t7-span-readings.json"]  # A26: the job's spans, the readings
    (t7,) = [p for p in runs if p.name == "t7-ramsey-xy.json"]
    m7 = archive.load(t7)["meta"]
    assert (t7.name, m7["processor"], m7["kickoff"]) == ("t7-ramsey-xy.json", "ibm_fez", "Test 7")
    assert m7["calibration_last_update_utc"] == "2026-10-16T20:59:56Z" and m7["qubit"] == 143
    assert (
        "- **One qubit, one job, one day, for finding 28.** Finding 28 is from one job on ibm_fez on 16 October 2026, "
        "on qubit 143 alone, under one published calibration stamp." in README
    )
    assert "- **Three processors, three days.** The hardware results of findings 1 to 10" in README
    assert "all on 5 to 7 October 2026." in README
    # Amendment A17: findings 11 to 13, one processor on one day, three published calibration stamps
    reuse = [p for p in runs if archive.load(p)["meta"]["utc"][:10] == "2026-10-10"]
    assert sorted(p.name for p in reuse) == [
        "k43-map.json",
        "k43-reuse.json",
        "k44-reset.json",
        "k45-collapse.json",
        "k46-middle.json",
        "k47-wait.json",
    ]
    assert {archive.load(p)["meta"]["processor"] for p in reuse} == {"ibm_fez"}
    stamps = {archive.load(p)["meta"].get("calibration_last_update_utc") for p in reuse} - {None}
    assert sorted(s[11:16] for s in stamps) == ["03:16", "06:12", "09:56"]
    assert "Findings 11 to 13 are from one processor on one day, across three published calibration stamps." in README
    # Amendment A19: finding 14, one job on 11 October 2026 under a fourth stamp
    (k48,) = [p for p in runs if archive.load(p)["meta"]["utc"][:10] == "2026-10-11"]
    m48 = archive.load(k48)["meta"]
    assert k48.name == "k48-wait-test.json" and m48["processor"] == "ibm_fez"
    assert m48["calibration_last_update_utc"][11:16] == "01:35" and m48["calibration_last_update_utc"] not in stamps
    # Amendment A22: findings 15 to 19, five jobs on ibm_fez on 13 October 2026
    a22 = [p for p in runs if archive.load(p)["meta"]["utc"][:10] == "2026-10-13"]
    assert sorted(p.name for p in a22) == [
        "k49-wait-test.json",
        "k50-neighbour-test.json",
        "k51-known-offset.json",
        "k52-phase-sweep.json",
        "k53-revised-check.json",
    ]
    assert {archive.load(p)["meta"]["processor"] for p in a22} == {"ibm_fez"}
    # the last two jobs' stamps changed while they waited: which calibration they ran under is not known
    late = {p.name: archive.load(p)["run"] for p in a22}
    assert [
        n for n, r_ in late.items() if r_["calibration_after_fetch_utc"] != r_["calibration_at_submission_utc"]
    ] == [
        "k52-phase-sweep.json",
        "k53-revised-check.json",
    ]
    # Amendment A23, 1d: what those stamps changed, from calibration history 01
    first, last = archive.load(a22[0])["run"], archive.load(a22[-1])["run"]
    rows = [r_ for r_ in _history_rows() if first["calibration_at_build_utc"] < r_["stamp_utc"]]
    rows = [r_ for r_ in rows if r_["stamp_utc"] <= last["calibration_at_submission_utc"]]
    assert [r_["stamp_utc"][11:] for r_ in rows] == ["17:32:21Z", "18:56:54Z", "19:57:03Z"]
    assert all(not any(c.startswith(("q_", "g1_", "cz_")) for c in _history_changed(r_["stamp_utc"])) for r_ in rows)
    assert _history_after(last["calibration_at_submission_utc"])["q_readout_error"] == "154"
    assert (
        "- **One processor, one day, six waiting qubits, for findings 15 to 19.** Findings 15 to 19 are from five jobs "
        "on ibm_fez on 13 October 2026. From finding 15's calibration stamp to finding 19's submission no published "
        "T1, T2, readout, gate or CZ value changed; during finding 19's job, at 20:29:58 UTC, IBM published new "
        "readout errors on 154 qubits." in README
    )
    # Amendment A23: finding 20 on ibm_kingston on 14 October, finding 21 on ibm_fez on 15 October, one job each
    a23 = {p.name: p for p in runs if p.name in ("k55-revised-check.json", "k54-revised-check-day-2.json")}
    a23 = {archive.load(p)["meta"]["utc"][:10]: p for p in a23.values()}
    assert {d: (p.name, archive.load(p)["meta"]["processor"]) for d, p in a23.items()} == {
        "2026-10-14": ("k55-revised-check.json", "ibm_kingston"),
        "2026-10-15": ("k54-revised-check-day-2.json", "ibm_fez"),
    }
    # Amendment A24: Kickoffs 56 to 59 on ibm_kingston (Kickoff 56's job began on 14 October), 60 to 62 on ibm_fez
    late = sorted(
        (p.name, archive.load(p)["meta"]["utc"][:10], archive.load(p)["meta"]["processor"])
        for p in runs
        if archive.load(p)["meta"]["utc"][:10] in ("2026-10-14", "2026-10-15")
    )
    assert late == [
        ("k54-revised-check-day-2.json", "2026-10-15", "ibm_fez"),
        ("k55-revised-check.json", "2026-10-14", "ibm_kingston"),
        ("k56-phase-sweep.json", "2026-10-14", "ibm_kingston"),
        ("k57-peak-check.json", "2026-10-15", "ibm_kingston"),
        ("k58-placement-comparison.json", "2026-10-15", "ibm_kingston"),
        ("k59-peak-check-day-2.json", "2026-10-15", "ibm_kingston"),
        ("k60-draw-stopped.json", "2026-10-15", "ibm_fez"),
        ("k61-readout-check.json", "2026-10-15", "ibm_fez"),
        ("k62-peak-check.json", "2026-10-15", "ibm_fez"),
    ]
    assert (
        "- **Two processors, two calibration days, for the check at the peak phase.** On ibm_kingston it has run on "
        "eight waiting qubits of new chains, under the daily calibrations of 14 and 15 October 2026 (findings 23 and "
        "25), and on finding 20's three chains (finding 24); on ibm_fez on four, on 15 October (finding 27)." in README
    )
    k55 = archive.load(a23["2026-10-14"])
    stamps = {r_["stamp_utc"] for r_ in k55["calibration_record"]["stamps"]}
    assert len(stamps) == 2 and k55["run"]["calibration_after_fetch_utc"] in stamps
    assert (
        "- **Two processors, three days, for the active-neighbour check.** On ibm_fez it has run on six waiting "
        "qubits, on 13 October 2026 (findings 16 to 19) and again on 15 October (finding 21); on ibm_kingston on four, "
        "on 14 October (finding 20). Which of two calibration stamps finding 20's job ran under is not known." in README
    )


def test_finding_6_times():
    t = archive.load(K37)["meta"]["tasks"]
    assert {x["created_utc"][:10] for x in t} | {x["completed_utc"][:10] for x in t} == {"2026-10-06"}
    w = {n: [x for x in t if x["wave"] == n] for n in (1, 2)}
    span = {n: (hhmm(min(x["created_utc"] for x in w[n])), hhmm(max(x["completed_utc"] for x in w[n]))) for n in w}
    assert span == {1: ("00:45", "02:22"), 2: ("11:31", "11:35")}
    assert "6 October 2026; first wave 00:45 to 02:22 UTC, second wave 11:31 to 11:35 UTC" in README
    done2 = sorted(_utc(x["completed_utc"]) for x in w[2])
    assert round((done2[-1] - done2[0]).total_seconds() / 60) == 3
    assert "when all three tasks ran within 3 minutes" in README
    assert [x["program"] for x in t] == ["P27", "P53", "P27"] * 2


def test_finding_6_programs():
    rec = archive.load(K37)
    p27 = [tuple(p) for p in rec["programs"]["P27"]["pairs"]]
    p53 = {tuple(p) for p in rec["programs"]["P53"]["pairs"]}
    assert (len(p27), len(p53), set(p27) <= p53) == (27, 53, True)
    assert [tuple(p) for p in archive.load(f"{archive.RIGETTI}/main.json")["pairs"]] == p27
    assert "the main job's 27-pair program and the 53-pair screen, which contains the same 27 pairs" in README


def test_finding_6_numbers():
    run = k37()[2]
    m = {k: v["pearson"] for k, v in run["measures"].items()}
    assert (r(m["c_2"], 3), r(m["c_1"], 3)) == (0.997, 0.998) and "r = 0.997 to 0.998 minutes apart" in README
    assert (r(m["t27"], 2), r(m["t53"], 2)) == (0.97, 0.76)
    assert "0.97 (27-pair) and 0.76 (53-pair) across about 9 hours" in README
    d = run["descriptive"]
    pair = (d["r_T1w1_vs_34b_main_A_no_mean_of_four"]["pearson"], d["r_T2w1_vs_34b_screen"]["pearson"])
    assert (r(pair[0], 2), r(pair[1], 2)) == (0.99, 0.98)
    assert "0.99 and 0.98 against its own Kickoff 34b run the day before" in README
    assert (r(m["d_1"], 2), r(m["d_2"], 2)) == (0.07, -0.25)
    assert "r = 0.07 in the first wave and −0.25 in the second" in README
    assert (
        run["verdict"]["on_pearson"] == "PLACEMENT"
        and 'PLACEMENT, read as "the levels depend on the program"' in README
    )


def test_kickoff_37_gap():
    run = k37()[2]
    assert round(run["gap"]["seconds"] / 3600) == 9 and run["verdict"]["readings_per_amendments_A1_A2"]["N_hours"] == 9
    assert "planned two hours after the first and ran nine hours after it" in README
    assert "a fixed program's levels held over about 9 hours and a day (Kickoff 37)" in README
    assert "PLACEMENT (the levels depend on the program; they held over about 9 hours)" in README
    assert archive.load(K37)["meta"]["second_wave"] == (
        "The second wave was planned about two hours after the first and ran about nine hours after it; "
        "the two-hour question was not tested."
    )


def test_finding_2_the_five_excluded_pairs_under_the_screen_program():
    excluded = {tuple(p) for p in k34b()[2]["excluded_pairs"]}
    five = k37()[2]["after_the_fact"]["the_five_low_pairs"]
    assert {tuple(int(q) for q in k.split("-")) for k in five} == excluded and len(excluded) == 5
    t2 = [v[f"T2_w{w}"] for v in five.values() for w in (1, 2)]
    assert (r(min(t2), 2), r(max(t2), 2)) == (0.70, 0.84)
    assert "under the 53-pair screen program they read 0.70 to 0.84" in README


def test_the_kickoff_37_row_and_the_open_quantum_guidance():
    assert "| 37, 6 October 2026 | Did the Rigetti levels change between runs" in README
    assert "`rigetti_cepheus_1_108q/k37-placement.json` |" in README
    assert "On Open Quantum, a pair named in a program is not the physical pair: Kickoff 40 showed" in README
    assert "Use a map there only with the exact program that measured it, and read its pair names as labels." in README
    assert "On Open Quantum, use a map only with the exact program that measured it." not in README


# --------------------------------------------------------------------------- Amendment A7: findings 7 to 10
R = archive.RIGETTI


def test_finding_2_against_the_pinned_levels():
    d = k40_stage2()["descriptive"]["r_kA_vs_34b_kA_shared_working"]
    assert (d["n"], r(d["pearson"], 2)) == (20, -0.17)
    assert "do not match the pinned levels (r = −0.17 on the 20 shared working pairs)" in README


def test_finding_6_kickoffs_38_and_40():
    t = archive.load(f"{R}/k38-activity.json")["meta"]["tasks"]
    assert (hhmm(min(x["created_utc"] for x in t)), hhmm(max(x["completed_utc"] for x in t))) == ("13:42", "13:46")
    assert "Kickoff 38 (6 October 2026, 13:42 to 13:46 UTC)" in README
    m = k38()[2]
    assert (r(m["measures"]["a"]["pearson"], 2), r(m["measures"]["f"]["pearson"], 2)) == (0.99, -0.15)
    assert m["verdict"]["on_pearson"] == "ACTIVITY"
    assert "(r = 0.99) and not like the 53-pair one (r = −0.15)" in README and "(verdict ACTIVITY)" in README
    d = k40_stage1()["descriptive_outside_reading"]
    rs = (r(d["r_X_vs_k37_27pair_program"]["pearson"], 2), r(d["r_X_vs_k37_53pair_program"]["pearson"], 2))
    assert rs == (-0.18, 0.24)
    # Amendment A13: the mismatch is measured; where the Open Quantum pairs ran is a reading, and the alternative named
    assert "do not match the pinned levels of the same named pairs (r = −0.18 and 0.24)" in README
    assert "Open Quantum records no placement, so where its pairs ran is not measured" in README
    assert "is not excluded by these runs" in README


def test_finding_7():
    a = k35_recomputed()["analysis"]
    days = [archive.load(f"ibm_fez/k35-day{d}.json")["meta"]["utc"] for d in (1, 2, 3)]
    assert [x[:10] for x in days] == ["2026-10-05", "2026-10-06", "2026-10-07"]
    assert [hhmm(x) for x in days] == ["17:02", "14:56", "14:21"]
    assert "one job a day on 5, 6 and 7 October 2026 at 17:02, 14:56 and 14:21 UTC" in README
    ac = a["across"]
    assert (ac["edges_on_all_days"], r(ac["raw"]["13"]["pearson"], 2), r(ac["corrected"]["13"], 2)) == (176, 0.86, 0.89)
    assert "correlates with Day 1 at r = 0.86 (0.89 after correcting" in README
    assert (round(ac["worst_decile_overlap_13"] * 18), ac["decile_size"]) == (9, 18)
    assert "9 of the 18 worst pairs on Day 1 were still among the 18 worst on Day 3" in README
    assert a["original_rule"]["verdict"] == a["verdict"]["verdict"] == "HOLDS"
    fl = a["flagged"]
    assert len(fl["pairs"]) == 4 and r(fl["without"]["corrected"]["13"], 2) == 0.74
    assert "without all four the corrected correlation from Day 1 to Day 3 is 0.74" in README
    # three of the four flagged edges carry the most extreme k on the chip (among its six largest |k| every day)
    edges = [tuple(e) for e in archive.full_chip_day(archive.load("ibm_fez/k35-day1.json"))["edges"]]
    for d in "123":
        k = np.abs(np.array(a["per_day"][d]["k"]))
        top = {edges[i] for i in np.argsort(-k)[:6]}
        assert len(top & {tuple(p) for p in fl["pairs"]}) == 3, d
    assert "and three of them carry the most extreme values on the chip" in README
    # both pairs on qubit 149 fell on Day 2 and came back on Day 3: k fell by 3.5 and 4.1 and came back by 4.7 and 7.6,
    # while IBM's x for them changed by at most 16% (Amendment A8, R4, with the author's wording of 7 October)
    on149 = [i for i, e in enumerate(edges) if 149 in e]
    assert len(on149) == 2
    falls, rises, changes = [], [], []
    for i in on149:
        k1, k2, k3 = (a["per_day"][d]["k"][i] for d in "123")
        assert k2 < -4 and k1 > k2 + 2 and k3 > k2 + 2
        falls.append(k1 - k2)
        rises.append(k3 - k2)
        x = [archive.load(f"ibm_fez/k35-day{d}.json")["published_at_submission"][i]["x"] for d in (1, 2, 3)]
        changes.append(max(x) / min(x) - 1)
    assert sorted(r(f, 1) for f in falls) == [3.5, 4.1] and sorted(r(v, 1) for v in rises) == [4.7, 7.6]
    assert round(max(changes), 2) == 0.16
    assert "On Day 2 both pairs on one qubit fell sharply and recovered on Day 3" in README
    assert (
        "while k fell by 3.5 and 4.1 on Day 2 and came back by 4.7 and 7.6 on Day 3, and x changed by at most 16%."
        in README
    )
    assert min(r(ac["x_raw"][k]["pearson"], 2) for k in ("12", "23", "13")) == 0.99
    rkx = [r(a["per_day"][d]["r_k_x"]["pearson"], 2) for d in "123"]
    assert (max(rkx), min(rkx)) == (0.06, -0.07) and "(r between 0.07 and −0.07)" in README


def test_finding_8():
    s1, s2, s3 = k40_stage1(), k40_stage2(), k40_stage3()
    t = [x for st in ("placement", "map", "payoff") for x in archive.load(f"{R}/k40-{st}.json")["tasks"]]
    assert (hhmm(min(x["created_utc"] for x in t)), hhmm(max(x["ended_utc"] for x in t))) == ("15:17", "15:50")
    assert "6 October 2026, 15:17 to 15:50 UTC; Kickoff 34b's 27 named pairs" in README
    assert s1["reading"] == "PINNED" and s1["records_match_names"] and r(s1["d"]["pearson"], 2) == 0.99
    v = s2["verdict_stats"]
    assert (s2["n_working_with_x"], s2["verdict"]) == (23, "DIAGNOSTIC")
    got = (r(v["S1"]["r_split_A"]["pearson"], 2), r(v["S2"]["r_AB"]["pearson"], 2), r(v["S3"]["r_Ax"]["pearson"], 2))
    assert got == (0.97, 0.81, 0.20)
    assert "the map repeated (r = 0.97), carried over to circuit B (r = 0.81)" in README
    assert "and was not explained by Rigetti's figures (r = 0.20)" in README
    assert s3["verdict"] == "NOT SETTLED" and round(100 * s3["gains"]["L_prior"]["relative_error_reduction"]) == 31
    assert "gave 31% less error than choosing by the published figures" in README
    fez = archive.map_from_record(archive.load("ibm_fez/k31-map.json"), n_permutations=100)
    assert (r(v["sd_kA_between_pairs"], 1), r(fez["sd_kA_between_pairs"], 1)) == (1.1, 0.2)
    assert "(SD of k 1.1, against 0.2 on Kickoff 31's ibm_fez pairs)" in README
    assert sum(k < 0 for k in v["kA"]) == 3 and "a few pairs carry negative k" in README


def test_finding_9():
    t = [x for st in ("map", "payoff") for x in archive.load(f"{R}/k41-{st}.json")["tasks"]]
    assert (hhmm(min(x["created_utc"] for x in t)), hhmm(max(x["ended_utc"] for x in t))) == ("15:05", "15:58")
    assert "re-sent on 7 October 2026, 15:05 to 15:58 UTC, 23 to 24 hours after Kickoff 40" in README
    rec = archive.load(f"{R}/k41-map.json")
    pm = archive.pinned_map_persistence(
        k41_today(),
        k40_stage2(),
        archive.load(f"{R}/k41-figures.json")["A"],
        archive.load(f"{R}/k40-figures.json")["stage2"],
        rec["pairs"],
        rec["meta"]["permutation_seed"],
    )
    assert (r(pm["p_k"]["r"]["pearson"], 2), r(pm["p_k_prime"]["r"]["pearson"], 2), r(pm["p_L"]["pearson"], 2)) == (
        0.85,
        0.61,
        0.80,
    )
    assert pm["verdict"] == "HOLDS"
    assert "at r = 0.85 (0.61 without the two extreme pairs) and the plain level at r = 0.80: HOLDS" in README
    b = k41_partB()
    L = b["level"]
    assert (round(100 * L["relative_error_reduction"]), r(L["G"], 4), r(L["ci90"][0], 4), r(L["ci90"][1], 4)) == (
        27,
        0.0122,
        0.0077,
        0.0168,
    )
    assert L["verdict"] == "USEFUL" and b["kept_share"]["verdict"] == "NOT SETTLED"
    assert "(G = +0.0122, 90% interval +0.0077 to +0.0168): USEFUL" in README
    pairs, W = [tuple(p) for p in b["pairs"]], np.array(b["W"])
    S = [pairs.index(tuple(p)) for p in b["pick_set"]]
    assert len(S) == 23 and [tuple(p) for p in L["x_pick"]].index((94, 95)) == 5
    assert pairs[min(S, key=lambda i: W[i])] == (94, 95)
    assert (
        "The gain is dominated by one pair: Rigetti's figures rated 94-95 sixth best of 23, and it was the worst"
        in README
    )
    today, before = k41_today(), k40_stage2()
    dead = {e: [tuple(x["pair"]) for x in a["dead_pair_filter"]["excluded"]] for e, a in (("t", today), ("y", before))}
    assert (18, 19) in dead["y"] and (18, 19) not in dead["t"]
    assert {(72, 73), (76, 77)} <= set(dead["t"]) and not {(72, 73), (76, 77)} & set(dead["y"])
    assert "18-19 was back, 72-73 and 76-77 were gone" in README


def test_finding_10():
    d1 = archive.load(f"{R}/k42-day1.json")["tasks"]
    d2 = archive.load(f"{R}/k42-day2.json")["tasks"]
    assert (min(x["created_utc"] for x in d1)[:10], hhmm(min(x["created_utc"] for x in d1))) == ("2026-10-06", "17:46")
    assert (min(x["created_utc"] for x in d2)[:10], hhmm(min(x["created_utc"] for x in d2))) == ("2026-10-07", "16:17")
    assert "6 October 2026 at 17:46 UTC and 7 October at 16:17 UTC" in README
    sc = k42_scan()
    shape = [sc[d]["beside"]["shape_fraction_rms_le_2_shot"] for d in ("day1", "day2")]
    assert max(shape) < 0.1 and "fits fewer than one pair in ten within twice the shot noise" in README
    assert r(sc["day1"]["V3"]["r_deltaA_vs_k40_kA"]["pearson"], 2) == 0.24 and "(r = +0.24)" in README
    v5 = sc["V5"]
    low = sorted(v5["per_pair_r"].values())[:2]
    assert (r(v5["p_F"]["pearson"], 2), r(v5["median_per_pair_r"], 2), [r(x, 2) for x in low]) == (
        0.85,
        0.98,
        [0.04, 0.04],
    )
    assert "pooled r = 0.85 a day later, median per-pair r = 0.98, with two pairs at 0.04" in README
    for d in ("day1", "day2"):  # 94-95: a dip at the designed offset, -0.5, between higher neighbours
        rec = archive.load(f"{R}/k42-{d}.json")
        y = np.array(sc[d]["P11"]["A"])[[tuple(p) for p in rec["pairs"]].index((94, 95))]
        j = archive.SCAN["A"]["offsets"].index(-0.5)
        assert y[j] < y[j - 1] and y[j] < y[j + 1]
    sw = v5["switch"]["pairs"]
    assert (r(sw["11-12"]["day1_high_minus_low"], 1), r(sw["11-12"]["day2_high_minus_low"], 1)) == (0.3, 0.3)
    assert (r(sw["72-73"]["day1_high_minus_low"], 2), r(sw["72-73"]["day2_high_minus_low"], 2)) == (0.21, 0.11)
    assert (
        "pair 11-12 read about 0.3 higher on the same seven programs on both days, "
        "and 72-73 read 0.21 higher on the first day and 0.11 on the second" in README
    )
    v4, v4o = sc["V4_amended_governs"], sc["V4_original_rule"]
    assert (r(v4["A"]["r"]["pearson"], 2), r(v4["B"]["r"]["pearson"], 2), v4["verdict"], v4o["verdict"]) == (
        0.72,
        0.90,
        "HOLDS",
        "PARTIAL",
    )
    assert "(r = 0.72 for A, 0.90 for B; HOLDS under the amended rule, PARTIAL under the original)" in README


def test_the_flagged_line():
    a = k35_recomputed()
    edges = [tuple(e) for e in archive.full_chip_day(archive.load("ibm_fez/k35-day1.json"))["edges"]]
    flagged = [edges.index(tuple(p)) for p in a["analysis"]["flagged"]["pairs"]]
    levels = [a["levels"][d]["P_no"][i] for d in (1, 2, 3) for i in flagged]
    assert (r(min(levels), 2), r(max(levels), 2)) == (0.19, 0.39)
    assert r(np.median(a["levels"][1]["P_no"]), 2) == 0.89
    assert "these four read 0.19 to 0.39, against a median of 0.89 on the chip" in README


def test_the_new_rows_and_bullets():
    for k in (
        "35, 5 to 7 October 2026",
        "38, 6 October 2026",
        "40, 6 October 2026",
        "41, 7 October 2026",
        "42, 6 to 7 October 2026",
        "43, 10 October 2026",
        "44, 10 October 2026",
        "45, 10 October 2026",
        "46, 10 October 2026",
        "47, 10 October 2026",
        "48, 11 October 2026",
    ):
        assert f"| {k} |" in README
    assert "- **How long a map lasts beyond two days.**" in README and "- **Two routes to one processor.**" in README
    assert "`manacitra pick --by level` ranks by the plain level instead" in README
    assert "running as of 6 October 2026" not in README


def test_the_three_checks_picture():
    """The third picture (added after Amendment A7, at the author's request): its caption and alt text."""
    run = archive.load("ibm_fez/k31-map.json")
    an = archive.map_from_record(run)
    rs = (an["S1"]["r_split_A"]["pearson"], an["S2"]["r_AB"]["pearson"], an["S3"]["r_Ax"]["pearson"])
    assert tuple(r(v, 2) for v in rs) == (0.87, 0.82, -0.18) and r(an["S3"]["r_AB_given_x"], 2) == 0.82
    assert an["S2"]["p_one_sided"] < 1e-4 and an["verdict"]["verdict"] == "DIAGNOSTIC"
    copies = sum(1 for i in run["halves"]["A"][0] if run["order"][i - 1] == "A no")
    assert copies * run["meta"]["shots_per_circuit"] == 16_000
    assert "each half of the runs, 16,000 shots per variant per pair, gives nearly the same k (r = 0.87)" in README
    assert "k barely follows x (r = −0.18), and the carry-over survives with x taken out (r = 0.82)" in README
    assert "r = 0.82, p below 1 in 10,000, needs at least 0.4 with p below 0.05" in README
    method = (ROOT / "docs" / "method.md").read_text()
    assert "](diagrams/three-checks.svg)" in method and method.startswith("# The idea in six pictures")
    assert (Path(__file__).resolve().parents[1] / "docs" / "diagrams" / "three-checks.png").is_file()


def test_the_whole_chip_picture():
    """Finding 7's picture (after Amendment A7, at the author's request): its alt text and caption."""
    a = k35_recomputed()["analysis"]
    rho = {k: r(v["spearman"], 2) for k, v in a["across"]["raw"].items()}
    assert (rho["12"], rho["13"], rho["23"]) == (0.76, 0.66, 0.70)
    assert r(a["per_day"]["1"]["r_k_x"]["spearman"], 2) == -0.08
    assert r(a["original_rule"]["inputs"]["corrected_r_13"], 2) == 0.89 and len(a["flagged"]["pairs"]) == 4
    assert (
        "Day 2 with Day 1, 0.76; Day 3 with Day 1, 0.66, and with Day 2, 0.70; "
        "the published score with Day 1's map, −0.08" in README
    )
    assert "(rank correlations 0.76 and 0.66 with Day 1)" in README and "(−0.08 against Day 1's map)" in README
    assert "](diagrams/whole-chip-days.svg)" in (ROOT / "docs" / "findings.md").read_text()


def test_the_explainer_in_the_long_documentation():
    """The one-picture explainer at the top of docs/index.md: the numbers its alt text gives."""
    doc = (Path(__file__).resolve().parents[1] / "docs" / "index.md").read_text()
    run = archive.load("ibm_fez/k31-map.json")
    an = archive.map_from_record(run)
    k = np.array(an["kA"])
    pairs = [tuple(p) for p in run["pairs"]]
    order = np.argsort(-k, kind="stable")
    assert [pairs[i] for i in (order[0], order[13], order[-1])] == [(106, 107), (133, 134), (20, 21)]
    assert [r(k[i], 2) for i in (order[0], order[13], order[-1])] == [1.06, 0.87, 0.22]
    P = archive.p11_table(run)
    gap = [
        np.mean(P[[j for j, lb in enumerate(run["order"]) if lb == "A off"], i])
        - np.mean(P[[j for j, lb in enumerate(run["order"]) if lb == "A no"], i])
        for i in (order[0], order[13], order[-1])
    ]
    assert [r(g, 3) for g in gap] == [0.040, 0.033, 0.008]
    assert run["order"].count("A no") * run["meta"]["shots_per_circuit"] == 32_000
    assert (
        "106-107 moved 0.040 (k = 1.06), the median pair 133-134 moved 0.033 (k = 0.87), "
        "and 20-21 moved 0.008 (k = 0.22)" in doc
    )
    assert (
        "repeats (r = 0.87, needs at least 0.5), carries over (r = 0.82" in doc
        and "](diagrams/map-explainer.svg)" in doc
    )


def test_finding_9_the_level_only_pairs_against_the_x_only_pairs_apart_from_94_95():
    """Amendment A8, R3: the three pairs only the level pick chose (0-1, 24-25, 87-88) against the two only the x pick
    chose apart from 94-95 (22-23, 65-66), in mean workload fidelity W. The expected 0.00013 was computed by
    tests/_independent_readings.py (k41_one_pair), which does not import manacitra."""
    expected_difference = 0.00013  # from tests/_independent_readings.py, Amendment A8
    b = k41_partB()
    L = b["level"]
    pairs, W = [tuple(p) for p in b["pairs"]], np.array(b["W"])
    only_L = [pairs.index(tuple(p)) for p in L["pick"] if p not in L["x_pick"]]
    only_x = [pairs.index(tuple(p)) for p in L["x_pick"] if p not in L["pick"] and tuple(p) != (94, 95)]
    assert [pairs[i] for i in only_L] == [(0, 1), (24, 25), (87, 88)]
    assert [pairs[i] for i in only_x] == [(22, 23), (65, 66)]
    assert abs((W[only_L].mean() - W[only_x].mean()) - expected_difference) < 1e-4
    assert r(W[only_L].mean() - W[only_x].mean(), 4) == 0.0001
    assert (
        "The three pairs only the level pick chose and the two only the x pick chose, apart from 94-95, differ in mean "
        "fidelity by 0.0001." in README
    )
    assert "the two picks otherwise tie" not in README and "The whole gain is one pair" not in README


def test_the_scores_compared_on_each_chip():
    """Amendment A8, R4: the kept share was tested as a chooser on ibm_kingston too (finding 4, NOT SETTLED)."""
    assert {n: v for n, _, v in k33("ibm_kingston")[0]}["verdict"] == "NOT SETTLED"
    doc = (Path(__file__).resolve().parents[1] / "docs" / "index.md").read_text()
    for text in (README, " ".join(doc.split())):
        assert "was not settled on ibm_kingston" in text
        assert (
            "On every payoff run both scores were scored against the published figures: on IBM the kept share was the "
            "primary test and the level a reference line; on Rigetti the reverse" in text
        )  # A14's wording, by the author's ruling of 8 October; build report section 26 notes Kickoff 40's rule
        assert "third chip" not in text


# --------------------------------------------------------------------------- Amendment A8, R5: retired phrases
#: Phrases the README has retired, with the amendment that retired each; no README line, no line of docs/index.md and
#: no diagram may carry one
RETIRED = [
    "running as of 6 October 2026",  # A7: Kickoff 35 ran and is reported
    "is running as of",  # A7
    "The findings come from runs on 5 and 6 October 2026",  # A7
    "Three processors, two days",  # A7
    "On Open Quantum, use a map only with the exact program that measured it.",  # A7
    "today, use a map only within the job",  # A5
    "SD of k 1.1, against 0.3",  # A7, corrected to the data
    "15:06 to 16:20",  # A7, corrected to the data
    "The whole gain is one pair",  # A8, R3
    "the two picks otherwise tie",  # A8, R3
    "Neither has been tested on a third chip",  # A8, R4
    "IBM's figures for them did not move",  # A8, R4
    "k swung by 3 to 4",  # A8, the author's wording of 7 October
    "IBM's figures for them barely moved",  # A8, the author's wording of 7 October
    "have not been compared head to head",  # A8, the author's wording of 7 October
    # A13: placement on Open Quantum is a reading of the correlation evidence, not a measurement
    "had run its pairs on the named qubits",  # A13
    "ran on other qubits than",  # A13
    "labels, not locations",  # A13
    "the level was not tested as a chooser",  # A14: it was, for reference, on both IBM chips
    "highest kept share first",  # A15: pick ranks by |1 - k|
    "the n pairs that kept the most",  # A15, the pipeline diagram and its alt text
    "Ten findings, from runs on 5 to 7 October 2026",  # A17: thirteen, from 5 to 10 October
    "collapses on every chain tried that contains 143",  # A17: two chains containing 143 did not collapse
    "collapsed on every chain containing 143",  # A17, the same
    "into every idle window of the chain by",  # A17 ruling R1: only the windows long enough to hold the sequence
    "Thirteen findings, from runs on 5 to 10 October 2026",  # A19: fourteen, from 5 to 11 October
    "Whether the offset persists across days.",  # A19: edited with finding 14's evidence of 11 October
    "Whether a measured wait loss chooses better placements",  # A19: the bullet on choosing by the Ramsey loss
    "an established finding about the circuit, not tested here",  # A19 R1: the rule rests on it, and AGREE tests that
    "would test whether the wander is that slow",  # A19 R1: the disconfirmer names a later run, and what narrows it
    "compared with Qiskit's and with MERA-style placement, has not been run",  # A20: and refocusing, and ADAPT
    "the fourteen findings in full, and what has not been shown",  # A20: and what was known before them
    "The steps v0.1.0 and v0.1.1 took",  # A20: every release since took them
    "every release from v0.1.0 to v0.5.0",  # A20 R1, Q4: v0.5.0 ran the tree check after tagging, not before
    "how a reuse-shaped circuit would fare, on one processor on one day",  # A20 R1, Q3: findings 13 and 14, two days
    "Fourteen findings, from runs on 5 to 11 October 2026",  # A22: nineteen, from 5 to 13 October
    "The findings come from runs on 5 to 11 October 2026",  # A22, the same
    "the fourteen findings in full, what was known before them",  # A22: nineteen
    # A22: the placement bullet adds the active-neighbour check
    "Whether choosing qubits by the Ramsey loss at the circuit's wait gives better placements",
    "Nineteen findings, from runs on 5 to 13 October 2026",  # A23: twenty-one, from 5 to 15 October
    "The findings come from runs on 5 to 13 October 2026",  # A23, the same
    "the nineteen findings in full, what was known before them",  # A23: twenty-one
    "New on this branch",  # A23: the README's opening section is "Latest findings"
    "The active-neighbour check has run on one processor",  # A23: the margin's record, on two processors
    "The run cannot separate the recalibration",  # A23, 1d: no published value changed at the new stamp
    "which published calibration they ran under is not known",  # A23, 1d: what the stamps changed, from the history
    "To be released as 0.6.0",  # the 0.6.0 release: released, with its date (A23, ruling R1, Q3)
    "Twenty-one findings, from runs on 5 to 15 October 2026",  # A24: twenty-seven
    "the twenty-one findings in full",  # A24: twenty-seven, with the table of all of them
    "the check runs with the neighbours active",  # A24: the README opens with the check at the peak phase
    "To be released as 0.7.0",  # the 0.7.0 release: released, with its date
    "To be released as 0.8.0",  # the 0.8.0 release: released, with its date
    "To be released as 0.9.0",  # the 0.9.0 release: released, with its date
    "To be released as 0.10.0",  # the 0.10.0 release: released, with its date
    "The ±0.15 margin held on one processor for two days and failed on a second",  # A24: the margin at the peak
]
DIAGRAMS = Path(__file__).resolve().parents[1] / "docs" / "diagrams"


def svg_text(path: Path) -> str:
    """Every piece of text in an SVG (the diagrams write text as text, not as paths), joined by spaces."""
    import xml.etree.ElementTree as ET

    return " ".join(" ".join(t.strip() for t in ET.parse(path).getroot().itertext() if t.strip()).split())


def test_the_readme_carries_no_retired_phrase():
    flat = " ".join(README.split())
    assert [p for p in RETIRED if p in flat] == []


def test_the_docs_page_carries_no_retired_phrase():
    """docs/index.md is prose a stranger reads, and it carried one of the stale sentences (A8, R4): the author's ruling
    of 7 October puts it under the same check."""
    flat = " ".join((Path(__file__).resolve().parents[1] / "docs" / "index.md").read_text().split())
    assert [p for p in RETIRED if p in flat] == []


@pytest.mark.parametrize("svg", sorted(p.name for p in DIAGRAMS.glob("*.svg")))
def test_no_diagram_carries_a_retired_phrase(svg):
    text = svg_text(DIAGRAMS / svg)
    assert text, f"{svg}: no text found; the check would pass on anything"
    assert [p for p in RETIRED if p in text] == []


def test_the_pipeline_diagram_says_kickoff_35_ran():
    assert "on ibm_fez a whole-chip map held for two days (finding 7); beyond that is open." in svg_text(
        DIAGRAMS / "pipeline.svg"
    )


@pytest.mark.parametrize("page", README_PAGES)
def test_every_link_resolves(page):
    """Every relative link on the README and its pages names a file that exists, and every in-page anchor names a
    heading (or an explicit anchor) that exists on the page it points to."""
    import re

    def anchors(path: Path) -> set:
        text = path.read_text()
        slugs = {
            re.sub(r"[^\w\- ]", "", h.strip().lower()).replace(" ", "-") for h in re.findall(r"^#+ (.+)$", text, re.M)
        }
        return slugs | set(re.findall(r'<a id="([^"]+)"></a>', text))

    here = (ROOT / page).parent
    bad = []
    for target in re.findall(r"\]\(([^)\s]+)\)", (ROOT / page).read_text()):
        if re.match(r"[a-z]+:", target):
            continue
        file, _, anchor = target.partition("#")
        path = (here / file).resolve() if file else ROOT / page
        if not path.exists():
            bad.append(target)
        elif anchor and path.suffix == ".md" and anchor not in anchors(path):
            bad.append(target)
    assert bad == [], f"{page}: {bad}"


def test_the_findings_table_matches_the_findings():
    """The table of findings, one row per finding, on docs/findings.md (the README's until A24): each row's headline is
    that finding's own bold sentence, word for word; its kickoffs are the ones the finding names; and every verdict word
    in the row (the capitalised words) is in that kickoff's row of the kickoffs table, so the summary carries nothing
    the full text does not."""
    import re

    findings = (ROOT / "docs" / "findings.md").read_text()
    kickoffs = (ROOT / "docs" / "kickoffs.md").read_text()
    full = dict(re.findall(r'^(\d+)\. <a id="finding-\d+"></a>\*\*(.+?)\*\*', findings, re.M))
    table = findings.split("\n## The findings in one table\n", 1)[1].split("\n## ", 1)[0]
    rows = re.findall(r"^\| \[(\d+)\]\(#finding-\1\) \| (.+?) \| [^|]+ \| ([^|]+) \| (.+?) \|$", table, re.M)
    rows = [(n, head, when.rsplit(", ", 1)[0], verdict) for n, head, when, verdict in rows]  # "37, 38, 6 Oct": 37, 38
    assert [n for n, *_ in rows] == [str(i) for i in range(1, 31)] == list(full)
    for n, head, kicks, verdict in rows:
        assert head == full[n], n
        item = findings.split(f'<a id="finding-{n}"></a>', 1)[1].split("<a id=", 1)[0]
        table_rows = ""
        if n == "30":  # A28: finding 30 is test 11 on a third day and tests 16 and 17
            assert item.split("**", 2)[2].startswith(f" ({kicks}; ibm_fez, 19 October 2026)."), n
        for k in kicks.replace(" to 15 Oct", "").split(", "):
            if n != "30":
                assert (f"Kickoff {k}" if k[0].isdigit() else f"({k};") in item, (n, k)  # A25: finding 28 is test 7
            for name in _tests_named(k):  # A27: finding 29 is tests 8 to 11
                table_rows += next(line for line in kickoffs.splitlines() if line.startswith(f"| {name}, "))
        words = set(re.findall(r"\b[A-Z]{3,}(?: [A-Z]{3,})*\b", verdict))
        assert words and all(w in table_rows for w in words), (n, words)


def _tests_named(k: str) -> list[str]:
    """A kickoff's name as the kickoffs table's rows begin, a range of tests ("tests 8 to 11") or a pair ("tests 16 and
    17") one row per test."""
    if not k.startswith("tests "):
        return [k]
    if " and " in k:
        return [f"test {x}" for x in k[len("tests ") :].split(" and ")]
    a, b = (int(x) for x in k[len("tests ") :].split(" to "))
    return [f"test {i}" for i in range(a, b + 1)]


#: Amendment A24, the author's ruling of 14 October: the README's table of findings has one row per thread
THREADS = {
    "The kept-share map on IBM processors": (1, 7),
    "The map on a second vendor's processor": (2, 6, 8, 9, 10),
    "What the neighbours do not explain": (3,),
    "Choosing pairs by the map": (4, 11),
    "The rule can say no": (5, 26),
    "The collapse on 143 and 144, and the wait": (12, 13),
    "The check and its instrument": (14, 15, 16, 17, 18, 19, 20, 21),
    "The check at the peak phase": (22, 23, 24, 25, 27),
    "The fringe on 143: one line or two": (28,),  # A25
    "When a qubit's fringe changes: the shared state within a span": (29,),  # A27; its first name retired by R2
    "The duty across spans, jobs and days": (30,),  # A28
}


def test_the_readme_table_has_one_row_per_thread():
    """A24: the README's table of findings has one row per thread, each finding number in exactly one row and linked to
    its finding, the full table one row per finding on docs/findings.md; every verdict word in a row is in the kickoffs
    table's rows of that row's findings, and every row's state is one sentence."""
    import re

    readme = (ROOT / "README.md").read_text()
    findings = (ROOT / "docs" / "findings.md").read_text()
    kickoffs = (ROOT / "docs" / "kickoffs.md").read_text()
    section = readme.split("\n## Findings\n", 1)[1].split("\n## ", 1)[0]
    assert "](docs/findings.md#the-findings-in-one-table)" in section
    assert "Thirty findings, from runs on 5 to 19 October 2026." in section  # A28: test 11 on day 3, tests 16, 17
    rows = re.findall(r"^\| ([^|\[]+?) \| (\[.+?) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|$", section, re.M)
    assert [r_[0] for r_ in rows] == list(THREADS)
    seen = []
    full_rows = findings.split("\n## The findings in one table\n", 1)[1].split("\n## ", 1)[0]
    for thread, links, _where, state, verdict in rows:
        nums = [int(n) for n in re.findall(r"\[(\d+)\]\(docs/findings\.md#finding-\1\)", links)]
        assert tuple(nums) == THREADS[thread] and links.count("](") == len(nums), thread
        seen += nums
        assert len(re.findall(r"[.!?](?:\s|$)", state.strip() + " ")) == 1, thread
        kick_rows = ""
        for n in nums:
            row = next(line for line in full_rows.splitlines() if line.startswith(f"| [{n}](#finding-{n}) |"))
            for k in row.split(" | ")[3].rsplit(", ", 1)[0].replace(" to 15 Oct", "").split(", "):
                for name in _tests_named(k):
                    kick_rows += next(line for line in kickoffs.splitlines() if line.startswith(f"| {name}, "))
        words = set(re.findall(r"\b[A-Z]{3,}(?: [A-Z]{3,})*\b", verdict))
        assert words and all(w in kick_rows for w in words), (thread, words - {w for w in words if w in kick_rows})
    assert sorted(seen) == list(range(1, 31))
    # the record beside finding 26, Kickoff 60, is named in its thread's row and in the kickoffs table
    assert "Kickoff 60" in dict((r_[0], r_[3]) for r_ in rows)["The rule can say no"]
    assert "| 60, 15 October 2026 |" in kickoffs


def test_the_front_page():
    """The README itself, not its pages, shows the chip map under "What it does" (the picture that explains the project
    at a glance) and the pipeline, and says that pick can rank by the plain level, which its table's rows 8 and 9 rely
    on (the author's review of 8 October)."""
    front = (ROOT / "README.md").read_text()
    what = front.split("\n## What it does\n", 1)[1].split("\n## ", 1)[0]
    assert "](docs/diagrams/chip-map.svg)" in what and "](docs/diagrams/pipeline.svg)" in front
    assert (
        "by how close each pair's kept share is to the ideal of 1, |1 − k| (`--by kept-share-highest` gives the "
        "highest-first rule Kickoff 33 used), or, with `--by level`, by the plain level, which chose better pairs on "
        "the Rigetti processor where the kept share did not." in what
    )


def test_the_readme_itself_says_how_to_point_at_the_data_and_what_is_sent():
    """Amendment A12: three sentences the restructure had left only on linked pages are on the README itself: where
    --data goes, that a provider backend sends nothing without --submit, and that the published runs predate this
    release's checkable sealing."""
    front = " ".join((ROOT / "README.md").read_text().split())
    assert "`manacitra --data /path/to/manacitra/data verdict ibm_fez/k31-map.json`" in front
    assert "`--data` goes before the subcommand." in front
    assert "A provider backend sends nothing unless `--submit` is given" in front
    assert (
        "The published runs predate this release, so their sealed predictions rest on the author's dated records"
        in front
    )


def test_finding_4_reference_lines():
    """Amendment A14: Kickoff 33's rule scored, for reference beside the verdict, the plain level's pick and the
    same-day map's pick. Each figure the findings give is read from the archived analysis (which the reproduction
    suite recomputes at 1e-6) and compared at the text's rounding."""
    an = {c: archive.load(f"{c}/k33-payoff.json")["archived"]["analysis"] for c in ("ibm_fez", "ibm_kingston")}
    g = {c: an[c]["gains"] for c in an}
    assert [r(g[c]["L_prior"]["G"], 4) for c in an] == [0.0004, 0.0001]
    assert [r(g[c]["k_prior"]["G"], 4) for c in an] == [0.0012, 0.0004]
    assert r(g["ibm_fez"]["k_now"]["G"], 4) == -0.0003
    assert [r(v, 4) for v in g["ibm_fez"]["k_now"]["ci90"]] == [-0.001, 0.0003]
    assert r(g["ibm_kingston"]["k_now"]["G"], 4) == 0.0004
    assert not an["ibm_fez"]["level_beats_k"] and not an["ibm_kingston"]["level_beats_k"]
    p = an["ibm_fez"]["predictors"]
    assert r(float(np.corrcoef(p["k_prior"], p["k_now"])[0, 1]), 2) == 0.80
    picks = an["ibm_fez"]["picks"]
    assert set(picks["k_prior"]) != set(picks["k_now"])  # "did not pick the same eight"
    assert "(G = +0.0004 on ibm_fez and +0.0001 on ibm_kingston, against +0.0012 and +0.0004)" in README
    assert "(G = −0.0003, 90% interval −0.0010 to +0.0003) and gained +0.0004 on ibm_kingston" in README
    assert "(r = 0.80 between them) did not pick the same eight" in README
    # A24: the table with one row per finding is on the findings page
    table = (ROOT / "docs" / "findings.md").read_text()
    assert "| USEFUL on ibm_fez (G = +0.0012 in fidelity); NOT SETTLED on ibm_kingston |" in table


def test_the_distance_from_the_ideal_paragraph():
    """Amendment A15, docs/method.md: the Kickoff 35 pair, the Kickoff 33 prior map's largest k, and the one pair the
    two rules swap, with its distances from 1 and their shot noise, recomputed from the archive."""
    from manacitra.circuits import CIRCUITS, GAP
    from manacitra.keptshare import p11_from_bitstrings
    from manacitra.layout import pick_by_kept_share, pick_pairs, usable_pairs

    for day, (kk, lv) in ((2, (4.52, 0.51)), (3, (4.66, 0.52))):
        an = archive.load(f"ibm_fez/k35-day{day}.json")["archived"]["analysis"]
        edges, k, level = [tuple(e) for e in an["edges"]], np.asarray(an["k"]), np.asarray(an["P_no"])
        top = max(usable_pairs(level), key=lambda i: k[i])
        assert edges[top] == (33, 34) and (r(k[top], 2), r(level[top], 2)) == (kk, lv)
    fez = archive.fez_or_kingston("ibm_fez")
    k31, k32, k33 = fez["k31-map"], fez["k32-isolation"], fez["k33-payoff"]
    iso = archive.isolation_analysis(k32, k31["pairs"], k31["archived"]["analysis"]["kA"])
    k, pairs = np.asarray(iso["kD_all27"]), [tuple(p) for p in k33["pairs"]]
    level = np.asarray(iso["L_D_all27"]) * CIRCUITS["A"].ideal_no
    assert r(k.max(), 2) == 1.07
    old, new = set(pick_pairs(k, 8)), set(pick_by_kept_share(k, 8, level))
    assert [pairs[i] for i in old - new] == [(106, 107)] and [pairs[i] for i in new - old] == [(22, 23)]
    (a,), (b,) = old - new, new - old
    assert r(abs(1 - k[a]) - abs(1 - k[b]), 3) == 0.003
    dense = [tuple(q) for q in k32["selection"]["dense_pairs"]]
    D = {"no": [], "off": []}
    for (cond, v), c in zip(k32["plan"], k32["counts"]):
        if cond == "D":
            D[v].append(p11_from_bitstrings(c, len(dense)))
    n = len(D["no"]) * k32["meta"]["shots_per_circuit"]
    for p in ((106, 107), (22, 23)):
        i = dense.index(p)
        no, off = np.mean([x[i] for x in D["no"]]), np.mean([x[i] for x in D["off"]])
        assert r(np.sqrt(no * (1 - no) / n + off * (1 - off) / n) / GAP["A"], 2) == 0.05
    method = " ".join((ROOT / "docs" / "method.md").read_text().split())
    assert "33-34, at k 4.52 and 4.66, with a plain level of 0.51 and 0.52" in method
    assert "from a prior map whose largest k is 1.07" in method
    assert "(106-107 under highest first, 22-23 under |1 − k|)" in method
    assert "differ by 0.003 against a shot noise of about 0.05 in each" in method


# --------------------------------------------------------------------------- Amendment A17: findings 11 to 13
def _cell_F(case_recomputed, cell):
    return case_recomputed["part_A"]["cells"][cell]


def test_finding_11():
    """Kickoff 43, recomputed from the counts (tests/_reuse_runs.py): the verdict and its interval, the split by
    circuit and the mean without XOR_5, the original rule's chains through 33-34, the map's own verdict, and where 143
    sat in each placement."""
    from _reproduce import K43_MAP, K43_RUN, k43_run_recomputed, reuse_doc
    from _reuse_runs import _couplers, k43_map

    m, run = reuse_doc(K43_MAP), reuse_doc(K43_RUN)
    assert (
        hhmm(m["timestamps"]["running"]),
        hhmm(run["timestamps"]["running"]),
        hhmm(run["timestamps"]["finished"]),
    ) == (
        "04:13",
        "04:17",
        "04:54",
    )
    assert "(Kickoff 43; ibm_fez, 10 October 2026: the map at 04:13 UTC, the run from 04:17 to 04:54 UTC)" in README
    an, pl = k43_run_recomputed()
    g, g0 = an["G_reuse"], an["G_no_reuse"]
    assert an["verdict"] == "USEFUL FOR REUSE"
    # the points from the recompute; the interval ends from the run's own bootstrap, as archived (the recompute agrees
    # to 10⁻³ in tests/test_reproduction.py; its last digit can move with the platform's random stream)
    ga = run["archived"]["analysis"]
    assert (r(g["point"], 4), *(r(x, 4) for x in ga["G_reuse"]["ci90"])) == (0.2246, 0.2227, 0.2267)
    assert (r(g0["point"], 4), *(r(x, 4) for x in ga["G_no_reuse"]["ci90"])) == (0.0182, 0.0161, 0.0204)
    assert "the verdict is USEFUL FOR REUSE: G_reuse = +0.2246, 90% interval +0.2227 to +0.2267." in README
    assert "Without reuse, the same circuits gave G = +0.0182 (+0.0161 to +0.0204)." in README
    assert sum(v["shots_pooled"] for v in an["cells"].values()) == 16 * 100_000
    per = {c: an["per_circuit"][c]["G_reuse"]["point"] for c in ("XOR_5", "BV_10", "Sym_9", "Mul_13")}
    assert [r(v, 3) for v in per.values()] == [0.743, 0.288, 0.035, -0.167]
    assert r(np.mean([per[c] for c in ("BV_10", "Sym_9", "Mul_13")]), 3) == 0.052
    assert (
        "By circuit, G_reuse was +0.743 for XOR_5, +0.288 for BV_10, +0.035 for Sym_9 and −0.167 for Mul_13" in README
    )
    assert "Without XOR_5 the mean is +0.052." in README
    # Amendment A1: the as-fixed rule's eight chains, all through 33-34
    a = k43_map(m)
    e = [tuple(x) for x in a["edges"]].index((33, 34))
    assert (r(a["k"][e], 2), r(a["P_no"][e], 2)) == (4.65, 0.52)
    assert all((33, 34) in _couplers(v["beside_not_run"]["as_fixed"]["chain"]) for v in pl.values()) and len(pl) == 8
    assert "all eight chains would have gone through coupler 33-34 (k 4.65, plain level 0.52)" in README
    assert a["map_verdict_all_edges"]["verdict"] == a["map_verdict_after_filter"]["verdict"] == "NOT SETTLED"
    assert "The map's own verdict that morning was NOT SETTLED." in README
    # where 143 sat: never retired in XOR_5's and BV_10's calibration chains, once in Sym_9's, four times in Mul_13's;
    # never on a map chain
    times = {}
    for c in ("XOR_5", "BV_10", "Sym_9", "Mul_13"):
        row = run["placements"][f"{c}|reuse"]
        assert 143 not in pl[f"{c}|reuse"]["map"]["chain"] and 143 in row["calibration"]["chain"]
        times[c] = row["calibration"]["resets_on_physical_qubit"].get("143", 0)
    assert times == {"XOR_5": 0, "BV_10": 0, "Sym_9": 1, "Mul_13": 4}
    assert sorted(per, key=per.get)[-2:] == ["BV_10", "XOR_5"]
    assert "in Sym_9, 143's line was retired once, and in Mul_13, four times. The map's chains kept 143 out" in README


def test_finding_11_the_circuits_and_their_sources():
    """The four circuits are fetched, not copied: each names its repository, a full commit and the SHA-256 the runs
    used, and the structure the text relies on is in the record."""
    from _reproduce import K43_RUN, reuse_doc

    circ = reuse_doc(K43_RUN)["circuits"]
    assert sorted(circ) == ["BV_10", "Mul_13", "Sym_9", "XOR_5"]
    for c in circ.values():
        s = c["source"]
        assert s["repository"] in ("github.com/ruadapt/CaQR", "github.com/pnnl/QASMBench")
        assert len(s["commit"]) == 40 and len(s["sha256"]) == 64
    x = circ["XOR_5"]["reuse"]
    assert (x["w"], x["cz"], x["measures"], x["resets"]) == (3, 5, 6, 3)
    assert x["resets_per_line"] == [1, 0, 2] and x["measures_per_line"][2] == 3
    assert "XOR_5's reuse circuit, three lines of which two are retired" in README


def test_finding_12():
    """Kickoffs 44 to 46, recomputed from the counts: the collapsing and holding chains, the five explanations with
    their verdicts and intervals, and the calibration stamps."""
    from _reproduce import (
        K43_RUN,
        K44,
        K45,
        K46,
        k43_run_recomputed,
        k44_recomputed,
        k45_recomputed,
        k46_recomputed,
        reuse_doc,
    )

    when = [hhmm(reuse_doc(f)["timestamps"]["running"]) for f in (K44, K45, K46)]
    assert when == ["05:40", "05:57", "07:07"] and "10 October 2026, at 05:40, 05:57 and 07:07 UTC)" in README
    k43, _ = k43_run_recomputed()
    c45, c46 = k45_recomputed()["part_A"]["cells"], k46_recomputed()["part_A"]["cells"]
    ch45, ch46 = reuse_doc(K45)["cells"], reuse_doc(K46)["cells"]

    def F(cells, chains, chain):
        (cell,) = [c for c, v in chains.items() if v["chain"] == chain and c in cells]
        return cells[cell]

    assert reuse_doc(K43_RUN)["placements"]["XOR_5|reuse"]["calibration"]["chain"] == [144, 143, 142]
    a = [
        k43["cells"]["XOR_5|reuse|calibration"]["F"],
        F(c45, ch45, [144, 143, 142])["F"],
        F(c46, ch46, [144, 143, 142])["F"],
    ]
    assert [r(v, 3) for v in a] == [0.087, 0.090, 0.098]
    assert "collapsed on 144-143-142 (F 0.087 in Kickoff 43, 0.090 in Kickoff 45 and 0.098 in Kickoff 46)" in README
    low = {
        "142-143-144": F(c45, ch45, [142, 143, 144]),
        "136-143-142": F(c46, ch46, [136, 143, 142]),
        "136-143-144": F(c46, ch46, [136, 143, 144]),
        "143-144-145": F(c46, ch46, [143, 144, 145]),
    }
    assert {k: (r(v["F"], 3), v["class"]) for k, v in low.items()} == {
        "142-143-144": (0.071, "LOW"),
        "136-143-142": (0.091, "LOW"),
        "136-143-144": (0.094, "LOW"),
        "143-144-145": (0.074, "LOW"),
    }
    assert (
        "mirrored, on 142-143-144 (0.071); on 136-143-142 (0.091) and 136-143-144 (0.094); and on 143-144-145 (0.074)."
        in README
    )
    e45, k46 = F(c45, ch45, [143, 142, 141]), F(c46, ch46, [141, 142, 143])
    assert (r(e45["F"], 3), e45["class"], r(k46["F"], 3), k46["class"]) == (0.665, "HIGH", 0.467, "MIDDLE")
    assert (
        "143-142-141 held (Kickoff 45, F 0.665), and 141-142-143 fell to the middle band (Kickoff 46, 0.467)" in README
    )
    healthy = [k43["cells"]["XOR_5|reuse|map"], F(c45, ch45, [132, 131, 138]), F(c46, ch46, [132, 131, 138])]
    assert [r(v["F"], 3) for v in healthy] == [0.830, 0.829, 0.837] and r(
        F(c45, ch45, [125, 124, 123])["F"], 3
    ) == 0.784
    assert (
        "132-131-138 (0.830 in Kickoff 43, 0.829 in Kickoff 45 and 0.837 in Kickoff 46) and 125-124-123 (0.784)"
        in README
    )
    region = [k43["cells"]["XOR_5|no_reuse|calibration"]["F"], c45["F"]["F"]]
    assert ch45["F"]["chain"] == [124, 123, 136, 143, 142, 141] and [r(v, 3) for v in region] == [0.887, 0.868]
    assert "124-123-136-143-142-141, scored 0.887 in Kickoff 43 and 0.868 in Kickoff 45." in README
    # the five explanations
    p44 = k44_recomputed()
    d, adj = p44["D"]["c"], p44["beside_after_data"]["t1_decay_in_R0"]["D_c_with_T1_adjusted_eps"]
    assert p44["verdict"] == "NOT SUPPORTED" and reuse_doc(K44)["fixed_before_the_data"]["delta_c"] == 0.02
    a44, a45, a46 = (reuse_doc(f)["archived"]["analysis"] for f in (K44, K45, K46))  # interval ends, as archived
    ci = a44["D"]["c"]["ci90"]
    assert (r(d["point"], 3), r(ci[0], 3), r(ci[1], 3), r(adj, 3)) == (-0.034, -0.039, -0.028, -0.042)
    assert "D = −0.034, 90% interval −0.039 to −0.028, below the margin of 0.02." in README
    assert "Corrected with the published T1, after the data, D is −0.042. The verdict did not change." in README
    v45 = k45_recomputed()
    rep, idle = v45["part_B"]["verdicts"]["H_repeat"], v45["part_B"]["verdicts"]["H_idle"]
    assert rep["verdict"] == "NOT SUPPORTED" and idle["verdict"] == "SUPPORTED"
    ci_rep, ci_idle = (a45["part_B"]["verdicts"][h]["ci90"] for h in ("H_repeat", "H_idle"))
    assert (r(rep["D"], 3), r(ci_rep[0], 3), r(ci_rep[1], 3)) == (-0.018, -0.021, -0.014)
    assert (r(idle["D"], 3), r(ci_idle[0], 3), r(ci_idle[1], 3)) == (0.031, 0.026, 0.035)
    assert r(v45["beside_after_data"]["D_x_I2_without_141"], 3) == 0.014
    assert "NOT SUPPORTED, D = −0.018 (−0.021 to −0.014)." in README
    assert "SUPPORTED by its rule, D = +0.031 (+0.026 to +0.035)." in README and "(without it, D is +0.014" in README
    pub45 = reuse_doc(K45)["published_at_build"]["142"]["readout_error"]
    m44, m45 = p44["T_C_table"]["142"]["e_m"], v45["part_B"]["q142_first_mid_err"]
    m46 = k46_recomputed()["part_B"]["c_mid_err_142"]
    assert (r(m44, 3), r(m45, 3), r(m44 / pub45, 1), r(m45 / pub45, 1)) == (0.026, 0.049, 8.3, 15.6)
    assert (r(m46, 3), r(k46_recomputed()["part_B"]["q142_mid_err_over_readout"], 1)) == (0.004, 1.3)
    assert r((1 - m45) ** 3, 2) == 0.86 and 0.09 < r(a[1] / healthy[1]["F"], 2) < 0.12
    assert "0.026 in Kickoff 44 and 0.049 in Kickoff 45, 8.3 and 15.6 times its published readout error" in README
    assert "by a factor of about (1 − 0.049)³ = 0.86" in README and "(0.004 in Kickoff 46, 1.3 times)" in README
    sp = k46_recomputed()["part_B"]["H_spectator"]
    assert sp["verdict"] == "NOT SUPPORTED" and sp["margin"] == 0.05
    ci = a46["part_B"]["H_spectator"]["ci90"]
    assert (r(sp["D"], 3), r(ci[0], 3), r(ci[1], 3)) == (-0.003, -0.018, 0.011)
    assert "NOT SUPPORTED, D = −0.003 (−0.018 to +0.011), below the margin of 0.05." in README
    assert k46_recomputed()["part_A"]["patterns"] == ["no fixed pattern holds: reported as observed, with no reading"]
    # the stamps: 03:16:31 at the builds of 43 to 45; 05:52:36 at 06:19 with the CZ figures changed; 06:12:47 at 46,
    # with the region's readout, T1 and T2 unchanged
    s = [reuse_doc(f)["meta"]["calibration_last_update_utc"] for f in (K43_RUN, K44, K45, K46)]
    assert s == ["2026-10-10T03:16:31Z"] * 3 + ["2026-10-10T06:12:47Z"]
    chk = reuse_doc(K46)["published_at_check"]
    assert (chk["calibration_last_update_utc"], hhmm(chk["read_utc"])) == ("2026-10-10T05:52:36Z", "06:19")
    assert hhmm(reuse_doc(K45)["timestamps"]["running"]) == "05:57"  # 05:56:44, four minutes after 05:52:36
    cz45, cz46 = reuse_doc(K45)["published_cz_on_chains"], chk["published_cz_on_chains"]
    assert cz45["143-144"] != cz46["143-144"] and (r(cz45["143-144"], 4), r(cz46["143-144"], 4)) == (0.0022, 0.0026)
    p45, p46, b46 = reuse_doc(K45)["published_at_build"], chk["published"], reuse_doc(K46)["published_at_build"]
    for q in p46:
        for f in ("readout_error", "T1", "T2"):
            assert p45[q][f] == p46[q][f] == b46[q][f], (q, f)
    assert "At 06:19 UTC, when Kickoff 46 was checked, it read 05:52:36 UTC, four minutes before Kickoff 45" in README
    assert "Kickoff 46 ran under 06:12:47 UTC, a later calibration than Kickoffs 43 to 45" in README


def test_finding_13():
    """Kickoff 47, recomputed from the counts: Part A's cells and gains, Part B's losses, the fit, the scheduled waits,
    and what changed between calibrations."""
    from _reproduce import K46, K47, k46_recomputed, k47_recomputed, reuse_doc

    doc = reuse_doc(K47)
    assert (hhmm(doc["timestamps"]["running"]), hhmm(doc["timestamps"]["finished"])) == ("10:54", "10:57")
    assert "(Kickoff 47; ibm_fez, 10 October 2026, 10:54 to 10:57 UTC)" in README
    k = k47_recomputed()
    c, g = k["part_A"]["cells"], k["part_A"]["gains_beside"]
    assert k["part_A"]["H_phase"] == "SUPPORTED" and doc["cells"]["A0"]["chain"] == [144, 143, 142]
    a = doc["archived"]["analysis"]  # interval ends, as archived; points from the recompute
    ca, ga = a["part_A"]["cells"], a["part_A"]["gains_beside"]
    assert [r(c["A0"]["F"], 3)] + [r(x, 3) for x in ca["A0"]["ci90"]] == [0.071, 0.069, 0.073]
    assert [r(c["A1"]["F"], 3)] + [r(x, 3) for x in ca["A1"]["ci90"]] == [0.843, 0.838, 0.847]
    assert [r(g["A"]["gain"], 3)] + [r(x, 3) for x in ga["A"]["ci90"]] == [0.772, 0.767, 0.777]
    assert "(F 0.071, 90% interval 0.069 to 0.073), and scored 0.843 (0.838 to 0.847)" in README
    assert "a gain of +0.772 (+0.767 to +0.777)." in README
    # ruling R1: the pulses went only into the idle windows long enough to hold the sequence (four pulses per window)
    assert "into every idle window of the chain long enough to hold the sequence: a gain" in README
    skipped = 0
    for cell in ("A1", "J1", "C1"):
        rec = doc["refocusing"]["cells"][cell]
        for q_, before in rec["idle_windows_dt_before"].items():
            held = [w for w in before if w >= 100]
            assert rec["pulses_inserted_per_qubit"][q_] == 4 * len(held), (cell, q_)
            skipped += len(before) - len(held)
    assert skipped > 0 and "XY4" in doc["refocusing"]["sequence"]
    assert [r(c[x]["F"], 3) for x in ("J0", "J1", "C0", "C1")] == [0.875, 0.863, 0.833, 0.784]
    assert [r(-g[x]["gain"], 3) for x in ("C", "J")] == [0.049, 0.011]
    assert "chain J, 143-144-145, scored 0.875 without pulses and 0.863 with them" in README
    assert "and the healthy chain C, 132-131-138, 0.833 and 0.784." in README
    assert "Refocusing cost the healthy chain 0.049 and chain J 0.011." in README
    q = k["part_B"]["qubits"]["143"]
    assert q["kind_of_loss"] == "REFOCUSABLE" and doc["taus_us"] == [0, 1, 2, 3.4, 4, 8]
    qa = a["part_B"]["qubits"]["143"]
    assert [r(q["r_3p4"], 3)] + [r(x, 3) for x in qa["r_ci90"]] == [0.223, 0.215, 0.231]
    assert [r(q["e_3p4"], 3)] + [r(x, 3) for x in qa["e_ci90"]] == [0.015, 0.012, 0.018]
    assert "was 0.223 (0.215 to 0.231); with one refocusing pulse halfway" in README
    assert "the loss was 0.015 (0.012 to 0.018)." in README
    w = doc["refocusing"]["cells"]["A0"]["idle_windows_dt_before"]["143"]
    dt = doc["refocusing"]["dt_s"]
    assert len(w) == 3 and (r(min(w) * dt * 1e6, 2), r(max(w) * dt * 1e6, 2)) == (3.34, 3.37)
    assert "143 waited in three windows of 3.34 to 3.37 µs while its neighbours were measured and reset." in README
    fit = q["ramsey_fit"]
    assert (r(1000 * fit["f_MHz"], 1), r(1000 * fit["f_err"], 1)) == (46.7, 2.7)
    assert "a single offset of 46.7 ± 2.7 kHz describes 143's Ramsey curve over 0 to 8 µs." in README
    assert r(q["ramsey_P1"]["8"], 2) == 0.80 and "143's reached 0.80 at 8 µs" in README
    assert '"T₂ is reported from a Hahn echo sequence"' in README
    assert doc["citation_T2"]["says"].startswith("T2 is reported from a Hahn echo sequence")
    s46 = k46_recomputed()["beside_after_data"]["spectator_P1_in_S0_vs_T2"]
    p144 = [s46[k]["P1_S0"] for k in ("144;143", "144;145")]
    p143 = [s46[k]["P1_S0"] for k in ("143;136", "143;142", "143;144")]
    q144 = k["part_B"]["qubits"]["144"]
    assert {r(v, 2) for v in p144} == {0.15, 0.16} and r(np.mean(p144), 2) == 0.16
    assert r(min(p144), 2) == 0.15 and r(q144["r_3p4"], 3) == 0.012
    assert (r(min(p143), 2), r(max(p143), 2), r(q["r_3p4"], 3)) == (0.22, 0.24, 0.223)
    wait46 = k46_recomputed()["beside_after_data"]["tau_s0_s"]
    assert r(wait46 * 1e6, 2) == 3.37 and "its P(1) after a wait of 3.37 µs in superposition" in README
    stamps = [reuse_doc(f)["meta"]["calibration_last_update_utc"] for f in (K46, K47)]
    assert stamps == ["2026-10-10T06:12:47Z", "2026-10-10T09:56:30Z"]
    assert "to 0.012 under the 09:56 stamp (here, the rise in P(1) over a wait of 3.4 µs)" in README
    assert "143's stayed (0.22 to 0.24 in Kickoff 46, 0.223 here)." in README


def test_the_reuse_wait_picture():
    """Finding 13's picture: made from the data by docs/make_diagrams.py, referenced from finding 13, and its alt text
    carries the numbers of the data."""
    from _reproduce import k47_recomputed

    findings = (ROOT / "docs" / "findings.md").read_text()
    item = findings.split('<a id="finding-13"></a>', 1)[1]
    assert "](diagrams/reuse-wait.svg)" in item and (DIAGRAMS / "reuse-wait.png").is_file()
    alt = " ".join(item.split("![", 1)[1].split("](diagrams/reuse-wait.svg)", 1)[0].split())
    k = k47_recomputed()
    c, q = k["part_A"]["cells"], k["part_B"]["qubits"]["143"]
    for cell in ("A0", "A1", "C0", "C1"):
        assert f"{c[cell]['F']:.3f}" in alt, cell
    assert f"{q['ramsey_P1']['0']:.3f}" in alt and f"{q['ramsey_P1']['8']:.2f}" in alt
    assert max(q["echo_P1"].values()) <= 0.03 and "stay at 0.03 or below" in alt
    assert "46.7 ± 2.7 kHz" in alt and "three windows of 3.34 to 3.37 µs" in alt
    text = svg_text(DIAGRAMS / "reuse-wait.svg")
    assert "a fit: one steady offset, 46.7 ± 2.7 kHz" in text and "10 October 2026" in text


# --------------------------------------------------------------------------- Amendment A18: the wait, rerun
def test_the_wait_test_pages():
    """docs/method.md's paragraph on the wait test and docs/reproduce.md carry the numbers of the code, the offline
    snapshot and the archive: the exact ideal and the sensitivity, the blind offset, the job's size, M's waits in the
    snapshot and 143's live waits in Kickoff 47, and the two calibration stamps of 144's change."""
    pytest.importorskip("qiskit_ibm_runtime")
    from _reproduce import K46, K47, reuse_doc
    from qiskit_ibm_runtime.fake_provider import FakeFez

    from manacitra import wait

    method = " ".join((ROOT / "docs" / "method.md").read_text().split("\n## The wait test\n", 1)[1].split())
    page = " ".join((ROOT / "docs" / "reproduce.md").read_text().split())
    ideal = wait.wait_test_ideal()
    assert len(ideal) == 32 and 2**wait.WAIT_TEST_CLBITS == 64 and "uniform over 32 of the 64 outcomes" in method
    s = wait.wait_test_sensitivity()
    assert r(s["F_each_wait"], 3) == r(s["F_one_wait"], 3) == 0.5 and "or in only one, gives 0.5" in method
    fez = FakeFez()
    plain = wait.build_wait_test((144, 143, 142), False, fez)
    total = sum(wait.idle_windows(wait.scheduled(plain, fez.target), 143))
    assert round(1 / (total * fez.dt) / 1e3) == 105 and "about 105 kHz with the offline ibm_fez snapshot's" in method
    circuits, labels, shots = wait.wait_run((144, 143, 142), fez)
    assert len(circuits) == 58 and sum(shots) == 292_000 and "58 circuits and 292,000 shots" in page
    assert {n for lab, n in zip(labels, shots) if lab["part"] == "W"} == {10_000} and "10,000 shots each" in page
    assert {n for lab, n in zip(labels, shots) if lab["part"] == "B"} == {4_000} and "4,000 shots each" in page
    assert wait.KICKOFF_47_WAITS_DT == (0, 250, 500, 850, 1000, 2000)
    assert "waits of 0, 250, 500, 850, 1,000 and 2,000 dt" in page
    assert {v["dt"] for v in wait.wait_lengths(fez, (144, 143, 142)).values()} == {786}
    live = reuse_doc(K47)["refocusing"]["cells"]["A0"]["idle_windows_dt_before"]["143"]
    assert live == [836, 836, 842] and "M's waits are 786 dt in the snapshot" in page
    assert "143's waits on the live backend were 836, 836 and 842 dt" in page
    stamps = [reuse_doc(f)["meta"]["calibration_last_update_utc"] for f in (K46, K47)]
    assert [t[11:16] for t in stamps] == ["06:12", "09:56"]
    assert "from 0.15 under IBM's 06:12 UTC calibration stamp (Kickoff 46) to 0.012 under the 09:56 UTC stamp" in page


# --------------------------------------------------------------------------- Amendment A19: finding 14
def _item_14() -> str:
    findings = (ROOT / "docs" / "findings.md").read_text()
    return " ".join(findings.split('<a id="finding-14"></a>', 1)[1].split("\n## ", 1)[0].split("![", 1)[0].split())


def test_finding_14():
    """Kickoff 48, recomputed from the counts: what ran and when, the rule and its verdict, the five chains, the wait
    length, 143 a day later across the calibration stamps, the theory's numbers, and the residuals of the two chains
    with small losses. Interval ends are quoted from the archived analysis, points from the recompute."""
    from _reproduce import K43_RUN, K46, K47, K48, k47_recomputed, k48_recomputed, reuse_doc

    item = _item_14()
    doc = reuse_doc(K48)
    m, a = doc["meta"], doc["archived"]["analysis"]
    k = k48_recomputed()
    # what ran, and when
    assert (hhmm(doc["timestamps"]["running"]), hhmm(doc["timestamps"]["finished"])) == ("02:13", "02:14")
    assert "(Kickoff 48; ibm_fez, 11 October 2026, 02:13 to 02:14 UTC)" in item
    assert m["built_from"]["commit"].startswith("f28642a") and m["built_from"]["version"] == "0.4.0"
    assert "built unedited from this repository at commit `f28642a` (v0.4.0)" in item
    chains = ["-".join(map(str, m["chains"][n])) for n in ("143", "142", "124", "144", "131")]
    assert "five chains L1-M-L3, each without and with XY4 refocusing pulses: " + ", ".join(chains[:4]) in item
    assert f"and {chains[4]}, in four interleaved copies of 5,000 shots" in item
    assert m["copies"] == 4 and m["shots_by_part"] == {"W": 5000, "B": 2000} and "twice with 2,000 shots" in item
    assert [tuple(g) for g in m["groups"]] == [tuple(g) for g in wait.KICKOFF_47_GROUPS]
    us = [r(w * m["T_M"]["dt_s"] * 1e6, 2) for w in m["waits_dt"]]
    assert us == [0, 1, 2, 3.4, 4, 8, 10.45, 16] and m["T_M"]["used_dt"] == [2612]
    assert (
        "at Kickoff 47's six waits, at a wait equal to the circuit's own, T_M = 2,612 dt (10.45 µs), "
        "and at 16 µs" in item
    )
    tms = {v["T_M_dt"] for v in m["T_M"]["per_chain"].values()}
    assert tms == {2611} and "2,611 dt on every chain, made even." in item
    assert len(doc["counts"]) == 104 and m["calibration_last_update_utc"] == "2026-10-11T01:35:00Z"
    assert "One job of 104 circuits, under IBM's calibration stamp of 01:35 UTC." in item
    # the rule and the verdict
    fixed = doc["fixed_before_the_data"]
    assert (fixed["margin"], fixed["informative_floor"]) == (0.15, 0.2)
    assert "has its 90% interval inside ±0.15" in item and "entirely above 0.2" in item
    assert k["H48"] == "AGREE" and k["informative_chains"] == ["143", "142", "124"]
    assert "The verdict: AGREE, informative, with three informative chains." in item
    # the five chains
    for n, chain in zip(("143", "142", "124", "144", "131"), chains):
        p, pa = k["prediction"][n], a["prediction"][n]
        loss = f"{p['dP_R_TM']:.3f}"
        f_no, f_ref, f_pred = (f"{p[x]:.3f}" for x in ("F_no", "F_ref", "F_pred"))
        d = f"{p['d_M']:+.3f}".replace("-", "−")
        lo, hi = (f"{x:+.3f}".replace("-", "−") for x in pa["d_M_ci90"])
        if n == "143":
            want = (
                f"**{chain}**, with {n} waiting: Ramsey loss at T_M {loss}; F {f_no} without refocusing and {f_ref} "
                f"with; F_pred {f_pred}; d_M {d} (90% interval {lo} to {hi})."
            )
        else:
            want = (
                f"**{chain}**, with {n} waiting: Ramsey loss {loss}; F {f_no} and {f_ref}; F_pred {f_pred}; "
                f"d_M {d} ({lo} to {hi})."
            )
        assert want in item, want
        assert p["inside_margin"] and not p["outside_margin"]
        assert abs(r(p["F_no"], 3) - r(pa["F_no"], 3)) < 1e-12 and abs(p["d_M"] - pa["d_M"]) < 1e-9
    p143 = k["prediction"]["143"]
    assert (r(p143["F_no"], 3), r(p143["F_pred"], 3), r(p143["d_M"], 3)) == (0.389, 0.386, 0.003)
    assert min(abs(p["d_M"]) for p in k["prediction"].values()) == abs(p143["d_M"])
    assert "The closest case: 0.389 measured, 0.386 predicted." in item
    informative = [a["prediction"][n]["dP_R_TM_ci90"] for n in ("143", "142", "124")]
    others = [a["prediction"][n]["dP_R_TM_ci90"] for n in ("144", "131")]
    assert min(lo for lo, _ in informative) > 0.33 and max(hi for _, hi in others) < 0.09
    assert "90% intervals entirely above 0.33, and the other two's lay entirely below 0.09." in item
    # the established finding: the exact ideal is the parity, and a phase takes F to cos²(φ/2) = 1 − sin²(φ/2)
    ideal = wait.wait_test_ideal()
    assert len(ideal) == 32 and all(int(key[0]) == sum(map(int, key[1:])) % 2 for key in ideal)
    assert "F without refocusing is 1 − P(parity flipped)" in item
    assert "an established finding about the circuit, on which the rule rests:" in item  # A19, ruling R1
    # the wait length
    pb = k["part_B"]
    assert [pb[q]["kind_of_loss"] for q in ("142", "124")] == ["NOT REPRODUCED"] * 2
    assert [r(pb[q]["r"], 2) for q in ("142", "124")] == [0.06, 0.07]
    assert [r(k["prediction"][q]["dP_R_TM"], 2) for q in ("142", "124")] == [0.35, 0.37]
    assert (
        "with Ramsey losses of 0.06 and 0.07 there, yet they lost 0.35 and 0.37 over the circuit's "
        "10.45 µs wait" in item
    )
    assert "F 0.602 and 0.510 without refocusing, against 0.832 and 0.881 with it." in item
    # 143 a day later
    q = pb["143"]
    q47 = k47_recomputed()["part_B"]["qubits"]["143"]
    assert q["kind_of_loss"] == "REFOCUSABLE" and (r(q["r"], 3), r(q47["r_3p4"], 3)) == (0.260, 0.223)
    assert "REFOCUSABLE again, with a Ramsey loss of 0.260 at 3.4 µs (0.223 in finding 13)." in item
    fit, fit47 = q["ramsey_fit"], q47["ramsey_fit"]
    assert (r(1000 * fit["f_MHz"], 1), r(1000 * fit["f_err"], 1)) == (47.1, 1.8)
    assert (r(1000 * fit47["f_MHz"], 1), r(1000 * fit47["f_err"], 1)) == (46.7, 2.7)
    assert "gives 47.1 ± 1.8 kHz, against finding 13's fit of 46.7 ± 2.7 kHz." in item
    stamps = [reuse_doc(f)["meta"]["calibration_last_update_utc"] for f in (K43_RUN, K46, K47, K48)]
    assert [s[11:16] for s in stamps] == ["03:16", "06:12", "09:56", "01:35"] and stamps[-1][:10] == "2026-10-11"
    assert "from 03:16 UTC on 10 October to 01:35 UTC on 11 October, in runs spread over about 22 hours" in item
    span = (_utc(reuse_doc(K48)["timestamps"]["finished"]) - _utc(reuse_doc(K43_RUN)["timestamps"]["running"])).seconds
    assert round(span / 3600) == 22
    assert "collapsed on it under the 03:16, 06:12 and 09:56 stamps (findings 12 and 13)" in item
    assert "and the wait test read 0.389 under the 01:35 stamp." in item
    apart = _utc(doc["timestamps"]["running"]) - _utc(reuse_doc(K47)["timestamps"]["running"])
    assert round(apart.total_seconds() / 3600) == 15 and "under the last two stamps, about 15 hours apart." in item
    ram, ci = q["ramsey_P1"], a["part_B"]["143"]["ramsey_ci90"]
    assert (r(ram["2000"], 3), r(ram["4000"], 3)) == (0.627, 0.452) and ram["4000"] < ram["2000"] - 0.1
    assert ci["4000"][1] < ci["2000"][0] and k["beside"]["oscillation_143_8_or_TM_to_16us"]
    assert (
        "143's Ramsey P(1) fell from 0.627 at 8 µs to 0.452 at 16 µs, by more than 0.1 with separated "
        "intervals." in item
    )
    # the theory
    assert (r(fit["T_us"], 1), round(fit47["T_us"]), round(fit47["T_err"])) == (11.5, 108, 74)
    assert (r(q47["ramsey_P1"]["8"], 2), r(ram["2000"], 3)) == (0.80, 0.627)
    assert (
        "fitted at 11.5 µs, against 108 ± 74 µs the day before (a fit to waits up to 8 µs; at 8 µs its Ramsey P(1) "
        "was 0.80 then and 0.627 now)" in item
    )
    assert (r(q["echo_loss"]["2612"], 2), r(q["ramsey_loss"]["2612"], 2)) == (0.03, 0.58)
    assert "(an echo loss of 0.03 at 10.45 µs, against a Ramsey loss of 0.58)" in item
    assert r(p143["F_no"], 2) == 0.39 and "F without refocusing was 0.39, not near 0" in item
    cycles = fit["f_MHz"] * 2612 * m["T_M"]["dt_s"] * 1e6
    assert r(cycles, 1) == 0.5 and "about half a cycle over the 10.45 µs wait" in item
    # A19, ruling R1: the disconfirmer names a later run, since this job's echo is what the reading was drawn from
    assert "This job's echo is part of what the reading was drawn from, so it cannot test it." in item
    assert "if each decayed at about 11.5 µs, it is faster." in item and r(fit["T_us"], 1) == 11.5
    # the chains with small losses
    d144, d131 = (k["prediction"][n]["d_M"] for n in ("144", "131"))
    assert (f"{d144:+.3f}", f"{d131:+.3f}") == ("-0.057", "+0.094")
    assert "residuals of −0.057 (144) and +0.094 (131)" in item
    assert r(-k["prediction"]["131"]["gain"], 3) == 0.047 and "refocusing lowered F by 0.047." in item
    assert "one processor, one day and five qubits" in item and "Manacitra does not rank machines." in item


def test_finding_14_beside_the_findings():
    """The README's limit line, the kickoffs row, the pages that point to finding 14, and what has not been shown."""
    from _reproduce import K47, K48, reuse_doc

    doc = reuse_doc(K48)
    assert doc["meta"]["processor"] == "ibm_fez" and doc["meta"]["calibration_last_update_utc"].startswith("2026-10-11")
    assert (
        "- **One processor, one day, five qubits, for finding 14.** Finding 14 is from one job on ibm_fez on 11 "
        "October 2026, under one published calibration stamp." in README
    )
    assert "| 48, 11 October 2026 |" in README and "`ibm_fez/k48-wait-test.json`" in README
    method = " ".join((ROOT / "docs" / "method.md").read_text().split())
    page = " ".join((ROOT / "docs" / "reproduce.md").read_text().split())
    assert "It ran on five chains of ibm_fez on 11 October 2026" in method and "(findings.md#finding-14)" in method
    assert "The wait test ran on hardware in [finding 14](findings.md#finding-14)" in page
    flat = " ".join(README.split())
    assert "Finding 14 shows the check predicts; it has not been tested as a chooser." in flat
    assert "- **The MERA-style comparison.**" in flat
    assert "- **Other chips.** Findings 11 to 14 are from ibm_fez alone." in flat
    apart = _utc(doc["timestamps"]["running"]) - _utc(reuse_doc(K47)["timestamps"]["running"])
    assert round(apart.total_seconds() / 3600) == 15
    assert "finding 14 fitted it again, about 15 hours later and across one day boundary" in flat
    assert "ran under, over about 22 hours. Finding 15 saw it again on 13 October 2026" in flat  # A22, ruling R1, Q3
    assert "finding 14's calibration stamp. Whether it lasts longer, and why it is there, are not known" in flat


def test_what_was_known_before_findings_13_and_14():
    """Amendment A20: the findings page says what was known before findings 13 and 14, with each source it cites, just
    before what has not been shown, and says plainly that the check has not been tested against those methods. Amendment
    A21: it also cites a reset-heavy experiment on ibm_fez, as context only."""
    findings = (ROOT / "docs" / "findings.md").read_text()
    head = "\n## What was known before these findings\n"
    assert head in findings
    section, after = findings.split(head, 1)[1].split("\n## ", 1)
    assert after.startswith("What it has not shown\n")
    section = " ".join(section.split())
    for cited in (
        "(Ramsey, Physical Review 78, 695, 1950)",
        "(Hahn, Physical Review 80, 580, 1950)",
        "(Viola, Knill and Lloyd, Physical Review Letters 82, 2417, 1999)",
        "(Das, Tannu, Dangwal and Qureshi, MICRO 2021, doi 10.1145/3466752.3480059, arXiv:2109.05309)",
        "(arXiv:2204.14251)",
    ):
        assert cited in section, cited
    # ruling R1, Q1 and Q2: the paper studied how to insert refocusing, so it has its own lead-in, not ADAPT's
    assert (
        "How to insert refocusing for idle qubits of different kinds has been studied too: Niu and Todri-Sanial "
        "(arXiv:2204.14251) used Ramsey experiments on IBM's 7-qubit Lagos to explain why one insertion strategy beat "
        "another for a qubit beside a two-qubit gate." in section
    )
    # Amendment A21: Pokharel, Pan and others, cited as context, neither for nor against the findings
    assert "10.1038/s41567-026-03470-6" in section
    assert "not as evidence for or against findings 13 and 14" in section
    assert "These are established findings, cited and not tested here." in section
    # ruling R1, Q3: finding 13 (10 October) and finding 14 (11 October) each add their own part
    assert (
        "What findings 13 and 14 add is narrower: on one processor, a qubit whose loss a Ramsey wait showed and IBM's "
        "echo-measured T2 did not (finding 13, 10 October), and a rule, fixed before the run, that predicted from one "
        "qubit's Ramsey loss at a circuit's own wait length how a reuse-shaped circuit would fare (finding 14, 11 "
        "October)." in section
    )
    assert "has not been tested" in section
    untested = "Whether that check chooses better than ADAPT, or than refocusing every idle qubit, has not been tested."
    assert untested in section
    flat = " ".join(README.split())
    assert "with refocusing every idle qubit and with ADAPT's choice of qubits to refocus, has not been run." in flat
    assert (
        "the thirty findings in full, with a table of all of them, what was known before them, and what has not "
        "been shown." in flat
    )  # A25


def test_the_wait_test_hardware_picture():
    """Finding 14's picture: made from the data by docs/make_diagrams.py, referenced from finding 14, and its alt text
    carries the numbers of the data."""
    from _reproduce import k48_recomputed

    findings = (ROOT / "docs" / "findings.md").read_text()
    item = findings.split('<a id="finding-14"></a>', 1)[1]
    assert "](diagrams/wait-test-hardware.svg)" in item and (DIAGRAMS / "wait-test-hardware.png").is_file()
    alt = " ".join(item.split("![", 1)[1].split("](diagrams/wait-test-hardware.svg)", 1)[0].split())
    k = k48_recomputed()
    for n in ("143", "142", "124", "144", "131"):
        p = k["prediction"][n]
        chain = "-".join(map(str, p["chain"]))
        want = (
            f"{p['F_no']:.3f} without refocusing against {p['F_pred']:.3f} predicted, and {p['F_ref']:.3f} with"
            if n == "143"
            else (f"{chain}, {p['F_no']:.3f} against {p['F_pred']:.3f}, and {p['F_ref']:.3f}")
        )
        assert want in alt, want
    ram = {q: k["part_B"][q]["ramsey_P1"] for q in ("143", "142", "124", "144")}
    assert f"143 reads {ram['143']['850']:.3f}" in alt and max(ram[q]["850"] for q in ("142", "124", "144")) <= 0.073
    assert f"{ram['124']['850']:.3f} or below" in alt
    at_tm = ", ".join(f"{q} {ram[q]['2612']:.3f}" for q in ("124", "142"))
    assert f"at T_M, 143 reads {ram['143']['2612']:.3f}, {at_tm} and 144 {ram['144']['2612']:.3f}." in alt
    assert f"peaks at {ram['143']['2000']:.3f} at 8 µs and falls to {ram['143']['4000']:.3f} at 16 µs" in alt
    assert max(ram["143"].values()) == ram["143"]["2000"]
    assert f"to {ram['142']['4000']:.3f} and {ram['124']['4000']:.3f}." in alt
    text = svg_text(DIAGRAMS / "wait-test-hardware.svg")
    assert "11 October 2026, 02:13 to 02:14 UTC" in text and "T_M = 10.45 µs" in text
    assert "predicted from M's Ramsey loss at T_M" in text
    index = " ".join((ROOT / "docs" / "index.md").read_text().split())
    assert len(list(DIAGRAMS.glob("*.svg"))) == 16 and "# the sixteen diagrams, from data/" in index  # A28: sixteen


# --------------------------------------------------------------------------- findings 15 to 19 (Amendment A22)
def _q(x, nd: int, sign: bool = False) -> str:
    """x at nd places as the text prints it, with U+2212 for a minus; refuses a value whose rounding half up and
    Python's rounding of the stored number disagree (an exact half case, A19's lesson), which the text must not
    quote at that precision."""
    from decimal import ROUND_HALF_UP, Decimal

    s = f"{float(x):+.{nd}f}" if sign else f"{float(x):.{nd}f}"
    half_up = Decimal(repr(float(x))).quantize(Decimal(1).scaleb(-nd), ROUND_HALF_UP)
    assert Decimal(s) == half_up, f"{x!r} is an exact half case at {nd} places"
    return s.replace("-", "−")


def _item(n: int) -> str:
    """Finding n's item in docs/findings.md, whitespace joined, its picture's alt text left out."""
    findings = (ROOT / "docs" / "findings.md").read_text()
    item = findings.split(f'<a id="finding-{n}"></a>', 1)[1].split("<a id=", 1)[0].split("\n## ", 1)[0]
    return " ".join(item.split("![", 1)[0].split())


HISTORY = "ibm_fez/calibration-history-01.json"
#: the counts of a stamp's row: qubits or edges whose published value changed since the snapshot before it
HISTORY_COUNTS = ("q_T1", "q_T2", "q_frequency", "q_readout_error", "q_prob_meas0_prep1", "q_prob_meas1_prep0")
HISTORY_COUNTS += ("g1_any", "cz_error", "cz_length")


def _history_rows() -> list:
    from _reproduce import reuse_doc

    return reuse_doc(HISTORY)["stamps"]


def _history_after(stamp_utc: str) -> dict:
    """Calibration history 01's row for the stamp published next after stamp_utc."""
    rows = _history_rows()
    i = next(i for i, row in enumerate(rows) if row["stamp_utc"] == stamp_utc)
    return rows[i + 1]


def _history_changed(stamp_utc: str) -> set:
    """What changed at a stamp, by value against the snapshot before it: the counts that are not zero, and every other
    published field that changed (empty if nothing did)."""
    (row,) = [row for row in _history_rows() if row["stamp_utc"] == stamp_utc]
    counts = {f"{c} {row[c]}" for c in HISTORY_COUNTS if row[c] not in ("", "0")}
    other = {x.strip() for x in row["other_values_changed"].split(";") if x.strip()}
    assert (row["any_value_changed"] == "True") == bool(counts or other)
    return counts | other


def _history_publishes_no_frequency() -> bool:
    from _reproduce import reuse_doc

    doc = reuse_doc(HISTORY)
    no_field = "carry no frequency (and no anharmonicity) entry in any snapshot" in doc["how_compared"]
    return no_field and {row["q_frequency"] for row in _history_rows()[1:]} == {"0"}


def _posted(record: str, key: str = "rule") -> tuple[int, str, str]:
    from _reproduce import reuse_doc

    r = reuse_doc(record)["meta"][key]
    return r["posted"]["issue"], r["posted"]["url"], hhmm(r["posted"]["created_utc"])


def test_the_posted_rules_are_published_unchanged():
    """Amendment A22, 2b: the six rule files are in data/ibm_fez/ byte for byte, each with the SHA-256 posted publicly
    before its run, and each run's record names its rule, its hash and the issue it was posted in, before the job was
    submitted."""
    from _reproduce import K49, K50, K51, K52, K53, reuse_doc

    posted = {
        "k49-rule-v1-superseded.md": "abaf6ee9b2a3598a5bd1f31d0a83e2752bb7926dba5b2adef7d50c6f56ddb6f7",
        "k49-rule.md": "55cd962a29a780848dd6bace0c238cb0530b684b03da09659965be98c019fb40",
        "k50-rule.md": "8a3228b03e89fca5a81e101f59d9d65757a74a6c06f2b0205f158770b85da039",
        "k51-rule.md": "2489342e5207dd253a5ef208c82618834ce23264f89d819d5a29a9206fe1f9b4",
        "k52-rule.md": "fde743d9a103a48968973f1de2ee4d6126e340b1212e42872524b6e7672d03fb",
        "k53-rule.md": "f671af475c1b0b8fd47949e74507b4877739374577f12239f20ef891b631b7da",
    }
    import hashlib

    for name, sha in posted.items():
        text = (archive.data_dir() / "ibm_fez" / name).read_bytes()
        assert hashlib.sha256(text).hexdigest() == sha, name
        assert b"The rule is not changed after the data, whatever they show." in text
    issues = {"k49-rule-v1-superseded.md": 29, "k49-rule.md": 30, "k50-rule.md": 31, "k51-rule.md": 32}
    issues |= {"k52-rule.md": 33, "k53-rule.md": 33}
    for rec, key in (
        (K49, "rule"),
        (K49, "rule_superseded"),
        (K50, "rule"),
        (K51, "rule"),
        (K52, "rule"),
        (K53, "rule"),
    ):
        m = reuse_doc(rec)["meta"]
        r = m[key]
        assert r["sha256"] == posted[r["file"]] and r["posted"]["issue"] == issues[r["file"]]
        assert r["posted"]["url"] == f"https://github.com/dogma-guru/manacitra/issues/{issues[r['file']]}"
        assert _utc(r["posted"]["created_utc"]) < _utc(m["submitted_utc"]), (rec, key)
    # Kickoff 53's rule was posted with Kickoff 52's, before Kickoff 52 ran
    assert _utc(reuse_doc(K53)["meta"]["rule"]["posted"]["created_utc"]) < _utc(reuse_doc(K52)["meta"]["submitted_utc"])
    # Amendment A23: Kickoffs 54 and 55's rules, each in its processor's folder, posted before the first submission
    from _reproduce import K54, K55

    for rec, folder, name, sha, issue in (
        (K54, "ibm_fez", "k54-rule.md", "a918698bf29d9f733e3883e5ba20cf18bf0f8e3bd0e395d06d3e9b9d4331f384", 35),
        (K55, "ibm_kingston", "k55-rule.md", "5140b99ee4f3e7e097e508b5dba42a0acbc5ca84a44c0aa34f4d319148d71b28", 36),
    ):
        text = (archive.data_dir() / folder / name).read_bytes()
        assert hashlib.sha256(text).hexdigest() == sha, name
        assert b"The rule is not changed after the data, whatever they show." in text
        doc = reuse_doc(rec)
        r_ = doc["meta"]["rule"]
        assert (r_["file"], r_["sha256"], r_["posted"]["issue"]) == (name, sha, issue)
        assert r_["posted"]["url"] == f"https://github.com/dogma-guru/manacitra/issues/{issue}"
        first = doc.get("first_submission", {}).get("submitted_utc", doc["meta"]["submitted_utc"])
        assert _utc(r_["posted"]["created_utc"]) < _utc(first) <= _utc(doc["meta"]["submitted_utc"]), rec


def _bullet(chain: str, n: str, p: dict, pa: dict, first: bool) -> str:
    loss, f_no, f_ref, f_pred = (_q(p[x], 3) for x in ("dP_R_TM", "F_no", "F_ref", "F_pred"))
    d = _q(p["d_M"], 3, True)
    lo, hi = (_q(x, 3, True) for x in pa["d_M_ci90"])
    if first:
        return (
            f"**{chain}**, with {n} waiting: Ramsey loss at T_M {loss}; F {f_no} without refocusing and {f_ref} "
            f"with; F_pred {f_pred}; d_M {d} (90% interval {lo} to {hi})."
        )
    return (
        f"**{chain}**, with {n} waiting: Ramsey loss {loss}; F {f_no} and {f_ref}; F_pred {f_pred}; "
        f"d_M {d} ({lo} to {hi})"
    )


def test_finding_15():
    """Kickoff 49, recomputed from the counts by Kickoff 48's recompute: what ran and when, the posted rule, the five
    chains and the verdict, 144's miss against 11 October and within the job, and 143's offset beside the verdict.
    Interval ends from the archived analysis, points from the recompute."""
    from _reproduce import K48, K49, k48_recomputed, k49_recomputed, reuse_doc

    item = _item(15)
    doc, d48 = reuse_doc(K49), reuse_doc(K48)
    m, a = doc["meta"], doc["archived"]["analysis"]
    k, k48 = k49_recomputed(), k48_recomputed()
    assert (hhmm(doc["timestamps"]["running"]), hhmm(doc["timestamps"]["finished"])) == ("17:27", "17:30")
    assert "(Kickoff 49; ibm_fez, 13 October 2026, 17:27 to 17:30 UTC)" in item
    b = m["built_from"]
    assert b["commit"].startswith("a55354d") and b["version"] == "0.5.0"
    assert b["wait_py_sha256"] == d48["meta"]["built_from"]["wait_py_sha256"]
    assert (
        "built unedited from this repository at commit `a55354d` (v0.5.0), whose `wait.py` is the one finding 14 ran"
        in item
    )
    assert m["chains"] == d48["meta"]["chains"] and m["groups"] == d48["meta"]["groups"]
    assert m["waits_dt"] == d48["meta"]["waits_dt"] and m["copies"] == 4
    assert m["shots_by_part"] == {"W": 5000, "B": 2000}
    assert "in four interleaved copies of 5,000 shots, with Part B's circuits twice with 2,000 shots" in item
    assert {v["T_M_dt"] for v in m["T_M"]["per_chain"].values()} == {2611} and m["T_M"]["used_dt"] == [2612]
    assert r(2612 * m["T_M"]["dt_s"] * 1e6, 2) == 10.45
    assert "T_M was again 2,611 dt on every chain, made even to 2,612 dt (10.45 µs)." in item
    assert len(doc["counts"]) == 104 and m["calibration_last_update_utc"] == "2026-10-13T16:08:33Z"
    days = (_utc(m["calibration_last_update_utc"]) - _utc(d48["meta"]["calibration_last_update_utc"])).total_seconds()
    assert r(days / 86400, 2) == 2.61
    assert (
        "One job of 104 circuits, under IBM's calibration stamp of 16:08:33 UTC, 2.61 days after finding 14's." in item
    )
    # the rule, posted
    assert doc["fixed_before_the_data"] == d48["fixed_before_the_data"]
    n, url, when = _posted(K49)
    assert (n, when) == (30, "17:19") and f"([issue 30]({url}), 17:19 UTC)" in item
    n, url, when = _posted(K49, "rule_superseded")
    assert (n, when) == (29, "17:13") and f"([issue 29]({url}), 17:13 UTC) set Part A at three copies" in item
    assert "(`data/ibm_fez/k49-rule.md` and `k49-rule-v1-superseded.md`)" in item
    assert k["H48"] == "DISAGREE" and k["informative_chains"] == ["143", "144", "142", "124"]
    assert "The verdict: DISAGREE, with four informative chains." in item
    for j, nm in enumerate(("143", "142", "124", "144", "131")):
        p, pa = k["prediction"][nm], a["prediction"][nm]
        assert _bullet("-".join(map(str, p["chain"])), nm, p, pa, j == 0) in item, nm
    assert k["prediction"]["144"]["outside_margin"] and k["prediction"]["144"]["d_M_ci90"][0] > 0.15
    assert "d_M +0.182 (+0.163 to +0.201), entirely above +0.15." in item
    p131 = k["prediction"]["131"]
    assert not p131["informative"] and p131["d_M_ci90"][0] < 0.15 < p131["d_M_ci90"][1]
    assert "across the margin's edge, and not informative." in item
    # held on three, failed on one, the circuit doing better than predicted
    assert all(abs(k["prediction"][q]["d_M"]) < 0.02 for q in ("143", "142", "124"))
    assert "The rule held on 143, 142 and 124, each d_M within 0.02 of zero." in item
    assert k["prediction"]["144"]["d_M"] > 0 and "the failure was the circuit doing better than predicted" in item
    p48, p49 = k48["prediction"]["144"], k["prediction"]["144"]
    assert (_q(p48["dP_R_TM"], 3), _q(p49["dP_R_TM"], 3), _q(p48["F_no"], 3), _q(p49["F_no"], 3)) == (
        "0.074",
        "0.326",
        "0.790",
        "0.786",
    )
    assert (
        "rose from 0.074 to 0.326, while its wait test without refocusing stayed where it was, F 0.790 and then 0.786"
        in item
    )
    ram, pos = [], []
    for i, (lab, cts) in enumerate(zip(doc["labels"], doc["counts"]), 1):
        if lab["part"] == "B" and 144 in lab["qubits"] and lab["tau_dt"] == 2612 and lab["variant"] == "R":
            j = lab["qubits"].index(144)
            ram.append(sum(c for key, c in cts.items() if key.replace(" ", "")[::-1][j] == "1") / sum(cts.values()))
            pos.append(("B", i))
        if lab["part"] == "W" and lab["M"] == 144 and lab["variant"] == "no":
            pos.append(("W", i))
    assert [_q(x, 2) for x in ram] == ["0.34", "0.31"] and "read P(1) 0.34 and 0.31" in item
    per_copy = a["part_A"]["144"]["no"]["F_per_copy"]
    assert (len(per_copy), _q(min(per_copy), 3), _q(max(per_copy), 3)) == (4, "0.781", "0.789")
    assert "its four wait-test copies without refocusing read F 0.781 to 0.789" in item
    b_at = [i for kind, i in pos if kind == "B"]
    assert any(abs(i - j) == 1 for kind, i in pos if kind == "W" for j in b_at)
    assert "one of them run next to one of those Ramsey circuits" in item
    q48, q49 = k48["prediction"]["131"], k["prediction"]["131"]
    assert (_q(q48["dP_R_TM"], 3), _q(q49["dP_R_TM"], 3), _q(q48["F_no"], 2), _q(q49["F_no"], 2)) == (
        "0.059",
        "0.124",
        "0.86",
        "0.86",
    )
    assert "its Ramsey loss rising from 0.059 to 0.124 while its F held at 0.86" in item
    # beside the verdict
    q, q48b = k["part_B"]["143"], k48["part_B"]["143"]
    assert q["kind_of_loss"] == "REFOCUSABLE" and (_q(q["r"], 3), _q(q48b["r"], 3)) == ("0.234", "0.260")
    assert "REFOCUSABLE at 3.4 µs with a Ramsey loss of 0.234 (0.260 on 11 October)" in item
    f, f48 = q["ramsey_fit"], q48b["ramsey_fit"]
    assert (_q(1000 * f["f_MHz"], 1), _q(1000 * f["f_err"], 1)) == ("40.4", "3.2")
    assert (_q(1000 * f48["f_MHz"], 1), _q(1000 * f48["f_err"], 1)) == ("47.1", "1.8")
    assert "gives 40.4 ± 3.2 kHz, against finding 14's 47.1 ± 1.8 kHz." in item
    p1 = q["ramsey_P1"]
    assert not k["beside"]["oscillation_143_8_or_TM_to_16us"] and _q(p1["2000"] - p1["4000"], 3) == "0.056"
    assert "its Ramsey P(1) fell by 0.056 from 8 µs to 16 µs, short of 0.1." in item
    assert "Findings 16 to 18 take up the first." in item


def test_finding_16():
    """Kickoff 50, recomputed from the counts: what ran and when, the posted rule, the gap and Delta_active, and the
    state, readout, d1 and echo lines beside the verdict."""
    from _reproduce import K49, K50, k49_recomputed, k50_recomputed, reuse_doc

    item = _item(16)
    doc = reuse_doc(K50)
    m, a = doc["meta"], doc["archived"]["analysis"]
    k = k50_recomputed()
    assert (hhmm(doc["timestamps"]["running"]), hhmm(doc["timestamps"]["finished"])) == ("18:01", "18:02")
    assert "(Kickoff 50; ibm_fez, 13 October 2026, 18:01 to 18:02 UTC)" in item
    assert m["chains"] == {"144": [143, 144, 145], "143": [144, 143, 142]}
    assert "144 on 143-144-145, and 143 on 144-143-142 as the control." in item
    assert m["built_from"]["commit"].startswith("a55354d") and "built unedited at `a55354d`" in item
    assert {v["T_dt"] for v in m["T_M"]["per_chain"].values()} == {2611}
    assert r(2611 * m["T_M"]["dt_s"] * 1e6, 2) == 10.44 and "T_M = 2,611 dt (10.44 µs)" in item
    assert len(doc["counts"]) == 36 and m["shots_per_circuit"] == 5000 and m["copies"] == 2
    assert "Each circuit ran twice with 5,000 shots: 36 circuits in one job" in item
    assert m["calibration_last_update_utc"] == "2026-10-13T17:32:21Z"
    assert m["calibration_last_update_utc"] > reuse_doc(K49)["meta"]["calibration_last_update_utc"]
    # A23, 1d: the calibration history says what the stamp changed since finding 15's, the stamp just before it
    assert _history_after(reuse_doc(K49)["meta"]["calibration_last_update_utc"])["stamp_utc"] == "2026-10-13T17:32:21Z"
    assert not _history_changed("2026-10-13T17:32:21Z")
    assert (
        "under IBM's calibration stamp of 17:32:21 UTC, a new calibration stamp at which no published value changed "
        "(`ibm_fez/calibration-history-01.json`)." in item
    )
    n, url, when = _posted(K50)
    assert (n, when) == (
        31,
        "17:49",
    ) and f"([issue 31]({url}), 17:49 UTC; the file is `data/ibm_fez/k50-rule.md`)" in item
    fx = doc["fixed_before_the_data"]
    assert (fx["reproduced_floor"], fx["supported"], fx["not_supported_band"]) == (0.1, 0.1, 0.05)
    assert "entirely above +0.10" in item and "entirely below −0.10" in item and "entirely inside ±0.05" in item
    assert k["verdict"] == "NOT SUPPORTED (Kickoff 49's gap not present today)" and not k["reproduced"]
    assert "The verdict: NOT SUPPORTED (Kickoff 49's gap not present today)." in item
    p, pa = k["per_M"]["144"], a["per_M"]["144"]
    lo, hi = (_q(x, 3) for x in pa["loss_ci90"]["R0"])
    assert f"144's Ramsey loss over the wait (R0) was {_q(p['loss']['R0'], 3)} ({lo} to {hi})" in item
    assert _q(k49_recomputed()["prediction"]["144"]["dP_R_TM"], 3) == "0.326" and "against 0.326 in finding 15" in item
    assert f"F {_q(p['F_no'], 3)} without refocusing and {_q(p['F_ref'], 3)} with" in item
    lo, hi = (_q(x, 3, True) for x in pa["d0_ci90"])
    assert f"So d0 was {_q(p['d0'], 3, True)} ({lo} to {hi})." in item and pa["d0_ci90"][0] < 0.10
    gap = _utc(doc["timestamps"]["running"]) - _utc(reuse_doc(K49)["timestamps"]["running"])
    assert round(gap.total_seconds() / 60) == 33 and "This job began 33 minutes after finding 15's" in item
    k49 = reuse_doc(K49)
    assert k49["meta"]["T_M"]["used_dt"] == [2612] and 2612 - 2611 == 1
    assert [g for g in k49["meta"]["groups"] if 144 in g] == [[142, 144, 125]]
    assert "over a wait 1 dt shorter, where finding 15's Part B ran it beside 142 and 125" in item
    assert _history_publishes_no_frequency()
    assert (
        "The run cannot separate a change on the device in those 33 minutes from the circuits' other differences: at "
        "the new stamp no published value changed, and IBM does not publish ibm_fez's qubit frequencies." in item
    )
    lo, hi = (_q(x, 3, True) for x in pa["delta_active_ci90"])
    assert f"144 lost {_q(p['loss']['R1'], 3)}: Δ_active {_q(p['delta_active'], 3, True)} ({lo} to {hi})" in item
    c, ca = k["per_M"]["143"], a["per_M"]["143"]
    lo, hi = (_q(x, 3, True) for x in ca["delta_active_ci90"])
    d = _q(-c["delta_active"], 3)
    assert f"On 143 they raised the loss by {d} (Δ_active {_q(c['delta_active'], 3, True)}, from {lo} to {hi})." in item
    # beside the verdict: the neighbours' state, their readout, d1 and the echo
    assert (_q(-p["state_split_R0_minus_R2"], 2), _q(p["loss"]["R2"], 3)) == ("0.35", "0.394")
    assert (_q(-c["state_split_R0_minus_R2"], 2), _q(c["loss"]["R0"], 3), _q(c["loss"]["R2"], 3)) == (
        "0.25",
        "0.557",
        "0.809",
    )
    assert "the loss rose by 0.35 on 144, to 0.394, and by 0.25 on 143, from 0.557 to 0.809" in item
    assert pa["state_split_ci90"][1] < -0.3 and ca["state_split_ci90"][1] < -0.2
    rs = {q: [_q(x, 3, True) for x in a["per_M"][q]["readout_split_ci90"]] for q in ("144", "143")}
    assert all(lo_ < 0 < hi_ for lo_, hi_ in (a["per_M"][q]["readout_split_ci90"] for q in ("144", "143")))
    assert (
        f"90% intervals of {rs['144'][0]} to {rs['144'][1]} on 144 and {rs['143'][0]} to {rs['143'][1]} on 143" in item
    )
    assert all(m_["d1_vs_0p15"] == "inside" for m_ in k["per_M"].values())
    assert f"d1 {_q(p['d1'], 3, True)} on 144 and {_q(c['d1'], 3, True)} on 143" in item
    echo = [k["per_M"][q]["loss"][e] for q in ("144", "143") for e in ("E0", "E1")]
    assert (_q(min(echo), 3), _q(max(echo), 3)) == ("0.030", "0.044") and "(E0 and E1, 0.030 to 0.044)" in item
    assert "a static ZZ coupling was not tested as such" in item


def test_finding_17():
    """Kickoff 51, recomputed from the counts: the known phase, the posted rule, the swings, the design's blind spot on
    143 with its arithmetic, and the lines beside the verdict."""
    import math

    from _reproduce import K50, K51, k50_recomputed, k51_recomputed, reuse_doc

    item = _item(17)
    doc = reuse_doc(K51)
    m, a = doc["meta"], doc["archived"]["analysis"]
    k = k51_recomputed()
    assert (hhmm(doc["timestamps"]["running"]), hhmm(doc["timestamps"]["finished"])) == ("18:30", "18:32")
    assert "(Kickoff 51; ibm_fez, 13 October 2026, 18:30 to 18:32 UTC)" in item
    assert m["phis_deg"] == [-90, 0, 90] and "The run added φ of −90°, 0° and +90° on 144" in item
    assert len(doc["counts"]) == 56 and m["shots_per_circuit"] == 5000 and m["copies"] == 2
    assert "56 circuits, each twice with 5,000 shots" in item
    assert m["calibration_last_update_utc"] == reuse_doc(K50)["meta"]["calibration_last_update_utc"]
    assert "under the same calibration stamp as finding 16's." in item
    n, url, when = _posted(K51)
    assert (n, when) == (32, "18:24") and f"([issue 32]({url}), 18:24 UTC; `data/ibm_fez/k51-rule.md`)" in item
    fx = doc["fixed_before_the_data"]
    assert (fx["supported_outside"], fx["not_supported_inside"]) == (0.05, 0.03)
    assert k["verdict"] == "SUPPORTED" and "The verdict: SUPPORTED, on 144." in item
    p, pa = k["per_M"]["144"], a["per_M"]["144"]
    assert (_q(p["d0"]["-90"], 3, True), _q(p["d0"]["90"], 3, True)) == ("−0.121", "+0.198")
    lo, hi = (_q(x, 3, True) for x in pa["A_ci90"])
    assert f"d(φ) swung from −0.121 at −90° to +0.198 at +90°: A = {_q(p['A'], 3, True)} ({lo} to {hi})." in item
    assert pa["A_outside_0p05"]
    c, ca = k["per_M"]["143"], a["per_M"]["143"]
    lo, hi = (_q(x, 3, True) for x in ca["A_ci90"])
    assert f"**143:** A = {_q(c['A'], 3, True)} ({lo} to {hi}), inside ±0.03." in item and ca["A_inside_0p03"]
    # the blind spot: the swing's sensitivity goes as cos(theta), by the fits
    t144, t143 = p["fit_R0"]["theta_deg"], c["fit_R0"]["theta_deg"]
    assert round(t144) == 5 and round(t143, -1) == -100
    ratio = math.cos(math.radians(t144)) / abs(math.cos(math.radians(t143)))
    assert (
        round(ratio) == 6
        and "144's θ was near +5° and 143's near −100°, where the swing is about six times smaller" in item
    )
    assert "The design was nearly blind on 143, a flaw in it found after the data." in item
    assert "A ≈ −(F_ref / 2) cos θ × Δθ" in item
    # beside the verdict
    assert (_q(p["mean_abs_d1"], 3), _q(p["mean_abs_d0"], 3), _q(p["A1"], 3, True)) == ("0.042", "0.119", "+0.028")
    assert (
        "with a mean |d1| over the three phases of 0.042, against a mean |d0| of 0.119, and a swing A1 of +0.028"
        in item
    )
    assert (_q(c["mean_abs_d1"], 3), _q(c["mean_abs_d0"], 3)) == ("0.045", "0.027") and "(0.045 against 0.027)" in item
    fits = [_q(p["fit_R0"]["theta_deg"], 1, True), _q(p["fit_R2"]["theta_deg"], 1, True)]
    fits += [_q(c["fit_R0"]["theta_deg"], 1, True), _q(c["fit_R2"]["theta_deg"], 1, True)]
    assert fits == ["+5.2", "−70.8", "−99.5", "−137.1"]
    assert (
        "at +5.2° with idle neighbours and −70.8° with both neighbours in |1⟩, and 143's at −99.5° and −137.1°" in item
    )
    k50 = k50_recomputed()["per_M"]
    assert (_q(p["d0"]["0"], 3, True), _q(k50["144"]["d0"], 3, True)) == ("+0.039", "+0.044")
    assert (_q(c["d0"]["0"], 3, True), _q(k50["143"]["d0"], 3, True)) == ("−0.015", "−0.014")
    assert "+0.039 on 144 (+0.044 there) and −0.015 on 143 (−0.014 there)" in item


def test_finding_18():
    """Kickoff 52, recomputed from the counts: the sweep, the posted rule with its fit, the fitted offsets and the
    verdicts, the leftover part, the fits' quality and the residuals, the job's length and stamps, and the agreement
    with Kickoff 51's three-point fits."""
    from _reproduce import K48, K49, K50, K51, K52, k52_recomputed, reuse_doc

    item = _item(18)
    doc = reuse_doc(K52)
    m, a = doc["meta"], doc["archived"]["analysis"]
    k = k52_recomputed()
    assert (hhmm(doc["timestamps"]["running"]), hhmm(doc["timestamps"]["finished"])) == ("18:59", "20:00")
    assert "(Kickoff 52; ibm_fez, 13 October 2026, 18:59 to 20:00 UTC)" in item
    assert m["phis_deg"] == [0, 60, 120, 180, 240, 300]
    assert "φ of 0°, 60°, 120°, 180°, 240° and 300° on 143 (chain 144-143-142) and 144 (143-144-145)" in item
    assert (
        len(doc["counts"]) == 80
        and m["shots_per_circuit"] == 4000
        and "40 circuits, each twice with 4,000 shots" in item
    )
    n, url, when = _posted(K52)
    assert (n, when) == (
        33,
        "18:52",
    ) and f"([issue 33]({url}), 18:52 UTC; `data/ibm_fez/k52-rule.md`), with the fit in it" in item
    assert doc["fixed_before_the_data"]["margin_deg"] == 5.0 and "entirely outside ±5°" in item
    assert (k["H52a"], k["H52b"]) == ("DIFFERENT", "DIFFERENT")
    assert "The verdicts: DIFFERENT on 143 and DIFFERENT on 144." in item
    for q in ("143", "144"):
        p, pa = k["per_M"][q], a["per_M"][q]
        th = {c: _q(p["fits"][c]["theta_deg"], 1, True) for c in ("W", "R0", "R1")}
        lo, hi = (_q(x, 1, True) for x in pa["Delta_W_minus_R0"]["ci90"])
        d = _q(p["Delta_W_minus_R0"]["deg"], 1, True)
        want = f"**{q}:** θ_W {th['W']}°, θ_R0 {th['R0']}°, θ_R1 {th['R1']}°; Δ = {d}° ({lo}° to {hi}°)."
        assert want in item, want
    p3, p4 = k["per_M"]["143"], k["per_M"]["144"]
    assert _q(p4["fits"]["W"]["theta_deg"], 1, True) == "−16.1"  # the report rounded −16.148 to −16.2
    w1 = {q: k["per_M"][q]["W_minus_R1"]["deg"] for q in ("143", "144")}
    d0 = {q: k["per_M"][q]["Delta_W_minus_R0"]["deg"] for q in ("143", "144")}
    assert all(abs(w1[q]) < abs(d0[q]) for q in w1) and all(k["per_M"][q]["R1_closer_than_R0"] for q in w1)
    assert "4.8° away against 7.2° on 143 and 3.5° against 21.6° on 144" in item
    assert (_q(abs(w1["143"]), 1), _q(abs(d0["143"]), 1), _q(abs(w1["144"]), 1), _q(abs(d0["144"]), 1)) == (
        "4.8",
        "7.2",
        "3.5",
        "21.6",
    )
    lo3, hi3 = (_q(x, 1, True) for x in a["per_M"]["143"]["W_minus_R1"]["ci90"])
    lo4, hi4 = (_q(x, 1, True) for x in a["per_M"]["144"]["W_minus_R1"]["ci90"])
    assert w1["143"] > 0 > w1["144"]
    assert (
        f"θ_W − θ_R1 = {_q(w1['143'], 1, True)}° ({lo3}° to {hi3}°) on 143 and {_q(w1['144'], 1, True)}° "
        f"({lo4}° to {hi4}°) on 144, opposite in sign on the two qubits" in item
    )
    s3, s4 = p3["R1_minus_R0"]["deg"], p4["R1_minus_R0"]["deg"]
    assert (_q(s4, 1, True), _q(d0["144"], 1, True), _q(s3, 1, True), _q(d0["143"], 1, True)) == (
        "−18.1",
        "−21.6",
        "−12.0",
        "−7.2",
    )
    assert (
        "On 144 the neighbours' activity accounts for −18.1° of the −21.6°; on 143 it moves the Ramsey by "
        "−12.0°, past the wait test's −7.2°." in item
    )
    amps = [k["per_M"][q]["fits"][c]["amplitude"] for q in ("143", "144") for c in ("W", "R0", "R1")]
    res = [abs(x) for q in ("143", "144") for c in ("W", "R0", "R1") for x in k["per_M"][q]["fits"][c]["residuals"]]
    assert (_q(min(amps), 2), _q(max(amps), 2), _q(max(res), 3)) == ("0.41", "0.45", "0.007")
    assert "The fits' amplitudes were 0.41 to 0.45, and no residual at any phase exceeded 0.007." in item
    assert max(res) <= 0.007
    d0_144, d1_144 = p4["d0"].values(), p4["d1"].values()
    assert (_q(min(d0_144), 3, True), _q(max(d0_144), 3, True), _q(min(d1_144), 3, True), _q(max(d1_144), 3, True)) == (
        "−0.085",
        "+0.182",
        "+0.021",
        "+0.086",
    )
    assert (
        "the idle-neighbour residual d0 ranged from −0.085 to +0.182 on 144, and the active-neighbour d1 from "
        "+0.021 to +0.086" in item
    )
    # the job's length and the stamps
    ts = doc["timestamps"]
    assert round((_utc(ts["finished"]) - _utc(ts["running"])).total_seconds() / 60) == 61
    earlier = [reuse_doc(f)["timestamps"] for f in (K48, K49, K50, K51)]
    assert max((_utc(t["finished"]) - _utc(t["running"])).total_seconds() for t in earlier) / 60 < 2.05
    assert (
        "The job took about 61 minutes in IBM's record, against at most about 2 minutes for the jobs of "
        "findings 14 to 17." in item
    )
    run = doc["run"]
    assert (run["calibration_at_build_utc"], run["calibration_at_submission_utc"]) == ("2026-10-13T17:32:21Z",) * 2
    assert run["calibration_after_fetch_utc"] == "2026-10-13T18:56:54Z"
    before = (_utc(ts["running"]) - _utc(run["calibration_after_fetch_utc"])).total_seconds() / 60
    assert 1.5 < before < 2.5 and _utc(run["calibration_after_fetch_utc"]) < _utc(m["submitted_utc"])
    assert (
        "IBM's calibration stamp read 17:32:21 UTC at build and at submission, and 18:56:54 UTC after the fetch" in item
    )
    # A23, 1d: at the new stamp, the one after 17:32:21, only the layer-fidelity entries changed
    row = _history_after("2026-10-13T17:32:21Z")
    assert row["stamp_utc"] == run["calibration_after_fetch_utc"] and _history_changed(row["stamp_utc"]) == {
        "general.lf 97",
        "general_qlists.lf_chain 97",
    }
    assert (
        "a new calibration stamp, dated about two minutes before the job began, was published after it was submitted, "
        "and at it no published value changed but the layer-fidelity entries (`ibm_fez/calibration-history-01.json`)."
        in item
    )
    # Kickoff 51's three-point fits, made after the data, against the sweep
    k51 = reuse_doc(K51)["after_data_fits"]["fits"]
    gaps = [
        abs(k["per_M"][q]["fits"][c]["theta_deg"] - k51[q][f])
        for q in ("143", "144")
        for c, f in (("W", "wait_test_theta_deg"), ("R0", "R0_theta_deg"), ("R1", "R1_theta_deg"))
    ]
    assert max(gaps) < 1.3 and r(max(gaps), 1) == 1.3
    assert "agree with the three-point fits made after the data in finding 17 within 1.3° on every instrument" in item


def test_finding_19():
    """Kickoff 53, recomputed from the counts: the chains as drawn, the posted rule, the five informative cells and the
    verdict, the original rule beside it, the lean, the job's length and stamps, and the scope sentence."""
    from _reproduce import K50, K51, K52, K53, k50_recomputed, k51_recomputed, k52_recomputed, k53_recomputed, reuse_doc

    item = _item(19)
    doc = reuse_doc(K53)
    m, a = doc["meta"], doc["archived"]["analysis"]
    k = k53_recomputed()
    assert (hhmm(doc["timestamps"]["running"]), hhmm(doc["timestamps"]["finished"])) == ("20:19", "21:12")
    assert "(Kickoff 53; ibm_fez, 13 October 2026, 20:19 to 21:12 UTC)" in item
    draw = doc["chain_draw"]
    ex = draw["n_excluded"]
    assert (draw["n_candidates"], ex["uses a qubit of Kickoffs 48 to 52"], ex["a readout error above 3%"]) == (
        488,
        58,
        204,
    )
    assert (ex["a CZ error above 1%"], draw["n_survivors"]) == (38, 188)
    assert draw["n_candidates"] - sum(ex.values()) == draw["n_survivors"]
    assert (
        "was a candidate (488)" in item
        and "(58), then any with a readout error above 3% (204) or a CZ error above 1% (38), leaving 188" in item
    )
    assert "default_rng(5353)" in draw["procedure"] and "NumPy's `default_rng(5353)`" in item
    chains = ["-".join(map(str, c["chain"])) for c in draw["drawn"]]
    assert chains == ["31-30-29", "75-74-73", "120-121-116", "96-103-104"] and m["chains"] == [
        c["chain"] for c in draw["drawn"]
    ]
    assert "until four were taken: 31-30-29, 75-74-73, 120-121-116 and 96-103-104" in item
    used = {q for f in (K50, K51, K52) for ch in reuse_doc(f)["meta"]["chains"].values() for q in ch}
    used |= {123, 124, 125, 131, 132, 138, 141, 142, 143, 144, 145}
    assert not {q for c in draw["drawn"] for q in c["chain"]} & used
    assert m["phis_deg"] == [0, 90] and len(doc["counts"]) == 64 and m["shots_per_circuit"] == 3500
    assert "32 circuits, each twice with 3,500 shots." in item
    n, url, when = _posted(K53)
    assert (n, when) == (33, "18:52") and _utc(m["rule"]["posted"]["created_utc"]) < _utc(
        reuse_doc(K52)["meta"]["submitted_utc"]
    )
    assert f"([issue 33]({url}), 18:52 UTC, before Kickoff 52 ran; `data/ibm_fez/k53-rule.md`)" in item
    fx = doc["fixed_before_the_data"]
    assert (fx["margin"], fx["informative_floor"]) == (0.15, 0.2)
    assert k["H53"] == "AGREE" and k["informative_cells"] == ["30|+0", "30|+90", "74|+0", "121|+90", "103|+90"]
    assert "The verdict: AGREE, on all five informative cells." in item
    cells = {c["cell"]: c for c in k["cells"]}
    arch = {c["cell"]: c for c in a["cells"]}

    def d1(cell):
        lo, hi = (_q(x, 3, True) for x in arch[cell]["d1_ci90"])
        return _q(cells[cell]["d1"], 3, True), lo, hi

    v, lo, hi = d1("30|+0")
    v2, lo2, hi2 = d1("30|+90")
    assert f"**31-30-29**, with 30 waiting: d1 {v} at 0° ({lo} to {hi}) and {v2} at +90° ({lo2} to {hi2})." in item
    for chain, M, cell, ang in (
        ("75-74-73", 74, "74|+0", "0°"),
        ("120-121-116", 121, "121|+90", "+90°"),
        ("96-103-104", 103, "103|+90", "+90°"),
    ):
        v, lo, hi = d1(cell)
        assert f"**{chain}**, with {M} waiting: d1 {v} at {ang} ({lo} to {hi})." in item, cell
    assert max(arch[c]["d1_ci90"][1] for c in k["informative_cells"]) < 0.15
    # the original rule, beside
    assert k["beside"]["original_rule_verdict"] == "DISAGREE"
    out = [c for c in k["beside"]["original_rule_informative_cells"] if arch[c]["d0_ci90"][0] > 0.15]
    assert out == ["74|+90", "121|+90", "103|+90"] and len(k["beside"]["original_rule_informative_cells"]) == 5
    parts = []
    for c in out:
        lo, hi = (_q(x, 3, True) for x in arch[c]["d0_ci90"])
        parts.append(f"{c.split('|')[0]} at {_q(cells[c]['d0'], 3, True)} ({lo} to {hi})")
    assert f"{parts[0]}, {parts[1]} and {parts[2]}." in item
    zero = [cells[f"{M}|+0"] for M in ("30", "74", "121", "103")]
    assert (_q(min(c["d0"] for c in zero), 3, True), _q(max(c["d0"] for c in zero), 3, True)) == ("+0.012", "+0.078")
    assert "Without the added phase, the original check's residuals ran from +0.012 to +0.078" in item
    inf0 = [c for c in zero if c["informative_R0"]]
    assert (
        [c["cell"] for c in inf0] == ["30|+0"]
        and -0.15 < arch["30|+0"]["d0_ci90"][0]
        and arch["30|+0"]["d0_ci90"][1] < 0.15
    )
    assert sum(abs(c["d0"]) < abs(c["d1"]) for c in zero) == 3
    assert (
        "its one informative cell there sat inside the margin, and it was the closer of the two on three of the "
        "four chains" in item
    )
    b = k["beside"]
    assert abs(b["mean_abs_d1_informative"] - b["mean_abs_d0_informative"]) < 0.003
    assert (_q(b["mean_abs_d1_informative"], 3), _q(b["mean_abs_d0_informative"], 3)) == ("0.087", "0.084")
    assert "within 0.003 of each other: 0.087 for the revised one and 0.084 for the original" in item
    # the lean
    all_d1 = [c["d1"] for c in k["cells"]]
    assert min(all_d1) > 0 and (_q(min(all_d1), 3, True), _q(max(all_d1), 3, True)) == ("+0.046", "+0.114")
    assert (
        0.7 < max(all_d1) / 0.15 < 0.8
        and "Every d1 was positive, from +0.046 to +0.114, a lean that reached about three quarters of the margin"
        in item
    )
    before = [k50_recomputed()["per_M"][q]["d1"] for q in ("144", "143")]
    before += [v for q in ("144", "143") for v in k51_recomputed()["per_M"][q]["d1"].values()]
    before += [v for q in ("143", "144") for v in k52_recomputed()["per_M"][q]["d1"].values()]
    assert len(before) == 20 and (_q(min(before), 3, True), _q(max(before), 3, True)) == ("−0.002", "+0.086")
    assert "in findings 16 to 18 it ran from −0.002 to +0.086 on 143 and 144" in item
    # the job's length and the stamps
    ts, run = doc["timestamps"], doc["run"]
    assert round((_utc(ts["finished"]) - _utc(ts["running"])).total_seconds() / 60) == 53
    assert "The job took about 53 minutes in IBM's record, like finding 18's." in item
    assert run["calibration_at_build_utc"] == run["calibration_at_submission_utc"] == "2026-10-13T19:57:03Z"
    assert draw["calibration_stamp"] == run["calibration_at_build"]
    after = _utc(run["calibration_after_fetch_utc"])
    assert run["calibration_after_fetch_utc"] == "2026-10-13T20:41:52Z" and _utc(ts["running"]) < after < _utc(
        ts["finished"]
    )
    assert (
        "IBM's calibration stamp read 19:57:03 UTC at the draw, the build and the submission, and 20:41:52 UTC "
        "after the fetch, a new calibration stamp at which no published value changed." in item
    )
    # A23, 1d: between the two, one stamp the run's reads did not see, with new readout errors dated 19:11 UTC
    mid = _history_after("2026-10-13T19:57:03Z")
    assert mid["stamp_utc"] == "2026-10-13T20:29:58Z" and _utc(ts["running"]) < _utc(mid["stamp_utc"]) < after
    assert mid["q_readout_error"] == "154" and mid["readout_error_dates_latest_utc"][11:16] == "19:11"
    assert mid["stamp_utc"] not in {run[k] for k in run if k.endswith("_utc")}
    assert _history_after(mid["stamp_utc"])["stamp_utc"] == run["calibration_after_fetch_utc"]
    assert not _history_changed(run["calibration_after_fetch_utc"])
    assert (
        "Between the two, at 20:29:58 UTC, while the job was running, a stamp that the run's own reads did not see "
        "published new readout errors on 154 qubits, dated 19:11 UTC (`ibm_fez/calibration-history-01.json`); which "
        "readout values the job ran under is not known." in item
    )
    # the scope
    assert len({143, 144} | {c["chain"][1] for c in draw["drawn"]}) == 6
    assert "The active-neighbour check now rests on six waiting qubits on one processor" in item
    # A23, ruling R1, Q6: the second day followed
    assert (
        "It is the instrument that held in the cases tested; a second day on this code followed (finding 21)." in item
    )
    assert "Manacitra does not rank machines." in item


def test_findings_15_to_19_beside_the_findings():
    """Amendment A22: the README's rows, count, limit line and one sentence on the check's default; the kickoffs rows;
    the method's subsection and the reproduce page's pointers; and the four new bullets of what has not been shown,
    with the one edited bullet."""
    from _reproduce import K50, K51, K52, K53, k50_recomputed, k51_recomputed, k52_recomputed, k53_recomputed, reuse_doc

    readme = " ".join((ROOT / "README.md").read_text().split())
    # A23 changed the count, the limit line and two bullets of what has not been shown: see
    # test_the_findings_dates and test_findings_20_and_21_beside_the_findings
    assert (
        "now runs that Ramsey with the qubit's neighbours active, as they are in the circuit, by default; the "
        'idle-neighbour Ramsey, the 0.5.0 behaviour, remains with `neighbours="idle"`.' in readme
    )
    for f in (K50, K51, K52, K53):
        assert reuse_doc(f)["meta"]["utc"].startswith("2026-10-13")
    kick = (ROOT / "docs" / "kickoffs.md").read_text()
    for n in range(49, 54):
        assert f"| {n}, 13 October 2026 |" in kick and f"`ibm_fez/k{n}-rule.md`" in kick
    method = " ".join((ROOT / "docs" / "method.md").read_text().split())
    assert "### The Ramsey over the circuit's wait" in (ROOT / "docs" / "method.md").read_text()
    st = [-k50_recomputed()["per_M"][q]["state_split_R0_minus_R2"] for q in ("144", "143")]
    assert (_q(min(st), 2), _q(max(st), 2)) == ("0.25", "0.35")
    assert "Held in |1⟩ during the wait, they changed the waiting qubit's loss by 0.25 to 0.35" in method
    deltas = [k52_recomputed()["per_M"][q]["Delta_W_minus_R0"]["deg"] for q in ("143", "144")]
    assert [round(abs(x)) for x in deltas] == [7, 22] and "by about 7° and 22° on two qubits" in method
    assert (
        k53_recomputed()["H53"] == "AGREE"
        and "held within ±0.15, where the one with idle neighbours would have failed" in method
    )
    assert (  # A23, ruling R1, Q6
        "It is the instrument that held in the cases tested, on six waiting qubits of one processor (through finding "
        "19; findings 20 and 21 below)." in method
    )
    assert 'pass `neighbours="idle"`' in method
    page = " ".join((ROOT / "docs" / "reproduce.md").read_text().split())
    for n in range(15, 20):
        assert f"[Finding {n}](findings.md#finding-{n})" in page
    assert page.count("at `a55354d`") == 5 and "built by this code at `a55354d` (v0.5.0)" in page
    # what has not been shown
    flat = " ".join((ROOT / "docs" / "findings.md").read_text().split())
    assert (
        "- **Whether choosing qubits by the Ramsey loss at the circuit's wait, or the active-neighbour check, gives "
        "better placements for reuse circuits than other methods.**" in flat
    )
    assert (
        "- **It has not been tested as a chooser.** Neither check has been shown to choose better placements." in flat
    )
    assert "- **The mechanism of the neighbour shift is not established.** A static ZZ coupling is consistent" in flat
    banned = "veri" + "fied"  # A22, 4: the word waits for the release kickoff, after a second day
    assert banned not in flat.split("## What it has not shown", 1)[0].split('<a id="finding-15">', 1)[1]
    # the long documentation's row for the five runs
    index = " ".join((ROOT / "docs" / "index.md").read_text().split())
    k49 = __import__("_reproduce").k49_recomputed()
    d144 = _q(k49["prediction"]["144"]["d_M"], 3, True)
    a144 = _q(k51_recomputed()["per_M"]["144"]["A"], 3, True)
    deg = [_q(k52_recomputed()["per_M"][q]["Delta_W_minus_R0"]["deg"], 1, True) for q in ("143", "144")]
    assert (d144, a144, deg) == ("+0.182", "+0.159", ["−7.2", "−21.6"])
    assert (
        f"the wait test on a second day, DISAGREE ({d144} on 144); the neighbour test, NOT SUPPORTED (Kickoff 49's gap "
        f"not present today); the known offset, SUPPORTED (A {a144} on 144); the phase sweep, DIFFERENT on both "
        f"({deg[0]}° and {deg[1]}°); the revised check, AGREE, and the original DISAGREE on the same cells" in index
    )


def test_finding_15_in_the_persistence_bullet():
    """A22, ruling R1, Q3: the bullet on how long 143's offset persists says, as a lived fact, that finding 15 saw it
    again on 13 October 2026, REFOCUSABLE at 3.4 µs, about 2.6 days after finding 14's calibration stamp."""
    from _reproduce import K48, K49, k49_recomputed, reuse_doc

    stamps = [reuse_doc(f)["meta"]["calibration_last_update_utc"] for f in (K48, K49)]
    assert stamps == ["2026-10-11T01:35:00Z", "2026-10-13T16:08:33Z"]
    days = (_utc(stamps[1]) - _utc(stamps[0])).total_seconds() / 86400
    assert r(days, 1) == 2.6 and reuse_doc(K49)["meta"]["utc"].startswith("2026-10-13")
    assert k49_recomputed()["part_B"]["143"]["kind_of_loss"] == "REFOCUSABLE"
    flat = " ".join((ROOT / "docs" / "findings.md").read_text().split())
    bullet = flat.split("- **How long the offset persists.**", 1)[1].split(" - **", 1)[0]
    assert (
        "Finding 15 saw it again on 13 October 2026, REFOCUSABLE at 3.4 µs, about 2.6 days after finding 14's "
        "calibration stamp." in bullet
    )


def test_the_readme_for_a_first_reader():
    """Ruling R4, items 2, 3 and 7, from a first reader's notes: the README says whom Manacitra is for and how it and
    Sandhi relate, in the author's confirmed wording, with its factual clauses checked against the records (each newer
    test's rule posted before its run or read but test 8's; Sandhi's digests posted before the runs they predict); a
    glossary, "Words used here", whose every entry is taken from the page it links to; a reading order; and every page
    in docs/ opens with what it holds and whom it is for. The README's and docs/index.md's statements of what the tests
    check cover the numbers the runs measured, which the timings are not."""
    import glob
    import json

    readme = (ROOT / "README.md").read_text()
    flat = " ".join(readme.split())
    contents = readme.split("**Contents:** ", 1)[1].split("\n", 1)[0]
    assert contents.startswith("[Who it is for](#who-it-is-for) · [Latest finding]")
    assert contents.index("[Words used here](#words-used-here)") < contents.index("[Findings](#findings)")
    order = [
        readme.index(h)
        for h in (
            "**Contents:**",
            "\n## Who it is for\n",
            "\n## Latest finding",
            "\n## What it does",
            "\n## Words used here\n",
            "\n## Findings\n",
        )
    ]
    assert order == sorted(order)
    who = " ".join(readme.split("\n## Who it is for\n", 1)[1].split("\n## ", 1)[0].split())
    for s in (
        "The rule for each newer test is hashed and posted in a public issue before its run or read, all but test 8's, "
        "which was posted after its run;",
        "every number the runs measured, as this README and the findings give it, is checked by a test against the "
        "published files;",
        "Sandhi is a desk model kept in [`data/desk/sandhi/`](data/desk/sandhi/README.md), outside the package: since "
        "version 4, a two-state model fitted on the desk to Manacitra's records and nothing else, with no hardware.",
        "after the run, a scorer hashed with the predictions compares them with Manacitra's read of that run.",
        "a version that does not describe the record is set down in the open, as version 3 was. Neither names a cause.",
    ):
        assert s in who, s[:50]
    # the clause on the rules, against every record whose rule is posted in a public issue
    late = []
    for f in sorted(glob.glob(str(archive.data_dir() / "ibm_*" / "*.json"))):
        m = json.loads(Path(f).read_text()).get("meta", {})
        r_ = m.get("rule")
        if isinstance(r_, dict) and isinstance(r_.get("posted"), dict) and m.get("utc"):
            if _utc(r_["posted"]["created_utc"]) > _utc(m["utc"]):
                late.append(r_["file"])
    assert late == ["t8-rule.md"]
    assert "The rule's hash was posted after the run" in (ROOT / "docs" / "kickoffs.md").read_text()
    sandhi = " ".join((archive.data_dir() / "desk" / "sandhi" / "README.md").read_text().split())
    assert (
        "the model is set down at version 3" in sandhi and "`hmm_core.c`, listed in its `FORECAST-SHA256SUMS`" in sandhi
    )
    # the glossary: each entry and the line it is taken from on the page it links to
    words = " ".join(readme.split("\n## Words used here\n", 1)[1].split("\n## ", 1)[0].split())
    method = " ".join((ROOT / "docs" / "method.md").read_text().split())
    index = " ".join((ROOT / "docs" / "index.md").read_text().split())
    sources = {
        "**P(11)**": (index, "Read P(11), the share of shots that read 11."),
        "**Kept share** (k)": (
            method,
            "pair [106, 107] moved by 0.040, slightly more than the model's 0.038 (k = 1.06)",
        ),
        "**Map**": (method, "each coloured by its kept share"),
        "**The map rule's verdicts**": (index, "| NOISE | r_split < 0.3 |"),
        "**Ramsey fringe**": (
            method,
            "A Ramsey fringe read at a few waits on one quadrature can be fitted as one line",
        ),
        "**Quadrature**": (
            method,
            "the same with an S† before the final H, which advances the fringe by a quarter turn",
        ),
        "**Monitor**": (
            method,
            "The monitor reads it at one wait, in a fixed order of repeats, as often as the job allows",
        ),
        "**Antiphase**": (method, "At the wait 1/(4δ) two fixed lines point in opposite directions"),
        "**Execution span**": (method, "A provider may execute one job as several spans, each a run of the submitted"),
        "**Boundary**": (method, "a repeat whose circuits ran in different spans straddles"),
        "**Shot index**": (method, "one row per repeat and one column per shot index as returned"),
        "**Sweep**": (
            method,
            "The times are on the sweep clock, the returned order, and in seconds only if that order",
        ),
        "**Per-shot read**": (method, "A provider returns, for a completed job, each position's shots one by one."),
        "**Duty**": (method, "the duty b, the fraction of the series above it, never folded"),
        "**Weight**": (method, "with a free weight b on the upper line"),
        "**Correlation time** (τ_c)": (method, "the correlation time τ_c, that lag times the caller's sweep time"),
        "**Desk model** (Sandhi)": (sandhi, "a kinetic description of the records, fitted on the desk from bundles of"),
    }
    items = words.split(" - **")[1:]
    entries = ["**" + e.split(":", 1)[0] for e in items]
    fresh = {"**Shot**", "**P(1)**", "**H**"}  # ruling R5, item 4: no page defines them; given plainly, without a link
    assert entries[:4] == ["**Shot**", "**P(1)**", "**P(11)**", "**H**"]
    assert [e for e in entries if e not in fresh] == list(sources)
    for term, (page, line) in sources.items():
        assert line in page, term
    assert all("](" not in e for e, name in zip(items, entries) if name in fresh)
    assert "a shot, P(1) and H, which no page defines, are given plainly, without a link." in words
    assert "reading it as time assumes it is chronological and evenly spaced" in words
    assert "**MAP PRESENT** if r_split ≥ 0.5 and r_AB ≥ 0.4 with p < 0.05" in index
    # the reading order and the page headers
    assert (
        "**Reading order:** this README, then [`docs/method.md`](docs/method.md), then [`docs/findings.md`]"
        "(docs/findings.md); [`docs/index.md`](docs/index.md) for the long version; the rest as needed." in flat
    )
    for name in ("findings", "index", "install", "kickoffs", "method", "reproduce"):
        text = (ROOT / "docs" / f"{name}.md").read_text()
        header = text.split("\n\n", 2)[1]
        assert text.startswith("# ") and "for readers" in header and len(header.split(". ")) <= 3, name
    # what the tests check: the numbers the runs measured
    assert "every number the runs measured, as the README and the findings give it, is checked by a test." in flat
    assert "every measured number" not in flat
    assert "Every statistic the runs measured, in the README and the pages it links to" in index
    # ruling R5, item 2: the two headers, and the line under section 3, each word defined in the rule file named
    assert (
        "for readers who want the circuits, the three map rules with their thresholds, the backends and the guards in "
        "one place; the later tests' rules are fixed in their rule files and stated in the findings." in index
    )
    assert (
        "the three map rules and their thresholds are in [the long version](index.md); each later test's rule is in "
        "its rule file, named in its row of [the kickoffs](kickoffs.md)." in method
    )
    kick = (ROOT / "docs" / "kickoffs.md").read_text()
    assert all(f"t{n}-rule.md" in kick for n in range(7, 18))
    assert (
        "The later per-shot words (SHARED, NO CHANGE, BETWEEN, CHANGE, MIDDLE HIGH, NOT SEEN) are defined in "
        "`data/ibm_fez/t15-rule.md` and `data/ibm_fez/t17-rule.md`, and stated in findings 29 and 30." in index
    )
    r15 = (archive.data_dir() / "ibm_fez" / "t15-rule.md").read_text()
    r17 = (archive.data_dir() / "ibm_fez" / "t17-rule.md").read_text()
    assert "SHARED above 3, INDEPENDENT below 1.5" in r15
    assert "**NO CHANGE** at or under 2, **BETWEEN** over 2 to 3, **CHANGE**" in r15
    assert "**MIDDLE HIGH** if Z ≥ 2.0; **NOT SEEN** if Z < 1.0" in r17
    assert "every rule and threshold" not in index + method
    assert "—" not in who + words and "–" not in who + words


def test_how_long_the_tests_take():
    """Ruling R4, item 5: the README's install section and docs/install.md say how long the reproduction subset and
    the full suite take, the fast command first, each timed once in a clean clone on one laptop (build report section
    49, ruling R4), with the first reader's figure beside them; and the changelog's 0.10.0 entry names the change."""
    line = (
        "the reproduction subset, `pytest tests/test_reproduction.py tests/test_field_inventory.py`, about 6 "
        "minutes on one laptop with 10 cores, and the full suite, `pytest`, about 14 minutes on the same; a first "
        "reader reported about 10 minutes for the tests on theirs."
    )
    readme = " ".join((ROOT / "README.md").read_text().split())
    install = " ".join((ROOT / "docs" / "install.md").read_text().split())
    assert "How long the tests take: " + line in readme
    assert "## How long the tests take The " + line.removeprefix("the ") in install
    assert readme.index("How long the tests take") < readme.index("## Reproducing the numbers")
    report = " ".join((ROOT / "build-report.md").read_text().split())
    assert "The reproduction subset took about 6 minutes and the full suite about 14 minutes" in report
    log = " ".join((ROOT / "CHANGELOG.md").read_text().split("## 0.9.0", 1)[0].split())
    assert (
        "- Documentation: a glossary, page headers, a reading order, timings, and the quick start's pick matched to "
        "`manacitra pick`'s default, from a first reader's notes." in log
    )


def test_the_quick_start_prints_what_the_readme_shows():
    """Ruling R4, items 1 and 4: the README's quick start picks with `pick_by_kept_share`, `manacitra pick`'s default
    since Amendment A15, and prints the numbers its verdict rests on, each with the map rule's threshold (docs/index.md,
    section 3), and the simulator's planted over-rotation beside the measured kept share. Its code block, run here as
    the README gives it, prints the README's text block exactly; the statistics are the ones the map rule tests, each
    past its threshold, and the correlation the prose quotes is the one printed."""
    import contextlib
    import io
    import re

    pytest.importorskip("qiskit_aer")
    readme = (ROOT / "README.md").read_text()
    quick = readme.split("Then, on the simulator, with no account (paste this into a Python session):", 1)[1]
    code = quick.split("```python\n", 1)[1].split("\n```", 1)[0]
    shown = quick.split("```text\n", 1)[1].split("\n```", 1)[0]
    assert 'pick_by_kept_share(result["kA"], 8)' in code and "pick_pairs" not in code
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        exec(compile(code, "README quick start", "exec"), {"__name__": "__readme__"})
    assert buf.getvalue().rstrip("\n") == shown
    lines = shown.splitlines()
    assert lines[0].startswith("DIAGNOSTIC [") and len(lines) == 1 + 4 + 1 + 9 + 1
    stats = {
        m.group(1): float(m.group(2)) for m in re.finditer(r"^(r_split|r_AB|r_AB\.x|r_Ax)\s+(-?[0-9.]+)", shown, re.M)
    }
    assert stats["r_split"] >= 0.5 and stats["r_AB"] >= 0.4 and stats["r_AB.x"] >= 0.3 and abs(stats["r_Ax"]) < 0.5
    index = " ".join((ROOT / "docs" / "index.md").read_text().split())
    assert "| DIAGNOSTIC | r_split ≥ 0.5, r_AB ≥ 0.4 with p < 0.05, r_AB·x ≥ 0.3, and \\|r_Ax\\| < 0.5 |" in index
    r = lines[-1].rsplit("r = ", 1)[1]
    flat = " ".join(quick.split("## ", 1)[0].split())
    assert r == "-0.89" and "a measured map that tracks the planted one (r = −0.89)" in flat
    assert (
        "It prints `DIAGNOSTIC` and the eight pairs whose kept share is closest to the ideal of 1, the rule `manacitra "
        "pick` uses by default. `pick_pairs(k, n)` ranks highest first, the rule Kickoff 33 ran; `pick_by_kept_share` "
        "is the default since Amendment A15." in flat
    )
    assert "kept the most" not in flat


def test_the_readme_opens_with_the_latest_findings():
    """A28 (A27's section, replaced): a short section at the top of the README, after the opening description and
    before what it does, the findings table and installation, says that two runs on 143 on 19 October were read per
    shot under rules hashed before them, that every boundary of one job's six spans read NO CHANGE, which does not show
    the duties equal (ruling R3, item 2, in place of "the duty held"), the monitor means of three runs (with no
    clause on the switching time, by the author's ruling R1, Q1: the per-span
    correlation times of 17 and 19 October overlap), that the pattern noticed in the published weights was not seen
    on new data, and the desk model's record, in at most five sentences, each claim checked here against the
    records. It carries none of the words the kickoff keeps out, and ends "Released as 0.10.0 on 20 October 2026.",
    as the release pull request dated it."""
    import re

    import _reuse_runs as rr

    front = (ROOT / "README.md").read_text()
    head = "\n## Latest finding: the duty across spans, jobs and days\n"
    assert head in front
    before, rest = front.split(head, 1)
    section = rest.split("\n## ", 1)[0]
    assert "**Manacitra makes a map of a quantum processor's qubit pairs" in before
    assert not any(h in before for h in ("\n## What it does", "\n## Findings", "\n## Install and try it"))
    assert "[Latest finding](#latest-finding-the-duty-across-spans-jobs-and-days)" in before
    flat = " ".join(section.split())
    assert len(re.findall(r"[.!?](?:\s|$)", flat + " ")) <= 5
    d2, d3, t16, t17 = _t30_records()
    for rec in (d3, t16, t17):
        assert _utc(rec["meta"]["rule"]["posted"]["created_utc"]) < _utc(rec["meta"]["utc"])
        assert rec["meta"]["utc"][:10] == "2026-10-19"
    assert len(t17["jobs"]["B1"]["execution_metadata"]["execution_spans"]) == 6
    assert (
        "Two runs on ibm_fez's qubit 143 on 19 October 2026, test 11's design on a third day and one job of six "
        "execution spans, were read per shot, each run and each read under a rule hashed before it ([finding 30]"
        "(docs/findings.md#finding-30))." in flat
    )
    m16 = rr.t16_day3_read(t16, archive.load("ibm_fez/t15-error-model-read.json"), d3)
    m17 = rr.t17_read(t17)
    assert {b["word"] for b in m17["boundaries"][4:]} == {"NO CHANGE"} and len(m17["boundaries"][4:]) == 5
    means = [*m16["beside_day_means"]["day_mean_duties"], m17["between_jobs_job_rows"]["B1"]["job_mean_w_duty"]]
    assert [_q(x, 3) for x in means] == ["0.330", "0.341", "0.313"]
    assert max(b["ratio"] for b in m17["boundaries"][4:]) < 2  # each pair within twice its combined error
    assert (
        "Across the six spans of one job every boundary read NO CHANGE, each adjacent pair differing by less than "
        "twice its combined error, which does not show the duties equal; and the monitor means of runs on 17 and 19 "
        "October were 0.330, 0.341 and 0.313. A pattern" in flat
    )
    assert "switching time" not in flat and "moved" not in flat and "held" not in flat
    assert m17["middle_test"]["pooled"]["word"] == "NOT SEEN"
    assert (
        "A pattern noticed in the published weights, a job's middle span above its ends, was tested on new data under "
        "a rule fixed before them and not seen." in flat
    )
    assert (
        "The desk model Sandhi, at version 4.1, had its bets for one design hashed before the run and none counted "
        "against it, with its bets for the other design not yet scored; no cause is named." in flat
    )
    assert flat.endswith("Released as 0.10.0 on 20 October 2026.")  # the release pull request dated it
    for word in ("parit", "veri" + "fied", "valid" + "ated", "prov" + "en", "constant", "telegraph", "defect", "first"):
        assert word not in flat.lower(), word
    assert "—" not in flat and "–" not in flat


# --------------------------------------------------------------------------- findings 20 and 21 (Amendment A23)
def _cells_line(chain: str, m: str, parts: list) -> str:
    """A chain's line of informative cells, as finding 19's: "d1" is written once."""
    return (
        f"- **{chain}**, with {m} waiting: "
        + " and ".join([parts[0], *(x.removeprefix("d1 ") for x in parts[1:])])
        + "."
    )


def _d1_part(cell: dict, arch: dict) -> str:
    lo, hi = (_q(x, 3, True) for x in arch["d1_ci90"])
    ang = "0°" if cell["phi_deg"] == 0 else "+90°"
    return f"d1 {_q(cell['d1'], 3, True)} at {ang} ({lo} to {hi})"


def _measure_reset_dt(doc: dict) -> set:
    """The neighbours' measure and reset durations in the run's live build, in dt."""
    out = set()
    for c in doc["circuits"].values():
        for times in c["_neighbours"]["measure_reset_times"].values():
            out |= {(t["op"], t["duration_dt"]) for t in times["W-no unedited"]}
    return out


def test_finding_20():
    """Kickoff 55, recomputed from the counts: the chains as drawn, the window and the posted rule, the four informative
    cells and the verdict, the original rule beside it, the lean against ibm_fez's, the reading after the data and its
    single-phase estimate, and the stamps."""
    import math

    from _reproduce import (
        K50,
        K51,
        K52,
        K53,
        K54,
        K55,
        k52_recomputed,
        k53_recomputed,
        k54_recomputed,
        k55_recomputed,
        reuse_doc,
    )

    item = _item(20)
    doc = reuse_doc(K55)
    m, a = doc["meta"], doc["archived"]["analysis"]
    k = k55_recomputed()
    arch = {c["cell"]: c for c in a["cells"]}
    cells = {c["cell"]: c for c in k["cells"]}
    assert (hhmm(doc["timestamps"]["running"]), hhmm(doc["timestamps"]["finished"])) == ("22:42", "22:44")
    assert m["processor"] == "ibm_kingston" and m["utc"].startswith("2026-10-14")
    assert "(Kickoff 55; ibm_kingston, 14 October 2026, 22:42 to 22:44 UTC)" in item
    bf = m["built_from"]
    assert bf["commit"].startswith("e45f15d") and bf["pull_request"] == 34 and bf["version"] == "0.5.0"
    assert "built unedited from this repository at commit `e45f15d`, the head of pull request 34" in item
    # the draw
    draw = doc["chain_draw"]
    assert (draw["n_candidates"], draw["n_survivors"]) == (488, 290)
    assert draw["n_excluded"] == {"a readout error above 3%": 180, "a CZ error above 1%": 18}
    assert draw["n_candidates"] - sum(draw["n_excluded"].values()) == draw["n_survivors"]
    assert all(all(c["operational"].values()) for c in draw["drawn"])
    assert (
        "was a candidate (488). Any chain with a qubit whose readout error was above 3% was set aside (180), then any "
        "with a CZ error above 1% (18), leaving 290; no qubit was reported as not operational." in item
    )
    assert "default_rng(5555)" in draw["procedure"] and "NumPy's `default_rng(5555)`" in item
    chains = ["-".join(map(str, c["chain"])) for c in draw["drawn"]]
    assert chains == ["139-155-154", "31-18-11", "6-7-8", "42-43-44"] and m["chains"] == [
        c["chain"] for c in draw["drawn"]
    ]
    assert "until four were taken: 139-155-154, 31-18-11, 6-7-8 and 42-43-44 (`chain_draw` in the data)" in item
    # the circuits and shots
    parts = [lab["part"] for lab in doc["labels"]]
    assert (parts.count("W") + parts.count("R"), parts.count("B")) == (64, 24) and m["copies"] == 2
    assert m["shots_by_part"] == {"B": 1500, "R": 3500, "W": 3500}
    assert {lab["circuit"] for lab in doc["labels"] if lab["part"] == "B"} == {"R1", "X1"}
    assert {lab["phi_deg"] for lab in doc["labels"] if lab["part"] == "B" and lab["circuit"] == "R1"} == {180, 270}
    assert "32 circuits for the verdict, each twice with 3,500 shots." in item
    assert "Beside them, each twice with 1,500 shots, R1 at 180° and 270° and, on each M, X then a measurement." in item
    # T_M and the neighbours' measure and reset, against ibm_fez's
    tm = {M: v["T_dt"] for M, v in m["T_M"]["per_chain"].items()}
    assert tm == {"155": 3403, "18": 3403, "7": 3412, "43": 3403}
    assert (r(3403 * m["T_M"]["dt_s"] * 1e6, 2), r(3412 * m["T_M"]["dt_s"] * 1e6, 2)) == (13.61, 13.65)
    fez = {v["T_dt"] for f in (K50, K51, K52, K53, K54) for v in reuse_doc(f)["meta"]["T_M"]["per_chain"].values()}
    assert fez == {2611}
    assert (
        "T_M was 3,403 dt (13.61 µs) on three chains and 3,412 dt (13.65 µs) on 6-7-8, against 2,611 dt on ibm_fez in "
        "findings 16 to 19 and 21" in item
    )
    assert _measure_reset_dt(doc) == {("measure", 545), ("reset", 553)}
    assert _measure_reset_dt(reuse_doc(K54)) == {("measure", 415), ("reset", 421)}
    assert (
        "here the neighbours' measure took 545 dt and their reset 553 dt, against 415 dt and 421 dt on ibm_fez" in item
    )
    # the rule, its post and its window
    n, url, when = _posted(K55)
    assert (n, when) == (36, "22:25") and _utc(m["rule"]["posted"]["created_utc"]) < _utc(m["submitted_utc"])
    assert f"([issue 36]({url}), 22:25 UTC; `data/ibm_kingston/k55-rule.md`)" in item
    fx = doc["fixed_before_the_data"]
    assert (fx["margin"], fx["informative_floor"]) == (0.15, 0.2)
    w = doc["window"]["window"]
    assert w["applies"] and (hhmm(w["from_utc"]), hhmm(w["to_utc"])) == ("05:59", "12:04")
    assert w["from_utc"].startswith("2026-10-15") and not _utc(w["from_utc"]) <= _utc(m["submitted_utc"]) <= _utc(
        w["to_utc"]
    )
    assert hhmm(m["submitted_utc"]) == "22:42" and m["submitted_utc"].startswith("2026-10-14")
    assert _utc(doc["window"]["computed_utc"]) < _utc(doc["calibration_record"]["stamps"][0]["utc"])
    assert (
        "a window computed before the build, by a procedure it fixed, from ibm_kingston's calibration stamps of the "
        "previous 48 hours: 05:59 to 12:04 UTC on 15 October (`window` in the data). The job was submitted at 22:42 "
        "UTC on 14 October." in item
    )
    # the verdict
    assert k["H55"] == "DISAGREE" and k["informative_cells"] == ["155|+90", "18|+90", "7|+90", "43|+90"]
    assert "The verdict: DISAGREE." in item
    outside = [c for c in k["informative_cells"] if arch[c]["d1_ci90"][0] > 0.15]
    across = [c for c in k["informative_cells"] if arch[c]["d1_ci90"][0] < 0.15 < arch[c]["d1_ci90"][1]]
    assert (outside, across) == (["7|+90"], ["43|+90"])
    for chain, M, tail in (
        ("6-7-8", "7", ", entirely above +0.15"),
        ("42-43-44", "43", ", across the line"),
        ("139-155-154", "155", ""),
        ("31-18-11", "18", ""),
    ):
        c = f"{M}|+90"
        assert _cells_line(chain, M, [_d1_part(cells[c], arch[c]) + tail]) in item, c
    zero = [cells[f"{M}|+0"] for M in ("155", "18", "7", "43")]
    assert not any(c["informative_R1"] for c in zero)
    assert (_q(min(c["d1"] for c in zero), 3, True), _q(max(c["d1"] for c in zero), 3, True)) == ("+0.071", "+0.119")
    assert "No cell at φ = 0 was informative, and there d1 ran from +0.071 to +0.119." in item
    # the original rule, beside
    b = k["original_rule_and_comparison"]
    assert b["original_rule_verdict"] == "DISAGREE" and b["original_rule_informative_cells"] == k["informative_cells"]
    assert all(arch[c]["d0_ci90"][0] > 0.15 for c in k["informative_cells"])
    d0 = [cells[c]["d0"] for c in k["informative_cells"]]
    assert (_q(min(d0), 3, True), _q(max(d0), 3, True)) == ("+0.166", "+0.326")
    assert (
        "would have returned DISAGREE on the same four cells, every one of them entirely above +0.15, with d0 from "
        "+0.166 to +0.326" in item
    )
    gaps = [abs(cells[c]["d0"]) - abs(cells[c]["d1"]) for c in k["informative_cells"]]
    assert min(gaps) > 0 and (_q(min(gaps), 3), _q(max(gaps), 3)) == ("0.047", "0.093")
    assert (
        "On every informative cell the active-neighbour Ramsey was the closer of the two, its |d1| smaller than |d0| "
        "by 0.047 to 0.093." in item
    )
    # the lean, against ibm_fez's at the chains' own offsets
    lean = k["lean"]
    assert lean["n_d1_above_zero"] == lean["n_cells"] == 8 and _q(lean["mean_d1"], 3, True) == "+0.121"
    mean0 = sum(c["d1"] for c in zero) / 4
    fez0 = [[c["d1"] for c in r_["cells"] if c["phi_deg"] == 0] for r_ in (k53_recomputed(), k54_recomputed())]
    assert (_q(mean0, 3, True), *(_q(sum(x) / len(x), 3, True) for x in fez0)) == ("+0.092", "+0.059", "+0.069")
    assert mean0 > max(sum(x) / len(x) for x in fez0)
    assert (
        "Every d1 was positive, a mean of +0.121 over the eight cells; at the chains' own offsets, φ = 0, d1 ran from "
        "+0.071 to +0.119, a mean of +0.092, against means of +0.059 and +0.069 on ibm_fez's chains in findings 19 "
        "and 21." in item
    )
    assert "Its source is not separated." in item and "it does not compare the processors." in item
    # the reading after the data, and its single-phase estimate on 7
    left = {q: k52_recomputed()["per_M"][q]["W_minus_R1"]["deg"] for q in ("143", "144")}
    assert {q: _q(abs(v), 1) for q, v in left.items()} == {"143": "4.8", "144": "3.5"}
    assert "which finding 18 measured at 3.5° and 4.8° on ibm_fez" in item
    fit = k["beside"]["R1_fit"]["7"]
    assert (_q(fit["theta_deg"], 1, True), _q(fit["amplitude"], 3)) == ("+14.4", "0.382")
    assert "On 7, R1's fitted offset over the four phases was +14.4° and its amplitude 0.382" in item
    f_ref, th = k["chains"]["7"]["F_ref"], math.radians(fit["theta_deg"])
    excess = cells["7|+90"]["d1"] - cells["7|+0"]["d1"]
    per_deg = f_ref * fit["amplitude"] * math.pi / 180
    lean_only_at_0 = excess / (per_deg * math.sin(math.pi / 2 + th))
    leftover_at_both = excess / (per_deg * (math.sin(math.pi / 2 + th) - math.sin(th)))
    assert 10 <= lean_only_at_0 < 100 and 10 <= leftover_at_both < 100  # tens of degrees, either way
    assert "puts the leftover at tens of degrees, an estimate from a single phase" in item
    assert "A reading after the data: what failed is the margin, not the choice of instrument." in item
    assert "The sweep that would measure it was not run in this kickoff." in item
    # the stamps
    rows = doc["calibration_record"]["stamps"]
    seen = [(row["kind"], row["stamp_utc"][11:19], row["job_status"]) for row in rows]
    assert seen == [
        ("build", "22:21:08", ""),
        ("submission (rebuild)", "22:21:08", ""),
        ("poll", "22:21:08", "RUNNING"),
        ("after fetch", "22:21:08", "DONE"),
        ("poll", "22:41:12", "DONE"),
    ]
    assert utc_of(draw["calibration_stamp"]) == "2026-10-14T22:21:08Z"
    new = rows[-1]
    assert new["utc"].endswith("22:47:32Z") and _utc(new["utc"]) > _utc(doc["timestamps"]["finished"])
    assert _utc(new["stamp_utc"]) < _utc(m["submitted_utc"]) and m["submitted_utc"].endswith("22:42:24Z")
    assert (new["q_readout_error"], new["q_T1"], new["q_T2"], new["g1_any"], new["cz_error"], new["cz_length"]) == (
        "153",
        "0",
        "0",
        "0",
        "0",
        "0",
    )
    assert new["other_values_changed"] == "gate.measure.gate_error 153; qubit.init_error 97"
    assert (
        "A poll at 22:47:32 UTC, after the job had finished, first saw a stamp dated 22:41:12 UTC, before the "
        "submission at 22:42:24: at it IBM published new readout errors on 153 qubits and new initialisation errors on "
        "97, and no T1, T2, single-qubit gate or CZ value changed (`calibration_record` in the data)." in item
    )
    assert (
        "Which of the two stamps the job ran under is not known." in item
        and "Manacitra does not rank machines." in item
    )


def utc_of(stamp: str) -> str:
    """A stamp as IBM's properties give it (a local offset), in UTC, ISO 8601."""
    return datetime.fromisoformat(stamp).astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def test_finding_21():
    """Kickoff 54, recomputed from the counts: the fixed chains, the day and its stamps, the two submissions, the
    posted rule, the seven informative cells and the verdict, the original rule beside it, the single-neighbour shifts
    against finding 17's, the readout measured beside the published values, and qubit 103."""
    from _reproduce import K50, K51, K52, K53, K54, k51_recomputed, k54_recomputed, reuse_doc

    item = _item(21)
    doc = reuse_doc(K54)
    m, a = doc["meta"], doc["archived"]["analysis"]
    k = k54_recomputed()
    arch = {c["cell"]: c for c in a["cells"]}
    cells = {c["cell"]: c for c in k["cells"]}
    assert (hhmm(doc["timestamps"]["running"]), hhmm(doc["timestamps"]["finished"])) == ("15:07", "15:09")
    assert m["processor"] == "ibm_fez" and "(Kickoff 54; ibm_fez, 15 October 2026, 15:07 to 15:09 UTC)" in item
    assert m["built_from"]["commit"].startswith("e45f15d") and "built unedited at `e45f15d`" in item
    # the chains, fixed by the rule
    k52 = reuse_doc(K52)["meta"]["chains"]
    assert m["chains"] == [*reuse_doc(K53)["meta"]["chains"], k52["144"], k52["143"]]
    assert {tuple(reuse_doc(K50)["meta"]["chains"][q]) for q in ("144", "143")} == {tuple(c) for c in m["chains"][4:]}
    assert (
        "finding 19's four, 31-30-29, 75-74-73, 120-121-116 and 96-103-104, and the two of findings 16 to 18, "
        "143-144-145 and 144-143-142." in item
    )
    parts = [lab["part"] for lab in doc["labels"]]
    assert (parts.count("W") + parts.count("R"), parts.count("B"), len(parts)) == (96, 112, 208)
    assert m["shots_by_part"] == {"B": 1500, "R": 3500, "W": 3500} and m["copies"] == 2
    beside = {(lab["circuit"], lab["phi_deg"]) for lab in doc["labels"] if lab["part"] == "B"}
    assert {c for c, _ in beside} == {"X1", "XY4", "R1", "N-idle", "N-L1", "N-L3", "N-both"}
    assert {p for c, p in beside if c.startswith("N-")} == {0, 90, 180, 270}
    assert {lab["M"] for lab in doc["labels"] if lab["circuit"].startswith("N-")} == {144, 143}
    assert "48 circuits for the verdict, each twice with 3,500 shots." in item and "One job of 104 circuits." in item
    assert {v["T_dt"] for v in m["T_M"]["per_chain"].values()} == {2611} and "T_M was 2,611 dt (10.44 µs)" in item
    # the day
    fs = doc["first_submission"]
    mt = doc["maintenance"]
    assert fs["cancellation"]["ibm_fez"]["status_msg"] == "maintenance"
    gap = mt["summary"]["no_stamp_between"]
    assert gap[2] == "16 h 14 min" and round((_utc(gap[1]) - _utc(gap[0])).total_seconds() / 60) == 16 * 60 + 14
    assert (
        "IBM published no calibration stamp for it for 16 hours 14 minutes, from 13:30:22 UTC on 14 October to "
        "05:44:28 UTC on 15 October." in item
    )
    cyc = mt["summary"]["cycle_15_october_so_far"]
    assert cyc["T1"].startswith("2026-10-15T09:16:30Z") and cyc["single_qubit"].startswith("2026-10-15T10:08:09Z")
    cz = [row for row in mt["watch"] if row["cz_error"] not in ("", "0")]
    assert [row["stamp_utc"] for row in cz] == ["2026-10-15T12:05:17Z"]
    build = next(
        row for row in doc["calibration_record"]["stamps"] if row["kind"] == "build" and row["utc"] > "2026-10-15"
    )
    assert _utc(cz[0]["stamp_utc"]) < _utc(build["utc"])
    assert (
        "new T1 values were published at 09:16:30 UTC, new single-qubit gate errors at 10:08:09 UTC and new CZ errors "
        "at 12:05:17 UTC, all before the build" in item
    )
    second = [row for row in doc["calibration_record"]["stamps"] if row["utc"] >= build["utc"]]
    assert [row["kind"] for row in second] == ["build", "submission (rebuild)", "poll", "poll", "after fetch"]
    assert {row["stamp_utc"] for row in second} == {"2026-10-15T14:39:04Z"}
    assert set(doc["run"][x] for x in doc["run"] if x.endswith("_utc")) == {"2026-10-15T14:39:04Z"}
    walk = doc["calibration_record"]["walk_over_the_job"]
    assert walk["walk_distinct_stamps"] == ["2026-10-15T14:39:04Z"] and walk["all_polled_in_walk"]
    assert (
        "One stamp, 14:39:04 UTC, was in force at the build, the submission, both polls and the read after the fetch, "
        "and a walk over the stamps from the build to the fetch found no other" in item
    )
    # the submissions
    c = fs["cancellation"]
    assert (fs["job_id"], c["job_id"]) == ("db7uvo8r1c5c738lcatg",) * 2 and m["job_id"] == "db8ena6il99s73fprd9g"
    assert hhmm(fs["submitted_utc"]) == "21:11" and fs["submitted_utc"].startswith("2026-10-14")
    assert hhmm(c["cancel_called_utc"]) == "22:24" and (c["status_at_check"], c["status_after_cancel"]) == (
        "QUEUED",
        "CANCELLED",
    )
    assert c["timestamps"]["running"] is None and "author" in c["instruction"]
    assert hhmm(m["submitted_utc"]) == "15:05" and m["submitted_utc"].startswith("2026-10-15")
    assert fs["labels"] == doc["labels"] and fs["calibration_at_build"] != doc["run"]["calibration_at_build"]
    assert (
        "The job was first submitted at 21:11 UTC on 14 October (`db7uvo8r1c5c738lcatg`), and was cancelled in the "
        "queue at 22:24 UTC on the author's instruction, while ibm_fez reported maintenance; IBM records no running "
        "time for it." in item
    )
    assert "at 15:05 UTC on 15 October (`db8ena6il99s73fprd9g`)" in item
    # the rule
    n, url, when = _posted(K54)
    assert (n, when) == (35, "16:51") and _utc(m["rule"]["posted"]["created_utc"]) < _utc(fs["submitted_utc"])
    assert (
        f"([issue 35]({url}), 16:51 UTC on 14 October, before the first submission; `data/ibm_fez/k54-rule.md`)" in item
    )
    # the verdict
    assert k["H54"] == "AGREE" and k["informative_cells"] == [
        "30|+90",
        "74|+90",
        "121|+90",
        "103|+0",
        "103|+90",
        "144|+90",
        "143|+0",
    ]
    assert "The verdict: AGREE, on all seven informative cells." in item
    for chain, M in (
        ("31-30-29", "30"),
        ("75-74-73", "74"),
        ("120-121-116", "121"),
        ("96-103-104", "103"),
        ("143-144-145", "144"),
        ("144-143-142", "143"),
    ):
        inf = [c for c in k["informative_cells"] if c.split("|")[0] == M]
        assert _cells_line(chain, M, [_d1_part(cells[c], arch[c]) for c in inf]) in item, M
    ends = [arch[c]["d1_ci90"] for c in k["informative_cells"]]
    assert all(-0.15 < lo and hi < 0.15 for lo, hi in ends) and _q(max(hi for _, hi in ends), 3, True) == "+0.086"
    assert "Every d1 interval lay inside ±0.15; the widest reached +0.086." in item
    # the original rule, beside
    b = k["original_rule_and_comparison"]
    assert b["original_rule_verdict"] == "DISAGREE"
    out0 = [c for c in b["original_rule_informative_cells"] if arch[c]["d0_ci90"][0] > 0.15]
    over = [c for c in b["original_rule_informative_cells"] if arch[c]["d0_ci90"][0] < 0.15 < arch[c]["d0_ci90"][1]]
    assert (out0, over) == (["74|+90"], ["144|+90"])
    lo, hi = (_q(x, 3, True) for x in arch["74|+90"]["d0_ci90"])
    assert f"on 74 at +90°, with d0 {_q(cells['74|+90']['d0'], 3, True)} ({lo} to {hi}) entirely above +0.15" in item
    lo, hi = (_q(x, 3, True) for x in arch["144|+90"]["d0_ci90"])
    assert f"144 at +90° lay across the line, at {_q(cells['144|+90']['d0'], 3, True)} ({lo} to {hi})" in item
    assert (_q(b["mean_abs_d1_informative"], 3), _q(b["mean_abs_d0_informative"], 3)) == ("0.041", "0.109")
    assert "the revised check's mean |d1| was 0.041 and the original's mean |d0| 0.109" in item
    lean = k["lean"]
    assert lean["n_d1_above_zero"] == lean["n_cells"] == 12 and _q(lean["mean_d1_informative"], 3, True) == "+0.041"
    assert "Every one of the twelve d1 was positive, a mean of +0.041 over the informative cells." in item
    # one neighbour at a time
    nb, na = k["beside"]["neighbours"], a["beside"]["neighbours"]
    for q, (l1, l3), lead, tail in (
        ("144", ("143", "145"), "On 144 the shifts were", " in |1⟩"),
        ("143", ("144", "142"), "On 143 they were", ""),
    ):
        assert m["chains"][4 if q == "144" else 5] == [int(l1), int(q), int(l3)]
        sh = {v: _q(x, 1, True) for v, x in nb[q]["shift_deg"].items()}
        lo, hi = (_q(x, 1, True) for x in na[q]["sum_minus_both_ci90"])
        assert (
            f"{lead} {sh['L1']}° with only {l1}{tail}, {sh['L3']}° with only {l3} and {sh['both']}° with both; the sum "
            f"minus the joint shift was {_q(nb[q]['sum_minus_both_deg'], 1, True)}° ({lo}° to {hi}°)." in item
        ), q
    within = {q: _q(abs(nb[q]["sum_minus_both_deg"]), 1) for q in ("144", "143")}
    assert within == {"144": "0.3", "143": "3.4"} and "within 0.3° on 144 and 3.4° on 143" in item
    pair, pa = k["beside"]["pair_143_144"], a["beside"]["pair_143_144"]
    lo, hi = (_q(x, 1, True) for x in pa["difference_ci90"])
    a144, a143 = (_q(pair[f"from_{x}"], 1, True) for x in ("144_only_143_in_1", "143_only_144_in_1"))
    assert (
        f"{a144}° seen from 144 and {a143}° seen from 143, a difference of {_q(pair['difference_deg'], 1, True)}° "
        f"({lo}° to {hi}°)" in item
    )
    k51 = k51_recomputed()["per_M"]
    day1 = {q: k51[q]["fit_R2"]["theta_deg"] - k51[q]["fit_R0"]["theta_deg"] for q in ("144", "143")}
    assert {q: _q(v, 1, True) for q, v in day1.items()} == {"144": "−76.0", "143": "−37.6"}
    assert {q: _q(nb[q]["shift_deg"]["both"], 1, True) for q in ("144", "143")} == {"144": "−81.4", "143": "−40.5"}
    assert reuse_doc(K51)["meta"]["utc"].startswith("2026-10-13")
    assert (
        "−76.0° on 144 and −37.6° on 143 in finding 17's three-point fits on 13 October, −81.4° and −40.5° here."
        in item
    )
    assert (
        "A fixed shift per neighbour pair predicts both the sums and the symmetry; the mechanism is not tested." in item
    )
    # the readout, measured beside the published values at the stamp in force
    ro = k["beside"]["readout_P0_given_1"]
    p01 = [v["P0_given_1"] for v in ro.values()]
    assert (_q(min(p01), 3), _q(max(p01), 3)) == ("0.005", "0.024")
    assert "P(0|1), ran from 0.005 to 0.024 on the six waiting qubits" in item
    pub = doc["calibration_record"]["published_at_build"]
    assert utc_of(pub["last_update_date"]) == "2026-10-15T14:39:04Z"
    waiting = {str(c[1]): pub["qubits"][str(c[1])] for c in m["chains"]}
    top = sorted(waiting, key=lambda q: -waiting[q]["readout_error"]["value"])[:2]
    assert top == ["103", "143"]
    assert [_q(waiting[q]["readout_error"]["value"], 3) for q in top] == ["0.376", "0.232"]
    assert [_q(waiting[q]["prob_meas0_prep1"]["value"], 3) for q in top] == ["0.630", "0.368"]
    assert (
        "At the stamp in force IBM's table published readout errors of 0.376 on 103 and 0.232 on 143, and, for the "
        "quantity measured here, P(0|1) of 0.630 and 0.368." in item
    )
    assert "it says nothing about their cause, and nothing about anyone's calibration." in item
    # qubit 103
    cost = k["beside"]["pulse_cost"]
    clear = [q for q, v in a["beside"]["pulse_cost"].items() if v["P1_minus_Z_ci90"][0] > 0]
    assert clear == ["103"] and _q(cost["103"]["P1_minus_Z"], 3, True) == "+0.015"
    lo, hi = (_q(x, 3, True) for x in a["beside"]["pulse_cost"]["103"]["P1_minus_Z_ci90"])
    assert f"clear of zero, +0.015 ({lo} to {hi})" in item
    assert max(ro, key=lambda q: ro[q]["P0_given_1"]) == "103"
    fits = k["beside"]["R1_fit"]
    assert min(fits, key=lambda q: fits[q]["amplitude"]) == "103" and _q(fits["103"]["amplitude"], 3) == "0.325"
    worst = sorted(fits, key=lambda q: -max(abs(x) for x in fits[q]["residuals"]))[:2]
    assert worst == ["143", "103"]
    assert [_q(max(abs(x) for x in fits[q]["residuals"]), 3) for q in ("103", "143")] == ["0.039", "0.042"]
    assert "one of the two largest residuals of the R1 fits (0.039; 143's was 0.042). Its two cells held." in item
    assert all(cells[c]["d1_inside"] for c in ("103|+0", "103|+90"))
    assert "Manacitra does not rank machines." in item


def test_findings_20_and_21_beside_the_findings():
    """Amendment A23: the README's count; the two bullets of what has not been shown that A23 rewrote; the method's
    paragraph on the margin's record; the reproduce page's pointers; the kickoffs rows; the long documentation's row;
    the changelog's lead; and the data README's count of job IDs."""
    from _reproduce import (
        K53,
        K54,
        K55,
        k50_recomputed,
        k51_recomputed,
        k52_recomputed,
        k53_recomputed,
        k54_recomputed,
        k55_recomputed,
        reuse_doc,
    )

    readme = " ".join((ROOT / "README.md").read_text().split())
    assert "the thirty findings in full, with a table of all of them, what was known before them" in readme  # A27
    flat = " ".join((ROOT / "docs" / "findings.md").read_text().split())
    r53, r54, r55 = k53_recomputed(), k54_recomputed(), k55_recomputed()
    # the margin's bullet
    fez = [*r53["informative_cells"], *r54["informative_cells"]]
    assert r53["H53"] == r54["H54"] == "AGREE" and len(fez) == 12
    out = [
        c
        for c in r55["informative_cells"]
        if reuse_doc(K55)["archived"]["analysis"]["cells"][[x["cell"] for x in r55["cells"]].index(c)]["d1_ci90"][0]
        > 0.15
    ]
    assert out == ["7|+90"] and _q(next(c["d1"] for c in r55["cells"] if c["cell"] == "7|+90"), 3, True) == "+0.257"
    # A24 replaced this bullet with the margin at the peak phase (test_findings_22_to_27_beside_the_findings)
    assert "The ±0.15 margin held on one processor for two days and failed on a second." not in flat
    assert "The active-neighbour check has run on one processor." not in flat
    # the lean bullet
    cells = [k50_recomputed()["per_M"][q]["d1"] for q in ("144", "143")]
    cells += [v for q in ("144", "143") for v in k51_recomputed()["per_M"][q]["d1"].values()]
    cells += [v for q in ("143", "144") for v in k52_recomputed()["per_M"][q]["d1"].values()]
    cells += [c["d1"] for r_ in (r53, r55, r54) for c in r_["cells"]]
    assert (len(cells), sum(x > 0 for x in cells)) == (48, 47)
    zero = {
        n: [c["d1"] for c in r_["cells"] if c["phi_deg"] == 0]
        for n, r_ in (("fez", r53["cells"] + r54["cells"]), ("kingston", r55["cells"]))
        for r_ in [{"cells": r_}]
    }
    assert (_q(min(zero["kingston"]), 3, True), _q(max(zero["kingston"]), 3, True)) == ("+0.071", "+0.119")
    assert (_q(min(zero["fez"]), 3, True), _q(max(zero["fez"]), 3, True)) == ("+0.045", "+0.101")
    assert (
        "- **Its positive lean is unexplained.** The active-neighbour residual d1 has read high in 47 of its 48 cells "
        "so far (findings 16 to 21). On ibm_kingston the lean was larger: at the chains' own offsets d1 ran from "
        "+0.071 to +0.119 (finding 20), against +0.045 to +0.101 on ibm_fez (findings 19 and 21)." in flat
    )
    # the method's paragraph
    method = " ".join((ROOT / "docs" / "method.md").read_text().split())
    assert (
        "The margin's record, on two processors: on ibm_fez the check with the active-neighbour Ramsey predicted the "
        "wait test within ±0.15 on every informative cell on two days, across a maintenance" in method
    )
    assert (
        "on ibm_kingston it missed on one informative cell of four, by +0.257, where the check with idle neighbours "
        "would have missed on all four ([finding 20](findings.md#finding-20))" in method
    )
    # the reproduce page's pointers
    page = " ".join((ROOT / "docs" / "reproduce.md").read_text().split())
    for n in (20, 21):
        assert f"[{'F' if n == 20 else 'f'}inding {n}](findings.md#finding-{n})" in page
    assert "each with its circuits built by this code at `e45f15d`, the head of pull request 34, unedited" in page
    assert "(`k55_kingston` and `k54_day_two`)" in page
    # the kickoffs rows, and the long documentation's row
    kick = (ROOT / "docs" / "kickoffs.md").read_text()
    assert "| 54, 15 October 2026 |" in kick and "`ibm_fez/k54-rule.md`" in kick
    assert "| 55, 14 October 2026 |" in kick and "`ibm_kingston/k55-rule.md`" in kick
    index = " ".join((ROOT / "docs" / "index.md").read_text().split())
    d7 = _q(next(c["d1"] for c in r55["cells"] if c["cell"] == "7|+90"), 3, True)
    d74 = _q(next(c["d0"] for c in r54["cells"] if c["cell"] == "74|+90"), 3, True)
    assert (d7, d74) == ("+0.257", "+0.184")
    assert f"DISAGREE ({d7} on 7 at +90°), and the original DISAGREE on all four informative cells" in index
    assert f"AGREE on seven informative cells, and the original DISAGREE ({d74} on 74)" in index
    assert (
        "(and ibm_fez again on 10, 11, 13, 15 and 16 October, and ibm_kingston again on 14 and 15 October)" in index
    )  # A25
    # the changelog's lead: six runs on ibm_fez on 13 and 15 October and one on ibm_kingston on 14 October
    from manacitra import archive as ar

    fez_runs = [p for p in ar.records() if p.parent.name == "ibm_fez" and ar.load(p)["meta"]["kickoff"][8:].isdigit()]
    fez_runs = [p for p in fez_runs if 49 <= int(ar.load(p)["meta"]["kickoff"][8:]) <= 55]
    assert sorted(ar.load(p)["meta"]["utc"][:10] for p in fez_runs) == ["2026-10-13"] * 5 + ["2026-10-15"]
    assert reuse_doc(K55)["meta"]["utc"].startswith("2026-10-14")
    log = " ".join((ROOT / "CHANGELOG.md").read_text().split())
    assert "## 0.6.0 (15 October 2026)" in log and "## Unreleased" not in log
    assert (
        "(unreleased)" not in log.split("## 0.6.0 (15 October 2026)", 1)[1]
    )  # A24: 0.7.0's heading waits for its date
    assert (
        "Findings 15 to 21, from six runs on ibm_fez on 13 and 15 October 2026 and one on ibm_kingston on 14 October, "
        "with their data." in log
    )
    assert (
        "the original check would have returned DISAGREE in all three runs, and on each of the eight cells where it "
        "missed, the active-neighbour Ramsey was the closer instrument." in log
    )
    assert all(
        r_ == "DISAGREE"
        for r_ in (
            r53["beside"]["original_rule_verdict"],
            r54["original_rule_and_comparison"]["original_rule_verdict"],
            r55["original_rule_and_comparison"]["original_rule_verdict"],
        )
    )
    assert reuse_doc(K53)["meta"]["processor"] == reuse_doc(K54)["meta"]["processor"] == "ibm_fez"
    # the data README's job IDs
    ids = [ar.load(p)["meta"].get("job_id") for p in ar.records()]
    many = [j for p in ar.records() for j in ar.load(p)["meta"].get("job_ids", {}).values()]
    assert (len([i for i in ids if i]), len(many)) == (
        30,
        30,
    )  # A24: 56 and 61; 57 to 59, 62; A25: test 7; A27: 8 to 11; A27, R2: tests 12 and 14; A28: day 3 and test 17
    data = " ".join((ar.data_dir() / "README.md").read_text().split())
    assert "the thirty IBM `meta.job_id` values and the thirty of the runs with several jobs" in data
    assert "as do the job IDs that tests 13, 15 and 16 read (`per_shot_results`; test 16's `meta.jobs_read`)" in data
    assert "(`first_submission.job_id`)" in data


def test_the_phase_sweep_picture():
    """Finding 18's picture: made from the data by docs/make_diagrams.py, referenced from finding 18, and its alt text
    carries the fitted offsets of the data."""
    from _reproduce import k52_recomputed

    findings = (ROOT / "docs" / "findings.md").read_text()
    item = findings.split('<a id="finding-18"></a>', 1)[1].split("<a id=", 1)[0]
    assert "](diagrams/phase-sweep.svg)" in item and (DIAGRAMS / "phase-sweep.png").is_file()
    alt = " ".join(item.split("![", 1)[1].split("](diagrams/phase-sweep.svg)", 1)[0].split())
    p = k52_recomputed()["per_M"]["144"]
    th = {c: _q(p["fits"][c]["theta_deg"], 1, True) for c in ("W", "R0", "R1")}
    assert th == {"W": "−16.1", "R0": "+5.4", "R1": "−12.7"}
    assert (
        f"the wait test's offset θ_W is {th['W']}°, the idle-neighbour Ramsey's θ_R0 is {th['R0']}° and the "
        f"active-neighbour Ramsey's θ_R1 is {th['R1']}°" in alt
    )
    d, w1 = _q(p["Delta_W_minus_R0"]["deg"], 1, True), _q(p["W_minus_R1"]["deg"], 1, True)
    assert f"Δ = θ_W − θ_R0 is {d}°, and θ_W − θ_R1 is {w1}°" in alt and (d, w1) == ("−21.6", "−3.5")
    text = svg_text(DIAGRAMS / "phase-sweep.svg")
    assert "13 October 2026, 18:59 to 20:00 UTC" in text and "θ_W = −16.1°" in text and "θ_R0 = +5.4°" in text
    assert "θ_R1 = −12.7°" in text and "Δ = θ_W − θ_R0 = −21.6°" in text


# --------------------------------------------------------------------------- findings 22 to 27 (Amendment A24)
def _ci(c, nd: int = 3, deg: bool = False) -> str:
    u = "°" if deg else ""
    return f"({_q(c[0], nd, True)}{u} to {_q(c[1], nd, True)}{u})"


def _hms(utc: str) -> str:
    return datetime.fromisoformat(utc.replace("Z", "+00:00")).strftime("%H:%M:%S")


def _job_span(doc: dict) -> tuple[str, str]:
    t = doc["timestamps"]
    if "running" in t:
        return t["running"], t["finished"]
    jobs = sorted(t)
    return t[jobs[0]]["running"], t[jobs[-1]]["finished"]


def _shots(doc: dict) -> dict:
    """Shots per circuit of each (job, block), from the record's labels and counts."""
    out: dict = {}
    for lab, cts in zip(doc["labels"], doc["counts"]):
        out.setdefault((lab.get("job"), lab.get("block") or lab.get("part")), set()).add(sum(cts.values()))
    assert all(len(v) == 1 for v in out.values()), out
    return {k: v.pop() for k, v in out.items()}


def _shuffle_seed(draw: dict) -> int:
    import re

    return int(re.search(r"default_rng\((\d+)\)", draw["procedure"]).group(1))


def test_finding_22():
    """Amendment A24: finding 22 (Kickoff 56), every number from the recompute or the record."""
    from _reproduce import K55, K56, k55_recomputed, k56_recomputed, reuse_doc

    item, doc, r = _item(22), reuse_doc(K56), k56_recomputed()
    a, pm = doc["archived"]["analysis"]["per_M"], r["per_M"]
    t0, t1 = _job_span(doc)
    assert (t0[:10], t1[:10], _hms(t0), _hms(t1)) == ("2026-10-14", "2026-10-15", "23:59:32", "00:01:50")
    assert "(Kickoff 56; ibm_kingston, from 23:59:32 UTC on 14 October 2026 to 00:01:50 UTC on 15 October)" in item
    L = {M: pm[M]["L_W_minus_R1"]["deg"] for M in ("7", "43", "18")}
    assert (_q(L["7"], 1, True), _q(L["43"], 1, True), abs(L["18"]) < 0.05) == ("−36.7", "−11.7", True)
    assert (
        "measured the leftover between the wait test and the active-neighbour Ramsey: −36.7° on the qubit where "
        "finding 20 missed, −11.7° on a second and 0.0° on the third" in item
    )
    assert sorted(doc["meta"]["chains"]) == sorted(reuse_doc(K55)["meta"]["chains"][1:]) and doc["meta"]["chains"][
        0
    ] == [6, 7, 8]
    assert doc["meta"]["built_from"]["commit"].startswith("e45f15d")
    assert len({(x["M"], x["circuit"], x["phi_deg"]) for x in doc["labels"]}) == 63 and len(doc["labels"]) == 126
    assert set(_shots(doc).values()) == {3000} and doc["meta"]["phis_deg"] == list(wait.SWEEP_PHASES_DEG)
    assert "63 circuits, each twice with 3,000 shots, in one job." in item
    stamps = {x["stamp_utc"] for x in doc["calibration_record"]["stamps"]}
    assert stamps == {"2026-10-14T23:06:14Z"} and doc["calibration_record"]["walk_over_the_job"]["all_polled_in_walk"]
    since = doc["chains_fixed"]["since_kickoff_55"]
    early, late = since["since K55 draw stamp 22:21:08"], since["since K55 later stamp 22:41:12"]
    assert [early[k] for k in ("q_T1", "q_T2", "g1_any", "cz_error", "q_readout_error")] == [0, 0, 0, 0, 153]
    assert late["q_readout_error"] == 0
    assert (
        "One calibration stamp, 23:06:14 UTC, was in force from the build to the read after the fetch; against finding "
        "20's stamp at its draw, no published T1, T2, single-qubit gate or CZ value had changed, and readout errors "
        "had "
        "changed on 153 qubits, at the 22:41:12 UTC stamp finding 20 describes." in item
    )
    assert _posted(K56) == (37, "https://github.com/dogma-guru/manacitra/issues/37", "23:08")
    assert "([issue 37](https://github.com/dogma-guru/manacitra/issues/37), 23:08 UTC on 14 October;" in item
    rule = (archive.data_dir() / "ibm_kingston" / "k56-rule.md").read_text()
    assert "entirely outside [−10°, +10°]" in rule and "entirely inside [−5°, +5°]" in rule
    for chain, M, v in (("6-7-8", "7", "LARGE"), ("42-43-44", "43", "NOT SETTLED"), ("31-18-11", "18", "SMALL")):
        assert pm[M]["verdict"] == v
        pt = "0.0" if M == "18" else _q(L[M], 1, True)
        assert f"- **{chain}**, with {M} waiting: L = {pt}° {_ci(a[M]['L_W_minus_R1']['ci90'], 1, True)}: {v}." in item
    miss = next(c for c in k55_recomputed()["cells"] if c["cell"] == "7|+90")
    assert _q(miss["d1"], 3, True) == "+0.257"
    assert "Finding 20's miss, d1 +0.257 at +90°, was on 6-7-8, the chain with the large leftover." in item
    lean = {M: _q(pm[M]["mean_d1"], 3, True) for M in pm}
    assert lean == {"7": "+0.076", "43": "+0.081", "18": "+0.059"} and all(a[M]["mean_d1_ci90"][0] > 0 for M in a)
    assert (
        "was positive on all three, +0.076 on 7, +0.081 on 43 and +0.059 on 18, each interval entirely above zero"
        in item
    )
    d18, d7 = pm["18"]["d1"].values(), pm["7"]["d1"]
    assert (_q(min(d18), 3, True), _q(max(d18), 3, True)) == ("+0.037", "+0.086")
    assert (_q(min(d7.values()), 3, True), _q(max(d7.values()), 3, True)) == ("−0.099", "+0.244")
    assert all(a["7"]["d1_ci90"][p][0] > 0.15 for p in ("60", "120")) and _q(d7["120"], 3, True) == "+0.222"
    assert (
        "on 7 it ran from −0.099 to +0.244, and its cells at 60° and 120° (+0.244 and +0.222) lay entirely above +0.15"
        in item
    )
    pc = {M: pm[M]["pulse_cost"]["P1_minus_Z"] for M in pm}
    assert [_q(pc[M], 3, True) for M in ("7", "43", "18")] == ["−0.002", "−0.001", "+0.002"]
    assert all(a[M]["pulse_cost"]["P1_minus_Z_ci90"][0] < 0 < a[M]["pulse_cost"]["P1_minus_Z_ci90"][1] for M in a)
    assert (
        "The pulse-cost circuit's P(1) above Z's was −0.002, −0.001 and +0.002, each interval containing zero" in item
    )
    rr = {M: -pm[M]["R1_minus_R0"]["deg"] for M in pm}
    assert [_q(rr[M], 1) for M in ("7", "43", "18")] == ["13.2", "10.5", "17.1"]
    assert abs(pm["18"]["W_minus_R0"]["deg"] - pm["18"]["R1_minus_R0"]["deg"]) < 0.05
    assert 0.2 < pm["7"]["R1_minus_R0"]["deg"] / pm["7"]["W_minus_R0"]["deg"] < 0.3
    assert "by 13.2°, 10.5° and 17.1° (θ_R1 − θ_R0)" in item
    # the reading after the data: the shots alone redrawn, the copies pooled, with the rule's seed
    rng = np.random.default_rng(doc["meta"]["seeds"]["bootstrap"])
    _, q = __import__("_reuse_runs")._wait_test_keys()
    import _reuse_runs as reuse

    cells, bits, _ = reuse._cells_and_bits(
        doc["labels"], doc["counts"], lambda x: (str(x["M"]), x["circuit"], x["phi_deg"])
    )
    shots_only = {}
    for M in ("7", "43", "18"):
        Fb = []
        for p in reuse.K52_PHIS:
            V = np.array([x[1] for x in cells[(M, "W-no", p)]], float).sum(0)
            m = rng.multinomial(int(V.sum()), V / V.sum(), size=10_000)
            Fb.append(np.sqrt(m / m.sum(-1, keepdims=True) * q).sum(-1) ** 2)

        def dp(k):
            o, t = sum(x[1] for x in bits[k]), sum(x[2] for x in bits[k])
            return rng.binomial(t, o / t, size=10_000) / t

        z = dp((M, "Z", 0))
        R1 = np.stack([dp((M, "R1", p)) - z for p in reuse.K52_PHIS], -1)
        Lb = reuse._wrap(reuse.theta_wait_test(np.stack(Fb, -1)) - reuse.theta_ramsey(R1))
        shots_only[M] = reuse.pct(L[M] + reuse._wrap(Lb - L[M]))
    lo, hi = shots_only["43"]
    assert hi < -10 and abs(lo + 13.1) < 0.3 and abs(hi + 10.3) < 0.3  # "about": a platform's stream moves the ends
    assert shots_only["7"][1] < -10 and -5 < shots_only["18"][0] and shots_only["18"][1] < 5
    assert (
        "with the shots alone redrawn and the copies pooled, 43's interval would be about −13.1° to −10.3°, entirely "
        "outside ±10°; the verdicts on 7 and 18 would not change." in item
    )
    assert "Manacitra does not rank machines." in item


def _peak_lines(a: dict, chains: list) -> list:
    out = []
    for c, chain in zip(a["cells_phi_star"], chains):
        assert c["M"] == str(chain[1]) and c["informative_R1"]
        name = "-".join(map(str, chain))
        out.append(
            f"- **{name}**, with {c['M']} waiting: d1 {_q(c['d1'], 3, True)} at {a['phi_star_deg'][c['M']]}° "
            f"{_ci(c['d1_ci90'])}."
        )
    return out


def test_finding_23():
    """Amendment A24: finding 23 (Kickoff 57)."""
    from _reproduce import K57, k57_recomputed, reuse_doc

    item, doc, r = _item(23), reuse_doc(K57), k57_recomputed()
    a = doc["archived"]["analysis"]
    t0, t1 = _job_span(doc)
    assert (hhmm(t0), hhmm(t1), t0[:10]) == ("00:39", "00:43", "2026-10-15")
    assert "(Kickoff 57; ibm_kingston, 15 October 2026, 00:39 to 00:43 UTC)" in item
    d = doc["chain_draw"]
    assert (d["n_candidates"], d["n_survivors"], _shuffle_seed(d)) == (488, 272, 5757)
    assert d["n_excluded"] == {
        "uses a qubit of Kickoffs 55 and 56": 68,
        "a readout error above 3%": 136,
        "a CZ error above 1%": 12,
    }
    chains = [x["chain"] for x in d["drawn"]]
    assert chains == doc["meta"]["chains"] == [[0, 1, 2], [90, 89, 88], [57, 47, 48], [17, 27, 28]]
    assert (
        "Of 488 candidates, 68 used a qubit of findings 20 and 22, 136 had a qubit with a readout error above 3% and "
        "12 "
        "a coupler with a CZ error above 1%, leaving 272; shuffled with NumPy's `default_rng(5757)`, the first four "
        "were "
        "taken: 0-1-2, 90-89-88, 57-47-48 and 17-27-28" in item
    )
    sh = _shots(doc)
    assert (sh[(1, "sweep")], sh[(2, "verdict")], sh[(2, "beside")]) == (2000, 3000, 1500)
    phi = r["phi_star_deg"]
    assert phi == {"1": 164, "89": 220, "47": 156, "27": 211} == a["phi_star_deg"]
    assert _utc(doc["peaks"]["computed_utc"]) < _utc(doc["meta"]["T_M"]["per_job"]["2"]["recorded_utc"])
    assert "164°, 220°, 156° and 211°, recorded before job 2 was built (`peaks` in the data)" in item
    assert {x["stamp_utc"] for x in doc["calibration_record"]["stamps"]} == {"2026-10-15T00:05:34Z"}
    assert (
        _posted(K57)[0::2] == (38, "00:26")
        and "([issue 38](https://github.com/dogma-guru/manacitra/issues/38), 00:26 UTC;" in item
    )
    assert r["H57"] == "AGREE" and len(r["informative_cells"]) == 4
    assert all(line in item for line in _peak_lines(a, chains))
    p90 = a["check_at_plus90"]  # interval-derived: as archived (A17)
    assert p90["verdict"] == "AGREE" and len(p90["informative_cells"]) == 4
    d90 = [c["d1"] for c in p90["cells"]]
    assert (_q(min(d90), 3, True), _q(max(d90), 3, True)) == ("+0.040", "+0.061")
    assert "would also have returned AGREE, all four cells informative, with d1 from +0.040 to +0.061" in item
    assert (r["original_rule_at_phi_star"]["verdict"], p90["original_rule_verdict"]) == ("AGREE", "NOT SETTLED")
    lean = r["lean_phi_star"]
    assert lean["n_d1_above_zero"] == 4 and _q(lean["mean_d1"], 3, True) == "+0.049"
    assert "Every d1 at the peak was positive, a mean of +0.049." in item
    assert max(abs(v["difference_P1"]) for v in r["drift"].values()) <= 0.0105
    assert "R1's P(1) at φ* in job 2 lay within 0.010 of what job 1's fit gave there." in item
    z = {M: v["P1_Z"] for M, v in r["chains"].items()}
    others = [z[M] for M in ("89", "47", "27")]
    assert (_q(z["1"], 2), _q(min(others), 3), _q(max(others), 3)) == ("0.30", "0.005", "0.024")
    assert _q(r["chains"]["1"]["F_ref"], 3) == "0.571"
    ro = d["drawn"][0]["readout_error"]["1"]
    assert f"{100 * ro:.2f}%" == "0.87%" and ro < 0.03
    assert (
        "Qubit 1 read P(1) 0.30 at zero wait, against 0.005 to 0.024 on the other three, and its F_ref was 0.571."
        in item
    )
    assert "Its published readout error at the draw was 0.87%, under the 3% the draw screened on" in item
    c1, c90 = a["cells_phi_star"][0], p90["cells"][0]
    assert (_q(c1["d1"], 3, True), _q(c90["d1"], 3, True)) == ("+0.116", "+0.051")
    assert c1["d1"] == max(c["d1"] for c in a["cells_phi_star"])
    assert "Both its cells held: +0.116 at φ*, the run's largest residual, and +0.051 at +90°." in item


def test_finding_24():
    """Amendment A24: finding 24 (Kickoff 58)."""
    from _reproduce import K56, K58, k55_recomputed, k56_recomputed, k58_recomputed, reuse_doc

    item, doc, r = _item(24), reuse_doc(K58), k58_recomputed()
    pc = doc["archived"]["analysis"]["per_chain"]  # the intervals and what rests on them, as archived (A17)
    assert {M: (v["D"], v["verdict"]) for M, v in r["per_chain"].items()} == {
        M: (v["D"], v["verdict"]) for M, v in pc.items()
    }
    t0, t1 = _job_span(doc)
    assert (hhmm(t0), hhmm(t1)) == ("01:16", "01:19")
    assert "(Kickoff 58; ibm_kingston, 15 October 2026, 01:16 to 01:19 UTC)" in item
    assert doc["meta"]["chains"] == reuse_doc(K56)["meta"]["chains"]
    assert {M: v["phi_star_deg"] for M, v in pc.items()} == {"7": 167, "43": 213, "18": 223}
    rule = (archive.data_dir() / "ibm_kingston" / "k58-rule.md").read_text()
    assert "This run is a placement comparison, not a pass-rate test." in rule
    assert "No result on them enters any pass rate of the check." in rule
    assert "not a pass-rate test: by its rule, no result on these chains enters any pass rate of the check." in item
    assert _posted(K58)[0::2] == (39, "01:00")
    for chain, M, v in (
        ("6-7-8", "7", "PEAK SMALLER"),
        ("42-43-44", "43", "PEAK SMALLER"),
        ("31-18-11", "18", "NOT SEPARATED"),
    ):
        c = pc[M]
        assert c["verdict"] == v
        line = (
            f"- **{chain}**, with {M} waiting: d1 {_q(c['cells']['peak']['d1'], 3, True)} at {c['phi_star_deg']}° and "
            f"{_q(c['cells']['plus90']['d1'], 3, True)} at +90°; D = {_q(c['D'], 3, True)} {_ci(c['D_ci90'])}: {v}."
        )
        assert line in item, line
    assert abs(k56_recomputed()["per_M"]["18"]["L_W_minus_R1"]["deg"]) < 0.05
    assert all(
        c["cells"]["peak"]["informative_R1"] and c["cells"]["peak"]["d1_margin"] == "inside" for c in pc.values()
    )
    assert [pc[M]["cells"]["plus90"]["d1_margin"] for M in ("7", "43")] == ["outside", "across"]
    assert not pc["18"]["cells"]["plus90"]["informative_R1"]
    c7 = pc["7"]["cells"]["plus90"]
    assert f"At +90° the cell on 7 lay entirely outside, {_q(c7['d1'], 3, True)} {_ci(c7['d1_ci90'])}." in item
    assert _q(next(c["d1"] for c in k55_recomputed()["cells"] if c["cell"] == "7|+90"), 3, True) == "+0.257"
    assert "at +90° in finding 20 (+0.257), at 60° and 120° in finding 22, and at +90° here" in item
    d0 = [_q(pc[M]["original_rule"]["D0"], 3, True) for M in ("7", "43", "18")]
    assert d0 == ["+0.256", "+0.168", "+0.125"] and all(pc[M]["original_rule"]["D0"] > pc[M]["D"] for M in pc)
    th = [_q(pc[M]["job1_fit"]["theta_R1_deg"], 1, True) for M in ("7", "43", "18")]
    th56 = [_q(k56_recomputed()["per_M"][M]["fits"]["R1"]["theta_deg"], 1, True) for M in ("7", "43", "18")]
    assert th == ["+13.4", "−33.2", "−42.8"] and th56 == ["+16.3", "−37.3", "−38.1"]
    assert all(abs(pc[M]["job1_fit"]["theta_minus_kickoff_56_deg"]) < 5 for M in pc)
    moved = [abs(pc[M]["phi_star_deg"] - pc[M]["job1_fit"]["kickoff_56_implied_peak_deg"]) for M in ("7", "43", "18")]
    assert moved == [3, 4, 5]
    gap = (_utc(t0) - _utc(reuse_doc(K56)["timestamps"]["running"])).total_seconds() / 60
    assert 70 < gap < 80
    assert (
        "Job 1's fits put θ_R1 at +13.4°, −33.2° and −42.8°, within 5° of finding 22's (+16.3°, −37.3° and −38.1°) "
        "about 75 minutes later" in item
    )
    assert "the peaks they imply moved by 3°, 4° and 5°" in item
    Ls = [abs(k56_recomputed()["per_M"][M]["L_W_minus_R1"]["deg"]) for M in ("7", "43", "18")]
    assert [round(x) for x in Ls] == [37, 12, 0]
    assert all(c["cells"]["peak"]["d1"] > 0 for c in pc.values())


def test_finding_25():
    """Amendment A24: finding 25 (Kickoff 59)."""
    from _reproduce import K59, k59_recomputed, reuse_doc

    item, doc, r = _item(25), reuse_doc(K59), k59_recomputed()
    a = doc["archived"]["analysis"]
    t0, t1 = _job_span(doc)
    assert (hhmm(t0), hhmm(t1)) == ("12:46", "13:08")
    assert "(Kickoff 59; ibm_kingston, 15 October 2026, 12:46 to 13:08 UTC)" in item
    w = {x["stamp_utc"]: x for x in doc["window"]["stamps"]}
    assert w["2026-10-15T07:37:10Z"]["q_T1"] == "151" and w["2026-10-15T12:08:57Z"]["cz_error"] == "171"
    assert "new T1 values on 151 qubits at 07:37:10 UTC and new CZ errors on 171 couplers at 12:08:57 UTC" in item
    d = doc["chain_draw"]
    assert (d["n_candidates"], d["n_survivors"], _shuffle_seed(d)) == (488, 192, 5959)
    assert list(d["n_excluded"].values()) == [130, 150, 16]
    assert (
        "Of 488 candidates, 130 used one of those qubits, 150 had a readout error above 3% and 16 a CZ error above "
        "1%, leaving 192" in item
    )
    chains = [x["chain"] for x in d["drawn"]]
    assert "`default_rng(5959)` gave 22-23-16, 136-143-144, 69-68-67 and 126-125-124" in item
    assert r["phi_star_deg"] == {"23": 231, "143": 214, "68": 18, "125": 143}
    assert (doc["run"]["1"]["calibration_at_submission_utc"], doc["run"]["2"]["calibration_at_submission_utc"]) == (
        "2026-10-15T12:08:57Z",
        "2026-10-15T12:50:45Z",
    )
    new = [
        x
        for x in doc["calibration_record"]["stamps"]
        if x["stamp_utc"] == "2026-10-15T12:50:45Z" and x["new_stamp"] == "True"
    ]
    assert new and new[0]["any_value_changed"] in ("False", "0", "")
    assert _posted(K59)[0::2] == (40, "11:46")
    assert r["H59"] == "AGREE" and all(line in item for line in _peak_lines(a, chains))
    assert _q(r["job1_fits"]["68"]["theta_R1_deg"], 1, True) == "+162.4"
    assert "On 69-68-67 the Ramsey's offset was +162.4°, so its peak fell at 18°, far from +90°" in item
    z = {M: v["P1_Z"] for M, v in r["zero_wait_baseline"].items()}
    assert max(z.values()) < 0.1 and _q(z["125"], 3) == "0.060" and max(z, key=z.get) == "125"
    p90 = a["check_at_plus90"]
    assert p90["verdict"] == "AGREE" and p90["informative_cells"] == ["143|+90", "68|+90", "125|+90"]
    assert (r["original_rule_at_phi_star"]["verdict"], p90["original_rule_verdict"]) == ("AGREE", "NOT SETTLED")
    lean = r["lean_phi_star"]
    below = [c for c in a["cells_phi_star"] if c["d1"] < 0]
    assert _q(lean["mean_d1"], 3, True) == "+0.014" and len(below) == 2
    assert [c["M"] for c in a["cells_phi_star"] if c["d1_ci90"][1] < 0] == ["125"]
    from _reproduce import k57_recomputed, k62_recomputed

    others = (k57_recomputed()["lean_phi_star"]["mean_d1"], k62_recomputed()["lean_phi_star"]["mean_d1"])
    assert [_q(x, 3, True) for x in others] == ["+0.049", "+0.051"] and lean["mean_d1"] < min(others)
    assert "The mean d1 at the peak was +0.014, with two cells below zero" in item
    m1 = np.mean([abs(c["d1"]) for c in a["cells_phi_star"]])
    m9 = np.mean([abs(c["d1"]) for c in p90["cells"]])
    smaller = sum(abs(c["d1"]) < abs(d_["d1"]) for c, d_ in zip(a["cells_phi_star"], p90["cells"]))
    assert (_q(m1, 3), _q(m9, 3), smaller) == ("0.021", "0.052", 3)
    assert (
        "|d1| was smaller at φ* than at +90° on three of the four chains, a mean of 0.021 against 0.052 over all four "
        "cells." in item
    )


def test_finding_26():
    """Amendment A24: finding 26 (Kickoff 61), with Kickoff 60's draw beside it."""
    from _reproduce import K61, k61_recomputed, reuse_doc

    item, doc, r = _item(26), reuse_doc(K61), k61_recomputed()
    k60 = archive.load("ibm_fez/k60-draw-stopped.json")
    d60 = k60["chain_draw"]
    assert (hhmm(d60["utc"]), d60["n_candidates"], d60["n_survivors"], d60["drawn"]) == ("14:01", 488, 0, [])
    assert d60["n_excluded"] == {"a readout error above 3%": 360, "uses a qubit of Kickoffs 47 to 54 on ibm_fez": 128}
    pub = [v["readout_error"]["value"] for v in k60["published_at_draw"]["qubits"].values()]
    assert (sum(x > 0.03 for x in pub), len(pub)) == (134, 156)
    assert k60["published_at_draw"]["last_update_date"] == "2026-10-15 09:39:11-04:00"
    assert (
        k60["meta"]["rule"]["posted"]["issue"] == 41 and hhmm(k60["meta"]["rule"]["posted"]["created_utc"]) == "13:45"
    )
    assert (
        "At that stamp, 13:39:11 UTC, 134 of fez's 156 qubits were published above 3%: of 488 candidate chains, 128 "
        "used a qubit of earlier runs on fez and the other 360 each had a qubit published above 3%." in item
    )
    t0, t1 = _job_span(doc)
    assert (hhmm(t0), hhmm(t1)) == ("14:45", "14:46")
    assert "(Kickoff 61; ibm_fez, 15 October 2026, 14:45 to 14:46 UTC)" in item
    assert len(doc["meta"]["qubits"]) == 16 and set(_shots(doc).values()) == {2000}
    rule, v1 = doc["meta"]["rule"], doc["meta"]["rule"]["superseded"]
    assert (rule["posted"]["issue"], hhmm(rule["posted"]["created_utc"])) == (43, "14:28")
    assert (v1["posted"]["issue"], hhmm(v1["posted"]["created_utc"]), v1["closed_utc"]) == (
        42,
        "14:17",
        "2026-10-15T14:28:53Z",
    )
    t_v1 = (archive.data_dir() / "ibm_fez" / "k61-rule-v1-superseded.md").read_text()
    t_v2 = (archive.data_dir() / "ibm_fez" / "k61-rule.md").read_text()
    assert "eighteen" in t_v1 and "eighteen" not in t_v2.split("version 1, which counted the qubits as eighteen", 1)[1]
    assert _utc(rule["posted"]["created_utc"]) < _utc(doc["meta"]["submitted_utc"])
    assert r["H61_by_stamp"] == {
        "at submission": "PUBLISHED NOT READABLE",
        "new stamp 2026-10-15T14:39:04Z": "PUBLISHED NOT READABLE",
    }
    s16 = {x["stamp_utc"]: x["readout_error_16"] for x in doc["calibration_record"]["stamps"]}
    assert s16["2026-10-15T14:22:27Z"] == s16["2026-10-15T14:39:04Z"]
    e = {q: v["e"] for q, v in r["per_qubit"].items()}
    assert (_q(min(e.values()), 3), _q(max(e.values()), 3)) == ("0.004", "0.021")
    c = r["comparisons"]["at submission"]
    inc = c["inconsistent"]
    ps = [c["per_qubit"][q]["p"] for q in inc]
    assert len(inc) == 13 and (_q(min(ps), 2), _q(max(ps), 2)) == ("0.03", "0.44")
    assert all(c["per_qubit"][q]["e_minus_p"] < 0 for q in inc)
    assert (_q(e["143"], 3), _q(c["per_qubit"]["143"]["p"], 3)) == ("0.009", "0.232")
    assert sorted(set(e) - set(inc), key=int) == ["74", "75", "116"]
    assert "- The measured e was 0.004 to 0.021 on all sixteen qubits." in item
    assert (
        "Qubit 143 measured 0.009 against a published 0.232." in item
        and "- Three were CONSISTENT: 74, 75 and 116." in item
    )
    b = doc["archived"]["analysis"]["beside"]
    assert b["all_e_below_0.05"]
    diffs = [v["alone_minus_together"] for v in b["alone_against_together"].values()]
    assert max(abs(x[k]) for x in diffs for k in ("P10", "P01")) <= 0.00405
    assert all(x[k + "_ci90"][0] <= 1e-12 and x[k + "_ci90"][1] >= -1e-12 for x in diffs for k in ("P10", "P01"))
    zs = [v["Z_P1"] for v in b["alone_against_together"].values()]
    assert (_q(min(zs), 4), _q(max(zs), 4)) == ("0.0008", "0.0065")
    assert "were at most 0.004 in size, and every one's interval contained zero or touched it" in item
    assert "The six zero-wait baselines were 0.0008 to 0.0065." in item
    cyc = doc["cycle"]
    assert (
        cyc["T1_stamps"]["stamps_utc"][-1] == "2026-10-15T09:16:30Z"
        and cyc["CZ_stamps"]["stamps_utc"][-1] == "2026-10-15T12:05:17Z"
    )
    assert "nothing about anyone's calibration. Manacitra does not rank machines." in item


def test_finding_27():
    """Amendment A24: finding 27 (Kickoff 62)."""
    from _reproduce import K62, k62_recomputed, reuse_doc

    item, doc, r = _item(27), reuse_doc(K62), k62_recomputed()
    a = doc["archived"]["analysis"]
    t0, t1 = _job_span(doc)
    assert (hhmm(t0), hhmm(t1)) == ("15:31", "15:38")
    assert "(Kickoff 62; ibm_fez, 15 October 2026, 15:31 to 15:38 UTC)" in item
    sv = r["survey_against_table"]
    s_ = sv["summary"]
    assert (s_["n_qubits"], _q(s_["e_median"], 4), _q(s_["p_median"], 3)) == (156, "0.0098", "0.166")
    assert (s_["n_measured_above_3pct"], s_["n_published_above_3pct"]) == (25, 135)
    gap = {q: v["published_readout_error"] - v["e"] for q, v in sv["per_qubit"].items()}
    assert (sum(x > 0.05 for x in gap.values()), sum(abs(x) <= 0.01 for x in gap.values())) == (105, 13)
    assert [q for q, x in gap.items() if x < -0.01] == ["72"]
    q72 = sv["per_qubit"]["72"]
    assert (_q(q72["e"], 3), _q(q72["published_readout_error"], 3)) == ("0.381", "0.357")
    assert (
        "It measured a median readout error of 0.0098 over the 156 qubits, against a published median of 0.166 at the "
        "stamp in force (14:39:04 UTC), and 25 qubits above 3% against 135 published." in item
    )
    assert (
        "on 105 qubits and lay within 0.01 of it on 13; the measured exceeded the published by more than 0.01 on one, "
        "qubit 72 (0.381 against 0.357)." in item
    )
    d = doc["chain_draw"]
    assert (
        d["each_exclusion_alone_over_all_candidates"][
            "a published readout error above 3% (for comparison; not applied)"
        ]
        == 488
    )
    assert (d["n_candidates"], d["n_survivors"], _shuffle_seed(d)) == (488, 156, 6260)
    assert sorted(d["n_excluded"].values()) == [36, 128, 168]
    chains = [x["chain"] for x in d["drawn"]]
    assert "The draw, once, with `default_rng(6260)`, took 35-19-15, 20-21-36, 109-110-111 and 99-95-94." in item
    assert r["phi_star_deg"] == {"19": 110, "21": 194, "110": 245, "95": 216}
    sh = _shots(doc)
    assert (sh[(0, "survey")], sh[(1, "sweep")], sh[(2, "verdict")], sh[(2, "beside")]) == (2000, 2000, 3000, 1500)
    assert {x["stamp_utc"] for x in doc["calibration_record"]["stamps"]} == {"2026-10-15T14:39:04Z"}
    assert _posted(K62)[0::2] == (44, "15:06")
    ic = doc["window"]["interval_condition"]
    assert ic["intervals_outside_range_h"]["T1_stamps"] == [30.491] and ic["range_h"] == [20.0, 30.0]
    assert doc["window"]["CZ_stamps"]["stamps_utc"][-1] == "2026-10-15T12:05:17Z"
    assert "the interval between ibm_fez's last two daily T1 stamps was 30.49 h, outside the 20 to 30 hours" in item
    assert r["H62"] == "AGREE" and all(line in item for line in _peak_lines(a, chains))
    p90 = a["check_at_plus90"]
    assert p90["verdict"] == "AGREE" and p90["informative_cells"] == ["19|+90", "21|+90", "95|+90"]
    assert (r["original_rule_at_phi_star"]["verdict"], p90["original_rule_verdict"]) == ("AGREE", "AGREE")
    assert r["lean_phi_star"]["n_d1_above_zero"] == 4 and _q(r["lean_phi_star"]["mean_d1"], 3, True) == "+0.051"
    rb = r["readout_beside"]
    alone = [v["alone_job2"]["mean_of_the_two"] for v in rb.values()]
    survey = [v["survey_job0"]["e"] for v in rb.values()]
    assert max(abs(x - y) for x, y in zip(alone, survey)) <= 0.003
    assert (_q(min(alone + survey), 3), _q(max(alone + survey), 3)) == ("0.007", "0.020")
    pub = [v["published_at_survey_submission"]["readout_error"] for v in rb.values()]
    assert (_q(min(pub), 3), _q(max(pub), 3)) == ("0.019", "0.500")
    assert rb["19"]["published_at_survey_submission"]["prob_meas0_prep1"] == pytest.approx(0.9985, abs=5e-5)
    assert (
        "lay within 0.003 of its survey value; both lay between 0.007 and 0.020, where the table published 0.019 to "
        "0.500" in item
    )
    pk, pl = a["cells_phi_star"], p90["cells"]
    smaller = [c["M"] for c, d_ in zip(pk, pl) if abs(c["d1"]) < abs(d_["d1"])]
    assert (
        smaller == ["21", "110"]
        and abs(abs(pk[0]["d1"]) - abs(pl[0]["d1"])) < 0.002
        and abs(pk[3]["d1"]) > abs(pl[3]["d1"])
    )
    m1, m9 = np.mean([abs(c["d1"]) for c in pk]), np.mean([abs(c["d1"]) for c in pl])
    assert (_q(m1, 3), _q(m9, 3)) == ("0.051", "0.058")
    assert "the mean |d1| was 0.051 at φ* against 0.058 at +90°." in item


def test_findings_22_to_27_beside_the_findings():
    """Amendment A24: what has not been shown, before and after; the method's subsection; the reproduce page's pointer;
    the kickoffs rows; the long documentation's row; the changelog's lead as the kickoff fixed it; the data README."""
    from _reproduce import k56_recomputed, k57_recomputed, k59_recomputed, k62_recomputed

    flat = " ".join((ROOT / "docs" / "findings.md").read_text().split())
    assert (
        "- **At the peak phase the ±0.15 margin held in the cases tested; at +90° it failed on one chain of one "
        "processor.** At the peak phase the check held on three runs on new chains, on two processors, on twelve cells "
        "of twelve (findings 23, 25 and 27)." in flat
    )
    assert "Three runs at the peak phase: two calibration days on ibm_kingston and one day on ibm_fez." in flat
    means = [k57_recomputed()["lean_phi_star"]["mean_d1"], k59_recomputed()["lean_phi_star"]["mean_d1"]]
    means.append(k62_recomputed()["lean_phi_star"]["mean_d1"])
    assert [_q(x, 3, True) for x in means] == ["+0.049", "+0.014", "+0.051"]
    assert (
        "a mean d1 of +0.049, +0.014 and +0.051 in findings 23, 25 and 27, with two cells of twelve below zero, both "
        "in finding 25" in flat
    )
    assert "A chain with a larger lean could fail the ±0.15 margin without any offset." in flat
    # the +90 degree check's cells that were not informative: findings 24, 25 and 27 (none in finding 23)
    from _reproduce import K57, K58, K59, K62, reuse_doc

    arch = {k: reuse_doc(k)["archived"]["analysis"] for k in (K57, K58, K59, K62)}
    assert [M for M, v in arch[K58]["per_chain"].items() if not v["cells"]["plus90"]["informative_R1"]] == ["18"]
    assert all(c["informative_R1"] for c in arch[K57]["check_at_plus90"]["cells"])
    for k in (K59, K62):
        assert any(not c["informative_R1"] for c in arch[k]["check_at_plus90"]["cells"])
    assert (
        "the check at +90° has landed cells that were not informative on both processors (findings 24, 25 and 27)"
        in flat
    )
    assert (
        "- **The published readout table was shown not to describe ibm_fez's readout at one time (findings 26 and "
        "27).**" in flat
    )
    assert (
        "- **A static shift per neighbour pair is consistent with the data and was not tested as a mechanism** "
        "(finding 21's additivity and symmetry)." in flat
    )
    assert "- **It has not been tested as a chooser.**" in flat
    # the method's subsection
    method = " ".join((ROOT / "docs" / "method.md").read_text().split())
    assert (
        "### The check at the peak phase" in method
        and "informative by construction, a property of the design" in method
    )
    L = k56_recomputed()["per_M"]
    assert (_q(L["7"]["L_W_minus_R1"]["deg"], 1, True), abs(L["18"]["L_W_minus_R1"]["deg"]) < 0.05) == ("−36.7", True)
    assert "was −36.7° on one ibm_kingston qubit and 0.0° on another" in method
    assert "One shot count per job: qiskit-ibm-runtime 0.49.0 deprecates different shot counts" in method
    # the reproduce page, the kickoffs table and the long documentation
    page = " ".join((ROOT / "docs" / "reproduce.md").read_text().split())
    assert "All seven built their code at `e45f15d`, unedited" in page
    kick = (ROOT / "docs" / "kickoffs.md").read_text()
    for k in range(56, 63):
        assert f"| {k}, " in kick, k
    index = " ".join((ROOT / "docs" / "index.md").read_text().split())
    assert (
        "`k56_phase_sweep`, `k57_peak_check`, `k58_placement`, `k59_peak_check_day_two`, `k61_readout`, "
        "`k62_peak_check_fez`" in index
    )
    # the changelog's lead, as fixed by the kickoff
    log = " ".join((ROOT / "CHANGELOG.md").read_text().split())
    assert log.index("## 0.7.0 (15 October 2026)") < log.index("## 0.6.0 (15 October 2026)")
    assert "(unreleased)" not in log.split("## 0.7.0 (15 October 2026)", 1)[1] and "## Unreleased" not in log
    # the release pull request dated it; A25: 0.8.0's heading waits for its date
    assert (
        "## 0.7.0 (15 October 2026) The check can now be placed at the active-neighbour Ramsey's loss maximum: "
        "a six-phase "
        "sweep fixes each chain's peak phase, and the check runs there, where every cell is informative by "
        "construction. "
        "`manacitra.wait` gains the sweep, the fit, the peak phase and a readout survey with a per-qubit readout "
        "error from "
        "measured counts; the 0.6.0 check at +90° is unchanged. Findings 22 to 27, from four runs on ibm_kingston on "
        "14 "
        "and 15 October 2026 and two on ibm_fez on 15 October, with their data, and the record of a draw on ibm_fez "
        "that "
        "found no chain on the published readout table. At the peak phase the check predicted the wait test within "
        "±0.15 "
        "on twelve of twelve cells over three runs on new chains on two processors (findings 23, 25 and 27). On "
        "ibm_fez "
        "a direct measurement found readout errors of 0.004 to 0.021 on sixteen qubits the published table put at up "
        "to "
        "0.44, and a survey of all 156 qubits a median of 0.0098 against a published 0.166 (findings 26 and 27)." in log
    )


def test_the_a24_rules_are_published_unchanged():
    """Amendment A24, 2b: the eight rule files of Kickoffs 56 to 62 are in data/ byte for byte, each with the SHA-256
    posted publicly before its run, and each run's record names its rule, its hash and the issue it was posted in,
    before the job was submitted (Kickoff 60, which stopped at its draw, before the draw). Kickoff 61's record names its
    superseded version 1 and the issue that posted it, closed with a comment before version 2's run."""
    import hashlib

    posted = {
        ("ibm_kingston", "k56-rule.md"): ("9b859965f419a0d0d2c613fccf98052d0e6df91d35161a509bdd0c4d02fae333", 37),
        ("ibm_kingston", "k57-rule.md"): ("61207896b00e090a78df047c5f218363d7370a80b8d6809be726184a7092bb57", 38),
        ("ibm_kingston", "k58-rule.md"): ("988d611a3eca79da02ffdbfc36c9c604b8bd452bb9037ff5f1d76def3c88502b", 39),
        ("ibm_kingston", "k59-rule.md"): ("99db7f4bbcfe9224581bf90ea0dd4726fe68e965cb2d419c1cd39279c0b72bc0", 40),
        ("ibm_fez", "k60-rule.md"): ("e701f30537e2cee8552c67f94bc1419238c3e418725d8de40ab714050c30780c", 41),
        ("ibm_fez", "k61-rule-v1-superseded.md"): (
            "cb1375a1ba901d04c85dc465eb035dde400d8c598d1f64e04d9ae67feee472a2",
            42,
        ),
        ("ibm_fez", "k61-rule.md"): ("0a8a4242907a2c3607e7d729ecf504cfadcf296059ce9953c134d95ca551018b", 43),
        ("ibm_fez", "k62-rule.md"): ("ec13ffaf7b239d6e5f74ba4cda1eed33b5f84cee3e8e96b05c25b8f47aa19778", 44),
    }
    for (folder, name), (sha, _) in posted.items():
        text = (archive.data_dir() / folder / name).read_bytes()
        assert hashlib.sha256(text).hexdigest() == sha, name
        assert b"The rule is not changed after the data, whatever they show." in text, name
    records = {
        "ibm_kingston/k56-phase-sweep.json": "k56-rule.md",
        "ibm_kingston/k57-peak-check.json": "k57-rule.md",
        "ibm_kingston/k58-placement-comparison.json": "k58-rule.md",
        "ibm_kingston/k59-peak-check-day-2.json": "k59-rule.md",
        "ibm_fez/k60-draw-stopped.json": "k60-rule.md",
        "ibm_fez/k61-readout-check.json": "k61-rule.md",
        "ibm_fez/k62-peak-check.json": "k62-rule.md",
    }
    for path, name in records.items():
        doc = archive.load(path)
        r_ = doc["meta"]["rule"]
        sha, issue = posted[(path.split("/")[0], name)]
        assert (r_["file"], r_["sha256"], r_["posted"]["issue"]) == (name, sha, issue), path
        assert r_["posted"]["url"] == f"https://github.com/dogma-guru/manacitra/issues/{issue}"
        sub = doc["meta"].get("submitted_utc") or doc["chain_draw"]["utc"]
        first = min(sub.values()) if isinstance(sub, dict) else sub
        assert _utc(r_["posted"]["created_utc"]) < _utc(first), path
    v1 = archive.load("ibm_fez/k61-readout-check.json")["meta"]["rule"]["superseded"]
    assert (v1["file"], v1["sha256"], v1["posted"]["issue"]) == (
        "k61-rule-v1-superseded.md",
        posted[("ibm_fez", "k61-rule-v1-superseded.md")][0],
        42,
    )
    assert _utc(v1["posted"]["created_utc"]) < _utc(v1["closed_utc"])


def test_the_leftover_picture():
    """A24: finding 22's picture, made from the data by docs/make_diagrams.py and referenced from finding 22; its alt
    text and its own text carry the fitted offsets and the leftover of the data."""
    from _reproduce import K56, k56_recomputed, reuse_doc

    findings = (ROOT / "docs" / "findings.md").read_text()
    item = findings.split('<a id="finding-22"></a>', 1)[1].split("<a id=", 1)[0]
    assert "](diagrams/leftover-sweep.svg)" in item and (DIAGRAMS / "leftover-sweep.png").is_file()
    alt = " ".join(item.split("![", 1)[1].split("](diagrams/leftover-sweep.svg)", 1)[0].split())
    p = k56_recomputed()["per_M"]["7"]
    th = {c: _q(p["fits"][c]["theta_deg"], 1, True) for c in ("W", "R1")}
    # the interval as archived, as the figure draws it: a fitted angle's interval moves with a platform's random
    # stream (A17), and tests/excluded_fields.json names it with its measured movement
    arch = reuse_doc(K56)["archived"]["analysis"]["per_M"]["7"]["L_W_minus_R1"]
    L, ci = _q(p["L_W_minus_R1"]["deg"], 1, True), [_q(x, 1, True) for x in arch["ci90"]]
    assert (th["W"], th["R1"], L, ci) == ("−20.4", "+16.3", "−36.7", ["−39.1", "−34.2"])
    assert f"the wait test's offset θ_W is {th['W']}° and the Ramsey's offset θ_R1 is {th['R1']}°" in alt
    assert f"The leftover, L = θ_W − θ_R1, is {L}°, with a 90% interval of {ci[0]}° to {ci[1]}°" in alt
    text = svg_text(DIAGRAMS / "leftover-sweep.svg")
    assert "θ_W = −20.4°" in text and "θ_R1 = +16.3°" in text and "L = θ_W − θ_R1 = −36.7°" in text
    assert "−39.1° to −34.2°: LARGE" in text and "ibm_kingston, Kickoff 56, 14 to 15 October 2026, one job." in text


# --------------------------------------------------------------------------- finding 28 (Amendment A25)
def _t7():
    from _reproduce import T7, reuse_doc, t7_recomputed

    doc = reuse_doc(T7)
    an, _, rd = t7_recomputed()
    return doc, an, rd, " ".join(_item(28).split())


def _minute(stamp: str) -> str:
    t = datetime.fromisoformat(stamp.replace("Z", "+00:00")) + timedelta(seconds=30)
    return t.strftime("%H:%M")


def test_finding_28():
    """Finding 28 (test 7): its headline and design, the rule with its posted hash, the desk power check, the verdict's
    three clauses with their margins, the two lines, the centre, the split, the weight and the envelope, each number
    recomputed from the counts (points) or read from the archive (interval ends, A17), and each quoted only where its
    rounding is not an exact half case."""
    doc, an, rd, item = _t7()
    a = doc["archived"]["analysis"]
    ts = doc["timestamps"]
    assert (_minute(ts["running"]), _minute(ts["finished"])) == ("21:31", "21:34")
    assert item.startswith(
        "**On ibm_fez, qubit 143's Ramsey fringe over 0 to 63 µs was two fixed frequencies about 90 kHz apart at "
        "unequal weight, not one line decaying** (test 7; ibm_fez, 16 October 2026, 21:31 to 21:34 UTC)."
    )
    arch = a["beside"]["5_detuning_and_T2"]["archive_kHz"]
    assert arch == {"2026-10-11": [47.1, 1.8], "2026-10-13": [40.4, 3.2]}
    assert "47.1 ± 1.8 kHz on 11 October (finding 14) and 40.4 ± 3.2 kHz on 13 October (finding 15)" in item
    assert "a fit, labelled as a fit, gives 40.4 ± 3.2 kHz, against finding 14's 47.1 ± 1.8 kHz" in " ".join(
        _item(15).split()
    )
    # the design
    labels = doc["labels"]
    assert len(labels) == 260 and set(doc["shots"]) == {1500} and doc["meta"]["copies"] == 2
    assert len({(lab["circuit"], lab["t_requested_us"]) for lab in labels}) == 130
    assert doc["meta"]["built_from"]["commit"].startswith("b782d00") and doc["meta"]["built_from"]["tag"] == "v0.7.0"
    assert doc["job_options_as_recorded_by_ibm"] == {
        "dynamical_decoupling": {"enable": False},
        "twirling": {"enable_gates": False, "enable_measure": False},
    }
    assert "Dynamical decoupling, gate twirling and measurement twirling were off, as IBM recorded them" in item
    assert a["beside"]["8_scheduled_waits"]["all_equal_to_requested"] is True
    stamps = {r_["stamp_utc"] for r_ in doc["calibration_record"]["stamps"]}
    walk = doc["calibration_record"]["walk_over_the_job"]
    assert stamps == {"2026-10-16T20:59:56Z"} and walk["walk_distinct_stamps"] == ["2026-10-16T20:59:56Z"]
    assert "Every requested wait was scheduled exactly." in item
    assert (
        "One calibration stamp, 20:59:56 UTC, was in force at the build, the submission, every poll and the read"
        in item
    )
    # the rule and the desk power check
    posted = doc["meta"]["rule"]["posted"]
    assert (posted["issue"], posted["created_utc"][11:16]) == (50, "21:00")
    assert (
        "([issue 50](https://github.com/dogma-guru/manacitra/issues/50), 21:00 UTC; `data/ibm_fez/t7-rule.md`)" in item
    )
    import json

    keep = json.loads((archive.data_dir() / "desk" / "t7-power-check" / "keep-t7v51.json").read_text())
    pts = keep["per_point"]
    counted = [x for x in pts if x["counted"]]
    passing = [x for x in counted if x["fraction_generating_verdict"] >= 0.8]
    assert (len(pts), len(counted), len(passing), keep["keep"]["needed"]) == (135, 117, 106, 88)
    assert {x["n_draws"] for x in pts} == {200} and keep["keep"]["verdict"] == "KEPT"
    failing = [x for x in counted if x not in passing]
    assert len(failing) == 11
    assert {(x["delta_kHz"], x["tau_us"]) for x in failing} == {(8, 15), (11, 15), (3, 150)}
    assert (
        "On a grid of 135 simulated qubits, with 200 noisy draws at each, the rule returned the generating verdict in "
        "at least 80% of draws at 106 of 117 counted points, where 88 were needed: the design was kept." in item
    )
    assert "splits of 8 to 11 kHz on a 15 µs decay" in item and "3 kHz splits on a 150 µs decay" in item
    assert "Five earlier versions of the design preceded the rule and are recorded elsewhere" in item
    # the verdict and its clauses
    d = an["deciding"]
    assert an["verdict"] == a["verdict"] == "TWO FIXED FREQUENCIES"
    assert all(
        d["clauses"][k]
        for k in ("P_smaller_than_S_by_more_than_0.01", "delta_lower_bound_above_5_kHz", "b_interval_inside_0.05_0.95")
    )
    s_, p_, m_ = _q(d["held_out_error_S"], 4), _q(d["held_out_error_P"], 4), _q(-d["P_minus_S"], 4)
    assert (s_, p_, m_) == ("0.0733", "0.0200", "0.0533")
    assert (
        f"**The held-out error:** {s_} for S and {p_} for P, so P is smaller by {m_}, against a margin of 0.01." in item
    )
    P, S = an["fits"]["P"]["params"], an["fits"]["S"]["params"]
    dlo, dhi = a["deciding"]["delta_ci90_kHz"]
    blo, bhi = a["deciding"]["b_ci90"]
    dl = _q(P["delta_MHz"] * 1e3, 2)
    assert (dl, _q(dlo, 2), _q(dhi, 2)) == ("44.82", "44.72", "44.92")
    assert (
        f"**The split:** δ {dl} kHz, 90% interval {_q(dlo, 2)} to {_q(dhi, 2)} kHz, its lower bound above 5 kHz."
        in item
    )
    assert (_q(P["b"], 3), _q(blo, 3), _q(bhi, 3)) == ("0.355", "0.333", "0.377")
    assert "**The weight:** b 0.355, 90% interval 0.333 to 0.377, inside (0.05, 0.95)." in item
    # the lines, the centre, the envelope and S
    up, lo_ = (P["Delta0_MHz"] + P["delta_MHz"]) * 1e3, (P["Delta0_MHz"] - P["delta_MHz"]) * 1e3
    draws = np.array(doc["archived"]["bootstrap"]["draws"]["P"], float)  # interval ends from the archive (A17)
    assert doc["archived"]["bootstrap"]["meta"]["seed"] == 7304 and draws.shape == (2000, 7)
    d0_lo, d0_hi = (float(v) for v in np.percentile(draws[:, 3] * 1e3, [5, 95]))
    t_lo, t_hi = (float(v) for v in np.percentile(draws[:, 2], [5, 95]))
    assert (_q(up, 1), _q(lo_, 1), _q(1 - P["b"], 3)) == ("93.5", "3.8", "0.645")
    assert (_q(P["Delta0_MHz"] * 1e3, 1), _q(d0_lo, 1), _q(d0_hi, 1)) == ("48.7", "48.4", "48.9")
    assert (f"{P['tau_prime_us']:.0f}", f"{t_lo:.0f}", f"{t_hi:.0f}") == ("128", "117", "141")
    assert (
        "P's two lines sit at 93.5 kHz, with the weight 0.355, and at 3.8 kHz, with 0.645, about a centre Δ0 of 48.7 "
        "kHz (48.4 to 48.9), under one envelope of 128 µs (τ′, 117 to 141 µs)." in item
    )
    assert (_q(S["Delta_MHz"] * 1e3, 1), _q(S["tau_us"], 1), _q(S["c"], 3)) == ("94.0", "40.1", "0.317")
    assert (_q(P["c"], 3), _q(P["A"], 3)) == ("0.490", "0.487")
    assert (
        "S put its one line at 94.0 kHz with a decay of 40.1 µs and its centre at 0.317, following the upper line; P "
        "put the fringe's centre at 0.490 and its amplitude at 0.487." in item
    )


def test_finding_28_beside_the_verdict():
    """Finding 28's paragraph beside the verdict, in the rule's order, and the readings after the data: the telegraph
    diagnostic, the weight, the nodes and the wait test's own wait, the reading recorded before the data and the
    envelope's minima and maxima, the centre beside the archive, T2, the periodogram and the sideband check, the
    readout; the copies, the weight in execution order, the second half and the three consequences; and what it does
    not say."""
    doc, an, rd, item = _t7()
    a = doc["archived"]["analysis"]
    T = a["beside"]["1_telegraph_T"]
    assert T["gamma_per_us"] < 1e-15 and T["gamma_ci90_per_s"][1] < 3e-9 and _q(T["held_out_error"], 4) == "0.0306"
    assert f"{T['gamma_ci90_per_s'][1]:.1e}" == "2.5e-09"
    assert (
        "fitted no better (held-out error 0.0306) and put γ at zero, its lower bound (90% interval 0 to 2.5·10⁻⁹ "
        in item
    )
    rates = [v for pair in T["published_rates_per_s"].values() for v in pair]
    assert (min(rates), max(rates), round(1 / 63e-6, -3)) == (0.004, 1300, 16000)
    assert "from 0.004 to 1,300 per second, all read as zero over a 63 µs wait" in item
    assert "a rate far below 1/(63 µs), about 16,000 per second, cannot show there" in item
    assert (
        "The design separates switching within a shot from a mixture across shots, and it found no switching within"
        in item
    )
    assert a["beside"]["2_weight"]["ci_contains_0.5"] is False and "b's interval excludes equal weights (0.5)." in item
    nodes = [x["t_us"] for x in a["beside"]["3_beat_nodes"]["nodes"]]
    assert [_q(x, 1) for x in nodes] == ["5.6", "16.7", "27.9"]
    rev = 1 / (2 * an["fits"]["P"]["params"]["delta_MHz"])
    assert (_q(rev, 1), _q(rev - 10.45, 1)) == ("11.2", "0.7")
    assert (
        "P's first three nodes fall at 5.6, 16.7 and 27.9 µs, and the wait test's own wait on 143, 10.45 µs, lies 0.7"
        in item
    )
    assert a["beside"]["4_reading_23p7_kHz"]["reading"] == "neither"
    assert 'The fringe returned neither its pattern nor its disconfirmer (the fixed test reads "neither")' in item
    D = rd["D_envelope_recentred_on_P_c"]
    mins, maxs = [round(x) for x in D["local_minima_us"][:5]], [round(x) for x in D["local_maxima_us"][:5]]
    assert (mins, maxs) == ([5, 16, 28, 39, 50], [11, 22, 33, 44, 55])
    assert "the envelope's minima fall at 5, 16, 28, 39 and 50 µs and its maxima at 11, 22, 33, 44 and 55 µs" in item
    assert "whether 143's loss at that wait on 11 to 15 October was a beat feature is not tested by this job." in item
    t2 = a["beside"]["5_detuning_and_T2"]["published_at_submission"]["q143_T2_us"]
    assert (f"{t2:.0f}", f"{an['fits']['P']['params']['tau_prime_us']:.0f}") == ("235", "128")
    assert "IBM's published T2 for 143 at the stamp was 235 µs, beside the fitted envelope's 128 µs" in item
    assert "they are not the same quantity" in item
    six = a["beside"]["6_more_than_two"]
    assert (
        six["periodogram"]["reading"] == "MORE THAN TWO" and six["sideband_check"]["reading"] == "NO SIDEBAND RESOLVED"
    )
    ro = a["beside"]["7_readout"]
    assert (_q(ro["e"], 4), _q(ro["e_se"], 4), _q(ro["published_at_submission"]["q143_readout_error"], 4)) == (
        "0.0045",
        "0.0009",
        "0.0070",
    )
    assert "its readout error was 0.0045 (±0.0009), beside the published 0.0070." in item
    # what the counts show, which the rule did not assume
    A = rd["A_copy_agreement"]
    assert (_q(A["ramsey"]["sum_z2"], 1), A["ramsey"]["n"], A["ramsey"]["n_abs_z_over_3"]) == ("871.7", 128, 27)
    assert (_q(A["readout"]["sum_z2"], 2), A["readout"]["n"]) == ("0.95", 2)
    assert (
        "the sum of z² over the 128 circuits was 871.7, on 128 degrees of freedom, with 27 circuits beyond |z| = 3"
        in item
    )
    B = rd["B_weight_in_execution_order"]
    blocks = [b["weighted_mean"] for b in B["blocks_of_26"]]
    assert (_q(blocks[0], 3), _q(blocks[-1], 3), _q(min(blocks), 2), _q(max(blocks), 2)) == (
        "0.452",
        "0.269",
        "0.27",
        "0.46",
    )
    step = [r_["k"] for r_ in B["positions"]]
    high = [r_["k"] for r_ in B["positions"] if r_["b_pos"] > 0.4]
    assert max(high) == 98 and min(k for k in step if k > 98) == 101
    assert (
        "The ten blocks of 26 positions, in the order the circuits were submitted, read 0.452 in the first and 0.269 "
        in item
    )
    half = rd["C_P_on_each_half_of_the_run"]["second half (positions 130 to 259)"]["P"]
    assert (_q(half["delta_kHz"], 2), _q(half["b"], 3)) == ("44.76", "0.276")
    assert "gave the same split (δ 44.76 kHz) at b = 0.276" in item
    assert all(0.05 < b < 0.95 for b in blocks)
    for line in (
        "- **The intervals describe the job's average.**",
        "- **The verdict's clauses hold at every block's weight.**",
        "- **The periodogram's MORE THAN TWO cannot be told from the movement.**",
    ):
        assert line in _item(28), line
    assert "**What the counts show, which the rule did not assume** (readings after the data)." in item
    # what the finding does not say
    low = item.lower()
    for word in ("parit", "charge", "unusual", "ticket", "steady", "predicts better", "switching rate of"):
        assert word not in low, word
    assert "It names no cause for either line, for the split or for the movement of the weight." in item
    assert "Manacitra does not rank machines." in item


def test_finding_28_beside_the_finding():
    """A25, 2d and 2e: the three bullets added to what has not been shown, the README's row and limit line, the method
    subsection, the reproduce pointer, the kickoffs row, the long documentation's row, the data index and the
    changelog's lead as the kickoff fixed it."""
    flat = " ".join((ROOT / "docs" / "findings.md").read_text().split())
    for bullet in (
        "- **Finding 28 names no cause.** A Ramsey fringe shows two frequencies; it does not say what makes them. The "
        "design rules out switching between them within one shot and says nothing about how the mixture is made across "
        "shots.",
        "- **The intervals of finding 28 are a job average.** The rule's bootstrap treats the job as one stationary "
        "process; the job was executed as three spans, and the weight differed between them by more than its interval "
        "spans, read again under finding 29, part (d). The next rule carries the copies' agreement as a pre-fixed "
        "diagnostic.",  # A26; A27, R2 (question 9)
        "- **Finding 28 does not say what happens between execution spans.** The execution record says where the "
        "weight changed, read again under finding 29, part (d); it does not say why, and the repository has not tested "
        "either candidate.",  # A26; A27, R2 (question 9)
        "- **One qubit, one job, one day.** Nothing about 143 on another day, or about any other qubit, or about the "
        "loss at the wait test's own wait on the days of findings 13 to 18 and 21.",  # R1, Q4
    ):
        assert bullet in flat, bullet[:40]
    assert "- **It has not been tested as a chooser.**" in flat and "- **The physical origin of 143's offset.**" in flat
    assert (
        "and what would cause either was not measured. Finding 28 separates two lines present at once from one line, "
        "and rules out switching between them within a shot; it does not separate slow switching between shots from a "
        "fixed mixture, and names no cause." in flat
    )  # R1: the dated bullet amended
    readme = " ".join((ROOT / "README.md").read_text().split())
    assert (
        "| The fringe on 143: one line or two | [28](docs/findings.md#finding-28) | ibm_fez | Measured at every wait "
        "from 0 to 63 µs in two quadratures, 143's Ramsey fringe was two fixed frequencies about 90 kHz apart at "
        "unequal weight, not one line decaying; the weight differed between the job's execution spans. | TWO FIXED "
        "FREQUENCIES |" in readme  # A26 R1, Q6
    )
    method = " ".join((ROOT / "docs" / "method.md").read_text().split())
    assert "### The two-quadrature Ramsey and the two-model fit" in (ROOT / "docs" / "method.md").read_text()
    for name in ("`manacitra.wait.ramsey_xy`", "`ramsey_xy_fit`", "`ramsey_xy_band`", "`copies_check`"):
        assert name in method, name
    assert "a line at f and one at f + 500 kHz are the same function at every fitted wait" in method
    for word in ("TWO FIXED FREQUENCIES", "NO RESOLVED SPLIT", "NOT SETTLED"):
        assert word not in method.split("### The two-quadrature Ramsey", 1)[1], word
    page = " ".join((ROOT / "docs" / "reproduce.md").read_text().split())
    assert "with its circuits built unedited at `b782d00`, the commit of v0.7.0" in page
    assert "python -B analyse_t7.py --counts results-t7-counts.json --stamps stamps-t7.csv" in page
    assert "python power_t7v51.py fitcheck" in page
    kick = (ROOT / "docs" / "kickoffs.md").read_text()
    assert "| test 7, 16 October 2026 | Is qubit 143's Ramsey fringe over 0 to 63 µs one line" in kick
    assert "| ibm_fez | TWO FIXED FREQUENCIES. No predictions were sealed for this run. |" in kick  # R1, Q14
    index = " ".join((ROOT / "docs" / "index.md").read_text().split())
    assert "| ibm_fez, test 7: the two-quadrature Ramsey on 143, TWO FIXED FREQUENCIES" in index
    data = " ".join((archive.data_dir() / "README.md").read_text().split())
    assert "| `ibm_fez/t7-ramsey-xy.json` |" in data and "**Recomputing test 7** (finding 28)" in data
    log = " ".join((ROOT / "CHANGELOG.md").read_text().split())
    assert log.index("## 0.8.0 (17 October 2026)") < log.index("## 0.7.0 (15 October 2026)")
    assert "## 0.8.0 (unreleased)" not in log and "## Unreleased" not in log  # the release pull request dated it
    assert (
        "## 0.8.0 (17 October 2026) The qubit that waited in the circuits of findings 13 to 18 and 21, ibm_fez's 143, "
        "was "
        "measured at every wait from 0 to 63 µs in two quadratures under a rule fixed and hashed before the job. Its "
        "Ramsey fringe is two fixed "
        "frequencies about 90 kHz apart at unequal weight, not one line decaying: the two-line model's held-out error "
        "was a quarter of the one-line model's, the split 44.8 kHz, the upper line's weight 0.36 averaged over the "
        "job. The weight differed between the job's three execution spans, from about 0.46 to 0.27, which the rule did "
        "not assume and finding 28 reports as what the counts show. No cause is named. `manacitra.wait` gains the "
        "two-quadrature Ramsey, the one-line and two-line fit with a held-out error and a bootstrap, and a copies "
        "check; the rule's thresholds are the caller's. The desk power check that preceded the rule is published "
        "beside the data." in log
    )


def test_the_two_lines_picture():
    """Finding 28's picture: made from the data by docs/make_diagrams.py, referenced from finding 28, and its alt text
    and header carry the verdict and the numbers that decide it."""
    doc, an, _, _ = _t7()
    findings = (ROOT / "docs" / "findings.md").read_text()
    raw = findings.split('<a id="finding-28"></a>', 1)[1].split("<a id=", 1)[0]
    assert "](diagrams/two-lines-143.svg)" in raw and (DIAGRAMS / "two-lines-143.png").is_file()
    alt = " ".join(raw.split("![", 1)[1].split("](diagrams/two-lines-143.svg)", 1)[0].split())
    nodes = [m / (4 * an["fits"]["P"]["params"]["delta_MHz"]) for m in (1, 3, 5, 7, 9, 11)]
    assert ", ".join(_q(x, 1) for x in nodes) == "5.6, 16.7, 27.9, 39.0, 50.2, 61.4"
    assert "at the odd multiples of 1/(4δ), 5.6, 16.7, 27.9, 39.0, 50.2 and 61.4 µs" in alt
    assert (
        "TWO FIXED FREQUENCIES, held-out error 0.0733 (S) against 0.0200 (P), δ 44.82 kHz (44.72 to 44.92), b 0.355 "
        "(0.333 to 0.377)." in alt
    )
    text = svg_text(DIAGRAMS / "two-lines-143.svg")
    assert "TWO FIXED FREQUENCIES" in text and "ibm_fez, test 7, 16 October 2026, one job" in text
    assert "the wait test's own wait, 10.45 µs" in text


def test_the_t7_rule_is_published_unchanged():
    """A25, 2b: test 7's rule is in data/ byte for byte, with the SHA-256 posted publicly before its run (issue 50), and
    its record names the rule, its hash and the issue, posted before the job was submitted."""
    import hashlib

    sha = "350fe947ac9ff97749743951a2b05b402533dc2c5bffcfd0f1fa00faeae43c86"
    text = (archive.data_dir() / "ibm_fez" / "t7-rule.md").read_bytes()
    assert hashlib.sha256(text).hexdigest() == sha
    assert b"The rule is not changed after the data, whatever they show." in text
    m = archive.load("ibm_fez/t7-ramsey-xy.json")["meta"]
    assert m["rule"]["file"] == "t7-rule.md" and m["rule"]["sha256"] == sha
    assert m["rule"]["posted"] == {
        "issue": 50,
        "url": "https://github.com/dogma-guru/manacitra/issues/50",
        "created_utc": "2026-10-16T21:00:21Z",
    }
    assert m["rule"]["posted"]["created_utc"] < m["submitted_utc"] == "2026-10-16T21:23:19Z"


def test_the_power_check_folder():
    """A25, 2a: the desk power check beside the data: every file the folder's README lists has the SHA-256 it gives;
    the two scripts changed from the copies handed back differ from them only in their docstring's first line, as the
    README says; pretest_t7.py's SHA256SUMS holds the published copy's; and the release asset's SHA-256 is given."""
    import hashlib
    import re

    root = archive.data_dir() / "desk"
    readme = (root / "t7-power-check" / "README.md").read_text()
    rows = re.findall(r"^\| `([^`]+)` \| [^|]+ \| `([0-9a-f]{64})` \|$", readme, re.M)
    assert len(rows) == 10  # R1, Q8: the grid's run record
    for name, sha in rows:
        assert hashlib.sha256((root / "t7-power-check" / name).read_bytes()).hexdigest() == sha, name
    # the signing workflow's bundles (FILE.sigstore.json) sit beside the files on main, and are not the folder's files
    names = {p.name for p in (root / "t7-power-check").iterdir() if not archive.is_bundle(p)}
    names |= {f"../t7/{p.name}" for p in (root / "t7").iterdir() if not archive.is_bundle(p)}
    assert names == {n for n, _ in rows} | {"README.md", "../t7/SHA256SUMS"}
    pre = hashlib.sha256((root / "t7" / "pretest_t7.py").read_bytes()).hexdigest()
    assert (root / "t7" / "SHA256SUMS").read_text() == f"{pre}  pretest_t7.py\n"
    assert "`27c29bc2c242312ff9b2ab3b22c987263aa2900ebdcf966c24e0fcc1369b1a48`" in readme
    assert "\"DRAFT\" in the version 5.1 kickoff's name is the author's working label" in readme  # R1, Q9
    for name in ("t7-power-check/power_t7v51.py", "t7/pretest_t7.py"):
        first = (root / name).read_text().splitlines()[0]
        assert first.startswith('"""Test 7, ') and "tr" + "ace" not in (root / name).read_text().lower()


def test_finding_28_execution_spans():
    """A26: finding 28's reading of the weight per execution span, from the provider's span record (spans-t7.json) and
    the readings against it (t7-span-readings.json): the spans' positions and UTC times as the record gives them and the
    gaps between them, the weight per span with its counts, the step's neighbours on either side of the first boundary,
    the blocks that hold the boundaries, the copies check split by span, the labelled reading with its two candidates,
    and the method, reproduce and changelog lines. No sentence gives the weight's change a duration or a rate."""
    from _reproduce import T7_SPAN_READINGS, T7_SPANS, reuse_doc, t7_spans_recomputed

    derived, readings = t7_spans_recomputed()
    rec = reuse_doc(T7_SPANS)
    item = " ".join(_item(28).split())
    runs = [s_["position_runs"] for s_ in derived["spans"]]
    assert runs == [[[0, 99]], [[100, 199]], [[200, 259]]] and derived["spans_in_start_order"] == [0, 1, 2]
    times = [(s_["start_utc"][11:23], s_["stop_utc"][11:23]) for s_ in rec["spans"]]
    assert times == [
        ("21:31:39.632", "21:32:24.294"),
        ("21:32:24.300", "21:33:08.742"),
        ("21:33:08.748", "21:33:35.820"),
    ]
    stops = [round(float(s_["stop_utc"][17:]), 3) for s_ in rec["spans"]]
    assert stops == [24.294, 8.743, 35.82]  # the stops to the millisecond, rounded (08.742811 reads 08.743)
    assert (
        "0 to 99 (21:31:39.632 to 21:32:24.294 UTC), 100 to 199 (21:32:24.300 to 21:33:08.743 UTC) and 200 to 259 "
        "(21:33:08.748 to 21:33:35.820 UTC), with gaps of 6 ms and 5 ms between them." in item
    )
    gaps = [g["gap_s"] * 1e3 for g in derived["gaps"]]
    assert [f"{g:.0f}" for g in gaps] == ["6", "5"]
    assert derived["every_position_in_exactly_one_span_with_all_its_shots"] is True
    assert rec["read_utc"].startswith("2026-10-17") and "retrieved again, read-only, on 17 October" in item
    w = readings["weight_per_span"]
    assert [_q(x["weighted_mean"], 3) for x in w] == ["0.457", "0.315", "0.274"]
    assert [x["n_positions_passing_the_lever"] for x in w] == [33, 42, 27]
    assert (
        "was 0.457 in the first span, 0.315 in the second and 0.274 in the third, over 33, 42 and 27 positions" in item
    )
    first = readings["span_boundaries"]["first"]
    assert first["between_positions"] == [99, 100] and first["block"] == 4
    assert readings["span_boundaries"]["second"]["block"] == 8
    before = [(x["position"], _q(x["weight"], 3)) for x in first["before"]]
    after = [(x["position"], _q(x["weight"], 3)) for x in first["after"]]
    assert before == [(93, "0.484"), (97, "0.447"), (98, "0.473")]
    assert after == [(101, "0.315"), (103, "0.302"), (105, "0.306")]
    assert (
        "read 0.484, 0.447 and 0.473 at positions 93, 97 and 98, and 0.315, 0.302 and 0.306 at 101, 103 and 105."
        in item
    )
    assert "the first span boundary falls inside block 4 and the second inside block 8." in item
    same, cross = readings["copies_by_span"]["same_span"], readings["copies_by_span"]["cross_span"]
    assert (same["n"], _q(same["sum_z2"], 1), same["n_abs_z_over_3"]) == (43, "34.9", 0)
    assert (cross["n"], _q(cross["sum_z2"], 1), cross["n_abs_z_over_3"]) == (85, "836.8", 27)
    assert same["sum_z2"] < same["n"] and cross["sum_z2"] > 5 * cross["n"]
    assert (
        "the 43 circuits whose two copies ran in the same span give a sum of z² of 34.9 on 43 degrees of freedom, none "
        "beyond |z| = 3, and the 85 whose copies ran in different spans give 836.8 on 85, with all 27 beyond." in item
    )
    chi = [_q(x["chi2_per_dof_against_one_weight"], 1) for x in w]
    assert chi == ["0.8", "1.2", "3.1"]
    assert "in χ² per degree of freedom, was 0.8, 1.2 and 3.1)" in item
    assert "Two classes of candidate are theories that can be proved wrong, and neither has been tested." in item
    assert (
        "in the test record's span check of a run on ibm_kingston (`span-check-t9.md`; the processor confirmed by "
        "the author in chat, 17 October 2026), the readings of several qubits changed at span boundaries whose gaps "
        "were 10.3 s and 0.9 s." in item
    )  # A26 R1, Q4
    a = reuse_doc(T7_SPAN_READINGS)
    assert [x["weighted_mean"] for x in a["weight_per_span"]] == [x["weighted_mean"] for x in w]
    for word in ("minute", "drift", "in time", "per second"):
        assert word not in item.split("**What the counts show", 1)[1].split("This is a measurement", 1)[0], word
    method = " ".join((ROOT / "docs" / "method.md").read_text().split())
    assert "A provider may execute one job as several spans" in method
    assert "the copies check is reported split by whether a circuit's two copies ran in the same span." in method
    page = " ".join((ROOT / "docs" / "reproduce.md").read_text().split())
    assert 'pytest tests/test_reproduction.py -k "spans and 7"' in page  # A27, R1, item 20: -k selects test 7's case
    log = " ".join((ROOT / "CHANGELOG.md").read_text().split())
    assert (
        "- Amendment A26: finding 28 reads the weight per execution span, after the provider's execution record" in log
    )


# --------------------------------------------------------------------------- finding 29 (Amendment A27)
def test_finding_29():
    """Finding 29's numbers, each against the record it quotes: test 8's and test 9's counts of verdicts, the two
    candidates and the copies' signature from their fits; the spans' sizes, gaps and positions out of order from the
    providers' records; test 10's verdicts, switch and time within spans, and test 11's fits, monitor and boundary
    table from their analysis records, which the reproduction cases recompute; the counts read together and the desk
    model's rates from its report. Ruling R2 (A27): tests 12 to 15's records, the sharing, the two states on 143, the
    error of a span's weight and test 15's table of every boundary, row by row, against their records. It names no
    cause, and no word the kickoff keeps out but the one quoted field name `telegraph_sd`."""
    import math
    import re
    import statistics

    from _reuse_runs import _gz

    item = _item(29)
    t8 = archive.load("ibm_kingston/t8-survey.json")
    f1, f2, f3 = (
        _gz("ibm_kingston/fits-t8-job1.json.gz"),
        _gz("ibm_kingston/fits-t8-job2.json.gz"),
        t8["archived"]["fits_job3"],
    )
    c = {k: f1["count"][k] + f2["count"][k] for k in f1["count"]}
    assert (len(f1["qubits"]), len(f2["qubits"])) == (78, 54) and c == {
        "NO RESOLVED SPLIT": 119,
        "TWO FIXED FREQUENCIES": 2,
        "NOT SETTLED": 11,
        "NOT USABLE": 0,
    }
    assert (
        "Of the 132 qubits, 119 returned NO RESOLVED SPLIT, 2 TWO FIXED FREQUENCIES (43 and 134) and 11 NOT SETTLED"
        in item
    )
    q43, q43j3, q134j3 = f1["qubits"]["43"], f3["qubits"]["43"], f3["qubits"]["134"]
    assert (q43j3["verdict"], q134j3["verdict"]) == ("TWO FIXED FREQUENCIES", "NO RESOLVED SPLIT")
    assert [_q(x, 2) for x in (q43j3["P"]["params"]["delta_MHz"] * 1e3, *q43j3["deciding"]["delta_ci90_kHz"])] == [
        "5.83",
        "5.35",
        "7.33",
    ]
    assert [_q(x, 2) for x in (q43["P"]["params"]["delta_MHz"] * 1e3, *q43["deciding"]["delta_ci90_kHz"])] == [
        "5.45",
        "5.22",
        "5.85",
    ]
    assert _q(q134j3["lines_kHz"][0], 1) == "58.1" and q134j3["P"]["params"]["b"] > 0.99
    assert "at δ 5.83 kHz (90% interval 5.35 to 7.33) beside job 1's 5.45 kHz (5.22 to 5.85)" in item
    sig = [q for f in (f1, f2) for q, v in f["qubits"].items() if v["copies_check"]["ramsey"]["sum_z2"] > 512]
    assert len(sig) == 16 and "on 16 records the two copies of the Ramsey circuits disagreed" in item
    w = {x["k"]: x["b_pos"] for x in f1["qubits"]["134"]["weight_in_execution_order"]["positions"]}
    assert [_q(w[k], 3) for k in (96, 93, 104, 101)] == ["0.815", "1.001", "−0.013", "−0.008"]
    assert (
        "the positions of the first span implied weights of 0.815 to 1.001 on the upper line, near 55 kHz "
        "(positions 93, "
        "96 and 99)" in item
    )
    assert "those of the second −0.013 to −0.008 (101, 102 and 104)" in item
    assert "with no error of those weights on the record" in item  # A27, R2: test 15 read no job of test 8
    # test 9
    t9 = archive.load("ibm_kingston/t9-day2-scan.json")["archived"]
    a, b = t9["fits_job1_43_134"]["qubits"]["43"], t9["fits_job1_43_134"]["qubits"]["134"]
    assert (a["verdict"], b["verdict"]) == ("NOT SETTLED", "NO RESOLVED SPLIT")
    assert _q(-a["deciding"]["P_minus_S"], 4) == "0.0072" and _q(a["P"]["params"]["b"], 3) == "0.830"
    assert [_q(x, 2) for x in (a["P"]["params"]["delta_MHz"] * 1e3, *a["deciding"]["delta_ci90_kHz"])] == [
        "16.51",
        "15.71",
        "17.34",
    ]
    assert _q(b["lines_kHz"][1], 2) == "4.53" and _q(1 - b["P"]["params"]["b"], 3) == "0.993"
    s2, s3 = t9["fits_job2"]["count"], t9["fits_job3"]["count"]
    assert [s2[k] + s3[k] for k in ("STEADY", "STEPPED", "MOVING", "NOT USABLE")] == [106, 10, 6, 1]
    assert "Of the 123 qubits, 122 were usable: 106 returned STEADY, 10 STEPPED and 6 MOVING." in item
    g1 = _gz("ibm_kingston/fits-t9-job1.json.gz")
    sig9 = [
        q
        for q, v in g1["qubits"].items()
        if v["copies_check"]["ramsey"]["sum_z2"] > 512 and v["copies_check"]["readout"]["sum_z2"] <= 13.82
    ]
    assert len(sig9) == 11 and sum(t9["fits_job2"]["qubits"][q]["verdict"] == "STEPPED" for q in sig9) == 4
    # the spans
    sp = archive.load("ibm_kingston/spans-t8-t9.json")
    jobs = [j for j in sp["jobs"] if j["n_positions"] >= 260]
    t11 = archive.load("ibm_fez/t11-day2-monitor.json")
    every = [j["spans"] for j in jobs] + [archive.load("ibm_fez/spans-t7.json")["spans"]]
    every += [
        _gz(f"ibm_kingston/results-t10-job{j}-counts.json.gz")["execution_metadata"]["execution_spans"] for j in "123"
    ]
    every += [t11["jobs"][j]["execution_metadata"]["execution_spans"] for j in "123"]
    t12 = archive.load("ibm_fez/t12-short-monitor.json")
    t14 = archive.load("ibm_fez/t14-in-phase-control.json")
    every += [t["jobs"]["1"]["execution_metadata"]["execution_spans"] for t in (t12, t14)]  # A27, R2
    gaps, thirds, npos = [], [], []
    for spans in every:
        a_ = wait.span_assignment(spans)
        sizes = [len(s["positions"]) for s in a_["spans"]]
        assert len(sizes) == 3 and set(sizes[:2]) <= {100, 101} and 48 <= sizes[2] <= 100, sizes
        gaps += [g["gap_s"] for g in a_["gaps"]]
        thirds.append(sizes[2])
        npos.append(sum(sizes))
    assert (min(thirds), max(thirds), min(npos), max(npos)) == (48, 100, 248, 300)
    assert _q(min(gaps) * 1e3, 0) == "5" and _q(max(gaps), 1) == "19.1"
    assert "Every job of 248 to 300 positions ran as three execution spans." in item
    assert "the third the rest, 48 to 100" in item and "The gaps between spans ran from 5 ms to 19.1 s." in item
    s12 = wait.span_assignment(t12["jobs"]["1"]["execution_metadata"]["execution_spans"])
    span12 = {p_: i for i, s_ in enumerate(s12["spans"]) for p_ in s_["positions"]}
    assert (span12[99], span12[100], span12[101]) == (1, 0, 0)
    assert "and test 12 ran positions 100 and 101 in its first span and 99 in its second" in item
    j2 = next(j for j in sp["jobs"] if (j["test"], j["job"]) == ("t9", 2))
    span_of = {p: s["span"] for s in j2["spans"] for p in s["positions"]}
    assert (span_of[98], span_of[99], span_of[100]) == (1, 0, 0) and _q(j2["gaps"][0]["gap_s"], 1) == "10.3"
    assert "test 9's job 2 ran position 98 in its second span, after a gap of 10.3 s" in item
    ch = sp["comparison"]["scan"]["job2"]["changes"]
    assert (
        len(ch),
        sum(x["class"] == "at a boundary" for x in ch),
        sum(x["class"] == "within one repeat of one" for x in ch),
    ) == (20, 9, 9)
    # test 10
    t10 = archive.load("ibm_kingston/t10-monitor.json")["archived"]["analysis"]
    recs = [q for j in t10["per_job"].values() for q in j.values()]
    cnt = {k: sum(j[k] for j in t10["count_by_job"].values()) for k in t10["count_by_job"]["1"]}
    assert len(recs) == 192 and cnt == {
        "QUIET": 189,
        "SWITCHES AT BOUNDARIES ONLY": 1,
        "SWITCHES WITHIN SPANS": 0,
        "NOT USABLE": 2,
    }
    assert (
        "Of the 192 qubit records, 189 returned QUIET, 1 SWITCHES AT BOUNDARIES ONLY and none SWITCHES WITHIN SPANS; 2 "
        "were NOT USABLE." in item
    )
    (sw,) = [(j, q) for j, jj in t10["per_job"].items() for q, v in jj.items() if v["n_boundary"]]
    assert sw == ("1", "77") and t10["per_job"]["2"]["77"]["verdict"] == "QUIET"
    fits10 = _gz("ibm_kingston/fits-t10.json.gz")["jobs"]["1"]["per_qubit"]["77"]["switches"][0]
    assert (_q(fits10["d"], 3), _q(fits10["size_kHz"], 2)) == (
        "−1.139",
        "−9.06",
    ) and "−1.139 rad (−9.06 kHz at its 20 µs wait)" in item
    t_within = sum(q["within_time_s"] for q in recs if q["usable"])
    assert f"{round(t_within):,}" == "17,398" and "17,398 qubit-seconds" in item
    per = [v for q in recs for v in q["repeat_period_s"].values() if v]
    assert (_q(min(per), 2), _q(max(per), 2)) == (
        "0.58",
        "0.65",
    ) and "a span's duration over its repeats being 0.58 to 0.65 s" in item
    # test 11
    an = t11["archived"]["analysis"]
    j1 = an["jobs"]["1"]
    P, d = j1["analysis"]["fits"]["P"]["params"], j1["analysis"]["deciding"]
    assert j1["verdict"] == "CONFIRMED ON DAY 2"
    assert (_q(d["held_out_error_P"], 4), _q(d["held_out_error_S"], 4)) == ("0.0109", "0.1212")
    assert [_q(x, 2) for x in (P["delta_MHz"] * 1e3, *d["delta_ci90_kHz"])] == ["44.70", "44.65", "44.76"]
    assert [_q(x, 3) for x in (P["b"], *d["b_ci90"])] == ["0.466", "0.458", "0.474"]
    assert (
        "the split δ was 44.70 kHz (44.65 to 44.76) against day 1's 44.82 (44.72 to 44.92), and the weight b 0.466 "
        "(0.458 to 0.474) against 0.355 (0.333 to 0.377)" in item
    )
    d7 = archive.load("ibm_fez/t7-ramsey-xy.json")["archived"]["analysis"]["fits"]["P"]["params"]
    assert (
        _q((d7["Delta0_MHz"] - P["Delta0_MHz"]) * 1e3, 1) == "62.7"
        and _q((d7["delta_MHz"] - P["delta_MHz"]) * 1e3, 2) == "0.12"
    )
    assert _q(j1["R0_for_the_monitor"], 4) == "0.4749" and _q(j1["antiphase_wait_from_day2_split_us"], 1) == "5.6"
    pairs, t_mon = 0, 0.0
    for j in ("2", "3"):
        jj = an["jobs"][j]
        assert (jj["phase_verdict"], jj["weight_verdict"]) == ("QUIET", "WEIGHT QUIET")
        rows = jj["repeats"]
        pairs += sum(
            1 for x, y in zip(rows, rows[1:]) if not x["straddles"] and not y["straddles"] and x["span"] == y["span"]
        )
        t_mon += jj["phase"]["within_time_s"]
    assert (pairs, _q(t_mon, 1)) == (
        285,
        "167.7",
    ) and "in the 285 consecutive pairs within spans, over 167.7 s." in item
    assert (an["jobs"]["2"]["phase"]["straddling_repeats"], an["jobs"]["3"]["phase"]["straddling_repeats"]) == (
        [49, 50, 100],
        [50, 100],
    )
    last = an["jobs"]["3"]["boundary_table"]["boundaries"][-1]
    assert (_q(last["d_w"], 3), _q(max(0.10, 5 * last["se_w"]), 3)) == ("−0.111", "0.113")
    means = {j: [_q(x["mean_w"], 3) for x in an["jobs"][j]["weight"]["per_span"]] for j in ("2", "3")}
    assert means == {"2": ["0.340", "0.392", "0.360"], "3": ["0.323", "0.350", "0.237"]}
    assert [_q(x["weighted_mean"], 3) for x in j1["span_readings_A26"]["weight_per_span"]] == [
        "0.496",
        "0.433",
        "0.448",
    ]
    ps = an["jobs"]["2"]["weight"]["per_span"]
    floor = 5 * math.hypot(*(max(x["se_propagated"], x["se_sd_over_sqrt_n"]) for x in ps[:2]))
    assert _q(floor, 3) == "0.017" and "0.017" not in item  # A27, R2: a shot-noise floor, left out
    a12 = t12["archived"]["analysis"]
    assert _q(statistics.median(x["threshold_w"] for x in a12["pairs"]), 3) == "0.163"
    assert "about 0.115 in weight for one pair of repeats at 1,000 shots and 0.16 at 500" in item
    # read together, and the model, from its report
    rep = (archive.data_dir() / "desk/sandhi/v3.1/report-model-01-v3.md").read_text()
    for row in (
        "| 9, job 2 | 0 / 509 |",
        "| 9, job 3 | 0 / 349 |",
        "| All shuffled | 16 / 38 | 11 / 38 |",
        "| Test 11 monitors | 4 / 4 | 1 / 4 |",
        "| F at 4kHz | 1 / 479 |",
        "Stamp pair 1 is 16 / 47",
    ):
        assert row in rep, row
    for s in (
        "no frequency change of 4 kHz or more between consecutive repeats in 858 pairs",
        "one crossing of 479",
        "at 16 of 38 boundaries of the shuffled jobs and at all 4 of the monitor's",
        "by 0.10 or more at 11 of 38 and 1 of 4",
        "Of the 47 qubits in both test 8's job 1 and test 9's job 1, 16 changed",
    ):
        assert s in item, s
    for s in (
        "1.1·10⁻⁵ per qubit-second (9.6·10⁻⁸ to 9.4·10⁻⁵",
        "0.0025 per crossing (0.00037 to 0.0081; 1 of 479)",
        "0.42 per shuffled boundary (0.30 to 0.55; 16 of 38)",
        "0.95 per monitor boundary (0.64 to 0.9995; 4 of 4)",
        "0.36 per qubit (0.25 to 0.47; 17 of 48)",
        "0.0014 per second (1.2·10⁻⁵ to 0.011; 0 in 285 pairs over 168 s)",
    ):
        assert s in item, s
    for a_, b_ in (
        ("1.11399e−05", "9.4065e−05"),
        ("0.00246794", "0.00812839"),
        ("0.421749", "0.554002"),
        ("0.947985", "0.999538"),
        ("0.355184", "0.472002"),
        ("0.00135611", "0.0114509"),
    ):
        assert a_ in rep and b_ in rep
    for h in (
        "745059e38db0e54f4bcef2bc8cad17a2fde40223f0a1dde75982a621817a38a3",
        "02b8003461f948991217be683bc0706f611da57ac4e03d53ca8745274fc019b4",
    ):
        assert h in item
    for s in (
        '"The model is a kinetic description; it names no cause."',
        '"A record below its own floor is censored, not absent."',
        "\"The predictions are the model's, written before the run they predict, and they are what can prove it "
        'wrong."',
    ):
        assert s in item
    assert (
        "a probability of 0.52 (0.35 to 0.69); there was none" in item
        and "job 1's first difference of span means, 0.063, lay below it, at 13 of the shot-noise errors finding 28's "
        "method propagated and 1.16 of test 15's borrowed error"
        in item
    )
    assert "13.1774 combined errors" in rep
    # the rules and their issues
    for f, issue in (
        ("ibm_kingston/t8-rule.md", 53),
        ("ibm_kingston/t9-rule.md", 54),
        ("ibm_kingston/t10-rule.md", 55),
        ("ibm_fez/t11-rule.md", 58),
        ("ibm_fez/t12-rule.md", 59),
        ("ibm_fez/t13-rule.md", 61),
        ("ibm_fez/t14-rule.md", 62),
        ("ibm_fez/t15-rule.md", 63),
    ):
        assert f"issues/{issue})" in item and (archive.data_dir() / f).exists()
    assert (
        "test 8's was posted in [issue 53](https://github.com/dogma-guru/manacitra/issues/53) after its jobs had run"
        in item
    )
    assert (
        t8["meta"]["rule"]["posted"]["created_utc"] > t8["jobs"]["3"]["timestamps"]["finished"].replace(" ", "T")[:19]
    )
    for word in (
        "telegraph",
        "parit",
        "defect",
        "proof",
        "proves",
        "reveals",
        "kill",
        "benchmark",
        "pre-registered",
        "veri" + "fied",
        "valid" + "ated",
        "confirmed the model",
    ):
        # A27, R2 (question 3): the one quoted field name of test 15's published record is allowed, nothing else
        assert word not in item.lower().replace("`telegraph_sd`", "", 1), word
    assert item.count("telegraph") == 1 and "`telegraph_sd`" in item
    assert "They name no cause" in item and "Manacitra does not rank machines." in item
    assert not re.search("[\u2013\u2014]", item)
    assert "(f) The comparison class" not in item and "version 4" not in item  # A27, R2: questions 1 and 16
    _finding_29_r2(item, t12, t14)


def _t15_word(z: float) -> str:
    """Test 15's boundary word from its rule: NO CHANGE at or under 2, BETWEEN over 2 to 3, CHANGE over 3."""
    return "NO CHANGE" if z <= 2 else ("BETWEEN" if z <= 3 else "CHANGE")


def _t15_span(r: dict) -> dict:
    """A27, ruling R3 (S5): a separable span's statistics recomputed from test 15's published sweep means, as its
    read_t15.py computes them: the sharing ratio over the recorded independent share, the 1/e lag (lags 1 to 200), the
    threshold midway between the 10th and 90th percentiles, the duty, the switches and runs, the quarter-span duties,
    the middle fifth, and the estimated sampling standard deviation at the lag used (three sweeps as a ceiling). Each
    sweep mean is a mean over the span's rows, published at four places, and is recovered exactly as k/n, so that a
    value on the threshold falls as it fell in the read."""
    import math

    import numpy as np

    n = r["n_rows"]
    k = np.rint(np.array(r["sweep_means"], float) * n)
    assert np.all(np.abs(k / n - np.array(r["sweep_means"])) < 6e-5)
    mj = k / n
    big_n = len(mj)
    sweep = r["duration_s"] / big_n
    v_obs = float(mj.var(ddof=1))
    ratio = v_obs / r["v_ind"]
    word = "SHARED" if ratio > 3 else ("INDEPENDENT" if ratio < 1.5 else "UNDECIDED")
    x = mj - mj.mean()
    v0 = float(np.sum(x * x))
    acf = [float(np.sum(x[lag:] * x[:-lag]) / v0) for lag in range(1, 201)]
    excess = 1 - r["v_ind"] / v_obs
    below = [i for i, a in enumerate(acf) if a < excess / math.e]
    lag = below[0] + 1 if below else 201
    p10, p90 = (float(v) for v in np.percentile(mj, [10, 90]))
    high = mj > (p10 + p90) / 2
    idx = np.flatnonzero(np.diff(high.astype(np.int8)))
    bounds = np.concatenate([[0], idx + 1, [big_n]])
    lens, states = np.diff(bounds), high[bounds[:-1]]
    lo5, hi5 = p10 + 0.4 * (p90 - p10), p10 + 0.6 * (p90 - p10)
    mid5 = float(np.mean((mj >= lo5) & (mj <= hi5)))
    b = float(high.mean())
    used = (3 if lag < 3 else lag) if word == "SHARED" else None
    return {
        "n_shots": big_n,
        "sweep_s": sweep,
        "ratio": ratio,
        "word": word,
        "lag": lag,
        "duty": b,
        "switches": len(idx),
        "runs_high": float(lens[states].mean()),
        "runs_low": float(lens[~states].mean()),
        "quarters": [float(c.mean()) for c in np.array_split(high, 4)],
        "mid5": mid5,
        "lag_used": used,
        "ceiling": (lag < 3) if used else None,
        "sd": math.sqrt(2 * b * (1 - b) * used * sweep / r["duration_s"]) if used else None,
        "inflated": bool(big_n == 1000 and mid5 > 0.10),
    }


def _finding_29_r2(item: str, t12: dict, t14: dict) -> None:
    """A27, ruling R2: finding 29's sentences from tests 12 to 15, each number against its record; ruling R3: the
    table of every boundary derived from the published sweep means, the unlisted kingston qubits, the stamp's 16 of 47,
    and the lags and runs in returned indices."""
    import math

    import numpy as np
    from _reuse_runs import _gz

    q = _q
    # test 12
    a12 = t12["archived"]["analysis"]["analysis"]
    assert tuple(a12["verdicts"][k] for k in ("phase", "weight_by_pairs", "weight_by_levels")) == (
        "QUIET",
        "WEIGHT QUIET",
        "LEVELS DIFFER AT SOME",
    )
    assert (a12["n_pairs"]["within"], a12["n_pairs"]["boundary"]) == (117, 2) and a12["n_within"] == a12[
        "n_within_w"
    ] == 0
    lc = a12["level_changes"]
    assert [q(-x["difference"], 3) for x in lc] == ["0.013", "0.137"] and [q(-x["in_errors"], 1) for x in lc] == [
        "2.7",
        "24.6",
    ]
    assert (
        "at its second boundary the span mean of the weight was 0.137 lower, 24.6 times the rule's shot-noise error, "
        "and "
        "at its first 0.013 lower, 2.7 times" in item
    )
    assert [q(x["mean_w"], 3) for x in a12["weight_per_span"]] == ["0.356", "0.343", "0.206"]
    per = a12["repeat_period_s"].values()
    assert (q(a12["within_time_s"], 1), q(min(per), 2), q(max(per), 2)) == ("38.2", "0.29", "0.36")
    assert (
        "The weight per span was 0.356, 0.343 and 0.206, over 38.2 s within spans, a repeat taking 0.29 to 0.36 s."
        in item
    )
    # test 13
    f13 = archive.load("ibm_fez/t13-per-shot-read.json")["archived"]["analysis"]
    ys = [s_["Y"] for k in ("t11-job2", "t11-job3", "t12-job1") for s_ in f13["jobs"][k]["spans"]]
    assert set(f13["words"].values()) == {"SHARED"} and len(ys) == 9 and {y["word"] for y in ys} == {"SHARED"}
    assert (q(min(y["ratio"] for y in ys), 1), q(max(y["ratio"] for y in ys), 1)) == ("16.4", "37.6")
    assert (q(min(y["correlation_time_s"] for y in ys), 2), q(max(y["correlation_time_s"] for y in ys), 2)) == (
        "0.12",
        "0.19",
    )
    assert (min(y["correlation_time_sweeps"] for y in ys), max(y["correlation_time_sweeps"] for y in ys)) == (4, 10)
    assert (q(min(y["sweep_s"] for y in ys) * 1e3, 0), q(max(y["sweep_s"] for y in ys) * 1e3, 0)) == ("15", "35")
    b13 = [s_[k]["ratio"] for s_ in f13["jobs"]["t11-job1-beside"]["spans"] for k in ("Y", "X")]
    assert (q(min(b13), 2), q(max(b13), 2)) == ("0.86", "1.24")
    for s_ in (
        "All nine spans read SHARED, with ratios of 16.4 to 37.6, so each job is SHARED.",
        "was 4 to 10 sweeps (returned indices), or 0.12 to 0.19 s if the returned indices are chronological sweeps "
        "evenly spaced across the span (a span's duration over its shots per position, 15 to 35 ms).",
        "read ratios of 0.86 to 1.24, with no word.",
    ):
        assert s_ in item, s_
    # test 14
    a14 = t14["archived"]["analysis"]
    assert a14["usable"] is False and (q(a14["median_r_a"], 4), q(a14["median_r_c"], 3)) == ("0.0758", "0.452")
    assert "estimate_and_decision" in a14 and "actual_machine_time_s" not in a14["estimate_and_decision"]
    an14 = a14["analysis"]
    assert [q(an14["levels"]["R0"][k]["mean"], 4) for k in "012"] == ["0.4727", "0.4664", "0.4755"]
    assert [q(abs(x["in_errors"]), 1) for x in an14["level_changes"]["R0"]] == ["1.2", "1.4"]
    assert [q(abs(x["in_errors"]), 1) for x in an14["level_changes"]["phi_c"]] == ["0.0", "0.7"]
    assert [q(an14["frame_per_span_kHz"][k]["mean_kHz"], 2) for k in "012"] == ["−8.49", "−8.50", "−8.69"]
    assert (
        "the median length at the antiphase wait was 0.0758, under the rule's 0.08 (the in-phase wait's, 0.452" in item
    )
    assert (
        "R0 per span, 0.4727, 0.4664 and 0.4755, differed at the two boundaries by 1.2 and 1.4 of its rule's errors"
        in item
    )
    assert "the frame per span at the in-phase wait, −8.49, −8.50 and −8.69 kHz, by 0.0 and 0.7" in item
    # test 15: the words, the table row by row, its counts
    f15 = archive.load("ibm_fez/t15-error-model-read.json")["archived"]["analysis"]
    assert f15["words"] == {
        "t10-job1": "MIXED",
        "t10-job2": "MIXED",
        "t10-job3": "NOT SEPARABLE",
        "t11-job2": "SHARED",
        "t11-job3": "SHARED",
        "t12-job1": "SHARED",
        "t14-job1": "SHARED",
    }
    findings = (ROOT / "docs" / "findings.md").read_text()
    block = findings.split('<a id="finding-29"></a>', 1)[1].split('<a id="finding-30"></a>', 1)[0]
    rows = [r_.strip() for r_ in block.splitlines() if r_.strip().startswith("| test ")]
    bs = f15["boundaries"]
    assert len(rows) == len(bs) == 28
    # A27, R3 (S5): every separable span recomputed from its published sweep means, against the read's numbers
    stats = {}
    for jk, j in f15["jobs"].items():
        for qb, qq in j["qubits"].items():
            if not qq["listed_separable"]:
                continue
            for wk, w in qq["waits"].items():
                if wk == "control":
                    continue
                for sp in w["spans"]:
                    r_ = sp[w["quadrature_of_record"]]
                    st = _t15_span(r_)
                    stats[(jk, qb, sp["span"])] = st
                    assert (st["word"], st["lag"], st["duty"], st["switches"], st["quarters"]) == (
                        r_["word"],
                        r_["lag_1_over_e"],
                        r_["duty_b"],
                        r_["switches"],
                        r_["quarter_span_duties"],
                    ), (jk, qb, sp["span"])
                    assert (
                        abs(st["ratio"] / r_["ratio"] - 1) < 1e-3
                        and abs(st["mid5"] - r_["mid_sweep_fraction_middle_fifth"]) < 1e-12
                    )
                    assert abs(st["runs_high"] * st["sweep_s"] - r_["dwell_high_s"]) < 1e-9
                    assert abs(st["runs_low"] * st["sweep_s"] - r_["dwell_low_s"]) < 1e-9
                    assert st["inflated"] == r_["switch_counts_inflated"]
                    assert (st["sd"] is None) == (r_.get("telegraph_sd") is None)
                    if st["sd"] is not None:
                        assert abs(st["sd"] - r_["telegraph_sd"]) < 1e-12 and st["lag_used"] == r_["tau_c_sweeps_used"]
    assert len(stats) == 42
    # the published ratios, each from the record that published it
    an11 = archive.load("ibm_fez/t11-day2-monitor.json")["archived"]["analysis"]["jobs"]
    published = {}
    for jn in ("2", "3"):
        ps_ = an11[jn]["weight"]["per_span"]
        for x, y_ in zip(ps_, ps_[1:]):
            d_ = y_["mean_w"] - x["mean_w"]
            published[(f"t11-job{jn}", (x["span"], y_["span"]))] = (
                d_,
                d_ / math.hypot(x["se_propagated"], y_["se_propagated"]),
            )
    for x in t12["archived"]["analysis"]["analysis"]["level_changes"]:
        published[("t12-job1", tuple(x["spans"]))] = (x["difference"], x["in_errors"])
    for x in t14["archived"]["analysis"]["analysis"]["level_changes"]["w"]:
        published[("t14-job1", tuple(x["spans"]))] = (x["difference"], x["in_errors"])
    names = {
        "t10-job1": "test 10, job 1",
        "t10-job2": "test 10, job 2",
        "t11-job2": "test 11, job 2",
        "t11-job3": "test 11, job 3",
        "t12-job1": "test 12",
        "t14-job1": "test 14",
    }
    derived = []
    for row, b in zip(rows, bs):
        cells = [c_.strip() for c_ in row.strip("|").split("|")]
        assert len(cells) == 12, row
        sa, sb = (stats[(b["job"], str(b["qubit"]), sp_)] for sp_ in b["spans"])
        d_ = sb["duty"] - sa["duty"]
        both = sa["word"] == sb["word"] == "SHARED"
        sd_ = math.hypot(sa["sd"], sb["sd"]) if both else None
        word = _t15_word(abs(d_) / sd_) if both else "NOT READ"
        derived.append(word)
        assert (cells[0], cells[1], cells[2]) == (
            names[b["job"]],
            str(b["qubit"]),
            f"{b['spans'][0]} to {b['spans'][1]}",
        )
        assert cells[3] == f"{sa['duty']:.3f}, {sb['duty']:.3f}" and cells[4] == f"{sa['word']}, {sb['word']}", row
        assert cells[5] == q(d_, 3) and cells[8] == f"**{word}**" and word == b["word"], row
        if both:
            ceiling = "‡" if (sa["ceiling"] or sb["ceiling"]) else ""
            assert cells[6] == q(sd_, 4) + ceiling and cells[7] == q(abs(d_) / sd_, 2), row
        else:
            assert cells[6] == cells[7] == "", row
        pub_ = published.get((b["job"], tuple(b["spans"])))
        if pub_ is None:
            assert b["processor"] == "ibm_kingston" and cells[9:] == ["none published", "", ""], row
        else:
            zp = abs(pub_[0]) / sd_
            assert cells[9] == q(pub_[0], 3) and cells[10] == q(pub_[1], 1), row
            assert cells[11] == f"{q(zp, 2)}, {_t15_word(zp)}", row
    counts = {k: derived.count(k) for k in ("CHANGE", "BETWEEN", "NO CHANGE", "NOT READ")}
    assert counts == {"CHANGE": 0, "BETWEEN": 0, "NO CHANGE": 17, "NOT READ": 11}
    assert f15["table_counts_by_processor"] == {
        "ibm_kingston": {"NO CHANGE": 9, "NOT READ": 11},
        "ibm_fez": {"NO CHANGE": 8},
    }
    assert (
        "the 17 boundaries read, 8 on 143 and 9 on ibm_kingston, all read NO CHANGE, and 11 on ibm_kingston were not "
        "read" in item
    )
    read = [b for b in bs if b["word"] != "NOT READ"]
    sens = [x["ratio"] for b in read for x in b["sensitivity"].values()]
    assert q(max(sens), 2) == "1.81" and not any(b["word_changes_under_sensitivity"] for b in read)
    sds = [b["combined_sd"] for b in read]
    assert (q(min(sds), 3), q(max(sds), 3)) == ("0.044", "0.174") and "0.044 to 0.174 combined at a boundary" in item
    bj = f15["between_jobs_143"]["rows"]
    assert [q(x["ratio"], 2) for x in bj] == ["1.77", "0.14", "1.56"] and {x["word"] for x in bj} == {"NO CHANGE"}
    means, job_sd = {}, {}
    for jk in ("t11-job2", "t11-job3", "t12-job1", "t14-job1"):
        sts = [stats[(jk, "143", sp_)] for sp_ in (0, 1, 2)]
        means[jk] = sum(x["duty"] for x in sts) / 3
        job_sd[jk] = math.sqrt(sum(x["sd"] ** 2 for x in sts)) / 3
    order = ["t11-job2", "t11-job3", "t12-job1", "t14-job1"]
    zj = [abs(means[b_] - means[a_]) / math.hypot(job_sd[a_], job_sd[b_]) for a_, b_ in zip(order, order[1:])]
    assert [q(z, 2) for z in zj] == ["1.77", "0.14", "1.56"] and {_t15_word(z) for z in zj} == {"NO CHANGE"}
    assert "(ratios 1.77, 0.14 and 1.56)" in item and "(1.81 at most)" in item
    # the borrowed rows
    sb = {(r_["job"], tuple(r_["spans"])): r_ for r_ in f15["shuffled_borrowed"]["rows"]}
    keys = (("t11-job1", (0, 1)), ("t11-job1", (1, 2)), ("t7", (0, 1)), ("t7", (1, 2)))
    got = [(q(sb[k]["ratio"], 2), sb[k]["word"]) for k in keys]
    assert got == [("1.16", "NO CHANGE"), ("0.25", "NO CHANGE"), ("2.65", "BETWEEN"), ("0.71", "NO CHANGE")]
    assert all("borrowed" in sb[k]["label"] for k in keys)
    assert q(f15["shuffled_borrowed"]["tau_c_borrowed_s"], 3) == "0.137"
    assert "test 11's job 1 read NO CHANGE (borrowed) at both boundaries, 1.16 and 0.25" in item
    assert "test 7's job BETWEEN (borrowed) at its first, 2.65, and NO CHANGE (borrowed) at its second, 0.71" in item
    # 143's spans: correlation times, runs, the middle fifth, the duty against the published weight, the errors
    ss = []
    for jk, wk in (
        ("t11-job2", "monitor"),
        ("t11-job3", "monitor"),
        ("t12-job1", "monitor"),
        ("t14-job1", "antiphase"),
    ):
        j = f15["jobs"][jk]
        for sp, js in zip(j["qubits"]["143"]["waits"][wk]["spans"], j["spans"]):
            ss.append((jk, sp, js["duration_s"]))
    y = [(jk, sp["Y"], T) for jk, sp, T in ss]
    early = [r_ for r_ in y if r_[0] != "t14-job1"]
    late = [r_ for r_ in y if r_[0] == "t14-job1"]
    assert (q(min(r_[1]["tau_c_s"] for r_ in early), 3), q(max(r_[1]["tau_c_s"] for r_ in early), 3)) == (
        "0.121",
        "0.191",
    )
    assert [q(r_[1]["tau_c_s"], 3) for r_ in late] == ["0.174", "0.174", "0.375"]
    assert (q(min(r_[1]["dwell_high_s"] for r_ in y), 2), q(max(r_[1]["dwell_high_s"] for r_ in y), 2)) == (
        "0.10",
        "0.38",
    )
    assert (q(min(r_[1]["dwell_low_s"] for r_ in y), 2), q(max(r_[1]["dwell_low_s"] for r_ in y), 2)) == (
        "0.18",
        "0.67",
    )
    mid = [r_[1]["mid_sweep_fraction_middle_fifth"] * 100 for r_ in y]
    assert (q(min(mid), 1), q(max(mid), 1)) == ("0.2", "9.4")
    pub = f15["published_weight_level_changes"]
    w_of = {(jk, sp_): w_ for jk, xs in pub.items() for x in xs for sp_, w_ in zip(x["spans"], x["w"])}
    dw = [abs(sp["w_duty"] - w_of[(jk, sp["span"])]) for jk, sp, _ in ss]
    assert len(dw) == 12 and q(max(dw), 3) == "0.011"
    n_eff = [T / (2 * r_[1]["tau_c_s"]) for r_ in y for T in (r_[2],)]
    assert (round(min(n_eff[:9])), round(max(n_eff[:9])), round(min(n_eff[9:])), round(max(n_eff[9:]))) == (
        25,
        125,
        10,
        42,
    )
    sd = [r_[1]["telegraph_sd"] for r_ in y]
    assert (q(min(sd[:9]), 3), q(max(sd[:9]), 3), q(max(sd[9:]), 3)) == ("0.043", "0.081", "0.158")
    for s_ in (
        "these are correlation times of 0.121 to 0.191 s and of 0.174, 0.174 and 0.375 s",
        "with 0.2 to 9.4 percent of sweeps in the middle fifth",
        "the duty differs from the published weight by 0.000 to 0.011",
        "25 to 125 in the spans of tests 11 and 12 and 10 to 42 in test 14's",
        "It is 0.043 to 0.081 per span in tests 11 and 12 and up to 0.158 in test 14",
        "(ratios 18.6, 17.9 and 8.8)",
    ):
        assert s_ in item, s_
    assert [q(sp["Y"]["ratio"], 1) for jk, sp, _ in ss if jk == "t14-job1"] == ["18.6", "17.9", "8.8"]
    ctl = f15["jobs"]["t14-job1"]["qubits"]["143"]["waits"]["control"]["spans"]
    assert [q(s_["X"]["ratio"], 2) for s_ in ctl] + [q(s_["Y"]["ratio"], 2) for s_ in ctl] == [
        "1.14",
        "0.89",
        "1.01",
        "1.12",
        "1.12",
        "1.00",
    ]

    # kingston
    def kq(qb):
        out = []
        for k in ("t10-job1", "t10-job2"):
            w = list(f15["jobs"][k]["qubits"][qb]["waits"].values())[0]
            out += [sp[w["quadrature_of_record"]] for sp in w["spans"]]
        return out

    for qb, lo, hi in (("11", "13.6", "15.8"), ("95", "6.1", "7.6")):
        r_ = kq(qb)
        assert {x["word"] for x in r_} == {"SHARED"} and (
            q(min(x["ratio"] for x in r_), 1),
            q(max(x["ratio"] for x in r_), 1),
        ) == (lo, hi)
        assert all(x["tau_c_ceiling"] for x in r_) and q(max(x["tau_c_s"] for x in r_), 3) == "0.095"
    r120 = [x for x in kq("120") if x["word"] == "SHARED"]
    assert [q(x["tau_c_s"], 3) for x in r120] == ["0.349", "0.348", "0.698"]
    r_ind = kq("43") + kq("134")
    assert {x["word"] for x in r_ind} == {"INDEPENDENT"} and (
        q(min(x["ratio"] for x in r_ind), 2),
        q(max(x["ratio"] for x in r_ind), 2),
    ) == ("0.94", "1.06")
    # test 9's scan, beside
    v = [
        s_["within_span_scatter_against_binomial"]
        for qq in f15["beside"]["t9-job2"]["qubits"].values()
        for s_ in qq["spans"]
    ]
    assert [q(x, 2) for x in (np.median(v), np.percentile(v, 5), np.percentile(v, 95), max(v))] == [
        "0.97",
        "0.71",
        "1.31",
        "1.51",
    ]
    assert "median 0.97, 0.71 to 1.31 from the 5th to the 95th percentile, 1.51 at most" in item
    # test 10's jobs, SHARED and not
    t10 = archive.load("ibm_kingston/t10-monitor.json")["archived"]["analysis"]["per_job"]
    tw = {j: sum(x["within_time_s"] for x in t10[j].values() if x["usable"]) for j in "123"}
    assert (f"{round(tw['1'] + tw['2']):,}", f"{round(tw['3']):,}") == ("12,566", "4,831")
    assert (
        "and none in the 12,566 qubit-seconds of test 10's jobs 1 and 2, where 11 and 95 read SHARED in every span"
        in item
    )
    assert "no phase switch in 4,831 qubit-seconds" in item
    # the desk check's resolution, from test 15's rule as published
    rule15 = (archive.data_dir() / "ibm_fez/t15-rule.md").read_text()
    assert "NO CHANGE 74.2, BETWEEN 21.0, CHANGE 4.8" in rule15 and "NO CHANGE 59.8, BETWEEN 30.8, CHANGE 9.5" in rule15
    assert (
        "read NO CHANGE in 74.2 percent of trials and CHANGE in 4.8, and a change of 0.219 read CHANGE in 9.5" in item
    )
    # Sandhi's bets, posted with test 12's rule
    assert t12["meta"]["rule"]["posted"]["issue"] == 59
    assert "posted the two digests with test 12's rule, before its run ([issue 59]" in item
    # A27, R3 (S3): lags and runs in returned indices, seconds only on the stated condition; the inflation flags
    lags = {jk: [stats[(jk, "143", sp_)]["lag"] for sp_ in (0, 1, 2)] for jk in order}
    early_l = lags["t11-job2"] + lags["t11-job3"] + lags["t12-job1"]
    assert (min(early_l), max(early_l), lags["t14-job1"]) == (4, 10, [6, 6, 25])
    s143 = [stats[(jk, "143", sp_)] for jk in order for sp_ in (0, 1, 2)]
    assert [q(f(x["runs_high"] for x in s143), 1) for f in (min, max)] == ["3.3", "25.7"]
    assert [q(f(x["runs_low"] for x in s143), 1) for f in (min, max)] == ["5.9", "44.1"]
    assert (
        "with correlation lags of 4 to 10 sweeps in tests 11 and 12 and of 6, 6 and 25 in test 14, and mean runs of "
        "3.3 to 25.7 sweeps on the upper line and 5.9 to 44.1 on the lower" in item
    )
    assert "If the returned indices are chronological sweeps evenly spaced across the span" in item
    king = {
        qb: [stats[(jk, qb, sp_)] for jk in ("t10-job1", "t10-job2") for sp_ in (0, 1, 2)] for qb in ("11", "95", "120")
    }
    assert {x["lag"] for qb in ("11", "95") for x in king[qb]} == {1}
    assert all(x["ceiling"] for qb in ("11", "95") for x in king[qb])
    assert [q(np.mean([x[k] for x in king[qb]]), 1) for qb in ("11", "95") for k in ("runs_high", "runs_low")] == [
        "1.5",
        "5.7",
        "1.4",
        "5.2",
    ]
    shared120 = [x for x in king["120"] if x["word"] == "SHARED"]
    assert [x["lag"] for x in shared120] == [11, 11, 22] and all(x["inflated"] for x in shared120)
    assert sum(x["inflated"] for x in king["95"]) == 3 and not any(x["inflated"] for x in king["11"])
    assert "mean runs of about 1.5 and 1.4 sweeps high and 5.7 and 5.2 low" in item
    assert "lags of 11, 11 and 22 sweeps (0.349, 0.348 and 0.698 s)" in item
    assert "on 95 in three of its spans and on 120 in all three of its SHARED spans" in item
    mid143 = [x["mid5"] * 100 for x in s143]
    assert (q(min(mid143), 1), q(max(mid143), 1)) == ("0.2", "9.4")
    assert "(0.2 to 9.4 percent in the middle fifth)" in item
    # A27, R3 (S4): the widest quarter-span duties on 143, and the 17 read boundaries not independent
    spread = sorted(
        (
            (max(stats[(jk, "143", sp_)]["quarters"]) - min(stats[(jk, "143", sp_)]["quarters"]), jk, sp_)
            for jk in order
            for sp_ in (0, 1, 2)
        ),
        reverse=True,
    )
    assert [(jk, sp_) for _, jk, sp_ in spread[:2]] == [("t11-job3", 2), ("t12-job1", 0)]
    assert [f"{v:.3f}" for v in stats[("t11-job3", "143", 2)]["quarters"]] == ["0.180", "0.432", "0.260", "0.048"]
    assert [f"{v:.3f}" for v in stats[("t12-job1", "143", 0)]["quarters"]] == ["0.528", "0.176", "0.312", "0.408"]
    assert (
        "in test 11's job 3, span 2 (0.180, 0.432, 0.260 and 0.048) and in test 12's span 0 (0.528, 0.176, 0.312 and "
        "0.408)" in item
    )
    assert "The 17 read boundaries share spans and jobs and are not 17 independent tests." in item
    assert "does not show the duties equal" in item and "scatter of a time average" not in item
    # A27, R3 (B1): the kingston qubits outside the separable list, read as the record gives them
    unl, per_job = [], {}
    for jk in ("t10-job1", "t10-job2", "t10-job3"):
        for qb, qq in f15["jobs"][jk]["qubits"].items():
            if qq["listed_separable"]:
                continue
            for w in qq["waits"].values():
                for sp in w["spans"]:
                    ratio = sp[w["quadrature_of_record"]]["ratio"]
                    unl.append((int(qb), ratio))
                    per_job.setdefault(jk, []).append(ratio)
    assert [q(np.median(v_), 2) for v_ in per_job.values()] == ["1.06", "1.06", "1.06"]
    over = [qb for qb, r_ in unl if r_ > 3]
    assert (len(unl), len(over), sorted(set(over))) == (546, 25, [29, 34, 36, 47, 62, 77, 80, 104])
    assert (
        "their ratios had a median near 1.06 in each job, and 25 of 546 span readings, on 8 qubits (29, 34, 36, 47, "
        "62, 77, 80, 104), exceeded 3" in item
    )
    assert "the finding draws nothing from their ratios" in item
    fits = [
        _gz(f"ibm_kingston/{f}")["qubits"]
        for f in ("fits-t8-job1.json.gz", "fits-t8-job2.json.gz", "fits-t9-job1.json.gz")
    ]
    for qb in ("29", "34", "36", "47", "62", "77", "80", "104"):  # no two-line verdict on the record
        assert all(f[qb]["verdict"] == "NO RESOLVED SPLIT" for f in fits if qb in f), qb
    flat_all = " ".join(findings.split())
    assert "- **The shared-state reading is drawn only from qubits with two resolved lines.**" in flat_all
    # A27, R3 (S1): 16 of the 47 qubits compared across the two stamps, from the fits
    f81, f91 = fits[0], fits[2]
    both = set(f81) & set(f91)
    moved = {x for x in both if abs(f91[x]["S"]["params"]["Delta_MHz"] - f81[x]["S"]["params"]["Delta_MHz"]) * 1e3 >= 4}
    verdict = {x for x in both if f81[x]["verdict"] != f91[x]["verdict"]}
    assert (len(both), len(moved), len(verdict), verdict <= moved) == (47, 16, 3, True)
    assert (
        "about a third of the 47 qubits compared across them (16) changed by 4 kHz or more in the one-line fit" in item
    )
    assert "the 3 that changed verdict among them" in item and "third of one chip" not in item
    # finding 28's pointer (A27, R2, question 9), after its last paragraph
    f28 = findings.split('<a id="finding-28"></a>', 1)[1].split('<a id="finding-29"></a>', 1)[0].rsplit("\n29. ", 1)[0]
    assert f28.rstrip().splitlines()[-1].strip() == (
        "Finding 29's test 15 reads these differences of the weight between spans against the error of a time average: "
        "at a correlation time borrowed from the nearest monitor job, test 7's two boundaries read BETWEEN (2.65) and "
        "NO "
        "CHANGE (0.71)."
    )


def test_the_middle_note_is_published_as_one_dated_line():
    """Amendment A28, 2c (the author's answer 2): the note of 19 October that test 17's rule says is published with the
    run enters as one quoted line, the line test 17's rule tests, with three sentences: the note's name and SHA-256 (as
    ruling 4 of test 17 names it), when the line was written, and that the rest is kept outside the repository."""
    import re

    text = (archive.data_dir() / "ibm_fez" / "t17-middle-note-excerpt.md").read_text()
    quoted = [x for x in text.splitlines() if x.startswith(">")]
    assert quoted == [
        "> - **The middle span (not a test):** middle minus ends positive in all four monitor jobs, 0.41 to 1.11 "
        "telegraph sd."
    ]
    body = [x for x in text.splitlines() if x and not x.startswith(("#", ">"))]
    assert len(body) == 1 and len(re.findall(r"[.!?](?:\s|$)", body[0])) == 3
    assert "`t16-mantri-read-and-scorecard-2026-10-19.md`" in body[0]
    assert "31808acd2d115991f4695cbccafe84db075e6a2eea2647ca01774ce5e897352d" in body[0]
    assert "It was written on 19 October 2026, before test 17's rule was hashed." in body[0]
    assert body[0].endswith("The rest of the file is a working read kept outside the repository.")
    rulings = (archive.data_dir() / "ibm_fez" / "rulings-t17.md").read_text()
    assert "`tests/handback/t16-mantri-read-and-scorecard-2026-10-19.md`" in rulings
    assert "—" not in text and "–" not in text


# --------------------------------------------------------------------------- finding 30 (Amendment A28)
def _item30() -> str:
    """Finding 30's item, whitespace joined, with its pictures' alt text left out (they sit inside the item)."""
    import re

    findings = (ROOT / "docs" / "findings.md").read_text()
    item = findings.split('<a id="finding-30"></a>', 1)[1].split("\n## ", 1)[0]
    lines = item.split("\n")
    end = next(
        (i for i, x in enumerate(lines) if i and x and not x.startswith(" ")), len(lines)
    )  # the item's last line
    return " ".join(re.sub(r"!\[[^\]]*\]\([^)]*\)", "", "\n".join(lines[:end])).split())


def _t30_records():
    from _reproduce import reuse_doc

    return (
        reuse_doc("ibm_fez/t11-day2-monitor.json"),
        reuse_doc("ibm_fez/t11-day3-monitor.json"),
        reuse_doc("ibm_fez/t16-day3-per-shot-read.json"),
        reuse_doc("ibm_fez/t17-long-monitor.json"),
    )


def _rng(vals, nd: int) -> str:
    return f"{_q(min(vals), nd)} to {_q(max(vals), nd)}"


def test_finding_30_the_records():
    """Finding 30's records, each number against the record it quotes or its recompute: test 11's third day (job 1's
    fits beside days 1 and 2, the monitor's verdicts, pairs, time and boundary pair, and the items beside the verdict);
    test 16's per-shot read of it; test 17's jobs from the counts and per shot. Times are rounded to the minute."""
    import math

    import _reuse_runs as rr

    from manacitra import wait

    item = _item30()
    q = _q
    d2, d3, t16, t17 = _t30_records()
    # ruling R3, item 3: finding 29's boundaries in the opening, scoped as finding 29 states them (its table row's
    # "17 of 17 boundaries read NO CHANGE"; test 7's shuffled job BETWEEN (borrowed) at its first, 2.65)
    findings = " ".join((ROOT / "docs" / "findings.md").read_text().split())
    assert (
        "with 17 of 17 boundaries read NO CHANGE" in findings
        and "test 7's job BETWEEN (borrowed) at its first, 2.65" in findings
    )
    # ruling R5, item 1: the boundaries that could be read, counted from test 15's read: 28 monitor boundaries, 17 NO
    # CHANGE (9 on ibm_kingston, 8 on ibm_fez) and 11 NOT READ (all on ibm_kingston), none of those with both spans
    # SHARED
    bounds = archive.load("ibm_fez/t15-error-model-read.json")["archived"]["analysis"]["boundaries"]
    by = {}
    for b_ in bounds:
        by[(b_["word"], b_["processor"])] = by.get((b_["word"], b_["processor"]), 0) + 1
    assert len(bounds) == 28 and by == {
        ("NO CHANGE", "ibm_kingston"): 9,
        ("NO CHANGE", "ibm_fez"): 8,
        ("NOT READ", "ibm_kingston"): 11,
    }
    assert not any(b_["span_words"] == ["SHARED", "SHARED"] for b_ in bounds if b_["word"] == "NOT READ")
    assert (
        "and all seventeen monitor boundaries that could be read returned NO CHANGE under the error of a time average, "
        "nine on ibm_kingston and eight on ibm_fez; the eleven others, on ibm_kingston, were NOT READ, each with a "
        "span not read SHARED, with test 7's shuffled job read beside them at a borrowed correlation time." in item
    )
    assert "every weight boundary" not in item and "17 of 17" not in item
    # the rules and their issues, posted before each run or read
    issues = {"t11": 58, "t16": 67, "t17": 69}
    for rec, t in ((d3, "t11"), (t16, "t16"), (t17, "t17")):
        r_ = rec["meta"]["rule"]
        assert (r_["file"], r_["posted"]["issue"]) == (f"{t}-rule.md", issues[t])
        assert f"[issue {issues[t]}](https://github.com/dogma-guru/manacitra/issues/{issues[t]})" in item
        assert (archive.data_dir() / "ibm_fez" / r_["file"]).is_file()
    assert _utc(d3["meta"]["rule"]["posted"]["created_utc"]) < _utc(d3["meta"]["utc"])
    assert _utc(t16["meta"]["rule"]["posted"]["created_utc"]) < _utc(t16["meta"]["utc"])
    assert _utc(t17["meta"]["rule"]["posted"]["created_utc"]) < _utc(t17["meta"]["utc"])
    assert "(`data/ibm_fez/t11-rule.md`, `t16-rule.md` and `t17-rule.md`)" in item
    # test 11 on a third day
    a3 = d3["archived"]["analysis"]
    j1 = a3["jobs"]["1"]
    P, dec = j1["analysis"]["fits"]["P"]["params"], j1["analysis"]["deciding"]
    spans3 = {j: d3["jobs"][j]["execution_metadata"]["execution_spans"] for j in "123"}
    assert (hhmm(d3["meta"]["utc"]), hhmm(spans3["3"][-1]["stop_utc"] + "Z")) == ("04:09", "04:18")
    stamps = {row["stamp_utc"] for row in d3["calibration_record"]["stamps"]}
    assert stamps == {"2026-10-19T03:21:57Z"}
    assert "(ibm_fez, 04:09 to 04:18 UTC, under one stamp, 03:21:57 UTC)" in item
    gap = a3["gap_between_jobs_2_and_3"]["gap_s_from_the_execution_records"]
    assert q(gap, 1) == "186.6" and "the two jobs 186.6 s apart in the provider's record" in item
    assert j1["verdict"] == "CONFIRMED ON DAY 2" and "Job 1 returned CONFIRMED ON DAY 2" in item
    assert (q(dec["held_out_error_P"], 4), q(dec["held_out_error_S"], 4)) == ("0.0148", "0.1230")
    assert "P's held-out error was 0.0148 against S's 0.1230" in item
    assert [q(x, 2) for x in (P["delta_MHz"] * 1e3, *dec["delta_ci90_kHz"])] == ["44.97", "44.91", "45.02"]
    assert [q(x, 3) for x in (P["b"], *dec["b_ci90"])] == ["0.452", "0.442", "0.462"]
    assert "the split δ 44.97 kHz (90% interval 44.91 to 45.02) and the weight b 0.452 (0.442 to 0.462)" in item
    j2 = d2["archived"]["analysis"]["jobs"]["1"]
    P2, dec2 = j2["analysis"]["fits"]["P"]["params"], j2["analysis"]["deciding"]
    assert [q(x, 2) for x in (P2["delta_MHz"] * 1e3, *dec2["delta_ci90_kHz"])] == ["44.70", "44.65", "44.76"]
    assert [q(x, 3) for x in (P2["b"], *dec2["b_ci90"])] == ["0.466", "0.458", "0.474"]
    t7 = archive.load("ibm_fez/t7-ramsey-xy.json")["archived"]["analysis"]
    P7, dec7 = t7["fits"]["P"]["params"], t7["deciding"]
    assert [q(x, 2) for x in (P7["delta_MHz"] * 1e3, *dec7["delta_ci90_kHz"])] == ["44.82", "44.72", "44.92"]
    assert [q(x, 3) for x in (P7["b"], *dec7["b_ci90"])] == ["0.355", "0.333", "0.377"]
    assert (
        "beside day 2's 44.70 kHz (44.65 to 44.76) and 0.466 (0.458 to 0.474) and day 1's 44.82 kHz (44.72 to 44.92) "
        "and 0.355 (0.333 to 0.377)" in item
    )
    assert {a3["jobs"][j]["phase_verdict"] for j in "23"} == {"QUIET"}
    assert {a3["jobs"][j]["weight_verdict"] for j in "23"} == {"WEIGHT QUIET"}
    assert a3["pooled"] == {"phase": "QUIET", "weight": "WEIGHT QUIET"}
    lab3 = [lab for lab in d3["labels"] if lab["job"] in (2, 3)]
    pairs, t_within = 0, 0.0
    for j in (2, 3):
        idx = [k for k, lab in enumerate(d3["labels"]) if lab["job"] == j]
        labels = [{k: v for k, v in d3["labels"][i].items() if k != "job"} for i in idx]
        ones = [sum(n for key, n in d3["counts"][i].items() if key[-1] == "1") for i in idx]
        ph = wait.monitor_phase(ones, labels, spans3[str(j)], 5.6, shots=1000, **rr.T10_RULE)
        pairs += len(ph["pairs"])
        t_within += ph["within_time_s"]
        if j == 2:
            R0 = a3["R0"]
            w2 = wait.monitor_weight(
                ph, R0["value"], exchange=R0["branches_exchanged"], abs_min=rr.T11_W_MIN, n_se=rr.T10_RULE["n_se"]
            )
            (bp,) = [x for x in w2["pairs"] if (x["k"], x["k1"]) == (99, 100)]
            assert bp["kind"] == "boundary" and (q(bp["dw"], 3), q(bp["threshold"], 3)) == ("−0.072", "0.115")
    assert lab3 and (pairs, q(t_within, 1)) == (287, "161.8")
    assert "no phase switch and no weight switch in 287 consecutive pairs, over 161.8 s within spans" in item
    bt = {j: a3["jobs"][j]["boundary_table"]["boundaries"] for j in "23"}
    pair = [b for b in bt["2"] if (b["k"], b["k1"]) == (99, 100)]
    assert len(pair) == 1 and q(pair[0]["d_w"], 3) == "−0.072"
    tested = [p for j in "23" for p in a3["jobs"][j]["weight"]["switches_w"]]
    assert not tested
    assert "job 2's repeats 99 and 100, whose weight step was −0.072 against a threshold of 0.115" in item
    gaps = [
        (_utc(b["start_utc"] + "Z") - _utc(a["stop_utc"] + "Z")).total_seconds() * 1e3
        for sp in spans3.values()
        for a, b in zip(sp, sp[1:])
    ]
    assert (round(min(gaps)), round(max(gaps))) == (5, 6) and "the gaps between spans were 5 to 6 ms" in item
    big = max((abs(b["d_w"]) / b["se_w"], b["d_w"]) for j in "23" for b in bt[j])
    assert big[0] < 5 and q(big[1], 3) == "−0.072"
    lv = [a3["jobs"][j]["phase"]["levels"] for j in "23"]
    assert [len(x) for x in lv] == [1, 1] and {q(x[0]["mean"], 2) for x in lv} == {"−1.88"}
    lv2 = [d2["archived"]["analysis"]["jobs"][j]["phase"]["levels"][0]["mean"] for j in "23"]
    assert [q(x[0]["mean"] - y, 2) for x, y in zip(lv, lv2)] == ["0.16", "0.20"]
    assert "each monitor job held one level of phase, −1.88 rad, 0.16 and 0.20 rad above day 2's" in item
    w3 = {j: a3["jobs"][j]["weight"]["per_span"] for j in "23"}
    assert [q(x["mean_w"], 3) for x in w3["2"]] == ["0.338", "0.390", "0.327"]
    assert [q(x["mean_w"], 3) for x in w3["3"]] == ["0.341", "0.373", "0.335"]
    assert {q(x["se_propagated"], 3) for j in "23" for x in w3[j]} == {"0.002"}
    assert "0.338, 0.390 and 0.327 in job 2 and 0.341, 0.373 and 0.335 in job 3" in item
    a26 = [x["weighted_mean"] for x in j1["span_readings_A26"]["weight_per_span"]]
    assert [q(x, 3) for x in a26] == ["0.440", "0.521", "0.389"]
    ch = j1["weight_changes_across_boundaries"]["boundaries"]
    assert [q(ch[k]["change"], 3, sign=True) for k in ("first", "second")] == ["+0.102", "−0.169"]
    assert "job 1's weight per span by A26's method was 0.440, 0.521 and 0.389" in item
    assert "+0.102 and −0.169" in item
    # test 16
    a16 = t16["archived"]["analysis"]
    m16 = rr.t16_day3_read(t16, archive.load("ibm_fez/t15-error-model-read.json"), d3)
    sp16 = [s["Y"] for j in m16["jobs"].values() for s in j["spans"]]
    assert hhmm(t16["meta"]["utc"]) == "12:16" and "(no job; read at 12:16 UTC on 19 October)" in item
    assert {a16["jobs"][k]["job_word"] for k in ("d3-job2", "d3-job3")} == {"SHARED"}
    assert {x["word_of_the_ratio"] for x in sp16} == {"SHARED"}
    assert "all six spans with sharing ratios of " + _rng([x["ratio"] for x in sp16], 1) in item
    assert "The span duties were " + _rng([x["duty_b"] for x in sp16], 3) in item
    assert (min(x["lag_1_over_e"] for x in sp16), max(x["lag_1_over_e"] for x in sp16)) == (7, 12)
    assert "the correlation lags 7 to 12 sweeps, τ_c " + _rng([x["tau_c_s"] for x in sp16], 2) + " s" in item
    assert "as a time average " + _rng([x["telegraph_sd"] for x in sp16], 3) in item
    b16 = m16["boundaries"]
    assert {b["word"] for b in b16} == {"NO CHANGE"} and not any(b["word_changes_under_sensitivity"] for b in b16)
    assert "All four boundaries read NO CHANGE (ratios " + _rng([b["ratio"] for b in b16], 2) + ")" in item
    bj = m16["between_jobs"]["rows"][0]
    assert (bj["word"], q(bj["ratio"], 2)) == ("NO CHANGE", "0.17") and "and so did the two jobs (0.17)" in item
    sens = a16["between_jobs"]["rows"][0]["sensitivity"]
    assert {v["word"] for v in sens.values()} == {"NO CHANGE"}
    dm = m16["beside_day_means"]
    assert [q(x, 3) for x in dm["day_mean_duties"] + dm["day_sds"]] == ["0.330", "0.341", "0.020", "0.025"]
    assert q(dm["difference_over_sd"], 2) == "0.34"
    assert "0.330 (sd 0.020) on 17 October and 0.341 (sd 0.025) on 19 October, a difference of 0.34" in item
    mm = m16["beside_middle_minus_ends"]
    assert all(x["middle_minus_mean_of_ends"] > 0 for x in mm)
    assert _rng([x["difference_over_sd"] for x in mm], 2) == "0.41 to 1.11"
    assert "positive in all four, from 0.41 to 1.11 of its sd" in item
    jb = m16["job1_borrowed"]
    assert q(jb["tau_c_borrowed_s"], 3) == "0.219" and [q(x["ratio"], 2) for x in jb["rows"]] == ["1.16", "1.66"]
    assert {x["word"] for x in jb["rows"]} == {"NO CHANGE"}
    assert "(0.219 s), NO CHANGE (borrowed) at 1.16 and 1.66" in item
    # test 17
    a17c = t17["archived"]["analysis_counts"]["jobs"]
    m17 = rr.t17_read(t17)
    sp17 = {k: t17["jobs"][k]["execution_metadata"]["execution_spans"] for k in ("A1", "A2", "B1")}
    assert (hhmm(t17["meta"]["utc"]), hhmm(sp17["B1"][-1]["stop_utc"] + "Z")) == ("17:06", "17:12")
    build = [r_ for r_ in t17["calibration_record"]["stamps"] if r_["kind"] != "watch"]
    assert build and {r_["stamp_utc"] for r_ in build} == {"2026-10-19T16:47:37Z"}
    assert "(ibm_fez, 17:06 to 17:12 UTC, under one stamp, 16:47:37 UTC)" in item
    assert t17["jobs"]["A3"]["not_run"] and not t17["jobs"]["A3"]["decision_before_the_build"]["runs"]
    reps = {k: max(lab["repeat"] or 0 for lab in t17["labels"] if lab["job"] == k) for k in ("A1", "A2", "B1")}
    assert reps == {"A1": 123, "A2": 123, "B1": 298}
    assert sum(lab["job"] == "B1" for lab in t17["labels"]) == 600 and len(sp17["B1"]) == 6
    assert _rng([s["duration_s"] for s in sp17["B1"]], 1) == "27.0 to 27.9"
    assert "which ran as six spans of 27.0 to 27.9 s" in item
    v = {k: a17c[k]["verdicts"] for k in ("A1", "A2", "B1")}
    assert (v["A1"]["phase"], v["A2"]["phase"], v["B1"]["phase"]) == ("SWITCHES AT BOUNDARIES ONLY", "QUIET", "QUIET")
    assert {x["weight_by_pairs"] for x in v.values()} == {"WEIGHT SWITCHES AT BOUNDARIES ONLY"}
    assert [v[k]["weight_by_levels"] for k in ("A1", "A2", "B1")] == ["LEVELS DIFFER AT EVERY BOUNDARY"] * 2 + [
        "LEVELS DIFFER AT SOME"
    ]
    an = {k: a17c[k]["analysis"] for k in ("A1", "A2", "B1")}
    assert sum(x["n_pairs"]["within"] for x in an.values()) == 529 and all(
        x["n_within"] == x["n_within_w"] == 0 for x in an.values()
    )
    assert q(sum(x["within_time_s"] for x in an.values()), 1) == "234.7"
    assert "no switch within a span in 529 consecutive pairs over 234.7 s" in item
    s17 = {k: [s["Y"] for s in m17["jobs"][k]["spans"]] for k in ("A1", "A2", "B1")}
    assert sum(len(x) for x in s17.values()) == 12 and {x["word_of_the_ratio"] for v_ in s17.values() for x in v_} == {
        "SHARED"
    }
    assert "Read per shot, all twelve spans read SHARED." in item
    b17 = m17["boundaries"]
    assert [(b["word"], q(b["ratio"], 2)) for b in b17[:4]] == [
        ("NO CHANGE", "1.25"),
        ("BETWEEN", "2.35"),
        ("NO CHANGE", "1.91"),
        ("NO CHANGE", "0.76"),
    ]
    assert b17[2]["word_changes_under_sensitivity"] == ["tau_minus_1_sweep"]
    assert all(not b["word_changes_under_sensitivity"] for i, b in enumerate(b17) if i != 2)
    assert (
        "one boundary read BETWEEN (A1's second, 2.35) and three NO CHANGE (1.25, 1.91 and 0.76; A2's first reads "
        "BETWEEN at τ_c one sweep shorter)" in item
    )
    assert "the six spans' sharing ratios were " + _rng([x["ratio"] for x in s17["B1"]], 1) in item
    assert "their duties " + ", ".join(q(x["duty_b"], 3) for x in s17["B1"][:-1]) + " and " in item
    assert "τ_c " + _rng([x["tau_c_s"] for x in s17["B1"]], 2) + " s" in item
    assert {b["word"] for b in b17[4:]} == {"NO CHANGE"} and len(b17[4:]) == 5
    assert "all five boundaries read NO CHANGE (" + _rng([b["ratio"] for b in b17[4:]], 2) + "), under both" in item
    bt17 = m17["between_jobs"]
    assert bt17[0]["word"] is None and (bt17[1]["word"], q(bt17[1]["ratio"], 2)) == ("NO CHANGE", "0.45")
    assert [s["w_branch"] for s in m17["jobs"]["A1"]["spans"]] == ["b", "b", "1 - b"]
    assert "A2 to B1 read NO CHANGE (0.45); A1 to A2 was not compared" in item
    mid = [x["mid_sweep_fraction_middle_fifth"] * 100 for v_ in s17.values() for x in v_]
    assert _rng(mid, 1) == "1.0 to 1.6" and "the mid-sweep fraction was 1.0 to 1.6 percent in every span" in item
    acf = [a for x in s17["B1"] for a in x["acf_lags_490_to_510"]]
    assert (q(min(acf), 3), q(max(acf), 3, sign=True)) == ("−0.144", "+0.120")
    assert "at lags 490 to 510 ran from −0.144 to +0.120 across its spans, with no word" in item
    # ruling R3, item 10: A2's first span, the run's lowest duty and its largest sensitivity to the threshold; its
    # counts weight beside it; its boundary word at the threshold of record unchanged
    a2 = s17["A2"][0]
    cw = t17["archived"]["analysis_counts"]["jobs"]["A2"]["analysis"]["weight_per_span"][0]["mean_w"]
    assert (q(a2["duty_b"], 3), q(a2["duty_b_at_threshold_20_80"], 3), q(cw, 3)) == ("0.142", "0.446", "0.144")
    every = [x for v_ in s17.values() for x in v_]
    sens = [abs(x["duty_b_at_threshold_20_80"] - x["duty_b"]) for x in every]
    assert len(every) == 12 and min(x["duty_b"] for x in every) == a2["duty_b"] and max(sens) == sens[len(s17["A1"])]
    rb = t17["archived"]["per_shot_read"]["boundaries"][2]
    assert (rb["job"], rb["spans"], rb["word"], b17[2]["word"]) == ("A2", [0, 1], "NO CHANGE", "NO CHANGE")
    assert (
        "A2's first span, the lowest duty of the run, reads 0.142 at the rule's threshold and 0.446 at the 20th to "
        "80th, the largest sensitivity of the run's spans." in item
    )
    assert (
        "A NO CHANGE carries no evidence of a change in the duty" in item and "does not show the duties equal" in item
    )
    # the three runs on one table, and the correlation time
    day2 = m16["day2"]
    jobs3 = m16["between_jobs"]["jobs"]
    b1 = m17["between_jobs_job_rows"]["B1"]
    assert [q(x, 3) for x in (dm["day_mean_duties"][0], dm["day_mean_duties"][1], b1["job_mean_w_duty"])] == [
        "0.330",
        "0.341",
        "0.313",
    ]
    assert q(b1["job_sd"], 3) == "0.024"
    med2 = [float(np.median([s["Y"]["tau_c_s"] for s in day2[k]["spans"]])) for k in ("t11-job2", "t11-job3")]
    assert [q(x, 3) for x in med2] == ["0.137", "0.183"]
    assert [q(x["tau_c_median_s"], 3) for x in jobs3] == ["0.193", "0.248"] and q(b1["tau_c_median_s"], 3) == "0.208"
    sp2 = {j: d2["jobs"][j]["execution_metadata"]["execution_spans"] for j in "23"}
    assert (hhmm(sp2["2"][0]["start_utc"] + "Z"), hhmm(sp2["3"][-1]["stop_utc"] + "Z")) == ("20:01", "20:06")
    assert (hhmm(spans3["2"][0]["start_utc"] + "Z"), hhmm(spans3["3"][-1]["stop_utc"] + "Z")) == ("04:12", "04:18")
    assert (hhmm(sp17["B1"][0]["start_utc"] + "Z"), hhmm(sp17["B1"][-1]["stop_utc"] + "Z")) == ("17:10", "17:12")
    h1 = (_utc(spans3["2"][0]["start_utc"] + "Z") - _utc(sp2["3"][-1]["stop_utc"] + "Z")).total_seconds() / 3600
    h2 = (_utc(sp17["B1"][0]["start_utc"] + "Z") - _utc(spans3["3"][-1]["stop_utc"] + "Z")).total_seconds() / 3600
    assert (round(h1), round(h2)) == (32, 13)
    for row in (
        "| test 11, day 2, jobs 2 and 3 | 17 October, 20:01 to 20:06 | 0.330 | 0.020 | 0.137 and 0.183 s |",
        "| test 11, day 3, jobs 2 and 3 | 19 October, 04:12 to 04:18, about 32 hours later | 0.341 | 0.025 | 0.193 and "
        "0.248 s |",
        "| test 17, job B1 | 19 October, 17:10 to 17:12, about 13 hours later | 0.313 | 0.024 | 0.208 s |",
    ):
        assert row in item, row
    # the correlation time per span on each day and the job medians, by the author's ruling R1, Q1: 19 October's spans
    # (day 3 and test 17's three jobs) reach below 17 October's highest, so the ranges overlap
    tau17 = [s["Y"]["tau_c_s"] for k in ("t11-job2", "t11-job3") for s in day2[k]["spans"]]
    tau19 = [x["tau_c_s"] for x in sp16] + [x["tau_c_s"] for k in ("A1", "A2", "B1") for x in s17[k]]
    meds = [*med2, *(x["tau_c_median_s"] for x in jobs3)]
    meds += [m17["between_jobs_job_rows"][k]["tau_c_median_s"] for k in ("A1", "A2", "B1")]
    assert (len(tau17), len(tau19), len(meds)) == (6, 18, 7)
    assert (_rng(tau17, 3), _rng(tau19, 3), _rng(meds, 3)) == ("0.121 to 0.191", "0.143 to 0.349", "0.137 to 0.248")
    assert min(tau19) < max(tau17)
    assert (
        "The correlation time per span was 0.121 to 0.191 s on 17 October and 0.143 to 0.349 s on 19 October, with "
        "job medians of 0.137 to 0.248 s. The ranges overlap, and no rule on the record tests a change in it." in item
    )
    assert "moved" not in item and "near 0.2 s" not in item
    assert math.isfinite(b1["job_sd"])


def test_finding_30_the_two_estimators():
    """Ruling R3, item 6, as the author amended it: in "What it has not shown", the monitor's weight per span (test
    11's on day 3; test 12's analysis from the counts in test 17) against the per-shot duty on the weight's branch,
    over finding 30's eighteen monitor spans: less than 0.015 on the seventeen read on the b branch, and less than
    0.012 on finding 29's twelve, each recomputed unrounded (ruling R5, item 3); on the eighteenth, A1's last span,
    which the per-shot read places on the 1 - b branch, the monitor's 0.540 stands 0.066 from the duty on that branch
    (0.474) and 0.014 from the raw duty (0.526), unchanged."""
    _, d3, t16, t17 = _t30_records()
    rows = []
    for j, k in (("2", "d3-job2"), ("3", "d3-job3")):
        w = [s["mean_w"] for s in d3["archived"]["analysis"]["jobs"][j]["weight"]["per_span"]]
        spans = t16["archived"]["analysis"]["jobs"][k]["qubits"]["143"]["waits"]["monitor"]["spans"]
        assert len(w) == len(spans) == 3
        rows += [(k, i, w[i], s) for i, s in enumerate(spans)]
    for k in ("A1", "A2", "B1"):
        w = [s["mean_w"] for s in t17["archived"]["analysis_counts"]["jobs"][k]["analysis"]["weight_per_span"]]
        spans = t17["archived"]["per_shot_read"]["jobs"][k]["qubits"]["143"]["waits"]["monitor"]["spans"]
        assert len(w) == len(spans)
        rows += [(k, i, w[i], s) for i, s in enumerate(spans)]
    assert len(rows) == 18
    (other,) = [r for r in rows if r[3]["w_branch"] != "b"]
    assert (other[0], other[1], other[3]["w_branch"]) == ("A1", 2, "1 - b")
    seventeen = [abs(w - s["w_duty"]) for _, _, w, s in rows if s["w_branch"] == "b"]
    assert len(seventeen) == 17 and _q(max(seventeen), 4) == "0.0141" and max(seventeen) < 0.015  # ruling R5, item 3
    # finding 29's twelve monitor spans of 143, as finding 29's test reads them: the duty on the weight's branch against
    # the published weight per span
    f15 = archive.load("ibm_fez/t15-error-model-read.json")["archived"]["analysis"]
    pub = {
        (jk, s_): w_
        for jk, xs in f15["published_weight_level_changes"].items()
        for x in xs
        for s_, w_ in zip(x["spans"], x["w"])
    }
    twelve = [
        abs(sp["w_duty"] - pub[(jk, sp["span"])])
        for jk, wk in (
            ("t11-job2", "monitor"),
            ("t11-job3", "monitor"),
            ("t12-job1", "monitor"),
            ("t14-job1", "antiphase"),
        )
        for sp in f15["jobs"][jk]["qubits"]["143"]["waits"][wk]["spans"]
    ]
    assert len(twelve) == 12 and _q(max(twelve), 4) == "0.0112" and max(twelve) < 0.012
    w, s = other[2], other[3]
    assert (_q(w, 3), _q(s["w_duty"], 3), _q(s["Y"]["duty_b"], 3)) == ("0.540", "0.474", "0.526")
    assert (_q(abs(w - s["w_duty"]), 3), _q(abs(w - s["Y"]["duty_b"]), 3)) == ("0.066", "0.014")
    shown = " ".join((ROOT / "docs" / "findings.md").read_text().split()).split("## What it has not shown", 1)[1]
    assert (
        "the duty of the per-shot record agrees with the second by less than 0.012 on finding 29's twelve monitor "
        "spans of 143, and by less than 0.015 on seventeen of finding 30's eighteen (largest 0.0112 and 0.0141), each "
        "on the weight's branch; on the eighteenth, A1's last span, the per-shot read places the duty on the other "
        "branch, and the monitor's 0.540 stands 0.066 from the duty on that branch (0.474) and 0.014 from the raw "
        "duty (0.526)." in shown
    )
    assert "within 0.011 on finding 29's" not in shown and "within 0.014 on seventeen" not in shown


def test_the_long_duration_form():
    """Ruling R3, item 9, as the author amended it on 20 October 2026: the method page and `time_average_sd`'s
    docstring say the error of a time average is the long-duration form, give the exact variance, and bound the
    exact sd's shortfall, recomputed here from the published records over every span that carries the error (test 15's
    read for finding 29; tests 16 and 17 for finding 30): less than 2.6 percent on finding 29's, the most, 2.53, at test
    14's antiphase wait (job 1, third span); less than 1.6 percent on finding 30's, the most, 1.51, at test 17's A2,
    third span. Every recorded sd is the long-duration form; the code is unchanged."""
    import math

    def shortfalls(jobs: dict) -> list:
        out = []
        for jk, job in jobs.items():
            for qk, qubit in job["qubits"].items():
                for wk, w in qubit["waits"].items():
                    for i, s in enumerate(w["spans"]):
                        for quad in ("Y", "X"):
                            y = s.get(quad)
                            if not (isinstance(y, dict) and y.get("tau_c_s") and y.get("telegraph_sd") is not None):
                                continue
                            b, tau, t = y["duty_b"], y["tau_c_s"], y["duration_s"]
                            long_form = math.sqrt(2 * b * (1 - b) * tau / t)
                            assert math.isclose(y["telegraph_sd"], long_form, rel_tol=1e-9)
                            x = tau / t
                            out.append((1 - math.sqrt(1 - x * (1 - math.exp(-1 / x))), (jk, qk, wk, i, quad)))
        return out

    _, _, t16, t17 = _t30_records()
    f29 = shortfalls(archive.load("ibm_fez/t15-error-model-read.json")["archived"]["analysis"]["jobs"])
    f30 = shortfalls(t16["archived"]["analysis"]["jobs"]) + shortfalls(t17["archived"]["per_shot_read"]["jobs"])
    (m29, at29), (m30, at30) = max(f29), max(f30)
    assert (len(f29), len(f30)) == (37, 36)  # finding 30: eighteen spans, each in Y and X
    assert 100 * m29 < 2.6 and _q(100 * m29, 2) == "2.53" and at29 == ("t14-job1", "143", "antiphase", 2, "Y")
    assert 100 * m30 < 1.6 and _q(100 * m30, 2) == "1.51" and at30 == ("A2", "143", "monitor", 2, "Y")
    method = " ".join((ROOT / "docs" / "method.md").read_text().split())
    assert (
        "This is the long-duration form. For a span of duration T, the variance of the time average of a stationary "
        "two-state process with exponential correlation is 2 b(1 − b)[τ_c/T − (τ_c/T)²(1 − e^(−T/τ_c))]; on the spans "
        "of finding 29 the exact sd is smaller by less than 2.6 percent, the most at test 14's antiphase wait, and on "
        "those of finding 30 by less than 1.6 percent. The three-sweep ceiling is an operational floor on the lag, not "
        "a confidence bound on τ_c." in method
    )
    doc = " ".join(wait.time_average_sd.__doc__.split())
    assert (
        "This is the long-duration form. For a span of duration T, the variance of the time average of a stationary "
        "two-state process with exponential correlation is 2 b (1 - b) [tau_c / T - (tau_c / T)^2 (1 - exp(-T / "
        "tau_c))]; on the spans of finding 29 the exact sd is smaller by less than 2.6 percent, the most at test 14's "
        "antiphase wait, and on those of finding 30 by less than 1.6 percent. The three-sweep ceiling is an "
        "operational floor on the lag, not a confidence bound on tau_c." in doc
    )


def test_finding_30_records_name_their_reports():
    """A28 R1, Q14: each of finding 30's three records names its hand-back's report, which is not published, by
    SHA-256 under meta.not_copied (day 3's by the author's ruling, with numbers-t11-day3.json, the output of its kept
    numbers_t11_day3.py, so that the list names every hand-back file the record does not carry, as tests 16 and 17's
    do); day 2's record stays as released in 0.9.0."""
    for name, report, digest in (
        (
            "t11-day3-monitor.json",
            "report-t11-day3.md",
            "fcbd85fec7ccd0e6b6005b4c54c966503684a7023313e2b4bc269a75337d124a",
        ),
        (
            "t16-day3-per-shot-read.json",
            "report-t16.md",
            "42fcec518834c4b3f14f4da4fb63cb7bf0a9e2b08f4e2d75e121c6dcb9c1e5b0",
        ),
        ("t17-long-monitor.json", "report-t17.md", "71f523c26b6c4eac345e51c553b2f38cab6f408e25ad9aac7856b0d4c3d1fab7"),
    ):
        rows = {x["file"]: x["sha256"] for x in archive.load(f"ibm_fez/{name}")["meta"]["not_copied"]}
        assert rows[report] == digest, name
        assert not (ROOT / "data" / "ibm_fez" / report).exists()
    day3 = {x["file"] for x in archive.load("ibm_fez/t11-day3-monitor.json")["meta"]["not_copied"]}
    assert day3 == {"report-t11-day3.md", "numbers-t11-day3.json"}
    assert "not_copied" not in archive.load("ibm_fez/t11-day2-monitor.json")["meta"]


def test_finding_30_the_middle_test():
    """Finding 30's middle test, against test 17's rule, its record and the note's excerpt; each rule's error; the
    fixed sentences; and the words the kickoff keeps out of the finding's own prose."""
    import re

    import _reuse_runs as rr

    item = _item30()
    q = _q
    _, d3, t16, t17 = _t30_records()
    rule17 = (archive.data_dir() / "ibm_fez" / "t17-rule.md").read_text()
    excerpt = (archive.data_dir() / "ibm_fez" / "t17-middle-note-excerpt.md").read_text()
    line = (
        "- **The middle span (not a test):** middle minus ends positive in all four monitor jobs, 0.41 to 1.11 "
        "telegraph sd."
    )
    assert excerpt.count(line) == 1 and f"> {line}\n" in excerpt
    assert "31808acd2d115991f4695cbccafe84db075e6a2eea2647ca01774ce5e897352d" in excerpt
    assert "It was written on 19 October 2026, before test 17's rule was hashed." in excerpt
    assert "The rest of the file is a working read kept outside the repository." in excerpt
    quoted = line[2:].replace("**", "")
    assert f'"{quoted}"' in item and "`data/ibm_fez/t17-middle-note-excerpt.md`" in item
    assert "about 1.3" in rule17 and "higher by 0.05" in rule17
    assert "about 1.3 in expected Z for a middle higher by 0.05" in item
    assert "**MIDDLE HIGH** if Z ≥ 2.0; **NOT SEEN** if Z < 1.0" in rule17
    assert "MIDDLE HIGH at 2.0 or more, NOT SEEN under 1.0" in item
    m = rr.t17_read(t17)["middle_test"]
    assert [q(x["C"], 3, sign=True) for x in m["jobs"]] == ["−0.229", "+0.030", "+0.013"]
    assert (q(m["pooled"]["Z"], 2), m["pooled"]["word"]) == ("−0.97", "NOT SEEN")
    assert "The three jobs gave contrasts of −0.229, +0.030 and +0.013, and Z = −0.97: NOT SEEN." in item
    desk = t17["archived"]["desk"]
    assert desk["meta"]["sets"] == desk["n_sets_with_a_Z"] == 2000
    assert q(desk["false_alarm_rate_MIDDLE_HIGH"] * 100, 2) == "1.90"
    assert "2,000 synthetic sets of this run's jobs with no middle effect read MIDDLE HIGH in 1.90 percent" in item
    assert (
        "At the size noticed, the pattern was not seen; a smaller difference is not excluded by one run at this power."
        in item
    )
    # each rule's error
    a17c = t17["archived"]["analysis_counts"]["jobs"]
    lc = [abs(x["in_errors"]) for k in ("A1", "A2", "B1") for x in a17c[k]["analysis"]["level_changes"]]
    counted = [x for x in lc if x > 5]
    assert (q(min(counted), 1), q(max(counted), 1)) == ("9.8", "54.7") and len(lc) == 9
    b = rr.t17_read(t17)["boundaries"]
    assert _rng([x["ratio"] for x in b], 2) == "0.01 to 2.35"
    assert "the level changes were 9.8 to 54.7 of it, where test 15's error of a time average read all nine" in item
    assert "√(2 b(1 − b) τ_c / T) (`telegraph_sd` in their records)" in item
    assert "which the desk check measured at 1.90 percent" in item
    # the closing, and the words kept out of the finding's own prose
    assert (
        "They name no cause for the duty, the sharing, the switching, a difference between days or the spread of the "
        "X levels" in item
    )
    assert item.rstrip().endswith("Manacitra does not rank machines.")
    prose = item.replace(f'"{quoted}"', "").replace("`telegraph_sd`", "")
    for w in (
        "telegraph",
        "parity",
        "defect",
        "proof",
        "proves",
        "reveals",
        "kill",
        "benchmark",
        "pre-registered",
        "confirmed",
        "validated",
        "verified",
        "passed",
        "constant",
        "absent",
        "Mantri",
        "allowance",
        "instance",
        "open plan",
        "pay-as-you-go",
        "cost",
    ):
        assert not re.search(rf"\b{w}", prose), w
    # "first" never of a model; of a boundary or a span it stands ("A2's first reads"; "A2's first span", ruling R3,
    # item 10)
    assert not re.search(r"\bfirst\b(?! reads| span)", prose), "first"
    assert "—" not in item and "–" not in item


def test_finding_30_pictures():
    """Finding 30's two pictures: made from the data by docs/make_diagrams.py, referenced from finding 30, their alt
    text carrying the numbers they show, each checked against the records."""
    import re

    findings = (ROOT / "docs" / "findings.md").read_text()
    raw = findings.split('<a id="finding-30"></a>', 1)[1].split("\n## ", 1)[0]
    _, _, t16, t17 = _t30_records()
    b1 = t17["archived"]["per_shot_read"]["jobs"]["B1"]["qubits"]["143"]["waits"]["monitor"]["spans"]
    alt = " ".join(raw.split("![", 1)[1].split("](diagrams/sweep-series-143.svg)", 1)[0].split())
    assert (DIAGRAMS / "sweep-series-143.png").is_file()
    triples = "; ".join(
        f"{_q(s['Y']['duty_b'], 3)}, {_q(s['Y']['tau_c_s'], 2)} s, {_q(s['Y']['ratio'], 1)}" for s in b1
    )
    assert f"the span's duty, correlation time and sharing ratio: {triples}." in alt
    n_rows = [s["Y"]["n_rows"] for s in b1]
    assert (min(n_rows), max(n_rows)) == (48, 50) and "its 48 to 50 whole repeats at each of 1,000 returned" in alt
    text = svg_text(DIAGRAMS / "sweep-series-143.svg")
    assert "test 17's long job" in text and "every span SHARED" in text
    alt2 = " ".join(
        raw.split("](diagrams/sweep-series-143.svg)", 1)[1]
        .split("![", 1)[1]
        .split("](diagrams/duties-by-span-143.svg)", 1)[0]
        .split()
    )
    d3 = t16["archived"]["analysis"]["jobs"]
    w3 = [s["w_duty"] for k in ("d3-job2", "d3-job3") for s in d3[k]["qubits"]["143"]["waits"]["monitor"]["spans"]]
    w17 = [s["w_duty"] for s in b1]
    assert (
        "(" + ", ".join(_q(x, 3) for x in w3[:-1]) + f" and {_q(w3[-1], 3)}), their mean {_q(np.mean(w3), 3)}" in alt2
    )
    assert (
        "(" + ", ".join(_q(x, 3) for x in w17[:-1]) + f" and {_q(w17[-1], 3)}), their mean {_q(np.mean(w17), 3)}"
        in alt2
    )
    assert (DIAGRAMS / "duties-by-span-143.png").is_file()
    text = svg_text(DIAGRAMS / "duties-by-span-143.svg")
    assert "NO CHANGE at every boundary of both runs" in text and re.search(r"mean 0\.341", text)


def test_finding_30_beside_the_finding():
    """Amendment A28, 2b, 2e and 2f: the rules of tests 16 and 17 byte for byte, with the hashes their issues carry;
    what has not been shown, its three new bullets and the returned-order bullet's new sentence; the README's thread row
    and limits line; the method's two subsections, naming functions the package has; the reproduce page's commits and
    lines; the kickoffs rows; the long documentation's row; and the build report's section, with no CI run ID."""
    import hashlib
    import re

    from manacitra import wait

    _, d3, t16, t17 = _t30_records()
    for rec, name, sha, issue in (
        (t16, "t16-rule.md", "1162fb2749b74caf21a647a8bca0743293c4ca469576a5c9ee86886b411905d8", 67),
        (t17, "t17-rule.md", "1133816b66d2a4602771d8b8e9a38e222e030ef1783a0b438c638eba5d2c6d0c", 69),
    ):
        text = (archive.data_dir() / "ibm_fez" / name).read_bytes()
        assert hashlib.sha256(text).hexdigest() == sha == rec["meta"]["rule"]["sha256"], name
        assert rec["meta"]["rule"]["posted"]["issue"] == issue, name
    assert (t16["meta"]["rule"]["sha256"], t17["meta"]["rule"]["sha256"]) == (
        "1162fb2749b74caf21a647a8bca0743293c4ca469576a5c9ee86886b411905d8",
        "1133816b66d2a4602771d8b8e9a38e222e030ef1783a0b438c638eba5d2c6d0c",
    )
    findings = " ".join((ROOT / "docs" / "findings.md").read_text().split())
    shown = findings.split("## What it has not shown", 1)[1]
    for bullet in (
        "- **One qubit, three days.** The duty measurements and boundary tests are a record of ibm_fez's 143 at one "
        "wait on 17 to 19 October 2026; nothing about other qubits, waits, days or processors.",
        "- **One scored design.** Sandhi version 4.1 has been scored on one run of one design (D2). Its other bets "
        "(D1) are not yet scored, and a model's record on one run is a record, not a calibration.",
        "- **The middle test had modest power.** NOT SEEN counts against a difference of 0.05 and says little about "
        "smaller ones.",
        "Test 17's read reports the autocorrelation of its long job's sweep means at lags 490 to 510, from −0.144 to "
        "+0.120 across its six spans, with no word ([issue 69](https://github.com/dogma-guru/manacitra/issues/69)).",
    ):
        assert bullet in shown, bullet[:40]
    readme = " ".join((ROOT / "README.md").read_text().split())
    assert "| The duty across spans, jobs and days | [30](docs/findings.md#finding-30) | ibm_fez |" in readme
    assert (
        "- **One qubit, one processor, for finding 30.** Finding 30 is from two runs on ibm_fez's qubit 143" in readme
    )
    # by the author's rulings R1, Q1 and Q2: no switching-time clause in row eleven; the model's records named as
    # tests 10 to 15 and test 11's third day, since test 16 is a read of day 3, not a separate record
    assert (
        "and the monitor means of runs on 17 and 19 October were 0.330, 0.341 and 0.313; a pattern noticed in the "
        "published weights was not seen on new data;" in readme
    )
    assert "switching time" not in readme and "tests 10 to 16" not in readme
    assert (
        "the desk model Sandhi's versions 4 and 4.1 describe the records of tests 10 to 15 and of test 11's third day "
        "and no others, and version 4.1 has been scored on one run." in readme
    )
    sandhi = " ".join((ROOT / "data" / "desk" / "sandhi" / "README.md").read_text().split())
    assert "the per-shot records of tests 10 to 15 and of test 11's third day" in sandhi
    assert "tests 10 to 16" not in sandhi
    method = " ".join((ROOT / "docs" / "method.md").read_text().split())
    assert "### Reading a span per shot" in method and "### A test fixed after a pattern is noticed" in method
    for f in ("sweep_series", "sharing_ratio", "two_state_reading", "time_average_sd", "boundary_ratio"):
        assert f"`{f}`" in method or f"`manacitra.wait.{f}`" in method, f
        assert callable(getattr(wait, f)), f
    m = method.split("### Reading a span per shot", 1)[1]
    assert "√(2 b(1 − b) τ_c / T)" in m and "a lag under three sweeps read at three, as a ceiling" in m
    assert not re.search(r"\b(SHARED|NO CHANGE|BETWEEN|NOT SEEN|MIDDLE HIGH)\b", m)  # the words stay in the findings
    rep = " ".join((ROOT / "docs" / "reproduce.md").read_text().split())
    assert d3["jobs"]["2"]["built_from"]["manacitra_commit"].startswith("b782d00")
    assert t17["jobs"]["A1"]["built_from"]["manacitra_commit"].startswith("09bdebd")
    assert t17["jobs"]["B1"]["built_from"]["manacitra_commit"].startswith("b782d00")
    assert "its circuits built unedited at `b782d00`, the commit of v0.7.0" in rep
    assert "test 17 built its short monitors with the v0.8.0 release (`09bdebd`) and its long monitor with" in rep
    assert '`pytest tests/test_reproduction.py -k "third or 16 or 17"`' in rep
    assert (
        "`python -I -B score_model_01_v4_1.py --job B1,shots-t17-B1.npz,shots-t17-B1-meta.json,counts-t17-B1.json"
        in rep
    )
    kick = (ROOT / "docs" / "kickoffs.md").read_text()
    for name in ("test 11 on a third day", "test 16", "test 17"):
        assert any(x.startswith(f"| {name}, 19 October 2026 |") for x in kick.splitlines()), name
    index = (ROOT / "docs" / "index.md").read_text()
    assert (
        "| ibm_fez, test 11 on a third day and tests 16 and 17:" in index and "`t16_day3_read` and `t17_read`" in index
    )
    br = (ROOT / "build-report.md").read_text()
    sec = br.split("## 49. Amendment A28:", 1)[1]
    assert not re.search(r"\b\d{10,11}\b", sec)  # no CI run IDs
    assert "—" not in sec and "–" not in sec


def test_finding_30_the_desk_model():
    """Finding 30's desk model, versions 4 and 4.1: against their kickoffs (published, the service's name replaced),
    their posted issues, version 4's scorecard on day 3 and version 4.1's on test 17's long job (recounted from its
    published files, ruling R3, item 4), and the three sentences its report carries."""
    import json

    item = _item30()
    sandhi = archive.data_dir() / "desk" / "sandhi"
    k4 = (sandhi / "kickoffs" / "kickoff-model-01-v4-2026-10-18.md").read_text()
    k41 = (sandhi / "kickoffs" / "kickoff-model-01-v4.1-errata-2026-10-19.md").read_text()
    assert "fixed whole-repeat counts of 49, 50, 49 per span" in k41 and "48 or 49 whole repeats" in k41
    assert "a list of nine donor sweep times compared exactly" in k41
    assert (
        "the template fixed whole repeats of 49 and 50 per span, where the 1,000-shot monitor jobs keep 48 or 49 once "
        "straddling repeats are left out, and it compared sweep times with a list of nine exactly" in item
    )
    assert "widened by 10 percent on each side" in k41 and "widened by a tenth at each end (C2)" in item
    assert (
        "tests 10 to 15" in k4 and "fitted on the desk on 18 October to the per-shot records of tests 10 to 15" in item
    )
    for n in (66, 68):
        assert f"[issue {n}](https://github.com/dogma-guru/manacitra/issues/{n})" in item
    card16 = json.loads((sandhi / "v4" / "scorecard-t16.json").read_text())
    assert {f["status"] for f in card16["families"]} == {"not fully testable"}
    assert sum(f["bets_scored"] for f in card16["families"]) == 0
    card = json.loads((sandhi / "v4.1" / "scorecard-t17.json").read_text())
    # ruling R3, item 4: the scorecard's numbers recounted from its published files, then the stored summaries
    # against the recount
    import _reuse_runs as rr

    calib = json.loads((sandhi / "v4.1" / "scorecard-t17.calibration.json").read_text())
    rc = rr.scorecard_t17_recount(card, calib)
    fam = rc["families"]
    got = [(fam[k]["misses"], fam[k]["bets"], fam[k]["cutoff"]) for k in ("duty", "correlation", "emissions")]
    assert got == [(0, 12, 5), (0, 24, 9), (2, 4, 3)] and not any(f["counts_against"] for f in fam.values())
    assert rr.scorecard_t17_differences(card, calib) == []
    assert (
        "duty, 0 misses of 12 (cutoff 5); correlation, 0 of 24 (cutoff 9); emissions, 2 of 4 (cutoff 3), the two "
        "misses the X quadrature's two levels" in item
    )
    missed = sorted(q_ for (q_, _), inside in rc["inside"].items() if q_.startswith("q_") and not inside)
    assert missed == ["q_H_X", "q_L_X"], missed
    assert (rc["lr_probability"], rc["lr_trials"]) == (0.62, 100)
    (actual,) = [x for x in card["scenario_scores"] if x["scenario"] == "actual"]
    (lr,) = [e for e in actual["probability_events"] if e["prediction"] == "any_LR_reject_probability"]
    assert (lr["probability"], lr["observed"], card["any_monitor_boundary_LR_p_under_0p01"]) == (0.62, False, False)
    assert "no likelihood rejection at 1 percent, against its stated probability of 0.62 for any" in item
    assert "D1 is not yet scored." in item
    rep = (sandhi / "v4.1" / "report-model-01-v4.1.md").read_text()
    for s in (
        "The model is a kinetic description; it names no cause.",
        "The sweep clock is the returned order; seconds are conditional on that order being chronological.",
        "The predictions are the model's, written before the run they predict, and they are what can count against it.",
    ):
        assert s in rep and f'"{s}"' in item


def _round5c():
    import json

    root = archive.data_dir() / "desk" / "t7-power-check-round5c"
    return root, (root / "README.md").read_text(), json.loads((root / "compare-t7v51-round5c.json").read_text())


def test_the_round_5c_folder():
    """Amendment A28, section 4 (the author's answer 3 and ruling of 19 October 2026): round 5c beside round 5b. Every
    file the folder's README lists has the SHA-256 it gives, as published and as handed back; no file names the second
    machine; and the README's sentences of computed fact hold on the published comparison: KEPT on both machines, 106
    of 117; 8 of 27,000 draws differing in verdict, all at tau 150 us and delta 30 kHz, each with one machine's P fit
    in a distant minimum; at the two points with lines at 25 and 125 kHz, S's held-out error differing while every
    chi-square agrees; no point's 80% test moving."""
    import hashlib
    import re

    root, readme, cmp_ = _round5c()
    rows = re.findall(r"^\| `([^`]+)` \| [^|]+ \| `([0-9a-f]{64})` \| (?:`([0-9a-f]{64})`|the same) \|$", readme, re.M)
    assert len(rows) == 6
    for name, handed, published in rows:
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == (published or handed), name
    names = {p.name for p in root.iterdir() if not archive.is_bundle(p)}
    assert names == {n for n, *_ in rows} | {"README.md"}
    for p in root.iterdir():
        assert not re.search(r"d[o]gma", p.read_text(), re.I), p.name
    assert "`f37ca5ccb03e9a3d22b62a17011a32d8296892624d5ae0866c7ba5f9d7f9dd45`" in readme
    assert "`663280741fe5dcb6728e4bca5ef55afc759dac5823225b02981bd88929e4b41a`" in readme
    flat = " ".join(readme.split())
    for k in ("keep_round5c", "keep_main"):
        kp = cmp_[k]
        assert (kp["verdict"], kp["passing"], kp["counted_written"], kp["needed"]) == ("KEPT", 106, 117, 88)
    assert "KEPT on both machines: 106 of the 117 counted points" in flat
    grid = {}
    tables = (root / "tables-t7v51-on-round5c-draws.md").read_text()
    for m in re.finditer(r"^\| (\d+) \| (\d+) \| (\d+) \| (\d+) \|", tables, re.M):
        grid[int(m.group(1))] = (int(m.group(3)), int(m.group(4)))
    assert len(grid) == 135
    diff = [(p["index"], d) for p in cmp_["points"] for d in p["draws_verdict_differs_detail"]]
    assert cmp_["draws_whose_verdict_differs"] == len(diff) == 8
    assert {grid[i] for i, _ in diff} == {(150, 30)}
    chi = [sorted((d["round5c_fit"]["chi2_P"], d["main_fit"]["chi2_P"])) for _, d in diff]
    assert min(c[1] for c in chi) > 10_000 and max(c[0] for c in chi) < 80
    assert (round(min(c[1] for c in chi)), round(max(c[1] for c in chi))) == (10614, 19473)
    assert (round(min(c[0] for c in chi)), round(max(c[0] for c in chi))) == (44, 75)
    assert "8 of the 27,000 draws differ in verdict, all at τ = 150 µs and δ = 30 kHz" in flat
    assert "(P's χ² of 10,614 to 19,473 there, against 44 to 75 on the other)" in flat
    two = [p for p in cmp_["points"] if p["index"] in (118, 133)]
    assert [grid[p["index"]] for p in two] == [(60, 50), (150, 50)]
    assert all(
        p["largest_abs_difference"]["chi2_S"] < 3e-6 and p["largest_abs_difference"]["chi2_P"] < 1e-9 for p in two
    )
    assert all(p["draws_verdict_differs"] == [] for p in two)
    assert "while every χ² agrees to 3·10⁻⁶" in flat
    fr = [p for p in cmp_["points"] if not p["fractions_equal"]]
    assert [p["index"] for p in fr] == [42, 86, 87, 132]
    assert "No verdict moved:" in flat and "—" not in readme and "–" not in readme
    # by rulings R2 and R3: the report, written before the trace and published as handed back, calls the gaps a fact
    # not traced, and says the simulated data are the same on both machines, from S's chi-square on the fit waits; the
    # README says both, directly after the paragraph that traces the gaps
    report = " ".join((root / "report-t7v51-round5c.md").read_text().split())
    assert "a fact, not traced" in report
    assert "The simulated data are the same on both machines: S's χ² on the fit waits agrees" in report
    assert (
        "fails it on the other. The report beside this file, written before that explanation, calls these gaps a fact "
        "not traced; the third sentence above is the trace, made from the two result files after the report. Its "
        "sentence that the simulated data are the same on both machines rests on S's χ² over the fitted waits; at the "
        "two points named above the held-out counts differ, as the third sentence says. **The files.**" in flat
    )


ROUND5C = __import__("os").environ.get("MANACITRA_ROUND5C")


@pytest.mark.skipif(not ROUND5C, reason="needs both rounds' result files (MANACITRA_ROUND5C, a folder holding them)")
def test_the_round_5c_gaps_are_whole_counts():
    """Amendment A28, section 4, sentence 3, recounted from the two result files, attached to release 0.8.0 and to be
    attached to 0.10.0: at the two points with lines at 25 and 125 kHz, 393 draws differ in S's held-out error, each
    gap a whole multiple of 1/192,000 (64 held-out points of 3,000 shots) to within 0.05 of one; the true probability
    is exactly one half at six held-out waits, where the 50 kHz factor of the two lines' sum is zero."""
    import hashlib
    import json
    import math

    folder = Path(ROUND5C)
    files = {"results-t7v51.jsonl": "27c29bc2c242312ff9b2ab3b22c987263aa2900ebdcf966c24e0fcc1369b1a48"}
    files["results-t7v51-round5c.jsonl"] = "f37ca5ccb03e9a3d22b62a17011a32d8296892624d5ae0866c7ba5f9d7f9dd45"
    load = {}
    for name, sha in files.items():
        b = (folder / name).read_bytes()
        assert hashlib.sha256(b).hexdigest() == sha, name
        load[name] = {r["index"]: r for r in map(json.loads, b.decode().splitlines()) if r}
    main, second = load["results-t7v51.jsonl"], load["results-t7v51-round5c.jsonl"]
    gaps = []
    for i in (118, 133):
        dm = {r["draw"]: r for r in main[i]["draws"]}
        for r in second[i]["draws"]:
            g = r["mae_S"] - dm[r["draw"]]["mae_S"]
            if abs(g) > 1e-6:
                gaps.append(g * 192_000)
    assert len(gaps) == 393 and max(abs(x - round(x)) for x in gaps) < 0.05
    assert [t for t in range(1, 64, 2) if abs(math.cos(2 * math.pi * 0.050 * t)) < 1e-9] == [5, 15, 25, 35, 45, 55]


def test_the_changelog_0_10_0():
    """Amendment A28, section 5: the changelog's 0.10.0 heading above 0.9.0, dated 20 October 2026 by the release pull
    request, with the lead the kickoff fixed, word for word but for the switching-time clause, deleted by the author's
    ruling R1, Q1, and its clause on the duty, which ruling R3, item 2, rewrites as the boundaries' word; and the A28
    entry naming the package's new functions, finding 30's data, Sandhi's versions 4 and 4.1 and round 5c; no
    dashes."""
    log = (ROOT / "CHANGELOG.md").read_text()
    assert log.index("## 0.10.0 (20 October 2026)") < log.index("## 0.9.0 (18 October 2026)")
    assert "(unreleased)" not in log and "## Unreleased" not in log  # the release pull request dated it
    entry = " ".join(log.split("## 0.10.0 (20 October 2026)", 1)[1].split("\n## ", 1)[0].split())
    lead = (
        "Two runs on ibm_fez's qubit 143 on 19 October 2026 were read per shot, each run and each read under a rule "
        "hashed before it. In all eighteen monitor spans read, the state read SHARED. On a job of six spans every "
        "boundary read NO CHANGE, which does not show the duties equal; the monitor means of runs on 17 and 19 October "
        "were 0.330, 0.341 and 0.313. A pattern noticed in the published weights, a job's "
        "middle span above its ends, was tested on new data under a rule fixed before them and read NOT SEEN. The desk "
        "model Sandhi, at version 4.1, had its bets for one design hashed before the run, and on that run no family of "
        "its bets counted against it; its bets for the other design are not yet scored. `manacitra.wait` gains the "
        "per-shot read of a span: the sweep series, the sharing ratio, the duty and correlation time, and the error of "
        "a time average; thresholds and words are the caller's. No cause is named."
    )
    assert entry.startswith(lead + " - Amendment A28:")
    _, d3, t16, t17 = _t30_records()
    spans = [
        s
        for k in ("d3-job2", "d3-job3")
        for s in t16["archived"]["analysis"]["jobs"][k]["qubits"]["143"]["waits"]["monitor"]["spans"]
    ]
    spans += [
        s
        for k in ("A1", "A2", "B1")
        for s in t17["archived"]["per_shot_read"]["jobs"][k]["qubits"]["143"]["waits"]["monitor"]["spans"]
    ]
    assert len(spans) == 18 and {s["Y"]["word"] for s in spans} == {"SHARED"}  # "all eighteen monitor spans"
    for name in ("sweep_series", "sharing_ratio", "two_state_reading", "time_average_sd", "boundary_ratio"):
        assert f"`{name}`" in entry, name
    for path in ("`data/desk/sandhi/v4/`", "`data/desk/t7-power-check-round5c/`", "`t17-middle-note-excerpt.md`"):
        assert path in entry, path
    assert "—" not in entry and "–" not in entry
