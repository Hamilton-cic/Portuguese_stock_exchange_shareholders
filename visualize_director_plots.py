# -*- coding: utf-8 -*-
"""
Director network figures matching paper style (Battiston & Catanzaro 2004):
  - Board size distribution (fixed: English labels)
  - Director degree distribution CCDF (log-log)
  - Director assortativity table
  - Director Knn(k) (log-log)
  - Director site betweenness CCDF
"""
import os, sys
import numpy as np
import pandas as pd
import networkx as nx
from networkx.algorithms import bipartite
from scipy.stats import poisson
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

plt.rcParams["font.family"] = "DejaVu Sans"
os.makedirs("results", exist_ok=True)

# ── Build networks ────────────────────────────────────────────────────────────
df = pd.read_csv("boardmembers_2024.csv")
df = df.rename(columns={"name": "director"})
df = df.dropna(subset=["director", "company"]).drop_duplicates(subset=["director", "company"])

G_bip = nx.Graph()
G_bip.add_nodes_from(df["company"].unique(), bipartite=0)
G_bip.add_nodes_from(df["director"].unique(), bipartite=1)
for _, row in df.iterrows():
    G_bip.add_edge(row["company"], row["director"])

companies = {n for n, d in G_bip.nodes(data=True) if d.get("bipartite") == 0}
directors = {n for n, d in G_bip.nodes(data=True) if d.get("bipartite") == 1}
dir_net   = bipartite.weighted_projected_graph(G_bip, directors)

N_d = dir_net.number_of_nodes()
E_d = dir_net.number_of_edges()

STYLE = dict(color="#1a2e5a", marker="o", markersize=6,
             linewidth=1.8, markerfacecolor="#1a2e5a",
             markeredgecolor="white", markeredgewidth=0.8)

def comma_fmt(x, _):
    """Format with comma as decimal separator (paper style)."""
    s = f"{x:.2f}".rstrip("0").rstrip(".")
    return s.replace(".", ",") if "." in s else s


# ════════════════════════════════════════════════════════════════════════════
# FIG 0 — Board size distribution (fixed: English)
# ════════════════════════════════════════════════════════════════════════════
def make_board_size():
    board_sizes = df.groupby("company")["director"].count()
    total = len(board_sizes)
    counts = board_sizes.value_counts().sort_index()
    n_vals = counts.index.values
    p_vals = counts.values / total

    fig, ax = plt.subplots(figsize=(7, 5.5))
    ax.plot(n_vals, p_vals, **STYLE, label="PT, 24")

    ax.set_xlabel("n", fontsize=14)
    ax.set_ylabel("P(n)", fontsize=14)
    ax.set_xlim(0, 26)
    ax.set_ylim(0, None)
    ax.tick_params(labelsize=12)
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(comma_fmt))
    ax.legend(fontsize=12, framealpha=0.95, edgecolor="#cccccc")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", lw=0.5, alpha=0.4, linestyle="--")

    mean_n = board_sizes.mean()
    ax.axvline(mean_n, color="#E74C3C", lw=1.5, linestyle=":", alpha=0.7)
    ax.text(mean_n + 0.3, ax.get_ylim()[1] * 0.88,
            f"average = {mean_n:.1f}", fontsize=10, color="#E74C3C")

    fig.tight_layout()
    path = "results/fig_board_size_dist.png"
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {path}")


# ════════════════════════════════════════════════════════════════════════════
# FIG A — Director degree distribution CCDF (log-log)
# ════════════════════════════════════════════════════════════════════════════
def make_degree_loglog():
    degrees = sorted([d for _, d in dir_net.degree()], reverse=True)
    N = len(degrees)
    lam = np.mean(degrees)

    # CCDF: P'(k) = P(K >= k)
    unique_k = sorted(set(degrees))
    ccdf_k = [sum(1 for d in degrees if d >= k) / N for k in unique_k]

    # Poisson reference
    k_range = np.arange(1, max(degrees) + 1)
    p0 = poisson.pmf(0, lam)
    poisson_ccdf = [(1 - poisson.cdf(k - 1, lam)) / (1 - p0) for k in k_range]

    fig, ax = plt.subplots(figsize=(7, 5.5))
    ax.loglog(unique_k, ccdf_k, **STYLE, label="PT, 24", zorder=3)
    ax.loglog(k_range, poisson_ccdf, "--", color="#888888", lw=1.5,
              label=f"Poisson (λ={lam:.1f})", alpha=0.85)

    ax.set_xlabel("k", fontsize=14)
    ax.set_ylabel("P'(k)", fontsize=14)
    ax.tick_params(labelsize=12)
    ax.legend(fontsize=11, framealpha=0.95, edgecolor="#cccccc")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, which="both", lw=0.4, alpha=0.4, linestyle="--")

    # Annotate plateau
    mean_board = df.groupby("company")["director"].count().mean()
    ax.axvline(mean_board, color="#27AE60", lw=1.5, linestyle=":", alpha=0.8)
    ax.text(mean_board * 1.08, 0.55, f"avg board\nsize ≈{mean_board:.0f}",
            fontsize=9, color="#27AE60",
            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#27AE60", alpha=0.85))

    fig.tight_layout()
    path = "results/fig_dir_degree_loglog.png"
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {path}")


# ════════════════════════════════════════════════════════════════════════════
# FIG B — Director assortativity table
# ════════════════════════════════════════════════════════════════════════════
def make_assortativity_table():
    r_pt = nx.degree_assortativity_coefficient(dir_net)

    # Reference values from paper Table 2
    ref = {
        "IT '86": {"Board r": 0.12, "Director r": 0.13},
        "IT '02": {"Board r": 0.32, "Director r": 0.25},
        "US '99": {"Board r": 0.27, "Director r": 0.27},
        "PT '24": {"Board r": 0.063, "Director r": round(r_pt, 3)},
    }

    fig, ax = plt.subplots(figsize=(8, 3.8))
    ax.axis("off")

    col_labels = ["Dataset", "Board network  r", "Director network  r", "Interpretation"]
    interp = [
        "Mildly assortative",
        "Assortative  (strongest board)",
        "Assortative",
        "Board: near-neutral\nDirectors: assortative ✓",
    ]
    rows = []
    for (ds, vals), note in zip(ref.items(), interp):
        rows.append([ds,
                     f"{vals['Board r']:.3f}",
                     f"{vals['Director r']:.3f}",
                     note])

    tbl = ax.table(
        cellText=rows,
        colLabels=col_labels,
        loc="center",
        cellLoc="center",
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(11)
    tbl.scale(1.0, 2.0)

    # Header style
    for j in range(len(col_labels)):
        tbl[0, j].set_facecolor("#1a2e5a")
        tbl[0, j].set_text_props(color="white", fontweight="bold")

    # Highlight PT row
    for j in range(len(col_labels)):
        tbl[4, j].set_facecolor("#fff5f5")
        tbl[4, j].set_text_props(color="#E74C3C", fontweight="bold")

    # Alternating rows
    for i in [2, 4]:
        for j in range(len(col_labels)):
            if i != 4:
                tbl[i, j].set_facecolor("#f5f7fc")

    ax.set_title("Assortativity coefficients  r  —  PT '24 vs reference datasets",
                 fontsize=12, fontweight="bold", pad=14)

    fig.tight_layout()
    path = "results/fig_assortativity_table.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {path}")


# ════════════════════════════════════════════════════════════════════════════
# FIG C — Director Knn(k)  (log-log, like paper Fig. 13)
# ════════════════════════════════════════════════════════════════════════════
def make_knn():
    knn_map = nx.average_neighbor_degree(dir_net)
    knn_by_k = {}
    for node, k in dir_net.degree():
        if k > 0:
            knn_by_k.setdefault(k, []).append(knn_map[node])
    ks   = sorted(knn_by_k)
    knns = [np.mean(knn_by_k[k]) for k in ks]

    fig, ax = plt.subplots(figsize=(7, 5.5))
    ax.loglog(ks, knns, **STYLE, label="PT, 24")

    # Trend line (log-log linear fit)
    log_k = np.log10(ks)
    log_knn = np.log10(knns)
    slope, intercept = np.polyfit(log_k, log_knn, 1)
    k_fit = np.logspace(log_k.min(), log_k.max(), 60)
    ax.loglog(k_fit, 10**intercept * k_fit**slope, "--",
              color="#E74C3C", lw=1.5, alpha=0.8,
              label=f"trend  slope = {slope:+.2f}")

    ax.set_xlabel("k", fontsize=14)
    ax.set_ylabel("Knn(k)", fontsize=14)
    ax.tick_params(labelsize=12)
    ax.legend(fontsize=11, framealpha=0.95, edgecolor="#cccccc")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, which="both", lw=0.4, alpha=0.4, linestyle="--")

    r = nx.degree_assortativity_coefficient(dir_net)
    ax.text(0.97, 0.06,
            f"Assortativity  r = {r:.3f}\nSlope > 0  →  assortative\n(high-degree directors connect\nto other high-degree directors)",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=9.5,
            bbox=dict(boxstyle="round,pad=0.4", fc="#f0f4fb", ec="#1a2e5a", alpha=0.92))

    fig.tight_layout()
    path = "results/fig_dir_knn.png"
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {path}")


# ════════════════════════════════════════════════════════════════════════════
# FIG D — Director site betweenness CCDF  (like paper Fig. 9)
# ════════════════════════════════════════════════════════════════════════════
def make_betweenness():
    print("  Computing betweenness centrality...")
    btw_raw = nx.betweenness_centrality(dir_net, normalized=False)
    N = dir_net.number_of_nodes()

    # b/N (paper normalisation)
    b_over_N = sorted(btw_raw[n] / N for n in dir_net.nodes())
    b_over_N.sort(reverse=True)
    total = len(b_over_N)

    # CCDF: for each value b/N, fraction of nodes with betweenness >= that value
    unique_b = sorted(set(b_over_N), reverse=True)
    ccdf_b   = [sum(1 for x in b_over_N if x >= b) / total for b in unique_b]

    fig, ax = plt.subplots(figsize=(7, 5.5))
    ax.semilogy(unique_b, ccdf_b, **STYLE, label="PT, 24")

    ax.set_xlabel("b / N", fontsize=14)
    ax.set_ylabel("P'(b)", fontsize=14)
    ax.tick_params(labelsize=12)
    ax.legend(fontsize=11, framealpha=0.95, edgecolor="#cccccc", loc="upper right")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, which="both", lw=0.4, alpha=0.4, linestyle="--")

    # Annotate mean and max
    mean_b = np.mean(list(btw_raw.values())) / N
    max_b  = max(btw_raw.values()) / N
    # Find top node
    top_node = max(btw_raw, key=btw_raw.get)
    ax.text(0.97, 0.35,
            f"max b/N = {max_b:.1f}\n({top_node.split()[0]} {top_node.split()[-1]})\n\nmean b/N = {mean_b:.3f}",
            transform=ax.transAxes, ha="right", va="center", fontsize=9,
            bbox=dict(boxstyle="round,pad=0.4", fc="#f0f4fb", ec="#1a2e5a", alpha=0.92))

    fig.tight_layout()
    path = "results/fig_dir_betweenness.png"
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {path}")


# ── Run ───────────────────────────────────────────────────────────────────────
make_board_size()
make_degree_loglog()
make_assortativity_table()
make_knn()
make_betweenness()
print("\nDone.")
