"""Assemble the hand-back (rule section 6, runner prompt 'At the go' item 5). No AWS calls.

Order, as the runner prompt sets it: the report is already written; copy it with the raw result files, the programs,
the scripts as run and the logs; write SHA256SUMS over the hand-back; then search every file and write the redaction log.
The search covers twelve-digit account numbers, arn:aws strings carrying one, access keys, bucket names and email
addresses (common.redact), plus the working folder's name, the profile name and home paths. Any hit stops the script
before the hand-back is called ready.
"""
import os
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import HERE, redact, sha, utc

HANDBACK = Path.home() / "[the hand-back folder]"
EXTRA = [re.compile(re.escape(HERE.parent.name)), re.compile(re.escape(str(Path.home())))]
if os.environ.get("AWS_PROFILE"):
    EXTRA.append(re.compile(re.escape(os.environ["AWS_PROFILE"])))


def copy_in():
    HANDBACK.mkdir(parents=True, exist_ok=True)
    picks = ["report-probe-01.md", "run-log.json", "run.log", "go.log", "braket-probe-01-wait-rule.md", "rule.sha256"]
    # attempt-1: Task A refused by the spending limit window; attempt-2: Task A queued outside a window, then cancelled
    for prior in sorted(HERE.glob("attempt-*")):
        if prior.is_dir():
            shutil.copytree(prior, HANDBACK / prior.name, dirs_exist_ok=True)
    for name in picks:
        if (HERE / name).exists():
            shutil.copy2(HERE / name, HANDBACK / name)
    if (HERE / "redaction-log.md").exists():
        shutil.copy2(HERE / "redaction-log.md", HANDBACK / "raw-redaction-log.md")
    for sub, pattern in (("raw", "*"), ("programs", "*"), ("scripts", "*.py")):
        (HANDBACK / sub).mkdir(exist_ok=True)
        for f in sorted((HERE / sub).glob(pattern)):
            if f.is_file():
                shutil.copy2(f, HANDBACK / sub / f.name)


def files():
    return sorted(p for p in HANDBACK.rglob("*") if p.is_file() and p.name not in ("SHA256SUMS", "redaction-log.md"))


def main():
    copy_in()
    sums = "".join(f"{sha(p)}  {p.relative_to(HANDBACK).as_posix()}\n" for p in files())
    (HANDBACK / "SHA256SUMS").write_text(sums)
    rows, hits = [], []
    for p in files() + [HANDBACK / "SHA256SUMS"]:
        rel = p.relative_to(HANDBACK).as_posix()
        text = p.read_text(errors="replace")
        _, entries = redact(text, rel)
        for e in entries:
            rows.append(e)
            if e["action"] == "redacted":
                hits.append(f"{rel}: {e['kind']} ({e['count']})")
        for rx in EXTRA:
            n = len(rx.findall(text))
            if n:
                hits.append(f"{rel}: local name or path ({n})")
                rows.append({"file": rel, "kind": "local name or path", "count": n, "action": "found"})
        if not entries and not any(rx.search(text) for rx in EXTRA):
            rows.append({"file": rel, "kind": "none found", "count": 0, "action": "none"})
    when = utc()
    out = ["# Redaction log", "",
           "Final search of every file in the hand-back, after SHA256SUMS was written. "
           "Each file was also searched when it was first saved in the working folder; that log is `raw-redaction-log.md`.",
           "", "| UTC | file | kind | count | action |", "|---|---|---|---|---|"]
    out += [f"| {when} | {r['file']} | {r['kind']} | {r['count']} | {r['action']} |" for r in rows]
    (HANDBACK / "redaction-log.md").write_text("\n".join(out) + "\n")
    if hits:
        print("STOP: found in the hand-back:\n  " + "\n  ".join(hits))
        sys.exit(1)
    print(f"{when} hand-back clean: {len(files())} files, SHA256SUMS and redaction-log.md written")


if __name__ == "__main__":
    main()
