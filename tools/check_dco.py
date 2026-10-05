# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""The Developer Certificate of Origin check: every commit in a range carries a Signed-off-by line.

    python tools/check_dco.py BASE HEAD      check the commits in BASE..HEAD (exit 1 if any lacks a sign-off)

The signing workflow's bot commits (the Sigstore bundles) are exempt: they are made by GitHub Actions, not by a
contributor. See CONTRIBUTING.md.
"""

import re
import subprocess
import sys

BOT_NAMES = {"github-actions[bot]"}
BOT_EMAILS = {"41898282+github-actions[bot]@users.noreply.github.com"}
SIGNED_OFF = re.compile(r"^Signed-off-by: .+ <[^<>\s]+>\s*$", re.MULTILINE)


def commits(base: str, head: str, cwd=None) -> list[dict]:
    fmt = "%H%x1f%an%x1f%ae%x1f%B%x1e"
    out = subprocess.run(
        ["git", "log", f"--format={fmt}", f"{base}..{head}"], cwd=cwd, capture_output=True, text=True, check=True
    ).stdout
    rows = []
    for rec in out.split("\x1e"):
        rec = rec.strip("\n")
        if not rec:
            continue
        sha, name, email, body = rec.split("\x1f", 3)
        rows.append({"sha": sha, "author": name, "email": email, "message": body})
    return rows


def is_bot(c: dict) -> bool:
    return c["author"] in BOT_NAMES or c["email"] in BOT_EMAILS


def missing_signoff(base: str, head: str, cwd=None) -> list[dict]:
    return [c for c in commits(base, head, cwd) if not is_bot(c) and not SIGNED_OFF.search(c["message"])]


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2:
        print(__doc__)
        return 2
    base, head = argv
    cs = commits(base, head)
    bad = missing_signoff(base, head)
    exempt = sum(1 for c in cs if is_bot(c))
    if bad:
        print(f"DCO: {len(bad)} of {len(cs)} commit(s) lack a Signed-off-by line:")
        for c in bad:
            print(f"  {c['sha'][:7]} {c['message'].splitlines()[0] if c['message'] else ''}")
        print("Add one with `git commit -s` (or `git rebase --signoff` for earlier commits). See CONTRIBUTING.md.")
        return 1
    print(f"DCO: all {len(cs) - exempt} contributor commit(s) are signed off ({exempt} bot commit(s) exempt).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
