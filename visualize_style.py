# -*- coding: utf-8 -*-
"""
Two visualisations matching the style of the reference images.

Fig 4 — Full bipartite spring layout
  Blue circles  = Companies (labelled, size = board size)
  Green dots    = Board members (small, no label)
  Gray edges    = Board membership

Fig 5 — Company-only projection
  Blue circles  = Companies (size = degree in network)
  Green edges   = 1 shared director
  Orange edges  = 2-3 shared directors
  Red edges     = 4+ shared directors
  Edge thickness = number of shared directors
"""

import os, math, random
from collections import defaultdict

import numpy as np
import pandas as pd
import networkx as nx
from networkx.algorithms import bipartite
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D

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
board_net  = bipartite.weighted_projected_graph(G_bip, companies)

print(f"Companies: {len(companies)}  |  Directors: {len(directors)}  |  Edges: {G_bip.number_of_edges()}")

ABBREVS = {
    "CTT Correios de Portugal": "CTT",
    "Caixa Geral de Depósitos": "CGD",
    "Corticeira Amorim": "Cort. Amorim",
    "The Navigator Company": "Navigator",
    "Jerónimo Martins": "J. Martins",
    "MEO / Altice Portugal": "MEO",
    "Grupo José de Mello": "J. de Mello",
    "Grupo Champalimaud": "Champal.",
    "Grupo Nabeiro / Delta Cafés": "Delta",
    "Grupo Alves Ribeiro": "Alves Rib.",
    "Millennium BCP": "BCP",
    "Grupo Pestana": "Pestana",
    "Grupo Vila Galé": "Vila Galé",
    "Grupo Solverde": "Solverde",
    "Super Bock Group": "Super Bock",
    "Vista Alegre Atlantis": "Vista Aleg.",
    "VdA - Vieira de Almeida": "VdA",
    "Rothschild & Co (Portugal)": "Rothschild",
    "Sagres / SCC": "Sagres",
    "Sonae SGPS": "Sonae",
    "EDP Renováveis": "EDP Renov.",
    "Galp Energia": "Galp",
    "Grupo Azevedos": "Azevedos",
    "Banco Montepio": "Montepio",
    "Banco Carregosa": "Carregosa",
    "Banco Finantia": "Finantia",
    "Banco Best": "Best",
    "Grupo Valouro": "Valouro",
    "SL Benfica": "Benfica",
    "Sporting CP": "Sporting",
    "FC Porto": "FC Porto",
    "Luz Saúde": "Luz Saúde",
    "Trofa Saúde": "Trofa Saúde",
    "Sonae MC": "Sonae MC",
    "Sonae Sierra": "S. Sierra",
    "Sumol+Compal": "Sumol",
    "OCP Portugal": "OCP",
    "Banco Big": "Banco Big",
    "Banco CTT": "B. CTT",
    "Morais Leitão": "Mor. Leitão",
    "Media Capital": "Media Cap.",
    "Media Livre": "Media Livre",
    "OK Teleseguros": "OK Teles.",
}


# ═══════════════════════════════════════════════════════════════════════════
# FIG 4 — Full bipartite spring layout
# ═══════════════════════════════════════════════════════════════════════════

def make_fig4():
    print("\nGenerating Fig 4...")

    # Tighter spring layout — small k packs everything together
    pos = nx.spring_layout(G_bip, seed=12, k=0.55, iterations=500)

    # Squash slightly vertically to match the elliptical reference shape
    for n in pos:
        pos[n] = (pos[n][0] * 1.35, pos[n][1] * 0.95)

    fig, ax = plt.subplots(figsize=(20, 15))
    ax.set_facecolor("white")
    fig.patch.set_facecolor("white")

    # — Edges: board membership —
    from matplotlib.collections import LineCollection
    segs = [[(pos[u][0], pos[u][1]), (pos[v][0], pos[v][1])] for u, v in G_bip.edges()]
    lc = LineCollection(segs, colors="#aaaaaa", linewidths=0.4, alpha=0.6, zorder=1)
    ax.add_collection(lc)

    # — Director nodes (small green dots) —
    dx = [pos[d][0] for d in directors]
    dy = [pos[d][1] for d in directors]
    ax.scatter(dx, dy, s=28, c="#2ECC71", edgecolors="#1a7a44",
               linewidths=0.3, zorder=2, alpha=0.90)

    # — Company nodes (larger blue circles) —
    c_size = {c: max(350, G_bip.degree(c) * 65) for c in companies}
    cx = [pos[c][0] for c in companies]
    cy = [pos[c][1] for c in companies]
    csz = [c_size[c] for c in companies]
    ax.scatter(cx, cy, s=csz, c="#2F57C9", edgecolors="#1a3494",
               linewidths=0.8, zorder=3)

    # — Company labels —
    def label(name):
        if name in ABBREVS:
            return ABBREVS[name]
        parts = name.split()
        if len(parts) <= 2:
            return name
        stopwords = {"de","da","do","dos","das","e","SGPS","S.A.","Grupo","Banco"}
        key = [p for p in parts if p not in stopwords]
        return key[0] if key else parts[0]

    for c in companies:
        x, y = pos[c]
        fs = max(4.8, min(7.5, c_size[c] / 110))
        ax.text(x, y, label(c), ha="center", va="center",
                fontsize=fs, fontweight="bold", color="white",
                fontfamily="DejaVu Sans", zorder=4)

    # — Legend —
    legend_elements = [
        mpatches.Patch(facecolor="#2F57C9", edgecolor="#1a3494",
                       label=f"Empresa cotada ({len(companies)})"),
        mpatches.Patch(facecolor="#2ECC71", edgecolor="#1a7a44",
                       label=f"Membro conselho ({len(directors)})"),
        Line2D([0],[0], color="#aaaaaa", lw=1.2, alpha=0.8,
               label="Membro do conselho (aresta)"),
    ]
    ax.legend(handles=legend_elements, loc="upper left", fontsize=11,
              framealpha=0.97, edgecolor="#cccccc")

    ax.set_title(
        "Rede de Governação Corporativa — Bolsa Portuguesa 2024\n"
        "Empresas e Membros do Conselho de Administração",
        fontsize=16, pad=14,
    )
    ax.axis("off")

    all_x = [p[0] for p in pos.values()]
    all_y = [p[1] for p in pos.values()]
    pad = 0.06
    ax.set_xlim(min(all_x)-pad, max(all_x)+pad)
    ax.set_ylim(min(all_y)-pad, max(all_y)+pad)

    fig.tight_layout()
    path = "results/fig4_bipartite_spring.png"
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {path}")


# ═══════════════════════════════════════════════════════════════════════════
# FIG 5 — Company-only projection, edges by shared-director count
# ═══════════════════════════════════════════════════════════════════════════

def make_fig5():
    print("\nGenerating Fig 5...")

    # Keep only companies with at least one shared-director connection
    connected = [n for n in board_net.nodes() if board_net.degree(n) > 0]
    G_vis = board_net.subgraph(connected).copy()
    print(f"  Connected companies: {G_vis.number_of_nodes()}  edges: {G_vis.number_of_edges()}")

    pos = nx.spring_layout(G_vis, seed=7, k=1.3, iterations=500, weight="weight")

    fig, ax = plt.subplots(figsize=(20, 16))
    ax.set_facecolor("white")
    fig.patch.set_facecolor("white")

    degree = dict(G_vis.degree())

    # — Edges, coloured by weight —
    # weight=1 → green, 2-3 → orange, 4+ → red
    edges_by_type = {"green": [], "orange": [], "red": []}
    for u, v, data in G_vis.edges(data=True):
        w = data["weight"]
        seg = [(pos[u][0], pos[u][1]), (pos[v][0], pos[v][1])]
        if w >= 4:
            edges_by_type["red"].append((seg, w))
        elif w >= 2:
            edges_by_type["orange"].append((seg, w))
        else:
            edges_by_type["green"].append((seg, w))

    from matplotlib.collections import LineCollection

    def draw_edges(edge_list, color, base_lw, alpha):
        if not edge_list:
            return
        segs = [s for s, w in edge_list]
        lws  = [base_lw + (w - 1) * 0.5 for _, w in edge_list]
        for seg, lw in zip(segs, lws):
            ax.plot([seg[0][0], seg[1][0]], [seg[0][1], seg[1][1]],
                    color=color, lw=lw, alpha=alpha, zorder=1)

    draw_edges(edges_by_type["green"],  "#2ECC71", 0.7, 0.55)
    draw_edges(edges_by_type["orange"], "#F39C12", 1.2, 0.70)
    draw_edges(edges_by_type["red"],    "#E74C3C", 2.0, 0.85)

    # — Company nodes (blue circles, size = board size) —
    c_size = {c: max(250, G_bip.degree(c) * 60) for c in G_vis.nodes()}
    nx_nodes = list(G_vis.nodes())
    xs  = [pos[n][0] for n in nx_nodes]
    ys  = [pos[n][1] for n in nx_nodes]
    szs = [c_size[n] for n in nx_nodes]
    ax.scatter(xs, ys, s=szs, c="#2F57C9", edgecolors="#1a3494",
               linewidths=0.8, zorder=2)

    # — Labels — (reuse same ABBREVS dict from fig4 scope via closure)
    def label(name):
        if name in ABBREVS:
            return ABBREVS[name]
        parts = name.split()
        if len(parts) <= 2:
            return name
        stopwords = {"de","da","do","dos","das","e","SGPS","S.A.","Grupo","Banco"}
        key = [p for p in parts if p not in stopwords]
        return key[0] if key else parts[0]

    for n in nx_nodes:
        x, y = pos[n]
        fs = max(5.5, min(9, c_size[n] / 90))
        ax.text(x, y, label(n), ha="center", va="center",
                fontsize=fs, fontweight="bold", color="white",
                fontfamily="DejaVu Sans", zorder=3)

    # — Legend —
    n_green  = len(edges_by_type["green"])
    n_orange = len(edges_by_type["orange"])
    n_red    = len(edges_by_type["red"])

    legend_elements = [
        mpatches.Patch(facecolor="#2F57C9", edgecolor="#1a3494",
                       label=f"Empresa ({G_vis.number_of_nodes()} empresas com ligações)"),
        Line2D([0],[0], color="#2ECC71", lw=1.5,
               label=f"1 director partilhado ({n_green} pares)"),
        Line2D([0],[0], color="#F39C12", lw=2.5,
               label=f"2-3 directores partilhados ({n_orange} pares)"),
        Line2D([0],[0], color="#E74C3C", lw=3.5,
               label=f"4+ directores partilhados ({n_red} pares)"),
    ]
    ax.legend(handles=legend_elements, loc="upper left", fontsize=10,
              framealpha=0.95, edgecolor="#cccccc")

    ax.set_title(
        "Empresas ligadas por membros do conselho comuns — Bolsa Portuguesa 2024\n"
        "(espessura = nº de directores partilhados)",
        fontsize=14, pad=12,
    )
    ax.axis("off")

    all_x = [p[0] for p in pos.values()]
    all_y = [p[1] for p in pos.values()]
    pad = 0.08
    ax.set_xlim(min(all_x)-pad, max(all_x)+pad)
    ax.set_ylim(min(all_y)-pad, max(all_y)+pad)

    fig.tight_layout()
    path = "results/fig5_company_projection.png"
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {path}")


make_fig4()
make_fig5()
print("\nDone.")
