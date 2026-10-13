# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""The README's measured statistics, and the times, ranges and counts it shows, recomputed from data/ and compared at
the README's own rounding (times: to the nearest minute).

The README links to four pages in docs/ that carry most of its text: the findings in full, the method in six pictures,
the kickoffs, and the install details. Every check here reads the README and those pages together, as one text: a
number moved between them is still checked, and a retired phrase cannot come back on any of them."""

from datetime import datetime, timedelta
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
    assert "The findings come from runs on 5 to 13 October 2026." in README
    assert "Nineteen findings, from runs on 5 to 13 October 2026." in README
    # a reconstruction (A18, ruling R1: Kickoff 47's Part B circuits) is a record about a run, not a run
    runs = [
        p
        for p in archive.records()
        if p.parent.name != "simulated" and "k33-workload" not in p.name and "reconstruction" not in p.name
    ]
    days = {archive.load(p)["meta"]["utc"][:10] for p in runs if not p.name.endswith("coupling-map.json")}
    assert days == {"2026-10-05", "2026-10-06", "2026-10-07", "2026-10-10", "2026-10-11", "2026-10-13"}
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
    """The README's table of findings: each row's headline is that finding's own bold sentence in docs/findings.md,
    word for word; its kickoffs are the ones the finding names; and every verdict word in the row (the capitalised
    words) is in that kickoff's row of the kickoffs table, so the summary carries nothing the full text does not."""
    import re

    readme = (ROOT / "README.md").read_text()
    findings = (ROOT / "docs" / "findings.md").read_text()
    kickoffs = (ROOT / "docs" / "kickoffs.md").read_text()
    full = dict(re.findall(r'^(\d+)\. <a id="finding-\d+"></a>\*\*(.+?)\*\*', findings, re.M))
    rows = re.findall(
        r"^\| \[(\d+)\]\(docs/findings\.md#finding-\1\) \| (.+?) \| [^|]+ \| ([^|]+) \| (.+?) \|$", readme, re.M
    )
    rows = [(n, head, when.rsplit(", ", 1)[0], verdict) for n, head, when, verdict in rows]  # "37, 38, 6 Oct": 37, 38
    assert [n for n, *_ in rows] == [str(i) for i in range(1, 20)]
    for n, head, kicks, verdict in rows:
        assert head == full[n], n
        item = findings.split(f'<a id="finding-{n}"></a>', 1)[1].split("<a id=", 1)[0]
        table_rows = ""
        for k in kicks.split(", "):
            assert f"Kickoff {k}" in item, (n, k)
            table_rows += next(line for line in kickoffs.splitlines() if line.startswith(f"| {k}, "))
        words = set(re.findall(r"\b[A-Z]{3,}(?: [A-Z]{3,})*\b", verdict))
        assert words and all(w in table_rows for w in words), (n, words)


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
    front = (ROOT / "README.md").read_text()
    assert "| USEFUL on ibm_fez (G = +0.0012 in fidelity); NOT SETTLED on ibm_kingston |" in front


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
    assert "ran under, over about 22 hours. Whether it lasts longer, and why it is there, are not known" in flat


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
    assert "the nineteen findings in full, what was known before them, and what has not been shown." in flat  # A22


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
    assert len(list(DIAGRAMS.glob("*.svg"))) == 12 and "# the twelve diagrams, from data/" in index  # A22: twelve


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
    assert "under IBM's calibration stamp of 17:32:21 UTC, newer than finding 15's." in item
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
    assert "The run cannot separate the recalibration from the circuits' other differences." in item
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
    assert "a calibration stamped about two minutes before the job began was published after it was submitted" in item
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
        "after the fetch" in item
    )
    # the scope
    assert len({143, 144} | {c["chain"][1] for c in draw["drawn"]}) == 6
    assert "The active-neighbour check now rests on six waiting qubits on one processor" in item
    assert "It is the instrument that held in the cases tested; a second day on this code is planned." in item
    assert "Manacitra does not rank machines." in item


def test_findings_15_to_19_beside_the_findings():
    """Amendment A22: the README's rows, count, limit line and one sentence on the check's default; the kickoffs rows;
    the method's subsection and the reproduce page's pointers; and the four new bullets of what has not been shown,
    with the one edited bullet."""
    from _reproduce import K50, K51, K52, K53, k50_recomputed, k51_recomputed, k52_recomputed, k53_recomputed, reuse_doc

    readme = " ".join((ROOT / "README.md").read_text().split())
    assert "Nineteen findings, from runs on 5 to 13 October 2026." in readme
    assert "the nineteen findings in full, what was known before them, and what has not been shown." in readme
    assert (
        "- **One processor, one day, six waiting qubits, for findings 15 to 19.** Findings 15 to 19 are from five "
        "jobs on ibm_fez on 13 October 2026; for the last two, which published calibration they ran under is not known."
        in readme
    )
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
    assert "It is the instrument that held in the cases tested, on six waiting qubits of one processor." in method
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
        "- **The active-neighbour check has run on one processor.** It has been tested on six waiting qubits of ibm_fez"
        in flat
    )
    cells = [k50_recomputed()["per_M"][q]["d1"] for q in ("144", "143")]
    cells += [v for q in ("144", "143") for v in k51_recomputed()["per_M"][q]["d1"].values()]
    cells += [v for q in ("143", "144") for v in k52_recomputed()["per_M"][q]["d1"].values()]
    cells += [c["d1"] for c in k53_recomputed()["cells"]]
    assert (len(cells), sum(x > 0 for x in cells), _q(max(cells), 3, True)) == (28, 27, "+0.114")
    assert (
        "The active-neighbour residual d1 has read high in 27 of its 28 cells so far (findings 16 to 19), by up "
        "to +0.114." in flat
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
