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
    on their names. Nine intervals that also resample shots, Kickoff 42's nineteen bootstrap SDs, and (Amendment A17)
    the 283 interval fields of Kickoffs 43 to 47, enumerated below."""
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
    assert marked == shots | boot | REUSE_MARKED and (len(shots), len(boot), len(REUSE_MARKED)) == (9, 19, 283)


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


REUSE_CIRCUITS = ("XOR_5", "BV_10", "Mul_13", "Sym_9")
REUSE_MARKED = _reuse_marked()
