# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""Tables and the chip map figure.

Tables are plain Markdown. The figure needs matplotlib (the [docs] extra): a processor's coupling map with every
measured pair coloured by its kept share, on a colour-blind-safe sequential scale (viridis), the legend in words.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np


# --------------------------------------------------------------------------- tables
def markdown_table(headers: Sequence[str], rows: Sequence[Sequence]) -> str:
    def fmt(v):
        if isinstance(v, float):
            return f"{v:.3f}"
        if isinstance(v, (list, tuple)):
            return "[" + ", ".join(str(q) for q in v) + "]"
        return str(v)

    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    out += ["| " + " | ".join(fmt(v) for v in r) + " |" for r in rows]
    return "\n".join(out)


def map_table(pairs, kA, kB=None, x=None) -> str:
    """One row per pair, sorted from the pair that kept most of circuit A's gap to the one that kept least."""
    order = np.argsort(-np.asarray(kA, float))
    headers = ["pair", "k_A"] + (["k_B"] if kB is not None else []) + (["published x"] if x is not None else [])
    rows = []
    for i in order:
        r = [list(pairs[i]), float(kA[i])]
        if kB is not None:
            r.append(float(kB[i]))
        if x is not None:
            r.append(f"{x[i]:.4f}")
        rows.append(r)
    return markdown_table(headers, rows)


def verdict_lines(analysis: dict) -> str:
    """A short plain-text account of a map analysis: the verdict and every number the rule used."""
    from .stats import N_PERMUTATIONS, format_p

    v = analysis["verdict"]
    lines = [f"verdict: {v['verdict']}  ({v['rule']})"]
    for k, val in v["inputs"].items():
        if val is None:
            continue
        if k.startswith("p_"):
            lines.append(f"  {k}: {format_p(val, analysis.get('n_permutations', N_PERMUTATIONS))}")
        else:
            lines.append(f"  {k} = {val:.4f}" if isinstance(val, float) else f"  {k} = {val}")
    for k, ok in v.get("conditions", {}).items():
        lines.append(f"  [{'x' if ok else ' '}] {k}")
    if v.get("note"):
        lines.append(f"  note: {v['note']}")
    return "\n".join(lines)


# --------------------------------------------------------------------------- the chip map
def heavy_hex_coordinates(edges) -> dict[int, tuple[float, float]]:
    """Drawing coordinates for an IBM heavy-hex coupling map.

    Rows are the chains of consecutively numbered qubits; a qubit outside every chain is a bridge, drawn between the
    two rows it joins. Falls back to a spring layout for a map that does not fit this pattern.
    """
    es = {(min(a, b), max(a, b)) for a, b in edges}
    nodes = sorted({q for e in es for q in e})
    nb: dict[int, set[int]] = {q: set() for q in nodes}
    for a, b in es:
        nb[a].add(b)
        nb[b].add(a)
    rows, row_of = [], {}
    for q in nodes:
        if q in row_of:
            continue
        chain = [q]
        while chain[-1] + 1 in nb[chain[-1]]:
            chain.append(chain[-1] + 1)
        if len(chain) >= 3:
            for x, c in enumerate(chain):
                row_of[c] = (len(rows), x)
            rows.append(chain)
    coords: dict[int, tuple[float, float]] = {}
    for q, (r, x) in row_of.items():
        coords[q] = (float(x), -2.0 * r)
    ok = True
    for q in nodes:
        if q in coords:
            continue
        ns = [n for n in nb[q] if n in coords]
        if not ns:
            ok = False
            break
        coords[q] = (float(np.mean([coords[n][0] for n in ns])), float(np.mean([coords[n][1] for n in ns])))
    if ok and len(rows) >= 2:
        return coords
    import rustworkx as rx

    g = rx.PyGraph()
    idx = {q: g.add_node(q) for q in nodes}
    for a, b in es:
        g.add_edge(idx[a], idx[b], None)
    pos = rx.spring_layout(g, seed=1)
    return {q: tuple(pos[idx[q]]) for q in nodes}


def chip_map(
    ax,
    edges,
    values: dict,
    coords=None,
    cmap: str = "viridis",
    vmin=None,
    vmax=None,
    reverse: bool = False,
    qubit_size: float = 6,
    unmeasured_colour: str = "#c8c8c8",
    line_width: float = 4.0,
):
    """Draw the coupling map on `ax`, each measured pair coloured by its value; returns the ScalarMappable.

    reverse: colour low values as high (for a published error, where low is good), so that on both maps the same
    colour means "better" by that measure.
    """
    import matplotlib as mpl

    coords = coords or heavy_hex_coordinates(edges)
    es = {(min(a, b), max(a, b)) for a, b in edges}
    vals = {(min(a, b), max(a, b)): v for (a, b), v in values.items()}
    lo = min(vals.values()) if vmin is None else vmin
    hi = max(vals.values()) if vmax is None else vmax
    norm = mpl.colors.Normalize(lo, hi)
    cm = mpl.colormaps[cmap + ("_r" if reverse else "")]
    for a, b in sorted(es):
        (x0, y0), (x1, y1) = coords[a], coords[b]
        if (a, b) in vals:
            ax.plot([x0, x1], [y0, y1], color=cm(norm(vals[(a, b)])), lw=line_width, solid_capstyle="round", zorder=2)
        else:
            ax.plot([x0, x1], [y0, y1], color=unmeasured_colour, lw=1.0, zorder=1)
    xs = [coords[q][0] for q in coords]
    ys = [coords[q][1] for q in coords]
    ax.scatter(xs, ys, s=qubit_size, color="#8a8a8a", zorder=3, linewidths=0)
    ax.set_aspect("equal")
    ax.axis("off")
    return mpl.cm.ScalarMappable(norm=norm, cmap=cm)
