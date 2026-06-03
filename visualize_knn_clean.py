# -*- coding: utf-8 -*-
import os, sys
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

STYLE = dict(color="#1a2e5a", marker="o", markersize=6,
             linewidth=1.8, markerfacecolor="#1a2e5a",
             markeredgecolor="white", markeredgewidth=0.8)

knn_map  = nx.average_neighbor_degree(dir_net)
knn_by_k = {}
for node, k in dir_net.degree():
    if k > 0:
        knn_by_k.setdefault(k, []).append(knn_map[node])

ks   = sorted(knn_by_k)
knns = [np.mean(knn_by_k[k]) for k in ks]

# Trend line
log_k   = np.log10(ks)
log_knn = np.log10(knns)
slope, intercept = np.polyfit(log_k, log_knn, 1)
k_fit = np.logspace(log_k.min(), log_k.max(), 60)

fig, ax = plt.subplots(figsize=(7, 5.5))
ax.loglog(ks, knns, **STYLE, label="PT, 24")
ax.loglog(k_fit, 10**intercept * k_fit**slope, "--",
          color="#E74C3C", lw=1.5, alpha=0.8,
          label=f"trend  slope = {slope:+.2f}")

ax.set_xlabel("k", fontsize=14)
ax.set_ylabel("Knn(k)", fontsize=14)

# Match paper scale: x from 1 to 30, y from 3 to 50
ax.set_xlim(1, 30)
ax.set_ylim(3, 50)

# Clean integer tick labels on both axes (log scale)
ax.xaxis.set_major_formatter(ticker.ScalarFormatter())
ax.yaxis.set_major_formatter(ticker.ScalarFormatter())
ax.xaxis.set_minor_formatter(ticker.NullFormatter())
ax.yaxis.set_minor_formatter(ticker.NullFormatter())

ax.tick_params(labelsize=12)
ax.legend(fontsize=11, framealpha=0.95, edgecolor="#cccccc")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.grid(True, which="both", lw=0.4, alpha=0.4, linestyle="--")

fig.tight_layout()
path = "results/fig_dir_knn_v2.png"
fig.savefig(path, dpi=220, bbox_inches="tight")
plt.close(fig)
print(f"Saved {path}")
