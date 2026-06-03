# -*- coding: utf-8 -*-
import os
import numpy as np
import pandas as pd
import networkx as nx
from networkx.algorithms import bipartite
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

plt.rcParams["font.family"] = "DejaVu Sans"
os.makedirs("results", exist_ok=True)

df = pd.read_csv("boardmembers_2024.csv")
df = df.rename(columns={"name": "director"})
df = df.dropna(subset=["director", "company"]).drop_duplicates(subset=["director", "company"])

G_bip = nx.Graph()
G_bip.add_nodes_from(df["company"].unique(), bipartite=0)
G_bip.add_nodes_from(df["director"].unique(), bipartite=1)
for _, row in df.iterrows():
    G_bip.add_edge(row["company"], row["director"])

directors = {n for n, d in G_bip.nodes(data=True) if d.get("bipartite") == 1}
dir_net   = bipartite.weighted_projected_graph(G_bip, directors)

# c(k): average clustering coefficient for nodes of degree k
clust = nx.clustering(dir_net)
ck_by_k = {}
for node, k in dir_net.degree():
    if k >= 2:  # clustering undefined for degree < 2
        ck_by_k.setdefault(k, []).append(clust[node])

ks  = sorted(ck_by_k)
cks = [np.mean(ck_by_k[k]) for k in ks]

STYLE = dict(color="#1a2e5a", marker="o", markersize=6,
             linewidth=1.8, markerfacecolor="#1a2e5a",
             markeredgecolor="white", markeredgewidth=0.8)

fig, ax = plt.subplots(figsize=(7, 5.5))

# Log x, linear y — matching Fig. 16
ax.semilogx(ks, cks, **STYLE, label="PT, 24")

ax.set_xlabel("k", fontsize=14)
ax.set_ylabel("c(k)", fontsize=14)

# Match paper scale: x from 5 to ~150, y from 0 to 1
ax.set_xlim(5, max(ks) * 1.15)
ax.set_ylim(0, 1.05)
ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])

ax.xaxis.set_major_formatter(ticker.ScalarFormatter())
ax.xaxis.set_minor_formatter(ticker.NullFormatter())

ax.tick_params(labelsize=12)
ax.legend(fontsize=11, framealpha=0.95, edgecolor="#cccccc")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.grid(True, which="both", lw=0.4, alpha=0.4, linestyle="--")

fig.tight_layout()
path = "results/fig_dir_clustering_k.png"
fig.savefig(path, dpi=220, bbox_inches="tight")
plt.close(fig)
print(f"Saved {path}")
