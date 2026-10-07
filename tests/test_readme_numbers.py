# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""The README's measured statistics, and the times, ranges and counts it shows, recomputed from data/ and compared at
the README's own rounding (times: to the nearest minute)."""

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

from manacitra import archive

README = (Path(__file__).resolve().parents[1] / "README.md").read_text()


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
    assert "docs/diagrams/chip-map-table.md" in README


# --------------------------------------------------------------------------- Amendment A5: Kickoff 37
K37 = f"{archive.RIGETTI}/k37-placement.json"


def _utc(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def test_the_findings_dates():
    assert "The findings come from runs on 5 to 7 October 2026." in README
    runs = [
        p for p in archive.data_dir().rglob("*.json") if p.parent.name != "simulated" and "k33-workload" not in p.name
    ]
    days = {archive.load(p)["meta"]["utc"][:10] for p in runs if not p.name.endswith("coupling-map.json")}
    assert days == {"2026-10-05", "2026-10-06", "2026-10-07"}
    assert "- **Three processors, three days.**" in README and "all on 5 to 7 October 2026." in README


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
    assert rs == (-0.18, 0.24) and "(r = −0.18 and 0.24 against the pinned levels)" in README


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
    # both pairs on qubit 149 fell on Day 2 and came back on Day 3; IBM's x for them moved by less than 15%
    on149 = [i for i, e in enumerate(edges) if 149 in e]
    assert len(on149) == 2
    for i in on149:
        k1, k2, k3 = (a["per_day"][d]["k"][i] for d in "123")
        assert k2 < -4 and k1 > k2 + 2 and k3 > k2 + 2
        x = [archive.load(f"ibm_fez/k35-day{d}.json")["published_at_submission"][i]["x"] for d in (1, 2, 3)]
        assert max(x) / min(x) < 1.2  # x moved by up to 16% while k swung by more than 5
    assert "On Day 2 both pairs on one qubit fell sharply and recovered on Day 3" in README
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
    only_L = [pairs.index(tuple(p)) for p in L["pick"] if p not in L["x_pick"]]
    only_x = [pairs.index(tuple(p)) for p in L["x_pick"] if p not in L["pick"] and tuple(p) != (94, 95)]
    assert abs(W[only_L].mean() - W[only_x].mean()) < 0.001  # otherwise the picks tie
    assert "rated 94-95 sixth best of 23, and it was the worst on the workload; the two picks otherwise tie" in README
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
    ):
        assert f"| {k} |" in README
    assert "- **How long a map lasts beyond two days.**" in README and "- **Two routes to one processor.**" in README
    assert "`manacitra pick --by level` ranks by the plain level instead" in README
    assert "running as of 6 October 2026" not in README
