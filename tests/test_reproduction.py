# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""The acceptance bar: every field listed in tests/expected_fields.json reproduces to 1e-6 from the archived counts
in data/, compared strictly (tests/_reproduce.py)."""

import numpy as np
import pytest
from _reproduce import CASES, REQUIRED, TOL, k37

from manacitra import archive


@pytest.mark.parametrize("case", list(CASES))
def test_every_statistic_reproduces(case):
    rows, leaves = CASES[case]()
    assert leaves, "nothing was compared"
    worst = max(leaves)
    assert worst[0] <= TOL, f"{case}: {worst[1]} differs by {worst[0]:.3g}"
    for name, archived, reproduced in rows:
        if isinstance(archived, str):
            assert reproduced == archived, f"{case}: {name}"


@pytest.mark.parametrize("case,verdict", list(REQUIRED.items()))
def test_required_verdicts(case, verdict):
    rows, _ = CASES[case]()
    assert dict((n, r) for n, _, r in rows)["verdict"] == verdict


def test_k33_fez_gain_as_published():
    rows, _ = CASES["Kickoff 33, ibm_fez"]()
    G = dict((n, r) for n, _, r in rows)["G (top 8 by map minus top 8 by x)"]
    assert round(G, 4) == 0.0012


def test_k37_as_amendment_a5_states_it():
    """Amendment A5: the measures at the stated precision, the gap from the archived completion times, the verdict
    from the rule's fixed thresholds, and the two lines against Kickoff 34b."""
    r = k37()[2]
    m = {k: v["pearson"] for k, v in r["measures"].items()}
    assert [round(m[k], 6) for k in ("c_1", "c_2", "d_1", "d_2")] == [0.998384, 0.997482, 0.068990, -0.252175]
    assert (round(m["t27"], 3), round(m["t53"], 3)) == (0.968, 0.758)
    assert divmod(round(r["gap"]["seconds"] / 60), 60) == (9, 9)
    assert r["verdict"]["on_pearson"] == "PLACEMENT" and r["verdict"]["conditions"] == {
        "W": True,
        "N": False,
        "T": False,
        "S": True,
    }
    assert archive.placement_rule(m["c_1"], m["c_2"], m["d_1"], m["d_2"], m["t27"], m["t53"])[0] == "PLACEMENT"
    d = r["descriptive"]
    assert (d["r_T1w1_vs_34b_main_A_no_mean_of_four"]["n"], d["r_T2w1_vs_34b_screen"]["n"]) == (27, 53)
    assert round(d["r_T1w1_vs_34b_main_A_no_mean_of_four"]["pearson"], 3) == 0.989
    assert round(d["r_T2w1_vs_34b_screen"]["pearson"], 3) == 0.976


@pytest.mark.parametrize(
    "c,d,t,verdict",
    [
        ((0.69, 0.99), (0.1, 0.1), (0.9, 0.9), "NOT SETTLED (unstable)"),
        ((0.9, 0.9), (0.39, 0.1), (0.7, 0.9), "PLACEMENT"),
        ((0.9, 0.9), (0.7, 0.8), (0.1, 0.39), "DRIFT"),
        ((0.9, 0.9), (0.1, 0.1), (0.1, 0.1), "BOTH"),
        ((0.9, 0.9), (0.7, 0.7), (0.7, 0.7), "NEITHER"),
        ((0.9, 0.9), (0.4, 0.1), (0.9, 0.9), "MIXED"),
    ],
)
def test_the_placement_rule_at_its_thresholds(c, d, t, verdict):
    assert archive.placement_rule(*c, *d, *t)[0] == verdict


def test_k37_selection_note_sds():
    note = archive.load(f"{archive.RIGETTI}/k37-after-the-fact.json")["selection_note"]
    r = k37()[2]
    rec = archive.load(f"{archive.RIGETTI}/k37-placement.json")
    p53 = [tuple(p) for p in rec["programs"]["P53"]["pairs"]]
    at = [p53.index(tuple(p)) for p in rec["programs"]["P27"]["pairs"]]
    sds = [np.std(np.array(r["per_task_P11"][f"wave{w}-T2"])[at], ddof=1) for w in (1, 2)]
    assert f"SD {sds[0]:.3f} and {sds[1]:.3f}" in note


# --------------------------------------------------------------------------- Amendment A7, as it states the numbers
def near(value, stated, places):
    """value rounds to the stated figure (half away from zero, as the amendment rounds)."""
    return abs(value - stated) <= 0.5 * 10**-places + 1e-12


def test_k35_as_amendment_a7_states_it():
    from _reproduce import k35_recomputed

    a = k35_recomputed()["analysis"]
    pd = a["per_day"]
    for key, stated in (
        ("mean_k", (0.875, 0.812, 0.906)),
        ("sd_k_between_edges", (0.880, 0.950, 0.761)),
        ("reliability", (0.972, 0.982, 0.973)),
    ):
        assert all(near(pd[d][key], s, 3) for d, s in zip("123", stated)), key
    assert all(near(pd[d]["r_split"]["pearson"], s, 3) for d, s in zip("123", (0.945, 0.965, 0.947)))
    assert all(near(pd[d]["r_k_x"]["pearson"], s, 3) for d, s in zip("123", (0.063, -0.067, 0.008)))
    ac = a["across"]
    for k, r, rho, c, rx in (
        ("12", 0.856, 0.757, 0.876, 0.987),
        ("23", 0.672, 0.700, 0.687, 0.986),
        ("13", 0.862, 0.660, 0.886, 0.989),
    ):
        assert near(ac["raw"][k]["pearson"], r, 3) and near(ac["raw"][k]["spearman"], rho, 3), k
        assert near(ac["corrected"][k], c, 3) and near(ac["x_raw"][k]["pearson"], rx, 3), k
    assert ac["decile_size"] == 18
    assert round(ac["worst_decile_overlap_13"] * 18) == 9 and round(ac["best_decile_overlap_13"] * 18) == 12
    assert a["original_rule"]["verdict"] == a["verdict"]["verdict"] == "HOLDS"


def test_k38_as_amendment_a7_states_it():
    from _reproduce import k38

    r = k38()[2]
    m = r["measures"]
    for k, p, s in (("c", 0.996, 0.976), ("d", -0.142, -0.227), ("f", -0.151, -0.250), ("a", 0.989, 0.962)):
        assert near(m[k]["pearson"], p, 3) and near(m[k]["spearman"], s, 3), k
    assert r["verdict"]["on_pearson"] == "ACTIVITY"
    d = r["descriptive"]
    assert near(d["idle_pairs_P53i"]["T1_T4_pooled_mean"], 0.0039, 4) and near(
        d["idle_pairs_P53i"]["T1"]["max"], 0.0203, 4
    )
    low = [v["T1_P53i"] for v in d["five_P27_low_pairs"].values()]
    assert all(near(v, s, 3) for v, s in zip(low, (0.201, 0.252, 0.334, 0.440, 0.234)))
    assert d["five_low_count"] == {"T1_ge_0.6": 0, "T4_ge_0.6": 0, "mean_T1_T4_ge_0.6": 0}
    assert near(d["direction"]["mean_T3_minus_meanT1T4_on_27"], 0.168, 3)
    assert near(d["direction"]["mean_meanT1T4_minus_T2_on_27"], -0.012, 3)
    a37 = d["against_37"]
    assert near(a37["r_T2_vs_37_mean_P27"]["pearson"], 0.852, 3) and a37["r_T2_vs_37_mean_P27"]["n"] == 27
    assert near(a37["r_T3_vs_37_mean_P53_all_53"]["pearson"], 0.880, 3) and a37["r_T3_vs_37_mean_P53_all_53"]["n"] == 53


def test_k40_as_amendment_a7_states_it():
    from _reproduce import k40_stage1, k40_stage2, k40_stage3

    s1, s2, s3 = k40_stage1(), k40_stage2(), k40_stage3()
    assert near(s1["c"]["pearson"], 0.9979, 4) and near(s1["d"]["pearson"], 0.9924, 4)
    assert s1["records_match_names"] and s1["reading"] == "PINNED"
    d1 = s1["descriptive_outside_reading"]
    assert near(d1["r_X_vs_k37_27pair_program"]["pearson"], -0.18, 2)
    assert near(d1["r_X_vs_k37_53pair_program"]["pearson"], 0.24, 2)
    assert [e["pair"] for e in s2["dead_pair_filter"]["excluded"]] == [[11, 12], [18, 19]]
    assert (s2["n_working"], s2["n_working_with_x"]) == (25, 23)
    v = s2["verdict_stats"]
    assert near(v["S1"]["r_split_A"]["pearson"], 0.9737, 4) and near(v["S2"]["r_AB"]["pearson"], 0.8115, 4)
    assert near(v["S3"]["r_Ax"]["pearson"], 0.198, 3) and near(v["S3"]["r_AB_given_x"], 0.8122, 4)
    assert s2["verdict"] == "DIAGNOSTIC" and near(s2["leave_one_out"]["r_AB"]["pearson"], 0.66, 2)
    k34 = s2["descriptive"]["r_kA_vs_34b_kA_shared_working"]
    assert k34["n"] == 20 and near(k34["pearson"], -0.17, 2)
    c, g = s3["correlations_on_S"]["W"], s3["gains"]
    assert near(s3["mean_W_on_S"], 0.9532, 4) and len(s3["set_S_with_x"]) == 23
    assert near(c["k_prior"]["pearson"], 0.369, 3) and near(c["partial_k_prior_given_x"], 0.407, 3)
    assert near(c["L_prior"]["pearson"], 0.636, 3) and near(g["k_prior"]["G"], -0.0045, 4)
    assert near(g["k_prior"]["relative_error_reduction"], -0.098, 3)
    assert near(g["L_prior"]["relative_error_reduction"], 0.314, 3)
    assert s3["verdict"] == "NOT SETTLED"


def test_k41_as_amendment_a7_states_it():
    from _reproduce import k40_stage2, k41_partB, k41_today

    t = k41_today()
    assert [e["pair"] for e in t["dead_pair_filter"]["excluded"]] == [[11, 12], [72, 73], [76, 77]]
    assert (t["n_working"], t["n_working_with_x"], t["working_without_x"]) == (24, 23, [[18, 19]])
    v = t["verdict_stats"]
    assert near(v["S1"]["r_split_A"]["pearson"], 0.816, 3) and near(v["S1"]["r_split_B"]["pearson"], 0.651, 3)
    assert near(v["S2"]["r_AB"]["pearson"], 0.904, 3) and near(v["S3"]["r_Ax"]["pearson"], -0.004, 3)
    assert near(v["S3"]["r_AB_given_x"], 0.905, 3) and t["verdict"] == "DIAGNOSTIC"
    assert near(t["all_working"]["S2"]["r_AB"]["pearson"], -0.129, 3)
    k = dict(
        zip(map(tuple, t["dead_pair_filter"]["working_pairs"]), zip(t["all_working"]["kA"], t["all_working"]["kB"]))
    )
    assert near(k[(18, 19)][0], -5.77, 2) and near(k[(18, 19)][1], 1.84, 2)
    rec = archive.load(f"{archive.RIGETTI}/k41-map.json")
    f41 = archive.load(f"{archive.RIGETTI}/k41-figures.json")["A"]
    f40 = archive.load(f"{archive.RIGETTI}/k40-figures.json")["stage2"]
    pm = archive.pinned_map_persistence(t, k40_stage2(), f41, f40, rec["pairs"], rec["meta"]["permutation_seed"])
    assert len(pm["P_both"]) == 23
    assert near(pm["p_k"]["r"]["pearson"], 0.853, 3) and near(pm["p_k"]["r"]["spearman"], 0.784, 3)
    assert near(pm["p_k_prime"]["r"]["pearson"], 0.614, 3) and pm["p_k_prime"]["n"] == 21
    assert near(pm["p_L"]["pearson"], 0.802, 3) and near(pm["p_L"]["spearman"], 0.899, 3) and pm["p_L"]["n"] == 27
    assert pm["verdict"] == "HOLDS"
    ex = pm["beside"]["extremes_today_kA"]
    assert near(ex["42-43"], -0.23, 2) and near(ex["94-95"], -2.31, 2)
    b = k41_partB()
    assert near(b["mean_W"], 0.945, 3) and len(b["W"]) == 25  # the mean over all 25 pairs
    L, K = b["level"], b["kept_share"]
    assert (
        near(L["partial_r_given_x"], 0.504, 3)
        and near(L["G"], 0.0122, 4)
        and near(L["relative_error_reduction"], 0.268, 3)
    )
    assert L["overlap"] == 5 and L["verdict"] == "USEFUL"
    assert near(L["ci90"][0], 0.0077, 4) and near(L["ci90"][1], 0.0168, 4)
    assert (
        near(K["partial_r_given_x"], 0.403, 3)
        and near(K["G"], -0.0040, 4)
        and near(K["relative_error_reduction"], -0.089, 3)
    )
    assert K["overlap"] == 2 and K["verdict"] == "NOT SETTLED"
    s = b["same_day"]
    assert near(s["level"]["relative_error_reduction"], 0.153, 3) and near(
        s["kept_share"]["relative_error_reduction"], -0.177, 3
    )
    assert s["level"]["verdict"] == s["kept_share"]["verdict"] == "NOT SETTLED"


def test_k42_as_amendment_a7_states_it():
    from _reproduce import k42_scan

    ideal_A = [0.920476, 0.963423, 0.990636, 1.000000, 0.990486, 0.962235, 0.916530, 0.855691, 0.782875]
    assert all(near(archive.scan_ideal("A", a), s, 6) for a, s in zip(archive.SCAN["A"]["offsets"], ideal_A))
    sc = k42_scan()
    d1, d2 = sc["day1"], sc["day2"]
    assert (
        len(d1["working"]) == 26
        and d1["excluded"][0]["pair"] == [76, 77]
        and near(d1["excluded"][0]["max_P11_A"], 0.269, 3)
    )
    assert near(d1["V1"]["sd_deltaA_across_working"], 0.481, 3) and d1["V1"]["verdict"] == "SPREAD"
    assert near(d1["V2"]["r"]["pearson"], 0.369, 3) and near(d1["V2"]["r"]["spearman"], 0.691, 3)
    assert near(d1["V2"]["mean_abs_dA_minus_dB"], 0.347, 3) and d1["V2"]["verdict"] == "MIXED"
    v3 = d1["V3"]
    assert (
        near(v3["r_deltaA_vs_k40_kA"]["pearson"], 0.243, 3) and len(v3["pairs"]) == 24 and v3["verdict"] == "DOES NOT"
    )
    assert near(d1["beside"]["shape_fraction_rms_le_2_shot"], 0.077, 3)
    assert len(d2["working"]) == 27 and near(d2["beside"]["shape_fraction_rms_le_2_shot"], 0.093, 3)
    v4, v4o, v5 = sc["V4_amended_governs"], sc["V4_original_rule"], sc["V5"]
    assert (v4["A"]["n"], v4["B"]["n"], v4["verdict"]) == (21, 22, "HOLDS")
    assert near(v4["A"]["r"]["pearson"], 0.724, 3) and near(v4["B"]["r"]["pearson"], 0.904, 3)
    assert (v4o["A"]["n"], v4o["verdict"]) == (26, "PARTIAL")
    assert near(v4o["A"]["r"]["pearson"], 0.379, 3) and near(v4o["B"]["r"]["pearson"], 0.828, 3)
    assert near(v5["p_F"]["pearson"], 0.854, 3) and near(v5["p_F"]["spearman"], 0.842, 3)
    assert near(v5["median_per_pair_r"], 0.983, 3) and v5["verdict"] == "HOLDS"
    sw = v5["switch"]["pairs"]
    assert near(sw["11-12"]["day1_high_minus_low"], 0.334, 3) and near(sw["11-12"]["day2_high_minus_low"], 0.350, 3)
    assert near(sw["72-73"]["day1_high_minus_low"], 0.211, 3) and near(sw["72-73"]["day2_high_minus_low"], 0.107, 3)
    assert v5["switch"]["verdict"] == "MIXED"
    watched = {
        "94-95": (-0.39, -1.03, -0.68, -1.47),
        "42-43": (-0.26, -0.08, -0.35, -0.11),
        "18-19": (-1.50, -1.50, 1.50, -1.26),
    }
    for p, stated in watched.items():
        got = [d["beside"]["watch_pairs"][p][f]["delta"] for d in (d1, d2) for f in "AB"]
        assert all(near(g, s, 2) for g, s in zip(got, stated)), (p, got)
