# Copyright 2026 Anish Patel
# SPDX-License-Identifier: Apache-2.0
"""Reproduce the ibm_fez numbers of 5 October 2026 from the archived counts in data/.

Kickoff 31 ran circuits A and B on 27 pairs of ibm_fez at once, 8000 shots per circuit. This recomputes each pair's
kept share from the raw counts and applies the map rule, then compares with the published values.
"""

from manacitra import archive
from manacitra.report import map_table, verdict_lines

fez = archive.fez_or_kingston("ibm_fez")
run, settle = fez["k31-map"], fez["k29-settle"]
print(f"{run['meta']['processor']}, {run['meta']['utc'][:16]} UTC, job {run['meta']['job_id']}")

analysis = archive.map_from_record(run, prev_k=archive.previous_k_for(run, settle))
x = [r["x"] for r in run["published_at_submission"]]
print(map_table(run["pairs"], analysis["kA"], analysis["kB"], x))
print()
print(verdict_lines(analysis))

published = run["archived"]["analysis"]
print("\nreproduced against published:")
for name, mine, theirs in [
    ("r_split(k_A)", analysis["S1"]["r_split_A"]["pearson"], published["S1"]["r_split_A"]["pearson"]),
    ("r_AB", analysis["S2"]["r_AB"]["pearson"], published["S2"]["r_AB"]["pearson"]),
    ("r_Ax", analysis["S3"]["r_Ax"]["pearson"], published["S3"]["r_Ax"]["pearson"]),
    ("r_AB.x", analysis["S3"]["r_AB_given_x"], published["S3"]["r_AB_given_x"]),
]:
    print(f"  {name:13s} {mine:+.6f}  published {theirs:+.6f}  difference {abs(mine - theirs):.1e}")
