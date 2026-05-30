# -*- coding: utf-8 -*-
"""
Two network visualisations inspired by Battiston & Catanzaro (2004).

Fig A — Board network (Fig 1 style):
  Companies as nodes; edges only where >= 2 directors are shared.
  Edge colour/thickness scales with number of shared directors.

Fig B — Full bipartite graph snapshot:
  Companies on the left, directors on the right.
  Clearly shows the two-mode structure of the data.
"""

import os
import math
from collections import defaultdict

import numpy as np
import pandas as pd
import networkx as nx
from networkx.algorithms import bipartite
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.font_manager as fm
from matplotlib.lines import Line2D

# Use DejaVu Sans which ships with matplotlib and covers Portuguese characters
plt.rcParams["font.family"] = "DejaVu Sans"

os.makedirs("results", exist_ok=True)

# ── Load data ───────────────────────────────────────────────────────────────
df = pd.read_csv("boardmembers_2024.csv")
df = df.rename(columns={"name": "director"})
df = df.dropna(subset=["director", "company"]).drop_duplicates(subset=["director", "company"])

companies_list = df["company"].unique().tolist()
directors_list = df["director"].unique().tolist()

G_bip = nx.Graph()
G_bip.add_nodes_from(companies_list, bipartite=0)
G_bip.add_nodes_from(directors_list, bipartite=1)
for _, row in df.iterrows():
    G_bip.add_edge(row["company"], row["director"])

companies = {n for n, d in G_bip.nodes(data=True) if d.get("bipartite") == 0}
directors  = {n for n, d in G_bip.nodes(data=True) if d.get("bipartite") == 1}

board_net = bipartite.weighted_projected_graph(G_bip, companies)

# ═══════════════════════════════════════════════════════════════════════════
# FIG A — Board network (Fig 1 style)
#   Only edges where weight >= 2 (shared directors >= 2)
# ═══════════════════════════════════════════════════════════════════════════

def make_board_network_fig():
    """
    Full bipartite snapshot in a spring layout.
    Companies = large dark-blue nodes (labelled always).
    Directors  = small orange nodes (labelled only if on 2+ boards).
    Edges      = thin grey lines (board memberships).
    """
    print(f"  Full graph: {G_bip.number_of_nodes()} nodes, {G_bip.number_of_edges()} edges")

    # Spring layout on the full bipartite graph
    # k controls spacing; more iterations = better separation
    pos = nx.spring_layout(G_bip, seed=7, k=1.8, iterations=300)

    c_degree = {c: G_bip.degree(c) for c in companies}
    d_degree = {d: G_bip.degree(d) for d in directors}

    # ── Node sizes ───────────────────────────────────────────────────────
    company_sizes  = {c: max(120, c_degree[c] * 55)  for c in companies}
    director_sizes = {d: max(18,  d_degree[d] * 18)  for d in directors}

    node_list_c = list(companies)
    node_list_d = list(directors)

    sizes_c = [company_sizes[n]  for n in node_list_c]
    sizes_d = [director_sizes[n] for n in node_list_d]

    fig, ax = plt.subplots(figsize=(22, 18))
    ax.set_facecolor("white")
    fig.patch.set_facecolor("white")

    # Edges
    nx.draw_networkx_edges(
        G_bip, pos, ax=ax,
        edge_color="#bbbbbb", width=0.35, alpha=0.5,
    )

    # Director nodes (draw first so companies sit on top)
    nx.draw_networkx_nodes(
        G_bip, pos, ax=ax,
        nodelist=node_list_d,
        node_size=sizes_d,
        node_color="#E8824A",   # warm orange
        edgecolors="#a85a1a",
        linewidths=0.4,
        alpha=0.85,
    )

    # Company nodes
    nx.draw_networkx_nodes(
        G_bip, pos, ax=ax,
        nodelist=node_list_c,
        node_size=sizes_c,
        node_color="#1f5fa6",   # strong blue
        edgecolors="#0d3566",
        linewidths=0.8,
    )

    # Company labels — always shown, shortened to fit
    def short(name, max_words=3):
        parts = name.split()
        return " ".join(parts[:max_words]) if len(parts) > max_words else name

    company_labels = {n: short(n) for n in node_list_c}
    nx.draw_networkx_labels(
        G_bip, pos, labels=company_labels, ax=ax,
        font_size=6, font_color="white", font_weight="bold",
        font_family="DejaVu Sans",
    )

    # Director labels — only for those on 2+ boards (interlocking directors)
    director_labels = {d: short(d, 2) for d in node_list_d if d_degree[d] >= 2}
    nx.draw_networkx_labels(
        G_bip, pos, labels=director_labels, ax=ax,
        font_size=4.5, font_color="#5c2800",
        font_family="DejaVu Sans",
    )

    # Legend
    legend_elements = [
        mpatches.Patch(facecolor="#1f5fa6", edgecolor="#0d3566",
                       label=f"Company  (n={len(companies)}, size = board size)"),
        mpatches.Patch(facecolor="#E8824A", edgecolor="#a85a1a",
                       label=f"Director  (n={len(directors)}, size = # boards)"),
        Line2D([0], [0], color="#bbbbbb", lw=1, alpha=0.7,
               label=f"Board membership  ({G_bip.number_of_edges()} edges)"),
    ]
    ax.legend(handles=legend_elements, loc="lower left", fontsize=10,
              framealpha=0.95, edgecolor="#cccccc")

    ax.set_title(
        "Portuguese Corporate Board Network 2024\n"
        "All companies and board members  —  spring layout",
        fontsize=15, pad=14,
    )
    ax.axis("off")
    fig.tight_layout()
    path = "results/figA_board_network.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {path}")


# ═══════════════════════════════════════════════════════════════════════════
# FIG B — Full bipartite graph
#   Companies on the left (large coloured nodes)
#   Directors on the right (small nodes, coloured by number of boards)
# ═══════════════════════════════════════════════════════════════════════════

def make_bipartite_fig():
    """
    Two-panel bipartite figure:
      Left panel  — full bipartite (all 86 companies + 664 directors)
      Right panel — zoomed: only the 'interlocking' sub-graph
                    (companies and directors that appear on 2+ boards)
    """
    c_degree = {c: G_bip.degree(c) for c in companies}
    d_degree = {d: G_bip.degree(d) for d in directors}
    max_cd = max(c_degree.values())
    max_dd = max(d_degree.values())

    cmap_comp = plt.cm.Blues
    cmap_dir  = plt.cm.Oranges

    # Sort for visual grouping (largest boards at top)
    company_list  = sorted(companies, key=lambda c: -c_degree[c])
    director_list = sorted(directors, key=lambda d: -d_degree[d])
    n_c = len(company_list)
    n_d = len(director_list)

    # ── PANEL 1: full bipartite ──────────────────────────────────────────
    fig, axes = plt.subplots(1, 2, figsize=(26, 40),
                             gridspec_kw={"width_ratios": [1, 1.1]})
    fig.patch.set_facecolor("white")

    for ax, show_all in [(axes[0], True), (axes[1], False)]:
        ax.set_facecolor("white")

        # Which nodes to show
        if show_all:
            c_show = company_list
            d_show = director_list
            title  = ("Full bipartite graph\n"
                      f"{n_c} companies · {n_d} directors · "
                      f"{G_bip.number_of_edges()} memberships")
        else:
            # Only directors on 2+ boards and the companies they sit on
            d_show = [d for d in director_list if d_degree[d] >= 2]
            c_show_set = set()
            for d in d_show:
                c_show_set.update(G_bip.neighbors(d))
            c_show = [c for c in company_list if c in c_show_set]
            title  = ("Interlocking-director sub-graph\n"
                      f"directors on 2+ boards  "
                      f"({len(d_show)} directors · {len(c_show)} companies)")

        n_cs = len(c_show); n_ds = len(d_show)

        pos = {}
        for i, c in enumerate(c_show):
            pos[c] = (0.0, 1.0 - i / max(n_cs - 1, 1))
        for i, d in enumerate(d_show):
            pos[d] = (1.0, 1.0 - i / max(n_ds - 1, 1))

        # Edges
        for u, v in G_bip.edges():
            if u in pos and v in pos:
                ax.plot([pos[u][0], pos[v][0]], [pos[u][1], pos[v][1]],
                        color="#aaaaaa", lw=0.2 if show_all else 0.5,
                        alpha=0.25 if show_all else 0.45, zorder=1)

        # Company nodes + labels
        xs = [pos[c][0] for c in c_show]
        ys = [pos[c][1] for c in c_show]
        sz = [max(30, c_degree[c] * (8 if show_all else 14)) for c in c_show]
        col= [cmap_comp(0.35 + 0.65 * c_degree[c] / max_cd) for c in c_show]
        ax.scatter(xs, ys, s=sz, c=col, edgecolors="#1a478a",
                   linewidths=0.5, zorder=3)
        fs_c = 4.5 if show_all else 6.5
        for c in c_show:
            ax.text(pos[c][0] - 0.025, pos[c][1], c,
                    ha="right", va="center", fontsize=fs_c, color="#1a478a")

        # Director nodes + labels
        xd = [pos[d][0] for d in d_show]
        yd = [pos[d][1] for d in d_show]
        sz2= [max(5 if show_all else 15,
                  d_degree[d] * (4 if show_all else 12)) for d in d_show]
        col2=[cmap_dir(0.3 + 0.7 * d_degree[d] / max_dd) for d in d_show]
        ax.scatter(xd, yd, s=sz2, c=col2, edgecolors="#8b4500",
                   linewidths=0.3 if show_all else 0.5, zorder=3)
        fs_d = 3.5 if show_all else 5.5
        # Label all directors in the right panel; in left only 2+ boards
        for d in d_show:
            if (not show_all) or d_degree[d] >= 2:
                ax.text(pos[d][0] + 0.025, pos[d][1], d,
                        ha="left", va="center", fontsize=fs_d, color="#8b4500")

        # Column headers
        ax.text(0.0, 1.04, "Companies", ha="center", va="bottom",
                fontsize=11, fontweight="bold", color="#1a478a")
        ax.text(1.0, 1.04, "Directors", ha="center", va="bottom",
                fontsize=11, fontweight="bold", color="#8b4500")

        ax.set_title(title, fontsize=12, pad=20)
        ax.set_xlim(-0.6, 1.6)
        ax.set_ylim(-0.02, 1.09)
        ax.axis("off")

    # Shared legend
    legend_elements = [
        mpatches.Patch(facecolor=cmap_comp(0.7), edgecolor="#1a478a",
                       label=f"Company  (node size = board size)"),
        mpatches.Patch(facecolor=cmap_dir(0.7), edgecolor="#8b4500",
                       label=f"Director  (intensity = # boards)"),
        Line2D([0], [0], color="#aaaaaa", lw=1, alpha=0.6,
               label="Board membership (edge)"),
    ]
    fig.legend(handles=legend_elements, loc="lower center",
               ncol=3, fontsize=10, framealpha=0.9,
               edgecolor="#cccccc", bbox_to_anchor=(0.5, 0.005))

    fig.suptitle(
        "Portuguese Corporate Board Network 2024 — Bipartite graph",
        fontsize=15, y=1.001,
    )
    fig.tight_layout(rect=[0, 0.03, 1, 1])
    path = "results/figB_bipartite_graph.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {path}")


def make_fig3():
    """
    Radial bipartite layout — dense sunflower style (like the paper's Fig 1).
    Companies: orange squares on an inner ring.
    Directors: cyan circles on an outer ring, placed in the arc of their company/companies.
    Gray thin edges: board memberships.
    Orange thick edges: company pairs sharing >= 2 directors (board network).
    """
    random.seed(42)

    # Sort companies so adjacent sectors are visually related (by degree, then alpha)
    company_list = sorted(companies, key=lambda c: (-G_bip.degree(c), c))
    n_c = len(company_list)

    R_INNER = 1.7
    R_OUTER = 3.6

    # ── Company positions on inner circle ───────────────────────────────
    company_angles = {}
    pos = {}
    for i, c in enumerate(company_list):
        angle = 2 * math.pi * i / n_c - math.pi / 2   # start at top
        company_angles[c] = angle
        pos[c] = (R_INNER * math.cos(angle), R_INNER * math.sin(angle))

    # ── Director positions on outer ring ────────────────────────────────
    # Group single-board directors by their company
    single_board = defaultdict(list)
    multi_board  = []
    for d in directors:
        neighs = list(G_bip.neighbors(d))
        if len(neighs) == 1:
            single_board[neighs[0]].append(d)
        else:
            multi_board.append(d)

    sector_w = (2 * math.pi / n_c) * 0.88   # 88% of each sector

    for c in company_list:
        dirs = single_board[c]
        n_d  = len(dirs)
        ca   = company_angles[c]
        for j, d in enumerate(dirs):
            frac  = (j + 0.5) / n_d if n_d > 0 else 0.5
            angle = ca - sector_w / 2 + sector_w * frac
            r     = R_OUTER + random.uniform(-0.12, 0.12)
            pos[d] = (r * math.cos(angle), r * math.sin(angle))

    # Multi-board directors: place at circular mean of their companies' angles,
    # slightly inside the outer ring so they visually bridge companies
    for d in multi_board:
        neighs = list(G_bip.neighbors(d))
        ang    = [company_angles[c] for c in neighs]
        sin_m  = sum(math.sin(a) for a in ang) / len(ang)
        cos_m  = sum(math.cos(a) for a in ang) / len(ang)
        mean_a = math.atan2(sin_m, cos_m)
        r      = R_OUTER * 0.78 + random.uniform(-0.08, 0.08)
        pos[d] = (r * math.cos(mean_a), r * math.sin(mean_a))

    # ── Figure ──────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(22, 22))
    ax.set_facecolor("white")
    fig.patch.set_facecolor("white")
    ax.set_aspect("equal")

    # Gray membership edges
    for u, v in G_bip.edges():
        x0, y0 = pos[u]; x1, y1 = pos[v]
        ax.plot([x0, x1], [y0, y1], color="#c0c0c0", lw=0.25, alpha=0.35, zorder=1)

    # Orange board-network edges (companies sharing >= 2 directors)
    for u, v, data in board_net.edges(data=True):
        if data["weight"] >= 2:
            x0, y0 = pos[u]; x1, y1 = pos[v]
            lw = 0.9 + (data["weight"] - 2) * 0.7
            ax.plot([x0, x1], [y0, y1], color="#E07010", lw=lw, alpha=0.85, zorder=2)

    # Director nodes — cyan circles
    dx = [pos[d][0] for d in directors]
    dy = [pos[d][1] for d in directors]
    d_sz = [max(14, G_bip.degree(d) * 10) for d in directors]
    ax.scatter(dx, dy, s=d_sz, c="#56CCF2", edgecolors="#1a8aaa",
               linewidths=0.3, zorder=3, alpha=0.92)

    # Company nodes — orange squares
    cx = [pos[c][0] for c in company_list]
    cy = [pos[c][1] for c in company_list]
    c_sz = [max(220, G_bip.degree(c) * 42) for c in company_list]
    ax.scatter(cx, cy, s=c_sz, c="#F2994A", edgecolors="#a85000",
               linewidths=0.8, marker="s", zorder=4)

    # Company labels (white text inside squares)
    def abbrev(name):
        # Use acronym for long names, full name for short ones
        parts = name.split()
        if len(parts) <= 2:
            return name
        if len(name) <= 12:
            return name
        # First letters of main words (skip particles)
        skip = {"de", "da", "do", "dos", "das", "e", "a", "o", "os", "as",
                 "-", "SGPS", "S.A.", "SA"}
        acr = "".join(p[0].upper() for p in parts if p not in skip and len(p) > 1)
        return acr if len(acr) >= 2 else " ".join(parts[:2])

    for c in company_list:
        x, y = pos[c]
        ax.text(x, y, abbrev(c), ha="center", va="center",
                fontsize=4.2, fontweight="bold", color="white",
                fontfamily="DejaVu Sans", zorder=5)

    # Legend
    legend_elements = [
        mpatches.Patch(facecolor="#F2994A", edgecolor="#a85000",
                       label=f"Company  (n=86, square size = board size)"),
        mpatches.Patch(facecolor="#56CCF2", edgecolor="#1a8aaa",
                       label=f"Director  (n={len(directors)}, circle size = # boards served)"),
        Line2D([0], [0], color="#c0c0c0", lw=1, alpha=0.6,
               label="Board membership"),
        Line2D([0], [0], color="#E07010", lw=2.5, alpha=0.9,
               label="Companies sharing 2+ directors"),
    ]
    ax.legend(handles=legend_elements, loc="lower center",
              bbox_to_anchor=(0.5, -0.01), fontsize=11,
              framealpha=0.95, edgecolor="#cccccc", ncol=2)

    ax.set_title(
        "Portuguese Corporate Board Network 2024\n"
        f"86 companies · {len(directors)} directors · radial bipartite layout",
        fontsize=16, pad=16,
    )
    ax.axis("off")
    pad = 0.8
    ax.set_xlim(-(R_OUTER + pad), R_OUTER + pad)
    ax.set_ylim(-(R_OUTER + pad), R_OUTER + pad)
    fig.tight_layout()
    path = "results/fig3_radial_network.png"
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {path}")


print("Generating Fig A — Board network (spring layout)...")
make_board_network_fig()

print("Generating Fig B — Full bipartite graph...")
make_bipartite_fig()

print("Generating Fig 3 — Dense radial bipartite...")
make_fig3()

print("\nDone.")
