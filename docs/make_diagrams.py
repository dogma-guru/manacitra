# Copyright 2026 Anish Patel
# SPDX-License-Identifier: Apache-2.0
"""Make the four README diagrams from the data in data/, as SVG with a PNG fallback.

    python docs/make_diagrams.py [--out docs/diagrams]

1. kept-share.svg   the kept share in one picture: two circuits, their ideal outcomes, one good and one poor pair
2. chip-map.svg     ibm_fez's coupling map, the 27 pairs coloured by kept share, beside the published error rates
3. pipeline.svg     map, verdict, pick, run
4. payoff.svg       workload fidelity against the prior kept share, with the two picks of 8 marked

Colours: one sequential blue ramp for magnitude; two categorical slots for the two picks; text in ink, never in a
series colour. The figures carry their own light surface so they read on light and dark pages alike.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle  # noqa: E402

from manacitra import archive  # noqa: E402
from manacitra.circuits import CIRCUITS, GAP  # noqa: E402
from manacitra.layout import pick_pairs  # noqa: E402
from manacitra.report import heavy_hex_coordinates  # noqa: E402

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#8a8985"
GRID = "#e4e3df"
SERIES_1 = "#2a78d6"  # categorical slot 1: blue
SERIES_2 = "#eb6834"  # categorical slot 2: orange
RAMP = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
SEQ = LinearSegmentedColormap.from_list("manacitra_blue", RAMP)

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "text.color": INK,
        "axes.labelcolor": INK_2,
        "axes.edgecolor": MUTED,
        "xtick.color": INK_2,
        "ytick.color": INK_2,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "svg.hashsalt": "manacitra",
        "svg.fonttype": "none",
    }
)


def save(fig, out: Path, name: str):
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / f"{name}.svg", bbox_inches="tight", metadata={"Date": None})
    fig.savefig(out / f"{name}.png", bbox_inches="tight", dpi=160, metadata={"Software": None})
    plt.close(fig)


# --------------------------------------------------------------------------- 1. the kept share
def circuit_sketch(ax, x0, y0, title, angle_colour):
    """Two qubit lines, three CZ, single-qubit boxes between them; the boxes are where the two variants differ."""
    w = 4.6
    for dy in (0.0, -0.7):
        ax.plot([x0, x0 + w], [y0 + dy, y0 + dy], color=MUTED, lw=1.2)
    ax.text(x0 - 0.15, y0, "q₀", ha="right", va="center", color=INK_2, fontsize=9)
    ax.text(x0 - 0.15, y0 - 0.7, "q₁", ha="right", va="center", color=INK_2, fontsize=9)
    xs_box = [x0 + 0.35, x0 + 1.55, x0 + 2.75, x0 + 3.95]
    xs_cz = [x0 + 1.05, x0 + 2.25, x0 + 3.45]
    for xb in xs_box:
        for dy in (0.0, -0.7):
            ax.add_patch(
                FancyBboxPatch(
                    (xb - 0.22, y0 + dy - 0.17),
                    0.44,
                    0.34,
                    boxstyle="round,pad=0.01,rounding_size=0.06",
                    fc=angle_colour,
                    ec="none",
                    zorder=3,
                )
            )
    for xc in xs_cz:
        ax.plot([xc, xc], [y0, y0 - 0.7], color=INK, lw=1.4, zorder=3)
        for dy in (0.0, -0.7):
            ax.plot(xc, y0 + dy, "o", color=INK, ms=5, zorder=4)
    ax.text(x0, y0 + 0.45, title, ha="left", va="bottom", fontsize=10, color=INK)


def diagram_kept_share(out: Path):
    run = archive.load("ibm_fez/k31-map.json")
    an = archive.map_from_record(run)
    P = archive.p11_table(run)
    order = run["order"]
    no = np.mean([P[i] for i, lbl in enumerate(order) if lbl == "A no"], axis=0)
    off = np.mean([P[i] for i, lbl in enumerate(order) if lbl == "A off"], axis=0)
    kA = np.array(an["kA"])
    good, poor = int(np.argmax(kA)), int(np.argmin(kA))
    pairs = run["pairs"]

    fig = plt.figure(figsize=(10.5, 4.4))
    ax0 = fig.add_axes([0.0, 0.0, 0.42, 1.0])
    ax0.set_xlim(-0.6, 5.2)
    ax0.set_ylim(-3.2, 1.6)
    ax0.axis("off")
    circuit_sketch(ax0, 0.2, 0.7, "circuit A, no offset", RAMP[1])
    circuit_sketch(ax0, 0.2, -1.6, "circuit A, offset", RAMP[3])
    ax0.text(
        0.2,
        -2.85,
        "The same three CZ gates (black). Only the single-qubit\nangles (boxes) differ between the two.",
        fontsize=9,
        color=INK_2,
        va="top",
    )

    ax = fig.add_axes([0.50, 0.17, 0.48, 0.70])
    cols = [
        ("ideal\n(exact model)", CIRCUITS["A"].ideal_no, CIRCUITS["A"].ideal_off, None),
        (f"pair {pairs[good]}\nkept most", no[good], off[good], kA[good]),
        (f"pair {pairs[poor]}\nkept least", no[poor], off[poor], kA[poor]),
    ]
    for i, (_name, pn, po, k) in enumerate(cols):
        ax.plot([i, i], [pn, po], color=MUTED, lw=2, zorder=1)
        ax.plot(i, pn, "o", ms=9, color=RAMP[1], mec=SURFACE, mew=2, zorder=3)
        ax.plot(i, po, "o", ms=9, color=RAMP[3], mec=SURFACE, mew=2, zorder=3)
        ax.text(i + 0.1, po + 0.002, f"offset {po:.3f}", va="bottom", fontsize=8.5, color=INK_2)
        ax.text(i + 0.1, pn - 0.002, f"no offset {pn:.3f}", va="top", fontsize=8.5, color=INK_2)
        label = f"gap {po - pn:+.3f}" if k is None else f"gap {po - pn:+.3f},  k = {k:.2f}"
        ax.text(i, max(po, pn) + 0.012, label, ha="center", va="bottom", fontsize=9.5, color=INK)
    ax.set_xticks(range(3), [c[0] for c in cols])
    ax.tick_params(axis="x", length=0)
    ax.set_xlim(-0.5, 2.8)
    ax.set_ylim(0.80, 1.035)
    ax.set_ylabel("P(11), the share of shots reading 11")
    ax.yaxis.grid(True, color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    fig.text(
        0.50,
        0.94,
        f"k = measured gap ÷ ideal gap ({GAP['A']}). ibm_fez, 5 October 2026, 32,000 shots per variant per pair.",
        fontsize=9,
        color=INK_2,
    )
    save(fig, out, "kept-share")


# --------------------------------------------------------------------------- 2. the chip map
def diagram_chip_map(out: Path):
    run = archive.load("ibm_fez/k31-map.json")
    edges = [tuple(e) for e in archive.load("ibm_fez/coupling-map.json")["edges"]]
    an = archive.map_from_record(run)
    pairs = [tuple(p) for p in run["pairs"]]
    k = dict(zip(pairs, an["kA"]))
    x = {tuple(r["pair"]): r["x"] for r in run["published_at_submission"]}
    coords = heavy_hex_coordinates(edges)

    fig = plt.figure(figsize=(11, 5.6))
    ax1 = fig.add_axes([0.0, 0.08, 0.62, 0.82])
    ax2 = fig.add_axes([0.66, 0.30, 0.33, 0.45])

    def draw(ax, values, invert, lw):
        lo, hi = min(values.values()), max(values.values())
        for a, b in edges:
            (x0, y0), (x1, y1) = coords[a], coords[b]
            ax.plot([x0, x1], [y0, y1], color=GRID, lw=1.0, zorder=1)
        for (a, b), v in values.items():
            t = (v - lo) / (hi - lo)
            t = 1 - t if invert else t
            (x0, y0), (x1, y1) = coords[a], coords[b]
            ax.plot([x0, x1], [y0, y1], color=SEQ(0.12 + 0.88 * t), lw=lw, solid_capstyle="round", zorder=2)
        ax.scatter([c[0] for c in coords.values()], [c[1] for c in coords.values()], s=4, color=MUTED, zorder=3, lw=0)
        ax.set_aspect("equal")
        ax.axis("off")
        return lo, hi

    lo, hi = draw(ax1, k, False, 5.5)
    ax1.set_title("The map: each measured pair's kept share k", loc="left", fontsize=11, color=INK)
    xlo, xhi = draw(ax2, x, True, 3.5)
    ax2.set_title("The published error rates for the same pairs", loc="left", fontsize=9.5, color=INK)

    cax = fig.add_axes([0.08, 0.06, 0.40, 0.025])
    cb = fig.colorbar(
        plt.cm.ScalarMappable(norm=matplotlib.colors.Normalize(0.12, 1.0), cmap=SEQ), cax=cax, orientation="horizontal"
    )
    cb.set_ticks([0.12, 1.0], labels=[f"kept least\n(k = {lo:.2f})", f"kept most\n(k = {hi:.2f})"])
    cb.outline.set_visible(False)
    cax2 = fig.add_axes([0.69, 0.22, 0.27, 0.02])
    cb2 = fig.colorbar(
        plt.cm.ScalarMappable(norm=matplotlib.colors.Normalize(0.12, 1.0), cmap=SEQ), cax=cax2, orientation="horizontal"
    )
    cb2.set_ticks([0.12, 1.0], labels=[f"highest error\n(x = {xhi:.3f})", f"lowest error\n(x = {xlo:.3f})"])
    cb2.outline.set_visible(False)
    cb2.ax.tick_params(labelsize=8.5)
    fig.text(
        0.0,
        0.97,
        "ibm_fez, 27 pairs, 5 October 2026 (12:37 UTC). Grey: couplers not measured in this run.",
        fontsize=9,
        color=INK_2,
    )
    fig.text(
        0.66,
        0.12,
        "Dark means better on both maps. Read side by side,\n"
        "the two maps order the pairs differently\n(r = −0.18 between k and x on this run).",
        fontsize=8.5,
        color=INK_2,
        va="top",
    )
    save(fig, out, "chip-map")


# --------------------------------------------------------------------------- 3. the pipeline
def diagram_pipeline(out: Path):
    fig, ax = plt.subplots(figsize=(11, 3.9))
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 3.9)
    ax.axis("off")
    boxes = [
        ("Map", "16 short circuits on\nevery pair at once", "k per pair: how much of\na known gap it kept"),
        ("Verdict", "k from two circuits,\nsplit halves, published x", "NOISE / REDUNDANT /\nDIAGNOSTIC / NOT SETTLED"),
        ("Pick", "the map (and, for\ncomparison, x)", "the n pairs that\nkept the most"),
        ("Run", "your job, placed\non the picked pairs", "results on pairs chosen\nby what they keep"),
    ]
    w, h, gap, y = 2.2, 1.25, 0.55, 1.15
    for i, (name, inp, outp) in enumerate(boxes):
        x0 = 0.25 + i * (w + gap)
        ax.add_patch(
            FancyBboxPatch(
                (x0, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.12", fc="#eef4fc", ec=RAMP[3], lw=1.2
            )
        )
        ax.text(x0 + w / 2, y + h - 0.22, name, ha="center", va="top", fontsize=12, color=INK, weight="bold")
        ax.text(x0 + w / 2, y + 0.18, f"out: {outp}", ha="center", va="bottom", fontsize=8.3, color=INK_2)
        ax.text(x0 + w / 2, y - 0.12, f"in: {inp}", ha="center", va="top", fontsize=8.3, color=INK_2)
        if i < 3:
            ax.add_patch(
                FancyArrowPatch(
                    (x0 + w + 0.04, y + h / 2),
                    (x0 + w + gap - 0.04, y + h / 2),
                    arrowstyle="-|>",
                    mutation_scale=14,
                    color=INK_2,
                    lw=1.2,
                )
            )
    ax.add_patch(Rectangle((0.25, 3.05), 4 * w + 3 * gap, 0.62, fc="none", ec=MUTED, lw=1, ls=(0, (4, 3))))
    ax.text(
        0.37,
        3.36,
        "In the author's use: the rules and a set of predictions are written down, hashed and sealed\n"
        "before the map job is sent; the verdict is read off rules fixed in advance.",
        fontsize=8.6,
        color=INK_2,
        va="center",
    )
    ax.add_patch(
        FancyArrowPatch(
            (0.25 + w / 2, 3.05),
            (0.25 + w / 2, y + h + 0.03),
            arrowstyle="-|>",
            mutation_scale=12,
            color=MUTED,
            lw=1,
            ls=(0, (4, 3)),
        )
    )
    ax.text(
        0.25,
        0.1,
        "Persistence (how long a map lasts) is a fifth step, open until Kickoff 35's verdict is in.",
        fontsize=8.6,
        color=MUTED,
    )
    save(fig, out, "pipeline")


# --------------------------------------------------------------------------- 4. the payoff
def diagram_payoff(out: Path):
    fez = archive.fez_or_kingston("ibm_fez")
    k31, k32, k33 = fez["k31-map"], fez["k32-isolation"], fez["k33-payoff"]
    prior = archive.isolation_analysis(k32, k31["pairs"], k31["archived"]["analysis"]["kA"])
    k_prior = np.array(prior["kD_all27"])
    pay = archive.payoff_from_record(k33, k_prior, prior["L_D_all27"], archive.workload_ideal())
    W = np.array(pay["W"])
    x = [r["x"] for r in k33["published_at_submission"]]
    by_k, by_x = set(pick_pairs(k_prior, 8)), set(pick_pairs(x, 8, highest=False))
    err_k = 1 - W[list(by_k)].mean()
    err_x = 1 - W[list(by_x)].mean()
    less = 100 * (1 - err_k / err_x)

    fig, ax = plt.subplots(figsize=(8.4, 5.2))
    others = [i for i in range(len(W)) if i not in by_k | by_x]
    ax.scatter(k_prior[others], W[others], s=46, color="#c3c2b7", ec=SURFACE, lw=1.5, zorder=2, label="other pairs")
    ks = sorted(by_k)
    ax.scatter(k_prior[ks], W[ks], s=70, color=SERIES_1, ec=SURFACE, lw=1.5, zorder=3, label="top 8 by the map")
    xs = sorted(by_x)
    ax.scatter(
        k_prior[xs], W[xs], s=150, facecolor="none", ec=SERIES_2, lw=2, zorder=4, label="top 8 by published error rates"
    )
    ax.axhline(1 - err_k, color=SERIES_1, lw=1, ls=(0, (4, 3)), zorder=1)
    ax.axhline(1 - err_x, color=SERIES_2, lw=1, ls=(0, (4, 3)), zorder=1)
    ax.text(0.47, 1 - err_k + 0.00015, f"map's pick: mean error {err_k:.4f}", fontsize=8.5, color=INK_2, va="bottom")
    ax.text(
        0.47, 1 - err_x + 0.00015, f"published pick: mean error {err_x:.4f}", fontsize=8.5, color=INK_2, va="bottom"
    )
    ax.set_xlabel("kept share k, measured two hours before (Kickoff 32's run)")
    ax.set_ylabel("workload fidelity W (8 random 9-CZ circuits)")
    ax.yaxis.grid(True, color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    ax.legend(loc="lower right", frameon=False, fontsize=9)
    ax.set_title(
        f"Choosing by the map: {less:.1f}% less error than choosing by the published rates",
        loc="left",
        fontsize=11,
        color=INK,
        pad=22,
    )
    ax.text(
        0,
        1.02,
        "ibm_fez, 5 October 2026, 15:20 UTC. Pairs in both picks carry both marks. "
        f"G = {pay['gains']['k_prior']['G']:+.4f}, 90% interval [{pay['gains']['k_prior']['ci90'][0]:+.4f}, "
        f"{pay['gains']['k_prior']['ci90'][1]:+.4f}].",
        transform=ax.transAxes,
        fontsize=8.5,
        color=INK_2,
    )
    save(fig, out, "payoff")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parent / "diagrams")
    a = ap.parse_args(argv)
    diagram_kept_share(a.out)
    diagram_chip_map(a.out)
    diagram_pipeline(a.out)
    diagram_payoff(a.out)
    print(f"wrote 4 diagrams (SVG and PNG) to {a.out}")


if __name__ == "__main__":
    main()
