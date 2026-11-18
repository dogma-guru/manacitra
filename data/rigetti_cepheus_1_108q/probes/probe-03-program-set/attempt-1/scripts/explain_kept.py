"""Final search and redaction log for probe 03's hand-back, in the form the author ruled on 21 October 2026.

Runs finalize.py's search unchanged (the same patterns, the same account figures read with one read call and never
written, the field-name pattern still not applied to .py files as dated in probe 02's go.log). The difference is the
log: a match that the author has ruled on is written one entry per match, by file and line, as "explained, kept",
with the matched text and the pattern withheld (writing either would put an account figure in the hand-back).
Only the matches listed in EXPLAINED may be kept; any other match, or any of these missing, stops the script.

Order: copy the files in (finalize.copy_in), search every file, write redaction-log.md, then write SHA256SUMS over
every file including the log, then search SHA256SUMS. The scripts are not edited and are not excluded.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import finalize as f
import hashlib

from common import redact, sha, utc

REASON = "[withheld]"
# (file, line): SHA-256 of the line's stripped text, so that a shifted line cannot be kept by number alone
# (the text itself is not written here, since it carries the figure).
EXPLAINED = {
    ("scripts/run_probe.py", "[withheld]"): "[withheld]",
    ("scripts/run_probe.py", "[withheld]"): "[withheld]",
    ("scripts/run_probe.py", "[withheld]"): "[withheld]",
    ("scripts/run_probe-probe02-start.py", "[withheld]"): "[withheld]",
    ("scripts/run_probe-probe02-start.py", "[withheld]"): "[withheld]",
    ("scripts/run_probe-probe02-start.py", "[withheld]"): "[withheld]",
}


def search(p):
    """Return (redact entries, [(line, line text)] of matches of the extra patterns) for one file."""
    rel = p.relative_to(f.HANDBACK).as_posix()
    text = p.read_text(errors="replace")
    _, entries = redact(text, rel)
    lines = text.splitlines()
    found = []
    for rx in f.EXTRA:
        if rx is f.FIELD_NAMES[0] and p.suffix == ".py":
            continue   # dated 2026-10-21 in probe 02: field names in source are not figures; figures are still searched
        for m in rx.finditer(text):
            n = text.count("\n", 0, m.start()) + 1
            found.append((n, hashlib.sha256(lines[n - 1].strip().encode()).hexdigest()))
    return rel, entries, found


def main():
    f.EXTRA.extend(f.account_figures())
    f.copy_in()
    rows, explained, stops = [], [], []
    for p in f.files():
        rel, entries, found = search(p)
        for e in entries:
            rows.append(e)
            if e["action"] == "redacted":
                stops.append(f"{rel}: {e['kind']} ({e['count']})")
        for n, line in found:
            if EXPLAINED.get((rel, n)) == line:
                explained.append((rel, n))
            else:
                stops.append(f"{rel} line {n}: a search pattern matched (text withheld)")
        if not entries and not found:
            rows.append({"file": rel, "kind": "none found", "count": 0, "action": "none"})
    missing = set(EXPLAINED) - set(explained)
    if missing:
        stops.append(f"ruled matches not found: {sorted(missing)}")
    if stops:
        print("STOP:\n  " + "\n  ".join(stops))
        sys.exit(1)

    when = utc()
    others = sorted({r["file"] for r in rows} - {k[0] for k in EXPLAINED})
    out = ["# Redaction log", "",
           "Final search of every file in the hand-back, with the patterns of probe 02's final search: account numbers, "
           "arn:aws strings carrying one, access keys, bucket names, email addresses, the working folder's name, the "
           "profile name, home paths, and the account's spending figures for this device (read with one read call and "
           "written nowhere). Each file was also searched when it was first saved in the working folder; that log is "
           "`raw-redaction-log.md`.", "",
           "The spending limit's field names are not searched in `.py` files, as probe 02 dated on 21 October 2026 "
           "(its `go.log` and the comment in `scripts/finalize.py`): a field name in source is not a figure. The "
           "figures themselves are searched in every file, scripts included.", "",
           "## Matches explained and kept", "",
           "Kept at the author's ruling of 21 October 2026. The matched text and the pattern that matched are not "
           "written here. The scripts are as run: not edited, not excluded from the search.", "",
           "| UTC | file | line | action | reason |", "|---|---|---|---|---|"]
    out += [f"| {when} | {rel} | {n} | explained, kept | {REASON} |" for rel, n in sorted(EXPLAINED)]
    out += ["", "## Every file", "",
            f"Apart from the {len(EXPLAINED)} matches above, the same search over every file in the hand-back found "
            f"nothing to redact. Rows marked \"not redacted\" are the search's own recorded exceptions (fraction digits "
            f"of a published figure; a run of twelve digits inside a SHA-256 hash).", "",
            "| UTC | file | kind | count | action |", "|---|---|---|---|---|"]
    out += [f"| {when} | {r['file']} | {r['kind']} | {r['count']} | {r['action']} |" for r in rows]
    out += ["", f"Order: this log was made final at {when}; `SHA256SUMS` was then written over every file in the "
            "hand-back, this log included, and searched in turn."]
    (f.HANDBACK / "redaction-log.md").write_text("\n".join(out) + "\n")

    names = sorted(p for p in f.HANDBACK.rglob("*") if p.is_file() and p.name != "SHA256SUMS")
    (f.HANDBACK / "SHA256SUMS").write_text(
        "".join(f"{sha(p)}  {p.relative_to(f.HANDBACK).as_posix()}\n" for p in names))
    for p in (f.HANDBACK / "SHA256SUMS", f.HANDBACK / "redaction-log.md"):
        rel, entries, found = search(p)
        bad = [e for e in entries if e["action"] == "redacted"]
        if bad or found:
            print(f"STOP: {rel} matched after writing ({len(bad)} redaction kinds, {len(found)} pattern matches)")
            sys.exit(1)
    print(f"{utc()} hand-back clean: {len(names) + 1} files; {len(EXPLAINED)} matches explained and kept; "
          f"other files: {len(others)} searched, nothing to redact; SHA256SUMS written after the log")


if __name__ == "__main__":
    main()
