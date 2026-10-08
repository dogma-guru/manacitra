# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""Amendment A7, 5.1: pairs the vendor has flagged as not measured or not working are reported with and without.

The verdicts count every pair that runs, as the kickoffs fixed them; beside each verdict, the "flagged" block names the
flagged pairs, the flag's source, and the headline statistics recomputed without them."""

import numpy as np
import pytest

from manacitra import archive
from manacitra.layout import FLAG_SOURCES, published_score_braket, vendor_flag
from manacitra.report import verdict_lines
from manacitra.verdicts import analyse_map, persistence_analysis


# --------------------------------------------------------------------------- the flag and Braket's score
def test_the_vendor_flag():
    assert vendor_flag(two_qubit_error=1.0) == FLAG_SOURCES["ibm"]
    assert vendor_flag(cz_fidelity=0.5) == FLAG_SOURCES["braket"]
    assert vendor_flag(two_qubit_error=0.9999) is None and vendor_flag(cz_fidelity=0.5001) is None
    assert vendor_flag() is None


def test_published_score_braket_and_its_placeholder():
    """x = (1 - CZ fidelity) + (1 - readout fidelity) of each qubit; a CZ fidelity of exactly 0.5 is no figure."""
    assert published_score_braket(0.99, 0.95, 0.97) == pytest.approx(0.01 + 0.05 + 0.03)
    assert published_score_braket(0.5, 0.95, 0.97) is None
    assert published_score_braket(None, 0.95, 0.97) is None


def test_published_score_braket_gives_kickoff_40s_x():
    for f in archive.load(f"{archive.RIGETTI}/k40-pairs.json")["per_pair"]:
        assert published_score_braket(f["cz_fidelity"], *f["readout_fidelity"]) == f["x"]


# --------------------------------------------------------------------------- the map
@pytest.fixture(scope="module")
def arm2():
    rec = archive.load("simulated/k36-arm2.json")
    return archive.p11_table(rec), rec["order"], rec["x"]


def test_a_planted_flag_in_the_map(arm2):
    P, order, x = arm2
    flags = [None] * P.shape[1]
    flags[3] = flags[11] = vendor_flag(two_qubit_error=1.0)
    an = analyse_map(P, order, x=x, seed=36, n_permutations=200, flagged=flags)
    plain = analyse_map(P, order, x=x, seed=36, n_permutations=200)
    assert an["verdict"] == plain["verdict"], "the verdict counts every pair that runs"
    fl = an["flagged"]
    assert fl["pairs"] == [3, 11] and fl["sources"] == [FLAG_SOURCES["ibm"]]
    rest = [i for i in range(P.shape[1]) if i not in (3, 11)]
    sub = analyse_map(P[:, rest], order, x=np.asarray(x)[rest], seed=36, n_permutations=200)
    assert fl["without"]["n_pairs"] == len(rest)
    for k in ("S1", "S2", "S3", "mean_kA", "sd_kA_between_pairs"):
        assert fl["without"][k] == sub[k]
    assert "flagged by the vendor, outside the verdict: 2 pair(s)" in verdict_lines(an)


def test_no_flag_no_line(arm2):
    P, order, x = arm2
    an = analyse_map(P, order, x=x, seed=36, n_permutations=200)
    assert an["flagged"]["pairs"] == [] and an["flagged"]["without"] is None
    assert "flagged" not in verdict_lines(an)


def test_flags_follow_the_dead_pair_filter(arm2):
    """A flag is given per pair as run; after the dead-pair filter the block still names the pair by that index."""
    P, order, _ = arm2
    P = P.copy()
    P[[i for i, lab in enumerate(order) if lab == "A no"], 0] = 0.1  # pair 0 reads dead
    flags = [None] * P.shape[1]
    flags[5] = vendor_flag(cz_fidelity=0.5)
    an = analyse_map(P, order, seed=36, n_permutations=200, dead_pair_floor=0.5, flagged=flags)
    assert an["dead_pair_filter"]["excluded"] == [0]
    assert an["flagged"]["pairs"] == [5] and an["flagged"]["without"]["n_pairs"] == P.shape[1] - 2


def test_ibm_files_carry_the_flag():
    """An archived IBM map is read with each pair's flag from its published two-qubit error."""
    an = archive.map_from_record(archive.load("ibm_fez/k31-map.json"), n_permutations=200)
    assert an["flagged"]["pairs"] == []  # Kickoff 31 chose pairs by x: none flagged


# --------------------------------------------------------------------------- persistence
def test_a_planted_flag_in_persistence():
    days = archive.load("simulated/k36-persistence.json")["static"]["days"]
    planted = {d: dict(v) for d, v in days.items()}
    edges = planted["1"]["edges"]
    flagged = {edges[2], edges[7]}
    for d in planted:  # flagged on one day is enough
        planted[d]["flags"] = [
            FLAG_SOURCES["ibm"] if (e in flagged and d == "2") else None for e in planted[d]["edges"]
        ]
    a = persistence_analysis(planted)
    plain = persistence_analysis(days)
    assert a["verdict"] == plain["verdict"] and a["original_rule"] == plain["original_rule"]
    fl = a["flagged"]
    assert sorted(fl["pairs"]) == sorted(flagged) and fl["sources"] == [FLAG_SOURCES["ibm"]]
    sub = {
        d: {k: [v[k][i] for i, e in enumerate(v["edges"]) if e not in flagged] for k in ("edges", "x", "obs")}
        for d, v in days.items()
    }
    b = persistence_analysis(sub)
    w = fl["without"]
    assert w["n_edges"] == b["across"]["edges_on_all_days"] == len(edges) - 2
    assert w["reliability"] == {d: v["reliability"] for d, v in b["per_day"].items()}
    assert w["corrected"] == b["across"]["corrected"] and w["raw"] == b["across"]["raw"]
    assert w["worst_decile_overlap_13"] == b["across"]["worst_decile_overlap_13"]


def test_kickoff_35s_four_flagged_edges():
    """Amendment A7, section 1: four edges at an IBM two-qubit error of exactly 1.0 on every day; without them, on 172
    edges, each day's reliability recomputed on the subset, the corrected r and the worst decile."""
    from _reproduce import k35_recomputed

    fl = k35_recomputed()["analysis"]["flagged"]
    assert sorted(map(tuple, fl["pairs"])) == [(27, 28), (32, 33), (71, 72), (72, 73)]
    w = fl["without"]
    assert w["n_edges"] == 172
    assert [round(w["reliability"][d], 3) for d in "123"] == [0.928, 0.972, 0.942]
    assert [round(w["corrected"][k], 3) for k in ("12", "23", "13")] == [0.830, 0.428, 0.736]
    assert (w["decile_size"], round(w["worst_decile_overlap_13"] * 17)) == (17, 8)
