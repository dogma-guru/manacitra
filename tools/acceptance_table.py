# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""Print the acceptance table: each reproduction case, the archived value, the reproduced value, the difference,
and the count and largest difference of every numeric value compared."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tests"))
from _reproduce import CASES, TOL  # noqa: E402


def fmt(v):
    return v if isinstance(v, str) else f"{v:.6f}"


def main():
    print("| case | statistic | archived | reproduced | difference |")
    print("|---|---|---|---|---|")
    summary = []
    for case, fn in CASES.items():
        rows, leaves = fn()
        for name, a, r in rows:
            d = ("same" if a == r else "DIFFERENT") if isinstance(a, str) else f"{abs(a - r):.1e}"
            print(f"| {case} | {name} | {fmt(a)} | {fmt(r)} | {d} |")
        worst = max(leaves)
        summary.append((case, len(leaves), worst))
    print("\n| case | numeric values compared | largest difference | within 1e-6 |")
    print("|---|---|---|---|")
    for case, n, (d, path) in summary:
        print(f"| {case} | {n} | {d:.1e} (`{path}`) | {'yes' if d <= TOL else 'NO'} |")


if __name__ == "__main__":
    main()
