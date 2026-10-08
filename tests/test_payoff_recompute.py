# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""Amendment A11, item 3: Kickoff 33's payoff on ibm_fez, recomputed from the raw counts as the data README documents
it, against literals computed outside the package.

The literals below are the output of tests/_independent_readings.py (k33_payoff), which does not import manacitra: the
prior map from Kickoff 32's dense condition, each random circuit's two runs pooled per pair, the squared Hellinger
overlap against the workload's ideals on uncorrected counts, and the x recorded at submission."""

import runpy
from pathlib import Path

import pytest

from manacitra import archive

ROOT = Path(__file__).resolve().parents[1]

# From tests/_independent_readings.py (Amendment A11), run on the archive at 44a36db; errors rounded to 5 places
INDEPENDENT = {
    "pick_by_map": [[106, 107], [88, 89], [151, 152], [94, 95], [142, 143], [129, 130], [13, 14], [114, 115]],
    "pick_by_published": [[22, 23], [5, 6], [85, 86], [70, 71], [114, 115], [123, 124], [142, 143], [106, 107]],
    "shots_per_circuit_pooled": 16000,
    "error_map_pick": 0.00221,
    "error_published_pick": 0.00343,
    "less_error_percent": 35.6,
}


def _pairs(pick) -> str:
    return ", ".join(f"{a}-{b}" for a, b in pick)


def test_the_example_makes_the_independent_picks(capsys):
    """examples/03_pick_pairs.py, which goes through the package, prints the two picks and the 35.6%."""
    runpy.run_path(str(ROOT / "examples" / "03_pick_pairs.py"), run_name="__main__")
    out = capsys.readouterr().out
    assert f"chosen by the map:             {INDEPENDENT['pick_by_map']}" in out
    assert f"chosen by the published rates: {INDEPENDENT['pick_by_published']}" in out
    assert (
        f"map's pick {INDEPENDENT['error_map_pick']:.5f}, published pick {INDEPENDENT['error_published_pick']:.5f}"
        in out
    )
    assert f"the map's pick had {INDEPENDENT['less_error_percent']:.1f}% less error" in out


def test_the_pooling_the_record_implies():
    pay = archive.load("ibm_fez/k33-payoff.json")
    runs = [label for label in pay["order"] if label.startswith("R")]
    assert sorted(set(runs)) == [f"R{j}" for j in range(1, 9)] and all(runs.count(r) == 2 for r in set(runs))
    assert 2 * pay["meta"]["shots_per_circuit"] == INDEPENDENT["shots_per_circuit_pooled"]


def test_the_data_readme_and_the_readme_document_it():
    data = " ".join((archive.data_dir() / "README.md").read_text().split())
    assert f"The map's pick is {_pairs(INDEPENDENT['pick_by_map'])}." in data
    assert f"The published figures' pick is {_pairs(INDEPENDENT['pick_by_published'])}." in data
    assert "The mean error is 0.00221 for the map's pick and 0.00343 for the published pick, 35.6% less." in data
    assert "Kickoff 32's dense condition" in data and "(16,000 shots)" in data
    readme = (ROOT / "docs" / "findings.md").read_text()  # finding 4 in full, which the README's table links to
    assert "the prior map is Kickoff 32's dense condition" in readme
    assert "`python examples/03_pick_pairs.py` makes both picks" in readme


@pytest.mark.parametrize("key", ["pick_by_map", "pick_by_published"])
def test_the_package_picks_agree(key):
    """The package's own picks, as the payoff analysis records them, are the independent ones."""
    fez = archive.fez_or_kingston("ibm_fez")
    k33 = fez["k33-payoff"]
    picks = k33["archived"]["analysis"]["picks"]["k_prior" if key == "pick_by_map" else "x"]
    assert [k33["pairs"][i] for i in picks] == INDEPENDENT[key]
