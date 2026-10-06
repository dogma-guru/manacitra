# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""The README's measured statistics, and the times, ranges and counts it shows, recomputed from data/ and compared at
the README's own rounding (times: to the nearest minute)."""

from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pytest
from _reproduce import k31, k32, k33, k34b, k36

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


def test_the_open_question_on_the_rigetti_platform():
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
        ("ibm_fez/k29-settle.json", "02:24"),
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
    assert hhmm(m["utc_screen"]["completed_by"]) == "18:55" and "the screen (18:55 UTC)" in README
    assert hhmm(m["utc_main_job"]["wave_1_completed"][0]) == "22:15" and "the main job (22:15 UTC)" in README
    assert "main job 22:15 to 22:29 UTC" in README
    note = archive.load(f"{archive.RIGETTI}/main.json")["archived"]["descriptive"]["across_runs"]["note"]
    assert "test task (16:44 to 17:01 UTC" in note and "the test task (17:01 UTC)" in README


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
