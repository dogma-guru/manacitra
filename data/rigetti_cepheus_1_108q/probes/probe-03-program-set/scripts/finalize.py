"""Assemble the hand-back (rule section 6, runner prompt 'At the go' item 4). One read call (the spending figures, to search for).

Copied from probe 02's scripts/finalize.py; changed for probe 03: the folder names, the probe 03 files picked, and the
raw folder copied with its subfolders (the task's output files keep their relative paths under raw/output/).

Order, as the runner prompt sets it: the report is already written; copy it with the raw result files, the programs,
the scripts as run and the logs; write SHA256SUMS over the hand-back; then search every file and write the redaction log.
The search covers twelve-digit account numbers, arn:aws strings carrying one, access keys, bucket names and email
addresses (common.redact), plus the working folder's name, the profile name and home paths, and (from probe 02) the
account's spending figures for this device: the spending limit's field names and its current limit, queued, total and
remaining amounts, read with one read call and never written anywhere. Any hit stops the script before the hand-back
is called ready.
"""
import os
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import DEVICE_ARN, HERE, guard, redact, sha, utc

HANDBACK = Path.home() / "[the hand-back folder]"
EXTRA = [re.compile(re.escape(HERE.parent.name)), re.compile(re.escape(str(Path.home())))]
if os.environ.get("AWS_PROFILE"):
    EXTRA.append(re.compile(re.escape(os.environ["AWS_PROFILE"])))


FIELD_NAMES = [None]   # the spending limit's field names, set by account_figures


def account_figures():
    """The account's spending figures for this device, as strings to search for. Read call only."""
    from decimal import Decimal
    guard()
    from braket.aws import AwsSession
    resp = AwsSession().braket_client.search_spending_limits(
        filters=[{"name": "deviceArn", "operator": "EQUAL", "values": [DEVICE_ARN]}])
    FIELD_NAMES[0] = re.compile(r"\b(?:totalSpend|queuedSpend|spendingLimit)\b")
    out = [FIELD_NAMES[0]]
    for x in resp.get("spendingLimits", []):
        vals = [Decimal(x.get(k, "0")) for k in ("spendingLimit", "queuedSpend", "totalSpend")]
        vals.append(vals[0] - vals[1] - vals[2])
        for v in vals:
            if v >= 2:   # a figure this small could be a probe figure; the account's totals are not
                for txt in {str(v), str(v.normalize()), f"{v:.2f}"}:
                    out.append(re.compile(r"(?<![\d.])" + re.escape(txt) + r"(?![\d])"))
    return out


def copy_in():
    HANDBACK.mkdir(parents=True, exist_ok=True)
    # Attempt 2: attempt 1 is already in the hand-back under attempt-1/ and is left as it is; these are attempt 2's.
    picks = ["report-probe-03.md", "run-log.json", "run.log", "run-stdout.log", "go.log", "braket-probe-03-program-set-rule.md",
             "rule.sha256", "pre-go-checks.md"]
    for name in picks:
        if (HERE / name).exists():
            shutil.copy2(HERE / name, HANDBACK / name)
    if (HERE / "redaction-log.md").exists():
        shutil.copy2(HERE / "redaction-log.md", HANDBACK / "raw-redaction-log.md")
    for sub, pattern in (("raw", "*"), ("programs", "*"), ("scripts", "*.py")):
        (HANDBACK / sub).mkdir(exist_ok=True)
        for f in sorted((HERE / sub).rglob(pattern) if sub == "raw" else (HERE / sub).glob(pattern)):
            if f.is_file():
                dest = HANDBACK / sub / f.relative_to(HERE / sub)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, dest)


def files():
    # Attempt 2: only the top-level SHA256SUMS and log are left out; attempt-1/'s own are searched and summed.
    return sorted(p for p in HANDBACK.rglob("*")
                  if p.is_file() and p.relative_to(HANDBACK).as_posix() not in ("SHA256SUMS", "redaction-log.md"))


def main():
    EXTRA.extend(account_figures())
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
            if rx is FIELD_NAMES[0] and p.suffix == ".py":
                continue   # 2026-10-21: the scripts name these fields as code; their figures are still searched
            n = len(rx.findall(text))
            if n:
                hits.append(f"{rel}: local name or path ({n})")
                rows.append({"file": rel, "kind": "local name or path", "count": n, "action": "found"})
        if not entries and not any(rx.search(text) for rx in EXTRA
                                   if not (rx is FIELD_NAMES[0] and p.suffix == ".py")):
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
