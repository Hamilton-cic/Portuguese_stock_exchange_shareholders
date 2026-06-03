# -*- coding: utf-8 -*-
"""
Fig P (clean) — Pajek-style company projection network, no title/legend.
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

connected = [n for n in board_net.nodes() if board_net.degree(n) > 0]
G = board_net.subgraph(connected).copy()
print(f"Connected companies: {G.number_of_nodes()}  edges: {G.number_of_edges()}")

# ── Community detection ──────────────────────────────────────────────────────
partition  = community_louvain.best_partition(G, weight="weight", random_state=42)
modularity = community_louvain.modularity(partition, G, weight="weight")

from collections import Counter
comm_sizes  = Counter(partition.values())
top5_sorted = [cid for cid, _ in comm_sizes.most_common(5)]

PALETTE = {
    top5_sorted[0]: "#E74C3C",
    top5_sorted[1]: "#2F57C9",
    top5_sorted[2]: "#F39C12",
    top5_sorted[3]: "#27AE60",
    top5_sorted[4]: "#8E44AD",
}
DEFAULT_COLOR = "#aaaaaa"

def node_color(node):
    return PALETTE.get(partition[node], DEFAULT_COLOR)

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
components = sorted(nx.connected_components(G), key=len, reverse=True)
giant      = G.subgraph(components[0]).copy()
satellites = components[1:]

pos_giant = nx.kamada_kawai_layout(giant, weight=None)

gx = np.array([v[0] for v in pos_giant.values()])
gy = np.array([v[1] for v in pos_giant.values()])
gx = (gx - gx.mean()) / (gx.max() - gx.min() + 1e-9) * 1.6
gy = (gy - gy.mean()) / (gy.max() - gy.min() + 1e-9) * 1.4
for i, n in enumerate(pos_giant):
    pos_giant[n] = (gx[i], gy[i])

pos = dict(pos_giant)
sat_nodes_flat = [n for comp in satellites for n in comp]
n_sat = len(sat_nodes_flat)
R = 1.20
i = 0
for comp in satellites:
    comp = list(comp)
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

for u, v, data in G.edges(data=True):
    w = data.get("weight", 1)
    lw    = 0.6 + (w - 1) * 0.9
    alpha = 0.35 + min((w - 1) * 0.12, 0.5)
    ax.plot(
        [pos[u][0], pos[v][0]],
        [pos[u][1], pos[v][1]],
        color="#444444", linewidth=lw, alpha=alpha, zorder=1, solid_capstyle="round"
    )

NODE_SIZE = 120
for node in G.nodes():
    x, y  = pos[node]
    color = node_color(node)
    ax.scatter(x, y, s=NODE_SIZE, c=color, edgecolors="white",
               linewidths=1.0, zorder=3, alpha=0.95)

all_x = np.array([pos[n][0] for n in G.nodes()])
all_y = np.array([pos[n][1] for n in G.nodes()])
cx, cy = all_x.mean(), all_y.mean()

LABEL_OFFSET = 0.07

for node in G.nodes():
    x, y  = pos[node]
    lbl   = abbrev(node)
    color = node_color(node)

    dx, dy = x - cx, y - cy
    norm = max(np.sqrt(dx**2 + dy**2), 1e-6)
    ox = LABEL_OFFSET * dx / norm
    oy = LABEL_OFFSET * dy / norm
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

ax.axis("off")

pad = 0.14
ax.set_xlim(all_x.min() - pad, all_x.max() + pad)
ax.set_ylim(all_y.min() - pad, all_y.max() + pad)

fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
path = "results/figP_pajek_clean.png"
fig.savefig(path, dpi=240, bbox_inches="tight")
plt.close(fig)
print(f"Saved {path}")
