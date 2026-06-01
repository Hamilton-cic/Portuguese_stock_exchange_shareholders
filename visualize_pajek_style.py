# -*- coding: utf-8 -*-
"""
Fig P — Pajek-style company projection network.
  - Only connected companies (degree > 0)
  - Small circles coloured by Louvain community
  - Labels OUTSIDE nodes, pushed away from centre
  - Edge thickness = number of shared directors (weight)
"""

import os
import numpy as np
import pandas as pd
import networkx as nx
from networkx.algorithms import bipartite
import community as community_louvain
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

plt.rcParams["font.family"] = "DejaVu Sans"
os.makedirs("results", exist_ok=True)

# ── Data ────────────────────────────────────────────────────────────────────
df = pd.read_csv("boardmembers_2024.csv")
df = df.rename(columns={"name": "director"})
df = df.dropna(subset=["director", "company"]).drop_duplicates(subset=["director", "company"])

G_bip = nx.Graph()
G_bip.add_nodes_from(df["company"].unique(), bipartite=0)
G_bip.add_nodes_from(df["director"].unique(), bipartite=1)
for _, row in df.iterrows():
    G_bip.add_edge(row["company"], row["director"])

companies = {n for n, d in G_bip.nodes(data=True) if d.get("bipartite") == 0}
board_net  = bipartite.weighted_projected_graph(G_bip, companies)

# Keep only connected companies
connected = [n for n in board_net.nodes() if board_net.degree(n) > 0]
G = board_net.subgraph(connected).copy()
print(f"Connected companies: {G.number_of_nodes()}  edges: {G.number_of_edges()}")

# ── Community detection ──────────────────────────────────────────────────────
partition  = community_louvain.best_partition(G, weight="weight", random_state=42)
modularity = community_louvain.modularity(partition, G, weight="weight")

from collections import Counter
comm_sizes = Counter(partition.values())
top5_ids   = {cid for cid, _ in comm_sizes.most_common(5)}
top5_sorted = [cid for cid, _ in comm_sizes.most_common(5)]

# Palette matching the Italian paper style (red, blue, orange, green, purple, grey)
PALETTE = {
    top5_sorted[0]: "#E74C3C",   # red   — Industriais
    top5_sorted[1]: "#2F57C9",   # blue  — Financeiro
    top5_sorted[2]: "#F39C12",   # orange — Utilities
    top5_sorted[3]: "#27AE60",   # green — Sonae
    top5_sorted[4]: "#8E44AD",   # purple — ALTRI
}
DEFAULT_COLOR = "#aaaaaa"

COMM_NAMES = [
    "Industriais / Família",
    "Financeiro / Seguros",
    "Utilities / Distribuição",
    "Universo Sonae",
    "ALTRI / Media",
]

def node_color(node):
    cid = partition[node]
    return PALETTE.get(cid, DEFAULT_COLOR)

# ── Abbreviations ────────────────────────────────────────────────────────────
ABBREVS = {
    "CTT Correios de Portugal": "CTT", "Caixa Geral de Depósitos": "CGD",
    "Corticeira Amorim": "Amorim", "The Navigator Company": "Navigator",
    "Jerónimo Martins": "J.Martins", "MEO / Altice Portugal": "MEO",
    "Grupo José de Mello": "J.de Mello", "Grupo Champalimaud": "Champalimaud",
    "Grupo Nabeiro / Delta Cafés": "Delta", "Grupo Alves Ribeiro": "Alves Rib.",
    "Millennium BCP": "BCP", "Grupo Pestana": "Pestana",
    "Grupo Vila Galé": "Vila Galé", "Grupo Solverde": "Solverde",
    "Super Bock Group": "Super Bock", "Vista Alegre Atlantis": "Vista Alegre",
    "VdA - Vieira de Almeida": "VdA", "Rothschild & Co (Portugal)": "Rothschild",
    "Sagres / SCC": "Sagres", "Sonae SGPS": "Sonae SGPS",
    "EDP Renováveis": "EDP Renov.", "Galp Energia": "Galp",
    "Grupo Azevedos": "Azevedos", "Banco Montepio": "Montepio",
    "Banco Carregosa": "Carregosa", "Banco Finantia": "Finantia",
    "Banco Best": "Best", "Grupo Valouro": "Valouro",
    "SL Benfica": "S.L.Benfica", "Sporting CP": "Sporting CP",
    "Luz Saúde": "Luz Saúde", "Trofa Saúde": "Trofa Saúde",
    "Sonae MC": "Sonae MC", "Sonae Sierra": "Sonae Sierra",
    "Sumol+Compal": "Sumol+Compal", "OCP Portugal": "OCP",
    "Banco Big": "Banco Big", "Banco CTT": "Banco CTT",
    "Morais Leitão": "Morais Leitão", "Media Capital": "Media Capital",
    "Media Livre": "Media Livre", "OK Teleseguros": "OK Teles.",
    "ATRIUM BIRE SIGI": "Atrium", "CIAGEST - SIGI S.A": "Ciagest",
    "TEIXEIRA DUARTE": "Teixeira D.", "ALTRI SGPS": "ALTRI",
    "Cofina SGPS": "Cofina", "Novabase": "Novabase",
    "Mota-Engil": "Mota-Engil", "Ibersol": "Ibersol",
}

def abbrev(name):
    if name in ABBREVS:
        return ABBREVS[name]
    parts = name.split()
    if len(parts) <= 2:
        return name
    stop = {"de","da","do","dos","das","e","SGPS","S.A.","Grupo","Banco"}
    key = [p for p in parts if p not in stop]
    return (key[0] if key else parts[0])

# ── Layout ───────────────────────────────────────────────────────────────────
# Separate connected components: giant + small satellites
components = sorted(nx.connected_components(G), key=len, reverse=True)
giant      = G.subgraph(components[0]).copy()
satellites = components[1:]   # small isolated pairs/triads

# Kamada-Kawai on giant component — cleaner than spring for dense cliques
pos_giant = nx.kamada_kawai_layout(giant, weight=None)

# Scale giant to fill (-0.8, 0.8) range
gx = np.array([v[0] for v in pos_giant.values()])
gy = np.array([v[1] for v in pos_giant.values()])
gx = (gx - gx.mean()) / (gx.max() - gx.min() + 1e-9) * 1.6
gy = (gy - gy.mean()) / (gy.max() - gy.min() + 1e-9) * 1.4
for i, n in enumerate(pos_giant):
    pos_giant[n] = (gx[i], gy[i])

# Place satellites evenly around a circle outside the giant
pos = dict(pos_giant)
sat_nodes_flat = [n for comp in satellites for n in comp]
n_sat = len(sat_nodes_flat)
R = 1.20   # radius outside the main layout
i = 0
for comp in satellites:
    comp = list(comp)
    # centre angle for this satellite group
    angle = 2 * np.pi * i / max(n_sat, 1)
    cx_s  = R * np.cos(angle)
    cy_s  = R * np.sin(angle)
    if len(comp) == 1:
        pos[comp[0]] = (cx_s, cy_s)
        i += 1
    else:
        sub_pos = nx.spring_layout(G.subgraph(comp), seed=0, k=0.3)
        for j, n in enumerate(sub_pos):
            ang2 = 2 * np.pi * i / max(n_sat, 1)
            pos[n] = (R * np.cos(ang2), R * np.sin(ang2))
            i += 1

# ── Draw ─────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(22, 17))
ax.set_facecolor("white")
fig.patch.set_facecolor("white")

# — Edges (thickness and darkness by weight) —
for u, v, data in G.edges(data=True):
    w = data.get("weight", 1)
    lw    = 0.6 + (w - 1) * 0.9          # 0.6 for w=1, up to ~5 for w=6
    alpha = 0.35 + min((w - 1) * 0.12, 0.5)
    ax.plot(
        [pos[u][0], pos[v][0]],
        [pos[u][1], pos[v][1]],
        color="#444444", linewidth=lw, alpha=alpha, zorder=1, solid_capstyle="round"
    )

# — Nodes (small circles) —
NODE_SIZE = 120
for node in G.nodes():
    x, y  = pos[node]
    color = node_color(node)
    ax.scatter(x, y, s=NODE_SIZE, c=color, edgecolors="white",
               linewidths=1.0, zorder=3, alpha=0.95)

# — Labels outside nodes —
# Push label away from the graph centroid
all_x = np.array([pos[n][0] for n in G.nodes()])
all_y = np.array([pos[n][1] for n in G.nodes()])
cx, cy = all_x.mean(), all_y.mean()

LABEL_OFFSET = 0.07   # distance to push label from node centre

for node in G.nodes():
    x, y  = pos[node]
    lbl   = abbrev(node)
    color = node_color(node)

    # Direction away from centroid
    dx, dy = x - cx, y - cy
    norm = max(np.sqrt(dx**2 + dy**2), 1e-6)
    ox = LABEL_OFFSET * dx / norm
    oy = LABEL_OFFSET * dy / norm

    # Horizontal alignment: left if label is to the left of centre
    ha = "left" if ox >= 0 else "right"

    ax.text(
        x + ox, y + oy, lbl,
        ha=ha, va="center",
        fontsize=7.2, fontweight="bold",
        color=color,
        fontfamily="DejaVu Sans",
        zorder=4,
        bbox=dict(boxstyle="round,pad=0.05", fc="white", ec="none", alpha=0.6),
    )

# — Legend —
legend_handles = []
for i, cid in enumerate(top5_sorted):
    members = [n for n, c in partition.items() if c == cid]
    lbl = f"{COMM_NAMES[i]}  ({len(members)} empresas)"
    legend_handles.append(mpatches.Patch(facecolor=PALETTE[cid], edgecolor="white",
                                         linewidth=0.5, label=lbl))
# edge weight legend
from matplotlib.lines import Line2D
legend_handles += [
    Line2D([0],[0], color="#444444", lw=0.7, alpha=0.5, label="1 director partilhado"),
    Line2D([0],[0], color="#444444", lw=2.5, alpha=0.7, label="3 directores partilhados"),
    Line2D([0],[0], color="#444444", lw=5.0, alpha=0.9, label="5+ directores partilhados"),
]

ax.legend(handles=legend_handles, loc="upper left", fontsize=10,
          framealpha=0.96, edgecolor="#cccccc",
          title=f"Comunidade Louvain  (Q = {modularity:.3f})",
          title_fontsize=10)

# — Title —
ax.set_title(
    f"Rede de Interlocking Directorates — Bolsa Portuguesa 2024\n"
    f"{G.number_of_nodes()} empresas conectadas  ·  {G.number_of_edges()} ligações  "
    f"·  espessura = nº de directores partilhados",
    fontsize=14, pad=12,
)
ax.axis("off")

pad = 0.14
ax.set_xlim(all_x.min() - pad, all_x.max() + pad)
ax.set_ylim(all_y.min() - pad, all_y.max() + pad)

fig.tight_layout()
path = "results/figP_pajek_style.png"
fig.savefig(path, dpi=240, bbox_inches="tight")
plt.close(fig)
print(f"Saved {path}")
