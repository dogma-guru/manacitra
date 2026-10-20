# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""Amendment A4, R3: the inventory of archived fields, and the comparison's strictness.

Every field of every file in data/ is either recomputed and compared (tests/expected_fields.json) or excluded with a
reason (tests/excluded_fields.json), never both and never neither, so a new archived statistic cannot slip through
unlisted. And the comparison fails, as it must, when an inventoried statistic is changed, removed, emptied or made
NaN in memory; the files on disk are never touched."""

import copy
import hashlib
import json
import re

import _reproduce
import pytest
from _reproduce import CASES, TOL, clear_caches, data_fields, get, leaf_diffs, load_exclusions, load_inventory

from manacitra import archive as ar


def _data_files():
    root = ar.data_dir()
    return {str(p.relative_to(root)): p for p in ar.records(root)}


def _pattern(path: str) -> re.Pattern:
    """An excluded path covers itself and its subtree; [*] stands for any list index."""
    return re.compile("^" + re.escape(path).replace(re.escape("[*]"), r"\[\d+\]") + "(/|$)")


def _expected_by_file():
    out: dict = {}
    for case, groups in load_inventory()["cases"].items():
        for g in groups:
            for field in g["fields"]:
                out.setdefault(g["file"], {}).setdefault(field, []).append(case)
    return out


def test_every_case_has_an_inventory_and_every_inventory_a_case():
    assert set(load_inventory()["cases"]) == set(CASES)
    assert all(load_inventory()["cases"][c] for c in CASES)


def test_every_field_of_every_data_file_is_listed_once():
    expected, excluded = _expected_by_file(), load_exclusions()["files"]
    unlisted, both = [], []
    for name, path in _data_files().items():
        doc = json.loads(path.read_text())
        exp = expected.get(name, {})
        pats = [_pattern(p) for p in excluded.get(name, {})]
        for field in data_fields(doc):
            is_exp = field in exp or any(field.startswith(e + "/") for e in exp)
            is_exc = any(p.match(field) for p in pats)
            if not is_exp and not is_exc:
                unlisted.append(f"{name}: {field}")
            elif is_exp and is_exc:
                both.append(f"{name}: {field}")
    assert not unlisted, f"{len(unlisted)} field(s) in neither file, for example: {unlisted[:10]}"
    assert not both, f"{len(both)} field(s) both compared and excluded: {both[:10]}"


def test_every_listed_field_exists():
    files = _data_files()
    missing = []
    for name, fields in _expected_by_file().items():
        doc = json.loads(files[name].read_text())
        for field in fields:
            try:
                get(doc, field)
            except KeyError:
                missing.append(f"{name}: {field}")
    for name, paths in load_exclusions()["files"].items():
        doc = json.loads(files[name].read_text())
        fields = list(data_fields(doc))
        for p in paths:
            if not any(_pattern(p).match(f) for f in fields):
                missing.append(f"{name}: {p} (excluded)")
    assert not missing, missing


def test_every_exclusion_has_a_reason_and_is_narrower_than_a_file():
    for name, paths in load_exclusions()["files"].items():
        for p, reason in paths.items():
            assert isinstance(reason, str) and len(reason) >= 10, (name, p)
            assert p and p not in ("archived", "archived/analysis"), (name, p)


def test_k29_settling_analysis_is_under_test():
    """The reviewer's example: archived.analysis.z in the settling run is now an inventoried field."""
    fields = load_inventory()["cases"]["Kickoff 29 settling run and Kickoff 31 step 0, ibm_fez"][0]["fields"]
    assert "archived/analysis/z" in fields and "archived/analysis/verdict" in fields


# --------------------------------------------------------------------------- the comparison itself
def test_the_comparison_reports_a_missing_key_and_a_type_change():
    """The reviewer's two direct probes of the helper: both now fail."""
    missing = leaf_diffs({"checked": 1}, {"checked": 1, "omitted": 123})
    assert max(missing)[0] == float("inf") and "missing on the recomputed side" in max(missing)[1]
    to_none = leaf_diffs({"checked": 1, "omitted": None}, {"checked": 1, "omitted": 123})
    assert max(to_none)[0] == float("inf") and "type" in max(to_none)[1]


@pytest.mark.parametrize(
    "mine,archived,word",
    [
        (float("nan"), 1.0, "not finite"),
        (float("inf"), 1.0, "not finite"),
        (1.0, "1.0", "type"),
        ([1.0, 2.0], [1.0], "length"),
        (1.0, [1.0], "type"),
        (True, 1, "type"),
        ({"a": 1}, {"a": 1, "b": 2}, "missing on the recomputed side"),
        ({"a": 1, "b": 2}, {"a": 1}, "missing on the archived side"),
        ("MAP PRESENT", "NOISE", "against"),
    ],
)
def test_the_comparison_is_strict(mine, archived, word):
    worst = max(leaf_diffs(mine, archived))
    assert worst[0] > TOL and word in worst[1]


# --------------------------------------------------------------------------- mutations in memory
MUTATED = {
    "Kickoff 29 settling run and Kickoff 31 step 0, ibm_fez": ("ibm_fez/k29-settle.json", "archived/analysis/z"),
    "Kickoff 31, ibm_kingston": ("ibm_kingston/k31-map.json", "archived/robustness/r_AB/pearson"),
    "Kickoff 33, ibm_fez": (
        "ibm_fez/k33-payoff.json",
        "archived/analysis/gains/k_prior/ci90_circuits_and_shots_not_in_verdict",
    ),
    "Kickoff 34b, Rigetti Cepheus-1-108Q": ("rigetti_cepheus_1_108q/main.json", "archived/analysis/S2/r_AB/pearson"),
    "Kickoff 37, Rigetti Cepheus-1-108Q": (
        "rigetti_cepheus_1_108q/k37-placement.json",
        "archived/measures/d_2/pearson",
    ),
    # Amendment A7: one field of each new recompute
    "Kickoff 35, ibm_fez": ("ibm_fez/k35-persistence.json", "archived/across/verdict"),
    "Kickoff 38, Rigetti Cepheus-1-108Q": ("rigetti_cepheus_1_108q/k38-activity.json", "archived/verdict/on_pearson"),
    "Kickoff 40, stage 2, the map": ("rigetti_cepheus_1_108q/k40-map.json", "archived/analysis/verdict"),
    "Kickoff 41, Part A, the map a day later": (
        "rigetti_cepheus_1_108q/k41-map.json",
        "archived/analysis/p_k/r/pearson",
    ),
    "Kickoff 42, Day 2": ("rigetti_cepheus_1_108q/k42-day2.json", "archived/V5/verdict"),
    # Amendment A17: the verdict quantity of Kickoff 43 and the verdict of Kickoff 47
    "Kickoff 43, Job 2, the run": ("ibm_fez/k43-reuse.json", "archived/analysis/G_reuse/point"),
    "Kickoff 47, the wait": ("ibm_fez/k47-wait.json", "archived/analysis/part_A/H_phase"),
    # Amendment A19: the verdict of Kickoff 48
    "Kickoff 48, the wait test on hardware": ("ibm_fez/k48-wait-test.json", "archived/analysis/H48"),
    # Amendment A22: the verdicts of Kickoffs 49 to 53
    "Kickoff 49, the wait test on a second day": ("ibm_fez/k49-wait-test.json", "archived/analysis/H48"),
    "Kickoff 50, the neighbour test": ("ibm_fez/k50-neighbour-test.json", "archived/analysis/H50"),
    "Kickoff 51, a known offset": ("ibm_fez/k51-known-offset.json", "archived/analysis/verdict"),
    "Kickoff 52, the phase sweep": ("ibm_fez/k52-phase-sweep.json", "archived/analysis/H52b"),
    "Kickoff 53, the revised check on new chains": ("ibm_fez/k53-revised-check.json", "archived/analysis/H53"),
    # Amendment A23: the verdicts of Kickoffs 54 and 55
    "Kickoff 54, the revised check on a second day": ("ibm_fez/k54-revised-check-day-2.json", "archived/analysis/H54"),
    "Kickoff 55, the revised check on ibm_kingston": ("ibm_kingston/k55-revised-check.json", "archived/analysis/H55"),
    # Amendment A24: the verdicts of Kickoffs 56 to 59, 61 and 62
    "Kickoff 56, the phase sweep on ibm_kingston": ("ibm_kingston/k56-phase-sweep.json", "archived/analysis/H56a"),
    "Kickoff 57, the check at the peak phase": ("ibm_kingston/k57-peak-check.json", "archived/analysis/H57"),
    "Kickoff 58, the placement comparison": ("ibm_kingston/k58-placement-comparison.json", "archived/analysis/H58b"),
    "Kickoff 59, the check at the peak phase on a second day": (
        "ibm_kingston/k59-peak-check-day-2.json",
        "archived/analysis/H59",
    ),
    "Kickoff 61, the readout check on ibm_fez": ("ibm_fez/k61-readout-check.json", "archived/analysis/H61"),
    "Kickoff 62, the check at the peak phase on ibm_fez": ("ibm_fez/k62-peak-check.json", "archived/analysis/H62"),
    # Amendment A25: test 7's verdict
    "Test 7, two frequencies on qubit 143": ("ibm_fez/t7-ramsey-xy.json", "archived/analysis/verdict"),
}
HOW = ["999", "remove", "None", "NaN"]


def _mutate(doc, field, how):
    *parent, last = [int(p[1:-1]) if p.startswith("[") else p for p in field.split("/")]
    node = doc
    for p in parent:
        node = node[p]
    many = isinstance(node[last], list)
    if how == "999":
        node[last] = [999.0] * len(node[last]) if many else 999.0
    elif how == "remove":
        del node[last]
    elif how == "None":
        node[last] = None
    elif how == "NaN":
        node[last] = [float("nan")] * len(node[last]) if many else float("nan")


def _fingerprint():
    return {n: hashlib.sha256(p.read_bytes()).hexdigest() for n, p in _data_files().items()}


@pytest.fixture(scope="module")
def recomputed():
    """Each mutated case's recomputed tree and the data files it read, captured once."""
    out = {}
    real = _reproduce.compare

    def capture(case, tree, docs):
        out[case] = (tree, docs)
        return real(case, tree, docs)

    _reproduce.compare = capture
    clear_caches()
    try:
        for case in MUTATED:
            CASES[case]()
    finally:
        _reproduce.compare = real
        clear_caches()
    return out


@pytest.mark.parametrize("how", HOW)
@pytest.mark.parametrize("case", list(MUTATED))
def test_a_mutated_statistic_fails_the_comparison(case, how, recomputed):
    """One inventoried statistic changed to 999, removed, set to None or set to NaN in a copy of the loaded file: the
    comparison fails and names it. The files on disk are not touched."""
    file, field = MUTATED[case]
    before = _fingerprint()
    tree, docs = recomputed[case]
    assert max(_reproduce.compare(case, tree, docs))[0] <= TOL  # as archived, it passes
    mutated = copy.deepcopy(docs)
    _mutate(mutated[file], field, how)
    bad = [(d, p) for d, p in _reproduce.compare(case, tree, mutated) if not d <= TOL]
    assert bad, f"{case}: {field} set to {how} in memory, and the comparison still passed"
    assert all(field in p for _, p in bad), bad
    assert _fingerprint() == before


@pytest.mark.parametrize(
    "case,processor,run,field",
    [
        ("Kickoff 29 settling run and Kickoff 31 step 0, ibm_fez", "ibm_fez", "k29-settle", "archived/analysis/z"),
        ("Kickoff 34b, Rigetti Cepheus-1-108Q", None, "rigetti_cepheus_1_108q/main.json", "archived/analysis/kA"),
    ],
)
def test_the_reviewers_probe_end_to_end(case, processor, run, field, monkeypatch):
    """As the reviewer's coverage_probe.py did it: the loaded record is changed in memory, the case is run again from
    the data, and now it fails."""
    before = _fingerprint()
    if processor is not None:
        real = ar.fez_or_kingston
        doc = copy.deepcopy(real(processor))
        _mutate(doc[run], field, "999")
        monkeypatch.setattr(ar, "fez_or_kingston", lambda p: doc if p == processor else real(p))
    else:
        real_load = ar.load
        doc = copy.deepcopy(real_load(run))
        _mutate(doc, field, "999")
        monkeypatch.setattr(ar, "load", lambda p: doc if str(p) == run else real_load(p))
    clear_caches()
    try:
        _, leaves = CASES[case]()
    finally:
        monkeypatch.undo()
        clear_caches()
    bad = [p for d, p in leaves if not d <= TOL]
    assert bad and all(field in p for p in bad), bad
    assert _fingerprint() == before


# --------------------------------------------------------------------------- Amendment A7: seeded resampling
def test_the_resampling_rule():
    """Amendments A7 and A8, R6: a marked shots-resampled field at 10⁻³; a marked bootstrap field strictly under numpy
    2.5 or later, not compared under an older numpy; an unmarked field at 10⁻⁶ whatever its name; nothing infinite
    relaxed."""
    from _reproduce import INF, resampling_rule

    shots = "x.json: archived/analysis/gains/k_prior/ci90_circuits_and_shots_not_in_verdict[1]"
    passed = resampling_rule(3.2e-4, shots, "resampled-shots")
    assert passed[0] == 0.0 and "compared at 1e-3, difference 0.00032" in passed[1]
    assert resampling_rule(2e-3, shots, "resampled-shots")[0] == 2e-3
    assert resampling_rule(INF, shots, "resampled-shots")[0] == INF
    assert resampling_rule(3.2e-4, shots, None) == (3.2e-4, shots)  # the same name, unmarked: compared at 10⁻⁶
    boot = "y.json: archived/analysis/fits/A/boot_sd[18]"
    assert resampling_rule(0.013, boot, "resampled-bootstrap", numpy_ok=True)[0] == 0.013
    skipped = resampling_rule(0.013, boot, "resampled-bootstrap", numpy_ok=False)
    assert skipped[0] == 0.0 and skipped[1].startswith(boot) and "not compared under numpy" in skipped[1]
    assert resampling_rule(INF, boot, "resampled-bootstrap", numpy_ok=False)[0] == INF
    assert resampling_rule(0.013, boot, None, numpy_ok=False) == (0.013, boot)


def test_the_marked_fields_are_exactly_the_intended_ones():
    """Amendment A8, R6: the relaxed fields are a list, marked one by one in tests/expected_fields.json, not a pattern
    on their names. Nine intervals that also resample shots, Kickoff 42's nineteen bootstrap SDs, (Amendment A17) the
    283 interval fields of Kickoffs 43 to 47, (Amendment A19) Kickoff 48's 75, (Amendment A22) Kickoffs 49 to 53's
    336, (Amendment A23) Kickoffs 54 and 55's 147, (Amendment A24) Kickoffs 56 to 62's 385, (Amendment A25) test 7's
    32 and (Amendment A27) test 11's job 1's 26, enumerated below."""
    marked = {
        (g["file"], f, o["compare"])
        for groups in load_inventory()["cases"].values()
        for g in groups
        for f, o in g["fields"].items()
        if "compare" in o
    }
    shots = {
        (file, f"archived/analysis/gains/{pick}/ci90_circuits_and_shots_not_in_verdict", "resampled-shots")
        for file in (
            "ibm_fez/k33-payoff.json",
            "ibm_kingston/k33-payoff.json",
            "rigetti_cepheus_1_108q/k40-payoff.json",
        )
        for pick in ("k_prior", "L_prior", "k_now")
    }
    boot = {("rigetti_cepheus_1_108q/k42-after-the-fact.json", "median_boot_sd_deltaA", "resampled-bootstrap")}
    for day in (1, 2):
        file = f"rigetti_cepheus_1_108q/k42-day{day}.json"
        boot |= {(file, f"archived/analysis/fits/{fam}/boot_sd", "resampled-bootstrap") for fam in "AB"}
        boot.add((file, "archived/analysis/V1/median_boot_sd_deltaA", "resampled-bootstrap"))
        boot |= {
            (file, f"archived/analysis/beside/watch_pairs/{p}/{fam}/boot_sd", "resampled-bootstrap")
            for p in ("94-95", "42-43", "18-19")
            for fam in "AB"
        }
    assert marked == (
        shots
        | boot
        | REUSE_MARKED
        | WAIT_TEST_MARKED
        | A22_MARKED
        | A23_MARKED
        | A24_MARKED
        | A25_MARKED
        | A27_MARKED
        | A28_MARKED
    )
    assert (len(shots), len(boot), len(REUSE_MARKED), len(WAIT_TEST_MARKED)) == (9, 19, 283, 75)
    assert (len(A22_MARKED), len(A23_MARKED), len(A24_MARKED), len(A25_MARKED)) == (336, 147, 385, 32)
    assert (len(A27_MARKED), len(A28_MARKED)) == (26, 30)


def _reuse_marked() -> set:
    """Amendment A17: Kickoffs 43 to 47's 90% bootstrap intervals, which also resample shots, and their widths, each
    compared at 10⁻³ as Kickoff 33's intervals are; listed one by one. The ratios of two widths, Kickoff 46's per-pair
    intervals and Kickoff 47's combination intervals move by more than 10⁻³ on another random stream (Linux CI): they
    are in tests/excluded_fields.json, with the measured movement."""
    rs = "resampled-shots"
    out = set()
    f = "ibm_fez/k43-reuse.json"
    summary = ("ci90", "width", "shot_only_boot_ci90", "shot_only_boot_width")
    for g in ("G_reuse", "G_no_reuse", "Delta"):
        out |= {(f, f"archived/analysis/{g}/{x}", rs) for x in summary}
        out |= {(f, f"archived/analysis/per_circuit/{c}/{g}/{x}", rs) for c in REUSE_CIRCUITS for x in summary}
    out |= {
        (f, f"archived/analysis/cells/{c}|{m}|{p}/F_boot_ci90", rs)
        for c in REUSE_CIRCUITS
        for m in ("no_reuse", "reuse")
        for p in ("map", "calibration")
    }
    f = "ibm_fez/k44-reset.json"
    out |= {
        (f, f"archived/analysis/D/{q}/{x}", rs)
        for q in ("c", "e_m", "eps")
        for x in ("ci90", "width", "shot_only_ci90", "shot_only_width")
    }
    f = "ibm_fez/k45-collapse.json"
    out |= {(f, f"archived/analysis/part_A/cells/{c}/ci90", rs) for c in "ABCDEF"}
    out |= {
        (f, f"archived/analysis/part_B/verdicts/{h}/{x}", rs)
        for h in ("H_idle", "H_repeat")
        for x in ("ci90", "shot_only_ci90")
    }
    out.add((f, "archived/analysis/part_B/anomaly_141/ci90", rs))
    out |= {
        (f, f"archived/analysis/part_B/table/{q}/{x}_ci90", rs)
        for q in (117, 123, 124, 125, 131, 132, 138, 141, 142, 143, 144, 151)
        for x in ("x_I1", "x_I2", "r_1", "r_2", "r_3", "first_mid_err")
    }
    f = "ibm_fez/k46-middle.json"
    out |= {(f, f"archived/analysis/part_A/cells/{c}/ci90", rs) for c in "AGHJKC"}
    out.add((f, "archived/analysis/part_B/H_spectator/ci90", rs))
    pairs = ("124;123", "124;125", "131;130", "131;132", "131;138", "142;141", "142;143", "143;136", "143;142")
    pairs += ("143;144", "144;143", "144;145")
    out |= {(f, f"archived/analysis/part_B/table/{p}/c_mid_err_ci90", rs) for p in pairs}
    f = "ibm_fez/k47-wait.json"
    out |= {(f, f"archived/analysis/part_A/cells/{c}{v}/ci90", rs) for c in "AJC" for v in "01"}
    out |= {(f, f"archived/analysis/part_A/gains_beside/{c}/ci90", rs) for c in "AJC"}
    for q in (143, 131, 124, 142, 144, 125):
        b = f"archived/analysis/part_B/qubits/{q}"
        out |= {(f, f"{b}/{v}_ci90/{t}", rs) for v in ("ramsey", "echo") for t in ("0", "1", "2", "3.4", "4", "8")}
        out |= {(f, f"{b}/{x}", rs) for x in ("r_ci90", "e_ci90")}
    return out


def _wait_test_marked() -> set:
    """Amendment A19: Kickoff 48's 90% bootstrap intervals that stay within 10⁻³ over 200 other seeds, each compared at
    10⁻³: Part A's F on each chain and variant, the gains, and Part B's echo intervals and its losses' at 3.4 µs. The
    Ramsey intervals, the Ramsey loss at T_M's, d_M's and the combination intervals move by more: they are in
    tests/excluded_fields.json, with the measured movement."""
    rs, f, a = "resampled-shots", "ibm_fez/k48-wait-test.json", "archived/analysis"
    chains, qubits = ("143", "144", "142", "131", "124"), ("143", "131", "124", "142", "144", "125")
    waits = (0, 250, 500, 850, 1000, 2000, 2612, 4000)
    out = {(f, f"{a}/part_A/{c}/{v}/ci90", rs) for c in chains for v in ("no", "refocus")}
    out |= {(f, f"{a}/prediction/{c}/gain_ci90", rs) for c in chains}
    out |= {(f, f"{a}/part_B/{q}/echo_ci90/{w}", rs) for q in qubits for w in waits}
    out |= {(f, f"{a}/part_B/{q}/{x}", rs) for q in qubits for x in ("r_ci90", "e_ci90")}
    return out


def _a22_marked() -> set:
    """Amendment A22: Kickoffs 49 to 53's 90% bootstrap intervals, each compared at 10⁻³: every interval of each run's
    analysis, less those named in NOT_MARKED, which move by 8·10⁻⁴ or more over 200 other seeds (within reach of 10⁻³ on
    another platform's random stream, A17) or are fitted angles in degrees. Those are in tests/excluded_fields.json,
    with the measured movement. The copies of Kickoff 48's intervals beside Kickoff 49's verdict are compared
    exactly."""
    rs, a = "resampled-shots", "archived/analysis"
    out = set()
    f = "ibm_fez/k49-wait-test.json"
    chains, qubits = ("143", "144", "142", "131", "124"), ("143", "131", "124", "142", "144", "125")
    waits = (0, 250, 500, 850, 1000, 2000, 2612, 4000)
    k49 = {f"{a}/part_A/{c}/{v}/ci90" for c in chains for v in ("no", "refocus")}
    k49 |= {f"{a}/prediction/{c}/{x}" for c in chains for x in ("gain_ci90", "dP_R_TM_ci90", "d_M_ci90")}
    k49 |= {f"{a}/part_B/{q}/{v}_ci90/{w}" for q in qubits for v in ("ramsey", "echo") for w in waits}
    k49 |= {f"{a}/part_B/{q}/{x}" for q in qubits for x in ("r_ci90", "e_ci90", "r_minus_ke_ci90", "ke_minus_jr_ci90")}
    k49 |= {f"{a}/beside/q143_r_ci90"} | {f"{a}/beside/d_M_beside_k48/{c}/d_M_ci90_k49" for c in chains}
    out |= {(f, x, rs) for x in k49}
    f = "ibm_fez/k50-neighbour-test.json"
    for q in ("144", "143"):
        b = f"{a}/per_M/{q}"
        out |= {(f, f"{b}/{x}_ci90", rs) for x in ("F_no", "F_ref", "d0", "d1", "delta_active", "echo_active")}
        out |= {(f, f"{b}/{x}_ci90", rs) for x in ("readout_split", "state_split")}
        out |= {(f, f"{b}/P1_ci90/{c}", rs) for c in ("Z", "R0", "R1", "R2", "R3", "E0", "E1")}
        out |= {(f, f"{b}/loss_ci90/{c}", rs) for c in ("R0", "R1", "R2", "R3", "E0", "E1")}
        out.add((f, f"{a}/beside/d1/{q}/[1]", rs))
    out.add((f, f"{a}/beside/delta_active_143_ci90", rs))
    f = "ibm_fez/k51-known-offset.json"
    for q in ("144", "143"):
        b = f"{a}/per_M/{q}"
        out |= {(f, f"{b}/{x}_ci90", rs) for x in ("A", "A1", "A2", "F_ref", "P1_Z")}
        out |= {(f, f"{b}/{x}_ci90/{p}", rs) for x in ("F_no", "d0", "d1", "d2") for p in ("-90", "0", "90")}
        out |= {(f, f"{b}/loss_ci90/{c}|{p}", rs) for c in ("R0", "R1", "R2") for p in ("-90", "+0", "+90")}
        out |= {(f, f"{b}/fit_{c}/theta_ci90", rs) for c in ("R0", "R2")}
    f = "ibm_fez/k52-phase-sweep.json"
    phases = ("0", "60", "120", "180", "240", "300")
    for q in ("143", "144"):
        b = f"{a}/per_M/{q}"
        out |= {(f, f"{b}/{x}_ci90", rs) for x in ("F_ref", "P1_Z")}
        out |= {(f, f"{b}/{x}_ci90/{p}", rs) for x in ("F_no", "d0", "d1") for p in phases}
        out |= {(f, f"{b}/loss_ci90/{c}|{p}", rs) for c in ("R0", "R1") for p in phases}
        out |= {(f, f"{b}/fits/{c}/theta_ci90", rs) for c in ("W", "R0", "R1")}
        out |= {(f, f"{b}/{d}/ci90", rs) for d in ("Delta_W_minus_R0", "W_minus_R1", "R1_minus_R0")}
    f = "ibm_fez/k53-revised-check.json"
    out |= {(f, f"{a}/cells/[{i}]/{x}_ci90", rs) for i in range(8) for x in ("F_no", "loss_R0", "loss_R1", "d1", "d0")}
    out |= {(f, f"{a}/chains/{c}/{x}_ci90", rs) for c in ("30", "74", "121", "103") for x in ("F_ref", "P1_Z")}
    return out - {(f, x, rs) for f, xs in A22_NOT_MARKED.items() for x in xs}


#: The intervals of Kickoffs 49 to 53 that are excluded, not marked: the fitted angles in degrees, and those that move
#: by 8·10⁻⁴ or more over 200 other seeds (each with its measured movement in tests/excluded_fields.json)
A22_NOT_MARKED = {
    "ibm_fez/k49-wait-test.json": {
        f"archived/analysis/{x}"
        for x in (
            "prediction/144/d_M_ci90",
            "prediction/142/d_M_ci90",
            "beside/d_M_beside_k48/144/d_M_ci90_k49",
            "beside/d_M_beside_k48/142/d_M_ci90_k49",
            "part_B/124/ramsey_ci90/2612",
            "part_B/142/ramsey_ci90/2000",
            "part_B/142/ke_minus_jr_ci90",
            *(f"part_B/{q}/{x}" for q in ("143", "131", "144", "125") for x in ("r_minus_ke_ci90", "ke_minus_jr_ci90")),
        )
    },
    "ibm_fez/k51-known-offset.json": {
        f"archived/analysis/per_M/{x}"
        for x in (
            "144/d0_ci90/0",
            "144/d0_ci90/90",
            "144/d2_ci90/90",
            *(f"{q}/fit_{c}/theta_ci90" for q in ("144", "143") for c in ("R0", "R2")),
        )
    },
    "ibm_fez/k52-phase-sweep.json": {
        f"archived/analysis/per_M/{x}"
        for x in (
            "143/d0_ci90/240",
            "144/d1_ci90/120",
            "144/d1_ci90/240",
            *(f"{q}/fits/{c}/theta_ci90" for q in ("143", "144") for c in ("W", "R0", "R1")),
            *(f"{q}/{d}/ci90" for q in ("143", "144") for d in ("Delta_W_minus_R0", "W_minus_R1", "R1_minus_R0")),
        )
    },
    "ibm_fez/k53-revised-check.json": {
        "archived/analysis/cells/[2]/d1_ci90",
        "archived/analysis/cells/[5]/d1_ci90",
        "archived/analysis/cells/[6]/d0_ci90",
    },
}


def _a23_marked() -> set:
    """Amendment A23: Kickoffs 54 and 55's 90% bootstrap intervals, each compared at 10⁻³: the verdict's (each cell's
    F_no, losses, d1 and d0, and each chain's F_ref and P(1) of Z) and those beside it (P(0|1), the R1 fits', and
    Kickoff 54's pulse costs, single-neighbour fits, shifts and pair), less those named in A23_NOT_MARKED, which move by
    8·10⁻⁴ or more over 200 other seeds or are fitted angles in degrees, as A22's."""
    rs, a = "resampled-shots", "archived/analysis"
    out = set()
    for f, chains, neighbours in (
        ("ibm_fez/k54-revised-check-day-2.json", ("30", "74", "121", "103", "144", "143"), True),
        ("ibm_kingston/k55-revised-check.json", ("155", "18", "7", "43"), False),
    ):
        x5 = ("F_no", "loss_R0", "loss_R1", "d1", "d0")
        out |= {(f, f"{a}/cells/[{i}]/{x}_ci90", rs) for i in range(2 * len(chains)) for x in x5}
        out |= {(f, f"{a}/chains/{c}/{x}_ci90", rs) for c in chains for x in ("F_ref", "P1_Z")}
        out |= {(f, f"{a}/beside/readout_P0_given_1/{c}/ci90", rs) for c in chains}
        out |= {(f, f"{a}/beside/R1_fit/{c}/{x}_ci90", rs) for c in chains for x in ("theta", "amplitude")}
        if neighbours:
            out |= {(f, f"{a}/beside/pulse_cost/{c}/{x}_ci90", rs) for c in chains for x in ("P1", "P1_minus_Z")}
            for q in ("144", "143"):
                b = f"{a}/beside/neighbours/{q}"
                out |= {
                    (f, f"{b}/fits/{v}/{x}_ci90", rs)
                    for v in ("idle", "L1", "L3", "both")
                    for x in ("theta", "amplitude")
                }
                out |= {(f, f"{b}/shift_ci90/{v}", rs) for v in ("L1", "L3", "both")}
                out |= {(f, f"{b}/{x}_ci90", rs) for x in ("sum_of_singles", "sum_minus_both")}
            out |= {(f, f"{a}/beside/pair_143_144/{x}_ci90", rs) for x in ("from_144", "from_143", "difference")}
    return out - {(f, x, rs) for f, xs in A23_NOT_MARKED.items() for x in xs}


#: The intervals of Kickoffs 54 and 55 that are excluded, not marked: the fitted angles in degrees, and those that move
#: by 8·10⁻⁴ or more over 200 other seeds (each with its measured movement in tests/excluded_fields.json)
A23_NOT_MARKED = {
    "ibm_fez/k54-revised-check-day-2.json": {
        f"archived/analysis/{x}"
        for x in (
            *(f"cells/[{i}]/d1_ci90" for i in (1, 3, 9, 11)),
            *(f"cells/[{i}]/d0_ci90" for i in (8, 9)),
            "cells/[3]/loss_R0_ci90",
            *(f"beside/R1_fit/{c}/theta_ci90" for c in ("30", "74", "121", "103", "144", "143")),
            *(
                f"beside/neighbours/{q}/fits/{v}/theta_ci90"
                for q in ("144", "143")
                for v in ("idle", "L1", "L3", "both")
            ),
            "beside/neighbours/143/fits/L1/amplitude_ci90",
            *(f"beside/neighbours/{q}/shift_ci90/{v}" for q in ("144", "143") for v in ("L1", "L3", "both")),
            *(f"beside/neighbours/{q}/{x}_ci90" for q in ("144", "143") for x in ("sum_of_singles", "sum_minus_both")),
            *(f"beside/pair_143_144/{x}_ci90" for x in ("from_144", "from_143", "difference")),
        )
    },
    "ibm_kingston/k55-revised-check.json": {
        f"archived/analysis/{x}"
        for x in (
            *(f"cells/[{i}]/d0_ci90" for i in (2, 3, 5, 6)),
            "cells/[4]/d1_ci90",
            *(f"beside/R1_fit/{c}/theta_ci90" for c in ("155", "18", "7", "43")),
        )
    },
}


#: The intervals of Kickoffs 56 to 62 that are excluded, not marked: the fitted angles' intervals in degrees, and those
#: that move by 8·10⁻⁴ or more over 200 other seeds (each with its measured movement in tests/excluded_fields.json)
A24_NOT_MARKED = {
    "ibm_kingston/k56-phase-sweep.json": {
        "archived/analysis/per_M/18/L_W_minus_R1/ci90",
        "archived/analysis/per_M/18/R1_minus_R0/ci90",
        "archived/analysis/per_M/18/W_minus_R0/ci90",
        "archived/analysis/per_M/18/d0_ci90/0",
        "archived/analysis/per_M/18/d0_ci90/120",
        "archived/analysis/per_M/18/d0_ci90/300",
        "archived/analysis/per_M/18/d1_ci90/0",
        "archived/analysis/per_M/18/d1_ci90/120",
        "archived/analysis/per_M/18/d1_ci90/300",
        "archived/analysis/per_M/18/fits/R0/theta_ci90",
        "archived/analysis/per_M/18/fits/R1/theta_ci90",
        "archived/analysis/per_M/18/fits/W/theta_ci90",
        "archived/analysis/per_M/18/loss_ci90/R1|120",
        "archived/analysis/per_M/43/L_W_minus_R1/ci90",
        "archived/analysis/per_M/43/R1_minus_R0/ci90",
        "archived/analysis/per_M/43/W_minus_R0/ci90",
        "archived/analysis/per_M/43/d0_ci90/120",
        "archived/analysis/per_M/43/d0_ci90/300",
        "archived/analysis/per_M/43/d1_ci90/0",
        "archived/analysis/per_M/43/d1_ci90/180",
        "archived/analysis/per_M/43/d1_ci90/300",
        "archived/analysis/per_M/43/d1_ci90/60",
        "archived/analysis/per_M/43/fits/R0/theta_ci90",
        "archived/analysis/per_M/43/fits/R1/theta_ci90",
        "archived/analysis/per_M/43/fits/W/theta_ci90",
        "archived/analysis/per_M/43/loss_ci90/R0|120",
        "archived/analysis/per_M/7/F_no_ci90/300",
        "archived/analysis/per_M/7/L_W_minus_R1/ci90",
        "archived/analysis/per_M/7/R1_minus_R0/ci90",
        "archived/analysis/per_M/7/W_minus_R0/ci90",
        "archived/analysis/per_M/7/d0_ci90/120",
        "archived/analysis/per_M/7/d0_ci90/300",
        "archived/analysis/per_M/7/d0_ci90/60",
        "archived/analysis/per_M/7/d1_ci90/240",
        "archived/analysis/per_M/7/d1_ci90/300",
        "archived/analysis/per_M/7/d1_ci90/60",
        "archived/analysis/per_M/7/fits/R0/theta_ci90",
        "archived/analysis/per_M/7/fits/R1/theta_ci90",
        "archived/analysis/per_M/7/fits/W/theta_ci90",
        "archived/analysis/per_M/7/loss_ci90/R1|60",
    },
    "ibm_kingston/k57-peak-check.json": {
        "archived/analysis/cells_phi_star/[0]/d0_ci90",
        "archived/analysis/cells_phi_star/[0]/loss_R0_ci90",
        "archived/analysis/check_at_plus90/cells/[0]/F_no_ci90",
        "archived/analysis/check_at_plus90/cells/[0]/d0_ci90",
        "archived/analysis/check_at_plus90/cells/[0]/d1_ci90",
        "archived/analysis/check_at_plus90/cells/[0]/loss_R0_ci90",
        "archived/analysis/check_at_plus90/cells/[0]/loss_R1_ci90",
        "archived/analysis/check_at_plus90/cells/[1]/d0_ci90",
        "archived/analysis/check_at_plus90/cells/[1]/d1_ci90",
        "archived/analysis/check_at_plus90/cells/[1]/loss_R0_ci90",
        "archived/analysis/check_at_plus90/cells/[1]/loss_R1_ci90",
        "archived/analysis/check_at_plus90/cells/[2]/d0_ci90",
        "archived/analysis/check_at_plus90/cells/[2]/d1_ci90",
        "archived/analysis/check_at_plus90/cells/[2]/loss_R1_ci90",
        "archived/analysis/check_at_plus90/cells/[3]/F_no_ci90",
        "archived/analysis/check_at_plus90/cells/[3]/d0_ci90",
        "archived/analysis/check_at_plus90/cells/[3]/d1_ci90",
        "archived/analysis/check_at_plus90/cells/[3]/loss_R0_ci90",
        "archived/analysis/check_at_plus90/cells/[3]/loss_R1_ci90",
        "archived/analysis/job1_fits/1/theta_ci90",
        "archived/analysis/job1_fits/27/theta_ci90",
        "archived/analysis/job1_fits/47/theta_ci90",
        "archived/analysis/job1_fits/89/theta_ci90",
    },
    "ibm_kingston/k58-placement-comparison.json": {
        "archived/analysis/per_chain/18/D_ci90",
        "archived/analysis/per_chain/18/cells/peak/loss_R0_ci90",
        "archived/analysis/per_chain/18/cells/plus90/d0_ci90",
        "archived/analysis/per_chain/18/cells/plus90/loss_R0_ci90",
        "archived/analysis/per_chain/18/job1_fit/theta_ci90",
        "archived/analysis/per_chain/18/original_rule/D0_ci90",
        "archived/analysis/per_chain/43/D_ci90",
        "archived/analysis/per_chain/43/cells/plus90/d0_ci90",
        "archived/analysis/per_chain/43/cells/plus90/loss_R0_ci90",
        "archived/analysis/per_chain/43/job1_fit/theta_ci90",
        "archived/analysis/per_chain/43/original_rule/D0_ci90",
        "archived/analysis/per_chain/7/D_ci90",
        "archived/analysis/per_chain/7/cells/peak/d0_ci90",
        "archived/analysis/per_chain/7/cells/plus90/d0_ci90",
        "archived/analysis/per_chain/7/cells/plus90/d1_ci90",
        "archived/analysis/per_chain/7/job1_fit/theta_ci90",
        "archived/analysis/per_chain/7/original_rule/D0_ci90",
        "archived/analysis/per_chain/7/plus90_beside_kickoff_55/d1_ci90_this_run",
    },
    "ibm_kingston/k59-peak-check-day-2.json": {
        "archived/analysis/cells_phi_star/[0]/d1_ci90",
        "archived/analysis/cells_phi_star/[1]/d0_ci90",
        "archived/analysis/cells_phi_star/[2]/d0_ci90",
        "archived/analysis/check_at_plus90/cells/[0]/F_no_ci90",
        "archived/analysis/check_at_plus90/cells/[0]/d0_ci90",
        "archived/analysis/check_at_plus90/cells/[0]/d1_ci90",
        "archived/analysis/check_at_plus90/cells/[0]/loss_R0_ci90",
        "archived/analysis/check_at_plus90/cells/[0]/loss_R1_ci90",
        "archived/analysis/check_at_plus90/cells/[1]/d0_ci90",
        "archived/analysis/check_at_plus90/cells/[1]/d1_ci90",
        "archived/analysis/check_at_plus90/cells/[1]/loss_R0_ci90",
        "archived/analysis/check_at_plus90/cells/[1]/loss_R1_ci90",
        "archived/analysis/check_at_plus90/cells/[2]/d0_ci90",
        "archived/analysis/check_at_plus90/cells/[2]/d1_ci90",
        "archived/analysis/check_at_plus90/cells/[3]/loss_R1_ci90",
        "archived/analysis/job1_fits/125/theta_ci90",
        "archived/analysis/job1_fits/143/theta_ci90",
        "archived/analysis/job1_fits/23/theta_ci90",
        "archived/analysis/job1_fits/68/theta_ci90",
    },
    "ibm_fez/k61-readout-check.json": {},
    "ibm_fez/k62-peak-check.json": {
        "archived/analysis/cells_phi_star/[0]/loss_R0_ci90",
        "archived/analysis/check_at_plus90/cells/[1]/F_no_ci90",
        "archived/analysis/check_at_plus90/cells/[1]/d0_ci90",
        "archived/analysis/check_at_plus90/cells/[1]/d1_ci90",
        "archived/analysis/check_at_plus90/cells/[1]/loss_R0_ci90",
        "archived/analysis/check_at_plus90/cells/[1]/loss_R1_ci90",
        "archived/analysis/check_at_plus90/cells/[2]/d0_ci90",
        "archived/analysis/check_at_plus90/cells/[2]/d1_ci90",
        "archived/analysis/check_at_plus90/cells/[3]/d0_ci90",
        "archived/analysis/check_at_plus90/cells/[3]/d1_ci90",
        "archived/analysis/job1_fits/110/theta_ci90",
        "archived/analysis/job1_fits/19/theta_ci90",
        "archived/analysis/job1_fits/21/theta_ci90",
        "archived/analysis/job1_fits/95/theta_ci90",
    },
}


def _a24_marked() -> set:
    """Amendment A24: Kickoffs 56 to 59, 61 and 62's 90% bootstrap intervals, each compared at 10⁻³: every field of the
    archived analysis that is an interval (a part of its path names ci90), less those named in A24_NOT_MARKED."""
    rs = "resampled-shots"
    out = set()
    for f in A24_NOT_MARKED:
        doc = ar.load(f)
        out |= {
            (f, x, rs)
            for x in data_fields(doc)
            if x.startswith("archived/analysis/") and any("ci90" in part for part in x.split("/"))
        }
    return out - {(f, x, rs) for f, xs in A24_NOT_MARKED.items() for x in xs}


#: Amendment A25: test 7's fields compared at 10⁻³: those that moved by 10⁻⁶ or more, and less than 8·10⁻⁴, over 200
#: other seeds of every random stream its analysis draws (the bootstrap, the periodogram's noise and the fits' random
#: starts), and its intervals that move less than 8·10⁻⁴; the fields that moved more are excluded with their reasons
A25_MARKED = {
    ("ibm_fez/t7-ramsey-xy.json", f, "resampled-shots")
    for f in (
        "archived/analysis/fits/S/params/A",
        "archived/analysis/fits/S/params/tau_us",
        "archived/analysis/fits/S/params/phi0_rad",
        "archived/analysis/fits/S/chi2",
        "archived/analysis/fits/S/largest_abs_residual_sigma",
        "archived/analysis/fits/P/params/tau_prime_us",
        "archived/analysis/beside/1_telegraph_T/fit/params/c",
        "archived/analysis/beside/1_telegraph_T/fit/params/A",
        "archived/analysis/beside/3_beat_nodes/tau_S_us",
        "archived/analysis/beside/3_beat_nodes/tau_prime_P_us",
        "archived/analysis/beside/4_reading_23p7_kHz/contrasts_in_se/20_22_over_31_33_in_se",
        "archived/analysis/beside/4_reading_23p7_kHz/contrasts_in_se/41_43_over_31_33_in_se",
        "archived/analysis/beside/4_reading_23p7_kHz/contrasts_in_se/41_43_over_52_54_in_se",
        "archived/analysis/beside/4_reading_23p7_kHz/running_mean_max_rise_in_se",
        "archived/analysis/beside/5_detuning_and_T2/S_Delta_kHz",
        "archived/analysis/beside/5_detuning_and_T2/S_abs_Delta_kHz",
        "archived/analysis/beside/5_detuning_and_T2/tau_S_us",
        "archived/analysis/beside/5_detuning_and_T2/tau_prime_P_us",
        "archived/analysis/beside/6_more_than_two/periodogram/floors_95/X",
        "archived/analysis/beside/6_more_than_two/periodogram/floors_95/Y",
        "archived/analysis/beside/6_more_than_two/periodogram/floors_95/complex",
        "archived/analysis/beside/6_more_than_two/sideband_check/fit/params/tau_us",
        "archived/analysis/beside/6_more_than_two/sideband_check/fit/params/phi0_rad",
        "archived/analysis/beside/6_more_than_two/sideband_check/weights_ci90/w144",
        "archived/analysis/beside/6_more_than_two/sideband_check/weights_ci90/w142",
        "archived/analysis/beside/6_more_than_two/sideband_check/weights_ci90/wboth",
        "archived/readings_after_the_data/C_P_on_each_half_of_the_run/first half (positions 0 to 129)/S/chi2",
        "archived/readings_after_the_data/C_P_on_each_half_of_the_run/first half (positions 0 to 129)/S/Delta_kHz",
        "archived/readings_after_the_data/C_P_on_each_half_of_the_run/second half (positions 130 to 259)/P/lines_kHz",
        "archived/readings_after_the_data/C_P_on_each_half_of_the_run/second half (positions 130 to 259)/P/Delta0_kHz",
        "archived/readings_after_the_data/C_P_on_each_half_of_the_run/second half (positions 130 to 259)/"
        "P/tau_prime_us",
        "archived/readings_after_the_data/D_envelope_recentred_on_P_c/running_mean_max_rise_in_se",
    )
}


#: Amendment A27: test 11's job 1, test 7's analysis on day 2, compared at 10⁻³ by A25's rule for test 7: the fields
#: that moved by 10⁻⁶ or more, and less than 8·10⁻⁴, over 200 other seeds of the five random streams its analysis
#: draws, and its intervals that move less than 8·10⁻⁴; the fields that moved more are excluded with their reasons
J1 = "archived/analysis/jobs/1/"
A27_MARKED = {
    ("ibm_fez/t11-day2-monitor.json", f, "resampled-shots")
    for f in (
        J1 + "analysis/fits/S/params/tau_us",
        J1 + "analysis/fits/S/params/phi0_rad",
        J1 + "analysis/fits/S/largest_abs_residual_sigma",
        J1 + "analysis/fits/P/params/tau_prime_us",
        J1 + "analysis/beside/1_telegraph_T/fit/params/c",
        J1 + "analysis/beside/1_telegraph_T/fit/params/phi0_rad",
        J1 + "analysis/beside/3_beat_nodes/tau_S_us",
        J1 + "analysis/beside/3_beat_nodes/tau_prime_P_us",
        J1 + "analysis/beside/4_reading_23p7_kHz/contrasts_in_se/20_22_over_31_33_in_se",
        J1 + "analysis/beside/4_reading_23p7_kHz/contrasts_in_se/41_43_over_31_33_in_se",
        J1 + "analysis/beside/4_reading_23p7_kHz/contrasts_in_se/41_43_over_52_54_in_se",
        J1 + "analysis/beside/4_reading_23p7_kHz/running_mean_max_rise_in_se",
        J1 + "analysis/beside/5_detuning_and_T2/S_Delta_kHz",
        J1 + "analysis/beside/5_detuning_and_T2/S_abs_Delta_kHz",
        J1 + "analysis/beside/5_detuning_and_T2/tau_S_us",
        J1 + "analysis/beside/5_detuning_and_T2/tau_prime_P_us",
        J1 + "analysis/beside/6_more_than_two/periodogram/floors_95/X",
        J1 + "analysis/beside/6_more_than_two/periodogram/floors_95/Y",
        J1 + "analysis/beside/6_more_than_two/periodogram/floors_95/complex",
        J1 + "analysis/beside/6_more_than_two/sideband_check/fit/params/tau_us",
        J1 + "analysis/beside/6_more_than_two/sideband_check/weights_ci90/w144",
        J1 + "analysis/beside/6_more_than_two/sideband_check/weights_ci90/w142",
        J1 + "readings_after_the_data/C_P_on_each_half_of_the_run/first half (positions 0 to 129)/S/Delta_kHz",
        J1 + "readings_after_the_data/C_P_on_each_half_of_the_run/first half (positions 0 to 129)/P/tau_prime_us",
        J1 + "readings_after_the_data/C_P_on_each_half_of_the_run/second half (positions 130 to 259)/S/Delta_kHz",
        J1 + "readings_after_the_data/C_P_on_each_half_of_the_run/second half (positions 130 to 259)/P/tau_prime_us",
    )
}


#: Amendment A28: test 11's job 1 on a third day, by A27's rule for day 2: the fields that moved by 10⁻⁶ or more, and
#: less than 8·10⁻⁴, over 200 other seeds of the five random streams its analysis draws, and its intervals that move
#: less than 8·10⁻⁴, compared at 10⁻³; the fields that moved more are excluded with their reasons
A28_MARKED = {
    ("ibm_fez/t11-day3-monitor.json", f, "resampled-shots")
    for f in (
        J1 + "analysis/fits/S/params/tau_us",
        J1 + "analysis/fits/S/params/phi0_rad",
        J1 + "analysis/fits/S/largest_abs_residual_sigma",
        J1 + "analysis/fits/P/params/tau_prime_us",
        J1 + "analysis/beside/1_telegraph_T/fit/largest_abs_residual_sigma",
        J1 + "analysis/beside/1_telegraph_T/gamma_ci90_per_us",
        J1 + "analysis/beside/1_telegraph_T/delta_T_kHz",
        J1 + "analysis/beside/1_telegraph_T/lines_against_the_band/T_lines_kHz",
        J1 + "analysis/beside/1_telegraph_T/lines_against_the_band/T_reach_kHz",
        J1 + "analysis/beside/3_beat_nodes/tau_S_us",
        J1 + "analysis/beside/3_beat_nodes/tau_prime_P_us",
        J1 + "analysis/beside/4_reading_23p7_kHz/contrasts_in_se/20_22_over_31_33_in_se",
        J1 + "analysis/beside/4_reading_23p7_kHz/contrasts_in_se/41_43_over_31_33_in_se",
        J1 + "analysis/beside/4_reading_23p7_kHz/contrasts_in_se/41_43_over_52_54_in_se",
        J1 + "analysis/beside/4_reading_23p7_kHz/running_mean_max_rise_in_se",
        J1 + "analysis/beside/5_detuning_and_T2/S_Delta_kHz",
        J1 + "analysis/beside/5_detuning_and_T2/S_abs_Delta_kHz",
        J1 + "analysis/beside/5_detuning_and_T2/tau_S_us",
        J1 + "analysis/beside/5_detuning_and_T2/tau_prime_P_us",
        J1 + "analysis/beside/6_more_than_two/periodogram/floors_95/X",
        J1 + "analysis/beside/6_more_than_two/periodogram/floors_95/Y",
        J1 + "analysis/beside/6_more_than_two/periodogram/floors_95/complex",
        J1 + "analysis/beside/6_more_than_two/sideband_check/fit/params/tau_us",
        J1 + "analysis/beside/6_more_than_two/sideband_check/weights_ci90/w144",
        J1 + "analysis/beside/6_more_than_two/sideband_check/weights_ci90/w142",
        J1 + "readings_after_the_data/C_P_on_each_half_of_the_run/first half (positions 0 to 129)/S/Delta_kHz",
        J1 + "readings_after_the_data/C_P_on_each_half_of_the_run/first half (positions 0 to 129)/P/tau_prime_us",
        J1 + "readings_after_the_data/C_P_on_each_half_of_the_run/second half (positions 130 to 259)/S/chi2",
        J1 + "readings_after_the_data/C_P_on_each_half_of_the_run/second half (positions 130 to 259)/S/Delta_kHz",
        J1 + "readings_after_the_data/C_P_on_each_half_of_the_run/second half (positions 130 to 259)/P/tau_prime_us",
    )
}


REUSE_CIRCUITS = ("XOR_5", "BV_10", "Mul_13", "Sym_9")
REUSE_MARKED = _reuse_marked()
WAIT_TEST_MARKED = _wait_test_marked()
A22_MARKED = _a22_marked()
A23_MARKED = _a23_marked()
A24_MARKED = _a24_marked()
