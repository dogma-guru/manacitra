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
#: A command session's handle as the desk runner's polling calls passed it: a session_id followed by digits, alone or
#: as an array, or an array of digits mapped to session_id (A28, ruling R3, item 1)
HANDLE = re.compile(r"session_id\W{0,4}\d|\[[\d,]+\]\.map\(session_id")
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
        assert not re.search(r"chat\s*gpt|open\s*ai|codex", text, re.I), k.name
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


# --------------------------------------------------------------------------- versions 4 and 4.1 (Amendment A28)
#: The digests the author posted before each version's run: version 4's in issue 66, before test 11's third day, and
#: version 4.1's in issue 68, before test 17
POSTED_V4 = {
    "v4": (
        66,
        {
            "predictions-model-01-v4.md": "718a0b86f3caeb832630a2431f6c14e137d9c0b90ffe10ac877cbc0ac5b7481b",
            "predictions-model-01-v4.json": "cd8e4b87b64aa818a43b533ed0725cda47af79f1c1be25890743f1c1646f92af",
            "score_model_01_v4.py": "42287f2e3f881b148bfa10f23cfbc190dff2959fc156e0bdb88b6e627601d7bf",
            "FORECAST-SHA256SUMS": "1115b9bdddb43c0e81a68905709a8025d58106799e69da40f89614e76bddfcc2",
        },
    ),
    "v4.1": (
        68,
        {
            "predictions-model-01-v4.1.md": "5b2e45dea15f613d4314a959d5c06bebf0a663a5f1cb7e607f442ce45b98628f",
            "predictions-model-01-v4.1.json": "a30488be57eade0df185c594cd83befa5817f8e54261a47423017d0d9814fc54",
            "score_model_01_v4_1.py": "ae4aed5c957c5c5942629e82a5ccd291141a3038cb2a8aa490ff3f165493632c",
            "FORECAST-SHA256SUMS": "7903a281ccc808ed8dd13c4b316919554879ec29a353f7093642c98b9081b083",
        },
    ),
}


def _sums_of(path: Path) -> dict:
    out = {}
    for line in path.read_text().splitlines():
        if line.strip():
            h, name = line.split(maxsplit=1)
            out[name.strip()] = h
    return out


@pytest.mark.parametrize("version", ["v4", "v4.1"])
def test_versions_4_and_4_1_are_published_as_delivered(version):
    """Amendment A28, section 3: every file of the version here is its run's file, checked against the run's own
    SHA256SUMS, or, where the folder's README lists a replacement ("[local path]", "the desk runner", the session or,
    by ruling R2, the name of its variable), carries the published SHA-256 the README gives beside the delivered one,
    which is the run's; the scorer and its dependencies match FORECAST-SHA256SUMS, whose own digest and the
    predictions' are those posted; the compiled library is not committed; and no file names a home path or the desk
    runner's service."""
    folder = ROOT / version
    sums = _sums_of(folder / "SHA256SUMS")
    forecast = _sums_of(folder / "FORECAST-SHA256SUMS")
    readme = (ROOT / "README.md").read_text()
    issue, posted = POSTED_V4[version]
    assert f"[issue {issue}](https://github.com/dogma-guru/manacitra/issues/{issue})" in readme
    files = sorted(p for p in folder.iterdir() if p.is_file() and not archive.is_bundle(p))
    assert files and not (folder / "hmm_core.dylib").exists() and "hmm_core.dylib" in forecast
    replaced = 0
    for p in files:
        h = _sha(p)
        name = p.name
        row = next(line for line in readme.splitlines() if line.startswith(f"| `{version}/{name}` |"))
        if name.startswith("scorecard-t1"):  # from the tests' hand-backs, not the model's runs
            hashes = re.findall(r"`([0-9a-f]{64})`", row)
            assert h == hashes[-1] and (len(hashes) == 2 or row.endswith("| the same |")), name
            continue
        if name == "SHA256SUMS":
            assert row.endswith(f"`{h}` | the same |")
            continue
        if row.endswith("| the same |"):
            assert h == sums[name], name
        else:
            replaced += 1
            assert f"| `{sums[name]}` | `{h}` |" in row, name
            assert name not in forecast, name  # nothing the forecast hashed is changed
        if name in forecast:
            assert h == forecast[name], name
        text = p.read_text()
        assert not re.search(r"/Users/|/home/|chat\s*gpt|open\s*ai|codex", text, re.I), name
        assert not HANDLE.search(text), name
    for name, h in posted.items():
        assert _sha(folder / name) == h and h in readme, name
    assert replaced == {"v4": 3, "v4.1": 4}[version]


def test_the_command_session_handles_are_refused():
    """A28, ruling R3, item 1: version 4.1's run log carried, at 61f34df, the handles of the command sessions its
    polling calls read, 30 of them, six values on 14 lines; each is written "[a command session]", and the files check
    above refuses a handle in any form. The negative control writes one handle back into the published log, in memory,
    and then every handle, as the log stood at 61f34df; the check must catch both."""
    log = (ROOT / "v4.1" / "run.log").read_text()
    assert log.count("[a command session]") == 30 and not HANDLE.search(log)
    lines = [line for line in log.split("\n") if "[a command session]" in line]
    assert len(lines) == 14
    assert HANDLE.search(log.replace("[a command session]", "30707", 1))
    assert HANDLE.search(log.replace("[a command session]", "21563"))
    assert HANDLE.search("const rs=await Promise.allSettled([21563,93745].map(session_id=>tools.write_stdin(")


def test_the_scorecards_family_counts():
    """Amendment A28, section 3: the scorecards as the scorers wrote them, the local paths aside. Version 4's on test
    11's third day (test 16) scored no calibrated bet, every family "not fully testable"; version 4.1's on test 17's
    long job (D2) scored 12 duty bets with 0 misses (cutoff 5), 24 correlation bets with 0 (cutoff 9) and 4 emission
    bets with 2 (cutoff 3), no family counting against it, and no likelihood rejection at 1 percent against 0.62."""
    c16 = json.loads((ROOT / "v4" / "scorecard-t16.json").read_text())
    assert {f["status"] for f in c16["families"]} == {"not fully testable"}
    assert sum(f["bets_scored"] for f in c16["families"]) == sum(f["misses"] for f in c16["families"]) == 0
    assert (
        c16["sharing_spans_counting_against"] == []
        and c16["prediction_sha256"] == POSTED_V4["v4"][1]["predictions-model-01-v4.json"]
    )
    c17 = json.loads((ROOT / "v4.1" / "scorecard-t17.json").read_text())
    fam = {
        f["family"]: (f["bets_scored"], f["misses"], f["smallest_miss_count_under_0p05"], f["counts_against"])
        for f in c17["families"]
    }
    assert fam == {"duty": (12, 0, 5, False), "correlation": (24, 0, 9, False), "emissions": (4, 2, 3, False)}
    assert c17["matching_scenario"] == "actual" and c17["any_monitor_boundary_LR_p_under_0p01"] is False
    assert c17["prediction_sha256"] == POSTED_V4["v4.1"][1]["predictions-model-01-v4.1.json"]
    (actual,) = [x for x in c17["scenario_scores"] if x["scenario"] == "actual"]
    (lr,) = [e for e in actual["probability_events"] if e["prediction"] == "any_LR_reject_probability"]
    assert (lr["probability"], lr["observed"]) == (0.62, False)
    for c in (c16, c17):
        assert c["prediction_file"] == "[local path]"
