# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""Amendment A27: the desk model Sandhi beside finding 29 (data/desk/sandhi/). Its run is published as delivered and
checked against its own SHA256SUMS; its report carries the counts finding 29 quotes; the weight boundaries that the
repository's own records hold are recomputed from them; and, where the ledgers attached to the release are given
(MANACITRA_SANDHI_LEDGERS, a folder holding them), every count is recomputed from the ledgers' rows."""

import hashlib
import json
import math
import os
import re
from pathlib import Path

import pytest

from manacitra import archive

ROOT = archive.data_dir() / "desk" / "sandhi"
RUN = ROOT / "v3.1"
PREDICTIONS = {
    "predictions-model-01-v3.md": "745059e38db0e54f4bcef2bc8cad17a2fde40223f0a1dde75982a621817a38a3",
    "predictions-model-01-v3.json": "02b8003461f948991217be683bc0706f611da57ac4e03d53ca8745274fc019b4",
}
#: The two ledgers attached to the release as copies, their one `command` field written "[the desk runner's
#: environment]" (A27, ruling R1, item 4): the SHA-256 of each copy as published
PUBLISHED = {
    "events-model-01-v3.json": "000a75d40761f6f28ce9221134fe700d3a883538ffbb89dbd1346259e8350618",
    "frequency-ledger.json": "14ceaf554d9a843d35c72b406fd6d9b6814eb7f8f48a559f56fe2d574043b73f",
}
#: The frequency counts at 4 kHz the kickoff names, per job: (within-span events, trials, boundary events, trials)
FREQUENCY = {
    "9, job 2": (0, 509, 0, 77),
    "9, job 3": (0, 349, 0, 55),
    "10, job 1": (0, 9100, 1, 125),
    "10, job 2": (0, 9033, 0, 124),
    "10, job 3": (0, 7073, 0, 98),
}


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _sums() -> dict:
    out = {}
    for line in (RUN / "SHA256SUMS").read_text().splitlines():
        if line.strip():
            h, name = line.split(maxsplit=1)
            out[name.strip()] = h
    return out


def test_the_run_is_published_as_delivered():
    """Every file of the run here matches its line in the run's own SHA256SUMS, the two prediction files carry the
    digests the folder's README gives, and the kickoffs carry no name of the desk runner's service."""
    sums = _sums()
    files = [p for p in RUN.rglob("*") if p.is_file() and p.name != "SHA256SUMS" and not archive.is_bundle(p)]
    assert files and all(_sha(p) == sums[p.relative_to(RUN).as_posix()] for p in files)
    readme = (ROOT / "README.md").read_text()
    for name, h in PREDICTIONS.items():
        assert _sha(RUN / name) == h == sums[name] and h in readme
    # the signing workflow's bundles (FILE.sigstore.json) sit beside the files on main, and are not the folder's files
    for k in (p for p in (ROOT / "kickoffs").iterdir() if not archive.is_bundle(p)):
        text = k.read_text()
        assert not re.search(r"chat\s*gpt|open\s*ai", text, re.I), k.name
        assert _sha(k) in readme, k.name
    for held in ("run.log", "events-model-01-v3.json", "frequency-ledger.json"):
        assert held in sums and not (RUN / held).exists() and f"`{held}`" in readme
    for name, h in PUBLISHED.items():
        assert sums[name] in readme and h in readme, name  # both hashes of each copy (A27, R1, item 4)


def test_the_report_carries_the_counts_finding_29_quotes():
    """The run's report, a hashed record, holds the counts and rates finding 29 states, and its three sentences."""
    rep = (RUN / "report-model-01-v3.md").read_text()
    for job, (we, wn, be, bn) in FREQUENCY.items():
        assert f"| {job} | {we} / {wn} | {be} / {bn} |" in rep, job
    for row in (
        "| All shuffled | 16 / 38 | 11 / 38 |",
        "| Test 11 monitors | 4 / 4 | 1 / 4 |",
        "| F at 4kHz | 1 / 479 |",
        "| S at 4kHz | 17 / 48 |",
        "| W_B at own | 0 / 285 |",
    ):
        assert row in rep, row
    for s in (
        "The model is a kinetic description; it names no cause.",
        "A record below its own floor is censored, not absent.",
        "The predictions are the model's, written before the run they predict, and they are what can prove it wrong.",
    ):
        assert s in rep
    assert "No eligible observed cell lies outside its simulated 5th to 95th percentiles." in rep


def _events(means, nearest):
    """Adjacent span means against five combined errors (the record's own resolution), and the nearest three on
    either side of each boundary against 0.10 (the fixed floor)."""
    own = [abs(b[0] - a[0]) > 5 * math.hypot(a[1], b[1]) for a, b in zip(means, means[1:])]
    fixed = [abs(sum(after) / len(after) - sum(before) / len(before)) >= 0.10 for before, after in nearest]
    return sum(own), sum(fixed), len(own)


def test_the_weight_boundaries_the_records_hold():
    """The weight boundaries of test 7 and of test 11's three jobs, recomputed from the repository's records: the
    shuffled jobs' span means and errors (A26's method) and nearest three positions; the monitor's span means, each
    with the larger of its propagated error and its scatter, and nearest three whole repeats. They are the model's
    rows: t7, 2 of 2 and 1 of 2; test 11's job 1, 1 of 2 and 0 of 2; the monitors, 4 of 4 and 1 of 4."""
    rep = (RUN / "report-model-01-v3.md").read_text()
    t7 = archive.load("ibm_fez/t7-span-readings.json")
    t11 = archive.load("ibm_fez/t11-day2-monitor.json")["archived"]["analysis"]["jobs"]
    for name, sr, row in (
        ("t7", t7, "| t7 job1 | 2 / 2 | 1 / 2 |"),
        ("t11", t11["1"]["span_readings_A26"], "| t11 job1 | 1 / 2 | 0 / 2 |"),
    ):
        means = [(x["weighted_mean"], x["se"]) for x in sr["weight_per_span"]]
        near = [
            ([x["weight"] for x in b["before"]], [x["weight"] for x in b["after"]])
            for b in sr["span_boundaries"].values()
        ]
        own, fixed, n = _events(means, near)
        assert row == f"| {name} job1 | {own} / {n} | {fixed} / {n} |" and row in rep
    own = fixed = n = 0
    for j in ("2", "3"):
        rows = [r for r in t11[j]["repeats"] if not r["straddles"]]
        spans = list(dict.fromkeys(r["span"] for r in rows))
        means = []
        for x in t11[j]["weight"]["per_span"]:
            means.append((x["mean_w"], max(x["se_propagated"], x["se_sd_over_sqrt_n"])))
        near = []
        for a, b in zip(spans, spans[1:]):
            near.append(([r["w"] for r in rows if r["span"] == a][-3:], [r["w"] for r in rows if r["span"] == b][:3]))
        o, f, m = _events(means, near)
        own, fixed, n = own + o, fixed + f, n + m
    assert f"| Test 11 monitors | {own} / {n} | {fixed} / {n} |" == "| Test 11 monitors | 4 / 4 | 1 / 4 |"


LEDGERS = os.environ.get("MANACITRA_SANDHI_LEDGERS")


@pytest.mark.skipif(not LEDGERS, reason="needs the ledgers (MANACITRA_SANDHI_LEDGERS, a folder holding them)")
def test_every_count_from_the_ledgers():
    """From the ledgers themselves, each first checked against the run's SHA256SUMS or, for a copy attached to the
    release, against its published SHA-256: the frequency counts at 4 kHz per
    job, within spans and at their boundaries, and the weight boundaries of the shuffled jobs, 16 of 38 at the record's
    resolution and 11 of 38 at 0.10."""
    d, sums = Path(LEDGERS), _sums()
    for name in ("frequency-ledger.json", "shuffled-stamp-ledger.json"):
        assert _sha(d / name) in (sums[name], PUBLISHED.get(name)), name
    rows = json.loads((d / "frequency-ledger.json").read_text())["rows"]
    for job, want in FREQUENCY.items():
        t, j = (int(x) for x in re.findall(r"\d+", job))
        got = []
        for cls in ("within_span", "span_boundary"):
            sel = [r for r in rows if (r["test"], r["job"], r["trial_class"]) == (t, j, cls) and r["eligible_4khz"]]
            got += [sum(1 for r in sel if r["event_4khz"]), len(sel)]
        assert tuple(got) == want, job
    wb = json.loads((d / "shuffled-stamp-ledger.json").read_text())["weight_boundaries"]
    assert (len(wb), sum(r["event_own"] for r in wb), sum(r["event_fixed"] for r in wb)) == (38, 16, 11)
