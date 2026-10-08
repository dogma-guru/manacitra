# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""Write, or check, data/PROGRAMS.md: one row per program file (.qasm, .quil) under data/ (Amendment A8, R2).

    python tools/program_catalogue.py --write
    python tools/program_catalogue.py --check

The JSON records carry their own meta blocks; the program files cannot, so this catalogue indexes them. Each row gives
the file, the run and task(s) it belongs to, the processor and route, each task's UTC creation and end (or completion)
time and its shots, and the file's SHA-256, all read from the run records that sent the program or returned it. A file
sent by more than one task (a program re-sent, or sent by two kickoffs) has one line per use in its row.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
OUT = DATA / "PROGRAMS.md"
RIG = "rigetti_cepheus_1_108q"
ROUTE = {
    "braket": "Rigetti Cepheus-1-108Q, through Amazon Braket, pinned",
    "openquantum": "Rigetti Cepheus-1-108Q, through Open Quantum, Public plan",
}
KINDS = {".qasm": "as sent", ".quil": "compiled, as returned"}


def _load(name: str) -> dict:
    return json.loads((DATA / RIG / name).read_text())


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def program_files(data: Path = DATA) -> list[Path]:
    return sorted(p for p in data.rglob("*") if p.is_file() and p.suffix in KINDS)


def uses() -> dict[str, list[dict]]:
    """Per program file (its path under data/), every task that sent it or returned it, from the run records."""
    out: dict[str, list[dict]] = {}

    def add(path: str, run: str, route: str, task: str, created: str, ended: str, shots: int):
        out.setdefault(path, []).append(
            {"run": run, "route": route, "task": task, "created": created, "ended": ended, "shots": shots}
        )

    # Kickoffs 34b, 37 and 38, through Open Quantum: the programs are named by their SHA-256 in each record's meta.
    # Kickoff 34b's main job records its times per wave, not per task: its line gives the wave's submission and the
    # wave's last completion.
    by_sha = {_sha(p): f"{RIG}/{p.name}" for p in (DATA / RIG).glob("*.qasm")}
    main = _load("main.json")["meta"]
    for prog in main["programs"]["in_this_release"]:
        wave = 1 if prog["position"] <= 8 else 2
        w = main["utc_main_job"]
        task = f"main job, position {prog['position']}, {prog['label']} (wave {wave}; per-task times not recorded)"
        add(
            by_sha[prog["sha256"]],
            "Kickoff 34b",
            ROUTE["openquantum"],
            task,
            w[f"wave_{wave}_submitted"],
            w[f"wave_{wave}_completed"][-1],
            main["shots_per_circuit"],
        )
    for record, run in (("k37-placement.json", "Kickoff 37"), ("k38-activity.json", "Kickoff 38")):
        m = _load(record)["meta"]
        for t in m["tasks"]:
            path = by_sha[m["programs_sha256"][t["program"]]]
            label = f"{t['label']} ({t['program']})"
            add(path, run, ROUTE["openquantum"], label, t["created_utc"], t["completed_utc"], m["shots_per_task"])
    # Kickoff 40, through Amazon Braket: by stage, each task's program as sent and as compiled, by its label
    for record, stage in (("k40-placement.json", "stage1"), ("k40-map.json", "stage2"), ("k40-payoff.json", "stage3")):
        for t in _load(record)["tasks"]:
            for folder, suffix in (("programs", ".qasm"), ("compiled", ".quil")):
                path = f"{RIG}/{folder}/k40/{stage}/{t['task_label']}{suffix}"
                add(
                    path,
                    f"Kickoff 40, stage {stage[-1]}",
                    ROUTE["braket"],
                    t["task_label"],
                    t["created_utc"],
                    t["ended_utc"],
                    t["shots"],
                )
    # Kickoff 41: Kickoff 40's programs re-sent (k41-figures.json names each file); its own compiled programs
    figures = _load("k41-figures.json")["programs"]
    for record, part in (("k41-map.json", "A"), ("k41-payoff.json", "B")):
        sent = {Path(r["file"]).stem: f"{RIG}/{r['file']}" for r in figures[part]}
        for t in _load(record)["tasks"]:
            run = f"Kickoff 41, Part {part}"
            add(
                sent[t["task_label"]],
                run,
                ROUTE["braket"],
                t["task_label"],
                t["created_utc"],
                t["ended_utc"],
                t["shots"],
            )
            path = f"{RIG}/compiled/k41/part{part}/{t['task_label']}.quil"
            add(path, run, ROUTE["braket"], t["task_label"], t["created_utc"], t["ended_utc"], t["shots"])
    # Kickoff 42: one set of programs, sent on both days; each day's compiled programs
    for day in (1, 2):
        for t in _load(f"k42-day{day}.json")["tasks"]:
            run = f"Kickoff 42, Day {day}"
            for path in (
                f"{RIG}/programs/k42/{t['task_label']}.qasm",
                f"{RIG}/compiled/k42/day{day}/{t['task_label']}.quil",
            ):
                add(path, run, ROUTE["braket"], t["task_label"], t["created_utc"], t["ended_utc"], t["shots"])
    return out


def catalogue(data: Path = DATA) -> str:
    u = uses()
    rows = []
    for p in program_files(data):
        rel = p.relative_to(data).as_posix()
        if rel not in u:
            raise SystemExit(f"{rel}: no run record names this program file")
        us = u[rel]
        cells = [
            f"`{rel}`",
            KINDS[p.suffix],
            "<br>".join(f"{x['run']}: {x['task']}" for x in us),
            "<br>".join(sorted({x["route"] for x in us})),
            "<br>".join(f"{x['created']} to {x['ended']}" for x in us),
            "<br>".join(str(x["shots"]) for x in us),
            f"`{_sha(p)}`",
        ]
        rows.append("| " + " | ".join(cells) + " |")
    missing = sorted(set(u) - {p.relative_to(data).as_posix() for p in program_files(data)})
    if missing:
        raise SystemExit(f"run records name program files that are not in data/: {missing[:5]}")
    head = [
        "# Program files",
        "",
        "Every program file in `data/`: the programs as sent (`.qasm`) and the compiled programs the provider returned",
        "(`.quil`). They are data, under [`LICENSE`](LICENSE), like the JSON records. The JSON records carry their own",
        "`meta` blocks; these files cannot, so this catalogue indexes them, from the run records that sent or returned",
        "each one. A file sent by more than one task has one line per use. Times are as the run records give them",
        "(UTC: creation to end, or to completion as the runner's poller saw it).",
        "",
        "Generated by `python tools/program_catalogue.py --write`; `tests/test_program_catalogue.py` regenerates it",
        "and compares it byte for byte.",
        "",
        f"{len(rows)} files.",
        "",
        "| file | kind | run: task | processor and route | UTC | shots | SHA-256 |",
        "|---|---|---|---|---|---|---|",
    ]
    return "\n".join(head + rows) + "\n"


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    text = catalogue()
    if a.write:
        OUT.write_text(text)
        print(f"wrote {OUT} ({sum(line.startswith('| `') for line in text.splitlines())} files)")
    else:
        ok = OUT.exists() and OUT.read_text() == text
        print("data/PROGRAMS.md matches every program file" if ok else "data/PROGRAMS.md is out of date")
        sys.exit(0 if ok else 1)
