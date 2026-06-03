# -*- coding: utf-8 -*-
import os
import numpy as np
import pandas as pd
import networkx as nx
from networkx.algorithms import bipartite
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

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

degrees = sorted([d for _, d in dir_net.degree()], reverse=True)
N = len(degrees)
avg_k = np.mean(degrees)
max_k = max(degrees)

# CCDF: P'(k) = P(K >= k)
unique_k = sorted(set(degrees))
ccdf_k   = [sum(1 for d in degrees if d >= k) / N for k in unique_k]

STYLE = dict(color="#1a2e5a", marker="o", markersize=5,
             linewidth=1.8, markerfacecolor="#1a2e5a",
             markeredgecolor="white", markeredgewidth=0.8)

fig, ax = plt.subplots(figsize=(7, 5.5))

# Semi-log: linear x, log y  (matching Fig. 7 style)
ax.semilogy(unique_k, ccdf_k, **STYLE, label="PT, 24")

ax.set_xlabel("k", fontsize=14)
ax.set_ylabel("P'(k)", fontsize=14)

ax.set_xlim(0, max_k + 1)
ax.set_ylim(1e-3, 1.5)

ax.tick_params(labelsize=12)
ax.legend(fontsize=11, framealpha=0.95, edgecolor="#cccccc")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.grid(True, which="both", lw=0.4, alpha=0.4, linestyle="--")

# Annotate average degree of the director network
ax.axvline(avg_k, color="#27AE60", lw=1.5, linestyle=":", alpha=0.8)
ax.text(avg_k + 0.4, 0.6,
        f"avg degree\n= {avg_k:.1f}",
        fontsize=9, color="#27AE60",
        bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#27AE60", alpha=0.85))

fig.tight_layout()
path = "results/fig_dir_degree_v2.png"
fig.savefig(path, dpi=220, bbox_inches="tight")
plt.close(fig)
print(f"Saved {path}  (avg_k={avg_k:.2f}, max_k={max_k})")
